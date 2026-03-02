import "./Badge.css";

interface BadgeProps {
  label: string;
  variant?: "default" | "open" | "responded" | "resolved" | "declined";
}

const STATUS_PREFIX: Record<string, string> = {
  open: "\u29D7 ",
  responded: "\u21A9 ",
  resolved: "\u2713 ",
  declined: "\u2717 ",
};

export function Badge({ label, variant = "default" }: BadgeProps) {
  const prefix = STATUS_PREFIX[variant] ?? "";
  return <span class={`badge badge--${variant}`}>{prefix}{label}</span>;
}

/** Map feedback_type value to a display label. */
export function feedbackTypeLabel(type: string): string {
  return type.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}

/** Map status to badge variant. */
export function statusVariant(
  status: string
): "open" | "responded" | "resolved" | "declined" {
  switch (status) {
    case "responded":
      return "responded";
    case "resolved":
      return "resolved";
    case "declined":
      return "declined";
    default:
      return "open";
  }
}
