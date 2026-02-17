"""Tests for the Property model."""

from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import ConceptSchemeFactory, ProjectFactory, PropertyFactory, flush


@pytest.fixture
async def project(db_session: AsyncSession):
    return await flush(
        db_session, ProjectFactory.create(name="Test Project", namespace="https://example.org/vocab/")
    )


@pytest.fixture
async def scheme(db_session: AsyncSession, project):
    return await flush(
        db_session,
        ConceptSchemeFactory.create(
            project=project,
            title="Education Level",
            uri="http://example.org/schemes/education-level",
        ),
    )


@pytest.mark.asyncio
async def test_create_property_with_range_scheme(
    db_session: AsyncSession, project, scheme
) -> None:
    """Test creating a property with range_scheme_id."""
    prop = await flush(
        db_session,
        PropertyFactory.create(
            project=project,
            identifier="educationLevel",
            label="Education Level",
            description="The level of education",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_scheme=scheme,
            range_datatype=None,
            cardinality="single",
            required=False,
        ),
    )

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
    db_session: AsyncSession, project
) -> None:
    """Test creating a property with range_datatype."""
    prop = await flush(
        db_session,
        PropertyFactory.create(
            project=project,
            identifier="sampleSize",
            label="Sample Size",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:integer",
            cardinality="single",
            required=True,
        ),
    )

    assert prop.id is not None
    assert prop.identifier == "sampleSize"
    assert prop.range_scheme_id is None
    assert prop.range_datatype == "xsd:integer"
    assert prop.required is True


@pytest.mark.asyncio
async def test_property_id_is_uuidv7(db_session: AsyncSession, project) -> None:
    """Test that property IDs are UUIDv7."""
    prop = await flush(db_session, PropertyFactory.create(project=project))

    assert prop.id.version == 7


@pytest.mark.asyncio
async def test_property_relationships(
    db_session: AsyncSession, project, scheme
) -> None:
    """Test that property relationships are loaded correctly."""
    prop = await flush(
        db_session,
        PropertyFactory.create(
            project=project,
            identifier="educationLevel",
            label="Education Level",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_scheme=scheme,
            range_datatype=None,
            cardinality="single",
        ),
    )

    # Check relationships
    assert prop.project is not None
    assert prop.project.id == project.id
    assert prop.range_scheme is not None
    assert prop.range_scheme.id == scheme.id


@pytest.mark.asyncio
async def test_property_uri_computed_from_namespace(
    db_session: AsyncSession, project
) -> None:
    """Test that property URI is computed from project namespace and identifier."""
    prop = await flush(
        db_session,
        PropertyFactory.create(project=project, identifier="educationLevel"),
    )

    # Project namespace is "https://example.org/vocab/"
    assert prop.uri == "https://example.org/vocab/educationLevel"


@pytest.mark.asyncio
async def test_property_uri_none_when_no_namespace(db_session: AsyncSession) -> None:
    """Test that property URI is None when project has no namespace."""
    project_no_ns = await flush(db_session, ProjectFactory.create(namespace=None))

    prop = await flush(
        db_session,
        PropertyFactory.create(project=project_no_ns, identifier="educationLevel"),
    )

    assert prop.uri is None
