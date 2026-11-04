"""COUPLES · PHASE 1 (01/11/2026) — LA NATURE DE CHAQUE FICHE, ET LA CIVILITE RENDUE.

Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §1, §3 (T1-T4), §4 étape 2.
Les definitions sont celles de notice/AUDIT_NATURE_DES_FICHES_CONTACT_2026-11-01.md.

CE QUE FAIT CETTE ETAPE : elle remplit la table locale `contact_nature_current` de
phase2.sqlite, une ligne par fiche de `app_contact_current` (meme numero), et RIEN
d'autre. Personne ne lit cette table aujourd'hui : ni le push, ni l'ecran, ni le
worker. Elle n'ecrit ni chez Hektor, ni chez Supabase.

    nature_fiche   T1  personne_seule · couple · conjoint · conjoint_sans_prenom ·
                       case_conjoint_vide · case_vide_orpheline
    couple_deuxieme    pour un couple seulement : conjoint_avec_prenom · nom_recopie ·
                       case_vide · aucune_deuxieme_fiche · aucun_lien
    civilite_app   T2  « Mme. » quand Hektor n'a RIEN et que l'ancien logiciel disait
                       Madame (table `ancien_logiciel_contact`) ; NULL sinon
                       -> l'ecran affichera civilite_app, et a defaut `civilite`
    civilite_source    'ancien_logiciel' quand civilite_app est posee
    suit_principale_archivee  T3  case de conjoint vide, active, dont la principale
                       est archivee (elle suivra sa principale a l'ecran)
    supprimee_chez_hektor     T4  fiche sans agence : supprimee chez Hektor, gardee
                       chez nous parce qu'une annonce ou une offre la cite

⛔ POURQUOI UNE TABLE A PART et pas des colonnes de `app_contact_current` : le push
   des contacts lit cette table en `SELECT *` -- une colonne de plus partirait chez
   Supabase, ou elle n'existe pas, et ferait echouer tout le push. La phase 2 (accord
   requis) creera les colonnes chez Supabase et les ajoutera a l'envoi.
⛔ POURQUOI `civilite` N'EST PAS TOUCHEE (decision « A » du 01/11) : c'est le miroir de
   Hektor, la nuit suivante la remettrait a vide. Une civilite confirmee par un agent
   passe par le chemin normal (saisie -> Hektor) et rend civilite_app inutile : on ne la
   pose que si Hektor n'a RIEN.

RATTACHEMENT (01/11, accord de Frederic « Oui rattacher », synthese §11) : les cases
vides « orphelines » qu'un bien cite sont des couples COUPES EN DEUX -- la vraie
personne est une fiche nommee sur le meme bien. Quand UNE SEULE fiche nommee du meme
bien a ete creee LE MEME JOUR, la case lui est rattachee CHEZ NOUS : elle devient sa
« case_conjoint_vide » (couple_deuxieme = case_vide) et la personne devient un couple.
Les autres sont mises de cote (colonne `rattachement` = la raison). Rien chez Hektor,
rien dans `hektor_couple_contact_id` : seule cette table le sait (`rattachee_a`).
⛔ INTERRUPTEUR APP_CONTACT_RATTACHEMENT (.env) : eteint, la case reste « orpheline »
   et rien ne change ; `--rattacher` l'allume pour un essai a blanc.

⚠ PLACE DANS LE RUN : apres la construction de la couche (elle est videe et remplie
  chaque nuit). Etape NON BLOQUANTE : ratee, la table garde la nuit precedente --
  sans lecteur, rien ne change pour personne.
⚠ PAS DE BATTEMENT pour l'instant : une cle de battement s'enregistre chez Supabase
  (ecriture en production). Elle viendra avec la phase 2.

Usage :
    python phase2/contacts/nature_des_fiches.py            (remplace la table)
    python phase2/contacts/nature_des_fiches.py --a-blanc  (compte, n'ecrit rien)
    python phase2/contacts/nature_des_fiches.py --contact-id N [--a-blanc]
        (relecture d'une fiche : recalcule SON menage ; interrupteur APP_NATURE_A_LA_RELECTURE ; ne leve jamais)
Sortie : 0 = fait · 1 = echec (jamais 1 avec --contact-id).
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

try:  # lancé comme script (run) ou importé comme module (essais)
    from notaires_registre import notaires_hektor
except ImportError:  # pragma: no cover
    from phase2.contacts.notaires_registre import notaires_hektor
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
TABLE = "contact_nature_current"
TABLE_ANCIEN = "ancien_logiciel_contact"

# Les signes d'un couple sur une premiere fiche (audit du 01/11, §1).
CIVILITES_COUPLE = {"Mr./Mme", "M_Mme", "Mme_M", "Mme_Mme", "M_M"}
# COUPLES (04/11/2026) : le « _ » est le formulaire de COUPLE de Hektor (une civilite par place). Apres
#   « Transformer en couple » sur une personne sans civilite, Hektor ecrit « _Mr/Mme » (place 1 vide) :
#   EA32621 restait « personne seule » parce que le test etait une egalite exacte (synthese couples §57 bis).
#   Mesure du 04/11 sur les 356 835 fiches : 1 seule change (10260586) ; l'ancienne regle redonne la table
#   de la nuit a l'identique.
SEPARATEUR_DE_PLACES = "_"


def civilite_de_couple(civilite: Any) -> bool:
    texte = _texte(civilite)
    return texte in CIVILITES_COUPLE or SEPARATEUR_DE_PLACES in texte
DEUX_PRENOMS = re.compile(r"(\bet\b|&|/|\+|\bepoux\b|\bm\.? et mme\b)")
DEUX_NOMS = re.compile(r"\b(et|epoux)\b|&")
MADAME_ANCIEN = 2          # `gender` de l'ancien logiciel : 2 = Madame
MADAME_HEKTOR = "Mme."     # la forme que Hektor ecrit (1 514 fiches)


def normaliser(valeur: Any) -> str:
    return unicodedata.normalize("NFKD", str(valeur or "").strip().lower()).encode("ascii", "ignore").decode()


def _texte(valeur: Any) -> str:
    return str(valeur or "").strip()


def nommee(fiche: dict[str, Any]) -> bool:
    return bool(normaliser(fiche.get("nom")) or normaliser(fiche.get("prenom")))


def archivee(fiche: dict[str, Any]) -> bool:
    return _texte(fiche.get("archive")).lower() in {"1", "true"}


def secondes_par_principale(fiches: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    secondes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for f in fiches.values():
        lien = _texte(f.get("hektor_couple_contact_id"))
        if lien and lien != _texte(f.get("hektor_contact_id")):
            secondes[lien].append(f)
    return secondes


def nature(fiche: dict[str, Any], fiches: dict[str, dict[str, Any]],
           secondes: dict[str, list[dict[str, Any]]]) -> str:
    """La nature d'une fiche. Fonction PURE (elle ne lit que ce qu'on lui donne)."""
    numero = _texte(fiche.get("hektor_contact_id"))
    lien = _texte(fiche.get("hektor_couple_contact_id"))
    if lien and lien != numero:                          # une deuxieme fiche
        if not nommee(fiche):
            return "case_conjoint_vide" if lien in fiches else "case_vide_orpheline"
        return "conjoint" if normaliser(fiche.get("prenom")) else "conjoint_sans_prenom"
    if not nommee(fiche):
        return "case_vide_orpheline"
    signe = (civilite_de_couple(fiche.get("civilite"))
             or bool(DEUX_PRENOMS.search(normaliser(fiche.get("prenom"))))
             or bool(DEUX_NOMS.search(normaliser(fiche.get("nom"))))
             or any(normaliser(s.get("prenom")) for s in secondes.get(numero, [])))
    return "couple" if signe else "personne_seule"


def couple_deuxieme(fiche: dict[str, Any], secondes: dict[str, list[dict[str, Any]]]) -> str:
    """Ce qu'est la deuxieme fiche d'un COUPLE (cas a-e de l'audit, §2 et §2 bis)."""
    numero = _texte(fiche.get("hektor_contact_id"))
    if _texte(fiche.get("hektor_couple_contact_id")) != numero:
        return "aucun_lien"                              # e
    siennes = secondes.get(numero, [])
    if any(normaliser(s.get("prenom")) for s in siennes):
        return "conjoint_avec_prenom"                    # a
    if any(nommee(s) for s in siennes):
        return "nom_recopie"                             # b
    if siennes:
        return "case_vide"                               # c
    return "aucune_deuxieme_fiche"                       # d


def madames_de_l_ancien_logiciel(conn: sqlite3.Connection) -> set[str] | None:
    """Les numeros HEKTOR que l'ancien logiciel disait « Madame », sans contradiction.

    None si la table n'a pas ete chargee (charger_ancien_logiciel.py) : on ne rend
    alors aucune civilite, sans echouer.
    """
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (TABLE_ANCIEN,)).fetchone():
        return None
    genres: dict[str, set[Any]] = defaultdict(set)
    for hid, genre in conn.execute(f"SELECT hektor_contact_id, gender FROM {TABLE_ANCIEN} "
                                   "WHERE hektor_contact_id IS NOT NULL"):
        genres[str(hid)].add(genre)
    # une fiche Hektor visee par plusieurs anciennes fiches : seulement si TOUTES disent Madame
    return {hid for hid, g in genres.items() if g == {MADAME_ANCIEN}}


def _jour(fiche: dict[str, Any]) -> str:
    return _texte(fiche.get("date_enregistrement"))[:10]


def rattachements(fiches: dict[str, dict[str, Any]], biens_par_contact: dict[str, set[str]],
                  contacts_par_bien: dict[str, set[str]],
                  notaires: set[str] | None = None) -> tuple[dict[str, str], dict[str, str]]:
    """({case: personne}, {case: raison de la mise de cote}). Fonction PURE.

    Une case « orpheline » (vide, principale absente ou aucun lien) est rattachee a la
    SEULE fiche nommee, premiere de foyer ou sans foyer, qu'un de ses biens cite et qui
    est nee le meme jour qu'elle.
    """
    secondes = secondes_par_principale(fiches)
    faits: dict[str, str] = {}
    cote: dict[str, str] = {}
    for numero, f in fiches.items():
        if nature(f, fiches, secondes) != "case_vide_orpheline":
            continue
        biens = biens_par_contact.get(numero, set())
        if not biens:
            continue                                    # aucun bien : pas de voisin a chercher
        voisins = {v for b in biens for v in contacts_par_bien.get(b, set()) if v != numero and v in fiches}
        nommes = {v for v in voisins if nommee(fiches[v])
                  and _texte(fiches[v].get("hektor_couple_contact_id")) in ("", v)}
        # ⛔ 02/11 : un NOTAIRE ne reçoit jamais une case (il n'est pas un couple -- règle de Frédéric).
        sans_notaire = {v for v in nommes if not est_notaire(fiches[v], notaires)}
        if not sans_notaire:
            cote[numero] = "seule_personne_est_un_notaire" if nommes else "aucune_personne_sur_le_bien"
            continue
        nommes = sans_notaire
        meme_jour = {v for v in nommes if _jour(fiches[v]) and _jour(fiches[v]) == _jour(f)}
        if len(meme_jour) == 1:
            faits[numero] = meme_jour.pop()
        elif meme_jour:
            cote[numero] = "plusieurs_personnes_le_meme_jour"
        else:
            cote[numero] = "personne_nee_un_autre_jour"
    return faits, cote


def est_notaire(fiche: dict[str, Any], notaires: set[str] | None) -> bool:
    """Fiche d'un notaire du registre des ventes (par son numéro HEKTOR). Fonction PURE."""
    return bool(notaires) and _texte(fiche.get("hektor_target_id")) in notaires


def calculer(fiches: dict[str, dict[str, Any]], madames: set[str] | None,
             rattache: dict[str, str] | None = None, cote: dict[str, str] | None = None,
             notaires: set[str] | None = None) -> list[dict[str, Any]]:
    rattache = rattache or {}
    cote = cote or {}
    if rattache:
        # le lien n'existe que dans CE calcul : la couche et Hektor ne sont pas touches
        fiches = dict(fiches)
        for case, personne in rattache.items():
            fiches[case] = {**fiches[case], "hektor_couple_contact_id": personne}
            if not _texte(fiches[personne].get("hektor_couple_contact_id")):
                fiches[personne] = {**fiches[personne], "hektor_couple_contact_id": personne}
    personnes_rattachees = set(rattache.values())
    secondes = secondes_par_principale(fiches)
    lignes = []
    for numero, f in fiches.items():
        nat = nature(f, fiches, secondes)
        # ⛔ DÉCISION DE FRÉDÉRIC (02/11) : la personne qui RECOIT une case reste ce que dit Hektor (le plus
        #   souvent « personne seule » : chez Hektor elle n'a AUCUN lien de couple). Le rattachement ne sert
        #   qu'a MASQUER la coquille vide (case_conjoint_vide). Avant, elle passait « couple » (1 530 fiches
        #   actives de l'app affichees « Couple · conjoint a completer ») : une deduction que Hektor ne confirme
        #   pas. Creer un vrai couple depuis l'app = une question pour plus tard. Synthese couples §33.
        lien = _texte(f.get("hektor_couple_contact_id"))
        principale = fiches.get(lien) if lien and lien != numero else None
        # ⛔ RÈGLE DE FRÉDÉRIC (02/11) : UNE FICHE NOTAIRE N'EST JAMAIS UN COUPLE (historique et ajouts).
        #   · la fiche du notaire, nommée, prend la nature « notaire » (jamais « couple ») ;
        #   · une seconde fiche NOMMÉE d'un notaire n'est pas son « conjoint » : c'est une personne à part ;
        #   · la case VIDE d'un notaire reste « case_conjoint_vide » (rien à montrer, déjà masquée).
        if est_notaire(f, notaires) and nommee(f):
            nat = "notaire"
        elif nat in ("conjoint", "conjoint_sans_prenom") and principale is not None and est_notaire(principale, notaires):
            nat = "personne_seule"
        civilite_app = None
        if (madames is not None and not _texte(f.get("civilite")) and nommee(f)
                and _texte(f.get("hektor_target_id")) in madames):
            civilite_app = MADAME_HEKTOR
        lignes.append({
            "hektor_contact_id": numero,
            "nature_fiche": nat,
            "couple_deuxieme": couple_deuxieme(f, secondes) if nat == "couple" else None,
            "civilite_app": civilite_app,
            "civilite_source": "ancien_logiciel" if civilite_app else None,
            "suit_principale_archivee": int(nat == "case_conjoint_vide" and not archivee(f)
                                            and principale is not None and archivee(principale)),
            "supprimee_chez_hektor": int(not _texte(f.get("hektor_agence_id"))),
            "rattachee_a": rattache.get(numero),
            "rattachement": ("meme_bien_meme_jour" if numero in rattache or numero in personnes_rattachees
                             else cote.get(numero)),
        })
    return lignes


COLONNES = ("hektor_contact_id, hektor_target_id, hektor_couple_contact_id, hektor_agence_id, "
            "civilite, nom, prenom, archive, supabase_sync_eligible, date_enregistrement")


def lire_biens(conn: sqlite3.Connection) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Les biens (annonces) de chaque contact, et les contacts de chaque bien."""
    biens_par_contact: dict[str, set[str]] = defaultdict(set)
    contacts_par_bien: dict[str, set[str]] = defaultdict(set)
    for contact, bien in conn.execute("SELECT hektor_contact_id, hektor_annonce_id FROM app_contact_relation_current "
                                      "WHERE NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL"):
        contact, bien = _texte(contact), _texte(bien)
        biens_par_contact[contact].add(bien)
        contacts_par_bien[bien].add(contact)
    return biens_par_contact, contacts_par_bien


def charger_env() -> None:
    """Le meme .env que le push (meme fonction) : un seul endroit pour l'interrupteur."""
    sys.path.insert(0, str(ROOT / "phase2" / "sync"))
    try:
        from push_contacts_to_supabase import DEFAULT_ENV_FILES, load_env_file  # noqa: E402,PLC0415
        for chemin in DEFAULT_ENV_FILES:
            load_env_file(chemin)
    except Exception:  # noqa: BLE001 -- sans .env, l'interrupteur reste eteint
        pass


def rattachement_allume() -> bool:
    return (os.environ.get("APP_CONTACT_RATTACHEMENT") or "").strip().lower() in {"1", "on", "true", "oui"}


def lire(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    fiches = {_texte(r["hektor_contact_id"]): dict(r) for r in conn.execute(f"SELECT {COLONNES} FROM app_contact_current")}
    conn.row_factory = None
    return fiches


def ecrire(conn: sqlite3.Connection, lignes: list[dict[str, Any]]) -> None:
    """Remplace la table en une seule transaction (idempotente)."""
    calcule_le = datetime.now().isoformat(timespec="seconds")
    with conn:
        conn.execute(f"DROP TABLE IF EXISTS {TABLE}")
        conn.execute(f"""
            CREATE TABLE {TABLE} (
                hektor_contact_id TEXT PRIMARY KEY,
                nature_fiche TEXT NOT NULL,
                couple_deuxieme TEXT,
                civilite_app TEXT,
                civilite_source TEXT,
                suit_principale_archivee INTEGER NOT NULL,
                supprimee_chez_hektor INTEGER NOT NULL,
                rattachee_a TEXT,
                rattachement TEXT,
                calcule_le TEXT NOT NULL
            )""")
        conn.executemany(
            f"INSERT INTO {TABLE} VALUES (:hektor_contact_id, :nature_fiche, :couple_deuxieme, :civilite_app, "
            ":civilite_source, :suit_principale_archivee, :supprimee_chez_hektor, :rattachee_a, :rattachement, :calcule_le)",
            [{**l, "calcule_le": calcule_le} for l in lignes])


def bilan(fiches: dict[str, dict[str, Any]], lignes: list[dict[str, Any]]) -> list[str]:
    """Les comptes, serveur · actives · dans l'app : ceux de l'audit doivent ressortir."""
    tot, act, app = Counter(), Counter(), Counter()
    for l in lignes:
        f = fiches[l["hektor_contact_id"]]
        cles = [l["nature_fiche"]]
        if l["couple_deuxieme"]:
            cles.append("couple:" + l["couple_deuxieme"])
        if l["civilite_app"]:
            cles.append("T2 civilite Mme rendue")
        if l["suit_principale_archivee"]:
            cles.append("T3 case active, principale archivee")
        if l["supprimee_chez_hektor"]:
            cles.append("T4 supprimee chez Hektor")
        if l["rattachee_a"]:
            cles.append("R case rattachee a une personne du bien")
        elif l["rattachement"] == "meme_bien_meme_jour":
            cles.append("R personne recevant une case")
        elif l["rattachement"]:
            cles.append("R mise de cote : " + l["rattachement"])
        for cle in cles:
            tot[cle] += 1
            if not archivee(f):
                act[cle] += 1
            if _texte(f.get("supabase_sync_eligible")) in {"1", "True", "true"}:
                app[cle] += 1
    return [f"  {cle:40} serveur {tot[cle]:7}  actives {act[cle]:7}  app {app[cle]:6}" for cle in sorted(tot)]


def executer(conn: sqlite3.Connection, a_blanc: bool = False, rattacher: bool = False) -> int:
    fiches = lire(conn)
    madames = madames_de_l_ancien_logiciel(conn)
    if madames is None:
        print(f"[nature] table {TABLE_ANCIEN} absente : aucune civilite rendue (charger_ancien_logiciel.py)")
    notaires = notaires_hektor(conn)
    print(f"[nature] notaires du registre des ventes : {len(notaires)} (jamais couple, regle du 02/11)")
    faits: dict[str, str] = {}
    cote: dict[str, str] = {}
    if rattacher:
        faits, cote = rattachements(fiches, *lire_biens(conn), notaires=notaires)
        print(f"[nature] rattachement : {len(faits)} case(s) rattachee(s) a {len(set(faits.values()))} personne(s), "
              f"{len(cote)} mise(s) de cote")
    else:
        print("[nature] rattachement eteint (APP_CONTACT_RATTACHEMENT)")
    lignes = calculer(fiches, madames, faits, cote, notaires)
    print(f"[nature] {len(lignes)} fiche(s) :")
    for ligne in bilan(fiches, lignes):
        print(ligne)
    if a_blanc:
        print("[nature] A BLANC : rien n'est ecrit")
        return 0
    ecrire(conn, lignes)
    print(f"[nature] table {TABLE} remplie : {len(lignes)} ligne(s)")
    return 0


# ── COUPLES (04/11/2026) — LA NATURE A LA RELECTURE D'UNE FICHE (synthese couples §59-60) ──
# La nuit calcule toute la table ; une relecture d'une fiche (refresh_contact_inproc.py) envoyait
# donc la nature de la veille, ou RIEN pour un contact ne dans la journee. Meme remede que
# l'etape « conjoint » de la relecture : recalculer LE MENAGE de la fiche avant l'envoi.
# ⛔ INTERRUPTEUR APP_NATURE_A_LA_RELECTURE (.env) : eteint, rien n'est fait (la nuit suffit).
# ⚠ Le MENAGE (ecrit) = la principale P de la fiche, la fiche, toutes les secondes de P, et les
#   cases rattachees par la nuit a l'un d'eux. Le CONTEXTE (lu, pas ecrit) = en plus les secondes
#   de chacun : la nature d'un membre ne depend que de lui, de sa principale et de ses secondes.
# ⚠ Ce qui ne se calcule que sur TOUTE la table garde la valeur de la nuit : le rattachement des
#   cases orphelines (`rattachee_a`, `rattachement`, repris de la table tel quel). Un ancien
#   menage que la fiche vient de quitter n'est pas recalcule : la nuit s'en charge.
# ⚠ N'ecrit QUE des lignes (INSERT OR REPLACE) : jamais de DROP. Table absente -> rien.

def a_la_relecture_allume() -> bool:
    return (os.environ.get("APP_NATURE_A_LA_RELECTURE") or "").strip().lower() in {"1", "on", "true", "oui"}


def _fiches_par_numeros(conn: sqlite3.Connection, numeros: set[str]) -> dict[str, dict[str, Any]]:
    if not numeros:
        return {}
    conn.row_factory = sqlite3.Row
    try:
        marques = ",".join("?" * len(numeros))
        return {_texte(r["hektor_contact_id"]): dict(r) for r in conn.execute(
            f"SELECT {COLONNES} FROM app_contact_current WHERE hektor_contact_id IN ({marques})", sorted(numeros))}
    finally:
        conn.row_factory = None


def _secondes_de(conn: sqlite3.Connection, numeros: set[str]) -> set[str]:
    if not numeros:
        return set()
    marques = ",".join("?" * len(numeros))
    return {_texte(r[0]) for r in conn.execute(
        f"SELECT hektor_contact_id FROM app_contact_current WHERE hektor_couple_contact_id IN ({marques})",
        sorted(numeros))}


def menage_du_contact(conn: sqlite3.Connection, numero: str) -> tuple[set[str], dict[str, dict[str, Any]], dict[str, str], dict[str, str]]:
    """(numeros a ecrire, fiches du contexte, rattachements de la nuit, mises de cote de la nuit)."""
    fiche = _fiches_par_numeros(conn, {numero}).get(numero)
    if fiche is None:
        return set(), {}, {}, {}
    lien = _texte(fiche.get("hektor_couple_contact_id"))
    principale = lien or numero
    membres = {numero, principale} | _secondes_de(conn, {principale})
    rattache: dict[str, str] = {}
    cote: dict[str, str] = {}
    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)).fetchone():
        marques = ",".join("?" * len(membres))
        for case, personne, raison in conn.execute(
                f"SELECT hektor_contact_id, rattachee_a, rattachement FROM {TABLE} "
                f"WHERE hektor_contact_id IN ({marques}) OR rattachee_a IN ({marques})",
                sorted(membres) + sorted(membres)):
            case, personne = _texte(case), _texte(personne)
            if personne:
                rattache[case] = personne
                membres |= {case, personne}
            if _texte(raison):
                cote[case] = _texte(raison)
    contexte_numeros = set(membres) | _secondes_de(conn, membres)
    contexte = _fiches_par_numeros(conn, contexte_numeros)
    for case, personne in rattache.items():
        contexte_numeros |= _secondes_de(conn, {personne})
    contexte.update(_fiches_par_numeros(conn, contexte_numeros - set(contexte)))
    membres &= set(contexte)
    rattache = {c: p for c, p in rattache.items() if c in contexte and p in contexte}
    return membres, contexte, rattache, {c: r for c, r in cote.items() if c in membres}


def madames_parmi(conn: sqlite3.Connection, fiches: dict[str, dict[str, Any]]) -> set[str] | None:
    """Comme madames_de_l_ancien_logiciel, limite aux numeros HEKTOR des fiches donnees."""
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (TABLE_ANCIEN,)).fetchone():
        return None
    cibles = sorted({_texte(f.get("hektor_target_id")) for f in fiches.values()} - {""})
    if not cibles:
        return set()
    genres: dict[str, set[Any]] = defaultdict(set)
    marques = ",".join("?" * len(cibles))
    for hid, genre in conn.execute(f"SELECT hektor_contact_id, gender FROM {TABLE_ANCIEN} "
                                   f"WHERE hektor_contact_id IN ({marques})", cibles):
        genres[str(hid)].add(genre)
    return {hid for hid, g in genres.items() if g == {MADAME_ANCIEN}}


def calculer_menage(conn: sqlite3.Connection, numero: str) -> list[dict[str, Any]]:
    """Les lignes de nature du menage de la fiche, calculees par LA MEME fonction que la nuit."""
    membres, contexte, rattache, cote = menage_du_contact(conn, numero)
    if not membres:
        return []
    lignes = calculer(contexte, madames_parmi(conn, contexte), rattache, cote, notaires_hektor(conn))
    return [l for l in lignes if l["hektor_contact_id"] in membres]


def ecrire_lignes(conn: sqlite3.Connection, lignes: list[dict[str, Any]]) -> bool:
    """Remplace CES lignes seulement. False si la table n'existe pas (la nuit la creera)."""
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)).fetchone():
        return False
    calcule_le = datetime.now().isoformat(timespec="seconds")
    with conn:
        conn.executemany(
            f"INSERT OR REPLACE INTO {TABLE} VALUES (:hektor_contact_id, :nature_fiche, :couple_deuxieme, :civilite_app, "
            ":civilite_source, :suit_principale_archivee, :supprimee_chez_hektor, :rattachee_a, :rattachement, :calcule_le)",
            [{**l, "calcule_le": calcule_le} for l in lignes])
    return True


def executer_pour_contact(conn: sqlite3.Connection, numero: str, a_blanc: bool = False) -> int:
    lignes = calculer_menage(conn, numero)
    if not lignes:
        print(f"[nature] le contact {numero} n'est pas dans la couche : rien a faire")
        return 0
    print(f"[nature] menage de {numero} : " + ", ".join(f"{l['hektor_contact_id']}={l['nature_fiche']}" for l in lignes))
    if a_blanc:
        print("[nature] A BLANC : rien n'est ecrit")
        return 0
    if not ecrire_lignes(conn, lignes):
        print(f"[nature] table {TABLE} absente : rien n'est ecrit (la nuit la creera)")
        return 0
    print(f"[nature] {len(lignes)} ligne(s) du menage reecrite(s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--phase2-db", type=Path, default=DEFAULT_PHASE2_DB)
    ap.add_argument("--a-blanc", action="store_true")
    ap.add_argument("--rattacher", action="store_true", help="allume le rattachement pour CET appel")
    ap.add_argument("--contact-id", help="relecture d'une fiche : recalcule SON menage seulement (ne leve jamais)")
    args = ap.parse_args()
    charger_env()
    contact_id = (args.contact_id or "").strip()
    if contact_id and not a_la_relecture_allume():
        print("[nature] interrupteur APP_NATURE_A_LA_RELECTURE eteint : rien a faire (la nuit suffit)")
        return 0
    conn = sqlite3.connect(args.phase2_db, timeout=30)
    conn.execute("PRAGMA busy_timeout=30000")
    try:
        if contact_id:
            return executer_pour_contact(conn, contact_id, args.a_blanc)
        return executer(conn, args.a_blanc, args.rattacher or rattachement_allume())
    except Exception as erreur:  # noqa: BLE001
        print(f"[nature] ECHEC : {erreur}", file=sys.stderr)
        # La relecture d'une fiche ne doit JAMAIS echouer a cause de la nature : la nuit la recalcule.
        return 0 if contact_id else 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
