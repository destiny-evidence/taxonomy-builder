import { isAuthenticated, userDisplayName } from "../../state/auth";
import { login, logout } from "../../api/auth";

export function AuthStatus() {
  if (isAuthenticated.value) {
    return (
      <div class="auth-status">
        <span class="auth-status__name">{userDisplayName.value}</span>
        <button class="auth-status__btn" onClick={logout}>
          Sign out
        </button>
      </div>
    );
  }

  return (
    <button class="auth-status__btn" onClick={login}>
      Sign in
    </button>
  );
}
