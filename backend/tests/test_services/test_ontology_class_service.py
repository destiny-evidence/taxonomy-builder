"""Tests for OntologyClassService URI behavior."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.ontology_class import OntologyClassCreate, OntologyClassUpdate
from taxonomy_builder.services.ontology_class_service import (
    OntologyClassService,
    OntologyClassURIExistsError,
)
from taxonomy_builder.services.project_service import ProjectService


@pytest.fixture
def ontology_class_service(db_session: AsyncSession) -> OntologyClassService:
    """Create an OntologyClassService instance."""
    project_service = ProjectService(db_session)
    return OntologyClassService(db_session, project_service)


class TestCreateOntologyClassURI:
    """Tests for URI behavior on create."""

    @pytest.mark.asyncio
    async def test_create_computes_uri_from_namespace(
        self, project: Project, ontology_class_service: OntologyClassService
    ) -> None:
        """Create without explicit URI computes from project namespace."""
        cls_in = OntologyClassCreate(
            identifier="Finding", label="Finding"
        )
        cls = await ontology_class_service.create_ontology_class(project.id, cls_in)

        assert cls.uri == "https://example.org/test/Finding"

    @pytest.mark.asyncio
    async def test_create_with_explicit_uri_stores_as_is(
        self, project: Project, ontology_class_service: OntologyClassService
    ) -> None:
        """Create with explicit URI stores it directly (import path)."""
        cls_in = OntologyClassCreate(
            identifier="Finding",
            label="Finding",
            uri="https://external.org/ontology/Finding",
        )
        cls = await ontology_class_service.create_ontology_class(project.id, cls_in)

        assert cls.uri == "https://external.org/ontology/Finding"

    @pytest.mark.asyncio
    async def test_namespace_trailing_slash_stripped(
        self, project: Project, ontology_class_service: OntologyClassService
    ) -> None:
        """Trailing slash on namespace is stripped before computing URI."""
        cls_in = OntologyClassCreate(
            identifier="Study", label="Study"
        )
        cls = await ontology_class_service.create_ontology_class(project.id, cls_in)

        assert cls.uri == "https://example.org/test/Study"
        assert "//" not in cls.uri.replace("https://", "")

    @pytest.mark.asyncio
    async def test_duplicate_uri_raises_error(
        self, project: Project, ontology_class_service: OntologyClassService
    ) -> None:
        """Two classes with same URI in same project raises OntologyClassURIExistsError."""
        cls_in1 = OntologyClassCreate(
            identifier="Finding",
            label="Finding",
            uri="https://example.org/test/Finding",
        )
        await ontology_class_service.create_ontology_class(project.id, cls_in1)

        cls_in2 = OntologyClassCreate(
            identifier="Finding2",
            label="Finding 2",
            uri="https://example.org/test/Finding",
        )
        with pytest.raises(OntologyClassURIExistsError):
            await ontology_class_service.create_ontology_class(project.id, cls_in2)


class TestUpdateOntologyClassURI:
    """Tests for URI immutability on update."""

    @pytest.mark.asyncio
    async def test_update_identifier_does_not_change_uri(
        self, project: Project, ontology_class_service: OntologyClassService
    ) -> None:
        """URI is immutable — updating identifier does not change URI."""
        cls_in = OntologyClassCreate(
            identifier="Finding", label="Finding"
        )
        cls = await ontology_class_service.create_ontology_class(project.id, cls_in)
        original_uri = cls.uri

        update = OntologyClassUpdate(identifier="UpdatedFinding")
        updated = await ontology_class_service.update_ontology_class(cls.id, update)

        assert updated is not None
        assert updated.identifier == "UpdatedFinding"
        assert updated.uri == original_uri
