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
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase2.sync.push_upgrade_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES,
    SupabaseRestClient,
    load_env_files,
)

import os  # noqa: E402

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
    -- ⚠⚠ LE NUMERO HEKTOR DE LA PERSONNE -- trouve manquant par Frederic le 30/09.
    --   « Est-ce que mon registre des liens genere bien deux numeros, celui de
    --     Hektor et celui de mon app, pour anticiper la coupure ? »
    --   Il avait raison : un lien nomme DEUX objets, il faut donc QUATRE numeros.
    --   On avait les deux du bien et un seul de la personne.
    --   Les autres registres, eux, les portent tous (app_affaire_ledger a
    --   hektor_acquereur_id ; app_mandat a hektor_mandat_id).
    -- A QUOI IL SERT : a PARLER a Hektor de cette personne -- « retire M. X des
    --   mandants de ce bien ». Notre numero ne lui dit rien.
    -- ⚠ ET IL PERIME : le run le voit chaque nuit dans le miroir et le jette.
    --   Apres la coupure, plus personne ne pourra le donner.
    hektor_contact_id    TEXT,
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
    -- « HEKTOR NE LE MONTRE PLUS » -- le miroir ne l'a pas ramene ce coup-ci.
    present_in_hektor    INTEGER NOT NULL DEFAULT 1,
    absent_depuis        TEXT,
    -- ⚠⚠ « ON L'A SUPPRIME » -- ET CE N'EST PAS LA MEME CHOSE. Distinction posee
    --   le 30/09 apres un trou que j'avais ouvert le matin meme : quatre chemins
    --   effacent un lien (le worker quand une annonce ou un contact est
    --   supprime, et delete_local_annonce / delete_local_contact cote serveur)
    --   et AUCUN ne connaissait cette table. Ma vue les aurait affiches.
    --   `delete-never` protege contre un miroir qui se tait. Il ne doit PAS
    --   proteger contre une suppression VOULUE par un negociateur.
    -- DORMANTES pour l'instant : la vue exclut deja `present_in_hektor = 0`,
    -- ce qui ferme le trou des le run suivant. Ces colonnes serviront a fermer
    -- la FENETRE (jusqu'a 19 h entre le geste et le run), quand les quatre
    -- chemins les ecriront.
    retire_le            TEXT,
    retire_par           TEXT,
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


def _ajouter_colonne_si_absente(con: sqlite3.Connection, nom: str, type_sql: str) -> None:
    """SQLite n'a pas ADD COLUMN IF NOT EXISTS, et CREATE TABLE IF NOT EXISTS ne
    donne RIEN a une table qui existe deja -- pas meme une colonne neuve."""
    colonnes = {r[1] for r in con.execute("PRAGMA table_info(app_relation)")}
    if nom not in colonnes:
        con.execute("ALTER TABLE app_relation ADD COLUMN %s %s" % (nom, type_sql))


def refresh(con: sqlite3.Connection, full: bool = True) -> dict:
    con.executescript(SCHEMA)
    _ajouter_colonne_si_absente(con, "hektor_contact_id", "TEXT")
    _ajouter_colonne_si_absente(con, "retire_le", "TEXT")
    _ajouter_colonne_si_absente(con, "retire_par", "TEXT")
    vu = now_iso()

    # LE DISTRIBUTEUR. On ignore la moitie haute -- voir la regle 1 en tete.
    prochain = (con.execute(
        "SELECT COALESCE(MAX(app_relation_id), 0) FROM app_relation WHERE app_relation_id < ?",
        (PLAGE_RESERVEE_APP,),
    ).fetchone()[0]) + 1

    # ══════════════════════════════════════════════════════════════════════════
    # LA CORRESPONDANCE COMPLETE -- ET ELLE N'EST PAS OU JE LA CHERCHAIS.
    #
    # J'ai d'abord pris `app_contact_identite_app` (62 038 lignes) et conclu que
    # « 50 982 contacts sur 96 070 ne sont plus traduisibles ». FAUX : cette
    # table est le JOURNAL DE LA BASCULE, pas la correspondance.
    # La correspondance vit dans app_contact_current, cote SERVEUR : 356 270
    # contacts, dont `hektor_contact_id` porte NOTRE numero (tous >= 10 000 000)
    # et `hektor_target_id` celui de HEKTOR (tous < 10 000 000).
    # Mesure du 30/09 : 96 070 sur 96 070 traduisibles -- 100 %.
    # ➡ LECON : avant de conclure a une perte, verifier qu'on a interroge LA
    #   BONNE TABLE. Une absence mesuree sur la mauvaise source n'est pas une
    #   absence, c'est une erreur de lecture.
    # ══════════════════════════════════════════════════════════════════════════
    # NOTRE numero de bien, pour les lignes qui n'arrivent pas par la couche
    # (celle-ci le porte deja). Meme lecture que mandat_ledger.
    dossiers: dict[str, int] = {}
    try:
        for r in con.execute(
            "SELECT id, hektor_annonce_id FROM app_dossier WHERE hektor_annonce_id IS NOT NULL"
        ):
            dossiers[str(r["hektor_annonce_id"])] = r["id"]
    except sqlite3.OperationalError:
        pass

    numero_hektor: dict[int, str] = {}
    try:
        for r in con.execute(
            "SELECT hektor_contact_id, hektor_target_id FROM app_contact_current"
            " WHERE hektor_target_id IS NOT NULL"
        ):
            notre = str(r["hektor_contact_id"] or "").strip()
            chez_lui = str(r["hektor_target_id"] or "").strip()
            if notre.isdigit() and chez_lui:
                numero_hektor[int(notre)] = chez_lui
    except sqlite3.OperationalError:
        pass

    connus = {(int(r["app_contact_id"]), str(r["hektor_annonce_id"]))
              for r in con.execute(
                  "SELECT app_contact_id, hektor_annonce_id FROM app_relation")}

    # ══════════════════════════════════════════════════════════════════════════
    # L'ADOPTION -- ET SANS ELLE, LE PUSH S'ARRETERAIT
    #
    # Quand l'app rattache un mandant, sa RPC pose la ligne durable TOUT DE
    # SUITE, avec un numero de la plage haute (>= 1 000 000). Le miroir ne la
    # connait pas encore. Au run suivant, Hektor redescend le lien : ce script
    # verrait un couple INCONNU, lui donnerait un numero de la serie LOCALE, et
    # le push tenterait une deuxieme ligne pour le meme couple -> violation de
    # app_relation_couple_unique.
    #
    # ⚠ ET LE DEGAT NE SERAIT PAS LE CONFLIT, CE SERAIT L'ARRET. Les 01 et
    #   02/09/2026, deux nuits de suite, le push du ledger d'affaires a heurte un
    #   index unique et LE RUN S'EST ARRETE LA -- dix-huit heures de retard sans
    #   que rien ne le dise.
    #
    # ON ADOPTE DONC : si la doublure porte deja ce couple, on reprend SON
    # numero. C'est le serveur qui s'aligne sur le cloud, jamais l'inverse.
    # ══════════════════════════════════════════════════════════════════════════
    adoptes: dict[tuple[int, str], int] = {}
    try:
        for r in con.execute(
            "SELECT app_relation_id, app_contact_id, hektor_annonce_id"
            "  FROM app_relation__sb WHERE app_relation_id >= ?",
            (PLAGE_RESERVEE_APP,)
        ):
            cle_sb = (int(r["app_contact_id"]), str(r["hektor_annonce_id"] or "").strip())
            if cle_sb[1] and cle_sb not in connus:
                adoptes[cle_sb] = int(r["app_relation_id"])
    except (sqlite3.OperationalError, TypeError, ValueError):
        # La doublure n'a jamais ete descendue, ou elle est vide. On ne devine
        # pas -- et tant que rien n'ecrit depuis l'app, il n'y a rien a adopter.
        pass
    adoptes_au_depart = len(adoptes)

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
        elif cle in adoptes:
            # NE DANS L'APP : on reprend son numero, on n'en fabrique pas un autre.
            identifiant = adoptes.pop(cle)
            connus.add(cle)
            neufs += 1
        else:
            identifiant = prochain
            prochain += 1
            connus.add(cle)
            neufs += 1
        vus_ce_run.append(cle)

        con.execute(
            """
            INSERT INTO app_relation(app_relation_id, app_contact_id, app_dossier_id,
                hektor_annonce_id, hektor_contact_id, fait, role_hektor, source,
                relation_key, first_seen_at, last_seen_at, present_in_hektor, absent_depuis)
            VALUES (?, ?, ?, ?, ?, 'proprietaire_du_bien', ?, ?, ?, ?, ?, 1, NULL)
            ON CONFLICT(app_contact_id, hektor_annonce_id) DO UPDATE SET
                app_dossier_id=COALESCE(excluded.app_dossier_id, app_relation.app_dossier_id),
                -- on COMBLE, on n'ecrase jamais : si on l'avait deja, on le garde
                hektor_contact_id=COALESCE(app_relation.hektor_contact_id, excluded.hektor_contact_id),
                role_hektor=excluded.role_hektor,
                source=excluded.source,
                relation_key=excluded.relation_key,
                last_seen_at=excluded.last_seen_at,
                present_in_hektor=1,
                absent_depuis=NULL
            """,
            (identifiant, contact, dossier, annonce, numero_hektor.get(contact),
             r["role_contact"], r["relation_source"], r["relation_key"], vu, vu),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # ══════════════════════════════════════════════════════════════════════════
    # 2e SOURCE -- CE QUE L'APP TIENT ET QUE LE MIROIR IGNORE
    #
    # `app_relation_app_seule` est le FILET pose le 21/09 (26bis-RELATIONS) : il
    # recense les liens que Supabase porte et que le serveur ne connait pas. Sa
    # note dit elle-meme qu'ils ne sont « JAMAIS REINJECTES » -- il observait,
    # faute d'une table durable ou les verser. Elle existe maintenant.
    #
    # MESURE DU 30/09 : 45 lignes, dont 11 VIVANTES (les 34 autres ont disparu
    # de Supabase aussi, et gardent leur `absent_depuis`). Sur ces 11 :
    #     leur contact existe cote serveur        11 / 11
    #     leur annonce existe au miroir           11 / 11
    #     elles sont absentes de app_relation     11 / 11
    #     ET 3 SONT APPARUES LE 30/09 -- ce n'est pas du vieux bruit, c'est vivant.
    #
    # ⚠ LEUR `hektor_contact_id` PORTE DEJA NOTRE NUMERO (>= 10 000 000). Le nom
    #   de la colonne ment, comme partout depuis la bascule du 23/09. On ne
    #   traduit donc pas : on verifie la plage, et on ecarte ce qui n'y est pas.
    #
    # ⚠ DO NOTHING : la 1re source (la couche) est plus riche. Ce filet ne fait
    #   que COMBLER -- il ne reecrit jamais une ligne connue.
    #
    # ⚠ present_in_hektor = 0 : par definition, le miroir ne les montre pas.
    #   La vue ne les affichera donc pas encore -- mais le registre les GARDE,
    #   et c'est tout ce qu'on lui demande. Le jour ou Hektor les redescend, la
    #   1re source les reprend et les passe a 1.
    # ══════════════════════════════════════════════════════════════════════════
    depuis_app_seule = 0
    illisibles = 0
    try:
        lignes_app = con.execute(
            "SELECT hektor_contact_id, hektor_annonce_id, donnees_json"
            "  FROM app_relation_app_seule WHERE absent_depuis IS NULL").fetchall()
    except sqlite3.OperationalError:
        lignes_app = []
    for r in lignes_app:
        brut = str(r["hektor_contact_id"] or "").strip()
        annonce = str(r["hektor_annonce_id"] or "").strip()
        if not brut.isdigit() or int(brut) < 10_000_000 or not annonce:
            ecartes += 1
            continue
        contact = int(brut)
        cle = (contact, annonce)
        vus_ce_run.append(cle)
        if cle in connus:
            continue
        # ⚠ ON NE GOBE PLUS L'ERREUR EN SILENCE. Ma premiere version faisait
        #   `except Exception: donnees = {}` -- et `json` n'etait pas importe.
        #   Le NameError a ete avale, les 6 lignes sont parties SANS leur role
        #   ni leur cle, et RIEN NE L'A DIT. C'est la faute meme que j'avais
        #   notee en memoire le matin : « compter ce qu'on ecarte, toujours ».
        try:
            donnees = json.loads(r["donnees_json"] or "{}")
        except (ValueError, TypeError):
            donnees = {}
            illisibles += 1
        identifiant = adoptes.pop(cle) if cle in adoptes else prochain
        if cle not in adoptes and identifiant == prochain:
            prochain += 1
        connus.add(cle)
        depuis_app_seule += 1
        con.execute(
            """
            INSERT INTO app_relation(app_relation_id, app_contact_id, app_dossier_id,
                hektor_annonce_id, hektor_contact_id, fait, role_hektor, source,
                relation_key, first_seen_at, last_seen_at, present_in_hektor, absent_depuis)
            VALUES (?, ?, ?, ?, ?, 'proprietaire_du_bien', ?, 'app_seule', ?, ?, ?, 0, NULL)
            ON CONFLICT(app_contact_id, hektor_annonce_id) DO NOTHING
            """,
            (identifiant, contact, dossiers.get(annonce),
             annonce, numero_hektor.get(contact),
             donnees.get("role_contact"), donnees.get("relation_key"), vu, vu),
        )

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

    # ══════════════════════════════════════════════════════════════════════════
    # LES RETRAITS DECIDES DANS L'APP                              02/10/2026
    #
    # Decision de Frederic du 30/09 : « retirer un mandant PART chez Hektor et la
    # ligne RESTE chez nous, datee ». Les colonnes retire_le / retire_par existent
    # depuis ce jour-la, et le push les ENVOIE -- mais rien ne les lisait jamais.
    #
    # SANS CE BLOC, voici ce qui arriverait le jour ou le geste existera :
    #   lundi 14:00   l'app note le retrait dans le cloud. Le lien disparait de
    #                 l'ecran, car la vue filtre dessus :
    #                 WHERE (r.present_in_hektor AND (r.retire_le IS NULL))
    #   mardi 07:00   le serveur reconstruit depuis LE MIROIR HEKTOR, qui ignore
    #                 le retrait -- il ne peut pas l'inventer
    #   mardi 07:01   il POUSSE sa liste entiere, retire_le = NULL compris
    #                 ⛔ LE LIEN REAPPARAIT, et le run dit « reussi »
    #
    # ON LIT DONC LA DOUBLURE, et c'est un CHOIX, discute avec Frederic le 02/10 :
    #   · la doublure est le temoin local du cloud -> on reste sur la regle du
    #     projet « chercher d'abord en LOCAL, le miroir garde tout »
    #   · une lecture reseau depuis le run a ete ecartee : elle marchait, mais elle
    #     ajoutait une dependance au cloud dans le run de nuit
    #
    # ⚠⚠ ELLE N'EST FRAICHE QUE SI ON LA RAFRAICHIT AVANT. Mesure du 02/10 :
    #        07:00:14 -> 07:01:00   relation_ledger --refresh --push
    #        08:00:03               app_relation__sb rafraichie par la descente
    #     Le push passe AVANT : la doublure a donc ~23 h de retard, et un retrait
    #     d'hier apres-midi serait invisible. D'ou l'etape de run qui precede
    #     celle-ci :  pull_from_supabase.py --table app_relation
    #     ⛔ SANS CETTE ETAPE, CE BLOC NE VOIT RIEN. Le bilan le DIT
    #       (doublure_du / retards_possibles) au lieu de se taire.
    #
    # ⚠ ON POSE, ON NE RETIRE PAS -- delibere.
    #   « On comble, on n'ecrase jamais » (la regle de hektor_contact_id) serait
    #   FAUSSE ici : un retrait est un etat REVERSIBLE, pas une identite -- retirer
    #   puis RATTACHER laisserait le lien cache pour toujours.
    #   Mais l'inverse est pire : effacer un retrait a tort fait REAPPARAITRE un
    #   lien a l'ecran. Tant que le rattachement n'existe pas dans le front, on
    #   AJOUTE ce que la doublure affirme et on COMPTE les divergences sans y
    #   toucher. Le complement se posera ICI, avec de vraies donnees pour l'eprouver.
    retraits_poses = 0
    retraits_divergents = 0
    retraits_leves = 0
    doublure_du = None
    try:
        doublure_du = con.execute(
            "SELECT derniere_descente FROM sb_pull_state"
            " WHERE table_name = 'app_relation__sb'").fetchone()
        doublure_du = doublure_du[0] if doublure_du else None

        # ══════════════════════════════════════════════════════════════════════
        # ⭐ 5e (08/10/2026) -- LA SYMETRIE QUI MANQUAIT : EFFACER UN RETRAIT LEVE
        # ══════════════════════════════════════════════════════════════════════
        # CE BLOC ETAIT ANNONCE ICI MEME, et sa condition est remplie :
        #   « Tant que le rattachement n'existe pas dans le front, on AJOUTE ce que
        #     la doublure affirme [...]. Le complement se posera ICI, avec de vraies
        #     donnees pour l'eprouver. »
        #   Le rattachement existe dans l'ecran depuis le 03/10 -- joue en reel le
        #   08/10. Sans ce bloc, la RPC a beau effacer le retrait au clic : le
        #   serveur garde l'ancien et LE REPOUSSE des le lendemain, le mandant
        #   redisparait. A NE JAMAIS SEPARER du patch
        #   supabase/patch_5e_rattacher_apres_retrait_2026-10-08.sql.
        #
        # ⚠ LA REGLE QUI AUTORISE CE BLOC : `retire_le` / `retire_par` APPARTIENNENT
        #   A L'APP (relation_disparue.py l. 77). Le miroir Hektor ne peut pas les
        #   produire -- Hektor se contente de ne plus montrer le lien. Le cloud fait
        #   donc autorite, et le serveur s'y aligne DANS LES DEUX SENS.
        #
        # ⚠ GARDE DE FRAICHEUR, la meme que la sentinelle ⑥ : si la doublure n'est
        #   pas DU JOUR, on ne leve RIEN. Lever depuis une copie d'hier ferait
        #   REAPPARAITRE un lien retire hier apres-midi -- l'erreur inverse, et plus
        #   grave. On s'abstient, et on le DIT.
        #
        # ⚠ ON PILOTE DEPUIS LA PETITE TABLE (les retraits LOCAUX : 3 lignes au
        #   08/10), jamais depuis les 132 713 liens -- la lecon des 79 minutes du
        #   03/10.
        #
        # ⚠ ON N'EFFACE QUE CE QUE LA DOUBLURE CONTREDIT EXPLICITEMENT : le couple
        #   doit ETRE dans la doublure ET y porter `retire_le IS NULL`. Un couple
        #   absent ne prouve rien -- on le laisse.
        if doublure_du and str(doublure_du)[:10] == datetime.now().date().isoformat():
            con.execute("DROP TABLE IF EXISTS temp.retraits_locaux")
            con.execute(
                "CREATE TEMP TABLE retraits_locaux AS"
                " SELECT app_contact_id, hektor_annonce_id FROM app_relation"
                "  WHERE retire_le IS NOT NULL")
            con.execute("CREATE INDEX temp.idx_retraits_locaux"
                        " ON retraits_locaux (app_contact_id, hektor_annonce_id)")
            con.execute("DROP TABLE IF EXISTS temp.retraits_leves")
            con.execute(
                "CREATE TEMP TABLE retraits_leves AS"
                " SELECT l.app_contact_id, l.hektor_annonce_id"
                "   FROM temp.retraits_locaux l"
                "   JOIN app_relation__sb s"
                "     ON s.app_contact_id    = l.app_contact_id"
                "    AND s.hektor_annonce_id = l.hektor_annonce_id"
                "  WHERE s.retire_le IS NULL")
            cur_lev = con.execute(
                "UPDATE app_relation SET retire_le = NULL, retire_par = NULL"
                "  FROM temp.retraits_leves v"
                " WHERE app_relation.app_contact_id    = v.app_contact_id"
                "   AND app_relation.hektor_annonce_id = v.hektor_annonce_id"
                "   AND app_relation.retire_le IS NOT NULL")
            retraits_leves = cur_lev.rowcount or 0
            con.execute("DROP TABLE IF EXISTS temp.retraits_leves")
            con.execute("DROP TABLE IF EXISTS temp.retraits_locaux")
        elif doublure_du:
            print("   !! retraits NON leves : la doublure est du %s, pas du jour"
                  % str(doublure_du)[:10])


        # ══════════════════════════════════════════════════════════════════════
        # ⚠⚠ LA QUESTION LA MOINS CHERE D'ABORD            corrige le 03/10/2026
        # ══════════════════════════════════════════════════════════════════════
        # CE QUE CA A COUTE, et c'est mesure, pas estime :
        #     01/10  50 s   ·   02/10  46 s   ·   03/10  79 MINUTES  (x103)
        # Le run de nuit a fini a 08:21 au lieu de 07:41, il est donc tombe DANS
        # la descente de 08:15, et les trois etapes suivantes -- qui ecrivent dans
        # CETTE base -- ont echoue. 17 etapes n'ont jamais demarre, dont TOUTES
        # les montees vers le cloud.
        #
        # POURQUOI : l'UPDATE ci-dessous demande, pour CHACUNE des 132 683 lignes,
        # « la doublure contient-elle ce couple ? ». app_relation__sb n'a AUCUN
        # index -- la descente recopie les donnees, jamais les index, et elle
        # termine par DROP TABLE + RENAME (pull_from_supabase.py:681), donc tout
        # index pose y est detruit chaque nuit. Plan reel : SCAN app_relation +
        # deux CORRELATED SCALAR SUBQUERY -> SCAN s. Soit ~17,6 milliards de
        # lectures de ligne, trois fois.
        #
        # ⛔ ET TOUT CELA POUR RIEN : la doublure portait 0 retrait, le serveur
        #   aussi. Mon propre message de commit du 02/10 le disait -- « ZERO EFFET
        #   AUJOURD'HUI : aucune RPC ni aucun ecran ne sait ecrire retire_le » --
        #   et je ne m'en suis pas servi pour mesurer le COUT. Deuxieme fois en
        #   quatre jours : le 30/09 j'avais rendu une vue 100 a 280 fois plus
        #   lente en verifiant son contenu et jamais son temps.
        #
        # ⭐ L'ORDRE EST LE CORRECTIF. On demande d'abord s'il y a quelque chose a
        #   adopter : un seul passage, qui s'arrete au premier retrait trouve. Les
        #   nuits normales ne paient meme pas la construction de l'index.
        #
        # ⚠ LE SENS EST RIGOUREUSEMENT CONSERVE : si la doublure ne porte AUCUN
        #   retrait, alors tout retrait du serveur est par definition divergent --
        #   le COUNT ci-dessous dit donc exactement ce que disait le NOT EXISTS.
        if con.execute("SELECT 1 FROM app_relation__sb"
                       " WHERE retire_le IS NOT NULL LIMIT 1").fetchone() is None:
            retraits_poses = 0
            retraits_divergents = con.execute(
                "SELECT COUNT(*) FROM app_relation"
                " WHERE retire_le IS NOT NULL").fetchone()[0]
            con.commit()
            return _bilan_relations(lus, neufs, revus, ecartes, adoptes_au_depart,
                                    adoptes, depuis_app_seule, illisibles, sans_bien,
                                    sortis, doublure_du, retraits_poses,
                                    retraits_divergents, retraits_leves)

        # ══════════════════════════════════════════════════════════════════════
        # ⛔⛔ POSER UN INDEX SUR LA DOUBLURE NE SUFFIT PAS -- mesure du 03/10
        # ══════════════════════════════════════════════════════════════════════
        # Ma 1re version de ce correctif creait un index sur app_relation__sb et
        # gardait les sous-requetes correlees. EPROUVE SUR LES VRAIES DONNEES : le
        # plan ne bouge PAS d'un iota, avant comme apres l'index :
        #     SCAN app_relation / CORRELATED SCALAR SUBQUERY -> SCAN s
        # Donc le chemin cher restait aussi lent qu'avant, et je ne l'aurais JAMAIS
        # vu en relisant le code -- seule l'execution sur une copie fidele l'a dit.
        #
        # POURQUOI. La descente cree les colonnes de la doublure SANS TYPE DECLARE
        # (PRAGMA table_info rend ''), donc sans affinite. Face a app_relation,
        # dont app_contact_id est INTEGER, SQLite n'utilise pas l'index :
        #     · egalite avec une CONSTANTE entiere -> SEARCH ... USING INDEX  ✔
        #     · sous-requete correlee sur colonne  -> SCAN s                  ✘
        #
        # ⭐ LA BONNE REPARATION N'EST PAS DE FORCER L'OPTIMISEUR, C'EST DE RENDRE
        #   LA TABLE INTERIEURE PETITE. Un retrait est un GESTE HUMAIN : il y en a
        #   0 aujourd'hui et il y en aura une poignee. On extrait donc d'abord les
        #   seuls retraits dans une table TYPEE, puis on pilote la mise a jour
        #   DEPUIS elle. Le cout devient proportionnel au NOMBRE DE RETRAITS, plus
        #   au carre du registre -- et il le reste meme si l'optimiseur choisit mal.
        con.execute("DROP TABLE IF EXISTS temp.retraits_doublure")
        con.execute("CREATE TEMP TABLE retraits_doublure ("
                    " app_contact_id INTEGER, hektor_annonce_id TEXT,"
                    " retire_le TEXT, retire_par TEXT)")
        con.execute("INSERT INTO temp.retraits_doublure"
                    " SELECT app_contact_id, hektor_annonce_id, retire_le, retire_par"
                    "   FROM app_relation__sb WHERE retire_le IS NOT NULL")
        con.execute("CREATE INDEX temp.idx_retraits_doublure"
                    " ON retraits_doublure (app_contact_id, hektor_annonce_id)")

        # UPDATE..FROM : SQLite >= 3.33 (ici 3.50.4, cote .venv du run aussi). Il
        # pilote depuis la PETITE table et retrouve chaque ligne du registre par sa
        # cle unique -- SEARCH r USING sqlite_autoindex_app_relation_1.
        cur = con.execute(
            "UPDATE app_relation SET retire_le = s.retire_le, retire_par = s.retire_par"
            "  FROM temp.retraits_doublure s"
            " WHERE app_relation.app_contact_id    = s.app_contact_id"
            "   AND app_relation.hektor_annonce_id = s.hektor_annonce_id"
            "   AND app_relation.retire_le IS NULL")
        retraits_poses = cur.rowcount or 0
        # divergence : le SERVEUR porte un retrait que la doublure ne porte pas.
        # On ne tranche pas -- on compte, et le bilan du run le dira.
        retraits_divergents = con.execute(
            "SELECT COUNT(*) FROM app_relation r"
            " WHERE r.retire_le IS NOT NULL"
            "   AND NOT EXISTS (SELECT 1 FROM temp.retraits_doublure s"
            "                    WHERE s.app_contact_id = r.app_contact_id"
            "                      AND s.hektor_annonce_id = r.hektor_annonce_id)").fetchone()[0]
        con.execute("DROP TABLE IF EXISTS temp.retraits_doublure")
    except (sqlite3.OperationalError, TypeError, ValueError) as exc:
        # La doublure n'existe pas encore (descente jamais passee). On ne devine
        # pas, et on NE CASSE PAS LE RUN : le bilan rendra doublure_du = None.
        #
        # ⛔ ET IL FAUT L'EFFACER ICI -- defaut trouve le 03/10 en eprouvant le cas
        #   « doublure absente ». `doublure_du` est lu AVANT l'adoption, depuis
        #   sb_pull_state. Si la table a disparu mais que l'etat garde sa date, le
        #   bilan annoncait une doublure FRAICHE alors que RIEN n'avait ete adopte
        #   -- le garde-fou de fraicheur restait donc muet, exactement la panne
        #   qu'il existe pour empecher. Le code contredisait son propre commentaire.
        doublure_du = None
        print("   !! retraits non lus (%s)" % str(exc)[:100])

    con.commit()
    return _bilan_relations(lus, neufs, revus, ecartes, adoptes_au_depart, adoptes,
                            depuis_app_seule, illisibles, sans_bien, sortis,
                            doublure_du, retraits_poses, retraits_divergents,
                            retraits_leves)


def _bilan_relations(lus, neufs, revus, ecartes, adoptes_au_depart, adoptes,
                     depuis_app_seule, illisibles, sans_bien, sortis,
                     doublure_du, retraits_poses, retraits_divergents,
                     retraits_leves=0) -> dict:
    """LE bilan, en UN seul endroit.

    ⚠ IL EXISTE PARCE QU'IL Y A DEUX SORTIES : le raccourci « rien a adopter » et
      le chemin complet. Deux dictionnaires recopies a la main auraient derive au
      premier champ ajoute -- et une cle manquante ne se verrait PAS : le run
      afficherait un bilan incomplet sans rien signaler.
    """
    return {"lus": lus, "neufs": neufs, "revus": revus, "ecartes": ecartes,
            "adoptes_du_cloud": adoptes_au_depart - len(adoptes),
            "depuis_app_seule": depuis_app_seule,
            "app_seule_illisibles": illisibles,
            "sans_notre_numero_de_bien": sans_bien, "sortis_du_miroir": sortis,
            "doublure_du": doublure_du,
            "retraits_adoptes": retraits_poses,
            "retraits_divergents": retraits_divergents,
            "retraits_leves": retraits_leves}


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
    print("   RETIRES volontairement (CONSERVES)  : %s" % q("SELECT COUNT(*) FROM app_relation WHERE retire_le IS NOT NULL"))
    print("   avec le numero HEKTOR de la personne: %s" % q("SELECT COUNT(*) FROM app_relation WHERE hektor_contact_id IS NOT NULL"))
    print("   SANS ce numero                      : %s   (doit tendre vers 0)" % q("SELECT COUNT(*) FROM app_relation WHERE hektor_contact_id IS NULL"))
    for role, n in con.execute("SELECT role_hektor, COUNT(*) FROM app_relation GROUP BY 1 ORDER BY 2 DESC"):
        print("      dernier libelle Hektor %-12s %s" % (role, n))
    print("")
    doublons = q("SELECT COUNT(*) FROM (SELECT 1 FROM app_relation"
                 " GROUP BY app_contact_id, hektor_annonce_id HAVING COUNT(*) > 1)")
    print("   doublons sur la cle                 : %s   (doit valoir 0)" % doublons)
    hors = q("SELECT COUNT(*) FROM app_relation WHERE app_contact_id < 10000000")
    print("   numeros de contact hors plage app   : %s   (doit valoir 0)" % hors)
    # ⚠ 09/10/2026 -- CE CONTROLE MESURAIT TROP LARGE, ET IL A CRIE POUR RIEN.
    #   Il comptait TOUTES les lignes de la plage de l'app. Or le 30/09, une heure
    #   apres l'avoir ecrit, on a ajoute l'ADOPTION (commit b8f1276) : le run
    #   reprend le numero pose par l'app au lieu d'en inventer un second, sinon le
    #   push heurte l'index unique du couple et LE RUN S'ARRETE LA (incident des
    #   01-02/09, 18 h perdues). Les deux pieces se contredisaient depuis ce
    #   jour-la sans que ca se voie : l'adoption n'a servi pour la premiere fois
    #   que le 09/10 (adoptes_du_cloud = 1), et le controle a aussitot crie pour
    #   une ligne parfaitement saine.
    #   CE QU'ON VEUT VRAIMENT SAVOIR : le run a-t-il INVENTE un numero dans la
    #   plage de l'app ? Une ligne adoptee porte le numero de la DOUBLURE ; une
    #   ligne inventee par le run n'y figure pas. C'est le discriminant.
    #   ⚠ Doublure illisible : on NE SE TAIT PAS, on retombe sur l'ancien compte,
    #     quitte a crier a tort. Un silence couterait plus cher.
    dans_plage = q("SELECT COUNT(*) FROM app_relation WHERE app_relation_id >= %d"
                   % PLAGE_RESERVEE_APP)
    try:
        adoptees = q("SELECT COUNT(*) FROM app_relation r"
                     " WHERE r.app_relation_id >= %d"
                     "   AND EXISTS (SELECT 1 FROM app_relation__sb s"
                     "               WHERE s.app_relation_id = r.app_relation_id)"
                     % PLAGE_RESERVEE_APP)
        envahis = dans_plage - adoptees
        doublure_lue = True
    except sqlite3.OperationalError:
        envahis, doublure_lue = dans_plage, False
    print("   dans la plage de l'app              : %s   (posees par l'app : normal)"
          % dans_plage)
    if not doublure_lue:
        print("   !! DOUBLURE app_relation__sb ILLISIBLE -- impossible de dire")
        print("      lesquelles viennent de l'app. On compte tout.")
    print("   dont INVENTEES PAR LE RUN           : %s   (doit valoir 0)" % envahis)
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



# =============================================================================
# LE PUSH VERS SUPABASE                                            30/09/2026
#
# delete-never : on UPSERT, on n'efface jamais. Une ligne que le miroir ne
# montre plus porte present_in_hektor = 0 et RESTE. C'est ce qui distingue ce
# registre de `app_contact_relation_current`, videe et refaite a chaque nuit --
# et c'est la raison d'etre de toute la table : 82 386 liens qu'un bien vendu
# emportait hors du cloud.
#
# ⛔ `--push` NE SE LANCE JAMAIS SEUL. Lecon du 07/09/2026, payee sur le ledger
#    d'affaires : un push lance a la main a 07:52 a efface une annulation de
#    compromis faite a 06:38, parce qu'il envoyait l'etat du miroir LOCAL, fige
#    au run de 04:18. « La cause n'est pas le push, c'est l'ordre. Pousser sans
#    rafraichir revient a affirmer un etat qu'on n'a pas relu. »
#    Le garde-fou est dans le code, pas seulement en commentaire.
#
# ⚠ TOUT MONTE -- decision de Frederic du 30/09 : « il faut tout monter pour
#   avoir le registre des liens entier ». On n'applique donc AUCUN filtre sur
#   le parc ici. C'est le montage du mandat : le registre porte tout, les
#   ecrans filtrent.
# =============================================================================

# Les colonnes sont NOMMEES une a une : une colonne locale inconnue de Supabase
# ferait tomber le lot entier (« column ... does not exist »).
COLONNES_POUSSEES = (
    "app_relation_id", "app_contact_id", "app_dossier_id", "hektor_annonce_id",
    "fait", "role_hektor", "source", "relation_key",
    "hektor_contact_id", "first_seen_at", "last_seen_at", "present_in_hektor",
    "absent_depuis", "retire_le", "retire_par",
)


def lignes_a_pousser(con: sqlite3.Connection) -> list[dict]:
    lignes = []
    for r in con.execute("SELECT * FROM app_relation"):
        d = {c: r[c] for c in COLONNES_POUSSEES if c in r.keys()}
        # SQLite garde 0/1 ; Supabase attend un booleen. Sans cette ligne,
        # PostgREST recoit 1 pour un champ boolean et refuse le lot entier.
        d["present_in_hektor"] = bool(d.get("present_in_hektor"))
        lignes.append(d)
    return lignes


def pousser(con: sqlite3.Connection, taille_lot: int = 500, a_blanc: bool = False) -> dict:
    lignes = lignes_a_pousser(con)
    if a_blanc:
        return {"a_blanc": True, "lignes": len(lignes),
                "colonnes": len(COLONNES_POUSSEES),
                "exemple": dict(lignes[0]) if lignes else {}}

    load_env_files(DEFAULT_ENV_FILES)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis")
    client = SupabaseRestClient(base_url=url, service_role_key=cle)
    if not client.table_available(TABLE):
        raise RuntimeError(
            "app_relation n'existe pas cote Supabase. Appliquer d'abord "
            "supabase/patch_app_relation_2026-09-30.sql.")
    client.upsert_rows(path=TABLE, rows=lignes, batch_size=taille_lot)
    return {"lignes_poussees": len(lignes)}

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Le registre des liens, en local. DORMANT.")
    parser.add_argument("--refresh", action="store_true", help="Remplit la table depuis la couche des liens.")
    parser.add_argument("--controle", action="store_true", help="Affiche les controles, sans rien ecrire.")
    parser.add_argument("--partiel", action="store_true",
                        help="N'applique pas present_in_hektor=0 aux lignes non revues.")
    parser.add_argument("--push", action="store_true",
                        help="UPSERT vers Supabase (delete-never). Exige --refresh.")
    parser.add_argument("--push-a-blanc", action="store_true",
                        help="Compte ce qui serait pousse, sans rien envoyer.")
    parser.add_argument("--push-seul-je-sais", action="store_true",
                        help="Lever le garde-fou et pousser SANS rafraichir.")
    parser.add_argument("--taille-lot", type=int, default=500)
    args = parser.parse_args()
    if not (args.refresh or args.controle or args.push or args.push_a_blanc):
        parser.error("choisir --refresh, --controle, --push ou --push-a-blanc")

    # ⛔ LE GARDE-FOU DU 07/09. Pousser sans rafraichir, c'est affirmer un etat
    #    qu'on n'a pas relu : le push envoie le miroir LOCAL, qui date du dernier
    #    run, et ecrase en ligne tout geste fait depuis.
    if args.push and not args.refresh and not args.push_seul_je_sais:
        parser.error(
            "--push sans --refresh est refuse : le push enverrait l'etat du miroir "
            "LOCAL, qui date du dernier run, et ecraserait en ligne tout geste fait "
            "depuis (lecon du 07/09/2026, ledger d'affaires). Utiliser "
            "`--refresh --push`, ou assumer avec --push-seul-je-sais.")

    con = _open_local()
    try:
        if args.refresh:
            bilan = refresh(con, full=not args.partiel)
            print("REFRESH app_relation")
            for k in ("lus", "neufs", "revus", "adoptes_du_cloud", "depuis_app_seule", "app_seule_illisibles", "ecartes",
                      "sans_notre_numero_de_bien", "sortis_du_miroir",
                      # 02/10 : les retraits decides dans l'app
                      # 09/10 : retraits_leves manquait ici -- il etait calcule et
                      # renvoye, mais JAMAIS imprime. Le controle ecrit pour 5e-B
                      # etait donc impossible a faire.
                      "doublure_du", "retraits_adoptes", "retraits_divergents",
                      "retraits_leves"):
                print("   %-28s : %s" % (k, bilan[k]))
            # ⚠ UNE DOUBLURE PERIMEE NE SE VOIT PAS : elle rend des chiffres, ils
            #   sont juste vieux. Sans ce controle, un retrait d'hier apres-midi
            #   serait manque EN SILENCE -- la famille de panne la plus chere ici.
            aujourdhui = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
            if not bilan["doublure_du"]:
                print("   !! DOUBLURE ABSENTE -- aucun retrait ne peut etre lu.")
                print("      Attendu : l'etape « doublure des liens » juste avant celle-ci")
                print("      (pull_from_supabase.py --table app_relation).")
            elif not str(bilan["doublure_du"]).startswith(aujourdhui):
                print("   !! DOUBLURE DU %s, PAS D'AUJOURD'HUI (%s)."
                      % (str(bilan["doublure_du"])[:16], aujourdhui))
                print("      Un retrait decide depuis sa descente serait MANQUE, et le")
                print("      push l'effacerait. Verifier l'etape « doublure des liens ».")
            if bilan["retraits_divergents"]:
                print("   !! %s retrait(s) que le SERVEUR porte et la doublure non."
                      % bilan["retraits_divergents"])
                print("      On n'y touche pas : effacer un retrait a tort fait REAPPARAITRE")
                print("      le lien a l'ecran. A regarder a la main.")
        elif not (args.push or args.push_a_blanc):
            con.executescript(SCHEMA)
        if args.push_a_blanc:
            bilan = pousser(con, a_blanc=True)
            print("")
            print("PUSH A BLANC -- rien n'est envoye")
            print("   lignes qui partiraient  : %s" % bilan["lignes"])
            print("   colonnes envoyees       : %s" % bilan["colonnes"])
            for k, v in sorted(bilan["exemple"].items()):
                print("      %-20s = %r" % (k, v))
        elif args.push:
            bilan = pousser(con, taille_lot=args.taille_lot)
            print("")
            print("PUSH app_relation -> Supabase : %s lignes" % bilan["lignes_poussees"])
        if args.refresh or args.controle:
            controle(con)
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
