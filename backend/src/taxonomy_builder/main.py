"""FastAPI application entry point."""

import subprocess
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from sqlalchemy import text

from taxonomy_builder.api.comments import comments_router, concept_comments_router
from taxonomy_builder.api.concepts import concepts_router, scheme_concepts_router
from taxonomy_builder.api.history import router as history_router
from taxonomy_builder.api.ontology import router as ontology_router
from taxonomy_builder.api.ontology_classes import (
    ontology_classes_router,
    project_ontology_classes_router,
)
from taxonomy_builder.api.projects import router as projects_router
from taxonomy_builder.api.properties import project_properties_router, properties_router
from taxonomy_builder.api.schemes import project_schemes_router, schemes_router
from taxonomy_builder.config import settings
from taxonomy_builder.database import db_manager
from taxonomy_builder.services.core_ontology_service import get_core_ontology


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize and cleanup application resources."""
    db_manager.init(settings.effective_database_url)
    # Warm the core ontology cache at startup
    get_core_ontology()
    yield
    await db_manager.close()


app = FastAPI(
    title="Taxonomy Builder",
    description="A web-based taxonomy management tool for SKOS vocabularies",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(projects_router)
app.include_router(project_schemes_router)
app.include_router(schemes_router)
app.include_router(project_properties_router)
app.include_router(properties_router)
app.include_router(project_ontology_classes_router)
app.include_router(ontology_classes_router)
app.include_router(scheme_concepts_router)
app.include_router(concepts_router)
app.include_router(concept_comments_router)
app.include_router(comments_router)
app.include_router(history_router)
app.include_router(ontology_router)


@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check() -> Response:
    """Health check endpoint. Returns 200 if database is accessible."""
    try:
        async with db_manager.session() as session:
            await session.execute(text("SELECT 1"))
        return Response(
            status_code=200, content='{"status": "healthy"}', media_type="application/json"
        )
    except Exception:
        return Response(
            status_code=503, content='{"status": "unhealthy"}', media_type="application/json"
        )


def _get_git_branch() -> str | None:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _get_git_commit() -> str | None:
    """Get the current git commit hash (short)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


@app.get("/api/dev/info")
async def dev_info() -> dict:
    """Development info endpoint. Returns git branch and other dev info.

    This endpoint is intended for local development to help identify
    which worktree/branch you're looking at.
    """
    return {
        "branch": _get_git_branch(),
        "commit": _get_git_commit(),
    }
