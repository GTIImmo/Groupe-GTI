#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L'ETAT DU 11/11, POUR LE TEMOIN DE LA GARDE DU BIEN.                         23/11/2026

    python -u -X utf8 phase2/checks/extraire_etat_du_11_11_pour_la_garde_du_bien.py

POURQUOI. La garde ⑤ du lot de refus (Console/enqueue_refus_offres_mortes_lot.js) se prouve en rejouant LE VRAI CODE
du lot sur l'etat d'AVANT le geste du 11/11 (son mot du 23/11, § 4 a : « rejouee sur le 11/11, elle doit retenir
EXACTEMENT ces 17 offres -- et PAS UNE DE PLUS »). Ce script ne fait que FOURNIR cet etat ; il ne juge rien.

CE QU'IL LIT, EN LECTURE SEULE :
  1. le registre du 11/11 a 08:00 (07:00:18 UTC), dans la sauvegarde datee
     C:\\Hektor\\Backups\\critical\\critical_20261111_080002.sqlite.gz -- 31 151 lignes, AVANT le lot de 17:21 ;
     ⚠ `present_in_hektor` y est un ENTIER (0/1) : il est rendu en BOOLEEN, comme le rend PostgREST, sinon
       vivante() du lot (« === false ») laisserait passer les lignes supprimees ;
     ⚠ `transaction_origine` n'existait pas encore (posee le 16/11) : aucune ligne du classeur au 11/11 -> null ;
  2. chez Supabase (lecture seule, REPEATABLE READ READ ONLY) : les travaux change_hektor_offre_status poses du 11 au
     13/11 -- ce que le lot a VRAIMENT fait, et les 19 reacceptations du 12/11.
ECRIT : C:\\Hektor\\chantier_classeur_q6_cache\\garde_du_bien\\etat_du_11_11.json (hors du depot).
CODES : 0 fait . 2 pas pu
"""
from __future__ import annotations

import gzip
import json
import shutil
import sqlite3
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))

SAUVEGARDE = Path(r"C:\Hektor\Backups\critical\critical_20261111_080002.sqlite.gz")
SORTIE = Path(r"C:\Hektor\chantier_classeur_q6_cache\garde_du_bien")
COLONNES = ("app_affaire_id", "app_chaine_id", "kind", "state", "hektor_annonce_id", "hektor_affaire_id",
            "present_in_hektor", "montant", "date")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if not SAUVEGARDE.exists():
        print("⛔ pas de sauvegarde du 11/11 : %s -- code 2" % SAUVEGARDE)
        return 2
    SORTIE.mkdir(parents=True, exist_ok=True)
    tmp = SORTIE / "critical_20261111.sqlite"
    with gzip.open(SAUVEGARDE, "rb") as src, tmp.open("wb") as dst:
        shutil.copyfileobj(src, dst, 1 << 22)
    try:
        con = sqlite3.connect("file:%s?mode=ro" % tmp.as_posix(), uri=True)
        quand = con.execute("select min(created_at) from _backup_manifest").fetchone()[0] \
            if "created_at" in [r[1] for r in con.execute("pragma table_info(_backup_manifest)")] else None
        if quand is None:
            quand = con.execute("select * from _backup_manifest limit 1").fetchone()[0]
        lignes = []
        for r in con.execute("select %s from app_affaire_ledger" % ", ".join(COLONNES)):
            d = dict(zip(COLONNES, r))
            d["hektor_annonce_id"] = None if d["hektor_annonce_id"] is None else str(d["hektor_annonce_id"])
            d["hektor_affaire_id"] = None if d["hektor_affaire_id"] in (None, "") else str(d["hektor_affaire_id"])
            p = d["present_in_hektor"]
            d["present_in_hektor"] = None if p is None else bool(int(p))
            d["transaction_origine"] = None
            lignes.append(d)
        con.close()
    finally:
        tmp.unlink(missing_ok=True)
    import sauvegarde_datee_classeur as S
    try:
        cn, cu = S.connexion()
    except Exception as e:  # noqa: BLE001
        print("⛔ Supabase n'a pas pu etre lu (%s) -- code 2" % str(e).splitlines()[0][:160])
        return 2
    try:
        cu.execute("select id, status, created_at, hektor_annonce_id, payload_json from public.app_console_job "
                   "where job_type = 'change_hektor_offre_status' and created_at >= '2026-11-11' "
                   "and created_at < '2026-11-14' order by created_at")
        travaux = []
        for i, st, cr, ann, p in cu.fetchall():
            p = p or {}
            travaux.append({"id": str(i), "status": st, "created_at": str(cr), "hektor_annonce_id": str(ann or ""),
                            "type": p.get("type"), "origine": p.get("origine"),
                            "app_affaire_id": p.get("app_affaire_id"), "hektor_offre_id": p.get("hektor_offre_id")})
        cn.rollback()
    finally:
        cn.close()
    out = {"sauvegarde": SAUVEGARDE.name, "prise_le_utc": str(quand), "lignes": lignes, "travaux": travaux}
    f = SORTIE / "etat_du_11_11.json"
    f.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print("registre du 11/11 : %d lignes (sauvegarde %s, %s) ; travaux du 11 au 13/11 : %d -> %s"
          % (len(lignes), SAUVEGARDE.name, quand, len(travaux), f))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
