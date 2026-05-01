"""Tests for MCP output formatters."""

from taxonomy_builder.mcp.formatters import (
    format_concept,
    format_concept_brief,
    format_feedback,
    format_feedback_brief,
    format_project,
    format_scheme,
    format_tree,
)


class FakeScheme:
    def __init__(self, uri="http://example.org/concepts"):
        self.uri = uri


class FakeConcept:
    def __init__(
        self,
        *,
        id="019abc",
        identifier="TST000001",
        pref_label="Dogs",
        definition=None,
        scope_note=None,
        alt_labels=None,
        broader=None,
        narrower=None,
        related=None,
        scheme=None,
    ):
        self.id = id
        self.identifier = identifier
        self.pref_label = pref_label
        self.definition = definition
        self.scope_note = scope_note
        self.alt_labels = alt_labels or []
        self.broader = broader or []
        self.narrower = narrower or []
        self.related = related or []
        self.scheme = scheme or FakeScheme()

    @property
    def uri(self):
        base = self.scheme.uri if self.scheme and self.scheme.uri else "http://example.org/concepts"
        return f"{base.rstrip('/')}/{self.identifier}"


class FakeProject:
    def __init__(
        self,
        *,
        id="019proj",
        name="My Project",
        description="A test project",
        namespace="https://example.org/vocab/",
        identifier_prefix="TST",
        schemes=None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.namespace = namespace
        self.identifier_prefix = identifier_prefix
        self.schemes = schemes or []


class TestFormatProject:
    def test_basic(self):
        project = FakeProject()
        result = format_project(project)
        assert "My Project" in result
        assert "019proj" in result
        assert "https://example.org/vocab/" in result
        assert "A test project" in result

    def test_no_description(self):
        project = FakeProject(description=None)
        result = format_project(project)
        assert "My Project" in result


class TestFormatScheme:
    def test_basic(self):
        scheme = type("S", (), {
            "id": "019scheme",
            "title": "Evidence Types",
            "description": "Types of evidence",
            "uri": "http://example.org/evidence",
            "project_id": "019proj",
            "concepts": [],
        })()
        result = format_scheme(scheme)
        assert "Evidence Types" in result
        assert "019scheme" in result

    def test_with_concepts(self):
        concepts = [FakeConcept(pref_label=f"Concept {i}") for i in range(5)]
        scheme = type("S", (), {
            "id": "019scheme",
            "title": "Test",
            "description": None,
            "uri": "http://example.org/test",
            "project_id": "019proj",
            "concepts": concepts,
        })()
        result = format_scheme(scheme)
        assert "5 concepts" in result


class TestFormatConcept:
    def test_minimal(self):
        concept = FakeConcept()
        result = format_concept(concept)
        assert "Dogs" in result
        assert "019abc" in result
        assert "TST000001" in result

    def test_full(self):
        parent = FakeConcept(id="019parent", pref_label="Animals")
        child = FakeConcept(id="019child", pref_label="Puppies")
        related = FakeConcept(id="019related", pref_label="Cats")
        concept = FakeConcept(
            definition="Domesticated canines",
            scope_note="All breeds",
            alt_labels=["Canines", "Domestic dogs"],
            broader=[parent],
            narrower=[child],
            related=[related],
        )
        result = format_concept(concept)
        assert "Domesticated canines" in result
        assert "All breeds" in result
        assert "Canines" in result
        assert "Domestic dogs" in result
        assert "Animals" in result
        assert "Puppies" in result
        assert "Cats" in result


class TestFormatConceptBrief:
    def test_basic(self):
        concept = FakeConcept(pref_label="Dogs", definition="Good boys")
        result = format_concept_brief(concept)
        assert "Dogs" in result
        assert "019abc" in result


class TestFormatTree:
    def test_empty(self):
        result = format_tree([])
        assert result == "(empty scheme)"

    def test_flat(self):
        tree = [
            {"id": "1", "pref_label": "Animals", "identifier": "TST000001", "narrower": []},
            {"id": "2", "pref_label": "Plants", "identifier": "TST000002", "narrower": []},
        ]
        result = format_tree(tree)
        assert "Animals" in result
        assert "Plants" in result
        # Should not be indented (root level)
        lines = result.strip().split("\n")
        assert not lines[0].startswith(" ")
        assert not lines[1].startswith(" ")

    def test_nested(self):
        tree = [
            {
                "id": "1",
                "pref_label": "Animals",
                "identifier": "TST000001",
                "narrower": [
                    {
                        "id": "2",
                        "pref_label": "Dogs",
                        "identifier": "TST000002",
                        "narrower": [
                            {
                                "id": "3",
                                "pref_label": "Poodles",
                                "identifier": "TST000003",
                                "narrower": [],
                            }
                        ],
                    },
                    {
                        "id": "4",
                        "pref_label": "Cats",
                        "identifier": "TST000004",
                        "narrower": [],
                    },
                ],
            }
        ]
        result = format_tree(tree)
        lines = result.strip().split("\n")
        # Root not indented
        assert lines[0].startswith("Animals")
        # Children indented 2 spaces
        assert lines[1].startswith("  Dogs")
        # Grandchildren indented 4 spaces
        assert lines[2].startswith("    Poodles")
        assert lines[3].startswith("  Cats")


class FakeFeedback:
    def __init__(
        self,
        *,
        id="019fb",
        status="open",
        entity_type="concept",
        entity_label="Dogs",
        feedback_type="unclear_definition",
        content="The definition is vague",
        author_name="Reviewer User",
        created_at="2026-04-01",
        response_content=None,
        responded_by_name=None,
    ):
        self.id = id
        self.status = status
        self.entity_type = entity_type
        self.entity_label = entity_label
        self.feedback_type = feedback_type
        self.content = content
        self.author_name = author_name
        self.created_at = created_at
        self.response_content = response_content
        self.responded_by_name = responded_by_name


class TestFormatFeedback:
    def test_basic(self):
        fb = FakeFeedback()
        result = format_feedback(fb)
        assert "[open]" in result
        assert "unclear_definition" in result
        assert "Dogs" in result
        assert "The definition is vague" in result
        assert "Reviewer User" in result
        assert "019fb" in result

    def test_with_response(self):
        fb = FakeFeedback(
            status="responded",
            response_content="We'll clarify this",
            responded_by_name="Manager User",
        )
        result = format_feedback(fb)
        assert "[responded]" in result
        assert "We'll clarify this" in result

    def test_no_response(self):
        fb = FakeFeedback()
        result = format_feedback(fb)
        assert "(none)" in result


class TestFormatFeedbackBrief:
    def test_basic(self):
        fb = FakeFeedback()
        result = format_feedback_brief(fb)
        assert "[open]" in result
        assert "concept" in result
        assert "Dogs" in result
        assert "019fb" in result
