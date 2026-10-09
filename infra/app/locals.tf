locals {
  name             = "${var.app_name}-${var.environment}"
  name_short       = "${replace(var.app_name, "-", "")}${substr(var.environment, 0, 4)}"
  is_production    = var.environment == "production"
  is_development   = var.environment != "production" && var.environment != "staging"
  db_migrator_name        = "db-migrator-${var.environment}"
  builder_custom_domain   = "${var.builder_subdomain}.${var.custom_domain}"
  feedback_custom_domain  = "${var.feedback_subdomain}.${var.custom_domain}"

  # Only the attributes both endpoint types share, so the conditional types match
  frontdoor_endpoint = local.is_production ? {
    id        = azurerm_cdn_frontdoor_endpoint.this[0].id
    name      = azurerm_cdn_frontdoor_endpoint.this[0].name
    host_name = azurerm_cdn_frontdoor_endpoint.this[0].host_name
    } : {
    id        = data.azurerm_cdn_frontdoor_endpoint.shared[0].id
    name      = data.azurerm_cdn_frontdoor_endpoint.shared[0].name
    host_name = data.azurerm_cdn_frontdoor_endpoint.shared[0].host_name
  }

  minimum_resource_tags = {
    "Created by"  = var.created_by
    "Environment" = var.environment
    "Owner"       = var.owner
    "Project"     = var.project
    "Region"      = var.region
  }
}
