# -*- coding: utf-8 -*-
"""26bis-3 : LA CARTE DES CHAMPS D'UNE ANNONCE. Lecture seule, rien n'est ecrit."""
import json, os, sqlite3, subprocess, sys
from pathlib import Path

R = Path(r"C:\Hektor\Projet")
S = Path(r"C:\Users\admin\AppData\Local\Temp\claude\C--Hektor\90804d76-518a-45cd-a401-a13d420e026b\scratchpad")

def sql(req):
    (S / "_carte.sql").write_text(req, encoding="utf-8")
    out = subprocess.run(["node", str(S / "run_sql_rows.js"), str(S / "_carte.sql")],
                         capture_output=True, text=True, cwd=str(R)).stdout
    return [json.loads(l) for l in out.strip().splitlines() if l.startswith("[")]

# 1. les colonnes de l'app
cols_dossier = {r["column_name"] for r in sql(
    "select column_name from information_schema.columns where table_name='app_dossier_current';")[0]}

# 2. les cles du grand bloc, avec leur taux de remplissage
bloc = sql("""with cles as (select jsonb_object_keys(detail_payload_json::jsonb) k
              from app_dossier_detail_current where detail_payload_json is not null)
              select k, count(*) n from cles group by 1 order by 2 desc;""")[0]
cles_bloc = {r["k"]: int(r["n"]) for r in bloc}

# 3. les colonnes du serveur
loc = sqlite3.connect(f"file:{R/'phase2'/'phase2.sqlite'}?mode=ro", uri=True)
cols_serveur = {r[1] for r in loc.execute("pragma table_info(app_view_generale)")}

# 4. ce que le worker sait pousser
poussables = set("""title description address address_complement postal_code city private_city
private_postal building transport proximity environment kitchen exposure view garden pool terrace
interior_state exterior_state dpe_value ges_value diagnostic_risk_comment mandate_number mandate_type
mandate_start_date mandate_end_date price net_seller_price surface carrez_surface room_count
bedroom_count floor level_count bathroom_count shower_room_count wc_count land_surface garden_surface
terrace_count garage_count garage_surface parking_inside_count parking_outside_count construction_year
copro_lots copro_charges copro_quote_part copro_works_fund fees latitude longitude""".split())

print("=" * 72)
print("LA CARTE DES CHAMPS D'UNE ANNONCE -- mesure du 21/09/2026")
print("=" * 72)
print(f"  colonnes dans l'app (app_dossier_current)      : {len(cols_dossier):>4}")
print(f"  cles du GRAND BLOC (detail_payload_json)       : {len(cles_bloc):>4}")
print(f"  colonnes sur le serveur (app_view_generale)    : {len(cols_serveur):>4}")
print(f"  champs que le worker sait POUSSER chez Hektor  : {len(poussables):>4}")
print()
total = len(cols_dossier) + len(cles_bloc)
print(f"  -> l'annonce porte donc ~{total} champs distincts cote app,")
print(f"    dont {len(cles_bloc)} dans un seul paquet de donnees.")
print()
communes = cols_dossier & cols_serveur
print(f"  colonnes communes app / serveur (arbitrables aujourd'hui) : {len(communes)}")
print("   ", ", ".join(sorted(communes)[:24]), "...")
print()
print("  TOP 20 des cles du grand bloc les plus remplies :")
for k, n in list(cles_bloc.items())[:20]:
    print(f"    {k:<34} {n:>7}")
