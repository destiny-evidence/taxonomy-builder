"""MCP tools for taxonomy builder."""

from uuid import UUID

from fastmcp.dependencies import Depends
from fastmcp.tools import ToolResult
from mcp.types import TextContent

from taxonomy_builder.config import settings
from taxonomy_builder.mcp.dependencies import (
    get_concept_service,
    get_export_service,
    get_feedback_service,
    get_history_service,
    get_project_service,
    get_scheme_service,
)
from taxonomy_builder.mcp.formatters import (
    format_concept,
    format_concept_brief,
    format_feedback,
    format_feedback_brief,
    format_project,
    format_scheme,
    format_tree,
)
from taxonomy_builder.mcp.server import mcp, require_manager
from taxonomy_builder.schemas.concept import ConceptCreate, ConceptUpdate
from taxonomy_builder.schemas.concept_scheme import (
    ConceptSchemeCreate,
    ConceptSchemeUpdate,
)
from taxonomy_builder.schemas.project import ProjectCreate
from taxonomy_builder.services.concept_scheme_service import ConceptSchemeService
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.feedback_service import (
    FeedbackNotFoundError,
    FeedbackService,
)
from taxonomy_builder.services.history_service import HistoryService
from taxonomy_builder.services.project_service import ProjectService
from taxonomy_builder.services.skos_export_service import SKOSExportService

# When auth is enabled, apply the manager role check to all tools.
_auth = require_manager if settings.mcp_auth else None


# --- Exploring tools ---


@mcp.tool(auth=_auth)
async def list_projects(
    svc: ProjectService = Depends(get_project_service),
) -> str:
    """List all taxonomy projects.

    Returns a list of all projects with their names, namespaces, and IDs.
    Use the project ID to explore its concept schemes.
    """
    projects = await svc.list_projects()
    if not projects:
        return "No projects found."
    return "\n\n".join(format_project(p) for p in projects)


@mcp.tool(auth=_auth)
async def create_project(
    name: str,
    namespace: str,
    identifier_prefix: str,
    description: str | None = None,
    svc: ProjectService = Depends(get_project_service),
) -> str:
    """Create a new taxonomy project.

    Args:
        name: Project name (must be unique)
        namespace: Base URI namespace for the project (e.g. "https://example.org/vocab/")
        identifier_prefix: 1-4 uppercase letters used to prefix concept identifiers (e.g. "EVD")
        description: Optional project description
    """
    project = await svc.create_project(
        ProjectCreate(
            name=name,
            namespace=namespace,
            identifier_prefix=identifier_prefix,
            description=description,
        )
    )
    return f"Created project: {format_project(project)}"


@mcp.tool(auth=_auth)
async def list_schemes(
    project_id: str,
    svc: ConceptSchemeService = Depends(get_scheme_service),
) -> str:
    """List all concept schemes in a project.

    Args:
        project_id: UUID of the project
    """
    schemes = await svc.list_schemes_for_project(UUID(project_id))
    if not schemes:
        return "No schemes found in this project."
    return "\n\n".join(format_scheme(s) for s in schemes)


@mcp.tool(auth=_auth)
async def get_scheme(
    scheme_id: str,
    svc: ConceptSchemeService = Depends(get_scheme_service),
) -> str:
    """Get details about a concept scheme including concept count.

    Args:
        scheme_id: UUID of the concept scheme
    """
    scheme = await svc.get_scheme(UUID(scheme_id))
    return format_scheme(scheme)


@mcp.tool(auth=_auth)
async def get_concept_tree(
    scheme_id: str,
    svc: ConceptService = Depends(get_concept_service),
) -> str:
    """Get the full concept hierarchy for a scheme as an indented tree.

    Shows all concepts organised by their broader/narrower relationships.
    Top-level concepts (no broader) appear at root. Children are indented.
    Use this to understand the overall structure before making changes.

    Args:
        scheme_id: UUID of the concept scheme
    """
    tree = await svc.get_tree(UUID(scheme_id))
    return format_tree(tree)


@mcp.tool(auth=_auth)
async def search_concepts(
    query: str,
    scheme_id: str | None = None,
    project_id: str | None = None,
    svc: ConceptService = Depends(get_concept_service),
) -> str:
    """Search for concepts by label, definition, or alternative labels.

    Searches pref_label, definition, and alt_labels fields using
    case-insensitive substring matching. Provide scheme_id to search
    within one scheme, or project_id to search across all schemes in a
    project. At least one must be given.

    Args:
        query: Search text to match against labels and definitions
        scheme_id: UUID of a concept scheme to search within
        project_id: UUID of a project to search across all its schemes
    """
    if not scheme_id and not project_id:
        return "Provide either scheme_id or project_id."
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


@mcp.tool(auth=_auth)
async def get_concept(
    concept_id: str,
    svc: ConceptService = Depends(get_concept_service),
) -> str:
    """Get full details of a concept including relationships.

    Returns the concept's label, definition, scope note, alt labels,
    and its broader, narrower, and related concepts.

    Args:
        concept_id: UUID of the concept
    """
    concept = await svc.get_concept(UUID(concept_id))
    return format_concept(concept)


# --- Building tools ---


@mcp.tool(auth=_auth)
async def create_scheme(
    project_id: str,
    title: str,
    description: str | None = None,
    uri: str | None = None,
    svc: ConceptSchemeService = Depends(get_scheme_service),
) -> str:
    """Create a new concept scheme in a project.

    Args:
        project_id: UUID of the project
        title: Title for the new scheme
        description: Optional description
        uri: Optional base URI for concepts in this scheme
    """
    scheme = await svc.create_scheme(
        UUID(project_id),
        ConceptSchemeCreate(title=title, description=description, uri=uri),
    )
    return f"Created scheme: {format_scheme(scheme)}"


@mcp.tool(auth=_auth)
async def create_concept(
    scheme_id: str,
    pref_label: str,
    definition: str | None = None,
    scope_note: str | None = None,
    alt_labels: list[str] | None = None,
    broader_concept_id: str | None = None,
    concept_svc: ConceptService = Depends(get_concept_service),
    project_svc: ProjectService = Depends(get_project_service),
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
    scheme = await concept_svc.get_scheme(UUID(scheme_id))
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


@mcp.tool(auth=_auth)
async def create_concepts_batch(
    scheme_id: str,
    concepts: list[dict],
    concept_svc: ConceptService = Depends(get_concept_service),
    project_svc: ProjectService = Depends(get_project_service),
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
    for i, c in enumerate(concepts):
        if "pref_label" not in c:
            return f"Invalid batch entry [{i}]: missing required field 'pref_label'."
        broader_ref = c.get("broader_concept_id")
        if broader_ref:
            if isinstance(broader_ref, str) and broader_ref.startswith("#"):
                try:
                    idx = int(broader_ref[1:])
                except ValueError:
                    return (
                        f"Invalid broader_concept_id {broader_ref!r} at [{i}]:"
                        " batch references must be of the form '#N' where N is an integer."
                    )
                if idx < 0 or idx >= i:
                    return (
                        f"Invalid broader_concept_id {broader_ref!r} at [{i}]:"
                        f" index out of range (must reference an earlier entry, 0..{i - 1})."
                    )
            else:
                try:
                    UUID(broader_ref)
                except ValueError:
                    return (
                        f"Invalid broader_concept_id {broader_ref!r} at [{i}]:"
                        " not a valid UUID or '#N' batch reference."
                    )

    created = []
    scheme = await concept_svc.get_scheme(UUID(scheme_id))

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
            if isinstance(broader_ref, str) and broader_ref.startswith("#"):
                broader_id = created[int(broader_ref[1:])].id
            else:
                broader_id = UUID(broader_ref)
            await concept_svc.add_broader(concept.id, broader_id)
            concept = await concept_svc.get_concept(concept.id)

        created.append(concept)

    lines = [f"Created {len(created)} concept(s):"]
    for c in created:
        lines.append(f"  {format_concept_brief(c)}")
    return "\n".join(lines)


@mcp.tool(auth=_auth)
async def add_broader(
    concept_id: str,
    broader_concept_id: str,
    svc: ConceptService = Depends(get_concept_service),
) -> str:
    """Add a broader (parent) relationship between two concepts.

    Both concepts must already exist in the same scheme. Polyhierarchy is
    supported — a concept can have multiple broader concepts.

    Args:
        concept_id: UUID of the narrower (child) concept
        broader_concept_id: UUID of the broader (parent) concept
    """
    await svc.add_broader(UUID(concept_id), UUID(broader_concept_id))
    concept = await svc.get_concept(UUID(concept_id))
    return f"Added broader relationship: {format_concept(concept)}"


@mcp.tool(auth=_auth)
async def remove_broader(
    concept_id: str,
    broader_concept_id: str,
    svc: ConceptService = Depends(get_concept_service),
) -> str:
    """Remove a broader (parent) relationship between two concepts.

    Args:
        concept_id: UUID of the narrower (child) concept
        broader_concept_id: UUID of the broader (parent) concept whose link should be removed
    """
    await svc.remove_broader(UUID(concept_id), UUID(broader_concept_id))
    concept = await svc.get_concept(UUID(concept_id))
    return f"Removed broader relationship: {format_concept(concept)}"


@mcp.tool(auth=_auth)
async def move_concept(
    concept_id: str,
    new_parent_id: str | None = None,
    previous_parent_id: str | None = None,
    svc: ConceptService = Depends(get_concept_service),
) -> str:
    """Move a concept to a new parent within its scheme.

    Can replace an existing parent, add an additional parent (polyhierarchy),
    or move to root level.

    Args:
        concept_id: UUID of the concept to move
        new_parent_id: UUID of the new parent concept (omit to move to root)
        previous_parent_id: UUID of the parent to replace (omit to add as additional parent)
    """
    concept = await svc.move_concept(
        UUID(concept_id),
        UUID(new_parent_id) if new_parent_id else None,
        UUID(previous_parent_id) if previous_parent_id else None,
    )
    return f"Moved: {format_concept(concept)}"


# --- Refining tools ---


@mcp.tool(auth=_auth)
async def update_scheme(
    scheme_id: str,
    title: str | None = None,
    description: str | None = None,
    uri: str | None = None,
    svc: ConceptSchemeService = Depends(get_scheme_service),
) -> str:
    """Update a concept scheme's title, description, or URI.

    Only provided fields are updated.

    Args:
        scheme_id: UUID of the concept scheme
        title: New title
        description: New description
        uri: New base URI
    """
    scheme = await svc.update_scheme(
        UUID(scheme_id),
        ConceptSchemeUpdate(title=title, description=description, uri=uri),
    )
    return f"Updated: {format_scheme(scheme)}"


@mcp.tool(auth=_auth)
async def update_concept(
    concept_id: str,
    pref_label: str | None = None,
    definition: str | None = None,
    scope_note: str | None = None,
    alt_labels: list[str] | None = None,
    svc: ConceptService = Depends(get_concept_service),
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


@mcp.tool(auth=_auth)
async def update_concepts_batch(
    updates: list[dict],
    svc: ConceptService = Depends(get_concept_service),
) -> str:
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
    for i, u in enumerate(updates):
        if "concept_id" not in u:
            return f"Invalid update entry [{i}]: missing required field 'concept_id'."
        try:
            UUID(u["concept_id"])
        except ValueError:
            return (
                f"Invalid concept_id {u['concept_id']!r} at [{i}]: not a valid UUID."
            )

    updated = []
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


@mcp.tool(auth=_auth)
async def add_related(
    concept_id: str,
    related_concept_id: str,
    svc: ConceptService = Depends(get_concept_service),
) -> str:
    """Add a related (associative) relationship between two concepts.

    Related relationships are symmetric — if A is related to B, B is related to A.
    Both concepts must be in the same scheme.

    Args:
        concept_id: UUID of one concept
        related_concept_id: UUID of the other concept
    """
    await svc.add_related(UUID(concept_id), UUID(related_concept_id))
    concept = await svc.get_concept(UUID(concept_id))
    return f"Added related relationship: {format_concept(concept)}"


@mcp.tool(auth=_auth)
async def remove_related(
    concept_id: str,
    related_concept_id: str,
    svc: ConceptService = Depends(get_concept_service),
) -> str:
    """Remove a related (associative) relationship between two concepts.

    Args:
        concept_id: UUID of one concept
        related_concept_id: UUID of the other concept
    """
    await svc.remove_related(UUID(concept_id), UUID(related_concept_id))
    concept = await svc.get_concept(UUID(concept_id))
    return f"Removed related relationship: {format_concept(concept)}"


# --- Quality & History tools ---


@mcp.tool(auth=_auth)
async def check_quality(
    scheme_id: str,
    svc: ConceptService = Depends(get_concept_service),
) -> str:
    """Analyse a concept scheme for common quality issues.

    Checks for:
    - Concepts missing definitions
    - Concepts missing scope notes
    - Duplicate preferred labels
    - Alt labels that conflict with other concepts' preferred labels

    Also reports statistics: total concepts, top-level count, max depth.

    Args:
        scheme_id: UUID of the concept scheme to analyse
    """
    concepts = await svc.list_concepts_for_scheme(UUID(scheme_id))
    tree = await svc.get_tree(UUID(scheme_id))

    if not concepts:
        return "Scheme has no concepts."

    issues: list[str] = []

    missing_def = [c for c in concepts if not c.definition]
    if missing_def:
        labels = ", ".join(c.pref_label for c in missing_def[:10])
        suffix = f" (and {len(missing_def) - 10} more)" if len(missing_def) > 10 else ""
        issues.append(f"Missing definitions ({len(missing_def)}): {labels}{suffix}")

    missing_scope = [c for c in concepts if not c.scope_note]
    if missing_scope:
        labels = ", ".join(c.pref_label for c in missing_scope[:10])
        suffix = (
            f" (and {len(missing_scope) - 10} more)" if len(missing_scope) > 10 else ""
        )
        issues.append(f"Missing scope notes ({len(missing_scope)}): {labels}{suffix}")

    label_counts: dict[str, list[str]] = {}
    for c in concepts:
        label_lower = c.pref_label.lower()
        label_counts.setdefault(label_lower, []).append(c.pref_label)
    dupes = {k: v for k, v in label_counts.items() if len(v) > 1}
    if dupes:
        for label, instances in dupes.items():
            issues.append(
                f"Duplicate label: '{instances[0]}' appears {len(instances)} times"
            )

    pref_labels_lower = {c.pref_label.lower(): c.pref_label for c in concepts}
    for c in concepts:
        for alt in c.alt_labels or []:
            if alt.lower() in pref_labels_lower and alt.lower() != c.pref_label.lower():
                issues.append(
                    f"Alt label '{alt}' on '{c.pref_label}' conflicts with "
                    f"pref label '{pref_labels_lower[alt.lower()]}'"
                )

    def max_depth(nodes: list[dict], depth: int = 0) -> int:
        if not nodes:
            return depth
        return max(max_depth(n.get("narrower", []), depth + 1) for n in nodes)

    depth = max_depth(tree)
    top_count = len(tree)

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


@mcp.tool(auth=_auth)
async def get_history(
    scheme_id: str,
    limit: int = 20,
    svc: HistoryService = Depends(get_history_service),
) -> str:
    """Get recent change history for a concept scheme.

    Args:
        scheme_id: UUID of the concept scheme
        limit: Maximum number of events to return (default 20)
    """
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
        lines.append(
            f"  [{ts}] {user_name}: {event.action} {event.entity_type}{entity_label}"
        )
    return "\n".join(lines)


# --- Management tools ---


@mcp.tool(auth=_auth)
async def delete_scheme(
    scheme_id: str,
    confirm_title: str,
    svc: ConceptSchemeService = Depends(get_scheme_service),
) -> str:
    """Delete a concept scheme and all its concepts.

    This cannot be undone. Fails if the scheme is referenced by properties.
    To prevent accidental deletion of the wrong scheme, you must pass the
    exact current title of the scheme as confirm_title; the deletion is
    aborted if it does not match.

    Args:
        scheme_id: UUID of the concept scheme to delete
        confirm_title: Must exactly match the scheme's current title
    """
    scheme = await svc.get_scheme(UUID(scheme_id))
    if scheme.title != confirm_title:
        return (
            f"Aborted: scheme {scheme_id} is titled '{scheme.title}', "
            f"not '{confirm_title}'. No deletion performed."
        )
    title = scheme.title
    project_id = scheme.project_id
    await svc.delete_scheme(UUID(scheme_id))
    return f"Deleted scheme '{title}' ({scheme_id}) from project {project_id}."


@mcp.tool(auth=_auth)
async def export_scheme(
    scheme_id: str,
    format: str = "ttl",
    svc: SKOSExportService = Depends(get_export_service),
) -> str:
    """Export a concept scheme as SKOS RDF.

    Args:
        scheme_id: UUID of the concept scheme
        format: Output format — "ttl" (Turtle), "xml" (RDF/XML), or "jsonld" (JSON-LD)
    """
    return await svc.export_scheme(UUID(scheme_id), format)


@mcp.tool(auth=_auth)
async def delete_concept(
    concept_id: str,
    confirm_label: str,
    svc: ConceptService = Depends(get_concept_service),
) -> str:
    """Delete a concept and all its relationships.

    This removes the concept and any broader, narrower, and related relationships.
    This action cannot be undone. To prevent accidental deletion of the wrong
    concept, you must pass the exact current pref_label of the concept as
    confirm_label; the deletion is aborted if it does not match.

    Args:
        concept_id: UUID of the concept to delete
        confirm_label: Must exactly match the concept's current pref_label
    """
    concept = await svc.get_concept(UUID(concept_id))
    if concept.pref_label != confirm_label:
        return (
            f"Aborted: concept {concept_id} is labelled '{concept.pref_label}', "
            f"not '{confirm_label}'. No deletion performed."
        )
    label = concept.pref_label
    scheme_title = concept.scheme.title
    await svc.delete_concept(UUID(concept_id))
    return f"Deleted concept '{label}' ({concept_id}) from scheme '{scheme_title}'."


# --- Feedback tools ---


@mcp.tool(auth=_auth)
async def get_feedback_counts(
    project_svc: ProjectService = Depends(get_project_service),
    feedback_svc: FeedbackService = Depends(get_feedback_service),
) -> str:
    """Get open feedback counts for all projects.

    Shows how many unresolved feedback items exist per project,
    useful for prioritising triage work.
    """
    projects = await project_svc.list_projects()
    if not projects:
        return "No projects found."
    counts = await feedback_svc.get_open_counts([p.id for p in projects])

    lines = ["Open feedback counts:"]
    for p in projects:
        count = counts.get(p.id, 0)
        if count > 0:
            lines.append(f"  {p.name}: {count}")
    if len(lines) == 1:
        return "No open feedback across any project."
    return "\n".join(lines)


@mcp.tool(auth=_auth)
async def get_feedback(
    feedback_id: str,
    svc: FeedbackService = Depends(get_feedback_service),
) -> str:
    """Get full details of a single feedback item.

    Args:
        feedback_id: UUID of the feedback item
    """
    try:
        fb = await svc.get(UUID(feedback_id))
    except FeedbackNotFoundError:
        return f"Feedback '{feedback_id}' not found."
    return format_feedback(fb)


@mcp.tool(auth=_auth)
async def list_feedback(
    project_id: str,
    status: str | None = None,
    entity_type: str | None = None,
    feedback_type: str | None = None,
    query: str | None = None,
    svc: FeedbackService = Depends(get_feedback_service),
) -> ToolResult:
    """List feedback for a project with optional filters.

    Args:
        project_id: UUID of the project
        status: Filter by status — "open", "responded", "resolved", or "declined"
        entity_type: Filter by entity type — "concept", "scheme", "ontology_class", or "property"
        feedback_type: Filter by feedback type (e.g. "unclear_definition", "missing_term")
        query: Search text across feedback content, entity labels, and author names
    """
    items = await svc.list_all(
        UUID(project_id),
        status=status,
        entity_type=entity_type,
        feedback_type=feedback_type,
        q=query,
    )
    if not items:
        return ToolResult(
            content=[TextContent(type="text", text="No feedback found.")],
            structured_content={"feedback": []},
        )
    lines = [f"Feedback ({len(items)} item(s)):"]
    for fb in items:
        lines.append(f"  {format_feedback_brief(fb)}")
    return ToolResult(
        content=[TextContent(type="text", text="\n".join(lines))],
        structured_content={"feedback": [fb.to_manager_dict() for fb in items]},
    )


@mcp.tool(auth=_auth)
async def respond_to_feedback(
    feedback_id: str,
    content: str,
    svc: FeedbackService = Depends(get_feedback_service),
) -> str:
    """Add or update a response to feedback.

    Only works on feedback with status "open" or "responded".

    Args:
        feedback_id: UUID of the feedback item
        content: Response text (1-10000 characters)
    """
    fb = await svc.respond(UUID(feedback_id), content)
    return f"Responded: {format_feedback(fb)}"


@mcp.tool(auth=_auth)
async def resolve_feedback(
    feedback_id: str,
    content: str | None = None,
    svc: FeedbackService = Depends(get_feedback_service),
) -> str:
    """Resolve feedback (mark as addressed).

    Args:
        feedback_id: UUID of the feedback item
        content: Optional response message
    """
    fb = await svc.resolve(UUID(feedback_id), content)
    return f"Resolved: {format_feedback(fb)}"


@mcp.tool(auth=_auth)
async def decline_feedback(
    feedback_id: str,
    content: str | None = None,
    svc: FeedbackService = Depends(get_feedback_service),
) -> str:
    """Decline feedback (mark as not actionable).

    Args:
        feedback_id: UUID of the feedback item
        content: Optional response message explaining why
    """
    fb = await svc.decline(UUID(feedback_id), content)
    return f"Declined: {format_feedback(fb)}"
