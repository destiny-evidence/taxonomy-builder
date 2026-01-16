# PRD: Authentication & Authorization

## Overview

Integrate Keycloak for user authentication and implement role-based access control to enable multi-user collaboration on taxonomy management. Authorization via OpenFGA will be added in a later phase.

## Problem

Currently the application has no authentication:
- Anyone with access can modify any data
- No audit trail of who made changes
- Cannot support multiple teams with different projects
- Cannot deploy to production without access control

## Requirements

### Phase 1: Authentication (Current Focus)

1. **Keycloak** integration (self-hosted via Docker)
   - OAuth 2.0 / OpenID Connect flow
   - Support for multiple organizations/realms
   - Self-hosted for development, can connect to hosted instance for production
2. **Login/logout flow:**
   - Unauthenticated users redirected to login
   - JWT tokens with secure httpOnly cookies
   - Logout clears session
3. **User profile:**
   - Store user ID, email, display name from Keycloak
   - Create local user record on first login
   - Track organization membership from Keycloak groups/roles

### Phase 2: Authorization (Future)

1. **OpenFGA** for fine-grained authorization
   - Project-level permissions (viewer, contributor, owner)
   - Organization-based access control
   - Users inherit project access through their organizations

2. **Role-based access control (RBAC):**

   | Role | Permissions |
   |------|-------------|
   | Viewer | Read all projects/schemes/concepts |
   | Editor | Viewer + Create/edit concepts, schemes |
   | Admin | Editor + Create/delete projects, manage users |

3. **API protection:**
   - All mutating endpoints require authentication
   - Read endpoints require authentication (no public access)

## User Flow

### Login

1. User navigates to application
2. If not authenticated, redirect to Keycloak login page
3. User authenticates with Keycloak (credentials or SSO)
4. Keycloak redirects back with authorization code
5. Backend exchanges code for tokens
6. Backend creates/updates local user record
7. Backend returns JWT in httpOnly cookie
8. User sees application with their identity

### Logout

1. User clicks logout
2. Session cookie cleared
3. Redirect to Keycloak logout (for full SSO logout)
4. Redirect back to login page

## Technical Approach

### Backend

**Dependencies:**
- `python-jose` for JWT handling
- `httpx` for Keycloak token exchange

**Configuration:**
```python
class Settings(BaseSettings):
    keycloak_url: str  # e.g., http://localhost:8080
    keycloak_realm: str  # e.g., taxonomy-builder
    keycloak_client_id: str
    keycloak_client_secret: str
    oidc_redirect_uri: str  # e.g., http://localhost:5173/auth/callback
```

**New models:**

```python
class User(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    keycloak_user_id: Mapped[str] = mapped_column(unique=True)  # Keycloak subject ID
    email: Mapped[str]
    display_name: Mapped[str]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    last_login_at: Mapped[datetime]
```

**New endpoints:**

```
GET /api/auth/login -> Redirect to Keycloak
GET /api/auth/callback -> Handle Keycloak redirect, issue JWT cookie
POST /api/auth/logout -> Clear cookie, redirect to Keycloak logout
GET /api/auth/me -> Return current user info
```

**Authentication dependency:**

```python
@dataclass
class AuthenticatedUser:
    user: User
    org_id: str | None
    org_name: str | None
    org_roles: list[str]

async def get_current_user(
    authorization: str | None = Header(None),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthenticatedUser:
    if authorization is None:
        raise HTTPException(401, "Not authenticated")
    token = authorization.removeprefix("Bearer ")
    claims = await auth_service.validate_token(token)
    user = await auth_service.get_or_create_user(claims)
    return AuthenticatedUser(user=user, ...)

CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
```

### Frontend

**Auth state:**

```typescript
// state/auth.ts
export const accessToken = signal<string | null>(null);
export const currentUser = signal<AuthUser | null>(null);
export const isAuthenticated = computed(() => currentUser.value !== null);
```

**Protected routes:**

```typescript
function ProtectedRoute({ children }) {
  if (!isAuthenticated.value) {
    window.location.href = "/api/auth/login";
    return null;
  }
  return children;
}
```

**User display:**

```typescript
// In AppShell header
<div class="user-menu">
  {currentUser.value?.display_name}
  <button onClick={logout}>Logout</button>
</div>
```

### Session Management

JWT in httpOnly cookie with:
- Short expiry (15 minutes)
- Refresh token for seamless renewal
- CSRF protection via SameSite=Strict

## Keycloak Configuration

### Docker Setup

Keycloak runs in Docker alongside the application:

```yaml
keycloak:
  image: quay.io/keycloak/keycloak:latest
  command: start-dev
  environment:
    KEYCLOAK_ADMIN: admin
    KEYCLOAK_ADMIN_PASSWORD: admin
    KC_DB: postgres
    KC_DB_URL: jdbc:postgresql://db:5432/keycloak
    KC_DB_USERNAME: keycloak
    KC_DB_PASSWORD: keycloak
  ports:
    - "8080:8080"
```

### Realm Setup (Manual Steps)

After `docker compose up`:
1. Access Keycloak admin at `http://localhost:8080/admin`
2. Login as admin/admin
3. Create realm: `taxonomy-builder`
4. Create client:
   - Client ID: `taxonomy-builder-app`
   - Client Protocol: openid-connect
   - Access Type: confidential
   - Valid Redirect URIs: `http://localhost:5173/auth/callback`
   - Web Origins: `http://localhost:5173`
5. Note the client secret from Credentials tab
6. Create test users as needed

### Organization Support

Keycloak supports organizations via:
- **Groups**: Create groups for each org (EEF, UCL, PIK, etc.)
- **Group membership**: Assign users to groups
- **Token claims**: Configure client to include groups in token

## Database Migration

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    keycloak_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP
);

-- Update change_events to reference users
ALTER TABLE change_events
ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id);
```

## UI Changes

1. **Login page:** Simple page with "Sign in" button (redirects to Keycloak)
2. **Header:** Show user name and logout button
3. **Auth callback page:** Handle redirect from Keycloak, show loading state

## Out of Scope (Phase 1)

- Fine-grained authorization (OpenFGA) - Phase 2
- Project-scoped permissions - Phase 2
- Organization management UI - manage via Keycloak admin
- API keys for programmatic access
- Multi-tenancy

## Success Criteria (Phase 1)

- Keycloak runs in Docker alongside the app
- Users can log in via Keycloak
- Unauthenticated requests are rejected with 401
- User identity shown in UI header
- Local user record created on first login
- Logout works correctly

## Future: Phase 2 Authorization

Once basic auth is working, add:
1. OpenFGA for fine-grained authorization
2. ProjectOrganization model linking projects to Keycloak groups
3. Permission checks on API endpoints
4. Organization switcher in UI for multi-org users
