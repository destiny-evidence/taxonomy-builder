"""Tests for Related relationship API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_related import ConceptRelated
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project


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
    scheme = ConceptScheme(project_id=project.id, title="Test Scheme")
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


@pytest.fixture
async def scheme2(db_session: AsyncSession, project: Project) -> ConceptScheme:
    """Create a second concept scheme for testing."""
    scheme = ConceptScheme(project_id=project.id, title="Other Scheme")
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


@pytest.fixture
async def concepts(db_session: AsyncSession, scheme: ConceptScheme) -> list[Concept]:
    """Create multiple concepts for testing."""
    dogs = Concept(scheme_id=scheme.id, pref_label="Dogs")
    cats = Concept(scheme_id=scheme.id, pref_label="Cats")
    vet_medicine = Concept(scheme_id=scheme.id, pref_label="Veterinary Medicine")
    db_session.add_all([dogs, cats, vet_medicine])
    await db_session.flush()
    for c in [dogs, cats, vet_medicine]:
        await db_session.refresh(c)
    return [dogs, cats, vet_medicine]


@pytest.fixture
async def concept_other_scheme(db_session: AsyncSession, scheme2: ConceptScheme) -> Concept:
    """Create a concept in a different scheme."""
    concept = Concept(scheme_id=scheme2.id, pref_label="Other Concept")
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)
    return concept


# Add related tests


@pytest.mark.asyncio
async def test_add_related_returns_201(
    client: AsyncClient, concepts: list[Concept]
) -> None:
    """Test that adding a related relationship returns 201."""
    dogs, cats, vet_medicine = concepts

    response = await client.post(
        f"/api/concepts/{dogs.id}/related",
        json={"related_concept_id": str(cats.id)},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_add_related_concept_not_found_returns_404(
    client: AsyncClient, concepts: list[Concept]
) -> None:
    """Test adding related when concept doesn't exist."""
    dogs, cats, vet_medicine = concepts

    response = await client.post(
        f"/api/concepts/{uuid4()}/related",
        json={"related_concept_id": str(cats.id)},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_related_related_not_found_returns_404(
    client: AsyncClient, concepts: list[Concept]
) -> None:
    """Test adding related when related concept doesn't exist."""
    dogs, cats, vet_medicine = concepts

    response = await client.post(
        f"/api/concepts/{dogs.id}/related",
        json={"related_concept_id": str(uuid4())},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_related_duplicate_returns_409(
    client: AsyncClient, db_session: AsyncSession, concepts: list[Concept]
) -> None:
    """Test adding duplicate related relationship fails."""
    dogs, cats, vet_medicine = concepts

    # Create existing relationship (ordered)
    id1, id2 = (dogs.id, cats.id) if dogs.id < cats.id else (cats.id, dogs.id)
    rel = ConceptRelated(concept_id=id1, related_concept_id=id2)
    db_session.add(rel)
    await db_session.flush()

    response = await client.post(
        f"/api/concepts/{dogs.id}/related",
        json={"related_concept_id": str(cats.id)},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_add_related_self_reference_returns_400(
    client: AsyncClient, concepts: list[Concept]
) -> None:
    """Test adding self-referencing related relationship fails."""
    dogs, cats, vet_medicine = concepts

    response = await client.post(
        f"/api/concepts/{dogs.id}/related",
        json={"related_concept_id": str(dogs.id)},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_add_related_different_scheme_returns_400(
    client: AsyncClient, concepts: list[Concept], concept_other_scheme: Concept
) -> None:
    """Test adding related between different schemes fails."""
    dogs, cats, vet_medicine = concepts

    response = await client.post(
        f"/api/concepts/{dogs.id}/related",
        json={"related_concept_id": str(concept_other_scheme.id)},
    )
    assert response.status_code == 400


# Remove related tests


@pytest.mark.asyncio
async def test_remove_related_returns_204(
    client: AsyncClient, db_session: AsyncSession, concepts: list[Concept]
) -> None:
    """Test that removing a related relationship returns 204."""
    dogs, cats, vet_medicine = concepts

    # Create existing relationship (ordered)
    id1, id2 = (dogs.id, cats.id) if dogs.id < cats.id else (cats.id, dogs.id)
    rel = ConceptRelated(concept_id=id1, related_concept_id=id2)
    db_session.add(rel)
    await db_session.flush()

    response = await client.delete(f"/api/concepts/{dogs.id}/related/{cats.id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_remove_related_not_found_returns_404(
    client: AsyncClient, concepts: list[Concept]
) -> None:
    """Test removing non-existent related relationship."""
    dogs, cats, vet_medicine = concepts

    response = await client.delete(f"/api/concepts/{dogs.id}/related/{cats.id}")
    assert response.status_code == 404


# Get concept with related tests


@pytest.mark.asyncio
async def test_get_concept_includes_related_in_response(
    client: AsyncClient, db_session: AsyncSession, concepts: list[Concept]
) -> None:
    """Test getting a concept includes its related concepts."""
    dogs, cats, vet_medicine = concepts

    # Create related relationships
    id1, id2 = (dogs.id, cats.id) if dogs.id < cats.id else (cats.id, dogs.id)
    rel = ConceptRelated(concept_id=id1, related_concept_id=id2)
    db_session.add(rel)
    await db_session.flush()

    response = await client.get(f"/api/concepts/{dogs.id}")
    assert response.status_code == 200
    data = response.json()

    assert "related" in data
    assert len(data["related"]) == 1
    assert data["related"][0]["pref_label"] == "Cats"


@pytest.mark.asyncio
async def test_get_concept_related_is_symmetric(
    client: AsyncClient, db_session: AsyncSession, concepts: list[Concept]
) -> None:
    """Test that related concepts appear from both sides."""
    dogs, cats, vet_medicine = concepts

    # Create related relationship
    id1, id2 = (dogs.id, cats.id) if dogs.id < cats.id else (cats.id, dogs.id)
    rel = ConceptRelated(concept_id=id1, related_concept_id=id2)
    db_session.add(rel)
    await db_session.flush()

    # Check from dogs side
    response = await client.get(f"/api/concepts/{dogs.id}")
    dogs_data = response.json()
    assert len(dogs_data["related"]) == 1
    assert dogs_data["related"][0]["pref_label"] == "Cats"

    # Check from cats side
    response = await client.get(f"/api/concepts/{cats.id}")
    cats_data = response.json()
    assert len(cats_data["related"]) == 1
    assert cats_data["related"][0]["pref_label"] == "Dogs"
