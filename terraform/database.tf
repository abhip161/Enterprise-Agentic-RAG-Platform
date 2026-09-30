# ──────────────────────────────────────────────
# database.tf — Cloud SQL Postgres 15
# ──────────────────────────────────────────────

resource "google_sql_database_instance" "postgres" {
  name             = "${var.app_name}-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"

    ip_configuration {
      # Public IP exists (required by Cloud SQL Auth Proxy) but no authorized
      # networks are whitelisted — no direct TCP access is possible.
      ipv4_enabled    = true
      private_network = google_compute_network.vpc.id
    }

    backup_configuration {
      enabled = true
    }
  }

  deletion_protection = false
  depends_on          = [google_service_networking_connection.private_vpc_connection]
}

resource "google_sql_database" "rag_db" {
  name     = "enterprise_rag"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "rag_admin" {
  name     = "rag_admin"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# Grant the default compute SA Cloud SQL Client role for Cloud Run
resource "google_project_iam_member" "cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}
