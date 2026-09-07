"""
VibeSignal AI - Audience Demographics Generator
Generates synthetic creator audience breakdowns by age group,
gender, and Indian state.

Each creator receives:
- 6 age-group rows
- 3 gender rows
- 8 state rows
Total: 17 rows per creator × 200 creators = 3,400 rows

Percentage shares within each demographic_type sum to exactly 100.
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

AGE_GROUPS = ["13-17", "18-24", "25-34", "35-44", "45-54", "55+"]
GENDERS    = ["male", "female", "non-binary"]

INDIAN_STATES = [
    "Maharashtra", "Karnataka",   "Delhi",
    "Tamil Nadu",  "Telangana",   "Gujarat",
    "Rajasthan",   "West Bengal",
]

NICHE_AGE_WEIGHTS = {
    "gaming":  [0.25, 0.35, 0.20, 0.10, 0.06, 0.04],
    "beauty":  [0.10, 0.30, 0.30, 0.15, 0.10, 0.05],
    "fitness": [0.05, 0.25, 0.35, 0.20, 0.10, 0.05],
    "finance": [0.02, 0.10, 0.30, 0.30, 0.18, 0.10],
    "travel":  [0.05, 0.20, 0.30, 0.25, 0.15, 0.05],
    "food":    [0.08, 0.22, 0.28, 0.22, 0.12, 0.08],
    "fashion": [0.12, 0.32, 0.28, 0.15, 0.08, 0.05],
    "tech":    [0.08, 0.28, 0.32, 0.20, 0.08, 0.04],
}

DEFAULT_AGE_WEIGHTS = [0.10, 0.25, 0.28, 0.20, 0.12, 0.05]

NICHE_GENDER_WEIGHTS = {
    "beauty":  [0.20, 0.72, 0.08],
    "fashion": [0.20, 0.72, 0.08],
    "gaming":  [0.62, 0.30, 0.08],
    "tech":    [0.62, 0.30, 0.08],
    "finance": [0.62, 0.30, 0.08],
    "fitness": [0.45, 0.48, 0.07],
    "travel":  [0.45, 0.48, 0.07],
    "food":    [0.45, 0.48, 0.07],
}

DEFAULT_GENDER_WEIGHTS = [0.45, 0.48, 0.07]

# metro-heavy distribution for Indian D2C audiences
STATE_WEIGHTS = [
    0.20,  # Maharashtra
    0.15,  # Karnataka
    0.14,  # Delhi
    0.12,  # Tamil Nadu
    0.10,  # Telangana
    0.10,  # Gujarat
    0.09,  # Rajasthan
    0.10,  # West Bengal
]


def generate_percentage_distribution(
    base_weights: list,
    noise_limit: float = 0.05,
) -> list:
    """
    Add controlled noise to base weights and return a list
    of percentages that sum to exactly 100.00.
    """
    noisy = [
        max(0.01, w + random.uniform(-noise_limit, noise_limit))
        for w in base_weights
    ]
    total       = sum(noisy)
    percentages = [round((w / total) * 100, 2) for w in noisy]

    # fix floating-point rounding so sum is exactly 100
    diff            = round(100.0 - sum(percentages), 2)
    percentages[-1] = round(percentages[-1] + diff, 2)

    return percentages


def generate_audience_demographics(creators_df: pd.DataFrame) -> pd.DataFrame:
    rows           = []
    demographic_id = 1

    for _, creator in creators_df.iterrows():
        creator_id  = int(creator["creator_id"])
        niche       = creator["niche"]
        recorded_at = fake.date_between(start_date="-6m", end_date="today")

        # --- age group rows ---
        age_weights  = NICHE_AGE_WEIGHTS.get(niche, DEFAULT_AGE_WEIGHTS)
        age_pcts     = generate_percentage_distribution(age_weights, noise_limit=0.04)

        for age_group, pct in zip(AGE_GROUPS, age_pcts):
            rows.append({
                "demographic_id":    demographic_id,
                "creator_id":        creator_id,
                "demographic_type":  "age_group",
                "demographic_value": age_group,
                "percentage_share":  pct,
                "recorded_at":       recorded_at,
            })
            demographic_id += 1

        # --- gender rows ---
        gender_weights = NICHE_GENDER_WEIGHTS.get(niche, DEFAULT_GENDER_WEIGHTS)
        gender_pcts    = generate_percentage_distribution(gender_weights, noise_limit=0.03)

        for gender, pct in zip(GENDERS, gender_pcts):
            rows.append({
                "demographic_id":    demographic_id,
                "creator_id":        creator_id,
                "demographic_type":  "gender",
                "demographic_value": gender,
                "percentage_share":  pct,
                "recorded_at":       recorded_at,
            })
            demographic_id += 1

        # --- state rows ---
        state_pcts = generate_percentage_distribution(STATE_WEIGHTS, noise_limit=0.04)

        for state, pct in zip(INDIAN_STATES, state_pcts):
            rows.append({
                "demographic_id":    demographic_id,
                "creator_id":        creator_id,
                "demographic_type":  "state",
                "demographic_value": state,
                "percentage_share":  pct,
                "recorded_at":       recorded_at,
            })
            demographic_id += 1

    return pd.DataFrame(rows)


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)

    creators_path = os.path.join(DATA_DIR, "creators.csv")
    if not os.path.exists(creators_path):
        raise FileNotFoundError(
            "creators.csv not found. Run 01_generate_creators.py first."
        )

    creators_df = pd.read_csv(creators_path)

    required = {"creator_id", "niche"}
    missing  = required - set(creators_df.columns)
    if missing:
        raise ValueError(f"creators.csv missing columns: {sorted(missing)}")

    demo_df = generate_audience_demographics(creators_df)

    print("Audience demographics shape:", demo_df.shape)

    expected_rows = len(AGE_GROUPS) + len(GENDERS) + len(INDIAN_STATES)
    rows_per_creator = demo_df.groupby("creator_id").size()
    wrong_counts     = (rows_per_creator != expected_rows).sum()
    print(f"Creators with wrong row count: {wrong_counts} (should be 0, expected {expected_rows} each)")

    pct_sums = (
        demo_df.groupby(["creator_id", "demographic_type"])["percentage_share"].sum()
    )
    invalid = (abs(pct_sums - 100) > 0.01).sum()
    print(f"Groups not summing to 100: {invalid} (should be 0)")

    orphans = (~demo_df["creator_id"].isin(creators_df["creator_id"])).sum()
    print(f"Orphan creator refs: {orphans} (should be 0)")

    print("\nAverage 18-24 share by niche:")
    print(
        demo_df[
            (demo_df["demographic_type"]  == "age_group") &
            (demo_df["demographic_value"] == "18-24")
        ]
        .merge(creators_df[["creator_id", "niche"]], on="creator_id")
        .groupby("niche")["percentage_share"]
        .mean().sort_values(ascending=False).round(1)
    )

    print("\nAverage share by state:")
    print(
        demo_df[demo_df["demographic_type"] == "state"]
        .groupby("demographic_value")["percentage_share"]
        .mean().sort_values(ascending=False).round(1)
    )

    output_path = os.path.join(DATA_DIR, "audience_demographics.csv")
    demo_df.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")