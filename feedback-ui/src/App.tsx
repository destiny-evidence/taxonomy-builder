import { useEffect } from "preact/hooks";
import { initAuth, login, logout } from "./api/auth";
import { authInitialized, authLoading, isAuthenticated, userDisplayName } from "./state/auth";

export function App() {
  useEffect(() => {
    initAuth();
  }, []);

  if (!authInitialized.value) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h1>Feedback</h1>
      {authLoading.value && <p>Authenticating...</p>}
      {isAuthenticated.value ? (
        <div>
          <p>Signed in as {userDisplayName.value}</p>
          <button onClick={logout}>Sign out</button>
        </div>
      ) : (
        <div>
          <p>Not signed in (public access)</p>
          <button onClick={login}>Sign in</button>
        </div>
      )}
    </div>
  );
}
