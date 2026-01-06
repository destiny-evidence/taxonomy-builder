import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { ExportModal } from "../../../src/components/schemes/ExportModal";

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

  it("calls window.open with correct URL on download", () => {
    const mockOpen = vi.fn();
    vi.stubGlobal("open", mockOpen);

    render(<ExportModal {...defaultProps} />);

    const downloadButton = screen.getByText("Download");
    fireEvent.click(downloadButton);

    expect(mockOpen).toHaveBeenCalledWith(
      "/api/schemes/test-scheme-123/export?format=ttl",
      "_blank"
    );
  });

  it("uses selected format in download URL", () => {
    const mockOpen = vi.fn();
    vi.stubGlobal("open", mockOpen);

    render(<ExportModal {...defaultProps} />);

    const jsonldRadio = screen.getByDisplayValue("jsonld");
    fireEvent.click(jsonldRadio);

    const downloadButton = screen.getByText("Download");
    fireEvent.click(downloadButton);

    expect(mockOpen).toHaveBeenCalledWith(
      "/api/schemes/test-scheme-123/export?format=jsonld",
      "_blank"
    );
  });

  it("calls onClose after download", () => {
    vi.stubGlobal("open", vi.fn());
    const onClose = vi.fn();

    render(<ExportModal {...defaultProps} onClose={onClose} />);

    const downloadButton = screen.getByText("Download");
    fireEvent.click(downloadButton);

    expect(onClose).toHaveBeenCalled();
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
