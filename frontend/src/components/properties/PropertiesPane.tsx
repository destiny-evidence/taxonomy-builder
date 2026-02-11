import { Button } from "../common/Button";
import type { Property, OntologyClass } from "../../types/models";
import "./PropertiesPane.css";

interface PropertiesPaneProps {
  projectId: string;
  properties: Property[];
  schemes: { id: string; title: string }[];
  ontologyClasses: OntologyClass[];
  loading?: boolean;
  error?: string | null;
  onCreate: () => void;
  onEdit: (property: Property) => void;
  onDelete: (property: Property) => void;
}

export function PropertiesPane({
  properties,
  ontologyClasses,
  loading,
  error,
  onCreate,
  onEdit,
  onDelete,
}: PropertiesPaneProps) {
  const classLabelMap = new Map(ontologyClasses.map((c) => [c.uri, c.label]));

  function getDomainLabel(uri: string): string {
    return classLabelMap.get(uri) ?? uri;
  }

  function getRangeDisplay(prop: Property): string {
    if (prop.range_scheme) return prop.range_scheme.title;
    if (prop.range_datatype) return prop.range_datatype;
    return "—";
  }

  return (
    <div class="properties-pane">
      <div class="properties-pane__header">
        <h2 class="properties-pane__title">Properties</h2>
        <Button onClick={onCreate}>New Property</Button>
      </div>

      {error ? (
        <div class="properties-pane__error" role="alert">
          <p>Failed to load properties.</p>
          <p>{error}</p>
        </div>
      ) : loading ? (
        <div class="properties-pane__empty">
          <p>Loading properties...</p>
        </div>
      ) : properties.length === 0 ? (
        <div class="properties-pane__empty">
          <p>No properties defined yet.</p>
          <p>Properties link vocabulary classes to concept schemes or datatypes.</p>
        </div>
      ) : (
        <div class="properties-pane__table-wrapper">
          <table class="properties-pane__table">
            <thead>
              <tr>
                <th scope="col">Label</th>
                <th scope="col">Identifier</th>
                <th scope="col">Applies to</th>
                <th scope="col">Range</th>
                <th scope="col">Cardinality</th>
                <th scope="col">Required</th>
                <th scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              {properties.map((prop) => (
                <tr key={prop.id}>
                  <td class="properties-pane__cell--label">{prop.label}</td>
                  <td class="properties-pane__cell--identifier">
                    <code>{prop.identifier}</code>
                  </td>
                  <td>{getDomainLabel(prop.domain_class)}</td>
                  <td>{getRangeDisplay(prop)}</td>
                  <td>{prop.cardinality}</td>
                  <td>{prop.required ? "Yes" : "No"}</td>
                  <td class="properties-pane__cell--actions">
                    <Button variant="ghost" size="sm" onClick={() => onEdit(prop)} aria-label={`Edit ${prop.label}`}>
                      Edit
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => onDelete(prop)} aria-label={`Delete ${prop.label}`}>
                      Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
