"""Shared constants for ontology processing."""

from rdflib import URIRef
from rdflib.namespace import OWL, RDFS, SKOS

# Well-known external URIs allowed as superclass targets. These are not
# required to exist in a project's own class list and are excluded from
# cycle detection.
WELL_KNOWN_SUPERCLASS_URIS: frozenset[str] = frozenset({
    str(SKOS.Concept),
    str(OWL.Thing),
    str(RDFS.Resource),
})

# Same set as URIRefs for use in rdflib graph operations.
WELL_KNOWN_SUPERCLASS_URIREFS: frozenset[URIRef] = frozenset({
    SKOS.Concept,
    OWL.Thing,
    RDFS.Resource,
})
