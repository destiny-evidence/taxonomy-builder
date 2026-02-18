import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { CommentsSection } from "../../../src/components/concepts/CommentsSection";
import { commentsApi } from "../../../src/api/comments";
import type { Comment, User } from "../../../src/types/models";

vi.mock("../../../src/api/comments", () => ({
  commentsApi: {
    listForConcept: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
    resolve: vi.fn(),
    unresolve: vi.fn(),
  },
}));

function mockComment(id: string, user: User, content: string, resolver: User | null = null, can_delete = false): Comment {
  return {
    id: id,
    concept_id: "concept-1",
    user_id: user.id,
    parent_comment_id: null,
    content,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    resolved_at: resolver ? new Date().toISOString() : null,
    resolved_by: resolver?.id ?? null,
    resolver,
    user,
    can_delete,
    replies: [],
  };
}

const mockUser1: User = {
  id: "user-1",
  display_name: "John"
}

const mockUser2: User = {
  id: "user-2",
  display_name: "Jimmy"
}

const mockComments: Comment[] = [
  { ...mockComment("comment-1", mockUser1, "First unresolved comment", null, true), replies: [
    mockComment("reply-1", mockUser2, "Reply to first comment"),
  ]},
  mockComment("comment-2", mockUser2, "Second unresolved comment"),
  mockComment("comment-3", mockUser1, "Resolved comment", mockUser2, true),
];

async function renderExpanded() {
  render(<CommentsSection conceptId="concept-1" />);
  await waitFor(() => {
    expect(commentsApi.listForConcept).toHaveBeenCalled();
  });
  fireEvent.click(screen.getByText(/Comments/));
}

describe("CommentsSection", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(commentsApi.listForConcept).mockResolvedValue(mockComments);
  });

  describe("filtering", () => {
    it("should show only unresolved comments by default", async () => {
      await renderExpanded();

      expect(screen.getByText("First unresolved comment")).toBeInTheDocument();
      expect(screen.getByText("Second unresolved comment")).toBeInTheDocument();
      expect(screen.queryByText("Resolved comment")).not.toBeInTheDocument();
    });

    it("should show all comments when 'All' filter is selected", async () => {
      await renderExpanded();

      fireEvent.click(screen.getByText("All"));

      expect(screen.getByText("First unresolved comment")).toBeInTheDocument();
      expect(screen.getByText("Second unresolved comment")).toBeInTheDocument();
      expect(screen.getByText("Resolved comment")).toBeInTheDocument();
    });

    it("should show only resolved comments when 'Resolved' filter is selected", async () => {
      await renderExpanded();

      fireEvent.click(screen.getByText("Resolved"));

      expect(screen.queryByText("First unresolved comment")).not.toBeInTheDocument();
      expect(screen.queryByText("Second unresolved comment")).not.toBeInTheDocument();
      expect(screen.getByText("Resolved comment")).toBeInTheDocument();
    });
  });
});
