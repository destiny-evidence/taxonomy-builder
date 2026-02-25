/**
 * Service worker registration.
 *
 * Only registers in production builds. In development, Vite's dev server
 * handles module loading and HMR, so the service worker would interfere.
 */

export function registerServiceWorker(): void {
  if (!import.meta.env.PROD) {
    console.log("[SW] Skipping registration in development mode");
    return;
  }

  if (!("serviceWorker" in navigator)) {
    console.log("[SW] Service workers not supported");
    return;
  }

  window.addEventListener("load", async () => {
    try {
      const base = import.meta.env.BASE_URL;
      const registration = await navigator.serviceWorker.register(
        `${base}sw.js`,
        { scope: base }
      );
      console.log("[SW] Registered with scope:", registration.scope);
    } catch (error) {
      console.error("[SW] Registration failed:", error);
    }
  });
}
