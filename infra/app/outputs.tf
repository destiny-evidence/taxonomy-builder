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

output "frontdoor_endpoint_hostname" {
  description = "Hostname of the Front Door endpoint"
  value       = azurerm_cdn_frontdoor_endpoint.this.host_name
}

output "frontdoor_custom_domain_validation_token" {
  description = "DNS TXT record value for custom domain validation (add as _dnsauth.yourdomain)"
  value       = var.custom_domain != null ? azurerm_cdn_frontdoor_custom_domain.this.validation_token : null
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

# Keycloak outputs
output "keycloak_realm_id" {
  description = "ID of the Keycloak realm"
  value       = local.keycloak_realm_id
}

output "keycloak_api_client_id" {
  description = "Client ID for the Taxonomy Builder API"
  value       = keycloak_openid_client.api.client_id
}

output "keycloak_ui_client_id" {
  description = "Client ID for the Taxonomy Builder UI"
  value       = keycloak_openid_client.ui.client_id
}

output "feedback_frontdoor_custom_domain_validation_token" {
  description = "DNS TXT record value for feedback custom domain validation (add as _dnsauth.{feedback_domain})"
  value       = azurerm_cdn_frontdoor_custom_domain.feedback.validation_token
}

output "keycloak_issuer_url" {
  description = "Keycloak issuer URL for OIDC configuration"
  value       = "https://${var.custom_domain}/realms/${var.keycloak_realm_name}"
}
