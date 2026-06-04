from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.api.routes import router
from server.core.config import settings

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

app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {
        "message": "Single-Criteria Solver API",
        "docs": "/docs",
    }