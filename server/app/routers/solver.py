from fastapi import APIRouter, HTTPException, status
from shared.schemas.optimization import SolveRequest as LinearSolveRequest, SolveResponse as LinearSolverResponse
from shared.schemas.topsis import SolveRequest as TSSolveRequest, SolveResponse as TSSolveResponse
from app.services.pulp_solver import solve as linear_solver
from app.services.topsis_solver import solve as topsis_solver

router = APIRouter()


@router.post(
    "/solvers/linear",
    response_model=LinearSolverResponse,
    status_code=status.HTTP_200_OK,
)
def solve_linear(req: LinearSolveRequest) -> LinearSolverResponse:
    try:
        return linear_solver(req)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post(
    "/solvers/topsis",
    response_model=TSSolveResponse,
    status_code=status.HTTP_200_OK,
)
def solve_topsis(req: TSSolveRequest) -> TSSolveResponse:
    try:
        return topsis_solver(req)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))