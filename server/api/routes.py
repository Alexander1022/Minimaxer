from fastapi import APIRouter, HTTPException, status
from schemas.optimization import SolveRequest, SolveResponse

router = APIRouter()

# Health check endpoint
@router.get("/health")
def health_check():
    return {"status": "ok"}

# Optimization endpoint - tbd
@router.post("/solve")
def solve_problem():
    return {"message": "Solve solve solve"}