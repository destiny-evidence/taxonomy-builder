import { isAuthenticated, userDisplayName } from "../../state/auth";
import { login, logout, register } from "../../api/auth";
import "./AuthStatus.css";

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
    <div class="auth-status">
      <button class="auth-status__btn" onClick={login}>
        Sign in
      </button>
      <button class="auth-status__link" onClick={register}>
        Create account
      </button>
    </div>
  );
}
