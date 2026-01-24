"""Application configuration."""

from urllib.parse import quote_plus

from pydantic import computed_field
from pydantic_settings import BaseSettings


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
