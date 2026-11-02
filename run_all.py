# =============================================================================
# FILE: run_all.py
# ROLE: Reproducible batch run — all predefined scenarios, no user input
# DESCRIPTION:
#   Runs AHP then TOPSIS on the 3 predefined IoT scenarios and writes:
#     - results/weights.csv              : AHP weights + consistency per scenario
#     - results/ranking_<scenario>.csv   : TOPSIS ranking per scenario
#     - results/summary.md               : Markdown tables (used in the README)
#     - figures/ranking_<scenario>.png   : ranking bar chart per scenario
#
#   Run with: python run_all.py
# =============================================================================

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no window: figures are only saved to disk

import pandas as pd

from ahp import compute_ahp_weights
from chart import plot_ranking
from data.networks import ALTERNATIVES, CRITERIA, DECISION_MATRIX, SCENARIOS
from topsis import run_topsis

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"


def run_scenario(scenario: dict) -> tuple:
    """Returns (ahp_result, topsis_result) for one predefined scenario."""
    ahp_result = compute_ahp_weights(scenario["matrix"])
    topsis_result = run_topsis(
        decision_matrix=DECISION_MATRIX,
        weights=ahp_result["weights"],
        criteria=CRITERIA,
        alternatives=ALTERNATIVES,
    )
    return ahp_result, topsis_result


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)

    weight_rows = []
    summary = ["# Résultats AHP-TOPSIS (générés par `python run_all.py`)", ""]

    for key, scenario in SCENARIOS.items():
        if scenario["matrix"] is None:  # custom scenario: interactive only
            continue
        ahp_result, topsis_result = run_scenario(scenario)
        slug = scenario["slug"]

        row = {"scenario": scenario["name"]}
        row.update({c["name"]: round(w, 4) for c, w in zip(CRITERIA, ahp_result["weights"])})
        row.update({"lambda_max": round(ahp_result["lambda_max"], 4),
                    "CI": round(ahp_result["CI"], 4),
                    "CR": round(ahp_result["CR"], 4),
                    "consistent": ahp_result["consistent"]})
        weight_rows.append(row)

        ranking = pd.DataFrame([
            {"rank": r["rank"], "network": r["network"],
             "closeness_Ci": round(r["closeness"], 4),
             "D_plus": round(r["distance_best"], 4),
             "D_minus": round(r["distance_worst"], 4)}
            for r in topsis_result["ranking"]
        ])
        ranking.to_csv(RESULTS_DIR / f"ranking_{slug}.csv", index=False)

        plot_ranking(topsis_result["ranking"], scenario_name=scenario["name"],
                     output_path=str(FIGURES_DIR / f"ranking_{slug}.png"), show=False)

        summary += [f"## {key}. {scenario['name']}", "",
                    f"Cohérence AHP : CR = {ahp_result['CR']:.4f} "
                    f"({'cohérent' if ahp_result['consistent'] else 'incohérent'}, seuil 0,10)", "",
                    ranking.to_markdown(index=False), "",
                    f"![Classement {scenario['name']}](../figures/ranking_{slug}.png)", ""]

    weights = pd.DataFrame(weight_rows)
    weights.to_csv(RESULTS_DIR / "weights.csv", index=False)
    summary[2:2] = ["## Poids AHP des critères", "", weights.to_markdown(index=False), ""]
    (RESULTS_DIR / "summary.md").write_text("\n".join(summary), encoding="utf-8")
    print(f"\n✅ Résultats écrits dans {RESULTS_DIR.name}/ et {FIGURES_DIR.name}/")


if __name__ == "__main__":
    main()
