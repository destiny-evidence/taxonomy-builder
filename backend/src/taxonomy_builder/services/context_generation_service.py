"""JSON-LD @context generation service."""

import logging
from uuid import UUID

from taxonomy_builder.config import settings
from taxonomy_builder.schemas.snapshot import SnapshotVocabulary
from taxonomy_builder.schemas.validators import uri_local_name

logger = logging.getLogger(__name__)


class ContextGenerationService:
    """Service for generating JSON-LD @context documents from vocabulary snapshots.

    The generated context enables consumers to expand compact URIs
    (e.g. ``esea:C00008``) and unprefixed terms (e.g. ``Investigation``)
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

        # 1. @vocab — unprefixed terms resolve to the project namespace
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

        def precedence(term) -> tuple[int, UUID]:
            # Oldest wins within a tier so a later import can't take an existing unprefixed term.
            if term.uri.startswith(project_namespace):
                tier = 0
            elif term.uri.startswith(settings.evrepo_namespace):
                tier = 1
            else:
                tier = 2
            return tier, term.id

        for snapshot_class in sorted(snapshot.classes, key=precedence):
            local_name = uri_local_name(snapshot_class.uri)
            if not local_name:
                continue
            compact = self._compact_uri(snapshot_class.uri, namespace_to_prefix)
            if local_name in used_terms:
                # Not by full URI: a full-URI key whose value is a CURIE sends
                # rdflib's JSON-LD parser into infinite recursion.
                logger.warning(
                    "Context term collision: class %s not given unprefixed term %r",
                    snapshot_class.uri,
                    local_name,
                )
                context[compact] = compact
            else:
                used_terms[local_name] = snapshot_class.uri
                context[local_name] = compact

        # 4. Property term mappings
        for prop in sorted(snapshot.properties, key=precedence):
            local_name = uri_local_name(prop.uri)
            if not local_name:
                continue

            in_project_namespace = prop.uri.startswith(project_namespace)
            entry: dict[str, str] = {}

            # @id — only needed for properties outside the project namespace
            if not in_project_namespace:
                entry["@id"] = self._compact_uri(prop.uri, namespace_to_prefix)

            # @type
            if prop.property_type == "object" or (
                prop.range_scheme_id is not None or prop.range_class is not None
            ):
                entry["@type"] = "@id"
            elif prop.range_datatype:
                entry["@type"] = prop.range_datatype

            # @container
            if prop.cardinality == "multiple":
                entry["@container"] = "@set"

            owns_unprefixed_term = used_terms.setdefault(local_name, prop.uri) == prop.uri

            if not entry:
                # In project namespace with no annotations — resolved via @vocab
                continue

            # Simplify: if only @id, emit as string instead of object
            value = entry["@id"] if set(entry) == {"@id"} else entry
            if owns_unprefixed_term:
                context[local_name] = value
            else:
                logger.warning(
                    "Context term collision: property %s not given unprefixed term %r",
                    prop.uri,
                    local_name,
                )

            # A CURIE key only picks up @type/@container from its own entry.
            compact = entry.get("@id")
            if compact and compact != prop.uri and value is entry:
                context[compact] = entry
            elif not owns_unprefixed_term:
                context[prop.uri] = value

        # 5. Named individual aliases (e.g., CodingStatus values)
        for individual in snapshot.named_individuals:
            local_name = uri_local_name(individual.uri)
            if not local_name or local_name in used_terms:
                continue
            compact = self._compact_uri(individual.uri, namespace_to_prefix)
            used_terms[local_name] = individual.uri
            context[local_name] = compact

        return {"@context": context}

    @staticmethod
    def _compact_uri(uri: str, namespace_to_prefix: dict[str, str]) -> str:
        """Compact a URI using known prefix mappings, or return the full URI."""
        for namespace, prefix in namespace_to_prefix.items():
            if uri.startswith(namespace):
                return f"{prefix}:{uri[len(namespace) :]}"
        return uri
