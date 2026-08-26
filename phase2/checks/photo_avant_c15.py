# -*- coding: utf-8 -*-
"""C.15 (3) -- LA PHOTO D'AVANT, et le comparateur qui va avec.

POURQUOI. C.15 va faire entrer 4 165 annonces qui n'etaient jamais entrees -- toutes les
locations, tout l'immobilier professionnel, le neuf. Or les vues, le registre des mandats,
les rapprochements et les compteurs ont TOUS ete calcules jusqu'ici sur un parc ampute.
Sans photo d'avant, on ne saura pas distinguer un effet voulu d'une regression : tout aura
bouge, et on n'aura aucun point de comparaison.

C'est la lecon des neuf attendus ecrits la veille du run, le 25/08 : ecrire ce qu'on attend
AVANT, sinon on trouve normal ce qu'on decouvre.

LECTURE SEULE. Ce script ne modifie rien -- ni le miroir, ni le serveur, ni Supabase.

    python phase2/checks/photo_avant_c15.py              prend une photo et la compare
    python phase2/checks/photo_avant_c15.py --ecrire     prend une photo ET l'enregistre
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
MIROIR = RACINE / "data" / "hektor.sqlite"
SERVEUR = RACINE / "phase2" / "phase2.sqlite"
PHOTO = Path(__file__).resolve().parent / "photo_avant_c15.json"

sys.path.insert(0, str(RACINE / "phase2" / "sync"))


def lecture(chemin: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{chemin.as_posix()}?mode=ro", uri=True)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def compte(conn: sqlite3.Connection, sql: str) -> int | str:
    try:
        return int(conn.execute(sql).fetchone()[0])
    except Exception as err:  # table absente, colonne renommee : on le dit, on ne plante pas
        return f"?({str(err)[:60]})"


def env_supabase() -> tuple[str, str] | None:
    for fichier in (RACINE / "apps" / "hektor-v1" / ".env", RACINE / ".env"):
        if not fichier.exists():
            continue
        for ligne in fichier.read_text(encoding="utf-8", errors="ignore").splitlines():
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            cle, valeur = ligne.split("=", 1)
            os.environ.setdefault(cle.strip(), valeur.strip().strip('"').strip("'"))
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    return (url, cle) if url and cle else None


def compte_supabase(url: str, cle: str, table: str) -> int | str:
    requete = urllib.request.Request(
        f"{url.rstrip('/')}/rest/v1/{table}?select=*&limit=1",
        headers={"apikey": cle, "Authorization": f"Bearer {cle}",
                 "Prefer": "count=exact", "Range": "0-0"},
    )
    try:
        reponse = urllib.request.urlopen(requete, timeout=60)
        return int(str(reponse.headers.get("content-range", "?")).split("/")[-1])
    except urllib.error.HTTPError as err:
        return f"?(http {err.code})"
    except Exception as err:
        return f"?({str(err)[:40]})"


def prendre_photo() -> dict:
    mesures: dict[str, object] = {}
    miroir, serveur = lecture(MIROIR), lecture(SERVEUR)

    # --- le miroir : ce que Hektor nous donne
    for table in ("hektor_annonce", "hektor_annonce_detail", "hektor_mandat",
                  "hektor_offre", "hektor_compromis", "hektor_vente", "hektor_contact"):
        mesures[f"miroir.{table}"] = compte(miroir, f"SELECT COUNT(*) FROM {table}")
    mesures["miroir.annonces_par_offre_type"] = dict(
        miroir.execute("SELECT COALESCE(offre_type,'(null)'), COUNT(*) "
                       "FROM hektor_annonce GROUP BY 1").fetchall())

    # --- le serveur : identite, corps, registres
    for table in ("app_dossier", "app_view_generale", "app_contact", "app_affaire_ledger",
                  "app_search_registry", "app_annonce_champ_app", "app_annonce_app_seule",
                  "app_contact_relation_current", "app_dossier_current"):
        mesures[f"serveur.{table}"] = compte(serveur, f"SELECT COUNT(*) FROM {table}")

    # --- ce que les quatre index produiraient
    try:
        import export_app_payload as export

        mesures["index.actives"] = compte(
            serveur, f"SELECT COUNT(*) FROM app_view_generale WHERE {export.ANNONCES_SCOPE_WHERE}")
        for cle, sql in (("index.archives", export.SQL_ARCHIVE_ANNONCE_INDEX_BASE),
                         ("index.historiques", export.SQL_HISTORICAL_ANNONCE_INDEX_BASE)):
            mesures[cle] = compte(serveur, f"SELECT COUNT(*) FROM ({sql.strip().rstrip(';')})")
        mesures["index.filtre_offre"] = export.FILTRE_OFFRE_APP
    except Exception as err:
        mesures["index.erreur"] = str(err)[:120]

    # --- les compteurs metier, ceux qui s'afficheront a l'ecran
    mesures["registre.mandats"] = compte(
        serveur, "SELECT COUNT(*) FROM app_view_generale WHERE COALESCE(numero_mandat,'') <> ''")
    mesures["registre.sans_mandat"] = compte(
        serveur, "SELECT COUNT(*) FROM app_view_generale WHERE COALESCE(numero_mandat,'') = ''")
    mesures["annonces.par_statut"] = dict(
        serveur.execute("SELECT COALESCE(detail_statut_name, statut_annonce,'(vide)'), COUNT(*) "
                        "FROM app_view_generale GROUP BY 1 ORDER BY 2 DESC").fetchall())

    # --- Supabase : ce que l'app montre vraiment
    creds = env_supabase()
    if creds:
        url, cle = creds
        for table in ("app_dossier_current", "app_archive_annonce_index_current",
                      "app_historical_annonce_index_current", "app_brouillon_annonce_index_current",
                      "app_mandat_register_current", "app_contact_current",
                      "app_affaire_ledger", "app_contact_relation_current"):
            mesures[f"supabase.{table}"] = compte_supabase(url, cle, table)
    else:
        mesures["supabase.erreur"] = "identifiants absents"

    miroir.close()
    serveur.close()
    return {"prise_le": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mesures": mesures}


def afficher(photo: dict, precedente: dict | None) -> None:
    avant = (precedente or {}).get("mesures", {})
    print(f"=== PHOTO DU {photo['prise_le']} ===")
    if precedente:
        print(f"    comparee a celle du {precedente['prise_le']}")
    print()
    for cle, valeur in photo["mesures"].items():
        if isinstance(valeur, dict):
            print(f"   {cle}")
            for sous_cle, sous_valeur in valeur.items():
                ancien = (avant.get(cle) or {}).get(sous_cle)
                ecart = ""
                if isinstance(ancien, int) and isinstance(sous_valeur, int) and ancien != sous_valeur:
                    ecart = f"   <<< {sous_valeur - ancien:+d}"
                print(f"      {str(sous_cle):<24} {sous_valeur}{ecart}")
            continue
        ancien = avant.get(cle)
        ecart = ""
        if isinstance(ancien, int) and isinstance(valeur, int) and ancien != valeur:
            ecart = f"   <<< {valeur - ancien:+d}"
        print(f"   {cle:<44} {valeur}{ecart}")


def main() -> int:
    parseur = argparse.ArgumentParser(description="C.15 (3) : la photo d'avant, et sa comparaison.")
    parseur.add_argument("--ecrire", action="store_true",
                         help="enregistre la photo (ecrase la precedente)")
    arguments = parseur.parse_args()

    precedente = json.loads(PHOTO.read_text(encoding="utf-8")) if PHOTO.exists() else None
    photo = prendre_photo()
    afficher(photo, precedente)

    if arguments.ecrire:
        PHOTO.write_text(json.dumps(photo, ensure_ascii=True, indent=1), encoding="utf-8")
        print()
        print(f"photo enregistree : {PHOTO}")
    elif precedente is None:
        print()
        print("AUCUNE photo enregistree. Relance avec --ecrire pour poser la reference.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
