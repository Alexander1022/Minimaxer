import pulp

from models import SolveRequest, SolveResponse


def solve(req: SolveRequest) -> SolveResponse:
    declared = set(req.variables)

    unknown_in_obj = set(req.objective) - declared
    if unknown_in_obj:
        raise ValueError(f"Objective references undeclared variables: {sorted(unknown_in_obj)}")

    for i, c in enumerate(req.constraints):
        unknown = set(c.coefficients) - declared
        if unknown:
            raise ValueError(f"Constraint {i} references undeclared variables: {sorted(unknown)}")

    sense = pulp.LpMaximize if req.goal == "max" else pulp.LpMinimize
    prob = pulp.LpProblem("lp", sense)

    cat = "Integer" if req.var_type == "integer" else "Continuous"
    lp_vars = pulp.LpVariable.dicts("", req.variables, cat=cat)

    prob += pulp.lpSum(coef * lp_vars[name] for name, coef in req.objective.items())

    for c in req.constraints:
        expr = pulp.lpSum(coef * lp_vars[name] for name, coef in c.coefficients.items())
        if c.operator == "<=":
            prob += expr <= c.rhs
        elif c.operator == ">=":
            prob += expr >= c.rhs
        else:
            prob += expr == c.rhs

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    status = pulp.LpStatus[prob.status]
    if status == "Optimal":
        return SolveResponse(
            status=status,
            objective_value=pulp.value(prob.objective),
            variables={name: var.varValue for name, var in lp_vars.items()},
        )

    return SolveResponse(status=status, objective_value=None, variables=None)