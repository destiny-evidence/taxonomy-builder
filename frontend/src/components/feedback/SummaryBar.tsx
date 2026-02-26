import { summaryStats, statusFilter } from "../../state/feedback";
import type { FeedbackStatus } from "../../types/models";
import "./SummaryBar.css";

const CARDS: { key: FeedbackStatus | ""; stat: keyof ReturnType<typeof summaryStats["peek"]>; label: string; modifier: string }[] = [
  { key: "", stat: "total", label: "Total", modifier: "" },
  { key: "open", stat: "open", label: "Open", modifier: "summary-card--warning" },
  { key: "responded", stat: "responded", label: "Responded", modifier: "summary-card--primary" },
  { key: "resolved", stat: "resolved", label: "Resolved", modifier: "summary-card--success" },
  { key: "declined", stat: "declined", label: "Declined", modifier: "summary-card--muted" },
];

export function SummaryBar() {
  const stats = summaryStats.value;
  const active = statusFilter.value;

  function handleClick(key: FeedbackStatus | "") {
    statusFilter.value = active === key ? "" : key;
  }

  return (
    <div class="summary-bar">
      {CARDS.map((card) => (
        <button
          key={card.key}
          type="button"
          class={`summary-card ${card.modifier} ${active === card.key ? "summary-card--active" : ""}`}
          onClick={() => handleClick(card.key)}
        >
          <div class="summary-card__number">{stats[card.stat]}</div>
          <div class="summary-card__label">{card.label}</div>
        </button>
      ))}
    </div>
  );
}
