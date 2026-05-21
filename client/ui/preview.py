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

        bg_direction = "Максимизиране" if req.direction == "maximize" else "Минимизиране"

        lines = [
            f"## Задача: {req.name}",
            "",
            f"**Посока:** `{bg_direction}`",
            "",
            "### Целева функция",
            "",
            f"`{bg_direction} {format_expression(req.objective.coefficients)}`",
            "",
            "### Променливи",
            "",
        ]

        if not req.variables:
            lines.append("_Няма дефинирани променливи._")
        else:
            for var in req.variables:
                cat_bg = var.category.replace("Continuous", "Непрекъсната").replace("Integer", "Целочислена").replace("Binary", "Булева")
                lines.append(
                    f"- `{var.name}` | долна граница: `{var.low_bound}` | горна граница: `{var.up_bound}` | категория: `{cat_bg}`"
                )

        lines.extend(["", "### Ограничения", ""])

        if not req.constraints:
            lines.append("_Няма дефинирани ограничения._")
        else:
            for constraint in req.constraints:
                label = constraint.name or "без_име"
                expr = format_expression(constraint.coefficients)
                lines.append(
                    f"- `{label}`: `{expr} {constraint.operator} {constraint.rhs}`"
                )

        return "\n".join(lines)

    except (ValueError, ValidationError, KeyError) as exc:
        return f"### Грешка при прегледа\n\n`{exc}`"