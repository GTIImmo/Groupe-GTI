#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHANTIER 7, PIECE ④ -- SORTIR UNE ANNONCE DU BROUILLON : tout est-il en place ?
                                                                  20/10/2026

Un type de travail neuf vit a HUIT endroits, et une faute a UN SEUL ne produit
AUCUNE erreur : le travail est cree, personne ne le reclame, il reste « pending »
a vie. Ce controle lit les FICHIERS et verifie que tout porte le meme nom, et que
chaque etape du chemin existe.

⚠ ET IL REGARDE AUSSI LES GARDES, pas seulement les noms. C'est la lecon du 20/10 :
  a la piece ②, mes 20 controles verifiaient le nom du geste partout et aucun ne
  verifiait si le geste etait OFFERT -- la modale le refusait, et c'est Frederic qui
  l'a trouve en cliquant.

⛔ AUCUN APPEL -- ni Hektor, ni Supabase. Lecture de fichiers.

    python phase2/checks/test_piece4_sortir_du_brouillon.py
    sortie 0 = tout coherent · 1 = un endroit manque
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parents[2]
TYPE = "exit_hektor_draft_annonce"
echecs: list[str] = []


def controle(nom: str, condition: bool, detail: str = "") -> None:
    print(f"{'  OK  ' if condition else 'ECHEC '} {nom}{'' if condition else ' -- ' + detail}")
    if not condition:
        echecs.append(nom)


def lire(chemin: str) -> str:
    p = RACINE / chemin
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


WORKER = lire("Console/console_job_worker.js")
API = lire("apps/hektor-v1/src/lib/api.ts")
APP = lire("apps/hektor-v1/src/App.tsx")
SCRIPT = lire("phase2/sync/marquer_brouillon_sorti.py")
PATCH = lire("supabase/patch_chantier7_piece4_sortir_du_brouillon_2026-10-20.sql")
INVERSE = lire("supabase/patch_chantier7_piece4_sortir_du_brouillon_2026-10-20_INVERSE.sql")
TEMOIN = lire("supabase/patch_chantier7_piece4_sortir_du_brouillon_2026-10-20_REPETITION.sql")

print(f"LE TYPE DE TRAVAIL : {TYPE}\n")

# ── LE WORKER ────────────────────────────────────────────────────────────────
controle("(1) le worker le route vers le service ADMIN", f'"{TYPE}",' in WORKER)
controle("(2) ⭐ loadDossier le laisse passer SUR UN BROUILLON",
         f'job.job_type === "{TYPE}"' in WORKER,
         "sinon loadDossier jette « Annonce en cours de creation » avant de commencer")
controle("(3) le handler existe", "async function handleExitHektorDraftAnnonce(job)" in WORKER)
controle("(4) le routeur l'aiguille",
         f'case "{TYPE}":' in WORKER and "return handleExitHektorDraftAnnonce(job);" in WORKER)
# ⭐⭐ `etatAnnonce = 1` N'EST PAS UNE NOUVEAUTE, et c'est la meilleure nouvelle de la
#   piece ④ : createHektorAnnonceWithHttpDirect l'envoie DEJA (l. ~3959), dans ses
#   `activationCommands`, apres l'assistant. C'est ainsi que CHAQUE annonce que nous
#   creons est activee. Donc le mecanisme est eprouve en production depuis des mois --
#   mon « non mesure : que etatAnnonce = 1 suffise » tombe.
# ⚠ La creation envoie AUSSI diffusable=0 et partage=0. La bascule, elle, n'envoie
#   QUE etatAnnonce : on ne touche pas a la diffusion d'un bien qui existe deja.
_handler = WORKER.split("async function handleExitHektorDraftAnnonce(job)")[-1][:4000]
controle("(5) ⭐ le handler n'envoie QUE etatAnnonce (pas diffusable, pas partage)",
         _handler.count('champ: "etatAnnonce"') == 1
         and 'champ: "diffusable"' not in _handler
         and 'champ: "partage"' not in _handler,
         "la bascule ne doit pas toucher la diffusion d'un bien existant")
controle("(5 bis) ⭐ et la creation d'annonce garde ses 3 commandes d'activation",
         "const activationCommands = [" in WORKER
         and WORKER.count('champ: "etatAnnonce"') == 2,
         "temoin inverse : je ne dois pas avoir touche a la creation")
controle("(6) ⚠ le worker EXIGE le basculement (il relit isDraft apres)",
         "exit_draft_verify_after" in WORKER and "TOUJOURS un brouillon" in WORKER,
         "sans ca, un 200 passerait pour un succes")
controle("(7) ⚠ et il REFUSE les coquilles sans statut",
         "n'a aucun statut" in WORKER,
         "une regle qui ne vit qu'a l'ecran n'est pas une regle")

# ── LE MIROIR LOCAL ──────────────────────────────────────────────────────────
controle("(8) ⭐ le script qui corrige le miroir existe", bool(SCRIPT))
controle("(9) et le worker l'appelle", "marquer_brouillon_sorti.py" in WORKER,
         "sans lui, l'annonce serait NULLE PART jusqu'au run de 05:00")
controle("(10) le script relit apres avoir ecrit (preuve, pas absence d'erreur)",
         "toujours marque brouillon dans le miroir apres l'ecriture" in SCRIPT)

# ── LE FRONT ─────────────────────────────────────────────────────────────────
controle("(11) api.ts cree le travail", f"job_type: '{TYPE}'" in API)
controle("(12) App.tsx a son gestionnaire ET l'importe",
         "async function handleExitDraftAnnonce(" in APP
         and "  createExitHektorDraftAnnonceJob," in APP)
controle("(13) ⚠ l'ecran refuse les coquilles AVANT d'envoyer",
         "il n'y a rien a mettre en ligne" in APP)
controle("(14) ⭐ LE CRAN UNIQUE : un brouillon est un brouillon avant tout",
         "const ckStage = estBrouillon ? 'brouillon'" in APP,
         "sinon un brouillon Estimation et un brouillon Actif n'ont pas la meme fiche")
controle("(15) le cran existe et est en LECTURE SEULE",
         "brouillon: { label: 'Brouillon'" in APP and "led: '#c98a1e', ro: true" in APP)
controle("(16) ⚠ et il ne propose PLUS « Creer le mandat »",
         "brouillon: { label: 'Brouillon'" in APP
         and "Creer le mandat" not in APP.split("brouillon: { label: 'Brouillon'")[1][:600]
         and "Créer le mandat" not in APP.split("brouillon: { label: 'Brouillon'")[1][:600])
controle("(17) ⭐ LE BOUTON existe, dans le bandeau de lecture seule",
         "props.onExitDraft?.(dossier)}>Mettre en ligne</button>" in APP,
         "le cran est `ro` : sans bouton dans le bandeau, AUCUNE issue")
controle("(18) la propriete est declaree partout ou sa voisine l'est",
         APP.count("onExitDraft?: (dossier: Dossier) => void")
         == APP.count("onRestoreAnnonce?: (dossier: Dossier) => void"),
         f"{APP.count('onExitDraft?: (dossier: Dossier) => void')} contre "
         f"{APP.count('onRestoreAnnonce?: (dossier: Dossier) => void')}")
controle("(19) et passee partout ou sa voisine l'est",
         APP.count("onExitDraft={isManagerOrAdmin ? handleExitDraftAnnonce : undefined}")
         == APP.count("onRestoreAnnonce={handleRestoreHektorAnnonce}"))

# ── LES 3 VERROUS (dans le patch a coller) ───────────────────────────────────
controle("(20) le patch SQL touche les 3 verrous",
         all(x in PATCH for x in ("app_console_job_job_type_check",
                                  "app_console_can_request_job",
                                  "app_console_claim_next_job")))
controle("(21) l'inverse et le temoin existent",
         TYPE in INVERSE and TYPE in TEMOIN)
controle("(22) le patch rend un TABLEAU (l'editeur n'affiche pas les NOTICE)",
         "SELECT 1 AS \"#\"" in PATCH and "SELECT 1 AS \"#\"" in INVERSE)

# ── TEMOIN INVERSE : ce qui marchait marche encore ───────────────────────────
controle("(23) TEMOIN INVERSE -- la piece ② (detail brouillon) est intacte",
         '"prepare_brouillon_annonce_detail"' in WORKER
         and "async function handlePrepareBrouillonAnnonceDetail(job)" in WORKER)
controle("(24) TEMOIN INVERSE -- la branche ARCHIVE de loadDossier est intacte",
         "    if (READ_ONLY_ARCHIVE_JOB_TYPES.has(job.job_type)) {" in WORKER,
         "la forme d'origine doit subsister pour l'archive")
controle("(25) TEMOIN INVERSE -- le cran archive et son bouton Desarchiver",
         "archive: { label: 'Archivée'" in APP
         and "onRestoreAnnonce?.(dossier)}>Désarchiver</button>" in APP)

# ── LECON 30 sur les patchs neufs ────────────────────────────────────────────
nus: list[str] = []
for nom, texte in (("patch", PATCH), ("inverse", INVERSE), ("temoin", TEMOIN)):
    for m in re.finditer(r"(\w+)\s*(?:text\s*)?:=\s*(replace\(\s*)?\$([a-z0-9]+)\$(.*?)\$\3\$", texte, re.S):
        variable, enveloppe, tag, contenu = m.group(1), m.group(2), m.group(3), m.group(4)
        if "\n" not in contenu or enveloppe:
            continue
        if not re.search(re.escape(variable) + r"\s*:=\s*replace\(\s*" + re.escape(variable) + r"\s*,\s*chr\(13\)", texte):
            nus.append(f"{nom}:{texte[:m.start()].count(chr(10)) + 1} ({variable})")
controle("(26) ⚠⚠ LECON 30 : tout litteral multi-ligne est normalise chr(13)",
         not nus, f"non normalises : {nus}")

print()
if echecs:
    print(f"{len(echecs)} controle(s) en ECHEC : " + ", ".join(echecs))
    sys.exit(1)
print("Le geste existe de bout en bout : les 3 verrous, le worker, le miroir, l'ecran.")
print("Un brouillon a UNE seule presentation et UNE seule issue -- et les coquilles sont refusees.")
