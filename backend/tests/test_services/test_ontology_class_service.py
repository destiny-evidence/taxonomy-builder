"""Tests for OntologyClassService URI behavior."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.ontology_class import OntologyClassCreate, OntologyClassUpdate
from taxonomy_builder.services.ontology_class_service import (
    OntologyClassService,
)
from taxonomy_builder.services.project_service import ProjectService


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project with namespace for testing."""
    project = Project(
        name="Test Project",
        namespace="https://example.org/vocab/",
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def project_no_namespace(db_session: AsyncSession) -> Project:
    """Create a project without namespace for testing."""
    project = Project(name="No Namespace Project")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


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

        assert cls.uri == "https://example.org/vocab/Finding"

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
    async def test_create_without_namespace_raises_400(
        self,
        project_no_namespace: Project,
        ontology_class_service: OntologyClassService,
    ) -> None:
        """Create without namespace and no explicit URI raises ValueError."""
        cls_in = OntologyClassCreate(
            identifier="Finding", label="Finding"
        )
        with pytest.raises(ValueError, match="namespace"):
            await ontology_class_service.create_ontology_class(
                project_no_namespace.id, cls_in
            )

    @pytest.mark.asyncio
    async def test_create_with_explicit_uri_no_namespace_ok(
        self,
        project_no_namespace: Project,
        ontology_class_service: OntologyClassService,
    ) -> None:
        """Create with explicit URI works even without project namespace."""
        cls_in = OntologyClassCreate(
            identifier="Finding",
            label="Finding",
            uri="https://external.org/ontology/Finding",
        )
        cls = await ontology_class_service.create_ontology_class(
            project_no_namespace.id, cls_in
        )
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

        assert cls.uri == "https://example.org/vocab/Study"
        assert "//" not in cls.uri.replace("https://", "")


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
