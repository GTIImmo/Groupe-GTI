# -*- coding: utf-8 -*-
"""GARDE DES SESSIONS DU CHANTIER RECRUTEMENT -- delegation de Frederic du 20/11/2026.

Crochet « PreToolUse » de Claude Code (reglages utilisateur). Il est lance avant
chaque commande, chaque ecriture de fichier et chaque appel aux outils de la base
et du deploiement. Il ne REFUSE QUE pour les sessions inscrites dans
SESSIONS (une par ligne) : l'autre session du projet n'est jamais genee.

POURQUOI CETTE FORME ET PAS DES REGLES « deny » DU PROJET : une regle de
.claude/settings.json s'applique a TOUTES les sessions du projet. Elle aurait
interdit a la session du classeur d'ecrire dans phase2/ et Console/, ou elle
travaille. Ici, la garde ne vise que les sessions du chantier recrutement.

CE QU'ELLE REFUSE (le perimetre de la delegation, note §15) :
  - redemarrer, arreter ou modifier un service ; tuer un processus ;
  - creer, modifier, lancer ou supprimer une tache planifiee ;
  - git push, reset --hard, rebase, clean, stash, checkout --, restore,
    add . / add -A / commit -a, branch -D ;
  - installer un logiciel (pip, npm install, winget, choco) ;
  - toucher au registre Windows, au pare-feu, aux droits, a la politique d'execution ;
  - ecrire dans Console/, phase2/, un fichier .env, les scripts planifies existants,
    monitoring/ (sauf check_gti_health.py), les patchs supabase existants, les
    reglages de Claude Code et cette garde elle-meme ;
  - les outils qui deploient ou modifient la base hors SQL (Vercel, migrations
    Supabase, branches) et les taches planifiees de Claude.

ELLE NE PROUVE RIEN SEULE : c'est un garde-fou, pas un bac a sable. Une ecriture
deguisee (un script Python qui ouvre un fichier) peut lui echapper ; la regle
ecrite de la delegation reste la vraie limite.

EN CAS D'ERREUR INTERNE : refus pour une session inscrite (on ferme), passage
pour les autres (on ne gene personne).
"""
import json
import os
import re
import sys

SESSIONS = r"C:\Hektor\recrutement_donnees\garde\sessions.txt"
JOURNAL = r"C:\Hektor\recrutement_donnees\garde\refus.txt"

# ── LES COMMANDES ────────────────────────────────────────────────────────────
COMMANDES_INTERDITES = [
    (r"\b(restart|stop|start|set|new|remove|suspend|resume)-service\b", "toucher un service Windows"),
    (r"\bsc(\.exe)?\s+(stop|start|config|delete|create|pause|continue)\b", "toucher un service Windows"),
    (r"\bnet(\.exe)?\s+(stop|start)\b", "toucher un service Windows"),
    (r"\b(stop-process|taskkill)\b", "tuer un processus"),
    (r"\b(register|set|unregister|disable|enable|start|stop)-scheduledtask\b", "toucher une tache planifiee"),
    (r"\bschtasks(\.exe)?\b.*/(create|change|delete|run|end)\b", "toucher une tache planifiee"),
    (r"\bgit\b[^|;&]*\bpush\b", "pousser (un push redeploie toute l'app)"),
    (r"\bgit\b[^|;&]*\breset\b[^|;&]*--hard\b", "git reset --hard"),
    (r"\bgit\b[^|;&]*\brebase\b", "git rebase"),
    (r"\bgit\b[^|;&]*\bclean\b", "git clean"),
    (r"\bgit\b[^|;&]*\bstash\b", "git stash (cacherait le travail de l'autre session)"),
    (r"\bgit\b[^|;&]*\b(checkout|switch)\b", "git checkout / switch (le dossier est partage avec l'autre session)"),
    (r"\bgit\b[^|;&]*\b(pull|merge)\b", "git pull / merge (le dossier est partage avec l'autre session)"),
    (r"\bgit\b[^|;&]*\brestore\b(?![^|;&]*--staged)", "git restore (efface des modifications)"),
    (r"\bgit\b[^|;&]*\badd\b[^|;&]*(\s-a\b|\s-A\b|\s--all\b|\s\.(\s|$))", "git add global (on stage fichier par fichier)"),
    (r"\bgit\b[^|;&]*\bcommit\b[^|;&]*\s-(a|am)\b", "git commit -a (on stage fichier par fichier)"),
    (r"\bgit\b[^|;&]*\bbranch\b[^|;&]*\s-D\b", "supprimer une branche"),
    (r"\b(pip|pip3)(\.exe)?\s+install\b|\bpython[\w.]*\s+-m\s+pip\s+install\b", "installer un logiciel"),
    (r"\bnpm(\.cmd)?\s+(install|i|ci|uninstall|update)\b", "installer un logiciel"),
    (r"\b(winget|choco)\b", "installer un logiciel"),
    (r"\breg(\.exe)?\s+(add|delete|import)\b|\b(set|new|remove)-itemproperty\b[^|;&]*hk(lm|cu)", "toucher le registre Windows"),
    (r"\bnetsh\b|\b(set|new|remove)-netfirewall", "toucher le pare-feu"),
    (r"\b(icacls|takeown)\b|\bset-acl\b", "changer des droits"),
    (r"\bset-executionpolicy\b", "changer la politique d'execution"),
]

# Chemins proteges (en minuscules, barres obliques normales).
RACINE = "c:/hektor/projet/"
DOSSIERS_PROTEGES = [
    RACINE + "console/",
    RACINE + "phase2/",
    RACINE + ".claude/",
    "c:/users/admin/.claude/settings",
]
FICHIERS_PROTEGES = [
    RACINE + "recrutement/garde_session.py",
    RACINE + "scheduled/run_full_pipeline.ps1",
    RACINE + "run_full_pipeline.ps1",
]

# Une commande qui CITE un chemin protege ET porte un verbe d'ecriture est refusee.
# (Une simple lecture de phase2/ ou Console/ passe : grep, cat, python -c en lecture.)
VERBES_ECRITURE = re.compile(
    r"\b(set-content|add-content|out-file|remove-item|move-item|copy-item|rename-item|new-item|"
    r"clear-content)\b|(^|[\s;&|(])(rm|mv|cp|del|erase|rmdir|rd|ren|move|copy|touch|truncate)\s|\bsed\s+-i\b|\btee\b",
    re.I,
)
# Une redirection (> ou >>) vers un chemin protege est refusee.
REDIRECTION = re.compile(r"\d?>>?\s*[\"']?([^\s\"'|;&]+)")
SUPPRESSION_RECURSIVE = re.compile(r"\brm\s+-[a-z]*r[a-z]*f?\b|\bremove-item\b[^|;&]*-recurse\b|\brmdir\s+/s\b", re.I)
ZONES_JETABLES = ("/temp/claude/", "\\temp\\claude\\", "scratchpad")

# ── LES OUTILS ───────────────────────────────────────────────────────────────
OUTILS_INTERDITS = re.compile(
    r"^mcp__6be32f9b[^_]*__(apply_migration|deploy_edge_function|create_branch|merge_branch|reset_branch|"
    r"rebase_branch|delete_branch|pause_project|restore_project|create_project)$"
    r"|^mcp__580c961f[^_]*__(?!get_|list_|search_|aggregate_|count_|web_fetch|read_)"
    r"|^mcp__scheduled-tasks__(create|update|delete|run)_",
)


def normaliser(chemin):
    return (chemin or "").replace("\\", "/").lower()


def fichier_interdit(chemin):
    c = normaliser(chemin)
    if not c:
        return None
    base = c.rsplit("/", 1)[-1]
    if base == ".env":
        return "ecrire dans un fichier .env"
    if c in FICHIERS_PROTEGES:
        return "modifier un fichier protege (" + base + ")"
    for d in DOSSIERS_PROTEGES:
        if c.startswith(d):
            return "ecrire dans " + d.replace(RACINE, "")
    if c.startswith(RACINE + "scheduled/") and "recrutement" not in base:
        return "modifier un script planifie existant (" + base + ")"
    if c.startswith(RACINE + "monitoring/") and base != "check_gti_health.py":
        return "modifier la surveillance (" + base + ")"
    if c.startswith(RACINE + "supabase/") and "recrutement" not in base:
        return "modifier un patch supabase existant (" + base + ")"
    return None


def commande_interdite(cmd):
    texte = cmd or ""
    bas = texte.lower()
    for motif, raison in COMMANDES_INTERDITES:
        if re.search(motif, texte, re.I):
            return raison
    if SUPPRESSION_RECURSIVE.search(texte) and not any(z in bas for z in ZONES_JETABLES):
        return "supprimer un dossier en entier hors du brouillon"
    cmd_norm = normaliser(texte)
    for cible in REDIRECTION.findall(texte):
        c = normaliser(cible)
        if c in ("/dev/null", "$null", "nul", "&1", "&2"):
            continue
        if cite_un_chemin_protege(c):
            return "ecrire (redirection) dans un chemin protege"
    if VERBES_ECRITURE.search(texte) and cite_un_chemin_protege(cmd_norm):
        return "ecrire dans un chemin protege"
    return None


def cite_un_chemin_protege(texte_norm):
    cibles = DOSSIERS_PROTEGES + FICHIERS_PROTEGES
    courtes = ["console/", "phase2/", "run_full_pipeline", "garde_session.py", ".claude/settings"]
    if any(c in texte_norm for c in cibles):
        return True
    if any(re.search(r"(^|[\s\"'/=])" + re.escape(c), texte_norm) for c in courtes):
        return True
    return bool(re.search(r"(^|[\s\"'/=])\.env($|[\s\"'])", texte_norm))


def sessions_gardees():
    try:
        with open(SESSIONS, encoding="utf-8") as f:
            return {ligne.split()[0] for ligne in f if ligne.strip() and not ligne.startswith("#")}
    except FileNotFoundError:
        return set()


def refuser(raison, outil):
    try:
        from datetime import datetime
        with open(JOURNAL, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}\t{outil}\t{raison}\n")
    except Exception:
        pass
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "GARDE RECRUTEMENT : " + raison + ". C'est hors de la delegation du 20/11 "
                "(note du chantier, §15) : s'arreter et demander a Frederic."
            ),
        }
    }, ensure_ascii=False))
    sys.exit(0)


BRUT = ""


def main():
    donnees = json.loads(BRUT or "{}")
    if donnees.get("session_id") not in sessions_gardees():
        sys.exit(0)  # une autre session : la garde ne la regarde pas
    outil = donnees.get("tool_name") or ""
    entree = donnees.get("tool_input") or {}
    raison = None
    if outil in ("Bash", "PowerShell"):
        raison = commande_interdite(entree.get("command"))
    elif outil in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
        raison = fichier_interdit(entree.get("file_path") or entree.get("notebook_path"))
    elif OUTILS_INTERDITS.search(outil):
        raison = "un outil qui deploie ou modifie l'infrastructure (" + outil.split("__")[-1] + ")"
    if raison:
        refuser(raison, outil)
    sys.exit(0)


if __name__ == "__main__":
    try:
        BRUT = sys.stdin.read()
        main()
    except SystemExit:
        raise
    except Exception as exc:  # erreur interne : on ferme pour une session gardee, on laisse passer les autres
        try:
            gardee = json.loads(BRUT or "{}").get("session_id") in sessions_gardees()
        except Exception:
            gardee = any(s in (BRUT or "") for s in sessions_gardees())
        if gardee:
            refuser("erreur interne de la garde (" + type(exc).__name__ + ")", "garde")
        sys.exit(0)
