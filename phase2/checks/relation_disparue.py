# -*- coding: utf-8 -*-
"""UN LIEN NE DISPARAIT PAS. LOCALE.                            30/09/2026

CE QU'ELLE SURVEILLE, ET POURQUOI C'EST CELA
---------------------------------------------
`app_relation` est le registre des liens : il garde tout, definitivement. La
seule question qui compte pour un registre est donc :

    est-ce qu'il contient toujours TOUT ce qu'on lui a confie ?

⚠ ELLE EST ECRITE APRES CELLE DU MANDAT, ET ELLE EN REPREND LES DEUX LECONS.
  (1) « Echu », « vendu », « archive » N'ONT AUCUN SENS POUR UN REGISTRE. Un
      lien sur un bien vendu en 2019 doit y figurer ; c'est meme LE cas qui
      justifie la table -- 82 386 liens que le cloud perdait.
  (2) NE PAS COMPARER A UNE GRANDEUR TRANSITOIRE. Le cloud porte moins que la
      table, et ce sera vrai jusqu'au rebranchement : c'est une INFORMATION,
      jamais une alerte. Une sentinelle qui surveille un ecart voulu ne survit
      pas a son chantier.

LES QUATRE GARDES, QUI RESTERONT VRAIES APRES LA COUPURE
---------------------------------------------------------
    source_absents   un lien de la couche absent de la table
                     -> l'etape de nuit ne passe plus, et le registre cesse
                        d'etre complet SANS RIEN DIRE
    doublons         deux lignes pour un meme couple (contact, bien)
                     -> la cle a cede
    hors_plage_app   un app_contact_id sous 10 000 000
                     -> la substitution d'identite n'a pas eu lieu, et on
                        rangerait un numero Hektor dans une colonne qui
                        s'appelle app_contact_id
    plage_envahie    un id du run dans la plage reservee a l'app
                     -> le defaut d'aout, cinq jours de creations impossibles

LA MESURE SE FAIT EN MEMOIRE, PAS EN SQL
-----------------------------------------
⚠ LECON PAYEE LE MATIN MEME : un `NOT EXISTS` sur une table sans index a tenu un
  verrou d'ecriture 8 min 30 sur phase2.sqlite (132 000 x 132 000 comparaisons),
  puis a ete coupe avant le commit. Et la sonde du mandat, ecrite de la meme
  facon, tournait plus de DEUX MINUTES avant d'etre coupee -- une garde qui ne
  tourne pas n'est pas une garde.
  132 000 couples tiennent dans un ensemble Python. La mesure prend moins d'une
  seconde, et n'ouvre AUCUNE transaction d'ecriture.

CE QU'ELLE REND
---------------
`None` si une table manque -- une mesure impossible n'est PAS un zero, et la
sonde doit le dire.

LECTURE SEULE.
    python phase2/checks/relation_disparue.py     code 1 si grave
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"

# La moitie haute est reservee aux liens nes dans l'app.
PLAGE_RESERVEE_APP = 1_000_000
# Sous ce seuil, un numero de contact n'est pas un numero d'app.
PLAGE_CONTACT_APP = 10_000_000
# Les deux libelles du MEME fait Hektor (« proprietaire du bien »).
ROLES_DU_BIEN = ("mandant", "proprietaire")

# ⑤ et ⑥ ajoutees le 03/10/2026 -- LE CONTRAT D'AUTORITE DE LA RELATION.
#
# POURQUOI ELLES MANQUAIENT, ET CE QU'ELLES GARDENT.
#   Le plan reclame depuis le 30/09 « un registre des relations autonome, mis a jour
#   selon un CONTRAT D'AUTORITE entre le run de nuit Hektor et les workers de l'app ».
#   Ce contrat EXISTE EN FAIT -- l'adoption de `retire_le` depuis la doublure, dans
#   relation_ledger.refresh() -- mais PAS EN DROIT : rien ne verifiait qu'il tenait.
#
#   LA REGLE, et elle est simple : `retire_le` / `retire_par` APPARTIENNENT A L'APP.
#   Le miroir Hektor ne peut PAS les produire : quand un negociateur retire un
#   mandant, Hektor se contente de ne plus montrer le lien -- il ne dit jamais
#   « celui-ci a ete retire le 3 a 16h43 par Frederic ». Seule l'app le sait.
#
#   CE QUE CA COUTE QUAND LE CONTRAT LACHE, et c'est mesure : le run reconstruit sa
#   table depuis le miroir, n'y voit aucun retrait, et POUSSE sa liste entiere --
#   retire_le = NULL compris. LE LIEN REAPPARAIT A L'ECRAN, et le run dit « reussi ».
#
# ⑤ `retraits_perdus` : le cloud porte un retrait que le serveur ignore.
#    C'est l'etat EXACT d'avant l'ecrasement. Zero exige.
# ⑥ `doublure_perimee` : la doublure n'est pas du jour.
#    ⚠ C'EST LA GARDE DE LA GARDE. L'adoption lit la doublure ; si elle date, elle
#      ne voit pas le retrait d'hier apres-midi et ⑤ reste a zero EN MENTANT.
#      `doublure_du` etait deja rendu dans le bilan du ledger -- mais il n'etait
#      QU'IMPRIME. Rien n'en faisait une alerte. Une mesure que personne ne lit
#      n'est pas une garde.
GRAVES = ("source_absents", "doublons", "hors_plage_app", "plage_envahie",
          "retraits_perdus", "doublure_perimee")


def _table_existe(conn: sqlite3.Connection, nom: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ?", (nom,)
    ).fetchone() is not None


def mesurer(conn: sqlite3.Connection) -> dict | None:
    if not _table_existe(conn, "app_relation"):
        return None

    lignes = conn.execute("SELECT COUNT(*) FROM app_relation").fetchone()[0]

    connus = set()
    doublons = 0
    hors_plage_app = 0
    plage_envahie = 0
    for contact, annonce, ident in conn.execute(
        "SELECT app_contact_id, hektor_annonce_id, app_relation_id FROM app_relation"
    ):
        cle = (int(contact), str(annonce))
        if cle in connus:
            doublons += 1
        connus.add(cle)
        if int(contact) < PLAGE_CONTACT_APP:
            hors_plage_app += 1
        if int(ident) >= PLAGE_RESERVEE_APP:
            plage_envahie += 1

    # ① LA CHAINE A-T-ELLE TOURNE ? Tout lien de la couche doit etre dans la
    #    table. S'il en manque, l'etape de nuit ne passe plus -- et le registre
    #    cesse d'etre complet sans rien dire.
    source_absents = None
    source_lus = None
    if _table_existe(conn, "app_contact_relation_current"):
        places = ",".join("?" for _ in ROLES_DU_BIEN)
        source_absents = 0
        source_lus = 0
        for contact, annonce in conn.execute(
            "SELECT hektor_contact_id, hektor_annonce_id FROM app_contact_relation_current"
            f" WHERE role_contact IN ({places})", ROLES_DU_BIEN
        ):
            brut = str(contact or "").strip()
            a = str(annonce or "").strip()
            if not brut.isdigit() or not a:
                continue
            source_lus += 1
            if (int(brut), a) not in connus:
                source_absents += 1

    # ② LE RETARD DU CLOUD -- INFORMATION, JAMAIS UNE ALERTE.
    #    Il porte les biens du parc ; la table porte tout. L'ecart disparaitra
    #    au rebranchement, et Frederic a tranche le 30/09 : TOUT MONTERA.
    retard_cloud = None
    if _table_existe(conn, "app_contact_relation_current__sb"):
        places = ",".join("?" for _ in ROLES_DU_BIEN)
        au_cloud = conn.execute(
            "SELECT COUNT(*) FROM app_contact_relation_current__sb"
            f" WHERE role_contact IN ({places})", ROLES_DU_BIEN
        ).fetchone()[0]
        retard_cloud = lignes - au_cloud

    # ─── ⑤ ET ⑥ : LE CONTRAT D'AUTORITE SUR `retire_le` ───────────────────────
    #   La doublure est le temoin local du cloud. Si elle manque, on ne MESURE pas,
    #   on le DIT -- None, jamais zero : « non mesure » et « rien a signaler » ne
    #   sont pas la meme chose, et les confondre est la panne la plus chere d'ici.
    retraits_perdus = None
    doublure_perimee = None
    doublure_du = None
    if _table_existe(conn, "app_relation__sb"):
        # ⑤ le cloud a un retrait, le serveur l'ignore -> le prochain push l'efface
        retraits_perdus = conn.execute(
            "SELECT COUNT(*) FROM app_relation__sb s"
            " WHERE s.retire_le IS NOT NULL"
            "   AND EXISTS (SELECT 1 FROM app_relation r"
            "                WHERE r.app_contact_id = s.app_contact_id"
            "                  AND r.hektor_annonce_id = s.hektor_annonce_id"
            "                  AND r.retire_le IS NULL)").fetchone()[0]
        # ⑥ la doublure est-elle du jour ? Sans ca, ⑤ vaut zero en mentant.
        ligne = conn.execute(
            "SELECT derniere_descente FROM sb_pull_state"
            " WHERE table_name = 'app_relation__sb'").fetchone()
        doublure_du = ligne[0] if ligne and ligne[0] else None
        if doublure_du:
            doublure_perimee = 0 if str(doublure_du)[:10] == date.today().isoformat() else 1

    comptes = {
        "lignes": lignes,
        "doublons": doublons,
        "hors_plage_app": hors_plage_app,
        "plage_envahie": plage_envahie,
        "source_absents": source_absents,
        "source_lus": source_lus,
        "retard_cloud": retard_cloud,
        "retraits_perdus": retraits_perdus,
        "doublure_perimee": doublure_perimee,
        "doublure_du": doublure_du,
        "marques_absents": conn.execute(
            "SELECT COUNT(*) FROM app_relation WHERE present_in_hektor = 0").fetchone()[0],
    }
    comptes["graves"] = sum(comptes[c] or 0 for c in GRAVES)
    return comptes


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    conn = sqlite3.connect(f"file:{BASE.as_posix()}?mode=ro", uri=True)
    try:
        m = mesurer(conn)
    finally:
        conn.close()
    if m is None:
        print("NON MESURABLE : app_relation manque -- ce n'est pas un zero")
        return 2
    print("UN LIEN NE DISPARAIT PAS")
    print("   liens au registre             : %s" % m["lignes"])
    print("   doublons sur la cle           : %s   (doit valoir 0)" % m["doublons"])
    print("   contacts hors plage app       : %s   (doit valoir 0)" % m["hors_plage_app"])
    print("   ids dans la plage de l'app    : %s   (doit valoir 0)" % m["plage_envahie"])
    if m["source_absents"] is None:
        print("   liens de la couche absents    : NON MESURE (couche absente)")
    else:
        print("   liens de la couche absents    : %s sur %s   (doit valoir 0)"
              % (m["source_absents"], m["source_lus"]))
    print("   marques sortis (CONSERVES)    : %s" % m["marques_absents"])
    print("")
    print("   -- le contrat d'autorite : retire_le appartient a l'APP --")
    if m["retraits_perdus"] is None:
        print("   retraits perdus               : NON MESURE (doublure absente)")
        print("   doublure du                   : NON MESUREE")
    else:
        print("   retraits perdus               : %s   (doit valoir 0)" % m["retraits_perdus"])
        print("   doublure du                   : %s%s"
              % (m["doublure_du"],
                 "   ⚠ PAS DU JOUR" if m["doublure_perimee"] else ""))
    print("")
    print("   -- information, jamais une alerte --")
    print("   retard du cloud               : %s" % m["retard_cloud"])
    print("      (le cloud porte les biens du parc, la table porte tout ;")
    print("       Frederic a tranche le 30/09 : tout montera)")
    if m["graves"]:
        print("")
        print("GRAVE : %s ecart(s) -- un lien ne disparait pas." % m["graves"])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
