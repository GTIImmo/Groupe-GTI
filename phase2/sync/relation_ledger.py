# -*- coding: utf-8 -*-
"""LE REGISTRE DES LIENS, CHEZ NOUS. LOCAL, DORMANT.            30/09/2026

CE QUE C'EST
------------
L'equivalent de `app_mandat` (fait le matin meme) et de `app_affaire_ledger`,
pour les LIENS entre une personne et un bien. Une table DURABLE, que rien ne
vide, ou chaque lien a SA ligne et SON numero.

POURQUOI ELLE MANQUE, ET CE QU'ON PERD SANS ELLE
------------------------------------------------
`app_contact_relation_current` n'est pas un registre : elle est EFFACEE ET
REFAITE CHAQUE NUIT depuis six fenetres de Hektor. Le lien n'existe chez nous
que parce que Hektor l'a dit cette nuit-la.

    « Un lien nait toujours chez Hektor. Le jour de la coupure, plus rien
      n'arrive. »  -- audit du 30/09, et le plan l'ecrivait deja le 03/09 :
    « ce patron meurt a la coupure ».

Consequence mesurable aujourd'hui : un bien qui sort du parc emporte ses liens
hors du cloud. 86 168 liens sont dans ce cas -- dont 49 942 mandants et 32 444
proprietaires. Le jour ou un bien se vend, ON NE SAIT PLUS QUI EN ETAIT LE
MANDANT.

CE QU'ELLE PORTE, ET CE QU'ELLE NE PORTE PAS
---------------------------------------------
    mandant · proprietaire     132 622 liens      -> ELLE LES PORTE
    acquereur (3 types)         34 925 liens      -> ELLE NE LES PORTE PAS

⚠ LES ACQUEREURS NE SE RECOPIENT PAS, C'EST UNE DECISION. Un acquereur n'est
  pas un lien au bien : il existe PARCE QU'IL A FAIT UNE OFFRE. Ce fait est
  deja tenu chez nous, durablement et a deux robinets, dans app_affaire_ledger
  (30 352 affaires portent app_contact_id, toutes dans la plage de l'app). Les
  34 925 lignes « acquereur » du miroir sont une SECONDE COPIE. Le registre les
  PROJETTERA depuis le ledger ; il ne les stockera pas. Deux copies finissent
  toujours par dire deux choses -- c'est exactement ce qui est arrive au
  registre des mandats, qui a menti pendant deux mois.

LE FAIT BRUT, PAS LE LIBELLE
-----------------------------
Hektor ne connait qu'UN fait : « proprietaire du bien ». Le build reecrit le
role APRES le calcul de la cle -- `mandant` si l'annonce a un numero de mandat,
`proprietaire` sinon (build_contacts_layer.py:1337). On stocke donc LE FAIT, et
le libelle se DERIVE a l'affichage. Sinon chaque mandat signe changerait
l'identite du lien.

⭐ ET LA MESURE DONNE RAISON A CE CHOIX : sur 132 622 couples (contact, bien),
   ZERO ne porte les deux roles. Ce sont deja deux noms d'une meme chose.
   (J'avais annonce « 117 022 liens a dedoublonner » : c'etait faux, il n'y a
    AUCUN doublon. 74 166 + 58 456 = 132 622 = le nombre de couples distincts.)

LES TROIS REGLES COPIEES DES REGISTRES QUI MARCHENT
-----------------------------------------------------
1. DEUX DISTRIBUTEURS, DEUX PLAGES, QUI NE SE CROISENT JAMAIS.
   Le run prend `MAX(id) WHERE id < PLAGE_RESERVEE_APP`, JAMAIS le MAX global.
   C'est la ligne exacte qui a coute cinq jours en aout cote affaires.
2. ON NE RENUMEROTE JAMAIS UNE LIGNE CONNUE.
   `app_relation_id` est absent du ON CONFLICT DO UPDATE.
3. DELETE-NEVER. Un lien que le miroir ne montre plus est MARQUE, jamais
   supprime -- `present_in_hektor = 0` et `absent_depuis`.

LA CLE, ET SA LIMITE, DITE FRANCHEMENT
---------------------------------------
    UNIQUE (app_contact_id, hektor_annonce_id)

app_contact_id est rempli a 100 % (0 numero hors plage app sur 132 622), et
hektor_annonce_id est toujours la puisque le lien vient de Hektor. C'est le
meme montage que app_mandat : la cle technique porte la reference Hektor dont
les workers ont besoin, et NOTRE numero de bien (`app_dossier_id`) est porte a
cote, comme identite.

⚠ SA LIMITE : le jour ou l'app creera un lien sur une annonce NEE DANS L'APP,
  il n'y aura pas de hektor_annonce_id. Il faudra alors basculer la cle sur
  (app_contact_id, app_dossier_id). Ce n'est PAS un probleme aujourd'hui -- rien
  n'ecrit encore dans cette table -- mais ce sera le premier geste de l'etape
  « le worker ecrit ». C'est ecrit ici pour ne pas le redecouvrir.

⚠ ET NEUF LIGNES N'ONT PAS DE app_dossier_id : leur annonce n'existe NI dans le
  miroir NI chez nous (toutes venues de `api_contact_detail_annonces`). On les
  GARDE -- un registre ne jette pas ce qu'il ne sait pas ranger -- et le
  controle les compte a part.

CE QUE CE SCRIPT FAIT, ET NE FAIT PAS
--------------------------------------
Il LIT `app_contact_relation_current` (le resultat des six fenetres) et remplit
`app_relation` en local. Il n'ecrit PAS dans Supabase, n'appelle PAS Hektor, ne
touche a RIEN d'existant. Il est DORMANT : rien ne le lance, rien ne le lit.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"

TABLE = "app_relation"

# La moitie haute est RESERVEE aux liens nes dans l'app. Meme valeur et meme
# role que pour le mandat, l'affaire et le dossier.
PLAGE_RESERVEE_APP = 1_000_000

# Les deux libelles que Hektor donne a UN SEUL fait : « proprietaire du bien ».
ROLES_DU_BIEN = ("mandant", "proprietaire")

for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


SCHEMA = """
CREATE TABLE IF NOT EXISTS app_relation (
    app_relation_id      INTEGER PRIMARY KEY,
    -- NOTRE identite des deux cotes du lien.
    app_contact_id       INTEGER NOT NULL,
    app_dossier_id       INTEGER,
    -- La reference Hektor, gardee pour les workers -- meme montage que
    -- app_mandat. Elle sert aussi de cle technique tant que tout lien nait
    -- chez Hektor (voir « LA CLE, ET SA LIMITE » en tete).
    hektor_annonce_id    TEXT NOT NULL,
    -- ⚠ LE FAIT BRUT, PAS LE LIBELLE. Hektor ne connait que « proprietaire du
    --   bien » ; `mandant` et `proprietaire` sont deux affichages du meme fait,
    --   choisis selon que l'annonce porte un numero de mandat. Mesure du 30/09 :
    --   sur 132 622 couples, ZERO ne porte les deux roles.
    --   On stocke le fait ; le libelle se derive a l'ecran.
    fait                 TEXT NOT NULL DEFAULT 'proprietaire_du_bien',
    -- Ce que Hektor en disait au dernier passage -- INFORMATION, pas identite.
    role_hektor          TEXT,
    -- Laquelle des six fenetres l'a montre en dernier.
    source               TEXT,
    -- Le hache actuel (relation_key), garde EN DOUBLURE le temps de la
    -- transition : c'est lui que le carnet C.9-d connait.
    relation_key         TEXT,
    first_seen_at        TEXT,
    last_seen_at         TEXT,
    -- delete-never : marque, jamais supprime.
    present_in_hektor    INTEGER NOT NULL DEFAULT 1,
    absent_depuis        TEXT,
    UNIQUE (app_contact_id, hektor_annonce_id)
);
CREATE INDEX IF NOT EXISTS idx_app_relation_contact ON app_relation (app_contact_id);
CREATE INDEX IF NOT EXISTS idx_app_relation_dossier ON app_relation (app_dossier_id);
CREATE INDEX IF NOT EXISTS idx_app_relation_annonce ON app_relation (hektor_annonce_id);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _open_local() -> sqlite3.Connection:
    con = sqlite3.connect(PHASE2_DB)
    con.row_factory = sqlite3.Row
    # busy_timeout : phase2 a PLUSIEURS ecrivains. Les 5 s par defaut ont deja
    # tue un rattrapage entier.
    con.execute("PRAGMA busy_timeout = 60000")
    return con


def refresh(con: sqlite3.Connection, full: bool = True) -> dict:
    con.executescript(SCHEMA)
    vu = now_iso()

    # LE DISTRIBUTEUR. On ignore la moitie haute -- voir la regle 1 en tete.
    prochain = (con.execute(
        "SELECT COALESCE(MAX(app_relation_id), 0) FROM app_relation WHERE app_relation_id < ?",
        (PLAGE_RESERVEE_APP,),
    ).fetchone()[0]) + 1

    connus = {(int(r["app_contact_id"]), str(r["hektor_annonce_id"]))
              for r in con.execute(
                  "SELECT app_contact_id, hektor_annonce_id FROM app_relation")}

    places = ",".join("?" for _ in ROLES_DU_BIEN)
    lignes = con.execute(
        "SELECT hektor_contact_id, hektor_annonce_id, app_dossier_id, role_contact,"
        "       relation_source, relation_key"
        "  FROM app_contact_relation_current"
        f" WHERE role_contact IN ({places})", ROLES_DU_BIEN
    ).fetchall()

    lus = neufs = revus = ecartes = sans_bien = 0
    vus_ce_run: list[tuple[int, str]] = []

    for r in lignes:
        lus += 1
        brut = str(r["hektor_contact_id"] or "").strip()
        annonce = str(r["hektor_annonce_id"] or "").strip()
        # ⚠ LE GARDE-FOU QUI COMPTE. Depuis la bascule du 23/09, cette colonne
        #   ne contient QUE des numeros d'app (mesure du 30/09 : 167 547 sur
        #   167 547). Un numero hors plage voudrait dire que la substitution
        #   n'a pas eu lieu -- on ECARTE et on le DIT, plutot que de ranger un
        #   numero Hektor dans une colonne qui s'appelle app_contact_id.
        if not brut.isdigit() or int(brut) < 10_000_000 or not annonce:
            ecartes += 1
            continue
        contact = int(brut)
        dossier = r["app_dossier_id"]
        if dossier is None:
            sans_bien += 1

        cle = (contact, annonce)
        if cle in connus:
            identifiant = None
            revus += 1
        else:
            identifiant = prochain
            prochain += 1
            connus.add(cle)
            neufs += 1
        vus_ce_run.append(cle)

        con.execute(
            """
            INSERT INTO app_relation(app_relation_id, app_contact_id, app_dossier_id,
                hektor_annonce_id, fait, role_hektor, source, relation_key,
                first_seen_at, last_seen_at, present_in_hektor, absent_depuis)
            VALUES (?, ?, ?, ?, 'proprietaire_du_bien', ?, ?, ?, ?, ?, 1, NULL)
            ON CONFLICT(app_contact_id, hektor_annonce_id) DO UPDATE SET
                app_dossier_id=COALESCE(excluded.app_dossier_id, app_relation.app_dossier_id),
                role_hektor=excluded.role_hektor,
                source=excluded.source,
                relation_key=excluded.relation_key,
                last_seen_at=excluded.last_seen_at,
                present_in_hektor=1,
                absent_depuis=NULL
            """,
            (identifiant, contact, dossier, annonce,
             r["role_contact"], r["relation_source"], r["relation_key"], vu, vu),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # delete-never : ce que le miroir ne montre plus est MARQUE, jamais efface.
    #
    # ⚠⚠ CETTE ETAPE A ETE REECRITE LE 30/09, APRES UN INCIDENT QUE J'AI CAUSE.
    #   Ma premiere version posait les cles vues dans une table temporaire SANS
    #   INDEX, puis faisait un `UPDATE ... WHERE NOT EXISTS (SELECT ... FROM
    #   _vus_rel ...)`. SQLite parcourait donc les ~132 000 lignes de la table
    #   temporaire POUR CHACUNE des ~132 000 lignes du registre :
    #   17 milliards de comparaisons.
    #   RESULTAT MESURE : 8 min 30 de processeur a 100 %, ET UN VERROU
    #   D'ECRITURE TENU SUR phase2.sqlite PENDANT TOUT CE TEMPS -- pendant
    #   lequel les autres ecrivains (rafraichissement d'un contact a
    #   l'ouverture de sa fiche, worker) attendent puis abandonnent.
    #   Le processus a ete coupe avant le commit : zero ligne ecrite, huit
    #   minutes de base bloquee pour rien.
    #
    # LA REPARATION N'EST PAS UN INDEX, C'EST DE NE PLUS DEMANDER CE CALCUL A
    # SQLite. Les deux ensembles sont deja en memoire : la difference se fait
    # en Python, en une passe, et l'UPDATE ne touche QUE les lignes concernees
    # -- zero en regime normal. Le verrou dure des millisecondes.
    # ══════════════════════════════════════════════════════════════════════════
    sortis = 0
    if full and vus_ce_run:
        vus = set(vus_ce_run)
        a_marquer = [
            (int(r["app_contact_id"]), str(r["hektor_annonce_id"]))
            for r in con.execute(
                "SELECT app_contact_id, hektor_annonce_id FROM app_relation"
                " WHERE present_in_hektor = 1")
            if (int(r["app_contact_id"]), str(r["hektor_annonce_id"])) not in vus
        ]
        if a_marquer:
            con.executemany(
                "UPDATE app_relation SET present_in_hektor = 0,"
                "       absent_depuis = COALESCE(absent_depuis, ?)"
                " WHERE app_contact_id = ? AND hektor_annonce_id = ?",
                [(vu, c, a) for c, a in a_marquer])
        sortis = len(a_marquer)

    con.commit()
    return {"lus": lus, "neufs": neufs, "revus": revus, "ecartes": ecartes,
            "sans_notre_numero_de_bien": sans_bien, "sortis_du_miroir": sortis}


def controle(con: sqlite3.Connection) -> None:
    q = lambda s: con.execute(s).fetchone()[0]   # noqa: E731
    print("")
    print("CONTROLES")
    print("   lignes                              : %s" % q("SELECT COUNT(*) FROM app_relation"))
    print("   contacts distincts                  : %s" % q("SELECT COUNT(DISTINCT app_contact_id) FROM app_relation"))
    print("   biens distincts                     : %s" % q("SELECT COUNT(DISTINCT hektor_annonce_id) FROM app_relation"))
    print("   avec NOTRE numero de bien           : %s" % q("SELECT COUNT(*) FROM app_relation WHERE app_dossier_id IS NOT NULL"))
    print("   SANS notre numero de bien           : %s   (leur annonce n'existe nulle part)"
          % q("SELECT COUNT(*) FROM app_relation WHERE app_dossier_id IS NULL"))
    print("   sortis du miroir (CONSERVES)        : %s" % q("SELECT COUNT(*) FROM app_relation WHERE present_in_hektor = 0"))
    for role, n in con.execute("SELECT role_hektor, COUNT(*) FROM app_relation GROUP BY 1 ORDER BY 2 DESC"):
        print("      dernier libelle Hektor %-12s %s" % (role, n))
    print("")
    doublons = q("SELECT COUNT(*) FROM (SELECT 1 FROM app_relation"
                 " GROUP BY app_contact_id, hektor_annonce_id HAVING COUNT(*) > 1)")
    print("   doublons sur la cle                 : %s   (doit valoir 0)" % doublons)
    hors = q("SELECT COUNT(*) FROM app_relation WHERE app_contact_id < 10000000")
    print("   numeros de contact hors plage app   : %s   (doit valoir 0)" % hors)
    envahis = q("SELECT COUNT(*) FROM app_relation WHERE app_relation_id >= %d" % PLAGE_RESERVEE_APP)
    print("   DANS LA PLAGE RESERVEE A L'APP      : %s   (doit valoir 0)" % envahis)
    if envahis:
        print("   >> L'ALLOCATEUR EST FAUX. C'est le defaut d'aout, a l'identique.")

    # CE QUE LA TABLE GAGNE SUR LE CLOUD D'AUJOURD'HUI.
    try:
        cloud = q("SELECT COUNT(*) FROM app_contact_relation_current__sb"
                  " WHERE role_contact IN ('mandant','proprietaire')")
        print("")
        print("   le CLOUD en porte aujourd'hui       : %s" % cloud)
        print("   la TABLE en porte                   : %s" % q("SELECT COUNT(*) FROM app_relation"))
        print("      -> ce qu'un bien vendu emportait  : %s liens"
              % (q("SELECT COUNT(*) FROM app_relation") - cloud))
    except sqlite3.OperationalError:
        print("   (doublure absente : comparaison au cloud impossible)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Le registre des liens, en local. DORMANT.")
    parser.add_argument("--refresh", action="store_true", help="Remplit la table depuis la couche des liens.")
    parser.add_argument("--controle", action="store_true", help="Affiche les controles, sans rien ecrire.")
    parser.add_argument("--partiel", action="store_true",
                        help="N'applique pas present_in_hektor=0 aux lignes non revues.")
    args = parser.parse_args()
    if not args.refresh and not args.controle:
        parser.error("choisir --refresh ou --controle")

    con = _open_local()
    try:
        if args.refresh:
            bilan = refresh(con, full=not args.partiel)
            print("REFRESH app_relation")
            for k in ("lus", "neufs", "revus", "ecartes",
                      "sans_notre_numero_de_bien", "sortis_du_miroir"):
                print("   %-28s : %s" % (k, bilan[k]))
        else:
            con.executescript(SCHEMA)
        controle(con)
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
