from enum import Enum
from pydantic import BaseModel, Field

class OptimizationDirection(str, Enum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"

class ConstraintOperator(str, Enum):
    LTE = "<=" # less than or equal to
    GTE = ">=" # greater than or equal to
    EQ = "==" # equal to

# Пример x >= 0, x <= 10
class VariableDefinition(BaseModel):
    name: str = Field(..., examples=["x"])
    low_bound: float | None = Field(default=None)
    up_bound: float | None = Field(default=None)
    category: str = Field(default="Continuous", examples=["Continuous", "Integer", "Binary"])

# Пример 3x + 4y
class LinearExpression(BaseModel):
    coefficients: dict[str, float] = Field(...)

# Пример c1 : 2x + 3y <= 10
class ConstraintDefinition(BaseModel):
    name: str | None = Field(default=None)
    coefficients: dict[str, float] = Field(...)
    operator: ConstraintOperator = Field(...)
    rhs: float = Field(...)

# JSON request schema за API-то
class SolveRequest(BaseModel):
    name: str = Field(default="OptimizationProblem")
    direction: OptimizationDirection
    variables: list[VariableDefinition]
    objective: LinearExpression
    constraints: list[ConstraintDefinition]


# Пример x = 5.0
class VariableResult(BaseModel):
    name: str
    value: float | None

# JSON response schema от API-то
class SolveResponse(BaseModel):
    problem_name: str
    status: str
    objective_value: float | None
    variables: list[VariableResult]