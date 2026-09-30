"""
Cloud SQL Postgres Connection Pool — used by PostgresSaver for persistent memory.

On Cloud Run, connects via Unix socket through the built-in Cloud SQL Auth Proxy.
Locally, falls back to MemorySaver if DB credentials are not set.

Environment variables:
    DB_HOST     — Unix socket path e.g. "/cloudsql/project:region:instance"
    DB_NAME     — Database name (default: enterprise_rag)
    DB_USER     — Database user (default: rag_admin)
    DB_PASSWORD — Database password (required for production)
"""

import os
import logfire
from psycopg_pool import ConnectionPool


def get_db_pool() -> ConnectionPool | None:
    """
    Create a psycopg3 ConnectionPool for Cloud SQL Postgres.

    Returns None if DB credentials are not set (local dev mode).
    The caller should fall back to MemorySaver when None is returned.
    """
    db_host = os.getenv("DB_HOST")  # "/cloudsql/project:region:instance"
    db_name = os.getenv("DB_NAME", "enterprise_rag")
    db_user = os.getenv("DB_USER", "rag_admin")
    db_pass = os.getenv("DB_PASSWORD")

    if not all([db_host, db_pass]):
        logfire.warning("DB credentials not set — will use MemorySaver (RAM)")
        return None

    conninfo = f"host={db_host} dbname={db_name} user={db_user} password={db_pass}"

    try:
        pool = ConnectionPool(conninfo, min_size=1, max_size=5, open=True)
        logfire.info(
            "✅ Postgres pool opened — host={host} db={db}",
            host=db_host,
            db=db_name,
        )
        return pool
    except Exception as e:
        logfire.error("❌ Failed to create DB pool: {error}", error=str(e))
        return None
