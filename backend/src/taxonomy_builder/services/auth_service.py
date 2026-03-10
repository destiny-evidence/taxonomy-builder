"""Authentication service for OIDC token validation and user management."""

from datetime import datetime
from uuid import UUID

import httpx
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.config import settings
from taxonomy_builder.models.user import User


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class AuthService:
    """Service for authentication and user management.

    Handles OIDC token validation with Keycloak and local user provisioning.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._jwks_cache: dict | None = None
        self._oidc_config: dict | None = None

    @property
    def _issuer_url(self) -> str:
        """Get the Keycloak issuer URL for the configured realm."""
        return f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"

    async def get_oidc_config(self) -> dict:
        """Fetch OIDC configuration from Keycloak."""
        if self._oidc_config is None:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self._issuer_url}/.well-known/openid-configuration"
                )
                resp.raise_for_status()
                self._oidc_config = resp.json()
        return self._oidc_config

    async def get_jwks(self) -> dict:
        """Fetch JWKS from Keycloak for token validation."""
        if self._jwks_cache is None:
            config = await self.get_oidc_config()
            async with httpx.AsyncClient() as client:
                resp = await client.get(config["jwks_uri"])
                resp.raise_for_status()
                self._jwks_cache = resp.json()
        return self._jwks_cache

    async def validate_token(self, token: str) -> dict:
        """Validate an OIDC access token and return claims.

        Args:
            token: The access token from Keycloak

        Returns:
            Token claims including sub, email, name, and group claims

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            jwks = await self.get_jwks()
            unverified_header = jwt.get_unverified_header(token)

            # Find the right key
            rsa_key = None
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = key
                    break

            if rsa_key is None:
                raise AuthenticationError("Unable to find appropriate key")

            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=settings.keycloak_client_id,
                issuer=self._issuer_url,
            )
            return payload
        except JWTError as e:
            raise AuthenticationError(f"Token validation failed: {e}")

    async def get_or_create_user(self, token_claims: dict) -> User:
        """Get existing user or create new one from OIDC claims.

        Args:
            token_claims: Validated token claims from Keycloak

        Returns:
            User instance (existing or newly created)
        """
        keycloak_user_id = token_claims["sub"]

        # Try to find existing user
        result = await self.db.execute(
            select(User).where(User.keycloak_user_id == keycloak_user_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            # Create new user
            display_name = token_claims.get(
                "name", token_claims.get("preferred_username", "Unknown")
            )
            user = User(
                keycloak_user_id=keycloak_user_id,
                email=token_claims.get("email", f"{keycloak_user_id}@unknown"),
                display_name=display_name,
                last_login_at=datetime.now(),
            )
            self.db.add(user)
            await self.db.flush()
            await self.db.refresh(user)
        else:
            # Update last login
            user.last_login_at = datetime.now()
            await self.db.flush()

        return user

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by internal ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    def extract_org_claims(self, token_claims: dict) -> dict:
        """Extract organization claims from Keycloak token.

        Keycloak can include group membership in tokens via the groups claim.
        Groups can be used to represent organizations.

        Args:
            token_claims: The decoded token claims

        Returns:
            Dict with org_id, org_name, and roles
        """
        # Keycloak uses "groups" claim for group membership
        groups = token_claims.get("groups", [])

        # For now, use the first group as the "primary" organization
        # In Phase 2, we'll handle multi-org properly
        org_id = groups[0] if groups else None
        org_name = org_id  # Group name is the org name

        # Keycloak realm roles are in realm_access.roles
        realm_roles = token_claims.get("realm_access", {}).get("roles", [])

        return {
            "org_id": org_id,
            "org_name": org_name,
            "roles": realm_roles,
        }
