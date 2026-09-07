# Learning Journal — VibeSignal AI

**Internship: 18 May 2026 – 31 August 2026**


*This journal was written throughout the project, not summarised at the end. The entries reflect what I was actually thinking at each stage — including the mistakes, the dead ends, and the moments where something clicked after days of not understanding it.*


## Week 1–2 
### Getting oriented and defining the problem

The first thing I did was read everything I could find about creator marketing analytics in India. Not academic papers — actual agency reports, Influencer Marketing Hub's India data, Qoruz's 2025 benchmarks. I wanted to understand what practitioners actually look at before I designed anything.

The thing that struck me immediately was how everyone leads with engagement rate. Every campaign brief I could find online listed "minimum 4% engagement rate" as a creator requirement, as if that single number was a reliable filter. But when I looked at the actual conversion data from public case studies, the correlation was weak at best. Brands paying premium rates for high-engagement macro creators were getting average-at-best returns.

That observation became the thesis: engagement and conversion are different things, and the tools most brands use treat them as the same thing.

---

## Week 3–4 
### Designing the schema — the decision that shapes everything

I spent more time on the schema design than on anything else in the first month. This surprised me. I expected to spend most of my time on analysis, but I kept coming back to the same realisation: if the data structure is wrong, the analysis is wrong. You can't fix a bad schema with clever SQL.

The most important design decision was the grain of the conversions table. My first instinct was to store conversions at the campaign level — total conversions per campaign, total revenue per campaign. That would have been clean and simple. But it would have made creator-level ROI calculation impossible without additional assumptions. I changed it to store one row per purchase, which meant I could trace a conversion back to the specific post and creator that drove it through the promo code.

The second important decision was the demographics table format. I initially built it wide — one column per demographic bucket. It had 22 columns. The moment I tried to write a query that filtered by demographic type and then computed percentage shares, I understood why long format exists. I rebuilt it as 17 rows per creator with `demographic_type` and `demographic_value` columns. The query went from a 40-line pivot to a 6-line GROUP BY.

**What I learned:** Schema decisions made at the beginning determine what questions you can answer at the end. It is worth spending three days on the data model before writing a single line of analysis code.

---

## Week 5–6 
### Data generation — where the first real bugs appeared

Writing the data generation scripts felt mechanical until the bugs started. Then it became the most interesting part of the project.

---

### Bug 1 — The Promo Code Collision

**What happened:**  
Script 02 generates promo codes for each creator-campaign partnership. My original approach: take the first 8 characters of the creator's handle and append a random 2-digit number.

```python
promo_code = f"{handle_clean[:8]}{random.randint(10, 99)}"
```

This looked fine until I loaded the data into Supabase. PostgreSQL rejected 18 rows with a unique constraint violation. The promo code column has a UNIQUE constraint, and I had 18 collisions across 361 rows.

**Why it happened:**  
`random.randint(10, 99)` gives 90 possible values. With Indian names, the handle prefixes are not uniformly distributed — names like "rahul", "priya", "anjali" appear multiple times. When two creators with the same handle prefix get the same random suffix, the codes collide.

**How I fixed it:**  
The solution was to use `cc_id` — the partnership counter — as the suffix instead of a random number. `cc_id` is a sequential integer assigned to each partnership, so it is guaranteed unique by construction.

```python
promo_code = f"{handle_clean[:8]}{partnership_id}"
```

I re-ran the validation check after the fix. Zero duplicate promo codes across all 361 rows.

**What I learned:**  
Random number generation with small ranges fails predictably when the input space has patterns. The right fix was not to increase the random range — it was to replace randomness with something deterministic. A counter is always unique. A random number is only probably unique.

---

### Bug 2 — The 68.0 Problem

**What happened:**  
When I loaded `campaign_creators.csv` into Supabase, several rows failed with:

```
invalid input syntax for type integer: "68.0"
```

The `campaign_id` column was defined as INTEGER in PostgreSQL. The CSV had values like `68.0`, `1.0`, `44.0`.

**Why it happened:**  
Pandas represents nullable integers using float64 by default. When a column can contain NaN (which `campaign_id` can, because organic posts don't belong to a campaign), pandas automatically upcasts integers to float64. When you write to CSV, `68` becomes `68.0`.

**How I fixed it:**  
Pandas has a dedicated nullable integer type — `Int64` with a capital I. Unlike `int64`, it can hold NaN without converting to float.

```python
posts_df["campaign_id"] = posts_df["campaign_id"].astype("Int64")
```

After this, the CSV writes `68` as `68` and `<NA>` for null values. Supabase accepted the import without errors.

**What I learned:**  
The lowercase `int64` and uppercase `Int64` in pandas are not the same type. This is a known Python footgun that I had read about but never encountered before. It only bites you when a column has both integer values and nulls, which is exactly the situation for optional foreign keys like `campaign_id` on posts.

---

### Bug 3 — The Promo Code Attribution Bug (Worse Than Bug 1)

**What happened:**  
This one took me two days to find. In the original `script 04_generate_conversions.py`, I built the promo code lookup like this:

```python
promo_lookup = dict(
    zip(
        campaign_creators_df["creator_id"].tolist(),
        campaign_creators_df["promo_code"].tolist(),
    )
)
```

Then I looked up codes with:

```python
promo_code = promo_lookup.get(creator_id)
```

The bug: when a creator appears in multiple campaigns, the dictionary keeps only the last promo code for that creator. A creator in 3 campaigns gets one promo code in the lookup — whichever was processed last.

This meant conversions from the first two campaigns were being attributed to the third campaign's promo code. The attribution chain was silently broken across a significant number of rows.

**Why it took so long to find:**  
The code produced no errors. The data loaded cleanly. The issue only became visible when I manually traced a conversion from its `promo_code` back through `campaign_creators` to the originating campaign and noticed the campaign IDs didn't match.

**How I fixed it:**  
Changed the lookup key from `creator_id` alone to `(campaign_id, creator_id)` — a tuple that uniquely identifies each partnership.

```python
promo_lookup = {}
for _, row in campaign_creators_df.iterrows():
    key = (int(row["campaign_id"]), int(row["creator_id"]))
    promo_lookup[key] = row["promo_code"]
```

And the lookup:

```python
if has_campaign:
    promo_code = promo_lookup.get((campaign_id, creator_id), pd.NA)
```

**What I learned:**  
Silent data corruption is far more dangerous than an error that crashes the script. An error tells you something is wrong. Silent corruption lets you build an entire analysis on top of wrong data without knowing it. The lesson: any time you build a lookup dictionary in a data pipeline, check whether the key is actually unique. A non-unique key means you are silently overwriting values.

---

### Bug 4 — The avg_engagement_rate KeyError in Script 07

**What happened:**  
Script 07 (the VibeScore model) threw:

```
KeyError: 'avg_engagement_rate'
```

at the line:

```python
scores["engagement_score"] = normalize(scores["avg_engagement_rate"])
```

**Why it happened:**  
The `creators.csv` file has a column called `avg_engagement_rate`. The `post_engagement` aggregation in the same script also produces a column called `avg_engagement_rate`. When I merged these two dataframes, pandas renamed them to `avg_engagement_rate_x` and `avg_engagement_rate_y` to avoid the collision. The original column name disappeared.

**How I fixed it:**  
Renamed the computed column from the posts aggregation before the merge, so the creator-level column from `creators.csv` retained its original name:

```python
post_engagement = post_engagement.rename(columns={
    "avg_engagement_rate": "post_avg_er"
})
```

After this, `scores["avg_engagement_rate"]` refers unambiguously to the creator-level baseline, and `post_avg_er` refers to the post-level computation.

**What I learned:**  
Pandas merge column suffixes are a common trap when merging dataframes that share column names. The merge does not fail — it just silently renames columns. Always check `df.columns` after any merge that could produce conflicts.

---

### Bug 5 — CHARTS_DIR Undefined in EDA Cells

**What happened:**  
The EDA notebook threw `NameError: name 'CHARTS_DIR' is not defined` in Cell 5 even though `CHARTS_DIR` was defined in Cell 1.

**Why it happened:**  
I had written the notebook assuming cells would always be run sequentially from Cell 1. When I re-ran Cell 5 after restarting the kernel, Cell 1 had not run, so `CHARTS_DIR` was not in memory.

**How I fixed it:**  
Made each cell self-contained by adding the necessary imports and variable definitions at the top of each cell that needed them. This means Cell 5 can be run in isolation without depending on Cell 1 having executed first.

**What I learned:**  
Jupyter notebooks are not scripts. Cell execution order is not guaranteed. Any variable that a cell depends on should either be defined in that cell or be computed from raw data files in that cell. Relying on previous cells having run is fragile.

---

## Week 7-8
### EDA — the finding that changed my interpretation

I went into the EDA expecting the data to confirm my hypothesis about the vanity metrics trap. It did confirm it — but in a more extreme way than I anticipated.

Nano creators averaged 7.89% engagement. Mega creators averaged 1.12%. That is a 7× difference, which is what I expected based on industry benchmarks.

But the CVR numbers were jarring. Nano: 0.06%. Mega: 1.73%. That is a 28× difference in the other direction.

I initially thought this was an artefact of how I had assigned creator performance profiles in the data generation. But when I traced through the logic, it was correct. The nano tier has a higher proportion of "vanity" profile creators (high engagement, low CVR). The mega tier has more "converter" profile creators because their audiences, while smaller in proportional engagement, tend to be more purchase-intent oriented.

The more interesting finding was the micro tier. Micro creators averaged 4.36% engagement and 3.96% CVR — the most balanced combination in the dataset. This is what the data was showing about where the real value sits in the Indian creator economy: not the nano creators who are cheap and engaging, not the macro creators who are expensive and converting, but the mid-tier creators who do both adequately at a cost structure that works for D2C budgets.

That finding shaped how I weighted the VibeScore model. If micro creators are genuinely the most balanced performers, the model should reflect that, and the recommendation distribution should show micro creators performing better overall than nano or mega. The final VibeScore averages confirmed: micro averaged 43.83, nano 36.88, macro 39.39, mega 27.30.

---

## Week 9–10
### Power BI — the frustration of DAX

I had used Power BI before for basic reports. DAX was new to me, and it is not intuitive coming from pandas or SQL.

The Avg Campaign ROI measure took me three attempts to get right. My first version:

```dax
Avg Campaign ROI =
AVERAGEX(VALUES(campaigns[campaign_id]), [Campaign ROI %])
```

This returned 11,462%. Clearly wrong. The issue: some campaigns have very small creator fees with proportionally large attributed revenue, producing individual ROI values of 1,000%+. Averaging those with AVERAGEX weights each campaign equally regardless of size, so the extreme outliers dominate.

My second attempt used a simple average of the column, which produced a different wrong answer.

The correct approach was a blended portfolio ROI — total attributed revenue minus total fees, divided by total fees:

```dax
Portfolio ROI % =
DIVIDE(
    [Campaign Revenue] - [Campaign Spend],
    [Campaign Spend],
    0
) * 100
```

This is the same calculation, applied to the aggregated totals rather than averaged across campaigns. The result: 109.99%, which is defensible given the input data.

The lesson was about the difference between average-of-ratios and ratio-of-averages. These produce different numbers and answer different questions. 109.99% answers "what is the overall portfolio return?" 11,462% answers "what is the typical campaign return?" — and it was wrong because typical is not mean when the distribution is skewed.

The Monthly Revenue Trend was another frustration. The trend chart kept showing time-of-day data instead of monthly aggregates because Power BI defaults to the lowest grain available when a datetime column is on the X-axis. The fix required either creating a `Dim_Date` table and using month-level grain, or computing a `conversion_month` calculated column in text format and sorting it by a `YYYYMM` numeric column.

I ended up doing both — the `Dim_Date` table for proper time intelligence and the calculated column for the trend chart display.

---

## Week 11–12 
### VibeScore validation and budget allocator

After the VibeScore model ran, I spent a week checking whether the outputs made sense. Not just whether the numbers were in range, but whether the ranking was defensible.

The top-ranked creator in the dataset, Garima Bala (VibeScore: 70.30), is a micro creator on Instagram in the travel niche. Her high ranking comes from an ROI of 369% and a CVR of 3.37%. Looking at her dimension scores: ROI score 89.4, conversion score 91.2, engagement score 38.6. The engagement score is relatively low, which is consistent with micro tier, but the model correctly weights that dimension at only 10%. Her overall score reflects what matters: she converts.

The creators who rank poorly despite high followers are almost all mega creators. Their ROI scores are uniformly low because the fee-to-revenue ratio for mega partnerships is compressed. This is the model working correctly.

The budget allocator followed naturally from the VibeScore model. The greedy allocation logic is simple — sort by score, fill from the top until the budget runs out — but the interesting part was testing different objective parameters. Running the allocator with `objective = "awareness"` produces a noticeably different creator mix than `objective = "sales"`, because the objective boosts adjust the effective VibeScore before sorting. That dynamic behaviour is what makes the tool analytically useful rather than just a sorted list with a budget cutoff.

---

## Week 13–14 
### Retrospective on what I would do differently

With two weeks left, I started thinking about what I would change if I were starting again.

**I would design the time dimension earlier.** Adding `Dim_Date` to Power BI late in the project required revisiting several measures and chart configurations that had already been built without time intelligence in mind. If I had designed the date table in week 3 instead of week 11, the trend analysis would have been cleaner throughout.

**I would instrument the data generation scripts with timing.** Each script runs quickly on 200 creators and 1,972 conversions, but the validation checks are nested loops in some places. At 10,000 creators the scripts would be slow. Adding `time.perf_counter()` instrumentation early would have made performance bottlenecks visible before they became problems.

**I would write the metrics dictionary in week 1, not week 13.** I know what every column means because I designed it. But when I went back to document the columns at the end of the project, I found two column names that were slightly ambiguous and two that had changed purpose slightly during development. Writing the dictionary alongside the schema design would have forced me to be precise about definitions while they were still fresh.

---

## Final Week 
### What this project actually taught me

Three months ago I thought data analysis was primarily about choosing the right chart type and making it look good. I know that is not what it is now.

Most of this project was deciding. Deciding what questions to ask before deciding how to answer them. Deciding what data to collect before deciding how to analyse it. Deciding which metric to weight at 35% and which to weight at 10%, and being able to explain why. The technical skills — Python, SQL, Power BI, DAX — are real and I developed them. But the useful part is the reasoning behind the choices.

The bugs were the best teachers. Each one was a different kind of mistake:

- Bug 1 (promo codes): inadequate range analysis before choosing a generation method
- Bug 2 (68.0): not knowing how Pandas handles nullable types
- Bug 3 (attribution): building a lookup with a non-unique key
- Bug 4 (KeyError): not checking column names after a merge
- Bug 5 (CHARTS_DIR): assuming notebooks execute sequentially

None of these were hard to fix once I understood them. But understanding them required slowing down and reading the actual error rather than guessing. Most of my early debugging was guessing. Most of my late-project debugging was reading.

The finding I am most proud of is not the dashboard or the model. It is the CVR gap. When the data showed that nano creators convert at 0.06% and mega creators at 1.73%, and I could trace exactly why that happened through the architecture of the data — that felt like the first moment the project was doing something real. It was not showing me what I had put in. It was showing me what the structure of the data implied, which is a different thing.

That is what I want to keep doing.


