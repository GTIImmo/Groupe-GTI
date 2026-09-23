#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UN SEUL VERROU — tous ceux qui se gardent de la descente regardent le MEME fichier.
                                                                  23/09/2026

POURQUOI CE FICHIER EXISTE. L'audit du 23/09 a trouve DEUX fichiers de verrou pour
proteger la meme base :

    pull_from_supabase.lock      le VRAI, pose par VerrouUnique apres l'incident
                                 du 22/08 (deux descentes simultanees, ~2 800
                                 requetes, l'instance Supabase a cede jusqu'au
                                 redemarrage)
    phase2/.descente.lock        TESTE par trois scripts, CREE PAR PERSONNE

Le second n'a jamais existe sur le disque. La condition `VERROU.exists()` etait donc
toujours fausse, et ces trois scripts ecrivaient PENDANT la descente -- c'est-a-dire
exactement ce que leur propre commentaire disait vouloir eviter.

⚠ C'EST LA MEME FORME QUE LE DEFAUT C-4, trouve le matin du meme jour : un garde-fou
  present dans le code, lisible, convaincant -- et qui ne protege rien. Deux fois en
  une journee. D'ou ce controle : il ne verifie pas qu'un verrou EXISTE, il verifie
  que tout le monde regarde LE MEME, et que c'est bien celui que quelqu'un CREE.

NE TOUCHE A RIEN. Lecture de fichiers.
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
echecs: list[str] = []


def controle(nom: str, condition: bool, detail: str = "") -> None:
    print(f"{'  OK  ' if condition else 'ECHEC '} {nom}{'' if condition else ' -- ' + detail}")
    if not condition:
        echecs.append(nom)


def lire(rel: str) -> str:
    return io.open(RACINE / rel, encoding="utf-8").read()


# ── QUI CREE UN VERROU ? ──────────────────────────────────────────────────
source = lire("phase2/sync/pull_from_supabase.py")
vrai = re.search(r'^VERROU\s*=\s*["\']([^"\']+)["\']', source, re.M)
controle("le vrai verrou est bien declare par la descente", vrai is not None)
NOM_DU_VRAI = vrai.group(1) if vrai else "pull_from_supabase.lock"
controle("et c'est une classe qui le POSE (VerrouUnique)",
         "class VerrouUnique" in source)

# ── QUI LE REGARDE ? ──────────────────────────────────────────────────────
GARDIENS = [
    "phase2/identite/magasin_annonce_app.py",
    "phase2/identite/magasin_affaire_app.py",
    "phase2/identite/magasin_mandat_app.py",
    "phase2/identite/annonces_app_seule.py",
    "phase2/identite/migrer_registre_recherche_2026-08-30.py",
    "phase2/sync/sync_active_searches.py",
]
for rel in GARDIENS:
    t = lire(rel)
    declaration = re.search(r'^VERROU(?:_LOURD)?\s*=\s*(.+)$', t, re.M)
    vise_le_bon = declaration is not None and NOM_DU_VRAI in declaration.group(1)
    controle(f"{Path(rel).name} regarde le vrai verrou",
             vise_le_bon,
             declaration.group(1).strip() if declaration else "aucune declaration")

# ── AUCUN AUTRE FICHIER DE VERROU NE DOIT SUBSISTER ───────────────────────
# On accepte le nom dans un COMMENTAIRE (on explique le defaut corrige), jamais
# dans une affectation.
fautifs = []
MOI = Path(__file__).resolve()
for chemin in RACINE.rglob("*.py"):
    # Ce fichier-ci porte le nom fautif dans son explication et dans sa propre
    # detection : s'il ne s'excluait pas, il s'accuserait lui-meme. Quatrieme
    # controle faux de la journee, attrape tout de suite.
    if chemin.resolve() == MOI:
        continue
    if ".claude" in str(chemin) or ".venv" in str(chemin):
        continue
    for ligne in io.open(chemin, encoding="utf-8", errors="ignore"):
        nu = ligne.strip()
        if nu.startswith("#"):
            continue
        if ".descente.lock" in nu:
            fautifs.append(f"{chemin.relative_to(RACINE)} : {nu[:60]}")
controle("plus aucun second fichier de verrou dans du code actif",
         not fautifs, " ; ".join(fautifs[:3]))

# ── LA PREUVE : ce controle voit-il le defaut d'avant ? ───────────────────
try:
    avant = subprocess.run(
        ["git", "show", "HEAD:phase2/identite/magasin_affaire_app.py"],
        cwd=str(RACINE), capture_output=True, text=True, encoding="utf-8", timeout=30)
    if avant.returncode == 0 and avant.stdout:
        d = re.search(r'^VERROU\s*=\s*(.+)$', avant.stdout, re.M)
        controle("PREUVE : la version d'avant visait un AUTRE fichier",
                 d is not None and NOM_DU_VRAI not in d.group(1),
                 "elle visait deja le bon : ce controle ne voit rien")
    else:
        echecs.append("PREUVE non faite (version d'avant illisible)")
        print("ECHEC  PREUVE non faite : version d'avant illisible")
except Exception as err:  # pragma: no cover
    echecs.append("PREUVE non faite")
    print(f"ECHEC  PREUVE non faite : {type(err).__name__}")

print()
if echecs:
    print(f"{len(echecs)} controle(s) en ECHEC : " + ", ".join(echecs))
    sys.exit(1)
print("Tous les controles passent : un seul verrou, et tout le monde le regarde.")
