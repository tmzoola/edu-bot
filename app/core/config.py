from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute media root (uploads) — independent of the process working dir.
# Resolves to <repo>/app/media; in Docker a volume is mounted here.
MEDIA_ROOT = Path(__file__).resolve().parent.parent / "media"

# Book upload constraints (shared by the admin tool page and the admin panel).
BOOKS_DIR_NAME = "books"
ALLOWED_BOOK_EXT = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx",
    ".xls", ".xlsx", ".epub", ".djvu", ".txt",
}
MAX_BOOK_SIZE = 100 * 1024 * 1024  # 100 MB


class Settings(BaseSettings):
    APP_MODE: str = "DEV"
    DEBUG: bool = False
    SECRET_KEY: str

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str

    CORS_ALLOWED_ORIGINS: str = "http://localhost:8000"

    BOT_TOKEN: str
    WEBAPP_URL: str = "http://localhost:8000"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        extra="ignore",
    )


settings = Settings()
