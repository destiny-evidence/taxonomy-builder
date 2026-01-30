"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/taxonomy_builder"
    test_database_url: str = (
        "postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/taxonomy_builder_test"
    )

    # Keycloak OIDC settings (for JWT validation)
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "taxonomy-builder"
    keycloak_client_id: str = "taxonomy-builder-api"

    model_config = {"env_prefix": "TAXONOMY_"}


settings = Settings()
