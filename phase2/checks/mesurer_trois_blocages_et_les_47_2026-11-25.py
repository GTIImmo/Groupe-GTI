#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""SES TROIS PETITS BLOCAGES ET LA METHODE DES 47 (son mot du 25/11, soir) -- LECTURE SEULE, ⛔ RIEN N'EST ECRIT.

    python -X utf8 -u phase2\checks\mesurer_trois_blocages_et_les_47_2026-11-25.py

① ses doubles (VIALLARD 3308P0UX/YRUF0S9H, PAOLONE T2GZOY5O/O6R10ZQA) et PEE1XTR8/9B7U8221 : ce qui distingue les deux
  lignes de chaque paire, pour UNE regle ; et ses jumeaux (toute autre paire qu'elle prendrait).
② HUY49KEC et le motif COPIE_SEULE : la vraie vente de la chaine de la copie concorde-t-elle avec la ligne ? par quels
  champs -- ceux de HEKTOR, ou ceux que nous avons recopies de son Sheet (circulaires) ? combien de lignes debloquees ?
③ 9Q0FHAKK : ce que Hektor sait de la vente (le miroir local de la nuit : la piece, son payload, l'annonce, les contacts).
④ les 47 (+2) : l'etat d'aujourd'hui de chaque case cible, et les parts des chaines (une vente reglee sans part fait crier
  le moniteur).
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402

PAIRES = [("3308P0UX", "YRUF0S9H"), ("T2GZOY5O", "O6R10ZQA"), ("PEE1XTR8", "9B7U8221")]
COLS = ["Mandat", "Etat Actuel", "Offre Achat", "Compromis", "Annulée", "Vente Prévue", "Vente Fixée", "Signée",
        "Vente Réglée", "Numéro de facture", "Prix", "Commission TTC", "Acquéreur", "Négociateur 1", "Agence"]


def noms(t) -> set:
    return {x for x in re.findall(r"[A-ZÀ-Ü][A-ZÀ-Ü'\-]{2,}", str(t or "").upper()) if x not in {"NAN", "MME", "MR", "ET"}}


def main() -> int:
    con = sqlite3.connect("file:%s?mode=ro" % (P.DOSSIER / "socle.sqlite").as_posix(), uri=True)
    V = {i: {"v": v, "e": e or "", "ps": json.loads(ps) if ps else [], "pr": json.loads(pr) if pr else [], "m": m or "",
             "mt": mt or ""} for i, v, e, ps, pr, m, mt in con.execute(
        "select id_unique, verdict, etiquette, pieces, preuves, motif, motif_texte from verdict where passage=81")}
    con.close()
    cn, cu = P.pooler()
    cu.execute("select app_affaire_id, kind, state, date::text, app_chaine_id, app_dossier_uuid::text, app_dossier_numero, "
               "transaction_origine, hektor_affaire_id, coalesce(date_annulation_app,''), coalesce(vente_reglee_app,''), "
               "coalesce(numero_facture_app,''), numero_mandat, acquereurs_json::text, acquereur_json::text, "
               "honoraires_entree, montant, hektor_annonce_id, propositions_json::text from public.app_affaire_ledger")
    R = {}
    for r in cu.fetchall():
        R[int(r[0])] = dict(zip(["a", "genre", "etat", "date", "chaine", "uuid", "numero", "origine", "hk", "annul",
                                 "reglee", "facture", "mandat", "acqs", "acq", "hon", "montant", "annonce", "props"], r))
    cu.execute("select id_unique, app_affaire_id from public.app_classeur_lien")
    gel = defaultdict(set)
    for i, a in cu.fetchall():
        gel[i].add(int(a))
    cu.execute("select app_chaine_id, cote, nom_au_moment, pourcentage, origine from public.app_affaire_repartition")
    parts = defaultdict(list)
    for ch, cote, nom, pc, o in cu.fetchall():
        parts[ch].append((cote, nom, float(pc), o))
    cn.rollback()
    cn.close()
    img = json.loads((P.IMAGES / "2026-11-25_072625" / "sheet.json").read_text(encoding="utf-8"))
    ent = img["entete"]

    def case(i, c):
        return img["par_id"][i][0]["row"][ent.index(c)].strip()

    def copie(a):
        return PC.est_copie(a, R[a]["origine"], R[a]["hk"])

    def acq_hektor(a):
        return noms(" ".join([str(R[a]["acqs"] or ""), str(R[a]["acq"] or "")]))

    # ── ① LES DOUBLES ──
    print("① SES DOUBLES ET PEE1XTR8 -- ce qui distingue les deux lignes de chaque paire")
    for x, y in PAIRES:
        print("-" * 100)
        for i in (x, y):
            v = V[i]
            print("  %s (ligne %s) : %s" % (i, img["par_id"][i][0]["num"], " ; ".join("%s=%r" % (c, case(i, c)[:28])
                                                                                     for c in COLS)))
            print("     protocole 81 : %s %s ; pieces %s ; %s" % (v["v"], v["m"], v["ps"], (v["mt"] or "")[:160]))
            print("     preuves : %s" % " || ".join(str(p)[:110] for p in v["pr"]))
            print("     gel : %s" % sorted(gel.get(i, set())))
        ps = sorted(set(V[x]["ps"]) | set(V[y]["ps"]) | gel.get(x, set()) | gel.get(y, set()))
        print("     le dossier (pieces des deux lignes, protocole et gel) :")
        for a in ps:
            if a in R:
                r = R[a]
                print("       %-7s %-9s %-9s date %-10s %-11s chaine %-6s annul_app %-10r reglee %-12r facture %-14r "
                      "mandat %-6s acquereur %s %s" % (a, r["genre"], r["etat"], (r["date"] or "")[:10], r["numero"],
                                                       r["chaine"], r["annul"], r["reglee"][:12], r["facture"][:14],
                                                       r["mandat"], sorted(acq_hektor(a))[:3], "COPIE" if copie(a) else ""))
        meme = {c: case(x, c) == case(y, c) for c in ("Mandat", "Acquéreur", "Commission TTC", "Prix", "Offre Achat",
                                                       "Compromis", "Annulée", "Etat Actuel")}
        print("     MEMES COLONNES : %s" % meme)

    # ses jumeaux : toute paire de lignes TRANCHEES sur un meme dossier, ou en ATTENTE DEUX_LIGNES_UN_DOSSIER
    par_u = defaultdict(set)
    for i, v in V.items():
        if v["v"] == "TRANCHEE":
            k = [a for a in v["ps"] if a in R]
            hk = [a for a in k if not copie(a)] or k
            for u in {R[a]["uuid"] for a in hk}:
                par_u[u].add(i)
    partagees = {u: s for u, s in par_u.items() if len(s) > 1}
    deux = sorted(i for i, v in V.items() if v["m"] == "DEUX_LIGNES_UN_DOSSIER")
    print("  JUMEAUX : dossiers portes par 2+ lignes TRANCHEES : %s ; lignes en ATTENTE DEUX_LIGNES_UN_DOSSIER : %s" % (
        {R[next(a for a in R if R[a]["uuid"] == u)]["numero"]: sorted(s) for u, s in partagees.items()}, deux))

    # ── ② COPIE_SEULE ──
    print("\n② LE MOTIF COPIE_SEULE")
    for i in sorted(i for i, v in V.items() if v["m"] == "COPIE_SEULE"):
        cop = [a for a in gel.get(i, set()) if a in R and copie(a)]
        chaines = {R[a]["chaine"] for a in cop}
        vraies = sorted(a for a, r in R.items() if r["chaine"] in chaines and not copie(a))
        ventes = [a for a in vraies if R[a]["genre"] == "vente"]
        print("  %s (ligne %s) : %s ; copies %s -> chaines %s ; vraies pieces de la chaine %s" % (
            i, img["par_id"][i][0]["num"], " ; ".join("%s=%r" % (c, case(i, c)[:24]) for c in
                                                      ("Etat Actuel", "Mandat", "Acquéreur", "Vente Fixée", "Signée",
                                                       "Vente Réglée", "Numéro de facture", "Commission TTC")),
            cop, sorted(chaines), vraies))
        for a in ventes:
            r = R[a]
            m_ok = str(r["mandat"] or "").strip() == case(i, "Mandat")
            a_ok = bool(acq_hektor(a) & noms(case(i, "Acquéreur")))
            h_ok = r["hon"] is not None and case(i, "Commission TTC") and abs(float(r["hon"]) - float(
                re.sub(r"[^\d.]", "", case(i, "Commission TTC").replace(",", ".")) or 0)) < 1
            f_ok = bool(r["facture"]) and r["facture"].split()[0] == case(i, "Numéro de facture").split()[0] \
                if case(i, "Numéro de facture") else False
            print("     vente %s (Hektor) : date %s mandat %s acquereur %s honoraires %s | (recopie du Sheet le 16/11 : "
                  "reglee %r facture %r) -> mandat %s, acquereur %s, honoraires %s ; facture %s (circulaire)" % (
                      a, (r["date"] or "")[:10], r["mandat"], sorted(acq_hektor(a))[:3], r["hon"], r["reglee"],
                      r["facture"][:20], m_ok, a_ok, h_ok, f_ok))
        if not ventes:
            print("     pas de vraie vente dans la chaine de sa copie")

    # ── ③ 9Q0FHAKK ──
    print("\n③ 9Q0FHAKK -- ce que Hektor sait (le miroir local de la nuit)")
    loc = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(), uri=True)
    for a in (3650, 3647, 3648, 3646, 3649):
        pj, fs, ls, pres = loc.execute("select payload_json, first_seen_at, last_seen_at, present_in_hektor from "
                                       "app_affaire_ledger where app_affaire_id=?", (a,)).fetchone()
        p = json.loads(pj) if pj else {}
        garde = {k: p.get(k) for k in ("date", "dateStart", "dateEnd", "dateSignatureActe", "status", "prix", "honoraires",
                                       "honorairesEntree", "mandat", "retro_nom", "retro_honoraires", "retro_qualite",
                                       "note") if k in p}
        print("  piece %s (%s) : vue la 1re fois %s, la derniere %s, presente chez Hektor %s" % (a, R[a]["genre"], fs, ls, pres))
        print("     acquereurs : %s" % [(x.get("id"), x.get("nom"), x.get("prenom")) for x in (p.get("acquereurs") or [])
                                        if isinstance(x, dict)] if isinstance(p.get("acquereurs"), list) else
              "     acquereurs : %s" % str(p.get("acquereurs"))[:160])
        print("     mandants : %s" % str(p.get("mandants"))[:160])
        print("     %s" % {k: (str(v)[:60] if v is not None else None) for k, v in garde.items()})
    for t in ("app_historical_annonce_index_current", "app_archive_annonce_index_current"):
        cols = [r[1] for r in loc.execute("pragma table_info(%s)" % t)]
        k = "hektor_annonce_id" if "hektor_annonce_id" in cols else ("annonce_id" if "annonce_id" in cols else cols[0])
        rows = loc.execute("select * from %s where cast(%s as text)='8395'" % (t, k)).fetchall()
        for r in rows:
            d = dict(zip(cols, r))
            print("  annonce 8395 dans %s : %s" % (t, {c: d[c] for c in cols if c in ("date_maj", "source_updated_at",
                                                                                     "local_detail_updated_at", "statut",
                                                                                     "numero_mandat", "ville", "titre",
                                                                                     "numero_dossier") and c in d}))
    ann = loc.execute("select numero_mandat, numero_dossier, ville, statut_annonce, mandants_texte, adresse_detail, "
                      "code_postal from app_annonces_current where hektor_annonce_id=8395").fetchone()
    print("  annonce 8395 (app_annonces_current) : %s" % (ann,))
    for nom in ("POTTIER", "SOUCHON"):
        for r in loc.execute("select hektor_contact_id, civilite, prenom, nom, date_maj, hektor_couple_contact_id, "
                             "couple_role, ville from app_contact_current where upper(nom) like ?", ("%" + nom + "%",)):
            print("  contact %s : %s" % (nom, r))
    for r in loc.execute("select hektor_contact_id, hektor_annonce_id, numero_mandat, role_contact, transaction_type, "
                         "transaction_id, transaction_state, transaction_date from app_contact_relation_current where "
                         "hektor_contact_id in ('28441', '28776') or hektor_annonce_id='8395'"):
        print("  relation : %s" % (r,))
    pot = sorted((a, R[a]["genre"], R[a]["annonce"], R[a]["etat"]) for a in R
                 if "POTTIER" in acq_hektor(a))
    print("  toutes les pieces du registre au nom de POTTIER : %s" % pot)
    fac = sorted((R[a]["facture"][:14], a, R[a]["genre"]) for a in R if R[a]["facture"].startswith("GGTI0000384"))
    print("  factures GGTI0000384x au registre (recopiees du Sheet) : %s" % fac)
    loc.close()

    # ── ④ LES 47 (+2) : l'etat d'aujourd'hui ──
    print("\n④ LES 47 (+2) -- l'etat d'aujourd'hui des cases cibles, et les parts de leurs chaines")
    f47 = RACINE / "notice" / "CLASSEUR_LES_47_VALEURS_JAMAIS_POSEES_2026-11-25.csv"
    with f47.open(encoding="utf-8") as h:
        L = list(csv.DictReader(h, delimiter=";"))
    vides, sans_part, hk_seul = 0, [], []
    for x in L:
        a = int(x["piece"])
        r = R[a]
        if x["quoi"] == "VENTE_REGLEE":
            vides += 1 if not r["reglee"] and not r["facture"] else 0
            p = parts.get(r["chaine"], [])
            if not p:
                sans_part.append(x["id_unique"])
            elif all(o.startswith("hektor") for *_z, o in p):
                hk_seul.append(x["id_unique"])
        else:
            vides += 1 if not r["annul"] else 0
    print("  %d valeurs ; cases cibles encore VIDES aujourd'hui : %d" % (len(L), vides))
    print("  ventes reglees dont la chaine n'a AUCUNE part : %d %s ; seulement des parts hektor%% (supposition) : %d %s" % (
        len(sans_part), sans_part, len(hk_seul), hk_seul))
    return 0


if __name__ == "__main__":
    sys.exit(main())
