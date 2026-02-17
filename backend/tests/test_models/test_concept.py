"""Tests for the Concept model."""

from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from tests.factories import ConceptFactory, ConceptSchemeFactory, flush


@pytest.fixture
async def scheme(db_session: AsyncSession):
    return await flush(
        db_session,
        ConceptSchemeFactory.create(title="Test Scheme", uri="http://example.org/concepts"),
    )


@pytest.mark.asyncio
async def test_create_concept(db_session: AsyncSession, scheme) -> None:
    """Test creating a concept."""
    concept = await flush(
        db_session,
        ConceptFactory.create(
            scheme=scheme,
            pref_label="Test Concept",
            identifier="test",
            definition="A test concept",
            scope_note="Use for testing",
        ),
    )

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
async def test_concept_id_is_uuidv7(db_session: AsyncSession, scheme) -> None:
    """Test that concept IDs are UUIDv7."""
    concept = await flush(db_session, ConceptFactory.create(scheme=scheme))

    assert concept.id.version == 7


@pytest.mark.asyncio
async def test_concept_pref_label_required(db_session: AsyncSession, scheme) -> None:
    """Test that pref_label is required."""
    from sqlalchemy.exc import IntegrityError

    concept = Concept(scheme_id=scheme.id, pref_label=None)  # type: ignore[arg-type]
    db_session.add(concept)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_concept_optional_fields(db_session: AsyncSession, scheme) -> None:
    """Test that identifier, definition, scope_note are optional."""
    concept = await flush(
        db_session,
        ConceptFactory.create(scheme=scheme, identifier=None, definition=None, scope_note=None),
    )

    assert concept.identifier is None
    assert concept.definition is None
    assert concept.scope_note is None
    # URI is None when identifier is not set
    assert concept.uri is None


@pytest.mark.asyncio
async def test_concept_belongs_to_scheme(db_session: AsyncSession, scheme) -> None:
    """Test that concept has a relationship to scheme."""
    concept = await flush(db_session, ConceptFactory.create(scheme=scheme))

    assert concept.scheme.id == scheme.id
    assert concept.scheme.title == "Test Scheme"


@pytest.mark.asyncio
async def test_scheme_has_many_concepts(db_session: AsyncSession, scheme) -> None:
    """Test that a scheme can have multiple concepts."""
    ConceptFactory.create(scheme=scheme, pref_label="Concept 1")
    ConceptFactory.create(scheme=scheme, pref_label="Concept 2")
    await db_session.flush()

    await db_session.refresh(scheme)
    assert len(scheme.concepts) == 2


@pytest.mark.asyncio
async def test_cascade_delete_with_scheme(db_session: AsyncSession, scheme) -> None:
    """Test that concepts are deleted when scheme is deleted."""
    concept = await flush(db_session, ConceptFactory.create(scheme=scheme))
    concept_id = concept.id

    await db_session.delete(scheme)
    await db_session.flush()

    result = await db_session.execute(select(Concept).where(Concept.id == concept_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_duplicate_pref_label_allowed_in_scheme(db_session: AsyncSession, scheme) -> None:
    """Test that duplicate pref_labels are allowed within a scheme."""
    # SKOS allows duplicate labels (though not recommended)
    c1 = ConceptFactory.create(scheme=scheme, pref_label="Same Label", identifier="same-label-1")
    c2 = ConceptFactory.create(scheme=scheme, pref_label="Same Label", identifier="same-label-2")
    await db_session.flush()

    assert c1.id != c2.id
    assert c1.pref_label == c2.pref_label


# Alt labels tests


@pytest.mark.asyncio
async def test_concept_with_alt_labels(db_session: AsyncSession, scheme) -> None:
    """Test creating a concept with alt labels."""
    concept = await flush(
        db_session,
        ConceptFactory.create(
            scheme=scheme,
            pref_label="Dogs",
            alt_labels=["Canines", "Domestic dogs", "Canis familiaris"],
        ),
    )

    assert concept.alt_labels == ["Canines", "Domestic dogs", "Canis familiaris"]


@pytest.mark.asyncio
async def test_concept_alt_labels_default_empty(db_session: AsyncSession, scheme) -> None:
    """Test that alt_labels defaults to empty list."""
    concept = await flush(db_session, ConceptFactory.create(scheme=scheme))

    assert concept.alt_labels == []


@pytest.mark.asyncio
async def test_concept_alt_labels_persists(db_session: AsyncSession, scheme) -> None:
    """Test that alt labels persist correctly to database."""
    concept = await flush(
        db_session,
        ConceptFactory.create(scheme=scheme, pref_label="Animals", alt_labels=["Fauna", "Creatures"]),
    )
    concept_id = concept.id

    # Clear session cache and re-fetch
    db_session.expire_all()
    result = await db_session.execute(select(Concept).where(Concept.id == concept_id))
    fetched = result.scalar_one()

    assert fetched.alt_labels == ["Fauna", "Creatures"]


@pytest.mark.asyncio
async def test_concept_alt_labels_update(db_session: AsyncSession, scheme) -> None:
    """Test updating alt labels on existing concept."""
    concept = await flush(
        db_session, ConceptFactory.create(scheme=scheme, alt_labels=["Original"])
    )

    concept.alt_labels = ["New Label 1", "New Label 2"]
    await db_session.flush()
    await db_session.refresh(concept)

    assert concept.alt_labels == ["New Label 1", "New Label 2"]


@pytest.mark.asyncio
async def test_concept_alt_labels_clear(db_session: AsyncSession, scheme) -> None:
    """Test clearing alt labels to empty list."""
    concept = await flush(
        db_session, ConceptFactory.create(scheme=scheme, alt_labels=["Label 1", "Label 2"])
    )

    concept.alt_labels = []
    await db_session.flush()
    await db_session.refresh(concept)

    assert concept.alt_labels == []
