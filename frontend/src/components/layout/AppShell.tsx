import type { ComponentChildren } from "preact";
import { isAuthenticated, userDisplayName } from "../../state/auth";
import { logout } from "../../api/auth";
import "./AppShell.css";

interface AppShellProps {
  children: ComponentChildren;
}

export function AppShell({ children }: AppShellProps) {
  const handleLogout = () => {
    logout();
  };

  return (
    <div class="app-shell">
      <header class="app-header">
        <a href="/" class="app-header__logo">
          Taxonomy Builder
        </a>
        {isAuthenticated.value && userDisplayName.value && (
          <div class="app-header__user">
            <span class="app-header__user-name">{userDisplayName.value}</span>
            <button
              type="button"
              class="app-header__logout"
              onClick={handleLogout}
            >
              Sign out
            </button>
          </div>
        )}
      </header>
      <main class="app-main">{children}</main>
    </div>
  );
}
