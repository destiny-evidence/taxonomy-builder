"""Service for generating and writing published reader files to blob storage."""

from __future__ import annotations

import json
import logging

from taxonomy_builder.blob_store import BlobStore, CdnPurger
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.published_version import PublishedVersion
from taxonomy_builder.services.publishing_service import PublishingService

logger = logging.getLogger(__name__)

FORMAT_VERSION = "1.0"


class ReaderFileService:
    """Generates reader JSON files and writes them to blob storage."""

    def __init__(
        self,
        publishing_service: PublishingService,
        blob_store: BlobStore,
        cdn_purger: CdnPurger,
    ) -> None:
        self._publishing_service = publishing_service
        self._blob_store = blob_store
        self._cdn_purger = cdn_purger

    # ------------------------------------------------------------------
    # Pure rendering (static, no DB)
    # ------------------------------------------------------------------

    @staticmethod
    def render_vocabulary(version: PublishedVersion) -> bytes:
        """Render a vocabulary.json from a PublishedVersion."""
        snapshot = version.snapshot_vocabulary
        schemes = []
        for scheme in snapshot.concept_schemes:
            concepts_dict = {}
            top_concepts: list[str] = []
            for concept in scheme.concepts:
                cid = str(concept.id)
                broader = [str(b) for b in concept.broader_ids]
                if not broader:
                    top_concepts.append(cid)
                concepts_dict[cid] = {
                    "pref_label": concept.pref_label,
                    "identifier": concept.identifier,
                    "uri": concept.uri,
                    "definition": concept.definition,
                    "scope_note": concept.scope_note,
                    "alt_labels": concept.alt_labels,
                    "broader": broader,
                    "related": [str(r) for r in concept.related_ids],
                }
            schemes.append(
                {
                    "id": str(scheme.id),
                    "title": scheme.title,
                    "description": scheme.description,
                    "uri": scheme.uri,
                    "top_concepts": top_concepts,
                    "concepts": concepts_dict,
                }
            )

        properties = []
        for prop in snapshot.properties:
            properties.append(
                {
                    "id": str(prop.id),
                    "identifier": prop.identifier,
                    "uri": prop.uri,
                    "label": prop.label,
                    "description": prop.description,
                    "domain_class_uri": prop.domain_class,
                    "range_scheme_id": str(prop.range_scheme_id) if prop.range_scheme_id else None,
                    "range_scheme_uri": prop.range_scheme_uri,
                    "range_datatype": prop.range_datatype,
                    "cardinality": prop.cardinality,
                    "required": prop.required,
                }
            )

        classes = []
        for cls in snapshot.classes:
            classes.append(
                {
                    "id": str(cls.id),
                    "identifier": cls.identifier,
                    "uri": cls.uri,
                    "label": cls.label,
                    "description": cls.description,
                    "scope_note": cls.scope_note,
                }
            )

        doc = {
            "format_version": FORMAT_VERSION,
            "version": version.version,
            "title": version.title,
            "published_at": version.published_at.isoformat(),
            "publisher": version.publisher,
            "pre_release": not version.finalized,
            "previous_version_id": (
                str(version.previous_version_id) if version.previous_version_id else None
            ),
            "project": {
                "id": str(snapshot.project.id),
                "name": snapshot.project.name,
                "description": snapshot.project.description,
                "namespace": snapshot.project.namespace,
            },
            "schemes": schemes,
            "classes": classes,
            "properties": properties,
        }
        return json.dumps(doc, separators=(",", ":")).encode()

    @staticmethod
    def render_project_index(project: Project, versions: list[PublishedVersion]) -> bytes:
        """Render a project index.json from a project and its versions.

        ``versions`` must be sorted by version_sort_key descending (newest first).
        """
        latest_version = None
        for v in versions:
            if v.finalized:
                latest_version = v.version
                break

        version_entries = []
        for v in versions:
            snapshot = v.snapshot_vocabulary
            version_entries.append(
                {
                    "version": v.version,
                    "title": v.title,
                    "published_at": v.published_at.isoformat(),
                    "publisher": v.publisher,
                    "pre_release": not v.finalized,
                    "previous_version_id": (
                        str(v.previous_version_id) if v.previous_version_id else None
                    ),
                    "notes": v.notes,
                    "content_summary": {
                        "schemes": len(snapshot.concept_schemes),
                        "concepts": sum(len(s.concepts) for s in snapshot.concept_schemes),
                        "properties": len(snapshot.properties),
                        "classes": len(snapshot.classes),
                    },
                }
            )

        doc = {
            "format_version": FORMAT_VERSION,
            "project": {
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "namespace": project.namespace,
            },
            "latest_version": latest_version,
            "versions": version_entries,
        }
        return json.dumps(doc, separators=(",", ":")).encode()

    @staticmethod
    def render_root_index(projects_with_latest: list[tuple[Project, str | None]]) -> bytes:
        """Render the root index.json listing all published projects."""
        projects = []
        for project, latest_version in projects_with_latest:
            projects.append(
                {
                    "id": str(project.id),
                    "name": project.name,
                    "description": project.description,
                    "latest_version": latest_version,
                }
            )
        doc = {
            "format_version": FORMAT_VERSION,
            "projects": projects,
        }
        return json.dumps(doc, separators=(",", ":")).encode()

    # ------------------------------------------------------------------
    # Orchestration (service queries → render → blob writes → CDN purge)
    # ------------------------------------------------------------------

    async def publish_reader_files(self, version: PublishedVersion) -> None:
        """Generate and write all reader files for a published version."""
        project = version.project

        # 1. Write vocabulary (immutable — version in URL, never changes)
        vocab_path = f"{project.id}/{version.version}/vocabulary.json"
        await self._blob_store.put(vocab_path, self.render_vocabulary(version))

        # 2. Write project index (mutable — regenerated on each publish)
        all_versions = await self._publishing_service.list_versions(project.id)
        project_index_path = f"{project.id}/index.json"
        await self._blob_store.put(
            project_index_path, self.render_project_index(project, all_versions)
        )

        # 3. Write root index (skip for pre-releases of already-published projects)
        purge_paths = [f"/{project_index_path}"]
        is_first_publish = len(all_versions) == 1
        if version.finalized or is_first_publish:
            projects_with_latest = (
                await self._publishing_service.list_projects_with_latest_version()
            )
            await self._blob_store.put(
                "index.json", self.render_root_index(projects_with_latest)
            )
            purge_paths.append("/index.json")

        # 4. Purge CDN cache for mutable files
        await self._cdn_purger.purge(purge_paths)

        logger.info(
            "Published reader files for %s v%s (root_index=%s)",
            project.id,
            version.version,
            version.finalized or is_first_publish,
        )
