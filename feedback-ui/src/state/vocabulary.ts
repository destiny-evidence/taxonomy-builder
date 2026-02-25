import { computed, signal } from "@preact/signals";
import {
  getRootIndex,
  getProjectIndex,
  getVocabulary,
  type ProjectIndex,
  type RootIndexProject,
  type Vocabulary,
  type VocabConcept,
  type VocabScheme,
} from "../api/published";
import { route, navigate, navigateToProject, type EntityKind } from "../router";
import { isAuthenticated } from "./auth";
import { loadOwnFeedback } from "./feedback";

// --- Signals ---

export const loading = signal(false);
export const error = signal<string | null>(null);

export const projects = signal<RootIndexProject[]>([]);
export const currentProjectId = signal<string | null>(null);
export const vocabulary = signal<Vocabulary | null>(null);
export const selectedVersion = signal<string | null>(null);
export const projectIndex = signal<ProjectIndex | null>(null);
export const projectIndexLoading = signal(false);

// --- Derived ---

export const projectName = computed(
  () => vocabulary.value?.project.name ?? ""
);

/** Concept tree node for rendering the sidebar. */
export interface ConceptTreeNode {
  id: string;
  label: string;
  children: ConceptTreeNode[];
}

/**
 * Build a tree of concepts from a flat scheme.
 * Top concepts have no `broader` entries; children are grouped under their parents.
 */
function buildConceptTree(scheme: VocabScheme): ConceptTreeNode[] {
  const concepts = scheme.concepts;
  const childrenOf = new Map<string, string[]>();

  // Index children by broader parent
  for (const [id, concept] of Object.entries(concepts)) {
    for (const broaderId of concept.broader) {
      const existing = childrenOf.get(broaderId);
      if (existing) {
        existing.push(id);
      } else {
        childrenOf.set(broaderId, [id]);
      }
    }
  }

  function buildNode(id: string, concept: VocabConcept): ConceptTreeNode {
    const kids = childrenOf.get(id) ?? [];
    return {
      id,
      label: concept.pref_label,
      children: kids
        .map((childId) => {
          const child = concepts[childId];
          return child ? buildNode(childId, child) : null;
        })
        .filter((n): n is ConceptTreeNode => n !== null)
        .sort((a, b) => a.label.localeCompare(b.label)),
    };
  }

  // Top concepts: either explicitly listed, or those with no broader
  const topIds =
    scheme.top_concepts.length > 0
      ? scheme.top_concepts
      : Object.entries(concepts)
          .filter(([, c]) => c.broader.length === 0)
          .map(([id]) => id);

  return topIds
    .map((id) => {
      const concept = concepts[id];
      return concept ? buildNode(id, concept) : null;
    })
    .filter((n): n is ConceptTreeNode => n !== null)
    .sort((a, b) => a.label.localeCompare(b.label));
}

/** Concept trees indexed by scheme id. */
export const conceptTrees = computed<Map<string, ConceptTreeNode[]>>(() => {
  const vocab = vocabulary.value;
  if (!vocab) return new Map();
  const map = new Map<string, ConceptTreeNode[]>();
  for (const scheme of vocab.schemes) {
    map.set(scheme.id, buildConceptTree(scheme));
  }
  return map;
});

// --- Actions ---

export async function loadProjects(): Promise<void> {
  try {
    loading.value = true;
    error.value = null;
    const index = await getRootIndex();
    projects.value = index.projects;
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Failed to load projects";
  } finally {
    loading.value = false;
  }
}

export async function selectProject(projectId: string, version: string): Promise<void> {
  try {
    loading.value = true;
    error.value = null;
    currentProjectId.value = projectId;
    loadProjectIndex(projectId);
    await loadVersion(projectId, version);
    if (isAuthenticated.value) {
      loadOwnFeedback();
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Failed to load project";
  } finally {
    loading.value = false;
  }
}

export async function loadVersion(
  projectId: string,
  version: string
): Promise<void> {
  try {
    loading.value = true;
    error.value = null;
    selectedVersion.value = version;
    vocabulary.value = await getVocabulary(projectId, version);
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Failed to load vocabulary";
  } finally {
    loading.value = false;
  }
}

export async function resolveLatestVersion(projectId: string): Promise<string | null> {
  try {
    const index = await getProjectIndex(projectId);
    return index.versions.length > 0 ? index.versions[0].version : null;
  } catch {
    return null;
  }
}

async function loadProjectIndex(projectId: string): Promise<void> {
  if (projectIndex.value?.project.id === projectId) return;
  projectIndex.value = null;
  projectIndexLoading.value = true;
  try {
    projectIndex.value = await getProjectIndex(projectId);
  } catch {
    // Non-critical — version selector just won't have the full list
  } finally {
    projectIndexLoading.value = false;
  }
}

function entityExistsInVocabulary(
  vocab: Vocabulary,
  entityKind: EntityKind,
  entityId: string
): boolean {
  switch (entityKind) {
    case "scheme":
      return vocab.schemes.some((s) => s.id === entityId);
    case "concept":
      return vocab.schemes.some((s) => entityId in s.concepts);
    case "class":
      return vocab.classes.some((c) => c.id === entityId);
    case "property":
      return vocab.properties.some((p) => p.id === entityId);
  }
}

export async function switchVersion(version: string): Promise<void> {
  const projectId = currentProjectId.value;
  if (!projectId || version === selectedVersion.value) return;

  const { entityKind, entityId } = route.value;

  await loadVersion(projectId, version);

  const vocab = vocabulary.value;
  if (entityKind && entityId && vocab && entityExistsInVocabulary(vocab, entityKind, entityId)) {
    navigate(projectId, version, entityKind, entityId);
  } else {
    navigateToProject(projectId, version);
  }
}
