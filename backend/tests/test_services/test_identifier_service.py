"""Tests for IdentifierService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.services.identifier_service import (
    CounterOverflowError,
    IdentifierService,
    PrefixRequiredError,
)


@pytest.fixture
async def project_with_prefix(db_session: AsyncSession) -> Project:
    project = Project(name="ID Service Project", identifier_prefix="EVD")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def scheme(
    db_session: AsyncSession, project_with_prefix: Project
) -> ConceptScheme:
    scheme = ConceptScheme(
        project_id=project_with_prefix.id,
        title="ID Scheme",
        uri="http://example.org/s",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


async def test_allocate_returns_prefixed_identifier(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    service = IdentifierService(db_session)
    identifier = await service.allocate(project_with_prefix.id)
    assert identifier == "EVD000001"


async def test_allocate_increments_counter(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    service = IdentifierService(db_session)
    id1 = await service.allocate(project_with_prefix.id)
    id2 = await service.allocate(project_with_prefix.id)
    assert id1 == "EVD000001"
    assert id2 == "EVD000002"


async def test_allocate_without_prefix_raises(
    db_session: AsyncSession,
) -> None:
    project = Project(name="No Prefix Alloc")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    service = IdentifierService(db_session)
    with pytest.raises(PrefixRequiredError):
        await service.allocate(project.id)

    await db_session.refresh(project)
    assert project.identifier_counter == 0


async def test_allocate_overflow_raises(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    """Counter at 999999 -> next allocation should raise."""
    project_with_prefix.identifier_counter = 999999
    await db_session.flush()

    service = IdentifierService(db_session)
    with pytest.raises(CounterOverflowError):
        await service.allocate(project_with_prefix.id)

    await db_session.refresh(project_with_prefix)
    assert project_with_prefix.identifier_counter == 999999
