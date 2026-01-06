import { render } from "preact";
import { App } from "./App";
import "./styles/reset.css";
import "./styles/variables.css";

render(<App />, document.getElementById("app")!);
