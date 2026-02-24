# Storage account for frontend static files
resource "azurerm_storage_account" "frontend" {
  # Storage account name must be 3-24 chars, lowercase letters and numbers only
  name                     = "${local.name_short}fe"
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  # Allow blob public access for static website
  allow_nested_items_to_be_public = true

  tags = local.minimum_resource_tags
}

resource "azurerm_storage_account_static_website" "frontend" {
  storage_account_id = azurerm_storage_account.frontend.id
  error_404_document = "index.html"
  index_document     = "index.html"
}

# Output the static website endpoint for Application Gateway backend
output "frontend_static_website_url" {
  description = "Primary endpoint for the static website"
  value       = azurerm_storage_account.frontend.primary_web_endpoint
}

output "frontend_static_website_host" {
  description = "Host for the static website (without protocol)"
  value       = azurerm_storage_account.frontend.primary_web_host
}

# Storage account for feedback UI static files
resource "azurerm_storage_account" "feedback" {
  name                     = "${local.name_short}fb"
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  allow_nested_items_to_be_public = true

  tags = local.minimum_resource_tags
}

resource "azurerm_storage_account_static_website" "feedback" {
  storage_account_id = azurerm_storage_account.feedback.id
  error_404_document = "index.html"
  index_document     = "index.html"
}

# Storage account for published taxonomy documents (served via Front Door)
resource "azurerm_storage_account" "published" {
  name                     = "${local.name_short}pub"
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  allow_nested_items_to_be_public = true

  tags = local.minimum_resource_tags
}

resource "azurerm_storage_container" "published" {
  name                  = "published"
  storage_account_id    = azurerm_storage_account.published.id
  container_access_type = "blob"
}

# API identity needs write access to publish snapshots
resource "azurerm_role_assignment" "api_blob_contributor" {
  role_definition_name = "Storage Blob Data Contributor"
  scope                = azurerm_storage_account.published.id
  principal_id         = azurerm_user_assigned_identity.api.principal_id
}
