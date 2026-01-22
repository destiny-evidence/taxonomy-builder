# Storage account for frontend static files
resource "azurerm_storage_account" "frontend" {
  # Storage account name must be 3-24 chars, lowercase letters and numbers only
  name                     = "${local.name_short}fe"
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  # Enable static website hosting
  static_website {
    index_document     = "index.html"
    error_404_document = "index.html" # SPA routing - serve index.html for all routes
  }

  # Allow blob public access for static website
  allow_nested_items_to_be_public = true

  tags = local.minimum_resource_tags
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
