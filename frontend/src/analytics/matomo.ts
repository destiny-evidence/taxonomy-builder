declare global {
  interface Window {
    _mtm?: Array<Record<string, unknown>>;
  }
}

export function initMatomo(containerUrl: string | undefined): void {
  if (!containerUrl) return;

  const _mtm = (window._mtm = window._mtm || []);
  _mtm.push({ "mtm.startTime": new Date().getTime(), event: "mtm.Start" });

  const g = document.createElement("script");
  const s = document.getElementsByTagName("script")[0];
  g.async = true;
  g.src = containerUrl;
  s.parentNode!.insertBefore(g, s);
}
