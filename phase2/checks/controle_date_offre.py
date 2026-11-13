#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LA SENTINELLE DES DATES D'OFFRE.                             13/11/2026

Elle existe parce que le defaut s'est produit DEUX FOIS sans que personne ne le
voie : le 11/11 (1 185 offres) puis le 12/11 (8 offres), et c'est Frederic qui l'a
signale les deux fois.

⭐ LE CORRECTIF DU 13/11 EST STRUCTUREL (le lecteur refuse la colonne `date` d'une
  offre quand le journal n'est pas vide), donc le defaut ne devrait plus revenir.
  ⛔ MAIS « ne devrait plus » n'est pas « ne peut plus ». Cette sentinelle est la
    pour que, s'il revient par un chemin qu'on n'a pas prevu, il CRIE au lieu de
    dormir.

═══════════════════════════════════════════════════════════════════════════════
LES QUATRE CONTROLES, et ce que chacun attrape
═══════════════════════════════════════════════════════════════════════════════
  ① UNE OFFRE DATEE APRES SA PROPRE VENTE -- impossible dans la vraie vie.
    ⭐ C'est le controle le plus LARGE : il attrape le defaut d'aujourd'hui, mais
      aussi tous ceux de la meme famille qu'on n'a pas encore rencontres.
  ② LE LECTEUR REND-IL LA COLONNE `date` D'UNE OFFRE DONT LE JOURNAL N'EST PAS
    VIDE ? C'est exactement ce que le correctif du 13/11 interdit : si ca
    reapparait, c'est que quelqu'un a defait la regle.
  ③ UNE OFFRE DATEE DANS LE FUTUR.
  ④ ⭐ LE TEMOIN POSITIF, et il est OBLIGATOIRE : le nombre d'offres DATEES.
    ⛔ Un controle qui ne mesure que des zeros ne sait pas s'il a vraiment
      regarde. Si ce nombre s'effondre, le controle le dit.

SORTIE : 0 tout va bien . 1 au moins un rouge . 2 pas pu mesurer.
LECTURE SEULE -- elle n'ecrit rien, nulle part.
"""
from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
import json
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                                   # noqa: BLE001
    pass

# ⚠ SEUILS. Le socle des offres datees est mesure le 13/11 : 11 159 sur 11 222.
#   On tolere qu'il vive (le parc bouge), on crie s'il S'EFFONDRE.
PLANCHER_OFFRES_DATEES = 10_500
PLANCHER_OFFRES = 10_000
# ⭐ LE SOCLE DES OFFRES SAISIES APRES COUP, mesure le 13/11 : 9. Il n'est pas un
#   defaut -- c'est une pratique reelle de l'agence. On crie s'il BOUGE, DANS LES
#   DEUX SENS : une chute dirait qu'on a perdu des dates, une montee qu'on en
#   fabrique.
SOCLE_OFFRE_APRES_VENTE = 9
TOLERANCE_SOCLE = 3


# ⚠ LE PROJET LIT DEUX FICHIERS .env, pas un seul -- DEFAULT_ENV_FILES dans
#   phase2/sync/pull_from_supabase.py. Les identifiants Supabase sont dans
#   apps/hektor-v1/.env, pas a la racine. Ne lire que le premier donnait
#   « SUPABASE_URL absente » alors qu'elle existait.
FICHIERS_ENV = (RACINE / ".env", RACINE / "apps" / "hektor-v1" / ".env")


def charger_env() -> None:
    for f in FICHIERS_ENV:
        if not f.exists():
            continue
        for ligne in f.read_text(encoding="utf-8", errors="replace").splitlines():
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            cle, _, val = ligne.partition("=")
            os.environ.setdefault(cle.strip(), val.strip().strip('"').strip("'"))


# ⭐ ON APPELLE LA FONCTION EN BASE, pas du SQL libre : c'est le patron des
#   controles du projet (ils lisent /rest/v1/...), et surtout UNE SEULE
#   DEFINITION du controle -- ecrit deux fois, il finirait par dire deux choses.
RPC = "/rest/v1/rpc/app_controle_date_offre"


def main() -> int:
    charger_env()
    # ⚠ LE REPLI SUR VITE_SUPABASE_URL N'EST PAS UN LUXE : la racine ne porte que
    #   SUPABASE_POOLER_HOST, et c'est apps/hektor-v1/.env qui porte l'URL -- sous
    #   le nom VITE_SUPABASE_URL. C'est exactement ce que fait affaire_ledger.py
    #   l. 1723. ⭐ Lecon 15 du projet : chercher comment le projet fait DEJA.
    url = (os.environ.get("SUPABASE_URL")
           or os.environ.get("VITE_SUPABASE_URL") or "").rstrip("/")
    cle = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
           or os.environ.get("SUPABASE_SERVICE_KEY") or "")
    if not url or not cle:
        print("⚠ URL ou clé de service absentes des deux .env -- PAS PU MESURER")
        return 2
    req = urllib.request.Request(
        url + RPC, data=b"{}", method="POST",
        headers={"apikey": cle, "Authorization": "Bearer " + cle,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            lignes = json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as e:
        # ⛔ UNE LECTURE RATEE N'EST JAMAIS UN VERT -- regle du projet.
        print("⚠ lecture impossible (%s) -- PAS PU MESURER, ce n'est PAS un vert"
              % str(e)[:120])
        return 2
    if not lignes:
        print("⚠ la requête n'a rien rendu -- PAS PU MESURER")
        return 2
    d = lignes[0] if isinstance(lignes, list) else lignes

    print("=" * 74)
    print("SENTINELLE DES DATES D'OFFRE")
    print("=" * 74)
    rouge = []

    def dire(ok, libelle, valeur, attendu):
        marque = "  OK  " if ok else " ROUGE"
        print("  [%s] %-44s %8s   (%s)" % (marque, libelle, valeur, attendu))
        if not ok:
            rouge.append(libelle)

    # ④ LE TEMOIN POSITIF D'ABORD : il dit si on a vraiment regarde
    offres = int(d.get("offres") or 0)
    datees = int(d.get("offres_datees") or 0)
    dire(offres >= PLANCHER_OFFRES, "TEMOIN : offres lues", offres,
         "au moins %d" % PLANCHER_OFFRES)
    dire(datees >= PLANCHER_OFFRES_DATEES, "TEMOIN : offres datees", datees,
         "au moins %d -- socle du 13/11 : 11 159" % PLANCHER_OFFRES_DATEES)

    # ⭐⭐ LE SOCLE, TOLERE ET SURVEILLE -- pas declare rouge.
    #   Mesure le 12/11 puis le 13/11 : des offres SAISIES APRES COUP, pas des
    #   dates fausses. L'essai du chainage le tolere deja sous le nom
    #   SOCLE_BLOC_APRES_LA_VENTE. ⛔ « Un essai qui crie tous les jours n'est plus
    #   un essai » : on juge L'ECART au socle, jamais l'absence -- et le nombre
    #   reste AFFICHE pour qu'on le voie bouger.
    socle = int(d.get("offre_apres_sa_vente") or 0)
    dire(abs(socle - SOCLE_OFFRE_APRES_VENTE) <= TOLERANCE_SOCLE,
         "offres datees APRES leur vente (socle tolere)", socle,
         "%d +/- %d -- on juge l'ECART" % (SOCLE_OFFRE_APRES_VENTE, TOLERANCE_SOCLE))
    dire(int(d.get("date_lue_journal_non_vide") or 0) == 0,
         "`date` lue alors que le journal n'est pas vide",
         d.get("date_lue_journal_non_vide"), "0 -- la regle du 13/11")
    dire(int(d.get("offre_dans_le_futur") or 0) == 0,
         "une offre datee dans le FUTUR", d.get("offre_dans_le_futur"), "0")

    print("-" * 74)
    if rouge:
        print("⛔ %d CONTROLE(S) ROUGE(S) :" % len(rouge))
        for r in rouge:
            print("     . " + r)
        print()
        print("  ⭐ SI c'est « `date` lue alors que le journal n'est pas vide » :")
        print("    quelqu'un a defait la regle du 13/11. Voir la migration")
        print("    date_offre_jamais_l_horodatage_d_un_mouvement_2026_11_13.")
        return 1
    print("✅ tout est vert -- et le témoin positif confirme qu'on a bien mesuré.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
