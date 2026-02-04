import { useState, useEffect } from "preact/hooks";
import { Button } from "../common/Button";
import { PropertyList } from "../properties/PropertyList";
import { PropertyDetail } from "../properties/PropertyDetail";
import { currentProject } from "../../state/projects";
import { schemes } from "../../state/schemes";
import {
  properties,
  propertiesLoading,
  propertiesError,
  selectedPropertyId,
  selectedProperty,
} from "../../state/properties";
import { propertiesApi } from "../../api/properties";
import "./SchemesPane.css";

interface SchemesPaneProps {
  projectId: string;
  currentSchemeId: string | null;
  onSchemeSelect: (schemeId: string) => void;
  onNewScheme: () => void;
  onImport: () => void;
}

export function SchemesPane({
  projectId,
  currentSchemeId,
  onSchemeSelect,
  onNewScheme,
  onImport,
}: SchemesPaneProps) {
  const [propertiesExpanded, setPropertiesExpanded] = useState(true);
  const projectSchemes = schemes.value.filter((s) => s.project_id === projectId);
  const project = currentProject.value;

  // Load properties when project changes
  useEffect(() => {
    loadProperties();
  }, [projectId]);

  async function loadProperties() {
    propertiesLoading.value = true;
    propertiesError.value = null;
    try {
      properties.value = await propertiesApi.listForProject(projectId);
    } catch (err) {
      propertiesError.value = err instanceof Error ? err.message : "Failed to load properties";
    } finally {
      propertiesLoading.value = false;
    }
  }

  function handlePropertySelect(propertyId: string) {
    selectedPropertyId.value = propertyId;
  }

  function handlePropertyClose() {
    selectedPropertyId.value = null;
  }

  function handleNewProperty() {
    // TODO: Implement new property creation flow
    console.log("New property clicked");
  }

  return (
    <div class="schemes-pane">
      <div class="schemes-pane__header">
        <a href="/projects" class="schemes-pane__back-link">
          Projects
        </a>
        <h2 class="schemes-pane__project-title">{project?.name}</h2>
      </div>

      <div class="schemes-pane__content">
        {/* Schemes section */}
        <div class="schemes-pane__section">
          <h3 class="schemes-pane__section-title">Schemes</h3>
          {projectSchemes.length === 0 ? (
            <div class="schemes-pane__empty">No schemes in this project</div>
          ) : (
            <div class="schemes-pane__list">
              {projectSchemes.map((scheme) => (
                <button
                  key={scheme.id}
                  class={`schemes-pane__item ${
                    scheme.id === currentSchemeId ? "schemes-pane__item--selected" : ""
                  }`}
                  onClick={() => onSchemeSelect(scheme.id)}
                >
                  {scheme.title}
                </button>
              ))}
            </div>
          )}
          <div class="schemes-pane__section-actions">
            <Button variant="secondary" size="sm" onClick={onNewScheme}>
              + New Scheme
            </Button>
            <Button variant="secondary" size="sm" onClick={onImport}>
              Import
            </Button>
          </div>
        </div>

        {/* Properties section */}
        <div class="schemes-pane__section">
          <button
            class="schemes-pane__section-header"
            onClick={() => setPropertiesExpanded(!propertiesExpanded)}
          >
            <span class={`schemes-pane__expand-icon ${propertiesExpanded ? "schemes-pane__expand-icon--expanded" : ""}`}>
              ▶
            </span>
            <h3 class="schemes-pane__section-title">Properties</h3>
          </button>

          {propertiesExpanded && (
            <div class="schemes-pane__section-content">
              {selectedProperty.value ? (
                <PropertyDetail
                  property={selectedProperty.value}
                  onRefresh={loadProperties}
                  onClose={handlePropertyClose}
                />
              ) : (
                <PropertyList
                  onSelect={handlePropertySelect}
                  onNew={handleNewProperty}
                />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
