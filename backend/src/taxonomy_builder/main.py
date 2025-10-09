"""Main FastAPI application for the taxonomy builder."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from taxonomy_builder.api import taxonomies

app = FastAPI(
    title="Taxonomy Builder API",
    description="SKOS-based taxonomy builder for evidence repositories",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(taxonomies.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
