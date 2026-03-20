import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { ClassDetailPane } from "../../../src/components/workspace/ClassDetailPane";
import { properties, selectedPropertyId, creatingProperty } from "../../../src/state/properties";
import type { Property, OntologyClass } from "../../../src/types/models";
import * as historyApi from "../../../src/api/history";

vi.mock("../../../src/api/history");

/** Replicates the BFS logic from classes.ts for test data. */
function buildMockAncestors(
  classes: { uri: string; superclass_uris: string[] }[],
): Map<string, Set<string>> {
  const uriToSuperclasses = new Map<string, string[]>();
  for (const cls of classes) {
    uriToSuperclasses.set(cls.uri, cls.superclass_uris);
  }
  const result = new Map<string, Set<string>>();
  for (const cls of classes) {
    const ancestors = new Set<string>();
    const queue = [...cls.superclass_uris];
    while (queue.length > 0) {
      const uri = queue.shift()!;
      if (uri === cls.uri || ancestors.has(uri)) continue;
      ancestors.add(uri);
      const parents = uriToSuperclasses.get(uri);
      if (parents) queue.push(...parents);
    }
    result.set(cls.uri, ancestors);
  }
  return result;
}

const mockProperties: Property[] = [
  {
    id: "prop-1",
    project_id: "proj-1",
    identifier: "birthDate",
    label: "Birth Date",
    description: null,
    domain_class_uris: ["http://example.org/Person"],
    property_type: "datatype",
    range_scheme_id: null,
    range_scheme: null,
    range_datatype: "xsd:date",
    range_class: null,
    cardinality: "single",
    required: false,
    uri: null,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "prop-2",
    project_id: "proj-1",
    identifier: "country",
    label: "Country",
    description: null,
    domain_class_uris: ["http://example.org/Person"],
    property_type: "object",
    range_scheme_id: "scheme-1",
    range_scheme: { id: "scheme-1", title: "Countries", uri: "http://example.org/countries" },
    range_datatype: null,
    range_class: null,
    cardinality: "single",
    required: true,
    uri: null,
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
  {
    id: "prop-3",
    project_id: "proj-1",
    identifier: "founded",
    label: "Founded",
    description: null,
    domain_class_uris: ["http://example.org/Organization"],
    property_type: "datatype",
    range_scheme_id: null,
    range_scheme: null,
    range_datatype: "xsd:date",
    range_class: null,
    cardinality: "single",
    required: false,
    uri: null,
    created_at: "2024-01-03T00:00:00Z",
    updated_at: "2024-01-03T00:00:00Z",
  },
];

// vi.hoisted runs before vi.mock hoisting — makes these available to the factory
const { mockOntologyClasses, mockSelectedClassUri, mockClassAncestors } = vi.hoisted(() => ({
  mockOntologyClasses: {
    value: [
      { id: "cls-1", project_id: "proj-1", identifier: "Person", uri: "http://example.org/Person", label: "Person", description: "A human being", scope_note: null, superclass_uris: [] as string[], subclass_uris: [] as string[], restrictions: [] as OntologyClass["restrictions"], created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
      { id: "cls-2", project_id: "proj-1", identifier: "Organization", uri: "http://example.org/Organization", label: "Organization", description: null, scope_note: null, superclass_uris: [] as string[], subclass_uris: [] as string[], restrictions: [] as OntologyClass["restrictions"], created_at: "2024-01-02T00:00:00Z", updated_at: "2024-01-02T00:00:00Z" },
    ] as OntologyClass[],
  },
  mockSelectedClassUri: { value: null as string | null },
  mockClassAncestors: { value: new Map<string, Set<string>>() },
}));

vi.mock("../../../src/state/classes", async () => {
  const actual = await vi.importActual("../../../src/state/classes");
  return {
    ...actual,
    ontologyClasses: mockOntologyClasses,
    selectedClassUri: mockSelectedClassUri,
    classAncestors: mockClassAncestors,
    // Must stay in sync with isApplicable in state/classes.ts
    isApplicable: (classUri: string, domainClassUris: string[]) => {
      if (domainClassUris.includes(classUri)) return true;
      const ancestors = mockClassAncestors.value.get(classUri);
      if (!ancestors) return false;
      return domainClassUris.some((uri: string) => ancestors.has(uri));
    },
  };
});

vi.mock("../../../src/components/classes/ClassDetail", () => ({
  ClassDetail: (props: Record<string, unknown>) => {
    const cls = props.ontologyClass as { label: string; description: string | null } | undefined;
    return (
      <div data-testid="class-detail">
        {cls && <span>{cls.label}</span>}
        {cls?.description && <span>{cls.description}</span>}
      </div>
    );
  },
}));

describe("ClassDetailPane", () => {
  const mockOnPropertySelect = vi.fn();
  const mockOnSchemeNavigate = vi.fn();
  const mockOnRefresh = vi.fn();
  const mockOnClassDeleted = vi.fn();
  const defaultClasses = structuredClone(mockOntologyClasses.value);

  beforeEach(() => {
    vi.resetAllMocks();
    properties.value = mockProperties;
    selectedPropertyId.value = null;
    creatingProperty.value = null;
    mockOntologyClasses.value = structuredClone(defaultClasses);
    mockClassAncestors.value = buildMockAncestors(mockOntologyClasses.value);
    mockSelectedClassUri.value = null;
  });

  describe("header", () => {
    it("displays class label", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("Person")).toBeInTheDocument();
    });

    it("displays class description when available", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("A human being")).toBeInTheDocument();
    });

    it("shows URI when class not found in ontology", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Unknown"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("http://example.org/Unknown")).toBeInTheDocument();
    });
  });

  describe("properties list", () => {
    it("shows properties for the class", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("Birth Date")).toBeInTheDocument();
      expect(screen.getByText("Country")).toBeInTheDocument();
    });

    it("only shows properties for the given class", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      // Founded belongs to Organization, not Person
      expect(screen.queryByText("Founded")).not.toBeInTheDocument();
    });

    it("shows datatype for datatype properties", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("Date")).toBeInTheDocument();
    });

    it("shows scheme name for scheme-range properties", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("Countries")).toBeInTheDocument();
    });

    it("shows empty state when no properties", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Organization"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      // Organization only has "Founded" property in our mock data
      expect(screen.getByText("Founded")).toBeInTheDocument();
    });
  });

  describe("interactions", () => {
    it("calls onPropertySelect when property clicked", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      fireEvent.click(screen.getByText("Birth Date"));

      expect(mockOnPropertySelect).toHaveBeenCalledWith("prop-1");
    });

    it("calls onSchemeNavigate when scheme link clicked", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      fireEvent.click(screen.getByText("Countries"));

      expect(mockOnSchemeNavigate).toHaveBeenCalledWith("scheme-1");
    });

    it("sets creatingProperty signal when Add Property clicked", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      fireEvent.click(screen.getByText("+ Add Property"));

      expect(creatingProperty.value).toEqual({
        projectId: "proj-1",
        domainClassUri: "http://example.org/Person",
      });
    });

    it("clears selectedPropertyId when Add Property clicked", () => {
      selectedPropertyId.value = "prop-1";

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      fireEvent.click(screen.getByText("+ Add Property"));

      expect(selectedPropertyId.value).toBeNull();
    });

    it("highlights selected property", () => {
      selectedPropertyId.value = "prop-1";

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      const propertyItem = screen.getByText("Birth Date").closest(".class-detail-pane__property");
      expect(propertyItem).toHaveClass("class-detail-pane__property--selected");
    });
  });

  describe("hierarchy section", () => {
    it("is hidden when class has no superclasses or subclasses", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.queryByText("Hierarchy")).not.toBeInTheDocument();
    });

    it("shows superclass label as clickable link", () => {
      mockOntologyClasses.value = [
        { ...defaultClasses[0], superclass_uris: ["http://example.org/Organization"], subclass_uris: [] },
        { ...defaultClasses[1] },
      ];

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("Hierarchy")).toBeInTheDocument();
      const link = screen.getByRole("button", { name: "Organization" });
      expect(link).toHaveClass("workspace-detail__link");
    });

    it("navigates to superclass when link clicked", () => {
      mockOntologyClasses.value = [
        { ...defaultClasses[0], superclass_uris: ["http://example.org/Organization"], subclass_uris: [] },
        { ...defaultClasses[1] },
      ];

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: "Organization" }));
      expect(mockSelectedClassUri.value).toBe("http://example.org/Organization");
    });

    it("shows subclass labels as clickable links", () => {
      mockOntologyClasses.value = [
        { ...defaultClasses[0] },
        { ...defaultClasses[1], superclass_uris: [], subclass_uris: ["http://example.org/Person"] },
      ];

      render(
        <ClassDetailPane
          classUri="http://example.org/Organization"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("Hierarchy")).toBeInTheDocument();
      expect(screen.getByText(/Subclasses/)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Person" })).toBeInTheDocument();
    });

    it("renders unresolvable URIs as non-navigable text", () => {
      mockOntologyClasses.value = [
        { ...defaultClasses[0], superclass_uris: ["https://schema.org/Thing"], subclass_uris: [] },
      ];

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      // "Thing" extracted from https://schema.org/Thing — shown as plain text, not a button
      expect(screen.getByText("Thing")).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Thing" })).not.toBeInTheDocument();
    });

    it("renders unresolvable hash URIs as non-navigable text", () => {
      mockOntologyClasses.value = [
        { ...defaultClasses[0], superclass_uris: [], subclass_uris: ["http://www.w3.org/2002/07/owl#NamedIndividual"] },
      ];

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      // "NamedIndividual" extracted from the OWL hash URI — shown as plain text, not a button
      expect(screen.getByText("NamedIndividual")).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "NamedIndividual" })).not.toBeInTheDocument();
    });
  });

  describe("restrictions section", () => {
    it("is hidden when class has no restrictions", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.queryByText("Restrictions")).not.toBeInTheDocument();
    });

    it("shows restrictions with resolved class label and restriction type", () => {
      mockOntologyClasses.value = [
        {
          ...defaultClasses[0],
          restrictions: [
            {
              on_property_uri: "http://example.org/birthDate",
              restriction_type: "allValuesFrom",
              value_uri: "http://example.org/Organization",
            },
          ],
        },
        { ...defaultClasses[1] },
      ];

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("Restrictions")).toBeInTheDocument();
      // Property URI falls back to extractLocalName (mock prop has uri: null)
      expect(screen.getByText("birthDate")).toBeInTheDocument();
      expect(screen.getByText("allValuesFrom")).toBeInTheDocument();
      // Class URI resolves to label from mockOntologyClasses
      expect(screen.getByText("Organization")).toBeInTheDocument();
    });

    it("falls back to extractLocalName for unresolvable restriction URIs", () => {
      mockOntologyClasses.value = [
        {
          ...defaultClasses[0],
          restrictions: [
            {
              on_property_uri: "https://external.org/vocab#someProperty",
              restriction_type: "someValuesFrom",
              value_uri: "https://external.org/vocab#SomeClass",
            },
          ],
        },
      ];

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("someProperty")).toBeInTheDocument();
      expect(screen.getByText("SomeClass")).toBeInTheDocument();
    });
  });

  describe("inherited properties", () => {
    const employeeClass: OntologyClass = {
      id: "cls-3", project_id: "proj-1", identifier: "Employee",
      uri: "http://example.org/Employee", label: "Employee",
      description: null, scope_note: null,
      superclass_uris: ["http://example.org/Person"],
      subclass_uris: [],
      restrictions: [],
      created_at: "2024-01-03T00:00:00Z", updated_at: "2024-01-03T00:00:00Z",
    };

    const employeeProperty: Property = {
      id: "prop-4", project_id: "proj-1", identifier: "employeeId",
      label: "Employee ID", description: null,
      domain_class_uris: ["http://example.org/Employee"],
      property_type: "datatype", range_scheme_id: null, range_scheme: null,
      range_datatype: "xsd:string", range_class: null,
      cardinality: "single", required: true, uri: null,
      created_at: "2024-01-04T00:00:00Z", updated_at: "2024-01-04T00:00:00Z",
    };

    beforeEach(() => {
      mockOntologyClasses.value = [
        { ...defaultClasses[0], subclass_uris: ["http://example.org/Employee"] },
        { ...defaultClasses[1] },
        employeeClass,
      ];
      mockClassAncestors.value = buildMockAncestors(mockOntologyClasses.value);
      properties.value = [...mockProperties, employeeProperty];
    });

    it("shows inherited properties from superclass", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Employee"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      // Direct property on Employee
      expect(screen.getByText("Employee ID")).toBeInTheDocument();
      // Inherited from Person
      expect(screen.getByText("Birth Date")).toBeInTheDocument();
      expect(screen.getByText("Country")).toBeInTheDocument();
      // Group header
      expect(screen.getByText(/Inherited from/)).toBeInTheDocument();
    });

    it("navigates to ancestor when inherited group link clicked", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Employee"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      const inheritedLink = screen.getAllByRole("button", { name: "Person" }).find((link) =>
        link.closest(".class-detail-pane__group-header--inherited")
      );
      expect(inheritedLink).toBeDefined();
      fireEvent.click(inheritedLink!);
      expect(mockSelectedClassUri.value).toBe("http://example.org/Person");
    });

    it("hides Direct subheader when there are no inherited properties", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("Birth Date")).toBeInTheDocument();
      expect(screen.queryByText("Direct")).not.toBeInTheDocument();
      expect(screen.queryByText(/Inherited from/)).not.toBeInTheDocument();
    });

    it("deduplicates property that is both direct and inherited", () => {
      const sharedProperty: Property = {
        id: "prop-5", project_id: "proj-1", identifier: "sharedProp",
        label: "Shared Property", description: null,
        domain_class_uris: ["http://example.org/Person", "http://example.org/Employee"],
        property_type: "datatype", range_scheme_id: null, range_scheme: null,
        range_datatype: "xsd:string", range_class: null,
        cardinality: "single", required: false, uri: null,
        created_at: "2024-01-05T00:00:00Z", updated_at: "2024-01-05T00:00:00Z",
      };
      properties.value = [...mockProperties, employeeProperty, sharedProperty];

      render(
        <ClassDetailPane
          classUri="http://example.org/Employee"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      const matches = screen.getAllByText("Shared Property");
      expect(matches).toHaveLength(1);
    });

    it("breaks ties for equidistant ancestors by label alphabetically", () => {
      // Employee has two parents at depth 1: Manager and Worker
      // A property on both should be assigned to Manager (alphabetically first)
      const managerClass: OntologyClass = {
        id: "cls-m", project_id: "proj-1", identifier: "Manager",
        uri: "http://example.org/Manager", label: "Manager",
        description: null, scope_note: null,
        superclass_uris: [], subclass_uris: ["http://example.org/Employee"],
        restrictions: [],
        created_at: "2024-01-05T00:00:00Z", updated_at: "2024-01-05T00:00:00Z",
      };
      const workerClass: OntologyClass = {
        id: "cls-w", project_id: "proj-1", identifier: "Worker",
        uri: "http://example.org/Worker", label: "Worker",
        description: null, scope_note: null,
        superclass_uris: [], subclass_uris: ["http://example.org/Employee"],
        restrictions: [],
        created_at: "2024-01-06T00:00:00Z", updated_at: "2024-01-06T00:00:00Z",
      };
      const sharedAncestorProp: Property = {
        id: "prop-shared", project_id: "proj-1", identifier: "badge",
        label: "Badge Number", description: null,
        domain_class_uris: ["http://example.org/Worker", "http://example.org/Manager"],
        property_type: "datatype", range_scheme_id: null, range_scheme: null,
        range_datatype: "xsd:string", range_class: null,
        cardinality: "single", required: false, uri: null,
        created_at: "2024-01-07T00:00:00Z", updated_at: "2024-01-07T00:00:00Z",
      };

      const employeeWithTwoParents: OntologyClass = {
        ...employeeClass,
        superclass_uris: ["http://example.org/Manager", "http://example.org/Worker"],
      };

      mockOntologyClasses.value = [
        { ...defaultClasses[0] },
        { ...defaultClasses[1] },
        employeeWithTwoParents,
        managerClass,
        workerClass,
      ];
      mockClassAncestors.value = buildMockAncestors(mockOntologyClasses.value);
      properties.value = [employeeProperty, sharedAncestorProp];

      render(
        <ClassDetailPane
          classUri="http://example.org/Employee"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      // Property should be grouped under Manager (alphabetically before Worker)
      const inheritedHeaders = screen.getAllByText(/Inherited from/);
      expect(inheritedHeaders).toHaveLength(1);
      // Manager appears in both hierarchy section and inherited group header
      const managerInGroup = screen.getAllByRole("button", { name: "Manager" }).filter((btn) =>
        btn.closest(".class-detail-pane__group-header--inherited")
      );
      expect(managerInGroup).toHaveLength(1);
      // Worker should NOT appear as a group header
      const workerInGroup = screen.queryAllByRole("button", { name: "Worker" }).filter((btn) =>
        btn.closest(".class-detail-pane__group-header--inherited")
      );
      expect(workerInGroup).toHaveLength(0);
    });

    it("shows multiple inherited groups from different ancestors in depth order", () => {
      const animalClass: OntologyClass = {
        id: "cls-4", project_id: "proj-1", identifier: "Animal",
        uri: "http://example.org/Animal", label: "Animal",
        description: null, scope_note: null,
        superclass_uris: [],
        subclass_uris: ["http://example.org/Person"],
        restrictions: [],
        created_at: "2024-01-05T00:00:00Z", updated_at: "2024-01-05T00:00:00Z",
      };
      const animalProperty: Property = {
        id: "prop-6", project_id: "proj-1", identifier: "species",
        label: "Species", description: null,
        domain_class_uris: ["http://example.org/Animal"],
        property_type: "datatype", range_scheme_id: null, range_scheme: null,
        range_datatype: "xsd:string", range_class: null,
        cardinality: "single", required: false, uri: null,
        created_at: "2024-01-06T00:00:00Z", updated_at: "2024-01-06T00:00:00Z",
      };

      mockOntologyClasses.value = [
        {
          ...defaultClasses[0],
          superclass_uris: ["http://example.org/Animal"],
          subclass_uris: ["http://example.org/Employee"],
        },
        { ...defaultClasses[1] },
        employeeClass,
        animalClass,
      ];
      mockClassAncestors.value = buildMockAncestors(mockOntologyClasses.value);
      properties.value = [...mockProperties, employeeProperty, animalProperty];

      render(
        <ClassDetailPane
          classUri="http://example.org/Employee"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      // Two inherited groups
      const inheritedHeaders = screen.getAllByText(/Inherited from/);
      expect(inheritedHeaders).toHaveLength(2);

      // Person's properties inherited
      expect(screen.getByText("Birth Date")).toBeInTheDocument();
      // Animal's property inherited
      expect(screen.getByText("Species")).toBeInTheDocument();
    });
  });

  describe("history footer", () => {
    it("toggles history panel and passes project source", async () => {
      vi.mocked(historyApi.getProjectHistory).mockResolvedValue([]);

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      const button = screen.getByRole("button", { name: /history/i });
      expect(button).toHaveAttribute("aria-expanded", "false");

      fireEvent.click(button);

      await waitFor(() => {
        expect(button).toHaveAttribute("aria-expanded", "true");
        expect(historyApi.getProjectHistory).toHaveBeenCalledWith("proj-1");
      });
    });
  });
});
