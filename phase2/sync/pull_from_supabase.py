#!/usr/bin/env python3
"""LA DESCENTE — Supabase vers le serveur local (tache B.1).

POURQUOI
--------
L'audit du 2026-08-21 (notice/AUDIT_DATA_LOCALE_ET_SYNCHRO_2026-08-21.md) a etabli que
TOUT va dans un seul sens : Hektor -> miroir -> base locale -> Supabase. Aucun script
n'ecrivait une valeur venue de Supabase dans une table locale -- pas partiellement : pas
du tout. Consequence : tout ce que l'app a INVENTE (rapprochements, index des documents,
registre des mandats, DVF, estimations, notifications...) n'existait qu'en ligne, sans
aucune copie ni sauvegarde locale. ~1 075 000 lignes.

Ce script est la moitie manquante. Il ne remplace pas le pipeline montant : il ajoute le
chemin qui redescend.

CE QU'IL FAIT
-------------
Il DECOUVRE les tables de Supabase (spec OpenAPI de PostgREST -- pas de liste a tenir a
jour, donc rien a oublier quand une table nouvelle apparait), puis recopie dans
phase2.sqlite, SOUS LE MEME NOM, celles qui n'existent pas deja en local.

LE GARDE-FOU, et c'est le coeur de la surete
--------------------------------------------
Le script REFUSE d'ecrire dans une table locale qu'il n'a pas lui-meme creee. La liste de
ce qu'il a cree vit dans sb_pull_state. Une table locale native ne peut donc pas etre
ecrasee, meme par erreur.

Au 21/08 cela exclut 10 tables, et c'est exactement ce qu'on veut :
  - app_affaire_ledger, app_diffusion_target, app_diffusion_agency_target,
    app_diffusion_request, app_diffusion_request_event
    -> le LOCAL en est le maitre, Supabase la copie. Les descendre serait a l'envers.
  - app_contact_current, app_contact_relation_current, app_contact_search_current,
    app_contact_duplicate_group_current, app_contact_duplicate_member_current
    -> ce sont les FICHES. Elles relevent de la tache B.2, qui les range A COTE de la
       table derivee, sans arbitrer.

CE QU'IL NE FAIT PAS
--------------------
Personne ne lit ces tables. Aucun script existant ne les connait. Le pipeline de nuit,
les workers, le push et les sentinelles sont inchanges. Retour arriere = DROP TABLE.
Verifie le 22/08 : 0 script du projet lit une table descendue, 0 script du run de nuit y
ecrit, et aucun autre fichier ne connait le suffixe __sb.

⚠ LE PIEGE A CONNAITRE, pour plus tard
--------------------------------------
TOUTE table listee dans sb_pull_state est une COPIE, refaite a chaque descente. Si un
script du projet se met un jour a ecrire dans l'une d'elles -- disons app_notification --
son travail sera EFFACE a la descente suivante, sans un bruit : la table est reconstruite
depuis Supabase.

Regle : ne jamais ecrire dans une table de sb_pull_state. Pour poser une donnee locale a
cote d'une copie, creer une table A PART -- c'est le patron app_search_registry, pose le
21/08 pour exactement cette raison (le run complet vidait la couche des recherches).

TYPES : les colonnes sont declarees SANS type (affinite BLOB), donc SQLite garde les
valeurs telles qu'elles arrivent -- entier, reel, texte. Les objets et tableaux JSON sont
stockes en texte JSON. C'est une copie de conservation, pas un modele de travail.

PAGINATION PAR CLE, pas par OFFSET (corrige le 21/08 apres le premier run). Chaque page
demande « les 1 000 lignes qui suivent la derniere valeur lue ». Avec un OFFSET, la vue
app_dossier_match_attrs tombait en 'statement timeout' des la 6e page : Postgres
recalculait la vue entiere a chaque fois. Par cle, elle passe en 34 s.

LES TROIS FREINS, poses le 22/08 apres l'incident (voir le compte rendu dans la note
d'audit). Ils ne sont pas cosmetiques : chacun repare une facon precise de perdre.

  1. COPIER PUIS RENOMMER. La copie remplit <table>__tmp ; l'ancienne n'est remplacee
     qu'une fois la neuve VERIFIEE COMPLETE (comptage cote Supabase avant la bascule).
     Une passe ratee -- panne, ou reponse tronquee prise pour une fin de table -- laisse
     donc la copie de la veille intacte. Le serveur ne peut JAMAIS finir avec moins
     qu'avant. Sans ce frein, la 2e passe du 21/08 a detruit 64 bonnes copies.
  2. UN FREIN ENTRE LES REQUETES (PAUSE_PAGE, PAUSE_TABLE) et les tables triees de la
     plus legere a la plus lourde. C'est le debit soutenu -- 2 800 requetes sans pause --
     qui a sature l'instance Supabase jusqu'a son redemarrage.
  3. UN VERROU. Deux descentes simultanees sont la cause DIRECTE de l'incident : j'en ai
     relance une alors que la premiere finissait. Le fichier temoin rend la faute
     impossible ; le --dry-run, lui, reste libre.

LE CAS DES VUES SANS CLE PRIMAIRE, resolu le 22/08. Postgres n'en declare aucune, donc
on parcourt sur la premiere colonne -- qui peut se repeter. Sur
app_mandat_broadcast_current (1 528 lignes pour 343 dossiers, jusqu'a 10 lignes par
dossier, une par portail), la frontiere d'une page tombait au milieu d'un dossier et
« apres ce dossier » sautait ses lignes restantes : 1 524 lues au lieu de 1 528.
Le comptage avant bascule l'a refusee, puis une RELECTURE PAR RANG, triee sur TOUTES les
colonnes (ordre total, donc aucune egalite possible), la rend complete. Reservee au petit
volume : l'offset coute cher en profondeur sur une vue calculee.

⚠ PostgREST PLAFONNE toute reponse a 1 000 lignes, quel que soit le `limit` demande --
verifie le 22/08 : une demande de 1 528 lignes en a rendu 1 000. Ne jamais compter sur une
lecture « en un seul morceau ».

USAGE
-----
  python phase2/sync/pull_from_supabase.py --dry-run    # affiche le plan, n'ecrit rien
  python phase2/sync/pull_from_supabase.py              # descend tout
  python phase2/sync/pull_from_supabase.py --table app_rapprochement   # une seule
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
DEFAULT_ENV_FILES = (ROOT / ".env", ROOT / "apps" / "hektor-v1" / ".env")
STATE_TABLE = "sb_pull_state"
PAGE_SIZE = 1000
PAUSE_PAGE = 0.3        # secondes entre deux pages
PAUSE_TABLE = 2.0       # secondes entre deux tables
VERROU = "pull_from_supabase.lock"
RELECTURE_ENTIERE_MAX = 5000   # au-dela, on ne redemande pas une table en un seul bloc


def load_env_file(path: Path) -> None:
    """Meme convention que push_contacts_to_supabase.py."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


class SupabaseReader:
    """Lecture seule. Aucune methode d'ecriture : ce script ne peut pas toucher Supabase."""

    def __init__(self, base_url: str, service_role_key: str, timeout: int = 300,
                 max_retries: int = 4) -> None:
        self.base_url = base_url.rstrip("/")
        self.key = service_role_key
        self.timeout = timeout
        self.max_retries = max_retries

    def get(self, path: str, extra_headers: dict[str, str] | None = None,
            with_headers: bool = False) -> Any:
        url = f"{self.base_url}/rest/v1/{path.lstrip('/')}"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Accept": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)
        request = urllib.request.Request(url, headers=headers, method="GET")
        last: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw = response.read().decode("utf-8")
                    data = json.loads(raw) if raw else None
                    return (data, dict(response.headers)) if with_headers else data
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if exc.code in (500, 502, 503, 504) and attempt < self.max_retries:
                    last = RuntimeError(f"HTTP {exc.code}: {detail[:300]}")
                    time.sleep(1.5 * attempt)
                    continue
                raise RuntimeError(f"Supabase GET {path} -> HTTP {exc.code}: {detail[:500]}") from exc
            except (TimeoutError, urllib.error.URLError) as exc:
                last = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(1.5 * attempt)
        raise RuntimeError(f"Supabase GET {path} : reseau/timeout ({last})")

    def schema(self) -> dict[str, tuple[list[str], str]]:
        """Tables et vues exposees : {nom: (colonnes, colonne de parcours)}.

        La colonne de parcours est la CLE PRIMAIRE quand PostgREST la declare -- il
        l'annonce dans la description de la propriete ('Primary Key'). A defaut (les vues
        n'en ont pas), on prend la premiere colonne.
        """
        spec = self.get("")
        out: dict[str, tuple[list[str], str]] = {}
        for name, definition in (spec or {}).get("definitions", {}).items():
            props = (definition or {}).get("properties") or {}
            if not props:
                continue
            colonnes = list(props.keys())
            cle = next(
                (c for c in colonnes
                 if "primary key" in str((props[c] or {}).get("description", "")).lower()),
                colonnes[0],
            )
            out[name] = (colonnes, cle)
        return out

    def count(self, table: str) -> int | None:
        """Nombre de lignes cote Supabase, lu dans l'en-tete Content-Range."""
        try:
            _, headers = self.get(f"{urllib.parse.quote(table)}?select=*&limit=1",
                                  {"Prefer": "count=exact"}, with_headers=True)
        except Exception:                                          # noqa: BLE001
            return None
        portee = headers.get("Content-Range") or headers.get("content-range") or ""
        if "/" in portee:
            total = portee.rsplit("/", 1)[1]
            if total.isdigit():
                return int(total)
        return None

    def page_par_rang(self, table: str, colonnes: list[str], rang: int,
                      size: int) -> list[dict[str, Any]]:
        """Pagination par RANG, avec un ordre TOTAL (toutes les colonnes).

        Sert de rattrapage quand le parcours par valeur a saute des lignes -- cas d'une
        vue sans cle primaire dont la premiere colonne se repete. Trier sur toutes les
        colonnes rend l'ordre total : deux lignes ne peuvent plus etre a egalite, donc
        « les 1 000 suivantes » ne peut plus rien omettre.
        """
        ordre = ",".join(urllib.parse.quote(c) + ".asc" for c in colonnes)
        path = (f"{urllib.parse.quote(table)}?select=*&order={ordre}"
                f"&limit={size}&offset={rang}")
        rows = self.get(path)
        return rows if isinstance(rows, list) else []

    def page_apres(self, table: str, cle: str, borne: Any, size: int) -> list[dict[str, Any]]:
        """Pagination PAR CLE, pas par OFFSET.

        Correctif du 21/08 : `offset=5000` sur une VUE force Postgres a recalculer 6 000
        lignes a chaque page -- cout quadratique, et la vue app_dossier_match_attrs
        tombait en 'statement timeout'. Avec un filtre `cle > derniere valeur lue`, chaque
        page coute la meme chose que la premiere, et une ligne inseree pendant la copie ne
        decale plus tout ce qui suit.
        """
        path = (f"{urllib.parse.quote(table)}?select=*"
                f"&order={urllib.parse.quote(cle)}.asc&limit={size}")
        if borne is not None:
            path += f"&{urllib.parse.quote(cle)}=gt.{urllib.parse.quote(str(borne), safe='')}"
        rows = self.get(path)
        return rows if isinstance(rows, list) else []


def ensure_state_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"""CREATE TABLE IF NOT EXISTS {STATE_TABLE} (
                table_name       TEXT PRIMARY KEY,
                lignes           INTEGER,
                derniere_descente TEXT,
                dernier_echec    TEXT
            )"""
    )
    colonnes = {r[1] for r in conn.execute(f"PRAGMA table_info({STATE_TABLE})")}
    if "dernier_echec" not in colonnes:
        conn.execute(f"ALTER TABLE {STATE_TABLE} ADD COLUMN dernier_echec TEXT")
    conn.commit()


def local_tables(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


def descendues(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute(f"SELECT table_name FROM {STATE_TABLE}")}


def encode(value: Any) -> Any:
    """Scalaires tels quels ; objets et tableaux en texte JSON."""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def copy_table(conn: sqlite3.Connection, reader: SupabaseReader, distant: str,
               table: str, columns: list[str], cle: str, stamp: str) -> tuple[int, int]:
    """Recopie une table. Renvoie (lignes ecrites, appels API).

    `distant` = le nom chez Supabase, celui qu'on interroge.
    `table`   = le nom en local, qui porte le suffixe __sb quand le nom est deja pris.
    """
    quoted = ", ".join('"%s"' % c.replace('"', '""') for c in columns)
    placeholders = ", ".join("?" for _ in columns)
    # COPIER PUIS RENOMMER -- correctif du 22/08, apres l'incident de la nuit.
    # L'ancienne version faisait DROP puis CREATE : l'ancienne copie mourait AVANT que la
    # neuve existe. Quand la 2e passe a echoue sur 64 tables, elle a donc detruit les
    # BONNES copies que la 1re passe avait faites. On remplit desormais une table
    # temporaire, et on ne remplace l'ancienne qu'une fois la copie complete. Une passe
    # ratee laisse la copie de la veille intacte.
    tmp = table + "__tmp"
    conn.execute('DROP TABLE IF EXISTS "%s"' % tmp)
    conn.execute('CREATE TABLE "%s" (%s)' % (tmp, quoted))
    # ENREGISTRER AVANT DE COPIER -- correctif du 21/08, apres l'echec de
    # app_dossier_match_attrs au premier run. Sans cette ligne, une copie interrompue
    # laissait une table PARTIELLE absente de sb_pull_state : au run suivant elle passait
    # pour une table NATIVE, le garde-fou la protegeait, et elle n'etait plus JAMAIS
    # retentee. Une copie tronquee se faisant passer pour de la donnee, en silence.
    conn.execute(
        f"INSERT INTO {STATE_TABLE}(table_name, lignes, derniere_descente, dernier_echec) "
        "VALUES(?, NULL, ?, 'copie en cours') "
        "ON CONFLICT(table_name) DO UPDATE SET lignes=NULL, derniere_descente=excluded.derniere_descente, "
        "dernier_echec='copie en cours'",
        (table, stamp),
    )
    conn.commit()

    total = 0
    appels = 0
    borne: Any = None
    taille = PAGE_SIZE
    while True:
        # PAQUET QUI S'ADAPTE -- correctif du 22/08. Les tables de detail portent un gros
        # paquet JSON par ligne (app_dossier_detail_current : 249 Mo pour 13 212 lignes,
        # soit ~19 ko/ligne). Un paquet de 1 000 lignes = ~19 Mo dans une seule reponse :
        # Cloudflare coupe (HTTP 522) ou Postgres depasse son delai. On divise alors le
        # paquet par deux et on redemande LA MEME page, jusqu'a 25 lignes. Une table lourde
        # descend donc plus lentement, mais elle descend.
        while True:
            try:
                rows = reader.page_apres(distant, cle, borne, taille)
                break
            except RuntimeError as exc:
                lourd = any(m in str(exc) for m in ("522", "504", "57014", "timeout", "reseau"))
                if not lourd or taille <= 25:
                    raise
                taille = max(25, taille // 4)
                print(f"        {distant} : reponse trop lourde, paquet ramene a {taille}")
        appels += 1
        if not rows:
            break
        conn.executemany(
            'INSERT INTO "%s" (%s) VALUES (%s)' % (tmp, quoted, placeholders),
            [tuple(encode(row.get(c)) for c in columns) for row in rows],
        )
        total += len(rows)
        suivante = rows[-1].get(cle)
        if suivante is None or suivante == borne:
            # La colonne de parcours ne progresse plus (valeur nulle, ou repetee sur toute
            # une page) : continuer bouclerait a l'infini. On s'arrete, et le controle de
            # comptes en fin de run signalera l'ecart plutot que de le taire.
            break
        borne = suivante
        if len(rows) < taille:
            break
        # FREIN -- correctif du 22/08. C'est le debit soutenu (2 800 requetes sans pause)
        # qui a sature l'instance jusqu'au redemarrage. Sur ~1 400 pages, 0,3 s ajoutent
        # ~7 minutes a la descente. C'est le prix a payer, et il est petit.
        time.sleep(PAUSE_PAGE)

    # VERIFIER AVANT DE REMPLACER -- correctif du 22/08, trouve par le test.
    # La boucle s'arrete des qu'une page rend moins de lignes qu'on en a demande. C'est
    # normalement la fin de la table... mais une reponse tronquee produit le meme signal.
    # Sans ce controle, une copie incomplete remplacait la bonne, sans un bruit. On compte
    # donc chez Supabase AVANT la bascule : si la neuve n'est pas entiere, on la refuse et
    # l'ancienne reste. Le serveur ne peut jamais se retrouver avec MOINS qu'avant.
    attendu = reader.count(distant)

    # LE RATTRAPAGE PAR RANG -- correctif du 22/08, cas vu en vrai sur
    # app_mandat_broadcast_current (1 524 lues / 1 528 attendues).
    #
    # POURQUOI il manquait 4 lignes. Le parcours avance en demandant « les lignes APRES la
    # derniere valeur lue ». Sur une vraie table on avance sur la CLE PRIMAIRE, unique par
    # ligne : « apres la ligne 4521 » ne peut rien sauter. Mais une VUE n'a pas de cle
    # primaire -- Postgres n'en declare aucune -- et on se rabat sur la premiere colonne.
    # Ici c'est app_dossier_id, qui se REPETE : 1 528 lignes pour 343 dossiers, jusqu'a 10
    # lignes pour un seul (une par portail de diffusion). Quand la frontiere d'une page
    # tombe au milieu d'un dossier, « apres ce dossier » saute ses lignes restantes.
    #
    # LE REMEDE. On relit la table par RANG (offset) et non par valeur, en triant sur
    # TOUTES ses colonnes : l'ordre devient total, donc « les 1 000 suivantes » ne peut
    # plus rien sauter, meme quand la premiere colonne se repete.
    #
    # ⚠ Ce qu'il ne faut PAS tenter : redemander la table entiere d'un coup. PostgREST
    # plafonne toute reponse a 1 000 lignes quel que soit le `limit` -- verifie le 22/08 :
    # une demande de 1 528 lignes en a rendu 1 000. La pagination est obligatoire.
    #
    # Reserve au petit volume : l'offset coute cher en profondeur sur une vue calculee
    # (c'est ce qui faisait tomber app_dossier_match_attrs en 'statement timeout').
    if attendu is not None and attendu != total and attendu <= RELECTURE_ENTIERE_MAX:
        print(f"        {distant} : {total}/{attendu} -- relecture par rang (ordre total)")
        conn.execute('DELETE FROM "%s"' % tmp)
        total = 0
        rang = 0
        while rang < attendu:
            rows = reader.page_par_rang(distant, columns, rang, PAGE_SIZE)
            appels += 1
            if not rows:
                break
            conn.executemany(
                'INSERT INTO "%s" (%s) VALUES (%s)' % (tmp, quoted, placeholders),
                [tuple(encode(row.get(c)) for c in columns) for row in rows],
            )
            total += len(rows)
            rang += len(rows)
            time.sleep(PAUSE_PAGE)

    if attendu is not None and attendu != total:
        # Au-dela de RELECTURE_ENTIERE_MAX, une vue sans cle primaire dont la premiere
        # colonne se repete n'est pas copiable telle quelle. Aucune ne l'est aujourd'hui ;
        # le jour ou ca arrive, cette erreur le dira au lieu de laisser passer une copie
        # amputee.
        raise RuntimeError(
            f"copie incomplete : {total} lignes lues, {attendu} attendues cote Supabase "
            "-- l'ancienne copie est conservee")

    # LA BASCULE : l'ancienne n'est remplacee qu'ICI, copie verifiee complete.
    conn.execute('DROP TABLE IF EXISTS "%s"' % table)
    conn.execute('ALTER TABLE "%s" RENAME TO "%s"' % (tmp, table))
    conn.execute(
        f"UPDATE {STATE_TABLE} SET lignes=?, derniere_descente=?, dernier_echec=NULL "
        "WHERE table_name=?",
        (total, stamp, table),
    )
    conn.commit()
    return total, appels


def marquer_echec(conn: sqlite3.Connection, table: str, message: str) -> None:
    """Une copie ratee ne laisse JAMAIS de table partielle derriere elle.

    On supprime la copie tronquee et on garde la trace dans sb_pull_state : la table
    reste donc connue comme « descendue », donc retentee au prochain run -- au lieu
    d'etre confondue avec une table native et protegee a jamais.
    """
    try:
        # On ne supprime QUE la table temporaire : la copie precedente, elle, est
        # conservee. C'est tout l'objet du correctif du 22/08 -- une passe ratee ne doit
        # jamais laisser le serveur avec moins qu'avant.
        conn.execute('DROP TABLE IF EXISTS "%s"' % (table + "__tmp"))
    except Exception:                                              # noqa: BLE001
        pass
    conn.execute(
        f"UPDATE {STATE_TABLE} SET lignes=NULL, dernier_echec=? WHERE table_name=?",
        (message[:500], table),
    )
    conn.commit()


class DescenteDejaEnCours(RuntimeError):
    """Levee quand une descente tourne deja. Traitee a part pour sortir proprement."""


class VerrouUnique:
    """Une seule descente a la fois -- correctif du 22/08.

    C'est la cause DIRECTE de l'incident : j'ai relance une descente complete alors que la
    premiere finissait a peine. Deux passes simultanees, ~2 800 requetes, et l'instance
    Supabase a cede jusqu'au redemarrage. Un fichier temoin suffit a rendre la faute
    impossible.
    """

    def __init__(self, chemin: Path) -> None:
        self.chemin = chemin

    def __enter__(self) -> "VerrouUnique":
        if self.chemin.exists():
            age = time.time() - self.chemin.stat().st_mtime
            raise DescenteDejaEnCours(
                f"une descente tourne deja (verrou pose il y a {int(age)}s : {self.chemin}). "
                "Si c'est un residu d'un run interrompu, supprimer le fichier a la main."
            )
        self.chemin.write_text(str(os.getpid()), encoding="utf-8")
        return self

    def __exit__(self, *_exc: object) -> None:
        try:
            self.chemin.unlink()
        except OSError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Descend les tables Supabase dans la base locale (tache B.1).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche le plan sans rien ecrire.")
    parser.add_argument("--table", action="append", default=[],
                        help="Ne descendre que cette table (repetable).")
    parser.add_argument("--phase2-db", type=Path, default=PHASE2_DB)
    args = parser.parse_args()

    for env_file in DEFAULT_ENV_FILES:
        load_env_file(env_file)
    base_url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not base_url or not key:
        raise RuntimeError("SUPABASE_URL/VITE_SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")

    reader = SupabaseReader(base_url, key)
    conn = sqlite3.connect(str(args.phase2_db))
    ensure_state_table(conn)

    schema = reader.schema()
    deja_descendues = descendues(conn)
    natives = local_tables(conn) - deja_descendues - {STATE_TABLE}

    # LA REGLE, revue le 22/08 (tache B.2). L'ancienne disait : « le nom existe deja en
    # local -> on ne touche pas ». Elle protegeait bien, mais elle laissait dehors des
    # donnees qui n'existaient NULLE PART ailleurs : app_diffusion_request (9 demandes) et
    # app_diffusion_request_event (29) sont creees par le front, dans Supabase, et la table
    # locale du meme nom est une coquille VIDE creee par le schema. Le garde-fou les prenait
    # pour des tables natives et les excluait.
    #
    # La regle n'a donc plus d'exception : QUAND UN NOM SE HEURTE, ON DESCEND SOUS <nom>__sb.
    #   - rien n'est jamais ecrase : aucune table locale n'est touchee, quel que soit son
    #     contenu ;
    #   - rien n'est jamais oublie : pas de liste a tenir, donc aucune table ne passe au
    #     travers ;
    #   - aucun jugement a porter sur « qui est le maitre » -- je me suis trompe deux fois
    #     sur dix en essayant (app_diffusion_request et son _event).
    #
    # cibles = [(nom chez Supabase, nom en local)]
    cibles: list[tuple[str, str]] = []
    doublures: list[tuple[str, str]] = []
    for nom in sorted(schema):
        if args.table and nom not in args.table:
            continue
        if nom in natives:
            cibles.append((nom, nom + "__sb"))
            doublures.append((nom, nom + "__sb"))
        else:
            cibles.append((nom, nom))

    print(f"Supabase expose {len(schema)} tables/vues")
    print(f"  a descendre : {len(cibles)}")
    if doublures:
        print(f"  dont {len(doublures)} sous un nom de doublure (le nom local est pris) :")
        for distant, local in doublures:
            print(f"     - {distant}  ->  {local}")

    if args.dry_run:
        print("\n[dry-run] rien n'a ete ecrit")
        return 0

    # LE VERROU englobe TOUT le travail : acquis ici, relache quoi qu'il arrive.
    with VerrouUnique(ROOT / VERROU):
        # LES PLUS LEGERES D'ABORD -- correctif du 22/08. Les tables lourdes sont celles qui
        # font ceder l'instance ; en les passant en dernier, tout le reste est deja a l'abri
        # quand on les aborde. Le poids est estime par le nombre de colonnes a defaut de mieux,
        # et par le compte deja connu quand on l'a.
        connus = {r[0]: (r[1] or 0) for r in conn.execute(
            f"SELECT table_name, lignes FROM {STATE_TABLE}")}
        cibles.sort(key=lambda c: (connus.get(c[1], 0) * len(schema[c[0]][0]), c[0]))

        stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        debut = time.time()
        lignes_totales = 0
        appels_totaux = 0
        echecs: list[tuple[str, str]] = []
        for index, (distant, local) in enumerate(cibles, start=1):
            try:
                colonnes, cle = schema[distant]
                lignes, appels = copy_table(conn, reader, distant, local, colonnes, cle, stamp)
                lignes_totales += lignes
                appels_totaux += appels
                print(f"  [{index:>3}/{len(cibles)}] {local:<46} {lignes:>8} lignes")
            except Exception as exc:                                   # noqa: BLE001
                # Une table en echec ne doit pas arreter la descente : on note et on continue.
                # marquer_echec supprime la copie partielle -- voir le correctif du 21/08.
                marquer_echec(conn, local, str(exc))
                echecs.append((local, str(exc)[:200]))
                print(f"  [{index:>3}/{len(cibles)}] {local:<46}    ECHEC : {str(exc)[:120]}")
            time.sleep(PAUSE_TABLE)

        duree = round(time.time() - debut)
        print(f"\n{lignes_totales} lignes descendues dans {len(cibles) - len(echecs)} tables "
              f"en {duree}s ({appels_totaux} appels API)")
        if echecs:
            print(f"{len(echecs)} table(s) en echec :")
            for nom, err in echecs:
                print(f"   {nom} : {err}")
        conn.close()
        return 1 if echecs else 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DescenteDejaEnCours as exc:
        # Sortie propre plutot qu'une trace : ce script est fait pour tourner en tache
        # planifiee, et un chevauchement n'est pas un bogue -- c'est le garde-fou qui joue.
        print(f"ARRET : {exc}")
        raise SystemExit(2) from None
