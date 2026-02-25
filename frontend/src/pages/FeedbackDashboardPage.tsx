import { useEffect } from "preact/hooks";
import { Breadcrumb } from "../components/layout/Breadcrumb";
import { SummaryBar } from "../components/feedback/SummaryBar";
import { FeedbackFilters } from "../components/feedback/FeedbackFilters";
import { ManagerCard } from "../components/feedback/ManagerCard";
import { LoadingSpinner } from "../components/common/LoadingOverlay";
import {
  allFeedback,
  feedbackLoading,
  feedbackError,
  filteredFeedback,
  resetFilters,
} from "../state/feedback";
import { currentProject } from "../state/projects";
import { feedbackManagerApi } from "../api/feedback";
import { projectsApi } from "../api/projects";
import "./FeedbackDashboardPage.css";

interface FeedbackDashboardPageProps {
  path?: string;
  projectId?: string;
}

export function FeedbackDashboardPage({
  projectId,
}: FeedbackDashboardPageProps) {
  useEffect(() => {
    if (!projectId) return;
    loadFeedback(projectId);
    loadProject(projectId);
    return () => {
      resetFilters();
      allFeedback.value = [];
    };
  }, [projectId]);

  async function loadProject(id: string) {
    if (currentProject.value?.id === id) return;
    try {
      currentProject.value = await projectsApi.get(id);
    } catch {
      // Project name just won't show in breadcrumb
    }
  }

  async function loadFeedback(id: string) {
    feedbackLoading.value = true;
    feedbackError.value = null;
    try {
      allFeedback.value = await feedbackManagerApi.listAll(id);
    } catch (err) {
      feedbackError.value =
        err instanceof Error ? err.message : "Failed to load feedback";
    } finally {
      feedbackLoading.value = false;
    }
  }

  if (!projectId) {
    return <div>Project ID required</div>;
  }

  const projectName = currentProject.value?.name ?? "Project";
  const items = filteredFeedback.value;

  return (
    <div class="feedback-dashboard">
      <Breadcrumb
        items={[
          { label: "Projects", href: "/projects" },
          { label: projectName, href: `/projects/${projectId}` },
          { label: "Feedback" },
        ]}
      />
      <div class="feedback-dashboard__content">
        <div class="feedback-dashboard__header">
          <h1 class="feedback-dashboard__title">Feedback</h1>
          <a
            href={`/projects/${projectId}`}
            class="feedback-dashboard__back"
          >
            Back to workspace
          </a>
        </div>

        {feedbackLoading.value ? (
          <LoadingSpinner />
        ) : feedbackError.value ? (
          <div class="feedback-dashboard__error">{feedbackError.value}</div>
        ) : (
          <>
            <SummaryBar />
            <FeedbackFilters />
            {items.length === 0 ? (
              <div class="feedback-dashboard__empty">
                {allFeedback.value.length === 0
                  ? "No feedback submitted yet."
                  : "No feedback matches the current filters."}
              </div>
            ) : (
              <div class="feedback-dashboard__list">
                {items.map((fb) => (
                  <ManagerCard
                    key={fb.id}
                    item={fb}
                    projectId={projectId}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
