# =============================================================================
# FILE: chart.py
# ROLE: Visualization — Ranking Bar Chart Generator
# DESCRIPTION:
#   Generates a clean, labeled bar chart of TOPSIS closeness scores.
#   The best-ranked network is highlighted in a distinct color.
#   Called optionally from main.py after TOPSIS computation.
# =============================================================================

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


# =============================================================================
# FUNCTION: plot_ranking
# =============================================================================
def plot_ranking(ranking: list, scenario_name: str = "") -> None:
    """
    Generates and displays a horizontal bar chart of TOPSIS closeness scores.

    The chart:
      - Shows all networks ranked from best (top) to worst (bottom).
      - Highlights the top-ranked network in gold.
      - Annotates each bar with its exact Ci score.
      - Adds a vertical reference line at Ci = 0.5 (neutral threshold).

    Args:
        ranking       (list): Output ranking list from run_topsis().
                              Each entry is a dict with keys:
                              'rank', 'network', 'closeness'.
        scenario_name (str) : Name of the selected IoT scenario (for title).
    """

    # --- Prepare data (display best at top → reverse for horizontal bar chart) ---
    networks   = [entry["network"]   for entry in ranking]
    scores     = [entry["closeness"] for entry in ranking]
    ranks      = [entry["rank"]      for entry in ranking]

    # Reverse so rank 1 is at the top
    networks_display = networks[::-1]
    scores_display   = scores[::-1]
    ranks_display    = ranks[::-1]

    n = len(networks)

    # --- Color scheme ---
    # Gold for rank 1, steel blue for the rest
    colors = []
    for rank in ranks_display:
        if rank == 1:
            colors.append("#FFD700")    # Gold — best network
        elif rank == 2:
            colors.append("#C0C0C0")    # Silver
        elif rank == 3:
            colors.append("#CD7F32")    # Bronze
        else:
            colors.append("#4A90D9")    # Steel blue — other networks

    # --- Create figure ---
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#F8F9FA")
    ax.set_facecolor("#F0F4F8")

    # --- Draw horizontal bars ---
    y_positions = np.arange(n)
    bars = ax.barh(
        y_positions,
        scores_display,
        color=colors,
        edgecolor="white",
        linewidth=1.2,
        height=0.6
    )

    # --- Annotate bars with Ci score ---
    for i, (bar, score) in enumerate(zip(bars, scores_display)):
        ax.text(
            score + 0.008,                   # Slightly right of bar end
            bar.get_y() + bar.get_height() / 2,
            f"{score:.4f}",
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
            color="#333333"
        )

    # --- Neutral threshold line at Ci = 0.5 ---
    ax.axvline(
        x=0.5,
        color="#E74C3C",
        linestyle="--",
        linewidth=1.2,
        alpha=0.7,
        label="Neutral threshold (Ci = 0.5)"
    )

    # --- Axis formatting ---
    ax.set_yticks(y_positions)
    ax.set_yticklabels(networks_display, fontsize=12, fontweight="bold")
    ax.set_xlabel("Closeness Coefficient (Ci)", fontsize=12, labelpad=10)
    ax.set_xlim(0, 1.1)
    ax.set_xticks(np.arange(0, 1.1, 0.1))
    ax.xaxis.grid(True, linestyle="--", alpha=0.5, color="white")
    ax.set_axisbelow(True)

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # --- Title ---
    title_main = "AHP-TOPSIS — IoT Network Ranking"
    title_sub  = f"Scenario: {scenario_name}" if scenario_name else ""
    ax.set_title(
        f"{title_main}\n{title_sub}",
        fontsize=14,
        fontweight="bold",
        pad=15,
        color="#1A1A2E"
    )

    # --- Legend ---
    gold_patch   = mpatches.Patch(color="#FFD700", label="🥇 Rank 1 — Best Network")
    silver_patch = mpatches.Patch(color="#C0C0C0", label="🥈 Rank 2")
    bronze_patch = mpatches.Patch(color="#CD7F32", label="🥉 Rank 3")
    blue_patch   = mpatches.Patch(color="#4A90D9", label="Other Networks")
    red_line     = mpatches.Patch(color="#E74C3C", label="Neutral threshold (Ci = 0.5)")

    ax.legend(
        handles=[gold_patch, silver_patch, bronze_patch, blue_patch, red_line],
        loc="lower right",
        fontsize=9,
        framealpha=0.9
    )

    # --- Footer annotation ---
    fig.text(
        0.99, 0.01,
        "Higher Ci score = Better network for this scenario",
        ha="right",
        va="bottom",
        fontsize=8,
        color="#888888",
        style="italic"
    )

    plt.tight_layout()
    plt.savefig("ranking_chart.png", dpi=150, bbox_inches="tight")
    print("\n  📊 Chart saved as 'ranking_chart.png'")
    plt.show()
