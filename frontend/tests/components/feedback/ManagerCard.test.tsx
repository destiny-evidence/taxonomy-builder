import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { ManagerCard } from "../../../src/components/feedback/ManagerCard";
import type { FeedbackManagerRead } from "../../../src/types/models";

vi.mock("../../../src/api/feedback", () => ({
  feedbackManagerApi: {
    respond: vi.fn(),
    resolve: vi.fn(),
    decline: vi.fn(),
  },
}));

vi.mock("../../../src/api/concepts", () => ({
  conceptsApi: { get: vi.fn() },
}));

function mockItem(overrides: Partial<FeedbackManagerRead> = {}): FeedbackManagerRead {
  return {
    id: "fb-1",
    project_id: "proj-1",
    snapshot_version: "1.0",
    entity_type: "concept",
    entity_id: "concept-1",
    entity_label: "Test Concept",
    feedback_type: "unclear_definition",
    content: "Original question",
    status: "responded",
    responses: [],
    created_at: new Date().toISOString(),
    can_delete: false,
    author_name: "Reader",
    ...overrides,
  };
}

describe("ManagerCard", () => {
  it("renders every response in the thread when expanded", () => {
    const item = mockItem({
      responses: [
        {
          content: "First answer",
          created_at: new Date().toISOString(),
          responded_by_name: "Manager A",
        },
        {
          content: "Second answer",
          created_at: new Date().toISOString(),
          responded_by_name: "Manager B",
        },
      ],
    });

    render(<ManagerCard item={item} projectId="proj-1" />);
    fireEvent.click(screen.getByText("Test Concept"));

    expect(screen.getByText("First answer")).toBeInTheDocument();
    expect(screen.getByText("Second answer")).toBeInTheDocument();
    expect(screen.getByText(/by Manager A/)).toBeInTheDocument();
    expect(screen.getByText(/by Manager B/)).toBeInTheDocument();
  });
});
