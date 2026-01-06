"""Concept service for business logic."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_broader import ConceptBroader
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.schemas.concept import ConceptCreate, ConceptUpdate


class ConceptNotFoundError(Exception):
    """Raised when a concept is not found."""

    def __init__(self, concept_id: UUID) -> None:
        self.concept_id = concept_id
        super().__init__(f"Concept with id '{concept_id}' not found")


class SchemeNotFoundError(Exception):
    """Raised when a concept scheme is not found."""

    def __init__(self, scheme_id: UUID) -> None:
        self.scheme_id = scheme_id
        super().__init__(f"Concept scheme with id '{scheme_id}' not found")


class BroaderRelationshipExistsError(Exception):
    """Raised when a broader relationship already exists."""

    def __init__(self, concept_id: UUID, broader_concept_id: UUID) -> None:
        self.concept_id = concept_id
        self.broader_concept_id = broader_concept_id
        super().__init__(f"Broader relationship already exists")


class BroaderRelationshipNotFoundError(Exception):
    """Raised when a broader relationship is not found."""

    def __init__(self, concept_id: UUID, broader_concept_id: UUID) -> None:
        self.concept_id = concept_id
        self.broader_concept_id = broader_concept_id
        super().__init__(f"Broader relationship not found")


class ConceptService:
    """Service for managing concepts."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_scheme(self, scheme_id: UUID) -> ConceptScheme:
        """Get a scheme by ID or raise SchemeNotFoundError."""
        result = await self.db.execute(
            select(ConceptScheme).where(ConceptScheme.id == scheme_id)
        )
        scheme = result.scalar_one_or_none()
        if scheme is None:
            raise SchemeNotFoundError(scheme_id)
        return scheme

    async def list_concepts_for_scheme(self, scheme_id: UUID) -> list[Concept]:
        """List all concepts for a scheme, ordered alphabetically by pref_label."""
        await self._get_scheme(scheme_id)

        result = await self.db.execute(
            select(Concept)
            .where(Concept.scheme_id == scheme_id)
            .options(selectinload(Concept.broader))
            .order_by(Concept.pref_label)
        )
        return list(result.scalars().all())

    async def create_concept(self, scheme_id: UUID, concept_in: ConceptCreate) -> Concept:
        """Create a new concept in a scheme."""
        await self._get_scheme(scheme_id)

        concept = Concept(
            scheme_id=scheme_id,
            pref_label=concept_in.pref_label,
            identifier=concept_in.identifier,
            definition=concept_in.definition,
            scope_note=concept_in.scope_note,
            alt_labels=concept_in.alt_labels,
        )
        self.db.add(concept)
        await self.db.flush()
        # Re-fetch to get broader relationship loaded
        return await self.get_concept(concept.id)

    async def get_concept(self, concept_id: UUID) -> Concept:
        """Get a concept by ID with broader relationships loaded."""
        result = await self.db.execute(
            select(Concept)
            .where(Concept.id == concept_id)
            .options(selectinload(Concept.broader))
            .execution_options(populate_existing=True)
        )
        concept = result.scalar_one_or_none()
        if concept is None:
            raise ConceptNotFoundError(concept_id)
        return concept

    async def update_concept(self, concept_id: UUID, concept_in: ConceptUpdate) -> Concept:
        """Update an existing concept."""
        concept = await self.get_concept(concept_id)

        if concept_in.pref_label is not None:
            concept.pref_label = concept_in.pref_label
        if concept_in.identifier is not None:
            concept.identifier = concept_in.identifier
        if concept_in.definition is not None:
            concept.definition = concept_in.definition
        if concept_in.scope_note is not None:
            concept.scope_note = concept_in.scope_note
        if concept_in.alt_labels is not None:
            concept.alt_labels = concept_in.alt_labels

        await self.db.flush()
        # Re-fetch to get fresh broader relationship
        return await self.get_concept(concept_id)

    async def delete_concept(self, concept_id: UUID) -> None:
        """Delete a concept."""
        concept = await self.get_concept(concept_id)
        await self.db.delete(concept)
        await self.db.flush()

    async def add_broader(self, concept_id: UUID, broader_concept_id: UUID) -> None:
        """Add a broader relationship."""
        # Verify both concepts exist
        await self.get_concept(concept_id)
        await self.get_concept(broader_concept_id)

        rel = ConceptBroader(concept_id=concept_id, broader_concept_id=broader_concept_id)
        self.db.add(rel)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise BroaderRelationshipExistsError(concept_id, broader_concept_id)

    async def remove_broader(self, concept_id: UUID, broader_concept_id: UUID) -> None:
        """Remove a broader relationship."""
        result = await self.db.execute(
            select(ConceptBroader).where(
                ConceptBroader.concept_id == concept_id,
                ConceptBroader.broader_concept_id == broader_concept_id,
            )
        )
        rel = result.scalar_one_or_none()
        if rel is None:
            raise BroaderRelationshipNotFoundError(concept_id, broader_concept_id)
        await self.db.delete(rel)
        await self.db.flush()

    async def get_tree(self, scheme_id: UUID) -> list[dict]:
        """Get the concept tree for a scheme as a DAG.

        Returns a list of root concepts (concepts with no broader relationships),
        each with a 'narrower' field containing their children recursively.
        Concepts with multiple parents appear under each parent.
        """
        await self._get_scheme(scheme_id)

        # Get all concepts for the scheme
        result = await self.db.execute(
            select(Concept)
            .where(Concept.scheme_id == scheme_id)
            .order_by(Concept.pref_label)
        )
        concepts = list(result.scalars().all())

        if not concepts:
            return []

        # Build a map of concept_id -> concept
        concept_map = {c.id: c for c in concepts}

        # Build parent -> children map
        children_map: dict[UUID, list[Concept]] = {c.id: [] for c in concepts}

        # Get all broader relationships for this scheme's concepts
        concept_ids = list(concept_map.keys())
        result = await self.db.execute(
            select(ConceptBroader).where(ConceptBroader.concept_id.in_(concept_ids))
        )
        broader_rels = list(result.scalars().all())

        # Track which concepts have parents (are not roots)
        has_parent: set[UUID] = set()

        for rel in broader_rels:
            if rel.broader_concept_id in concept_map:
                children_map[rel.broader_concept_id].append(concept_map[rel.concept_id])
                has_parent.add(rel.concept_id)

        # Find root concepts (no parents)
        roots = [c for c in concepts if c.id not in has_parent]

        def build_tree_node(concept: Concept) -> dict:
            """Recursively build a tree node."""
            children = sorted(children_map[concept.id], key=lambda c: c.pref_label)
            return {
                "id": concept.id,
                "scheme_id": concept.scheme_id,
                "identifier": concept.identifier,
                "pref_label": concept.pref_label,
                "definition": concept.definition,
                "scope_note": concept.scope_note,
                "uri": concept.uri,
                "alt_labels": concept.alt_labels,
                "created_at": concept.created_at,
                "updated_at": concept.updated_at,
                "narrower": [build_tree_node(child) for child in children],
            }

        return [build_tree_node(root) for root in roots]
