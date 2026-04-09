"""MCP server for taxonomy builder — FastMCP setup and auth."""

from fastmcp import FastMCP
from fastmcp.server.auth import AccessToken, AuthProvider, RemoteAuthProvider, TokenVerifier
from pydantic import AnyHttpUrl

from taxonomy_builder.config import settings
from taxonomy_builder.database import db_manager
from taxonomy_builder.services.auth_service import AuthService


class KeycloakTokenVerifier(TokenVerifier):
    """Verify Keycloak JWTs and resolve local users."""

    async def verify_token(self, token: str) -> AccessToken | None:
        async with db_manager.session() as session:
            auth_service = AuthService(session)
            try:
                claims = await auth_service.validate_token(token)
            except Exception:
                return None

            user = await auth_service.get_or_create_user(claims)
            org_claims = auth_service.extract_org_claims(claims)
            roles = org_claims.get("roles", [])

            if "vocabulary.manager" not in roles:
                return None

            return AccessToken(
                token=token,
                client_id=str(user.id),
                scopes=roles,
                claims=claims,
            )


def _build_auth() -> AuthProvider | None:
    """Build auth provider based on config. None disables auth for local dev."""
    if not settings.mcp_auth:
        return None

    keycloak_issuer = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
    return RemoteAuthProvider(
        token_verifier=KeycloakTokenVerifier(),
        authorization_servers=[AnyHttpUrl(keycloak_issuer)],
        base_url=AnyHttpUrl(settings.mcp_base_url),
        resource_name="Taxonomy Builder MCP",
        scopes_supported=["openid", "profile", "email", "roles", "groups"],
    )


auth_provider = _build_auth()

mcp = FastMCP(
    "taxonomy-builder",
    instructions=(
        "You are a taxonomy building assistant. Use these tools to create, "
        "explore, and refine SKOS vocabularies. Start by listing projects, "
        "then explore schemes and their concept trees. Build taxonomies by "
        "creating concepts and organising them into hierarchies with broader/"
        "narrower relationships. Use check_quality to find issues."
    ),
    auth=auth_provider,
)

# Import tools to register them with the server
import taxonomy_builder.mcp.tools  # noqa: F401, E402
