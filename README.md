# Chronic Disease & Community Health Mapping — Washington State

**Author:** Waleed Al-Adawi · **Year:** 2024 · **Stack:** R (Shiny + Leaflet + sf) · Python (pandas + matplotlib + seaborn) · **Data:** CDC PLACES 2024

---

## Overview

This project examines how chronic disease prevalence, behavioral risk factors, and access-to-care measures overlap at the census-tract level across Washington State. Using the CDC PLACES 2024 dataset — which provides modeled health estimates for all ~1,770 tracts in the state — the analysis identifies geographic clusters where multiple health burdens concentrate simultaneously, revealing communities that face compounding disadvantages in physical inactivity, obesity, diabetes, high blood pressure, smoking, and insurance coverage.

The centerpiece deliverable is an **interactive Shiny web application** that lets users select any combination of seven health variables, set custom prevalence thresholds using statistically-informed sliders, and instantly visualize which census tracts meet all selected criteria on a Leaflet map. This enables public health practitioners, researchers, and policymakers to pinpoint high-need areas for targeted intervention — moving beyond single-indicator dashboards toward a layered, multi-variable geographic lens.

This work was completed as part of a capstone project (DATA 424) through the CHORDS Lab at Eastern Washington University.

**Skills demonstrated:** geospatial analysis, interactive web application development, multivariate health data exploration, census-tract-level epidemiological mapping, correlation analysis, clustering, publication-quality data visualization, R Shiny full-stack development

---

## Key Findings

1. **High blood pressure and diabetes show the strongest linear relationship** across Washington census tracts (r = 0.88), meaning communities burdened by one condition almost universally carry elevated rates of the other — suggesting shared socioeconomic or environmental drivers.

2. **Physical inactivity and obesity are tightly coupled** (r = 0.81), with tracts in central and eastern Washington consistently scoring high on both. The relationship follows a steep positive slope indicating that even small shifts in activity rates correspond to meaningful differences in obesity prevalence.

3. **Physical inactivity and diabetes co-occur strongly** (r = 0.78), reinforcing that sedentary-behavior tracts face compounding chronic disease burden beyond obesity alone.

4. **Smoking and obesity are strongly associated** (r = 0.83), with tracts that have high smoking rates almost invariably showing elevated obesity, reinforcing the behavioral clustering pattern at the sub-county geographic scale.

5. **High-burden tracts concentrate in central and eastern Washington** — Yakima, Grant, Franklin, Adams, and Okanogan counties contain the largest shares of tracts where diabetes, obesity, and inactivity simultaneously exceed statewide medians.

6. **Lack of health insurance correlates positively with diabetes and obesity prevalence**, suggesting that access barriers compound existing chronic disease disparities in underserved tracts.

---

## Visualizations

### Fig 1 — Correlation Matrix (Seven Health Variables)

![Correlation Matrix](outputs/fig1_correlation_matrix.png)

A lower-triangle heatmap showing Pearson correlations among all seven selected health measures across ~1,770 census tracts. The color gradient (light yellow to deep teal) encodes correlation strength, with annotated r-values in each cell. The matrix reveals a clear block of strongly intercorrelated chronic conditions (diabetes, BP, obesity, physical inactivity) in the upper-left quadrant, while access and prevention measures show weaker but still meaningful associations. This visualization guided the scatterplot analysis by identifying which variable pairs warranted closer examination.

### Fig 2 — Scatterplot Grid (Key Variable Pairs)

![Scatterplot Grid](outputs/fig2_scatterplot_grid.png)

A 2x2 panel showing the four most policy-relevant relationships at tract level: physical inactivity vs. obesity (r = 0.81), high blood pressure vs. diabetes (r = 0.88), obesity vs. diabetes (r = 0.73), and smoking vs. high blood pressure (r = 0.50). Each panel includes a fitted regression line and the Pearson r annotation. Points are semi-transparent to reveal density clustering — the tight linear bands in the BP-diabetes and inactivity-obesity panels confirm these are not driven by outliers but represent consistent population-level gradients across Washington communities.

### Fig 3 — County Diabetes Prevalence Ranking

![County Ranking](outputs/fig3_county_diabetes_ranking.png)

A horizontal bar chart of the top 15 counties by mean diabetes prevalence (averaged across tracts within each county). Ferry County leads at 15.6%, followed by Pacific (15.0%) and Okanogan (14.4%). Yakima County (12.9%), highlighted in burnt orange as the capstone focus area, ranks sixth — all in central/eastern Washington. King County (Seattle metro) appears near the bottom with roughly 9%. This county-level view complements the tract-level map by showing which jurisdictions carry the highest aggregate chronic disease burden and would benefit most from targeted public health investment.

### Fig 4 — Distribution of Key Health Outcomes

![Distributions](outputs/fig4_outcome_distributions.png)

Three side-by-side histograms showing the tract-level distribution of diabetes, obesity, and high blood pressure prevalence across all Washington census tracts. Vertical dashed lines mark the statewide median for each measure. Diabetes shows a right-skewed distribution with a long tail extending above 18%, indicating a subset of tracts with substantially elevated rates. Obesity and BP follow roughly normal distributions but with notable right shoulders. These distributions informed the threshold-setting logic in the Shiny app's slider controls.

---

## Interactive Shiny Application

The crown jewel of this project is a full-stack **R Shiny web application** that brings the analysis to life:

- **Multi-variable filtering** — Select any combination of 7 health indicators via checkboxes
- **Dynamic threshold sliders** — Ranges auto-adjust to each variable's data spread, with built-in statistical reference points (mean, median, Q3) displayed as guide text
- **Interactive Leaflet map** — Census tracts meeting ALL selected thresholds highlight in crimson (#990000) on a CartoDB base layer
- **Tract-level popups** — Click any highlighted tract to see its exact prevalence values for all selected variables
- **Real-time summary statistics** — Header displays count of matching tracts and percentage of state total

The app enables public health professionals to ask questions like: *"Which census tracts have diabetes above 12%, obesity above 35%, AND lack of insurance above 15%?"* — and get an instant geographic answer.

**Tech stack:** R · Shiny · Leaflet · sf · dplyr · htmltools · scales

---

## Team Acknowledgment

This project was a collaborative capstone effort. Huge shout-out to my teammates who made this work possible:

- **Audrey Kimball** — data processing, report writing, and analysis contributions
- **Caleb Graves** — project coordination, methodology design, and EDA work
- **Maxwell Yenney** — data wrangling, visualization development, and technical implementation

Working with this team through the CHORDS Lab capstone was an outstanding experience. The depth of analysis and the interactive application we delivered together far exceeded what any one person could accomplish alone.

---

## Data Sources

| Dataset | Source | Granularity | Year |
|---------|--------|-------------|------|
| CDC PLACES | Centers for Disease Control and Prevention | Census tract | 2024 release |
| TIGER/Line Shapefiles | U.S. Census Bureau | Census tract boundaries | 2022 |

---

## Methodology

```
eda_analysis.py
├── load_data()          # Read places_wa_clean.csv, subset 7 key variables
├── correlation_matrix() # Pearson r across all variable pairs → heatmap
├── scatterplot_grid()   # 2×2 panel of strongest/most relevant pairs
├── county_ranking()     # Aggregate tract means by county → bar chart
└── distributions()      # Histogram panel for diabetes, obesity, BP

shiny-app/app.R
├── ui
│   ├── checkboxGroupInput()   # Variable selection (7 indicators)
│   ├── dynamic sliderInput()  # Threshold controls with stat guides
│   └── leafletOutput()        # Map rendering panel
└── server
    ├── reactive_filters()     # Apply selected thresholds to tract data
    ├── render_leaflet()       # Base map + CartoDB tiles
    ├── observe_proxy()        # Update polygons on filter change
    └── popup_builder()        # Tract-level detail on click
```

---

## Repo Structure

```
chronic-disease-mapping-wa/
├── README.md
├── eda_analysis.py              # Python EDA → 4 figures + 2 CSVs
├── requirements.txt             # Python dependencies
├── data/
│   ├── places_wa_clean.csv      # CDC PLACES 2024 (WA tracts, ~1,770 rows)
│   └── sources.md               # Data source documentation
├── outputs/
│   ├── fig1_correlation_matrix.png
│   ├── fig2_scatterplot_grid.png
│   ├── fig3_county_diabetes_ranking.png
│   ├── fig4_outcome_distributions.png
│   ├── correlation_matrix.csv
│   └── county_averages.csv
├── shiny-app/
│   └── app.R                    # Interactive Leaflet mapping tool
├── LICENSE
└── .gitignore
```

---

## Running the Analysis

```bash
# Python EDA (generates all figures and summary tables)
pip install -r requirements.txt
python eda_analysis.py

# Shiny application (requires R with shiny, leaflet, sf, dplyr)
cd shiny-app
Rscript -e "shiny::runApp('app.R', port = 3838)"
```

---

## Relevance

Washington's Department of Health and regional Accountable Communities of Health (ACHs) prioritize data-driven approaches to reduce chronic disease disparities. This analysis directly supports those efforts by:

- Identifying specific census tracts where multiple health burdens overlap — enabling precision public health targeting rather than broad county-level interventions
- Demonstrating that behavioral risk factors (inactivity, smoking) and chronic outcomes (diabetes, BP, obesity) cluster geographically, suggesting shared community-level determinants
- Providing an interactive tool that health departments, community health workers, and grant writers can use to justify resource allocation to the highest-need areas

The approach mirrors methods used by the Washington State Cancer Registry, CHORDS Lab, and CDC's own 500 Cities/PLACES initiative — applying sub-county analytics to move beyond aggregate statistics toward actionable geographic intelligence.

---

## License

Code: [MIT License](LICENSE)
Non-code content (figures, documentation): [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)
