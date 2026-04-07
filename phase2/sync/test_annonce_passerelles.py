from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hektor_pipeline.common import Settings

DEFAULT_ID_ANNONCE = "61909"
DEFAULT_TARGETS: tuple[tuple[str, str], ...] = (
    ("bienicidirect", "5"),
    ("leboncoinDirect", "42"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Teste l'ajout des passerelles agence pour une annonce Hektor.")
    parser.add_argument("--id-annonce", default=DEFAULT_ID_ANNONCE, help="ID Hektor de l'annonce")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env()
    targets = [{"portal_key": portal_key, "hektor_broadcast_id": broadcast_id} for portal_key, broadcast_id in DEFAULT_TARGETS]

    session = requests.Session()

    auth_response = session.post(
        f"{settings.base_url}/Api/OAuth/Authenticate/",
        params={
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "grant_type": "client_credentials",
        },
        timeout=settings.timeout,
    )
    auth_response.raise_for_status()
    access_token = auth_response.json()["access_token"]

    sso_response = session.post(
        f"{settings.base_url}/Api/OAuth/Sso/",
        params={
            "token": access_token,
            "scope": "sso",
            "client_id": settings.client_id,
        },
        timeout=settings.timeout,
    )
    sso_response.raise_for_status()
    jwt = sso_response.json()["jwt"]

    results: list[dict[str, object]] = []
    for target in targets:
        response = session.request(
            "PUT",
            f"{settings.base_url}/Api/Passerelle/addAnnonceToPasserelle/",
            headers={"jwt": jwt},
            params={
                "idPasserelle": str(target["hektor_broadcast_id"]),
                "idAnnonce": str(args.id_annonce),
            },
            timeout=settings.timeout,
        )
        refresh = response.headers.get("x-refresh-token")
        if refresh:
            jwt = refresh
        results.append(
            {
                "portal_key": str(target["portal_key"]),
                "idPasserelle": str(target["hektor_broadcast_id"]),
                "status_code": response.status_code,
                "body": response.text,
            }
        )

    print(
        json.dumps(
            {
                "id_annonce": str(args.id_annonce),
                "targets": targets,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
