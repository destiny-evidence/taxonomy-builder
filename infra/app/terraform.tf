terraform {
  required_version = ">= 1.0"

  cloud {
    organization = "destiny-evidence"

    workspaces {
      project = "DESTINY"
      tags    = ["taxonomy-builder"]
    }
  }

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.26"
    }

    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.1"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.7"
    }

    github = {
      source  = "integrations/github"
      version = "~> 6.6"
    }

    keycloak = {
      source  = "keycloak/keycloak"
      version = "~> 5.0"
    }
  }
}

provider "azurerm" {
  features {}
}

provider "azuread" {
}

provider "github" {
  owner = "destiny-evidence"
  app_auth {
    id              = var.github_app_id
    installation_id = var.github_app_installation_id
    pem_file        = var.github_app_pem
  }
}

provider "keycloak" {
  client_id = "admin-cli"
  username  = "admin"
  password  = var.keycloak_admin_password
  url       = "https://${var.custom_domain}"
}
