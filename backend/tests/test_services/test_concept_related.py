"""Tests for related relationship service methods."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.services.concept_service import (
    ConceptService,
    RelatedRelationshipExistsError,
    RelatedRelationshipNotFoundError,
    RelatedSameSchemeError,
    RelatedSelfReferenceError,
)


@pytest.fixture
def service(db_session: AsyncSession) -> ConceptService:
    """Create a concept service for testing."""
    return ConceptService(db_session)


@pytest.mark.asyncio
async def test_add_related_creates_relationship(
    service: ConceptService, concepts: list[Concept]
) -> None:
    """Test that add_related creates a related relationship."""
    dogs, cats, vet_medicine = concepts

    await service.add_related(dogs.id, cats.id)

    # Verify relationship exists by fetching the concept
    dog_concept = await service.get_concept(dogs.id)
    related_ids = {c.id for c in dog_concept.related}
    assert cats.id in related_ids


@pytest.mark.asyncio
async def test_add_related_is_symmetric(
    service: ConceptService, concepts: list[Concept]
) -> None:
    """Test that related relationship is visible from both concepts."""
    dogs, cats, vet_medicine = concepts

    # Add relationship from dogs to cats
    await service.add_related(dogs.id, cats.id)

    # Should be visible from both sides
    dog_concept = await service.get_concept(dogs.id)
    cat_concept = await service.get_concept(cats.id)

    assert cats.id in {c.id for c in dog_concept.related}
    assert dogs.id in {c.id for c in cat_concept.related}


@pytest.mark.asyncio
async def test_add_related_orders_ids(
    service: ConceptService, concepts: list[Concept], db_session: AsyncSession
) -> None:
    """Test that add_related stores IDs with smaller ID first."""
    dogs, cats, vet_medicine = concepts

    # Try adding in both orders - should result in same stored relationship
    await service.add_related(dogs.id, cats.id)

    # Query the raw table to verify ordering
    from sqlalchemy import select

    from taxonomy_builder.models.concept_related import ConceptRelated

    result = await db_session.execute(select(ConceptRelated))
    rel = result.scalar_one()

    # The smaller UUID should be concept_id
    assert rel.concept_id < rel.related_concept_id


@pytest.mark.asyncio
async def test_add_related_rejects_self_reference(
    service: ConceptService, concepts: list[Concept]
) -> None:
    """Test that a concept cannot be related to itself."""
    dogs, cats, vet_medicine = concepts

    with pytest.raises(RelatedSelfReferenceError):
        await service.add_related(dogs.id, dogs.id)


@pytest.mark.asyncio
async def test_add_related_rejects_different_scheme(
    service: ConceptService, concepts: list[Concept], concept_other_scheme: Concept
) -> None:
    """Test that concepts from different schemes cannot be related."""
    dogs, cats, vet_medicine = concepts

    with pytest.raises(RelatedSameSchemeError):
        await service.add_related(dogs.id, concept_other_scheme.id)


@pytest.mark.asyncio
async def test_add_related_rejects_duplicate(
    service: ConceptService, concepts: list[Concept]
) -> None:
    """Test that duplicate related relationships are rejected."""
    dogs, cats, vet_medicine = concepts

    await service.add_related(dogs.id, cats.id)

    # Try to add the same relationship again (should fail)
    with pytest.raises(RelatedRelationshipExistsError):
        await service.add_related(dogs.id, cats.id)


@pytest.mark.asyncio
async def test_add_related_rejects_duplicate_reverse_order(
    service: ConceptService, concepts: list[Concept]
) -> None:
    """Test that duplicate relationships are rejected regardless of order."""
    dogs, cats, vet_medicine = concepts

    await service.add_related(dogs.id, cats.id)

    # Try to add the same relationship in reverse order (should also fail)
    with pytest.raises(RelatedRelationshipExistsError):
        await service.add_related(cats.id, dogs.id)


@pytest.mark.asyncio
async def test_remove_related_deletes_relationship(
    service: ConceptService, concepts: list[Concept]
) -> None:
    """Test that remove_related deletes the relationship."""
    dogs, cats, vet_medicine = concepts

    await service.add_related(dogs.id, cats.id)
    await service.remove_related(dogs.id, cats.id)

    # Verify relationship is gone
    dog_concept = await service.get_concept(dogs.id)
    assert cats.id not in {c.id for c in dog_concept.related}


@pytest.mark.asyncio
async def test_remove_related_works_from_either_direction(
    service: ConceptService, concepts: list[Concept]
) -> None:
    """Test that remove_related works regardless of which concept is passed first."""
    dogs, cats, vet_medicine = concepts

    # Add relationship
    await service.add_related(dogs.id, cats.id)

    # Remove using reverse order
    await service.remove_related(cats.id, dogs.id)

    # Verify relationship is gone
    dog_concept = await service.get_concept(dogs.id)
    assert cats.id not in {c.id for c in dog_concept.related}


@pytest.mark.asyncio
async def test_remove_related_not_found_raises(
    service: ConceptService, concepts: list[Concept]
) -> None:
    """Test that removing non-existent relationship raises error."""
    dogs, cats, vet_medicine = concepts

    with pytest.raises(RelatedRelationshipNotFoundError):
        await service.remove_related(dogs.id, cats.id)


@pytest.mark.asyncio
async def test_get_concept_includes_related(
    service: ConceptService, concepts: list[Concept]
) -> None:
    """Test that get_concept includes related concepts."""
    dogs, cats, vet_medicine = concepts

    # Create multiple related relationships
    await service.add_related(dogs.id, cats.id)
    await service.add_related(dogs.id, vet_medicine.id)

    dog_concept = await service.get_concept(dogs.id)

    related_labels = {c.pref_label for c in dog_concept.related}
    assert related_labels == {"Cats", "Veterinary Medicine"}
