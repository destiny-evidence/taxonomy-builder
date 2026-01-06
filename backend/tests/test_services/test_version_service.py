"""Tests for the VersionService."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.change_event import ChangeEvent
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.published_version import PublishedVersion
from taxonomy_builder.schemas.concept import ConceptCreate
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.version_service import VersionService


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
        description="A test scheme",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


@pytest.mark.asyncio
async def test_publish_version_creates_snapshot(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that publishing creates a version with a snapshot."""
    service = VersionService(db_session)

    version = await service.publish_version(
        scheme_id=scheme.id,
        version_label="1.0",
        notes="Initial release",
    )

    assert version.id is not None
    assert version.scheme_id == scheme.id
    assert version.version_label == "1.0"
    assert version.notes == "Initial release"
    assert version.snapshot is not None
    assert "scheme" in version.snapshot
    assert version.snapshot["scheme"]["title"] == "Test Scheme"


@pytest.mark.asyncio
async def test_publish_version_includes_concepts_and_relationships(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that published snapshot includes all concepts and relationships."""
    concept_service = ConceptService(db_session)

    # Create concepts with relationships
    parent = await concept_service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Animals"),
    )
    child = await concept_service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Dogs"),
    )
    related = await concept_service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Wolves"),
    )

    await concept_service.add_broader(child.id, parent.id)
    await concept_service.add_related(child.id, related.id)

    # Publish version
    version_service = VersionService(db_session)
    version = await version_service.publish_version(
        scheme_id=scheme.id,
        version_label="1.0",
    )

    # Verify snapshot contains all concepts
    assert len(version.snapshot["concepts"]) == 3

    # Find the child concept in snapshot
    child_snapshot = next(
        c for c in version.snapshot["concepts"] if c["pref_label"] == "Dogs"
    )
    assert str(parent.id) in child_snapshot["broader_ids"]
    assert str(related.id) in child_snapshot["related_ids"]


@pytest.mark.asyncio
async def test_publish_version_creates_change_event(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that publishing creates a change event."""
    service = VersionService(db_session)

    version = await service.publish_version(
        scheme_id=scheme.id,
        version_label="1.0",
    )

    # Check that a change event was created
    result = await db_session.execute(
        select(ChangeEvent).where(
            ChangeEvent.entity_type == "published_version",
            ChangeEvent.entity_id == version.id,
            ChangeEvent.action == "publish",
        )
    )
    event = result.scalar_one()

    assert event.scheme_id == scheme.id
    assert event.before_state is None
    assert event.after_state is not None
    assert event.after_state["version_label"] == "1.0"


@pytest.mark.asyncio
async def test_list_versions(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test listing versions for a scheme."""
    service = VersionService(db_session)

    await service.publish_version(scheme_id=scheme.id, version_label="1.0")
    await service.publish_version(scheme_id=scheme.id, version_label="2.0")

    versions = await service.list_versions(scheme_id=scheme.id)

    assert len(versions) == 2
    # Should be ordered by published_at descending (most recent first)
    assert versions[0].version_label == "2.0"
    assert versions[1].version_label == "1.0"


@pytest.mark.asyncio
async def test_get_version(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test getting a specific version."""
    service = VersionService(db_session)

    published = await service.publish_version(
        scheme_id=scheme.id, version_label="1.0"
    )

    version = await service.get_version(version_id=published.id)

    assert version is not None
    assert version.id == published.id
    assert version.version_label == "1.0"


@pytest.mark.asyncio
async def test_duplicate_version_label_fails(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that publishing with a duplicate version label fails."""
    from taxonomy_builder.services.version_service import DuplicateVersionLabelError

    service = VersionService(db_session)

    await service.publish_version(scheme_id=scheme.id, version_label="1.0")

    with pytest.raises(DuplicateVersionLabelError):
        await service.publish_version(scheme_id=scheme.id, version_label="1.0")
