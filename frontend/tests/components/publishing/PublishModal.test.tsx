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
  suggested_pre_release_version: "2.0-pre1",
  latest_version: "1.0",
  latest_pre_release_version: null,
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
  suggested_pre_release_version: null,
  latest_version: null,
  latest_pre_release_version: null,
};

const mockPreviewFirstPublish: publishingApi.PublishPreview = {
  validation: { valid: true, errors: [] },
  diff: null,
  content_summary: { schemes: 2, concepts: 10, properties: 3 },
  suggested_version: "1.0",
  suggested_pre_release_version: "1.0-pre1",
  latest_version: null,
  latest_pre_release_version: null,
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

    it("renders diff sections as collapsible details with grouped counts", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        const details = document.querySelectorAll("details.publish-modal__diff-section");
        expect(details.length).toBe(3);
      });

      expect(screen.getByText(/Added \(1\).*1 concept/)).toBeInTheDocument();
      expect(screen.getByText(/Modified \(1\).*1 concept/)).toBeInTheDocument();
      expect(screen.getByText(/Removed \(1\).*1 concept/)).toBeInTheDocument();
    });

    it("shows field-level changes for modified items", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("definition")).toBeInTheDocument();
        expect(screen.getByText("old def")).toBeInTheDocument();
        expect(screen.getByText("new def")).toBeInTheDocument();
      });
    });

    it("shows info icon next to pre-release checkbox", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        const infoIcon = document.querySelector(".publish-modal__info-icon");
        expect(infoIcon).toBeInTheDocument();
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

    it("pre-fills version input with suggested version", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        const input = screen.getByLabelText("Version") as HTMLInputElement;
        expect(input.value).toBe("1.1");
      });
    });

    it("switches version to pre-release suggestion when checkbox is checked", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(
          (screen.getByLabelText("Version") as HTMLInputElement).value
        ).toBe("1.1");
      });

      fireEvent.click(screen.getByLabelText("Pre-release"));

      // Input shows base version, suffix is shown separately
      expect(
        (screen.getByLabelText("Version") as HTMLInputElement).value
      ).toBe("2.0");
      expect(screen.getByText("-pre1")).toBeInTheDocument();
    });

    it("allows manual version override", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );
      vi.mocked(publishingApi.publishingApi.publish).mockResolvedValue({
        id: "ver-custom",
        project_id: "project-123",
        version: "3.0",
        title: "Custom version",
        notes: null,
        finalized: true,
        published_at: "2026-02-18T10:00:00Z",
        publisher: "Bob",
        latest: true,
        previous_version_id: "ver-2",
      });

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByLabelText("Version")).toBeInTheDocument();
      });

      fireEvent.input(screen.getByLabelText("Version"), {
        target: { value: "3.0" },
      });
      fireEvent.input(screen.getByLabelText(/Title/), {
        target: { value: "Custom version" },
      });

      const publishBtn = screen.getAllByText("Publish").find(
        (el) => el.classList.contains("btn")
      )!;
      fireEvent.click(publishBtn);

      // Confirm step
      fireEvent.click(screen.getByText("Confirm & Publish"));

      await waitFor(() => {
        expect(publishingApi.publishingApi.publish).toHaveBeenCalledWith(
          "project-123",
          expect.objectContaining({
            version: "3.0",
            title: "Custom version",
          })
        );
      });
    });

    it("resets version to suggestion when checkbox is toggled", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByLabelText("Version")).toBeInTheDocument();
      });

      // Manually edit version
      fireEvent.input(screen.getByLabelText("Version"), {
        target: { value: "99.99" },
      });
      expect(
        (screen.getByLabelText("Version") as HTMLInputElement).value
      ).toBe("99.99");

      // Toggle pre-release on — resets to pre-release suggestion (base only in input)
      fireEvent.click(screen.getByLabelText("Pre-release"));
      expect(
        (screen.getByLabelText("Version") as HTMLInputElement).value
      ).toBe("2.0");
      expect(screen.getByText("-pre1")).toBeInTheDocument();

      // Toggle pre-release off — resets to release suggestion
      fireEvent.click(screen.getByLabelText("Pre-release"));
      expect(
        (screen.getByLabelText("Version") as HTMLInputElement).value
      ).toBe("1.1");
    });

    it("shows recent versions near version input", async () => {
      const previewWithPreRelease: publishingApi.PublishPreview = {
        ...mockPreview,
        latest_version: "1.0",
        latest_pre_release_version: "1.1-pre1",
      };

      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        previewWithPreRelease
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        const hint = screen.getByText(/Recent:/);
        expect(hint).toBeInTheDocument();
        expect(hint.textContent).toContain("1.1-pre1");
        expect(hint.textContent).toContain("1.0");
      });
    });

    it("hides recent versions hint when no versions exist", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreviewFirstPublish
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue([]);

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByLabelText("Version")).toBeInTheDocument();
      });

      expect(screen.queryByText(/Recent:/)).not.toBeInTheDocument();
    });

    it("disables Publish button when title is empty", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        const publishBtn = screen.getAllByText("Publish").find(
          (el) => el.classList.contains("btn")
        )!;
        expect(publishBtn).toBeDisabled();
      });
    });

    it("shows format hint and disables Publish for invalid version format", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByLabelText("Version")).toBeInTheDocument();
      });

      fireEvent.input(screen.getByLabelText("Version"), {
        target: { value: "banana" },
      });
      fireEvent.input(screen.getByLabelText(/Title/), {
        target: { value: "A title" },
      });

      expect(screen.getByText(/Version must be/)).toBeInTheDocument();

      const publishBtn = screen.getAllByText("Publish").find(
        (el) => el.classList.contains("btn")
      )!;
      expect(publishBtn).toBeDisabled();
    });

    it("disables Publish button when validation fails", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreviewInvalid
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue([]);

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        const publishBtn = screen.getAllByText("Publish").find(
          (el) => el.classList.contains("btn")
        )!;
        expect(publishBtn).toBeDisabled();
      });
    });
  });

  describe("confirmation step", () => {
    it("shows confirmation step when Publish is clicked", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/Title/)).toBeInTheDocument();
      });

      fireEvent.input(screen.getByLabelText(/Title/), {
        target: { value: "New release" },
      });

      const publishBtn = screen.getAllByText("Publish").find(
        (el) => el.classList.contains("btn")
      )!;
      fireEvent.click(publishBtn);

      expect(screen.getByText(/cannot be changed/i)).toBeInTheDocument();
      expect(screen.getByText("1.1")).toBeInTheDocument();
      expect(screen.getByText(/New release/)).toBeInTheDocument();
      expect(publishingApi.publishingApi.publish).not.toHaveBeenCalled();
    });

    it("returns to preview when Back is clicked on confirmation", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/Title/)).toBeInTheDocument();
      });

      fireEvent.input(screen.getByLabelText(/Title/), {
        target: { value: "New release" },
      });

      const publishBtn = screen.getAllByText("Publish").find(
        (el) => el.classList.contains("btn")
      )!;
      fireEvent.click(publishBtn);

      expect(screen.getByText(/cannot be changed/i)).toBeInTheDocument();

      fireEvent.click(screen.getByText("Back"));

      expect(screen.getByLabelText(/Title/)).toBeInTheDocument();
    });
  });

  describe("publishing", () => {
    it("calls publish with correct data for a release", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );
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

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/Title/)).toBeInTheDocument();
      });

      fireEvent.input(screen.getByLabelText(/Title/), {
        target: { value: "New release" },
      });

      const publishBtn = screen.getAllByText("Publish").find(
        (el) => el.classList.contains("btn")
      )!;
      fireEvent.click(publishBtn);

      // Confirm step
      fireEvent.click(screen.getByText("Confirm & Publish"));

      await waitFor(() => {
        expect(publishingApi.publishingApi.publish).toHaveBeenCalledWith(
          "project-123",
          expect.objectContaining({
            version: "1.1",
            title: "New release",
            pre_release: false,
          })
        );
      });
    });

    it("calls publish with pre_release=true when checkbox is checked", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );
      vi.mocked(publishingApi.publishingApi.publish).mockResolvedValue({
        id: "ver-pre",
        project_id: "project-123",
        version: "2.0-pre1",
        title: "Pre-release",
        notes: null,
        finalized: false,
        published_at: "2026-02-18T10:00:00Z",
        publisher: "Bob",
        latest: false,
        previous_version_id: "ver-2",
      });

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByLabelText("Pre-release")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByLabelText("Pre-release"));
      fireEvent.input(screen.getByLabelText(/Title/), {
        target: { value: "Pre-release" },
      });

      const publishBtn = screen.getAllByText("Publish").find(
        (el) => el.classList.contains("btn")
      )!;
      fireEvent.click(publishBtn);

      // Confirm step
      fireEvent.click(screen.getByText("Confirm & Publish"));

      await waitFor(() => {
        expect(publishingApi.publishingApi.publish).toHaveBeenCalledWith(
          "project-123",
          expect.objectContaining({
            version: "2.0-pre1",
            title: "Pre-release",
            pre_release: true,
          })
        );
      });
    });

    it("shows success step after publishing", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );
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

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/Title/)).toBeInTheDocument();
      });

      fireEvent.input(screen.getByLabelText(/Title/), {
        target: { value: "New release" },
      });
      const publishBtn = screen.getAllByText("Publish").find(
        (el) => el.classList.contains("btn")
      )!;
      fireEvent.click(publishBtn);

      // Confirm step
      fireEvent.click(screen.getByText("Confirm & Publish"));

      await waitFor(() => {
        expect(screen.getByText(/1\.1/)).toBeInTheDocument();
        expect(screen.getByText(/published successfully/)).toBeInTheDocument();
      });
    });

    it("shows pre-release success message", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );
      vi.mocked(publishingApi.publishingApi.publish).mockResolvedValue({
        id: "ver-pre",
        project_id: "project-123",
        version: "2.0-pre1",
        title: "Pre-release",
        notes: null,
        finalized: false,
        published_at: "2026-02-18T10:00:00Z",
        publisher: "Bob",
        latest: false,
        previous_version_id: "ver-2",
      });

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByLabelText("Pre-release")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByLabelText("Pre-release"));
      fireEvent.input(screen.getByLabelText(/Title/), {
        target: { value: "Pre-release" },
      });
      const publishBtn = screen.getAllByText("Publish").find(
        (el) => el.classList.contains("btn")
      )!;
      fireEvent.click(publishBtn);

      // Confirm step
      fireEvent.click(screen.getByText("Confirm & Publish"));

      await waitFor(() => {
        expect(screen.getByText(/published as pre-release/)).toBeInTheDocument();
      });
    });

    it("shows error when publish fails", async () => {
      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        mockVersions
      );
      vi.mocked(publishingApi.publishingApi.publish).mockRejectedValue(
        new Error("Version already exists")
      );

      render(<PublishModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/Title/)).toBeInTheDocument();
      });

      fireEvent.input(screen.getByLabelText(/Title/), {
        target: { value: "New release" },
      });
      const publishBtn = screen.getAllByText("Publish").find(
        (el) => el.classList.contains("btn")
      )!;
      fireEvent.click(publishBtn);

      // Confirm step
      fireEvent.click(screen.getByText("Confirm & Publish"));

      await waitFor(() => {
        expect(
          screen.getByText(/Version already exists/)
        ).toBeInTheDocument();
      });
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

    it("shows pre-release badge for non-finalized versions", async () => {
      const versionsWithPreRelease: publishingApi.PublishedVersionRead[] = [
        {
          id: "ver-pre",
          project_id: "project-123",
          version: "1.1-pre1",
          title: "Pre-release",
          notes: null,
          finalized: false,
          published_at: "2026-02-18T10:00:00Z",
          publisher: "Bob",
          latest: false,
          previous_version_id: "ver-2",
        },
        ...mockVersions,
      ];

      vi.mocked(publishingApi.publishingApi.getPreview).mockResolvedValue(
        mockPreview
      );
      vi.mocked(publishingApi.publishingApi.listVersions).mockResolvedValue(
        versionsWithPreRelease
      );

      render(<PublishModal {...defaultProps} initialTab="versions" />);

      await waitFor(() => {
        expect(screen.getByText("1.1-pre1")).toBeInTheDocument();
        expect(screen.getByText("pre-release")).toBeInTheDocument();
      });
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
