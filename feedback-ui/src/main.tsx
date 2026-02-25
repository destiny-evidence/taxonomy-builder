import { render } from "preact";
import { App } from "./App";
import { registerServiceWorker } from "./sw-register";
import "./styles/variables.css";
import "./styles/reset.css";

registerServiceWorker();
render(<App />, document.getElementById("app")!);
