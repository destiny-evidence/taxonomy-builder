import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { SchemeForm } from "../../../src/components/schemes/SchemeForm";
import { schemesApi } from "../../../src/api/schemes";
import type { ConceptScheme } from "../../../src/types/models";

vi.mock("../../../src/api/schemes");

const existingScheme: ConceptScheme = {
  id: "scheme-1",
  project_id: "proj-1",
  title: "Animals",
  description: "Animal taxonomy",
  scope_note: "Use to classify the species studied, not the study setting",
  uri: "http://example.org/animals",
  position: 0,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

describe("SchemeForm", () => {
  const defaultProps = {
    projectId: "proj-1",
    onSuccess: vi.fn(),
    onCancel: vi.fn(),
  };

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("populates scope note from existing scheme", () => {
    render(<SchemeForm {...defaultProps} scheme={existingScheme} />);

    expect(screen.getByLabelText("Scope Note")).toHaveValue(
      "Use to classify the species studied, not the study setting",
    );
  });

  it("sends scope note when creating a scheme", async () => {
    vi.mocked(schemesApi.create).mockResolvedValue(existingScheme);
    render(<SchemeForm {...defaultProps} />);

    fireEvent.input(screen.getByLabelText(/title/i), { target: { value: "Animals" } });
    fireEvent.input(screen.getByLabelText("Scope Note"), {
      target: { value: "Use to classify the species studied, not the study setting" },
    });
    fireEvent.click(screen.getByRole("button", { name: /create scheme/i }));

    await waitFor(() => {
      expect(schemesApi.create).toHaveBeenCalledWith("proj-1", {
        title: "Animals",
        description: null,
        scope_note: "Use to classify the species studied, not the study setting",
        uri: null,
      });
    });
  });

  it("sends null scope note when left empty", async () => {
    vi.mocked(schemesApi.create).mockResolvedValue(existingScheme);
    render(<SchemeForm {...defaultProps} />);

    fireEvent.input(screen.getByLabelText(/title/i), { target: { value: "Animals" } });
    fireEvent.click(screen.getByRole("button", { name: /create scheme/i }));

    await waitFor(() => {
      expect(schemesApi.create).toHaveBeenCalledWith(
        "proj-1",
        expect.objectContaining({ scope_note: null }),
      );
    });
  });
});
