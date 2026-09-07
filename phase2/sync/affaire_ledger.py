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
    -- 1.1 (03/09/2026) : LE DOSSIER D'AFFAIRE. L'offre, le compromis et la vente
    -- d'un MEME acquereur sur une MEME annonce partagent ce numero. Il est FRAPPE
    -- par une sequence, jamais calcule -- « deux copies d'une formule divergent tot
    -- ou tard ». Hektor ne le connait pas : rien a arbitrer, personne a contredire.
    -- ⚠ IL N'EST PAS DANS LE « ON CONFLICT DO UPDATE SET » plus bas, ET C'EST VOULU :
    --   ce que le run ne reecrit pas, il le preserve. C'est la protection par
    --   omission, celle des trois champs de contact.
    app_chaine_id       INTEGER,
    acquereur_json      TEXT,
    -- 1.8 (04/09/2026) : TOUS LES ACQUEREURS, pas seulement le premier.
    -- Frederic : « si on a les donnees en brut, pourquoi en garder juste un ? »
    -- _compact_party() fait obj[0] -- ecrit pour AFFICHER une partie, puis
    -- reutilise pour fabriquer la ligne du registre. Resultat mesure le 04/09 :
    -- 4 536 acquereurs presents chez Hektor et invisibles ici (2 993 sur les
    -- compromis, 1 543 sur les ventes). 17,1 % des compromis en portent
    -- plusieurs, et UN SUR QUATRE parmi les recents.
    -- ⚠ COLONNE ADDITIVE : acquereur_json garde le principal, pour que le front
    --   ne casse pas. Sa migration est la part « ecran » de 1.8.
    acquereurs_json     TEXT,
    -- 1.2 (03/09/2026) : LES CHAMPS QUE HEKTOR IGNORE -- CLASSE A.
    -- Hektor n'a AUCUNE destination pour eux (campagne 0.1). Zero conflit
    -- possible : il n'a rien a dire. Ces colonnes sont donc ECRITES PAR L'APP
    -- SEULE, dans Supabase. Le local ne les invente pas, ne les pousse pas
    -- (COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS) et ne les reecrit pas (absentes du
    -- ON CONFLICT DO UPDATE SET). Il les RECOIT apres le push, pour que la
    -- sauvegarde de nuit les emporte.
    -- ⚠ jours_validite A QUITTE LA CLASSE A LE 07/09 (1.2b). Il est reste sous
    --   ce commentaire deux jours de trop : Hektor le GARDE, dans la proposition
    --   de l'OFFRE, la ou l'app le saisit. Il est desormais relu a chaque run,
    --   comme date_fin_retractation juste en dessous.
    jours_validite      TEXT,
    -- Ceux-la restent de classe A, verifie sur la charge reelle de l'offre :
    -- aucune destination, ni dans l'offre ni dans la proposition.
    taux_honoraires     TEXT,
    notaire_id          TEXT,
    -- ⚠ CELLE-CI N'EST PAS DE CLASSE A, ET C'EST UNE CORRECTION DU 03/09.
    -- 0.1 rangeait jours_retractation en classe A, alors que sa propre mesure
    -- disait « retraction_days 10 -> dateEnd, B mais CONVERTI ». Hektor CONNAIT
    -- ce delai : il en garde la DATE de fin. Le figer dans une colonne protegee,
    -- ce serait LE GEL que Frederic avait repere le premier. On relit donc la
    -- date chez Hektor a chaque run, et le nombre de jours SE DEDUIT (fin - date)
    -- au lieu d'etre stocke une deuxieme fois.
    date_fin_retractation TEXT,
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
       hektor_acquereur_id AS acq_id, acquereur_json AS acq_json, acquereur_json AS acq_tous,
       offre_state AS state,
       raw_montant AS montant, COALESCE(offre_event_date, raw_date, synced_at) AS dt,
       NULL AS date_acte, NULL AS sequestre, NULL AS date_fin,
       -- 1.2b (07/09/2026) : LA VALIDITE EST DE CLASSE B, PAS A -- ma faute.
       -- Hektor la garde, dans la PROPOSITION de l'offre. Preuve sans nouvel
       -- essai, les six offres de 24933 lues en direct : 10, 10, 20, 20, 15, 10.
       -- Trois valeurs distinctes : il garde ce qu'on lui envoie.
       -- 0.1 avait conclu « aucun champ » en mesurant sur un COMPROMIS et en
       -- generalisant aux trois genres -- exactement la faute corrigee la veille
       -- sur jours_retractation, et que j'ai reproduite.
       -- ⚠ « 0 » VEUT DIRE VIDE, comme partout chez Hektor (le projet le sait
       --   depuis le DPE). Mesure du 07/09 sur le miroir : 10 811 offres sur
       --   11 083 portent « 0 », et 271 seulement une vraie valeur.
       NULLIF(json_extract(propositions_json, '$[0].validite'), '0') AS validite,
       raw_json
FROM hektor.hektor_offre WHERE hektor_annonce_id IS NOT NULL
UNION ALL
SELECT hektor_annonce_id, hektor_mandat_id, 'compromis', hektor_compromis_id,
       NULL, acquereurs_json, acquereurs_json, compromis_state,
       COALESCE(prix_publique, prix_net_vendeur), COALESCE(date_start, synced_at),
       date_signature_acte, sequestre,
       -- CLASSE B : la fin du delai de retractation, telle que HEKTOR la porte.
       -- C'est elle qui fait foi ; le nombre de jours s'en deduit.
       date_end,
       NULL AS validite,          -- la validite ne concerne QUE l'offre
       raw_json
FROM hektor.hektor_compromis WHERE hektor_annonce_id IS NOT NULL
UNION ALL
SELECT hektor_annonce_id, hektor_mandat_id, 'vente', hektor_vente_id,
       NULL, acquereurs_json, acquereurs_json, NULL,
       prix, COALESCE(date_vente, synced_at),
       NULL, NULL, NULL,
       NULL AS validite,          -- idem
       raw_json
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
    if "app_chaine_id" not in colonnes:
        con.execute(f"ALTER TABLE {LEDGER_TABLE} ADD COLUMN app_chaine_id INTEGER")
        con.commit()
        print(f"[affaire_ledger] colonne app_chaine_id ajoutee a {LEDGER_TABLE}")
    for neuve in ("jours_validite", "taux_honoraires", "notaire_id",
                  "date_fin_retractation", "acquereurs_json"):
        if neuve not in colonnes:
            con.execute(f"ALTER TABLE {LEDGER_TABLE} ADD COLUMN {neuve} TEXT")
            con.commit()
            print(f"[affaire_ledger] colonne {neuve} ajoutee a {LEDGER_TABLE}")
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
                numero_mandat, hektor_acquereur_id, app_contact_id, acquereur_json, acquereurs_json,
                state, montant, date, date_acte,
                sequestre, date_fin_retractation, jours_validite,
                payload_json, first_seen_at, last_seen_at, present_in_hektor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
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
                acquereurs_json=excluded.acquereurs_json,
                state=excluded.state, montant=excluded.montant, date=excluded.date,
                date_acte=excluded.date_acte, sequestre=excluded.sequestre,
                date_fin_retractation=excluded.date_fin_retractation,
                -- 1.2b : jours_validite EST RELU A CHAQUE RUN. Il etait absent de
                -- cette liste tant qu'on le croyait de classe A -- « protection par
                -- omission ». Il ne l'est plus : Hektor le connait, donc Hektor fait
                -- foi, et le figer serait exactement le gel que 1.2 avait evite sur
                -- jours_retractation.
                jours_validite=excluded.jours_validite,
                payload_json=excluded.payload_json,
                last_seen_at=excluded.last_seen_at, present_in_hektor=1
            """,
            (
                propose, dossier_par_annonce.get(annonce),
                int(annonce), kind, affaire_id, mid or None, numero or None, acq_id or None,
                contact_app_par_hektor.get(acq_id) if acq_id else None,
                json.dumps(party, ensure_ascii=True, separators=(",", ":")) if party else None,
                normalize_text(r["acq_tous"]) or None,     # 1.8 : la liste ENTIERE, telle que Hektor la donne
                normalize_text(r["state"]) or None, normalize_text(r["montant"]) or None,
                normalize_text(r["dt"]) or None, normalize_text(r["date_acte"]) or None,
                normalize_text(r["sequestre"]) or None,
                normalize_text(r["date_fin"]) or None,
                normalize_text(r["validite"]) or None,     # 1.2b : classe B, relue
                normalize_text(r["raw_json"]) or None,
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
    # ─── LES CHAINES SE RECALCULENT ICI, ENTIEREMENT, A CHAQUE RUN (04/09) ───
    # Frederic : « le run doit actualiser les chaines comme l'app le ferait ».
    # Une chaine n'est pas une saisie mais une DEDUCTION : on la refait a neuf
    # plutot que de la conserver. Cout mesure : 0,09 s sur 29 321 lignes.
    # Ce qui remplace l'ancien dispositif -- une sequence chez Supabase, et une
    # colonne protegee que le run n'avait pas le droit de toucher.
    chaines = recalculer_les_chaines(con)
    total = con.execute(f"SELECT COUNT(*) FROM {LEDGER_TABLE}").fetchone()[0]
    return {"seen": seen, "inserted": inserted, "marked_absent": absent,
            "ledger_total": total, "chaines": chaines}


ETATS_OFFRE_MORTS = {"refused", "refusee"}
ETATS_OFFRE_ACCEPTEE = {"accepted", "acceptee"}
ETATS_COMPROMIS_MORTS = {"cancelled", "annule"}
ORDRE_DES_BLOCS = {"offre": 0, "compromis": 1, "vente": 2}


def _date_utile(valeur: object) -> str | None:
    """Une date exploitable pour ordonner les blocs, ou rien.

    ⚠ 224 transactions du parc portent une date inexploitable (203 vides ou
    « 0000-00-00 », 7 en 1990, 14 offres sans date). Sans date, on ne peut dire ni
    ce qui precede ni ce qui suit : ces transactions ouvrent leur propre chaine et
    n'en rejoignent jamais aucune. Decision de Frederic le 04/09 : « on peut tenter
    de les rattacher a la main, mais pas dans la regle. »
    """
    texte = normalize_text(valeur)[:10] if valeur is not None else ""
    if len(texte) != 10:
        return None
    try:
        annee = int(texte[:4])
    except ValueError:
        return None
    return texte if 2000 <= annee <= 2030 else None


def _acquereurs(brut: object) -> set[str]:
    """Les identifiants de TOUS les acquereurs d'une transaction (1.8)."""
    if isinstance(brut, str):
        try:
            brut = json.loads(brut)
        except Exception:
            return set()
    if isinstance(brut, dict):
        brut = [brut]
    if not isinstance(brut, list):
        return set()
    out: set[str] = set()
    for item in brut:
        if isinstance(item, dict):
            ident = normalize_text(item.get("id"))
            if ident and ident != "0":
                out.add(ident)
    return out


def recalculer_les_chaines(con: sqlite3.Connection) -> dict[str, int]:
    """LA REGLE DE CHAINAGE -- refondue le 04/09/2026 par Frederic.

    ═══ CE QU'ELLE REMPLACE, ET POURQUOI ═══

    La premiere version (1.1, 03/09) regroupait par (annonce, acquereur). Elle
    partait d'une idee juste mais fausse : qu'une affaire se reconnait a QUI achete.
    Mesures du 04/09 sur le parc entier :
        1 034 ventes isolees alors que leur compromis etait sur la meme annonce
          109 d'entre elles au MEME NOM DE FAMILLE (un couple, un doublon de contact)
          386 transactions sans aucun acquereur, donc chacune seule
    L'identite de l'acheteur CHANGE d'une etape a l'autre : l'offre au nom de
    Monsieur, le compromis aux deux noms, l'acte au nom de Madame. Trois fois la
    meme affaire, trois dossiers.

    QUATRE AUTRES PISTES ONT ETE MESUREES ET ECARTEES -- ne pas les refaire :
        le croisement des listes completes  +56 chaines sur 13 348 seulement
        le montant + la chronologie         99,7 % MAIS 149 ambiguites, dont
                                            145 du scenario que Frederic a decrit :
                                            deux compromis au meme prix, un annule
        le mandat                           412 annonces ont UN mandat et PLUSIEURS
                                            acquereurs : il les fusionnerait a tort
        la periode de mandat                ne departage que 4 des 41 ambiguites

    ═══ LA REGLE, DANS LES MOTS DE FREDERIC ═══

        « Une chaine c'est trois blocs, ou deux, ou un seul. Par logique un
          compromis est clos soit quand il est annule soit quand la vente est
          passee. Une vente est close quand elle est passee, sinon supprimee.
          L'etat ferme la chaine, pour permettre d'en ouvrir une autre. »

    Une affaire n'est donc PAS une identite : c'est une SEQUENCE OUVERTE sur un
    bien. Chaque bloc rejoint le precedent encore vivant.

        OUVRE   une offre (une chaine par acquereur)
                un compromis qui ne trouve pas d'offre acceptee ouverte
                une vente qui ne trouve pas de compromis ouvert

        FERME   la VENTE            -- l'affaire a abouti
                l'offre REFUSEE     -- l'affaire est morte
                le compromis ANNULE -- l'affaire est morte

        Une chaine fermee ne recoit plus jamais rien.

    ⚠ C'EST CE QUI REGLE LA REVENTE, sans avoir besoin du mandat. Un bien vendu en
      2020 puis remis en vente en 2026 : la chaine de 2020 est fermee par sa vente,
      la nouvelle offre ne peut qu'en ouvrir une seconde -- meme si c'est le MEME
      acheteur qui rachete. Mesure du 04/09 : 7 507 compromis sont anterieurs a une
      vente et TOUJOURS marques actifs chez Hektor, parce que personne ne les clot
      apres l'acte. Sans la fermeture par la vente, ils seraient tous candidats.

    ═══ LE NUMERO DE LA CHAINE ═══

    C'est le PLUS PETIT app_affaire_id de ses transactions -- autrement dit, le
    numero de celle qui l'a ouverte. Ni sequence, ni compteur :
      * stable   -- il ne bouge pas tant que la premiere transaction reste en tete
      * unique   -- une transaction n'appartient qu'a une chaine
      * refaisable -- le run recalcule tout chaque nuit et retombe sur les memes
                    numeros, sans etat a conserver
    Frederic, 04/09 : « le run doit actualiser les chaines comme l'app le ferait ».
    Une chaine n'est pas une saisie, c'est une DEDUCTION -- et une deduction se
    refait. Cout mesure d'un recalcul complet : 0,09 s sur 29 321 lignes.

    ⚠ RESERVE ASSUMEE : on raisonne sur l'etat FINAL de chaque transaction, pas sur
      son etat au moment des faits. Une offre aujourd'hui « refusee » a pu etre
      acceptee d'abord. L'historique existe (les `propositions` de chaque offre
      portent chaque evenement date) : s'en servir affinerait le resultat, jamais
      ne le degraderait. A faire quand le besoin s'en fera sentir.
    """
    # ─── CE QUE HEKTOR A EFFACE NE COMPTE PLUS DANS LA CHAINE (07/09/2026) ───
    #
    # Jusqu'ici cette requete lisait TOUT le registre, sans regarder
    # present_in_hektor. C'etait sans consequence tant que le drapeau ne se
    # levait jamais -- mesure du 07/09 : 0 ligne sur 29 327, des deux cotes.
    # Le miroir ne perdant rien, refresh_ledger revoyait toujours tout.
    #
    # ⚠ MAIS LE REMPLACEMENT DU MIROIR REVEILLE CE DEFAUT. Des que le miroir
    #   cesse de garder ce que Hektor a efface, le drapeau se leve pour de vrai,
    #   et une vente irait se rattacher a un compromis QUI N'EXISTE PLUS
    #   (`compromis_vivant` le compterait encore). D'ou cette correction AVANT.
    #
    # ⚠ ET LE FILTRE NAIF EST FAUX. « WHERE present_in_hektor » exclurait aussi
    #   les transactions NEES DANS L'APP : elles portent present_in_hektor=false
    #   ET aucun numero Hektor jusqu'a ce que le run les adopte. Une offre creee
    #   le matin perdrait son dossier jusqu'au lendemain.
    #   La regle est donc celle de l'ecran, mot pour mot (affaireEstVivante) :
    #
    #       exclure SI  (elle porte un numero Hektor)  ET  (present_in_hektor faux)
    #       pas de numero = nee chez nous = VIVANTE
    #
    # ⚠ ON NE REMET PAS app_chaine_id A NULL pour les exclues : elles ne sont
    #   simplement plus dans `attribution`, donc leur numero de chaine reste tel
    #   quel. La trace garde son dossier -- c'est voulu, on veut pouvoir dire
    #   « cette vente appartenait au dossier 12 648 », meme effacee chez Hektor.
    lignes = list(con.execute(f"""
        SELECT app_affaire_id, hektor_annonce_id, kind, state, date, acquereurs_json
          FROM {LEDGER_TABLE}
         WHERE NOT (
                   TRIM(COALESCE(CAST(hektor_affaire_id AS TEXT), '')) <> ''
               AND CAST(present_in_hektor AS TEXT) IN ('0', 'false', 'False')
               )
    """))
    par_annonce: dict[str, list[tuple]] = {}
    for app_id, annonce, kind, state, date, acq in lignes:
        par_annonce.setdefault(normalize_text(annonce), []).append(
            (int(app_id), normalize_text(kind), normalize_text(state).lower(),
             _date_utile(date), _acquereurs(acq))
        )

    attribution: dict[int, int] = {}
    anomalies: dict[str, int] = {}
    sans_date = 0

    def signale(quoi: str) -> None:
        anomalies[quoi] = anomalies.get(quoi, 0) + 1

    for annonce, items in par_annonce.items():
        # sans date : chacune sa chaine, elle-meme, et on n'y revient plus
        for app_id, kind, state, date, acqs in items:
            if date is None:
                attribution[app_id] = app_id
                sans_date += 1

        datees = sorted((x for x in items if x[3] is not None),
                        key=lambda y: (y[3], ORDRE_DES_BLOCS.get(y[1], 9), y[0]))
        ouvertes: list[dict] = []   # les chaines encore OUVERTES de ce bien
        toutes: list[dict] = []     # toutes celles du bien, pour numeroter a la fin

        def ouvrir(app_id: int, acqs: set[str]) -> dict:
            chaine = {"membres": [app_id], "acquereurs": set(acqs),
                      "offre_acceptee": False, "compromis": False}
            ouvertes.append(chaine)
            toutes.append(chaine)
            return chaine

        for app_id, kind, state, date, acqs in datees:
            if kind == "offre":
                # une chaine par acquereur -- plusieurs offres coexistent, c'est normal
                cible = next((c for c in ouvertes
                              if not c["compromis"] and (acqs & c["acquereurs"])), None)
                if cible is None:
                    cible = ouvrir(app_id, acqs)
                else:
                    cible["membres"].append(app_id)
                    cible["acquereurs"] |= acqs
                if state in ETATS_OFFRE_ACCEPTEE:
                    cible["offre_acceptee"] = True
                elif state in ETATS_OFFRE_MORTS:
                    ouvertes.remove(cible)          # l'etat FERME la chaine

            elif kind == "compromis":
                candidates = [c for c in ouvertes if c["offre_acceptee"] and not c["compromis"]]
                if len(candidates) == 1:
                    cible = candidates[0]
                    cible["membres"].append(app_id)
                else:
                    if len(candidates) > 1:
                        signale("plusieurs chaines a offre acceptee")
                    cible = ouvrir(app_id, acqs)
                cible["compromis"] = True
                cible["acquereurs"] |= acqs
                if state in ETATS_COMPROMIS_MORTS:
                    ouvertes.remove(cible)          # annule : la chaine est close

            else:  # vente -- elle ferme toujours la chaine qu'elle rejoint
                candidates = [c for c in ouvertes if c["compromis"]]
                if len(candidates) == 1:
                    cible = candidates[0]
                    cible["membres"].append(app_id)
                    ouvertes.remove(cible)
                else:
                    # ON NE DEVINE PAS. La vente reste seule, et on le DIT.
                    signale("vente : plusieurs compromis ouverts" if candidates
                            else "vente sans compromis ouvert")
                    ouvrir(app_id, acqs)

        # ⚠ ON NUMEROTE A LA FIN, ET C'EST INDISPENSABLE. Le numero d'une chaine est
        # le plus petit app_affaire_id de ses membres -- or une transaction au numero
        # plus bas peut la rejoindre APRES coup. Numeroter au fil de l'eau laissait
        # les premiers membres avec l'ancien numero : mesure du 05/09, 21 710 chaines
        # au lieu de 12 648, soit 9 000 dossiers coupes en deux.
        for chaine in toutes:
            tete = min(chaine["membres"])
            for membre in chaine["membres"]:
                attribution[membre] = tete

    con.executemany(f"UPDATE {LEDGER_TABLE} SET app_chaine_id=? WHERE app_affaire_id=?",
                    [(chaine, app_id) for app_id, chaine in attribution.items()])
    con.commit()
    resultat = {"transactions": len(attribution),
                "chaines": len(set(attribution.values())),
                "sans_date": sans_date}
    resultat.update(anomalies)
    return resultat


def redescendre_ce_que_l_app_possede(client, con: sqlite3.Connection) -> dict[str, int]:
    """1.1 -- LE DOSSIER D'AFFAIRE : un numero par (annonce, acquereur).

    L'offre, le compromis et la vente d'un meme acquereur sur une meme annonce
    partagent ce numero. Il est FRAPPE par une sequence, jamais calcule -- « deux
    copies d'une formule divergent tot ou tard ». Hektor ne le connait pas : rien
    a arbitrer, personne a contredire.

    IL N'Y A QU'UN SEUL FRAPPEUR, ET CE N'EST PAS CE SCRIPT.
    C'est Supabase, parce que c'est la que l'APP pose deja les siens au moment du
    geste. Une premiere version frappait ici, localement, a partir du MAX() de la
    table locale -- encore vide. Elle aurait redemarre a 1 pendant que Supabase en
    etait a 13 347 : deux series pour une meme chose, la faute que le projet
    s'interdit depuis le debut.

    LE RUN FAIT DONC DEUX GESTES, DANS CET ORDRE, ET APRES LE PUSH :
      1. il demande a Supabase de combler les trous (les transactions creees DANS
         Hektor arrivent sans chaine -- l'app n'etait pas la pour leur en poser une) ;
      2. il redescend le resultat dans la colonne locale.

    POURQUOI REDESCENDRE. La colonne locale n'est jamais poussee (voir
    COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS) : elle ne sert pas a ecrire, elle sert a ce
    que la sauvegarde de nuit emporte aussi cette connaissance. La chaine est de la
    donnee app-owned que Hektor ne saura JAMAIS reconstruire -- en particulier
    celles que l'app pose au geste, qui disent de quelle offre un compromis est ne.
    """
    posees = client._request(method="POST", path="rpc/app_attribuer_chaines_affaire")
    if isinstance(posees, list) and posees:
        posees = posees[0]
    posees = int(posees or 0)
    if posees:
        print(f"[affaire_ledger] {posees} affaire(s) rattachee(s) a un dossier d'affaire")

    # On redescend TOUT ce que l'app possede -- la chaine et les champs de classe A.
    # Le local ne s'en sert pas pour ecrire ; il les garde pour que la sauvegarde de
    # nuit emporte aussi cette connaissance, que Hektor ne saura jamais reconstruire.
    colonnes = list(COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS)
    lignes = client.fetch_all_rows(path=LEDGER_TABLE,
                                   select="app_affaire_id," + ",".join(colonnes),
                                   order="app_affaire_id.asc")
    consigne = (f"UPDATE {LEDGER_TABLE} SET " + ", ".join(f"{c}=?" for c in colonnes)
                + " WHERE app_affaire_id=?")
    valeurs = [tuple(l.get(c) for c in colonnes) + (l.get("app_affaire_id"),)
               for l in lignes if l.get("app_affaire_id") is not None]
    con.executemany(consigne, valeurs)
    con.commit()
    manquantes = con.execute(
        f"SELECT COUNT(*) FROM {LEDGER_TABLE} WHERE app_chaine_id IS NULL").fetchone()[0]
    return {"chainees_par_supabase": posees, "lignes_redescendues": len(valeurs),
            "colonnes_redescendues": len(colonnes), "locales_sans_chaine": manquantes}


# ─── CE QUE LE PUSH N'ENVOIE PAS, ET C'EST VITAL ───
#
# `SELECT *` envoie TOUTES les colonnes, et l'upsert PostgREST REMPLACE la ligne.
# Une colonne que le local ne sait pas remplir ecraserait donc sa valeur chez
# Supabase -- en silence, et pour les 29 320 lignes d'un coup.
#
# app_chaine_id est exactement ce cas (03/09/2026) : c'est SUPABASE qui frappe ces
# numeros, parce que c'est la que l'app pose les siens au moment du geste. Le local,
# lui, n'en sait rien. S'il les poussait, il les effacerait.
#
# UN SEUL EMETTEUR A LA FOIS -- la regle est ancienne (note d'identite du 08/08,
# retiree du git le 19/08) : « Pendant la transition, un seul minte. Jamais les deux
# en meme temps. » Ici l'emetteur est Supabase, et le local n'a rien a dire.
# Les colonnes de CLASSE A rejoignent la liste pour la meme raison exactement :
# c'est l'app qui les ecrit, chez Supabase, et le local ne les connait pas. Les
# pousser reviendrait a envoyer des NULL par-dessus des valeurs saisies.
# date_fin_retractation N'EN EST PAS : celle-la, Hektor la connait et le local la
# lit dans le miroir -- elle se pousse et se rafraichit comme les autres.
# ⚠ app_chaine_id A QUITTE CETTE LISTE LE 04/09. Elle y etait parce que Supabase
# frappait les numeros et que le local ne les connaissait pas. Depuis la refonte de
# la regle (recalculer_les_chaines), c'est LE LOCAL qui les calcule, a chaque run,
# pour toutes les lignes. Il doit donc les pousser.
# ⚠ jours_validite A QUITTE CETTE LISTE LE 07/09 (1.2b), ET C'ETAIT MA FAUTE.
# Je l'avais range en classe A sur une mesure de 0.1 faite sur un COMPROMIS puis
# generalisee aux trois genres. Hektor le garde bel et bien -- dans la PROPOSITION
# de l'OFFRE, la ou l'app le saisit. Six offres de 24933 lues en direct portent
# trois valeurs distinctes (10, 15, 20). Il est desormais relu a chaque run,
# comme date_fin_retractation.
# ⚠ MEME FAUTE QUE SUR jours_retractation, CORRIGEE LA VEILLE. La cause est
#   toujours la meme : 0.1 mesure un champ sur UN SEUL genre et conclut pour les
#   trois. A garder en tete pour les etapes 2, 3 et 4 de 0.1.
COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS = (
    "taux_honoraires", "notaire_id",
)


# ⛔ NE JAMAIS LANCER `--push` SEUL EN PLEINE JOURNEE. Lecon du 07/09/2026.
#
# CE QUI S'EST PASSE, en une heure :
#     06:38  un compromis est ANNULE depuis l'app
#            -> le worker ecrit `cancelled` chez Supabase, en quelques secondes
#     07:52  `--push` lance a la main (pour un autre correctif)
#            -> il pousse l'etat du MIROIR LOCAL, qui date du run de 04:18,
#               quand le compromis etait encore `active`
#            -> l'annulation est EFFACEE chez Supabase
#     08:05  le read-through passe et ne repare rien : il ne relit que le
#            compromis POINTE par la fiche, et ce n'etait plus celui-la
#
# LE GESTE DE L'UTILISATEUR EST DONC PERDU JUSQU'AU RUN SUIVANT. Ici l'ecran a
# rattrape (le garde-fou 2.2c bloquait, le bouton « Annuler » etait a cote, un
# clic a suffi) -- mais c'est une chance, pas un mecanisme.
#
# LA CAUSE N'EST PAS LE PUSH, C'EST L'ORDRE. Le run de nuit fait refresh PUIS
# push : le miroir est frais, l'etat pousse est le bon. Pousser sans rafraichir
# revient a affirmer un etat qu'on n'a pas relu.
#
# ➡ REGLE : `--push` ne se lance jamais seul. Soit `--refresh --push` (le
#   defaut sans argument), soit on attend le run. Et si le miroir lui-meme est
#   perime -- il ne connait que ce que Hektor avait a 04:18 -- alors AUCUN push
#   manuel ne peut etre juste pour les gestes du jour.
#
# ⚠ CE N'EST PAS LE MEME PROBLEME QUE LA DOUBLURE. Le garde-fou
#   retirer_les_lignes_en_conflit() protege des collisions d'IDENTITE (deux
#   numeros pour un meme triplet). Ici l'identite est bonne : c'est la VALEUR
#   qui est perimee, et rien ne la protege.
def ledger_rows_for_push(con: sqlite3.Connection) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for r in con.execute(f"SELECT * FROM {LEDGER_TABLE}"):
        d = dict(r)
        for interdite in COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS:
            d.pop(interdite, None)
        # ⚠ acquereurs_json est jsonb cote Supabase : sans ce decodage on y
        # pousserait une CHAINE DE CARACTERES contenant du JSON, pas du JSON.
        for jcol in ("acquereur_json", "acquereurs_json", "payload_json"):
            v = d.get(jcol)
            if isinstance(v, str) and v:
                try:
                    d[jcol] = json.loads(v)
                except Exception:
                    d[jcol] = None
        d["present_in_hektor"] = bool(d.get("present_in_hektor"))
        rows.append(d)
    return rows


# ─── UNE LIGNE NE DOIT PLUS ARRETER LE RUN ENTIER ───
#
# 01 et 02/09/2026, deux nuits de suite : le push a heurte l'index unique
#     Key (hektor_annonce_id, kind, hektor_affaire_id)=(24933, offre, 33037)
# et le run s'est arrete LA. Tout ce qui venait apres -- le push principal
# compris -- n'a pas tourne, et l'app est restee dix-huit heures en arriere sans
# que rien ne le dise. Le degat n'etait pas le conflit : c'etait l'arret.
#
# La cause d'ordonnancement est traitee ailleurs (le pipeline descend desormais
# la doublure JUSTE AVANT cette etape, au lieu de consulter celle de la veille).
# Ce garde-fou traite l'autre moitie : ce qui se passe quand un conflit survient
# quand meme, par un chemin qu'on n'a pas prevu.
#
# On compare donc le lot a la doublure -- l'image du serveur, descendue a
# l'instant. Une ligne dont le triplet Hektor appartient LA-BAS a un autre numero
# d'app est ecartee du lot : le serveur a deja la verite, et la pousser ne ferait
# que creer un doublon. Le reste passe, le run continue.
#
# ET ON LE DIT FORT. Une ligne ecartee en silence, c'est un registre incomplet
# qui se fait passer pour un registre a jour -- exactement ce qu'on refuse
# ailleurs dans ce projet. Les cles ecartees sont nommees une par une.
def retirer_les_lignes_en_conflit(
    con: sqlite3.Connection, rows: list[dict[str, object]]
) -> tuple[list[dict[str, object]], list[tuple[str, str, str, object, object]]]:
    try:
        cloud = {
            (str(a), str(k), str(h)): n
            for a, k, h, n in con.execute(
                """SELECT hektor_annonce_id, kind, hektor_affaire_id, app_affaire_id
                     FROM app_affaire_ledger__sb
                    WHERE hektor_affaire_id IS NOT NULL
                      AND TRIM(CAST(hektor_affaire_id AS TEXT)) <> ''"""
            )
        }
    except sqlite3.OperationalError:
        # Pas de doublure : on ne sait rien, donc on ne retire rien. Comportement
        # d'avant, a l'identique.
        return rows, []

    gardees: list[dict[str, object]] = []
    ecartees: list[tuple[str, str, str, object, object]] = []
    for row in rows:
        hid = row.get("hektor_affaire_id")
        if hid is None or str(hid).strip() == "":
            gardees.append(row)
            continue
        cle = (str(row.get("hektor_annonce_id")), str(row.get("kind")), str(hid).strip())
        proprietaire = cloud.get(cle)
        if proprietaire is not None and int(proprietaire) != int(row.get("app_affaire_id")):
            ecartees.append((cle[0], cle[1], cle[2], row.get("app_affaire_id"), proprietaire))
        else:
            gardees.append(row)
    return gardees, ecartees


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
        rows, ecartees = retirer_les_lignes_en_conflit(con, rows)
        for annonce, kind, hid, id_local, id_serveur in ecartees:
            print(f"[affaire_ledger] ECARTEE du push : ({annonce}, {kind}, {hid}) "
                  f"-- le serveur la porte sous {id_serveur}, le local sous {id_local}. "
                  f"Le serveur fait foi ; la prochaine adoption resorbera l'ecart.")
        if ecartees:
            print(f"[affaire_ledger] {len(ecartees)} ligne(s) ecartee(s) : le run CONTINUE, "
                  f"mais le registre n'est pas complet sur ces lignes.")
        client.upsert_rows(path=LEDGER_TABLE, rows=rows, batch_size=args.batch_size)
        result["push"] = {"rows_pushed": len(rows), "rows_ecartees": len(ecartees),
                          "cles_ecartees": [f"{a}/{k}/{h}" for a, k, h, _, _ in ecartees]}
        # APRES le push, jamais avant : les lignes nouvelles doivent d'abord exister
        # chez Supabase pour qu'il puisse leur poser une chaine.
        result["chaines"] = redescendre_ce_que_l_app_possede(client, con)
    con.close()
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
