#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPARIEUR V2 -- PASSE 3 : L'ACCORD DE TROIS FAMILLES DISJOINTES. 13/11/2026

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ POURQUOI CE FICHIER EXISTE -- ET C'EST LE COEUR DE TOUT LE TRAVAIL
═══════════════════════════════════════════════════════════════════════════════
La passe 2 a rendu « 97,8 % CERTAIN ». ⛔ CE CHIFFRE NE VAUT RIEN : les seuils,
c'est moi qui les ai poses. **Un apparieur qui se note lui-meme se donne toujours
une bonne note.**

Frederic demande a etre « sur a 100 % ». La seule forme rigoureuse de cette
certitude, sans gel et sans la v1, est L'ACCORD DE METHODES INDEPENDANTES. On
apparie donc TROIS FOIS, avec trois familles de signaux **disjointes** :

    famille A -- LE MANDAT seul              (un numero administratif)
    famille B -- L'IDENTITE seule            (les noms des personnes)
    famille C -- LES DATES seules            (les evenements de l'affaire)

⭐⭐ CES TROIS FAMILLES NE PARTAGENT AUCUNE DONNEE. Un mandat recycle ne peut pas
  tromper B ni C ; un homonyme ne peut pas tromper A ni C ; une date mal saisie ne
  peut pas tromper A ni B. **Quand les trois nomment le MEME bien, ce n'est plus
  un score : c'est une triple coincidence, et il n'y a pas de cause commune.**

⭐ LE PRIX EST VOLONTAIREMENT EXCLU DES TROIS. Mesure de la passe 1 : il differe
  dans 44,5 % des cas, et toujours dans le meme sens (le classeur porte le prix de
  presentation, nous le prix traite). Un signal faux la moitie du temps ne peut
  pas servir de juge.

CE QUE LA SORTIE DIT, POUR CHAQUE LIGNE :
    3 familles d'accord   -> CERTAIN. Rien de plus a faire.
    2 d'accord, 1 muette  -> SOLIDE. Le signal manquant est absent, pas contraire.
    2 d'accord, 1 CONTRE  -> A REGARDER. Une famille dit autre chose.
    aucune majorite       -> A TRANCHER A LA MAIN.
⭐ C'est une liste FINIE, et c'est elle qui donne le 100 % : les certaines, plus
  celles que Frederic a tranchees.

LECTURE SEULE. Ni le gel, ni le CSV de la v1, ni sa logique.
"""
from __future__ import annotations

import collections
import csv
import io
import sqlite3
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

SORTIE = RACINE / "notice" / "APPARIEUR_V2_ACCORD_2026-11-13.csv"
CHAMPS_PERSONNES = ("acquereur_json", "acquereurs_json", "mandants_json")


def main() -> int:
    print("=" * 82)
    print("PASSE 3 -- L'ACCORD DE TROIS FAMILLES DISJOINTES")
    print("  A = le mandat seul . B = l'identite seule . C = les dates seules")
    print("  (le PRIX est exclu : faux dans 44,5 % des cas, mesure de la passe 1)")
    print("=" * 82)

    tx = lire_le_registre()
    par_bien = collections.defaultdict(list)
    for t in tx:
        par_bien[t["hektor_annonce_id"]].append(t)

    # ── les index, un par famille ───────────────────────────────────────────
    iA = collections.defaultdict(set)      # mandat -> biens
    iB = collections.defaultdict(set)      # mot de nom -> biens
    iC = collections.defaultdict(set)      # jour -> biens
    iCg = collections.defaultdict(set)     # (genre, jour) -> biens
    noms_bien = collections.defaultdict(set)
    jours_bien = collections.defaultdict(set)
    for t in tx:
        b = t["hektor_annonce_id"]
        m = chiffres(t.get("numero_mandat"))
        if m:
            iA[m].add(b)
        mots: set[str] = set()
        for ch in CHAMPS_PERSONNES:
            mots |= noms_du_blob(t.get(ch))
        noms_bien[b] |= mots
        for mot in mots:
            iB[mot].add(b)
        for d in (jour(t.get("date")), jour(t.get("date_acte"))):
            if d:
                iC[d].add(b)
                jours_bien[b].add(d)
                # ⭐ l index PAR GENRE : une date du classeur ne vaut que contre
                #   une transaction du MEME genre (correction du 13/11)
                iCg[(t["kind"], d)].add(b)

    # notre numero de dossier -- signal a part, utilise comme ARBITRE
    ref_bien: dict = {}
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                          uri=True, timeout=30)
    c = con.cursor()
    c.execute("""select mandat_numero_reference, hektor_annonce_id
                   from app_registre_mandats_current
                  where mandat_numero_reference is not null
                    and trim(mandat_numero_reference) <> ''""")
    for ref, ann in c.fetchall():
        try:
            ref_bien.setdefault(pur(ref), set()).add(int(ann))
        except (TypeError, ValueError):
            pass
    con.close()
    print("\nindex : A %d mandats . B %d mots . C %d jours . arbitre %d references"
          % (len(iA), len(iB), len(iC), len(ref_bien)))

    entetes, lignes = lire_le_sheet()
    ic = {k: (entetes.index(k) if k in entetes else None) for k in (
        "ID Unique", "Mandat", "Acquéreur", "Vendeur", "Etat Actuel",
        "Offre Achat", "Compromis", "Vente Prévue", "Vente Fixée", "product_ref")}

    def case(l, nom):
        i = ic.get(nom)
        return str(l[i]).strip() if i is not None and i < len(l) else ""

    # ── LES TROIS FAMILLES, CHACUNE SEULE ───────────────────────────────────
    def famille_A(l):
        """LE MANDAT. Rend un bien SEULEMENT s'il est sans ambiguite."""
        m = chiffres(case(l, "Mandat"))
        if not m:
            return None, "pas de mandat"
        s = iA.get(m, set())
        if len(s) == 1:
            return next(iter(s)), "mandat unique"
        if not s:
            return None, "mandat inconnu"
        return None, "mandat sur %d biens" % len(s)

    def famille_B(l):
        """L'IDENTITE. ⭐ On exige l'INTERSECTION des biens de CHAQUE mot, et au
        moins DEUX mots : un seul mot (« jean ») touche 3 176 transactions."""
        mots = noms(case(l, "Acquéreur")) | noms(case(l, "Vendeur"))
        if len(mots) < 2:
            return None, "moins de 2 mots de nom"
        # ⛔⛔ CORRIGE LE 13/11 APRES AVOIR REGARDE DES LIGNES REELLES.
        #   J exigeais l INTERSECTION des biens de CHAQUE mot. Un seul mot
        #   parasite du classeur (« Ind. », « Societe », « representee par son
        #   gerant ») suffisait a vider l intersection -> 1 160 lignes classees
        #   a tort « aucun bien porte ces noms », dont la ligne 10 qui avait
        #   CINQ noms en commun, TROIS dates justes, le mandat et le prix egal.
        #   ⭐ LA BONNE REGLE EST UN VOTE : on prend le bien qui partage LE PLUS
        #     de mots, et on exige un ECART NET avec le suivant.
        par_score = collections.Counter()
        for mot in mots:
            for b in iB.get(mot, ()):  
                par_score[b] += 1
        if not par_score:
            return None, "aucun bien porte ces noms"
        haut = par_score.most_common()
        if haut[0][1] < 2:
            return None, "un seul mot en commun au mieux"
        if len(haut) == 1:
            return haut[0][0], "identite, %d mots" % haut[0][1]
        if haut[0][1] > haut[1][1]:
            return haut[0][0], "identite, %d mots contre %d" % (haut[0][1], haut[1][1])
        exaequo = sum(1 for x in haut if x[1] == haut[0][1])
        return None, "identite : %d biens a egalite sur %d mots" % (exaequo, haut[0][1])

    def famille_C(l):
        """LES DATES. ⭐ On exige qu'AU MOINS DEUX dates du classeur tombent sur
        le MEME bien : une seule date est partagee par des centaines d'affaires."""
        # ⛔ CORRIGE LE 13/11 : je comparais les dates SANS LE GENRE, donc une
        #   « Vente Prevue » du classeur pouvait tomber sur une date de compromis.
        #   C est ce qui a fait voter cette famille pour un mauvais bien sur la
        #   ligne 973. ⭐ Chaque date du classeur ne vaut que contre SON genre.
        GENRE_DE = {"Offre Achat": "offre", "Compromis": "compromis",
                    "Vente Prévue": "vente", "Vente Fixée": "vente"}
        paires = {(GENRE_DE[k], jour(case(l, k))) for k in GENRE_DE}
        paires = {(g, d) for g, d in paires if d}
        ds = {d for _, d in paires}
        if len(ds) < 2:
            return None, "moins de 2 dates"
        compte = collections.Counter()
        for g, d in paires:
            for b in iCg.get((g, d), ()):
                compte[b] += 1
        if not compte:
            return None, "aucun bien a ces dates"
        haut = compte.most_common()
        if haut[0][1] < 2:
            return None, "aucun bien n'a 2 dates"
        if len(haut) > 1 and haut[0][1] == haut[1][1]:
            return None, "%d biens a egalite sur %d dates" % (
                sum(1 for x in haut if x[1] == haut[0][1]), haut[0][1])
        return haut[0][0], "dates x%d" % haut[0][1]

    # ── LE DEPOUILLEMENT ────────────────────────────────────────────────────
    verdict = collections.Counter()
    sortie = []
    for num, l in lignes:
        a, ra = famille_A(l)
        b, rb = famille_B(l)
        cc, rc = famille_C(l)
        ref = pur(case(l, "product_ref"))
        arb = next(iter(ref_bien[ref])) if (ref and len(ref_bien.get(ref, ())) == 1) else None

        votes = [x for x in (a, b, cc) if x is not None]
        muettes = 3 - len(votes)
        gagnant = None
        etiquette = ""
        if votes:
            compte = collections.Counter(votes)
            haut = compte.most_common()
            if len(haut) == 1:
                gagnant = haut[0][0]
                n = haut[0][1]
                if n == 3:
                    etiquette = "CERTAIN -- 3 familles d'accord"
                elif n == 2:
                    etiquette = "SOLIDE -- 2 d'accord, 1 muette"
                else:
                    etiquette = "FAIBLE -- 1 seule famille a parle"
            else:
                if haut[0][1] > haut[1][1]:
                    gagnant = haut[0][0]
                    etiquette = "A REGARDER -- %d contre %d" % (haut[0][1], haut[1][1])
                else:
                    etiquette = "A TRANCHER -- familles en desaccord"
        else:
            etiquette = "AUCUNE famille n'a pu parler"

        # ⭐ L'ARBITRE : notre numero de dossier, qui n'est dans aucune famille
        accord_arbitre = ""
        if arb is not None and gagnant is not None:
            accord_arbitre = "arbitre OK" if arb == gagnant else "⛔ ARBITRE CONTRE"
        elif arb is not None:
            accord_arbitre = "arbitre seul : %s" % arb

        verdict[etiquette] += 1
        if accord_arbitre:
            verdict["    (%s)" % accord_arbitre] += 1
        sortie.append([num, case(l, "ID Unique"), gagnant if gagnant else "",
                       etiquette, a or "", ra, b or "", rb, cc or "", rc,
                       arb or "", accord_arbitre, muettes])

    print("\n" + "-" * 82)
    print("LE VERDICT -- par ACCORD, pas par score")
    print("-" * 82)
    for k in ("CERTAIN -- 3 familles d'accord", "SOLIDE -- 2 d'accord, 1 muette",
              "FAIBLE -- 1 seule famille a parle", "A REGARDER -- 2 contre 1",
              "A TRANCHER -- familles en desaccord", "AUCUNE famille n'a pu parler"):
        for vk, n in verdict.items():
            if vk.startswith(k[:18]) and not vk.startswith("    "):
                print("   %-40s %5d  (%5.1f %%)" % (vk, n, 100.0 * n / len(lignes)))
    print()
    for vk, n in sorted(verdict.items()):
        if vk.startswith("    "):
            print("   %-40s %5d" % (vk.strip(), n))

    print("\n" + "-" * 82)
    print("POURQUOI CHAQUE FAMILLE SE TAIT -- c'est ca qui dit ou gagner du terrain")
    print("-" * 82)
    for i, nom in ((5, "A (mandat)"), (7, "B (identite)"), (9, "C (dates)")):
        muet = collections.Counter(r[i] for r in sortie if not r[i - 1])
        print("\n   %s :" % nom)
        for k, n in muet.most_common(5):
            print("      %-40s %5d" % (k, n))

    with io.open(SORTIE, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["ligne", "ID Unique", "bien retenu", "verdict",
                    "A bien", "A raison", "B bien", "B raison", "C bien", "C raison",
                    "arbitre (n° dossier)", "accord arbitre", "familles muettes"])
        w.writerows(sortie)
    print("\n   ecrit : %s" % SORTIE)
    print("\n" + "=" * 82)
    print("Rien n'a ete ecrit en base, ni chez Hektor, ni dans le classeur.")
    print("Le gel n'a pas ete ouvert une seule fois.")
    print("=" * 82)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
