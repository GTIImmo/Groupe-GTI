#!/usr/bin/env python3
"""Run « recherches actives » (filet de fond, n°5 de l'archi cible).

Rafraîchit depuis Hektor les contacts ayant au moins une recherche ACTIVE, SANS
filtre date_maj — pour capter les éditions de recherche faites directement dans
Hektor (que le quotidien `--changed-only` manque, car éditer une recherche ne
bump pas la date_maj du contact). Complète le read-through (qui ne couvre que les
contacts ouverts) : ce run rattrape ceux que personne n'ouvre.

Périmètre : `app_contact_search_current.is_active = 1` dans la base locale phase2
(~3 590 contacts). Traite par lots via le pipeline éprouvé :
  sync_contact_details (fetch ContactById, ~0,3s/contact) -> normalize ->
  build_contacts_layer -> push_contacts_to_supabase (qui saute déjà les "dirty").

Coût mesuré ~0,3s/contact -> ~20 min pour un passage complet. Idempotent et
reprenable (chaque lot est indépendant). À planifier 1×/jour (tâche planifiée).
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
PYTHON = sys.executable
# Verrou des traitements lourds phase2, pose par pull_from_supabase (descente) ET par
# comparer_doublures (releve) depuis le 22/08. On le LIT entre deux lots pour ceder la
# place ; on ne le POSE jamais : la descente est planifiee et quotidienne, un rattrapage
# de 5 h qui la ferait sauter serait pire que le mal.
VERROU_LOURD = ROOT / "pull_from_supabase.lock"
# L'etape 1 le relache avant que l'etape 2 le reprenne : sans marge, on se faufilerait
# dans cet interstice pour repartir juste avant les CREATE INDEX du releve.
VERROU_MARGE_S = 5.0


def active_search_contact_ids(db_path: Path) -> list[str]:
    """Les NUMEROS DE HEKTOR des contacts ayant >=1 recherche active.

    ⚠ C-6, 23/09/2026 -- CETTE LISTE PART CHEZ HEKTOR, ET ELLE VENAIT DE CHEZ NOUS.
      Elle est tiree de NOTRE couche puis passee telle quelle a
      `sync_contact_details` (donc a l'API de Hektor) et a
      `normalize_source --contact-id` (donc au MIROIR). Tant qu'un contact porte
      le meme numero des deux cotes, cela ne se voit pas. Le jour de la bascule,
      ce sont nos numeros qui partaient : Hektor aurait repondu 404 -- et il les
      aurait inscrits en liste noire -- pendant que le miroir, lui, se serait
      laisse ecrire des fiches vides sous nos numeros.

      On demande donc explicitement la CIBLE. Aujourd'hui elle vaut l'identite,
      la liste est identique au caractere pres.
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT DISTINCT COALESCE(NULLIF(c.hektor_target_id, ''), s.hektor_contact_id) "
            "       AS pour_hektor "
            "FROM app_contact_search_current s "
            "LEFT JOIN app_contact_current c ON c.hektor_contact_id = s.hektor_contact_id "
            "WHERE s.is_active = 1 AND (s.archive IS NULL OR s.archive = 0) "
            "ORDER BY CAST(pour_hektor AS INTEGER)"
        ).fetchall()
    finally:
        conn.close()
    out: list[str] = []
    seen: set[str] = set()
    for row in rows:
        cid = str(row["pour_hektor"] or "").strip()
        if cid.isdigit() and cid not in seen:
            seen.add(cid)
            out.append(cid)
    return out


def identites_pour_ces_cibles(db_path: Path, cibles: list[str]) -> list[str]:
    """Le chemin inverse : sous quel numero NOTRE couche range-t-elle ces contacts ?

    Les trois etapes locales ne parlent pas la meme langue : `normalize_source`
    travaille sur le MIROIR (numeros de Hektor), le push travaille sur NOTRE
    couche (identites). Une seule liste pour les deux etait juste tant que les
    deux numeros etaient egaux.
    """
    if not cibles:
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        connues: dict[str, str] = {}
        for debut in range(0, len(cibles), 400):
            tranche = cibles[debut:debut + 400]
            trous = ",".join("?" for _ in tranche)
            for row in conn.execute(
                f"SELECT hektor_contact_id, hektor_target_id FROM app_contact_current "
                f"WHERE hektor_target_id IN ({trous})", tuple(tranche)
            ):
                cible = str(row["hektor_target_id"] or "").strip()
                if cible:
                    connues[cible] = str(row["hektor_contact_id"] or "").strip()
    finally:
        conn.close()
    # Un contact que notre couche ne connait pas encore reste sous son numero de
    # Hektor : c'est ce que faisait le code d'avant, et c'est juste.
    return [connues.get(cible) or cible for cible in cibles]


def acquereur_contact_ids(hektor_db: Path) -> list[str]:
    """IDs des contacts NON archives portant la typologie Hektor « acquereur ».

    Perimetre du RATTRAPAGE (21/08/2026). Le run quotidien ne relit que les contacts
    dont l'app connait deja une recherche active (~3 800) : un contact qui gagne sa
    PREMIERE recherche n'y entre jamais, et creer une recherche ne bouge pas la
    date_maj du contact -- il reste donc invisible indefiniment. La typologie, elle,
    est dans le listing (rafraichi chaque nuit) et ENVELOPPE les recherches : sonde du
    21/08 sur 249 fiches lues en direct, aucune recherche connue hors de cette
    typologie. Relire tous les acquereurs ferme le trou.

    Sonde du 21/08 : 1 fiche sur 249 portait une recherche que l'app ignorait,
    soit ~270 recherches invisibles sur 67 483 contacts.
    """
    conn = sqlite3.connect(f"file:{hektor_db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT hektor_contact_id FROM hektor_contact "
            "WHERE archive = '0' AND typologie_json LIKE '%acqu%' "
            "ORDER BY CAST(hektor_contact_id AS INTEGER)"
        ).fetchall()
    finally:
        conn.close()
    out: list[str] = []
    seen: set[str] = set()
    for row in rows:
        cid = str(row["hektor_contact_id"] or "").strip()
        if cid.isdigit() and cid not in seen:
            seen.add(cid)
            out.append(cid)
    return out


CARNET_ACQUEREUR_TABLE = "sync_contact_typologie_acquereur"


def carnet_acquereur_ids(hektor_db: Path, plafond: int) -> list[str]:
    """LES CONTACTS QUI VIENNENT DE DEVENIR ACQUEREURS -- 20/09/2026.

    Hektor pose lui-meme la typologie « acquereur » quand une recherche est
    enregistree (prouve sur 605075, 605414, 605429 : crees « mandant », devenus
    « acquereur, mandant » sans intervention). Le listing de 05:00 rapporte cette
    typologie chaque nuit ; normalize_source inscrit le PASSAGE dans ce carnet.

    Relire ces fiches-la, et elles seules, fait entrer la recherche creee dans
    Hektor -- le seul cas que ni le delta de 05:00 (la date_maj ne bouge pas) ni
    la passe habituelle de 03:00 (elle ne lit que les recherches DEJA connues) ne
    voient.

    Le carnet peut ne pas exister (premier passage, ou retour arriere par DROP) :
    on rend une liste vide, jamais une erreur.
    """
    conn = sqlite3.connect(f"file:{hektor_db}?mode=ro", uri=True)
    try:
        existe = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (CARNET_ACQUEREUR_TABLE,),
        ).fetchone()
        if not existe:
            return []
        rows = conn.execute(
            f"SELECT hektor_contact_id FROM {CARNET_ACQUEREUR_TABLE} "
            f"WHERE traite_le IS NULL ORDER BY detecte_le, CAST(hektor_contact_id AS INTEGER)"
        ).fetchall()
    finally:
        conn.close()
    out = [str(r[0]).strip() for r in rows if str(r[0] or "").strip().isdigit()]
    # PLAFOND DE DEBIT, pas de confort : un jour d'import massif chez Hektor
    # (reprise de portefeuille, reclassement en masse) ferait basculer des
    # milliers de fiches d'un coup. On en prend un nombre borne ; le reste attend
    # la nuit suivante, le carnet ne perd rien.
    return out[:plafond] if plafond > 0 else out


def marquer_carnet_traite(hektor_db: Path, ids: list[str], depuis: str) -> int:
    """Marque traitees les fiches du carnet dont le DETAIL a ete relu pendant ce
    run. On ne se fie pas au fait d'avoir demande la lecture : on verifie qu'elle
    a eu lieu (sync_contact_state.last_detail_sync_at). Une fiche en echec, en
    liste noire ou sautee par le coupe-circuit reste donc a traiter demain."""
    if not ids:
        return 0
    conn = sqlite3.connect(str(hektor_db))
    try:
        conn.execute("PRAGMA busy_timeout = 30000")
        marques = 0
        for lot in (ids[i : i + 400] for i in range(0, len(ids), 400)):
            places = ",".join("?" for _ in lot)
            cur = conn.execute(
                f"""
                UPDATE {CARNET_ACQUEREUR_TABLE}
                   SET traite_le = ?,
                       lu_le = (SELECT s.last_detail_sync_at FROM sync_contact_state s
                                 WHERE s.hektor_contact_id = {CARNET_ACQUEREUR_TABLE}.hektor_contact_id)
                 WHERE traite_le IS NULL
                   AND hektor_contact_id IN ({places})
                   AND EXISTS (SELECT 1 FROM sync_contact_state s
                                WHERE s.hektor_contact_id = {CARNET_ACQUEREUR_TABLE}.hektor_contact_id
                                  AND s.last_detail_sync_at >= ?)
                """,
                [datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), *lot, depuis],
            )
            marques += cur.rowcount or 0
        conn.commit()
        return marques
    finally:
        conn.close()


class EchecEtape(RuntimeError):
    """Echec d'une des 4 etapes d'un lot, en gardant LAQUELLE.

    Sans ca, le coupe-circuit ne pouvait qu'accuser Hektor : le 22/08 il a annonce un
    bannissement d'IP alors que les fetchs passaient tous (success=300 errors=0) et que
    la panne etait un « database is locked » local.
    """

    def __init__(self, script: str, code: int, commande: str) -> None:
        super().__init__(f"Echec etape: {commande} (code {code})")
        self.script = script


def etape_est_reseau(script: str) -> bool:
    """Seul sync_contact_details parle a Hektor ; les 3 autres etapes sont locales."""
    return script.replace("\\", "/").endswith("sync_contact_details.py")


def run_step(args: list[str]) -> None:
    result = subprocess.run([PYTHON, *args], cwd=str(ROOT))
    if result.returncode != 0:
        raise EchecEtape(args[0], result.returncode, " ".join(args))


def fetch_all(ids: list[str], *, request_delay_seconds: float,
              batch_size: int, batch_pause_seconds: float) -> None:
    """LA lecture Hektor : UN seul processus pour toute la session, donc UNE authentification.

    C'est le correctif du 23/08/2026, et c'est le vrai. Jusqu'ici, sync_contact_details
    etait relance a chaque lot de 300 : chaque processus refaisait
    /Api/OAuth/Authenticate/ puis /Api/OAuth/Sso/ de zero. Mesure en base :

        30/05  ->   1 processus pour 43 842 fiches   (43 842 fiches / authentification)
        22/08  ->  88 processus pour 23 059 fiches   (   262 fiches / authentification)

    90 fois plus de demandes de jeton pour moitie moins de donnees. Et TOUS nos echecs
    tombaient sur /Api/OAuth/Authenticate/, jamais sur ContactById : ce n'est pas la
    lecture qui etait bridee, c'est la redemande de jeton en rafale -- le motif qu'une
    protection lit comme une attaque sur les identifiants.

    Les valeurs par defaut reprennent celles du run quotidien, seul run a n'avoir jamais
    eu d'incident en quatre mois : gros lots, vraie pause entre eux, delai court entre
    deux fiches.
    """
    # Les IDs passent par un FICHIER, pas par la ligne de commande : a 5 000 contacts le
    # CSV depasse les 32 767 caracteres de Windows et le processus ne demarre pas du tout
    # (WinError 206, constate le 23/08). Le fichier leve toute limite de taille de session.
    with tempfile.NamedTemporaryFile("w", suffix=".ids", delete=False, encoding="utf-8") as fh:
        fh.write(",".join(ids))
        liste = fh.name
    try:
        _fetch_step(liste, request_delay_seconds, batch_size, batch_pause_seconds)
    finally:
        try:
            os.unlink(liste)
        except OSError:
            pass


def _fetch_step(liste: str, request_delay_seconds: float,
                batch_size: int, batch_pause_seconds: float) -> None:
    run_step([
        "phase2/sync/sync_contact_details.py", "--contact-id-file", liste,
        "--skip-listing-refresh", "--limit", "0",
        "--request-delay-seconds", str(request_delay_seconds),
        "--batch-size", str(batch_size),
        "--batch-pause-seconds", str(batch_pause_seconds),
        "--max-consecutive-hard-errors", "3", "--no-normalize",
    ])


def process_local(ids: list[str], db_path: Path) -> None:
    """Etapes 2 a 4 : normalize -> couche contacts -> push. AUCUN appel a Hektor.

    ⚠ C-6, 23/09/2026 -- TROIS ETAPES, DEUX LANGUES. `normalize_source` travaille
      sur le MIROIR : il lui faut le numero de Hektor. Le push travaille sur
      NOTRE couche : il lui faut l'identite. Une seule liste servait aux deux,
      ce qui etait juste tant que les deux numeros etaient egaux.
      `build_contacts_layer` accepte les deux (il traduit dans les deux sens,
      cf. refresh_contact_slice) ; on lui donne l'identite, qui est sa langue.
    """
    csv_hektor = ",".join(ids)
    identites = identites_pour_ces_cibles(db_path, ids)
    csv_app = ",".join(identites)
    run_step(["normalize_source.py", "--contact-id", csv_hektor])
    run_step(["phase2/contacts/build_contacts_layer.py", "--contact-id", csv_app, "--no-reports"])
    # --include-archived-searches (21/08/2026) : SANS cette option, ce run considererait
    # les recherches archivees deja poussees comme "disparues" et les supprimerait de
    # Supabase -- defaisant chaque nuit ce que le run de 05:30 vient d'ecrire.
    run_step([
        "phase2/sync/push_contacts_to_supabase.py", "--contact-id", csv_app,
        "--push-mode", "full", "--contacts-scope", "active_or_eligible", "--skip-stats",
        "--include-archived-searches",
    ])


def ceder_au_verrou(attente_max: float) -> float:
    """Attend que le verrou des traitements lourds retombe. Retourne les secondes cedees.

    Un arret force ne relache PAS le fichier temoin (l'autre session l'a verifie), donc on
    ne peut pas attendre indefiniment : passe le plafond, on repart en le disant. Ce n'est
    plus fatal depuis que les connexions phase2 portent busy_timeout=30000.
    """
    if not VERROU_LOURD.exists():
        return 0.0
    debut = time.time()
    try:
        age = int(time.time() - VERROU_LOURD.stat().st_mtime)
    except OSError:
        age = -1
    print(
        f"[recherches-actives] VERROU : un traitement lourd tient {VERROU_LOURD.name}"
        f" (pose il y a {age}s) -- on cede la place et on attend"
    )
    while VERROU_LOURD.exists():
        if time.time() - debut >= attente_max:
            print(
                f"[recherches-actives] VERROU : toujours la apres {int(attente_max)}s"
                " -- verrou probablement residuel (un arret force ne le relache pas)."
                " On repart quand meme."
            )
            return time.time() - debut
        time.sleep(5.0)
    time.sleep(VERROU_MARGE_S)  # l'etape 2 reprend le verrou juste apres l'etape 1
    cede = time.time() - debut
    print(f"[recherches-actives] VERROU : relache, on reprend apres {int(cede)}s cedees")
    return cede


def conseil_reprise(dernier_id_sur: str, descending: bool = False) -> str:
    """Le conseil de reprise, par IDENTIFIANT et jamais par position."""
    if not dernier_id_sur:
        return "Reprise : aucun lot complet, tout reprendre depuis le debut."
    option = "--start-before-id" if descending else "--start-after-id"
    return f"Reprise : {option} {dernier_id_sur}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run recherches actives : refresh Hektor des contacts a recherche active, sans filtre date_maj."
    )
    parser.add_argument("--batch-size", type=int, default=300, help="Contacts par lot (defaut 300).")
    parser.add_argument("--limit", type=int, default=0, help="Nombre max de contacts a traiter. 0 = tous.")
    parser.add_argument(
        "--start-after-id", type=int, default=0,
        help="REPRISE RECOMMANDEE : ne traite que les contacts dont l'id est STRICTEMENT "
             "superieur a N. Un identifiant ne bouge pas, contrairement a une position : "
             "la liste des acquereurs a perdu 67 entrees en 5 h le 22/08. Prendre l'id du "
             "dernier contact reellement reconstruit et pousse, que le run affiche en sortant.",
    )
    parser.add_argument(
        "--descending", action="store_true",
        help="Parcourir des identifiants les PLUS GRANDS aux plus petits, donc du contact "
             "le plus recent au plus ancien. C'est l'ordre de la methode de reference "
             "(backfill_contact_missing.ps1 : « RECENTS d'abord »), et c'est la ou vivent "
             "les recherches : 12,7 %% des acquereurs de la derniere tranche d'ids en "
             "portent une, contre 0 %% dans la tranche 433 737-453 638.",
    )
    parser.add_argument(
        "--start-before-id", type=int, default=0,
        help="Reprise en parcours DECROISSANT : ne traite que les contacts d'id "
             "STRICTEMENT INFERIEUR a N. Pendant du --start-after-id du parcours croissant.",
    )
    parser.add_argument(
        "--start-at", type=int, default=0,
        help="Reprise : ignore les N premiers contacts de la liste (ordre stable, id croissant). "
             "0 = depuis le debut. Sert a relancer un rattrapage interrompu sans refaire "
             "ce qui est deja passe.",
    )
    parser.add_argument("--phase2-db", type=Path, default=PHASE2_DB)
    parser.add_argument("--hektor-db", type=Path, default=HEKTOR_DB)
    parser.add_argument(
        "--scope", choices=("actives", "acquereurs"), default="actives",
        help="actives = contacts a recherche active connue (defaut, run de 03:00). "
             "acquereurs = TOUS les contacts de typologie acquereur (rattrapage).",
    )
    parser.add_argument(
        "--pause-between-batches", type=float, default=0.0,
        help="Pause en secondes entre deux lots. 0 = aucune (defaut). Mettre 20 sur un "
             "rattrapage long : tenir 6 appels/s pendant des heures est la forme qui a "
             "fait bannir notre IP au rattrapage des documents.",
    )
    parser.add_argument(
        "--max-consecutive-failed-batches", type=int, default=3,
        help="Coupe-circuit : abandonne le run apres N lots consecutifs en echec "
             "(defaut 3, 0 = desactive). Sans lui, un bannissement d'IP au lot 12 "
             "laisse le run taper 226 lots de plus sur une porte fermee.",
    )
    # Valeurs de la METHODE DE REFERENCE, documentee dans
    # notice/NOTE_EXTRACTION_CHAUFFAGE_HEKTOR_2026-06-09.md et reprise telle quelle par
    # scheduled/backfill_contact_missing.ps1 : 2 000 par vague, 100 par lot, 0,5 s entre
    # deux fiches, 60 s entre deux lots, 300 s entre deux vagues. C'est le seul regime dont
    # on ait la preuve ecrite qu'il a fait passer des dizaines de milliers d'elements sans
    # jamais rien declencher -- la note l'estime a ~24 h pour 50 000.
    # Ce qui compte n'est pas la vitesse instantanee mais le TAUX D'OCCUPATION : des lots de
    # 100 suivis de 60 s de pause ne sollicitent Hektor que 45 % du temps ; des lots de
    # 1 000, 83 %. Les compteurs de pare-feu travaillent sur des fenetres glissantes.
    parser.add_argument(
        "--fetch-batch-size", type=int, default=100,
        help="Taille des lots DANS la lecture Hektor (defaut 100, methode de reference).",
    )
    parser.add_argument(
        "--fetch-batch-pause-seconds", type=float, default=60.0,
        help="Pause entre deux lots de lecture (defaut 60 s, methode de reference).",
    )
    parser.add_argument(
        "--batches-per-wave", type=int, default=0,
        help="Travailler par VAGUES de N lots, avec --pause-between-batches entre deux "
             "vagues au lieu d'entre chaque lot. 0 = comportement historique (pause apres "
             "chaque lot). Une vague de 4 lots = 1 200 fiches, puis une vraie respiration.",
    )
    parser.add_argument(
        "--request-delay-seconds", type=float, default=0.5,
        help="Delai entre deux fiches DANS un lot (defaut 0,5 s, methode de reference). "
             "0 = pleine vitesse, ce qui produit des pointes a ~9 appels/s.",
    )
    parser.add_argument(
        "--attente-verrou-max", type=float, default=1800.0,
        help="Plafond d'attente quand un traitement lourd (descente, releve des doublures) "
             "tient pull_from_supabase.lock. Au-dela on repart quand meme : un arret force "
             "ne relache pas le verrou. 0 = ne jamais ceder.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Affiche le volume sans fetch.")
    parser.add_argument(
        "--sans-carnet-acquereur", action="store_true",
        help="INTERRUPTEUR (20/09/2026) : ne pas traiter les contacts qui viennent de "
             "devenir acquereurs. Le run redevient alors exactement celui d'avant.",
    )
    parser.add_argument(
        "--carnet-seul", action="store_true",
        help="Ne traiter QUE les contacts devenus acquereurs (le carnet), sans la passe "
             "habituelle. C'est la forme utilisee en fin de run quotidien : quelques fiches, "
             "pour que la recherche creee dans Hektor entre le matin meme au lieu du "
             "lendemain 03:00. Sans carnet a traiter, le script sort immediatement.",
    )
    parser.add_argument(
        "--max-carnet-acquereur", type=int, default=500,
        help="Plafond de fiches du carnet par passage (defaut 500). Le reste attend la "
             "nuit suivante : le carnet ne perd rien.",
    )
    args = parser.parse_args()

    if args.carnet_seul:
        ids = []
        libelle = "contacts devenus acquereurs (carnet seul)"
    elif args.scope == "acquereurs":
        ids = acquereur_contact_ids(args.hektor_db)
        libelle = "acquereurs (typologie Hektor)"
    else:
        ids = active_search_contact_ids(args.phase2_db)
        libelle = "contacts a recherche active"
    if args.descending:
        ids = list(reversed(ids))
    # LE CARNET D'ABORD (20/09/2026). Ces fiches-la sont la raison d'etre du
    # correctif : une recherche vient d'y naitre chez Hektor. Elles passent en
    # tete pour etre lues meme si le run s'arrete plus tard -- et elles suivent
    # EXACTEMENT le meme chemin que les autres : meme cadence, meme session, meme
    # coupe-circuit. Aucune requete supplementaire n'est inventee ici.
    ids_carnet: list[str] = []
    if not args.sans_carnet_acquereur:
        ids_carnet = carnet_acquereur_ids(args.hektor_db, args.max_carnet_acquereur)
        # Un contact du carnet PEUT deja etre dans la liste habituelle -- c'est le
        # cas des qualifications d'acquereur, ou l'app a cree la recherche et ou
        # Hektor a pose la typologie dans la foulee. On ne le lit pas deux fois,
        # mais on le marque quand meme traite : sinon il resterait au carnet
        # indefiniment (defaut trouve a l'essai du 20/09).
        deja = set(ids)
        a_ajouter = [c for c in ids_carnet if c not in deja]
        if ids_carnet:
            print(
                f"[recherches-actives] carnet : {len(ids_carnet)} contact(s) devenu(s) acquereur"
                f" -- {len(a_ajouter)} lu(s) en tete, {len(ids_carnet) - len(a_ajouter)} deja dans la liste"
            )
        if a_ajouter:
            ids = a_ajouter + ids
    population = len(ids)
    if args.start_before_id and args.start_before_id > 0:
        avant = len(ids)
        ids = [c for c in ids if int(c) < args.start_before_id]
        print(
            f"[recherches-actives] reprise avant l'id {args.start_before_id} : "
            f"{avant - len(ids)} contacts deja faits ecartes, {len(ids)} restants"
        )
    if args.start_after_id and args.start_after_id > 0:
        avant = len(ids)
        ids = [c for c in ids if int(c) > args.start_after_id]
        print(
            f"[recherches-actives] reprise apres l'id {args.start_after_id} : "
            f"{avant - len(ids)} contacts deja faits ecartes, {len(ids)} restants"
        )
    skipped = 0
    if args.start_at and args.start_at > 0:
        # L'ordre de la liste est stable (id croissant), donc un index vaut reprise.
        skipped = min(args.start_at, population)
        ids = ids[skipped:]
    if args.limit and args.limit > 0:
        ids = ids[: args.limit]
    total = len(ids)
    if skipped:
        print(
            f"[recherches-actives] {population} {libelle} au total -- {skipped} ignore(s) "
            f"(--start-at {args.start_at}), {total} a traiter"
        )
    elif total != population:
        print(f"[recherches-actives] {population} {libelle} au total, {total} a traiter")
    else:
        print(f"[recherches-actives] {total} {libelle}")
    if args.dry_run:
        print("[recherches-actives] dry-run : aucun fetch")
        return 0
    if total == 0:
        return 0

    start = time.time()
    # Repere de debut, pour ne marquer traitees que les fiches du carnet dont la
    # lecture a EU LIEU pendant ce run (et pas une lecture d'hier).
    debut_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    done = 0
    failed_batches = 0
    consecutive_failed = 0
    cede_total = 0.0
    # Point de reprise SUR : le dernier id d'un lot reussi tant qu'AUCUN lot n'a echoue
    # avant lui. Des le premier echec on cesse de l'avancer, sinon on annoncerait une
    # reprise qui enjambe le lot mort -- le defaut du compteur `done`, qui additionne les
    # lots reussis ET rates (900 contacts perdus le 22/08 au matin, 967 l'apres-midi).
    dernier_id_sur = ""
    echec_rencontre = False
    etapes_en_echec: list[str] = []
    aborted = False
    # LECTURE : un seul processus, une seule authentification, pour toute la session.
    if args.attente_verrou_max > 0:
        cede_total += ceder_au_verrou(args.attente_verrou_max)
    print(
        f"[recherches-actives] lecture Hektor : {total} fiches en UNE session "
        f"(lots de {args.fetch_batch_size}, pause {int(args.fetch_batch_pause_seconds)}s, "
        f"delai {args.request_delay_seconds}s) -- 1 authentification"
    )
    try:
        fetch_all(ids, request_delay_seconds=args.request_delay_seconds,
                  batch_size=args.fetch_batch_size,
                  batch_pause_seconds=args.fetch_batch_pause_seconds)
    except Exception as exc:  # noqa: BLE001
        print(f"[recherches-actives] LECTURE HEKTOR EN ECHEC : {exc}")
        print(f"[recherches-actives] {conseil_reprise('', args.descending)}")
        return 2
    print(f"[recherches-actives] lecture terminee ({round(time.time() - start)}s) -- etapes locales")

    for i in range(0, total, max(args.batch_size, 1)):
        batch = ids[i : i + max(args.batch_size, 1)]
        # Robustesse : une tranche locale en echec ne doit PAS arreter tout le run.
        try:
            process_local(batch, args.phase2_db)
            consecutive_failed = 0
            etapes_en_echec = []
            if not echec_rencontre:
                dernier_id_sur = batch[-1]
        except Exception as exc:  # noqa: BLE001
            failed_batches += 1
            consecutive_failed += 1
            echec_rencontre = True
            etapes_en_echec.append(getattr(exc, "script", "?"))
            print(f"[recherches-actives] LOT EN ECHEC (contacts {i}-{i + len(batch)}): {exc} -- on continue")
        done += len(batch)
        print(f"[recherches-actives] {done}/{total} ({round(time.time() - start)}s)")
        # Coupe-circuit (21/08/2026). Des lots qui echouent EN CHAINE ne sont plus un
        # hoquet : c'est la signature d'un bannissement d'IP ou d'une session Hektor
        # morte. Continuer, c'est marteler une porte fermee pendant des heures --
        # exactement ce qui a aggrave le rattrapage des documents. On sort ici : le run
        # est reprenable, et il faut verifier depuis une AUTRE IP avant de conclure a
        # une panne Hektor.
        if args.max_consecutive_failed_batches > 0 and consecutive_failed >= args.max_consecutive_failed_batches:
            aborted = True
            # Nommer le vrai coupable. Le 22/08 ce message accusait un bannissement d'IP
            # alors que Hektor repondait parfaitement et que la panne etait un verrou
            # SQLite local : chercher au mauvais endroit coute plus cher que l'arret.
            reseau = [e for e in etapes_en_echec if etape_est_reseau(e)]
            locales = [e for e in etapes_en_echec if not etape_est_reseau(e)]
            if reseau and not locales:
                cause = (
                    "Echec RESEAU (sync_contact_details) : Hektor n'a pas repondu."
                    " Suspecter un bannissement d'IP ou une session morte ; verifier depuis"
                    " une AUTRE IP avant de relancer."
                )
            elif locales and not reseau:
                noms = ", ".join(sorted({Path(e).name for e in locales}))
                cause = (
                    f"Echec LOCAL a l'etape {noms} : les fetchs Hektor sont passes, ce n'est"
                    " PAS un bannissement. Lire la trace ci-dessus (verrou SQLite tenu par un"
                    " autre traitement, disque, schema) ; inutile de changer d'IP."
                )
            else:
                cause = (
                    "Echecs MIXTES reseau et local : lire les traces ci-dessus avant de"
                    " conclure, les deux causes sont presentes."
                )
            print(
                f"[recherches-actives] COUPE-CIRCUIT : {consecutive_failed} lots consecutifs en echec"
                f" -- run ABANDONNE a {done}/{total} ({round(time.time() - start)}s). {cause}"
                f" {conseil_reprise(dernier_id_sur, args.descending)}"
            )
            break
        # Pause de fin de VAGUE (23/08/2026). Le delai par fiche aplatit le profil DANS un
        # lot, mais ne cree aucune respiration : le run enchainait 17 lots sans jamais
        # s'arreter. Une vague de N lots suivie d'une vraie pause donne au compteur
        # glissant d'en face le temps de redescendre.
        no_lot = i // max(args.batch_size, 1) + 1
        fin_de_vague = args.batches_per_wave <= 0 or no_lot % args.batches_per_wave == 0
        if args.pause_between_batches > 0 and fin_de_vague and done < total:
            if args.batches_per_wave > 0:
                print(
                    f"[recherches-actives] fin de vague ({args.batches_per_wave} lots) "
                    f"-- pause de {int(args.pause_between_batches)}s"
                )
            time.sleep(args.pause_between_batches)
    if ids_carnet:
        # On marque APRES les etapes locales : une fiche n'est « traitee » que si
        # son detail a vraiment ete relu. Ce qui a echoue revient demain.
        marques = marquer_carnet_traite(args.hektor_db, ids_carnet, debut_utc)
        print(
            f"[recherches-actives] carnet : {marques}/{len(ids_carnet)} fiche(s) marquee(s) traitee(s)"
            + ("" if marques == len(ids_carnet) else " -- le reste sera repris au prochain passage")
        )
    if cede_total > 0:
        print(f"[recherches-actives] {int(cede_total)}s cedees au total a un traitement lourd")
    if aborted:
        return 2  # 2 = abandon coupe-circuit (a distinguer de 1 = echecs partiels)
    if failed_batches:
        print(
            f"[recherches-actives] TERMINE AVEC {failed_batches} lot(s) en echec sur "
            f"{((total - 1) // max(args.batch_size, 1)) + 1} -- {done} contacts traites en "
            f"{round(time.time() - start)}s. {conseil_reprise(dernier_id_sur, args.descending)}"
        )
        return 1  # code non nul -> la tache planifiee signale l'echec partiel
    # Afficher le point de reprise MEME quand tout s'est bien passe : la passe complete se
    # fait desormais en sessions courtes (--limit), pour rester loin du volume qui a fait
    # bannir notre IP le 22/08 (25 800 fiches en 1 h 47). Sans cette ligne il faudrait
    # repecher l'identifiant dans le journal a chaque session.
    fin_de_liste = not (args.limit and args.limit > 0 and total >= args.limit)
    suite = (
        "liste terminee, rien ne reste apres cet id."
        if fin_de_liste
        else f"session suivante : {'--start-before-id' if args.descending else '--start-after-id'} {dernier_id_sur}"
    )
    print(
        f"[recherches-actives] termine OK : {done} contacts en {round(time.time() - start)}s"
        f" -- dernier id traite {dernier_id_sur or '(aucun)'} ; {suite}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
