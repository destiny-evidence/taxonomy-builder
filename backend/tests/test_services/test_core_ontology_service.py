"""Tests for Core Ontology Service - parsing OWL classes and properties from TTL."""

from pathlib import Path

import pytest

from taxonomy_builder.config import Settings
from taxonomy_builder.services.core_ontology_service import CoreOntologyService


# Sample TTL data for testing class parsing

SIMPLE_CLASSES_TTL = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/vocab/> .

ex:Investigation a owl:Class ;
    rdfs:label "Investigation" ;
    rdfs:comment "A research effort" .

ex:Finding a owl:Class ;
    rdfs:label "Finding" ;
    rdfs:comment "A specific result" .
"""

CLASS_WITH_MULTILINE_COMMENT_TTL = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/vocab/> .

ex:Investigation a owl:Class ;
    rdfs:label "Investigation" ;
    rdfs:comment \"\"\"A discrete research effort reported within a reference.
    Corresponds to a study, trial, or evaluation.\"\"\" .
"""

UNION_CLASS_TTL = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/vocab/> .

ex:Investigation a owl:Class ;
    rdfs:label "Investigation" .

ex:Intervention a owl:Class ;
    rdfs:label "Intervention" .

ex:Fundable a owl:Class ;
    owl:unionOf (ex:Investigation ex:Intervention) ;
    rdfs:label "Fundable" ;
    rdfs:comment "Entities that can receive funding." .
"""

BLANK_NODE_CLASS_TTL = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/vocab/> .

ex:Investigation a owl:Class ;
    rdfs:label "Investigation" .

# Blank node for AllDisjointClasses
[] a owl:AllDisjointClasses ;
    owl:members (ex:Investigation) .
"""

NO_CLASSES_TTL = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/vocab/> .

ex:something rdfs:label "Not a class" .
"""

MISSING_LABEL_TTL = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/vocab/> .

ex:Investigation a owl:Class ;
    rdfs:comment "A class without a label" .

ex:Finding a owl:Class ;
    rdfs:label "Finding" .
"""

NO_COMMENT_TTL = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/vocab/> .

ex:Investigation a owl:Class ;
    rdfs:label "Investigation" .
"""


class TestParseClasses:
    """Test class parsing from TTL content."""

    def test_parse_classes_from_ttl_content(self) -> None:
        """Test that we can parse OWL classes from TTL content."""
        service = CoreOntologyService()
        result = service.parse_from_string(SIMPLE_CLASSES_TTL)

        assert len(result.classes) == 2
        uris = [c.uri for c in result.classes]
        assert "http://example.org/vocab/Investigation" in uris
        assert "http://example.org/vocab/Finding" in uris

    def test_extracts_uri_label_and_comment(self) -> None:
        """Test that uri, label, and comment are extracted correctly."""
        service = CoreOntologyService()
        result = service.parse_from_string(SIMPLE_CLASSES_TTL)

        investigation = next(
            c for c in result.classes if "Investigation" in c.uri
        )
        assert investigation.uri == "http://example.org/vocab/Investigation"
        assert investigation.label == "Investigation"
        assert investigation.comment == "A research effort"

    def test_handles_multiline_comment(self) -> None:
        """Test that multiline comments are handled correctly."""
        service = CoreOntologyService()
        result = service.parse_from_string(CLASS_WITH_MULTILINE_COMMENT_TTL)

        investigation = result.classes[0]
        assert "discrete research effort" in investigation.comment
        assert "study, trial, or evaluation" in investigation.comment

    def test_excludes_union_classes(self) -> None:
        """Test that union classes (with owl:unionOf) are excluded from the classes list."""
        service = CoreOntologyService()
        result = service.parse_from_string(UNION_CLASS_TTL)

        # Should have Investigation and Intervention, but NOT Fundable
        assert len(result.classes) == 2
        uris = [c.uri for c in result.classes]
        assert "http://example.org/vocab/Investigation" in uris
        assert "http://example.org/vocab/Intervention" in uris
        assert "http://example.org/vocab/Fundable" not in uris

    def test_excludes_blank_nodes(self) -> None:
        """Test that blank nodes are not included in the classes list."""
        service = CoreOntologyService()
        result = service.parse_from_string(BLANK_NODE_CLASS_TTL)

        # Should only have Investigation, not the blank node
        assert len(result.classes) == 1
        assert result.classes[0].uri == "http://example.org/vocab/Investigation"

    def test_returns_empty_list_for_no_classes(self) -> None:
        """Test that an empty list is returned when there are no OWL classes."""
        service = CoreOntologyService()
        result = service.parse_from_string(NO_CLASSES_TTL)

        assert len(result.classes) == 0

    def test_handles_missing_labels_gracefully(self) -> None:
        """Test that classes without labels use URI fragment as label."""
        service = CoreOntologyService()
        result = service.parse_from_string(MISSING_LABEL_TTL)

        # Should have both classes
        assert len(result.classes) == 2

        # Investigation should use URI fragment as label
        investigation = next(
            c for c in result.classes if "Investigation" in c.uri
        )
        assert investigation.label == "Investigation"

        # Finding should have its explicit label
        finding = next(c for c in result.classes if "Finding" in c.uri)
        assert finding.label == "Finding"

    def test_handles_missing_comment(self) -> None:
        """Test that classes without comments have None for comment."""
        service = CoreOntologyService()
        result = service.parse_from_string(NO_COMMENT_TTL)

        investigation = result.classes[0]
        assert investigation.comment is None


# Sample TTL data for testing property parsing

OBJECT_PROPERTY_TTL = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/vocab/> .

ex:Investigation a owl:Class ;
    rdfs:label "Investigation" .

ex:Finding a owl:Class ;
    rdfs:label "Finding" .

ex:hasFinding a owl:ObjectProperty ;
    rdfs:label "has finding" ;
    rdfs:comment "Links an investigation to its findings." ;
    rdfs:domain ex:Investigation ;
    rdfs:range ex:Finding .
"""

DATATYPE_PROPERTY_TTL = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.org/vocab/> .

ex:Finding a owl:Class ;
    rdfs:label "Finding" .

ex:sampleSize a owl:DatatypeProperty ;
    rdfs:label "sample size" ;
    rdfs:comment "Number of participants in the finding." ;
    rdfs:domain ex:Finding ;
    rdfs:range xsd:integer .
"""

UNION_DOMAIN_TTL = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/vocab/> .

ex:Investigation a owl:Class ;
    rdfs:label "Investigation" .

ex:Intervention a owl:Class ;
    rdfs:label "Intervention" .

ex:Funder a owl:Class ;
    rdfs:label "Funder" .

ex:Fundable a owl:Class ;
    owl:unionOf (ex:Investigation ex:Intervention) ;
    rdfs:label "Fundable" .

ex:fundedBy a owl:ObjectProperty ;
    rdfs:label "funded by" ;
    rdfs:comment "Links a fundable entity to its funder(s)." ;
    rdfs:domain ex:Fundable ;
    rdfs:range ex:Funder .
"""

UNION_RANGE_TTL = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/vocab/> .

ex:Investigation a owl:Class ;
    rdfs:label "Investigation" .

ex:Person a owl:Class ;
    rdfs:label "Person" .

ex:Organization a owl:Class ;
    rdfs:label "Organization" .

ex:Agent a owl:Class ;
    owl:unionOf (ex:Person ex:Organization) ;
    rdfs:label "Agent" .

ex:conductedBy a owl:ObjectProperty ;
    rdfs:label "conducted by" ;
    rdfs:domain ex:Investigation ;
    rdfs:range ex:Agent .
"""

PROPERTY_MISSING_DOMAIN_RANGE_TTL = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/vocab/> .

ex:someProperty a owl:ObjectProperty ;
    rdfs:label "some property" .

ex:anotherProperty a owl:DatatypeProperty ;
    rdfs:label "another property" .
"""

MULTIPLE_PROPERTIES_TTL = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.org/vocab/> .

ex:Investigation a owl:Class ;
    rdfs:label "Investigation" .

ex:Finding a owl:Class ;
    rdfs:label "Finding" .

ex:hasFinding a owl:ObjectProperty ;
    rdfs:label "has finding" ;
    rdfs:domain ex:Investigation ;
    rdfs:range ex:Finding .

ex:partOfInvestigation a owl:ObjectProperty ;
    rdfs:label "part of investigation" ;
    rdfs:domain ex:Finding ;
    rdfs:range ex:Investigation .

ex:sampleSize a owl:DatatypeProperty ;
    rdfs:label "sample size" ;
    rdfs:domain ex:Finding ;
    rdfs:range xsd:integer .

ex:attritionRate a owl:DatatypeProperty ;
    rdfs:label "attrition rate" ;
    rdfs:domain ex:Finding ;
    rdfs:range xsd:decimal .
"""


class TestParseObjectProperties:
    """Test object property parsing from TTL content."""

    def test_parse_object_properties(self) -> None:
        """Test that we can parse OWL object properties from TTL content."""
        service = CoreOntologyService()
        result = service.parse_from_string(OBJECT_PROPERTY_TTL)

        assert len(result.object_properties) == 1
        prop = result.object_properties[0]
        assert prop.uri == "http://example.org/vocab/hasFinding"
        assert prop.label == "has finding"
        assert prop.comment == "Links an investigation to its findings."
        assert prop.property_type == "object"

    def test_extracts_domain_and_range(self) -> None:
        """Test that domain and range are extracted as lists."""
        service = CoreOntologyService()
        result = service.parse_from_string(OBJECT_PROPERTY_TTL)

        prop = result.object_properties[0]
        assert prop.domain == ["http://example.org/vocab/Investigation"]
        assert prop.range == ["http://example.org/vocab/Finding"]

    def test_expands_union_class_in_domain(self) -> None:
        """Test that union classes in domain are expanded to member classes."""
        service = CoreOntologyService()
        result = service.parse_from_string(UNION_DOMAIN_TTL)

        funded_by = next(
            p for p in result.object_properties if "fundedBy" in p.uri
        )
        # Domain should be expanded to [Investigation, Intervention]
        assert len(funded_by.domain) == 2
        assert "http://example.org/vocab/Investigation" in funded_by.domain
        assert "http://example.org/vocab/Intervention" in funded_by.domain
        # Range should remain as is
        assert funded_by.range == ["http://example.org/vocab/Funder"]

    def test_expands_union_class_in_range(self) -> None:
        """Test that union classes in range are expanded to member classes."""
        service = CoreOntologyService()
        result = service.parse_from_string(UNION_RANGE_TTL)

        conducted_by = next(
            p for p in result.object_properties if "conductedBy" in p.uri
        )
        # Range should be expanded to [Person, Organization]
        assert len(conducted_by.range) == 2
        assert "http://example.org/vocab/Person" in conducted_by.range
        assert "http://example.org/vocab/Organization" in conducted_by.range
        # Domain should remain as is
        assert conducted_by.domain == ["http://example.org/vocab/Investigation"]

    def test_handles_missing_domain_or_range(self) -> None:
        """Test that properties without domain/range have empty lists."""
        service = CoreOntologyService()
        result = service.parse_from_string(PROPERTY_MISSING_DOMAIN_RANGE_TTL)

        obj_prop = next(
            p for p in result.object_properties if "someProperty" in p.uri
        )
        assert obj_prop.domain == []
        assert obj_prop.range == []


class TestParseDatatypeProperties:
    """Test datatype property parsing from TTL content."""

    def test_parse_datatype_properties(self) -> None:
        """Test that we can parse OWL datatype properties from TTL content."""
        service = CoreOntologyService()
        result = service.parse_from_string(DATATYPE_PROPERTY_TTL)

        assert len(result.datatype_properties) == 1
        prop = result.datatype_properties[0]
        assert prop.uri == "http://example.org/vocab/sampleSize"
        assert prop.label == "sample size"
        assert prop.comment == "Number of participants in the finding."
        assert prop.property_type == "datatype"

    def test_datatype_property_has_range_datatype(self) -> None:
        """Test that datatype properties have their XSD datatype in range."""
        service = CoreOntologyService()
        result = service.parse_from_string(DATATYPE_PROPERTY_TTL)

        prop = result.datatype_properties[0]
        assert prop.domain == ["http://example.org/vocab/Finding"]
        assert prop.range == ["http://www.w3.org/2001/XMLSchema#integer"]

    def test_handles_missing_domain_or_range(self) -> None:
        """Test that datatype properties without domain/range have empty lists."""
        service = CoreOntologyService()
        result = service.parse_from_string(PROPERTY_MISSING_DOMAIN_RANGE_TTL)

        dt_prop = next(
            p for p in result.datatype_properties if "anotherProperty" in p.uri
        )
        assert dt_prop.domain == []
        assert dt_prop.range == []


class TestParseMultipleProperties:
    """Test parsing multiple properties from a single TTL."""

    def test_parses_both_object_and_datatype_properties(self) -> None:
        """Test that both object and datatype properties are extracted."""
        service = CoreOntologyService()
        result = service.parse_from_string(MULTIPLE_PROPERTIES_TTL)

        assert len(result.object_properties) == 2
        assert len(result.datatype_properties) == 2

        obj_uris = [p.uri for p in result.object_properties]
        assert "http://example.org/vocab/hasFinding" in obj_uris
        assert "http://example.org/vocab/partOfInvestigation" in obj_uris

        dt_uris = [p.uri for p in result.datatype_properties]
        assert "http://example.org/vocab/sampleSize" in dt_uris
        assert "http://example.org/vocab/attritionRate" in dt_uris


class TestConfiguration:
    """Test configuration and file loading."""

    def test_settings_has_core_ontology_path(self) -> None:
        """Test that Settings has a core_ontology_path field."""
        settings = Settings()
        assert hasattr(settings, "core_ontology_path")

    def test_default_path_points_to_bundled_file(self) -> None:
        """Test that the default path points to the bundled evrepo-core.ttl file."""
        settings = Settings()
        path = Path(settings.core_ontology_path)
        assert path.name == "evrepo-core.ttl"
        assert path.exists(), f"Bundled file does not exist at {path}"

    def test_service_loads_from_file_path(self) -> None:
        """Test that the service can load from a file path."""
        settings = Settings()
        service = CoreOntologyService()
        result = service.parse_from_file(settings.core_ontology_path)

        # Should have parsed the bundled ontology
        assert len(result.classes) > 0
        # Should have Investigation class from the core ontology
        uris = [c.uri for c in result.classes]
        assert any("Investigation" in uri for uri in uris)
