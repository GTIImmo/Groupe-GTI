from __future__ import annotations

import json
import re
import unicodedata
from typing import Any
from urllib.parse import quote

import requests
from fastapi import HTTPException

from ..settings import Settings


class HektorBridgeService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._cached_hektor_jwt: str | None = None

    def _rest_headers(self) -> dict[str, str]:
        return {
            "apikey": self.settings.supabase_service_role_key,
            "Authorization": f"Bearer {self.settings.supabase_service_role_key}",
            "Content-Type": "application/json",
        }

    def _normalize_text(self, value: str | None) -> str:
        if not value:
            return ""
        normalized = unicodedata.normalize("NFD", value)
        without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
        return re.sub(r"\s+", " ", without_marks).strip().lower()

    def _is_validation_approved(self, value: str | None) -> bool:
        normalized = self._normalize_text(value)
        return normalized in {"oui", "valide", "validee", "validation ok", "ok"}

    def _normalize_hektor_message(self, value: str | None) -> str:
        return re.sub(r"\s+", " ", (value or "").replace("Ãƒâ€š", " ")).strip()

    def _parse_maybe_json(self, text: str) -> Any:
        try:
            return json.loads(text)
        except Exception:
            return text

    def _raise_for_response(self, response: requests.Response, fallback: str) -> None:
        if response.ok:
            return
        try:
            payload = response.json()
            if isinstance(payload, dict):
                message = payload.get("message") or payload.get("error") or payload.get("msg")
            else:
                message = str(payload)
        except Exception:
            message = response.text.strip() or fallback
        raise HTTPException(status_code=response.status_code if response.status_code >= 400 else 500, detail=str(message))

    def _supabase_select_single(self, table: str, select: str, filters: dict[str, str]) -> dict[str, Any]:
        response = requests.get(
            f"{self.settings.supabase_url}/rest/v1/{table}",
            headers=self._rest_headers(),
            params={"select": select, **filters},
            timeout=30,
        )
        self._raise_for_response(response, f"Unable to load {table}")
        rows = response.json() or []
        if not rows:
            raise HTTPException(status_code=404, detail=f"{table} introuvable")
        return rows[0]

    def _load_dossier(self, app_dossier_id: int) -> dict[str, Any]:
        return self._supabase_select_single(
            "app_dossiers_current",
            "app_dossier_id,hektor_annonce_id,numero_dossier,validation_diffusion_state,agence_nom",
            {"app_dossier_id": f"eq.{app_dossier_id}"},
        )

    def _load_targets(self, app_dossier_id: int) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.settings.supabase_url}/rest/v1/app_diffusion_target",
            headers=self._rest_headers(),
            params={
                "select": "app_dossier_id,hektor_annonce_id,hektor_broadcast_id,portal_key,target_state",
                "app_dossier_id": f"eq.{app_dossier_id}",
                "order": "portal_key.asc",
            },
            timeout=30,
        )
        self._raise_for_response(response, "Unable to load diffusion targets")
        return response.json() or []

    def _load_agency_targets(self, agence_nom: str | None) -> list[dict[str, Any]]:
        if not agence_nom:
            return []
        response = requests.get(
            f"{self.settings.supabase_url}/rest/v1/app_diffusion_agency_target",
            headers=self._rest_headers(),
            params={
                "select": "agence_nom,portal_key,hektor_broadcast_id,is_active",
                "is_active": "eq.1",
            },
            timeout=30,
        )
        self._raise_for_response(response, "Unable to load agency targets")
        normalized_agency = self._normalize_text(agence_nom)
        rows = response.json() or []
        return [row for row in rows if self._normalize_text(str(row.get("agence_nom") or "")) == normalized_agency]

    def _replace_targets_from_agency_defaults(
        self,
        dossier: dict[str, Any],
        actor_name: str | None,
        actor_role: str,
        target_state: str,
    ) -> list[dict[str, Any]]:
        agency_targets = self._load_agency_targets(dossier.get("agence_nom"))
        if not agency_targets:
            raise HTTPException(status_code=400, detail=f"Aucun mapping agence pour '{dossier.get('agence_nom') or ''}'")
        delete_response = requests.delete(
            f"{self.settings.supabase_url}/rest/v1/app_diffusion_target",
            headers=self._rest_headers(),
            params={"app_dossier_id": f"eq.{dossier['app_dossier_id']}"},
            timeout=30,
        )
        self._raise_for_response(delete_response, "Unable to clear diffusion targets")
        payload = [
            {
                "app_dossier_id": dossier["app_dossier_id"],
                "hektor_annonce_id": dossier["hektor_annonce_id"],
                "hektor_broadcast_id": str(item["hektor_broadcast_id"]),
                "portal_key": item.get("portal_key"),
                "target_state": target_state,
                "source_ref": "accepted_default" if target_state == "enabled" else "console_seed",
                "note": "Activation par defaut suite a acceptation" if target_state == "enabled" else "Passerelles proposees par defaut dans la console diffusion",
                "requested_by_role": actor_role,
                "requested_by_name": actor_name,
            }
            for item in agency_targets
        ]
        insert_response = requests.post(
            f"{self.settings.supabase_url}/rest/v1/app_diffusion_target",
            headers={**self._rest_headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
            json=payload,
            timeout=30,
        )
        self._raise_for_response(insert_response, "Unable to seed diffusion targets from agency")
        return insert_response.json() or []

    def _authenticate_hektor(self) -> str:
        if not (self.settings.hektor_api_base_url and self.settings.hektor_client_id and self.settings.hektor_client_secret):
            raise HTTPException(status_code=500, detail="Configuration Hektor incomplete")
        base_url = self.settings.hektor_api_base_url.rstrip("/")
        auth_response = requests.post(
            f"{base_url}/Api/OAuth/Authenticate/",
            params={
                "client_id": self.settings.hektor_client_id,
                "client_secret": self.settings.hektor_client_secret,
                "grant_type": "client_credentials",
            },
            timeout=30,
        )
        auth_payload = self._parse_maybe_json(auth_response.text)
        if not auth_response.ok or not isinstance(auth_payload, dict) or not auth_payload.get("access_token"):
            raise HTTPException(status_code=500, detail=self._normalize_hektor_message(str(auth_payload)))
        sso_response = requests.post(
            f"{base_url}/Api/OAuth/Sso/",
            params={
                "token": str(auth_payload["access_token"]),
                "scope": "sso",
                "client_id": self.settings.hektor_client_id,
            },
            timeout=30,
        )
        sso_payload = self._parse_maybe_json(sso_response.text)
        if not sso_response.ok or not isinstance(sso_payload, dict) or not sso_payload.get("jwt"):
            raise HTTPException(status_code=500, detail=self._normalize_hektor_message(str(sso_payload)))
        self._cached_hektor_jwt = str(sso_payload["jwt"])
        return self._cached_hektor_jwt

    def _call_hektor(self, path: str, method: str = "GET", retry: bool = True) -> tuple[Any, str]:
        base_url = (self.settings.hektor_api_base_url or "").rstrip("/")
        if not self._cached_hektor_jwt:
            self._authenticate_hektor()
        response = requests.request(
            method,
            f"{base_url}{path}",
            headers={
                "Accept": "application/json",
                "jwt": self._cached_hektor_jwt or "",
            },
            timeout=60,
        )
        refresh_token = response.headers.get("x-refresh-token")
        if refresh_token:
            self._cached_hektor_jwt = refresh_token
        parsed = self._parse_maybe_json(response.text)
        if response.status_code == 403 and isinstance(parsed, str) and "expired token" in parsed.lower() and retry:
            self._cached_hektor_jwt = None
            self._authenticate_hektor()
            return self._call_hektor(path, method=method, retry=False)
        if not response.ok:
            raise HTTPException(status_code=500, detail=self._normalize_hektor_message(str(parsed)))
        return parsed, response.text

    def _fetch_annonce_detail(self, annonce_id: str) -> dict[str, Any]:
        parsed, _ = self._call_hektor(
            f"/Api/Annonce/AnnonceById/?id={annonce_id}&version={self.settings.hektor_api_version}",
            method="GET",
        )
        if not isinstance(parsed, dict):
            raise HTTPException(status_code=500, detail="Lecture annonce Hektor invalide")
        return parsed

    def _fetch_annonce_search_result(self, dossier: dict[str, Any]) -> dict[str, Any] | None:
        numero_dossier = str(dossier.get("numero_dossier") or "").strip()
        if not numero_dossier:
            return None
        search = quote(numero_dossier, safe="")
        parsed, _ = self._call_hektor(
            f"/Api/Annonce/searchAnnonces/?search={search}&strict=1&version={self.settings.hektor_api_version}",
            method="GET",
        )
        if not isinstance(parsed, dict):
            return None
        annonce_id = str(dossier.get("hektor_annonce_id") or "").strip()
        rows = parsed.get("liste")
        if not isinstance(rows, list):
            rows = parsed.get("data")
        if not isinstance(rows, list):
            return None
        for row in rows:
            if isinstance(row, dict) and str(row.get("id") or "") == annonce_id:
                return row
        return rows[0] if rows and isinstance(rows[0], dict) else None

    def _extract_diffusable(self, detail_payload: dict[str, Any]) -> str | None:
        if detail_payload.get("diffusable") is not None:
            return str(detail_payload.get("diffusable"))
        data = detail_payload.get("data")
        if isinstance(data, dict):
            candidates = [data.get("annonce"), data.get("keyData"), data]
            for candidate in candidates:
                if isinstance(candidate, dict) and candidate.get("diffusable") is not None:
                    return str(candidate.get("diffusable"))
        return None

    def _extract_validation_state(self, detail_payload: dict[str, Any]) -> str | None:
        def normalize_validation_value(value: Any) -> str | None:
            text = str(value).strip()
            if not text:
                return None
            lowered = text.lower()
            if lowered in {"1", "true", "oui", "ok", "valide", "validee", "validation ok"}:
                return "oui"
            if lowered in {"0", "false", "non", "invalide"}:
                return "non"
            return text

        validation_keys = (
            "validation",
            "valide",
            "validated",
            "isValid",
            "is_valid",
            "checkValid",
            "check_valid",
            "validationMandat",
            "validation_mandat",
        )
        for key in validation_keys:
            value = detail_payload.get(key)
            if value is not None:
                return normalize_validation_value(value)
        data = detail_payload.get("data")
        if isinstance(data, dict):
            for candidate in (data.get("annonce"), data.get("keyData"), data):
                if not isinstance(candidate, dict):
                    continue
                for key in validation_keys:
                    value = candidate.get(key)
                    if value is not None:
                        return normalize_validation_value(value)
        return None

    def _read_observed_diffusable(self, dossier: dict[str, Any]) -> str | None:
        annonce_id = str(dossier["hektor_annonce_id"])
        try:
            return self._extract_diffusable(self._fetch_annonce_detail(annonce_id))
        except Exception:
            search_row = self._fetch_annonce_search_result(dossier)
            return self._extract_diffusable(search_row or {})

    def _set_property_validation(self, dossier: dict[str, Any], state: int, dry_run: bool) -> dict[str, Any]:
        annonce_id = str(dossier["hektor_annonce_id"])
        before_payload: dict[str, Any] | None = None
        before_error: str | None = None
        try:
            before_payload = self._fetch_annonce_detail(annonce_id)
        except Exception as error:
            before_error = self._normalize_hektor_message(str(error))
        before_validation = self._extract_validation_state(before_payload or {}) if before_payload else None
        before_diffusable = self._extract_diffusable(before_payload or {}) if before_payload else None
        if dry_run:
            return {
                "hektor_annonce_id": annonce_id,
                "dry_run": True,
                "requested_state": state,
                "validation_result": "would_patch_property_validation",
                "observed_validation_before": before_validation,
                "observed_validation": before_validation,
                "observed_diffusable_before": before_diffusable,
                "observed_diffusable": before_diffusable,
                "read_before_error": before_error,
                "read_after_error": None,
                "error": None,
            }

        query = f"idAnnonce={requests.utils.quote(annonce_id, safe='')}&state={state}&version={requests.utils.quote(self.settings.hektor_api_version, safe='')}"
        parsed, raw_text = self._call_hektor(f"/Api/Annonce/PropertyValidation/?{query}", method="PATCH")
        response_payload = parsed if isinstance(parsed, dict) else None
        response_error = None
        if isinstance(response_payload, dict):
            raw_error = response_payload.get("error")
            response_error = self._normalize_hektor_message(str(raw_error)) if raw_error not in (None, "", False) else None

        after_payload: dict[str, Any] | None = None
        after_error: str | None = None
        try:
            after_payload = self._fetch_annonce_detail(annonce_id)
        except Exception as error:
            after_error = self._normalize_hektor_message(str(error))
        observed_validation = self._extract_validation_state(after_payload or {}) if after_payload else None
        if observed_validation is None and isinstance(response_payload, dict):
            observed_validation = self._extract_validation_state(response_payload)
        observed_diffusable = self._extract_diffusable(after_payload or {}) if after_payload else None
        if observed_diffusable is None and isinstance(response_payload, dict):
            observed_diffusable = self._extract_diffusable(response_payload)
        return {
            "hektor_annonce_id": annonce_id,
            "dry_run": False,
            "requested_state": state,
            "validation_result": "patched",
            "response_status": 200,
            "response_payload": response_payload,
            "response_preview": raw_text[:1000] if raw_text else "",
            "error": response_error,
            "observed_validation_before": before_validation,
            "observed_validation": observed_validation,
            "observed_diffusable_before": before_diffusable,
            "observed_diffusable": observed_diffusable,
            "read_before_error": before_error,
            "read_after_error": after_error,
        }

    def _fetch_annonce_broadcasts(self, annonce_id: str) -> list[dict[str, Any]]:
        parsed, _ = self._call_hektor(
            f"/Api/Annonce/ListPasserelles/?idAnnonce={requests.utils.quote(annonce_id, safe='')}",
            method="GET",
        )
        if isinstance(parsed, dict) and isinstance(parsed.get("data"), list):
            return [item for item in parsed["data"] if isinstance(item, dict)]
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        return []

    def _portal_is_enabled(self, row: dict[str, Any]) -> bool:
        for key in ("enabled", "is_enabled", "actif", "active", "selected", "checked"):
            value = row.get(key)
            if isinstance(value, bool):
                return value
            if value is not None and str(value).strip().lower() in {"1", "true", "oui", "yes", "active", "enabled"}:
                return True
        return False

    def _try_diffuse_request(self, annonce_id: str) -> str:
        attempts = [
            ("PATCH", {"idAnnonce": annonce_id, "version": self.settings.hektor_api_version}),
        ]
        errors: list[str] = []
        for method, params in attempts:
            query = "&".join(f"{key}={requests.utils.quote(str(value), safe='')}" for key, value in params.items())
            try:
                _, raw_text = self._call_hektor(f"/Api/Annonce/Diffuse/?{query}", method=method)
                return raw_text[:500] or f"{method} ok"
            except HTTPException as error:
                errors.append(f"{method} {params} => {self._normalize_hektor_message(str(error.detail))}")
        raise HTTPException(status_code=500, detail=" | ".join(errors))

    def _set_diffusable_state(self, dossier: dict[str, Any], requested: bool, dry_run: bool) -> dict[str, Any]:
        annonce_id = str(dossier["hektor_annonce_id"])
        current = self._read_observed_diffusable(dossier)
        requested_value = "1" if requested else "0"
        if current == requested_value:
            return {"changed": False, "result": "already_diffusable" if requested else "already_not_diffusable"}
        if dry_run:
            return {"changed": True, "result": "would_patch_diffuse"}
        try:
            response_preview = self._try_diffuse_request(annonce_id)
            observed = self._read_observed_diffusable(dossier)
            if observed == requested_value:
                return {"changed": True, "result": response_preview}
            return {"changed": True, "result": f"diffuse_unconfirmed: observed_diffusable={observed}; response={response_preview}"}
        except HTTPException as error:
            message = self._normalize_hektor_message(str(error.detail))
            try:
                if self._read_observed_diffusable(dossier) == requested_value:
                    return {"changed": True, "result": f"confirmed_after_diffuse_error: {message}"}
            except Exception:
                pass
            return {"changed": True, "result": f"diffuse_unconfirmed: {message}"}

    def _ensure_diffusable(self, dossier: dict[str, Any], dry_run: bool) -> dict[str, Any]:
        return self._set_diffusable_state(dossier, True, dry_run)

    def _apply_portal_change(self, action: str, annonce_id: str, broadcast_id: str) -> Any:
        path = "/Api/Passerelle/addAnnonceToPasserelle/" if action == "add" else "/Api/Passerelle/removeAnnonceToPasserelle/"
        method = "PUT" if action == "add" else "DELETE"
        query = f"idPasserelle={requests.utils.quote(broadcast_id, safe='')}&idAnnonce={requests.utils.quote(annonce_id, safe='')}"
        parsed, _ = self._call_hektor(f"{path}?{query}", method=method)
        return parsed

    def set_diffusable(self, app_dossier_id: int, diffusable: bool, dry_run: bool) -> dict[str, Any]:
        dossier = self._load_dossier(app_dossier_id)
        if dry_run:
            return {
                "app_dossier_id": dossier["app_dossier_id"],
                "hektor_annonce_id": str(dossier["hektor_annonce_id"]),
                "dry_run": True,
                "requested_diffusable": diffusable,
                "changed": True,
                "result": "would_patch_diffuse",
                "observed_diffusable": self._read_observed_diffusable(dossier),
                "error": None,
            }
        ensure_result = self._set_diffusable_state(dossier, diffusable, dry_run=False)
        observed_diffusable = self._read_observed_diffusable(dossier)
        expected = "1" if diffusable else "0"
        return {
            "app_dossier_id": dossier["app_dossier_id"],
            "hektor_annonce_id": str(dossier["hektor_annonce_id"]),
            "dry_run": False,
            "requested_diffusable": diffusable,
            "changed": bool(ensure_result["changed"]),
            "result": self._normalize_hektor_message(str(ensure_result["result"])),
            "observed_diffusable": observed_diffusable,
            "error": None if observed_diffusable == expected else f"Hektor n'a pas confirme diffusable = {expected} apres PATCH Diffuse.",
        }

    def set_validation(self, app_dossier_id: int, state: int, dry_run: bool) -> dict[str, Any]:
        dossier = self._load_dossier(app_dossier_id)
        result = self._set_property_validation(dossier, state, dry_run)
        return {
            "app_dossier_id": dossier["app_dossier_id"],
            **result,
        }

    def _run_apply(self, dossier: dict[str, Any], requested_by: str | None, dry_run: bool, ensure_diffusable_flag: bool, reset_to_agency_defaults: bool) -> dict[str, Any]:
        targets = self._load_targets(int(dossier["app_dossier_id"]))
        if (reset_to_agency_defaults or not targets) and dossier.get("agence_nom"):
            targets = self._replace_targets_from_agency_defaults(
                dossier,
                requested_by,
                "system" if reset_to_agency_defaults else "app",
                "enabled" if reset_to_agency_defaults else "disabled",
            )
        if not targets:
            raise HTTPException(status_code=400, detail=f"Aucune cible de diffusion pour app_dossier_id={dossier['app_dossier_id']}")

        diffusable_changed = False
        diffusable_result = "not_managed_in_console"
        observed_diffusable: str | None = None
        if ensure_diffusable_flag:
            try:
                ensure_result = self._ensure_diffusable(dossier, dry_run)
                diffusable_changed = bool(ensure_result["changed"])
                diffusable_result = self._normalize_hektor_message(str(ensure_result["result"]))
                if not dry_run:
                    try:
                        observed_diffusable = self._read_observed_diffusable(dossier)
                    except Exception as error:
                        observed_diffusable = None
                        diffusable_result = self._normalize_hektor_message(f"{diffusable_result} | detail_read_error: {error}")
                    if observed_diffusable != "1":
                        return {
                            "app_dossier_id": dossier["app_dossier_id"],
                            "hektor_annonce_id": str(dossier["hektor_annonce_id"]),
                            "dry_run": dry_run,
                            "diffusable_changed": diffusable_changed,
                            "diffusable_result": diffusable_result,
                            "observed_diffusable": observed_diffusable,
                            "validation_state": dossier.get("validation_diffusion_state"),
                            "validation_approved": self._is_validation_approved(dossier.get("validation_diffusion_state")),
                            "waiting_on_hektor": True,
                            "waiting_message": "En attente de mise a jour Hektor. Le bien n'est pas encore confirme en diffusable."
                            if self._is_validation_approved(dossier.get("validation_diffusion_state"))
                            else "Action Hektor non appliquee : l'annonce est encore en validation = non. Ouvre Hektor pour corriger la validation, puis relance.",
                            "current_enabled_count": 0,
                            "targets_count": len(targets),
                            "to_add_count": 0,
                            "to_remove_count": 0,
                            "applied": [],
                            "failed": [],
                            "pending": [],
                        }
            except Exception as error:
                return {
                    "app_dossier_id": dossier["app_dossier_id"],
                    "hektor_annonce_id": str(dossier["hektor_annonce_id"]),
                    "dry_run": dry_run,
                    "diffusable_changed": diffusable_changed,
                    "diffusable_result": self._normalize_hektor_message(str(error)),
                    "observed_diffusable": observed_diffusable,
                    "validation_state": dossier.get("validation_diffusion_state"),
                    "validation_approved": self._is_validation_approved(dossier.get("validation_diffusion_state")),
                    "waiting_on_hektor": True,
                    "waiting_message": "Action Hektor envoyee, mais le retour serveur n'est pas assez propre pour confirmer automatiquement le resultat.",
                    "current_enabled_count": 0,
                    "targets_count": len(targets),
                    "to_add_count": 0,
                    "to_remove_count": 0,
                    "applied": [],
                    "failed": [],
                    "pending": [],
                }

        to_add = [item for item in targets if item.get("target_state") == "enabled"]
        to_remove = [item for item in targets if item.get("target_state") == "disabled"]
        applied: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        for target in to_add:
            if dry_run:
                applied.append({"action": "add", "portal_key": target.get("portal_key"), "broadcast_id": target.get("hektor_broadcast_id"), "dry_run": True})
                continue
            try:
                parsed = self._apply_portal_change("add", str(dossier["hektor_annonce_id"]), str(target["hektor_broadcast_id"]))
                applied.append({"action": "add", "portal_key": target.get("portal_key"), "broadcast_id": target.get("hektor_broadcast_id"), "result": parsed})
            except Exception as error:
                failed.append({"action": "add", "portal_key": target.get("portal_key"), "broadcast_id": target.get("hektor_broadcast_id"), "error": self._normalize_hektor_message(str(error))})

        for target in to_remove:
            if dry_run:
                applied.append({"action": "remove", "portal_key": target.get("portal_key"), "broadcast_id": target.get("hektor_broadcast_id"), "dry_run": True})
                continue
            try:
                parsed = self._apply_portal_change("remove", str(dossier["hektor_annonce_id"]), str(target["hektor_broadcast_id"]))
                applied.append({"action": "remove", "portal_key": target.get("portal_key"), "broadcast_id": target.get("hektor_broadcast_id"), "result": parsed})
            except Exception as error:
                failed.append({"action": "remove", "portal_key": target.get("portal_key"), "broadcast_id": target.get("hektor_broadcast_id"), "error": self._normalize_hektor_message(str(error))})

        observed_broadcasts: list[dict[str, Any]] = []
        if not dry_run:
            try:
                observed_diffusable = self._read_observed_diffusable(dossier)
            except Exception as error:
                failed.append({"action": "read-detail", "error": self._normalize_hektor_message(str(error))})
            try:
                observed_broadcasts = self._fetch_annonce_broadcasts(str(dossier["hektor_annonce_id"]))
            except Exception as error:
                failed.append({"action": "read-broadcasts", "error": self._normalize_hektor_message(str(error))})

        return {
            "app_dossier_id": dossier["app_dossier_id"],
            "hektor_annonce_id": str(dossier["hektor_annonce_id"]),
            "dry_run": dry_run,
            "diffusable_changed": diffusable_changed,
            "diffusable_result": diffusable_result,
            "observed_diffusable": observed_diffusable,
            "validation_state": dossier.get("validation_diffusion_state"),
            "validation_approved": self._is_validation_approved(dossier.get("validation_diffusion_state")),
            "waiting_on_hektor": False,
            "waiting_message": None,
            "current_enabled_count": len(to_add),
            "targets_count": len(targets),
            "to_add_count": len(to_add),
            "to_remove_count": len(to_remove),
            "applied": applied,
            "failed": failed,
            "observed_broadcast_count": sum(1 for item in observed_broadcasts if self._portal_is_enabled(item)),
            "observed_broadcasts": observed_broadcasts,
            "pending": [],
        }

    def _accept_validation_first(self, dossier: dict[str, Any], requested_by: str | None, dry_run: bool) -> dict[str, Any]:
        validation = self._set_property_validation(dossier, 1, dry_run)
        observed_validation = str(validation.get("observed_validation") or "").strip() or None
        observed_diffusable = str(validation.get("observed_diffusable") or "").strip() or None
        validation_approved = self._is_validation_approved(observed_validation)
        if not validation_approved:
            return {
                "app_dossier_id": dossier["app_dossier_id"],
                "hektor_annonce_id": str(dossier["hektor_annonce_id"]),
                "dry_run": dry_run,
                "validation_result": validation.get("validation_result"),
                "observed_validation": observed_validation,
                "diffusable_changed": False,
                "diffusable_result": "skipped_until_validation_confirmed",
                "observed_diffusable": observed_diffusable,
                "validation_state": observed_validation,
                "validation_approved": False,
                "waiting_on_hektor": True,
                "waiting_message": "En attente de validation Hektor. La demande est acceptee, mais Hektor n'a pas encore confirme validation = oui.",
                "current_enabled_count": 0,
                "targets_count": 0,
                "to_add_count": 0,
                "to_remove_count": 0,
                "applied": [],
                "failed": [],
                "pending": [],
                "validation_response_status": validation.get("response_status"),
                "validation_error": validation.get("error"),
            }

        apply_result = self._run_apply(
            {
                **dossier,
                "validation_diffusion_state": observed_validation,
            },
            requested_by,
            dry_run,
            True,
            True,
        )
        return {
            **apply_result,
            "validation_result": validation.get("validation_result"),
            "observed_validation": observed_validation,
            "validation_state": observed_validation,
            "validation_approved": True,
            "validation_response_status": validation.get("response_status"),
            "validation_error": validation.get("error"),
        }

    def apply(self, app_dossier_id: int, dry_run: bool, ensure_diffusable: bool, requested_by: str | None = None) -> dict[str, Any]:
        dossier = self._load_dossier(app_dossier_id)
        return self._run_apply(dossier, requested_by, dry_run, ensure_diffusable, False)

    def accept(self, app_dossier_id: int, dry_run: bool, requested_by: str | None = None) -> dict[str, Any]:
        dossier = self._load_dossier(app_dossier_id)
        return self._accept_validation_first(dossier, requested_by, dry_run)
