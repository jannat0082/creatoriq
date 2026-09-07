"""
VibeSignal AI - Posts Data Generator
Generates synthetic post-level engagement metrics derived from
each creator's average engagement rate.

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

POSTS_PER_CREATOR = (3, 8)

CONTENT_FORMATS_BY_PLATFORM = {
    "instagram": ["reel", "story", "image", "carousel"],
    "youtube":   ["short", "video"],
    "twitter":   ["text", "image", "video"],
}

REACH_MULTIPLIER = {
    "instagram": (0.15, 0.45),
    "youtube":   (0.20, 0.65),
    "twitter":   (0.10, 0.35),
}


def get_content_format(platform: str) -> str:
    return random.choice(CONTENT_FORMATS_BY_PLATFORM[platform])


def calculate_post_engagement_rate(
    creator_avg_engagement_rate: float,
    engagement_variance: float,
) -> float:
    """
    Post-level engagement varies around the creator average.
    engagement_variance from creators.csv controls how consistent
    a creator is across posts.
    """
    variation = max(0.10, engagement_variance * 2)
    rate      = creator_avg_engagement_rate + random.uniform(-variation, variation)
    return round(max(0.10, rate), 2)


def split_engagements(
    total_engagements: int,
    content_format: str,
) -> tuple:
    """
    Split engagements into likes, comments, shares, saves.
    Reels and carousels get proportionally more shares/saves.
    """
    if content_format in ["reel", "short", "carousel"]:
        likes_r    = random.uniform(0.68, 0.78)
        comments_r = random.uniform(0.06, 0.12)
        shares_r   = random.uniform(0.07, 0.13)
    else:
        likes_r    = random.uniform(0.72, 0.84)
        comments_r = random.uniform(0.06, 0.12)
        shares_r   = random.uniform(0.03, 0.08)

    likes    = int(total_engagements * likes_r)
    comments = int(total_engagements * comments_r)
    shares   = int(total_engagements * shares_r)
    saves    = max(total_engagements - likes - comments - shares, 0)

    return likes, comments, shares, saves


def calculate_clicks(
    likes: int,
    comments: int,
    shares: int,
    saves: int,
    is_campaign_post: bool,
) -> int:
    """
    Campaign posts generate higher click intent than organic posts.
    """
    total_actions = likes + comments + shares + saves
    click_rate    = random.uniform(0.06, 0.16) if is_campaign_post \
                    else random.uniform(0.01, 0.06)
    return int(total_actions * click_rate)


def generate_posts(
    creators_df: pd.DataFrame,
    campaign_creators_df: pd.DataFrame,
) -> pd.DataFrame:
    rows    = []
    post_id = 1

    creator_campaigns = (
        campaign_creators_df
        .groupby("creator_id")["campaign_id"]
        .apply(list)
        .to_dict()
    )

    for _, creator in creators_df.iterrows():
        creator_id          = int(creator["creator_id"])
        platform            = creator["platform"]
        followers           = int(creator["follower_count"])
        avg_engagement_rate = float(creator["avg_engagement_rate"])
        engagement_variance = float(creator["engagement_variance"])

        if platform not in REACH_MULTIPLIER:
            raise ValueError(
                f"Unsupported platform '{platform}' for creator_id {creator_id}."
            )

        num_posts = random.randint(*POSTS_PER_CREATOR)

        for _ in range(num_posts):
            content_format = get_content_format(platform)

            lo, hi = REACH_MULTIPLIER[platform]
            reach  = max(int(followers * random.uniform(lo, hi)), 1)

            # cap views at reach for non-YouTube to avoid
            # engagement rates that appear > 100%
            if platform == "youtube":
                views = int(reach * random.uniform(0.85, 1.05))
            else:
                views = int(reach * random.uniform(0.75, 1.00))

            campaigns_for_creator = creator_campaigns.get(creator_id, [])
            is_campaign_post      = bool(campaigns_for_creator) and random.random() < 0.70

            campaign_id = random.choice(campaigns_for_creator) \
                          if is_campaign_post else pd.NA

            post_er = calculate_post_engagement_rate(
                creator_avg_engagement_rate=avg_engagement_rate,
                engagement_variance=engagement_variance,
            )

            total_eng = int(reach * (post_er / 100))
            likes, comments, shares, saves = split_engagements(total_eng, content_format)

            clicks = calculate_clicks(
                likes=likes,
                comments=comments,
                shares=shares,
                saves=saves,
                is_campaign_post=is_campaign_post,
            )

            rows.append({
                "post_id":              post_id,
                "creator_id":           creator_id,
                "campaign_id":          campaign_id,
                "platform":             platform,
                "content_format":       content_format,
                "likes":                likes,
                "comments":             comments,
                "shares":               shares,
                "saves":                saves,
                "views":                views,
                "clicks":               clicks,
                "reach":                reach,
                "post_engagement_rate": post_er,
                "posted_at":            fake.date_time_between(
                                            start_date="-1y",
                                            end_date="now",
                                        ),
            })
            post_id += 1

    return pd.DataFrame(rows)


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)

    creators_path          = os.path.join(DATA_DIR, "creators.csv")
    campaign_creators_path = os.path.join(DATA_DIR, "campaign_creators.csv")

    for path in [creators_path, campaign_creators_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} not found. Run earlier scripts first.")

    creators_df          = pd.read_csv(creators_path)
    campaign_creators_df = pd.read_csv(campaign_creators_path)

    posts_df = generate_posts(creators_df, campaign_creators_df)

    print("Posts shape:", posts_df.shape)

    orphan_c = (~posts_df["creator_id"].isin(creators_df["creator_id"])).sum()
    print(f"Orphan creator refs:  {orphan_c} (should be 0)")

    valid_ids   = set(campaign_creators_df["campaign_id"].unique())
    has_camp    = posts_df["campaign_id"].notna()
    orphan_camp = (has_camp & ~posts_df.loc[has_camp, "campaign_id"].isin(valid_ids)).sum()
    print(f"Orphan campaign refs: {orphan_camp} (should be 0)")

    dup_ids = posts_df["post_id"].duplicated().sum()
    print(f"Duplicate post IDs:   {dup_ids} (should be 0)")

    organic_pct = posts_df["campaign_id"].isna().mean() * 100
    print(f"Organic posts:        {organic_pct:.1f}%")

    posts_df["computed_er"] = (
        (posts_df["likes"] + posts_df["comments"] +
         posts_df["shares"] + posts_df["saves"])
        / posts_df["reach"] * 100
    )
    comparison = (
        posts_df.merge(creators_df[["creator_id", "avg_engagement_rate"]], on="creator_id")
        .groupby("creator_id")
        .agg(stated=("avg_engagement_rate", "first"),
             actual=("computed_er", "mean"))
        .head(5)
    )
    print("\nStated vs actual engagement rate (first 5 creators):")
    print(comparison.round(2))

    print("\nAverage engagement rate by content format:")
    print(
        posts_df.groupby("content_format")["computed_er"]
        .mean().sort_values(ascending=False).round(2)
    )

    posts_df = posts_df.drop(columns=["computed_er"])

    posts_df["campaign_id"] = posts_df["campaign_id"].astype("Int64")

    output_path = os.path.join(DATA_DIR, "posts.csv")
    posts_df.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")