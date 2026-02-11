import { useState, useEffect } from "preact/hooks";
import { Input } from "../common/Input";
import { Button } from "../common/Button";
import { propertiesApi } from "../../api/properties";
import { ApiError } from "../../api/client";
import type { Property, ConceptScheme, OntologyClass } from "../../types/models";
import "./PropertyForm.css";

const ALLOWED_DATATYPES = [
  "xsd:string",
  "xsd:integer",
  "xsd:decimal",
  "xsd:boolean",
  "xsd:date",
  "xsd:dateTime",
  "xsd:anyURI",
];

const IDENTIFIER_PATTERN = /^[a-zA-Z][a-zA-Z0-9_-]*$/;

export function labelToIdentifier(label: string): string {
  let slug = label
    .replace(/[^\x20-\x7E]/g, "") // strip non-ASCII
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "") // strip punctuation
    .trim()
    .replace(/[\s-]+/g, "-") // collapse whitespace/hyphens
    .replace(/^-+|-+$/g, ""); // trim leading/trailing hyphens

  if (!slug) return "";

  if (/^[0-9]/.test(slug)) {
    slug = `prop-${slug}`;
  }

  return slug;
}

interface PropertyFormProps {
  projectId: string;
  schemes: ConceptScheme[];
  ontologyClasses: OntologyClass[];
  property?: Property | null;
  onSuccess: () => void;
  onCancel: () => void;
}

type RangeType = "scheme" | "datatype";

export function PropertyForm({
  projectId,
  schemes,
  ontologyClasses,
  property,
  onSuccess,
  onCancel,
}: PropertyFormProps) {
  const isEdit = !!property;

  const [label, setLabel] = useState(property?.label ?? "");
  const [identifier, setIdentifier] = useState(property?.identifier ?? "");
  const [identifierTouched, setIdentifierTouched] = useState(isEdit);
  const [description, setDescription] = useState(property?.description ?? "");
  const [domainClass, setDomainClass] = useState(property?.domain_class ?? "");
  const [rangeType, setRangeType] = useState<RangeType>(() => {
    if (property?.range_datatype) return "datatype";
    if (property?.range_scheme_id) return "scheme";
    return schemes.length > 0 ? "scheme" : "datatype";
  });
  const [rangeSchemeId, setRangeSchemeId] = useState(property?.range_scheme_id ?? "");
  const [rangeDatatype, setRangeDatatype] = useState(property?.range_datatype ?? "");
  const [cardinality, setCardinality] = useState<"single" | "multiple">(
    property?.cardinality ?? "single"
  );
  const [required, setRequired] = useState(property?.required ?? false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [identifierError, setIdentifierError] = useState<string | null>(null);

  // Sync form state when property prop changes
  useEffect(() => {
    setLabel(property?.label ?? "");
    setIdentifier(property?.identifier ?? "");
    setIdentifierTouched(!!property);
    setDescription(property?.description ?? "");
    setDomainClass(property?.domain_class ?? "");
    if (property?.range_datatype) setRangeType("datatype");
    else if (property?.range_scheme_id) setRangeType("scheme");
    else setRangeType(schemes.length > 0 ? "scheme" : "datatype");
    setRangeSchemeId(property?.range_scheme_id ?? "");
    setRangeDatatype(property?.range_datatype ?? "");
    setCardinality(property?.cardinality ?? "single");
    setRequired(property?.required ?? false);
    setError(null);
    setIdentifierError(null);
  }, [property]);

  function handleLabelChange(value: string) {
    setLabel(value);
    if (!identifierTouched) {
      const generated = labelToIdentifier(value);
      setIdentifier(generated);
      validateIdentifier(generated);
    }
  }

  function handleIdentifierChange(value: string) {
    setIdentifierTouched(true);
    setIdentifier(value);
    validateIdentifier(value);
  }

  function validateIdentifier(value: string) {
    if (value && !IDENTIFIER_PATTERN.test(value)) {
      setIdentifierError("Must start with a letter and contain only letters, numbers, hyphens, or underscores");
    } else {
      setIdentifierError(null);
    }
  }

  function handleRangeTypeChange(type: RangeType) {
    setRangeType(type);
    if (type === "scheme") {
      setRangeDatatype("");
    } else {
      setRangeSchemeId("");
    }
  }

  const hasSchemes = schemes.length > 0;
  const rangeValid =
    (rangeType === "scheme" && rangeSchemeId) ||
    (rangeType === "datatype" && rangeDatatype);

  function getMissingFields(): string[] {
    const missing: string[] = [];
    if (!label.trim()) missing.push("Label");
    if (!identifier.trim()) missing.push("Identifier");
    else if (identifierError) missing.push("Identifier (invalid)");
    if (!domainClass) missing.push("Applies to");
    if (!rangeValid) missing.push(rangeType === "scheme" ? "Scheme selection" : "Datatype selection");
    return missing;
  }

  const hasChanges = !isEdit || (
    label !== (property?.label ?? "") ||
    description !== (property?.description ?? "") ||
    domainClass !== (property?.domain_class ?? "") ||
    rangeSchemeId !== (property?.range_scheme_id ?? "") ||
    rangeDatatype !== (property?.range_datatype ?? "") ||
    cardinality !== (property?.cardinality ?? "single") ||
    required !== (property?.required ?? false)
  );

  const missingFields = getMissingFields();
  const canSubmit = missingFields.length === 0 && hasChanges && !loading;

  async function handleSubmit(e: Event) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isEdit) {
        await propertiesApi.update(property!.id, {
          label,
          description: description || null,
          domain_class: domainClass,
          range_scheme_id: rangeType === "scheme" ? rangeSchemeId : null,
          range_datatype: rangeType === "datatype" ? rangeDatatype : null,
          cardinality,
          required,
        });
      } else {
        await propertiesApi.create(projectId, {
          identifier,
          label,
          description: description || null,
          domain_class: domainClass,
          range_scheme_id: rangeType === "scheme" ? rangeSchemeId : null,
          range_datatype: rangeType === "datatype" ? rangeDatatype : null,
          cardinality,
          required,
        });
      }
      onSuccess();
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 409) {
          setError("A property with this identifier already exists");
        } else {
          setError(err.message);
        }
      } else {
        setError(err instanceof Error ? err.message : "An error occurred");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <form class="property-form" onSubmit={handleSubmit} role="form">
      {error && <div class="property-form__error" role="alert">{error}</div>}

      <Input
        label="Label"
        name="label"
        value={label}
        placeholder="Display name for this property"
        required
        onChange={handleLabelChange}
      />

      <div class={`input-field ${identifierError ? "input-field--error" : ""}`}>
        <label class="input-field__label" for="input-identifier">
          Identifier<span class="input-field__required">*</span>
        </label>
        <input
          id="input-identifier"
          name="identifier"
          type="text"
          class="input-field__input"
          value={identifier}
          placeholder="auto-generated-from-label"
          readOnly={isEdit}
          aria-required="true"
          aria-invalid={!!identifierError}
          aria-describedby={identifierError ? "identifier-error" : undefined}
          onInput={(e) => handleIdentifierChange(e.currentTarget.value)}
        />
        {identifierError && (
          <span id="identifier-error" class="input-field__error" role="alert">{identifierError}</span>
        )}
      </div>

      <Input
        label="Description"
        name="description"
        value={description}
        placeholder="Optional description"
        multiline
        onChange={setDescription}
      />

      <div class="input-field">
        <label class="input-field__label" for="input-domain-class">
          Applies to<span class="input-field__required">*</span>
        </label>
        <select
          id="input-domain-class"
          class="input-field__input"
          value={domainClass}
          aria-required="true"
          onChange={(e) => setDomainClass(e.currentTarget.value)}
        >
          <option value="">Select a class...</option>
          {ontologyClasses.map((cls) => (
            <option key={cls.uri} value={cls.uri}>
              {cls.label}
            </option>
          ))}
        </select>
      </div>

      <fieldset class="property-form__fieldset">
        <legend class="property-form__legend">Range</legend>
        <div class="property-form__range-toggle">
          <label class="property-form__radio-label">
            <input
              type="radio"
              name="range-type"
              value="scheme"
              checked={rangeType === "scheme"}
              disabled={!hasSchemes}
              onChange={() => handleRangeTypeChange("scheme")}
            />
            Concept Scheme
            {!hasSchemes && (
              <span class="property-form__hint">Create a scheme first</span>
            )}
          </label>
          <label class="property-form__radio-label">
            <input
              type="radio"
              name="range-type"
              value="datatype"
              checked={rangeType === "datatype"}
              onChange={() => handleRangeTypeChange("datatype")}
            />
            Datatype
          </label>
        </div>

        {rangeType === "scheme" && hasSchemes && (
          <select
            class="input-field__input"
            value={rangeSchemeId}
            onChange={(e) => setRangeSchemeId(e.currentTarget.value)}
            aria-label="Scheme select"
          >
            <option value="">Select a scheme...</option>
            {schemes.map((s) => (
              <option key={s.id} value={s.id}>
                {s.title}
              </option>
            ))}
          </select>
        )}

        {rangeType === "datatype" && (
          <select
            class="input-field__input"
            value={rangeDatatype}
            onChange={(e) => setRangeDatatype(e.currentTarget.value)}
            aria-label="Datatype select"
          >
            <option value="">Select a datatype...</option>
            {ALLOWED_DATATYPES.map((dt) => (
              <option key={dt} value={dt}>
                {dt}
              </option>
            ))}
          </select>
        )}
      </fieldset>

      <fieldset class="property-form__fieldset">
        <legend class="property-form__legend">Cardinality</legend>
        <div class="property-form__range-toggle">
          <label class="property-form__radio-label">
            <input
              type="radio"
              name="cardinality"
              value="single"
              checked={cardinality === "single"}
              onChange={() => setCardinality("single")}
            />
            Single
          </label>
          <label class="property-form__radio-label">
            <input
              type="radio"
              name="cardinality"
              value="multiple"
              checked={cardinality === "multiple"}
              onChange={() => setCardinality("multiple")}
            />
            Multiple
          </label>
        </div>
      </fieldset>

      <label class="property-form__checkbox-label">
        <input
          type="checkbox"
          checked={required}
          onChange={(e) => setRequired(e.currentTarget.checked)}
        />
        Required
      </label>

      {!canSubmit && !loading && (
        <div class="property-form__missing" aria-live="polite">
          {missingFields.length > 0
            ? `Still needed: ${missingFields.join(", ")}`
            : "No changes to save"}
        </div>
      )}

      <div class="property-form__actions">
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={!canSubmit}>
          {loading ? "Saving..." : isEdit ? "Save Changes" : "Create Property"}
        </Button>
      </div>
    </form>
  );
}
