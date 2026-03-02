import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { ClassDetail } from "../../../src/components/classes/ClassDetail";
import { classesApi } from "../../../src/api/classes";
import { ApiError } from "../../../src/api/client";
import type { OntologyClass } from "../../../src/types/models";

vi.mock("../../../src/api/classes");

const mockClass: OntologyClass = {
  id: "cls-1",
  project_id: "proj-1",
  identifier: "Person",
  label: "Person",
  description: "A human being",
  scope_note: "Used for individual persons",
  uri: "http://example.org/Person",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const mockClassNoDescription: OntologyClass = {
  id: "cls-2",
  project_id: "proj-1",
  identifier: "Organization",
  label: "Organization",
  description: null,
  scope_note: null,
  uri: "http://example.org/Organization",
  created_at: "2024-01-02T00:00:00Z",
  updated_at: "2024-01-02T00:00:00Z",
};

const mockOnRefresh = vi.fn();
const mockOnDeleted = vi.fn();
const mockOnSuccess = vi.fn();
const mockOnCancel = vi.fn();

function renderView(cls: OntologyClass = mockClass) {
  return render(
    <ClassDetail
      ontologyClass={cls}
      onRefresh={mockOnRefresh}
      onDeleted={mockOnDeleted}
    />
  );
}

function renderCreate() {
  return render(
    <ClassDetail
      mode="create"
      projectId="proj-1"
      onSuccess={mockOnSuccess}
      onCancel={mockOnCancel}
      onRefresh={mockOnRefresh}
    />
  );
}

describe("ClassDetail", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe("view mode", () => {
    it("displays class label as heading", () => {
      renderView();
      expect(screen.getByRole("heading", { name: "Person" })).toBeInTheDocument();
    });

    it("displays identifier", () => {
      renderView();
      const mono = document.querySelector(".workspace-detail__value--mono");
      expect(mono).toHaveTextContent("Person");
    });

    it("displays description when present", () => {
      renderView();
      expect(screen.getByText("A human being")).toBeInTheDocument();
    });

    it("does not display description section when null", () => {
      renderView(mockClassNoDescription);
      expect(screen.queryByText("A human being")).not.toBeInTheDocument();
    });

    it("displays scope note when present", () => {
      renderView();
      expect(screen.getByText("Used for individual persons")).toBeInTheDocument();
    });

    it("does not display scope note section when null", () => {
      renderView(mockClassNoDescription);
      expect(screen.queryByText("Scope Note")).not.toBeInTheDocument();
    });

    it("shows Edit button", () => {
      renderView();
      expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
    });

    it("shows Delete button", () => {
      renderView();
      expect(screen.getByRole("button", { name: /delete/i })).toBeInTheDocument();
    });
  });

  describe("edit mode", () => {
    it("enters edit mode when Edit clicked", () => {
      renderView();
      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      expect(screen.getByText("Edit Class")).toBeInTheDocument();
      expect(screen.getByLabelText(/label/i)).toBeInTheDocument();
    });

    it("pre-fills form with current values", () => {
      renderView();
      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      expect((screen.getByLabelText(/label/i) as HTMLInputElement).value).toBe("Person");
    });

    it("shows identifier as read-only text in edit mode", () => {
      renderView();
      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      // Identifier should not be an input in edit mode
      const identifierInputs = screen.queryAllByLabelText(/identifier/i);
      const textInputs = identifierInputs.filter((el) => el.tagName === "INPUT");
      expect(textInputs).toHaveLength(0);
    });

    it("shows Save and Cancel buttons", () => {
      renderView();
      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
    });

    it("cancels edit mode", () => {
      renderView();
      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /cancel/i }));

      expect(screen.queryByText("Edit Class")).not.toBeInTheDocument();
    });

    it("disables Save when no changes", () => {
      renderView();
      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      expect(screen.getByRole("button", { name: /save/i })).toBeDisabled();
    });

    it("enables Save when changes are made", () => {
      renderView();
      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const labelInput = screen.getByLabelText(/label/i);
      fireEvent.input(labelInput, { target: { value: "Updated Person" } });

      expect(screen.getByRole("button", { name: /save/i })).not.toBeDisabled();
    });

    it("calls classesApi.update on save", async () => {
      vi.mocked(classesApi.update).mockResolvedValue({ ...mockClass, label: "Updated" });

      renderView();
      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const labelInput = screen.getByLabelText(/label/i);
      fireEvent.input(labelInput, { target: { value: "Updated" } });
      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(classesApi.update).toHaveBeenCalledWith("cls-1", expect.objectContaining({
          label: "Updated",
        }));
        expect(mockOnRefresh).toHaveBeenCalled();
      });
    });

    it("shows error on 409 conflict", async () => {
      vi.mocked(classesApi.update).mockRejectedValue(new ApiError(409, "Conflict"));

      renderView();
      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const labelInput = screen.getByLabelText(/label/i);
      fireEvent.input(labelInput, { target: { value: "Changed" } });
      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent(/identifier already exists/i);
      });
    });
  });

  describe("delete", () => {
    it("shows confirmation dialog when Delete clicked", () => {
      renderView();
      fireEvent.click(screen.getByRole("button", { name: /delete/i }));

      expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    });

    it("calls classesApi.delete on confirm", async () => {
      vi.mocked(classesApi.delete).mockResolvedValue(undefined as never);

      renderView();
      fireEvent.click(screen.getByRole("button", { name: /delete/i }));
      fireEvent.click(screen.getByRole("button", { name: /confirm/i }));

      await waitFor(() => {
        expect(classesApi.delete).toHaveBeenCalledWith("cls-1");
        expect(mockOnDeleted).toHaveBeenCalled();
      });
    });
  });

  describe("create mode", () => {
    it("shows New Class heading", () => {
      renderCreate();
      expect(screen.getByText("New Class")).toBeInTheDocument();
    });

    it("shows editable identifier field", () => {
      renderCreate();
      const identifierInput = screen.getByLabelText(/identifier/i);
      expect(identifierInput).toBeInTheDocument();
      expect(identifierInput.tagName).toBe("INPUT");
    });

    it("auto-generates identifier from label", async () => {
      renderCreate();
      const labelInput = screen.getByLabelText(/label/i);
      fireEvent.input(labelInput, { target: { value: "My Cool Class" } });

      await waitFor(() => {
        const identifierInput = screen.getByLabelText(/identifier/i) as HTMLInputElement;
        expect(identifierInput.value).toBe("myCoolClass");
      });
    });

    it("stops auto-generation after manual identifier edit", async () => {
      renderCreate();
      const identifierInput = screen.getByLabelText(/identifier/i);
      fireEvent.input(identifierInput, { target: { value: "customId" } });

      const labelInput = screen.getByLabelText(/label/i);
      fireEvent.input(labelInput, { target: { value: "Some Label" } });

      await waitFor(() => {
        expect((screen.getByLabelText(/identifier/i) as HTMLInputElement).value).toBe("customId");
      });
    });

    it("validates identifier format", async () => {
      renderCreate();
      const identifierInput = screen.getByLabelText(/identifier/i);
      fireEvent.input(identifierInput, { target: { value: "123invalid" } });

      await waitFor(() => {
        expect(screen.getByText(/must start with a letter/i)).toBeInTheDocument();
      });
    });

    it("calls classesApi.create on submit", async () => {
      vi.mocked(classesApi.create).mockResolvedValue(mockClass);

      renderCreate();
      const labelInput = screen.getByLabelText(/label/i);
      fireEvent.input(labelInput, { target: { value: "Person" } });

      await waitFor(() => {
        const identifierInput = screen.getByLabelText(/identifier/i) as HTMLInputElement;
        expect(identifierInput.value).toBe("person");
      });

      fireEvent.click(screen.getByRole("button", { name: /create class/i }));

      await waitFor(() => {
        expect(classesApi.create).toHaveBeenCalledWith("proj-1", expect.objectContaining({
          label: "Person",
          identifier: "person",
        }));
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    it("calls onCancel when Cancel clicked", () => {
      renderCreate();
      fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
      expect(mockOnCancel).toHaveBeenCalled();
    });

    it("shows error on 409 conflict during create", async () => {
      vi.mocked(classesApi.create).mockRejectedValue(new ApiError(409, "Conflict"));

      renderCreate();
      const labelInput = screen.getByLabelText(/label/i);
      fireEvent.input(labelInput, { target: { value: "Person" } });

      await waitFor(() => {
        expect((screen.getByLabelText(/identifier/i) as HTMLInputElement).value).toBe("person");
      });

      fireEvent.click(screen.getByRole("button", { name: /create class/i }));

      await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent(/identifier already exists/i);
      });
    });

  });
});
