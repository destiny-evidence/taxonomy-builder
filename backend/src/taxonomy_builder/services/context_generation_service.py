"""JSON-LD @context generation service."""

from taxonomy_builder.schemas.snapshot import SnapshotVocabulary


class ContextGenerationService:
    """Service for generating JSON-LD @context documents from vocabulary snapshots.

    The generated context enables consumers to expand compact URIs
    (e.g. ``esea:C00008``) and bare type terms (e.g. ``Investigation``)
    back to their full URIs.
    """

    def generate(self, snapshot: SnapshotVocabulary) -> dict:
        """Build a JSON-LD @context from a vocabulary snapshot."""
        project_ns = snapshot.project.namespace.rstrip("/") + "/"
        prefixes = dict(snapshot.project.namespace_prefixes)

        # Build reverse lookup: namespace URL → prefix name (longest NS first
        # so that more-specific namespaces match before shorter ones).
        ns_to_prefix: dict[str, str] = dict(
            sorted(
                ((ns, pfx) for pfx, ns in prefixes.items()),
                key=lambda item: len(item[0]),
                reverse=True,
            )
        )

        ctx: dict[str, object] = {}

        # 1. @vocab — bare terms resolve to the project namespace
        ctx["@vocab"] = project_ns

        # 2. Namespace prefix mappings (skip empty-string keys — invalid in JSON-LD)
        for prefix, ns in sorted(prefixes.items()):
            if prefix:
                ctx[prefix] = ns

        # 3. Class term mappings
        used_terms: dict[str, str] = {}  # local_name → full URI (for collision detection)

        for cls in snapshot.classes:
            local_name = self._local_name(cls.uri)
            if not local_name:
                continue
            if cls.uri.startswith(project_ns):
                # Resolved via @vocab — no explicit entry needed,
                # but reserve the local name for collision detection.
                used_terms.setdefault(local_name, cls.uri)
                continue
            compact = self._compact_uri(cls.uri, ns_to_prefix)
            if local_name in used_terms:
                # Collision — use full URI as key
                ctx[cls.uri] = compact
            else:
                used_terms[local_name] = cls.uri
                ctx[local_name] = compact

        # 4. Property term mappings
        for prop in snapshot.properties:
            local_name = self._local_name(prop.uri)
            if not local_name:
                continue

            in_project_ns = prop.uri.startswith(project_ns)
            entry: dict[str, str] = {}

            # @id — only needed for properties outside the project namespace
            if not in_project_ns:
                entry["@id"] = self._compact_uri(prop.uri, ns_to_prefix)

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
                term_key = prop.uri  # collision
            else:
                used_terms[local_name] = prop.uri
                term_key = local_name

            # Simplify: if only @id, emit as string instead of object
            if set(entry.keys()) == {"@id"}:
                ctx[term_key] = entry["@id"]
            else:
                ctx[term_key] = entry

        return {"@context": ctx}

    @staticmethod
    def _local_name(uri: str) -> str:
        """Extract the local name from a URI (part after last ``/`` or ``#``)."""
        for sep in ("#", "/"):
            idx = uri.rfind(sep)
            if idx >= 0:
                return uri[idx + 1:]
        return uri

    @staticmethod
    def _compact_uri(uri: str, ns_to_prefix: dict[str, str]) -> str:
        """Compact a URI using known prefix mappings, or return the full URI."""
        for ns, prefix in ns_to_prefix.items():
            if uri.startswith(ns):
                return f"{prefix}:{uri[len(ns):]}"
        return uri
