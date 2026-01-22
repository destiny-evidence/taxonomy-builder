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
  }
}

provider "azurerm" {
  features {}
}

provider "azuread" {
}
