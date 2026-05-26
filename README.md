# Behavioral Health Treatment Gap Analysis — Washington State

**Author:** Waleed Adawi &nbsp;·&nbsp; **Year:** 2026  
**Stack:** Python 3 · SQLite · numpy · matplotlib  
**Data:** SAMHSA NSDUH 2021–2022 · HRSA Health Professional Shortage Areas (Q2 FY2026)

---

## Overview

### The Problem

Millions of Americans who meet clinical criteria for a mental health condition never receive treatment. This is not a knowledge gap — it is a structural one: not enough providers, not enough affordable care, and not enough geographic access, particularly in rural and agricultural communities. The result is a measurable treatment gap: the difference between how many people have a diagnosable mental health condition and how many actually receive care.

### Why It Matters

For state health agencies and federally-funded behavioral health clinics — especially Certified Community Behavioral Health Clinics (CCBHCs), which are required to document treatment access and unmet need as a condition of federal certification — quantifying this gap is not optional. It drives grant applications, workforce planning, and program justification. A CCBHC Data Quality Analyst's core function is to produce exactly this kind of analysis: taking authoritative federal datasets, loading them into a clean and auditable data environment, and generating outputs that can be submitted to HRSA and SAMHSA.

### Objective

This project quantifies the behavioral health treatment gap at the state level across all 50 states and DC, then zooms into Washington State — with particular focus on Yakima County, one of the most severely shortage-designated mental health areas in the state. The analysis uses two federal datasets, five SQL-based queries, and eight visualizations to answer:

1. Where does Washington rank nationally for unmet mental health need?
2. How does Washington's treatment gap compare to the national average — and what drives the difference?
3. How severe is the provider shortage in Yakima County relative to the rest of Washington?
4. Do federal agency claims about behavioral health access hold up against the data?

---

## Methodology

The project follows a standard data quality analyst workflow: source → load → audit → analyze → communicate.

**Step 1 — Data Sourcing.** Two authoritative federal datasets were identified: SAMHSA's NSDUH 2021–2022 Model-Based State Prevalence Estimates (providing state-level mental health and substance use metrics for all 50 states and DC) and HRSA's HPSA Designation Database (providing county-level Mental Health Professional Shortage Area scores for Washington). Washington-specific values were sourced from SAMHSA's state-specific PDF (`NSDUHsaeWashington2022.pdf`, Tables 106A/106B) to ensure maximum precision using the Small Area Estimation hierarchical Bayes methodology.

**Step 2 — Database Design.** A normalized SQLite database was built with two tables: `nsduh_state` (51 rows, 8 behavioral health metrics per state) and `hrsa_shortage` (30 rows, Washington county-level HPSA designations). SQLite was chosen for portability and to demonstrate relational database competency without infrastructure dependencies.

**Step 3 — Data Quality Audit.** Before running any analysis, a programmatic audit was executed via SQL (`Query 4`) to verify zero null values, zero out-of-bounds percentages, and complete coverage across all 51 records. This mirrors the pre-submission audit a CCBHC Data Quality Analyst runs before filing federal grant reports.

**Step 4 — SQL-Based Analysis.** Five queries were executed against the database covering: MH treatment gap ranking (all 51 jurisdictions), Washington vs. national comparison, combined MH and SUD gap analysis for the ten highest-gap states, the data quality audit, and Washington county-level HPSA rankings.

**Step 5 — Exploratory Data Analysis.** Eight visualizations were produced covering distributions, scatterplots, grouped comparisons, bubble charts, and ranked bars. Each chart was designed to communicate a specific finding to both technical and non-technical audiences.

**Step 6 — Validation and Communication.** Stated claims from SAMHSA, HRSA, Washington State, and the CCBHC program were located in official documentation and cross-referenced against the data to confirm, qualify, or contextualize each claim.

**Tools:** Python 3 · SQLite · numpy · matplotlib · SAMHSA NSDUH SAE methodology · HRSA HPSA scoring framework

---

## Data Processing

### Data Sources

| Dataset | Source | Access Date |
|---|---|---|
| NSDUH 2021–2022 Model-Based State Prevalence Estimates | [SAMHSA](https://www.samhsa.gov/data/report/2021-2022-nsduh-state-prevalence-estimates) | May 2026 |
| Washington State NSDUH Tables 106A/106B (exact SAE figures) | [NSDUHsaeWashington2022.pdf](https://www.samhsa.gov/data/sites/default/files/reports/rpt42728/NSDUHsaeWashington2022.pdf) | May 2026 |
| Mental Health HPSA Designations — Washington County-Level | [HRSA BCD_HPSA_FCT_DET_MH](https://data.hrsa.gov/data/download?data=SHORT) | May 2026 |

### Data Evaluation

The NSDUH dataset uses Small Area Estimation (SAE) with a hierarchical Bayes model. This is SAMHSA's most precise state-level estimation methodology — it combines direct survey estimates with model-based predictors to produce reliable figures even for smaller states with limited sample sizes. The six metrics per state cover AMI prevalence, AMI treatment rate, AMI unmet need rate, SMI prevalence, SUD prevalence, and SUD treatment rate.

The HRSA HPSA dataset uses a composite shortage score (0–25) that accounts for population-to-provider ratio, poverty rate, and travel distance to the nearest mental health provider. It is the authoritative federal metric for designating shortage areas and determines eligibility for NHSC loan repayment, J-1 visa waivers, and federal grant priority consideration.

### Data Cleaning

Both datasets were loaded as-is from federal sources — no imputation, no interpolation, no estimated values. Washington State's AMI prevalence (27.14%) and treatment rate (23.88%) were taken directly from SAMHSA's state-specific PDF rather than the multi-state summary table to ensure the highest available precision. The **treatment gap** throughout this project is calculated as:

```
treatment_gap = ami_prevalence_pct − ami_received_treatment_pct
```

A positive gap means more people have AMI than are receiving treatment. Negative gaps (observed in DC, NJ, MA, CT, VT, MN, NE, NY, MD) reflect cross-state care-seeking behavior captured by NSDUH's SAE model — residents of high-resource states seek care in other states, inflating the measured treatment rate above the in-state prevalence estimate. This is a documented methodological artifact, not a data error.

### Data Quality Audit Results

```sql
Query 4 — Programmatic Audit
  Total records      : 51
  Null AMI prevalence: 0
  Null AMI treatment : 0
  Out-of-range prev  : 0
  Out-of-range tx    : 0
  Result             : PASS — zero violations
```

All 51 records passed all integrity checks. Dataset confirmed ready for grant-reportable analysis.

---

## EDA + Analysis

### Summary Statistics

| Metric | National Min | National Avg | National Max | Washington |
|---|---|---|---|---|
| AMI Prevalence (%) | 17.44 (NJ) | 22.98 | 28.87 (ME) | **27.14** |
| AMI Treatment Rate (%) | 14.33 (TX) | 20.78 | 31.22 (DC) | **23.88** |
| MH Treatment Gap (pp) | −11.07 (DC) | +2.20 | +8.66 (NV) | **+3.26** |
| SUD Prevalence (%) | 9.90 (AL) | 18.64 | 25.88 (OR) | **20.23** |
| SUD Treatment Gap (pp) | 6.08 (AL) | 14.05 | 20.21 (OR) | **15.55** |
| AMI Unmet Need (%) | 36.4 (DC) | 52.0 | 61.8 (WY) | **51.2** |

**What this immediately tells us:** Washington has the 4th-highest AMI prevalence nationally — one of the most mentally ill adult populations in the country by this measure. Yet its treatment rate is only modestly above average. That gap between high need and insufficient coverage is the central finding of this entire analysis.

---

### Fig 1 — Treatment Gap by State: Top 20 (Washington Highlighted)

![Top 20 States by Treatment Gap](outputs/fig1_treatment_gap_ranking.png)

Nevada, Wyoming, and Idaho dominate the top of the ranking with gaps exceeding 7 percentage points — driven by extreme rural provider shortages, limited state behavioral health infrastructure, and high rates of poverty among affected populations. Washington ranks 17th out of 51 jurisdictions, with a gap of 3.3 pp — above the national average of 2.2 pp and above both Pacific Northwest neighbors (Oregon ranks 10th at 4.7 pp; Idaho ranks 3rd at 7.4 pp).

The states appearing at the bottom — Minnesota, Nebraska, Vermont, New York, Massachusetts, Connecticut, New Jersey, and DC — show negative gaps, meaning their measured treatment utilization exceeds their in-state AMI prevalence estimates. This is a documented artifact of NSDUH's SAE methodology: in high-resource states, residents frequently seek care across state lines, and that out-of-state treatment is still attributed to the home state in the survey. This does not indicate over-treatment; it indicates geographic care-seeking behavior. SAMHSA explicitly documents this in its methodology notes.

---

### Fig 2 — Washington vs. National Average

![WA vs National Average](outputs/fig2_wa_vs_national.png)

Washington's AMI prevalence (27.14%) is 4.16 percentage points above the national average (22.98%), yet its treatment rate (23.88%) is only 3.10 points above average (20.78%). This asymmetry — need growing faster than access — is the structural driver of Washington's above-average treatment gap. The state serves a high-prevalence population that consistently outpaces treatment capacity.

For a CCBHC in Washington, this chart provides the grant-narrative framing required in needs assessments: the problem is not just a low treatment rate, but a disproportionately large population in need relative to the care available. It directly supports arguments for expanded CCBHC capacity, workforce recruitment incentives, and targeted outreach in high-prevalence regions like Yakima.

---

### Fig 3 — Washington County HPSA Scores: Top 10 (Yakima Highlighted)

![WA County HPSA Scores](outputs/fig3_yakima_hpsa_rank.png)

Yakima County's HPSA score of 19 out of 25 places it second in Washington, trailing only Ferry County (score 20). Seven of the ten counties shown — Ferry, Yakima, Pend Oreille, Stevens, Garfield, Lincoln, and Adams — meet or exceed HRSA's federal high-priority threshold of 16, qualifying for the full suite of federal shortage-area incentives.

The HPSA composite score reflects three simultaneous pressures: population-to-provider ratio (Yakima has a large rural and agricultural population with few mental health providers), poverty rate (Yakima is among Washington's poorest counties by federal poverty thresholds), and travel distance to the nearest available care. A score of 19 means all three are severe at once. For CCBHC workforce planning, this directly supports NHSC site applications, J-1 visa waiver requests for international medical graduates, and priority scoring in SAMHSA grant competitions.

---

### Fig 4 — AMI Prevalence vs. Treatment Rate (All 51 Jurisdictions)

![Prevalence vs Treatment Scatter](outputs/fig4_prevalence_vs_treatment.png)

This scatterplot shows the relationship between how many adults in each state have AMI and how many receive treatment. The dashed diagonal line represents perfect parity — zero treatment gap. States above it have more treatment than prevalence (negative gap); states below it have more need than care (positive gap).

**Key observations:**

The correlation between prevalence and treatment rate is weak-to-moderate (r ≈ 0.43), meaning higher prevalence does not reliably predict higher treatment access. States with similar prevalence rates can have very different treatment rates depending on provider supply, insurance coverage policy, and rural vs. urban population distribution. Washington falls well below the parity line — high prevalence, but treatment does not keep pace. This visualization makes the access gap tangible: Washington is not a state that lacks demand for behavioral health services. It is a state where demand far outpaces supply.

For a non-technical audience: every dot is a state. The higher the dot sits above the diagonal, the better that state is at getting people who need mental health care into treatment. Washington sits below the line, meaning it has more people who need care than it has people actually receiving it.

---

### Fig 5 — Distribution of Mental Health Treatment Gaps

![Gap Distribution](outputs/fig5_gap_distribution.png)

The histogram shows where all 51 jurisdictions fall on the spectrum from best (lowest gap) to worst (highest gap). The distribution is roughly bell-shaped with a slight right skew — most states cluster between 0 and 4 pp — with a tail of high-gap outliers (Nevada, Wyoming, Texas, Idaho, Tennessee) in the 6–8 pp range.

Washington's 3.3 pp gap is highlighted in red. It sits just above the national mean of 2.2 pp, comfortably in the upper half of the distribution. The key takeaway is not that Washington is among the worst states — it is not — but that its high AMI prevalence means the **absolute number of people** falling into that gap is substantially larger than a mid-tier gap percentage suggests. Washington's 27% prevalence rate applied to a population of roughly 5.7 million adults means hundreds of thousands of people with a diagnosable mental illness who are not receiving care.

---

### Fig 6 — Mental Health vs. Substance Use Disorder Gaps (Top 12 States)

![MH vs SUD Gaps](outputs/fig6_mh_vs_sud_gaps.png)

This grouped bar chart reveals a consistent and important pattern across all high-gap states: the SUD treatment gap is not just worse than the MH gap — it is consistently 2 to 4 times larger. In Washington, the MH gap is 3.3 pp. The SUD gap is 15.6 pp. That means for every person with a mental health condition who is not getting care, there are roughly five people with a substance use disorder who aren't getting care.

This matters directly for CCBHCs, which are federally required to serve both MH and SUD populations and must document unmet need for each population separately under SAMHSA certification criteria. The SUD gap cannot be explained away by cross-state care-seeking effects — it reflects a genuine and severe shortage of SUD treatment capacity across the country. States that rank highly on MH gaps almost universally rank worse on SUD gaps, suggesting shared structural drivers: rural location, provider shortage, poverty, and insurance access barriers.

---

### Fig 7 — Unmet Mental Health Need: Top 20 States

![Unmet Need Ranking](outputs/fig7_unmet_need_ranking.png)

The `ami_unmet_need_pct` metric measures the share of adults *who already have AMI* and still do not receive any mental health treatment. It is a different lens from the treatment gap: instead of comparing prevalence to treatment rates, it asks directly — of the people who are sick, what fraction gets no care at all?

Nationally, more than half of all adults with AMI go without any treatment in a given year. Washington's unmet need rate of 51.2% means roughly half of all Washington adults with AMI receive no treatment — consistent with the national average despite Washington's progressive health policy reputation. The states with the lowest unmet need (lower end of the chart) are generally high-resource, high-insurance-coverage states — Vermont, Rhode Island, Maine, Massachusetts — where state investment in behavioral health, Medicaid expansion generosity, and higher provider density combine to improve access.

**For a non-technical audience:** In Washington, if you put 100 people with a mental illness in a room, about 51 of them will not see a therapist, psychiatrist, or counselor all year. That is the problem this analysis quantifies.

---

### Fig 8 — Washington County HPSA Scores vs. Designated Population

![HPSA Bubble Chart](outputs/fig8_hpsa_bubble.png)

This bubble chart adds a population dimension to the HPSA score ranking. Bubble size represents the number of people in each county who fall under the HPSA designation — the population without adequate mental health provider access. The combination of score (shortage severity) and bubble size (scale of the problem) reveals where the burden is largest.

Yakima County is notable on both dimensions: a high score (19/25) and a large designated population (256,000 people). Thurston County has a lower score (6/25) but an enormous designated population (312,500), reflecting a large suburban county where shortage is less severe but still affects a very large number of people. Ferry County has the highest score (20/25) but a tiny population (8,500), reflecting extreme rural shortage with limited scale. For CCBHC planning purposes, Yakima presents the most acute combination of severity and scale — the largest high-priority shortage in Washington State.

---

### What the Data Is Telling Us

Taken together, these eight charts tell a consistent story:

**Washington is a high-need, under-resourced state for behavioral health.** Its AMI prevalence is in the top 10 nationally, but its treatment infrastructure has not kept pace with that need. The result is a 3.3 pp mental health treatment gap and a 15.6 pp SUD treatment gap — both above the national averages for their respective domains.

**The geographic dimension of this problem is concentrated in rural eastern Washington.** Yakima, Ferry, Pend Oreille, Stevens, Garfield, Adams, and Lincoln counties all score at or above the federal high-priority HPSA threshold. These are agricultural, rural, and lower-income counties where the combination of provider shortage, poverty, and distance creates compound barriers to access.

**The SUD crisis is being systematically under-addressed.** Across every high-gap state, the substance use disorder treatment gap dwarfs the mental health gap. Washington's SUD gap of 15.6 pp means that roughly 1 in 6 Washington adults has a substance use disorder that goes untreated in a given year. For CCBHCs — which are required to serve both populations — this represents the single largest area of unmet service demand.

**More than half of people with AMI go without care.** A 51.2% unmet need rate is not a policy success. Despite Washington's Medicaid expansion, behavioral health integration initiatives, and relatively high per-capita healthcare spending, the majority of people with diagnosable mental illness remain untreated.

---

### Validating Official Claims Against the Data

#### SAMHSA Claims

**Claim:** "More than half of U.S. adults with Any Mental Illness did not receive mental health services in the past year." *(SAMHSA, 2022 NSDUH National Report)*

**Data verdict: Confirmed.** The national average `ami_unmet_need_pct` across all 51 jurisdictions in this dataset is 52.0%. Washington's figure is 51.2%. SAMHSA's headline claim understates the problem in high-gap states like Wyoming (61.8% unmet need) and Texas (61.2%), but accurately reflects the national pattern.

**Claim:** SAMHSA's 2021–2022 NSDUH report states that AMI prevalence among U.S. adults is approximately 22–23%.

**Data verdict: Confirmed.** The national average AMI prevalence across all 51 jurisdictions in this dataset is 22.98% — precisely within the range SAMHSA reports nationally. Washington's 27.14% is a statistically significant outlier above this national average, as documented in SAMHSA's own state-specific PDF.

#### HRSA Claims

**Claim:** HRSA designates Yakima County as a Mental Health Health Professional Shortage Area with a score of 19/25, making it one of the most severely shortage-designated counties in Washington State.

**Data verdict: Confirmed and contextualized.** The HRSA HPSA database confirms Yakima's score of 19/25 — the second highest in Washington, behind only Ferry County (20/25). Of Washington's 30 designated counties, 7 meet or exceed the federal high-priority threshold of 16. HRSA's characterization of Yakima as a high-severity shortage area is directly supported by the data.

**Claim:** HRSA states that HPSA scores ≥ 16 qualify for federal high-priority shortage designation, unlocking NHSC loan repayment and J-1 visa waiver eligibility.

**Data verdict: Confirmed.** This threshold is applied as-is in the analysis. Seven Washington counties meet it: Ferry (20), Yakima (19), Pend Oreille (18), Stevens (17), Garfield (17), Lincoln (16), and Adams (16).

#### Washington State / Yakima Context

**Claim:** Washington State health agencies and Yakima Valley Farm Workers Clinic program documentation identify Yakima County as facing compound behavioral health access barriers: high agricultural population, elevated poverty, rural geography, and bilingual/bicultural service gaps.

**Data verdict: Supported.** Yakima's HPSA score of 19 is calculated by HRSA using precisely the metrics that reflect these conditions: population-to-provider ratio (reflecting provider shortage relative to the large rural population), poverty rate (reflecting Yakima's elevated federal poverty rate), and travel time (reflecting geographic distance from urban mental health services). The score operationalizes the compound barriers documented by local health agencies.

#### Federal CCBHC Program

**Claim:** SAMHSA's CCBHC certification criteria require clinics to serve both mental health and substance use disorder populations, and to document unmet need in their service area as part of grant compliance.

**Data verdict: The data directly supports the program rationale.** Washington's 3.3 pp MH gap and 15.6 pp SUD gap — both above the national averages — constitute exactly the kind of documented unmet need that CCBHC needs assessments are designed to capture. The HPSA data for Yakima further supports the workforce shortage rationale behind CCBHC workforce incentive provisions. The five SQL queries in this project map directly to the data documentation requirements in SAMHSA's CCBHC Program Guidance: gap analysis, comparative benchmarking, multi-condition coverage, data quality validation, and shortage-area documentation.

---

### Answering the Main Questions

**1. Where does Washington rank nationally for unmet mental health need?**
Washington ranks 17th out of 51 jurisdictions for mental health treatment gap (3.3 pp). It ranks in the upper half of the unmet need distribution, with a 51.2% unmet need rate equal to the national average despite its above-average prevalence.

**2. What drives Washington's above-average treatment gap?**
The gap is not driven by an unusually low treatment rate — Washington's 23.88% treatment rate is above the national average (20.78%). It is driven by an unusually high prevalence rate (27.14%, 4th highest nationally) that treatment capacity has not kept pace with. Washington has more people in need than its treatment infrastructure can serve.

**3. How severe is the provider shortage in Yakima County?**
Yakima County's HPSA score of 19/25 places it in the top 7% of shortage-designated counties in Washington. With a designated population of 256,000 people and a score reflecting simultaneous pressure from provider shortage, poverty, and geographic distance, Yakima represents the most actionable target for CCBHC expansion, NHSC recruitment, and federal workforce incentive programs in the state.

**4. Do federal claims hold up against the data?**
Yes — with nuance. SAMHSA's national claims about unmet need are confirmed and in some cases understate the problem in high-gap states. HRSA's HPSA designations for Washington are confirmed and directly usable for workforce planning. The CCBHC program rationale is fully supported by the gap data.

---

### Recommendations

Based on the data, five recommendations are directly supported:

**1. Prioritize CCBHC expansion in Yakima, Stevens, Pend Oreille, and Garfield counties.** All four have HPSA scores ≥ 17, meaning shortage severity is extreme. A CCBHC serving these areas qualifies for the full suite of federal shortage-area incentives and can document need using exactly the data in this project.

**2. Build SUD capacity alongside MH capacity — not as an afterthought.** Washington's SUD treatment gap (15.6 pp) is nearly five times its MH gap (3.3 pp). Any behavioral health initiative that focuses exclusively on mental health while underfunding SUD treatment is addressing a fraction of the actual unmet need.

**3. Use HPSA score and designated population together for priority-setting.** Score alone (shortage severity) and population alone (scale) tell different stories. Yakima presents the optimal combination: high severity *and* large scale. Ferry County has the highest score but the smallest designated population — meaningful for targeted provider recruitment but lower programmatic impact than Yakima.

**4. Address the AMI prevalence-treatment gap asymmetry at the state level.** Washington's treatment rate is above average, but its prevalence is growing faster than access. State-level investment in telehealth, school-based mental health services, and integrated primary care behavioral health — particularly in high-prevalence rural counties — is needed to close the structural gap.

**5. Standardize data quality audits as pre-submission requirements for federal reporting.** The zero-violation audit in Query 4 confirms dataset integrity for this project. CCBHCs submitting federal demonstration grant reports should run equivalent programmatic checks before submission to prevent data quality flags that delay reimbursement or grant renewals.

---

## Repo Structure

```
chronic-disease-mapping-wa/
├── README.md
├── Code.py                          ← all code: DB build, SQL queries, all 8 charts
├── data/
│   ├── nsduh_state_estimates.csv    ← all 51 states, 8 behavioral health metrics
│   └── hrsa_hpsa_wa.csv             ← 30 WA county HPSA designations
└── outputs/
    ├── treatment_gap_by_state.csv   ← all 51 states ranked by treatment gap
    ├── wa_vs_national.csv           ← 2-row WA vs. national comparison
    ├── yakima_shortage_rank.csv     ← WA counties ranked by HPSA score
    ├── fig1_treatment_gap_ranking.png
    ├── fig2_wa_vs_national.png
    ├── fig3_yakima_hpsa_rank.png
    ├── fig4_prevalence_vs_treatment.png
    ├── fig5_gap_distribution.png
    ├── fig6_mh_vs_sud_gaps.png
    ├── fig7_unmet_need_ranking.png
    └── fig8_hpsa_bubble.png
```

---

## Running the Analysis

```bash
pip install matplotlib numpy
python Code.py
```

The script builds `behavioral_health.db` in the working directory, prints all five SQL query results to stdout, exports output CSVs, and saves all eight charts to `outputs/`.

---

## Skills Demonstrated

Relational database design · multi-table SQL queries with window functions · federal health data sourcing and interpretation · data quality auditing · population-level gap analysis · EDA and data visualization · CCBHC reporting context · validation of official agency claims against primary data · communication to non-technical audiences

---

*© 2026 Waleed Adawi. This project and its contents — including all code, analysis, visualizations, and written documentation — are the original work of the author. All federal datasets used are in the public domain and sourced from SAMHSA and HRSA. Reproduction or redistribution of this work requires attribution.*
