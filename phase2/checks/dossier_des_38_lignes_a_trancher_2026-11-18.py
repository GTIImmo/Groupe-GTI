#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE DOSSIER DES LIGNES A TRANCHER : LES TROIS SOURCES EN FACE.   18/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\dossier_des_38_lignes_a_trancher_2026-11-18.py

⛔ LECTURE SEULE. Il produit un JSON pour l'ecran interactif, rien d'autre.

⭐⭐⭐ SA DEMANDE : « fais sur chacune de ces lignes une recherche sur sheet, apps et
  classeur modelo pour tenter de comprendre toi-meme et me faire une recommandation ».

LES TROIS SOURCES, ET CE QUE CHACUNE SAIT :
   ① LE SHEET        le classeur Google, 4 794 lignes -- ce que l'agence a ecrit
   ② L'APP           notre registre : la transaction, son etat, ses montants
   ③ MODELO          mandats_extraits.xlsx (35 Mo) -- l'export des mandats depuis
                     Netty/Hektor, avec date_start, date_end, date_of_sales_agreement,
                     date_of_deed, state. C'EST LA TROISIEME VOIX : quand le Sheet et
                     l'app se contredisent, c'est elle qui tranche.

LES LIGNES RETENUES :
   . les ecarts de DATE D'OFFRE a 366 jours pile ou plus d'un an (les fautes de
     saisie d'annee que le plan annonce depuis le 14/11)
   . les ecarts de COMMISSION TTC dits « autre rapport » -- ceux que ni le trou
     (nous = 0), ni la part d'entree (x0,50), ni l'arrondi n'expliquent
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "monitoring"))
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import apparier_classeur as ap                                      # noqa: E402
import check_gti_health as cgh                                      # noqa: E402

ECARTS = RACINE / "notice" / "A4_RAPPORT_GEL_ECARTS_SEULS_2026-11-17.csv"
MODELO = RACINE / "mandats_extraits.xlsx"
SORTIE = RACINE / "notice" / "LIGNES_A_TRANCHER_2026-11-18.json"
LOT_API = 60


def nb(v):
    t = re.sub(r"[^0-9.,-]", "", str(v or "")).replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def une_date(v):
    t = str(v or "").strip()
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


def date_vraie(t):
    """LA VRAIE DATE D'UNE OFFRE, et ce n'est PAS la colonne `date`.

    ⛔⛔ LA FAUTE QUE FREDERIC A TROUVEE LE 18/11 : « la date de l'offre d'achat
      du 61OW86CS est erronee, c'est la date de notre script de masse. Normalement
      on avait corrige la date !! ». Il avait raison deux fois.
      ① la colonne `date` d'une offre refusee porte L'HORODATAGE DE NOTRE GESTE
        du 11-12/11 (1 206 offres, 1 140 en deux heures) -- c'est une decision
        assumee du 12/11 : « la colonne ne se corrige PAS ».
      ② LA CORRECTION EXISTE, et elle est en service depuis le 12/11 : les ecrans
        lisent la vraie date dans `propositions_json`. MON script, lui, lisait la
        colonne brute -- donc mon dossier affichait la date du script.
    ⭐ LA VRAIE DATE est la premiere entree de type « proposition » :
        [{"date":"2021-02-27","type":"proposition"}, {"type":"accepte"},
         {"date":"2026-11-11 18:50:50","type":"refus"}]   <- notre geste
    ⭐ Et elle y est pour LES 1 206 : aucune date n'est perdue.
    """
    brut = str(t.get("date") or "")[:10]
    blob = t.get("propositions_json")
    if not blob:
        return brut, brut, ""
    try:
        items = blob if isinstance(blob, list) else json.loads(blob)
    except (ValueError, TypeError):
        return brut, brut, ""
    props = [str(x.get("date") or "")[:10] for x in items
             if isinstance(x, dict) and str(x.get("type") or "") == "proposition"]
    props = [d for d in props if d and not d.startswith("0000")]
    if not props:
        return brut, brut, ""
    vraie = min(props)
    if vraie == brut:
        return brut, brut, ""
    return vraie, brut, ("la colonne `date` dit %s -- c'est NOTRE GESTE du 11-12/11 ; "
                         "la vraie date de la proposition est %s" % (brut, vraie))


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


def charger_modelo():
    """MODELO : l'export des mandats. On n'en garde que ce qui sert ici."""
    try:
        from openpyxl import load_workbook
    except ImportError:
        print("⚠ openpyxl absent -- MODELO ne sera pas consulte.")
        return {}
    if not MODELO.exists():
        print("⚠ %s absent -- MODELO ne sera pas consulte." % MODELO.name)
        return {}
    wb = load_workbook(MODELO, read_only=True)
    ws = wb.worksheets[0]
    it = ws.iter_rows(values_only=True)
    tete = list(next(it))
    garde = ["mandate_number", "linked_product_ref", "date_start", "date_end",
             "date_of_sales_agreement", "date_of_deed", "state", "deleted",
             "contact_full_name", "product_recap", "mandate_type"]
    idx = {k: tete.index(k) for k in garde if k in tete}
    par_num = {}
    n = 0
    for r in it:
        d = {k: r[i] for k, i in idx.items()}
        num = str(d.get("mandate_number") or "").strip()
        if not num:
            continue
        n += 1
        par_num.setdefault(num, []).append(d)
    wb.close()
    print("MODELO : %d mandats lus, %d numeros distincts" % (n, len(par_num)))
    return par_num


def iso(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()[:10]
    return str(v or "")[:10]


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== LE DOSSIER DES LIGNES A TRANCHER (lecture seule) ===")
    print()
    with ECARTS.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    print("le rapport du gel : %d lignes d'ecart" % len(rows))

    # ─── LE CHOIX DES LIGNES ─────────────────────────────────────────────────
    a_trancher = []
    for r in rows:
        iu = r["ID Unique"]
        # ① les dates d'offre a un an ou plus
        if "ECART" in str(r.get("v_Offre Achat", "")).upper():
            a, b = une_date(r.get("c_Offre Achat")), une_date(r.get("n_Offre Achat"))
            if a and b:
                d = abs((a - b).days)
                if d > 365:
                    a_trancher.append({"id_unique": iu, "famille": "date d offre",
                                       "ecart": "%d jours" % d, "ecart_num": d,
                                       "classeur": a.isoformat(), "nous": b.isoformat()})
        # ② les commissions « autre rapport »
        if "ECART" in str(r.get("v_Commission TTC", "")).upper():
            a, b = nb(r.get("c_Commission TTC")), nb(r.get("n_Commission TTC"))
            if a is None or b is None:
                continue
            if not b or not a:
                continue                       # le trou / l'annulee : explique
            rap = a / b
            if abs(rap - 0.5) < 0.02 or abs(rap - 1) < 0.05:
                continue                       # part d'entree / arrondi : explique
            a_trancher.append({"id_unique": iu, "famille": "commission",
                               "ecart": "%.0f EUR (x%.2f)" % (abs(a - b), rap),
                               "ecart_num": abs(a - b),
                               "classeur": "%.0f" % a, "nous": "%.0f" % b})
    print("lignes retenues : %d" % len(a_trancher))
    par_fam = {}
    for x in a_trancher:
        par_fam[x["famille"]] = par_fam.get(x["famille"], 0) + 1
    for k, v in par_fam.items():
        print("   %-16s %3d" % (k, v))
    if not a_trancher:
        print("⛔ aucune ligne retenue -- le tri est suspect.")
        return 2
    print()

    # ─── ① LE SHEET ──────────────────────────────────────────────────────────
    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE DU SHEET RATEE.")
        return 2
    i_id = entetes.index("ID Unique")
    du_sheet = {}
    for rang, l in lignes:
        iu = str(l[i_id] if i_id < len(l) else "").strip()
        if iu:
            du_sheet[iu] = (rang, {entetes[i]: re.sub(r"\s+", " ", str(l[i] or "")).strip()
                                   for i in range(min(len(entetes), len(l)))
                                   if entetes[i]})
    print("le Sheet : %d lignes" % len(du_sheet))

    # ─── ② L'APP ─────────────────────────────────────────────────────────────
    cl = client()
    liens = []
    pas, dep = 1000, 0
    while True:
        lot = cl.get("app_classeur_lien", {"select": "id_unique,app_affaire_id,role",
                                           "order": "ligne_classeur",
                                           "limit": pas, "offset": dep}) or []
        liens.extend(lot)
        if len(lot) < pas:
            break
        dep += pas
    par_iu = {}
    for r in liens:
        par_iu.setdefault(str(r["id_unique"]).strip(), []).append(r["app_affaire_id"])
    vises = sorted({a for x in a_trancher for a in par_iu.get(x["id_unique"], [])})
    ledger = {}
    for i in range(0, len(vises), LOT_API):
        lot = vises[i:i + LOT_API]
        for r in (cl.get("app_affaire_ledger",
                         {"select": "app_affaire_id,kind,state,date,date_acte,montant,"
                                    "numero_mandat,honoraires_entree,honoraires_sortie,"
                                    "commission_agence,hektor_annonce_id,app_chaine_id,"
                                    "hektor_affaire_id,propositions_json",
                          "app_affaire_id": "in.(%s)" % ",".join(map(str, lot))}) or []):
            ledger[str(r["app_affaire_id"])] = r
    print("l'app : %d transactions lues" % len(ledger))

    # ─── ③ MODELO ────────────────────────────────────────────────────────────
    modelo = charger_modelo()
    print()

    # ─── LE DOSSIER, LIGNE PAR LIGNE ─────────────────────────────────────────
    dossier = []
    for x in sorted(a_trancher, key=lambda y: -y["ecart_num"]):
        iu = x["id_unique"]
        rang, sh = du_sheet.get(iu, (None, {}))
        trs = [ledger[str(a)] for a in par_iu.get(iu, []) if str(a) in ledger]
        num_mandat = sh.get("Mandat", "")
        mdl = modelo.get(str(num_mandat).strip(), [])
        #: ⭐ LA RECOMMANDATION, et elle s'appuie sur les trois sources
        reco, pourquoi = "a regarder", []
        if x["famille"] == "date d offre":
            an_cl = int(x["classeur"][:4])
            an_no = int(x["nous"][:4])
            meme_jour = x["classeur"][5:] == x["nous"][5:]
            if meme_jour and an_cl != an_no:
                reco = "NOUS corrigeons chez nous" if an_cl > an_no else "le CLASSEUR se trompe"
                pourquoi.append("MEME JOUR ET MEME MOIS, seule l'ANNEE differe "
                                "(%s contre %s) -> c'est une faute de SAISIE, "
                                "pas un desaccord" % (an_cl, an_no))
                if mdl:
                    d1 = iso(mdl[0].get("date_start"))
                    pourquoi.append("MODELO : le mandat %s demarre le %s"
                                    % (num_mandat, d1 or "?"))
                    if d1 and d1[:4] == str(an_cl):
                        reco = "le CLASSEUR a raison"
                        pourquoi.append("-> l'annee du mandat confirme LE CLASSEUR")
                    elif d1 and d1[:4] == str(an_no):
                        reco = "NOUS avons raison"
                        pourquoi.append("-> l'annee du mandat confirme NOTRE date")
            else:
                pourquoi.append("le jour ou le mois differe aussi : ce n'est pas "
                                "une simple faute d'annee")
        else:
            a, b = nb(x["classeur"]), nb(x["nous"])
            he = nb((trs[0] if trs else {}).get("honoraires_entree"))
            hs = nb((trs[0] if trs else {}).get("honoraires_sortie"))
            ca = nb((trs[0] if trs else {}).get("commission_agence"))
            pourquoi.append("chez nous : honoraires entree %s . sortie %s . "
                            "commission_agence %s" % (he, hs, ca))
            #: ⭐⭐⭐ LE CRITERE OBJECTIF QUI TRANCHE SANS AVIS : LE TAUX. Une
            #:   commission d'agence vit entre ~3 % et ~10 % du prix. Un taux de
            #:   72 % (18 000 sur un bien a 25 000, cas NEFHS7JI) est IMPOSSIBLE.
            #:   On ne juge donc pas « qui a raison » au sentiment : on regarde
            #:   lequel des deux chiffres est PLAUSIBLE.
            prix = nb(x_prix := sh.get("Prix", ""))
            #: ⛔ et on n'utilise le prix QUE s'il en est un : la colonne porte
            #:   1 008 DEPARTEMENTS et des prix d'annonce avant 2025.
            if prix and prix >= 10000:
                t_cl = 100.0 * a / prix
                t_no = 100.0 * b / prix
                pourquoi.append("le taux sur le prix (%.0f EUR) : classeur %.1f %% . "
                                "nous %.1f %%" % (prix, t_cl, t_no))
                ok_cl = 2.0 <= t_cl <= 12.0
                ok_no = 2.0 <= t_no <= 12.0
                if ok_cl and not ok_no:
                    reco = "le CLASSEUR a raison (notre taux est impossible)"
                    pourquoi.append("⭐ %.1f %% est hors de tout bareme -- la valeur "
                                    "de l'app est aberrante" % t_no)
                elif ok_no and not ok_cl:
                    reco = "NOUS avons raison (le taux du classeur est impossible)"
                    pourquoi.append("⭐ %.1f %% est hors de tout bareme" % t_cl)
                elif ok_cl and ok_no:
                    reco = "LES DEUX sont plausibles -- a toi de dire"
                    pourquoi.append("⚠ les deux taux tiennent dans le bareme : "
                                    "aucune mesure ne tranche, c'est une decision")
                else:
                    pourquoi.append("⚠ AUCUN des deux taux n'est plausible -- le "
                                    "prix du classeur est peut-etre faux lui aussi")
            else:
                pourquoi.append("⚠ pas de prix exploitable (la colonne porte aussi "
                                "des departements et des prix d'annonce)")
            if he and hs and abs((he + hs) - a) < 2:
                reco = "NOUS avons raison (le classeur ne voit qu'une part)"
                pourquoi.append("⭐ entree + sortie = %.0f = le classeur -> le "
                                "classeur porte LE TOTAL, nous le detaillons" % (he + hs))
            elif ca and abs(ca * 1.2 - a) < 2:
                reco = "AUCUN ECART REEL -- c'est la TVA"
                pourquoi.append("⭐ commission_agence x 1,20 = %.0f = le classeur "
                                "(il est TTC, nous HT)" % (ca * 1.2))
            elif b and a and abs(a / b - 2) < 0.02:
                reco = "le CLASSEUR porte LE DOUBLE"
                pourquoi.append("⭐ rapport exactement x2 : une part comptee deux fois ?")
        dossier.append({
            "id": iu, "ligne_sheet": rang, "famille": x["famille"],
            "ecart": x["ecart"], "classeur": x["classeur"], "nous": x["nous"],
            "etat_classeur": sh.get("Etat Actuel", ""),
            "mandat": num_mandat, "ville": sh.get("Ville", ""),
            "vendeur": sh.get("Vendeur", ""), "acquereur": sh.get("Acquéreur", ""),
            "prix_sheet": sh.get("Prix", ""),
            "commission_sheet": sh.get("Commission TTC", ""),
            "sheet_offre": sh.get("Offre Achat", ""),
            "sheet_compromis": sh.get("Compromis", ""),
            "sheet_vente": sh.get("Vente Réglée", ""),
            "app": [{"id": t["app_affaire_id"], "kind": t["kind"],
                     "state": t.get("state"), "date": date_vraie(t)[0],
                     "date_brute": date_vraie(t)[1],
                     "alerte_date": date_vraie(t)[2],
                     "annonce": t.get("hektor_annonce_id"),
                     "mandat": t.get("numero_mandat"),
                     "he": t.get("honoraires_entree"),
                     "hs": t.get("honoraires_sortie"),
                     "ca": t.get("commission_agence"),
                     "hektor": t.get("hektor_affaire_id")} for t in trs],
            "modelo": [{"num": m.get("mandate_number"),
                        "ref": m.get("linked_product_ref"),
                        "debut": iso(m.get("date_start")),
                        "fin": iso(m.get("date_end")),
                        "compromis": iso(m.get("date_of_sales_agreement")),
                        "acte": iso(m.get("date_of_deed")),
                        "etat": m.get("state"), "type": m.get("mandate_type"),
                        "nom": str(m.get("contact_full_name") or "")[:60]}
                       for m in mdl[:3]],
            "reco": reco, "pourquoi": pourquoi})

    SORTIE.write_text(json.dumps(dossier, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print("ecrit : %s  (%d lignes)" % (SORTIE, len(dossier)))
    print()
    print("=== LES RECOMMANDATIONS, PAR VERDICT ===")
    from collections import Counter
    for r, n in Counter(d["reco"] for d in dossier).most_common():
        print("   %-48s %3d" % (r[:48], n))
    print()
    print("=== LES LIGNES OU MODELO A PARLE ===")
    print("   %d lignes sur %d ont trouve leur mandat dans MODELO"
          % (sum(1 for d in dossier if d["modelo"]), len(dossier)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
