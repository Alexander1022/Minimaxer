from shared.schemas.optimization import (
    ConstraintDefinition,
    ConstraintOperator,
    LinearExpression,
    OptimizationDirection,
    SolveRequest,
    VariableDefinition,
)

from client.core.parsing import parse_float, parse_required_float


def rows_to_variables(rows):
    variables = []

    if rows is None:
        return variables

    if hasattr(rows, "values"):
        rows = rows.values.tolist()

    for row in rows:
        if not row or not row[0]:
            continue

        name = str(row[0]).strip()
        low_bound = parse_float(row[1], f"Low bound for variable {name}")
        up_bound = parse_float(row[2], f"Upper bound for variable {name}")
        category = str(row[3] or "Continuous").strip()

        variables.append(
            VariableDefinition(
                name=name,
                low_bound=low_bound,
                up_bound=up_bound,
                category=category,
            )
        )

    return variables


def rows_to_coefficients(rows):
    coefficients = {}

    if rows is None:
        return coefficients

    if hasattr(rows, "values"):
        rows = rows.values.tolist()

    for row in rows:
        if not row or not row[0]:
            continue

        name = str(row[0]).strip()
        value = float(row[1])
        coefficients[name] = value

    return coefficients


def rows_to_constraints(rows):
    constraints = []

    if rows is None:
        return constraints

    if hasattr(rows, "values"):
        rows = rows.values.tolist()

    for row in rows:
        if not row or not row[1]:
            continue

        name = None if row[0] in [None, ""] else str(row[0]).strip()
        coefficients_raw = str(row[1]).strip()
        operator = str(row[2]).strip()
        rhs = parse_required_float(row[3], f"RHS for constraint {name or 'unnamed'}")

        coefficients = {}

        for part in coefficients_raw.split(","):
            var_name, coef = part.split(":")
            coefficients[var_name.strip()] = parse_required_float(
                coef.strip(),
                f"Coefficient for variable {var_name.strip()} in constraint {name or 'unnamed'}",
            )

        constraints.append(
            ConstraintDefinition(
                name=name,
                coefficients=coefficients,
                operator=ConstraintOperator(operator),
                rhs=rhs,
            )
        )

    return constraints


def build_request(problem_name, direction, variables_table, objective_table, constraints_table):
    variables = rows_to_variables(variables_table)
    objective_coefficients = rows_to_coefficients(objective_table)
    constraints = rows_to_constraints(constraints_table)

    return SolveRequest(
        name=problem_name or "OptimizationProblem",
        direction=OptimizationDirection(direction),
        variables=variables,
        objective=LinearExpression(coefficients=objective_coefficients),
        constraints=constraints,
    )