# ──────────────────────────────────────────────
# ingestion.tf — Eventarc Trigger + Ingestion SA IAM
# ──────────────────────────────────────────────

# Service account for the ingestion service
resource "google_service_account" "ingestion_sa" {
  account_id   = "${var.app_name}-ingestion-sa"
  display_name = "Ingestion Service Account"
}

# Ingestion SA can receive Eventarc events
resource "google_project_iam_member" "ingestion_event_receiver" {
  project = var.project_id
  role    = "roles/eventarc.eventReceiver"
  member  = "serviceAccount:${google_service_account.ingestion_sa.email}"
}

# Ingestion SA can read from RAW and write to PROCESSED buckets
resource "google_project_iam_member" "ingestion_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.ingestion_sa.email}"
}

# Ingestion SA can invoke Cloud Run services
resource "google_project_iam_member" "ingestion_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.ingestion_sa.email}"
}

# Ingestion SA can call Vertex AI (embeddings) and Document AI
resource "google_project_iam_member" "ingestion_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.ingestion_sa.email}"
}

resource "google_project_iam_member" "ingestion_documentai" {
  project = var.project_id
  role    = "roles/documentai.apiUser"
  member  = "serviceAccount:${google_service_account.ingestion_sa.email}"
}

# ──────────────────────────────────────────────
# Eventarc Trigger — GCS object.finalized → /ingest
# ──────────────────────────────────────────────

resource "google_eventarc_trigger" "gcs_to_ingestion" {
  name     = "${var.app_name}-gcs-trigger"
  location = var.region

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }

  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.raw.name
  }

  destination {
    cloud_run_service {
      service = google_cloud_run_v2_service.ingestion.name
      path    = "/ingest"
      region  = var.region
    }
  }

  service_account = google_service_account.ingestion_sa.email

  depends_on = [
    google_project_iam_member.eventarc_service_agent,
    google_project_iam_member.gcs_pubsub_publisher,
    google_project_iam_member.ingestion_event_receiver,
    google_project_iam_member.ingestion_run_invoker,
  ]
}
