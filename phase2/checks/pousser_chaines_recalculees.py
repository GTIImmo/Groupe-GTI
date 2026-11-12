# -*- coding: utf-8 -*-
"""POUSSER LES DOSSIERS RECALCULES -- UNE SEULE COLONNE          12/11/2026

    .venv\\Scripts\\python.exe phase2\\checks\\pousser_chaines_recalculees.py
    .venv\\Scripts\\python.exe phase2\\checks\\pousser_chaines_recalculees.py --envoyer

⛔⛔ EN BLANC PAR DEFAUT. Sans --envoyer, ce programme COMPTE et n'ecrit RIEN.

POURQUOI IL EXISTE. Allumer un interrupteur de chainage ne change rien avant le run
de 05:00 : les dossiers se recalculent la nuit. La seule commande qui les appliquerait
tout de suite est `affaire_ledger.py --push`, et celle-la pousse TOUT LE REGISTRE
depuis le miroir local -- c'est le geste que le projet s'interdit en journee :

    07/09/2026, 06:38  un compromis est annule depuis l'app
                07:52  un `--push` lance a la main pousse le miroir de 04:18
                       -> l'annulation est EFFACEE chez Supabase

⭐ CE PROGRAMME NE FAIT PAS CA. Il n'envoie QUE `app_chaine_id`, et seulement sur les
  lignes dont le dossier change. Aucun etat, aucune date, aucun montant, aucun nom.
  Tout ce qu'un collaborateur a saisi depuis 05:00 reste intact.

⭐ ET IL EST SANS CONSEQUENCE DURABLE : le run de nuit recalcule les dossiers DE ZERO,
  avec les memes interrupteurs et les memes donnees. Il retrouvera donc le meme
  resultat. Ce programme ne fait qu'avancer l'horloge de quelques heures.

LA METHODE, et elle est volontairement etroite :
  1. le registre local est copie EN MEMOIRE -- phase2.sqlite n'est jamais ouvert en
     ecriture, donc aucun verrou, et aucune gene pour les taches qui tournent ;
  2. le chainage est rejoue sur cette copie, avec les interrupteurs du .env ;
  3. on lit chez Supabase les dossiers actuels, et on ne garde que les ECARTS ;
  4. en --envoyer, un PATCH par ligne ecartee, sur la seule colonne app_chaine_id.

LES GARDES :
  . refus si le run de nuit tourne (une tache GTI active) -- code 3 ;
  . refus si plus de 20 % du registre bougerait -- code 4. Un interrupteur mal
    compris deplacerait tout ; un recalcul normal deplace ~10 % au plus.
  . le temoin des invariants est verifie APRES calcul, AVANT d'envoyer : aucun
    dossier a deux ventes, aucun a deux compromis vivants -- code 5 sinon.

Codes de sortie : 0 rien a faire ou pose · 1 panne · 3 run en cours · 4 trop de
                  mouvement · 5 un invariant casse
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

from phase2.sync import affaire_ledger as AL     # noqa: E402

BASE_LOCALE = RACINE / "phase2" / "phase2.sqlite"
TABLE = "app_affaire_ledger"
PLAFOND_MOUVEMENT = 0.20


def charger_env() -> tuple[str, str]:
    for rel in (".env", "apps/hektor-v1/.env"):
        chemin = RACINE / rel
        if not chemin.exists():
            continue
        for ligne in chemin.read_text(encoding="utf-8", errors="replace").splitlines():
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            cle, valeur = ligne.split("=", 1)
            cle, valeur = cle.strip(), valeur.strip().strip('"').strip("'")
            if cle and cle not in os.environ:
                os.environ[cle] = valeur
    url = (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "").rstrip("/")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not (url and cle):
        raise SystemExit("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis")
    return url, cle


def un_run_tourne() -> str:
    """Une tache planifiee GTI est-elle en cours ?

    ⚠ ON NE LIT PAS LE TEXTE FRANCAIS DE schtasks. Le 21/10, un garde-fou lisait
      « Pret / En cours d'execution » et s'est trompe pendant que le run tournait.
      On lit donc le CODE d'etat (/fo csv), colonne « Status », valeur 'Running'.
    """
    try:
        sortie = subprocess.run(
            ["schtasks", "/query", "/fo", "csv", "/v"],
            capture_output=True, text=True, timeout=60, encoding="utf-8",
            errors="replace").stdout or ""
    except Exception:                                            # noqa: BLE001
        return ""      # on ne sait pas : on ne bloque pas sur une mesure ratee
    for ligne in sortie.splitlines():
        if "GTI" not in ligne:
            continue
        if '"Running"' in ligne or ",Running," in ligne:
            return ligne.split(",")[1].strip('"') if "," in ligne else "une tache GTI"
    return ""


def copie_en_memoire() -> sqlite3.Connection:
    src = sqlite3.connect(f"file:{BASE_LOCALE}?mode=ro", uri=True, timeout=120)
    src.execute("PRAGMA busy_timeout=120000")
    m = sqlite3.connect(":memory:")
    cols = [c[1] for c in src.execute(f"pragma table_info({TABLE})")]
    m.execute(f"create table {TABLE} ({','.join(cols)})")
    m.executemany(f"insert into {TABLE} values ({','.join('?' * len(cols))})",
                  src.execute(f"select * from {TABLE}"))
    m.execute(f"create unique index ix on {TABLE}(app_affaire_id)")
    m.commit()
    src.close()
    return m


def lire_supabase(url: str, cle: str, chemin: str) -> list[dict]:
    sorties, apres = [], 0
    while True:
        requete = urllib.request.Request(
            f"{url}/rest/v1/{chemin}&limit=1000&offset={apres}",
            headers={"apikey": cle, "Authorization": f"Bearer {cle}"})
        with urllib.request.urlopen(requete, timeout=120) as reponse:
            page = json.load(reponse)
        if not page:
            return sorties
        sorties += page
        apres += 1000


def patcher(url: str, cle: str, app_affaire_id: int, chaine: int | None) -> None:
    corps = json.dumps({"app_chaine_id": chaine}).encode("utf-8")
    requete = urllib.request.Request(
        f"{url}/rest/v1/{TABLE}?app_affaire_id=eq.{app_affaire_id}",
        data=corps, method="PATCH",
        headers={"apikey": cle, "Authorization": f"Bearer {cle}",
                 "Content-Type": "application/json", "Prefer": "return=minimal"})
    with urllib.request.urlopen(requete, timeout=60) as reponse:
        if reponse.status not in (200, 204):
            raise RuntimeError(f"PATCH {app_affaire_id} -> HTTP {reponse.status}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pousser les dossiers recalcules -- la colonne app_chaine_id seule")
    parser.add_argument("--envoyer", action="store_true",
                        help="ecrire reellement (sans ce drapeau : en blanc)")
    parser.add_argument("--limite", type=int, default=0,
                        help="n'envoyer que les N premiers ecarts (0 = tous)")
    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                            # noqa: BLE001
        pass

    url, cle = charger_env()
    AL.chainage_v2_actif()
    print("les interrupteurs du chainage :")
    for nom, lecture in (("V2", AL.chainage_v2_actif),
                         ("vente seule (C)", AL.chainage_vente_seule_actif),
                         ("offre acceptee seule (B)", AL.chainage_offre_acceptee_seule_actif),
                         ("compromis annule (A)", AL.chainage_compromis_annule_seul_actif),
                         ("meme acheteur (D)", AL.chainage_meme_acheteur_actif),
                         ("rattachements a la main", AL.chainage_rattachement_manuel_actif)):
        print(f"   {nom:<26} {'on' if lecture() else 'off'}")
    print()

    occupe = un_run_tourne()
    if occupe:
        print(f"⛔ REFUS : une tache planifiee tourne ({occupe}). "
              f"On ne recalcule pas les dossiers pendant un run.")
        return 3

    con = copie_en_memoire()
    with contextlib.redirect_stdout(io.StringIO()):
        resultat = AL.recalculer_les_chaines(con)
    neuf = {int(a): (int(c) if c is not None else None)
            for a, c in con.execute(f"select app_affaire_id, app_chaine_id from {TABLE}")}
    genre = {int(a): (k, (s or "").lower())
             for a, k, s in con.execute(f"select app_affaire_id, kind, state from {TABLE}")}
    con.close()
    print(f"le chainage recalcule : {resultat['chaines']} dossiers")

    # ─── LES INVARIANTS, AVANT D'ENVOYER QUOI QUE CE SOIT ────────────────────
    par_dossier = defaultdict(list)
    for app_id, chaine in neuf.items():
        if chaine is not None:
            par_dossier[chaine].append(app_id)
    deux_ventes = [c for c, mb in par_dossier.items()
                   if sum(1 for a in mb if genre[a][0] == "vente") > 1]
    deux_compromis = [c for c, mb in par_dossier.items()
                      if sum(1 for a in mb if genre[a][0] == "compromis"
                             and genre[a][1] not in ("cancelled", "annule")) > 1]
    print(f"   dossiers a DEUX ventes            : {len(deux_ventes)}")
    print(f"   dossiers a DEUX compromis vivants : {len(deux_compromis)}")
    if deux_ventes or deux_compromis:
        print("⛔ REFUS : un invariant du projet est casse. Rien n'est envoye.")
        print(f"   deux ventes    : {sorted(deux_ventes)[:20]}")
        print(f"   deux compromis : {sorted(deux_compromis)[:20]}")
        return 5
    print()

    # ─── LES ECARTS AVEC CE QUE SUPABASE PORTE ──────────────────────────────
    actuel = {int(l["app_affaire_id"]): l["app_chaine_id"]
              for l in lire_supabase(url, cle, f"{TABLE}?select=app_affaire_id,app_chaine_id&order=app_affaire_id.asc")}
    print(f"le registre chez Supabase : {len(actuel)} transactions")
    ecarts = []
    for app_id, chaine in sorted(neuf.items()):
        if app_id not in actuel:
            continue            # une ligne que Supabase n'a pas encore : le run la posera
        avant = actuel[app_id]
        avant = int(avant) if avant is not None else None
        if avant != chaine:
            ecarts.append((app_id, avant, chaine))
    part = (len(ecarts) / len(actuel)) if actuel else 0
    print(f"transactions dont le dossier CHANGE : {len(ecarts)}  ({part:.1%})")
    print(f"dossiers distincts avant : {len({a for _i, a, _n in ecarts if a is not None})}"
          f"   apres : {len({n for _i, _a, n in ecarts if n is not None})}")
    print()
    for app_id, avant, apres in ecarts[:15]:
        print(f"   transaction {app_id:<8} dossier {avant} -> {apres}")
    if len(ecarts) > 15:
        print(f"   ... et {len(ecarts) - 15} autres")
    print()

    if part > PLAFOND_MOUVEMENT:
        print(f"⛔ REFUS : {part:.1%} du registre bougerait, le plafond est "
              f"{PLAFOND_MOUVEMENT:.0%}. Rien n'est envoye.")
        return 4
    if not ecarts:
        print("rien a faire : Supabase porte deja ces dossiers.")
        return 0
    if not args.envoyer:
        print("EN BLANC : rien n'a ete ecrit. Ajouter --envoyer pour poser ces "
              f"{len(ecarts)} changements (colonne app_chaine_id SEULE).")
        return 0

    lot = ecarts[:args.limite] if args.limite > 0 else ecarts
    poses, rates = 0, []
    for app_id, _avant, apres in lot:
        try:
            patcher(url, cle, app_id, apres)
            poses += 1
        except (urllib.error.URLError, RuntimeError, OSError) as erreur:
            rates.append((app_id, str(erreur)[:120]))
            if len(rates) >= 10:
                print("⛔ ARRET : 10 echecs. On ne continue pas a l'aveugle.")
                break
        if poses % 200 == 0 and poses:
            print(f"   ... {poses} poses")
    print()
    print(f"poses : {poses} / {len(lot)}")
    if rates:
        print(f"echecs : {len(rates)}")
        for app_id, message in rates[:10]:
            print(f"   {app_id} : {message}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
