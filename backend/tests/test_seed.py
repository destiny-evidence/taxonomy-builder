"""Tests for seed data creation."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.class_superclass import ClassSuperclass
from taxonomy_builder.seed import create_seed_data


@pytest.mark.asyncio
async def test_seed_creates_class_superclass_rows(db_session: AsyncSession) -> None:
    """Seed imports evrepo-core.ttl and creates ClassSuperclass rows for rdfs:subClassOf."""
    await create_seed_data(db_session)

    result = await db_session.execute(select(ClassSuperclass))
    rows = result.scalars().all()

    assert len(rows) > 0, "Expected at least one ClassSuperclass row from evrepo-core import"
