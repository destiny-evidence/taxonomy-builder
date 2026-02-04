import { useState, useEffect } from "preact/hooks";
import { Button } from "../common/Button";
import { Input } from "../common/Input";
import { propertiesApi } from "../../api/properties";
import { ontologyApi } from "../../api/ontology";
import { schemes } from "../../state/schemes";
import type { OntologyClass, PropertyCreate } from "../../types/models";
import "./PropertyForm.css";

interface PropertyFormProps {
  projectId: string;
  onSuccess: () => void;
  onCancel: () => void;
}

const ALLOWED_DATATYPES = [
  "xsd:string",
  "xsd:integer",
  "xsd:decimal",
  "xsd:boolean",
  "xsd:date",
  "xsd:dateTime",
  "xsd:anyURI",
];

// Pattern for URI-safe identifiers
const IDENTIFIER_PATTERN = /^[a-zA-Z][a-zA-Z0-9_-]*$/;

function toCamelCase(str: string): string {
  return str
    .toLowerCase()
    .replace(/[^a-zA-Z0-9]+(.)/g, (_, char) => char.toUpperCase())
    .replace(/^./, (char) => char.toLowerCase())
    .replace(/[^a-zA-Z0-9]/g, "");
}

function validateIdentifier(value: string): string | null {
  if (!value.trim()) {
    return "Identifier is required";
  }
  if (!value[0].match(/[a-zA-Z]/)) {
    return "Identifier must start with a letter";
  }
  if (!IDENTIFIER_PATTERN.test(value)) {
    return "Identifier must be URI-safe: letters, numbers, underscores, and hyphens only";
  }
  return null;
}

export function PropertyForm({ projectId, onSuccess, onCancel }: PropertyFormProps) {
  // Form state
  const [label, setLabel] = useState("");
  const [identifier, setIdentifier] = useState("");
  const [identifierTouched, setIdentifierTouched] = useState(false);
  const [description, setDescription] = useState("");
  const [domainClass, setDomainClass] = useState("");
  const [rangeType, setRangeType] = useState<"scheme" | "datatype">("datatype");
  const [rangeSchemeId, setRangeSchemeId] = useState("");
  const [rangeDatatype, setRangeDatatype] = useState("");
  const [cardinality, setCardinality] = useState<"single" | "multiple">("single");
  const [required, setRequired] = useState(false);

  // Loading states
  const [ontologyClasses, setOntologyClasses] = useState<OntologyClass[]>([]);
  const [ontologyLoading, setOntologyLoading] = useState(true);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Validation
  const identifierError = identifier ? validateIdentifier(identifier) : null;

  // Load ontology on mount
  useEffect(() => {
    async function loadOntology() {
      try {
        const ontology = await ontologyApi.get();
        setOntologyClasses(ontology.classes);
      } catch (err) {
        console.error("Failed to load ontology:", err);
      } finally {
        setOntologyLoading(false);
      }
    }
    loadOntology();
  }, []);

  // Auto-generate identifier from label (only if not manually touched)
  useEffect(() => {
    if (!identifierTouched && label) {
      setIdentifier(toCamelCase(label));
    }
  }, [label, identifierTouched]);

  function handleIdentifierChange(value: string) {
    setIdentifierTouched(true);
    setIdentifier(value);
  }

  const projectSchemes = schemes.value.filter((s) => s.project_id === projectId);

  // Validation: check if form is complete
  const isValid =
    label.trim() &&
    identifier.trim() &&
    !identifierError &&
    domainClass &&
    (rangeType === "scheme" ? rangeSchemeId : rangeDatatype);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    if (!isValid) return;

    setSubmitLoading(true);
    setError(null);

    const data: PropertyCreate = {
      label: label.trim(),
      identifier: identifier.trim(),
      description: description.trim() || undefined,
      domain_class: domainClass,
      range_scheme_id: rangeType === "scheme" ? rangeSchemeId : undefined,
      range_datatype: rangeType === "datatype" ? rangeDatatype : undefined,
      cardinality,
      required,
    };

    try {
      await propertiesApi.create(projectId, data);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create property");
    } finally {
      setSubmitLoading(false);
    }
  }

  if (ontologyLoading) {
    return <div class="property-form__loading">Loading...</div>;
  }

  return (
    <form class="property-form" onSubmit={handleSubmit}>
      <h3 class="property-form__title">New Property</h3>

      {error && <div class="property-form__error">{error}</div>}

      <Input
        label="Label"
        name="label"
        value={label}
        onChange={setLabel}
        required
        placeholder="e.g., Date of Birth"
      />

      <Input
        label="Identifier"
        name="identifier"
        value={identifier}
        onChange={handleIdentifierChange}
        required
        error={identifierError ?? undefined}
        placeholder="e.g., dateOfBirth"
      />

      <Input
        label="Description"
        name="description"
        value={description}
        onChange={setDescription}
        multiline
        placeholder="Optional description"
      />

      <div class="property-form__field">
        <label class="property-form__label" htmlFor="domain-class">
          Domain Class <span class="property-form__required">*</span>
        </label>
        <select
          id="domain-class"
          class="property-form__select"
          value={domainClass}
          onChange={(e) => setDomainClass((e.target as HTMLSelectElement).value)}
          required
        >
          <option value="">Select a class...</option>
          {ontologyClasses.map((cls) => (
            <option key={cls.uri} value={cls.uri}>
              {cls.label}
            </option>
          ))}
        </select>
      </div>

      <div class="property-form__field">
        <label class="property-form__label">
          Range Type <span class="property-form__required">*</span>
        </label>
        <div class="property-form__radio-group">
          <label class="property-form__radio">
            <input
              type="radio"
              name="rangeType"
              value="scheme"
              checked={rangeType === "scheme"}
              onChange={() => setRangeType("scheme")}
            />
            <span>Scheme</span>
          </label>
          <label class="property-form__radio">
            <input
              type="radio"
              name="rangeType"
              value="datatype"
              checked={rangeType === "datatype"}
              onChange={() => setRangeType("datatype")}
            />
            <span>Datatype</span>
          </label>
        </div>
      </div>

      {rangeType === "scheme" ? (
        <div class="property-form__field">
          <label class="property-form__label" htmlFor="range-scheme">
            Range Scheme <span class="property-form__required">*</span>
          </label>
          <select
            id="range-scheme"
            class="property-form__select"
            value={rangeSchemeId}
            onChange={(e) => setRangeSchemeId((e.target as HTMLSelectElement).value)}
            required
          >
            <option value="">Select a scheme...</option>
            {projectSchemes.map((scheme) => (
              <option key={scheme.id} value={scheme.id}>
                {scheme.title}
              </option>
            ))}
          </select>
        </div>
      ) : (
        <div class="property-form__field">
          <label class="property-form__label" htmlFor="range-datatype">
            Range Datatype <span class="property-form__required">*</span>
          </label>
          <select
            id="range-datatype"
            class="property-form__select"
            value={rangeDatatype}
            onChange={(e) => setRangeDatatype((e.target as HTMLSelectElement).value)}
            required
          >
            <option value="">Select a datatype...</option>
            {ALLOWED_DATATYPES.map((dt) => (
              <option key={dt} value={dt}>
                {dt}
              </option>
            ))}
          </select>
        </div>
      )}

      <div class="property-form__field">
        <label class="property-form__label">Cardinality</label>
        <div class="property-form__radio-group">
          <label class="property-form__radio">
            <input
              type="radio"
              name="cardinality"
              value="single"
              checked={cardinality === "single"}
              onChange={() => setCardinality("single")}
            />
            <span>Single value</span>
          </label>
          <label class="property-form__radio">
            <input
              type="radio"
              name="cardinality"
              value="multiple"
              checked={cardinality === "multiple"}
              onChange={() => setCardinality("multiple")}
            />
            <span>Multiple values</span>
          </label>
        </div>
      </div>

      <div class="property-form__field">
        <label class="property-form__checkbox">
          <input
            type="checkbox"
            checked={required}
            onChange={(e) => setRequired((e.target as HTMLInputElement).checked)}
          />
          <span>Required</span>
        </label>
      </div>

      <div class="property-form__actions">
        <Button variant="secondary" onClick={onCancel} disabled={submitLoading}>
          Cancel
        </Button>
        <Button type="submit" disabled={!isValid || submitLoading}>
          {submitLoading ? "Creating..." : "Create Property"}
        </Button>
      </div>
    </form>
  );
}
