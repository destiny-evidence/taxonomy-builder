"""Blob storage abstraction for publishing taxonomy snapshots.

Write-only interface — reads happen at the CDN/reverse-proxy layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings

if TYPE_CHECKING:
    from taxonomy_builder.config import Settings


@runtime_checkable
class BlobStore(Protocol):
    """Write-side interface for blob storage."""

    def put(self, path: str, data: bytes, content_type: str = "application/json") -> None:
        """Write data to the given path, overwriting if it exists."""
        ...

    def delete(self, path: str) -> None:
        """Delete the blob at the given path. No-op if it doesn't exist."""
        ...

    def exists(self, path: str) -> bool:
        """Check whether a blob exists at the given path."""
        ...

    def list(self, prefix: str) -> list[str]:
        """List all blob paths matching the given prefix."""
        ...


class FilesystemBlobStore:
    """Blob store backed by the local filesystem."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def _resolve(self, path: str) -> Path:
        full = (self._root / path).resolve()
        if not full.is_relative_to(self._root):
            raise ValueError(f"Path escapes root: {path}")
        return full

    def put(self, path: str, data: bytes, content_type: str = "application/json") -> None:
        full = self._resolve(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(data)

    def delete(self, path: str) -> None:
        self._resolve(path).unlink(missing_ok=True)

    def exists(self, path: str) -> bool:
        return self._resolve(path).is_file()

    def list(self, prefix: str) -> list[str]:
        base = self._resolve(prefix)
        if base.is_dir():
            return sorted(
                str(p.relative_to(self._root))
                for p in base.rglob("*")
                if p.is_file()
            )
        # Partial prefix — glob in parent directory
        if not base.parent.exists():
            return []
        return sorted(
            str(p.relative_to(self._root))
            for p in base.parent.glob(f"{base.name}*")
            if p.is_file()
        )


class AzureBlobStore:
    """Blob store backed by Azure Blob Storage."""

    def __init__(self, account_url: str, container_name: str) -> None:
        credential = DefaultAzureCredential()
        client = BlobServiceClient(account_url, credential=credential)
        self._container = client.get_container_client(container_name)

    def put(self, path: str, data: bytes, content_type: str = "application/json") -> None:
        self._container.upload_blob(
            name=path,
            data=data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )

    def delete(self, path: str) -> None:
        try:
            self._container.get_blob_client(path).delete_blob()
        except ResourceNotFoundError:
            pass

    def exists(self, path: str) -> bool:
        try:
            self._container.get_blob_client(path).get_blob_properties()
            return True
        except ResourceNotFoundError:
            return False

    def list(self, prefix: str) -> list[str]:
        return [b.name for b in self._container.list_blobs(name_starts_with=prefix)]


_blob_store: BlobStore | None = None


def init_blob_store(settings: Settings) -> None:
    global _blob_store
    _blob_store = create_blob_store(settings)


def get_blob_store() -> BlobStore:
    if _blob_store is None:
        raise RuntimeError("Blob store not initialized")
    return _blob_store


def create_blob_store(settings: Settings) -> BlobStore:
    if settings.blob_backend == "filesystem":
        return FilesystemBlobStore(root=Path(settings.blob_filesystem_root))
    elif settings.blob_backend == "azure":
        if not settings.blob_azure_account_url:
            raise ValueError("TAXONOMY_BLOB_AZURE_ACCOUNT_URL required when blob_backend=azure")
        return AzureBlobStore(
            account_url=settings.blob_azure_account_url,
            container_name=settings.blob_azure_container,
        )
    else:
        raise ValueError(f"Unknown blob_backend: {settings.blob_backend}")
