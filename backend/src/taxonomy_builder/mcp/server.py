"""MCP server for taxonomy builder — FastMCP setup and auth."""

from fastmcp import FastMCP
from fastmcp.server.auth import (
    AccessToken,
    AuthProvider,
    RemoteAuthProvider,
    TokenVerifier,
)
from pydantic import AnyHttpUrl

from taxonomy_builder.config import settings
from taxonomy_builder.database import db_manager
from taxonomy_builder.services.auth_service import AuthService


class KeycloakTokenVerifier(TokenVerifier):
    """Verify Keycloak JWTs and return an AccessToken with full claims."""

    async def verify_token(self, token: str) -> AccessToken | None:
        async with db_manager.session() as session:
            auth_service = AuthService(session)
            try:
                claims = await auth_service.validate_token(token)
            except Exception:
                return None

            return AccessToken(
                token=token,
                client_id=claims.get("azp", ""),
                scopes=claims.get("scope", "").split(),
                claims=claims,
            )


def require_manager(ctx) -> bool:
    """Auth check: require vocabulary.manager realm role."""
    if ctx.token is None:
        return False
    roles = ctx.token.claims.get("realm_access", {}).get("roles", [])
    return "vocabulary.manager" in roles


def _build_auth() -> AuthProvider | None:
    """Build auth provider based on config. None disables auth for local dev."""
    if not settings.mcp_auth:
        return None

    keycloak_issuer = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
    return RemoteAuthProvider(
        token_verifier=KeycloakTokenVerifier(),
        authorization_servers=[AnyHttpUrl(keycloak_issuer)],
        base_url=AnyHttpUrl(settings.mcp_base_url),
        resource_name=settings.mcp_resource_name,
        scopes_supported=["openid", "profile", "email", "roles", "mcp:tools"],
    )


auth_provider = _build_auth()

mcp = FastMCP(
    "taxonomy-builder",
    instructions=(
        f"You are a taxonomy building assistant connected to the "
        f"'{settings.environment}' environment. Use these tools to create, "
        "explore, and refine SKOS vocabularies. Start by listing projects, "
        "then explore schemes and their concept trees. Build taxonomies by "
        "creating concepts and organising them into hierarchies with broader/"
        "narrower relationships. Use check_quality to find issues."
    ),
    auth=auth_provider,
)

# Import tools to register them with the server
import taxonomy_builder.mcp.tools  # noqa: F401, E402
