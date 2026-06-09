from fastapi import APIRouter, HTTPException
from shared.schemas.optimization import SolveRequest as LinearSolveRequest, SolveResponse as LinearSolverResponse
from shared.schemas.topsis import SolveRequest as TSSolveRequest, SolveResponse as TSSolveResponse
from server.services.pulp_solver import solve as linear_solver
from server.services.topsis_solver import solve as topsis_solver

router = APIRouter()

# Health check endpoint
@router.get("/health")
def health_check():
    return {"status": "ok"}

# TODO: Divide both routes into external router files and include them here

@router.post("/linear-solve", response_model=LinearSolverResponse)
def solve_linear(req: LinearSolveRequest) -> LinearSolverResponse:
    try:
        return linear_solver(req)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@router.post("/solve", response_model=LinearSolverResponse)
def solve(req: LinearSolveRequest) -> LinearSolverResponse:
    try:
        return linear_solver(req)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@router.post("/topsis-solve", response_model=TSSolveResponse)
def solve_topsis(req: TSSolveRequest) -> TSSolveResponse:
    try:
        return topsis_solver(req)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))