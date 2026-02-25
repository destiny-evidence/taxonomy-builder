import { artificialLatency, bypassCache } from "../../api/latency";
import "./LatencyToggle.css";

export function LatencyToggle() {
  return (
    <div class="latency-toggle">
      <span class="latency-toggle__label">Latency</span>
      <input
        class="latency-toggle__input"
        type="number"
        min={0}
        step={100}
        value={artificialLatency.value}
        onInput={(e) => {
          artificialLatency.value = parseInt(
            (e.target as HTMLInputElement).value,
            10
          ) || 0;
        }}
      />
      <span>ms</span>
      <span class="latency-toggle__divider" />
      <label class="latency-toggle__checkbox-label">
        <input
          type="checkbox"
          checked={bypassCache.value}
          onChange={(e) => {
            bypassCache.value = (e.target as HTMLInputElement).checked;
          }}
        />
        Bypass cache
      </label>
    </div>
  );
}
