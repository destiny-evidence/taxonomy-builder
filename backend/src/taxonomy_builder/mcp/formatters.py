"""Format models as LLM-friendly text output."""

def _safe_get(obj, attr_name):
    """Get a relationship attribute only if it's already loaded (avoids lazy load).

    For SQLAlchemy models, checks instance state to avoid triggering lazy loads.
    For plain objects, falls back to getattr.
    """
    try:
        from sqlalchemy.orm import attributes

        state = attributes.instance_state(obj)
        return state.dict.get(attr_name)
    except Exception:
        return getattr(obj, attr_name, None)


def format_project(project) -> str:
    lines = [
        f"{project.name} (id: {project.id})",
        f"  Namespace: {project.namespace}",
        f"  Prefix: {project.identifier_prefix}",
    ]
    if project.description:
        lines.append(f"  Description: {project.description}")
    if project.schemes:
        lines.append(f"  Schemes: {len(project.schemes)}")
    return "\n".join(lines)


def format_scheme(scheme) -> str:
    lines = [
        f"{scheme.title} (id: {scheme.id})",
        f"  Project: {scheme.project_id}",
    ]
    if scheme.description:
        lines.append(f"  Description: {scheme.description}")
    if scheme.uri:
        lines.append(f"  URI: {scheme.uri}")
    concept_count = len(scheme.concepts) if scheme.concepts else 0
    lines.append(f"  {concept_count} concepts")
    return "\n".join(lines)


def format_concept(concept) -> str:
    lines = [
        f"{concept.pref_label} (id: {concept.id})",
        f"  Identifier: {concept.identifier}",
        f"  URI: {concept.uri}",
    ]
    scheme = _safe_get(concept, "scheme")
    scheme_title = getattr(scheme, "title", None) if scheme else None
    if scheme_title:
        lines.append(f"  Scheme: {scheme_title} (id: {scheme.id})")
    if concept.definition:
        lines.append(f"  Definition: {concept.definition}")
    if concept.scope_note:
        lines.append(f"  Scope Note: {concept.scope_note}")
    if concept.alt_labels:
        lines.append(f"  Alt Labels: {', '.join(concept.alt_labels)}")
    broader = _safe_get(concept, "broader")
    if broader:
        labels = [f"{c.pref_label} (id: {c.id})" for c in broader]
        lines.append(f"  Broader: {', '.join(labels)}")
    narrower = _safe_get(concept, "narrower")
    if narrower:
        labels = [f"{c.pref_label} (id: {c.id})" for c in narrower]
        lines.append(f"  Narrower: {', '.join(labels)}")
    if concept.related:
        labels = [f"{c.pref_label} (id: {c.id})" for c in concept.related]
        lines.append(f"  Related: {', '.join(labels)}")
    return "\n".join(lines)


def format_concept_brief(concept) -> str:
    parts = [f"{concept.pref_label} (id: {concept.id})"]
    if concept.definition:
        # Truncate long definitions
        defn = concept.definition
        if len(defn) > 80:
            defn = defn[:77] + "..."
        parts.append(f" — {defn}")
    return "".join(parts)


def format_feedback(feedback) -> str:
    lines = [
        f"[{feedback.status}] \"{feedback.feedback_type}\" on"
        f" {feedback.entity_type} '{feedback.entity_label}' (id: {feedback.id})",
        f"  By: {feedback.author_name} ({feedback.created_at})",
        f"  Content: {feedback.content}",
    ]
    if feedback.response_content:
        lines.append(f"  Response: {feedback.response_content}")
    else:
        lines.append("  Response: (none)")
    return "\n".join(lines)


def format_feedback_brief(feedback) -> str:
    return (
        f"[{feedback.status}] {feedback.entity_type} '{feedback.entity_label}'"
        f" — {feedback.feedback_type} (id: {feedback.id})"
    )


def format_tree(tree_nodes: list[dict], indent: int = 0) -> str:
    if not tree_nodes and indent == 0:
        return "(empty scheme)"
    lines = []
    for node in tree_nodes:
        prefix = "  " * indent
        lines.append(f"{prefix}{node['pref_label']} (id: {node['id']})")
        if node.get("narrower"):
            lines.append(format_tree(node["narrower"], indent + 1))
    return "\n".join(lines)
