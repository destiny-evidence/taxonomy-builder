"""Tests for ConceptScheme API endpoints."""

from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.ontology_class import OntologyClass
from taxonomy_builder.models.project import Project


@pytest.fixture
async def scheme(db_session: AsyncSession, project: Project) -> ConceptScheme:
    """Create a concept scheme for testing."""
    scheme = ConceptScheme(
        project_id=project.id,
        title="Test Scheme",
        description="A test scheme",
        uri="http://example.org/schemes/test",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


# List schemes tests


@pytest.mark.asyncio
async def test_list_schemes_empty(authenticated_client: AsyncClient, project: Project) -> None:
    """Test listing schemes when none exist."""
    response = await authenticated_client.get(f"/api/projects/{project.id}/schemes")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_schemes(
    authenticated_client: AsyncClient,
    project: Project,
    scheme: ConceptScheme,
) -> None:
    """Test listing schemes returns all schemes for project."""
    response = await authenticated_client.get(f"/api/projects/{project.id}/schemes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(scheme.id)
    assert data[0]["title"] == "Test Scheme"


@pytest.mark.asyncio
async def test_list_schemes_project_not_found(authenticated_client: AsyncClient) -> None:
    """Test listing schemes for non-existent project."""
    response = await authenticated_client.get(f"/api/projects/{uuid4()}/schemes")
    assert response.status_code == 404


# Create scheme tests


@pytest.mark.asyncio
async def test_create_scheme(authenticated_client: AsyncClient, project: Project) -> None:
    """Test creating a new scheme."""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/schemes",
        json={
            "title": "New Scheme",
            "description": "A new scheme",
            "uri": "http://example.org/new",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Scheme"
    assert data["description"] == "A new scheme"
    assert data["uri"] == "http://example.org/new"
    assert data["project_id"] == str(project.id)
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_scheme_title_only(
    authenticated_client: AsyncClient,
    project: Project,
) -> None:
    """Test creating a scheme with only title."""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/schemes",
        json={"title": "Minimal Scheme"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Minimal Scheme"
    assert data["description"] is None
    assert data["uri"] is None


@pytest.mark.asyncio
async def test_create_scheme_duplicate_title(
    authenticated_client: AsyncClient, project: Project, scheme: ConceptScheme
) -> None:
    """Test creating a scheme with duplicate title fails."""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/schemes",
        json={"title": "Test Scheme"},  # Same as existing scheme
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_scheme_empty_title(
    authenticated_client: AsyncClient,
    project: Project,
) -> None:
    """Test creating a scheme with empty title fails."""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/schemes",
        json={"title": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_scheme_project_not_found(authenticated_client: AsyncClient) -> None:
    """Test creating a scheme for non-existent project."""
    response = await authenticated_client.post(
        f"/api/projects/{uuid4()}/schemes",
        json={"title": "New Scheme"},
    )
    assert response.status_code == 404


# Get scheme tests


@pytest.mark.asyncio
async def test_get_scheme(authenticated_client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test getting a single scheme."""
    response = await authenticated_client.get(f"/api/schemes/{scheme.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(scheme.id)
    assert data["title"] == "Test Scheme"
    assert data["description"] == "A test scheme"


@pytest.mark.asyncio
async def test_get_scheme_not_found(authenticated_client: AsyncClient) -> None:
    """Test getting a non-existent scheme."""
    response = await authenticated_client.get(f"/api/schemes/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_scheme_invalid_uuid(authenticated_client: AsyncClient) -> None:
    """Test getting a scheme with invalid UUID."""
    response = await authenticated_client.get("/api/schemes/not-a-uuid")
    assert response.status_code == 422


# Update scheme tests


@pytest.mark.asyncio
async def test_update_scheme(authenticated_client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test updating a scheme."""
    response = await authenticated_client.put(
        f"/api/schemes/{scheme.id}",
        json={
            "title": "Updated Scheme",
            "description": "Updated description",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Scheme"
    assert data["description"] == "Updated description"
    # Other fields should remain unchanged
    assert data["uri"] == "http://example.org/schemes/test"


@pytest.mark.asyncio
async def test_update_scheme_partial(
    authenticated_client: AsyncClient,
    scheme: ConceptScheme,
) -> None:
    """Test partial update of a scheme."""
    response = await authenticated_client.put(
        f"/api/schemes/{scheme.id}",
        json={"description": "Only description changed"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Scheme"  # Unchanged
    assert data["description"] == "Only description changed"


@pytest.mark.asyncio
async def test_update_scheme_not_found(authenticated_client: AsyncClient) -> None:
    """Test updating a non-existent scheme."""
    response = await authenticated_client.put(
        f"/api/schemes/{uuid4()}",
        json={"title": "New Title"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_scheme_duplicate_title(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    project: Project,
    scheme: ConceptScheme,
) -> None:
    """Test updating scheme to duplicate title fails."""
    # Create another scheme
    scheme2 = ConceptScheme(project_id=project.id, title="Another Scheme")
    db_session.add(scheme2)
    await db_session.flush()

    # Try to rename it to the same title as the first scheme
    response = await authenticated_client.put(
        f"/api/schemes/{scheme2.id}",
        json={"title": "Test Scheme"},
    )
    assert response.status_code == 409


# Delete scheme tests


@pytest.mark.asyncio
async def test_delete_scheme(authenticated_client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test deleting a scheme."""
    response = await authenticated_client.delete(f"/api/schemes/{scheme.id}")
    assert response.status_code == 204

    # Verify it's deleted
    response = await authenticated_client.get(f"/api/schemes/{scheme.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_scheme_not_found(authenticated_client: AsyncClient) -> None:
    """Test deleting a non-existent scheme."""
    response = await authenticated_client.delete(f"/api/schemes/{uuid4()}")
    assert response.status_code == 404


# Ordering / position tests


async def _create_scheme(client: AsyncClient, project_id: UUID, title: str) -> dict:
    """Create a scheme via the API and return its JSON body."""
    response = await client.post(
        f"/api/projects/{project_id}/schemes",
        json={"title": title},
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_create_scheme_appends_position(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """New schemes get sequential positions, appended to the end."""
    a = await _create_scheme(authenticated_client, project.id, "A")
    b = await _create_scheme(authenticated_client, project.id, "B")
    c = await _create_scheme(authenticated_client, project.id, "C")

    assert a["position"] == 0
    assert b["position"] == 1
    assert c["position"] == 2


@pytest.mark.asyncio
async def test_list_schemes_ordered_by_position(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """Listing returns schemes in position order, not alphabetical."""
    # Create out of alphabetical order to prove position drives ordering.
    await _create_scheme(authenticated_client, project.id, "Zebra")
    await _create_scheme(authenticated_client, project.id, "Apple")

    response = await authenticated_client.get(f"/api/projects/{project.id}/schemes")
    assert response.status_code == 200
    data = response.json()
    assert [s["title"] for s in data] == ["Zebra", "Apple"]
    assert [s["position"] for s in data] == [0, 1]


@pytest.mark.asyncio
async def test_reorder_scheme_move_down(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """Moving a scheme to a higher index shifts the in-between schemes up."""
    a = await _create_scheme(authenticated_client, project.id, "A")
    await _create_scheme(authenticated_client, project.id, "B")
    await _create_scheme(authenticated_client, project.id, "C")

    response = await authenticated_client.put(
        f"/api/schemes/{a['id']}/position", json={"position": 2}
    )
    assert response.status_code == 200
    assert response.json()["position"] == 2

    data = (await authenticated_client.get(f"/api/projects/{project.id}/schemes")).json()
    assert [s["title"] for s in data] == ["B", "C", "A"]
    assert [s["position"] for s in data] == [0, 1, 2]


@pytest.mark.asyncio
async def test_reorder_scheme_move_up(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """Moving a scheme to a lower index shifts the in-between schemes down."""
    await _create_scheme(authenticated_client, project.id, "A")
    await _create_scheme(authenticated_client, project.id, "B")
    c = await _create_scheme(authenticated_client, project.id, "C")

    response = await authenticated_client.put(
        f"/api/schemes/{c['id']}/position", json={"position": 0}
    )
    assert response.status_code == 200
    assert response.json()["position"] == 0

    data = (await authenticated_client.get(f"/api/projects/{project.id}/schemes")).json()
    assert [s["title"] for s in data] == ["C", "A", "B"]
    assert [s["position"] for s in data] == [0, 1, 2]


@pytest.mark.asyncio
async def test_reorder_scheme_clamps_out_of_range(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """An out-of-range target index clamps to the last position without gaps."""
    a = await _create_scheme(authenticated_client, project.id, "A")
    await _create_scheme(authenticated_client, project.id, "B")
    await _create_scheme(authenticated_client, project.id, "C")

    response = await authenticated_client.put(
        f"/api/schemes/{a['id']}/position", json={"position": 99}
    )
    assert response.status_code == 200

    data = (await authenticated_client.get(f"/api/projects/{project.id}/schemes")).json()
    assert [s["title"] for s in data] == ["B", "C", "A"]
    assert [s["position"] for s in data] == [0, 1, 2]


@pytest.mark.asyncio
async def test_delete_scheme_closes_position_gap(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """Deleting a scheme re-closes the position sequence."""
    await _create_scheme(authenticated_client, project.id, "A")
    b = await _create_scheme(authenticated_client, project.id, "B")
    await _create_scheme(authenticated_client, project.id, "C")

    response = await authenticated_client.delete(f"/api/schemes/{b['id']}")
    assert response.status_code == 204

    data = (await authenticated_client.get(f"/api/projects/{project.id}/schemes")).json()
    assert [s["title"] for s in data] == ["A", "C"]
    assert [s["position"] for s in data] == [0, 1]


@pytest.mark.asyncio
async def test_reorder_scheme_not_found(authenticated_client: AsyncClient) -> None:
    """Reordering a non-existent scheme returns 404."""
    response = await authenticated_client.put(
        f"/api/schemes/{uuid4()}/position", json={"position": 0}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reorder_scheme_negative_position(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """A negative target index is rejected."""
    a = await _create_scheme(authenticated_client, project.id, "A")
    response = await authenticated_client.put(
        f"/api/schemes/{a['id']}/position", json={"position": -1}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_reorder_scheme_is_project_scoped(
    authenticated_client: AsyncClient, db_session: AsyncSession, project: Project
) -> None:
    """Reordering within one project does not affect another project's schemes."""
    other = Project(
        name="Other Project",
        namespace="https://example.org/other/",
        identifier_prefix="OTH",
    )
    db_session.add(other)
    await db_session.flush()

    await _create_scheme(authenticated_client, project.id, "A")
    b = await _create_scheme(authenticated_client, project.id, "B")
    other_x = await _create_scheme(authenticated_client, other.id, "X")

    await authenticated_client.put(
        f"/api/schemes/{b['id']}/position", json={"position": 0}
    )

    # Other project's scheme keeps its position.
    other_data = (
        await authenticated_client.get(f"/api/projects/{other.id}/schemes")
    ).json()
    assert [s["title"] for s in other_data] == ["X"]
    assert other_data[0]["position"] == 0
    assert other_x["position"] == 0


@pytest.mark.asyncio
async def test_delete_scheme_referenced_by_property(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    project: Project,
    scheme: ConceptScheme,
) -> None:
    """Test deleting a scheme that is referenced by a property fails."""
    from taxonomy_builder.models.property import Property

    ont_cls = OntologyClass(
        project_id=project.id,
        identifier="Finding",
        label="Finding",
        uri="https://example.org/vocab/Finding",
    )
    db_session.add(ont_cls)
    await db_session.flush()

    # Create a property that references this scheme
    prop = Property(
        project_id=project.id,
        identifier="testProp",
        label="Test Property",
        range_scheme_id=scheme.id,
        cardinality="single",
        required=False,
        uri="https://example.org/vocab/testProp",
    )
    prop.domain_classes = [ont_cls]
    db_session.add(prop)
    await db_session.flush()

    # Try to delete the scheme
    response = await authenticated_client.delete(f"/api/schemes/{scheme.id}")
    assert response.status_code == 409
    assert "referenced by" in response.json()["detail"].lower()
