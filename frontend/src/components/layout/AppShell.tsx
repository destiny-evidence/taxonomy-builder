import type { ComponentChildren } from "preact";
import { isAuthenticated, userDisplayName } from "../../state/auth";
import { logout } from "../../api/auth";
import { BranchIndicator } from "./BranchIndicator";
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
        <div class="app-header__left">
          <a href="/" class="app-header__logo">
            Taxonomy Builder
          </a>
          <BranchIndicator />
        </div>
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
