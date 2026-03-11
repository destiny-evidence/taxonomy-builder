"""Identifier allocation, validation, and reconciliation service."""

import re
from uuid import UUID

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project

MAX_COUNTER = 999999


class PrefixRequiredError(Exception):
    """Raised when allocating an identifier without a project prefix."""

    def __init__(self, project_id: UUID) -> None:
        self.project_id = project_id
        super().__init__(
            "Cannot generate identifier: project has no identifier_prefix configured. "
            "Set a prefix in project settings first."
        )


class CounterOverflowError(Exception):
    """Raised when the identifier counter exceeds 999999."""

    def __init__(self, project_id: UUID) -> None:
        self.project_id = project_id
        super().__init__(
            f"Identifier counter overflow for project {project_id}. "
            f"Maximum {MAX_COUNTER} identifiers reached."
        )


class IdentifierService:
    """Owns identifier allocation, import validation, and counter reconciliation."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def allocate(self, project_id: UUID) -> str:
        """Allocate the next sequential identifier for a project.

        Uses UPDATE ... WHERE ... RETURNING to atomically increment only
        when preconditions are met (prefix set, counter below limit).
        No compensating decrements needed on error paths.

        Returns:
            Identifier string like "EVD000001".

        Raises:
            PrefixRequiredError: If project has no identifier_prefix.
            CounterOverflowError: If counter would exceed 999999.
        """
        result = await self.db.execute(
            text(
                "UPDATE projects "
                "SET identifier_counter = identifier_counter + 1 "
                "WHERE id = :project_id "
                "AND identifier_prefix IS NOT NULL "
                "AND identifier_counter < :max_counter "
                "RETURNING identifier_prefix, identifier_counter"
            ),
            {"project_id": project_id, "max_counter": MAX_COUNTER},
        )
        row = result.one_or_none()

        if row is not None:
            prefix, counter = row[0], row[1]
            return f"{prefix}{counter:06d}"

        # No row updated — diagnose why
        state = await self.db.execute(
            select(Project.identifier_prefix, Project.identifier_counter).where(
                Project.id == project_id
            )
        )
        project = state.one()
        if project.identifier_prefix is None:
            raise PrefixRequiredError(project_id)
        raise CounterOverflowError(project_id)

    async def validate_imported(
        self, project_id: UUID, identifiers: list[str]
    ) -> list[dict]:
        """Validate a list of identifiers to be imported.

        Returns a list of conflict dicts. Empty list means no conflicts.
        """
        conflicts: list[dict] = []

        # Check for duplicates within the import list (one conflict per identifier)
        seen: set[str] = set()
        reported: set[str] = set()
        for ident in identifiers:
            if ident in seen and ident not in reported:
                conflicts.append({
                    "type": "duplicate_in_file",
                    "identifier": ident,
                    "message": f"Identifier '{ident}' appears multiple times in import file",
                })
                reported.add(ident)
            seen.add(ident)

        # Check for collisions with existing identifiers in project
        unique_identifiers = list(seen)
        if unique_identifiers:
            result = await self.db.execute(
                select(Concept.identifier)
                .join(ConceptScheme, Concept.scheme_id == ConceptScheme.id)
                .where(
                    ConceptScheme.project_id == project_id,
                    Concept.identifier.in_(unique_identifiers),
                )
            )
            existing = {row[0] for row in result.fetchall()}
            for ident in existing:
                conflicts.append({
                    "type": "collision",
                    "identifier": ident,
                    "message": f"Identifier '{ident}' already exists in project",
                })

        return conflicts

    async def reconcile_counter(
        self, project_id: UUID, imported_identifiers: list[str]
    ) -> None:
        """Advance project counter to account for imported identifiers.

        Monotonic: never moves counter backward.
        """
        result = await self.db.execute(
            select(Project.identifier_prefix).where(Project.id == project_id)
        )
        row = result.one_or_none()
        if row is None or row[0] is None:
            return

        prefix = row[0]

        # Match imported identifiers against ^{PREFIX}(\d+)$
        # Skip values above MAX_COUNTER to avoid bricking future allocations
        pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
        max_found = 0
        for ident in imported_identifiers:
            m = pattern.match(ident)
            if m:
                value = int(m.group(1))
                if value <= MAX_COUNTER:
                    max_found = max(max_found, value)

        if max_found > 0:
            # WHERE clause enforces monotonicity — never moves counter backward
            await self.db.execute(
                update(Project)
                .where(Project.id == project_id, Project.identifier_counter < max_found)
                .values(identifier_counter=max_found)
            )
