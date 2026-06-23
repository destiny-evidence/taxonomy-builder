"""Tests for the deferrable unique constraint on (project_id, position).

The test DB is built from metadata, so the deferrable constraint is present.
Because the test session never commits, deferred checks must be forced with
``SET CONSTRAINTS ... IMMEDIATE`` to observe them.
"""

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.concept_scheme import ConceptSchemeCreate
from taxonomy_builder.services.concept_scheme_service import ConceptSchemeService


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    project = Project(
        name="Constraint Test",
        namespace="http://example.org/constraint",
        identifier_prefix="CON",
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_reorder_tolerates_transient_duplicate_positions(
    db_session: AsyncSession, project: Project
) -> None:
    """The shift UPDATE transiently duplicates positions; deferral lets it pass.

    A non-deferrable constraint would raise during the shift UPDATE. Forcing an
    immediate check after the reorder proves the final sequence is valid.
    """
    service = ConceptSchemeService(db_session)
    a = await service.create_scheme(project.id, ConceptSchemeCreate(title="A"))
    await service.create_scheme(project.id, ConceptSchemeCreate(title="B"))
    await service.create_scheme(project.id, ConceptSchemeCreate(title="C"))

    await service.reorder_scheme(a.id, 2)

    # Validate the deferred constraint now; the gapless final state must pass.
    await db_session.execute(
        text("SET CONSTRAINTS uq_scheme_position_per_project IMMEDIATE")
    )

    schemes = (
        await db_session.execute(
            select(ConceptScheme)
            .where(ConceptScheme.project_id == project.id)
            .order_by(ConceptScheme.position)
        )
    ).scalars().all()
    assert [s.title for s in schemes] == ["B", "C", "A"]
    assert [s.position for s in schemes] == [0, 1, 2]


@pytest.mark.asyncio
async def test_duplicate_positions_rejected_at_check(
    db_session: AsyncSession, project: Project
) -> None:
    """Two schemes sharing a position are rejected when the constraint is checked."""
    db_session.add_all(
        [
            ConceptScheme(
                project_id=project.id, title="One", uri="http://example.org/1", position=0
            ),
            ConceptScheme(
                project_id=project.id, title="Two", uri="http://example.org/2", position=0
            ),
        ]
    )
    await db_session.flush()  # deferred: no error yet

    with pytest.raises(IntegrityError):
        await db_session.execute(
            text("SET CONSTRAINTS uq_scheme_position_per_project IMMEDIATE")
        )
