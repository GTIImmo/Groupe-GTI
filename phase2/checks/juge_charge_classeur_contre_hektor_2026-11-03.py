#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""LE JUGE DE LA CHARGE DE COMMISSION -- etape 0 de la proposition A11 (03/11/2026).

DEMANDE DE FREDERIC : « clore le sujet de la charge de la commission sur le registre
des mandats et preparer le rattrapage par le sheet du registre des transactions ».

CE QU'IL FAIT. Pour chaque ligne du classeur rattachee par le gel (app_classeur_lien,
cle « ID Unique »), il pose TROIS temoins cote a cote :

    ① LE CLASSEUR    colonne Q « Charge Commission »   955 lignes, Vendeur / Acquereur
    ② NOUS           app_affaire_ledger.charge_commission_app   (vide a 100 % aujourd hui)
    ③ HEKTOR         les DEUX CASES du mandat, lues dans le TEXTE de
                     hektor_annonce_detail.raw_json, par l annonce de la transaction

⭐ POURQUOI CE RAPPORT EXISTE. Personne n a jamais compare le classeur a Hektor.
  Le script rapport_gel_tous_les_champs.py compare le classeur a NOTRE colonne --
  qui est vide -- donc il ne peut rien dire. C est la reserve ecrite dans A9 :
  « ce serait un TROISIEME temoin, et il arbitrerait le classeur ».

⛔ CE QU IL DECIDE. Si l accord classeur <-> Hektor est eleve, on remplit les ~25 800
  autres mandats depuis Hektor en confiance. S il est faible, on ne garde QUE les 955
  du classeur. Sans ce rapport, remplir 25 800 mandats serait un acte de foi -- et la
  mesure du 14/10 a montre qu une source plausible peut se tromper une fois sur deux.

⚠ LA MESURE DU 14/10 NE DIT RIEN CONTRE HEKTOR : « sur 25 lignes ou le classeur dit
  Acquereur, 13 sont rangees cote vendeur chez Hektor » deduisait la charge des
  MONTANTS entree/sortie. Or entree+sortie == honoraires sur 9 275 / 9 275 : ce sont
  deux MORCEAUX d une commission, pas deux payeurs. Ce desaccord condamne la methode
  de deduction par les montants, pas les deux cases du mandat.

⛔ AUCUNE ECRITURE : ni chez nous, ni chez Hektor, ni dans le classeur. Il produit un
  rapport dans notice/ et rien d autre. La base locale est ouverte en mode=ro.

⚠ A LANCER UNE SEULE FOIS : il lit la plage entiere du classeur par l API Sheets.

    .venv\\Scripts\\python.exe phase2\\checks\\juge_charge_classeur_contre_hektor_2026-11-03.py
"""
from __future__ import annotations

import io
import os
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "sync"))
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

from rapport_gel_tous_les_champs import (  # noqa: E402
    charger_classeur,
    client,
    lire_tout,
)

BASE_LOCALE = "file:%s?mode=ro" % (RACINE / "data" / "hektor.sqlite").as_posix()
SORTIE = RACINE / "notice" / "JUGE_CHARGE_CLASSEUR_HEKTOR_2026-11-03.md"

#: ⭐⭐ LES TEMOINS, MESURES LE 03/11 -- un par verdict, plus un temoin INVERSE.
#:   ⛔ Ma premiere version prenait 62774 (le bac a sable) parce que j avais sa
#:     capture en main. Le garde-fou a mordu, et il avait raison : 62774 n a
#:     AUCUNE des deux cases (raw_json de 13 027 octets, 0 et 0). Une capture du
#:     FORMULAIRE D OFFRE ne dit rien de la charge du mandat.
#:   ⭐ Lecon : un temoin se MESURE, il ne se recopie pas de memoire.
TEMOINS_POSITIFS = {
    "10000": "vendeur",      # case vendeur 6 650, case acquereur absente
    "10": "acquereur",       # case acquereur 3 500, case vendeur absente
}
#: ⭐ LE TEMOIN INVERSE : il ne doit PAS apparaitre. Sans lui, un code qui rend
#:   « vendeur » pour tout le monde passerait les temoins positifs.
TEMOIN_INVERSE = "62774"

RE_V = re.compile(r"Honoraires vendeur ou bailleur montant\s*:\s*([0-9]+(?:\.[0-9]+)?)", re.I)
RE_A = re.compile(r"Honoraires acqu\w*reur ou locataire\s*:\s*([0-9]+(?:\.[0-9]+)?)", re.I)


def sans_accent(v) -> str:
    s = unicodedata.normalize("NFD", str(v or ""))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def mot_de_charge(v) -> str:
    """Ramene TOUTES les ecritures a 'vendeur' | 'acquereur' | 'les_deux' | ''.

    ⚠ LES TROIS SOURCES N ECRIVENT PAS PAREIL, et c est mesure :
        le classeur -> « Vendeur » / « Acquereur »
        nous        -> « vendeur » / « acquereur » (la RPC traduit deja 'mandant')
        Hektor      -> « vendeur » TOUJOURS minuscule, « Acheteur » TOUJOURS
                       majuscule (casse rigide sur 81 925 lignes)
    ⛔ Donc un .lower()[:3] NE SUFFIT PAS : « Acheteur » donne 'ach' et
      « Acquereur » donne 'acq'. Il faut cette table, pas une troncature.
    """
    s = sans_accent(v).strip().lower()
    if not s:
        return ""
    if s in ("les_deux", "les deux"):
        return "les_deux"
    if s.startswith("vend") or s.startswith("mandant") or s.startswith("bailleur"):
        return "vendeur"
    if s.startswith("acqu") or s.startswith("achet") or s.startswith("locataire"):
        return "acquereur"
    return "?" + s[:18]


def charge_hektor_par_annonce() -> tuple[dict, dict]:
    """Les deux cases du mandat, par annonce. Rend (charge, montants).

    ⚠ ON PREND LA DERNIERE OCCURRENCE : les deux cases figurent DEUX FOIS dans
      16 823 annonces ; elles sont identiques 25 118 fois et divergent 51 fois
      (7 100 puis 6 000, toujours a la baisse). Reserve declaree dans A11 §1.10.
    ⛔ ON N APPELLE JAMAIS fetchall() : raw_json pese 775,4 Mo. On itere au curseur.
    """
    charge: dict[str, str] = {}
    montants: dict[str, tuple] = {}
    con = sqlite3.connect(BASE_LOCALE, uri=True)
    try:
        cur = con.cursor()
        for aid, raw in cur.execute(
                "select hektor_annonce_id, raw_json from hektor_annonce_detail"
                " where raw_json like '%onoraires vendeur ou bailleur montant%'"
                "    or raw_json like '%onoraires acqu%reur ou locataire%'"):
            vs = RE_V.findall(raw or "")
            as_ = RE_A.findall(raw or "")
            v = float(vs[-1]) if vs else 0.0
            a = float(as_[-1]) if as_ else 0.0
            if v > 0 and a > 0:
                mot = "les_deux"
            elif v > 0:
                mot = "vendeur"
            elif a > 0:
                mot = "acquereur"
            else:
                continue
            charge[str(aid)] = mot
            montants[str(aid)] = (v, a)
    finally:
        con.close()
    return charge, montants


def main() -> int:
    cl = client()                      # ⚠ d abord : il charge le .env que l API Sheets lit
    entetes, lignes = charger_classeur()
    idx = {n: i for i, n in enumerate(entetes)}

    def case(l, nom):
        i = idx.get(nom)
        return str(l[i]).strip() if i is not None and i < len(l) else ""

    if "Charge Commission" not in idx:
        raise SystemExit("ARRET : la colonne « Charge Commission » est absente du classeur")
    print("classeur : %d lignes, %d colonnes (Charge Commission en %d)"
          % (len(lignes), len(entetes), idx["Charge Commission"]))

    liens = lire_tout(cl, "app_classeur_lien",
                      "id_unique,app_affaire_id,role,confiance,preuves",
                      "id_unique.asc,app_affaire_id.asc")
    led = lire_tout(cl, "app_affaire_ledger",
                    "app_affaire_id,app_chaine_id,kind,numero_mandat,"
                    "charge_commission_app,hektor_annonce_id",
                    "app_affaire_id.asc")
    print("gel : %d liens · registre : %d transactions" % (len(liens), len(led)))

    hek, montants = charge_hektor_par_annonce()
    print("Hektor : %d annonces portent une charge dans les deux cases" % len(hek))

    # ⭐⭐ LES TEMOINS -- si l un tombe, la lecture est en panne et TOUT le rapport
    #    serait faux. Un zero ne se croit jamais sans temoin positif, et un temoin
    #    positif ne se croit pas sans son inverse.
    for aid, attendu in TEMOINS_POSITIFS.items():
        vu = hek.get(aid, "")
        if vu != attendu:
            raise SystemExit(
                "ARRET : temoin positif annonce %s -> attendu « %s », lu « %s »."
                " La lecture de raw_json est en panne, le rapport serait faux."
                % (aid, attendu, vu or "(rien)"))
        print("temoin positif : annonce %-7s -> « %-9s » %s  OK"
              % (aid, vu, montants[aid]))
    if TEMOIN_INVERSE in hek:
        raise SystemExit(
            "ARRET : temoin INVERSE annonce %s -> il rend « %s » alors qu il ne porte"
            " AUCUNE des deux cases. La lecture ramasse n importe quoi."
            % (TEMOIN_INVERSE, hek[TEMOIN_INVERSE]))
    print("temoin inverse : annonce %-7s -> absent, comme attendu     OK" % TEMOIN_INVERSE)

    tx = {str(x["app_affaire_id"]): x for x in led}
    par_id: dict[str, list[dict]] = defaultdict(list)
    for x in liens:
        par_id[str(x["id_unique"]).strip()].append(x)

    verdicts = Counter()
    accord = Counter()
    par_confiance = Counter()
    detail: list[dict] = []

    for l in lignes:
        q = mot_de_charge(case(l, "Charge Commission"))
        if not q:
            verdicts["classeur VIDE (colonne Q)"] += 1
            continue
        verdicts["classeur renseigne"] += 1

        iu = case(l, "ID Unique")
        ls = par_id.get(iu, [])
        if not ls:
            verdicts["  -> ligne NON RATTACHEE par le gel"] += 1
            continue
        parr: dict[str, dict] = {}
        conf = ""
        for x in ls:
            t = tx.get(str(x["app_affaire_id"]))
            if t:
                parr[str(x.get("role") or t.get("kind") or "")] = t
                conf = conf or str(x.get("confiance") or "")
        if not parr:
            verdicts["  -> rattachee mais transaction absente du registre"] += 1
            continue

        avancee = parr.get("vente") or parr.get("compromis") or parr.get("offre")
        annonce = str(avancee.get("hektor_annonce_id") or "")
        nous = mot_de_charge(avancee.get("charge_commission_app"))
        h = hek.get(annonce, "")

        if not annonce:
            verdicts["  -> transaction SANS id d annonce"] += 1
            continue
        if not h:
            verdicts["  -> HEKTOR MUET sur cette annonce"] += 1
            par_confiance["muet · %s" % (conf or "(sans)")] += 1
            detail.append({"id_unique": iu, "annonce": annonce,
                           "mandat": str(avancee.get("numero_mandat") or ""),
                           "classeur": q, "nous": nous or "(vide)", "hektor": "(muet)",
                           "verdict": "HEKTOR MUET", "confiance": conf,
                           "montants": ""})
            continue

        egal = (q == h)
        verdicts["  -> comparables"] += 1
        accord["%s : classeur %s / Hektor %s" % ("ACCORD" if egal else "DESACCORD", q, h)] += 1
        par_confiance["%s · %s" % ("accord" if egal else "DESACCORD", conf or "(sans)")] += 1
        if not egal:
            v, a = montants.get(annonce, (0.0, 0.0))
            detail.append({"id_unique": iu, "annonce": annonce,
                           "mandat": str(avancee.get("numero_mandat") or ""),
                           "classeur": q, "nous": nous or "(vide)", "hektor": h,
                           "verdict": "DESACCORD", "confiance": conf,
                           "montants": "vendeur=%.0f acquereur=%.0f" % (v, a)})

    comparables = verdicts.get("  -> comparables", 0)
    n_accord = sum(c for k, c in accord.items() if k.startswith("ACCORD"))
    taux = (100.0 * n_accord / comparables) if comparables else 0.0

    print()
    print("=" * 74)
    for k, c in verdicts.most_common():
        print("  %-48s %6d" % (k, c))
    print("=" * 74)
    print("  ACCORD : %d / %d comparables  =  %.1f %%" % (n_accord, comparables, taux))
    print("=" * 74)
    for k, c in sorted(accord.items(), key=lambda kv: -kv[1]):
        print("  %-50s %6d" % (k, c))

    ecrire_rapport(verdicts, accord, par_confiance, detail, comparables, n_accord, taux,
                   len(lignes), len(hek))
    print()
    print("rapport : %s" % SORTIE)
    print("FIN -- aucune ecriture en base, aucun appel Hektor, classeur en LECTURE seule")
    return 0


def ecrire_rapport(verdicts, accord, par_confiance, detail, comparables,
                   n_accord, taux, n_lignes, n_hek) -> None:
    o: list[str] = []
    o.append("# LE JUGE DE LA CHARGE : LE CLASSEUR CONTRE HEKTOR — 03/11/2026")
    o.append("")
    o.append("> Étape 0 de `notice/A11_CHARGE_COMMISSION_PROPOSITION_FINALE_2026-11-03.md`.")
    o.append("> ⛔ Lecture seule : aucune écriture en base, aucun appel à Hektor,")
    o.append("> le classeur lu par l'API Sheets sans y rien écrire.")
    o.append("")
    o.append("## LE VERDICT")
    o.append("")
    o.append("```")
    o.append("accord classeur <-> Hektor : %d / %d comparables  =  %.1f %%"
             % (n_accord, comparables, taux))
    o.append("```")
    o.append("")
    o.append("## LE CHEMIN DES LIGNES")
    o.append("")
    o.append("```")
    o.append("classeur lu : %d lignes" % n_lignes)
    o.append("Hektor      : %d annonces portent une charge" % n_hek)
    o.append("")
    for k, c in verdicts.most_common():
        o.append("%-50s %6d" % (k, c))
    o.append("```")
    o.append("")
    o.append("## LE DÉTAIL DE L'ACCORD")
    o.append("")
    o.append("```")
    for k, c in sorted(accord.items(), key=lambda kv: -kv[1]):
        o.append("%-52s %6d" % (k, c))
    o.append("```")
    o.append("")
    o.append("## PAR NIVEAU DE CONFIANCE DU LIEN GELÉ")
    o.append("")
    o.append("```")
    for k, c in sorted(par_confiance.items(), key=lambda kv: -kv[1]):
        o.append("%-40s %6d" % (k, c))
    o.append("```")
    o.append("")
    o.append("## ⭐ LA LISTE NOMMÉE — désaccords et silences")
    o.append("")
    o.append("⚠ *Un contrôle qui agrège perd ce qui sert à agir* : chaque ligne est nommée.")
    o.append("")
    o.append("```")
    o.append("%-14s %-9s %-8s %-10s %-10s %-10s %-12s %s"
             % ("ID Unique", "annonce", "mandat", "classeur", "nous", "Hektor",
                "confiance", "montants Hektor"))
    for d in detail[:400]:
        o.append("%-14s %-9s %-8s %-10s %-10s %-10s %-12s %s"
                 % (d["id_unique"][:14], d["annonce"], d["mandat"][:8],
                    d["classeur"][:10], d["nous"][:10], d["hektor"][:10],
                    d["confiance"][:12], d["montants"]))
    if len(detail) > 400:
        o.append("... et %d autres lignes" % (len(detail) - 400))
    o.append("```")
    o.append("")
    o.append("## CE QUE ÇA DÉCIDE")
    o.append("")
    o.append("- **accord élevé** → on remplit les ~25 800 autres mandats depuis Hektor,")
    o.append("  en repli derrière le classeur et derrière la saisie (A11 étapes ① à ③).")
    o.append("- **accord faible** → on ne garde QUE les 955 du classeur, et Hektor ne sert")
    o.append("  qu'à **afficher avec sa provenance**, jamais comme valeur de référence.")
    o.append("")
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    io.open(SORTIE, "w", encoding="utf-8", newline="\n").write("\n".join(o) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
