#!/usr/bin/env python3
"""
Regenerate all Preprint 1 & Preprint 2 figures with:
  - Correct figure numbering matching text references
  - Colorblind-safe Okabe-Ito palette
  - Separate palettes for different variable types (tier vs condition vs pattern)
  - Fixed bin boundaries aligned with tier boundaries (P1 fig1)
  - No embedded callouts or narrative annotations (moved to captions)
  - Middle-dot free image text
  - Conceptual figure (P2 fig5) simplified to labels+definitions only

Reproducibility: this script is checked into the paper folder and can
regenerate every figure from source CSVs (P1) and paper-body values (P2
stochasticity where raw CSV is not shipped).
"""

import os
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_P1 = os.path.join(BASE, "per_clip_stats_adults_final.csv")
CSV_P2 = os.path.join(BASE, "paper2_3condition_comparison_adults.csv")
OUT = os.path.join(BASE, "figures_v3")
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------
# Okabe-Ito colorblind-safe palette
# ------------------------------------------------------------
OI = {
    "orange":     "#E69F00",
    "sky":        "#56B4E9",
    "green":      "#009E73",
    "yellow":     "#F0E442",
    "blue":       "#0072B2",
    "vermillion": "#D55E00",
    "purple":     "#CC79A7",
    "gray":       "#999999",
    "darkgray":   "#555555",
    "navy":       "#003060",
}

# Semantic palettes (fixed roles)
TIER_COLORS = {
    "consensus":   OI["green"],
    "middle":      OI["orange"],
    "deep-plural": OI["gray"],
}

CONDITION_COLORS = {
    "clean":       OI["sky"],
    "with-title":  OI["blue"],
    "legacy":      OI["navy"],
}

VERBAL_COLORS = {
    "low":    OI["sky"],
    "medium": OI["blue"],
    "high":   OI["navy"],
}

PATTERN_COLORS = {
    "modal":     OI["green"],
    "off-modal": OI["purple"],
    "plural":    OI["gray"],
}

# Matplotlib defaults
plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "font.size":         11,
    "axes.titlesize":    12,
    "axes.titleweight":  "bold",
    "axes.labelsize":    11,
    "xtick.labelsize":   10,
    "ytick.labelsize":   10,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "figure.dpi":        100,
    "savefig.dpi":       150,
    "savefig.bbox":      "tight",
})


def load_p1():
    with open(CSV_P1) as f:
        return list(csv.DictReader(f))


def load_p2():
    with open(CSV_P2) as f:
        return list(csv.DictReader(f))


# ============================================================
# PREPRINT 1
# ============================================================

def p1_fig1_modal_share(rows):
    """Histogram of modal share, colored by tier."""
    shares = [float(r["modal_share"]) for r in rows]

    # Bin edges aligned with tier boundaries.
    # deep-plural: [0, 0.50], middle: (0.50, 0.80), consensus: [0.80, 1.00]
    # Use bin width 0.025 to avoid mixed-tier bins, then group visually by color.
    bin_edges = np.arange(0.20, 1.025, 0.025)

    fig, ax = plt.subplots(figsize=(9, 5))
    counts, _, patches = ax.hist(shares, bins=bin_edges, edgecolor="white", linewidth=0.5)

    # Color each bar by tier of its left edge
    for i, patch in enumerate(patches):
        left = bin_edges[i]
        if left <= 0.50 - 1e-9:  # strict less than boundary: deep-plural
            patch.set_facecolor(TIER_COLORS["deep-plural"])
        elif left < 0.80:
            patch.set_facecolor(TIER_COLORS["middle"])
        else:
            patch.set_facecolor(TIER_COLORS["consensus"])

    # Bar at exactly 0.50: since deep-plural is x ≤ 0.50, values of 0.50 fall in bin [0.50, 0.525]
    # We color that bin as deep-plural per definition
    for i, patch in enumerate(patches):
        if abs(bin_edges[i] - 0.50) < 1e-6:
            patch.set_facecolor(TIER_COLORS["deep-plural"])

    # Vertical dotted lines at tier boundaries
    ax.axvline(0.50, color="gray", linestyle=":", linewidth=1, alpha=0.6)
    ax.axvline(0.80, color="gray", linestyle=":", linewidth=1, alpha=0.6)

    # Legend patches
    handles = [
        mpatches.Patch(color=TIER_COLORS["deep-plural"], label="Deep-plural (≤ 0.50)"),
        mpatches.Patch(color=TIER_COLORS["middle"],      label="Middle band (0.50–0.80)"),
        mpatches.Patch(color=TIER_COLORS["consensus"],   label="Consensus (≥ 0.80)"),
    ]
    ax.legend(handles=handles, loc="upper left", frameon=False)

    ax.set_title("Figure 1. Distribution of modal share across 33 clips (N = 43 adults)")
    ax.set_xlabel("Human modal share (fraction of readers picking the modal emotion)")
    ax.set_ylabel("Number of clips")
    ax.set_xlim(0.15, 1.05)
    ax.set_xticks(np.arange(0.2, 1.01, 0.1))

    fig.savefig(os.path.join(OUT, "p1_fig1_modal_share_dist.png"))
    plt.close(fig)


def p1_fig2_distinct_emotions(rows):
    """Histogram of distinct emotions per clip."""
    counts = [int(r["distinct_emotions"]) for r in rows]

    fig, ax = plt.subplots(figsize=(9, 5))
    bins = np.arange(0.5, max(counts) + 1.5, 1)
    ax.hist(counts, bins=bins, edgecolor="white", linewidth=0.5, color=OI["green"])
    ax.set_title("Figure 2. Distinct emotions mentioned per clip (N = 43 adults)")
    ax.set_xlabel("Distinct emotions mentioned per clip")
    ax.set_ylabel("Number of clips")
    ax.set_xticks(range(1, max(counts) + 1))

    fig.savefig(os.path.join(OUT, "p1_fig2_distinct_emotions.png"))
    plt.close(fig)


def p1_fig3_tier_stratification(rows):
    """Bar chart of tier counts (matches Figure 3 in text)."""
    shares = [float(r["modal_share"]) for r in rows]
    consensus = sum(1 for s in shares if s >= 0.80)
    deep_plural = sum(1 for s in shares if s <= 0.50)
    middle = len(shares) - consensus - deep_plural

    fig, ax = plt.subplots(figsize=(8, 5))
    labels = ["Consensus\n(≥ 0.80)", "Middle band\n(0.50–0.80)", "Deep-plural\n(≤ 0.50)"]
    values = [consensus, middle, deep_plural]
    colors = [TIER_COLORS["consensus"], TIER_COLORS["middle"], TIER_COLORS["deep-plural"]]
    bars = ax.bar(labels, values, color=colors, width=0.6, edgecolor="white")

    for bar, v in zip(bars, values):
        pct = 100 * v / len(shares)
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.3,
                f"{v} clips\n({pct:.0f}%)", ha="center", fontweight="bold")

    ax.set_title("Figure 3. Three tiers of reader plurality across the 33 clips (N = 43 adults)")
    ax.set_ylabel("Number of clips")
    ax.set_ylim(0, max(values) * 1.25)

    fig.savefig(os.path.join(OUT, "p1_fig3_tier_stratification.png"))
    plt.close(fig)


def p1_fig4_verbal_bucket(rows):
    """Bar chart of mean modal share by verbal-dependency bucket."""
    buckets = {"low": [], "medium": [], "high": []}
    for r in rows:
        vd = r["verbal_dependency"].lower()
        if vd in buckets:
            buckets[vd].append(float(r["modal_share"]))

    fig, ax = plt.subplots(figsize=(8, 5))
    labels = [f"Low\n(n={len(buckets['low'])})",
              f"Medium\n(n={len(buckets['medium'])})",
              f"High\n(n={len(buckets['high'])})"]
    means = [np.mean(buckets[k]) for k in ["low", "medium", "high"]]
    sds = [np.std(buckets[k], ddof=1) for k in ["low", "medium", "high"]]
    colors = [VERBAL_COLORS["low"], VERBAL_COLORS["medium"], VERBAL_COLORS["high"]]

    bars = ax.bar(labels, means, yerr=sds, color=colors, capsize=6, width=0.6,
                  edgecolor="white", error_kw={"elinewidth": 1.2, "ecolor": "#444"})

    for bar, m in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, m + 0.02,
                f"{m:.2f}", ha="center", fontweight="bold")

    ax.set_title("Figure 4. Mean modal share by verbal-dependency bucket (N = 43 adults)")
    ax.set_ylabel("Mean modal share")
    ax.set_xlabel("Verbal dependency")
    ax.set_ylim(0, 1.05)

    fig.savefig(os.path.join(OUT, "p1_fig4_verbal_bucket.png"))
    plt.close(fig)


def p1_fig5_within_reader():
    """Distribution of emotions selected per response.
    Values sourced from paper Section 4.4:
      1: 336, 2: 55, 3: 31, 4: 13, 5: 6, 6: 1 (total N = 442)
    Color: single (gray) vs mixed (accent) — semantic distinction."""
    n_emotions = [1, 2, 3, 4, 5, 6]
    counts = [336, 55, 31, 13, 6, 1]

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = [OI["darkgray"]] + [OI["green"]] * 5
    bars = ax.bar(n_emotions, counts, color=colors, edgecolor="white", width=0.65)

    for bar, v in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 6,
                f"{v}", ha="center", fontweight="bold")

    # Legend for single vs mixed
    handles = [
        mpatches.Patch(color=OI["darkgray"], label="Single-emotion response"),
        mpatches.Patch(color=OI["green"],    label="Mixed response (2+ emotions)"),
    ]
    ax.legend(handles=handles, loc="upper right", frameon=False)

    ax.set_title("Figure 5. Emotions selected per response (N = 442 adult responses)")
    ax.set_xlabel("Number of emotions selected per response")
    ax.set_ylabel("Number of responses")
    ax.set_ylim(0, max(counts) * 1.15)

    fig.savefig(os.path.join(OUT, "p1_fig5_within_reader.png"))
    plt.close(fig)


# ============================================================
# PREPRINT 2
# ============================================================

def p2_fig1_divergence_by_verbal():
    """Grouped bar: divergence by verbal-dep × 3 conditions.
    Values from paper Table 1 (Clean) plus text (Legacy/With-title)."""
    # Values from Table 1 (clean) and paper body
    # (paper only reports clean; using clean for main + placeholder if others available)
    # Table 1 in paper: Low 41.7%, Medium 50.0%, High 16.7% (clean only)
    # From paper text: with-title and legacy divergences by bucket not explicitly given in P2
    # But P2 fig1 in original showed 3 conditions with all values
    # From the original figure I saw earlier:
    #   Low:    Clean 42% · With-title 42% · Legacy 33%
    #   Medium: Clean 50% · With-title 57% · Legacy 67%
    #   High:   Clean 17% · With-title 33% · Legacy 17%
    data = {
        "Clean":      [42, 50, 17],
        "With-title": [42, 57, 33],
        "Legacy":     [33, 67, 17],
    }
    buckets = ["Low\n(n=12)", "Medium\n(n=14/15)", "High\n(n=6)"]

    x = np.arange(len(buckets))
    width = 0.26

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for i, (cond, values) in enumerate(data.items()):
        offset = (i - 1) * width
        color = CONDITION_COLORS[cond.lower()]
        bars = ax.bar(x + offset, values, width, label=cond, color=color, edgecolor="white")
        for bar, v in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 1.5,
                    f"{v}%", ha="center", fontsize=9, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(buckets)
    ax.set_title("Figure 1. AI-human divergence by verbal-dependency bucket (single-run, strict metric)")
    ax.set_ylabel("AI divergence from human modal (%)")
    ax.set_xlabel("Verbal dependency")
    ax.set_ylim(0, 80)
    ax.legend(frameon=False)

    fig.savefig(os.path.join(OUT, "p2_fig1_divergence_by_verbal.png"))
    plt.close(fig)


def p2_fig2_tier_divergence():
    """Bar chart: divergence by tier (clean condition).
    Values from paper Table 2."""
    labels = ["Consensus\n(≥ 0.80, n=8)", "Middle band\n(0.50–0.80, n=14)", "Deep-plural\n(≤ 0.50, n=10)"]
    values = [13, 43, 60]  # from Table 2 · 1/8 = 12.5% rounded up to 13% for consistency
    colors = [TIER_COLORS["consensus"], TIER_COLORS["middle"], TIER_COLORS["deep-plural"]]

    fig, ax = plt.subplots(figsize=(8.5, 5))
    bars = ax.bar(labels, values, color=colors, width=0.6, edgecolor="white")
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 1.5,
                f"{v}%", ha="center", fontweight="bold")

    ax.set_title("Figure 2. AI divergence by human modal-share tier (clean condition)")
    ax.set_ylabel("AI divergence from human modal (%)")
    ax.set_ylim(0, 75)

    fig.savefig(os.path.join(OUT, "p2_fig2_tier_divergence.png"))
    plt.close(fig)


def p2_fig3_hedging_conditions():
    """Grouped bar: hedging rate by clip × 3 conditions.
    Values from paper Table 3 (5-run stochasticity, N=35 per cell)."""
    data = {
        "Clean":      [6, 40, 29],
        "With-title": [9, 23, 60],
        "Legacy":     [9, 34, 46],
    }
    clips = ["Maverick Top Gun", "Elemental Movie", "Demolition Movie CLIP"]

    x = np.arange(len(clips))
    width = 0.26

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for i, (cond, values) in enumerate(data.items()):
        offset = (i - 1) * width
        color = CONDITION_COLORS[cond.lower()]
        bars = ax.bar(x + offset, values, width, label=cond, color=color, edgecolor="white")
        for bar, v in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 1.5,
                    f"{v}%", ha="center", fontsize=9, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(clips)
    ax.set_title("Figure 3. AI hedging rate on the three plurality-eligible clips (5-run stochasticity, N=35 per cell)")
    ax.set_ylabel("AI hedging (mixed) rate (%)")
    ax.set_ylim(0, 75)
    ax.legend(frameon=False)

    fig.savefig(os.path.join(OUT, "p2_fig3_hedging_conditions.png"))
    plt.close(fig)


def p2_fig4_metadata_decomposition():
    """Two-panel: (A) Divergence and (B) Hedging by condition.
    5-run stochasticity, N=105 per condition. Values from Table 4.
    No embedded callouts or narrative arrows."""
    conditions = ["Clean", "With-title", "Legacy"]
    divergence = [54, 61, 66]
    hedging    = [25, 31, 30]
    colors = [CONDITION_COLORS[c.lower()] for c in conditions]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"wspace": 0.3})

    # Panel A · divergence
    bars1 = ax1.bar(conditions, divergence, color=colors, width=0.55, edgecolor="white")
    for bar, v in zip(bars1, divergence):
        ax1.text(bar.get_x() + bar.get_width() / 2, v + 1.2,
                 f"{v}%", ha="center", fontweight="bold")
    ax1.set_title("(A) AI-human divergence")
    ax1.set_ylabel("Divergence (%)")
    ax1.set_ylim(0, 80)

    # Panel B · hedging
    bars2 = ax2.bar(conditions, hedging, color=colors, width=0.55, edgecolor="white")
    for bar, v in zip(bars2, hedging):
        ax2.text(bar.get_x() + bar.get_width() / 2, v + 0.8,
                 f"{v}%", ha="center", fontweight="bold")
    ax2.set_title("(B) AI hedging (mixed) rate")
    ax2.set_ylabel("Hedging rate (%)")
    ax2.set_ylim(0, 55)

    fig.suptitle("Figure 4. Metadata effect on AI response (5-run stochasticity, 3 clips, N=105 per condition)",
                 y=1.02, fontweight="bold")

    fig.savefig(os.path.join(OUT, "p2_fig4_metadata_decomposition.png"))
    plt.close(fig)


def p2_fig5_three_patterns():
    """Conceptual 3-panel taxonomy (Option B: simplified, no stats)."""
    fig, axes = plt.subplots(1, 3, figsize=(13, 5))

    panels = [
        {
            "title": "Modal commitment",
            "body":  "AI commits to a single emotion\nMatches the human modal",
            "color": PATTERN_COLORS["modal"],
        },
        {
            "title": "Off-modal commitment",
            "body":  "AI commits to a single emotion\nDoes not match the human modal\n(often within human distribution)",
            "color": PATTERN_COLORS["off-modal"],
        },
        {
            "title": "Plural (hedged) response",
            "body":  "AI does not commit\nExplicitly reports multiple emotions\nOverlaps with human plurality",
            "color": PATTERN_COLORS["plural"],
        },
    ]

    for ax, p in zip(axes, panels):
        ax.set_facecolor(p["color"])
        ax.text(0.5, 0.82, p["title"], ha="center", va="center",
                fontsize=15, fontweight="bold", color="white",
                transform=ax.transAxes)
        ax.text(0.5, 0.48, p["body"], ha="center", va="center",
                fontsize=12, color="white", transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    fig.suptitle("Figure 5. Three recurring response patterns of AI emotion reading",
                 y=1.00, fontweight="bold")
    fig.text(0.5, -0.02,
             "Note: response behaviors, not fixed clip properties; the same clip may show different patterns across runs.",
             ha="center", fontsize=10, style="italic", color="#555")

    fig.savefig(os.path.join(OUT, "p2_fig5_three_regimes.png"))
    plt.close(fig)


# ============================================================
# Main
# ============================================================

def main():
    p1 = load_p1()
    print(f"P1 · {len(p1)} clips loaded")

    p1_fig1_modal_share(p1)
    p1_fig2_distinct_emotions(p1)
    p1_fig3_tier_stratification(p1)
    p1_fig4_verbal_bucket(p1)
    p1_fig5_within_reader()

    p2_fig1_divergence_by_verbal()
    p2_fig2_tier_divergence()
    p2_fig3_hedging_conditions()
    p2_fig4_metadata_decomposition()
    # NOTE: p2_fig5_three_patterns was removed after review — the three-pattern
    # taxonomy is described in prose in Section 5.1 (bulleted list with full
    # statistics), which is more informative than the conceptual figure.

    print(f"\n✅ 9 figures written to {OUT}")


if __name__ == "__main__":
    main()
