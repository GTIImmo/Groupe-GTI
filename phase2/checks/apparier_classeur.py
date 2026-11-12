"""COPIE REPAREE de rapprocher_classeur_suivi.py -- 28/10/2026.

⛔ L'ORIGINAL N'EST PAS TOUCHE : il reste LE TEMOIN. Lance tel quel, il doit rendre
   EXACTEMENT le meme resultat que lui (4 595 / 4 773 le 28/10).

LES TROIS REPARATIONS, chacune derriere son interrupteur, pour mesurer ce que
CHACUNE rapporte :

  --reparer prix      ⛔ le classeur donne des EUROS, et nous stockons selon le GENRE :
                         l'OFFRE en euros (mediane 95 000), le COMPROMIS et la VENTE
                         en CENTIMES (mediane 9 700 000 et 9 900 000, 99 % des lignes).
                         L'etage « mandat + prix » ne pouvait donc matcher QUE sur une
                         offre. On ajoute la valeur en euros A COTE de celle en centimes
                         -- on n'enleve rien, on ne peut donc rien perdre.

  --reparer dates     ⛔ on n'utilisait que la colonne `date`, jamais `date_acte`, et du
                         cote classeur on ignorait « Vente Prevue ».
                         Or l'ecran de Hektor le dit : « Signature acte auth. PREVU le »
                         = `compromis.date_acte` = « Vente Prevue ». La moitie des dates
                         etait ignoree DES DEUX COTES, alors que la date est le signal
                         le plus sur (4,4 % de collisions contre 48 % pour le vendeur).

  --reparer propositions  ⛔ 12/11/2026. Pour une OFFRE, `date` porte le DERNIER
                         mouvement. Nos 1 185 refus du 11/11 ont donc deplace la date
                         de 1 185 offres au 11/11/2026, et 17 lignes gelees le 29/10
                         etaient PERDUES pour cette seule raison. On ajoute les dates
                         du journal (propositions_json), comme le chainage le fait deja.

  --reparer plafond   ⛔ l'etage 9 (« sans mandat », celui qui rattrape les MANDATS DE
                         RECHERCHE) ne regardait que les chaines dont la derniere date
                         est >= 2026-01-01. Toute ligne plus ancienne etait hors
                         d'atteinte -- d'ou seulement 30 rattrapages.

  --reparer tout      les trois

    .venv\\Scripts\\python.exe phase2\\checks\\apparier_classeur.py
    .venv\\Scripts\\python.exe phase2\\checks\\apparier_classeur.py --reparer prix
    .venv\\Scripts\\python.exe phase2\\checks\\apparier_classeur.py --reparer tout

⛔ LECTURE SEULE, des deux cotes. N'ecrit qu'un CSV, que personne ne lit.

────────────────────────────────────────────────────────────────────────────────
L'EN-TETE D'ORIGINE, conserve :

Rapprocher chaque ligne du classeur de suivi des ventes d'une affaire de l'app.

LECTURE SEULE, DES DEUX COTES. Ne modifie ni le classeur, ni la base, ni Hektor.
Ecrit un seul fichier : notice/RAPPROCHEMENT_CLASSEUR_<date>.csv

POURQUOI. Sans ce rapprochement le projet est impossible : on ne peut ni completer
une ligne existante, ni eviter d'en creer une en double. La colonne `affair_uuid`
du classeur est VIDE sur les 4 760 lignes -- c'est la place prevue pour y poser,
un jour, le numero de chaine que ce programme calcule.

LA CASCADE, ET POURQUOI CHAQUE ETAGE EXISTE
  1  le mandat porte par une AFFAIRE, une seule chaine            ~60 %
  2  le mandat via le REGISTRE DES MANDATS -> le bien -> ses affaires
       ⚠ etage ajoute le 14/10 : chercher le numero dans app_affaire_ledger
         seulement ratait les biens dont le mandat a change.
  3  + le nom de l'ACQUEREUR          4  + le nom du VENDEUR
  5  + le PRIX                        6  + une DATE du cycle
  7  + le NEGOCIATEUR
  8  chaines JUMELLES : meme bien, numeros consecutifs, memes dates -- un COUPLE
       d'acquereurs fait deux chaines chez nous et une seule ligne au classeur.
  9  SANS LE MANDAT : acquereur + vendeur, sur les affaires recentes.
       ⚠ etage indispensable : quand l'affaire passe par un MANDAT DE RECHERCHE,
         le classeur porte le numero du mandat de recherche et nous celui du
         mandat de vente -- ils ne coincideront JAMAIS (etabli le 14/10 :
         7 lignes vivantes sur 10 retrouvees ainsi).

LE GARDE-FOU QUI A EVITE UN DOUBLON (14/10)
  Une ligne que la cascade ne reconnait pas n'est PAS une ligne a creer : on
  cherche encore par l'acquereur SEUL, et si une seule affaire recente repond,
  on s'ABSTIENT et on le signale. C'est ce test qui a montre que la chaine 29031
  -- qu'on s'appretait a creer -- existait deja au classeur, ligne 4737.

LES NOMS : on ne compare que les mots ECRITS EN MAJUSCULES, et jamais les prenoms
  courants. Mesure du 14/10 : comparer tous les mots de 4 lettres rapprochait
  « M. GERENTON Serge » et « Agnes DELOM | Serge CHEVALIER » sur le PRENOM.

    .venv\\Scripts\\python.exe phase2\\checks\\rapprocher_classeur_suivi.py
    .venv\\Scripts\\python.exe phase2\\checks\\rapprocher_classeur_suivi.py --vivantes
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, date
from pathlib import Path

import requests

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "monitoring"))
from check_google_scopes import load_env_file  # noqa: E402

SHEET_ID = "1wFd3pQYItvOrbk10W0r--bmhOaV1R4tWgZ3dq1XCipk"
ONGLET = "Sheet1"
BASE_LOCALE = RACINE / "phase2" / "phase2.sqlite"
VIVANT = ("Offre d'achat", "Compromis en attente", "Vente prévue", "Vente fixée")

#: Les prenoms et mots de forme qui ne designent personne. Sans cette liste, deux
#: familles differentes se rapprochent sur « Serge » ou « Marie ».
BRUIT = {
    "JEAN", "MARIE", "PIERRE", "MICHEL", "SERGE", "ANDRE", "LOUIS", "PAUL", "CLAUDE",
    "RENE", "BERNARD", "DANIEL", "ROBERT", "ALAIN", "PHILIPPE", "PATRICK", "CHRISTIAN",
    "JACQUES", "FRANCOIS", "LAURENT", "OLIVIER", "ERIC", "THIERRY", "PASCAL",
    "CATHERINE", "SYLVIE", "NATHALIE", "ISABELLE", "CHRISTINE", "MARTINE", "MONIQUE",
    "NICOLE", "ANNIE", "JEANNE", "ANNETTE", "AGNES", "CHANTAL", "GENEVIEVE",
    "VERONIQUE", "FRANCOISE", "MANON", "THEO", "NICOLAS", "MYRIAM", "ELISABETH",
    "SYLVAIN", "JULIEN", "MAXIME", "THOMAS", "ANTOINE", "VINCENT", "STEPHANE",
    "MADAME", "MONSIEUR", "MME", "MLLE", "IND", "INDIVISION", "CONSORTS", "SCI",
    "SARL", "SAS", "SASU", "EURL", "SNC", "SCP", "EARL", "STE", "SOCIETE", "NAN",
    "REPRESENTEE", "REPRESENTE", "PAR", "SON", "LEUR", "RUE", "AVENUE", "CHEMIN",
    "ROUTE", "PLACE", "LIEU", "ALLEE", "IMPASSE", "BOULEVARD",
}


# ⛔ Drapeau de la reparation « noms » : mots_propres() est appelee partout, y
#   compris au chargement du registre, donc le drapeau ne peut pas lui etre passe
#   en parametre sans toucher 12 appels. Il est pose par main() avant tout calcul.
MORCEAUX_DE_NOM = False


def mots_propres(texte: str, majuscules_seulement: bool = True) -> set[str]:
    """Les NOMS DE FAMILLE d'un texte -- pas les prenoms, pas les mots de forme."""
    brut = str(texte or "")
    trouves = re.findall(r"[A-Za-zÀ-ÿ'\-]{4,}", brut)
    if majuscules_seulement:
        trouves = [m for m in trouves if m.upper() == m]
    out = set()
    for m in trouves:
        n = unicodedata.normalize("NFD", m.upper())
        n = "".join(c for c in n if unicodedata.category(c) != "Mn")
        n = n.replace("'", "").replace("-", "")
        if len(n) >= 4 and n not in BRUIT:
            out.add(n)
        # ⭐ REPARATION « noms » (28/10) -- LE TRAIT D'UNION N'EST PAS LA MEME CHOSE
        #   DES DEUX COTES. Le classeur ecrit « DUMAS-PEYRACHON » d'un bloc ; notre
        #   blob porte deux acquereurs, « DUMAS » et « PEYRACHON ». Colles, ils ne se
        #   rencontrent jamais. On AJOUTE les morceaux a cote -- on n'enleve rien,
        #   donc aucun rapprochement existant ne peut se perdre.
        #   ⛔ On ne rapproche PAS deux orthographes (« PRHDHON » / « PRUDHON ») :
        #     ce serait du flou, et le flou a deja mordu trois fois.
        if MORCEAUX_DE_NOM:
            for bout in re.split(r"[-']", m):
                b = unicodedata.normalize("NFD", bout.upper())
                b = "".join(c for c in b if unicodedata.category(c) != "Mn")
                if len(b) >= 4 and b not in BRUIT:
                    out.add(b)
    return out


def nombre(v) -> float | None:
    try:
        return round(float(str(v).replace(" ", "").replace(" ", "")
                          .replace(" ", "").replace("€", "").replace(",", ".")))
    except (TypeError, ValueError):
        return None


def avancement_du_dossier(e) -> str:
    """OU EN EST un dossier chez nous : VENDU · COMPROMIS · OFFRE · ECHEC.

    ⭐ Idee de Frederic, 29/10 : « pourquoi on ne compare pas aussi l'avancement
      du dossier ? » -- et c'est un signal INDEPENDANT des quatre autres : il ne
      regarde ni le nom, ni le mandat, ni le prix, ni la date, mais LA FORME.
      Mesure du 29/10 : il concorde sur 4 509 des 4 666 liens (96,6 %).
    """
    g = {str(x or "").lower() for x in e["genres"]}
    etats = e.get("etats", set())
    if "vente" in g:
        return "VENDU"
    if "compromis" in g:
        return "ECHEC" if "cancelled" in etats else "COMPROMIS"
    if "offre" in g:
        return "ECHEC" if etats <= {"refused", "none", ""} else "OFFRE"
    return ""


def avancement_de_la_ligne(etat: str) -> str:
    """OU EN EST la ligne du classeur, dit par sa colonne « Etat Actuel »."""
    e = str(etat or "").strip().lower()
    if any(x in e for x in ("réglée", "reglee", "fixée", "fixee", "signé", "signe")):
        return "VENDU"
    if "annul" in e:
        return "ECHEC"
    if "prévue" in e or "prevue" in e or "compromis" in e:
        return "COMPROMIS"
    if "offre" in e:
        return "OFFRE"
    return ""


def _date_fr(v):
    """Une date DEJA au format du classeur (jj/mm/aaaa) -> un objet date.

    ⚠ NE PAS CONFONDRE AVEC `jour()`, juste en dessous : celle-la convertit NOS
      dates (aaaa-mm-jj) VERS le format du classeur. Les deux sens existent, et
      les melanger donne un signal MUET qui passe pour un signal VERT.
    """
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", str(v or "").strip())
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def jour(v) -> str:
    s = str(v or "").strip()[:10]
    if not s or s.startswith("0000"):
        return ""
    try:
        return datetime.strptime(s, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return ""


def noms_du_blob(blob) -> str:
    """acquereurs_json / mandants_json -> les noms, liste OU objet seul."""
    try:
        charge = json.loads(blob) if blob else None
    except (TypeError, ValueError):
        return ""
    gens = charge if isinstance(charge, list) else [charge] if isinstance(charge, dict) else []
    return " ".join(str(g.get("nom") or "").upper() for g in gens if isinstance(g, dict))


def dates_des_propositions(blob) -> set[str]:
    """Les dates du JOURNAL d'une offre -- propositions et acceptations.

    ⛔ POURQUOI, mesure du 12/11/2026. Pour une OFFRE, la colonne `date` porte le
       DERNIER MOUVEMENT, pas la proposition. Nos 1 185 refus du 11/11 ont donc
       deplace la date de 1 185 offres au 11/11/2026 -- Hektor y inscrit son
       dernier evenement. Exemple releve, l'offre 14112 :
           2021-03-25 22:59:59   proposition
           2021-03-25 23:00:00   accepte
           2026-11-11 19:16:36   refus        <- et c'est CA que porte `date`
       17 lignes du classeur, gelees le 29/10, etaient perdues pour cette seule
       raison : l'apparieur ne lisait que `date`.
    ⭐ LE CHAINAGE LE FAIT DEJA (affaire_ledger.py) : il ordonne une offre sur la
       date de sa PREMIERE PROPOSITION. On ne fait qu'aligner l'apparieur.
    ⚠ LE REFUS EST VOLONTAIREMENT EXCLU : il est deja porte par `date`, et
      l'ajouter n'apporterait aucune date neuve. On ne garde donc que les deux
      types qui correspondent a ce que le classeur appelle « Offre Achat ».
    """
    try:
        charge = json.loads(blob) if blob else None
    except (TypeError, ValueError):
        return set()
    if not isinstance(charge, list):
        charge = [charge] if isinstance(charge, dict) else []
    sorties = set()
    for e in charge:
        if not isinstance(e, dict):
            continue
        if str(e.get("type") or "").strip().lower() not in ("proposition", "accepte"):
            continue
        d = jour(e.get("date"))
        if d:
            sorties.add(d)
    return sorties


# ───────────────────────────────── le classeur
def lire_classeur() -> tuple[list[str], list[tuple[int, list]]]:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_file(
        os.environ["GOOGLE_WORKSPACE_SERVICE_ACCOUNT_FILE"],
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly",
                "https://www.googleapis.com/auth/spreadsheets"][1:],
    ).with_subject(os.environ["GOOGLE_WORKSPACE_SUBJECT_EMAIL"])
    creds.refresh(Request())
    rep = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{ONGLET}!A1:AL6000",
        headers={"Authorization": f"Bearer {creds.token}"}, timeout=180)
    rep.raise_for_status()
    valeurs = rep.json().get("values", [])
    if not valeurs:
        raise SystemExit("ARRET : le classeur est vide")
    lignes = [(r, l) for r, l in enumerate(valeurs[1:], start=2)
              if any(str(x).strip() for x in l)]
    return valeurs[0], lignes


# ───────────────────────────────── notre cote
def charger_affaires(con: sqlite3.Connection, rep: set[str]) -> dict:
    """Une entree par chaine : ses noms, ses montants, ses dates, son bien."""
    chaines: dict[int, dict] = {}
    for (ch, mandat, kind, acq, acq1, mand, montant, date, dossier,
         annonce, date_acte, state, propositions) in con.execute(
            "SELECT app_chaine_id, numero_mandat, kind, acquereurs_json, acquereur_json, "
            "       mandants_json, montant, date, app_dossier_id, hektor_annonce_id, "
            "       date_acte, state, propositions_json "
            "  FROM app_affaire_ledger WHERE app_chaine_id IS NOT NULL"):
        e = chaines.setdefault(ch, {
            "mandats": set(), "acq": set(), "mand": set(), "montants": set(),
            "dates": set(), "dossier": dossier, "annonce": str(annonce or ""),
            "genres": set(), "nego": set(), "derniere": "", "etats": set(),
        })
        # ⭐ l'ETAT de chaque transaction -- il sert a dire OU EN EST le dossier
        #   (reparation « avancement », 29/10, idee de Frederic)
        e["etats"].add(str(state or "").strip().lower())
        if mandat:
            e["mandats"].add(str(mandat).strip())
        e["acq"] |= mots_propres(noms_du_blob(acq) or noms_du_blob(acq1))
        e["mand"] |= mots_propres(noms_du_blob(mand))
        m = nombre(montant)
        if m:
            e["montants"].add(m)
            # ⛔ REPARATION « prix » : l'unite depend du GENRE. L'offre est en EUROS,
            #   le compromis et la vente en CENTIMES (mesure du 28/10 : mediane
            #   95 000 contre 9 700 000 et 9 900 000). On AJOUTE la valeur en euros
            #   a cote -- on n'enleve rien, donc on ne peut rien perdre.
            if ("prix" in rep and m >= 1000
                    and str(kind or "").lower() in ("compromis", "vente")):
                e["montants"].add(round(m / 100))
        if jour(date):
            e["dates"].add(jour(date))
        # ⛔ REPARATION « dates » : `date_acte` n'etait jamais lue. Pour un compromis
        #   c'est « Signature acte auth. PREVU le » chez Hektor, donc « Vente Prevue »
        #   au classeur. C'est la moitie de nos dates.
        if "dates" in rep and jour(date_acte):
            e["dates"].add(jour(date_acte))
        # ⛔ REPARATION « propositions » (12/11/2026) -- voir dates_des_propositions().
        #   Pour une OFFRE, `date` est celle du DERNIER mouvement : un refus la
        #   deplace. On AJOUTE les dates du journal a cote -- on n'enleve rien,
        #   donc on ne peut rien perdre, exactement comme la reparation « prix ».
        if "propositions" in rep and str(kind or "").lower() == "offre":
            e["dates"] |= dates_des_propositions(propositions)
        e["genres"].add(kind)
        d = str(date or "")[:10]
        if d > e["derniere"]:
            e["derniere"] = d
    for ch, nom in con.execute(
            "SELECT app_chaine_id, nom_au_moment FROM app_affaire_repartition "
            " WHERE nom_au_moment IS NOT NULL AND nom_au_moment <> ''"):
        if ch in chaines:
            chaines[ch]["nego"] |= mots_propres(nom, majuscules_seulement=False)
    return chaines


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Rapprocher le classeur et nos affaires")
    parser.add_argument("--vivantes", action="store_true",
                        help="n'examiner que les lignes en cours")
    parser.add_argument("--reparer", default="",
                        help="prix | dates | plafond | refdossier | tout -- virgule. "
                             "Sans ce drapeau le programme se comporte EXACTEMENT comme "
                             "l'original : c'est le temoin.")
    args = parser.parse_args()
    rep = {x.strip() for x in args.reparer.split(",") if x.strip()}
    if "tout" in rep:   # ⚠ « tout » AJOUTE, il n'ecrase pas les autres drapeaux
        # ⛔⛔ « refdossier » N'EST PAS DANS « tout », ET C'EST UNE DECISION DE
        #   FREDERIC, prise le 29/10 : « oublie la reference annonce, reviens sur
        #   ton gele » puis « la reference annonce UNIQUEMENT pour ecart, comme les
        #   autres champs ».
        #   ➡ Le numero de dossier est un CHAMP DU RAPPORT D'ECARTS, pas une preuve
        #     de rapprochement. Le code de l'etage reste, derriere son interrupteur,
        #     ETEINT : on ne l'allume qu'avec son accord.
        #   ⚠ Le gel a ete REMIS A SON ETAT D'ORIGINE le meme jour (0 etage
        #     « n° de dossier », 0 ecart avec la sauvegarde datee).
        rep |= {"prix", "dates", "plafond", "exclusivite", "recherche",
                "preuves", "noms", "veto", "ordre", "rattrapage",
                "avancement", "unicite", "propositions"}
        rep.discard("tout")
    print(f"reparations actives : {', '.join(sorted(rep)) if rep else 'AUCUNE (temoin)'}")
    global MORCEAUX_DE_NOM
    MORCEAUX_DE_NOM = "noms" in rep

    load_env_file(RACINE / ".env")
    entete, lignes = lire_classeur()
    index = {n: i for i, n in enumerate(entete)}
    case = lambda l, n: (str(l[index[n]]).strip()
                         if n in index and index[n] < len(l) else "")
    if args.vivantes:
        lignes = [(r, l) for r, l in lignes if case(l, "Etat Actuel") in VIVANT]
    print(f"classeur : {len(lignes)} ligne(s) a rapprocher")

    con = sqlite3.connect(f"file:{BASE_LOCALE}?mode=ro", uri=True, timeout=120)
    con.execute("PRAGMA busy_timeout=120000")
    chaines = charger_affaires(con, rep)
    # le REGISTRE DES MANDATS : un numero peut designer un bien sans affaire
    bien_du_mandat: dict[str, set] = defaultdict(set)
    for _num_mandat, dossier in con.execute(
            "SELECT numero_mandat, app_dossier_id FROM app_mandat "
            " WHERE numero_mandat IS NOT NULL AND numero_mandat <> ''"):
        if dossier:
            bien_du_mandat[str(_num_mandat).strip()].add(dossier)
    # ⭐⭐ REPARATION « recherche » -- UN MANDAT DE RECHERCHE N'A PAS DE BIEN.
    #   Il est porte par app_mandat.type (536 numeros, de 2014 a 2026), et son
    #   `mandants_texte` donne LE NOM DE L'ACQUEREUR qui cherche.
    #   ⛔ Ne pas confondre avec app_contact_mandat_recherche_current, qui n'en
    #     a que 32 : ce n'est PAS la bonne source (faute du 23/10).
    noms_recherche: dict = {}
    for _n, _mt in con.execute(
            "SELECT numero_mandat, mandants_texte FROM app_mandat "
            " WHERE numero_mandat IS NOT NULL AND numero_mandat <> '' "
            "   AND (lower(coalesce(type,'')) LIKE '%recherch%' "
            "     OR lower(coalesce(type_app,'')) LIKE '%recherch%')"):
        mots = mots_propres(_mt, majuscules_seulement=False)
        if mots:
            noms_recherche[str(_n).strip()] = mots

    # ⭐⭐ LE NUMERO DE DOSSIER (29/10) -- TROUVE PAR FREDERIC, ET OUBLIE DEPUIS
    #   LE DEBUT : « le numero de dossier aurait du servir aussi pour rapprocher
    #   certaines transactions, je crois que nous l'avons oublie ».
    #   ⛔ Il avait raison : `product_ref` n'etait lu par AUCUN des deux apparieurs.
    #   ⭐ Or c'est NOTRE numero de dossier (VM68712, VA3224, VT9194) -- et c'est un
    #     QUASI-IDENTIFIANT : 24 468 valeurs uniques sur 24 521 (49 partagees par
    #     deux mandats, 2 par trois). Mesure du 29/10.
    #   ⚠ IL NE RATTRAPE QU'UNE LIGNE AUJOURD'HUI (664 des 679 lignes qui le portent
    #     etaient deja rattachees par d'autres preuves) -- mais il CONFIRME 599 liens
    #     sans rien devoir aux huit autres signaux, et il servira a chaque ligne neuve.
    #   ⚠ ON LIT LE REGISTRE DES MANDATS, pas app_dossier_current : un bien vendu,
    #     clos ou archive n'est plus dans celui-la (regle du projet).
    #   ⛔⛔ ET LA JOINTURE SE FAIT PAR LE NUMERO D'ANNONCE, PAS PAR app_dossier_id.
    #     Defaut trouve le 29/10, quelques heures apres la pose : les deux tables
    #     portent une colonne `app_dossier_id` qui ne parle PAS de la meme chose --
    #        registre des mandats : -281472776635305, -281462364753394  (15 chiffres)
    #        registre des transactions : 284, 504, 1428                 (petits entiers)
    #     166 valeurs communes sur 24 491, contre 7 921 par hektor_annonce_id.
    #     ⛔ Le signal ne mordait donc que sur 0,7 % de ce qu'il pouvait.
    #     ⭐ MEME NOM, SERIES DIFFERENTES : c'est le piege deja paye deux fois sur ce
    #       projet (hektor_contact_id qui porte NOTRE numero ; 43 qui vaut deux
    #       personnes selon la serie). On croise sur la colonne qu'on a MESUREE.
    numeros_du_dossier: dict[str, set] = defaultdict(set)
    for _nd, _annonce in con.execute(
            "SELECT numero_dossier, hektor_annonce_id FROM app_mandat_register_current "
            " WHERE numero_dossier IS NOT NULL AND numero_dossier <> '' "
            "   AND hektor_annonce_id IS NOT NULL"):
        numeros_du_dossier[str(_annonce).strip()].add(str(_nd).strip().upper())
    con.close()
    print(f"numeros de dossier connus : {sum(len(v) for v in numeros_du_dossier.values())}")
    print(f"nos affaires : {len(chaines)} chaines")
    print(f"mandats de RECHERCHE connus : {len(noms_recherche)}")

    par_mandat: dict[str, set] = defaultdict(set)
    par_dossier: dict[int, set] = defaultdict(set)
    par_ref: dict[str, set] = defaultdict(set)
    for ch, e in chaines.items():
        for m in e["mandats"]:
            par_mandat[m].add(ch)
        if e["dossier"]:
            par_dossier[e["dossier"]].add(ch)
        # ⭐ le numero de dossier de la chaine, pose ICI et pas dans
        #   charger_affaires : il vient du REGISTRE DES MANDATS, pas du ledger,
        #   et il se croise par le NUMERO D'ANNONCE (voir la mesure ci-dessus).
        e["refs"] = set(numeros_du_dossier.get(str(e["annonce"]).strip(), set()))
        for r in e["refs"]:
            par_ref[r].add(ch)
    print(f"chaines portant un numero de dossier : "
          f"{sum(1 for e in chaines.values() if e['refs'])}")
    # ⛔ REPARATION « plafond » : l'etage 9 ne regardait que 2026, donc toute
    #   ligne plus ancienne etait hors d'atteinte -- d'ou 30 rattrapages seulement.
    seuil = "0000-00-00" if "plafond" in rep else "2026-01-01"
    recentes = {ch for ch, e in chaines.items() if e["derniere"] >= seuil}
    compte_lignes = Counter(case(l, "Mandat") for _, l in lignes if case(l, "Mandat"))

    # ⭐⭐⭐ REPARATION « unicite » (29/10) -- IDEE DE FREDERIC.
    #   « la ligne 3229 n'a qu'UNE preuve, le numero de mandat, mais cette preuve
    #     a beaucoup de valeur : seul risque un doublon, et cela se verifie. »
    #   ⭐ IL A RAISON, ET LA MESURE LE CONFIRME : une preuve vaut par sa RARETE,
    #     pas par sa nature. Combien de chaines porte chaque signal ?
    #        un numero de mandat   80,4 % n'en designent QU UNE SEULE
    #        un nom                61,1 %
    #        un montant            48,1 %
    #        une date               9,9 %   <- bon DEPARTAGEUR, mauvais IDENTIFIANT
    #   ➡ si un signal ne designe QU UNE affaire chez nous ET QU UNE ligne au
    #     classeur, aucun doublon n'est possible : la correspondance est FORCEE,
    #     meme seule. C'est deja la regle de l'etage 1 ; on l'etend aux autres.
    #   ⚠ CETTE REGLE NE DEPLACE AUCUN LIEN. Elle ne change que la CONFIANCE.
    chaines_par_mandat: dict[str, set] = {}
    chaines_par_nom: dict[str, set] = {}
    for _ch, _e in chaines.items():
        for _m in _e["mandats"]:
            chaines_par_mandat.setdefault(_m, set()).add(_ch)
        for _n in _e["acq"] | _e["mand"]:
            chaines_par_nom.setdefault(_n, set()).add(_ch)

    def signal_unique(l, ch) -> str:
        """Un signal qui ne peut designer QUE cette affaire, des DEUX cotes."""
        e = chaines.get(ch)
        if not e:
            return ""
        m = case(l, "Mandat")
        if (m and m in e["mandats"]
                and len(chaines_par_mandat.get(m, ())) == 1
                and compte_lignes.get(m, 0) == 1):
            return "mandat unique des deux côtés"
        noms = mots_propres(case(l, "Acquéreur"))
        if noms and (noms & e["acq"]):
            vus = set()
            for n in noms:
                vus |= chaines_par_nom.get(n, set())
            if len(vus) == 1:
                return "acquéreur unique dans tout le registre"
        return ""

    def reduire(cand: set, cible: set, champ: str) -> set:
        if not cible:
            return cand
        filtre = {c for c in cand if cible & chaines[c][champ]}
        return filtre or cand

    # ⭐⭐⭐ REPARATION « preuves » (28/10) -- L'ETIQUETTE DE L'ETAGE MENT.
    #   reduire() rend `filtre or cand` : si un signal ne trouve rien, on garde les
    #   candidats d'avant -- et la ligne reste etiquetee « mandat + acquereur » alors
    #   que l'acquereur n'a RIEN departage. Mesure du 28/10 : 59 % seulement des
    #   « mandat + acquereur + exclusivite » ont vraiment l'acquereur dans la chaine,
    #   contre 99 % sans exclusivite ; 39 lignes portent « acquereur » a tort.
    #   ⛔ Consequence : l'exclusivite servait les lignes dans un ordre fonde sur une
    #   etiquette fausse, et la chaine partait a la mauvaise ligne (12 faux liens).
    #   ➡ On COMPTE ce qui mord VRAIMENT entre une ligne et une chaine. Ce n'est pas
    #     un score pour CHOISIR un candidat (la cascade garde ce role) : c'est l'ordre
    #     de SERVICE de l'exclusivite -- qui reserve sa chaine en premier.
    def preuves(l, ch: int) -> int:
        e = chaines.get(ch)
        if not e:
            return 0
        n = 0
        if mots_propres(case(l, "Acquéreur")) & e["acq"]:
            n += 2                              # le signal le plus fort
        if mots_propres(case(l, "Vendeur")) & e["mand"]:
            n += 1
        prix = nombre(case(l, "Prix"))
        if prix and prix in e["montants"]:
            n += 1
        cols = ["Offre Achat", "Compromis", "Vente Fixée", "Vente Prévue"]
        if ({jour(case(l, c)) for c in cols} - {""}) & e["dates"]:
            n += 1
        if case(l, "Mandat") and case(l, "Mandat") in e["mandats"]:
            n += 1
        # ⭐⭐ LA 9e PREUVE (29/10) -- LE NUMERO DE DOSSIER.
        #   Elle ne doit RIEN aux huit autres : le numero de dossier n'entre dans
        #   aucun etage de la cascade et ne derive ni du mandat, ni des noms, ni
        #   des dates. Quand il concorde, c'est une confirmation INDEPENDANTE.
        #   ⚠ Elle vaut 1, comme le mandat -- pas 2 : le signal est rare (679
        #     lignes du classeur sur 4 773 le portent), donc il ne doit pas
        #     bousculer l'ordre de service des 4 094 lignes qui ne l'ont pas.
        ref = case(l, "product_ref").strip().upper()
        if ref and ref in e["refs"]:
            n += 1
        # ⭐ L'ETAT, enfin un signal (defaut ⑤, jamais traite jusqu'ici) : une ligne
        #   « Vente reglee / fixee / Signee » ne peut pas etre une chaine SANS vente,
        #   et une « Annulee » n'a aucune raison de rafler celle qui PORTE la vente.
        etat = case(l, "Etat Actuel").lower()
        a_vente = "vente" in {str(g or "").lower() for g in e["genres"]}
        finie = any(m in etat for m in ("vente réglée", "vente fixée", "signé"))
        if finie == a_vente:
            n += 1
        return n

    # ⭐⭐ REPARATION « exclusivite » -- le departage devient une FONCTION, pour
    #   pouvoir le REJOUER sur les seules chaines encore LIBRES.
    def resoudre(l, exclues: set):
            mandat = case(l, "Mandat")
            acq = mots_propres(case(l, "Acquéreur"))
            vend = mots_propres(case(l, "Vendeur"))
            nego = mots_propres(case(l, "Négociateur 1"), majuscules_seulement=False)
            prix = nombre(case(l, "Prix"))
            # ⭐⭐ NOTRE NUMERO DE DOSSIER, porte par la colonne `product_ref` du
            #   classeur (VM68712, VA3224...). ⛔ CE N'EST PAS un numero d'annonce :
            #   je l'ai compare a `hektor_annonce_id` le 29/10 et mes « 646 ecarts »
            #   etaient 646 CONCORDANCES. 442 valeurs de 7 caracteres, 135 de 6,
            #   100 de 5, et 33 seulement tout en chiffres (celles-la sont autre chose).
            ref = case(l, "product_ref").strip().upper()
            if ref.isdigit():
                ref = ""
            cols_date = ["Offre Achat", "Compromis", "Vente Fixée"]
            if "dates" in rep:          # ⛔ REPARATION « dates » : elle manquait
                cols_date.append("Vente Prévue")
            dates = {case(l, c) for c in cols_date} - {""}

            # ── ETAGE 0 : LE MANDAT DE RECHERCHE (repare le 28/10)
            #   Il n'a PAS de bien, et c'est NORMAL. Son nom confirme l'acquereur,
            #   et on cherche alors la chaine de CET acquereur, sans plafond d'annee.
            if "recherche" in rep and mandat in noms_recherche and acq:
                nom_m = noms_recherche[mandat]
                if acq & nom_m:            # le classeur et le mandat disent le MEME nom
                    c0 = {ch for ch, e0 in chaines.items()
                          if (acq & e0["acq"]) and ch not in exclues}
                    if len(c0) > 1:
                        c1 = {ch for ch in c0 if nom_m & chaines[ch]["acq"]}
                        c0 = c1 or c0
                    if len(c0) == 1:
                        return c0, "0 mandat de recherche + acquéreur", "sûre"

            # ── etages 1 et 2 : par le mandat, des DEUX chemins
            par_affaire = set(par_mandat.get(mandat, set())) - exclues
            par_bien = set()
            for d in bien_du_mandat.get(mandat, set()):
                par_bien |= par_dossier.get(d, set())
            par_bien -= exclues
            cand = (par_affaire & par_bien) or par_affaire or par_bien
            chemin = ("mandat" if par_affaire else ("mandat -> registre -> bien" if par_bien else ""))
            etage, confiance = ("1 mandat", "sûre") if cand else ("", "")

            if len(cand) == 1 and compte_lignes.get(mandat, 0) == 1:
                etage, confiance = "1 mandat seul", "sûre"
            elif cand:
                avant = len(cand)

                # ⭐⭐⭐ REPARATION « ordre » (29/10) -- LA DATE PASSE DEVANT.
                #   Mesure du 23/10, jamais appliquee jusqu'ici
                #   (notice/REGLE_APPARIEMENT_2026-10-23.md § 2) :
                #       vendeur (251) + ville (208) + prix (20)  =  479 / 737  (65 %)
                #       LA DATE, SEULE                           =  594 / 737  (81 %)
                #   « La date fait plus, a elle seule, que le vendeur + la ville +
                #     le prix REUNIS. Et elle doit venir AVANT eux. »
                #   ⛔ « Le prix d'annonce SORT de la regle : c'est le pire signal. »
                #   ⚠ POURQUOI C'EST SUR : un mandat recycle separe ses biens DANS LE
                #     TEMPS, et l'ecart est souvent d'une decennie. Le nom se repete,
                #     le prix se repete, la DATE non.
                def _par_date(c0):
                    if not dates:
                        return c0
                    f0 = {c for c in c0 if dates & chaines[c]["dates"]}
                    return f0 or c0

                def _par_avancement(c0):
                    # ⭐ REPARATION « avancement » (29/10, idee de Frederic).
                    #   Entre plusieurs candidats, celui dont LE STADE correspond.
                    #   Une ligne « Annulee » ne va pas sur une affaire VENDUE ;
                    #   une ligne « Vente reglee » ne va pas sur une offre seule.
                    #   ⚠ `or c0` : si AUCUN candidat n'est au bon stade, on ne perd
                    #     personne -- c'est alors un ECART a signaler, pas un tri.
                    a0 = avancement_de_la_ligne(case(l, "Etat Actuel"))
                    if not a0:
                        return c0
                    f0 = {c for c in c0 if avancement_du_dossier(chaines[c]) == a0}
                    return f0 or c0

                def _par_prix(c0):
                    if not prix:
                        return c0
                    f0 = {c for c in c0 if prix in chaines[c]["montants"]}
                    return f0 or c0

                def _par_ref(c0):
                    # ⭐⭐ LE NUMERO DE DOSSIER EN TETE DU DEPARTAGE (29/10).
                    #   Il est QUASI-UNIQUE (24 468 sur 24 521) : quand il mord, il
                    #   designe le bien et plus rien d'autre. Il passe donc AVANT
                    #   l'acquereur et la date -- mais seulement quand il existe
                    #   (679 lignes sur 4 773 le portent).
                    #   ⚠ `or c0` comme partout : un signal qui ne trouve rien ne
                    #     doit JAMAIS vider les candidats.
                    if not ref:
                        return c0
                    f0 = {c for c in c0 if ref in chaines[c]["refs"]}
                    return f0 or c0

                if "ordre" in rep:
                    etapes = ([("1b mandat + n° de dossier", _par_ref, "sûre")]
                              if "refdossier" in rep else []) + [
                              ("2 mandat + acquéreur", lambda c0: reduire(c0, acq, "acq"), "sûre"),
                              ("3 mandat + date", _par_date, "sûre"),
                              ("4 mandat + avancement", _par_avancement, "sûre")
                              if "avancement" in rep else
                              ("4 mandat + vendeur", lambda c0: reduire(c0, vend, "mand"), "sûre"),
                              ("5 mandat + vendeur", lambda c0: reduire(c0, vend, "mand"), "sûre")
                              if "avancement" in rep else
                              ("5 mandat + prix", _par_prix, "bonne"),
                              ("6 mandat + prix", _par_prix, "bonne")
                              if "avancement" in rep else
                              ("6 mandat + négociateur", lambda c0: reduire(c0, nego, "nego"), "bonne"),
                              ("7 mandat + négociateur", lambda c0: reduire(c0, nego, "nego"), "bonne")]
                else:
                    etapes = [("2 mandat + acquéreur", lambda c0: reduire(c0, acq, "acq"), "sûre"),
                              ("3 mandat + vendeur", lambda c0: reduire(c0, vend, "mand"), "sûre"),
                              ("4 mandat + prix", _par_prix, "bonne"),
                              ("5 mandat + date", _par_date, "bonne"),
                              ("6 mandat + négociateur", lambda c0: reduire(c0, nego, "nego"), "bonne")]
                for nom_etape, filtre, conf in etapes:
                    cand = filtre(cand)
                    if len(cand) == 1:
                        etage, confiance = nom_etape, conf
                        break
                if len(cand) != 1:
                    tri = sorted(cand)
                    jumelles = (len(tri) > 1
                                and len({chaines[c]["dossier"] for c in tri}) == 1
                                and all(b - a == 1 for a, b in zip(tri, tri[1:]))
                                and len({tuple(sorted(chaines[c]["dates"]))
                                         for c in tri}) == 1)
                    if jumelles:
                        cand, etage, confiance = {tri[0]}, "7 chaînes jumelles", "bonne"
                    else:
                        etage, confiance = f"ambiguë ({avant} chaînes)", "aucune"

            # ── ⭐⭐ ETAGE 8bis : SANS LE MANDAT, PAR NOTRE NUMERO DE DOSSIER (29/10)
            #   Trouve par Frederic : « le numero de dossier aurait du servir aussi
            #   pour rapprocher certaines transactions, je crois qu'on l'a oublie ».
            #   Il vient AVANT l'etage 9 (acquereur + vendeur) parce qu'il est
            #   QUASI-UNIQUE : 24 468 numeros pour 24 521 biens. Quand il designe
            #   une seule chaine, il n'y a rien a departager.
            #   ⚠ IL NE S'APPLIQUE PAS SI LE MANDAT A DEJA TRANCHE : on ne refait
            #     pas un choix sur, on comble un trou.
            #   ⚠ Et il reste « a valider » : le numero designe LE BIEN, pas la
            #     transaction -- un bien peut porter plusieurs affaires.
            if "refdossier" in rep and len(cand) != 1 and ref:
                parref = set(par_ref.get(ref, set())) - exclues
                if len(parref) > 1 and acq:
                    p2 = {c for c in parref if acq & chaines[c]["acq"]}
                    parref = p2 or parref
                if len(parref) > 1:
                    a0 = avancement_de_la_ligne(case(l, "Etat Actuel"))
                    if a0:
                        p3 = {c for c in parref if avancement_du_dossier(chaines[c]) == a0}
                        parref = p3 or parref
                if len(parref) == 1:
                    cand, etage, confiance = parref, "8b n° de dossier", "à valider"

            # ── etage 9 : SANS le mandat (cas du mandat de recherche)
            if len(cand) != 1 and acq:
                sans = {c for c in recentes if acq & chaines[c]["acq"]} - exclues
                if vend:
                    sans2 = {c for c in sans if vend & chaines[c]["mand"]}
                    sans = sans2 or sans
                if len(sans) > 1 and "avancement" in rep:
                    a0 = avancement_de_la_ligne(case(l, "Etat Actuel"))
                    if a0:
                        sansA = {c for c in sans if avancement_du_dossier(chaines[c]) == a0}
                        sans = sansA or sans
                if len(sans) > 1 and nego:
                    sans3 = {c for c in sans if nego & chaines[c]["nego"]}
                    sans = sans3 or sans
                if len(sans) == 1:
                    cand, etage, confiance = sans, "9 sans mandat (acquéreur + vendeur)", "à valider"
                elif sans and not cand:
                    # ⭐⭐⭐ REPARATION « rattrapage » (29/10) -- LE CRAN QUI MANQUAIT.
                    #   Mesure du 23/10, jamais appliquee
                    #   (notice/AUDIT_VENTES_REGLEES_ABSENTES_2026-10-23.md) :
                    #     83 ventes reglees du classeur semblaient ABSENTES.
                    #     Cherchees par l'ACQUEREUR : 63 sur 83 (76 %) sont BIEN chez
                    #     nous -- seul le NUMERO DE MANDAT differe.
                    #        L195 classeur 17381 -> nous 17396  BARRUEL  65 000 = 65 000
                    #        L301 classeur 16503 -> nous 17148  BERTHAUT 42 000 = 42 000
                    #   ➡ « la cascade doit avoir un dernier cran : si le MANDAT ne
                    #     trouve rien, chercher par l'ACQUEREUR + (le MONTANT ou la DATE) »
                    #   ⭐ Et le panel du 29/10 l'a reconfirme : L504, L1915, L1335 et
                    #     L965 ont un mandat DIFFERENT et un lien pourtant JUSTE.
                    #
                    # ⚠ ON EXIGE LES DEUX : l'acquereur (deja filtre dans `sans`) ET
                    #   une PREUVE CHIFFREE -- le montant exact, ou une date exacte.
                    #   Sans cette preuve on ne tranche pas : le nom seul se repete.
                    if "rattrapage" in rep:
                        par_date = {c for c in sans if dates & chaines[c]["dates"]}
                        par_prix = ({c for c in sans if prix in chaines[c]["montants"]}
                                    if prix else set())
                        # la DATE d'abord (elle tranche mieux : mesure du 23/10),
                        # et le prix seulement si la date n'a pas suffi.
                        for retenu, quoi in ((par_date & par_prix, "date + montant"),
                                             (par_date, "date"),
                                             (par_prix, "montant")):
                            if len(retenu) == 1:
                                cand = retenu
                                etage = f"10 acquéreur + {quoi} (mandat différent)"
                                confiance = "bonne" if quoi != "montant" else "à valider"
                                break
                    if len(cand) != 1:
                        etage, confiance = f"à trancher ({len(sans)} pistes)", "aucune"

            return cand, etage, confiance

    # ── PASSE 1 : chacun pour soi, exactement comme avant
    brut = []
    for rang, l in lignes:
        cand, etage, confiance = resoudre(l, set())
        brut.append([rang, l, cand, etage, confiance])

    # ── PASSE 2 : L'EXCLUSIVITE. On sert les lignes par ORDRE DE SURETE (l'etage),
    #   et une chaine prise n'est plus candidate. Celle qui arrive apres rejoue son
    #   departage sur les chaines LIBRES ; si elle n'en trouve plus une seule, elle
    #   s'ABSTIENT, et on DIT par qui sa chaine etait prise.
    if "exclusivite" in rep:
        def rang_etage(e):
            return int(e[0]) if e[:1].isdigit() else 99
        def cle_ordre(i):
            # ⛔ SANS « preuves » : l'ancien ordre, l'etage seul (on garde le temoin).
            if "preuves" not in rep:
                return (0, 0, rang_etage(brut[i][3]), brut[i][0])
            cand = brut[i][2]
            if len(cand) != 1:
                return (9, 0, rang_etage(brut[i][3]), brut[i][0])
            ch0 = next(iter(cand))
            # ⭐⭐⭐ « SANS PRIVILEGIER LES ANNULEES » -- Frederic, 29/10.
            #   UNE AFFAIRE QUI A ABOUTI PASSE AVANT UNE AFFAIRE MORTE, toujours.
            #   Logique : une chaine qui PORTE UNE VENTE appartient a la ligne qui
            #   dit « vendu », pas a celle qui dit « annulee ». L'inverse laissait
            #   une annulee tenir la vente pendant que la vraie vente s'abstenait
            #   (mesure du 29/10 : L4121 « Annulee » tenait la chaine 7850 et
            #   L1760 « Vente reglee » restait sans rien, sur le MEME mandat 3813).
            #   ⚠ Ce n'est PAS « l'aboutie gagne toujours » : c'est l'aboutie qui
            #     SERT D'ABORD. Si sa chaine ne lui va pas, l'autre la reprend.
            e0 = chaines.get(ch0)
            a_vente = bool(e0) and "vente" in {str(g or "").lower() for g in e0["genres"]}
            etat0 = case(brut[i][1], "Etat Actuel").strip().lower()
            morte = etat0 == "annulée"
            priorite = 1 if (morte and a_vente) else 0      # 0 = sert en premier
            # ⭐ AVEC : la ligne qui a LE PLUS DE PREUVES sur sa chaine sert d'abord.
            #   Le signe moins met le mieux prouve en tete.
            n = preuves(brut[i][1], ch0)
            return (priorite, -n, rang_etage(brut[i][3]), brut[i][0])

        ordre = sorted(range(len(brut)), key=cle_ordre)
        prises: dict = {}
        rejoues = volees = 0
        for i in ordre:
            cand = brut[i][2]
            if len(cand) != 1:
                continue
            ch = next(iter(cand))
            if ch not in prises:
                prises[ch] = brut[i][0]
                continue
            rejoues += 1
            c2, e2, f2 = resoudre(brut[i][1], set(prises))
            if len(c2) == 1:
                brut[i][2:5] = [c2, e2 + " + exclusivité", f2]
                prises[next(iter(c2))] = brut[i][0]
            else:
                volees += 1
                brut[i][2:5] = [set(), f"chaîne {ch} déjà prise par L{prises[ch]}", "aucune"]
        print(f"exclusivité : {rejoues} ligne(s) rejouée(s), dont {volees} abstention(s)")

    # ⭐⭐⭐ REPARATION « veto » (29/10) -- LE DERNIER MOT DE L'ACQUEREUR.
    #   Mesure du 28/10 : 8 liens cumulent TROIS contradictions a la fois --
    #   une ligne « Annulee » posee sur une chaine qui porte une VENTE, avec
    #   l'acquereur ET le vendeur qui disent autre chose. Examines un par un le
    #   29/10 : AUCUN des 8 n'a d'affaire chez nous. Trois visaient une chaine
    #   deja prise, LEGITIMEMENT, par une ligne dont l'acquereur colle aussi
    #   (L380, L3785, L2193) ; les cinq autres n'ont aucune chaine a leur nom.
    #   ➡ Les rattacher ailleurs serait faux : il faut les DETACHER.
    #
    # ⛔ POURQUOI PAS UN VETO SIMPLE SUR L'ACQUEREUR. 188 liens ont l'acquereur
    #   qui se contredit, et le taux est LE MEME chez les liens les plus surs
    #   (mesure du 28/10 : 27,5 % contre 21,5 %). Beaucoup sont des orthographes
    #   (« PRHDHON » / « PRUDHON »). Un veto strict casserait des liens justes.
    #   ➡ On n'ecarte que le CUMUL : l'acquereur SE CONTREDIT, et au moins deux
    #     autres signaux disent la meme chose.
    if "veto" in rep:
        ecartes = 0
        for i, (rang, l, cand, etage, confiance) in enumerate(brut):
            if len(cand) != 1:
                continue
            ch = next(iter(cand))
            e = chaines.get(ch)
            if not e:
                continue
            contre = 0
            acq = mots_propres(case(l, "Acquéreur"))
            if acq and e["acq"] and not (acq & e["acq"]):
                contre += 1                   # l'acquereur se contredit
            # ⭐⭐ LE SIGNAL LE PLUS NET : L'ECART DE DATE (29/10).
            #   Mesure : 4 446 liens sur 4 669 ont moins d'UN MOIS d'ecart entre
            #   le classeur et la chaine. 13 seulement depassent DEUX ANS -- et
            #   une affaire du classeur datee 2024 ne peut pas etre une vente de
            #   2016. C'est le meme ACHETEUR revenu, pas la meme affaire.
            #   ⛔ CE SIGNAL ETAIT MORT DANS MON AUDIT DU 28/10 : j'appliquais
            #     `jour()` aux dates DU CLASSEUR, alors qu'elle convertit NOS
            #     dates VERS leur format. Elle rendait "" a chaque fois, et le
            #     signal annoncait « 0 » -- un zero de mesure, pas un vrai zero.
            dcl = [_date_fr(case(l, c)) for c in
                   ("Offre Achat", "Compromis", "Vente Prévue", "Vente Fixée")]
            dcl = [x for x in dcl if x]
            dno = [x for x in (_date_fr(y) for y in e["dates"]) if x]
            if dcl and dno:
                jours = min(abs((a0 - b0).days) for a0 in dcl for b0 in dno)
                if jours > 730:
                    contre += 2               # plus de deux ans : ce n'est pas elle
            vend = mots_propres(case(l, "Vendeur"))
            if vend and e["mand"] and not (vend & e["mand"]):
                contre += 1
            etat = case(l, "Etat Actuel").strip().lower()
            a_vente = "vente" in {str(g or "").lower() for g in e["genres"]}
            if etat == "annulée" and a_vente:
                contre += 1
            if any(x in etat for x in ("vente réglée", "vente fixée")) and not a_vente:
                contre += 1
            mandat_l = case(l, "Mandat")
            if mandat_l and e["mandats"] and mandat_l not in e["mandats"]:
                contre += 1
            if contre >= 3:
                ecartes += 1
                brut[i][2:5] = [set(),
                                f"ecartee : {contre} signaux se contredisent (acquéreur, "
                                f"et son affaire n'est pas chez nous)", "aucune"]
        print(f"veto : {ecartes} lien(s) ecarte(s) -- l'acquereur et 2 autres signaux "
              f"se contredisent")

    resultats, bilan, unicites = [], Counter(), 0
    for rang, l, cand, etage, confiance in brut:
        # ⛔ BUG DU REFACTOR, trouve par Frederic le 28/10 : `mandat` etait calcule
        #   dans resoudre(), donc hors de portee ici -- Python prenait la variable
        #   de la boucle de chargement du registre, restee a sa DERNIERE valeur
        #   (18975 sur les 4 773 lignes). On le recalcule.
        mandat = case(l, "Mandat")
        chaine = next(iter(cand)) if len(cand) == 1 else None
        if not chaine:
            etage = etage or "aucune correspondance"
            confiance = confiance or "aucune"
        if ("unicite" in rep and chaine and confiance not in ("sûre", "aucune")):
            u = signal_unique(l, chaine)
            if u:
                confiance = "sûre"
                etage = f"{etage} · {u}"
                unicites += 1
        bilan[confiance] += 1
        e = chaines.get(chaine) if chaine else None
        resultats.append({
            "ligne du classeur": rang,
            # ⭐⭐ « ID Unique » ET le compte de preuves, ajoutes le 29/10 pour que
            #   le REGEL puisse se faire depuis ce fichier, sans rejouer la cascade.
            #   ⛔ « ID Unique » est LA CLE : le rang se decale des qu'on insere une
            #     ligne, et les 12 404 liens deviendraient faux EN SILENCE
            #     (lecon du 22/10, re-apprise le 29/10).
            "ID Unique": case(l, "ID Unique"),
            "preuves": preuves(l, chaine) if chaine else 0,
            "vivante": "OUI" if case(l, "Etat Actuel") in VIVANT else "",
            "Etat Actuel": case(l, "Etat Actuel"),
            "Mandat (classeur)": mandat,
            "Agence": case(l, "Agence"),
            "Négociateur 1": case(l, "Négociateur 1"),
            "Acquéreur": case(l, "Acquéreur")[:60],
            "Vendeur": case(l, "Vendeur")[:60],
            "Prix": case(l, "Prix"),
            "chaîne trouvée": chaine or "",
            "confiance": confiance,
            "par quelle clé": etage,
            "mandat chez nous": " ".join(sorted(e["mandats"])) if e else "",
            "genres chez nous": " ".join(sorted(e["genres"])) if e else "",
            "annonce": e["annonce"] if e else "",
            "mandat different ?": ("OUI" if e and mandat and e["mandats"]
                                   and mandat not in e["mandats"] else ""),
        })

    marque = ("_" + "-".join(sorted(rep))) if rep else "_temoin"
    sortie = (RACINE / "notice"
              / f"APPARIEMENT_CLASSEUR_{datetime.now():%Y-%m-%d}{marque}.csv")
    with sortie.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(resultats[0]), delimiter=";")
        w.writeheader()
        w.writerows(resultats)

    trouvees = sum(1 for r in resultats if r["chaîne trouvée"])
    print()
    print(f"{'confiance':<14}{'lignes':>8}")
    for k in ("sûre", "bonne", "à valider", "aucune"):
        if bilan.get(k):
            print(f"   {k:<11}{bilan[k]:>8}")
    print(f"\n   => RECONNUES : {trouvees} / {len(lignes)} ({100*trouvees//max(1,len(lignes))} %)")
    viv = [r for r in resultats if r["vivante"] == "OUI"]
    if viv:
        vt = sum(1 for r in viv if r["chaîne trouvée"])
        print(f"   => VIVANTES  : {vt} / {len(viv)} ({100*vt//len(viv)} %)")
    diff = sum(1 for r in resultats if r["mandat different ?"] == "OUI")
    print(f"   => dont le numero de mandat DIFFERE du notre : {diff}")
    print()
    print("par clé :")
    for k, n in Counter(r["par quelle clé"] for r in resultats).most_common(12):
        print(f"   {n:>6}  {k}")
    print()
    print(f"ecrit : {sortie}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
