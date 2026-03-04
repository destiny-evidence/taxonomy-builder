# Epic #108: Core Ontology Expressivity — Specification

## Overview

The evidence repository core ontology uses OWL/RDFS features that the taxonomy builder can't yet represent: class hierarchies (`rdfs:subClassOf`), multi-domain properties (`owl:unionOf`), property type distinctions (`rdf:Property` vs `owl:ObjectProperty` vs `owl:DatatypeProperty`), and concept dual-typing (concepts as instances of OWL classes). This epic adds end-to-end support for these constructs across the full pipeline: import → data model → snapshot → published JSON → export → builder UI → feedback UI.

Pushing exemplar EEF/EPPI data through the system is a high priority — the ESEA vocabulary is our first real customer dataset and the implementation must faithfully round-trip it.

The published format stays at version 1.0 (no customer has seen it yet) — the schema is updated in place and existing dev artifacts are purged.

For the earlier Codex-generated draft, see `docs/epic-108-issue-drafts-rewrite.md`.

## User Stories

- As a **vocabulary author**, I can import a TTL file with `rdfs:subClassOf` relationships and see them preserved in the builder, so that my class hierarchy is faithfully represented.
- As a **vocabulary author**, I can manually add/remove superclass relationships between classes, so that I can build hierarchies without importing.
- As a **vocabulary author**, I can import properties with `owl:unionOf` domains and have all domain classes stored, so that multi-domain properties aren't silently truncated.
- As a **vocabulary author**, I can assign multiple domain classes to a property in the builder, so that a property applies to several classes.
- As a **vocabulary author**, I can set a property's type to `rdf:Property` with no range constraint, so that polymorphic properties like `codedValue` are representable.
- As a **vocabulary author**, I can import concepts with OWL class types (e.g. `esea:EducationLevelConcept`) and have those types preserved on export, so that downstream tooling receives correct typing.
- As a **vocabulary reader**, I can see which classes a property applies to and what superclasses a class has, so that I understand the ontology structure.
- As a **vocabulary author**, I can export a project as TTL and get back a graph isomorphic to what I imported, so that I trust the tool isn't losing data.

---

## Decisions

### Published format and migration

**Stay on format version 1.0.** The published reader JSON schema (`vocabulary.schema.json`, `FORMAT_VERSION` in `reader_file_service.py`) currently declares version `"1.0"`. No customer has seen any published data yet — the first they'll see will include all #108 changes. Rather than bumping to `"2.0"` (which implies a breaking change from something that was never public), we keep `"1.0"` as the first public version and update its schema in place. This avoids the awkward optics of launching at version 2.0 and removes all compatibility/migration concerns.

**Purge existing published artifacts.** All existing published files in blob storage are internal dev/test data. Purge them as part of the format scaffold stripe. Republish everything fresh with the new schema shape. No version filtering in project indexes, no fallback rendering, no dual-read — there is simply nothing old to accommodate.

**Format scaffold as the first stripe.** All new fields (`superclasses`, `domain_class_uris`, `property_type`, concept `type_uris`) are added to the snapshot schema and published JSON with safe defaults (empty lists, inferred values). This means each subsequent stripe only needs to populate real data behind fields the format already expects. The `FORMAT_VERSION` stays `"1.0"` — the const in the schema and code doesn't change.

### Data model — class hierarchies (#109)

**DAG with multi-parent support and cycle rejection.** Class hierarchies follow the same pattern as concept broader/narrower relationships. A class can have multiple superclasses. Self-edges and cycles are rejected at import and API time via DFS cycle detection.

**`class_superclass` join table.** Follows the `ConceptBroader` pattern exactly: composite PK on `(class_id, superclass_id)`, both FK → `ontology_classes.id` with `CASCADE`. Relationship added to `OntologyClass` model with `lazy="selectin"`.

**External superclass URIs validated via allowlist.** When a class has `rdfs:subClassOf skos:Concept`, the target URI won't be in the project's class set. Rather than allowing any external URI (which wouldn't catch typos) or blocking all external URIs (which would reject valid ontologies), we maintain a small allowlist of well-known URIs: `skos:Concept`, `owl:Thing`, `rdfs:Resource`. Superclass URIs are validated against project classes plus this allowlist.

**Concept-typed classes imported as ontology classes (pending Andrew's confirmation).** The parser currently excludes classes that are `rdfs:subClassOf skos:Concept` (like `EffectSizeMetricConcept`) from the ontology class list. We propose removing this exclusion so they import as regular ontology classes, and their `rdfs:subClassOf skos:Concept` edge round-trips through the standard export code. This is necessary for the constraint system (Stripe 5) — restrictions reference these classes, and they only resolve if imported. Andrew initially said concept-typed classes should be an "export concern"; we've asked whether importing them is acceptable given the restriction dependency. If the class list gets noisy, a computed `concept_type_class` distinction can be derived from superclass URIs — no schema change needed, just UI filtering.

### Data model — concept dual-typing

**Concept OWL types preserved as `concept_type_uris`.** When importing ESEA vocabulary, concepts like `esea:C1010` are typed as both `skos:Concept` and `esea:EducationLevelConcept`. Currently the OWL type is silently dropped — only `skos:Concept` typing survives. Since EEF/EPPI is our first customer and their data pipeline expects these types, we preserve them.

The implementation is a narrow type-preservation slice: add `concept_type_uris: list[str]` to the Concept model (PostgreSQL ARRAY column), capture non-`skos:Concept` `rdf:type` URIs on import, carry them through the snapshot and published JSON, and emit them as extra `rdf:type` triples on export. Display is read-only in the first pass — editing concept types can be deferred.

### Data model — multi-domain properties (#110)

**`property_domain_class` join table.** Replaces the scalar `domain_class` column as the source of truth for which classes a property applies to. Composite PK on `(property_id, class_id)`, both FK with `CASCADE`.

**Scalar `domain_class` column kept during transition.** The join table is authoritative; the scalar is populated from the first (sorted) URI for backward compatibility. The column will be dropped in a future cleanup issue.

**Domain URIs sorted alphabetically.** OWL semantics say union order doesn't matter, but the RDF Collection export is ordered. Sorting alphabetically ensures deterministic output, simplifies diff/comparison, and avoids spurious changes in version history.

**Existing data is clean.** All properties currently have valid `domain_class` URIs pointing to project classes (confirmed by snapshot validation). The data migration from scalar to join table can assume clean data.

### Data model — property types (#111)

**Required `property_type` column.** Values: `"object"`, `"datatype"`, `"rdf"`. The parser already detects these types but never persists them. Added as NOT NULL with `server_default="object"`, backfilled: properties with `range_datatype` → `"datatype"`.

**`rdf:Property` allows 0 or 1 range.** All three range columns may be null for `rdf`-typed properties. `object` and `datatype` properties keep the strict exactly-one-range rule. This accommodates polymorphic properties like `codedValue` that intentionally have no fixed range.

### Builder UI

**Must-have for epic completion.** Import-only is not enough — authors need to create and edit all new features manually.

**Companion UI issues for each pipeline stripe.** Each existing pipeline issue (#109, #110, #111) gets a companion issue covering the API schema changes, service CRUD methods, builder components, and feedback-ui display for that feature. Pipeline and UI ship as separate PRs — pipeline first (data can flow), UI second (authors can interact). This keeps PRs reviewable and lets the pipeline be validated independently. Feedback-ui display work is folded into the companion UI issues rather than tracked separately.

**Superclass picker: simple dropdown.** Classes are few (5–15 per project). The dropdown excludes self and descendants to prevent cycles. Modal/search is overkill at this scale.

**Property type → range enforcement in UI.** Selecting a property type immediately filters available range options: `"object"` shows scheme or class pickers, `"datatype"` shows XSD type picker, `"rdf"` shows all options plus "No range constraint." This prevents invalid combinations before the user tries to save.

**Applicability closure deferred.** ClassDetailPane ships with exact-match filtering (`domain_class_uris.includes(classUri)`). The `classAncestors` computed signal, `isApplicable` helper, and inherited property display are a follow-up issue. No ancestor traversal infrastructure is built until then.

### Testing and seed data

**Golden roundtrip tests.** Fixture-driven: TTL → import → snapshot → publish → export → `rdflib.compare.isomorphic()` against original graph. `isomorphic()` handles blank-node comparison (fresh `BNode()` IDs on each parse make naive triple-set comparison impossible).

**Seed replaced with TTL import.** The seed module currently hard-codes class/property data as Python literals. In Stripe 2, it's replaced with `SKOSImportService.execute()` importing the evrepo-core TTL file. This exercises the import pipeline and keeps seed data in sync with the vocab files.

### Data model — OWL restriction preservation

**Structured pass-through for `allValuesFrom` restrictions.** Andrew confirmed restrictions should be preserved. All 11 restrictions in the current vocab files follow one pattern: `owl:allValuesFrom` on `evrepo:codedValue`, constraining which concept type a CodingAnnotation subclass accepts. A small `class_restriction` table captures them all: `(class_id, on_property_uri, restriction_type, value_uri)`. Import parses the blank-node pattern, creates records. Export replays them. No UI for creating/editing restrictions in the first pass.

This is tightly coupled with concept-typed classes and dual-typing: the restriction references a concept-typed class (e.g. `EducationLevelConcept`), which only resolves if that class is imported as an ontology class, and concepts are dual-typed as instances of it.

### Out of scope (settled)

**Named individuals (`owl:oneOf`, #112) — not needed.** The builder represents enumerated value sets as SKOS concepts in concept schemes. `owl:NamedIndividual` maps to concepts in the builder's model. Import reports as `info`.

---

## Pipeline Overview

```
TTL file
  │
  ▼
rdf_parser.py          ← parse, validate, extract metadata
  │
  ▼
skos_import_service.py ← create DB records (models)
  │
  ▼
SQLAlchemy models      ← ontology_class.py, property.py, concept.py, join tables
  │
  ▼
snapshot_service.py    ← build SnapshotVocabulary from DB
  │
  ▼
schemas/snapshot.py    ← SnapshotClass, SnapshotProperty, SnapshotConcept (validation)
  │
  ▼
reader_file_service.py ← render JSON for published files
  │
  ▼
published JSON         ← vocabulary.schema.json contract
  │
  ▼
skos_export_service.py ← snapshot → RDF graph → TTL/XML/JSON-LD
  │
  ▼
frontend / feedback-ui ← display and authoring
```

---

## Implementation Stripes

Each stripe is one or two PRs. Stop after each stripe, review, commit. Do not roll into the next stripe automatically.

### Stripe 1: Format scaffold

Update the format 1.0 schema in place with all new fields. Purge existing published artifacts from blob storage. No DB schema changes, no new tables. After this stripe, projects publish valid JSON with new fields at safe defaults.

**Snapshot schema** (`schemas/snapshot.py`):
- `SnapshotClass`: add `superclass_uris: list[str] = Field(default_factory=list)`
- `SnapshotClass.from_class`: set `superclass_uris=[]`
- `SnapshotConcept`: add `concept_type_uris: list[str] = Field(default_factory=list)`
- `SnapshotConcept.from_concept`: set `concept_type_uris=[]`
- `SnapshotProperty`: add `property_type: str = "object"` and `domain_class_uris: list[str]`
- `SnapshotProperty.from_property`: set `property_type="datatype" if property.range_datatype else "object"`, `domain_class_uris=[property.domain_class]`
- Rename `require_exactly_one_range` → `require_valid_range`: when `property_type == "rdf"`, allow 0 or 1 range; otherwise keep strict exactly-one rule

**Snapshot service** (`services/snapshot_service.py`):
- `_validate_references`: add superclass URI validation (each must be in `class_uris` or in the well-known allowlist). Change domain_class check to iterate `domain_class_uris` list.

**Reader file service** (`services/reader_file_service.py`):
- `FORMAT_VERSION` stays `"1.0"` (no version bump)
- Class rendering: add `"superclasses": cls.superclass_uris`
- Concept rendering: add `"type_uris": concept.concept_type_uris`
- Property rendering: replace `"domain_class_uri"` with `"domain_class_uris"`, add `"property_type"`

**Published format schema** (`docs/published-format/vocabulary.schema.json`):
- `format_version` const stays `"1.0"`
- Classes: add `superclasses` (required array of URI strings)
- Concepts: add `type_uris` (required array of URI strings, empty if none)
- Properties: replace `domain_class_uri` with `domain_class_uris` (required array), add `property_type` (required enum)
- Simplify `oneOf` range constraint: remove from JSON Schema (enforced by Pydantic)

**Feedback UI types** (`feedback-ui/src/api/published.ts`):
- `VocabClass`: add `superclasses: string[]`
- `VocabConcept`: add `type_uris: string[]`
- `VocabProperty`: replace `domain_class_uri` with `domain_class_uris: string[]`, add `property_type`

**Purge published artifacts:**
- Clear blob storage of all existing published files (dev/test data only, no customers)
- Republish seed projects after purge to verify new schema shape

**Import warnings** (`services/rdf_parser.py`):
- Upgrade `_check_unsupported_restrictions`: `info` → `warning`, now enumerates each restriction found (property name, restriction type, value) instead of just a count. Message says "dropped on import" until Stripe 5 adds preservation.
- `_check_unsupported_named_individuals`: stays `info`

**Acceptance criteria:** DONE (branch `feature/108-format-scaffold`)
- [x] Published JSON schema updated with new fields
- [x] `FORMAT_VERSION` remains `"1.0"`
- [x] `classes[].superclasses` is `[]` for existing projects
- [x] Concepts include `type_uris: []` in published JSON
- [x] `properties[].domain_class_uris` wraps existing scalar in a list
- [x] `properties[].property_type` inferred as `"object"` or `"datatype"`
- [x] `rdf` property type with no range passes snapshot validation
- [x] OWL restriction import warning is `warning` severity with enumerated details
- [x] Feedback-ui types and components updated for new field names
- [x] 808 backend tests pass, 40 feedback-ui tests pass, lint clean

---

### Stripe 2: #109 — `rdfs:subClassOf` + concept dual-typing (pipeline)

Class hierarchy data pipeline plus concept type preservation. Two PRs: pipeline first, then UI.

#### Pipeline PR

**Data model — class hierarchy:** New file `models/class_superclass.py` following `ConceptBroader` pattern. Add `superclasses` relationship on `OntologyClass`. Register in `models/__init__.py`. Migration.

**Data model — concept types:** Add `concept_type_uris` column to `concepts` table (PostgreSQL ARRAY of strings, default `{}`). No join table needed — these are URI strings, not FK references.

**RDF parser** (`services/rdf_parser.py`):

*Concept-typed classes:* Remove `if subject in concept_subclasses: continue` from `find_owl_classes` (line 365). Classes like `EffectSizeMetricConcept` import as regular ontology classes.

*New function:* `extract_class_superclasses(g, class_uris)` → `list[tuple[URIRef, URIRef]]`. Walk `rdfs:subClassOf` triples, keep edges where subject is in `class_uris` and object is in `class_uris` or the well-known allowlist. Skip blank nodes. Cycle detection via DFS.

*New function:* `extract_concept_type_uris(g, concept_uri)` → `list[str]`. Collect all `rdf:type` values for a concept that are URIRefs and not `skos:Concept` (or its subclasses). Return as sorted list of URI strings.

*Rename:* `_check_unsupported_subclasses` → `_check_subclasses` (now supported).

*Update:* `analyze_graph` → include `"class_superclasses"` in returned dict.

**Import service** (`services/skos_import_service.py`):
- In `_import_classes`: build `uri_to_id` map, create `ClassSuperclass` records for each edge, flush
- In `_import_concepts`: capture concept type URIs via `extract_concept_type_uris`, store in `concept.concept_type_uris`

**Snapshot schema** (`schemas/snapshot.py`):
- `SnapshotClass.from_class`: change to `superclass_uris=[s.uri for s in ontology_class.superclasses]`
- `SnapshotConcept.from_concept`: change to `concept_type_uris=list(concept.concept_type_uris) if concept.concept_type_uris else []`

**Export service** (`services/skos_export_service.py`):
- In `_add_class_to_graph`: emit `rdfs:subClassOf` triple for each superclass URI
- In concept export: emit `rdf:type` triples for each URI in `concept_type_uris`

**Seed data replacement:**
Replace `taxonomy_builder.seed` Python literals with TTL import via `SKOSImportService.execute()`. Exercises the import pipeline and keeps seed in sync with vocab files.

**Acceptance criteria (pipeline):**
- [ ] Importing TTL with `A rdfs:subClassOf B` stores edge in `class_superclass`
- [ ] Concept-typed classes (`X rdfs:subClassOf skos:Concept`) imported as ontology classes
- [ ] Cycle in subclass graph → validation error, import blocked
- [ ] Concepts with `rdf:type esea:EducationLevelConcept` preserve type URIs
- [ ] Concept type URIs appear in snapshot and published JSON
- [ ] Export emits `rdfs:subClassOf` triples and concept `rdf:type` triples
- [ ] Seed module imports TTL instead of using Python literals

#### UI PR (#109 companion issue)

**API endpoints** (follow concept broader pattern):
- `POST /api/classes/{id}/superclass` — add superclass (cycle detection)
- `DELETE /api/classes/{id}/superclass/{superclass_id}` — remove

**Schema** (`schemas/ontology_class.py`):
- `OntologyClassRead`: add `superclasses: list[OntologyClassBrief]`, `subclasses: list[OntologyClassBrief]`
- `OntologyClassBrief`: `{ id, uri, label }`

**Builder UI** (`ClassDetailPane.tsx`):
- "Superclasses" section: list + "Add superclass" dropdown (excludes self and descendants)
- "Subclasses" section: read-only list with links

**Feedback UI** (`ClassDetail.tsx`):
- "Subclass of" section with links
- Concept type URIs: read-only display (show OWL type labels if resolvable)

**Acceptance criteria (UI):**
- [ ] `POST /api/classes/{id}/superclass` adds relationship, rejects cycles
- [ ] `DELETE /api/classes/{id}/superclass/{sid}` removes relationship
- [ ] Builder ClassDetailPane shows superclass/subclass sections with add/remove
- [ ] Feedback ClassDetail shows "Subclass of" section
- [ ] Concept type URIs visible in reader (read-only)

---

### Stripe 3: #110 — `owl:unionOf` domains (pipeline + UI)

Two PRs: pipeline first, then UI.

#### Pipeline PR

**Data model:** New file `models/property_domain_class.py`. Add `domain_classes` relationship on `Property`. Keep scalar `domain_class` column. Migration: add table + data migration from existing scalars.

**RDF parser:** Replace `_resolve_union_first` with `_resolve_union_all`. Update `extract_property_metadata` to return `"domain_uris"` list. Remove `_check_unsupported_union_domains`.

**Import service:** Read `domain_uris` list, create `PropertyDomainClass` records, sort alphabetically, set scalar to first.

**Snapshot:** `domain_class_uris=sorted(c.uri for c in property.domain_classes)`.

**Export:** Single domain → plain triple. Multiple → blank-node `owl:unionOf` RDF Collection, sorted.

**Acceptance criteria (pipeline):**
- [ ] Union domains stored as multiple `PropertyDomainClass` records
- [ ] Malformed RDF Collection → warning, partial import
- [ ] Domain URIs sorted alphabetically
- [ ] Single-domain export: plain triple. Multi-domain: `owl:unionOf`, graph isomorphic

#### UI PR (#110 companion issue)

**Schema:** `PropertyCreate`/`PropertyUpdate` accept `domain_class_uris: list[str]`. `PropertyRead` adds `domain_class_uris`.

**Builder UI:** Multi-select domain class picker (pills/tags). At least one required.

**Builder filter:** `p.domain_class_uris.includes(classUri)` — exact match, no closure.

**Feedback UI:** PropertyDetail shows multiple domain classes. ClassDetail filters by multi-domain membership.

**Acceptance criteria (UI):**
- [ ] Multi-select domain class picker in builder
- [ ] ClassDetailPane filters by `includes()` (no closure)
- [ ] Feedback UIs updated for multi-domain

---

### Stripe 4: #111 — Property type distinctions (pipeline + UI)

Two PRs or one — implementer's call.

#### Pipeline

**Data model:** Add `property_type` column. NOT NULL, `server_default="object"`. Backfill `"datatype"` where `range_datatype` is set.

**Import:** Persist `property_type` from parser. `rdf` with no range: all range columns `None`.

**Snapshot:** `property_type=property.property_type`.

**Export:** Emit correct `rdf:type` per property type. Fix missing `range_class` → `rdfs:range` emission.

**Acceptance criteria (pipeline):**
- [ ] `property_type` persisted for all three types
- [ ] `rdf:Property` with no range passes validation
- [ ] Export emits correct RDF type and `rdfs:range` for `range_class`

#### UI (#111 companion issue)

**Builder UI:** Property type radio group. Enforce type → range mapping: selecting type filters available range options. `rdf` allows "No range constraint."

**Feedback UI:** Show property type label in meta row.

**Acceptance criteria (UI):**
- [ ] Type selector filters range options
- [ ] `rdf` allows no range
- [ ] Feedback shows type label

---

### Stripe 5: Constraint system (restrictions + concept-typed classes + dual-typing)

The OWL constraint system round-trips as a package: restrictions reference concept-typed classes, which are meaningful because concepts are dual-typed as instances of them. All three pieces ship together.

#### Data model

**`class_restriction` table:** `class_id` (FK → `ontology_classes.id`, CASCADE), `on_property_uri` (String), `restriction_type` (String, e.g. `"allValuesFrom"`), `value_uri` (String). Composite PK or separate PK with unique constraint.

**`concept_type_uris` column on `concepts`:** PostgreSQL ARRAY of strings, default `{}`. Stores non-`skos:Concept` `rdf:type` URIs.

**Concept-typed classes:** Remove `if subject in concept_subclasses: continue` filter from `find_owl_classes`. Classes like `EducationLevelConcept` import as regular ontology classes with `rdfs:subClassOf skos:Concept` stored as a superclass edge (uses Stripe 2 infrastructure). Pending Andrew's confirmation on class list presentation — can filter by `skos:Concept` superclass if noisy.

#### RDF parser

- New function: `extract_restrictions(g, class_uris)` — parse `rdfs:subClassOf` blank nodes with `owl:Restriction`, extract `owl:onProperty` and `owl:allValuesFrom`. Return structured list.
- New function: `extract_concept_type_uris(g, concept_uri)` — collect non-`skos:Concept` `rdf:type` URIs.
- Update `_check_unsupported_restrictions` to enumerate which restrictions were found (property URI + value URI), not just count.

#### Import

- Create `ClassRestriction` records from parsed restrictions.
- Store `concept_type_uris` on concepts during `_import_concepts`.
- Concept-typed classes imported via existing `_import_classes` (no longer excluded).

#### Snapshot + published JSON

- `SnapshotClass`: add `restrictions: list[dict]` (each with `on_property_uri`, `restriction_type`, `value_uri`)
- `SnapshotConcept.from_concept`: populate `concept_type_uris` from DB column
- Reader: emit `restrictions` on classes, `type_uris` on concepts
- Published schema: add both fields

#### Export

- Emit `rdfs:subClassOf [ a owl:Restriction ; owl:onProperty ... ; owl:allValuesFrom ... ]` for each restriction.
- Emit extra `rdf:type` triples for each concept's `concept_type_uris`.
- Concept-typed classes export their `rdfs:subClassOf skos:Concept` via standard Stripe 2 export code.

#### Acceptance criteria

- [ ] All 11 `allValuesFrom` restrictions round-trip through import/export
- [ ] Concept-typed classes imported as ontology classes with `skos:Concept` superclass
- [ ] Concepts preserve OWL type URIs (`concept_type_uris`)
- [ ] Restriction export produces correct blank-node structure
- [ ] Concept `rdf:type` triples emitted for dual-typed concepts
- [ ] Import warning enumerates specific restrictions found

---

## Finishing Touches (on #108)

After all stripes merge. Tasks on the epic, not separate issues.

### Golden roundtrip tests

Create `backend/tests/fixtures/rdf/` with:
1. `evrepo-like-full.ttl` — all features: subClassOf, unionOf, property types, range_class, concept dual-typing, restrictions, concept-typed classes
2. `class-cycle.ttl` — circular subClassOf → must fail validation
3. `malformed-union.ttl` — unionOf with non-URI members or unterminated list
4. `rdf-property-no-range.ttl` — rdf:Property with no rdfs:range

Golden test: import → snapshot → validate → render JSON → export → `isomorphic()`.

### Publish representability gate

`check_representability(snapshot)` — safety net against future constructs added without export support.

---

## Follow-up Issues

| Issue | Description |
|---|---|
| **Applicability closure** | `classAncestors` signal, `isApplicable` helper, inherited property display in both UIs. Depends on #109 + #110. |
| **Remove scalar `domain_class` column** | Drop transitional column. Separate migration. |
| **Class tree rendering** | Render class list as tree in ProjectPane. Design decision on visual treatment. |
| **Concept type editing UI** | UI for editing `concept_type_uris` (read-only in first pass). |
| **Restriction editing UI** | UI for viewing/editing `allValuesFrom` restrictions on classes (read-only in first pass). |

---

## Cross-cutting File Tracker

| File | S1 (fmt) | #109 pipe | #109 UI | #110 pipe | #110 UI | #111 pipe | #111 UI | S5 (constraints) |
|---|---|---|---|---|---|---|---|---|
| **Models** | | | | | | | | |
| `models/class_superclass.py` | | new | | | | | | |
| `models/class_restriction.py` | | | | | | | | new |
| `models/property_domain_class.py` | | | | new | | | | |
| `models/ontology_class.py` | | modify | | | | | | |
| `models/concept.py` | | | | | | | | modify |
| `models/property.py` | | | | modify | | modify | | |
| `models/__init__.py` | | modify | | modify | | | | modify |
| **Services** | | | | | | | | |
| `services/rdf_parser.py` | modify | modify | | modify | | | | modify |
| `services/skos_import_service.py` | | modify | | modify | | modify | | modify |
| `services/ontology_class_service.py` | | | modify | | | | | |
| `services/property_service.py` | | | | | modify | | modify | |
| `services/snapshot_service.py` | modify | | | | | | | |
| `services/reader_file_service.py` | modify | | | | | | | modify |
| `services/skos_export_service.py` | | modify | | modify | | modify | | modify |
| **Schemas** | | | | | | | | |
| `schemas/snapshot.py` | modify | modify | | modify | | modify | | modify |
| `schemas/ontology_class.py` | | | modify | | | | | |
| `schemas/property.py` | | | | | modify | | modify | |
| `schemas/skos_import.py` | | | | modify | | | | |
| **API** | | | | | | | | |
| `api/ontology_classes.py` | | | modify | | | | | |
| **Docs** | | | | | | | | |
| `vocabulary.schema.json` | modify | | | | | | | modify |
| **Frontend** | | | | | | | | |
| `types/models.ts` | | | modify | | modify | | modify | |
| `ClassDetailPane.tsx` | | | modify | | modify | | | |
| `PropertyDetail.tsx` (builder) | | | | | modify | | modify | |
| **Feedback UI** | | | | | | | | |
| `api/published.ts` | modify | | | | | | | |
| `ClassDetail.tsx` (feedback) | | | modify | | modify | | | |
| `PropertyDetail.tsx` (feedback) | | | | | modify | | modify | |
| **Seed** | | | | | | | | |
| `taxonomy_builder/seed.py` | | modify | | | | | | |
| **Migrations** | | | | | | | | |
| `alembic/versions/` | | new | | new | | new | | new |

---

## GitHub Issues

### Existing issues (backend pipeline)

#109, #110, #111 already exist with good requirement bodies. This plan adds implementation detail but doesn't replace them.

### New issues needed

| Issue | Scope | Depends on |
|---|---|---|
| **Format scaffold** | Stripe 1. Could be a task on #108 instead. | nothing |
| **Class hierarchy management UI** | #109 UI: API endpoints, schema, ClassDetailPane, feedback ClassDetail | #109 pipeline |
| **Multi-domain property editing UI** | #110 UI: schema, multi-select picker, ClassDetailPane filter, feedback display | #110 pipeline |
| **Property type editing UI** | #111 UI: schema, type selector with range enforcement, feedback display | #111 pipeline |
| **Constraint system preservation** | Stripe 5: restriction table, concept dual-typing, concept-typed class import. All `allValuesFrom` restrictions round-trip. | #109 pipeline (needs superclass infrastructure) |
| **Applicability closure** | classAncestors, isApplicable, inherited property display in both UIs | #109 UI + #110 UI |
