"""Tests for seed data creation."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.class_superclass import ClassSuperclass
from taxonomy_builder.seed import create_seed_data


@pytest.mark.asyncio
async def test_seed_creates_class_superclass_rows(db_session: AsyncSession) -> None:
    """Seed imports evrepo-core.ttl + ontology-expressivity.ttl and creates ClassSuperclass rows."""
    created = await create_seed_data(db_session)

    # 17 from evrepo-core.ttl + 9 from ontology-expressivity.ttl
    assert created["classes"] == 26
    # 41 from evrepo-core.ttl + 15 from ontology-expressivity.ttl
    assert created["properties"] == 56

    result = await db_session.execute(select(ClassSuperclass))
    edges = result.scalars().all()
    # 5 from evrepo-core + 7 from expressivity (Study→Entity, RCT→Study,
    # ObservationalStudy→Study, Finding→Entity, QuantitativeFinding→Finding,
    # MeasuredOutcome→Outcome, MeasuredOutcome→Finding)
    # Note: StudyDesignConcept→skos:Concept is external, not stored
    assert len(edges) == 12
