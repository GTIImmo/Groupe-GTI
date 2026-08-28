# -*- coding: utf-8 -*-
"""L'ESSAI DE LA NUIT (C.19) -- a lancer le lendemain matin.

CE QU'IL VERIFIE. Une correction a ete posee dans NOS donnees le 29/08 au soir sur
une vente archivee. Entre-temps le run de nuit a :
  1. DETRUIT app_view_generale et l'a refaite depuis le miroir Hektor,
  2. rafraichi app_affaire_ledger depuis ce meme miroir,
  3. pousse le tout vers Supabase.
Chacune de ces trois etapes ecrase notre correction. Le magasin et le contrat
doivent l'avoir REPOSEE, aux trois endroits.

SI TOUT EST VERT : la chaine tient, l'app peut corriger une transaction sans que
Hektor l'apprenne et sans que le run l'efface.

SI QUELQUE CHOSE EST ROUGE : dire OU, sans deviner pourquoi.

    python phase2/identite/verifier_essai_nuit_c19.py
    python phase2/identite/verifier_essai_nuit_c19.py --restaurer
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"
TEMOIN = RACINE / "notice" / "ESSAI_NUIT_C19_2026-08-29.json"

ATTENDU_MONTANT = "123456"
ATTENDU_NET = "111111"


def charger_env() -> tuple[str, str]:
    for fichier in (RACINE / ".env", RACINE / "apps" / "hektor-v1" / ".env"):
        if not fichier.exists():
            continue
        for ligne in fichier.read_text(encoding="utf-8", errors="ignore").splitlines():
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            k, v = ligne.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis")
    return url.rstrip("/"), cle


def lire_supabase(chemin: str, params: str):
    url, cle = charger_env()
    requete = urllib.request.Request(
        url + "/rest/v1/" + chemin + "?" + params,
        headers={"apikey": cle, "Authorization": "Bearer " + cle})
    with urllib.request.urlopen(requete, timeout=60) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def egal(valeur, attendu) -> bool:
    """123456, '123456' et '123456.00' sont la meme chose."""
    if valeur is None:
        return False
    try:
        return abs(float(str(valeur).replace(",", ".")) - float(attendu)) < 0.005
    except (TypeError, ValueError):
        return str(valeur).strip() == str(attendu)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--restaurer", action="store_true",
                    help="retire la correction et remet l'etat d'avant")
    args = ap.parse_args()

    if not TEMOIN.exists():
        print("Temoin introuvable : %s" % TEMOIN)
        return 2
    avant = json.loads(TEMOIN.read_text(encoding="utf-8"))
    aid = avant["app_affaire_id"]

    conn = sqlite3.connect("file:" + BASE.as_posix() + "?mode=rw", timeout=60, uri=True)
    conn.execute("PRAGMA busy_timeout = 30000")

    print("=" * 68)
    print("ESSAI DE LA NUIT -- affaire %s (vente, annonce %s)" % (aid, avant["annonce"]))
    print("=" * 68)
    print("   valeur de Hektor : %s      valeur saisie dans l'app : %s"
          % (avant["ledger_montant"], ATTENDU_MONTANT))
    print()

    controles = []

    l = conn.execute("SELECT montant FROM app_affaire_ledger WHERE app_affaire_id=?",
                     (aid,)).fetchone()
    controles.append(("le ledger local", l[0] if l else None, ATTENDU_MONTANT))

    v = conn.execute(
        "SELECT vente_prix, prix_net_vendeur FROM app_view_generale "
        "WHERE CAST(hektor_annonce_id AS TEXT)=? AND CAST(vente_id AS TEXT)=?",
        (avant["annonce"], avant["hid"])).fetchone()
    controles.append(("la vue -- vente_prix", v[0] if v else None, ATTENDU_MONTANT))
    controles.append(("la vue -- prix_net_vendeur", v[1] if v else None, ATTENDU_NET))

    m = conn.execute("SELECT COUNT(*) FROM app_affaire_champ_app WHERE app_affaire_id=?",
                     (aid,)).fetchone()[0]
    controles.append(("le magasin local (2 lignes)", m, 2))

    try:
        r = lire_supabase("app_affaire_ledger", "select=montant&app_affaire_id=eq.%d" % aid)
        controles.append(("le ledger Supabase", r[0]["montant"] if r else None, ATTENDU_MONTANT))
    except Exception as err:
        controles.append(("le ledger Supabase", "illisible (%s)" % str(err)[:40], ATTENDU_MONTANT))

    try:
        r = lire_supabase("app_affaire_champ_app", "select=champ&app_affaire_id=eq.%d" % aid)
        controles.append(("le magasin Supabase (2 lignes)", len(r), 2))
    except Exception as err:
        controles.append(("le magasin Supabase (2 lignes)", "illisible (%s)" % str(err)[:40], 2))

    verts = 0
    for libelle, obtenu, attendu in controles:
        ok = egal(obtenu, attendu)
        verts += 1 if ok else 0
        print("   %-32s %-12s %s" % (libelle, obtenu, "OK" if ok else "<-- PERDU"))

    print()
    if verts == len(controles):
        print("   TOUT TIENT (%d/%d). La correction a survecu au run de nuit," % (verts, len(controles)))
        print("   aux trois endroits, et Hektor n'en sait toujours rien.")
    else:
        print("   %d/%d seulement. Voir les lignes marquees ci-dessus." % (verts, len(controles)))

    if args.restaurer:
        print()
        print("--- remise en etat ---")
        conn.execute("UPDATE app_affaire_ledger SET montant=? WHERE app_affaire_id=?",
                     (avant["ledger_montant"], aid))
        conn.execute("UPDATE app_view_generale SET vente_prix=? "
                     "WHERE CAST(hektor_annonce_id AS TEXT)=? AND CAST(vente_id AS TEXT)=?",
                     (avant["vue_prix"], avant["annonce"], avant["hid"]))
        conn.execute("DELETE FROM app_affaire_champ_app WHERE app_affaire_id=?", (aid,))
        conn.commit()
        url, cle = charger_env()
        for chemin, params in (("app_affaire_champ_app", "app_affaire_id=eq.%d" % aid),):
            requete = urllib.request.Request(url + "/rest/v1/" + chemin + "?" + params,
                                             method="DELETE",
                                             headers={"apikey": cle, "Authorization": "Bearer " + cle})
            urllib.request.urlopen(requete, timeout=60).read()
        corps = json.dumps({"montant": avant["ledger_montant"]}).encode()
        requete = urllib.request.Request(
            url + "/rest/v1/app_affaire_ledger?app_affaire_id=eq.%d" % aid,
            data=corps, method="PATCH",
            headers={"apikey": cle, "Authorization": "Bearer " + cle,
                     "Content-Type": "application/json", "Prefer": "return=minimal"})
        urllib.request.urlopen(requete, timeout=60).read()
        print("   etat d'avant remis partout (%s)." % avant["ledger_montant"])

    conn.close()
    return 0 if verts == len(controles) else 1


if __name__ == "__main__":
    raise SystemExit(main())
