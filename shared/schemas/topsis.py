from enum import Enum
from pydantic import BaseModel, Field

class CriteriaDirection(str, Enum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"

'''
    Всяка една критерия има име, посока (мин или мак) и тежест.
    Сумата на тежестите трябва да прави 1.
'''
class CriteriaDefinition(BaseModel):
    name: str = Field(..., examples=["цена", "качество"], description="Име на критерий")
    direction: CriteriaDirection
    weight: float = Field(..., description="Колко е важен критерият")

class AlternativeDefinition(BaseModel):
    name: str = Field(..., description="Дефиниция на алтернатива")
    '''
        Пример за values би бил:
        {"price": 200.00, "quality": 10}
        И това е за всяка една алтернатива
    '''
    values: dict[str, float] = Field(...)

class SolveRequest(BaseModel):
    problem_name: str = Field(..., examples="Име на задача")
    criterias: list[CriteriaDefinition] = Field(..., description="Списък от критерии")
    alternatives: list[AlternativeDefinition] = Field(..., description="Списък от алтернативи")

class RankedAlternative(BaseModel):
    rank: int = Field(...)
    name: str = Field(..., description="Име на алтернатива")
    closeness_score: float = Field(..., description="Относителна близот до идеалното решение")
    values: dict[str, float] = Field(..., description="Стойности")

class SolveResponse(BaseModel):
    problem_name: str
    status: str
    rankings: list[RankedAlternative] = Field(..., description="Подредени алтернативи") 