from enum import Enum
from pydantic import BaseModel, Field

class CriteriaDirection(str, Enum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"

class CriteriaType(str, Enum):
    QUANTITATIVE = "quantitative"
    QUALITATIVE = "qualitative"

class CriteriaDefinition(BaseModel):
    name: str = Field(..., examples=["цена", "качество"])
    direction: CriteriaDirection
    weight: float = Field(...)
    type: CriteriaType = Field(default=CriteriaType.QUANTITATIVE)

class AlternativeDefinition(BaseModel):
    name: str = Field(...)
    values: dict[str, float] = Field(...)

class SolveRequest(BaseModel):
    problem_name: str = Field(...)
    criterias: list[CriteriaDefinition] = Field(...)
    alternatives: list[AlternativeDefinition] = Field(...)
    concordance_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    discordance_threshold: float = Field(default=0.3, ge=0.0, le=1.0)

class OutrankingPair(BaseModel):
    dominator: str
    dominated: str
    concordance: float
    discordance: float

class SolveResponse(BaseModel):
    problem_name: str
    status: str
    kernel: list[str] = Field(default_factory=list)
    dominated: list[str] = Field(default_factory=list)
    outranking: list[OutrankingPair] = Field(default_factory=list)
    alternative_names: list[str] = Field(default_factory=list)
    concordance_matrix: list[list[float]] = Field(default_factory=list)
    discordance_matrix: list[list[float]] = Field(default_factory=list)
