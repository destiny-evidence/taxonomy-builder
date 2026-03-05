"""Tests for seed data creation."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.class_superclass import ClassSuperclass
from taxonomy_builder.seed import create_seed_data


@pytest.mark.asyncio
async def test_seed_creates_class_superclass_rows(db_session: AsyncSession) -> None:
    """Seed imports evrepo-core.ttl and creates ClassSuperclass rows for rdfs:subClassOf."""
    created = await create_seed_data(db_session)

    assert created["classes"] == 15, "Expected 15 ontology classes from evrepo-core.ttl"
    assert created["properties"] == 34, "Expected 34 properties from evrepo-core.ttl"

    result = await db_session.execute(select(ClassSuperclass))
    edges = result.scalars().all()
    assert len(edges) == 5, (
        "Expected 5 subClassOf edges: "
        "Intervention/ControlCondition/TemporalCondition → Condition, "
        "Numeric/StringCodingAnnotation → CodingAnnotation"
    )
