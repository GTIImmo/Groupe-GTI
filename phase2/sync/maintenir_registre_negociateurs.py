"""REGISTRE DES NEGOCIATEURS, etape 2 (04/11/2026) -- LA MISE A JOUR DE NUIT.

Audit : notice/AUDIT_REGISTRE_NEGOCIATEURS_2026-11-04.md §12. La logique est TOUTE dans la base
(supabase/patch_registre_negociateurs_nuit_2026-11-04.sql, fonction app_negociateur_registre_maintenir) :
ce script ne fait que lui donner ce qu'elle ne peut pas savoir -- QUELLES fiches la liste de Hektor de
CETTE nuit contient -- puis il ecrit son compte rendu au journal du run.

LA PRESENCE CHEZ HEKTOR : raw_api_response (data/hektor.sqlite, lecture seule), listes `list_negos` et
`list_negos_inactive` relues chaque nuit par sync_raw.py. ⚠ Seule la DERNIERE reponse de chaque page est
gardee, et une page qui n'existe plus reste avec sa vieille date (mesure du 04/11 : pages 3-4 d'avril, 5-8 de
juin). On ne garde donc que les pages de la nuit : celles lues dans les 6 h qui precedent la plus recente.
Liste plus vieille que 36 h -> presence inconnue : la fonction ne marque alors AUCUNE absence (plancher).

⛔ INTERRUPTEUR APP_REGISTRE_NEGOCIATEURS (.env) : 0 ou absent = rien ; « blanc » = la fonction suit le meme
   chemin puis annule tout, seul le compte rendu sort ; 1 = elle ecrit.
⚠ AUCUNE requete chez Hektor. Etape NON BLOQUANTE dans le run : ratee, le registre garde la nuit d'avant.

Usage :
    python phase2/sync/maintenir_registre_negociateurs.py             (selon l'interrupteur)
    python phase2/sync/maintenir_registre_negociateurs.py --a-blanc   (force l'essai a blanc)
    python phase2/sync/maintenir_registre_negociateurs.py --presents  (affiche la liste de la nuit, n'appelle rien)
Sortie : 0 = fait (ou eteint) · 1 = echec.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[2]
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
LISTES = ("list_negos", "list_negos_inactive")
FENETRE_NUIT = timedelta(hours=6)
PLUS_VIEILLE = timedelta(hours=36)


def charger_env() -> None:
    """Le meme .env que les autres pushs (meme fonction) : un seul endroit pour l'interrupteur."""
    sys.path.insert(0, str(ROOT / "phase2" / "sync"))
    try:
        from push_contacts_to_supabase import DEFAULT_ENV_FILES, load_env_file  # noqa: PLC0415
        for chemin in DEFAULT_ENV_FILES:
            load_env_file(chemin)
    except Exception:  # noqa: BLE001 -- sans .env, l'interrupteur reste eteint
        pass


def _date(texte: str) -> datetime | None:
    try:
        d = datetime.fromisoformat(str(texte).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def presents_de_la_nuit() -> tuple[list[str] | None, str]:
    """Les n° de negociateur que la liste de Hektor de CETTE nuit contient, et une phrase qui dit d'ou ils viennent."""
    conn = sqlite3.connect(f"file:{HEKTOR_DB.as_posix()}?mode=ro", uri=True)
    try:
        pages = []
        for liste in LISTES:
            pages += conn.execute(
                """
                SELECT r.fetched_at, r.payload_json FROM raw_api_response r
                JOIN (SELECT endpoint_name, object_type, object_id_key, page_key, MAX(id) AS max_id
                        FROM raw_api_response WHERE endpoint_name = ?
                       GROUP BY endpoint_name, object_type, object_id_key, page_key) l ON l.max_id = r.id
                """,
                (liste,),
            ).fetchall()
    finally:
        conn.close()
    dates = [d for d in (_date(p[0]) for p in pages) if d]
    if not dates:
        return None, "aucune liste de negociateurs dans raw_api_response"
    derniere = max(dates)
    if datetime.now(timezone.utc) - derniere > PLUS_VIEILLE:
        return None, f"la liste la plus recente date du {derniere.isoformat()} : trop vieille, presence inconnue"
    ids: set[str] = set()
    gardees = 0
    fins = 0  # pages de la nuit qui disent « pas de page suivante » : une par liste lue jusqu'au bout
    for quand, payload in pages:
        d = _date(quand)
        if not d or derniere - d > FENETRE_NUIT:
            continue  # une page d'une autre nuit (elle n'existe plus chez Hektor, ou la nuit ne l'a pas relue)
        gardees += 1
        corps = json.loads(payload) or {}
        if (corps.get("metadata") or {}).get("nextPage", "absent") is None:
            fins += 1
        data = corps.get("data") or []
        for item in data if isinstance(data, list) else []:
            if isinstance(item, dict) and str(item.get("id") or "").strip():
                ids.add(str(item["id"]).strip())
    # ⚠ MESURE DU 04/11 : la nuit lit 5 pages au plus (sync_raw --update-max-pages) et compte depuis 0 alors que Hektor
    #   commence a 1 (pages « 0 » et « 1 » = la meme) : la liste complete (152 fiches, 8 pages) n'est jamais lue en
    #   entier. Une liste qui n'est pas lue jusqu'a sa derniere page ne dit PAS qui a disparu -> presence inconnue.
    if fins < len(LISTES):
        return None, (f"liste incomplete : {len(ids)} fiches sur {gardees} pages de la nuit, {fins} liste(s) sur {len(LISTES)} "
                      f"lue(s) jusqu'a la derniere page (plafond de pages de sync_raw) -- aucune absence ne sera marquee")
    return sorted(ids, key=lambda x: int(x) if x.isdigit() else 0), f"{len(ids)} fiches sur {gardees} pages de la nuit (la plus recente : {derniere.isoformat()})"


def appeler(presents: list[str] | None, a_blanc: bool) -> dict:
    url = (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "").strip().rstrip("/")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not cle:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY requis")
    corps = json.dumps({"p_presents": presents, "p_a_blanc": a_blanc}).encode("utf-8")
    requete = urllib.request.Request(
        f"{url}/rest/v1/rpc/app_negociateur_registre_maintenir", data=corps, method="POST",
        headers={"apikey": cle, "Authorization": f"Bearer {cle}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(requete, timeout=120) as reponse:
            return json.loads(reponse.read().decode("utf-8") or "{}")
    except HTTPError as erreur:
        raise RuntimeError(f"HTTP {erreur.code} : {erreur.read().decode('utf-8', 'replace')[:500]}") from erreur


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--a-blanc", action="store_true", help="force l'essai a blanc (rien n'est ecrit)")
    parser.add_argument("--presents", action="store_true", help="affiche la liste de la nuit et sort")
    args = parser.parse_args()
    charger_env()

    presents, origine = presents_de_la_nuit()
    if args.presents:
        print(json.dumps({"origine": origine, "presents": presents}, ensure_ascii=False))
        return 0

    mode = (os.environ.get("APP_REGISTRE_NEGOCIATEURS") or "0").strip().lower()
    if args.a_blanc:
        mode = "blanc"
    if mode not in {"blanc", "1", "on", "oui", "true"}:
        print("registre des negociateurs : interrupteur eteint (APP_REGISTRE_NEGOCIATEURS), rien n'est fait")
        return 0
    a_blanc = mode == "blanc"
    print(f"registre des negociateurs : {'A BLANC' if a_blanc else 'ECRITURE'} · presence : {origine}")
    try:
        rapport = appeler(presents, a_blanc)
    except Exception as erreur:  # noqa: BLE001
        print(f"ECHEC : {erreur}")
        return 1
    print(json.dumps(rapport, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
