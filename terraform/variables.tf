# ──────────────────────────────────────────────
# Input Variables
# ──────────────────────────────────────────────

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "us-central1"
}

variable "app_name" {
  description = "Base name for all resources (e.g. enterprise-rag)"
  type        = string
  default     = "enterprise-rag"
}

# ──────────────────────────────────────────────
# API Keys & Secrets (passed via terraform.tfvars)
# ──────────────────────────────────────────────

variable "groq_api_key" {
  description = "Groq API key for LLM inference"
  type        = string
  sensitive   = true
}

variable "groq_fallback_api_key" {
  description = "Groq fallback API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "judge_groq" {
  description = "Groq API key for eval judge LLM"
  type        = string
  sensitive   = true
  default     = ""
}

variable "logfire_token" {
  description = "Pydantic Logfire token"
  type        = string
  sensitive   = true
}

variable "portkey_api_key" {
  description = "Portkey API key"
  type        = string
  sensitive   = true
}

variable "portkey_config_id" {
  description = "Portkey Config ID"
  type        = string
  default     = ""
}

variable "qdrant_url" {
  description = "Qdrant Cloud cluster endpoint URL"
  type        = string
}

variable "qdrant_api_key" {
  description = "Qdrant Cloud API key"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Cloud SQL rag_admin user password"
  type        = string
  sensitive   = true
}

variable "openrouter_api_key" {
  description = "OpenRouter API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langsmith_api_key" {
  description = "LangSmith API key for tracing"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langsmith_project" {
  description = "LangSmith project name"
  type        = string
  default     = "enterprise-rag"
}
