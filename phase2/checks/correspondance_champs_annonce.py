# -*- coding: utf-8 -*-
"""N.1-(b) -- LA CORRESPONDANCE : nom du worker <-> colonne de l'app ou cle du blob.

POURQUOI CET OUTIL EXISTE
-------------------------
La carte A1 du 19/08 (notice/A1_CHAMPS_PROPRIETE_APP_2026-08-19.md) classe 189 champs
d'annonce en VERT / BLEU / ORANGE. Mais son paragraphe 6, « ce que je n'ai pas verifie »,
laisse un trou nomme :

    « La correspondance exacte entre chaque champ du worker et sa colonne ou sa cle de
      blob. Les noms different (title -> titre_bien + texte_principal_titre). A FAIRE
      AVANT A2, sinon on retire du paquet une colonne qui ne correspond a rien. »

C'est exactement le defaut que cet outil cherche. Retirer un champ du paquet de l'import
(le geste VERT) n'a d'effet QUE si l'on vise la bonne colonne : viser un nom qui n'existe
pas ne protege rien, et ne dit rien -- le run continue, la saisie est ecrasee en silence.

CE QU'IL FAIT, ET CE QU'IL NE FAIT PAS
--------------------------------------
Il rapproche des NOMS. Il ne mesure aucun comportement de Hektor : l'axe A/B/C
(« Hektor accepte-t-il l'ecriture ? ») est un autre travail, et il a besoin de celui-ci
pour savoir quelle colonne relire.

LECTURE SEULE. Aucun appel Hektor, aucune ecriture, aucune connexion a Supabase :
tout se lit dans le worker et dans le miroir local.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
WORKER = RACINE / "Console" / "console_job_worker.js"
BASE = RACINE / "phase2" / "phase2.sqlite"

# ON LIT TOUT. Pas d'echantillon.
#
# -- CE GARDE-FOU A ETE ECRIT APRES S'ETRE FAIT PRENDRE. La premiere version lisait les
#    4 000 premieres lignes et declarait PISCINE_CHAUFFEE, SHON, typeChauff, syndic et
#    terrain_viabilise ABSENTS de l'app. Ils y sont : 96, 111, 101, 250 et 48 lignes sur
#    13 439 -- tous au-dela du rang 4 000. Un echantillon pris dans l'ordre du fichier
#    n'est pas un echantillon : c'est un debut.
#    Un champ rare est precisement celui qu'on croira perdu. La base est locale et tient
#    en quelques secondes : il n'y a aucune raison de ne pas tout lire.
ECHANTILLON_BLOB = None

for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# --------------------------------------------------------------------------- worker
def _bloc_crochets(texte: str, depuis: int) -> str:
    """Le contenu du [ ... ] equilibre qui commence a partir de `depuis`."""
    i = texte.index("[", depuis)
    profondeur = 0
    for j in range(i, len(texte)):
        if texte[j] == "[":
            profondeur += 1
        elif texte[j] == "]":
            profondeur -= 1
            if profondeur == 0:
                return texte[i : j + 1]
    raise ValueError("crochet non ferme")


def champs_du_worker() -> dict[str, dict]:
    """Les 189 champs, avec leurs alias.

    Deux formes coexistent dans le worker, et il faut les lire differemment :
      - CLEANFIELD_*  : des PAIRES  [canonique, [alias...]]
      - WIZARD_*      : un objet profil -> liste de noms
    Compter les chaines sans distinguer les deux rend 9 + 81 au lieu de 27 + 26 --
    l'erreur a ete faite le 28/09 avant d'ouvrir le fichier.
    """
    s = WORKER.read_text(encoding="utf-8", errors="replace")
    champs: dict[str, dict] = {}

    for nom, famille in (
        ("HEKTOR_CLEANFIELD_TEXT_KEYS", "texte"),
        ("HEKTOR_CLEANFIELD_NUMBER_KEYS", "nombre"),
    ):
        bloc = _bloc_crochets(s, s.index(nom))
        for canon, alias_brut in re.findall(
            r"\[\s*['\"]([^'\"]+)['\"]\s*,\s*(\[[^\]]*\])", bloc
        ):
            alias = re.findall(r"['\"]([^'\"]+)['\"]", alias_brut)
            champs[canon] = {"famille": famille, "alias": sorted(set(alias) | {canon})}

    i = s.index("{", s.index("HEKTOR_WIZARD_FIELDS_BY_PROFILE"))
    profondeur = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            profondeur += 1
        elif s[j] == "}":
            profondeur -= 1
            if profondeur == 0:
                break
    for nom in sorted(set(re.findall(r"['\"]([^'\"]+)['\"]", s[i : j + 1]))):
        champs.setdefault(nom, {"famille": "equipement", "alias": [nom]})
    return champs


# ------------------------------------------------------------------------ l'app
# Le chemin le plus long mesure sur le blob fait SIX niveaux :
#   console_missing_fields_json / groups / <groupe> / editer / fields / <NOM>
# S'arreter a 6 coupe donc pile sur le dernier. On garde de la marge.
PROFONDEUR_MAX = 10

# LES SEPT QUE AUCUNE REGLE NE TROUVE -- resolus a la main, le 28/09, et verifies un par
# un contre les colonnes de app_view_generale.
#
# Ce ne sont pas sept oublis : ce sont EXACTEMENT les exceptions que la carte A1 nommait
# deja. Le rapprochement automatique tombe sur sa propre liste d'exceptions, ce qui est
# la meilleure preuve qu'on pouvait en attendre.
#   - title / description : le cas cite par A1 §6, mot pour mot
#   - les quatre mandate_* : les champs ORANGE, en attente de l'arbitrage de C.4
#   - private_postal      : le pendant de private_city, deja rapproche par suffixe
#
# -- title EST AMBIGU PAR NATURE, et c'est le piege de A1. titre_bien est un COALESCE qui
#    prefere ann.titre (le LISTING) a det.texte_principal_titre (le DETAIL). Pousser un
#    titre et le relire dans titre_bien peut donc rendre l'ancienne valeur sans que rien
#    n'echoue. La relecture doit viser texte_principal_titre.
TRADUCTION_A_LA_MAIN: dict[str, tuple[str, ...]] = {
    "title": ("texte_principal_titre", "titre_bien"),
    "description": ("texte_principal_html",),
    "private_postal": ("code_postal_prive_detail",),
    "mandate_number": ("numero_mandat",),
    "mandate_type": ("mandat_type",),
    "mandate_start_date": ("mandat_date_debut",),
    "mandate_end_date": ("mandat_date_fin",),
}


def _marcher(noeud, chemin: str, racine: dict, props: dict, profondeur: int = 0) -> None:
    """Descend dans le blob en OUVRANT les JSON ranges comme du texte.

    -- C'EST CE QUI A FAUSSE LA PREMIERE MESURE, le 28/09. Un rapprochement sur les
       seules cles de premier niveau rend « 180 absents sur 189 » et laisse croire que
       les noms du worker n'existent nulle part dans l'app. Ils existent. Ils sont a
       TROIS niveaux de profondeur :

           detail_payload_json -> equipements_json -> props -> ASCENSEUR -> value

       et le maillon du milieu est une CHAINE contenant du JSON, que json.loads ne
       traverse pas tout seul. Le nom, lui, est EXACT : « ASCENSEUR » cote worker,
       « ASCENSEUR » cote blob. Il n'y avait rien a traduire ; il y avait un chemin a
       suivre. Une mesure qui ne descend pas ne mesure pas l'absence : elle mesure sa
       propre profondeur.
    """
    if profondeur > PROFONDEUR_MAX:
        return
    if isinstance(noeud, str) and noeud[:1] in "[{":
        try:
            noeud = json.loads(noeud)
        except (TypeError, ValueError):
            return
    if isinstance(noeud, dict):
        # DEUX porteurs, pas un. « props » vient du detail d'API ; « fields » vient de
        # la capture de console (console_missing_fields_json/groups/<g>/editer/fields).
        # Ne lire que « props » laisse croire que les 12 diagnostics sont absents : ils
        # sont sous « fields », dans 12 814 lignes sur 13 439.
        for porteur in ("props", "fields"):
            if isinstance(noeud.get(porteur), dict):
                for nom in noeud[porteur]:
                    props.setdefault(nom, set()).add(f"{chemin}/{porteur}" if chemin else porteur)
        for cle, valeur in noeud.items():
            if profondeur == 0:
                racine[cle] = racine.get(cle, 0) + 1
            _marcher(valeur, f"{chemin}/{cle}", racine, props, profondeur + 1)
    elif isinstance(noeud, list):
        for element in noeud:
            _marcher(element, f"{chemin}[]", racine, props, profondeur + 1)


def univers_app() -> tuple[list[str], dict[str, int], dict[str, set]]:
    cx = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
    try:
        colonnes = [r[1] for r in cx.execute("PRAGMA table_info(app_view_generale)")]
        racine: dict[str, int] = {}
        props: dict[str, set] = {}
        requete = (
            "SELECT detail_payload_json FROM app_dossier_detail_current "
            "WHERE detail_payload_json IS NOT NULL"
        )
        if ECHANTILLON_BLOB:
            requete += f" LIMIT {int(ECHANTILLON_BLOB)}"
        for (brut,) in cx.execute(requete):
            try:
                charge = json.loads(brut)
            except (TypeError, ValueError):
                continue
            if isinstance(charge, dict):
                _marcher(charge, "", racine, props)
        return colonnes, racine, props
    finally:
        cx.close()


def _normaliser(nom: str) -> str:
    return re.sub(r"[^a-z0-9]", "", nom.lower())


# Cote app, un meme champ porte souvent d'ou il VIENT, pas ce qu'il EST :
# adresse_detail, ville_privee_detail, code_postal_public_listing, chauffage_console_json.
# Le worker, lui, ne connait que le champ. Retirer la provenance rapproche les deux.
SUFFIXES_DE_PROVENANCE = (
    "_console_json", "_console", "_detail", "_listing", "_json", "_html",
)


def _sans_provenance(nom: str) -> str:
    """Le nom prive de ce qui dit d'ou il vient. Une seule couche : on ne devine pas."""
    bas = nom.lower()
    for suffixe in SUFFIXES_DE_PROVENANCE:
        if bas.endswith(suffixe) and len(bas) > len(suffixe):
            return _normaliser(bas[: -len(suffixe)])
    return _normaliser(bas)


def main() -> int:
    champs = champs_du_worker()
    colonnes, cles_blob, props = univers_app()

    print(f"LES 189 CHAMPS DU WORKER : {len(champs)}")
    for f in ("texte", "nombre", "equipement"):
        print(f"   {f:12s} {sum(1 for v in champs.values() if v['famille'] == f):3d}")
    print("")
    print("L'UNIVERS DE L'APP, sur la TOTALITE du miroir local :")
    print(f"   {len(colonnes):3d} colonnes de app_view_generale")
    print(f"   {len(cles_blob):3d} cles au premier niveau du blob")
    print(f"   {len(props):3d} noms sous un porteur 'props' ou 'fields' (equipements, diagnostics)")
    print("")

    index: dict[str, list[tuple[str, str]]] = defaultdict(list)
    # La seconde carte est tenue A PART, et elle n'est consultee QUE si la premiere
    # est muette : un rapprochement par suffixe est une PISTE, pas une preuve.
    index_suffixe: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for c in colonnes:
        index[_normaliser(c)].append(("colonne", c))
        index_suffixe[_sans_provenance(c)].append(("colonne", c))
    for c in cles_blob:
        index[_normaliser(c)].append(("blob", c))
        index_suffixe[_sans_provenance(c)].append(("blob", c))
    for nom_prop, porteurs in props.items():
        porteur = sorted(porteurs)[0].lstrip("/") or "?"
        cible = ("blob", f"{porteur}/{nom_prop}")
        index[_normaliser(nom_prop)].append(cible)
        index_suffixe[_sans_provenance(nom_prop)].append(cible)

    verdicts: dict[str, list] = defaultdict(list)
    detail: dict[str, list[tuple[str, str]]] = {}
    for nom, info in sorted(champs.items()):
        trouves: list[tuple[str, str]] = []
        for alias in info["alias"]:
            for cible in index.get(_normaliser(alias), []):
                if cible not in trouves:
                    trouves.append(cible)
        a_la_main = False
        if not trouves and nom in TRADUCTION_A_LA_MAIN:
            trouves = [("a la main", c) for c in TRADUCTION_A_LA_MAIN[nom]]
            a_la_main = True
        par_suffixe = False
        if not trouves:
            for alias in info["alias"]:
                for cible in index_suffixe.get(_sans_provenance(alias), []):
                    if cible not in trouves:
                        trouves.append(cible)
            par_suffixe = bool(trouves)
        detail[nom] = trouves
        if a_la_main:
            verdicts["A LA MAIN"].append(nom)
        elif par_suffixe:
            verdicts["SUFFIXE"].append(nom)
        elif not trouves:
            verdicts["ABSENT"].append(nom)
        elif len(trouves) == 1:
            verdicts["UN SEUL"].append(nom)
        else:
            verdicts["AMBIGU"].append(nom)

    print("=" * 72)
    for etat in ("UN SEUL", "AMBIGU", "SUFFIXE", "A LA MAIN", "ABSENT"):
        noms = verdicts[etat]
        print(f"{etat:8s} {len(noms):3d} / {len(champs)}")
    print("=" * 72)

    if verdicts["AMBIGU"]:
        print("\nAMBIGUS -- plusieurs cibles pour un seul nom. C'est le cas 'title' de A1 :")
        for nom in verdicts["AMBIGU"]:
            cibles = ", ".join(f"{k}:{v}" for k, v in detail[nom])
            print(f"   {nom:32s} -> {cibles}")

    if verdicts["A LA MAIN"]:
        print("")
        print("A LA MAIN -- aucune regle ne les trouve ; la cible est ecrite en dur et verifiee.")
        for nom in verdicts["A LA MAIN"]:
            cibles = ", ".join(v2 for _, v2 in detail[nom])
            print(f"   {nom:32s} -> {cibles}")

    if verdicts["SUFFIXE"]:
        print("")
        print("PAR SUFFIXE -- le nom ne tombe juste qu'une fois la provenance retiree.")
        print("A CONFIRMER DANS LE CODE, un par un : c'est une piste, pas une preuve.")
        for nom in verdicts["SUFFIXE"]:
            cibles = ", ".join(f"{k}:{v}" for k, v in detail[nom])
            print(f"   {nom:32s} -> {cibles}")

    if verdicts["ABSENT"]:
        print(f"\nABSENTS -- aucune colonne ni cle de blob ne porte ce nom ({len(verdicts['ABSENT'])}) :")
        for i in range(0, len(verdicts["ABSENT"]), 3):
            print("   " + "".join(f"{n:34s}" for n in verdicts["ABSENT"][i : i + 3]))
        print("\n   ATTENTION : 'absent' ne veut pas dire 'perdu'. Il veut dire que le nom")
        print("   ne suffit pas a trouver la cible -- il faudra la lire dans le code.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
