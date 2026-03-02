# Vocabulary artefacts

Domain vocabulary definitions for the evidence repository. These files are the canonical source for the ontology and concept schemes that the taxonomy builder manages.

## Two-layer architecture

The vocabulary is split across two namespaces, layered so that sector-specific extensions build on a shared core:

**[`evrepo-core/`](evrepo-core/)** — Sector-agnostic evidence synthesis foundation. Defines the evidence graph structure (Investigation → Finding → Intervention/Outcome/Context), the CodingAnnotation provenance pattern, ObservedResult, EffectEstimate, the Condition hierarchy (Intervention/ControlCondition/TemporalCondition), and the CodingStatus enumeration. Shared across education, health, and climate sectors.

- Namespace: `https://vocab.evidence-repository.org/`
- `evrepo-core.ttl` — OWL/Turtle ontology

**[`esea/`](esea/)** — Education Sector Evidence Architecture. Extends the core with education-specific concept schemes covering all 24 taxonomy fields (169 concepts), CodingAnnotation subclasses with OWL restrictions, and domain properties.

- Namespace: `https://vocab.esea.education/`
- `esea-vocab.ttl` — SKOS concept schemes, OWL classes, and properties
- `esea-context.jsonld` — JSON-LD @context for serialising evidence data
- `example-finding.jsonld` — Worked example: a cluster RCT with per-arm data

A health or climate domain would add a sibling directory (e.g. `health/`) that imports `evrepo-core/` and defines its own concept schemes.

## Usage

These files can be imported into the taxonomy builder via the Turtle import UI, or used as project templates ([#99](https://github.com/destiny-evidence/taxonomy-builder/issues/99)). The JSON-LD context and example are for consumers of the published vocabulary.

For a detailed explanation of the OWL patterns used and their relationship to the builder's data model, see [docs/ontology-expressivity/](../docs/ontology-expressivity/).
