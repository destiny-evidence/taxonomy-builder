output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.this.name
}

output "api_container_app_fqdn" {
  description = "FQDN of the API container app"
  value       = data.azurerm_container_app.api.ingress[0].fqdn
}

output "keycloak_container_app_fqdn" {
  description = "FQDN of the Keycloak container app"
  value       = azurerm_container_app.keycloak.ingress[0].fqdn
}

output "application_gateway_public_ip" {
  description = "Public IP address of the Application Gateway"
  value       = azurerm_public_ip.gateway.ip_address
}

output "postgresql_server_fqdn" {
  description = "FQDN of the PostgreSQL Flexible Server"
  value       = azurerm_postgresql_flexible_server.this.fqdn
}

output "github_actions_client_id" {
  description = "Client ID for GitHub Actions OIDC"
  value       = azuread_application_registration.github_actions.client_id
}

output "container_registry_login_server" {
  description = "Login server for the container registry"
  value       = data.azurerm_container_registry.this.login_server
}
