"""Tests for the history API."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.concept import ConceptCreate
from taxonomy_builder.services.concept_service import ConceptService


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(name="Test Project")
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
async def test_get_scheme_history_not_found(authenticated_client: AsyncClient) -> None:
    """Test 404 for non-existent scheme."""
    response = await authenticated_client.get(f"/api/schemes/{uuid4()}/history")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_concept_history_not_found(authenticated_client: AsyncClient) -> None:
    """Test 404 for non-existent concept."""
    response = await authenticated_client.get(f"/api/concepts/{uuid4()}/history")
    assert response.status_code == 404
