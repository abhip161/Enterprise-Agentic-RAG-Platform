# ──────────────────────────────────────────────
# output.tf — Print service URLs after terraform apply
# ──────────────────────────────────────────────

output "backend_url" {
  description = "Backend API URL"
  value       = google_cloud_run_v2_service.backend.uri
}

output "ui_url" {
  description = "Streamlit Chat UI URL"
  value       = google_cloud_run_v2_service.ui.uri
}

output "ingestion_url" {
  description = "Ingestion Service URL (internal only)"
  value       = google_cloud_run_v2_service.ingestion.uri
}

output "evals_url" {
  description = "Evals Dashboard URL"
  value       = google_cloud_run_v2_service.evals.uri
}

output "redis_host" {
  description = "Redis Memorystore private IP"
  value       = google_redis_instance.cache.host
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL connection name for Auth Proxy"
  value       = google_sql_database_instance.postgres.connection_name
}
