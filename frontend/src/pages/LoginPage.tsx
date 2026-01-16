import { useEffect } from "preact/hooks";
import { route } from "preact-router";
import { login } from "../api/auth";
import { isAuthenticated } from "../state/auth";
import { Button } from "../components/common/Button";
import "./LoginPage.css";

interface LoginPageProps {
  path?: string;
}

export function LoginPage({}: LoginPageProps) {
  // Redirect to home if already authenticated
  useEffect(() => {
    if (isAuthenticated.value) {
      route("/", true);
    }
  }, []);

  const handleLogin = () => {
    login();
  };

  return (
    <div class="login-page">
      <div class="login-card">
        <h1 class="login-title">Taxonomy Builder</h1>
        <p class="login-description">
          Sign in to manage your SKOS vocabularies
        </p>
        <Button onClick={handleLogin} variant="primary">
          Sign in
        </Button>
      </div>
    </div>
  );
}
