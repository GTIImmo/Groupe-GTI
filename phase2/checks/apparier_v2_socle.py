#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPARIEUR V2 -- LE SOCLE : lecture, normalisation, extraction. 13/11/2026

Module partage par toutes les passes de l'apparieur v2. Il ne DECIDE rien : il
lit et il normalise. La logique d'appariement vit dans les passes.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ LES TROIS REGLES D'INDEPENDANCE
═══════════════════════════════════════════════════════════════════════════════
  1. on ne lit JAMAIS `app_classeur_lien` (le gel) ;
  2. on ne lit JAMAIS le CSV d'appariement de la v1 (il porte deja la reponse) ;
  3. on n'importe AUCUNE logique de `apparier_classeur.py`. On lui emprunte
     `lire_classeur` et `load_env_file`, et RIEN d'autre : lire un fichier n'est
     pas apparier.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ LES TROIS DEFAUTS QUE LA PASSE 1 A TROUVES DANS MA PROPRE METHODE
═══════════════════════════════════════════════════════════════════════════════
① JE LISAIS LES CLES DU JSON COMME DES NOMS DE PERSONNES. En appliquant une
  regex de mots au JSON brut, j'extrayais `null`, `ville`, `datemaj`, `pays`,
  `adresse`, `nom`, `prenom`, `longitude`... soit 31 127 transactions « partageant
  un nom ». ⭐ Il FAUT parser le JSON et lire les champs, jamais le texte brut.
  ⚠ Et `acquereurs_json` est PARFOIS UN OBJET, PARFOIS UN TABLEAU (faute payee
    quatre fois le 12/11) : les deux formes se gerent ici, une fois pour toutes.

② JE MESURAIS LA PUISSANCE D'UN SIGNAL EN TRANSACTIONS. « Le mandat designe
  3 transactions en mediane » faisait croire a de l'ambiguite : c'est exactement
  UN DOSSIER COMPLET (offre + compromis + vente partagent le mandat). ⭐ On
  mesure au niveau du BIEN, puis le GENRE choisit la transaction.

③ JE COMPARAIS SANS NORMALISER LES ACCENTS. « Allegre » ne trouvait pas
  « Allègre » (12/11). Le classeur est saisi A LA MAIN.

═══════════════════════════════════════════════════════════════════════════════
⭐ CE QUE LA MESURE A ETABLI, ET QUI FONDE LA CONCEPTION
═══════════════════════════════════════════════════════════════════════════════
    mandat + montant    96,0 % designent UN SEUL bien   <- le meilleur signal
    mandat seul         90,2 %
    nom + mandat        92,8 %
    nom + montant       78,1 %
    montant seul        53,0 %
  et « bien + genre » identifie LA transaction pour 9 652 biens sur 10 691 (90,3 %)
  ⚠ restent 818 biens a 2 offres et 111 a 3 offres : la date et le montant
    departagent.
"""
from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")


# ─────────────────────────────────────────────────────────────────────────────
# NORMALISER
# ─────────────────────────────────────────────────────────────────────────────
def sans_accent(t) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(t or ""))
                   if unicodedata.category(c) != "Mn")


def pur(t) -> str:
    return re.sub(r"\s+", " ", sans_accent(t).strip().lower())


def chiffres(t) -> str:
    return "".join(c for c in str(t or "") if c.isdigit())


def somme(t):
    """Un montant en euros entiers, ou None. Gere « 1 234,56 », « 1.234,56 »,
    « 1,234.56 », « 170 000 EUR », les espaces insecables et les apostrophes."""
    s = sans_accent(str(t or "")).strip()
    if not s:
        return None
    s = s.replace("EUR", "").replace("\u20ac", "")
    s = s.replace("\u00a0", "").replace("'", "").replace(" ", "")
    if "," in s and "." in s:
        s = (s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".")
             else s.replace(",", ""))
    else:
        s = s.replace(",", ".")
    s = re.sub(r"[^0-9.\-]", "", s)
    if not s or s in {"-", "."}:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return int(round(v)) if v else None


# ⭐ LES MOIS FRANCAIS, par leurs QUATRE premieres lettres sans accent : c est
#   suffisant pour les distinguer tous, et ca absorbe les abreviations du classeur
#   (« fevr », « sept », « dec. », « aout »).
_MOIS = {
    "janv": 1, "jan": 1, "fevr": 2, "fev": 2, "mars": 3, "mar": 3,
    "avri": 4, "avr": 4, "mai": 5, "juin": 6, "juil": 7, "aout": 8,
    "sept": 9, "sep": 9, "octo": 10, "oct": 10, "nove": 11, "nov": 11,
    "dece": 12, "dec": 12,
}


def jour(t) -> str:
    """Une date en AAAA-MM-JJ, ou ''. ⚠ `0000-00-00` et `1990-01-01` sont les
    deux SENTINELLES de Hektor : elles ne valent pas une date."""
    s = str(t or "").strip()
    if not s or s.startswith("0000") or s.startswith("1990-01-01"):
        return ""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        a, mo, j = m.groups()
        return "" if a in {"0000", "1990"} else "%s-%s-%s" % (a, mo, j)
    m = re.match(r"^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})", s)
    if m:
        j, mo, a = m.groups()
        a = ("20" + a) if len(a) == 2 else a
        if a in {"0000", "1990"}:
            return ""
        try:
            return "%s-%02d-%02d" % (a, int(mo), int(j))
        except ValueError:
            return ""
    # ⭐⭐⭐ LE FORMAT FRANCAIS LITTERAL -- ajoute le 13/11, et c'est LE DEFAUT LE
    #   PLUS RENTABLE DE TOUT CE TRAVAIL. Le classeur est saisi a la main et ecrit
    #   « 9 aout25 », « 24 fevrier25 », « 12 decembre25 », « 1 decembre25 » : jour,
    #   mois EN FRANCAIS, annee sur deux chiffres, SOUVENT SANS ESPACE avant l annee.
    #   ⛔ MESURE AVANT CORRECTION : je perdais 13 677 dates sur 31 037 -- 44,1 %.
    #     C est ce qui faisait taire ma famille « dates » 744 + 648 fois (« moins de
    #     2 dates », « aucun bien n a 2 dates »).
    #   ⭐ Trouve en relisant MON PROPRE TABLEAU : la ligne 566 annoncait « 2 dates
    #     lisibles » alors que le classeur en portait QUATRE.
    mm = re.match(r"^(\d{1,2})\s*([A-Za-zÀ-ɏ]{3,12})\.?\s*(\d{2,4})\s*$", s)
    if mm:
        j, mois, a = mm.groups()
        n = _MOIS.get(pur(mois)[:4])
        if n:
            a = ("20" + a) if len(a) == 2 else a
            if a not in {"0000", "1990"}:
                # ⛔ ON VALIDE CONTRE LE CALENDRIER REEL : sans ca, « 32 janvier25 »
                #   rendait « 2025-01-32 ». Une date impossible est pire qu une date
                #   absente -- elle se compare, et elle ne tombe jamais juste.
                try:
                    import datetime
                    return datetime.date(int(a), n, int(j)).isoformat()
                except (ValueError, TypeError):
                    return ""
    return ""


# ⚠ CIVILITES, FORMES SOCIALES ET LIAISONS. Elles ne distinguent personne, et
#   « SCI » ou « M » dans un ensemble de noms cree de faux partages.
MOTS_VIDES = {
    "mr", "mme", "mlle", "monsieur", "madame", "mademoiselle", "mrs",
    "sci", "sarl", "sas", "sasu", "eurl", "scp", "snc", "sca", "scm", "sc",
    "indivision", "succession", "hoirie", "consorts", "cts",
    "et", "ou", "de", "du", "des", "la", "le", "les", "aux",
    "ep", "epouse", "epoux", "veuve", "vve", "nee", "ne",
    # ⛔ AJOUTES LE 13/11 APRES AVOIR REGARDE DES LIGNES REELLES. Le classeur est
    #   saisi a la main et porte des mots de LIAISON et de STRUCTURE qui ne
    #   designent personne : « Societe GRAIL Jo-nathan », « Ind. TOINET »,
    #   « SCI CNAV representee par son gerant Nicolas Aboulin ».
    #   ⭐ Ils ne faisaient pas que du bruit : ils FAISAIENT ECHOUER l intersection
    #     de ma famille « identite » -- 1 160 lignes classees a tort
    #     « aucun bien porte ces noms ».
    "ind", "societe", "ste", "representee", "represente", "gerant",
    "gerante", "par", "son", "sa", "ses", "pour", "compte",
    "nan", "none", "null", "vide", "inconnu", "inconnue",
}


def _mots_de_nom(texte) -> set[str]:
    mots = re.split(r"[^A-Za-z\u00c0-\u024f]+", sans_accent(texte or ""))
    return {m.lower() for m in mots if len(m) >= 3 and m.lower() not in MOTS_VIDES}


# ⭐ LES CHAMPS QUI PORTENT UN NOM DE PERSONNE, chez Hektor.
CHAMPS_DE_NOM = ("nom", "prenom", "prenom1", "prenom2", "raison_sociale",
                 "raisonsociale", "societe", "denomination", "lastname",
                 "firstname", "name")


def _personnes(obj, sortie: list[dict]) -> None:
    """Descend dans un JSON (objet, tableau, imbrication) et ramasse les
    DICTIONNAIRES qui ressemblent a une personne."""
    if isinstance(obj, dict):
        if any(k in obj for k in CHAMPS_DE_NOM):
            sortie.append(obj)
        for v in obj.values():
            if isinstance(v, (dict, list)):
                _personnes(v, sortie)
    elif isinstance(obj, list):
        for v in obj:
            _personnes(v, sortie)


def personnes_du_blob(blob) -> list[dict]:
    """Les personnes d'un champ JSON de Hektor.
    ⛔ ON PARSE, ON NE LIT PAS LE TEXTE BRUT : sinon on ramasse les CLES
      (`nom`, `ville`, `datemaj`...) et on fabrique 31 127 faux partages.
    ⚠ Le champ est parfois un OBJET, parfois un TABLEAU, parfois une CHAINE
      contenant du JSON, parfois None. Les quatre sont geres."""
    if blob in (None, "", b""):
        return []
    if isinstance(blob, (bytes, bytearray)):
        try:
            blob = blob.decode("utf-8", "replace")
        except Exception:                                           # noqa: BLE001
            return []
    if isinstance(blob, str):
        s = blob.strip()
        if not s or s in {"null", "[]", "{}"}:
            return []
        try:
            blob = json.loads(s)
        except Exception:                                           # noqa: BLE001
            # ⚠ ON NE RETOMBE PAS SUR LE TEXTE BRUT : mieux vaut aucun nom
            #   qu'un nom faux. Une lecture ratee n'est jamais un vert.
            return []
    out: list[dict] = []
    _personnes(blob, out)
    return out


def noms_du_blob(blob) -> set[str]:
    """Les mots de nom des personnes d'un champ JSON."""
    out: set[str] = set()
    for p in personnes_du_blob(blob):
        for ch in CHAMPS_DE_NOM:
            if p.get(ch):
                out |= _mots_de_nom(p[ch])
    return out


def ids_du_blob(blob) -> set[str]:
    """Les IDENTIFIANTS de contact des personnes d'un champ JSON.
    ⭐⭐ C'est le signal le plus sur qui existe : « comparer des NOMS la ou il y a
      des IDENTIFIANTS » a coute quatre erreurs le 12/11."""
    out: set[str] = set()
    for p in personnes_du_blob(blob):
        for ch in ("id", "contact_id", "hektor_contact_id", "idcontact"):
            v = p.get(ch)
            if v not in (None, "", 0, "0"):
                out.add(str(v).strip())
    return out


def noms(texte) -> set[str]:
    """Les mots de nom d'un TEXTE LIBRE (une case du classeur)."""
    return _mots_de_nom(texte)


# ─────────────────────────────────────────────────────────────────────────────
# LIRE
# ─────────────────────────────────────────────────────────────────────────────
def lire_le_sheet():
    """(entetes, [(numero_de_ligne, ligne), ...]) -- ⚠ lecture reseau."""
    import sys
    sys.path.insert(0, str(RACINE / "phase2" / "checks"))
    from apparier_classeur import lire_classeur, load_env_file  # noqa: E402
    load_env_file(RACINE / ".env")
    entetes, brutes = lire_classeur()
    return entetes, [(n, l) for n, l in brutes]


COLONNES_TX = (
    "app_affaire_id", "kind", "state", "date", "date_acte", "montant",
    "numero_mandat", "hektor_annonce_id", "app_chaine_id",
    "acquereur_json", "acquereurs_json", "mandants_json", "propositions_json",
    "hektor_acquereur_id", "present_in_hektor",
)


def lire_le_registre():
    """Les transactions, depuis la base LOCALE, en lecture seule.
    ⚠ Elle porte l'etat de la derniere descente : les gestes du jour n'y sont
      pas encore. Sans consequence ici -- on apparie vers des TRANSACTIONS,
      dont le numero ne bouge JAMAIS."""
    con = sqlite3.connect("file:%s?mode=ro"
                          % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                          uri=True, timeout=30)
    c = con.cursor()
    c.execute("select %s from app_affaire_ledger" % ", ".join(COLONNES_TX))
    tx = [dict(zip(COLONNES_TX, r)) for r in c.fetchall()]
    con.close()
    return tx
