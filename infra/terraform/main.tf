terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "datalake" {
  name          = "${var.project_id}-autolavado-lake"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
}

resource "google_pubsub_topic" "ingesta_topic" {
  name = "ingesta-ventas-topic"
}

resource "google_service_account" "worker_sa" {
  account_id   = "worker-limpieza-sa"
  display_name = "Service Account Worker Limpieza (Mínimo Privilegio)"
}

resource "google_storage_bucket_iam_member" "worker_bucket_perm" {
  bucket = google_storage_bucket.datalake.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.worker_sa.email}"
}
