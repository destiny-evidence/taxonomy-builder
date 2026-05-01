"""Tests for ConceptService.search_concepts."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.services.concept_service import ConceptService


async def test_search_by_pref_label(db_session: AsyncSession, scheme: ConceptScheme):
    """Search should match pref_label case-insensitively."""
    db_session.add(Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="c1"))
    db_session.add(Concept(scheme_id=scheme.id, pref_label="Cats", identifier="c2"))
    db_session.add(Concept(scheme_id=scheme.id, pref_label="Dog breeds", identifier="c3"))
    await db_session.flush()

    svc = ConceptService(db_session)
    results = await svc.search_concepts("dog", scheme_id=scheme.id)
    labels = [c.pref_label for c in results]
    assert "Dogs" in labels
    assert "Dog breeds" in labels
    assert "Cats" not in labels


async def test_search_by_definition(db_session: AsyncSession, scheme: ConceptScheme):
    """Search should match definition text."""
    db_session.add(
        Concept(
            scheme_id=scheme.id,
            pref_label="Animals",
            identifier="c1",
            definition="Living organisms that are not plants",
        )
    )
    db_session.add(
        Concept(
            scheme_id=scheme.id,
            pref_label="Plants",
            identifier="c2",
            definition="Photosynthetic organisms",
        )
    )
    await db_session.flush()

    svc = ConceptService(db_session)
    results = await svc.search_concepts("organisms", scheme_id=scheme.id)
    assert len(results) == 2


async def test_search_by_alt_labels(db_session: AsyncSession, scheme: ConceptScheme):
    """Search should match alt_labels case-insensitively."""
    db_session.add(
        Concept(
            scheme_id=scheme.id,
            pref_label="Dogs",
            identifier="c1",
            alt_labels=["Canines", "Hounds"],
        )
    )
    db_session.add(Concept(scheme_id=scheme.id, pref_label="Cats", identifier="c2"))
    await db_session.flush()

    svc = ConceptService(db_session)
    results = await svc.search_concepts("canine", scheme_id=scheme.id)
    labels = [c.pref_label for c in results]
    assert "Dogs" in labels
    assert "Cats" not in labels


async def test_search_no_results(db_session: AsyncSession, scheme: ConceptScheme):
    """Search with no matches returns empty list."""
    db_session.add(Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="c1"))
    await db_session.flush()

    svc = ConceptService(db_session)
    results = await svc.search_concepts("zebra", scheme_id=scheme.id)
    assert results == []


async def test_search_invalid_scheme(db_session: AsyncSession):
    """Search with non-existent scheme raises SchemeNotFoundError."""
    from uuid import uuid4

    from taxonomy_builder.services.concept_service import SchemeNotFoundError

    svc = ConceptService(db_session)
    with pytest.raises(SchemeNotFoundError):
        await svc.search_concepts("anything", scheme_id=uuid4())


async def test_search_results_ordered(db_session: AsyncSession, scheme: ConceptScheme):
    """Search results should be ordered by pref_label."""
    db_session.add(Concept(scheme_id=scheme.id, pref_label="Zebra fish", identifier="c1"))
    db_session.add(Concept(scheme_id=scheme.id, pref_label="Angel fish", identifier="c2"))
    db_session.add(Concept(scheme_id=scheme.id, pref_label="Clown fish", identifier="c3"))
    await db_session.flush()

    svc = ConceptService(db_session)
    results = await svc.search_concepts("fish", scheme_id=scheme.id)
    labels = [c.pref_label for c in results]
    assert labels == ["Angel fish", "Clown fish", "Zebra fish"]


async def test_search_requires_scope(db_session: AsyncSession):
    """Search without scheme_id or project_id raises ValueError."""
    svc = ConceptService(db_session)
    with pytest.raises(ValueError, match="Either scheme_id or project_id"):
        await svc.search_concepts("anything")


async def test_search_by_project(
    db_session: AsyncSession, project: Project, scheme: ConceptScheme, scheme2: ConceptScheme
):
    """Search by project_id finds concepts across all schemes."""
    db_session.add(Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="c1"))
    db_session.add(Concept(scheme_id=scheme2.id, pref_label="Dog food", identifier="c2"))
    db_session.add(Concept(scheme_id=scheme.id, pref_label="Cats", identifier="c3"))
    await db_session.flush()

    svc = ConceptService(db_session)
    results = await svc.search_concepts("dog", project_id=project.id)
    labels = [c.pref_label for c in results]
    assert "Dogs" in labels
    assert "Dog food" in labels
    assert "Cats" not in labels
