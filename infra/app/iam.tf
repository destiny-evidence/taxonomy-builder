# Role assignments for managed identity access

# API Container App - ACR Pull
resource "azurerm_role_assignment" "api_acr_pull" {
  principal_id         = azurerm_user_assigned_identity.api.principal_id
  scope                = data.azurerm_container_registry.this.id
  role_definition_name = "AcrPull"

  lifecycle {
    ignore_changes = [principal_id, scope]
  }
}

# Keycloak Container App - ACR Pull
resource "azurerm_role_assignment" "keycloak_acr_pull" {
  principal_id         = azurerm_user_assigned_identity.keycloak.principal_id
  scope                = data.azurerm_container_registry.this.id
  role_definition_name = "AcrPull"

  lifecycle {
    ignore_changes = [principal_id, scope]
  }
}
