terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Configure Google Provider
provider "google" {
  project      = var.project_id
  region       = var.region
  access_token = var.access_token
}

# Enable required APIs
resource "google_project_service" "cloudrun" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifactregistry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudbuild" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

locals {
  image_name = "${var.region}-docker.pkg.dev/${var.project_id}/${var.service_name}/${var.service_name}:${var.docker_image_tag}"
}

# Create Artifact Registry repository
resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = var.service_name
  format        = "DOCKER"
  description   = "Docker repository for ${var.service_name}"
}

# Build and push Docker image natively
resource "terraform_data" "docker_build_and_push" {
  triggers_replace = [
    var.docker_image_tag,
    filesha1("${path.module}/../../Dockerfile")
  ]

  provisioner "local-exec" {
    command = "docker build --platform linux/amd64 -t ${local.image_name} ../.. && gcloud auth configure-docker ${var.region}-docker.pkg.dev --quiet && docker push ${local.image_name}"
  }

  depends_on = [
    google_artifact_registry_repository.app,
    google_project_service.cloudbuild
  ]
}

# Deploy to Cloud Run
resource "google_cloud_run_service" "app" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      containers {
        image = local.image_name

        resources {
          limits = {
            cpu    = "1"
            memory = "2Gi" # 2GB required for Semgrep MCP server
          }
        }

        env {
          name  = "OPENAI_API_KEY"
          value = var.openai_api_key
        }

        env {
          name  = "GEMINI_API_KEY"
          value = var.gemini_api_key
        }

        env {
          name  = "GEMINI_MODEL"
          value = var.gemini_model
        }

        env {
          name  = "SEMGREP_APP_TOKEN"
          value = var.semgrep_app_token
        }

        env {
          name  = "ENVIRONMENT"
          value = "production"
        }

        env {
          name  = "PYTHONUNBUFFERED"
          value = "1"
        }

        ports {
          container_port = 8000
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"
        "autoscaling.knative.dev/maxScale" = "1"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.cloudrun,
    terraform_data.docker_build_and_push
  ]
}

# Make the service publicly accessible
resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_service.app.name
  location = google_cloud_run_service.app.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "service_url" {
  value       = google_cloud_run_service.app.status[0].url
  description = "URL of the deployed Cloud Run service"
}

output "project_id" {
  value       = var.project_id
  description = "GCP Project ID"
}

output "region" {
  value       = var.region
  description = "GCP region"
}
