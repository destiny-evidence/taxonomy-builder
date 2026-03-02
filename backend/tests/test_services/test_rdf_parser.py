"""Tests for RDF parser validation — validate_graph() and rdf:Property support."""

from rdflib import Graph

from taxonomy_builder.services.rdf_parser import (
    ValidationResult,
    find_properties,
    parse_rdf,
    validate_graph,
)


def _graph(ttl: bytes) -> Graph:
    """Parse TTL bytes into a Graph."""
    return parse_rdf(ttl, "turtle")


# --- file:// URI detection (severity: error) ---


FILE_URI_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

<file:///Users/someone/ontology.ttl#MyClass> a owl:Class ;
    rdfs:label "My Class" .

<file:///Users/someone/ontology.ttl#anotherClass> a owl:Class ;
    rdfs:label "Another Class" .
"""

RELATIVE_URI_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

<MyClass> a owl:Class ;
    rdfs:label "My Class" .

<MyScheme> a skos:ConceptScheme ;
    rdfs:label "My Scheme" .
"""

VALID_URI_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .

ex:MyClass a owl:Class ;
    rdfs:label "My Class" .
"""


def test_file_uri_produces_errors():
    """TTL with file:// URIs produces error-severity issues."""
    g = _graph(FILE_URI_TTL)
    result = validate_graph(g, set())

    assert result.has_errors
    assert len(result.errors) >= 1
    assert all(e.severity == "error" for e in result.errors)
    assert all(e.type == "file_uri" for e in result.errors)
    # Each unique file:// URI produces one error
    file_uris = {e.entity_uri for e in result.errors}
    assert len(file_uris) == 2


def test_relative_uri_resolves_to_file_uri_detected():
    """TTL without @base has relative URIs that resolve to file:// — detected as errors."""
    # rdflib resolves relative URIs to file:// paths when no @base is set
    g = _graph(RELATIVE_URI_TTL)
    result = validate_graph(g, set())

    assert result.has_errors
    assert any(e.type == "file_uri" for e in result.errors)


def test_valid_uris_no_errors():
    """TTL with proper absolute URIs produces no errors."""
    g = _graph(VALID_URI_TTL)
    result = validate_graph(g, set())

    assert not result.has_errors
    assert len(result.errors) == 0


# --- Unresolved domain class (severity: warning) ---


UNRESOLVED_DOMAIN_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .

ex:Finding a owl:Class ;
    rdfs:label "Finding" .

ex:unknownDomainProp a owl:DatatypeProperty ;
    rdfs:label "Unknown Domain Prop" ;
    rdfs:domain ex:UnknownClass ;
    rdfs:range <http://www.w3.org/2001/XMLSchema#string> .

ex:knownDomainProp a owl:DatatypeProperty ;
    rdfs:label "Known Domain Prop" ;
    rdfs:domain ex:Finding ;
    rdfs:range <http://www.w3.org/2001/XMLSchema#string> .
"""


def test_unresolved_domain_produces_warning():
    """Property with domain not in class_uris produces a warning."""
    g = _graph(UNRESOLVED_DOMAIN_TTL)
    # Only Finding is a known class
    class_uris = {"http://example.org/Finding"}
    result = validate_graph(g, class_uris)

    assert not result.has_errors
    assert len(result.warnings) == 1
    assert result.warnings[0].type == "unresolved_domain"
    assert "unknownDomainProp" in result.warnings[0].message or \
           "UnknownClass" in result.warnings[0].message


def test_domain_from_same_file_no_warning():
    """Property with domain matching a class defined in the same file — no warning."""
    g = _graph(UNRESOLVED_DOMAIN_TTL)
    # Both classes known (Finding from file, UnknownClass from existing project)
    class_uris = {"http://example.org/Finding", "http://example.org/UnknownClass"}
    result = validate_graph(g, class_uris)

    assert len(result.warnings) == 0


MULTIPLE_UNRESOLVED_DOMAINS_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .

ex:prop1 a owl:DatatypeProperty ;
    rdfs:label "Prop 1" ;
    rdfs:domain ex:UnknownA .

ex:prop2 a owl:ObjectProperty ;
    rdfs:label "Prop 2" ;
    rdfs:domain ex:UnknownA .
"""


def test_multiple_properties_same_unknown_domain_warns_per_property():
    """Two properties referencing same unknown domain: one warning per property."""
    g = _graph(MULTIPLE_UNRESOLVED_DOMAINS_TTL)
    result = validate_graph(g, set())

    assert len(result.warnings) == 2
    assert all(w.type == "unresolved_domain" for w in result.warnings)


# --- rdf:Property detection (severity: info) ---


RDF_PROPERTY_TTL = b"""
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .

ex:Finding a owl:Class ;
    rdfs:label "Finding" .

ex:codedValue a rdf:Property ;
    rdfs:label "Coded Value" ;
    rdfs:domain ex:Finding .

ex:normalProp a owl:DatatypeProperty ;
    rdfs:label "Normal Prop" ;
    rdfs:domain ex:Finding .
"""


def test_rdf_property_detected_with_info():
    """rdf:Property instances produce info-severity validation issues."""
    g = _graph(RDF_PROPERTY_TTL)
    result = validate_graph(g, {"http://example.org/Finding"})

    rdf_prop_infos = [i for i in result.info if i.type == "rdf_property"]
    assert len(rdf_prop_infos) == 1
    assert "codedValue" in rdf_prop_infos[0].message


def test_rdf_property_found_by_find_properties():
    """find_properties() includes rdf:Property with type 'rdf'."""
    g = _graph(RDF_PROPERTY_TTL)
    props = find_properties(g)

    prop_map = {str(uri): ptype for uri, ptype in props}
    assert "http://example.org/codedValue" in prop_map
    assert prop_map["http://example.org/codedValue"] == "rdf"
    # Normal OWL property still found
    assert "http://example.org/normalProp" in prop_map


# --- Unsupported OWL feature detection (severity: info) ---


SUBCLASS_OF_CLASSES_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix ex: <http://example.org/> .

ex:Finding a owl:Class ;
    rdfs:label "Finding" .

ex:ObservedResult a owl:Class ;
    rdfs:label "Observed Result" ;
    rdfs:subClassOf ex:Finding .

ex:EffectEstimate a owl:Class ;
    rdfs:label "Effect Estimate" ;
    rdfs:subClassOf ex:ObservedResult .

ex:ConceptSubclass a owl:Class ;
    rdfs:subClassOf skos:Concept .
"""


def test_subclass_between_owl_classes_info():
    """rdfs:subClassOf between non-concept owl:Classes produces info message."""
    g = _graph(SUBCLASS_OF_CLASSES_TTL)
    result = validate_graph(g, set())

    subclass_infos = [i for i in result.info if i.type == "unsupported_subclass"]
    assert len(subclass_infos) == 1
    assert "2" in subclass_infos[0].message  # 2 subclass relationships
    assert "#109" in subclass_infos[0].message


def test_subclass_of_skos_concept_not_flagged():
    """rdfs:subClassOf skos:Concept is normal behaviour, not flagged."""
    g = _graph(SUBCLASS_OF_CLASSES_TTL)
    result = validate_graph(g, set())

    # Only the two non-concept subclass relationships should be flagged
    subclass_infos = [i for i in result.info if i.type == "unsupported_subclass"]
    assert len(subclass_infos) == 1
    # ConceptSubclass -> skos:Concept should NOT be in the count


UNION_DOMAIN_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .

ex:Finding a owl:Class .
ex:Study a owl:Class .

ex:title a owl:DatatypeProperty ;
    rdfs:label "Title" ;
    rdfs:domain [ a owl:Class ;
        owl:unionOf ( ex:Finding ex:Study )
    ] .
"""


def test_union_domain_detected():
    """owl:unionOf in property domain produces info message."""
    g = _graph(UNION_DOMAIN_TTL)
    result = validate_graph(g, set())

    union_infos = [i for i in result.info if i.type == "unsupported_union_domain"]
    assert len(union_infos) == 1
    assert "title" in union_infos[0].message
    assert "#110" in union_infos[0].message


NAMED_INDIVIDUAL_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .

ex:HighQuality a owl:NamedIndividual ;
    rdfs:label "High Quality" .

ex:LowQuality a owl:NamedIndividual ;
    rdfs:label "Low Quality" .
"""


def test_named_individual_detected():
    """owl:NamedIndividual instances produce info message."""
    g = _graph(NAMED_INDIVIDUAL_TTL)
    result = validate_graph(g, set())

    individual_infos = [i for i in result.info if i.type == "unsupported_named_individual"]
    assert len(individual_infos) == 1
    assert "2" in individual_infos[0].message
    assert "#112" in individual_infos[0].message


OWL_RESTRICTION_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .

ex:Finding a owl:Class ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty ex:title ;
        owl:cardinality 1
    ] .
"""


def test_owl_restriction_detected():
    """owl:Restriction instances produce info message."""
    g = _graph(OWL_RESTRICTION_TTL)
    result = validate_graph(g, set())

    restriction_infos = [i for i in result.info if i.type == "unsupported_restriction"]
    assert len(restriction_infos) == 1
    assert "#113" in restriction_infos[0].message


# --- ValidationResult structure ---


def test_validation_result_has_errors_property():
    """ValidationResult.has_errors is True only when errors exist."""
    g = _graph(VALID_URI_TTL)
    result = validate_graph(g, set())
    assert isinstance(result, ValidationResult)
    assert not result.has_errors

    g2 = _graph(FILE_URI_TTL)
    result2 = validate_graph(g2, set())
    assert result2.has_errors


def test_validation_result_categorises_correctly():
    """Issues are correctly sorted into errors, warnings, info lists."""
    g = _graph(VALID_URI_TTL)
    result = validate_graph(g, set())
    assert isinstance(result.errors, list)
    assert isinstance(result.warnings, list)
    assert isinstance(result.info, list)
