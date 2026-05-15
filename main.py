from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from schemas import SolveRequest, SolveResponse
from solver import solve

app = FastAPI(
    title=settings.APP_NAME,
    description="API Server for Minimaxer, a single-criteria decision-making tool.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/solve", response_model=SolveResponse)
def solve_endpoint(req: SolveRequest) -> SolveResponse:
    try:
        return solve(req)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))