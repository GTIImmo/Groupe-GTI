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
    charger_corps_suspects,
    charger_mandants_du_registre_des_liens,
    compute_mandat_version_score,
    normalize_embedded_avenants,
    texte_des_mandants,
)
from phase2.sync.push_upgrade_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES,
    SupabaseRestClient,
    load_env_files,
)

import os  # noqa: E402

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

    # ══════════════════════════════════════════════════════════════════════════
    # L'ADOPTION -- ET SANS ELLE, LE PUSH S'ARRETERAIT
    #
    # Le worker ecrit un mandat NE DANS L'APP directement chez Supabase, avec un
    # numero de la plage haute (>= 1 000 000, distribue par app_mandat_id_app_seq).
    # Le miroir ne le connait pas encore. Au run suivant, Hektor le redescend :
    # ce script verrait un couple INCONNU, lui donnerait un numero de la serie
    # LOCALE, et le push tenterait d'inserer une deuxieme ligne pour le meme
    # couple -> violation de app_mandat_couple_unique.
    #
    # ⚠ ET LE DEGAT NE SERAIT PAS LE CONFLIT, CE SERAIT L'ARRET. Les 01 et
    #   02/09/2026, deux nuits de suite, le push du ledger d'affaires a heurte un
    #   index unique et LE RUN S'EST ARRETE LA -- tout ce qui suivait n'a pas
    #   tourne, et l'app est restee dix-huit heures en arriere sans que rien ne
    #   le dise.
    #
    # ON ADOPTE DONC : si la doublure porte deja ce couple, on reprend SON numero
    # au lieu d'en fabriquer un. C'est la regle du projet -- « un numero ne se
    # perd jamais », et c'est le serveur qui s'aligne, pas le cloud.
    # ══════════════════════════════════════════════════════════════════════════
    adoptes: dict[tuple[str, str], int] = {}
    try:
        for r in con.execute(
            "SELECT app_mandat_id, hektor_annonce_id, numero_mandat FROM app_mandat__sb"
            " WHERE app_mandat_id >= ?", (PLAGE_RESERVEE_APP,)
        ):
            cle_sb = (str(r["hektor_annonce_id"] or "").strip(),
                      str(r["numero_mandat"] or "").strip())
            if cle_sb[0] and cle_sb[1] and cle_sb not in connus:
                adoptes[cle_sb] = int(r["app_mandat_id"])
    except sqlite3.OperationalError:
        # La doublure n'a jamais ete descendue. On ne devine pas -- et tant que
        # rien n'ecrit depuis l'app, il n'y a rien a adopter.
        pass
    adoptes_au_depart = len(adoptes)

    # Notre numero d'annonce, pour que la ligne porte NOTRE identite et pas
    # seulement celle de Hektor.
    dossiers = {}
    for r in con.execute(
        "SELECT id, hektor_annonce_id FROM app_dossier WHERE hektor_annonce_id IS NOT NULL"
    ):
        dossiers[str(r["hektor_annonce_id"])] = r["id"]

    # ═════════════════════════════════════════════════════════════════════════
    # LES MANDANTS : NOTRE REGISTRE DES LIENS EN RECOURS.          06/10/2026
    # ═════════════════════════════════════════════════════════════════════════
    # LE DEFAUT, MESURE LE 06/10. Le registre des ANNONCES a un recours que
    # celui des mandats n'a pas -- et c'est TOUTE la difference :
    #
    #   view_generale   COALESCE( m.mandants_texte , det.proprietaires_resume )
    #                                                ^^^ un deuxieme recours
    #   ici (avant)     courante["mandants"]  or  le plat du MEME bloc
    #                   -> deux recours qui puisent au MEME endroit. Aucun ailleurs.
    #
    # Le 29/09, cette table a copie la SOURCE du registre -- et son commit disait
    # juste : « la table doit lire la MEME CHOSE ». Mais la VALEUR du registre ne
    # vient pas de la source seule : elle passe par le COALESCE de la vue. On avait
    # copie la source, pas la recette. D'ou 255 lignes plus pauvres que la vue.
    #
    # CE QUE LE BLOC « mandats » DE HEKTOR DONNE, au-dela du n 18339 (son
    # referentiel est gele au 30-01-2026, ses trois routes s'arretent ensemble) :
    #     457 lignes  un corps EMPRUNTE a un autre bien (montant ET mandants)
    #     258 lignes  de VENTE, le champ est VIDE -- presque toutes des SOCIETES
    #                 (« SCI JCL », « SCAM », « MAISON EN FRANCE »)
    #
    # LA REGLE, ET ELLE DISTINGUE DEUX CHOSES QUI NE SE RESSEMBLENT PAS :
    #   ① corps SUSPECT  -> on remplace, QUELLE QUE SOIT LA NATURE.
    #        Un corps emprunte est FAUX, pas incomplet : le restreindre aux ventes
    #        laisserait une ligne fausse pour rien (mesure : 456 VENTE + 1 INCONNUE).
    #   ② champ VIDE et nature = VENTE  -> on comble.
    #   ③ champ VIDE et nature != VENTE -> ON NE TOUCHE A RIEN.
    #        Arbitrage de Frederic du 06/10, qui prolonge sa decision du 26/08 :
    #        les 2 073 lignes de LOCATION / nature inconnue restent ECARTEES.
    #        « il faut pas les rajouter, les garder exclus ».
    #   ④ sinon -> le texte de Hektor, inchange (24 022 lignes).
    #
    # ⚠ ET ON NE TRIE PAS les noms par mandat. Tentation ecartee le 06/10 apres
    #   mesure : une personne peut etre mandante de DEUX mandats du meme bien
    #   (10 cas sur 39 -- elle a renouvele), donc « ecarter ce que l'autre mandat
    #   nomme » est faux EN PRINCIPE. Et plusieurs mandants n'est pas une anomalie :
    #   c'est le cas de 47,5 % du registre (un couple, une fratrie, une indivision).
    #
    # ⚠ L'ORDRE DANS LE RUN COMPTE : app_relation doit etre construit AVANT cette
    #   etape, sinon on lit les liens de la VEILLE. Voir run_full_pipeline.ps1.
    #
    # ⭐ IMPORTEES, JAMAIS RECOPIEES -- meme regle que les deux formules du haut.
    #   UNE SEULE lecture pour tout le lot (132 697 liens, 2,66 s mesure), jamais
    #   une requete par mandat.
    mandants_app = charger_mandants_du_registre_des_liens(con)
    corps_suspects = charger_corps_suspects(con)
    mandants_remplaces = mandants_combles = mandants_sans_recours = 0
    sans_recours_exemples: list[tuple[str, str]] = []

    lus = neufs = revus = sans_numero = 0
    vus_ce_run = []

    def _poser(annonce: str, numero: str, versions: list[dict], origine: str,
               repli=None) -> None:
        """Ecrit UNE ligne de registre. `versions` est deja trie, meilleure en tete."""
        nonlocal prochain, neufs, revus
        courante = versions[0] if versions else {}
        avenants = normalize_embedded_avenants(versions) if versions else []
        cle = (annonce, numero)
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
        plat = repli if repli is not None else {}

        def _du_plat(colonne):
            try:
                return plat[colonne]
            except Exception:
                return None

        # LA NATURE EST CALCULEE ICI, et non plus dans la liste des parametres :
        # la regle des mandants en a besoin pour decider. Meme formule, meme ordre
        # d'arguments -- rien ne change pour la colonne `nature` elle-meme.
        nature_ligne = _nature(
            courante.get("type"),
            courante.get("note") or _du_plat("note"),
            offres.get(annonce),
        )

        # ── LES MANDANTS : voir le bloc commente au-dessus de _poser ──
        nonlocal mandants_remplaces, mandants_combles, mandants_sans_recours
        mandants_hektor = _texte(courante.get("mandants")) or _texte(_du_plat("mandants_texte"))
        corps_suspect = (annonce, numero) in corps_suspects
        nos_mandants = texte_des_mandants(mandants_app.get(annonce) or []) or None

        if corps_suspect:
            # ① un corps emprunte est FAUX : on le remplace, quelle que soit la nature.
            #   ⚠ et s'il n'y a RIEN chez nous, on prefere le VIDE au nom d'un autre bien.
            mandants_ligne = nos_mandants
            if nos_mandants:
                mandants_remplaces += 1
            else:
                mandants_sans_recours += 1
                if len(sans_recours_exemples) < 40:
                    sans_recours_exemples.append((annonce, numero))
        elif not mandants_hektor and nature_ligne == "VENTE":
            # ② un vide sur une VENTE : on comble.
            mandants_ligne = nos_mandants
            if nos_mandants:
                mandants_combles += 1
            else:
                mandants_sans_recours += 1
                if len(sans_recours_exemples) < 40:
                    sans_recours_exemples.append((annonce, numero))
        else:
            # ③ et ④ : LOCATION / GESTION / nature inconnue, ou un texte deja bon.
            mandants_ligne = mandants_hektor

        con.execute(
            """
            INSERT INTO app_mandat(app_mandat_id, app_dossier_id, hektor_annonce_id,
                numero_mandat, hektor_mandat_id, famille, type, date_enregistrement,
                date_debut, date_fin, montant, mandants_texte, note, payload_json,
                date_cloture, first_seen_at, last_seen_at, offre_type, nature,
                versions_json, version_count, avenants_json, avenant_count,
                origine, present_in_hektor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(hektor_annonce_id, numero_mandat) DO UPDATE SET
                app_dossier_id=COALESCE(excluded.app_dossier_id, app_mandat.app_dossier_id),
                hektor_mandat_id=excluded.hektor_mandat_id,
                offre_type=excluded.offre_type,
                nature=excluded.nature,
                origine=excluded.origine,
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
                _texte(courante.get("id")) or _texte(_du_plat("hektor_mandat_id")),
                _famille(courante.get("type"), numero),
                _texte(courante.get("type")),
                _texte(courante.get("dateEnregistrement")) or _texte(_du_plat("date_enregistrement")),
                _texte(courante.get("debut")) or _texte(_du_plat("date_debut")),
                _texte(courante.get("fin")) or _texte(_du_plat("date_fin")),
                _montant(courante.get("montant")) or _montant(_du_plat("montant")),
                mandants_ligne,
                _texte(courante.get("note")) or _texte(_du_plat("note")),
                json.dumps(courante, ensure_ascii=True, separators=(",", ":")) if courante else None,
                _texte(courante.get("cloture")) or _texte(_du_plat("date_cloture")),
                vu, vu,
                offres.get(annonce),
                nature_ligne,
                json.dumps([dict(v, montant=_montant(v.get("montant"))) for v in versions],
                           ensure_ascii=True, separators=(",", ":")),
                len(versions),
                json.dumps(avenants, ensure_ascii=True, separators=(",", ":")),
                len(avenants),
                origine,
            ),
        )

    # =========================================================================
    # 1re SOURCE -- LE DETAIL DE L'ANNONCE. C'EST CELLE DU REGISTRE.
    #
    # CORRECTION DU 30/09, ET ELLE ANNULE MON PREMIER JET. J'avais pris
    # `hektor_mandat` pour source. C'est la mauvaise, et l'outil de controle
    # (registre_depuis_app_mandat.py) l'a montre : sur 28 couples la table
    # croyait voir deux VERSIONS d'un mandat la ou il y a deux MANDATS
    # DIFFERENTS qui partagent un numero --
    #     n° 14856   2011 -> 59 000 EUR   ET   2022 -> 160 000 EUR
    #     n° 4028    04/08 -> 106 000     ET   06/08 -> 13 800
    # -- et choisissait « la plus complete » entre deux dossiers etrangers.
    #
    # LA DIFFERENCE TIENT A LA QUESTION POSEE :
    #     le detail       « quels sont les mandats de CE bien, MAINTENANT »
    #     hektor_mandat   accumule tout ce qui est passe
    # Le registre lit le detail (SQL_REGISTER_RAW_BASE : hektor_annonce_detail).
    # La table doit lire la meme chose, sans quoi elle ne peut pas le refaire.
    #
    # Mesure du 30/09 : le detail porte 24 666 couples, hektor_mandat 24 754 ;
    # le detail n'a RIEN que le miroir n'ait (0), et le miroir garde 88 couples
    # que le detail a oublies -- d'ou la 2e source, plus bas.
    # =========================================================================
    par_couple: dict = {}
    for d in con.execute(
        "SELECT hektor_annonce_id, mandats_json FROM hektor.hektor_annonce_detail"
        " WHERE TRIM(COALESCE(mandats_json, '')) NOT IN ('', '[]')"
    ).fetchall():
        annonce = str(d["hektor_annonce_id"] or "").strip()
        if not annonce:
            continue
        try:
            items = json.loads(d["mandats_json"])
        except Exception:
            continue
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            lus += 1
            numero = _texte(item.get("numero"))
            if not numero:
                sans_numero += 1
                continue
            # ⚠ ON NE NETTOIE PAS ICI. Mesure du 30/09 : nettoyer le montant
            #   AVANT compute_mandat_version_score change le classement, donc
            #   LA VERSION RETENUE (annonce 59279 : le registre garde la ligne
            #   close a 0 EUR, la table prenait l'ouverte a 172 500). Ce n'est
            #   pas au nettoyage d'affichage d'arbitrer quel mandat fait foi.
            #   Le score se calcule sur la matiere brute -- exactement comme le
            #   registre. Le « 0 » ne disparait qu'A L'ECRITURE.
            par_couple.setdefault((annonce, numero), []).append(item)

    multi_versions = 0
    for (annonce, numero), versions in par_couple.items():
        versions.sort(key=compute_mandat_version_score, reverse=True)
        if len(versions) > 1:
            multi_versions += 1
        _poser(annonce, numero, versions, "detail")

    # =========================================================================
    # 2e SOURCE -- LE MIROIR, POUR CE QUE LE DETAIL A OUBLIE (88 couples).
    #
    # ON N'ECRASE JAMAIS CE QUE LE DETAIL A POSE. Un mandat que le detail
    # connait est a jour ; celui du miroir peut dater. Le miroir ne sert donc
    # qu'a COMBLER -- la regle « la source la plus riche gagne, la plus pauvre
    # ne fait que combler », deja appliquee a la source `no_mandat`.
    #
    # Et parce qu'on ne prend ici QUE des couples inconnus du detail, le
    # melange de deux mandats homonymes ne peut plus se produire : il n'y a
    # qu'une seule reponse possible par couple.
    # =========================================================================
    depuis_miroir = 0
    groupes: dict = {}
    for m in con.execute(
        "SELECT hektor_mandat_id, hektor_annonce_id, numero, type, date_enregistrement,"
        " date_debut, date_fin, date_cloture, montant, mandants_texte, note, raw_json"
        " FROM hektor.hektor_mandat"
    ).fetchall():
        annonce = str(m["hektor_annonce_id"] or "").strip()
        numero = str(m["numero"] or "").strip()
        if not annonce or not numero:
            continue
        if (annonce, numero) in par_couple:
            continue                      # le detail a deja repondu
        groupes.setdefault((annonce, numero), []).append(m)

    for (annonce, numero), rangee in groupes.items():
        versions = [v for v in (_version_depuis_ligne(l) for l in rangee) if v]
        versions.sort(key=compute_mandat_version_score, reverse=True)
        plat = _ligne_de_la_version(rangee, versions[0] if versions else {})
        depuis_miroir += 1
        _poser(annonce, numero, versions, "miroir", repli=plat)

    # ------------------------------------------------------------------ 3e SOURCE
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
            # ⚠ ET LA VERSION DE REPLI AUSSI, SI LA LIGNE N'EN A AUCUNE.
            #   Une ligne posee par un run anterieur, avant que les colonnes de
            #   version existent, reste sinon a zero version -- alors que le
            #   registre en compte UNE. Mesure du 30/09 : annonces 62038 et
            #   63003. Le COALESCE/NULLIF garantit qu'on ne remplace JAMAIS une
            #   version venue du detail : on ne fait que combler du vide.
            con.execute(
                "UPDATE app_mandat SET offre_type = COALESCE(NULLIF(offre_type,''), ?),"
                "                       nature = COALESCE(NULLIF(nature,''), ?),"
                "                       versions_json = COALESCE(NULLIF(versions_json,''), ?),"
                "                       version_count = CASE"
                "                            WHEN COALESCE(versions_json,'') IN ('', '[]')"
                "                            THEN 1 ELSE version_count END,"
                "                       avenants_json = COALESCE(NULLIF(avenants_json,''), '[]'),"
                "                       avenant_count = COALESCE(avenant_count, 0)"
                " WHERE hektor_annonce_id = ? AND numero_mandat = ?",
                (offres.get(annonce), _nature(None, None, offres.get(annonce)),
                 json.dumps([{
                     "id": None, "numero": numero, "type": None, "debut": None,
                     "fin": None, "cloture": None, "montant": None,
                     "mandants": None, "note": None, "avenants": [],
                 }], ensure_ascii=True, separators=(",", ":")),
                 annonce, numero),
            )
            continue
        if cle in adoptes:
            identifiant = adoptes.pop(cle)
        else:
            identifiant = prochain
            prochain += 1
        connus.add(cle)
        depuis_annonce += 1
        vus_ce_run.append(cle)
        # UNE VERSION DE REPLI, EXACTEMENT COMME LE REGISTRE EN FABRIQUE UNE.
        # Le registre, quand aucune fiche n'existe, pose une version vide
        # portant le seul numero -- et compte donc UNE version, pas zero.
        # Sans elle, `register_version_count` vaut 1 a l'ecran et NULL dans la
        # table : mesure du 30/09, deux lignes (annonces 62038 et 63003).
        version_repli = [{
            "id": None, "numero": numero, "type": None, "debut": None,
            "fin": None, "cloture": None, "montant": None, "mandants": None,
            "note": None, "avenants": [],
        }]
        con.execute(
            """
            INSERT INTO app_mandat(app_mandat_id, app_dossier_id, hektor_annonce_id,
                numero_mandat, famille, first_seen_at, last_seen_at, offre_type,
                nature, versions_json, version_count, avenants_json, avenant_count,
                origine, present_in_hektor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, '[]', 0, 'annonce', 1)
            ON CONFLICT(hektor_annonce_id, numero_mandat) DO NOTHING
            """,
            (identifiant, dossiers.get(annonce), annonce, numero,
             _famille(None, numero), vu, vu, offres.get(annonce),
             _nature(None, None, offres.get(annonce)),
             json.dumps(version_repli, ensure_ascii=True, separators=(",", ":"))),
        )

    adoptes_faits = adoptes_au_depart - len(adoptes)

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
    # ⚠ LE BILAN DOIT DIRE CE QU'IL A FAIT. Une reparation muette ne se mesure pas,
    #   et c'est ainsi que le deballeur de la diffusion a rendu zero trois mois
    #   (`deballeur-forme-inconnue-silence`) : le correctif n'est pas le carton,
    #   c'est LE COMPTEUR.
    return {"lus": lus, "neufs": neufs, "revus": revus,
            "adoptes_du_cloud": adoptes_faits,
            "sans_numero": sans_numero, "multi_versions": multi_versions,
            "depuis_miroir": depuis_miroir, "depuis_annonce": depuis_annonce,
            "sortis_du_miroir": sortis,
            "mandants_remplaces": mandants_remplaces,
            "mandants_combles": mandants_combles,
            "mandants_sans_recours": mandants_sans_recours,
            "mandants_sans_recours_exemples": sans_recours_exemples}


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



# =============================================================================
# LE PUSH VERS SUPABASE -- A.3-tech, etape A (30/09/2026)
#
# delete-never : on UPSERT, on n'efface jamais. Une ligne que le miroir ne
# montre plus porte present_in_hektor = 0 et RESTE. C'est ce qui distingue ce
# registre de la vue de travail, qui est videe et refaite a chaque push.
#
# ⛔ `--push` NE SE LANCE JAMAIS SEUL. Lecon du 07/09/2026, payee sur le ledger
#    d'affaires, et elle vaut mot pour mot ici :
#        06:38  un geste est fait depuis l'app -> le worker l'ecrit chez Supabase
#        07:52  `--push` lance a la main -> il pousse l'etat du MIROIR LOCAL,
#               qui date du run de 04:18 -> LE GESTE EST EFFACE
#    « La cause n'est pas le push, c'est l'ordre. Pousser sans rafraichir revient
#      a affirmer un etat qu'on n'a pas relu. »
#    Le garde-fou est donc dans le code, pas seulement dans un commentaire :
#    main() refuse --push sans --refresh, sauf --push-seul-je-sais assume.
#
# ⚠ TOUT RESTE EN `text` COTE SUPABASE, y compris versions_json et avenants_json.
#   C'est delibere : l'autre piege, ecrit dans affaire_ledger.py, est qu'une
#   colonne jsonb recevant une CHAINE de JSON accepte sans erreur et range du
#   texte dans du jsonb -- invisible. En restant en text on ne peut pas y tomber.
# =============================================================================

# Les colonnes de la table LOCALE qui n'existent pas cote Supabase seraient
# refusees par PostgREST (« column ... does not exist », et tout le lot tombe).
# On envoie donc EXACTEMENT les colonnes connues, nommees ici.
COLONNES_POUSSEES = (
    "app_mandat_id", "app_dossier_id", "hektor_annonce_id", "numero_mandat",
    "hektor_mandat_id", "famille", "type", "date_enregistrement", "date_debut",
    "date_fin", "montant", "mandants_texte", "note", "payload_json", "origine",
    "offre_type", "nature", "date_cloture", "versions_json", "version_count",
    "avenants_json", "avenant_count", "first_seen_at", "last_seen_at",
    "present_in_hektor",
)


def lignes_a_pousser(con: sqlite3.Connection) -> list[dict]:
    lignes = []
    for r in con.execute("SELECT * FROM app_mandat"):
        d = {c: r[c] for c in COLONNES_POUSSEES if c in r.keys()}
        # SQLite garde 0/1 ; Supabase attend un booleen. Sans cette ligne,
        # PostgREST reçoit 1 pour un champ boolean et refuse le lot entier.
        d["present_in_hektor"] = bool(d.get("present_in_hektor"))
        lignes.append(d)
    return lignes


def pousser(con: sqlite3.Connection, taille_lot: int = 200, a_blanc: bool = False) -> dict:
    lignes = lignes_a_pousser(con)
    if a_blanc:
        exemple = dict(lignes[0]) if lignes else {}
        for cle in ("payload_json", "versions_json", "avenants_json"):
            if exemple.get(cle):
                exemple[cle] = str(exemple[cle])[:60] + " ..."
        return {"a_blanc": True, "lignes": len(lignes),
                "colonnes": len(COLONNES_POUSSEES), "exemple": exemple}

    load_env_files(DEFAULT_ENV_FILES)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis")
    client = SupabaseRestClient(base_url=url, service_role_key=cle)
    if not client.table_available(TABLE):
        raise RuntimeError(
            "app_mandat n'existe pas cote Supabase. Appliquer d'abord "
            "supabase/patch_app_mandat_2026-09-29.sql puis "
            "supabase/patch_app_mandat_versions_2026-09-30.sql.")
    client.upsert_rows(path=TABLE, rows=lignes, batch_size=taille_lot)
    return {"lignes_poussees": len(lignes)}

def main() -> int:
    parser = argparse.ArgumentParser(
        description="A.3-tech phase 1 : remplit app_mandat depuis le miroir. LOCAL, dormant.")
    parser.add_argument("--refresh", action="store_true", help="Remplit la table depuis le miroir.")
    parser.add_argument("--controle", action="store_true", help="Affiche les controles, sans rien ecrire.")
    parser.add_argument("--partiel", action="store_true",
                        help="N'applique pas present_in_hektor=0 aux lignes non revues.")
    parser.add_argument("--push", action="store_true",
                        help="UPSERT vers Supabase (delete-never). Exige --refresh.")
    parser.add_argument("--push-a-blanc", action="store_true",
                        help="Compte et montre ce qui serait pousse, sans rien envoyer.")
    parser.add_argument("--push-seul-je-sais", action="store_true",
                        help="Lever le garde-fou et pousser SANS rafraichir. Voir sa raison.")
    parser.add_argument("--taille-lot", type=int, default=200)
    args = parser.parse_args()
    if not (args.refresh or args.controle or args.push or args.push_a_blanc):
        parser.error("choisir --refresh, --controle, --push ou --push-a-blanc")

    # ⛔ LE GARDE-FOU DU 07/09. Pousser sans rafraichir, c'est affirmer un etat
    #    qu'on n'a pas relu : le push envoie le miroir LOCAL, qui date du dernier
    #    run, et ecrase en ligne tout geste fait depuis. Sur le ledger d'affaires
    #    cela a efface l'annulation d'un compromis faite une heure plus tot.
    if args.push and not args.refresh and not args.push_seul_je_sais:
        parser.error(
            "--push sans --refresh est refuse : le push enverrait l'etat du miroir "
            "LOCAL, qui date du dernier run, et ecraserait en ligne tout geste fait "
            "depuis (lecon du 07/09/2026, ledger d'affaires). Utiliser "
            "`--refresh --push`, ou assumer avec --push-seul-je-sais.")

    if not HEKTOR_DB.exists():
        print("miroir introuvable : %s" % HEKTOR_DB, file=sys.stderr)
        return 2

    con = _open_local()
    try:
        if args.refresh:
            bilan = refresh(con, full=not args.partiel)
            print("REFRESH app_mandat")
            for k in ("lus", "neufs", "revus", "adoptes_du_cloud", "sans_numero", "multi_versions",
                      "depuis_miroir", "depuis_annonce", "sortis_du_miroir"):
                print("   %-22s : %s" % (k, bilan[k]))
            # LES MANDANTS, DITS A VOIX HAUTE (06/10/2026).
            print("   --- mandants, notre registre des liens en recours ---")
            print("   %-22s : %s   (corps emprunte a un autre bien)"
                  % ("remplaces", bilan["mandants_remplaces"]))
            print("   %-22s : %s   (champ vide sur une VENTE)"
                  % ("combles", bilan["mandants_combles"]))
            print("   %-22s : %s   (ni Hektor ni nous ne les connaissent)"
                  % ("sans recours", bilan["mandants_sans_recours"]))
            exemples = bilan.get("mandants_sans_recours_exemples") or []
            if exemples:
                # ⚠ ON LES NOMME. « 30 lignes restent vides » n'est pas actionnable ;
                #   une liste d'annonces a corriger dans nos liens, si.
                print("      a corriger dans app_relation :")
                for annonce, numero in exemples[:20]:
                    print("         annonce %-8s n° %s" % (annonce, numero))
                if len(exemples) > 20:
                    print("         ... et %d autres" % (len(exemples) - 20))
        elif not (args.push or args.push_a_blanc):
            con.executescript(SCHEMA)
        if args.push_a_blanc:
            bilan = pousser(con, a_blanc=True)
            print("")
            print("PUSH A BLANC -- rien n'est envoye")
            print("   lignes qui partiraient  : %s" % bilan["lignes"])
            print("   colonnes envoyees       : %s" % bilan["colonnes"])
            for k, v in sorted(bilan["exemple"].items()):
                print("      %-22s = %r" % (k, v))
        elif args.push:
            bilan = pousser(con, taille_lot=args.taille_lot)
            print("")
            print("PUSH app_mandat -> Supabase : %s lignes" % bilan["lignes_poussees"])
        if args.refresh or args.controle:
            controle(con)
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
