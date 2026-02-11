import { useState, useEffect } from "preact/hooks";
import { Button } from "../common/Button";
import { Input } from "../common/Input";
import { propertiesApi } from "../../api/properties";
import { ApiError } from "../../api/client";
import { ontologyApi } from "../../api/ontology";
import { schemes } from "../../state/schemes";
import type { OntologyClass, PropertyCreate } from "../../types/models";
import "./PropertyForm.css";

interface PropertyFormProps {
  projectId: string;
  domainClassUri?: string;
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
  // Already looks like an identifier — just lcfirst
  if (/^[a-zA-Z][a-zA-Z0-9]*$/.test(str)) {
    return str[0].toLowerCase() + str.slice(1);
  }
  let result = str
    .toLowerCase()
    .replace(/[^a-zA-Z0-9]+(.)/g, (_, char) => char.toUpperCase())
    .replace(/^./, (char) => char.toLowerCase())
    .replace(/[^a-zA-Z0-9]/g, "");
  if (result && !result[0].match(/[a-zA-Z]/)) {
    result = "prop-" + result;
  }
  return result;
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

export function PropertyForm({ projectId, domainClassUri, onSuccess, onCancel }: PropertyFormProps) {
  // Form state
  const [label, setLabel] = useState("");
  const [identifier, setIdentifier] = useState("");
  const [identifierTouched, setIdentifierTouched] = useState(false);
  const [description, setDescription] = useState("");
  const [domainClass, setDomainClass] = useState(domainClassUri ?? "");
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

  // Sync domainClass state when prop changes (handles case where prop arrives after mount)
  useEffect(() => {
    if (domainClassUri) {
      setDomainClass(domainClassUri);
    }
  }, [domainClassUri]);

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
  const hasLabel = !!label.trim();
  const hasIdentifier = !!identifier.trim();
  const hasValidIdentifier = !identifierError;
  const hasDomainClass = !!domainClass;
  const hasRangeValue = rangeType === "scheme" ? !!rangeSchemeId : !!rangeDatatype;

  const isValid = hasLabel && hasIdentifier && hasValidIdentifier && hasDomainClass && hasRangeValue;

  function getMissingFields(): string[] {
    const missing: string[] = [];
    if (!hasLabel) missing.push("Label");
    if (!hasIdentifier) missing.push("Identifier");
    else if (!hasValidIdentifier) missing.push("Valid identifier");
    if (!hasDomainClass) missing.push("Domain class");
    if (!hasRangeValue) missing.push(rangeType === "scheme" ? "Range scheme" : "Range datatype");
    return missing;
  }

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
      range_scheme_id: rangeType === "scheme" ? rangeSchemeId || undefined : undefined,
      range_datatype: rangeType === "datatype" ? rangeDatatype || undefined : undefined,
      cardinality,
      required,
    };

    try {
      await propertiesApi.create(projectId, data);
      onSuccess();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("A property with this identifier already exists");
      } else {
        setError(err instanceof Error ? err.message : "Failed to create property");
      }
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

      {error && <div class="property-form__error" role="alert">{error}</div>}

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
        {domainClassUri ? (
          <div class="property-form__class-display">
            {ontologyClasses.find((c) => c.uri === domainClassUri)?.label ?? domainClassUri}
          </div>
        ) : (
          <select
            id="domain-class"
            class="property-form__select"
            value={domainClass}
            aria-required="true"
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
        )}
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
              disabled={projectSchemes.length === 0}
              onChange={() => setRangeType("scheme")}
            />
            <span>Scheme</span>
            {projectSchemes.length === 0 && (
              <span class="property-form__hint" style="font-style: italic">Create a scheme first</span>
            )}
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

      {!isValid && !submitLoading && (
        <div class="property-form__missing" aria-live="polite">
          Still needed: {getMissingFields().join(", ")}
        </div>
      )}

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
