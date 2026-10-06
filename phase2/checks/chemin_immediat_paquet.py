# -*- coding: utf-8 -*-
"""LE CHEMIN IMMEDIAT CONSTRUIT-IL ENCORE SON PAQUET ?    LECTURE SEULE. 06/10/2026

POURQUOI CE CONTROLE EXISTE
----------------------------
Le 05/10/2026, de 08:44 a 16:34, **13 retours de fiche ont echoue en silence**.
La cause : `charger_mandants_du_registre_des_liens` (export_app_payload.py) lisait
`ligne["ann"]`, ce qui exige `con.row_factory = sqlite3.Row`.

    le run de nuit         pose row_factory  (mandat_ledger.py:184)  -> il passait
    registre_mandats_upsert pose row_factory                         -> il passait
    push_single_annonce    NE LE POSE PAS    (ligne 669)             -> il CASSAIT

J'avais « prouve » ce correctif TROIS FOIS, toujours par un chemin qui pose
`row_factory`. Neuf heures de panne, zero alerte, et l'ecran ne montrait rien.

⭐ LA LECON, ET ELLE EST DEJA EN MEMOIRE (`eprouver-c-est-executer-le-code`) :
  une fonction partagee par plusieurs chemins ne doit JAMAIS etre eprouvee par un
  seul. Ce controle EXECUTE le chemin qui casse, pas celui qui marche.

CE QU'IL FAIT, ET CE QU'IL NE FAIT PAS
---------------------------------------
Il ouvre la base **exactement comme `push_single_annonce_to_supabase.py` ligne 669** :

    sqlite3.connect(...)        <- et SURTOUT PAS de row_factory

puis appelle `build_payload(dossier_ids=[...])`, le meme appel qu'a sa ligne 746.

⛔ IL N'ECRIT RIEN. Ni en local, ni chez Supabase, ni chez Hektor :
   · la connexion est ouverte en `mode=ro`
   · il ne fabrique pas les tables temporaires (le paquet se construit tres bien
     sur l'`app_view_generale` deja en place)
   · il n'appelle NI `push_payload`, NI `reappliquer_saisies_app`
   Donc il est sans danger meme pendant un run -- il LIT, point.

⚠ ET IL NE SE CONTENTE PAS DE « PAS D'EXCEPTION ». Un paquet vide ne leve rien :
  c'est exactement comme ca que le deballeur de la diffusion a rendu zero pendant
  trois mois (`deballeur-forme-inconnue-silence`). Il compte donc ce qu'il a lu, et
  **il l'imprime** -- parce qu'un controle qui ne dit pas ce qu'il a lu peut
  affirmer le contraire de la verite sans se tromper d'un chiffre (lecon du 30/09).

LES TEMOINS SONT CHOISIS PAR REQUETE, PAS ECRITS EN DUR
--------------------------------------------------------
Un identifiant en dur devient faux des que l'annonce est vendue ou archivee. Le
controle choisit donc lui-meme, a chaque passage, un temoin de chaque famille :

    ordinaire       un mandat au corps sain, avec des mandants
    corps_suspect   une des lignes dont le corps vient d'un autre mandat
    sans_mandant    une ligne de VENTE que Hektor laisse vide
    multi_mandats   un bien qui porte plusieurs mandats

Si une famille est vide, il le DIT et passe -- il ne la saute pas en silence.

    python phase2/checks/chemin_immediat_paquet.py
    python phase2/checks/chemin_immediat_paquet.py --annonce 61811
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase2.sync.export_app_payload import (  # noqa: E402
    attach_hektor_read,
    build_payload,
    charger_corps_suspects,
)

PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"

for flux in (sys.stdout, sys.stderr):
    try:
        # ⚠ line_buffering : sans lui la sortie reste tamponnee quand on redirige,
        #   et on ne voit RIEN pendant les ~20 s que prend chaque temoin. Un
        #   controle muet pendant deux minutes se fait tuer avant sa conclusion.
        flux.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass


def _connexion_du_chemin_immediat() -> sqlite3.Connection:
    """La MEME forme que push_single_annonce_to_supabase.py ligne 669.

    ⚠⚠ L'ABSENCE DE `row_factory` EST LE COEUR DE CE CONTROLE. Ne pas l'ajouter
      « pour faire propre » : ce serait transformer le chemin qui casse en celui
      qui marche, et le controle cesserait de voir quoi que ce soit.
    Seule difference assumee : `mode=ro`, pour qu'il ne puisse rien ecrire.
    """
    con = sqlite3.connect(f"file:{PHASE2_DB.as_posix()}?mode=ro", uri=True, timeout=60)
    con.execute("PRAGMA busy_timeout = 60000")
    return con


def choisir_temoins(con: sqlite3.Connection) -> dict[str, tuple[str, int]]:
    """Un temoin par famille : (hektor_annonce_id, app_dossier_id).

    ⚠⚠ LE TEMOIN DOIT ETRE DANS LE PERIMETRE DES DOSSIERS, et c'est une erreur que
      j'ai faite en ecrivant ce controle : ma premiere version prenait les temoins
      dans `app_dossier` (61 352 lignes, tout le parc). Elle tombait donc sur des
      annonces ARCHIVEES, que `SQL_DOSSIERS_BASE` ne sert pas -- et les quatre
      temoins « echouaient » avec `dossiers=0` alors que le chemin etait SAIN.
      ⭐ UN CONTROLE QUI CRIE AU LOUP NE SERT A RIEN : on le desactive au bout de
        trois fois, et le jour de la vraie panne il n'est plus la.
      On choisit donc dans `app_view_generale`, qui EST le perimetre.
    """
    temoins: dict[str, tuple[str, int]] = {}
    # LE PERIMETRE EXACT, copie d'ANNONCES_SCOPE_WHERE : un dossier archive ou
    # vendu n'est PAS servi par SQL_DOSSIERS_BASE, donc `dossiers=0` y est NORMAL.
    PERIM = (
        " COALESCE(v.archive, '0') = '0'"
        " AND COALESCE(v.detail_statut_name, v.statut_annonce, '')"
        "     IN ('Actif', 'Sous offre', 'Sous compromis', 'Estimation')"
        " AND v.app_dossier_id IS NOT NULL")

    def _premier(sql: str, params: tuple = ()) -> tuple[str, int] | None:
        ligne = con.execute(sql, params).fetchone()
        return (str(ligne[0]), int(ligne[1])) if ligne and ligne[1] is not None else None

    # Le cas ordinaire : un dossier SERVI, avec un mandat et des mandants.
    t = _premier(
        "SELECT v.hektor_annonce_id, v.app_dossier_id FROM app_view_generale v"
        " WHERE " + PERIM +
        "   AND TRIM(COALESCE(v.mandants_texte, '')) <> ''"
        "   AND TRIM(COALESCE(v.numero_mandat, '')) <> ''"
        " ORDER BY v.app_dossier_id DESC LIMIT 1")
    if t:
        temoins["ordinaire"] = t

    # Une ligne de VENTE que Hektor laisse sans mandant.
    t = _premier(
        "SELECT v.hektor_annonce_id, v.app_dossier_id FROM app_view_generale v"
        "  JOIN app_mandat m ON CAST(m.hektor_annonce_id AS TEXT) = CAST(v.hektor_annonce_id AS TEXT)"
        " WHERE " + PERIM +
        "   AND (m.mandants_texte IS NULL OR TRIM(m.mandants_texte) = '')"
        "   AND m.origine = 'detail' AND m.nature = 'VENTE' LIMIT 1")
    if t:
        temoins["sans_mandant"] = t

    # Un bien qui porte PLUSIEURS mandats.
    t = _premier(
        "SELECT v.hektor_annonce_id, v.app_dossier_id FROM app_view_generale v"
        " WHERE " + PERIM +
        "   AND CAST(v.hektor_annonce_id AS TEXT) IN ("
        "     SELECT CAST(hektor_annonce_id AS TEXT) FROM app_mandat"
        "      GROUP BY 1 HAVING COUNT(*) > 1) LIMIT 1")
    if t:
        temoins["multi_mandats"] = t

    # Une ligne dont le corps vient d'un AUTRE mandat.
    # ⚠ charger_corps_suspects rend un ensemble VIDE si le miroir n'est pas attache
    #   -- c'est volontaire et documente, mais ici on l'attache, donc il doit parler.
    suspects = charger_corps_suspects(con)
    for annonce_id, _numero in sorted(suspects):
        ligne = con.execute(
            "SELECT v.app_dossier_id FROM app_view_generale v"
            " WHERE " + PERIM + " AND CAST(v.hektor_annonce_id AS TEXT) = ?",
            (annonce_id,)).fetchone()
        if ligne and ligne[0] is not None:
            temoins["corps_suspect"] = (annonce_id, int(ligne[0]))
            break
    return temoins


def eprouver(annonce_id: str, app_dossier_id: int) -> tuple[bool, str]:
    """Rejoue la construction du paquet. Rend (ok, ce qu'on a lu)."""
    con = _connexion_du_chemin_immediat()
    try:
        attach_hektor_read(con)
        paquet = build_payload(
            limit=None,
            dossier_ids=[app_dossier_id],
            include_filter_catalog=False,
            connection=con,
        )
    except Exception as exc:
        traceback.print_exc()
        return False, "EXCEPTION %s : %s" % (type(exc).__name__, exc)
    finally:
        try:
            con.close()
        except Exception:
            pass

    dossiers = paquet.get("dossiers") or []
    registre = paquet.get("mandat_register_rows") or paquet.get("mandat_register") or []
    if not isinstance(dossiers, list):
        dossiers = []
    if not isinstance(registre, list):
        registre = []
    avec_json = sum(
        1 for r in registre
        if isinstance(r, dict) and str(r.get("mandants_json") or "").strip() not in ("", "[]"))
    lu = "dossiers=%d · lignes de registre=%d · dont mandants_json=%d" % (
        len(dossiers), len(registre), avec_json)

    # ⚠ UN PAQUET VIDE NE LEVE RIEN. C'est le silence qu'on refuse.
    if not dossiers:
        return False, lu + "  ⛔ AUCUN dossier construit"
    return True, lu


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annonce", help="eprouver UNE annonce precise (son id Hektor)")
    args = parser.parse_args()

    print("CONTROLE — le chemin immediat construit-il son paquet ? (lecture seule)")
    print("   la connexion est ouverte SANS row_factory, comme")
    print("   push_single_annonce_to_supabase.py ligne 669.")
    print()

    con = _connexion_du_chemin_immediat()
    try:
        attach_hektor_read(con)
        if args.annonce:
            ligne = con.execute(
                "SELECT id FROM app_dossier WHERE CAST(hektor_annonce_id AS TEXT) = ?",
                (str(args.annonce),)).fetchone()
            if not ligne or ligne[0] is None:
                print("   ⛔ annonce %s : aucun app_dossier_id" % args.annonce)
                return 1
            temoins = {"demande": (str(args.annonce), int(ligne[0]))}
        else:
            temoins = choisir_temoins(con)
    finally:
        try:
            con.close()
        except Exception:
            pass

    attendues = ("ordinaire", "corps_suspect", "sans_mandant", "multi_mandats")
    if not args.annonce:
        for famille in attendues:
            if famille not in temoins:
                # On le DIT, on ne le saute pas.
                print("   ⚠ famille « %s » : aucun temoin trouve -- NON EPROUVEE" % famille)

    if not temoins:
        print("   ⛔ aucun temoin : le controle n'a RIEN eprouve.")
        return 1

    echecs = 0
    for famille, (annonce_id, app_dossier_id) in sorted(temoins.items()):
        ok, lu = eprouver(annonce_id, app_dossier_id)
        print("   %-14s annonce %-8s dossier %-8s %s  %s"
              % (famille, annonce_id, app_dossier_id, "OK  " if ok else "ECHEC", lu))
        if not ok:
            echecs += 1

    print()
    if echecs:
        print("⛔ %d temoin(s) sur %d en ECHEC — le chemin immediat est casse." % (echecs, len(temoins)))
        print("   C'est la panne du 05/10 qui recommence : un retour de fiche echouera")
        print("   en silence, et l'ecran ne montrera rien.")
        return 1
    print("✅ %d temoin(s) sur %d : le paquet se construit." % (len(temoins), len(temoins)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
