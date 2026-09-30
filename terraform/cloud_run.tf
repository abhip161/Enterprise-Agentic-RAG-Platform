# ──────────────────────────────────────────────
# cloud_run.tf — Four Cloud Run Services
# Backend, UI, Ingestion, Evals
# ──────────────────────────────────────────────

locals {
  ar_prefix = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}"

  # Shared env vars for services that need GCP/LLM access
  common_env = {
    PROJECT_ID            = var.project_id
    LOCATION              = var.region
    GROQ_API_KEY          = var.groq_api_key
    GROQ_FALLBACK_API_KEY = var.groq_fallback_api_key
    LOGFIRE_TOKEN         = var.logfire_token
    PORTKEY_API_KEY       = var.portkey_api_key
    PORTKEY_CONFIG_ID     = var.portkey_config_id
    QDRANT_CLUSTER_ENDPOINT = var.qdrant_url
    QDRANT_API_KEY        = var.qdrant_api_key
    OPENROUTER_API_KEY    = var.openrouter_api_key
    LANGSMITH_TRACING     = "true"
    LANGSMITH_ENDPOINT    = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY     = var.langsmith_api_key
    LANGSMITH_PROJECT     = var.langsmith_project
  }
}

# ──────────────────────────────────────────────
# 1. Backend — FastAPI + LangGraph Agent
# ──────────────────────────────────────────────

resource "google_cloud_run_v2_service" "backend" {
  name     = "${var.app_name}-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

    containers {
      image = "${local.ar_prefix}/backend:latest"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          memory = "1Gi"
          cpu    = "1"
        }
      }

      # Common env vars
      dynamic "env" {
        for_each = local.common_env
        content {
          name  = env.key
          value = env.value
        }
      }

      # Backend-specific env vars
      env {
        name  = "LOCAL_MODE"
        value = "false"
      }
      env {
        name  = "USE_SEMANTIC_CACHE"
        value = "true"
      }
      env {
        name  = "REDIS_HOST"
        value = google_redis_instance.cache.host
      }
      env {
        name  = "REDIS_PORT"
        value = "6379"
      }
      env {
        name  = "DB_HOST"
        value = "/cloudsql/${google_sql_database_instance.postgres.connection_name}"
      }
      env {
        name  = "DB_NAME"
        value = "enterprise_rag"
      }
      env {
        name  = "DB_USER"
        value = "rag_admin"
      }
      env {
        name  = "DB_PASSWORD"
        value = var.db_password
      }
    }

    # Direct VPC Egress for Redis (private IP) + Cloud SQL
    vpc_access {
      network_interfaces {
        network    = google_compute_network.vpc.name
        subnetwork = google_compute_subnetwork.subnet.name
      }
      egress = "ALL_TRAFFIC"
    }

    # Cloud SQL Auth Proxy sidecar (built into Cloud Run)
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.postgres.connection_name]
      }
    }
  }

  depends_on = [google_project_service.services]
}

# Public access for backend
resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ──────────────────────────────────────────────
# 2. UI — Streamlit Chat Interface
# ──────────────────────────────────────────────

resource "google_cloud_run_v2_service" "ui" {
  name     = "${var.app_name}-ui"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = "${local.ar_prefix}/ui:latest"

      ports {
        container_port = 8501
      }

      resources {
        limits = {
          memory = "512Mi"
          cpu    = "1"
        }
      }

      env {
        name  = "BACKEND_URL"
        value = google_cloud_run_v2_service.backend.uri
      }
      env {
        name  = "LOGFIRE_TOKEN"
        value = var.logfire_token
      }
    }
  }

  depends_on = [google_project_service.services]
}

resource "google_cloud_run_v2_service_iam_member" "ui_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.ui.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ──────────────────────────────────────────────
# 3. Ingestion — Eventarc Webhook (Internal Only)
# ──────────────────────────────────────────────

resource "google_cloud_run_v2_service" "ingestion" {
  name     = "${var.app_name}-ingestion"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = "${local.ar_prefix}/ingestion:latest"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          memory = "2Gi"
          cpu    = "2"
        }
      }

      # Common env vars
      dynamic "env" {
        for_each = local.common_env
        content {
          name  = env.key
          value = env.value
        }
      }

      env {
        name  = "GCP_RAW_BUCKET"
        value = google_storage_bucket.raw.name
      }
      env {
        name  = "GCP_PROCESSED_BUCKET"
        value = google_storage_bucket.processed.name
      }
    }

    # Direct VPC Egress for internal services
    vpc_access {
      network_interfaces {
        network    = google_compute_network.vpc.name
        subnetwork = google_compute_subnetwork.subnet.name
      }
      egress = "ALL_TRAFFIC"
    }
  }

  depends_on = [google_project_service.services]
}

# ──────────────────────────────────────────────
# 4. Evals — RAGAS Evaluation Dashboard
# ──────────────────────────────────────────────

resource "google_cloud_run_v2_service" "evals" {
  name     = "${var.app_name}-evals"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {
      image = "${local.ar_prefix}/evals:latest"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          memory = "1Gi"
          cpu    = "1"
        }
      }

      env {
        name  = "BACKEND_URL"
        value = google_cloud_run_v2_service.backend.uri
      }
      env {
        name  = "LOGFIRE_TOKEN"
        value = var.logfire_token
      }
      env {
        name  = "JUDGE_GROQ"
        value = var.judge_groq
      }
      env {
        name  = "GCP_PROCESSED_BUCKET"
        value = google_storage_bucket.processed.name
      }

      # Vertex AI for RAGAS embeddings
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "LOCATION"
        value = var.region
      }
    }
  }

  depends_on = [google_project_service.services]
}

resource "google_cloud_run_v2_service_iam_member" "evals_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.evals.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
