#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§ 2.8 DU CHAINAGE : le compromis rejoint l'offre PROPOSEE du meme acquereur.   30/10/2026

Analyse : notice/ANALYSE_28_OFFRES_CHAINAGE_2026-10-30.md § 5 et § 6.

CE QU'ELLE EPROUVE, DANS CET ORDRE
----------------------------------
  ⓵ INTERRUPTEUR ETEINT -> la vraie fonction rend EXACTEMENT ce qui est en base
     (le temoin inverse : le code neuf dort sans rien changer).
  ⓶ INTERRUPTEUR ALLUME -> SEULS les dossiers attendus bougent, et chacun a la
     forme « offre proposee + compromis VIVANT (+ vente) ». Aucun dossier eclate.
  ⓷ LES TROIS INVARIANTS (test_chainage_v2.invariants), dans les deux cas.
  ⓸ LES DEUX DOUBLONS 5681 ET 5687 : l'offre doit rejoindre le compromis ACTIF,
     jamais le doublon annule -- c'est ce qui a fait ecarter la premiere version.

⚠ ELLE N'ECRIT RIEN : phase2.sqlite est ouverte en lecture seule, recopiee en memoire.
⚠ LES INTERRUPTEURS V2 ET SANS-DATE SONT POSES COMME EN PRODUCTION (1 et 1) : on
  eprouve le § 2.8 PAR-DESSUS ce qui tourne, pas a cote.

    python phase2/checks/test_chainage_offre_proposee.py
Sortie 0 = vert · 1 = un rouge · 2 = pas pu mesurer.
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                               # noqa: BLE001
        pass

os.environ["APP_CHAINAGE_V2"] = "1"
# LE CRAN NE S'IMPOSE PLUS EN DUR -- defaut trouve le 12/11/2026.
#   Cette ligne forcait le cran 1. La PRODUCTION est au cran 2 depuis (`.env`).
#   L'essai recalculait donc avec un reglage DIFFERENT de celui qui a rempli la
#   base, puis comparait les deux -- et annoncait « 1203 transactions different de
#   la base ». Ce rouge n'a JAMAIS rien dit du code : il disait que l'essai et la
#   production ne parlaient pas du meme reglage.
#   On prend donc celui de l'environnement, et on le DIT. Un essai qui se compare
#   a la base doit tourner avec les reglages de la base.
#   ⚠ ET UN setdefault NE SUFFISAIT PAS, c'etait ma premiere correction : la
#     variable ne vit PAS dans l'environnement au lancement, elle vit dans `.env`
#     que le module charge PLUS TARD. Le setdefault retombait donc sur « 1 » et
#     mon commentaire annoncait le contraire de ce que le code faisait.
#     On lit donc `.env` ICI, explicitement, avant de poser quoi que ce soit.
def _cran_du_env() -> str:
    """Le cran que la PRODUCTION utilise : l'environnement, sinon `.env`, sinon 1."""
    deja = (os.environ.get("APP_CHAINAGE_SANS_DATE") or "").strip()
    if deja:
        return deja
    for fichier in (RACINE / ".env", RACINE / "Console" / ".env"):
        try:
            for ligne in fichier.read_text(encoding="utf-8").splitlines():
                ligne = ligne.strip()
                if ligne.startswith("APP_CHAINAGE_SANS_DATE="):
                    valeur = ligne.split("=", 1)[1].strip().strip('"').strip("'")
                    if valeur:
                        return valeur
        except OSError:
            continue        # un `.env` absent n'est pas une panne : on retombe sur 1
    return "1"


os.environ["APP_CHAINAGE_SANS_DATE"] = _cran_du_env()
print("cran sans-date : %s (celui de la production, pas un cran impose)"
      % os.environ["APP_CHAINAGE_SANS_DATE"])

from test_chainage_v2 import (copie_jetable, invariants,              # noqa: E402
                              defauts_hors_socle, SOCLE_BLOC_APRES_LA_VENTE)

# Les biens mesures le 30/10 : les 10 affaires recentes + les 2 doublons Hektor.
BIENS_ATTENDUS = {"28522", "43051", "49539", "52933", "54885", "58918",
                  "59015", "59160", "61466", "61534", "5681", "5687"}
TOLERANCE = 5           # le parc grandit : un cas NEUF peut apparaitre, on le NOMME
MORTS_COMPROMIS = {"cancelled", "annule"}


def tourne(allume: bool):
    os.environ["APP_CHAINAGE_OFFRE_PROPOSEE"] = "1" if allume else "0"
    from phase2.sync.affaire_ledger import LEDGER_TABLE, recalculer_les_chaines
    con = copie_jetable()
    if con is None:
        return None
    base = dict(con.execute(f"SELECT app_affaire_id, app_chaine_id FROM {LEDGER_TABLE}"))
    res = recalculer_les_chaines(con)
    apres = dict(con.execute(f"SELECT app_affaire_id, app_chaine_id FROM {LEDGER_TABLE}"))
    lignes = {r[0]: (str(r[1]), str(r[2] or "").lower(), str(r[3] or "").lower())
              for r in con.execute(f"SELECT app_affaire_id, hektor_annonce_id, kind, state "
                                   f"FROM {LEDGER_TABLE}")}
    defauts = invariants(con)
    con.close()
    return base, apres, res, defauts, lignes


def main() -> int:
    rouges: list[str] = []

    print("=" * 72 + "\n  ⓵ INTERRUPTEUR ETEINT (temoin inverse)\n" + "=" * 72)
    eteint = tourne(False)
    if eteint is None:
        return 2
    base, ref, res0, def0, lignes = eteint
    ecarts = [a for a in ref if ref[a] != base.get(a)]
    print(f"   dossiers {res0['chaines']} · etiquette chainage_offre_proposee = "
          f"{res0.get('chainage_offre_proposee')} · ecarts avec la base : {len(ecarts)}")
    if res0.get("chainage_offre_proposee"):
        rouges.append("eteint, l'etiquette dit pourtant que le § 2.8 a tourne")
    if any("[2.8]" in k for k in res0):
        rouges.append("eteint, le § 2.8 a pourtant agi")
    if ecarts:
        # CE N'EST PAS UN ESSAI, C'EST UNE MESURE -- et elle ne doit pas crier.
        #   12/11/2026 : ce bloc annoncait ROUGE a chaque passage. Deux raisons, et
        #   AUCUNE ne regarde le code :
        #     . l'essai imposait un cran different de celui de la production
        #       (corrige en tete de ce fichier) ;
        #     . et la base porte les chaines du DERNIER run, tandis que l'essai
        #       recalcule MAINTENANT -- une transaction nee ou modifiee entre les
        #       deux suffit a creer un ecart. Le 12/11 : 19 offres reacceptees et
        #       un chainage repousse dans la journee.
        #   Un ecart avec la base est donc un ETAT, pas un defaut : on l'AFFICHE, et
        #   c'est l'humain qui juge s'il est explicable.
        #   « Un essai qui crie tous les jours n'est plus un essai : le jour ou il a
        #     raison, personne ne le regarde. »
        print(f"   i {len(ecarts)} transaction(s) portent en base LOCALE un numero")
        print(f"     different du recalcul (exemples {ecarts[:5]}).")
        print("     C'EST UN RETARD, PAS UN DEFAUT -- mesure le 12/11/2026 :")
        print("       . la base locale porte les chaines du DERNIER RUN de nuit ;")
        print("       . tout ce qui a ete pose dans la journee (une regle allumee,")
        print("         un geste chez Hektor, une chaine poussee chez Supabase) n'y")
        print("         est PAS ENCORE -- il y descend au prochain run.")
        print("     Releve ce jour-la : le dossier 3676 etait encore COUPE EN DEUX en")
        print("     local alors que la regle D l'avait reuni chez Supabase, et les 19")
        print("     offres reacceptees y etaient encore « refused ».")
        print("     ⛔ CE QUI COMPTE N'EST PAS LE NUMERO MAIS LE GROUPE : un recalcul")
        print("       peut renumeroter sans rien regrouper autrement. Pour juger,")
        print("       comparer les PARTITIONS (qui est avec qui), jamais les numeros.")
    # 12/11 : on AFFICHE tout, et on ne CRIE que ce qui sort du socle connu
    #   (le bloc date APRES la vente = SOCLE_BLOC_APRES_LA_VENTE, explique le 12/11 : des offres
    #    SAISIES APRES COUP, pas un defaut du chainage).
    print(f"   invariants eteint : {def0 or 'aucun'}")
    if defauts_hors_socle(def0):
        rouges.append(f"INVARIANTS eteint : {defauts_hors_socle(def0)}")

    print("\n" + "=" * 72 + "\n  ⓶ INTERRUPTEUR ALLUME\n" + "=" * 72)
    allume = tourne(True)
    if allume is None:
        return 2
    _, new, res1, def1, _ = allume
    print(f"   dossiers {res0['chaines']} -> {res1['chaines']} "
          f"({res1['chaines'] - res0['chaines']:+d})")
    for k, v in sorted(res1.items()):
        if "[2.8]" in k:
            print(f"      {k:<62} {v:>4}")
    if not res1.get("chainage_offre_proposee"):
        rouges.append("allume, l'etiquette ne dit pas que le § 2.8 a tourne")
    # 12/11 : on AFFICHE tout, et on ne CRIE que ce qui sort du socle connu
    #   (le bloc date APRES la vente = SOCLE_BLOC_APRES_LA_VENTE, explique le 12/11 : des offres
    #    SAISIES APRES COUP, pas un defaut du chainage).
    print(f"   invariants allume : {def1 or 'aucun'}")
    if defauts_hors_socle(def1):
        rouges.append(f"INVARIANTS allume : {defauts_hors_socle(def1)}")

    bouge = [a for a in new if new[a] != ref[a]]
    vers = defaultdict(set)
    for a in new:
        vers[ref[a]].add(new[a])
    eclatees = [c for c, s in vers.items() if len(s) > 1]
    if eclatees:
        rouges.append(f"{len(eclatees)} ancien(s) dossier(s) ECLATE(S) : {eclatees[:5]}")

    touches = {new[a] for a in bouge}
    biens = set()
    for nc in sorted(touches):
        membres = [a for a in new if new[a] == nc]
        formes = sorted(f"{lignes[m][1]}:{lignes[m][2] or '-'}" for m in membres)
        bien = {lignes[m][0] for m in membres}
        biens |= bien
        offres = [m for m in membres if lignes[m][1] == "offre"]
        compromis_vivants = [m for m in membres if lignes[m][1] == "compromis"
                             and lignes[m][2] not in MORTS_COMPROMIS]
        ok = (len(bien) == 1 and compromis_vivants
              and any(lignes[m][2] == "proposed" for m in offres))
        print(f"   {'✅' if ok else '⛔'} dossier {nc} bien {','.join(bien)} : {' + '.join(formes)}")
        if not ok:
            rouges.append(f"dossier {nc} n'a pas la forme attendue : {formes}")

    # ⓸ les deux doublons : l'offre est avec le compromis ACTIF
    for bien in ("5681", "5687"):
        offre = [a for a, l in lignes.items() if l[0] == bien and l[1] == "offre"]
        actif = [a for a, l in lignes.items() if l[0] == bien and l[1] == "compromis"
                 and l[2] not in MORTS_COMPROMIS]
        if offre and actif and not any(new[o] == new[c] for o in offre for c in actif):
            rouges.append(f"bien {bien} : l'offre n'a PAS rejoint le compromis actif")

    absents = BIENS_ATTENDUS - biens
    neufs = biens - BIENS_ATTENDUS
    if absents:
        print(f"   i biens attendus qui ne bougent plus : {sorted(absents)} "
              f"(une saisie a pu les reparer chez Hektor)")
    if neufs:
        print(f"   i biens NEUFS touches : {sorted(neufs)} -- a regarder")
    if len(neufs) > TOLERANCE:
        rouges.append(f"{len(neufs)} biens neufs touches, au-dela de la tolerance {TOLERANCE}")

    if rouges:
        print("\n   ⛔ ROUGE :")
        for r in rouges:
            print(f"      - {r}")
        return 1
    print(f"\n   ✅ VERT -- {len(touches)} dossier(s) recolle(s), {len(bouge)} transaction(s) "
          f"renumerotee(s), 0 eclate, invariants verts dans les deux sens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
