import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { RelatedSelector } from "../../../src/components/concepts/RelatedSelector";
import { conceptsApi } from "../../../src/api/concepts";

vi.mock("../../../src/api/concepts");

const mockConceptsApi = vi.mocked(conceptsApi);

describe("RelatedSelector", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const defaultProps = {
    conceptId: "concept-1",
    currentRelated: [],
    availableConcepts: [
      {
        id: "concept-2",
        scheme_id: "scheme-1",
        identifier: "c2",
        pref_label: "Cats",
        definition: null,
        scope_note: null,
        uri: null,
        alt_labels: [],
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
        broader: [],
        related: [],
      },
      {
        id: "concept-3",
        scheme_id: "scheme-1",
        identifier: "c3",
        pref_label: "Veterinary Medicine",
        definition: null,
        scope_note: null,
        uri: null,
        alt_labels: [],
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
        broader: [],
        related: [],
      },
    ],
    onChanged: vi.fn(),
  };

  describe("display", () => {
    it("shows empty message when no related concepts", () => {
      render(<RelatedSelector {...defaultProps} />);

      expect(screen.getByText(/No related concepts/)).toBeInTheDocument();
    });

    it("shows current related concepts", () => {
      render(
        <RelatedSelector
          {...defaultProps}
          currentRelated={[
            { id: "concept-2", pref_label: "Cats", scheme_id: "scheme-1", identifier: "c2", definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
          ]}
        />
      );

      expect(screen.getByText("Cats")).toBeInTheDocument();
    });

    it("shows Add Related button when there are addable concepts", () => {
      render(<RelatedSelector {...defaultProps} />);

      expect(screen.getByText("+ Add Related")).toBeInTheDocument();
    });
  });

  describe("filtering", () => {
    it("filters out self from available concepts", () => {
      render(<RelatedSelector {...defaultProps} />);

      fireEvent.click(screen.getByText("+ Add Related"));

      const select = screen.getByRole("combobox");
      // concept-1 (self) should not be in dropdown
      expect(select).not.toContainHTML("concept-1");
    });

    it("filters out concepts that are already related from dropdown", () => {
      render(
        <RelatedSelector
          {...defaultProps}
          currentRelated={[
            { id: "concept-2", pref_label: "Cats", scheme_id: "scheme-1", identifier: "c2", definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
          ]}
        />
      );

      fireEvent.click(screen.getByText("+ Add Related"));

      // Cats should not be in the dropdown since it's already related
      const select = screen.getByRole("combobox");
      expect(select).not.toContainHTML("Cats");
      // But Veterinary Medicine should be available
      expect(select).toContainHTML("Veterinary Medicine");
    });

    it("hides Add Related button when all concepts are already related", () => {
      render(
        <RelatedSelector
          {...defaultProps}
          currentRelated={[
            { id: "concept-2", pref_label: "Cats", scheme_id: "scheme-1", identifier: "c2", definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
            { id: "concept-3", pref_label: "Veterinary Medicine", scheme_id: "scheme-1", identifier: "c3", definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
          ]}
        />
      );

      expect(screen.queryByText("+ Add Related")).not.toBeInTheDocument();
    });
  });

  describe("add related", () => {
    it("shows dropdown when Add Related clicked", () => {
      render(<RelatedSelector {...defaultProps} />);

      fireEvent.click(screen.getByText("+ Add Related"));

      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });

    it("calls API and onChanged when adding related", async () => {
      mockConceptsApi.addRelated.mockResolvedValue({ status: "created" });
      const onChanged = vi.fn();

      render(<RelatedSelector {...defaultProps} onChanged={onChanged} />);

      fireEvent.click(screen.getByText("+ Add Related"));

      const select = screen.getByRole("combobox");
      fireEvent.change(select, { target: { value: "concept-2" } });

      fireEvent.click(screen.getByText("Add"));

      await waitFor(() => {
        expect(mockConceptsApi.addRelated).toHaveBeenCalledWith("concept-1", "concept-2");
      });

      await waitFor(() => {
        expect(onChanged).toHaveBeenCalled();
      });
    });

    it("disables Add button when no concept selected", () => {
      render(<RelatedSelector {...defaultProps} />);

      fireEvent.click(screen.getByText("+ Add Related"));

      const addButton = screen.getByText("Add");
      expect(addButton).toBeDisabled();
    });
  });

  describe("remove related", () => {
    it("calls API and onChanged when removing related", async () => {
      mockConceptsApi.removeRelated.mockResolvedValue(undefined);
      const onChanged = vi.fn();

      render(
        <RelatedSelector
          {...defaultProps}
          currentRelated={[{ id: "concept-2", pref_label: "Cats", scheme_id: "scheme-1", identifier: "c2", definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" }]}
          onChanged={onChanged}
        />
      );

      const removeButton = screen.getByTitle("Remove related relationship");
      fireEvent.click(removeButton);

      await waitFor(() => {
        expect(mockConceptsApi.removeRelated).toHaveBeenCalledWith("concept-1", "concept-2");
      });

      await waitFor(() => {
        expect(onChanged).toHaveBeenCalled();
      });
    });
  });
});
