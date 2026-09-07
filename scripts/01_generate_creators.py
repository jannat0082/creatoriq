"""
VibeSignal AI - Creator Data Generator
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

NUM_CREATORS = 200

TIER_WEIGHTS = {
    "nano":  0.50,
    "micro": 0.30,
    "macro": 0.15,
    "mega":  0.05,
}

TIER_CONFIG = {
    "nano": {
        "followers":  (1_000, 10_000),
        "engagement": (6.0, 10.0),
        "cost_inr":   (1_500, 8_000),
    },
    "micro": {
        "followers":  (10_000, 100_000),
        "engagement": (3.0, 6.0),
        "cost_inr":   (8_000, 35_000),
    },
    "macro": {
        "followers":  (100_000, 1_000_000),
        "engagement": (1.0, 3.0),
        "cost_inr":   (35_000, 200_000),
    },
    "mega": {
        "followers":  (1_000_000, 5_000_000),
        "engagement": (0.5, 1.5),
        "cost_inr":   (200_000, 1_000_000),
    },
}


PLATFORMS = ["instagram", "youtube", "twitter"]

NICHES = [
    "fitness", "beauty", "gaming", "finance",
    "travel", "food",   "fashion", "tech",
]

INDIAN_LANGUAGES = [
    "Hindi", "English", "Hinglish",
    "Gujarati", "Marathi", "Tamil", "Telugu",
]

CITY_TIERS = ["Tier 1", "Tier 2", "Tier 3"]


def create_handle(name: str) -> str:
    clean = name.lower().replace(" ", "_").replace(".", "")
    return f"@{clean}{random.randint(1, 999)}"


def calculate_authenticity_risk(
    follower_growth_spike: int,
    comment_like_ratio: float,
    engagement_variance: float,
) -> int:
    """
    Synthetic risk score from 0 to 100.
    Prototype only — not a verified fake-engagement detector.
    audience_authenticity_score = 100 - authenticity_risk_score.
    Use only one of these two in the VibeScore model to avoid
    double-counting the same signal.
    """
    risk_points = 0

    if follower_growth_spike == 1:
        risk_points += 35

    if comment_like_ratio < 0.02:
        risk_points += 20

    if engagement_variance > 0.35:
        risk_points += 20

    risk_points += random.randint(0, 20)

    return min(100, risk_points)


def get_risk_level(risk_score: int) -> str:
    if risk_score < 35:
        return "low"
    if risk_score < 65:
        return "medium"
    return "high"


def generate_creators(n: int = NUM_CREATORS) -> pd.DataFrame:
    rows = []

    tiers = random.choices(
        population=list(TIER_WEIGHTS.keys()),
        weights=list(TIER_WEIGHTS.values()),
        k=n,
    )

    for i in range(n):
        tier   = tiers[i]
        config = TIER_CONFIG[tier]

        follower_count      = random.randint(*config["followers"])
        avg_engagement_rate = round(random.uniform(*config["engagement"]), 2)
        estimated_cost_inr  = random.randint(*config["cost_inr"])

        follower_growth_spike = random.choice([0, 0, 0, 0, 1])
        comment_like_ratio    = round(random.uniform(0.01, 0.12), 3)
        engagement_variance   = round(random.uniform(0.05, 0.50), 2)

        authenticity_risk_score = calculate_authenticity_risk(
            follower_growth_spike=follower_growth_spike,
            comment_like_ratio=comment_like_ratio,
            engagement_variance=engagement_variance,
        )

        audience_authenticity_score = 100 - authenticity_risk_score
        authenticity_risk_level     = get_risk_level(authenticity_risk_score)

        name   = fake.name()
        handle = create_handle(name)

        rows.append({
            "creator_id":                  i + 1,
            "name":                        name,
            "handle":                      handle,
            "platform":                    random.choice(PLATFORMS),
            "niche":                       random.choice(NICHES),
            "tier":                        tier,
            "follower_count":              follower_count,
            "avg_engagement_rate":         avg_engagement_rate,
            "estimated_cost_inr":          estimated_cost_inr,
            "country":                     "India",
            "primary_language":            random.choice(INDIAN_LANGUAGES),
            "city_tier":                   random.choice(CITY_TIERS),
            "follower_growth_spike":       follower_growth_spike,
            "comment_like_ratio":          comment_like_ratio,
            "engagement_variance":         engagement_variance,
            "authenticity_risk_score":     authenticity_risk_score,
            "authenticity_risk_level":     authenticity_risk_level,
            "audience_authenticity_score": audience_authenticity_score,
            "joined_date":                 fake.date_between(
                                               start_date="-3y",
                                               end_date="-3m",
                                           ),
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)

    df = generate_creators()

    print("Shape:", df.shape)

    print("\nTier distribution:")
    print(df["tier"].value_counts())

    print("\nAverage engagement rate by tier (%):")
    print(
        df.groupby("tier")["avg_engagement_rate"]
        .mean()
        .reindex(["nano", "micro", "macro", "mega"])
        .round(2)
    )

    print("\nAverage estimated cost by tier (INR):")
    print(
        df.groupby("tier")["estimated_cost_inr"]
        .mean()
        .reindex(["nano", "micro", "macro", "mega"])
        .round()
    )

    print("\nAuthenticity risk distribution:")
    print(df["authenticity_risk_level"].value_counts())

    print("\nPlatform distribution:")
    print(df["platform"].value_counts())

    print("\nSample rows:")
    print(df.head(3).to_string())

    output_path = os.path.join(DATA_DIR, "creators.csv")
    df.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")