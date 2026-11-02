"""Tests de non-régression de l'outil AHP-TOPSIS."""
import numpy as np
import pytest

from ahp import compute_ahp_weights
from data.networks import ALTERNATIVES, CRITERIA, DECISION_MATRIX, SCENARIOS
from topsis import run_topsis

PREDEFINED = [k for k, s in SCENARIOS.items() if s["matrix"] is not None]


def test_data_shapes():
    assert DECISION_MATRIX.shape == (len(ALTERNATIVES), len(CRITERIA))
    assert all(c["objective"] in ("min", "max") for c in CRITERIA)


@pytest.mark.parametrize("key", PREDEFINED)
def test_pairwise_matrix_is_reciprocal(key):
    m = SCENARIOS[key]["matrix"]
    assert np.allclose(m * m.T, 1.0)


@pytest.mark.parametrize("key", PREDEFINED)
def test_ahp_weights_valid_and_consistent(key):
    result = compute_ahp_weights(SCENARIOS[key]["matrix"])
    assert np.isclose(result["weights"].sum(), 1.0)
    assert (result["weights"] > 0).all()
    assert result["consistent"] and result["CR"] < 0.10


def test_ahp_perfectly_consistent_matrix():
    w = np.array([0.5, 0.3, 0.2])
    m = w[:, None] / w[None, :]
    result = compute_ahp_weights(m)
    assert np.allclose(result["weights"], w)
    assert result["CR"] == pytest.approx(0.0, abs=1e-9)


def test_ahp_rejects_invalid_matrix():
    with pytest.raises(ValueError):
        compute_ahp_weights(np.array([[1.0, 2.0], [0.5, 2.0]]))  # diagonale != 1


def test_topsis_dominant_alternative_ranks_first():
    criteria = [{"name": "gain", "unit": "", "objective": "max"},
                {"name": "cost", "unit": "", "objective": "min"}]
    matrix = np.array([[10.0, 1.0], [5.0, 5.0], [1.0, 10.0]])
    result = run_topsis(matrix, np.array([0.5, 0.5]), criteria, ["A", "B", "C"])
    assert [r["network"] for r in result["ranking"]] == ["A", "B", "C"]
    assert result["ranking"][0]["closeness"] == pytest.approx(1.0)


@pytest.mark.parametrize("key, expected_best", [("1", "Sigfox"), ("2", "Wi-Fi"), ("3", "Sigfox")])
def test_scenario_recommendations(key, expected_best):
    weights = compute_ahp_weights(SCENARIOS[key]["matrix"])["weights"]
    ranking = run_topsis(DECISION_MATRIX, weights, CRITERIA, ALTERNATIVES)["ranking"]
    assert ranking[0]["network"] == expected_best
    closeness = [r["closeness"] for r in ranking]
    assert all(0.0 <= c <= 1.0 for c in closeness)
