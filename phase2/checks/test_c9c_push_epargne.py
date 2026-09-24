#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C.9-c — LE PUSH N'EFFACE PLUS UNE ANNONCE QUE LE SERVEUR NE CONNAIT PAS ENCORE.
                                                                  24/09/2026

(1) la regle, dans les deux sens : on epargne UNIQUEMENT une annonce de la plage
    de l'app que le serveur ignore. Une annonce de Hektor disparue, et une annonce
    nee dans l'app que le serveur CONNAIT, restent effacables -- c'est le chemin
    normal de l'archivage.
(2) le branchement : le filtre est applique AVANT le frein de securite et AVANT
    toute suppression. ⚠ Et on le rejoue sur la version d'AVANT, EPINGLEE PAR SON
    NUMERO DE COMMIT : deux controles de cette semaine lisaient `git show HEAD:` et
    echouent a tort depuis que le correctif est commite.
(3) les vraies donnees, EN LECTURE SEULE : les fonctions du push, sur la vraie base
    et le vrai Supabase (GET seulement), sans rien effacer.

N'ECRIT RIEN, NULLE PART.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
# ⚠ L'ENVIRONNEMENT DU RUN, AVANT l'import : run_full_pipeline.ps1 l. 243 pose
#   APP_BROUILLON_BUCKET_ENABLED=1, et le push le lit A L'IMPORT. Sans lui, la vue
#   locale garde les 417 brouillons -- c'est ce qui a fabrique, le 24/09, un faux
#   « trou » de 417 annonces. Rejouer les ETAPES du run sans son ENVIRONNEMENT, c'est
#   la faute ecrite en tete de la liste le 22/09.
import os  # noqa: E402
os.environ["APP_BROUILLON_BUCKET_ENABLED"] = "1"
sys.path.insert(0, str(RACINE / "phase2" / "sync"))
import push_upgrade_to_supabase as push  # noqa: E402

VERSION_AVANT = "bd3ca5f"   # le dernier commit SANS C.9-c -- ne pas remplacer par HEAD
FICHIER = "phase2/sync/push_upgrade_to_supabase.py"
echecs: list[str] = []


def controle(nom: str, condition: bool, detail: str = "") -> None:
    print(f"{'  OK  ' if condition else 'ECHEC '} {nom}{'' if condition else ' -- ' + detail}")
    if not condition:
        echecs.append(nom)


# ── (1) la regle ──────────────────────────────────────────────────────────
a_effacer, epargnees = push.separer_annonces_app_en_attente(
    [5, 7, 10000001, 10000002, 10000003], {10000002})
controle("(1) une annonce nee dans l'app, inconnue du serveur, est EPARGNEE",
         epargnees == [10000001, 10000003], str(epargnees))
controle("(1) une annonce de Hektor disparue reste effacable (archivage normal)",
         5 in a_effacer and 7 in a_effacer, str(a_effacer))
controle("(1) une annonce nee dans l'app que le serveur CONNAIT reste effacable",
         10000002 in a_effacer, str(a_effacer))
controle("(1) rien n'est perdu ni invente", sorted(a_effacer + epargnees) == [5, 7, 10000001, 10000002, 10000003])
controle("(1) liste vide -> rien", push.separer_annonces_app_en_attente([], set()) == ([], []))


# ── (2) le branchement, et la preuve sur la version d'avant ─────────────────
def branchement_correct(source: str) -> tuple[bool, str]:
    appel = source.find("separer_annonces_app_en_attente(\n        stale_ids")
    if appel < 0:
        appel = source.find("separer_annonces_app_en_attente(stale_ids")
    frein = source.find("if stale_ids and not args.allow_stale_deletes")
    suppression = source.find('delete_rows_by_ids(path="app_dossier_current"')
    if appel < 0:
        return False, "le filtre n'est pas applique a stale_ids"
    if not (0 <= appel < frein < suppression):
        return False, f"ordre faux : filtre {appel}, frein {frein}, suppression {suppression}"
    # et entre le filtre et la suppression, personne ne recalcule stale_ids
    entre = source[appel:suppression]
    if re.search(r"\n\s+stale_ids\s*=\s*stale_remote_ids\(\)", entre):
        return False, "stale_ids est recalcule APRES le filtre"
    return True, ""


actuel = (RACINE / FICHIER).read_text(encoding="utf-8")
ok, pourquoi = branchement_correct(actuel)
controle("(2) le filtre passe AVANT le frein et AVANT toute suppression", ok, pourquoi)

avant = subprocess.run(["git", "show", f"{VERSION_AVANT}:{FICHIER}"], cwd=RACINE,
                       capture_output=True, text=True, encoding="utf-8")
if avant.returncode != 0 or not avant.stdout:
    controle("(2) PREUVE sur la version d'avant", False, f"illisible ({VERSION_AVANT})")
else:
    ok_avant, pourquoi_avant = branchement_correct(avant.stdout)
    controle(f"(2) PREUVE : sur {VERSION_AVANT} (avant C.9-c), le controle ECHOUE",
             not ok_avant, "il passait deja : ce controle ne voit rien")
    print(f"       version d'avant : « {pourquoi_avant} »")

# ── (3) les vraies donnees, en lecture seule ─────────────────────────────
push.load_env_files(push.DEFAULT_ENV_FILES)
url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
if not url or not cle:
    controle("(3) vraies donnees", False, "environnement Supabase absent")
else:
    client = push.SupabaseRestClient(base_url=url, service_role_key=cle)
    local = push.fetch_local_app_dossier_identity()
    locaux = {r["app_dossier_id"] for r in local}
    distants = client.fetch_all_rows(path="app_dossier_current",
                                     select="app_dossier_id,hektor_annonce_id",
                                     order="app_dossier_id.asc")
    ids_distants = {int(r["app_dossier_id"]) for r in distants if r.get("app_dossier_id") is not None}
    disparues = sorted(ids_distants - locaux)
    connus = push.fetch_local_app_range_ids()
    a_effacer, epargnees = push.separer_annonces_app_en_attente(disparues, connus)
    controle("(3) les fonctions du push tournent sur la vraie base et le vrai Supabase", True)
    controle("(3) dans l'environnement du run, la vue locale colle a Supabase",
             len(locaux - ids_distants) == 0, f"{len(locaux - ids_distants)} en trop")
    controle("(3) aujourd'hui : aucune annonce nee dans l'app, rien a epargner",
             epargnees == [], str(epargnees[:10]))
    print(f"       vue locale {len(locaux)} · Supabase {len(ids_distants)} · "
          f"« disparues » brutes {len(disparues)} · epargnees {len(epargnees)} · "
          f"numeros app connus du serveur {len(connus)}")

print()
if echecs:
    print(f"{len(echecs)} controle(s) en ECHEC : " + ", ".join(echecs))
    sys.exit(1)
print("Le push epargne une annonce que le serveur ne connait pas encore -- et seulement elle.")
