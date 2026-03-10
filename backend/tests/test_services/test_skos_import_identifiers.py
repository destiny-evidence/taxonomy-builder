"""Tests for SKOS import identifier collision and counter reconciliation."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.services.skos_import_service import (
    SKOSImportError,
    SKOSImportService,
)

SIMPLE_TTL = """\
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix : <http://example.org/test/> .

:scheme a skos:ConceptScheme ;
    skos:prefLabel "Test Scheme" .

:EVD000001 a skos:Concept ;
    skos:inScheme :scheme ;
    skos:prefLabel "First" .

:EVD000002 a skos:Concept ;
    skos:inScheme :scheme ;
    skos:prefLabel "Second" .
"""

# Two schemes with concepts that share the same local name → duplicate identifier
DUPLICATE_ID_TTL = """\
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix s1: <http://example.org/test/s1/> .
@prefix s2: <http://example.org/test/s2/> .

s1:scheme a skos:ConceptScheme ;
    skos:prefLabel "Scheme One" .

s2:scheme a skos:ConceptScheme ;
    skos:prefLabel "Scheme Two" .

s1:DUP001 a skos:Concept ;
    skos:inScheme s1:scheme ;
    skos:prefLabel "In scheme one" .

s2:DUP001 a skos:Concept ;
    skos:inScheme s2:scheme ;
    skos:prefLabel "In scheme two" .
"""


@pytest.fixture
async def project_with_prefix(db_session: AsyncSession) -> Project:
    project = Project(
        name="Import Collision Project",
        identifier_prefix="EVD",
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


async def test_import_reconciles_counter(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    """After importing EVD000001 and EVD000002, counter should be 2."""
    service = SKOSImportService(db_session)
    await service.execute(
        project_with_prefix.id,
        SIMPLE_TTL.encode(),
        "test.ttl",
    )
    await db_session.refresh(project_with_prefix)
    assert project_with_prefix.identifier_counter == 2


async def test_import_preview_detects_collision(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    """Preview should report collision with existing concept."""
    scheme = ConceptScheme(
        project_id=project_with_prefix.id,
        title="Existing",
        uri="http://example.org/test/scheme",
    )
    db_session.add(scheme)
    await db_session.flush()

    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Existing First",
        identifier="EVD000001",
    )
    db_session.add(concept)
    await db_session.flush()

    service = SKOSImportService(db_session)
    preview = await service.preview(
        project_with_prefix.id,
        SIMPLE_TTL.encode(),
        "test.ttl",
    )
    collision_issues = [
        i for i in preview.validation_issues
        if i.type == "identifier_collision"
    ]
    assert len(collision_issues) > 0
    assert preview.valid is False


async def test_import_execute_blocks_on_collision(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    """Execute should raise when imported identifiers collide with existing."""
    scheme = ConceptScheme(
        project_id=project_with_prefix.id,
        title="Existing",
        uri="http://example.org/test/scheme",
    )
    db_session.add(scheme)
    await db_session.flush()

    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Existing First",
        identifier="EVD000001",
    )
    db_session.add(concept)
    await db_session.flush()

    service = SKOSImportService(db_session)
    with pytest.raises(SKOSImportError, match="identifier conflicts"):
        await service.execute(
            project_with_prefix.id,
            SIMPLE_TTL.encode(),
            "test.ttl",
        )


async def test_import_preview_detects_duplicate_identifiers(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    """Two concepts in different schemes with the same local name → duplicate."""
    service = SKOSImportService(db_session)
    preview = await service.preview(
        project_with_prefix.id,
        DUPLICATE_ID_TTL.encode(),
        "test.ttl",
    )
    dup_issues = [
        i for i in preview.validation_issues
        if i.type == "identifier_duplicate_in_file"
    ]
    assert len(dup_issues) > 0
    assert preview.valid is False


async def test_import_execute_blocks_on_duplicate_identifiers(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    """Execute should raise when import file has duplicate identifiers."""
    service = SKOSImportService(db_session)
    with pytest.raises(SKOSImportError, match="identifier conflicts"):
        await service.execute(
            project_with_prefix.id,
            DUPLICATE_ID_TTL.encode(),
            "test.ttl",
        )
