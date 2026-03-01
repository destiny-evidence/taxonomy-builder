# Ontology expressivity: what the builder can and cannot represent

**Epic:** [#108](https://github.com/destiny-evidence/taxonomy-builder/issues/108)
**Date:** 2026-03-02

## Introduction

The taxonomy builder is a general-purpose tool for managing OWL/SKOS vocabularies. It lets users who are not familiar with OWL or SKOS create and iterate on controlled vocabularies — concept schemes, ontology classes, and properties — through a web interface.

The first domain application of the builder is the education evidence repository, which uses a two-layer vocabulary architecture to describe structured research evidence. That vocabulary has grown to use OWL/RDFS features that the builder cannot yet represent. This document explains what those features are, why the domain needs them, and how the builder should evolve to support them.

The audience is developers working on the taxonomy builder. Each gap is explained through the concrete domain pattern that motivates it, not as an abstract OWL exercise.

## The two-layer vocabulary architecture

The evidence repository vocabulary is split across two namespaces:

- **evrepo** (`https://evrepo.example.org/vocab/`) — domain-agnostic core. Defines the evidence graph structure (Investigation → Finding → Intervention/Outcome/Context), the CodingAnnotation provenance pattern, ObservedResult/EffectEstimate statistical classes, and the Condition hierarchy. Shared across education, health, and climate sectors.
- **esea** (`https://esea.example.org/vocab/`) — education-specific extension. Defines SKOS concept schemes (education level, outcome, setting, etc.) and education-specific properties that extend the core.

The builder manages the domain vocabulary layer — concept schemes with their concepts, ontology classes, and properties. The core ontology was originally loaded as a static file at startup; since [#93](https://github.com/destiny-evidence/taxonomy-builder/issues/93), classes and properties are fully project-scoped. The canonical vocabulary files live in [`vocab/`](../../vocab/) — `evrepo-core/` for the shared foundation and `esea/` for the education extension. Note that `evrepo-core.ttl` is a working draft — it defines the core classes and properties (Investigation, Finding, Intervention, etc.) but does not yet include the CodingAnnotation pattern, ObservedResult, Condition hierarchy, or provenance properties described in this document. Those are defined in the JSON-LD context and examples but await formal OWL definitions in the TTL.

The builder is not education-specific. The evrepo/esea vocabulary is one domain application. A health or climate domain would define its own extension vocabulary. Issue [#99](https://github.com/destiny-evidence/taxonomy-builder/issues/99) proposes a template picker that would let users bootstrap a new project from bundled TTL files, replacing the current seed-data approach which hard-codes evidence-synthesis classes for developer convenience.

### The evidence graph

The core ontology defines this structure:

```
Reference (bibliographic record, identified by DOI)
  └─ LinkedDataEnhancement
       └─ Investigation (one per study within a paper)
            ├─ documentType, funderResearch, isRetracted, dataSource
            └─ Finding (one per comparison × outcome)
                 ├─ evaluates → Intervention
                 ├─ comparedTo → ControlCondition | TemporalCondition
                 ├─ hasContext → Context
                 ├─ hasOutcome → Outcome
                 ├─ hasArmData → ObservedResult[] (per-arm stats)
                 └─ hasEffectEstimate → EffectEstimate[]
```

A Finding is the atomic unit of evidence — one pairwise comparison for one outcome. A paper with 3 comparisons × 2 outcomes produces 6 Findings under the same Investigation.

## What the builder represents today

The builder's data model stores three entity types per project:

| Entity | What it stores | Published format |
|--------|---------------|-----------------|
| **Concept Scheme** | Title, URI, concepts with hierarchy (broader/narrower DAG) | `schemes[]` with flat concept map, `top_concepts` array |
| **Ontology Class** | Identifier, URI, label, description, scope note | `classes[]` flat array |
| **Property** | Identifier, URI, label, domain class (single), range (one of: scheme, class, or datatype), cardinality | `properties[]` with `domain_class_uri` and exactly one of `range_scheme_id`, `range_class`, `range_datatype` |

The published vocabulary format ([`docs/published-format/`](../published-format/README.md)) serialises these into static JSON files consumed by the reader frontend. The vocabulary JSON schema ([`vocabulary.schema.json`](../published-format/vocabulary.schema.json)) enforces the property range constraint: each property must have exactly one range type. The example files ([`example/`](../published-format/example/)) demonstrate a minimal project with classes, a scheme, and a property with `range_scheme_id` set, `range_class: null`, and `range_datatype: null`.

For SKOS export, the builder serialises concept schemes as standard SKOS Turtle, RDF/XML, or JSON-LD via the `SKOSExportService`. Classes and properties are included with basic OWL type declarations. Version metadata in exports is tracked in [#118](https://github.com/destiny-evidence/taxonomy-builder/issues/118).

This model covers simple vocabularies well. But the evidence repository core ontology uses five OWL/RDFS features that fall outside what the builder can represent.

## The five gaps

### 1. Class hierarchies — `rdfs:subClassOf`

**Issue:** [#109](https://github.com/destiny-evidence/taxonomy-builder/issues/109) — Subclass relationships between ontology classes
**Priority:** High (blocking)

#### The domain pattern: Conditions

The `evaluates`/`comparedTo` structure on a Finding needs to work uniformly across study designs. A Finding evaluates one Condition compared to another. Condition is a superclass with three subclasses:

- **Intervention** — an active treatment or programme (carries educationTheme, duration, implementerType)
- **ControlCondition** — business-as-usual, waitlist, active control
- **TemporalCondition** — a time-defined measurement occasion (pre-test, post-test, follow-up)

For a standard RCT, `evaluates` points to an Intervention and `comparedTo` points to a ControlCondition. For a pre-post design, both may be TemporalConditions. Without the subclass hierarchy, each study design would need its own relationship pattern.

The same pattern appears in CodingAnnotation (see [gap 3](#3-property-type-distinctions)) where `StringCodingAnnotation`, `NumericCodingAnnotation`, and domain-specific subclasses constrain the type of `codedValue`.

```turtle
evrepo:Condition a owl:Class .
evrepo:Intervention rdfs:subClassOf evrepo:Condition .
evrepo:ControlCondition rdfs:subClassOf evrepo:Condition .
evrepo:TemporalCondition rdfs:subClassOf evrepo:Condition .
```

See [`patterns/condition-hierarchy.jsonld`](patterns/condition-hierarchy.jsonld) for a worked example.

#### What breaks without it

The builder models classes as a flat list. You can create Condition, Intervention, ControlCondition, and TemporalCondition as separate classes, but there is no way to express that Intervention *is a kind of* Condition. This means:

- The export cannot emit `rdfs:subClassOf` triples
- The UI cannot render a class tree (it renders a flat list)
- Properties with `rdfs:domain evrepo:Condition` cannot be understood as applying to all three subclasses

#### Proposed solution

An association table `class_superclass` (following the same pattern as `ConceptBroader`) with cycle detection. The API exposes `POST/DELETE /api/classes/{id}/superclass`. The frontend renders classes as a tree, reusing the existing tree infrastructure from concepts. See [#109](https://github.com/destiny-evidence/taxonomy-builder/issues/109) for the full design.

#### Impact on published format

The `classes[]` array in `vocabulary.schema.json` would need a `superclasses` field (array of class URIs), similar to how concepts have `broader`.

---

### 2. Multi-domain properties — `owl:unionOf`

**Issue:** [#110](https://github.com/destiny-evidence/taxonomy-builder/issues/110) — Multi-domain properties (union domains)
**Priority:** High (blocking)

#### The domain pattern: provenance across classes

The CodingAnnotation pattern wraps every coded value with provenance — who coded it, the supporting text from the source document, and a status. But the same provenance properties also appear on ObservedResult and EffectEstimate (which carry their own class-level provenance *without* the CodingAnnotation wrapper).

This means `supportingText`, `codedBy`, and `sourceLocation` each need to apply to three unrelated classes:

```turtle
evrepo:supportingText a owl:DatatypeProperty ;
    rdfs:domain [ owl:unionOf (
        evrepo:CodingAnnotation
        evrepo:ObservedResult
        evrepo:EffectEstimate
    ) ] ;
    rdfs:range xsd:string .
```

See [`patterns/union-domain-properties.ttl`](patterns/union-domain-properties.ttl) for the full Turtle.

#### What breaks without it

The builder's `Property` model has a single `domain_class` field (a VARCHAR holding one class URI). There is no way to express that `supportingText` applies to CodingAnnotation, ObservedResult, *and* EffectEstimate. You would have to either:

- Create three separate properties (`supportingText_coding`, `supportingText_observed`, `supportingText_effect`) — semantically wrong, bloats the UI
- Pick one domain class and accept that the export is incomplete
- Omit the domain entirely — loses information

#### Proposed solution

Replace the single `domain_class` field with a many-to-many relationship. The API accepts `domain_classes: list[str]`. The export emits `rdfs:domain [ owl:unionOf (...) ]` for multi-domain properties, or plain `rdfs:domain <class>` for single-domain. Migration converts existing single values to single-element lists. See [#110](https://github.com/destiny-evidence/taxonomy-builder/issues/110) for details.

#### Impact on published format

The `domain_class_uri` field in `vocabulary.schema.json` would change from a single string to an array of strings, or a parallel `domain_class_uris` field would be added.

---

### 3. Property type distinctions

**Issue:** [#111](https://github.com/destiny-evidence/taxonomy-builder/issues/111) — Property type distinction (ObjectProperty / DatatypeProperty / rdf:Property)
**Priority:** Medium

#### The domain pattern: polymorphic `codedValue`

RDF/OWL distinguishes three kinds of properties:

- `owl:ObjectProperty` — links to another resource (e.g. `evaluates` → Intervention)
- `owl:DatatypeProperty` — links to a literal value (e.g. `effectSize` → xsd:decimal)
- `rdf:Property` — intentionally untyped, can link to either

The builder infers property kind from the range: if range is a class or scheme, it's an ObjectProperty; if range is a datatype, it's a DatatypeProperty. This works for most properties but fails for `codedValue`.

`codedValue` is the core of the CodingAnnotation pattern. On a concept-valued annotation (like EducationLevelCodingAnnotation), `codedValue` points to a SKOS concept — an object. On a StringCodingAnnotation, `codedValue` holds a string — a literal. On a NumericCodingAnnotation, a decimal. The property is intentionally polymorphic, declared as `rdf:Property` rather than either `owl:ObjectProperty` or `owl:DatatypeProperty`.

See [`patterns/coding-annotation-pattern.jsonld`](patterns/coding-annotation-pattern.jsonld) for all three CodingAnnotation types in use.

#### What breaks without it

The builder has no way to represent `rdf:Property`. When exporting, it would emit either `owl:ObjectProperty` or `owl:DatatypeProperty` based on the range, which is incorrect for the polymorphic case. OWL reasoners treat this distinction as meaningful — declaring `codedValue` as an ObjectProperty would make literal values invalid.

#### Proposed solution

Add a `property_type` field to the Property model with values `"object"`, `"datatype"`, and `"rdf"`. Default is inferred from range fields for backwards compatibility. Explicitly settable for the `rdf:Property` case. The export emits the correct RDF type declaration. See [#111](https://github.com/destiny-evidence/taxonomy-builder/issues/111).

#### Impact on published format

A new `property_type` field in the properties schema. Existing consumers can ignore it since the range fields still determine behaviour.

---

### 4. Enumeration classes — `owl:oneOf`

**Issue:** [#112](https://github.com/destiny-evidence/taxonomy-builder/issues/112) — Named individuals and enumeration classes
**Priority:** Low (workaround available)

#### The domain pattern: CodingStatus

Every CodingAnnotation carries a `status` that records whether the value has been coded, is not applicable, or is not reported. This is modelled as an enumeration — a closed set of exactly three named individuals:

```turtle
evrepo:CodingStatus a owl:Class ;
    owl:oneOf (evrepo:coded evrepo:notApplicable evrepo:notReported) .

evrepo:coded a owl:NamedIndividual, evrepo:CodingStatus .
evrepo:notApplicable a owl:NamedIndividual, evrepo:CodingStatus .
evrepo:notReported a owl:NamedIndividual, evrepo:CodingStatus .
```

The fourth state — "not yet coded" — is represented by the absence of a CodingAnnotation entirely.

See [`patterns/enumeration-class.ttl`](patterns/enumeration-class.ttl) for the full Turtle.

#### What breaks without it

The builder has no concept of named individuals or `owl:oneOf`. It cannot represent the constraint that CodingStatus has exactly three members and no others.

#### Pragmatic workaround

Model enumeration classes as concept schemes. CodingStatus becomes a concept scheme with three concepts (coded, notApplicable, notReported). This is semantically close — concept schemes are controlled vocabularies — and reuses existing infrastructure. At export time, the exporter could optionally emit the `owl:oneOf` / `owl:NamedIndividual` pattern instead of SKOS, triggered by a flag on the scheme.

This workaround is recommended for now. Native named individual support would only be needed if the pattern becomes common enough to justify a new entity type. See [#112](https://github.com/destiny-evidence/taxonomy-builder/issues/112).

#### Impact on published format

None if using the concept scheme workaround. If native support is added later, a new `individuals` entity type would be needed.

---

### 5. Export-time OWL features

**Issue:** [#113](https://github.com/destiny-evidence/taxonomy-builder/issues/113) — Export-time OWL features (concept subclasses, restrictions, type bridge)
**Priority:** Low (deferrable)

#### The domain patterns

Three patterns in the core ontology don't require data model changes but need correct handling during serialisation:

**Concept-typed class subclasses.** Each concept scheme has a corresponding OWL class that is a subclass of `skos:Concept`. For example, EducationLevel concepts are instances of both `skos:Concept` and `esea:EducationLevel`. This dual-typing enables OWL property range constraints on the concept class while preserving SKOS compatibility.

```turtle
esea:EducationLevel rdfs:subClassOf skos:Concept .
esea:C1020 a skos:Concept, esea:EducationLevel .
```

**OWL restrictions.** CodingAnnotation subclasses use OWL restrictions to constrain `codedValue`. For example, `NumericCodingAnnotation` restricts `codedValue` to `xsd:decimal`. This is deep OWL DL machinery that the builder does not need to author — it can be emitted at export time from conventions.

**Concept-type bridge.** An optional `concept_type_class` field on ConceptScheme would allow the exporter to automatically emit the class declaration and dual-type all concepts. This is a small additive change.

#### Relationship to other gaps

These are all export concerns. The data authored in the builder is correct without them — only the serialised output needs the OWL decorations. They depend on [#62](https://github.com/destiny-evidence/taxonomy-builder/issues/62) (published document formats) for delivery. The concept-type bridge depends on [#109](https://github.com/destiny-evidence/taxonomy-builder/issues/109) for the `rdfs:subClassOf skos:Concept` emission.

#### Impact on published format

The Turtle and JSON-LD exports would include additional triples. The published JSON format is unaffected — it already has `classes[]` and `schemes[]` as separate arrays, and the bridge between them is an export-time concern.

## Build-time vs export-time

The five gaps fall into two categories:

| Category | Issues | What changes |
|----------|--------|-------------|
| **Data model** (build-time) | #109, #110, #111 | Database schema, API, UI, published JSON format |
| **Serialisation** (export-time) | #112 (workaround), #113 | Turtle/JSON-LD export only |

The data model changes (#109–#111) must be implemented in the builder. Without them, the builder literally cannot store the information. These affect the database schema, the API, the frontend, and the published JSON format.

The serialisation changes (#112–#113) can be handled by a smarter exporter. The builder stores concept schemes and classes; the exporter decides whether to emit `owl:oneOf` for an enumeration or `rdfs:subClassOf skos:Concept` for a concept class. The data in the builder is complete — the export adds OWL decorations.

### Dependency chain

```
#109 (subclasses) ─┐
#110 (union domains)├── #62 (published formats) ── #113 (export-time OWL)
#111 (property types)┘                              │
                                                     └── #112 (enumerations, if native)
```

Issues #109, #110, and #111 are independent of each other and can be implemented in parallel. All three feed into #62 (published document formats), which is the delivery vehicle for correct Turtle/JSON-LD export. Issue #113 is deferred until #62 is in progress. Issue #112 uses a concept scheme workaround and does not block anything.

## How published formats need to change

The published JSON format (`vocabulary.schema.json`) will need the following changes as the data model issues are resolved:

| Change | Triggered by | Schema impact |
|--------|-------------|--------------|
| `superclasses` on classes | #109 | `classes[].superclasses: string[]` (array of class URIs) |
| Multi-domain properties | #110 | `properties[].domain_class_uris: string[]` replacing single `domain_class_uri` |
| Property type field | #111 | `properties[].property_type: "object" \| "datatype" \| "rdf"` |

The Turtle/JSON-LD export formats will need:

| Change | Triggered by |
|--------|-------------|
| `rdfs:subClassOf` triples | #109 |
| `owl:unionOf` domain expressions | #110 |
| Correct `owl:ObjectProperty` / `owl:DatatypeProperty` / `rdf:Property` declarations | #111 |
| `owl:oneOf` for enumerations (optional) | #112 |
| Dual-typed concepts, OWL restrictions | #113 |

## Mapping real data

The ontology patterns described above are not theoretical — they exist to support the transformation of existing research datasets into a shared semantic format. Two worked examples demonstrate how real source data maps into the evidence graph, and why the builder needs to represent these OWL features. See [**Mapping examples**](mapping-examples.md) for detailed walkthroughs of each.

## Example files

### OWL pattern illustrations ([`patterns/`](patterns/))

Focused examples of the OWL/RDFS features the builder needs to support:

| File | Pattern |
|------|---------|
| [`coding-annotation-pattern.jsonld`](patterns/coding-annotation-pattern.jsonld) | CodingAnnotation wrapping — String, Numeric, concept-valued; status enumeration |
| [`condition-hierarchy.jsonld`](patterns/condition-hierarchy.jsonld) | Condition subclass hierarchy — evaluates/comparedTo across study designs |
| [`observed-result-per-arm.jsonld`](patterns/observed-result-per-arm.jsonld) | Per-arm ObservedResults linked via forCondition; class-level provenance |
| [`union-domain-properties.ttl`](patterns/union-domain-properties.ttl) | Union domains — supportingText/codedBy across three classes |
| [`enumeration-class.ttl`](patterns/enumeration-class.ttl) | owl:oneOf enumeration — CodingStatus with three named individuals |

### Worked mapping examples ([`worked-examples/`](worked-examples/))

Real data mapped into the evidence graph. See [mapping-examples.md](mapping-examples.md) for detailed walkthroughs.

| File | Description |
|------|-------------|
| [`3ie-study-34810-source.csv`](worked-examples/3ie-study-34810-source.csv) | Source data — raw 3ie DEP rows for study 34810 (3 rows, 52 columns) |
| [`3ie-mapping-example.jsonld`](worked-examples/3ie-mapping-example.jsonld) | Study 34810 mapped from the CSV above into the nested evidence graph |
| [`vocab/esea/example-finding.jsonld`](../../vocab/esea/example-finding.jsonld) | EEF cluster RCT with full quantitative data (canonical, lives in vocab/) |

The canonical vocabulary files are in [`vocab/`](../../vocab/):

| File | Description |
|------|-------------|
| [`evrepo-core/evrepo-core.ttl`](../../vocab/evrepo-core/evrepo-core.ttl) | Core ontology — classes and properties for evidence graph structure |
| [`esea/esea-vocab.ttl`](../../vocab/esea/esea-vocab.ttl) | ESEA vocabulary — education-specific concept schemes, classes, and properties |
| [`esea/esea-context.jsonld`](../../vocab/esea/esea-context.jsonld) | JSON-LD @context for serialisation |
| [`esea/example-finding.jsonld`](../../vocab/esea/example-finding.jsonld) | Worked example — cluster RCT with per-arm data |
