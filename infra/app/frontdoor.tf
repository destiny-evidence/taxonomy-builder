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

resource "azurerm_cdn_frontdoor_origin_group" "published" {
  name                     = "published-origin-group"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id

  load_balancing {
    sample_size                 = 4
    successful_samples_required = 3
  }
}

resource "azurerm_cdn_frontdoor_origin_group" "feedback" {
  name                     = "feedback-origin-group"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id

  load_balancing {
    sample_size                 = 4
    successful_samples_required = 3
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

resource "azurerm_cdn_frontdoor_origin" "published" {
  name                          = "published-origin"
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.published.id

  enabled                        = true
  host_name                      = azurerm_storage_account.published.primary_blob_host
  http_port                      = 80
  https_port                     = 443
  origin_host_header             = azurerm_storage_account.published.primary_blob_host
  certificate_name_check_enabled = true
}

resource "azurerm_cdn_frontdoor_origin" "feedback" {
  name                          = "feedback-origin"
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.feedback.id

  enabled                        = true
  host_name                      = azurerm_storage_account.feedback.primary_web_host
  http_port                      = 80
  https_port                     = 443
  origin_host_header             = azurerm_storage_account.feedback.primary_web_host
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

resource "azurerm_cdn_frontdoor_route" "published" {
  name                          = "published-route"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.this.id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.published.id
  cdn_frontdoor_origin_ids      = [azurerm_cdn_frontdoor_origin.published.id]

  supported_protocols    = ["Http", "Https"]
  patterns_to_match      = ["/${azurerm_storage_container.published.name}/*"]
  forwarding_protocol    = "HttpsOnly"
  link_to_default_domain = true
  https_redirect_enabled = true

  cdn_frontdoor_custom_domain_ids = [azurerm_cdn_frontdoor_custom_domain.this.id]
  cdn_frontdoor_rule_set_ids      = [azurerm_cdn_frontdoor_rule_set.published_cache.id]

  cache {
    query_string_caching_behavior = "IgnoreQueryString"
    compression_enabled           = true
    content_types_to_compress     = ["application/json"]
  }
}

# Cache rule set for published content — CDN caches aggressively, purged on publish
resource "azurerm_cdn_frontdoor_rule_set" "published_cache" {
  name                     = "publishedcache"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id
}

resource "azurerm_cdn_frontdoor_rule" "cache_published" {
  name                      = "CachePublished"
  cdn_frontdoor_rule_set_id = azurerm_cdn_frontdoor_rule_set.published_cache.id
  order                     = 1

  actions {
    route_configuration_override_action {
      cache_behavior                = "OverrideAlways"
      cache_duration                = "365.00:00:00"
      compression_enabled           = true
      query_string_caching_behavior = "IgnoreQueryString"
    }
    response_header_action {
      header_action = "Overwrite"
      header_name   = "Cache-Control"
      # Browser caches content but checks with FrontDoor each time.
      # In the future we may consider a TTL here for local caching.
      value = "no-cache"
    }
  }
}

# --- Feedback UI (subdomain) ---

# Custom domain for feedback UI
resource "azurerm_cdn_frontdoor_custom_domain" "feedback" {
  name                     = replace(local.feedback_custom_domain, ".", "-")
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id
  host_name                = local.feedback_custom_domain

  tls {
    certificate_type    = "ManagedCertificate"
    minimum_tls_version = "TLS12"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Feedback UI SPA — catch-all route on the feedback subdomain
resource "azurerm_cdn_frontdoor_route" "feedback" {
  name                          = "feedback-route"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.this.id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.feedback.id
  cdn_frontdoor_origin_ids      = [azurerm_cdn_frontdoor_origin.feedback.id]

  supported_protocols    = ["Http", "Https"]
  patterns_to_match      = ["/*"]
  forwarding_protocol    = "HttpsOnly"
  link_to_default_domain = false
  https_redirect_enabled = true

  cdn_frontdoor_custom_domain_ids = [azurerm_cdn_frontdoor_custom_domain.feedback.id]
  cdn_frontdoor_rule_set_ids      = var.cache_feedback_ui_at_edge ? [azurerm_cdn_frontdoor_rule_set.feedback_cache.id] : []

  dynamic "cache" {
    for_each = var.cache_feedback_ui_at_edge ? [1] : []
    content {
      query_string_caching_behavior = "IgnoreQueryString"
      compression_enabled           = true
      content_types_to_compress     = ["text/html", "application/javascript", "text/css", "application/json"]
    }
  }
}

# API proxy on the feedback subdomain — avoids CORS by keeping requests same-origin
resource "azurerm_cdn_frontdoor_route" "feedback_api" {
  name                          = "feedback-api-route"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.this.id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.api.id
  cdn_frontdoor_origin_ids      = [azurerm_cdn_frontdoor_origin.api.id]

  supported_protocols    = ["Http", "Https"]
  patterns_to_match      = ["/api/*"]
  forwarding_protocol    = "HttpsOnly"
  link_to_default_domain = false
  https_redirect_enabled = true

  cdn_frontdoor_custom_domain_ids = [azurerm_cdn_frontdoor_custom_domain.feedback.id]
}

# Published data on the feedback subdomain
resource "azurerm_cdn_frontdoor_route" "feedback_published" {
  name                          = "feedback-published-route"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.this.id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.published.id
  cdn_frontdoor_origin_ids      = [azurerm_cdn_frontdoor_origin.published.id]

  supported_protocols    = ["Http", "Https"]
  patterns_to_match      = ["/${azurerm_storage_container.published.name}/*"]
  forwarding_protocol    = "HttpsOnly"
  link_to_default_domain = false
  https_redirect_enabled = true

  cdn_frontdoor_custom_domain_ids = [azurerm_cdn_frontdoor_custom_domain.feedback.id]
  cdn_frontdoor_rule_set_ids      = [azurerm_cdn_frontdoor_rule_set.published_cache.id]

  cache {
    query_string_caching_behavior = "IgnoreQueryString"
    compression_enabled           = true
    content_types_to_compress     = ["application/json"]
  }
}

resource "azurerm_cdn_frontdoor_custom_domain_association" "feedback" {
  cdn_frontdoor_custom_domain_id = azurerm_cdn_frontdoor_custom_domain.feedback.id
  cdn_frontdoor_route_ids = [
    azurerm_cdn_frontdoor_route.feedback.id,
    azurerm_cdn_frontdoor_route.feedback_api.id,
    azurerm_cdn_frontdoor_route.feedback_published.id,
  ]

  lifecycle {
    create_before_destroy = true
  }
}

# Cache rule set for feedback UI static assets — purged on deploy
resource "azurerm_cdn_frontdoor_rule_set" "feedback_cache" {
  name                     = "feedbackcache"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id
}

# Service worker must always revalidate (browsers cap at 24h, but CDN must not cache it)
resource "azurerm_cdn_frontdoor_rule" "feedback_sw_no_cache" {
  name                      = "FeedbackSwNoCache"
  cdn_frontdoor_rule_set_id = azurerm_cdn_frontdoor_rule_set.feedback_cache.id
  order                     = 1
  behavior_on_match         = "Stop"

  conditions {
    url_path_condition {
      operator     = "Equal"
      match_values = ["/sw.js"]
    }
  }

  actions {
    response_header_action {
      header_action = "Overwrite"
      header_name   = "Cache-Control"
      value         = "no-cache"
    }
  }
}

# Cache hashed static assets aggressively (JS, CSS, fonts, images)
resource "azurerm_cdn_frontdoor_rule" "feedback_cache_assets" {
  name                      = "FeedbackCacheAssets"
  cdn_frontdoor_rule_set_id = azurerm_cdn_frontdoor_rule_set.feedback_cache.id
  order                     = 2
  behavior_on_match         = "Stop"

  conditions {
    url_file_extension_condition {
      operator     = "Equal"
      match_values = ["js", "css", "woff", "woff2", "png", "jpg", "svg", "ico"]
    }
  }

  actions {
    route_configuration_override_action {
      cache_behavior                = "OverrideAlways"
      cache_duration                = "30.00:00:00"
      compression_enabled           = true
      query_string_caching_behavior = "IgnoreQueryString"
    }
    response_header_action {
      header_action = "Overwrite"
      header_name   = "Cache-Control"
      value         = "public, max-age=2592000, immutable"
    }
  }
}

# HTML files: browser revalidates with Front Door each time
resource "azurerm_cdn_frontdoor_rule" "feedback_html_no_cache" {
  name                      = "FeedbackHtmlNoCache"
  cdn_frontdoor_rule_set_id = azurerm_cdn_frontdoor_rule_set.feedback_cache.id
  order                     = 3
  behavior_on_match         = "Stop"

  conditions {
    url_file_extension_condition {
      operator     = "Equal"
      match_values = ["html"]
    }
  }

  actions {
    response_header_action {
      header_action = "Overwrite"
      header_name   = "Cache-Control"
      value         = "no-cache"
    }
  }
}

# Catch-all: everything not matched above revalidates on every request
resource "azurerm_cdn_frontdoor_rule" "feedback_default_no_cache" {
  name                      = "FeedbackDefaultNoCache"
  cdn_frontdoor_rule_set_id = azurerm_cdn_frontdoor_rule_set.feedback_cache.id
  order                     = 4

  actions {
    response_header_action {
      header_action = "Overwrite"
      header_name   = "Cache-Control"
      value         = "no-cache"
    }
  }
}

# API identity needs permission to purge cached content on publish
# Role "CDN Front Door Purge" is created manually at the subscription level
data "azurerm_role_definition" "cdn_purge" {
  name  = "CDN Front Door Purge"
  scope = data.azurerm_subscription.current.id
}

resource "azurerm_role_assignment" "api_cdn_purger" {
  role_definition_id = data.azurerm_role_definition.cdn_purge.role_definition_id
  scope              = azurerm_cdn_frontdoor_profile.this.id
  principal_id       = azurerm_user_assigned_identity.api.principal_id
}

# GitHub Actions needs permission to purge feedback UI cache on deploy
resource "azurerm_role_assignment" "gha_cdn_purger" {
  role_definition_id = data.azurerm_role_definition.cdn_purge.role_definition_id
  scope              = azurerm_cdn_frontdoor_profile.this.id
  principal_id       = azuread_service_principal.github_actions.object_id
}

resource "azurerm_cdn_frontdoor_route" "keycloak" {
  name                          = "keycloak-route"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.this.id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.keycloak.id
  cdn_frontdoor_origin_ids      = [azurerm_cdn_frontdoor_origin.keycloak.id]

  supported_protocols    = ["Http", "Https"]
  patterns_to_match      = ["/auth/*", "/realms/*", "/resources/*", "/.well-known/*"]
  forwarding_protocol    = "HttpsOnly"
  link_to_default_domain = true
  https_redirect_enabled = true

  cdn_frontdoor_custom_domain_ids = [azurerm_cdn_frontdoor_custom_domain.this.id]
}

# Custom domain
resource "azurerm_cdn_frontdoor_custom_domain" "this" {
  name                     = replace(local.builder_custom_domain, ".", "-")
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id
  host_name                = local.builder_custom_domain

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
    azurerm_cdn_frontdoor_route.published.id,
    azurerm_cdn_frontdoor_route.keycloak.id,
  ]
}
