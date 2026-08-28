# -*- coding: utf-8 -*-
"""C.19 (etape 1) -- LE MAGASIN DES CHAMPS D'AFFAIRE, cote serveur.

CE QU'IL FAIT. Il descend ce que l'app a saisi sur une transaction -- un prix
corrige, une date rectifiee -- depuis Supabase vers une table locale A PART, que
le run de nuit ne reconstruit jamais.

POURQUOI UNE TABLE A PART. app_view_generale est DETRUITE et refaite chaque nuit
depuis le miroir Hektor. Une valeur ecrite par l'app dans cette table ne
survivrait pas jusqu'a 05:30. C'est le patron deja eprouve CINQ fois ici :
app_dossier, app_affaire_ledger, app_search_registry, app_contact, et
app_mandat_champ_app (28/08, eprouve de bout en bout).

LA CLE : app_affaire_id, et pas le numero Hektor. Deliberé. Le patch du 20/08 a
justement retire la dependance au numero Hektor -- Hektor tient trois compteurs
qui se telescopent (7 541 numeros portes par deux types). Ranger par numero
Hektor reconstruirait cette dependance, et interdirait a une affaire NEE DANS
L'APP d'avoir des champs corriges.

CE QU'IL N'AFFIRME PAS. Il NOTE ce que l'app detient ; il ne tranche pas. C'est
appliquer_contrat_affaire.py qui arbitrera, avec la regle validee le 28/08 :

    l'app a une valeur   ->  elle gagne
    l'app n'a rien       ->  ON NE TOUCHE A RIEN

UNE LECTURE RATEE NE VAUT JAMAIS "RIEN A DIRE". Si Supabase est injoignable, on
le dit et on ne conclut rien -- surtout pas que l'app n'a plus de saisie.

PERSONNE NE LIT ENCORE CETTE TABLE. Retour arriere : DROP TABLE app_affaire_champ_app.

    python phase2/identite/magasin_affaire_app.py --dry-run
    python phase2/identite/magasin_affaire_app.py
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
MAGASIN = "app_affaire_champ_app"
LEDGER = "app_affaire_ledger"

# Les 13 champs de la modale "changer statut". Le magasin les accepte tous ;
# c'est le CONTRAT (etape 2) qui decidera lesquels l'app possede vraiment.
CHAMPS_CONNUS = (
    "montant", "prix_de_vente", "prix_net_vendeur", "date", "date_acte",
    "jours_validite", "jours_retractation", "sequestre", "honoraires",
    "commission_agence", "acquereur_id", "notaire_id", "numero_mandat",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS app_affaire_champ_app (
    app_affaire_id      INTEGER NOT NULL,
    champ               TEXT    NOT NULL,
    valeur_app          TEXT,
    valeur_miroir       TEXT,
    hektor_annonce_id   TEXT,
    kind                TEXT,
    origine             TEXT,
    vu_le               TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    vu_la_premiere_fois TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (app_affaire_id, champ)
)
"""


def norme(valeur) -> str:
    """Compare ce qui est comparable : un montant, une date, du texte."""
    if valeur is None:
        return ""
    texte = str(valeur).strip()
    if texte.lower() in ("none", "null", "0000-00-00", "0000-00-00 00:00:00"):
        return ""
    # un montant : 90000.00 et 90000 sont la meme chose
    try:
        nombre = float(texte.replace(",", "."))
        if nombre == int(nombre):
            return str(int(nombre))
        return ("%.2f" % nombre).rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        pass
    return texte[:10] if len(texte) >= 10 and texte[4] == "-" and texte[7] == "-" else texte


def charger_env() -> tuple[str, str]:
    """Le meme lecteur que les autres etapes du run -- on ne reinvente pas."""
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
            "select": "app_affaire_id,champ,valeur_app,origine,ecrit_le,ecrit_par",
            "order": "app_affaire_id",
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

    # Ce que le serveur sait de chaque affaire : sa valeur de reference.
    reference: dict[int, dict] = {}
    for aid, annonce, kind, montant, date, date_acte, sequestre in conn.execute(
            "SELECT app_affaire_id, hektor_annonce_id, kind, montant, date, date_acte, sequestre "
            "FROM " + LEDGER):
        if aid is None:
            continue
        reference[int(aid)] = {
            "hektor_annonce_id": annonce, "kind": kind,
            "montant": montant, "date": date, "date_acte": date_acte, "sequestre": sequestre,
        }
    print("ledger : %d affaires" % len(reference))

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
        aid = ligne.get("app_affaire_id")
        champ = str(ligne.get("champ") or "").strip()
        valeur = norme(ligne.get("valeur_app"))
        if aid is None or not champ:
            continue
        aid = int(aid)
        if not valeur:
            vides += 1
            continue
        ref = reference.get(aid)
        if ref is None:
            # L'affaire n'est pas (ou plus) dans le ledger : on le signale, on ne devine pas.
            inconnus += 1
            continue
        if args.dry_run:
            continue
        conn.execute(
            "INSERT INTO " + MAGASIN + " "
            "(app_affaire_id, champ, valeur_app, valeur_miroir, hektor_annonce_id, kind, origine, vu_le) "
            "VALUES (?,?,?,?,?,?,?,CURRENT_TIMESTAMP) "
            "ON CONFLICT(app_affaire_id, champ) DO UPDATE SET "
            "  valeur_app    = excluded.valeur_app, "
            "  valeur_miroir = excluded.valeur_miroir, "
            "  origine       = excluded.origine, "
            "  vu_le         = CURRENT_TIMESTAMP",
            (aid, champ, valeur, norme(ref.get(champ)) or None,
             ref.get("hektor_annonce_id"), ref.get("kind"),
             str(ligne.get("origine") or "saisie_app")))
        ecrits += 1

    if not args.dry_run:
        conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM " + MAGASIN).fetchone()[0]
    conn.close()

    print()
    print("   saisies reprises                    : %d" % ecrits)
    print("   saisies vides (ignorees)            : %d" % vides)
    print("   affaires inconnues du ledger        : %d" % inconnus)
    print("   magasin : %d ligne(s)%s"
          % (total, "   (dry-run : rien ecrit)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
