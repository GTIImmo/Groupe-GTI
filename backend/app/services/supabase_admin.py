from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timezone
from typing import Any

import requests
from fastapi import HTTPException

from ..auth import AuthenticatedUser
from ..settings import Settings


class SupabaseAdminService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _admin_headers(self) -> dict[str, str]:
        return {
            "apikey": self.settings.supabase_service_role_key,
            "Authorization": f"Bearer {self.settings.supabase_service_role_key}",
            "Content-Type": "application/json",
        }

    def _rest_headers(self) -> dict[str, str]:
        return self._admin_headers()

    def _raise_for_response(self, response: requests.Response, fallback: str) -> None:
        if response.ok:
            return
        try:
            payload = response.json()
            message = payload.get("msg") or payload.get("message") or payload.get("error_description") or payload.get("error")
        except Exception:
            message = response.text.strip() or fallback
        raise HTTPException(status_code=response.status_code if response.status_code >= 400 else 500, detail=str(message))

    def _normalize_email(self, email: str | None) -> str:
        return str(email or "").strip().lower()

    def _is_workspace_email(self, email: str | None) -> bool:
        normalized = self._normalize_email(email)
        domain = self.settings.google_workspace_domain
        return bool(normalized and normalized.endswith(f"@{domain}"))

    def _rest_rows(self, table: str, params: dict[str, Any], fallback: str) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.settings.supabase_url}/rest/v1/{table}",
            headers=self._rest_headers(),
            params=params,
            timeout=30,
        )
        self._raise_for_response(response, fallback)
        return response.json() or []

    def _resolve_hektor_google_identity(self, email: str, role: str) -> dict[str, Any]:
        normalized = self._normalize_email(email)
        user_rows = [
            row for row in self._rest_rows(
                "app_user_directory",
                {
                    "select": "id_user,user_type,display_name,email",
                    "email": f"ilike.{normalized}",
                    "user_type": "eq.NEGO",
                    "limit": 10,
                },
                "Unable to resolve Hektor user directory",
            )
            if self._normalize_email(row.get("email")) == normalized and str(row.get("user_type") or "").upper() == "NEGO"
        ]
        agency_rows = [
            row for row in self._rest_rows(
                "app_hektor_negotiator_agency_directory",
                {
                    "select": "hektor_negociateur_id,hektor_user_id,hektor_agence_id,agence_id_user,agence_nom,display_name,email,is_active",
                    "email": f"ilike.{normalized}",
                    "is_active": "eq.true",
                    "limit": 20,
                },
                "Unable to resolve Hektor negotiator agency directory",
            )
            if self._normalize_email(row.get("email")) == normalized and row.get("is_active") is True
        ]
        metadata: dict[str, Any] = {
            "match_source": "auto_create_user",
            "user_directory_count": len(user_rows),
            "active_agency_directory_count": len(agency_rows),
        }

        conflict_reason: str | None = None
        selected_user = user_rows[0] if len(user_rows) == 1 else None
        selected_agency: dict[str, Any] | None = None

        if len(user_rows) > 1:
            conflict_reason = "multiple_active_hektor_users_for_email"
        elif selected_user:
            user_id = str(selected_user.get("id_user") or "").strip()
            matching_agencies = [row for row in agency_rows if str(row.get("hektor_user_id") or "").strip() == user_id]
            if len(matching_agencies) == 1:
                selected_agency = matching_agencies[0]
            elif len(matching_agencies) > 1:
                conflict_reason = "multiple_active_agencies_for_hektor_user"
            elif len(agency_rows) == 1:
                conflict_reason = "hektor_user_and_agency_directory_mismatch"
        elif len(agency_rows) == 1:
            selected_agency = agency_rows[0]
        elif len(agency_rows) > 1:
            conflict_reason = "multiple_active_agencies_for_email"

        if conflict_reason:
            metadata["conflict_reason"] = conflict_reason
            return {
                "link_status": "conflict",
                "hektor_user_id": None,
                "hektor_negociateur_id": None,
                "negociateur_email": None,
                "metadata_json": metadata,
            }

        if selected_agency:
            metadata["match_source"] = "app_hektor_negotiator_agency_directory"
            metadata["agence_nom"] = selected_agency.get("agence_nom")
            return {
                "link_status": "linked",
                "hektor_user_id": str(selected_agency.get("hektor_user_id") or "").strip() or None,
                "hektor_negociateur_id": str(selected_agency.get("hektor_negociateur_id") or "").strip() or None,
                "negociateur_email": self._normalize_email(selected_agency.get("email")) or normalized,
                "metadata_json": metadata,
            }

        if selected_user:
            metadata["match_source"] = "app_user_directory"
            return {
                "link_status": "linked",
                "hektor_user_id": str(selected_user.get("id_user") or "").strip() or None,
                "hektor_negociateur_id": None,
                "negociateur_email": self._normalize_email(selected_user.get("email")) or normalized,
                "metadata_json": metadata,
            }

        metadata["match_source"] = "workspace_only"
        if role == "commercial":
            metadata["conflict_reason"] = "commercial_without_hektor_match"
            return {
                "link_status": "pending",
                "hektor_user_id": None,
                "hektor_negociateur_id": None,
                "negociateur_email": None,
                "metadata_json": metadata,
            }

        return {
            "link_status": "linked",
            "hektor_user_id": None,
            "hektor_negociateur_id": None,
            "negociateur_email": None,
            "metadata_json": metadata,
        }

    def _sync_google_workspace_identity(self, *, user_id: str, email: str, role: str, is_active: bool) -> dict[str, Any] | None:
        normalized = self._normalize_email(email)
        if not self._is_workspace_email(normalized):
            if is_active:
                raise HTTPException(status_code=400, detail=f"Utilisateur actif hors domaine {self.settings.google_workspace_domain} refuse")
            return None

        resolved = self._resolve_hektor_google_identity(normalized, role) if is_active else {
            "link_status": "disabled",
            "hektor_user_id": None,
            "hektor_negociateur_id": None,
            "negociateur_email": None,
            "metadata_json": {"match_source": "disabled_profile"},
        }
        now = datetime.now(timezone.utc).isoformat()
        identity_payload = {
            "app_user_id": user_id,
            "google_email": normalized,
            "workspace_domain": self.settings.google_workspace_domain,
            "hektor_user_id": resolved["hektor_user_id"],
            "hektor_negociateur_id": resolved["hektor_negociateur_id"],
            "negociateur_email": resolved["negociateur_email"],
            "link_status": resolved["link_status"],
            "is_active": bool(is_active),
            "last_checked_at": now,
            "metadata_json": resolved["metadata_json"],
            "updated_at": now,
        }
        response = requests.post(
            f"{self.settings.supabase_url}/rest/v1/app_google_workspace_identity",
            headers={**self._rest_headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
            params={"on_conflict": "app_user_id"},
            json=[identity_payload],
            timeout=30,
        )
        self._raise_for_response(response, "Unable to upsert app_google_workspace_identity")
        rows = response.json() or []
        return rows[0] if rows else identity_payload

    # ---- Le REGISTRE DES NÉGOCIATEURS (04/11/2026) --------------------------------------------------------------
    # Frédéric : « penser au nouvel utilisateur dans l'app ». Audit : notice/AUDIT_REGISTRE_NEGOCIATEURS_2026-11-04.md
    # §9 et §22. À la création (et à la modification) d'un compte, il est relié TOUT DE SUITE à sa personne du registre :
    #   1. la personne choisie par l'admin (le cas tordu : Franck, compte @gti-immobilier.fr, fiche Hektor en gmail) ;
    #   2. sinon UNE personne au même e-mail (le sien ou celui d'une de ses fiches Hektor) ;
    #   3. sinon des personnes au même NOM -> rien n'est relié, l'écran propose de choisir (jamais de lien deviné) ;
    #   4. sinon une personne « sans fiche Hektor » est créée et signalée ; sa fiche s'y rattachera seule la nuit où
    #      elle arrivera chez Hektor (la nuit adopte par l'e-mail de la personne).
    # Le compte est déjà créé quand on arrive ici : un échec du registre ne le défait pas, il est RENDU à l'écran.

    _CIVILITE = re.compile(r"^\s*(m_mme|mr\.?/mme\.?|mme\.?|mlle\.?|mr\.?|m\.)\s+", re.IGNORECASE)

    def _cle_nom(self, nom: str | None) -> str:
        """La même clé que app_neg_cle_nom (la nuit) : civilité retirée, sans accents, minuscules, espaces réduits."""
        texte = self._CIVILITE.sub("", str(nom or ""))
        texte = "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")
        return re.sub(r"\s+", " ", texte.strip()).lower()

    def _journal_registre(self, personne: int, apres: str, *, evenement: str = "compte_app_relie", a_signaler: bool = False) -> None:
        response = requests.post(
            f"{self.settings.supabase_url}/rest/v1/app_negociateur_journal",
            headers=self._rest_headers(),
            json=[{"app_personne_id": personne, "evenement": evenement, "champ": "app_user_id", "apres": apres,
                   "a_signaler": a_signaler, "nuit": date.today().isoformat()}],
            timeout=30,
        )
        self._raise_for_response(response, "Unable to write app_negociateur_journal")

    def _relier_personne(self, personne: int, user_id: str, apres: str, *, a_signaler: bool = False) -> None:
        response = requests.patch(
            f"{self.settings.supabase_url}/rest/v1/app_negociateur_personne",
            headers=self._rest_headers(),
            params={"app_personne_id": f"eq.{personne}"},
            json={"app_user_id": user_id, "updated_at": datetime.now(timezone.utc).isoformat()},
            timeout=30,
        )
        self._raise_for_response(response, "Unable to link app_negociateur_personne")
        self._journal_registre(personne, apres, a_signaler=a_signaler)

    def lier_registre_negociateurs(self, *, user_id: str, email: str, nom: str, role: str, is_active: bool,
                                   personne_choisie: int | None = None, creer: bool = True) -> dict[str, Any]:
        email = self._normalize_email(email)
        personnes = self._rest_rows(
            "app_negociateur_personne",
            {"select": "app_personne_id,nom,email,type_personne,actif,app_user_id", "order": "app_personne_id.asc", "limit": 2000},
            "Unable to read app_negociateur_personne",
        )
        par_id = {int(p["app_personne_id"]): p for p in personnes}
        resume = lambda p, etat, **extra: {"etat": etat, "personne": int(p["app_personne_id"]), "nom": p.get("nom"), **extra}  # noqa: E731
        actuelle = next((p for p in personnes if str(p.get("app_user_id") or "") == str(user_id)), None)

        # 1. le choix de l'admin
        if personne_choisie is not None:
            cible = par_id.get(int(personne_choisie))
            if not cible:
                return {"etat": "erreur", "message": f"Personne {personne_choisie} absente du registre des négociateurs"}
            if actuelle and int(actuelle["app_personne_id"]) == int(personne_choisie):
                return resume(cible, "deja")
            if cible.get("app_user_id") and str(cible["app_user_id"]) != str(user_id):
                return resume(cible, "conflit", message="Cette personne est déjà reliée à un autre compte de l'app")
            if actuelle:
                # le compte change de personne : l'ancienne lâche le compte, et c'est écrit au journal
                response = requests.patch(
                    f"{self.settings.supabase_url}/rest/v1/app_negociateur_personne",
                    headers=self._rest_headers(),
                    params={"app_personne_id": f"eq.{int(actuelle['app_personne_id'])}"},
                    json={"app_user_id": None, "updated_at": datetime.now(timezone.utc).isoformat()},
                    timeout=30,
                )
                self._raise_for_response(response, "Unable to unlink app_negociateur_personne")
                self._journal_registre(int(actuelle["app_personne_id"]), f"{email} retiré (relié à {cible.get('nom')} par l'admin)")
            self._relier_personne(int(cible["app_personne_id"]), user_id, f"{email} (choix de l'admin)")
            return resume(cible, "relie", par="choix")
        if actuelle:
            return resume(actuelle, "deja")

        # 2. par l'e-mail : celui de la personne, ou celui d'une de ses fiches Hektor
        fiches = self._rest_rows(
            "app_negociateur_fiche",
            {"select": "app_personne_id", "email_vu": f"eq.{email}", "limit": 100},
            "Unable to read app_negociateur_fiche",
        ) if email else []
        ids = {int(p["app_personne_id"]) for p in personnes if self._normalize_email(p.get("email")) == email and email}
        ids |= {int(f["app_personne_id"]) for f in fiches}
        ids = {i for i in ids if par_id.get(i) and par_id[i].get("type_personne") != "agence"}
        if len(ids) == 1:
            cible = par_id[next(iter(ids))]
            if cible.get("app_user_id"):
                return resume(cible, "conflit", message="La personne de cet e-mail est déjà reliée à un autre compte de l'app")
            self._relier_personne(int(cible["app_personne_id"]), user_id, f"{email} (par l'e-mail)")
            return resume(cible, "relie", par="email")

        # 3. par le nom : on PROPOSE, on ne relie pas. ⚠ Même une personne déjà reliée à un AUTRE compte est proposée :
        #    Franck a deux comptes de l'app (gmail, relié ; @gti-immobilier.fr, non relié) -- créer une personne aurait
        #    fabriqué un doublon de lui (mesuré le 04/11). L'écran dit qu'elle est déjà reliée.
        cle = self._cle_nom(nom)
        candidats = [p for p in personnes if cle and self._cle_nom(p.get("nom")) == cle
                     and p.get("type_personne") not in ("agence", "inconnu")]
        if len(ids) > 1 or candidats:
            liste = [par_id[i] for i in sorted(ids)] if len(ids) > 1 else candidats
            return {"etat": "a_choisir", "candidats": [{"personne": int(p["app_personne_id"]), "nom": p.get("nom"), "email": p.get("email"),
                                                        "dejaRelie": bool(p.get("app_user_id"))} for p in liste]}

        # 4. personne inconnue : née dans l'app, sans fiche Hektor, signalée -- À LA CRÉATION du compte seulement (un compte
        #    existant qu'on modifie, comme le compte d'essai, ne fait pas naître une personne sans qu'on le demande)
        if not creer:
            return {"etat": "non_relie"}
        type_personne = {"admin": "administrateur", "commercial": "negociateur"}.get(str(role), "inconnu")
        response = requests.post(
            f"{self.settings.supabase_url}/rest/v1/app_negociateur_personne",
            headers={**self._rest_headers(), "Prefer": "return=representation"},
            json=[{"nom": str(nom or email).strip() or email, "email": email or None, "type_personne": type_personne,
                   "actif": bool(is_active), "origine": "app", "app_user_id": user_id,
                   "a_valider": f"née dans l'app le {date.today().strftime('%d/%m/%Y')} (compte {email}), sans fiche Hektor",
                   "cle_regroupement": f"app:{user_id}"}],
            timeout=30,
        )
        self._raise_for_response(response, "Unable to create app_negociateur_personne")
        cree = (response.json() or [{}])[0]
        self._journal_registre(int(cree["app_personne_id"]), f"{email} (personne née dans l'app, sans fiche Hektor)",
                               evenement="personne_nouvelle", a_signaler=True)
        return resume(cree, "cree")

    def _lier_registre_sans_echec(self, **params: Any) -> dict[str, Any]:
        try:
            return self.lier_registre_negociateurs(**params)
        except HTTPException as error:
            return {"etat": "erreur", "message": str(error.detail)}
        except Exception as error:  # noqa: BLE001 -- le compte est créé : on rend l'échec, on ne le défait pas
            return {"etat": "erreur", "message": str(error)}

    def load_profile(self, user: AuthenticatedUser) -> dict[str, Any]:
        params = {
            "select": "id,email,role,is_active,display_name,first_name,last_name",
            "or": f"(id.eq.{user.id},email.ilike.{user.email or ''})",
        }
        response = requests.get(
            f"{self.settings.supabase_url}/rest/v1/app_user_profile",
            headers=self._rest_headers(),
            params=params,
            timeout=30,
        )
        self._raise_for_response(response, "Unable to load app_user_profile")
        rows = response.json() or []
        for row in rows:
            if str(row.get("id") or "") == user.id:
                return row
        return rows[0] if rows else {}

    def assert_admin(self, user: AuthenticatedUser) -> dict[str, Any]:
        profile = self.load_profile(user)
        if not profile:
            raise HTTPException(status_code=403, detail=f"Profil admin introuvable pour {user.email or user.id}")
        role = str(profile.get("role") or "")
        is_active = profile.get("is_active")
        if role not in {"admin", "manager"} or is_active is not True:
            raise HTTPException(status_code=403, detail="Acces admin refuse")
        return profile

    def assert_can_apply_portals(self, user: AuthenticatedUser, authorization: str | None, app_dossier_id: int) -> tuple[dict[str, Any], bool]:
        """Qui peut envoyer les portails d'une annonce chez Hektor (lot 4, 03/11/2026).

        Regle de Frederic : un negociateur coche et decoche ses portails DES QUE l'annonce est
        diffusable (validee + Diffusable coche par la Direction). Admin et manager : comme avant.
        Commercial : seulement si
          · le dossier est `diffusable = '1'` dans app_dossier_current, et
          · il a acces au dossier, juge par la MEME regle que la base : app_console_can_access_dossier
            appelee AVEC SON PROPRE JETON (pas la cle de service).
        Rend (profil, privilegie). Un appel non privilegie ne doit jamais rendre une annonce
        diffusable ni toucher la validation : l'appelant le garantit.
        Voir notice/PLAN_DEV_LISTING_ANNONCES_LISTE_PUBLICITE_2026-11-03.md, lot 4.
        """
        profile = self.load_profile(user)
        if not profile or profile.get("is_active") is not True:
            raise HTTPException(status_code=403, detail="Compte utilisateur inactif ou introuvable")
        role = str(profile.get("role") or "")
        if role in {"admin", "manager"}:
            return profile, True
        if role != "commercial":
            raise HTTPException(status_code=403, detail="Acces refuse")
        rows = self._rest_rows(
            "app_dossier_current",
            {"select": "app_dossier_id,hektor_annonce_id,diffusable", "app_dossier_id": f"eq.{int(app_dossier_id)}", "limit": "1"},
            "Unable to load app_dossier_current",
        )
        if not rows:
            raise HTTPException(status_code=404, detail="Annonce introuvable")
        if str(rows[0].get("diffusable") or "").strip() != "1":
            raise HTTPException(status_code=403, detail="Annonce pas encore diffusable : la Direction doit la valider et cocher Diffusable")
        token = str(authorization or "").split(" ", 1)[1].strip() if " " in str(authorization or "") else ""
        if not token:
            raise HTTPException(status_code=401, detail="Authorization bearer manquant")
        response = requests.post(
            f"{self.settings.supabase_url}/rest/v1/rpc/app_console_can_access_dossier",
            headers={
                "apikey": self.settings.supabase_anon_key,
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"target_app_dossier_id": int(app_dossier_id), "target_hektor_annonce_id": str(rows[0].get("hektor_annonce_id") or "")},
            timeout=30,
        )
        if not response.ok or response.json() is not True:
            raise HTTPException(status_code=403, detail="Annonce hors de ton perimetre")
        return profile, False

    def assert_active_profile(self, user: AuthenticatedUser) -> dict[str, Any]:
        profile = self.load_profile(user)
        if not profile:
            raise HTTPException(status_code=403, detail=f"Profil utilisateur introuvable pour {user.email or user.id}")
        if profile.get("is_active") is not True:
            raise HTTPException(status_code=403, detail="Compte utilisateur inactif")
        return profile

    def _assert_workspace_subject_allowed(
        self,
        user: AuthenticatedUser,
        subject_email: str,
        *,
        account_label: str,
        action_label: str,
        forbidden_label: str,
    ) -> dict[str, Any]:
        profile = self.assert_active_profile(user)
        normalized_subject = self._normalize_email(subject_email)
        if not self._is_workspace_email(normalized_subject):
            raise HTTPException(status_code=400, detail=f"Compte {account_label} hors domaine {self.settings.google_workspace_domain}")

        role = str(profile.get("role") or "")
        if role in {"admin", "manager"}:
            return profile
        if role != "commercial":
            raise HTTPException(status_code=403, detail=f"Role non autorise pour {action_label}")

        identity_rows = self._rest_rows(
            "app_google_workspace_identity",
            {
                "select": "google_email,negociateur_email,link_status,is_active",
                "app_user_id": f"eq.{user.id}",
                "is_active": "eq.true",
                "limit": 1,
            },
            "Unable to read Google Workspace identity",
        )
        identity = identity_rows[0] if identity_rows else {}
        allowed_emails = {
            self._normalize_email(user.email),
            self._normalize_email(profile.get("email")),
            self._normalize_email(identity.get("google_email")),
            self._normalize_email(identity.get("negociateur_email")),
        }
        allowed_emails.discard("")
        if normalized_subject not in allowed_emails or identity.get("link_status") != "linked":
            raise HTTPException(status_code=403, detail=forbidden_label)
        return profile

    def assert_calendar_subject_allowed(self, user: AuthenticatedUser, subject_email: str) -> dict[str, Any]:
        return self._assert_workspace_subject_allowed(
            user,
            subject_email,
            account_label="Agenda",
            action_label="modifier Google Agenda",
            forbidden_label="Agenda Google non autorise pour cet utilisateur",
        )

    def assert_gmail_subject_allowed(self, user: AuthenticatedUser, subject_email: str) -> dict[str, Any]:
        return self._assert_workspace_subject_allowed(
            user,
            subject_email,
            account_label="Gmail",
            action_label="envoyer un email",
            forbidden_label="Gmail non autorise pour cet utilisateur",
        )

    def list_users(self) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.settings.supabase_url}/rest/v1/app_user_profile",
            headers=self._rest_headers(),
            params={"select": "*", "order": "is_active.desc,display_name.asc"},
            timeout=30,
        )
        self._raise_for_response(response, "Unable to list users")
        return response.json() or []

    def _load_profile_by_id(self, user_id: str) -> dict[str, Any]:
        response = requests.get(
            f"{self.settings.supabase_url}/rest/v1/app_user_profile",
            headers=self._rest_headers(),
            params={"select": "*", "id": f"eq.{user_id}", "limit": 1},
            timeout=30,
        )
        self._raise_for_response(response, "Unable to read user profile by id")
        rows = response.json() or []
        return rows[0] if rows else {}

    def _upsert_profile(self, profile_payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            f"{self.settings.supabase_url}/rest/v1/app_user_profile",
            headers={**self._rest_headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
            params={"on_conflict": "id"},
            json=[profile_payload],
            timeout=30,
        )
        self._raise_for_response(response, "Unable to upsert user profile")
        rows = response.json() or []
        if rows:
            return rows[0]
        profile = self._load_profile_by_id(str(profile_payload["id"]))
        if not profile:
            raise HTTPException(status_code=500, detail="Profil utilisateur non cree dans app_user_profile")
        return profile

    def create_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        email = self._normalize_email(payload["email"])
        if not self._is_workspace_email(email):
            raise HTTPException(status_code=400, detail=f"Creation utilisateur reservee aux comptes @{self.settings.google_workspace_domain}")
        display_name = payload.get("displayName") or " ".join(filter(None, [payload.get("firstName"), payload.get("lastName")])).strip() or payload["email"]
        auth_response = requests.post(
            f"{self.settings.supabase_url}/auth/v1/admin/users",
            headers=self._admin_headers(),
            json={
                "email": email,
                "password": payload["password"],
                "email_confirm": True,
                "user_metadata": {
                    "first_name": payload.get("firstName") or None,
                    "last_name": payload.get("lastName") or None,
                    "display_name": display_name,
                },
            },
            timeout=30,
        )
        self._raise_for_response(auth_response, "Unable to create auth user")
        auth_payload = auth_response.json()
        auth_user = auth_payload.get("user") or auth_payload
        user_id = auth_user.get("id")
        if not user_id:
            lookup_response = requests.get(
                f"{self.settings.supabase_url}/auth/v1/admin/users",
                headers=self._admin_headers(),
                params={"page": 1, "per_page": 1000},
                timeout=30,
            )
            self._raise_for_response(lookup_response, "Unable to read auth users after create")
            users = lookup_response.json().get("users") or []
            matched = next((item for item in users if self._normalize_email(item.get("email")) == email), None)
            user_id = matched.get("id") if matched else None
        if not user_id:
            raise HTTPException(status_code=500, detail="Supabase auth user id missing")

        profile_payload = {
            "id": user_id,
            "email": email,
            "role": payload["role"],
            "first_name": payload.get("firstName") or None,
            "last_name": payload.get("lastName") or None,
            "display_name": display_name,
            "is_active": payload.get("isActive", True),
            # PERIMETRE (12/10/2026) : jusqu'ou ce compte voit. « reseau » par
            # defaut, donc un compte cree sans cette case voit tout -- comme avant.
            "perimetre": payload.get("perimetre") or "reseau",
        }
        profile = self._upsert_profile(profile_payload)
        if str(profile.get("id") or "") != str(user_id):
            raise HTTPException(status_code=500, detail="Profil utilisateur incoherent apres creation")
        identity = self._sync_google_workspace_identity(
            user_id=user_id,
            email=email,
            role=payload["role"],
            is_active=payload.get("isActive", True),
        )
        registre = self._lier_registre_sans_echec(
            user_id=user_id, email=email, nom=display_name, role=payload["role"], is_active=payload.get("isActive", True),
            personne_choisie=payload.get("registrePersonneId"),
        )
        return {
            "ok": True,
            "userId": user_id,
            "email": email,
            "googleWorkspaceIdentity": {
                "linkStatus": identity.get("link_status") if identity else None,
                "hektorUserId": identity.get("hektor_user_id") if identity else None,
                "hektorNegociateurId": identity.get("hektor_negociateur_id") if identity else None,
            },
            "registre": registre,
        }

    def update_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        email = self._normalize_email(payload["email"])
        is_active = payload.get("isActive", True)
        if is_active and not self._is_workspace_email(email):
            raise HTTPException(status_code=400, detail=f"Utilisateur actif hors domaine @{self.settings.google_workspace_domain} refuse")
        display_name = payload.get("displayName") or " ".join(filter(None, [payload.get("firstName"), payload.get("lastName")])).strip() or email
        champs = {
            "email": email,
            "role": payload["role"],
            "first_name": payload.get("firstName") or None,
            "last_name": payload.get("lastName") or None,
            "display_name": display_name,
            "is_active": is_active,
        }
        # PERIMETRE (12/10/2026) : on ne l'ecrit QUE s'il est fourni. Sinon on
        # laisse celui du compte tel quel -- un ecran plus ancien qui n'envoie pas
        # la case ne doit pas remettre tout le monde a « reseau » sans le vouloir.
        if payload.get("perimetre"):
            champs["perimetre"] = payload["perimetre"]
        response = requests.patch(
            f"{self.settings.supabase_url}/rest/v1/app_user_profile",
            headers=self._rest_headers(),
            params={"id": f"eq.{payload['id']}"},
            json=champs,
            timeout=30,
        )
        self._raise_for_response(response, "Unable to update user profile")
        identity = self._sync_google_workspace_identity(
            user_id=payload["id"],
            email=email,
            role=payload["role"],
            is_active=is_active,
        )
        registre = self._lier_registre_sans_echec(
            user_id=payload["id"], email=email, nom=display_name, role=payload["role"], is_active=is_active,
            personne_choisie=payload.get("registrePersonneId"), creer=False,
        )
        return {
            "ok": True,
            "registre": registre,
            "googleWorkspaceIdentity": {
                "linkStatus": identity.get("link_status") if identity else None,
                "hektorUserId": identity.get("hektor_user_id") if identity else None,
                "hektorNegociateurId": identity.get("hektor_negociateur_id") if identity else None,
            },
        }

    def send_reset(self, email: str) -> dict[str, Any]:
        body: dict[str, Any] = {"email": email}
        if self.settings.app_base_url:
            body["redirect_to"] = self.settings.app_base_url
        response = requests.post(
            f"{self.settings.supabase_url}/auth/v1/recover",
            headers=self._admin_headers(),
            json=body,
            timeout=30,
        )
        self._raise_for_response(response, "Unable to send reset email")
        return {"ok": True}

    # ---- Suivi des runs d'agent IA (Phase 3, propose-only) --------------------
    # Best-effort : la tracabilite ne doit jamais faire echouer la generation.

    def insert_agent_run(self, row: dict[str, Any]) -> int | None:
        try:
            response = requests.post(
                f"{self.settings.supabase_url}/rest/v1/app_agent_run",
                headers={**self._rest_headers(), "Prefer": "return=representation"},
                json=[row],
                timeout=20,
            )
            if not response.ok:
                return None
            rows = response.json() or []
            return int(rows[0]["id"]) if rows and rows[0].get("id") is not None else None
        except Exception:
            return None

    def update_agent_run_decision(self, run_id: int, patch: dict[str, Any]) -> bool:
        try:
            response = requests.patch(
                f"{self.settings.supabase_url}/rest/v1/app_agent_run",
                headers=self._rest_headers(),
                params={"id": f"eq.{run_id}"},
                json=patch,
                timeout=20,
            )
            return response.ok
        except Exception:
            return False
