from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "ADAPPT"
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api"
    FRONTEND_URL: str = "http://localhost:5173"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://localhost/adappt"

    # Auth
    JWT_SECRET_KEY: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ACTIVATION_TOKEN_EXPIRE_HOURS: int = 24

    # Storage
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    LOCAL_STORAGE_DIR: str = "./uploads"
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET_NAME: str | None = None
    PRESIGNED_URL_EXPIRE_SECONDS: int = 3600

    # Email
    EMAIL_BACKEND: Literal["console", "smtp"] = "console"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAIL_FROM_ADDRESS: str = "noreply@adappt.dev"
    EMAIL_FROM_NAME: str = "ADAPPT"

    # Google Forms / Sheets integration
    REGISTRATION_SYNC_MODE: Literal["csv", "google_sheets"] = "csv"
    GOOGLE_SERVICE_ACCOUNT_JSON: str | None = None
    GOOGLE_SHEET_ID: str | None = None
    GOOGLE_SHEET_WORKSHEET: str = "Form Responses 1"
    REGISTRATION_CSV_PATH: str = "./dev_data/registrations.csv"
    GOOGLE_FORM_URL: str = "https://forms.google.com/PLACEHOLDER"

    # Uploads
    MAX_DOCUMENT_SIZE_MB: int = 25
    MAX_VIDEO_SIZE_MB: int = 300
    ALLOWED_DOCUMENT_EXTENSIONS: str = "pdf,ppt,pptx"
    ALLOWED_VIDEO_EXTENSIONS: str = "mp4,mov,webm"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_document_extensions_list(self) -> list[str]:
        return [e.strip().lower() for e in self.ALLOWED_DOCUMENT_EXTENSIONS.split(",")]

    @property
    def allowed_video_extensions_list(self) -> list[str]:
        return [e.strip().lower() for e in self.ALLOWED_VIDEO_EXTENSIONS.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
