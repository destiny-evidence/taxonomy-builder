"""Tests for the ClassSuperclass model (superclass/subclass relationships)."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.class_superclass import ClassSuperclass
from taxonomy_builder.models.ontology_class import OntologyClass
from taxonomy_builder.models.project import Project


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(
        name="Test Project",
        namespace="http://example.org/",
        identifier_prefix="TST",
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def classes(db_session: AsyncSession, project: Project) -> list[OntologyClass]:
    """Create ontology classes for testing hierarchy."""
    condition = OntologyClass(
        project_id=project.id,
        identifier="Condition",
        label="Condition",
        uri="http://example.org/Condition",
    )
    intervention = OntologyClass(
        project_id=project.id,
        identifier="Intervention",
        label="Intervention",
        uri="http://example.org/Intervention",
    )
    control = OntologyClass(
        project_id=project.id,
        identifier="ControlCondition",
        label="Control Condition",
        uri="http://example.org/ControlCondition",
    )
    entity = OntologyClass(
        project_id=project.id,
        identifier="Entity",
        label="Entity",
        uri="http://example.org/Entity",
    )
    db_session.add_all([condition, intervention, control, entity])
    await db_session.flush()
    for c in [condition, intervention, control, entity]:
        await db_session.refresh(c)
    return [condition, intervention, control, entity]


@pytest.mark.asyncio
async def test_create_superclass_relationship(
    db_session: AsyncSession, classes: list[OntologyClass]
) -> None:
    """Test creating a superclass relationship."""
    condition, intervention, control, entity = classes

    rel = ClassSuperclass(class_id=intervention.id, superclass_id=condition.id)
    db_session.add(rel)
    await db_session.flush()

    assert rel.class_id == intervention.id
    assert rel.superclass_id == condition.id


@pytest.mark.asyncio
async def test_class_can_have_multiple_superclasses(
    db_session: AsyncSession, classes: list[OntologyClass]
) -> None:
    """Test that a class can have multiple superclasses (multiple inheritance)."""
    condition, intervention, control, entity = classes

    # Intervention is both a Condition and an Entity
    rel1 = ClassSuperclass(class_id=intervention.id, superclass_id=condition.id)
    rel2 = ClassSuperclass(class_id=intervention.id, superclass_id=entity.id)
    db_session.add_all([rel1, rel2])
    await db_session.flush()

    result = await db_session.execute(
        select(ClassSuperclass).where(ClassSuperclass.class_id == intervention.id)
    )
    superclass_rels = list(result.scalars().all())
    assert len(superclass_rels) == 2


@pytest.mark.asyncio
async def test_class_can_be_superclass_to_multiple(
    db_session: AsyncSession, classes: list[OntologyClass]
) -> None:
    """Test that a class can be superclass to multiple subclasses."""
    condition, intervention, control, entity = classes

    # Condition is superclass to both Intervention and ControlCondition
    rel1 = ClassSuperclass(class_id=intervention.id, superclass_id=condition.id)
    rel2 = ClassSuperclass(class_id=control.id, superclass_id=condition.id)
    db_session.add_all([rel1, rel2])
    await db_session.flush()

    result = await db_session.execute(
        select(ClassSuperclass).where(ClassSuperclass.superclass_id == condition.id)
    )
    subclass_rels = list(result.scalars().all())
    assert len(subclass_rels) == 2


@pytest.mark.asyncio
async def test_cascade_delete_subclass(
    db_session: AsyncSession, classes: list[OntologyClass]
) -> None:
    """Test that superclass relationships are deleted when subclass is deleted."""
    condition, intervention, control, entity = classes

    rel = ClassSuperclass(class_id=intervention.id, superclass_id=condition.id)
    db_session.add(rel)
    await db_session.flush()

    await db_session.delete(intervention)
    await db_session.flush()

    result = await db_session.execute(
        select(ClassSuperclass).where(ClassSuperclass.superclass_id == condition.id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_cascade_delete_superclass(
    db_session: AsyncSession, classes: list[OntologyClass]
) -> None:
    """Test that superclass relationships are deleted when superclass is deleted."""
    condition, intervention, control, entity = classes

    rel = ClassSuperclass(class_id=intervention.id, superclass_id=condition.id)
    db_session.add(rel)
    await db_session.flush()

    await db_session.delete(condition)
    await db_session.flush()

    result = await db_session.execute(
        select(ClassSuperclass).where(ClassSuperclass.class_id == intervention.id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_superclasses_relationship_access(
    db_session: AsyncSession, classes: list[OntologyClass]
) -> None:
    """Test accessing superclasses via relationship on OntologyClass."""
    condition, intervention, control, entity = classes

    # Intervention subClassOf Condition and Entity
    rel1 = ClassSuperclass(class_id=intervention.id, superclass_id=condition.id)
    rel2 = ClassSuperclass(class_id=intervention.id, superclass_id=entity.id)
    db_session.add_all([rel1, rel2])
    await db_session.flush()
    await db_session.refresh(intervention)

    superclass_labels = {c.label for c in intervention.superclasses}
    assert superclass_labels == {"Condition", "Entity"}


@pytest.mark.asyncio
async def test_subclasses_relationship_access(
    db_session: AsyncSession, classes: list[OntologyClass]
) -> None:
    """Test accessing subclasses via relationship on OntologyClass."""
    condition, intervention, control, entity = classes

    # Intervention and ControlCondition are both subClasses of Condition
    rel1 = ClassSuperclass(class_id=intervention.id, superclass_id=condition.id)
    rel2 = ClassSuperclass(class_id=control.id, superclass_id=condition.id)
    db_session.add_all([rel1, rel2])
    await db_session.flush()
    await db_session.refresh(condition)

    subclass_labels = {c.label for c in condition.subclasses}
    assert subclass_labels == {"Intervention", "Control Condition"}
