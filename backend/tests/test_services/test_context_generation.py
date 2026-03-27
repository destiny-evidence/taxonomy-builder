"""Tests for JSON-LD @context generation from vocabulary snapshots."""

from uuid import UUID

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
        snapshot = _make_snapshot(classes=[
            {
                "id": str(EXT_CLASS_ID),
                "identifier": "Investigation",
                "label": "Investigation",
                "uri": f"{EXTERNAL_NS}Investigation",
            }
        ])
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["Investigation"] == "evrepo:Investigation"

    def test_in_namespace_class_not_listed(self):
        snapshot = _make_snapshot(classes=[
            {
                "id": str(CLASS_ID),
                "identifier": "EducationLevelCodingAnnotation",
                "label": "Education Level Coding Annotation",
                "uri": f"{PROJECT_NS}EducationLevelCodingAnnotation",
            }
        ])
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert "EducationLevelCodingAnnotation" not in ctx

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
        snapshot = _make_snapshot(properties=[
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
        ])
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["educationLevel"] == {"@type": "@id"}

    def test_datatype_property_has_xsd_type(self):
        snapshot = _make_snapshot(properties=[
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
        ])
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["isRetracted"] == {"@type": "xsd:boolean"}
        assert ctx["xsd"] == "http://www.w3.org/2001/XMLSchema#"

    def test_multiple_cardinality_has_container_set(self):
        snapshot = _make_snapshot(properties=[
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
        ])
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["educationLevel"] == {"@type": "@id", "@container": "@set"}

    def test_external_property_includes_id(self):
        snapshot = _make_snapshot(properties=[
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
        ])
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["hasInvestigation"] == {
            "@id": "evrepo:hasInvestigation",
            "@type": "@id",
        }

    def test_rdf_property_no_range_in_project_ns_omitted(self):
        snapshot = _make_snapshot(properties=[
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
        ])
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert "codedValue" not in ctx

    def test_rdf_property_no_range_external_ns_has_id_only(self):
        snapshot = _make_snapshot(properties=[
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
        ])
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["codedValue"] == "evrepo:codedValue"


class TestCollisions:
    def test_class_collision_project_ns_wins(self):
        snapshot = _make_snapshot(classes=[
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
        ])
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        # Project-namespace class is resolved via @vocab, not explicitly listed.
        # External class gets the full URI as key since "Outcome" is taken.
        assert "Outcome" not in ctx
        assert ctx[f"{EXTERNAL_NS}Outcome"] == "evrepo:Outcome"


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
