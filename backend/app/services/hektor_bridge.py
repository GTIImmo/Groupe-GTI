from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from ..settings import Settings


class HektorBridgeService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _run_script(self, args: list[str], timeout: int = 120) -> dict[str, Any]:
        completed = subprocess.run(
            [self.settings.python_executable, *args],
            cwd=self.settings.project_root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()
        if completed.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=stderr or stdout or f"Commande Python echouee ({completed.returncode})",
            )
        if not stdout:
            return {"stdout": None, "stderr": stderr or None}
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {"stdout": stdout, "stderr": stderr or None}

    def _refresh_single_annonce(self, hektor_annonce_id: str) -> dict[str, Any]:
        if not hektor_annonce_id.strip():
            return {"ok": False, "error": "hektor_annonce_id manquant"}
        return self._run_script(
            [str(self.settings.refresh_single_annonce_script), "--id-annonce", hektor_annonce_id.strip()],
        )

    def apply(self, app_dossier_id: int, dry_run: bool, ensure_diffusable: bool) -> dict[str, Any]:
        args = [str(self.settings.hektor_writeback_script), "apply-targets", "--app-dossier-id", str(app_dossier_id)]
        if dry_run:
            args.append("--dry-run")
        if ensure_diffusable:
            args.append("--ensure-diffusable")
        payload = self._run_script(args)
        annonce_id = str(payload.get("hektor_annonce_id") or "").strip()
        if not dry_run and annonce_id:
            payload["refresh_single_annonce"] = self._refresh_single_annonce(annonce_id)
        return payload

    def accept(self, app_dossier_id: int, dry_run: bool) -> dict[str, Any]:
        args = [str(self.settings.hektor_writeback_script), "accept-request", "--app-dossier-id", str(app_dossier_id)]
        if dry_run:
            args.append("--dry-run")
        payload = self._run_script(args)
        annonce_id = str(payload.get("hektor_annonce_id") or "").strip()
        if not dry_run and annonce_id:
            payload["refresh_single_annonce"] = self._refresh_single_annonce(annonce_id)
        return payload
