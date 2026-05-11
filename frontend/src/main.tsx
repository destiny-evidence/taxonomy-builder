import { render } from "preact";
import { App } from "./App";
import { initMatomo } from "./analytics/matomo";
import { MATOMO_CONTAINER_URL } from "./config";
import "./styles/reset.css";
import "./styles/variables.css";

initMatomo(MATOMO_CONTAINER_URL);
render(<App />, document.getElementById("app")!);
