import math

import numpy as np
import pytest
from fastapi.testclient import TestClient

from server.main import app
from server.services.electre_solver import solve as electre_solve
from shared.schemas.electre import (
    AlternativeDefinition,
    CriteriaDefinition,
    CriteriaDirection,
    CriteriaType,
    SolveRequest,
)

client = TestClient(app)


def _classic_request(c_thr=0.65, d_thr=0.35):
    return SolveRequest(
        problem_name="Classic",
        criterias=[
            CriteriaDefinition(name="c1", direction=CriteriaDirection.MAXIMIZE, weight=0.20),
            CriteriaDefinition(name="c2", direction=CriteriaDirection.MAXIMIZE, weight=0.15),
            CriteriaDefinition(name="c3", direction=CriteriaDirection.MAXIMIZE, weight=0.40),
            CriteriaDefinition(name="c4", direction=CriteriaDirection.MAXIMIZE, weight=0.25),
        ],
        alternatives=[
            AlternativeDefinition(name="A", values={"c1": 15, "c2": 9, "c3": 6, "c4": 10}),
            AlternativeDefinition(name="B", values={"c1": 10, "c2": 6, "c3": 8, "c4": 8}),
            AlternativeDefinition(name="C", values={"c1": 14, "c2": 10, "c3": 5, "c4": 12}),
            AlternativeDefinition(name="D", values={"c1": 9, "c2": 7, "c3": 9, "c4": 11}),
        ],
        concordance_threshold=c_thr,
        discordance_threshold=d_thr,
    )


def test_classic_example_kernel_and_outranking():
    resp = electre_solve(_classic_request())
    assert resp.status == "Optimal"
    assert set(resp.kernel) == {"A", "C", "D"}
    assert resp.dominated == ["B"]
    assert len(resp.outranking) == 1
    pair = resp.outranking[0]
    assert pair.dominator == "D"
    assert pair.dominated == "B"
    assert pair.concordance == pytest.approx(0.80, rel=1e-6)
    assert pair.discordance == pytest.approx(1.0 / 6.0, rel=1e-6)


def test_concordance_matrix_shape_and_bounds():
    resp = electre_solve(_classic_request())
    C = np.array(resp.concordance_matrix)
    assert C.shape == (4, 4)
    assert np.all(np.diag(C) == 0.0)
    assert np.all(C >= 0.0)
    assert np.all(C <= 1.0 + 1e-9)


def test_discordance_matrix_shape_and_bounds():
    resp = electre_solve(_classic_request())
    D = np.array(resp.discordance_matrix)
    assert D.shape == (4, 4)
    assert np.all(np.diag(D) == 0.0)
    assert np.all(D >= 0.0)
    assert np.all(D <= 1.0 + 1e-9)


def test_low_concordance_threshold_expands_outranking():
    resp_strict = electre_solve(_classic_request(c_thr=0.9, d_thr=0.1))
    resp_loose = electre_solve(_classic_request(c_thr=0.3, d_thr=0.9))
    assert len(resp_loose.outranking) >= len(resp_strict.outranking)


def test_all_pairs_outrank_yields_empty_kernel():
    req = _classic_request(c_thr=0.0, d_thr=1.0)
    resp = electre_solve(req)
    assert resp.status == "Optimal"
    assert resp.kernel == []
    assert len(resp.outranking) == 4 * 3


def test_no_outranking_status_when_thresholds_unsatisfiable():
    req = _classic_request(c_thr=0.99, d_thr=0.0)
    resp = electre_solve(req)
    assert resp.status == "NoOutranking"
    assert resp.outranking == []
    assert set(resp.kernel) == {"A", "B", "C", "D"}


def test_minimize_direction_is_inverted_correctly():
    req = SolveRequest(
        problem_name="Min",
        criterias=[
            CriteriaDefinition(name="cost", direction=CriteriaDirection.MINIMIZE, weight=0.5),
            CriteriaDefinition(name="quality", direction=CriteriaDirection.MAXIMIZE, weight=0.5),
        ],
        alternatives=[
            AlternativeDefinition(name="Cheap", values={"cost": 10, "quality": 5}),
            AlternativeDefinition(name="Pricey", values={"cost": 20, "quality": 5}),
        ],
        concordance_threshold=0.5,
        discordance_threshold=0.5,
    )
    resp = electre_solve(req)
    assert resp.kernel == ["Cheap"]
    assert resp.dominated == ["Pricey"]
    pairs = [(p.dominator, p.dominated) for p in resp.outranking]
    assert pairs == [("Cheap", "Pricey")]


def test_constant_column_does_not_divide_by_zero():
    req = SolveRequest(
        problem_name="Const",
        criterias=[
            CriteriaDefinition(name="a", direction=CriteriaDirection.MAXIMIZE, weight=0.5),
            CriteriaDefinition(name="b", direction=CriteriaDirection.MAXIMIZE, weight=0.5),
        ],
        alternatives=[
            AlternativeDefinition(name="X", values={"a": 5, "b": 1}),
            AlternativeDefinition(name="Y", values={"a": 5, "b": 2}),
            AlternativeDefinition(name="Z", values={"a": 5, "b": 3}),
        ],
    )
    resp = electre_solve(req)
    assert resp.status == "Optimal"
    D = np.array(resp.discordance_matrix)
    assert np.all(np.isfinite(D))


def test_identical_alternatives_have_zero_discordance_between_them():
    req = SolveRequest(
        problem_name="Twins",
        criterias=[
            CriteriaDefinition(name="a", direction=CriteriaDirection.MAXIMIZE, weight=0.5),
            CriteriaDefinition(name="b", direction=CriteriaDirection.MAXIMIZE, weight=0.5),
        ],
        alternatives=[
            AlternativeDefinition(name="X", values={"a": 5, "b": 5}),
            AlternativeDefinition(name="Y", values={"a": 5, "b": 5}),
            AlternativeDefinition(name="Z", values={"a": 3, "b": 3}),
        ],
    )
    resp = electre_solve(req)
    D = np.array(resp.discordance_matrix)
    assert D[0, 1] == pytest.approx(0.0, abs=1e-9)
    assert D[1, 0] == pytest.approx(0.0, abs=1e-9)


def test_qualitative_criteria_are_solved_like_quantitative():
    req_quant = SolveRequest(
        problem_name="Q",
        criterias=[
            CriteriaDefinition(name="a", direction=CriteriaDirection.MAXIMIZE, weight=0.5, type=CriteriaType.QUANTITATIVE),
            CriteriaDefinition(name="b", direction=CriteriaDirection.MAXIMIZE, weight=0.5, type=CriteriaType.QUANTITATIVE),
        ],
        alternatives=[
            AlternativeDefinition(name="X", values={"a": 4, "b": 2}),
            AlternativeDefinition(name="Y", values={"a": 3, "b": 5}),
            AlternativeDefinition(name="Z", values={"a": 5, "b": 4}),
        ],
    )
    req_qual = req_quant.model_copy(deep=True)
    for c in req_qual.criterias:
        c.type = CriteriaType.QUALITATIVE

    r_quant = electre_solve(req_quant)
    r_qual = electre_solve(req_qual)
    assert r_quant.concordance_matrix == r_qual.concordance_matrix
    assert r_quant.discordance_matrix == r_qual.discordance_matrix
    assert set(r_quant.kernel) == set(r_qual.kernel)


def test_single_alternative_yields_itself_as_kernel():
    req = SolveRequest(
        problem_name="Solo",
        criterias=[
            CriteriaDefinition(name="a", direction=CriteriaDirection.MAXIMIZE, weight=1.0),
        ],
        alternatives=[
            AlternativeDefinition(name="Only", values={"a": 42}),
        ],
    )
    resp = electre_solve(req)
    assert resp.kernel == ["Only"]
    assert resp.outranking == []


def test_empty_criterias_returns_empty_status():
    req = SolveRequest(
        problem_name="Empty",
        criterias=[],
        alternatives=[
            AlternativeDefinition(name="A", values={}),
        ],
    )
    resp = electre_solve(req)
    assert resp.status == "EmptyInput"
    assert resp.kernel == []


def test_empty_alternatives_returns_empty_status():
    req = SolveRequest(
        problem_name="Empty",
        criterias=[
            CriteriaDefinition(name="a", direction=CriteriaDirection.MAXIMIZE, weight=1.0),
        ],
        alternatives=[],
    )
    resp = electre_solve(req)
    assert resp.status == "EmptyInput"


def test_invalid_weights_raise_value_error():
    req = SolveRequest(
        problem_name="BadWeights",
        criterias=[
            CriteriaDefinition(name="a", direction=CriteriaDirection.MAXIMIZE, weight=0.3),
            CriteriaDefinition(name="b", direction=CriteriaDirection.MAXIMIZE, weight=0.3),
        ],
        alternatives=[
            AlternativeDefinition(name="X", values={"a": 1, "b": 1}),
            AlternativeDefinition(name="Y", values={"a": 2, "b": 2}),
        ],
    )
    with pytest.raises(ValueError, match="тежест"):
        electre_solve(req)


def test_missing_criterion_value_raises_value_error():
    req = SolveRequest(
        problem_name="Missing",
        criterias=[
            CriteriaDefinition(name="a", direction=CriteriaDirection.MAXIMIZE, weight=0.5),
            CriteriaDefinition(name="b", direction=CriteriaDirection.MAXIMIZE, weight=0.5),
        ],
        alternatives=[
            AlternativeDefinition(name="X", values={"a": 1, "b": 2}),
            AlternativeDefinition(name="Y", values={"a": 3}),
        ],
    )
    with pytest.raises(ValueError, match="липсващи"):
        electre_solve(req)


def test_weights_close_to_one_within_tolerance_are_accepted():
    req = SolveRequest(
        problem_name="Float",
        criterias=[
            CriteriaDefinition(name="a", direction=CriteriaDirection.MAXIMIZE, weight=1.0 / 3.0),
            CriteriaDefinition(name="b", direction=CriteriaDirection.MAXIMIZE, weight=1.0 / 3.0),
            CriteriaDefinition(name="c", direction=CriteriaDirection.MAXIMIZE, weight=1.0 / 3.0),
        ],
        alternatives=[
            AlternativeDefinition(name="X", values={"a": 1, "b": 1, "c": 1}),
            AlternativeDefinition(name="Y", values={"a": 2, "b": 2, "c": 2}),
        ],
    )
    resp = electre_solve(req)
    assert resp.status == "Optimal"


CLASSIC_API_PAYLOAD = {
    "problem_name": "API_Classic",
    "criterias": [
        {"name": "c1", "direction": "maximize", "weight": 0.20, "type": "quantitative"},
        {"name": "c2", "direction": "maximize", "weight": 0.15, "type": "qualitative"},
        {"name": "c3", "direction": "maximize", "weight": 0.40, "type": "quantitative"},
        {"name": "c4", "direction": "maximize", "weight": 0.25, "type": "qualitative"},
    ],
    "alternatives": [
        {"name": "A", "values": {"c1": 15, "c2": 9, "c3": 6, "c4": 10}},
        {"name": "B", "values": {"c1": 10, "c2": 6, "c3": 8, "c4": 8}},
        {"name": "C", "values": {"c1": 14, "c2": 10, "c3": 5, "c4": 12}},
        {"name": "D", "values": {"c1": 9, "c2": 7, "c3": 9, "c4": 11}},
    ],
    "concordance_threshold": 0.65,
    "discordance_threshold": 0.35,
}


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_api_classic_payload_returns_expected_kernel():
    resp = client.post("/api/electre-solve", json=CLASSIC_API_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Optimal"
    assert set(data["kernel"]) == {"A", "C", "D"}
    assert data["dominated"] == ["B"]
    assert len(data["outranking"]) == 1


def test_api_default_thresholds_are_used_when_omitted():
    payload = {k: v for k, v in CLASSIC_API_PAYLOAD.items() if "threshold" not in k}
    resp = client.post("/api/electre-solve", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Optimal"


def test_api_invalid_weights_return_422():
    bad = {**CLASSIC_API_PAYLOAD}
    bad["criterias"] = [
        {**c, "weight": 0.1} for c in CLASSIC_API_PAYLOAD["criterias"]
    ]
    resp = client.post("/api/electre-solve", json=bad)
    assert resp.status_code == 422
    assert "тежест" in resp.json()["detail"].lower()


def test_api_missing_value_returns_422():
    bad = {**CLASSIC_API_PAYLOAD}
    bad["alternatives"] = [
        {"name": "A", "values": {"c1": 15, "c2": 9, "c3": 6}},
        {"name": "B", "values": {"c1": 10, "c2": 6, "c3": 8, "c4": 8}},
        {"name": "C", "values": {"c1": 14, "c2": 10, "c3": 5, "c4": 12}},
        {"name": "D", "values": {"c1": 9, "c2": 7, "c3": 9, "c4": 11}},
    ]
    resp = client.post("/api/electre-solve", json=bad)
    assert resp.status_code == 422


def test_api_empty_criterias_returns_200_with_empty_status():
    payload = {**CLASSIC_API_PAYLOAD, "criterias": []}
    resp = client.post("/api/electre-solve", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "EmptyInput"


def test_api_invalid_concordance_threshold_returns_422():
    bad = {**CLASSIC_API_PAYLOAD, "concordance_threshold": 1.5}
    resp = client.post("/api/electre-solve", json=bad)
    assert resp.status_code == 422


def test_api_response_preserves_qualitative_type_in_request():
    resp = client.post("/api/electre-solve", json=CLASSIC_API_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert "alternative_names" in data
    assert data["alternative_names"] == ["A", "B", "C", "D"]


def test_api_outranking_pair_has_required_fields():
    resp = client.post("/api/electre-solve", json=CLASSIC_API_PAYLOAD)
    assert resp.status_code == 200
    pair = resp.json()["outranking"][0]
    assert set(pair.keys()) == {"dominator", "dominated", "concordance", "discordance"}
    assert math.isclose(pair["concordance"], 0.80, rel_tol=1e-6)
