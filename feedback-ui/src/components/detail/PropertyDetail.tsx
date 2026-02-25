import { vocabulary, selectedVersion } from "../../state/vocabulary";
import { navigate } from "../../router";
import { FeedbackSection } from "../feedback/FeedbackSection";
import type { VocabProperty } from "../../api/published";

interface PropertyDetailProps {
  propertyId: string;
}

function findProperty(propertyId: string): VocabProperty | null {
  const vocab = vocabulary.value;
  if (!vocab) return null;
  return vocab.properties.find((p) => p.id === propertyId) ?? null;
}

export function PropertyDetail({ propertyId }: PropertyDetailProps) {
  const prop = findProperty(propertyId);
  if (!prop) return <div class="detail">Property not found</div>;

  // Resolve domain class label
  const domainClass = (vocabulary.value?.classes ?? []).find(
    (c) => c.uri === prop.domain_class_uri
  );

  // Resolve range scheme title
  const rangeScheme = prop.range_scheme_id
    ? (vocabulary.value?.schemes ?? []).find((s) => s.id === prop.range_scheme_id)
    : null;

  return (
    <div class="detail">
      <h1 class="detail__title">{prop.label}</h1>
      <div class="detail__uri">{prop.uri}</div>

      {prop.description && (
        <div class="detail__section">
          <div class="detail__label">Description</div>
          <div class="detail__text">{prop.description}</div>
        </div>
      )}

      <div class="detail__section">
        <div class="detail__label">Identifier</div>
        <div class="detail__text">{prop.identifier}</div>
      </div>

      <div class="detail__section">
        <div class="detail__meta-row">
          <div class="detail__meta-item">
            <strong>Domain: </strong>
            {domainClass ? (
              <span
                class="detail__link"
                onClick={() => {
                  const version = selectedVersion.value;
                  if (version) navigate(version, "class", domainClass.id);
                }}
              >
                {domainClass.label}
              </span>
            ) : (
              prop.domain_class_uri
            )}
          </div>

          <div class="detail__meta-item">
            <strong>Range: </strong>
            {rangeScheme ? (
              <span
                class="detail__link"
                onClick={() => {
                  const version = selectedVersion.value;
                  if (version) navigate(version, "scheme", rangeScheme.id);
                }}
              >
                {rangeScheme.title}
              </span>
            ) : (
              prop.range_datatype ?? "—"
            )}
          </div>

          <div class="detail__meta-item">
            <strong>Cardinality: </strong>
            {prop.cardinality}
          </div>

          <div class="detail__meta-item">
            <strong>Required: </strong>
            {prop.required ? "Yes" : "No"}
          </div>
        </div>
      </div>

      <FeedbackSection
        entityType="property"
        entityId={propertyId}
        entityLabel={prop.label}
      />
    </div>
  );
}
