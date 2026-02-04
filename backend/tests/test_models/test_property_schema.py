"""Tests for Property Pydantic schemas."""

import pytest
from pydantic import ValidationError

from taxonomy_builder.schemas.property import (
    ALLOWED_DATATYPES,
    PropertyCreate,
    PropertyUpdate,
)


class TestPropertyCreate:
    """Tests for PropertyCreate schema."""

    def test_valid_property_with_range_scheme(self) -> None:
        """Test creating a valid property with range_scheme_id."""
        from uuid import uuid4

        scheme_id = uuid4()
        prop = PropertyCreate(
            identifier="educationLevel",
            label="Education Level",
            description="The level of education",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_scheme_id=scheme_id,
            cardinality="single",
            required=False,
        )
        assert prop.identifier == "educationLevel"
        assert prop.range_scheme_id == scheme_id
        assert prop.range_datatype is None
        assert prop.cardinality == "single"

    def test_valid_property_with_range_datatype(self) -> None:
        """Test creating a valid property with range_datatype."""
        prop = PropertyCreate(
            identifier="sampleSize",
            label="Sample Size",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:integer",
            cardinality="single",
            required=True,
        )
        assert prop.identifier == "sampleSize"
        assert prop.range_scheme_id is None
        assert prop.range_datatype == "xsd:integer"

    def test_identifier_strips_whitespace(self) -> None:
        """Test that identifier has whitespace stripped."""
        prop = PropertyCreate(
            identifier="  educationLevel  ",
            label="Education Level",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        assert prop.identifier == "educationLevel"

    def test_identifier_must_be_uri_safe(self) -> None:
        """Test that identifier must be URI-safe."""
        # Invalid: contains spaces
        with pytest.raises(ValidationError) as exc_info:
            PropertyCreate(
                identifier="education level",
                label="Education Level",
                domain_class="https://evrepo.example.org/vocab/Finding",
                range_datatype="xsd:string",
                cardinality="single",
            )
        assert "must be URI-safe" in str(exc_info.value)

    def test_identifier_must_start_with_letter(self) -> None:
        """Test that identifier must start with a letter."""
        with pytest.raises(ValidationError) as exc_info:
            PropertyCreate(
                identifier="123abc",
                label="Test",
                domain_class="https://evrepo.example.org/vocab/Finding",
                range_datatype="xsd:string",
                cardinality="single",
            )
        assert "must start with a letter" in str(exc_info.value)

    def test_identifier_allows_underscores_and_hyphens(self) -> None:
        """Test that identifier can contain underscores and hyphens."""
        prop = PropertyCreate(
            identifier="education_level-type",
            label="Education Level Type",
            domain_class="https://evrepo.example.org/vocab/Finding",
            range_datatype="xsd:string",
            cardinality="single",
        )
        assert prop.identifier == "education_level-type"

    def test_cardinality_must_be_single_or_multiple(self) -> None:
        """Test that cardinality must be 'single' or 'multiple'."""
        with pytest.raises(ValidationError) as exc_info:
            PropertyCreate(
                identifier="test",
                label="Test",
                domain_class="https://evrepo.example.org/vocab/Finding",
                range_datatype="xsd:string",
                cardinality="many",
            )
        assert "cardinality" in str(exc_info.value).lower()

    def test_valid_datatypes(self) -> None:
        """Test that all allowed datatypes are accepted."""
        for datatype in ALLOWED_DATATYPES:
            prop = PropertyCreate(
                identifier="testProp",
                label="Test",
                domain_class="https://evrepo.example.org/vocab/Finding",
                range_datatype=datatype,
                cardinality="single",
            )
            assert prop.range_datatype == datatype

    def test_invalid_datatype_rejected(self) -> None:
        """Test that invalid datatypes are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PropertyCreate(
                identifier="testProp",
                label="Test",
                domain_class="https://evrepo.example.org/vocab/Finding",
                range_datatype="xsd:float",
                cardinality="single",
            )
        assert "must be one of" in str(exc_info.value)


class TestPropertyUpdate:
    """Tests for PropertyUpdate schema."""

    def test_partial_update(self) -> None:
        """Test updating only some fields."""
        prop = PropertyUpdate(label="New Label")
        assert prop.label == "New Label"
        assert prop.identifier is None
        assert prop.cardinality is None

    def test_identifier_validation_on_update(self) -> None:
        """Test that identifier validation applies on update."""
        with pytest.raises(ValidationError):
            PropertyUpdate(identifier="invalid identifier")
