from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import solver
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lifespan events can be added here
    yield

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="API Server for Minimaxer, a single-criteria decision-making tool.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(solver.router, prefix="/api", tags=["solver"])

    @app.get("/api/health", tags=["health"])
    def health_check():
        return {"status": "ok"}

    @app.get("/")
    def root():
        return {
            "message": "Minimaxer API",
            "docs": "/docs",
        }

    return app

app = create_app()