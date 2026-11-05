"""REGISTRE DES UTILISATEURS ET DES AGENCES, etape 2 (05/11/2026) -- LA TENUE DE NUIT.

Audit : notice/AUDIT_REGISTRE_NEGOCIATEURS_2026-11-04.md §35 et §40. La logique est TOUTE dans la base
(supabase/patch_registre_utilisateurs_agences_etape2_2026-11-05.sql, fonction
app_registre_utilisateurs_agences_maintenir) : ce script ne fait que lui donner ce qu'elle ne peut pas lire --
les fiches BRUTES de Hektor que la nuit a deja telechargees (data/hektor.sqlite, lecture seule) :
  hektor_agence.raw_json       les agences, avec le juridique, la carte professionnelle, le bareme, le logo ;
  hektor_negociateur.raw_json  les negociateurs, avec prenom, nom, fonction, telephones, e-mail, photo.
Puis il ecrit son compte rendu au journal du run.

⛔ INTERRUPTEUR APP_REGISTRE_AGENCES (.env) : 0 ou absent = rien ; « blanc » = la fonction suit le meme chemin
   puis annule tout, seul le compte rendu sort ; 1 = elle ecrit.
⚠ AUCUNE requete chez Hektor. Etape NON BLOQUANTE dans le run : ratee, le registre garde la nuit d'avant.
⚠ Rien dans l'app ne lit encore ces tables (etape 5 du §35).

Usage :
    python phase2/sync/maintenir_registre_agences.py             (selon l'interrupteur)
    python phase2/sync/maintenir_registre_agences.py --a-blanc   (force l'essai a blanc)
    python phase2/sync/maintenir_registre_agences.py --compter   (dit ce qu'il enverrait, n'appelle rien)
Sortie : 0 = fait (ou eteint) · 1 = echec.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[2]
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
# les champs du negociateur que la fonction lit (le reste du brut ne voyage pas)
CHAMPS_NEGO = ("id", "idUser", "agence", "nom", "prenom", "fonction", "telephone", "portable", "email", "avatar")
# plancher : en dessous, la liste locale est tenue pour cassee et rien n'est envoye
MIN_AGENCES = 10
MIN_NEGOS = 100


def charger_env() -> None:
    """Le meme .env que les autres pushs (meme fonction) : un seul endroit pour l'interrupteur."""
    sys.path.insert(0, str(ROOT / "phase2" / "sync"))
    try:
        from push_contacts_to_supabase import DEFAULT_ENV_FILES, load_env_file  # noqa: PLC0415
        for chemin in DEFAULT_ENV_FILES:
            load_env_file(chemin)
    except Exception:  # noqa: BLE001 -- sans .env, l'interrupteur reste eteint
        pass


def lire_listes() -> tuple[list[dict], list[dict]]:
    conn = sqlite3.connect(f"file:{HEKTOR_DB.as_posix()}?mode=ro", uri=True)
    try:
        agences = [json.loads(x) for (x,) in conn.execute("SELECT raw_json FROM hektor_agence WHERE raw_json IS NOT NULL")]
        negos = [json.loads(x) for (x,) in conn.execute("SELECT raw_json FROM hektor_negociateur WHERE raw_json IS NOT NULL")]
    finally:
        conn.close()
    agences = [a for a in agences if isinstance(a, dict) and str(a.get("id") or "").strip()]
    negos = [{k: n.get(k) for k in CHAMPS_NEGO} for n in negos if isinstance(n, dict) and str(n.get("id") or "").strip()]
    return agences, negos


def appeler(agences: list[dict], negos: list[dict], a_blanc: bool) -> dict:
    url = (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "").strip().rstrip("/")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not cle:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY requis")
    corps = json.dumps({"p_agences": agences, "p_negos": negos, "p_a_blanc": a_blanc}, ensure_ascii=False).encode("utf-8")
    requete = urllib.request.Request(
        f"{url}/rest/v1/rpc/app_registre_utilisateurs_agences_maintenir", data=corps, method="POST",
        headers={"apikey": cle, "Authorization": f"Bearer {cle}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(requete, timeout=180) as reponse:
            return json.loads(reponse.read().decode("utf-8") or "{}")
    except HTTPError as erreur:
        raise RuntimeError(f"HTTP {erreur.code} : {erreur.read().decode('utf-8', 'replace')[:500]}") from erreur


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--a-blanc", action="store_true", help="force l'essai a blanc (rien n'est ecrit)")
    parser.add_argument("--compter", action="store_true", help="dit ce qui serait envoye et sort")
    args = parser.parse_args()
    charger_env()

    agences, negos = lire_listes()
    if args.compter:
        print(json.dumps({"agences": len(agences), "negociateurs": len(negos)}, ensure_ascii=False))
        return 0

    mode = (os.environ.get("APP_REGISTRE_AGENCES") or "0").strip().lower()
    if args.a_blanc:
        mode = "blanc"
    if mode not in {"blanc", "1", "on", "oui", "true"}:
        print("registre des agences : interrupteur eteint (APP_REGISTRE_AGENCES), rien n'est fait")
        return 0
    if len(agences) < MIN_AGENCES or len(negos) < MIN_NEGOS:
        print(f"ECHEC : listes locales trop courtes ({len(agences)} agences, {len(negos)} negociateurs) -- rien n'est envoye")
        return 1
    a_blanc = mode == "blanc"
    print(f"registre des agences : {'A BLANC' if a_blanc else 'ECRITURE'} · {len(agences)} agences, {len(negos)} negociateurs")
    try:
        rapport = appeler(agences, negos, a_blanc)
    except Exception as erreur:  # noqa: BLE001
        print(f"ECHEC : {erreur}")
        return 1
    print(json.dumps(rapport, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
