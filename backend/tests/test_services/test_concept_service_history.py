"""Tests for change tracking in ConceptService."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.change_event import ChangeEvent
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.concept import ConceptCreate, ConceptUpdate
from taxonomy_builder.services.concept_service import ConceptService


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def scheme(db_session: AsyncSession, project: Project) -> ConceptScheme:
    """Create a concept scheme for testing."""
    scheme = ConceptScheme(
        project_id=project.id,
        title="Test Scheme",
        uri="http://example.org/concepts",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


@pytest.mark.asyncio
async def test_create_concept_creates_change_event(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that creating a concept records a change event."""
    service = ConceptService(db_session)

    concept = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(
            pref_label="Dogs",
            identifier="dogs",
            definition="A domestic animal",
        ),
    )

    # Check that a change event was created
    result = await db_session.execute(
        select(ChangeEvent).where(
            ChangeEvent.entity_type == "concept",
            ChangeEvent.entity_id == concept.id,
            ChangeEvent.action == "create",
        )
    )
    event = result.scalar_one()

    assert event.scheme_id == scheme.id
    assert event.before_state is None
    assert event.after_state is not None
    assert event.after_state["pref_label"] == "Dogs"
    assert event.after_state["identifier"] == "dogs"
    assert event.after_state["definition"] == "A domestic animal"


@pytest.mark.asyncio
async def test_update_concept_creates_change_event_with_before_after(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that updating a concept records before and after states."""
    service = ConceptService(db_session)

    # Create a concept first
    concept = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(
            pref_label="Dog",
            definition=None,
        ),
    )
    concept_id = concept.id

    # Update the concept
    await service.update_concept(
        concept_id=concept_id,
        concept_in=ConceptUpdate(
            pref_label="Dogs",
            definition="A domestic animal",
        ),
    )

    # Check that an update change event was created
    result = await db_session.execute(
        select(ChangeEvent).where(
            ChangeEvent.entity_type == "concept",
            ChangeEvent.entity_id == concept_id,
            ChangeEvent.action == "update",
        )
    )
    event = result.scalar_one()

    assert event.scheme_id == scheme.id
    assert event.before_state is not None
    assert event.after_state is not None
    assert event.before_state["pref_label"] == "Dog"
    assert event.before_state["definition"] is None
    assert event.after_state["pref_label"] == "Dogs"
    assert event.after_state["definition"] == "A domestic animal"


@pytest.mark.asyncio
async def test_delete_concept_creates_change_event(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that deleting a concept records a change event with before state."""
    service = ConceptService(db_session)

    # Create a concept first
    concept = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(
            pref_label="Dogs",
            definition="A domestic animal",
        ),
    )
    concept_id = concept.id
    scheme_id = scheme.id

    # Delete the concept
    await service.delete_concept(concept_id)

    # Check that a delete change event was created
    result = await db_session.execute(
        select(ChangeEvent).where(
            ChangeEvent.entity_type == "concept",
            ChangeEvent.entity_id == concept_id,
            ChangeEvent.action == "delete",
        )
    )
    event = result.scalar_one()

    assert event.scheme_id == scheme_id
    assert event.before_state is not None
    assert event.after_state is None
    assert event.before_state["pref_label"] == "Dogs"
    assert event.before_state["definition"] == "A domestic animal"


@pytest.mark.asyncio
async def test_delete_concept_records_broader_relationship_deletion(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that deleting a concept with broader relationships records relationship deletions."""
    service = ConceptService(db_session)

    # Create parent and child concepts
    parent = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Animals"),
    )
    child = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Dogs"),
    )

    # Add broader relationship (child -> parent)
    await service.add_broader(child.id, parent.id)

    # Delete the child concept
    await service.delete_concept(child.id)

    # Check that a broader relationship delete event was created
    result = await db_session.execute(
        select(ChangeEvent)
        .where(
            ChangeEvent.entity_type == "concept_broader",
            ChangeEvent.action == "delete",
        )
        .order_by(ChangeEvent.timestamp)
    )
    events = list(result.scalars().all())

    assert len(events) == 1
    event = events[0]
    assert event.scheme_id == scheme.id
    assert event.before_state is not None
    assert event.before_state["concept_id"] == str(child.id)
    assert event.before_state["broader_concept_id"] == str(parent.id)
    assert event.after_state is None


@pytest.mark.asyncio
async def test_delete_concept_records_narrower_relationship_deletions(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that deleting a concept with narrower relationships records those deletions."""
    service = ConceptService(db_session)

    # Create parent and children concepts
    parent = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Animals"),
    )
    child1 = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Dogs"),
    )
    child2 = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Cats"),
    )

    # Add broader relationships (children -> parent)
    await service.add_broader(child1.id, parent.id)
    await service.add_broader(child2.id, parent.id)

    # Delete the parent concept
    await service.delete_concept(parent.id)

    # Check that broader relationship delete events were created for both children
    result = await db_session.execute(
        select(ChangeEvent)
        .where(
            ChangeEvent.entity_type == "concept_broader",
            ChangeEvent.action == "delete",
        )
        .order_by(ChangeEvent.timestamp)
    )
    events = list(result.scalars().all())

    assert len(events) == 2
    child_ids = {e.before_state["concept_id"] for e in events}
    assert str(child1.id) in child_ids
    assert str(child2.id) in child_ids
    for event in events:
        assert event.before_state["broader_concept_id"] == str(parent.id)


@pytest.mark.asyncio
async def test_delete_concept_records_related_relationship_deletions(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that deleting a concept with related relationships records those deletions."""
    service = ConceptService(db_session)

    # Create concepts
    concept1 = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Dogs"),
    )
    concept2 = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Wolves"),
    )

    # Add related relationship
    await service.add_related(concept1.id, concept2.id)

    # Delete concept1
    await service.delete_concept(concept1.id)

    # Check that a related relationship delete event was created
    result = await db_session.execute(
        select(ChangeEvent)
        .where(
            ChangeEvent.entity_type == "concept_related",
            ChangeEvent.action == "delete",
        )
        .order_by(ChangeEvent.timestamp)
    )
    events = list(result.scalars().all())

    assert len(events) == 1
    event = events[0]
    assert event.scheme_id == scheme.id
    assert event.before_state is not None
    # Related relationships are stored with smaller ID first
    if concept1.id < concept2.id:
        assert event.before_state["concept_id"] == str(concept1.id)
        assert event.before_state["related_concept_id"] == str(concept2.id)
    else:
        assert event.before_state["concept_id"] == str(concept2.id)
        assert event.before_state["related_concept_id"] == str(concept1.id)


@pytest.mark.asyncio
async def test_add_broader_creates_change_event(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that adding a broader relationship creates a change event."""
    service = ConceptService(db_session)

    # Create parent and child concepts
    parent = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Animals"),
    )
    child = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Dogs"),
    )

    # Add broader relationship
    await service.add_broader(child.id, parent.id)

    # Check that a create change event was created for this relationship
    result = await db_session.execute(
        select(ChangeEvent).where(
            ChangeEvent.entity_type == "concept_broader",
            ChangeEvent.entity_id == child.id,
            ChangeEvent.action == "create",
        )
    )
    event = result.scalar_one()

    assert event.scheme_id == scheme.id
    assert event.before_state is None
    assert event.after_state is not None
    assert event.after_state["concept_id"] == str(child.id)
    assert event.after_state["broader_concept_id"] == str(parent.id)
    # Verify labels are included
    assert event.after_state["concept_label"] == "Dogs"
    assert event.after_state["broader_label"] == "Animals"


@pytest.mark.asyncio
async def test_remove_broader_creates_change_event(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that removing a broader relationship creates a change event."""
    service = ConceptService(db_session)

    # Create parent and child concepts
    parent = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Animals"),
    )
    child = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Dogs"),
    )

    # Add broader relationship
    await service.add_broader(child.id, parent.id)

    # Remove broader relationship
    await service.remove_broader(child.id, parent.id)

    # Check that a delete change event was created
    result = await db_session.execute(
        select(ChangeEvent).where(
            ChangeEvent.entity_type == "concept_broader",
            ChangeEvent.action == "delete",
        )
    )
    event = result.scalar_one()

    assert event.scheme_id == scheme.id
    assert event.entity_id == child.id
    assert event.before_state is not None
    assert event.before_state["concept_id"] == str(child.id)
    assert event.before_state["broader_concept_id"] == str(parent.id)
    # Verify labels are included
    assert event.before_state["concept_label"] == "Dogs"
    assert event.before_state["broader_label"] == "Animals"
    assert event.after_state is None


@pytest.mark.asyncio
async def test_add_related_creates_change_event(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that adding a related relationship creates a change event."""
    service = ConceptService(db_session)

    # Create concepts
    concept1 = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Dogs"),
    )
    concept2 = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Wolves"),
    )

    # Add related relationship
    await service.add_related(concept1.id, concept2.id)

    # Check that a create change event was created
    result = await db_session.execute(
        select(ChangeEvent).where(
            ChangeEvent.entity_type == "concept_related",
            ChangeEvent.action == "create",
        )
    )
    event = result.scalar_one()

    assert event.scheme_id == scheme.id
    assert event.before_state is None
    assert event.after_state is not None
    # Related relationships are stored with smaller ID first
    if concept1.id < concept2.id:
        assert event.after_state["concept_id"] == str(concept1.id)
        assert event.after_state["related_concept_id"] == str(concept2.id)
        assert event.after_state["concept_label"] == "Dogs"
        assert event.after_state["related_label"] == "Wolves"
    else:
        assert event.after_state["concept_id"] == str(concept2.id)
        assert event.after_state["related_concept_id"] == str(concept1.id)
        assert event.after_state["concept_label"] == "Wolves"
        assert event.after_state["related_label"] == "Dogs"


@pytest.mark.asyncio
async def test_remove_related_creates_change_event(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that removing a related relationship creates a change event."""
    service = ConceptService(db_session)

    # Create concepts
    concept1 = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Dogs"),
    )
    concept2 = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Wolves"),
    )

    # Add related relationship
    await service.add_related(concept1.id, concept2.id)

    # Remove related relationship
    await service.remove_related(concept1.id, concept2.id)

    # Check that a delete change event was created
    result = await db_session.execute(
        select(ChangeEvent).where(
            ChangeEvent.entity_type == "concept_related",
            ChangeEvent.action == "delete",
        )
    )
    event = result.scalar_one()

    assert event.scheme_id == scheme.id
    assert event.before_state is not None
    assert event.after_state is None
    # Related relationships are stored with smaller ID first
    if concept1.id < concept2.id:
        assert event.before_state["concept_id"] == str(concept1.id)
        assert event.before_state["related_concept_id"] == str(concept2.id)
        assert event.before_state["concept_label"] == "Dogs"
        assert event.before_state["related_label"] == "Wolves"
    else:
        assert event.before_state["concept_id"] == str(concept2.id)
        assert event.before_state["related_concept_id"] == str(concept1.id)
        assert event.before_state["concept_label"] == "Wolves"
        assert event.before_state["related_label"] == "Dogs"


@pytest.mark.asyncio
async def test_move_concept_creates_change_events(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that moving a concept creates change events for the relationship changes."""
    service = ConceptService(db_session)

    # Create concepts
    old_parent = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Old Parent"),
    )
    new_parent = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="New Parent"),
    )
    child = await service.create_concept(
        scheme_id=scheme.id,
        concept_in=ConceptCreate(pref_label="Child"),
    )

    # Add initial broader relationship
    await service.add_broader(child.id, old_parent.id)

    # Move concept to new parent
    await service.move_concept(child.id, new_parent.id, old_parent.id)

    # Check that change events were created for both the remove and add
    result = await db_session.execute(
        select(ChangeEvent)
        .where(
            ChangeEvent.entity_type == "concept_broader",
            ChangeEvent.entity_id == child.id,
        )
        .order_by(ChangeEvent.timestamp)
    )
    events = list(result.scalars().all())

    # Should have: create (initial), delete (move), create (move)
    assert len(events) == 3

    # First event: initial add_broader
    assert events[0].action == "create"
    assert events[0].after_state["broader_concept_id"] == str(old_parent.id)

    # Second event: remove_broader from old parent
    assert events[1].action == "delete"
    assert events[1].before_state["broader_concept_id"] == str(old_parent.id)

    # Third event: add_broader to new parent
    assert events[2].action == "create"
    assert events[2].after_state["broader_concept_id"] == str(new_parent.id)
