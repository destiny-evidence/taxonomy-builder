import { render, screen } from "@testing-library/preact";
import { describe, it, expect, beforeEach } from "vitest";

import { Sidebar } from "../../src/components/sidebar/Sidebar";
import { vocabulary, loading, error } from "../../src/state/vocabulary";
import type { Vocabulary, VocabScheme } from "../../src/api/published";

function scheme(id: string, title: string, position?: number): VocabScheme {
  return {
    id,
    title,
    description: null,
    uri: `http://example.org/${id}`,
    position,
    top_concepts: [],
    concepts: {},
  };
}

function makeVocab(schemes: VocabScheme[]): Vocabulary {
  return {
    format_version: "1.0",
    version: "1.0",
    title: "V1",
    published_at: "2026-01-01T00:00:00+00:00",
    publisher: null,
    pre_release: false,
    previous_version_id: null,
    project: { id: "p1", name: "Proj", description: null, namespace: null },
    schemes,
    classes: [],
    properties: [],
  };
}

function renderedTitles(): string[] {
  return screen
    .getAllByText(/.+/, { selector: ".sidebar__section-title" })
    .map((el) => el.textContent ?? "");
}

describe("Sidebar scheme ordering", () => {
  beforeEach(() => {
    loading.value = false;
    error.value = null;
  });

  it("renders schemes in position order regardless of array order", () => {
    vocabulary.value = makeVocab([
      scheme("c", "Charlie", 2),
      scheme("a", "Alpha", 0),
      scheme("b", "Bravo", 1),
    ]);
    render(<Sidebar />);
    expect(renderedTitles()).toEqual(["Alpha", "Bravo", "Charlie"]);
  });

  it("preserves array order for legacy artifacts without position", () => {
    vocabulary.value = makeVocab([
      scheme("x", "Xray"),
      scheme("y", "Yankee"),
      scheme("z", "Zulu"),
    ]);
    render(<Sidebar />);
    expect(renderedTitles()).toEqual(["Xray", "Yankee", "Zulu"]);
  });
});
