"""
Chronic Disease Mapping — Washington State Census Tracts
=========================================================
Exploratory data analysis of CDC PLACES 2024 data for ~1,770
Washington State census tracts. Produces scatterplots, a
correlation matrix, county-level bar charts, and distribution
histograms — all saved to outputs/.

Author : Waleed Adawi (portfolio adaptation of capstone team work)
Stack  : Python 3 · pandas · matplotlib · seaborn · numpy
Data   : CDC PLACES 2024 release (census-tract level)
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ── paths ────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data", "places_wa_clean.csv")
OUT  = os.path.join(BASE, "outputs")
os.makedirs(OUT, exist_ok=True)

# ── load & subset ────────────────────────────────────────────
df = pd.read_csv(DATA, dtype={"tract_fips": str})

VARS = {
    # health outcomes
    "diabetes_crude_prev":  "Diabetes",
    "obesity_crude_prev":   "Obesity",
    "bphigh_crude_prev":    "High Blood Pressure",
    # health behaviors
    "csmoking_crude_prev":  "Smoking",
    "lpa_crude_prev":       "Physical Inactivity",
    # access / prevention
    "checkup_crude_prev":   "Routine Checkups",
    "access2_crude_prev":   "Lack of Insurance",
}

sub = df[["county_name", "tract_fips"] + list(VARS.keys())].copy()

# ── palette ──────────────────────────────────────────────────
BG       = "#FAFAFA"
ACCENT   = "#005f73"
ACCENT2  = "#0a9396"
GRID_CLR = "#E0E0E0"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor":   BG,
    "axes.grid":        True,
    "grid.color":       GRID_CLR,
    "grid.linewidth":   0.4,
    "font.family":      "sans-serif",
    "font.size":        11,
})

# ── Fig 1 — Correlation matrix ───────────────────────────────
corr = sub[list(VARS.keys())].corr()
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
ax.set_title("Correlation Matrix — Key Health Indicators\nWashington Census Tracts (CDC PLACES 2024)",
             fontsize=13, fontweight="bold", pad=14)
plt.tight_layout()
fig.savefig(os.path.join(OUT, "fig1_correlation_matrix.png"), dpi=180)
plt.close(fig)
print("  ✓ fig1_correlation_matrix.png")

# ── Fig 2 — Scatterplot grid (4 key relationships) ──────────
pairs = [
    ("lpa_crude_prev",    "obesity_crude_prev",  "Physical Inactivity vs Obesity"),
    ("bphigh_crude_prev", "diabetes_crude_prev", "High Blood Pressure vs Diabetes"),
    ("obesity_crude_prev","diabetes_crude_prev",  "Obesity vs Diabetes"),
    ("csmoking_crude_prev","bphigh_crude_prev",  "Smoking vs High Blood Pressure"),
]

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
for ax, (xvar, yvar, title) in zip(axes.flat, pairs):
    ax.scatter(sub[xvar], sub[yvar], alpha=0.35, s=14, color=ACCENT, edgecolors="none")
    # linear fit
    m, b = np.polyfit(sub[xvar].dropna(), sub[yvar].dropna(), 1)
    xline = np.linspace(sub[xvar].min(), sub[xvar].max(), 100)
    ax.plot(xline, m * xline + b, color="#bb3e03", linewidth=1.8)
    r = sub[[xvar, yvar]].corr().iloc[0, 1]
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xlabel(VARS[xvar] + " (%)", fontsize=9)
    ax.set_ylabel(VARS[yvar] + " (%)", fontsize=9)
    ax.annotate(f"r = {r:.2f}", xy=(0.04, 0.92), xycoords="axes fraction",
                fontsize=10, color="#bb3e03", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#bb3e03", alpha=0.85))
fig.suptitle("Key Variable Relationships — Washington Census Tracts",
             fontsize=14, fontweight="bold", y=1.01)
plt.tight_layout()
fig.savefig(os.path.join(OUT, "fig2_scatterplot_grid.png"), dpi=180, bbox_inches="tight")
plt.close(fig)
print("  ✓ fig2_scatterplot_grid.png")

# ── Fig 3 — County bar chart (top 15 by diabetes prevalence) ─
county_avg = (
    sub.groupby("county_name")[list(VARS.keys())]
    .mean()
    .reset_index()
    .sort_values("diabetes_crude_prev", ascending=False)
)

top15 = county_avg.head(15).sort_values("diabetes_crude_prev")

fig, ax = plt.subplots(figsize=(10, 7))
colors = [ACCENT if c != "Yakima" else "#bb3e03" for c in top15["county_name"]]
ax.barh(top15["county_name"], top15["diabetes_crude_prev"], color=colors, edgecolor="white", height=0.7)
ax.set_xlabel("Average Diabetes Crude Prevalence (%)", fontsize=11)
ax.set_title("Top 15 Counties by Average Diabetes Prevalence\nWashington State — CDC PLACES 2024",
             fontsize=13, fontweight="bold", pad=12)
for i, (val, county) in enumerate(zip(top15["diabetes_crude_prev"], top15["county_name"])):
    ax.text(val + 0.15, i, f"{val:.1f}%", va="center", fontsize=9, color="#333")
ax.set_xlim(0, top15["diabetes_crude_prev"].max() * 1.15)
sns.despine(left=True)
plt.tight_layout()
fig.savefig(os.path.join(OUT, "fig3_county_diabetes_ranking.png"), dpi=180)
plt.close(fig)
print("  ✓ fig3_county_diabetes_ranking.png")

# ── Fig 4 — Distribution histograms (health outcomes) ────────
outcome_vars = ["diabetes_crude_prev", "obesity_crude_prev", "bphigh_crude_prev"]
fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
hist_colors = [ACCENT, ACCENT2, "#94d2bd"]
for ax, var, clr in zip(axes, outcome_vars, hist_colors):
    ax.hist(sub[var].dropna(), bins=30, color=clr, edgecolor="white", linewidth=0.5)
    med = sub[var].median()
    ax.axvline(med, color="#bb3e03", linewidth=1.5, linestyle="--", label=f"Median: {med:.1f}%")
    ax.set_title(VARS[var], fontsize=11, fontweight="bold")
    ax.set_xlabel("Crude Prevalence (%)", fontsize=9)
    ax.set_ylabel("Census Tracts", fontsize=9)
    ax.legend(fontsize=8)
fig.suptitle("Distribution of Health Outcomes Across Census Tracts",
             fontsize=13, fontweight="bold", y=1.02)
plt.tight_layout()
fig.savefig(os.path.join(OUT, "fig4_outcome_distributions.png"), dpi=180, bbox_inches="tight")
plt.close(fig)
print("  ✓ fig4_outcome_distributions.png")

# ── summary CSVs ─────────────────────────────────────────────
county_avg.to_csv(os.path.join(OUT, "county_averages.csv"), index=False)
corr.to_csv(os.path.join(OUT, "correlation_matrix.csv"))
print("  ✓ county_averages.csv")
print("  ✓ correlation_matrix.csv")

print("\n✅ All outputs saved to outputs/")
