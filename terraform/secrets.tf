# ─────────────────────────────────────────────────────────────
# Secret Manager — existing secrets
# ─────────────────────────────────────────────────────────────

data "google_secret_manager_secret" "groq_api_key" {
  secret_id = "groq-api-key"
  project   = var.project_id
}

data "google_secret_manager_secret" "groq_fallback_api_key" {
  secret_id = "groq-fallback-api-key"
  project   = var.project_id
}

data "google_secret_manager_secret" "qdrant_api_key" {
  secret_id = "qdrant-api-key"
  project   = var.project_id
}

data "google_secret_manager_secret" "openrouter_api_key" {
  secret_id = "openrouter-api-key"
  project   = var.project_id
}

data "google_secret_manager_secret" "langsmith_api_key" {
  secret_id = "langsmith-api-key"
  project   = var.project_id
}

data "google_secret_manager_secret" "portkey_api_key" {
  secret_id = "portkey-api-key"
  project   = var.project_id
}

data "google_secret_manager_secret" "logfire_token" {
  secret_id = "logfire-token"
  project   = var.project_id
}

data "google_secret_manager_secret" "db_password" {
  secret_id = "db-password"
  project   = var.project_id
}

data "google_secret_manager_secret" "judge_groq_api_key" {
  secret_id = "judge-groq-api-key"
  project   = var.project_id
}


# ─────────────────────────────────────────────────────────────
# Cloud Run service account → Secret Manager access
# ─────────────────────────────────────────────────────────────

locals {
  cloud_run_service_account = "398329761549-compute@developer.gserviceaccount.com"
}

resource "google_secret_manager_secret_iam_member" "cloud_run_secrets" {
  for_each = {
    groq_api_key          = data.google_secret_manager_secret.groq_api_key.id
    groq_fallback_api_key = data.google_secret_manager_secret.groq_fallback_api_key.id
    qdrant_api_key        = data.google_secret_manager_secret.qdrant_api_key.id
    openrouter_api_key    = data.google_secret_manager_secret.openrouter_api_key.id
    langsmith_api_key     = data.google_secret_manager_secret.langsmith_api_key.id
    portkey_api_key       = data.google_secret_manager_secret.portkey_api_key.id
    logfire_token         = data.google_secret_manager_secret.logfire_token.id
    db_password           = data.google_secret_manager_secret.db_password.id
    judge_groq_api_key    = data.google_secret_manager_secret.judge_groq_api_key.id
  }

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.cloud_run_service_account}"
}