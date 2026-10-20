#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHANTIER 7, PIECE ② -- LE TYPE DE TRAVAIL EST-IL ECRIT PAREIL PARTOUT ?
                                                                  20/10/2026

POURQUOI CE CONTROLE EXISTE. La regle du projet (memoire
« nouveau-type-de-travail-trois-verrous ») : un type de travail neuf vit a HUIT
endroits -- 3 verrous en base, 5 dans le code. Une seule faute de frappe dans un
seul d'entre eux ne produit AUCUNE erreur : le travail est cree, personne ne le
reclame, et il reste « pending » a vie. C'est exactement ce qui est arrive le
03/10 a `unlink_hektor_mandant`.

Ce controle lit les FICHIERS (pas la base -- les 3 verrous sont dans le patch SQL
que Frederic colle) et verifie que la meme chaine, au caractere pres, est partout.

⛔ IL NE LIT RIEN EN BASE ET N'ECRIT RIEN. Lecture de fichiers, point.
⚠ IL NE REMPLACE PAS LE TEMOIN SQL (..._REPETITION.sql), qui lui mesure la base.

    python phase2/checks/test_piece2_coherence_type_travail.py
    sortie 0 = tout coherent · 1 = un endroit manque ou diverge
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parents[2]
TYPE_TRAVAIL = "prepare_brouillon_annonce_detail"
TABLE_CACHE = "app_brouillon_annonce_detail_cache"
SCRIPT = "Console/prepare_brouillon_annonce_detail.py"

echecs: list[str] = []


def controle(nom: str, condition: bool, detail: str = "") -> None:
    print(f"{'  OK  ' if condition else 'ECHEC '} {nom}{'' if condition else ' -- ' + detail}")
    if not condition:
        echecs.append(nom)


def lire(chemin: str) -> str:
    p = RACINE / chemin
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


WORKER = lire("Console/console_job_worker.js")
API = lire("apps/hektor-v1/src/lib/api.ts")
APP = lire("apps/hektor-v1/src/App.tsx")
PATCH = lire("supabase/patch_chantier7_piece2_detail_brouillon_2026-10-20.sql")
INVERSE = lire("supabase/patch_chantier7_piece2_detail_brouillon_2026-10-20_INVERSE.sql")
TEMOIN = lire("supabase/patch_chantier7_piece2_detail_brouillon_2026-10-20_REPETITION.sql")
SCRIPT_PY = lire(SCRIPT)

print(f"LE TYPE DE TRAVAIL : {TYPE_TRAVAIL}\n")

# ─────────── LES 5 ENDROITS DU CODE ───────────
controle("(1) le script python existe", bool(SCRIPT_PY), f"{SCRIPT} absent")
controle("(2) le worker le cite dans DEUX listes de routage",
         WORKER.count(f'"{TYPE_TRAVAIL}"') >= 2,
         f'{WORKER.count(chr(34) + TYPE_TRAVAIL + chr(34))} occurrence(s) entre guillemets')
controle("(3) le worker a son gestionnaire",
         "async function handlePrepareBrouillonAnnonceDetail(job)" in WORKER)
controle("(4) le routeur du worker l'aiguille",
         f'case "{TYPE_TRAVAIL}":' in WORKER and "return handlePrepareBrouillonAnnonceDetail(job);" in WORKER)
controle("(5) loadDossier connait le 4e index",
         "app_brouillon_annonce_index_current?" in WORKER,
         "la 4e branche manque -> « Dossier introuvable »")

# ─────────── LE FRONT ───────────
controle("(6) api.ts cree le travail",
         f"job_type: '{TYPE_TRAVAIL}'" in API,
         "le front ne sait pas le demander")
controle("(7) App.tsx a son gestionnaire ET l'importe",
         "handlePrepareBrouillonAnnonceDetail(dossier" in APP
         and "  createPrepareBrouillonAnnonceDetailJob," in APP,
         "gestionnaire ou import manquant")
controle("(8) ⭐ LE CUL-DE-SAC EST FERME : le message mort a disparu",
         "reprenez la saisie directement dans Hektor via le bouton" not in APP,
         "le bouton affiche encore le message au lieu de demander le cache")
controle("(9) et il appelle bien la demande",
         "await handlePrepareBrouillonAnnonceDetail(lightweightDetailTarget)" in APP)

# ─────────── LES 3 VERROUS (dans le patch a coller) ───────────
controle("(10) le patch SQL existe et cite le type",
         bool(PATCH) and PATCH.count(TYPE_TRAVAIL) >= 3,
         f"{PATCH.count(TYPE_TRAVAIL)} occurrence(s) -- il en faut au moins 3 (un par verrou)")
controle("(11) le patch touche les 3 verrous ET les droits",
         all(x in PATCH for x in ("app_console_job_job_type_check",
                                  "app_console_can_request_job",
                                  "app_console_claim_next_job",
                                  "app_console_can_access_dossier")))
controle("(12) l'inverse existe", bool(INVERSE) and TYPE_TRAVAIL in INVERSE)
controle("(13) le temoin existe", bool(TEMOIN) and TYPE_TRAVAIL in TEMOIN)

# ─────────── LA TABLE DU CACHE, ECRITE PAREIL PARTOUT ───────────
controle("(14) la table du cache est la MEME dans le script, le worker et le front",
         TABLE_CACHE in SCRIPT_PY and TABLE_CACHE in WORKER and TABLE_CACHE in API)

# ─────────── ⭐ LE CHEMIN DU SCRIPT, TEL QUE LE WORKER L'APPELLE ───────────
# Un chemin faux = « script introuvable » a l'execution, mais seulement quand
# quelqu'un cliquera. On le verifie MAINTENANT.
chemins = re.findall(r'"(Console/prepare_\w+\.py)"', WORKER)
manquants = [c for c in sorted(set(chemins)) if not (RACINE / c).exists()]
controle("(15) ⭐ tous les scripts que le worker appelle EXISTENT sur le disque",
         not manquants, f"introuvables : {manquants}")
controle("(16) et le notre est bien dans cette liste", SCRIPT in chemins, str(sorted(set(chemins))))

# ─────────── ⚠ AUCUNE VARIANTE ORTHOGRAPHIQUE ───────────
# Le mode de panne du projet : « detail » ecrit « details » a UN endroit sur huit.
variantes = set()
for texte in (WORKER, API, APP, PATCH, INVERSE, TEMOIN, SCRIPT_PY):
    for trouve in re.findall(r"prepare_brouillon\w*", texte):
        if trouve != TYPE_TRAVAIL:
            variantes.add(trouve)
controle("(17) ⚠ aucune variante orthographique du nom",
         not variantes, f"variantes trouvees : {sorted(variantes)}")

# ─────────── ⭐ LE TEMOIN INVERSE : LES DEUX SOEURS SONT INTACTES ───────────
for soeur, script_soeur in (("prepare_archived_annonce_detail", "Console/prepare_archived_annonce_detail.py"),
                            ("prepare_historical_annonce_detail", "Console/prepare_historical_annonce_detail.py")):
    ok = (WORKER.count(f'"{soeur}"') >= 2
          and f'case "{soeur}":' in WORKER
          and (RACINE / script_soeur).exists()
          and f"job_type: '{soeur}'" in API)
    controle(f"(18) TEMOIN INVERSE : {soeur} est intacte", ok,
             "j'ai casse une famille qui marchait")

# ─────────── ⚠ L'OPTION A EST RESPECTEE : LA FICHE RESTE EN LECTURE SEULE ───────────
# Frederic a choisi l'option A le 20/10 : on ouvre la fiche, on ne l'ouvre pas a
# l'ecriture. La ligne 426 d'App.tsx NE DOIT PAS avoir bouge.
controle("(19) ⭐ OPTION A tenue : le brouillon reste en LECTURE SEULE",
         "if ((item as { is_brouillon?: boolean }).is_brouillon === true) return true" in APP,
         "la ligne de lecture seule a bouge -- ce n'est PAS ce qui a ete decide")

# ═══ ⚠⚠ LECON 30, RENDUE MECANIQUE -- LE PIEGE QUI A FAILLI PASSER LE 20/10 ═══
#
# Dans un patch destine a etre COLLE, tout litteral « dollar-quote » qui tient sur
# PLUSIEURS LIGNES porte les fins de ligne DU FICHIER. Or git, sous Windows, passe
# ces .sql en CRLF au checkout -- alors que la source lue en base est normalisee par
# replace(..., chr(13), ''). Consequences, et la deuxieme est la pire :
#   · un BLOC INSERE non normalise met des CR dans le corps de la fonction ;
#   · une ANCRE non normalisee NE CORRESPOND A RIEN -> le retour arriere ne retire
#     rien EN SE CROYANT DEJA FAIT. Un inverse muet est pire qu'un inverse absent.
# ➡ Donc : tout litteral multi-ligne doit etre enveloppe dans replace(..., chr(13), '').
PATCHS = {
    "patch": "supabase/patch_chantier7_piece2_detail_brouillon_2026-10-20.sql",
    "inverse": "supabase/patch_chantier7_piece2_detail_brouillon_2026-10-20_INVERSE.sql",
    "temoin": "supabase/patch_chantier7_piece2_detail_brouillon_2026-10-20_REPETITION.sql",
}
def litteraux_non_normalises(texte: str, nom: str) -> list[str]:
    """Les litteraux dollar MULTI-LIGNE affectes a une variable et NON normalises."""
    trouves: list[str] = []
    # ⚠ ON NE REGARDE QUE LES DONNEES, pas le code : seuls les litteraux AFFECTES a
    #   une variable (ancre, bloc, remplace…) partent dans un `replace` ou un
    #   `EXECUTE`. Les $garde$ / $temoin$ qui enveloppent les blocs DO sont du code
    #   execute par Postgres : un CR dedans ne gene personne.
    for m in re.finditer(r"(\w+)\s*(?:text\s*)?:=\s*(replace\(\s*)?\$([a-z0-9]+)\$(.*?)\$\3\$",
                         texte, re.S):
        variable, enveloppe, tag, contenu = m.group(1), m.group(2), m.group(3), m.group(4)
        if "\n" not in contenu:
            continue                                    # une seule ligne : immunise
        if enveloppe:
            continue                                    # := replace($tag$ … ) : normalise
        # sinon : accepte une normalisation faite ailleurs dans le meme bloc, par
        #   <variable> := replace(<variable>, chr(13), '')
        ailleurs = re.search(re.escape(variable) + r"\s*:=\s*replace\(\s*"
                             + re.escape(variable) + r"\s*,\s*chr\(13\)", texte)
        if not ailleurs:
            ligne = texte[:m.start()].count("\n") + 1
            trouves.append(f"{nom}:{ligne} ({variable}, ${tag}$)")
    return trouves


# ⭐ LA PREUVE D'ABORD : un controle qui ne MORD PAS ne prouve rien. On lui donne
#   deux faux patchs -- un propre, un fautif -- et il doit trouver exactement l'un.
_FAUTIF = "DO $g$\nDECLARE\n  ancre text := $a$ligne un\nligne deux$a$;\nBEGIN\nEND\n$g$;"
_PROPRE = "DO $g$\nDECLARE\n  ancre text := replace($a$ligne un\nligne deux$a$, chr(13), '');\nBEGIN\nEND\n$g$;"
_mord = litteraux_non_normalises(_FAUTIF, "faux")
_epargne = litteraux_non_normalises(_PROPRE, "faux")
controle("(20) LA PREUVE D'ABORD : le controle lecon 30 MORD sur un cas fautif",
         len(_mord) == 1 and len(_epargne) == 0,
         f"fautif -> {_mord} (attendu 1) · propre -> {_epargne} (attendu 0)")
if len(_mord) != 1 or _epargne:
    print("\n⛔ LE CONTROLE (20) NE SAIT PAS DETECTER : le (21) ne prouverait RIEN.")
    sys.exit(2)

nus: list[str] = []
crlf: list[str] = []
for nom, chemin in PATCHS.items():
    brut = (RACINE / chemin).read_bytes()
    if b"\r\n" in brut:
        crlf.append(nom)
    nus += litteraux_non_normalises(brut.decode("utf-8", errors="replace"), nom)

controle("(21) ⚠⚠ LECON 30 : tout litteral MULTI-LIGNE est normalise chr(13)",
         not nus, f"non normalises : {nus}")
controle("(22) et les trois patchs sont en LF pur",
         not crlf, f"en CRLF : {crlf} -- a reecrire en LF avant de les coller")

print()
if echecs:
    print(f"{len(echecs)} controle(s) en ECHEC : " + ", ".join(echecs))
    sys.exit(1)
print("Les 8 endroits portent le meme nom, les deux familles soeurs sont intactes,")
print("et la fiche d'un brouillon reste en lecture seule comme decide.")
