declare global {
  interface Window {
    _mtm?: Array<Record<string, unknown>>;
  }
}

export function initMatomo(containerUrl: string | undefined): void {
  if (!containerUrl) return;
  if (document.querySelector(`script[src="${containerUrl}"]`)) return;

  window._mtm = window._mtm || [];
  window._mtm.push({ "mtm.startTime": Date.now(), event: "mtm.Start" });

  const script = document.createElement("script");
  script.async = true;
  script.src = containerUrl;
  const firstScript = document.getElementsByTagName("script")[0];
  if (firstScript?.parentNode) {
    firstScript.parentNode.insertBefore(script, firstScript);
  } else {
    document.head.appendChild(script);
  }
}
