import hashlib
import hmac
import shutil
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from app.config import get_settings

settings = get_settings()


def sign_local_download(storage_key: str, expires_at: int) -> str:
    """HMAC signature for a local-disk "presigned" download URL.

    Mirrors how a real S3 presigned GET works: the URL itself is the
    credential (signature + expiry in the query string), so it can be handed
    to a plain <a href> without an Authorization header.
    """
    message = f"{storage_key}:{expires_at}".encode()
    return hmac.new(settings.JWT_SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()


def verify_local_download_signature(storage_key: str, expires_at: int, signature: str) -> bool:
    if time.time() > expires_at:
        return False
    expected = sign_local_download(storage_key, expires_at)
    return hmac.compare_digest(expected, signature)


@dataclass
class PresignedUpload:
    """What the frontend needs to upload a file directly to the storage backend."""

    upload_url: str
    storage_key: str
    method: str = "PUT"
    fields: dict | None = None  # used by S3 POST-policy uploads; empty for PUT


class StorageBackend(ABC):
    @abstractmethod
    def build_storage_key(self, team_id: int, file_type: str, filename: str) -> str: ...

    @abstractmethod
    def create_presigned_upload(self, storage_key: str, content_type: str) -> PresignedUpload: ...

    @abstractmethod
    def create_presigned_download(self, storage_key: str, filename: str) -> str: ...

    @abstractmethod
    def delete(self, storage_key: str) -> None: ...

    @abstractmethod
    def save_local_upload(self, storage_key: str, source_path: str) -> None:
        """Dev-only escape hatch used by the local backend's own direct-upload route."""
        ...


def _build_key(team_id: int, file_type: str, filename: str) -> str:
    safe_name = Path(filename).name
    return f"teams/{team_id}/{file_type}/{uuid.uuid4().hex}-{safe_name}"


class LocalDiskStorage(StorageBackend):
    """Development stand-in for S3. Mimics the presigned-upload shape so the
    frontend upload flow (and the API contract) is identical to production:
    the browser still PUTs bytes to an "upload_url", it just happens to be a
    same-origin backend route instead of an S3 bucket.
    """

    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def build_storage_key(self, team_id: int, file_type: str, filename: str) -> str:
        return _build_key(team_id, file_type, filename)

    def create_presigned_upload(self, storage_key: str, content_type: str) -> PresignedUpload:
        return PresignedUpload(
            upload_url=f"{settings.API_PREFIX}/uploads/local/{storage_key}",
            storage_key=storage_key,
            method="PUT",
        )

    def create_presigned_download(self, storage_key: str, filename: str) -> str:
        expires_at = int(time.time()) + settings.PRESIGNED_URL_EXPIRE_SECONDS
        signature = sign_local_download(storage_key, expires_at)
        return (
            f"{settings.API_PREFIX}/uploads/local-download/{storage_key}"
            f"?filename={quote(filename)}&expires={expires_at}&sig={signature}"
        )

    def delete(self, storage_key: str) -> None:
        path = self.base_dir / storage_key
        if path.exists():
            path.unlink()

    def save_local_upload(self, storage_key: str, source_path: str) -> None:
        dest = self.base_dir / storage_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source_path, dest)

    def resolve_path(self, storage_key: str) -> Path:
        return self.base_dir / storage_key


class S3Storage(StorageBackend):
    def __init__(self, bucket: str, region: str) -> None:
        import boto3

        self.bucket = bucket
        self.client = boto3.client("s3", region_name=region)

    def build_storage_key(self, team_id: int, file_type: str, filename: str) -> str:
        return _build_key(team_id, file_type, filename)

    def create_presigned_upload(self, storage_key: str, content_type: str) -> PresignedUpload:
        url = self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": storage_key, "ContentType": content_type},
            ExpiresIn=settings.PRESIGNED_URL_EXPIRE_SECONDS,
        )
        return PresignedUpload(upload_url=url, storage_key=storage_key, method="PUT")

    def create_presigned_download(self, storage_key: str, filename: str) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": storage_key,
                "ResponseContentDisposition": f'attachment; filename="{filename}"',
            },
            ExpiresIn=settings.PRESIGNED_URL_EXPIRE_SECONDS,
        )

    def delete(self, storage_key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=storage_key)

    def save_local_upload(self, storage_key: str, source_path: str) -> None:
        raise NotImplementedError("S3Storage expects direct browser-to-S3 uploads.")


_storage_instance: StorageBackend | None = None


def get_storage() -> StorageBackend:
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    if settings.STORAGE_BACKEND == "s3":
        if not settings.S3_BUCKET_NAME:
            raise RuntimeError("S3_BUCKET_NAME must be set when STORAGE_BACKEND=s3")
        _storage_instance = S3Storage(settings.S3_BUCKET_NAME, settings.AWS_REGION)
    else:
        _storage_instance = LocalDiskStorage(settings.LOCAL_STORAGE_DIR)
    return _storage_instance
