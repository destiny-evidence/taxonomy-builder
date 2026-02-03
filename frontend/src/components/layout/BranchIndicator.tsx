import "./BranchIndicator.css";

// Branch info is set at build/dev time via environment variables
// configured by the worktree setup script
const BRANCH_NAME = import.meta.env.VITE_BRANCH_NAME as string | undefined;
const BRANCH_COLOR = import.meta.env.VITE_BRANCH_COLOR as string | undefined;

export function BranchIndicator() {
  // Don't render anything if branch info is not set
  if (!BRANCH_NAME) {
    return null;
  }

  return (
    <div class="branch-indicator" style={{ "--branch-color": BRANCH_COLOR }}>
      <span class="branch-indicator__icon">
        <svg
          width="14"
          height="14"
          viewBox="0 0 16 16"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fill-rule="evenodd"
            d="M11.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122V6A2.5 2.5 0 0110 8.5H6a1 1 0 00-1 1v1.128a2.251 2.251 0 11-1.5 0V5.372a2.25 2.25 0 111.5 0v1.836A2.492 2.492 0 016 7h4a1 1 0 001-1v-.628A2.25 2.25 0 019.5 3.25zM4.25 12a.75.75 0 100 1.5.75.75 0 000-1.5zM3.5 3.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0z"
          />
        </svg>
      </span>
      <span class="branch-indicator__name">{BRANCH_NAME}</span>
    </div>
  );
}
