"""Tests for the Concept model."""

from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project


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
    concept = Concept(scheme_id=scheme.id, pref_label="UUID Test")
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)

    assert concept.id.version == 7


@pytest.mark.asyncio
async def test_concept_pref_label_required(db_session: AsyncSession, scheme: ConceptScheme) -> None:
    """Test that pref_label is required."""
    from sqlalchemy.exc import IntegrityError

    concept = Concept(scheme_id=scheme.id, pref_label=None)  # type: ignore[arg-type]
    db_session.add(concept)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_concept_optional_fields(db_session: AsyncSession, scheme: ConceptScheme) -> None:
    """Test that identifier, definition, scope_note are optional."""
    concept = Concept(scheme_id=scheme.id, pref_label="Minimal Concept")
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)

    assert concept.identifier is None
    assert concept.definition is None
    assert concept.scope_note is None
    # URI is None when identifier is not set
    assert concept.uri is None


@pytest.mark.asyncio
async def test_concept_belongs_to_scheme(db_session: AsyncSession, scheme: ConceptScheme) -> None:
    """Test that concept has a relationship to scheme."""
    concept = Concept(scheme_id=scheme.id, pref_label="Related Concept")
    db_session.add(concept)
    await db_session.flush()
    await db_session.refresh(concept)

    assert concept.scheme.id == scheme.id
    assert concept.scheme.title == "Test Scheme"


@pytest.mark.asyncio
async def test_scheme_has_many_concepts(db_session: AsyncSession, scheme: ConceptScheme) -> None:
    """Test that a scheme can have multiple concepts."""
    concept1 = Concept(scheme_id=scheme.id, pref_label="Concept 1")
    concept2 = Concept(scheme_id=scheme.id, pref_label="Concept 2")
    db_session.add_all([concept1, concept2])
    await db_session.flush()

    await db_session.refresh(scheme)
    assert len(scheme.concepts) == 2


@pytest.mark.asyncio
async def test_cascade_delete_with_scheme(db_session: AsyncSession, scheme: ConceptScheme) -> None:
    """Test that concepts are deleted when scheme is deleted."""
    concept = Concept(scheme_id=scheme.id, pref_label="To Delete")
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
    concept1 = Concept(scheme_id=scheme.id, pref_label="Same Label")
    concept2 = Concept(scheme_id=scheme.id, pref_label="Same Label")
    db_session.add_all([concept1, concept2])
    await db_session.flush()

    assert concept1.id != concept2.id
    assert concept1.pref_label == concept2.pref_label
