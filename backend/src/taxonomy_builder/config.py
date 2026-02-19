"""Application configuration."""

from pathlib import Path
from urllib.parse import quote_plus

from pydantic import computed_field
from pydantic_settings import BaseSettings


def _default_core_ontology_path() -> str:
    """Get the default path to the bundled core ontology file."""
    return str(Path(__file__).parent / "data" / "evrepo-core.ttl")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database connection - either provide full URL or individual components
    database_url: str | None = None
    db_host: str | None = None
    db_name: str | None = None
    db_user: str | None = None
    db_password: str | None = None

    test_database_url: str = (
        "postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/taxonomy_builder_test"
    )

    # Keycloak OIDC settings (for JWT validation)
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "taxonomy-builder"
    keycloak_client_id: str = "taxonomy-builder-api"

    # Core ontology file path
    core_ontology_path: str = _default_core_ontology_path()

    # Blob storage
    blob_backend: str = "filesystem"
    blob_filesystem_root: str = "./.blob-storage"
    blob_azure_account_url: str | None = None
    blob_azure_container: str = "published"

    # CDN cache purge (Azure Front Door)
    cdn_subscription_id: str | None = None
    cdn_resource_group: str | None = None
    cdn_profile_name: str | None = None
    cdn_endpoint_name: str | None = None

    model_config = {"env_prefix": "TAXONOMY_"}

    @computed_field
    @property
    def effective_database_url(self) -> str:
        """Get the database URL, constructing from components if needed."""
        if self.database_url:
            return self.database_url
        if self.db_host and self.db_name and self.db_user and self.db_password:
            password = quote_plus(self.db_password)
            return f"postgresql+asyncpg://{self.db_user}:{password}@{self.db_host}:5432/{self.db_name}"
        # Default for local development
        return "postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/taxonomy_builder"


settings = Settings()
