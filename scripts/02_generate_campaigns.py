"""
VibeSignal AI - Campaign Data Generator
Synthetic Dataset • Indian D2C • Data-Driven Campaign Insights
"""

import os
import random

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker("en_IN")

random.seed(42)
np.random.seed(42)
Faker.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

NUM_BRANDS    = 15
NUM_CAMPAIGNS = 70

OBJECTIVES = ["awareness", "engagement", "traffic", "sales"]
STATUSES   = ["draft", "active", "completed", "paused"]

INDUSTRIES = [
    "fashion", "beauty", "food & beverage",
    "fitness", "personal care", "home decor",
    "electronics", "edtech",
]

TARGET_SEGMENTS       = ["Gen Z", "Millennials", "Urban professionals", "Parents"]
TARGET_AGE_GROUPS     = ["18-24", "25-34", "35-44"]
PLATFORMS             = ["instagram", "youtube", "twitter"]
CREATOR_TIER_PREFERENCES = ["nano", "micro", "macro", "mixed"]

BUDGET_RANGES = {
    "small": (50_000,    300_000),
    "mid":   (300_000,   1_000_000),
    "large": (1_000_000, 2_000_000),
}

BUDGET_WEIGHTS = {
    "small": 0.55,
    "mid":   0.35,
    "large": 0.10,
}


def choose_campaign_budget() -> float:
    budget_group = random.choices(
        population=list(BUDGET_WEIGHTS.keys()),
        weights=list(BUDGET_WEIGHTS.values()),
        k=1,
    )[0]
    lo, hi = BUDGET_RANGES[budget_group]
    return round(random.uniform(lo, hi), 2)


def create_promo_code(handle: str, partnership_id: int) -> str:
    clean = (
        handle.replace("@", "")
              .replace("_", "")
              .replace(".", "")
              .upper()
    )
    return f"{clean[:8]}{partnership_id}"


def calculate_creator_fee(creator: pd.Series) -> float:
    """
    Negotiate a synthetic fee close to the creator's base cost estimate.
    Stays within ±15% of estimated_cost_inr so fees never wildly
    exceed campaign budgets.
    """
    base = float(creator["estimated_cost_inr"])
    return round(base * random.uniform(0.85, 1.15), 2)


def generate_brands(n: int = NUM_BRANDS) -> pd.DataFrame:
    rows = []
    for i in range(n):
        rows.append({
            "brand_id":       i + 1,
            "brand_name":     fake.company(),
            "industry":       random.choice(INDUSTRIES),
            "target_segment": random.choice(TARGET_SEGMENTS),
            "country":        "India",
        })
    return pd.DataFrame(rows)


def generate_campaigns(
    brands_df: pd.DataFrame,
    n: int = NUM_CAMPAIGNS,
) -> pd.DataFrame:
    rows         = []
    brand_ids    = brands_df["brand_id"].tolist()
    brand_lookup = brands_df.set_index("brand_id")

    for i in range(n):
        # use random.choice so brand assignment is genuinely random
        # within the seeded environment
        brand_id = random.choice(brand_ids)
        brand    = brand_lookup.loc[brand_id]

        start    = fake.date_between(start_date="-1y", end_date="-1m")
        duration = random.randint(14, 90)
        end      = start + pd.Timedelta(days=duration)

        rows.append({
            "campaign_id":            i + 1,
            "brand_id":               int(brand_id),
            "campaign_name":          f"{fake.catch_phrase()} Campaign",
            "objective":              random.choice(OBJECTIVES),
            "target_segment":         str(brand["target_segment"]),
            "target_age_group":       random.choice(TARGET_AGE_GROUPS),
            "target_niche":           str(brand["industry"]),
            "preferred_platform":     random.choice(PLATFORMS),
            "preferred_creator_tier": random.choice(CREATOR_TIER_PREFERENCES),
            "total_budget_inr":       choose_campaign_budget(),
            "start_date":             start,
            "end_date":               end,
            "status":                 random.choice(STATUSES),
        })

    return pd.DataFrame(rows)


def get_candidate_creators(
    campaign: pd.Series,
    creators_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Select creators matching campaign niche and platform preferences.
    Falls back to full creator pool when filtered set is too small.
    """
    candidates = creators_df[
        (creators_df["niche"]     == campaign["target_niche"]) &
        (creators_df["platform"]  == campaign["preferred_platform"])
    ].copy()

    if campaign["preferred_creator_tier"] != "mixed":
        tier_match = candidates[
            candidates["tier"] == campaign["preferred_creator_tier"]
        ]
        if len(tier_match) >= 2:
            candidates = tier_match

    if len(candidates) < 3:
        candidates = creators_df.copy()

    return candidates


def generate_campaign_creators(
    campaigns_df: pd.DataFrame,
    creators_df: pd.DataFrame,
) -> tuple:
    rows           = []
    partnership_id = 1
    creator_campaigns: dict = {}

    for _, campaign in campaigns_df.iterrows():
        candidates      = get_candidate_creators(campaign, creators_df)
        campaign_budget = float(campaign["total_budget_inr"])

        # allocate 65-85% of budget to creator fees
        max_creator_spend = campaign_budget * random.uniform(0.65, 0.85)
        remaining_spend   = max_creator_spend

        desired_count        = random.randint(3, 8)
        selected_creator_ids = set()
        partnerships_created = 0

        shuffled = candidates.sample(
            frac=1,
            random_state=int(campaign["campaign_id"]) + 500,
        )

        for _, creator in shuffled.iterrows():
            if partnerships_created >= desired_count:
                break

            creator_id = int(creator["creator_id"])

            if creator_id in selected_creator_ids:
                continue

            fee = calculate_creator_fee(creator)

            if fee > remaining_spend:
                continue

            selected_creator_ids.add(creator_id)
            remaining_spend   -= fee
            partnerships_created += 1

            impressions           = int(creator["follower_count"] * random.uniform(0.25, 0.95))
            estimated_engagements = int(impressions * (creator["avg_engagement_rate"] / 100))

            revenue_multiple = random.uniform(0.6, 3.0)
            if random.random() < 0.12:
                revenue_multiple = random.uniform(3.0, 5.0)

            revenue_attributed = round(fee * revenue_multiple, 2)
            promo_code         = create_promo_code(creator["handle"], partnership_id)

            creator_campaigns.setdefault(creator_id, []).append(
                int(campaign["campaign_id"])
            )

            rows.append({
                "cc_id":                    partnership_id,
                "campaign_id":              int(campaign["campaign_id"]),
                "creator_id":               creator_id,
                "creator_fee_inr":          fee,
                "revenue_attributed_inr":   revenue_attributed,
                "impressions_delivered":    impressions,
                "estimated_engagements":    estimated_engagements,
                "promo_code":               promo_code,
                "status":                   random.choice(["confirmed", "active", "completed"]),
            })

            partnership_id += 1

    return pd.DataFrame(rows), creator_campaigns


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)

    creators_path = os.path.join(DATA_DIR, "creators.csv")
    if not os.path.exists(creators_path):
        raise FileNotFoundError(
            "creators.csv not found. Run 01_generate_creators.py first."
        )

    creators_df = pd.read_csv(creators_path)

    required = {"creator_id", "handle", "tier", "niche", "platform",
                "follower_count", "avg_engagement_rate", "estimated_cost_inr"}
    missing  = required - set(creators_df.columns)
    if missing:
        raise ValueError(f"creators.csv missing columns: {sorted(missing)}")

    brands_df    = generate_brands()
    campaigns_df = generate_campaigns(brands_df)
    campaign_creators_df, _ = generate_campaign_creators(campaigns_df, creators_df)

    # referential integrity
    assert (~campaign_creators_df["creator_id"].isin(creators_df["creator_id"])).sum() == 0, \
        "Orphan creator references found"
    assert (~campaign_creators_df["campaign_id"].isin(campaigns_df["campaign_id"])).sum() == 0, \
        "Orphan campaign references found"

    dupes = campaign_creators_df["promo_code"].duplicated().sum()
    print(f"Orphan creator refs:  0")
    print(f"Orphan campaign refs: 0")
    print(f"Duplicate promo codes: {dupes} (should be 0)")

    # budget check — no campaign should overspend
    allocated = (
        campaign_creators_df.groupby("campaign_id")["creator_fee_inr"]
        .sum().reset_index(name="allocated_inr")
    )
    budget_check = campaigns_df.merge(allocated, on="campaign_id", how="left")
    budget_check["allocated_inr"] = budget_check["allocated_inr"].fillna(0)
    exceeded = (budget_check["allocated_inr"] > budget_check["total_budget_inr"]).sum()
    print(f"Campaigns exceeding budget: {exceeded} (should be 0)")

    print(f"\nCampaign budget range (INR):")
    print(f"  Min: ₹{campaigns_df['total_budget_inr'].min():,.0f}")
    print(f"  Max: ₹{campaigns_df['total_budget_inr'].max():,.0f}")
    print(f"  Avg: ₹{campaigns_df['total_budget_inr'].mean():,.0f}")

    print(f"\nPartnership table shape: {campaign_creators_df.shape}")

    merged = campaign_creators_df.merge(
        creators_df[["creator_id", "tier"]], on="creator_id", how="left"
    )
    merged["roi_proxy"] = merged["revenue_attributed_inr"] / merged["creator_fee_inr"]
    print("\nAverage ROI proxy by tier:")
    print(
        merged.groupby("tier")["roi_proxy"]
        .mean()
        .reindex(["nano", "micro", "macro", "mega"])
        .round(2)
    )

    brands_df.to_csv(os.path.join(DATA_DIR, "brands.csv"), index=False)
    campaigns_df.to_csv(os.path.join(DATA_DIR, "campaigns.csv"), index=False)
    campaign_creators_df.to_csv(os.path.join(DATA_DIR, "campaign_creators.csv"), index=False)
    print("\nSaved: brands.csv, campaigns.csv, campaign_creators.csv")

