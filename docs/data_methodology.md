# Data Methodology

### VibeSignal AI — ETL Pipeline, Dimensional Model & Data Generation Logic

*For metric definitions and schema references, see [metrics_dictionary.md](metrics_dictionary.md).*
*For implementation issues and fixes, see [learning_journal.md](learning_journal.md).*



## ✶ Design Intent

VibeSignal AI was designed around a practical business question:

**Does creator engagement translate into purchase performance?**

Follower count and engagement rate are widely used for creator selection, but neither directly measures commercial impact. To evaluate this gap, the dataset needed creator-level conversion, revenue attribution, campaign economics, and audience information.

Because campaign-level creator performance data is generally proprietary, VibeSignal AI uses **synthetic data calibrated to published industry benchmarks**. Creator performance archetypes are defined before conversion events are generated, allowing the analysis to test the relationship between engagement and conversion within a controlled data environment.

The dataset is therefore synthetic, but its structure and parameter ranges are designed to represent realistic Indian D2C creator-marketing scenarios.



## ✶ ETL Architecture

```text
┌─────────────────────────────────────────────────────┐
│ EXTRACT                                             │
│ Faker (en_IN) + NumPy + seeded random generation   │
│ Benchmark ranges → creator and campaign parameters  │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ TRANSFORM                                           │
│ Scripts 01–05 → entities, relationships, events     │
│ Scripts 07–08 → VibeScore and budget allocation     │
│ Validation → referential + business-rule checks     │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ LOAD                                                │
│ CSV → Supabase PostgreSQL                            │
│ vibe_scores.csv → Power BI                           │
│ Excel report → openpyxl                              │
└─────────────────────────────────────────────────────┘
```

The generation workflow follows the dependency sequence:

**01 → 02 → 03 → 04 → 05**

Scripts 06–08 operate after the core dataset has been generated.

A fixed random seed (`42`) is used across Python's random module, NumPy, and Faker to ensure reproducible outputs within the same Python and library environment.



## ✶ Dimensional Model

The analytical model follows a **star-schema approach**, separating descriptive dimensions from transactional facts.

### Dimension Tables

* `creators` — creator profile, tier, platform, niche and authenticity attributes
* `brands` — brand and industry information
* `campaigns` — campaign objectives, budgets, dates and targeting criteria
* `audience_demographics` — creator audience composition in long format

### Fact Tables

* `campaign_creators` — creator-campaign partnerships and financial performance
* `posts` — individual content performance
* `conversions` — individual purchase events

| Fact Table          | Grain                            | Primary Analytical Use             |
| ------------------- | -------------------------------- | ---------------------------------- |
| `campaign_creators` | One creator-campaign partnership | Creator economics and ROI          |
| `posts`             | One published post               | Engagement and click performance   |
| `conversions`       | One purchase event               | CVR, revenue and customer analysis |

The **purchase-event grain** of the conversions table is a key modeling decision. It enables analysis at creator, campaign, post, demographic, device and time levels rather than limiting analysis to campaign-level totals.



## ✶ Data Generation Logic

###  Creators

Creator tiers are generated using an Indian creator-economy distribution:

| Tier  | Share | Followers | Engagement Rate |
| ----- | ----: | --------: | --------------: |
| Nano  |   50% |    1K–10K |       6.0–10.0% |
| Micro |   30% |  10K–100K |        3.0–6.0% |
| Macro |   15% |   100K–1M |        1.0–3.0% |
| Mega  |    5% |     1M–5M |        0.5–1.5% |

Creator profiles also include authenticity indicators such as:

* Follower growth spikes
* Comment-to-like ratio
* Engagement variance
* Authenticity risk score

These signals are combined into a rule-based risk score. In a production environment, these attributes would be derived from platform/API data rather than generated synthetically.



###  Campaigns & Partnerships

Campaigns are generated across three budget bands:

| Campaign Size | Share |    Budget |
| ------------- | ----: | --------: |
| Small         |   55% |  ₹50K–₹3L |
| Mid           |   35% |  ₹3L–₹10L |
| Large         |   10% | ₹10L–₹20L |

Creator selection first applies **niche and platform compatibility**, followed by the campaign's preferred creator tier where applicable. A fallback to the wider creator pool prevents overly restrictive targeting rules from producing unassigned campaigns.

Creator fees are generated around the estimated creator rate card:

`creator_fee = estimated_cost × uniform(0.85, 1.15)`

A budget validation step ensures allocated creator fees remain within the campaign budget.



###  Posts

Post performance is derived from creator-level engagement characteristics rather than generated independently.

The core relationship is:

`total_engagements = reach × post_engagement_rate`

Engagements are then distributed across likes, comments, shares and saves based on content format and platform characteristics.

Campaign posts receive higher click-rate assumptions than organic content because they include a defined call-to-action.

This preserves a logical relationship between **creator → content → engagement → clicks**.



###  Conversions

Creators are assigned one performance archetype before conversion events are generated:

| Archetype | Share | CVR Range | Profile                                   |
| --------- | ----: | --------: | ----------------------------------------- |
| Vanity    |   45% |  0.1–0.8% | High engagement, low purchase intent      |
| Converter |   35% |  2.5–8.0% | Moderate engagement, high purchase intent |
| Performer |   20% |  1.5–4.5% | Balanced performance                      |

The archetype remains consistent across campaigns, representing a creator's underlying audience purchase behavior within the synthetic model.

Order values follow a right-skewed distribution with a mean around ₹1,500, bounded between ₹299 and ₹15,000. This produces a more realistic revenue distribution than a uniform model.

### Attribution

Creator attribution uses the composite key:

`(campaign_id, creator_id)`

This is important because the same creator can participate in multiple campaigns and receive different promotional codes. Using `creator_id` alone would create incorrect revenue attribution.



###  Audience Demographics

Audience demographics are stored in **long format**, with demographic records grouped by creator and demographic type.

The dataset contains:

* 6 age groups
* 3 gender categories
* 8 Indian states

Shares are generated using niche-specific base distributions with controlled variation and normalised to **100% within each creator and demographic type**.

The long-format structure provides greater flexibility for filtering, aggregation and future demographic expansion than a wide table containing separate columns for every category.



## ✶ Validation Protocol

Validation is performed before each dataset is written to disk.

Key checks include:

| Validation                           | Expected Result |
| ------------------------------------ | --------------: |
| Orphan foreign keys                  |               0 |
| Duplicate unique keys                |               0 |
| Nulls in required fields             |               0 |
| Budget violations                    |               0 |
| Invalid date sequences               |               0 |
| Demographic shares not equal to 100% |               0 |

Validation results are printed during execution. Non-zero results are surfaced as warnings before data is loaded into Supabase.

This provides a basic data-quality layer between generation and analytics.



## ✶ Power BI Data Model

Power BI combines the Supabase tables with `vibe_scores.csv`, which is generated separately from the creator-performance scoring process.

The model uses:

* Dimension-to-fact relationships for filtering
* A dedicated `Dim_Date` table for time intelligence
* Active relationships for primary analytical paths
* Inactive relationships where alternative date/filter paths could introduce ambiguity

`Dim_Date` covers **January 2024 through December 2026** and is configured as the model's date table.

The primary date relationship is connected to conversion events, while post-level date analysis can use the corresponding inactive relationship when required through DAX.



## ✶ Analytical Design Principle

The methodology follows one central principle:

 **Creator scale should not be treated as a substitute for creator performance.**

The pipeline therefore preserves the complete analytical chain:

**Creator → Campaign → Content → Click → Conversion → Revenue**

This structure allows VibeSignal AI to evaluate creators using commercial outcomes alongside engagement, audience fit and authenticity rather than relying on follower count or engagement rate alone.

The resulting dataset supports the Power BI analysis, VibeScore framework, campaign planning and creator recommendations presented elsewhere in the project.




