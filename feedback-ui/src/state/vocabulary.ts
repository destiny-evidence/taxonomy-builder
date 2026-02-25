import { computed, signal } from "@preact/signals";
import {
  getRootIndex,
  getProjectIndex,
  getVocabulary,
  type RootIndexProject,
  type ProjectIndex,
  type Vocabulary,
  type VocabConcept,
  type VocabScheme,
  type VersionEntry,
} from "../api/published";
import { isAuthenticated } from "./auth";
import { loadOwnFeedback } from "./feedback";

// --- Signals ---

export const loading = signal(false);
export const error = signal<string | null>(null);

export const projects = signal<RootIndexProject[]>([]);
export const currentProjectId = signal<string | null>(null);
export const projectIndex = signal<ProjectIndex | null>(null);
export const vocabulary = signal<Vocabulary | null>(null);
export const selectedVersion = signal<string | null>(null);

// --- Derived ---

export const versions = computed<VersionEntry[]>(
  () => projectIndex.value?.versions ?? []
);

export const projectName = computed(
  () => vocabulary.value?.project.name ?? projectIndex.value?.project.name ?? ""
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
    // Auto-select first project (multi-project picker deferred)
    if (index.projects.length > 0) {
      await selectProject(index.projects[0].id);
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Failed to load projects";
  } finally {
    loading.value = false;
  }
}

export async function selectProject(projectId: string): Promise<void> {
  try {
    loading.value = true;
    error.value = null;
    currentProjectId.value = projectId;
    const idx = await getProjectIndex(projectId);
    projectIndex.value = idx;
    // Load latest version
    const version = idx.latest_version ?? idx.versions[0]?.version;
    if (version) {
      await loadVersion(projectId, version);
    }
    // Load own feedback now that project is known
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
