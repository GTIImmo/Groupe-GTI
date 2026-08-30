#!/usr/bin/env python3
"""C.4 — LE CARNET DES CHAMPS D'ANNONCE, côté serveur.

CE QUE C'EST, ET CE QUE CE N'EST PAS.

Ce n'est PAS une copie de la liste des annonces : elle existe déjà, et rien ne la
double. C'est un carnet d'EXCEPTIONS — une ligne par champ dont l'app est
l'auteur. Ses deux frères le montrent : `app_mandat_champ_app` tient 1 ligne,
`app_affaire_champ_app` en tient 2. Le grand registre, lui, a 13 374 pages.

CE QUE CE SCRIPT FAIT. Il descend chez toi ce que l'app a saisi, et le range dans
une table qui n'est JAMAIS reconstruite — contrairement aux tables dérivées, que
le pipeline efface et refait à chaque run. Une saisie posée ici survit à tout.

Il note aussi, en face de chaque saisie, ce que le serveur croit savoir
(`valeur_miroir`). Non pour trancher — ce n'est pas son rôle — mais pour qu'on
puisse voir d'un coup d'œil où l'app et Hektor divergent.

CE QU'IL NE FAIT PAS. Il n'applique rien. C'est `contrat_autorite.py` qui décide
quels champs l'app possède vraiment, et pour l'annonce cette liste est VIDE.
Tant qu'elle l'est, ce carnet se remplit sans que rien ne change en production.

LA GARDE QUI COMPTE, héritée de ses frères : **une lecture ratée ne vaut jamais
« l'app n'a rien à dire »**. Si Supabase est illisible, on sort sans rien écrire.
Conclure du silence, c'est exactement ce que ce projet passe son temps à corriger.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"
VERROU = RACINE / "phase2" / ".descente.lock"
MAGASIN = "app_annonce_champ_app"
VUE = "app_view_generale"

# Les champs que les gestes de C.4 écriront. Le carnet les accepte tous ;
# c'est le CONTRAT qui décidera lesquels l'app possède vraiment.
#
# LA SUPPRESSION N'EST PAS ICI, ET C'EST VOLONTAIRE (arbitrage du 30/08).
# Ce carnet sert aux champs CORRIGÉS : une valeur que l'app tient pour juste en
# face de celle d'Hektor. Une suppression n'est pas une correction, c'est un
# événement — l'annonce s'en va, il n'y a plus rien à comparer. La ranger ici
# aurait mélangé deux natures dans la même table.
CHAMPS_CONNUS = (
    "archive",              # archiver / désarchiver
    "negociateur_email",    # affecter le négociateur
    "statut_annonce",       # changer le statut
    "diffusable",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS app_annonce_champ_app (
  app_dossier_id       INTEGER NOT NULL,
  champ                TEXT    NOT NULL,
  valeur_app           TEXT,
  valeur_miroir        TEXT,
  vu_le                TEXT,
  vu_la_premiere_fois  TEXT DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (app_dossier_id, champ)
);
"""


def norme(valeur) -> str:
    """Une valeur vide, quelle que soit sa forme, est une absence."""
    if valeur is None:
        return ""
    texte = str(valeur).strip()
    return "" if texte.lower() in ("", "none", "null") else texte


def charger_env() -> tuple[str, str]:
    """Le meme lecteur que les autres etapes du run -- on ne reinvente pas.

    DEUX fichiers, et le second compte : les cles Supabase vivent dans
    apps/hektor-v1/.env, pas a la racine. Ma premiere version ne lisait que la
    racine et echouait, alors que le script frere passait -- la difference tenait
    a cette seule ligne.
    """
    for fichier in (RACINE / ".env", RACINE / "apps" / "hektor-v1" / ".env"):
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


def lire_saisies(url: str, cle: str) -> list[dict]:
    """Ce que l'app a saisi. Pagine : PostgREST plafonne a 1 000 lignes."""
    lignes: list[dict] = []
    depuis = 0
    while True:
        params = urllib.parse.urlencode({
            "select": "app_dossier_id,champ,valeur_app,origine,ecrit_le,ecrit_par",
            "order": "app_dossier_id",
            "offset": str(depuis),
            "limit": "1000",
        })
        requete = urllib.request.Request(
            url + "/rest/v1/" + MAGASIN + "?" + params,
            headers={"apikey": cle, "Authorization": "Bearer " + cle},
        )
        with urllib.request.urlopen(requete, timeout=60) as reponse:
            paquet = json.loads(reponse.read().decode("utf-8"))
        lignes.extend(paquet)
        if len(paquet) < 1000:
            return lignes
        depuis += 1000


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="montre sans rien ecrire")
    args = ap.parse_args()

    # La descente tient ce verrou ~21 minutes. Ecrire pendant qu'elle tourne,
    # c'est l'incident du 22/08 -- on ne recommence pas.
    if VERROU.exists() and not args.dry_run:
        print("La descente est en cours (verrou present) -- on ne touche a rien.")
        return 0

    conn = sqlite3.connect("file:" + BASE.as_posix() + "?mode=rw", timeout=60, uri=True)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute(SCHEMA)

    # Ce que le serveur croit savoir de chaque annonce : la valeur de reference.
    #
    # TOUS LES CHAMPS N'EN ONT PAS. `supprime`, par exemple, n'existe nulle part
    # cote serveur -- c'est une notion que seule l'app porte. Le carnet doit
    # l'accepter quand meme : il enregistre ce que l'app dit, il ne se limite pas
    # a ce qu'Hektor sait dire. On ne lit donc que les colonnes qui existent, et
    # les autres restent sans valeur de reference. C'est une absence, pas un trou.
    presentes = {d[1] for d in conn.execute("PRAGMA table_info(" + VUE + ")")}
    avec_miroir = [c for c in CHAMPS_CONNUS if c in presentes]
    sans_miroir = [c for c in CHAMPS_CONNUS if c not in presentes]
    colonnes = ", ".join(avec_miroir)
    reference: dict[int, dict] = {}
    for ligne in conn.execute(
            "SELECT app_dossier_id, hektor_annonce_id" +
            (", " + colonnes if colonnes else "") + " FROM " + VUE):
        did = ligne[0]
        if did is None:
            continue
        reference[int(did)] = dict(
            {"hektor_annonce_id": ligne[1]},
            **{champ: ligne[2 + i] for i, champ in enumerate(avec_miroir)})
    print("vue    : %d annonce(s)" % len(reference))
    if sans_miroir:
        print("         (sans equivalent cote serveur : %s)" % ", ".join(sans_miroir))

    url, cle = charger_env()
    try:
        saisies = lire_saisies(url, cle)
    except Exception as err:
        # Une lecture ratee ne vaut JAMAIS "l'app n'a rien a dire".
        print("Supabase illisible (%s) -- on ne conclut rien." % str(err)[:80])
        conn.close()
        return 4
    print("app    : %d saisie(s) lue(s) dans %s" % (len(saisies), MAGASIN))

    ecrits = inconnus = vides = 0
    for ligne in saisies:
        did = ligne.get("app_dossier_id")
        champ = str(ligne.get("champ") or "").strip()
        valeur = norme(ligne.get("valeur_app"))
        if did is None or not champ:
            continue
        did = int(did)
        if not valeur:
            vides += 1
            continue
        ref = reference.get(did)
        if ref is None:
            # L'annonce n'est pas (ou plus) dans la vue : on le signale, on ne devine pas.
            inconnus += 1
            continue
        if args.dry_run:
            continue
        conn.execute(
            "INSERT INTO " + MAGASIN + " "
            "(app_dossier_id, champ, valeur_app, valeur_miroir, vu_le) "
            "VALUES (?,?,?,?,CURRENT_TIMESTAMP) "
            "ON CONFLICT(app_dossier_id, champ) DO UPDATE SET "
            "  valeur_app    = excluded.valeur_app, "
            "  valeur_miroir = excluded.valeur_miroir, "
            "  vu_le         = CURRENT_TIMESTAMP",
            (did, champ, valeur, norme(ref.get(champ)) or None))
        ecrits += 1

    if not args.dry_run:
        conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM " + MAGASIN).fetchone()[0]
    conn.close()

    print()
    print("   saisies reprises                    : %d" % ecrits)
    print("   saisies vides (ignorees)            : %d" % vides)
    print("   annonces inconnues de la vue        : %d" % inconnus)
    print("   carnet : %d ligne(s)%s"
          % (total, "   (dry-run : rien ecrit)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
