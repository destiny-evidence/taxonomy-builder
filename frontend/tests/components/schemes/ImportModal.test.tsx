import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { ImportModal } from "../../../src/components/schemes/ImportModal";
import * as schemesApi from "../../../src/api/schemes";

// Mock HTMLDialogElement methods for jsdom
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = vi.fn();
  HTMLDialogElement.prototype.close = vi.fn();
});

// Mock the schemesApi
vi.mock("../../../src/api/schemes", () => ({
  schemesApi: {
    previewImport: vi.fn(),
    executeImport: vi.fn(),
  },
}));

describe("ImportModal", () => {
  const defaultProps = {
    isOpen: true,
    projectId: "test-project-123",
    onClose: vi.fn(),
    onSuccess: vi.fn(),
  };

  const mockPreview: schemesApi.ImportPreview = {
    valid: true,
    schemes: [
      {
        title: "Taxonomy A",
        description: "First taxonomy",
        uri: "http://example.org/taxonomy-a",
        concepts_count: 42,
        relationships_count: 38,
        warnings: [],
      },
      {
        title: "Taxonomy B",
        description: null,
        uri: "http://example.org/taxonomy-b",
        concepts_count: 15,
        relationships_count: 12,
        warnings: ["Concept http://example.org/foo has no prefLabel"],
      },
    ],
    total_concepts_count: 57,
    total_relationships_count: 50,
    errors: [],
  };

  const mockResult: schemesApi.ImportResult = {
    schemes_created: [
      { id: "uuid-1", title: "Taxonomy A", concepts_created: 42 },
      { id: "uuid-2", title: "Taxonomy B", concepts_created: 15 },
    ],
    total_concepts_created: 57,
    total_relationships_created: 50,
  };

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders file input when opened", () => {
    render(<ImportModal {...defaultProps} />);

    expect(screen.getByLabelText(/Select RDF file/i)).toBeInTheDocument();
  });

  it("shows supported file formats", () => {
    render(<ImportModal {...defaultProps} />);

    expect(
      screen.getByText(/Supported formats:.*\.ttl.*\.rdf.*\.jsonld.*\.nt/i)
    ).toBeInTheDocument();
  });

  it("Preview button is disabled until file selected", () => {
    render(<ImportModal {...defaultProps} />);

    const previewButton = screen.getByText("Preview");
    expect(previewButton).toBeDisabled();
  });

  it("Preview button is enabled after file selected", async () => {
    render(<ImportModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/Select RDF file/i);
    const file = new File(["test content"], "test.ttl", {
      type: "text/turtle",
    });
    fireEvent.change(fileInput, { target: { files: [file] } });

    const previewButton = screen.getByText("Preview");
    expect(previewButton).not.toBeDisabled();
  });

  it("calls previewImport API when Preview clicked", async () => {
    vi.mocked(schemesApi.schemesApi.previewImport).mockResolvedValue(
      mockPreview
    );

    render(<ImportModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/Select RDF file/i);
    const file = new File(["test content"], "test.ttl", {
      type: "text/turtle",
    });
    fireEvent.change(fileInput, { target: { files: [file] } });

    const previewButton = screen.getByText("Preview");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(schemesApi.schemesApi.previewImport).toHaveBeenCalledWith(
        "test-project-123",
        file
      );
    });
  });

  it("displays scheme cards with correct counts", async () => {
    vi.mocked(schemesApi.schemesApi.previewImport).mockResolvedValue(
      mockPreview
    );

    render(<ImportModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/Select RDF file/i);
    const file = new File(["test content"], "test.ttl", {
      type: "text/turtle",
    });
    fireEvent.change(fileInput, { target: { files: [file] } });

    const previewButton = screen.getByText("Preview");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Taxonomy A")).toBeInTheDocument();
      expect(screen.getByText("Taxonomy B")).toBeInTheDocument();
    });

    // Check concept counts
    expect(screen.getByText(/42 concepts/)).toBeInTheDocument();
    expect(screen.getByText(/15 concepts/)).toBeInTheDocument();

    // Check relationship counts
    expect(screen.getByText(/38 relationships/)).toBeInTheDocument();
    expect(screen.getByText(/12 relationships/)).toBeInTheDocument();

    // Check totals
    expect(screen.getByText(/57 concepts/)).toBeInTheDocument();
    expect(screen.getByText(/50 relationships/)).toBeInTheDocument();
  });

  it("displays warnings on scheme cards", async () => {
    vi.mocked(schemesApi.schemesApi.previewImport).mockResolvedValue(
      mockPreview
    );

    render(<ImportModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/Select RDF file/i);
    const file = new File(["test content"], "test.ttl", {
      type: "text/turtle",
    });
    fireEvent.change(fileInput, { target: { files: [file] } });

    const previewButton = screen.getByText("Preview");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(
        screen.getByText(/Concept http:\/\/example.org\/foo has no prefLabel/)
      ).toBeInTheDocument();
    });
  });

  it("shows error message when preview fails", async () => {
    vi.mocked(schemesApi.schemesApi.previewImport).mockRejectedValue(
      new Error("Could not parse RDF file")
    );

    render(<ImportModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/Select RDF file/i);
    const file = new File(["invalid content"], "test.ttl", {
      type: "text/turtle",
    });
    fireEvent.change(fileInput, { target: { files: [file] } });

    const previewButton = screen.getByText("Preview");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(
        screen.getByText(/Could not parse RDF file/)
      ).toBeInTheDocument();
    });
  });

  it("Import button calls executeImport API", async () => {
    vi.mocked(schemesApi.schemesApi.previewImport).mockResolvedValue(
      mockPreview
    );
    vi.mocked(schemesApi.schemesApi.executeImport).mockResolvedValue(
      mockResult
    );

    render(<ImportModal {...defaultProps} />);

    // Select file and preview
    const fileInput = screen.getByLabelText(/Select RDF file/i);
    const file = new File(["test content"], "test.ttl", {
      type: "text/turtle",
    });
    fireEvent.change(fileInput, { target: { files: [file] } });

    const previewButton = screen.getByText("Preview");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Taxonomy A")).toBeInTheDocument();
    });

    // Click Import
    const importButton = screen.getByText("Import All");
    fireEvent.click(importButton);

    await waitFor(() => {
      expect(schemesApi.schemesApi.executeImport).toHaveBeenCalledWith(
        "test-project-123",
        file
      );
    });
  });

  it("calls onSuccess callback after successful import", async () => {
    vi.mocked(schemesApi.schemesApi.previewImport).mockResolvedValue(
      mockPreview
    );
    vi.mocked(schemesApi.schemesApi.executeImport).mockResolvedValue(
      mockResult
    );
    const onSuccess = vi.fn();

    render(<ImportModal {...defaultProps} onSuccess={onSuccess} />);

    // Select file and preview
    const fileInput = screen.getByLabelText(/Select RDF file/i);
    const file = new File(["test content"], "test.ttl", {
      type: "text/turtle",
    });
    fireEvent.change(fileInput, { target: { files: [file] } });

    const previewButton = screen.getByText("Preview");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Taxonomy A")).toBeInTheDocument();
    });

    // Click Import
    const importButton = screen.getByText("Import All");
    fireEvent.click(importButton);

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it("displays loading state during preview", async () => {
    let resolvePreview: (value: schemesApi.ImportPreview) => void;
    const previewPromise = new Promise<schemesApi.ImportPreview>((resolve) => {
      resolvePreview = resolve;
    });
    vi.mocked(schemesApi.schemesApi.previewImport).mockReturnValue(
      previewPromise
    );

    render(<ImportModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/Select RDF file/i);
    const file = new File(["test content"], "test.ttl", {
      type: "text/turtle",
    });
    fireEvent.change(fileInput, { target: { files: [file] } });

    const previewButton = screen.getByText("Preview");
    fireEvent.click(previewButton);

    // Should show loading state
    expect(screen.getByText(/Parsing/i)).toBeInTheDocument();

    // Resolve and check loading disappears
    resolvePreview!(mockPreview);
    await waitFor(() => {
      expect(screen.queryByText(/Parsing/i)).not.toBeInTheDocument();
    });
  });

  it("Cancel button calls onClose", async () => {
    const onClose = vi.fn();

    render(<ImportModal {...defaultProps} onClose={onClose} />);

    const cancelButton = screen.getByText("Cancel");
    fireEvent.click(cancelButton);

    expect(onClose).toHaveBeenCalled();
  });

  it("Cancel button in preview step calls onClose", async () => {
    vi.mocked(schemesApi.schemesApi.previewImport).mockResolvedValue(
      mockPreview
    );
    const onClose = vi.fn();

    render(<ImportModal {...defaultProps} onClose={onClose} />);

    // Select file and preview
    const fileInput = screen.getByLabelText(/Select RDF file/i);
    const file = new File(["test content"], "test.ttl", {
      type: "text/turtle",
    });
    fireEvent.change(fileInput, { target: { files: [file] } });

    const previewButton = screen.getByText("Preview");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Taxonomy A")).toBeInTheDocument();
    });

    const cancelButton = screen.getByText("Cancel");
    fireEvent.click(cancelButton);

    expect(onClose).toHaveBeenCalled();
  });

  it("shows scheme descriptions when available", async () => {
    vi.mocked(schemesApi.schemesApi.previewImport).mockResolvedValue(
      mockPreview
    );

    render(<ImportModal {...defaultProps} />);

    const fileInput = screen.getByLabelText(/Select RDF file/i);
    const file = new File(["test content"], "test.ttl", {
      type: "text/turtle",
    });
    fireEvent.change(fileInput, { target: { files: [file] } });

    const previewButton = screen.getByText("Preview");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("First taxonomy")).toBeInTheDocument();
    });
  });

  it("shows success message after import completes", async () => {
    vi.mocked(schemesApi.schemesApi.previewImport).mockResolvedValue(
      mockPreview
    );
    vi.mocked(schemesApi.schemesApi.executeImport).mockResolvedValue(
      mockResult
    );

    render(<ImportModal {...defaultProps} />);

    // Select file and preview
    const fileInput = screen.getByLabelText(/Select RDF file/i);
    const file = new File(["test content"], "test.ttl", {
      type: "text/turtle",
    });
    fireEvent.change(fileInput, { target: { files: [file] } });

    const previewButton = screen.getByText("Preview");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Taxonomy A")).toBeInTheDocument();
    });

    // Click Import
    const importButton = screen.getByText("Import All");
    fireEvent.click(importButton);

    await waitFor(() => {
      expect(
        screen.getByText(/Successfully imported 2 schemes/)
      ).toBeInTheDocument();
    });
  });
});
