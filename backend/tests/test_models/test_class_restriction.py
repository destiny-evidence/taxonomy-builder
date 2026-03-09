"""Tests for ClassRestriction model."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.class_restriction import ClassRestriction
from taxonomy_builder.models.ontology_class import OntologyClass
from taxonomy_builder.models.project import Project


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    p = Project(name="Test Project", namespace="http://example.org/")
    db_session.add(p)
    await db_session.flush()
    await db_session.refresh(p)
    return p


@pytest.fixture
async def ontology_class(db_session: AsyncSession, project: Project) -> OntologyClass:
    cls = OntologyClass(
        project_id=project.id,
        identifier="StringAnnotation",
        label="String Annotation",
        uri="http://example.org/StringAnnotation",
    )
    db_session.add(cls)
    await db_session.flush()
    await db_session.refresh(cls)
    return cls


@pytest.mark.asyncio
async def test_create_restriction(db_session: AsyncSession, ontology_class: OntologyClass):
    r = ClassRestriction(
        class_id=ontology_class.id,
        on_property_uri="http://example.org/codedValue",
        restriction_type="allValuesFrom",
        value_uri="http://www.w3.org/2001/XMLSchema#string",
    )
    db_session.add(r)
    await db_session.flush()
    await db_session.refresh(r)

    assert r.id is not None
    assert r.class_id == ontology_class.id
    assert r.restriction_type == "allValuesFrom"


@pytest.mark.asyncio
async def test_restriction_via_relationship(db_session: AsyncSession, ontology_class: OntologyClass):
    r = ClassRestriction(
        class_id=ontology_class.id,
        on_property_uri="http://example.org/codedValue",
        restriction_type="allValuesFrom",
        value_uri="http://www.w3.org/2001/XMLSchema#string",
    )
    db_session.add(r)
    await db_session.flush()
    await db_session.refresh(ontology_class)

    assert len(ontology_class.restrictions) == 1
    assert ontology_class.restrictions[0].on_property_uri == "http://example.org/codedValue"


@pytest.mark.asyncio
async def test_cascade_delete_on_class(db_session: AsyncSession, ontology_class: OntologyClass):
    r = ClassRestriction(
        class_id=ontology_class.id,
        on_property_uri="http://example.org/codedValue",
        restriction_type="allValuesFrom",
        value_uri="http://www.w3.org/2001/XMLSchema#string",
    )
    db_session.add(r)
    await db_session.flush()
    restriction_id = r.id

    await db_session.delete(ontology_class)
    await db_session.flush()
    # Restriction should be gone via CASCADE
    result = await db_session.execute(
        select(ClassRestriction).where(ClassRestriction.id == restriction_id)
    )
    assert result.scalar_one_or_none() is None
