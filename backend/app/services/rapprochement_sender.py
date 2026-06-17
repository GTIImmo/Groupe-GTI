"""Chokepoint unique d'envoi de l'email de rapprochement (Lot C).

Utilisé par l'envoi manuel (POST /emails/rapprochement/send) ET par le worker de
relance. Centralise TOUS les garde-fous au même endroit :
- filtrage opt-out AVANT tout envoi (RGPD) ;
- plafond de volume quotidien (anti-spam, indépendant du DNS) + seuil d'alerte ;
- envoi réel uniquement si EMAIL_REAL_SEND_ENABLED ; sinon dry-run forcé ;
- en-têtes List-Unsubscribe + List-Unsubscribe-Post ;
- persistance de l'envoi et des identifiants Gmail.

Aucun envoi réel n'a lieu tant que `email_real_send_enabled` est faux : on log un
dry-run via le service Google Workspace existant (réutilisé, non dupliqué).
"""

from __future__ import annotations

from typing import Any

from ..settings import Settings
from .email_tracking import EmailTrackingService
from .google_workspace_service import GoogleWorkspaceService
from .rapprochement_email import RapprochementEmailService

# Domaine Workspace : seul un négociateur @gti-immobilier.fr peut être expéditeur
# « send-as » (DWD). Sinon on retombe sur la boîte accueil (signée par le négociateur).
GTI_DOMAIN = "gti-immobilier.fr"
FALLBACK_SENDER = "accueil@gti-immobilier.fr"

# Statuts qui rendent un bien « déjà vu » pour cet acquéreur : on ne le repropose pas
# dans un nouvel email (il reste visible dans l'historique de l'espace client).
BLOCKING_STATUTS = {"propose", "proposé", "visite", "ecarte", "ecarté", "écarté", "refuse", "refusé"}


def _norm_email(value: str | None) -> str:
    return (value or "").strip().lower()


class RapprochementSender:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.tracking = EmailTrackingService(settings)
        self.renderer = RapprochementEmailService(settings)
        self.workspace = GoogleWorkspaceService(settings)

    def _resolve_dossier_ids(self, annonce_ids: list[int]) -> list[int]:
        """Mappe les hektor_annonce_id vers les app_dossier_id réels (ordre préservé)."""
        if not annonce_ids:
            return []
        ids = ",".join(str(a) for a in annonce_ids)
        rows = self.renderer._rest_get(
            "app_dossier_current",
            {"select": "app_dossier_id,hektor_annonce_id", "hektor_annonce_id": f"in.({ids})"},
        )
        by_annonce = {int(r["hektor_annonce_id"]): int(r["app_dossier_id"])
                      for r in rows if r.get("app_dossier_id") is not None and r.get("hektor_annonce_id") is not None}
        return [by_annonce[a] for a in annonce_ids if a in by_annonce]

    def _resolve_biens(self, annonce_ids: list[int]) -> list[dict[str, Any]]:
        """annonce_id -> {annonce_id, dossier_id, nego_email} (ordre préservé, biens connus seulement)."""
        if not annonce_ids:
            return []
        ids = ",".join(str(a) for a in annonce_ids)
        rows = self.renderer._rest_get(
            "app_dossier_current",
            {"select": "app_dossier_id,hektor_annonce_id,negociateur_email",
             "hektor_annonce_id": f"in.({ids})"},
        )
        by_annonce: dict[int, dict[str, Any]] = {}
        for r in rows:
            a = r.get("hektor_annonce_id")
            d = r.get("app_dossier_id")
            if a is None or d is None:
                continue
            by_annonce[int(a)] = {
                "annonce_id": int(a),
                "dossier_id": int(d),
                "nego_email": r.get("negociateur_email"),
            }
        return [by_annonce[a] for a in annonce_ids if a in by_annonce]

    def _fresh_filter(self, biens: list[dict[str, Any]], hektor_contact_id: str | None) -> list[dict[str, Any]]:
        """Garde uniquement les biens « frais » : jamais proposés/écartés/refusés à cet acquéreur.

        Filtrage par hektor_contact_id (stable, robuste à l'édition de la recherche qui
        change contact_search_key). Sans contact_id, on ne peut pas filtrer -> tout est frais.
        """
        if not hektor_contact_id or not biens:
            return biens
        dossier_ids = sorted({b["dossier_id"] for b in biens})
        ids = ",".join(str(d) for d in dossier_ids)
        try:
            rows = self.renderer._rest_get(
                "app_bien_acquereur_statut",
                {"select": "app_dossier_id,status", "hektor_contact_id": f"eq.{hektor_contact_id}",
                 "app_dossier_id": f"in.({ids})"},
            )
        except Exception:
            return biens  # en cas d'erreur de lecture, on ne bloque pas l'envoi
        blocked = {int(r["app_dossier_id"]) for r in rows
                   if r.get("app_dossier_id") is not None
                   and _norm_email(r.get("status")).strip() in BLOCKING_STATUTS}
        return [b for b in biens if b["dossier_id"] not in blocked]

    def send_grouped(
        self,
        *,
        recipient_email: str,
        annonce_ids: list[int],
        variante: str = "pull",
        contact_search_key: str | None = None,
        hektor_contact_id: str | None = None,
        prenom: str | None = None,
        civilite: str | None = None,
        criteres: str | None = None,
        custom_intro: str | None = None,
        dry_run: bool = True,
        relance_type: str | None = None,
        created_by: str | None = None,
        fallback_sender_email: str | None = None,
    ) -> dict[str, Any]:
        """Envoi « 1 email par négociateur de mandat ».

        1) Ne garde que les biens frais (jamais proposés/écartés à cet acquéreur).
        2) Regroupe par négociateur du MANDAT (app_dossier_current.negociateur_email).
        3) Pour chaque groupe : 1 email envoyé DEPUIS la boîte du négociateur (send-as @gti),
           repli sur accueil@ si le négociateur n'a pas de boîte Workspace.
        Réutilise self.send() par groupe : opt-out, plafond, tracking, List-Unsubscribe inchangés.
        """
        recipient = (recipient_email or "").strip()
        if not recipient:
            return {"ok": False, "skipped": "no_recipient", "grouped": True, "groups": []}
        if self.tracking.is_opted_out(recipient):
            return {"ok": False, "skipped": "opt_out", "recipient": recipient, "grouped": True, "groups": []}

        biens = self._resolve_biens(annonce_ids)
        if not biens:
            return {"ok": False, "skipped": "no_bien", "grouped": True, "groups": []}

        fresh = self._fresh_filter(biens, hektor_contact_id)
        if not fresh:
            # Tous les biens ont déjà été vus/proposés : rien de neuf à envoyer.
            return {"ok": False, "skipped": "no_fresh_bien", "grouped": True, "groups": []}

        # Regroupement par expéditeur (négociateur du mandat, ou accueil@ en repli).
        fallback = (fallback_sender_email or "").strip() or FALLBACK_SENDER
        groups: dict[str, list[int]] = {}
        for b in fresh:
            nego = _norm_email(b.get("nego_email"))
            sender = b["nego_email"] if nego.endswith("@" + GTI_DOMAIN) else fallback
            groups.setdefault(sender, []).append(b["annonce_id"])

        results: list[dict[str, Any]] = []
        sent_annonce_ids: list[int] = []
        for sender, aids in groups.items():
            res = self.send(
                recipient_email=recipient, sender_email=sender, annonce_ids=aids,
                variante=variante, contact_search_key=contact_search_key,
                hektor_contact_id=hektor_contact_id, prenom=prenom, civilite=civilite,
                criteres=criteres, custom_intro=custom_intro, dry_run=dry_run,
                relance_type=relance_type, created_by=created_by,
            )
            res["senderEmail"] = sender
            res["annonceIds"] = aids
            results.append(res)
            if res.get("ok"):
                sent_annonce_ids.extend(aids)

        any_ok = any(r.get("ok") for r in results)
        return {
            "ok": any_ok,
            "grouped": True,
            "dryRun": results[0].get("dryRun") if results else None,
            "groups": results,
            "groupCount": len(results),
            "sentCount": sum(1 for r in results if r.get("ok")),
            "sentAnnonceIds": sent_annonce_ids,
            "filteredCount": len(biens) - len(fresh),
        }

    def send(
        self,
        *,
        recipient_email: str,
        sender_email: str,
        annonce_ids: list[int],
        variante: str = "push",
        contact_search_key: str | None = None,
        hektor_contact_id: str | None = None,
        prenom: str | None = None,
        civilite: str | None = None,
        criteres: str | None = None,
        custom_intro: str | None = None,
        dry_run: bool = True,
        relance_type: str | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        recipient = (recipient_email or "").strip()
        if not recipient:
            return {"ok": False, "skipped": "no_recipient"}

        # 1) Opt-out (RGPD) : jamais d'envoi à un désinscrit.
        if self.tracking.is_opted_out(recipient):
            return {"ok": False, "skipped": "opt_out", "recipient": recipient}

        # 2) Mode d'envoi : réel uniquement si activé en conf ET demandé.
        real = bool(self.settings.email_real_send_enabled) and not dry_run
        effective_dry_run = not real

        # 3) Plafond quotidien (uniquement pour les envois réels).
        daily_count = 0
        cap_alert = False
        if real:
            daily_count = self.tracking.count_real_sends_today()
            if daily_count >= int(self.settings.email_daily_send_cap):
                return {"ok": False, "skipped": "daily_cap",
                        "dailyCount": daily_count, "cap": self.settings.email_daily_send_cap}
            cap_alert = daily_count >= int(self.settings.email_daily_send_alert)

        # 4) Résoudre annonce_id (Hektor) -> app_dossier_id réel, pour que les biens
        #    enregistrés correspondent aux tokens ❤️/✕ (qui portent l'app_dossier_id)
        #    et au ciblage du worker de relance.
        dossier_ids = self._resolve_dossier_ids(annonce_ids)

        # Résout l'index de recherche (stable) depuis la clé, encore valide à l'envoi.
        search_index = None
        if contact_search_key:
            try:
                rows = self.renderer._rest_get(
                    "app_contact_search_current",
                    {"select": "search_index", "contact_search_key": f"eq.{contact_search_key}", "limit": "1"})
                if rows and rows[0].get("search_index") is not None:
                    search_index = int(rows[0]["search_index"])
            except Exception:
                pass

        # 5) Création de l'envoi (statut dépend du mode).
        envoi = self.tracking.create_envoi(
            contact_search_key=contact_search_key, hektor_contact_id=hektor_contact_id,
            recipient_email=recipient, sender_email=sender_email, variante=variante,
            subject="", dossier_ids=dossier_ids, dry_run=effective_dry_run, created_by=created_by,
            search_index=search_index,
        )
        envoi_id = envoi["id"]

        # 5) Rendu du template avec l'id d'envoi réel (liens trackés) + variation relance.
        rendered = self.renderer.render_preview(
            annonce_ids=annonce_ids, variante=variante, prenom=prenom, civilite=civilite,
            criteres=criteres, envoi_id=envoi_id, relance_type=relance_type, custom_intro=custom_intro,
            hektor_contact_id=hektor_contact_id,
        )

        # 6) En-têtes de désinscription 1-clic.
        headers = self.tracking.list_unsubscribe_headers(envoi_id)

        # 7) Envoi via Google Workspace (réel ou dry-run loggé).
        result = self.workspace.send_gmail_message(
            subject_email=sender_email, to=[recipient], subject=rendered["subject"],
            body_text=rendered["text"], body_html=rendered["html"], reply_to=sender_email,
            extra_headers=headers, dry_run=effective_dry_run,
            related_entity_type="contact", related_entity_id=hektor_contact_id,
        )

        if real and result.get("ok"):
            self.tracking.mark_sent(envoi_id, gmail_message_id=result.get("messageId"),
                                    gmail_thread_id=result.get("threadId"))

        return {
            "ok": bool(result.get("ok")), "dryRun": effective_dry_run, "envoiId": envoi_id,
            "subject": rendered["subject"], "listUnsubscribe": headers.get("List-Unsubscribe"),
            "dailyCount": daily_count + (1 if real and result.get("ok") else 0),
            "dailyCap": self.settings.email_daily_send_cap, "capAlert": cap_alert,
            "messageId": result.get("messageId"), "relanceType": relance_type,
        }
