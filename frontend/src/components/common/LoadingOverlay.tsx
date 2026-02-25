import "./LoadingOverlay.css";

/** Absolute-positioned overlay with spinner (parent needs position:relative). */
export function LoadingOverlay() {
  return (
    <div class="loading-overlay">
      <div class="loading-overlay__spinner" />
    </div>
  );
}

/** Inline centered spinner that replaces content. */
export function LoadingSpinner() {
  return (
    <div class="loading-spinner">
      <div class="loading-spinner__circle" />
    </div>
  );
}
