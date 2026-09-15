#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE MIROIR CONSOLE ENTRE DANS LE REGISTRE DES AFFAIRES.      16/09/2026

Demande de Frederic, 16/09 : « je voulais que le rattrapage et l'entretien
quotidien console pour notaire et le reste soient recuperes comme une sorte de
miroir de Hektor puis envoyes au registre des affaires ou il y a les chaines,
sur le serveur et l'app ».

CE QUE FAIT CE PROGRAMME, EN UNE PHRASE
---------------------------------------
Il prend ce que la console a lu chez Hektor -- les deux notaires, le taux
d'honoraire VENDEUR, les unites de partage -- et le range dans
`app_affaire_ledger`, le registre dont LE SERVEUR EST LE MAITRE.

POURQUOI, ET C'EST LE MEME GESTE QUE LA REPARTITION LE 15/09
-----------------------------------------------------------
`app_affaire_console` est un MIROIR : une recopie du formulaire de Hektor. Le
jour ou l'acces s'arrete, plus personne ne sait la relire ni la regenerer. Le
registre, lui, est a nous -- et il est deja du bon cote de la frontiere que la
descente trace elle-meme :

    app_affaire_ledger        creee par la descente : NON  -> serveur maitre
    app_affaire_console       creee par la descente : OUI  -> copie du cloud

Donc : on LIT le miroir (en local), on ECRIT le registre (en local), et le push
existant porte le tout vers l'app. Aucun ecrivain de plus, aucun sens inverse.

⚠ ON NE FAIT QUE LIRE `app_affaire_console`. Y ecrire depuis le serveur serait
  efface au matin suivant : la descente remplace cette table entiere chaque jour.

LA REGLE DE FUSION, MESUREE AVANT D'ETRE ECRITE (16/09)
-------------------------------------------------------
    vente      L'API D'ABORD. Cote par cote sur 9 223 ventes : 9 223 accords,
               27 contradictions (0,3 %), 2 377 cotes ou l'API parle SEULE --
               et ZERO ou la console parle seule. Preferer la console y perdrait
               2 377 notaires.
    compromis  LA CONSOLE SEULE. L'API est aveugle : 0 notaire sur 10 599.
    offre      PERSONNE. Il n'existe pas d'assistant a ouvrir pour une offre --
               ce n'est pas un oubli, c'est la forme de Hektor.

⚠ LES CONTRADICTIONS SONT COMPTEES ET NOMMEES, jamais avalees. 27 aujourd'hui.

⚠ `entree` = LE NOTAIRE DE L'ACQUEREUR, `sortie` = CELUI DU MANDANT.
  C'est l'inverse de ce que le schema affirmait jusqu'au 16/09, et l'inverse de
  ce que l'analogie avec les honoraires d'entree suggere. Mesure : sur 366
  ventes dont les deux cotes different, entree = acquereur 366 fois, l'inverse
  0 fois. Ne pas « recorriger » sans refaire la mesure.

⚠ UNE SAISIE HUMAINE N'EST JAMAIS ECRASEE. Une ligne dont `notaires_origine`
  vaut 'saisie' est laissee telle quelle -- meme principe que la garde de
  `app_repartition_absorber`, en local cette fois puisque le registre est local.

    python phase2/sync/registre_depuis_console.py            # a blanc
    python phase2/sync/registre_depuis_console.py --ecrire
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

from push_contacts_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES,
    SupabaseRestClient,
    load_env_file,
)

PHASE2_DB = RACINE / "phase2" / "phase2.sqlite"
LEDGER = "app_affaire_ledger"
CONSOLE = "app_affaire_console"


def _texte(valeur: Any) -> str:
    return "" if valeur is None else str(valeur).strip()


def _charger(brut: Any) -> Any:
    """Un JSON qui peut arriver en texte ou deja decode. Jamais d'exception."""
    if brut is None:
        return None
    if isinstance(brut, (dict, list)):
        return brut
    t = _texte(brut)
    if not t:
        return None
    try:
        return json.loads(t)
    except (ValueError, TypeError):
        return None


def _nom_de_fiche(fiche: dict[str, Any]) -> str:
    """Le nom tel qu'on l'ecrit partout ailleurs : civilite prenom nom."""
    morceaux = [_texte(fiche.get("civilite")), _texte(fiche.get("prenom")),
                _texte(fiche.get("nom"))]
    return " ".join(m for m in morceaux if m).strip()


def notaires_de_l_api(brut: Any) -> dict[str, tuple[str, str]]:
    """{ 'acquereur': (id, nom), 'mandant': (id, nom) } depuis `notaires_json`.

    ⚠ entree = ACQUEREUR, sortie = MANDANT. Voir l'avertissement en tete.
    """
    objet = _charger(brut)
    sortie = {"acquereur": ("", ""), "mandant": ("", "")}
    if not isinstance(objet, dict):
        return sortie
    for cle, role in (("entree", "acquereur"), ("sortie", "mandant")):
        fiche = objet.get(cle)
        if isinstance(fiche, dict):
            sortie[role] = (_texte(fiche.get("id")), _nom_de_fiche(fiche))
    return sortie


def notaires_de_la_console(parties: Any, ids_acq: Any, ids_man: Any) -> dict[str, tuple[str, str]]:
    """Le PREMIER notaire de chaque cote, avec son nom quand la console l'a lu.

    ⚠ ON NE FABRIQUE RIEN : pas de nom releve -> pas de nom. Un identifiant sans
      nom reste un identifiant honnete.
    """
    resultat = {"acquereur": ("", ""), "mandant": ("", "")}
    bloc = _charger(parties) or {}
    for role, colonne, cle_bloc in (("acquereur", ids_acq, "notaires_acquereur"),
                                    ("mandant", ids_man, "notaires_mandant")):
        identifiant, nom = "", ""
        liste = _charger(colonne)
        if isinstance(liste, list) and liste:
            premier = liste[0]
            identifiant = _texte(premier.get("id") if isinstance(premier, dict) else premier)
        detaillee = bloc.get(cle_bloc) if isinstance(bloc, dict) else None
        if isinstance(detaillee, list):
            for partie in detaillee:
                if not isinstance(partie, dict):
                    continue
                if not identifiant:
                    identifiant = _texte(partie.get("id"))
                if _texte(partie.get("id")) == identifiant:
                    nom = _texte(partie.get("nom"))
                    break
        resultat[role] = (identifiant, nom)
    return resultat


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    # Le calcul est TOUJOURS fait et affiche ; `--ecrire` est ce qui pose.
    ap.add_argument("--ecrire", action="store_true",
                    help="Ecrire dans le registre. Sans lui, rien n'est modifie.")
    # ─── POURQUOI CETTE ETAPE POUSSE ELLE-MEME ───
    #
    # Le push du registre (`affaire_ledger.py --push`) tourne AVANT les deux
    # entretiens console, donc avant que cette etape ait de quoi travailler. Sans
    # envoi ici, ce qu'on vient de poser attendrait la nuit SUIVANTE pour arriver
    # dans l'app -- un jour de retard, tous les jours.
    #
    # ⚠ ON N'ENVOIE QUE LES HUIT COLONNES, avec la cle. PostgREST en mode
    #   merge-duplicates ne met a jour que les champs fournis : `state`, `montant`
    #   et tout le reste de la ligne ne sont pas touches. C'est ce qui rend cet
    #   envoi sans danger la ou `--push` complet, lance seul en pleine journee,
    #   avait efface une annulation le 07/09.
    ap.add_argument("--pousser", action="store_true",
                    help="Envoyer les colonnes posees vers Supabase (upsert partiel).")
    # ⚠ POUR LE PREMIER REMPLISSAGE, ET POUR LUI SEUL. `--pousser` n'envoie que ce
    #   que l'execution vient d'ecrire -- quelques lignes par nuit. Le jour ou le
    #   registre est deja rempli en local mais pas en ligne (premiere mise en
    #   service, ou restauration), il faut pouvoir tout renvoyer une fois.
    ap.add_argument("--tout", action="store_true",
                    help="Envoyer TOUTES les lignes qui portent une valeur, pas seulement les nouvelles.")
    ap.add_argument("--db", default=str(PHASE2_DB))
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    try:
        colonnes = {r[1] for r in con.execute(f"PRAGMA table_info({LEDGER})")}
        manquantes = [c for c in ("notaire_acquereur_id", "notaire_mandant_id",
                                  "taux_honoraire_entree", "notaires_origine")
                      if c not in colonnes]
        if manquantes:
            print("Le registre n'a pas encore ses colonnes :", ", ".join(manquantes))
            print("Lancer `affaire_ledger.py` d'abord : c'est lui qui les ajoute.")
            return 2

        # ─── LE MIROIR, EN MEMOIRE, EN UN SEUL PASSAGE ───
        # La copie locale de app_affaire_console n'a pas d'index (elle est creee
        # par la descente). Une jointure SQL balaierait la table pour chaque
        # affaire -- mesure du 15/09 sur un cas voisin : plus de sept minutes.
        miroir: dict[int, sqlite3.Row] = {}
        for ligne in con.execute(
                f"SELECT app_affaire_id, kind, notaires_acquereur, notaires_mandant, "
                f"parties_json, taux_honoraire_entree, unites_entree_percent, "
                f"unites_sortie_percent FROM {CONSOLE}"):
            miroir[int(ligne["app_affaire_id"])] = ligne

        resume = {"lues": len(miroir), "ecrites": 0, "inchangees": 0,
                  "protegees": 0, "sans_lecture": 0,
                  "notaire_api": 0, "notaire_console": 0, "contradictions": 0}
        exemples: list[str] = []
        a_poser: list[tuple] = []

        for ligne in con.execute(
                f"SELECT app_affaire_id, kind, notaires_json, notaires_origine, "
                f"notaire_acquereur_id, notaire_acquereur_nom, notaire_mandant_id, "
                f"notaire_mandant_nom, taux_honoraire_entree, unites_entree_percent, "
                f"unites_sortie_percent FROM {LEDGER}"):
            aff = int(ligne["app_affaire_id"])
            # ⚠ LA SAISIE HUMAINE EST INTOUCHABLE, et c'est le seul cas ou l'on
            #   passe son chemin sans rien regarder.
            if _texte(ligne["notaires_origine"]) == "saisie":
                resume["protegees"] += 1
                continue
            lecture = miroir.get(aff)
            api = notaires_de_l_api(ligne["notaires_json"])
            console = (notaires_de_la_console(lecture["parties_json"],
                                              lecture["notaires_acquereur"],
                                              lecture["notaires_mandant"])
                       if lecture is not None else
                       {"acquereur": ("", ""), "mandant": ("", "")})
            if lecture is None and not any(api[r][0] for r in api):
                resume["sans_lecture"] += 1
                continue

            retenu: dict[str, tuple[str, str]] = {}
            origine = ""
            for role in ("acquereur", "mandant"):
                id_api, nom_api = api[role]
                id_con, nom_con = console[role]
                if id_api and id_con and id_api != id_con:
                    resume["contradictions"] += 1
                    if len(exemples) < 10:
                        exemples.append(f"affaire {aff} ({ligne['kind']}) {role} : "
                                        f"API {id_api} / console {id_con}")
                # L'API D'ABORD quand elle parle : mesure du 16/09, elle est
                # strictement plus riche la ou elle voit (2 377 cotes contre 0).
                if id_api:
                    retenu[role] = (id_api, nom_api or nom_con)
                    origine = origine or "api"
                elif id_con:
                    retenu[role] = (id_con, nom_con)
                    origine = origine or "console"
                else:
                    retenu[role] = ("", "")
            if retenu["acquereur"][0] or retenu["mandant"][0]:
                resume["notaire_api" if origine == "api" else "notaire_console"] += 1

            taux = _texte(lecture["taux_honoraire_entree"]) if lecture is not None else ""
            u_e = _texte(lecture["unites_entree_percent"]) if lecture is not None else ""
            u_s = _texte(lecture["unites_sortie_percent"]) if lecture is not None else ""

            neuf = (retenu["acquereur"][0], retenu["acquereur"][1],
                    retenu["mandant"][0], retenu["mandant"][1],
                    taux, u_e, u_s, origine or None)
            ancien = (_texte(ligne["notaire_acquereur_id"]), _texte(ligne["notaire_acquereur_nom"]),
                      _texte(ligne["notaire_mandant_id"]), _texte(ligne["notaire_mandant_nom"]),
                      _texte(ligne["taux_honoraire_entree"]),
                      _texte(ligne["unites_entree_percent"]),
                      _texte(ligne["unites_sortie_percent"]),
                      _texte(ligne["notaires_origine"]) or None)
            # ⚠ VIDE N'EFFACE PAS. Si la console n'a rien lu cette fois-ci, on ne
            #   retire pas ce qu'une lecture precedente avait pose.
            if not any(neuf[:7]):
                resume["inchangees"] += 1
                continue
            if neuf == ancien:
                resume["inchangees"] += 1
                continue
            a_poser.append(neuf + (aff, ligne["kind"]))

        print("-- CE QUE LE MIROIR CONSOLE DONNE AU REGISTRE --")
        print(f"   lectures console disponibles     {resume['lues']:>7}")
        print(f"   notaires venus de l'API          {resume['notaire_api']:>7}")
        print(f"   notaires venus de la CONSOLE     {resume['notaire_console']:>7}")
        print(f"   lignes a ecrire                  {len(a_poser):>7}")
        print(f"   deja a jour                      {resume['inchangees']:>7}")
        print(f"   protegees (saisie humaine)       {resume['protegees']:>7}")
        print(f"   sans aucune source               {resume['sans_lecture']:>7}")
        print(f"   CONTRADICTIONS api/console       {resume['contradictions']:>7}")
        for exemple in exemples:
            print(f"      {exemple}")
        if exemples and resume["contradictions"] > len(exemples):
            print(f"      ... et {resume['contradictions'] - len(exemples)} autres")

        if not args.ecrire:
            print("a blanc : RIEN n'a ete ecrit. Ajouter --ecrire.")
            return 0

        con.executemany(
            f"""UPDATE {LEDGER} SET notaire_acquereur_id = ?, notaire_acquereur_nom = ?,
                   notaire_mandant_id = ?, notaire_mandant_nom = ?,
                   taux_honoraire_entree = ?, unites_entree_percent = ?,
                   unites_sortie_percent = ?, notaires_origine = ?
                 WHERE app_affaire_id = ?""", [l[:9] for l in a_poser])
        con.commit()
        resume["ecrites"] = len(a_poser)
        print(f"   ECRITES                          {resume['ecrites']:>7}")

        if not args.pousser:
            print("   Pas d'envoi : le push du registre les portera la nuit suivante.")
            return 0
        a_envoyer = a_poser
        if args.tout:
            a_envoyer = [tuple(r) for r in con.execute(f"SELECT notaire_acquereur_id, notaire_acquereur_nom, notaire_mandant_id, notaire_mandant_nom, taux_honoraire_entree, unites_entree_percent, unites_sortie_percent, notaires_origine, app_affaire_id, kind FROM {LEDGER} WHERE COALESCE(notaire_acquereur_id, '') <> ''    OR COALESCE(notaire_mandant_id, '') <> ''    OR COALESCE(taux_honoraire_entree, '') <> ''")]
            print(f"   --tout : {len(a_envoyer)} ligne(s) a renvoyer")
        if not a_envoyer:
            print("   Rien a envoyer.")
            return 0
        for fichier in DEFAULT_ENV_FILES:
            load_env_file(fichier)
        url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
        cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not cle:
            print("!! SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents", file=sys.stderr)
            return 1
        client = SupabaseRestClient(base_url=url, service_role_key=cle)
        lignes = [{
            "app_affaire_id": ligne[8],
            # ⚠ `kind` EST OBLIGATOIRE DANS LA CHARGE, MEME EN MISE A JOUR.
            #   Postgres verifie les NOT NULL de la ligne PROPOSEE avant de
            #   detecter le conflit : un upsert partiel sans `kind` echoue en
            #   « null value in column kind », meme quand la ligne existe deja.
            #   Mesure du 16/09, deux essais. La valeur est la notre, inchangee.
            "kind": ligne[9],
            "notaire_acquereur_id": ligne[0] or None,
            "notaire_acquereur_nom": ligne[1] or None,
            "notaire_mandant_id": ligne[2] or None,
            "notaire_mandant_nom": ligne[3] or None,
            "taux_honoraire_entree": ligne[4] or None,
            "unites_entree_percent": ligne[5] or None,
            "unites_sortie_percent": ligne[6] or None,
            "notaires_origine": ligne[7],
        } for ligne in a_envoyer]
        # ⚠  EXPLICITE, ET C'EST INDISPENSABLE ICI. La table porte DEUX
        #   index uniques -- la cle primaire et le triplet (annonce, genre, numero
        #   Hektor). Sans cette precision, PostgREST a tente un INSERT et Postgres
        #   a refuse : « null value in column kind ». Mesure du 16/09, au premier essai.
        envoyees = client.upsert_rows("app_affaire_ledger?on_conflict=app_affaire_id",
                                      lignes, batch_size=400)
        print(f"   ENVOYEES vers l'app              {envoyees:>7}")
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
