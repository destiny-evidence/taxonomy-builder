# Shared container registry
data "azurerm_container_registry" "this" {
  name                = var.container_registry_name
  resource_group_name = var.container_registry_resource_group
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

# Keycloak Container App identity
resource "azurerm_user_assigned_identity" "keycloak" {
  name                = "${local.name}-keycloak"
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
  version                         = "1.8.1-beta"
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
      value = "https://${var.custom_domain}"
    },
    {
      name  = "TAXONOMY_KEYCLOAK_REALM"
      value = "taxonomy-builder"
    },
    {
      name  = "TAXONOMY_KEYCLOAK_CLIENT_ID"
      value = "taxonomy-builder-api"
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
      name  = "TAXONOMY_CDN_SUBSCRIPTION_ID"
      value = data.azurerm_subscription.current.subscription_id
    },
    {
      name  = "TAXONOMY_CDN_RESOURCE_GROUP"
      value = azurerm_resource_group.this.name
    },
    {
      name  = "TAXONOMY_CDN_PROFILE_NAME"
      value = azurerm_cdn_frontdoor_profile.this.name
    },
    {
      name  = "TAXONOMY_CDN_ENDPOINT_NAME"
      value = azurerm_cdn_frontdoor_endpoint.this.name
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

# Keycloak Container App
resource "azurerm_container_app" "keycloak" {
  name                         = "${local.name}-keycloak"
  container_app_environment_id = module.container_app_api.container_app_env_id
  resource_group_name          = azurerm_resource_group.this.name
  revision_mode                = "Single"


  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.keycloak.id]
  }

  template {
    min_replicas = 1
    max_replicas = 1

    container {
      name   = "keycloak"
      image  = "quay.io/keycloak/keycloak:${var.keycloak_image_tag}"
      args   = ["start"]
      cpu    = var.keycloak_cpu
      memory = var.keycloak_memory

      env {
        name  = "KC_DB"
        value = "postgres"
      }
      env {
        name  = "KC_DB_URL"
        value = "jdbc:postgresql://${azurerm_postgresql_flexible_server.this.fqdn}:5432/${local.keycloak_db_name}"
      }
      env {
        name  = "KC_DB_USERNAME"
        value = var.db_admin_login
      }
      env {
        name        = "KC_DB_PASSWORD"
        secret_name = "kc-db-password"
      }
      env {
        name  = "KC_HOSTNAME_STRICT"
        value = "false"
      }
      env {
        name  = "KC_PROXY_HEADERS"
        value = "xforwarded"
      }
      env {
        name  = "KC_HTTP_ENABLED"
        value = "true"
      }
      env {
        name  = "KEYCLOAK_ADMIN"
        value = "admin"
      }
      env {
        name        = "KEYCLOAK_ADMIN_PASSWORD"
        secret_name = "kc-admin-password"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8080
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  secret {
    name  = "kc-db-password"
    value = var.db_admin_password
  }

  secret {
    name  = "kc-admin-password"
    value = var.keycloak_admin_password
  }

  tags = local.minimum_resource_tags
}

# Data source for API Container App (for gateway backend)
data "azurerm_container_app" "api" {
  name                = module.container_app_api.container_app_name
  resource_group_name = azurerm_resource_group.this.name
  depends_on          = [module.container_app_api]
}

