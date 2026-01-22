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
  version                         = "1.7.1"
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
      name = "TAXONOMY_DATABASE_CONFIG"
      value = jsonencode({
        DB_FQDN = azurerm_postgresql_flexible_server.this.fqdn
        DB_NAME = azurerm_postgresql_flexible_server_database.taxonomy.name
        DB_USER = data.azuread_group.db_crud_group.display_name
      })
    },
    {
      name  = "TAXONOMY_KEYCLOAK_URL"
      value = "https://${module.container_app_keycloak.container_app_fqdn}"
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
  ]

  secrets = []

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
module "container_app_keycloak" {
  source                          = "app.terraform.io/destiny-evidence/container-app/azure"
  version                         = "1.7.1"
  app_name                        = "${var.app_name}-keycloak"
  cpu                             = var.keycloak_cpu
  environment                     = var.environment
  container_registry_id           = data.azurerm_container_registry.this.id
  container_registry_login_server = data.azurerm_container_registry.this.login_server
  infrastructure_subnet_id        = azurerm_subnet.keycloak.id
  memory                          = var.keycloak_memory
  resource_group_name             = azurerm_resource_group.this.name
  region                          = azurerm_resource_group.this.location
  min_replicas                    = 1
  max_replicas                    = 1
  tags                            = local.minimum_resource_tags

  # Keycloak uses its own official image, not our ACR
  container_image = "quay.io/keycloak/keycloak:latest"

  identity = {
    id           = azurerm_user_assigned_identity.keycloak.id
    principal_id = azurerm_user_assigned_identity.keycloak.principal_id
    client_id    = azurerm_user_assigned_identity.keycloak.client_id
  }

  command = ["start", "--optimized"]

  env_vars = [
    {
      name  = "KC_DB"
      value = "postgres"
    },
    {
      name  = "KC_DB_URL"
      value = "jdbc:postgresql://${azurerm_postgresql_flexible_server.this.fqdn}:5432/${local.keycloak_db_name}"
    },
    {
      name  = "KC_DB_USERNAME"
      value = var.db_admin_login
    },
    {
      name        = "KC_DB_PASSWORD"
      secret_name = "kc-db-password"
    },
    {
      name  = "KC_HOSTNAME_STRICT"
      value = "false"
    },
    {
      name  = "KC_PROXY_HEADERS"
      value = "xforwarded"
    },
    {
      name  = "KC_HTTP_ENABLED"
      value = "true"
    },
    {
      name  = "KEYCLOAK_ADMIN"
      value = "admin"
    },
    {
      name        = "KEYCLOAK_ADMIN_PASSWORD"
      secret_name = "kc-admin-password"
    },
  ]

  secrets = [
    {
      name  = "kc-db-password"
      value = var.db_admin_password
    },
    {
      name  = "kc-admin-password"
      value = var.keycloak_admin_password
    },
  ]

  ingress = {
    external_enabled           = true
    allow_insecure_connections = false
    target_port                = 8080
    transport                  = "auto"
    traffic_weight = {
      latest_revision = true
      percentage      = 100
    }
  }

  custom_scale_rules = []
}

# Data source for API Container App (for gateway backend)
data "azurerm_container_app" "api" {
  name                = module.container_app_api.container_app_name
  resource_group_name = azurerm_resource_group.this.name
  depends_on          = [module.container_app_api]
}

data "azurerm_container_app" "keycloak" {
  name                = module.container_app_keycloak.container_app_name
  resource_group_name = azurerm_resource_group.this.name
  depends_on          = [module.container_app_keycloak]
}
