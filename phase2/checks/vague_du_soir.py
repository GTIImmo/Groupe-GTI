"""LA VAGUE DU SOIR -- UNE SEULE COMMANDE (procedure C, validee par Frederic le 24/11, son 10e mot).

SON MOT : « ⭐ C VALIDE. [...] ON LANCE DES QUE LA PREPARATION EST VERTE ET QUE J'AI ACCORDE LES QUATRE PIECES. ⛔ GARDE CES
DEUX VERROUS, ILS NE DEPENDENT PAS DE L'HEURE : . la garde de depart « aucun run ni descente ne tourne » -- et verifie aussi
qu'aucune tache planifiee ne croise l'heure que tu choisis ; . le point de non-retour de l'etape 4, compare piece par piece
au rejeu du matin. C'est lui qui protege, pas l'horaire. »

⛔ PAR DEFAUT CETTE COMMANDE EST A BLANC : elle ne touche NI le depot, NI .env, NI la base locale, NI Supabase, NI Hektor.
   Les etapes 1 et 2 se jouent sur des COPIES (le dossier de la scene), l'etape 3 n'est pas jouee, l'etape 4 tourne en
   memoire, et les etapes 5 a 8 sont seulement DITES. Le geste exige `--geste` ET l'empreinte du manifeste accorde.

LES ETAPES (une garde qui refuse -> arret ; avant l'etape 5, l'arret REMET TOUT COMME AVANT : fichier, code, .env) :
  0  LES GARDES DE DEPART -- les pieces du jour et leurs empreintes ; ⛔ AUCUN RUN NI DESCENTE ne tourne (taches ET processus) ;
     ⛔ AUCUNE TACHE PLANIFIEE GTI ne tourne ni ne demarre dans la fenetre ; le fichier des coupes en place est l'ancien ;
     l'interrupteur est eteint ; le code porte encore les deux exclusions ; la pre-garde d'A2 (lecture Supabase) ; aucune
     piece nee dans l'app depuis la preparation ; le registre local est celui de l'image du matin.
  1  LES SAUVEGARDES DATEES -- locales (le fichier des coupes, le module de nuit, .env, les chaines et etiquettes du registre
     local) ; chez Supabase (le registre : chaines et etiquettes ; le compteur et le journal des etiquettes ; la repartition).
  2  LA POSE -- le brouillon devient phase2/sync/detachements_manuels.csv ; 4126 et 21520 sortent d'EXCLUES_DE_LA_REGLE_E
     (par l'arbre de syntaxe, et rien d'autre) ; .env : APP_CHAINAGE_DETACHEMENTS=1 et APP_CHAINAGE_GARDE_G2=0.
  3  LA DOUBLURE DU LEDGER -- pull_from_supabase.py --table app_affaire_ledger (la meme etape que le run).
  4  ⛔ LE POINT DE NON-RETOUR -- LA VRAIE FONCTION (recalculer_les_chaines du module POSE, avec le fichier POSE et les
     interrupteurs POSES) sur une copie EN MEMOIRE du registre local, comparee PIECE PAR PIECE au rejeu exact du matin.
     Au moindre ecart : tout est remis comme avant, et la commande s'arrete. Rien n'a ete pousse.
  5  LE CHAINAGE ET SA POUSSEE -- affaire_ledger.py --refresh --push. ⛔ LE SEUL GESTE IRREVERSIBLE.
  6  LE CONTROLE -- les chaines chez Supabase sont celles du rejeu, piece par piece.
  7  A2 (puis A1 et A3 s'ils sont au manifeste) -- le patch par pieces, ses gardes ; s'il refuse, rien n'est ecrit et on
     s'arrete ; puis sa repetition.
  8  LA REPARTITION -- repartition_commission.py --purger-orphelines --pousser (le verrou et les orphelines, le soir meme).
  9  ARRET -- le compte rendu, ecrit au fil dans le dossier de la scene.

USAGE :
  python -X utf8 phase2/checks/vague_du_soir.py --manifeste M.json                 # A BLANC, etapes 0 a 4 (le defaut)
  python -X utf8 phase2/checks/vague_du_soir.py --manifeste M.json --seulement 0   # une etape (a blanc)
  python -X utf8 phase2/checks/vague_du_soir.py --manifeste M.json --attendu-temoin E.json   # le temoin inverse de l'etape 4
  python -X utf8 phase2/checks/vague_du_soir.py --manifeste M.json --geste --accord <md5 du manifeste>   # ⛔ SUR SON ACCORD
  python -X utf8 phase2/checks/vague_du_soir.py --remettre <dossier de la scene>    # avant l'etape 5 : tout comme avant
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

SYNC = RACINE / "phase2" / "sync"
MODULE = SYNC / "affaire_ledger.py"
FICHIER_DET = SYNC / "detachements_manuels.csv"
FICHIER_RAT = SYNC / "rattachements_manuels.csv"
ENV = RACINE / ".env"
BASE = RACINE / "phase2" / "phase2.sqlite"
PY_RUN = RACINE / ".venv" / "Scripts" / "python.exe"      # le python du run (run_full_pipeline.ps1, l. 166)
SCENES = Path(r"C:\Hektor\chantier_classeur_q6_cache\vague_du_soir")
A_RETIRER = (4126, 21520)
INTERRUPTEURS = {"APP_CHAINAGE_DETACHEMENTS": "1", "APP_CHAINAGE_GARDE_G2": "0"}
# LA FENETRE : la commande entiere dure ~8 min (etapes 0, 1, 2, 4 mesurees le 24/11 a blanc : 3 + 1 + 0 + 164..193 s ; 3, 5
#   et 8 au journal du run : 95 + 139 + 4 s). 20 min = 2,5 fois la duree : aucune tache GTI ne doit tourner ni demarrer
#   dedans. ⚠ « GTI Relances Email » demarre a chaque heure pile (08:00 -> 22:00) et « GTI Health Monitor » aux heures
#   paires a :48 : le creneau sur est donc hh:02 -> hh:25 (sauf si une autre tache le croise -- la garde le dit).
FENETRE_MIN = 20
SCRIPTS_DU_RUN = ("run_full_pipeline", "run_quotidien", "run_descente", "affaire_ledger.py", "pull_from_supabase.py",
                  "repartition_commission.py", "relancer_run")

JOURNAL = None


def dire(s: str = "") -> None:
    print(s, flush=True)
    if JOURNAL is not None:
        with JOURNAL.open("a", encoding="utf-8") as f:
            f.write(s + "\n")


def md5(p: Path) -> str:
    return hashlib.md5(Path(p).read_bytes()).hexdigest()   # les octets TELS QUELS (memoire « md5 et CRLF »)


class Refus(Exception):
    pass


def powershell(cmd: str) -> str:
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    if r.returncode != 0:
        raise Refus("powershell a echoue : %s" % r.stderr.strip()[:300])
    return r.stdout


# ═══════════════════════════════════════════ 0. LES GARDES DE DEPART ═══════════════════════════════════════════════
def taches_gti() -> list[dict]:
    out = powershell(
        "Get-ScheduledTask -TaskName 'GTI*' | ForEach-Object { $i = $_ | Get-ScheduledTaskInfo; "
        "[pscustomobject]@{ nom = $_.TaskName; etat = [string]$_.State; "
        "prochain = $(if ($i.NextRunTime) { $i.NextRunTime.ToString('s') } else { '' }); "
        "dernier = $(if ($i.LastRunTime) { $i.LastRunTime.ToString('s') } else { '' }) } } | ConvertTo-Json")
    d = json.loads(out) if out.strip() else []
    return d if isinstance(d, list) else [d]


def processus_du_run() -> list[str]:
    out = powershell(
        "Get-CimInstance Win32_Process | Where-Object { $_.Name -in @('python.exe','powershell.exe','pwsh.exe') } | "
        "Select-Object ProcessId, Name, CommandLine | ConvertTo-Json")
    d = json.loads(out) if out.strip() else []
    d = d if isinstance(d, list) else [d]
    moi = os.getpid()
    return ["%s %s : %s" % (p["ProcessId"], p["Name"], (p.get("CommandLine") or "")[:160]) for p in d
            if p["ProcessId"] != moi and any(s in (p.get("CommandLine") or "") for s in SCRIPTS_DU_RUN)
            and "vague_du_soir.py" not in (p.get("CommandLine") or "")]


def lire_env(p: Path) -> dict:
    d = {}
    for l_ in p.read_text(encoding="utf-8").splitlines():
        if "=" in l_ and not l_.lstrip().startswith("#"):
            k, v = l_.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def exclusions_e(source: str) -> dict:
    noeud = next(n for n in ast.parse(source).body if isinstance(n, ast.AnnAssign)
                 and getattr(n.target, "id", "") == "EXCLUES_DE_LA_REGLE_E")
    return ast.literal_eval(noeud.value)


def chaines_du_registre(con: sqlite3.Connection) -> dict:
    return {int(a): (int(c) if c is not None else None)
            for a, c in con.execute("select app_affaire_id, app_chaine_id from app_affaire_ledger")}


def etape_0(M: dict, a_blanc: bool) -> list[str]:
    refus = []

    def garde(ok: bool, texte: str):
        dire("   %s %s" % ("✅" if ok else "⛔", texte))
        if not ok:
            refus.append(texte)

    dire("0. LES GARDES DE DEPART")
    # les pieces du jour, avec leurs empreintes
    for nom in ("brouillon", "attendu_E", "a2_patch", "a2_pregarde", "a2_repetition", "a1_patch", "a3_patch",
                "a1_a3_inverse", "commande"):
        if nom not in M and nom in ("a1_patch", "a3_patch", "a1_a3_inverse", "commande"):
            continue
        x = M[nom]
        ok = Path(x["chemin"]).exists() and md5(Path(x["chemin"])) == x["md5"]
        garde(ok, "piece du jour %-14s %s (md5 %s)" % (nom, Path(x["chemin"]).name, x["md5"][:8]))
    # ⛔ aucun run ni descente : les taches ET les processus
    T = taches_gti()
    for t in T:
        if t["nom"] in ("GTI Quotidien", "GTI Descente"):
            garde(t["etat"] != "Running", "%s ne tourne pas (etat %s)" % (t["nom"], t["etat"]))
    pr = processus_du_run()
    garde(not pr, "aucun processus du run (%s)" % ("aucun" if not pr else " ; ".join(pr)[:300]))
    # ⛔ aucune tache planifiee GTI ne tourne, ni ne demarre dans la fenetre
    maintenant = datetime.now()
    fin = maintenant + timedelta(minutes=FENETRE_MIN)
    for t in sorted(T, key=lambda t: t["prochain"] or "9"):
        if t["etat"] == "Disabled":
            continue
        prochain = datetime.fromisoformat(t["prochain"]) if t["prochain"] else None
        tourne = t["etat"] == "Running"
        croise = prochain is not None and maintenant <= prochain <= fin
        garde(not tourne and not croise, "%-32s %-8s prochain %s%s" % (
            t["nom"], t["etat"], t["prochain"] or "-",
            " ⛔ TOURNE" if tourne else (" ⛔ DANS LA FENETRE (%d min)" % FENETRE_MIN if croise else "")))
    # le fichier des coupes en place est l'ancien ; l'interrupteur est eteint ; le code porte encore les deux exclusions
    garde(md5(FICHIER_DET) == M["fichier_en_place_md5"], "le fichier des coupes en place est l'ancien (md5 %s)" %
          md5(FICHIER_DET)[:8])
    e = lire_env(ENV)
    garde(e.get("APP_CHAINAGE_DETACHEMENTS", "0") != "1", "l'interrupteur APP_CHAINAGE_DETACHEMENTS est eteint (%s)" %
          e.get("APP_CHAINAGE_DETACHEMENTS", "absent"))
    ex = exclusions_e(MODULE.read_text(encoding="utf-8"))
    garde(all(k in ex for k in A_RETIRER), "le code porte encore les exclusions %s (%d en tout)" % (A_RETIRER, len(ex)))
    r = subprocess.run(["git", "-C", str(RACINE), "diff", "--quiet", "--", str(MODULE), str(FICHIER_DET)])
    garde(r.returncode == 0, "le module de nuit et le fichier des coupes sont ceux du depot (git diff vide)")
    # le registre local est celui de l'image du matin (la comparaison de l'etape 4 compare ce qui est comparable)
    con = sqlite3.connect("file:%s?mode=ro" % BASE.as_posix(), uri=True)
    ch_loc = chaines_du_registre(con)
    con.close()
    img = sqlite3.connect("file:%s?mode=ro" % (Path(M["image_dossier"]) / "registre.sqlite").as_posix(), uri=True)
    ch_img = chaines_du_registre(img)
    img.close()
    ec = [a for a in set(ch_loc) | set(ch_img) if ch_loc.get(a) != ch_img.get(a)]
    garde(not ec, "le registre local est celui de l'image du matin (%d pieces ; %d ecart(s) %s)" % (
        len(ch_loc), len(ec), sorted(ec)[:10]))
    # chez Supabase, en LECTURE SEULE : aucune piece nee dans l'app depuis la preparation ; la pre-garde d'A2
    import protocole_classeur as P
    cn, cu = P.pooler()
    cu.execute("select app_affaire_id from public.app_affaire_ledger")
    ids_sb = {int(r[0]) for r in cu.fetchall()}
    neuves = sorted(ids_sb - set(ch_loc))
    garde(not neuves, "aucune piece chez Supabase qui ne soit au registre local (%d chez Supabase ; neuves %s)" % (
        len(ids_sb), neuves[:10]))
    cu.execute(Path(M["a2_pregarde"]["chemin"]).read_text(encoding="utf-8"))
    cols = [c.name for c in cu.description]
    vals = cu.fetchone()
    for c_, v_ in zip(cols, vals):
        garde(v_ is True, "pre-garde A2 : %s" % c_)
    # la pre-garde d'A1 et d'A3 : les avis, les notes et les conditions n'ont pas bouge depuis la fabrication (sinon leurs
    #   patchs refuseraient APRES le chainage -- on s'arrete AVANT)
    if "a1a3_empreintes" in M:
        E = M["a1a3_empreintes"]
        cu.execute("select (select md5(coalesce(string_agg(concat_ws('|', id_unique, app_dossier_uuid, app_dossier_numero), "
                   "';' order by id_unique), '')) from public.app_classeur_avis), (select md5(coalesce(string_agg(concat_ws("
                   "'|', app_affaire_id, app_chaine_id), ';' order by app_affaire_id), '')) from public.app_affaire_note), "
                   "(select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, rang, app_chaine_id), ';' order by "
                   "app_affaire_id, rang), '')) from public.app_affaire_condition)")
        for nom_, v_ in zip(("avis", "notes", "conditions"), cu.fetchone()):
            garde(v_ == E[nom_], "pre-garde A1/A3 : les %s n'ont pas bouge depuis la fabrication (%s)" % (nom_, v_[:8]))
    cn.rollback()
    cn.close()
    return refus


# ═══════════════════════════════════════════ 1. LES SAUVEGARDES DATEES ═════════════════════════════════════════════
def sql_sauvegardes(suffixe: str) -> str:
    return """-- vague du soir -- LES SAUVEGARDES DATEES chez Supabase (etape 1). Ne detruit rien.
begin;
create table public.app_affaire_ledger_chaines_avant_vague_%(s)s as
  select app_affaire_id, app_chaine_id, app_dossier_id, app_dossier_uuid, app_dossier_numero, now() as copie_le
    from public.app_affaire_ledger;
create table public.app_dossier_numero_compteur_avant_vague_%(s)s as select * from public.app_dossier_numero_compteur;
create table public.app_dossier_etiquette_journal_avant_vague_%(s)s as select * from public.app_dossier_etiquette_journal;
create table public.app_affaire_repartition_avant_vague_%(s)s as select * from public.app_affaire_repartition;
revoke all on public.app_affaire_ledger_chaines_avant_vague_%(s)s, public.app_dossier_numero_compteur_avant_vague_%(s)s,
  public.app_dossier_etiquette_journal_avant_vague_%(s)s, public.app_affaire_repartition_avant_vague_%(s)s
  from public, anon, authenticated;
do $$
begin
  if (select count(*) from public.app_affaire_ledger_chaines_avant_vague_%(s)s) <> (select count(*) from public.app_affaire_ledger)
     or (select count(*) from public.app_affaire_repartition_avant_vague_%(s)s) <> (select count(*) from public.app_affaire_repartition)
  then raise exception '⛔ sauvegardes incompletes'; end if;
end $$;
commit;
""" % {"s": suffixe}


def etape_1(scene: Path, a_blanc: bool, suffixe: str) -> None:
    dire("1. LES SAUVEGARDES DATEES")
    s = scene / "sauvegardes"
    s.mkdir(parents=True, exist_ok=True)
    for p in (FICHIER_DET, MODULE, ENV):
        shutil.copy2(p, s / p.name)
        dire("   locale : %s (md5 %s)" % (p.name, md5(s / p.name)[:8]))
    con = sqlite3.connect("file:%s?mode=ro" % BASE.as_posix(), uri=True)
    rows = con.execute("select app_affaire_id, app_chaine_id, app_dossier_uuid, app_dossier_numero from app_affaire_ledger")
    with (s / "registre_local_chaines_etiquettes.tsv").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write("\t".join("" if x is None else str(x) for x in r) + "\n")
    con.close()
    dire("   locale : les chaines et etiquettes du registre local -> registre_local_chaines_etiquettes.tsv")
    q = sql_sauvegardes(suffixe)
    (s / "sauvegardes_supabase.sql").write_text(q, encoding="utf-8")
    if a_blanc:
        dire("   chez Supabase : A BLANC -- le SQL est ecrit (sauvegardes_supabase.sql), PAS joue : registre (chaines et "
             "etiquettes), compteur et journal des etiquettes, repartition, suffixe %s" % suffixe)
    else:
        jouer_sql(q, "sauvegardes chez Supabase")


# ═══════════════════════════════════════════ 2. LA POSE ════════════════════════════════════════════════════════════
def module_sans_les_deux(source: str) -> str:
    """Retire 4126 et 21520 d'EXCLUES_DE_LA_REGLE_E par l'arbre de syntaxe (la methode du retrait a blanc du 24/11), et
    PROUVE qu'il ne manque qu'elles, toutes les autres valeurs intactes, et que le module compile."""
    arbre = ast.parse(source)
    noeud = next(n for n in arbre.body if isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") ==
                 "EXCLUES_DE_LA_REGLE_E")
    lignes = source.split("\n")
    a_effacer = set()
    for k, v in zip(noeud.value.keys, noeud.value.values):
        if ast.literal_eval(k) in A_RETIRER:
            a_effacer |= set(range(k.lineno - 1, v.end_lineno))
    neuf = "\n".join(l_ for n, l_ in enumerate(lignes) if n not in a_effacer)
    avant, apres = exclusions_e(source), exclusions_e(neuf)
    if set(avant) - set(apres) != set(A_RETIRER) or any(apres[k] != avant[k] for k in apres):
        raise Refus("la retouche ne retire pas exactement %s" % (A_RETIRER,))
    compile(neuf, "affaire_ledger.py (retouche)", "exec")
    return neuf


def garder_fins(origine: Path, texte: str) -> bytes:
    """Le texte, avec les fins de ligne du fichier d'origine (LF ou CRLF), en octets."""
    t = texte.replace("\r\n", "\n")
    return (t.replace("\n", "\r\n") if b"\r\n" in origine.read_bytes() else t).encode("utf-8")


def env_pose(texte: str) -> str:
    lignes, vus = [], set()
    for l_ in texte.splitlines():
        k = l_.split("=", 1)[0].strip() if "=" in l_ and not l_.lstrip().startswith("#") else None
        if k in INTERRUPTEURS:
            lignes.append("%s=%s" % (k, INTERRUPTEURS[k]))
            vus.add(k)
        else:
            lignes.append(l_)
    for k, v in INTERRUPTEURS.items():
        if k not in vus:
            lignes.append("%s=%s" % (k, v))
    return "\n".join(lignes) + ("\n" if texte.endswith("\n") else "")


def etape_2(M: dict, scene: Path, a_blanc: bool) -> dict:
    dire("2. LA POSE%s" % (" -- A BLANC, dans la scene (aucun fichier du depot ni .env touche)" if a_blanc else ""))
    cible = (scene / "pose") if a_blanc else None
    if cible:
        cible.mkdir(parents=True, exist_ok=True)
    det = (cible / FICHIER_DET.name) if a_blanc else FICHIER_DET
    mod = (cible / MODULE.name) if a_blanc else MODULE
    env = (cible / ".env") if a_blanc else ENV
    # ⛔ 25/11, LE GESTE DE 08:09 S'EST ARRETE ICI : au geste, le module pose EST le module du depot (meme fichier). La
    #   preuve « depot moins les seules lignes retirees » comparait donc le fichier A LUI-MEME (0 retiree -> refus). Les
    #   ORIGINAUX sont lus ICI, AVANT toute ecriture, et les preuves comparent le pose a eux -- a blanc comme au geste.
    orig_mod, orig_env = MODULE.read_bytes(), ENV.read_bytes()
    shutil.copyfile(M["brouillon"]["chemin"], det)
    if md5(det) != M["brouillon"]["md5"]:
        raise Refus("le fichier des coupes pose n'a pas l'empreinte du brouillon")
    dire("   le brouillon -> %s (md5 %s = le brouillon accorde ; %d lignes)" % (
        det, md5(det)[:8], len(det.read_text(encoding="utf-8").splitlines())))
    neuf = module_sans_les_deux(MODULE.read_text(encoding="utf-8"))
    mod.write_bytes(garder_fins(MODULE, neuf))
    # ⚠ 25/11 : la pose a blanc du 24/11 avait reecrit le module en CRLF (write_text sous Windows) alors que le depot est en
    #   LF. On garde les fins de ligne d'origine, et on PROUVE que le fichier pose est le depot MOINS les seules lignes
    #   retirees : aucune ligne ajoutee, aucune changee.
    import difflib
    d_ = list(difflib.unified_diff(orig_mod.decode("utf-8").split("\n"),
                                   mod.read_bytes().decode("utf-8").split("\n"), lineterm="", n=0))
    plus = [l_ for l_ in d_ if l_.startswith("+") and not l_.startswith("+++")]
    moins = [l_ for l_ in d_ if l_.startswith("-") and not l_.startswith("---")]
    if plus or not moins:
        raise Refus("le module pose n'est pas le depot moins des lignes (%d ajoutee(s), %d retiree(s))" % (len(plus), len(moins)))
    dire("   le retrait de E -> %s : %s retirees (%d lignes en moins, 0 ajoutee, fins de ligne d'origine), %d exclusions "
         "restent, le module compile (md5 %s)" % (mod, "+".join(map(str, A_RETIRER)), len(moins), len(exclusions_e(neuf)),
                                                  md5(mod)[:8]))
    env.write_bytes(garder_fins(ENV, env_pose(ENV.read_text(encoding="utf-8"))))
    # ⚠ 25/11 : un diff ligne a ligne signalait la fin de fichier comme une ligne « vide » deplacee (un artefact
    #   d'alignement). LA PREUVE JUSTE : sans les lignes des deux interrupteurs, le .env pose porte EXACTEMENT les lignes
    #   d'origine, et rien d'autre.
    from collections import Counter

    def hors_interrupteurs(t: str) -> Counter:
        return Counter(l_ for l_ in t.replace("\r\n", "\n").split("\n")
                       if l_.split("=", 1)[0].strip() not in INTERRUPTEURS)
    avant_, apres_ = hors_interrupteurs(orig_env.decode("utf-8")), hors_interrupteurs(env.read_bytes().decode("utf-8"))
    if avant_ != apres_:
        diff_ = (avant_ - apres_) + (apres_ - avant_)
        raise Refus(".env pose change autre chose que les deux interrupteurs (cles seulement, jamais les valeurs) : %s"
                    % sorted({l_.split("=")[0] for l_ in diff_}))
    e = lire_env(env)
    if any(e.get(k) != v for k, v in INTERRUPTEURS.items()):
        raise Refus(".env pose ne porte pas les interrupteurs")
    dire("   .env -> %s : %s" % (env, ", ".join("%s=%s" % (k, e[k]) for k in INTERRUPTEURS)))
    return {"det": det, "mod": mod, "env": env}


def remettre(scene: Path) -> None:
    s = scene / "sauvegardes"
    for p in (FICHIER_DET, MODULE, ENV):
        if (s / p.name).exists():
            shutil.copyfile(s / p.name, p)
            dire("   remis : %s (md5 %s)" % (p, md5(p)[:8]))


# ═══════════════════════════════════════════ 4. LE POINT DE NON-RETOUR ═════════════════════════════════════════════
def charger_module(chemin: Path, det: Path):
    """Le module POSE. A blanc, c'est la copie de la scene : ses deux fichiers sont pointes sur le fichier de la scene et
    sur les rattachements de production. Au geste, c'est le vrai fichier du depot, tel quel."""
    src = chemin.read_text(encoding="utf-8")
    if chemin.resolve() != MODULE.resolve():
        for avant, apres in (("ROOT = Path(__file__).resolve().parents[2]", "ROOT = Path(%r)" % str(RACINE)),
                             ('FICHIER_RATTACHEMENTS = Path(__file__).resolve().parent / "rattachements_manuels.csv"',
                              "FICHIER_RATTACHEMENTS = Path(%r)" % str(FICHIER_RAT)),
                             ('FICHIER_DETACHEMENTS = Path(__file__).resolve().parent / "detachements_manuels.csv"',
                              "FICHIER_DETACHEMENTS = Path(%r)" % str(det))):
            if src.count(avant) != 1:
                raise Refus("le module a change : ancre introuvable %r" % avant[:60])
            src = src.replace(avant, apres)
        chemin = chemin.parent / "_module_pose.py"
        chemin.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("al_vague_du_soir", chemin)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def etape_4(M: dict, pose: dict, attendu: Path) -> tuple[list, dict]:
    dire("4. ⛔ LE POINT DE NON-RETOUR -- la vraie fonction, sur une copie en memoire du registre local, contre le rejeu "
         "du matin (%s)" % attendu.name)
    t0 = time.time()
    mod = charger_module(pose["mod"], pose["det"])
    mem = sqlite3.connect("file:vague_du_soir_registre?mode=memory", uri=True)   # uri : l'attache en lecture seule
    mem.execute("attach database ? as src", ("file:%s?mode=ro" % BASE.as_posix(),))
    cols = [r[1] for r in mem.execute("pragma src.table_info(app_affaire_ledger)") if r[1] != "payload_json"]
    mem.execute("create table app_affaire_ledger as select %s from src.app_affaire_ledger" % ", ".join(cols))
    mem.execute("create table app_mandat_register_current as select numero_mandat, hektor_annonce_id, numero_dossier "
                "from src.app_mandat_register_current")
    mem.commit()
    mem.execute("detach database src")
    env = lire_env(pose["env"])
    gardes = {k: os.environ.get(k) for k in INTERRUPTEURS}
    os.environ.update({k: env[k] for k in INTERRUPTEURS})
    try:
        with contextlib.redirect_stdout(io.StringIO()) as sortie:
            res = mod.recalculer_les_chaines(mem)
    finally:
        for k, v in gardes.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    soir = chaines_du_registre(mem)
    mem.close()
    matin = {int(k): v for k, v in json.loads(Path(attendu).read_text(encoding="utf-8"))["ch"].items()}
    ecarts = sorted(a for a in set(soir) | set(matin) if soir.get(a) != matin.get(a))
    dire("   %d pieces ce soir, %d au rejeu du matin ; ⭐ ECARTS PIECE PAR PIECE : %d %s ; en %.0f s" % (
        len(soir), len(matin), len(ecarts), [(a, matin.get(a), soir.get(a)) for a in ecarts[:12]], time.time() - t0))
    dire("   (le compte rendu de la fonction : %s)" % (sortie.getvalue().strip().splitlines() or [""])[-1][:200])
    return ecarts, res


# ═══════════════════════════════════════════ 5 a 8 : LE GESTE ══════════════════════════════════════════════════════
def jouer_sql(q: str, quoi: str) -> None:
    """Un patch (begin ... commit), joue tel quel par la connexion du run. S'il leve, rien n'est ecrit (rollback)."""
    import psycopg2
    import urllib.parse
    from phase2.sync import push_upgrade_to_supabase as PU
    PU.load_env_files(PU.DEFAULT_ENV_FILES)
    u = urllib.parse.urlparse(os.environ["DATABASE_URL"])
    cn = psycopg2.connect(host=os.environ["SUPABASE_POOLER_HOST"], port=5432, dbname="postgres",
                          user="postgres.dwaqxfrinihnychuoptk", password=urllib.parse.unquote(u.password),
                          connect_timeout=15, sslmode="require")
    cn.autocommit = True        # le patch porte son begin ... commit (memoire « un patch porte son commit; »)
    try:
        cn.cursor().execute(q)
        for n in cn.notices:
            dire("      " + n.strip())
        dire("   ✅ %s : joue" % quoi)
    except Exception as e:  # noqa: BLE001
        raise Refus("%s : REFUSE, rien n'est ecrit -- %s" % (quoi, str(e).strip()[:600]))
    finally:
        cn.close()


def a_blanc_sql(chemin: Path) -> int:
    """UN ESSAI A BLANC, joue par LA CONNEXION DU GESTE (celle que l'etape 7 utilisera) : le fichier ne doit porter AUCUN
    commit ; il doit finir par une erreur VOULUE qui commence par « A BLANC » ; la transaction est annulee EXPLICITEMENT ;
    puis une relecture prouve qu'aucune des tables que le fichier cree n'existe."""
    import re
    import psycopg2
    import urllib.parse
    from phase2.sync import push_upgrade_to_supabase as PU
    q = chemin.read_text(encoding="utf-8")
    if re.search(r"^\s*commit\s*;", q, re.I | re.M):
        dire("⛔ %s porte un commit : ce n'est pas un essai a blanc, il n'est PAS envoye" % chemin.name)
        return 2
    tables = sorted(set(re.findall(r"create table public\.(\w+)", q, re.I)))
    PU.load_env_files(PU.DEFAULT_ENV_FILES)
    u = urllib.parse.urlparse(os.environ["DATABASE_URL"])
    cn = psycopg2.connect(host=os.environ["SUPABASE_POOLER_HOST"], port=5432, dbname="postgres",
                          user="postgres.dwaqxfrinihnychuoptk", password=urllib.parse.unquote(u.password),
                          connect_timeout=15, sslmode="require")
    cn.autocommit = False
    t0 = time.time()
    message, code = "", 1
    try:
        cn.cursor().execute(q)
        message = "⛔ LE FICHIER N'A PAS LEVE SON ERREUR VOULUE -- annule quand meme"
    except Exception as e:  # noqa: BLE001
        message = str(e).strip()
        code = 0 if message.startswith("A BLANC") else 1
    finally:
        cn.rollback()
    for n in cn.notices:
        dire("      " + n.strip())
    dire("%s (%.0f s)" % (message, time.time() - t0))
    cu = cn.cursor()
    cu.execute("select %s" % (", ".join("to_regclass('public.%s') is null" % t for t in tables) or "true"))
    rien = all(cu.fetchone())
    cn.rollback()
    cn.close()
    dire("   relu apres : les %d table(s) que le fichier cree sont absentes -> %s" % (
        len(tables), "RIEN N'EST RESTE" if rien else "⛔ UNE TABLE EST RESTEE"))
    return code if rien else 3


def lancer(args: list[str], quoi: str) -> None:
    dire("   $ %s %s" % (PY_RUN.name, " ".join(args)))
    t0 = time.time()
    r = subprocess.run([str(PY_RUN), "-X", "utf8", *args], cwd=str(RACINE), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    for l_ in (r.stdout + r.stderr).strip().splitlines()[-25:]:
        dire("      " + l_)
    if r.returncode != 0:
        raise Refus("%s : code %d" % (quoi, r.returncode))
    dire("   ✅ %s en %.0f s" % (quoi, time.time() - t0))


def etape_6(attendu: Path) -> list:
    import protocole_classeur as P
    cn, cu = P.pooler()
    cu.execute("select app_affaire_id, app_chaine_id from public.app_affaire_ledger")
    sb = {int(a): (int(c) if c is not None else None) for a, c in cu.fetchall()}
    cn.rollback()
    cn.close()
    matin = {int(k): v for k, v in json.loads(Path(attendu).read_text(encoding="utf-8"))["ch"].items()}
    ec = sorted(a for a in set(sb) | set(matin) if sb.get(a) != matin.get(a))
    dire("6. LE CONTROLE -- chez Supabase : %d pieces ; ecarts au rejeu du matin : %d %s" % (len(sb), len(ec), ec[:12]))
    return ec


# ═══════════════════════════════════════════ LA COMMANDE ═══════════════════════════════════════════════════════════
def main() -> int:
    global JOURNAL
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifeste")
    ap.add_argument("--seulement", type=int, choices=range(0, 5))
    ap.add_argument("--attendu-temoin", default="", help="un AUTRE rejeu attendu, pour le temoin inverse de l'etape 4")
    ap.add_argument("--geste", action="store_true")
    ap.add_argument("--accord", default="", help="l'empreinte md5 du manifeste qu'il a accorde")
    ap.add_argument("--remettre", default="")
    ap.add_argument("--a-blanc-sql", default="", help="un essai a blanc (sans commit, erreur voulue) par la connexion du geste")
    a = ap.parse_args()
    if a.a_blanc_sql:
        return a_blanc_sql(Path(a.a_blanc_sql))
    if a.remettre:
        remettre(Path(a.remettre))
        return 0
    M = json.loads(Path(a.manifeste).read_text(encoding="utf-8"))
    if a.geste and a.accord != md5(Path(a.manifeste)):
        dire("⛔ --geste exige --accord = l'empreinte du manifeste accorde (%s)" % md5(Path(a.manifeste)))
        return 2
    a_blanc = not a.geste
    horo = datetime.now().strftime("%Y%m%d_%H%M%S")
    scene = SCENES / ("%s_%s" % (horo, "a_blanc" if a_blanc else "GESTE"))
    scene.mkdir(parents=True, exist_ok=False)
    JOURNAL = scene / "compte_rendu.txt"
    dire("LA VAGUE DU SOIR -- %s -- %s -- manifeste %s (md5 %s) -- scene %s" % (
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "⛔ A BLANC" if a_blanc else "⛔⛔ LE GESTE", Path(a.manifeste).name,
        md5(Path(a.manifeste))[:8], scene))
    durees = {}
    attendu = Path(a.attendu_temoin or M["attendu_E"]["chemin"])
    pose = None
    # ⛔ 25/11, LE GESTE DE 08:09 : la remise ne jouait que si l'etape 2 avait FINI (`pose is not None`) -- un refus PENDANT
    #   la pose laissait le fichier des coupes et le module poses (remis a la main a 08:1x). La remise joue desormais des que
    #   la pose a COMMENCE, pour TOUTE erreur (pas seulement un refus), et jamais une fois l'etape 5 commencee (« apres
    #   l'etape 5, on ne revient pas en arriere » : une poussee interrompue se tranche avec lui, pas par la machine).
    pose_commencee = etape5_commencee = False
    try:
        t = time.time()
        if a.seulement in (None, 0):
            refus = etape_0(M, a_blanc)
            durees[0] = time.time() - t
            if refus:
                dire("   ⛔ %d GARDE(S) REFUSE(NT)%s" % (len(refus), " -- A BLANC : on continue pour eprouver la suite"
                                                        if a_blanc else ""))
                if not a_blanc:
                    return 10
        if a.seulement == 0:
            return 0
        t = time.time()
        etape_1(scene, a_blanc, horo)
        durees[1] = time.time() - t
        t = time.time()
        pose_commencee = True
        pose = etape_2(M, scene, a_blanc)
        durees[2] = time.time() - t
        if a_blanc:
            dire("3. LA DOUBLURE DU LEDGER -- A BLANC : non jouee (elle ecrit la doublure locale). Au geste : "
                 "phase2/sync/pull_from_supabase.py --table app_affaire_ledger (mesuree 1 min 35 s le 24/11 au run)")
        else:
            t = time.time()
            lancer(["phase2/sync/pull_from_supabase.py", "--table", "app_affaire_ledger"], "la doublure du ledger")
            durees[3] = time.time() - t
        t = time.time()
        ecarts, _res = etape_4(M, pose, attendu)
        durees[4] = time.time() - t
        if ecarts:
            raise Refus("⛔ LE POINT DE NON-RETOUR REFUSE : %d piece(s) n'arrivent pas la ou le matin l'a prevu" % len(ecarts))
        dire("   ✅ LE POINT DE NON-RETOUR PASSE : 0 ecart")
        if a_blanc:
            dire("5 a 8 -- A BLANC, DITES SEULEMENT :")
            dire("   5. $ .venv python phase2/sync/affaire_ledger.py --refresh --push   (⛔ le seul geste irreversible)")
            dire("   6. le controle : les chaines chez Supabase = le rejeu du matin, piece par piece (lecture)")
            dire("   7. A2 : %s (puis sa repetition)" % Path(M["a2_patch"]["chemin"]).name)
            dire("   8. $ .venv python phase2/sync/repartition_commission.py --purger-orphelines --pousser")
            remettre_si_geste = False
        else:
            t = time.time()
            etape5_commencee = True
            lancer(["phase2/sync/affaire_ledger.py", "--refresh", "--push"], "le chainage et sa poussee")
            durees[5] = time.time() - t
            t = time.time()
            if etape_6(attendu):
                raise Refus("⛔ LE CONTROLE : les chaines chez Supabase ne sont pas celles du rejeu -- A2 NE SE JOUE PAS")
            durees[6] = time.time() - t
            t = time.time()
            jouer_sql(Path(M["a2_patch"]["chemin"]).read_text(encoding="utf-8"), "A2")
            for nom in ("a1_patch", "a3_patch"):
                if nom in M:
                    jouer_sql(Path(M[nom]["chemin"]).read_text(encoding="utf-8"), nom)
            # la repetition d'A2, en lecture seule (le journal, les parts du lot, la mise de cote, 0 vente reglee sans part,
            #   0 orpheline, les membres comme le rejeu, l'empreinte d'apres)
            import protocole_classeur as P
            cn_, cu_ = P.pooler()
            cu_.execute(Path(M["a2_repetition"]["chemin"]).read_text(encoding="utf-8"))
            for c_, v_ in zip([c.name for c in cu_.description], cu_.fetchone()):
                dire("      repetition A2 : %-48s %s" % (c_, v_))
            cn_.rollback()
            cn_.close()
            durees[7] = time.time() - t
            t = time.time()
            lancer(["phase2/sync/repartition_commission.py", "--purger-orphelines", "--pousser"], "la repartition")
            durees[8] = time.time() - t
    except Exception as e:  # noqa: BLE001 -- TOUTE erreur, pas seulement un refus
        import traceback
        dire("⛔ ARRET : %s" % e)
        if not isinstance(e, Refus):
            dire(traceback.format_exc())
        if not a_blanc and pose_commencee and not etape5_commencee:
            dire("   AVANT L'ETAPE 5 : TOUT EST REMIS COMME AVANT")
            remettre(scene)
        elif not a_blanc and etape5_commencee:
            dire("   ⛔ L'ETAPE 5 A COMMENCE : RIEN N'EST REMIS PAR LA MACHINE -- on s'arrete et on tranche avec lui")
        return 1
    dire("9. ARRET -- durees (s) : %s ; total %.0f s" % (
        ", ".join("%d: %.0f" % kv for kv in sorted(durees.items())), sum(durees.values())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
