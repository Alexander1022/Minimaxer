from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Single-Criteria Solver API"
    ALLOWED_ORIGINS: list[str] = ["*"]

settings = Settings()