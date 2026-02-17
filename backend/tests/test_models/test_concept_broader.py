"""Tests for the ConceptBroader model (broader relationships)."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_broader import ConceptBroader
from tests.factories import ConceptFactory, ConceptSchemeFactory, flush


@pytest.fixture
async def concepts(db_session: AsyncSession) -> list[Concept]:
    """Create multiple concepts for testing hierarchy."""
    scheme = ConceptSchemeFactory.create()
    animals = ConceptFactory.create(scheme=scheme, pref_label="Animals")
    mammals = ConceptFactory.create(scheme=scheme, pref_label="Mammals")
    pets = ConceptFactory.create(scheme=scheme, pref_label="Pets")
    dogs = ConceptFactory.create(scheme=scheme, pref_label="Dogs")
    cats = ConceptFactory.create(scheme=scheme, pref_label="Cats")
    await db_session.flush()
    for c in [animals, mammals, pets, dogs, cats]:
        await db_session.refresh(c)
    return [animals, mammals, pets, dogs, cats]


@pytest.mark.asyncio
async def test_create_broader_relationship(
    db_session: AsyncSession, concepts: list[Concept]
) -> None:
    """Test creating a broader relationship."""
    animals, mammals, pets, dogs, cats = concepts

    # Dogs broader Mammals
    rel = ConceptBroader(concept_id=dogs.id, broader_concept_id=mammals.id)
    db_session.add(rel)
    await db_session.flush()

    assert rel.concept_id == dogs.id
    assert rel.broader_concept_id == mammals.id


@pytest.mark.asyncio
async def test_concept_can_have_multiple_broader(
    db_session: AsyncSession, concepts: list[Concept]
) -> None:
    """Test that a concept can have multiple broader concepts (polyhierarchy)."""
    animals, mammals, pets, dogs, cats = concepts

    # Dogs is both a Mammal and a Pet
    rel1 = ConceptBroader(concept_id=dogs.id, broader_concept_id=mammals.id)
    rel2 = ConceptBroader(concept_id=dogs.id, broader_concept_id=pets.id)
    db_session.add_all([rel1, rel2])
    await db_session.flush()

    # Query all broader for dogs
    result = await db_session.execute(
        select(ConceptBroader).where(ConceptBroader.concept_id == dogs.id)
    )
    broader_rels = list(result.scalars().all())
    assert len(broader_rels) == 2


@pytest.mark.asyncio
async def test_concept_can_be_broader_to_multiple(
    db_session: AsyncSession, concepts: list[Concept]
) -> None:
    """Test that a concept can be broader to multiple concepts."""
    animals, mammals, pets, dogs, cats = concepts

    # Mammals is broader to both Dogs and Cats
    rel1 = ConceptBroader(concept_id=dogs.id, broader_concept_id=mammals.id)
    rel2 = ConceptBroader(concept_id=cats.id, broader_concept_id=mammals.id)
    db_session.add_all([rel1, rel2])
    await db_session.flush()

    # Query all narrower for mammals
    result = await db_session.execute(
        select(ConceptBroader).where(ConceptBroader.broader_concept_id == mammals.id)
    )
    narrower_rels = list(result.scalars().all())
    assert len(narrower_rels) == 2


@pytest.mark.asyncio
async def test_duplicate_broader_relationship_fails(
    db_session: AsyncSession, concepts: list[Concept]
) -> None:
    """Test that duplicate broader relationships are prevented."""
    animals, mammals, pets, dogs, cats = concepts

    rel1 = ConceptBroader(concept_id=dogs.id, broader_concept_id=mammals.id)
    db_session.add(rel1)
    await db_session.flush()

    # Try to add the same relationship again
    rel2 = ConceptBroader(concept_id=dogs.id, broader_concept_id=mammals.id)
    db_session.add(rel2)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_cascade_delete_narrower_concept(
    db_session: AsyncSession, concepts: list[Concept]
) -> None:
    """Test that broader relationships are deleted when narrower concept is deleted."""
    animals, mammals, pets, dogs, cats = concepts

    rel = ConceptBroader(concept_id=dogs.id, broader_concept_id=mammals.id)
    db_session.add(rel)
    await db_session.flush()

    # Delete dogs (the narrower concept)
    await db_session.delete(dogs)
    await db_session.flush()

    # The relationship should be gone
    result = await db_session.execute(
        select(ConceptBroader).where(ConceptBroader.broader_concept_id == mammals.id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_cascade_delete_broader_concept(
    db_session: AsyncSession, concepts: list[Concept]
) -> None:
    """Test that broader relationships are deleted when broader concept is deleted."""
    animals, mammals, pets, dogs, cats = concepts

    rel = ConceptBroader(concept_id=dogs.id, broader_concept_id=mammals.id)
    db_session.add(rel)
    await db_session.flush()

    # Delete mammals (the broader concept)
    await db_session.delete(mammals)
    await db_session.flush()

    # The relationship should be gone
    result = await db_session.execute(
        select(ConceptBroader).where(ConceptBroader.concept_id == dogs.id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_concept_broader_relationship_access(
    db_session: AsyncSession, concepts: list[Concept]
) -> None:
    """Test accessing broader concepts via relationship."""
    animals, mammals, pets, dogs, cats = concepts

    # Dogs is both a Mammal and a Pet
    rel1 = ConceptBroader(concept_id=dogs.id, broader_concept_id=mammals.id)
    rel2 = ConceptBroader(concept_id=dogs.id, broader_concept_id=pets.id)
    db_session.add_all([rel1, rel2])
    await db_session.flush()
    await db_session.refresh(dogs)

    # Access broader concepts through relationship
    broader_labels = {c.pref_label for c in dogs.broader}
    assert broader_labels == {"Mammals", "Pets"}


@pytest.mark.asyncio
async def test_concept_narrower_relationship_access(
    db_session: AsyncSession, concepts: list[Concept]
) -> None:
    """Test accessing narrower concepts via relationship."""
    animals, mammals, pets, dogs, cats = concepts

    # Dogs and Cats are both Mammals
    rel1 = ConceptBroader(concept_id=dogs.id, broader_concept_id=mammals.id)
    rel2 = ConceptBroader(concept_id=cats.id, broader_concept_id=mammals.id)
    db_session.add_all([rel1, rel2])
    await db_session.flush()
    await db_session.refresh(mammals)

    # Access narrower concepts through relationship
    narrower_labels = {c.pref_label for c in mammals.narrower}
    assert narrower_labels == {"Dogs", "Cats"}
