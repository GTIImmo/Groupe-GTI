#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE RAPPORT DU GEL, AVEC TOUS LES CHAMPS.                        29/10/2026

Demande de Frederic : « il faut d'abord refaire l'ensemble du rapport d'analyse
du gel avec TOUS les champs cette fois, et pense aux decouvertes ».

LECTURE SEULE DE BOUT EN BOUT. N'ecrit ni en base, ni chez Hektor, ni dans le
classeur. Produit deux fichiers dans notice/ : une synthese et un detail.

⭐ CE QU'IL COMPARE. Pour chaque ligne du classeur RATTACHEE par le gel
  (app_classeur_lien, cle « ID Unique »), les 38 colonnes du classeur face a ce
  que nous portons -- en prenant LA BONNE TRANSACTION pour chaque champ (la date
  du compromis sur le compromis, celle de la vente sur la vente).

⛔ LES DECOUVERTES DEJA PAYEES, ET CODEES ICI -- les oublier rendrait le rapport
  faux en silence :

  ① TTC / HT (sa consigne du 29/10, en majuscules) : le classeur est TTC,
    `commission_agence` est HT. Le bon vis-a-vis de « Commission TTC » est
    `honoraires_entree` (98,7 % des cas) ; `commission_agence` x 1,20 sert de repli.
  ② LE PRIX N'EST COMPARABLE QU'A PARTIR DE 2025. Mesure du 29/10 : 2026 95 %
    identiques, 2025 84 %, mais 2024 23 % et 2023 32 % avec 60-70 % de
    « classeur superieur » -- le classeur portait alors un PRIX D'ANNONCE.
    ⛔ Les ecarts d'avant 2025 sont donc marques « hors perimetre », pas « faux ».
  ③ LE PRIX PORTE PARFOIS UN DEPARTEMENT. 1 002 lignes de 2018-2020 ont 42, 43
    ou 63 dans la case Prix, et 13 un code postal. ⛔ NOUS faisons foi.
  ④ LE MONTANT EST EN CENTIMES sur le compromis et la vente, en EUROS sur l'offre.
  ⑤ LES DATES DU CLASSEUR SONT EN jj/mm/aaaa, les notres en aaaa-mm-jj.
    ⛔⛔ Melanger les deux conversions donne un signal MUET qui passe pour un
      signal VERT (defaut paye le 29/10). Deux fonctions, deux noms, un temoin.
  ⑥ LE BLOB NE PORTE QUE LE NOM DE FAMILLE. La fiche contact porte le nom
    complet, et c'est elle que l'ecran affiche (cas L80, « BOULAHIA » vs
    « Badia BOULAHIA »). On tolere aussi l'INVERSION nom/prenom du classeur.
  ⑦ LE CHAINAGE DOUTEUX : 219 transactions portent un nom ETRANGER a leur propre
    chaine. Un ecart de nom y est un probleme de CHAINAGE, pas de donnee.
    ⛔ Ces lignes sont marquees et la mise en conformite doit les SAUTER.
  ⑧ ⭐⭐ DEUX NOMS DU CLASSEUR SONT DES ALIAS, confirmes par Frederic le 29/10 :
    GIRAUD = Aline VALETTE (68) · ALVES MENDES = Lucie DECHANDON (178).
    ⛔ Sans eux on ajouterait la meme personne deux fois, et on couperait sa
      commission en deux -- sur 282 cases.
  ⑨ ⭐⭐ ET 14 NOMS SONT DE VRAIS ANCIENS NEGOCIATEURS ABSENTS DE NOTRE REGISTRE
    (dit par Frederic le 29/10). Ce ne sont NI des alias, NI des erreurs : c'est
    notre annuaire qui est incomplet. Ils sont comptes a part.
  ⑩ « meilleursagents » N'EST PAS UNE PERSONNE : un apporteur, toujours en
    negociateur 2 (17 fois sur 17).

    .venv\\Scripts\\python.exe phase2\\checks\\rapport_gel_tous_les_champs.py
"""
from __future__ import annotations

import csv
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

import requests

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "sync"))
from push_contacts_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES,
    load_env_file,
)

SHEET_ID = "1wFd3pQYItvOrbk10W0r--bmhOaV1R4tWgZ3dq1XCipk"
ONGLET = "Sheet1"

#: ⭐ LES ALIAS CONFIRMES PAR FREDERIC (29/10) -- « OUI C'EST LA MEME PERSONNE ».
#:   Preuves : l'alias SEUL negociateur donne 70/70 et 55/58 ; les deux noms ne
#:   coexistent JAMAIS sur une ligne ; le nom cible n'apparait JAMAIS au classeur.
#: ⭐ DEPUIS LE 09/11/2026 CES ALIAS VIVENT EN BASE, dans la table
#:   `app_classeur_alias_negociateur` (posee avec l'accord de Frederic).
#:   Ce dictionnaire n'est plus que le REPLI : si la table est illisible, on
#:   garde les deux alias connus PLUTOT que de les perdre en silence -- sans eux
#:   le rapport compte la meme personne deux fois sur 282 cases.
#: ⛔ ET LE REPLI SE DIT A L'ECRAN. Un repli muet est un faux vert.
#: ⚠ LES NOMBRES CI-DESSOUS SONT DES `hektor_user_id`, et le code les compare
#:   bien a des hektor_user_id (l. 556) : il etait JUSTE. Mais un nombre seul est
#:   AMBIGU -- 68 et 178 sont AUSSI des numeros de NEGOCIATEUR, et ils designent
#:   alors Nadege PEYRARD et David BADIER, deux autres personnes. C'est pour ca
#:   que la table porte `app_personne_id`, qui n'a qu'un seul sens possible.
ALIAS_REPLI = {
    "GIRAUD": ("68", "Aline VALETTE"),
    "ALVES MENDES": ("178", "Lucie DECHANDON"),
}

#: Rempli par charger_alias() au demarrage. Jamais lu avant.
ALIAS_NEGOCIATEUR: dict[str, tuple[str, str]] = {}


def charger_alias(cl) -> str:
    """Lit `app_classeur_alias_negociateur` et remplit ALIAS_NEGOCIATEUR.

    La table porte `app_personne_id` ; le rapport, lui, compare des
    `hektor_user_id`. On fait donc le pont par les FICHES de la personne -- et
    une personne peut en avoir plusieurs, ce qu'un nombre code en dur ne savait
    pas porter.

    Rend une phrase a IMPRIMER : d'ou viennent les alias, et combien.
    ⛔ Sur echec, on retombe sur ALIAS_REPLI et on le DIT.
    """
    global ALIAS_NEGOCIATEUR
    try:
        rangs = lire_tout(cl, "app_classeur_alias_negociateur",
                          "texte_classeur,app_personne_id,nom_chez_nous",
                          "texte_classeur.asc")
        fiches = lire_tout(cl, "app_negociateur_fiche",
                           "app_personne_id,hektor_user_id", "app_personne_id.asc")
    except Exception as exc:  # noqa: BLE001
        ALIAS_NEGOCIATEUR = dict(ALIAS_REPLI)
        return ("alias : LECTURE DE LA TABLE RATEE (%s) -> REPLI sur les %d alias "
                "codes. Ce n'est PAS un vert." % (type(exc).__name__, len(ALIAS_REPLI)))
    if not rangs:
        ALIAS_NEGOCIATEUR = dict(ALIAS_REPLI)
        return ("alias : la table est VIDE -> REPLI sur les %d alias codes. "
                "A verifier." % len(ALIAS_REPLI))

    user_ids: dict[str, set[str]] = {}
    for f in fiches:
        pid = str(f.get("app_personne_id") or "").strip()
        uid = str(f.get("hektor_user_id") or "").strip()
        if pid and uid:
            user_ids.setdefault(pid, set()).add(uid)

    neuf: dict[str, tuple[str, str]] = {}
    muets: list[str] = []
    for r in rangs:
        texte = str(r.get("texte_classeur") or "").strip()
        pid = str(r.get("app_personne_id") or "").strip()
        nom = str(r.get("nom_chez_nous") or "").strip()
        ids = sorted(user_ids.get(pid, set()))
        if not texte or not ids:
            muets.append("%s (personne %s sans hektor_user_id)" % (texte, pid))
            continue
        # plusieurs fiches -> plusieurs user_id : on les garde tous, separes
        for uid in ids:
            neuf.setdefault(texte, (uid, nom))
    ALIAS_NEGOCIATEUR = neuf
    phrase = "alias : %d lus EN BASE (table du 09/11)" % len(neuf)
    if muets:
        phrase += " . ⚠ %d SANS IDENTIFIANT : %s" % (len(muets), ", ".join(muets))
    return phrase

#: ⭐ DE VRAIS ANCIENS NEGOCIATEURS, ABSENTS DE NOTRE REGISTRE (Frederic, 29/10).
#:   ⛔ NE PAS les traiter comme des erreurs : c'est l'annuaire qui est incomplet.
ANCIENS_HORS_REGISTRE = {
    "ABED", "ALLEMAND", "BERTRAND", "AGRAIN", "PETROSINO", "BRUNON", "LAUGIER",
    "EXBRAYAT", "COMMERE", "ADAMO", "LEFAURE", "PITIOT", "BALIQUE",
    "FRANCHINI Marjorie",
}

#: Ni une personne, ni un negociateur : un apporteur d'affaires.
PAS_UNE_PERSONNE = {"meilleursagents", "GTI", "DENOPCE 1/2"}

#: ⛔ L'annee a partir de laquelle le PRIX du classeur est comparable (decouverte ②).
PRIX_COMPARABLE_DES = 2025

#: ⛔⛔ DEFAUT CORRIGE LE 29/10, ET IL ETAIT GRAVE. Ma premiere version prenait
#:   TOUT nombre a cinq chiffres pour un code postal : elle a ecarte 1 725 VRAIS
#:   PRIX (18 160 EUR, 46 000 EUR, 76 000 EUR...) en les declarant « hors
#:   perimetre ». Un prix hors perimetre ne se corrige pas : le defaut aurait
#:   fait renoncer a 1 725 corrections legitimes, EN SILENCE.
#: ➡ Un departement tient sur UN a TROIS chiffres. Rien d'autre ne s'exclut
#:   automatiquement : les ~13 codes postaux reels tomberont en ECART, nommes.
RE_DEPARTEMENT = re.compile(r"^\s*\d{1,3}\s*$")

#: ⭐ LA NATURE DU BIEN : le classeur ecrit une FAMILLE (« Maison »), nous un
#:   CODE NUMERIQUE ('1'). Table tiree de `draftAnnoncePropertyGroups`
#:   (App.tsx:856) -- la source du projet, pas une invention.
#: ⭐⭐ L'AMBIGUITE DU CODE 17 EST TRANCHEE PAR LA MESURE (05/11/2026). La crainte
#:   ecrite ici disait : « 17 vaut Chalet en habitation et Local professionnel en
#:   commerce (App.tsx:908 et 934), sans `commerce_sous_type` on ne tranche pas ».
#:   LA BASE DIT AUTREMENT, et la regle est absolue, avec son temoin inverse :
#:     code 17 ->  86 lignes sur  86 SANS sous-type commerce -> jamais du commerce
#:     code 23 -> 526 lignes sur 526 AVEC sous-type commerce -> toujours du commerce
#:   -> le commerce se reconnait au CODE 23, pas au 17. Un chalet est une MAISON.
#: ⛔ CE QUE LA TABLE NE TRADUIT PAS, ET C'EST VOULU (exclusion DECLAREE) :
#:   les 38 MANDATS DE RECHERCHE portent une LISTE DE SOUHAITS en TEXTE
#:   (« Maison / Villa / Mas »), jamais un code. Regle absolue mesuree le 05/11 :
#:   38 sur 38 sont `recherche` ET sans annonce ; 24 539 sur 24 539 codes
#:   numeriques sont des biens reels. Un souhait multiple n'a pas de famille --
#:   ces lignes sortent en « hors table », nommees, et c'est le bon resultat.
#: ⬜ Restent 2 codes NON IDENTIFIES, laisses dehors EXPRES : « 38 » (1 ligne) et
#:   « 0 » (1 ligne) -- absents des deux listes de l'app. Ne pas les deviner.
FAMILLE_DU_CODE = {
    # les maisons
    "11": "Maison", "28": "Maison", "30": "Maison", "1": "Maison", "39": "Maison",
    "10": "Maison", "22": "Maison", "27": "Maison", "49": "Maison", "25": "Maison",
    # les appartements
    "2": "Appartement", "18": "Appartement", "31": "Appartement", "26": "Appartement",
    "4": "Appartement", "41": "Appartement", "50": "Appartement",
    # les terrains
    "5": "Terrain", "44": "Terrain", "45": "Terrain", "43": "Terrain",
    # les autres
    "20": "Autre", "24": "Autre", "29": "Autre", "15": "Garage",
    "21": "Immeuble", "16": "Garage", "7": "Autre",
    # ⭐ le 17 est un CHALET (App.tsx:908) : une MAISON, pas un « autre ».
    #   86 lignes sur 86 sans sous-type commerce -> l'ambiguite n'existe pas.
    "17": "Maison",
    # ⭐ le 23 est l'immobilier PROFESSIONNEL, absent des deux listes de l'app.
    #   Le vrai type est dans `commerce_sous_type` (Bureaux, Fonds de commerce,
    #   Local d'activite...). 526 lignes sur 526 en portent un.
    "23": "Commerce",
}

#: Ce que le classeur ecrit, ramene a la meme famille.
FAMILLE_DU_CLASSEUR = {
    "maison": "Maison", "appartement": "Appartement", "terrain": "Terrain",
    "immeuble": "Immeuble", "garage": "Garage", "parking": "Garage",
    "local commercial": "Commerce", "commerce": "Commerce", "autre": "Autre",
}


# ───────────────────────────────── les conversions de date
# ⛔⛔ DEUX FONCTIONS, DEUX NOMS, ET ELLES NE SE MELANGENT PAS. Le 29/10 j'ai
#   applique `jour()` (qui convertit NOS dates VERS le format du classeur) a des
#   dates DU classeur : elle rendait "" et le signal annoncait « 0 ecart ».
def date_du_classeur(v) -> date | None:
    """jj/mm/aaaa (le format du classeur) -> un objet date."""
    t = str(v or "").strip()
    if not t:
        return None
    for forme in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(t, forme).date()
        except ValueError:
            continue
    return None


def date_de_chez_nous(v) -> date | None:
    """aaaa-mm-jj[THH:MM:SS...] (le format du registre) -> un objet date."""
    t = str(v or "").strip()
    if not t or t.startswith("0000"):
        return None
    try:
        return datetime.strptime(t[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


# ───────────────────────────────── les noms
MOTS_DE_FORME = {"MME", "MLLE", "MONSIEUR", "MADAME", "SCI", "SARL", "SAS", "INDIVISION",
                 "CONSORTS", "HOIRIE", "SUCCESSION", "VEUVE", "EPOUX", "EPOUSE"}


def mots_du_nom(v) -> set[str]:
    """Les mots exploitables d'un nom, FORMES COLLEES COMPRISES.

    ⛔⛔ TROIS DEFAUTS CORRIGES le 29/10, chacun trouve par un temoin positif :
      . un seuil de 4 lettres jetait KUS (47 cases), GTI, SAY -> seuil a 3 ;
      . le classeur COLLE ce que l'annuaire SEPARE (DIMARIA / DI MARIA) ;
      . ⛔ filtrer la particule (DI, DE = 2 lettres) AVANT d'aplatir donnait
        « MAGALIMARIA » au lieu de « DIMARIA » : on aplatit D'ABORD.
    """
    t = unicodedata.normalize("NFKD", str(v or "")).encode("ascii", "ignore").decode()
    t = t.upper().replace("-", " ").replace("'", " ").replace(".", " ").replace(",", " ")
    tous = [m for m in t.split() if m and m not in MOTS_DE_FORME]
    out = {m for m in tous if len(m) >= 3}
    for i in range(len(tous)):
        for j in range(i + 2, len(tous) + 1):
            colle = "".join(tous[i:j])
            if len(colle) >= 3:
                out.add(colle)
    return out


def aplati(v) -> str:
    """Une chaine ramenee a ses lettres, sans accent ni ponctuation."""
    t = unicodedata.normalize("NFKD", str(v or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z]", "", t.upper())


def se_ressemblent(a, b, seuil: float = 0.82) -> bool:
    """RAPPROCHEMENT TOLERANT AUX FAUTES DE FRAPPE -- demande de Frederic :
    « lorsqu'on cherche le nom on rapproche meme avec faute de frappe ».

    ⭐ Mesure du 29/10, sur les villes : « Olliergue » / « Olliergues » et
      « Chamaliere s/Loire » / « Chamalieres-sur-Loire » sont la MEME commune,
      et une comparaison mot a mot les declarait differentes.
    ⚠ ON NE DESCEND PAS SOUS 0,82 : plus bas, « Saint-Just » rejoindrait
      « Saint-Jean ». Le seuil est un choix, pas une evidence.
    """
    from difflib import SequenceMatcher
    x, y = aplati(a), aplati(b)
    if not x or not y:
        return False
    if x == y or x.startswith(y) or y.startswith(x):
        return True
    return SequenceMatcher(None, x, y).ratio() >= seuil


def nombre(v) -> float | None:
    t = str(v or "").strip().replace(" ", "").replace(" ", "")
    t = t.replace("€", "").replace("EUR", "")
    if not t:
        return None
    # le classeur ecrit « 162 500,00 » ou « 162500.00 »
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def euros(v, kind: str) -> float | None:
    """⛔⛔ DEFAUT CORRIGE LE 29/10, ET C'EST FREDERIC QUI L'A VU A L'ECRAN :
    « pourquoi sur ton tableau les prix sont comme ca ? » -- 181.6, 510.0, 1950.0.

    J'AVAIS DIVISE PAR 100 le compromis et la vente, sur la foi d'une note
    disant « montant en CENTIMES pour compromis/vente, en EUROS pour l'offre ».
    ⛔ CETTE REGLE NE VAUT PAS POUR app_affaire_ledger.montant. Mesure du jour :

        compromis  mediane  97 000     offre  mediane  95 000
        vente      mediane  99 000     et compromis/vente portent « .00 »

    Un bien a 18 160 EUR devenait 181,60 -- et l'ecart de prix etait alors
    TOUJOURS faux, sur les 4 680 lignes.
    ⭐ ET LE PROJET L'AVAIT DEJA ECRIT, dans le patch du 08/09 :
      « TEXTE, comme montant et sequestre : on recopie ce que Hektor ecrit
        (« 162500.00 »), on ne le reinterprete pas. »
    ➡ LECON : une regle lue dans une note se MESURE sur la table avant d'etre
      appliquee. Un commentaire n'est pas une mesure.
    """
    return nombre(v)


# ───────────────────────────────── les sources
def charger_classeur() -> tuple[list[str], list[list]]:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_file(
        os.environ["GOOGLE_WORKSPACE_SERVICE_ACCOUNT_FILE"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    ).with_subject(os.environ["GOOGLE_WORKSPACE_SUBJECT_EMAIL"])
    creds.refresh(Request())
    rep = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{ONGLET}!A1:AL6000",
        headers={"Authorization": f"Bearer {creds.token}"}, timeout=180)
    rep.raise_for_status()
    val = rep.json().get("values", [])
    if not val:
        raise SystemExit("ARRET : le classeur est vide")
    return val[0], [l for l in val[1:] if any(str(x).strip() for x in l)]


def client():
    for f in DEFAULT_ENV_FILES:
        load_env_file(f)
    from repartition_commission import client as _c
    cl = _c()
    if cl is None:
        raise SystemExit("ARRET : pas de client Supabase")
    return cl


def lire_tout(cl, table: str, champs: str, ordre: str) -> list[dict]:
    """⚠ ORDRE TOTAL OBLIGATOIRE : limit/offset sans `order` saute des lignes en
    silence (lecon du 15/09 : 4 lignes sur 13 309 invisibles)."""
    out: list[dict] = []
    while True:
        page = cl.request(method="GET", path=(
            f"{table}?select={champs}&order={ordre}&limit=1000&offset={len(out)}"))
        if not isinstance(page, list) or not page:
            return out
        out.extend(page)
        if len(page) < 1000:
            return out


def noms_du_blob(blob) -> set[str]:
    """Les noms portes par un blob de parties (liste OU objet seul).
    ⚠ Une forme inconnue doit rendre un ENSEMBLE VIDE, jamais lever."""
    import json
    if blob is None:
        return set()
    charge = blob
    if isinstance(blob, str):
        try:
            charge = json.loads(blob)
        except (TypeError, ValueError):
            return mots_du_nom(blob)
    gens = charge if isinstance(charge, list) else [charge] if isinstance(charge, dict) else []
    out: set[str] = set()
    for g in gens:
        if not isinstance(g, dict):
            continue
        for cle in ("nom", "display_name", "raison_sociale", "prenom"):
            out |= mots_du_nom(g.get(cle))
    return out


# ───────────────────────────────── le verdict d'un champ
IDENTIQUE = "identique"
ECART = "ECART"
CLASSEUR_SEUL = "classeur seul"
NOUS_SEULS = "nous seuls"
VIDES = "les deux vides"
HORS = "hors perimetre"


def verdict(a_classeur, a_nous, egal) -> str:
    vide_c = a_classeur in (None, "", [])
    vide_n = a_nous in (None, "", [])
    if vide_c and vide_n:
        return VIDES
    if vide_c:
        return NOUS_SEULS
    if vide_n:
        return CLASSEUR_SEUL
    return IDENTIQUE if egal else ECART


def main() -> int:
    cl = client()
    print(charger_alias(cl))   # ⭐ AVANT tout calcul : le rapport s'en sert au ⑧
    entetes, lignes = charger_classeur()
    idx = {n: i for i, n in enumerate(entetes)}

    def case(l, nom):
        i = idx.get(nom)
        return str(l[i]).strip() if i is not None and i < len(l) else ""

    print("classeur : %d lignes, %d colonnes" % (len(lignes), len(entetes)))

    liens = lire_tout(cl, "app_classeur_lien", "id_unique,app_affaire_id,role,confiance,preuves",
                      "id_unique.asc,app_affaire_id.asc")
    led = lire_tout(cl, "app_affaire_ledger",
                    "app_affaire_id,app_chaine_id,kind,state,numero_mandat,montant,date,date_acte,"
                    "honoraires_entree,honoraires_sortie,commission_agence,charge_commission_app,"
                    "acquereurs_json,mandants_json,notaire_acquereur_nom,notaire_mandant_nom,"
                    "hektor_annonce_id", "app_affaire_id.asc")
    rep = lire_tout(cl, "app_affaire_repartition",
                    "app_chaine_id,cote,rang,hektor_user_id,nom_au_moment,pourcentage,origine",
                    "app_chaine_id.asc,cote.asc,rang.asc")
    reg = lire_tout(cl, "app_mandat_register_current",
                    "hektor_annonce_id,numero_mandat,numero_dossier,ville,type_bien,"
                    "agence_nom,commercial_nom",
                    "hektor_annonce_id.asc,numero_mandat.asc")
    print("gel : %d liens · registre : %d transactions · repartition : %d · mandats : %d"
          % (len(liens), len(led), len(rep), len(reg)))

    tx = {str(x["app_affaire_id"]): x for x in led}
    par_id: dict[str, list[dict]] = defaultdict(list)
    for x in liens:
        par_id[str(x["id_unique"]).strip()].append(x)
    par_chaine: dict[str, list[dict]] = defaultdict(list)
    for x in rep:
        par_chaine[str(x["app_chaine_id"])].append(x)
    par_annonce: dict[str, dict] = {}
    for x in reg:
        par_annonce.setdefault(str(x.get("hektor_annonce_id") or ""), x)

    # ⭐ LE CHAINAGE DOUTEUX (decouverte ⑦) : une transaction dont le nom
    #   d'acquereur est etranger a TOUTES ses voisines de chaine.
    membres: dict[str, list[dict]] = defaultdict(list)
    for x in led:
        if x.get("app_chaine_id"):
            membres[str(x["app_chaine_id"])].append(x)
    douteuse: set[str] = set()
    for _ch, gens in membres.items():
        if len(gens) < 2:
            continue
        for x in gens:
            mien = noms_du_blob(x.get("acquereurs_json"))
            if not mien:
                continue
            voisins: set[str] = set()
            for y in gens:
                if str(y["app_affaire_id"]) != str(x["app_affaire_id"]):
                    voisins |= noms_du_blob(y.get("acquereurs_json"))
            if voisins and not (mien & voisins):
                douteuse.add(str(x["app_affaire_id"]))
    print("chainage douteux : %d transaction(s) portent un nom etranger a leur chaine"
          % len(douteuse))

    CHAMPS = ["Mandat", "Prix", "Commission TTC", "Charge Commission", "Offre Achat",
              "Compromis", "Vente Prevue", "Vente Fixee", "Etat Actuel", "Acquereur",
              "Vendeur", "Notaire", "Negociateur 1", "Negociateur 2", "Negociateur 3",
              "Agence", "Ville", "Nature", "Vente Reglee", "Numero de facture",
              "product_ref"]
    synthese: dict[str, Counter] = {c: Counter() for c in CHAMPS}
    detail: list[dict] = []
    notes = Counter()

    for l in lignes:
        iu = case(l, "ID Unique")
        ls = par_id.get(iu, [])
        if not ls:
            notes["ligne NON RATTACHEE par le gel"] += 1
            continue
        parr: dict[str, dict] = {}
        for x in ls:
            t = tx.get(str(x["app_affaire_id"]))
            if t:
                parr[str(x.get("role") or t.get("kind") or "")] = t
        if not parr:
            notes["rattachee mais transaction absente du registre"] += 1
            continue
        la_plus_avancee = parr.get("vente") or parr.get("compromis") or parr.get("offre")
        chaine = str(la_plus_avancee.get("app_chaine_id") or "")
        annonce = str(la_plus_avancee.get("hektor_annonce_id") or "")
        mandat_reg = par_annonce.get(annonce, {})
        ligne = {"ID Unique": iu, "Mandat classeur": case(l, "Mandat"),
                 "Etat classeur": case(l, "Etat Actuel"),
                 "roles geles": "+".join(sorted(parr)),
                 "chainage douteux": "OUI" if any(
                     str(t["app_affaire_id"]) in douteuse for t in parr.values()) else ""}

        def pose(champ, val_c, val_n, v):
            synthese[champ][v] += 1
            ligne["c_" + champ] = "" if val_c is None else str(val_c)
            ligne["n_" + champ] = "" if val_n is None else str(val_n)
            ligne["v_" + champ] = v

        # ── ① LE MANDAT
        c = case(l, "Mandat")
        n = str(la_plus_avancee.get("numero_mandat") or "") or str(mandat_reg.get("numero_mandat") or "")
        pose("Mandat", c, n, verdict(c, n, c.strip() == n.strip()))

        # ── ② LE PRIX -- ⛔ comparable a partir de 2025 SEULEMENT
        c_brut = case(l, "Prix")
        annee = None
        for champ_date in ("Vente Fixee", "Vente Prevue", "Compromis", "Offre Achat"):
            d = date_du_classeur(case(l, {"Vente Fixee": "Vente Fixée", "Vente Prevue": "Vente Prévue",
                                          "Compromis": "Compromis", "Offre Achat": "Offre Achat"}[champ_date]))
            if d:
                annee = d.year
                break
        n_prix = euros(la_plus_avancee.get("montant"), str(la_plus_avancee.get("kind") or ""))
        if RE_DEPARTEMENT.match(c_brut):
            pose("Prix", c_brut, n_prix, HORS)
            notes["Prix : le classeur porte un DEPARTEMENT (1 a 3 chiffres)"] += 1
        elif annee is not None and annee < PRIX_COMPARABLE_DES:
            pose("Prix", c_brut, n_prix, HORS)
            notes["Prix : annee < %d, hors perimetre (decouverte 2)" % PRIX_COMPARABLE_DES] += 1
        else:
            cp, np_ = nombre(c_brut), n_prix
            egal = cp is not None and np_ is not None and abs(cp - np_) <= max(1.0, 0.005 * max(cp, np_))
            pose("Prix", c_brut, np_, verdict(c_brut, np_, egal))

        # ── ③ LA COMMISSION -- ⛔ classeur TTC, commission_agence HT
        c_com = nombre(case(l, "Commission TTC"))
        n_com = nombre(la_plus_avancee.get("honoraires_entree"))
        voie = "honoraires_entree (TTC)"
        if n_com is None:
            ht = nombre(la_plus_avancee.get("commission_agence"))
            if ht is not None:
                n_com, voie = ht * 1.20, "commission_agence x 1,20 (HT -> TTC)"
        egal = c_com is not None and n_com is not None and abs(c_com - n_com) <= max(1.0, 0.01 * max(c_com, n_com))
        pose("Commission TTC", case(l, "Commission TTC"),
             None if n_com is None else round(n_com, 2), verdict(c_com, n_com, egal))
        if n_com is not None:
            notes["Commission lue par : " + voie] += 1

        pose("Charge Commission", case(l, "Charge Commission"),
             la_plus_avancee.get("charge_commission_app"),
             verdict(case(l, "Charge Commission"), la_plus_avancee.get("charge_commission_app"),
                     str(case(l, "Charge Commission")).lower()[:3]
                     == str(la_plus_avancee.get("charge_commission_app") or "").lower()[:3]))

        # ── ④ LES QUATRE DATES, chacune sur SA transaction
        for champ_c, role, cle in (("Offre Achat", "offre", "date"),
                                   ("Compromis", "compromis", "date"),
                                   ("Vente Prévue", "compromis", "date_acte"),
                                   ("Vente Fixée", "vente", "date")):
            nom_sortie = champ_c.replace("Prévue", "Prevue").replace("Fixée", "Fixee")
            dc = date_du_classeur(case(l, champ_c))
            t = parr.get(role)
            dn = date_de_chez_nous(t.get(cle)) if t else None
            egal = dc is not None and dn is not None and abs((dc - dn).days) <= 3
            pose(nom_sortie, dc, dn, verdict(dc, dn, egal))

        # ── ⑤ L'ETAT / L'AVANCEMENT
        etat = case(l, "Etat Actuel")
        etats = {str(t.get("state") or "").lower() for t in parr.values()}
        if parr.get("vente"):
            notre = "VENDU"
        elif any("cancel" in e or "annul" in e or "refus" in e for e in etats):
            notre = "ANNULE"
        elif parr.get("compromis"):
            notre = "COMPROMIS"
        elif parr.get("offre"):
            notre = "OFFRE"
        else:
            notre = ""
        attendu = ("VENDU" if "égl" in etat or "ixé" in etat or "ixe" in etat
                   else "ANNULE" if "nnul" in etat
                   else "COMPROMIS" if "ompromis" in etat or "révue" in etat or "revue" in etat
                   else "OFFRE" if "ffre" in etat else "")
        pose("Etat Actuel", etat, notre, verdict(etat, notre, attendu == notre))

        # ── ⑥ LES PARTIES -- ⛔ le blob ne porte que le nom de famille
        for champ_c, cle in (("Acquéreur", "acquereurs_json"), ("Vendeur", "mandants_json")):
            nom_sortie = champ_c.replace("Acquéreur", "Acquereur")
            c_mots = mots_du_nom(case(l, champ_c))
            n_mots: set[str] = set()
            for t in parr.values():
                n_mots |= noms_du_blob(t.get(cle))
            # ⭐ un mot commun d'abord, puis le rapprochement TOLERANT mot a mot
            egal = bool(c_mots & n_mots) or any(
                se_ressemblent(a, b) for a in c_mots for b in n_mots)
            pose(nom_sortie, case(l, champ_c), " ".join(sorted(n_mots)) or None,
                 verdict(case(l, champ_c), n_mots or None, egal))

        # ── ⑦ LE NOTAIRE
        c_not = mots_du_nom(case(l, "Notaire"))
        n_not: set[str] = set()
        for t in parr.values():
            n_not |= mots_du_nom(t.get("notaire_acquereur_nom")) | mots_du_nom(t.get("notaire_mandant_nom"))
        pose("Notaire", case(l, "Notaire"), " ".join(sorted(n_not)) or None,
             verdict(case(l, "Notaire"), n_not or None, bool(c_not & n_not)))

        # ── ⑧ LES TROIS NEGOCIATEURS -- ⭐ alias et anciens hors registre
        nos_lignes = par_chaine.get(chaine, [])
        nos_ids = {str(r["hektor_user_id"]).strip() for r in nos_lignes
                   if str(r.get("hektor_user_id") or "").strip()}
        nos_mots: set[str] = set()
        for r in nos_lignes:
            nos_mots |= mots_du_nom(r.get("nom_au_moment"))
        nos_mots |= mots_du_nom(mandat_reg.get("commercial_nom"))
        for rang, champ_c in ((1, "Négociateur 1"), (2, "Négociateur 2"), (3, "Négociateur 3")):
            nom_sortie = "Negociateur %d" % rang
            brut = case(l, champ_c)
            if not brut:
                pose(nom_sortie, "", "", VIDES)
                continue
            if brut in PAS_UNE_PERSONNE:
                pose(nom_sortie, brut, "", HORS)
                notes["Negociateur : « %s » n'est pas une personne" % brut] += 1
                continue
            if brut in ALIAS_NEGOCIATEUR:
                ident, vrai = ALIAS_NEGOCIATEUR[brut]
                trouve = ident in nos_ids
                pose(nom_sortie, "%s (alias de %s)" % (brut, vrai),
                     vrai if trouve else "", IDENTIQUE if trouve else CLASSEUR_SEUL)
                notes["Negociateur : alias applique (%s -> %s)" % (brut, vrai)] += 1
                continue
            if brut in ANCIENS_HORS_REGISTRE:
                pose(nom_sortie, brut, "", HORS)
                notes["Negociateur : ancien ABSENT de notre registre"] += 1
                continue
            cm = mots_du_nom(brut)
            pose(nom_sortie, brut, " ".join(sorted(nos_mots)) or None,
                 verdict(brut, nos_mots or None, bool(cm & nos_mots)))

        # ── ⑨ LE BIEN : agence et ville, AVEC tolerance aux fautes de frappe
        for champ_c, cle in (("Agence", "agence_nom"), ("Ville", "ville")):
            c_v, n_v = case(l, champ_c), str(mandat_reg.get(cle) or "")
            cm, nm = mots_du_nom(c_v), mots_du_nom(n_v)
            egal = bool(cm & nm) or se_ressemblent(c_v, n_v)
            pose(champ_c, c_v, n_v, verdict(c_v, n_v, egal))

        # ── ⑨ bis LA NATURE se compare par FAMILLE, jamais mot a mot
        c_nat = case(l, "Nature")
        code = str(mandat_reg.get("type_bien") or "").strip()
        fam_c = FAMILLE_DU_CLASSEUR.get(c_nat.lower().strip())
        fam_n = FAMILLE_DU_CODE.get(code)
        libelle = "%s -> %s" % (code, fam_n or "code inconnu") if code else ""
        if c_nat and code and fam_c is None:
            pose("Nature", c_nat, libelle, HORS)
            notes["Nature : famille du classeur non repertoriee (« %s »)" % c_nat] += 1
        elif code and fam_n is None:
            pose("Nature", c_nat, libelle, HORS)
            notes["Nature : code %s hors table (serie commerce ?)" % code] += 1
        else:
            pose("Nature", c_nat, libelle, verdict(c_nat, libelle, fam_c == fam_n))

        # ── ⑩ CE QUE NOUS N'AVONS NULLE PART
        for champ_c in ("Vente Réglée", "Numéro de facture"):
            nom_sortie = champ_c.replace("Réglée", "Reglee").replace("Numéro", "Numero")
            v = case(l, champ_c)
            pose(nom_sortie, v, None, CLASSEUR_SEUL if v else VIDES)
        # ⛔⛔ DEFAUT CORRIGE LE 29/10 -- Frederic : « je pense qu'il y a un
        #   probleme avec la colonne ref prod chez nous ». Il avait raison.
        #   `product_ref` du classeur N'EST PAS un numero d'annonce : c'est NOTRE
        #   NUMERO DE DOSSIER (VM68712, VA3224, VT9194 -- 442 valeurs de 7
        #   caracteres, 135 de 6, et 33 seulement tout en chiffres).
        #   Je le comparais a `hektor_annonce_id` : les « 646 ecarts » etaient
        #   646 CONCORDANCES mesurees contre la mauvaise colonne.
        # ⭐ Repli sur le numero d'annonce pour les 33 valeurs numeriques.
        c_ref = case(l, "product_ref")
        dossier = str(mandat_reg.get("numero_dossier") or "")
        if c_ref.isdigit():
            pose("product_ref", c_ref, annonce, verdict(c_ref, annonce, c_ref.strip() == annonce.strip()))
        else:
            pose("product_ref", c_ref, dossier,
                 verdict(c_ref, dossier, c_ref.strip().upper() == dossier.strip().upper()))

        detail.append(ligne)

    # ───────────────────────────────── la synthese
    print("")
    print("=" * 96)
    print("LA SYNTHESE PAR CHAMP -- sur %d lignes rattachees" % len(detail))
    print("=" * 96)
    print("%-20s %8s %8s %10s %9s %8s %8s" % ("champ", "identiq", "ECART", "class.seul",
                                              "nous seuls", "vides", "hors"))
    for c in CHAMPS:
        s = synthese[c]
        print("%-20s %8d %8d %10d %9d %8d %8d" % (
            c, s[IDENTIQUE], s[ECART], s[CLASSEUR_SEUL], s[NOUS_SEULS], s[VIDES], s[HORS]))

    print("")
    print("-- LES NOTES, ET LES DECOUVERTES APPLIQUEES --")
    for k, v in notes.most_common():
        print("   %-62s %6d" % (k, v))

    # ───────────────────────────────── les fichiers
    colonnes = ["ID Unique", "Mandat classeur", "Etat classeur", "roles geles", "chainage douteux"]
    for c in CHAMPS:
        colonnes += ["c_" + c, "n_" + c, "v_" + c]
    # ⭐ LE RAPPORT PORTE LA DATE DE SA MESURE, pas une date figee dans le code.
    #   Avant le 09/11 les deux noms etaient gravés au 29/10 : relancer le
    #   rapport ECRASAIT la mesure d'origine en MENTANT sur sa date.
    jour = date.today().isoformat()
    dest = RACINE / "notice" / ("A4_RAPPORT_GEL_TOUS_LES_CHAMPS_%s.csv" % jour)
    with open(dest, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=colonnes, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(detail)
    print("\ndetail complet : %s  (%d lignes)" % (dest, len(detail)))

    ecarts = [d for d in detail if any(d.get("v_" + c) == ECART for c in CHAMPS)]
    dest2 = RACINE / "notice" / ("A4_RAPPORT_GEL_ECARTS_SEULS_%s.csv" % jour)
    with open(dest2, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=colonnes, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(ecarts)
    print("les ecarts seuls : %s  (%d lignes)" % (dest2, len(ecarts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
