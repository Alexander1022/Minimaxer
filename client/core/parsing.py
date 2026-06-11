import logging

logger = logging.getLogger(__name__)


def parse_float(value, field_name):
    if value in [None, ""]:
        return None

    try:
        return float(value)
    except ValueError:
        logger.warning("%s трябва да е число, получено: %r", field_name, value)
        raise ValueError(f"{field_name} трябва да е число, получено: {value!r}")


def parse_required_float(value, field_name):
    if value in [None, ""]:
        raise ValueError(f"{field_name} е задължително")

    try:
        return float(value)
    except ValueError:
        logger.warning("%s трябва да е число, получено: %r", field_name, value)
        raise ValueError(f"{field_name} трябва да е число, получено: {value!r}")


def normalize_rows(rows):
    if rows is None:
        return []

    if hasattr(rows, "values"):
        rows = rows.values.tolist()

    return [
        list(row)
        for row in rows
        if row and any(cell not in [None, ""] for cell in row)
    ]