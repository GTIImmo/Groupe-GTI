#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TACHE 3.3 DU CHANTIER CLASSEUR -- L'AUDIT DES COLONNES QUI ONT UNE CASE.

LECTURE SEULE DE BOUT EN BOUT. N'ecrit ni en base, ni chez Hektor, ni dans le
classeur. Il lit le rapport du gel deja produit (A4_RAPPORT_GEL_TOUS_LES_CHAMPS)
et la base, et il repond a UNE question : combien de valeurs 3.3 pose-t-elle
VRAIMENT, et dans quelle case ?

(!) LE PERIMETRE DU PLAN ETAIT PERIME. Le plan annonce « les 7 colonnes P S T W
  AB AD (+ AF comparer) ». La source de verite est l'artefact des 38 choix de
  Frederic (collection `choix`), et il dit, depuis le 09/11 a 13:13 :
      P vides . S vides . T vides . W vides . AF comparer
      AB rien . AD rien      <- SORTIES du perimetre
  ==> 3.3 porte donc QUATRE colonnes a poser et UNE a comparer, pas sept.

(!!) ET « classeur seul » NE VEUT PAS DIRE « une case vide a remplir ». C'est
  la decouverte de cet audit. Le rapport du gel cherche la date de l'offre sur la
  transaction OFFRE RELIEE PAR LE GEL. Quand cette transaction n'existe pas, il
  rend « classeur seul » -- ce qui se lit « il nous manque la donnee » alors que,
  le plus souvent, il nous manque LA TRANSACTION ENTIERE. Trois cas tres
  differents se cachent sous un seul mot :

      A  le gel la relie, sa date est vide     -> une CASE a remplir
      B  elle existe DANS LA CHAINE, avec sa
         date, mais le gel ne l'a pas reliee   -> RIEN a remplir, le rapport se
                                                 trompe -- a verifier au fond
      E  aucune transaction de ce role dans
         la chaine                             -> il faudrait la CREER, ce qui
                                                 n'est pas « remplir un vide »

(!) ET LE ZERO EST UN VIDE DEGUISE. Une commission a 0 chez nous n'est pas une
  valeur saisie, c'est une absence -- mais `verdict()` la range en « ECART »
  parce que 0 n'est pas la chaine vide. Le compte des « vides » les rate donc.
  (Lecon du projet : un zero ne se croit pas sans temoin positif.)

    python -X utf8 phase2/checks/audit_33_colonnes_qui_ont_une_case.py
    python -X utf8 phase2/checks/audit_33_colonnes_qui_ont_une_case.py --rapport notice/A4_...csv
"""
from __future__ import annotations

import argparse
import collections
import csv
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

from rapport_gel_tous_les_champs import (  # noqa: E402
    client, lire_tout, nombre, date_du_classeur_tolerante, date_de_chez_nous)

# (colonne du classeur, lettre, role de la transaction qui porte la donnee)
LES_DATES = (("Offre Achat", "S", "offre"),
             ("Compromis", "T", "compromis"),
             ("Vente Fixee", "W", "vente"))


def dernier_rapport() -> Path:
    cands = sorted((RACINE / "notice").glob("A4_RAPPORT_GEL_TOUS_LES_CHAMPS_*.csv"))
    if not cands:
        raise SystemExit("ARRET : aucun rapport du gel dans notice/")
    return cands[-1]


def annee_de_la_ligne(l: dict):
    """L'annee de l'affaire, vue du classeur : la date la plus avancee d'abord."""
    for c in ("c_Vente Fixee", "c_Vente Prevue", "c_Compromis", "c_Offre Achat"):
        d = date_du_classeur_tolerante(l.get(c))
        if d:
            return d.year
    return "?"


def espaces(n) -> str:
    return format(int(n), ",d").replace(",", " ")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapport", default=None)
    args = ap.parse_args()
    chemin = Path(args.rapport) if args.rapport else dernier_rapport()
    print("rapport lu : %s" % chemin.name)
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        L = list(csv.DictReader(f, delimiter=";"))
    print("lignes rattachees : %d" % len(L))

    cl = client()
    liens = lire_tout(cl, "app_classeur_lien", "id_unique,app_affaire_id,role",
                      "id_unique.asc,app_affaire_id.asc")
    led = lire_tout(cl, "app_affaire_ledger",
                    "app_affaire_id,app_chaine_id,kind,state,date,date_acte,"
                    "honoraires_entree,commission_agence", "app_affaire_id.asc")
    print("gel %d liens . registre %d transactions" % (len(liens), len(led)))

    tx = {str(x["app_affaire_id"]): x for x in led}
    par_chaine: dict[str, list] = collections.defaultdict(list)
    for x in led:
        if x.get("app_chaine_id"):
            par_chaine[str(x["app_chaine_id"])].append(x)
    par_id: dict[str, list] = collections.defaultdict(list)
    for x in liens:
        par_id[str(x["id_unique"])].append(x)

    def les_miennes(iu: str) -> list[dict]:
        return [m for m in (tx.get(str(x["app_affaire_id"])) for x in par_id.get(iu, [])) if m]

    def les_voisines(mes: list[dict]) -> list[dict]:
        chaines = {str(m.get("app_chaine_id")) for m in mes if m.get("app_chaine_id")}
        return [y for ch in chaines for y in par_chaine.get(ch, [])]

    # --------------------------------- (1) LES TROIS DATES, cas par cas
    print("\n=== (1) LES DATES : ce que « classeur seul » cache vraiment ===")
    a_poser = 0
    for champ, lettre, role in LES_DATES:
        cs = [l for l in L if l["v_" + champ] == "classeur seul"]
        cpt = collections.Counter()
        desaccords = []
        for l in cs:
            mes = les_miennes(l["ID Unique"])
            if role in {str(m.get("kind") or "") for m in mes}:
                cpt["A . case vide -> A POSER"] += 1
                continue
            du_role = [y for y in les_voisines(mes) if str(y.get("kind") or "") == role]
            avec = [y for y in du_role if y.get("date")]
            if avec:
                dc = date_du_classeur_tolerante(l["c_" + champ])
                dn = date_de_chez_nous(avec[0].get("date"))
                if dc and dn and abs((dc - dn).days) <= 3:
                    cpt["B . existe dans la chaine, MEME date -> rien a faire"] += 1
                else:
                    cpt["B . existe dans la chaine, AUTRE date -> a regarder"] += 1
                    desaccords.append((l["ID Unique"], dc, dn))
            elif du_role:
                cpt["C . existe dans la chaine SANS date"] += 1
            elif not les_voisines(mes):
                cpt["D . aucune chaine"] += 1
            else:
                cpt["E . AUCUNE transaction de ce role -> il faudrait la CREER"] += 1
        print("\n  %s (%s) : %d lignes « classeur seul »" % (champ, lettre, len(cs)))
        for k, v in sorted(cpt.items()):
            print("     %-56s %4d" % (k, v))
        a_poser += cpt["A . case vide -> A POSER"]
        for iu, dc, dn in desaccords[:6]:
            print("       desaccord : %s classeur %s . nous %s" % (iu, dc, dn))
    print("\n  ==> TOTAL des DATES a poser (cas A) : %d" % a_poser)

    # --------------------------------- (2) LA COMMISSION
    print("\n=== (2) P Commission TTC : les « classeur seul » ===")
    cpt = collections.Counter()
    ans, som = collections.Counter(), collections.Counter()
    for l in [x for x in L if x["v_Commission TTC"] == "classeur seul"]:
        mes = les_miennes(l["ID Unique"])
        miennes = {str(m["app_affaire_id"]) for m in mes}
        cc = nombre(l["c_Commission TTC"])
        vals = []
        for y in les_voisines(mes):
            if str(y["app_affaire_id"]) in miennes:
                continue
            v = nombre(y.get("honoraires_entree"))
            if v is None:
                ht = nombre(y.get("commission_agence"))
                v = None if ht is None else ht * 1.20
            if v is not None:
                vals.append(v)
        if not vals:
            cpt["vrai vide : aucune voisine ne porte de commission"] += 1
            a = annee_de_la_ligne(l)
            ans[a] += 1
            som[a] += cc or 0
        elif cc is not None and any(abs(cc - v) <= max(1.0, 0.01 * max(cc, v)) for v in vals):
            cpt["une VOISINE porte LA MEME -> le rapport se trompe"] += 1
        else:
            cpt["une voisine porte une commission DIFFERENTE"] += 1
    for k, v in sorted(cpt.items()):
        print("   %-56s %4d" % (k, v))
    print("   les vrais vides, par annee du classeur :")
    for a in sorted(ans, key=str):
        print("      %-6s %3d lignes . %10s EUR" % (a, ans[a], espaces(som[a])))
    print("      TOTAL  %3d lignes . %10s EUR" % (sum(ans.values()), espaces(sum(som.values()))))

    # --------------------------------- (3) LE ZERO DEGUISE
    print("\n=== (3) LE ZERO DEGUISE : des « ECART » ou NOTRE valeur vaut 0 ===")
    for champ in ("Commission TTC", "Prix"):
        z = [l for l in L if l["v_" + champ] == "ECART" and nombre(l["n_" + champ]) == 0]
        tot = sum(nombre(l["c_" + champ]) or 0 for l in z)
        print("   %-16s %3d lignes . le classeur y porte %10s EUR"
              % (champ, len(z), espaces(tot)))

    # --------------------------------- (4) AF LE PRIX, a COMPARER seulement
    print("\n=== (4) AF Prix -- decide « comparer » : on ne pose RIEN, on LISTE ===")
    c = collections.Counter(l["v_Prix"] for l in L)
    for k, v in c.most_common():
        print("   %-18s %4d" % (k, v))

    # --------------------------------- (5) W vs V : a quelle colonne colle date_acte
    print("\n=== (5) TEMOIN : notre `compromis.date_acte` colle a QUELLE colonne ? ===")
    c = collections.Counter()
    for l in L:
        dn = date_de_chez_nous(l["n_Vente Prevue"]) or date_du_classeur_tolerante(l["n_Vente Prevue"])
        if dn is None:
            continue
        dp = date_du_classeur_tolerante(l["c_Vente Prevue"])
        df = date_du_classeur_tolerante(l["c_Vente Fixee"])
        ep = abs((dp - dn).days) if dp else None
        ef = abs((df - dn).days) if df else None
        if ep is not None and ep <= 3 and (ef is None or ef > 3):
            c["V Vente Prevue"] += 1
        elif ef is not None and ef <= 3 and (ep is None or ep > 3):
            c["W Vente Fixee"] += 1
        elif ep is not None and ef is not None and ep <= 3 and ef <= 3:
            c["les deux"] += 1
        else:
            c["ni l une ni l autre"] += 1
    for k, v in sorted(c.items(), key=lambda t: -t[1]):
        print("   %-24s %4d" % (k, v))
    print("   ==> l appariement du rapport (date_acte = Vente Prevue) est le BON.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
