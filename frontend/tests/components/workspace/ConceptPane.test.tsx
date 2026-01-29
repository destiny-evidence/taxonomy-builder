import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/preact";
import { ConceptPane } from "../../../src/components/workspace/ConceptPane";
import { selectedConceptId, concepts } from "../../../src/state/concepts";
import type { Concept } from "../../../src/types/models";

// Mock ConceptDetail since it has complex dependencies
vi.mock("../../../src/components/concepts/ConceptDetail", () => ({
  ConceptDetail: ({ concept }: { concept: Concept }) => (
    <div data-testid="concept-detail">ConceptDetail: {concept.pref_label}</div>
  ),
}));

const mockConcept: Concept = {
  id: "concept-1",
  scheme_id: "scheme-1",
  identifier: "animals",
  pref_label: "Animals",
  definition: "Living organisms",
  scope_note: null,
  uri: "http://example.org/animals",
  alt_labels: [],
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  broader: [],
  related: [],
};

describe("ConceptPane", () => {
  const mockOnDelete = vi.fn();
  const mockOnRefresh = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
    selectedConceptId.value = null;
    concepts.value = [];
  });

  it("shows empty state when no concept is selected", () => {
    render(
      <ConceptPane
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    expect(screen.getByText(/select a concept/i)).toBeInTheDocument();
  });

  it("shows ConceptDetail when concept is selected", () => {
    // Set up state so selectedConcept computed signal returns mockConcept
    concepts.value = [mockConcept];
    selectedConceptId.value = "concept-1";

    render(
      <ConceptPane
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    );

    expect(screen.getByTestId("concept-detail")).toBeInTheDocument();
    expect(screen.getByText("ConceptDetail: Animals")).toBeInTheDocument();
  });
});
