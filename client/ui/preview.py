from pydantic import ValidationError
from client.core.builders import build_request


def format_expression(coefficients):
    if not coefficients:
        return "0"

    parts = []

    for var_name, coef in coefficients.items():
        if coef == 1:
            parts.append(f"{var_name}")
        elif coef == -1:
            parts.append(f"-{var_name}")
        else:
            parts.append(f"{coef}·{var_name}")

    return " + ".join(parts).replace("+ -", "- ")


def preview_problem(problem_name, direction, variables_table, objective_table, constraints_table):
    try:
        req = build_request(
            problem_name,
            direction,
            variables_table,
            objective_table,
            constraints_table,
        )

        lines = [
            f"## {req.name}",
            "",
            f"**Direction:** `{req.direction}`",
            "",
            "### Objective",
            "",
            f"`{req.direction} {format_expression(req.objective.coefficients)}`",
            "",
            "### Variables",
            "",
        ]

        if not req.variables:
            lines.append("_No variables defined._")
        else:
            for var in req.variables:
                lines.append(
                    f"- `{var.name}` | low: `{var.low_bound}` | up: `{var.up_bound}` | category: `{var.category}`"
                )

        lines.extend(["", "### Constraints", ""])

        if not req.constraints:
            lines.append("_No constraints defined._")
        else:
            for constraint in req.constraints:
                label = constraint.name or "unnamed"
                expr = format_expression(constraint.coefficients)
                lines.append(
                    f"- `{label}`: `{expr} {constraint.operator} {constraint.rhs}`"
                )

        return "\n".join(lines)

    except (ValueError, ValidationError, KeyError) as exc:
        return f"### Preview error\n\n`{exc}`"