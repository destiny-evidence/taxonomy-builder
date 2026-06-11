import { render, fireEvent, screen } from "@testing-library/preact";
import { describe, it, expect, vi, beforeEach } from "vitest";

const { register, login } = vi.hoisted(() => ({
  register: vi.fn(),
  login: vi.fn(),
}));
vi.mock("../../src/keycloak", () => ({
  keycloak: { register, login, logout: vi.fn() },
}));

import { AuthStatus } from "../../src/components/layout/AuthStatus";
import { currentUser, authInitialized } from "../../src/state/auth";

describe("AuthStatus (logged out)", () => {
  beforeEach(() => {
    register.mockClear();
    login.mockClear();
    currentUser.value = null;
    authInitialized.value = true;
  });

  it("opens self-registration from the Create account button", () => {
    render(<AuthStatus />);
    fireEvent.click(screen.getByText("Create account"));
    expect(register).toHaveBeenCalledOnce();
    expect(login).not.toHaveBeenCalled();
  });
});
