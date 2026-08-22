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
import sqlite3
import subprocess
import sys
import time
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
    """IDs des contacts ayant >=1 recherche active (couche locale phase2)."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT DISTINCT hektor_contact_id FROM app_contact_search_current "
            "WHERE is_active = 1 AND (archive IS NULL OR archive = 0) "
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


def process_batch(ids: list[str]) -> None:
    csv = ",".join(ids)
    # 1) fetch ContactById (sans date_maj : --contact-id court-circuite la sélection)
    run_step([
        "phase2/sync/sync_contact_details.py", "--contact-id", csv,
        "--skip-listing-refresh", "--limit", "0", "--request-delay-seconds", "0",
        "--batch-size", str(len(ids)), "--batch-pause-seconds", "0",
        "--max-consecutive-hard-errors", "3", "--no-normalize",
    ])
    # 2) normalize -> 3) build couche contacts -> 4) push (saute les dirty via C)
    run_step(["normalize_source.py", "--contact-id", csv])
    run_step(["phase2/contacts/build_contacts_layer.py", "--contact-id", csv, "--no-reports"])
    # --include-archived-searches (21/08/2026) : SANS cette option, ce run considererait
    # les recherches archivees deja poussees comme "disparues" et les supprimerait de
    # Supabase -- defaisant chaque nuit ce que le run de 05:30 vient d'ecrire.
    run_step([
        "phase2/sync/push_contacts_to_supabase.py", "--contact-id", csv,
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


def conseil_reprise(dernier_id_sur: str) -> str:
    """Le conseil de reprise, par IDENTIFIANT et jamais par position."""
    if not dernier_id_sur:
        return "Reprise : aucun lot complet, tout reprendre depuis le debut."
    return f"Reprise : --start-after-id {dernier_id_sur}"


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
    parser.add_argument(
        "--attente-verrou-max", type=float, default=1800.0,
        help="Plafond d'attente quand un traitement lourd (descente, releve des doublures) "
             "tient pull_from_supabase.lock. Au-dela on repart quand meme : un arret force "
             "ne relache pas le verrou. 0 = ne jamais ceder.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Affiche le volume sans fetch.")
    args = parser.parse_args()

    if args.scope == "acquereurs":
        ids = acquereur_contact_ids(args.hektor_db)
        libelle = "acquereurs (typologie Hektor)"
    else:
        ids = active_search_contact_ids(args.phase2_db)
        libelle = "contacts a recherche active"
    population = len(ids)
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
    for i in range(0, total, max(args.batch_size, 1)):
        batch = ids[i : i + max(args.batch_size, 1)]
        if args.attente_verrou_max > 0:
            cede_total += ceder_au_verrou(args.attente_verrou_max)
        # Robustesse : un lot en échec (hoquet Hektor/réseau) ne doit PAS arrêter
        # tout le run — on log et on continue avec les lots suivants.
        try:
            process_batch(batch)
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
                f" {conseil_reprise(dernier_id_sur)}"
            )
            break
        if args.pause_between_batches > 0 and done < total:
            time.sleep(args.pause_between_batches)
    if cede_total > 0:
        print(f"[recherches-actives] {int(cede_total)}s cedees au total a un traitement lourd")
    if aborted:
        return 2  # 2 = abandon coupe-circuit (a distinguer de 1 = echecs partiels)
    if failed_batches:
        print(
            f"[recherches-actives] TERMINE AVEC {failed_batches} lot(s) en echec sur "
            f"{((total - 1) // max(args.batch_size, 1)) + 1} -- {done} contacts traites en "
            f"{round(time.time() - start)}s. {conseil_reprise(dernier_id_sur)}"
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
        else f"session suivante : --start-after-id {dernier_id_sur}"
    )
    print(
        f"[recherches-actives] termine OK : {done} contacts en {round(time.time() - start)}s"
        f" -- dernier id traite {dernier_id_sur or '(aucun)'} ; {suite}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
