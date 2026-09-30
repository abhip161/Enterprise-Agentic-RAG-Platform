# ──────────────────────────────────────────────
# main.tf — Core Infrastructure
# VPC, GCS Buckets, Redis Memorystore,
# Artifact Registry, API Services, Eventarc SA IAM
# ──────────────────────────────────────────────

data "google_project" "project" {
  project_id = var.project_id
}

# ──────────────────────────────────────────────
# Enable Required GCP APIs
# ──────────────────────────────────────────────

locals {
  required_apis = [
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "documentai.googleapis.com",
    "aiplatform.googleapis.com",
    "compute.googleapis.com",
    "vpcaccess.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "eventarc.googleapis.com",
    "redis.googleapis.com",
    "servicenetworking.googleapis.com",
  ]
}

resource "google_project_service" "services" {
  for_each           = toset(local.required_apis)
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# ──────────────────────────────────────────────
# VPC Network + Subnet
# ──────────────────────────────────────────────

resource "google_compute_network" "vpc" {
  name                    = "${var.app_name}-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.services]
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${var.app_name}-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
}

# Private services access for Cloud SQL + Redis
resource "google_compute_global_address" "private_ip_range" {
  name          = "${var.app_name}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
  depends_on              = [google_project_service.services]
}

# ──────────────────────────────────────────────
# GCS Buckets — Raw + Processed
# ──────────────────────────────────────────────

resource "google_storage_bucket" "raw" {
  name                        = "${var.project_id}-rag-raw"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
  depends_on                  = [google_project_service.services]
}

resource "google_storage_bucket" "processed" {
  name                        = "${var.project_id}-rag-processed"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
  depends_on                  = [google_project_service.services]
}

# ──────────────────────────────────────────────
# Redis Memorystore — Semantic Cache
# ──────────────────────────────────────────────

resource "google_redis_instance" "cache" {
  name               = "${var.app_name}-cache"
  tier               = "BASIC"
  memory_size_gb     = 1
  region             = var.region
  authorized_network = google_compute_network.vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  redis_version = "REDIS_7_0"
  display_name  = "RAG Semantic Cache"

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# ──────────────────────────────────────────────
# Artifact Registry — Docker Image Repository
# ──────────────────────────────────────────────

resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "${var.app_name}-repo"
  description   = "Docker images for Enterprise RAG microservices"
  format        = "DOCKER"
  depends_on    = [google_project_service.services]
}

# ──────────────────────────────────────────────
# Eventarc Service Agent
# ──────────────────────────────────────────────

# Explicitly create/get the Google-managed Eventarc service identity.
resource "google_project_service_identity" "eventarc" {
  project    = var.project_id
  service    = "eventarc.googleapis.com"
  depends_on = [google_project_service.services]
}

resource "google_project_iam_member" "eventarc_service_agent" {
  project = var.project_id
  role    = "roles/eventarc.serviceAgent"
  member  = google_project_service_identity.eventarc.member

  depends_on = [
    google_project_service_identity.eventarc
  ]
}

# GCS service agent needs Pub/Sub publisher to emit object events
resource "google_project_iam_member" "gcs_pubsub_publisher" {
  project    = var.project_id
  role       = "roles/pubsub.publisher"
  member     = "serviceAccount:service-${data.google_project.project.number}@gs-project-accounts.iam.gserviceaccount.com"
  depends_on = [google_project_service.services]
}
