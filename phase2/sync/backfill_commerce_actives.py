# -*- coding: utf-8 -*-
"""C.15 -- remplit le bloc commerce des annonces ACTIVES dans Supabase, une fois.

POURQUOI CE SCRIPT EXISTE.
Le paquet nocturne (push_upgrade_to_supabase.py) n'envoie une annonce que si son
`source_hash` a change. Or ce hache est calcule sur le CONTENU HEKTOR : il ne bouge
pas quand c'est NOUS qui apprenons quelque chose de neuf. Les sous-types commerce
viennent de la console GraphQL, pas de l'API : ils ont ete ajoutes a la vue serveur
sans toucher au hache. Consequence mesuree le 27/08/2026 :

    archives          782 / 782  remplies   (poussees par remplacement complet)
    historique         92 /  92  remplies   (idem)
    annonces actives    1 / 160  remplie    <-- bloquees par le hache

Et aucun run futur ne les debloquera : il faudrait qu'un negociateur modifie chaque
annonce dans Hektor. D'ou ce rattrapage unique.

CE QU'IL FAIT, ET RIEN D'AUTRE.
Un PATCH par annonce sur app_dossier_current, portant UNIQUEMENT les 11 colonnes
commerce. Aucune ligne creee, aucune supprimee, aucune autre colonne touchee --
le `source_hash` en particulier reste intact, donc le delta nocturne n'est pas fausse.

    python phase2/sync/backfill_commerce_actives.py --dry-run   montre sans ecrire
    python phase2/sync/backfill_commerce_actives.py             ecrit
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SERVEUR = RACINE / "phase2" / "phase2.sqlite"
FICHIERS_ENV = (RACINE / ".env", RACINE / "apps" / "hektor-v1" / ".env")

COLONNES = (
    "commerce_sous_type", "commerce_famille", "commerce_activite", "commerce_loyer",
    "commerce_charges", "commerce_taxe_fonciere", "commerce_bail_duree",
    "commerce_bail_echeance", "commerce_etat", "commerce_zone", "commerce_json",
)


def charger_env() -> tuple[str, str]:
    for fichier in FICHIERS_ENV:
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
    if not url or not cle:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis")
    return url.rstrip("/"), cle


def appeler(url: str, cle: str, methode: str, chemin: str, requete: dict[str, str],
            corps: object | None = None, prefer: str | None = None) -> object | None:
    adresse = "%s/rest/v1/%s?%s" % (url, chemin, urllib.parse.urlencode(requete))
    entetes = {"apikey": cle, "Authorization": "Bearer %s" % cle,
               "Content-Type": "application/json"}
    if prefer:
        entetes["Prefer"] = prefer
    donnees = json.dumps(corps, ensure_ascii=True).encode("utf-8") if corps is not None else None
    requete_http = urllib.request.Request(adresse, data=donnees, headers=entetes, method=methode)
    for tentative in (1, 2, 3):
        try:
            with urllib.request.urlopen(requete_http, timeout=60) as reponse:
                brut = reponse.read().decode("utf-8")
                return json.loads(brut) if brut else None
        except urllib.error.HTTPError as err:
            detail = err.read().decode("utf-8", errors="replace")
            if err.code in (500, 502, 503, 504) and tentative < 3:
                time.sleep(1.5 * tentative)
                continue
            raise RuntimeError("Supabase %s sur %s : %s" % (err.code, chemin, detail[:300])) from err
        except (TimeoutError, urllib.error.URLError):
            if tentative >= 3:
                raise
            time.sleep(1.5 * tentative)
    return None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parseur = argparse.ArgumentParser(description="C.15 : rattrapage unique du bloc commerce.")
    parseur.add_argument("--dry-run", action="store_true", help="montre ce qui serait ecrit, n'ecrit pas")
    arguments = parseur.parse_args()

    url, cle = charger_env()

    # --- 1. qui a besoin d'etre rempli, cote Supabase
    cibles = appeler(url, cle, "GET", "app_dossier_current",
                     {"select": "app_dossier_id", "offre_type": "eq.10",
                      "order": "app_dossier_id.asc", "limit": "10000"})
    identifiants = [int(ligne["app_dossier_id"]) for ligne in (cibles or [])]
    print("annonces immo pro actives dans l'app : %d" % len(identifiants))
    if not identifiants:
        print("rien a faire.")
        return 0

    # --- 2. ce que le serveur sait d'elles
    conn = sqlite3.connect("file:%s?mode=ro" % SERVEUR.as_posix(), uri=True)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.row_factory = sqlite3.Row
    trous = ",".join("?" * len(identifiants))
    lignes = conn.execute(
        "SELECT app_dossier_id, %s FROM app_view_generale WHERE app_dossier_id IN (%s)"
        % (", ".join(COLONNES), trous), identifiants).fetchall()
    conn.close()

    par_id = {int(ligne["app_dossier_id"]): ligne for ligne in lignes}
    print("retrouvees sur le serveur            : %d" % len(par_id))
    absentes = [i for i in identifiants if i not in par_id]
    if absentes:
        print("ABSENTES du serveur (ignorees)       : %d  %s" % (len(absentes), absentes[:10]))

    # --- 3. le rattrapage, une annonce a la fois
    ecrites = vides = 0
    repartition: dict[str, int] = {}
    for numero, identifiant in enumerate(identifiants, start=1):
        ligne = par_id.get(identifiant)
        if ligne is None:
            continue
        paquet = {}
        for colonne in COLONNES:
            valeur = ligne[colonne]
            paquet[colonne] = None if valeur is None or str(valeur).strip() == "" else str(valeur)
        if not paquet.get("commerce_sous_type"):
            vides += 1
            continue
        repartition[paquet["commerce_sous_type"]] = repartition.get(paquet["commerce_sous_type"], 0) + 1
        if arguments.dry_run:
            ecrites += 1
            continue
        appeler(url, cle, "PATCH", "app_dossier_current",
                {"app_dossier_id": "eq.%d" % identifiant}, corps=paquet,
                prefer="return=minimal")
        ecrites += 1
        if numero % 25 == 0:
            print("   ... %d / %d" % (numero, len(identifiants)))

    print()
    print("%s : %d annonces%s" % ("SIMULATION" if arguments.dry_run else "ECRITES",
                                  ecrites, "" if not vides else ", %d sans sous-type ignorees" % vides))
    print()
    print("repartition :")
    for libelle, nombre in sorted(repartition.items(), key=lambda paire: -paire[1]):
        print("   %-28s %d" % (libelle, nombre))

    # --- 4. le REGISTRE DES MANDATS, meme probleme, meme remede
    #
    # Le registre est une table a part (app_mandat_register_current), alimentee par
    # son propre paquet. La colonne vient d'y etre ajoutee : les lignes deja en place
    # sont vides. On ne reconstruit PAS le registre entier -- 23 833 lignes, et un
    # ecran blanc le temps de l'operation. On remplit les lignes concernees, annonce
    # par annonce. Les runs suivants porteront la colonne d'eux-memes.
    print()
    print("--- registre des mandats ---")
    conn = sqlite3.connect("file:%s?mode=ro" % SERVEUR.as_posix(), uri=True)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("ATTACH DATABASE 'file:%s?mode=ro' AS hektor"
                 % (RACINE / "data" / "hektor.sqlite").as_posix())
    sous_types = {
        str(annonce): libelle
        for annonce, libelle in conn.execute(
            "SELECT hektor_annonce_id, sous_type_label FROM hektor.hektor_annonce_commercial "
            "WHERE COALESCE(sous_type_label,'') <> ''")
    }
    conn.close()
    print("sous-types connus                    : %d" % len(sous_types))

    # PIEGE : PostgREST plafonne une reponse a 1 000 lignes. Lister "toutes les lignes
    # vides" du registre (23 833) rendait les 1 000 premieres, aucune immo pro, donc
    # "0 a faire" -- un faux negatif silencieux. On interroge par la liste des annonces
    # immo pro connues, decoupee en tranches.
    presentes: set[str] = set()
    connues = sorted(sous_types)
    for depart in range(0, len(connues), 100):
        tranche = connues[depart:depart + 100]
        reponse = appeler(url, cle, "GET", "app_mandat_register_current",
                          {"select": "hektor_annonce_id",
                           "hektor_annonce_id": "in.(%s)" % ",".join(tranche),
                           "limit": "1000"})
        presentes |= {str(ligne["hektor_annonce_id"]) for ligne in (reponse or [])}
    a_traiter = sorted(presentes)
    print("annonces immo pro presentes au registre : %d" % len(a_traiter))

    touchees = 0
    for numero, annonce in enumerate(a_traiter, start=1):
        if arguments.dry_run:
            touchees += 1
            continue
        appeler(url, cle, "PATCH", "app_mandat_register_current",
                {"hektor_annonce_id": "eq.%s" % annonce},
                corps={"commerce_sous_type": sous_types[annonce]}, prefer="return=minimal")
        touchees += 1
        if numero % 50 == 0:
            print("   ... %d / %d" % (numero, len(a_traiter)))
    print("%s : %d annonces du registre" % ("SIMULATION" if arguments.dry_run else "ECRITES", touchees))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
