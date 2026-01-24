locals {
  prod_db_storage_mb   = 131072
  dev_db_storage_mb    = 32768
  prod_db_storage_tier = "P10"
  dev_db_storage_tier  = "P4"
}

data "azuread_group" "db_crud_group" {
  object_id = var.db_crud_group_id
}

data "azuread_group" "db_admin_group" {
  object_id = var.db_admin_group_id
}

# PostgreSQL Flexible Server (shared by taxonomy-builder and Keycloak)
resource "azurerm_postgresql_flexible_server" "this" {
  name                          = "${local.name}-psqlflexibleserver"
  resource_group_name           = azurerm_resource_group.this.name
  location                      = azurerm_resource_group.this.location
  version                       = "16"
  delegated_subnet_id           = azurerm_subnet.db.id
  private_dns_zone_id           = azurerm_private_dns_zone.db.id
  public_network_access_enabled = false
  administrator_login           = var.db_admin_login
  administrator_password        = var.db_admin_password
  zone                          = "1"
  backup_retention_days         = local.is_production ? 35 : 7

  dynamic "high_availability" {
    for_each = local.is_production ? [1] : []
    content {
      mode = "ZoneRedundant"
    }
  }

  storage_mb   = local.is_development ? local.dev_db_storage_mb : local.prod_db_storage_mb
  storage_tier = local.is_development ? local.dev_db_storage_tier : local.prod_db_storage_tier

  sku_name = local.is_development ? "B_Standard_B1ms" : "GP_Standard_D2ds_v4"

  authentication {
    password_auth_enabled         = true
    active_directory_auth_enabled = true
    tenant_id                     = var.azure_tenant_id
  }

  depends_on = [azurerm_private_dns_zone_virtual_network_link.db]
  tags       = local.minimum_resource_tags

  lifecycle {
    ignore_changes = [
      zone,
      high_availability[0].standby_availability_zone
    ]
  }
}

# Taxonomy Builder database
resource "azurerm_postgresql_flexible_server_database" "taxonomy" {
  name      = local.taxonomy_db_name
  server_id = azurerm_postgresql_flexible_server.this.id
  collation = "en_US.utf8"
  charset   = "UTF8"

  lifecycle {
    prevent_destroy = true
  }
}

# Keycloak database
resource "azurerm_postgresql_flexible_server_database" "keycloak" {
  name      = local.keycloak_db_name
  server_id = azurerm_postgresql_flexible_server.this.id
  collation = "en_US.utf8"
  charset   = "UTF8"

  lifecycle {
    prevent_destroy = true
  }
}

# Database admin identity
resource "azurerm_user_assigned_identity" "db_admin" {
  location            = azurerm_resource_group.this.location
  name                = data.azuread_group.db_admin_group.display_name
  resource_group_name = azurerm_resource_group.this.name
  tags                = local.minimum_resource_tags
}

resource "azurerm_postgresql_flexible_server_active_directory_administrator" "admin" {
  server_name         = azurerm_postgresql_flexible_server.this.name
  resource_group_name = azurerm_resource_group.this.name
  tenant_id           = var.azure_tenant_id
  object_id           = var.db_admin_group_id
  principal_name      = data.azuread_group.db_admin_group.display_name
  principal_type      = "Group"
}

# Database migrator identity
resource "azurerm_user_assigned_identity" "db_migrator" {
  name                = "${var.app_name}-${local.db_migrator_name}"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  tags                = local.minimum_resource_tags
}

resource "azurerm_role_assignment" "db_migrator_acr_access" {
  principal_id         = azurerm_user_assigned_identity.db_migrator.principal_id
  scope                = data.azurerm_container_registry.this.id
  role_definition_name = "AcrPull"

  lifecycle {
    ignore_changes = [principal_id, scope]
  }
}

# Database migrator Container App Job
resource "azurerm_container_app_job" "db_migrator" {
  name                         = local.db_migrator_name
  location                     = azurerm_resource_group.this.location
  resource_group_name          = azurerm_resource_group.this.name
  container_app_environment_id = module.container_app_api.container_app_env_id

  replica_timeout_in_seconds = 1800 # 30 minutes
  replica_retry_limit        = 0

  manual_trigger_config {
    parallelism              = 1
    replica_completion_count = 1
  }

  registry {
    identity = azurerm_user_assigned_identity.db_migrator.id
    server   = data.azurerm_container_registry.this.login_server
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.db_migrator.id]
  }

  secret {
    name  = "db-password"
    value = var.db_admin_password
  }

  template {
    container {
      # Placeholder image - updated by GitHub Actions
      image   = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
      name    = "${local.db_migrator_name}0"
      command = ["alembic", "upgrade", "head"]

      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "APP_NAME"
        value = local.db_migrator_name
      }

      env {
        name  = "ENV"
        value = var.environment
      }

      env {
        name  = "TAXONOMY_DB_HOST"
        value = azurerm_postgresql_flexible_server.this.fqdn
      }

      env {
        name  = "TAXONOMY_DB_NAME"
        value = azurerm_postgresql_flexible_server_database.taxonomy.name
      }

      env {
        name  = "TAXONOMY_DB_USER"
        value = var.db_admin_login
      }

      env {
        name        = "TAXONOMY_DB_PASSWORD"
        secret_name = "db-password"
      }
    }
  }

  tags = local.minimum_resource_tags

  lifecycle {
    ignore_changes = [template[0].container[0].image]
  }
}
