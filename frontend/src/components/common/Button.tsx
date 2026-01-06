import type { ComponentChildren, JSX } from "preact";
import "./Button.css";

interface ButtonProps {
  children: ComponentChildren;
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  type?: "button" | "submit";
  disabled?: boolean;
  onClick?: (e: JSX.TargetedMouseEvent<HTMLButtonElement>) => void;
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  type = "button",
  disabled = false,
  onClick,
}: ButtonProps) {
  return (
    <button
      type={type}
      class={`btn btn--${variant} btn--${size}`}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
