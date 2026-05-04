# =============================================================================
# FILE: topsis.py
# ROLE: TOPSIS Engine — Network Ranking Calculation
# DESCRIPTION:
#   Implements the Technique for Order of Preference by Similarity to
#   Ideal Solution (TOPSIS) method.
#   Takes the decision matrix and AHP weights as input and returns:
#     - A full ranking of all alternatives (IoT networks)
#     - Intermediate results for transparency and reporting
#   This module is generic and reusable for any alternatives/criteria.
# =============================================================================

import numpy as np


# =============================================================================
# FUNCTION: run_topsis
# =============================================================================
def run_topsis(decision_matrix: np.ndarray,
               weights: np.ndarray,
               criteria: list,
               alternatives: list) -> dict:
    """
    Executes the full TOPSIS algorithm.

    Steps:
      1. Vector normalization of the decision matrix.
      2. Apply AHP weights to get the weighted normalized matrix.
      3. Determine Ideal Best (A+) and Ideal Worst (A-) for each criterion,
         respecting the objective (min or max).
      4. Compute Euclidean distance of each alternative to A+ and A-.
      5. Compute the Closeness Coefficient (Ci) for each alternative.
      6. Rank alternatives by Ci in descending order (higher = better).

    Args:
        decision_matrix (np.ndarray): Raw performance data (n_alt x n_crit).
        weights         (np.ndarray): AHP weight vector (n_crit,). Sums to 1.
        criteria        (list)      : List of criterion dicts with 'objective' key.
        alternatives    (list)      : List of alternative name strings.

    Returns:
        dict with keys:
            'normalized_matrix'  : np.ndarray — after vector normalization
            'weighted_matrix'    : np.ndarray — after applying weights
            'ideal_best'         : np.ndarray — A+ vector
            'ideal_worst'        : np.ndarray — A- vector
            'distance_best'      : np.ndarray — D+ for each alternative
            'distance_worst'     : np.ndarray — D- for each alternative
            'closeness'          : np.ndarray — Ci scores
            'ranking'            : list of dicts — sorted results

    Raises:
        ValueError: If dimensions are inconsistent.
    """

    # --- Input Validation ---
    _validate_inputs(decision_matrix, weights, criteria, alternatives)

    n_alt, n_crit = decision_matrix.shape

    # -------------------------------------------------------------------------
    # STEP 1: Vector Normalization
    # Each element is divided by the Euclidean norm of its column.
    # Formula: r_ij = x_ij / sqrt(sum(x_kj^2))
    # -------------------------------------------------------------------------
    col_norms = np.sqrt((decision_matrix ** 2).sum(axis=0))  # Shape: (n_crit,)

    # Guard against division by zero (column of all zeros)
    col_norms[col_norms == 0] = 1.0

    normalized_matrix = decision_matrix / col_norms           # Shape: (n_alt, n_crit)

    # -------------------------------------------------------------------------
    # STEP 2: Weighted Normalized Matrix
    # Multiply each column by its corresponding AHP weight.
    # Formula: v_ij = w_j * r_ij
    # -------------------------------------------------------------------------
    weighted_matrix = normalized_matrix * weights             # Broadcasting (n_alt, n_crit)

    # -------------------------------------------------------------------------
    # STEP 3: Ideal Best (A+) and Ideal Worst (A-)
    # For each criterion:
    #   - If 'max' (benefit): A+ = max column value, A- = min column value
    #   - If 'min' (cost)   : A+ = min column value, A- = max column value
    # -------------------------------------------------------------------------
    ideal_best  = np.zeros(n_crit)
    ideal_worst = np.zeros(n_crit)

    for j, criterion in enumerate(criteria):
        col = weighted_matrix[:, j]
        if criterion["objective"] == "max":
            ideal_best[j]  = col.max()
            ideal_worst[j] = col.min()
        else:  # "min"
            ideal_best[j]  = col.min()
            ideal_worst[j] = col.max()

    # -------------------------------------------------------------------------
    # STEP 4: Euclidean Distances to A+ and A-
    # Formula:
    #   D+_i = sqrt( sum_j (v_ij - A+_j)^2 )
    #   D-_i = sqrt( sum_j (v_ij - A-_j)^2 )
    # -------------------------------------------------------------------------
    diff_best  = weighted_matrix - ideal_best   # Shape: (n_alt, n_crit)
    diff_worst = weighted_matrix - ideal_worst

    distance_best  = np.sqrt((diff_best  ** 2).sum(axis=1))  # Shape: (n_alt,)
    distance_worst = np.sqrt((diff_worst ** 2).sum(axis=1))

    # -------------------------------------------------------------------------
    # STEP 5: Closeness Coefficient (Ci)
    # Formula: Ci = D-_i / (D+_i + D-_i)
    # Range: [0, 1] — higher is better (closer to ideal best)
    # -------------------------------------------------------------------------
    denominator = distance_best + distance_worst

    # Guard against division by zero (degenerate case)
    denominator[denominator == 0] = 1e-10

    closeness = distance_worst / denominator                  # Shape: (n_alt,)

    # -------------------------------------------------------------------------
    # STEP 6: Ranking
    # Sort alternatives by Ci in descending order.
    # -------------------------------------------------------------------------
    sorted_indices = np.argsort(closeness)[::-1]             # Descending order

    ranking = []
    for rank, idx in enumerate(sorted_indices, start=1):
        ranking.append({
            "rank":          rank,
            "network":       alternatives[idx],
            "closeness":     closeness[idx],
            "distance_best": distance_best[idx],
            "distance_worst":distance_worst[idx],
            "index":         idx
        })

    return {
        "normalized_matrix":  normalized_matrix,
        "weighted_matrix":    weighted_matrix,
        "ideal_best":         ideal_best,
        "ideal_worst":        ideal_worst,
        "distance_best":      distance_best,
        "distance_worst":     distance_worst,
        "closeness":          closeness,
        "ranking":            ranking
    }


# =============================================================================
# FUNCTION: print_topsis_results
# =============================================================================
def print_topsis_results(topsis_result: dict,
                         criteria: list,
                         alternatives: list,
                         verbose: bool = False) -> None:
    """
    Prints a formatted summary of TOPSIS results.

    Args:
        topsis_result (dict) : Output from run_topsis().
        criteria      (list) : List of criterion dicts from networks.py.
        alternatives  (list) : List of alternative name strings.
        verbose       (bool) : If True, also prints intermediate matrices.
    """
    ranking        = topsis_result["ranking"]
    ideal_best     = topsis_result["ideal_best"]
    ideal_worst    = topsis_result["ideal_worst"]
    weighted_matrix = topsis_result["weighted_matrix"]

    # --- Optional: Verbose intermediate results ---
    if verbose:
        _print_matrix(
            topsis_result["normalized_matrix"],
            alternatives, criteria,
            title="NORMALIZED MATRIX"
        )
        _print_matrix(
            weighted_matrix,
            alternatives, criteria,
            title="WEIGHTED NORMALIZED MATRIX"
        )

        print("\n" + "=" * 60)
        print("  IDEAL BEST (A+) and IDEAL WORST (A-)")
        print("=" * 60)
        print(f"  {'Criterion':<22} {'A+':>10} {'A-':>10}")
        print("-" * 60)
        for j, criterion in enumerate(criteria):
            print(f"  {criterion['name']:<22} {ideal_best[j]:>10.6f} {ideal_worst[j]:>10.6f}")

    # --- Main Ranking Table ---
    print("\n" + "=" * 60)
    print("  TOPSIS FINAL RANKING")
    print("=" * 60)
    print(f"  {'Rank':<6} {'Network':<12} {'Score (Ci)':>12} {'D+':>10} {'D-':>10}")
    print("-" * 60)

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    for entry in ranking:
        medal = medals.get(entry["rank"], "  ")
        print(
            f"  {entry['rank']:<4} "
            f"{medal} {entry['network']:<10} "
            f"{entry['closeness']:>12.4f} "
            f"{entry['distance_best']:>10.4f} "
            f"{entry['distance_worst']:>10.4f}"
        )

    print("=" * 60)
    best = ranking[0]
    print(f"\n  ✅ RECOMMENDED NETWORK : {best['network']}")
    print(f"     Closeness Score     : {best['closeness']:.4f}")
    print("=" * 60)


# =============================================================================
# INTERNAL HELPER: _print_matrix
# =============================================================================
def _print_matrix(matrix: np.ndarray,
                  alternatives: list,
                  criteria: list,
                  title: str = "MATRIX") -> None:
    """
    Prints a formatted matrix with row and column labels.

    Args:
        matrix       (np.ndarray): 2D array to display.
        alternatives (list)      : Row labels (network names).
        criteria     (list)      : Column labels (criterion dicts).
        title        (str)       : Display title.
    """
    crit_names = [c["name"][:10] for c in criteria]   # Truncate for display

    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)

    # Header
    header = f"  {'Network':<12}"
    for name in crit_names:
        header += f" {name:>12}"
    print(header)
    print("-" * 75)

    # Rows
    for i, alt in enumerate(alternatives):
        row = f"  {alt:<12}"
        for j in range(len(criteria)):
            row += f" {matrix[i, j]:>12.6f}"
        print(row)

    print("=" * 75)


# =============================================================================
# INTERNAL HELPER: _validate_inputs
# =============================================================================
def _validate_inputs(decision_matrix: np.ndarray,
                     weights: np.ndarray,
                     criteria: list,
                     alternatives: list) -> None:
    """
    Validates all TOPSIS inputs for dimensional consistency.

    Raises:
        ValueError: With a descriptive message if any check fails.
    """
    if decision_matrix.ndim != 2:
        raise ValueError("Decision matrix must be a 2D numpy array.")

    n_alt, n_crit = decision_matrix.shape

    if len(alternatives) != n_alt:
        raise ValueError(
            f"Number of alternatives ({len(alternatives)}) must match "
            f"number of rows in decision matrix ({n_alt})."
        )

    if len(criteria) != n_crit:
        raise ValueError(
            f"Number of criteria ({len(criteria)}) must match "
            f"number of columns in decision matrix ({n_crit})."
        )

    if len(weights) != n_crit:
        raise ValueError(
            f"Weight vector length ({len(weights)}) must match "
            f"number of criteria ({n_crit})."
        )

    if not np.isclose(weights.sum(), 1.0, atol=1e-4):
        raise ValueError(
            f"Weights must sum to 1.0. Current sum: {weights.sum():.4f}."
        )

    for criterion in criteria:
        if criterion.get("objective") not in ("min", "max"):
            raise ValueError(
                f"Criterion '{criterion.get('name')}' has invalid objective "
                f"'{criterion.get('objective')}'. Must be 'min' or 'max'."
            )
