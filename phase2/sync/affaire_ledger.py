"""Ledger d'affaires app-owned (offre / compromis / vente) — NIVEAU B.

Objectif : indépendance vis-à-vis de Hektor. On accumule chaque affaire vue dans une table
app-owned, en **UPSERT sur l'id stable** (les changements d'état — ex. compromis active -> cancelled —
sont reflétés) mais **jamais supprimée** : si Hektor retire une affaire, on la conserve avec
`present_in_hektor = false`. Le registre continue de lire Hektor comme aujourd'hui (le branchement
lecture = étape B+ séparée) ; ici on ne fait que **sécuriser la donnée**.

Table locale : phase2/phase2.sqlite -> app_affaire_ledger.
Table Supabase : public.app_affaire_ledger (même schéma).
NON touchée par delete_local_annonce (delete-never) : exemption par simple absence de la table
de sa liste de nettoyage.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"

sys.path.insert(0, str(ROOT / "phase2" / "sync"))
from export_app_payload import _compact_party, normalize_text  # noqa: E402
from push_upgrade_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES,
    SupabaseRestClient,
    load_env_files,
)

import os  # noqa: E402

LEDGER_TABLE = "app_affaire_ledger"

# LA FRONTIERE ENTRE LES DEUX SERIES DE NUMEROS.
#   en dessous : les affaires vues chez Hektor, numerotees par ce script (a 28 981)
#   au-dessus  : les affaires NEES DANS L'APP, numerotees par la sequence Supabase
#                app_affaire_id_app_seq
# Le run ne distribue JAMAIS au-dessus de cette frontiere -- sinon les deux series
# se telescopent et la sequence de l'app se met a rendre des numeros deja pris.
PLAGE_RESERVEE_APP = 1_000_000

# Identite (20/08/2026) : l'affaire porte d'abord le numero de l'app.
#   app_affaire_id -- UNE serie pour les trois types. Hektor, lui, tient trois compteurs
#     separes dont les numeros se telescopent : 7 541 numeros sont portes par deux types
#     differents, sur des annonces et des acquereurs differents. Le numero de Hektor n'est
#     donc unique QUE dans son type -- d'ou l'index unique sur le triplet, et pas sur l'id.
#   app_dossier_id -- le numero d'annonce de l'app, a cote de celui de Hektor.
# Les deux colonnes Hektor deviennent facultatives : une affaire saisie dans l'app existe
# avant que Hektor ne la numerote, et parfois sans que Hektor la numerote jamais.
DDL_SQLITE = f"""
CREATE TABLE IF NOT EXISTS {LEDGER_TABLE} (
    app_affaire_id      INTEGER PRIMARY KEY,
    app_dossier_id      INTEGER,
    hektor_annonce_id   INTEGER,
    kind                TEXT NOT NULL,
    hektor_affaire_id   TEXT,
    hektor_mandat_id    TEXT,
    numero_mandat       TEXT,
    hektor_acquereur_id TEXT,
    app_contact_id      INTEGER,
    acquereur_json      TEXT,
    state               TEXT,
    montant             TEXT,
    date                TEXT,
    date_acte           TEXT,
    sequestre           TEXT,
    payload_json        TEXT,
    first_seen_at       TEXT,
    last_seen_at        TEXT,
    present_in_hektor   INTEGER NOT NULL DEFAULT 1
);
-- Cle de reconciliation : c'est par ce triplet qu'on reconnait, au retour de Hektor, une
-- affaire deja connue. Partiel, car une affaire nee dans l'app n'a pas encore de numero
-- Hektor et ne doit pas entrer en collision avec les autres.
CREATE UNIQUE INDEX IF NOT EXISTS idx_affaire_ledger_hektor
    ON {LEDGER_TABLE}(hektor_annonce_id, kind, hektor_affaire_id)
    WHERE hektor_affaire_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_affaire_ledger_annonce ON {LEDGER_TABLE}(hektor_annonce_id);
CREATE INDEX IF NOT EXISTS idx_affaire_ledger_dossier ON {LEDGER_TABLE}(app_dossier_id);
CREATE INDEX IF NOT EXISTS idx_affaire_ledger_acq ON {LEDGER_TABLE}(hektor_acquereur_id);
"""

# Toutes les affaires, offres INCLUSES (pas de filtre mandat : 98% des offres ont mandat_id=0).
LEDGER_SQL = """
SELECT hektor_annonce_id, hektor_mandat_id, 'offre' AS kind, hektor_offre_id AS affaire_id,
       hektor_acquereur_id AS acq_id, acquereur_json AS acq_json, offre_state AS state,
       raw_montant AS montant, COALESCE(offre_event_date, raw_date, synced_at) AS dt,
       NULL AS date_acte, NULL AS sequestre, raw_json
FROM hektor.hektor_offre WHERE hektor_annonce_id IS NOT NULL
UNION ALL
SELECT hektor_annonce_id, hektor_mandat_id, 'compromis', hektor_compromis_id,
       NULL, acquereurs_json, compromis_state,
       COALESCE(prix_publique, prix_net_vendeur), COALESCE(date_start, synced_at),
       date_signature_acte, sequestre, raw_json
FROM hektor.hektor_compromis WHERE hektor_annonce_id IS NOT NULL
UNION ALL
SELECT hektor_annonce_id, hektor_mandat_id, 'vente', hektor_vente_id,
       NULL, acquereurs_json, NULL,
       prix, COALESCE(date_vente, synced_at),
       NULL, NULL, raw_json
FROM hektor.hektor_vente WHERE hektor_annonce_id IS NOT NULL
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _open_local() -> sqlite3.Connection:
    con = sqlite3.connect(PHASE2_DB)
    con.row_factory = sqlite3.Row
    con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
    return con


def _mandat_numero(con: sqlite3.Connection) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    for row in con.execute("SELECT hektor_annonce_id, hektor_mandat_id, numero FROM hektor.hektor_mandat"):
        a, m, n = normalize_text(row[0]), normalize_text(row[1]), normalize_text(row[2])
        if a and m and n:
            out[(a, m)] = n
    return out


def refresh_ledger(con: sqlite3.Connection, *, full: bool = True) -> dict[str, int]:
    """UPSERT (delete-never) de toutes les affaires courantes dans le ledger local.
    En mode full, les lignes non revues ce run passent present_in_hektor=0 (conservées)."""
    con.executescript(DDL_SQLITE)

    # ── LA TABLE EXISTE DEJA : le CREATE ci-dessus ne l'a pas touchee ──
    #
    # CREATE TABLE IF NOT EXISTS ne fait RIEN sur une table existante -- pas meme
    # ajouter une colonne nouvelle. Sans ce rattrapage, le prochain run tomberait
    # sur « no such column: app_contact_id » et LE RUN DE NUIT ECHOUERAIT.
    # On ajoute donc la colonne si elle manque, sans rien casser si elle est la.
    colonnes = {r[1] for r in con.execute(f"PRAGMA table_info({LEDGER_TABLE})")}
    if "app_contact_id" not in colonnes:
        con.execute(f"ALTER TABLE {LEDGER_TABLE} ADD COLUMN app_contact_id INTEGER")
        con.commit()
        print(f"[affaire_ledger] colonne app_contact_id ajoutee a {LEDGER_TABLE}")
    run_ts = now_iso()
    mnum = _mandat_numero(con)

    existing_first: dict[tuple[str, str, str], str] = {}
    for row in con.execute(f"SELECT hektor_annonce_id, kind, hektor_affaire_id, first_seen_at FROM {LEDGER_TABLE}"):
        existing_first[(str(row[0]), str(row[1]), str(row[2]))] = row[3] or run_ts

    # Le numero d'affaire est distribue ici, par le serveur local, comme app_dossier.id.
    # On ne renumerote JAMAIS une ligne connue : l'ON CONFLICT ci-dessous laisse
    # app_affaire_id intact. Seules les affaires nouvelles prennent un numero.
    #
    # ⬇ 01/09/2026 -- LE RUN NE PIOCHE PLUS DANS LA PLAGE DE L'APP.
    #
    # CE QUI S'ETAIT PASSE. Deux chemins distribuent des numeros dans la MEME
    # serie, et chacun comptait a sa maniere :
    #    le run   « je prends LE PLUS GRAND + 1 »   -- il regardait TOUTE la table
    #    l'app    « je prends LE SUIVANT »          -- sequence app_affaire_id_app_seq
    #
    # Le 25/08, la premiere affaire nee dans l'app a pris 1 000 001. Le MAX de la
    # table a donc saute a un million -- et le run, qui regardait ce MAX, s'est mis
    # a compter a partir de la. Le 27/08, un rattrapage de 305 vieilles affaires
    # HEKTOR (2021-2026) a pris 1 000 008 ... 1 000 312 : la plage reservee etait
    # envahie par des affaires qui n'avaient rien a y faire.
    #
    # La sequence de l'app, elle, n'en a rien su. Restee a 1 000 017, elle a
    # continue de distribuer 1 000 018, 1 000 019... DES NUMEROS DEJA PRIS. La base
    # refusait (« duplicate key »), et le front traduisait ce refus en « une action
    # Hektor est deja en cours pour cette annonce ».
    #
    # ➡ RESULTAT : AUCUNE creation d'offre, de compromis NI de vente depuis l'app
    #   n'a pu aboutir DU 27/08 AU 01/09, sur AUCUN bien -- sous un message qui
    #   parlait d'autre chose. Trouve en testant le protocole des statuts.
    #
    # LE CORRECTIF. Le run ignore desormais la moitie haute : il repart de 28 982
    # et ne remontera plus jamais vers l'app -- il faudrait 971 000 affaires
    # nouvelles pour que la serie basse rattrape la haute.
    #
    # ON NE TOUCHE PAS AUX 323 DEJA PLACEES. Elles sont coherentes des deux cotes
    # (empreinte md5 identique local/Supabase, zero doublon), et AUCUN code ne lit
    # le seuil -- il n'apparait que dans des commentaires. Les renumeroter
    # violerait la regle du projet (« un dossier ne perd jamais son numero ») pour
    # corriger une gene devenue documentaire.
    next_affaire_id = (con.execute(
        f"SELECT COALESCE(MAX(app_affaire_id), 0) FROM {LEDGER_TABLE} WHERE app_affaire_id < ?",
        (PLAGE_RESERVEE_APP,),
    ).fetchone()[0]) + 1

    # ------------------------------------------------------------------ C.4 25/08
    # LES AFFAIRES NEES DANS L'APP, A ADOPTER PLUTOT QU'A DUPLIQUER.
    #
    # Depuis C.4, une offre / un compromis / une vente peut naitre DANS L'APP : elle prend
    # un numero de la plage reservee (>= 1 000 000), sa case Hektor reste VIDE, et
    # present_in_hektor vaut false. Elle vit d'abord dans Supabase seulement.
    #
    # Quand Hektor l'enregistre enfin, ce run la voit arriver comme une affaire NEUVE. Sans
    # la regle ci-dessous, il lui donnerait un SECOND numero -- et la meme vente
    # existerait deux fois dans ton registre.
    #
    # LA CLE D'ADOPTION EST (annonce, type, ACQUEREUR), et pas le mandat : 98 % des offres
    # n'ont pas de mandat, et c'est deja ainsi que les offres, compromis et ventes sont
    # chaines dans ce projet.
    #
    # ON N'ADOPTE QUE SI C'EST SUR : il faut un acquereur, et une seule candidate. En cas
    # d'ambiguite on laisse le numero neuf partir -- deux lignes visibles valent mieux
    # qu'une fusion silencieuse sur une vente.
    #
    # La source est la DOUBLURE descendue chaque matin (app_affaire_ledger__sb) : la table
    # locale, elle, ne connait pas encore ces affaires.
    # ── ADOPTION PAR LE TRIPLET (02/09/2026) ──────────────────────────
    #
    # POURQUOI ELLE A FALLU. Le run du 02/09 a PLANTE ici meme :
    #     Supabase REST error 409 -- Key (24933, offre, 33037) already exists
    #     violates unique constraint "idx_app_affaire_ledger_hektor"
    # et tout ce qui suivait dans le pipeline n'a pas tourne -- dont le push
    # principal vers Supabase, laissant l'app 18 h en arriere.
    #
    # DEUX CAUSES CUMULEES :
    #   1. la doublure consultee datait de la descente de LA VEILLE ; l'offre
    #      creee a 13h18 n'y figurait pas du tout ;
    #   2. et meme presente, elle n'aurait pas ete adoptable : depuis le
    #      01/09 le worker lui pose son numero Hektor en QUINZE SECONDES
    #      (poserIdTransactionSurAffaire), donc elle n'est plus « orpheline »
    #      et le filtre ci-dessous ne la voyait plus.
    # Le commentaire du worker disait « ecrire le numero ici supprime la
    # condition : l'adoption devient inutile ». Elle ne devient pas inutile,
    # ELLE DEVIENT IMPOSSIBLE -- et le run se met a fabriquer un doublon.
    #
    # LE TRIPLET EST LA CLE LA PLUS SURE QU'ON AIT : c'est deja l'unicite de la
    # table (idx_app_affaire_ledger_hektor), celle-la meme qui a fait planter le
    # run. Deux lignes ne peuvent pas le partager -- aucune ambiguite n'est
    # possible, contrairement a l'adoption par acquereur qui doit compter ses
    # candidates. Si la doublure dit que ce triplet porte le numero 1 001 324,
    # c'est que cette ligne EST cette affaire.
    #
    # (La cause 1 se traite ailleurs : le pipeline descend desormais la doublure
    #  juste avant cette etape.)
    adoptables_par_triplet: dict[tuple[str, str, str], int] = {}
    try:
        for a_id, a_kind, a_hid, a_num in con.execute(
            """SELECT hektor_annonce_id, kind, hektor_affaire_id, app_affaire_id
                 FROM app_affaire_ledger__sb
                WHERE hektor_affaire_id IS NOT NULL
                  AND TRIM(CAST(hektor_affaire_id AS TEXT)) <> ''"""
        ):
            adoptables_par_triplet[(str(a_id), str(a_kind), str(a_hid))] = int(a_num)
    except sqlite3.OperationalError:
        # La doublure n'existe pas encore (descente jamais lancee) : rien a adopter.
        adoptables_par_triplet = {}

    adoptables: dict[tuple[str, str, str], int] = {}
    ambigus: set[tuple[str, str, str]] = set()
    try:
        for a_id, a_kind, a_acq, a_num in con.execute(
            """SELECT hektor_annonce_id, kind, hektor_acquereur_id, app_affaire_id
                 FROM app_affaire_ledger__sb
                WHERE (hektor_affaire_id IS NULL OR TRIM(CAST(hektor_affaire_id AS TEXT)) = '')
                  AND CAST(present_in_hektor AS TEXT) IN ('0', 'false', 'False')
                  AND hektor_acquereur_id IS NOT NULL
                  AND TRIM(CAST(hektor_acquereur_id AS TEXT)) <> ''"""
        ):
            cle = (str(a_id), str(a_kind), str(a_acq))
            if cle in adoptables:
                ambigus.add(cle)          # deux candidates : on n'adopte plus
            else:
                adoptables[cle] = int(a_num)
        for cle in ambigus:
            adoptables.pop(cle, None)
    except sqlite3.OperationalError:
        # La doublure n'existe pas encore (descente jamais lancee) : rien a adopter.
        adoptables = {}
    adoptees = 0

    dossier_par_annonce: dict[str, int] = {
        str(a): int(i) for i, a in con.execute(
            "SELECT id, hektor_annonce_id FROM app_dossier WHERE hektor_annonce_id IS NOT NULL"
        )
    }

    # ── L'ACQUEREUR PAR LE NUMERO DE L'APP (01/09/2026) ──────────────────
    #
    # SOULEVE PAR FREDERIC : « les ids Hektor etant les axes, il y aura un
    # probleme lors de la coupure ». Le lien entre une vente et son ACHETEUR ne
    # passait que par hektor_acquereur_id -- le seul lien du projet qui ne fut
    # pas double. Il etait DEJA rompu pour 2 802 affaires (9,7 %) : il ne restait
    # d'elles que acquereur_json, le nom sans le lien.
    #
    # `app_contact` est la doublure d'identite des contacts : elle n'est jamais
    # reconstruite, c'est elle qui porte le numero que nous donnons aux gens.
    # Si elle n'existe pas encore, on continue sans -- la colonne reste vide, et
    # le COALESCE de l'ON CONFLICT garantit qu'on n'efface jamais un rattachement
    # deja etabli.
    contact_app_par_hektor: dict[str, int] = {}
    try:
        for h, a in con.execute(
            "SELECT hektor_contact_id, app_contact_id FROM app_contact "
            "WHERE hektor_contact_id IS NOT NULL AND app_contact_id IS NOT NULL"
        ):
            contact_app_par_hektor[str(h).strip()] = int(a)
    except sqlite3.OperationalError:
        contact_app_par_hektor = {}

    seen = 0
    inserted = 0
    for r in con.execute(LEDGER_SQL):
        annonce = normalize_text(r["hektor_annonce_id"])
        affaire_id = normalize_text(r["affaire_id"])
        kind = normalize_text(r["kind"])
        if not (annonce and affaire_id and kind):
            continue
        mid = normalize_text(r["hektor_mandat_id"])
        party = _compact_party(r["acq_json"])
        acq_id = normalize_text(r["acq_id"]) or (normalize_text(party.get("id")) if party else "")
        numero = mnum.get((annonce, mid), "") if mid and mid != "0" else ""
        key = (annonce, kind, affaire_id)
        first_seen = existing_first.get(key, run_ts)
        nouvelle = key not in existing_first
        if nouvelle:
            inserted += 1
        # Numero propose : ignore par SQLite si la ligne existe deja (DO UPDATE ne le touche pas).
        # On n'avance le compteur que pour une affaire reellement nouvelle.
        propose = next_affaire_id
        if nouvelle:
            # C.4 : si l'app a deja cree cette affaire, on REPREND son numero au lieu
            # d'en distribuer un neuf. Une adoption ne sert qu'une fois.
            #
            # DEUX CHEMINS, LE PLUS SUR D'ABORD :
            #   1. par le TRIPLET -- l'affaire porte deja son numero Hektor, donc
            #      c'est EXACTEMENT elle. Aucune ambiguite possible.
            #   2. par l'ACQUEREUR -- elle n'a pas encore de numero Hektor. On
            #      n'adopte que si une seule candidate, comme avant.
            adopte = adoptables_par_triplet.get((annonce, kind, affaire_id))
            if adopte is None and acq_id:
                adopte = adoptables.pop((annonce, kind, acq_id), None)
            if adopte is not None:
                propose = adopte
                adoptees += 1
            else:
                next_affaire_id += 1
        con.execute(
            f"""
            INSERT INTO {LEDGER_TABLE}(app_affaire_id, app_dossier_id,
                hektor_annonce_id, kind, hektor_affaire_id, hektor_mandat_id,
                numero_mandat, hektor_acquereur_id, app_contact_id, acquereur_json, state, montant, date, date_acte,
                sequestre, payload_json, first_seen_at, last_seen_at, present_in_hektor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(hektor_annonce_id, kind, hektor_affaire_id)
              WHERE hektor_affaire_id IS NOT NULL DO UPDATE SET
                app_dossier_id=excluded.app_dossier_id,
                hektor_mandat_id=excluded.hektor_mandat_id,
                numero_mandat=excluded.numero_mandat,
                hektor_acquereur_id=excluded.hektor_acquereur_id,
                -- VIDE NE GAGNE PAS : un contact que l'app ne connait pas encore
                -- ne doit pas effacer un rattachement deja etabli.
                app_contact_id=COALESCE(excluded.app_contact_id, {LEDGER_TABLE}.app_contact_id),
                acquereur_json=excluded.acquereur_json,
                state=excluded.state, montant=excluded.montant, date=excluded.date,
                date_acte=excluded.date_acte, sequestre=excluded.sequestre,
                payload_json=excluded.payload_json,
                last_seen_at=excluded.last_seen_at, present_in_hektor=1
            """,
            (
                propose, dossier_par_annonce.get(annonce),
                int(annonce), kind, affaire_id, mid or None, numero or None, acq_id or None,
                contact_app_par_hektor.get(acq_id) if acq_id else None,
                json.dumps(party, ensure_ascii=True, separators=(",", ":")) if party else None,
                normalize_text(r["state"]) or None, normalize_text(r["montant"]) or None,
                normalize_text(r["dt"]) or None, normalize_text(r["date_acte"]) or None,
                normalize_text(r["sequestre"]) or None, normalize_text(r["raw_json"]) or None,
                first_seen, run_ts,
            ),
        )
        seen += 1

    if adoptees:
        print(f"[affaire_ledger] {adoptees} affaire(s) nee(s) dans l'app ADOPTEE(S) "
              f"au lieu d'etre dupliquee(s)")
    absent = 0
    if full:
        cur = con.execute(f"UPDATE {LEDGER_TABLE} SET present_in_hektor=0 WHERE last_seen_at <> ?", (run_ts,))
        absent = cur.rowcount or 0
    con.commit()
    total = con.execute(f"SELECT COUNT(*) FROM {LEDGER_TABLE}").fetchone()[0]
    return {"seen": seen, "inserted": inserted, "marked_absent": absent, "ledger_total": total}


def ledger_rows_for_push(con: sqlite3.Connection) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for r in con.execute(f"SELECT * FROM {LEDGER_TABLE}"):
        d = dict(r)
        for jcol in ("acquereur_json", "payload_json"):
            v = d.get(jcol)
            if isinstance(v, str) and v:
                try:
                    d[jcol] = json.loads(v)
                except Exception:
                    d[jcol] = None
        d["present_in_hektor"] = bool(d.get("present_in_hektor"))
        rows.append(d)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh + push du ledger d'affaires (Niveau B).")
    parser.add_argument("--refresh", action="store_true", help="UPSERT local depuis le miroir Hektor.")
    parser.add_argument("--push", action="store_true", help="UPSERT vers Supabase (delete-never).")
    parser.add_argument("--batch-size", type=int, default=200)
    args = parser.parse_args()
    if not (args.refresh or args.push):
        args.refresh = args.push = True  # backfill par défaut

    con = _open_local()
    result: dict[str, object] = {}
    if args.refresh:
        result["refresh"] = refresh_ledger(con, full=True)
    if args.push:
        load_env_files(DEFAULT_ENV_FILES)
        url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not (url and key):
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
        client = SupabaseRestClient(base_url=url, service_role_key=key)
        rows = ledger_rows_for_push(con)
        client.upsert_rows(path=LEDGER_TABLE, rows=rows, batch_size=args.batch_size)
        result["push"] = {"rows_pushed": len(rows)}
    con.close()
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
