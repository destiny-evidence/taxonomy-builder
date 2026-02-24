# GitHub Actions OIDC federation for CI/CD

data "azuread_client_config" "current" {
}

data "azurerm_subscription" "current" {
}

# Azure AD application for GitHub Actions
resource "azuread_application_registration" "github_actions" {
  display_name     = "github-actions-${local.name}"
  sign_in_audience = "AzureADMyOrg"
}

resource "azuread_service_principal" "github_actions" {
  client_id                    = azuread_application_registration.github_actions.client_id
  app_role_assignment_required = true
  owners                       = [data.azuread_client_config.current.object_id]
}

# Federated identity credential for GitHub Actions environment
resource "azuread_application_federated_identity_credential" "github" {
  display_name = "gha-${var.app_name}-deploy-${var.environment}"

  application_id = azuread_application_registration.github_actions.id
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:${var.github_repo}:environment:${var.environment}"
}

# GitHub Actions - ACR Push (for building and pushing images)
resource "azurerm_role_assignment" "gha_acr_push" {
  role_definition_name = "AcrPush"
  scope                = data.azurerm_container_registry.this.id
  principal_id         = azuread_service_principal.github_actions.object_id
}

# GitHub Actions - ACR Pull
resource "azurerm_role_assignment" "gha_acr_pull" {
  role_definition_name = "AcrPull"
  scope                = data.azurerm_container_registry.this.id
  principal_id         = azuread_service_principal.github_actions.object_id
}

# GitHub Actions - Resource Group Reader
resource "azurerm_role_assignment" "gha_rg_reader" {
  role_definition_name = "Reader"
  scope                = azurerm_resource_group.this.id
  principal_id         = azuread_service_principal.github_actions.object_id
}

# GitHub Actions - Container App Environment Contributor
resource "azurerm_role_assignment" "gha_container_app_env_contributor" {
  role_definition_name = "Contributor"
  scope                = module.container_app_api.container_app_env_id
  principal_id         = azuread_service_principal.github_actions.object_id
}

# GitHub Actions - API Container App Contributor
resource "azurerm_role_assignment" "gha_api_contributor" {
  role_definition_name = "Contributor"
  scope                = module.container_app_api.container_app_id
  principal_id         = azuread_service_principal.github_actions.object_id
}

# GitHub Actions - Keycloak Container App Contributor
resource "azurerm_role_assignment" "gha_keycloak_contributor" {
  role_definition_name = "Contributor"
  scope                = azurerm_container_app.keycloak.id
  principal_id         = azuread_service_principal.github_actions.object_id
}

# GitHub Actions - DB Migrator Job Contributor
resource "azurerm_role_assignment" "gha_db_migrator_contributor" {
  role_definition_name = "Contributor"
  scope                = azurerm_container_app_job.db_migrator.id
  principal_id         = azuread_service_principal.github_actions.object_id
}

# GitHub Actions - Storage Blob Data Contributor (for deploying frontend)
resource "azurerm_role_assignment" "gha_storage_blob_contributor" {
  role_definition_name = "Storage Blob Data Contributor"
  scope                = azurerm_storage_account.frontend.id
  principal_id         = azuread_service_principal.github_actions.object_id
}

# GitHub Actions - Storage Account Contributor (for listing keys during blob upload)
resource "azurerm_role_assignment" "gha_storage_account_contributor" {
  role_definition_name = "Storage Account Contributor"
  scope                = azurerm_storage_account.frontend.id
  principal_id         = azuread_service_principal.github_actions.object_id
}

# GitHub Actions - Feedback UI Storage Blob Data Contributor
resource "azurerm_role_assignment" "gha_feedback_blob_contributor" {
  role_definition_name = "Storage Blob Data Contributor"
  scope                = azurerm_storage_account.feedback.id
  principal_id         = azuread_service_principal.github_actions.object_id
}

# GitHub Actions - Feedback UI Storage Account Contributor
resource "azurerm_role_assignment" "gha_feedback_account_contributor" {
  role_definition_name = "Storage Account Contributor"
  scope                = azurerm_storage_account.feedback.id
  principal_id         = azuread_service_principal.github_actions.object_id
}

# GitHub repository environment for deployment variables
resource "github_repository_environment" "environment" {
  repository  = "taxonomy-builder"
  environment = var.environment
}

resource "github_actions_environment_variable" "registry_name" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "REGISTRY_NAME"
  value         = data.azurerm_container_registry.this.name
}

resource "github_actions_environment_variable" "azure_client_id" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "AZURE_CLIENT_ID"
  value         = azuread_application_registration.github_actions.client_id
}

resource "github_actions_environment_variable" "azure_subscription_id" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "AZURE_SUBSCRIPTION_ID"
  value         = data.azurerm_subscription.current.subscription_id
}

resource "github_actions_environment_variable" "azure_tenant_id" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "AZURE_TENANT_ID"
  value         = data.azurerm_subscription.current.tenant_id
}

resource "github_actions_environment_variable" "app_name" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "APP_NAME"
  value         = var.app_name
}

resource "github_actions_environment_variable" "container_app_name" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "CONTAINER_APP_NAME"
  value         = module.container_app_api.container_app_name
}

resource "github_actions_environment_variable" "container_app_env" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "CONTAINER_APP_ENV"
  value         = module.container_app_api.container_app_env_name
}

resource "github_actions_environment_variable" "environment_name" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "ENVIRONMENT_NAME"
  value         = var.environment
}

resource "github_actions_environment_variable" "resource_group" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "RESOURCE_GROUP"
  value         = azurerm_resource_group.this.name
}

resource "github_actions_environment_variable" "storage_account_name" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "STORAGE_ACCOUNT_NAME"
  value         = azurerm_storage_account.frontend.name
}

resource "github_actions_environment_variable" "api_base_url" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "API_BASE_URL"
  value         = "/api"
}

resource "github_actions_environment_variable" "keycloak_url" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "KEYCLOAK_URL"
  value         = "https://${var.custom_domain}"
}

resource "github_actions_environment_variable" "keycloak_realm" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "KEYCLOAK_REALM"
  value         = "taxonomy-builder"
}

resource "github_actions_environment_variable" "keycloak_client_id" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "KEYCLOAK_CLIENT_ID"
  value         = "taxonomy-builder-ui"
}

# Feedback UI deployment variables

resource "github_actions_environment_variable" "feedback_storage_account_name" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "FEEDBACK_STORAGE_ACCOUNT_NAME"
  value         = azurerm_storage_account.feedback.name
}

resource "github_actions_environment_variable" "frontdoor_profile_name" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "FRONTDOOR_PROFILE_NAME"
  value         = azurerm_cdn_frontdoor_profile.this.name
}

resource "github_actions_environment_variable" "frontdoor_endpoint_name" {
  repository    = github_repository_environment.environment.repository
  environment   = github_repository_environment.environment.environment
  variable_name = "FRONTDOOR_ENDPOINT_NAME"
  value         = azurerm_cdn_frontdoor_endpoint.this.name
}
