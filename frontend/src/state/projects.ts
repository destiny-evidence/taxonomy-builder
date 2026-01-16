import { signal } from "@preact/signals";
import type { Project } from "../types/models";

export const projects = signal<Project[]>([]);
export const projectsLoading = signal(false);
export const projectsError = signal<string | null>(null);
export const currentProject = signal<Project | null>(null);
