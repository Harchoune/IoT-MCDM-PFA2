# =============================================================================
# FILE: main.py  (UPDATED — v2)
# ROLE: Orchestrator — Entry Point of the AHP-TOPSIS Algorithm
# CHANGES FROM v1:
#   + Imports export_results_to_csv and run_sensitivity_analysis from utils.py
#   + After ranking display, asks user if they want CSV export
#   + Asks user if they want to run the sensitivity analysis
#   All core AHP and TOPSIS logic is UNCHANGED.
# =============================================================================

import numpy as np
import sys

# --- Internal Modules ---
from data.networks import (
    ALTERNATIVES,
    CRITERIA,
    DECISION_MATRIX,
    SCENARIOS
)
from ahp     import compute_ahp_weights, get_manual_matrix, print_ahp_results
from topsis  import run_topsis, print_topsis_results
from chart   import plot_ranking

# ── NEW IMPORTS ───────────────────────────────────────────────────────────────
from utils import export_results_to_csv, run_sensitivity_analysis
# ─────────────────────────────────────────────────────────────────────────────


# =============================================================================
# FUNCTION: print_welcome
# =============================================================================
def print_welcome() -> None:
    """Displays the welcome banner and project info."""
    print("\n" + "=" * 60)
    print("       AHP-TOPSIS IoT NETWORK SELECTION TOOL")
    print("       Final Year Project — MCDM Algorithm")
    print("=" * 60)
    print("  Networks  :", ", ".join(ALTERNATIVES))
    print("  Criteria  :", len(CRITERIA))
    for c in CRITERIA:
        direction = "↑ maximize" if c["objective"] == "max" else "↓ minimize"
        print(f"    • {c['name']:<22} [{c['unit']:<10}] {direction}")
    print("=" * 60)


# =============================================================================
# FUNCTION: select_scenario
# =============================================================================
def select_scenario() -> tuple:
    """
    Prompts the user to select a predefined IoT scenario or enter a custom one.

    Returns:
        tuple: (scenario dict, scenario key string)
    """
    print("\n  AVAILABLE SCENARIOS:")
    print("-" * 60)
    for key, scenario in SCENARIOS.items():
        print(f"  [{key}] {scenario['name']}")
        print(f"       {scenario['description'].splitlines()[0]}")

    print("-" * 60)

    while True:
        choice = input("\n  Select a scenario number: ").strip()
        if choice in SCENARIOS:
            selected = SCENARIOS[choice]
            print(f"\n  ✅ Scenario selected: {selected['name']}")
            print(f"  {selected['description']}")
            return selected, choice
        else:
            print(f"  ⚠ Invalid choice. Please enter one of: {list(SCENARIOS.keys())}")


# =============================================================================
# FUNCTION: get_ahp_matrix
# =============================================================================
def get_ahp_matrix(scenario: dict, choice: str) -> np.ndarray:
    """
    Returns the pairwise comparison matrix for the selected scenario.
    For the custom scenario (choice "4"), prompts the user for manual input.

    Args:
        scenario (dict): The selected scenario dict.
        choice   (str) : The scenario key.

    Returns:
        np.ndarray: The 5x5 pairwise comparison matrix.
    """
    if choice == "4":
        print("\n  You selected the Custom Scenario.")
        print("  You will now enter pairwise comparisons for each pair of criteria.")
        return get_manual_matrix(CRITERIA)
    else:
        print("\n  Using predefined pairwise comparison matrix for this scenario.")
        _print_comparison_matrix(scenario["matrix"])
        return scenario["matrix"]


# =============================================================================
# FUNCTION: ask_verbose
# =============================================================================
def ask_verbose() -> bool:
    """Asks the user whether to display intermediate computation matrices."""
    print("\n" + "-" * 60)
    ans = input("  Show intermediate matrices (normalized, weighted)? [y/N]: ").strip().lower()
    return ans == "y"


# =============================================================================
# FUNCTION: ask_chart
# =============================================================================
def ask_chart() -> bool:
    """Asks the user whether to generate and display the ranking bar chart."""
    ans = input("  Generate a ranking bar chart? [Y/n]: ").strip().lower()
    return ans != "n"


# =============================================================================
# ── NEW FUNCTION ──────────────────────────────────────────────────────────────
# FUNCTION: ask_csv_export
# =============================================================================
def ask_csv_export() -> bool:
    """Asks the user whether to export results to a CSV file."""
    ans = input("  Export results to CSV? [Y/n]: ").strip().lower()
    return ans != "n"


# =============================================================================
# ── NEW FUNCTION ──────────────────────────────────────────────────────────────
# FUNCTION: ask_sensitivity
# =============================================================================
def ask_sensitivity() -> bool:
    """Asks the user whether to run the sensitivity analysis."""
    ans = input("  Run Sensitivity Analysis (academic Hanine method)? [Y/n]: ").strip().lower()
    return ans != "n"


# =============================================================================
# ── NEW FUNCTION ──────────────────────────────────────────────────────────────
# FUNCTION: select_sensitivity_criterion
# =============================================================================
def select_sensitivity_criterion(weights: np.ndarray) -> int:
    """
    Lets the user choose which criterion to vary in the sensitivity analysis,
    or defaults automatically to the highest-weight criterion.

    Args:
        weights (np.ndarray): AHP weight vector.

    Returns:
        int: Index of the criterion to vary.
    """
    auto_idx  = int(np.argmax(weights))
    auto_name = CRITERIA[auto_idx]["name"]

    print("\n" + "-" * 60)
    print("  SENSITIVITY ANALYSIS — Criterion Selection")
    print("-" * 60)
    print("  Which criterion should be varied?")
    print()

    for i, c in enumerate(CRITERIA):
        marker = "★" if i == auto_idx else " "
        print(f"  [{i}] {marker} {c['name']:<22}  weight = {weights[i]:.4f}")

    print(f"\n  (★ = highest weight, auto-selected if you press Enter)")
    print("-" * 60)

    while True:
        raw = input(f"  Enter criterion index [0-{len(CRITERIA)-1}] or Enter for auto: ").strip()
        if raw == "":
            print(f"  ✅ Auto-selected: [{auto_idx}] {auto_name}")
            return auto_idx
        try:
            idx = int(raw)
            if 0 <= idx < len(CRITERIA):
                print(f"  ✅ Selected: [{idx}] {CRITERIA[idx]['name']}")
                return idx
            else:
                print(f"  ⚠ Please enter a number between 0 and {len(CRITERIA)-1}.")
        except ValueError:
            print("  ⚠ Invalid input. Enter a number or press Enter.")


# =============================================================================
# FUNCTION: _print_comparison_matrix
# =============================================================================
def _print_comparison_matrix(matrix: np.ndarray) -> None:
    """Prints the pairwise comparison matrix in a readable format."""
    n = len(CRITERIA)
    short_names = [c["name"][:8] for c in CRITERIA]

    print("\n  Pairwise Comparison Matrix:")
    print("-" * 60)

    header = f"  {'':>10}"
    for name in short_names:
        header += f" {name:>10}"
    print(header)
    print("-" * 60)

    for i in range(n):
        row = f"  {short_names[i]:>10}"
        for j in range(n):
            val = matrix[i][j]
            if val < 1 and val > 0:
                formatted = f"1/{int(round(1/val))}"
            else:
                formatted = f"{int(val)}"
            row += f" {formatted:>10}"
        print(row)

    print("-" * 60)


# =============================================================================
# MAIN FUNCTION
# =============================================================================
def main() -> None:
    """
    Main execution flow of the AHP-TOPSIS IoT Network Selection Algorithm.
    """

    # ── Step 0: Welcome Screen ────────────────────────────────────────────────
    print_welcome()

    # ── Step 1: Scenario Selection ────────────────────────────────────────────
    scenario, choice = select_scenario()

    # ── Step 2: Get AHP Pairwise Comparison Matrix ───────────────────────────
    ahp_matrix = get_ahp_matrix(scenario, choice)

    # ── Step 3: Run AHP — Compute Criteria Weights ───────────────────────────
    print("\n  ⏳ Running AHP...")

    try:
        ahp_result = compute_ahp_weights(ahp_matrix)
    except ValueError as e:
        print(f"\n  ❌ AHP Error: {e}")
        sys.exit(1)

    print_ahp_results(ahp_result, CRITERIA)

    if not ahp_result["consistent"]:
        print("\n  ⚠️  Warning: Proceeding with inconsistent weights.")
        print("     Consider revising your pairwise comparisons.")
        ans = input("  Continue anyway? [y/N]: ").strip().lower()
        if ans != "y":
            print("  Exiting. Please revise your pairwise comparison matrix.")
            sys.exit(0)

    weights = ahp_result["weights"]

    # ── Step 4: Run TOPSIS — Rank IoT Networks ───────────────────────────────
    print("\n  ⏳ Running TOPSIS...")

    try:
        topsis_result = run_topsis(
            decision_matrix=DECISION_MATRIX,
            weights=weights,
            criteria=CRITERIA,
            alternatives=ALTERNATIVES
        )
    except ValueError as e:
        print(f"\n  ❌ TOPSIS Error: {e}")
        sys.exit(1)

    # ── Step 5: Display Results ───────────────────────────────────────────────
    verbose = ask_verbose()
    print_topsis_results(topsis_result, CRITERIA, ALTERNATIVES, verbose=verbose)

    # ── Step 6: Optional Ranking Bar Chart ───────────────────────────────────
    if ask_chart():
        try:
            plot_ranking(
                topsis_result["ranking"],
                scenario_name=scenario["name"]
            )
        except Exception as e:
            print(f"\n  ⚠️  Chart generation failed: {e}")

    # ── Step 7: NEW — Optional CSV Export ─────────────────────────────────────
    if ask_csv_export():
        try:
            export_results_to_csv(
                ranking       = topsis_result["ranking"],
                scenario_name = scenario["name"],
                ahp_result    = ahp_result,
                criteria      = CRITERIA,
                output_dir    = "."          # Saves in the project root folder
            )
        except Exception as e:
            print(f"\n  ⚠️  CSV export failed: {e}")

    # ── Step 8: NEW — Optional Sensitivity Analysis ───────────────────────────
    if ask_sensitivity():
        varied_idx = select_sensitivity_criterion(weights)

        try:
            run_sensitivity_analysis(
                baseline_weights       = weights,
                decision_matrix        = DECISION_MATRIX,
                criteria               = CRITERIA,
                alternatives           = ALTERNATIVES,
                scenario_name          = scenario["name"],
                varied_criterion_index = varied_idx,
                weight_range           = (0.05, 0.95),   # Sweep from 5% to 95%
                steps                  = 19,              # 19 evenly spaced steps
                output_dir             = "."
            )
        except Exception as e:
            print(f"\n  ⚠️  Sensitivity analysis failed: {e}")

    # ── Done ──────────────────────────────────────────────────────────────────
    print("\n  ✅ Analysis complete. Thank you for using AHP-TOPSIS IoT Selector.")
    print("=" * 60 + "\n")


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    main()
