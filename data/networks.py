# =============================================================================
# FILE: data/networks.py
# ROLE: Technical Database — Decision Matrix + Criteria Metadata
# DESCRIPTION:
#   Loads the raw input data from the CSV files stored next to this module:
#     - decision_matrix.csv : performance of each network on each criterion
#     - criteria.csv        : name, unit and objective (min/max) of each criterion
#     - scenarios/*.csv     : AHP pairwise comparison matrices (Saaty scale)
#   The calculation engine (ahp.py, topsis.py) never reads files directly.
#   To update a value or add a network, edit the CSV files only.
#
# Decision matrix values (indicative orders of magnitude):
#   - LoRaWAN : Low power (~50mW TX), long range (5-15km), low data rate (0.3-50kbps)
#   - Sigfox  : Ultra-low power (~25mW), very long range (10-40km), very low rate (0.1kbps)
#   - NB-IoT  : Moderate power (~300mW), good coverage (10km), moderate rate (250kbps)
#   - LTE-M   : Moderate-high power (~400mW), wide coverage (10km), good rate (1000kbps)
#   - Wi-Fi   : High power (~1000mW), short range (0.1km), very high rate (54000kbps)
#   - BLE     : Very low power (~15mW), very short range (0.1km), moderate rate (1000kbps)
# =============================================================================

import csv
from fractions import Fraction
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).resolve().parent
SCENARIO_DIR = DATA_DIR / "scenarios"


def _read_rows(path: Path) -> list:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# =============================================================================
# SECTION 1: CRITERIA METADATA
#   - 'name'      : Full display name
#   - 'unit'      : Measurement unit
#   - 'objective' : 'min' (lower is better) or 'max' (higher is better)
# =============================================================================
_criteria_rows = _read_rows(DATA_DIR / "criteria.csv")
CRITERIA_KEYS = [row["key"] for row in _criteria_rows]
CRITERIA = [
    {"name": row["name"], "unit": row["unit"], "objective": row["objective"]}
    for row in _criteria_rows
]

# =============================================================================
# SECTION 2: ALTERNATIVES + DECISION MATRIX
# Rows    → Alternatives (networks)
# Columns → Criteria, in the same order as CRITERIA
# =============================================================================
_matrix_rows = _read_rows(DATA_DIR / "decision_matrix.csv")
ALTERNATIVES = [row["network"] for row in _matrix_rows]
DECISION_MATRIX = np.array(
    [[float(row[key]) for key in CRITERIA_KEYS] for row in _matrix_rows],
    dtype=float,
)


# =============================================================================
# SECTION 3: PREDEFINED AHP SCENARIOS
# Scale: 1=Equal, 3=Moderate, 5=Strong, 7=Very Strong, 9=Extreme importance.
# Fractions such as "1/3" are allowed in the CSV files.
# =============================================================================
def load_pairwise_matrix(path: Path) -> np.ndarray:
    """Reads an AHP pairwise comparison matrix (criteria order = CRITERIA_KEYS)."""
    rows = {row["criterion"]: row for row in _read_rows(path)}
    return np.array(
        [[float(Fraction(rows[i][j])) for j in CRITERIA_KEYS] for i in CRITERIA_KEYS],
        dtype=float,
    )


SCENARIOS = {
    "1": {
        "name": "Smart Agriculture (Remote Sensor Monitoring)",
        "slug": "smart_agriculture",
        "description": (
            "Long-range coverage and low energy are critical.\n"
            "Low data rate and high latency are acceptable.\n"
            "Cost matters but is secondary."
        ),
        "matrix": load_pairwise_matrix(SCENARIO_DIR / "1_smart_agriculture.csv"),
    },
    "2": {
        "name": "Smart Factory (Industrial Automation)",
        "slug": "smart_factory",
        "description": (
            "Ultra-low latency and high data rate are critical.\n"
            "Range is moderate. Energy and cost are secondary."
        ),
        "matrix": load_pairwise_matrix(SCENARIO_DIR / "2_smart_factory.csv"),
    },
    "3": {
        "name": "Smart City (Asset Tracking)",
        "slug": "smart_city",
        "description": (
            "Cost and coverage are the top priorities.\n"
            "Energy efficiency also matters.\n"
            "Data rate and latency are less critical."
        ),
        "matrix": load_pairwise_matrix(SCENARIO_DIR / "3_smart_city.csv"),
    },
    "4": {
        "name": "Custom Scenario (Manual Input)",
        "slug": "custom",
        "description": (
            "You will enter your own pairwise comparison matrix manually.\n"
            "Useful for testing a specific IoT use case."
        ),
        "matrix": None,  # Will be filled interactively in main.py
    },
}
