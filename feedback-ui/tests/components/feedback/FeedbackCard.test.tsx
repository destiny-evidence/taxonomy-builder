import { render, screen } from "@testing-library/preact";
import { describe, it, expect, vi } from "vitest";

vi.mock("../../../src/state/feedback", () => ({
  deleteFeedback: vi.fn(),
}));

import { FeedbackCard } from "../../../src/components/feedback/FeedbackCard";
import type { FeedbackRead } from "../../../src/api/feedback";

function makeFeedback(overrides: Partial<FeedbackRead> = {}): FeedbackRead {
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
    ...overrides,
  };
}

describe("FeedbackCard", () => {
  it("renders every response in the thread", () => {
    const feedback = makeFeedback({
      responses: [
        {
          author: "Vocabulary manager",
          content: "First answer",
          created_at: new Date().toISOString(),
        },
        {
          author: "Vocabulary manager",
          content: "Second answer",
          created_at: new Date().toISOString(),
        },
      ],
    });

    render(<FeedbackCard feedback={feedback} />);

    expect(screen.getByText("First answer")).toBeInTheDocument();
    expect(screen.getByText("Second answer")).toBeInTheDocument();
    expect(screen.getAllByText(/Vocabulary manager/)).toHaveLength(2);
  });
});
