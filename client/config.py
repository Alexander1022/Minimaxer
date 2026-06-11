from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # In Docker Compose the server is reachable at `http://server:8000/api`.
    # Locally (no Docker) the default works because both processes run on the host.
    API_BASE_URL: str = "http://127.0.0.1:8000/api"


settings = Settings()
