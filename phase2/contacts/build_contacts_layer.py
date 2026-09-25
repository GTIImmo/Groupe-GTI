from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
DEFAULT_PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
DEFAULT_REPORT_DIR = ROOT / "exports_contacts_audit"


GENERIC_CONTACT_NAMES = {
    "m",
    "mr",
    "mme",
    "m mme",
    "mr mme",
    "monsieur",
    "madame",
    "monsieur madame",
    "monsieur mme",
    "m et mme",
    "mr et mme",
}

SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass(frozen=True)
class ContactRow:
    hektor_contact_id: str
    hektor_agence_id: str | None
    hektor_negociateur_id: str | None
    civilite: str | None
    nom: str | None
    prenom: str | None
    archive: int
    date_enregistrement: str | None
    date_maj: str | None
    email: str | None
    portable: str | None
    fixe: str | None
    ville: str | None
    code_postal: str | None
    adresse: str | None
    typologie_json: str | None
    raw_json: str | None
    synced_at: str | None
    # Le MENAGE selon Hektor (son `refCouple`) : les fiches d'un meme menage
    # partagent cette valeur, et la porteuse est celle dont l'identifiant l'egale.
    hektor_couple_contact_id: str | None = None
    # L'identite de la porteuse, resolue APRES le chargement (voir resoudre_menages).
    # None tant qu'on n'a pas cherche, ou quand la porteuse a disparu de Hektor.
    couple_identite_porteuse: str | None = None
    # ═══════════════════════════════════════════════════════════════════════
    # L4-c ④ 22/09/2026 — LE NUMERO POUR VISER HEKTOR, PORTE PAR LA COUCHE
    # ═══════════════════════════════════════════════════════════════════════
    # ⛔ SANS CE CHAMP, LA BASCULE COUPE LE LIEN VERS HEKTOR POUR TOUT LE PARC.
    #   Le raisonnement, verifie le 22/09 avant d'allumer quoi que ce soit :
    #     · le push ecrit en FUSION (resolution=merge-duplicates), donc une
    #       colonne absente de l'envoi est PRESERVEE -- rassurant, mais hors
    #       sujet ;
    #     · car la bascule ne modifie pas une ligne : elle CHANGE SA CLE.
    #       '605449' devient '10356127', qui n'entre en conflit avec rien ->
    #       ce n'est pas une fusion, c'est une ligne NEUVE, sans cible ;
    #     · et le declencheur `app_contact_remplir_cible` ne la remplit pas :
    #       il ne le fait que sous 10 000 000 ;
    #     · pendant ce temps l'ancienne ligne n'est plus produite -> vue comme
    #       disparue -> supprimee.
    #   Soit 62 000 lignes remplacees, TOUTES avec une case cible vide, et plus
    #   un seul contact joignable chez Hektor. Sans une erreur, sans un bruit.
    #
    # LA VALEUR EST EVIDENTE ET N'A PAS A ETRE CHERCHEE : c'est l'identifiant
    # que porte le MIROIR, qui est une copie de Hektor. On le garde au moment
    # ou on lui substitue l'identite de l'app -- deux lignes plus bas.
    hektor_target_id: str | None = None

    @property
    def est_fiche_de_menage(self) -> bool:
        """La seconde fiche d'un menage : vide, et rattachee a une autre.

        Mesure du 11/09 sur les 355 978 contacts : 133 343 fiches sont sans nom
        NI prenom, et 133 286 portent la civilite « Mr./Mme ». Ce n'est pas un
        defaut de recuperation -- l'API rend la meme chose, `coordonnees: null`
        compris. C'est la place du SECOND MEMBRE, que Hektor cree pour tout le
        parc et que personne n'a jamais remplie ici.
        """
        if clean_text(self.nom) or clean_text(self.prenom):
            return False
        lien = clean_text(self.hektor_couple_contact_id)
        return bool(lien) and lien != clean_text(self.hektor_contact_id)

    @property
    def couple_role(self) -> str | None:
        """Ce que l'ecran doit savoir, en UN champ.

            « menage_resolu »    fiche vide, porteuse connue  -> A MASQUER
                                 l'identite est ailleurs, la montrer ferait deux
                                 lignes pour une personne  (regle de Frederic,
                                 11/09 : « une personne, une ligne »)
            « menage_orphelin »  fiche vide, porteuse DISPARUE de Hektor
                                 -> A GARDER : elle est rattachee a un bien reel,
                                 la masquer ferait disparaitre un mandant sans
                                 explication
            None                 tout le reste

        On ne pose PAS de role « porteur » : il faudrait savoir qui pointe vers
        nous, et personne ne s'en servirait. Regle du plan : jamais un champ
        genere mais inutilise.
        """
        if not self.est_fiche_de_menage:
            return None
        return "menage_resolu" if clean_text(self.couple_identite_porteuse) else "menage_orphelin"

    @property
    def display_name(self) -> str:
        # ── LA FICHE DE MENAGE EMPRUNTE L'IDENTITE DE SA PORTEUSE.
        #
        # ⚠ ET C'EST EXACTEMENT CE QUE FAIT HEKTOR. Son formulaire de compromis
        #   affiche pour la fiche muette 485955 : « Mr./Mme Test SELL AND SIGNE / »
        #   -- la civilite de la fiche, l'identite de la porteuse 141053, puis un
        #   slash qui est la place vide du second prenom. On reproduit son geste
        #   au lieu d'en inventer un : c'est ce que l'utilisateur voit deja
        #   ailleurs, et aucun prefixe fabrique ne vient s'y ajouter -- une
        #   porteuse nommee « ABDENOURI MONSIEUR ET MADAME » donnerait sinon
        #   « M. et Mme ABDENOURI MONSIEUR ET MADAME ».
        if self.est_fiche_de_menage:
            if clean_text(self.couple_identite_porteuse):
                return " ".join(part for part in [self.civilite, self.couple_identite_porteuse]
                                if clean_text(part))
            # Porteuse disparue de Hektor : 14 080 liens sur 124 455, verifie par
            # appel API (404). « Mr./Mme » tout court rendrait ces fiches
            # indistinguables les unes des autres ; le numero, lui, les separe.
            return f"Contact {self.hektor_contact_id}"
        # ── UNE CIVILITE N'EST PAS UN NOM.
        #
        # ⚠ C'ETAIT LE DEFAUT D'ORIGINE, et il survivait au correctif ci-dessus.
        #   L'ancienne formule joignait civilite + prenom + nom, et son repli
        #   « Contact <numero> » ne se declenchait QUE si les trois manquaient.
        #   Une fiche vide portant « Mr./Mme » sortait donc « Mr./Mme » tout
        #   court -- 133 286 fiches au depart, et il en restait ENCORE 22 414
        #   apres la resolution des menages : celles qui n'ont aucun lien, donc
        #   personne pour les nommer. Toutes identiques a l'ecran, impossibles a
        #   distinguer l'une de l'autre.
        if not clean_text(self.nom) and not clean_text(self.prenom):
            return f"Contact {self.hektor_contact_id}"
        return " ".join(part for part in [self.civilite, self.prenom, self.nom] if clean_text(part)) or f"Contact {self.hektor_contact_id}"

    @property
    def email_normalized(self) -> str:
        return normalize_email(self.email)

    @property
    def phone_primary(self) -> str | None:
        return clean_text(self.portable) or clean_text(self.fixe) or None

    @property
    def phone_normalized(self) -> str:
        return normalize_phone(self.portable) or normalize_phone(self.fixe)

    @property
    def first_name_normalized(self) -> str:
        return normalize_text(self.prenom)

    @property
    def last_name_normalized(self) -> str:
        return normalize_text(self.nom)

    @property
    def city_normalized(self) -> str:
        return normalize_text(self.ville)

    @property
    def postal_code_normalized(self) -> str:
        return clean_text(self.code_postal) or ""

    @property
    def completeness_score(self) -> int:
        return sum(
            1
            for value in (
                self.email,
                self.portable,
                self.fixe,
                self.ville,
                self.code_postal,
                self.prenom,
                self.nom,
                self.date_maj,
            )
            if clean_text(value)
        )


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_text(value: Any) -> str:
    text = clean_text(value).lower()
    text = "".join(ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_email(value: Any) -> str:
    return clean_text(value).lower()


def normalize_phone(value: Any) -> str:
    digits = re.sub(r"\D+", "", clean_text(value))
    if digits.startswith("33") and len(digits) == 11:
        digits = f"0{digits[2:]}"
    return digits if len(digits) >= 9 else ""


def stable_hash(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()


def short_hash(value: str) -> str:
    if not value:
        return ""
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def parse_bool_archive(value: Any) -> int:
    return 1 if clean_text(value).lower() in {"1", "true", "oui", "yes"} else 0


def json_array(value: Any) -> str:
    return json.dumps(value or [], ensure_ascii=False, separators=(",", ":"))


def parse_json_value(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    text = clean_text(value)
    if not text:
        return fallback
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return fallback


def json_items(value: Any) -> list[dict[str, Any]]:
    data = parse_json_value(value, [])
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def first_non_empty(*values: Any) -> str | None:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return None


# ═══════════════════════════════════════════════════════════════════════════
# L4-b (②) — LA SUBSTITUTION D'IDENTITE                          21/09/2026
# ═══════════════════════════════════════════════════════════════════════════
# LE DEFAUT, mesure en reel le 21/09 sur le premier contact ne dans l'app : il
# a fini en DEUX fiches. L'app lui avait donne l'identite 10 000 001 ; le retour
# du worker l'a repose sous le numero que Hektor venait de lui donner, 605450.
# Rien ne disait au serveur que les deux numeros designent la meme personne.
#
# LA CORRESPONDANCE EST REDESCENDUE AVANT LE BUILD, dans app_contact_identite_app
# (phase2/identite/descendre_correspondance_contacts.py). Ici, on s'en sert pour
# une chose et une seule : remplacer le numero Hektor par l'identite de l'app,
# A L'ENTREE, avant tout calcul.
#
# ⚠ C'EST POUR CA QUE CA SE PASSE ICI ET PAS AU PUSH. Les cles des relations et
#   des recherches ne CONTIENNENT pas le numero de contact : elles sont
#   CALCULEES dessus (`relation_key = stable_hash({"contact_id": ...})`, plus
#   bas dans ce fichier). Substituer apres coup laisserait des empreintes
#   calculees sur un numero et des colonnes portant l'autre -- et le run suivant
#   prendrait ces lignes pour des disparues, donc il les SUPPRIMERAIT.
#
# INERTE PAR DEFAUT : la table n'existe pas encore chez tout le monde, et elle
# est vide tant qu'aucun contact ne nait dans l'app. `identite_app` rend alors
# exactement ce qu'on lui donne, et le build se comporte comme avant.
_IDENTITE_APP: dict[str, str] = {}
_NUMERO_MIROIR: dict[str, str] = {}
PLAGE_NUMEROS_APP = 10_000_000


# ⚠ SI TU LANCES CE SCRIPT A LA MAIN, HORS DU RUN : ENCHAINE AVEC
#       python phase2/contacts/elargir_perimetre_console.py
#   Le build remet l'eligibilite a ce que SA regle dit (59 230 au 24/09) ;
#   c'est elargir_perimetre_console qui repose ensuite les personnes citees
#   par Hektor (+2 763). Entre les deux, la couche est incomplete : un push
#   joue dans cet intervalle prendrait ces 2 763 pour des disparues et LES
#   SUPPRIMERAIT de Supabase.
#   Dans le run de nuit l'ordre est correct (etape 8 puis 17). A la main, il
#   s'oublie -- constate DEUX FOIS en 24 h, les 23 et 24/09.

def charger_identites_app(conn: sqlite3.Connection) -> int:
    """Charge la correspondance numero Hektor -> identite de l'app.

    ⚠ C-3, 23/09/2026 -- L'INVARIANT QUI MANQUAIT. L'etape qui remplit cette
      table est NON BLOQUANTE dans le run (run_full_pipeline.ps1) : si Supabase
      ne repond pas, on garde la table de la veille et le run continue. C'est le
      bon choix un soir ordinaire, ou la table est vide et ou il n'y a rien a
      traduire.

      Ce n'est plus le bon choix apres la bascule. La couche porterait alors des
      identites a nous, et un build sans correspondance les rangerait toutes
      sous les numeros de Hektor -- en RECALCULANT au passage les empreintes des
      relations et des recherches, donc en fabriquant un parc entier de fiches
      en double.

      D'ou la regle, qui s'arme toute seule : SI LA COUCHE PORTE DEJA DES
      IDENTITES A NOUS ET QUE LA CORRESPONDANCE EST VIDE, ON S'ARRETE. Tant que
      la bascule n'est pas faite, aucune identite n'est dans la plage et cette
      garde ne se declenche jamais.
    """
    _IDENTITE_APP.clear()
    _NUMERO_MIROIR.clear()

    # ── LE REGISTRE LOCAL D'ABORD, 24/09/2026 ──────────────────────────────
    # LE DEFAUT QUE CECI FERME, et il a coute 294 179 doublons le matin du 24.
    # La table descendue de Supabase ne connait que le PERIMETRE ELIGIBLE
    # (61 985 paires au 24/09), parce que la vue qui l'alimente lit
    # app_contact_current COTE SUPABASE. Les 294 187 contacts hors perimetre
    # n'y figurent pas -- le build les rangeait donc sous leur numero de
    # Hektor, et le registre, qui les avait deja numerotes, leur donnait une
    # SECONDE identite. Le parc a double en une nuit, en silence.
    #
    # Or la serie d'identite est LOCALE : « Supabase RECOIT la serie, il ne
    # la fabrique jamais » (regle du 19/08). Le registre `app_contact` est
    # donc la source, et il connait les 356 166 paires -- perimetre ou pas.
    # La table descendue reste lue APRES, en complement : elle ne peut
    # qu'ajouter ce que le registre ignorerait encore.
    if table_exists(conn, "app_contact"):
        for row in conn.execute(
                "SELECT hektor_target_id, hektor_contact_id FROM app_contact "
                " WHERE hektor_target_id IS NOT NULL AND hektor_contact_id IS NOT NULL"):
            hektor_id = clean_text(row[0])
            identite = clean_text(row[1])
            if hektor_id and identite and hektor_id != identite:
                _IDENTITE_APP[hektor_id] = identite
                _NUMERO_MIROIR[identite] = hektor_id

    if table_exists(conn, "app_contact_identite_app"):
        for row in conn.execute(
                "SELECT hektor_contact_id, app_identite FROM app_contact_identite_app"):
            hektor_id = clean_text(row[0])
            identite = clean_text(row[1])
            if hektor_id and identite and hektor_id != identite:
                _IDENTITE_APP[hektor_id] = identite
                # Le chemin inverse, pose ICI une fois pour toutes : le chercher
                # a chaque appel coutait un parcours de toute la table.
                _NUMERO_MIROIR[identite] = hektor_id

    if not _IDENTITE_APP and table_exists(conn, "app_contact_current"):
        deja_bascule = conn.execute(
            "SELECT COUNT(*) FROM app_contact_current"
            " WHERE CAST(hektor_contact_id AS INTEGER) >= ?",
            (PLAGE_NUMEROS_APP,)).fetchone()[0]
        if deja_bascule:
            raise RuntimeError(
                f"ARRET : {deja_bascule} contact(s) de la couche portent deja une identite "
                f"a nous (>= {PLAGE_NUMEROS_APP}), mais la correspondance est VIDE. "
                "Construire maintenant les rangerait sous les numeros de Hektor et "
                "recalculerait toutes les empreintes. Relancer "
                "phase2/identite/descendre_correspondance_contacts.py d'abord.")
    return len(_IDENTITE_APP)


def identite_app(contact_id: Any) -> str:
    """Le numero sous lequel ce contact doit etre RANGE chez nous.

    Pour 356 000 contacts sur 356 002, c'est le numero de Hektor lui-meme : ils
    y sont nes. Pour ceux qui sont nes dans l'app, c'est leur identite.
    """
    texte = clean_text(contact_id)
    return _IDENTITE_APP.get(texte, texte)


def numero_hektor_pour_le_miroir(contact_id: Any) -> str:
    """Le chemin inverse : sous quel numero le MIROIR connait-il ce contact ?

    Un rafraichissement cible peut arriver avec l'identite de l'app ; le miroir,
    lui, ne connait que le numero de Hektor. Sans cette traduction, la requete
    ne trouverait rien et la fiche paraitrait disparue.
    """
    texte = clean_text(contact_id)
    # C-3 23/09 : table inverse posee au chargement. Avant, chaque appel
    # parcourait toute la correspondance -- invisible sur 1 ligne, mais
    # 61 984 parcours de 61 984 entrees le jour de la bascule.
    return _NUMERO_MIROIR.get(texte, texte)


def normalize_contact_ids(values: Iterable[Any]) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        for chunk in clean_text(raw_value).replace(";", ",").split(","):
            contact_id = clean_text(chunk)
            if not contact_id:
                continue
            if not contact_id.isdigit():
                raise ValueError(f"ID contact invalide: {contact_id}")
            if contact_id in seen:
                continue
            seen.add(contact_id)
            ids.append(contact_id)
    return ids


def active_archive_flag(value: Any) -> int:
    return 0 if parse_bool_archive(value) else 1


def contact_from_row(row: sqlite3.Row) -> ContactRow:
    # L4-b (②) : le miroir parle en numeros de Hektor ; chez nous, un contact ne
    # dans l'app se range sous SON identite. La substitution a lieu ici, a
    # l'entree, pour que tout ce qui suit -- empreintes comprises -- soit
    # calcule sur un seul numero.
    return ContactRow(
        hektor_contact_id=identite_app(row["hektor_contact_id"]),
        # L4-c ④ : la CIBLE, c'est le numero du miroir -- celui de Hektor, par
        # definition. On le capture ici, au moment meme ou l'identite le
        # remplace, parce que c'est le seul endroit ou les deux coexistent.
        hektor_target_id=clean_text(row["hektor_contact_id"]) or None,
        hektor_agence_id=clean_text(row["hektor_agence_id"]) or None,
        hektor_negociateur_id=clean_text(row["hektor_negociateur_id"]) or None,
        civilite=clean_text(row["civilite"]) or None,
        nom=clean_text(row["nom"]) or None,
        prenom=clean_text(row["prenom"]) or None,
        archive=parse_bool_archive(row["archive"]),
        date_enregistrement=clean_text(row["date_enregistrement"]) or None,
        date_maj=clean_text(row["date_maj"]) or None,
        email=clean_text(row["email"]) or None,
        portable=clean_text(row["portable"]) or None,
        fixe=clean_text(row["fixe"]) or None,
        ville=clean_text(row["ville"]) or None,
        code_postal=clean_text(row["code_postal"]) or None,
        adresse=clean_text(row["adresse"]) or None,
        typologie_json=clean_text(row["typologie_json"]) or None,
        raw_json=clean_text(row["raw_json"]) or None,
        synced_at=clean_text(row["synced_at"]) or None,
        hektor_couple_contact_id=identite_app(row["hektor_couple_contact_id"]) or None,
    )


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    # busy_timeout 30 s (22/08/2026). phase2.sqlite a plusieurs ecrivains : le rattrapage
    # acquereurs a ete tue par « database is locked » parce que la Descente (07:30,
    # pull_from_supabase) ecrivait au meme moment et que le defaut de sqlite3 est 5 s.
    # Meme reglage que hektor_pipeline.common.connect_db, qui lui a tenu.
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_contacts_schema(conn: sqlite3.Connection) -> None:
    relation_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(app_contact_relation_current)").fetchall()
    }
    if relation_columns and "relation_key" not in relation_columns:
        conn.execute("DROP TABLE app_contact_relation_current")

    # ⚠ L4-c ④ 22/09 : CREATE TABLE IF NOT EXISTS N'AJOUTE RIEN A UNE TABLE
    #   DEJA CREEE. Lecon payee le matin meme : le recensement des relations
    #   demandait une colonne que son DDL declarait, mais que la table posee la
    #   veille n'avait pas -- l'INSERT tombait, et le run disait « succes ».
    #   On rattrape donc explicitement les installations existantes, a chaque
    #   passage. Idempotent : la colonne presente n'est pas re-ajoutee.
    colonnes_contact = {
        row["name"] for row in conn.execute("PRAGMA table_info(app_contact_current)").fetchall()
    }
    if colonnes_contact and "hektor_target_id" not in colonnes_contact:
        conn.execute("ALTER TABLE app_contact_current ADD COLUMN hektor_target_id TEXT")

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS app_contact_current (
            hektor_contact_id TEXT PRIMARY KEY,
            -- L4-c ④ 22/09 : LE numero pour viser Hektor. Tant qu'identite et
            -- cible sont egales il ne sert a rien ; le jour de la bascule, il
            -- est la SEULE chose qui garde le parc joignable (voir ContactRow).
            hektor_target_id TEXT,
            hektor_agence_id TEXT,
            hektor_negociateur_id TEXT,
            negociateur_email TEXT,
            commercial_nom TEXT,
            agence_nom TEXT,
            civilite TEXT,
            nom TEXT,
            prenom TEXT,
            display_name TEXT NOT NULL,
            -- Le MENAGE. `hektor_couple_contact_id` est la reference de Hektor,
            -- assumee comme telle ; le numero de l'app arrive apres, pose par le
            -- registre d'identite. `couple_role` est ce que l'ecran lit.
            hektor_couple_contact_id TEXT,
            couple_role TEXT,
            archive INTEGER NOT NULL DEFAULT 0,
            date_enregistrement TEXT,
            date_maj TEXT,
            email TEXT,
            phone_primary TEXT,
            phone_secondary TEXT,
            ville TEXT,
            code_postal TEXT,
            adresse TEXT,
            typologies_json TEXT NOT NULL DEFAULT '[]',
            relation_roles_json TEXT NOT NULL DEFAULT '[]',
            linked_annonce_count INTEGER NOT NULL DEFAULT 0,
            active_search_count INTEGER NOT NULL DEFAULT 0,
            total_search_count INTEGER NOT NULL DEFAULT 0,
            has_contact_detail INTEGER NOT NULL DEFAULT 0,
            contact_detail_synced_at TEXT,
            supabase_sync_eligible INTEGER NOT NULL DEFAULT 0,
            eligibility_reasons_json TEXT NOT NULL DEFAULT '[]',
            duplicate_group_count INTEGER NOT NULL DEFAULT 0,
            duplicate_max_severity TEXT,
            duplicate_primary_candidate_id TEXT,
            completeness_score INTEGER NOT NULL DEFAULT 0,
            source_hash TEXT NOT NULL,
            refreshed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS app_contact_relation_current (
            relation_key TEXT PRIMARY KEY,
            hektor_contact_id TEXT NOT NULL,
            hektor_annonce_id TEXT NOT NULL,
            app_dossier_id INTEGER,
            numero_dossier TEXT,
            numero_mandat TEXT,
            titre_bien TEXT,
            role_contact TEXT NOT NULL,
            contact_date_maj TEXT,
            relation_source TEXT NOT NULL DEFAULT 'api_annonce_detail',
            transaction_type TEXT,
            transaction_id TEXT,
            transaction_state TEXT,
            transaction_date TEXT,
            transaction_amount TEXT,
            is_active_annonce INTEGER NOT NULL DEFAULT 0,
            last_seen_at TEXT,
            refreshed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS app_contact_search_current (
            contact_search_key TEXT PRIMARY KEY,
            app_search_id INTEGER,
            hektor_contact_id TEXT NOT NULL,
            search_index INTEGER NOT NULL,
            archive INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 0,
            offre TEXT,
            villes_json TEXT NOT NULL DEFAULT '[]',
            types_json TEXT NOT NULL DEFAULT '[]',
            criteres_json TEXT NOT NULL DEFAULT '[]',
            prix_min TEXT,
            prix_max TEXT,
            surface_min TEXT,
            surface_max TEXT,
            pieces_min TEXT,
            pieces_max TEXT,
            chambre_min TEXT,
            chambre_max TEXT,
            surface_terrain_min TEXT,
            surface_terrain_max TEXT,
            contact_date_maj TEXT,
            refreshed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS app_contact_duplicate_group_current (
            duplicate_group_id TEXT PRIMARY KEY,
            rule_code TEXT NOT NULL,
            severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
            review_status TEXT NOT NULL DEFAULT 'proposed',
            archive_pattern TEXT NOT NULL,
            member_count INTEGER NOT NULL,
            active_count INTEGER NOT NULL,
            archived_count INTEGER NOT NULL,
            linked_annonce_count INTEGER NOT NULL DEFAULT 0,
            primary_candidate_hektor_contact_id TEXT,
            normalized_key_hash TEXT NOT NULL,
            suspected_mass_archive_error INTEGER NOT NULL DEFAULT 0,
            review_hint TEXT,
            refreshed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS app_contact_duplicate_member_current (
            duplicate_group_id TEXT NOT NULL,
            hektor_contact_id TEXT NOT NULL,
            is_primary_candidate INTEGER NOT NULL DEFAULT 0,
            archive INTEGER NOT NULL DEFAULT 0,
            display_name TEXT NOT NULL,
            email_hash TEXT,
            phone_hash TEXT,
            date_maj TEXT,
            linked_annonce_count INTEGER NOT NULL DEFAULT 0,
            completeness_score INTEGER NOT NULL DEFAULT 0,
            member_rank INTEGER NOT NULL DEFAULT 0,
            refreshed_at TEXT NOT NULL,
            PRIMARY KEY (duplicate_group_id, hektor_contact_id)
        );

        CREATE TABLE IF NOT EXISTS app_contact_audit_run (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL,
            contacts_total INTEGER NOT NULL,
            contacts_active INTEGER NOT NULL,
            contacts_archived INTEGER NOT NULL,
            duplicate_group_total INTEGER NOT NULL,
            duplicate_member_total INTEGER NOT NULL,
            high_or_critical_group_total INTEGER NOT NULL,
            suspected_mass_archive_error_total INTEGER NOT NULL,
            report_summary_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_app_contact_current_archive
            ON app_contact_current(archive, date_maj);
        CREATE INDEX IF NOT EXISTS idx_app_contact_current_name
            ON app_contact_current(nom, prenom);
        CREATE INDEX IF NOT EXISTS idx_app_contact_current_email
            ON app_contact_current(email);
        CREATE INDEX IF NOT EXISTS idx_app_contact_current_phone
            ON app_contact_current(phone_primary);
        CREATE INDEX IF NOT EXISTS idx_app_contact_current_nego
            ON app_contact_current(negociateur_email, hektor_negociateur_id);
        CREATE INDEX IF NOT EXISTS idx_app_contact_relation_contact
            ON app_contact_relation_current(hektor_contact_id);
        CREATE INDEX IF NOT EXISTS idx_app_contact_relation_annonce
            ON app_contact_relation_current(hektor_annonce_id);
        CREATE INDEX IF NOT EXISTS idx_app_contact_relation_transaction
            ON app_contact_relation_current(transaction_type, transaction_id);
        CREATE INDEX IF NOT EXISTS idx_app_contact_relation_role_active
            ON app_contact_relation_current(role_contact, is_active_annonce);
        CREATE INDEX IF NOT EXISTS idx_app_contact_search_contact
            ON app_contact_search_current(hektor_contact_id);
        CREATE INDEX IF NOT EXISTS idx_app_contact_search_active
            ON app_contact_search_current(is_active, archive);
        CREATE INDEX IF NOT EXISTS idx_app_contact_duplicate_severity
            ON app_contact_duplicate_group_current(severity, suspected_mass_archive_error);
        CREATE INDEX IF NOT EXISTS idx_app_contact_duplicate_member_contact
            ON app_contact_duplicate_member_current(hektor_contact_id);
        """
    )
    existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(app_contact_current)").fetchall()}
    for column_name, column_type in (
        ("negociateur_email", "TEXT"),
        ("commercial_nom", "TEXT"),
        ("agence_nom", "TEXT"),
        ("active_search_count", "INTEGER NOT NULL DEFAULT 0"),
        ("total_search_count", "INTEGER NOT NULL DEFAULT 0"),
        ("has_contact_detail", "INTEGER NOT NULL DEFAULT 0"),
        ("contact_detail_synced_at", "TEXT"),
        ("supabase_sync_eligible", "INTEGER NOT NULL DEFAULT 0"),
        ("eligibility_reasons_json", "TEXT NOT NULL DEFAULT '[]'"),
        ("adresse", "TEXT"),
        # Le menage, 11/09/2026. La table n'est jamais recreee -- elle est videe
        # puis remplie -- donc sans ces deux lignes l'insertion tomberait sur
        # « no such column » des le premier run.
        ("hektor_couple_contact_id", "TEXT"),
        ("couple_role", "TEXT"),
    ):
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE app_contact_current ADD COLUMN {column_name} {column_type}")
    conn.commit()


def load_contacts(
    conn: sqlite3.Connection,
    limit: int | None = None,
    contact_ids: Iterable[str] | None = None,
) -> list[ContactRow]:
    ids = normalize_contact_ids(contact_ids or [])
    params: list[Any] = []
    sql = """
        SELECT hektor_contact_id, hektor_agence_id, hektor_negociateur_id, civilite, nom, prenom,
               archive, date_enregistrement, date_maj, email, portable, fixe, ville, code_postal, adresse,
               typologie_json, raw_json, synced_at, hektor_couple_contact_id
        FROM hektor_contact
        WHERE NULLIF(TRIM(hektor_contact_id), '') IS NOT NULL
    """
    if ids:
        placeholders = ",".join("?" for _ in ids)
        sql += f" AND CAST(hektor_contact_id AS TEXT) IN ({placeholders})\n"
        params.extend(ids)
    sql += " ORDER BY CAST(hektor_contact_id AS INTEGER)"
    if limit and limit > 0:
        sql += f" LIMIT {int(limit)}"
    return resoudre_menages(conn, [contact_from_row(row) for row in conn.execute(sql, params).fetchall()])


def resoudre_menages(conn: sqlite3.Connection, contacts: list[ContactRow]) -> list[ContactRow]:
    """Donne a chaque fiche de menage l'identite de sa porteuse.

    ⚠ ON CHERCHE EN BASE, PAS DANS LE LOT. `load_contacts` accepte une liste
      d'identifiants -- c'est ce que fait refresh_contact_inproc.py pour un seul
      contact. La porteuse n'est alors PAS dans le lot charge, et se contenter de
      la chercher en memoire donnerait « Contact 457053 » a une fiche dont le nom
      existe. Une requete, quelle que soit la taille du lot.

    ⚠ ON NE FABRIQUE AUCUN NOM. Si la porteuse a disparu de Hektor -- 14 080 cas
      sur 124 455 liens, verifie par appel API qui repond 404 -- le champ reste
      vide et l'affichage retombe sur le numero. « Mieux vaut un champ absent
      qu'un champ menteur. »
    """
    a_resoudre = {c.hektor_couple_contact_id for c in contacts if c.est_fiche_de_menage}
    a_resoudre.discard(None)
    if not a_resoudre:
        return contacts

    # ── G-13, 23/09/2026 : LA TRADUCTION ALLAIT DANS LE MAUVAIS SENS ───────
    # `hektor_couple_contact_id` a DEJA ete traduit en identite a l'entree du
    # build (contact_from_row). Mais la requete ci-dessous interroge le MIROIR,
    # qui ne connait que les numeros de Hektor. Chercher une identite dedans ne
    # rend rien -- et le defaut serait MUET : le nom de la porteuse resterait
    # vide et l'ecran retomberait sur le numero, exactement le « Contact 457053 »
    # que cette fonction existe pour eviter.
    # On interroge donc avec le numero DU MIROIR, et on range le resultat sous
    # l'identite, qui est ce que les fiches portent.
    identites: dict[str, str] = {}
    ids = [str(x) for x in a_resoudre]
    identite_par_numero_miroir = {numero_hektor_pour_le_miroir(i): i for i in ids}
    numeros_miroir = list(identite_par_numero_miroir.keys())
    # SQLite plafonne le nombre de parametres : on decoupe, comme partout ailleurs.
    for depart in range(0, len(numeros_miroir), 400):
        tranche = numeros_miroir[depart:depart + 400]
        marques = ",".join("?" for _ in tranche)
        for ligne in conn.execute(
            f"""SELECT hektor_contact_id, prenom, nom FROM hektor_contact
                 WHERE CAST(hektor_contact_id AS TEXT) IN ({marques})""",
            tranche,
        ).fetchall():
            identite = " ".join(
                part for part in [clean_text(ligne["prenom"]), clean_text(ligne["nom"])] if part
            )
            if identite:
                lu = clean_text(ligne["hektor_contact_id"])
                identites[identite_par_numero_miroir.get(lu, lu)] = identite

    if not identites:
        return contacts
    return [
        replace(c, couple_identite_porteuse=identites.get(c.hektor_couple_contact_id))
        if c.est_fiche_de_menage else c
        for c in contacts
    ]


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    return conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone() is not None


def load_active_annonce_ids(hektor_conn: sqlite3.Connection) -> set[str]:
    if table_exists(hektor_conn, "case_dossier_source"):
        return {
            clean_text(row["hektor_annonce_id"])
            for row in hektor_conn.execute(
                """
                SELECT hektor_annonce_id
                FROM case_dossier_source
                WHERE COALESCE(archive, '0') = '0'
                  AND NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL
                """
            )
        }
    if table_exists(hektor_conn, "hektor_annonce"):
        return {
            clean_text(row["hektor_annonce_id"])
            for row in hektor_conn.execute(
                """
                SELECT hektor_annonce_id
                FROM hektor_annonce
                WHERE COALESCE(archive, '0') = '0'
                  AND NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL
                """
            )
        }
    return set()


def contact_id_from_payload(value: Any) -> str:
    item = value[0] if isinstance(value, list) and value and isinstance(value[0], dict) else value
    if not isinstance(item, dict):
        return ""
    # L4-b (②) : meme substitution que partout ailleurs -- les relations doivent
    # designer la personne par son identite, sinon elles pendent sous la seconde
    # fiche au lieu de la premiere.
    return identite_app(
        first_non_empty(item.get("id"), item.get("id_contact"), item.get("contact_id")) or "")


# ═══════════════════════════════════════════════════════════════════════════
# C.9-d 24/09/2026 — LE CARNET DES LIENS (app_relation_registry), EN DOUBLURE
# ═══════════════════════════════════════════════════════════════════════════
# Audit : notice/AUDIT_C9_ANNONCE_NEE_DANS_APP_2026-09-24.md (D5).
#
# L'identifiant d'un lien (relation_key) est FABRIQUE a partir de sa recette :
# le contact, le numero HEKTOR du bien, le role, la source, la transaction. Le
# jour ou un bien n'aura plus de numero Hektor (ne dans l'app, apres la coupure),
# la recette ne pourra plus rien fabriquer. C.9-f la fera donc avec NOTRE numero
# de bien -- et sans ce carnet, les 167 000 identifiants changeraient d'un coup.
#
# CE CARNET NOTE, pour chaque lien ECRIT, son identifiant et SA RECETTE EXACTE
# (celle qui a servi au hache), plus notre numero de bien. C.9-f y lira
# l'identifiant fige d'un lien deja connu. D'ici la, PERSONNE NE LE LIT : il
# observe. Aucun identifiant ne change.
#
# ⚠ LA RECETTE EST PRISE A LA SOURCE, dans add_relation : le role est reecrit
#   plus bas (mandant / proprietaire), et relire la table ne retrouve
#   l'identifiant que pour 57 % des liens (mesure du 24/09).
# ⚠ SEUL LE BUILD COMPLET l'ecrit : le build cible ne voit qu'une poignee de
#   liens, et marquerait « disparus » tous les autres.
# ⚠ IL NE PEUT PAS FAIRE TOMBER LE BUILD : tout se passe dans un SAVEPOINT ; a la
#   moindre erreur, ses ecritures sont annulees et le build continue.
# RETOUR ARRIERE : retirer l'appel dans build_contacts_layer ; DROP TABLE app_relation_registry.
_ANCRES_RELATIONS: dict[str, dict[str, Any]] = {}

# ═══════════════════════════════════════════════════════════════════════════
# C.9-f 25/09/2026 — L'IDENTIFIANT D'UN LIEN SE FABRIQUE AVEC *NOTRE* NUMERO
# ═══════════════════════════════════════════════════════════════════════════
# Jusqu'ici la recette prenait le numero HEKTOR du bien. Apres la coupure, un
# bien ne dans l'app n'en aura plus : la recette ne pourrait plus rien fabriquer.
# Elle prend donc desormais NOTRE numero (app_dossier_id).
#
# ⚠ SEUL, ce changement refabriquerait 167 487 identifiants d'un coup (mesure du
#   25/09). Le push supprimerait puis reposerait 167 000 lignes en une nuit --
#   c'est ce qui a sature Supabase le 22/08. D'OU LE CARNET (C.9-d) : pour un
#   lien DEJA CONNU, on reprend l'identifiant qu'il avait ; seul un lien NEUF
#   recoit un identifiant fabrique avec notre numero. Attendu : 0 change.
#
# L'ancre (contact, notre n° de bien, role, source, type et n° de transaction)
# ne laisse qu'UN champ libre dans la recette : le numero du bien. Le carnet rend
# donc simplement CELUI QUI A SERVI AU HACHE, et la recette rejouee redonne
# exactement le meme identifiant.
#
# TROIS CAS, dans cet ordre :
#   ancre connue du carnet   -> on REPREND le numero d'origine (rien ne change)
#   ancre inconnue (neuf)    -> NOTRE numero
#   pas de numero chez nous  -> repli : le numero Hektor (9 liens le 25/09,
#                               des biens que Hektor lui-meme ne connait plus)
# Un lien disparu puis revenu retrouve son identifiant : le carnet n'efface rien.
#
# DEUX GARDE-FOUS, parce qu'ici un defaut ne crie jamais :
#   a l'entree  carnet absent ou trop court   -> on ne substitue pas du tout
#   a la sortie trop d'identifiants changes   -> on RECOMMENCE sans substituer,
#               donc exactement le comportement d'avant (build_contacts_layer)
# RETOUR ARRIERE : appeler load_relations(..., substituer=False).
_CLES_FIGEES: dict[tuple[str, ...], str | None] = {}

# Au-dela de ce nombre d'identifiants disparus en une nuit, on ne croit plus la
# substitution : un run ordinaire en voit quelques-uns (6 le 24/09, mouvements
# reels chez Hektor), jamais des centaines.
SEUIL_CLES_CHANGEES = 1000


def _ancre_relation(contact_id, app_dossier_id, role, source, transaction_type, transaction_id):
    """L'ancre d'un lien : tout ce qui l'identifie SAUF le numero du bien.

    Les deux cotes (le carnet relu, et add_relation) doivent la fabriquer
    pareil : le carnet rend du JSON (entier ou texte), add_relation des valeurs
    Python. On ramene tout a du texte, et le vide et l'absent se valent.
    """
    def part(v):
        return "" if v is None else str(v)
    return (part(contact_id), part(app_dossier_id), part(role), part(source),
            part(transaction_type), part(transaction_id))


def charger_cles_figees(conn: sqlite3.Connection) -> tuple[dict, dict]:
    """Relit le carnet : ancre -> le numero de bien qui a SERVI au hache.

    Sans filtrer absent_depuis : un lien revenu doit retrouver son identifiant.
    Une ancre portee par deux identifiants differents est AMBIGUE -- on ne
    reprend alors rien pour elle (0 cas mesure le 25/09).
    """
    try:
        lignes = conn.execute(
            "SELECT relation_key, contact_id, app_dossier_id, role, source,"
            " json_extract(recette_json, '$.transaction_type'),"
            " json_extract(recette_json, '$.transaction_id'),"
            " json_extract(recette_json, '$.annonce_id')"
            " FROM app_relation_registry WHERE app_dossier_id IS NOT NULL").fetchall()
    except sqlite3.Error as exc:
        return {}, {"statut": "carnet_illisible", "erreur": type(exc).__name__}
    cles: dict[tuple[str, ...], str | None] = {}
    ambigues = 0
    for _cle, contact, dossier, role, source, ttype, tid, annonce in lignes:
        ancre = _ancre_relation(contact, dossier, role, source, ttype, tid)
        annonce = None if annonce is None else str(annonce)
        if ancre not in cles:
            cles[ancre] = annonce
        elif cles[ancre] != annonce:
            cles[ancre] = None  # ambigue : on laissera fabriquer
            ambigues += 1
    return cles, {"statut": "ok", "notes": len(lignes), "ancres": len(cles), "ambigues": ambigues}

REGISTRE_RELATIONS_DDL = """
CREATE TABLE IF NOT EXISTS app_relation_registry (
    relation_key      TEXT PRIMARY KEY,
    contact_id        TEXT NOT NULL,
    app_dossier_id    INTEGER,
    hektor_annonce_id TEXT,
    role              TEXT,
    source            TEXT,
    recette_json      TEXT NOT NULL,
    first_seen_at     TEXT NOT NULL,
    last_seen_at      TEXT NOT NULL,
    absent_depuis     TEXT
);
CREATE INDEX IF NOT EXISTS idx_relation_registry_ancre
    ON app_relation_registry(contact_id, app_dossier_id, role, source);
"""


def enregistrer_registre_relations(
    conn: sqlite3.Connection, cles_ecrites: list[str], refreshed_at: str, complet: bool,
) -> dict[str, Any]:
    """Consigne dans le carnet les liens reellement ecrits. Ne leve JAMAIS."""
    try:
        conn.execute("SAVEPOINT registre_relations")
    except sqlite3.Error as exc:
        print(f"[carnet des liens] non ouvert ({type(exc).__name__}) -- le build continue")
        return {"statut": "erreur", "erreur": type(exc).__name__}
    try:
        for instruction in REGISTRE_RELATIONS_DDL.strip().split(";"):
            if instruction.strip():
                conn.execute(instruction)
        lignes = []
        sans_recette = 0
        for cle in cles_ecrites:
            ancre = _ANCRES_RELATIONS.get(cle)
            if ancre is None:
                sans_recette += 1
                continue
            recette = ancre["recette"]
            lignes.append((
                cle, recette["contact_id"], ancre["app_dossier_id"], recette["annonce_id"],
                recette["role"], recette["source"],
                json.dumps(recette, ensure_ascii=True, sort_keys=True, separators=(",", ":")),
                refreshed_at, refreshed_at))
        avant = conn.execute("SELECT COUNT(*) FROM app_relation_registry").fetchone()[0]
        conn.executemany(
            "INSERT INTO app_relation_registry (relation_key, contact_id, app_dossier_id, "
            "hektor_annonce_id, role, source, recette_json, first_seen_at, last_seen_at) "
            "VALUES (?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(relation_key) DO UPDATE SET last_seen_at = excluded.last_seen_at, "
            "absent_depuis = NULL, "
            "app_dossier_id = COALESCE(app_relation_registry.app_dossier_id, excluded.app_dossier_id)",
            lignes)
        apres = conn.execute("SELECT COUNT(*) FROM app_relation_registry").fetchone()[0]
        absentes = 0
        if complet:
            absentes = conn.execute(
                "UPDATE app_relation_registry SET absent_depuis = ? "
                "WHERE absent_depuis IS NULL AND last_seen_at < ?",
                (refreshed_at, refreshed_at)).rowcount or 0
        conflits = conn.execute(
            "SELECT COUNT(*) FROM (SELECT 1 FROM app_relation_registry "
            " WHERE absent_depuis IS NULL AND app_dossier_id IS NOT NULL "
            " GROUP BY contact_id, app_dossier_id, role, source, "
            "          json_extract(recette_json, '$.transaction_type'), "
            "          json_extract(recette_json, '$.transaction_id') "
            " HAVING COUNT(*) > 1)").fetchone()[0]
        sans_dossier = conn.execute(
            "SELECT COUNT(*) FROM app_relation_registry "
            "WHERE absent_depuis IS NULL AND app_dossier_id IS NULL").fetchone()[0]
        conn.execute("RELEASE registre_relations")
        bilan = {"statut": "ok", "ecrits": len(lignes), "nouveaux": apres - avant,
                 "disparus_marques": absentes, "carnet": apres, "ancres_en_conflit": conflits,
                 "sans_numero_de_bien": sans_dossier, "sans_recette": sans_recette,
                 "complet": complet}
        print(f"[carnet des liens] {len(lignes)} liens notes, {apres - avant} nouveaux, "
              f"{absentes} marques disparus, conflits {conflits}, sans numero de bien {sans_dossier}, "
              f"sans recette {sans_recette} (carnet : {apres})")
        return bilan
    except Exception as exc:
        try:
            conn.execute("ROLLBACK TO registre_relations")
            conn.execute("RELEASE registre_relations")
        except sqlite3.Error:
            pass
        print(f"[carnet des liens] ERREUR ({type(exc).__name__}) -- ecritures annulees, le build continue")
        return {"statut": "erreur", "erreur": type(exc).__name__}


def load_relations(
    hektor_conn: sqlite3.Connection,
    phase2_conn: sqlite3.Connection,
    contact_ids: Iterable[str] | None = None,
    substituer: bool = True,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, set[str]]]:
    contact_filter = set(normalize_contact_ids(contact_ids or []))
    _ANCRES_RELATIONS.clear()  # C.9-d : les recettes de CETTE lecture seulement
    # ── C.9-f : le carnet, et le garde-fou D'ENTREE ─────────────────────────
    global _CLES_FIGEES
    _CLES_FIGEES = {}
    if substituer:
        cles, bilan = charger_cles_figees(phase2_conn)
        deja_ecrits = 0
        try:
            deja_ecrits = phase2_conn.execute(
                "SELECT COUNT(*) FROM app_contact_relation_current").fetchone()[0]
        except sqlite3.Error:
            deja_ecrits = 0
        # Un carnet absent ou nettement plus court que la couche ne peut pas
        # figer les identifiants existants : substituer les refabriquerait tous.
        if deja_ecrits > 1000 and len(cles) < 0.9 * deja_ecrits:
            print(f"[numero de bien dans la cle] REFUS : le carnet ne couvre que "
                  f"{len(cles)} ancres pour {deja_ecrits} liens ecrits -- on garde le "
                  f"numero Hektor (comportement d'avant)")
        else:
            _CLES_FIGEES = cles
            print(f"[numero de bien dans la cle] carnet : {bilan.get('ancres', 0)} ancres "
                  f"({bilan.get('ambigues', 0)} ambigues) pour {deja_ecrits} liens ecrits")
    # ── G-14, 23/09/2026 : DEUX TAMIS, PARCE QU'IL Y A DEUX LANGUES ─────────
    # `contact_filter` sert aux requetes SQL ci-dessous, qui interrogent LE
    # MIROIR : il doit rester en numeros de Hektor (refresh_contact_slice lui
    # passe `ids_miroir`, l. 1757).
    # Mais `add_relation` compare APRES la substitution d'identite, donc en
    # numeros A NOUS. Le meme ensemble ne peut pas servir aux deux : le jour de
    # la bascule, les deux cotes ne se rencontreraient JAMAIS et toutes les
    # relations du contact rafraichi seraient jetees -- en silence.
    # Aujourd'hui les deux ensembles sont identiques.
    contact_filter_apres_substitution = {
        identite_app(cid) for cid in contact_filter} | set(contact_filter)
    dossier_by_annonce: dict[str, sqlite3.Row] = {}
    for row in phase2_conn.execute(
        """
        SELECT d.id AS app_dossier_id, d.hektor_annonce_id, d.numero_dossier, d.numero_mandat, vg.titre_bien
        FROM app_dossier d
        LEFT JOIN app_view_generale vg ON vg.app_dossier_id = d.id
        WHERE d.hektor_annonce_id IS NOT NULL
        """
    ):
        dossier_by_annonce[clean_text(row["hektor_annonce_id"])] = row

    active_annonce_ids = load_active_annonce_ids(hektor_conn)
    relation_by_key: dict[str, dict[str, Any]] = {}
    contact_filter_placeholders = ",".join("?" for _ in contact_filter)
    contact_filter_params = sorted(contact_filter)

    def add_relation(
        *,
        contact_id: str,
        annonce_id: str,
        role: str,
        contact_date_maj: str | None,
        relation_source: str,
        last_seen_at: str | None,
        transaction_type: str | None = None,
        transaction_id: str | None = None,
        transaction_state: str | None = None,
        transaction_date: str | None = None,
        transaction_amount: str | None = None,
    ) -> None:
        # ⚠ L4-c ① 22/09 : LA SUBSTITUTION SE FAIT ICI, ET NULLE PART AILLEURS.
        # C'est LE point de passage de toutes les sources de relations. Le 21/09
        # je l'avais posee sur DEUX entrees seulement (le payload des relations
        # et les lignes de detail) -- trois autres sources l'evitaient :
        #     api_annonce_detail_proprietaires   75 543 relations
        #     sync_annonce_contact_link          50 524
        #     api_list_offres                    11 137
        # La repetition du 22/09 l'a montre sans ambiguite : en simulant la
        # bascule, ces trois sources tombaient a ZERO et le total perdait
        # 11 270 relations. Elles gardaient le numero de Hektor pendant que la
        # couche des contacts portait celui de l'app : plus aucune
        # correspondance, donc « contact inconnu », donc jetees.
        # Une seule porte vaut mieux que cinq entrees a ne pas oublier.
        contact_id = identite_app(contact_id)
        annonce_id = clean_text(annonce_id)
        role = clean_text(role) or "contact"
        if not contact_id or not annonce_id:
            return
        # G-14 : le tamis D'APRES la substitution -- voir plus haut.
        if contact_filter and contact_id not in contact_filter_apres_substitution:
            return
        dossier = dossier_by_annonce.get(annonce_id)
        source_identity = relation_source if clean_text(transaction_id) else "non_transaction"
        # ── C.9-f : QUEL NUMERO DE BIEN ENTRE DANS LA RECETTE ────────────────
        # Par defaut celui de Hektor (repli : sans numero chez nous, on n'a rien
        # d'autre). Sinon : celui que le carnet a fige, ou le notre si le lien
        # est neuf. Voir l'en-tete de _CLES_FIGEES.
        annonce_pour_la_cle = annonce_id
        if dossier is not None and _CLES_FIGEES is not None:
            notre_numero = str(dossier["app_dossier_id"])
            figee = _CLES_FIGEES.get(_ancre_relation(
                contact_id, notre_numero, role, source_identity, transaction_type, transaction_id))
            annonce_pour_la_cle = figee if figee else notre_numero
        # C.9-d : la recette, nommee pour pouvoir la noter.
        recette = {
            "contact_id": contact_id,
            "annonce_id": annonce_pour_la_cle,
            "role": role,
            "source": source_identity,
            "transaction_type": transaction_type,
            "transaction_id": transaction_id,
        }
        relation_key = stable_hash(recette)[:24]
        _ANCRES_RELATIONS[relation_key] = {
            "recette": recette,
            "app_dossier_id": dossier["app_dossier_id"] if dossier else None,
        }
        relation_by_key[relation_key] = {
            "relation_key": relation_key,
            "hektor_contact_id": contact_id,
            "hektor_annonce_id": annonce_id,
            "app_dossier_id": dossier["app_dossier_id"] if dossier else None,
            "numero_dossier": dossier["numero_dossier"] if dossier else None,
            "numero_mandat": dossier["numero_mandat"] if dossier else None,
            "titre_bien": dossier["titre_bien"] if dossier else None,
            "role_contact": role,
            "contact_date_maj": clean_text(contact_date_maj) or None,
            "relation_source": relation_source,
            "transaction_type": clean_text(transaction_type) or None,
            "transaction_id": clean_text(transaction_id) or None,
            "transaction_state": clean_text(transaction_state) or None,
            "transaction_date": clean_text(transaction_date) or None,
            "transaction_amount": clean_text(transaction_amount) or None,
            "is_active_annonce": int(annonce_id in active_annonce_ids),
            "last_seen_at": clean_text(last_seen_at) or None,
        }

    if table_exists(hektor_conn, "hektor_annonce_detail") and not contact_filter:
        for row in hektor_conn.execute(
            """
            SELECT hektor_annonce_id, proprietaires_json, synced_at
            FROM hektor_annonce_detail
            WHERE NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL
              AND NULLIF(TRIM(proprietaires_json), '') IS NOT NULL
              AND TRIM(proprietaires_json) NOT IN ('[]', '{}', 'null')
            """
        ):
            for owner in json_items(row["proprietaires_json"]):
                add_relation(
                    contact_id=clean_text(owner.get("id")),
                    annonce_id=clean_text(row["hektor_annonce_id"]),
                    role="proprietaire",
                    contact_date_maj=clean_text(owner.get("datemaj")),
                    relation_source="api_annonce_detail_proprietaires",
                    last_seen_at=clean_text(row["synced_at"]) or None,
                )

    if table_exists(hektor_conn, "sync_annonce_contact_link"):
        link_where = """
            WHERE NULLIF(TRIM(hektor_contact_id), '') IS NOT NULL
              AND NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL
        """
        link_params: list[Any] = []
        if contact_filter:
            link_where += f" AND CAST(hektor_contact_id AS TEXT) IN ({contact_filter_placeholders})"
            link_params.extend(contact_filter_params)
        for row in hektor_conn.execute(
            f"""
            SELECT hektor_annonce_id, hektor_contact_id, role_contact, contact_date_maj, last_seen_at
            FROM sync_annonce_contact_link
            {link_where}
            """,
            link_params,
        ):
            add_relation(
                contact_id=clean_text(row["hektor_contact_id"]),
                annonce_id=clean_text(row["hektor_annonce_id"]),
                role=clean_text(row["role_contact"]) or "contact",
                contact_date_maj=clean_text(row["contact_date_maj"]) or None,
                relation_source="sync_annonce_contact_link",
                last_seen_at=clean_text(row["last_seen_at"]) or None,
            )

    if table_exists(hektor_conn, "hektor_offre"):
        offre_where = "WHERE NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL"
        offre_params: list[Any] = []
        if contact_filter:
            offre_where += f" AND CAST(hektor_acquereur_id AS TEXT) IN ({contact_filter_placeholders})"
            offre_params.extend(contact_filter_params)
        for row in hektor_conn.execute(
            f"""
            SELECT hektor_offre_id, hektor_annonce_id, hektor_mandat_id, hektor_acquereur_id,
                   offre_state, offre_event_date, raw_date, raw_montant, acquereur_json, synced_at
            FROM hektor_offre
            {offre_where}
            """,
            offre_params,
        ):
            acquereur_items = json_items(row["acquereur_json"])
            acquereur = acquereur_items[0] if acquereur_items else {}
            add_relation(
                contact_id=first_non_empty(row["hektor_acquereur_id"], contact_id_from_payload(acquereur)) or "",
                annonce_id=clean_text(row["hektor_annonce_id"]),
                role="acquereur_offre",
                contact_date_maj=clean_text(acquereur.get("datemaj")) if isinstance(acquereur, dict) else None,
                relation_source="api_list_offres",
                transaction_type="offre",
                transaction_id=clean_text(row["hektor_offre_id"]),
                transaction_state=clean_text(row["offre_state"]),
                transaction_date=first_non_empty(row["offre_event_date"], row["raw_date"], row["synced_at"]),
                transaction_amount=clean_text(row["raw_montant"]),
                last_seen_at=clean_text(row["synced_at"]) or None,
            )

    if table_exists(hektor_conn, "hektor_compromis") and not contact_filter:
        for row in hektor_conn.execute(
            """
            SELECT hektor_compromis_id, hektor_annonce_id, hektor_mandat_id, compromis_state,
                   date_start, date_end, date_signature_acte, prix_publique, prix_net_vendeur,
                   acquereurs_json, synced_at
            FROM hektor_compromis
            WHERE NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL
            """
        ):
            for acquereur in json_items(row["acquereurs_json"]):
                add_relation(
                    contact_id=contact_id_from_payload(acquereur),
                    annonce_id=clean_text(row["hektor_annonce_id"]),
                    role="acquereur_compromis",
                    contact_date_maj=clean_text(acquereur.get("datemaj")),
                    relation_source="api_list_compromis",
                    transaction_type="compromis",
                    transaction_id=clean_text(row["hektor_compromis_id"]),
                    transaction_state=clean_text(row["compromis_state"]),
                    transaction_date=first_non_empty(row["date_start"], row["date_signature_acte"], row["date_end"], row["synced_at"]),
                    transaction_amount=first_non_empty(row["prix_publique"], row["prix_net_vendeur"]),
                    last_seen_at=clean_text(row["synced_at"]) or None,
                )

    if table_exists(hektor_conn, "hektor_vente") and not contact_filter:
        for row in hektor_conn.execute(
            """
            SELECT hektor_vente_id, hektor_annonce_id, hektor_mandat_id, date_vente, prix,
                   acquereurs_json, synced_at
            FROM hektor_vente
            WHERE NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL
            """
        ):
            for acquereur in json_items(row["acquereurs_json"]):
                add_relation(
                    contact_id=contact_id_from_payload(acquereur),
                    annonce_id=clean_text(row["hektor_annonce_id"]),
                    role="acquereur_vente",
                    contact_date_maj=clean_text(acquereur.get("datemaj")),
                    relation_source="api_list_ventes",
                    transaction_type="vente",
                    transaction_id=clean_text(row["hektor_vente_id"]),
                    transaction_state="vente",
                    transaction_date=first_non_empty(row["date_vente"], row["synced_at"]),
                    transaction_amount=clean_text(row["prix"]),
                    last_seen_at=clean_text(row["synced_at"]) or None,
                )

    existing_contact_annonce_pairs = {
        (row["hektor_contact_id"], row["hektor_annonce_id"])
        for row in relation_by_key.values()
    }
    if table_exists(hektor_conn, "raw_api_response"):
        raw_columns = {
            row["name"]
            for row in hektor_conn.execute("PRAGMA table_info(raw_api_response)").fetchall()
        }
        fetched_expr = "fetched_at" if "fetched_at" in raw_columns else "NULL AS fetched_at"
        raw_where = "endpoint_name = 'contact_detail'"
        raw_params: list[Any] = []
        if contact_filter:
            raw_where += f" AND (CAST(object_id AS TEXT) IN ({contact_filter_placeholders}) OR CAST(object_id_key AS TEXT) IN ({contact_filter_placeholders}))"
            raw_params.extend(contact_filter_params)
            raw_params.extend(contact_filter_params)
        detail_rows = hektor_conn.execute(
            f"""
            SELECT object_id, object_id_key, payload_json, {fetched_expr}
            FROM raw_api_response
            WHERE {raw_where}
            ORDER BY id DESC
            """,
            raw_params,
        ).fetchall()
        seen_contacts: set[str] = set()
        for row in detail_rows:
            # L4-b (②) : substitution a l'entree (voir identite_app).
            contact_id = identite_app(first_non_empty(row["object_id_key"], row["object_id"]))
            if not contact_id or contact_id in seen_contacts:
                continue
            seen_contacts.add(contact_id)
            try:
                payload = json.loads(row["payload_json"])
            except json.JSONDecodeError:
                continue
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, dict):
                continue
            contact_payload = data.get("contact") if isinstance(data.get("contact"), dict) else {}
            contact_date_maj = clean_text(contact_payload.get("datemaj") or contact_payload.get("date_maj")) or None
            for annonce in json_items(data.get("annonces")):
                annonce_id = clean_text(annonce.get("id"))
                pair = (clean_text(contact_id), annonce_id)
                if not annonce_id or pair in existing_contact_annonce_pairs:
                    continue
                add_relation(
                    contact_id=clean_text(contact_id),
                    annonce_id=annonce_id,
                    role="mandant",
                    contact_date_maj=contact_date_maj or clean_text(annonce.get("datemaj")) or None,
                    relation_source="api_contact_detail_annonces",
                    last_seen_at=clean_text(row["fetched_at"]) or None,
                )
                existing_contact_annonce_pairs.add(pair)

    relation_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    roles_by_contact: dict[str, set[str]] = defaultdict(set)
    for row in relation_by_key.values():
        contact_id = row["hektor_contact_id"]
        # Règle mandant/propriétaire : côté vente, on distingue par la PRÉSENCE d'un numéro de
        # mandat (mandant = bien sous mandat) plutôt que par la source du lien (annonce vs fiche).
        # Réassigne aussi role_contact pour que la table relations ET relation_roles_json soient
        # cohérents. Les rôles acquéreur/notaire/etc. ne sont pas touchés.
        if row.get("role_contact") in ("proprietaire", "mandant"):
            row["role_contact"] = "mandant" if clean_text(row.get("numero_mandat")) else "proprietaire"
        roles_by_contact[contact_id].add(row["role_contact"])
        relation_rows[contact_id].append(row)
    return relation_rows, roles_by_contact


def criteria_map(search: dict[str, Any]) -> dict[str, str]:
    output: dict[str, str] = {}
    criteres = search.get("criteres")
    items: list[dict[str, Any]]
    if isinstance(criteres, list):
        items = [item for item in criteres if isinstance(item, dict)]
    elif isinstance(criteres, dict):
        items = [item for item in criteres.values() if isinstance(item, dict)]
    else:
        items = []
    for item in items:
        key = clean_text(item.get("cle"))
        if not key:
            continue
        value = clean_text(item.get("valeur"))
        if value:
            output[key] = value
    return output


def load_contact_searches(
    hektor_conn: sqlite3.Connection,
    contact_ids: Iterable[str] | None = None,
) -> tuple[list[dict[str, Any]], Counter[str], Counter[str]]:
    if not table_exists(hektor_conn, "raw_api_response"):
        return [], Counter(), Counter()

    ids = normalize_contact_ids(contact_ids or [])
    where_parts = ["endpoint_name = 'contact_detail'"]
    params: list[Any] = []
    if ids:
        placeholders = ",".join("?" for _ in ids)
        where_parts.append(f"(CAST(object_id AS TEXT) IN ({placeholders}) OR CAST(object_id_key AS TEXT) IN ({placeholders}))")
        params.extend(ids)
        params.extend(ids)

    search_rows: list[dict[str, Any]] = []
    total_counts: Counter[str] = Counter()
    active_counts: Counter[str] = Counter()
    rows = hektor_conn.execute(
        f"""
        SELECT object_id, object_id_key, payload_json
        FROM raw_api_response
        WHERE {" AND ".join(where_parts)}
        ORDER BY id DESC
        """,
        params,
    ).fetchall()
    seen_contacts: set[str] = set()
    for row in rows:
        # L4-b (②) : substitution a l'entree. Elle compte double ici : c'est
        # `contact_id` qui entre dans l'empreinte de la recherche, deux lignes
        # plus bas.
        contact_id = identite_app(first_non_empty(row["object_id_key"], row["object_id"]))
        if not contact_id or contact_id in seen_contacts:
            continue
        seen_contacts.add(contact_id)
        try:
            payload = json.loads(row["payload_json"])
        except json.JSONDecodeError:
            continue
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            continue
        contact_payload = data.get("contact") if isinstance(data.get("contact"), dict) else {}
        contact_date_maj = clean_text(contact_payload.get("datemaj") or contact_payload.get("date_maj")) or None
        recherches = data.get("recherches")
        if not isinstance(recherches, list):
            continue
        for index, search in enumerate(recherches):
            if not isinstance(search, dict):
                continue
            archive = parse_bool_archive(search.get("archive"))
            is_active = int(not archive)
            criteria = criteria_map(search)
            key_payload = {"contact_id": contact_id, "index": index, "search": search}
            search_key = stable_hash(key_payload)[:24]
            total_counts[contact_id] += 1
            active_counts[contact_id] += is_active
            search_rows.append(
                {
                    "contact_search_key": search_key,
                    "hektor_contact_id": contact_id,
                    "search_index": index,
                    "archive": archive,
                    "is_active": is_active,
                    "offre": clean_text(search.get("offre")) or None,
                    "villes_json": json_array(search.get("villes") or []),
                    "types_json": json.dumps(search.get("types") or {}, ensure_ascii=False, separators=(",", ":")),
                    "criteres_json": json.dumps(search.get("criteres") or [], ensure_ascii=False, separators=(",", ":")),
                    "prix_min": criteria.get("ITEM_PRIX_MIN"),
                    "prix_max": criteria.get("ITEM_PRIX_MAX"),
                    "surface_min": criteria.get("ITEM_SURFACE_MIN"),
                    "surface_max": criteria.get("ITEM_SURFACE_MAX"),
                    "pieces_min": criteria.get("ITEM_PIECES_MIN"),
                    "pieces_max": criteria.get("ITEM_PIECES_MAX"),
                    "chambre_min": criteria.get("ITEM_CHAMBRE_MIN"),
                    "chambre_max": criteria.get("ITEM_CHAMBRE_MAX"),
                    "surface_terrain_min": criteria.get("ITEM_SURFACE_TERRAIN_MIN"),
                    "surface_terrain_max": criteria.get("ITEM_SURFACE_TERRAIN_MAX"),
                    "contact_date_maj": contact_date_maj,
                }
            )
    return search_rows, total_counts, active_counts


def load_contact_detail_state(
    hektor_conn: sqlite3.Connection,
    contact_ids: Iterable[str] | None = None,
) -> dict[str, str | None]:
    ids = normalize_contact_ids(contact_ids or [])
    detail_state: dict[str, str | None] = {}
    if table_exists(hektor_conn, "sync_contact_state"):
        columns = {
            row["name"]
            for row in hektor_conn.execute("PRAGMA table_info(sync_contact_state)").fetchall()
        }
        if {"hektor_contact_id", "last_detail_sync_at"}.issubset(columns):
            state_where = "WHERE last_detail_sync_at IS NOT NULL"
            state_params: list[Any] = []
            if ids:
                placeholders = ",".join("?" for _ in ids)
                state_where += f" AND CAST(hektor_contact_id AS TEXT) IN ({placeholders})"
                state_params.extend(ids)
            for row in hektor_conn.execute(
                f"""
                SELECT hektor_contact_id, last_detail_sync_at
                FROM sync_contact_state
                {state_where}
                """,
                state_params,
            ).fetchall():
                contact_id = identite_app(row["hektor_contact_id"])  # L4-b (②)
                if contact_id:
                    detail_state[contact_id] = clean_text(row["last_detail_sync_at"]) or None

    if table_exists(hektor_conn, "raw_api_response"):
        raw_columns = {
            row["name"]
            for row in hektor_conn.execute("PRAGMA table_info(raw_api_response)").fetchall()
        }
        fetched_expr = "fetched_at" if "fetched_at" in raw_columns else "NULL AS fetched_at"
        raw_where = "endpoint_name = 'contact_detail'"
        raw_params: list[Any] = []
        if ids:
            placeholders = ",".join("?" for _ in ids)
            raw_where += f" AND (CAST(object_id AS TEXT) IN ({placeholders}) OR CAST(object_id_key AS TEXT) IN ({placeholders}))"
            raw_params.extend(ids)
            raw_params.extend(ids)
        rows = hektor_conn.execute(
            f"""
            SELECT object_id, object_id_key, {fetched_expr}
            FROM raw_api_response
            WHERE {raw_where}
            ORDER BY id DESC
            """,
            raw_params,
        ).fetchall()
        for row in rows:
            contact_id = identite_app(first_non_empty(row["object_id_key"], row["object_id"]))  # L4-b (②)
            if not contact_id:
                continue
            detail_state.setdefault(contact_id, clean_text(row["fetched_at"]) or None)
    return detail_state


def load_directory_maps(hektor_conn: sqlite3.Connection) -> tuple[dict[str, dict[str, str | None]], dict[str, str | None]]:
    negotiators: dict[str, dict[str, str | None]] = {}
    agencies: dict[str, str | None] = {}
    if hektor_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hektor_agence'").fetchone():
        for row in hektor_conn.execute("SELECT hektor_agence_id, nom FROM hektor_agence"):
            agencies[clean_text(row["hektor_agence_id"])] = clean_text(row["nom"]) or None
    if hektor_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hektor_negociateur'").fetchone():
        for row in hektor_conn.execute(
            """
            SELECT hektor_negociateur_id, hektor_agence_id, nom, prenom, email
            FROM hektor_negociateur
            """
        ):
            negotiator_id = clean_text(row["hektor_negociateur_id"])
            if not negotiator_id:
                continue
            display_name = " ".join(part for part in [clean_text(row["prenom"]), clean_text(row["nom"])] if part) or None
            agency_id = clean_text(row["hektor_agence_id"])
            negotiators[negotiator_id] = {
                "negociateur_email": clean_text(row["email"]) or None,
                "commercial_nom": display_name,
                "agence_nom": agencies.get(agency_id),
            }
    return negotiators, agencies


def duplicate_key_groups(contacts: Iterable[ContactRow]) -> dict[tuple[str, str], list[ContactRow]]:
    groups: dict[tuple[str, str], list[ContactRow]] = defaultdict(list)
    for contact in contacts:
        first = contact.first_name_normalized
        last = contact.last_name_normalized
        full_name = f"{first} {last}".strip()
        email = contact.email_normalized
        phone = contact.phone_normalized
        city = contact.city_normalized
        postal_code = contact.postal_code_normalized
        name_is_generic = not first and (not last or last in GENERIC_CONTACT_NAMES or full_name in GENERIC_CONTACT_NAMES)

        if email:
            groups[("exact_email", email)].append(contact)
        if email and phone and (first or last):
            groups[("exact_full_identity", f"{email}|{phone}|{first}|{last}")].append(contact)
        if phone and (first or last) and not name_is_generic:
            groups[("exact_phone_name", f"{phone}|{first}|{last}")].append(contact)
        if first and last and not name_is_generic and (city or postal_code):
            groups[("same_name_place", f"{first}|{last}|{city}|{postal_code}")].append(contact)
    return {key: group for key, group in groups.items() if len(group) >= 2}


def archive_pattern(group: list[ContactRow]) -> str:
    archived = sum(contact.archive for contact in group)
    active = len(group) - archived
    if active and archived:
        return "active_plus_archived"
    if archived:
        return "all_archived"
    return "all_active"


def group_severity(rule_code: str, group: list[ContactRow]) -> str:
    pattern = archive_pattern(group)
    if rule_code == "exact_full_identity":
        return "critical" if pattern == "active_plus_archived" or len(group) >= 5 else "high"
    if rule_code == "exact_email":
        return "critical" if len(group) >= 10 else "high"
    if rule_code == "exact_phone_name":
        return "high" if pattern == "active_plus_archived" or len(group) >= 5 else "medium"
    return "medium" if pattern == "active_plus_archived" else "low"


def primary_candidate(group: list[ContactRow], linked_counts: dict[str, int]) -> ContactRow:
    return sorted(
        group,
        key=lambda contact: (
            contact.archive,
            -linked_counts.get(contact.hektor_contact_id, 0),
            -contact.completeness_score,
            clean_text(contact.date_maj),
            clean_text(contact.date_enregistrement),
            -int(contact.hektor_contact_id) if contact.hektor_contact_id.isdigit() else 0,
        ),
    )[0]


def review_hint(rule_code: str, severity: str, pattern: str, member_count: int, archived_count: int) -> str:
    if severity == "critical" and pattern == "active_plus_archived":
        return "Priorite forte: identite identique avec fiche active et fiche(s) archivee(s). Ne pas supprimer; verifier fusion Hektor."
    if pattern == "active_plus_archived" and archived_count >= 1:
        return "Suspect transfert archive: conserver le candidat actif le plus complet, verifier les fiches archivees."
    if member_count >= 10:
        return "Groupe massif: verifier s'il s'agit d'une adresse partagée ou d'une creation automatique."
    if rule_code == "same_name_place":
        return "Probable uniquement: verifier manuellement avant fusion."
    return "Doublon probable: classer puis traiter manuellement."


def build_duplicate_records(
    contacts: list[ContactRow],
    linked_counts: dict[str, int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    group_rows: list[dict[str, Any]] = []
    member_rows: list[dict[str, Any]] = []
    best_duplicate_by_contact: dict[str, dict[str, Any]] = {}
    for (rule_code, normalized_key), group in duplicate_key_groups(contacts).items():
        sorted_group = sorted(group, key=lambda contact: int(contact.hektor_contact_id) if contact.hektor_contact_id.isdigit() else contact.hektor_contact_id)
        member_ids = [contact.hektor_contact_id for contact in sorted_group]
        active_count = sum(1 for contact in sorted_group if not contact.archive)
        archived_count = len(sorted_group) - active_count
        pattern = archive_pattern(sorted_group)
        severity = group_severity(rule_code, sorted_group)
        candidate = primary_candidate(sorted_group, linked_counts)
        linked_annonce_count = sum(linked_counts.get(contact.hektor_contact_id, 0) for contact in sorted_group)
        suspected_mass_archive_error = int(pattern == "active_plus_archived" and archived_count >= 1 and severity in {"high", "critical"})
        duplicate_group_id = stable_hash({"rule": rule_code, "members": member_ids})[:20]
        row = {
            "duplicate_group_id": duplicate_group_id,
            "rule_code": rule_code,
            "severity": severity,
            "archive_pattern": pattern,
            "member_count": len(sorted_group),
            "active_count": active_count,
            "archived_count": archived_count,
            "linked_annonce_count": linked_annonce_count,
            "primary_candidate_hektor_contact_id": candidate.hektor_contact_id,
            "normalized_key_hash": short_hash(normalized_key),
            "suspected_mass_archive_error": suspected_mass_archive_error,
            "review_hint": review_hint(rule_code, severity, pattern, len(sorted_group), archived_count),
        }
        group_rows.append(row)
        for rank, contact in enumerate(
            sorted(
                sorted_group,
                key=lambda item: (
                    0 if item.hektor_contact_id == candidate.hektor_contact_id else 1,
                    item.archive,
                    -linked_counts.get(item.hektor_contact_id, 0),
                    -item.completeness_score,
                ),
            ),
            start=1,
        ):
            member_rows.append(
                {
                    "duplicate_group_id": duplicate_group_id,
                    "hektor_contact_id": contact.hektor_contact_id,
                    "is_primary_candidate": int(contact.hektor_contact_id == candidate.hektor_contact_id),
                    "archive": contact.archive,
                    "display_name": contact.display_name,
                    "email_hash": short_hash(contact.email_normalized),
                    "phone_hash": short_hash(contact.phone_normalized),
                    "date_maj": contact.date_maj,
                    "linked_annonce_count": linked_counts.get(contact.hektor_contact_id, 0),
                    "completeness_score": contact.completeness_score,
                    "member_rank": rank,
                }
            )
            current = best_duplicate_by_contact.get(contact.hektor_contact_id)
            if current is None or SEVERITY_RANK[severity] > SEVERITY_RANK.get(str(current.get("severity")), 0):
                best_duplicate_by_contact[contact.hektor_contact_id] = row
    return group_rows, member_rows, best_duplicate_by_contact


def build_contact_rows(
    contacts: list[ContactRow],
    relation_rows: dict[str, list[dict[str, Any]]],
    roles_by_contact: dict[str, set[str]],
    total_search_counts: Counter[str],
    active_search_counts: Counter[str],
    duplicate_member_counts: Counter[str],
    best_duplicate_by_contact: dict[str, dict[str, Any]],
    negotiator_map: dict[str, dict[str, str | None]],
    agency_map: dict[str, str | None],
    contact_detail_state: dict[str, str | None],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for contact in contacts:
        roles = sorted(roles_by_contact.get(contact.hektor_contact_id, set()))
        duplicate = best_duplicate_by_contact.get(contact.hektor_contact_id)
        directory = negotiator_map.get(contact.hektor_negociateur_id or "", {})
        relations = relation_rows.get(contact.hektor_contact_id, [])
        active_relation_count = sum(1 for row in relations if int(row.get("is_active_annonce") or 0))
        active_search_count = active_search_counts.get(contact.hektor_contact_id, 0)
        eligibility_reasons = []
        if active_relation_count:
            eligibility_reasons.append("active_annonce_relation")
        if active_search_count:
            eligibility_reasons.append("active_search")
        payload = {
            "hektor_contact_id": contact.hektor_contact_id,
            "hektor_agence_id": contact.hektor_agence_id,
            "hektor_negociateur_id": contact.hektor_negociateur_id,
            "negociateur_email": directory.get("negociateur_email"),
            "commercial_nom": directory.get("commercial_nom"),
            "agence_nom": directory.get("agence_nom") or agency_map.get(contact.hektor_agence_id or ""),
            "civilite": contact.civilite,
            "nom": contact.nom,
            "prenom": contact.prenom,
            "display_name": contact.display_name,
            "hektor_target_id": contact.hektor_target_id,  # L4-c ④
            "hektor_couple_contact_id": contact.hektor_couple_contact_id,
            "couple_role": contact.couple_role,
            "archive": contact.archive,
            "date_enregistrement": contact.date_enregistrement,
            "date_maj": contact.date_maj,
            "email": contact.email,
            "phone_primary": contact.phone_primary,
            "phone_secondary": contact.fixe if contact.portable and contact.fixe else None,
            "ville": contact.ville,
            "code_postal": contact.code_postal,
            "adresse": contact.adresse,
            "typologies_json": contact.typologie_json or "[]",
            "relation_roles_json": json_array(roles),
            "linked_annonce_count": len({row["hektor_annonce_id"] for row in relations}),
            "active_search_count": active_search_count,
            "total_search_count": total_search_counts.get(contact.hektor_contact_id, 0),
            "has_contact_detail": int(contact.hektor_contact_id in contact_detail_state),
            "contact_detail_synced_at": contact_detail_state.get(contact.hektor_contact_id),
            "supabase_sync_eligible": int(bool(eligibility_reasons)),
            "eligibility_reasons_json": json_array(eligibility_reasons),
            "duplicate_group_count": duplicate_member_counts.get(contact.hektor_contact_id, 0),
            "duplicate_max_severity": duplicate.get("severity") if duplicate else None,
            "duplicate_primary_candidate_id": duplicate.get("primary_candidate_hektor_contact_id") if duplicate else None,
            "completeness_score": contact.completeness_score,
        }
        payload["source_hash"] = stable_hash({key: value for key, value in payload.items() if key != "source_hash"})
        rows.append(payload)
    return rows


def replace_table_rows(conn: sqlite3.Connection, table: str, rows: list[dict[str, Any]], refreshed_at: str) -> None:
    conn.execute(f"DELETE FROM {table}")
    if not rows:
        conn.commit()
        return
    keys = list(rows[0].keys())
    if "refreshed_at" not in keys:
        keys.append("refreshed_at")
    placeholders = ",".join("?" for _ in keys)
    columns = ",".join(keys)
    values = []
    for row in rows:
        values.append(tuple(row.get(key, refreshed_at if key == "refreshed_at" else None) for key in keys))
    conn.executemany(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)
    conn.commit()


# C.2b (30/08) -- LE REGISTRE PORTE AUSSI LE NUMERO DE CONTACT DE L'APP.
#
# La relecture d'identite du 24/08 se terminait par cinq recommandations. Quatre ont
# ete appliquees le lendemain ; la cinquieme -- « et le registre : lui ajouter
# app_contact_id, puis relacher son NOT NULL » -- est tombee entre deux commits.
#
# NOT NULL est parti parce qu'une recherche nee dans l'app n'a PAS de numero Hektor.
# La base existante a ete migree par migrer_registre_recherche_2026-08-30.py ; ce DDL
# ne sert qu'aux bases neuves, mais il doit dire la meme chose qu'elles.
#
# LES DEUX INDEX SONT PARTIELS : un couple ne protege rien quand sa colonne est vide.
SEARCH_REGISTRY_DDL = """
CREATE TABLE IF NOT EXISTS app_search_registry (
    app_search_id      INTEGER PRIMARY KEY,
    hektor_contact_id  TEXT,
    app_contact_id     INTEGER,
    search_index       INTEGER NOT NULL,
    contact_search_key TEXT,
    first_seen_at      TEXT,
    last_seen_at       TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_search_registry_pair
    ON app_search_registry(hektor_contact_id, search_index)
    WHERE hektor_contact_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_search_registry_pair_app
    ON app_search_registry(app_contact_id, search_index)
    WHERE app_contact_id IS NOT NULL;
"""


def assign_search_ids(
    conn: sqlite3.Connection,
    search_rows: list[dict[str, Any]],
    refreshed_at: str,
) -> dict[str, int]:
    """Redonne a chaque recherche le numero qu'elle portait deja, ou lui en attribue un.

    Le nom d'une recherche (`contact_search_key`) est le hache de son CONTENU : il change
    des que le contenu change, et la ligne est alors detruite puis recreee -- emportant
    tout ce qui pendait dessous. Le numero, lui, est attache a la PAIRE (contact, rang),
    qui ne bouge pas : Hektor n'efface jamais une recherche, il pose une date d'archivage,
    donc le rang ne glisse pas.

    Le registre est une table A PART, jamais videe. La couche des recherches, elle, est
    reconstruite entierement a chaque run complet : un numero range la-dedans ne
    survivrait pas.

    EN DOUBLURE (21/08/2026) : ce numero n'est encore la cle de rien. On l'observe.
    """
    conn.executescript(SEARCH_REGISTRY_DDL)
    if not search_rows:
        return {"reprises": 0, "attribues": 0}

    # ═══════════════════════════════════════════════════════════════════════
    # L4-c ① 22/09/2026 — LE REGISTRE SE RETROUVE SOUS L'UN OU L'AUTRE NUMERO
    # ═══════════════════════════════════════════════════════════════════════
    # POURQUOI C'EST NECESSAIRE. Ce registre s'ancre sur la paire
    # (numero de contact, rang). Le jour ou l'identite du contact devient
    # `app_contact_id`, les lignes arrivent avec l'autre numero : la recherche
    # n'est plus reconnue, elle recoit un numero neuf et un nom neuf fige --
    # 11 368 cles changent d'un coup, et tout ce qui pend dessous devient
    # orphelin, SANS UN BRUIT (aucune cle etrangere ne protege ces tables).
    # C'est le piege que l'audit du 22/09 a sorti.
    #
    # ⛔ POURQUOI ON NE POUVAIT PAS LE FAIRE AVANT CE MATIN. Les deux series de
    #   numeros se RECOUVRAIENT : 194 683 numeros existaient dans les deux en
    #   designant des personnes DIFFERENTES. Indexer les deux dans le meme
    #   dictionnaire aurait rendu la ligne d'un AUTRE contact -- 194 683 fois,
    #   sans erreur et sans trace.
    #   Depuis le decalage (L4-c ⓪, 22/09), les plages sont DISJOINTES :
    #       < 10 000 000  numero de Hektor
    #       >= 10 000 000 numero de l'app
    #   Un numero dit d'ou il vient, donc les deux cles peuvent cohabiter.
    ids = sorted({str(row["hektor_contact_id"]) for row in search_rows})
    known: dict[tuple[str, int], tuple[int, str | None]] = {}
    for start in range(0, len(ids), 400):
        chunk = ids[start:start + 400]
        placeholders = ",".join("?" for _ in chunk)
        for cid, aid, idx, sid, key in conn.execute(
            f"SELECT hektor_contact_id, app_contact_id, search_index, app_search_id, contact_search_key "
            f"FROM app_search_registry "
            f"WHERE hektor_contact_id IN ({placeholders}) OR app_contact_id IN ({placeholders})",
            tuple(chunk) + tuple(chunk),
        ):
            valeur = (int(sid), key)
            if cid is not None:
                known[(str(cid), int(idx))] = valeur
            if aid is not None:
                known[(str(aid), int(idx))] = valeur

    # L4-b 21/09/2026 -- LE COULOIR DU SERVEUR. Le prochain numero se prend parmi
    # ceux que le SERVEUR a fabriques, jamais parmi ceux de l'app (>= 1 000 000).
    # Sans ce filtre, la premiere recherche nee dans l'app ferait sauter la serie
    # du serveur dans la plage de l'app, et deux recherches differentes
    # finiraient par porter le meme numero -- sans que rien ne le signale.
    next_id = int(conn.execute(
        "SELECT COALESCE(MAX(app_search_id), 0) FROM app_search_registry "
        "WHERE app_search_id < 1000000").fetchone()[0]) + 1
    nouveaux: list[tuple[Any, ...]] = []
    noms_a_poser: list[tuple[Any, ...]] = []
    reprises = 0
    noms_figes = 0
    for row in search_rows:
        pair = (str(row["hektor_contact_id"]), int(row["search_index"]))
        connu = known.get(pair)
        if connu is None:
            sid = next_id
            next_id += 1
            # Recherche jamais vue : on garde le nom qui vient d'etre calcule, et on le FIGE.
            known[pair] = (sid, str(row["contact_search_key"]))
            nouveaux.append((sid, pair[0], pair[1], str(row["contact_search_key"]), refreshed_at, refreshed_at))
        else:
            sid, nom_fige = connu
            reprises += 1
            if nom_fige:
                # LE GESTE : on rend a la recherche le nom qu'elle portait deja, au lieu du
                # nom qui vient d'etre recalcule a partir de son contenu. Le contenu peut
                # changer autant qu'il veut -- la ligne garde son identite, et l'empreinte
                # (stable_payload_hash) fait enfin son travail : mise a jour au lieu de
                # destruction/recreation.
                if nom_fige != row["contact_search_key"]:
                    noms_figes += 1
                row["contact_search_key"] = nom_fige
            else:
                # Paire connue mais sans nom enregistre (registre pose avant ce correctif) :
                # on adopte le nom courant comme nom definitif.
                known[pair] = (sid, str(row["contact_search_key"]))
                noms_a_poser.append((str(row["contact_search_key"]), pair[0], pair[1]))
        row["app_search_id"] = sid

    if nouveaux:
        conn.executemany(
            "INSERT INTO app_search_registry(app_search_id, hektor_contact_id, search_index, "
            "contact_search_key, first_seen_at, last_seen_at) VALUES (?, ?, ?, ?, ?, ?)",
            nouveaux,
        )
    # L4-c ① 22/09 : les mises a jour visent LES DEUX colonnes, pour la meme
    # raison que la lecture plus haut -- la ligne peut arriver sous l'un ou
    # l'autre numero. Sans ca, une ligne retrouvee par la doublure n'aurait
    # jamais ete marquee « vue », et le menage l'aurait crue disparue.
    # Sans danger depuis que les plages sont disjointes (L4-c ⓪).
    if noms_a_poser:
        conn.executemany(
            "UPDATE app_search_registry SET contact_search_key = ? "
            "WHERE search_index = ? AND (hektor_contact_id = ? OR app_contact_id = ?)",
            [(nom, rang, cid, cid) for nom, cid, rang in noms_a_poser],
        )
    conn.executemany(
        "UPDATE app_search_registry SET last_seen_at = ? "
        "WHERE search_index = ? AND (hektor_contact_id = ? OR app_contact_id = ?)",
        [(refreshed_at, pair[1], pair[0], pair[0]) for pair in known],
    )
    return {
        "reprises": reprises,
        "attribues": len(nouveaux),
        "noms_rendus": noms_figes,
        "noms_adoptes": len(noms_a_poser),
    }


def insert_table_rows(conn: sqlite3.Connection, table: str, rows: list[dict[str, Any]], refreshed_at: str) -> None:
    if not rows:
        return
    keys = list(rows[0].keys())
    if "refreshed_at" not in keys:
        keys.append("refreshed_at")
    placeholders = ",".join("?" for _ in keys)
    columns = ",".join(keys)
    values = [
        tuple(refreshed_at if key == "refreshed_at" else row.get(key) for key in keys)
        for row in rows
    ]
    conn.executemany(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)


def load_existing_duplicate_fields(
    conn: sqlite3.Connection,
    contact_ids: Iterable[str],
) -> dict[str, dict[str, Any]]:
    ids = normalize_contact_ids(contact_ids)
    if not ids:
        return {}
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"""
        SELECT hektor_contact_id, duplicate_group_count, duplicate_max_severity, duplicate_primary_candidate_id
        FROM app_contact_current
        WHERE CAST(hektor_contact_id AS TEXT) IN ({placeholders})
        """,
        ids,
    ).fetchall()
    return {
        clean_text(row["hektor_contact_id"]): {
            "duplicate_group_count": row["duplicate_group_count"],
            "duplicate_max_severity": row["duplicate_max_severity"],
            "duplicate_primary_candidate_id": row["duplicate_primary_candidate_id"],
        }
        for row in rows
    }


def load_existing_relation_rows(
    conn: sqlite3.Connection,
    contact_ids: Iterable[str],
) -> list[dict[str, Any]]:
    ids = normalize_contact_ids(contact_ids)
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"""
        SELECT *
        FROM app_contact_relation_current
        WHERE CAST(hektor_contact_id AS TEXT) IN ({placeholders})
        """,
        ids,
    ).fetchall()
    return [dict(row) for row in rows]


def merge_relation_rows(
    current_rows: list[dict[str, Any]],
    previous_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_key = {clean_text(row.get("relation_key")): row for row in previous_rows if clean_text(row.get("relation_key"))}
    for row in current_rows:
        key = clean_text(row.get("relation_key"))
        if key:
            by_key[key] = row
    return list(by_key.values())


def preserve_duplicate_fields(
    contact_rows: list[dict[str, Any]],
    previous_duplicate_fields: dict[str, dict[str, Any]],
) -> None:
    for row in contact_rows:
        previous = previous_duplicate_fields.get(clean_text(row.get("hektor_contact_id")))
        if not previous:
            continue
        row.update(previous)
        row["source_hash"] = stable_hash({key: value for key, value in row.items() if key != "source_hash"})


def write_reports(report_dir: Path, summary: dict[str, Any], group_rows: list[dict[str, Any]], member_rows: list[dict[str, Any]]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "contact_audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    top_groups = sorted(
        group_rows,
        key=lambda row: (
            -SEVERITY_RANK[str(row["severity"])],
            -int(row["suspected_mass_archive_error"]),
            -int(row["member_count"]),
            str(row["rule_code"]),
        ),
    )[:5000]
    with (report_dir / "contact_duplicate_groups_top.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(top_groups[0].keys()) if top_groups else ["duplicate_group_id"])
        writer.writeheader()
        writer.writerows(top_groups)

    group_ids = {row["duplicate_group_id"] for row in top_groups[:1000]}
    top_members = [row for row in member_rows if row["duplicate_group_id"] in group_ids]
    with (report_dir / "contact_duplicate_members_top.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(top_members[0].keys()) if top_members else ["duplicate_group_id", "hektor_contact_id"])
        writer.writeheader()
        writer.writerows(top_members)


def refresh_contact_slice(
    *,
    contact_ids: Iterable[str],
    hektor_db: Path = DEFAULT_HEKTOR_DB,
    phase2_db: Path = DEFAULT_PHASE2_DB,
) -> dict[str, Any]:
    ids = normalize_contact_ids(contact_ids)
    if not ids:
        raise ValueError("Au moins un ID contact est requis")

    started_at = now_utc_iso()
    hektor_conn = connect(hektor_db)
    phase2_conn = connect(phase2_db)
    try:
        init_contacts_schema(phase2_conn)
        # L4-b (②) : la correspondance D'ABORD -- tout ce qui suit s'en sert.
        charger_identites_app(phase2_conn)
        # Deux listes, et il faut les deux. Le MIROIR ne connait que les numeros
        # de Hektor ; NOS tables rangent sous l'identite. Un rafraichissement
        # peut arriver avec l'un ou l'autre : le worker envoie le numero de
        # Hektor, un ecran de l'app enverrait l'identite.
        ids_miroir = [numero_hektor_pour_le_miroir(contact_id) for contact_id in ids]
        ids_chez_nous = [identite_app(contact_id) for contact_id in ids]
        contacts = load_contacts(hektor_conn, contact_ids=ids_miroir)
        valid_contact_ids = {contact.hektor_contact_id for contact in contacts}
        relation_rows, roles_by_contact = load_relations(hektor_conn, phase2_conn, contact_ids=ids_miroir)
        search_rows, total_search_counts, active_search_counts = load_contact_searches(hektor_conn, contact_ids=ids_miroir)
        contact_detail_state = load_contact_detail_state(hektor_conn, contact_ids=ids_miroir)

        raw_relation_total = sum(len(rows) for rows in relation_rows.values())
        relation_rows = {
            contact_id: rows
            for contact_id, rows in relation_rows.items()
            if contact_id in valid_contact_ids
        }
        raw_search_total = len(search_rows)
        search_rows = [row for row in search_rows if row["hektor_contact_id"] in valid_contact_ids]
        roles_by_contact = {
            contact_id: roles
            for contact_id, roles in roles_by_contact.items()
            if contact_id in valid_contact_ids
        }

        negotiator_map, agency_map = load_directory_maps(hektor_conn)
        previous_duplicate_fields = load_existing_duplicate_fields(phase2_conn, ids_chez_nous)
        previous_relation_rows = load_existing_relation_rows(phase2_conn, ids_chez_nous)
        contact_rows = build_contact_rows(
            contacts,
            relation_rows,
            roles_by_contact,
            total_search_counts,
            active_search_counts,
            Counter(),
            {},
            negotiator_map,
            agency_map,
            contact_detail_state,
        )
        preserve_duplicate_fields(contact_rows, previous_duplicate_fields)
        current_relation_rows = [row for rows in relation_rows.values() for row in rows]
        relation_flat_rows = merge_relation_rows(
            current_relation_rows,
            previous_relation_rows,
        )
        refreshed_at = now_utc_iso()

        # L4-b (②) : on vide sous LES DEUX numeros. Sous l'identite parce que
        # c'est la qu'on repose ; sous le numero de Hektor parce qu'une fiche y
        # a peut-etre ete rangee avant ce correctif -- c'est exactement la
        # seconde fiche de l'essai du 21/09, et si on ne l'enleve pas, elle
        # survit a sa propre correction.
        for contact_id in dict.fromkeys([*ids, *ids_miroir, *ids_chez_nous]):
            phase2_conn.execute("DELETE FROM app_contact_current WHERE hektor_contact_id = ?", (contact_id,))
            phase2_conn.execute("DELETE FROM app_contact_relation_current WHERE hektor_contact_id = ?", (contact_id,))
            phase2_conn.execute("DELETE FROM app_contact_search_current WHERE hektor_contact_id = ?", (contact_id,))

        assign_search_ids(phase2_conn, search_rows, refreshed_at)
        insert_table_rows(phase2_conn, "app_contact_current", contact_rows, refreshed_at)
        insert_table_rows(phase2_conn, "app_contact_relation_current", relation_flat_rows, refreshed_at)
        insert_table_rows(phase2_conn, "app_contact_search_current", search_rows, refreshed_at)
        phase2_conn.commit()

        missing_contact_ids = [contact_id for contact_id in ids if contact_id not in valid_contact_ids]
        return {
            "started_at": started_at,
            "finished_at": refreshed_at,
            "mode": "contact_slice",
            "requested_contact_ids": ids,
            "contacts_total": len(contact_rows),
            "missing_contact_ids": missing_contact_ids,
            "relations_total": len(relation_flat_rows),
            "previous_relations_preserved": max(0, len(relation_flat_rows) - len(current_relation_rows)),
            "relations_skipped_missing_contact": raw_relation_total - len(current_relation_rows),
            "searches_total": len(search_rows),
            "active_searches_total": sum(int(row["is_active"]) for row in search_rows),
            "searches_skipped_missing_contact": raw_search_total - len(search_rows),
            "supabase_sync_eligible_contacts": sum(int(row["supabase_sync_eligible"]) for row in contact_rows),
            "duplicate_fields_preserved": sum(1 for row in contact_rows if row["hektor_contact_id"] in previous_duplicate_fields),
        }
    finally:
        hektor_conn.close()
        phase2_conn.close()


def verifier_substitution(conn: sqlite3.Connection, relation_rows: dict) -> dict[str, Any]:
    """C.9-f — combien d'identifiants de liens ont change ? Ne leve JAMAIS.

    Attendu : ZERO. Le carnet rend a chaque lien deja connu l'identifiant qu'il
    avait ; seuls les liens reellement neufs en recoivent un. Quelques
    disparitions sont normales (un lien retire chez Hektor) -- des centaines, non.
    """
    try:
        anciennes = {r[0] for r in conn.execute(
            "SELECT relation_key FROM app_contact_relation_current")}
    except sqlite3.Error as exc:
        return {"statut": "non_mesure", "erreur": type(exc).__name__, "recommence": False}
    if not anciennes:
        return {"statut": "premier_build", "recommence": False}
    nouvelles = {row["relation_key"] for rows in relation_rows.values() for row in rows}
    disparues = len(anciennes - nouvelles)
    recommence = disparues > SEUIL_CLES_CHANGEES
    bilan = {"statut": "recommence_sans_substitution" if recommence else "ok",
             "identifiants_disparus": disparues, "identifiants_neufs": len(nouvelles - anciennes),
             "seuil": SEUIL_CLES_CHANGEES, "recommence": recommence}
    if recommence:
        print(f"[numero de bien dans la cle] ALERTE : {disparues} identifiants de liens "
              f"disparaitraient (seuil {SEUIL_CLES_CHANGEES}) -- on RECOMMENCE avec le "
              f"numero Hektor, comme avant. Rien n'est ecrit avec la substitution.")
    else:
        print(f"[numero de bien dans la cle] {disparues} identifiant(s) disparu(s), "
              f"{len(nouvelles - anciennes)} neuf(s) -- sous le seuil")
    return bilan


def build_contacts_layer(
    *,
    hektor_db: Path = DEFAULT_HEKTOR_DB,
    phase2_db: Path = DEFAULT_PHASE2_DB,
    report_dir: Path = DEFAULT_REPORT_DIR,
    limit: int | None = None,
    write_reports_enabled: bool = True,
) -> dict[str, Any]:
    started_at = now_utc_iso()
    hektor_conn = connect(hektor_db)
    phase2_conn = connect(phase2_db)
    try:
        init_contacts_schema(phase2_conn)
        # L4-b (②) : la correspondance D'ABORD. Sans elle, un contact ne dans
        # l'app serait repose sous le numero de Hektor -- une seconde fiche.
        charger_identites_app(phase2_conn)
        contacts = load_contacts(hektor_conn, limit)
        relation_rows, roles_by_contact = load_relations(hektor_conn, phase2_conn)
        # ── C.9-f : LE GARDE-FOU DE SORTIE ──────────────────────────────────
        # Le carnet doit rendre les identifiants INCHANGES. S'il en manque trop,
        # c'est que la reprise n'a pas fonctionne -- et laisser passer ferait
        # supprimer puis reposer tout le parc chez Supabase (22/08). On
        # RECOMMENCE alors sans substituer : le comportement d'avant, a l'identique.
        substitution = verifier_substitution(phase2_conn, relation_rows)
        if substitution.get("recommence"):
            relation_rows, roles_by_contact = load_relations(
                hektor_conn, phase2_conn, substituer=False)
        search_rows, total_search_counts, active_search_counts = load_contact_searches(hektor_conn)
        contact_detail_state = load_contact_detail_state(hektor_conn)
        valid_contact_ids = {contact.hektor_contact_id for contact in contacts}
        raw_relation_total = sum(len(rows) for rows in relation_rows.values())
        relation_rows = {
            contact_id: rows
            for contact_id, rows in relation_rows.items()
            if contact_id in valid_contact_ids
        }
        raw_search_total = len(search_rows)
        search_rows = [row for row in search_rows if row["hektor_contact_id"] in valid_contact_ids]
        roles_by_contact = {
            contact_id: roles
            for contact_id, roles in roles_by_contact.items()
            if contact_id in valid_contact_ids
        }
        skipped_missing_contact_relations = raw_relation_total - sum(len(rows) for rows in relation_rows.values())
        skipped_missing_contact_searches = raw_search_total - len(search_rows)
        negotiator_map, agency_map = load_directory_maps(hektor_conn)
        linked_counts = {contact_id: len({row["hektor_annonce_id"] for row in rows}) for contact_id, rows in relation_rows.items()}
        group_rows, member_rows, best_duplicate_by_contact = build_duplicate_records(contacts, linked_counts)
        duplicate_member_counts = Counter(row["hektor_contact_id"] for row in member_rows)
        contact_rows = build_contact_rows(
            contacts,
            relation_rows,
            roles_by_contact,
            total_search_counts,
            active_search_counts,
            duplicate_member_counts,
            best_duplicate_by_contact,
            negotiator_map,
            agency_map,
            contact_detail_state,
        )
        relation_flat_rows = [row for rows in relation_rows.values() for row in rows]
        refreshed_at = now_utc_iso()

        assign_search_ids(phase2_conn, search_rows, refreshed_at)
        replace_table_rows(phase2_conn, "app_contact_current", contact_rows, refreshed_at)
        replace_table_rows(phase2_conn, "app_contact_relation_current", relation_flat_rows, refreshed_at)
        # C.9-d : le carnet des liens, en doublure. Ne leve jamais.
        carnet_des_liens = enregistrer_registre_relations(
            phase2_conn, [row["relation_key"] for row in relation_flat_rows], refreshed_at,
            complet=not limit)
        replace_table_rows(phase2_conn, "app_contact_search_current", search_rows, refreshed_at)
        replace_table_rows(phase2_conn, "app_contact_duplicate_group_current", group_rows, refreshed_at)
        replace_table_rows(phase2_conn, "app_contact_duplicate_member_current", member_rows, refreshed_at)

        severity_counts = Counter(row["severity"] for row in group_rows)
        rule_counts = Counter(row["rule_code"] for row in group_rows)
        archive_pattern_counts = Counter(row["archive_pattern"] for row in group_rows)
        summary = {
            "started_at": started_at,
            "finished_at": refreshed_at,
            "contacts_total": len(contacts),
            "contacts_active": sum(1 for contact in contacts if not contact.archive),
            "contacts_archived": sum(1 for contact in contacts if contact.archive),
            "relations_total": len(relation_flat_rows),
            "transaction_relations_total": sum(1 for row in relation_flat_rows if row.get("transaction_id")),
            "contacts_with_relation": len(relation_rows),
            "relations_skipped_missing_contact": skipped_missing_contact_relations,
            "relation_registry": carnet_des_liens,
            "substitution_numero_bien": substitution,
            "searches_total": len(search_rows),
            "active_searches_total": sum(int(row["is_active"]) for row in search_rows),
            "contacts_with_active_search": sum(1 for count in active_search_counts.values() if count),
            "contacts_with_detail": sum(1 for contact in contacts if contact.hektor_contact_id in contact_detail_state),
            "searches_skipped_missing_contact": skipped_missing_contact_searches,
            "supabase_sync_eligible_contacts": sum(int(row["supabase_sync_eligible"]) for row in contact_rows),
            "duplicate_group_total": len(group_rows),
            "duplicate_member_total": len(set(row["hektor_contact_id"] for row in member_rows)),
            "high_or_critical_group_total": sum(1 for row in group_rows if row["severity"] in {"high", "critical"}),
            "suspected_mass_archive_error_total": sum(int(row["suspected_mass_archive_error"]) for row in group_rows),
            "duplicate_rule_counts": dict(sorted(rule_counts.items())),
            "duplicate_severity_counts": dict(sorted(severity_counts.items())),
            "duplicate_archive_pattern_counts": dict(sorted(archive_pattern_counts.items())),
            "report_dir": str(report_dir),
        }
        phase2_conn.execute(
            """
            INSERT INTO app_contact_audit_run (
                started_at, finished_at, contacts_total, contacts_active, contacts_archived,
                duplicate_group_total, duplicate_member_total, high_or_critical_group_total,
                suspected_mass_archive_error_total, report_summary_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                started_at,
                refreshed_at,
                summary["contacts_total"],
                summary["contacts_active"],
                summary["contacts_archived"],
                summary["duplicate_group_total"],
                summary["duplicate_member_total"],
                summary["high_or_critical_group_total"],
                summary["suspected_mass_archive_error_total"],
                json.dumps(summary, ensure_ascii=False, separators=(",", ":")),
            ),
        )
        phase2_conn.commit()
    finally:
        hektor_conn.close()
        phase2_conn.close()

    if write_reports_enabled:
        write_reports(report_dir, summary, group_rows, member_rows)
    return summary


# ── SECONDE PASSE, 24/09/2026 : UN CONTACT NEUF NE DOIT PAS PASSER UNE NUIT ──
# ── SOUS SON NUMERO HEKTOR ──────────────────────────────────────────────────
# Le run fait : build (17:47) -> registre (17:51) -> push. Le registre decouvre
# les contacts neufs EN LISANT la couche que le build vient d'ecrire : un contact
# cree chez Hektor dans la journee est donc ecrit sous son numero Hektor, recoit
# son identite juste APRES, part vers Supabase sous l'ancien numero, et n'est
# traduit qu'au run suivant. Pendant ce jour, tout ce que l'app lui accroche
# (rapprochements, recherches...) porte un numero qui va disparaitre -- mesure du
# 24/09 : 67 rapprochements des 23 contacts L4-c-bis encore sous l'ancien numero.
# Depuis la bascule du 23/09 seulement (avant, identite = numero Hektor).
# ➡ Le run relance le build APRES le registre, AVANT le push, avec cette option :
#   s'il n'y a rien a traduire il s'arrete sans rien ecrire ; sinon il refait
#   exactement ce que le build du lendemain aurait fait -- en avance.
def contacts_a_traduire(phase2_db: Path) -> int:
    """Contacts de la couche encore sous leur numero Hektor alors que le registre
    leur a donne une identite (meme regle que registre_couche_desaccord, sans le
    delai de 36 h). Lecture seule."""
    conn = sqlite3.connect(f"file:{Path(phase2_db).as_posix()}?mode=ro", uri=True, timeout=30)
    try:
        return conn.execute(
            """
            SELECT COUNT(*)
            FROM app_contact_current c
            JOIN app_contact r ON r.hektor_target_id = c.hektor_contact_id
            WHERE CAST(c.hektor_contact_id AS INTEGER) < 10000000
              AND CAST(r.hektor_contact_id AS INTEGER) >= 10000000
            """
        ).fetchone()[0]
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Construit la couche Contacts Phase2 et audite les doublons sans suppression.")
    parser.add_argument("--hektor-db", type=Path, default=DEFAULT_HEKTOR_DB)
    parser.add_argument("--phase2-db", type=Path, default=DEFAULT_PHASE2_DB)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--limit", type=int, default=0, help="Limite de contacts pour test local. 0 = tous.")
    parser.add_argument(
        "--contact-id",
        action="append",
        default=[],
        help="Reconstruit uniquement un ou plusieurs contacts Hektor (valeurs separees par virgule acceptees).",
    )
    parser.add_argument("--no-reports", action="store_true", help="Ne genere pas les CSV/JSON d'audit.")
    parser.add_argument(
        "--seulement-si-contacts-a-traduire",
        action="store_true",
        help="Seconde passe du run : ne reconstruit que si des contacts neufs attendent leur identite.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    contact_ids = normalize_contact_ids(args.contact_id)
    if args.seulement_si_contacts_a_traduire:
        a_traduire = contacts_a_traduire(args.phase2_db)
        if a_traduire == 0:
            print("[seconde passe] 0 contact a traduire -- rien a refaire, rien n'est ecrit")
            return 0
        print(f"[seconde passe] {a_traduire} contact(s) neuf(s) attendent leur identite -- on reconstruit")
    if contact_ids:
        summary = refresh_contact_slice(
            contact_ids=contact_ids,
            hektor_db=args.hektor_db,
            phase2_db=args.phase2_db,
        )
    else:
        summary = build_contacts_layer(
            hektor_db=args.hektor_db,
            phase2_db=args.phase2_db,
            report_dir=args.report_dir,
            limit=args.limit or None,
            write_reports_enabled=not args.no_reports,
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
