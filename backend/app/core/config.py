from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PlacementOS"
    environment: str = "development"
    database_url: str = "sqlite:///./placementos.db"
    cors_origins: list[str] = ["http://localhost:5173"]
    jwt_secret: str = "local-development-secret-change-before-deploy"
    access_token_minutes: int = 60
    judge0_base_url: str = ""
    judge0_api_key: str = ""
    judge0_secure_deployment_confirmed: bool = False
    judge0_python_language_id: int = 71
    max_submissions_per_minute: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def validate_production(self) -> None:
        if self.environment.lower() == "production":
            if self.jwt_secret == "local-development-secret-change-before-deploy":
                raise RuntimeError("Set a unique JWT_SECRET before production startup.")
            if not self.cors_origins:
                raise RuntimeError("Configure explicit CORS_ORIGINS for production.")


settings = Settings()
settings.validate_production()
