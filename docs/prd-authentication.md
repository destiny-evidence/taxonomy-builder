# PRD: Authentication & Authorization

## Overview

Integrate Microsoft Entra External ID for user authentication and implement role-based access control to enable multi-user collaboration on taxonomy management.

## Problem

Currently the application has no authentication:
- Anyone with access can modify any data
- No audit trail of who made changes
- Cannot support multiple teams with different projects
- Cannot deploy to production without access control

## Requirements

### Authentication

1. **Microsoft Entra External ID** integration
   - OAuth 2.0 / OpenID Connect flow
   - Support for SSO with evidence platform
2. **Login/logout flow:**
   - Unauthenticated users redirected to login
   - Session management with secure tokens
   - Logout clears session
3. **User profile:**
   - Store user ID, email, display name from Entra
   - Create local user record on first login

### Authorization

1. **Role-based access control (RBAC):**

   | Role | Permissions |
   |------|-------------|
   | Viewer | Read all projects/schemes/concepts |
   | Editor | Viewer + Create/edit concepts, schemes |
   | Admin | Editor + Create/delete projects, manage users |

2. **Project-scoped permissions** (stretch goal):
   - Users can have different roles per project
   - Admins can invite users to projects

3. **API protection:**
   - All mutating endpoints require authentication
   - Read endpoints require authentication (no public access)

## User Flow

### Login

1. User navigates to application
2. If not authenticated, redirect to Entra login page
3. User authenticates with Entra (SSO or credentials)
4. Entra redirects back with authorization code
5. Backend exchanges code for tokens
6. Backend creates session, returns session cookie
7. User sees application with their identity

### Logout

1. User clicks logout
2. Session destroyed on backend
3. Redirect to Entra logout (optional, for full SSO logout)
4. Redirect back to login page

## Technical Approach

### Backend

**Dependencies:**
- `authlib` or `python-jose` for JWT handling
- `httpx` for Entra token exchange

**Configuration:**
```python
class Settings(BaseSettings):
    entra_client_id: str
    entra_client_secret: str
    entra_tenant_id: str
    entra_redirect_uri: str
```

**New models:**

```python
class User(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    entra_id: Mapped[str] = mapped_column(unique=True)  # Entra object ID
    email: Mapped[str]
    display_name: Mapped[str]
    role: Mapped[str] = mapped_column(default="viewer")  # viewer, editor, admin
    created_at: Mapped[datetime]
    last_login: Mapped[datetime]
```

**New endpoints:**

```
GET /auth/login -> Redirect to Entra
GET /auth/callback -> Handle Entra redirect, create session
POST /auth/logout -> Destroy session
GET /auth/me -> Return current user info
```

**Authentication middleware:**

```python
async def get_current_user(request: Request, session: AsyncSession) -> User:
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(401, "Not authenticated")
    # Validate token, lookup user
    return user

# Dependency for protected routes
CurrentUser = Annotated[User, Depends(get_current_user)]
```

**Authorization decorator:**

```python
def require_role(minimum_role: str):
    def decorator(func):
        async def wrapper(user: CurrentUser, ...):
            if not has_permission(user.role, minimum_role):
                raise HTTPException(403, "Insufficient permissions")
            return await func(user, ...)
        return wrapper
    return decorator
```

### Frontend

**Auth state:**

```typescript
// state/auth.ts
export const currentUser = signal<User | null>(null);
export const isAuthenticated = computed(() => currentUser.value !== null);
```

**Protected routes:**

```typescript
function ProtectedRoute({ children }) {
  if (!isAuthenticated.value) {
    window.location.href = "/auth/login";
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

**Option A: JWT in httpOnly cookie**
- Stateless, scalable
- Short expiry with refresh token

**Option B: Server-side sessions**
- Session ID in cookie, data in Redis/DB
- Easier revocation

Recommend **Option A** for simplicity in MVP.

## Entra Configuration

Required Entra app registration:
1. Create app registration in Entra admin center
2. Configure redirect URI: `https://app.example.com/auth/callback`
3. Add API permissions: `openid`, `profile`, `email`
4. Generate client secret
5. Note: Tenant ID, Client ID, Client Secret

## Database Migration

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    entra_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Update change_events to reference users
ALTER TABLE change_events
ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id);
```

## UI Changes

1. **Login page:** Simple branded page with "Sign in with Microsoft" button
2. **Header:** Show user name and logout button
3. **Role indicators:** Show user's role somewhere accessible
4. **Permission errors:** Friendly message when action not allowed

## Out of Scope

- Project-scoped permissions (all users see all projects)
- User management UI (manage via Entra or direct DB)
- API keys for programmatic access
- Multi-tenancy
- Custom roles beyond viewer/editor/admin

## Rollout Plan

1. Deploy with auth optional (feature flag)
2. Test with small group
3. Enable auth required for all users
4. Migrate any existing test data to have user attribution

## Success Criteria

- Users can log in via Microsoft Entra
- Unauthenticated requests are rejected
- User identity shown in UI
- Changes are attributed to users in history
- Editors can create/edit, viewers cannot
- Admins can manage projects
