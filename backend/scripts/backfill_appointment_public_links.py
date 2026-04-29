from __future__ import annotations

import argparse
import os
from pathlib import Path

from app.services.appointment_service import AppointmentService
from app.settings import get_settings


ROOT = Path(__file__).resolve().parents[2]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def iter_annonce_ids(service: AppointmentService, limit: int | None) -> list[int]:
    params = {
        "select": "hektor_annonce_id",
        "hektor_annonce_id": "not.is.null",
        "order": "hektor_annonce_id.asc",
    }
    if limit is not None:
        params["limit"] = str(limit)
    rows = service._rest_get("app_dossier_current", params=params)
    annonce_ids: list[int] = []
    seen: set[int] = set()
    for row in rows:
        value = row.get("hektor_annonce_id")
        try:
            annonce_id = int(value)
        except (TypeError, ValueError):
            continue
        if annonce_id in seen:
            continue
        seen.add(annonce_id)
        annonce_ids.append(annonce_id)
    return annonce_ids


def main() -> None:
    parser = argparse.ArgumentParser(description="Cree et enrichit les liens publics RDV avec les contacts nego/agence.")
    parser.add_argument("--annonce-id", action="append", dest="annonce_ids", help="Annonce Hektor a traiter. Peut etre repete.")
    parser.add_argument("--limit", type=int, default=None, help="Limite le nombre d'annonces lues depuis app_dossier_current.")
    args = parser.parse_args()

    load_env_file(ROOT / ".env")
    load_env_file(ROOT / "apps" / "hektor-v1" / ".env")

    settings = get_settings()
    service = AppointmentService(settings)

    annonce_ids = [int(value) for value in (args.annonce_ids or [])]
    if not annonce_ids:
        annonce_ids = iter_annonce_ids(service, args.limit)

    processed = 0
    enriched = 0
    for annonce_id in annonce_ids:
        try:
            link = service._ensure_link_for_annonce(annonce_id)
            dossier = service._read_dossier_by_annonce(annonce_id)
            before = {
                "negociateur_phone": str(link.get("negociateur_phone") or "").strip(),
                "negociateur_mobile": str(link.get("negociateur_mobile") or "").strip(),
                "agence_phone": str(link.get("agence_phone") or "").strip(),
                "agence_email": str(link.get("agence_email") or "").strip(),
            }
            updated = service._maybe_enrich_link_contacts(link, dossier)
            after = {
                "negociateur_phone": str(updated.get("negociateur_phone") or "").strip(),
                "negociateur_mobile": str(updated.get("negociateur_mobile") or "").strip(),
                "agence_phone": str(updated.get("agence_phone") or "").strip(),
                "agence_email": str(updated.get("agence_email") or "").strip(),
            }
            processed += 1
            if after != before and any(after.values()):
                enriched += 1
            print(f"annonce={annonce_id} token={updated.get('token')} enriched={after != before}")
        except Exception as exc:
            print(f"annonce={annonce_id} error={exc}")

    print(f"processed={processed} enriched={enriched}")


if __name__ == "__main__":
    main()
