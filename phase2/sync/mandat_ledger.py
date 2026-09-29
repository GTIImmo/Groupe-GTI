# -*- coding: utf-8 -*-
"""A.3-tech phase 1 -- LE REGISTRE DES MANDATS, CHEZ NOUS.

CE QUE C'EST
------------
L'equivalent de `app_affaire_ledger`, pour les mandats. Une table DURABLE, qui
n'est jamais detruite ni reconstruite, ou chaque mandat a SA ligne et SON numero.

POURQUOI ELLE MANQUE, ET CE QU'ON PERD SANS ELLE
------------------------------------------------
`app_mandat_register_current` n'est PAS un registre : c'est une vue de travail,
effacee et refaite a chaque push, et FILTREE SUR LE STATUT DE L'ANNONCE. La
lecon est ecrite dans le worker (28/08) :

    « Une annonce qui passe a "Clos" ou "Vendu" en SORT -- la ligne disparait au
      moment precis ou l'on veut y poser la date. [...] 642 des 1 105 mandats
      absents du registre le sont parce qu'ils sont clos. »

Mesure du 29/09 : 23 091 lignes du registre sont figees au 31/07, et les annonces
qui ont quitte le parc depuis ont perdu les leurs. Cette table-ci ne perd rien.

CE QUE CE SCRIPT FAIT, ET CE QU'IL NE FAIT PAS
-----------------------------------------------
Il LIT le miroir (`hektor.hektor_mandat`) et remplit `app_mandat` en local.
Il n'ecrit PAS dans Supabase, ne touche PAS au registre, n'appelle PAS Hektor.
Il est DORMANT : rien ne le lance, rien ne le lit. On l'appelle a la main.

LES TROIS REGLES COPIEES DU LEDGER D'AFFAIRES, ET POURQUOI
-----------------------------------------------------------
1. DEUX DISTRIBUTEURS, DEUX PLAGES, QUI NE SE CROISENT JAMAIS.
   Le run prend `MAX(id) WHERE id < PLAGE_RESERVEE_APP`, JAMAIS le MAX global.
   -- C'est la ligne exacte qui a coute cinq jours en aout : le run avait vu un
      MAX a un million, s'etait mis a compter depuis la, et envahissait la plage
      de l'app ; la sequence distribuait alors des numeros DEJA PRIS, et AUCUNE
      creation d'offre, de compromis ni de vente n'aboutissait -- sous un message
      qui parlait d'autre chose.

2. ON NE RENUMEROTE JAMAIS UNE LIGNE CONNUE.
   `app_mandat_id` est absent du ON CONFLICT DO UPDATE : un mandat garde son
   numero pour toujours. C'est la regle du projet (« un numero ne se perd jamais »).

3. LA PROTECTION PAR OMISSION.
   Ce que le run ne reecrit pas, il le preserve. `date_cloture` est donc HORS du
   ON CONFLICT : l'app la possede deja (CHAMPS_APP_MANDAT), le carnet
   `app_mandat_champ_app` la porte, et le run n'a pas a l'ecraser.

LA CLE : LE COUPLE (annonce, numero de mandat)
-----------------------------------------------
Ce n'est pas `hektor_mandat_id` : Hektor REUTILISE ses identifiants bas
(23 452 distincts pour 23 840 mandats). Le projet a tranche pour le couple, et
la mesure le confirme : 24 939 sur 24 939 au 28/08, 24 999 sur 24 999 au 29/09.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"

TABLE = "app_mandat"

# La moitie haute est RESERVEE aux mandats nes dans l'app. Le run ne la regarde
# jamais. Meme valeur et meme role que pour l'affaire et le dossier.
PLAGE_RESERVEE_APP = 1_000_000

# Les deux familles de registre, deja etablies par le projet : les types anglo
# de Hektor d'un cote, les libelles francais de PROTEXA de l'autre.
FAMILLE_HEKTOR = {"SIMPLE", "EXCLUSIF", "ACCORD"}

for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


SCHEMA = """
CREATE TABLE IF NOT EXISTS app_mandat (
    app_mandat_id        INTEGER PRIMARY KEY,
    app_dossier_id       INTEGER,
    hektor_annonce_id    TEXT NOT NULL,
    numero_mandat        TEXT NOT NULL,
    hektor_mandat_id     TEXT,
    famille              TEXT,
    type                 TEXT,
    date_enregistrement  TEXT,
    date_debut           TEXT,
    date_fin             TEXT,
    montant              TEXT,
    mandants_texte       TEXT,
    note                 TEXT,
    payload_json         TEXT,
    -- D'OU VIENT LA LIGNE. Deux sources, comme le registre actuel :
    --   'mandat'  la fiche mandat de Hektor (hektor_mandat) -- complete
    --   'annonce' le numero porte par l'annonce (hektor_annonce.no_mandat),
    --             quand AUCUNE fiche mandat n'existe. Type et dates sont vides.
    -- ⚠ TROUVE PAR LE 4e CONTROLE, le 29/09 : ma premiere version ne lisait que
    --   hektor_mandat et perdait 2 072 numeros -- dont l'annonce 63003, que le
    --   registre avait et que la table n'avait pas. Un numero EMIS doit figurer
    --   au registre, meme si sa fiche n'est jamais redescendue.
    origine              TEXT,
    -- HORS du ON CONFLICT : protection par omission. L'app possede ce champ
    -- (CHAMPS_APP_MANDAT), le carnet app_mandat_champ_app le porte, et le run
    -- n'a pas a l'ecraser avec ce que Hektor en pense.
    date_cloture         TEXT,
    first_seen_at        TEXT,
    last_seen_at         TEXT,
    -- delete-never : une ligne que le miroir ne montre plus est MARQUEE, jamais
    -- supprimee. Meme patron que les photos et que le ledger d'affaires.
    present_in_hektor    INTEGER NOT NULL DEFAULT 1,
    UNIQUE (hektor_annonce_id, numero_mandat)
);
CREATE INDEX IF NOT EXISTS idx_app_mandat_annonce ON app_mandat (hektor_annonce_id);
CREATE INDEX IF NOT EXISTS idx_app_mandat_numero  ON app_mandat (numero_mandat);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _open_local() -> sqlite3.Connection:
    con = sqlite3.connect(PHASE2_DB)
    con.row_factory = sqlite3.Row
    # busy_timeout : phase2 a PLUSIEURS ecrivains. Les 5 s par defaut ont deja
    # tue un rattrapage entier. Toute connexion phase2 doit le poser.
    con.execute("PRAGMA busy_timeout = 60000")
    con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
    return con


def _famille(type_mandat, numero) -> str:
    """HEKTOR ou PROTEXA. Le type tranche ; le numero confirme."""
    t = (type_mandat or "").strip().upper()
    if t in FAMILLE_HEKTOR:
        return "HEKTOR"
    if t:
        return "PROTEXA"
    # Sans type : les numeros HEKTOR sont longs (M63-01055 -> 6301055), ceux de
    # PROTEXA tiennent sur cinq chiffres. On ne devine que faute de mieux.
    n = (numero or "").strip()
    return "HEKTOR" if n.isdigit() and len(n) > 6 else "PROTEXA"


def _ajouter_colonne_si_absente(con: sqlite3.Connection, nom: str, type_sql: str) -> None:
    """SQLite n'a pas ADD COLUMN IF NOT EXISTS. On regarde avant d'ajouter.

    Une table qui existe deja ne recoit RIEN de CREATE TABLE IF NOT EXISTS --
    pas meme une colonne neuve. C'est le piege deja note dans affaire_ledger.py.
    """
    colonnes = {r[1] for r in con.execute("PRAGMA table_info(app_mandat)")}
    if nom not in colonnes:
        con.execute("ALTER TABLE app_mandat ADD COLUMN %s %s" % (nom, type_sql))


def refresh(con: sqlite3.Connection, full: bool = True) -> dict:
    con.executescript(SCHEMA)
    _ajouter_colonne_si_absente(con, "origine", "TEXT")
    vu = now_iso()

    # LE DISTRIBUTEUR. On ignore la moitie haute -- voir la regle 1 en tete.
    prochain = (con.execute(
        "SELECT COALESCE(MAX(app_mandat_id), 0) FROM app_mandat WHERE app_mandat_id < ?",
        (PLAGE_RESERVEE_APP,),
    ).fetchone()[0]) + 1

    connus = set()
    for r in con.execute("SELECT hektor_annonce_id, numero_mandat FROM app_mandat"):
        connus.add((str(r["hektor_annonce_id"]), str(r["numero_mandat"])))

    # Notre numero d'annonce, pour que la ligne porte NOTRE identite et pas
    # seulement celle de Hektor.
    dossiers = {}
    for r in con.execute(
        "SELECT id, hektor_annonce_id FROM app_dossier WHERE hektor_annonce_id IS NOT NULL"
    ):
        dossiers[str(r["hektor_annonce_id"])] = r["id"]

    lus = neufs = revus = sans_numero = 0
    vus_ce_run = []

    lignes = con.execute(
        "SELECT hektor_mandat_id, hektor_annonce_id, numero, type, date_enregistrement,"
        " date_debut, date_fin, date_cloture, montant, mandants_texte, note, raw_json"
        " FROM hektor.hektor_mandat"
    ).fetchall()

    for m in lignes:
        lus += 1
        annonce = str(m["hektor_annonce_id"] or "").strip()
        numero = str(m["numero"] or "").strip()
        if not annonce or not numero:
            sans_numero += 1
            continue
        cle = (annonce, numero)
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
            INSERT INTO app_mandat(app_mandat_id, app_dossier_id, hektor_annonce_id,
                numero_mandat, hektor_mandat_id, famille, type, date_enregistrement,
                date_debut, date_fin, montant, mandants_texte, note, payload_json,
                date_cloture, first_seen_at, last_seen_at, origine, present_in_hektor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'mandat', 1)
            ON CONFLICT(hektor_annonce_id, numero_mandat) DO UPDATE SET
                app_dossier_id=COALESCE(excluded.app_dossier_id, app_mandat.app_dossier_id),
                hektor_mandat_id=excluded.hektor_mandat_id,
                origine='mandat',
                famille=excluded.famille,
                type=excluded.type,
                date_enregistrement=excluded.date_enregistrement,
                date_debut=excluded.date_debut,
                date_fin=excluded.date_fin,
                montant=excluded.montant,
                mandants_texte=excluded.mandants_texte,
                note=excluded.note,
                payload_json=excluded.payload_json,
                last_seen_at=excluded.last_seen_at,
                present_in_hektor=1
            """,
            (
                identifiant, dossiers.get(annonce), annonce, numero,
                str(m["hektor_mandat_id"] or "") or None,
                _famille(m["type"], numero), m["type"], m["date_enregistrement"],
                m["date_debut"], m["date_fin"], m["montant"], m["mandants_texte"],
                m["note"], m["raw_json"], m["date_cloture"], vu, vu,
            ),
        )

    # ------------------------------------------------------------------ 2e SOURCE
    # LE NUMERO PORTE PAR L'ANNONCE, QUAND AUCUNE FICHE MANDAT N'EXISTE.
    #
    # C'est ce que fait deja le registre actuel, et c'est ce que ma premiere
    # version perdait : 2 072 numeros emis dont la fiche n'est jamais redescendue
    # du detail (le run ne relit pas le detail d'une annonce archivee depuis des
    # annees). Trouve par le 4e controle : l'annonce 63003 etait au registre et
    # pas dans la table.
    #
    # ⚠ ON N'ECRASE JAMAIS UNE LIGNE VENUE DU MANDAT. La fiche est plus riche
    #   (type, dates, mandants) ; le numero seul ne doit pas la remplacer. D'ou
    #   le `DO NOTHING` : la ligne n'est posee que si le couple est inconnu.
    depuis_annonce = 0
    for a in con.execute(
        "SELECT hektor_annonce_id, no_mandat FROM hektor.hektor_annonce"
        " WHERE TRIM(COALESCE(no_mandat, '')) <> ''"
    ).fetchall():
        annonce = str(a["hektor_annonce_id"] or "").strip()
        numero = str(a["no_mandat"] or "").strip()
        if not annonce or not numero:
            continue
        cle = (annonce, numero)
        if cle in connus:
            vus_ce_run.append(cle)
            continue
        identifiant = prochain
        prochain += 1
        connus.add(cle)
        depuis_annonce += 1
        vus_ce_run.append(cle)
        con.execute(
            """
            INSERT INTO app_mandat(app_mandat_id, app_dossier_id, hektor_annonce_id,
                numero_mandat, famille, first_seen_at, last_seen_at, origine,
                present_in_hektor)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'annonce', 1)
            ON CONFLICT(hektor_annonce_id, numero_mandat) DO NOTHING
            """,
            (identifiant, dossiers.get(annonce), annonce, numero,
             _famille(None, numero), vu, vu),
        )

    sortis = 0
    if full and vus_ce_run:
        con.execute("CREATE TEMP TABLE IF NOT EXISTS _vus(a TEXT, n TEXT)")
        con.execute("DELETE FROM _vus")
        con.executemany("INSERT INTO _vus(a, n) VALUES (?, ?)", vus_ce_run)
        cur = con.execute(
            "UPDATE app_mandat SET present_in_hektor = 0"
            " WHERE present_in_hektor = 1"
            "   AND NOT EXISTS (SELECT 1 FROM _vus v"
            "                    WHERE v.a = app_mandat.hektor_annonce_id"
            "                      AND v.n = app_mandat.numero_mandat)"
        )
        sortis = cur.rowcount or 0

    con.commit()
    return {"lus": lus, "neufs": neufs, "revus": revus,
            "sans_numero": sans_numero, "depuis_annonce": depuis_annonce,
            "sortis_du_miroir": sortis}


def controle(con: sqlite3.Connection) -> None:
    def q(sql):
        return con.execute(sql).fetchone()[0]

    print("")
    print("CONTROLES")
    print("   lignes                              : %s" % q("SELECT COUNT(*) FROM app_mandat"))
    print("   numeros de mandat distincts         : %s" % q("SELECT COUNT(DISTINCT numero_mandat) FROM app_mandat"))
    print("   annonces distinctes                 : %s" % q("SELECT COUNT(DISTINCT hektor_annonce_id) FROM app_mandat"))
    print("   avec NOTRE numero d'annonce         : %s" % q("SELECT COUNT(*) FROM app_mandat WHERE app_dossier_id IS NOT NULL"))
    print("   sortis du miroir (CONSERVES)        : %s" % q("SELECT COUNT(*) FROM app_mandat WHERE present_in_hektor = 0"))
    for famille, n in con.execute("SELECT famille, COUNT(*) FROM app_mandat GROUP BY 1 ORDER BY 2 DESC"):
        print("      famille %-10s              : %s" % (famille, n))
    for origine, n in con.execute("SELECT origine, COUNT(*) FROM app_mandat GROUP BY 1 ORDER BY 2 DESC"):
        print("      venu de %-10s              : %s" % (origine, n))
    print("")
    # LE CONTROLE QUI COMPTE : aucun numero ne doit tomber dans la plage de l'app.
    envahis = q("SELECT COUNT(*) FROM app_mandat WHERE app_mandat_id >= %d" % PLAGE_RESERVEE_APP)
    print("   DANS LA PLAGE RESERVEE A L'APP      : %s   (doit valoir 0)" % envahis)
    if envahis:
        print("   >> L'ALLOCATEUR EST FAUX. C'est le defaut d'aout, a l'identique.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="A.3-tech phase 1 : remplit app_mandat depuis le miroir. LOCAL, dormant.")
    parser.add_argument("--refresh", action="store_true", help="Remplit la table depuis le miroir.")
    parser.add_argument("--controle", action="store_true", help="Affiche les controles, sans rien ecrire.")
    parser.add_argument("--partiel", action="store_true",
                        help="N'applique pas present_in_hektor=0 aux lignes non revues.")
    args = parser.parse_args()
    if not args.refresh and not args.controle:
        parser.error("choisir --refresh ou --controle")

    if not HEKTOR_DB.exists():
        print("miroir introuvable : %s" % HEKTOR_DB, file=sys.stderr)
        return 2

    con = _open_local()
    try:
        if args.refresh:
            bilan = refresh(con, full=not args.partiel)
            print("REFRESH app_mandat")
            for k in ("lus", "neufs", "revus", "sans_numero", "depuis_annonce", "sortis_du_miroir"):
                print("   %-22s : %s" % (k, bilan[k]))
        else:
            con.executescript(SCHEMA)
        controle(con)
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
