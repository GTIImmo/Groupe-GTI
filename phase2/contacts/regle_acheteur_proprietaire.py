# -*- coding: utf-8 -*-
"""L'ACHETEUR D'UNE VENTE N'EST PAS LE MANDANT DU BIEN QU'IL A ACHETE.   26/10/2026

⑧ · chantier des types, chantier 1 (C3 + D5 a/c) -- note
notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §7 et §8.

LE DEFAUT
---------
Depuis le 17/07/2026, a chaque VENTE, Hektor ajoute l'acheteur aux proprietaires
du bien, et le type « mandant » (mesure chez lui le 26/10 : 125 acheteurs sur 125).
Notre nuit le recopie, puis QUATRE endroits le disent « mandant » parce que le bien
porte un numero de mandat : la nuit (les types de l'annuaire), le registre des
liens, la vue des liens d'un contact, et le registre des mandats.
Mesure du 26/10 sur les transactions depuis le 17/07 : 92 acheteurs sur 92 rangés
proprietaires A LA VENTE ; au compromis seul 1 sur 72, a l'offre seule 5 sur 119.

LA DECISION DE FREDERIC (D2, 26/10)
-----------------------------------
« L'acheteur devient nouveau proprietaire DATE DE L'ACTE, sans etre mandant. »
Et D3 : le vendeur reste « Mandant » (mandat clos). Et s'il REVEND un jour, un
nouveau mandat le nommera : il redevient mandant.

LE CRITERE -- ET POURQUOI LE NOM DU MANDAT
------------------------------------------
Un lien « proprietaire » est un lien NE D'UNE VENTE quand :
    1. la personne est ACQUEREUR D'UNE VENTE de ce bien ;
    2. son nom N'EST PAS dans le texte d'un mandat de ce bien, TEL QUE HEKTOR L'A
       DONNE (`payload_json` / `versions_json` d'app_mandat, garde meme mandat
       clos -- et surtout pas `mandants_texte`, voir _textes_hektor_du_mandat) ;
    3. son nom est CONNU (une fiche sans nom ne se juge pas).
⭐ Le 2 n'est pas une coquetterie : chez Hektor, 10 acheteurs sur 125 sont NOMMES
   dans le texte du mandat -- des ventes anciennes (2007 -> 2021), de VRAIS
   mandants. Sans ce test, la regle les aurait declasses (D5 b : on n'y touche pas).
⚠ SA LIMITE, CONNUE ET VOULUE : un acheteur qui porte le MEME NOM qu'un vendeur
   (un enfant qui rachete a ses parents) est juge « nomme » et reste mandant. La
   regle se trompe alors du cote PRUDENT : elle ne declasse personne a tort.

CE QUE CE MODULE FAIT, ET NE FAIT PAS
-------------------------------------
Il DIT, pour une liste de liens, lesquels sont nes d'une vente, et depuis quand.
Il n'ecrit rien, n'appelle ni Hektor ni Supabase. Deux lecteurs, la meme regle :
    · build_contacts_layer.py  -- la nuit ne rebaptise plus ces liens « mandant »
    · relation_ledger.py       -- le registre pose `origine = 'vente'` et la date
Une regle ecrite deux fois finit par dire deux choses (le registre des mandats a
menti deux mois pour ca) : elle est donc ICI, une seule fois.

L'INTERRUPTEUR
--------------
APP_RELATION_ACHETEUR_PROPRIETAIRE=1 dans `.env`. Eteint (le defaut), personne ne
l'appelle et TOUT se comporte comme avant.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import unicodedata
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INTERRUPTEUR = "APP_RELATION_ACHETEUR_PROPRIETAIRE"
ORIGINE_VENTE = "vente"
ROLE_ACQUEREUR_VENTE = "acquereur_vente"
ROLES_DU_BIEN = ("mandant", "proprietaire")
# Un nom de moins de 2 lettres trouverait n'importe quel texte.
LONGUEUR_MINIMALE_DU_NOM = 2

_ENV_DEJA_CHARGE = False


def actif() -> bool:
    """L'interrupteur, lu APRES `.env` (meme patron que affaire_ledger.chainage_v2_actif)."""
    global _ENV_DEJA_CHARGE
    if not _ENV_DEJA_CHARGE:
        try:
            from phase2.sync.push_upgrade_to_supabase import DEFAULT_ENV_FILES, load_env_files
            load_env_files(DEFAULT_ENV_FILES)
        except Exception as souci:                                   # noqa: BLE001
            # On ne tombe pas pour ca (la variable d'environnement suffit, et
            # l'absence des deux veut dire ETEINT) -- mais on le DIT.
            print(f"[acheteur proprietaire] .env illisible : {souci!r} "
                  f"-- on s'en tient a la variable d'environnement")
        _ENV_DEJA_CHARGE = True
    return (os.environ.get(INTERRUPTEUR) or "0").strip() == "1"


def nom_compare(valeur: object) -> str:
    """« Rendela Christine » -> « RENDELACHRISTINE » : majuscules, sans accent, sans
    espace ni ponctuation. Le texte du mandat colle souvent le nom a l'adresse
    (« RENDELA CHRISTINE180 chemin… ») : on compare donc des lettres, pas des mots."""
    texte = unicodedata.normalize("NFD", str(valeur or "")).upper()
    return "".join(c for c in texte if c.isalnum() and not unicodedata.combining(c))


def est_nomme(nom: object, textes_des_mandats: Iterable[object]) -> bool:
    cle = nom_compare(nom)
    return any(cle and cle in nom_compare(t) for t in textes_des_mandats)


def ne_de_la_vente(nom: object, textes_des_mandats: Iterable[object]) -> bool:
    """Le coeur de la regle, sans base : critere 2 et 3 (le 1 est a l'appelant)."""
    if len(nom_compare(nom)) < LONGUEUR_MINIMALE_DU_NOM:
        return False                    # fiche sans nom : on ne juge pas
    return not est_nomme(nom, textes_des_mandats)


def _textes_hektor_du_mandat(payload_json: object, versions_json: object) -> list[str]:
    """Le texte des mandants TEL QUE HEKTOR L'A DONNE, version courante et versions
    gardees. ⛔ PAS `mandants_texte` : mandat_ledger.py (l. 645-668) le REMPLACE par
    nos liens quand le corps de Hektor est suspect ou vide sur une vente -- donc par
    une liste qui contient DEJA l'acheteur (mesure du 26/10 : 40 acheteurs sur 113
    y etaient, « M_Mme Florian JACQUIER » sur 61730). Juger sur lui, ce serait juger
    l'acheteur sur la faute qu'on corrige."""
    textes: list[str] = []
    for brut in (payload_json, versions_json):
        try:
            valeur = json.loads(brut) if isinstance(brut, str) else brut
        except (TypeError, ValueError):
            continue
        for morceau in (valeur if isinstance(valeur, list) else [valeur]):
            if isinstance(morceau, dict) and morceau.get("mandants"):
                textes.append(str(morceau["mandants"]))
    return textes


def charger_textes_des_mandats(conn: sqlite3.Connection,
                               annonces: Iterable[str]) -> dict[str, list[str]]:
    """Les textes des mandants donnes par Hektor pour TOUS les mandats connus de
    chaque bien (`app_mandat` local, delete-never : un mandat clos y reste)."""
    voulues = sorted({str(a) for a in annonces if str(a or "").strip()})
    textes: dict[str, list[str]] = {a: [] for a in voulues}
    if not voulues:
        return textes
    try:
        for i in range(0, len(voulues), 500):
            lot = voulues[i:i + 500]
            places = ",".join("?" for _ in lot)
            for annonce, payload, versions in conn.execute(
                    "SELECT CAST(hektor_annonce_id AS TEXT), payload_json, versions_json FROM app_mandat"
                    f" WHERE CAST(hektor_annonce_id AS TEXT) IN ({places})", lot):
                textes[str(annonce)].extend(_textes_hektor_du_mandat(payload, versions))
    except sqlite3.OperationalError as souci:
        # Sans registre des mandats, on ne PEUT PAS ecarter les vrais mandants :
        # on refuse de juger plutot que de declasser a l'aveugle.
        raise RuntimeError(f"app_mandat illisible, regle non appliquee : {souci}") from souci
    return textes


def charger_noms(conn: sqlite3.Connection, contacts: Iterable[str]) -> dict[str, str]:
    """Le NOM DE FAMILLE de chaque personne (NOTRE numero), lu dans l'annuaire local."""
    voulus = sorted({str(c) for c in contacts if str(c or "").strip()})
    noms: dict[str, str] = {}
    for i in range(0, len(voulus), 500):
        lot = voulus[i:i + 500]
        places = ",".join("?" for _ in lot)
        for contact, nom in conn.execute(
                "SELECT CAST(hektor_contact_id AS TEXT), nom FROM app_contact_current"
                f" WHERE CAST(hektor_contact_id AS TEXT) IN ({places})", lot):
            noms[str(contact)] = str(nom or "")
    return noms


def couples_nes_de_la_vente(conn: sqlite3.Connection,
                            liens: Iterable[dict]) -> dict[tuple[str, str], str]:
    """Pour des lignes au format de la table de nuit (hektor_contact_id = NOTRE
    numero, hektor_annonce_id, role_contact, transaction_date), rend
    {(contact, annonce): date de la vente} pour chaque lien du bien ne d'une vente.

    `liens` doit contenir A LA FOIS les liens du bien et les lignes
    « acquereur_vente » : c'est leur rencontre qui fait le critere 1."""
    ventes: dict[tuple[str, str], str] = {}
    du_bien: set[tuple[str, str]] = set()
    for l in liens:
        cle = (str(l.get("hektor_contact_id") or "").strip(),
               str(l.get("hektor_annonce_id") or "").strip())
        if not cle[0] or not cle[1]:
            continue
        role = l.get("role_contact")
        if role == ROLE_ACQUEREUR_VENTE:
            date = str(l.get("transaction_date") or "").strip()[:10]
            # Deux ventes du meme bien a la meme personne : la PLUS ANCIENNE est
            # celle qui l'a fait proprietaire.
            if cle not in ventes or (date and (not ventes[cle] or date < ventes[cle])):
                ventes[cle] = date
        elif role in ROLES_DU_BIEN:
            du_bien.add(cle)
    candidats = du_bien & set(ventes)
    if not candidats:
        return {}
    textes = charger_textes_des_mandats(conn, {a for _, a in candidats})
    noms = charger_noms(conn, {c for c, _ in candidats})
    return {cle: ventes[cle] for cle in sorted(candidats)
            if ne_de_la_vente(noms.get(cle[0], ""), textes.get(cle[1], []))}
