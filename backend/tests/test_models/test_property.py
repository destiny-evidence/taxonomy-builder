"""Tests for the Property model."""

from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.property import Property


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


@pytest.fixture
async def scheme(db_session: AsyncSession, project: Project) -> ConceptScheme:
    """Create a concept scheme for testing."""
    scheme = ConceptScheme(
        project_id=project.id,
        title="Education Level",
        uri="http://example.org/schemes/education-level",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


@pytest.mark.asyncio
async def test_create_property_with_range_scheme(
    db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """Test creating a property with range_scheme_id."""
    prop = Property(
        project_id=project.id,
        identifier="educationLevel",
        label="Education Level",
        description="The level of education",
        domain_class="https://evrepo.example.org/vocab/Finding",
        range_scheme_id=scheme.id,
        cardinality="single",
        required=False,
        uri="https://example.org/vocab/educationLevel",
    )
    db_session.add(prop)
    await db_session.flush()
    await db_session.refresh(prop)

    assert prop.id is not None
    assert isinstance(prop.id, UUID)
    assert prop.project_id == project.id
    assert prop.identifier == "educationLevel"
    assert prop.label == "Education Level"
    assert prop.description == "The level of education"
    assert prop.domain_class == "https://evrepo.example.org/vocab/Finding"
    assert prop.range_scheme_id == scheme.id
    assert prop.range_datatype is None
    assert prop.cardinality == "single"
    assert prop.required is False
    assert prop.created_at is not None
    assert prop.updated_at is not None


@pytest.mark.asyncio
async def test_create_property_with_range_datatype(
    db_session: AsyncSession, project: Project
) -> None:
    """Test creating a property with range_datatype."""
    prop = Property(
        project_id=project.id,
        identifier="sampleSize",
        label="Sample Size",
        domain_class="https://evrepo.example.org/vocab/Finding",
        range_datatype="xsd:integer",
        cardinality="single",
        required=True,
        uri="https://example.org/vocab/sampleSize",
    )
    db_session.add(prop)
    await db_session.flush()
    await db_session.refresh(prop)

    assert prop.id is not None
    assert prop.identifier == "sampleSize"
    assert prop.range_scheme_id is None
    assert prop.range_datatype == "xsd:integer"
    assert prop.required is True


@pytest.mark.asyncio
async def test_property_id_is_uuidv7(db_session: AsyncSession, project: Project) -> None:
    """Test that property IDs are UUIDv7."""
    prop = Property(
        project_id=project.id,
        identifier="testProp",
        label="Test Property",
        domain_class="https://evrepo.example.org/vocab/Finding",
        range_datatype="xsd:string",
        cardinality="single",
        required=False,
        uri="https://example.org/vocab/testProp",
    )
    db_session.add(prop)
    await db_session.flush()
    await db_session.refresh(prop)

    assert prop.id.version == 7


@pytest.mark.asyncio
async def test_property_relationships(
    db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """Test that property relationships are loaded correctly."""
    prop = Property(
        project_id=project.id,
        identifier="educationLevel",
        label="Education Level",
        domain_class="https://evrepo.example.org/vocab/Finding",
        range_scheme_id=scheme.id,
        cardinality="single",
        required=False,
        uri="https://example.org/vocab/educationLevel",
    )
    db_session.add(prop)
    await db_session.flush()
    await db_session.refresh(prop)

    assert prop.project is not None
    assert prop.project.id == project.id
    assert prop.range_scheme is not None
    assert prop.range_scheme.id == scheme.id
