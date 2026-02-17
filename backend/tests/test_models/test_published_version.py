"""Tests for the PublishedVersion model."""

from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.published_version import PublishedVersion
from tests.factories import ProjectFactory, PublishedVersionFactory, flush


@pytest.fixture
async def project(db_session: AsyncSession):
    return await flush(db_session, ProjectFactory.create())


@pytest.mark.asyncio
async def test_create_published_version(db_session: AsyncSession, project) -> None:
    """Test creating a published version with all fields."""
    snapshot = {
        "concept_schemes": [{"id": "abc", "title": "Test Scheme"}],
        "properties": [],
        "classes": [],
    }
    version = await flush(
        db_session,
        PublishedVersionFactory.create(
            project=project,
            version="1.0",
            title="Initial Release",
            notes="First published version.",
            publisher="Evidence Synthesis Institute",
            finalized=True,
            published_at=datetime.now(),
            snapshot=snapshot,
        ),
    )

    assert version.id is not None
    assert isinstance(version.id, UUID)
    assert version.project_id == project.id
    assert version.version == "1.0"
    assert version.title == "Initial Release"
    assert version.notes == "First published version."
    assert version.publisher == "Evidence Synthesis Institute"
    assert version.finalized is True
    assert version.published_at is not None
    assert version.snapshot == snapshot


@pytest.mark.asyncio
async def test_unique_version_per_project(db_session: AsyncSession, project) -> None:
    """Test that the same version string cannot be used twice for a project."""
    await flush(
        db_session,
        PublishedVersionFactory.create(project=project, version="1.0", snapshot={}),
    )

    PublishedVersionFactory.create(project=project, version="1.0", title="Duplicate", snapshot={})

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_same_version_different_projects(db_session: AsyncSession) -> None:
    """Test that the same version string can be used across different projects."""
    v1 = PublishedVersionFactory.create(version="1.0", title="Project 1 Release", snapshot={})
    v2 = PublishedVersionFactory.create(version="1.0", title="Project 2 Release", snapshot={})
    await db_session.flush()

    assert v1.id != v2.id
    assert v1.version == v2.version


@pytest.mark.asyncio
async def test_only_one_draft_per_project(db_session: AsyncSession, project) -> None:
    """Test that a project can only have one draft (non-finalized) version."""
    await flush(
        db_session,
        PublishedVersionFactory.create(
            project=project, version="1.0", title="Draft 1", finalized=False, snapshot={}
        ),
    )

    PublishedVersionFactory.create(
        project=project, version="2.0", title="Draft 2", finalized=False, snapshot={}
    )

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_draft_plus_finalized_succeeds(db_session: AsyncSession, project) -> None:
    """Test that a project can have one draft and one finalized version."""
    finalized = PublishedVersionFactory.create(
        project=project,
        version="1.0",
        title="Released",
        finalized=True,
        published_at=datetime.now(),
        snapshot={},
    )
    draft = PublishedVersionFactory.create(
        project=project, version="2.0", title="In Progress", finalized=False, snapshot={}
    )
    await db_session.flush()

    assert finalized.finalized is True
    assert draft.finalized is False


@pytest.mark.asyncio
async def test_version_lineage(db_session: AsyncSession, project) -> None:
    """Test self-referential FK for version chain."""
    v1 = await flush(
        db_session,
        PublishedVersionFactory.create(
            project=project,
            version="1.0",
            title="V1",
            finalized=True,
            published_at=datetime.now(),
            snapshot={},
        ),
    )

    v2 = await flush(
        db_session,
        PublishedVersionFactory.create(
            project=project,
            version="2.0",
            title="V2",
            finalized=True,
            published_at=datetime.now(),
            previous_version_id=v1.id,
            snapshot={},
        ),
    )

    assert v2.previous_version_id == v1.id
    assert v2.previous_version is not None
    assert v2.previous_version.id == v1.id


@pytest.mark.asyncio
async def test_cascade_delete_with_project(db_session: AsyncSession, project) -> None:
    """Test that deleting a project cascades to published versions."""
    version = await flush(
        db_session,
        PublishedVersionFactory.create(
            project=project, version="1.0", title="Release", snapshot={"concept_schemes": []}
        ),
    )
    version_id = version.id

    await db_session.delete(project)
    await db_session.flush()

    result = await db_session.execute(
        select(PublishedVersion).where(PublishedVersion.id == version_id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_jsonb_round_trip(db_session: AsyncSession, project) -> None:
    """Test that complex JSONB snapshot data round-trips correctly."""
    snapshot = {
        "concept_schemes": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "uri": "http://example.org/schemes/test",
                "title": "Test Scheme",
                "description": "A test scheme",
                "concepts": [
                    {
                        "id": "660e8400-e29b-41d4-a716-446655440000",
                        "identifier": "concept-1",
                        "uri": "http://example.org/schemes/test/concept-1",
                        "pref_label": "Concept One",
                        "definition": "The first concept",
                        "scope_note": None,
                        "alt_labels": ["Alt 1", "Alt 2"],
                        "broader_ids": [],
                        "related_ids": ["770e8400-e29b-41d4-a716-446655440000"],
                    }
                ],
            }
        ],
        "properties": [
            {
                "id": "880e8400-e29b-41d4-a716-446655440000",
                "identifier": "testProp",
                "uri": "http://example.org/vocab/testProp",
                "label": "Test Property",
                "description": None,
                "domain_class": "http://example.org/vocab/Finding",
                "range_scheme_id": None,
                "range_datatype": "xsd:string",
                "cardinality": "single",
                "required": False,
            }
        ],
        "classes": [
            {
                "uri": "http://example.org/vocab/Finding",
                "label": "Finding",
                "description": "A research finding",
            }
        ],
    }
    version = await flush(
        db_session,
        PublishedVersionFactory.create(
            project=project, version="1.0", title="Full Snapshot", snapshot=snapshot
        ),
    )

    assert version.snapshot == snapshot
    assert version.snapshot["concept_schemes"][0]["title"] == "Test Scheme"
    assert len(version.snapshot["concept_schemes"][0]["concepts"]) == 1
    assert version.snapshot["properties"][0]["required"] is False
    assert version.snapshot["classes"][0]["label"] == "Finding"


@pytest.mark.asyncio
async def test_version_sort_key(db_session: AsyncSession, project) -> None:
    """Test that version_sort_key is computed from the version string."""
    v3 = PublishedVersionFactory.create(
        project=project, version="1.2.3", title="Three-part", finalized=True, snapshot={}
    )
    v2 = PublishedVersionFactory.create(
        project=project, version="2.0", title="Two-part", finalized=True, snapshot={}
    )
    await db_session.flush()
    await db_session.refresh(v3)
    await db_session.refresh(v2)

    assert v3.version_sort_key == [1, 2, 3]
    assert v2.version_sort_key == [2, 0]


@pytest.mark.asyncio
async def test_latest_true_for_highest_finalized(db_session: AsyncSession, project) -> None:
    """Test that latest is True only for the highest finalized version."""
    PublishedVersionFactory.create(
        project=project,
        version="1.0",
        title="V1",
        finalized=True,
        published_at=datetime.now(),
        snapshot={},
    )
    PublishedVersionFactory.create(
        project=project,
        version="2.0",
        title="V2",
        finalized=True,
        published_at=datetime.now(),
        snapshot={},
    )
    await db_session.flush()

    # Re-query to get fresh column_property values
    result = await db_session.execute(
        select(PublishedVersion)
        .where(PublishedVersion.project_id == project.id)
        .execution_options(populate_existing=True)
    )
    versions = {v.version: v for v in result.scalars().all()}

    assert versions["2.0"].latest is True
    assert versions["1.0"].latest is False


@pytest.mark.asyncio
async def test_latest_excludes_drafts(db_session: AsyncSession, project) -> None:
    """Test that a draft with higher version doesn't count as latest."""
    PublishedVersionFactory.create(
        project=project,
        version="1.0",
        title="Released",
        finalized=True,
        published_at=datetime.now(),
        snapshot={},
    )
    PublishedVersionFactory.create(
        project=project, version="2.0", title="Draft", finalized=False, snapshot={}
    )
    await db_session.flush()

    result = await db_session.execute(
        select(PublishedVersion)
        .where(PublishedVersion.project_id == project.id)
        .execution_options(populate_existing=True)
    )
    versions = {v.version: v for v in result.scalars().all()}

    assert versions["1.0"].latest is True
    assert versions["2.0"].latest is False


@pytest.mark.asyncio
async def test_latest_false_when_not_finalized(db_session: AsyncSession, project) -> None:
    """Test that a single draft version is not latest."""
    PublishedVersionFactory.create(
        project=project, version="1.0", title="Draft", finalized=False, snapshot={}
    )
    await db_session.flush()

    result = await db_session.execute(
        select(PublishedVersion)
        .where(PublishedVersion.project_id == project.id)
        .execution_options(populate_existing=True)
    )
    loaded = result.scalar_one()

    assert loaded.latest is False


@pytest.mark.asyncio
async def test_latest_queryable(db_session: AsyncSession, project) -> None:
    """Test that latest can be used as a filter in queries."""
    PublishedVersionFactory.create(
        project=project,
        version="1.0",
        title="V1",
        finalized=True,
        published_at=datetime.now(),
        snapshot={},
    )
    PublishedVersionFactory.create(
        project=project,
        version="2.0",
        title="V2",
        finalized=True,
        published_at=datetime.now(),
        snapshot={},
    )
    await db_session.flush()

    result = await db_session.execute(
        select(PublishedVersion).where(
            PublishedVersion.project_id == project.id,
            PublishedVersion.latest == True,  # noqa: E712
        )
    )
    latest = result.scalar_one()

    assert latest.version == "2.0"


@pytest.mark.asyncio
async def test_latest_semver_ordering(db_session: AsyncSession, project) -> None:
    """Test that latest uses numeric semver ordering, not string ordering."""
    for v in ["1.0", "1.9", "1.10"]:
        PublishedVersionFactory.create(
            project=project,
            version=v,
            title=f"V{v}",
            finalized=True,
            published_at=datetime.now(),
            snapshot={},
        )
    await db_session.flush()

    result = await db_session.execute(
        select(PublishedVersion).where(
            PublishedVersion.project_id == project.id,
            PublishedVersion.latest == True,  # noqa: E712
        )
    )
    latest = result.scalar_one()

    # String ordering would give "1.9" > "1.10", but semver gives "1.10"
    assert latest.version == "1.10"
