"""Tests for blob store implementations."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.core.exceptions import ResourceNotFoundError

from taxonomy_builder.blob_store import (
    AzureBlobStore,
    AzureFrontDoorPurger,
    FilesystemBlobStore,
    NoOpPurger,
    create_blob_store,
    create_cdn_purger,
)
from taxonomy_builder.config import CDNSettings, Settings


class TestFilesystemBlobStore:
    async def test_put_creates_file(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        await store.put("foo/bar.json", b'{"key": "value"}')
        assert (tmp_path / "foo" / "bar.json").read_bytes() == b'{"key": "value"}'

    async def test_put_creates_intermediate_directories(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        await store.put("a/b/c/d.json", b"data")
        assert (tmp_path / "a" / "b" / "c" / "d.json").exists()

    async def test_put_overwrites_existing(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        await store.put("f.json", b"old")
        await store.put("f.json", b"new")
        assert (tmp_path / "f.json").read_bytes() == b"new"

    async def test_exists_true(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        await store.put("x.json", b"data")
        assert await store.exists("x.json") is True

    async def test_exists_false(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        assert await store.exists("missing.json") is False

    async def test_delete_removes_file(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        await store.put("to_delete.json", b"data")
        await store.delete("to_delete.json")
        assert not (tmp_path / "to_delete.json").exists()

    async def test_delete_missing_is_noop(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        await store.delete("nonexistent.json")  # should not raise

    async def test_list_returns_files_under_prefix(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        await store.put("projects/abc/v1/index.json", b"1")
        await store.put("projects/abc/v2/index.json", b"2")
        await store.put("projects/xyz/v1/index.json", b"3")
        result = await store.list("projects/abc")
        assert sorted(result) == [
            "projects/abc/v1/index.json",
            "projects/abc/v2/index.json",
        ]

    async def test_list_empty_prefix(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        assert await store.list("nonexistent") == []

    async def test_path_traversal_rejected(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        with pytest.raises(ValueError, match="Path escapes root"):
            await store.put("../../etc/passwd", b"evil")

    async def test_path_traversal_rejected_on_delete(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        with pytest.raises(ValueError, match="Path escapes root"):
            await store.delete("../outside")

    async def test_path_traversal_rejected_on_exists(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        with pytest.raises(ValueError, match="Path escapes root"):
            await store.exists("../outside")

    async def test_path_traversal_rejected_on_list(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        with pytest.raises(ValueError, match="Path escapes root"):
            await store.list("../outside")


async def _async_iter(items):
    """Helper to create an async iterable from a list."""
    for item in items:
        yield item


@patch("taxonomy_builder.blob_store.DefaultAzureCredential")
@patch("taxonomy_builder.blob_store.BlobServiceClient")
class TestAzureBlobStore:
    def _make_store(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> tuple[AzureBlobStore, MagicMock]:
        container = MagicMock()
        container.upload_blob = AsyncMock()
        blob_client = AsyncMock()
        container.get_blob_client.return_value = blob_client
        mock_client_cls.return_value.get_container_client.return_value = container
        store = AzureBlobStore("https://acct.blob.core.windows.net", "published")
        return store, container

    async def test_put_uploads_blob(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        store, container = self._make_store(mock_client_cls, mock_cred)
        await store.put("path/to/file.json", b'{"data": true}', "application/json")

        container.upload_blob.assert_called_once()
        kwargs = container.upload_blob.call_args.kwargs
        assert kwargs["name"] == "path/to/file.json"
        assert kwargs["data"] == b'{"data": true}'
        assert kwargs["overwrite"] is True

    async def test_put_sets_content_type(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        store, container = self._make_store(mock_client_cls, mock_cred)
        await store.put("file.xml", b"<xml/>", "application/xml")

        content_settings = container.upload_blob.call_args.kwargs["content_settings"]
        assert content_settings.content_type == "application/xml"

    async def test_delete_calls_delete_blob(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        store, container = self._make_store(mock_client_cls, mock_cred)
        await store.delete("path/to/file.json")

        container.get_blob_client.assert_called_once_with("path/to/file.json")
        container.get_blob_client.return_value.delete_blob.assert_called_once()

    async def test_delete_missing_is_noop(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        store, container = self._make_store(mock_client_cls, mock_cred)
        container.get_blob_client.return_value.delete_blob.side_effect = (
            ResourceNotFoundError("not found")
        )
        await store.delete("missing.json")  # should not raise

    async def test_exists_true(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        store, container = self._make_store(mock_client_cls, mock_cred)
        assert await store.exists("file.json") is True
        container.get_blob_client.return_value.get_blob_properties.assert_called_once()

    async def test_exists_false_on_missing(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        store, container = self._make_store(mock_client_cls, mock_cred)
        container.get_blob_client.return_value.get_blob_properties.side_effect = (
            ResourceNotFoundError("not found")
        )
        assert await store.exists("missing.json") is False

    async def test_list_returns_blob_names(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        store, container = self._make_store(mock_client_cls, mock_cred)
        blob1 = MagicMock()
        blob1.name = "prefix/a.json"
        blob2 = MagicMock()
        blob2.name = "prefix/b.json"
        container.list_blobs.return_value = _async_iter([blob1, blob2])

        result = await store.list("prefix/")
        assert result == ["prefix/a.json", "prefix/b.json"]
        container.list_blobs.assert_called_once_with(name_starts_with="prefix/")


class TestCreateBlobStore:
    def test_creates_filesystem_store(self, tmp_path: Path) -> None:
        settings = Settings(
            blob_backend="filesystem",
            blob_filesystem_root=str(tmp_path),
        )
        store = create_blob_store(settings)
        assert isinstance(store, FilesystemBlobStore)

    @patch("taxonomy_builder.blob_store.DefaultAzureCredential")
    @patch("taxonomy_builder.blob_store.BlobServiceClient")
    def test_creates_azure_store(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        settings = Settings(
            blob_backend="azure",
            blob_azure_account_url="https://acct.blob.core.windows.net",
            blob_azure_container="published",
        )
        store = create_blob_store(settings)
        assert isinstance(store, AzureBlobStore)

    def test_rejects_unknown_backend(self) -> None:
        settings = Settings(blob_backend="s3")
        with pytest.raises(ValueError, match="Unknown blob_backend"):
            create_blob_store(settings)

    def test_azure_requires_account_url(self) -> None:
        settings = Settings(blob_backend="azure", blob_azure_account_url=None)
        with pytest.raises(ValueError, match="TAXONOMY_BLOB_AZURE_ACCOUNT_URL"):
            create_blob_store(settings)


@patch("taxonomy_builder.blob_store.DefaultAzureCredential")
@patch("taxonomy_builder.blob_store.CdnManagementClient")
class TestAzureFrontDoorPurger:
    async def test_purge_calls_begin_purge_content(
        self, mock_cdn_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        mock_cdn_cls.return_value.afd_endpoints.begin_purge_content = AsyncMock()
        purger = AzureFrontDoorPurger(
            subscription_id="sub-123",
            resource_group="rg-test",
            profile_name="fd-test",
            endpoint_name="fde-test",
        )
        await purger.purge(["/published/abc/latest/*", "/published/abc/index.json"])

        mock_cdn_cls.return_value.afd_endpoints.begin_purge_content.assert_called_once()
        call_kwargs = (
            mock_cdn_cls.return_value.afd_endpoints.begin_purge_content.call_args.kwargs
        )
        assert call_kwargs["resource_group_name"] == "rg-test"
        assert call_kwargs["profile_name"] == "fd-test"
        assert call_kwargs["endpoint_name"] == "fde-test"

    async def test_purge_passes_correct_paths(
        self, mock_cdn_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        mock_cdn_cls.return_value.afd_endpoints.begin_purge_content = AsyncMock()
        purger = AzureFrontDoorPurger(
            subscription_id="sub-123",
            resource_group="rg-test",
            profile_name="fd-test",
            endpoint_name="fde-test",
        )
        await purger.purge(["/published/abc/latest/*"])

        contents = (
            mock_cdn_cls.return_value.afd_endpoints.begin_purge_content.call_args.kwargs[
                "contents"
            ]
        )
        assert contents.content_paths == ["/published/abc/latest/*"]

    async def test_purge_logs_on_failure(
        self, mock_cdn_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        mock_cdn_cls.return_value.afd_endpoints.begin_purge_content = AsyncMock(
            side_effect=Exception("auth failed")
        )
        purger = AzureFrontDoorPurger(
            subscription_id="sub-123",
            resource_group="rg-test",
            profile_name="fd-test",
            endpoint_name="fde-test",
        )
        # Should not raise — errors are logged, not propagated
        await purger.purge(["/some/path"])

    async def test_purge_prepends_path_prefix(
        self, mock_cdn_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        mock_cdn_cls.return_value.afd_endpoints.begin_purge_content = AsyncMock()
        purger = AzureFrontDoorPurger(
            subscription_id="sub-123",
            resource_group="rg-test",
            profile_name="fd-test",
            endpoint_name="fde-test",
            path_prefix="/published",
        )
        await purger.purge(["/abc/index.json", "/index.json"])

        contents = (
            mock_cdn_cls.return_value.afd_endpoints.begin_purge_content.call_args.kwargs[
                "contents"
            ]
        )
        assert contents.content_paths == [
            "/published/abc/index.json",
            "/published/index.json",
        ]


class TestNoOpPurger:
    async def test_purge_does_nothing(self) -> None:
        purger = NoOpPurger()
        await purger.purge(["/published/abc/latest/*"])  # should not raise


class TestCreateCdnPurger:
    def test_returns_noop_when_cdn_is_none(self) -> None:
        purger = create_cdn_purger(None)
        assert isinstance(purger, NoOpPurger)

    @patch("taxonomy_builder.blob_store.DefaultAzureCredential")
    @patch("taxonomy_builder.blob_store.CdnManagementClient")
    def test_returns_azure_purger_when_cdn_settings_present(
        self, mock_cdn_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        purger = create_cdn_purger(
            CDNSettings(
                subscription_id="sub-123",
                resource_group="rg-test",
                profile_name="fd-test",
                endpoint_name="fde-test",
            )
        )
        assert isinstance(purger, AzureFrontDoorPurger)
