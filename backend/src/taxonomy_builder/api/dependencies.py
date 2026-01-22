"""FastAPI dependencies for authentication and authorization."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.database import get_db
from taxonomy_builder.models.user import User
from taxonomy_builder.services.auth_service import AuthenticationError, AuthService


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency that provides an AuthService instance."""
    return AuthService(db)


@dataclass
class AuthenticatedUser:
    """Represents an authenticated user with their org claims."""

    user: User
    org_id: str | None
    org_name: str | None
    org_roles: list[str]


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthenticatedUser:
    """Dependency that extracts and validates the current user from token.

    Returns an AuthenticatedUser containing:
    - The User model instance
    - Organization claims from the Keycloak token

    Raises:
        HTTPException 401 if not authenticated
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    try:
        claims = await auth_service.validate_token(token)
        user = await auth_service.get_or_create_user(claims)
        org_claims = auth_service.extract_org_claims(claims)

        return AuthenticatedUser(
            user=user,
            org_id=org_claims["org_id"],
            org_name=org_claims["org_name"],
            org_roles=org_claims["roles"],
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    authorization: Annotated[str | None, Header()] = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthenticatedUser | None:
    """Dependency that optionally extracts user (for public endpoints)."""
    if authorization is None:
        return None

    try:
        return await get_current_user(authorization, auth_service)
    except HTTPException:
        return None


# Type alias for use in route function signatures
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
OptionalUser = Annotated[AuthenticatedUser | None, Depends(get_optional_user)]
