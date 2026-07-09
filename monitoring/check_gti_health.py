from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAME = "check_gti_health"

# Politique de fraicheur du heartbeat workers, par classe de frequence du
# registre (app_worker_registry.frequency). Valeur = age max toleré depuis le
# dernier succes, en minutes. None = worker "a la demande" -> jamais "en retard".
# Le run nuit tourne a 05:30 et le monitor toutes les 2h : 28h couvre un jour
# manque sans crier a tort.
WORKER_STALE_POLICY: dict[str, int | None] = {
    "pipeline_step": 28 * 60,
    "optional_pipeline_step": 50 * 60,
    "scheduled_or_manual": 28 * 60,
    "manual_or_scheduled": 28 * 60,
    "daemon_or_scheduled": 6 * 60,
    "service": 3 * 60,
    "watcher": 6 * 60,
    "console_follow_up": None,
    "backend_or_manual": None,
    "manual": None,
    "manual_or_watch": None,
}

# Criticite des taches planifiees Windows surveillees (defaut = warning).
TASK_CRITICALITY: dict[str, str] = {
    "GTI Quotidien": "critical",
}

# Codes LastTaskResult consideres comme sains : succes / en cours / jamais lance.
ACCEPTABLE_TASK_RESULTS = {0, 267009, 267011}

# Sentinelles de donnees : requetes read-only qui detectent les DERIVES SILENCIEUSES
# (idnego, notifications orphelines, diffusion sans mandat, chute d'actives...) que le
# monitoring infra ne voit pas. Calibrees sur la baseline live du 2026-07-04.
#   - "absolute" : anomalie si count > max (signaux qui doivent rester bas).
#   - "growth"   : compare au run precedent (via details_json.count persiste) ; alerte
#                  si hausse > growth_pct ET hausse absolue >= growth_abs.
#   - "drop"     : alerte si chute > drop_pct vs precedent ; critical sous min_floor.
DATA_SENTINELS: list[dict[str, Any]] = [
    {
        "key": "data.actives_total",
        "label": "Annonces actives",
        "table": "app_dossier_current",
        "params": {"archive": "eq.0"},
        "rule": "drop",
        "drop_pct": 12,
        "min_floor": 500,
    },
    {
        "key": "data.actives_sans_nego",
        "label": "Annonces actives sans negociateur",
        "table": "app_dossier_current",
        "params": {"archive": "eq.0", "or": "(negociateur_email.is.null,negociateur_email.eq.)"},
        "rule": "growth",
        "growth_pct": 15,
        "growth_abs": 300,
    },
    {
        "key": "data.diffusees_sans_mandat",
        "label": "Annonces diffusees sans mandat",
        "table": "app_dossier_current",
        "params": {"nb_portails_actifs": "gt.0", "or": "(mandat_type.is.null,mandat_type.eq.)"},
        "rule": "absolute",
        "max": 150,
    },
    {
        "key": "data.diffusion_erreur",
        "label": "Annonces en erreur de diffusion",
        "table": "app_dossier_current",
        "params": {"has_diffusion_error": "eq.true"},
        "rule": "absolute",
        "max": 10,
    },
    {
        "key": "data.contacts_sans_nego",
        "label": "Contacts eligibles sans negociateur",
        "table": "app_contact_current",
        "params": {"supabase_sync_eligible": "eq.true", "or": "(negociateur_email.is.null,negociateur_email.eq.)"},
        "rule": "growth",
        "growth_pct": 15,
        "growth_abs": 500,
    },
    {
        "key": "data.contacts_doublons",
        "label": "Doublons contacts high/critical",
        "table": "app_contact_current",
        "params": {"duplicate_max_severity": "in.(high,critical)"},
        "rule": "growth",
        "growth_pct": 15,
        "growth_abs": 500,
    },
    {
        "key": "data.notif_orphelines",
        "label": "Notifications sans destinataire",
        "table": "app_notification",
        "params": {"negociateur_email": "is.null"},
        "rule": "absolute",
        "max": 20,
    },
    {
        "key": "data.notif_non_lues",
        "label": "Notifications non lues",
        "table": "app_notification",
        "params": {"read_at": "is.null"},
        "rule": "absolute",
        "max": 300,
    },
]

# Surfaces publiques a sonder depuis l'exterieur (up-check HTTP simple).
PUBLIC_SURFACES = [
    ("surface.app_vercel", "App metier (Vercel)", "https://groupe-gti.vercel.app"),
    ("surface.vitrine", "Vitrine agences (GitHub Pages)", "https://gtiimmo.github.io/vitrine/"),
    ("surface.rdv_public", "Portail RDV public", "https://gtiimmo.github.io/vitrine/rdv/index.html"),
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(dt: datetime | None = None) -> str:
    return (dt or utc_now()).isoformat().replace("+00:00", "Z")


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip().strip('"').strip("'")
        os.environ[key] = value


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    cleaned = str(value).strip()
    if not cleaned:
        return None
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def age_minutes(dt: datetime | None) -> float | None:
    if dt is None:
        return None
    return max(0.0, (utc_now() - dt).total_seconds() / 60.0)


def file_mtime(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    except OSError:
        return None


def dir_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                continue
    return total


def newest_file(directory: Path, pattern: str) -> Path | None:
    if not directory.exists():
        return None
    files = [p for p in directory.glob(pattern) if p.is_file()]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def tail_text(path: Path, max_bytes: int = 8192) -> str:
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - max_bytes), os.SEEK_SET)
            return handle.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def simple_error_seen(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in (" error", "failed", "exception", "traceback", "echou", "erreur"))


@dataclass
class CheckResult:
    status_key: str
    domain: str
    component: str
    check_name: str
    status: str
    severity: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    observed_at: str = field(default_factory=iso_utc)

    def status_row(self) -> dict[str, Any]:
        return {
            "status_key": self.status_key,
            "domain": self.domain,
            "component": self.component,
            "check_name": self.check_name,
            "status": self.status,
            "severity": self.severity,
            "message": self.message[:1000],
            "observed_at": self.observed_at,
            "details_json": self.details,
            "source": SOURCE_NAME,
            "updated_at": iso_utc(),
        }

    def event_row(self) -> dict[str, Any]:
        return {
            "event_key": self.status_key,
            "domain": self.domain,
            "component": self.component,
            "check_name": self.check_name,
            "status": self.status,
            "severity": self.severity,
            "message": self.message[:1000],
            "observed_at": self.observed_at,
            "details_json": self.details,
            "source": SOURCE_NAME,
        }


class SupabaseClient:
    def __init__(self, url: str, service_role_key: str, timeout_seconds: int = 15) -> None:
        self.url = url.rstrip("/")
        self.key = service_role_key
        self.timeout_seconds = timeout_seconds

    def _headers(self, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def request(
        self,
        path: str,
        *,
        method: str = "GET",
        params: dict[str, str] | None = None,
        payload: Any | None = None,
        prefer: str | None = None,
    ) -> Any:
        query = ""
        if params:
            query = "?" + urllib.parse.urlencode(params, doseq=False, safe="(),.*")
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        request = urllib.request.Request(
            f"{self.url}/rest/v1/{path}{query}",
            data=body,
            method=method,
            headers=self._headers(prefer),
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                text = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase HTTP {exc.code} on {path}: {detail[:500]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Supabase unreachable on {path}: {exc}") from exc
        if not text:
            return None
        return json.loads(text)

    def get(self, path: str, params: dict[str, str] | None = None) -> Any:
        return self.request(path, params=params)

    def count(self, path: str, params: dict[str, str] | None = None) -> int | None:
        """Compte exact via PostgREST (en-tete Content-Range), sans ramener les lignes."""
        merged = dict(params or {})
        merged["limit"] = "1"
        query = "?" + urllib.parse.urlencode(merged, doseq=False, safe="(),.*")
        request = urllib.request.Request(
            f"{self.url}/rest/v1/{path}{query}",
            method="GET",
            headers=self._headers(prefer="count=exact"),
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                content_range = response.headers.get("Content-Range") or ""
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"Supabase count HTTP {exc.code} on {path}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Supabase count unreachable on {path}: {exc}") from exc
        if "/" in content_range:
            total = content_range.rsplit("/", 1)[-1].strip()
            if total.isdigit():
                return int(total)
        return None

    def upsert_status(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        self.request(
            "app_monitor_status",
            method="POST",
            params={"on_conflict": "status_key"},
            payload=rows,
            prefer="resolution=merge-duplicates,return=minimal",
        )

    def insert_events(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        self.request("app_monitor_event", method="POST", payload=rows, prefer="return=minimal")

    def purge_stale_status(self, cutoff_iso: str) -> None:
        """Supprime les statuts non re-emis depuis cutoff (cle resolue / obsolete).

        Le run vient d'upserter tous les statuts courants avec updated_at=now ; toute
        ligne plus ancienne que cutoff correspond donc a une cle qui n'est plus emise.
        """
        self.request(
            "app_monitor_status",
            method="DELETE",
            params={"updated_at": f"lt.{cutoff_iso}"},
            prefer="return=minimal",
        )


class Alerter:
    """Canal d'alerte sortant : previent Frederic (email + WhatsApp) sur bascule vers critical.

    Palier 1 / Lot 1.4. Best-effort STRICT : un echec d'envoi ne casse jamais le monitor.
    - Email : SMTP direct (smtplib) avec la config SMTP_* existante du projet.
    - WhatsApp : POST vers une passerelle configurable (env WHATSAPP_ALERT_WEBHOOK),
      inactif tant que la passerelle n'est pas fournie.
    Destinataires par defaut : Frederic (jamais accueil@).
    """

    def __init__(self, args: argparse.Namespace) -> None:
        self.enabled = not getattr(args, "no_alerts", False)
        self.email_to = args.alert_email
        self.whatsapp_to = args.alert_whatsapp
        self.whatsapp_webhook = os.getenv("WHATSAPP_ALERT_WEBHOOK", "").strip()
        self.whatsapp_token = os.getenv("WHATSAPP_ALERT_TOKEN", "").strip()
        self.smtp_host = os.getenv("SMTP_HOST", "").strip()
        self.smtp_port = int(os.getenv("SMTP_PORT", "0") or 0)
        self.smtp_user = os.getenv("SMTP_USER", "").strip()
        self.smtp_pass = os.getenv("SMTP_PASS", "")
        self.smtp_from = (os.getenv("SMTP_FROM", "").strip() or self.smtp_user)
        self.smtp_secure = (os.getenv("SMTP_SECURE", "") or "").strip().lower()
        self.timeout = 20

    def compose(self, critical_results: list["CheckResult"], kind: str = "critical") -> tuple[str, str]:
        host = socket.gethostname()
        stamp = iso_utc()
        if kind == "recovery":
            subject = "[GTI Monitoring] Retour a la normale"
            body = "\n".join(
                ["Les alertes critiques GTI/Hektor sont resolues.", "", f"Hote: {host}", f"Heure: {stamp}"]
            )
            return subject, body
        count = len(critical_results)
        subject = f"[GTI Monitoring] {count} alerte(s) critique(s)"
        lines = [f"{count} alerte(s) critique(s) detectee(s) sur GTI/Hektor :", ""]
        for result in critical_results:
            lines.append(f"- [{result.status_key}] {result.message}")
        lines += ["", f"Hote: {host}", f"Heure: {stamp}"]
        return subject, "\n".join(lines)

    def dispatch(self, critical_results: list["CheckResult"], kind: str = "critical", dry_run: bool = False) -> None:
        if not self.enabled:
            return
        subject, body = self.compose(critical_results, kind=kind)
        if dry_run:
            print(f"[alert dry-run] to={self.email_to} / whatsapp={self.whatsapp_to}\n{subject}\n{body}")
            return
        self._send_email(subject, body)
        self._send_whatsapp(f"{subject}\n{body}")

    def _send_email(self, subject: str, body: str) -> None:
        if not (self.smtp_host and self.email_to and self.smtp_from):
            print("[alert] email ignore: SMTP non configure", file=sys.stderr)
            return
        try:
            import smtplib
            from email.message import EmailMessage

            message = EmailMessage()
            message["From"] = self.smtp_from
            message["To"] = self.email_to
            message["Subject"] = subject
            message.set_content(body)
            port = self.smtp_port or (465 if self.smtp_secure == "ssl" else 587)
            if self.smtp_secure == "ssl" or port == 465:
                with smtplib.SMTP_SSL(self.smtp_host, port, timeout=self.timeout) as server:
                    if self.smtp_user:
                        server.login(self.smtp_user, self.smtp_pass)
                    server.send_message(message)
            else:
                with smtplib.SMTP(self.smtp_host, port, timeout=self.timeout) as server:
                    if self.smtp_secure in ("starttls", "tls"):
                        server.starttls()
                    if self.smtp_user:
                        server.login(self.smtp_user, self.smtp_pass)
                    server.send_message(message)
        except Exception as exc:
            print(f"[alert] email echoue: {exc}", file=sys.stderr)

    def _send_whatsapp(self, text: str) -> None:
        if not self.whatsapp_webhook:
            print("[alert] whatsapp ignore: WHATSAPP_ALERT_WEBHOOK absent", file=sys.stderr)
            return
        try:
            payload = json.dumps({"to": self.whatsapp_to, "text": text}).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if self.whatsapp_token:
                headers["Authorization"] = f"Bearer {self.whatsapp_token}"
            request = urllib.request.Request(self.whatsapp_webhook, data=payload, method="POST", headers=headers)
            with urllib.request.urlopen(request, timeout=self.timeout):
                pass
        except Exception as exc:
            print(f"[alert] whatsapp echoue: {exc}", file=sys.stderr)


class Monitor:
    def __init__(self, args: argparse.Namespace, supabase: SupabaseClient | None) -> None:
        self.args = args
        self.supabase = supabase
        self.root = Path(args.project_root).resolve()
        self.results: list[CheckResult] = []

    def add(
        self,
        status_key: str,
        domain: str,
        component: str,
        check_name: str,
        status: str,
        message: str,
        details: dict[str, Any] | None = None,
        severity: str | None = None,
    ) -> None:
        if severity is None:
            severity = "info" if status == "ok" else status
        self.results.append(
            CheckResult(
                status_key=status_key,
                domain=domain,
                component=component,
                check_name=check_name,
                status=status,
                severity=severity,
                message=message,
                details=details or {},
            )
        )

    def safe_check(self, label: str, func: Any) -> None:
        try:
            func()
        except Exception as exc:
            self.add(
                f"monitor.{label}",
                "system",
                "monitor",
                label,
                "unknown",
                f"Check {label} failed locally: {exc}",
                {"error": str(exc)},
                severity="unknown",
            )

    def run(self) -> list[CheckResult]:
        checks = [
            ("supabase_registry", self.check_supabase_registry),
            ("worker_heartbeat", self.check_worker_heartbeat),
            ("scheduled_tasks", self.check_scheduled_tasks),
            ("data_sentinels", self.check_data_sentinels),
            ("email_volume", self.check_email_volume),
            ("public_surfaces", self.check_public_surfaces),
            ("vitrine_catalogue", self.check_vitrine_catalogue),
            ("cron_health", self.check_cron_health),
            ("supabase_runs", self.check_supabase_runs),
            ("console_jobs", self.check_console_jobs),
            ("backend_health", self.check_backend_health),
            ("sqlite_files", self.check_sqlite_files),
            ("local_logs", self.check_local_logs),
            ("playwright_sessions", self.check_playwright_sessions),
            ("document_storage", self.check_document_storage),
        ]
        for label, check in checks:
            self.safe_check(label, check)
        self.add_summary()
        return self.results

    def check_supabase_registry(self) -> None:
        if not self.supabase:
            self.add("supabase.registry", "system", "supabase", "worker_registry", "unknown", "Supabase not configured")
            return
        rows = self.supabase.get(
            "app_worker_registry",
            {
                "select": "worker_key,status,criticality,monitoring_domain",
                "order": "worker_key.asc",
            },
        )
        all_rows = rows or []
        if len(all_rows) == 0:
            self.add("supabase.registry", "system", "supabase", "worker_registry", "critical", "Worker registry is empty")
            return
        # On ne compte que les workers operationnels : les 'disabled' (ex : prototype ACTIF
        # abandonne) ne doivent pas gonfler le compteur ni la realite pilotee.
        operational = [row for row in all_rows if row.get("status") != "disabled"]
        disabled = len(all_rows) - len(operational)
        critical = sum(1 for row in operational if row.get("criticality") == "critical")
        message = f"Registre workers: {len(operational)} actifs"
        if disabled:
            message += f" ({disabled} desactives)"
        self.add(
            "supabase.registry",
            "system",
            "supabase",
            "worker_registry",
            "ok",
            message,
            {"worker_count": len(operational), "disabled_count": disabled, "critical_count": critical},
        )

    def check_worker_heartbeat(self) -> None:
        """Preuve de vie par worker : alerte si un worker planifie n'a plus de succes recent.

        Lit le heartbeat (last_success_at) ecrit par chaque worker. Degrade en
        info si les colonnes ne sont pas encore provisionnees (migration
        patch_worker_heartbeat non appliquee), sans polluer le resume.
        """
        if not self.supabase:
            return
        try:
            rows = self.supabase.get(
                "app_worker_registry",
                {
                    "select": "worker_key,worker_name,criticality,frequency,status,last_success_at,last_run_at,last_status",
                    "order": "worker_key.asc",
                },
            )
        except Exception as exc:
            self.add(
                "workers.heartbeat",
                "system",
                "workers",
                "heartbeat",
                "ok",
                "Heartbeat workers en attente de migration (patch_worker_heartbeat_2026-07-04.sql)",
                {"pending_migration": True, "error": str(exc)[:300]},
                severity="info",
            )
            return
        rows = rows or []
        default_max = float(self.args.worker_stale_default_minutes)
        stale: list[dict[str, Any]] = []
        never: list[str] = []
        scheduled = 0
        for row in rows:
            if (row.get("status") or "active") != "active":
                continue
            frequency = row.get("frequency") or ""
            max_age = WORKER_STALE_POLICY.get(frequency, default_max)
            if max_age is None:
                continue  # worker a la demande : pas de notion de retard
            scheduled += 1
            worker_key = row.get("worker_key") or "?"
            success_at = parse_iso(row.get("last_success_at"))
            if success_at is None:
                never.append(worker_key)
                continue
            age = age_minutes(success_at) or 0.0
            if age > float(max_age):
                criticality = row.get("criticality") or "medium"
                severity = "critical" if criticality == "critical" else "warning"
                stale.append(
                    {
                        "worker_key": worker_key,
                        "age": age,
                        "threshold": float(max_age),
                        "severity": severity,
                        "frequency": frequency,
                        "criticality": criticality,
                        "last_status": row.get("last_status"),
                    }
                )
        for item in stale:
            self.add(
                f"workers.heartbeat:{item['worker_key']}",
                "system",
                "workers",
                "heartbeat_worker",
                item["severity"],
                f"Worker sans succes depuis {item['age']:.0f} min (seuil {item['threshold']:.0f}): {item['worker_key']}",
                {
                    "worker_key": item["worker_key"],
                    "age_minutes": item["age"],
                    "threshold_minutes": item["threshold"],
                    "frequency": item["frequency"],
                    "criticality": item["criticality"],
                    "last_status": item["last_status"],
                },
                severity=item["severity"],
            )
        if any(item["severity"] == "critical" for item in stale):
            summary_status = "critical"
        elif stale:
            summary_status = "warning"
        else:
            summary_status = "ok"
        self.add(
            "workers.heartbeat",
            "system",
            "workers",
            "heartbeat",
            summary_status,
            f"Heartbeat workers: {scheduled} planifies suivis, {len(stale)} en retard, {len(never)} sans premier signe",
            {
                "scheduled_tracked": scheduled,
                "stale_count": len(stale),
                "stale_workers": [item["worker_key"] for item in stale],
                "never_reported": never,
            },
        )

    def check_scheduled_tasks(self) -> None:
        """Surveille les taches planifiees Windows GTI (LastTaskResult != 0 = echec).

        Complementaire du heartbeat : detecte un planificateur qui echoue meme
        quand le worker lui-meme n'a pas eu l'occasion de tourner. Utilise
        Get-ScheduledTaskInfo (proprietes en anglais -> insensible a la locale).
        Skip propre hors Windows.
        """
        if os.name != "nt":
            self.add(
                "scheduledtasks",
                "system",
                "scheduledtasks",
                "windows_tasks",
                "ok",
                "Verification taches planifiees ignoree (hors Windows)",
                {"skipped": True},
                severity="info",
            )
            return
        names = [n.strip() for n in str(self.args.scheduled_tasks).split(",") if n.strip()]
        if not names:
            return
        ps_names = ",".join("'" + n.replace("'", "''") + "'" for n in names)
        script = (
            "$ErrorActionPreference='SilentlyContinue';"
            f"$names=@({ps_names});"
            "$out=foreach($n in $names){"
            " $t=Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue;"
            " if($t){ $i=$t|Get-ScheduledTaskInfo;"
            "  $age=$null; if($i.LastRunTime){$age=[int]((Get-Date)-$i.LastRunTime).TotalMinutes};"
            "  [pscustomobject]@{Name=$n;State=[string]$t.State;LastResult=$i.LastTaskResult;AgeMin=$age} }"
            " else { [pscustomobject]@{Name=$n;State='NotFound';LastResult=$null;AgeMin=$null} } };"
            "$out | ConvertTo-Json -Compress -Depth 3"
        )
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True,
                text=True,
                timeout=self.args.timeout_seconds,
            )
            raw = (proc.stdout or "").strip()
            data = json.loads(raw) if raw else []
        except Exception as exc:
            self.add(
                "scheduledtasks",
                "system",
                "scheduledtasks",
                "windows_tasks",
                "unknown",
                f"Impossible de lire les taches planifiees: {exc}",
                {"error": str(exc)[:300]},
                severity="unknown",
            )
            return
        if isinstance(data, dict):
            data = [data]
        problems: list[dict[str, Any]] = []
        for row in data:
            name = row.get("Name") or "?"
            state = row.get("State") or "?"
            result = row.get("LastResult")
            if state == "Disabled":
                continue  # tache volontairement desactivee : pas une alerte
            criticality = TASK_CRITICALITY.get(name, "warning")
            if state == "NotFound":
                problems.append({"name": name, "severity": "warning", "reason": "tache introuvable", "result": None})
                continue
            if result is not None and int(result) not in ACCEPTABLE_TASK_RESULTS:
                severity = "critical" if criticality == "critical" else "warning"
                problems.append({"name": name, "severity": severity, "reason": f"dernier resultat {result}", "result": result})
        for item in problems:
            slug = str(item["name"]).lower().replace(" ", "_")
            self.add(
                f"scheduledtasks:{slug}",
                "system",
                "scheduledtasks",
                "windows_task",
                item["severity"],
                f"Tache planifiee {item['name']}: {item['reason']}",
                {"task": item["name"], "reason": item["reason"], "last_result": item["result"]},
                severity=item["severity"],
            )
        if any(item["severity"] == "critical" for item in problems):
            summary_status = "critical"
        elif problems:
            summary_status = "warning"
        else:
            summary_status = "ok"
        self.add(
            "scheduledtasks",
            "system",
            "scheduledtasks",
            "windows_tasks",
            summary_status,
            f"Taches planifiees: {len(data)} suivies, {len(problems)} en anomalie",
            {"tracked": len(data), "problem_count": len(problems), "problems": [item["name"] for item in problems]},
        )

    def _previous_sentinel_count(self, status_key: str) -> int | None:
        """Lit le count du run precedent depuis app_monitor_status.details_json.count."""
        try:
            rows = self.supabase.get(
                "app_monitor_status",
                {"status_key": f"eq.{status_key}", "select": "details_json", "limit": "1"},
            ) if self.supabase else None
        except Exception:
            return None
        if rows:
            detail = rows[0].get("details_json") or {}
            value = detail.get("count")
            if isinstance(value, (int, float)):
                return int(value)
        return None

    def _evaluate_sentinel(self, sentinel: dict[str, Any], count: int) -> tuple[str, str, dict[str, Any]]:
        label = sentinel["label"]
        rule = sentinel["rule"]
        if rule == "absolute":
            max_v = int(sentinel["max"])
            if count > max_v:
                return "warning", f"{label}: {count} (seuil {max_v})", {"rule": rule, "threshold": max_v}
            return "ok", f"{label}: {count} (seuil {max_v})", {"rule": rule, "threshold": max_v}
        previous = self._previous_sentinel_count(sentinel["key"])
        if previous is None:
            return "ok", f"{label}: {count} (baseline etablie)", {"rule": rule, "previous": None}
        if rule == "growth":
            growth_pct = float(sentinel.get("growth_pct", 15))
            growth_abs = int(sentinel.get("growth_abs", 0))
            if count > previous * (1 + growth_pct / 100) and (count - previous) >= growth_abs:
                return "warning", f"{label}: {count} (etait {previous}, +{count - previous})", {"rule": rule, "previous": previous, "growth_pct": growth_pct}
            return "ok", f"{label}: {count} (prec. {previous})", {"rule": rule, "previous": previous}
        if rule == "drop":
            drop_pct = float(sentinel.get("drop_pct", 12))
            floor = int(sentinel.get("min_floor", 0))
            if count < floor:
                return "critical", f"{label}: {count} sous le plancher {floor}", {"rule": rule, "previous": previous, "floor": floor}
            if count < previous * (1 - drop_pct / 100):
                return "warning", f"{label}: chute {previous} -> {count}", {"rule": rule, "previous": previous, "drop_pct": drop_pct}
            return "ok", f"{label}: {count} (prec. {previous})", {"rule": rule, "previous": previous}
        return "ok", f"{label}: {count}", {"rule": rule}

    def check_data_sentinels(self) -> None:
        """Sentinelles de donnees : detecte les derives silencieuses (idnego, orphelines,
        diffusion sans mandat, chute d'actives...) invisibles pour le monitoring infra.
        Chaque sentinelle persiste son count pour la comparaison au run suivant.
        """
        if not self.supabase:
            return
        for sentinel in DATA_SENTINELS:
            key = sentinel["key"]
            try:
                count = self.supabase.count(sentinel["table"], sentinel.get("params"))
            except Exception as exc:
                self.add(
                    key,
                    "data_quality",
                    "data",
                    "sentinel",
                    "unknown",
                    f"Sentinelle '{sentinel['label']}' illisible: {exc}",
                    {"error": str(exc)[:200]},
                    severity="unknown",
                )
                continue
            if count is None:
                continue
            status, message, details = self._evaluate_sentinel(sentinel, count)
            details["count"] = count
            self.add(key, "data_quality", "data", "sentinel", status, message, details)

    def check_email_volume(self) -> None:
        """Volume d'emails REELS envoyes aujourd'hui vs plafond quotidien (anti-spam).

        Complement du garde-fou backend (EMAIL_DAILY_SEND_CAP). Surface une derive
        (surge d'envois) ou confirme le calme (ex : apres blocage des relances auto).
        """
        if not self.supabase:
            return
        try:
            cap = int(os.getenv("EMAIL_DAILY_SEND_CAP", "80") or 80)
            alert = int(os.getenv("EMAIL_DAILY_SEND_ALERT", "50") or 50)
        except ValueError:
            cap, alert = 80, 50
        today = utc_now().strftime("%Y-%m-%dT00:00:00Z")
        try:
            count = self.supabase.count(
                "app_email_envoi",
                {"dry_run": "eq.false", "created_at": f"gte.{today}"},
            )
        except Exception as exc:
            self.add(
                "email.volume_today",
                "business",
                "email",
                "daily_volume",
                "unknown",
                f"Volume email illisible: {exc}",
                {"error": str(exc)[:200]},
                severity="unknown",
            )
            return
        if count is None:
            return
        status = "warning" if count >= alert else "ok"
        self.add(
            "email.volume_today",
            "business",
            "email",
            "daily_volume",
            status,
            f"Emails reels aujourd'hui: {count}/{cap} (seuil alerte {alert})",
            {"count": count, "cap": cap, "alert": alert},
        )

    def check_public_surfaces(self) -> None:
        """Sonde synthetique : les surfaces publiques repondent-elles depuis Internet ?

        Vu de l'exterieur (pas depuis le serveur) : app Vercel, vitrine agences, RDV public.
        """
        for key, label, url in PUBLIC_SURFACES:
            started = time.monotonic()
            try:
                request = urllib.request.Request(url, method="GET", headers={"User-Agent": "gti-monitor"})
                with urllib.request.urlopen(request, timeout=self.args.backend_timeout_seconds) as response:
                    elapsed_ms = int((time.monotonic() - started) * 1000)
                    status = "ok" if response.status == 200 else "warning"
                    self.add(
                        key, "system", "surface", "http_up", status,
                        f"{label}: HTTP {response.status}",
                        {"url": url, "elapsed_ms": elapsed_ms},
                    )
            except Exception as exc:
                self.add(
                    key, "system", "surface", "http_up", "warning",
                    f"{label} injoignable: {exc}",
                    {"url": url, "error": str(exc)[:200]},
                )

    def check_vitrine_catalogue(self) -> None:
        """Sante du catalogue vitrine : nb de biens + fraicheur (generatedAt).

        Un catalogue vide ou fige = ecrans en agence qui affichent du blanc ou du perime,
        sans que personne ne le voie. Detecte les deux cas.
        """
        url = self.args.vitrine_catalogue_url
        try:
            request = urllib.request.Request(url, method="GET", headers={"User-Agent": "gti-monitor"})
            with urllib.request.urlopen(request, timeout=self.args.backend_timeout_seconds) as response:
                raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
        except Exception as exc:
            self.add(
                "surface.vitrine_catalogue", "business", "surface", "vitrine_catalogue", "warning",
                f"Catalogue vitrine illisible: {exc}",
                {"url": url, "error": str(exc)[:200]},
            )
            return
        items = data.get("items") if isinstance(data, dict) else data
        count = len(items) if isinstance(items, list) else 0
        generated = parse_iso(data.get("generatedAt")) if isinstance(data, dict) else None
        age_hours = (age_minutes(generated) or 0.0) / 60.0 if generated else None
        min_items = int(self.args.vitrine_min_items)
        fresh_hours = float(self.args.vitrine_freshness_hours)
        problems = []
        if count < min_items:
            problems.append(f"seulement {count} biens (seuil {min_items})")
        if age_hours is not None and age_hours > fresh_hours:
            problems.append(f"fige depuis {age_hours:.0f}h (seuil {fresh_hours:.0f}h)")
        if problems:
            status, message = "warning", "Vitrine: " + " ; ".join(problems)
        elif age_hours is not None:
            status, message = "ok", f"Vitrine OK: {count} biens, genere il y a {age_hours:.0f}h"
        else:
            status, message = "ok", f"Vitrine OK: {count} biens"
        self.add(
            "surface.vitrine_catalogue", "business", "surface", "vitrine_catalogue", status,
            message,
            {"url": url, "items": count, "age_hours": age_hours, "min_items": min_items, "freshness_hours": fresh_hours},
        )

    def check_cron_health(self) -> None:
        """Sante pg_cron : alerte si un job planifie echoue ou se fige.

        Comble l'angle mort revele le 04/07 (cron rapprochement-alerts en echec,
        invisible). Degrade en info si la RPC app_cron_health n'est pas provisionnee.
        """
        if not self.supabase:
            return
        try:
            rows = self.supabase.request("rpc/app_cron_health", method="POST", payload={})
        except Exception as exc:
            self.add(
                "cron.health",
                "system",
                "cron",
                "pg_cron",
                "ok",
                "Sante pg_cron en attente de migration (patch_cron_health_rpc_2026-07-04.sql)",
                {"pending_migration": True, "error": str(exc)[:200]},
                severity="info",
            )
            return
        rows = rows or []
        stale_limit = float(self.args.cron_stale_minutes)
        problems: list[dict[str, Any]] = []
        for row in rows:
            if row.get("active") is False:
                continue
            jobname = row.get("jobname") or "?"
            last_status = row.get("last_status")
            age = age_minutes(parse_iso(row.get("last_run")))
            if last_status == "failed":
                problems.append({"job": jobname, "reason": "dernier run en echec"})
            elif age is not None and age > stale_limit:
                problems.append({"job": jobname, "reason": f"pas de run depuis {age:.0f} min"})
        for item in problems:
            slug = str(item["job"]).replace(" ", "_").replace("-", "_")
            self.add(
                f"cron.health:{slug}",
                "system",
                "cron",
                "pg_cron_job",
                "warning",
                f"Cron {item['job']}: {item['reason']}",
                {"job": item["job"], "reason": item["reason"]},
            )
        summary_status = "warning" if problems else "ok"
        self.add(
            "cron.health",
            "system",
            "cron",
            "pg_cron",
            summary_status,
            f"pg_cron: {len(rows)} jobs suivis, {len(problems)} en anomalie",
            {"job_count": len(rows), "problem_count": len(problems), "problems": [item["job"] for item in problems]},
        )

    def check_supabase_runs(self) -> None:
        if not self.supabase:
            return
        delta_rows = self.supabase.get(
            "app_delta_run",
            {
                "select": "id,status,scope,started_at,finished_at,notes",
                "order": "started_at.desc",
                "limit": "10",
            },
        ) or []
        completed = [row for row in delta_rows if row.get("status") == "completed"]
        # Anti-bruit : ne compter que les echecs RECENTS (un echec deja corrige depuis
        # 2 jours ne doit plus polluer le signal courant).
        delta_error_window = float(self.args.delta_error_window_minutes)
        failed = [
            row
            for row in delta_rows
            if row.get("status") == "failed"
            and (age_minutes(parse_iso(row.get("started_at"))) or 0.0) <= delta_error_window
        ]
        latest_completed = completed[0] if completed else None
        latest_finished = parse_iso(latest_completed.get("finished_at") if latest_completed else None)
        latest_age = age_minutes(latest_finished)
        stale_limit = float(self.args.supabase_freshness_minutes)
        if latest_age is None:
            self.add(
                "supabase.delta_run.freshness",
                "system",
                "supabase",
                "delta_run_freshness",
                "warning",
                "No completed app_delta_run found",
                {"recent_runs": len(delta_rows)},
            )
        elif latest_age > stale_limit:
            self.add(
                "supabase.delta_run.freshness",
                "system",
                "supabase",
                "delta_run_freshness",
                "warning",
                f"Latest completed Supabase delta run is stale: {latest_age:.0f} min",
                {"age_minutes": latest_age, "threshold_minutes": stale_limit},
            )
        else:
            self.add(
                "supabase.delta_run.freshness",
                "system",
                "supabase",
                "delta_run_freshness",
                "ok",
                f"Latest completed Supabase delta run age: {latest_age:.0f} min",
                {"age_minutes": latest_age, "threshold_minutes": stale_limit},
            )
        # Remonter la RAISON du dernier echec (extraite de notes.error) directement dans
        # l'alerte, pour un diagnostic immediat (ex : PG 21000 doublon d'upsert).
        if failed:
            latest_failed = failed[0]  # failed derive de delta_rows trie started_at desc
            notes = latest_failed.get("notes")
            if isinstance(notes, dict):
                reason = str(notes.get("error") or notes)[:300]
            elif notes:
                reason = str(notes)[:300]
            else:
                reason = "(sans detail)"
            failed_scope = latest_failed.get("scope") or "?"
            errors_message = (
                f"{len(failed)} app_delta_run en echec sur {len(delta_rows)} recents "
                f"- dernier ({failed_scope}): {reason}"
            )
            errors_details = {
                "failed_count": len(failed),
                "recent_count": len(delta_rows),
                "latest_scope": failed_scope,
                "latest_error": reason,
            }
        else:
            errors_message = f"0 app_delta_run en echec sur {len(delta_rows)} recents"
            errors_details = {"failed_count": 0, "recent_count": len(delta_rows)}
        self.add(
            "supabase.delta_run.errors",
            "system",
            "supabase",
            "delta_run_errors",
            "warning" if failed else "ok",
            errors_message,
            errors_details,
        )

    def check_console_jobs(self) -> None:
        if not self.supabase:
            return
        rows = self.supabase.get(
            "app_console_job",
            {
                "select": "id,job_type,status,requested_at,started_at,worker_id,error_message",
                "status": "in.(pending,running,error)",
                "order": "requested_at.desc",
                "limit": "200",
            },
        ) or []
        pending_stale = []
        running_stale = []
        error_recent = []
        pending_limit = float(self.args.console_pending_minutes)
        running_limit = float(self.args.console_running_minutes)
        error_window = float(self.args.console_error_window_minutes)
        for row in rows:
            status = row.get("status")
            if status == "pending":
                current_age = age_minutes(parse_iso(row.get("requested_at"))) or 0
                if current_age > pending_limit:
                    pending_stale.append(row)
            elif status == "running":
                current_age = age_minutes(parse_iso(row.get("started_at"))) or 0
                if current_age > running_limit:
                    running_stale.append(row)
            elif status == "error":
                # Anti-bruit : on ne compte que les erreurs recentes (les erreurs historiques
                # deja corrigees ne doivent plus polluer le signal courant).
                error_age = age_minutes(parse_iso(row.get("requested_at")))
                if error_age is None or error_age <= error_window:
                    error_recent.append(row)
        if running_stale:
            self.add(
                "console.jobs.running_stale",
                "system",
                "console",
                "running_jobs",
                "critical",
                f"{len(running_stale)} Console jobs running too long",
                {"count": len(running_stale), "threshold_minutes": running_limit},
            )
        else:
            self.add(
                "console.jobs.running_stale",
                "system",
                "console",
                "running_jobs",
                "ok",
                "No stale running Console jobs",
                {"threshold_minutes": running_limit},
            )
        self.add(
            "console.jobs.pending_stale",
            "system",
            "console",
            "pending_jobs",
            "warning" if pending_stale else "ok",
            f"{len(pending_stale)} Console jobs pending too long",
            {"count": len(pending_stale), "threshold_minutes": pending_limit},
        )
        self.add(
            "console.jobs.errors",
            "business",
            "console",
            "error_jobs",
            "warning" if error_recent else "ok",
            f"{len(error_recent)} Console jobs in error (last {error_window / 60:.0f}h)",
            {"count": len(error_recent), "window_minutes": error_window},
        )

    def check_backend_health(self) -> None:
        url = self.args.backend_health_url
        if not url:
            self.add("backend.health", "system", "backend", "health", "unknown", "Backend health URL not configured")
            return
        attempts = max(1, int(self.args.backend_health_attempts))
        last_error: str | None = None
        for attempt in range(1, attempts + 1):
            request = urllib.request.Request(url, method="GET")
            started = time.monotonic()
            try:
                with urllib.request.urlopen(request, timeout=self.args.backend_timeout_seconds) as response:
                    elapsed_ms = int((time.monotonic() - started) * 1000)
                    payload = response.read().decode("utf-8", errors="replace")[:500]
                    if response.status != 200:
                        self.add(
                            "backend.health",
                            "system",
                            "backend",
                            "health",
                            "warning",
                            f"Backend health returned HTTP {response.status}",
                            {"url": url, "elapsed_ms": elapsed_ms, "attempt": attempt, "body": payload},
                        )
                    else:
                        message = "Backend health OK" if attempt == 1 else f"Backend health OK (reveil, tentative {attempt})"
                        self.add(
                            "backend.health",
                            "system",
                            "backend",
                            "health",
                            "ok",
                            message,
                            {"url": url, "elapsed_ms": elapsed_ms, "attempt": attempt},
                        )
                    return
            except Exception as exc:
                last_error = str(exc)
                # 1re tentative en echec = probable cold start Render : reveil puis nouvelle mesure.
                if attempt < attempts:
                    time.sleep(self.args.backend_retry_delay_seconds)
        self.add(
            "backend.health",
            "system",
            "backend",
            "health",
            "warning",
            f"Backend health unreachable after {attempts} attempt(s): {last_error}",
            {"url": url, "attempts": attempts, "error": last_error},
        )

    def check_sqlite_files(self) -> None:
        sqlite_specs = [
            ("sqlite.hektor", self.root / "data" / "hektor.sqlite", self.args.sqlite_freshness_minutes, "critical"),
            ("sqlite.phase2", self.root / "phase2" / "phase2.sqlite", self.args.sqlite_freshness_minutes, "critical"),
        ]
        for key, path, freshness_minutes, stale_status in sqlite_specs:
            if not path.exists():
                self.add(key, "system", "sqlite", "file_presence", "critical", f"SQLite missing: {path}", {"path": str(path)})
                continue
            mtime = file_mtime(path)
            current_age = age_minutes(mtime)
            details = {"path": str(path), "size_bytes": path.stat().st_size, "mtime": iso_utc(mtime) if mtime else None}
            if current_age is not None:
                details["age_minutes"] = current_age
            if current_age is not None and current_age > float(freshness_minutes):
                self.add(key, "system", "sqlite", "mtime", stale_status, f"SQLite stale: {path.name} age {current_age:.0f} min", details)
            else:
                self.add(key, "system", "sqlite", "mtime", "ok", f"SQLite fresh enough: {path.name}", details)
        wal_path = self.root / "data" / "hektor.sqlite-wal"
        if wal_path.exists():
            size_mb = wal_path.stat().st_size / (1024 * 1024)
            status = "critical" if size_mb > self.args.wal_critical_mb else "warning" if size_mb > self.args.wal_warning_mb else "ok"
            self.add(
                "sqlite.hektor.wal_size",
                "system",
                "sqlite",
                "wal_size",
                status,
                f"Hektor WAL size: {size_mb:.1f} MB",
                {"path": str(wal_path), "size_mb": size_mb, "warning_mb": self.args.wal_warning_mb, "critical_mb": self.args.wal_critical_mb},
            )

    def check_local_logs(self) -> None:
        tmp_dir = self.root / ".tmp"
        console_log_dir = self.root / "Console" / "logs"
        latest_pipeline = newest_file(tmp_dir, "full_pipeline_*.log")
        if not latest_pipeline:
            self.add("logs.pipeline.latest", "system", "logs", "pipeline_log", "warning", "No full pipeline log found", {"directory": str(tmp_dir)})
        else:
            mtime = file_mtime(latest_pipeline)
            current_age = age_minutes(mtime) or 0
            tail = tail_text(latest_pipeline)
            has_error = simple_error_seen(tail)
            stale = current_age > float(self.args.pipeline_log_freshness_minutes)
            status = "warning" if has_error or stale else "ok"
            self.add(
                "logs.pipeline.latest",
                "system",
                "logs",
                "pipeline_log",
                status,
                f"Latest pipeline log: {latest_pipeline.name}",
                {"path": str(latest_pipeline), "age_minutes": current_age, "tail_has_error_token": has_error},
            )
        self._check_log_dir_size("logs.tmp.size", tmp_dir)
        self._check_log_dir_size("logs.console.size", console_log_dir)

    def _check_log_dir_size(self, status_key: str, directory: Path) -> None:
        if not directory.exists():
            self.add(status_key, "system", "logs", "log_dir_size", "warning", f"Log directory missing: {directory}", {"path": str(directory)})
            return
        size_mb = dir_size_bytes(directory) / (1024 * 1024)
        status = "warning" if size_mb > float(self.args.log_dir_warning_mb) else "ok"
        self.add(
            status_key,
            "system",
            "logs",
            "log_dir_size",
            status,
            f"Log directory size {size_mb:.1f} MB: {directory.name}",
            {"path": str(directory), "size_mb": size_mb, "warning_mb": self.args.log_dir_warning_mb},
        )

    def check_playwright_sessions(self) -> None:
        session_dir = self.root / "Console" / "sessions"
        expected = {
            "actions": "critical",
            "admin": "critical",
            "documents": "warning",
            "sync_light": "warning",
        }
        missing = []
        present = []
        for kind, missing_status in expected.items():
            path = session_dir / f"storage_state_{kind}.json"
            if path.exists():
                present.append(kind)
            else:
                missing.append({"kind": kind, "status": missing_status, "path": str(path)})
        if any(item["status"] == "critical" for item in missing):
            status = "critical"
        elif missing:
            status = "warning"
        else:
            status = "ok"
        self.add(
            "playwright.hektor.sessions",
            "system",
            "playwright",
            "hektor_sessions",
            status,
            f"Hektor Playwright sessions present={len(present)} missing={len(missing)}",
            {"present": present, "missing": missing},
        )
        matterport_path = self.root / "Console" / "matterport_storage_state.json"
        self.add(
            "playwright.matterport.session",
            "system",
            "playwright",
            "matterport_session",
            "ok" if matterport_path.exists() else "warning",
            "Matterport Playwright session present" if matterport_path.exists() else "Matterport Playwright session missing",
            {"path": str(matterport_path)},
        )

    def check_document_storage(self) -> None:
        path = Path(self.args.document_storage_path)
        if not path.exists():
            self.add(
                "documents.local_storage",
                "system",
                "documents",
                "storage_presence",
                "warning",
                f"Local document storage missing: {path}",
                {"path": str(path)},
            )
            return
        size_mb = dir_size_bytes(path) / (1024 * 1024)
        self.add(
            "documents.local_storage",
            "system",
            "documents",
            "storage_presence",
            "ok",
            f"Local document storage reachable: {path}",
            {"path": str(path), "size_mb": size_mb},
        )

    def add_summary(self) -> None:
        critical = sum(1 for result in self.results if result.status == "critical")
        warning = sum(1 for result in self.results if result.status == "warning")
        unknown = sum(1 for result in self.results if result.status == "unknown")
        status = "critical" if critical else "warning" if warning or unknown else "ok"
        severity = "critical" if critical else "warning" if warning else "unknown" if unknown else "info"
        self.add(
            "monitor.summary",
            "system",
            "monitor",
            "summary",
            status,
            f"GTI monitor summary: {critical} critical, {warning} warning, {unknown} unknown",
            {"critical": critical, "warning": warning, "unknown": unknown, "total_checks": len(self.results)},
            severity=severity,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GTI local read-only health supervisor.")
    parser.add_argument("--project-root", default=str(ROOT))
    # Backend en prod = Render (public), pas localhost. Surchargeable via GTI_BACKEND_HEALTH_URL
    # (ex : http://127.0.0.1:8000/health pour surveiller une instance locale de dev).
    parser.add_argument(
        "--backend-health-url",
        default=os.getenv("GTI_BACKEND_HEALTH_URL", "https://gti-backend-xlyf.onrender.com/health"),
    )
    # Timeout dedie plus large que le timeout global : Render peut sortir de veille (cold start).
    parser.add_argument("--backend-timeout-seconds", type=int, default=60)
    # Le monitor ping toutes les 2h -> backend souvent en veille. 1re tentative = reveil,
    # 2e = mesure reelle. Evite les faux "injoignable" dus au cold start Render.
    parser.add_argument("--backend-health-attempts", type=int, default=2)
    parser.add_argument("--backend-retry-delay-seconds", type=float, default=3.0)
    parser.add_argument("--vitrine-catalogue-url", default="https://gtiimmo.github.io/vitrine/exports/catalogue_vitrine.json")
    parser.add_argument("--vitrine-min-items", type=int, default=100)
    parser.add_argument("--vitrine-freshness-hours", type=float, default=30.0)
    parser.add_argument("--cron-stale-minutes", type=int, default=30)
    parser.add_argument("--document-storage-path", default=os.getenv("CONSOLE_LOCAL_ARCHIVE_ROOT", r"C:\Hektor\HektorConsoleDocuments"))
    parser.add_argument("--timeout-seconds", type=int, default=15)
    parser.add_argument("--supabase-freshness-minutes", type=int, default=30 * 60)
    parser.add_argument("--delta-error-window-minutes", type=int, default=24 * 60)
    parser.add_argument("--worker-stale-default-minutes", type=int, default=28 * 60)
    parser.add_argument(
        "--scheduled-tasks",
        default="GTI Quotidien,GTI Recherches Actives,GTI Health Monitor,GTI Relances Email",
        help="Noms des taches planifiees Windows a surveiller (separes par des virgules).",
    )
    parser.add_argument("--sqlite-freshness-minutes", type=int, default=30 * 60)
    parser.add_argument("--pipeline-log-freshness-minutes", type=int, default=30 * 60)
    parser.add_argument("--console-pending-minutes", type=int, default=60)
    parser.add_argument("--console-running-minutes", type=int, default=45)
    parser.add_argument("--console-error-window-minutes", type=int, default=48 * 60)
    parser.add_argument("--status-ttl-hours", type=float, default=24.0)
    parser.add_argument("--wal-warning-mb", type=int, default=512)
    parser.add_argument("--wal-critical-mb", type=int, default=1024)
    parser.add_argument("--log-dir-warning-mb", type=int, default=1024)
    parser.add_argument("--alert-email", default=os.getenv("GTI_ALERT_EMAIL", "frederic.gerphagnon@gti-immobilier.fr"))
    parser.add_argument("--alert-whatsapp", default=os.getenv("GTI_ALERT_WHATSAPP", "0658770893"))
    parser.add_argument("--no-alerts", action="store_true", help="Desactive l'envoi d'alertes sortantes.")
    parser.add_argument("--test-alert", action="store_true", help="Compose et affiche une alerte de test (aucun envoi).")
    parser.add_argument("--dry-run", action="store_true", help="Run checks but do not write to Supabase.")
    parser.add_argument("--emit-ok-events", action="store_true", help="Insert events for OK checks too.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--strict-exit", action="store_true", help="Exit non-zero on critical or unknown checks.")
    return parser


def configure_supabase(args: argparse.Namespace) -> SupabaseClient | None:
    project_root = Path(args.project_root)
    load_env_file(project_root / ".env")
    load_env_file(project_root / "backend" / ".env")
    load_env_file(project_root / "apps" / "hektor-v1" / ".env")
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not service_key:
        return None
    return SupabaseClient(url, service_key, timeout_seconds=args.timeout_seconds)


def write_results(
    supabase: SupabaseClient | None,
    results: list[CheckResult],
    emit_ok_events: bool,
    status_ttl_hours: float = 24.0,
    alerter: "Alerter | None" = None,
) -> tuple[bool, str | None]:
    if not supabase:
        return False, "Supabase writes skipped"
    try:
        # Etats precedents (avant upsert) pour dedupliquer les events : on n'insere un
        # event que sur CHANGEMENT d'etat, pas a chaque run (fini les memes warnings 12x/jour).
        previous_status: dict[str, Any] = {}
        try:
            prev_rows = supabase.get("app_monitor_status", {"select": "status_key,status", "limit": "2000"})
            for prev_row in prev_rows or []:
                previous_status[prev_row.get("status_key")] = prev_row.get("status")
        except Exception:
            previous_status = {}

        supabase.upsert_status([result.status_row() for result in results])

        problem_states = {"warning", "critical", "unknown"}
        event_rows = []
        for result in results:
            was = previous_status.get(result.status_key)
            changed = was != result.status
            # Event si : mode verbeux, OU transition impliquant un etat problematique
            # (nouveau probleme, aggravation, ou resolution).
            if emit_ok_events or (changed and (result.status in problem_states or was in problem_states)):
                event_rows.append(result.event_row())
        supabase.insert_events(event_rows)

        # TTL : purge des statuts obsoletes (cle resolue ou plus emise depuis > ttl).
        if status_ttl_hours and status_ttl_hours > 0:
            try:
                cutoff = iso_utc(utc_now() - timedelta(hours=status_ttl_hours))
                supabase.purge_stale_status(cutoff)
            except Exception:
                pass  # purge best-effort : ne doit pas faire echouer l'ecriture des statuts

        # Alerte sortante : uniquement sur BASCULE vers critical (nouvelle cle critique),
        # pas a chaque run tant que le probleme persiste. Best-effort : n'echoue jamais.
        if alerter is not None:
            try:
                newly_critical = [
                    result
                    for result in results
                    if result.status == "critical" and previous_status.get(result.status_key) != "critical"
                ]
                had_critical = any(state == "critical" for state in previous_status.values())
                has_critical = any(result.status == "critical" for result in results)
                if newly_critical:
                    alerter.dispatch(newly_critical, kind="critical")
                elif had_critical and not has_critical:
                    alerter.dispatch([], kind="recovery")
            except Exception:
                pass  # alerting best-effort

        return True, None
    except Exception as exc:
        return False, str(exc)


def print_report(results: list[CheckResult], as_json: bool) -> None:
    if as_json:
        print(json.dumps([result.status_row() for result in results], ensure_ascii=True, indent=2))
        return
    for result in results:
        print(f"[{result.status.upper():8}] {result.status_key}: {result.message}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    supabase = configure_supabase(args)
    alerter = Alerter(args)
    if args.test_alert:
        sample = CheckResult(
            status_key="test.critical",
            domain="system",
            component="test",
            check_name="test",
            status="critical",
            severity="critical",
            message="Alerte de TEST du canal de monitoring (aucun incident reel).",
        )
        alerter.dispatch([sample], kind="critical", dry_run=True)
        return 0
    monitor = Monitor(args, supabase)
    results = monitor.run()
    if args.dry_run:
        wrote, write_error = False, None
    else:
        wrote, write_error = write_results(supabase, results, args.emit_ok_events, args.status_ttl_hours, alerter)
    if args.dry_run:
        results.append(
            CheckResult(
                status_key="monitor.supabase_write",
                domain="system",
                component="monitor",
                check_name="supabase_write",
                status="ok",
                severity="info",
                message="Dry-run mode: Supabase writes skipped intentionally",
                details={"dry_run": True},
            )
        )
    elif write_error:
        results.append(
            CheckResult(
                status_key="monitor.supabase_write",
                domain="system",
                component="monitor",
                check_name="supabase_write",
                status="critical",
                severity="critical",
                message=f"Unable to write monitor results to Supabase: {write_error}",
                details={"error": write_error},
            )
        )
    elif wrote:
        results.append(
            CheckResult(
                status_key="monitor.supabase_write",
                domain="system",
                component="monitor",
                check_name="supabase_write",
                status="ok",
                severity="info",
                message="Monitor results written to Supabase",
            )
        )
    print_report(results, args.json)
    if args.strict_exit and any(result.status in {"critical", "unknown"} for result in results):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
