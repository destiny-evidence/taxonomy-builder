# Shared container registry
data "azurerm_container_registry" "this" {
  name                = var.shared_container_registry_name
  resource_group_name = var.shared_resource_group_name
}

resource "azurerm_resource_group" "this" {
  name     = "rg-${local.name}"
  location = var.region
  tags     = merge({ "Budget Code" = var.budget_code }, local.minimum_resource_tags)
}

# API Container App identity
resource "azurerm_user_assigned_identity" "api" {
  name                = "${local.name}-api"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  tags                = local.minimum_resource_tags
}

# Add API identity to DB CRUD group for managed identity auth
resource "azuread_group_member" "api_to_db_crud" {
  group_object_id  = var.db_crud_group_id
  member_object_id = azurerm_user_assigned_identity.api.principal_id
}

# API Container App
module "container_app_api" {
  source                          = "app.terraform.io/destiny-evidence/container-app/azure"
  version                         = "1.9.1"
  app_name                        = var.app_name
  cpu                             = var.api_cpu
  environment                     = var.environment
  container_registry_id           = data.azurerm_container_registry.this.id
  container_registry_login_server = data.azurerm_container_registry.this.login_server
  infrastructure_subnet_id        = azurerm_subnet.api.id
  memory                          = var.api_memory
  resource_group_name             = azurerm_resource_group.this.name
  region                          = azurerm_resource_group.this.location
  min_replicas                    = var.api_min_replicas
  max_replicas                    = var.api_max_replicas
  tags                            = local.minimum_resource_tags

  identity = {
    id           = azurerm_user_assigned_identity.api.id
    principal_id = azurerm_user_assigned_identity.api.principal_id
    client_id    = azurerm_user_assigned_identity.api.client_id
  }

  env_vars = [
    {
      name  = "APP_NAME"
      value = var.app_name
    },
    {
      name  = "ENV"
      value = var.environment
    },
    {
      name  = "TAXONOMY_DB_HOST"
      value = azurerm_postgresql_flexible_server.this.fqdn
    },
    {
      name  = "TAXONOMY_DB_NAME"
      value = azurerm_postgresql_flexible_server_database.taxonomy.name
    },
    {
      name  = "TAXONOMY_DB_USER"
      value = var.db_admin_login
    },
    {
      name  = "TAXONOMY_KEYCLOAK_URL"
      value = var.shared_keycloak_url
    },
    {
      name  = "TAXONOMY_KEYCLOAK_REALM"
      value = var.keycloak_realm_name
    },
    {
      name  = "TAXONOMY_KEYCLOAK_CLIENT_ID"
      value = "taxonomy-builder-api-${var.environment}"
    },
    {
      name  = "AZURE_CLIENT_ID"
      value = azurerm_user_assigned_identity.api.client_id
    },
    {
      name  = "TAXONOMY_BLOB_BACKEND"
      value = "azure"
    },
    {
      name  = "TAXONOMY_BLOB_AZURE_ACCOUNT_URL"
      value = "https://${azurerm_storage_account.published.name}.blob.core.windows.net"
    },
    {
      name  = "TAXONOMY_BLOB_AZURE_CONTAINER"
      value = azurerm_storage_container.published.name
    },
    {
      name  = "TAXONOMY_PUBLISHED_BASE_URL"
      value = "https://${local.builder_custom_domain}/${azurerm_storage_container.published.name}"
    },
    {
      name = "TAXONOMY_CDN"
      value = jsonencode({
        subscription_id = data.azurerm_subscription.current.subscription_id
        resource_group  = var.shared_resource_group_name
        profile_name    = data.azurerm_cdn_frontdoor_profile.shared.name
        endpoint_name   = azurerm_cdn_frontdoor_endpoint.this.name
      })
    },
    {
      name        = "TAXONOMY_DB_PASSWORD"
      secret_name = "db-password"
    },
  ]

  secrets = [
    {
      name  = "db-password" # TODO: This should use managed auth.
      value = var.db_admin_password
    },
  ]

  ingress = {
    external_enabled           = true
    allow_insecure_connections = false
    target_port                = 8000
    transport                  = "auto"
    traffic_weight = {
      latest_revision = true
      percentage      = 100
    }
  }

  custom_scale_rules = [
    {
      name             = "cpu-scale-rule"
      custom_rule_type = "cpu"
      metadata = {
        type  = "Utilization"
        value = "70"
      }
    }
  ]
}

