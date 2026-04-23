from __future__ import annotations

import argparse
import base64
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
VITRINE_DIR = ROOT / "Ecrans Android"

PROPERTY_TYPE_LABELS = {
    "1": "Maison",
    "2": "Appartement",
    "3": "Parking / Garage",
    "4": "Bureau",
    "5": "Terrain",
    "6": "Local",
    "7": "Immeuble",
    "8": "Divers",
    "9": "Programme neuf",
    "10": "Loft / Atelier",
    "11": "Boutique",
    "12": "Appartement meublé",
    "13": "Maison meublée",
    "14": "Garage",
    "15": "Parking",
    "16": "Local professionnel",
    "17": "Chalet",
    "18": "Bâtiment",
    "19": "Demeure",
    "20": "Propriété",
    "21": "Mas",
    "22": "Hôtel particulier",
    "23": "Commerce",
    "24": "Immeuble",
    "25": "Villa",
    "26": "Studio",
    "27": "Duplex",
    "28": "Triplex",
    "29": "Atelier",
    "30": "Ferme",
}


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def parse_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def as_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        number = float(str(value).replace(",", "."))
    except ValueError:
        return None
    if number <= 0:
        return None
    return round(number)


def as_price(value: Any) -> float:
    if value in (None, ""):
        return 0
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return 0


def visible_photos(images_json: str | None, listing_photo: str | None, max_photos: int) -> list[str]:
    photos: list[str] = []
    seen: set[str] = set()

    def add(url: str | None) -> None:
        text = str(url or "").strip()
        if not text or text in seen:
            return
        seen.add(text)
        photos.append(text)

    images = parse_json(images_json, [])
    if isinstance(images, list):
        ordered = sorted(
            [img for img in images if isinstance(img, dict)],
            key=lambda img: as_int(img.get("order")) or 9999,
        )
        for img in ordered:
            if str(img.get("visible", "1")).strip() == "0":
                continue
            add(img.get("path") or img.get("pathTumb") or img.get("url"))
            if len(photos) >= max_photos:
                return photos

    add(listing_photo)
    return photos[:max_photos]


def absolutize_url(url: str | None, base_url: str = "https://www.gti-immobilier.fr/") -> str:
    text = str(url or "").strip()
    if not text:
        return ""
    if text.startswith("//"):
        return "https:" + text
    if text.startswith(("http://", "https://")):
        return text
    return urljoin(base_url, text)


def collect_urls(value: Any) -> list[str]:
    urls: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for child in node.values():
                walk(child)
            return
        if isinstance(node, list):
            for child in node:
                walk(child)
            return
        if isinstance(node, str):
            text = node.strip()
            if text.startswith(("http://", "https://", "//", "/")):
                urls.append(absolutize_url(text))

    walk(value)
    return urls


def dpe_from_raw(*json_values: str | None) -> dict[str, str]:
    out = {"conso": "", "ges": ""}
    seen: set[str] = set()
    urls: list[str] = []

    for value in json_values:
        parsed = parse_json(value, None)
        if parsed is None:
            continue
        for url in collect_urls(parsed):
            if not url or url in seen:
                continue
            seen.add(url)
            urls.append(url)

    dpe_urls = [u for u in urls if "/wa/images/DPEImages/" in u or "dpe" in u.lower() or "ges" in u.lower()]
    for url in dpe_urls:
        filename = (url.rsplit("/", 1)[-1] or "").lower()
        if not out["conso"] and (
            filename.startswith("dpeg_web")
            or filename.startswith("dpe_")
            or "dpe_fr_cons_" in filename
        ):
            out["conso"] = url
            continue
        if not out["ges"] and (filename.startswith("ges_") or "dpe_fr_ges_" in filename):
            out["ges"] = url
            continue
        if out["conso"] and out["ges"]:
            break
    return out


def terrain_surface(terrain_json: str | None, fallback: Any) -> int | None:
    parsed = parse_json(terrain_json, {})
    if isinstance(parsed, dict):
        props = parsed.get("props")
        if isinstance(props, dict):
            for key in ("surfterrain", "surfaceTerrain", "terrain"):
                entry = props.get(key)
                if isinstance(entry, dict):
                    value = as_int(entry.get("value"))
                    if value:
                        return value
    return as_int(fallback)


def agency_label(row: sqlite3.Row) -> str:
    parts: list[str] = []
    agency = str(row["agence_nom"] or "").strip()
    agency_phone = str(row["agence_tel"] or "").strip()
    nego = " ".join(part for part in [row["nego_prenom"], row["nego_nom"]] if part).strip()
    nego_phone = str(row["nego_portable"] or "").strip()
    if agency:
        parts.append(agency)
    if agency_phone:
        parts.append(f"TEL : {agency_phone}")
    if nego:
        parts.append(f"NEGOCIATEUR EN CHARGE DU BIEN : {nego}")
    if nego_phone:
        parts.append(f"TEL : {nego_phone}")
    return " ".join(parts) or "GTI Immobilier"


def property_type_label(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "Bien immobilier"
    return PROPERTY_TYPE_LABELS.get(text, f"Type {text}" if text.isdigit() else text)


def build_items(limit: int | None, max_photos: int) -> list[dict[str, Any]]:
    conn = connect(PHASE2_DB)
    try:
        sql = """
        SELECT
            v.app_dossier_id,
            v.hektor_annonce_id,
            v.numero_dossier,
            v.numero_mandat,
            v.titre_bien,
            v.ville,
            v.code_postal,
            v.prix,
            v.surface,
            v.nb_pieces,
            v.nb_chambres,
            v.type_bien,
            v.surface_habitable_detail,
            v.surface_terrain_detail,
            v.terrasse_detail,
            v.garage_box_detail,
            v.date_maj,
            v.offre_type,
            v.statut_annonce,
            v.photo_url_listing,
            v.images_json,
            v.images_preview_json,
            v.annonce_list_raw_json,
            v.detail_raw_json,
            v.terrain_json,
            h.agence_tel,
            h.nego_nom,
            h.nego_prenom,
            h.nego_portable,
            COALESCE(v.agence_nom, h.agence_nom) AS agence_nom
        FROM app_view_generale v
        LEFT JOIN (
            SELECT
                a.hektor_annonce_id,
                ag.nom AS agence_nom,
                ag.tel AS agence_tel,
                n.nom AS nego_nom,
                n.prenom AS nego_prenom,
                n.portable AS nego_portable
            FROM hektor.hektor_annonce a
            LEFT JOIN hektor.hektor_agence ag ON ag.hektor_agence_id = a.hektor_agence_id
            LEFT JOIN hektor.hektor_negociateur n ON n.hektor_negociateur_id = a.hektor_negociateur_id
        ) h ON h.hektor_annonce_id = CAST(v.hektor_annonce_id AS TEXT)
        WHERE COALESCE(v.archive, '0') = '0'
          AND COALESCE(v.diffusable, '0') = '1'
          AND LOWER(COALESCE(v.statut_annonce, '')) IN ('actif', 'sous offre', 'sous compromis')
        ORDER BY datetime(v.date_maj) DESC, v.hektor_annonce_id DESC
        """
        conn.execute(f"ATTACH DATABASE '{HEKTOR_DB.as_posix()}' AS hektor")
        rows = conn.execute(sql).fetchall()
    finally:
        conn.close()

    items: list[dict[str, Any]] = []
    for row in rows[:limit]:
        surface = as_int(row["surface_habitable_detail"]) or as_int(row["surface"])
        item = {
            "id": f"HEKTOR_{row['hektor_annonce_id']}",
            "ref": row["numero_dossier"] or row["numero_mandat"] or str(row["hektor_annonce_id"]),
            "agence": agency_label(row),
            "title": row["titre_bien"] or "Bien immobilier",
            "nature": property_type_label(row["type_bien"]),
            "propertyType": property_type_label(row["type_bien"]),
            "city": " ".join(part for part in [row["ville"], row["code_postal"]] if part).strip(),
            "postalCode": row["code_postal"] or "",
            "price": as_price(row["prix"]),
            "surface": surface or 0,
            "rooms": as_int(row["nb_pieces"]) or 0,
            "bedrooms": as_int(row["nb_chambres"]) or 0,
            "offerType": row["offre_type"] or "VENTE",
            "status": "2",
            "state": str(row["statut_annonce"] or "").strip(),
            "photos": visible_photos(row["images_json"], row["photo_url_listing"], max_photos),
            "url": "https://groupe-gti-immobilier.la-boite-immo.com/",
            "updatedAt": row["date_maj"] or "",
            "phone": row["nego_portable"] or row["agence_tel"] or "",
            "weight": 0,
            "terrain": terrain_surface(row["terrain_json"], row["surface_terrain_detail"]) or 0,
            "parkingInterieur": as_int(row["garage_box_detail"]) or 0,
        }
        dpe = dpe_from_raw(
            row["images_json"],
            row["images_preview_json"],
            row["annonce_list_raw_json"],
            row["detail_raw_json"],
        )
        if dpe["conso"] or dpe["ges"]:
            item["dpe"] = dpe
        if str(row["terrasse_detail"] or "").strip().upper() in {"OUI", "YES", "TRUE", "1"}:
            item["terrasse"] = 1
        items.append(item)
    return items


def write_catalogue(items: list[dict[str, Any]], outputs: list[Path]) -> None:
    payload = {
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "items": items,
    }
    for output in outputs:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {output} items={len(items)}")


def read_github_token(token_file: Path) -> str:
    if not token_file.exists():
        raise RuntimeError(f"GitHub token file missing: {token_file}")
    token = token_file.read_text(encoding="utf-8").strip()
    if len(token) < 20:
        raise RuntimeError(f"Invalid GitHub token in: {token_file}")
    return token


def github_request(url: str, token: str, method: str = "GET", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "GTI-vitrine-export",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub {method} failed HTTP {exc.code}: {body[:300]}") from exc


def github_get_file_sha(owner: str, repo: str, path: str, branch: str, token: str) -> str:
    encoded_path = quote(path.strip("/"), safe="/")
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{encoded_path}?ref={quote(branch)}"
    try:
        payload = github_request(url, token=token)
    except RuntimeError as exc:
        if "HTTP 404" in str(exc):
            return ""
        raise
    return str(payload.get("sha") or "")


def push_file_to_github(local_file: Path, owner: str, repo: str, branch: str, dest_path: str, token_file: Path) -> None:
    token = read_github_token(token_file)
    encoded_path = quote(dest_path.strip("/"), safe="/")
    sha = github_get_file_sha(owner=owner, repo=repo, path=dest_path, branch=branch, token=token)
    payload = {
        "message": f"update {dest_path}",
        "content": base64.b64encode(local_file.read_bytes()).decode("ascii"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{encoded_path}"
    github_request(url, token=token, method="PUT", payload=payload)
    print(f"pushed {local_file} -> {owner}/{repo}@{branch}:{dest_path}")


def push_many_files_to_github(files: list[tuple[Path, str]], owner: str, repo: str, branch: str, token_file: Path) -> None:
    for local_file, dest_path in files:
        push_file_to_github(
            local_file=local_file,
            owner=owner,
            repo=repo,
            branch=branch,
            dest_path=dest_path,
            token_file=token_file,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporte le catalogue vitrine Android depuis les donnees projet locales.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-photos", type=int, default=20)
    parser.add_argument("--output", action="append", default=[])
    parser.add_argument("--push-github", action="store_true")
    parser.add_argument("--github-owner", default="GTIImmo")
    parser.add_argument("--github-repo", default="vitrine")
    parser.add_argument("--github-branch", default="main")
    parser.add_argument("--github-path", default="exports/catalogue_vitrine.json")
    parser.add_argument("--github-token-file", default="github_token.txt")
    parser.add_argument("--push-front", action="store_true")
    args = parser.parse_args()

    items = build_items(args.limit, args.max_photos)
    outputs = [Path(p) for p in args.output] or [
        VITRINE_DIR / "data" / "catalogue_vitrine.json",
        VITRINE_DIR / "exports" / "catalogue_vitrine.json",
        VITRINE_DIR / "vitrine-main" / "data" / "catalogue_vitrine.json",
        VITRINE_DIR / "vitrine-main" / "exports" / "catalogue_vitrine.json",
    ]
    write_catalogue(items, outputs)
    if args.push_github:
        files_to_push: list[tuple[Path, str]] = [
            (outputs[1], args.github_path),
        ]
        if args.push_front:
            files_to_push.extend(
                [
                    (VITRINE_DIR / "index.html", "index.html"),
                    (VITRINE_DIR / "style.css", "style.css"),
                    (VITRINE_DIR / "script.js", "script.js"),
                ]
            )
        push_many_files_to_github(
            files=files_to_push,
            owner=args.github_owner,
            repo=args.github_repo,
            branch=args.github_branch,
            token_file=Path(args.github_token_file),
        )


if __name__ == "__main__":
    main()
