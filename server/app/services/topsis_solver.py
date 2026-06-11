import numpy as np
import math

from shared.schemas.topsis import (
    SolveRequest,
    SolveResponse,
    RankedAlternative,
    CriteriaDirection
)

def solve(req: SolveRequest) -> SolveResponse:
    if not req.criterias or not req.alternatives:
        return SolveResponse(
            problem_name=req.problem_name,
            status="EmptyInput",
            rankings=[]
        )
    
    criterias_names = [c.name for c in req.criterias]

    for alt in req.alternatives:
        missing = set(criterias_names) - set(alt.values.keys())
        if missing:
            raise ValueError(f"Алтернативата '{alt.name}' има липсващи стойности за критерии: ${missing}")
        
    matrix = np.array(
        [[alt.values[c_name] for c_name in criterias_names] for alt in req.alternatives],
        dtype=float
    )
    weights = np.array(
        [c.weight for c in req.criterias], dtype=float
    )
    
    if not math.isclose(np.sum(weights), 1.0, rel_tol=1e-5):
        raise ValueError(f"Сумата на тежестите трябва да е 1.0, а в момента е {np.sum(weights):.4f}")
    benefit = np.array(
        [c.direction == CriteriaDirection.MAXIMIZE for c in req.criterias],
        dtype=bool
    )

    col_norms = np.sqrt((matrix**2).sum(axis=0))
    norm_matrix = matrix / col_norms

    weighted_matrix = norm_matrix * weights

    pis = np.where(benefit, weighted_matrix.max(axis=0), weighted_matrix.min(axis=0))
    nis = np.where(benefit, weighted_matrix.min(axis=0), weighted_matrix.max(axis=0))

    s_pos = np.sqrt(((weighted_matrix-pis)**2).sum(axis=1))
    s_neg = np.sqrt(((weighted_matrix-nis)**2).sum(axis=1))

    total_distance = s_pos + s_neg

    closeness = np.where(total_distance == 0, 0.5, s_neg / total_distance)

    sorted_res = np.argsort(closeness)[::-1]

    rankings = []
    for rank_idx, alt_idx in enumerate(sorted_res, start=1):
        alt_def = req.alternatives[alt_idx]
        rankings.append(
            RankedAlternative(
                rank=rank_idx,
                name=alt_def.name,
                closeness_score=float(closeness[alt_idx]),
                values=alt_def.values
            )
        )

    return SolveResponse(
        problem_name=req.problem_name,
        status="Optimal",
        rankings=rankings
    )