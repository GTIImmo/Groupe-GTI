# -*- coding: utf-8 -*-
"""A.3 — LES MANDATS DE RECHERCHE DANS LE REGISTRE AFFICHE.     16/10/2026

Produit, pour le fabricant du registre, les lignes des mandats QUI N'ONT PAS DE
BIEN. ⚠ Ce module ne modifie rien : il RAJOUTE des lignes à côté.

═══════════════════════════════════════════════════════════════════════════════
POURQUOI UN MODULE À PART, ET PAS UNE RETOUCHE DU FABRICANT
═══════════════════════════════════════════════════════════════════════════════
`build_mandat_register_rows` ENUMERE LES ANNONCES (`FROM hektor.hektor_annonce`)
puis leur attache leurs mandats. Un mandat de recherche n'a pas d'annonce : il
ne peut pas entrer par cette porte, et élargir la requête obligerait à toucher
2 600 lignes de code qui marchent.

On produit donc les lignes À CÔTÉ, au MÊME FORMAT, et on les ajoute à la liste.
Si ce module échoue, le registre est exactement celui d'avant — rien ne casse.

═══════════════════════════════════════════════════════════════════════════════
CE QU'UNE LIGNE DE RECHERCHE MET DANS LES COLONNES DU BIEN
═══════════════════════════════════════════════════════════════════════════════
Les 9 colonnes de l'écran gardent leur sens, elles changent de SOURCE :

    N° de mandat          le numéro · numero_dossier reste VIDE
    Statut du mandat      calculé sur les dates -- identique, aucun code
    État                  l'état de LA RECHERCHE (Active / Archivée / —)
    Dates début/fin       identiques
    Montant               le BUDGET de la recherche (prix_max)
    Mandant(s)            le chercheur -- déjà dans mandants_texte
    Nature et situation   les types cherchés + les communes
    Actions               le front décidera (fiche contact)

⚠ AUCUNE COLONNE AJOUTÉE À LA TABLE. On remplit celles qui existent.

═══════════════════════════════════════════════════════════════════════════════
LE RATTACHEMENT À UNE RECHERCHE — mesuré sur les 38, le 15/10
═══════════════════════════════════════════════════════════════════════════════
    19  le contact a EXACTEMENT une recherche   -> c'est elle
     2  le contact en a plusieurs               -> la COMMUNE du registre légal
                                                   tranche (18682 « Issoire 63500 »
                                                   désigne la recherche 0, pas la 1)
    11  le contact n'a AUCUNE recherche         -> la ligne existe quand même, et
                                                   elle le DIT. Un mandat signé sans
                                                   recherche saisie est une
                                                   information, pas un trou.
     6  pas de contact identifié                -> la ligne existe aussi

⭐ ON N'INVENTE JAMAIS DE RATTACHEMENT. Quand plusieurs recherches restent
  possibles et qu'aucune commune ne tranche, on n'en choisit AUCUNE et la
  colonne reste au niveau du contact.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _sans_accent(texte) -> str:
    return unicodedata.normalize("NFKD", str(texte or "")).encode(
        "ascii", "ignore").decode().upper().strip()


def _types_json(brut):
    """Les types cherches. ⚠ CE N'EST PAS UNE LISTE : c'est un OBJET
    {code: libelle} -- mesure du 16/10 : {"1":"Maison"}.

    ⭐ On RECOPIE la regle du front (contactSearchTypes, App.tsx:35632) plutot
      que d'en inventer une : on garde les entrees "vraies", et on prend le
      LIBELLE quand il y en a un, la clef sinon. Mon premier lecteur traitait
      l'objet comme une liste et rendait VIDE partout.
    """
    try:
        valeur = json.loads(brut or "{}")
    except Exception:
        return []
    if not isinstance(valeur, dict):
        return _liste_json(brut)
    out = []
    for clef, libelle in valeur.items():
        texte = str(libelle if libelle is not None else "").strip()
        vrai = libelle is True or libelle == 1 or texte.lower() not in ("", "0", "false")
        if not vrai:
            continue
        out.append(texte if texte and texte != "1" else str(clef))
    return [x for x in out if x]


def _liste_json(brut):
    try:
        valeur = json.loads(brut or "[]")
    except Exception:
        return []
    # ⚠ Un blob peut être une LISTE ou un OBJET SEUL (leçon du projet).
    if isinstance(valeur, dict):
        valeur = [valeur]
    if not isinstance(valeur, list):
        return []
    out = []
    for item in valeur:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
        elif isinstance(item, dict):
            for clef in ("ville", "libelle", "nom", "label", "name"):
                if item.get(clef):
                    out.append(str(item[clef]).strip())
                    break
    return out


def _choisir_recherche(recherches, commune):
    """LA recherche que ce mandat couvre, ou None si on ne peut pas trancher.

    ⭐ Une seule -> c'est elle. Plusieurs -> seule la COMMUNE du registre légal
      tranche, et seulement si elle désigne UNE seule recherche. Sinon None :
      on préfère ne rien dire à dire peut-être.
    """
    if not recherches:
        return None
    if len(recherches) == 1:
        return recherches[0]
    if not commune:
        return None
    cible = _sans_accent(commune)
    retenues = []
    for rech in recherches:
        for ville in _liste_json(rech["villes_json"]):
            v = _sans_accent(ville)
            if v and (v in cible or cible in v):
                retenues.append(rech)
                break
    return retenues[0] if len(retenues) == 1 else None


def charger_mandats_sans_bien(con: sqlite3.Connection) -> list[dict]:
    """Les lignes de registre des mandats portés par un CONTACT.

    Rend une liste au format de `build_mandat_register_rows`. Liste vide si la
    colonne `app_contact_id` n'existe pas encore (environnement plus ancien) :
    ⚠ on ne fait jamais tomber le registre entier pour une colonne manquante.
    """
    colonnes = {r[1] for r in con.execute("PRAGMA table_info(app_mandat)")}
    if "app_contact_id" not in colonnes:
        return []

    # ── les recherches, par contact, en UNE lecture (pas une par mandat)
    recherches_par_contact: dict[str, list[dict]] = {}
    try:
        for ligne in con.execute(
                "SELECT hektor_contact_id, search_index, is_active, villes_json,"
                "       types_json, prix_min, prix_max"
                "  FROM app_contact_search_current"):
            recherches_par_contact.setdefault(str(ligne[0]), []).append({
                "search_index": ligne[1], "is_active": ligne[2],
                "villes_json": ligne[3], "types_json": ligne[4],
                "prix_min": ligne[5], "prix_max": ligne[6],
            })
    except sqlite3.OperationalError:
        recherches_par_contact = {}      # table absente : on continue sans

    lignes: list[dict] = []
    for (numero, app_contact_id, type_mandat, date_debut, date_fin,
         date_cloture, mandants, note, payload_json, versions_json,
         avenants_json, famille, source_app) in con.execute(
            "SELECT numero_mandat, app_contact_id, type, date_debut, date_fin,"
            "       date_cloture, mandants_texte, note, payload_json,"
            "       versions_json, avenants_json, famille, source_app"
            "  FROM app_mandat WHERE hektor_annonce_id = ''"):
        numero = str(numero or "").strip()
        if not numero:
            continue
        try:
            payload = json.loads(payload_json or "{}")
        except Exception:
            payload = {}
        commune = None
        situation_brute = str((payload or {}).get("situation") or "")
        # ⭐ CE QUE LE MANDAT COUVRE, EN TOUTES LETTRES (pose le 16/10).
        #   Elle vient de `product_recap` (export) ou de la colonne 8 du
        #   registre legal. ⚠ Elle NE SERT PAS a choisir la recherche : voir
        #   le bloc de importer_mandats_recherche.py -- une designation decrit
        #   souvent un bien DEJA trouve, et sa commune n'est pas celle cherchee.
        designation = str((payload or {}).get("designation") or "").strip()
        if situation_brute:
            from phase2.sync.importer_mandats_recherche import commune_cherchee
            commune = commune_cherchee(situation_brute)

        recherches = recherches_par_contact.get(str(app_contact_id or ""), [])
        rech = _choisir_recherche(recherches, commune)

        # ── « Nature et situation » : ce qu'il cherche, et où
        types = _types_json(rech["types_json"]) if rech else []
        villes = _liste_json(rech["villes_json"]) if rech else []
        if not villes and commune:
            villes = [commune]
        situation = " · ".join(x for x in (" / ".join(types[:3]), ", ".join(villes[:3])) if x)

        # ⭐ LE REPLI, QUAND AUCUNE RECHERCHE N'EST SAISIE — 17 des 38.
        #   La colonne du front lit `type_bien` puis `ville`, et ecrit
        #   « Recherche » d'elle-meme quand le type manque
        #   (mandateRegisterNatureParts, App.tsx:9239). En versant la phrase
        #   dans la ligne d'adresse, la colonne rend :
        #       Recherche
        #       Maison de ville sise 22 avenue Marechal Foch - 63120 COURPIERE
        #   ⭐ ZERO LIGNE DE FRONT A CHANGER. Et `villes` reste propre pour le
        #     payload de detail : on ne salit pas la donnee pour remplir une case.
        col_type = " / ".join(types[:3]) or None
        col_ville = (villes[0] if villes else None)
        if not col_type and not col_ville and designation:
            col_ville = designation
        if not situation:
            situation = designation or None

        # ── « État » : celui de la recherche, pas d'une annonce
        if rech is None:
            etat = "Sans recherche" if app_contact_id else "Contact inconnu"
        else:
            etat = "Recherche active" if rech["is_active"] else "Recherche archivée"

        budget = (rech or {}).get("prix_max") or (rech or {}).get("prix_min")

        # ⭐ LA CLE : « C<contact>:<numero> ». Elle ne peut pas heurter celles des
        #   biens, qui valent « <annonce>:<numero> » -- une annonce est numerique.
        cle = f"C{app_contact_id}:{numero}" if app_contact_id else f"C:{numero}"

        lignes.append({
            "register_row_id": cle,
            "corps_suspect": 0,
            "app_dossier_id": None,
            "hektor_annonce_id": None,     # ⚠ rendu facultatif le 15/10, table d'affichage
            "numero_dossier": None,
            "numero_mandat": numero,
            # ── le mandat lui-meme
            "mandat_source_id": None,
            "mandat_numero_reference": numero,
            "mandat_type": type_mandat,
            "mandat_type_source": type_mandat,
            "mandat_date_debut": date_debut,
            "mandat_date_fin": date_fin,
            "mandat_date_cloture": date_cloture,
            "mandat_montant": None,
            "mandants_texte": mandants,
            "mandants_json": None,
            "mandat_note": note,
            # ── ce que la recherche met dans les colonnes du bien
            "titre_bien": situation or None,
            "type_bien": col_type,
            "ville": col_ville,
            "prix": budget,
            "statut_annonce": etat,
            "adresse_privee_listing": None,
            "adresse_detail": None,
            "code_postal": None,
            "code_postal_prive_detail": None,
            "ville_privee_detail": None,
            "photo_url_listing": None,
            "images_preview_json": None,
            "commerce_sous_type": None,
            "offre_type": None,
            "archive": "0",
            "diffusable": "0",
            # ── les colonnes OBLIGATOIRES de la table d'affichage
            "nb_portails_actifs": 0,
            "has_diffusion_error": False,
            "register_detail_available": False,
            "register_version_count": 1,
            "register_embedded_avenant_count": 0,
            "price_change_event_count": 0,
            # ⭐ LE TRI : groupe 1 comme les mandats hors serie courante, et le
            #   numero pour l'ordre. Sans cela ils tomberaient tous a 0 et se
            #   grouperaient en bout de liste (le tri fait -int(annonce or 0)).
            "register_sort_group": 1,
            "register_sort_num": int("".join(c for c in numero if c.isdigit()) or 0),
            "register_source_kind": "recherche",
            "register_history_json": versions_json,
            "register_avenants_json": avenants_json,
            "register_detail_payload_json": json.dumps(
                {"mandat_de_recherche": True, "situation": situation_brute or None,
                 "designation": designation or None,
                 "commune_cherchee": commune, "source": source_app,
                 "recherche_index": (rech or {}).get("search_index"),
                 "budget_min": (rech or {}).get("prix_min"),
                 "budget_max": (rech or {}).get("prix_max"),
                 "types": types, "villes": villes},
                ensure_ascii=True, separators=(",", ":")),
            "affaires_detail_json": None,
            "commercial_id": None,
            "commercial_nom": None,
            "negociateur_email": None,
            "agence_nom": (payload or {}).get("agence") or None,
            "validation_diffusion_state": None,
            "portails_resume": None,
            "priority": None,
            "offre_id": None, "offre_state": None,
            "offre_last_proposition_type": None,
            "compromis_id": None, "compromis_state": None, "vente_id": None,
            "source_updated_at": None,
            "price_change_last_source_kind": None,
            "price_change_last_old_value": None,
            "price_change_last_new_value": None,
            "price_change_last_detected_at": None,
            "price_change_last_source_updated_at": None,
        })
    return lignes
