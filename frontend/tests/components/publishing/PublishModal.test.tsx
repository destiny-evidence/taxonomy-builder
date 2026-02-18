import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { PublishModal } from "../../../src/components/publishing/PublishModal";
import * as publishingApi from "../../../src/api/publishing";

beforeEach(() => {
  HTMLDialogElement.prototype.showModal = vi.fn();
  HTMLDialogElement.prototype.close = vi.fn();
});

vi.mock("../../../src/api/publishing", () => ({
  publishingApi: {
    getPreview: vi.fn(),
    publish: vi.fn(),
    listVersions: vi.fn(),
    finalizeVersion: vi.fn(),
    deleteDraft: vi.fn(),
  },
}));

const mockPreview: publishingApi.PublishPreview = {
  validation: { valid: true, errors: [] },
  diff: {
    added: [
      { id: "c1", uri: null, label: "New Concept", entity_type: "concept" },
    ],
    modified: [
      {
        id: "c2",
        label: "Changed Concept",
        entity_type: "concept",
        changes: [{ field: "definition", old: "old def", new: "new def" }],
      },
    ],
    removed: [
      { id: "c3", uri: null, label: "Removed Concept", entity_type: "concept" },
    ],
  },
  content_summary: { schemes: 2, concepts: 10, properties: 3 },
  suggested_version: "1.1",
};

const mockPreviewInvalid: publishingApi.PublishPreview = {
  validation: {
    valid: false,
    errors: [
      {
        code: "scheme_missing_uri",
        message: "Scheme 'Test' has no URI.",
        entity_type: "scheme",
        entity_id: "s1",
        entity_label: "Test",
      },
    ],
  },
  diff: null,
  content_summary: { schemes: 1, concepts: 5, properties: 0 },
  suggested_version: null,
};

const mockPreviewFirstPublish: publishingApi.PublishPreview = {
  validation: { valid: true, errors: [] },
  diff: null,
  content_summary: { schemes: 2, concepts: 10, properties: 3 },
  suggested_version: "1.0",
};

const mockVersions: publishingApi.PublishedVersionRead[] = [
  {
    id: "ver-2",
    project_id: "project-123",
    version: "1.0",
    title: "Initial release",
    notes: "First published version",
    finalized: true,
    published_at: "2026-01-15T10:00:00Z",
    publisher: "Alice",
    latest: true,
    previous_version_id: null,
  },
];

describe("PublishModal", () => {
  const defaultProps = {
    isOpen: true,
    projectId: "project-123",
    onClose: vi.fn(),
  };

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("loading state", () => {
    it("shows loading indicator while fetching data", () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockReturnValue(
        new Promise(() => {})
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockReturnValue(
        new Promise(() => {})
      );

      render(<PublishModal {...defaultProps} />);

      expect(screen.getByText(/Loading/i)).toBeInTheDocument();
    });
  });

  describe("preview step", () => {
    it("displays content summary after loading", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText(/2 schemes/)).toBeInTheDocument();
        expect(screen.getByText(/10 concepts/)).toBeInTheDocument();
        expect(screen.getByText(/3 properties/)).toBeInTheDocument();
      });
    });

    it("shows diff sections when changes exist", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("New Concept")).toBeInTheDocument();
        expect(screen.getByText("Changed Concept")).toBeInTheDocument();
        expect(screen.getByText("Removed Concept")).toBeInTheDocument();
      });
    });

    it("shows first version message when diff is null", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreviewFirstPublish
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue([]);

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(
          screen.getByText(/first version/i)
        ).toBeInTheDocument();
      });
    });

    it("displays validation errors when invalid", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreviewInvalid
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue([]);

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(
          screen.getByText(/Scheme 'Test' has no URI/)
        ).toBeInTheDocument();
      });
    });

    it("disables Continue button when validation fails", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreviewInvalid
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue([]);

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Continue")).toBeDisabled();
      });
    });

    it("enables Continue button when validation passes", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Continue")).not.toBeDisabled();
      });
    });

    it("advances to form step when Continue is clicked", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Continue")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Continue"));

      expect(screen.getByLabelText(/Version/)).toBeInTheDocument();
    });
  });

  describe("tabs", () => {
    it("switches between Publish and Versions tabs", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText(/2 schemes/)).toBeInTheDocument();
      });

      const versionsTab = screen.getAllByText("Versions")[0];
      fireEvent.click(versionsTab);

      expect(screen.getByText("1.0")).toBeInTheDocument();
      expect(screen.getByText("Initial release")).toBeInTheDocument();
    });
  });

  describe("form step", () => {
    async function navigateToForm() {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Continue")).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText("Continue"));
    }

    it("pre-fills version with suggested value", async () => {
      await navigateToForm();

      const versionInput = screen.getByLabelText(/Version/) as HTMLInputElement;
      expect(versionInput.value).toBe("1.1");
    });

    it("calls publish with finalized=true when Publish clicked", async () => {
      vi.mocked(publishingApi.publishingApi.publish).mockResolvedValue({
        id: "ver-new",
        project_id: "project-123",
        version: "1.1",
        title: "New release",
        notes: null,
        finalized: true,
        published_at: "2026-02-18T10:00:00Z",
        publisher: "Bob",
        latest: true,
        previous_version_id: "ver-2",
      });

      await navigateToForm();

      const titleInput = screen.getByLabelText(/Title/);
      fireEvent.input(titleInput, { target: { value: "New release" } });

      const publishBtn = screen.getAllByText("Publish").find(
        (el) => el.classList.contains("btn")
      )!;
      fireEvent.click(publishBtn);

      await waitFor(() => {
        expect(publishingApi.publishingApi.publish).toHaveBeenCalledWith(
          "project-123",
          expect.objectContaining({
            version: "1.1",
            title: "New release",
            finalized: true,
          })
        );
      });
    });

    it("calls publish with finalized=false when Save as Draft clicked", async () => {
      vi.mocked(publishingApi.publishingApi.publish).mockResolvedValue({
        id: "ver-draft",
        project_id: "project-123",
        version: "1.1",
        title: "Draft release",
        notes: null,
        finalized: false,
        published_at: null,
        publisher: null,
        latest: false,
        previous_version_id: null,
      });

      await navigateToForm();

      const titleInput = screen.getByLabelText(/Title/);
      fireEvent.input(titleInput, { target: { value: "Draft release" } });

      fireEvent.click(screen.getByText("Save as Draft"));

      await waitFor(() => {
        expect(publishingApi.publishingApi.publish).toHaveBeenCalledWith(
          "project-123",
          expect.objectContaining({
            finalized: false,
          })
        );
      });
    });

    it("disables buttons when version or title is empty", async () => {
      await navigateToForm();

      // Version is pre-filled but title is empty
      const publishBtn = screen.getAllByText("Publish").find(
        (el) => el.classList.contains("btn")
      )!;
      expect(publishBtn).toBeDisabled();
      expect(screen.getByText("Save as Draft")).toBeDisabled();
    });

    it("shows success step after publishing", async () => {
      vi.mocked(publishingApi.publishingApi.publish).mockResolvedValue({
        id: "ver-new",
        project_id: "project-123",
        version: "1.1",
        title: "New release",
        notes: null,
        finalized: true,
        published_at: "2026-02-18T10:00:00Z",
        publisher: "Bob",
        latest: true,
        previous_version_id: "ver-2",
      });

      await navigateToForm();

      fireEvent.input(screen.getByLabelText(/Title/), {
        target: { value: "New release" },
      });
      const publishBtn = screen.getAllByText("Publish").find(
        (el) => el.classList.contains("btn")
      )!;
      fireEvent.click(publishBtn);

      await waitFor(() => {
        expect(screen.getByText(/1\.1/)).toBeInTheDocument();
        expect(screen.getByText(/published successfully/)).toBeInTheDocument();
      });
    });

    it("shows error when publish fails", async () => {
      vi.mocked(publishingApi.publishingApi.publish).mockRejectedValue(
        new Error("Version already exists")
      );

      await navigateToForm();

      fireEvent.input(screen.getByLabelText(/Title/), {
        target: { value: "New release" },
      });
      const publishBtn = screen.getAllByText("Publish").find(
        (el) => el.classList.contains("btn")
      )!;
      fireEvent.click(publishBtn);

      await waitFor(() => {
        expect(
          screen.getByText(/Version already exists/)
        ).toBeInTheDocument();
      });
    });
  });

  describe("draft management", () => {
    const mockDraft: publishingApi.PublishedVersionRead = {
      id: "ver-draft",
      project_id: "project-123",
      version: "1.1",
      title: "Upcoming release",
      notes: "Work in progress",
      finalized: false,
      published_at: null,
      publisher: null,
      latest: false,
      previous_version_id: null,
    };

    it("shows draft panel when draft exists", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue([
        mockDraft,
        ...mockVersions,
      ]);

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText(/Draft: v1\.1/)).toBeInTheDocument();
        expect(screen.getByText("Upcoming release")).toBeInTheDocument();
      });
    });

    it("shows Finalize and Discard buttons for draft", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue([
        mockDraft,
        ...mockVersions,
      ]);

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Finalize")).toBeInTheDocument();
        expect(screen.getByText("Discard")).toBeInTheDocument();
      });
    });

    it("disables Finalize when validation is invalid", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreviewInvalid
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue([
        mockDraft,
      ]);

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Finalize")).toBeDisabled();
      });
    });

    it("calls finalizeVersion when Finalize clicked", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue([
        mockDraft,
        ...mockVersions,
      ]);
      vi.mocked(publishingApi.publishingApi.finalizeVersion).mockResolvedValue({
        ...mockDraft,
        finalized: true,
        published_at: "2026-02-18T10:00:00Z",
      });

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Finalize")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Finalize"));

      await waitFor(() => {
        expect(
          publishingApi.publishingApi.finalizeVersion
        ).toHaveBeenCalledWith("project-123", "ver-draft");
      });
    });

    it("calls deleteDraft when Discard clicked", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue([
        mockDraft,
        ...mockVersions,
      ]);
      vi.mocked(publishingApi.publishingApi.deleteDraft).mockResolvedValue(
        undefined
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Discard")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Discard"));

      await waitFor(() => {
        expect(publishingApi.publishingApi.deleteDraft).toHaveBeenCalledWith(
          "project-123",
          "ver-draft"
        );
      });
    });
  });

  describe("versions tab", () => {
    it("shows empty state when no versions exist", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreviewFirstPublish
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue([]);

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText(/first version/i)).toBeInTheDocument();
      });

      const versionsTab = screen.getAllByText("Versions")[0];
      fireEvent.click(versionsTab);

      expect(screen.getByText(/No published versions/)).toBeInTheDocument();
    });

    it("shows version list with publisher and date", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText(/2 schemes/)).toBeInTheDocument();
      });

      const versionsTab = screen.getAllByText("Versions")[0];
      fireEvent.click(versionsTab);

      expect(screen.getByText("1.0")).toBeInTheDocument();
      expect(screen.getByText("Initial release")).toBeInTheDocument();
      expect(screen.getByText(/Alice/)).toBeInTheDocument();
      expect(screen.getByText("latest")).toBeInTheDocument();
    });
  });

  describe("initialTab", () => {
    it("opens to versions tab when initialTab is versions", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} initialTab="versions" />);

      await waitFor(() => {
        expect(screen.getByText("Initial release")).toBeInTheDocument();
        expect(screen.getByText("1.0")).toBeInTheDocument();
      });
    });
  });

  describe("error handling", () => {
    it("shows error when preview fetch fails", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockRejectedValue(
        new Error("Network error")
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue([]);

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText(/Network error/)).toBeInTheDocument();
      });
    });
  });
});
