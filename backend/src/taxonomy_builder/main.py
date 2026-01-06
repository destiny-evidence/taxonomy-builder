"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from taxonomy_builder.api.concepts import concepts_router, scheme_concepts_router
from taxonomy_builder.api.history import router as history_router
from taxonomy_builder.api.projects import router as projects_router
from taxonomy_builder.api.schemes import project_schemes_router, schemes_router
from taxonomy_builder.api.versions import router as versions_router
from taxonomy_builder.config import settings
from taxonomy_builder.database import db_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize and cleanup application resources."""
    db_manager.init(settings.database_url)
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
app.include_router(scheme_concepts_router)
app.include_router(concepts_router)
app.include_router(history_router)
app.include_router(versions_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
