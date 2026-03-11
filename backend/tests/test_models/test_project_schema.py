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
        project = ProjectCreate(name="Test Project", description="A test project")
        assert project.name == "Test Project"
        assert project.description == "A test project"

    def test_project_create_without_description(self) -> None:
        """Test creating a ProjectCreate without description."""
        project = ProjectCreate(name="No Description")
        assert project.name == "No Description"
        assert project.description is None

    def test_project_create_requires_name(self) -> None:
        """Test that ProjectCreate requires a name."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate()  # type: ignore[call-arg]
        assert "name" in str(exc_info.value)

    def test_project_create_name_cannot_be_empty(self) -> None:
        """Test that ProjectCreate name cannot be empty."""
        with pytest.raises(ValidationError):
            ProjectCreate(name="")

    def test_project_create_name_is_stripped(self) -> None:
        """Test that ProjectCreate name is stripped of whitespace."""
        project = ProjectCreate(name="  Spaced Name  ")
        assert project.name == "Spaced Name"

    @pytest.mark.parametrize("prefix", ["C", "EVD", "ABCD"])
    def test_create_accepts_valid_prefix(self, prefix: str) -> None:
        p = ProjectCreate(name="Test", identifier_prefix=prefix)
        assert p.identifier_prefix == prefix

    @pytest.mark.parametrize("prefix", ["evd", "ABCDE", "", "AB1"])
    def test_create_rejects_invalid_prefix(self, prefix: str) -> None:
        with pytest.raises(ValidationError, match="identifier_prefix"):
            ProjectCreate(name="Test", identifier_prefix=prefix)

    def test_create_prefix_defaults_to_none(self) -> None:
        assert ProjectCreate(name="Test").identifier_prefix is None


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

    def test_update_accepts_valid_prefix(self) -> None:
        assert ProjectUpdate(identifier_prefix="ABC").identifier_prefix == "ABC"


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
            namespace=None,
            identifier_prefix=None,
            identifier_counter=0,
        )
        assert project.id == UUID("01234567-89ab-7def-8123-456789abcdef")
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.created_at == now
        assert project.updated_at == now

    def test_read_includes_prefix_and_counter(self) -> None:
        p = ProjectRead(
            id="01234567-0123-0123-0123-012345678901",
            name="Test",
            description=None,
            namespace=None,
            identifier_prefix="EVD",
            identifier_counter=42,
            created_at="2026-01-01T00:00:00",
            updated_at="2026-01-01T00:00:00",
        )
        assert p.identifier_prefix == "EVD"
        assert p.identifier_counter == 42

    def test_project_read_requires_all_fields(self) -> None:
        """Test that ProjectRead requires all fields."""
        with pytest.raises(ValidationError):
            ProjectRead(name="Test")  # type: ignore[call-arg]
