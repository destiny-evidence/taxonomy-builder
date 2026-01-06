import { signal, computed } from "@preact/signals";
import type { Project } from "../types/models";

export const projects = signal<Project[]>([]);
export const projectsLoading = signal(false);
export const projectsError = signal<string | null>(null);
export const currentProject = signal<Project | null>(null);

export const projectsById = computed(() => {
  const map = new Map<string, Project>();
  for (const project of projects.value) {
    map.set(project.id, project);
  }
  return map;
});
