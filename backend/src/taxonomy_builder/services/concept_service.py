"""Concept service for business logic."""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_broader import ConceptBroader
from taxonomy_builder.models.concept_related import ConceptRelated
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.schemas.concept import ConceptCreate, ConceptUpdate
from taxonomy_builder.services.change_tracker import ChangeTracker


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


class CycleDetectedError(Exception):
    """Raised when a move operation would create a cycle in the hierarchy."""

    def __init__(self, concept_id: UUID, target_id: UUID) -> None:
        self.concept_id = concept_id
        self.target_id = target_id
        super().__init__("Cannot move concept to its own descendant - would create cycle")


class SelfReferenceError(Exception):
    """Raised when trying to make a concept its own parent."""

    def __init__(self, concept_id: UUID) -> None:
        self.concept_id = concept_id
        super().__init__("Cannot make concept a parent of itself")


class RelatedRelationshipExistsError(Exception):
    """Raised when a related relationship already exists."""

    def __init__(self, concept_id: UUID, related_concept_id: UUID) -> None:
        self.concept_id = concept_id
        self.related_concept_id = related_concept_id
        super().__init__(f"Related relationship already exists")


class RelatedRelationshipNotFoundError(Exception):
    """Raised when a related relationship is not found."""

    def __init__(self, concept_id: UUID, related_concept_id: UUID) -> None:
        self.concept_id = concept_id
        self.related_concept_id = related_concept_id
        super().__init__(f"Related relationship not found")


class RelatedSelfReferenceError(Exception):
    """Raised when trying to relate a concept to itself."""

    def __init__(self, concept_id: UUID) -> None:
        self.concept_id = concept_id
        super().__init__(f"A concept cannot be related to itself")


class RelatedSameSchemeError(Exception):
    """Raised when trying to relate concepts from different schemes."""

    def __init__(self, concept_id: UUID, related_concept_id: UUID) -> None:
        self.concept_id = concept_id
        self.related_concept_id = related_concept_id
        super().__init__(f"Related concepts must be in the same scheme")


class ConceptService:
    """Service for managing concepts."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._tracker = ChangeTracker(db)

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
            .options(
                selectinload(Concept.broader),
                selectinload(Concept._related_as_subject),
                selectinload(Concept._related_as_object),
            )
            .order_by(Concept.pref_label)
        )
        return list(result.scalars().all())

    async def create_concept(
        self, scheme_id: UUID, concept_in: ConceptCreate, user_id: UUID | None = None
    ) -> Concept:
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

        # Record change event
        await self._tracker.record(
            scheme_id=scheme_id,
            entity_type="concept",
            entity_id=concept.id,
            action="create",
            before=None,
            after=self._tracker.serialize_concept(concept),
            user_id=user_id,
        )

        # Re-fetch to get broader relationship loaded
        return await self.get_concept(concept.id)

    async def get_concept(self, concept_id: UUID) -> Concept:
        """Get a concept by ID with broader and related relationships loaded."""
        result = await self.db.execute(
            select(Concept)
            .where(Concept.id == concept_id)
            .options(
                selectinload(Concept.broader),
                selectinload(Concept._related_as_subject),
                selectinload(Concept._related_as_object),
            )
            .execution_options(populate_existing=True)
        )
        concept = result.scalar_one_or_none()
        if concept is None:
            raise ConceptNotFoundError(concept_id)
        return concept

    async def update_concept(
        self, concept_id: UUID, concept_in: ConceptUpdate, user_id: UUID | None = None
    ) -> Concept:
        """Update an existing concept."""
        concept = await self.get_concept(concept_id)

        # Capture before state
        before_state = self._tracker.serialize_concept(concept)

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

        # Record change event
        await self._tracker.record(
            scheme_id=concept.scheme_id,
            entity_type="concept",
            entity_id=concept_id,
            action="update",
            before=before_state,
            after=self._tracker.serialize_concept(concept),
            user_id=user_id,
        )

        # Re-fetch to get fresh broader relationship
        return await self.get_concept(concept_id)

    async def delete_concept(self, concept_id: UUID, user_id: UUID | None = None) -> None:
        """Delete a concept."""
        concept = await self.get_concept(concept_id)

        # Capture before state and scheme_id before deletion
        before_state = self._tracker.serialize_concept(concept)
        scheme_id = concept.scheme_id
        concept_label = concept.pref_label

        # Record deletion of broader relationships (where this concept is the narrower)
        result = await self.db.execute(
            select(ConceptBroader).where(ConceptBroader.concept_id == concept_id)
        )
        broader_rels = list(result.scalars().all())
        for rel in broader_rels:
            broader_concept = await self.get_concept(rel.broader_concept_id)
            await self._tracker.record(
                scheme_id=scheme_id,
                entity_type="concept_broader",
                entity_id=rel.concept_id,
                action="delete",
                before=self._tracker.serialize_broader(
                    rel.concept_id,
                    rel.broader_concept_id,
                    concept_label,
                    broader_concept.pref_label,
                ),
                after=None,
                user_id=user_id,
            )

        # Record deletion of narrower relationships (where this concept is the broader)
        result = await self.db.execute(
            select(ConceptBroader).where(ConceptBroader.broader_concept_id == concept_id)
        )
        narrower_rels = list(result.scalars().all())
        for rel in narrower_rels:
            narrower_concept = await self.get_concept(rel.concept_id)
            await self._tracker.record(
                scheme_id=scheme_id,
                entity_type="concept_broader",
                entity_id=rel.concept_id,
                action="delete",
                before=self._tracker.serialize_broader(
                    rel.concept_id,
                    rel.broader_concept_id,
                    narrower_concept.pref_label,
                    concept_label,
                ),
                after=None,
                user_id=user_id,
            )

        # Record deletion of related relationships (either as subject or object)
        result = await self.db.execute(
            select(ConceptRelated).where(
                or_(
                    ConceptRelated.concept_id == concept_id,
                    ConceptRelated.related_concept_id == concept_id,
                )
            )
        )
        related_rels = list(result.scalars().all())
        for rel in related_rels:
            # Get the other concept's label
            other_concept_id = (
                rel.related_concept_id
                if rel.concept_id == concept_id
                else rel.concept_id
            )
            other_concept = await self.get_concept(other_concept_id)
            # Determine labels based on ID ordering
            if rel.concept_id < rel.related_concept_id:
                id1, id2 = rel.concept_id, rel.related_concept_id
                if rel.concept_id == concept_id:
                    label1, label2 = concept_label, other_concept.pref_label
                else:
                    label1, label2 = other_concept.pref_label, concept_label
            else:
                id1, id2 = rel.related_concept_id, rel.concept_id
                if rel.related_concept_id == concept_id:
                    label1, label2 = concept_label, other_concept.pref_label
                else:
                    label1, label2 = other_concept.pref_label, concept_label
            await self._tracker.record(
                scheme_id=scheme_id,
                entity_type="concept_related",
                entity_id=concept_id,
                action="delete",
                before=self._tracker.serialize_related(id1, id2, label1, label2),
                after=None,
                user_id=user_id,
            )

        await self.db.delete(concept)
        await self.db.flush()

        # Record change event
        await self._tracker.record(
            scheme_id=scheme_id,
            entity_type="concept",
            entity_id=concept_id,
            action="delete",
            before=before_state,
            after=None,
            user_id=user_id,
        )

    async def add_broader(
        self, concept_id: UUID, broader_concept_id: UUID, user_id: UUID | None = None
    ) -> None:
        """Add a broader relationship."""
        # Verify both concepts exist
        concept = await self.get_concept(concept_id)
        broader_concept = await self.get_concept(broader_concept_id)

        rel = ConceptBroader(concept_id=concept_id, broader_concept_id=broader_concept_id)
        self.db.add(rel)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise BroaderRelationshipExistsError(concept_id, broader_concept_id)

        # Record change event
        await self._tracker.record(
            scheme_id=concept.scheme_id,
            entity_type="concept_broader",
            entity_id=concept_id,
            action="create",
            before=None,
            after=self._tracker.serialize_broader(
                concept_id,
                broader_concept_id,
                concept.pref_label,
                broader_concept.pref_label,
            ),
            user_id=user_id,
        )

    async def remove_broader(
        self, concept_id: UUID, broader_concept_id: UUID, user_id: UUID | None = None
    ) -> None:
        """Remove a broader relationship."""
        concept = await self.get_concept(concept_id)
        broader_concept = await self.get_concept(broader_concept_id)

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

        # Record change event
        await self._tracker.record(
            scheme_id=concept.scheme_id,
            entity_type="concept_broader",
            entity_id=concept_id,
            action="delete",
            before=self._tracker.serialize_broader(
                concept_id,
                broader_concept_id,
                concept.pref_label,
                broader_concept.pref_label,
            ),
            after=None,
            user_id=user_id,
        )

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

    async def add_related(
        self, concept_id: UUID, related_concept_id: UUID, user_id: UUID | None = None
    ) -> None:
        """Add a related relationship between two concepts.

        The relationship is symmetric and stored with concept_id < related_concept_id.
        Both concepts must be in the same scheme.
        """
        # Check for self-reference
        if concept_id == related_concept_id:
            raise RelatedSelfReferenceError(concept_id)

        # Verify both concepts exist and get their scheme_ids
        concept = await self.get_concept(concept_id)
        related_concept = await self.get_concept(related_concept_id)

        # Check same scheme
        if concept.scheme_id != related_concept.scheme_id:
            raise RelatedSameSchemeError(concept_id, related_concept_id)

        # Order IDs - smaller first
        if concept_id < related_concept_id:
            id1, id2 = concept_id, related_concept_id
            label1, label2 = concept.pref_label, related_concept.pref_label
        else:
            id1, id2 = related_concept_id, concept_id
            label1, label2 = related_concept.pref_label, concept.pref_label

        rel = ConceptRelated(concept_id=id1, related_concept_id=id2)
        self.db.add(rel)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise RelatedRelationshipExistsError(concept_id, related_concept_id)

        # Record change event
        await self._tracker.record(
            scheme_id=concept.scheme_id,
            entity_type="concept_related",
            entity_id=concept_id,
            action="create",
            before=None,
            after=self._tracker.serialize_related(id1, id2, label1, label2),
            user_id=user_id,
        )

    async def remove_related(
        self, concept_id: UUID, related_concept_id: UUID, user_id: UUID | None = None
    ) -> None:
        """Remove a related relationship between two concepts.

        Works regardless of which concept is passed first (symmetric).
        """
        concept = await self.get_concept(concept_id)
        related_concept = await self.get_concept(related_concept_id)

        # Order IDs - smaller first (to match storage)
        if concept_id < related_concept_id:
            id1, id2 = concept_id, related_concept_id
            label1, label2 = concept.pref_label, related_concept.pref_label
        else:
            id1, id2 = related_concept_id, concept_id
            label1, label2 = related_concept.pref_label, concept.pref_label

        result = await self.db.execute(
            select(ConceptRelated).where(
                ConceptRelated.concept_id == id1,
                ConceptRelated.related_concept_id == id2,
            )
        )
        rel = result.scalar_one_or_none()
        if rel is None:
            raise RelatedRelationshipNotFoundError(concept_id, related_concept_id)
        await self.db.delete(rel)
        await self.db.flush()

        # Record change event
        await self._tracker.record(
            scheme_id=concept.scheme_id,
            entity_type="concept_related",
            entity_id=concept_id,
            action="delete",
            before=self._tracker.serialize_related(id1, id2, label1, label2),
            after=None,
            user_id=user_id,
        )

    async def _is_descendant(self, concept_id: UUID, potential_descendant_id: UUID) -> bool:
        """Check if potential_descendant_id is a descendant of concept_id.

        Uses BFS to traverse the narrower (children) relationships.
        Returns True if potential_descendant_id is found under concept_id.
        """
        visited: set[UUID] = set()
        queue: list[UUID] = [concept_id]

        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            # Get narrower concepts (children) - concepts where this is the broader
            result = await self.db.execute(
                select(ConceptBroader.concept_id).where(
                    ConceptBroader.broader_concept_id == current_id
                )
            )
            children_ids = [row[0] for row in result.fetchall()]

            for child_id in children_ids:
                if child_id == potential_descendant_id:
                    return True
                queue.append(child_id)

        return False

    async def move_concept(
        self,
        concept_id: UUID,
        new_parent_id: UUID | None,
        previous_parent_id: UUID | None,
        user_id: UUID | None = None,
    ) -> Concept:
        """Move a concept to a new parent (or to root if new_parent_id is None).

        Args:
            concept_id: The concept being moved
            new_parent_id: The new parent (None = move to root)
            previous_parent_id: The parent to replace (None = add new parent without removing)
            user_id: The ID of the user performing the move

        Raises:
            ConceptNotFoundError: If concept or parent doesn't exist
            SelfReferenceError: If new_parent_id == concept_id
            CycleDetectedError: If new_parent_id is a descendant of concept_id
        """
        # Verify concept exists
        await self.get_concept(concept_id)

        # Validate: not moving to self
        if new_parent_id == concept_id:
            raise SelfReferenceError(concept_id)

        # Validate: new parent exists (if specified)
        if new_parent_id is not None:
            await self.get_concept(new_parent_id)

            # Validate: not moving to descendant (cycle detection)
            if await self._is_descendant(concept_id, new_parent_id):
                raise CycleDetectedError(concept_id, new_parent_id)

        # Remove previous parent relationship (if specified)
        if previous_parent_id is not None:
            try:
                await self.remove_broader(concept_id, previous_parent_id, user_id=user_id)
            except BroaderRelationshipNotFoundError:
                pass  # Previous parent was already removed, continue

        # Add new parent relationship (if specified)
        if new_parent_id is not None:
            try:
                await self.add_broader(concept_id, new_parent_id, user_id=user_id)
            except BroaderRelationshipExistsError:
                pass  # Already has this parent, that's fine

        # Re-fetch to get fresh relationships
        return await self.get_concept(concept_id)
