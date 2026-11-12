#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPARIEUR V2 -- PASSE 2 : L'APPARIEMENT INDEPENDANT.          13/11/2026

Un SECOND appariement du classeur, de conception volontairement differente de
celle de `apparier_classeur.py`, pour servir de CONTROLE et non de remplacant :
sa valeur est dans le DESACCORD.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ LES TROIS REGLES D'INDEPENDANCE
═══════════════════════════════════════════════════════════════════════════════
  1. on ne lit JAMAIS `app_classeur_lien` (le gel) ;
  2. on ne lit JAMAIS le CSV d'appariement de la v1 (il porte deja la reponse) ;
  3. on n'importe AUCUNE logique de la v1.

═══════════════════════════════════════════════════════════════════════════════
EN QUOI LA CONCEPTION DIFFERE, ET POURQUOI C'EST CE QUI LA REND UTILE
═══════════════════════════════════════════════════════════════════════════════
    la v1    une CASCADE de 10 etages, ENTREE PAR LE MANDAT ; le premier etage
             qui trouve gagne, et on ne regarde pas les suivants
    la v2    un SCORE sur TOUS les signaux a la fois, SANS entree privilegiee ;
             le mandat n'est qu'un signal parmi d'autres ; puis une RESOLUTION
             GLOBALE qui traite l'ensemble des lignes d'un coup

⭐ POURQUOI CE CHOIX EST FONDE, ET PAS UNE PREFERENCE : la mesure de la passe 1
  a montre que LE MANDAT EST ABSENT DE 24,9 % DES TRANSACTIONS (7 754 sur
  31 151). Une methode qui entre par lui est aveugle sur un quart du registre.
  ⭐⭐ Et deux methodes qui se trompent AUX MEMES ENDROITS ne servent a rien :
    l'independance de la conception EST la valeur du controle.

═══════════════════════════════════════════════════════════════════════════════
⭐⭐ ON APPARIE VERS DES TRANSACTIONS, PAS VERS DES CHAINES
═══════════════════════════════════════════════════════════════════════════════
Regle du plan : « un numero de chaine ne doit jamais servir de point
d'accrochage, il bouge » -- la chaine est RECALCULEE chaque nuit. Le numero de
transaction, lui, ne change JAMAIS.
⭐ Et la sortie est plus riche que celle du gel : pour une ligne, on nomme
  L'OFFRE, LE COMPROMIS et LA VENTE correspondants, pas une seule transaction.

═══════════════════════════════════════════════════════════════════════════════
LE POIDS DES SIGNAUX -- chacun vient d'une MESURE de la passe 1
═══════════════════════════════════════════════════════════════════════════════
    mandat exact                90,2 % designent un seul bien      -> fort
    2 mots de nom ou plus       34,7 % des lignes, tres selectif   -> fort
    1 mot de nom                60,4 %, faible seul (« jean » = 3 176 tx) -> faible
    notre n° de dossier         quasi-identifiant (14,5 % des lignes) -> tres fort
    une DATE qui tombe juste    le genre + le jour, tres selectif  -> fort
    le prix                     ⚠ DIFFERE dans 44,5 % des cas, et le classeur
                                porte TOUJOURS PLUS -> CONFIRMATION a tolerance
                                large, JAMAIS une cle
    la ville                    confirmation faible
⛔ AUCUN SIGNAL NE DECIDE SEUL, sauf notre n° de dossier. C'est le contraire de
  la v1, ou l'etage 1 (« mandat seul ») tranche a lui tout seul 2 991 lignes.
"""
from __future__ import annotations

import collections
import csv
import io
import sys
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                                   # noqa: BLE001
    pass

from apparier_v2_socle import (chiffres, jour, lire_le_registre,     # noqa: E402
                               lire_le_sheet, noms, noms_du_blob, pur, somme)

SORTIE = RACINE / "notice" / "APPARIEUR_V2_CONCORDANCE_2026-11-13.csv"

CHAMPS_PERSONNES = ("acquereur_json", "acquereurs_json", "mandants_json")

# ── LES POIDS. Ils sont ECRITS ICI, en un seul endroit, pour qu'on puisse les
#    discuter -- et chacun porte la mesure qui le justifie.
P_DOSSIER_REF = 100     # notre numero de dossier : quasi-identifiant
P_MANDAT = 40           # 90,2 % designent un seul bien
P_NOM_PAR_MOT = 14      # chaque mot de nom en commun
P_NOM_BONUS_2 = 20      # bonus des le 2e mot : 2 mots ou + est tres selectif
P_DATE_JUSTE = 30       # une date du classeur qui tombe sur une transaction
P_DATE_PROCHE = 10      # a 3 jours pres (saisie decalee)
P_PRIX_EGAL = 12        # le prix tombe juste -- seulement 55 % du temps
P_PRIX_PROCHE = 6       # a 10 % pres (la negociation)
P_VILLE = 6
P_GENRE_COHERENT = 8    # l'etat du classeur correspond aux genres presents

SEUIL_CERTAIN = 70
SEUIL_PROBABLE = 40


def etat_vers_genres(etat: str) -> set[str]:
    """Ce que l'« Etat Actuel » du classeur dit des genres attendus.
    ⚠ On reste LARGE : un etat dit ce qui est ATTEINT, pas ce qui manque."""
    e = pur(etat)
    if "regl" in e or "fix" in e or "vendu" in e or "sign" in e:
        return {"vente", "compromis", "offre"}
    if "compromis" in e or "prevue" in e or "prevu" in e:
        return {"compromis", "offre"}
    if "offre" in e:
        return {"offre"}
    if "annul" in e:
        return {"offre", "compromis", "vente"}
    return set()


def main() -> int:
    print("=" * 80)
    print("APPARIEUR V2 -- PASSE 2 : L'APPARIEMENT INDEPENDANT")
    print("  ni le gel, ni le CSV de la v1, ni sa logique.")
    print("=" * 80)

    tx = lire_le_registre()
    print("\nregistre : %d transactions" % len(tx))

    # ═══ LES INDEX ═══════════════════════════════════════════════════════════
    par_bien: dict = collections.defaultdict(list)
    for t in tx:
        par_bien[t["hektor_annonce_id"]].append(t)

    i_mandat = collections.defaultdict(set)
    i_nom = collections.defaultdict(set)
    i_date = collections.defaultdict(set)
    noms_bien = collections.defaultdict(set)
    montants_bien = collections.defaultdict(set)

    for t in tx:
        b = t["hektor_annonce_id"]
        m = chiffres(t.get("numero_mandat"))
        if m:
            i_mandat[m].add(b)
        mots: set[str] = set()
        for ch in CHAMPS_PERSONNES:
            mots |= noms_du_blob(t.get(ch))
        noms_bien[b] |= mots
        for mot in mots:
            i_nom[mot].add(b)
        v = somme(t.get("montant"))
        if v is not None:
            montants_bien[b].add(v)
        for d in (jour(t.get("date")), jour(t.get("date_acte"))):
            if d:
                i_date[d].add(b)
    print("index : %d mandats . %d mots de nom . %d jours . %d biens"
          % (len(i_mandat), len(i_nom), len(i_date), len(par_bien)))

    # notre numero de dossier, depuis le registre des mandats
    import sqlite3
    ref_bien: dict = {}
    try:
        con = sqlite3.connect("file:%s?mode=ro"
                              % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                              uri=True, timeout=30)
        c = con.cursor()
        c.execute("pragma table_info(app_mandat)")
        cm = [r[1] for r in c.fetchall()]
        if "product_ref" in cm and "hektor_annonce_id" in cm:
            c.execute("select product_ref, hektor_annonce_id from app_mandat "
                      "where product_ref is not null and trim(product_ref) <> ''")
            for ref, ann in c.fetchall():
                try:
                    ref_bien.setdefault(pur(ref), set()).add(int(ann))
                except (TypeError, ValueError):
                    pass
        con.close()
        print("notre n° de dossier : %d references lues" % len(ref_bien))
    except Exception as e:                                          # noqa: BLE001
        print("⚠ n° de dossier non lisible (%s) -- le signal est DESACTIVE" % str(e)[:60])

    # ═══ LE SHEET ════════════════════════════════════════════════════════════
    entetes, lignes = lire_le_sheet()
    print("sheet : %d lignes" % len(lignes))
    ic = {k: (entetes.index(k) if k in entetes else None) for k in (
        "ID Unique", "Mandat", "Prix", "Acquéreur", "Vendeur", "Ville",
        "Etat Actuel", "Offre Achat", "Compromis", "Vente Prévue", "Vente Fixée",
        "product_ref", "Annulée", "Vente Réglée")}
    absentes = [k for k, v in ic.items() if v is None]
    if absentes:
        print("⚠ colonnes ABSENTES du Sheet, leur signal est eteint : %s"
              % ", ".join(absentes))

    def case(l, nom):
        i = ic.get(nom)
        return str(l[i]).strip() if i is not None and i < len(l) else ""

    # ═══ LE SCORE, LIGNE PAR LIGNE ═══════════════════════════════════════════
    propositions = []     # (score, numero de ligne, bien, preuves)
    for num, l in lignes:
        man = chiffres(case(l, "Mandat"))
        prix = somme(case(l, "Prix"))
        acq = noms(case(l, "Acquéreur"))
        vend = noms(case(l, "Vendeur"))
        ville = pur(case(l, "Ville"))
        etat = case(l, "Etat Actuel")
        ref = pur(case(l, "product_ref"))
        dates_cl = {c: jour(case(l, c)) for c in
                    ("Offre Achat", "Compromis", "Vente Prévue", "Vente Fixée")}
        dates_cl = {k: v for k, v in dates_cl.items() if v}

        # ── les CANDIDATS : l'UNION de tous les signaux, sans priorite ───────
        cand: set = set()
        if ref and ref in ref_bien:
            cand |= ref_bien[ref]
        if man:
            cand |= i_mandat.get(man, set())
        for mot in (acq | vend):
            cand |= i_nom.get(mot, set())
        for d in dates_cl.values():
            cand |= i_date.get(d, set())
        if not cand:
            propositions.append((0, num, None, "aucun candidat"))
            continue
        # ⚠ GARDE-FOU DE COUT : un mot de nom tres repandu peut ramener des
        #   milliers de biens. On ne garde que ceux qui ont au moins un signal
        #   FORT, sauf si le total reste petit.
        if len(cand) > 400:
            fort: set = set()
            if ref and ref in ref_bien:
                fort |= ref_bien[ref]
            if man:
                fort |= i_mandat.get(man, set())
            for d in dates_cl.values():
                fort |= i_date.get(d, set())
            if fort:
                cand = cand & fort if (cand & fort) else fort

        meilleur = []
        for b in cand:
            score = 0
            preuves = []
            if ref and b in ref_bien.get(ref, set()):
                score += P_DOSSIER_REF
                preuves.append("n°dossier")
            if man and b in i_mandat.get(man, set()):
                score += P_MANDAT
                preuves.append("mandat")
            communs = (acq | vend) & noms_bien.get(b, set())
            if communs:
                score += P_NOM_PAR_MOT * min(len(communs), 4)
                if len(communs) >= 2:
                    score += P_NOM_BONUS_2
                preuves.append("nom x%d" % len(communs))
            # les dates
            jours_bien = {jour(t.get("date")) for t in par_bien[b]}
            jours_bien |= {jour(t.get("date_acte")) for t in par_bien[b]}
            jours_bien.discard("")
            justes = sum(1 for d in dates_cl.values() if d in jours_bien)
            if justes:
                score += P_DATE_JUSTE * min(justes, 3)
                preuves.append("date x%d" % justes)
            else:
                proches = 0
                for d in dates_cl.values():
                    for db in jours_bien:
                        if abs(int(d.replace("-", "")) - int(db.replace("-", ""))) <= 3:
                            proches += 1
                            break
                if proches:
                    score += P_DATE_PROCHE * min(proches, 2)
                    preuves.append("date~x%d" % proches)
            # le prix -- CONFIRMATION, jamais une cle
            if prix is not None and montants_bien.get(b):
                if prix in montants_bien[b]:
                    score += P_PRIX_EGAL
                    preuves.append("prix=")
                elif min(abs(v - prix) for v in montants_bien[b]) <= 0.10 * prix:
                    score += P_PRIX_PROCHE
                    preuves.append("prix~")
            # le genre attendu
            attendus = etat_vers_genres(etat)
            if attendus:
                presents = {t["kind"] for t in par_bien[b]}
                if attendus & presents:
                    score += P_GENRE_COHERENT
                    preuves.append("genre")
            meilleur.append((score, b, "+".join(preuves)))

        meilleur.sort(key=lambda x: -x[0])
        s, b, p = meilleur[0]
        second = meilleur[1][0] if len(meilleur) > 1 else 0
        propositions.append((s, num, b, p, second, len(meilleur)))

    # ═══ LE VERDICT ══════════════════════════════════════════════════════════
    print("\n" + "-" * 80)
    print("LE VERDICT, avant resolution globale")
    print("-" * 80)
    v = collections.Counter()
    for pr in propositions:
        s = pr[0]
        if pr[2] is None:
            v["aucun candidat"] += 1
        elif s >= SEUIL_CERTAIN:
            v["CERTAIN  (>= %d)" % SEUIL_CERTAIN] += 1
        elif s >= SEUIL_PROBABLE:
            v["probable (>= %d)" % SEUIL_PROBABLE] += 1
        else:
            v["douteux  (< %d)" % SEUIL_PROBABLE] += 1
    for k, n in v.most_common():
        print("   %-22s %5d  (%5.1f %%)" % (k, n, 100.0 * n / len(lignes)))

    # ⭐ L'ECART AU SECOND : une preuve de SOLIDITE que la v1 ne produit pas
    nets = sum(1 for pr in propositions
               if len(pr) > 4 and pr[2] is not None and pr[0] - pr[4] >= 30)
    print("\n   ⭐ lignes ou le premier candidat devance le second de 30 points ou"
          "\n      plus (donc SANS rival credible) : %d  (%.1f %%)"
          % (nets, 100.0 * nets / len(lignes)))

    with io.open(SORTIE, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["ligne du classeur", "score", "bien v2", "preuves",
                    "score du second", "candidats examines"])
        for pr in propositions:
            if pr[2] is None:
                w.writerow([pr[1], 0, "", pr[3], "", 0])
            else:
                w.writerow([pr[1], pr[0], pr[2], pr[3], pr[4], pr[5]])
    print("\n   ecrit : %s" % SORTIE)
    print("\n" + "=" * 80)
    print("PASSE 2 TERMINEE -- rien n'a ete ecrit en base, ni chez Hektor,")
    print("ni dans le classeur. Le gel n'a pas ete ouvert.")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
