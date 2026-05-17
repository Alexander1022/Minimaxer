import pulp

from schemas import (
    SolveRequest,
    SolveResponse,
    VariableResult,
    OptimizationDirection,
    ConstraintOperator,
)


def solve(req: SolveRequest) -> SolveResponse:
    var_names = {v.name for v in req.variables}

    unknown_in_obj = set(req.objective.coefficients.keys()) - var_names
    if unknown_in_obj:
        raise ValueError(f"Objective references undeclared variables: {sorted(unknown_in_obj)}")

    for i, c in enumerate(req.constraints):
        unknown = set(c.coefficients.keys()) - var_names
        if unknown:
            raise ValueError(f"Constraint {i} references undeclared variables: {sorted(unknown)}")

    sense = pulp.LpMaximize if req.direction == OptimizationDirection.MAXIMIZE else pulp.LpMinimize
    prob = pulp.LpProblem(req.name, sense)

    var_map = {}
    for var_def in req.variables:
        lp_var = pulp.LpVariable(
            var_def.name,
            lowBound=var_def.low_bound,
            upBound=var_def.up_bound,
            cat=var_def.category,
        )
        var_map[var_def.name] = lp_var

    prob += pulp.lpSum(
        coef * var_map[name] for name, coef in req.objective.coefficients.items()
    )

    for c in req.constraints:
        expr = pulp.lpSum(coef * var_map[name] for name, coef in c.coefficients.items())
        if c.operator == ConstraintOperator.LTE:
            prob += expr <= c.rhs
        elif c.operator == ConstraintOperator.GTE:
            prob += expr >= c.rhs
        else:
            prob += expr == c.rhs

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    status = pulp.LpStatus[prob.status]
    if status == "Optimal":
        return SolveResponse(
            problem_name=req.name,
            status=status,
            objective_value=pulp.value(prob.objective),
            variables=[
                VariableResult(name=name, value=var_map[name].varValue)
                for name in sorted(var_map.keys())
            ],
        )

    return SolveResponse(problem_name=req.name, status=status, objective_value=None, variables=None)