import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_name: str
    db_user: str
    db_password: str
    db_host: str = "database"
    db_port: int = 5432
    secret_key: str
    admin_email: str
    admin_password: str
    algorithm: str = "HS256"
    access_token_minutes: int = 480

    model_config = SettingsConfigDict(
        env_prefix="DELIVERY_",
        env_file=".env",
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url.replace("postgres://", "postgresql://", 1)
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def environment(self) -> str:
        return os.getenv("ENVIRONMENT", "development")

    @property
    def debug(self) -> bool:
        return os.getenv("DEBUG", "false").lower() == "true"

    @property
    def allowed_origins(self) -> list[str]:
        origins = os.getenv("ALLOWED_ORIGINS", "")
        return [origin.strip() for origin in origins.split(",") if origin.strip()]


settings = Settings()
