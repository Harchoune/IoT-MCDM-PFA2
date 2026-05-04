# =============================================================================
# FILE: data/networks.py
# ROLE: Technical Database — Decision Matrix + Criteria Metadata
# DESCRIPTION:
#   This file is the ONLY place where raw network performance data is stored.
#   It is completely separated from the calculation engine.
#   To update a value or add a new network, only this file needs to be modified.
# =============================================================================

import numpy as np

# =============================================================================
# SECTION 1: ALTERNATIVES (IoT Networks to evaluate)
# =============================================================================

ALTERNATIVES = [
    "LoRaWAN",
    "Sigfox",
    "NB-IoT",
    "LTE-M",
    "Wi-Fi",
    "BLE"
]

# =============================================================================
# SECTION 2: CRITERIA METADATA
# Each criterion is defined with:
#   - 'name'      : Full display name
#   - 'unit'      : Measurement unit
#   - 'objective' : 'min' (lower is better) or 'max' (higher is better)
# =============================================================================

CRITERIA = [
    {
        "name": "Energy Consumption",
        "unit": "mW",
        "objective": "min"   # Lower energy consumption is better
    },
    {
        "name": "Range / Coverage",
        "unit": "km",
        "objective": "max"   # Higher range is better
    },
    {
        "name": "Data Rate",
        "unit": "kbps",
        "objective": "max"   # Higher data rate is better
    },
    {
        "name": "Total Cost",
        "unit": "USD/year",
        "objective": "min"   # Lower cost is better
    },
    {
        "name": "Latency",
        "unit": "ms",
        "objective": "min"   # Lower latency is better
    }
]

# =============================================================================
# SECTION 3: DECISION MATRIX
# Rows    → Alternatives (6 networks)
# Columns → Criteria (5 criteria), in the same order as CRITERIA list above:
#           [Energy(mW), Range(km), DataRate(kbps), Cost(USD/yr), Latency(ms)]
#
# Sources & References:
#   - LoRaWAN : Low power (~50mW TX), long range (5-15km), low data rate (0.3-50kbps)
#   - Sigfox  : Ultra-low power (~25mW), very long range (10-40km), very low rate (0.1kbps)
#   - NB-IoT  : Moderate power (~300mW), good coverage (10km), moderate rate (250kbps)
#   - LTE-M   : Moderate-high power (~400mW), wide coverage (10km), good rate (1000kbps)
#   - Wi-Fi   : High power (~1000mW), short range (0.1km), very high rate (54000kbps)
#   - BLE     : Very low power (~15mW), very short range (0.1km), moderate rate (1000kbps)
# =============================================================================

DECISION_MATRIX = np.array([
    # Energy(mW)  Range(km)  DataRate(kbps)  Cost(USD/yr)  Latency(ms)
    [   50,          10,          50,             100,          500   ],  # LoRaWAN
    [   25,          40,           0.1,             50,         6000  ],  # Sigfox
    [  300,          10,         250,             200,          1500  ],  # NB-IoT
    [  400,          10,        1000,             400,           100  ],  # LTE-M
    [ 1000,           0.1,     54000,             150,            10  ],  # Wi-Fi
    [   15,           0.1,      1000,              80,            10  ],  # BLE
], dtype=float)


# =============================================================================
# SECTION 4: PREDEFINED AHP SCENARIOS
# These are ready-to-use pairwise comparison matrices for common IoT use cases.
# The matrix is 5x5 (one entry per pair of criteria).
# Scale: 1=Equal, 3=Moderate, 5=Strong, 7=Very Strong, 9=Extreme importance.
#
# Criteria order in the matrix:
#   [0] Energy Consumption
#   [1] Range / Coverage
#   [2] Data Rate
#   [3] Total Cost
#   [4] Latency
# =============================================================================

SCENARIOS = {

    "1": {
        "name": "Smart Agriculture (Remote Sensor Monitoring)",
        "description": (
            "Long-range coverage and low energy are critical.\n"
            "Low data rate and high latency are acceptable.\n"
            "Cost matters but is secondary."
        ),
        "matrix": np.array([
            # Energy  Range  DataRate  Cost  Latency
            [1,       1/3,   5,        2,    7      ],  # Energy
            [3,       1,     7,        3,    9      ],  # Range
            [1/5,     1/7,   1,        1/3,  2      ],  # DataRate
            [1/2,     1/3,   3,        1,    5      ],  # Cost
            [1/7,     1/9,   1/2,      1/5,  1      ],  # Latency
        ], dtype=float)
    },

    "2": {
        "name": "Smart Factory (Industrial Automation)",
        "description": (
            "Ultra-low latency and high data rate are critical.\n"
            "Range is moderate. Energy and cost are secondary."
        ),
        "matrix": np.array([
            # Energy  Range  DataRate  Cost  Latency
            [1,       2,     1/5,      1/2,  1/7    ],  # Energy
            [1/2,     1,     1/7,      1/3,  1/9    ],  # Range
            [5,       7,     1,        3,    1/2    ],  # DataRate
            [2,       3,     1/3,      1,    1/5    ],  # Cost
            [7,       9,     2,        5,    1      ],  # Latency
        ], dtype=float)
    },

    "3": {
        "name": "Smart City (Asset Tracking)",
        "description": (
            "Cost and coverage are the top priorities.\n"
            "Energy efficiency also matters.\n"
            "Data rate and latency are less critical."
        ),
        "matrix": np.array([
            # Energy  Range  DataRate  Cost  Latency
            [1,       1/2,   3,        1/2,  5      ],  # Energy
            [2,       1,     5,        1/2,  7      ],  # Range
            [1/3,     1/5,   1,        1/5,  2      ],  # DataRate
            [2,       2,     5,        1,    7      ],  # Cost
            [1/5,     1/7,   1/2,      1/7,  1      ],  # Latency
        ], dtype=float)
    },

    "4": {
        "name": "Custom Scenario (Manual Input)",
        "description": (
            "You will enter your own pairwise comparison matrix manually.\n"
            "Useful for testing a specific IoT use case."
        ),
        "matrix": None   # Will be filled interactively in main.py
    }
}
