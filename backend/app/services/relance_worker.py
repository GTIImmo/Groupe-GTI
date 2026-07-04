"""Worker de relances automatiques (Lot C).

Lit les envois de rapprochement actifs, applique le moteur de décision
(`relance_engine.decide_relance`) et, le cas échéant, envoie UNE relance via le
chokepoint `RapprochementSender` (mêmes garde-fous : opt-out, plafond quotidien,
en-têtes List-Unsubscribe, dry-run/real selon conf).

Réconciliation avec la file de rappel HUMAINE `app_relance_rapprochement` (J+5) :
- relance auto envoyée OU état terminal -> on marque le rappel J+5 'fait' (pas de doublon) ;
- clic sans RDV -> on laisse / met à jour un rappel 'a_faire' pour contact humain (pas d'auto-relance).

Entrée CLI (à planifier en tâche/service Windows) :
    python -m app.services.relance_worker [--limit N] [--dry-run]
"""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime
from typing import Any

import requests

from ..settings import Settings, get_settings
from . import relance_engine
from .email_tracking import EmailTrackingService
from .rapprochement_sender import RapprochementSender


class RelanceWorker:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.tracking = EmailTrackingService(settings)
        self.sender = RapprochementSender(settings)

    def _get(self, path: str, params: dict[str, str]) -> list[dict[str, Any]]:
        r = requests.get(f"{self.settings.supabase_url}/rest/v1/{path}",
                         headers={"apikey": self.settings.supabase_service_role_key,
                                  "Authorization": f"Bearer {self.settings.supabase_service_role_key}"},
                         params=params, timeout=30)
        r.raise_for_status()
        return r.json() or []

    def _biens_of(self, envoi_id: str) -> list[int]:
        rows = self._get("app_email_envoi_bien", {"select": "app_dossier_id", "envoi_id": f"eq.{envoi_id}"})
        return [int(r["app_dossier_id"]) for r in rows if r.get("app_dossier_id") is not None]

    def _annonce_ids(self, dossier_ids: list[int]) -> list[int]:
        if not dossier_ids:
            return []
        ids = ",".join(str(d) for d in dossier_ids)
        rows = self._get("app_dossier_current",
                         {"select": "app_dossier_id,hektor_annonce_id", "app_dossier_id": f"in.({ids})"})
        return [int(r["hektor_annonce_id"]) for r in rows if r.get("hektor_annonce_id") is not None]

    def _contact(self, hektor_contact_id: str | None) -> dict[str, Any]:
        if not hektor_contact_id:
            return {}
        rows = self._get("app_contacts_current",
                         {"select": "civilite,prenom", "hektor_contact_id": f"eq.{hektor_contact_id}", "limit": "1"})
        return rows[0] if rows else {}

    def run(self, *, limit: int = 200, include_dry_run: bool = False, auto_send: bool = False) -> dict[str, Any]:
        now = datetime.now(UTC)
        max_relances = int(self.settings.email_relance_max_per_bien)

        params = {
            "select": "*",
            "statut": "not.in.(refuse,rdv,repondu,desinscrit)",
            "order": "created_at.asc",
            "limit": str(limit),
        }
        if not include_dry_run:
            params["dry_run"] = "eq.false"
        envois = self._get("app_email_envoi", params)

        stats = {"scanned": len(envois), "sent": 0, "skipped": 0, "alerts": 0,
                 "stopped": 0, "blocked": 0, "errors": 0, "details": []}

        for env in envois:
            # Isolation par envoi : un envoi defaillant ne doit plus abattre tout le batch
            # (avant ce correctif, une ValueError d'expediteur hors @gti faisait planter
            # le worker en exit 1 a chaque execution horaire, bloquant toutes les relances).
            try:
                decision = relance_engine.decide_relance(env, now, max_relances=max_relances)
                action, rtype, reason = decision["action"], decision["type"], decision["reason"]
                dossier_ids = self._biens_of(env["id"])

                if action == "skip":
                    stats["skipped"] += 1
                    if reason.startswith("terminal") or reason == "opt_out":
                        stats["stopped"] += 1
                        self.tracking.reconcile_human_relances(
                            contact_search_key=env.get("contact_search_key"), app_dossier_ids=dossier_ids,
                            status="fait", note=f"Auto: relance close ({reason})")
                    continue

                if action == "alert_human":
                    stats["alerts"] += 1
                    self.tracking.reconcile_human_relances(
                        contact_search_key=env.get("contact_search_key"), app_dossier_ids=dossier_ids,
                        status="a_faire", note="Clic « ça m'intéresse » sans RDV — rappeler le contact")
                    continue

                # action == "send"
                # GARDE-FOU (2026-07-04) : l'envoi AUTOMATIQUE de relance au CLIENT est
                # volontairement BLOQUE par defaut. A reprendre proprement plus tard (notamment
                # le repli d'expediteur hors @gti-immobilier.fr, cf. sender_email perso qui
                # faisait planter le worker). Reactivation deliberee via --allow-auto-send
                # ou RELANCE_AUTO_SEND_ENABLED=true.
                if not auto_send:
                    stats["blocked"] += 1
                    stats["details"].append({"envoi": env["id"], "action": "send", "type": rtype,
                                             "reason": reason, "blocked": "auto_send_disabled"})
                    continue

                annonce_ids = self._annonce_ids(dossier_ids)
                if not annonce_ids:
                    stats["skipped"] += 1
                    continue
                contact = self._contact(env.get("hektor_contact_id"))
                res = self.sender.send(
                    recipient_email=env.get("recipient_email") or "",
                    sender_email=env.get("sender_email") or "",
                    annonce_ids=annonce_ids, variante=env.get("variante") or "push",
                    contact_search_key=env.get("contact_search_key"), hektor_contact_id=env.get("hektor_contact_id"),
                    prenom=contact.get("prenom"), civilite=contact.get("civilite"),
                    relance_type=rtype, dry_run=not self.settings.email_real_send_enabled,
                )
                if res.get("skipped") == "daily_cap":
                    stats["details"].append({"envoi": env["id"], "skipped": "daily_cap"})
                    break  # plafond quotidien atteint : on arrête le batch
                if res.get("ok"):
                    stats["sent"] += 1
                    self.tracking.bump_relances_count(env["id"])
                    self.tracking.reconcile_human_relances(
                        contact_search_key=env.get("contact_search_key"), app_dossier_ids=dossier_ids,
                        status="fait", note=f"Auto: relance {rtype} envoyée")
                else:
                    stats["skipped"] += 1
                stats["details"].append({"envoi": env["id"], "action": action, "type": rtype,
                                         "reason": reason, "result": res.get("ok"), "dryRun": res.get("dryRun")})
            except Exception as exc:
                stats["errors"] += 1
                stats["details"].append({"envoi": env.get("id"), "error": str(exc)[:300]})
                continue

        return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Worker de relances email de rapprochement")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--include-dry-run", action="store_true",
                        help="Inclure les envois dry-run (tests). Par défaut, envois réels uniquement.")
    parser.add_argument("--allow-auto-send", action="store_true",
                        help="Autorise l'envoi AUTOMATIQUE de relance au client (BLOQUE par defaut "
                             "depuis 2026-07-04 ; a reprendre proprement avant reactivation).")
    args = parser.parse_args()
    settings = get_settings()
    auto_send = args.allow_auto_send or str(os.getenv("RELANCE_AUTO_SEND_ENABLED", "")).strip().lower() in ("1", "true", "yes", "on")
    stats = RelanceWorker(settings).run(limit=args.limit, include_dry_run=args.include_dry_run, auto_send=auto_send)
    print(f"[relance_worker] real_send={settings.email_real_send_enabled} auto_send={auto_send} "
          f"scanned={stats['scanned']} sent={stats['sent']} blocked={stats['blocked']} "
          f"alerts={stats['alerts']} stopped={stats['stopped']} skipped={stats['skipped']} errors={stats['errors']}")


if __name__ == "__main__":
    main()
