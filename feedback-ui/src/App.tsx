import { useEffect } from "preact/hooks";
import { initAuth } from "./api/auth";
import { authInitialized } from "./state/auth";
import { AppShell } from "./components/layout/AppShell";

export function App() {
  useEffect(() => {
    initAuth();
  }, []);

  if (!authInitialized.value) {
    return <div style="display:flex;align-items:center;justify-content:center;height:100vh">Loading...</div>;
  }

  return <AppShell />;
}
