import { useEffect } from "preact/hooks";
import { initAuth } from "./api/auth";
import { authInitialized, isAuthenticated } from "./state/auth";
import { loadOwnFeedback } from "./state/feedback";
import { AppShell } from "./components/layout/AppShell";

export function App() {
  useEffect(() => {
    initAuth();
  }, []);

  // Load own feedback when authenticated
  useEffect(() => {
    if (isAuthenticated.value) {
      loadOwnFeedback();
    }
  }, [isAuthenticated.value]);

  if (!authInitialized.value) {
    return (
      <div style="display:flex;align-items:center;justify-content:center;height:100vh">
        Loading...
      </div>
    );
  }

  return <AppShell />;
}
