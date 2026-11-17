#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LES 129 POSABLES RECOUPENT-ELLES LES 195 DU 16/11 ?             17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\audit_doublon_avec_les_195_2026-11-17.py

⛔ LECTURE SEULE.

⭐⭐⭐ SA QUESTION, ET ELLE EST CAPITALE : « Mais on a pas deja ajouter les offres
  d'achat 195 ? ». Les 195 posees le 16/11 comptent **160 OFFRES** (96 refused +
  64 accepted) et 35 compromis. Je propose d'en poser 102 de plus. SI CE SONT LES
  MEMES, on fabriquerait 102 doublons dans le registre.

LE RAISONNEMENT NE SUFFIT PAS. Logiquement, mon audit ne PEUT PAS les recompter :
il demande « la chaine liee a-t-elle une transaction de ce type ? », et les 195
SONT dans le registre avec leur `kind`. Mais un raisonnement n'est pas une mesure --
et deux fois aujourd'hui, un raisonnement juste m'a donne un chiffre faux.
➡ ON MESURE, par TROIS chemins independants.

  ① les id_unique du lot posable sont-ils DEJA porteurs d'une transaction
     `transaction_origine = 'classeur'` ? (l'intersection directe)
  ② leurs CHAINES portent-elles deja une transaction d'origine classeur ?
     (plus large : meme si le type differe)
  ③ TEMOIN POSITIF : les id_unique des 195 sont-ils bien ABSENTS du lot posable ?
     Si l'intersection est vide dans les deux sens, c'est sur.
"""
from __future__ import annotations

import csv
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "monitoring"))
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import check_gti_health as cgh                                      # noqa: E402

AUDIT = RACINE / "notice" / "AUDIT_C5_LOT_B_2026-11-17.csv"
LOT_API = 60


def client():
    for f in (RACINE / ".env", RACINE / "backend" / ".env",
              RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    cle = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise SystemExit("⛔ pas d'identifiants Supabase.")
    return cgh.SupabaseClient(url, cle, timeout_seconds=30)


def tout_lire(cl, table, select, ordre, params=None):
    out, pas, dep = [], 1000, 0
    while True:
        p = {"select": select, "order": ordre, "limit": pas, "offset": dep}
        if params:
            p.update(params)
        lot = cl.get(table, p) or []
        out.extend(lot)
        if len(lot) < pas:
            return out
        dep += pas


def main() -> int:
    print("=== LES 129 POSABLES RECOUPENT-ELLES LES 195 DU 16/11 ? ===")
    print()
    with AUDIT.open(encoding="utf-8-sig", newline="") as f:
        manque = list(csv.DictReader(f, delimiter=";"))
    #: ⛔⛔ LA MEME FAUTE D'ACCENT, EN MIROIR, ET LE GARDE-FOU L'A ATTRAPEE. La
    #:   base porte « sûre » ; mais l'audit NORMALISE avant d'ecrire, donc le CSV
    #:   porte « sure ». J'ai cherche « sûre » et obtenu 0 POSABLE sur 233 lignes.
    #:   ➡ ON ACCEPTE LES DEUX FORMES, une fois pour toutes, et on ne se fie plus
    #:     a sa memoire pour savoir laquelle est ou.
    posables = [m for m in manque
                if m["confiance_du_lien"].strip().lower() in ("sure", "sûre")
                and m["chaine_VIVANTE"].strip().lower() in ("false", "0", "")]
    print("le CSV de l'audit : %d manquantes" % len(manque))
    print("le lot POSABLE (sûre + chaine close) : %d" % len(posables))
    for k, n in Counter(m["type"] for m in posables).most_common():
        print("   %-10s %4d" % (k, n))
    #: ⛔ TEMOIN : si le lot posable est vide, c'est le filtre qui est faux
    if not (100 <= len(posables) <= 160):
        print("⛔ LE LOT POSABLE A BOUGE (%d, attendu ~129) -- le filtre est suspect."
              % len(posables))
        return 2
    ids_posables = {m["id_unique"] for m in posables}
    print()

    cl = client()
    #: les 195 : on les retrouve par transaction_origine
    les_195 = tout_lire(cl, "app_affaire_ledger",
                        "app_affaire_id,kind,state,app_chaine_id",
                        "app_affaire_id", {"transaction_origine": "eq.classeur"})
    print("les transactions d'origine « classeur » : %d" % len(les_195))
    for k, n in Counter("%s/%s" % (r["kind"], r["state"]) for r in les_195).most_common():
        print("   %-22s %4d" % (k, n))
    if len(les_195) != 195:
        print("⚠ ce n'est plus 195 mais %d -- on continue, en le disant." % len(les_195))
    ids_195 = {r["app_affaire_id"] for r in les_195}
    chaines_195 = {r["app_chaine_id"] for r in les_195 if r["app_chaine_id"]}
    print()

    #: le pont id_unique <-> transaction
    liens = tout_lire(cl, "app_classeur_lien", "id_unique,app_affaire_id",
                      "ligne_classeur")
    par_id = defaultdict(list)
    for r in liens:
        par_id[str(r["id_unique"]).strip()].append(r["app_affaire_id"])
    #: et les id_unique QUI ONT RECU une des 195
    id_unique_des_195 = {i for i, aff in par_id.items()
                         if any(a in ids_195 for a in aff)}
    print("=== ① L'INTERSECTION DIRECTE ===")
    print("   id_unique qui ont RECU une des 195      : %d" % len(id_unique_des_195))
    inter = ids_posables & id_unique_des_195
    print("   ⭐ dont ils sont AUSSI dans le lot posable : %d" % len(inter))
    if inter:
        print("   ⛔⛔ RECOUPEMENT -- les voici :")
        for i in sorted(inter)[:20]:
            d = [m for m in posables if m["id_unique"] == i]
            for m in d:
                print("      %-10s %-10s %s  annonce %s"
                      % (i, m["type"], m["date_classeur"], m["annonce"]))
    else:
        print("   ✅ AUCUN RECOUPEMENT par ce chemin.")
    print()

    print("=== ② PAR LES CHAINES (plus large : meme si le type differe) ===")
    chaines_posables = {m["chaine"] for m in posables if m["chaine"]}
    comm = {str(c) for c in chaines_posables} & {str(c) for c in chaines_195}
    print("   chaines du lot posable            : %d" % len(chaines_posables))
    print("   chaines qui portent une des 195   : %d" % len(chaines_195))
    print("   ⭐ chaines COMMUNES                : %d" % len(comm))
    if comm:
        print("   ⚠ une chaine commune ne veut pas dire un doublon : elle peut")
        print("     avoir recu une OFFRE le 16/11 et manquer son COMPROMIS.")
        print("     On regarde donc le TYPE, ligne par ligne :")
        par_chaine_195 = defaultdict(set)
        for r in les_195:
            if r["app_chaine_id"]:
                par_chaine_195[str(r["app_chaine_id"])].add(r["kind"])
        vrais = [m for m in posables
                 if str(m["chaine"]) in comm
                 and m["type"] in par_chaine_195.get(str(m["chaine"]), set())]
        print("      ⛔ MEME CHAINE **ET** MEME TYPE (un vrai doublon) : %d" % len(vrais))
        for m in vrais[:15]:
            print("         %-10s %-10s chaine %s  %s"
                  % (m["id_unique"], m["type"], m["chaine"], m["date_classeur"]))
        if not vrais:
            print("      ✅ AUCUN : les chaines communes manquent un AUTRE type.")
            #: ⭐ et on dit lequel, pour que ce soit comprehensible
            for m in [x for x in posables if str(x["chaine"]) in comm][:8]:
                print("         %-10s il manque un %-10s ; la chaine a deja : %s"
                      % (m["id_unique"], m["type"],
                         " ".join(sorted(par_chaine_195.get(str(m["chaine"]), set())))))
    print()

    print("=== ③ ⛔ LE TEMOIN POSITIF : LE FILTRE SAIT-IL TROUVER UN RECOUPEMENT ? ===")
    #: on cherche l'intersection avec TOUTES les manquantes, pas seulement les
    #: posables. Si elle est vide AUSSI, c'est que la methode ne sait rien trouver.
    ids_tous = {m["id_unique"] for m in manque}
    inter_tous = ids_tous & id_unique_des_195
    print("   id_unique de TOUTES les manquantes qui ont recu une des 195 : %d"
          % len(inter_tous))
    if inter_tous:
        print("   ✅ la methode SAIT trouver un recoupement -- donc le 0 ci-dessus")
        print("     (s'il y en a un) est un VRAI zero.")
        for i in sorted(inter_tous)[:10]:
            for m in [x for x in manque if x["id_unique"] == i][:1]:
                print("      %-10s il manque un %-10s . chaine vivante %s . lien %s"
                      % (i, m["type"], m["chaine_VIVANTE"], m["confiance_du_lien"]))
    else:
        print("   ⚠ AUCUN recoupement nulle part : soit c'est vrai, soit le pont")
        print("     id_unique <-> transaction est mal lu. A REGARDER.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
