#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LES APPARIEMENTS QU'IL JUGE FAUX : L'AUDIT, LIGNE PAR LIGNE.     18/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\audit_appariements_suspects_2026-11-18.py

⛔ LECTURE SEULE. Le Sheet, la base locale (phase2.sqlite en mode ro) et MODELO.

⭐⭐⭐ SA DEMANDE DU 18/11 : « il y a 3 ou 4 appariements qui semblent faux que nous
  devons auditer ». Ses six « rien » de l'arbitrage, dont trois portent sa note.

LA METHODE, et elle ne se contente PAS de regarder l'ecart de date :
  ① LA LIGNE DU SHEET EN ENTIER -- toutes ses colonnes non vides. Un appariement
    se juge sur les NOMS, le MANDAT, le PRIX et la VILLE, pas sur une date.
  ② NOTRE CHAINE EN ENTIER -- toutes ses transactions, leurs etats, leurs dates
    VRAIES (la cascade, pas la colonne `date`), ses mandants et ses acquereurs.
  ③ ⭐⭐ LA PREUVE INTERNE : une AUTRE transaction de la chaine tombe-t-elle au
    jour pres sur une date du Sheet ? Si oui, LE DOSSIER EST LE BON et l'ecart
    est une faute de saisie. C'est une preuve, pas un avis.
  ④ ⭐⭐⭐ Y A-T-IL UN MEILLEUR CANDIDAT ? On cherche, parmi TOUTES nos chaines,
    celles qui partagent un NOM avec le vendeur ou l'acquereur du Sheet, et on
    regarde si l'une d'elles colle MIEUX sur les dates. Sans ca, dire « faux »
    n'avance a rien : il faut nommer le bon.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "monitoring"))
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import apparier_classeur as ap                                      # noqa: E402
#: ⭐ LECON 15 : chercher si le projet a DEJA tranche. Le classeur ecrit ses dates
#:   sur DEUX formes (« 05/12/2023 » et « 5 decembre23 »), et la fonction qui lit
#:   les deux existe depuis le 14/11 -- on l'importe, on ne la reecrit pas.
import rapport_gel_tous_les_champs as rg                            # noqa: E402

BASE = RACINE / "phase2" / "phase2.sqlite"
DOSSIER = RACINE / "notice" / "LIGNES_A_TRANCHER_2026-11-18.json"

#: ses six « rien », avec sa note quand il en a laisse une
SUSPECTS = {
    "1ESJE28Q": "2012 apps et le sheet 2024",
    "53ZS73KW": "pas le bon lien, les dates sont trop eloignees",
    "TR42PT5H": "pas la bonne, les dates sont differentes",
    "8Q3LHGZ4": "",
    "74IL9C8F": "",
    "QH6672TZ": "",
}


def une_date(t):
    """⛔⛔ LE DEFAUT QUI M'A FAIT ANNONCER « AUCUNE TRANSACTION NE COLLE » ALORS
    QUE LE COMPROMIS DE 74IL9C8F COLLAIT AU JOUR EXACT : `ap.jour()` rend du
    JJ/MM/AAAA, et je ne lisais que l'ISO. Les etages ③ et ④ rendaient donc ZERO
    PAR CONSTRUCTION -- un zero qui rassure a tort, la lecon deja payee.
    ➡ CETTE FONCTION LIT LES DEUX FORMES, d'ou qu'elles viennent."""
    t = str(t or "").strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2}).*", t)
    if m:
        try:
            return date(*(int(x) for x in m.groups()))
        except ValueError:
            return None
    m = re.fullmatch(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})", t)
    if m:
        j, mo, a = (int(x) for x in m.groups())
        a = a + 2000 if a < 100 else a
        try:
            return date(a, mo, j)
        except ValueError:
            return None
    return None


def date_du_sheet(v):
    """⛔⛔ LES DEUX FORMATS DU CLASSEUR, et c'est le SECOND defaut de ce script :
    ma premiere version passait par ap._date_fr, qui ne lit pas « 7 aout19 ».
    Resultat affiche : « dates du Sheet : aucune » sur QH6672TZ et TR42PT5H --
    donc un etage ③ muet sur deux des six cas, sans le dire."""
    return rg.date_du_classeur_tolerante(v) or une_date(v)


def date_vraie(t: dict) -> str:
    """⭐ la VRAIE date d'une offre vit dans propositions_json, pas dans `date`."""
    if str(t.get("kind") or "").lower() != "offre":
        return ap.jour(t.get("date"))
    props = ap.dates_des_propositions(t.get("propositions_json"))
    bons = sorted(x for x in props if x and not str(x).startswith("0000"))
    return bons[0] if bons else ap.jour(t.get("date"))


def main() -> int:
    d = {x["id"]: x for x in json.loads(DOSSIER.read_text(encoding="utf-8"))}
    manquants = [k for k in SUSPECTS if k not in d]
    if manquants:
        print("⛔ absents du dossier : %s" % " ".join(manquants))
        return 2

    # ─── ① LE SHEET, LIGNE ENTIERE ───────────────────────────────────────────
    #: ⚠ sans ca, la cle de service n'est pas dans l'environnement : le Sheet
    #:   repond KeyError et on croirait a une panne de lecture.
    ap.load_env_file(RACINE / ".env")
    entetes, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes]
    if len(lignes) < 3000:
        print("⛔ LECTURE DU SHEET RATEE -- %d lignes." % len(lignes))
        return 2
    i_id = entetes.index("ID Unique")
    du_sheet = {}
    for rang, l in lignes:
        iu = str(l[i_id] if i_id < len(l) else "").strip()
        if iu in SUSPECTS:
            du_sheet[iu] = (rang, {entetes[i]: re.sub(r"\s+", " ", str(l[i] or "")).strip()
                                   for i in range(min(len(entetes), len(l)))
                                   if entetes[i]})
    print("le Sheet : %d lignes lues, %d des %d suspects retrouves"
          % (len(lignes), len(du_sheet), len(SUSPECTS)))
    if len(du_sheet) != len(SUSPECTS):
        print("⛔ un suspect ne se retrouve pas au Sheet -- on s'arrete.")
        return 2

    # ─── ② NOS CHAINES ───────────────────────────────────────────────────────
    con = sqlite3.connect("file:%s?mode=ro" % BASE, uri=True, timeout=120)
    con.execute("PRAGMA busy_timeout=120000")
    con.row_factory = sqlite3.Row
    liens = {}
    for r in con.execute("SELECT id_unique, app_affaire_id, role FROM app_classeur_lien"):
        liens.setdefault(str(r["id_unique"]).strip(), []).append(
            (r["app_affaire_id"], r["role"]))
    vises = sorted({a for iu in SUSPECTS for a, _ in liens.get(iu, [])})
    print("le gel : %d liens pour les %d suspects" % (len(vises), len(SUSPECTS)))
    chaines_du_suspect = {}
    for iu in SUSPECTS:
        chs = set()
        for a, _ in liens.get(iu, []):
            for r in con.execute("SELECT app_chaine_id FROM app_affaire_ledger "
                                 " WHERE app_affaire_id = ?", (a,)):
                if r["app_chaine_id"]:
                    chs.add(r["app_chaine_id"])
        chaines_du_suspect[iu] = chs
    chaine_complete = {}
    for ch in sorted({c for v in chaines_du_suspect.values() for c in v}):
        chaine_complete[ch] = [dict(r) for r in con.execute(
            "SELECT app_affaire_id, kind, state, date, date_acte, montant, "
            "       numero_mandat, honoraires_entree, hektor_annonce_id, "
            "       propositions_json, mandants_json, acquereurs_json, acquereur_json "
            "  FROM app_affaire_ledger WHERE app_chaine_id = ? "
            " ORDER BY app_affaire_id", (ch,))]

    # ─── ④ TOUTES LES CHAINES, pour chercher un MEILLEUR candidat ────────────
    print("chargement de toutes les chaines pour la recherche de candidats...")
    toutes = ap.charger_affaires(con, {"prix", "dates", "propositions"})
    con.close()
    print("nos affaires : %d chaines" % len(toutes))
    print()

    for iu, note in sorted(SUSPECTS.items()):
        x, (rang, ligne) = d[iu], du_sheet[iu]
        geles = [a for a, _ in liens.get(iu, [])]
        print("=" * 78)
        print("⛔ %s -- %s . ligne %d du Sheet" % (iu, x["famille"], rang))
        if note:
            print("   ⭐ SA NOTE : %s" % note)
        print("   le desaccord : classeur %s . nous %s . ecart %s"
              % (x["classeur"], x["nous"], x["ecart"]))
        print()
        print("   ① LA LIGNE DU SHEET, en entier :")
        for k, v in ligne.items():
            if v and k != "ID Unique":
                print("      %-24s %s" % (k[:24], v[:84]))
        print()
        print("   ② NOTRE COTE -- le gel pointe %s"
              % (", ".join("%s (%s)" % (a, r) for a, r in liens.get(iu, [])) or "RIEN"))
        for ch in sorted(chaines_du_suspect[iu]):
            lot = chaine_complete.get(ch, [])
            print("      chaine %s -- %d transaction(s) :" % (ch, len(lot)))
            for t in lot:
                gelee = "  <= LE LIEN DU GEL" if t["app_affaire_id"] in geles else ""
                vraie, brute = date_vraie(t), ap.jour(t["date"])
                marque = ("  (`date` dit %s)" % brute) if brute != vraie else ""
                print("         %-8s %-10s %-10s %-11s%s%s"
                      % (t["app_affaire_id"], t["kind"], t["state"] or "", vraie,
                         marque, gelee))
                noms_m = ap.noms_du_blob(t["mandants_json"])
                noms_a = (ap.noms_du_blob(t["acquereurs_json"])
                          or ap.noms_du_blob(t["acquereur_json"]))
                if noms_m:
                    print("            vendeur(s)   %s" % str(noms_m)[:70])
                if noms_a:
                    print("            acquereur(s) %s" % str(noms_a)[:70])
                if t["numero_mandat"]:
                    print("            mandat %s . annonce %s . montant %s . hon. %s"
                          % (t["numero_mandat"], t["hektor_annonce_id"],
                             t["montant"], t["honoraires_entree"]))
        print()
        # ─── ③ LA PREUVE INTERNE ─────────────────────────────────────────────
        print("   ③ LA PREUVE INTERNE -- une AUTRE transaction colle-t-elle au jour pres ?")
        paires = [("offre", x.get("sheet_offre")),
                  ("compromis", x.get("sheet_compromis")),
                  ("vente", x.get("sheet_vente"))]
        trouve, comparaisons = False, 0
        for kind, au_sheet in paires:
            ds = date_du_sheet(au_sheet)
            if not ds:
                continue
            vu = False
            for ch in sorted(chaines_du_suspect[iu]):
                for t in chaine_complete.get(ch, []):
                    if str(t["kind"]).lower() != kind:
                        continue
                    dn = une_date(date_vraie(t))
                    if not dn:
                        continue
                    vu = True
                    comparaisons += 1
                    ec = abs((dn - ds).days)
                    if ec <= 3:
                        print("      ⭐⭐ %-9s le Sheet %s . nous %s -- %d jour(s) "
                              "=> LE DOSSIER EST LE BON"
                              % (kind, ds.isoformat(), dn.isoformat(), ec))
                        trouve = True
                    else:
                        print("      %-12s le Sheet %s . nous %s -- %d jours"
                              % (kind, ds.isoformat(), dn.isoformat(), ec))
            if not vu:
                print("      %-12s le Sheet %s . nous N'AVONS PAS cette transaction"
                      % (kind, ds.isoformat()))
        if not trouve:
            print("      ⛔ AUCUNE transaction ne colle -- rien ne confirme le dossier.")
        print()
        # ─── ④ UN MEILLEUR CANDIDAT ? ────────────────────────────────────────
        print("   ④ Y A-T-IL UN MEILLEUR CANDIDAT dans nos chaines ?")
        mots_v = {m for m in ap.mots_propres(ligne.get("Vendeur", ""),
                                             majuscules_seulement=False) if len(m) >= 4}
        mots_a = {m for m in ap.mots_propres(ligne.get("Acquereur", "")
                                             or ligne.get("Acquéreur", ""),
                                             majuscules_seulement=False) if len(m) >= 4}
        cibles = {u.isoformat() for _, v in paires for u in [date_du_sheet(v)] if u}
        print("      noms cherches : vendeur %s . acquereur %s"
              % (sorted(mots_v) or "-", sorted(mots_a) or "-"))
        print("      dates du Sheet : %s" % (" . ".join(sorted(cibles)) or "aucune"))
        cands = []
        for ch, e in toutes.items():
            nv = len(mots_v & e["mand"]) if mots_v else 0
            na = len(mots_a & e["acq"]) if mots_a else 0
            if not (nv or na):
                continue
            #: ⛔ LE MEME DEFAUT QU'EN ③ : les dates de la chaine sont en JJ/MM/AAAA
            #:   (ap.jour) et les cibles en ISO. On NORMALISE LES DEUX avant de
            #:   croiser, sinon l'intersection est vide par construction.
            siennes = {u.isoformat() for dd in e["dates"]
                       for u in [une_date(dd)] if u}
            colle = len(cibles & siennes)
            proche = 0
            for c in cibles:
                dc = une_date(c)
                for dd in siennes:
                    du = une_date(dd)
                    if dc and du and abs((du - dc).days) <= 7:
                        proche += 1
                        break
            cands.append((colle, proche, nv + na, ch, e))
        cands.sort(key=lambda t: (t[0], t[1], t[2], t[3]), reverse=True)
        if not cands:
            print("      ⛔ aucune chaine ne partage un nom -- pas de candidat.")
        for colle, proche, nn, ch, e in cands[:6]:
            dej = "  <= C'EST DEJA LE LIEN DU GEL" if ch in chaines_du_suspect[iu] else ""
            print("      chaine %-7s noms %d . dates EXACTES %d . a 7 jours %d%s"
                  % (ch, nn, colle, proche, dej))
            print("         mandats %s . dossier %s . annonce %s"
                  % (sorted(e["mandats"])[:3], e["dossier"], e["annonce"]))
            print("         ses dates : %s" % " . ".join(sorted(e["dates"])[:8]))
            print("         vendeurs  : %s" % str(sorted(e["mand"])[:6])[:72])
        print()
        if x.get("modelo"):
            print("   ⑤ MODELO (les mandats extraits) :")
            for m in x["modelo"][:2]:
                print("      mandat debut %s . fin %s . compromis %s . acte %s . etat %s"
                      % (m.get("debut"), m.get("fin"), m.get("compromis"),
                         m.get("acte"), m.get("etat")))
        print()
        #: ⭐⭐ LE GARDE-FOU DU TEMOIN POSITIF -- pose APRES m'etre fait prendre :
        #:   si l'etage ③ n'a rien pu comparer alors que le Sheet ET nous portons
        #:   des dates, ce n'est pas un verdict, c'est une panne de lecture.
        if cibles and not comparaisons:
            print("   ⛔⛔ AUCUNE COMPARAISON N'A PU ETRE FAITE alors que le Sheet "
                  "porte %d date(s) et que nos transactions en portent aussi." % len(cibles))
            print("      -> ce n'est PAS « aucune ne colle », c'est une lecture ratee.")
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
