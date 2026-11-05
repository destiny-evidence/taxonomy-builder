import { render, screen } from "@testing-library/preact";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { PropertyDetail } from "../../../src/components/detail/PropertyDetail";
import { vocabulary } from "../../../src/state/vocabulary";
import type { VocabProperty } from "../../../src/api/published";
import { makeVocabulary } from "../../fixtures";

vi.mock("../../../src/components/feedback/FeedbackSection", () => ({
  FeedbackSection: () => null,
}));

function makeProperty(overrides: Partial<VocabProperty> = {}): VocabProperty {
  return {
    id: "prop-1",
    identifier: "lat",
    uri: "http://www.w3.org/2003/01/geo/wgs84_pos#lat",
    label: "latitude",
    description: null,
    domain_class_uris: [],
    property_type: "datatype",
    range_scheme_id: null,
    range_scheme_uri: null,
    range_datatype: null,
    range_class: null,
    cardinality: "single",
    required: false,
    ...overrides,
  };
}

function rangeText(): string | null {
  return screen.getByText("Range:").parentElement?.textContent ?? null;
}

describe("PropertyDetail range", () => {
  beforeEach(() => {
    vocabulary.value = null;
  });

  it("shows Any when the property has no range", () => {
    vocabulary.value = makeVocabulary({ properties: [makeProperty()] });
    render(<PropertyDetail propertyId="prop-1" />);
    expect(rangeText()).toBe("Range: Any");
  });

  it("shows the datatype when one is set", () => {
    vocabulary.value = makeVocabulary({
      properties: [makeProperty({ range_datatype: "xsd:string" })],
    });
    render(<PropertyDetail propertyId="prop-1" />);
    expect(rangeText()).toBe("Range: xsd:string");
  });

  it("shows a dash when the range class is not in the vocabulary", () => {
    vocabulary.value = makeVocabulary({
      properties: [makeProperty({ range_class: "http://example.org/Missing" })],
    });
    render(<PropertyDetail propertyId="prop-1" />);
    expect(rangeText()).toBe("Range: —");
  });
});
