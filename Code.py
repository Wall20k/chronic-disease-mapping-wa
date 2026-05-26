"""
=============================================================================
Chronic Disease Mapping — Washington State Census Tracts
=============================================================================
Author  : Waleed Adawi
Course  : DATA 424 — Senior Capstone (Washington State University)
Year    : 2025
Project : CHORDS Lab — Interactive WA Census-Tract Health Data Map
Data    : CDC PLACES 2024 Release (census-tract level estimates)
Tools   : Python 3 · pandas · numpy · matplotlib · seaborn · scipy

Description
-----------
End-to-end analysis pipeline for the CHORDS Lab capstone project. This
script loads the CDC PLACES 2024 dataset filtered to Washington State
(~1,770 census tracts), cleans and validates the data, computes summary
statistics, generates exploratory visualizations, performs correlation
and regression analysis, and produces a static geographic map of chronic
disease prevalence across Washington.

The core objective is to help Extension scientists, community researchers,
and citizen scientists explore patterns in chronic disease prevalence and
related exposure variables at the census-tract level.

Run
---
    pip install pandas numpy matplotlib seaborn scipy
    python Code.py
=============================================================================
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# ==========================================================================
# 1.  CONFIGURATION
# ==========================================================================

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data", "places_wa_clean.csv")
OUT  = os.path.join(BASE, "outputs")
os.makedirs(OUT, exist_ok=True)

# Seven key health indicators selected for this project
VARS = {
    # -- Health Outcomes --
    "diabetes_crude_prev":  "Diabetes",
    "obesity_crude_prev":   "Obesity",
    "bphigh_crude_prev":    "High Blood Pressure",
    # -- Health Behaviors --
    "csmoking_crude_prev":  "Smoking",
    "lpa_crude_prev":       "Physical Inactivity",
    # -- Access & Prevention --
    "checkup_crude_prev":   "Routine Checkups",
    "access2_crude_prev":   "Lack of Insurance",
}

# Visual theme -- consistent across all figures
BG       = "#FAFAFA"
ACCENT   = "#005f73"
ACCENT2  = "#0a9396"
GRID_CLR = "#E0E0E0"
ALERT    = "#bb3e03"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor":   BG,
    "axes.grid":        True,
    "grid.color":       GRID_CLR,
    "grid.linewidth":   0.4,
    "font.family":      "sans-serif",
    "font.size":        11,
})


# ==========================================================================
# 2.  DATA LOADING & CLEANING
# ==========================================================================

print("=" * 65)
print("  Chronic Disease Mapping -- Washington State Census Tracts")
print("=" * 65)

print("\n[1/8] Loading CDC PLACES 2024 data ...")

if not os.path.exists(DATA):
    sys.exit(f"ERROR: Data file not found at {DATA}")

df_raw = pd.read_csv(DATA, dtype={"tract_fips": str, "county_fips": str})
print(f"       Loaded {df_raw.shape[0]:,} rows x {df_raw.shape[1]} columns")

keep_cols = ["state_abbr", "county_name", "county_fips", "tract_fips",
             "total_population"] + list(VARS.keys()) + ["geolocation"]
df = df_raw[keep_cols].copy()

print("[2/8] Validating and cleaning data ...")

for col in VARS:
    df[col] = pd.to_numeric(df[col], errors="coerce")

missing = df[list(VARS.keys())].isna().sum()
has_missing = missing[missing > 0]
if len(has_missing) > 0:
    print("       Missing values detected:")
    for col, n in has_missing.items():
        print(f"         {VARS[col]}: {n} tracts")
    before = len(df)
    df = df.dropna(subset=list(VARS.keys()))
    print(f"       Dropped {before - len(df)} incomplete rows")
else:
    print("       No missing values in key variables -- data is clean")

for col in VARS:
    out_of_range = ((df[col] < 0) | (df[col] > 100)).sum()
    if out_of_range > 0:
        print(f"       WARNING: {out_of_range} out-of-range values in {VARS[col]}")

coords = df["geolocation"].str.extract(r"POINT \(([^ ]+) ([^ ]+)\)")
df["longitude"] = coords[0].astype(float)
df["latitude"]  = coords[1].astype(float)

print(f"       Final dataset: {len(df):,} census tracts across "
      f"{df['county_name'].nunique()} counties")


# ==========================================================================
# 3.  SUMMARY STATISTICS
# ==========================================================================

print("[3/8] Computing summary statistics ...")

summary = df[list(VARS.keys())].describe().T
summary.index = [VARS[c] for c in summary.index]
summary = summary.round(2)

print("\n       Summary Statistics -- 7 Key Health Indicators")
print("       " + "-" * 57)
for idx, row in summary.iterrows():
    print(f"       {idx:<22s}  mean={row['mean']:5.1f}%  "
          f"std={row['std']:4.1f}  range=[{row['min']:.1f}, {row['max']:.1f}]")
print()


# ==========================================================================
# 4.  FIGURE 1 -- Correlation Matrix
# ==========================================================================

print("[4/8] Generating Fig 1 -- Correlation matrix ...")

corr = df[list(VARS.keys())].corr()
labels = [VARS[c] for c in corr.columns]

fig, ax = plt.subplots(figsize=(9, 7.5))
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
sns.heatmap(
    corr, mask=mask, annot=True, fmt=".2f",
    cmap="YlGnBu", vmin=-1, vmax=1,
    linewidths=0.6, linecolor="white",
    xticklabels=labels, yticklabels=labels,
    cbar_kws={"shrink": 0.75, "label": "Pearson r"},
    ax=ax,
)
ax.set_title(
    "Correlation Matrix -- Key Health Indicators\n"
    "Washington Census Tracts (CDC PLACES 2024)",
    fontsize=13, fontweight="bold", pad=14,
)
plt.tight_layout()
fig.savefig(os.path.join(OUT, "fig1_correlation_matrix.png"), dpi=180)
plt.close(fig)
print("       Done: fig1_correlation_matrix.png")

pairs_corr = []
cols = list(VARS.keys())
for i in range(len(cols)):
    for j in range(i + 1, len(cols)):
        r = corr.loc[cols[i], cols[j]]
        pairs_corr.append((VARS[cols[i]], VARS[cols[j]], r))
pairs_corr.sort(key=lambda x: abs(x[2]), reverse=True)
print("\n       Top 5 strongest correlations:")
for a, b, r in pairs_corr[:5]:
    print(f"         {a} <-> {b}: r = {r:.3f}")
print()


# ==========================================================================
# 5.  FIGURE 2 -- Scatterplot Grid (Key Relationships)
# ==========================================================================

print("[5/8] Generating Fig 2 -- Scatterplot grid ...")

pairs = [
    ("lpa_crude_prev",      "obesity_crude_prev",   "Physical Inactivity vs Obesity"),
    ("bphigh_crude_prev",   "diabetes_crude_prev",  "High Blood Pressure vs Diabetes"),
    ("obesity_crude_prev",  "diabetes_crude_prev",  "Obesity vs Diabetes"),
    ("csmoking_crude_prev", "bphigh_crude_prev",    "Smoking vs High Blood Pressure"),
]

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
for ax, (xvar, yvar, title) in zip(axes.flat, pairs):
    ax.scatter(df[xvar], df[yvar], alpha=0.35, s=14,
               color=ACCENT, edgecolors="none")
    m, b = np.polyfit(df[xvar].dropna(), df[yvar].dropna(), 1)
    xline = np.linspace(df[xvar].min(), df[xvar].max(), 100)
    ax.plot(xline, m * xline + b, color=ALERT, linewidth=1.8)
    r = df[[xvar, yvar]].corr().iloc[0, 1]
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xlabel(VARS[xvar] + " (%)", fontsize=9)
    ax.set_ylabel(VARS[yvar] + " (%)", fontsize=9)
    ax.annotate(
        f"r = {r:.2f}", xy=(0.04, 0.92), xycoords="axes fraction",
        fontsize=10, color=ALERT, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="white",
                  ec=ALERT, alpha=0.85),
    )

fig.suptitle(
    "Key Variable Relationships -- Washington Census Tracts",
    fontsize=14, fontweight="bold", y=1.01,
)
plt.tight_layout()
fig.savefig(os.path.join(OUT, "fig2_scatterplot_grid.png"),
            dpi=180, bbox_inches="tight")
plt.close(fig)
print("       Done: fig2_scatterplot_grid.png")


# ==========================================================================
# 6.  FIGURE 3 -- County Ranking (Top 15 by Diabetes Prevalence)
# ==========================================================================

print("[6/8] Generating Fig 3 -- County diabetes ranking ...")

county_avg = (
    df.groupby("county_name")[list(VARS.keys())]
    .mean()
    .reset_index()
    .sort_values("diabetes_crude_prev", ascending=False)
)

top15 = county_avg.head(15).sort_values("diabetes_crude_prev")

fig, ax = plt.subplots(figsize=(10, 7))
colors = [ACCENT if c != "Ferry" else ALERT for c in top15["county_name"]]
ax.barh(top15["county_name"], top15["diabetes_crude_prev"],
        color=colors, edgecolor="white", height=0.7)
ax.set_xlabel("Average Diabetes Crude Prevalence (%)", fontsize=11)
ax.set_title(
    "Top 15 Counties by Average Diabetes Prevalence\n"
    "Washington State -- CDC PLACES 2024",
    fontsize=13, fontweight="bold", pad=12,
)
for i, (val, county) in enumerate(
        zip(top15["diabetes_crude_prev"], top15["county_name"])):
    ax.text(val + 0.15, i, f"{val:.1f}%", va="center", fontsize=9, color="#333")
ax.set_xlim(0, top15["diabetes_crude_prev"].max() * 1.15)
sns.despine(left=True)
plt.tight_layout()
fig.savefig(os.path.join(OUT, "fig3_county_diabetes_ranking.png"), dpi=180)
plt.close(fig)
print("       Done: fig3_county_diabetes_ranking.png")

print(f"\n       Highest: {county_avg.iloc[0]['county_name']} "
      f"({county_avg.iloc[0]['diabetes_crude_prev']:.1f}%)")
print(f"       Lowest:  {county_avg.iloc[-1]['county_name']} "
      f"({county_avg.iloc[-1]['diabetes_crude_prev']:.1f}%)")
print()


# ==========================================================================
# 7.  FIGURE 4 -- Distribution Histograms
# ==========================================================================

print("[7/8] Generating Fig 4 -- Outcome distributions ...")

outcome_vars = ["diabetes_crude_prev", "obesity_crude_prev", "bphigh_crude_prev"]
fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
hist_colors = [ACCENT, ACCENT2, "#94d2bd"]

for ax, var, clr in zip(axes, outcome_vars, hist_colors):
    ax.hist(df[var].dropna(), bins=30, color=clr,
            edgecolor="white", linewidth=0.5)
    med = df[var].median()
    ax.axvline(med, color=ALERT, linewidth=1.5, linestyle="--",
               label=f"Median: {med:.1f}%")
    ax.set_title(VARS[var], fontsize=11, fontweight="bold")
    ax.set_xlabel("Crude Prevalence (%)", fontsize=9)
    ax.set_ylabel("Census Tracts", fontsize=9)
    ax.legend(fontsize=8)

fig.suptitle(
    "Distribution of Health Outcomes Across Census Tracts",
    fontsize=13, fontweight="bold", y=1.02,
)
plt.tight_layout()
fig.savefig(os.path.join(OUT, "fig4_outcome_distributions.png"),
            dpi=180, bbox_inches="tight")
plt.close(fig)
print("       Done: fig4_outcome_distributions.png")


# ==========================================================================
# 8.  FIGURE 5 -- Static Choropleth Map (Diabetes Prevalence)
# ==========================================================================

print("[8/8] Generating Fig 5 -- Census-tract map of diabetes prevalence ...")

fig, ax = plt.subplots(figsize=(14, 10))
ax.set_facecolor("#e8ecf1")

sc = ax.scatter(
    df["longitude"], df["latitude"],
    c=df["diabetes_crude_prev"],
    cmap="YlOrRd",
    s=12,
    alpha=0.75,
    edgecolors="none",
    vmin=df["diabetes_crude_prev"].quantile(0.02),
    vmax=df["diabetes_crude_prev"].quantile(0.98),
)

cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.02)
cbar.set_label("Diabetes Crude Prevalence (%)", fontsize=11)

for _, row in county_avg.head(5).iterrows():
    county_tracts = df[df["county_name"] == row["county_name"]]
    cx = county_tracts["longitude"].mean()
    cy = county_tracts["latitude"].mean()
    ax.annotate(
        f"{row['county_name']}\n{row['diabetes_crude_prev']:.1f}%",
        xy=(cx, cy), fontsize=8, fontweight="bold",
        color="#333", ha="center",
        bbox=dict(boxstyle="round,pad=0.25", fc="white",
                  ec="#999", alpha=0.85),
    )

ax.set_title(
    "Diabetes Prevalence by Census Tract -- Washington State\n"
    "CDC PLACES 2024  |  Each dot = one census tract",
    fontsize=14, fontweight="bold", pad=14,
)
ax.set_xlabel("Longitude", fontsize=10)
ax.set_ylabel("Latitude", fontsize=10)
ax.set_aspect(1.3)
ax.grid(True, alpha=0.3)

plt.tight_layout()
fig.savefig(os.path.join(OUT, "fig5_wa_diabetes_map.png"),
            dpi=200, bbox_inches="tight")
plt.close(fig)
print("       Done: fig5_wa_diabetes_map.png")


# ==========================================================================
# 9.  EXPORT SUMMARY DATA
# ==========================================================================

print("\nExporting summary data ...")

county_avg.to_csv(os.path.join(OUT, "county_averages.csv"), index=False)
print("       Done: county_averages.csv")

corr.to_csv(os.path.join(OUT, "correlation_matrix.csv"))
print("       Done: correlation_matrix.csv")

summary.to_csv(os.path.join(OUT, "summary_statistics.csv"))
print("       Done: summary_statistics.csv")


# ==========================================================================
# 10.  FINAL REPORT
# ==========================================================================

print("\n" + "=" * 65)
print("  ANALYSIS COMPLETE")
print("=" * 65)
print(f"""
  Dataset : CDC PLACES 2024 -- Washington State
  Tracts  : {len(df):,}
  Counties: {df['county_name'].nunique()}

  Outputs saved to {OUT}/
    - fig1_correlation_matrix.png
    - fig2_scatterplot_grid.png
    - fig3_county_diabetes_ranking.png
    - fig4_outcome_distributions.png
    - fig5_wa_diabetes_map.png
    - county_averages.csv
    - correlation_matrix.csv
    - summary_statistics.csv
""")
