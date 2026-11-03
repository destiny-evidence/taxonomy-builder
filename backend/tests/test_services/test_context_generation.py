"""Tests for JSON-LD @context generation from vocabulary snapshots."""

import json
from uuid import UUID

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD

from taxonomy_builder.schemas.snapshot import SnapshotVocabulary
from taxonomy_builder.services.context_generation_service import ContextGenerationService

PROJECT_ID = UUID("01965a00-0000-7000-8000-000000000000")
SCHEME_ID = UUID("01965a00-0000-7000-8000-000000000001")
CLASS_ID = UUID("01965a00-0000-7000-8000-b00000000001")
EXT_CLASS_ID = UUID("01965a00-0000-7000-8000-b00000000002")
PROP_OBJ_ID = UUID("01965a00-0000-7000-8000-a00000000001")
PROP_DT_ID = UUID("01965a00-0000-7000-8000-a00000000002")
PROP_MULTI_ID = UUID("01965a00-0000-7000-8000-a00000000003")
PROP_EXT_ID = UUID("01965a00-0000-7000-8000-a00000000004")
PROP_RDF_ID = UUID("01965a00-0000-7000-8000-a00000000005")

PROJECT_NS = "https://vocab.esea.education/"
EXTERNAL_NS = "https://vocab.evidence-repository.org/"

DEFAULT_PREFIXES = {
    "esea": PROJECT_NS,
    "evrepo": EXTERNAL_NS,
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
}


def _make_snapshot(
    *,
    classes=None,
    properties=None,
    namespace_prefixes=None,
    namespace=PROJECT_NS,
):
    """Build a SnapshotVocabulary for testing context generation."""
    snap = {
        "project": {
            "id": str(PROJECT_ID),
            "name": "ESEA",
            "description": None,
            "namespace": namespace,
            "namespace_prefixes": namespace_prefixes or DEFAULT_PREFIXES,
        },
        "concept_schemes": [
            {
                "id": str(SCHEME_ID),
                "title": "Education Level",
                "uri": f"{PROJECT_NS}educationLevel",
                "concepts": [
                    {
                        "id": "01965a00-0000-7000-8000-000000000099",
                        "pref_label": "Primary",
                        "identifier": "C00001",
                        "uri": f"{PROJECT_NS}C00001",
                        "broader_ids": [],
                        "related_ids": [],
                        "alt_labels": [],
                        "concept_type_uris": [],
                    }
                ],
            }
        ],
        "classes": classes or [],
        "properties": properties or [],
    }
    return SnapshotVocabulary.model_validate(snap)


class TestVocabAndPrefixes:
    def test_vocab_set_to_project_namespace(self):
        snapshot = _make_snapshot()
        result = ContextGenerationService().generate(snapshot)
        assert result["@context"]["@vocab"] == PROJECT_NS

    def test_namespace_prefixes_included(self):
        snapshot = _make_snapshot()
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["esea"] == PROJECT_NS
        assert ctx["evrepo"] == EXTERNAL_NS

    def test_vocab_ensures_trailing_slash(self):
        snapshot = _make_snapshot(namespace="https://vocab.esea.education")
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["@vocab"] == "https://vocab.esea.education/"


class TestClassTerms:
    def test_external_class_mapped_with_prefix(self):
        snapshot = _make_snapshot(
            classes=[
                {
                    "id": str(EXT_CLASS_ID),
                    "identifier": "Investigation",
                    "label": "Investigation",
                    "uri": f"{EXTERNAL_NS}Investigation",
                }
            ]
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["Investigation"] == "evrepo:Investigation"

    def test_in_namespace_class_listed_with_prefix(self):
        snapshot = _make_snapshot(
            classes=[
                {
                    "id": str(CLASS_ID),
                    "identifier": "EducationLevelCodingAnnotation",
                    "label": "Education Level Coding Annotation",
                    "uri": f"{PROJECT_NS}EducationLevelCodingAnnotation",
                }
            ]
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["EducationLevelCodingAnnotation"] == "esea:EducationLevelCodingAnnotation"

    def test_external_class_without_prefix_uses_full_uri(self):
        snapshot = _make_snapshot(
            namespace_prefixes={"esea": PROJECT_NS},
            classes=[
                {
                    "id": str(EXT_CLASS_ID),
                    "identifier": "Investigation",
                    "label": "Investigation",
                    "uri": "https://unknown.org/Investigation",
                }
            ],
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["Investigation"] == "https://unknown.org/Investigation"


class TestPropertyTerms:
    def test_object_property_has_type_id(self):
        snapshot = _make_snapshot(
            properties=[
                {
                    "id": str(PROP_OBJ_ID),
                    "identifier": "educationLevel",
                    "label": "Education Level",
                    "uri": f"{PROJECT_NS}educationLevel",
                    "property_type": "object",
                    "range_scheme_id": str(SCHEME_ID),
                    "range_scheme_uri": f"{PROJECT_NS}educationLevel",
                    "range_datatype": None,
                    "range_class": None,
                    "cardinality": "single",
                    "required": False,
                }
            ]
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["educationLevel"] == {"@type": "@id"}

    def test_datatype_property_has_xsd_type(self):
        snapshot = _make_snapshot(
            properties=[
                {
                    "id": str(PROP_DT_ID),
                    "identifier": "isRetracted",
                    "label": "Is Retracted",
                    "uri": f"{PROJECT_NS}isRetracted",
                    "property_type": "datatype",
                    "range_scheme_id": None,
                    "range_scheme_uri": None,
                    "range_datatype": "xsd:boolean",
                    "range_class": None,
                    "cardinality": "single",
                    "required": False,
                }
            ]
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["isRetracted"] == {"@type": "xsd:boolean"}
        assert ctx["xsd"] == "http://www.w3.org/2001/XMLSchema#"

    def test_multiple_cardinality_has_container_set(self):
        snapshot = _make_snapshot(
            properties=[
                {
                    "id": str(PROP_MULTI_ID),
                    "identifier": "educationLevel",
                    "label": "Education Level",
                    "uri": f"{PROJECT_NS}educationLevel",
                    "property_type": "object",
                    "range_scheme_id": str(SCHEME_ID),
                    "range_scheme_uri": f"{PROJECT_NS}educationLevel",
                    "range_datatype": None,
                    "range_class": None,
                    "cardinality": "multiple",
                    "required": False,
                }
            ]
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["educationLevel"] == {"@type": "@id", "@container": "@set"}

    def test_external_property_includes_id(self):
        snapshot = _make_snapshot(
            properties=[
                {
                    "id": str(PROP_EXT_ID),
                    "identifier": "hasInvestigation",
                    "label": "Has Investigation",
                    "uri": f"{EXTERNAL_NS}hasInvestigation",
                    "property_type": "object",
                    "range_scheme_id": None,
                    "range_scheme_uri": None,
                    "range_datatype": None,
                    "range_class": f"{EXTERNAL_NS}Investigation",
                    "cardinality": "single",
                    "required": False,
                }
            ]
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["hasInvestigation"] == {
            "@id": "evrepo:hasInvestigation",
            "@type": "@id",
        }

    def test_rdf_property_no_range_in_project_ns_omitted(self):
        snapshot = _make_snapshot(
            properties=[
                {
                    "id": str(PROP_RDF_ID),
                    "identifier": "codedValue",
                    "label": "Coded Value",
                    "uri": f"{PROJECT_NS}codedValue",
                    "property_type": "rdf",
                    "range_scheme_id": None,
                    "range_scheme_uri": None,
                    "range_datatype": None,
                    "range_class": None,
                    "cardinality": "single",
                    "required": False,
                }
            ]
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert "codedValue" not in ctx

    def test_rdf_property_no_range_external_ns_has_id_only(self):
        snapshot = _make_snapshot(
            properties=[
                {
                    "id": str(PROP_RDF_ID),
                    "identifier": "codedValue",
                    "label": "Coded Value",
                    "uri": f"{EXTERNAL_NS}codedValue",
                    "property_type": "rdf",
                    "range_scheme_id": None,
                    "range_scheme_uri": None,
                    "range_datatype": None,
                    "range_class": None,
                    "cardinality": "single",
                    "required": False,
                }
            ]
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["codedValue"] == "evrepo:codedValue"


class TestCollisions:
    def test_class_collision_project_ns_wins(self):
        snapshot = _make_snapshot(
            classes=[
                {
                    "id": str(CLASS_ID),
                    "identifier": "Outcome",
                    "label": "Outcome (ESEA)",
                    "uri": f"{PROJECT_NS}Outcome",
                },
                {
                    "id": str(EXT_CLASS_ID),
                    "identifier": "Outcome",
                    "label": "Outcome (Core)",
                    "uri": f"{EXTERNAL_NS}Outcome",
                },
            ]
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        # Project-namespace class takes the short name; the external one is
        # listed under its CURIE. A full-URI key would loop rdflib's parser.
        assert ctx["Outcome"] == "esea:Outcome"
        assert ctx["evrepo:Outcome"] == "evrepo:Outcome"
        assert f"{EXTERNAL_NS}Outcome" not in ctx


class TestLongestMatchPrefix:
    def test_longer_namespace_matches_before_shorter(self):
        """When one namespace is a prefix of another, the longer one should match."""
        snapshot = _make_snapshot(
            namespace_prefixes={
                "esea": PROJECT_NS,
                "evrepo": EXTERNAL_NS,
                "evreposub": f"{EXTERNAL_NS}sub/",
            },
            classes=[
                {
                    "id": str(EXT_CLASS_ID),
                    "identifier": "Widget",
                    "label": "Widget",
                    "uri": f"{EXTERNAL_NS}sub/Widget",
                },
                {
                    "id": str(CLASS_ID),
                    "identifier": "Investigation",
                    "label": "Investigation",
                    "uri": f"{EXTERNAL_NS}Investigation",
                },
            ],
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["Widget"] == "evreposub:Widget"
        assert ctx["Investigation"] == "evrepo:Investigation"


class TestEmptyPrefixFiltering:
    def test_empty_prefix_not_emitted(self):
        """An empty-string prefix key should not appear in the context."""
        snapshot = _make_snapshot(
            namespace_prefixes={
                "": "https://example.org/default/",
                "esea": PROJECT_NS,
            },
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert "" not in ctx
        assert "esea" in ctx


class TestEmptySnapshot:
    def test_no_classes_no_properties(self):
        snapshot = _make_snapshot(classes=[], properties=[])
        result = ContextGenerationService().generate(snapshot)
        ctx = result["@context"]
        assert "@vocab" in ctx
        assert "esea" in ctx


class TestNamedIndividuals:
    """Named individuals should appear as simple URI aliases in the context."""

    def test_named_individuals_emitted(self):
        from taxonomy_builder.schemas.snapshot import SnapshotNamedIndividual

        snapshot = _make_snapshot()
        snapshot.named_individuals = [
            SnapshotNamedIndividual(uri=f"{EXTERNAL_NS}coded", label="Coded"),
            SnapshotNamedIndividual(uri=f"{EXTERNAL_NS}notApplicable", label="Not Applicable"),
            SnapshotNamedIndividual(uri=f"{EXTERNAL_NS}notReported", label="Not Reported"),
        ]
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["coded"] == "evrepo:coded"
        assert ctx["notApplicable"] == "evrepo:notApplicable"
        assert ctx["notReported"] == "evrepo:notReported"

    def test_named_individual_no_collision_with_class(self):
        """If a named individual's local name collides with a class, skip it."""
        from taxonomy_builder.schemas.snapshot import SnapshotNamedIndividual

        snapshot = _make_snapshot(
            classes=[
                {
                    "id": str(CLASS_ID),
                    "identifier": "Coded",
                    "label": "Coded",
                    "uri": f"{PROJECT_NS}Coded",
                }
            ]
        )
        snapshot.named_individuals = [
            SnapshotNamedIndividual(uri=f"{EXTERNAL_NS}Coded", label="Coded"),
        ]
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        # Class wins — individual skipped
        assert ctx["Coded"] == "esea:Coded"


class TestInNamespaceClassesExplicit:
    """Classes in the project namespace should still get explicit context entries.

    Even when @vocab covers the project namespace, consumers need explicit
    class terms so JSON-LD processors can resolve bare type names like
    "EducationLevelCodingAnnotation" without relying on @vocab — particularly
    when the consuming context uses a different @vocab.
    """

    def test_in_namespace_class_gets_explicit_entry(self):
        """A class in the project namespace should appear with an explicit
        prefixed mapping, not be silently omitted."""
        snapshot = _make_snapshot(
            classes=[
                {
                    "id": str(CLASS_ID),
                    "identifier": "EducationLevelCodingAnnotation",
                    "label": "Education Level Coding Annotation",
                    "uri": f"{PROJECT_NS}EducationLevelCodingAnnotation",
                }
            ]
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert "EducationLevelCodingAnnotation" in ctx
        assert ctx["EducationLevelCodingAnnotation"] == "esea:EducationLevelCodingAnnotation"

    def test_multiple_in_namespace_classes_all_listed(self):
        """All project-namespace classes should get entries, not just external ones."""
        classes = [
            {
                "id": "01965a00-0000-7000-8000-b00000000010",
                "identifier": name,
                "label": name,
                "uri": f"{PROJECT_NS}{name}",
            }
            for name in [
                "EducationLevelCodingAnnotation",
                "DocumentTypeCodingAnnotation",
                "SettingCodingAnnotation",
            ]
        ]
        snapshot = _make_snapshot(classes=classes)
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        for name in [
            "EducationLevelCodingAnnotation",
            "DocumentTypeCodingAnnotation",
            "SettingCodingAnnotation",
        ]:
            assert name in ctx, f"{name} missing from context"
            assert ctx[name] == f"esea:{name}"


class TestRdfPropertyWithDatatype:
    """rdf:Property with a range_datatype should emit @type, not collapse to
    a bare string alias or be omitted entirely.

    The generator currently handles rdf:Property with no range (correctly
    emitting just @id for external, omitting for in-namespace), but when
    a range_datatype IS present it should be honoured.
    """

    def test_rdf_property_with_datatype_external_ns(self):
        """An external rdf:Property with range_datatype should include @type."""
        snapshot = _make_snapshot(
            properties=[
                {
                    "id": str(PROP_RDF_ID),
                    "identifier": "supportingText",
                    "label": "Supporting Text",
                    "uri": f"{EXTERNAL_NS}supportingText",
                    "property_type": "rdf",
                    "range_scheme_id": None,
                    "range_scheme_uri": None,
                    "range_datatype": "xsd:string",
                    "range_class": None,
                    "cardinality": "single",
                    "required": False,
                }
            ]
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["supportingText"] == {
            "@id": "evrepo:supportingText",
            "@type": "xsd:string",
        }

    def test_rdf_property_with_datatype_in_namespace(self):
        """An in-namespace rdf:Property with range_datatype should emit @type."""
        snapshot = _make_snapshot(
            properties=[
                {
                    "id": str(PROP_RDF_ID),
                    "identifier": "dataSource",
                    "label": "Data Source",
                    "uri": f"{PROJECT_NS}dataSource",
                    "property_type": "rdf",
                    "range_scheme_id": None,
                    "range_scheme_uri": None,
                    "range_datatype": "xsd:string",
                    "range_class": None,
                    "cardinality": "single",
                    "required": False,
                }
            ]
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert "dataSource" in ctx, "in-namespace rdf:Property with datatype should not be omitted"
        assert ctx["dataSource"] == {"@type": "xsd:string"}


GN_NS = "http://www.geonames.org/ontology#"
DCT_NS = "http://purl.org/dc/terms/"
DESTINY_NS = "https://vocab.destiny-evidence.org/"
SHARED_PREFIXES = {
    **DEFAULT_PREFIXES,
    "gn": GN_NS,
    "dct": DCT_NS,
    "dsny": DESTINY_NS,
}


def _string_prop(prop_id: int, uri: str, property_type: str = "datatype") -> dict:
    return {
        "id": f"01965a00-0000-7000-8000-c0000000000{prop_id}",
        "identifier": uri.rsplit("#", 1)[-1].rsplit("/", 1)[-1],
        "label": "x",
        "uri": uri,
        "property_type": property_type,
        "range_datatype": "xsd:string" if property_type == "datatype" else None,
        "cardinality": "single",
        "required": False,
    }


def _context_both_orders(props: list[dict], namespace: str) -> list[dict]:
    return [
        ContextGenerationService().generate(
            _make_snapshot(
                properties=ordering,
                namespace=namespace,
                namespace_prefixes=SHARED_PREFIXES,
            )
        )["@context"]
        for ordering in (props, list(reversed(props)))
    ]


class TestSharedLocalNames:
    """Terms from different vocabularies sharing a local name (#268)."""

    def test_project_term_keeps_bare_name(self):
        props = [_string_prop(1, f"{EXTERNAL_NS}name"), _string_prop(2, f"{GN_NS}name")]
        first, second = _context_both_orders(props, namespace=EXTERNAL_NS)

        assert first == second
        assert first["name"] == {"@type": "xsd:string"}
        assert first["gn:name"] == {"@id": "gn:name", "@type": "xsd:string"}

    def test_priority_namespace_beats_other_external(self):
        # gn:name is older, but evrepo outranks other external vocabularies.
        props = [_string_prop(1, f"{GN_NS}name"), _string_prop(2, f"{EXTERNAL_NS}name")]
        first, second = _context_both_orders(props, namespace=DESTINY_NS)

        assert first == second
        assert first["name"] == {"@id": "evrepo:name", "@type": "xsd:string"}
        assert first["evrepo:name"] == {"@id": "evrepo:name", "@type": "xsd:string"}
        assert first["gn:name"] == {"@id": "gn:name", "@type": "xsd:string"}

    def test_oldest_external_term_wins_tie(self):
        props = [_string_prop(1, f"{DCT_NS}title"), _string_prop(2, f"{GN_NS}title")]
        first, second = _context_both_orders(props, namespace=DESTINY_NS)

        assert first == second
        assert first["title"] == {"@id": "dct:title", "@type": "xsd:string"}
        assert first["gn:title"] == {"@id": "gn:title", "@type": "xsd:string"}

    def test_untyped_project_term_still_reserves_bare_name(self):
        """A project term resolved via @vocab must not be shadowed by an external one."""
        props = [
            _string_prop(1, f"{DESTINY_NS}label", property_type="rdf"),
            _string_prop(2, f"{GN_NS}label"),
        ]
        first, second = _context_both_orders(props, namespace=DESTINY_NS)

        assert first == second
        assert "label" not in first
        assert first["gn:label"] == {"@id": "gn:label", "@type": "xsd:string"}

    def test_payload_expands_through_generated_context(self):
        props = [_string_prop(1, f"{EXTERNAL_NS}name"), _string_prop(2, f"{GN_NS}name")]
        ctx = _context_both_orders(props, namespace=DESTINY_NS)[0]
        doc = {"@context": ctx, "@id": "http://example.org/x", "name": "a", "gn:name": "b"}

        g = Graph().parse(data=json.dumps(doc), format="json-ld")
        assert set(g.predicate_objects(URIRef("http://example.org/x"))) == {
            (URIRef(f"{EXTERNAL_NS}name"), Literal("a", datatype=XSD.string)),
            (URIRef(f"{GN_NS}name"), Literal("b", datatype=XSD.string)),
        }

    def test_context_with_clashes_parses_with_rdflib(self):
        """rdflib, used by destiny-repository projection, recursed forever on
        full-URI keys pointing at CURIEs."""
        snapshot = _make_snapshot(
            classes=[
                {"id": str(CLASS_ID), "identifier": "Outcome", "label": "Outcome",
                 "uri": f"{PROJECT_NS}Outcome"},
                {"id": str(EXT_CLASS_ID), "identifier": "Outcome", "label": "Outcome",
                 "uri": f"{EXTERNAL_NS}Outcome"},
                {"id": "01965a00-0000-7000-8000-b00000000003", "identifier": "Outcome",
                 "label": "Outcome", "uri": "http://unbound.example/Outcome"},
            ],
            properties=[_string_prop(1, f"{EXTERNAL_NS}name"), _string_prop(2, f"{GN_NS}name"),
                        _string_prop(3, "http://unbound.example/name")],
            namespace_prefixes=SHARED_PREFIXES,
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        doc = {
            "@context": ctx,
            "@id": "http://example.org/x",
            "@type": ["Outcome", "evrepo:Outcome"],
            "name": "a",
            "gn:name": "b",
        }

        g = Graph().parse(data=json.dumps(doc), format="json-ld")
        subject = URIRef("http://example.org/x")
        assert set(g.objects(subject, RDF.type)) == {
            URIRef(f"{PROJECT_NS}Outcome"),
            URIRef(f"{EXTERNAL_NS}Outcome"),
        }
        assert (subject, URIRef(f"{GN_NS}name"), Literal("b", datatype=XSD.string)) in g
