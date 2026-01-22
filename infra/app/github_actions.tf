# GitHub Actions OIDC federation for CI/CD

data "azuread_client_config" "current" {
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
