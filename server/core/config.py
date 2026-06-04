from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Decision Making System"
    ALLOWED_ORIGINS: list[str] = ["*"]

settings = Settings()