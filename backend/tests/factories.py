"""Factory Boy factories for test data creation.

Uses SQLAlchemyModelFactory with sqlalchemy_session_persistence=None so that
factory.create() calls session.add() (sync, safe on AsyncSession) but skips
the sync flush/commit. Tests must await flush() to persist.

Usage:
    from tests.factories import ConceptFactory, flush

    async def test_something(db_session):
        concept = await flush(db_session, ConceptFactory.create(
            pref_label="Dogs", identifier="dogs",
        ))
        # concept.scheme and concept.scheme.project are auto-created
"""

from contextvars import ContextVar
from uuid import uuid4

import factory
import factory.alchemy
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.change_event import ChangeEvent
from taxonomy_builder.models.comment import Comment
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.property import Property
from taxonomy_builder.models.published_version import PublishedVersion
from taxonomy_builder.models.user import User

# ---------------------------------------------------------------------------
# Session injection via ContextVar
# ---------------------------------------------------------------------------

_session: ContextVar[AsyncSession] = ContextVar("test_session")


def set_session(session: AsyncSession) -> None:
    _session.set(session)


def get_session() -> AsyncSession:
    return _session.get()


# ---------------------------------------------------------------------------
# Async persistence helper
# ---------------------------------------------------------------------------


async def flush(session: AsyncSession, obj):
    """Flush and refresh a factory-created object (and its relationship graph)."""
    await session.flush()
    await session.refresh(obj)
    return obj


# ---------------------------------------------------------------------------
# Base factory
# ---------------------------------------------------------------------------


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session_factory = get_session
        sqlalchemy_session_persistence = None


# ---------------------------------------------------------------------------
# Model factories
# ---------------------------------------------------------------------------


class ProjectFactory(BaseFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Project {n}")
    description = None
    namespace = None


class ConceptSchemeFactory(BaseFactory):
    class Meta:
        model = ConceptScheme

    project = factory.SubFactory(ProjectFactory)
    title = factory.Sequence(lambda n: f"Scheme {n}")
    description = None
    uri = factory.LazyAttribute(
        lambda o: f"http://example.org/schemes/{o.title.lower().replace(' ', '-')}"
    )


class ConceptFactory(BaseFactory):
    class Meta:
        model = Concept

    scheme = factory.SubFactory(ConceptSchemeFactory)
    pref_label = factory.Sequence(lambda n: f"Concept {n}")
    identifier = factory.LazyAttribute(
        lambda o: o.pref_label.lower().replace(" ", "-")
    )
    definition = None
    scope_note = None
    alt_labels = factory.LazyFunction(list)


class UserFactory(BaseFactory):
    class Meta:
        model = User

    keycloak_user_id = factory.Sequence(lambda n: f"keycloak-{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    display_name = factory.Sequence(lambda n: f"User {n}")


class CommentFactory(BaseFactory):
    class Meta:
        model = Comment

    concept_id = None  # caller must supply
    user = factory.SubFactory(UserFactory)
    content = factory.Sequence(lambda n: f"Comment {n}")
    parent_comment_id = None
    deleted_at = None


class PropertyFactory(BaseFactory):
    class Meta:
        model = Property

    project = factory.SubFactory(ProjectFactory)
    identifier = factory.Sequence(lambda n: f"prop{n}")
    label = factory.Sequence(lambda n: f"Property {n}")
    description = None
    domain_class = "https://example.org/ontology/Finding"
    range_scheme = None
    range_datatype = "xsd:string"
    cardinality = "single"
    required = False


class ChangeEventFactory(BaseFactory):
    class Meta:
        model = ChangeEvent

    entity_type = "concept"
    entity_id = factory.LazyFunction(uuid4)
    action = "create"
    project_id = None
    scheme_id = None
    user_id = None
    before_state = None
    after_state = None


class PublishedVersionFactory(BaseFactory):
    class Meta:
        model = PublishedVersion

    project = factory.SubFactory(ProjectFactory)
    version = factory.Sequence(lambda n: f"{n + 1}.0")
    title = factory.LazyAttribute(lambda o: f"Version {o.version}")
    notes = None
    finalized = False
    published_at = None
    previous_version_id = None
    publisher = None
    snapshot = factory.LazyFunction(lambda: {"concept_schemes": [], "properties": [], "classes": []})
