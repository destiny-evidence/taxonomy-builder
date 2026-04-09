"""MCP tools for taxonomy builder."""

from uuid import UUID

from fastmcp import Context

from taxonomy_builder.config import settings
from taxonomy_builder.database import db_manager
from taxonomy_builder.mcp.formatters import (
    format_concept,
    format_concept_brief,
    format_project,
    format_scheme,
    format_tree,
)
from taxonomy_builder.mcp.server import mcp
from taxonomy_builder.schemas.concept import ConceptCreate, ConceptUpdate
from taxonomy_builder.schemas.concept_scheme import ConceptSchemeCreate, ConceptSchemeUpdate
from taxonomy_builder.schemas.project import ProjectCreate
from taxonomy_builder.services.concept_scheme_service import ConceptSchemeService
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.history_service import HistoryService
from taxonomy_builder.services.project_service import ProjectService
from taxonomy_builder.services.skos_export_service import SKOSExportService


def _get_user_id(ctx: Context) -> UUID | None:
    """Extract user_id from MCP auth context.

    When auth is enabled, the KeycloakTokenVerifier sets client_id to the
    local user's UUID. When auth is disabled, returns None (no user attribution).

    Raises if auth is enabled but no client_id is present — that means the
    request somehow bypassed the auth middleware.
    """
    client_id = ctx.client_id
    if client_id is not None:
        return UUID(client_id)

    if settings.mcp_auth:
        raise RuntimeError("MCP auth is enabled but no client_id in request context")

    return None


# --- Exploring tools ---


@mcp.tool()
async def list_projects(ctx: Context) -> str:
    """List all taxonomy projects.

    Returns a list of all projects with their names, namespaces, and IDs.
    Use the project ID to explore its concept schemes.
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ProjectService(session, user_id=user_id)
        projects = await svc.list_projects()
    if not projects:
        return "No projects found."
    return "\n\n".join(format_project(p) for p in projects)


@mcp.tool()
async def create_project(
    ctx: Context,
    name: str,
    namespace: str,
    identifier_prefix: str,
    description: str | None = None,
) -> str:
    """Create a new taxonomy project.

    Args:
        name: Project name (must be unique)
        namespace: Base URI namespace for the project (e.g. "https://example.org/vocab/")
        identifier_prefix: 1-4 uppercase letters used to prefix concept identifiers (e.g. "EVD")
        description: Optional project description
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ProjectService(session, user_id=user_id)
        project = await svc.create_project(
            ProjectCreate(
                name=name,
                namespace=namespace,
                identifier_prefix=identifier_prefix,
                description=description,
            )
        )
    return f"Created project: {format_project(project)}"


@mcp.tool()
async def list_schemes(ctx: Context, project_id: str) -> str:
    """List all concept schemes in a project.

    Args:
        project_id: UUID of the project
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ConceptSchemeService(session, user_id=user_id)
        schemes = await svc.list_schemes_for_project(UUID(project_id))
    if not schemes:
        return "No schemes found in this project."
    return "\n\n".join(format_scheme(s) for s in schemes)


@mcp.tool()
async def get_scheme(ctx: Context, scheme_id: str) -> str:
    """Get details about a concept scheme including concept count.

    Args:
        scheme_id: UUID of the concept scheme
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ConceptSchemeService(session, user_id=user_id)
        scheme = await svc.get_scheme(UUID(scheme_id))
    return format_scheme(scheme)


@mcp.tool()
async def get_concept_tree(ctx: Context, scheme_id: str) -> str:
    """Get the full concept hierarchy for a scheme as an indented tree.

    Shows all concepts organised by their broader/narrower relationships.
    Top-level concepts (no broader) appear at root. Children are indented.
    Use this to understand the overall structure before making changes.

    Args:
        scheme_id: UUID of the concept scheme
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ConceptService(session, user_id=user_id)
        tree = await svc.get_tree(UUID(scheme_id))
    return format_tree(tree)


@mcp.tool()
async def search_concepts(
    ctx: Context,
    query: str,
    scheme_id: str | None = None,
    project_id: str | None = None,
) -> str:
    """Search for concepts by label or definition text.

    Searches pref_label and definition fields using case-insensitive matching.
    Provide scheme_id to search within one scheme, or project_id to search
    across all schemes in a project. At least one must be given.

    Args:
        query: Search text to match against labels and definitions
        scheme_id: UUID of a concept scheme to search within
        project_id: UUID of a project to search across all its schemes
    """
    if not scheme_id and not project_id:
        return "Provide either scheme_id or project_id."
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ConceptService(session, user_id=user_id)
        results = await svc.search_concepts(
            query,
            scheme_id=UUID(scheme_id) if scheme_id else None,
            project_id=UUID(project_id) if project_id else None,
        )
    if not results:
        return f"No concepts matching '{query}'."
    lines = [f"Found {len(results)} concept(s):"]
    for c in results:
        lines.append(f"  {format_concept_brief(c)}")
    return "\n".join(lines)


@mcp.tool()
async def get_concept(ctx: Context, concept_id: str) -> str:
    """Get full details of a concept including relationships.

    Returns the concept's label, definition, scope note, alt labels,
    and its broader, narrower, and related concepts.

    Args:
        concept_id: UUID of the concept
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ConceptService(session, user_id=user_id)
        concept = await svc.get_concept(UUID(concept_id))
    return format_concept(concept)


# --- Building tools ---


@mcp.tool()
async def create_scheme(
    ctx: Context,
    project_id: str,
    title: str,
    description: str | None = None,
    uri: str | None = None,
) -> str:
    """Create a new concept scheme in a project.

    Args:
        project_id: UUID of the project
        title: Title for the new scheme
        description: Optional description
        uri: Optional base URI for concepts in this scheme
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ConceptSchemeService(session, user_id=user_id)
        scheme = await svc.create_scheme(
            UUID(project_id),
            ConceptSchemeCreate(title=title, description=description, uri=uri),
        )
    return f"Created scheme: {format_scheme(scheme)}"


@mcp.tool()
async def create_concept(
    ctx: Context,
    scheme_id: str,
    pref_label: str,
    definition: str | None = None,
    scope_note: str | None = None,
    alt_labels: list[str] | None = None,
    broader_concept_id: str | None = None,
) -> str:
    """Create a new concept in a scheme.

    Optionally place it under a parent concept via broader_concept_id.
    An identifier is automatically allocated.

    Args:
        scheme_id: UUID of the concept scheme
        pref_label: Preferred label for the concept
        definition: Optional definition text
        scope_note: Optional scope note
        alt_labels: Optional list of alternative labels
        broader_concept_id: Optional UUID of parent concept
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        concept_svc = ConceptService(session, user_id=user_id)
        scheme = await concept_svc.get_scheme(UUID(scheme_id))

        project_svc = ProjectService(session, user_id=user_id)
        identifier = await project_svc.allocate_identifier(scheme.project_id)

        concept = await concept_svc.create_concept(
            UUID(scheme_id),
            ConceptCreate(
                pref_label=pref_label,
                definition=definition,
                scope_note=scope_note,
                alt_labels=alt_labels or [],
            ),
            identifier=identifier,
            scheme=scheme,
        )

        if broader_concept_id:
            await concept_svc.add_broader(concept.id, UUID(broader_concept_id))
            concept = await concept_svc.get_concept(concept.id)

    return f"Created: {format_concept(concept)}"


@mcp.tool()
async def create_concepts_batch(
    ctx: Context,
    scheme_id: str,
    concepts: list[dict],
) -> str:
    """Create multiple concepts in a single operation.

    Each concept dict should have:
    - pref_label (required): The preferred label
    - definition (optional): Definition text
    - scope_note (optional): Scope note
    - alt_labels (optional): List of alternative labels
    - broader_concept_id (optional): UUID of parent concept

    For broader_concept_id, you can reference concepts created earlier in
    the same batch by using the special syntax "#N" where N is the 0-based
    index of the concept in this batch. For example, "#0" refers to the
    first concept in the batch.

    Args:
        scheme_id: UUID of the concept scheme
        concepts: List of concept definitions
    """
    user_id = _get_user_id(ctx)
    created = []
    async with db_manager.session() as session:
        concept_svc = ConceptService(session, user_id=user_id)
        scheme = await concept_svc.get_scheme(UUID(scheme_id))

        project_svc = ProjectService(session, user_id=user_id)

        for c in concepts:
            identifier = await project_svc.allocate_identifier(scheme.project_id)
            concept = await concept_svc.create_concept(
                UUID(scheme_id),
                ConceptCreate(
                    pref_label=c["pref_label"],
                    definition=c.get("definition"),
                    scope_note=c.get("scope_note"),
                    alt_labels=c.get("alt_labels", []),
                ),
                identifier=identifier,
                scheme=scheme,
            )

            broader_ref = c.get("broader_concept_id")
            if broader_ref:
                # Support "#N" syntax for referencing earlier batch items
                if isinstance(broader_ref, str) and broader_ref.startswith("#"):
                    idx = int(broader_ref[1:])
                    broader_id = created[idx].id
                else:
                    broader_id = UUID(broader_ref)
                await concept_svc.add_broader(concept.id, broader_id)
                concept = await concept_svc.get_concept(concept.id)

            created.append(concept)

    lines = [f"Created {len(created)} concept(s):"]
    for c in created:
        lines.append(f"  {format_concept_brief(c)}")
    return "\n".join(lines)


@mcp.tool()
async def set_broader(
    ctx: Context,
    concept_id: str,
    broader_concept_id: str,
    action: str = "add",
) -> str:
    """Add or remove a broader (parent) relationship.

    Args:
        concept_id: UUID of the narrower (child) concept
        broader_concept_id: UUID of the broader (parent) concept
        action: "add" or "remove"
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ConceptService(session, user_id=user_id)
        if action == "add":
            await svc.add_broader(UUID(concept_id), UUID(broader_concept_id))
        elif action == "remove":
            await svc.remove_broader(UUID(concept_id), UUID(broader_concept_id))
        else:
            return f"Invalid action '{action}'. Use 'add' or 'remove'."
        concept = await svc.get_concept(UUID(concept_id))
    return format_concept(concept)


@mcp.tool()
async def move_concept(
    ctx: Context,
    concept_id: str,
    new_parent_id: str | None = None,
    previous_parent_id: str | None = None,
) -> str:
    """Move a concept to a new parent within its scheme.

    Can replace an existing parent, add an additional parent (polyhierarchy),
    or move to root level.

    Args:
        concept_id: UUID of the concept to move
        new_parent_id: UUID of the new parent concept (omit to move to root)
        previous_parent_id: UUID of the parent to replace (omit to add as additional parent)
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ConceptService(session, user_id=user_id)
        concept = await svc.move_concept(
            UUID(concept_id),
            UUID(new_parent_id) if new_parent_id else None,
            UUID(previous_parent_id) if previous_parent_id else None,
        )
    return f"Moved: {format_concept(concept)}"


# --- Refining tools ---


@mcp.tool()
async def update_scheme(
    ctx: Context,
    scheme_id: str,
    title: str | None = None,
    description: str | None = None,
    uri: str | None = None,
) -> str:
    """Update a concept scheme's title, description, or URI.

    Only provided fields are updated.

    Args:
        scheme_id: UUID of the concept scheme
        title: New title
        description: New description
        uri: New base URI
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ConceptSchemeService(session, user_id=user_id)
        scheme = await svc.update_scheme(
            UUID(scheme_id),
            ConceptSchemeUpdate(title=title, description=description, uri=uri),
        )
    return f"Updated: {format_scheme(scheme)}"


@mcp.tool()
async def update_concept(
    ctx: Context,
    concept_id: str,
    pref_label: str | None = None,
    definition: str | None = None,
    scope_note: str | None = None,
    alt_labels: list[str] | None = None,
) -> str:
    """Update a concept's label, definition, scope note, or alt labels.

    Only provided fields are updated. Pass an empty list for alt_labels to clear them.

    Args:
        concept_id: UUID of the concept to update
        pref_label: New preferred label
        definition: New definition text
        scope_note: New scope note
        alt_labels: New list of alternative labels (empty list clears)
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ConceptService(session, user_id=user_id)
        concept = await svc.update_concept(
            UUID(concept_id),
            ConceptUpdate(
                pref_label=pref_label,
                definition=definition,
                scope_note=scope_note,
                alt_labels=alt_labels,
            ),
        )
    return f"Updated: {format_concept(concept)}"


@mcp.tool()
async def update_concepts_batch(ctx: Context, updates: list[dict]) -> str:
    """Update multiple concepts in a single operation.

    Each update dict should have:
    - concept_id (required): UUID of the concept
    - pref_label (optional): New preferred label
    - definition (optional): New definition
    - scope_note (optional): New scope note
    - alt_labels (optional): New alt labels list

    Args:
        updates: List of update definitions
    """
    user_id = _get_user_id(ctx)
    updated = []
    async with db_manager.session() as session:
        svc = ConceptService(session, user_id=user_id)
        for u in updates:
            concept = await svc.update_concept(
                UUID(u["concept_id"]),
                ConceptUpdate(
                    pref_label=u.get("pref_label"),
                    definition=u.get("definition"),
                    scope_note=u.get("scope_note"),
                    alt_labels=u.get("alt_labels"),
                ),
            )
            updated.append(concept)

    lines = [f"Updated {len(updated)} concept(s):"]
    for c in updated:
        lines.append(f"  {format_concept_brief(c)}")
    return "\n".join(lines)


@mcp.tool()
async def set_related(
    ctx: Context,
    concept_id: str,
    related_concept_id: str,
    action: str = "add",
) -> str:
    """Add or remove a related (associative) relationship between concepts.

    Related relationships are symmetric — if A is related to B, B is related to A.
    Both concepts must be in the same scheme.

    Args:
        concept_id: UUID of one concept
        related_concept_id: UUID of the other concept
        action: "add" or "remove"
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ConceptService(session, user_id=user_id)
        if action == "add":
            await svc.add_related(UUID(concept_id), UUID(related_concept_id))
        elif action == "remove":
            await svc.remove_related(UUID(concept_id), UUID(related_concept_id))
        else:
            return f"Invalid action '{action}'. Use 'add' or 'remove'."
        concept = await svc.get_concept(UUID(concept_id))
    return format_concept(concept)


# --- Quality & History tools ---


@mcp.tool()
async def check_quality(ctx: Context, scheme_id: str) -> str:
    """Analyse a concept scheme for common quality issues.

    Checks for:
    - Concepts missing definitions
    - Concepts missing scope notes
    - Duplicate preferred labels
    - Alt labels that conflict with other concepts' preferred labels
    - Orphan concepts (no broader, when other top-level concepts exist)

    Also reports statistics: total concepts, top-level count, max depth.

    Args:
        scheme_id: UUID of the concept scheme to analyse
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ConceptService(session, user_id=user_id)
        concepts = await svc.list_concepts_for_scheme(UUID(scheme_id))
        tree = await svc.get_tree(UUID(scheme_id))

    if not concepts:
        return "Scheme has no concepts."

    issues: list[str] = []

    # Missing definitions
    missing_def = [c for c in concepts if not c.definition]
    if missing_def:
        labels = ", ".join(c.pref_label for c in missing_def[:10])
        suffix = f" (and {len(missing_def) - 10} more)" if len(missing_def) > 10 else ""
        issues.append(f"Missing definitions ({len(missing_def)}): {labels}{suffix}")

    # Missing scope notes
    missing_scope = [c for c in concepts if not c.scope_note]
    if missing_scope:
        labels = ", ".join(c.pref_label for c in missing_scope[:10])
        suffix = f" (and {len(missing_scope) - 10} more)" if len(missing_scope) > 10 else ""
        issues.append(f"Missing scope notes ({len(missing_scope)}): {labels}{suffix}")

    # Duplicate pref_labels
    label_counts: dict[str, list[str]] = {}
    for c in concepts:
        label_lower = c.pref_label.lower()
        label_counts.setdefault(label_lower, []).append(c.pref_label)
    dupes = {k: v for k, v in label_counts.items() if len(v) > 1}
    if dupes:
        for label, instances in dupes.items():
            issues.append(f"Duplicate label: '{instances[0]}' appears {len(instances)} times")

    # Alt label / pref label conflicts
    pref_labels_lower = {c.pref_label.lower(): c.pref_label for c in concepts}
    for c in concepts:
        for alt in (c.alt_labels or []):
            if alt.lower() in pref_labels_lower and alt.lower() != c.pref_label.lower():
                issues.append(
                    f"Alt label '{alt}' on '{c.pref_label}' conflicts with "
                    f"pref label '{pref_labels_lower[alt.lower()]}'"
                )

    # Compute depth
    def max_depth(nodes: list[dict], depth: int = 0) -> int:
        if not nodes:
            return depth
        return max(max_depth(n.get("narrower", []), depth + 1) for n in nodes)

    depth = max_depth(tree)
    top_count = len(tree)

    # Build report
    lines = [f"Quality report for scheme ({len(concepts)} concepts):"]
    lines.append(f"  Top-level concepts: {top_count}")
    lines.append(f"  Max depth: {depth}")

    if issues:
        lines.append(f"\nIssues ({len(issues)}):")
        for issue in issues:
            lines.append(f"  - {issue}")
    else:
        lines.append("\nNo issues found.")

    return "\n".join(lines)


@mcp.tool()
async def get_history(ctx: Context, scheme_id: str, limit: int = 20) -> str:
    """Get recent change history for a concept scheme.

    Args:
        scheme_id: UUID of the concept scheme
        limit: Maximum number of events to return (default 20)
    """
    async with db_manager.session() as session:
        svc = HistoryService(session)
        events = await svc.get_scheme_history(UUID(scheme_id), limit=limit)

    if not events:
        return "No history found."

    lines = [f"Recent changes ({len(events)}):"]
    for event in events:
        user_name = event.user.display_name if event.user else "unknown"
        ts = event.timestamp.strftime("%Y-%m-%d %H:%M")
        entity_label = ""
        if event.after_state and "pref_label" in event.after_state:
            entity_label = f" '{event.after_state['pref_label']}'"
        elif event.before_state and "pref_label" in event.before_state:
            entity_label = f" '{event.before_state['pref_label']}'"
        lines.append(f"  [{ts}] {user_name}: {event.action} {event.entity_type}{entity_label}")
    return "\n".join(lines)


# --- Management tools ---


@mcp.tool()
async def delete_scheme(ctx: Context, scheme_id: str) -> str:
    """Delete a concept scheme and all its concepts.

    This cannot be undone. Fails if the scheme is referenced by properties.

    Args:
        scheme_id: UUID of the concept scheme to delete
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ConceptSchemeService(session, user_id=user_id)
        scheme = await svc.get_scheme(UUID(scheme_id))
        title = scheme.title
        await svc.delete_scheme(UUID(scheme_id))
    return f"Deleted scheme '{title}' ({scheme_id})."


@mcp.tool()
async def export_scheme(
    ctx: Context,
    scheme_id: str,
    format: str = "ttl",
) -> str:
    """Export a concept scheme as SKOS RDF.

    Args:
        scheme_id: UUID of the concept scheme
        format: Output format — "ttl" (Turtle), "xml" (RDF/XML), or "jsonld" (JSON-LD)
    """
    async with db_manager.session() as session:
        svc = SKOSExportService(session)
        return await svc.export_scheme(UUID(scheme_id), format)


@mcp.tool()
async def delete_concept(ctx: Context, concept_id: str) -> str:
    """Delete a concept and all its relationships.

    This removes the concept and any broader, narrower, and related relationships.
    This action cannot be undone.

    Args:
        concept_id: UUID of the concept to delete
    """
    user_id = _get_user_id(ctx)
    async with db_manager.session() as session:
        svc = ConceptService(session, user_id=user_id)
        concept = await svc.get_concept(UUID(concept_id))
        label = concept.pref_label
        await svc.delete_concept(UUID(concept_id))
    return f"Deleted concept '{label}' ({concept_id})."
