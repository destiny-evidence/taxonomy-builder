# Public IP for Application Gateway
resource "azurerm_public_ip" "gateway" {
  name                = "pip-${local.name}-gateway"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = local.minimum_resource_tags
}

# Application Gateway
resource "azurerm_application_gateway" "this" {
  name                = "agw-${local.name}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location

  sku {
    name     = var.gateway_sku_name
    tier     = var.gateway_sku_tier
    capacity = var.gateway_capacity
  }

  gateway_ip_configuration {
    name      = "gateway-ip-config"
    subnet_id = azurerm_subnet.gateway.id
  }

  # Frontend configuration
  frontend_port {
    name = "http-port"
    port = 80
  }

  frontend_port {
    name = "https-port"
    port = 443
  }

  frontend_ip_configuration {
    name                 = "frontend-ip-config"
    public_ip_address_id = azurerm_public_ip.gateway.id
  }

  # Backend pools
  backend_address_pool {
    name  = "api-backend-pool"
    fqdns = [data.azurerm_container_app.api.ingress[0].fqdn]
  }

  backend_address_pool {
    name  = "frontend-backend-pool"
    fqdns = [azurerm_storage_account.frontend.primary_web_host]
  }

  backend_address_pool {
    name  = "keycloak-backend-pool"
    fqdns = [data.azurerm_container_app.keycloak.ingress[0].fqdn]
  }

  # Backend HTTP settings
  backend_http_settings {
    name                                = "api-http-settings"
    cookie_based_affinity               = "Disabled"
    port                                = 443
    protocol                            = "Https"
    request_timeout                     = 60
    pick_host_name_from_backend_address = true

    probe_name = "api-health-probe"
  }

  backend_http_settings {
    name                                = "frontend-http-settings"
    cookie_based_affinity               = "Disabled"
    port                                = 443
    protocol                            = "Https"
    request_timeout                     = 60
    pick_host_name_from_backend_address = true
  }

  backend_http_settings {
    name                                = "keycloak-http-settings"
    cookie_based_affinity               = "Disabled"
    port                                = 443
    protocol                            = "Https"
    request_timeout                     = 60
    pick_host_name_from_backend_address = true

    probe_name = "keycloak-health-probe"
  }

  # Health probes
  probe {
    name                                      = "api-health-probe"
    protocol                                  = "Https"
    path                                      = "/health"
    interval                                  = 30
    timeout                                   = 30
    unhealthy_threshold                       = 3
    pick_host_name_from_backend_http_settings = true
  }

  probe {
    name                                      = "keycloak-health-probe"
    protocol                                  = "Https"
    path                                      = "/health"
    interval                                  = 30
    timeout                                   = 30
    unhealthy_threshold                       = 3
    pick_host_name_from_backend_http_settings = true
  }

  # HTTP Listener (redirects to HTTPS in production)
  http_listener {
    name                           = "http-listener"
    frontend_ip_configuration_name = "frontend-ip-config"
    frontend_port_name             = "http-port"
    protocol                       = "Http"
  }

  # URL path map for routing /api/* to API backend, everything else to frontend
  url_path_map {
    name                               = "url-path-map"
    default_backend_address_pool_name  = "frontend-backend-pool"
    default_backend_http_settings_name = "frontend-http-settings"

    path_rule {
      name                       = "api-path-rule"
      paths                      = ["/api/*"]
      backend_address_pool_name  = "api-backend-pool"
      backend_http_settings_name = "api-http-settings"
    }

    path_rule {
      name                       = "keycloak-path-rule"
      paths                      = ["/auth/*", "/realms/*"]
      backend_address_pool_name  = "keycloak-backend-pool"
      backend_http_settings_name = "keycloak-http-settings"
    }
  }

  # Request routing rule
  request_routing_rule {
    name               = "main-routing-rule"
    priority           = 100
    rule_type          = "PathBasedRouting"
    http_listener_name = "http-listener"
    url_path_map_name  = "url-path-map"
  }

  tags = local.minimum_resource_tags

  lifecycle {
    # Ignore changes to SSL certificates which may be managed externally
    ignore_changes = [
      ssl_certificate,
      http_listener,
      request_routing_rule,
    ]
  }
}
