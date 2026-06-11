import math
from shared.schemas.electre import (
    CriteriaDefinition,
    CriteriaDirection,
    CriteriaType,
    AlternativeDefinition,
    SolveRequest,
)
from client.core.parsing import parse_required_float


def rows_to_criteria(rows):
    criterias = []

    if rows is None:
        return criterias

    if hasattr(rows, "values"):
        rows = rows.values.tolist()

    for row in rows:
        if not row or not row[0]:
            continue

        name = str(row[0]).strip()

        direction_str = str(row[1]).strip().lower() if len(row) > 1 and row[1] is not None else "maximize"
        direction = CriteriaDirection.MAXIMIZE
        if direction_str in ["minimize", "минимизиране", "min", "минимизирай"]:
            direction = CriteriaDirection.MINIMIZE

        weight = parse_required_float(row[2], f"Тежест за критерий {name}")

        type_str = str(row[3]).strip().lower() if len(row) > 3 and row[3] is not None else "quantitative"
        c_type = CriteriaType.QUANTITATIVE
        if type_str in ["qualitative", "качествен", "качествена", "qual"]:
            c_type = CriteriaType.QUALITATIVE

        criterias.append(
            CriteriaDefinition(
                name=name,
                direction=direction,
                weight=weight,
                type=c_type,
            )
        )

    return criterias


def rows_to_alternatives(rows, criterias):
    alternatives = []

    if rows is None:
        return alternatives

    if hasattr(rows, "values"):
        rows = rows.values.tolist()
    criteria_names = [c.name for c in criterias]

    for row in rows:
        if not row or not row[0]:
            continue

        name = str(row[0]).strip()
        values = {}

        for i, criteria_name in enumerate(criteria_names):
            col_index = i + 1
            if col_index < len(row):
                val = parse_required_float(
                    row[col_index],
                    f"Стойност за {criteria_name} при алтернатива {name}",
                )
                values[criteria_name] = val
            else:
                values[criteria_name] = 0.0

        alternatives.append(
            AlternativeDefinition(name=name, values=values)
        )

    return alternatives


def build_electre_request(
    problem_name,
    criteria_table,
    alternatives_table,
    concordance_threshold,
    discordance_threshold,
):
    criterias = rows_to_criteria(criteria_table)

    if criterias:
        weights_sum = sum(c.weight for c in criterias)
        if not math.isclose(weights_sum, 1.0, rel_tol=1e-5):
            raise ValueError(
                f"Сумата на тежестите трябва да е 1.0, а в момента е {weights_sum:.4f}"
            )

    alternatives = rows_to_alternatives(alternatives_table, criterias)

    try:
        c_thr = float(concordance_threshold)
    except (TypeError, ValueError):
        raise ValueError("Прагът на съгласие трябва да е число между 0 и 1.")
    try:
        d_thr = float(discordance_threshold)
    except (TypeError, ValueError):
        raise ValueError("Прагът на несъгласие трябва да е число между 0 и 1.")

    if not (0.0 <= c_thr <= 1.0):
        raise ValueError("Прагът на съгласие трябва да е в интервала [0, 1].")
    if not (0.0 <= d_thr <= 1.0):
        raise ValueError("Прагът на несъгласие трябва да е в интервала [0, 1].")

    return SolveRequest(
        problem_name=problem_name or "ELECTRE_Problem",
        criterias=criterias,
        alternatives=alternatives,
        concordance_threshold=c_thr,
        discordance_threshold=d_thr,
    )
