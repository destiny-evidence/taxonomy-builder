"""Identifier allocation, validation, and reconciliation service."""

from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

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
