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
          "retraits_perdus", "doublure_perimee", "registre_sans_mandant")


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
    ids_plage_app = []
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
            ids_plage_app.append(int(ident))

    # ⚠ 09/10/2026 -- UN NUMERO DANS LA PLAGE DE L'APP N'EST PLUS UNE AVARIE.
    #   Depuis le 30/09 le run ADOPTE le numero pose par l'app (relation_ledger lit
    #   app_relation__sb) au lieu d'en inventer un second : sans ca le push heurte
    #   l'index unique du couple et le run s'arrete. La premiere adoption a eu lieu
    #   le 09/10, et cette sentinelle serait passee au ROUGE pour une ligne saine.
    #   Reste une avarie : un numero de cette plage que la DOUBLURE ne connait pas
    #   -- celui-la, c'est le run qui l'a invente. Doublure absente : on recompte
    #   tout, on crie, on ne se tait pas.
    plage_envahie = len(ids_plage_app)
    if ids_plage_app and _table_existe(conn, "app_relation__sb"):
        places = ",".join("?" for _ in ids_plage_app)
        adoptes = {
            int(r[0]) for r in conn.execute(
                "SELECT app_relation_id FROM app_relation__sb"
                " WHERE app_relation_id IN (%s)" % places, ids_plage_app)
        }
        plage_envahie = sum(1 for i in ids_plage_app if i not in adoptes)

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

    # ─── ⑦ LE REGISTRE DES MANDATS SAIT-IL CE QUE LES LIENS SAVENT ? ─────────
    #   Signale par Frederic le 04/10 : des lignes du registre n'affichent AUCUN
    #   mandant alors que la fiche annonce et le registre des relations les ont.
    #   638 lignes sans mandant, dont 607 que NOS liens connaissent -- parce que
    #   `mandants_texte` etait la seule colonne du registre restee un TEXTE
    #   recopie de Hektor, sans repli quand Hektor se tait (bien vendu, archive).
    #   ⭐ CETTE GARDE VAUT 607 LE JOUR OU ELLE EST POSEE, ET DOIT VALOIR 0 DES
    #     LE PREMIER PUSH QUI SUIT LE PATCH. C'est elle qui dira que le correctif
    #     tient -- et, plus tard, que personne ne l'a defait.
    #   ⚠ LES DEUX CASTS NE SONT PAS DECORATIFS : `hektor_annonce_id` est un
    #     INTEGER au registre et un TEXT dans les liens. Sans eux la jointure est
    #     muette et la garde rend 0 EN MENTANT (mesure du 05/10 : 0 sans cast,
    #     607 avec). Meme famille que l'affinite qui a coute 79 minutes le 03/10.
    registre_sans_mandant = None
    registre_sans_mandant_total = None
    if _table_existe(conn, "app_mandat_register_current") and _table_existe(conn, "app_contact_current"):
        registre_sans_mandant_total = conn.execute(
            "SELECT COUNT(*) FROM app_mandat_register_current"
            " WHERE TRIM(COALESCE(mandants_texte, '')) = ''").fetchone()[0]
        registre_sans_mandant = conn.execute(
            "SELECT COUNT(*) FROM app_mandat_register_current g"
            " WHERE TRIM(COALESCE(g.mandants_texte, '')) = ''"
            "   AND EXISTS (SELECT 1 FROM app_relation r"
            "                 JOIN app_contact_current c"
            "                   ON c.hektor_contact_id = CAST(r.app_contact_id AS TEXT)"
            "                WHERE CAST(r.hektor_annonce_id AS TEXT) = CAST(g.hektor_annonce_id AS TEXT)"
            "                  AND r.retire_le IS NULL"
            "                  AND r.role_hektor IN ('mandant', 'proprietaire')"
            "                  AND TRIM(COALESCE(c.display_name, '')) <> '')").fetchone()[0]

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
        "registre_sans_mandant": registre_sans_mandant,
        "registre_sans_mandant_total": registre_sans_mandant_total,
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
    print("   -- le registre des mandats sait-il ce que les liens savent ? --")
    if m["registre_sans_mandant"] is None:
        print("   lignes sans mandant           : NON MESURE (registre absent)")
    else:
        print("   lignes sans mandant           : %s au total" % m["registre_sans_mandant_total"])
        print("      dont les liens les savent  : %s   (doit valoir 0)"
              % m["registre_sans_mandant"])
    print("")
    print("   -- information, jamais une alerte --")
    print("   retard du cloud               : %s" % m["retard_cloud"])
    print("      (le cloud porte les biens du parc, la table porte tout ;")
    print("       Frederic a tranche le 30/09 : tout montera)")
    if m["graves"]:
        print("")
        # ⚠ Le total melange DEUX familles depuis le 05/10 : les liens perdus et
        #   les lignes du registre qui ignorent un mandant connu. Le detail
        #   au-dessus dit laquelle a bouge ; ce total dit seulement « regarde ».
        print("GRAVE : %s ecart(s) -- voir le detail ci-dessus." % m["graves"])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
