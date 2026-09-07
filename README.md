## ✶ Overview

Selecting the right creators is one of the most important decisions in influencer marketing. Most existing platforms provide campaign analytics after a campaign ends, which is useful for reporting but not for planning. VibeSignal AI shifts creator marketing from intuition-based selection to data-driven decision-making by helping brands evaluate creators, compare campaign strategies, and optimize marketing budgets before campaign execution.

## ✶ Business Objective

The objective of VibeSignal AI is to help Indian D2C brands maximize campaign ROI by selecting the right creators and allocating budgets intelligently before campaigns begin. Instead of relying only on follower count or engagement, the platform evaluates creators using multiple business dimensions and recommends the most suitable creator strategy for a fixed campaign budget.

## ✶ Problem Statement

Brands often need to answer questions such as:
- Which creators should we collaborate with?
- How should we distribute our campaign budget?
- Should we invest in nano, micro, or mixed creators?
- Which creators provide the highest business value?

Most influencer marketing platforms focus on post-campaign reporting instead of helping businesses make these decisions beforehand. This creates inefficient budget allocation and increases marketing risk.

## ✶ Solution
VibeSignal AI provides an end-to-end decision-support system for creator selection and budget planning.

The platform enables businesses to:
- Evaluate creators using the VibeScore framework.
- Compare nano, micro, and mixed creator strategies.
- Estimate budget allocation options.
- Identify risky or low-authenticity creators.
- Analyze engagement and conversion performance.
- Generate executive reports and interactive dashboards.

Instead of relying on intuition, brands can use transparent analytics to select creators and optimize marketing investments.

##  ✶ Methodology

The project follows a complete analytics workflow:

1. Generate realistic creator marketing datasets.
2. Store structured data in PostgreSQL on Supabase.
3. Clean and validate the datasets.
4. Perform exploratory data analysis (EDA).
5. Analyze creator performance and audience behavior.
6. Calculate VibeScore for each creator.
7. Generate KPI reports.
8. Visualize insights using Power BI.
9. Support data-driven creator selection and budget planning.

## ✶ Core Insight

The analysis shows that nano creators can generate significantly higher engagement, while larger creators may deliver stronger conversion performance. This makes engagement-only evaluation insufficient for ROI-focused campaigns. VibeSignal AI is designed to support more balanced creator selection by considering both engagement quality and conversion potential.

## ✶ VibeScore Framework

VibeScore assigns each creator a score from 0 to 100 across five dimensions.

| Dimension | Weight | Purpose |
|---|---:|---|
| Audience Fit | 30% | Measures how well the creator reaches the intended audience. |
| Engagement Quality | 25% | Evaluates whether followers are genuinely interacting with the content. |
| Content Relevance | 20% | Assesses how closely the content aligns with the brand category. |
| Cost Efficiency | 15% | Measures value delivered per rupee spent. |
| Authenticity Risk | 10% | Flags possible signs of fake or low-quality engagement. |

### ✶ Score Bands
- **75–100**: Scale — increase investment.
- **50–74**: Watch — monitor closely.
- **25–49**: Improve — refine the partnership strategy.
- **0–24**: Stop — exit the partnership.

> VibeScore is a prototype decision framework. Weights are configurable and intentionally transparent.

## ✶ Tech Stack

| Component | Technology |
|---|---|
| Database | PostgreSQL on Supabase |
| Data Generation | Python, Faker, Pandas, NumPy |
| Analysis | Jupyter Notebook, Matplotlib, Seaborn |
| Scoring Model | Python-based weighted algorithm |
| Risk Indicator | Rule-based signal detection |
| Reporting | openpyxl |
| Dashboard | Power BI |


## ✶ Data & Schema

The database contains 5,165 rows across 7 tables.

| Table | Rows | Description |
|---|---:|---|
| brands | 15 | D2C brand profiles |
| creators | 200 | Creator profiles with tier and engagement data |
| campaigns | 70 | Campaign budgets, objectives, and dates |
| campaign_creators | 460 | Creator assignments and fees |
| posts | 783 | Content metrics such as likes, views, clicks, and reach |
| conversions | 2,437 | Purchases attributed to promo codes |
| audience_demographics | 1,200 | Audience breakdown by creator |



## ✶ Repository Structure
```bash
vibesignal-ai
│
├── sql/
│   └── schema.sql
│
├── scripts/
│   ├── 01_generate_creators.py
│   ├── 02_generate_campaigns.py
│   ├── 03_generate_posts.py
│   ├── 04_generate_conversions.py
│   ├── 05_generate_audience_demographics.py
│   ├── 06_generate_excel_report.py
│   ├── 07_vibescore_model.py
│   └── 08_budget_allocator.py
│
├── notebooks/
│   ├── 01_eda_analysis.ipynb
│   └── charts/
│
├── dashboards/
│   ├── .gitkeep
│   ├── P1_executive_overview.png.jpeg
│   ├── P2_creator_intelligence.png.jpeg
│   └── P3_campaign_roi.png.jpeg
│
├── docs/
│   ├── data_methodology.md
│   ├── learning_journal.md
│   └── metrics_dictionary.md
│
├── data/
│   ├── allocation_micro.csv
│   ├── allocation_mixed.csv
│   ├── allocation_nano.csv
│   ├── audience_demographics.csv
│   ├── brands.csv
│   ├── budget_allocation_comparison.csv
│   ├── campaign_creators.csv
│   ├── campaigns.csv
│   ├── conversions.csv
│   ├── creators.csv
│   ├── posts.csv
│   ├── vibe_scores.csv
│   ├── vibe_score_summary.csv
│   └── vibescore_weights.json
│
├── README.md
└── .gitignore
```
## ✶ Setup & Usage

### Prerequisites

- Python 3.10 or higher  
- Git  
- A local virtual environment (recommended)  
- Optional: Supabase/PostgreSQL access if you want to recreate the full DB

### Installation

```bash
git clone https://github.com/jannat0082/vibesignal-ai.git
cd vibesignal-ai

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install --upgrade pip
pip install faker pandas numpy matplotlib seaborn scikit-learn openpyxl
```

### Generate Data & Run Pipeline

```bash
python scripts/01_generate_creators.py
python scripts/02_generate_campaigns.py
python scripts/03_generate_posts.py
python scripts/04_generate_conversions.py
python scripts/05_generate_audience_demographics.py
python scripts/06_generate_excel_report.py
python scripts/07_vibescore_model.py
python scripts/08_budget_allocator.py
```

### Notes
- The `data/` directory is gitignored because it contains generated outputs.
- The scripts are intended to be executed in sequence.
- Additional analysis is available in `notebooks/01_eda_analysis.ipynb`.

## ✶ Challenges and Resolutions

- **Promo code collisions** were caused by a limited random number range. This was resolved by using `cc_id` as a unique identifier.
- **Nullable integer export issues** occurred because pandas converted integers to float values such as `68.0`. This was resolved by casting fields to `Int64` before export.
- **Limited campaign history** reduced creator coverage. This was improved by increasing the number of campaigns from 40 to 70.

## ✶ Data Disclaimer

VibeSignal AI uses **benchmark-informed synthetic data** for demonstration and evaluation purposes. Engagement and conversion patterns are grounded in public influencer marketing benchmark ranges, but:

- Recommendations are intended to demonstrate decision-support logic.  
- Outputs are **not** guaranteed real-world outcomes.  
- Production use would require real campaign data, creator consent, and platform-compliant data access.

## ✶ Project Status

| Module               | Status       |
|----------------------|--------------|
| Data Generation      |  Complete    |
| Database Schema      |  Complete    |
| EDA Notebook         |  Complete    |
| Excel KPI Report     |  Complete    |
| VibeScore Model      |  Prototype   |
| Budget Allocator     |  Prototype   |
| Power BI Dashboard   |  Completed   |





