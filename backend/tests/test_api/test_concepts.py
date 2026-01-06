"""Tests for Concept API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_broader import ConceptBroader
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
    scheme = ConceptScheme(
        project_id=project.id,
        title="Test Scheme",
        uri="http://example.org/concepts",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


@pytest.fixture
async def concept(db_session: AsyncSession, scheme: ConceptScheme) -> Concept:
    """Create a concept for testing."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Test Concept",
        identifier="test",
        definition="A test concept",
        scope_note="For testing",
    )
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)
    return concept


# List concepts tests


@pytest.mark.asyncio
async def test_list_concepts_empty(client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test listing concepts when none exist."""
    response = await client.get(f"/api/schemes/{scheme.id}/concepts")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_concepts(client: AsyncClient, scheme: ConceptScheme, concept: Concept) -> None:
    """Test listing concepts returns all concepts for scheme."""
    response = await client.get(f"/api/schemes/{scheme.id}/concepts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(concept.id)
    assert data[0]["pref_label"] == "Test Concept"


@pytest.mark.asyncio
async def test_list_concepts_alphabetical(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that concepts are returned in alphabetical order."""
    concept_z = Concept(scheme_id=scheme.id, pref_label="Zebra")
    concept_a = Concept(scheme_id=scheme.id, pref_label="Apple")
    concept_m = Concept(scheme_id=scheme.id, pref_label="Mango")
    db_session.add_all([concept_z, concept_a, concept_m])
    await db_session.flush()

    response = await client.get(f"/api/schemes/{scheme.id}/concepts")
    assert response.status_code == 200
    data = response.json()
    labels = [c["pref_label"] for c in data]
    assert labels == ["Apple", "Mango", "Zebra"]


@pytest.mark.asyncio
async def test_list_concepts_scheme_not_found(client: AsyncClient) -> None:
    """Test listing concepts for non-existent scheme."""
    response = await client.get(f"/api/schemes/{uuid4()}/concepts")
    assert response.status_code == 404


# Create concept tests


@pytest.mark.asyncio
async def test_create_concept(client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test creating a new concept."""
    response = await client.post(
        f"/api/schemes/{scheme.id}/concepts",
        json={
            "pref_label": "New Concept",
            "identifier": "new",
            "definition": "A new concept",
            "scope_note": "Use for new things",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["pref_label"] == "New Concept"
    assert data["identifier"] == "new"
    assert data["definition"] == "A new concept"
    assert data["scheme_id"] == str(scheme.id)
    assert data["uri"] == "http://example.org/concepts/new"  # Computed URI
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_concept_pref_label_only(client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test creating a concept with only pref_label."""
    response = await client.post(
        f"/api/schemes/{scheme.id}/concepts",
        json={"pref_label": "Minimal Concept"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["pref_label"] == "Minimal Concept"
    assert data["definition"] is None


@pytest.mark.asyncio
async def test_create_concept_empty_pref_label(client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test creating a concept with empty pref_label fails."""
    response = await client.post(
        f"/api/schemes/{scheme.id}/concepts",
        json={"pref_label": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_concept_scheme_not_found(client: AsyncClient) -> None:
    """Test creating a concept for non-existent scheme."""
    response = await client.post(
        f"/api/schemes/{uuid4()}/concepts",
        json={"pref_label": "New Concept"},
    )
    assert response.status_code == 404


# Get concept tests


@pytest.mark.asyncio
async def test_get_concept(client: AsyncClient, concept: Concept) -> None:
    """Test getting a single concept."""
    response = await client.get(f"/api/concepts/{concept.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(concept.id)
    assert data["pref_label"] == "Test Concept"
    assert data["broader"] == []


@pytest.mark.asyncio
async def test_get_concept_with_broader(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme, concept: Concept
) -> None:
    """Test getting a concept includes its broader concepts."""
    # Create a broader concept
    broader = Concept(scheme_id=scheme.id, pref_label="Broader Concept")
    db_session.add(broader)
    await db_session.flush()

    # Add broader relationship
    rel = ConceptBroader(concept_id=concept.id, broader_concept_id=broader.id)
    db_session.add(rel)
    await db_session.flush()

    response = await client.get(f"/api/concepts/{concept.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["broader"]) == 1
    assert data["broader"][0]["pref_label"] == "Broader Concept"


@pytest.mark.asyncio
async def test_get_concept_not_found(client: AsyncClient) -> None:
    """Test getting a non-existent concept."""
    response = await client.get(f"/api/concepts/{uuid4()}")
    assert response.status_code == 404


# Update concept tests


@pytest.mark.asyncio
async def test_update_concept(client: AsyncClient, concept: Concept) -> None:
    """Test updating a concept."""
    response = await client.put(
        f"/api/concepts/{concept.id}",
        json={
            "pref_label": "Updated Concept",
            "definition": "Updated definition",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pref_label"] == "Updated Concept"
    assert data["definition"] == "Updated definition"


@pytest.mark.asyncio
async def test_update_concept_partial(client: AsyncClient, concept: Concept) -> None:
    """Test partial update of a concept."""
    response = await client.put(
        f"/api/concepts/{concept.id}",
        json={"definition": "Only definition changed"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pref_label"] == "Test Concept"  # Unchanged
    assert data["definition"] == "Only definition changed"


@pytest.mark.asyncio
async def test_update_concept_not_found(client: AsyncClient) -> None:
    """Test updating a non-existent concept."""
    response = await client.put(
        f"/api/concepts/{uuid4()}",
        json={"pref_label": "New Label"},
    )
    assert response.status_code == 404


# Delete concept tests


@pytest.mark.asyncio
async def test_delete_concept(client: AsyncClient, concept: Concept) -> None:
    """Test deleting a concept."""
    response = await client.delete(f"/api/concepts/{concept.id}")
    assert response.status_code == 204

    # Verify it's deleted
    response = await client.get(f"/api/concepts/{concept.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_concept_not_found(client: AsyncClient) -> None:
    """Test deleting a non-existent concept."""
    response = await client.delete(f"/api/concepts/{uuid4()}")
    assert response.status_code == 404


# Broader relationship tests


@pytest.mark.asyncio
async def test_add_broader(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme, concept: Concept
) -> None:
    """Test adding a broader relationship."""
    broader = Concept(scheme_id=scheme.id, pref_label="Broader Concept")
    db_session.add(broader)
    await db_session.flush()
    await db_session.refresh(broader)

    response = await client.post(
        f"/api/concepts/{concept.id}/broader",
        json={"broader_concept_id": str(broader.id)},
    )
    assert response.status_code == 201

    # Verify the relationship
    response = await client.get(f"/api/concepts/{concept.id}")
    data = response.json()
    assert len(data["broader"]) == 1
    assert data["broader"][0]["id"] == str(broader.id)


@pytest.mark.asyncio
async def test_add_broader_concept_not_found(client: AsyncClient, concept: Concept) -> None:
    """Test adding broader when narrower concept doesn't exist."""
    response = await client.post(
        f"/api/concepts/{uuid4()}/broader",
        json={"broader_concept_id": str(concept.id)},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_broader_broader_not_found(client: AsyncClient, concept: Concept) -> None:
    """Test adding broader when broader concept doesn't exist."""
    response = await client.post(
        f"/api/concepts/{concept.id}/broader",
        json={"broader_concept_id": str(uuid4())},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_broader_duplicate(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme, concept: Concept
) -> None:
    """Test adding duplicate broader relationship fails."""
    broader = Concept(scheme_id=scheme.id, pref_label="Broader Concept")
    db_session.add(broader)
    await db_session.flush()
    rel = ConceptBroader(concept_id=concept.id, broader_concept_id=broader.id)
    db_session.add(rel)
    await db_session.flush()

    response = await client.post(
        f"/api/concepts/{concept.id}/broader",
        json={"broader_concept_id": str(broader.id)},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_remove_broader(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme, concept: Concept
) -> None:
    """Test removing a broader relationship."""
    broader = Concept(scheme_id=scheme.id, pref_label="Broader Concept")
    db_session.add(broader)
    await db_session.flush()
    rel = ConceptBroader(concept_id=concept.id, broader_concept_id=broader.id)
    db_session.add(rel)
    await db_session.flush()
    await db_session.refresh(broader)

    response = await client.delete(f"/api/concepts/{concept.id}/broader/{broader.id}")
    assert response.status_code == 204

    # Verify the relationship is removed
    response = await client.get(f"/api/concepts/{concept.id}")
    data = response.json()
    assert len(data["broader"]) == 0


@pytest.mark.asyncio
async def test_remove_broader_not_found(client: AsyncClient, concept: Concept) -> None:
    """Test removing a non-existent broader relationship."""
    response = await client.delete(f"/api/concepts/{concept.id}/broader/{uuid4()}")
    assert response.status_code == 404


# Tree endpoint tests


@pytest.mark.asyncio
async def test_get_tree_empty(client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test getting tree when no concepts exist."""
    response = await client.get(f"/api/schemes/{scheme.id}/tree")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_tree_flat(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test getting tree with only root concepts."""
    concept1 = Concept(scheme_id=scheme.id, pref_label="Root 1")
    concept2 = Concept(scheme_id=scheme.id, pref_label="Root 2")
    db_session.add_all([concept1, concept2])
    await db_session.flush()

    response = await client.get(f"/api/schemes/{scheme.id}/tree")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    labels = {c["pref_label"] for c in data}
    assert labels == {"Root 1", "Root 2"}


@pytest.mark.asyncio
async def test_get_tree_with_hierarchy(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test getting tree with parent-child relationships."""
    parent = Concept(scheme_id=scheme.id, pref_label="Parent")
    child = Concept(scheme_id=scheme.id, pref_label="Child")
    db_session.add_all([parent, child])
    await db_session.flush()

    rel = ConceptBroader(concept_id=child.id, broader_concept_id=parent.id)
    db_session.add(rel)
    await db_session.flush()

    response = await client.get(f"/api/schemes/{scheme.id}/tree")
    assert response.status_code == 200
    data = response.json()

    # Only parent should be at root level
    assert len(data) == 1
    assert data[0]["pref_label"] == "Parent"
    assert len(data[0]["narrower"]) == 1
    assert data[0]["narrower"][0]["pref_label"] == "Child"


@pytest.mark.asyncio
async def test_get_tree_polyhierarchy(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that concept appears under all parents in tree (DAG)."""
    mammals = Concept(scheme_id=scheme.id, pref_label="Mammals")
    pets = Concept(scheme_id=scheme.id, pref_label="Pets")
    dogs = Concept(scheme_id=scheme.id, pref_label="Dogs")
    db_session.add_all([mammals, pets, dogs])
    await db_session.flush()

    # Dogs is both a Mammal and a Pet
    rel1 = ConceptBroader(concept_id=dogs.id, broader_concept_id=mammals.id)
    rel2 = ConceptBroader(concept_id=dogs.id, broader_concept_id=pets.id)
    db_session.add_all([rel1, rel2])
    await db_session.flush()

    response = await client.get(f"/api/schemes/{scheme.id}/tree")
    assert response.status_code == 200
    data = response.json()

    # Should have 2 root concepts (Mammals and Pets)
    assert len(data) == 2
    root_labels = {c["pref_label"] for c in data}
    assert root_labels == {"Mammals", "Pets"}

    # Dogs should appear under both
    for root in data:
        assert len(root["narrower"]) == 1
        assert root["narrower"][0]["pref_label"] == "Dogs"


@pytest.mark.asyncio
async def test_get_tree_scheme_not_found(client: AsyncClient) -> None:
    """Test getting tree for non-existent scheme."""
    response = await client.get(f"/api/schemes/{uuid4()}/tree")
    assert response.status_code == 404


# Alt labels tests


@pytest.mark.asyncio
async def test_create_concept_with_alt_labels(client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test creating a concept with alt labels."""
    response = await client.post(
        f"/api/schemes/{scheme.id}/concepts",
        json={
            "pref_label": "Dogs",
            "alt_labels": ["Canines", "Domestic dogs"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["alt_labels"] == ["Canines", "Domestic dogs"]


@pytest.mark.asyncio
async def test_create_concept_alt_labels_default(client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test that alt_labels defaults to empty list."""
    response = await client.post(
        f"/api/schemes/{scheme.id}/concepts",
        json={"pref_label": "Test Concept"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["alt_labels"] == []


@pytest.mark.asyncio
async def test_get_concept_includes_alt_labels(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that getting a concept includes alt labels."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Animals",
        alt_labels=["Fauna", "Living things"],
    )
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)

    response = await client.get(f"/api/concepts/{concept.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["alt_labels"] == ["Fauna", "Living things"]


@pytest.mark.asyncio
async def test_update_concept_alt_labels(client: AsyncClient, concept: Concept) -> None:
    """Test updating concept alt labels."""
    response = await client.put(
        f"/api/concepts/{concept.id}",
        json={"alt_labels": ["New Synonym", "Another Synonym"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["alt_labels"] == ["New Synonym", "Another Synonym"]


@pytest.mark.asyncio
async def test_update_concept_clear_alt_labels(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test clearing alt labels by setting to empty list."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Test",
        alt_labels=["Label 1", "Label 2"],
    )
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)

    response = await client.put(
        f"/api/concepts/{concept.id}",
        json={"alt_labels": []},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["alt_labels"] == []


@pytest.mark.asyncio
async def test_update_concept_without_alt_labels_preserves_existing(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that updating without alt_labels preserves existing labels."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Test",
        alt_labels=["Existing Label"],
    )
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)

    response = await client.put(
        f"/api/concepts/{concept.id}",
        json={"definition": "New definition"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["alt_labels"] == ["Existing Label"]


@pytest.mark.asyncio
async def test_list_concepts_includes_alt_labels(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that listing concepts includes alt labels."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Test",
        alt_labels=["Synonym"],
    )
    db_session.add(concept)
    await db_session.flush()

    response = await client.get(f"/api/schemes/{scheme.id}/concepts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["alt_labels"] == ["Synonym"]


@pytest.mark.asyncio
async def test_tree_includes_alt_labels(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that tree endpoint includes alt labels."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Root",
        alt_labels=["Base", "Top"],
    )
    db_session.add(concept)
    await db_session.flush()

    response = await client.get(f"/api/schemes/{scheme.id}/tree")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["alt_labels"] == ["Base", "Top"]
