import { useEffect, useState } from "preact/hooks";
import { API_BASE } from "../../config";
import "./BranchIndicator.css";

interface DevInfo {
  branch: string | null;
  commit: string | null;
}

/**
 * Generate a consistent HSL color from a string.
 * Uses a simple hash function to get a hue value.
 */
function stringToColor(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  // Use hash to get a hue (0-360), keep saturation and lightness for good visibility
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 70%, 45%)`;
}

export function BranchIndicator() {
  const [devInfo, setDevInfo] = useState<DevInfo | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/dev/info`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch dev info");
        return res.json();
      })
      .then(setDevInfo)
      .catch(() => setError(true));
  }, []);

  // Don't render anything in production or if there's an error
  if (error || !devInfo?.branch) {
    return null;
  }

  const branchColor = stringToColor(devInfo.branch);

  return (
    <div class="branch-indicator" style={{ "--branch-color": branchColor }}>
      <span class="branch-indicator__icon">
        <svg
          width="14"
          height="14"
          viewBox="0 0 16 16"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fill-rule="evenodd"
            d="M11.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122V6A2.5 2.5 0 0110 8.5H6a1 1 0 00-1 1v1.128a2.251 2.251 0 11-1.5 0V5.372a2.25 2.25 0 111.5 0v1.836A2.492 2.492 0 016 7h4a1 1 0 001-1v-.628A2.25 2.25 0 019.5 3.25zM4.25 12a.75.75 0 100 1.5.75.75 0 000-1.5zM3.5 3.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0z"
          />
        </svg>
      </span>
      <span class="branch-indicator__name">{devInfo.branch}</span>
      {devInfo.commit && (
        <span class="branch-indicator__commit">{devInfo.commit}</span>
      )}
    </div>
  );
}
