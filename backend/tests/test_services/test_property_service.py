"""Tests for PropertyService."""

from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.property import PropertyCreate, PropertyUpdate
from taxonomy_builder.services.concept_scheme_service import ConceptSchemeService
from taxonomy_builder.services.project_service import ProjectNotFoundError, ProjectService
from taxonomy_builder.services.property_service import (
    DomainClassNotFoundError,
    InvalidRangeError,
    ProjectNamespaceRequiredError,
    PropertyIdentifierExistsError,
    PropertyService,
    PropertyURIExistsError,
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


@pytest.fixture
def property_service(db_session: AsyncSession) -> PropertyService:
    """Create a PropertyService with all required dependencies."""
    project_service = ProjectService(db_session)
    scheme_service = ConceptSchemeService(db_session)
    return PropertyService(db_session, project_service, scheme_service)


# --- Pure schema validation (no DB needed) ---


class TestPropertySchemaValidation:
    """PropertyCreate/PropertyUpdate schema validation."""

    @pytest.mark.parametrize(
        "range_kwargs",
        [
            pytest.param(
                {"range_scheme_id": uuid4(), "range_datatype": "xsd:string"},
                id="scheme+datatype",
            ),
            pytest.param(
                {
                    "range_class": "https://example.org/Foo",
                    "range_datatype": "xsd:string",
                },
                id="class+datatype",
            ),
            pytest.param(
                {
                    "range_class": "https://example.org/Foo",
                    "range_scheme_id": uuid4(),
                },
                id="class+scheme",
            ),
            pytest.param({}, id="none"),
        ],
    )
    def test_create_rejects_invalid_range_combination(
        self, range_kwargs: dict
    ) -> None:
        """PropertyCreate requires exactly one range field."""
        with pytest.raises(ValidationError, match="(?i)exactly one"):
            PropertyCreate(
                identifier="testProp",
                label="Test",
                domain_class="https://evrepo.example.org/vocab/Finding",
                cardinality="single",
                **range_kwargs,
            )

    def test_update_rejects_multiple_range_fields(self) -> None:
        """PropertyUpdate rejects setting >1 range field."""
        with pytest.raises(ValidationError, match="(?i)at most one"):
            PropertyUpdate(
                range_scheme_id=uuid4(),
                range_datatype="xsd:integer",
            )


# --- Service tests ---


class TestCreateProperty:
    """Tests for PropertyService.create_property."""

    @pytest.mark.asyncio
    async def test_create_property_with_range_scheme(
        self, db_session: AsyncSession, project: Project, scheme: ConceptScheme, property_service: PropertyService
    ) -> None:
        """Test creating a property with range_scheme_id."""
        service = property_service
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
        self, db_session: AsyncSession, project: Project, property_service: PropertyService
    ) -> None:
        """Test creating a property with range_datatype."""
        service = property_service
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
    async def test_create_property_with_range_class(
        self, db_session: AsyncSession, project: Project, property_service: PropertyService
    ) -> None:
        """Test creating a property with range_class (URI string)."""
        service = property_service
        prop_in = PropertyCreate(
            identifier="educationLevel",
            label="Education Level",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_class="https://example.org/ontology/EducationLevel",
            cardinality="single",
        )

        prop = await service.create_property(project.id, prop_in)

        assert prop.id is not None
        assert prop.range_class == "https://example.org/ontology/EducationLevel"
        assert prop.range_scheme_id is None
        assert prop.range_datatype is None

    @pytest.mark.asyncio
    async def test_create_property_invalid_domain_class(
        self, db_session: AsyncSession, project: Project, property_service: PropertyService
    ) -> None:
        """Test that invalid domain_class raises DomainClassNotFoundError."""
        service = property_service
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
    async def test_create_property_scheme_not_in_project(
        self, db_session: AsyncSession, project: Project, other_scheme: ConceptScheme, property_service: PropertyService
    ) -> None:
        """Test that referencing a scheme from another project raises error."""
        service = property_service
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
        self, db_session: AsyncSession, project: Project, property_service: PropertyService
    ) -> None:
        """Test that duplicate identifier in same project raises error."""
        service = property_service

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
        self, db_session: AsyncSession, project: Project, property_service: PropertyService
    ) -> None:
        """Test that referencing a non-existent scheme raises error."""
        service = property_service
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_scheme_id=uuid4(),
            cardinality="single",
        )

        with pytest.raises(SchemeNotInProjectError):
            await service.create_property(project.id, prop_in)


class TestListProperties:
    """Tests for PropertyService.list_properties."""

    @pytest.mark.asyncio
    async def test_list_properties_empty(
        self, db_session: AsyncSession, project: Project, property_service: PropertyService
    ) -> None:
        """Test listing properties when none exist."""
        service = property_service
        properties = await service.list_properties(project.id)
        assert properties == []

    @pytest.mark.asyncio
    async def test_list_properties_returns_all_for_project(
        self, db_session: AsyncSession, project: Project, property_service: PropertyService
    ) -> None:
        """Test listing returns all properties for a project."""
        service = property_service

        # Create two properties
        prop1_in = PropertyCreate(
            identifier="prop1",
            label="Property 1",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        prop2_in = PropertyCreate(
            identifier="prop2",
            label="Property 2",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:integer",
            cardinality="multiple",
        )
        await service.create_property(project.id, prop1_in)
        await service.create_property(project.id, prop2_in)

        properties = await service.list_properties(project.id)
        assert len(properties) == 2
        identifiers = {p.identifier for p in properties}
        assert identifiers == {"prop1", "prop2"}

    @pytest.mark.asyncio
    async def test_list_properties_excludes_other_projects(
        self, db_session: AsyncSession, project: Project, other_project: Project, property_service: PropertyService
    ) -> None:
        """Test that listing only returns properties for the specified project."""
        service = property_service

        # Create property in each project
        prop1_in = PropertyCreate(
            identifier="prop1",
            label="Property 1",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        prop2_in = PropertyCreate(
            identifier="prop2",
            label="Property 2",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        await service.create_property(project.id, prop1_in)
        await service.create_property(other_project.id, prop2_in)

        properties = await service.list_properties(project.id)
        assert len(properties) == 1
        assert properties[0].identifier == "prop1"

    @pytest.mark.asyncio
    async def test_list_properties_project_not_found(
        self, db_session: AsyncSession, property_service: PropertyService
    ) -> None:
        """Test that listing properties for non-existent project raises error."""
        service = property_service
        with pytest.raises(ProjectNotFoundError):
            await service.list_properties(uuid4())


class TestGetProperty:
    """Tests for PropertyService.get_property."""

    @pytest.mark.asyncio
    async def test_get_property_success(
        self, db_session: AsyncSession, project: Project, property_service: PropertyService
    ) -> None:
        """Test getting a property by ID."""
        service = property_service
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test Property",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        created = await service.create_property(project.id, prop_in)

        prop = await service.get_property(created.id)
        assert prop is not None
        assert prop.id == created.id
        assert prop.identifier == "testProp"

    @pytest.mark.asyncio
    async def test_get_property_not_found(
        self, db_session: AsyncSession, property_service: PropertyService
    ) -> None:
        """Test that getting a non-existent property returns None."""
        service = property_service
        prop = await service.get_property(uuid4())
        assert prop is None


class TestUpdateProperty:
    """Tests for PropertyService.update_property."""

    @pytest.mark.asyncio
    async def test_update_property_label(
        self, db_session: AsyncSession, project: Project, property_service: PropertyService
    ) -> None:
        """Test updating a property's label."""
        service = property_service
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Original Label",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        created = await service.create_property(project.id, prop_in)

        update = PropertyUpdate(label="Updated Label")
        updated = await service.update_property(created.id, update)

        assert updated is not None
        assert updated.label == "Updated Label"
        assert updated.identifier == "testProp"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_property_description(
        self, db_session: AsyncSession, project: Project, property_service: PropertyService
    ) -> None:
        """Test updating a property's description."""
        service = property_service
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        created = await service.create_property(project.id, prop_in)

        update = PropertyUpdate(description="New description")
        updated = await service.update_property(created.id, update)

        assert updated is not None
        assert updated.description == "New description"

    @pytest.mark.asyncio
    async def test_update_property_required(
        self, db_session: AsyncSession, project: Project, property_service: PropertyService
    ) -> None:
        """Test updating a property's required flag."""
        service = property_service
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
            required=False,
        )
        created = await service.create_property(project.id, prop_in)

        update = PropertyUpdate(required=True)
        updated = await service.update_property(created.id, update)

        assert updated is not None
        assert updated.required is True

    @pytest.mark.asyncio
    async def test_update_property_not_found(
        self, db_session: AsyncSession, property_service: PropertyService
    ) -> None:
        """Test that updating a non-existent property returns None."""
        service = property_service
        update = PropertyUpdate(label="New Label")
        result = await service.update_property(uuid4(), update)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_property_change_range_scheme(
        self, db_session: AsyncSession, project: Project, scheme: ConceptScheme, property_service: PropertyService
    ) -> None:
        """Test updating a property to use a different range scheme."""
        # Create a second scheme
        scheme2 = ConceptScheme(
            project_id=project.id,
            title="Second Scheme",
            uri="http://example.org/schemes/second",
        )
        db_session.add(scheme2)
        await db_session.flush()
        await db_session.refresh(scheme2)

        service = property_service
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_scheme_id=scheme.id,
            cardinality="single",
        )
        created = await service.create_property(project.id, prop_in)

        update = PropertyUpdate(range_scheme_id=scheme2.id)
        updated = await service.update_property(created.id, update)

        assert updated is not None
        assert updated.range_scheme_id == scheme2.id

    @pytest.mark.asyncio
    async def test_update_property_change_from_scheme_to_datatype(
        self, db_session: AsyncSession, project: Project, scheme: ConceptScheme, property_service: PropertyService
    ) -> None:
        """Test updating from range_scheme_id to range_datatype."""
        service = property_service
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_scheme_id=scheme.id,
            cardinality="single",
        )
        created = await service.create_property(project.id, prop_in)

        # Clear scheme, set datatype
        update = PropertyUpdate(range_scheme_id=None, range_datatype="xsd:string")
        updated = await service.update_property(created.id, update)

        assert updated is not None
        assert updated.range_scheme_id is None
        assert updated.range_datatype == "xsd:string"

    @pytest.mark.asyncio
    async def test_update_property_change_to_range_class(
        self, db_session: AsyncSession, project: Project, property_service: PropertyService
    ) -> None:
        """Test updating from range_datatype to range_class."""
        service = property_service
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        created = await service.create_property(project.id, prop_in)

        update = PropertyUpdate(
            range_datatype=None,
            range_class="https://example.org/ontology/Foo",
        )
        updated = await service.update_property(created.id, update)

        assert updated is not None
        assert updated.range_class == "https://example.org/ontology/Foo"
        assert updated.range_datatype is None
        assert updated.range_scheme_id is None

    @pytest.mark.asyncio
    async def test_update_property_invalid_range_scheme(
        self, db_session: AsyncSession, project: Project, other_scheme: ConceptScheme, property_service: PropertyService
    ) -> None:
        """Test that updating to a scheme from another project raises error."""
        service = property_service
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        created = await service.create_property(project.id, prop_in)

        update = PropertyUpdate(range_scheme_id=other_scheme.id, range_datatype=None)
        with pytest.raises(SchemeNotInProjectError):
            await service.update_property(created.id, update)

    @pytest.mark.asyncio
    async def test_update_property_clearing_all_ranges_error(
        self, db_session: AsyncSession, project: Project, property_service: PropertyService
    ) -> None:
        """Test that clearing all range fields raises error at service level."""
        service = property_service
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        created = await service.create_property(project.id, prop_in)

        # Explicitly set both to None — schema allows (0 set), service rejects resulting state
        update = PropertyUpdate(range_scheme_id=None, range_datatype=None)
        with pytest.raises(InvalidRangeError):
            await service.update_property(created.id, update)


class TestDeleteProperty:
    """Tests for PropertyService.delete_property."""

    @pytest.mark.asyncio
    async def test_delete_property_success(
        self, db_session: AsyncSession, project: Project, property_service: PropertyService
    ) -> None:
        """Test deleting a property."""
        service = property_service
        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        created = await service.create_property(project.id, prop_in)

        result = await service.delete_property(created.id)
        assert result is True

        # Verify it's gone
        prop = await service.get_property(created.id)
        assert prop is None

    @pytest.mark.asyncio
    async def test_delete_property_not_found(
        self, db_session: AsyncSession, property_service: PropertyService
    ) -> None:
        """Test that deleting a non-existent property returns False."""
        service = property_service
        result = await service.delete_property(uuid4())
        assert result is False


class TestPropertyURI:
    """Tests for URI behavior on Property create/update."""

    @pytest.mark.asyncio
    async def test_create_computes_uri_from_namespace(
        self, project: Project, property_service: PropertyService
    ) -> None:
        """Create without explicit URI computes from project namespace."""
        prop_in = PropertyCreate(
            identifier="educationLevel",
            label="Education Level",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        prop = await property_service.create_property(project.id, prop_in)

        assert prop.uri == "https://example.org/vocab/educationLevel"

    @pytest.mark.asyncio
    async def test_create_with_explicit_uri_stores_as_is(
        self, project: Project, property_service: PropertyService
    ) -> None:
        """Create with explicit URI stores it directly (import path)."""
        prop_in = PropertyCreate(
            identifier="educationLevel",
            label="Education Level",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
            uri="https://external.org/props/educationLevel",
        )
        prop = await property_service.create_property(project.id, prop_in)

        assert prop.uri == "https://external.org/props/educationLevel"

    @pytest.mark.asyncio
    async def test_create_without_namespace_raises(
        self,
        db_session: AsyncSession,
        property_service: PropertyService,
    ) -> None:
        """Create without namespace and no explicit URI raises ProjectNamespaceRequiredError."""
        project_nn = Project(name="No Namespace")
        db_session.add(project_nn)
        await db_session.flush()
        await db_session.refresh(project_nn)

        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        with pytest.raises(ProjectNamespaceRequiredError):
            await property_service.create_property(project_nn.id, prop_in)

    @pytest.mark.asyncio
    async def test_create_with_explicit_uri_no_namespace_ok(
        self,
        db_session: AsyncSession,
        property_service: PropertyService,
    ) -> None:
        """Create with explicit URI works even without project namespace."""
        project_nn = Project(name="No Namespace")
        db_session.add(project_nn)
        await db_session.flush()
        await db_session.refresh(project_nn)

        prop_in = PropertyCreate(
            identifier="testProp",
            label="Test",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
            uri="https://external.org/props/testProp",
        )
        prop = await property_service.create_property(project_nn.id, prop_in)
        assert prop.uri == "https://external.org/props/testProp"

    @pytest.mark.asyncio
    async def test_update_identifier_does_not_change_uri(
        self, project: Project, property_service: PropertyService
    ) -> None:
        """URI is immutable — updating identifier does not change URI."""
        prop_in = PropertyCreate(
            identifier="educationLevel",
            label="Education Level",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        prop = await property_service.create_property(project.id, prop_in)
        original_uri = prop.uri

        update = PropertyUpdate(identifier="renamedProp")
        updated = await property_service.update_property(prop.id, update)

        assert updated is not None
        assert updated.identifier == "renamedProp"
        assert updated.uri == original_uri


class TestURICollision:
    """Tests for URI collision handling."""

    @pytest.mark.asyncio
    async def test_duplicate_uri_different_identifier_raises_uri_error(
        self, project: Project, property_service: PropertyService
    ) -> None:
        """Two properties with different identifiers but same URI raises PropertyURIExistsError."""
        prop_in1 = PropertyCreate(
            identifier="prop1",
            label="Property 1",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
            uri="https://example.org/vocab/sharedUri",
        )
        await property_service.create_property(project.id, prop_in1)

        prop_in2 = PropertyCreate(
            identifier="prop2",
            label="Property 2",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:integer",
            cardinality="single",
            uri="https://example.org/vocab/sharedUri",
        )
        with pytest.raises(PropertyURIExistsError):
            await property_service.create_property(project.id, prop_in2)
