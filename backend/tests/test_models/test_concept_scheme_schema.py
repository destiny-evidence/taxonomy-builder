"""Tests for ConceptScheme Pydantic schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from faker import Faker
from pydantic import ValidationError

from taxonomy_builder.schemas.concept_scheme import (
    ConceptSchemeCreate,
    ConceptSchemeRead,
    ConceptSchemeUpdate,
)

fake = Faker()


class TestConceptSchemeCreate:
    """Tests for ConceptSchemeCreate schema."""

    def test_valid_concept_scheme_create(self) -> None:
        """Test creating a valid concept scheme."""
        title = fake.sentence(nb_words=3)
        description = fake.sentence()
        uri = fake.uri()
        scheme = ConceptSchemeCreate(
            title=title,
            description=description,
            uri=uri,
        )
        assert scheme.title == title
        assert scheme.description == description
        assert scheme.uri == uri

    def test_concept_scheme_create_title_only(self) -> None:
        """Test creating a scheme with only title."""
        title = fake.sentence(nb_words=3)
        scheme = ConceptSchemeCreate(title=title)
        assert scheme.title == title
        assert scheme.description is None
        assert scheme.uri is None

    def test_concept_scheme_create_requires_title(self) -> None:
        """Test that title is required."""
        with pytest.raises(ValidationError) as exc_info:
            ConceptSchemeCreate()  # type: ignore[call-arg]
        assert "title" in str(exc_info.value)

    def test_concept_scheme_create_title_cannot_be_empty(self) -> None:
        """Test that title cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            ConceptSchemeCreate(title="")
        assert "title" in str(exc_info.value)

    def test_concept_scheme_create_title_is_stripped(self) -> None:
        """Test that title whitespace is stripped."""
        scheme = ConceptSchemeCreate(title="  Padded Title  ")
        assert scheme.title == "Padded Title"


class TestConceptSchemeUpdate:
    """Tests for ConceptSchemeUpdate schema."""

    def test_concept_scheme_update_all_fields_optional(self) -> None:
        """Test that all fields are optional for update."""
        scheme = ConceptSchemeUpdate()
        assert scheme.title is None
        assert scheme.description is None
        assert scheme.uri is None

    def test_concept_scheme_update_with_title(self) -> None:
        """Test updating with a new title."""
        title = fake.sentence(nb_words=3)
        scheme = ConceptSchemeUpdate(title=title)
        assert scheme.title == title

    def test_concept_scheme_update_with_all_fields(self) -> None:
        """Test updating all fields."""
        title = fake.sentence(nb_words=3)
        description = fake.sentence()
        uri = fake.uri()
        scheme = ConceptSchemeUpdate(
            title=title,
            description=description,
            uri=uri,
        )
        assert scheme.title == title
        assert scheme.description == description
        assert scheme.uri == uri

    def test_concept_scheme_update_title_cannot_be_empty(self) -> None:
        """Test that title cannot be empty string if provided."""
        with pytest.raises(ValidationError) as exc_info:
            ConceptSchemeUpdate(title="")
        assert "title" in str(exc_info.value)

    def test_concept_scheme_update_title_is_stripped(self) -> None:
        """Test that title whitespace is stripped."""
        scheme = ConceptSchemeUpdate(title="  Padded  ")
        assert scheme.title == "Padded"


class TestConceptSchemeRead:
    """Tests for ConceptSchemeRead schema."""

    def test_valid_concept_scheme_read(self) -> None:
        """Test reading a valid concept scheme."""
        now = datetime.now()
        scheme_id = uuid4()
        project_id = uuid4()
        title = fake.sentence(nb_words=3)
        description = fake.sentence()
        uri = fake.uri()
        scheme = ConceptSchemeRead(
            id=scheme_id,
            project_id=project_id,
            title=title,
            description=description,
            uri=uri,
            created_at=now,
            updated_at=now,
        )
        assert scheme.id == scheme_id
        assert scheme.project_id == project_id
        assert scheme.title == title
        assert scheme.description == description
        assert scheme.uri == uri
        assert scheme.created_at == now
        assert scheme.updated_at == now

    def test_concept_scheme_read_requires_all_fields(self) -> None:
        """Test that required fields must be provided."""
        with pytest.raises(ValidationError):
            ConceptSchemeRead()  # type: ignore[call-arg]

    def test_concept_scheme_read_optional_fields_can_be_none(self) -> None:
        """Test that optional fields can be None."""
        now = datetime.now()
        scheme = ConceptSchemeRead(
            id=fake.uuid4(),
            project_id=fake.uuid4(),
            title=fake.sentence(nb_words=3),
            description=None,
            uri=None,
            created_at=now,
            updated_at=now,
        )
        assert scheme.description is None
        assert scheme.uri is None
