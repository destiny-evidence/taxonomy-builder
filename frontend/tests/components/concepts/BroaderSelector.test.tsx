import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { BroaderSelector } from "../../../src/components/concepts/BroaderSelector";
import { conceptsApi } from "../../../src/api/concepts";

vi.mock("../../../src/api/concepts");

const mockConceptsApi = vi.mocked(conceptsApi);

describe("BroaderSelector", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const defaultProps = {
    conceptId: "concept-1",
    currentBroader: [],
    availableConcepts: [
      {
        id: "concept-2",
        scheme_id: "scheme-1",
        identifier: "c2",
        pref_label: "Mammals",
        definition: null,
        scope_note: null,
        uri: null,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      },
      {
        id: "concept-3",
        scheme_id: "scheme-1",
        identifier: "c3",
        pref_label: "Vertebrates",
        definition: null,
        scope_note: null,
        uri: null,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      },
    ],
    onChanged: vi.fn(),
  };

  describe("display", () => {
    it("shows empty message when no broader concepts", () => {
      render(<BroaderSelector {...defaultProps} />);

      expect(screen.getByText(/No broader concepts/)).toBeInTheDocument();
    });

    it("shows current broader concepts", () => {
      render(
        <BroaderSelector
          {...defaultProps}
          currentBroader={[
            { id: "concept-2", pref_label: "Mammals" },
          ]}
        />
      );

      expect(screen.getByText("Mammals")).toBeInTheDocument();
    });

    it("shows Add Broader button when there are addable concepts", () => {
      render(<BroaderSelector {...defaultProps} />);

      expect(screen.getByText("+ Add Broader")).toBeInTheDocument();
    });
  });

  describe("filtering", () => {
    it("filters out concepts that are already broader from dropdown", () => {
      render(
        <BroaderSelector
          {...defaultProps}
          currentBroader={[
            { id: "concept-2", pref_label: "Mammals" },
          ]}
        />
      );

      fireEvent.click(screen.getByText("+ Add Broader"));

      // Mammals should not be in the dropdown since it's already a broader
      const select = screen.getByRole("combobox");
      expect(select).not.toContainHTML("Mammals");
      // But Vertebrates should be available
      expect(select).toContainHTML("Vertebrates");
    });

    it("hides Add Broader button when all concepts are already broader", () => {
      render(
        <BroaderSelector
          {...defaultProps}
          currentBroader={[
            { id: "concept-2", pref_label: "Mammals" },
            { id: "concept-3", pref_label: "Vertebrates" },
          ]}
        />
      );

      expect(screen.queryByText("+ Add Broader")).not.toBeInTheDocument();
    });
  });

  describe("add broader", () => {
    it("shows dropdown when Add Broader clicked", () => {
      render(<BroaderSelector {...defaultProps} />);

      fireEvent.click(screen.getByText("+ Add Broader"));

      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });

    it("calls API and onChanged when adding broader", async () => {
      mockConceptsApi.addBroader.mockResolvedValue(undefined);
      const onChanged = vi.fn();

      render(<BroaderSelector {...defaultProps} onChanged={onChanged} />);

      fireEvent.click(screen.getByText("+ Add Broader"));

      const select = screen.getByRole("combobox");
      fireEvent.change(select, { target: { value: "concept-2" } });

      fireEvent.click(screen.getByText("Add"));

      await waitFor(() => {
        expect(mockConceptsApi.addBroader).toHaveBeenCalledWith("concept-1", "concept-2");
      });

      await waitFor(() => {
        expect(onChanged).toHaveBeenCalled();
      });
    });

    it("disables Add button when no concept selected", () => {
      render(<BroaderSelector {...defaultProps} />);

      fireEvent.click(screen.getByText("+ Add Broader"));

      const addButton = screen.getByText("Add");
      expect(addButton).toBeDisabled();
    });
  });

  describe("remove broader", () => {
    it("calls API and onChanged when removing broader", async () => {
      mockConceptsApi.removeBroader.mockResolvedValue(undefined);
      const onChanged = vi.fn();

      render(
        <BroaderSelector
          {...defaultProps}
          currentBroader={[{ id: "concept-2", pref_label: "Mammals" }]}
          onChanged={onChanged}
        />
      );

      const removeButton = screen.getByTitle("Remove broader relationship");
      fireEvent.click(removeButton);

      await waitFor(() => {
        expect(mockConceptsApi.removeBroader).toHaveBeenCalledWith("concept-1", "concept-2");
      });

      await waitFor(() => {
        expect(onChanged).toHaveBeenCalled();
      });
    });
  });
});
