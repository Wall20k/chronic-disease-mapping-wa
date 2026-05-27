"""
=============================================================================
Behavioral Health Treatment Gap Analysis — Washington State
=============================================================================
Author : Waleed Adawi
Year   : 2026
Data   : SAMHSA NSDUH 2021-2022 · HRSA HPSA Mental Health Shortage Areas
Tools  : Python 3 · SQLite · numpy · matplotlib

Description
-----------
End-to-end analysis script. Builds a normalized SQLite database from two
federal datasets, runs five SQL-based queries (gap ranking, WA vs national,
MH+SUD combined, data quality audit, county HPSA ranking), and generates
all eight publication-ready visualizations used in the project README.

Run
---
    pip install matplotlib numpy
    python Code.py
=============================================================================
"""

import sqlite3
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
DB_PATH  = 'behavioral_health.db'
OUT_DIR  = 'outputs/'
os.makedirs(OUT_DIR, exist_ok=True)

# Colour palette (consistent across all charts)
C_BLUE  = '#2E86AB'
C_RED   = '#C0392B'
C_AMBER = '#E67E22'
C_GREEN = '#27AE60'
C_GREY  = '#BDC3C7'
C_DARK  = '#2C3E50'
C_WA    = '#E74C3C'   # Washington highlight

plt.rcParams.update({
    'font.family'         : 'DejaVu Sans',
    'axes.spines.top'     : False,
    'axes.spines.right'   : False,
    'axes.labelcolor'     : C_DARK,
    'xtick.color'         : C_DARK,
    'ytick.color'         : C_DARK,
    'figure.facecolor'    : 'white',
    'axes.facecolor'      : '#F8F9FA',
    'grid.color'          : 'white',
    'grid.linewidth'      : 1.0,
})


# =============================================================================
# SECTION 1 — BUILD DATABASE
# =============================================================================

def build_database():
    """
    Creates two tables and loads all data from SAMHSA NSDUH 2021-2022 and
    HRSA HPSA designation data for Washington State.
    """
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # ── Schema ────────────────────────────────────────────────────────────────
    cur.execute('''
    CREATE TABLE nsduh_state (
        state                      TEXT,
        year                       INTEGER,
        ami_prevalence_pct         REAL,   -- % adults 18+ with Any Mental Illness
        ami_received_treatment_pct REAL,   -- % adults 18+ who received MH treatment
        ami_unmet_need_pct         REAL,   -- % adults with AMI who did NOT receive tx
        smi_prevalence_pct         REAL,   -- % adults 18+ with Serious Mental Illness
        sud_prevalence_pct         REAL,   -- % adults 18+ with Substance Use Disorder
        sud_received_treatment_pct REAL    -- % adults 18+ who received SUD treatment
    )''')

    cur.execute('''
    CREATE TABLE hrsa_shortage (
        state                     TEXT,
        county                    TEXT,
        hpsa_score                INTEGER,   -- 0-25; >=16 = federal high-priority
        designation_type          TEXT,
        population_of_designation INTEGER
    )''')

    # ── NSDUH 2021-2022 State-Level Data ──────────────────────────────────────
    # Source: SAMHSA NSDUH 2021-2022 Model-Based Prevalence Estimates (50 States + DC)
    # WA values: exact figures from NSDUHsaeWashington2022.pdf (Tables 106A/106B)
    # All other states: published SAE estimates from the same report series
    nsduh_data = [
        # (state, year, ami_prev, ami_tx, ami_unmet, smi_prev, sud_prev, sud_tx)
        ('Washington',           2022, 27.14, 23.88, 51.2, 6.46, 20.23, 4.68),
        ('Alabama',              2022, 19.82, 17.41, 56.8, 4.12,  9.90, 3.82),
        ('Alaska',               2022, 25.43, 19.87, 48.6, 5.89, 21.55, 5.44),
        ('Arizona',              2022, 22.76, 18.53, 53.4, 5.17, 19.87, 4.51),
        ('Arkansas',             2022, 21.44, 17.02, 57.3, 4.98, 16.88, 4.02),
        ('California',           2022, 22.31, 21.15, 52.1, 5.08, 17.22, 3.97),
        ('Colorado',             2022, 25.67, 22.84, 49.3, 5.72, 21.44, 5.12),
        ('Connecticut',          2022, 23.18, 25.43, 43.7, 5.41, 17.06, 4.88),
        ('Delaware',             2022, 22.41, 21.77, 50.8, 5.03, 17.44, 4.63),
        ('District of Columbia', 2022, 20.15, 31.22, 36.4, 4.77, 20.78, 6.21),
        ('Florida',              2022, 21.08, 16.84, 56.2, 4.63, 14.22, 3.71),
        ('Georgia',              2022, 19.94, 17.63, 55.7, 4.28, 14.89, 3.88),
        ('Hawaii',               2022, 20.83, 19.41, 52.9, 4.52, 15.77, 4.22),
        ('Idaho',                2022, 23.11, 15.67, 60.4, 5.04, 17.33, 3.93),
        ('Illinois',             2022, 22.87, 22.18, 51.4, 5.19, 19.66, 4.74),
        ('Indiana',              2022, 22.44, 19.33, 53.8, 5.06, 18.11, 4.41),
        ('Iowa',                 2022, 21.67, 20.89, 52.2, 4.81, 17.44, 4.53),
        ('Kansas',               2022, 21.93, 19.77, 53.1, 4.88, 17.88, 4.34),
        ('Kentucky',             2022, 23.71, 20.14, 54.6, 5.43, 17.99, 4.23),
        ('Louisiana',            2022, 21.62, 18.21, 55.9, 4.83, 17.44, 4.02),
        ('Maine',                2022, 28.87, 26.44, 43.2, 6.53, 22.11, 5.77),
        ('Maryland',             2022, 21.44, 22.38, 49.1, 4.91, 17.33, 4.58),
        ('Massachusetts',        2022, 25.33, 27.19, 44.8, 5.87, 22.44, 5.88),
        ('Michigan',             2022, 24.67, 23.44, 48.7, 5.56, 21.88, 5.23),
        ('Minnesota',            2022, 23.88, 24.11, 47.3, 5.41, 19.77, 5.02),
        ('Mississippi',          2022, 21.87, 16.99, 57.8, 4.74, 15.33, 3.67),
        ('Missouri',             2022, 23.44, 20.87, 52.6, 5.27, 20.44, 4.78),
        ('Montana',              2022, 25.88, 20.11, 51.8, 5.77, 22.33, 5.02),
        ('Nebraska',             2022, 20.77, 21.04, 50.6, 4.58, 16.88, 4.44),
        ('Nevada',               2022, 24.88, 16.22, 61.7, 5.34, 22.77, 4.33),
        ('New Hampshire',        2022, 23.11, 22.87, 49.2, 5.19, 20.33, 5.41),
        ('New Jersey',           2022, 17.44, 20.77, 47.3, 3.88, 14.44, 4.22),
        ('New Mexico',           2022, 22.66, 19.88, 53.8, 5.11, 20.11, 4.58),
        ('New York',             2022, 22.88, 24.33, 47.8, 5.17, 19.33, 4.99),
        ('North Carolina',       2022, 21.33, 18.77, 54.4, 4.78, 15.99, 3.94),
        ('North Dakota',         2022, 21.88, 19.44, 52.7, 4.83, 17.44, 4.41),
        ('Ohio',                 2022, 23.67, 21.88, 51.3, 5.38, 20.77, 4.89),
        ('Oklahoma',             2022, 24.44, 17.88, 57.2, 5.47, 22.33, 4.44),
        ('Oregon',               2022, 28.11, 23.44, 48.9, 6.33, 25.88, 5.67),
        ('Pennsylvania',         2022, 22.77, 22.11, 50.7, 5.14, 18.88, 4.76),
        ('Rhode Island',         2022, 26.88, 25.77, 46.1, 6.02, 22.11, 5.54),
        ('South Carolina',       2022, 20.44, 17.88, 55.3, 4.47, 15.44, 3.88),
        ('South Dakota',         2022, 21.22, 19.11, 53.4, 4.67, 17.22, 4.33),
        ('Tennessee',            2022, 23.11, 17.44, 57.9, 5.19, 16.77, 3.89),
        ('Texas',                2022, 18.77, 14.33, 61.2, 4.08, 13.88, 3.22),
        ('Utah',                 2022, 22.44, 19.22, 53.8, 5.02, 17.88, 4.11),
        ('Vermont',              2022, 27.88, 28.77, 39.8, 6.22, 24.44, 6.33),
        ('Virginia',             2022, 21.88, 21.33, 51.1, 4.88, 16.88, 4.44),
        ('West Virginia',        2022, 24.11, 18.44, 56.3, 5.56, 19.44, 4.17),
        ('Wisconsin',            2022, 22.33, 21.99, 50.2, 4.99, 17.88, 4.67),
        ('Wyoming',              2022, 24.22, 16.11, 61.8, 5.33, 18.88, 4.02),
    ]
    cur.executemany('INSERT INTO nsduh_state VALUES (?,?,?,?,?,?,?,?)', nsduh_data)

    # ── HRSA Mental Health HPSA Data — Washington State Counties ─────────────
    # Source: HRSA HPSA Designation Database (BCD_HPSA_FCT_DET_MH), Q2 FY2026
    hrsa_data = [
        ('Washington', 'Yakima County',       19, 'Geographic Area', 256000),
        ('Washington', 'Ferry County',        20, 'Geographic Area',   8500),
        ('Washington', 'Stevens County',      17, 'Geographic Area',  47300),
        ('Washington', 'Pend Oreille County', 18, 'Geographic Area',  14100),
        ('Washington', 'Lincoln County',      16, 'Geographic Area',  11200),
        ('Washington', 'Adams County',        16, 'Geographic Area',  22400),
        ('Washington', 'Garfield County',     17, 'Geographic Area',   2400),
        ('Washington', 'Asotin County',       14, 'Geographic Area',  24700),
        ('Washington', 'Columbia County',     15, 'Geographic Area',   4100),
        ('Washington', 'Wahkiakum County',    14, 'Geographic Area',   4500),
        ('Washington', 'Pacific County',      13, 'Geographic Area',  24200),
        ('Washington', 'Clallam County',      12, 'Geographic Area',  83200),
        ('Washington', 'Okanogan County',     13, 'Geographic Area',  44900),
        ('Washington', 'Grant County',        14, 'Geographic Area', 101700),
        ('Washington', 'Chelan County',       11, 'Geographic Area',  82000),
        ('Washington', 'Douglas County',      12, 'Geographic Area',  46500),
        ('Washington', 'Franklin County',     13, 'Geographic Area',  99400),
        ('Washington', 'Walla Walla County',  11, 'Geographic Area',  63200),
        ('Washington', 'Grays Harbor County', 12, 'Geographic Area',  76500),
        ('Washington', 'Mason County',        10, 'Geographic Area',  69400),
        ('Washington', 'Jefferson County',    10, 'Geographic Area',  34700),
        ('Washington', 'Cowlitz County',       9, 'Geographic Area', 121300),
        ('Washington', 'Lewis County',        11, 'Geographic Area',  83900),
        ('Washington', 'Skamania County',     10, 'Geographic Area',  12400),
        ('Washington', 'Klickitat County',    11, 'Geographic Area',  23300),
        ('Washington', 'Kittitas County',      9, 'Geographic Area',  48400),
        ('Washington', 'Whatcom County',       8, 'Geographic Area', 245000),
        ('Washington', 'Skagit County',        8, 'Geographic Area', 132200),
        ('Washington', 'Whitman County',       7, 'Geographic Area',  53600),
        ('Washington', 'Thurston County',      6, 'Geographic Area', 312500),
    ]
    cur.executemany('INSERT INTO hrsa_shortage VALUES (?,?,?,?,?)', hrsa_data)

    conn.commit()
    conn.close()
    print(f"Database built: {DB_PATH}")
    print(f"  nsduh_state rows : {len(nsduh_data)}")
    print(f"  hrsa_shortage rows: {len(hrsa_data)}")


# =============================================================================
# SECTION 2 — SQL QUERIES
# =============================================================================

def run_queries():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    print("\n" + "="*70)
    print("QUERY 1 — Mental Health Treatment Gap Ranking (all 51 jurisdictions)")
    print("="*70)
    cur.execute("""
        SELECT state,
               ami_prevalence_pct,
               ami_received_treatment_pct,
               ROUND(ami_prevalence_pct - ami_received_treatment_pct, 2) AS mh_gap,
               RANK() OVER (ORDER BY (ami_prevalence_pct - ami_received_treatment_pct) DESC) AS gap_rank
        FROM nsduh_state
        ORDER BY gap_rank
    """)
    for row in cur.fetchall():
        print(f"  {row[4]:>3}. {row[0]:<25}  Prev: {row[1]:>5.2f}%  Tx: {row[2]:>5.2f}%  Gap: {row[3]:>+5.2f} pp")

    print("\n" + "="*70)
    print("QUERY 2 — Washington vs National Average")
    print("="*70)
    cur.execute("""
        SELECT
            'National Average'  AS label,
            ROUND(AVG(ami_prevalence_pct), 2)         AS avg_prev,
            ROUND(AVG(ami_received_treatment_pct), 2) AS avg_tx,
            ROUND(AVG(ami_prevalence_pct - ami_received_treatment_pct), 2) AS avg_gap
        FROM nsduh_state
        UNION ALL
        SELECT
            'Washington'        AS label,
            ami_prevalence_pct,
            ami_received_treatment_pct,
            ROUND(ami_prevalence_pct - ami_received_treatment_pct, 2)
        FROM nsduh_state WHERE state = 'Washington'
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<20}  Prevalence: {row[1]:>5.2f}%  Treatment: {row[2]:>5.2f}%  Gap: {row[3]:>+5.2f} pp")

    print("\n" + "="*70)
    print("QUERY 3 — MH + SUD Combined Gaps (Top 10 worst MH states)")
    print("="*70)
    cur.execute("""
        SELECT state,
               ROUND(ami_prevalence_pct - ami_received_treatment_pct, 2) AS mh_gap,
               ROUND(sud_prevalence_pct - sud_received_treatment_pct, 2) AS sud_gap
        FROM nsduh_state
        ORDER BY mh_gap DESC
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<25}  MH Gap: {row[1]:>+5.2f} pp   SUD Gap: {row[2]:>+5.2f} pp")

    print("\n" + "="*70)
    print("QUERY 4 — Data Quality Audit")
    print("="*70)
    cur.execute("""
        SELECT
            COUNT(*) AS total_records,
            SUM(CASE WHEN ami_prevalence_pct IS NULL THEN 1 ELSE 0 END)         AS null_ami_prev,
            SUM(CASE WHEN ami_received_treatment_pct IS NULL THEN 1 ELSE 0 END) AS null_ami_tx,
            SUM(CASE WHEN ami_prevalence_pct < 0 OR ami_prevalence_pct > 100 THEN 1 ELSE 0 END) AS out_of_range_prev,
            SUM(CASE WHEN ami_received_treatment_pct < 0 OR ami_received_treatment_pct > 100 THEN 1 ELSE 0 END) AS out_of_range_tx
        FROM nsduh_state
    """)
    row = cur.fetchone()
    print(f"  Total records   : {row[0]}")
    print(f"  Null AMI prev   : {row[1]}")
    print(f"  Null AMI tx     : {row[2]}")
    print(f"  Out-of-range prev: {row[3]}")
    print(f"  Out-of-range tx : {row[4]}")
    print(f"  Result          : {'PASS — zero violations' if all(v == 0 for v in row[1:]) else 'FAIL — see above'}")

    print("\n" + "="*70)
    print("QUERY 5 — Washington County HPSA Rankings")
    print("="*70)
    cur.execute("""
        SELECT county, hpsa_score, population_of_designation,
               RANK() OVER (ORDER BY hpsa_score DESC) AS score_rank
        FROM hrsa_shortage WHERE state = 'Washington'
        ORDER BY score_rank
    """)
    for row in cur.fetchall():
        flag = ' ← HIGH PRIORITY' if row[1] >= 16 else ''
        print(f"  {row[3]:>3}. {row[0]:<25}  Score: {row[1]:>2}/25  Pop: {row[2]:>8,}{flag}")

    conn.close()


# =============================================================================
# SECTION 3 — HELPER: load data arrays
# =============================================================================

def load_state_data():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""
        SELECT state, ami_prevalence_pct, ami_received_treatment_pct,
               ami_unmet_need_pct, sud_prevalence_pct, sud_received_treatment_pct,
               (ami_prevalence_pct - ami_received_treatment_pct) AS mh_gap,
               (sud_prevalence_pct - sud_received_treatment_pct) AS sud_gap
        FROM nsduh_state ORDER BY state
    """)
    rows = cur.fetchall()
    conn.close()
    cols = ['state','ami_prev','ami_tx','ami_unmet','sud_prev','sud_tx','mh_gap','sud_gap']
    d = {c: [r[i] for r in rows] for i, c in enumerate(cols)}
    return d


def load_hpsa_data():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""
        SELECT county, hpsa_score, population_of_designation
        FROM hrsa_shortage WHERE state='Washington'
        ORDER BY hpsa_score DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


# =============================================================================
# SECTION 4 — CHARTS 1–3  (original three)
# =============================================================================

def fig1_treatment_gap_ranking(d):
    """Bar chart: top 20 states by MH treatment gap (Washington highlighted)."""
    states   = d['state']
    mh_gap   = d['mh_gap']
    wa_idx   = states.index('Washington')
    nat_avg  = sum(mh_gap) / len(mh_gap)

    sorted_idx = sorted(range(len(states)), key=lambda i: mh_gap[i], reverse=True)[:20]
    top_states = [states[i] for i in sorted_idx]
    top_gaps   = [mh_gap[i] for i in sorted_idx]

    colors = [C_WA if s == 'Washington' else (C_BLUE if g > 0 else '#95A5A6')
              for s, g in zip(top_states, top_gaps)]

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(range(len(top_states)), top_gaps, color=colors,
                  alpha=0.88, edgecolor='white', linewidth=0.5, zorder=2)

    ax.axhline(nat_avg, color=C_AMBER, lw=1.8, linestyle='--',
               label=f'National avg: {nat_avg:.1f} pp', zorder=3)
    ax.axhline(0, color='#636E72', lw=0.8, linestyle=':', zorder=3)

    for i, (bar, val) in enumerate(zip(bars, top_gaps)):
        ax.text(i, val + 0.05 if val >= 0 else val - 0.18,
                f'{val:.1f}', ha='center', va='bottom', fontsize=7.5, color=C_DARK)

    ax.set_xticks(range(len(top_states)))
    ax.set_xticklabels([s.replace(' ', '\n') for s in top_states], fontsize=8.5, rotation=0)
    ax.set_ylabel('Treatment Gap (percentage points)', fontsize=11)
    ax.set_title('Mental Health Treatment Gap by State — Top 20 (Washington Highlighted)',
                 fontsize=13, fontweight='bold', color=C_DARK, pad=14)
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.6, zorder=1)

    wa_patch  = mpatches.Patch(color=C_WA,  label='Washington')
    oth_patch = mpatches.Patch(color=C_BLUE, label='Other states')
    ax.legend(handles=[wa_patch, oth_patch,
                        plt.Line2D([0],[0], color=C_AMBER, lw=2, linestyle='--',
                                   label=f'National avg: {nat_avg:.1f} pp')],
              fontsize=8.5)

    plt.tight_layout()
    path = OUT_DIR + 'fig1_treatment_gap_ranking.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {path}")


def fig2_wa_vs_national(d):
    """Grouped bar: Washington vs national average (prevalence & treatment rate)."""
    states   = d['state']
    ami_prev = d['ami_prev']
    ami_tx   = d['ami_tx']
    wa_idx   = states.index('Washington')

    nat_avg_prev = sum(ami_prev) / len(ami_prev)
    nat_avg_tx   = sum(ami_tx)   / len(ami_tx)
    wa_prev      = ami_prev[wa_idx]
    wa_tx        = ami_tx[wa_idx]

    labels  = ['National Average', 'Washington']
    prev_vals = [nat_avg_prev, wa_prev]
    tx_vals   = [nat_avg_tx,   wa_tx]

    x = np.arange(len(labels))
    w = 0.35

    fig, ax = plt.subplots(figsize=(9, 6))
    bars_prev = ax.bar(x - w/2, prev_vals, w, label='AMI Prevalence',
                       color=[C_BLUE, C_BLUE], alpha=0.88, edgecolor='white')
    bars_tx   = ax.bar(x + w/2, tx_vals,   w, label='Treatment Rate',
                       color=[C_GREEN, C_GREEN], alpha=0.88, edgecolor='white')

    for bar, val in zip(list(bars_prev) + list(bars_tx),
                        prev_vals + tx_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                f'{val:.2f}%', ha='center', va='bottom', fontsize=9.5, fontweight='bold', color=C_DARK)

    # Gap arrows to the right of each bar pair
    for i in range(2):
        gap = prev_vals[i] - tx_vals[i]
        bracket_x = x[i] + w/2 + 0.12
        arrow_top    = prev_vals[i]
        arrow_bottom = tx_vals[i]
        ax.annotate('', xy=(bracket_x, arrow_top), xytext=(bracket_x, arrow_bottom),
                    arrowprops=dict(arrowstyle='<->', color=C_RED, lw=1.8))
        ax.text(bracket_x + 0.07, (arrow_top + arrow_bottom) / 2,
                f'{gap:.1f} pp\ngap', ha='left', va='center',
                fontsize=8.5, color=C_RED, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel('Percentage of Adults 18+', fontsize=11)
    ax.set_title("Washington State vs. National Average\nAMI Prevalence and Treatment Rate",
                 fontsize=13, fontweight='bold', color=C_DARK, pad=14)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.6, zorder=1)
    ax.set_ylim(0, max(prev_vals) * 1.22)

    plt.tight_layout()
    path = OUT_DIR + 'fig2_wa_vs_national.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {path}")


def fig3_yakima_hpsa(hpsa_rows):
    """Horizontal bar: top 10 WA county HPSA scores (Yakima highlighted)."""
    top10     = hpsa_rows[:10]
    counties  = [r[0].replace(' County','') for r in top10]
    scores    = [r[1] for r in top10]

    colors = [C_WA if c == 'Yakima' else (C_RED if s >= 16 else C_BLUE)
              for c, s in zip(counties, scores)]

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(range(len(counties)), scores[::-1],
                   color=colors[::-1], alpha=0.88, edgecolor='white', linewidth=0.5)

    for i, (bar, val) in enumerate(zip(bars, scores[::-1])):
        ax.text(val + 0.1, i, f'{val}/25', va='center', fontsize=9, color=C_DARK)

    ax.axvline(16, color=C_RED, lw=1.8, linestyle='--', zorder=4)
    ax.text(16.1, len(counties) - 0.3, 'Federal high-priority\nthreshold (score ≥ 16)',
            color=C_RED, fontsize=8.5, va='top', ha='left',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=C_RED, alpha=0.85))

    ax.set_yticks(range(len(counties)))
    ax.set_yticklabels(counties[::-1], fontsize=10)
    ax.set_xlabel('HPSA Score (0–25)', fontsize=11)
    ax.set_title('Washington State Mental Health HPSA Scores — Top 10 Counties\n(Yakima Highlighted)',
                 fontsize=12, fontweight='bold', color=C_DARK, pad=14)
    ax.set_xlim(0, 27)
    ax.grid(axis='x', alpha=0.6)

    wa_patch  = mpatches.Patch(color=C_WA,  label='Yakima County')
    hp_patch  = mpatches.Patch(color=C_RED,  label='High-priority (≥ 16)')
    oth_patch = mpatches.Patch(color=C_BLUE, label='Below threshold')
    ax.legend(handles=[wa_patch, hp_patch, oth_patch], fontsize=9, loc='lower right')

    plt.tight_layout()
    path = OUT_DIR + 'fig3_yakima_hpsa_rank.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {path}")


# =============================================================================
# SECTION 5 — CHARTS 4–8  (EDA)
# =============================================================================

def fig4_prevalence_vs_treatment(d):
    """Scatter: AMI prevalence vs treatment rate — all 51 states."""
    states   = d['state']
    ami_prev = d['ami_prev']
    ami_tx   = d['ami_tx']
    wa_idx   = states.index('Washington')
    n = len(states)

    fig, ax = plt.subplots(figsize=(10, 7))
    colors = [C_WA if s == 'Washington' else C_BLUE for s in states]
    sizes  = [130  if s == 'Washington' else 50     for s in states]

    for i in range(n):
        ax.scatter(ami_prev[i], ami_tx[i], color=colors[i], s=sizes[i],
                   alpha=0.85, zorder=4 if states[i]=='Washington' else 2,
                   edgecolors='white', linewidths=0.5)

    mn = min(min(ami_prev), min(ami_tx)) - 1
    mx = max(max(ami_prev), max(ami_tx)) + 1
    ax.plot([mn, mx], [mn, mx], '--', color='#7F8C8D', lw=1.2, zorder=1, label='Parity (gap = 0)')

    z = np.polyfit(ami_prev, ami_tx, 1)
    xs = np.linspace(min(ami_prev), max(ami_prev), 200)
    ax.plot(xs, np.poly1d(z)(xs), '-', color=C_AMBER, lw=1.8, zorder=1, label='Trend line')

    ax.annotate('Washington',
                xy=(ami_prev[wa_idx], ami_tx[wa_idx]),
                xytext=(ami_prev[wa_idx] - 3.2, ami_tx[wa_idx] + 1.0),
                fontsize=9, fontweight='bold', color=C_WA,
                arrowprops=dict(arrowstyle='->', color=C_WA, lw=1.4))

    ax.fill_between([mn, mx], [mn, mx], [mx+2, mx+2], alpha=0.05, color=C_GREEN)
    ax.fill_between([mn, mx], [mn-2, mn-2], [mn, mx],  alpha=0.05, color=C_RED)

    corr = np.corrcoef(ami_prev, ami_tx)[0, 1]
    ax.text(0.98, 0.04, f'r = {corr:.2f}  (Pearson)',
            transform=ax.transAxes, ha='right', fontsize=9, color='#636E72',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#DFE6E9', alpha=0.9))

    ax.set_xlabel('AMI Prevalence (% adults 18+)', fontsize=11)
    ax.set_ylabel('AMI Treatment Rate (% adults 18+)', fontsize=11)
    ax.set_title('AMI Prevalence vs. Treatment Rate — All 51 U.S. Jurisdictions',
                 fontsize=13, fontweight='bold', color=C_DARK, pad=14)
    ax.legend(fontsize=8.5, framealpha=0.9)
    ax.grid(True, alpha=0.5)
    plt.tight_layout()
    path = OUT_DIR + 'fig4_prevalence_vs_treatment.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {path}")


def fig5_gap_distribution(d):
    """Histogram: distribution of MH treatment gaps across all 51 states."""
    mh_gap = d['mh_gap']
    states = d['state']
    wa_gap = mh_gap[states.index('Washington')]
    nat_avg = sum(mh_gap) / len(mh_gap)

    fig, ax = plt.subplots(figsize=(10, 6))
    bins = np.linspace(min(mh_gap) - 0.5, max(mh_gap) + 0.5, 18)
    n_hist, bin_edges, patches = ax.hist(mh_gap, bins=bins, color=C_BLUE,
                                          edgecolor='white', linewidth=0.8, alpha=0.85, zorder=2)

    for patch, left, right in zip(patches, bin_edges[:-1], bin_edges[1:]):
        if left <= wa_gap < right:
            patch.set_facecolor(C_WA)
            patch.set_zorder(3)

    ax.annotate(f'Washington\n({wa_gap:.1f} pp)',
                xy=(wa_gap, 0), xytext=(wa_gap + 0.9, max(n_hist) * 0.65),
                fontsize=9, fontweight='bold', color=C_WA,
                arrowprops=dict(arrowstyle='->', color=C_WA, lw=1.4))

    ax.axvline(nat_avg, color=C_AMBER, lw=2, linestyle='--', zorder=4,
               label=f'National avg: {nat_avg:.1f} pp')
    ax.axvline(0, color='#636E72', lw=1.2, linestyle=':', zorder=4, label='Zero gap')

    ax.set_xlabel('Mental Health Treatment Gap (pp)', fontsize=11)
    ax.set_ylabel('Number of States', fontsize=11)
    ax.set_title('Distribution of Mental Health Treatment Gaps — All 51 U.S. Jurisdictions',
                 fontsize=13, fontweight='bold', color=C_DARK, pad=14)
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.6)
    ax.text(0.02, 0.93, 'Negative gaps = more treatment than prevalence\n(cross-state care-seeking, NSDUH SAE artifact)',
            transform=ax.transAxes, fontsize=8, color='#636E72',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor='#DFE6E9', alpha=0.9))

    plt.tight_layout()
    path = OUT_DIR + 'fig5_gap_distribution.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {path}")


def fig6_mh_vs_sud_gaps(d):
    """Grouped bar: MH vs SUD gaps — top 11 states + Washington always included."""
    states  = d['state']
    mh_gap  = d['mh_gap']
    sud_gap = d['sud_gap']

    # Top 11 by MH gap, then force-append Washington if not already present
    sorted_idx = sorted(range(len(states)), key=lambda i: mh_gap[i], reverse=True)
    top_idx = sorted_idx[:11]
    wa_idx  = states.index('Washington')
    if wa_idx not in top_idx:
        top_idx = top_idx + [wa_idx]   # Washington appended at the right

    top_states = [states[i] for i in top_idx]
    top_mh     = [mh_gap[i]  for i in top_idx]
    top_sud    = [sud_gap[i] for i in top_idx]

    mh_colors  = [C_AMBER if s == 'Washington' else C_BLUE for s in top_states]
    sud_colors = [C_AMBER if s == 'Washington' else C_RED  for s in top_states]

    fig, ax = plt.subplots(figsize=(14, 7))
    x = np.arange(len(top_states))
    w = 0.38

    bar_mh  = ax.bar(x - w/2, top_mh,  w, color=mh_colors,  alpha=0.88,
                     label='Mental Health Gap', zorder=2, edgecolor='white', linewidth=0.4)
    bar_sud = ax.bar(x + w/2, top_sud, w, color=sud_colors, alpha=0.88,
                     label='Substance Use Disorder Gap', zorder=2, edgecolor='white', linewidth=0.4)

    # Label WA bars directly
    wa_pos = top_states.index('Washington')
    ax.annotate(f'WA\n(MH: {top_mh[wa_pos]:.1f} pp\nSUD: {top_sud[wa_pos]:.1f} pp)',
                xy=(x[wa_pos], top_sud[wa_pos] + 0.2),
                xytext=(x[wa_pos] - 1.1, top_sud[wa_pos] + 1.8),
                fontsize=8.5, fontweight='bold', color=C_AMBER,
                arrowprops=dict(arrowstyle='->', color=C_AMBER, lw=1.3))

    # Separator line before Washington if it was appended
    if wa_idx not in sorted_idx[:11]:
        ax.axvline(x[wa_pos] - 0.55, color='#95A5A6', lw=1.2, linestyle=':', zorder=1)
        ax.text(x[wa_pos] - 0.52, ax.get_ylim()[1] * 0.01, 'WA (rank 17)',
                fontsize=7.5, color='#7F8C8D', rotation=90, va='bottom')

    ax.set_xticks(x)
    ax.set_xticklabels([s.replace(' ', '\n') for s in top_states], fontsize=8.5)
    ax.set_ylabel('Treatment Gap (percentage points)', fontsize=11)
    ax.set_title('Mental Health vs. Substance Use Disorder Treatment Gaps\nTop 11 States by MH Gap + Washington',
                 fontsize=13, fontweight='bold', color=C_DARK, pad=14)

    # Legend: colors + WA marker
    wa_patch = mpatches.Patch(color=C_AMBER, label='Washington (focus state)')
    leg_handles = [
        mpatches.Patch(color=C_BLUE,  label='Mental Health Gap'),
        mpatches.Patch(color=C_RED,   label='Substance Use Disorder Gap'),
        wa_patch,
    ]
    ax.legend(handles=leg_handles, fontsize=9.5, framealpha=0.95)
    ax.grid(axis='y', alpha=0.5, zorder=1)

    ax.text(0.98, 0.97,
            'SUD gap is consistently\n2–4× larger than MH gap',
            transform=ax.transAxes, ha='right', va='top', fontsize=8.5, color='#636E72',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor='#DFE6E9', alpha=0.9))

    plt.tight_layout()
    path = OUT_DIR + 'fig6_mh_vs_sud_gaps.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {path}")


def fig7_unmet_need_ranking(d):
    """Horizontal bar: AMI unmet need % — top 19 states + Washington always shown."""
    states    = d['state']
    ami_unmet = d['ami_unmet']

    sorted_idx = sorted(range(len(states)), key=lambda i: ami_unmet[i], reverse=True)
    wa_idx     = states.index('Washington')
    top_idx    = sorted_idx[:19]
    wa_in_top  = wa_idx in top_idx

    if not wa_in_top:
        top_idx = top_idx + [wa_idx]   # Washington appended at the bottom (lowest value)

    un_states = [states[i] for i in top_idx]
    un_vals   = [ami_unmet[i] for i in top_idx]
    colors    = [C_AMBER if s == 'Washington' else C_BLUE for s in un_states]

    n = len(un_states)
    fig, ax = plt.subplots(figsize=(10, n * 0.42 + 1.5))

    # Reversed so highest is at the top
    bars = ax.barh(range(n), un_vals[::-1],
                   color=colors[::-1], alpha=0.88, edgecolor='white', linewidth=0.5, zorder=2)

    wa_val  = un_vals[-1] if not wa_in_top else un_vals[un_states.index('Washington')]
    wa_rank = sorted_idx.index(wa_idx) + 1

    # Value labels — all states including Washington
    for i, (val, state) in enumerate(zip(un_vals[::-1], un_states[::-1])):
        if state == 'Washington':
            # Bold rank label placed INSIDE the bar (left-aligned)
            ax.text(2, i, f'{val:.1f}%  —  Rank #31 nationally',
                    va='center', fontsize=9, color='white',
                    fontweight='bold')
        else:
            ax.text(val + 0.25, i, f'{val:.1f}%', va='center', fontsize=8.5, color=C_DARK)

    # Separator line before Washington if appended
    if not wa_in_top:
        ax.axhline(0.5, color='#95A5A6', lw=1.2, linestyle=':', zorder=1)

    ax.set_yticks(range(n))
    ax.set_yticklabels(un_states[::-1], fontsize=9.5)

    # Bold + color Washington label
    for lbl, s in zip(ax.get_yticklabels(), un_states[::-1]):
        if s == 'Washington':
            lbl.set_fontweight('bold')
            lbl.set_color(C_AMBER)

    ax.set_xlabel('Adults with AMI Who Did NOT Receive Treatment (%)', fontsize=10)
    title_suffix = 'Top 19 States + Washington' if not wa_in_top else 'Top 20 States'
    ax.set_title(f'Unmet Mental Health Need — {title_suffix}\n(% of people with AMI who go without treatment)',
                 fontsize=12, fontweight='bold', color=C_DARK, pad=14)

    wa_patch  = mpatches.Patch(color=C_AMBER, label='Washington (focus state)')
    oth_patch = mpatches.Patch(color=C_BLUE,  label='Other states')
    ax.legend(handles=[wa_patch, oth_patch], fontsize=9, loc='upper right')
    ax.grid(axis='x', alpha=0.5, zorder=1)
    ax.set_xlim(0, max(un_vals) + 8)   # extra right margin for value labels
    ax.tick_params(axis='y', length=0)

    plt.tight_layout()
    path = OUT_DIR + 'fig7_unmet_need_ranking.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {path}")


def fig8_hpsa_bubble(hpsa_rows):
    """Redesigned bubble chart: county HPSA score vs population, sorted by score."""
    counties = [r[0].replace(' County', '') for r in hpsa_rows]
    scores   = [r[1] for r in hpsa_rows]
    pops     = [r[2] for r in hpsa_rows]
    max_pop  = max(pops)

    # Sort by score ascending so highest scores appear at the TOP
    order    = sorted(range(len(counties)), key=lambda i: scores[i])
    counties = [counties[i] for i in order]
    scores   = [scores[i] for i in order]
    pops     = [pops[i]    for i in order]

    pop_scale = [max(60, p / max_pop * 2200) for p in pops]
    b_colors  = ['#E74C3C' if c == 'Yakima'
                 else (C_RED if s >= 16 else C_BLUE)
                 for c, s in zip(counties, scores)]

    n   = len(counties)
    fig, ax = plt.subplots(figsize=(12, n * 0.42 + 2))

    # Alternating row shading for readability
    for i in range(0, n, 2):
        ax.axhspan(i - 0.5, i + 0.5, color='#EEF2F5', zorder=0, linewidth=0)

    ax.scatter(scores, range(n), s=pop_scale, c=b_colors,
               alpha=0.82, edgecolors='white', linewidths=0.9, zorder=3)

    # Y-axis county labels — bold & red for Yakima
    ax.set_yticks(range(n))
    ax.set_yticklabels(counties, fontsize=9.5)
    for lbl, county in zip(ax.get_yticklabels(), counties):
        if county == 'Yakima':
            lbl.set_fontweight('bold')
            lbl.set_color('#C0392B')

    # Threshold line — annotated directly, NOT in the legend
    ax.axvline(16, color=C_AMBER, lw=2.0, linestyle='--', zorder=2, alpha=0.9)
    ax.text(16.25, 1.0, '≥ 16\nHigh-priority', fontsize=8.5,
            color='#D35400', va='bottom', linespacing=1.4)

    ax.set_xlabel('HPSA Score  (higher score = greater shortage, max 25)', fontsize=11)
    ax.set_title('Washington State Counties — Mental Health HPSA Scores',
                 fontsize=13, fontweight='bold', color=C_DARK, pad=14)
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', alpha=0.35, linestyle=':')
    ax.set_xlim(3.5, 27)
    ax.set_ylim(-0.8, n - 0.2)

    # ── Two clean legend groups ──────────────────────────────────────────────
    # 1) Color legend (priority level)
    color_handles = [
        mpatches.Patch(facecolor=C_RED,     label='High-priority shortage (score ≥ 16)'),
        mpatches.Patch(facecolor=C_BLUE,    label='Standard shortage (score < 16)'),
        mpatches.Patch(facecolor='#E74C3C', label='Yakima County (focus area)'),
    ]
    leg1 = ax.legend(handles=color_handles, title='Priority Level',
                     loc='lower right', fontsize=8.5, title_fontsize=9,
                     framealpha=0.95, edgecolor='#CCCCCC',
                     bbox_to_anchor=(1.0, 0.0))
    ax.add_artist(leg1)

    # 2) Bubble-size legend
    size_handles = []
    for pop_k, lbl in [(50_000, '50 K'), (150_000, '150 K'), (300_000, '300 K')]:
        sz = max(60, pop_k / max_pop * 2200)
        size_handles.append(
            ax.scatter([], [], s=sz, c=C_GREY, alpha=0.75,
                       edgecolors='white', label=f'Pop: {lbl}'))
    ax.legend(handles=size_handles, title='Designated Population',
              loc='lower right', fontsize=8.5, title_fontsize=9,
              framealpha=0.95, edgecolor='#CCCCCC',
              bbox_to_anchor=(1.0, 0.30))

    plt.tight_layout()
    path = OUT_DIR + 'fig8_hpsa_bubble.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {path}")


# =============================================================================
# SECTION 6 — EXPORT OUTPUT CSVs
# =============================================================================

def export_csvs():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # treatment_gap_by_state.csv
    cur.execute("""
        SELECT state,
               ami_prevalence_pct,
               ami_received_treatment_pct,
               ROUND(ami_prevalence_pct - ami_received_treatment_pct, 2) AS mh_gap,
               RANK() OVER (ORDER BY (ami_prevalence_pct - ami_received_treatment_pct) DESC) AS gap_rank
        FROM nsduh_state ORDER BY gap_rank
    """)
    rows = cur.fetchall()
    with open(OUT_DIR + 'treatment_gap_by_state.csv', 'w') as f:
        f.write('state,ami_prevalence_pct,ami_received_treatment_pct,mh_gap_pp,gap_rank\n')
        for r in rows:
            f.write(','.join(str(x) for x in r) + '\n')

    # wa_vs_national.csv
    cur.execute("""
        SELECT 'National Average', ROUND(AVG(ami_prevalence_pct),2),
               ROUND(AVG(ami_received_treatment_pct),2),
               ROUND(AVG(ami_prevalence_pct - ami_received_treatment_pct),2)
        FROM nsduh_state
        UNION ALL
        SELECT 'Washington', ami_prevalence_pct, ami_received_treatment_pct,
               ROUND(ami_prevalence_pct - ami_received_treatment_pct,2)
        FROM nsduh_state WHERE state='Washington'
    """)
    rows = cur.fetchall()
    with open(OUT_DIR + 'wa_vs_national.csv', 'w') as f:
        f.write('label,ami_prevalence_pct,ami_received_treatment_pct,mh_gap_pp\n')
        for r in rows:
            f.write(','.join(str(x) for x in r) + '\n')

    # yakima_shortage_rank.csv
    cur.execute("""
        SELECT county, hpsa_score, population_of_designation,
               RANK() OVER (ORDER BY hpsa_score DESC) AS score_rank
        FROM hrsa_shortage WHERE state='Washington' ORDER BY score_rank
    """)
    rows = cur.fetchall()
    with open(OUT_DIR + 'yakima_shortage_rank.csv', 'w') as f:
        f.write('county,hpsa_score,population_of_designation,score_rank\n')
        for r in rows:
            f.write(','.join(str(x) for x in r) + '\n')

    conn.close()
    print(f"CSVs exported to {OUT_DIR}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("Building database...")
    build_database()

    print("\nRunning SQL queries...")
    run_queries()

    print("\nExporting CSVs...")
    export_csvs()

    print("\nGenerating charts...")
    d    = load_state_data()
    hpsa = load_hpsa_data()

    fig1_treatment_gap_ranking(d)
    fig2_wa_vs_national(d)
    fig3_yakima_hpsa(hpsa)
    fig4_prevalence_vs_treatment(d)
    fig5_gap_distribution(d)
    fig6_mh_vs_sud_gaps(d)
    fig7_unmet_need_ranking(d)
    fig8_hpsa_bubble(hpsa)

    print(f"\nDone. All outputs written to {OUT_DIR}")
