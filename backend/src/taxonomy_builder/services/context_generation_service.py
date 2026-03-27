"""JSON-LD @context generation service."""

import logging

from taxonomy_builder.schemas.snapshot import SnapshotVocabulary

logger = logging.getLogger(__name__)


class ContextGenerationService:
    """Service for generating JSON-LD @context documents from vocabulary snapshots.

    The generated context enables consumers to expand compact URIs
    (e.g. ``esea:C00008``) and bare type terms (e.g. ``Investigation``)
    back to their full URIs.
    """

    def generate(self, snapshot: SnapshotVocabulary) -> dict:
        """Build a JSON-LD @context from a vocabulary snapshot."""
        project_namespace = snapshot.project.namespace.rstrip("/") + "/"
        prefixes = dict(snapshot.project.namespace_prefixes)

        # Build reverse lookup: namespace URL → prefix name (longest namespace
        # first so that more-specific namespaces match before shorter ones).
        namespace_to_prefix: dict[str, str] = dict(
            sorted(
                ((namespace, prefix) for prefix, namespace in prefixes.items()),
                key=lambda item: len(item[0]),
                reverse=True,
            )
        )

        context: dict[str, object] = {}

        # 1. @vocab — bare terms resolve to the project namespace
        context["@vocab"] = project_namespace

        # 2. Namespace prefix mappings
        # Skip empty-string keys: Turtle allows `@prefix : <ns>` which
        # produces an empty prefix after import — invalid as a JSON-LD term.
        for prefix, namespace in sorted(prefixes.items()):
            if prefix:
                context[prefix] = namespace

        # 3. Class term mappings
        # Reserve prefix names so class/property local names can't overwrite them.
        used_terms: dict[str, str] = {prefix: prefix for prefix in prefixes}

        for snapshot_class in snapshot.classes:
            local_name = self._local_name(snapshot_class.uri)
            if not local_name:
                continue
            if snapshot_class.uri.startswith(project_namespace):
                # Resolved via @vocab — no explicit entry needed,
                # but reserve the local name for collision detection.
                used_terms.setdefault(local_name, snapshot_class.uri)
                continue
            compact = self._compact_uri(snapshot_class.uri, namespace_to_prefix)
            if local_name in used_terms:
                # Collision with existing term or prefix — use full URI as key
                logger.warning(
                    "Context term collision: class %s mapped to full URI "
                    "(local name %r already used)",
                    snapshot_class.uri, local_name,
                )
                context[snapshot_class.uri] = compact
            else:
                used_terms[local_name] = snapshot_class.uri
                context[local_name] = compact

        # 4. Property term mappings
        for prop in snapshot.properties:
            local_name = self._local_name(prop.uri)
            if not local_name:
                continue

            in_project_namespace = prop.uri.startswith(project_namespace)
            entry: dict[str, str] = {}

            # @id — only needed for properties outside the project namespace
            if not in_project_namespace:
                entry["@id"] = self._compact_uri(prop.uri, namespace_to_prefix)

            # @type
            if prop.property_type == "object" or (
                prop.range_scheme_id is not None
                or prop.range_class is not None
            ):
                entry["@type"] = "@id"
            elif prop.property_type == "datatype" and prop.range_datatype:
                entry["@type"] = prop.range_datatype

            # @container
            if prop.cardinality == "multiple":
                entry["@container"] = "@set"

            if not entry:
                # In project namespace with no annotations — resolved via @vocab
                continue

            # Determine the term key
            if local_name in used_terms and used_terms[local_name] != prop.uri:
                logger.warning(
                    "Context term collision: property %s mapped to full URI "
                    "(local name %r already used)",
                    prop.uri, local_name,
                )
                term_key = prop.uri  # collision
            else:
                used_terms[local_name] = prop.uri
                term_key = local_name

            # Simplify: if only @id, emit as string instead of object
            if set(entry.keys()) == {"@id"}:
                context[term_key] = entry["@id"]
            else:
                context[term_key] = entry

        return {"@context": context}

    @staticmethod
    def _local_name(uri: str) -> str:
        """Extract the local name from a URI (part after last ``/`` or ``#``)."""
        for sep in ("#", "/"):
            idx = uri.rfind(sep)
            if idx >= 0:
                return uri[idx + 1:]
        return uri

    @staticmethod
    def _compact_uri(uri: str, namespace_to_prefix: dict[str, str]) -> str:
        """Compact a URI using known prefix mappings, or return the full URI."""
        for namespace, prefix in namespace_to_prefix.items():
            if uri.startswith(namespace):
                return f"{prefix}:{uri[len(namespace):]}"
        return uri
