"""Saari settings yahan se aati hain. Values .env file ya environment variables se override hoti hain."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "CodeClash"
    DATABASE_URL: str = "postgresql+asyncpg://codeclash:codeclash@localhost:5432/codeclash"
    REDIS_URL: str = "redis://localhost:6379/0"

    # ⚠️ Production mein isko lamba random string banao:  python -c "import secrets;print(secrets.token_hex(32))"
    JWT_SECRET: str = "dev-secret-change-me-before-deploying-0000"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 din

    BATTLE_DURATION_SECONDS: int = 15 * 60
    MAX_CODE_LENGTH: int = 50_000
    SUBMIT_COOLDOWN_SECONDS: int = 3  # spam submissions rokne ke liye

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
