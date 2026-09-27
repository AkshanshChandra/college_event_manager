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

    # Registration: the portal has its own native registration form (source
    # of truth). REGISTRATION_SYNC_MODE/CSV settings remain for optional
    # bulk-import tooling; GOOGLE_SHEET_ID is also used as the destination
    # when admins push registrations out to a Google Sheet for visibility.
    REGISTRATION_SYNC_MODE: Literal["csv", "google_sheets"] = "csv"
    GOOGLE_SERVICE_ACCOUNT_JSON: str | None = None
    GOOGLE_SHEET_ID: str | None = None
    GOOGLE_SHEET_WORKSHEET: str = "Registrations"
    REGISTRATION_CSV_PATH: str = "./dev_data/registrations.csv"
    PAYMENT_PER_PERSON_INR: int = 300
    PAYMENT_SCREENSHOT_MAX_SIZE_MB: int = 10
    PAYMENT_SCREENSHOT_ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,webp,pdf"

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

    @property
    def payment_screenshot_allowed_extensions_list(self) -> list[str]:
        return [e.strip().lower() for e in self.PAYMENT_SCREENSHOT_ALLOWED_EXTENSIONS.split(",")]


DEV_JWT_SECRET_DEFAULT = "dev-secret-change-me"


def assert_production_safety(settings: Settings) -> None:
    """Refuse to boot with unsafe defaults in production. Cheap insurance
    against the classic "forgot to set env vars on the new server" mistake —
    these specific defaults are severe enough (forgeable JWTs, leaked stack
    traces) that failing loudly beats logging a warning nobody reads.
    """
    if settings.ENVIRONMENT != "production":
        return

    errors = []
    if settings.JWT_SECRET_KEY == DEV_JWT_SECRET_DEFAULT:
        errors.append("JWT_SECRET_KEY is still the dev default — set a long random secret.")
    if settings.DEBUG:
        errors.append("DEBUG=true in production leaks stack traces — set DEBUG=false.")
    if settings.STORAGE_BACKEND == "local":
        errors.append(
            "STORAGE_BACKEND=local in production stores uploads on the app server's disk, "
            "which is lost on redeploy — set STORAGE_BACKEND=s3 with real AWS credentials."
        )
    if settings.EMAIL_BACKEND == "console":
        errors.append(
            "EMAIL_BACKEND=console in production means activation/confirmation emails are "
            "only logged, never sent — set EMAIL_BACKEND=smtp with real credentials."
        )

    if errors:
        raise RuntimeError(
            "Refusing to start with unsafe production configuration:\n- "
            + "\n- ".join(errors)
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
