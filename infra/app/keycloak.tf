# Keycloak realm and client configuration

locals {
  keycloak_realm_id = var.existing_keycloak_realm_id != null ? var.existing_keycloak_realm_id : keycloak_realm.this[0].id
}

# Realm (created only if existing_keycloak_realm_id is not provided)
resource "keycloak_realm" "this" {
  count = var.existing_keycloak_realm_id == null ? 1 : 0

  realm   = var.keycloak_realm_name
  enabled = true

  login_theme = "keycloak"

  login_with_email_allowed       = true
  duplicate_emails_allowed       = false
  reset_password_allowed         = true
  remember_me                    = true
  verify_email                   = false
  registration_allowed           = false
  registration_email_as_username = true
}

# API Client (bearer-only resource server)
resource "keycloak_openid_client" "api" {
  realm_id  = local.keycloak_realm_id
  client_id = "taxonomy-builder-api"
  name      = "Taxonomy Builder API"
  enabled   = true

  access_type = "BEARER-ONLY"
}

# API User role on the API client (includes feedback-user)
resource "keycloak_role" "api_user" {
  realm_id    = local.keycloak_realm_id
  client_id   = keycloak_openid_client.api.id
  name        = "api-user"
  description = "User with access to the Taxonomy Builder API"

  composite_roles = [keycloak_role.feedback_user.id]
}

# Client scope for API audience
resource "keycloak_openid_client_scope" "api" {
  realm_id               = local.keycloak_realm_id
  name                   = "taxonomy-builder-api-scope"
  description            = "Scope for accessing the Taxonomy Builder API"
  include_in_token_scope = true
}

# Audience Resolve protocol mapper on the scope
resource "keycloak_openid_audience_resolve_protocol_mapper" "api" {
  realm_id        = local.keycloak_realm_id
  client_scope_id = keycloak_openid_client_scope.api.id
  name            = "audience-resolve"
}

# Role scope mapping - link api-user role to the client scope
resource "keycloak_generic_role_mapper" "api_scope_role" {
  realm_id        = local.keycloak_realm_id
  client_scope_id = keycloak_openid_client_scope.api.id
  role_id         = keycloak_role.api_user.id
}

# UI Client (public, standard flow for browser authentication)
resource "keycloak_openid_client" "ui" {
  realm_id  = local.keycloak_realm_id
  client_id = "taxonomy-builder-ui"
  name      = "Taxonomy Builder UI"
  enabled   = true

  access_type                  = "PUBLIC"
  standard_flow_enabled        = true
  direct_access_grants_enabled = false
  full_scope_allowed           = false

  valid_redirect_uris = ["https://${local.builder_custom_domain}/*"]
  web_origins         = ["https://${local.builder_custom_domain}"]
}

# --- Feedback ---

# Feedback User role on the API client (limited permissions)
resource "keycloak_role" "feedback_user" {
  realm_id    = local.keycloak_realm_id
  client_id   = keycloak_openid_client.api.id
  name        = "feedback-user"
  description = "User with access to submit feedback only"
}

# Client scope for feedback API access
resource "keycloak_openid_client_scope" "feedback_api" {
  realm_id               = local.keycloak_realm_id
  name                   = "feedback-api-scope"
  description            = "Scope for accessing the feedback API"
  include_in_token_scope = true
}

# Audience Resolve protocol mapper on the feedback scope
resource "keycloak_openid_audience_resolve_protocol_mapper" "feedback_api" {
  realm_id        = local.keycloak_realm_id
  client_scope_id = keycloak_openid_client_scope.feedback_api.id
  name            = "audience-resolve"
}

# Role scope mapping - link feedback-user role to the feedback client scope
resource "keycloak_generic_role_mapper" "feedback_scope_role" {
  realm_id        = local.keycloak_realm_id
  client_scope_id = keycloak_openid_client_scope.feedback_api.id
  role_id         = keycloak_role.feedback_user.id
}

# Feedback UI Client (public, standard flow for browser authentication)
resource "keycloak_openid_client" "feedback_ui" {
  realm_id  = local.keycloak_realm_id
  client_id = "taxonomy-feedback-ui"
  name      = "Taxonomy Feedback UI"
  enabled   = true

  access_type                  = "PUBLIC"
  standard_flow_enabled        = true
  direct_access_grants_enabled = false
  full_scope_allowed           = false

  valid_redirect_uris = ["https://${local.feedback_custom_domain}/*"]
  web_origins         = ["https://${local.feedback_custom_domain}"]
}

# --- Default role assignment ---

# Add api-user to the realm's built-in default roles so all users get it
data "keycloak_role" "default_roles" {
  realm_id = local.keycloak_realm_id
  name     = "default-roles-${var.keycloak_realm_name}"
}

resource "keycloak_generic_role_mapper" "default_api_user" {
  realm_id  = local.keycloak_realm_id
  role_id   = keycloak_role.api_user.id
  parent_id = data.keycloak_role.default_roles.id
}

# --- Client scopes ---

resource "keycloak_openid_client_default_scopes" "ui" {
  realm_id  = local.keycloak_realm_id
  client_id = keycloak_openid_client.ui.id

  default_scopes = [
    "openid",
    "profile",
    "email",
    "basic",
    "roles",
    "web-origins",
    "acr",
    keycloak_openid_client_scope.api.name,
  ]
}

resource "keycloak_openid_client_default_scopes" "feedback_ui" {
  realm_id  = local.keycloak_realm_id
  client_id = keycloak_openid_client.feedback_ui.id

  default_scopes = [
    "openid",
    "profile",
    "email",
    "basic",
    "roles",
    "web-origins",
    "acr",
    keycloak_openid_client_scope.feedback_api.name,
  ]
}
