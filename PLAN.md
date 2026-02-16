# Issue #58 — Phase 1: Remove Existing Versioning

## Issue Summary

Issue #58 calls for revamping versioning to be project-level (not scheme-level) with semantic versioning. Before building the new system, we need to cleanly remove the two existing versioning mechanisms:

1. **`ConceptScheme.version`** — a free-text metadata field on the scheme
2. **`PublishedVersion` model** — a full snapshot/publishing system tied to schemes

## Implications for the History System

The history tab (HistoryPanel) displays a chronological feed of ChangeEvents for a scheme. Removing versioning touches this system in three places:

### 1. Existing "published_version" change events become orphaned

When a version was published, the VersionService recorded a ChangeEvent with:
- `entity_type: "published_version"`, `action: "publish"`
- `after_state: { version_label, notes }`

After removal, any existing change events with `entity_type="published_version"` will still sit in the `change_events` table. The HistoryPanel will still render them — they'll show as **"Published Version — v1.0"** in the timeline. This is harmless: the event data is self-contained in `after_state`, so it doesn't need to look up the now-deleted `published_versions` table. These are audit records and should be preserved.

**No action needed** — old publish events remain visible and correctly rendered. They just won't have new ones added.

### 2. `serialize_scheme()` in ChangeTracker captures `version`

The ChangeTracker's `serialize_scheme()` method includes `scheme.version` in its output. This means every scheme create/update change event currently stores the version field in its before/after state. After we remove `ConceptScheme.version`, we must also remove `"version"` from `serialize_scheme()`. Historical events will still contain the old `version` key in their JSONB — that's fine, it's immutable audit data.

### 3. Frontend history strings reference `published_version`

[historyStrings.ts](frontend/src/components/history/historyStrings.ts) has `published_version: "Version"` in `ENTITY_TYPE_LABELS`, and [HistoryPanel.tsx](frontend/src/components/history/HistoryPanel.tsx) lines 58-62 have a special case rendering `version_label` from the after_state. We should **keep both** so that old publish events continue to render nicely. No code removal needed here.

### Summary: History is safe

The history system uses string-typed `entity_type` and stores full state snapshots in JSONB. Old events are self-describing and don't need the PublishedVersion model to render. The only code change needed is removing `"version"` from `serialize_scheme()`.

## Implications for the Database

- **Drops the `published_versions` table entirely.** Any published snapshots will be lost. Back up first if needed.
- **Drops the `version` column from `concept_schemes`.** Any version metadata there will be lost.
- **Migration is irreversible in practice** — down-migration can recreate structure but not data.
- **Alembic history stays linear** — new migration at head, old migration files stay untouched.

## Affected Files

### Backend — Delete entirely
- `backend/src/taxonomy_builder/models/published_version.py`
- `backend/src/taxonomy_builder/schemas/version.py`
- `backend/src/taxonomy_builder/services/version_service.py`
- `backend/src/taxonomy_builder/api/versions.py`
- `backend/tests/test_models/test_published_version.py`
- `backend/tests/test_services/test_version_service.py`
- `backend/tests/test_api/test_versions.py`

### Backend — Edit
- `backend/src/taxonomy_builder/models/__init__.py` — remove PublishedVersion import
- `backend/src/taxonomy_builder/models/concept_scheme.py` — remove `version` field
- `backend/src/taxonomy_builder/schemas/concept_scheme.py` — remove `version` from Create/Update/Read
- `backend/src/taxonomy_builder/api/dependencies.py` — remove `get_version_service`
- `backend/src/taxonomy_builder/main.py` — remove versions router
- `backend/src/taxonomy_builder/services/change_tracker.py` — remove `version` from `serialize_scheme()`
- `backend/tests/test_api/test_schemes.py` — remove version from test data
- `backend/tests/test_models/test_concept_scheme.py` — remove version from test data

### Frontend — Delete entirely
- `frontend/src/api/versions.ts`
- `frontend/src/components/versions/VersionsPanel.tsx`
- `frontend/src/components/versions/PublishDialog.tsx`
- `frontend/src/components/versions/VersionExportModal.tsx`
- `frontend/tests/components/versions/VersionsPanel.test.tsx`
- `frontend/tests/components/versions/PublishDialog.test.tsx`

### Frontend — Edit
- `frontend/src/types/models.ts` — remove PublishedVersion types + version from ConceptScheme
- `frontend/src/components/schemes/SchemeDetail.tsx` — remove version field
- `frontend/src/components/schemes/SchemeList.tsx` — remove version display
- `frontend/src/components/workspace/TreePane.tsx` — remove version display

### Frontend — Keep as-is (for historical event rendering)
- `frontend/src/components/history/HistoryPanel.tsx` — published_version rendering stays
- `frontend/src/components/history/historyStrings.ts` — published_version label stays

### New
- Alembic migration to drop `published_versions` table and `version` column from `concept_schemes`

## Implementation Plan

### Stripe 1: Remove PublishedVersion backend (model, service, API, schemas)

- **Red**: Verify existing version tests pass, then confirm they reference code we're about to remove
- **Green**:
  - Delete `published_version.py` model, `version.py` schema, `version_service.py`, `api/versions.py`
  - Remove imports from `models/__init__.py`, `main.py`, `dependencies.py`
  - Delete all version test files (`test_published_version.py`, `test_version_service.py`, `test_api/test_versions.py`)
- **Refactor**: Ensure no remaining imports or references
- **Commit**: "Remove PublishedVersion model, service, API, and tests"

### Stripe 2: Remove `version` field from ConceptScheme

- **Red**: Update scheme tests to remove version from test data and assertions
- **Green**:
  - Remove `version` from ConceptScheme model
  - Remove `version` from ConceptScheme Pydantic schemas (Create, Update, Read)
  - Remove `version` from `ChangeTracker.serialize_scheme()`
  - Update test fixtures and assertions in `test_schemes.py` and `test_concept_scheme.py`
- **Refactor**: Confirm all backend tests pass
- **Commit**: "Remove version field from ConceptScheme model and schemas"

### Stripe 3: Add Alembic migration

- **Green**: Generate migration to drop `published_versions` table and `version` column from `concept_schemes`
- **Verify**: Run `alembic upgrade head` against test database
- **Commit**: "Add migration to drop versioning tables and columns"

### Stripe 4: Remove frontend versioning code

- **Green**:
  - Delete `api/versions.ts`, `components/versions/` directory, version test files
  - Remove `PublishedVersion` types from `models.ts`, remove `version` from ConceptScheme interface
  - Remove version references from `SchemeDetail.tsx`, `SchemeList.tsx`, `TreePane.tsx`
  - Keep `published_version` handling in HistoryPanel and historyStrings (for old events)
- **Verify**: `npm run typecheck && npm test && npm run build`
- **Commit**: "Remove frontend versioning UI, API client, and types"
