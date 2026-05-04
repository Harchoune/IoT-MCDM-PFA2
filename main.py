# =============================================================================
# FILE: main.py
# ROLE: Orchestrator — Entry Point of the AHP-TOPSIS Algorithm
# DESCRIPTION:
#   This is the main script that ties all modules together.
#   Execution flow:
#     1. Display welcome screen and available IoT networks/criteria.
#     2. Let the user select a predefined IoT scenario (or enter a custom one).
#     3. Call the AHP module → compute criteria weights.
#     4. Call the TOPSIS module → rank the IoT networks.
#     5. Display full results and generate a bar chart.
#
#   Run with: python3 main.py
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
def select_scenario() -> dict:
    """
    Prompts the user to select a predefined IoT scenario or enter a custom one.

    Returns:
        dict: The selected scenario dict from SCENARIOS, with 'matrix' populated.
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
        choice   (str) : The scenario key (e.g., "1", "2", "3", "4").

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
    """
    Asks the user whether to display intermediate computation matrices.

    Returns:
        bool: True if verbose output is desired.
    """
    print("\n" + "-" * 60)
    ans = input("  Show intermediate matrices (normalized, weighted)? [y/N]: ").strip().lower()
    return ans == "y"


# =============================================================================
# FUNCTION: ask_chart
# =============================================================================
def ask_chart() -> bool:
    """
    Asks the user whether to generate and display the ranking bar chart.

    Returns:
        bool: True if chart is desired.
    """
    ans = input("  Generate a ranking bar chart? [Y/n]: ").strip().lower()
    return ans != "n"


# =============================================================================
# FUNCTION: _print_comparison_matrix
# =============================================================================
def _print_comparison_matrix(matrix: np.ndarray) -> None:
    """
    Prints the pairwise comparison matrix in a readable format.

    Args:
        matrix (np.ndarray): The AHP pairwise comparison matrix.
    """
    n = len(CRITERIA)
    short_names = [c["name"][:8] for c in CRITERIA]

    print("\n  Pairwise Comparison Matrix:")
    print("-" * 60)

    # Header row
    header = f"  {'':>10}"
    for name in short_names:
        header += f" {name:>10}"
    print(header)
    print("-" * 60)

    # Data rows
    for i in range(n):
        row = f"  {short_names[i]:>10}"
        for j in range(n):
            val = matrix[i][j]
            # Format fractions nicely
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

    # --- Step 0: Welcome Screen ---
    print_welcome()

    # --- Step 1: Scenario Selection ---
    scenario, choice = select_scenario()

    # --- Step 2: Get AHP Pairwise Comparison Matrix ---
    ahp_matrix = get_ahp_matrix(scenario, choice)

    # --- Step 3: Run AHP — Compute Criteria Weights ---
    print("\n  ⏳ Running AHP...")

    try:
        ahp_result = compute_ahp_weights(ahp_matrix)
    except ValueError as e:
        print(f"\n  ❌ AHP Error: {e}")
        sys.exit(1)

    print_ahp_results(ahp_result, CRITERIA)

    # Warn user if matrix is inconsistent but continue anyway
    if not ahp_result["consistent"]:
        print("\n  ⚠️  Warning: Proceeding with inconsistent weights.")
        print("     Consider revising your pairwise comparisons.")
        ans = input("  Continue anyway? [y/N]: ").strip().lower()
        if ans != "y":
            print("  Exiting. Please revise your pairwise comparison matrix.")
            sys.exit(0)

    weights = ahp_result["weights"]

    # --- Step 4: Run TOPSIS — Rank IoT Networks ---
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

    # --- Step 5: Display Results ---
    verbose = ask_verbose()
    print_topsis_results(topsis_result, CRITERIA, ALTERNATIVES, verbose=verbose)

    # --- Step 6: Optional Bar Chart ---
    if ask_chart():
        try:
            plot_ranking(
                topsis_result["ranking"],
                scenario_name=scenario["name"]
            )
        except Exception as e:
            print(f"\n  ⚠️  Chart generation failed: {e}")

    print("\n  ✅ Analysis complete. Thank you for using AHP-TOPSIS IoT Selector.")
    print("=" * 60 + "\n")


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    main()
