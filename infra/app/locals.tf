locals {
  name             = "${var.app_name}-${var.environment}"
  name_short       = "${replace(var.app_name, "-", "")}${substr(var.environment, 0, 4)}"
  is_production    = var.environment == "production"
  is_development   = var.environment != "production" && var.environment != "staging"
  db_migrator_name = "db-migrator-${var.environment}"


  minimum_resource_tags = {
    "Created by"  = var.created_by
    "Environment" = var.environment
    "Owner"       = var.owner
    "Project"     = var.project
    "Region"      = var.region
  }
}
