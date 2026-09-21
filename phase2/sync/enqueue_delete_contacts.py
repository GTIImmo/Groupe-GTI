#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MENAGE DES CONTACTS D'ESSAI — enfile les suppressions.        21/09/2026

POURQUOI UN OUTIL PLUTOT QU'UN CLIC. Le bouton « Supprimer » de la fiche fait
exactement ce que fait ce script : il pose un travail `delete_hektor_contact`
dans `app_console_job`, avec la phrase de confirmation, et le worker s'en
charge. Mais il demande d'ouvrir chaque fiche -- ce qui declenche une relecture
chez Hektor au passage -- et de taper la phrase une fois par contact. Pour un
menage d'essais, c'est long et c'est fragile.

C'est le jumeau de `enqueue_delete_drafts.py`, ecrit le 07/09 pour la meme
raison du cote des brouillons.

⚠ CE SCRIPT ECRIT CHEZ HEKTOR, par l'intermediaire du worker. La suppression
  d'un contact est IRREVERSIBLE chez lui. D'ou :
    - DRY-RUN PAR DEFAUT : sans --apply il montre et n'enfile rien ;
    - un PLAFOND (SAFETY_MAX) ;
    - la RAISON est obligatoire et voyage dans la charge (`source`), pour
      qu'on sache dans six mois pourquoi ces fiches ont disparu.

⚠ LA PHRASE DE CONFIRMATION SE COMPOSE SUR LE NUMERO DEMANDE. Depuis le 21/09
  le worker accepte l'identite de l'app OU le numero de Hektor -- les deux
  designent la meme personne. Avant ce correctif, un contact ne dans l'app ne
  pouvait pas etre supprime : la phrase de l'ecran portait 10 000 002 et le
  worker attendait 605 453.

Usage :
  python enqueue_delete_contacts.py --ids 605450,605453 --raison "essais L4-b"
  python enqueue_delete_contacts.py --ids 605450 --raison "..." --apply
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
CANDIDATS_ENV = [
    RACINE / "apps" / "hektor-v1" / ".env",
    RACINE / ".env",
    RACINE / "Console" / ".env",
]

SAFETY_MAX = 20
JOB_PRIORITY = 12


def charger_env() -> None:
    for chemin in CANDIDATS_ENV:
        if not chemin.exists():
            continue
        for brut in chemin.read_text(encoding="utf-8", errors="ignore").splitlines():
            ligne = brut.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            cle, valeur = ligne.split("=", 1)
            cle = cle.strip()
            if cle and cle not in os.environ:
                os.environ[cle] = valeur.strip().strip('"').strip("'")


def reglages() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")
    return url.rstrip("/"), cle


def appel(url: str, cle: str, chemin: str, methode: str = "GET", corps=None, prefer=None):
    entetes = {"apikey": cle, "Authorization": f"Bearer {cle}",
               "Accept": "application/json", "Content-Type": "application/json"}
    if prefer:
        entetes["Prefer"] = prefer
    donnees = json.dumps(corps).encode("utf-8") if corps is not None else None
    requete = urllib.request.Request(f"{url}/rest/v1/{chemin}", data=donnees,
                                     headers=entetes, method=methode)
    with urllib.request.urlopen(requete, timeout=60) as reponse:
        texte = reponse.read().decode("utf-8")
        return json.loads(texte) if texte.strip() else []


def main() -> int:
    parser = argparse.ArgumentParser(description="Enfile des suppressions de contacts Hektor.")
    parser.add_argument("--ids", required=True,
                        help="Numeros separes par des virgules (identite de l'app OU numero Hektor).")
    parser.add_argument("--raison", required=True,
                        help="Pourquoi on supprime. Voyage dans la charge du travail.")
    parser.add_argument("--apply", action="store_true",
                        help="Enfile reellement. Sans lui, on montre et on ne fait rien.")
    args = parser.parse_args()

    ids = [x.strip() for x in args.ids.split(",") if x.strip()]
    if not ids:
        print("REFUS : aucun numero.")
        return 2
    if not all(x.isdigit() for x in ids):
        print("REFUS : les numeros doivent etre... des numeros.")
        return 2
    if len(ids) > SAFETY_MAX:
        print(f"REFUS : {len(ids)} contacts (plafond {SAFETY_MAX}).")
        return 3

    charger_env()
    url, cle = reglages()

    # ON NE SUPPRIME PAS CE QU'ON N'A PAS REGARDE. On relit chaque fiche et on
    # l'affiche : un numero tape de travers doit sauter aux yeux AVANT l'envoi.
    filtre = ",".join(ids)
    fiches = appel(url, cle,
                   f"app_contact_current?select=hektor_contact_id,hektor_target_id,nom,prenom,email"
                   f"&hektor_contact_id=in.({filtre})")
    connus = {str(f["hektor_contact_id"]): f for f in fiches}

    print(f"{len(ids)} numero(s) demande(s), {len(connus)} fiche(s) retrouvee(s) :")
    for numero in ids:
        fiche = connus.get(numero)
        if not fiche:
            print(f"  {numero}  ⚠ INTROUVABLE dans l'app -- le travail partira quand meme,")
            print(f"           le worker refusera s'il ne la voit pas non plus chez Hektor.")
            continue
        cible = fiche.get("hektor_target_id") or "(vide)"
        print(f"  {numero}  {fiche.get('prenom') or ''} {fiche.get('nom') or ''}"
              f"  <{fiche.get('email') or '-'}>  cible Hektor : {cible}")

    if not args.apply:
        print("\nDRY-RUN : rien n'a ete enfile. Ajouter --apply pour le faire.")
        return 0

    travaux = [{
        "job_type": "delete_hektor_contact",
        "status": "queued",
        "priority": JOB_PRIORITY,
        "payload_json": {
            "source": args.raison,
            "contact_id": numero,
            "hektor_contact_id": numero,
            "confirm_text": f"SUPPRIMER CONTACT {numero}",
        },
    } for numero in ids]

    crees = appel(url, cle, "app_console_job", methode="POST", corps=travaux,
                  prefer="return=representation")
    print(f"\n{len(crees)} travail(aux) enfile(s) :")
    for travail in crees:
        print(f"  {travail.get('id')}  contact {travail.get('payload_json', {}).get('hektor_contact_id')}")
    print("\nLe worker `actions` les prend en charge. Suivre avec app_console_job_log.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
