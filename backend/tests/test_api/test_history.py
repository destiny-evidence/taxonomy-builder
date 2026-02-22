"""Tests for the history API."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.concept import ConceptCreate
from taxonomy_builder.schemas.property import PropertyCreate
from taxonomy_builder.services.concept_scheme_service import ConceptSchemeService
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.project_service import ProjectService
from taxonomy_builder.services.property_service import PropertyService


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(name="Test Project", namespace="https://example.org/vocab/")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def scheme(db_session: AsyncSession, project: Project) -> ConceptScheme:
    """Create a concept scheme for testing."""
    scheme = ConceptScheme(
        project_id=project.id,
        title="Test Scheme",
        uri="http://example.org/concepts",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


@pytest.mark.asyncio
async def test_get_scheme_history(
    authenticated_client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test getting history for a scheme."""
    # Create some concepts to generate change events
    service = ConceptService(db_session)
    concept = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Dogs"),
    )
    await service.update_concept(
        concept_id=concept.id,
        concept_in=ConceptCreate(pref_label="Dogs Updated"),
    )

    # Get the history
    response = await authenticated_client.get(f"/api/schemes/{scheme.id}/history")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least create and update events

    # Events should be ordered by timestamp descending (most recent first)
    assert data[0]["action"] == "update"
    assert data[1]["action"] == "create"


@pytest.mark.asyncio
async def test_get_scheme_history_with_pagination(
    authenticated_client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test pagination for scheme history."""
    # Create multiple concepts to generate change events
    service = ConceptService(db_session)
    for i in range(5):
        await service.create_concept(
            scheme_id=scheme.id,
            concept_in=ConceptCreate(pref_label=f"Concept {i}"),
        )

    # Test limit
    response = await authenticated_client.get(f"/api/schemes/{scheme.id}/history?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Test offset
    response = await authenticated_client.get(f"/api/schemes/{scheme.id}/history?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_concept_history(
    authenticated_client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test getting history for a specific concept."""
    # Create and update a concept
    service = ConceptService(db_session)
    concept = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Dogs"),
    )
    await service.update_concept(
        concept_id=concept.id,
        concept_in=ConceptCreate(pref_label="Dogs Updated"),
    )

    # Get the concept history
    response = await authenticated_client.get(f"/api/concepts/{concept.id}/history")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2  # Exactly create and update events

    # Events should be ordered by timestamp descending (most recent first)
    assert data[0]["action"] == "update"
    assert data[0]["entity_id"] == str(concept.id)
    assert data[1]["action"] == "create"
    assert data[1]["entity_id"] == str(concept.id)


@pytest.mark.asyncio
async def test_get_scheme_history_includes_user_display_name(
    authenticated_client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that history response includes user_display_name field."""
    # Create a concept to generate a change event
    service = ConceptService(db_session)
    await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Test Concept"),
    )

    response = await authenticated_client.get(f"/api/schemes/{scheme.id}/history")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Verify user_display_name field is present
    assert "user_display_name" in data[0]


@pytest.mark.asyncio
async def test_get_scheme_history_null_user_returns_null_display_name(
    authenticated_client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that history with null user_id returns null for user_display_name."""
    # Create a concept without user context (simulates system change or deleted user)
    service = ConceptService(db_session)  # No user_id passed
    await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="System Concept"),
    )

    response = await authenticated_client.get(f"/api/schemes/{scheme.id}/history")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # user_display_name should be null when user_id is null
    assert data[0]["user_display_name"] is None


@pytest.mark.asyncio
async def test_get_scheme_history_shows_user_display_name(
    authenticated_client: AsyncClient, scheme: ConceptScheme
) -> None:
    """Test that history shows the display name of the user who made changes."""
    # Create a concept via API (which records user_id from authenticated user)
    response = await authenticated_client.post(
        f"/api/schemes/{scheme.id}/concepts",
        json={"pref_label": "Test Concept"},
    )
    assert response.status_code == 201

    # Get history - should show "Test User" (from test_user fixture)
    response = await authenticated_client.get(f"/api/schemes/{scheme.id}/history")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["user_display_name"] == "Test User"


# ============ Project history ============


@pytest.mark.asyncio
async def test_get_project_history(
    authenticated_client: AsyncClient, db_session: AsyncSession, project: Project
) -> None:
    """Test getting history for a project returns property change events."""
    service = PropertyService(db_session, ProjectService(db_session), ConceptSchemeService(db_session))
    prop = await service.create_property(
        project_id=project.id,
        property_in=PropertyCreate(
            identifier="birthDate",
            label="Birth Date",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:date",
            cardinality="single",
        ),
    )
    await service.update_property(
        property_id=prop.id,
        property_in=PropertyCreate(
            identifier="birthDate",
            label="Date of Birth",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:date",
            cardinality="single",
        ),
    )

    response = await authenticated_client.get(f"/api/projects/{project.id}/history")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least create and update events
    # Most recent first
    assert data[0]["action"] == "update"
    assert data[0]["entity_type"] == "property"
    assert data[0]["project_id"] == str(project.id)
    assert data[1]["action"] == "create"
    assert data[1]["entity_type"] == "property"
    assert data[1]["project_id"] == str(project.id)


@pytest.mark.asyncio
async def test_get_project_history_with_pagination(
    authenticated_client: AsyncClient, db_session: AsyncSession, project: Project
) -> None:
    """Test pagination for project history."""
    service = PropertyService(db_session, ProjectService(db_session), ConceptSchemeService(db_session))
    for i in range(5):
        await service.create_property(
            project_id=project.id,
            property_in=PropertyCreate(
                identifier=f"prop{i}",
                label=f"Property {i}",
                domain_class="https://evrepo.example.org/vocab/Finding",
                range_datatype="xsd:string",
                cardinality="single",
            ),
        )

    response = await authenticated_client.get(
        f"/api/projects/{project.id}/history?limit=2"
    )
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = await authenticated_client.get(
        f"/api/projects/{project.id}/history?limit=2&offset=2"
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


# ============ Property history ============


@pytest.mark.asyncio
async def test_get_property_history(
    authenticated_client: AsyncClient, db_session: AsyncSession, project: Project
) -> None:
    """Test getting history for a specific property."""
    service = PropertyService(db_session, ProjectService(db_session), ConceptSchemeService(db_session))
    prop = await service.create_property(
        project_id=project.id,
        property_in=PropertyCreate(
            identifier="birthDate",
            label="Birth Date",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:date",
            cardinality="single",
        ),
    )
    await service.update_property(
        property_id=prop.id,
        property_in=PropertyCreate(
            identifier="birthDate",
            label="Date of Birth",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:date",
            cardinality="single",
        ),
    )

    response = await authenticated_client.get(f"/api/properties/{prop.id}/history")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["action"] == "update"
    assert data[0]["entity_id"] == str(prop.id)
    assert data[1]["action"] == "create"
    assert data[1]["entity_id"] == str(prop.id)


