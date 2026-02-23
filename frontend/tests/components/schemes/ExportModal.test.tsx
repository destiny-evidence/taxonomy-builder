import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { ExportModal } from "../../../src/components/schemes/ExportModal";

// Mock the schemes API
vi.mock("../../../src/api/schemes", async () => {
  const actual = await vi.importActual("../../../src/api/schemes");
  return {
    ...actual,
    schemesApi: {
      exportScheme: vi.fn(),
    },
  };
});

import { schemesApi } from "../../../src/api/schemes";

// Mock HTMLDialogElement methods for jsdom
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = vi.fn();
  HTMLDialogElement.prototype.close = vi.fn();
});

describe("ExportModal", () => {
  const defaultProps = {
    isOpen: true,
    schemeId: "test-scheme-123",
    schemeTitle: "Animal Kingdom",
    onClose: vi.fn(),
  };

  beforeEach(() => {
    // Default: exportScheme resolves with a blob
    vi.mocked(schemesApi.exportScheme).mockResolvedValue(
      new Blob(["content"], { type: "text/turtle" })
    );

    // Mock URL.createObjectURL / revokeObjectURL
    vi.stubGlobal("URL", {
      ...globalThis.URL,
      createObjectURL: vi.fn(() => "blob:mock-url"),
      revokeObjectURL: vi.fn(),
    });

    // Prevent jsdom "Not implemented: navigation" warning from a.click()
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("displays the scheme title", () => {
    render(<ExportModal {...defaultProps} />);

    expect(screen.getByText(/Animal Kingdom/)).toBeInTheDocument();
  });

  it("has Turtle format selected by default", () => {
    render(<ExportModal {...defaultProps} />);

    const turtleRadio = screen.getByDisplayValue("ttl") as HTMLInputElement;
    expect(turtleRadio.checked).toBe(true);
  });

  it("allows selecting different formats", () => {
    render(<ExportModal {...defaultProps} />);

    const xmlRadio = screen.getByDisplayValue("xml") as HTMLInputElement;
    fireEvent.click(xmlRadio);

    expect(xmlRadio.checked).toBe(true);
  });

  it("calls exportScheme with correct params on download", async () => {
    render(<ExportModal {...defaultProps} />);

    const downloadButton = screen.getByText("Download");
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(schemesApi.exportScheme).toHaveBeenCalledWith(
        "test-scheme-123",
        "ttl"
      );
    });
  });

  it("uses selected format in export call", async () => {
    render(<ExportModal {...defaultProps} />);

    const jsonldRadio = screen.getByDisplayValue("jsonld");
    fireEvent.click(jsonldRadio);

    const downloadButton = screen.getByText("Download");
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(schemesApi.exportScheme).toHaveBeenCalledWith(
        "test-scheme-123",
        "jsonld"
      );
    });
  });

  it("calls onClose after download completes", async () => {
    const onClose = vi.fn();

    render(<ExportModal {...defaultProps} onClose={onClose} />);

    const downloadButton = screen.getByText("Download");
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("calls onClose when cancel button clicked", () => {
    const onClose = vi.fn();

    render(<ExportModal {...defaultProps} onClose={onClose} />);

    const cancelButton = screen.getByText("Cancel");
    fireEvent.click(cancelButton);

    expect(onClose).toHaveBeenCalled();
  });

  it("shows all three format options", () => {
    render(<ExportModal {...defaultProps} />);

    expect(screen.getByText("Turtle (.ttl)")).toBeInTheDocument();
    expect(screen.getByText("RDF/XML (.rdf)")).toBeInTheDocument();
    expect(screen.getByText("JSON-LD (.jsonld)")).toBeInTheDocument();
  });
});
