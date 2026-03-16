"""Tests for the Project Pydantic schemas."""

from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from taxonomy_builder.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate


class TestProjectCreate:
    """Tests for ProjectCreate schema."""

    def test_valid_project_create(self) -> None:
        """Test creating a valid ProjectCreate schema."""
        project = ProjectCreate(
            name="Test Project",
            description="A test project",
            namespace="https://example.org/vocab",
            identifier_prefix="TST",
        )
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.identifier_prefix == "TST"

    def test_project_create_without_description(self) -> None:
        """Test creating a ProjectCreate without description."""
        project = ProjectCreate(
            name="No Description",
            namespace="https://example.org/vocab",
            identifier_prefix="TST",
        )
        assert project.name == "No Description"
        assert project.description is None

    def test_project_create_requires_name(self) -> None:
        """Test that ProjectCreate requires a name."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate()  # type: ignore[call-arg]
        assert "name" in str(exc_info.value)

    def test_project_create_requires_namespace(self) -> None:
        """Test that ProjectCreate requires a namespace."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(name="Test")  # type: ignore[call-arg]
        assert "namespace" in str(exc_info.value)

    def test_project_create_name_cannot_be_empty(self) -> None:
        """Test that ProjectCreate name cannot be empty."""
        with pytest.raises(ValidationError):
            ProjectCreate(
                name="",
                namespace="https://example.org/vocab",
                identifier_prefix="TST",
            )

    def test_project_create_requires_identifier_prefix(self) -> None:
        """Test that ProjectCreate requires identifier_prefix."""
        with pytest.raises(ValidationError, match="identifier_prefix"):
            ProjectCreate(name="Test", namespace="https://example.org/vocab")

    def test_project_create_name_is_stripped(self) -> None:
        """Test that ProjectCreate name is stripped of whitespace."""
        project = ProjectCreate(
            name="  Spaced Name  ",
            namespace="https://example.org/vocab",
            identifier_prefix="TST",
        )
        assert project.name == "Spaced Name"


class TestProjectUpdate:
    """Tests for ProjectUpdate schema."""

    def test_project_update_all_fields_optional(self) -> None:
        """Test that all fields in ProjectUpdate are optional."""
        project = ProjectUpdate()
        assert project.name is None
        assert project.description is None

    def test_project_update_with_name(self) -> None:
        """Test ProjectUpdate with only name."""
        project = ProjectUpdate(name="New Name")
        assert project.name == "New Name"
        assert project.description is None

    def test_project_update_with_description(self) -> None:
        """Test ProjectUpdate with only description."""
        project = ProjectUpdate(description="New Description")
        assert project.name is None
        assert project.description == "New Description"

    def test_project_update_rejects_null_namespace(self) -> None:
        """Test that ProjectUpdate rejects explicitly setting namespace to null."""
        with pytest.raises(ValidationError):
            ProjectUpdate(namespace=None)

    def test_project_update_rejects_null_prefix(self) -> None:
        """Test that ProjectUpdate rejects explicitly setting identifier_prefix to null."""
        with pytest.raises(ValidationError):
            ProjectUpdate(identifier_prefix=None)


class TestProjectRead:
    """Tests for ProjectRead schema."""

    def test_valid_project_read(self) -> None:
        """Test creating a valid ProjectRead schema."""
        now = datetime.now()
        project = ProjectRead(
            id=UUID("01234567-89ab-7def-8123-456789abcdef"),
            name="Test Project",
            description="A test project",
            created_at=now,
            updated_at=now,
            namespace="https://example.org/vocab",
            identifier_prefix="TST",
            identifier_counter=0,
            prefix_locked=False,
        )
        assert project.id == UUID("01234567-89ab-7def-8123-456789abcdef")
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.created_at == now
        assert project.updated_at == now

    def test_project_read_requires_all_fields(self) -> None:
        """Test that ProjectRead requires all fields."""
        with pytest.raises(ValidationError):
            ProjectRead(name="Test")  # type: ignore[call-arg]
