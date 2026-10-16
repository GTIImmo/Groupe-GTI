# -*- coding: utf-8 -*-
"""A.3 — LES MANDATS DE RECHERCHE QUI MANQUENT AU REGISTRE.     15/10/2026

Fait entrer dans `app_mandat` les mandats de recherche que Hektor ne nous sert
PAS, lus dans les deux sources legales fournies par Frederic.

═══════════════════════════════════════════════════════════════════════════════
POURQUOI ILS MANQUENT — ce n'est ni un bug ni un filtre de notre cote
═══════════════════════════════════════════════════════════════════════════════
Notre SEULE porte est l'annonce : le registre se construit depuis
`AnnonceById.mandats`. Or un mandat de RECHERCHE n'est pas porte par un bien,
il est porte par la PERSONNE qui nous mandate pour chercher. Et les trois
routes « Mandat » de l'API sont GELEES au n 18339 / 30-01-2026 (verifie par
appels reels le 21/07). Un mandat de recherche recent n'a donc AUCUNE porte.

    ce que le registre LEGAL en porte (mars-oct 2026)   19
    ce que nous en avions                                3
    -> 16 manquants, soit 84 %

    + 22 autres dans les exports Modelo (jusqu'au 26/02/2026)

═══════════════════════════════════════════════════════════════════════════════
COMMENT ILS ENTRENT — sans toucher a la cle du registre
═══════════════════════════════════════════════════════════════════════════════
    hektor_annonce_id = ''      la chaine VIDE, JAMAIS NULL
    app_contact_id    = le chercheur
    numero_mandat     = le numero de la serie PROTEXA, inchange

⭐ Le vide, pas le NULL : l'index UNIQUE (annonce, numero) continue de proteger
  (('',18741) deux fois -> REFUSE), alors qu'avec NULL il ne protegerait plus
  rien (deux NULL ne sont jamais egaux en SQL). Eprouve le 15/10.
  Et on ne peut pas se rabattre sur le numero seul : 8 116 numeros sont portes
  par PLUSIEURS annonces -- Hektor les recycle.

═══════════════════════════════════════════════════════════════════════════════
LES GARDE-FOUS — chacun repond a un fait mesure
═══════════════════════════════════════════════════════════════════════════════
① L'ALLOCATEUR. `app_mandat_id` est pris dans la plage DU RUN
   (MAX(id) WHERE id < 1 000 000), jamais dans celle de l'app (>= 1 000 000).
   C'est le montage dont le ratage a coute CINQ JOURS en aout, cote affaires.
② LE MARQUAGE NOCTURNE. Le run fait `UPDATE ... present_in_hektor = 0
   WHERE present_in_hektor = 1 AND <pas vu ce run>`. Ces lignes ne seront
   JAMAIS vues (pas d'annonce, API gelee) : on les pose donc DIRECTEMENT a 0,
   ce qui est la verite (« le miroir ne les porte pas ») et les met hors
   d'atteinte de cet UPDATE pour toujours. Aucune reecriture chaque nuit.
③ ⚠ LE PIEGE « 8 682 ». Le fichier protexa ecrit 8 682 la ou le registre legal
   dit 18 682 -- et 8682 EXISTE chez nous : une VENTE DE 2014. On REFUSE donc
   tout numero deja present au registre avec une autre nature. Le registre
   legal fait foi sur le numero.
④ IDEMPOTENT. Relancer ne cree pas de doublon : la cle ('', numero) le refuse,
   et le script met a jour au lieu d'inserer.
⑤ RIEN SANS `--ecrire`.

⚠ CE QUE CE SCRIPT NE FAIT PAS : ces lignes n'apparaitront PAS encore a
  l'ecran. Le fabricant du registre part des ANNONCES
  (`charger_mandats_depuis_app_mandat` fait `if not annonce: continue`).
  C'est l'etape suivante du plan (la vue), volontairement separee.

    python phase2/sync/importer_mandats_recherche.py            (a blanc)
    python phase2/sync/importer_mandats_recherche.py --ecrire
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase2.sync.mandat_ledger import _famille  # noqa: E402

for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PHASE2 = ROOT / "phase2" / "phase2.sqlite"
PDF_LEGAL = ROOT / "Certif_Export_RT14405_12586.pdf"
XLS_LEGAL = ROOT / "Export_RT14405_12598.xls"       # le MEME registre, en colonnes
XLSX_PROTEXA = ROOT / "liste des mandats de recherche protexa.xlsx"
# ⚠ Voir reparer_nature_depuis_sources_legales.py : les deux fichiers n'ont pas
#   la meme origine, l'etiquette doit le dire.
EXPORTS = (("mandats_extraits.xlsx", "modelo"),
           ("liste mandat du 02_02_2026 au 28_02_2026.xlsx", "hektor_fevrier"))
PLAGE_RESERVEE_APP = 1_000_000          # la meme que mandat_ledger.py
# Les codes d'exclusivite des exports, deja confirmes par
# manual_mandat_corrections.py (EXCLUSIVITY_LABELS, ecrit le 05/10).
EXCLUSIVITE = {"1": "EXCLUSIF", "3": "ACCORD", "5": "SIMPLE"}

CIVILITES = {"M", "MR", "MME", "MLLE", "MM", "MONSIEUR", "MADAME", "ET", "DE",
             "DU", "LA", "LE", "SCI", "SARL", "SAS"}


# ─────────────────────────────────────────────────────────── le registre LEGAL
COMMUNE = re.compile(r"-\s*([A-Za-zÀ-ÿ'’\-. ]+?)\s+(\d{5})\s*$")


def commune_cherchee(situation):
    """« Mandat de recherche - Tence 43190 » -> « Tence 43190 ».

    Rend None quand la cellule porte autre chose : Hektor y ecrit parfois le
    commentaire du negociateur (18502, « MME VIT SEULE , SON MARI... »).
    On ne devine pas — sans la forme « ... - Commune 12345 », on rend None.
    """
    for morceau in (situation or "").split("|"):
        trouve = COMMUNE.search(morceau.strip())
        if trouve:
            return "%s %s" % (trouve.group(1).strip(), trouve.group(2))
    return None


def lire_registre_legal_xls() -> dict[str, dict]:
    """Le registre legal en EXCEL — la bonne source depuis le 15/10.

    ⭐ POURQUOI ELLE REMPLACE LE PDF : le PDF colle le nom ET l'adresse dans la
      meme cellule (« Mme. DEBOUCQ Sylvie 1 place des vallards ... »), ce qui
      rendait l'appariement aux contacts impossible -- 0 nom retrouve sur 16.
      Ce fichier-ci porte des COLONNES :
          0 N° Ordre · 1 Date (+ agence) · 2 Nom du/des mandant(s)
          5 Adresse(s) · 7 Objet du mandat · 8 Nature et situation · 9 Repertoire

    ⚠ DEUX PIEGES DU FORMAT, tous deux payes le 15/10 :
      · c'est un VRAI .xls (OLE2), pas un .xlsx -- il faut `xlrd`, pas openpyxl ;
      · xlrd rend les nombres en FLOTTANT : la cellule vaut 18420.0, et retirer
        les non-chiffres donnerait « 184200 ». D'ou le passage par int().
    """
    if not XLS_LEGAL.exists():
        return {}
    import xlrd
    feuille = xlrd.open_workbook(str(XLS_LEGAL)).sheet_by_index(0)

    def numero_de(valeur):
        if isinstance(valeur, float):
            return str(int(valeur))
        chiffres = re.sub(r"\D", "", str(valeur))
        return chiffres or None

    out: dict[str, dict] = {}
    for i in range(4, feuille.nrows):                 # 0-3 = en-tete du registre
        numero = numero_de(feuille.cell_value(i, 0))
        if not numero:
            continue
        nom = str(feuille.cell_value(i, 2)).strip()
        objet = str(feuille.cell_value(i, 7)).strip()
        if not objet or "recherche" not in objet.lower():
            continue
        cellule_date = str(feuille.cell_value(i, 1))
        date = re.search(r"\d{2}/\d{2}/\d{4}", cellule_date)
        agence = re.search(r"\(Agence ([^)]*)\)", cellule_date)
        jj, mm, aaaa = (date.group(0).split("/") if date else ("", "", ""))
        out.setdefault(numero, {
            "numero": numero,
            "debut": f"{aaaa}-{mm}-{jj}" if date else None,
            "type": objet.split("\n")[0].strip(),
            "libelle": objet.split("\n")[0].strip(),
            # ⭐ le nom SEUL, sans l'adresse. Plusieurs mandants sont separes
            #   par des retours a la ligne dans la meme cellule.
            "mandants": " | ".join(x.strip() for x in nom.split("\n") if x.strip())[:200],
            "adresses": " | ".join(x.strip() for x in
                                   str(feuille.cell_value(i, 5)).split("\n") if x.strip())[:200],
            # ⭐ LA COMMUNE CHERCHEE — colonne 8, « Nature et Situation ».
            #   Pour une VENTE elle decrit le bien ; pour une RECHERCHE elle dit
            #   CE QUE LE CLIENT CHERCHE, et c'est la SEULE source qui le dit :
            #   « Mandat de recherche - Tence 43190 ».
            #   ⚠ Je l'avais PERDUE a l'import du 15/10. Elle sert a deux choses :
            #     (1) trancher quelle recherche un mandat couvre quand le contact en
            #         a plusieurs — mesure : 18682 « Issoire 63500 » designe la
            #         recherche 0, pas la 1 (Vezezoux) ;
            #     (2) remplir « Nature et situation » au registre quand AUCUNE
            #         recherche n'est saisie — 11 des 38 sont dans ce cas.
            #   ⚠ Hektor y met parfois autre chose (18502 : le commentaire du
            #     negociateur). On garde le brut, on extrait la commune si elle y est.
            "situation": " | ".join(x.strip() for x in
                                    str(feuille.cell_value(i, 8)).split("\n") if x.strip())[:200],
            "agence": (agence.group(1) if agence else ""),
            "source": "registre_legal",
        })
    return out


def lire_registre_legal_pdf() -> dict[str, dict]:
    """Repli : le PDF certifie, si l'Excel n'est pas la. ⚠ Il colle nom et
    adresse -- l'appariement des contacts y est beaucoup moins bon."""
    if not PDF_LEGAL.exists():
        print(f"   ⚠ {PDF_LEGAL.name} absent, source ignoree", file=sys.stderr)
        return {}
    from pypdf import PdfReader
    # ⚠ Les ligatures sortent cassees de l'extraction : Ł=è  Ø=é  ¨=È
    brut = "\n".join((p.extract_text() or "") for p in PdfReader(str(PDF_LEGAL)).pages)
    brut = (brut.replace("Ł", "è").replace("Ł", "è").replace("Ø", "é")
                .replace("¨", "È").replace("\\'", "'"))
    # ⚠ le separateur de milliers est une ESPACE INSECABLE, pas une espace
    debuts = [(m.start(), re.sub(r"\D", "", m.group(1)), m.group(2))
              for m in re.finditer(r"^(\d{1,3}[\s ]\d{3})\s+(\d{2}/\d{2}/\d{4})",
                                   brut, re.M)]
    objet = re.compile(r"(Mandat de (?:recherche|vente|location|gestion)[^\n]*"
                       r"|Vente de fonds de commerce)", re.I)
    out: dict[str, dict] = {}
    for i, (pos, numero, date) in enumerate(debuts):
        fin = debuts[i + 1][0] if i + 1 < len(debuts) else len(brut)
        bloc = " ".join(brut[pos:fin].split())
        trouve = objet.search(bloc)
        if not trouve:
            continue
        libelle = trouve.group(1).strip()
        if "recherche" not in libelle.lower():
            continue
        nom = re.search(r"\(Agence[^)]*\)\s+\d{2}/\d{2}/\d{4}\s+(.+?)\s+Mandat de", bloc)
        ag = re.search(r"\(Agence\s*([^)]*)\)", bloc)
        jj, mm, aaaa = date.split("/")
        out.setdefault(numero, {
            "numero": numero, "debut": f"{aaaa}-{mm}-{jj}",
            "type": libelle.split("Mandat de recherche")[0].strip() or libelle,
            "libelle": libelle,
            "mandants": (nom.group(1).strip() if nom else "")[:200],
            "agence": " ".join((ag.group(1) if ag else "").split()),
            "source": "registre_legal",
        })
    return out


def lire_xlsx_protexa() -> dict[str, str]:
    """Le NOM SEUL du mandant, par numero.

    ⚠ POURQUOI CETTE SOURCE EN PLUS DU PDF, ET C'EST UNE PANNE VECUE (15/10) :
      le PDF colle le nom ET l'adresse dans la meme cellule --
      « Mme. DEBOUCQ Sylvie 1 place des vallards Saint-Didier-en-Velay (43140) ».
      L'empreinte cherchait donc un contact nomme « DEBOUCQ SYLVIE PLACE
      VALLARDS SAINT DIDIER VELAY » : 0 trouve sur 16. Ce fichier-ci porte le
      nom et l'adresse dans DEUX COLONNES.
    """
    if not XLSX_PROTEXA.exists():
        return {}
    from openpyxl import load_workbook
    wb = load_workbook(XLSX_PROTEXA, read_only=True, data_only=True)
    noms: dict[str, str] = {}
    for brute in wb.worksheets[0].iter_rows(values_only=True):
        cellules = ["" if c is None else str(c).strip() for c in brute]
        if not cellules:
            continue
        numero = re.sub(r"\D", "", cellules[0])
        if numero and len(cellules) > 2 and cellules[2]:
            noms.setdefault(numero, cellules[2])
    wb.close()
    return noms


def couper_adresse(nom: str) -> str:
    """Le nom s'arrete ou l'adresse commence -- c'est-a-dire au premier CHIFFRE.

    Filet pour les mandats que le xlsx protexa ne couvre pas (anterieurs au
    02/04). « Mme. LANIEL Amandine champet Saint-Maurice-de... » n'a pas de
    chiffre : on garde alors les 4 premiers mots, ce qui suffit a l'empreinte.
    """
    coupe = re.split(r"\s\d", nom or "", maxsplit=1)[0].strip()
    mots = coupe.split()
    return " ".join(mots[:4]) if len(mots) > 4 else coupe


# ──────────────────────────────────────────────────────────── les exports Modelo
def lire_exports() -> dict[str, dict]:
    from openpyxl import load_workbook
    out: dict[str, dict] = {}
    for nom, etiquette in EXPORTS:
        chemin = ROOT / nom
        if not chemin.exists():
            continue
        wb = load_workbook(chemin, read_only=True, data_only=True)
        it = wb.worksheets[0].iter_rows(values_only=True)
        entete = [str(c).strip() if c is not None else "" for c in next(it)]
        for brute in it:
            ligne = dict(zip(entete, brute))
            if str(ligne.get("mandate_type") or "").strip() != "3":   # 3 = RECHERCHE
                continue
            numero = str(ligne.get("mandate_number") or "").strip()
            if not numero:
                continue
            out.setdefault(numero, {
                "numero": numero,
                "debut": str(ligne.get("date_start") or ligne.get("date") or "")[:10] or None,
                "fin": str(ligne.get("date_end") or "")[:10] or None,
                # ⚠⚠ LE TYPE EST CELUI DE HEKTOR, PAS UN LIBELLE INVENTE.
                #   Defaut du 15/10, trouve par une question de Frederic : j'avais
                #   ecrit « Mandat de recherche » comme type. Or le type est la
                #   CATEGORIE JURIDIQUE (SIMPLE / EXCLUSIF / ACCORD), pas l'objet
                #   -- et c'est lui qui determine la FAMILLE DE REGISTRE.
                #   Consequence mesuree : mes 22 lignes sortaient en PROTEXA alors
                #   que les 716 mandats de la meme epoque (n 17555-18297) sont
                #   TOUS en HEKTOR. L'export donne la bonne valeur : `exclusivity`
                #   (22 SIMPLE + 4 EXCLUSIF). L'objet, lui, vit dans `nature`.
                "type": EXCLUSIVITE.get(str(ligne.get("exclusivity") or "").strip()),
                "libelle": EXCLUSIVITE.get(str(ligne.get("exclusivity") or "").strip()),
                "mandants": str(ligne.get("contact_full_name") or "").strip()[:200],
                # ⭐ CE QUE LE MANDAT COUVRE, EN TOUTES LETTRES. Retrouve le
                #   16/10, apres la question de Frederic « autant creer une
                #   recherche et l'archiver ? ». Non : il n'y avait rien a mettre
                #   DEDANS, parce que cette phrase-la etait restee dans le fichier.
                #   Mesure : 22 des 38 mandats sans bien n'avaient AUCUN texte ;
                #   `product_recap` en donne un pour 22 sur 22.
                #
                #   ⚠ CLE DISTINCTE DE `situation`, ET C'EST VOULU. `situation`
                #     (registre legal, colonne 8) dit CE QUE LE CLIENT CHERCHE, et
                #     elle alimente `commune_cherchee()` pour trancher quelle
                #     recherche un mandat couvre -- arbitrage mesure sur les 38.
                #     `product_recap`, lui, decrit souvent UN BIEN DEJA DESIGNE
                #     (« sise 22 avenue Marechal Foch - 63120 COURPIERE », 5 cas
                #     sur 11). Verser sa commune dans l'arbitrage ferait choisir
                #     une recherche sur la commune DU BIEN, pas sur celle cherchee.
                #     On l'affiche, on ne s'en sert pas pour decider.
                "designation": str(ligne.get("product_recap") or "").strip()[:400] or None,
                "agence": "",
                "blob_contact": ligne.get("linked_contact_id"),
                "source": etiquette,
            })
        wb.close()
    return out


# ───────────────────────────────────────────────────── retrouver le chercheur
def empreinte(nom: str) -> frozenset:
    texte = unicodedata.normalize("NFKD", nom or "").encode("ascii", "ignore").decode().upper()
    return frozenset(m for m in re.findall(r"[A-Z]{2,}", texte) if m not in CIVILITES)


def _tel(valeur) -> str:
    """Les 9 derniers chiffres : c'est ce qui survit aux +33, aux espaces et
    aux points. En-deca de 9 chiffres on ne compare pas (trop court)."""
    chiffres = re.sub(r"\D", "", str(valeur or ""))
    return chiffres[-9:] if len(chiffres) >= 9 else ""


def _sans_accent(texte) -> str:
    return unicodedata.normalize("NFKD", str(texte or "")).encode(
        "ascii", "ignore").decode().upper().strip()


def batir_index_fort(con: sqlite3.Connection):
    """Les index qui identifient VRAIMENT une personne : e-mail, telephone,
    et (nom, prenom) SEPARES.

    ⭐ POURQUOI, ET CE QUE CA RAPPORTE (mesure du 15/10 sur les 26 mandats de
      recherche des exports) : contre l'appariement par le nom entier, celui-ci
      resout 24 sur 26, dont 5 qui etaient AMBIGUS et 1 INTROUVABLE. Les deux
      qu'il manque, l'ancien les trouve -- d'ou la cascade, pas le remplacement.

    ⚠ ON N'ACCEPTE QU'UNE CORRESPONDANCE UNIQUE. Une adresse d'agence partagee
      par trente contacts tombe donc d'elle-meme : elle n'est jamais unique.
    """
    mails: dict[str, set] = defaultdict(set)
    tels: dict[str, set] = defaultdict(set)
    noms: dict[tuple, set] = defaultdict(set)
    for cid, nom, prenom, mail, p1, p2 in con.execute(
            "SELECT hektor_contact_id, nom, prenom, email, phone_primary, phone_secondary"
            "  FROM app_contact_current"):
        cid = str(cid)
        if mail and "@" in str(mail):
            mails[str(mail).strip().lower()].add(cid)
        for telephone in (p1, p2):
            clef = _tel(telephone)
            if clef:
                tels[clef].add(cid)
        if nom:
            noms[(_sans_accent(nom), _sans_accent(prenom))].add(cid)
    return mails, tels, noms


def retrouver_fort(blob, forts):
    """Rend (id, par_quoi) ou (None, '') -- l'identite par ce qui ne ment pas.

    `blob` est la colonne `linked_contact_id` des exports Modelo : malgre son
    nom, ce n'est PAS un identifiant mais la FICHE COMPLETE du contact, en
    JSON. ⚠ Elle porte UNE LISTE de personnes (1 a 3 : les couples), jamais un
    objet seul -- mesure du 15/10, mais on gere les deux (lecon du projet sur
    les blobs JSON).
    """
    mails, tels, noms = forts
    try:
        charge = json.loads(blob) if blob else None
    except Exception:
        return None, ""
    if charge is None:
        return None, ""
    gens = charge if isinstance(charge, list) else [charge]
    for personne in gens:
        if not isinstance(personne, dict):
            continue
        mail = str(personne.get("email") or "").strip().lower()
        if mail and len(mails.get(mail, ())) == 1:
            return next(iter(mails[mail])), "email"
        for champ in ("phone_mobile", "phone_fixed", "phone_pro"):
            clef = _tel(personne.get(champ))
            if clef and len(tels.get(clef, ())) == 1:
                return next(iter(tels[clef])), "telephone"
        couple = (_sans_accent(personne.get("last_name")),
                  _sans_accent(personne.get("first_name")))
        if couple[0] and len(noms.get(couple, ())) == 1:
            return next(iter(noms[couple])), "nom+prenom"
    return None, ""


def batir_index(con: sqlite3.Connection):
    index: dict[frozenset, list[tuple[str, str]]] = defaultdict(list)
    for cid, nom in con.execute(
            "SELECT hektor_contact_id, display_name FROM app_contact_current"
            " WHERE COALESCE(TRIM(display_name), '') <> ''"):
        cle = empreinte(nom)
        if cle:
            index[cle].append((str(cid), nom))
    chercheurs = {str(c) for (c,) in con.execute(
        "SELECT DISTINCT hektor_contact_id FROM app_contact_search_current")}
    return index, chercheurs


def retrouver(nom_brut: str, index, chercheurs):
    """Rend (etat, id, nom). ⭐ L'homonymie se tranche par « a-t-il une
    RECHERCHE enregistree ? » -- quelqu'un qui nous mandate pour chercher en a
    une. Mesure du 15/10 : cela tranche 6 cas sur 11."""
    morceaux = [nom_brut] + [p.strip() for p in re.split(r"[/|]", nom_brut or "") if p.strip()]
    for morceau in morceaux:
        cle = empreinte(morceau)
        if not cle or cle not in index:
            continue
        candidats = index[cle]
        if len(candidats) == 1:
            return "trouve", candidats[0][0], candidats[0][1]
        avec = [c for c in candidats if c[0] in chercheurs]
        if len(avec) == 1:
            return "leve", avec[0][0], avec[0][1]
        return "ambigu", None, f"{len(candidats)} homonymes"
    return "absent", None, ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fait entrer au registre les mandats de recherche absents.")
    parser.add_argument("--ecrire", action="store_true")
    parser.add_argument("--base", default=str(PHASE2))
    args = parser.parse_args()

    # ⭐ L'EXCEL D'ABORD (colonnes separees), le PDF en repli.
    legal = lire_registre_legal_xls()
    via = "Excel"
    if not legal:
        legal = lire_registre_legal_pdf()
        via = "PDF (repli -- nom et adresse colles)"
    modelo = lire_exports()
    # ⭐ LES RETOUCHES DE NOM NE VALENT QUE POUR LE REPLI PDF — 15/10.
    #   ⚠ DEFAUT ATTRAPE PAR LA MESURE : appliquees a l'Excel, elles ABIMENT
    #     des noms deja propres. `couper_adresse` garde 4 mots au plus, donc
    #     « M. FAYARD Adrien et Myriam » devenait « M. FAYARD Adrien et » et
    #     « M. CURSOUX ODILE ET DANIEL » perdait DANIEL -- deux contacts perdus.
    #   Et le xlsx protexa n'apporte plus rien face a l'Excel : compares nom a
    #   nom sur les 19, l'Excel fait MIEUX 2 fois et jamais moins bien.
    repris = 0
    if via != "Excel":
        noms_propres = lire_xlsx_protexa()
        for numero, bloc in legal.items():
            propre = noms_propres.get(numero)
            # LE PIEGE « 8 682 », DEUXIEME VISAGE : le xlsx a perdu le « 1 » de
            # tete sur le mandat de M. JOUM. On ne corrige pas le numero (le
            # registre legal fait foi), on va juste CHERCHER LE NOM sous la
            # forme tronquee -- et seulement si elle ne designe pas, elle aussi,
            # un mandat du registre.
            if not propre and numero.startswith("1") and numero[1:] not in legal:
                propre = noms_propres.get(numero[1:])
            if propre:
                bloc["mandants"] = propre
                repris += 1
            elif bloc.get("mandants"):
                bloc["mandants"] = couper_adresse(bloc["mandants"])
    print(f"sources : {len(legal)} au registre legal [{via}] · {len(modelo)} dans les exports Modelo")
    if repris:
        print(f"          {repris} noms repris du xlsx protexa (repli PDF)")
    # Le registre LEGAL fait foi quand les deux parlent du meme numero.
    sources = dict(modelo)
    sources.update(legal)
    print(f"          {len(sources)} mandats de recherche distincts\n")

    con = sqlite3.connect(args.base, timeout=120)
    con.execute("PRAGMA busy_timeout=120000")
    colonnes = {r[1] for r in con.execute("PRAGMA table_info(app_mandat)")}
    if "app_contact_id" not in colonnes:
        print("ARRET : la colonne app_contact_id n'existe pas. Poser les colonnes d'abord.",
              file=sys.stderr)
        return 2

    deja = defaultdict(list)
    for num, ann, nat in con.execute(
            "SELECT numero_mandat, hektor_annonce_id, nature FROM app_mandat"):
        deja[str(num).strip()].append((str(ann), nat))
    index, chercheurs = batir_index(con)
    forts = batir_index_fort(con)
    prochain = (con.execute(
        "SELECT COALESCE(MAX(app_mandat_id), 0) FROM app_mandat WHERE app_mandat_id < ?",
        (PLAGE_RESERVEE_APP,)).fetchone()[0] or 0) + 1
    print(f"allocateur : les nouveaux ids partiront de {prochain} "
          f"(plage DU RUN, < {PLAGE_RESERVEE_APP})\n")

    a_poser, refus, lignes = [], Counter(), []
    etats = Counter()
    for numero in sorted(sources, key=lambda x: int(x) if x.isdigit() else 0):
        s = sources[numero]
        porteurs = deja.get(numero, [])
        # ③ le piege « 8 682 » : ce numero est-il deja pris par autre chose ?
        conflit = [p for p in porteurs if p[0] != "" and (p[1] or "") != "RECHERCHE"]
        if conflit:
            refus[f"numero deja pris par un mandat {conflit[0][1]} (annonce {conflit[0][0]})"] += 1
            lignes.append((numero, "REFUSE", s["source"], "", f"deja {conflit[0][1]} sur {conflit[0][0]}"))
            continue
        deja_pose = any(p[0] == "" for p in porteurs)
        # ⚠ ON NE REFUSE PLUS UNE LIGNE DEJA POSEE -- defaut du 15/10.
        #   L'idempotence est assuree par le ON CONFLICT DO UPDATE, pas par
        #   cette garde. En refusant ici, un CORRECTIF du script ne pouvait
        #   plus atteindre les lignes deja ecrites : c'est ce qui a bloque la
        #   reparation de `type` et `famille` sur les 22 mandats Modelo.
        # ⚠ CETTE GARDE NE VISE QUE LES LIGNES DE HEKTOR, pas les notres.
        #   Hektor raccroche parfois un mandat de recherche au bien trouve :
        #   cette ligne-la existe deja et porte une ANNONCE. Nos propres lignes,
        #   elles, ont une annonce VIDE -- les confondre interdisait au script de
        #   se corriger lui-meme (defaut du 15/10).
        if [p for p in porteurs if (p[1] or "") == "RECHERCHE" and p[0] != ""]:
            refus["deja au registre, raccroche a une annonce par Hektor"] += 1
            continue
        # ⭐ LA CASCADE : ce qui ne ment pas d'abord (e-mail, telephone,
        #   nom+prenom), le nom entier ensuite. Les exports Modelo portent la
        #   fiche complete du contact ; le registre legal, lui, n'a que le nom.
        cid, par = retrouver_fort(s.get("blob_contact"), forts)
        if cid:
            etat, qui = "trouve", f"par {par}"
            etats[par] += 1
        else:
            etat, cid, qui = retrouver(s["mandants"], index, chercheurs)
            etats[etat] += 1
        a_poser.append((numero, s, cid))
        lignes.append((numero, "a jour" if deja_pose else "A POSER",
                       s["source"], cid or "", qui[:40]))

    neufs = sum(1 for x in lignes if x[1] == "A POSER")
    print(f"A POSER : {neufs} neufs · {len(a_poser) - neufs} deja la (mis a jour)")
    srs = etats["email"] + etats["telephone"] + etats["nom+prenom"]
    print(f"   contact retrouve : {srs + etats['trouve'] + etats['leve']} sur {len(a_poser)}")
    print(f"      par e-mail        {etats['email']:>3}   ⭐ ce qui ne ment pas")
    print(f"      par telephone     {etats['telephone']:>3}")
    print(f"      par nom+prenom    {etats['nom+prenom']:>3}")
    print(f"      par le nom entier {etats['trouve']:>3}")
    print(f"      homonymie levee   {etats['leve']:>3}   (le seul qui a une recherche enregistree)")
    print(f"      AMBIGU, laisse vide  {etats['ambigu']:>3}")
    print(f"      introuvable          {etats['absent']:>3}")
    print("\nREFUSES")
    for motif, nb in refus.most_common():
        print(f"   {nb:>4}  {motif}")
    print(f"\n{'n°':>7}  {'etat':<8} {'source':<15} {'contact':<12} qui")
    for num, etat, src, cid, qui in lignes:
        print(f"{num:>7}  {etat:<8} {src:<15} {str(cid):<12} {qui}")

    if not args.ecrire:
        print("\nA BLANC — rien n'a ete ecrit. Relancer avec --ecrire.")
        con.close()
        return 0

    vu = datetime.now(timezone.utc).isoformat(timespec="seconds")
    poses = 0
    for numero, s, cid in a_poser:
        con.execute(
            "INSERT INTO app_mandat("
            "  app_mandat_id, app_dossier_id, hektor_annonce_id, numero_mandat,"
            "  hektor_mandat_id, famille, type, date_enregistrement, date_debut,"
            "  date_fin, mandants_texte, note, payload_json, date_cloture,"
            "  first_seen_at, last_seen_at, offre_type, nature, origine,"
            "  present_in_hektor, app_contact_id, nature_app, type_app, source_app)"
            " VALUES (?, NULL, '', ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, NULL,"
            "         ?, ?, NULL, 'RECHERCHE', ?, 0, ?, 'RECHERCHE', ?, ?)"
            " ON CONFLICT(hektor_annonce_id, numero_mandat) DO UPDATE SET"
            "   type = excluded.type,"
            "   famille = excluded.famille,"
            "   date_debut = excluded.date_debut,"
            "   date_fin = excluded.date_fin,"
            "   mandants_texte = excluded.mandants_texte,"
            "   app_contact_id = COALESCE(excluded.app_contact_id, app_mandat.app_contact_id),"
            # ⚠ LE PAYLOAD ET LA NOTE DOIVENT SUIVRE, SINON LE SCRIPT NE PEUT PAS
            #   S'ENRICHIR. Defaut du 15/10 : j'ai ajoute la commune cherchee a la
            #   source, relance, et les 38 lignes sont restees comme avant --
            #   payload_json n'etait pas dans cette clause. Une colonne absente du
            #   DO UPDATE est une colonne figee a la naissance.
            "   payload_json = excluded.payload_json,"
            "   note = excluded.note,"
            "   last_seen_at = excluded.last_seen_at",
            (prochain + poses, numero,
             # ⭐ LA FAMILLE SE DEDUIT, ELLE NE S'ECRIT PAS EN DUR. C'est la
             #   regle du projet (FAMILLE_HEKTOR : SIMPLE/EXCLUSIF/ACCORD ->
             #   HEKTOR ; libelle francais -> PROTEXA), et la dupliquer ici
             #   l'aurait fait diverger. Voir le defaut du 15/10 ci-dessus.
             _famille(s.get("libelle"), numero),
             s.get("libelle"), s.get("debut"), s.get("debut"),
             s.get("fin"), s.get("mandants") or None,
             f"{s['source']} : {s.get('agence') or ''}".strip(" :"),
             json.dumps(s, ensure_ascii=True, separators=(",", ":")),
             vu, vu, s["source"],
             int(cid) if cid else None, s.get("type"), s["source"]))
        poses += 1
    con.commit()
    total = con.execute(
        "SELECT COUNT(*) FROM app_mandat WHERE hektor_annonce_id = ''").fetchone()[0]
    print(f"\nECRIT : {poses} mandats poses.")
    print(f"   lignes du registre sans annonce (mandats de recherche) : {total}")
    print("   natures du registre :")
    for r in con.execute("SELECT nature, COUNT(*) FROM app_mandat GROUP BY 1 ORDER BY 2 DESC"):
        print(f"      {r[0]:<12} {r[1]}")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
