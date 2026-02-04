import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { ClassCard } from "../../../src/components/model/ClassCard";
import type { OntologyClass, Property } from "../../../src/types/models";

const mockClass: OntologyClass = {
  uri: "http://example.org/Investigation",
  label: "Investigation",
  comment: "A discrete research effort",
};

const mockProperties: Property[] = [
  {
    id: "prop-1",
    project_id: "proj-1",
    identifier: "hasFinding",
    label: "Has Finding",
    description: null,
    domain_class: "http://example.org/Investigation",
    range_scheme_id: null,
    range_scheme: null,
    range_datatype: "xsd:string",
    cardinality: "multiple",
    required: false,
    uri: null,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "prop-2",
    project_id: "proj-1",
    identifier: "fundedBy",
    label: "Funded By",
    description: null,
    domain_class: "http://example.org/Investigation",
    range_scheme_id: "scheme-1",
    range_scheme: { id: "scheme-1", title: "Funders", uri: null },
    range_datatype: null,
    cardinality: "multiple",
    required: false,
    uri: null,
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

describe("ClassCard", () => {
  const mockOnAddProperty = vi.fn();
  const mockOnPropertyClick = vi.fn();
  const mockOnSchemeClick = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe("rendering", () => {
    it("displays class label", () => {
      render(
        <ClassCard
          ontologyClass={mockClass}
          properties={[]}
          onAddProperty={mockOnAddProperty}
          onPropertyClick={mockOnPropertyClick}
          onSchemeClick={mockOnSchemeClick}
        />
      );

      expect(screen.getByText("Investigation")).toBeInTheDocument();
    });

    it("shows class description in tooltip", () => {
      render(
        <ClassCard
          ontologyClass={mockClass}
          properties={[]}
          onAddProperty={mockOnAddProperty}
          onPropertyClick={mockOnPropertyClick}
          onSchemeClick={mockOnSchemeClick}
        />
      );

      const header = screen.getByText("Investigation").closest(".class-card__header");
      expect(header).toHaveAttribute("title", "A discrete research effort");
    });

    it("displays properties for the class", () => {
      render(
        <ClassCard
          ontologyClass={mockClass}
          properties={mockProperties}
          onAddProperty={mockOnAddProperty}
          onPropertyClick={mockOnPropertyClick}
          onSchemeClick={mockOnSchemeClick}
        />
      );

      expect(screen.getByText("Has Finding")).toBeInTheDocument();
      expect(screen.getByText("Funded By")).toBeInTheDocument();
    });

    it("shows datatype indicator for datatype properties", () => {
      render(
        <ClassCard
          ontologyClass={mockClass}
          properties={mockProperties}
          onAddProperty={mockOnAddProperty}
          onPropertyClick={mockOnPropertyClick}
          onSchemeClick={mockOnSchemeClick}
        />
      );

      expect(screen.getByText("xsd:string")).toBeInTheDocument();
    });

    it("shows scheme name for scheme properties", () => {
      render(
        <ClassCard
          ontologyClass={mockClass}
          properties={mockProperties}
          onAddProperty={mockOnAddProperty}
          onPropertyClick={mockOnPropertyClick}
          onSchemeClick={mockOnSchemeClick}
        />
      );

      expect(screen.getByText("Funders")).toBeInTheDocument();
    });

    it("shows empty state when no properties", () => {
      render(
        <ClassCard
          ontologyClass={mockClass}
          properties={[]}
          onAddProperty={mockOnAddProperty}
          onPropertyClick={mockOnPropertyClick}
          onSchemeClick={mockOnSchemeClick}
        />
      );

      expect(screen.getByText(/no properties/i)).toBeInTheDocument();
    });

    it("shows add property button", () => {
      render(
        <ClassCard
          ontologyClass={mockClass}
          properties={[]}
          onAddProperty={mockOnAddProperty}
          onPropertyClick={mockOnPropertyClick}
          onSchemeClick={mockOnSchemeClick}
        />
      );

      expect(screen.getByRole("button", { name: /add property/i })).toBeInTheDocument();
    });
  });

  describe("interactions", () => {
    it("calls onAddProperty when add button clicked", () => {
      render(
        <ClassCard
          ontologyClass={mockClass}
          properties={[]}
          onAddProperty={mockOnAddProperty}
          onPropertyClick={mockOnPropertyClick}
          onSchemeClick={mockOnSchemeClick}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /add property/i }));

      expect(mockOnAddProperty).toHaveBeenCalledWith(mockClass.uri);
    });

    it("calls onPropertyClick when property clicked", () => {
      render(
        <ClassCard
          ontologyClass={mockClass}
          properties={mockProperties}
          onAddProperty={mockOnAddProperty}
          onPropertyClick={mockOnPropertyClick}
          onSchemeClick={mockOnSchemeClick}
        />
      );

      fireEvent.click(screen.getByText("Has Finding"));

      expect(mockOnPropertyClick).toHaveBeenCalledWith("prop-1");
    });

    it("calls onSchemeClick when scheme link clicked", () => {
      render(
        <ClassCard
          ontologyClass={mockClass}
          properties={mockProperties}
          onAddProperty={mockOnAddProperty}
          onPropertyClick={mockOnPropertyClick}
          onSchemeClick={mockOnSchemeClick}
        />
      );

      fireEvent.click(screen.getByText("Funders"));

      expect(mockOnSchemeClick).toHaveBeenCalledWith("scheme-1");
    });
  });
});
