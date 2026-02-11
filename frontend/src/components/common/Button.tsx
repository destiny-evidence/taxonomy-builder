import type { ComponentChildren, JSX } from "preact";
import "./Button.css";

interface ButtonProps {
  children: ComponentChildren;
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  type?: "button" | "submit";
  disabled?: boolean;
  "aria-label"?: string;
  onClick?: (e: JSX.TargetedMouseEvent<HTMLButtonElement>) => void;
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  type = "button",
  disabled = false,
  "aria-label": ariaLabel,
  onClick,
}: ButtonProps) {
  return (
    <button
      type={type}
      class={`btn btn--${variant} btn--${size}`}
      disabled={disabled}
      aria-label={ariaLabel}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
