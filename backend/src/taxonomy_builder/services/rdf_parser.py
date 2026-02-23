"""Pure RDF parsing and analysis — no database access."""

from rdflib import Graph, Literal, URIRef
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
    """Find owl:ObjectProperty and owl:DatatypeProperty instances.

    Returns list of (uri, property_type) tuples, deduplicated by URI.
    If a property is typed as both ObjectProperty and DatatypeProperty,
    the type is resolved from rdfs:range: XSD range -> datatype,
    otherwise -> object.
    """
    object_props: set[URIRef] = set()
    datatype_props: set[URIRef] = set()

    for subject in g.subjects(RDF.type, OWL.ObjectProperty):
        if isinstance(subject, URIRef):
            object_props.add(subject)

    for subject in g.subjects(RDF.type, OWL.DatatypeProperty):
        if isinstance(subject, URIRef):
            datatype_props.add(subject)

    all_uris = object_props | datatype_props
    properties: list[tuple[URIRef, str]] = []

    for uri in all_uris:
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

    return properties


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
        "domain_uri": str(domain) if isinstance(domain, URIRef) else None,
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
