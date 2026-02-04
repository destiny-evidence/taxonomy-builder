"""Tests for PropertyService."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.property import Property
from taxonomy_builder.schemas.property import PropertyCreate
from taxonomy_builder.services.property_service import (
    DomainClassNotFoundError,
    InvalidRangeError,
    PropertyIdentifierExistsError,
    PropertyService,
    SchemeNotInProjectError,
)


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
async def other_project(db_session: AsyncSession) -> Project:
    """Create another project for testing cross-project validation."""
    project = Project(
        name="Other Project",
        namespace="https://other.org/vocab/",
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


@pytest.fixture
async def other_scheme(db_session: AsyncSession, other_project: Project) -> ConceptScheme:
    """Create a scheme in another project for testing cross-project validation."""
    scheme = ConceptScheme(
        project_id=other_project.id,
        title="Other Scheme",
        uri="http://other.org/schemes/other",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


class TestCreateProperty:
    """Tests for PropertyService.create_property."""

    @pytest.mark.asyncio
    async def test_create_property_with_range_scheme(
        self, db_session: AsyncSession, project: Project, scheme: ConceptScheme
    ) -> None:
        """Test creating a property with range_scheme_id."""
        service = PropertyService(db_session)
        prop_in = PropertyCreate(
            identifier="educationLevel",
            label="Education Level",
            description="The level of education",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_scheme_id=scheme.id,
            cardinality="single",
            required=False,
        )

        prop = await service.create_property(project.id, prop_in)

        assert prop.id is not None
        assert prop.identifier == "educationLevel"
        assert prop.label == "Education Level"
        assert prop.range_scheme_id == scheme.id
        assert prop.range_datatype is None

    @pytest.mark.asyncio
    async def test_create_property_with_range_datatype(
        self, db_session: AsyncSession, project: Project
    ) -> None:
        """Test creating a property with range_datatype."""
        service = PropertyService(db_session)
        prop_in = PropertyCreate(
            identifier="sampleSize",
            label="Sample Size",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:integer",
            cardinality="single",
            required=True,
        )

        prop = await service.create_property(project.id, prop_in)

        assert prop.identifier == "sampleSize"
        assert prop.range_scheme_id is None
        assert prop.range_datatype == "xsd:integer"
        assert prop.required is True

    @pytest.mark.asyncio
    async def test_create_property_invalid_domain_class(
        self, db_session: AsyncSession, project: Project
    ) -> None:
        """Test that invalid domain_class raises DomainClassNotFoundError."""
        service = PropertyService(db_session)
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://example.org/InvalidClass",
            range_datatype="xsd:string",
            cardinality="single",
        )

        with pytest.raises(DomainClassNotFoundError) as exc_info:
            await service.create_property(project.id, prop_in)
        assert "InvalidClass" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_property_both_range_fields_error(
        self, db_session: AsyncSession, project: Project, scheme: ConceptScheme
    ) -> None:
        """Test that providing both range_scheme_id and range_datatype raises error."""
        service = PropertyService(db_session)
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_scheme_id=scheme.id,
            range_datatype="xsd:string",
            cardinality="single",
        )

        with pytest.raises(InvalidRangeError) as exc_info:
            await service.create_property(project.id, prop_in)
        assert "exactly one" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_property_neither_range_field_error(
        self, db_session: AsyncSession, project: Project
    ) -> None:
        """Test that providing neither range field raises error."""
        service = PropertyService(db_session)
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://evrepo.example.org/vocab/Finding",
            cardinality="single",
        )

        with pytest.raises(InvalidRangeError) as exc_info:
            await service.create_property(project.id, prop_in)
        assert "exactly one" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_property_scheme_not_in_project(
        self, db_session: AsyncSession, project: Project, other_scheme: ConceptScheme
    ) -> None:
        """Test that referencing a scheme from another project raises error."""
        service = PropertyService(db_session)
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_scheme_id=other_scheme.id,
            cardinality="single",
        )

        with pytest.raises(SchemeNotInProjectError):
            await service.create_property(project.id, prop_in)

    @pytest.mark.asyncio
    async def test_create_property_duplicate_identifier(
        self, db_session: AsyncSession, project: Project
    ) -> None:
        """Test that duplicate identifier in same project raises error."""
        service = PropertyService(db_session)

        # Create first property
        prop_in1 = PropertyCreate(
            identifier="testProp",
            label="Test 1",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        await service.create_property(project.id, prop_in1)

        # Try to create second property with same identifier
        prop_in2 = PropertyCreate(
            identifier="testProp",
            label="Test 2",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:integer",
            cardinality="single",
        )
        with pytest.raises(PropertyIdentifierExistsError):
            await service.create_property(project.id, prop_in2)

    @pytest.mark.asyncio
    async def test_create_property_scheme_not_found(
        self, db_session: AsyncSession, project: Project
    ) -> None:
        """Test that referencing a non-existent scheme raises error."""
        service = PropertyService(db_session)
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_scheme_id=uuid4(),
            cardinality="single",
        )

        with pytest.raises(SchemeNotInProjectError):
            await service.create_property(project.id, prop_in)
