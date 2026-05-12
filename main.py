from fastapi import FastAPI, HTTPException

from models import SolveRequest, SolveResponse
from solver import solve

app = FastAPI(title="Linear Programming Solver")


@app.post("/solve", response_model=SolveResponse)
def solve_endpoint(req: SolveRequest) -> SolveResponse:
    try:
        return solve(req)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))