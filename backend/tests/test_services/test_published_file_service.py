"""Tests for PublishedFileService and SKOSExportService.render_rdf_artifacts."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID

import pytest
from rdflib import Graph
from rdflib.namespace import RDF, SKOS

from taxonomy_builder.blob_store import FilesystemBlobStore, NoOpPurger
from taxonomy_builder.schemas.snapshot import SnapshotVocabulary
from taxonomy_builder.services.skos_export_service import SKOSExportService

# ---------------------------------------------------------------------------
# Test helpers – same lightweight stand-ins as test_reader_file_service.py
# ---------------------------------------------------------------------------

PROJECT_ID = UUID("01965a00-0000-7000-8000-000000000000")
SCHEME_ID = UUID("01965a00-0000-7000-8000-000000000001")
CONCEPT_A_ID = UUID("01965a00-0000-7000-8000-000000000002")
CONCEPT_B_ID = UUID("01965a00-0000-7000-8000-000000000003")
VERSION_ID = UUID("01965a00-0000-7000-8000-f00000000001")


def _make_snapshot():
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
                "concepts": [
                    {
                        "id": str(CONCEPT_A_ID),
                        "pref_label": "Red",
                        "identifier": "red",
                        "uri": "http://example.org/colors/red",
                        "definition": "A warm color.",
                        "scope_note": None,
                        "alt_labels": ["Crimson"],
                        "broader_ids": [],
                        "related_ids": [],
                        "concept_type_uris": [],
                    },
                    {
                        "id": str(CONCEPT_B_ID),
                        "pref_label": "Blue",
                        "identifier": "blue",
                        "uri": "http://example.org/colors/blue",
                        "definition": None,
                        "scope_note": None,
                        "alt_labels": [],
                        "broader_ids": [],
                        "related_ids": [],
                        "concept_type_uris": [],
                    },
                ],
            }
        ],
        "properties": [],
        "classes": [],
    }


def _make_version(*, snapshot=None):
    snap = snapshot or _make_snapshot()
    return SimpleNamespace(
        id=VERSION_ID,
        project_id=PROJECT_ID,
        version="1.0",
        title="Initial release",
        finalized=True,
        published_at=datetime(2026, 2, 1, 9, 0, 0, tzinfo=UTC),
        publisher="Jane Smith",
        notes=None,
        previous_version_id=None,
        snapshot=snap,
        snapshot_vocabulary=SnapshotVocabulary.model_validate(snap),
        project=SimpleNamespace(
            id=PROJECT_ID,
            name="Demo Taxonomy",
            description="A demo.",
            namespace="http://example.org/taxonomies/demo",
        ),
    )


# ===================================================================
# SKOSExportService.render_rdf_artifacts
# ===================================================================


class TestRenderRdfArtifacts:
    @pytest.fixture
    def service(self, db_session):
        return SKOSExportService(db_session)

    def test_returns_three_formats(self, service):
        version = _make_version()
        artifacts = service.render_rdf_artifacts(version)
        assert set(artifacts.keys()) == {"vocabulary.ttl", "vocabulary.jsonld", "vocabulary.rdf"}

    def test_content_types(self, service):
        version = _make_version()
        artifacts = service.render_rdf_artifacts(version)
        assert artifacts["vocabulary.ttl"][1] == "text/turtle"
        assert artifacts["vocabulary.jsonld"][1] == "application/ld+json"
        assert artifacts["vocabulary.rdf"][1] == "application/rdf+xml"

    def test_all_values_are_bytes(self, service):
        version = _make_version()
        artifacts = service.render_rdf_artifacts(version)
        for filename, (data, _) in artifacts.items():
            assert isinstance(data, bytes), f"{filename} data should be bytes"

    def test_ttl_parseable(self, service):
        version = _make_version()
        artifacts = service.render_rdf_artifacts(version)
        g = Graph()
        g.parse(data=artifacts["vocabulary.ttl"][0], format="turtle")
        assert (None, RDF.type, SKOS.ConceptScheme) in g
        assert (None, RDF.type, SKOS.Concept) in g

    def test_xml_parseable(self, service):
        version = _make_version()
        artifacts = service.render_rdf_artifacts(version)
        g = Graph()
        g.parse(data=artifacts["vocabulary.rdf"][0], format="xml")
        assert (None, RDF.type, SKOS.ConceptScheme) in g
        assert (None, RDF.type, SKOS.Concept) in g

    def test_jsonld_parseable(self, service):
        version = _make_version()
        artifacts = service.render_rdf_artifacts(version)
        g = Graph()
        g.parse(data=artifacts["vocabulary.jsonld"][0], format="json-ld")
        assert (None, RDF.type, SKOS.ConceptScheme) in g
        assert (None, RDF.type, SKOS.Concept) in g

    def test_contains_expected_triples(self, service):
        """All three formats should contain the same core triples."""
        version = _make_version()
        artifacts = service.render_rdf_artifacts(version)
        fmt_map = {
            "vocabulary.ttl": "turtle",
            "vocabulary.rdf": "xml",
            "vocabulary.jsonld": "json-ld",
        }
        for filename, (data, _) in artifacts.items():
            g = Graph()
            g.parse(data=data, format=fmt_map[filename])
            schemes = list(g.subjects(RDF.type, SKOS.ConceptScheme))
            assert len(schemes) == 1, f"{filename}: expected 1 scheme"
            concepts = list(g.subjects(RDF.type, SKOS.Concept))
            assert len(concepts) == 2, f"{filename}: expected 2 concepts"


# ===================================================================
# PublishingService.publish_artifacts integration tests
# ===================================================================


class TestPublishArtifacts:
    @pytest.fixture
    async def publishable(self, db_session):
        from taxonomy_builder.models.concept import Concept
        from taxonomy_builder.models.concept_scheme import ConceptScheme
        from taxonomy_builder.models.project import Project

        project = Project(
            name="Artifact Test",
            namespace="http://example.org/artifacts",
            identifier_prefix="ART",
        )
        db_session.add(project)
        await db_session.flush()
        await db_session.refresh(project)

        scheme = ConceptScheme(
            project_id=project.id,
            title="Terms",
            uri="http://example.org/artifacts/terms",
        )
        db_session.add(scheme)
        await db_session.flush()
        await db_session.refresh(scheme)

        db_session.add(Concept(scheme_id=scheme.id, pref_label="Alpha", identifier="alpha"))
        await db_session.flush()

        db_session.expunge(project)
        return project

    def _make_service(self, db_session, blob_store, purger):
        from taxonomy_builder.services.concept_service import ConceptService
        from taxonomy_builder.services.project_service import ProjectService
        from taxonomy_builder.services.publishing_service import PublishingService
        from taxonomy_builder.services.reader_file_service import ReaderFileService
        from taxonomy_builder.services.snapshot_service import SnapshotService

        ps = ProjectService(db_session)
        cs = ConceptService(db_session)
        ss = SnapshotService(db_session, ps, cs)
        return PublishingService(
            db_session,
            ps,
            ss,
            reader_file_service=ReaderFileService(blob_store, purger),
            blob_store=blob_store,
            skos_export_service=SKOSExportService(db_session),
        )

    async def _publish(self, service, project, version_str="1.0"):
        from taxonomy_builder.schemas.publishing import PublishRequest

        request = PublishRequest(version=version_str, title=f"V{version_str}", pre_release=False)
        return await service.publish(project.id, request, publisher="Tester")

    @pytest.mark.asyncio
    async def test_writes_rdf_artifacts(self, db_session, publishable, tmp_path):
        blob_store = FilesystemBlobStore(root=tmp_path)
        purger = NoOpPurger()
        service = self._make_service(db_session, blob_store, purger)
        version = await self._publish(service, publishable)
        await service.publish_artifacts(version)

        pid = str(publishable.id)
        assert (tmp_path / pid / "1.0" / "vocabulary.ttl").exists()
        assert (tmp_path / pid / "1.0" / "vocabulary.jsonld").exists()
        assert (tmp_path / pid / "1.0" / "vocabulary.rdf").exists()
        # Reader files should still be written too
        assert (tmp_path / pid / "1.0" / "vocabulary.json").exists()

    @pytest.mark.asyncio
    async def test_rdf_artifacts_parseable(self, db_session, publishable, tmp_path):
        blob_store = FilesystemBlobStore(root=tmp_path)
        purger = NoOpPurger()
        service = self._make_service(db_session, blob_store, purger)
        version = await self._publish(service, publishable)
        await service.publish_artifacts(version)

        pid = str(publishable.id)
        for filename, fmt in [
            ("vocabulary.ttl", "turtle"),
            ("vocabulary.rdf", "xml"),
            ("vocabulary.jsonld", "json-ld"),
        ]:
            data = (tmp_path / pid / "1.0" / filename).read_bytes()
            g = Graph()
            g.parse(data=data, format=fmt)
            assert (None, RDF.type, SKOS.ConceptScheme) in g
            assert (None, RDF.type, SKOS.Concept) in g
