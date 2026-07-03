from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = ""  # Must be set via environment variable
    SECRET_KEY: str = ""  # Must be set via .env
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    CORS_ORIGINS: str = "http://localhost"
    DEEPSEEK_API_KEY: str = ""

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL must be set via environment variable")
        return v


settings = Settings()

if not settings.SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Please configure it in backend/.env")
if len(settings.SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY must be at least 32 characters")
