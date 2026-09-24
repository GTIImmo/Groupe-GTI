#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C.9-b — UNE ANNONCE, UN NUMERO : le serveur et Supabase sont-ils d'accord ?
                                                                  24/09/2026

L'OEIL QUI MANQUAIT A L'ANNONCE (defaut D4 de l'audit du 24/09). Le contact en a
un depuis le matin meme -- `registre_couche_desaccord`, qui aurait vu passer les
294 179 identites doublees. L'annonce n'en avait aucun : 13 doublures sont
comparees chaque nuit, pas elle, et le push reconcilie les ecarts EN SILENCE
(`id_rewrites`, push_upgrade_to_supabase.py).

ON COMPARE DEUX CORRESPONDANCES « numero de l'app <-> numero Hektor » :
    le serveur   app_dossier            (61 267 lignes, toutes les annonces)
    Supabase     app_dossier_current    (13 432, les non archivees -- lue dans sa
                                         copie descendue a 07:30, ou en direct)

CE QUI EST GRAVE -- le seuil est ZERO, et il tient : mesure du 24/09, 0 partout,
empreinte de la copie identique a celle de Supabase en direct.
    deux_numeros          une meme annonce Hektor porte deux numeros (D1)
    croisements           un meme numero vise deux annonces Hektor
    inconnus_du_serveur   un numero de la plage de HEKTOR que le serveur ignore
    plage_sans_adoption   un numero >= 10 M sur le serveur que C.9-a n'a pas
                          adopte -- le compteur a deborde (D2-3)

CE QUI N'EST PAS GRAVE, et qu'on compte a part pour ne pas crier pour rien :
    en_attente            une annonce nee dans l'app que Hektor n'a pas encore
                          numerotee (ou que le miroir n'a pas encore tiree).
                          Elle n'existe que dans Supabase, et c'est normal.

UNE SEULE FORMULE, lue par la sonde de sante ET par le controle de nuit : deux
copies d'une meme regle divergent tot ou tard.

LECTURE SEULE.
    python phase2/checks/annonce_un_numero.py        la mesure, code 1 si grave
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"
PLAGE = 10_000_000
GRAVES = ("deux_numeros", "croisements", "inconnus_du_serveur", "plage_sans_adoption")

# Le CAST est du cote Supabase seulement : cote serveur, les colonnes restent nues
# pour que SQLite se serve de la cle primaire et de l'index UNIQUE (hektor_annonce_id).
_S_ID = "CAST(s.app_dossier_id AS INTEGER)"
_S_HK = "CAST(NULLIF(s.hektor_annonce_id, '') AS INTEGER)"

REQUETES = {
    "deux_numeros": f"""
        SELECT COUNT(*) FROM app_dossier_current s
          JOIN app_dossier d ON d.hektor_annonce_id = {_S_HK}
         WHERE d.id <> {_S_ID}""",
    "croisements": f"""
        SELECT COUNT(*) FROM app_dossier_current s
          JOIN app_dossier d ON d.id = {_S_ID}
         WHERE {_S_HK} IS NOT NULL AND d.hektor_annonce_id IS NOT NULL
           AND d.hektor_annonce_id <> {_S_HK}""",
    "inconnus_du_serveur": f"""
        SELECT COUNT(*) FROM app_dossier_current s
         WHERE {_S_ID} < {PLAGE}
           AND NOT EXISTS (SELECT 1 FROM app_dossier d WHERE d.id = {_S_ID})""",
    "en_attente": f"""
        SELECT COUNT(*) FROM app_dossier_current s
         WHERE {_S_ID} >= {PLAGE}
           AND NOT EXISTS (SELECT 1 FROM app_dossier d WHERE d.id = {_S_ID})""",
}


def _table_existe(conn: sqlite3.Connection, nom: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (nom,)).fetchone() is not None


def mesurer(conn: sqlite3.Connection) -> dict | None:
    """Rend les comptes, et `graves` leur somme. None si la mesure est impossible
    (une des deux tables manque) -- ce n'est PAS un zero, et la sonde le dira."""
    if not _table_existe(conn, "app_dossier") or not _table_existe(conn, "app_dossier_current"):
        return None
    comptes = {cle: conn.execute(sql).fetchone()[0] for cle, sql in REQUETES.items()}
    if _table_existe(conn, "app_dossier_adoption"):
        comptes["plage_sans_adoption"] = conn.execute(
            f"SELECT COUNT(*) FROM app_dossier d WHERE d.id >= {PLAGE} AND NOT EXISTS "
            "(SELECT 1 FROM app_dossier_adoption a WHERE a.app_dossier_id = d.id)").fetchone()[0]
    else:
        comptes["plage_sans_adoption"] = conn.execute(
            f"SELECT COUNT(*) FROM app_dossier WHERE id >= {PLAGE}").fetchone()[0]
    comptes["graves"] = sum(comptes[c] for c in GRAVES)
    comptes["serveur"] = conn.execute("SELECT COUNT(*) FROM app_dossier").fetchone()[0]
    comptes["supabase"] = conn.execute("SELECT COUNT(*) FROM app_dossier_current").fetchone()[0]
    return comptes


def main() -> int:
    conn = sqlite3.connect(f"file:{BASE.as_posix()}?mode=ro", uri=True)
    try:
        m = mesurer(conn)
    finally:
        conn.close()
    if m is None:
        print("NON MESURABLE : app_dossier ou app_dossier_current manque.")
        return 2
    print(f"serveur {m['serveur']} annonces · copie Supabase {m['supabase']}")
    for cle in GRAVES:
        print(f"  {cle:22} {m[cle]}")
    print(f"  {'en_attente':22} {m['en_attente']}   (normal : nee dans l'app, pas encore chez Hektor)")
    if m["graves"]:
        print(f"GRAVE : {m['graves']} ecart(s) -- une annonce doit avoir UN numero.")
        return 1
    print("Une annonce, un numero : le serveur et Supabase sont d'accord.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
