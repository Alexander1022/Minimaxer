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

    for alt in req.alternatives:
        missing = set(criteria_names) - set(alt.values.keys())
        if missing:
            raise ValueError(
                f"Алтернативата '{alt.name}' има липсващи стойности за критерии: {missing}"
            )

    matrix = np.array(
        [[alt.values[c_name] for c_name in criteria_names] for alt in req.alternatives],
        dtype=float,
    )
    weights = np.array([c.weight for c in req.criterias], dtype=float)

    if not math.isclose(np.sum(weights), 1.0, rel_tol=1e-5):
        raise ValueError(
            f"Сумата на тежестите трябва да е 1.0, а в момента е {np.sum(weights):.4f}"
        )

    benefit = np.array(
        [c.direction == CriteriaDirection.MAXIMIZE for c in req.criterias],
        dtype=bool,
    )

    M = np.where(benefit, matrix, -matrix)
    n_alts = M.shape[0]

    ranges = M.max(axis=0) - M.min(axis=0)
    global_max_range = float(np.max(ranges))
    if global_max_range == 0.0:
        global_max_range = 1.0

    concordance_mask = M[:, None, :] >= M[None, :, :]
    C = (concordance_mask * weights).sum(axis=2)
    np.fill_diagonal(C, 0.0)

    diff = M[None, :, :] - M[:, None, :]
    worse = diff > 0
    norm_diff = diff / global_max_range
    masked = np.where(worse, norm_diff, -np.inf)
    D = masked.max(axis=2)
    D = np.where(np.isfinite(D), D, 0.0)
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

    index_counter = [0]
    index = {}
    lowlink = {}
    on_stack = set()
    stack = []
    sccs = []
    
    def strongconnect(v):
        index[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack.add(v)
        
        for w in range(n_alts):
            if outrank[v, w]:
                if w not in index:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif w in on_stack:
                    lowlink[v] = min(lowlink[v], index[w])
                    
        if lowlink[v] == index[v]:
            scc = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                scc.append(w)
                if w == v:
                    break
            sccs.append(scc)

    for v in range(n_alts):
        if v not in index:
            strongconnect(v)
            
    kernel_indices = []
    for scc in sccs:
        is_dominated = False
        scc_set = set(scc)
        for v in scc:
            for u in range(n_alts):
                if u not in scc_set and outrank[u, v]:
                    is_dominated = True
                    break
            if is_dominated:
                break
        if not is_dominated:
            kernel_indices.extend(scc)
            
    kernel = [req.alternatives[i].name for i in kernel_indices]
    dominated_list = [req.alternatives[i].name for i in range(n_alts) if i not in kernel_indices]

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
