from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/ai_content_studio"
    SECRET_KEY: str = ""  # Must be set via .env
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    CORS_ORIGINS: str = "http://localhost"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

if not settings.SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Please configure it in backend/.env")
