"""Tests for RDF parser validation — validate_graph() and rdf:Property support."""

from rdflib import Graph, URIRef

from taxonomy_builder.services.rdf_parser import (
    ValidationResult,
    detect_superclass_cycles,
    extract_class_metadata,
    extract_concept_type_uris,
    extract_property_metadata,
    extract_restrictions,
    find_owl_classes,
    find_properties,
    parse_rdf,
    validate_graph,
)


def _graph(ttl: bytes) -> Graph:
    """Parse TTL bytes into a Graph."""
    return parse_rdf(ttl, "turtle")


# --- URI scheme validation (severity: error) ---


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


UNSUPPORTED_SCHEME_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

<ftp://example.org/MyClass> a owl:Class ;
    rdfs:label "My Class" .
"""


def test_unsupported_uri_scheme_produces_errors():
    """TTL with non-http(s) URI schemes (e.g. ftp://) produces errors."""
    g = _graph(UNSUPPORTED_SCHEME_TTL)
    result = validate_graph(g, set())

    assert result.has_errors
    scheme_errors = [e for e in result.errors if e.type == "unsupported_uri_scheme"]
    assert len(scheme_errors) >= 1
    assert "ftp" in scheme_errors[0].message


def test_file_uri_has_base_hint():
    """file:// URIs get a specific hint about missing @base directive."""
    g = _graph(FILE_URI_TTL)
    result = validate_graph(g, set())

    file_errors = [e for e in result.errors if e.type == "file_uri"]
    assert len(file_errors) >= 1
    assert "@base" in file_errors[0].message


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


def test_subclass_no_longer_flagged_as_unsupported():
    """rdfs:subClassOf between owl:Classes is now supported — no info message."""
    g = _graph(SUBCLASS_OF_CLASSES_TTL)
    result = validate_graph(g, set())

    unsupported = [i for i in result.info if i.type == "unsupported_subclass"]
    assert len(unsupported) == 0


# --- superclass_uris extraction ---


def test_extract_class_metadata_includes_superclass_uris():
    """extract_class_metadata() should include superclass_uris for classes with rdfs:subClassOf."""
    g = _graph(SUBCLASS_OF_CLASSES_TTL)

    obs_uri = URIRef("http://example.org/ObservedResult")
    metadata = extract_class_metadata(g, obs_uri, exclude_superclass_uris=set())
    assert metadata["superclass_uris"] == ["http://example.org/Finding"]


def test_extract_class_metadata_no_superclass():
    """Classes without rdfs:subClassOf should have empty superclass_uris."""
    g = _graph(SUBCLASS_OF_CLASSES_TTL)
    finding_uri = URIRef("http://example.org/Finding")
    metadata = extract_class_metadata(g, finding_uri, exclude_superclass_uris=set())
    assert metadata["superclass_uris"] == []


def test_extract_class_metadata_filters_skos_concept_superclass():
    """superclass_uris should exclude skos:Concept and concept subclasses."""
    ttl = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix ex: <http://example.org/> .

ex:ConceptType a owl:Class ;
    rdfs:subClassOf skos:Concept .

ex:SpecialConcept a owl:Class ;
    rdfs:subClassOf ex:ConceptType .
"""
    g = _graph(ttl)

    from taxonomy_builder.services.rdf_parser import find_concept_subclasses
    concept_subs = find_concept_subclasses(g)

    special_uri = URIRef("http://example.org/SpecialConcept")
    metadata = extract_class_metadata(g, special_uri, exclude_superclass_uris=concept_subs)
    # ConceptType is a concept subclass, so should be filtered out
    assert metadata["superclass_uris"] == []


def test_extract_class_metadata_filters_blank_node_superclass():
    """superclass_uris should exclude blank nodes (OWL restrictions)."""
    ttl = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .

ex:Parent a owl:Class .

ex:Child a owl:Class ;
    rdfs:subClassOf ex:Parent ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty ex:title ;
        owl:allValuesFrom ex:StringType
    ] .
"""
    g = _graph(ttl)
    child_uri = URIRef("http://example.org/Child")
    metadata = extract_class_metadata(g, child_uri, exclude_superclass_uris=set())
    # Only the named URIRef superclass, not the blank node restriction
    assert metadata["superclass_uris"] == ["http://example.org/Parent"]


# --- Cycle detection ---


def test_detect_superclass_cycles_no_cycle():
    """DAG with no cycles returns empty list."""
    class_metadata = [
        {"uri": "http://example.org/A", "superclass_uris": ["http://example.org/B"]},
        {"uri": "http://example.org/B", "superclass_uris": ["http://example.org/C"]},
        {"uri": "http://example.org/C", "superclass_uris": []},
    ]
    assert detect_superclass_cycles(class_metadata) == []


def test_detect_superclass_cycles_simple_cycle():
    """Direct cycle A→B→A detected."""
    class_metadata = [
        {"uri": "http://example.org/A", "superclass_uris": ["http://example.org/B"]},
        {"uri": "http://example.org/B", "superclass_uris": ["http://example.org/A"]},
    ]
    cycles = detect_superclass_cycles(class_metadata)
    assert len(cycles) == 1


def test_detect_superclass_cycles_self_referential():
    """Self-loop A→A detected."""
    class_metadata = [
        {"uri": "http://example.org/A", "superclass_uris": ["http://example.org/A"]},
    ]
    cycles = detect_superclass_cycles(class_metadata)
    assert len(cycles) == 1


def test_detect_superclass_cycles_three_node_cycle():
    """Transitive cycle A→B→C→A detected."""
    class_metadata = [
        {"uri": "http://example.org/A", "superclass_uris": ["http://example.org/B"]},
        {"uri": "http://example.org/B", "superclass_uris": ["http://example.org/C"]},
        {"uri": "http://example.org/C", "superclass_uris": ["http://example.org/A"]},
    ]
    cycles = detect_superclass_cycles(class_metadata)
    assert len(cycles) == 1
    # The cycle-forming back-edge should reference A
    assert any("A" in edge[1] for edge in cycles)


def test_detect_superclass_cycles_diamond_is_valid():
    """Diamond hierarchy (D→B, D→C, B→A, C→A) is a valid DAG, no cycles."""
    class_metadata = [
        {"uri": "http://example.org/D", "superclass_uris": ["http://example.org/B", "http://example.org/C"]},
        {"uri": "http://example.org/B", "superclass_uris": ["http://example.org/A"]},
        {"uri": "http://example.org/C", "superclass_uris": ["http://example.org/A"]},
        {"uri": "http://example.org/A", "superclass_uris": []},
    ]
    assert detect_superclass_cycles(class_metadata) == []


def test_validate_graph_cycle_produces_error():
    """Cycle in subClassOf should produce an error-severity validation issue."""
    ttl = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .

ex:A a owl:Class ;
    rdfs:label "A" ;
    rdfs:subClassOf ex:B .

ex:B a owl:Class ;
    rdfs:label "B" ;
    rdfs:subClassOf ex:A .
"""
    g = _graph(ttl)
    result = validate_graph(g, set())
    assert result.has_errors
    cycle_errors = [e for e in result.errors if e.type == "superclass_cycle"]
    assert len(cycle_errors) == 1


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


def test_union_domain_no_unsupported_info():
    """owl:unionOf in property domain no longer emits unsupported info (#110)."""
    g = _graph(UNION_DOMAIN_TTL)
    result = validate_graph(g, set())

    union_infos = [i for i in result.info if i.type == "unsupported_union_domain"]
    assert len(union_infos) == 0


def test_union_domain_extracts_all_classes():
    """extract_property_metadata resolves union domain to all class URIs."""
    g = _graph(UNION_DOMAIN_TTL)
    props = find_properties(g)
    assert len(props) == 1
    uri, ptype = props[0]

    metadata = extract_property_metadata(g, uri, ptype)
    assert sorted(metadata["domain_uris"]) == [
        "http://example.org/Finding",
        "http://example.org/Study",
    ]


UNION_DOMAIN_RDF_PROPERTY_TTL = b"""
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .

ex:Finding a owl:Class .
ex:CodingAnnotation a owl:Class .

ex:codedBy a rdf:Property ;
    rdfs:label "Coded By" ;
    rdfs:domain [ a owl:Class ;
        owl:unionOf ( ex:Finding ex:CodingAnnotation )
    ] .
"""


def test_union_domain_rdf_property_extracts_all_classes():
    """rdf:Property with union domain extracts all class URIs."""
    g = _graph(UNION_DOMAIN_RDF_PROPERTY_TTL)
    props = find_properties(g)
    uri, ptype = [(u, t) for u, t in props if str(u).endswith("codedBy")][0]

    metadata = extract_property_metadata(g, uri, ptype)
    assert sorted(metadata["domain_uris"]) == [
        "http://example.org/CodingAnnotation",
        "http://example.org/Finding",
    ]


THREE_MEMBER_UNION_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.org/> .

ex:Finding a owl:Class .
ex:CodingAnnotation a owl:Class .
ex:Study a owl:Class .

ex:supportingText a owl:DatatypeProperty ;
    rdfs:label "Supporting Text" ;
    rdfs:domain [ a owl:Class ;
        owl:unionOf ( ex:Finding ex:CodingAnnotation ex:Study )
    ] ;
    rdfs:range xsd:string .
"""


def test_three_member_union_extracts_all():
    """extract_property_metadata on 3-member union returns all 3 URIs."""
    g = _graph(THREE_MEMBER_UNION_TTL)
    props = find_properties(g)
    assert len(props) == 1
    uri, ptype = props[0]

    metadata = extract_property_metadata(g, uri, ptype)
    assert sorted(metadata["domain_uris"]) == [
        "http://example.org/CodingAnnotation",
        "http://example.org/Finding",
        "http://example.org/Study",
    ]


def test_plain_domain_returns_single_uri_list():
    """Plain URIRef domain returns a one-element domain_uris list."""
    ttl = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.org/> .

ex:Finding a owl:Class .
ex:title a owl:DatatypeProperty ;
    rdfs:label "Title" ;
    rdfs:domain ex:Finding ;
    rdfs:range xsd:string .
"""
    g = _graph(ttl)
    props = find_properties(g)
    uri, ptype = props[0]
    metadata = extract_property_metadata(g, uri, ptype)
    assert metadata["domain_uris"] == ["http://example.org/Finding"]


def test_no_domain_returns_empty_list():
    """Property with no rdfs:domain returns domain_uris=[]."""
    ttl = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.org/> .

ex:title a owl:DatatypeProperty ;
    rdfs:label "Title" ;
    rdfs:range xsd:string .
"""
    g = _graph(ttl)
    props = find_properties(g)
    uri, ptype = props[0]
    metadata = extract_property_metadata(g, uri, ptype)
    assert metadata["domain_uris"] == []


def test_unresolved_union_domain_members_warn():
    """_check_unresolved_domains warns for each unresolved URI in a union."""
    ttl = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .

ex:Finding a owl:Class .

ex:title a owl:DatatypeProperty ;
    rdfs:label "Title" ;
    rdfs:domain [ a owl:Class ;
        owl:unionOf ( ex:Finding ex:Unknown ex:AlsoUnknown )
    ] .
"""
    g = _graph(ttl)
    known = {"http://example.org/Finding"}
    result = validate_graph(g, known)
    unresolved = [
        w for w in result.warnings if w.type == "unresolved_domain"
    ]
    # Should warn about ex:Unknown and ex:AlsoUnknown but not ex:Finding
    assert len(unresolved) == 2
    messages = " ".join(w.message for w in unresolved)
    assert "Unknown" in messages
    assert "AlsoUnknown" in messages


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
    """owl:Restriction instances produce warning with enumerated details."""
    g = _graph(OWL_RESTRICTION_TTL)
    result = validate_graph(g, set())

    restriction_warnings = [w for w in result.warnings if w.type == "unsupported_restriction"]
    assert len(restriction_warnings) == 1
    assert restriction_warnings[0].severity == "warning"
    # Property name from the fixture is "title"
    assert "title" in restriction_warnings[0].message
    assert "dropped on import" in restriction_warnings[0].message


OWL_ALL_VALUES_FROM_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .

ex:StringAnnotation a owl:Class ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty ex:codedValue ;
        owl:allValuesFrom ex:StringType
    ] .
"""


def test_all_values_from_restriction_not_warned():
    """allValuesFrom restrictions are now handled — no unsupported_restriction warning."""
    g = _graph(OWL_ALL_VALUES_FROM_TTL)
    result = validate_graph(g, set())

    restriction_warnings = [w for w in result.warnings if w.type == "unsupported_restriction"]
    assert len(restriction_warnings) == 0


# --- Empty graph detection ---


EMPTY_GRAPH_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
"""


def test_empty_graph_produces_warning():
    """A graph with no triples produces a warning."""
    g = _graph(EMPTY_GRAPH_TTL)
    result = validate_graph(g, set())

    assert len(result.warnings) == 1
    assert result.warnings[0].type == "empty_graph"


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


# --- Restriction extraction (#144) ---


RESTRICTION_TTL = b"""
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix ex: <http://example.org/> .

ex:CodingAnnotation a owl:Class ;
    rdfs:label "CodingAnnotation" .

ex:StringAnnotation a owl:Class ;
    rdfs:subClassOf ex:CodingAnnotation ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty ex:codedValue ;
        owl:allValuesFrom xsd:string
    ] ;
    rdfs:label "String Annotation" .

ex:codedValue a rdf:Property ;
    rdfs:label "coded value" .
"""

CONCEPT_TYPED_CLASS_TTL = b"""
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix ex: <http://example.org/> .

ex:EducationLevelConcept a owl:Class ;
    rdfs:subClassOf skos:Concept ;
    rdfs:label "Education Level Concept" .

ex:EducationLevelScheme a skos:ConceptScheme ;
    rdfs:label "Education Levels" .

ex:Primary a ex:EducationLevelConcept , skos:Concept ;
    skos:inScheme ex:EducationLevelScheme ;
    skos:prefLabel "Primary" .
"""


def test_extract_restrictions():
    g = _graph(RESTRICTION_TTL)
    class_uris = find_owl_classes(g)
    class_uri_set = {str(u) for u in class_uris}

    restrictions = extract_restrictions(g, class_uri_set)

    assert len(restrictions) == 1
    r = restrictions[0]
    assert r["class_uri"] == "http://example.org/StringAnnotation"
    assert r["on_property_uri"] == "http://example.org/codedValue"
    assert r["restriction_type"] == "allValuesFrom"
    assert r["value_uri"] == "http://www.w3.org/2001/XMLSchema#string"


def test_extract_restrictions_multiple():
    """Multiple restrictions on different classes."""
    ttl = b"""
    @prefix owl: <http://www.w3.org/2002/07/owl#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix ex: <http://example.org/> .

    ex:Base a owl:Class ; rdfs:label "Base" .
    ex:ClassA a owl:Class ;
        rdfs:subClassOf ex:Base ;
        rdfs:subClassOf [ a owl:Restriction ;
            owl:onProperty ex:value ;
            owl:allValuesFrom xsd:string ] ;
        rdfs:label "A" .
    ex:ClassB a owl:Class ;
        rdfs:subClassOf ex:Base ;
        rdfs:subClassOf [ a owl:Restriction ;
            owl:onProperty ex:value ;
            owl:allValuesFrom xsd:integer ] ;
        rdfs:label "B" .
    """
    g = _graph(ttl)
    class_uris = find_owl_classes(g)

    restrictions = extract_restrictions(g, {str(u) for u in class_uris})
    assert len(restrictions) == 2


def test_extract_concept_type_uris():
    g = _graph(CONCEPT_TYPED_CLASS_TTL)

    concept_uri = URIRef("http://example.org/Primary")
    type_uris = extract_concept_type_uris(g, concept_uri)

    assert type_uris == ["http://example.org/EducationLevelConcept"]


def test_extract_concept_type_uris_plain_concept():
    """A plain skos:Concept should have no extra type URIs."""
    ttl = b"""
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    @prefix ex: <http://example.org/> .

    ex:Scheme a skos:ConceptScheme ; skos:prefLabel "S" .
    ex:Concept1 a skos:Concept ;
        skos:inScheme ex:Scheme ;
        skos:prefLabel "C1" .
    """
    g = _graph(ttl)

    type_uris = extract_concept_type_uris(g, URIRef("http://example.org/Concept1"))
    assert type_uris == []


def test_extract_concept_type_uris_captures_all_non_skos():
    """Round-trip fidelity: capture ALL rdf:type URIs, not just concept subclasses."""
    ttl = b"""
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    @prefix owl: <http://www.w3.org/2002/07/owl#> .
    @prefix ex: <http://example.org/> .

    ex:Scheme a skos:ConceptScheme ; skos:prefLabel "S" .
    ex:Thing a skos:Concept , ex:MarkerClass ;
        skos:inScheme ex:Scheme ;
        skos:prefLabel "Thing" .
    """
    g = _graph(ttl)

    type_uris = extract_concept_type_uris(g, URIRef("http://example.org/Thing"))
    assert "http://example.org/MarkerClass" in type_uris


def test_find_owl_classes_includes_concept_typed():
    """find_owl_classes should include concept-typed classes (subClassOf skos:Concept)."""
    g = _graph(CONCEPT_TYPED_CLASS_TTL)

    classes = find_owl_classes(g)
    class_uris = {str(c) for c in classes}
    assert "http://example.org/EducationLevelConcept" in class_uris


def test_extract_class_metadata_includes_skos_concept_superclass():
    """Concept-typed classes should have skos:Concept in superclass_uris."""
    g = _graph(CONCEPT_TYPED_CLASS_TTL)

    uri = URIRef("http://example.org/EducationLevelConcept")
    metadata = extract_class_metadata(g, uri)

    assert "http://www.w3.org/2004/02/skos/core#Concept" in metadata["superclass_uris"]


def test_somevaluesfrom_restriction_extracted():
    """someValuesFrom should be extracted, not warned about."""
    ttl = b"""
    @prefix owl: <http://www.w3.org/2002/07/owl#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix ex: <http://example.org/> .

    ex:Cls a owl:Class ;
        rdfs:subClassOf [ a owl:Restriction ;
            owl:onProperty ex:prop ;
            owl:someValuesFrom ex:Range ] ;
        rdfs:label "Cls" .
    """
    g = _graph(ttl)

    restrictions = extract_restrictions(g, {"http://example.org/Cls"})
    assert len(restrictions) == 1
    assert restrictions[0]["restriction_type"] == "someValuesFrom"
    assert restrictions[0]["value_uri"] == "http://example.org/Range"

    # No unsupported warning
    result = validate_graph(g, {"http://example.org/Cls"})
    restriction_warnings = [
        w for w in result.warnings if w.type == "unsupported_restriction"
    ]
    assert len(restriction_warnings) == 0


def test_hasvalue_restriction_extracted():
    """hasValue should be extracted."""
    ttl = b"""
    @prefix owl: <http://www.w3.org/2002/07/owl#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix ex: <http://example.org/> .

    ex:Cls a owl:Class ;
        rdfs:subClassOf [ a owl:Restriction ;
            owl:onProperty ex:status ;
            owl:hasValue ex:Active ] ;
        rdfs:label "Cls" .
    """
    g = _graph(ttl)

    restrictions = extract_restrictions(g, {"http://example.org/Cls"})
    assert len(restrictions) == 1
    assert restrictions[0]["restriction_type"] == "hasValue"
    assert restrictions[0]["value_uri"] == "http://example.org/Active"
