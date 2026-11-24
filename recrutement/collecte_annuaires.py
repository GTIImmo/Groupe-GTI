"""Recrutement -- piece 1 : le collecteur des annuaires de mandataires (20/11/2026).

Note du chantier : notice/CHANTIER_RECRUTEMENT_ANNUAIRE_MANDATAIRES_2026-11-20.md

CE QUE FAIT CE SCRIPT
    Il lit les annuaires PUBLICS de trois reseaux (iad, SAFTI, Keller Williams) pour NOTRE REGION
    (les 4 departements de nos 17 agences : 07, 42, 43, 63) et ecrit un CSV a ouvrir dans Excel.
    Il n'ecrit RIEN en base, ne touche NI Hektor, NI le worker, NI le run de nuit.

LES COORDONNEES (correction du chantier par Frederic, 20/11, note §9 -- elle remplace « sans
    telephone ni email ») : on garde le telephone et l'e-mail SEULEMENT quand la page les AFFICHE a
    tout visiteur, sans clic, avec leur source (`source_contact`). Jamais un contact cache derriere un
    clic, masque ou encode (iad). La commande `controle` le VERIFIE (0 coordonnee iad, toute
    coordonnee a sa source et un format valide, aucune hors de sa colonne).
CE QU'IL NE GARDE JAMAIS : ni photo, ni texte de presentation, ni date de naissance.

LA POLITESSE
    robots.txt respecte (avec ses jokers), Crawl-delay respecte, une page toutes les 3 s au plus
    (5 s chez KW), arret net du reseau sur un 403.

LA METHODE (memoire « mesure longue : decoupee, ecrite au fil »)
    Des sous-commandes, chacune s'arrete d'elle-meme apres --minutes (9 par defaut) et REPREND
    la ou elle s'etait arretee. Tout s'ecrit au fil dans une base SQLite locale, hors du depot :
        C:/Hektor/recrutement_donnees/recrutement.sqlite
        C:/Hektor/recrutement_donnees/journal.txt          (une ligne horodatee par evenement)
    Code de sortie : 0 = fini · 3 = coupe par le temps, relancer la meme commande · 1 = erreur.

LES COMMANDES, dans l'ordre (toujours `python -X utf8 -u`)
    communes                    les communes des 4 departements (API ouverte geo.api.gouv.fr)
    iad liste | iad fiches      les pages departement, puis une fiche par conseiller (le RSAC)
    safti liste | safti fiches  une grille de communes (liste « aux alentours »), puis les fiches
    kw liste | kw fiches        le plan de site (205 fiches France), puis les fiches
    siren                       l'API ouverte « Recherche d'entreprises » ; place les fiches KW et
                                RETIRE tout ce qui est hors region (minimisation)
    csv                         le CSV + le compte rendu
    controle                    les comptes, les doublons, les temoins (code 0 vert / 1 rouge)
    Option --limite N : n'en lit que N (essai).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html as html_lib
import json
import math
import os
import re
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

import requests

# --------------------------------------------------------------------------------------------
# REGLAGES
# --------------------------------------------------------------------------------------------
DOSSIER = Path(os.environ.get("RECRUTEMENT_DONNEES", r"C:\Hektor\recrutement_donnees"))
BASE = DOSSIER / "recrutement.sqlite"
JOURNAL = DOSSIER / "journal.txt"
SORTIE = DOSSIER / "sortie"

DEPARTEMENTS = ("07", "42", "43", "63")  # « notre region » = les 4 departements de nos agences
IAD_PAGES_DEPARTEMENT = {
    "07": "ardeche-07",
    "42": "loire-42",
    "43": "haute-loire-43",
    "63": "puy-de-dome-63",
}

# Nos 17 agences actives, lues dans app_registre_agence le 20/11/2026. Ses colonnes adresse / CP /
# ville sont VIDES : la position vient de la commune (centre de la commune, geo.api.gouv.fr).
AGENCES_GTI = (
    ("Ambert", "63"), ("Annonay", "07"), ("Brioude", "43"), ("Courpière", "63"),
    ("Craponne-sur-Arzon", "43"), ("Dunières", "43"), ("Firminy", "42"), ("Issoire", "63"),
    ("Le Puy-en-Velay", "43"), ("Monistrol-sur-Loire", "43"), ("Montbrison", "42"),
    ("Saint-Bonnet-le-Château", "42"), ("Saint-Didier-en-Velay", "43"), ("Saint-Étienne", "42"),
    ("Saint-Just-Saint-Rambert", "42"), ("Tence", "43"), ("Yssingeaux", "43"),
)

# SAFTI : la page d'une commune donne ses conseillers + ceux « aux alentours » (mesure du 20/11 :
# jusqu'a ~13-15 km, liste complete, sans pagination). On interroge une grille de communes
# espacees de 10 km au plus : toute commune de la region est a moins de 10 km d'une page lue.
SAFTI_ESPACEMENT_KM = 10.0

INTERVALLE = {  # secondes minimum entre deux pages d'un meme hote
    "www.iadfrance.fr": 3.0,
    "www.safti.fr": 3.0,
    "www.kwfrance.com": 5.0,
    "geo.api.gouv.fr": 0.3,
    "recherche-entreprises.api.gouv.fr": 0.3,
}
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")

CODE_FINI, CODE_ERREUR, CODE_A_REPRENDRE = 0, 1, 3


# --------------------------------------------------------------------------------------------
# OUTILS
# --------------------------------------------------------------------------------------------
def maintenant() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def aujourdhui() -> str:
    return dt.date.today().isoformat()


def journal(reseau: str, message: str) -> None:
    ligne = f"{maintenant()} [{reseau}] {message}"
    print(ligne, flush=True)
    DOSSIER.mkdir(parents=True, exist_ok=True)
    with open(JOURNAL, "a", encoding="utf-8") as f:
        f.write(ligne + "\n")


def sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")


def cle_commune(nom: str) -> str:
    t = sans_accents(nom or "").lower().replace("'", " ").replace("-", " ")
    t = re.sub(r"\bste?\b", lambda m: "sainte" if m.group(0) == "ste" else "saint", t)
    return re.sub(r"\s+", " ", t).strip()


def chemin_safti(nom: str, cp: str) -> str:
    t = sans_accents(nom).lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return f"{t}-{cp}"


def departement_de(cp: str | None) -> str | None:
    cp = (cp or "").strip()
    if not re.fullmatch(r"\d{5}", cp):
        return None
    return "20" if cp.startswith("20") else cp[:2]


def distance_km(lat1, lon1, lat2, lon2) -> float:
    p = math.radians
    a = (math.sin(p(lat2 - lat1) / 2) ** 2
         + math.cos(p(lat1)) * math.cos(p(lat2)) * math.sin(p(lon2 - lon1) / 2) ** 2)
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def siren_valide(siren: str | None) -> bool:
    """Le SIREN porte une cle de Luhn."""
    if not siren or not re.fullmatch(r"\d{9}", siren):
        return False
    total = 0
    for i, c in enumerate(reversed(siren)):
        n = int(c)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def siren_depuis_rsac(texte: str | None) -> str | None:
    """« 530 547 108 RSAC VANNES » / « 999057524 » / « RSAC 878043025 » -> les 9 chiffres."""
    if not texte:
        return None
    m = re.search(r"(?<!\d)(\d{3})[\s\u00a0\u202f.]?(\d{3})[\s\u00a0\u202f.]?(\d{3})(?!\d)", texte)
    return "".join(m.groups()) if m else None


def separer_nom(nom_complet: str) -> tuple[str, str]:
    """« Carole Pichon-Grand » -> (Carole, Pichon-Grand) ; « Sylvie VERSCHAVE » -> (Sylvie, VERSCHAVE)."""
    # ⚠ 24/11 : vu en réel, Dr House met parfois du HTML dans le « name » de son JSON-LD (un duo : « <p>Prénom
    #   <strong>Nom</strong></p><p>&nbsp;et&nbsp;</p>… ») -- 3 fiches. Un nom n'a jamais de balise ni d'entité :
    #   on les retire ici, pour TOUTES les sources (la prochaine collecte réécrit les noms déjà connus).
    nom_complet = re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]*>", " ", nom_complet or ""))).strip()
    # « Ariane Roffet (EI) » : la mention entre parentheses n'est pas un nom
    mots = [m for m in re.sub(r"\([^)]*\)", " ", nom_complet or "").split() if re.search(r"[A-Za-zÀ-ÿ]", m)]
    if not mots:
        return "", ""
    majuscules = [m for m in mots if len(m) > 1 and m.upper() == m and re.search(r"[A-Z]", sans_accents(m))]
    if majuscules and len(majuscules) < len(mots):
        nom = " ".join(majuscules)
        prenom = " ".join(m for m in mots if m not in majuscules)
        return prenom, nom
    return mots[0], " ".join(mots[1:])


class ArretNet(Exception):
    """Un 403 / un refus : on arrete ce reseau tout de suite (regle du projet : jamais insister)."""


class TempsEcoule(Exception):
    pass


# --------------------------------------------------------------------------------------------
# LA BASE LOCALE
# --------------------------------------------------------------------------------------------
SCHEMA = """
create table if not exists commune (
    code_insee text primary key, nom text, cle text, cp text, codes_postaux text, dep text,
    lat real, lon real, population integer
);
create table if not exists page_lue (
    url text primary key, reseau text, lu_le text, statut_http integer, note text
);
create table if not exists grille_safti (
    chemin text primary key, dep text, population integer, ordre integer,
    lue integer default 0, chemin_rendu text, nb_ville integer, nb_alentours integer
);
create table if not exists fiche (
    reseau text not null, identifiant text not null, url text, prenom text, nom text,
    commune text, code_postal text, departement text, lat real, lon real,
    siren text, rsac_ville text, nb_annonces integer, nb_avis integer, note_avis real,
    distinction text, fiche_lue integer default 0, desactive integer default 0,
    premiere_vue text, derniere_vue text,
    primary key (reseau, identifiant)
);
create table if not exists entreprise (
    siren text primary key, trouve integer, date_creation text, etat text, naf text,
    siege_cp text, siege_commune text, siege_lat real, siege_lon real, lu_le text,
    diffusion text, opposition integer
);
-- R2 (20/11 au soir) : LA MISE A JOUR. Chaque passage est une COLLECTE numerotee ; chaque fiche lue
-- pendant une collecte ouverte y laisse une OBSERVATION. Rien n'est supprime sur une absence.
-- ⚠ `numero` est TOUJOURS pose par le code (max + 1), jamais laisse a SQLite.
create table if not exists collecte (
    numero integer primary key, debut text not null, fin text, etat text not null, note text
);
create table if not exists observation (
    collecte integer not null, reseau text not null, identifiant text not null,
    primary key (collecte, reseau, identifiant)
);
create table if not exists source_etat (
    collecte integer not null, reseau text not null, vus integer, precedent integer,
    sante text not null, raison text, primary key (collecte, reseau)
);
-- le carnet : ce qu'un humain corrige dans l'app. La relecture ne l'ecrase jamais : il vit a part et
-- s'applique a la lecture (export, envoi).
create table if not exists correction (
    reseau text not null, identifiant text not null, champ text not null, valeur text,
    par text, le text not null, primary key (reseau, identifiant, champ)
);
-- « ne plus contacter » et « effacer » : des EMPREINTES seulement (sha256), lues avant tout enregistrement
create table if not exists liste_noire (
    empreinte text primary key, nature text not null, le text not null
);
create table if not exists evenement_fiche (
    le text not null, collecte integer, reseau text not null, identifiant text not null,
    quoi text not null, detail text
);
"""

# CORRECTION DU 20/11 (note §9) : les coordonnees entrent, mais SEULEMENT celles que la page AFFICHE
# a tout visiteur, sans clic ; `source_contact` dit la page et le champ. Jamais un contact cache ou
# encode (iad : le controle exige 0 coordonnee iad).
COLONNES_CONTACT = ("telephone", "email", "source_contact")
COLONNES_FICHE = ("url", "prenom", "nom", "commune", "code_postal", "departement", "lat", "lon",
                  "siren", "rsac_ville", "nb_annonces", "nb_avis", "note_avis", "distinction",
                  "fiche_lue", "desactive", "agence", "fonction") + COLONNES_CONTACT
# les reseaux ou un contact est CACHE (derriere un clic, masque, encode) : on n'en garde aucun
RESEAUX_CONTACT_CACHE = ("iad",)


def ouvrir_base() -> sqlite3.Connection:
    DOSSIER.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(BASE, timeout=60)
    con.execute("pragma journal_mode=wal")
    con.execute("pragma busy_timeout=60000")
    con.executescript(SCHEMA)
    presentes = {r[1] for r in con.execute("pragma table_info(fiche)")}
    for col in ("agence", "fonction") + COLONNES_CONTACT:  # migration de la base du 20/11 matin
        if col not in presentes:
            con.execute(f"alter table fiche add column {col} text")
    # R2 : l'etat de suivi. ⚠ PAS « etat » : l'export joint deja entreprise.etat (actif / cesse).
    for col, typ in (("etat_suivi", "text"), ("etat_depuis", "text"), ("absences", "integer default 0"),
                     ("motif_depart", "text")):
        if col not in presentes:
            con.execute(f"alter table fiche add column {col} {typ}")
    con.commit()
    con.row_factory = sqlite3.Row
    return con


# ---- R2 : la collecte ouverte et la liste « ne plus contacter » (lues une fois par processus) ----
_CACHE: dict = {}


def collecte_ouverte(con) -> int | None:
    if "collecte" not in _CACHE:
        r = con.execute("select numero from collecte where etat='en_cours' order by numero desc limit 1").fetchone()
        _CACHE["collecte"] = r[0] if r else None
    return _CACHE["collecte"]


def _h(texte: str) -> str:
    return hashlib.sha256(texte.encode("utf-8")).hexdigest()


def empreintes_personne(siren=None, telephone=None, email=None, prenom=None, nom=None, departement=None) -> list[tuple[str, str]]:
    """Ce qui reconnait une personne SANS la garder lisible : SIREN, telephone, e-mail, nom + departement."""
    e = []
    if siren:
        e.append(("siren", _h("siren:" + re.sub(r"\D", "", siren))))
    if telephone:
        e.append(("telephone", _h("tel:" + re.sub(r"\D", "", telephone))))
    if email:
        e.append(("email", _h("email:" + email.strip().lower())))
    if nom and departement:
        e.append(("nom", _h("nom:" + _cle_nom(prenom, nom) + ":" + departement)))
    return e


def liste_noire(con) -> set:
    if "noire" not in _CACHE:
        _CACHE["noire"] = {r[0] for r in con.execute("select empreinte from liste_noire")}
    return _CACHE["noire"]


def telephone_lisible(brut: str | None) -> str | None:
    """« +33674933054 » / « 06.74.93.30.54 » -> « 06 74 93 30 54 » ; autre chose -> rien."""
    chiffres = re.sub(r"\D", "", brut or "")
    if chiffres.startswith("33") and len(chiffres) == 11:
        chiffres = "0" + chiffres[2:]
    if not re.fullmatch(r"0[1-9]\d{8}", chiffres):
        return None
    return " ".join(chiffres[i:i + 2] for i in range(0, 10, 2))


def email_lisible(brut: str | None) -> str | None:
    e = (brut or "").strip().lower().removeprefix("mailto:").split("?")[0]
    return e if re.fullmatch(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}", e) else None


def enregistrer_fiche(con: sqlite3.Connection, reseau: str, identifiant: str, **champs) -> None:
    """Ecrit au fil. Ne remplace jamais une valeur connue par un vide ; garde la date de premiere vue."""
    inconnus = set(champs) - set(COLONNES_FICHE)
    if inconnus:  # verrou de minimisation : aucune colonne hors de la liste ne peut entrer
        raise ValueError(f"colonnes refusees : {sorted(inconnus)}")
    jour = aujourdhui()
    existe = con.execute("select * from fiche where reseau=? and identifiant=?", (reseau, identifiant)).fetchone()
    # R2 : LA LISTE « NE PLUS CONTACTER » EST LUE AVANT TOUT ENREGISTREMENT. Une personne qui y est
    # n'entre pas ; si elle etait la, elle sort (avec ses observations).
    noire = liste_noire(con)
    if noire:
        avant = dict(existe) if existe else {}
        fusion = {k: (champs.get(k) if champs.get(k) not in (None, "") else avant.get(k))
                  for k in ("siren", "telephone", "email", "prenom", "nom", "departement")}
        if any(e in noire for _, e in empreintes_personne(**fusion)):
            con.execute("delete from fiche where reseau=? and identifiant=?", (reseau, identifiant))
            con.execute("delete from observation where reseau=? and identifiant=?", (reseau, identifiant))
            con.commit()
            journal("liste-noire", f"une fiche {reseau} ecartee : la personne a demande a ne plus etre contactee")
            return
    n_collecte = collecte_ouverte(con)
    if n_collecte:
        con.execute("insert or ignore into observation (collecte, reseau, identifiant) values (?,?,?)",
                    (n_collecte, reseau, identifiant))
    if not existe:
        con.execute("insert into fiche (reseau, identifiant, premiere_vue, derniere_vue) values (?,?,?,?)",
                    (reseau, identifiant, jour, jour))
    sets, vals = ["derniere_vue=?"], [jour]
    for k, v in champs.items():
        if v is None or v == "":
            continue
        sets.append(f"{k}=?")
        vals.append(v)
    con.execute(f"update fiche set {', '.join(sets)} where reseau=? and identifiant=?", (*vals, reseau, identifiant))
    con.commit()


def noter_page(con, url, reseau, statut, note=""):
    con.execute("insert or replace into page_lue (url, reseau, lu_le, statut_http, note) values (?,?,?,?,?)",
                (url, reseau, maintenant(), statut, note))
    con.commit()


# --------------------------------------------------------------------------------------------
# LE LECTEUR POLI : robots.txt, Crawl-delay, intervalle par hote, arret net sur 403
# --------------------------------------------------------------------------------------------
class Lecteur:
    def __init__(self, fin: float):
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"})
        self.dernier: dict[str, float] = {}
        self.robots: dict[str, tuple[list, float]] = {}
        self.fin = fin

    def _robots(self, hote: str) -> tuple[list, float]:
        if hote in self.robots:
            return self.robots[hote]
        regles, delai = [], 0.0
        try:
            r = self.s.get(f"https://{hote}/robots.txt", timeout=30)
            if r.status_code == 200:
                regles, delai = analyser_robots(r.text)
        except requests.RequestException:
            pass
        self.robots[hote] = (regles, delai)
        return regles, delai

    def autorise(self, url: str) -> bool:
        parts = urlsplit(url)
        if parts.netloc.endswith("api.gouv.fr"):
            return True  # API publiques faites pour etre appelees
        regles, _ = self._robots(parts.netloc)
        chemin = parts.path + (("?" + parts.query) if parts.query else "")
        return robots_autorise(regles, chemin)

    def get(self, url: str, reseau: str, entetes: dict | None = None) -> requests.Response:
        if time.time() > self.fin:
            raise TempsEcoule()
        hote = urlsplit(url).netloc
        if not self.autorise(url):
            raise PermissionError(f"robots.txt interdit {url}")
        _, delai_robots = self._robots(hote)
        intervalle = max(INTERVALLE.get(hote, 3.0), delai_robots)
        attente = self.dernier.get(hote, 0) + intervalle - time.time()
        if attente > 0:
            time.sleep(attente)
        r = None
        for essai in range(3):
            try:
                r = self.s.get(url, timeout=30, allow_redirects=True, headers=entetes)
            except requests.RequestException as e:
                journal(reseau, f"reseau indisponible ({e.__class__.__name__}) sur {url}, essai {essai + 1}/3")
                time.sleep(15)
                continue
            finally:
                self.dernier[hote] = time.time()
            if r.status_code in (429, 503):
                journal(reseau, f"HTTP {r.status_code} sur {url} : pause de {60 * (essai + 1)} s")
                time.sleep(60 * (essai + 1))
                continue
            break
        if r is None:
            raise requests.ConnectionError(f"aucune reponse pour {url}")
        if r.status_code == 403:
            raise ArretNet(f"HTTP 403 sur {url}")
        return r

    def post(self, url: str, reseau: str, donnees: dict, entetes: dict | None = None) -> requests.Response:
        """R1 (20/11 soir) : le formulaire de recherche d'un annuaire (Lucarne : « ou recherchez-vous ? »).
        Memes regles que get : robots.txt, intervalle par hote, arret net sur 403. Un seul essai."""
        if time.time() > self.fin:
            raise TempsEcoule()
        hote = urlsplit(url).netloc
        if not self.autorise(url):
            raise PermissionError(f"robots.txt interdit {url}")
        _, delai_robots = self._robots(hote)
        attente = self.dernier.get(hote, 0) + max(INTERVALLE.get(hote, 3.0), delai_robots) - time.time()
        if attente > 0:
            time.sleep(attente)
        try:
            r = self.s.post(url, data=donnees, timeout=30, headers=entetes)
        finally:
            self.dernier[hote] = time.time()
        if r.status_code == 403:
            raise ArretNet(f"HTTP 403 sur {url}")
        return r


def analyser_robots(texte: str) -> tuple[list, float]:
    groupes, courant, dernier_ua = [], None, False
    for brut in texte.splitlines():
        ligne = brut.split("#", 1)[0].strip()
        if ":" not in ligne:
            continue
        k, v = ligne.split(":", 1)
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            if courant is None or not dernier_ua:
                courant = {"ua": [], "regles": [], "delai": 0.0}
                groupes.append(courant)
            courant["ua"].append(v.lower())
            dernier_ua = True
            continue
        dernier_ua = False
        if courant is None:
            continue
        if k in ("allow", "disallow"):
            courant["regles"].append((k, v))
        elif k == "crawl-delay":
            try:
                courant["delai"] = float(v)
            except ValueError:
                pass
    etoile = [g for g in groupes if "*" in g["ua"]]
    regles = [r for g in etoile for r in g["regles"]]
    delai = max([g["delai"] for g in etoile] or [0.0])
    return regles, delai


def robots_autorise(regles: list, chemin: str) -> bool:
    meilleur, verdict = -1, True
    for genre, motif in regles:
        if not motif:
            continue  # « Disallow: » vide = tout permis
        rx = "^" + re.escape(motif).replace(r"\*", ".*")
        if rx.endswith(r"\$"):
            rx = rx[:-2] + "$"
        if re.match(rx, chemin):
            longueur = len(motif)
            if longueur > meilleur or (longueur == meilleur and genre == "allow"):
                meilleur, verdict = longueur, (genre == "allow")
    return verdict


# --------------------------------------------------------------------------------------------
# DECODAGE DES PAGES
# --------------------------------------------------------------------------------------------
def nuxt_data(texte: str):
    """iad (Nuxt 3) : la charge est un tableau « devalue » ou chaque nombre est un renvoi."""
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', texte, re.S)
    if not m:
        return None
    tab = json.loads(m.group(1))
    enveloppes = {"Reactive", "ShallowReactive", "Ref", "ShallowRef", "EmptyRef", "NuxtError"}

    def resoudre(i, profondeur=0):
        if not isinstance(i, int) or i < 0:
            return None
        if profondeur > 60:
            return None
        v = tab[i]
        if isinstance(v, list):
            if v and isinstance(v[0], str) and v[0] in enveloppes:
                return resoudre(v[1], profondeur + 1) if len(v) > 1 else None
            if v and isinstance(v[0], str) and v[0] in ("Set", "Map", "Date", "RegExp", "BigInt", "null", "undefined"):
                return None
            return [resoudre(x, profondeur + 1) for x in v]
        if isinstance(v, dict):
            return {k: resoudre(x, profondeur + 1) for k, x in v.items()}
        return v

    return tab, resoudre


def next_data(texte: str):
    """SAFTI (Next.js) : la charge est dans __NEXT_DATA__."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', texte, re.S)
    return json.loads(m.group(1)) if m else None


def chercher_dicts(obj, predicat, profondeur=0):
    if profondeur > 25:
        return
    if isinstance(obj, dict):
        if predicat(obj):
            yield obj
        for v in obj.values():
            yield from chercher_dicts(v, predicat, profondeur + 1)
    elif isinstance(obj, list):
        for v in obj:
            yield from chercher_dicts(v, predicat, profondeur + 1)


def json_ld(texte: str) -> list:
    blocs = []
    for m in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', texte, re.S):
        try:
            d = json.loads(m)
        except json.JSONDecodeError:
            continue
        blocs.extend(d.get("@graph", [d]) if isinstance(d, dict) else d)
    return blocs


def texte_visible(texte: str) -> str:
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", texte, flags=re.S)
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", t)))


def commune_cp(texte: str | None) -> tuple[str | None, str | None]:
    """« Montbrison (42600) » -> (Montbrison, 42600)."""
    m = re.search(r"^(.*?)\s*\((\d{5})\)", texte or "")
    return (m.group(1).strip(), m.group(2)) if m else (None, None)


# --------------------------------------------------------------------------------------------
# COMMUNES (geo.api.gouv.fr, donnees ouvertes de l'Etat)
# --------------------------------------------------------------------------------------------
def cmd_communes(con, lecteur, args) -> int:
    for dep in DEPARTEMENTS:
        url = f"https://geo.api.gouv.fr/departements/{dep}/communes?fields=nom,code,codesPostaux,centre,population&format=json"
        r = lecteur.get(url, "communes")
        r.raise_for_status()
        n = 0
        for c in r.json():
            cps = c.get("codesPostaux") or []
            lon, lat = (c.get("centre") or {}).get("coordinates", (None, None))
            con.execute("insert or replace into commune values (?,?,?,?,?,?,?,?,?)",
                        (c["code"], c["nom"], cle_commune(c["nom"]), cps[0] if cps else None,
                         ",".join(cps), dep, lat, lon, c.get("population") or 0))
            n += 1
        con.commit()
        journal("communes", f"departement {dep} : {n} communes")
    manquantes = [nom for nom, dep in AGENCES_GTI if position_commune(con, nom, None, dep) is None]
    if manquantes:
        journal("communes", f"⚠ agences sans position : {manquantes}")
        return CODE_ERREUR
    journal("communes", f"les {len(AGENCES_GTI)} agences GTI sont placees")
    return CODE_FINI


def position_commune(con, nom: str | None, cp: str | None, dep: str | None = None):
    """Le centre d'une commune, par (cp, nom), sinon par nom dans le departement."""
    cle = cle_commune(nom or "")
    if cp:
        for r in con.execute("select * from commune where (','||codes_postaux||',') like ?", (f"%,{cp},%",)):
            if r["cle"] == cle:
                return r
        lignes = con.execute("select * from commune where (','||codes_postaux||',') like ?", (f"%,{cp},%",)).fetchall()
        if len(lignes) == 1:
            return lignes[0]
    if cle:
        dep = dep or departement_de(cp)
        q = "select * from commune where cle=?" + (" and dep=?" if dep else "")
        lignes = con.execute(q, (cle, dep) if dep else (cle,)).fetchall()
        if len(lignes) == 1:
            return lignes[0]
    return None


# --------------------------------------------------------------------------------------------
# IAD
# --------------------------------------------------------------------------------------------
IAD = "https://www.iadfrance.fr"


def cmd_iad_liste(con, lecteur, args) -> int:
    lus = 0
    for dep, slug in IAD_PAGES_DEPARTEMENT.items():
        page, total, par_page = 1, None, None
        while True:
            url = f"{IAD}/trouver-un-conseiller/{slug}" + (f"?page={page}" if page > 1 else "")
            deja = con.execute("select statut_http, note from page_lue where url=? and substr(lu_le,1,10)=?",
                               (url, aujourdhui())).fetchone()
            if deja and deja["statut_http"] == 200 and not args.relire:
                total, par_page = json.loads(deja["note"] or "{}").get("total"), json.loads(deja["note"] or "{}").get("par_page")
            else:
                r = lecteur.get(url, "iad")
                if r.status_code != 200:
                    noter_page(con, url, "iad", r.status_code)
                    journal("iad", f"⚠ HTTP {r.status_code} sur {url}")
                    break
                nd = nuxt_data(r.text)
                if not nd:
                    noter_page(con, url, "iad", r.status_code, "pas de __NUXT_DATA__")
                    journal("iad", f"⚠ page sans donnees : {url}")
                    break
                tab, resoudre = nd
                bloc = next((resoudre(i) for i, v in enumerate(tab)
                             if isinstance(v, dict) and "totalItems" in v and "sectorSlug" in v), None)
                if not bloc:
                    noter_page(con, url, "iad", r.status_code, "pas de liste")
                    journal("iad", f"⚠ pas de liste sur {url}")
                    break
                total, par_page = bloc.get("totalItems"), bloc.get("itemsPerPage")
                items = bloc.get("items") or []
                gardes = 0
                for a in items:
                    if not isinstance(a, dict) or not a.get("userName"):
                        continue
                    commune, cp = commune_cp(a.get("statusOrSector"))
                    dep_agent = departement_de(cp)
                    if dep_agent and dep_agent not in DEPARTEMENTS:
                        continue  # liste de la Loire, conseiller pose ailleurs : hors region
                    prenom, nom = separer_nom(a.get("fullName") or "")
                    enregistrer_fiche(con, "iad", a["userName"], url=f"{IAD}/conseiller-immobilier/{a['userName']}",
                                      prenom=prenom, nom=nom, commune=commune, code_postal=cp,
                                      departement=dep_agent or dep, nb_annonces=a.get("propertyCount"),
                                      nb_avis=a.get("reviewsCount"), note_avis=a.get("reviewsRatingAverage"))
                    gardes += 1
                noter_page(con, url, "iad", 200, json.dumps({"total": total, "par_page": par_page, "items": len(items)}))
                journal("iad", f"{slug} page {page} : {len(items)} sur la page, {gardes} gardes (total annonce {total})")
                lus += 1
                if args.limite and lus >= args.limite:
                    return CODE_FINI
            if not total or not par_page or page * par_page >= total:
                break
            page += 1
    n = con.execute("select count(*) from fiche where reseau='iad'").fetchone()[0]
    journal("iad", f"liste finie : {n} conseillers iad dans la region")
    return CODE_FINI


def cmd_iad_fiches(con, lecteur, args) -> int:
    a_lire = con.execute("select identifiant, url from fiche where reseau='iad' and (fiche_lue=0 or ?) order by identifiant",
                         (1 if args.relire else 0,)).fetchall()
    journal("iad", f"fiches a lire : {len(a_lire)}")
    for n, f in enumerate(a_lire, 1):
        if args.limite and n > args.limite:
            break
        r = lecteur.get(f["url"], "iad")
        noter_page(con, f["url"], "iad", r.status_code)
        if r.status_code == 404:
            enregistrer_fiche(con, "iad", f["identifiant"], fiche_lue=1, desactive=1)
            journal("iad", f"{f['identifiant']} : fiche disparue (404)")
            continue
        if r.status_code != 200:
            journal("iad", f"⚠ {f['identifiant']} : HTTP {r.status_code}")
            continue
        nd = nuxt_data(r.text)
        agent = None
        if nd:
            tab, resoudre = nd
            agent = next((resoudre(i) for i, v in enumerate(tab)
                          if isinstance(v, dict) and "fullName" in v and "legal" in v), None)
        if not agent:
            journal("iad", f"⚠ {f['identifiant']} : fiche sans donnees conseiller")
            continue
        rsac = ((agent.get("legal") or {}).get("rsac") or {})
        siren = siren_depuis_rsac(str(rsac.get("number") or "")) or siren_depuis_rsac(agent.get("legalDescription"))
        loc = agent.get("location") or {}
        cp = loc.get("postcode")
        prenom, nom = separer_nom(agent.get("fullName") or "")
        enregistrer_fiche(con, "iad", f["identifiant"], prenom=prenom, nom=nom, commune=loc.get("place"),
                          code_postal=cp, departement=departement_de(cp), siren=siren,
                          rsac_ville=(rsac.get("place") or None), nb_annonces=agent.get("propertyCount"),
                          nb_avis=agent.get("reviewsCount"), note_avis=agent.get("reviewsRatingAverage"),
                          fiche_lue=1, desactive=1 if agent.get("isDeactivated") else 0)
        if n % 20 == 0:
            journal("iad", f"{n}/{len(a_lire)} fiches lues")
    reste = con.execute("select count(*) from fiche where reseau='iad' and fiche_lue=0").fetchone()[0]
    journal("iad", f"fiches : reste {reste} a lire")
    return CODE_FINI if reste == 0 or args.limite else CODE_A_REPRENDRE


# --------------------------------------------------------------------------------------------
# SAFTI
# --------------------------------------------------------------------------------------------
SAFTI = "https://www.safti.fr"


def preparer_grille_safti(con) -> int:
    if con.execute("select count(*) from grille_safti").fetchone()[0]:
        return 0
    communes = con.execute("select * from commune where dep in (%s) and lat is not null" %
                           ",".join("?" * len(DEPARTEMENTS)), DEPARTEMENTS).fetchall()
    if not communes:
        raise RuntimeError("lancer d'abord la commande `communes`")
    agences = {(cle_commune(nom), dep) for nom, dep in AGENCES_GTI}
    tri = sorted(communes, key=lambda c: ((c["cle"], c["dep"]) not in agences, -(c["population"] or 0)))
    choisies = []
    for c in tri:
        if not c["cp"]:
            continue
        if all(distance_km(c["lat"], c["lon"], o["lat"], o["lon"]) > SAFTI_ESPACEMENT_KM for o in choisies):
            choisies.append(c)
    for ordre, c in enumerate(choisies):
        con.execute("insert or ignore into grille_safti (chemin, dep, population, ordre) values (?,?,?,?)",
                    (chemin_safti(c["nom"], c["cp"]), c["dep"], c["population"], ordre))
    con.commit()
    journal("safti", f"grille : {len(choisies)} communes sur {len(communes)} (espacement {SAFTI_ESPACEMENT_KM:g} km)")
    return len(choisies)


def cmd_safti_liste(con, lecteur, args) -> int:
    preparer_grille_safti(con)
    a_lire = con.execute("select chemin from grille_safti where lue=0 or ? order by ordre",
                         (1 if args.relire else 0,)).fetchall()
    journal("safti", f"pages commune a lire : {len(a_lire)}")
    for n, g in enumerate(a_lire, 1):
        if args.limite and n > args.limite:
            break
        url = f"{SAFTI}/trouver-un-conseiller/{g['chemin']}"
        r = lecteur.get(url, "safti")
        noter_page(con, url, "safti", r.status_code)
        if r.status_code != 200:
            journal("safti", f"⚠ {g['chemin']} : HTTP {r.status_code}")
            con.execute("update grille_safti set lue=1, chemin_rendu=? where chemin=?", (f"HTTP {r.status_code}", g["chemin"]))
            con.commit()
            continue
        nd = next_data(r.text)
        pp = ((nd or {}).get("props") or {}).get("pageProps") or {}
        rendu = ((pp.get("cityUrlSearch") or {}).get("path")) or "?"
        ville, alentours = pp.get("initialAgents") or [], pp.get("initialExtendedAgents") or []
        gardes = 0
        for a in ville + alentours:
            if not isinstance(a, dict) or not a.get("slug"):
                continue
            cp = str(a.get("postCode") or "").strip()
            dep = departement_de(cp)
            if dep not in DEPARTEMENTS:
                continue
            enregistrer_fiche(con, "safti", a["slug"], url=f"{SAFTI}/votre-conseiller-safti/{a['slug']}",
                              prenom=(a.get("firstName") or "").strip(), nom=(a.get("lastName") or "").strip(),
                              commune=(a.get("city") or "").strip(), code_postal=cp, departement=dep,
                              lat=a.get("lat"), lon=a.get("lng"), nb_annonces=a.get("nbProperties"),
                              nb_avis=a.get("googleMBUserRatingsTotal"), note_avis=a.get("googleMBRating"))
            gardes += 1
        total_v, total_a = pp.get("totalInitialAgents"), pp.get("totalInitialExtendedAgents")
        if (total_v is not None and total_v > len(ville)) or (total_a is not None and total_a > len(alentours)):
            journal("safti", f"⚠ {g['chemin']} : liste TRONQUEE ({len(ville)}/{total_v} + {len(alentours)}/{total_a})")
        con.execute("update grille_safti set lue=1, chemin_rendu=?, nb_ville=?, nb_alentours=? where chemin=?",
                    (rendu, len(ville), len(alentours), g["chemin"]))
        con.commit()
        if re.sub(r"[\s\-]+", "-", rendu) != g["chemin"]:
            journal("safti", f"{g['chemin']} compris comme « {rendu} »")
        if n % 20 == 0:
            nb = con.execute("select count(*) from fiche where reseau='safti'").fetchone()[0]
            journal("safti", f"{n}/{len(a_lire)} communes lues, {nb} conseillers connus")
    reste = con.execute("select count(*) from grille_safti where lue=0").fetchone()[0]
    nb = con.execute("select count(*) from fiche where reseau='safti'").fetchone()[0]
    journal("safti", f"liste : reste {reste} communes, {nb} conseillers SAFTI dans la region")
    return CODE_FINI if reste == 0 or args.limite else CODE_A_REPRENDRE


def cmd_safti_fiches(con, lecteur, args) -> int:
    a_lire = con.execute("select identifiant, url, prenom, nom from fiche where reseau='safti' and (fiche_lue=0 or ?) order by identifiant",
                         (1 if args.relire else 0,)).fetchall()
    journal("safti", f"fiches a lire : {len(a_lire)}")
    for n, f in enumerate(a_lire, 1):
        if args.limite and n > args.limite:
            break
        r = lecteur.get(f["url"], "safti")
        noter_page(con, f["url"], "safti", r.status_code)
        if r.status_code == 404:
            enregistrer_fiche(con, "safti", f["identifiant"], fiche_lue=1, desactive=1)
            journal("safti", f"{f['identifiant']} : fiche disparue (404)")
            continue
        if r.status_code != 200:
            journal("safti", f"⚠ {f['identifiant']} : HTTP {r.status_code}")
            continue
        nd = next_data(r.text) or {}
        blocs = list(chercher_dicts(nd, lambda d: "rsac" in d and "lastName" in d))
        # la fiche peut citer d'autres conseillers : on prend celui qui porte LES NOMS de la fiche
        soi = [b for b in blocs if cle_commune(str(b.get("lastName"))) == cle_commune(f["nom"] or "")
               and cle_commune(str(b.get("firstName"))) == cle_commune(f["prenom"] or "")]
        if len(blocs) > 1 and len(soi) != 1:
            journal("safti", f"⚠ {f['identifiant']} : {len(blocs)} blocs conseiller, {len(soi)} a son nom")
        m = soi[0] if soi else (blocs[0] if len(blocs) == 1 else None)
        if not m:
            journal("safti", f"⚠ {f['identifiant']} : fiche sans bloc conseiller")
            continue
        rsac = str(m.get("rsac") or "")
        ville_rsac = None
        mv = re.search(r"RSAC\s+(?:DE\s+)?(.+)$", rsac, re.I)
        if mv:
            ville_rsac = mv.group(1).strip()
        distinctions = [lib for cle, lib in (("conseillerClubExcellence", "Club Excellence"),) if m.get(cle)]
        # coordonnees AFFICHEES : le telephone du bloc conseiller, l'adresse @safti.fr a son nom
        tel = telephone_lisible(m.get("phoneNumber"))
        adresses = sorted(set(a.lower() for a in re.findall(r"[A-Za-z0-9._\-]+@safti\.fr", r.text)))
        cle_nom = re.sub(r"[^a-z]", "", sans_accents(f["nom"] or "").lower())
        a_son_nom = [a for a in adresses if cle_nom and cle_nom in re.sub(r"[^a-z]", "", a.split("@")[0])]
        mail = a_son_nom[0] if len(a_son_nom) == 1 else None
        sources = [s for s, v in (("fiche SAFTI : telephone affiche", tel), ("fiche SAFTI : e-mail affiche", mail)) if v]
        enregistrer_fiche(con, "safti", f["identifiant"], siren=siren_depuis_rsac(rsac), rsac_ville=ville_rsac,
                          distinction=", ".join(distinctions) or None, fiche_lue=1, telephone=tel, email=mail,
                          source_contact=" + ".join(sources) or None)
        if n % 20 == 0:
            journal("safti", f"{n}/{len(a_lire)} fiches lues")
    reste = con.execute("select count(*) from fiche where reseau='safti' and fiche_lue=0").fetchone()[0]
    journal("safti", f"fiches : reste {reste} a lire")
    return CODE_FINI if reste == 0 or args.limite else CODE_A_REPRENDRE


# --------------------------------------------------------------------------------------------
# KELLER WILLIAMS
# --------------------------------------------------------------------------------------------
KW = "https://www.kwfrance.com"


def cmd_kw_liste(con, lecteur, args) -> int:
    r = lecteur.get(f"{KW}/sitemap.xml", "kw")
    r.raise_for_status()
    urls = sorted(set(re.findall(r"<loc>(https://www\.kwfrance\.com/conseiller/[^<]+)</loc>", r.text)))
    for u in urls:
        ident = u.rsplit(",", 1)[-1] if "," in u else u.rsplit("/", 1)[-1]
        if not con.execute("select 1 from fiche where reseau='kw' and identifiant=?", (ident,)).fetchone():
            con.execute("insert into fiche (reseau, identifiant, url, premiere_vue, derniere_vue) values ('kw',?,?,?,?)",
                        (ident, u, aujourdhui(), aujourdhui()))
        else:
            con.execute("update fiche set derniere_vue=? where reseau='kw' and identifiant=?", (aujourdhui(), ident))
    con.commit()
    journal("kw", f"plan de site : {len(urls)} conseillers en France (la region sera connue par le SIREN)")
    return CODE_FINI


def cmd_kw_fiches(con, lecteur, args) -> int:
    a_lire = con.execute("select identifiant, url from fiche where reseau='kw' and (fiche_lue=0 or ?) order by cast(identifiant as integer)",
                         (1 if args.relire else 0,)).fetchall()
    journal("kw", f"fiches a lire : {len(a_lire)}")
    for n, f in enumerate(a_lire, 1):
        if args.limite and n > args.limite:
            break
        r = lecteur.get(f["url"], "kw")
        noter_page(con, f["url"], "kw", r.status_code)
        if r.status_code in (404, 410):
            enregistrer_fiche(con, "kw", f["identifiant"], fiche_lue=1, desactive=1)
            continue
        if r.status_code != 200:
            journal("kw", f"⚠ {f['identifiant']} : HTTP {r.status_code}")
            continue
        personne = next((b for b in json_ld(r.text) if isinstance(b, dict) and b.get("@type") == "Person"), {})
        nom_complet = (personne.get("name") or "").strip()
        if not nom_complet:  # repli : le slug « prenom.nom »
            slug = f["url"].rsplit("/", 1)[-1].split(",")[0]
            nom_complet = " ".join(p.capitalize() for p in slug.replace("-", " ").split("."))
        prenom, nom = separer_nom(nom_complet)
        mr = re.search(r"RSAC\s*(?:de\s+([A-Za-zÀ-ÿ' \-]+?)\s*)?(?:n°\s*)?(\d[\d \u00a0]{8,12})", texte_visible(r.text))
        siren = siren_depuis_rsac(mr.group(2)) if mr else None
        tel = telephone_lisible(personne.get("telephone"))  # affiche en clair sur la fiche (« Contact »)
        enregistrer_fiche(con, "kw", f["identifiant"], prenom=prenom, nom=nom, siren=siren,
                          rsac_ville=(mr.group(1).strip() if mr and mr.group(1) else None), fiche_lue=1,
                          telephone=tel, source_contact="fiche KW : telephone affiche" if tel else None)
        if n % 20 == 0:
            journal("kw", f"{n}/{len(a_lire)} fiches lues")
    reste = con.execute("select count(*) from fiche where reseau='kw' and fiche_lue=0").fetchone()[0]
    journal("kw", f"fiches : reste {reste} a lire")
    return CODE_FINI if reste == 0 or args.limite else CODE_A_REPRENDRE


# --------------------------------------------------------------------------------------------
# CORRECTION DU 20/11 -- LES NOUVELLES SOURCES (sondes du 20/11, note §9-§10)
# --------------------------------------------------------------------------------------------
def lire(lecteur, url, reseau, entetes=None) -> str | None:
    r = lecteur.get(url, reseau, entetes)
    if r.status_code != 200:
        journal(reseau, f"⚠ HTTP {r.status_code} sur {url}")
        return None
    if "challenge-platform" in r.text and "cf-chl" in r.text and len(r.text) < 30000:
        raise ArretNet(f"page anti-robot sur {url}")  # on ne contourne jamais
    return r.text


def texte_de(fragment: str) -> str:
    t = re.sub(r"<br\s*/?>", " / ", fragment or "")
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", t))).strip(" /")


def cle_personne(nom_complet: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", sans_accents(nom_complet).lower()).strip("-")


def ld_agence(texte: str) -> dict:
    """Le bloc JSON-LD « RealEstateAgent » d'une page d'agence : nom, CP, commune, position, telephone."""
    for b in json_ld(texte):
        if isinstance(b, dict) and "RealEstateAgent" in str(b.get("@type")):
            adr = b.get("address") or {}
            geo = b.get("geo") or {}
            return {"nom": b.get("name"), "cp": str(adr.get("postalCode") or "").strip() or None,
                    "commune": adr.get("addressLocality"), "lat": _flottant(geo.get("latitude")),
                    "lon": _flottant(geo.get("longitude")), "tel": telephone_lisible(b.get("telephone"))}
    return {}


def choisir_telephone(numeros: list[str], exclus: set) -> str | None:
    """Le numero de LA PERSONNE : jamais le standard de l'agence ; un mobile d'abord."""
    propres = [n for n in dict.fromkeys(telephone_lisible(x) for x in numeros) if n and n not in exclus]
    mobiles = [n for n in propres if n.startswith(("06", "07"))]
    return (mobiles or propres or [None])[0]


def compter_fin(reseau: str, con) -> int:
    n = con.execute("select count(*) from fiche where reseau=?", (reseau,)).fetchone()[0]
    t = con.execute("select count(*) from fiche where reseau=? and (telephone is not null or email is not null)", (reseau,)).fetchone()[0]
    journal(reseau, f"fini : {n} personnes dans la region, {t} avec une coordonnee affichee")
    return CODE_FINI


# ---- LE REGISTRE PUBLIC (API Recherche d'entreprises) ---------------------------------------
REGISTRE = "https://recherche-entreprises.api.gouv.fr/search"


def cmd_registre(con, lecteur, args) -> int:
    """Les entreprises individuelles ACTIVES en 68.31Z de la region. Deux pieges (sonde du 20/11) :
    le filtre departement porte aussi sur des etablissements FERMES -> on garde le SIEGE dans la
    region ; et ⛔ une personne en OPPOSITION a la prospection n'est PAS gardee du tout : sa seule
    source ici est le registre, et elle a refuse cet usage."""
    page, gardes, opposees, hors = 1, 0, 0, 0
    while True:
        url = (f"{REGISTRE}?activite_principale=68.31Z&departement={','.join(DEPARTEMENTS)}&nature_juridique=1000"
               f"&etat_administratif=A&minimal=true&include=siege,dirigeants&per_page=25&page={page}")
        r = lecteur.get(url, "registre")
        if r.status_code != 200:
            journal("registre", f"⚠ HTTP {r.status_code} page {page}")
            return CODE_ERREUR
        d = r.json()
        for e in d.get("results") or []:
            siege = e.get("siege") or {}
            dep = siege.get("departement") or departement_de(siege.get("code_postal"))
            if dep not in DEPARTEMENTS:
                hors += 1
                continue
            if e.get("opposition_diffusion_commerciale"):
                opposees += 1
                continue
            dirigeant = next((x for x in e.get("dirigeants") or [] if x.get("nom")), {})
            prenom = (dirigeant.get("prenoms") or "").split()[0].capitalize() if dirigeant.get("prenoms") else ""
            nom = (dirigeant.get("nom") or "").strip()
            if not nom:
                continue
            s = e["siren"]
            enregistrer_fiche(con, "registre", s, url=f"https://annuaire-entreprises.data.gouv.fr/entreprise/{s}",
                              prenom=prenom, nom=nom, commune=_diffusible(siege.get("libelle_commune")),
                              code_postal=_diffusible(siege.get("code_postal")), departement=dep,
                              lat=_flottant(siege.get("latitude")), lon=_flottant(siege.get("longitude")),
                              siren=s, fiche_lue=1, fonction="entrepreneur individuel (68.31Z)")
            con.execute("insert or replace into entreprise values (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (s, 1, e.get("date_creation"), e.get("etat_administratif"), e.get("activite_principale"),
                         _diffusible(siege.get("code_postal")), _diffusible(siege.get("libelle_commune")),
                         _flottant(siege.get("latitude")), _flottant(siege.get("longitude")), maintenant(),
                         e.get("statut_diffusion"), 0))
            con.commit()
            gardes += 1
        total_pages = d.get("total_pages") or 1
        if page % 10 == 0 or page >= total_pages:
            journal("registre", f"page {page}/{total_pages} : {gardes} gardes, {opposees} en opposition (ecartes), {hors} siege hors region")
        if page >= total_pages or (args.limite and page >= args.limite):
            break
        page += 1
    return CODE_FINI


# ---- ORPI ------------------------------------------------------------------------------------
ORPI = "https://www.orpi.com"
INTERVALLE["www.orpi.com"] = 5.0  # Cloudflare present : rester lent, s'arreter au premier defi
ORPI_DEPARTEMENTS = ("loire", "ardeche", "puy-de-dome", "haute-loire")


def cmd_orpi(con, lecteur, args) -> int:
    agences = []
    for nom_dep in ORPI_DEPARTEMENTS:
        url = f"{ORPI}/agences-immobilieres-{nom_dep}/"
        r = lecteur.get(url, "orpi")
        if r.status_code != 200 or f"agences-immobilieres-{nom_dep}" not in r.url:
            journal("orpi", f"{nom_dep} : pas de page departement (redirigee : {r.url})")
            continue
        for b in json_ld(r.text):
            if isinstance(b, dict) and b.get("@type") == "ItemList":
                agences += [i.get("url") for i in b.get("itemListElement") or [] if i.get("url")]
    agences = list(dict.fromkeys(agences))
    journal("orpi", f"{len(agences)} agences dans les pages departement")
    for n, url in enumerate(agences, 1):
        if args.limite and n > args.limite:
            break
        t = lire(lecteur, url, "orpi")
        if not t:
            continue
        ag = ld_agence(t)
        dep = departement_de(ag.get("cp"))
        if dep not in DEPARTEMENTS:
            continue
        exclus = {ag.get("tel")} if ag.get("tel") else set()
        cartes = t.split('<article class="c-box c-box--senary">')[1:]
        for c in cartes:
            c = c.split("</article>")[0]
            m_nom = re.search(r"<h4[^>]*>(.*?)</h4>", c, re.S)
            if not m_nom:
                continue
            nom_complet = texte_de(m_nom.group(1))
            m_f = re.search(r'<p class="mt-n mb-xs[^"]*">(.*?)</p>', c, re.S)
            m_id = re.search(r"agentId=(\d+)", c)
            tel = choisir_telephone(re.findall(r'href="tel:([^"]+)"', c), exclus)
            prenom, nom = separer_nom(nom_complet)
            ident = m_id.group(1) if m_id else f"{url.rstrip('/').rsplit('/', 1)[-1]}/{cle_personne(nom_complet)}"
            enregistrer_fiche(con, "orpi", ident, url=url, prenom=prenom, nom=nom, fonction=texte_de(m_f.group(1)) if m_f else None,
                              agence=ag.get("nom"), commune=ag.get("commune"), code_postal=ag.get("cp"), departement=dep,
                              lat=ag.get("lat"), lon=ag.get("lon"), fiche_lue=1, telephone=tel,
                              source_contact="page agence Orpi : telephone affiche" if tel else None)
        journal("orpi", f"{n}/{len(agences)} {ag.get('nom')} : {len(cartes)} personnes")
    return compter_fin("orpi", con)


# ---- LAFORET ---------------------------------------------------------------------------------
LAFORET = "https://www.laforet.com"
LAFORET_DEPARTEMENTS = ("loire", "haute-loire", "puy-de-dome", "ardeche")


def cmd_laforet(con, lecteur, args) -> int:
    slugs = []
    for nom_dep in LAFORET_DEPARTEMENTS:
        t = lire(lecteur, f"{LAFORET}/departement/immobilier-{nom_dep}", "laforet")
        if t:
            slugs += re.findall(r'/agence-immobiliere/([a-z0-9\-]+)"', t)
    slugs = list(dict.fromkeys(slugs))
    journal("laforet", f"{len(slugs)} agences dans les pages departement")
    for n, slug in enumerate(slugs, 1):
        if args.limite and n > args.limite:
            break
        url = f"{LAFORET}/agence-immobiliere/{slug}"
        t = lire(lecteur, url, "laforet")
        if not t:
            continue
        ag = ld_agence(t)
        dep = departement_de(ag.get("cp"))
        if dep not in DEPARTEMENTS:
            continue
        i = t.find("Notre équipe")
        bloc = t[i:t.find("</section>", i)] if i >= 0 else ""
        personnes = re.findall(r"<h3[^>]*>(.*?)</h3>\s*<p[^>]*>(.*?)</p>", bloc, re.S)
        for nom_brut, fonction in personnes:
            nom_complet = texte_de(nom_brut)
            prenom, nom = separer_nom(nom_complet)
            enregistrer_fiche(con, "laforet", f"{slug}/{cle_personne(nom_complet)}", url=url, prenom=prenom, nom=nom,
                              fonction=texte_de(fonction), agence=ag.get("nom"), commune=ag.get("commune"),
                              code_postal=ag.get("cp"), departement=dep, lat=ag.get("lat"), lon=ag.get("lon"), fiche_lue=1)
        journal("laforet", f"{n}/{len(slugs)} {ag.get('nom')} : {len(personnes)} personnes")
    return compter_fin("laforet", con)


# ---- CENTURY 21 (l'equipe est sur le mini-site de chaque agence) ------------------------------
C21 = "https://www.century21.fr"
C21_DEPARTEMENTS = ("d-07_ardeche", "d-42_loire", "d-43_haute_loire", "d-63_puy_de_dome")


def cmd_c21(con, lecteur, args) -> int:
    agences = []
    for slug in C21_DEPARTEMENTS:
        t = lire(lecteur, f"{C21}/trouver_agence/{slug}/", "c21")
        if not t:
            continue
        m = re.search(r"data-agencies='(.*?)'", t, re.S)
        if not m:
            journal("c21", f"⚠ {slug} : pas de liste d'agences")
            continue
        liste = json.loads(html_lib.unescape(m.group(1)))
        positions = sorted((t.find(a["absolute_url"]), a) for a in liste if a.get("absolute_url") in t)
        for k, (pos, a) in enumerate(positions):
            fin = positions[k + 1][0] if k + 1 < len(positions) else len(t)
            mini = re.search(r'href="(//www\.century21[^"]+)"', t[pos:fin])
            a["mini"] = ("https:" + mini.group(1).rstrip("/")) if mini else None
            agences.append(a)
    journal("c21", f"{len(agences)} agences, {sum(1 for a in agences if a.get('mini'))} avec un mini-site")
    for n, a in enumerate(agences, 1):
        if args.limite and n > args.limite:
            break
        dep = departement_de(a.get("code_postal"))
        if dep not in DEPARTEMENTS or not a.get("mini"):
            continue
        t = lire(lecteur, a["mini"] + "/agence/", "c21")
        if not t:
            continue
        cartes = t.split("sa-agence-notre_agence__employee")[1:]
        for c in cartes:
            m_nom = re.search(r'c-text-theme-heading-4[^"]*">(.*?)</div>', c, re.S)
            if not m_nom:
                continue
            m_f = re.search(r'c-text-theme-mentions[^"]*">(.*?)</div>', c, re.S)
            nom_complet = texte_de(m_nom.group(1))
            prenom, nom = separer_nom(nom_complet)
            enregistrer_fiche(con, "c21", f"{a['ref_agence']}/{cle_personne(nom_complet)}", url=a["mini"] + "/agence/",
                              prenom=prenom, nom=nom, fonction=texte_de(m_f.group(1)) if m_f else None, agence=a.get("nom"),
                              commune=(a.get("ville") or "").title(), code_postal=a.get("code_postal"), departement=dep,
                              lat=_flottant(a.get("lat")), lon=_flottant(a.get("lng")), fiche_lue=1)
        journal("c21", f"{n}/{len(agences)} {a.get('nom')} : {len(cartes)} personnes")
    return compter_fin("c21", con)


# ---- 42EME AVENUE (Saint-Etienne, Andrezieux, Monistrol) --------------------------------------
A42 = "https://www.42emeavenue.com"


def cmd_42avenue(con, lecteur, args) -> int:
    t = lire(lecteur, f"{A42}/sitemap-institutionnel.xml", "42avenue")
    urls = sorted(set(re.findall(r"<loc>(https://www\.42emeavenue\.com/conseiller-[^<]+\.php)</loc>", t or "")))
    journal("42avenue", f"{len(urls)} fiches dans le plan de site")
    for n, url in enumerate(urls, 1):
        if args.limite and n > args.limite:
            break
        f = lire(lecteur, url, "42avenue")
        if not f:
            continue
        titre = texte_de((re.search(r"<title>(.*?)</title>", f, re.S) or [None, ""])[1])
        nom_complet = titre.rsplit(" - ", 1)[-1].strip()
        sans_scripts = re.sub(r"<script.*?</script>|<style.*?</style>", " ", f, flags=re.S)
        morceaux = html_lib.unescape(re.sub(r"<[^>]+>", "|", sans_scripts)).split("|")
        visible = " | ".join(re.sub(r"\s+", " ", x).strip() for x in morceaux if x.strip()) + " |"
        m_rcs = re.search(r"([^|]{3,60}?)\s*\|\s*Numéro RCS\s*:\s*(\d{9})", visible)
        m_cp = re.search(r"Numéro RCS[^|]*\|(?:[^|]*\|){0,4}?\s*(\d{5})\s+([^|]+?)\s*\|", visible)
        m_ag = re.search(r"Numéro RCS[^|]*\|\s*[^|]+\|\s*([^|]+?)\s*\|", visible)
        tel = choisir_telephone(re.findall(r'Tél mobile\s*:\s*<a href="tel:([^"]+)"', f), set())
        prenom, nom = separer_nom(nom_complet)
        cp = m_cp.group(1) if m_cp else "42000"
        fonction = m_rcs.group(1).strip() if m_rcs else (titre.split(" à ")[0].strip() if " à " in titre else None)
        enregistrer_fiche(con, "42avenue", url.rsplit("/", 1)[-1].removesuffix(".php"), url=url, prenom=prenom, nom=nom,
                          fonction=fonction, siren=m_rcs.group(2) if m_rcs else None,
                          agence=m_ag.group(1) if m_ag else "42ème Avenue", commune=m_cp.group(2).title() if m_cp else "Saint-Étienne",
                          code_postal=cp, departement=departement_de(cp), fiche_lue=1, telephone=tel,
                          source_contact="fiche 42eme Avenue : mobile affiche" if tel else None)
    return compter_fin("42avenue", con)


# ---- LA MANUFACTURE DE L'IMMO (Saint-Etienne, Saint-Just-Malmont) -----------------------------
MANU = "https://www.lamanufacturedelimmo.fr"


def cmd_manufacture(con, lecteur, args) -> int:
    t = lire(lecteur, f"{MANU}/agent-sitemap.xml", "manufacture")
    urls = sorted(set(re.findall(r"<loc>(https://www\.lamanufacturedelimmo\.fr/agent/[^<]+/)</loc>", t or "")))
    journal("manufacture", f"{len(urls)} fiches dans le plan de site")
    for n, url in enumerate(urls, 1):
        if args.limite and n > args.limite:
            break
        f = lire(lecteur, url, "manufacture")
        if not f:
            continue
        corps = f[:f.find("<footer")] if "<footer" in f else f
        nom_complet = texte_de((re.search(r"<h1[^>]*>(.*?)</h1>", corps, re.S) or [None, ""])[1])
        visible = texte_visible(corps)
        # « inscrit au RSAC de X sous le n°<SIRET> » ou « inscrit au RCS de X Sous le n° 999 999 999 »
        m_rsac = re.search(r"(?:RSAC|RCS) de ([A-Za-zÀ-ÿ' \-]+?) [Ss]ous le n°\s*(\d{3}\s?\d{3}\s?\d{3})", visible)
        m_f = re.search(re.escape(nom_complet) + r"\s+((?:Agent|Conseill|Négociat|Direct|Assist|Gestion)[^|]{0,60}?)\s+(?:Entrepreneur|Associé|Je parle|\d)", visible) if nom_complet else None
        prenom, nom = separer_nom(nom_complet)
        cle_nom = re.sub(r"[^a-z]", "", sans_accents(nom).lower())
        mails = [email_lisible(x) for x in re.findall(r'href="(mailto:[^"]+)"', corps)]
        mail = next((m for m in mails if m and cle_nom and cle_nom in re.sub(r"[^a-z]", "", m.split("@")[0])), None)
        tel = choisir_telephone([unquote(x) for x in re.findall(r'href="tel:([^"]+)"', corps)], set())
        sources = [s for s, v in (("fiche La Manufacture : telephone affiche", tel), ("fiche La Manufacture : e-mail affiche", mail)) if v]
        enregistrer_fiche(con, "manufacture", url.rstrip("/").rsplit("/", 1)[-1], url=url, prenom=prenom, nom=nom,
                          fonction=m_f.group(1).strip() if m_f else None,
                          siren=siren_depuis_rsac(m_rsac.group(2)) if m_rsac else None,
                          rsac_ville=m_rsac.group(1).strip() if m_rsac else None, agence="La Manufacture de l'Immo",
                          commune="Saint-Étienne", code_postal="42000", departement="42", fiche_lue=1,
                          telephone=tel, email=mail, source_contact=" + ".join(sources) or None)
    return compter_fin("manufacture", con)


# ---- outils communs du 2e lot -----------------------------------------------------------------
def deja_lue_aujourdhui(con, url) -> bool:
    """Page deja lue (HTTP 200) PENDANT LA COLLECTE EN COURS ; hors collecte (relecture `-Source`), aujourd'hui.
    ⚠ 24/11 : c'etait « aujourd'hui » dans tous les cas -- une page lue le matin (un essai) n'etait pas relue par
    la collecte ouverte l'apres-midi, et ses fiches n'y etaient pas VUES. Le nom est garde (4 lecteurs l'appellent)."""
    n = collecte_ouverte(con)
    debut = con.execute("select debut from collecte where numero=?", (n,)).fetchone() if n else None
    if debut and debut[0]:
        r = con.execute("select statut_http from page_lue where url=? and lu_le >= ?", (url, debut[0])).fetchone()
    else:
        r = con.execute("select statut_http from page_lue where url=? and substr(lu_le,1,10)=?", (url, aujourdhui())).fetchone()
    return bool(r and r["statut_http"] == 200)


def sources_contact(nom_source: str, tel, mail) -> str | None:
    s = [x for x, v in ((f"{nom_source} : telephone affiche", tel), (f"{nom_source} : e-mail affiche", mail)) if v]
    return " + ".join(s) or None


def siren_depuis_siret(v) -> str | None:
    chiffres = re.sub(r"\D", "", str(v or ""))
    return chiffres[:9] if len(chiffres) in (9, 14) else None


def dans_la_region(cp) -> str | None:
    dep = departement_de(str(cp or "").strip())
    return dep if dep in DEPARTEMENTS else None


# ---- CAPIFRANCE et OPTIMHOME (meme plateforme : pages par ville, JSON-LD par conseiller) -------
PLATEFORME_CAPI = {"capifrance": "https://www.capifrance.fr", "optimhome": "https://www.optimhome.com"}


def cmd_capi_optim(reseau: str, con, lecteur, args) -> int:
    base = PLATEFORME_CAPI[reseau]
    nom_source = {"capifrance": "page ville Capifrance", "optimhome": "page ville Optimhome"}[reseau]
    t = lire(lecteur, f"{base}/sitemap/content/conseillers", reseau) or ""
    villes = [u for u in re.findall(r"<loc>([^<]+/fr/conseillers/[^<]+)</loc>", t)
              if re.search(r"_(%s)/?$" % "|".join(DEPARTEMENTS), u)]
    journal(reseau, f"{len(villes)} pages ville dans la region (plan de site)")
    for n, url in enumerate(villes, 1):
        if args.limite and n > args.limite:
            break
        if deja_lue_aujourdhui(con, url) and not args.relire:
            continue
        p = lire(lecteur, url, reseau)
        noter_page(con, url, reseau, 200 if p else 0)
        if not p:
            continue
        agents = [b for b in json_ld(p) if isinstance(b, dict) and "RealEstateAgent" in str(b.get("@type")) and b.get("url")]
        for b in agents:
            adr = b.get("address") or {}
            dep = dans_la_region(adr.get("postalCode"))
            if not dep:
                continue
            hote = urlsplit(b["url"]).netloc
            # dans la CARTE du conseiller : le bouton « contact » de son mini-site, puis le lien d'appel
            m_contact = re.search(re.escape(f'href="https://{hote}/') + r'(?:fr/)?contact"', p)  # Capifrance : /fr/contact ; Optimhome : /contact
            fenetre = p[m_contact.start():m_contact.start() + 2500] if m_contact else ""
            m_tel = re.search(r'href="tel:([^"]+)"', fenetre)
            tel = telephone_lisible(m_tel.group(1)) if m_tel else None
            mail = email_lisible(b.get("email"))
            note = b.get("aggregateRating") or {}
            prenom, nom = separer_nom(b.get("name") or "")
            enregistrer_fiche(con, reseau, hote.split(".")[0], url=b["url"], prenom=prenom, nom=nom,
                              commune=adr.get("addressLocality"), code_postal=adr.get("postalCode"), departement=dep,
                              siren=siren_depuis_siret(b.get("iso6523Code")), nb_avis=note.get("ratingCount"),
                              note_avis=_flottant(note.get("ratingValue")), fiche_lue=1, telephone=tel, email=mail,
                              source_contact=sources_contact(nom_source, tel, mail))
        if n % 10 == 0:
            journal(reseau, f"{n}/{len(villes)} pages ville")
    return compter_fin(reseau, con)


# ---- BSK IMMOBILIER (API publique de la page « conseillers ») ---------------------------------
BSK = "https://bskimmobilier.com"


def cmd_bsk(con, lecteur, args) -> int:
    for dep in DEPARTEMENTS:
        page = 1
        while True:
            url = (f"{BSK}/api/agent/search?location[type]=department&location[value]={dep}"
                   f"&sort=created_at&page[size]=24&page[number]={page}")
            r = lecteur.get(url, "bsk", {"Accept": "application/json"})
            if r.status_code != 200:
                journal("bsk", f"⚠ HTTP {r.status_code} departement {dep}")
                break
            d = r.json()
            for a in d.get("data") or []:
                ville = a.get("addressCity") or {}
                dep_a = dans_la_region(ville.get("zipCode"))
                if not dep_a:
                    continue
                tel, mail = telephone_lisible(a.get("phone")), email_lisible(a.get("email"))
                enregistrer_fiche(con, "bsk", str(a["id"]), url=a.get("url"), prenom=(a.get("firstName") or "").strip(),
                                  nom=(a.get("lastName") or "").strip(), commune=ville.get("name"),
                                  code_postal=ville.get("zipCode"), departement=dep_a, lat=_flottant(ville.get("latitude")),
                                  lon=_flottant(ville.get("longitude")), siren=siren_depuis_siret(a.get("rsacNumber")),
                                  rsac_ville=(a.get("rsacCity") or {}).get("name"), nb_annonces=a.get("adsCount"),
                                  nb_avis=(a.get("metaReviews") or {}).get("total"), fiche_lue=1, telephone=tel, email=mail,
                                  source_contact=sources_contact("annuaire BSK", tel, mail))
            meta = d.get("meta") or {}
            journal("bsk", f"departement {dep} page {page}/{meta.get('last_page')} : {meta.get('total')} conseillers")
            if page >= (meta.get("last_page") or 1):
                break
            page += 1
    return compter_fin("bsk", con)


# ---- MEGAGENCE (la page « nos consultants » charge tout le reseau en un JSON) ------------------
MEGA = "https://www.megagence.com"


def cmd_megagence(con, lecteur, args) -> int:
    r = lecteur.get(f"{MEGA}/nos-consultants/search?name=", "megagence", {"X-Requested-With": "XMLHttpRequest"})
    if r.status_code != 200:
        journal("megagence", f"⚠ HTTP {r.status_code}")
        return CODE_ERREUR
    d = r.json()
    journal("megagence", f"{d.get('total')} consultants dans le reseau")
    for a in d.get("data") or []:
        dep = dans_la_region(a.get("cp"))
        if not dep:
            continue
        m_url = re.search(r'href="([^"]*/votre-consultant/[^"]+)"', a.get("html") or "")
        url = m_url.group(1) if m_url else f"{MEGA}/nos-consultants"
        url = url if url.startswith("http") else MEGA + url
        tel = telephone_lisible(a.get("telephone"))
        enregistrer_fiche(con, "megagence", str(a["id_contact"]), url=url, prenom=(a.get("prenom") or "").strip(),
                          nom=(a.get("nom") or "").strip(), commune=a.get("ville"), code_postal=a.get("cp"),
                          departement=dep, lat=_flottant(a.get("latitude")), lon=_flottant(a.get("longitude")),
                          fiche_lue=1, telephone=tel, source_contact=sources_contact("annuaire Megagence", tel, None))
    return compter_fin("megagence", con)


# ---- EXPERTIMO (l'annuaire est sur reseau-expertimo.fr ; la carte charge tout le reseau) ------
REXP = "https://www.reseau-expertimo.fr"
REXP_EXCLUS = {"462"}  # robots.txt : « Disallow: /462-mandataire/ » -> cette personne n'est PAS gardee


def cmd_expertimo(con, lecteur, args) -> int:
    r = lecteur.get(f"{REXP}/i/JsonMap/agences", "expertimo")
    if r.status_code != 200:
        journal("expertimo", f"⚠ HTTP {r.status_code}")
        return CODE_ERREUR
    marqueurs = r.json().get("markers") or []
    journal("expertimo", f"{len(marqueurs)} entrees dans la carte du reseau")
    for m in marqueurs:
        a = m.get("data") or {}
        if a.get("type") != "MANDATAIRE" or str(a.get("id")) in REXP_EXCLUS:
            continue
        dep = dans_la_region(a.get("cp"))
        if not dep:
            continue
        tel, mail = telephone_lisible(a.get("tel")), email_lisible(a.get("mail"))
        enregistrer_fiche(con, "expertimo", str(a["id"]), url=f"{REXP}/{a['id']}-mandataire/1",
                          prenom=(a.get("prenom") or "").strip(), nom=(a.get("nom") or "").strip(),
                          commune=a.get("ville"), code_postal=a.get("cp"), departement=dep,
                          lat=_flottant(m.get("lat")), lon=_flottant(m.get("lng")), fiche_lue=1, telephone=tel, email=mail,
                          source_contact=sources_contact("carte Expertimo", tel, mail))
    return compter_fin("expertimo", con)


# ---- DR HOUSE IMMO (114 pages de liste ; un JSON-LD par conseiller ; puis la fiche pour le RSAC) -
DRH = "https://www.drhouse-immo.com"


def cmd_drhouse(con, lecteur, args) -> int:
    page, derniere = 1, None
    while True:
        url = f"{DRH}/conseillers-immobiliers?page={page}"
        if not (deja_lue_aujourdhui(con, url) and not args.relire):
            p = lire(lecteur, url, "drhouse")
            noter_page(con, url, "drhouse", 200 if p else 0)
            if p:
                if derniere is None:
                    derniere = max([int(x) for x in re.findall(r"conseillers-immobiliers\?page=(\d+)", p)] or [1])
                for b in json_ld(p):
                    if not (isinstance(b, dict) and "RealEstateAgent" in str(b.get("@type")) and b.get("url")):
                        continue
                    adr = b.get("address") or {}
                    # le JSON-LD ne donne que le DEPARTEMENT (2 chiffres) : le code postal est dans l'adresse de la fiche
                    m_cp = re.search(r"/conseiller-immobilier/[^/]*-(\d{5})/", b["url"])
                    cp = m_cp.group(1) if m_cp else None
                    # le code postal de l'adresse fait foi ; les 2 chiffres du JSON-LD seulement s'il n'y en a pas
                    dep = dans_la_region(cp) if cp else (str(adr.get("postalCode")) if str(adr.get("postalCode")) in DEPARTEMENTS else None)
                    if not dep or re.match(r"(?i)agence\b", b.get("name") or ""):
                        continue  # hors region, ou une fiche d'AGENCE (pas une personne)
                    tel, mail = telephone_lisible(b.get("telephone")), email_lisible(b.get("email"))
                    note = b.get("aggregateRating") or {}
                    prenom, nom = separer_nom(b.get("name") or "")
                    enregistrer_fiche(con, "drhouse", b["url"].rstrip("/").rsplit("/", 1)[-1] + "/" + (cp or dep),
                                      url=b["url"], prenom=prenom, nom=nom, commune=adr.get("addressLocality"),
                                      code_postal=cp, departement=dep, nb_avis=note.get("reviewCount"),
                                      note_avis=_flottant(note.get("ratingValue")), telephone=tel, email=mail,
                                      source_contact=sources_contact("annuaire Dr House", tel, mail))
        derniere = derniere or max([int(x) for x in re.findall(r"page=(\d+)", " ".join(
            r[0] for r in con.execute("select url from page_lue where reseau='drhouse'")))] or [114])
        if page % 20 == 0:
            journal("drhouse", f"page {page}/{derniere}")
        if page >= derniere or (args.limite and page >= args.limite):
            break
        page += 1
    # la fiche de chaque conseiller de la region : le RSAC
    for f in con.execute("select identifiant, url from fiche where reseau='drhouse' and fiche_lue=0").fetchall():
        p = lire(lecteur, f["url"], "drhouse")
        if not p:
            continue
        v = texte_visible(p)  # « Entreprise individuelle, Agent commercial 999999999 RSAC <ville ou n°> »
        m = re.search(r"Agent commercial\s*(\d{3}\s?\d{3}\s?\d{3})", v)
        mv = re.search(r"Agent commercial\s*[\d\s]+RSAC\s+(?:de\s+)?([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' \-]{1,40}?)\s+(?:À propos|[A-Z][a-z])", v)
        enregistrer_fiche(con, "drhouse", f["identifiant"], siren=siren_depuis_rsac(m.group(1)) if m else None,
                          rsac_ville=mv.group(1).strip() if mv else None, fiche_lue=1)
    return compter_fin("drhouse", con)


# ---- 3G IMMO (une carte GeoJSON du reseau ; puis le mini-site pour le RSAC et les annonces) ----
G3 = "https://3gimmo.com"
BOITE_REGION = (44.2, 46.35, 2.35, 4.95)  # lat min, lat max, lon min, lon max des 4 departements


def cmd_3g(con, lecteur, args) -> int:
    r = lecteur.get(f"{G3}/resultCRONS/agents_site.geojson", "3g")
    if r.status_code != 200:
        journal("3g", f"⚠ HTTP {r.status_code}")
        return CODE_ERREUR
    points = r.json().get("features") or []
    dans_boite = [f for f in points if (f.get("geometry") or {}).get("coordinates")
                  and BOITE_REGION[0] <= f["geometry"]["coordinates"][1] <= BOITE_REGION[1]
                  and BOITE_REGION[2] <= f["geometry"]["coordinates"][0] <= BOITE_REGION[3]]
    journal("3g", f"{len(points)} conseillers sur la carte, {len(dans_boite)} dans le cadre de la region")
    for n, f in enumerate(dans_boite, 1):
        if args.limite and n > args.limite:
            break
        pr = f.get("properties") or {}
        ident = str(pr.get("id"))
        if con.execute("select 1 from fiche where reseau='3g' and identifiant=? and fiche_lue=1", (ident,)).fetchone() and not args.relire:
            continue
        lon, lat = f["geometry"]["coordinates"][:2]
        g = lecteur.get(f"https://geo.api.gouv.fr/communes?lat={lat}&lon={lon}&fields=nom,codesPostaux,codeDepartement&format=json", "3g")
        commune = (g.json() or [{}])[0] if g.status_code == 200 else {}
        dep = commune.get("codeDepartement")
        if dep not in DEPARTEMENTS:
            continue
        url = f"{G3}/{pr.get('site')}" if pr.get("site") else f"{G3}/votre-conseiller"
        tel = telephone_lisible(pr.get("tel"))
        siren = rsac_ville = nb_annonces = None
        if pr.get("site"):
            p = lire(lecteur, url, "3g") or ""
            m = re.search(r'id="textRSAC"[^>]*>(.*?)</p>', p, re.S)
            if m:
                txt = texte_de(m.group(1))
                siren = siren_depuis_rsac(txt)
                mv = re.search(r"RSAC de\s+([A-Za-zÀ-ÿ' \-]+?)\s+\d", txt)
                rsac_ville = mv.group(1) if mv else None
            nb_annonces = next((b.get("numberOfItems") for b in json_ld(p) if isinstance(b, dict) and b.get("@type") == "ItemList"), None)
            # ⛔ l'e-mail est dans un champ CACHE de la page (affiche seulement par un appel au clic) : non lu
        prenom, nom = separer_nom(pr.get("name") or "")
        cps = commune.get("codesPostaux") or []
        enregistrer_fiche(con, "3g", ident, url=url, prenom=prenom, nom=nom, commune=commune.get("nom"),
                          code_postal=cps[0] if cps else None, departement=dep, lat=lat, lon=lon, siren=siren,
                          rsac_ville=rsac_ville, nb_annonces=nb_annonces, fiche_lue=1, telephone=tel,
                          source_contact=sources_contact("carte 3G Immo", tel, None))
    return compter_fin("3g", con)


# ---- LF IMMO (ex-Lafourmi : le plan de site des conseillers porte le code postal) ------------
LF = "https://www.lfimmo.fr"


def cmd_lfimmo(con, lecteur, args) -> int:
    import gzip
    r = lecteur.get(f"{LF}/data/sitemaps/1/sitemap.xml.gz", "lfimmo")
    index = gzip.decompress(r.content).decode("utf-8", "replace") if r.content[:2] == b"\x1f\x8b" else r.text
    m = re.search(r"<loc>([^<]*agents[^<]*\.xml(?:\.gz)?)</loc>", index)
    if not m:
        journal("lfimmo", "⚠ pas de plan de site des conseillers")
        return CODE_ERREUR
    r = lecteur.get(m.group(1), "lfimmo")
    xml = gzip.decompress(r.content).decode("utf-8", "replace") if r.content[:2] == b"\x1f\x8b" else r.text
    urls = [u for u in re.findall(r"<loc>([^<]+/agents/[^<]+)</loc>", xml) if dans_la_region(u.rstrip("/")[-5:])]
    journal("lfimmo", f"{len(urls)} conseillers de la region dans le plan de site")
    for url in urls:
        p = lire(lecteur, url, "lfimmo")
        if not p:
            continue
        v = texte_visible(p)
        m_r = re.search(r"RSAC de\s+([A-Za-zÀ-ÿ' \-]+?)\s+sous le n°\s*(\d[\d\s]{8,12})", v)
        m_v = re.search(r"(\d+)\s+biens? à vendre", v)
        m_a = re.search(r"([\d,.]+)\s*/\s*5 sur un total de (\d+) avis", v)
        nom_complet = texte_de((re.search(r"<h1[^>]*>(.*?)</h1>", p, re.S) or [None, ""])[1])
        prenom, nom = separer_nom(nom_complet)
        cle_nom = re.sub(r"[^a-z]", "", sans_accents(nom).lower())
        mails = re.findall(r"[a-z0-9.\-]+@lfimmo\.fr", v.lower())
        mail = next((x for x in mails if cle_nom and cle_nom in re.sub(r"[^a-z]", "", x.split("@")[0])), None)
        tel = choisir_telephone(re.findall(r'href="tel:([^"]+)"', p), set())
        cp = url.rstrip("/")[-5:]
        commune = re.sub(r"-\d{5}$", "", url.rstrip("/").rsplit("/", 1)[-1]).split("-")[-1].title()
        enregistrer_fiche(con, "lfimmo", url.rstrip("/").rsplit("/", 1)[-1].split("-")[0], url=url, prenom=prenom, nom=nom,
                          commune=commune, code_postal=cp, departement=dans_la_region(cp),
                          siren=siren_depuis_rsac(m_r.group(2)) if m_r else None, rsac_ville=m_r.group(1) if m_r else None,
                          nb_annonces=int(m_v.group(1)) if m_v else None, nb_avis=int(m_a.group(2)) if m_a else None,
                          note_avis=_flottant(m_a.group(1).replace(",", ".")) if m_a else None, fiche_lue=1,
                          telephone=tel, email=mail, source_contact=sources_contact("fiche LF immo", tel, mail))
    return compter_fin("lfimmo", con)


# ---- SEXTANT (la page « nos conseillers » embarque toute la carte en JSON) --------------------
SEXTANT = "https://www.sextantfrance.fr"


def cmd_sextant(con, lecteur, args) -> int:
    p = lire(lecteur, f"{SEXTANT}/contact/nos-conseillers-immobiliers/", "sextant") or ""
    m = re.search(r'<script[^>]*id="agentsMapData"[^>]*>(.*?)</script>', p, re.S)
    agents = json.loads(m.group(1)) if m else []
    agents = agents.get("agents", agents) if isinstance(agents, dict) else agents
    journal("sextant", f"{len(agents)} conseillers sur la carte")
    for a in agents:
        dep = dans_la_region(a.get("postcode"))
        if not dep:
            continue
        url = a.get("minisiteUrl") or f"{SEXTANT}/contact/nos-conseillers-immobiliers/"
        siren = rsac_ville = None
        if a.get("minisiteUrl"):
            mini = texte_visible(lire(lecteur, a["minisiteUrl"], "sextant") or "")
            m_num = re.search(r"RSAC\s*:\s*([\d\s  ]{9,22})", mini)
            m_ville = re.search(r"Ville du greffe\s*:\s*([A-ZÀ-Ü][A-ZÀ-Ü' \-]+)", mini)
            siren = siren_depuis_rsac(m_num.group(1)) if m_num else None
            rsac_ville = m_ville.group(1).strip()[:40] if m_ville else None
            if not siren:
                journal("sextant", f"⚠ RSAC non lu sur {a['minisiteUrl']}")
        tel = telephone_lisible(a.get("phone"))
        prenom, nom = separer_nom(a.get("name") or "")
        enregistrer_fiche(con, "sextant", str(a.get("id") or a.get("slug")), url=url, prenom=prenom, nom=nom,
                          commune=a.get("city"), code_postal=a.get("postcode"), departement=dep,
                          lat=_flottant(a.get("lat")), lon=_flottant(a.get("lng")), siren=siren, rsac_ville=rsac_ville,
                          fiche_lue=1, telephone=tel, source_contact=sources_contact("carte Sextant", tel, None))
    return compter_fin("sextant", con)


# ---- COTE PARTICULIERS (reseau d'agences : l'equipe sur le site de chaque agence) -------------
COTEP = "https://www.coteparticuliers.com"


def cmd_cotepart(con, lecteur, args) -> int:
    p = lire(lecteur, f"{COTEP}/agences", "cotepart") or ""
    cartes = p.split('class="card__content"')[1:]
    retenues = []
    for c in cartes:
        m_site = re.search(r'href="(https://[a-z0-9\-]+\.coteparticuliers\.com)"', c)
        m_cp = re.search(r'card__adresse[^>]*>\s*(\d{5})\s+([^<]+)<', c)
        if m_site and m_cp and dans_la_region(m_cp.group(1)):
            retenues.append((m_site.group(1), m_cp.group(1), m_cp.group(2).strip()))
    journal("cotepart", f"{len(cartes)} agences, {len(retenues)} dans la region")
    for site, cp, ville in retenues:
        t = lire(lecteur, site + "/", "cotepart") or ""
        for b in t.split('class="collaborateur"')[1:]:
            m_nom = re.search(r'collaborateur__name[^>]*>(.*?)</p>', b, re.S)
            if not m_nom:
                continue
            nom_complet = texte_de(m_nom.group(1))
            mail = email_lisible((re.search(r'href="(mailto:[^"]+)"', b) or [None, None])[1])
            tel = choisir_telephone(re.findall(r'(?:data-phone="|href="tel:)([^"]+)"', b), set())
            prenom, nom = separer_nom(nom_complet)
            enregistrer_fiche(con, "cotepart", f"{site.split('//')[1].split('.')[0]}/{cle_personne(nom_complet)}", url=site,
                              prenom=prenom, nom=nom, agence=f"Côté Particuliers {ville}", commune=ville, code_postal=cp,
                              departement=dans_la_region(cp), fiche_lue=1, telephone=tel, email=mail,
                              source_contact=sources_contact("site agence Cote Particuliers", tel, mail))
    return compter_fin("cotepart", con)


# ---- EXP FRANCE (annuaire national pagine ; la commune ne s'y trouve pas -> par le SIREN) -----
EXP = "https://www.expfrance.fr"


def cmd_exp(con, lecteur, args) -> int:
    page, derniere, vus = 1, 1, 0
    while page <= derniere:
        p = lire(lecteur, f"{EXP}/findanagent?page={page}", "exp") or ""
        flux = ""
        for s in re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', p, re.S):
            try:
                flux += json.loads('"' + s + '"')
            except json.JSONDecodeError:
                continue
        objets = re.findall(r'\{"id":"[0-9a-f\-]{36}","name":.*?"licence_number":(?:"[^"]*"|null)[^{}]*\}', flux)
        for o in objets:
            try:
                a = json.loads(o)
            except json.JSONDecodeError:
                continue
            tel, mail = telephone_lisible(a.get("phone")), email_lisible(a.get("email"))
            prenom, nom = separer_nom(a.get("name") or "")
            # departement INCONNU ici : la commande `siren` le pose par le siege, puis retire le hors region
            enregistrer_fiche(con, "exp", a["id"], url=a.get("microsite") or f"{EXP}/findanagent", prenom=prenom, nom=nom,
                              siren=siren_depuis_siret(a.get("licence_number")), fiche_lue=1, telephone=tel, email=mail,
                              source_contact=sources_contact("annuaire eXp", tel, mail))
            vus += 1
        m_total = re.search(r"(\d[\d\s]*)\s*eXpairs", texte_visible(p))
        if page == 1 and m_total:
            derniere = -(-int(re.sub(r"\D", "", m_total.group(1))) // 40)
        if args.limite and page >= args.limite:
            break
        page += 1
    journal("exp", f"{vus} conseillers lus sur {page} pages (France entiere ; la region viendra du SIREN)")
    return CODE_FINI


# ============================================================================================
# R1 -- LES SOURCES DU 20/11 AU SOIR (note §10 et §14). Sondees le 20/11 : robots.txt lu, une
# requete a la fois. Ecartees, et pourquoi (note §10) : Square Habitat (agences seulement, aucune
# personne), Guy Hoquet (l'annuaire passe par le service d'un tiers), Immonial (plus de site),
# Proprietes-privees (aucune connexion, 2e essai).
# ============================================================================================

def _cle_nom(prenom: str | None, nom: str | None) -> str:
    """Prenom + nom, sans accents ni ordre : « Marie DURAND » == « DURAND Marie »."""
    return "-".join(sorted(cle_personne(f"{prenom or ''} {nom or ''}").split("-")))


# ---- GROUPEMENT IMMOBILIER (une page par departement, puis la fiche de chaque mandataire) -----
GROUPEMENT = "https://www.groupementimmo.fr"


def cmd_groupement(con, lecteur, args) -> int:
    p = lire(lecteur, f"{GROUPEMENT}/mandataires/1", "groupement") or ""
    # la carte donne le lien de chaque departement (identifiant INTERNE, pas le numero INSEE)
    pages = {m.group(2): m.group(1) for m in re.finditer(r'data-target="(/mandataires/dep-\d+/1)" id="departement(\d+)"', p)}
    pages = {d: u for d, u in pages.items() if d in DEPARTEMENTS}
    journal("groupement", f"pages departement de la region : {sorted(pages)}")
    for dep, chemin in sorted(pages.items()):
        liste = lire(lecteur, GROUPEMENT + chemin, "groupement") or ""
        for fiche in sorted(set(re.findall(r'href="(/(\d+)-mandataire/1)"', liste))):
            url = GROUPEMENT + fiche[0]
            f = lire(lecteur, url, "groupement")
            noter_page(con, url, "groupement", 200 if f else 0)
            if not f:
                continue
            # le standard et l'adresse du RESEAU sont dans le JSON-LD : ils sont ecartes
            reseau_tel = {telephone_lisible(b.get("telephone")) for b in json_ld(f) if isinstance(b, dict)}
            bloc = texte_de(f)
            # la DERNIERE mention « Mandataire <commune> (<CP>) <telephone> » est la carte de la personne
            lieux = list(re.finditer(r"Mandataire\s+((?:(?!Mandataire)[^()])+?)\s*\((\d{5})\)\s*((?:0\d(?:\s?\d{2}){4})?)", bloc))
            m = lieux[-1] if lieux else None
            if not m or not dans_la_region(m.group(2)):
                continue
            # le nom : le bloc « Service » du JSON-LD, « Prenom NOM | Agent mandataire chez [X] »
            service = next((b for b in json_ld(f) if isinstance(b, dict) and b.get("@type") == "Service"), {})
            prenom, nom = separer_nom((service.get("name") or "").split("|")[0].strip())
            if not nom:
                continue
            tel = choisir_telephone([m.group(3)], reseau_tel)
            mails = [email_lisible(x) for x in re.findall(r'href="mailto:([^"]+)"', f)]
            mail = next((x for x in mails if x and not x.startswith("contact@")), None)
            pos = con.execute("select lat, lon from commune where cle=?", (cle_commune(m.group(1)),)).fetchone()
            enregistrer_fiche(con, "groupement", fiche[1], url=url, prenom=prenom, nom=nom, commune=m.group(1).strip(),
                              code_postal=m.group(2), departement=dans_la_region(m.group(2)), fonction="Mandataire",
                              lat=pos["lat"] if pos else None, lon=pos["lon"] if pos else None,
                              fiche_lue=1, telephone=tel, email=mail,
                              source_contact=sources_contact("fiche Groupement Immobilier", tel, mail))
    return compter_fin("groupement", con)


# ---- IMMO-DIFFUSION (une page par departement ; la fiche ne donne parfois aucun numero) -------
IMMODIF = "https://www.immo-diffusion.fr"
IMMODIF_DEPARTEMENTS = {"42": "rhone-alpes/loire", "07": "rhone-alpes/ardeche",
                        "63": "auvergne/puy-de-dome", "43": "auvergne/haute-loire"}
RX_TEL_TEXTE = re.compile(r"(?<!\d)0[1-9](?:[ .]?\d{2}){4}(?!\d)")


def cmd_immodiffusion(con, lecteur, args) -> int:
    for dep, chemin in IMMODIF_DEPARTEMENTS.items():
        liste = lire(lecteur, f"{IMMODIF}/fr/{chemin}/agents-immobiliers", "immodiffusion") or ""
        agents = re.findall(r'<a[^>]+href="(/fr/agent-immobilier/(\d+))"[^>]*>(.*?)</a>', liste, re.S)
        journal("immodiffusion", f"departement {dep} : {len(agents)} agents")
        for chemin_fiche, ident, carte in agents:
            m = re.search(r"Agent (?:immobilier|commercial)", texte_de(carte))
            fonction = m.group(0) if m else None
            url = IMMODIF + chemin_fiche
            if deja_lue_aujourdhui(con, url) and not args.relire:
                continue
            f = lire(lecteur, url, "immodiffusion")
            noter_page(con, url, "immodiffusion", 200 if f else 0)
            if not f:
                continue
            # le titre porte la commune, le nom et le departement : « Agent immobilier COMMUNE : Prenom Nom Agent Immo-Diffusion 42 »
            t = re.search(r"<title>\s*(Agent (?:immobilier|commercial))?\s*(.*?)\s*:\s*(.*?)\s+Agent Immo-Diffusion\s+(\d{2}|2[AB])", f, re.S)
            if not t or t.group(4) != dep:
                continue
            commune, nom_complet = texte_de(t.group(2)), texte_de(t.group(3))
            if "ARCHIVE" in nom_complet.upper():
                continue  # « Agent ARCHIVE … » : une fiche d'agence fermee, pas une personne
            prenom, nom = separer_nom(nom_complet)
            pos = con.execute("select cp, lat, lon from commune where cle=? and dep=?", (cle_commune(commune), dep)).fetchone()
            tel = choisir_telephone(RX_TEL_TEXTE.findall(texte_visible(f)), set())
            enregistrer_fiche(con, "immodiffusion", ident, url=url, prenom=prenom, nom=nom, commune=commune.title(),
                              code_postal=pos["cp"] if pos else None, departement=dep,
                              lat=pos["lat"] if pos else None, lon=pos["lon"] if pos else None,
                              fonction=fonction or (t.group(1) or None), fiche_lue=1, telephone=tel,
                              source_contact=sources_contact("fiche Immo-Diffusion", tel, None))
    return compter_fin("immodiffusion", con)


# ---- A LA LUCARNE (le formulaire « ou recherchez-vous ? » par departement ; le numero est pris
#      sur la FICHE PUBLIQUE du conseiller, jamais dans la reponse du formulaire) ---------------
LUCARNE = "https://www.alalucarne.com"
LUCARNE_NOMS = {"07": " Ardèche", "42": " Loire", "43": " Haute-Loire", "63": " Puy-de-Dôme"}


def cmd_lucarne(con, lecteur, args) -> int:
    for dep in DEPARTEMENTS:
        r = lecteur.post(f"{LUCARNE}/agents/rechercheDpt.php", "lucarne",
                         {"dpt": dep, "name": LUCARNE_NOMS[dep], "pageHonoraires": ""},
                         {"Referer": f"{LUCARNE}/trouver-un-conseiller/"})
        if r.status_code != 200:
            journal("lucarne", f"⚠ HTTP {r.status_code} departement {dep}")
            continue
        # une carte = <div class="card"> : le nom (h6 card-title), « CP <b> COMMUNE</b> », le lien de la fiche
        cartes = re.split(r'<div class="card"', r.text)[1:]
        journal("lucarne", f"departement {dep} : {len(cartes)} conseiller(s)")
        for c in cartes:
            m_id = re.search(r'href="/conseiller/\?conseiller=(\d+)"', c)
            m_nom = re.search(r'<h6 class="card-title"><b>(.*?)</b></h6>', c, re.S)
            m_lieu = re.search(r"card-subtitle[^>]*>\s*(\d{5})\s*<b>(.*?)</b>", c, re.S)
            if not (m_id and m_nom and m_lieu) or dans_la_region(m_lieu.group(1)) != dep:
                continue
            ident, nom_complet = m_id.group(1), texte_de(m_nom.group(1))
            cp, commune = m_lieu.group(1), texte_de(m_lieu.group(2))
            url = f"{LUCARNE}/conseiller/?conseiller={ident}"
            f = lire(lecteur, url, "lucarne") or ""
            noter_page(con, url, "lucarne", 200 if f else 0)
            nums = re.findall(r"\+33\s?\(0\)\s?([1-9](?:[ .]?\d{2}){4})", texte_visible(f))
            tel = choisir_telephone(["0" + re.sub(r"\D", "", n) for n in nums], set())
            prenom, nom = separer_nom(nom_complet)
            pos = con.execute("select lat, lon from commune where cle=? and dep=?", (cle_commune(commune), dep)).fetchone()
            enregistrer_fiche(con, "lucarne", ident, url=url, prenom=prenom, nom=nom, commune=commune.title(),
                              code_postal=cp, departement=dep, fonction="Conseiller", lat=pos["lat"] if pos else None,
                              lon=pos["lon"] if pos else None, fiche_lue=1, telephone=tel,
                              source_contact=sources_contact("fiche publique Lucarne", tel, None))
    return compter_fin("lucarne", con)


# ---- LIBERKEYS (le plan du site liste tous les agents ; la fiche dit le departement du secteur) --
LIBERKEYS = "https://www.liberkeys.com"


def cmd_liberkeys(con, lecteur, args) -> int:
    plan = lire(lecteur, f"{LIBERKEYS}/sitemap.xml", "liberkeys") or ""
    agents = sorted(set(re.findall(r"<loc>(https://www\.liberkeys\.com/agents/[^<]+)</loc>", plan)))
    journal("liberkeys", f"{len(agents)} agents en France (plan du site) : on ne garde que la region")
    for n, url in enumerate(agents, 1):
        if args.limite and n > args.limite:
            break
        # MINIMISATION : l'adresse d'une fiche porte le NOM de l'agent. Pour un agent HORS region, on ne
        # garde que son EMPREINTE (pour reprendre une lecture coupee), jamais son adresse.
        empreinte = "empreinte:" + hashlib.sha1(url.encode()).hexdigest()[:16]
        if (deja_lue_aujourdhui(con, url) or deja_lue_aujourdhui(con, empreinte)) and not args.relire:
            continue
        f = lire(lecteur, url, "liberkeys")
        m = re.search(r"Secteur\s+(\d{2}|2[AB])\b", texte_visible(f)) if f else None
        dans_region = bool(m and m.group(1) in DEPARTEMENTS)
        noter_page(con, url if dans_region else empreinte, "liberkeys", 200 if f else 0)
        if not dans_region:
            continue
        titre = re.search(r"<title>\s*(.*?)\s+-\s+Agent Liberkeys", f, re.S)
        prenom, nom = separer_nom(texte_de(titre.group(1)) if titre else "")
        tel = choisir_telephone(re.findall(r'href="tel:([^"]+)"', f), set())
        mail = next((email_lisible(x) for x in re.findall(r'href="mailto:([^"]+)"', f) if "liberkeys.com" in x), None)
        enregistrer_fiche(con, "liberkeys", url.rsplit("/", 1)[-1], url=url, prenom=prenom, nom=nom,
                          departement=m.group(1), fonction="Mandataire immobilier", fiche_lue=1, telephone=tel, email=mail,
                          source_contact=sources_contact("fiche Liberkeys", tel, mail))
        if n % 50 == 0:
            journal("liberkeys", f"{n}/{len(agents)} fiches")
    return compter_fin("liberkeys", con)


# ---- MAXIHOME (une page : nom, e-mail, telephone ; AUCUNE commune nulle part) ------------------
# La personne n'est gardee que si le registre public la place dans la region : meme prenom et meme
# nom qu'UNE SEULE entreprise individuelle immobiliere (68.31Z) de la region, deja lue par la commande
# `registre` (donc jamais une personne en opposition). Homonyme ou rien trouve : la personne n'entre pas.
MAXIHOME = "https://www.maxihome.net"


def cmd_maxihome(con, lecteur, args) -> int:
    p = lire(lecteur, f"{MAXIHOME}/nos-mandataires.html", "maxihome") or ""
    cartes = re.findall(r"<a href='(https://www\.maxihome\.net/mandataire-immobilier-([^']+)\.html)'>(.*?)</a>", p, re.S)
    journal("maxihome", f"{len(cartes)} conseillers en France (aucune commune sur le site)")
    registre = {}
    for r in con.execute("select identifiant, prenom, nom, commune, code_postal, departement, lat, lon, siren "
                         "from fiche where reseau='registre'"):
        registre.setdefault(_cle_nom(r["prenom"], r["nom"]), []).append(r)
    places = homonymes = 0
    for url, slug, carte in cartes:
        titre = re.search(r"class='agence_titre'>\s*(.*?)\s*</div>", carte, re.S)
        prenom, nom = separer_nom(texte_de(titre.group(1)) if titre else "")
        candidats = registre.get(_cle_nom(prenom, nom), [])
        if len(candidats) != 1:
            homonymes += len(candidats) > 1
            continue
        reg = candidats[0]
        desc = re.search(r"class='agence_description'>(.*?)</div>", carte, re.S)
        bloc = desc.group(1) if desc else ""
        tel = telephone_lisible(texte_de(bloc.split("fa-phone")[-1])) if "fa-phone" in bloc else None
        mail = next((email_lisible(x) for x in re.findall(r"[\w.+\-]+@[\w\-]+\.[\w.]+", texte_de(bloc))), None)
        enregistrer_fiche(con, "maxihome", slug, url=url, prenom=prenom, nom=nom, commune=reg["commune"],
                          code_postal=reg["code_postal"], departement=reg["departement"], lat=reg["lat"], lon=reg["lon"],
                          siren=reg["siren"], fonction="Mandataire", fiche_lue=1, telephone=tel, email=mail,
                          source_contact=sources_contact("annuaire Maxihome", tel, mail))
        places += 1
    journal("maxihome", f"places par le registre : {places} · homonymes ecartes : {homonymes}")
    return compter_fin("maxihome", con)


# --------------------------------------------------------------------------------------------
# SIREN (API ouverte « Recherche d'entreprises ») + placement + MINIMISATION
# --------------------------------------------------------------------------------------------
def cmd_siren(con, lecteur, args) -> int:
    sirens = [r[0] for r in con.execute(
        "select distinct f.siren from fiche f left join entreprise e on e.siren=f.siren "
        "where f.siren is not null and (e.siren is null or ?)", (1 if args.relire else 0,))]
    journal("siren", f"SIREN a interroger : {len(sirens)}")
    for n, s in enumerate(sirens, 1):
        if args.limite and n > args.limite:
            break
        r = lecteur.get(f"https://recherche-entreprises.api.gouv.fr/search?q={s}&page=1&per_page=5", "siren")
        if r.status_code != 200:
            journal("siren", f"⚠ {s} : HTTP {r.status_code}")
            continue
        res = next((x for x in r.json().get("results") or [] if x.get("siren") == s), None)
        siege = (res or {}).get("siege") or {}
        opposition = 1 if (res or {}).get("opposition_diffusion_commerciale") else 0
        if opposition:
            # ⛔ La personne s'est OPPOSEE a l'usage commercial des donnees du registre : on ne garde
            # RIEN qui en vienne (ni creation, ni siege). Seulement le fait qu'elle s'y oppose.
            ligne = (s, 1, None, None, None, None, None, None, None, maintenant(), res.get("statut_diffusion"), 1)
        else:
            ligne = (s, 1 if res else 0, (res or {}).get("date_creation"), (res or {}).get("etat_administratif"),
                     (res or {}).get("activite_principale"), _diffusible(siege.get("code_postal")),
                     _diffusible(siege.get("libelle_commune")), _flottant(siege.get("latitude")),
                     _flottant(siege.get("longitude")), maintenant(), (res or {}).get("statut_diffusion"), 0)
        con.execute("insert or replace into entreprise values (?,?,?,?,?,?,?,?,?,?,?,?)", ligne)
        con.commit()
        if n % 50 == 0:
            journal("siren", f"{n}/{len(sirens)}")
    # KW : la fiche ne dit pas ou exerce le conseiller -> la commune du siege de son entreprise
    # (jamais pour une personne en opposition : ses donnees de registre ne sont pas gardees).
    # (meme chose pour eXp, dont l'annuaire ne donne pas la commune non plus)
    for f in con.execute("select f.reseau, f.identifiant, e.siege_cp, e.siege_commune, e.siege_lat, e.siege_lon "
                         "from fiche f join entreprise e on e.siren=f.siren "
                         "where f.departement is null and e.opposition=0").fetchall():
        cp, commune, lat, lon, dep = f["siege_cp"], f["siege_commune"], f["siege_lat"], f["siege_lon"], departement_de(f["siege_cp"])
        if not dep and commune:  # code postal non diffusible : la commune, si elle est UNIQUE dans la region
            lignes = con.execute("select * from commune where cle=?", (cle_commune(commune),)).fetchall()
            if len(lignes) == 1:
                cp, dep, lat, lon = lignes[0]["cp"], lignes[0]["dep"], lignes[0]["lat"], lignes[0]["lon"]
        enregistrer_fiche(con, f["reseau"], f["identifiant"], commune=commune, code_postal=cp, departement=dep, lat=lat, lon=lon)
    # MINIMISATION : on ne garde que la region. Ce qui est hors region, ou introuvable, est RETIRE.
    if args.limite:
        journal("siren", "essai (--limite) : pas de retrait hors region")
        return CODE_FINI
    reste_kw = con.execute("select count(*) from fiche where reseau='kw' and fiche_lue=0").fetchone()[0]
    if reste_kw:
        journal("siren", f"⚠ {reste_kw} fiches KW pas encore lues : pas de retrait (relancer `kw fiches`)")
        return CODE_A_REPRENDRE
    hors = con.execute("select reseau, count(*) n from fiche where departement is null or departement not in (%s) group by reseau"
                       % ",".join("?" * len(DEPARTEMENTS)), DEPARTEMENTS).fetchall()
    for h in hors:
        journal("siren", f"retrait hors region / sans localisation : {h['reseau']} {h['n']}")
    con.execute("delete from fiche where departement is null or departement not in (%s)" % ",".join("?" * len(DEPARTEMENTS)),
                DEPARTEMENTS)
    con.execute("delete from entreprise where siren not in (select siren from fiche where siren is not null)")
    con.commit()
    return CODE_FINI


def _flottant(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _diffusible(v):
    """« [NON-DIFFUSIBLE] » (diffusion partielle au registre) -> rien."""
    return None if not v or "DIFFUSIBLE" in str(v).upper() else v


# --------------------------------------------------------------------------------------------
# R2 -- LA MISE A JOUR : qui arrive, qui part, qui revient, qui change de reseau (note §13, R2)
# --------------------------------------------------------------------------------------------
SEUIL_SOURCE = 0.70          # une source qui rend moins de 70 % de ses fiches de la fois d'avant est MALADE
SOURCE_PETITE = 5            # en dessous, seul « aucune fiche lue » rend une source malade
SOURCE_TEMOINS = 10          # a partir de 10 fiches, 3 temoins : il en faut au moins 2 revus
ABSENCES_DEPART = 2          # « parti » : absent de 2 collectes de suite, source saine


def _evenement(con, n, reseau, identifiant, quoi, detail=None):
    con.execute("insert into evenement_fiche (le, collecte, reseau, identifiant, quoi, detail) values (?,?,?,?,?,?)",
                (maintenant(), n, reseau, identifiant, quoi, detail))


def cmd_collecte_ouvrir(con, lecteur, args) -> int:
    n = collecte_ouverte(con)
    if n:
        journal("collecte", f"la collecte n° {n} est deja ouverte : on la reprend")
        return CODE_FINI
    if not con.execute("select 1 from collecte").fetchone():
        journal("collecte", "⛔ aucune collecte n° 1 : lancer d'abord `collecte initiale`")
        return CODE_ERREUR
    n = con.execute("select max(numero) from collecte").fetchone()[0] + 1
    con.execute("insert into collecte (numero, debut, etat) values (?,?,'en_cours')", (n, maintenant()))
    # ⛔ 24/11, TROUVE PAR LE 1er PASSAGE COMPLET (collecte n° 2) : sans ces deux lignes, les marques « deja lu »
    #   de la collecte d'avant restaient posees -- SAFTI n'a rien relu (« pages a lire : 0, fiches a lire : 0 »),
    #   KW n'a pas relu ses 10 fiches de la region (ses temoins), 3G a saute ses 39 fiches : aucune n'a ete VUE,
    #   et les trois sources sont sorties MALADES. Une collecte neuve RELIT TOUT. (A la REPRISE d'une collecte
    #   deja ouverte -- coupure a 9 min --, on ne passe pas ici : les marques posees pendant elle sont gardees.)
    n_fiches = con.execute("update fiche set fiche_lue=0 where fiche_lue=1").rowcount
    n_grille = con.execute("update grille_safti set lue=0 where lue=1").rowcount
    con.commit()
    _CACHE["collecte"] = n
    journal("collecte", f"collecte n° {n} ouverte ; a relire : {n_fiches} fiches, {n_grille} communes SAFTI")
    return CODE_FINI


def cmd_collecte_initiale(con, lecteur, args) -> int:
    """R2.2 : la collecte du 20/11 devient la n° 1 -- la reference. Personne n'y est « nouveau »."""
    if con.execute("select 1 from collecte").fetchone():
        journal("collecte", "il y a deja des collectes : rien a faire")
        return CODE_FINI
    debut = con.execute("select min(premiere_vue) from fiche").fetchone()[0] or aujourdhui()
    con.execute("insert into collecte (numero, debut, fin, etat, note) values (1, ?, ?, 'finie', ?)",
                (debut, maintenant(), "reprise de la collecte du 20/11/2026 (pieces 1 et correction)"))
    con.execute("insert or ignore into observation (collecte, reseau, identifiant) select 1, reseau, identifiant from fiche")
    for r in con.execute("select reseau, count(*) n from fiche group by reseau").fetchall():
        con.execute("insert into source_etat (collecte, reseau, vus, precedent, sante, raison) values (1,?,?,null,'premiere',?)",
                    (r["reseau"], r["n"], "collecte de reference"))
    con.execute("update fiche set etat_suivi='present', etat_depuis=?, absences=0", (debut,))
    con.commit()
    journal("collecte", f"collecte n° 1 posee : {con.execute('select count(*) from observation').fetchone()[0]} observations")
    return CODE_FINI


def _temoins(con, reseau, n_prec) -> list[str]:
    """Les 3 fiches les plus anciennes de la source, vues a la collecte precedente : elles doivent revenir."""
    return [r[0] for r in con.execute(
        "select f.identifiant from fiche f join observation o on o.reseau=f.reseau and o.identifiant=f.identifiant "
        "where f.reseau=? and o.collecte=? order by f.premiere_vue, f.identifiant limit 3", (reseau, n_prec))]


def sante_source(vus: int, precedent: int | None, temoins_revus: int | None, nb_temoins: int) -> tuple[str, str]:
    if precedent is None:
        return "premiere", "pas de collecte precedente"
    if precedent > 0 and vus == 0:
        return "malade", f"aucune fiche lue (la fois d'avant : {precedent})"
    if precedent >= SOURCE_PETITE and vus < SEUIL_SOURCE * precedent:
        return "malade", f"{vus} fiches contre {precedent} la fois d'avant (moins de {SEUIL_SOURCE:.0%})"
    if precedent >= SOURCE_TEMOINS and nb_temoins >= 3 and (temoins_revus or 0) < 2:
        return "malade", f"temoins revus : {temoins_revus} sur {nb_temoins}"
    return "saine", f"{vus} fiches (la fois d'avant : {precedent})"


def cmd_maj(con, lecteur, args) -> int:
    n = collecte_ouverte(con)
    if not n:
        journal("maj", "⛔ aucune collecte ouverte : rien a comparer")
        return CODE_ERREUR
    r = con.execute("select max(numero) from collecte where numero < ? and etat='finie'", (n,)).fetchone()
    prec = r[0] if r else None
    jour = aujourdhui()
    sources = [x[0] for x in con.execute("select distinct reseau from observation where collecte in (?, ?)", (n, prec or -1))]
    sante = {}
    for reseau in sources:
        vus = con.execute("select count(*) from observation where collecte=? and reseau=?", (n, reseau)).fetchone()[0]
        precedent = con.execute("select count(*) from observation where collecte=? and reseau=?", (prec, reseau)).fetchone()[0] if prec else None
        tem = _temoins(con, reseau, prec) if prec else []
        revus = sum(1 for t in tem if con.execute("select 1 from observation where collecte=? and reseau=? and identifiant=?",
                                                  (n, reseau, t)).fetchone()) if tem else None
        s, raison = sante_source(vus, precedent, revus, len(tem))
        sante[reseau] = s
        con.execute("insert or replace into source_etat (collecte, reseau, vus, precedent, sante, raison) values (?,?,?,?,?,?)",
                    (n, reseau, vus, precedent, s, raison))
        journal("maj", f"{reseau:14} {s.upper():8} {raison}")
    vus_ici = {(x[0], x[1]) for x in con.execute("select reseau, identifiant from observation where collecte=?", (n,))}
    deja_vus = {(x[0], x[1]) for x in con.execute("select reseau, identifiant from observation where collecte<?", (n,))}
    comptes: dict[str, int] = {}
    partis_ici: list[tuple] = []  # ceux que CETTE collecte vient de rendre absents ou partis (jamais par la date)
    for f in con.execute("select reseau, identifiant, etat_suivi, absences, siren, url from fiche where reseau in (%s)"
                         % ",".join("?" * len(sources)), sources).fetchall():
        cle, ancien = (f["reseau"], f["identifiant"]), f["etat_suivi"]
        if cle in vus_ici:
            if cle not in deja_vus and prec:
                nouveau, motif = "nouveau", None
            elif ancien == "parti":
                nouveau, motif = "revenu", None
            else:
                nouveau, motif = "present", None
            absences = 0
        elif sante.get(f["reseau"]) == "malade":
            continue  # ⛔ LE GARDE-FOU : une source malade ne fait partir personne ; l'etat ne bouge pas
        else:
            absences = (f["absences"] or 0) + 1
            nouveau, motif = ("parti", f"absent de {absences} collectes de suite") if absences >= ABSENCES_DEPART else ("absent", None)
            if ancien == "parti":
                nouveau, motif = "parti", None  # deja parti : on n'ecrit rien de neuf
        if nouveau != ancien or (f["absences"] or 0) != absences:
            revu = nouveau in ("present", "revenu", "nouveau")
            sets = ("etat_suivi=?, absences=?" + (", etat_depuis=?" if nouveau != ancien else "")
                    + (", motif_depart=?" if motif or revu else ""))
            vals = [nouveau, absences] + ([jour] if nouveau != ancien else []) + ([motif] if motif or revu else [])
            con.execute(f"update fiche set {sets} where reseau=? and identifiant=?", (*vals, *cle))
            if nouveau != ancien:
                _evenement(con, n, *cle, nouveau, motif)
                comptes[nouveau] = comptes.get(nouveau, 0) + 1
                if nouveau in ("absent", "parti"):
                    partis_ici.append(cle)
    # A CHANGE DE RESEAU : devenu absent (ou parti) ICI, vu ailleurs a cette collecte sous le meme SIREN
    for cle in partis_ici:
        f = con.execute("select reseau, identifiant, siren from fiche where reseau=? and identifiant=?", cle).fetchone()
        if not f or not f["siren"]:
            continue
        ailleurs = [x[0] for x in con.execute("select f2.reseau from fiche f2 join observation o on o.reseau=f2.reseau "
                                              "and o.identifiant=f2.identifiant where f2.siren=? and f2.reseau<>? and o.collecte=?",
                                              (f["siren"], f["reseau"], n))]
        if ailleurs:
            motif = "a rejoint " + ", ".join(NOMS_RESEAUX.get(a, a) for a in sorted(set(ailleurs)))
            con.execute("update fiche set etat_suivi='parti', motif_depart=? where reseau=? and identifiant=?",
                        (motif, f["reseau"], f["identifiant"]))
            _evenement(con, n, f["reseau"], f["identifiant"], "change_de_reseau", motif)
            comptes["change_de_reseau"] = comptes.get("change_de_reseau", 0) + 1
    # LA PREUVE POSITIVE : la page d'un absent repond 404/410 -> parti tout de suite (au plus 50 par collecte)
    if not args.sans_reseau:
        absents_ici = [cle for cle in partis_ici
                       if con.execute("select 1 from fiche where reseau=? and identifiant=? and etat_suivi='absent'", cle).fetchone()]
        for cle in absents_ici[:50]:
            f = con.execute("select reseau, identifiant, url from fiche where reseau=? and identifiant=?", cle).fetchone()
            if not (f["url"] or "").startswith("http"):
                continue
            try:
                rep = lecteur.get(f["url"], "maj")
            except (PermissionError, requests.RequestException):
                continue
            perdu = rep.status_code in (404, 410) or urlsplit(rep.url).path in ("", "/")
            if perdu:
                motif = f"sa page a disparu (HTTP {rep.status_code})" if rep.status_code in (404, 410) else "sa page renvoie vers l'accueil"
                con.execute("update fiche set etat_suivi='parti', motif_depart=? where reseau=? and identifiant=?",
                            (motif, f["reseau"], f["identifiant"]))
                _evenement(con, n, f["reseau"], f["identifiant"], "parti", motif)
                comptes["parti_preuve"] = comptes.get("parti_preuve", 0) + 1
    malades = sorted(r for r, s in sante.items() if s == "malade")
    con.execute("update collecte set etat='finie', fin=?, note=? where numero=?",
                (maintenant(), f"malades : {', '.join(malades) or 'aucune'} ; {comptes}", n))
    con.commit()
    _CACHE.pop("collecte", None)
    journal("maj", f"collecte n° {n} fermee : {comptes or 'aucun changement'} ; sources malades : {', '.join(malades) or 'aucune'}")
    return CODE_ERREUR if malades else CODE_FINI


# --------------------------------------------------------------------------------------------
# CSV + COMPTE RENDU
# --------------------------------------------------------------------------------------------
NOMS_RESEAUX = {"iad": "iad", "safti": "SAFTI", "kw": "Keller Williams", "registre": "registre public (independant)",
                "orpi": "Orpi", "laforet": "Laforêt", "c21": "Century 21", "42avenue": "42ème Avenue",
                "manufacture": "La Manufacture de l'Immo", "capifrance": "Capifrance", "optimhome": "Optimhome",
                "bsk": "BSK Immobilier", "megagence": "Megagence", "expertimo": "Expertimo", "drhouse": "Dr House Immo",
                "3g": "3G Immo", "lfimmo": "LF immo (ex-Lafourmi)", "sextant": "Sextant", "cotepart": "Côté Particuliers",
                "exp": "eXp France", "groupement": "Groupement Immobilier", "immodiffusion": "Immo-Diffusion",
                "lucarne": "A La Lucarne de l'immobilier", "liberkeys": "Liberkeys", "maxihome": "Maxihome"}
COLONNES_CSV = ("reseau", "prenom", "nom", "fonction", "agence", "commune", "code_postal", "departement",
                "agence_gti_la_plus_proche", "distance_km", "telephone", "email", "source_contact",
                "pourquoi_sans_contact", "nb_annonces", "nb_avis", "note_avis", "distinction", "siren", "rsac_ville",
                "entreprise_creee_le", "anciennete_ans", "entreprise_active", "opposition_prospection_registre",
                "autres_reseaux", "fiche_publique", "premiere_vue", "fiche_desactivee",
                "etat_suivi", "etat_depuis", "motif_depart", "corrige_dans_l_app")
POURQUOI_SANS_CONTACT = {  # ce que dit la source quand la case reste vide
    "iad": "iad : numero derriere un clic (non force)",
    "kw": "KW : pas d'e-mail publie (formulaire)",
    "registre": "registre public : aucune coordonnee",
    "laforet": "Laforêt : aucun contact personnel publie",
    "c21": "Century 21 : aucun contact personnel publie",
    "42avenue": "42eme Avenue : pas d'e-mail publie (formulaire)",
    "orpi": "Orpi : e-mail par formulaire seulement",
    "megagence": "Megagence : pas d'e-mail publie (formulaire)",
    "sextant": "Sextant : pas d'e-mail publie (formulaire)",
    "3g": "3G Immo : e-mail non affiche (champ cache, non lu)",
    "immodiffusion": "Immo-Diffusion : pas d'e-mail publie",
    "lucarne": "Lucarne : pas d'e-mail publie",
}
# le carnet : seuls ces champs se corrigent dans l'app (le reste vient des annuaires ou du registre)
CHAMPS_CORRIGEABLES = ("prenom", "nom", "telephone", "email", "commune", "code_postal", "fonction", "agence")


def agences_placees(con):
    out = []
    for nom, dep in AGENCES_GTI:
        c = position_commune(con, nom, None, dep)
        if c is not None:
            out.append((nom, c["lat"], c["lon"]))
    return out


def lignes_csv(con) -> list[dict]:
    agences = agences_placees(con)
    par_siren: dict[str, set] = {}
    for r in con.execute("select reseau, siren from fiche where siren is not null"):
        par_siren.setdefault(r["siren"], set()).add(r["reseau"])
    carnet: dict[tuple, dict] = {}
    for c in con.execute("select reseau, identifiant, champ, valeur from correction"):
        if c["champ"] in CHAMPS_CORRIGEABLES:
            carnet.setdefault((c["reseau"], c["identifiant"]), {})[c["champ"]] = c["valeur"]
    lignes = []
    for f in con.execute("select f.*, e.date_creation, e.etat, e.opposition from fiche f left join entreprise e on e.siren=f.siren "
                         "where f.departement in (%s)" % ",".join("?" * len(DEPARTEMENTS)), DEPARTEMENTS):
        if f["reseau"] == "registre" and par_siren.get(f["siren"], set()) - {"registre"}:
            continue  # deja connu par un reseau : une seule ligne, celle du reseau (« autres_reseaux » le dit)
        lat, lon = f["lat"], f["lon"]
        if lat is None:
            c = position_commune(con, f["commune"], f["code_postal"])
            if c is not None:
                lat, lon = c["lat"], c["lon"]
        proche, dist = "", ""
        if lat is not None and agences:
            nom, d = min(((a[0], distance_km(lat, lon, a[1], a[2])) for a in agences), key=lambda x: x[1])
            proche, dist = nom, round(d, 1)
        anciennete = ""
        if f["date_creation"]:
            try:
                anciennete = round((dt.date.today() - dt.date.fromisoformat(f["date_creation"])).days / 365.25, 1)
            except ValueError:
                pass
        autres = sorted(par_siren.get(f["siren"], set()) - {f["reseau"]}) if f["siren"] else []
        pourquoi = ""
        if not (f["telephone"] and f["email"]):
            pourquoi = POURQUOI_SANS_CONTACT.get(f["reseau"], "rien d'affiche sur la page" if not (f["telephone"] or f["email"])
                                                 else ("pas d'e-mail affiche" if f["telephone"] else "pas de telephone affiche"))
        lignes.append({
            "reseau": NOMS_RESEAUX.get(f["reseau"], f["reseau"]), "prenom": f["prenom"] or "", "nom": f["nom"] or "",
            "fonction": f["fonction"] or "", "agence": f["agence"] or "",
            "commune": f["commune"] or "", "code_postal": f["code_postal"] or "", "departement": f["departement"] or "",
            "agence_gti_la_plus_proche": proche, "distance_km": dist,
            "telephone": f["telephone"] or "", "email": f["email"] or "", "source_contact": f["source_contact"] or "",
            "pourquoi_sans_contact": pourquoi,
            "nb_annonces": "" if f["nb_annonces"] is None else f["nb_annonces"],
            "nb_avis": "" if f["nb_avis"] is None else f["nb_avis"],
            "note_avis": "" if not f["note_avis"] else f["note_avis"],
            "distinction": f["distinction"] or "", "siren": f["siren"] or "", "rsac_ville": f["rsac_ville"] or "",
            "entreprise_creee_le": f["date_creation"] or "", "anciennete_ans": anciennete,
            "entreprise_active": {"A": "oui", "C": "CESSEE"}.get(f["etat"] or "", ""),
            "opposition_prospection_registre": "OUI" if f["opposition"] else "",
            "autres_reseaux": ", ".join(NOMS_RESEAUX.get(a, a) for a in autres),
            "fiche_publique": f["url"] or "", "premiere_vue": f["premiere_vue"] or "",
            "fiche_desactivee": "oui" if f["desactive"] else "",
            "etat_suivi": f["etat_suivi"] or "", "etat_depuis": f["etat_depuis"] or "",
            "motif_depart": f["motif_depart"] or "", "corrige_dans_l_app": "",
        })
        # LE CARNET GAGNE : une valeur corrigee dans l'app remplace celle des annuaires, a chaque export
        corr = carnet.get((f["reseau"], f["identifiant"]))
        if corr:
            lignes[-1].update({k: v or "" for k, v in corr.items()})
            lignes[-1]["corrige_dans_l_app"] = ", ".join(sorted(corr))
            if {"telephone", "email"} & set(corr):
                lignes[-1]["source_contact"] = (lignes[-1]["source_contact"] + " + corrige dans l'app").strip(" +")
    lignes.sort(key=lambda l: (l["distance_km"] if l["distance_km"] != "" else 9999, l["nom"]))
    return lignes


def cmd_csv(con, lecteur, args) -> int:
    SORTIE.mkdir(parents=True, exist_ok=True)
    lignes = lignes_csv(con)
    chemin = SORTIE / f"candidats_region_{aujourdhui()}.csv"
    tmp = chemin.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES_CSV, delimiter=";")
        w.writeheader()
        for l in lignes:
            w.writerow({k: (str(v).replace(".", ",") if isinstance(v, float) else v) for k, v in l.items()})
    os.replace(tmp, chemin)
    journal("csv", f"{len(lignes)} lignes -> {chemin}")
    return CODE_FINI


# --------------------------------------------------------------------------------------------
# CONTROLE : comptes, doublons, temoins
# --------------------------------------------------------------------------------------------
RX_TELEPHONE = re.compile(r"(?:\+33\s?|0)[1-9](?:[\s.\-]?\d{2}){4}")
# Les temoins positifs vivent A COTE DES DONNEES (temoins.txt, « reseau identifiant » par ligne), pas
# dans le code : un identifiant de conseiller est une donnee personnelle, il n'a rien a faire dans
# l'historique git (minimisation, 20/11 au soir). Fichier absent ou vide = controle ROUGE : un controle
# sans temoin ne prouve rien.
FICHIER_TEMOINS = DOSSIER / "temoins.txt"


def temoins_positifs() -> list[tuple[str, str]]:
    if not FICHIER_TEMOINS.exists():
        return []
    return [tuple(l.split()[:2]) for l in FICHIER_TEMOINS.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#") and len(l.split()) >= 2]


def cmd_controle(con, lecteur, args) -> int:
    rouge = 0
    journal("controle", "--- comptes par reseau et departement ---")
    for r in con.execute("select reseau, departement, count(*) n, sum(fiche_lue) lues, sum(siren is not null) avec_siren "
                         "from fiche group by 1,2 order by 1,2"):
        journal("controle", f"{r['reseau']:6} {r['departement']} : {r['n']:4} fiches, {r['lues']} lues, {r['avec_siren']} avec SIREN")
    # 1. LA REGLE DES COORDONNEES (correction du 20/11, note §9)
    fuites = 0
    #  a. aucune coordonnee hors des 3 colonnes prevues (ni nom, ni commune, ni distinction...)
    for f in con.execute("select * from fiche"):
        for k in f.keys():
            v = f[k]
            if isinstance(v, str) and k not in ("url",) + COLONNES_CONTACT and (RX_TELEPHONE.search(v) or "@" in v):
                fuites += 1
                journal("controle", f"⛔ coordonnee hors de sa colonne : {f['reseau']}/{f['identifiant']} colonne {k}")
    #  b. aucune coordonnee pour un reseau ou elle est CACHEE (iad)
    caches = con.execute("select count(*) from fiche where reseau in (%s) and (telephone is not null or email is not null)"
                         % ",".join("?" * len(RESEAUX_CONTACT_CACHE)), RESEAUX_CONTACT_CACHE).fetchone()[0]
    journal("controle", f"coordonnees gardees la ou elles sont cachees ({', '.join(RESEAUX_CONTACT_CACHE)}) : {caches}")
    fuites += caches
    #  c. toute coordonnee porte sa source, et un format valide
    sans_source = con.execute("select count(*) from fiche where (telephone is not null or email is not null) "
                              "and source_contact is null").fetchone()[0]
    mauvais = sum(1 for r in con.execute("select telephone, email from fiche where telephone is not null or email is not null")
                  if (r["telephone"] and telephone_lisible(r["telephone"]) != r["telephone"])
                  or (r["email"] and email_lisible(r["email"]) != r["email"]))
    journal("controle", f"coordonnees sans source : {sans_source} · au format invalide : {mauvais}")
    fuites += sans_source + mauvais
    #  d. pas de colonne interdite (photo, texte de presentation, naissance)
    colonnes = [r[1] for r in con.execute("pragma table_info(fiche)")]
    interdites = [c for c in colonnes if c in ("photo", "phone", "description", "naissance", "date_naissance")]
    fuites += len(interdites)
    journal("controle", f"regle des coordonnees : {'VERT' if not fuites else 'ROUGE'} ({fuites})")
    rouge += bool(fuites)
    for r in con.execute("select reseau, count(*) n, sum(telephone is not null) t, sum(email is not null) e "
                         "from fiche group by 1 order by 1"):
        journal("controle", f"{r['reseau']:12} : {r['n']:4} fiches, {r['t']} telephones, {r['e']} e-mails")
    # 2. temoins positifs
    temoins = temoins_positifs()
    if not temoins:
        journal("controle", f"⛔ aucun temoin positif ({FICHIER_TEMOINS}) : un controle sans temoin ne prouve rien")
        rouge += 1
    for reseau, ident in temoins:
        ok = con.execute("select 1 from fiche where reseau=? and identifiant=?", (reseau, ident)).fetchone()
        journal("controle", f"temoin positif {reseau}/{ident} : {'present' if ok else 'ABSENT'}")
        rouge += not ok
    # 3. SIREN : presence, validite, entreprise trouvee
    for r in con.execute("select reseau, count(*) n, sum(siren is null) sans, "
                         "sum(siren is not null and fiche_lue=1) avec from fiche group by 1"):
        journal("controle", f"{r['reseau']:6} : {r['sans']} fiches sans SIREN sur {r['n']}")
    invalides = [r[0] for r in con.execute("select distinct siren from fiche where siren is not null") if not siren_valide(r[0])]
    journal("controle", f"SIREN a cle invalide : {len(invalides)} {invalides[:5]}")
    nt = con.execute("select count(*) from entreprise where trouve=0").fetchone()[0]
    cess = con.execute("select count(*) from entreprise where etat='C'").fetchone()[0]
    opp = con.execute("select count(*) from entreprise where opposition=1").fetchone()[0]
    fuite_opp = con.execute("select count(*) from entreprise where opposition=1 and "
                            "coalesce(date_creation, etat, naf, siege_cp, siege_commune) is not null").fetchone()[0]
    journal("controle", f"entreprises introuvables : {nt} · CESSEES : {cess} · en OPPOSITION a la prospection : {opp}")
    journal("controle", f"temoin : donnees de registre gardees pour une personne en opposition : {fuite_opp} "
                        f"({'VERT' if not fuite_opp else 'ROUGE'})")
    rouge += bool(fuite_opp)
    # 4. la meme personne dans deux reseaux
    for r in con.execute("select siren, group_concat(reseau||'/'||identifiant, ' + ') qui from fiche where siren is not null "
                         "group by siren having count(*) > 1"):
        journal("controle", f"meme SIREN dans plusieurs fiches : {r['siren']} -> {r['qui']}")
    # 5. SAFTI : la grille est-elle lue, des listes tronquees ?
    g = con.execute("select count(*) n, sum(lue) lues, sum(replace(chemin_rendu,' ','-') != chemin) autres from grille_safti").fetchone()
    journal("controle", f"grille SAFTI : {g['lues']}/{g['n']} communes lues, {g['autres']} comprises comme une autre commune")
    journal("controle", f"VERDICT : {'VERT' if not rouge else 'ROUGE'}")
    return CODE_FINI if not rouge else CODE_ERREUR


# --------------------------------------------------------------------------------------------
COMMANDES = {
    ("communes", None): cmd_communes,
    ("iad", "liste"): cmd_iad_liste, ("iad", "fiches"): cmd_iad_fiches,
    ("safti", "liste"): cmd_safti_liste, ("safti", "fiches"): cmd_safti_fiches,
    ("kw", "liste"): cmd_kw_liste, ("kw", "fiches"): cmd_kw_fiches,
    ("siren", None): cmd_siren, ("csv", None): cmd_csv, ("controle", None): cmd_controle,
    # correction du 20/11
    ("registre", None): cmd_registre, ("orpi", None): cmd_orpi, ("laforet", None): cmd_laforet,
    ("c21", None): cmd_c21, ("42avenue", None): cmd_42avenue, ("manufacture", None): cmd_manufacture,
    ("capifrance", None): lambda con, l, a: cmd_capi_optim("capifrance", con, l, a),
    ("optimhome", None): lambda con, l, a: cmd_capi_optim("optimhome", con, l, a),
    ("bsk", None): cmd_bsk, ("megagence", None): cmd_megagence, ("expertimo", None): cmd_expertimo,
    ("drhouse", None): cmd_drhouse, ("3g", None): cmd_3g, ("lfimmo", None): cmd_lfimmo,
    ("sextant", None): cmd_sextant, ("cotepart", None): cmd_cotepart, ("exp", None): cmd_exp,
    # R1, 20/11 au soir
    ("groupement", None): cmd_groupement, ("immodiffusion", None): cmd_immodiffusion,
    ("lucarne", None): cmd_lucarne, ("liberkeys", None): cmd_liberkeys, ("maxihome", None): cmd_maxihome,
    # R2, la mise a jour
    ("collecte", "initiale"): cmd_collecte_initiale, ("collecte", "ouvrir"): cmd_collecte_ouvrir,
    ("maj", None): cmd_maj,
}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("commande")
    p.add_argument("etape", nargs="?")
    p.add_argument("--limite", type=int, default=0, help="n'en lire que N (essai)")
    p.add_argument("--minutes", type=float, default=9.0, help="duree maximale de la commande (defaut 9)")
    p.add_argument("--relire", action="store_true", help="relire meme ce qui est deja lu")
    p.add_argument("--sans-reseau", action="store_true", help="maj : ne pas verifier les pages des absents (essai hors ligne)")
    args = p.parse_args(argv)
    fn = COMMANDES.get((args.commande, args.etape))
    if not fn:
        p.error(f"commande inconnue : {args.commande} {args.etape or ''}")
    con = ouvrir_base()
    lecteur = Lecteur(fin=time.time() + args.minutes * 60)
    nom = f"{args.commande} {args.etape or ''}".strip()
    journal(nom, f"debut (limite={args.limite or '-'}, {args.minutes:g} min max)")
    try:
        code = fn(con, lecteur, args)
    except TempsEcoule:
        journal(nom, f"coupe a {args.minutes:g} min : relancer la meme commande, elle reprend")
        return CODE_A_REPRENDRE
    except ArretNet as e:
        journal(nom, f"⛔ ARRET NET : {e}")
        return CODE_ERREUR
    except PermissionError as e:
        journal(nom, f"⛔ {e}")
        return CODE_ERREUR
    journal(nom, f"fin, code {code}")
    return code


if __name__ == "__main__":
    sys.exit(main())
