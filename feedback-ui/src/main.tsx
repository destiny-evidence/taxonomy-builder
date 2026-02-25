import { render } from "preact";
import { App } from "./App";
import { registerServiceWorker } from "./sw-register";

registerServiceWorker();
render(<App />, document.getElementById("app")!);
