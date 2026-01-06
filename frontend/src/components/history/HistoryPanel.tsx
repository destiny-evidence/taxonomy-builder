import { useEffect, useState } from "preact/hooks";
import { getSchemeHistory } from "../../api/history";
import type { ChangeEvent } from "../../types/models";

interface HistoryPanelProps {
  schemeId: string;
}

export function HistoryPanel({ schemeId }: HistoryPanelProps) {
  const [history, setHistory] = useState<ChangeEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      try {
        setLoading(true);
        setError(null);
        const data = await getSchemeHistory(schemeId);
        setHistory(data);
      } catch (err) {
        setError("Failed to load history");
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, [schemeId]);

  if (loading) {
    return <div>Loading history...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (history.length === 0) {
    return <div>No history available.</div>;
  }

  return (
    <div className="history-panel">
      <h3>History</h3>
      <ul>
        {history.map((event) => (
          <li key={event.id}>
            <span className="action">{event.action}</span>
            <span className="entity-type">{event.entity_type}</span>
            <span className="timestamp">
              {new Date(event.timestamp).toLocaleString()}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
