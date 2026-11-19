# -*- coding: utf-8 -*-
"""AUDIT V2, TEMPS 1 -- LA PHOTO EN LECTURE SEULE -- audit independant du 19/11/2026 (session de reprise V2).

Lit, sans rien ecrire nulle part sauf dans le dossier de travail :
  - le Sheet (API Google, GET seul) ;
  - phase2.sqlite en mode=ro (WAL : lecture concurrente sans verrou) ;
  - MODELO (mandats_extraits.xlsx) en lecture seule.

⛔ REGLE D'INDEPENDANCE n° 1 : on NE LIT PAS app_classeur_lien (le gel) ici.
   Il ne sera lu qu'APRES que mon appariement soit arrete et ecrit.
"""
import json
import pickle
import sqlite3
import sys
import time
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
SORTIE = RACINE / ".tmp" / "audit_v2_2026-11-19" / "photo"   # .tmp/ est ignore par git
SORTIE.mkdir(exist_ok=True)
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import apparier_classeur as ap  # noqa: E402  (on n'emprunte que lire_classeur et load_env_file)

t0 = time.time()
# ── 1. LE SHEET
ap.load_env_file(RACINE / ".env")
entetes, lignes = ap.lire_classeur()
if len(lignes) < 4700:
    raise SystemExit("ARRET : lecture du Sheet ratee (%d lignes)" % len(lignes))
(SORTIE / "sheet.json").write_text(json.dumps({"entetes": entetes, "lignes": lignes,
                                               "lu_le": time.strftime("%Y-%m-%d %H:%M:%S")},
                                              ensure_ascii=False), encoding="utf-8")
print("Sheet : %d lignes, %d colonnes d'en-tete" % (len(lignes), len(entetes)))

# ── 2. LA BASE LOCALE, EN LECTURE SEULE
con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                      uri=True, timeout=120)
con.execute("PRAGMA busy_timeout=120000")


def tout(sql):
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


photo = {}
photo["ledger"] = tout(
    "SELECT app_affaire_id, hektor_affaire_id, kind, state, date, date_acte, montant,"
    " numero_mandat, hektor_annonce_id, hektor_mandat_id, app_mandat_id, app_chaine_id,"
    " app_dossier_id, app_dossier_numero, app_dossier_uuid, acquereur_json, acquereurs_json,"
    " mandants_json, propositions_json, hektor_acquereur_id, app_contact_id,"
    " present_in_hektor, transaction_origine, honoraires_entree, honoraires_sortie,"
    " commission_agence, prix_net_vendeur, first_seen_at, last_seen_at, mandat_origine"
    " FROM app_affaire_ledger")
print("registre : %d transactions" % len(photo["ledger"]))
if len(photo["ledger"]) < 31000:
    raise SystemExit("ARRET : lecture du registre ratee")

COLS_ANN = ("hektor_annonce_id, numero_dossier, numero_mandat, titre_bien, ville, code_postal,"
            " type_bien, prix, commercial_nom, agence_nom, statut_annonce, mandat_type,"
            " mandat_date_debut, mandat_date_fin, mandants_texte")
for t in ("app_annonces_current", "app_archive_annonce_index_current",
          "app_historical_annonce_index_current", "app_mandat_register_current",
          "app_registre_mandats_current"):
    photo[t] = tout("SELECT %s FROM %s" % (COLS_ANN, t))
    print("%s : %d" % (t, len(photo[t])))

photo["app_mandat"] = tout(
    "SELECT app_mandat_id, hektor_annonce_id, numero_mandat, hektor_mandat_id, type, type_app,"
    " date_enregistrement, date_debut, date_fin, date_cloture, mandants_texte, origine,"
    " source_app, present_in_hektor FROM app_mandat")
print("app_mandat : %d" % len(photo["app_mandat"]))

# les noms des contacts, pour les acquereurs portes par un identifiant seul
photo["contacts"] = {r[0]: (r[1], r[2], r[3]) for r in con.execute(
    "SELECT hektor_contact_id, nom, prenom, display_name FROM app_contact_current")}
print("contacts : %d" % len(photo["contacts"]))
con.close()

# ── 3. MODELO
from openpyxl import load_workbook  # noqa: E402

GARDE = ["mandate_id", "mandate_number", "mandate_type", "exclusivity", "contact_full_name",
         "linked_product_ref", "product_recap", "date", "date_start", "date_end",
         "observations", "state", "deleted", "time_created", "date_of_sales_agreement",
         "date_of_deed"]
modelo = []
for chemin in (RACINE / "mandats_extraits.xlsx",
               RACINE / "liste mandat du 02_02_2026 au 28_02_2026.xlsx"):
    wb = load_workbook(chemin, read_only=True)
    ws = wb.worksheets[0]
    it = ws.iter_rows(values_only=True)
    tete = list(next(it))
    idx = {k: tete.index(k) for k in GARDE if k in tete}
    for r in it:
        d = {k: r[i] for k, i in idx.items()}
        for k in ("contact_full_name", "product_recap", "observations"):
            if isinstance(d.get(k), str):
                d[k] = d[k][:400]
        d["_fichier"] = chemin.name
        modelo.append(d)
    wb.close()
photo["modelo"] = modelo
print("MODELO : %d mandats (deux fichiers)" % len(modelo))

with open(SORTIE / "base.pkl", "wb") as f:
    pickle.dump(photo, f)
print("photo ecrite en %.0f s" % (time.time() - t0))
