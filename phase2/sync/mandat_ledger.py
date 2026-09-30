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
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ⚠ IMPORTEES, JAMAIS RECOPIEES. Ce sont les formules du registre, celles qui
#   choisissent la bonne version d'un mandat et depouillent ses avenants. Une
#   deuxieme copie qui derive est precisement ce que le projet a deja paye.
from phase2.sync.export_app_payload import (  # noqa: E402
    compute_mandat_version_score,
    normalize_embedded_avenants,
)

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
    -- LA NATURE DU MANDAT -- LUE, JAMAIS DEVINEE.
    -- ⚠ A NE PAS CONFONDRE AVEC `famille`, ET C'EST TOUT L'ENJEU : deux axes
    --   differents, comme les « couleurs » et les « lettres » de la carte A1.
    --      famille = DE QUEL REGISTRE vient le numero   (HEKTOR / PROTEXA)
    --      nature  = CE QU'EST le mandat                (VENTE / GESTION / ...)
    -- Mesure du 29/09 : 23 559 VENTE · 260 GESTION · 38 RECHERCHE · 1 LOCATION,
    -- et 2 960 sans indice -- dont 2 342 sur des annonces de location.
    -- ⚠ LES « INCONNUE » RESTENT INCONNUES. Les ranger d'office en VENTE serait
    --   exactement l'erreur que Frederic a corrigee trois fois le 29/09 :
    --   compter comme perdu ce qui etait ecarte volontairement.
    nature               TEXT,
    -- LE TYPE D'OFFRE DE L'ANNONCE, ET IL EST INDISPENSABLE.
    -- Cette table porte TOUT, locations comprises -- c'est la regle du projet,
    -- « le serveur recoit tous les types ». Mais le REGISTRE, lui, n'en admet
    -- que trois (TYPES_OFFRE_APP : 0 vente, 10 vente immo pro, 6 neuf).
    -- ⚠ SANS CETTE COLONNE ON ANNONCE DES PERTES QUI N'EN SONT PAS : le 29/09
    --   j'ai compte « 2 983 mandats absents du registre ». Frederic a demande
    --   si c'etaient des locations. C'ETAIT LE CAS POUR 2 348 D'ENTRE EUX,
    --   ecartes par sa decision du 26/08. La vraie perte etait 635.
    offre_type           TEXT,
    -- HORS du ON CONFLICT : protection par omission. L'app possede ce champ
    -- (CHAMPS_APP_MANDAT), le carnet app_mandat_champ_app le porte, et le run
    -- n'a pas a l'ecraser avec ce que Hektor en pense.
    date_cloture         TEXT,
    -- ── CE QUE LE REGISTRE SAIT FAIRE, ET QUE LA TABLE DOIT SAVOIR AUSSI ──
    -- L'ECRAN LES LIT DEJA : register_version_count affiche « +N versions »,
    -- register_avenants_json affiche les avenants. Si la table ne les porte
    -- pas, la bascule ferait PERDRE deux fonctions a l'ecran -- en silence.
    --
    -- versions_json  TOUTES les versions du couple, LA MEILLEURE EN TETE
    --                (ordre de compute_mandat_version_score). C'est de la que
    --                le registre tirera son historique.
    -- avenants_json  les avenants depouilles. ⚠ Le parc n'en porte QU'UN SEUL
    --                (n° 18499, 02/04/2026) -- mesure du 30/09. La colonne
    --                existe parce que l'ecran la lit, pas parce qu'elle est
    --                pleine.
    versions_json        TEXT,
    version_count        INTEGER,
    avenants_json        TEXT,
    avenant_count        INTEGER,
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


# Les types d'offre qui designent une LOCATION (ou du saisonnier). Ils ne sont
# pas dans le registre de l'app, mais la table les porte -- et leur nature doit
# etre nommee plutot que laissee « inconnue ».
TYPES_LOCATION = ("2", "11", "8")


def _nature(type_mandat, note, offre_type) -> str:
    """CE QU'EST le mandat. L'ordre compte, et il est justifie ligne a ligne.

    La note porte « Objet mandat : ... » -- c'est la seule source qui nomme un
    mandat de gestion ou de recherche. Elle passe donc AVANT le type d'offre :
    les 260 mandats de gestion portent tous sur un bien en location, et leur
    nature est GESTION, pas LOCATION.
    """
    n = (note or "").upper()
    if "MANDAT DE GESTION" in n or "MANDAT DE GERANCE" in n:
        return "GESTION"
    if "MANDAT DE RECHERCHE" in n:
        return "RECHERCHE"
    t = (type_mandat or "").strip().upper()
    if t in ("SIMPLE", "EXCLUSIF", "ACCORD") or "VENTE" in t:
        return "VENTE"
    if str(offre_type or "") in TYPES_LOCATION:
        return "LOCATION"
    if "MANDAT DE LOCATION" in n:
        return "LOCATION"
    if "MANDAT DE VENTE" in n:
        return "VENTE"
    return "INCONNUE"


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


def _texte(valeur) -> str | None:
    """Le meme nettoyage que normalize_text du registre : vide -> None."""
    if valeur is None:
        return None
    s = str(valeur).strip()
    return s or None


def _montant(valeur) -> str | None:
    """UN MONTANT DE ZERO EST UN MONTANT VIDE -- et c'est une regle du projet.

    Mesure du 30/09 : 171 lignes portaient « 0 » la ou le registre n'affiche
    rien. La colonne plate du miroir met 0 quand la fiche ne dit rien ; le
    tableau `mandats` du detail, lui, ne met rien du tout. Garder « 0 » ferait
    apparaitre « 0 EUR » sur 171 lignes d'un registre ou la case est vide
    aujourd'hui.

    C'est le meme piege que le DPE, deja paye une fois : « vide » y vaut la
    chaine "0", qui est vraie pour l'ordinateur et fausse pour l'agence. La
    regle du projet est d'exiger un nombre STRICTEMENT POSITIF.

    ⚠ ET CE N'EST PAS QU'UN AFFICHAGE : compute_mandat_version_score compte les
      champs remplis. Un « 0 » compte comme rempli et peut faire gagner la
      mauvaise version. On nettoie donc AVANT de noter, pas apres.
    """
    s = _texte(valeur)
    if not s:
        return None
    try:
        return None if float(s.replace(",", ".")) == 0 else s
    except ValueError:
        return s


def _version_depuis_ligne(ligne) -> dict:
    """LE raw_json D'UNE LIGNE DU MIROIR **EST** UN OBJET VERSION.

    Verifie le 30/09 : ses cles sont exactement celles que le registre lit dans
    le tableau `mandats` du detail -- id, numero, type, debut, fin, cloture,
    montant, mandants, note, avenants, dateEnregistrement. Les deux chemins
    lisent donc LA MEME MATIERE, et peuvent porter LE MEME JUGEMENT.

    Repli sur les colonnes plates si le raw_json manque ou ne s'ouvre pas : une
    version pauvre vaut mieux qu'une version perdue, et le score la classera
    derriere toute version complete -- ce qui est le comportement voulu.
    """
    brut = ligne["raw_json"]
    if brut:
        try:
            objet = json.loads(brut)
            if isinstance(objet, dict) and objet:
                # meme nettoyage sur la photocopie : le score se calcule dessus
                objet["montant"] = _montant(objet.get("montant"))
                return objet
        except Exception:
            pass
    return {
        "id": _texte(ligne["hektor_mandat_id"]),
        "numero": _texte(ligne["numero"]),
        "type": _texte(ligne["type"]),
        "debut": _texte(ligne["date_debut"]),
        "fin": _texte(ligne["date_fin"]),
        "cloture": _texte(ligne["date_cloture"]),
        "montant": _montant(ligne["montant"]),
        "mandants": _texte(ligne["mandants_texte"]),
        "note": _texte(ligne["note"]),
        "dateEnregistrement": _texte(ligne["date_enregistrement"]),
        "avenants": [],
    }


def _ligne_de_la_version(rangee, version) -> object:
    """La ligne du miroir qui porte la version retenue.

    On en a besoin pour trois choses que la version ne dit pas toujours : son
    identifiant Hektor, sa date de cloture, et son raw_json (payload_json garde
    la photocopie de CETTE version-la, pas d'une autre).
    """
    vise = _texte(version.get("id")) if version else None
    if vise:
        for ligne in rangee:
            if _texte(ligne["hektor_mandat_id"]) == vise:
                return ligne
    return rangee[0]


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
    _ajouter_colonne_si_absente(con, "offre_type", "TEXT")
    _ajouter_colonne_si_absente(con, "nature", "TEXT")
    _ajouter_colonne_si_absente(con, "versions_json", "TEXT")
    _ajouter_colonne_si_absente(con, "version_count", "INTEGER")
    _ajouter_colonne_si_absente(con, "avenants_json", "TEXT")
    _ajouter_colonne_si_absente(con, "avenant_count", "INTEGER")
    vu = now_iso()

    # Le type d'offre de chaque annonce, lu une fois. Il ne sert pas a filtrer
    # ici -- la table porte tout -- mais a ce que le CONTROLE sache distinguer
    # une perte reelle d'une location volontairement ecartee.
    offres = {}
    for a in con.execute(
        "SELECT hektor_annonce_id, offre_type FROM hektor.hektor_annonce"
    ):
        offres[str(a["hektor_annonce_id"])] = str(a["offre_type"] or "")

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

    # ══════════════════════════════════════════════════════════════════════════
    # ON GROUPE PAR COUPLE AVANT D'ECRIRE -- ET C'EST LE CORRECTIF DU 30/09.
    #
    # Le miroir porte 25 003 lignes pour 24 754 couples : 147 couples ont
    # PLUSIEURS versions du meme mandat. La premiere version de ce script les
    # ecrivait a la file, donc LA DERNIERE LUE GAGNAIT -- un ordre qui ne veut
    # rien dire. Le registre, lui, choisit LA PLUS COMPLETE depuis toujours
    # (compute_mandat_version_score). Mesure du 30/09 : les deux choix se
    # rejoignent sur 141 couples et DIVERGENT SUR 6.
    #
    # Les 6, et ce ne sont pas des nuances d'affichage :
    #     n° 4069   158 685 EUR (2012)  au lieu de   76 230 EUR (2020)
    #     n° 3958   168 000 EUR (2012)  au lieu de  244 900 EUR (2020)
    #     n° 4425    52 000 EUR (2012)  au lieu de  149 000 EUR (2021)
    #     n° 4141   SIMPLE               au lieu de  ACCORD
    #     n° 3838   EXCLUSIF             au lieu de  SIMPLE
    #     n° 17195  date de fin decalee d'un jour
    # « Un mandat simple presente comme exclusif n'est pas une nuance
    #   d'affichage : les deux n'ont pas les memes effets juridiques. »
    #
    # ⚠ LA FORMULE EST IMPORTEE, PAS RECOPIEE. Une deuxieme copie qui derive est
    #   exactement ce que le projet a paye sur les vues et sur les renvois.
    # ══════════════════════════════════════════════════════════════════════════
    groupes: dict[tuple[str, str], list[sqlite3.Row]] = {}
    for m in con.execute(
        "SELECT hektor_mandat_id, hektor_annonce_id, numero, type, date_enregistrement,"
        " date_debut, date_fin, date_cloture, montant, mandants_texte, note, raw_json"
        " FROM hektor.hektor_mandat"
    ).fetchall():
        lus += 1
        annonce = str(m["hektor_annonce_id"] or "").strip()
        numero = str(m["numero"] or "").strip()
        if not annonce or not numero:
            sans_numero += 1
            continue
        groupes.setdefault((annonce, numero), []).append(m)

    multi_versions = 0
    for (annonce, numero), rangee in groupes.items():
        # Les versions, telles que le registre les voit : le raw_json de chaque
        # ligne EST l'objet version (memes cles : id/numero/type/debut/fin/
        # cloture/montant/mandants/note/avenants). Verifie le 30/09.
        versions = []
        for ligne in rangee:
            item = _version_depuis_ligne(ligne)
            if item:
                versions.append(item)
        versions.sort(key=compute_mandat_version_score, reverse=True)
        if len(rangee) > 1:
            multi_versions += 1
        # La ligne du miroir qui PORTE la version retenue -- on garde son
        # hektor_mandat_id, sa date de cloture et son raw_json.
        courante = versions[0] if versions else {}
        m = _ligne_de_la_version(rangee, courante)

        avenants = normalize_embedded_avenants(versions) if versions else []

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
                date_cloture, first_seen_at, last_seen_at, offre_type, nature,
                versions_json, version_count, avenants_json, avenant_count,
                origine, present_in_hektor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'mandat', 1)
            ON CONFLICT(hektor_annonce_id, numero_mandat) DO UPDATE SET
                app_dossier_id=COALESCE(excluded.app_dossier_id, app_mandat.app_dossier_id),
                hektor_mandat_id=excluded.hektor_mandat_id,
                offre_type=excluded.offre_type,
                nature=excluded.nature,
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
                versions_json=excluded.versions_json,
                version_count=excluded.version_count,
                avenants_json=excluded.avenants_json,
                avenant_count=excluded.avenant_count,
                last_seen_at=excluded.last_seen_at,
                present_in_hektor=1
            """,
            (
                identifiant, dossiers.get(annonce), annonce, numero,
                str(m["hektor_mandat_id"] or "") or None,
                _famille(courante.get("type"), numero),
                _texte(courante.get("type")),
                _texte(courante.get("dateEnregistrement")) or m["date_enregistrement"],
                _texte(courante.get("debut")) or m["date_debut"],
                _texte(courante.get("fin")) or m["date_fin"],
                _montant(courante.get("montant")) or _montant(m["montant"]),
                _texte(courante.get("mandants")) or m["mandants_texte"],
                _texte(courante.get("note")) or m["note"],
                m["raw_json"], m["date_cloture"], vu, vu,
                offres.get(annonce),
                _nature(courante.get("type"), courante.get("note") or m["note"],
                        offres.get(annonce)),
                json.dumps(versions, ensure_ascii=True, separators=(",", ":")),
                len(versions),
                json.dumps(avenants, ensure_ascii=True, separators=(",", ":")),
                len(avenants),
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
            # ⚠ LA LIGNE EXISTE DEJA -- on ne la reecrit PAS (sa source, la fiche,
            #   est plus riche). Mais le type d'offre, lui, doit etre pose : sans
            #   lui le controle ne sait pas distinguer une location d'une perte,
            #   et il a deja annonce « 2 983 perdus » pour 263 reels.
            con.execute(
                "UPDATE app_mandat SET offre_type = COALESCE(NULLIF(offre_type,''), ?),"
                "                       nature = COALESCE(NULLIF(nature,''), ?)"
                " WHERE hektor_annonce_id = ? AND numero_mandat = ?",
                (offres.get(annonce), _nature(None, None, offres.get(annonce)),
                 annonce, numero),
            )
            continue
        identifiant = prochain
        prochain += 1
        connus.add(cle)
        depuis_annonce += 1
        vus_ce_run.append(cle)
        con.execute(
            """
            INSERT INTO app_mandat(app_mandat_id, app_dossier_id, hektor_annonce_id,
                numero_mandat, famille, first_seen_at, last_seen_at, offre_type,
                nature, origine, present_in_hektor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'annonce', 1)
            ON CONFLICT(hektor_annonce_id, numero_mandat) DO NOTHING
            """,
            (identifiant, dossiers.get(annonce), annonce, numero,
             _famille(None, numero), vu, vu, offres.get(annonce),
             _nature(None, None, offres.get(annonce))),
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


# Les trois seuls types d'offre que le registre de l'app admet. Decision de
# Frederic du 26/08 : les locations (2, 11) et le saisonnier (8) restent au
# serveur et n'apparaissent PAS dans l'app.
TYPES_ADMIS_AU_REGISTRE = ("0", "10", "6")

LIBELLE_OFFRE = {
    "0": "0  vente", "2": "2  LOCATION", "6": "6  neuf", "8": "8  SAISONNIER",
    "10": "10 vente immo pro", "11": "11 LOCATION immo pro",
}


def comparer_au_registre(con: sqlite3.Connection) -> None:
    """Ce que la table a et que le registre n'a pas -- EN SEPARANT LES LOCATIONS.

    ⚠ POURQUOI CETTE SEPARATION EXISTE. Le 29/09 j'ai annonce « 2 983 mandats
      perdus par le registre ». Frederic : « est-ce que ce ne sont pas des
      mandats de location ? ». C'etait le cas pour 2 348 d'entre eux -- ecartes
      par sa propre decision du 26/08, donc PAS des pertes. La vraie perte
      etait 635. Un total qui melange les deux ne veut rien dire.
    """
    try:
        vue = {(str(a), str(n)) for a, n in con.execute(
            "SELECT hektor_annonce_id, numero_mandat FROM app_mandat_register_current")}
    except sqlite3.OperationalError:
        print("   (registre absent de cette base : comparaison impossible)")
        return

    import collections
    from datetime import date
    aujourd_hui = date.today().isoformat()
    par_type = collections.Counter()
    perdus_reels = 0
    encore_en_cours = 0
    for a, n, t, fin in con.execute(
        "SELECT hektor_annonce_id, numero_mandat, offre_type, date_fin FROM app_mandat"
    ):
        if (str(a), str(n)) in vue:
            continue
        type_offre = str(t or "")
        par_type[type_offre] += 1
        if type_offre in TYPES_ADMIS_AU_REGISTRE:
            perdus_reels += 1
            if fin and fin >= aujourd_hui:
                encore_en_cours += 1

    print("")
    print("ABSENTS DU REGISTRE, par type d'offre de l'annonce :")
    for t, n in par_type.most_common():
        admis = "  <- type ADMIS : vraie perte" if t in TYPES_ADMIS_AU_REGISTRE else "  (ecarte volontairement)"
        print("   %-22s %6s%s" % (LIBELLE_OFFRE.get(t, t or "(inconnu)"), n, admis))
    print("")
    print("   TOTAL brut                          : %s" % sum(par_type.values()))
    print("   PERTE REELLE (types admis)          : %s" % perdus_reels)
    print("   dont mandats ENCORE EN COURS        : %s" % encore_en_cours)


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
    for nature, n in con.execute("SELECT nature, COUNT(*) FROM app_mandat GROUP BY 1 ORDER BY 2 DESC"):
        print("      nature  %-10s              : %s" % (nature, n))
    # ── CE QUE L'ECRAN LIT, ET QUE LA TABLE DOIT SAVOIR RENDRE ───────────────
    print("   versions retenues sur plusieurs     : %s   (miroir : 147 couples)"
          % q("SELECT COUNT(*) FROM app_mandat WHERE COALESCE(version_count,0) > 1"))
    print("   avenants portes                     : %s   (miroir : 1 seul)"
          % q("SELECT COUNT(*) FROM app_mandat WHERE COALESCE(avenant_count,0) > 0"))
    print("   lignes SANS versions_json           : %s   (doit valoir 0 pour origine=mandat)"
          % q("SELECT COUNT(*) FROM app_mandat WHERE origine = 'mandat'"
              "   AND (versions_json IS NULL OR versions_json IN ('', '[]'))"))

    print("")
    # LE CONTROLE QUI COMPTE : aucun numero ne doit tomber dans la plage de l'app.
    envahis = q("SELECT COUNT(*) FROM app_mandat WHERE app_mandat_id >= %d" % PLAGE_RESERVEE_APP)
    print("   DANS LA PLAGE RESERVEE A L'APP      : %s   (doit valoir 0)" % envahis)
    if envahis:
        print("   >> L'ALLOCATEUR EST FAUX. C'est le defaut d'aout, a l'identique.")

    comparer_au_registre(con)


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
