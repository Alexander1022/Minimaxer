from typing import Literal
from pydantic import BaseModel


class Constraint(BaseModel):
    coefficients: dict[str, float]
    operator: Literal["<=", ">=", "="]
    rhs: float


class SolveRequest(BaseModel):
    variables: list[str]
    objective: dict[str, float]
    goal: Literal["max", "min"]
    var_type: Literal["continuous", "integer"] = "continuous"
    constraints: list[Constraint]


class SolveResponse(BaseModel):
    status: str
    objective_value: float | None
    variables: dict[str, float] | None