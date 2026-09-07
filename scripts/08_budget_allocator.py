"""
VibeSignal AI - Budget Allocator
Script 08

Takes a campaign budget in INR and recommends creator
selections across three strategies: nano-focus, micro-focus,
and mixed. Outputs a side-by-side scenario comparison.

Requires vibe_scores.csv from script 07.
Synthetic data only — for portfolio and demo use.
"""

# the question this solves:
# "I have X rupees — which creators do I pick?"
# most analytics tools answer which creators performed well
# this tool answers what to do before the campaign starts

import json
import os

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


# ---
# load vibe scores
# ---

scores_path = os.path.join(DATA_DIR, "vibe_scores.csv")
if not os.path.exists(scores_path):
    raise FileNotFoundError(
        "vibe_scores.csv not found. Run 07_vibescore_model.py first."
    )

creators = pd.read_csv(os.path.join(DATA_DIR, "creators.csv"))
scores   = pd.read_csv(scores_path)

# merge estimated cost back in case it's not in scores
if "estimated_cost_inr" not in scores.columns:
    scores = scores.merge(
        creators[["creator_id", "estimated_cost_inr"]],
        on="creator_id", how="left",
    )

print("VibeScore data loaded.")
print(f"  {len(scores)} creators available for selection")
print()


# ---
# campaign configuration
# ---

# these are the inputs a brand manager would provide
# in the Streamlit app they'll be sliders and dropdowns

CAMPAIGN_BUDGET_INR = 500_000      # ₹5,00,000 — typical mid-size D2C campaign
CAMPAIGN_OBJECTIVE  = "sales"      # awareness / engagement / traffic / sales
TARGET_NICHE        = None         # None means any niche — or set e.g. "beauty"
TARGET_PLATFORM     = None         # None means any platform

# fee buffer — don't spend 100% on fees
# keep 20% for content production and contingency
FEE_BUDGET_INR = CAMPAIGN_BUDGET_INR * 0.80

print(f"Campaign budget:    ₹{CAMPAIGN_BUDGET_INR:,.0f}")
print(f"Fee budget (80%):   ₹{FEE_BUDGET_INR:,.0f}")
print(f"Objective:          {CAMPAIGN_OBJECTIVE}")
print(f"Niche filter:       {TARGET_NICHE or 'any'}")
print(f"Platform filter:    {TARGET_PLATFORM or 'any'}")
print()


# ---
# filter creator pool
# ---

pool = scores.copy()

# only consider creators with a track record
# Stop-rated creators excluded from recommendations
pool = pool[pool["recommendation"] != "Stop"]

# apply niche and platform filters if specified
if TARGET_NICHE:
    pool = pool[pool["niche"] == TARGET_NICHE]
if TARGET_PLATFORM:
    pool = pool[pool["platform"] == TARGET_PLATFORM]

# adjust VibeScore weight based on campaign objective
# for sales campaigns, conversion matters most
# for awareness, engagement and reach matter more
OBJECTIVE_BOOST = {
    "sales":       {"conversion_score": 0.15, "roi_score": 0.10},
    "awareness":   {"engagement_score": 0.15, "audience_fit_score": 0.10},
    "engagement":  {"engagement_score": 0.20, "conversion_score": 0.05},
    "traffic":     {"conversion_score": 0.10, "audience_fit_score": 0.10},
}

boost = OBJECTIVE_BOOST.get(CAMPAIGN_OBJECTIVE, {})
if boost:
    pool = pool.copy()
    for col, extra in boost.items():
        if col in pool.columns:
            pool["vibe_score"] = pool["vibe_score"] + (pool[col] * extra)
    pool["vibe_score"] = pool["vibe_score"].clip(0, 100)

pool = pool.sort_values("vibe_score", ascending=False).reset_index(drop=True)

print(f"Eligible creator pool: {len(pool)} creators")
print()


# ---
# allocation engine
# ---

def allocate_budget(
    pool: pd.DataFrame,
    fee_budget: float,
    tier_filter: list,
    max_creators: int,
    min_creators: int = 1,
) -> pd.DataFrame:
    """
    Greedy budget allocation — highest VibeScore first,
    within budget, within tier filter.

    Returns selected creators with allocated fees.
    Fee is negotiated at 90-100% of estimated_cost_inr
    to reflect realistic partnership dynamics.
    """
    candidates = pool[pool["tier"].isin(tier_filter)].copy()

    selected     = []
    remaining    = fee_budget
    num_selected = 0

    for _, creator in candidates.iterrows():
        if num_selected >= max_creators:
            break

        # negotiate fee — slight variation around estimated cost
        base_fee    = float(creator["estimated_cost_inr"])
        negotiated  = round(base_fee * np.random.uniform(0.90, 1.00), 2)

        if negotiated <= remaining:
            row = creator.to_dict()
            row["allocated_fee_inr"] = negotiated
            selected.append(row)
            remaining    -= negotiated
            num_selected += 1

    result = pd.DataFrame(selected) if selected else pd.DataFrame()

    if len(result) < min_creators:
        return pd.DataFrame()  # strategy not viable at this budget

    return result


np.random.seed(42)

# Strategy 1 — Nano focus
# many small creators, maximum diversity, lower individual authority
nano_selection = allocate_budget(
    pool=pool,
    fee_budget=FEE_BUDGET_INR,
    tier_filter=["nano"],
    max_creators=15,
    min_creators=5,
)

# Strategy 2 — Micro focus
# balanced approach, 3-8 creators, best for most D2C campaigns
micro_selection = allocate_budget(
    pool=pool,
    fee_budget=FEE_BUDGET_INR,
    tier_filter=["micro"],
    max_creators=8,
    min_creators=3,
)

# Strategy 3 — Mixed
# one macro anchor for reach, supported by micro/nano for conversion
macro_anchor = allocate_budget(
    pool=pool,
    fee_budget=FEE_BUDGET_INR * 0.50,  # macro gets 50% of budget
    tier_filter=["macro"],
    max_creators=1,
    min_creators=1,
)
if not macro_anchor.empty:
    remaining_for_support = FEE_BUDGET_INR - macro_anchor["allocated_fee_inr"].sum()
    support_pool = pool[~pool["creator_id"].isin(macro_anchor["creator_id"])]
    support_selection = allocate_budget(
        pool=support_pool,
        fee_budget=remaining_for_support,
        tier_filter=["micro", "nano"],
        max_creators=5,
        min_creators=2,
    )
    if not support_selection.empty:
        mixed_selection = pd.concat(
            [macro_anchor, support_selection], ignore_index=True
        )
    else:
        mixed_selection = pd.DataFrame()
else:
    mixed_selection = pd.DataFrame()


# ---
# scenario summary builder
# ---

def summarise_strategy(
    selection: pd.DataFrame,
    strategy_name: str,
    total_budget: float,
) -> dict:
    """
    Compute key metrics for one allocation strategy.
    """
    if selection.empty:
        return {
            "strategy":          strategy_name,
            "viable":            False,
            "num_creators":      0,
            "total_fee_inr":     0,
            "pct_budget_used":   0,
            "avg_vibe_score":    0,
            "avg_roi_pct":       0,
            "avg_cvr":           0,
            "est_total_reach":   0,
            "tier_mix":          "N/A",
        }

    total_fee     = selection["allocated_fee_inr"].sum()
    est_reach     = (
        selection["follower_count"] * 0.35
    ).sum().astype(int)

    tier_counts   = selection["tier"].value_counts().to_dict()
    tier_mix      = ", ".join(
        f"{count} {tier}" for tier, count in tier_counts.items()
    )

    return {
        "strategy":          strategy_name,
        "viable":            True,
        "num_creators":      len(selection),
        "total_fee_inr":     round(total_fee, 2),
        "pct_budget_used":   round((total_fee / total_budget) * 100, 1),
        "avg_vibe_score":    round(selection["vibe_score"].mean(), 2),
        "avg_roi_pct":       round(selection["avg_roi_pct"].mean(), 2),
        "avg_cvr":           round(selection["avg_cvr"].mean(), 4),
        "est_total_reach":   est_reach,
        "tier_mix":          tier_mix,
    }


summaries = [
    summarise_strategy(nano_selection,  "Nano Focus",  CAMPAIGN_BUDGET_INR),
    summarise_strategy(micro_selection, "Micro Focus", CAMPAIGN_BUDGET_INR),
    summarise_strategy(mixed_selection, "Mixed",       CAMPAIGN_BUDGET_INR),
]

comparison = pd.DataFrame(summaries)


# ---
# print results
# ---

print("=" * 65)
print("VIBESIGNAL AI — BUDGET ALLOCATION RESULTS")
print(f"Budget: ₹{CAMPAIGN_BUDGET_INR:,.0f} | Objective: {CAMPAIGN_OBJECTIVE}")
print("Synthetic data — portfolio/demo only")
print("=" * 65)
print()

print("STRATEGY COMPARISON:")
print(comparison[[
    "strategy", "num_creators", "total_fee_inr",
    "pct_budget_used", "avg_vibe_score", "avg_roi_pct",
    "est_total_reach", "tier_mix",
]].to_string(index=False))
print()

# print creator details for each viable strategy
for strategy_name, selection in [
    ("NANO FOCUS",  nano_selection),
    ("MICRO FOCUS", micro_selection),
    ("MIXED",       mixed_selection),
]:
    if selection.empty:
        print(f"{strategy_name}: not viable at this budget")
        print()
        continue

    print(f"{strategy_name} — {len(selection)} creators:")
    print(
        selection[[
            "name", "tier", "platform", "niche",
            "vibe_score", "avg_roi_pct", "allocated_fee_inr",
        ]]
        .sort_values("vibe_score", ascending=False)
        .to_string(index=False)
    )
    total = selection["allocated_fee_inr"].sum()
    print(f"  Total fee: ₹{total:,.2f}")
    print()


# ---
# recommendation
# ---

# pick the strategy with the highest average VibeScore
# among viable options — simple, transparent, explainable
viable = comparison[comparison["viable"] == True]

if not viable.empty:
    best_idx      = viable["avg_vibe_score"].idxmax()
    best_strategy = viable.loc[best_idx, "strategy"]

    print("=" * 65)
    print(f"RECOMMENDED STRATEGY: {best_strategy}")
    print(
        f"Highest average VibeScore ({viable.loc[best_idx, 'avg_vibe_score']}) "
        f"among viable options."
    )
    print(
        "Note: recommendation is based on synthetic data and prototype "
        "logic — not a guaranteed real-world outcome."
    )
    print("=" * 65)
else:
    print("No viable strategy found at this budget.")
    print("Try increasing the budget or removing niche/platform filters.")


# ---
# save outputs
# ---

comparison_path = os.path.join(DATA_DIR, "budget_allocation_comparison.csv")
comparison.to_csv(comparison_path, index=False)
print(f"\ncomparison saved: {comparison_path}")

# save each strategy's creator list
for name, df in [
    ("nano",  nano_selection),
    ("micro", micro_selection),
    ("mixed", mixed_selection),
]:
    if not df.empty:
        path = os.path.join(DATA_DIR, f"allocation_{name}.csv")
        df.to_csv(path, index=False)
        print(f"allocation saved: {path}")

print()
print("Budget allocator complete.")