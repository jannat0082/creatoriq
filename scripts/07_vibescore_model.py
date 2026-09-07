"""
VibeSignal AI - VibeScore Model
Script 07

Scores each creator from 0 to 100 using five dimensions
that actually matter for Indian D2C brand decisions.

"""

# wanted a single number per creator that a brand manager
# could act on immediately — instead of juggling five metrics
# separately and guessing which one matters most
#
# weighted scoring made more sense here than black-box ML
# because the relationships between these metrics and business
# value are already understood from the EDA
#
# weights are a design decision, not a fixed truth —
# they can be tuned per brand or campaign objective

import json
import os

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


# ---
# load data
# ---

required_files = [
    "creators.csv",
    "campaign_creators.csv",
    "posts.csv",
    "conversions.csv",
    "audience_demographics.csv",
]

missing = [
    f for f in required_files
    if not os.path.exists(os.path.join(DATA_DIR, f))
]
if missing:
    raise FileNotFoundError(
        "Run generator scripts first. Missing:\n" + "\n".join(missing)
    )

creators          = pd.read_csv(os.path.join(DATA_DIR, "creators.csv"))
campaign_creators = pd.read_csv(os.path.join(DATA_DIR, "campaign_creators.csv"))
posts             = pd.read_csv(os.path.join(DATA_DIR, "posts.csv"))
conversions       = pd.read_csv(os.path.join(DATA_DIR, "conversions.csv"))
demographics      = pd.read_csv(os.path.join(DATA_DIR, "audience_demographics.csv"))

print("data loaded.")
print(f"  creators:          {len(creators)}")
print(f"  campaign_creators: {len(campaign_creators)}")
print(f"  posts:             {len(posts)}")
print(f"  conversions:       {len(conversions)}")
print(f"  demographics:      {len(demographics)}")
print()


# ---
# weights
# ---

# ROI and conversion weighted highest — they tie directly to revenue
# engagement quality matters but less than actual purchase behaviour
# authenticity at 15% — fake audiences destroy ROI silently
# audience fit at 15% — right audience matters as much as reach
# raw engagement rate lowest — EDA proved it misleading on its own

WEIGHTS = {
    "roi_score":          0.35,
    "conversion_score":   0.25,
    "authenticity_score": 0.15,
    "audience_fit_score": 0.15,
    "engagement_score":   0.10,
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-6, "weights must sum to 1.0"


# ---
# step 1: compute raw metrics per creator
# ---

# ROI per creator using INR columns
cc = campaign_creators.merge(
    creators[["creator_id", "tier", "platform", "niche"]],
    on="creator_id", how="left",
)
cc["roi_pct"] = (
    (cc["revenue_attributed_inr"] - cc["creator_fee_inr"])
    / cc["creator_fee_inr"].replace(0, np.nan)
) * 100

roi_by_creator = (
    cc.groupby("creator_id")
    .agg(
        avg_roi_pct       = ("roi_pct",                "mean"),
        total_revenue_inr = ("revenue_attributed_inr", "sum"),
        total_fee_inr     = ("creator_fee_inr",        "sum"),
        num_campaigns     = ("campaign_id",             "nunique"),
    )
    .reset_index()
)

# post-level engagement
posts["engagement_rate"] = (
    (posts["likes"] + posts["comments"] + posts["shares"])
    / posts["reach"].replace(0, np.nan)
) * 100

posts["comment_like_ratio"] = posts["comments"] / (posts["likes"] + 1)

# rename before merging to avoid column name conflict
# creators.csv already has avg_engagement_rate — keeping that one
post_engagement = (
    posts.groupby("creator_id")
    .agg(
        post_avg_er            = ("engagement_rate",    "mean"),
        avg_comment_like_ratio = ("comment_like_ratio", "mean"),
        total_clicks           = ("clicks",             "sum"),
        total_posts            = ("post_id",             "count"),
    )
    .reset_index()
)

# conversion rate per creator
conv_counts = (
    conversions.groupby("post_id")
    .size()
    .reset_index(name="num_conversions")
)
posts_conv = posts.merge(conv_counts, on="post_id", how="left")
posts_conv["num_conversions"] = posts_conv["num_conversions"].fillna(0)
posts_conv["cvr"] = (
    posts_conv["num_conversions"]
    / posts_conv["clicks"].replace(0, np.nan)
) * 100

cvr_by_creator = (
    posts_conv.groupby("creator_id")
    .agg(
        avg_cvr           = ("cvr",            "mean"),
        total_conversions = ("num_conversions", "sum"),
    )
    .reset_index()
)

# audience fit — 18-34 share as proxy for D2C core demographic
young_adult_share = (
    demographics[
        (demographics["demographic_type"] == "age_group") &
        (demographics["demographic_value"].isin(["18-24", "25-34"]))
    ]
    .groupby("creator_id")["percentage_share"]
    .sum()
    .reset_index(name="young_adult_share_pct")
)

print("raw metrics computed.")


# ---
# step 2: merge into one scoring dataframe
# ---

# start from creators — pull the columns we need directly
# avg_engagement_rate here is the creator-level baseline from creators.csv
scores = creators[[
    "creator_id", "name", "tier", "platform", "niche",
    "follower_count",
    "avg_engagement_rate",        # creator baseline — used for engagement_score
    "audience_authenticity_score",
    "authenticity_risk_level",
    "estimated_cost_inr",
]].copy()

scores = scores.merge(roi_by_creator,    on="creator_id", how="left")
scores = scores.merge(post_engagement,   on="creator_id", how="left")
scores = scores.merge(cvr_by_creator,    on="creator_id", how="left")
scores = scores.merge(young_adult_share, on="creator_id", how="left")

# creators with no campaign history get 0 — penalised, not excluded
scores = scores.fillna(0)

print(f"scoring dataframe shape: {scores.shape}")
print(f"columns: {list(scores.columns)}")
print()


# ---
# step 3: normalize each metric to 0-100
# ---

def normalize(series: pd.Series) -> pd.Series:
    """
    Min-max normalisation.
    Lowest value gets 0, highest gets 100.
    Returns 50 for everyone if all values are identical.
    """
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series([50.0] * len(series), index=series.index)
    return ((series - lo) / (hi - lo)) * 100


# using avg_engagement_rate from creators.csv — no suffix conflict
scores["roi_score"]          = normalize(scores["avg_roi_pct"])
scores["conversion_score"]   = normalize(scores["avg_cvr"])
scores["authenticity_score"] = normalize(scores["audience_authenticity_score"])
scores["audience_fit_score"] = normalize(scores["young_adult_share_pct"])
scores["engagement_score"]   = normalize(scores["avg_engagement_rate"])

print("normalisation done.")


# ---
# step 4: weighted VibeScore
# ---

scores["vibe_score"] = (
    scores["roi_score"]          * WEIGHTS["roi_score"]          +
    scores["conversion_score"]   * WEIGHTS["conversion_score"]   +
    scores["authenticity_score"] * WEIGHTS["authenticity_score"] +
    scores["audience_fit_score"] * WEIGHTS["audience_fit_score"] +
    scores["engagement_score"]   * WEIGHTS["engagement_score"]
).round(2)


# ---
# step 5: recommendation labels
# ---

def label(score: float) -> str:
    if score >= 75:
        return "Scale"
    if score >= 50:
        return "Watch"
    if score >= 25:
        return "Improve"
    return "Stop"


scores["recommendation"] = scores["vibe_score"].apply(label)


# ---
# step 6: final results table
# ---

output_cols = [
    "creator_id", "name", "tier", "platform", "niche",
    "follower_count", "avg_engagement_rate",
    "avg_roi_pct", "avg_cvr",
    "audience_authenticity_score", "authenticity_risk_level",
    "young_adult_share_pct",
    "roi_score", "conversion_score", "authenticity_score",
    "audience_fit_score", "engagement_score",
    "vibe_score", "recommendation",
    "num_campaigns", "total_conversions", "estimated_cost_inr",
]

results = (
    scores[output_cols]
    .sort_values("vibe_score", ascending=False)
    .reset_index(drop=True)
)


# ---
# step 7: print results
# ---

print()
print("=" * 60)
print("VIBESIGNAL AI — VIBESCORE RESULTS")
print("Synthetic data — portfolio/demo only")
print("=" * 60)
print()

print("top 10 creators by VibeScore:")
print(
    results[[
        "name", "tier", "vibe_score",
        "recommendation", "avg_roi_pct", "avg_cvr",
    ]]
    .head(10)
    .to_string(index=False)
)
print()

print("recommendation distribution:")
print(results["recommendation"].value_counts().to_string())
print()

print("average VibeScore by tier:")
print(
    results.groupby("tier")["vibe_score"]
    .mean()
    .reindex(["nano", "micro", "macro", "mega"])
    .round(2)
    .to_string()
)
print()

print("average VibeScore by authenticity risk:")
print(
    results.groupby("authenticity_risk_level")["vibe_score"]
    .mean()
    .round(2)
    .to_string()
)
print()

print("dimension scores by tier:")
dim_cols = [
    "roi_score", "conversion_score", "authenticity_score",
    "audience_fit_score", "engagement_score",
]
print(
    results.groupby("tier")[dim_cols]
    .mean()
    .reindex(["nano", "micro", "macro", "mega"])
    .round(1)
    .to_string()
)
print()


# ---
# step 8: save outputs
# ---

scores_path = os.path.join(DATA_DIR, "vibe_scores.csv")
results.to_csv(scores_path, index=False)
print(f"scores saved:  {scores_path}")

weights_path = os.path.join(DATA_DIR, "vibescore_weights.json")
with open(weights_path, "w") as f:
    json.dump(WEIGHTS, f, indent=2)
print(f"weights saved: {weights_path}")

summary = (
    results.groupby("recommendation")
    .agg(
        count          = ("creator_id",  "count"),
        avg_vibe_score = ("vibe_score",  "mean"),
        avg_roi        = ("avg_roi_pct", "mean"),
        avg_cvr        = ("avg_cvr",     "mean"),
    )
    .round(2)
    .reset_index()
)
summary_path = os.path.join(DATA_DIR, "vibescore_summary.csv")
summary.to_csv(summary_path, index=False)
print(f"summary saved: {summary_path}")
print()
print("VibeScore model complete.")