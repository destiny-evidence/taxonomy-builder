"""Tests for the Project Pydantic schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from faker import Faker
from pydantic import ValidationError

from taxonomy_builder.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

fake = Faker()


class TestProjectCreate:
    """Tests for ProjectCreate schema."""

    def test_valid_project_create(self) -> None:
        """Test creating a valid ProjectCreate schema."""
        name = fake.company()
        description = fake.sentence()
        project = ProjectCreate(name=name, description=description)
        assert project.name == name
        assert project.description == description

    def test_project_create_without_description(self) -> None:
        """Test creating a ProjectCreate without description."""
        name = fake.company()
        project = ProjectCreate(name=name)
        assert project.name == name
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


class TestProjectUpdate:
    """Tests for ProjectUpdate schema."""

    def test_project_update_all_fields_optional(self) -> None:
        """Test that all fields in ProjectUpdate are optional."""
        project = ProjectUpdate()
        assert project.name is None
        assert project.description is None

    def test_project_update_with_name(self) -> None:
        """Test ProjectUpdate with only name."""
        name = fake.company()
        project = ProjectUpdate(name=name)
        assert project.name == name
        assert project.description is None

    def test_project_update_with_description(self) -> None:
        """Test ProjectUpdate with only description."""
        description = fake.sentence()
        project = ProjectUpdate(description=description)
        assert project.name is None
        assert project.description == description


class TestProjectRead:
    """Tests for ProjectRead schema."""

    def test_valid_project_read(self) -> None:
        """Test creating a valid ProjectRead schema."""
        now = datetime.now()
        project_id = uuid4()
        name = fake.company()
        description = fake.sentence()
        project = ProjectRead(
            id=project_id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
            namespace=None,
        )
        assert project.id == project_id
        assert project.name == name
        assert project.description == description
        assert project.created_at == now
        assert project.updated_at == now

    def test_project_read_requires_all_fields(self) -> None:
        """Test that ProjectRead requires all fields."""
        with pytest.raises(ValidationError):
            ProjectRead(name="Test")  # type: ignore[call-arg]
