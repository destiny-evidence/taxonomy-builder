"""Integration tests for MCP tools.

These tests call the tool functions directly with a real database session,
bypassing the MCP transport layer. This validates the business logic and
formatting of each tool.
"""

from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.database import db_manager
from taxonomy_builder.mcp import tools
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.user import User


class FakeContext:
    """Minimal fake MCP Context for tool testing."""

    def __init__(self, user_id: UUID | None = None):
        self.client_id = str(user_id) if user_id else None


@pytest.fixture
def ctx(test_user: User) -> FakeContext:
    return FakeContext(user_id=test_user.id)


@pytest.fixture
def anon_ctx() -> FakeContext:
    return FakeContext()


@pytest.fixture(autouse=True)
def _patch_db_manager(db_session: AsyncSession, monkeypatch):
    """Patch db_manager.session to use the test session.

    This ensures tools use the test transaction (which gets rolled back),
    rather than creating their own sessions against the real database.
    """
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def fake_session():
        yield db_session
        # Don't commit — the test fixture handles rollback

    monkeypatch.setattr(db_manager, "session", fake_session)


# --- Exploring tools ---


class TestListProjects:
    async def test_empty(self, ctx):
        result = await tools.list_projects(ctx)
        assert result == "No projects found."

    async def test_with_projects(self, ctx, project: Project):
        result = await tools.list_projects(ctx)
        assert project.name in result
        assert str(project.id) in result


class TestCreateProject:
    async def test_basic(self, ctx):
        result = await tools.create_project(
            ctx,
            name="MCP Test Project",
            namespace="https://example.org/mcp-test/",
            identifier_prefix="MCP",
        )
        assert "MCP Test Project" in result
        assert "Created" in result

    async def test_with_description(self, ctx):
        result = await tools.create_project(
            ctx,
            name="Described Project",
            namespace="https://example.org/described/",
            identifier_prefix="DSC",
            description="A project with a description",
        )
        assert "Described Project" in result
        assert "A project with a description" in result


class TestListSchemes:
    async def test_empty(self, ctx, project: Project):
        result = await tools.list_schemes(ctx, str(project.id))
        assert "No schemes found" in result

    async def test_with_schemes(self, ctx, scheme: ConceptScheme, project: Project):
        result = await tools.list_schemes(ctx, str(project.id))
        assert scheme.title in result


class TestGetScheme:
    async def test_basic(self, ctx, scheme: ConceptScheme):
        result = await tools.get_scheme(ctx, str(scheme.id))
        assert scheme.title in result
        assert str(scheme.id) in result

    async def test_not_found(self, ctx):
        with pytest.raises(Exception):
            await tools.get_scheme(ctx, str(uuid4()))


class TestGetConceptTree:
    async def test_empty_scheme(self, ctx, scheme: ConceptScheme):
        result = await tools.get_concept_tree(ctx, str(scheme.id))
        assert "empty" in result.lower()

    async def test_with_hierarchy(
        self, ctx, db_session: AsyncSession, scheme: ConceptScheme
    ):
        parent = Concept(
            scheme_id=scheme.id, pref_label="Animals", identifier="c1"
        )
        child = Concept(
            scheme_id=scheme.id, pref_label="Dogs", identifier="c2"
        )
        db_session.add_all([parent, child])
        await db_session.flush()

        from taxonomy_builder.models.concept_broader import ConceptBroader

        db_session.add(
            ConceptBroader(concept_id=child.id, broader_concept_id=parent.id)
        )
        await db_session.flush()

        result = await tools.get_concept_tree(ctx, str(scheme.id))
        assert "Animals" in result
        assert "Dogs" in result
        # Dogs should be indented under Animals
        lines = result.strip().split("\n")
        animals_line = next(l for l in lines if "Animals" in l)
        dogs_line = next(l for l in lines if "Dogs" in l)
        assert not animals_line.startswith(" ")
        assert dogs_line.startswith("  ")


class TestSearchConcepts:
    async def test_finds_match(
        self, ctx, db_session: AsyncSession, scheme: ConceptScheme
    ):
        db_session.add(
            Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="c1")
        )
        await db_session.flush()

        result = await tools.search_concepts(ctx, "dog", scheme_id=str(scheme.id))
        assert "Dogs" in result
        assert "Found 1" in result

    async def test_no_match(self, ctx, scheme: ConceptScheme):
        result = await tools.search_concepts(ctx, "zebra", scheme_id=str(scheme.id))
        assert "No concepts matching" in result

    async def test_project_wide(
        self, ctx, db_session: AsyncSession, project: Project,
        scheme: ConceptScheme, scheme2: ConceptScheme,
    ):
        db_session.add(Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="s1"))
        db_session.add(Concept(scheme_id=scheme2.id, pref_label="Dog food", identifier="s2"))
        await db_session.flush()

        result = await tools.search_concepts(ctx, "dog", project_id=str(project.id))
        assert "Dogs" in result
        assert "Dog food" in result
        assert "Found 2" in result

    async def test_requires_scope(self, ctx):
        result = await tools.search_concepts(ctx, "anything")
        assert "Provide either" in result


class TestGetConcept:
    async def test_basic(self, ctx, concept: Concept):
        result = await tools.get_concept(ctx, str(concept.id))
        assert concept.pref_label in result
        assert str(concept.id) in result

    async def test_not_found(self, ctx):
        with pytest.raises(Exception):
            await tools.get_concept(ctx, str(uuid4()))


# --- Building tools ---


class TestCreateScheme:
    async def test_basic(self, ctx, project: Project):
        result = await tools.create_scheme(
            ctx, str(project.id), "New Scheme", description="A new scheme"
        )
        assert "New Scheme" in result
        assert "Created" in result

    async def test_with_uri(self, ctx, project: Project):
        result = await tools.create_scheme(
            ctx,
            str(project.id),
            "URI Scheme",
            uri="http://example.org/vocab/test",
        )
        assert "URI Scheme" in result


class TestCreateConcept:
    async def test_basic(self, ctx, scheme: ConceptScheme):
        result = await tools.create_concept(ctx, str(scheme.id), "Dogs")
        assert "Dogs" in result
        assert "Created" in result

    async def test_with_broader(
        self, ctx, db_session: AsyncSession, scheme: ConceptScheme
    ):
        parent = Concept(
            scheme_id=scheme.id, pref_label="Animals", identifier="c-parent"
        )
        db_session.add(parent)
        await db_session.flush()

        result = await tools.create_concept(
            ctx,
            str(scheme.id),
            "Dogs",
            definition="Good boys",
            broader_concept_id=str(parent.id),
        )
        assert "Dogs" in result
        assert "Animals" in result  # broader should show


class TestCreateConceptsBatch:
    async def test_basic(self, ctx, scheme: ConceptScheme):
        result = await tools.create_concepts_batch(
            ctx,
            str(scheme.id),
            [
                {"pref_label": "Animals"},
                {"pref_label": "Plants"},
            ],
        )
        assert "Created 2" in result
        assert "Animals" in result
        assert "Plants" in result

    async def test_with_batch_references(self, ctx, scheme: ConceptScheme):
        result = await tools.create_concepts_batch(
            ctx,
            str(scheme.id),
            [
                {"pref_label": "Animals"},
                {"pref_label": "Dogs", "broader_concept_id": "#0"},
            ],
        )
        assert "Created 2" in result
        assert "Dogs" in result


class TestSetBroader:
    async def test_add(self, ctx, db_session: AsyncSession, scheme: ConceptScheme):
        parent = Concept(
            scheme_id=scheme.id, pref_label="Animals", identifier="p1"
        )
        child = Concept(
            scheme_id=scheme.id, pref_label="Dogs", identifier="c1"
        )
        db_session.add_all([parent, child])
        await db_session.flush()

        result = await tools.set_broader(
            ctx, str(child.id), str(parent.id), "add"
        )
        assert "Dogs" in result
        assert "Animals" in result

    async def test_remove(
        self, ctx, db_session: AsyncSession, scheme: ConceptScheme
    ):
        from taxonomy_builder.models.concept_broader import ConceptBroader

        parent = Concept(
            scheme_id=scheme.id, pref_label="Animals", identifier="p1"
        )
        child = Concept(
            scheme_id=scheme.id, pref_label="Dogs", identifier="c1"
        )
        db_session.add_all([parent, child])
        await db_session.flush()
        db_session.add(
            ConceptBroader(concept_id=child.id, broader_concept_id=parent.id)
        )
        await db_session.flush()

        result = await tools.set_broader(
            ctx, str(child.id), str(parent.id), "remove"
        )
        assert "Dogs" in result

    async def test_invalid_action(
        self, ctx, db_session: AsyncSession, scheme: ConceptScheme
    ):
        c = Concept(scheme_id=scheme.id, pref_label="X", identifier="x1")
        db_session.add(c)
        await db_session.flush()
        result = await tools.set_broader(ctx, str(c.id), str(c.id), "invalid")
        assert "Invalid action" in result


class TestMoveConcept:
    async def test_reparent(
        self, ctx, db_session: AsyncSession, scheme: ConceptScheme
    ):
        from taxonomy_builder.models.concept_broader import ConceptBroader

        parent1 = Concept(scheme_id=scheme.id, pref_label="Animals", identifier="m1")
        parent2 = Concept(scheme_id=scheme.id, pref_label="Pets", identifier="m2")
        child = Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="m3")
        db_session.add_all([parent1, parent2, child])
        await db_session.flush()
        db_session.add(ConceptBroader(concept_id=child.id, broader_concept_id=parent1.id))
        await db_session.flush()

        result = await tools.move_concept(
            ctx, str(child.id),
            new_parent_id=str(parent2.id),
            previous_parent_id=str(parent1.id),
        )
        assert "Dogs" in result
        assert "Pets" in result

    async def test_move_to_root(
        self, ctx, db_session: AsyncSession, scheme: ConceptScheme
    ):
        from taxonomy_builder.models.concept_broader import ConceptBroader

        parent = Concept(scheme_id=scheme.id, pref_label="Animals", identifier="mr1")
        child = Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="mr2")
        db_session.add_all([parent, child])
        await db_session.flush()
        db_session.add(ConceptBroader(concept_id=child.id, broader_concept_id=parent.id))
        await db_session.flush()

        result = await tools.move_concept(
            ctx, str(child.id),
            previous_parent_id=str(parent.id),
        )
        assert "Dogs" in result
        assert "Moved" in result


# --- Refining tools ---


class TestUpdateScheme:
    async def test_update_title(self, ctx, scheme: ConceptScheme):
        result = await tools.update_scheme(ctx, str(scheme.id), title="New Title")
        assert "New Title" in result
        assert "Updated" in result

    async def test_update_description(self, ctx, scheme: ConceptScheme):
        result = await tools.update_scheme(
            ctx, str(scheme.id), description="New description"
        )
        assert "New description" in result


class TestUpdateConcept:
    async def test_update_label(self, ctx, concept: Concept):
        result = await tools.update_concept(
            ctx, str(concept.id), pref_label="Updated Label"
        )
        assert "Updated Label" in result
        assert "Updated" in result

    async def test_update_definition(self, ctx, concept: Concept):
        result = await tools.update_concept(
            ctx, str(concept.id), definition="A new definition"
        )
        assert "A new definition" in result


class TestUpdateConceptsBatch:
    async def test_basic(
        self, ctx, db_session: AsyncSession, scheme: ConceptScheme
    ):
        c1 = Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="b1")
        c2 = Concept(scheme_id=scheme.id, pref_label="Cats", identifier="b2")
        db_session.add_all([c1, c2])
        await db_session.flush()

        result = await tools.update_concepts_batch(
            ctx,
            [
                {"concept_id": str(c1.id), "definition": "Canines"},
                {"concept_id": str(c2.id), "definition": "Felines"},
            ],
        )
        assert "Updated 2" in result


class TestSetRelated:
    async def test_add(self, ctx, db_session: AsyncSession, scheme: ConceptScheme):
        c1 = Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="r1")
        c2 = Concept(scheme_id=scheme.id, pref_label="Cats", identifier="r2")
        db_session.add_all([c1, c2])
        await db_session.flush()

        result = await tools.set_related(
            ctx, str(c1.id), str(c2.id), "add"
        )
        assert "Dogs" in result
        assert "Cats" in result


# --- Quality & History tools ---


class TestCheckQuality:
    async def test_empty_scheme(self, ctx, scheme: ConceptScheme):
        result = await tools.check_quality(ctx, str(scheme.id))
        assert "no concepts" in result.lower()

    async def test_missing_definitions(
        self, ctx, db_session: AsyncSession, scheme: ConceptScheme
    ):
        db_session.add(
            Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="q1")
        )
        db_session.add(
            Concept(
                scheme_id=scheme.id,
                pref_label="Cats",
                identifier="q2",
                definition="Felines",
            )
        )
        await db_session.flush()

        result = await tools.check_quality(ctx, str(scheme.id))
        assert "Missing definitions" in result
        assert "Dogs" in result

    async def test_duplicate_labels(
        self, ctx, db_session: AsyncSession, scheme: ConceptScheme
    ):
        db_session.add(
            Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="d1")
        )
        db_session.add(
            Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="d2")
        )
        await db_session.flush()

        result = await tools.check_quality(ctx, str(scheme.id))
        assert "Duplicate label" in result


class TestGetHistory:
    async def test_empty(self, ctx, scheme: ConceptScheme):
        result = await tools.get_history(ctx, str(scheme.id))
        assert "No history" in result


# --- Management tools ---


class TestDeleteScheme:
    async def test_basic(
        self, ctx, db_session: AsyncSession, project: Project
    ):
        from taxonomy_builder.models.concept_scheme import ConceptScheme as CS

        s = CS(project_id=project.id, title="To Delete")
        db_session.add(s)
        await db_session.flush()

        result = await tools.delete_scheme(ctx, str(s.id))
        assert "Deleted" in result
        assert "To Delete" in result


class TestDeleteConcept:
    async def test_basic(self, ctx, concept: Concept):
        label = concept.pref_label
        concept_id = str(concept.id)
        result = await tools.delete_concept(ctx, concept_id)
        assert "Deleted" in result
        assert label in result


class TestExportScheme:
    async def test_basic(
        self, ctx, db_session: AsyncSession, scheme: ConceptScheme
    ):
        db_session.add(
            Concept(
                scheme_id=scheme.id, pref_label="Dogs", identifier="e1"
            )
        )
        await db_session.flush()

        result = await tools.export_scheme(ctx, str(scheme.id))
        # Should contain SKOS turtle output
        assert "skos:" in result.lower() or "@prefix" in result.lower()
