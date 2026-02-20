"""Blob storage abstraction for publishing taxonomy snapshots.

Write-only interface — reads happen at the CDN/reverse-proxy layer.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from azure.core.exceptions import ResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential
from azure.mgmt.cdn.aio import CdnManagementClient
from azure.mgmt.cdn.models import AfdPurgeParameters
from azure.storage.blob import ContentSettings
from azure.storage.blob.aio import BlobServiceClient

if TYPE_CHECKING:
    from taxonomy_builder.config import CDNSettings, Settings


@runtime_checkable
class BlobStore(Protocol):
    """Write-side interface for blob storage."""

    async def put(self, path: str, data: bytes, content_type: str = "application/json") -> None:
        """Write data to the given path, overwriting if it exists."""
        ...

    async def delete(self, path: str) -> None:
        """Delete the blob at the given path. No-op if it doesn't exist."""
        ...

    async def exists(self, path: str) -> bool:
        """Check whether a blob exists at the given path."""
        ...

    async def list(self, prefix: str) -> list[str]:
        """List all blob paths matching the given prefix."""
        ...

    async def close(self) -> None:
        """Release underlying resources."""
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

    async def put(self, path: str, data: bytes, content_type: str = "application/json") -> None:
        full = self._resolve(path)
        await asyncio.to_thread(self._sync_put, full, data)

    @staticmethod
    def _sync_put(full: Path, data: bytes) -> None:
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(data)

    async def delete(self, path: str) -> None:
        await asyncio.to_thread(self._resolve(path).unlink, True)

    async def exists(self, path: str) -> bool:
        return await asyncio.to_thread(self._resolve(path).is_file)

    async def list(self, prefix: str) -> list[str]:
        return await asyncio.to_thread(self._sync_list, prefix)

    def _sync_list(self, prefix: str) -> list[str]:
        base = self._resolve(prefix)
        if base.is_dir():
            return sorted(
                str(p.relative_to(self._root))
                for p in base.rglob("*")
                if p.is_file()
            )
        if not base.parent.exists():
            return []
        return sorted(
            str(p.relative_to(self._root))
            for p in base.parent.glob(f"{base.name}*")
            if p.is_file()
        )

    async def close(self) -> None:
        pass


class AzureBlobStore:
    """Blob store backed by Azure Blob Storage."""

    def __init__(self, account_url: str, container_name: str) -> None:
        self._credential = DefaultAzureCredential()
        self._client = BlobServiceClient(account_url, credential=self._credential)
        self._container = self._client.get_container_client(container_name)

    async def put(self, path: str, data: bytes, content_type: str = "application/json") -> None:
        await self._container.upload_blob(
            name=path,
            data=data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )

    async def delete(self, path: str) -> None:
        try:
            await self._container.get_blob_client(path).delete_blob()
        except ResourceNotFoundError:
            pass

    async def exists(self, path: str) -> bool:
        try:
            await self._container.get_blob_client(path).get_blob_properties()
            return True
        except ResourceNotFoundError:
            return False

    async def list(self, prefix: str) -> list[str]:
        return [b.name async for b in self._container.list_blobs(name_starts_with=prefix)]

    async def close(self) -> None:
        await self._client.close()
        await self._credential.close()


@runtime_checkable
class CdnPurger(Protocol):
    """Interface for purging CDN-cached paths."""

    async def purge(self, paths: list[str]) -> None:
        """Purge the given paths from the CDN cache."""
        ...

    async def close(self) -> None:
        """Release underlying resources."""
        ...


class AzureFrontDoorPurger:
    """Purges paths from Azure Front Door cache."""

    def __init__(
        self,
        subscription_id: str,
        resource_group: str,
        profile_name: str,
        endpoint_name: str,
    ) -> None:
        self._credential = DefaultAzureCredential()
        self._client = CdnManagementClient(self._credential, subscription_id)
        self._resource_group = resource_group
        self._profile_name = profile_name
        self._endpoint_name = endpoint_name

    async def purge(self, paths: list[str]) -> None:
        poller = await self._client.afd_endpoints.begin_purge_content(
            resource_group_name=self._resource_group,
            profile_name=self._profile_name,
            endpoint_name=self._endpoint_name,
            contents=AfdPurgeParameters(content_paths=paths),
        )
        await poller.wait()

    async def close(self) -> None:
        await self._client.close()
        await self._credential.close()


class NoOpPurger:
    """No-op purger for local dev (Caddy doesn't cache)."""

    async def purge(self, paths: list[str]) -> None:
        pass

    async def close(self) -> None:
        pass


_blob_store: BlobStore | None = None


def init_blob_store(settings: Settings) -> None:
    global _blob_store
    _blob_store = create_blob_store(settings)


def get_blob_store() -> BlobStore:
    if _blob_store is None:
        raise RuntimeError("Blob store not initialized")
    return _blob_store


async def close_blob_store() -> None:
    global _blob_store
    if _blob_store is not None:
        await _blob_store.close()
    _blob_store = None


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


_cdn_purger: CdnPurger | None = None


def init_cdn_purger(settings: Settings) -> None:
    global _cdn_purger
    cdn = settings.cdn if settings.blob_backend == "azure" else None
    _cdn_purger = create_cdn_purger(cdn)


def get_cdn_purger() -> CdnPurger:
    if _cdn_purger is None:
        raise RuntimeError("CDN purger not initialized")
    return _cdn_purger


async def close_cdn_purger() -> None:
    global _cdn_purger
    if _cdn_purger is not None:
        await _cdn_purger.close()
    _cdn_purger = None


def create_cdn_purger(cdn: CDNSettings | None) -> CdnPurger:
    if cdn is not None:
        return AzureFrontDoorPurger(
            subscription_id=cdn.subscription_id,
            resource_group=cdn.resource_group,
            profile_name=cdn.profile_name,
            endpoint_name=cdn.endpoint_name,
        )
    return NoOpPurger()
