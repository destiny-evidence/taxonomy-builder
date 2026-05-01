"""Integration tests for MCP tools.

These tests call the tool functions directly with a real database session,
bypassing the MCP transport layer. This validates the business logic and
formatting of each tool.

Services are injected via explicit kwargs, overriding the Depends() defaults
that would normally be resolved by FastMCP's DI layer.
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.mcp import tools
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.feedback import Feedback
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.user import User
from taxonomy_builder.services.concept_scheme_service import ConceptSchemeService
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.feedback_service import FeedbackService
from taxonomy_builder.services.history_service import HistoryService
from taxonomy_builder.services.project_service import ProjectService
from taxonomy_builder.services.skos_export_service import SKOSExportService

# --- Exploring tools ---


class TestListProjects:
    async def test_empty(self, project_svc: ProjectService):
        result = await tools.list_projects(svc=project_svc)
        assert result == "No projects found."

    async def test_with_projects(self, project: Project, project_svc: ProjectService):
        result = await tools.list_projects(svc=project_svc)
        assert project.name in result
        assert str(project.id) in result


class TestCreateProject:
    async def test_basic(self, project_svc: ProjectService):
        result = await tools.create_project(
            name="MCP Test Project",
            namespace="https://example.org/mcp-test/",
            identifier_prefix="MCP",
            svc=project_svc,
        )
        assert "MCP Test Project" in result
        assert "Created" in result

    async def test_with_description(self, project_svc: ProjectService):
        result = await tools.create_project(
            name="Described Project",
            namespace="https://example.org/described/",
            identifier_prefix="DSC",
            description="A project with a description",
            svc=project_svc,
        )
        assert "Described Project" in result
        assert "A project with a description" in result


class TestListSchemes:
    async def test_empty(self, project: Project, scheme_svc: ConceptSchemeService):
        result = await tools.list_schemes(str(project.id), svc=scheme_svc)
        assert "No schemes found" in result

    async def test_with_schemes(
        self, scheme: ConceptScheme, project: Project,
        scheme_svc: ConceptSchemeService,
    ):
        result = await tools.list_schemes(str(project.id), svc=scheme_svc)
        assert scheme.title in result


class TestGetScheme:
    async def test_basic(self, scheme: ConceptScheme, scheme_svc: ConceptSchemeService):
        result = await tools.get_scheme(str(scheme.id), svc=scheme_svc)
        assert scheme.title in result
        assert str(scheme.id) in result

    async def test_not_found(self, scheme_svc: ConceptSchemeService):
        with pytest.raises(Exception):
            await tools.get_scheme(str(uuid4()), svc=scheme_svc)


class TestGetConceptTree:
    async def test_empty_scheme(
        self, scheme: ConceptScheme, concept_svc: ConceptService,
    ):
        result = await tools.get_concept_tree(str(scheme.id), svc=concept_svc)
        assert "empty" in result.lower()

    async def test_with_hierarchy(
        self, db_session: AsyncSession, scheme: ConceptScheme,
        concept_svc: ConceptService,
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

        result = await tools.get_concept_tree(str(scheme.id), svc=concept_svc)
        assert "Animals" in result
        assert "Dogs" in result
        lines = result.strip().split("\n")
        animals_line = next(ln for ln in lines if "Animals" in ln)
        dogs_line = next(ln for ln in lines if "Dogs" in ln)
        assert not animals_line.startswith(" ")
        assert dogs_line.startswith("  ")


class TestSearchConcepts:
    async def test_finds_match(
        self, db_session: AsyncSession, scheme: ConceptScheme,
        concept_svc: ConceptService,
    ):
        db_session.add(
            Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="c1")
        )
        await db_session.flush()

        result = await tools.search_concepts(
            "dog", scheme_id=str(scheme.id), svc=concept_svc,
        )
        assert "Dogs" in result
        assert "Found 1" in result

    async def test_no_match(
        self, scheme: ConceptScheme, concept_svc: ConceptService,
    ):
        result = await tools.search_concepts(
            "zebra", scheme_id=str(scheme.id), svc=concept_svc,
        )
        assert "No concepts matching" in result

    async def test_project_wide(
        self, db_session: AsyncSession, project: Project,
        scheme: ConceptScheme, scheme2: ConceptScheme,
        concept_svc: ConceptService,
    ):
        db_session.add(Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="s1"))
        db_session.add(Concept(scheme_id=scheme2.id, pref_label="Dog food", identifier="s2"))
        await db_session.flush()

        result = await tools.search_concepts(
            "dog", project_id=str(project.id), svc=concept_svc,
        )
        assert "Dogs" in result
        assert "Dog food" in result
        assert "Found 2" in result

    async def test_requires_scope(self):
        result = await tools.search_concepts("anything")
        assert "Provide either" in result


class TestGetConcept:
    async def test_basic(self, concept: Concept, concept_svc: ConceptService):
        result = await tools.get_concept(str(concept.id), svc=concept_svc)
        assert concept.pref_label in result
        assert str(concept.id) in result

    async def test_not_found(self, concept_svc: ConceptService):
        with pytest.raises(Exception):
            await tools.get_concept(str(uuid4()), svc=concept_svc)


# --- Building tools ---


class TestCreateScheme:
    async def test_basic(
        self, project: Project, scheme_svc: ConceptSchemeService,
    ):
        result = await tools.create_scheme(
            str(project.id), "New Scheme", svc=scheme_svc,
        )
        assert "New Scheme" in result
        assert "Created" in result

    async def test_with_uri(
        self, project: Project, scheme_svc: ConceptSchemeService,
    ):
        result = await tools.create_scheme(
            str(project.id),
            "URI Scheme",
            uri="http://example.org/vocab/test",
            svc=scheme_svc,
        )
        assert "URI Scheme" in result


class TestCreateConcept:
    async def test_basic(
        self, scheme: ConceptScheme,
        concept_svc: ConceptService, project_svc: ProjectService,
    ):
        result = await tools.create_concept(
            str(scheme.id), "Dogs",
            concept_svc=concept_svc, project_svc=project_svc,
        )
        assert "Dogs" in result
        assert "Created" in result

    async def test_with_broader(
        self, db_session: AsyncSession, scheme: ConceptScheme,
        concept_svc: ConceptService, project_svc: ProjectService,
    ):
        parent = Concept(
            scheme_id=scheme.id, pref_label="Animals", identifier="c-parent"
        )
        db_session.add(parent)
        await db_session.flush()

        result = await tools.create_concept(
            str(scheme.id),
            "Dogs",
            definition="Good boys",
            broader_concept_id=str(parent.id),
            concept_svc=concept_svc,
            project_svc=project_svc,
        )
        assert "Dogs" in result
        assert "Animals" in result


class TestCreateConceptsBatch:
    async def test_basic(
        self, scheme: ConceptScheme,
        concept_svc: ConceptService, project_svc: ProjectService,
    ):
        result = await tools.create_concepts_batch(
            str(scheme.id),
            [
                {"pref_label": "Animals"},
                {"pref_label": "Plants"},
            ],
            concept_svc=concept_svc,
            project_svc=project_svc,
        )
        assert "Created 2" in result
        assert "Animals" in result
        assert "Plants" in result

    async def test_with_batch_references(
        self, scheme: ConceptScheme,
        concept_svc: ConceptService, project_svc: ProjectService,
    ):
        result = await tools.create_concepts_batch(
            str(scheme.id),
            [
                {"pref_label": "Animals"},
                {"pref_label": "Dogs", "broader_concept_id": "#0"},
            ],
            concept_svc=concept_svc,
            project_svc=project_svc,
        )
        assert "Created 2" in result
        assert "Dogs" in result


class TestAddBroader:
    async def test_add(
        self, db_session: AsyncSession, scheme: ConceptScheme,
        concept_svc: ConceptService,
    ):
        parent = Concept(
            scheme_id=scheme.id, pref_label="Animals", identifier="p1"
        )
        child = Concept(
            scheme_id=scheme.id, pref_label="Dogs", identifier="c1"
        )
        db_session.add_all([parent, child])
        await db_session.flush()

        result = await tools.add_broader(
            str(child.id), str(parent.id), svc=concept_svc,
        )
        assert "Dogs" in result
        assert "Animals" in result
        assert "Added broader" in result


class TestRemoveBroader:
    async def test_remove(
        self, db_session: AsyncSession, scheme: ConceptScheme,
        concept_svc: ConceptService,
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

        result = await tools.remove_broader(
            str(child.id), str(parent.id), svc=concept_svc,
        )
        assert "Dogs" in result
        assert "Removed broader" in result


class TestMoveConcept:
    async def test_reparent(
        self, db_session: AsyncSession, scheme: ConceptScheme,
        concept_svc: ConceptService,
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
            str(child.id),
            new_parent_id=str(parent2.id),
            previous_parent_id=str(parent1.id),
            svc=concept_svc,
        )
        assert "Dogs" in result
        assert "Pets" in result

    async def test_move_to_root(
        self, db_session: AsyncSession, scheme: ConceptScheme,
        concept_svc: ConceptService,
    ):
        from taxonomy_builder.models.concept_broader import ConceptBroader

        parent = Concept(scheme_id=scheme.id, pref_label="Animals", identifier="mr1")
        child = Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="mr2")
        db_session.add_all([parent, child])
        await db_session.flush()
        db_session.add(ConceptBroader(concept_id=child.id, broader_concept_id=parent.id))
        await db_session.flush()

        result = await tools.move_concept(
            str(child.id),
            previous_parent_id=str(parent.id),
            svc=concept_svc,
        )
        assert "Dogs" in result
        assert "Moved" in result


# --- Refining tools ---


class TestUpdateScheme:
    async def test_update_title(
        self, scheme: ConceptScheme, scheme_svc: ConceptSchemeService,
    ):
        result = await tools.update_scheme(
            str(scheme.id), title="New Title", svc=scheme_svc,
        )
        assert "New Title" in result
        assert "Updated" in result

    async def test_update_description(
        self, scheme: ConceptScheme, scheme_svc: ConceptSchemeService,
    ):
        result = await tools.update_scheme(
            str(scheme.id), description="New description", svc=scheme_svc,
        )
        assert "New description" in result


class TestUpdateConcept:
    async def test_update_label(
        self, concept: Concept, concept_svc: ConceptService,
    ):
        result = await tools.update_concept(
            str(concept.id), pref_label="Updated Label", svc=concept_svc,
        )
        assert "Updated Label" in result
        assert "Updated" in result

    async def test_update_definition(
        self, concept: Concept, concept_svc: ConceptService,
    ):
        result = await tools.update_concept(
            str(concept.id), definition="A new definition", svc=concept_svc,
        )
        assert "A new definition" in result


class TestUpdateConceptsBatch:
    async def test_basic(
        self, db_session: AsyncSession, scheme: ConceptScheme,
        concept_svc: ConceptService,
    ):
        c1 = Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="b1")
        c2 = Concept(scheme_id=scheme.id, pref_label="Cats", identifier="b2")
        db_session.add_all([c1, c2])
        await db_session.flush()

        result = await tools.update_concepts_batch(
            [
                {"concept_id": str(c1.id), "definition": "Canines"},
                {"concept_id": str(c2.id), "definition": "Felines"},
            ],
            svc=concept_svc,
        )
        assert "Updated 2" in result


class TestAddRelated:
    async def test_add(
        self, db_session: AsyncSession, scheme: ConceptScheme,
        concept_svc: ConceptService,
    ):
        c1 = Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="r1")
        c2 = Concept(scheme_id=scheme.id, pref_label="Cats", identifier="r2")
        db_session.add_all([c1, c2])
        await db_session.flush()

        result = await tools.add_related(
            str(c1.id), str(c2.id), svc=concept_svc,
        )
        assert "Dogs" in result
        assert "Cats" in result
        assert "Added related" in result


class TestRemoveRelated:
    async def test_remove(
        self, db_session: AsyncSession, scheme: ConceptScheme,
        concept_svc: ConceptService,
    ):
        from taxonomy_builder.models.concept_related import ConceptRelated

        c1 = Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="rr1")
        c2 = Concept(scheme_id=scheme.id, pref_label="Cats", identifier="rr2")
        db_session.add_all([c1, c2])
        await db_session.flush()
        small, large = sorted([c1.id, c2.id])
        db_session.add(ConceptRelated(concept_id=small, related_concept_id=large))
        await db_session.flush()

        result = await tools.remove_related(
            str(c1.id), str(c2.id), svc=concept_svc,
        )
        assert "Removed related" in result


# --- Quality & History tools ---


class TestCheckQuality:
    async def test_empty_scheme(
        self, scheme: ConceptScheme, concept_svc: ConceptService,
    ):
        result = await tools.check_quality(str(scheme.id), svc=concept_svc)
        assert "no concepts" in result.lower()

    async def test_missing_definitions(
        self, db_session: AsyncSession, scheme: ConceptScheme,
        concept_svc: ConceptService,
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

        result = await tools.check_quality(str(scheme.id), svc=concept_svc)
        assert "Missing definitions" in result
        assert "Dogs" in result

    async def test_duplicate_labels(
        self, db_session: AsyncSession, scheme: ConceptScheme,
        concept_svc: ConceptService,
    ):
        db_session.add(
            Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="d1")
        )
        db_session.add(
            Concept(scheme_id=scheme.id, pref_label="Dogs", identifier="d2")
        )
        await db_session.flush()

        result = await tools.check_quality(str(scheme.id), svc=concept_svc)
        assert "Duplicate label" in result


class TestGetHistory:
    async def test_empty(
        self, scheme: ConceptScheme, history_svc: HistoryService,
    ):
        result = await tools.get_history(str(scheme.id), svc=history_svc)
        assert "No history" in result


# --- Management tools ---


class TestDeleteScheme:
    async def test_basic(
        self, db_session: AsyncSession, project: Project,
        scheme_svc: ConceptSchemeService,
    ):
        from taxonomy_builder.models.concept_scheme import ConceptScheme as CS

        s = CS(project_id=project.id, title="To Delete")
        db_session.add(s)
        await db_session.flush()

        result = await tools.delete_scheme(
            str(s.id), confirm_title="To Delete", svc=scheme_svc,
        )
        assert "Deleted" in result
        assert "To Delete" in result

    async def test_aborts_on_title_mismatch(
        self, db_session: AsyncSession, project: Project,
        scheme_svc: ConceptSchemeService,
    ):
        from taxonomy_builder.models.concept_scheme import ConceptScheme as CS

        s = CS(project_id=project.id, title="Real Title")
        db_session.add(s)
        await db_session.flush()

        result = await tools.delete_scheme(
            str(s.id), confirm_title="Wrong Title", svc=scheme_svc,
        )
        assert "Aborted" in result
        assert "Real Title" in result
        assert "Wrong Title" in result


class TestDeleteConcept:
    async def test_basic(self, concept: Concept, concept_svc: ConceptService):
        label = concept.pref_label
        concept_id = str(concept.id)
        result = await tools.delete_concept(
            concept_id, confirm_label=label, svc=concept_svc,
        )
        assert "Deleted" in result
        assert label in result

    async def test_aborts_on_label_mismatch(
        self, concept: Concept, concept_svc: ConceptService,
    ):
        result = await tools.delete_concept(
            str(concept.id), confirm_label="Not The Label", svc=concept_svc,
        )
        assert "Aborted" in result
        assert concept.pref_label in result
        assert "Not The Label" in result


class TestExportScheme:
    async def test_basic(
        self, db_session: AsyncSession, scheme: ConceptScheme,
        export_svc: SKOSExportService,
    ):
        db_session.add(
            Concept(
                scheme_id=scheme.id, pref_label="Dogs", identifier="e1"
            )
        )
        await db_session.flush()

        result = await tools.export_scheme(str(scheme.id), svc=export_svc)
        assert "skos:" in result.lower() or "@prefix" in result.lower()


# --- Feedback tools ---



def _make_feedback(project, user, **overrides):
    defaults = {
        "project_id": project.id,
        "snapshot_version": "1.0",
        "entity_type": "concept",
        "entity_id": "fake-entity-id",
        "entity_label": "Test Concept",
        "feedback_type": "unclear_definition",
        "content": "The definition is unclear",
        "user_id": user.id,
        "author_name": user.display_name,
        "author_email": user.email,
    }
    return Feedback(**(defaults | overrides))


class TestGetFeedbackCounts:
    async def test_no_feedback(
        self, project: Project,
        project_svc: ProjectService, feedback_svc: FeedbackService,
    ):
        result = await tools.get_feedback_counts(
            project_svc=project_svc, feedback_svc=feedback_svc,
        )
        assert "No open feedback" in result

    async def test_with_feedback(
        self, db_session: AsyncSession, project: Project, test_user: User,
        project_svc: ProjectService, feedback_svc: FeedbackService,
    ):
        db_session.add(_make_feedback(project, test_user))
        await db_session.flush()

        result = await tools.get_feedback_counts(
            project_svc=project_svc, feedback_svc=feedback_svc,
        )
        assert project.name in result


class TestListFeedback:
    async def test_empty(
        self, project: Project, feedback_svc: FeedbackService,
    ):
        result = await tools.list_feedback(str(project.id), svc=feedback_svc)
        assert "No feedback found" in result

    async def test_with_feedback(
        self, db_session: AsyncSession, project: Project, test_user: User,
        feedback_svc: FeedbackService,
    ):
        db_session.add(_make_feedback(project, test_user))
        await db_session.flush()

        result = await tools.list_feedback(str(project.id), svc=feedback_svc)
        assert "1 item" in result
        assert "Test Concept" in result

    async def test_filter_by_status(
        self, db_session: AsyncSession, project: Project, test_user: User,
        feedback_svc: FeedbackService,
    ):
        db_session.add(_make_feedback(project, test_user, status="open"))
        db_session.add(_make_feedback(project, test_user, status="resolved"))
        await db_session.flush()

        result = await tools.list_feedback(
            str(project.id), status="open", svc=feedback_svc,
        )
        assert "1 item" in result


class TestRespondToFeedback:
    async def test_basic(
        self, db_session: AsyncSession, project: Project, test_user: User,
        feedback_svc: FeedbackService,
    ):
        fb = _make_feedback(project, test_user)
        db_session.add(fb)
        await db_session.flush()

        result = await tools.respond_to_feedback(
            str(fb.id), "We'll fix this", svc=feedback_svc,
        )
        assert "Responded" in result
        assert "We'll fix this" in result


class TestResolveFeedback:
    async def test_basic(
        self, db_session: AsyncSession, project: Project, test_user: User,
        feedback_svc: FeedbackService,
    ):
        fb = _make_feedback(project, test_user)
        db_session.add(fb)
        await db_session.flush()

        result = await tools.resolve_feedback(str(fb.id), svc=feedback_svc)
        assert "Resolved" in result
        assert "[resolved]" in result

    async def test_with_message(
        self, db_session: AsyncSession, project: Project, test_user: User,
        feedback_svc: FeedbackService,
    ):
        fb = _make_feedback(project, test_user)
        db_session.add(fb)
        await db_session.flush()

        result = await tools.resolve_feedback(
            str(fb.id), "Fixed in v2", svc=feedback_svc,
        )
        assert "Fixed in v2" in result


class TestDeclineFeedback:
    async def test_basic(
        self, db_session: AsyncSession, project: Project, test_user: User,
        feedback_svc: FeedbackService,
    ):
        fb = _make_feedback(project, test_user)
        db_session.add(fb)
        await db_session.flush()

        result = await tools.decline_feedback(str(fb.id), svc=feedback_svc)
        assert "Declined" in result
        assert "[declined]" in result

    async def test_with_reason(
        self, db_session: AsyncSession, project: Project, test_user: User,
        feedback_svc: FeedbackService,
    ):
        fb = _make_feedback(project, test_user)
        db_session.add(fb)
        await db_session.flush()

        result = await tools.decline_feedback(
            str(fb.id), "Out of scope", svc=feedback_svc,
        )
        assert "Out of scope" in result
