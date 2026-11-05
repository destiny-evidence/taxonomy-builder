import { currentProject } from "../../state/projects";
import { externalPrefix } from "../../utils/terms";
import "./TermPrefix.css";

/** Marks a class or property from another vocabulary, e.g. "gn". */
export function TermPrefix({ uri }: { uri: string | null }) {
  const prefix = uri ? externalPrefix(uri, currentProject.value) : null;
  return prefix ? <span class="term-prefix">{prefix}</span> : null;
}
