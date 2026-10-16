"""Application configuration via environment variables and secrets."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="HIVECODE_", env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg://hivecode:hivecode@localhost:5432/hivecode"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # GitHub
    github_app_id: str = ""
    github_app_private_key: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    github_webhook_secret: str = ""

    # LLM
    llm_provider: str = "anthropic"
    llm_api_key: str = ""
    llm_model_analyst: str = "claude-sonnet-4-20250514"
    llm_model_coder: str = "claude-sonnet-4-20250514"
    llm_model_reviewer: str = "claude-sonnet-4-20250514"

    # Sandbox
    sandbox_image: str = "hivecode-runner:py312"
    sandbox_timeout_s: int = 1800

    # Security
    session_cookie_name: str = "__Host-session"
    session_idle_timeout_s: int = 86400  # 24h
    session_absolute_timeout_s: int = 604800  # 7 days
    csrf_header: str = "X-CSRF-Token"

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_s: int = 60

    # Task defaults
    max_repair_attempts: int = 3
    max_files_per_attempt: int = 15
    max_lines_per_attempt: int = 500
    task_time_limit_s: int = 1800  # 30 min
    task_cost_limit_usd: float = 5.00

    # Storage
    artifact_storage_bucket: str = "hivecode-artifacts"
    artifact_storage_endpoint: str = "http://localhost:9000"
    artifact_storage_access_key: str = "minioadmin"
    artifact_storage_secret_key: str = "minioadmin"

    # Environment
    environment: str = "local"
    log_level: str = "INFO"


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
