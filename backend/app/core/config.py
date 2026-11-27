from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PlacementOS"
    environment: str = "development"
    database_url: str = "sqlite:///./placementos.db"
    judge0_base_url: str = ""
    judge0_api_key: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
