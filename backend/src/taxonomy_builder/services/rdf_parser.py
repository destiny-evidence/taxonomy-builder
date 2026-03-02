"""Pure RDF parsing and analysis — no database access."""

from dataclasses import dataclass, field
from typing import Literal as LiteralType

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, XSD

# XSD namespace prefix for abbreviating datatype URIs
XSD_NS = str(XSD)

# File extension to RDFLib format mapping
FORMAT_MAP = {
    ".ttl": "turtle",
    ".turtle": "turtle",
    ".rdf": "xml",
    ".xml": "xml",
    ".owl": "xml",
    ".jsonld": "json-ld",
    ".json": "json-ld",
    ".nt": "nt",
    ".n3": "n3",
}


class InvalidRDFError(Exception):
    """RDF file could not be parsed."""

    def __init__(self, message: str = "Could not parse RDF file") -> None:
        super().__init__(message)


def detect_format(filename: str) -> str:
    """Detect RDF format from filename extension."""
    filename_lower = filename.lower()
    for ext, fmt in FORMAT_MAP.items():
        if filename_lower.endswith(ext):
            return fmt
    raise InvalidRDFError(
        f"Unsupported file format. Supported formats: {', '.join(FORMAT_MAP.keys())}"
    )


def parse_rdf(content: bytes, fmt: str) -> Graph:
    """Parse RDF content into a graph."""
    g = Graph()
    try:
        g.parse(data=content, format=fmt)
    except Exception as e:
        raise InvalidRDFError(f"Failed to parse RDF: {e}") from e
    return g


# --- Validation ---


@dataclass
class ValidationIssue:
    severity: LiteralType["error", "warning", "info"]
    type: str
    message: str
    entity_uri: str | None = None


@dataclass
class ValidationResult:
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    info: list[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


def validate_graph(g: Graph, class_uris: set[str]) -> ValidationResult:
    """Run validation checks on a parsed RDF graph before import.

    Args:
        g: The parsed RDF graph.
        class_uris: URIs of known classes (existing project classes + classes in the file).

    Returns:
        ValidationResult with categorised issues.
    """
    result = ValidationResult()

    if len(g) == 0:
        result.warnings.append(ValidationIssue(
            severity="warning",
            type="empty_graph",
            message=(
                "File parsed successfully but contains no RDF data — "
                "check the file format matches the file extension"
            ),
        ))
        return result

    _check_file_uris(g, result)
    _check_unresolved_domains(g, class_uris, result)
    _check_rdf_properties(g, result)
    _check_unsupported_subclasses(g, result)
    _check_unsupported_union_domains(g, result)
    _check_unsupported_named_individuals(g, result)
    _check_unsupported_restrictions(g, result)

    return result


def _check_file_uris(g: Graph, result: ValidationResult) -> None:
    """Detect file:// URIs in subjects and objects."""
    seen: set[str] = set()
    for s, _p, o in g:
        for node in (s, o):
            if isinstance(node, URIRef):
                uri_str = str(node)
                if uri_str.startswith("file://") and uri_str not in seen:
                    seen.add(uri_str)
                    result.errors.append(ValidationIssue(
                        severity="error",
                        type="file_uri",
                        message=(
                            f"file:// URI detected: {uri_str} — "
                            f"this usually means the file is missing an @base directive"
                        ),
                        entity_uri=uri_str,
                    ))


def _check_unresolved_domains(
    g: Graph, class_uris: set[str], result: ValidationResult
) -> None:
    """Warn when properties reference domain classes not in the known set."""
    # Collect classes defined in this graph
    file_class_uris = {str(uri) for uri in find_owl_classes(g)}
    all_class_uris = class_uris | file_class_uris

    for uri, _ptype in find_properties(g):
        domain = g.value(uri, RDFS.domain)
        if not isinstance(domain, URIRef):
            continue
        domain_str = str(domain)
        if domain_str not in all_class_uris:
            result.warnings.append(ValidationIssue(
                severity="warning",
                type="unresolved_domain",
                message=(
                    f"Property '{get_identifier_from_uri(uri)}' has domain "
                    f"'{domain_str}' which doesn't match any class in the project"
                ),
                entity_uri=str(uri),
            ))


def _check_rdf_properties(g: Graph, result: ValidationResult) -> None:
    """Detect rdf:Property instances for informational reporting."""
    for subject in g.subjects(RDF.type, RDF.Property):
        if isinstance(subject, URIRef):
            result.info.append(ValidationIssue(
                severity="info",
                type="rdf_property",
                message=(
                    f"'{get_identifier_from_uri(subject)}' is typed as rdf:Property "
                    f"(not owl:ObjectProperty/DatatypeProperty)"
                ),
                entity_uri=str(subject),
            ))


def _check_unsupported_subclasses(g: Graph, result: ValidationResult) -> None:
    """Detect rdfs:subClassOf between ontology classes (not concept subclasses)."""
    concept_subclasses = find_concept_subclasses(g)
    count = 0
    for s, _p, o in g.triples((None, RDFS.subClassOf, None)):
        if not isinstance(s, URIRef) or not isinstance(o, URIRef):
            continue
        # Skip subClassOf skos:Concept (that's normal concept typing)
        if o == SKOS.Concept:
            continue
        # Skip if the subject is a concept subclass (already handled)
        if s in concept_subclasses:
            continue
        count += 1

    if count:
        result.info.append(ValidationIssue(
            severity="info",
            type="unsupported_subclass",
            message=(
                f"Found {count} subclass relationship{'s' if count != 1 else ''} "
                f"between ontology classes — not yet supported (#109)"
            ),
        ))


def _check_unsupported_union_domains(g: Graph, result: ValidationResult) -> None:
    """Detect owl:unionOf in property domains."""
    # find_properties() includes owl:ObjectProperty, owl:DatatypeProperty, and rdf:Property
    for uri, _ptype in find_properties(g):
        domain = g.value(uri, RDFS.domain)
        if isinstance(domain, BNode) and (domain, OWL.unionOf, None) in g:
            result.info.append(ValidationIssue(
                severity="info",
                type="unsupported_union_domain",
                message=(
                    f"Property '{get_identifier_from_uri(uri)}' has a union domain "
                    f"— only first class will be used (#110)"
                ),
                entity_uri=str(uri),
            ))


def _check_unsupported_named_individuals(g: Graph, result: ValidationResult) -> None:
    """Detect owl:NamedIndividual instances."""
    count = sum(
        1 for s in g.subjects(RDF.type, OWL.NamedIndividual)
        if isinstance(s, URIRef)
    )
    if count:
        result.info.append(ValidationIssue(
            severity="info",
            type="unsupported_named_individual",
            message=(
                f"Found {count} named individual{'s' if count != 1 else ''} "
                f"— not yet supported (#112)"
            ),
        ))


def _check_unsupported_restrictions(g: Graph, result: ValidationResult) -> None:
    """Detect owl:Restriction instances."""
    count = sum(1 for _ in g.subjects(RDF.type, OWL.Restriction))
    if count:
        result.info.append(ValidationIssue(
            severity="info",
            type="unsupported_restriction",
            message=(
                f"Found {count} OWL restriction{'s' if count != 1 else ''} "
                f"— these will be skipped (#113)"
            ),
        ))


# --- URI helpers ---


def get_identifier_from_uri(uri: URIRef) -> str:
    """Extract identifier (local name) from URI."""
    uri_str = str(uri)
    if "#" in uri_str:
        return uri_str.split("#")[-1]
    return uri_str.rstrip("/").split("/")[-1]


def abbreviate_xsd(uri_str: str) -> str:
    """Convert full XSD URI to xsd: prefix form, or return as-is."""
    if uri_str.startswith(XSD_NS):
        return "xsd:" + uri_str[len(XSD_NS):]
    return uri_str


# --- SKOS concept/scheme helpers ---


def find_all_concepts(g: Graph) -> set[URIRef]:
    """Find all concepts including those typed as subclasses of skos:Concept."""
    concepts: set[URIRef] = set()

    for instance in g.subjects(RDF.type, SKOS.Concept):
        if isinstance(instance, URIRef):
            concepts.add(instance)

    for concept_class in g.transitive_subjects(RDFS.subClassOf, SKOS.Concept):
        for instance in g.subjects(RDF.type, concept_class):
            if isinstance(instance, URIRef):
                concepts.add(instance)

    return concepts


def find_concept_subclasses(g: Graph) -> set[URIRef]:
    """Find owl:Class URIs that are rdfs:subClassOf skos:Concept."""
    subclasses: set[URIRef] = set()
    for cls in g.transitive_subjects(RDFS.subClassOf, SKOS.Concept):
        if isinstance(cls, URIRef) and cls != SKOS.Concept:
            subclasses.add(cls)
    return subclasses


def get_scheme_title(g: Graph, scheme_uri: URIRef) -> str:
    """Get scheme title with priority: rdfs:label > skos:prefLabel > dcterms:title > URI."""
    label = g.value(scheme_uri, RDFS.label)
    if label:
        return str(label)

    label = g.value(scheme_uri, SKOS.prefLabel)
    if label:
        return str(label)

    label = g.value(scheme_uri, DCTERMS.title)
    if label:
        return str(label)

    return get_identifier_from_uri(scheme_uri)


def get_scheme_description(g: Graph, scheme_uri: URIRef) -> str | None:
    """Get scheme description from rdfs:comment or dcterms:description."""
    desc = g.value(scheme_uri, RDFS.comment)
    if desc:
        return str(desc)
    desc = g.value(scheme_uri, DCTERMS.description)
    if desc:
        return str(desc)
    return None


def get_concept_scheme(g: Graph, concept_uri: URIRef) -> URIRef | None:
    """Get the scheme a concept belongs to via skos:inScheme or skos:topConceptOf."""
    scheme = g.value(concept_uri, SKOS.inScheme)
    if scheme and isinstance(scheme, URIRef):
        return scheme

    scheme = g.value(concept_uri, SKOS.topConceptOf)
    if scheme and isinstance(scheme, URIRef):
        return scheme

    return None


def get_concept_pref_label(g: Graph, concept_uri: URIRef) -> tuple[str, str | None]:
    """Get prefLabel for concept, returning (label, warning) tuple."""
    label = g.value(concept_uri, SKOS.prefLabel)
    if label:
        return str(label), None

    local_name = get_identifier_from_uri(concept_uri)
    warning = f"Concept {concept_uri} has no prefLabel, using URI fragment: {local_name}"
    return local_name, warning


def count_broader_relationships(g: Graph, concepts: set[URIRef]) -> int:
    """Count broader relationships among the given concepts."""
    count = 0
    for concept in concepts:
        for broader in g.objects(concept, SKOS.broader):
            if isinstance(broader, URIRef) and broader in concepts:
                count += 1
    return count


# --- OWL class helpers ---


def find_owl_classes(g: Graph) -> list[URIRef]:
    """Find owl:Class instances that are NOT subclasses of skos:Concept and not blank nodes."""
    concept_subclasses = find_concept_subclasses(g)

    classes: list[URIRef] = []
    for subject in g.subjects(RDF.type, OWL.Class):
        if not isinstance(subject, URIRef):
            continue
        if (subject, OWL.unionOf, None) in g:
            continue
        if subject in concept_subclasses:
            continue
        classes.append(subject)

    return classes


def extract_class_metadata(g: Graph, class_uri: URIRef) -> dict:
    """Extract label, description, scope_note for an OWL class."""
    uri_str = str(class_uri)

    label = g.value(class_uri, RDFS.label)
    if not label:
        label = get_identifier_from_uri(class_uri)
    else:
        label = str(label)

    description = g.value(class_uri, RDFS.comment)
    scope_note = g.value(class_uri, SKOS.scopeNote)

    return {
        "identifier": get_identifier_from_uri(class_uri),
        "label": str(label),
        "description": str(description) if description else None,
        "scope_note": str(scope_note) if scope_note else None,
        "uri": uri_str,
    }


# --- OWL property helpers ---


def find_properties(g: Graph) -> list[tuple[URIRef, str]]:
    """Find owl:ObjectProperty, owl:DatatypeProperty, and rdf:Property instances.

    Returns list of (uri, property_type) tuples, deduplicated by URI.
    If a property is typed as both ObjectProperty and DatatypeProperty,
    the type is resolved from rdfs:range: XSD range -> datatype,
    otherwise -> object.  rdf:Property instances get type "rdf".
    """
    object_props: set[URIRef] = set()
    datatype_props: set[URIRef] = set()
    rdf_props: set[URIRef] = set()

    for subject in g.subjects(RDF.type, OWL.ObjectProperty):
        if isinstance(subject, URIRef):
            object_props.add(subject)

    for subject in g.subjects(RDF.type, OWL.DatatypeProperty):
        if isinstance(subject, URIRef):
            datatype_props.add(subject)

    for subject in g.subjects(RDF.type, RDF.Property):
        if isinstance(subject, URIRef):
            rdf_props.add(subject)

    owl_uris = object_props | datatype_props
    properties: list[tuple[URIRef, str]] = []

    for uri in owl_uris:
        is_obj = uri in object_props
        is_dt = uri in datatype_props
        if is_obj and is_dt:
            range_val = g.value(uri, RDFS.range)
            if range_val and str(range_val).startswith(str(XSD)):
                properties.append((uri, "datatype"))
            else:
                properties.append((uri, "object"))
        elif is_dt:
            properties.append((uri, "datatype"))
        else:
            properties.append((uri, "object"))

    # Add rdf:Property instances not already covered by OWL types
    for uri in rdf_props - owl_uris:
        properties.append((uri, "rdf"))

    return properties


def _resolve_union_first(g: Graph, bnode: BNode) -> URIRef | None:
    """Extract the first URIRef from an owl:unionOf RDF list on a blank node."""
    union_list = g.value(bnode, OWL.unionOf)
    if union_list is None:
        return None
    # Walk rdf:first/rdf:rest list
    first = g.value(union_list, RDF.first)
    if isinstance(first, URIRef):
        return first
    return None


def extract_property_metadata(g: Graph, prop_uri: URIRef, prop_type: str) -> dict:
    """Extract metadata for a property."""
    label = g.value(prop_uri, RDFS.label)
    if not label:
        label = get_identifier_from_uri(prop_uri)
    else:
        label = str(label)

    description = g.value(prop_uri, RDFS.comment)
    domain = g.value(prop_uri, RDFS.domain)
    range_val = g.value(prop_uri, RDFS.range)

    # Resolve union domains to first class in the union
    domain_uri: str | None = None
    if isinstance(domain, URIRef):
        domain_uri = str(domain)
    elif isinstance(domain, BNode):
        first_class = _resolve_union_first(g, domain)
        if first_class is not None:
            domain_uri = str(first_class)

    # Read allowMultiple annotation for cardinality (any namespace)
    cardinality = "single"
    for pred, obj in g.predicate_objects(prop_uri):
        if str(pred).endswith("allowMultiple") and isinstance(obj, Literal):
            if obj.toPython() is True:
                cardinality = "multiple"
            break

    return {
        "identifier": get_identifier_from_uri(prop_uri),
        "label": str(label),
        "description": str(description) if description else None,
        "property_type": prop_type,
        "domain_uri": domain_uri,
        "range_uri": str(range_val) if isinstance(range_val, URIRef) else None,
        "uri": str(prop_uri),
        "cardinality": cardinality,
    }


def resolve_object_range(
    g: Graph,
    range_uri: str,
    scheme_uris: set[str],
    class_uris: set[str],
) -> tuple[str, str] | None:
    """Resolve an object property range URI.

    Returns ("scheme", scheme_uri), ("class", range_uri),
    ("ambiguous", range_uri), or None.

    Strategies:
    1. RDF linkage: find concepts typed with the range class, follow inScheme
    2. Direct scheme URI match
    3. Class URI match
    """
    range_ref = URIRef(range_uri)

    # Strategy 1: Follow RDF linkage to a scheme
    matched_schemes: set[str] = set()
    for instance in g.subjects(RDF.type, range_ref):
        if not isinstance(instance, URIRef):
            continue
        scheme = get_concept_scheme(g, instance)
        if scheme and str(scheme) in scheme_uris:
            matched_schemes.add(str(scheme))
    if len(matched_schemes) == 1:
        return ("scheme", next(iter(matched_schemes)))
    if len(matched_schemes) > 1:
        return ("ambiguous", range_uri)

    # Strategy 2: Direct scheme URI match
    if range_uri in scheme_uris:
        return ("scheme", range_uri)

    # Strategy 3: Class URI match
    if range_uri in class_uris:
        return ("class", range_uri)

    return None


# --- Graph analysis ---


def analyze_graph(g: Graph) -> dict:
    """Analyze the RDF graph and extract all entity types."""
    schemes: list[URIRef] = []
    for scheme in g.subjects(RDF.type, SKOS.ConceptScheme):
        if isinstance(scheme, URIRef):
            schemes.append(scheme)

    all_concepts = find_all_concepts(g)

    concepts_by_scheme: dict[URIRef, set[URIRef]] = {s: set() for s in schemes}
    orphan_concepts: set[URIRef] = set()

    for concept in all_concepts:
        scheme = get_concept_scheme(g, concept)
        if scheme and scheme in concepts_by_scheme:
            concepts_by_scheme[scheme].add(concept)
        else:
            orphan_concepts.add(concept)

    warnings: list[str] = []
    if orphan_concepts:
        if len(schemes) == 1:
            concepts_by_scheme[schemes[0]].update(orphan_concepts)
        else:
            for orphan in orphan_concepts:
                warnings.append(
                    f"Concept {orphan} has no scheme membership and was skipped"
                )

    owl_classes = find_owl_classes(g)
    class_metadata = [extract_class_metadata(g, cls) for cls in owl_classes]

    owl_properties = find_properties(g)
    property_metadata = [
        extract_property_metadata(g, uri, ptype)
        for uri, ptype in owl_properties
    ]

    return {
        "schemes": schemes,
        "concepts_by_scheme": concepts_by_scheme,
        "warnings": warnings,
        "classes": class_metadata,
        "properties": property_metadata,
    }
