"""Service for orchestrating all published file writes to blob storage."""

from __future__ import annotations

import logging

from taxonomy_builder.blob_store import BlobStore, CdnPurger
from taxonomy_builder.models.published_version import PublishedVersion
from taxonomy_builder.services.reader_file_service import ReaderFileService
from taxonomy_builder.services.skos_export_service import SKOSExportService

logger = logging.getLogger(__name__)


class PublishedFileService:
    """Orchestrates reader file and RDF artifact writes during publishing."""

    def __init__(
        self,
        reader_file_service: ReaderFileService,
        skos_export_service: SKOSExportService,
        blob_store: BlobStore,
        cdn_purger: CdnPurger,
    ) -> None:
        self._reader_file_service = reader_file_service
        self._skos_export_service = skos_export_service
        self._blob_store = blob_store
        self._cdn_purger = cdn_purger

    async def publish(self, version: PublishedVersion) -> None:
        """Write all published files: reader JSON files + RDF artifacts."""
        await self._reader_file_service.publish_reader_files(version)

        # Write RDF artifacts (immutable — version in path, no CDN purge needed)
        artifacts = self._skos_export_service.render_rdf_artifacts(version)
        project = version.project
        for filename, (data, content_type) in artifacts.items():
            path = f"{project.id}/{version.version}/{filename}"
            await self._blob_store.put(path, data, content_type=content_type)

        logger.info(
            "Published RDF artifacts for %s v%s (%d files)",
            project.id,
            version.version,
            len(artifacts),
        )
