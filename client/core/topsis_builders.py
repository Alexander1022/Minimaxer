import math
from shared.schemas.topsis import (
    CriteriaDefinition,
    CriteriaDirection,
    AlternativeDefinition,
    SolveRequest
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
        direction_str = str(row[1]).strip()
        direction = CriteriaDirection.MAXIMIZE
        if direction_str.lower() in ["minimize", "минимизиране", "min", "минимизирай"]:
            direction = CriteriaDirection.MINIMIZE
            
        weight = parse_required_float(row[2], f"Тежест за критерий {name}")
        
        criterias.append(
            CriteriaDefinition(
                name=name,
                direction=direction,
                weight=weight
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
                val = parse_required_float(row[col_index], f"Стойност за {criteria_name} при алтернатива {name}")
                values[criteria_name] = val
            else:
                values[criteria_name] = 0.0
                
        alternatives.append(
            AlternativeDefinition(
                name=name,
                values=values
            )
        )
        
    return alternatives

def build_topsis_request(problem_name, criteria_table, alternatives_table):
    criterias = rows_to_criteria(criteria_table)
    
    if criterias:
        weights_sum = sum(c.weight for c in criterias)
        if not math.isclose(weights_sum, 1.0, rel_tol=1e-5):
            raise ValueError(f"Сумата на тежестите трябва да е 1.0, а в момента е {weights_sum:.4f}")

    alternatives = rows_to_alternatives(alternatives_table, criterias)
    
    return SolveRequest(
        problem_name=problem_name or "TOPSIS_Problem",
        criterias=criterias,
        alternatives=alternatives
    )
