# Mapping examples

How real-world source data maps into the evidence graph, and why the builder needs to represent the OWL features described in the [exposition](README.md).

The [Jacobs Foundation team briefing](https://github.com/destiny-evidence/taxonomy-builder) identifies three source datasets for the education evidence repository: **EEF** (Education Endowment Foundation), **3ie** (International Initiative for Impact Evaluation), and **WWHGE** (What Works in Gender and Education). Each has a different structure, different field names, and different levels of detail. The vocabulary is the shared language they get mapped into.

Two worked examples are included: an EEF cluster RCT with full quantitative data, and a 3ie study with metadata only. Together they show the range of what the evidence graph accommodates.

## The EEF example: full quantitative data

The [`vocab/esea/example-finding.jsonld`](../../vocab/esea/example-finding.jsonld) file models a cluster randomised controlled trial of a literacy intervention in Kenyan primary schools. This is a synthetic example based on typical EEF data, and it exercises the full depth of the evidence graph — including the quantitative layers that study-level databases like 3ie do not capture.

**The complete Investigation.** The top-level object is an Investigation with `documentType` (Journal Article, `esea:C00008`), `funderResearch` (EEF), `isRetracted` (false), and `dataSource` (EEF). These are investigation-level fields — they describe the study as a whole, not any individual finding.

**A single Finding with the full evidence graph.** The Investigation contains one Finding that demonstrates every major relationship:

- `evaluates` → an **Intervention** (a structured phonics programme) carrying two education themes (`esea:C00074` Literacy and Reading Interventions, `esea:C00055` Workforce Professional Development), an implementer type (`esea:C00133` NGO), implementation description (training + materials), fidelity data, duration (40 weeks), and a named programme
- `comparedTo` → a **ControlCondition** (business-as-usual)
- `hasContext` → a **Context** with education level (`esea:C00002` Primary), setting (`esea:C00146` Public School), country (KE), sub-national region (Bungoma County), and participants
- `hasOutcome` → an **Outcome** with outcome type (`esea:C00123` Basic Skills and Literacy) via the OutcomeCodingAnnotation pattern

**Per-arm ObservedResults.** The Finding has two ObservedResults, one per arm:

| | Intervention | Control |
|---|---|---|
| n | 580 | 518 |
| mean (post-test) | 24.3 | 18.7 |
| sd | 12.1 | 11.8 |
| preMean (baseline) | 8.2 | 8.0 |
| preSd | 5.4 | 5.2 |
| clusterCount | 25 schools | 25 schools |

Each ObservedResult links back to its Condition via `forCondition` and carries class-level provenance (`codedBy: "EEF"`, `sourceLocation: "Table 3, p. 18"`) — not CodingAnnotation wrapping.

**EffectEstimate with full statistics.** The Finding has one EffectEstimate: Hedges' g = 0.35 (SE = 0.12, 95% CI [0.11, 0.59]), baseline-adjusted, clustering-adjusted. The `effectSizeMetric` points to `evrepo:hedgesG` (effect size metrics are now in the core ontology, not ESEA-specific). The `estimateSource` is `evrepo:computedFromStats`. This is the kind of data that drives meta-analysis — the atomic unit the evidence repository is designed to serve.

**CodingAnnotation throughout.** Every coded field — education theme, implementer type, education level, country, outcome — is wrapped in a typed CodingAnnotation with `codedBy: "EEF"`, `supportingText` (the evidence from the source document), and `status: "coded"`. Multi-select fields like education theme use arrays of CodingAnnotations, each with its own provenance.

**Study Design not yet in vocabulary.** The ESEA vocabulary does not yet include a Study Design scheme (the wiki page does not exist). When added, it would appear as an Investigation-level CodingAnnotation alongside `documentType`.

## The 3ie Development Evidence Portal

The [3ie Development Evidence Portal](https://developmentevidence.3ieimpact.org/) (DEP) is a public database of impact evaluations and systematic reviews across development sectors. The education subset (`3ie DEP education IE data (Dec2025).xlsx`) contains **1,345 impact evaluations** across **10,544 rows** (multiple rows per study for multiple authors and outcomes). It is a flat tabular export with 52 columns covering bibliographic metadata, study design, geography, interventions, and outcomes. There is no nested structure — each row is a denormalised record.

The [`3ie-mapping-example.jsonld`](worked-examples/3ie-mapping-example.jsonld) example maps study 34810 (Kane & Ndoye, 2020 — an evaluation of a TVET internship programme in Senegal) from this flat format into the nested evidence graph. The source rows for this study are included as [`3ie-study-34810-source.csv`](worked-examples/3ie-study-34810-source.csv) so that the mapping can be traced column-by-column. This transformation illustrates several things:

**Flat fields map to nested structures.** The 3ie row has `country=Senegal`, `evaluation_method=Instrumental variable estimation`, `intervention=Technical and Vocational Education and Training (TVET)`, and `outcome=Index of employment` as peer columns. In the evidence graph, these land at different levels: country is on Context (nested inside Finding), evaluation method is on Investigation (the parent), intervention is on the Intervention condition (linked via `evaluates`), and outcome is on Outcome (linked via `hasOutcome`). A single flat row unfolds into a four-level hierarchy.

**Multiple outcomes create multiple Findings.** Study 34810 has two outcomes: "Index of employment" and "Employment type (regular employment)". In 3ie's tabular format these are two rows sharing all other fields. In the evidence graph, they become two separate Findings under the same Investigation, each with its own Outcome but sharing the same Intervention and Context. The Finding is the atomic unit — one comparison × one outcome.

**CodingAnnotation wraps every mapped value.** When the 3ie dataset says `implementation_agencies=Government agency`, the mapping does not just set `implementerType` to `esea:C00137`. It wraps the value in a CodingAnnotation that records:
- `codedValue`: the concept (`esea:C00137` — "National or State Government")
- `codedBy`: `"3ie"` (the source organisation, since we have no individual coder)
- `supportingText`: `"Government Of Senegal"` (the original value from the `implementation_agencies_name` column)
- `status`: `"coded"`

This provenance survives the transformation. A downstream consumer can see that the value came from 3ie's data, not from a human coder reviewing the original paper.

**Missing data uses the status enumeration.** The 3ie record has `research_funding_agency=Not specified`. This maps to a CodingAnnotation with `codedValue: null` and `status: "notReported"` — the source explicitly indicates the information is absent, which is different from the field simply being empty (which would mean "not yet coded" and the CodingAnnotation would be omitted entirely).

**Concept mapping requires judgement.** Not every 3ie field maps cleanly to an ESEA concept. The 3ie `sub_sector` value "Workforce development and vocational education" maps to education level `esea:C00005` (TVET), but this is an inference — 3ie codes sector, not ISCED level. The `unit_of_observation=Household` does not map to any participant type concept, so it becomes a free-text StringCodingAnnotation on `participants`. These mapping decisions are exactly the kind of case-by-case assessment the Jacobs briefing describes.

**Study-level vs finding-level data.** The 3ie DEP dataset contains no per-arm statistics (n, mean, sd) and no effect sizes (SMD, SE, confidence intervals). It is study-level metadata. Compare this with the EEF worked example ([`vocab/esea/example-finding.jsonld`](../../vocab/esea/example-finding.jsonld)) which has full quantitative data — ObservedResults with per-arm stats and EffectEstimates with Hedges' g. The evidence graph accommodates both: a Finding from 3ie has `evaluates`, `hasContext`, `hasOutcome` but no `hasArmData` or `hasEffectEstimate`. A Finding from EEF has all of these. The schema is additive — richer sources fill in more of the graph.

## Why this matters for the builder

The mapping pipeline is: source data → vocabulary-aligned JSON-LD → stored as LinkedDataEnhancement in the repository. The taxonomy builder's role is managing the vocabulary that the mapping targets. Every gap described in the [exposition](README.md) — subclasses, union domains, property types, enumerations — affects whether the builder can fully represent the vocabulary that these mappings need.

If the builder cannot represent the Condition hierarchy ([#109](https://github.com/destiny-evidence/taxonomy-builder/issues/109)), it cannot author the classes that `evaluates` and `comparedTo` point to. If it cannot represent union domains ([#110](https://github.com/destiny-evidence/taxonomy-builder/issues/110)), it cannot express that `supportingText` applies to both CodingAnnotation and ObservedResult. The 3ie example makes these gaps concrete: each `_comment` field in the JSON-LD notes which 3ie source field was mapped and how, showing the full chain from flat tabular data through vocabulary concepts to the nested evidence graph.
