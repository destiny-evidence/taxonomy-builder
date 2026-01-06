"""Tests for the PublishedVersion model."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.published_version import PublishedVersion


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
async def test_create_published_version(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test creating a published version."""
    version = PublishedVersion(
        scheme_id=scheme.id,
        version_label="1.0",
        snapshot={"scheme": {"title": "Test"}, "concepts": []},
        notes="Initial release",
    )
    db_session.add(version)
    await db_session.flush()
    await db_session.refresh(version)

    assert version.id is not None
    assert version.scheme_id == scheme.id
    assert version.version_label == "1.0"
    assert version.published_at is not None
    assert version.snapshot == {"scheme": {"title": "Test"}, "concepts": []}
    assert version.notes == "Initial release"


@pytest.mark.asyncio
async def test_snapshot_stores_complex_data(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that snapshot can store complex nested data."""
    complex_snapshot = {
        "scheme": {
            "id": str(scheme.id),
            "title": "Test Scheme",
            "uri": "http://example.org/concepts",
            "description": "A test description",
        },
        "concepts": [
            {
                "id": "concept-1",
                "pref_label": "Dogs",
                "definition": "A domestic animal",
                "broader": [],
                "narrower": ["concept-2"],
                "related": [],
            },
            {
                "id": "concept-2",
                "pref_label": "Poodles",
                "definition": "A breed of dog",
                "broader": ["concept-1"],
                "narrower": [],
                "related": [],
            },
        ],
    }

    version = PublishedVersion(
        scheme_id=scheme.id,
        version_label="2.0",
        snapshot=complex_snapshot,
    )
    db_session.add(version)
    await db_session.flush()
    await db_session.refresh(version)

    # Verify the snapshot is stored and retrieved correctly
    assert version.snapshot["scheme"]["title"] == "Test Scheme"
    assert len(version.snapshot["concepts"]) == 2
    assert version.snapshot["concepts"][0]["pref_label"] == "Dogs"
    assert version.snapshot["concepts"][1]["broader"] == ["concept-1"]
