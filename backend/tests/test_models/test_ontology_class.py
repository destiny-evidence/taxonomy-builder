"""Tests for the OntologyClass model."""

from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.ontology_class import OntologyClass
from taxonomy_builder.models.project import Project


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(
        name="Test Project",
        namespace="https://example.org/vocab/",
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_ontology_class_id_is_uuidv7(
    db_session: AsyncSession, project: Project
) -> None:
    """Test that ontology class IDs are UUIDv7."""
    cls = OntologyClass(
        project_id=project.id,
        identifier="Finding",
        label="Finding",
        uri="https://example.org/vocab/Finding",
    )
    db_session.add(cls)
    await db_session.flush()
    await db_session.refresh(cls)

    assert isinstance(cls.id, UUID)
    assert cls.id.version == 7


@pytest.mark.asyncio
async def test_ontology_class_unique_uri_per_project(
    db_session: AsyncSession, project: Project
) -> None:
    """Test that duplicate URIs within the same project are rejected."""
    cls1 = OntologyClass(
        project_id=project.id,
        identifier="Finding",
        label="Finding",
        uri="https://example.org/vocab/Finding",
    )
    db_session.add(cls1)
    await db_session.flush()

    cls2 = OntologyClass(
        project_id=project.id,
        identifier="Finding2",  # different identifier
        label="Finding 2",
        uri="https://example.org/vocab/Finding",  # same URI
    )
    db_session.add(cls2)
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_ontology_class_same_uri_different_projects(
    db_session: AsyncSession,
) -> None:
    """Test that the same URI can exist in different projects."""
    project1 = Project(name="Project 1", namespace="https://example.org/1/")
    project2 = Project(name="Project 2", namespace="https://example.org/2/")
    db_session.add_all([project1, project2])
    await db_session.flush()
    await db_session.refresh(project1)
    await db_session.refresh(project2)

    uri = "https://example.org/vocab/Finding"
    cls1 = OntologyClass(
        project_id=project1.id, identifier="Finding", label="Finding", uri=uri
    )
    cls2 = OntologyClass(
        project_id=project2.id, identifier="Finding", label="Finding", uri=uri
    )
    db_session.add_all([cls1, cls2])
    await db_session.flush()  # Should not raise

    await db_session.refresh(cls1)
    await db_session.refresh(cls2)
    assert cls1.uri == cls2.uri
