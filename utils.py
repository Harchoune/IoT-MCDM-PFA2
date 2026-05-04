# =============================================================================
# FILE: utils.py
# ROLE: Extensions — CSV Export + Academic Sensitivity Analysis
# DESCRIPTION:
#   This module adds two independent features to the AHP-TOPSIS pipeline.
#   It does NOT modify any core AHP or TOPSIS logic.
#
#   Feature 1 — export_results_to_csv()
#       Exports the final TOPSIS ranking to a structured CSV file.
#
#   Feature 2 — run_sensitivity_analysis()
#       Implements the academic "Hanine" sensitivity analysis methodology:
#       Systematically varies the weight of the most critical criterion,
#       proportionally redistributes the remaining weights, reruns TOPSIS
#       at each step, and tracks ranking stability across all variations.
#       Exports a full sensitivity report to CSV and generates a chart.
# =============================================================================

import csv
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from datetime import datetime

# Internal module — TOPSIS engine (no modification)
from topsis import run_topsis


# =============================================================================
# FEATURE 1: CSV EXPORT
# =============================================================================

def export_results_to_csv(
    ranking: list,
    scenario_name: str,
    ahp_result: dict,
    criteria: list,
    output_dir: str = "."
) -> str:
    """
    Exports the final AHP-TOPSIS results to a well-structured CSV file.

    The CSV contains two sections:
      Section A — Run metadata (scenario, date, consistency ratio).
      Section B — AHP criteria weights.
      Section C — Final TOPSIS ranking table.

    Args:
        ranking       (list) : Output ranking list from run_topsis().
        scenario_name (str)  : Name of the selected IoT scenario.
        ahp_result    (dict) : Output from compute_ahp_weights().
        criteria      (list) : List of criterion dicts from networks.py.
        output_dir    (str)  : Directory where the CSV will be saved.
                               Defaults to current directory.

    Returns:
        str: Absolute path of the generated CSV file.
    """

    # --- Build filename with timestamp to avoid overwriting ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = scenario_name.replace(" ", "_").replace("/", "-")[:30]
    filename  = f"results_{safe_name}_{timestamp}.csv"
    filepath  = os.path.join(output_dir, filename)

    with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # ── Section A: Metadata ──────────────────────────────────────────────
        writer.writerow(["# AHP-TOPSIS IoT Network Selection — Results Export"])
        writer.writerow(["Scenario",        scenario_name])
        writer.writerow(["Date",            datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["Lambda Max",      f"{ahp_result['lambda_max']:.4f}"])
        writer.writerow(["Consistency Index (CI)", f"{ahp_result['CI']:.4f}"])
        writer.writerow(["Consistency Ratio (CR)", f"{ahp_result['CR']:.4f}"])
        writer.writerow(["Matrix Consistent",
                         "YES" if ahp_result["consistent"] else "NO — Review comparisons"])
        writer.writerow([])  # Blank separator line

        # ── Section B: AHP Criteria Weights ─────────────────────────────────
        writer.writerow(["# SECTION B — AHP Criteria Weights"])
        writer.writerow(["Criterion", "Unit", "Objective", "Weight"])
        weights = ahp_result["weights"]
        for i, criterion in enumerate(criteria):
            writer.writerow([
                criterion["name"],
                criterion["unit"],
                criterion["objective"].upper(),
                f"{weights[i]:.4f}"
            ])
        writer.writerow([])  # Blank separator line

        # ── Section C: TOPSIS Final Ranking ─────────────────────────────────
        writer.writerow(["# SECTION C — TOPSIS Final Ranking"])
        writer.writerow([
            "Rank",
            "Network",
            "Closeness Score (Ci)",
            "Distance to Ideal Best (D+)",
            "Distance to Ideal Worst (D-)"
        ])
        for entry in ranking:
            writer.writerow([
                entry["rank"],
                entry["network"],
                f"{entry['closeness']:.4f}",
                f"{entry['distance_best']:.4f}",
                f"{entry['distance_worst']:.4f}"
            ])

    print(f"\n  📄 Results exported to: {os.path.abspath(filepath)}")
    return filepath


# =============================================================================
# FEATURE 2: SENSITIVITY ANALYSIS (Academic "Hanine" Methodology)
# =============================================================================

def run_sensitivity_analysis(
    baseline_weights: np.ndarray,
    decision_matrix: np.ndarray,
    criteria: list,
    alternatives: list,
    scenario_name: str,
    varied_criterion_index: int = None,
    weight_range: tuple = (0.05, 0.95),
    steps: int = 19,
    output_dir: str = "."
) -> dict:
    """
    Runs a full academic sensitivity analysis on the AHP-TOPSIS model.

    Methodology (Hanine et al., MCDM research):
      1. Identify the most critical criterion (highest AHP weight) or use
         a user-specified criterion index.
      2. Systematically vary its weight from weight_range[0] to weight_range[1].
      3. At each step, proportionally rescale ALL other criteria weights so
         the total always sums to exactly 1.0.
      4. Rerun TOPSIS with the new weight vector.
      5. Record the Rank-1 network and full Ci scores at each step.
      6. Identify the "stability threshold" — the weight value at which
         the top-ranked network changes for the first time.
      7. Export a full sensitivity report to CSV.
      8. Generate an academic-style sensitivity chart.

    Args:
        baseline_weights      (np.ndarray): Original AHP weight vector.
        decision_matrix       (np.ndarray): Raw performance data (n_alt x n_crit).
        criteria              (list)      : List of criterion dicts from networks.py.
        alternatives          (list)      : List of alternative name strings.
        scenario_name         (str)       : Name of the scenario (for labeling).
        varied_criterion_index (int|None) : Index of the criterion to vary.
                                            If None, the highest-weight criterion
                                            is selected automatically.
        weight_range          (tuple)     : (min_weight, max_weight) to sweep.
                                            Default: (0.05, 0.95).
        steps                 (int)       : Number of evenly spaced steps.
                                            Default: 19.
        output_dir            (str)       : Directory for output files.

    Returns:
        dict with keys:
            'varied_index'      : int   — index of the varied criterion
            'varied_name'       : str   — name of the varied criterion
            'weight_steps'      : list  — list of weight values tested
            'rankings_history'  : list  — list of ranking lists at each step
            'top1_history'      : list  — best network name at each step
            'ci_history'        : list  — full Ci array at each step
            'stable'            : bool  — True if top-1 never changed
            'threshold_weight'  : float|None — weight at first rank change
            'csv_path'          : str   — path to the exported CSV
            'chart_path'        : str   — path to the saved chart PNG
    """

    # ── Step 1: Select the criterion to vary ─────────────────────────────────
    if varied_criterion_index is None:
        varied_criterion_index = int(np.argmax(baseline_weights))

    varied_name   = criteria[varied_criterion_index]["name"]
    n_criteria    = len(criteria)
    baseline_top1 = None   # Will be set on first iteration

    print("\n" + "=" * 65)
    print("  SENSITIVITY ANALYSIS — Hanine Methodology")
    print("=" * 65)
    print(f"  Scenario          : {scenario_name}")
    print(f"  Varied Criterion  : [{varied_criterion_index}] {varied_name}")
    print(f"  Baseline Weight   : {baseline_weights[varied_criterion_index]:.4f}")
    print(f"  Weight Range      : {weight_range[0]:.2f} → {weight_range[1]:.2f}")
    print(f"  Steps             : {steps}")
    print("=" * 65)

    # ── Step 2: Generate weight sweep values ─────────────────────────────────
    weight_steps = np.linspace(weight_range[0], weight_range[1], steps)

    # ── Step 3: Initialize result containers ─────────────────────────────────
    rankings_history  = []   # Full ranking list at each step
    top1_history      = []   # Name of best network at each step
    ci_history        = []   # Full Ci array at each step
    weight_vectors    = []   # Full weight vector at each step

    stable            = True
    threshold_weight  = None

    # ── Step 4: Main sweep loop ───────────────────────────────────────────────
    for w_val in weight_steps:

        # Build the new weight vector
        new_weights = _redistribute_weights(
            baseline_weights, varied_criterion_index, w_val, n_criteria
        )

        # Rerun TOPSIS with the new weights
        result = run_topsis(
            decision_matrix=decision_matrix,
            weights=new_weights,
            criteria=criteria,
            alternatives=alternatives
        )

        ranking  = result["ranking"]
        top1     = ranking[0]["network"]
        ci_array = result["closeness"]

        rankings_history.append(ranking)
        top1_history.append(top1)
        ci_history.append(ci_array.copy())
        weight_vectors.append(new_weights.copy())

        # Set the baseline top-1 from the first iteration
        if baseline_top1 is None:
            baseline_top1 = top1

        # Detect first rank change
        if top1 != baseline_top1 and stable:
            stable           = False
            threshold_weight = w_val
            print(f"\n  ⚠️  RANK CHANGE DETECTED at weight = {w_val:.4f}")
            print(f"     Top-1 changed from [{baseline_top1}] → [{top1}]")

    # ── Step 5: Print console summary ────────────────────────────────────────
    _print_sensitivity_summary(
        weight_steps, top1_history, varied_name,
        stable, threshold_weight, baseline_top1
    )

    # ── Step 6: Export CSV ────────────────────────────────────────────────────
    csv_path = _export_sensitivity_csv(
        weight_steps       = weight_steps,
        top1_history       = top1_history,
        ci_history         = ci_history,
        weight_vectors     = weight_vectors,
        rankings_history   = rankings_history,
        criteria           = criteria,
        alternatives       = alternatives,
        varied_criterion_index = varied_criterion_index,
        varied_name        = varied_name,
        scenario_name      = scenario_name,
        stable             = stable,
        threshold_weight   = threshold_weight,
        output_dir         = output_dir
    )

    # ── Step 7: Generate chart ────────────────────────────────────────────────
    chart_path = _plot_sensitivity_chart(
        weight_steps           = weight_steps,
        ci_history             = ci_history,
        top1_history           = top1_history,
        alternatives           = alternatives,
        varied_name            = varied_name,
        scenario_name          = scenario_name,
        baseline_top1          = baseline_top1,
        threshold_weight       = threshold_weight,
        stable                 = stable,
        baseline_weight        = baseline_weights[varied_criterion_index],
        output_dir             = output_dir
    )

    return {
        "varied_index":     varied_criterion_index,
        "varied_name":      varied_name,
        "weight_steps":     weight_steps.tolist(),
        "rankings_history": rankings_history,
        "top1_history":     top1_history,
        "ci_history":       ci_history,
        "stable":           stable,
        "threshold_weight": threshold_weight,
        "csv_path":         csv_path,
        "chart_path":       chart_path
    }


# =============================================================================
# INTERNAL HELPER: _redistribute_weights
# =============================================================================
def _redistribute_weights(
    baseline: np.ndarray,
    varied_idx: int,
    new_value: float,
    n: int
) -> np.ndarray:
    """
    Sets the varied criterion's weight to new_value and proportionally
    rescales all other criteria weights so the total remains exactly 1.0.

    Formula:
        w_j_new = w_j_baseline * (1 - new_value) / sum(w_k_baseline for k ≠ varied)

    Args:
        baseline   (np.ndarray): Original weight vector.
        varied_idx (int)       : Index of the criterion being varied.
        new_value  (float)     : New weight to assign to the varied criterion.
        n          (int)       : Total number of criteria.

    Returns:
        np.ndarray: New weight vector summing to 1.0.
    """
    new_weights = np.zeros(n)
    new_weights[varied_idx] = new_value

    # Sum of all other baseline weights (used for proportional rescaling)
    other_sum = sum(baseline[j] for j in range(n) if j != varied_idx)

    if other_sum == 0:
        # Edge case: all other weights are 0 → distribute equally
        remaining = (1.0 - new_value) / (n - 1)
        for j in range(n):
            if j != varied_idx:
                new_weights[j] = remaining
    else:
        scale = (1.0 - new_value) / other_sum
        for j in range(n):
            if j != varied_idx:
                new_weights[j] = baseline[j] * scale

    return new_weights


# =============================================================================
# INTERNAL HELPER: _print_sensitivity_summary
# =============================================================================
def _print_sensitivity_summary(
    weight_steps: np.ndarray,
    top1_history: list,
    varied_name: str,
    stable: bool,
    threshold_weight: float,
    baseline_top1: str
) -> None:
    """Prints a concise console table of the sensitivity sweep results."""

    print("\n" + "-" * 65)
    print(f"  {'Weight of [' + varied_name + ']':<30} {'Best Network':<15} {'Status'}")
    print("-" * 65)

    prev_top1 = None
    for w, top1 in zip(weight_steps, top1_history):
        changed = (prev_top1 is not None and top1 != prev_top1)
        status  = "⚠️  CHANGED" if changed else ""
        marker  = "→" if top1 == baseline_top1 else "≠"
        print(f"  w = {w:.3f}  {marker}  {top1:<20} {status}")
        prev_top1 = top1

    print("-" * 65)
    if stable:
        print(f"\n  ✅ ROBUST MODEL: [{baseline_top1}] remains #1 across ALL weight variations.")
        print(f"     The model is stable — results do not depend on small weight changes.")
    else:
        print(f"\n  ⚠️  SENSITIVITY DETECTED:")
        print(f"     The top-ranked network changes at weight = {threshold_weight:.4f}.")
        print(f"     Below this threshold, [{baseline_top1}] is best.")
        print(f"     Review your scenario weights for robustness.")
    print("=" * 65)


# =============================================================================
# INTERNAL HELPER: _export_sensitivity_csv
# =============================================================================
def _export_sensitivity_csv(
    weight_steps, top1_history, ci_history, weight_vectors,
    rankings_history, criteria, alternatives, varied_criterion_index,
    varied_name, scenario_name, stable, threshold_weight, output_dir
) -> str:
    """Exports the full sensitivity analysis data to a CSV file."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"sensitivity_{timestamp}.csv"
    filepath  = os.path.join(output_dir, filename)

    with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # Metadata
        writer.writerow(["# Sensitivity Analysis Report — AHP-TOPSIS"])
        writer.writerow(["Scenario",          scenario_name])
        writer.writerow(["Varied Criterion",  f"[{varied_criterion_index}] {varied_name}"])
        writer.writerow(["Model Robust",      "YES" if stable else "NO"])
        writer.writerow(["Threshold Weight",
                         f"{threshold_weight:.4f}" if threshold_weight else "N/A — No change"])
        writer.writerow([])

        # Full weight vectors at each step
        writer.writerow(["# Full Weight Vectors at Each Step"])
        header = [f"w({c['name']})" for c in criteria]
        writer.writerow(["Step", f"w({varied_name}) [VARIED]"] + header + ["Top-1 Network"])
        for i, (w_val, wvec, top1) in enumerate(
                zip(weight_steps, weight_vectors, top1_history), start=1):
            row = [i, f"{w_val:.4f}"] + [f"{v:.4f}" for v in wvec] + [top1]
            writer.writerow(row)
        writer.writerow([])

        # Closeness scores at each step
        writer.writerow(["# Closeness Scores (Ci) at Each Step"])
        writer.writerow(["Step", f"w({varied_name})"] + alternatives)
        for i, (w_val, ci_arr) in enumerate(zip(weight_steps, ci_history), start=1):
            row = [i, f"{w_val:.4f}"] + [f"{v:.4f}" for v in ci_arr]
            writer.writerow(row)

    print(f"  📄 Sensitivity report exported to: {os.path.abspath(filepath)}")
    return filepath


# =============================================================================
# INTERNAL HELPER: _plot_sensitivity_chart
# =============================================================================
def _plot_sensitivity_chart(
    weight_steps, ci_history, top1_history, alternatives,
    varied_name, scenario_name, baseline_top1, threshold_weight,
    stable, baseline_weight, output_dir
) -> str:
    """
    Generates the academic sensitivity analysis chart.
    Shows Ci score trajectories for all alternatives as the varied criterion
    weight is swept, with a vertical marker at the threshold if detected.
    """

    # Convert ci_history (list of arrays) to a 2D array: (steps, n_alt)
    ci_matrix = np.array(ci_history)   # Shape: (steps, n_alt)
    n_alt     = len(alternatives)

    # Color palette — distinct colors for each network
    colors = [
        "#E74C3C",   # Red       — LoRaWAN
        "#3498DB",   # Blue      — Sigfox
        "#2ECC71",   # Green     — NB-IoT
        "#F39C12",   # Orange    — LTE-M
        "#9B59B6",   # Purple    — Wi-Fi
        "#1ABC9C",   # Teal      — BLE
    ]
    line_styles = ["-", "--", "-.", ":", "-", "--"]

    fig, (ax1, ax2) = plt.subplots(
        2, 1,
        figsize=(12, 9),
        gridspec_kw={"height_ratios": [3, 1]},
        sharex=True
    )
    fig.patch.set_facecolor("#F8F9FA")

    # ── Upper panel: Ci trajectories ─────────────────────────────────────────
    ax1.set_facecolor("#F0F4F8")

    for i, alt in enumerate(alternatives):
        ci_values = ci_matrix[:, i]
        lw = 2.5 if alt == baseline_top1 else 1.5
        ax1.plot(
            weight_steps,
            ci_values,
            label=alt,
            color=colors[i % len(colors)],
            linestyle=line_styles[i % len(line_styles)],
            linewidth=lw,
            marker="o",
            markersize=4
        )

    # Baseline weight vertical line
    ax1.axvline(
        x=baseline_weight,
        color="#34495E",
        linestyle="--",
        linewidth=1.5,
        alpha=0.8,
        label=f"Baseline weight ({baseline_weight:.3f})"
    )

    # Threshold vertical line (if rank change detected)
    if not stable and threshold_weight is not None:
        ax1.axvline(
            x=threshold_weight,
            color="#E74C3C",
            linestyle="-",
            linewidth=2.0,
            alpha=0.9,
            label=f"⚠ Threshold ({threshold_weight:.3f})"
        )
        ax1.annotate(
            f"Rank changes\nhere (w={threshold_weight:.3f})",
            xy=(threshold_weight, ax1.get_ylim()[1] * 0.85),
            xytext=(threshold_weight + 0.05, ax1.get_ylim()[1] * 0.85),
            fontsize=8,
            color="#E74C3C",
            arrowprops=dict(arrowstyle="->", color="#E74C3C")
        )

    ax1.set_ylabel("Closeness Coefficient (Ci)", fontsize=11)
    ax1.set_title(
        f"Sensitivity Analysis — AHP-TOPSIS\n"
        f"Scenario: {scenario_name} | Varied: {varied_name}",
        fontsize=13,
        fontweight="bold",
        color="#1A1A2E"
    )
    ax1.legend(loc="upper right", fontsize=9, framealpha=0.9)
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # ── Lower panel: Top-1 network band ──────────────────────────────────────
    ax2.set_facecolor("#F0F4F8")

    # Assign a numeric index to each top-1 network for plotting
    unique_nets = list(dict.fromkeys(top1_history))   # Preserves order
    net_to_idx  = {net: i for i, net in enumerate(unique_nets)}
    top1_idx    = [net_to_idx[t] for t in top1_history]
    net_colors  = [colors[alternatives.index(t) % len(colors)] for t in top1_history]

    # Draw colored segments
    for i in range(len(weight_steps) - 1):
        ax2.fill_between(
            [weight_steps[i], weight_steps[i + 1]],
            0, 1,
            color=net_colors[i],
            alpha=0.6
        )
        ax2.text(
            (weight_steps[i] + weight_steps[i + 1]) / 2,
            0.5,
            top1_history[i],
            ha="center", va="center",
            fontsize=7, fontweight="bold",
            color="white",
            rotation=90 if len(weight_steps) > 12 else 0
        )

    if not stable and threshold_weight is not None:
        ax2.axvline(x=threshold_weight, color="#E74C3C", linewidth=2.0)

    ax2.set_xlabel(f"Weight of [{varied_name}]", fontsize=11)
    ax2.set_ylabel("Top-1\nNetwork", fontsize=9)
    ax2.set_yticks([])
    ax2.set_ylim(0, 1)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.grid(False)

    # Robustness label
    robustness_text = (
        "✅ ROBUST — Top network stable across all weight variations"
        if stable else
        f"⚠ SENSITIVE — Rank changes at w = {threshold_weight:.3f}"
    )
    robustness_color = "#27AE60" if stable else "#E74C3C"
    fig.text(
        0.5, 0.01,
        robustness_text,
        ha="center", fontsize=10,
        color=robustness_color,
        fontweight="bold"
    )

    plt.tight_layout(rect=[0, 0.04, 1, 1])

    # Save chart
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    chart_name = f"sensitivity_chart_{timestamp}.png"
    chart_path = os.path.join(output_dir, chart_name)
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    print(f"  📊 Sensitivity chart saved as: {os.path.abspath(chart_path)}")
    plt.show()

    return chart_path
