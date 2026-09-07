# VibeSignal AI — Metrics Dictionary

**Version:** 1.0
**Last Updated:** 31 August 2026
**Maintained by:** Jannat

## ✶ Purpose

This dictionary defines the core data fields, calculated metrics, and business measures used across the VibeSignal AI analytics pipeline.

VibeSignal AI is an **India-first creator intelligence and campaign analytics platform for D2C brands**. The dataset is synthetic and designed for portfolio and analytical demonstration purposes.

The dictionary establishes a consistent definition for each metric so that the same business question produces the same result across Python, SQL, and Power BI.



# ✶ Data Model

The analytical model consists of seven core tables:

* **creators** — creator profiles and performance attributes
* **brands** — brand and audience information
* **campaigns** — campaign objectives, budgets, and targeting
* **campaign_creators** — creator–campaign partnerships and attribution
* **posts** — content-level performance
* **conversions** — customer purchases and revenue
* **audience_demographics** — creator audience composition

The `campaign_creators` table acts as the bridge between creators and campaigns and is central to campaign-level attribution.



# ✶ Core Creator Metrics

### `creator_id`

Unique identifier for each creator.

### `platform`

Primary social platform. Values include Instagram, YouTube, and Twitter.

### `niche`

Creator's primary content category, including fitness, beauty, gaming, finance, travel, food, fashion, and technology.

### `tier`

Creator classification based primarily on follower count:

| Tier  | Followers |
| ----- | --------: |
| Nano  |    1K–10K |
| Micro |  10K–100K |
| Macro |   100K–1M |
| Mega  |       1M+ |

Tier is used to analyse differences in reach, engagement, cost, and commercial performance.

### `follower_count`

Synthetic follower base associated with the creator.

### `avg_engagement_rate`

Creator-level baseline engagement rate. This represents the creator's typical performance and is distinct from individual post engagement.

### `estimated_cost_inr`

Estimated creator collaboration cost before negotiation.

### `primary_language`

Primary audience/content language, including Hindi, English, Hinglish, Gujarati, Marathi, Tamil, and Telugu.

### `city_tier`

Creator's city classification: Tier 1, Tier 2, or Tier 3.



# ✶ Creator Authenticity Metrics

### `follower_growth_spike`

Binary indicator identifying unusual recent follower growth.

### `comment_like_ratio`

Ratio of comments to likes. Very low ratios may indicate potentially low-quality or artificial engagement.

### `engagement_variance`

Measure of variation in post-level engagement. Higher variance is treated as a potential risk signal.

### `authenticity_risk_score`

Composite risk indicator ranging from 0–100.

**Logic:**

* Follower growth spike → +35
* Comment/like ratio below 0.02 → +20
* Engagement variance above 0.35 → +20
* Random noise → 0–20
* Maximum score → 100

### `authenticity_risk_level`

| Score | Level  |
| ----: | ------ |
|   <35 | Low    |
| 35–64 | Medium |
|   65+ | High   |

### `audience_authenticity_score`

Calculated as:

`100 − authenticity_risk_score`

This is the positive representation of the same underlying signal and should not be combined with the risk score as a separate VibeScore input.

> **Analytical note:** The authenticity score is a prototype indicator for demonstration purposes, not a validated fraud-detection model.



# ✶ Campaign Metrics

### `campaign_id`

Unique identifier for each campaign.

### `objective`

Campaign objective:

* Awareness
* Engagement
* Traffic
* Sales

### `target_segment`

Primary customer segment targeted by the campaign.

### `target_age_group`

Target customer age group: 18–24, 25–34, or 35–44.

### `target_niche`

Content category aligned with the campaign's business objective.

### `preferred_platform`

Primary platform selected for the campaign.

### `preferred_creator_tier`

Preferred creator size: Nano, Micro, Macro, or Mixed.

### `total_budget_inr`

Total campaign budget in Indian Rupees.

### `status`

Campaign lifecycle state: Draft, Active, Completed, or Paused.



# ✶ Creator–Campaign Partnership Metrics

The `campaign_creators` table represents the relationship between a creator and a campaign.

### `creator_fee_inr`

Negotiated creator fee for a specific partnership.

The synthetic fee is based on the creator's estimated cost with a ±15% negotiation range.

### `revenue_attributed_inr`

Revenue attributed to the creator–campaign partnership.

For the synthetic dataset, revenue is generated using a revenue multiple against creator fees.

In a production environment, this would be calculated from actual attributed conversions.

### `impressions_delivered`

Estimated campaign impressions:

`follower_count × platform reach factor`

### `estimated_engagements`

Estimated engagements:

`impressions_delivered × avg_engagement_rate`

### `promo_code`

Unique code assigned to each creator–campaign partnership.

This is the primary attribution key connecting conversions to a specific creator and campaign.

**Important:** attribution should use the creator–campaign relationship, not `creator_id` alone, because one creator can participate in multiple campaigns.



# ✶ Content Performance Metrics

### `reach`

Estimated number of unique users reached by a post.

### `views`

Estimated content views based on platform-specific viewing behaviour.

### `likes`

Number of post likes.

### `comments`

Number of post comments.

### `shares`

Number of post shares.

### `saves`

Residual engagement after likes, comments, and shares.

### `clicks`

Estimated users clicking through from the content.

Campaign posts use a higher click-intent assumption than organic posts.

### `post_engagement_rate`

Post-level engagement rate calculated using the creator's baseline engagement with controlled variation.

This should not be confused with the creator-level `avg_engagement_rate`.

### `content_format`

Platform-specific content format such as Reel, Story, Image, Carousel, Short, Video, or Text.



# ✶ Conversion & Revenue Metrics

### `conversion_id`

Unique identifier for each conversion.

### `order_value_inr`

Purchase value associated with a conversion.

### `promo_code`

Code used at checkout to attribute a purchase to the relevant creator–campaign partnership.

### `creator_performance_profile`

Creator classification based on commercial behaviour:

* **Vanity** — strong surface-level engagement but weaker commercial outcomes
* **Converter** — stronger conversion efficiency
* **Performer** — strong overall commercial performance

### `age_group`

Customer age segment.

### `gender`

Customer gender category.

### `location`

Customer city in India.

### `device_type`

Customer device used for conversion: Mobile, Desktop, or Tablet.

### `converted_at`

Timestamp of the customer conversion.




# ✶ Audience Metrics

### `demographic_type`

Type of audience attribute:

* Age group
* Gender
* State

### `demographic_value`

Specific demographic category.

### `percentage_share`

Percentage of the creator's audience belonging to the selected demographic.

For each creator and demographic type:

`SUM(percentage_share) = 100%`

### `recorded_at`

Date of the audience snapshot.



# ✶ VibeScore Framework

**VibeScore** is the primary creator-ranking metric in VibeSignal AI.

It is designed to measure **commercial creator quality rather than audience size alone**.

The score combines five dimensions:

| Dimension    | Weight |
| ------------ | -----: |
| ROI          |    35% |
| Conversion   |    25% |
| Authenticity |    15% |
| Audience Fit |    15% |
| Engagement   |    10% |

### ROI Score

Creator ROI:

`(Revenue Attributed − Creator Fee) / Creator Fee × 100`

The resulting value is min-max normalized to a 0–100 score.

### Conversion Score

Creator-level average conversion rate is calculated from post-level CVR:

`CVR = Conversions / Clicks × 100`

The result is normalized to 0–100.

### Authenticity Score

Based on the normalized audience authenticity measure.

### Audience Fit Score

Measures the creator's audience share within the core D2C buyer segment:

`18–24 audience share + 25–34 audience share`

The result is normalized to 0–100.

### Engagement Score

Based on the creator's average engagement rate and normalized to 0–100.

### Final VibeScore

`VibeScore = (ROI × 0.35) + (Conversion × 0.25) + (Authenticity × 0.15) + (Audience Fit × 0.15) + (Engagement × 0.10)`

**Range:** 0–100

The weighting intentionally gives **60% combined weight to ROI and conversion**, while engagement contributes only 10%.

### Recommendation

| VibeScore | Recommendation |
| --------: | -------------- |
|       ≥75 | Scale          |
|     50–74 | Watch          |
|     25–49 | Improve        |
|       <25 | Stop           |



# ✶ Campaign Performance Metrics

### Campaign ROI %

`(Total Attributed Revenue − Total Creator Fees) / Total Creator Fees × 100`

Measures the return generated relative to creator fees.

This calculation excludes production, management, and paid-media costs.

### Budget Efficiency

`Total Attributed Revenue / Total Creator Fees`

Example: a value of **2.1** means every ₹1 spent on creator fees generated ₹2.10 in attributed revenue.

### Portfolio ROI %

`(Total Attributed Revenue − Total Creator Fees) / Total Creator Fees × 100`

Portfolio ROI uses a **ratio-of-sums** approach rather than averaging individual campaign ROI percentages. This prevents smaller campaigns from receiving disproportionate influence.



# ✶ Post & Conversion Metrics

### Post CVR

`Conversions / Clicks × 100`

Posts with zero clicks are excluded from CVR calculations.

### Average CVR

Mean post-level CVR for a creator.

Each post contributes one observation, preventing high-volume campaigns from automatically dominating the creator average.

### Average Order Value

`Total Revenue / Total Conversions`

Can be analysed globally or across segments such as creator tier, city, campaign, or device.



# ✶ Power BI Measures

### Total Revenue INR

`SUM(Fact_Conversions[order_value_inr])`

Total purchase value under the current filter context.

### Total Conversions

`COUNTROWS(Fact_Conversions)`

Total number of conversions.

### Average Order Value INR

`Total Revenue INR / Total Conversions`

### Average Engagement Rate

Average of creator-level engagement rates.

The measure is creator-weighted rather than post-weighted so creators with more published content do not automatically receive greater influence.

### Campaign ROI %

`(Revenue Attributed − Creator Fees) / Creator Fees × 100`

### Portfolio ROI %

Portfolio-level ratio of total attributed revenue to total creator fees.

The metric should not be calculated as the simple average of campaign ROI percentages because campaign sizes differ.

### Rolling 3-Month Revenue

Uses the latest three-month period from the date dimension and requires an active relationship between the date table and conversion date.

### Portfolio Health Score

`(Watch Creators × 2 + Scale Creators × 3) / (Improve Creators + Stop Creators + High Risk Creators + 1)`

Higher values indicate a healthier creator portfolio.



# ✶ Business Glossary

**Creator Tier**
Creator classification based on follower scale.

**Vanity Metrics**
Surface-level indicators such as followers, likes, and engagement that may not reflect commercial performance.

**Vanity Metrics Trap**
Selecting creators primarily on engagement or audience size while overlooking conversion and revenue contribution.

**Attribution**
Connecting a customer purchase to the marketing activity responsible for the conversion.

**CVR — Conversion Rate**
Percentage of clicks that result in a purchase.

**ROI — Return on Investment**
Return generated relative to creator fees:

`(Revenue − Cost) / Cost × 100`

**Promo Code**
Unique identifier connecting a customer purchase to a creator–campaign partnership.

**D2C — Direct-to-Consumer**
Business model where brands sell directly to customers without traditional retail intermediaries.

**VibeScore**
VibeSignal AI's 0–100 commercial creator score, combining ROI, conversion, authenticity, audience fit, and engagement.



## ✶ Analytical Principle

VibeSignal AI is designed around a simple principle:

 **Creator selection should be driven by commercial performance, audience relevance, and authenticity—not follower count alone.**

The analytics layer therefore prioritizes **ROI and conversion outcomes** while using engagement, audience fit, and authenticity as supporting signals.
