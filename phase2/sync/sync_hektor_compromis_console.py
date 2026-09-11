# -*- coding: utf-8 -*-
"""LE RATTRAPAGE DES COMPROMIS PAR LA CONSOLE                      10/09/2026

CE QU'IL FAIT. Il va chercher, compromis par compromis, ce que l'API de Hektor
ne rend JAMAIS -- au premier rang le NOTAIRE, absent de 10 586 charges sur
10 586 -- et le range dans `app_affaire_console`, la table qu'aucun run ne
touche.

⚠ IL N'ECRIT RIEN CHEZ HEKTOR. L'extracteur qu'il pilote n'envoie que
  l'ouverture de l'assistant ; l'enregistrement, chez Hektor, est la requete qui
  porte `actionContainer[] = save + treat`, et ces deux mots n'existent pas dans
  son code. La tache 0.3 l'a mesure en contre-temoin : « ouvrir/fermer sans
  enregistrer -> AUCUN mouvement » de la date du bien.

POURQUOI LA CONSOLE, ET PAS L'API. Audit du 10/09, trois murs mesures :
  1. l'API n'accepte AUCUN filtre par annonce sur les transactions
     (« idAnnonce et id_annonce sont ignores, teste ») ;
  2. les transactions ne portent AUCUNE date de modification ;
  3. le detail de l'annonce n'en contient AUCUNE -- verifie sur la charge reelle
     de 24933 : 20 cles, pas une transaction.
Le formulaire de l'assistant, lui, porte tout. Il est la seule porte.

LA CADENCE EST CELLE DU RUN CHAUFFAGE, et c'est deliberé : 56 926 lectures sans
un seul bannissement. Le rattrapage des DOCUMENTS, lui, a fait bannir notre IP
par le debit et des 403 repetes. On ne s'ecarte pas de ce qui a tenu.

    debit mesure       2 300 lectures/heure
    10 586 compromis   4 h 36 a 5 h 53 selon le poids du formulaire

L'ORDRE DES PALIERS, et il n'est pas negociable :
    1 compromis   la lecture est-elle juste ?
    50            le parsage tient-il sur des anciens ?
    2023+ (1 588) la cadence tient-elle ? ~45 min
    le reste      de nuit

    python phase2/sync/sync_hektor_compromis_console.py --dry-run
    python phase2/sync/sync_hektor_compromis_console.py --limit 1
    python phase2/sync/sync_hektor_compromis_console.py --depuis 2023-01-01
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

RACINE = Path(__file__).resolve().parents[2]
PHASE2_DB = RACINE / "phase2" / "phase2.sqlite"
ENV_RACINE = RACINE / ".env"
ENV_APP = RACINE / "apps" / "hektor-v1" / ".env"
SESSION = RACINE / "Console" / "sessions" / "storage_state_admin.json"
EXTRACTEUR = RACINE / "Console" / "extract_hektor_compromis_console.js"
LOGIN = RACINE / "Console" / "playwright_login.js"
TABLE = "app_affaire_console"
# Le miroir porte la date de derniere modification du BIEN -- le signal de la
# tache 0.3, seul mouvement fiable quand une transaction change chez Hektor.
MIROIR = RACINE / "data" / "hektor.sqlite"


def charger_env(chemin: Path, prefixe: str = "") -> None:
    """Charge un .env dans l'environnement, sans jamais ecraser ce qui existe.

    `prefixe` restreint aux cles qui commencent par lui. Voir charger_porte_web.
    """
    if not chemin.exists():
        return
    for ligne in chemin.read_text(encoding="utf-8", errors="ignore").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, valeur = ligne.split("=", 1)
        cle = cle.strip()
        if prefixe and not cle.startswith(prefixe):
            continue
        if cle and cle not in os.environ:
            os.environ[cle] = valeur.strip().strip('"').strip("'")


def charger_porte_web() -> None:
    """Les adresses HEKTOR_* viennent de Console/.env, et EN PREMIER.

    ⚠ POURQUOI, mesure du 11/09. Ce pilote passe son environnement entier au
      sous-processus node (`env = dict(os.environ)`), et dotenv n'ecrase jamais
      une variable deja posee. En chargeant d'abord le .env de la RACINE, il
      imposait donc au node l'adresse de la porte API -- l'ancien domaine --
      alors que node aurait pris celle de Console/.env. Resultat : « Hektor 403
      sur l'ouverture » des la premiere lecture, sur une session pourtant valide.

    ⚠ SEULEMENT LE PREFIXE HEKTOR_ : ce fichier porte aussi des secrets et des
      reglages propres au worker, qui n'ont rien a faire ici. On prend l'adresse
      de la porte web, rien d'autre.
    """
    charger_env(RACINE / "Console" / ".env", prefixe="HEKTOR_")


def maintenant() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ─────────────────────────────────────────────────────────────── Supabase
def _supabase() -> tuple[str, str]:
    url = (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "").strip()
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not cle:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY requis")
    return url.rstrip("/"), cle


def supabase_get(chemin: str, requete: dict[str, str]) -> Any:
    url, cle = _supabase()
    adresse = f"{url}/rest/v1/{chemin.lstrip('/')}"
    if requete:
        adresse = f"{adresse}?{urllib.parse.urlencode(requete)}"
    req = urllib.request.Request(adresse, headers={
        "apikey": cle, "Authorization": f"Bearer {cle}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as rep:
            brut = rep.read().decode("utf-8")
            return json.loads(brut) if brut else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase {exc.code} sur {chemin} : {detail}") from exc


def supabase_upsert(lignes: list[dict[str, Any]]) -> None:
    if not lignes:
        return
    url, cle = _supabase()
    corps = json.dumps(lignes).encode("utf-8")
    req = urllib.request.Request(f"{url}/rest/v1/{TABLE}", data=corps, method="POST", headers={
        "apikey": cle, "Authorization": f"Bearer {cle}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal"})
    try:
        with urllib.request.urlopen(req, timeout=60) as rep:
            rep.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase upsert {exc.code} : {detail}") from exc


def aucun_travail_console_en_cours() -> None:
    """Meme garde-fou que le run chauffage : on ne lit pas pendant qu'on ecrit.

    Sans elle, notre ouverture pourrait croiser celle d'un worker en train de
    modifier la meme transaction -- et on lirait un etat de transition.
    """
    lignes = supabase_get("app_console_job", {
        "select": "id,job_type,status", "status": "in.(pending,running)", "limit": "20"})
    if isinstance(lignes, list) and lignes:
        raise RuntimeError(f"Travaux console en cours : {json.dumps(lignes)}")


# ─────────────────────────────────────────────────────────── le choix des cibles
def cibles(args: argparse.Namespace) -> list[dict[str, Any]]:
    """Les compromis a lire, pris dans le registre LOCAL.

    On lit le registre et pas le miroir : c'est lui qui porte `app_affaire_id`,
    la cle de la table d'arrivee. Le numero de Hektor ne suffirait pas -- il
    n'est unique que dans son type (7 541 numeros portes par deux types).
    """
    con = sqlite3.connect(f"file:{PHASE2_DB.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        # ⚠ LES COMPROMIS ANNULES SONT ECARTES, ET CE N'EST PAS UN CHOIX :
        #   Hektor REFUSE de les ouvrir. Mesure du 10/09, palier de 50 : les
        #   deux seuls echecs (50048 et 50008) sont les deux seuls `cancelled`
        #   du lot -- l'ouverture rend une reponse sans `stepContent`. Le
        #   message de Hektor est connu depuis le 03/09 : « un compromis
        #   cloture ne peut pas etre modifie ».
        #   Leur notaire restera donc inconnu. Ils sont 1 373 sur 10 586, tous
        #   termines : c'est de l'histoire, pas de la donnee vivante.
        ou = ["kind = 'compromis'", "present_in_hektor = 1",
              "COALESCE(state, '') NOT IN ('cancelled', 'annule')",
              "hektor_affaire_id IS NOT NULL", "hektor_annonce_id IS NOT NULL"]
        params: list[Any] = []
        if args.compromis:
            ou.append("hektor_affaire_id IN (%s)" % ",".join("?" for _ in args.compromis))
            params.extend(args.compromis)
        elif args.depuis:
            ou.append("date >= ?")
            params.append(args.depuis)
        sql = ("SELECT app_affaire_id, hektor_annonce_id, hektor_affaire_id, date "
               f"FROM app_affaire_ledger WHERE {' AND '.join(ou)} "
               "ORDER BY date DESC, app_affaire_id DESC")
        return [dict(r) for r in con.execute(sql, tuple(params))]
    finally:
        con.close()


def dates_annonces() -> dict[str, str]:
    """La date de derniere modification de CHAQUE bien, prise au miroir.

    ⚠ C'EST LE SIGNAL ETABLI PAR LA TACHE 0.3, et il a ete mesure, pas suppose :
      « seul l'ENREGISTREMENT la deplace ». Quatre positifs et quatre
      contre-temoins le 03/09 -- elle ne derive pas seule, la LECTURE ne la
      touche pas, ouvrir l'assistant et fermer SANS enregistrer ne la touche pas.
      C'est donc la bonne facon de savoir qu'une transaction a bouge chez Hektor.

    ⚠ ET LE SIGNAL EST LARGE : la date du bien bouge aussi pour une photo ou un
      prix. Il se trompe DU BON COTE -- on relira parfois pour rien, jamais on ne
      laissera passer une transaction modifiee.

    ⚠ PAS `app_dossier_current.source_updated_at` : mesure du 11/09, elle porte
      la date d'ENREGISTREMENT du bien (2018 pour l'annonce 24933), pas celle de
      sa derniere modification. Se tromper de colonne, c'est ne relire jamais.
    """
    if not MIROIR.exists():
        return {}
    con = sqlite3.connect(f"file:{MIROIR.as_posix()}?mode=ro", uri=True)
    try:
        return {str(a): str(d or "") for a, d in
                con.execute("SELECT hektor_annonce_id, date_maj FROM hektor_annonce")}
    finally:
        con.close()


def _instant(texte: str):
    """Une date Hektor ou ISO, ramenee a un instant comparable. None si illisible."""
    t = str(texte or "").strip().replace("Z", "+00:00").replace(" ", "T")
    if not t:
        return None
    try:
        v = datetime.fromisoformat(t)
    except ValueError:
        return None
    return v if v.tzinfo else v.replace(tzinfo=timezone.utc)


def deja_lues(stale_jours: int, suivre_annonce: bool = False) -> set[int]:
    """Ce que la table porte deja et qu'il est inutile de relire.

    ⚠ ON NE SAUTE PAS CE QUE LE WORKER A ECRIT. Sa lecture est la plus fraiche
      qui soit -- elle date du geste de l'utilisateur.

    `suivre_annonce` est le mode ENTRETIEN : on ne relit plus par rotation, on
    relit CE QUI A BOUGE. Une fiche est reprise si la date de son bien est
    posterieure a notre lecture. Mesure du 11/09 sur les 9 216 compromis lus :
    UN SEUL etait a relire. L'entretien coute donc quelques secondes par nuit,
    la ou une rotation a 90 jours en demandait cent par nuit pour rien.

    ⚠ QUAND UNE DES DEUX DATES MANQUE, ON NE RELIT PAS -- 299 cas, des biens que
      le miroir ne porte plus. Relire sans pouvoir comparer, ce serait les
      reprendre CHAQUE nuit sans jamais rien apprendre.
    """
    par_annonce = dates_annonces() if suivre_annonce else {}
    vues: set[int] = set()
    depart = 0
    while True:
        lot = supabase_get(TABLE, {
            "select": "app_affaire_id,hektor_annonce_id,lu_le",
            "order": "app_affaire_id.asc",
            "offset": str(depart), "limit": "1000"})
        if not isinstance(lot, list) or not lot:
            break
        for ligne in lot:
            quand = str(ligne.get("lu_le") or "")
            if suivre_annonce:
                bouge = _instant(par_annonce.get(str(ligne.get("hektor_annonce_id") or ""), ""))
                lue = _instant(quand)
                if bouge and lue and bouge > lue:
                    continue          # le bien a bouge depuis : on la reprend
            if stale_jours > 0 and quand:
                try:
                    age = (datetime.now(timezone.utc)
                           - datetime.fromisoformat(quand.replace("Z", "+00:00"))).days
                    if age > stale_jours:
                        continue
                except ValueError:
                    pass
            vues.add(int(ligne["app_affaire_id"]))
        depart += len(lot)
        if len(lot) < 1000:
            break
    return vues


# ─────────────────────────────────────────────────────────────── l'extracteur
def rafraichir_session(node: str, delai: int) -> None:
    env = dict(os.environ)
    env["CONSOLE_STORAGE_STATE_PATH"] = str(SESSION)
    fait = subprocess.run([node, str(LOGIN)], cwd=str(RACINE / "Console"), env=env,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=delai)
    if fait.returncode != 0:
        raise RuntimeError((fait.stderr or fait.stdout or "login Hektor en echec")[-2000:])


def lire_un_lot(node: str, lot: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    cmd = [node, str(EXTRACTEUR),
           "--storage-state", str(SESSION),
           "--timeout-ms", str(args.timeout_seconds * 1000),
           "--delay-ms", str(int(args.delay_seconds * 1000))]
    for c in lot:
        cmd.extend(["--cible", f"{c['hektor_annonce_id']}:{c['hektor_affaire_id']}"])
    fait = subprocess.run(cmd, cwd=str(RACINE / "Console"), capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=args.timeout_seconds * max(1, len(lot)) + 60)
    texte = (fait.stdout or "").strip()
    charge: dict[str, Any] = {}
    if texte:
        try:
            charge = json.loads(texte)
        except json.JSONDecodeError:
            i = texte.rfind("{")
            if i >= 0:
                charge = json.loads(texte[i:])
    if fait.returncode == 3 or charge.get("status") == "stopped_on_403":
        raise PermissionError(json.dumps(charge)[:2000])
    if fait.returncode == 2 or charge.get("status") == "session_expired":
        raise RuntimeError("Session Hektor expiree")
    if fait.returncode != 0:
        raise RuntimeError(str(charge.get("error") or fait.stderr or "extraction en echec")[:2000])
    return charge


def ligne_pour_supabase(cible: dict[str, Any], resultat: dict[str, Any]) -> dict[str, Any]:
    champs = resultat.get("champs") or {}
    return {
        "app_affaire_id": int(cible["app_affaire_id"]),
        "hektor_annonce_id": int(cible["hektor_annonce_id"]),
        "kind": "compromis",
        "hektor_affaire_id": str(cible["hektor_affaire_id"]),
        "acquereurs": champs.get("acquereurs"),
        "mandants": champs.get("mandants"),
        "notaires_acquereur": champs.get("notaires_acquereur"),
        "notaires_mandant": champs.get("notaires_mandant"),
        "montant_honoraire_entree": champs.get("montant_honoraire_entree"),
        "taux_honoraire_entree": champs.get("taux_honoraire_entree"),
        # ⚠ L'IDENTITE, ET ELLE MANQUAIT -- 0 ligne sur 8 600.
        #
        # Ce convertisseur est anterieur au lecteur d'identite : il ne copiait
        # que les NUMEROS. Resultat mesure le 11/09 : `parties_json` vide sur la
        # totalite du rattrapage, alors que le lecteur avait bel et bien capte
        # les noms que Hektor affiche dans son formulaire.
        #
        # Ces noms ne font pas double emploi avec le miroir : ils viennent de
        # Hektor LUI-MEME, et ils nomment des fiches que la couche contacts ne
        # sait pas nommer -- les notaires (typologie « partenaire »), et les
        # fiches de menage vides (voir 26bis-COUPLES).
        "parties_json": champs.get("parties"),
        # ⚠ NI LES UNITES NI LES CONDITIONS : elles vivent aux etapes 2 et 3,
        #   que cette passe ne parcourt pas. Elles sont donc ABSENTES de cette
        #   ligne -- et c'est sans danger : MESURE DU 10/09 sur une ligne
        #   d'essai, un upsert partiel ne touche PAS aux colonnes qu'il
        #   n'envoie pas. `unites_entree_percent` et `notaires_acquereur`
        #   ecrits par le worker ont survecu a un upsert qui ne portait que
        #   `mandants`. Le rattrapage complete donc le worker, il ne l'ecrase
        #   pas. (Je l'avais d'abord ecrit dans l'autre sens, sans le verifier.)
        "source": "rattrapage",
        "lu_le": resultat.get("lu_le") or maintenant(),
    }


def heure_limite_atteinte(stop_at: str) -> bool:
    """L'heure d'arret est-elle passee ?

    ⚠ POURQUOI CETTE CEINTURE EXISTE. Le run quotidien part a 05:00 et fait, lui
      aussi, de l'extraction CONSOLE (le chauffage). Deux flux console en meme
      temps, c'est le doublement de debit que la methode de reference interdit --
      et c'est ce qui a fait bannir notre IP en juillet.

      Une estimation ne suffit pas : si Hektor repond plus lentement qu'au dernier
      essai, un run parti a 22:00 peut mordre sur 03:00 ou 05:00. Cette ceinture
      rend l'estimation SANS IMPORTANCE.

      Et l'arret ne coute rien : chaque compromis deja lu est saute au
      relancement, donc la reprise repart exactement ou elle s'est arretee.
    """
    if not stop_at:
        return False
    try:
        h, m = (int(x) for x in stop_at.split(":", 1))
    except ValueError:
        return False
    maintenant = datetime.now()
    limite = maintenant.replace(hour=h, minute=m, second=0, microsecond=0)
    # Une heure du matin demandee a 22 h designe le LENDEMAIN.
    if limite < maintenant - timedelta(hours=12):
        limite += timedelta(days=1)
    return maintenant >= limite


def attendre_que_la_voie_soit_libre(maxi_minutes: int) -> str:
    """S'efface tant qu'un travail console tourne.

    Le garde-fou d'origine REFUSE de demarrer si un travail est en cours. C'est
    juste au demarrage, et inutile pendant quatre heures de run : l'utilisateur a
    le droit de se servir de l'app pendant que le rattrapage tourne. Chaque geste
    declenche un worker qui parle a Hektor lui aussi -- alors on lui laisse la
    place, au lieu de tirer en meme temps que lui.
    """
    debut = time.time()
    attendu = 0
    while True:
        try:
            aucun_travail_console_en_cours()
            if attendu:
                print(f"[courtoisie] voie libre apres {attendu} s")
            return ""
        except RuntimeError as exc:
            if "Travaux console en cours" not in str(exc):
                raise
            if time.time() - debut > maxi_minutes * 60:
                return f"travail console toujours en cours apres {maxi_minutes} min"
            if not attendu:
                print("[courtoisie] un travail console tourne -- on s'efface")
            time.sleep(15)
            attendu = int(time.time() - debut)


def par_lots(valeurs: list, taille: int):
    t = max(1, taille)
    for i in range(0, len(valeurs), t):
        yield valeurs[i:i + t]


def arguments() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Rattrapage console des compromis (lecture seule).")
    p.add_argument("--compromis", action="append", default=[],
                   help="Numero Hektor de compromis. Repetable.")
    p.add_argument("--depuis", default="", help="Ne prendre que les compromis a partir de cette date.")
    p.add_argument("--limit", type=int, default=1, help="Nombre maximum. 0 = sans limite.")
    p.add_argument("--stale-days", type=int, default=90,
                   help="Relire ce qui a plus de N jours. 0 = ne jamais relire.")
    p.add_argument("--suivre-annonce", action="store_true",
                   help="ENTRETIEN : relire une fiche quand la date de son BIEN a "
                        "bouge depuis notre lecture, au lieu d'une rotation a l'age.")
    p.add_argument("--force", action="store_true",
                   help="Relire meme ce que la table porte deja. Sert aux paliers d'essai.")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--skip-job-check", action="store_true")
    p.add_argument("--node-exe", default=os.environ.get("CONSOLE_NODE_EXE") or "node.exe")
    p.add_argument("--timeout-seconds", type=int, default=60)
    p.add_argument("--delay-seconds", type=float, default=0.5)
    p.add_argument("--batch-size", type=int, default=100)
    p.add_argument("--batch-pause-seconds", type=int, default=60,
                   help="Respiration entre deux lots. 60 s = methode de reference.")
    p.add_argument("--wave-every", type=int, default=2000,
                   help="Longueur d'une vague. 0 = pas de vague.")
    p.add_argument("--wave-pause-seconds", type=int, default=300,
                   help="Pause entre deux vagues. 300 s = methode de reference.")
    p.add_argument("--refresh-session-on-expired", action="store_true")
    p.add_argument("--stop-at", default="",
                   help="Heure locale HH:MM au-dela de laquelle on s'arrete entre deux lots.")
    p.add_argument("--courtoisie", action="store_true",
                   help="S'effacer tant qu'un travail console tourne, au lieu de refuser.")
    p.add_argument("--courtoisie-max-minutes", type=int, default=30,
                   help="Au-dela, on renonce plutot que d'attendre indefiniment.")
    return p.parse_args()


def main() -> int:
    args = arguments()
    charger_porte_web()          # AVANT la racine : voir charger_porte_web
    charger_env(ENV_RACINE)
    charger_env(ENV_APP)

    toutes = cibles(args)
    resume: dict[str, Any] = {
        "dry_run": args.dry_run,
        "candidates_avant_filtre": len(toutes),
        "lues": [], "erreurs": [],
    }

    vues = set() if (args.dry_run or args.force) else deja_lues(args.stale_days, args.suivre_annonce)
    retenues = [c for c in toutes if int(c["app_affaire_id"]) not in vues]
    if args.limit > 0:
        retenues = retenues[:args.limit]
    resume["deja_lues_sautees"] = len(toutes) - len([c for c in toutes
                                                     if int(c["app_affaire_id"]) not in vues])
    resume["selection"] = len(retenues)
    resume["apercu"] = [f"{c['hektor_annonce_id']}:{c['hektor_affaire_id']}" for c in retenues[:10]]

    if args.dry_run or not retenues:
        print(json.dumps(resume, ensure_ascii=False, indent=2))
        return 0

    if not SESSION.exists():
        raise RuntimeError(f"Session Playwright introuvable : {SESSION}")
    if not args.skip_job_check:
        aucun_travail_console_en_cours()

    depart = time.perf_counter()
    rafraichi = False
    traites = 0
    lots = list(par_lots(retenues, args.batch_size))
    for index, lot in enumerate(lots, start=1):
        # ── LES DEUX CEINTURES, AVANT CHAQUE LOT ──
        if heure_limite_atteinte(args.stop_at):
            resume["arret_horaire"] = (
                f"arret demande a {args.stop_at} -- {index - 1} lot(s) faits, "
                f"le reste sera repris au prochain lancement")
            break
        if args.courtoisie:
            renoncement = attendre_que_la_voie_soit_libre(args.courtoisie_max_minutes)
            if renoncement:
                resume["arret_courtoisie"] = renoncement
                break
        par_numero = {str(c["hektor_affaire_id"]): c for c in lot}
        try:
            charge = lire_un_lot(args.node_exe, lot, args)
        except PermissionError as exc:
            # ⚠ ARRET DUR. Un 403 n'est pas un incident a reessayer : c'est le
            #   debut d'un bannissement. Juillet nous l'a appris.
            resume["stopped_on_403"] = str(exc)[:1000]
            resume["elapsed_ms"] = int((time.perf_counter() - depart) * 1000)
            print(json.dumps(resume, ensure_ascii=False, indent=2))
            return 3
        except RuntimeError as exc:
            if (args.refresh_session_on_expired and not rafraichi
                    and "Session Hektor expiree" in str(exc)):
                rafraichir_session(args.node_exe, args.timeout_seconds)
                rafraichi = True
                charge = lire_un_lot(args.node_exe, lot, args)
            else:
                raise

        lignes = []
        for r in charge.get("resultats") or []:
            cible = par_numero.get(str(r.get("hektor_compromis_id")))
            if not cible:
                continue
            if r.get("status") != "done":
                resume["erreurs"].append({"cible": f"{r.get('hektor_annonce_id')}:"
                                                   f"{r.get('hektor_compromis_id')}",
                                          "status": r.get("status"), "error": r.get("error")})
                continue
            lignes.append(ligne_pour_supabase(cible, r))
            champs = r.get("champs") or {}
            resume["lues"].append({
                "cible": f"{r.get('hektor_annonce_id')}:{r.get('hektor_compromis_id')}",
                "notaires": len(champs.get("notaires_acquereur") or [])
                            + len(champs.get("notaires_mandant") or []),
                "acquereurs": len(champs.get("acquereurs") or []),
                "ms": r.get("elapsed_ms")})
        supabase_upsert(lignes)
        # ─── LA RESPIRATION ET LA VAGUE ───
        #
        # ⚠ CE N'EST PAS LE DEBIT QUI A FAIT BANNIR NOTRE IP, C'EST LA DUREE.
        #   L'en-tete du frein du worker le dit apres coup : « le blocage du
        #   19/08 est survenu apres QUATRE HEURES de flux ininterrompu a
        #   ~1,5 req/s, SANS LA MOINDRE ERREUR -- les compteurs de pare-feu
        #   travaillent sur des fenetres glissantes, donc c'est la DUREE
        #   d'exposition qui a franchi le seuil ». Un rattrapage qui ne s'arrete
        #   jamais finit bloque meme en allant lentement.
        #
        # Valeurs de la methode de reference (NOTE_EXTRACTION_CHAUFFAGE, section
        # rattrapage) : 100 par lot, 60 s entre lots, 300 s entre vagues de
        # 2 000. On ne les invente pas, on les recopie.
        traites += len(lot)
        if index < len(lots):
            if args.wave_every > 0 and traites % args.wave_every < args.batch_size:
                print(f"[vague] {traites} lus -- pause de {args.wave_pause_seconds} s")
                time.sleep(args.wave_pause_seconds)
            elif args.batch_pause_seconds > 0:
                time.sleep(args.batch_pause_seconds)

    resume["elapsed_ms"] = int((time.perf_counter() - depart) * 1000)
    print(json.dumps(resume, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
