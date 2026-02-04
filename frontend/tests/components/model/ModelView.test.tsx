import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/preact";
import { ModelView } from "../../../src/components/model/ModelView";
import { ontologyApi } from "../../../src/api/ontology";
import { propertiesApi } from "../../../src/api/properties";
import { ontology, ontologyLoading } from "../../../src/state/ontology";
import { properties } from "../../../src/state/properties";
import type { CoreOntology, Property } from "../../../src/types/models";

vi.mock("../../../src/api/ontology");
vi.mock("../../../src/api/properties");

const mockOntology: CoreOntology = {
  classes: [
    { uri: "http://example.org/Investigation", label: "Investigation", comment: "A research effort" },
    { uri: "http://example.org/Finding", label: "Finding", comment: "A specific result" },
  ],
  object_properties: [],
  datatype_properties: [],
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
];

describe("ModelView", () => {
  const mockOnSchemeSelect = vi.fn();
  const mockOnBack = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
    ontology.value = null;
    ontologyLoading.value = false;
    properties.value = [];
    vi.mocked(ontologyApi.get).mockResolvedValue(mockOntology);
    vi.mocked(propertiesApi.listForProject).mockResolvedValue([]);
  });

  describe("loading state", () => {
    it("shows loading indicator while loading ontology", async () => {
      vi.mocked(ontologyApi.get).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockOntology), 100))
      );

      render(
        <ModelView
          projectId="proj-1"
          projectName="Test Project"
          onSchemeSelect={mockOnSchemeSelect}
          onBack={mockOnBack}
        />
      );

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });
  });

  describe("rendering", () => {
    it("shows project name in header", async () => {
      render(
        <ModelView
          projectId="proj-1"
          projectName="Test Project"
          onSchemeSelect={mockOnSchemeSelect}
          onBack={mockOnBack}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("Test Project")).toBeInTheDocument();
      });
    });

    it("shows back button", async () => {
      render(
        <ModelView
          projectId="proj-1"
          projectName="Test Project"
          onSchemeSelect={mockOnSchemeSelect}
          onBack={mockOnBack}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /schemes/i })).toBeInTheDocument();
      });
    });

    it("displays class cards for each ontology class", async () => {
      render(
        <ModelView
          projectId="proj-1"
          projectName="Test Project"
          onSchemeSelect={mockOnSchemeSelect}
          onBack={mockOnBack}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("Investigation")).toBeInTheDocument();
        expect(screen.getByText("Finding")).toBeInTheDocument();
      });
    });

    it("groups properties by domain class", async () => {
      vi.mocked(propertiesApi.listForProject).mockResolvedValue(mockProperties);

      render(
        <ModelView
          projectId="proj-1"
          projectName="Test Project"
          onSchemeSelect={mockOnSchemeSelect}
          onBack={mockOnBack}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("Has Finding")).toBeInTheDocument();
      });
    });
  });

  describe("interactions", () => {
    it("calls onBack when back button clicked", async () => {
      render(
        <ModelView
          projectId="proj-1"
          projectName="Test Project"
          onSchemeSelect={mockOnSchemeSelect}
          onBack={mockOnBack}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /schemes/i })).toBeInTheDocument();
      });

      screen.getByRole("button", { name: /schemes/i }).click();

      expect(mockOnBack).toHaveBeenCalled();
    });
  });
});
