"""Tests for blob store implementations."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from azure.core.exceptions import ResourceNotFoundError

from taxonomy_builder.blob_store import AzureBlobStore, FilesystemBlobStore, create_blob_store
from taxonomy_builder.config import Settings


class TestFilesystemBlobStore:
    def test_put_creates_file(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        store.put("foo/bar.json", b'{"key": "value"}')
        assert (tmp_path / "foo" / "bar.json").read_bytes() == b'{"key": "value"}'

    def test_put_creates_intermediate_directories(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        store.put("a/b/c/d.json", b"data")
        assert (tmp_path / "a" / "b" / "c" / "d.json").exists()

    def test_put_overwrites_existing(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        store.put("f.json", b"old")
        store.put("f.json", b"new")
        assert (tmp_path / "f.json").read_bytes() == b"new"

    def test_exists_true(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        store.put("x.json", b"data")
        assert store.exists("x.json") is True

    def test_exists_false(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        assert store.exists("missing.json") is False

    def test_delete_removes_file(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        store.put("to_delete.json", b"data")
        store.delete("to_delete.json")
        assert not (tmp_path / "to_delete.json").exists()

    def test_delete_missing_is_noop(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        store.delete("nonexistent.json")  # should not raise

    def test_list_returns_files_under_prefix(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        store.put("projects/abc/v1/index.json", b"1")
        store.put("projects/abc/v2/index.json", b"2")
        store.put("projects/xyz/v1/index.json", b"3")
        result = store.list("projects/abc")
        assert sorted(result) == [
            "projects/abc/v1/index.json",
            "projects/abc/v2/index.json",
        ]

    def test_list_empty_prefix(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        assert store.list("nonexistent") == []

    def test_path_traversal_rejected(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        with pytest.raises(ValueError, match="Path escapes root"):
            store.put("../../etc/passwd", b"evil")

    def test_path_traversal_rejected_on_delete(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        with pytest.raises(ValueError, match="Path escapes root"):
            store.delete("../outside")

    def test_path_traversal_rejected_on_exists(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        with pytest.raises(ValueError, match="Path escapes root"):
            store.exists("../outside")

    def test_path_traversal_rejected_on_list(self, tmp_path: Path) -> None:
        store = FilesystemBlobStore(root=tmp_path)
        with pytest.raises(ValueError, match="Path escapes root"):
            store.list("../outside")


@patch("taxonomy_builder.blob_store.DefaultAzureCredential")
@patch("taxonomy_builder.blob_store.BlobServiceClient")
class TestAzureBlobStore:
    def _make_store(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> tuple[AzureBlobStore, MagicMock]:
        container = MagicMock()
        mock_client_cls.return_value.get_container_client.return_value = container
        store = AzureBlobStore("https://acct.blob.core.windows.net", "published")
        return store, container

    def test_put_uploads_blob(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        store, container = self._make_store(mock_client_cls, mock_cred)
        store.put("path/to/file.json", b'{"data": true}', "application/json")

        container.upload_blob.assert_called_once()
        kwargs = container.upload_blob.call_args.kwargs
        assert kwargs["name"] == "path/to/file.json"
        assert kwargs["data"] == b'{"data": true}'
        assert kwargs["overwrite"] is True

    def test_put_sets_content_type(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        store, container = self._make_store(mock_client_cls, mock_cred)
        store.put("file.xml", b"<xml/>", "application/xml")

        content_settings = container.upload_blob.call_args.kwargs["content_settings"]
        assert content_settings.content_type == "application/xml"

    def test_delete_calls_delete_blob(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        store, container = self._make_store(mock_client_cls, mock_cred)
        store.delete("path/to/file.json")

        container.get_blob_client.assert_called_once_with("path/to/file.json")
        container.get_blob_client.return_value.delete_blob.assert_called_once()

    def test_delete_missing_is_noop(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        store, container = self._make_store(mock_client_cls, mock_cred)
        container.get_blob_client.return_value.delete_blob.side_effect = (
            ResourceNotFoundError("not found")
        )
        store.delete("missing.json")  # should not raise

    def test_exists_true(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        store, container = self._make_store(mock_client_cls, mock_cred)
        assert store.exists("file.json") is True
        container.get_blob_client.return_value.get_blob_properties.assert_called_once()

    def test_exists_false_on_missing(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        store, container = self._make_store(mock_client_cls, mock_cred)
        container.get_blob_client.return_value.get_blob_properties.side_effect = (
            ResourceNotFoundError("not found")
        )
        assert store.exists("missing.json") is False

    def test_list_returns_blob_names(
        self, mock_client_cls: MagicMock, mock_cred: MagicMock
    ) -> None:
        store, container = self._make_store(mock_client_cls, mock_cred)
        blob1 = MagicMock()
        blob1.name = "prefix/a.json"
        blob2 = MagicMock()
        blob2.name = "prefix/b.json"
        container.list_blobs.return_value = [blob1, blob2]

        result = store.list("prefix/")
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
