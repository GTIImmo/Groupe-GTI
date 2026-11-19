# /!\ ARCHIVE LE 19/11/2026 -- NE PLUS LANCER.
# Decision de Frederic : « archive-le. Il n'a plus d'utilite. »
# Il tenait pour SIENNE toute ligne du Sheet qui porte un affair_uuid et la faisait
# avancer : le jour ou nos etiquettes de dossier arrivent en colonne A (chantier
# classeur, etape 5.2), il aurait pris les lignes humaines pour les siennes.
# Garde ici pour l'histoire et pour ses trois regles, pas pour servir. Il REFUSE de
# tourner (code 3) avant le moindre import et la moindre lecture du Sheet.
# Voir scheduled/_archive/LISEZMOI.md.
"""Alimenter l'AppSheet « Offres en cours et compromis » depuis notre registre.

Analyse : notice/ANALYSE_APPSHEET_SUIVI_TRANSACTIONS_2026-10-13.md

PERIMETRE ARRETE PAR FREDERIC (13/10/2026)
  - uniquement les lignes NOUVELLES ; l'historique n'est pas reconstitue ;
  - option A : une ligne creee par nous est ensuite FAITE AVANCER par nous
    (compromis, vente, notaire, etat) ;
  - une ligne saisie a la main n'est JAMAIS touchee.

LES TROIS REGLES, tirees d'une mesure (0 ligne sur 4 764 etait d'accord avec nous)
  1. on remplit un vide, on ne corrige JAMAIS un plein ;
  2. un etat ne RECULE jamais ;
  3. devant un doute, on s'abstient ET on le dit (chantier 4 : aucun echec silencieux).

LA MEMOIRE DU LIEN EST DANS LA FEUILLE, PAS CHEZ NOUS : la colonne `affair_uuid`
porte notre numero de chaine. Une ligne qui en porte un est a nous ; une ligne sans
numero est a l'humain. Pas de table miroir a tenir synchrone -- « deux copies d'une
verite divergent tot ou tard ».

    .venv\\Scripts\\python.exe scheduled\\push_suivi_appsheet.py              (a blanc)
    .venv\\Scripts\\python.exe scheduled\\push_suivi_appsheet.py --envoyer    (ecrit)
    .venv\\Scripts\\python.exe scheduled\\push_suivi_appsheet.py --envoyer --chaine 30725
                                                                   (une seule ligne)

/!\\ Le python du venv : google-auth et requests n'existent pas dans celui du systeme.
"""

from __future__ import annotations

# --- ARCHIVE LE 19/11/2026 : refus de tourner, avant tout import et toute lecture ---
import sys as _sys_archive

_sys_archive.stderr.write(
    "push_suivi_appsheet.py est ARCHIVE depuis le 19/11/2026 (decision de Frederic) : "
    "il ne tourne plus. Voir scheduled/_archive/LISEZMOI.md.\n"
)
raise SystemExit(3)

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "monitoring"))
from check_google_scopes import load_env_file  # noqa: E402

SHEET_ID = "1wFd3pQYItvOrbk10W0r--bmhOaV1R4tWgZ3dq1XCipk"
ONGLET = "Sheet1"
PLAGE = f"{ONGLET}!A1:AL6000"
# La colonne qui NOMME une ligne. Un numero de rang est une PLACE, et une place bouge
# des qu'un humain insere, supprime ou trie. « ID Unique » est la seule identite stable.
COLONNE_CLE = "ID Unique"
API_APPSHEET = "https://api.appsheet.com/api/v2"

# ─── Correspondances APPRISES en croisant 143 lignes de la feuille (13/10/2026) ───
# Elles ne sont pas inventees : chaque ligne a ete mesuree. Voir l'analyse.
TYPE_BIEN = {
    "1": "Maison", "25": "Maison", "30": "Maison", "39": "Maison", "17": "Maison", "22": "Maison",
    "2": "Appartement",
    "5": "Terrain", "43": "Terrain",
    "21": "Immeuble",
    "15": "Garage", "16": "Garage",
    "23": "Local Commercial",   # « Commerce » chez Hektor -- A CONFIRMER, non croise
}
AGENCES = {
    "Groupe GTI Saint-Etienne": "ST ETIENNE",
    "Groupe GTI Montbrison": "MONTBRISON",
    "Groupe GTI COURPIERE": "COURPIERE",
    "Groupe Gti Le Puy en Velay": "LE PUY",
    "Groupe GTI ANNONAY": "ANNONAY",
    "Groupe GTI Firminy": "FIRMINY",
    "Groupe GTI Tence": "TENCE",
    "Groupe GTI Craponne-sur-Arzon": "CRAPONNE",
    "Groupe GTI Saint-Bonnet-le-Château": "ST BONNET",
    "Groupe GTI Ambert": "AMBERT",
    "Groupe GTI Issoire": "ISSOIRE",
    "Groupe GTI Saint-Just-Saint-Rambert": "ST RAMBERT",
    "Groupe GTI Monistrol sur Loire": "MONISTROL",
    "Groupe GTI Dunières": "DUNIERES",
    "Groupe GTI BRIOUDE": "BRIOUDE",
    "Groupe GTI Yssingeaux": "YSSINGEAUX",
    "Groupe GTI Saint-Didier-en-Velay": "ST DIDIER",
}
# La regle du negociateur est le NOM DE FAMILLE en majuscules (29 cas sur 29).
# Seules les homonymies font exception.
NEGO_EXCEPTIONS = {"M. Arnaud VALLA": "VALLA A"}
NEGO_PARTICULES = {"DE", "DU", "LE", "LA", "DES", "VAN", "MC"}
CIVILITES = {"M.", "MME", "MME.", "M", "MLLE", "MLLE.", "MR", "MR."}

# L'echelle des etats : un etat ne recule jamais. ORDRE EXACT de la liste de reference
# (onglet « Agence », colonne D, lue le 13/10/2026) : elle en porte HUIT. « Compromis
# signe » et « Vente signee » n'apparaissent jamais dans Sheet1 -- la signature y est
# portee par les cases a cocher Signe / Signee -- mais ils existent dans la liste et dans
# l'onglet Reporting : un etat ecrit a la main ne doit pas nous faire reculer.
ETATS_RANG = {
    "": 0, "Offre d'achat": 1, "Compromis en attente": 2, "Compromis signé": 3,
    "Vente prévue": 4, "Vente fixée": 5, "Vente signée": 6, "Vente réglée": 7,
    "Annulée": 9,
}
# Les colonnes que nous ecrivons. Les autres appartiennent a l'humain et ne sont
# jamais citees dans une charge envoyee.
NOS_COLONNES = [
    "affair_uuid", "product_ref", "Mandat", "Nature", "Lien CRM", "Agence",
    "Négociateur 1", "Pourcentage 1", "Négociateur 2", "Pourcentage 2",
    "Notaire", "Charge Commission", "Etat Actuel", "Offre Achat", "Compromis",
    "Signé", "Vente Prévue", "Vente Fixée", "Signée", "Annulée", "Acquéreur", "Vendeur",
    "Prix", "Ville",
]
# Celles qu'on ne pose QU'A LA CREATION : ensuite, l'humain peut les avoir corrigees.
CREATION_SEULEMENT = {"Acquéreur", "Vendeur", "Prix", "Ville", "Notaire",
                      "Négociateur 1", "Pourcentage 1", "Négociateur 2", "Pourcentage 2",
                      "Charge Commission", "Nature", "Agence", "Offre Achat"}


# ───────────────────────────── outils de forme ─────────────────────────────

def jj(valeur) -> str:
    """Une date de Hektor -> JJ/MM/AAAA. Rend '' si elle est absente ou nulle."""
    brut = str(valeur or "").strip()[:10]
    if not brut or brut.startswith("0000"):
        return ""
    try:
        return datetime.strptime(brut, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return ""


def passee(valeur) -> bool:
    brut = str(valeur or "").strip()[:10]
    return bool(brut) and not brut.startswith("0000") and brut <= datetime.now().strftime("%Y-%m-%d")


def entier(valeur) -> str:
    """Un montant -> entier sans decimale (la feuille porte 110000, pas 110000.00)."""
    try:
        return str(int(round(float(str(valeur).replace(" ", "").replace(",", ".")))))
    except (TypeError, ValueError):
        return ""


def nom_negociateur(complet: str) -> str:
    """« Mme. Cécile MOUREY-LIBOZ » -> « MOUREY-LIBOZ ».

    LA REGLE, APPRISE SUR LES 29 CORRESPONDANCES CROISEES LE 13/10/2026 : la feuille
    garde le PREMIER mot entierement en majuscules, pas le dernier et pas la suite
    complete. C'est ce qui distingue « Marion BILLIG DURAND » -> « BILLIG » (et non
    « BILLIG DURAND », ce que faisait la premiere version, prise en defaut par le
    passage a blanc). Une seule homonymie force l'initiale : VALLA.
    """
    complet = str(complet or "").strip()
    if not complet:
        return ""
    if complet in NEGO_EXCEPTIONS:
        return NEGO_EXCEPTIONS[complet]
    mots = [m for m in complet.split()
            if m.upper().rstrip(".") not in {c.rstrip(".") for c in CIVILITES}]
    for mot in mots:
        noyau = mot.replace("-", "").replace("'", "")
        if noyau.isalpha() and mot.upper() == mot and mot.upper() not in NEGO_PARTICULES:
            return mot.upper()
    return mots[-1].upper() if mots else ""


def partie(blob: str | None) -> str:
    """acquereurs_json / mandants_json -> « M. NOM Prénom », TOUS les intervenants.

    ⚠ Le deballeur accepte une LISTE comme un OBJET SEUL : Hektor rend les deux.
    """
    if not blob:
        return ""
    try:
        charge = json.loads(blob)
    except (TypeError, ValueError):
        return ""
    gens = charge if isinstance(charge, list) else [charge]
    noms = []
    for personne in gens:
        if not isinstance(personne, dict):
            continue
        civilite = str(personne.get("civilite") or "").strip()
        nom = str(personne.get("nom") or "").strip()
        prenom = str(personne.get("prenom") or "").strip()
        morceaux = [x for x in (civilite, nom.upper() if nom else "", prenom) if x]
        if morceaux:
            noms.append(" ".join(morceaux))
    return " ".join(noms)


# ───────────────────────────── la feuille, en lecture ─────────────────────────────

def jeton_sheets() -> str:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    fichier = os.environ.get("GOOGLE_WORKSPACE_SERVICE_ACCOUNT_FILE", "").strip()
    sujet = os.environ.get("GOOGLE_WORKSPACE_SUBJECT_EMAIL", "").strip()
    if not fichier or not sujet:
        raise SystemExit("ARRET : cle de service ou compte emprunte absent du .env")
    creds = service_account.Credentials.from_service_account_file(
        fichier, scopes=["https://www.googleapis.com/auth/spreadsheets"]).with_subject(sujet)
    creds.refresh(Request())
    return creds.token


def lire_feuille() -> tuple[list[str], list[list[str]]]:
    jeton = jeton_sheets()
    reponse = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{PLAGE}",
        headers={"Authorization": f"Bearer {jeton}"}, timeout=90)
    if reponse.status_code != 200:
        raise SystemExit(f"ARRET : lecture de la feuille impossible ({reponse.status_code}) "
                         f"{reponse.text[:300]}")
    valeurs = reponse.json().get("values", [])
    if not valeurs:
        raise SystemExit("ARRET : la feuille est vide -- on n'ecrit pas dans le doute")
    return valeurs[0], valeurs[1:]


# ───────────────────────────── le registre, en lecture ─────────────────────────────

def chaines_a_examiner(con: sqlite3.Connection, depuis: str, une_seule: str | None,
                       deja_a_nous: set[str]) -> list[int]:
    """Les chaines a examiner : les NOUVELLES, plus celles qui ont DEJA une ligne a nous.

    Nouvelles : reperees par `first_seen_at`, ⚠ ET SURTOUT PAS PAR `date` -- mesure du
    13/10/2026 : 54 offres portaient toutes `2026-10-13T04:29:08Z`, la MEME seconde,
    sans montant ni etat, alors que nous les connaissions depuis le 31/07. Hektor
    re-tamponne cette date ; filtrer dessus aurait fabrique 54 lignes vides par jour.

    Deja a nous : sans elles, l'option A (« la ligne creee avance ensuite ») ne verrait
    jamais un compromis, une signature ou une annulation survenus APRES la creation --
    leur `first_seen_at` ne bouge pas. C'etait le defaut de la premiere version.
    """
    if une_seule:
        return [int(une_seule)]
    nouvelles = [r[0] for r in con.execute(
        "SELECT app_chaine_id FROM app_affaire_ledger "
        " WHERE app_chaine_id IS NOT NULL AND first_seen_at >= ? "
        " GROUP BY app_chaine_id ORDER BY MAX(first_seen_at) DESC", (depuis,))]
    deja_vues = set(nouvelles)
    suivies = sorted(int(u) for u in deja_a_nous if str(u).isdigit())
    return nouvelles + [c for c in suivies if c not in deja_vues]


# ─── L'ETAT N'EST PAS UNE SAISIE : IL SE DEDUIT DES DATES ET DES CASES ───
#
# Mesure du 13/10/2026 sur les 1 000 dernieres lignes de Sheet1 : cette regle redonne la
# colonne « Etat Actuel » 1 000 fois sur 1 000. Elle est donc CALCULEE -- par AppSheet,
# a l'enregistrement d'une ligne. Comme nous n'ecrivons pas par AppSheet, personne ne la
# recalculera pour nous : on applique la MEME regle, sur la ligne complete (ce qui y est
# deja + ce qu'on y ajoute). On ne choisit jamais l'etat : on pose les dates, il suit.
def etat_selon_la_feuille(cases: dict) -> str:
    def rempli(c):
        x = cases.get(c)
        return x is True or (x not in (None, False) and str(x).strip() != "")

    signe = cases.get("Signé") is True or str(cases.get("Signé", "")).upper() in ("TRUE", "VRAI")
    if rempli("Annulée"):
        return "Annulée"
    if rempli("Vente Réglée"):
        return "Vente réglée"
    if rempli("Vente Fixée"):
        return "Vente fixée"
    if rempli("Vente Prévue") and signe:
        return "Vente prévue"
    if rempli("Compromis"):
        return "Compromis en attente"
    return "Offre d'achat"


def evenements(blob) -> list[dict]:
    """propositions_json -> liste d'evenements {type, date}. Liste OU objet seul."""
    try:
        brut = json.loads(blob) if isinstance(blob, str) else blob
    except (TypeError, ValueError):
        return []
    if isinstance(brut, dict):
        brut = [brut]
    if not isinstance(brut, list):
        return []
    return [e for e in brut if isinstance(e, dict) and str(e.get("date") or "").strip()]


#: Les colonnes lues dans le registre, dans l'ordre ou ligne_attendue les indexe.
COLONNES_REGISTRE = ("kind, state, montant, date, date_acte, numero_mandat, app_dossier_id, "
                     "notaire_mandant_nom, notaire_acquereur_nom, acquereurs_json, acquereur_json, "
                     "mandants_json, honoraires_entree, honoraires_sortie, hektor_affaire_id, "
                     "present_in_hektor, propositions_json")


def charger_registre(con: sqlite3.Connection, chaines: list[int]) -> dict[int, list[tuple]]:
    """Toutes les affaires des chaines voulues, en UNE passe par paquet de 900.

    ⚠ `app_chaine_id` n'a pas d'index (mesure du 13/10 : 0,27 s par lecture, base de
      6 Go). Lire chaine par chaine coutait 8 minutes pour 1 748 chaines -- dont 1 617
      « vues pour la premiere fois » le MEME jour, le 15/09/2026 (realignement du
      registre). On ne pose pas d'index : la base est partagee avec le run de nuit.
    """
    par_chaine: dict[int, list[tuple]] = {}
    for debut in range(0, len(chaines), 900):
        paquet = chaines[debut:debut + 900]
        marques = ",".join("?" * len(paquet))
        for row in con.execute(
                f"SELECT app_chaine_id, {COLONNES_REGISTRE} FROM app_affaire_ledger "
                f" WHERE app_chaine_id IN ({marques})", paquet):
            par_chaine.setdefault(row[0], []).append(row[1:])
    return par_chaine


def ligne_attendue(con: sqlite3.Connection, chaine: int,
                   lignes: list[tuple] | None = None) -> dict | None:
    """Ce que la ligne de la feuille DEVRAIT contenir, d'apres notre registre.

    Chaque geste ne fait que POSER UNE DATE (ou cocher une case) ; l'etat en decoule :
        creer une offre        -> Offre Achat
        refuser l'offre        -> Annulee     (date de l'evenement « refus »)
        creer le compromis     -> Compromis + Vente Prevue (date d'acte prevue)
        le compromis est signe -> Signe       (sa date est passee et il est actif)
        annuler le compromis   -> Annulee     (date ou NOUS constatons l'annulation)
        creer la vente         -> Vente Fixee
        la vente est signee    -> Signee      (sa date est passee)
    """
    if lignes is None:
        lignes = con.execute(f"SELECT {COLONNES_REGISTRE} FROM app_affaire_ledger "
                             f" WHERE app_chaine_id = ?", (chaine,)).fetchall()
    affaires = {}
    for row in lignes:
        affaires[row[0]] = row
    if not affaires:
        return None
    offre, compromis, vente = affaires.get("offre"), affaires.get("compromis"), affaires.get("vente")
    socle = vente or compromis or offre

    # ── les dates de l'offre : dans ses EVENEMENTS, pas dans `date`
    # ⚠ Mesure du 13/10 : pour une offre refusee, `date` porte la date du REFUS
    #   (05/10/2026) et non celle de l'offre (20/07/2026). Les 1 117 offres refusees
    #   portent toutes un evenement « refus » date.
    date_offre, date_refus = "", ""
    if offre is not None:
        evts = evenements(offre[16])
        propositions = sorted(str(e["date"]) for e in evts if "refus" not in str(e.get("type", "")).lower())
        refus = sorted(str(e["date"]) for e in evts if "refus" in str(e.get("type", "")).lower())
        date_offre = jj(propositions[0]) if propositions else jj(offre[3])
        if str(offre[1] or "").lower() in ("refused", "refusee"):
            date_refus = jj(refus[-1]) if refus else jj(offre[3])

    cpr_mort = compromis is not None and str(compromis[1] or "").lower() in ("cancelled", "annule")
    if cpr_mort:
        # ⚠ Le registre ne porte AUCUNE date d'annulation de compromis (mesure). On pose la
        #   date ou NOUS la constatons : exacte au geste, a un jour pres a la descente.
        date_annulation = datetime.now().strftime("%d/%m/%Y")
    elif date_refus and compromis is None and vente is None:
        date_annulation = date_refus
    else:
        date_annulation = ""

    bien = con.execute(
        "SELECT numero_dossier, ville, code_postal, agence_nom, type_bien, "
        "       adresse_privee_listing, negociateur_email "
        "  FROM app_dossier_current WHERE app_dossier_id = ?", (socle[6],)).fetchone()
    (numero_dossier, ville, code_postal, agence, type_bien, adresse,
     email_nego) = bien or ("", "", "", "", "", "", "")

    # LA PART D'UNE PERSONNE = LA SOMME DE SES PARTS, COTE ENTREE ET COTE SORTIE.
    # Hektor coupe la commission en deux cotes ; la feuille, elle, donne UNE part par
    # personne, et leur somme fait 100 (997 lignes sur 1 000). Mesure du 13/10 sur la
    # chaine 29031 : BILLIG entree 50 + sortie 50 -> 100 dans la feuille. La premiere
    # version prenait la PREMIERE part puis forcait 100 pour un negociateur seul : juste
    # par hasard ici, et faux des qu'ils sont deux (entree 50 + sortie 25 / sortie 25
    # aurait donne 50 et 25).
    parts: dict[str, float] = {}
    for nom, pourcentage in con.execute(
            "SELECT nom_au_moment, pourcentage FROM app_affaire_repartition "
            " WHERE app_chaine_id = ? AND nom_au_moment IS NOT NULL AND nom_au_moment <> ''",
            (chaine,)):
        court = nom_negociateur(nom)
        try:
            valeur = float(pourcentage or 0)
        except (TypeError, ValueError):
            valeur = 0.0
        if court:
            parts[court] = parts.get(court, 0.0) + valeur
    propres = [(nom, entier(part)) for nom, part in
               sorted(parts.items(), key=lambda x: -x[1])]
    if not propres and str(email_nego or "").strip().lower() in NEGO_PAR_EMAIL:
        # Repli mesure le 13/10 : 3 affaires sur 5 n'ont aucune ligne de repartition.
        # Le negociateur du BIEN, retrouve par son e-mail dans l'onglet Utilisateurs
        # (35 e-mails sur 39 s'y retrouvent, 83 % des biens vivants).
        propres = [(NEGO_PAR_EMAIL[str(email_nego).strip().lower()], "100")]
    total_parts = sum(float(p or 0) for _, p in propres)

    notaires = [n for n in (socle[7], socle[8]) if str(n or "").strip()]
    charge = ""
    if str(socle[12] or "").strip():
        charge = "Vendeur"
    elif str(socle[13] or "").strip():
        charge = "Acquéreur"

    valeurs = {
        "affair_uuid": str(chaine),
        "product_ref": numero_dossier or "",
        "Mandat": str(socle[5] or ""),
        "Nature": TYPE_BIEN.get(str(type_bien or ""), ""),
        "Lien CRM": (f"https://app.netty.fr/~company38325aqy/admin/prod.php"
                     f"?act=show&prod_ref={numero_dossier}") if numero_dossier else "",
        "Agence": AGENCES.get(str(agence or ""), ""),
        "Négociateur 1": propres[0][0] if propres else "",
        "Pourcentage 1": propres[0][1] if propres else "",
        "Négociateur 2": propres[1][0] if len(propres) > 1 else "",
        "Pourcentage 2": propres[1][1] if len(propres) > 1 else "",
        "Notaire": " / ".join(notaires),
        "Charge Commission": charge,
        "Offre Achat": date_offre,
        "Compromis": jj(compromis[3]) if compromis is not None else "",
        # ⚠ De VRAIS booleens (bool:True 3 787 / bool:False 973, mesure du 13/10).
        #   « Signe » = le compromis a REELLEMENT ete signe : sa date est passee ET il est
        #   actif. Mesure : les 205 desaccords « date passee, case non cochee » sont TOUS
        #   des affaires annulees -- jamais signees.
        "Signé": bool(compromis is not None and not cpr_mort and passee(compromis[3])),
        "Vente Prévue": jj(compromis[4]) if compromis is not None else "",
        "Vente Fixée": jj(vente[3]) if vente is not None else "",
        "Signée": bool(vente is not None and passee(vente[3])),
        "Annulée": date_annulation,
        "Acquéreur": partie(socle[9] or socle[10]),
        "Vendeur": partie(socle[11]),
        "Prix": entier(socle[2]),
        "Ville": " ".join(x for x in (ville, code_postal, adresse) if str(x or "").strip()),
    }
    valeurs["Etat Actuel"] = etat_selon_la_feuille(valeurs)
    if propres and round(total_parts) != 100:
        # on n'invente pas la part manquante : elle fait la paie. On l'ecrit telle quelle
        # et on le DIT -- l'humain completera.
        valeurs["_alerte"] = f"les parts connues font {round(total_parts)} %, pas 100"
    # ⚠ Pour l'offre, la date de ses EVENEMENTS : `date` peut avoir ete re-tamponnee par
    #   Hektor (54 offres a la meme seconde le 13/10) et ferait passer une vieille offre
    #   pour une nouvelle.
    dates_reelles = [str(a[3] or "")[:10] for a in (compromis, vente) if a is not None]
    if date_offre:
        dates_reelles.append(datetime.strptime(date_offre, "%d/%m/%Y").strftime("%Y-%m-%d"))
    if date_refus:
        dates_reelles.append(datetime.strptime(date_refus, "%d/%m/%Y").strftime("%Y-%m-%d"))
    valeurs["_derniere_date"] = max((d for d in dates_reelles if d and not d.startswith("0000")),
                                    default="")
    return {k: v for k, v in valeurs.items() if isinstance(v, bool) or str(v).strip()}


# ───────────────────────────── decider, sans jamais ecraser ─────────────────────────────

#: Sans ces trois cases, une ligne neuve n'apprendrait rien a personne : la feuille
#: porte un mandat et un prix sur 100 % de ses lignes. On s'abstient plutot que de
#: salir un tableau de production avec une ligne creuse.
INDISPENSABLES = ("Mandat", "Prix", "product_ref", "Négociateur 1")

#: Une affaire dont la derniere date reelle est plus vieille que ca n'est pas « nouvelle »,
#: meme si notre registre vient de la decouvrir. Mesure du 13/10 : la chaine 11597, un
#: compromis annule de SEPTEMBRE 2022, porte un `first_seen_at` d'aout 2026 (realignement
#: d'identite du registre). Sans cette garde, elle serait nee dans la feuille avec une date
#: d'annulation au jour du passage.
JOURS_MAX_POUR_CREER = 90

#: e-mail (minuscules) -> NOM de l'onglet Utilisateurs ; rempli par main().
NEGO_PAR_EMAIL: dict[str, str] = {}


def decider(attendu: dict[str, str], existante: dict[str, str] | None) -> tuple[str, dict, str]:
    """Rend (geste, champs, explication). Geste : CREER · AVANCER · ABSTENTION · RIEN."""
    if existante is None:
        manquants = [c for c in INDISPENSABLES if not str(attendu.get(c, "")).strip()]
        if manquants:
            return ("INCOMPLET", {},
                    f"ne porte pas {', '.join(manquants)} -- on ne cree pas une ligne creuse")
        limite = (datetime.now() - timedelta(days=JOURS_MAX_POUR_CREER)).strftime("%Y-%m-%d")
        if str(attendu.get("_derniere_date") or "") < limite:
            return ("ANCIENNE", {},
                    f"derniere date reelle {attendu.get('_derniere_date') or 'inconnue'} : "
                    f"plus de {JOURS_MAX_POUR_CREER} jours, ce n'est pas une affaire nouvelle")
        return "CREER", attendu, "aucune ligne ne porte ce numero de chaine ni ce mandat"

    if not str(existante.get("affair_uuid") or "").strip():
        return ("ABSTENTION", {},
                f"la ligne {existante['_rang']} porte ce mandat mais pas notre numero : "
                f"saisie a la main, on n'y touche pas")

    # une ligne a nous : on la fait avancer -- vides seulement, et jamais en arriere
    champs = {}
    for colonne in NOS_COLONNES:
        if colonne in CREATION_SEULEMENT or colonne == "Etat Actuel":
            continue
        neuf = attendu.get(colonne)
        if neuf is None or (not isinstance(neuf, bool) and not str(neuf).strip()):
            continue
        ancien = str(existante.get(colonne) or "").strip()
        if colonne in ("Signé", "Signée"):
            # une case ne passe que de decochee a cochee, jamais l'inverse
            if neuf is True and ancien.upper() in ("", "FALSE", "FAUX", "N"):
                champs[colonne] = True
        elif not ancien:                    # on remplit un vide
            champs[colonne] = neuf

    # L'etat : RECALCULE avec la regle de la feuille, sur la ligne telle qu'elle sera
    # apres notre passage -- ce qu'un humain y a mis (Vente Reglee...) compte aussi. Et il
    # ne recule jamais : si le calcul rend un etat plus bas, on n'y touche pas.
    actuel = str(existante.get("Etat Actuel") or "").strip()
    apres = {**{k: v for k, v in existante.items() if not k.startswith("_")}, **champs}
    etat = etat_selon_la_feuille(apres)
    if etat != actuel and ETATS_RANG.get(etat, 0) > ETATS_RANG.get(actuel, 0):
        champs["Etat Actuel"] = etat
    if not champs:
        return "RIEN", {}, "la ligne est deja a jour"
    return "AVANCER", champs, f"ligne {existante['_rang']}, {len(champs)} case(s) a poser"


# ───────────────────────────── l'envoi ─────────────────────────────

def envoyer_appsheet(action: str, lignes: list[dict], app_id: str, cle: str,
                     table: str) -> tuple[bool, str]:
    """Voie 1 : parler a l'application AppSheet.

    C'est la meilleure des deux : AppSheet genere lui-meme la cle de ligne et applique
    ses valeurs initiales, ses validations et ses bots. Elle n'est PAS disponible chez
    GTI au 13/10/2026 : l'API AppSheet appartient aux licences superieures, et celle du
    compte est AppSheet Core (fournie avec Workspace). La console repond alors
    403 « The API is not enabled for the called application ». Le code reste ici : si la
    licence change, `--voie appsheet` le rouvre sans une ligne a reecrire.
    """
    reponse = requests.post(
        f"{API_APPSHEET}/apps/{app_id}/tables/{table}/Action",
        headers={"ApplicationAccessKey": cle, "Content-Type": "application/json"},
        json={"Action": action,
              "Properties": {"Locale": "fr-FR", "Timezone": "Romance Standard Time"},
              "Rows": lignes},
        timeout=60)
    ok = reponse.status_code in (200, 204)
    return ok, f"HTTP {reponse.status_code} {reponse.text[:300]}"


# ─────────────── Voie 2 : ecrire dans la source de donnees Google Sheets ───────────────
#
# AppSheet est bati SUR ce classeur : il relit sa source a chaque synchronisation. On
# ecrit donc la ou l'application lit. L'acces passe par la cle de service Workspace et
# le scope `spreadsheets`, autorises par l'administrateur du domaine le 13/10/2026, et
# le classeur est partage avec le compte emprunte. C'est l'usage ordinaire de Sheets,
# independant de la licence AppSheet.
#
# LA SEULE PRECAUTION QUE CETTE VOIE AJOUTE : la cle de ligne. AppSheet la genere
# normalement lui-meme ; ici c'est a nous. Sans cle valide, l'application affiche la
# ligne mais ne sait pas l'editer.
#
# ⚠ IL Y A DEUX GENERATIONS DE CLES DANS CETTE FEUILLE, et c'est la RECENTE qu'il faut
#   imiter. Mesure du 13/10 sur les 4 760 valeurs de « ID Unique » :
#       4 166 anciennes   8 caracteres  0-9 A-Z   (S13Z3PIN, 5YUGE9KA)
#         594 recentes    8 caracteres  0-9 a-f   (945146a0, 7cb7142f)
#   et les 500 DERNIERES sont hexadecimales sans exception. La premiere version de ce
#   fichier fabriquait des cles en majuscules : un format abandonne.
ALPHABET_CLE = "0123456789abcdef"


def colonne_lettre(index: int) -> str:
    """0 -> A, 25 -> Z, 26 -> AA. L'onglet va jusqu'a AL."""
    lettre, index = "", index + 1
    while index:
        index, reste = divmod(index - 1, 26)
        lettre = chr(65 + reste) + lettre
    return lettre


def cle_unique(deja_prises: set[str]) -> str:
    import secrets
    for _ in range(10_000):
        cle = "".join(secrets.choice(ALPHABET_CLE) for _ in range(8))
        if cle not in deja_prises:
            deja_prises.add(cle)
            return cle
    raise RuntimeError("impossible de fabriquer une cle de ligne libre")


def creer_dans_la_feuille(jeton: str, lignes: list[list[str]], depart: int,
                          plancher: int) -> tuple[bool, str]:
    """values.append, sur une plage qui DEMARRE APRES LE DERNIER TROU.

    ⚠⚠ C'EST LA PRECAUTION LA PLUS IMPORTANTE DE CE FICHIER, et elle vient d'une
      question de Frederic (13/10). `append` ne cherche pas la derniere ligne du
      classeur : il cherche « un tableau » dans la plage donnee et s'arrete AU PREMIER
      TROU. Or Sheet1 porte 5 lignes entierement vides -- 3541, 3693, 3837, 4019, 4070 --
      alors que les donnees vont jusqu'a 4766. Avec la plage « A:AL », la ligne neuve
      serait partie en 3541, EN PLEIN MILIEU, en decalant 1 225 lignes.
      On demarre donc la plage APRES le dernier trou connu : le tableau vu par Google
      est alors le bloc final, et l'ajout tombe bien a la suite.

    `insertDataOption=INSERT_ROWS` reste pose en second rempart : meme si la fin etait
    mal estimee, Google INSERE une ligne au lieu d'ecrire par-dessus une existante.
    Et le `plancher` fait echouer bruyamment tout atterrissage trop haut.
    """
    reponse = requests.post(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}"
        f"/values/{ONGLET}!A{depart}:AL:append",
        params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"},
        headers={"Authorization": f"Bearer {jeton}", "Content-Type": "application/json"},
        json={"values": lignes}, timeout=90)
    if reponse.status_code != 200:
        return False, f"HTTP {reponse.status_code} {reponse.text[:300]}"
    maj = reponse.json().get("updates", {})
    plage = str(maj.get("updatedRange", ""))
    # Controle d'atterrissage : la plage ecrite doit commencer au-dela du plancher.
    nombres = [int(x) for x in re.findall(r"[A-Z]+(\d+)", plage.split("!")[-1])]
    atterrie = min(nombres) if nombres else 0
    if atterrie and atterrie <= plancher:
        return False, (f"ATTERRISSAGE ANORMAL : ecrit en {plage}, soit AU-DESSUS de la "
                       f"ligne {plancher}. A verifier immediatement dans la feuille.")
    return True, f"HTTP 200 · {maj.get('updatedRows')} ligne(s) en {plage}"


def relire_les_cles(jeton: str, index: dict[str, int]) -> dict[int, str] | None:
    """La colonne « ID Unique » SEULE, relue JUSTE AVANT d'ecrire.

    Une requete, une colonne : c'est bien moins cher que la feuille entiere, et c'est
    ce qui permet de verifier qu'on ecrit toujours a la bonne ligne.

    Rend {rang: cle}, avec la MEME convention que `main()` : le rang 2 est la premiere
    ligne de donnees, la ligne 1 etant l'en-tete.
    Rend None si on n'a pas pu relire -- l'appelant REFUSE alors d'ecrire.
    """
    i = index.get(COLONNE_CLE)
    if i is None:
        return None
    lettre = colonne_lettre(i)
    try:
        reponse = requests.get(
            f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}"
            f"/values/{ONGLET}!{lettre}1:{lettre}6000",
            headers={"Authorization": f"Bearer {jeton}"}, timeout=90)
    except requests.RequestException:
        return None
    if reponse.status_code != 200:
        return None
    valeurs = reponse.json().get("values", [])
    if not valeurs:
        return None
    return {rang: (str(ligne[0]).strip() if ligne else "")
            for rang, ligne in enumerate(valeurs[1:], start=2)}


def avancer_dans_la_feuille(jeton: str, index: dict[str, int],
                            majs: list[dict]) -> tuple[bool, str]:
    """values:batchUpdate, CASE PAR CASE : on n'ecrit que les cellules decidees, jamais
    la ligne entiere -- une ligne entiere ecraserait les colonnes de l'humain.

    ⚠⚠ CONTROLE D'ATTERRISSAGE (22/10/2026). C'est le pendant, pour l'AVANCEE, de la
      precaution que `creer_dans_la_feuille` porte depuis le 13/10 -- meme danger, autre
      fonction, et celle-ci etait restee nue.

      Les rangs sont lus au DEBUT du passage (`lire_feuille`), et ecrits a la FIN : entre
      les deux, tout le calcul. Si un humain insere, supprime ou TRIE pendant ce temps,
      la ligne 4231 n'est plus la meme personne -- et on poserait la commission de l'un
      chez l'autre, EN SILENCE (Google repond « 200, 1 cellule ecrite » : il a livre a
      l'adresse donnee, il ne sait pas qu'on visait quelqu'un d'autre).

      Aujourd'hui le passage tourne la nuit, feuille deserte : le risque est nul. Des
      qu'on ecrira EN JOURNEE, avec du monde dans le classeur, il devient certain.

      La parade : on ecrit a un NOM, pas a une PLACE. Juste avant le batchUpdate on
      relit la colonne des cles et, pour chaque ligne :
         la cle est toujours au meme rang  -> on ecrit
         elle a bouge, et une seule ligne la porte -> ON LA SUIT, et on le DIT
         elle a disparu, ou plusieurs la portent  -> ON N'ECRIT PAS, et on le DIT
      Un tri complet de l'onglet est ainsi rattrape ligne par ligne, pas subi.
    """
    frais = relire_les_cles(jeton, index)
    if frais is None:
        return False, ("ARRET : impossible de relire la colonne « ID Unique » avant "
                       "d'ecrire. On n'ecrit pas dans le doute -- le prochain passage "
                       "reprendra ces lignes.")

    retenus: list[dict] = []
    suivis: list[str] = []
    ecartes: list[str] = []
    for maj in majs:
        rang = maj["_rang"]
        attendue = str(maj.get(COLONNE_CLE) or "").strip()
        if not attendue:
            ecartes.append(f"ligne {rang} : pas de « {COLONNE_CLE} », on ne sait pas la "
                           f"reconnaitre")
            continue
        if frais.get(rang) == attendue:
            retenus.append(maj)
            continue
        ailleurs = [r for r, cle in frais.items() if cle == attendue]
        if len(ailleurs) == 1:
            retenus.append({**maj, "_rang": ailleurs[0]})
            suivis.append(f"{attendue} : {rang} -> {ailleurs[0]}")
        elif not ailleurs:
            ecartes.append(f"{attendue} (ligne {rang}) : DISPARUE de la feuille")
        else:
            ecartes.append(f"{attendue} (ligne {rang}) : portee par PLUSIEURS lignes "
                           f"{ailleurs}")

    # Le signal passe par la sortie du passage, qui est lue : un deplacement n'est jamais
    # normal, et un ecart encore moins.
    for ligne in suivis:
        print(f"    ⚠ LIGNE DEPLACEE, on la suit par sa cle -- {ligne}")
    for ligne in ecartes:
        print(f"    ⛔ NON ECRITE -- {ligne}")

    data = []
    for maj in retenus:
        rang = maj["_rang"]
        for colonne, valeur in maj.items():
            if colonne.startswith("_"):
                continue
            i = index.get(colonne)
            if i is None:
                continue
            data.append({"range": f"{ONGLET}!{colonne_lettre(i)}{rang}", "values": [[valeur]]})
    # Le controle se raconte dans TOUS les cas, y compris quand il n'ecarte rien : un
    # compteur absent se lit « ca n'a pas tourne », pas « il n'y avait rien ».
    # ⚠ `suivis` est un SOUS-ENSEMBLE de `retenus` : les annoncer tels quels compterait
    #   deux fois une ligne deplacee. On publie des parts DISJOINTES, dont la somme doit
    #   retomber sur le total -- un compteur qui ne s'additionne pas ne se verifie pas.
    intactes = len(retenus) - len(suivis)
    controle = (f"controle d'atterrissage : {intactes} au meme rang + {len(suivis)} "
                f"deplacee(s) et suivie(s) + {len(ecartes)} ecartee(s) = {len(majs)}")
    if intactes + len(suivis) + len(ecartes) != len(majs):
        controle += " ⛔ COMPTE FAUX"
    if not data:
        return True, f"rien a ecrire · {controle}"
    reponse = requests.post(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values:batchUpdate",
        headers={"Authorization": f"Bearer {jeton}", "Content-Type": "application/json"},
        json={"valueInputOption": "USER_ENTERED", "data": data}, timeout=90)
    ok = reponse.status_code == 200
    corps = reponse.json().get("totalUpdatedCells") if ok else reponse.text[:300]
    return ok, (f"HTTP {reponse.status_code} · {len(data)} cellule(s) demandee(s), "
                f"{corps} ecrite(s) · {controle}")


# ───────────────────────────── le programme ─────────────────────────────

def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Alimenter l'AppSheet de suivi des transactions")
    parser.add_argument("--envoyer", action="store_true",
                        help="ECRIT dans l'AppSheet. Sans ce drapeau, rien ne part.")
    parser.add_argument("--depuis", default=datetime.now().strftime("%Y-%m-01"),
                        help="affaires VUES POUR LA PREMIERE FOIS depuis cette date (AAAA-MM-JJ)")
    parser.add_argument("--chaine", default=None, help="une seule chaine, par son numero")
    parser.add_argument("--max", type=int, default=0, help="s'arreter apres N gestes (0 = tous)")
    parser.add_argument("--voie", choices=("sheets", "appsheet"), default="sheets",
                        help="sheets : ecrire dans la source de donnees (defaut, seule "
                             "disponible avec une licence AppSheet Core) · appsheet : "
                             "l'API de l'application, si la licence l'inclut un jour")
    args = parser.parse_args()

    load_env_file(RACINE / ".env")
    app_id = os.environ.get("APPSHEET_APP_ID", "").strip()
    cle = os.environ.get("APPSHEET_ACCESS_KEY", "").strip()
    table = os.environ.get("APPSHEET_TABLE", ONGLET).strip() or ONGLET
    if args.envoyer and args.voie == "appsheet" and not (app_id and cle):
        print("ARRET : --voie appsheet demande APPSHEET_APP_ID et APPSHEET_ACCESS_KEY.")
        return 2

    entete, lignes_feuille = lire_feuille()

    # L'onglet « Utilisateurs » est la table de reference des negociateurs : NOM (le
    # libelle exact de « Negociateur 1 ») et Agence. Mesure du 13/10/2026 : la colonne
    # Agence de Sheet1 est celle du NEGOCIATEUR 1 dans cet onglet -- 790 fois sur 805
    # dans les 1 000 dernieres lignes -- et non celle du bien. On la lit donc ici.
    rep_ut = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/Utilisateurs!A1:U200",
        headers={"Authorization": f"Bearer {jeton_sheets()}"}, timeout=90)
    utilisateurs = rep_ut.json().get("values", []) if rep_ut.status_code == 200 else []
    agence_du_nego = {}
    if utilisateurs:
        iu = {n: i for i, n in enumerate(utilisateurs[0])}
        for l in utilisateurs[1:]:
            nom = str(l[iu["NOM"]]).strip() if iu.get("NOM") is not None and iu["NOM"] < len(l) else ""
            ag = str(l[iu["Agence"]]).strip() if iu.get("Agence") is not None and iu["Agence"] < len(l) else ""
            if nom:
                agence_du_nego[nom] = ag
            mail = str(l[iu["Email"]]).strip().lower() if iu.get("Email") is not None and iu["Email"] < len(l) else ""
            if nom and mail:
                NEGO_PAR_EMAIL[mail] = nom
    else:
        print("  ⚠ onglet Utilisateurs illisible : l'agence sera celle du BIEN, a verifier")
    index = {nom: i for i, nom in enumerate(entete)}

    def case(ligne: list[str], nom: str) -> str:
        i = index.get(nom)
        return str(ligne[i]).strip() if i is not None and i < len(ligne) else ""

    par_uuid, par_mandat = {}, {}
    for rang, ligne in enumerate(lignes_feuille, start=2):
        vue = {nom: case(ligne, nom) for nom in entete}
        vue["_rang"] = rang
        vue["_cle"] = case(ligne, "ID Unique")
        if vue.get("affair_uuid"):
            par_uuid[vue["affair_uuid"]] = vue
        if vue.get("Mandat"):
            par_mandat.setdefault(vue["Mandat"], []).append(vue)

    con = sqlite3.connect(f"file:{RACINE / 'phase2' / 'phase2.sqlite'}?mode=ro", uri=True, timeout=60)
    con.execute("PRAGMA busy_timeout=60000")

    compte = {"CREER": 0, "AVANCER": 0, "ABSTENTION": 0, "INCOMPLET": 0, "ANCIENNE": 0, "RIEN": 0,
              "AMBIGU": 0, "SANS DONNEE": 0}
    a_creer, a_avancer = [], []
    # Ou une ligne neuve atterrira -- calcule et DIT des le passage a blanc, parce que
    # c'est la seule chose qui pourrait abimer un tableau de production.
    trous = [r for r, l in enumerate(lignes_feuille, start=2)
             if not any(str(x).strip() for x in l)]
    derniere_pleine = max((r for r, l in enumerate(lignes_feuille, start=2)
                           if any(str(x).strip() for x in l)), default=1)
    depart = (max(trous) + 1) if trous else 2

    print(f"{'A BLANC -- rien ne sera ecrit' if not args.envoyer else 'ENVOI REEL'}"
          f" · feuille : {len(lignes_feuille)} lignes · depuis le {args.depuis}")
    print(f"  trous dans la feuille : {trous or 'aucun'} · derniere ligne pleine : "
          f"{derniere_pleine} · une ligne neuve irait en {derniere_pleine + 1}")
    print()

    a_examiner = chaines_a_examiner(con, args.depuis, args.chaine, set(par_uuid))
    registre = charger_registre(con, a_examiner)
    print(f"  chaines examinees : {len(a_examiner)}")
    print()
    for chaine in a_examiner:
        attendu = ligne_attendue(con, chaine, registre.get(chaine, []))
        if not attendu:
            compte["SANS DONNEE"] += 1
            continue
        nego = attendu.get("Négociateur 1", "")
        if nego in agence_du_nego and agence_du_nego[nego]:
            attendu["Agence"] = agence_du_nego[nego]
        elif nego and agence_du_nego:
            # hors de la liste : AppSheet l'affichera, mais ce n'est pas une valeur de reference
            attendu["_alerte"] = " ; ".join(x for x in (
                attendu.get("_alerte"), f"« {nego} » n'est pas dans l'onglet Utilisateurs") if x)
        existante = par_uuid.get(str(chaine))
        if existante is None:
            memes = par_mandat.get(attendu.get("Mandat", ""), [])
            if len(memes) > 1:
                compte["AMBIGU"] += 1
                print(f"  AMBIGU      chaine {chaine} : le mandat {attendu.get('Mandat')} porte "
                      f"{len(memes)} lignes -- a trancher a la main")
                continue
            existante = memes[0] if memes else None

        geste, champs, pourquoi = decider(attendu, existante)
        compte[geste] += 1
        if geste == "CREER":
            print(f"  CREER       chaine {chaine} · {pourquoi}")
            if attendu.get("_alerte"):
                print(f"                ⚠ {attendu['_alerte']}")
            for colonne in NOS_COLONNES:
                if isinstance(champs.get(colonne), bool) or champs.get(colonne):
                    print(f"                {colonne:<18} = {str(champs[colonne])[:62]}")
            a_creer.append(champs)
        elif geste == "AVANCER":
            print(f"  AVANCER     chaine {chaine} · {pourquoi}")
            for colonne, valeur in champs.items():
                ancien = str(existante.get(colonne) or "") or "(vide)"
                print(f"                {colonne:<18} {ancien[:24]:<24} -> {str(valeur)[:34]}")
            a_avancer.append({"ID Unique": existante["_cle"],
                              "_rang": existante["_rang"], **champs})
        elif geste in ("ABSTENTION", "INCOMPLET", "ANCIENNE"):
            print(f"  {geste:<11} chaine {chaine} · {pourquoi}")
        if args.max and (len(a_creer) + len(a_avancer)) >= args.max:
            print(f"  (arret apres {args.max} gestes, comme demande)")
            break

    con.close()
    print()
    print("  ".join(f"{k} {v}" for k, v in compte.items()))

    if not args.envoyer:
        print()
        print("Rien n'a ete ecrit. Pour envoyer : --envoyer (et --chaine <n> pour une seule ligne).")
        return 0

    if args.voie == "appsheet":
        for action, lot in (("Add", a_creer), ("Edit", a_avancer)):
            for debut in range(0, len(lot), 50):
                paquet = [{k: v for k, v in r.items() if not k.startswith("_")}
                          for r in lot[debut:debut + 50]]
                if not paquet:
                    continue
                ok, detail = envoyer_appsheet(action, paquet, app_id, cle, table)
                print(f"  {action} de {len(paquet)} ligne(s) : {'OK' if ok else 'ECHEC'} -- {detail}")
                if not ok:
                    return 1
        return 0

    # ── voie « sheets » : on ecrit la ou l'application lit
    jeton = jeton_sheets()
    if a_creer:
        # Une ligne complete, dans l'ordre exact de l'en-tete : les colonnes de l'humain
        # partent VIDES (jamais absentes -- une case manquante decalerait tout le reste).
        prises = {str(l.get("ID Unique") or "").strip()
                  for l in list(par_uuid.values()) + [x for v in par_mandat.values() for x in v]}
        prises.discard("")
        tableau = []
        for champs in a_creer:
            champs = dict(champs)
            champs["ID Unique"] = cle_unique(prises)
            tableau.append([champs.get(nom, "") for nom in entete])
        print(f"  la plage d'ajout demarre en A{depart} (apres le dernier trou)")
        ok, detail = creer_dans_la_feuille(jeton, tableau, depart, derniere_pleine - 1)
        print(f"  CREATION de {len(tableau)} ligne(s) : {'OK' if ok else 'ECHEC'} -- {detail}")
        if not ok:
            return 1
    if a_avancer:
        ok, detail = avancer_dans_la_feuille(jeton, index, a_avancer)
        print(f"  AVANCEE de {len(a_avancer)} ligne(s) : {'OK' if ok else 'ECHEC'} -- {detail}")
        if not ok:
            return 1
    if not a_creer and not a_avancer:
        print("  rien a envoyer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
