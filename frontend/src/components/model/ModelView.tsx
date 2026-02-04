import { useEffect, useState } from "preact/hooks";
import { Button } from "../common/Button";
import { ClassCard } from "./ClassCard";
import { PropertyForm } from "../properties/PropertyForm";
import { PropertyDetail } from "../properties/PropertyDetail";
import { ontologyApi } from "../../api/ontology";
import { propertiesApi } from "../../api/properties";
import {
  ontology,
  ontologyLoading,
  ontologyError,
  ontologyClasses,
} from "../../state/ontology";
import { properties, selectedPropertyId, selectedProperty } from "../../state/properties";
import "./ModelView.css";

interface ModelViewProps {
  projectId: string;
  projectName: string;
  onSchemeSelect: (schemeId: string) => void;
  onBack: () => void;
}

export function ModelView({
  projectId,
  projectName,
  onSchemeSelect,
  onBack,
}: ModelViewProps) {
  const [addingPropertyForClass, setAddingPropertyForClass] = useState<string | null>(null);

  // Load ontology on mount if not loaded
  useEffect(() => {
    if (!ontology.value && !ontologyLoading.value) {
      loadOntology();
    }
  }, []);

  // Load properties when project changes
  useEffect(() => {
    loadProperties();
  }, [projectId]);

  async function loadOntology() {
    ontologyLoading.value = true;
    ontologyError.value = null;
    try {
      ontology.value = await ontologyApi.get();
    } catch (err) {
      ontologyError.value = err instanceof Error ? err.message : "Failed to load ontology";
    } finally {
      ontologyLoading.value = false;
    }
  }

  async function loadProperties() {
    try {
      properties.value = await propertiesApi.listForProject(projectId);
    } catch (err) {
      console.error("Failed to load properties:", err);
    }
  }

  function handleAddProperty(classUri: string) {
    setAddingPropertyForClass(classUri);
    selectedPropertyId.value = null;
  }

  function handlePropertyClick(propertyId: string) {
    selectedPropertyId.value = propertyId;
    setAddingPropertyForClass(null);
  }

  function handlePropertyFormSuccess() {
    setAddingPropertyForClass(null);
    loadProperties();
  }

  function handlePropertyFormCancel() {
    setAddingPropertyForClass(null);
  }

  function handlePropertyDetailClose() {
    selectedPropertyId.value = null;
  }

  function getPropertiesForClass(classUri: string) {
    return properties.value.filter((p) => p.domain_class === classUri);
  }

  if (ontologyLoading.value) {
    return <div class="model-view__loading">Loading ontology...</div>;
  }

  if (ontologyError.value) {
    return <div class="model-view__error">{ontologyError.value}</div>;
  }

  return (
    <div class="model-view">
      <header class="model-view__header">
        <Button variant="ghost" size="sm" onClick={onBack}>
          ← Schemes
        </Button>
        <h1 class="model-view__title">{projectName}</h1>
        <span class="model-view__subtitle">Domain Model</span>
      </header>

      <div class="model-view__content">
        <div class="model-view__classes">
          {ontologyClasses.value.map((cls) => (
            <ClassCard
              key={cls.uri}
              ontologyClass={cls}
              properties={getPropertiesForClass(cls.uri)}
              onAddProperty={handleAddProperty}
              onPropertyClick={handlePropertyClick}
              onSchemeClick={onSchemeSelect}
            />
          ))}
        </div>

        {/* Property form/detail sidebar */}
        {(addingPropertyForClass || selectedProperty.value) && (
          <aside class="model-view__sidebar">
            {addingPropertyForClass ? (
              <PropertyForm
                projectId={projectId}
                domainClassUri={addingPropertyForClass}
                onSuccess={handlePropertyFormSuccess}
                onCancel={handlePropertyFormCancel}
              />
            ) : selectedProperty.value ? (
              <PropertyDetail
                property={selectedProperty.value}
                onRefresh={loadProperties}
                onClose={handlePropertyDetailClose}
              />
            ) : null}
          </aside>
        )}
      </div>
    </div>
  );
}
