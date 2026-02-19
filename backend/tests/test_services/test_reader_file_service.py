"""Tests for reader file rendering and publish_reader_files orchestration."""

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import jsonschema
import pytest

from taxonomy_builder.blob_store import FilesystemBlobStore, NoOpPurger
from taxonomy_builder.schemas.snapshot import SnapshotVocabulary
from taxonomy_builder.services.reader_file_service import ReaderFileService

# ---------------------------------------------------------------------------
# JSON schema loading for validation
# ---------------------------------------------------------------------------

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "docs" / "published-format"


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text())


VOCABULARY_SCHEMA = _load_schema("vocabulary.schema.json")
PROJECT_INDEX_SCHEMA = _load_schema("project-index.schema.json")
ROOT_INDEX_SCHEMA = _load_schema("root-index.schema.json")

# ---------------------------------------------------------------------------
# Test helpers – lightweight stand-ins for ORM objects
# ---------------------------------------------------------------------------

PROJECT_ID = UUID("01965a00-0000-7000-8000-000000000000")
SCHEME_ID = UUID("01965a00-0000-7000-8000-000000000001")
CONCEPT_A_ID = UUID("01965a00-0000-7000-8000-000000000002")
CONCEPT_B_ID = UUID("01965a00-0000-7000-8000-000000000003")
CONCEPT_CHILD_ID = UUID("01965a00-0000-7000-8000-000000000004")
CLASS_ID = UUID("01965a00-0000-7000-8000-b00000000001")
PROPERTY_ID = UUID("01965a00-0000-7000-8000-a00000000001")
VERSION_ID = UUID("01965a00-0000-7000-8000-f00000000001")


def _make_snapshot(
    *,
    concepts=None,
    properties=None,
    classes=None,
):
    """Build a snapshot dict matching SnapshotVocabulary serialised format."""
    if concepts is None:
        concepts = [
            {
                "id": str(CONCEPT_A_ID),
                "pref_label": "Red",
                "identifier": "red",
                "uri": "http://example.org/colors/red",
                "definition": None,
                "scope_note": None,
                "alt_labels": ["Crimson"],
                "broader_ids": [],
                "related_ids": [str(CONCEPT_B_ID)],
            },
            {
                "id": str(CONCEPT_B_ID),
                "pref_label": "Blue",
                "identifier": "blue",
                "uri": "http://example.org/colors/blue",
                "definition": "A cool color.",
                "scope_note": None,
                "alt_labels": [],
                "broader_ids": [],
                "related_ids": [str(CONCEPT_A_ID)],
            },
            {
                "id": str(CONCEPT_CHILD_ID),
                "pref_label": "Sky Blue",
                "identifier": "sky-blue",
                "uri": "http://example.org/colors/sky-blue",
                "definition": None,
                "scope_note": None,
                "alt_labels": [],
                "broader_ids": [str(CONCEPT_B_ID)],
                "related_ids": [],
            },
        ]
    if properties is None:
        properties = [
            {
                "id": str(PROPERTY_ID),
                "identifier": "riskColor",
                "uri": "http://example.org/riskColor",
                "label": "Risk Color",
                "description": "Color for risk.",
                "domain_class": "http://example.org/Finding",
                "range_scheme_id": str(SCHEME_ID),
                "range_scheme_uri": "http://example.org/colors",
                "range_datatype": None,
                "cardinality": "single",
                "required": False,
            }
        ]
    if classes is None:
        classes = [
            {
                "id": str(CLASS_ID),
                "identifier": "Finding",
                "uri": "http://example.org/Finding",
                "label": "Finding",
                "description": "A finding.",
                "scope_note": None,
            }
        ]
    return {
        "project": {
            "id": str(PROJECT_ID),
            "name": "Demo Taxonomy",
            "description": "A demo.",
            "namespace": "http://example.org/taxonomies/demo",
        },
        "concept_schemes": [
            {
                "id": str(SCHEME_ID),
                "title": "Colors",
                "description": "Color vocab.",
                "uri": "http://example.org/colors",
                "concepts": concepts,
            }
        ],
        "properties": properties,
        "classes": classes,
    }


def _make_version(
    *,
    version="1.0",
    title="Initial release",
    finalized=True,
    published_at=None,
    publisher="Jane Smith",
    notes=None,
    snapshot=None,
    project_id=PROJECT_ID,
    id=VERSION_ID,
):
    """Build a lightweight stand-in for PublishedVersion."""
    snap = snapshot or _make_snapshot()
    return SimpleNamespace(
        id=id,
        project_id=project_id,
        version=version,
        title=title,
        finalized=finalized,
        published_at=published_at or datetime(2026, 2, 1, 9, 0, 0, tzinfo=UTC),
        publisher=publisher,
        notes=notes,
        snapshot=snap,
        snapshot_vocabulary=SnapshotVocabulary.model_validate(snap),
    )


def _make_project(*, id=PROJECT_ID, name="Demo Taxonomy", description="A demo.", namespace="http://example.org/taxonomies/demo"):
    return SimpleNamespace(id=id, name=name, description=description, namespace=namespace)


# ===================================================================
# render_vocabulary
# ===================================================================


class TestRenderVocabulary:
    def test_format_version(self):
        version = _make_version()
        result = json.loads(ReaderFileService.render_vocabulary(version))
        assert result["format_version"] == "1.0"

    def test_version_metadata(self):
        version = _make_version(
            version="2.0",
            title="Second release",
            publisher="Bob",
            finalized=True,
            published_at=datetime(2026, 3, 1, 9, 0, 0, tzinfo=UTC),
        )
        result = json.loads(ReaderFileService.render_vocabulary(version))
        assert result["version"] == "2.0"
        assert result["title"] == "Second release"
        assert result["publisher"] == "Bob"
        assert result["pre_release"] is False
        assert result["published_at"] == "2026-03-01T09:00:00+00:00"

    def test_pre_release_flag(self):
        version = _make_version(version="1.0-pre1", finalized=False)
        result = json.loads(ReaderFileService.render_vocabulary(version))
        assert result["pre_release"] is True

    def test_project_metadata(self):
        version = _make_version()
        result = json.loads(ReaderFileService.render_vocabulary(version))
        project = result["project"]
        assert project["id"] == str(PROJECT_ID)
        assert project["name"] == "Demo Taxonomy"
        assert project["description"] == "A demo."
        assert project["namespace"] == "http://example.org/taxonomies/demo"

    def test_concepts_as_dict_keyed_by_uuid(self):
        version = _make_version()
        result = json.loads(ReaderFileService.render_vocabulary(version))
        concepts = result["schemes"][0]["concepts"]
        assert isinstance(concepts, dict)
        assert str(CONCEPT_A_ID) in concepts
        assert str(CONCEPT_B_ID) in concepts
        assert str(CONCEPT_CHILD_ID) in concepts

    def test_top_concepts_excludes_children(self):
        """top_concepts should be concepts with no broader relationships."""
        version = _make_version()
        result = json.loads(ReaderFileService.render_vocabulary(version))
        top = result["schemes"][0]["top_concepts"]
        assert str(CONCEPT_A_ID) in top
        assert str(CONCEPT_B_ID) in top
        assert str(CONCEPT_CHILD_ID) not in top

    def test_broader_ids_renamed_to_broader(self):
        version = _make_version()
        result = json.loads(ReaderFileService.render_vocabulary(version))
        child = result["schemes"][0]["concepts"][str(CONCEPT_CHILD_ID)]
        assert "broader" in child
        assert "broader_ids" not in child
        assert child["broader"] == [str(CONCEPT_B_ID)]

    def test_related_ids_renamed_to_related(self):
        version = _make_version()
        result = json.loads(ReaderFileService.render_vocabulary(version))
        concept_a = result["schemes"][0]["concepts"][str(CONCEPT_A_ID)]
        assert "related" in concept_a
        assert "related_ids" not in concept_a
        assert concept_a["related"] == [str(CONCEPT_B_ID)]

    def test_concept_fields_present(self):
        version = _make_version()
        result = json.loads(ReaderFileService.render_vocabulary(version))
        concept = result["schemes"][0]["concepts"][str(CONCEPT_A_ID)]
        assert concept["pref_label"] == "Red"
        assert concept["identifier"] == "red"
        assert concept["uri"] == "http://example.org/colors/red"
        assert concept["alt_labels"] == ["Crimson"]
        assert concept["definition"] is None
        assert concept["scope_note"] is None

    def test_domain_class_renamed_to_domain_class_uri(self):
        version = _make_version()
        result = json.loads(ReaderFileService.render_vocabulary(version))
        prop = result["properties"][0]
        assert "domain_class_uri" in prop
        assert "domain_class" not in prop
        assert prop["domain_class_uri"] == "http://example.org/Finding"

    def test_property_fields_preserved(self):
        version = _make_version()
        result = json.loads(ReaderFileService.render_vocabulary(version))
        prop = result["properties"][0]
        assert prop["id"] == str(PROPERTY_ID)
        assert prop["range_scheme_id"] == str(SCHEME_ID)
        assert prop["range_scheme_uri"] == "http://example.org/colors"
        assert prop["range_datatype"] is None
        assert prop["cardinality"] == "single"
        assert prop["required"] is False

    def test_classes_passed_through(self):
        version = _make_version()
        result = json.loads(ReaderFileService.render_vocabulary(version))
        cls = result["classes"][0]
        assert cls["id"] == str(CLASS_ID)
        assert cls["label"] == "Finding"

    def test_scheme_fields(self):
        version = _make_version()
        result = json.loads(ReaderFileService.render_vocabulary(version))
        scheme = result["schemes"][0]
        assert scheme["id"] == str(SCHEME_ID)
        assert scheme["title"] == "Colors"
        assert scheme["description"] == "Color vocab."
        assert scheme["uri"] == "http://example.org/colors"


# ===================================================================
# render_project_index
# ===================================================================


class TestRenderProjectIndex:
    def test_format_version(self):
        project = _make_project()
        versions = [_make_version()]
        result = json.loads(ReaderFileService.render_project_index(project, versions))
        assert result["format_version"] == "1.0"

    def test_project_metadata(self):
        project = _make_project()
        versions = [_make_version()]
        result = json.loads(ReaderFileService.render_project_index(project, versions))
        assert result["project"]["id"] == str(PROJECT_ID)
        assert result["project"]["name"] == "Demo Taxonomy"
        assert result["project"]["namespace"] == "http://example.org/taxonomies/demo"

    def test_latest_version_from_finalized(self):
        project = _make_project()
        versions = [
            _make_version(version="2.0", finalized=True),
            _make_version(version="1.0", finalized=True),
        ]
        result = json.loads(ReaderFileService.render_project_index(project, versions))
        assert result["latest_version"] == "2.0"

    def test_latest_version_null_when_only_pre_releases(self):
        project = _make_project()
        versions = [_make_version(version="1.0-pre1", finalized=False)]
        result = json.loads(ReaderFileService.render_project_index(project, versions))
        assert result["latest_version"] is None

    def test_version_entry_fields(self):
        project = _make_project()
        version = _make_version(
            version="1.0",
            title="Initial release",
            publisher="Jane",
            notes="First!",
            finalized=True,
            published_at=datetime(2026, 2, 1, 9, 0, 0, tzinfo=UTC),
        )
        result = json.loads(ReaderFileService.render_project_index(project, [version]))
        entry = result["versions"][0]
        assert entry["version"] == "1.0"
        assert entry["title"] == "Initial release"
        assert entry["publisher"] == "Jane"
        assert entry["notes"] == "First!"
        assert entry["pre_release"] is False
        assert entry["published_at"] == "2026-02-01T09:00:00+00:00"

    def test_content_summary_counts(self):
        """content_summary should count entities from the stored snapshot."""
        project = _make_project()
        version = _make_version()  # default snapshot: 1 scheme, 3 concepts, 1 prop, 1 class
        result = json.loads(ReaderFileService.render_project_index(project, [version]))
        summary = result["versions"][0]["content_summary"]
        assert summary["schemes"] == 1
        assert summary["concepts"] == 3
        assert summary["properties"] == 1
        assert summary["classes"] == 1


# ===================================================================
# render_root_index
# ===================================================================


class TestRenderRootIndex:
    def test_format_version(self):
        result = json.loads(ReaderFileService.render_root_index([]))
        assert result["format_version"] == "1.0"

    def test_empty_projects(self):
        result = json.loads(ReaderFileService.render_root_index([]))
        assert result["projects"] == []

    def test_project_with_latest_version(self):
        project = _make_project()
        result = json.loads(
            ReaderFileService.render_root_index([(project, "2.0")])
        )
        entry = result["projects"][0]
        assert entry["id"] == str(PROJECT_ID)
        assert entry["name"] == "Demo Taxonomy"
        assert entry["description"] == "A demo."
        assert entry["latest_version"] == "2.0"

    def test_project_with_null_latest_version(self):
        project = _make_project()
        result = json.loads(
            ReaderFileService.render_root_index([(project, None)])
        )
        assert result["projects"][0]["latest_version"] is None


# ===================================================================
# JSON schema validation
# ===================================================================


class TestSchemaValidation:
    """Validate rendered output against the authoritative JSON schemas."""

    def test_vocabulary_matches_schema(self):
        version = _make_version()
        doc = json.loads(ReaderFileService.render_vocabulary(version))
        jsonschema.validate(doc, VOCABULARY_SCHEMA)

    def test_project_index_matches_schema(self):
        project = _make_project()
        versions = [
            _make_version(version="2.0", finalized=True),
            _make_version(version="1.0-pre1", finalized=False, notes="Testing"),
        ]
        doc = json.loads(ReaderFileService.render_project_index(project, versions))
        jsonschema.validate(doc, PROJECT_INDEX_SCHEMA)

    def test_root_index_matches_schema(self):
        project = _make_project()
        doc = json.loads(ReaderFileService.render_root_index([(project, "2.0")]))
        jsonschema.validate(doc, ROOT_INDEX_SCHEMA)

    def test_root_index_empty_matches_schema(self):
        doc = json.loads(ReaderFileService.render_root_index([]))
        jsonschema.validate(doc, ROOT_INDEX_SCHEMA)


# ===================================================================
# publish_reader_files integration tests
# ===================================================================


class TestPublishReaderFiles:
    """Integration tests using FilesystemBlobStore and a real DB session."""

    @pytest.fixture
    async def publishable(self, db_session):
        """Create a publishable project and return (project, scheme)."""
        from taxonomy_builder.models.concept import Concept
        from taxonomy_builder.models.concept_scheme import ConceptScheme
        from taxonomy_builder.models.project import Project

        project = Project(name="Reader Test", namespace="http://example.org/reader")
        db_session.add(project)
        await db_session.flush()
        await db_session.refresh(project)

        scheme = ConceptScheme(
            project_id=project.id,
            title="Terms",
            uri="http://example.org/reader/terms",
        )
        db_session.add(scheme)
        await db_session.flush()
        await db_session.refresh(scheme)

        db_session.add(
            Concept(scheme_id=scheme.id, pref_label="Alpha", identifier="alpha")
        )
        await db_session.flush()

        # Expunge so the publishing service loads a fresh project with relationships
        db_session.expunge(project)
        return project

    def _make_publishing_service(self, db_session):
        from taxonomy_builder.services.concept_service import ConceptService
        from taxonomy_builder.services.project_service import ProjectService
        from taxonomy_builder.services.publishing_service import PublishingService
        from taxonomy_builder.services.snapshot_service import SnapshotService

        ps = ProjectService(db_session)
        cs = ConceptService(db_session)
        ss = SnapshotService(db_session, ps, cs)
        return PublishingService(db_session, ps, ss)

    async def _publish(self, db_session, project, version_str="1.0", pre_release=False):
        """Publish a version via the service layer."""
        from taxonomy_builder.schemas.publishing import PublishRequest

        pub = self._make_publishing_service(db_session)
        request = PublishRequest(
            version=version_str, title=f"V{version_str}", pre_release=pre_release
        )
        return await pub.publish(project.id, request, publisher="Tester")

    @pytest.mark.asyncio
    async def test_writes_all_three_files(self, db_session, publishable, tmp_path):
        blob_store = FilesystemBlobStore(root=tmp_path)
        purger = NoOpPurger()
        version = await self._publish(db_session, publishable)

        service = ReaderFileService(self._make_publishing_service(db_session), blob_store, purger)
        await service.publish_reader_files(version)

        pid = str(publishable.id)
        assert (tmp_path / pid / "1.0" / "vocabulary.json").exists()
        assert (tmp_path / pid / "index.json").exists()
        assert (tmp_path / "index.json").exists()

    @pytest.mark.asyncio
    async def test_vocabulary_content(self, db_session, publishable, tmp_path):
        blob_store = FilesystemBlobStore(root=tmp_path)
        purger = NoOpPurger()
        version = await self._publish(db_session, publishable)

        service = ReaderFileService(self._make_publishing_service(db_session), blob_store, purger)
        await service.publish_reader_files(version)

        vocab = json.loads(
            (tmp_path / str(publishable.id) / "1.0" / "vocabulary.json").read_text()
        )
        assert vocab["format_version"] == "1.0"
        assert vocab["version"] == "1.0"
        assert vocab["pre_release"] is False
        assert len(vocab["schemes"]) == 1
        assert len(vocab["schemes"][0]["concepts"]) == 1
        jsonschema.validate(vocab, VOCABULARY_SCHEMA)

    @pytest.mark.asyncio
    async def test_project_index_content(self, db_session, publishable, tmp_path):
        blob_store = FilesystemBlobStore(root=tmp_path)
        purger = NoOpPurger()
        version = await self._publish(db_session, publishable)

        service = ReaderFileService(self._make_publishing_service(db_session), blob_store, purger)
        await service.publish_reader_files(version)

        idx = json.loads(
            (tmp_path / str(publishable.id) / "index.json").read_text()
        )
        assert idx["latest_version"] == "1.0"
        assert len(idx["versions"]) == 1
        assert idx["versions"][0]["content_summary"]["concepts"] == 1
        jsonschema.validate(idx, PROJECT_INDEX_SCHEMA)

    @pytest.mark.asyncio
    async def test_root_index_content(self, db_session, publishable, tmp_path):
        blob_store = FilesystemBlobStore(root=tmp_path)
        purger = NoOpPurger()
        version = await self._publish(db_session, publishable)

        service = ReaderFileService(self._make_publishing_service(db_session), blob_store, purger)
        await service.publish_reader_files(version)

        root = json.loads((tmp_path / "index.json").read_text())
        assert len(root["projects"]) == 1
        assert root["projects"][0]["id"] == str(publishable.id)
        assert root["projects"][0]["latest_version"] == "1.0"
        jsonschema.validate(root, ROOT_INDEX_SCHEMA)

    @pytest.mark.asyncio
    async def test_cdn_purge_paths_for_release(self, db_session, publishable, tmp_path):
        blob_store = FilesystemBlobStore(root=tmp_path)
        purged: list[list[str]] = []

        class RecordingPurger:
            async def purge(self, paths: list[str]) -> None:
                purged.append(paths)
            async def close(self) -> None:
                pass

        version = await self._publish(db_session, publishable)
        service = ReaderFileService(self._make_publishing_service(db_session), blob_store, RecordingPurger())
        await service.publish_reader_files(version)

        assert len(purged) == 1
        paths = purged[0]
        pid = str(publishable.id)
        assert f"/{pid}/index.json" in paths
        assert "/index.json" in paths

    @pytest.mark.asyncio
    async def test_pre_release_skips_root_index_when_project_already_published(
        self, db_session, publishable, tmp_path
    ):
        blob_store = FilesystemBlobStore(root=tmp_path)
        purged: list[list[str]] = []

        class RecordingPurger:
            async def purge(self, paths: list[str]) -> None:
                purged.append(paths)
            async def close(self) -> None:
                pass

        # First publish a release
        v1 = await self._publish(db_session, publishable, "1.0")
        service = ReaderFileService(self._make_publishing_service(db_session), blob_store, RecordingPurger())
        await service.publish_reader_files(v1)

        # Now publish a pre-release
        v2 = await self._publish(db_session, publishable, "2.0-pre1", pre_release=True)
        await service.publish_reader_files(v2)

        # Second publish should NOT include root index in purge paths
        assert len(purged) == 2
        second_purge = purged[1]
        assert "/index.json" not in second_purge

    @pytest.mark.asyncio
    async def test_first_pre_release_writes_root_index(
        self, db_session, publishable, tmp_path
    ):
        """First-ever publish for a project writes root index even if pre-release."""
        blob_store = FilesystemBlobStore(root=tmp_path)
        purged: list[list[str]] = []

        class RecordingPurger:
            async def purge(self, paths: list[str]) -> None:
                purged.append(paths)
            async def close(self) -> None:
                pass

        version = await self._publish(
            db_session, publishable, "1.0-pre1", pre_release=True
        )
        service = ReaderFileService(self._make_publishing_service(db_session), blob_store, RecordingPurger())
        await service.publish_reader_files(version)

        assert (tmp_path / "index.json").exists()
        assert "/index.json" in purged[0]
