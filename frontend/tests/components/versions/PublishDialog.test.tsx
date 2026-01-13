import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { PublishDialog } from "../../../src/components/versions/PublishDialog";
import * as versionsApi from "../../../src/api/versions";

vi.mock("../../../src/api/versions");

// Mock HTMLDialogElement methods for jsdom
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = vi.fn();
  HTMLDialogElement.prototype.close = vi.fn();
});

describe("PublishDialog", () => {
  const defaultProps = {
    isOpen: true,
    schemeId: "test-scheme-123",
    onClose: vi.fn(),
    onPublished: vi.fn(),
  };

  afterEach(() => {
    vi.restoreAllMocks();
    vi.resetAllMocks();
  });

  it("renders version label input", () => {
    render(<PublishDialog {...defaultProps} />);

    expect(screen.getByLabelText(/version label/i)).toBeInTheDocument();
  });

  it("renders notes textarea", () => {
    render(<PublishDialog {...defaultProps} />);

    expect(screen.getByLabelText(/notes/i)).toBeInTheDocument();
  });

  it("disables publish button when version label is empty", () => {
    render(<PublishDialog {...defaultProps} />);

    const publishButton = screen.getByText("Publish");
    expect(publishButton).toBeDisabled();
  });

  it("enables publish button when version label is entered", () => {
    render(<PublishDialog {...defaultProps} />);

    const input = screen.getByLabelText(/version label/i);
    fireEvent.input(input, { target: { value: "1.0" } });

    const publishButton = screen.getByText("Publish");
    expect(publishButton).not.toBeDisabled();
  });

  it("calls publishVersion API on form submit", async () => {
    vi.mocked(versionsApi.publishVersion).mockResolvedValue({
      id: "version-1",
      scheme_id: "test-scheme-123",
      version_label: "1.0",
      published_at: "2024-01-15T10:30:00Z",
      snapshot: {},
      notes: "Initial release",
    });

    render(<PublishDialog {...defaultProps} />);

    const input = screen.getByLabelText(/version label/i);
    fireEvent.input(input, { target: { value: "1.0" } });

    const notesInput = screen.getByLabelText(/notes/i);
    fireEvent.input(notesInput, { target: { value: "Initial release" } });

    const publishButton = screen.getByText("Publish");
    fireEvent.click(publishButton);

    await waitFor(() => {
      expect(versionsApi.publishVersion).toHaveBeenCalledWith(
        "test-scheme-123",
        { version_label: "1.0", notes: "Initial release" }
      );
    });
  });

  it("calls onPublished and onClose after successful publish", async () => {
    const onPublished = vi.fn();
    const onClose = vi.fn();

    vi.mocked(versionsApi.publishVersion).mockResolvedValue({
      id: "version-1",
      scheme_id: "test-scheme-123",
      version_label: "1.0",
      published_at: "2024-01-15T10:30:00Z",
      snapshot: {},
      notes: null,
    });

    render(
      <PublishDialog
        {...defaultProps}
        onPublished={onPublished}
        onClose={onClose}
      />
    );

    const input = screen.getByLabelText(/version label/i);
    fireEvent.input(input, { target: { value: "1.0" } });

    const publishButton = screen.getByText("Publish");
    fireEvent.click(publishButton);

    await waitFor(() => {
      expect(onPublished).toHaveBeenCalled();
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("displays error message on publish failure", async () => {
    vi.mocked(versionsApi.publishVersion).mockRejectedValue(
      new Error("Version already exists")
    );

    render(<PublishDialog {...defaultProps} />);

    const input = screen.getByLabelText(/version label/i);
    fireEvent.input(input, { target: { value: "1.0" } });

    const publishButton = screen.getByText("Publish");
    fireEvent.click(publishButton);

    await waitFor(() => {
      expect(screen.getByText(/failed to publish/i)).toBeInTheDocument();
    });
  });

  it("calls onClose when cancel button clicked", () => {
    const onClose = vi.fn();

    render(<PublishDialog {...defaultProps} onClose={onClose} />);

    const cancelButton = screen.getByText("Cancel");
    fireEvent.click(cancelButton);

    expect(onClose).toHaveBeenCalled();
  });
});
