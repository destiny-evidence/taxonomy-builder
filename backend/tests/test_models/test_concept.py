"""Tests for the Concept model."""

from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project


@pytest.mark.asyncio
async def test_create_concept(db_session: AsyncSession, scheme: ConceptScheme) -> None:
    """Test creating a concept."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Test Concept",
        identifier="test",
        definition="A test concept",
        scope_note="Use for testing",
    )
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)

    assert concept.id is not None
    assert isinstance(concept.id, UUID)
    assert concept.scheme_id == scheme.id
    assert concept.pref_label == "Test Concept"
    assert concept.identifier == "test"
    assert concept.definition == "A test concept"
    assert concept.scope_note == "Use for testing"
    # URI is computed from scheme.uri + identifier
    assert concept.uri == "http://example.org/concepts/test"
    assert concept.created_at is not None
    assert concept.updated_at is not None


@pytest.mark.asyncio
async def test_concept_id_is_uuidv7(db_session: AsyncSession, scheme: ConceptScheme) -> None:
    """Test that concept IDs are UUIDv7."""
    concept = Concept(scheme_id=scheme.id, pref_label="UUID Test", identifier="uuid-test")
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)

    assert concept.id.version == 7


@pytest.mark.asyncio
async def test_concept_pref_label_required(db_session: AsyncSession, scheme: ConceptScheme) -> None:
    """Test that pref_label is required."""
    from sqlalchemy.exc import IntegrityError

    concept = Concept(scheme_id=scheme.id, pref_label=None, identifier="null-label")  # type: ignore[arg-type]
    db_session.add(concept)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_concept_optional_fields(db_session: AsyncSession, scheme: ConceptScheme) -> None:
    """Test that definition and scope_note are optional."""
    concept = Concept(scheme_id=scheme.id, pref_label="Minimal Concept", identifier="minimal")
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)

    assert concept.definition is None
    assert concept.scope_note is None


@pytest.mark.asyncio
async def test_concept_belongs_to_scheme(db_session: AsyncSession, scheme: ConceptScheme) -> None:
    """Test that concept has a relationship to scheme."""
    concept = Concept(scheme_id=scheme.id, pref_label="Related Concept", identifier="related")
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)

    assert concept.scheme.id == scheme.id
    assert concept.scheme.title == "Test Scheme"


@pytest.mark.asyncio
async def test_scheme_has_many_concepts(db_session: AsyncSession, scheme: ConceptScheme) -> None:
    """Test that a scheme can have multiple concepts."""
    concept1 = Concept(scheme_id=scheme.id, pref_label="Concept 1", identifier="c1")
    concept2 = Concept(scheme_id=scheme.id, pref_label="Concept 2", identifier="c2")
    db_session.add_all([concept1, concept2])
    await db_session.flush()

    await db_session.refresh(scheme)
    assert len(scheme.concepts) == 2


@pytest.mark.asyncio
async def test_cascade_delete_with_scheme(db_session: AsyncSession, scheme: ConceptScheme) -> None:
    """Test that concepts are deleted when scheme is deleted."""
    concept = Concept(scheme_id=scheme.id, pref_label="To Delete", identifier="to-delete")
    db_session.add(concept)
    await db_session.flush()
    concept_id = concept.id

    await db_session.delete(scheme)
    await db_session.flush()

    result = await db_session.execute(select(Concept).where(Concept.id == concept_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_duplicate_pref_label_allowed_in_scheme(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that duplicate pref_labels are allowed within a scheme."""
    # SKOS allows duplicate labels (though not recommended)
    concept1 = Concept(scheme_id=scheme.id, pref_label="Same Label", identifier="same-1")
    concept2 = Concept(scheme_id=scheme.id, pref_label="Same Label", identifier="same-2")
    db_session.add_all([concept1, concept2])
    await db_session.flush()

    assert concept1.id != concept2.id
    assert concept1.pref_label == concept2.pref_label


@pytest.mark.asyncio
async def test_duplicate_identifier_in_scheme_rejected(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that duplicate identifiers within the same scheme are rejected."""
    from sqlalchemy.exc import IntegrityError

    concept1 = Concept(scheme_id=scheme.id, pref_label="First", identifier="dupe")
    concept2 = Concept(scheme_id=scheme.id, pref_label="Second", identifier="dupe")
    db_session.add_all([concept1, concept2])

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_same_identifier_allowed_across_schemes(
    db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """Test that the same identifier is allowed in different schemes.

    Note: This may change — project-wide unique identifiers are likely once
    namespaces are globally unique. The constraint would move from
    (scheme_id, identifier) to (project_id, identifier).
    """
    other_scheme = ConceptScheme(
        project_id=project.id,
        title="Other Scheme",
        uri="http://example.org/other",
    )
    db_session.add(other_scheme)
    await db_session.flush()

    concept1 = Concept(scheme_id=scheme.id, pref_label="First", identifier="shared")
    concept2 = Concept(scheme_id=other_scheme.id, pref_label="Second", identifier="shared")
    db_session.add_all([concept1, concept2])
    await db_session.flush()

    assert concept1.id != concept2.id
    assert concept1.identifier == concept2.identifier
    assert concept1.scheme_id != concept2.scheme_id


# Alt labels tests


@pytest.mark.asyncio
async def test_concept_with_alt_labels(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test creating a concept with alt labels."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Dogs",
        identifier="dogs",
        alt_labels=["Canines", "Domestic dogs", "Canis familiaris"],
    )
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)

    assert concept.alt_labels == ["Canines", "Domestic dogs", "Canis familiaris"]


@pytest.mark.asyncio
async def test_concept_alt_labels_default_empty(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that alt_labels defaults to empty list."""
    concept = Concept(scheme_id=scheme.id, pref_label="Test", identifier="alt-default")
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)

    assert concept.alt_labels == []


@pytest.mark.asyncio
async def test_concept_alt_labels_persists(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that alt labels persist correctly to database."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Animals",
        identifier="animals",
        alt_labels=["Fauna", "Creatures"],
    )
    db_session.add(concept)
    await db_session.flush()
    concept_id = concept.id

    # Clear session cache and re-fetch
    db_session.expire_all()
    result = await db_session.execute(select(Concept).where(Concept.id == concept_id))
    fetched = result.scalar_one()

    assert fetched.alt_labels == ["Fauna", "Creatures"]


@pytest.mark.asyncio
async def test_concept_alt_labels_update(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test updating alt labels on existing concept."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Test",
        identifier="alt-update",
        alt_labels=["Original"],
    )
    db_session.add(concept)
    await db_session.flush()

    concept.alt_labels = ["New Label 1", "New Label 2"]
    await db_session.flush()
    await db_session.refresh(concept)

    assert concept.alt_labels == ["New Label 1", "New Label 2"]


@pytest.mark.asyncio
async def test_concept_alt_labels_clear(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test clearing alt labels to empty list."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Test",
        identifier="alt-clear",
        alt_labels=["Label 1", "Label 2"],
    )
    db_session.add(concept)
    await db_session.flush()

    concept.alt_labels = []
    await db_session.flush()
    await db_session.refresh(concept)

    assert concept.alt_labels == []


# concept_type_uris tests


@pytest.mark.asyncio
async def test_concept_type_uris_default(db_session: AsyncSession, scheme: ConceptScheme):
    """concept_type_uris defaults to empty list."""
    concept = Concept(scheme_id=scheme.id, pref_label="Test", identifier="type-default")
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)
    assert concept.concept_type_uris == []


@pytest.mark.asyncio
async def test_concept_type_uris_stored(db_session: AsyncSession, scheme: ConceptScheme):
    """concept_type_uris round-trips through DB."""
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Test",
        identifier="type-stored",
        concept_type_uris=["http://example.org/EducationLevelConcept"],
    )
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)
    assert concept.concept_type_uris == ["http://example.org/EducationLevelConcept"]
