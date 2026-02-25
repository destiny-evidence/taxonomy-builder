import { signal } from "@preact/signals";

export const isOffline = signal(!navigator.onLine);

window.addEventListener("online", () => {
  isOffline.value = false;
});
window.addEventListener("offline", () => {
  isOffline.value = true;
});
