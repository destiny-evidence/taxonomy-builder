"""Tests for Core Ontology Service - parsing OWL classes and properties from TTL."""

import pytest

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
