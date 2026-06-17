from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
_ENV_FILES_LOADED = False


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
    google_workspace_domain: str
    google_workspace_auth_mode: str
    google_workspace_dwd_client_id: str | None
    google_workspace_service_account_file: Path | None
    google_workspace_subject_email: str | None
    google_workspace_scopes: tuple[str, ...]
    smtp_host: str | None
    smtp_port: int
    smtp_user: str | None
    smtp_pass: str | None
    smtp_secure: bool
    smtp_from: str | None
    smtp_allow_user_from: bool
    appointment_email_logo_url: str | None
    email_tracking_base_url: str | None
    email_tracking_secret: str | None
    email_real_send_enabled: bool
    espace_search_write_enabled: bool
    email_daily_send_cap: int
    email_daily_send_alert: int
    email_relance_max_per_bien: int
    hektor_api_base_url: str | None
    hektor_client_id: str | None
    hektor_client_secret: str | None
    hektor_api_version: str
    openai_api_key: str | None
    openai_vision_model: str
    python_executable: str
    project_root: Path
    hektor_writeback_script: Path
    refresh_single_annonce_script: Path


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def _split_csv_env(name: str) -> tuple[str, ...]:
    value = os.getenv(name, "").strip()
    if not value:
        return ()
    return tuple(item.strip() for item in value.replace("\n", ",").split(",") if item.strip())


def _optional_path_env(name: str) -> Path | None:
    value = os.getenv(name, "").strip()
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[key] = value


def _load_env_files() -> None:
    global _ENV_FILES_LOADED
    if _ENV_FILES_LOADED:
        return
    for path in (
        ROOT / ".env",
        ROOT / "apps" / "hektor-v1" / ".env",
        ROOT / "apps" / "hektor-v1" / ".env.local",
        ROOT / "backend" / ".env",
        ROOT / "backend" / ".env.local",
    ):
        _load_env_file(path)
    if not os.getenv("SUPABASE_URL") and os.getenv("VITE_SUPABASE_URL"):
        os.environ["SUPABASE_URL"] = os.getenv("VITE_SUPABASE_URL", "")
    if not os.getenv("SUPABASE_ANON_KEY") and os.getenv("VITE_SUPABASE_ANON_KEY"):
        os.environ["SUPABASE_ANON_KEY"] = os.getenv("VITE_SUPABASE_ANON_KEY", "")
    _ENV_FILES_LOADED = True


def get_settings() -> Settings:
    _load_env_files()
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
        google_workspace_domain=os.getenv("GOOGLE_WORKSPACE_DOMAIN", "gti-immobilier.fr").strip().lower() or "gti-immobilier.fr",
        google_workspace_auth_mode=os.getenv("GOOGLE_WORKSPACE_AUTH_MODE", "domain_wide_delegation").strip().lower() or "domain_wide_delegation",
        google_workspace_dwd_client_id=os.getenv("GOOGLE_WORKSPACE_DWD_CLIENT_ID", "").strip() or None,
        google_workspace_service_account_file=_optional_path_env("GOOGLE_WORKSPACE_SERVICE_ACCOUNT_FILE"),
        google_workspace_subject_email=os.getenv("GOOGLE_WORKSPACE_SUBJECT_EMAIL", "").strip().lower() or None,
        google_workspace_scopes=_split_csv_env("GOOGLE_WORKSPACE_SCOPES"),
        smtp_host=os.getenv("SMTP_HOST", "").strip() or None,
        smtp_port=int(os.getenv("SMTP_PORT", "587").strip() or "587"),
        smtp_user=os.getenv("SMTP_USER", "").strip() or None,
        smtp_pass=os.getenv("SMTP_PASS", "").strip() or None,
        smtp_secure=(os.getenv("SMTP_SECURE", "").strip().lower() == "true" or (os.getenv("SMTP_PORT", "").strip() == "465")),
        smtp_from=os.getenv("SMTP_FROM", "").strip() or None,
        smtp_allow_user_from=os.getenv("SMTP_ALLOW_USER_FROM", "").strip().lower() == "true",
        appointment_email_logo_url=os.getenv("APPOINTMENT_EMAIL_LOGO_URL", "").strip() or None,
        email_tracking_base_url=os.getenv("EMAIL_TRACKING_BASE_URL", "").strip() or None,
        email_tracking_secret=os.getenv("EMAIL_TRACKING_SECRET", "").strip() or None,
        email_real_send_enabled=(os.getenv("EMAIL_REAL_SEND_ENABLED", "").strip().lower() == "true"),
        espace_search_write_enabled=(os.getenv("ESPACE_SEARCH_WRITE_ENABLED", "").strip().lower() == "true"),
        email_daily_send_cap=int(os.getenv("EMAIL_DAILY_SEND_CAP", "80").strip() or "80"),
        email_daily_send_alert=int(os.getenv("EMAIL_DAILY_SEND_ALERT", "50").strip() or "50"),
        email_relance_max_per_bien=int(os.getenv("EMAIL_RELANCE_MAX_PER_BIEN", "2").strip() or "2"),
        hektor_api_base_url=os.getenv("HEKTOR_API_BASE_URL", "").strip() or None,
        hektor_client_id=os.getenv("HEKTOR_CLIENT_ID", "").strip() or None,
        hektor_client_secret=os.getenv("HEKTOR_CLIENT_SECRET", "").strip() or None,
        hektor_api_version=os.getenv("HEKTOR_API_VERSION", "v2").strip() or "v2",
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip() or None,
        openai_vision_model=os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini",
        python_executable=os.getenv("PYTHON_EXECUTABLE", str(python_default)),
        project_root=ROOT,
        hektor_writeback_script=ROOT / "phase2" / "sync" / "hektor_diffusion_writeback.py",
        refresh_single_annonce_script=ROOT / "phase2" / "sync" / "refresh_single_annonce.py",
    )
