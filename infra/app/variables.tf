variable "app_name" {
  type        = string
  default     = "taxonomy-builder"
  description = "Application name"
}

variable "environment" {
  description = "The environment this stack is being deployed to (development, staging, production)"
  type        = string
}

variable "region" {
  description = "The Azure region resources will be deployed into"
  type        = string
}

# Database
variable "db_admin_login" {
  type        = string
  description = "Admin login for the PostgreSQL database"
}

variable "db_admin_password" {
  type        = string
  description = "Admin password for the PostgreSQL database"
  sensitive   = true
}

variable "db_crud_group_id" {
  type        = string
  description = "ID of the Azure AD group to assign database CRUD access"
}

variable "db_admin_group_id" {
  type        = string
  description = "ID of the Azure AD group to assign database admin access"
}

# Container Registry (shared)
variable "container_registry_name" {
  description = "The name of the shared container registry"
  type        = string
}

variable "container_registry_resource_group" {
  description = "The resource group containing the shared container registry"
  type        = string
}

# Container Apps
variable "api_cpu" {
  description = "CPU allocation for the API container app"
  type        = number
  default     = 0.5
}

variable "api_memory" {
  description = "Memory allocation for the API container app"
  type        = string
  default     = "1Gi"
}

variable "api_min_replicas" {
  description = "Minimum replicas for the API container app"
  type        = number
  default     = 1
}

variable "api_max_replicas" {
  description = "Maximum replicas for the API container app"
  type        = number
  default     = 10
}

variable "keycloak_cpu" {
  description = "CPU allocation for the Keycloak container app"
  type        = number
  default     = 0.5
}

variable "keycloak_memory" {
  description = "Memory allocation for the Keycloak container app"
  type        = string
  default     = "1Gi"
}

variable "keycloak_admin_password" {
  type        = string
  description = "Admin password for Keycloak"
  sensitive   = true
}

variable "keycloak_image_tag" {
  description = "Keycloak container image tag"
  type        = string
  default     = "26"
}

# Azure AD
variable "azure_tenant_id" {
  description = "Azure AD tenant ID"
  type        = string
}

# GitHub Actions
variable "github_repo" {
  type        = string
  default     = "destiny-evidence/taxonomy-builder"
  description = "GitHub repository for Actions OIDC"
}

# Resource tags
variable "budget_code" {
  description = "Budget code for tagging resource groups"
  type        = string
}

variable "created_by" {
  description = "Creator of this infrastructure (for tagging)"
  type        = string
}

variable "owner" {
  description = "Owner email for this infrastructure (for tagging)"
  type        = string
}

variable "project" {
  description = "Project name for tagging"
  type        = string
  default     = "DESTINY"
}

# Application Gateway
variable "gateway_sku_name" {
  description = "SKU name for Application Gateway"
  type        = string
  default     = "Standard_v2"
}

variable "gateway_sku_tier" {
  description = "SKU tier for Application Gateway"
  type        = string
  default     = "Standard_v2"
}

variable "gateway_capacity" {
  description = "Capacity (instance count) for Application Gateway"
  type        = number
  default     = 1
}
