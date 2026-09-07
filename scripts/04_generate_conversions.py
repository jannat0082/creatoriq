"""
VibeSignal AI - Conversions Data Generator
Generates synthetic purchase records for Indian D2C campaigns.

Creator performance profiles used in this file:
- vanity:    high engagement, lower conversion rate
- converter: moderate engagement, higher conversion rate
- performer: balanced engagement and conversion rate

This dataset is synthetic and intended for portfolio/demo use only.
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

CREATOR_TYPE_WEIGHTS = {
    "vanity":    0.45,
    "converter": 0.35,
    "performer": 0.20,
}

CONVERSION_RATE_BY_TYPE = {
    "vanity":    (0.001, 0.008),
    "converter": (0.025, 0.080),
    "performer": (0.015, 0.045),
}

ORDER_VALUE_MEAN_INR = 1_500
ORDER_VALUE_MIN_INR  = 299
ORDER_VALUE_MAX_INR  = 15_000

# 13-17 excluded from conversions — minors typically cannot purchase
AGE_GROUPS   = ["18-24", "25-34", "35-44", "45-54", "55+"]
GENDERS      = ["male", "female", "non-binary"]
DEVICE_TYPES = ["mobile", "desktop", "tablet"]
DEVICE_WEIGHTS = [0.75, 0.18, 0.07]

INDIAN_CITIES = [
    "Mumbai",    "Delhi",     "Bengaluru", "Hyderabad",
    "Chennai",   "Pune",      "Kolkata",   "Jaipur",
    "Ahmedabad", "Surat",
]


def assign_creator_types(creators_df: pd.DataFrame) -> dict:
    """
    Assign each creator one permanent synthetic performance profile.
    This is a modeling assumption for the demo dataset only.
    """
    types = random.choices(
        population=list(CREATOR_TYPE_WEIGHTS.keys()),
        weights=list(CREATOR_TYPE_WEIGHTS.values()),
        k=len(creators_df),
    )
    return dict(zip(creators_df["creator_id"].astype(int).tolist(), types))


def generate_order_value_inr() -> float:
    """Right-skewed synthetic D2C order values in INR."""
    value = np.random.exponential(ORDER_VALUE_MEAN_INR)
    value = max(ORDER_VALUE_MIN_INR, min(ORDER_VALUE_MAX_INR, value))
    return round(value, 2)


def build_promo_code_lookup(campaign_creators_df: pd.DataFrame) -> dict:
    """
    Map (campaign_id, creator_id) → promo_code.

    A creator can appear in multiple campaigns with different promo codes.
    Keying by creator_id alone would assign the wrong code to earlier
    campaigns — so we use the (campaign, creator) pair instead.
    """
    lookup = {}
    for _, row in campaign_creators_df.iterrows():
        key = (int(row["campaign_id"]), int(row["creator_id"]))
        lookup[key] = row["promo_code"]
    return lookup


def calculate_conversions(
    clicks: int,
    creator_type: str,
    is_campaign_post: bool,
) -> int:
    if clicks <= 0:
        return 0

    lo, hi = CONVERSION_RATE_BY_TYPE[creator_type]
    cvr    = random.uniform(lo, hi)

    # organic posts convert less — no dedicated CTA or offer
    if not is_campaign_post:
        cvr *= 0.60

    return int(clicks * cvr)


def generate_conversions(
    posts_df: pd.DataFrame,
    creators_df: pd.DataFrame,
    campaign_creators_df: pd.DataFrame,
) -> tuple:
    creator_types       = assign_creator_types(creators_df)
    promo_code_lookup   = build_promo_code_lookup(campaign_creators_df)

    rows          = []
    conversion_id = 1

    for _, post in posts_df.iterrows():
        creator_id       = int(post["creator_id"])
        post_id          = int(post["post_id"])
        clicks           = int(post["clicks"])
        posted_at        = pd.to_datetime(post["posted_at"])
        has_campaign     = pd.notna(post["campaign_id"])

        if has_campaign:
            campaign_id = int(post["campaign_id"])
            promo_code  = promo_code_lookup.get((campaign_id, creator_id), pd.NA)
        else:
            campaign_id = pd.NA
            promo_code  = pd.NA

        creator_type     = creator_types.get(creator_id, "vanity")
        num_conversions  = calculate_conversions(clicks, creator_type, has_campaign)

        for _ in range(num_conversions):
            days_after   = random.randint(0, 14)
            converted_at = posted_at + pd.Timedelta(days=days_after)

            rows.append({
                "conversion_id":               conversion_id,
                "post_id":                     post_id,
                "campaign_id":                 campaign_id,
                "creator_id":                  creator_id,
                "creator_performance_profile": creator_type,
                "order_value_inr":             generate_order_value_inr(),
                "promo_code":                  promo_code,
                "age_group":                   random.choice(AGE_GROUPS),
                "gender":                      random.choice(GENDERS),
                "location":                    random.choice(INDIAN_CITIES),
                "device_type":                 random.choices(
                                                   DEVICE_TYPES,
                                                   weights=DEVICE_WEIGHTS,
                                                   k=1,
                                               )[0],
                "converted_at":                converted_at,
            })
            conversion_id += 1

    columns = [
        "conversion_id", "post_id", "campaign_id", "creator_id",
        "creator_performance_profile", "order_value_inr", "promo_code",
        "age_group", "gender", "location", "device_type", "converted_at",
    ]

    return pd.DataFrame(rows, columns=columns), creator_types


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)

    paths = {
        "creators":          os.path.join(DATA_DIR, "creators.csv"),
        "posts":             os.path.join(DATA_DIR, "posts.csv"),
        "campaign_creators": os.path.join(DATA_DIR, "campaign_creators.csv"),
    }

    missing = [p for p in paths.values() if not os.path.exists(p)]
    if missing:
        raise FileNotFoundError(
            "Run earlier generators first. Missing:\n" + "\n".join(missing)
        )

    creators_df          = pd.read_csv(paths["creators"])
    posts_df             = pd.read_csv(paths["posts"])
    campaign_creators_df = pd.read_csv(paths["campaign_creators"])

    conversions_df, creator_types = generate_conversions(
        posts_df, creators_df, campaign_creators_df
    )

    conversions_df["campaign_id"] = conversions_df["campaign_id"].astype("Int64")
    conversions_df["post_id"]     = conversions_df["post_id"].astype("Int64")
    conversions_df["creator_id"]  = conversions_df["creator_id"].astype("Int64")

    print("Conversions shape:", conversions_df.shape)

    total  = conversions_df["order_value_inr"].sum()
    avg    = conversions_df["order_value_inr"].mean()
    print(f"\nTotal synthetic revenue:       ₹{total:,.2f}")
    print(f"Average synthetic order value: ₹{avg:,.2f}  (target ~₹1500)")

    print("\nDevice split:")
    print(
        conversions_df["device_type"]
        .value_counts(normalize=True).mul(100).round(1)
    )

    print("\nTop locations:")
    print(conversions_df["location"].value_counts().head(5))

    conv_by_post = (
        conversions_df.groupby("post_id").size()
        .reset_index(name="conversions")
    )
    perf = posts_df.merge(conv_by_post, on="post_id", how="left")
    perf["conversions"] = perf["conversions"].fillna(0)
    perf["creator_performance_profile"] = perf["creator_id"].map(creator_types)
    perf["cvr"] = perf["conversions"] / perf["clicks"].replace(0, np.nan)

    print("\nAverage CVR by creator profile (vanity lowest, converter highest):")
    print(
        perf.groupby("creator_performance_profile")["cvr"]
        .mean().mul(100).round(3)
        .reindex(["vanity", "converter", "performer"])
    )

    orphan_posts    = (~conversions_df["post_id"].isin(posts_df["post_id"])).sum()
    orphan_creators = (~conversions_df["creator_id"].isin(creators_df["creator_id"])).sum()
    print(f"\nOrphan post refs:    {orphan_posts}  (should be 0)")
    print(f"Orphan creator refs: {orphan_creators} (should be 0)")

    output_path = os.path.join(DATA_DIR, "conversions.csv")
    conversions_df.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")