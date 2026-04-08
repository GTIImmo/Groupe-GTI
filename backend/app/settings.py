from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    app_base_url: str | None
    google_client_id: str | None
    google_client_secret: str | None
    google_refresh_token: str | None
    google_sender_email: str | None
    smtp_host: str | None
    smtp_port: int
    smtp_user: str | None
    smtp_pass: str | None
    smtp_secure: bool
    smtp_from: str | None
    smtp_allow_user_from: bool
    hektor_api_base_url: str | None
    hektor_client_id: str | None
    hektor_client_secret: str | None
    hektor_api_version: str
    python_executable: str
    project_root: Path
    hektor_writeback_script: Path
    refresh_single_annonce_script: Path


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def get_settings() -> Settings:
    python_default = ROOT / ".venv" / "Scripts" / "python.exe"
    return Settings(
        supabase_url=_require_env("SUPABASE_URL"),
        supabase_anon_key=_require_env("SUPABASE_ANON_KEY"),
        supabase_service_role_key=_require_env("SUPABASE_SERVICE_ROLE_KEY"),
        app_base_url=os.getenv("APP_BASE_URL", "").strip() or None,
        google_client_id=os.getenv("GOOGLE_CLIENT_ID", "").strip() or None,
        google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", "").strip() or None,
        google_refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN", "").strip() or None,
        google_sender_email=os.getenv("GOOGLE_SENDER_EMAIL", "").strip() or None,
        smtp_host=os.getenv("SMTP_HOST", "").strip() or None,
        smtp_port=int(os.getenv("SMTP_PORT", "587").strip() or "587"),
        smtp_user=os.getenv("SMTP_USER", "").strip() or None,
        smtp_pass=os.getenv("SMTP_PASS", "").strip() or None,
        smtp_secure=(os.getenv("SMTP_SECURE", "").strip().lower() == "true" or (os.getenv("SMTP_PORT", "").strip() == "465")),
        smtp_from=os.getenv("SMTP_FROM", "").strip() or None,
        smtp_allow_user_from=os.getenv("SMTP_ALLOW_USER_FROM", "").strip().lower() == "true",
        hektor_api_base_url=os.getenv("HEKTOR_API_BASE_URL", "").strip() or None,
        hektor_client_id=os.getenv("HEKTOR_CLIENT_ID", "").strip() or None,
        hektor_client_secret=os.getenv("HEKTOR_CLIENT_SECRET", "").strip() or None,
        hektor_api_version=os.getenv("HEKTOR_API_VERSION", "v2").strip() or "v2",
        python_executable=os.getenv("PYTHON_EXECUTABLE", str(python_default)),
        project_root=ROOT,
        hektor_writeback_script=ROOT / "phase2" / "sync" / "hektor_diffusion_writeback.py",
        refresh_single_annonce_script=ROOT / "phase2" / "sync" / "refresh_single_annonce.py",
    )
