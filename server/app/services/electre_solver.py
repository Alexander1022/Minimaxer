import math
import numpy as np

from shared.schemas.electre import (
    SolveRequest,
    SolveResponse,
    OutrankingPair,
    CriteriaDirection,
)

def solve(req: SolveRequest) -> SolveResponse:
    if not req.criterias or not req.alternatives:
        return SolveResponse(
            problem_name=req.problem_name,
            status="EmptyInput",
        )

    criteria_names = [c.name for c in req.criterias]
    n_alts = len(req.alternatives)
    n_crit = len(criteria_names)

    for alt in req.alternatives:
        missing = set(criteria_names) - set(alt.values.keys())
        if missing:
            raise ValueError(
                f"Алтернативата '{alt.name}' има липсващи стойности за критерии: {missing}"
            )

    A = np.array(
        [[alt.values[c_name] for c_name in criteria_names] for alt in req.alternatives],
        dtype=float,
    )

    weights = np.array([c.weight for c in req.criterias], dtype=float)
    directions = np.array([c.direction == CriteriaDirection.MAXIMIZE for c in req.criterias])

    if not math.isclose(np.sum(weights), 1.0, rel_tol=1e-5):
        raise ValueError(f"Сумата на тежестите трябва да е 1.0, а е {np.sum(weights):.4f}")

    norms = np.sqrt(np.sum(A ** 2, axis=0))
    norms[norms == 0] = 1.0
    R = A / norms

    V = R * weights

    C = np.zeros((n_alts, n_alts))
    for k in range(n_alts):
        for l in range(n_alts):
            if k == l:
                continue
            better_or_equal = np.where(
                directions,
                A[k, :] >= A[l, :],
                A[k, :] <= A[l, :]
            )
            C[k, l] = np.sum(weights[better_or_equal])
    np.fill_diagonal(C, 0.0)

    D = np.zeros((n_alts, n_alts))
    for k in range(n_alts):
        for l in range(n_alts):
            if k == l:
                continue
            better_or_equal = np.where(
                directions,
                A[k, :] >= A[l, :],
                A[k, :] <= A[l, :]
            )
            D_kl = ~better_or_equal
            if not np.any(D_kl):
                D[k, l] = 0.0
                continue
            diff = np.abs(V[k, :] - V[l, :])
            numerator = np.max(diff[D_kl])
            denominator = np.max(diff)
            if denominator == 0:
                D[k, l] = 0.0
            else:
                D[k, l] = numerator / denominator
    np.fill_diagonal(D, 0.0)

    c_star = req.concordance_threshold
    d_star = req.discordance_threshold

    outrank = (C >= c_star) & (D <= d_star)
    np.fill_diagonal(outrank, False)

    outranking_pairs = []
    for i in range(n_alts):
        for j in range(n_alts):
            if outrank[i, j]:
                outranking_pairs.append(
                    OutrankingPair(
                        dominator=req.alternatives[i].name,
                        dominated=req.alternatives[j].name,
                        concordance=float(C[i, j]),
                        discordance=float(D[i, j]),
                    )
                )

    is_dominated = np.zeros(n_alts, dtype=bool)
    for j in range(n_alts):
        for i in range(n_alts):
            if i != j and outrank[i, j]:
                is_dominated[j] = True
                break

    kernel = [req.alternatives[i].name for i in range(n_alts) if not is_dominated[i]]
    dominated_list = [req.alternatives[i].name for i in range(n_alts) if is_dominated[i]]

    status = "Optimal"
    if not outranking_pairs:
        status = "NoOutranking"

    return SolveResponse(
        problem_name=req.problem_name,
        status=status,
        kernel=kernel,
        dominated=dominated_list,
        outranking=outranking_pairs,
        alternative_names=[a.name for a in req.alternatives],
        concordance_matrix=C.tolist(),
        discordance_matrix=D.tolist(),
    )