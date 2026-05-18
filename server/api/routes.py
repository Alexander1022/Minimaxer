from fastapi import APIRouter, HTTPException
from shared.schemas.optimization import SolveRequest, SolveResponse
from server.services.pulp_solver import solve

router = APIRouter()

# Health check endpoint
@router.get("/health")
def health_check():
    return {"status": "ok"}

# Optimization endpoint - tbd
@router.post("/solve", response_model=SolveResponse)
def solve_problem(req: SolveRequest) -> SolveResponse:
    try:
        return solve(req)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
