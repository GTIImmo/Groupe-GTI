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
    creation_echouee      (4c, 11/10/2026) une annonce nee dans l'app dont le
                          travail de creation est EN ERREUR : elle n'arrivera
                          jamais chez Hektor, et personne ne la comptait.

CE QUI N'EST PAS GRAVE, et qu'on compte a part pour ne pas crier pour rien :
    en_attente            une annonce nee dans l'app que Hektor n'a pas encore
                          numerotee (ou que le miroir n'a pas encore tiree).
                          Elle n'existe que dans Supabase, et c'est normal.

⚠ 4c -- POURQUOI `en_attente` NE JUGEAIT PAS, ET CE QUI A CHANGE. Au 24/09 ce
  compteur melangeait l'attente normale et l'echec, faute de savoir les separer :
  il etait donc range, a raison, dans « ce qui n'est pas grave ». Depuis le 11/10
  la coupure existe -- L'ETAT DU TRAVAIL DE CREATION, jamais la duree (mesure :
  l'attente normale va jusqu'a 44 MINUTES, file comprise ; tout delai aurait
  sonne faux). Les deux comptes sont exclusifs et leur somme est celle d'avant.
  Voir le commentaire de _TRAVAIL_EN_ERREUR, plus bas.

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
GRAVES = ("deux_numeros", "croisements", "inconnus_du_serveur", "plage_sans_adoption",
          # 4c (11/10/2026) : voir _TRAVAIL_EN_ERREUR ci-dessous.
          "creation_echouee")

# Le CAST est du cote Supabase seulement : cote serveur, les colonnes restent nues
# pour que SQLite se serve de la cle primaire et de l'index UNIQUE (hektor_annonce_id).
_S_ID = "CAST(s.app_dossier_id AS INTEGER)"
_S_HK = "CAST(NULLIF(s.hektor_annonce_id, '') AS INTEGER)"

# ── 4c (11/10/2026) : CE QUI SEPARE UNE ATTENTE NORMALE D'UN ECHEC ────────────
#
# `en_attente` comptait les deux ensemble, et c'est pour CELA qu'il etait range
# dans « ce qui n'est pas grave » : au 24/09, rien ne permettait de distinguer
# une annonce qui attend son numero d'une annonce dont la creation a RATE.
#
# ⚠ ON NE PEUT PAS TRANCHER SUR LA DUREE, et c'est la question de Frederic qui
#   l'a montre. Mesure du 11/10 sur les 79 creations reelles :
#       le travail lui-meme      28,2 s mini · 52,7 s median · 63,8 s au pire
#       l'attente dans la file    3,4 s median · 2 646 s AU PIRE (44 minutes)
#       bout en bout             59,7 s median · 2 669 s AU PIRE
#   N'importe quel delai -- 5, 15 ou meme 30 minutes -- aurait donc sonne
#   FAUSSEMENT au moins une fois dans l'histoire reelle. Une sentinelle qui crie
#   pour rien devient muette a force d'etre ignoree (cf. contact_sans_numero).
#
# ON TRANCHE DONC SUR L'ETAT DU TRAVAIL, jamais sur l'horloge :
#       pending / running  ->  on se TAIT, meme apres 44 minutes
#       done               ->  la ligne a son numero, rien a dire
#       error              ->  la creation a vraiment echoue  ->  GRAVE
#   Aucune fenetre, donc aucune fausse alerte possible par construction.
#
# ET L'ETAT `error` ARRIVE TOUT SEUL, par trois chemins qui existent deja :
#   le travail leve · il depasse les 10 min du minuteur du worker · il reste
#   bloque « running » plus de 30 min (garde-fou de app_console_claim_next_job).
#   Prix de cette surete : l'alerte peut arriver ~30-40 min apres le fait. Le
#   negociateur, LUI, est averti sur le moment (cloche, mecanisme du 20/08).
#
# LE LIEN ENTRE LE DOSSIER ET SON TRAVAIL : la CHARGE du travail, et elle seule.
#   La colonne app_console_job.app_dossier_id est VIDE sur les 79 creations
#   (mesure du 11/10, 0/79) ; `payload_json->app_dossier_id` y est par
#   CONSTRUCTION des que l'annonce nait dans l'app (la fonction SQL
#   app_create_annonce_job_optimistic l'y ecrit). Et `source_hash` ('c9e3:<jeton>')
#   est inutilisable : la synchro le REECRIT des que tout va bien.
_TRAVAIL_EN_ERREUR = """
    EXISTS (SELECT 1 FROM app_console_job j
             WHERE j.job_type = 'create_hektor_draft_annonce'
               AND j.status = 'error'
               AND CAST(json_extract(j.payload_json, '$.app_dossier_id') AS INTEGER) = {id})"""

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
    # 4c : la MEME population qu'avant, coupee en deux par l'etat du travail.
    #      Les deux requetes sont exclusives et leur somme est inchangee : un
    #      compte qui baisse ici doit se retrouver dans l'autre, jamais se perdre.
    "en_attente": f"""
        SELECT COUNT(*) FROM app_dossier_current s
         WHERE {_S_ID} >= {PLAGE}
           AND NOT EXISTS (SELECT 1 FROM app_dossier d WHERE d.id = {_S_ID})
           AND NOT {_TRAVAIL_EN_ERREUR.format(id=_S_ID)}""",
    "creation_echouee": f"""
        SELECT COUNT(*) FROM app_dossier_current s
         WHERE {_S_ID} >= {PLAGE}
           AND NOT EXISTS (SELECT 1 FROM app_dossier d WHERE d.id = {_S_ID})
           AND {_TRAVAIL_EN_ERREUR.format(id=_S_ID)}""",
}


def _table_existe(conn: sqlite3.Connection, nom: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (nom,)).fetchone() is not None


def mesurer(conn: sqlite3.Connection) -> dict | None:
    """Rend les comptes, et `graves` leur somme. None si la mesure est impossible
    (une des deux tables manque) -- ce n'est PAS un zero, et la sonde le dira."""
    if not _table_existe(conn, "app_dossier") or not _table_existe(conn, "app_dossier_current"):
        return None
    # 4c : la coupure a besoin de la doublure des travaux. Si elle manque, on NE
    # REND PAS un zero -- un zero dirait « rien n'a echoue », ce qu'on ne sait
    # pas. On revient au compte d'avant (les deux ensemble) et on le DIT.
    travaux = _table_existe(conn, "app_console_job")
    comptes = {cle: conn.execute(sql).fetchone()[0] for cle, sql in REQUETES.items()
               if travaux or cle not in ("en_attente", "creation_echouee")}
    comptes["creation_echouee_mesurable"] = travaux
    if not travaux:
        comptes["en_attente"] = conn.execute(f"""
            SELECT COUNT(*) FROM app_dossier_current s
             WHERE {_S_ID} >= {PLAGE}
               AND NOT EXISTS (SELECT 1 FROM app_dossier d WHERE d.id = {_S_ID})""").fetchone()[0]
        comptes["creation_echouee"] = None
    if _table_existe(conn, "app_dossier_adoption"):
        comptes["plage_sans_adoption"] = conn.execute(
            f"SELECT COUNT(*) FROM app_dossier d WHERE d.id >= {PLAGE} AND NOT EXISTS "
            "(SELECT 1 FROM app_dossier_adoption a WHERE a.app_dossier_id = d.id)").fetchone()[0]
    else:
        comptes["plage_sans_adoption"] = conn.execute(
            f"SELECT COUNT(*) FROM app_dossier WHERE id >= {PLAGE}").fetchone()[0]
    # Un compteur non mesurable ne pese pas dans la somme -- mais il reste
    # visible (`creation_echouee_mesurable`), il ne se deguise pas en zero.
    comptes["graves"] = sum(comptes[c] for c in GRAVES if comptes.get(c) is not None)
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
        valeur = "NON MESURABLE" if m[cle] is None else m[cle]
        print(f"  {cle:22} {valeur}")
    print(f"  {'en_attente':22} {m['en_attente']}   (normal : nee dans l'app, pas encore chez Hektor)")
    if m["graves"]:
        print(f"GRAVE : {m['graves']} ecart(s) -- une annonce doit avoir UN numero.")
        return 1
    if not m["creation_echouee_mesurable"]:
        # 4c : on ne dit pas « tout va bien » quand on n'a pas pu regarder.
        print("NON MESURABLE : la doublure app_console_job manque -- une creation")
        print("  echouee ne serait pas vue. « en_attente » melange donc les deux cas.")
        return 2
    print("Une annonce, un numero : le serveur et Supabase sont d'accord.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
