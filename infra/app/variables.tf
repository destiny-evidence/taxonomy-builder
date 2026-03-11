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

variable "keycloak_url" {
  description = "Base URL of the shared Keycloak instance"
  type        = string
}

variable "keycloak_realm_name" {
  description = "Name of the Keycloak realm"
  type        = string
  default     = "destiny"
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

variable "github_app_id" {
  description = "GitHub App ID for configuring repository environments"
  type        = string
}

variable "github_app_installation_id" {
  description = "GitHub App installation ID"
  type        = string
}

variable "github_app_pem" {
  description = "GitHub App private key PEM file contents"
  type        = string
  sensitive   = true
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

# Front Door
variable "custom_domain" {
  description = "Base domain (e.g., evidence-repository.org)"
  type        = string
}

variable "builder_subdomain" {
  description = "Subdomain prefix for the builder UI (e.g., taxonomy-beta)"
  type        = string
  default     = "taxonomy-beta"
}

variable "feedback_subdomain" {
  description = "Subdomain prefix for the reader UI (e.g., taxonomy-reader-beta)"
  type        = string
  default     = "taxonomy-reader-beta"
}

variable "cache_feedback_ui_at_edge" {
  description = "Enable Front Door edge caching for the feedback UI (disable for testing)"
  type        = bool
  default     = false
}
