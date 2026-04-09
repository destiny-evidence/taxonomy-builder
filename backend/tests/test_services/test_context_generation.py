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


DEFAULT_SCHEME = {
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


def _make_snapshot(
    *,
    classes=None,
    properties=None,
    concept_schemes=None,
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
        "concept_schemes": concept_schemes if concept_schemes is not None else [DEFAULT_SCHEME],
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
        # Project-namespace class takes the short name.
        # External class gets the full URI as key since "Outcome" is taken.
        assert ctx["Outcome"] == "esea:Outcome"
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


THEME_SCHEME_ID = UUID("01965a00-0000-7000-8000-000000000002")


def _theme_scheme(*, concept_type_uris=None):
    """Build an EducationThemeScheme with a concept that has concept_type_uris."""
    return {
        "id": str(THEME_SCHEME_ID),
        "title": "Education Theme",
        "uri": f"{PROJECT_NS}EducationThemeScheme",
        "concepts": [
            {
                "id": "01965a00-0000-7000-8000-000000000098",
                "pref_label": "Literacy and Reading Interventions",
                "identifier": "C00074",
                "uri": f"{PROJECT_NS}EducationThemeScheme/C00074",
                "broader_ids": [],
                "related_ids": [],
                "alt_labels": [],
                "concept_type_uris": concept_type_uris or [f"{PROJECT_NS}EducationThemeConcept"],
            }
        ],
    }


def _annotation_class(*, identifier="EducationThemeCodingAnnotation", value_uri=None):
    """Build a CodingAnnotation class with an allValuesFrom restriction."""
    return {
        "id": str(CLASS_ID),
        "identifier": identifier,
        "label": identifier.replace("CodingAnnotation", " Coding Annotation"),
        "uri": f"{PROJECT_NS}{identifier}",
        "restrictions": [
            {
                "on_property_uri": f"{EXTERNAL_NS}codedValue",
                "restriction_type": "allValuesFrom",
                "value_uri": value_uri or f"{PROJECT_NS}EducationThemeConcept",
            }
        ],
    }


class TestTypeScopedPrefixRedefinition:
    """Classes with allValuesFrom restrictions linking to a concept scheme
    should get type-scoped prefix redefinitions in the context.

    This enables pyld to expand esea:C00074 → esea:EducationThemeScheme/C00074
    when the codedValue appears inside a typed annotation node.
    """

    def test_annotation_class_gets_scoped_prefix(self):
        snapshot = _make_snapshot(
            concept_schemes=[_theme_scheme()],
            classes=[_annotation_class()],
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["EducationThemeCodingAnnotation"] == {
            "@id": "esea:EducationThemeCodingAnnotation",
            "@context": {"esea": f"{PROJECT_NS}EducationThemeScheme/"},
        }

    def test_class_without_restriction_stays_simple(self):
        """A class with no restrictions should not get a scoped context."""
        snapshot = _make_snapshot(
            concept_schemes=[_theme_scheme()],
            classes=[
                {
                    "id": str(CLASS_ID),
                    "identifier": "Investigation",
                    "label": "Investigation",
                    "uri": f"{EXTERNAL_NS}Investigation",
                }
            ],
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["Investigation"] == "evrepo:Investigation"

    def test_restriction_not_matching_any_scheme(self):
        """allValuesFrom a type that doesn't appear in any scheme's concepts
        should not produce a scoped context."""
        snapshot = _make_snapshot(
            concept_schemes=[_theme_scheme()],
            classes=[
                _annotation_class(value_uri=f"{PROJECT_NS}UnknownConcept"),
            ],
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        # Falls back to simple mapping
        assert ctx["EducationThemeCodingAnnotation"] == "esea:EducationThemeCodingAnnotation"

    def test_multiple_annotation_types_each_get_own_scheme(self):
        """Each annotation type should get a scoped prefix for its own scheme."""
        doc_scheme_id = UUID("01965a00-0000-7000-8000-000000000003")
        snapshot = _make_snapshot(
            concept_schemes=[
                _theme_scheme(),
                {
                    "id": str(doc_scheme_id),
                    "title": "Document Type",
                    "uri": f"{PROJECT_NS}DocumentTypeScheme",
                    "concepts": [
                        {
                            "id": "01965a00-0000-7000-8000-000000000097",
                            "pref_label": "RCT",
                            "identifier": "C00008",
                            "uri": f"{PROJECT_NS}DocumentTypeScheme/C00008",
                            "broader_ids": [],
                            "related_ids": [],
                            "alt_labels": [],
                            "concept_type_uris": [f"{PROJECT_NS}DocumentTypeConcept"],
                        }
                    ],
                },
            ],
            classes=[
                _annotation_class(),
                {
                    "id": str(EXT_CLASS_ID),
                    "identifier": "DocumentTypeCodingAnnotation",
                    "label": "Document Type Coding Annotation",
                    "uri": f"{PROJECT_NS}DocumentTypeCodingAnnotation",
                    "restrictions": [
                        {
                            "on_property_uri": f"{EXTERNAL_NS}codedValue",
                            "restriction_type": "allValuesFrom",
                            "value_uri": f"{PROJECT_NS}DocumentTypeConcept",
                        }
                    ],
                },
            ],
        )
        ctx = ContextGenerationService().generate(snapshot)["@context"]
        assert ctx["EducationThemeCodingAnnotation"] == {
            "@id": "esea:EducationThemeCodingAnnotation",
            "@context": {"esea": f"{PROJECT_NS}EducationThemeScheme/"},
        }
        assert ctx["DocumentTypeCodingAnnotation"] == {
            "@id": "esea:DocumentTypeCodingAnnotation",
            "@context": {"esea": f"{PROJECT_NS}DocumentTypeScheme/"},
        }
