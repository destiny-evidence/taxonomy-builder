# Azure Front Door for routing and custom domain

resource "azurerm_cdn_frontdoor_profile" "this" {
  name                = "fd-${local.name}"
  resource_group_name = azurerm_resource_group.this.name
  sku_name            = "Standard_AzureFrontDoor"

  tags = local.minimum_resource_tags
}

resource "azurerm_cdn_frontdoor_endpoint" "this" {
  name                     = "fde-${local.name}"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id

  tags = local.minimum_resource_tags
}

# Origin groups
resource "azurerm_cdn_frontdoor_origin_group" "frontend" {
  name                     = "frontend-origin-group"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id

  load_balancing {
    sample_size                 = 4
    successful_samples_required = 3
  }
}

resource "azurerm_cdn_frontdoor_origin_group" "api" {
  name                     = "api-origin-group"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id

  load_balancing {
    sample_size                 = 4
    successful_samples_required = 3
  }

  health_probe {
    path                = "/health"
    protocol            = "Https"
    interval_in_seconds = 30
  }
}

resource "azurerm_cdn_frontdoor_origin_group" "keycloak" {
  name                     = "keycloak-origin-group"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id

  load_balancing {
    sample_size                 = 4
    successful_samples_required = 3
  }

  health_probe {
    path                = "/health"
    protocol            = "Https"
    interval_in_seconds = 30
  }
}

# Origins
resource "azurerm_cdn_frontdoor_origin" "frontend" {
  name                          = "frontend-origin"
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.frontend.id

  enabled                        = true
  host_name                      = azurerm_storage_account.frontend.primary_web_host
  http_port                      = 80
  https_port                     = 443
  origin_host_header             = azurerm_storage_account.frontend.primary_web_host
  certificate_name_check_enabled = true
}

resource "azurerm_cdn_frontdoor_origin" "api" {
  name                          = "api-origin"
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.api.id

  enabled                        = true
  host_name                      = data.azurerm_container_app.api.ingress[0].fqdn
  http_port                      = 80
  https_port                     = 443
  origin_host_header             = data.azurerm_container_app.api.ingress[0].fqdn
  certificate_name_check_enabled = true
}

resource "azurerm_cdn_frontdoor_origin" "keycloak" {
  name                          = "keycloak-origin"
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.keycloak.id

  enabled                        = true
  host_name                      = azurerm_container_app.keycloak.ingress[0].fqdn
  http_port                      = 80
  https_port                     = 443
  origin_host_header             = azurerm_container_app.keycloak.ingress[0].fqdn
  certificate_name_check_enabled = true
}

# Routes
resource "azurerm_cdn_frontdoor_route" "frontend" {
  name                          = "frontend-route"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.this.id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.frontend.id
  cdn_frontdoor_origin_ids      = [azurerm_cdn_frontdoor_origin.frontend.id]

  supported_protocols    = ["Http", "Https"]
  patterns_to_match      = ["/*"]
  forwarding_protocol    = "HttpsOnly"
  link_to_default_domain = true
  https_redirect_enabled = true

  cdn_frontdoor_custom_domain_ids = [azurerm_cdn_frontdoor_custom_domain.this.id]
}

resource "azurerm_cdn_frontdoor_route" "api" {
  name                          = "api-route"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.this.id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.api.id
  cdn_frontdoor_origin_ids      = [azurerm_cdn_frontdoor_origin.api.id]

  supported_protocols    = ["Http", "Https"]
  patterns_to_match      = ["/api/*"]
  forwarding_protocol    = "HttpsOnly"
  link_to_default_domain = true
  https_redirect_enabled = true

  cdn_frontdoor_custom_domain_ids = [azurerm_cdn_frontdoor_custom_domain.this.id]
}

resource "azurerm_cdn_frontdoor_route" "keycloak" {
  name                          = "keycloak-route"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.this.id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.keycloak.id
  cdn_frontdoor_origin_ids      = [azurerm_cdn_frontdoor_origin.keycloak.id]

  supported_protocols    = ["Http", "Https"]
  patterns_to_match      = ["/auth/*", "/realms/*"]
  forwarding_protocol    = "HttpsOnly"
  link_to_default_domain = true
  https_redirect_enabled = true

  cdn_frontdoor_custom_domain_ids = [azurerm_cdn_frontdoor_custom_domain.this.id]
}

# Custom domain
resource "azurerm_cdn_frontdoor_custom_domain" "this" {
  name                     = replace(var.custom_domain, ".", "-")
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id
  host_name                = var.custom_domain

  tls {
    certificate_type    = "ManagedCertificate"
    minimum_tls_version = "TLS12"
  }
}

resource "azurerm_cdn_frontdoor_custom_domain_association" "this" {
  cdn_frontdoor_custom_domain_id = azurerm_cdn_frontdoor_custom_domain.this.id
  cdn_frontdoor_route_ids = [
    azurerm_cdn_frontdoor_route.frontend.id,
    azurerm_cdn_frontdoor_route.api.id,
    azurerm_cdn_frontdoor_route.keycloak.id,
  ]
}
