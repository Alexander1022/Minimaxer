from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Decision Making System"
    ALLOWED_ORIGINS: list[str] = ["*"]
    API_BASE_URL: str = "http://127.0.0.1:8000/api"

settings = Settings()