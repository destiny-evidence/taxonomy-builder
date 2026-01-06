"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/taxonomy_builder"
    test_database_url: str = (
        "postgresql+asyncpg://taxonomy:taxonomy@localhost:5432/taxonomy_builder_test"
    )

    model_config = {"env_prefix": "TAXONOMY_"}


settings = Settings()
