# =============================================================================
# FILE: ahp.py
# ROLE: AHP Engine — Criteria Weight Calculation + Consistency Check
# DESCRIPTION:
#   Implements the Analytic Hierarchy Process (AHP) method.
#   Takes a pairwise comparison matrix as input and returns:
#     - A normalized priority vector (weights for each criterion)
#     - A Consistency Ratio (CR) to validate the matrix
#   This module is generic and reusable for any number of criteria.
# =============================================================================

import numpy as np


# =============================================================================
# AHP RANDOM INDEX TABLE (Saaty, 1980)
# Used to compute the Consistency Ratio (CR = CI / RI)
# Key: number of criteria (n), Value: average Random Index
# =============================================================================
RANDOM_INDEX = {
    1: 0.00,
    2: 0.00,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49
}


# =============================================================================
# FUNCTION: compute_ahp_weights
# =============================================================================
def compute_ahp_weights(matrix: np.ndarray) -> dict:
    """
    Computes AHP priority weights from a pairwise comparison matrix.

    Steps:
      1. Normalize each column (divide each element by its column sum).
      2. Average each row of the normalized matrix → priority vector (weights).
      3. Compute lambda_max (principal eigenvalue approximation).
      4. Compute Consistency Index (CI) and Consistency Ratio (CR).

    Args:
        matrix (np.ndarray): Square pairwise comparison matrix (n x n).
                             Values follow Saaty's scale (1–9).

    Returns:
        dict with keys:
            'weights'     : np.ndarray — normalized priority vector (sums to 1.0)
            'lambda_max'  : float      — principal eigenvalue
            'CI'          : float      — Consistency Index
            'CR'          : float      — Consistency Ratio
            'consistent'  : bool       — True if CR < 0.10
            'n'           : int        — number of criteria

    Raises:
        ValueError: If matrix is not square, not positive, or size > 10.
    """

    # --- Input Validation ---
    _validate_matrix(matrix)

    n = matrix.shape[0]

    # --- Step 1: Normalize each column ---
    col_sums = matrix.sum(axis=0)                   # Sum of each column
    normalized = matrix / col_sums                  # Divide each element by its column sum

    # --- Step 2: Priority vector (weights) ---
    # Average of each row in the normalized matrix
    weights = normalized.mean(axis=1)               # Shape: (n,)

    # --- Step 3: Compute lambda_max ---
    # Multiply original matrix by the weights vector, then divide by weights
    weighted_sum = matrix @ weights                  # Matrix-vector product
    lambda_values = weighted_sum / weights           # Element-wise division
    lambda_max = lambda_values.mean()                # Average

    # --- Step 4: Consistency Index (CI) ---
    CI = (lambda_max - n) / (n - 1) if n > 1 else 0.0

    # --- Step 5: Consistency Ratio (CR) ---
    RI = RANDOM_INDEX.get(n, 1.49)                  # Fallback to 1.49 for n > 10
    CR = CI / RI if RI > 0 else 0.0

    consistent = CR < 0.10

    return {
        "weights": weights,
        "lambda_max": lambda_max,
        "CI": CI,
        "CR": CR,
        "consistent": consistent,
        "n": n
    }


# =============================================================================
# FUNCTION: get_manual_matrix
# =============================================================================
def get_manual_matrix(criteria: list) -> np.ndarray:
    """
    Interactively prompts the user to enter a pairwise comparison matrix
    element by element (upper triangle only). The lower triangle is filled
    automatically using reciprocals, and the diagonal is set to 1.

    Args:
        criteria (list): List of criterion name strings.

    Returns:
        np.ndarray: Complete pairwise comparison matrix (n x n).
    """
    n = len(criteria)
    matrix = np.ones((n, n), dtype=float)

    print("\n" + "=" * 60)
    print("  MANUAL PAIRWISE COMPARISON MATRIX ENTRY")
    print("=" * 60)
    print("  Saaty's scale:")
    print("    1 = Equal importance")
    print("    3 = Moderate importance")
    print("    5 = Strong importance")
    print("    7 = Very strong importance")
    print("    9 = Extreme importance")
    print("  (Use fractions like 1/3, 1/5 for inverse comparisons)")
    print("=" * 60)

    for i in range(n):
        for j in range(i + 1, n):
            while True:
                try:
                    prompt = (
                        f"\n  How important is [{criteria[i]['name']}]\n"
                        f"  compared to [{criteria[j]['name']}]?\n"
                        f"  Enter value (e.g. 3 or 1/3): "
                    )
                    raw = input(prompt).strip()

                    # Support fraction input like "1/3"
                    if "/" in raw:
                        num, den = raw.split("/")
                        value = float(num) / float(den)
                    else:
                        value = float(raw)

                    # Validate range
                    if value <= 0:
                        print("  ⚠ Value must be positive. Try again.")
                        continue
                    if value > 9 or value < 1/9:
                        print("  ⚠ Value should be between 1/9 and 9. Try again.")
                        continue

                    matrix[i][j] = value
                    matrix[j][i] = 1.0 / value
                    break

                except (ValueError, ZeroDivisionError):
                    print("  ⚠ Invalid input. Enter a number or fraction like 1/3.")

    return matrix


# =============================================================================
# FUNCTION: print_ahp_results
# =============================================================================
def print_ahp_results(ahp_result: dict, criteria: list) -> None:
    """
    Prints a formatted summary of the AHP computation results.

    Args:
        ahp_result (dict): Output from compute_ahp_weights().
        criteria (list)  : List of criterion dicts from networks.py.
    """
    weights    = ahp_result["weights"]
    lambda_max = ahp_result["lambda_max"]
    CI         = ahp_result["CI"]
    CR         = ahp_result["CR"]
    consistent = ahp_result["consistent"]

    print("\n" + "=" * 60)
    print("  AHP RESULTS — CRITERIA WEIGHTS")
    print("=" * 60)

    for i, criterion in enumerate(criteria):
        bar = "█" * int(weights[i] * 40)   # Visual bar proportional to weight
        print(f"  {criterion['name']:<22} {weights[i]:.4f}  {bar}")

    print("-" * 60)
    print(f"  Sum of weights       : {weights.sum():.4f}  (should be 1.0000)")
    print(f"  λ_max                : {lambda_max:.4f}")
    print(f"  Consistency Index    : {CI:.4f}")
    print(f"  Consistency Ratio    : {CR:.4f}")

    if consistent:
        print(f"  ✅ Matrix is CONSISTENT (CR < 0.10) — Weights are valid.")
    else:
        print(f"  ⚠️  Matrix is INCONSISTENT (CR ≥ 0.10) — Review your comparisons.")
        print(f"     Results may not be reliable.")

    print("=" * 60)


# =============================================================================
# INTERNAL HELPER: _validate_matrix
# =============================================================================
def _validate_matrix(matrix: np.ndarray) -> None:
    """
    Validates the pairwise comparison matrix before computation.

    Checks:
      - Must be a 2D numpy array.
      - Must be square (n x n).
      - All values must be strictly positive.
      - Size must be between 2 and 10 (RI table coverage).
      - Diagonal elements must all be 1.

    Args:
        matrix (np.ndarray): The matrix to validate.

    Raises:
        ValueError: With a descriptive message if any check fails.
    """
    if not isinstance(matrix, np.ndarray) or matrix.ndim != 2:
        raise ValueError("AHP matrix must be a 2D numpy array.")

    rows, cols = matrix.shape
    if rows != cols:
        raise ValueError(f"AHP matrix must be square. Got shape {matrix.shape}.")

    if rows < 2 or rows > 10:
        raise ValueError(f"Matrix size must be between 2 and 10. Got {rows}.")

    if np.any(matrix <= 0):
        raise ValueError("All matrix values must be strictly positive (> 0).")

    diagonal = np.diag(matrix)
    if not np.allclose(diagonal, 1.0):
        raise ValueError("Diagonal elements of the AHP matrix must all be 1.")
