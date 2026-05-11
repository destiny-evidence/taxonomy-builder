import { render } from "preact";
import { App } from "./App";
import { initMatomo } from "./analytics/matomo";
import { MATOMO_CONTAINER_URL } from "./config";
import { registerServiceWorker } from "./sw-register";
import "./styles/variables.css";
import "./styles/reset.css";

registerServiceWorker();
initMatomo(MATOMO_CONTAINER_URL);
render(<App />, document.getElementById("app")!);
