#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RAPATRIER LES POURCENTAGES DU CLASSEUR -> app_affaire_repartition.  13/11/2026

Lot 1 des 38 colonnes decidees par Frederic le 02/11 : les negociateurs
(colonnes I K M) et leurs pourcentages (J L N).

⛔⛔ CE SCRIPT N'ECRIT RIEN, NI EN BASE NI CHEZ HEKTOR NI DANS LE CLASSEUR.
  Il mesure, il rend compte, et avec --sql il DEPOSE UN FICHIER SQL a relire.
  La pose reste un geste de Frederic : ecriture en base de production.

⭐⭐⭐ LA REGLE DE DECOMPOSITION, mesuree le 13/11 sur les 4 702 lignes :

      ENTREE 50 %  +  SORTIE 50 %  =  100 %      4 696 lignes sur 4 702

  Le classeur ne donne que le TOTAL de chaque negociateur ; notre table, elle,
  range par COTE. On redecompose ainsi :

      celui qui a le plus (toujours >= 50) prend l'ENTREE, pour 50
      son excedent au-dessus de 50 va sur la SORTIE
      tous les autres vont entierement sur la SORTIE

  Deroulee sur chaque forme reelle du classeur :
      100           entree lui 50 . sortie lui 50          4 024 lignes (85,6 %)
      75 / 25       entree A 50   . sortie A 25, B 25        243
      50 / 50       entree A 50   . sortie B 50              409
      50 / 25 / 25  entree A 50   . sortie B 25, C 25         10

  ⚠ DANS LES 409 CAS « 50/50 » la regle ne dit pas lequel a rentre -- et ca ne
    change RIEN : les totaux par personne sont identiques dans les deux sens.
    C'est pourquoi la decomposition est marquee « classeur_reconstitue » et ne
    doit JAMAIS passer pour une saisie humaine (lecon du 08/09).
  ⛔ NE PAS departager par notre « n_Negociateur 1 » : mesure du 13/11, c'est du
    bruit (178 pour le 1er du classeur, 76 pour le 2e, 97 homonymies, 25 vides).

⛔⛔ LES TROIS DANGERS, ET CE QUE LE SCRIPT EN FAIT -- il REFUSE plutot que de
  deviner. Une commission posee sur la mauvaise personne ne se rattrape pas.

  ① LES VRAIS HOMONYMES. 9 noms de famille portent DEUX personnes differentes
    (BOUCHET, CHAMPAGNAC, FAURE, GERPHAGNON, GIRINON, KRIGER, MARTINEZ,
    REYNAUD, VALLA). Le classeur n'ecrit souvent que le nom.
    -> sans prenom pour trancher : QUARANTAINE, la ligne entiere est sautee.
    ⚠ A ne pas confondre avec les 20 noms qui ont PLUSIEURS FICHES pour UNE
      SEULE personne (plusieurs agences) : la, aucune ambiguite, on choisit
      une fiche (l'active d'abord, sinon le plus petit identifiant).

  ② LA SAISIE HUMAINE. origine = 'saisie' est intouchable.
    ⭐ Mesure du 13/11 : les 5 saisies de la base sont TOUTES hors perimetre du
      classeur. Le garde-fou ne devrait donc jamais mordre -- il est la pour le
      jour ou ce ne sera plus vrai.

  ③ CE QU'ON ECRASE. 3 458 chaines visees portent deja
    hektor_partage_suppose (une SUPPOSITION : 0 a plusieurs personnes) et
    261 portent hektor (une vraie source). Le classeur fait foi -- decision de
    Frederic, « ON PREND TOUT DU CLASSEUR » -- mais les deux familles sont
    COMPTEES A PART pour qu'il les voie.

LES REGLES DE NETTOYAGE, chacune tiree d'un cas reel du classeur :
    un pourcentage SANS NOM        -> ignore            (4U2U4D1K, 3e case a 50)
    un NOM SANS POURCENTAGE        -> reliquat 100-reste (A2GX2E7D, 7E3PIT7D)
    le MEME NOM deux fois          -> fusionne          (f9b55f79, d66a35e4)
    un seul nom, aucun pourcentage -> 100 %             (241K9JOU)
    un apporteur (meilleursagents) -> QUARANTAINE s'il porte une part

    python phase2/checks/rapatrier_repartition_classeur.py
    python phase2/checks/rapatrier_repartition_classeur.py --sql
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

# ⭐ ON REUTILISE LE RAPPORT DU GEL plutot que de recopier ses conversions :
#   ses dix decouvertes y sont codees, et deux lectures du meme classeur
#   doivent donner le meme resultat (regle du projet : ne rien dupliquer).
import rapport_gel_tous_les_champs as RAP  # noqa: E402
from rapport_gel_tous_les_champs import (  # noqa: E402
    PAS_UNE_PERSONNE,
    charger_alias,
    charger_classeur,
    client,
    date_du_classeur_tolerante,
    lire_tout,
    mots_du_nom,
    nombre,
)

# ⛔⛔ LE PIEGE QUI A COUTE 272 LIGNES AU PREMIER PASSAGE (13/11) :
#   charger_alias() REAFFECTE la globale du module d'origine. Un
#   « from ... import ALIAS_NEGOCIATEUR » copie donc le dictionnaire VIDE
#   d'avant l'appel, et les deux alias sont perdus en silence -- GIRAUD et
#   ALVES MENDES ressortaient « nom ABSENT de l'annuaire ».
#   ⭐ On passe par le MODULE, qui voit toujours la valeur courante.
def alias() -> dict:
    return RAP.ALIAS_NEGOCIATEUR

ORIGINE = "classeur_reconstitue"
#: ⚠ La trace porte LE JOUR DU GESTE, jamais une date figee : elle sert a
#:   retrouver quel passage a pose une ligne (le lot 1 est du 13/11, les
#:   divergences tranchees du 14/11).
ECRIT_PAR = "rapatriement classeur " + date.today().strftime("%d/%m/%Y")
INTOUCHABLE = "saisie"

#: ⭐⭐⭐ LES LEVEES D'AMBIGUITE, DITES PAR FREDERIC LE 13/11 -- ce sont des
#:   REGLES D'ECRITURE DU CLASSEUR, pas des suppositions :
#:     « dans le sheet "champagnac" = Joel Champagnac, sinon il y a
#:       "Julie Champagnac" ; ensuite Corinne REYNAUD avec un E, et
#:       Nicolas RAYNAUD avec un A »
#:
#: ⛔⛔ POURQUOI ELLES PASSENT AVANT L'INDICE DE HEKTOR -- mesure du 13/11 :
#:   sans elles, l'indice « deja pose sur la chaine » envoyait 69 lignes sur
#:   NICOLAS REYNAUD (196), alors que « REYNAUD » au classeur designe CORINNE.
#:   Hektor connait une personne nommee Nicolas REYNAUD ; le classeur, lui,
#:   ecrit RAYNAUD quand il parle de lui. L'orthographe FAIT la personne.
#:
#: ⚠ Le prenom ecrit en entier reste PRIORITAIRE : « Julie CHAMPAGNAC » est
#:   resolu avant que cette table ne soit consultee.
#: ⭐ A BASCULER un jour dans `app_classeur_alias_negociateur`, qui porte deja
#:   le meme mecanisme pour GIRAUD et ALVES MENDES. Ici c'est du code, donc
#:   aucune ecriture en base n'a ete faite pour les poser.
LEVEES_D_AMBIGUITE = {
    # 13/11, premier envoi :
    "CHAMPAGNAC": ("238", "Joel CHAMPAGNAC"),    # sinon « Julie CHAMPAGNAC »
    "REYNAUD": ("115", "Corinne REYNAUD"),       # Nicolas, lui, s'ecrit RAYNAUD
    # 13/11, second envoi : « Martinez seul c'est Pierrick Martinez sinon c'est
    #   Stephanie Martinez, et pour Bouchet c'est Nicolas Bouchet ».
    # ⭐ « SEUL » est exactement ce que fait cette table : elle n'est consultee
    #   QU'APRES (a) le prenom ecrit et (b) l'initiale. « MARTINEZ S » tombe donc
    #   sur Stephanie, et « MARTINEZ » tout court sur Pierrick.
    "MARTINEZ": ("56", "Pierrick MARTINEZ"),     # sinon « Stephanie MARTINEZ » (55)
    "BOUCHET": ("70", "Nicolas BOUCHET"),        # sinon « Mickael BOUCHET » (193)
}


# ----------------------------------------------------------- l'annuaire

#: Les quatre cases qui racontent la VIE d'une ligne du classeur. La plus
#: tardive des quatre est son « dernier mouvement ».
#: ⚠ « Vente Prevue » et « Signee » sont volontairement ABSENTES : la premiere
#:   est une PREVISION (elle peut etre posterieure a tout le reste sans qu'il
#:   se soit rien passe), la seconde n'est pas une date.
CASES_DU_MOUVEMENT = ("Offre Achat", "Compromis", "Vente Réglée", "Annulée")


def dernier_mouvement(ligne, idx: dict):
    """La date la PLUS TARDIVE de la ligne, ou None si aucune n'est lisible.

    ⭐⭐⭐ C'EST LA REGLE QUI DEPARTAGE DEUX LIGNES SUR LA MEME CHAINE, et elle
      a ete MESUREE avant d'etre codee (14/11/2026) :

        LA LIGNE DONT LE DERNIER MOUVEMENT EST LE PLUS RECENT PORTE LA
        REPARTITION DE LA CHAINE.

    ⭐ POURQUOI ELLE EST JUSTE, et ce n'est pas une convention commode : les
      « conflits » n'en sont pas. Ce sont DEUX AFFAIRES SUCCESSIVES SUR LE MEME
      BIEN -- meme mandat, acquereurs differents. Une offre ou un compromis
      TOMBE, puis la vente qui a ABOUTI. Celle qui est tombee n'a jamais
      encaisse de commission : il n'y a rien a y repartir.

        chaine 117, mandat 15323
          A  LEGRAND=50 + FORLICO=50   Vente reglee 21/03/2024  acq. DEBRAY
          B  FORLICO=100               Annulee      23/07/2023  acq. LANGLADE

    ⭐⭐ LE TEMOIN : j'ai eprouve DEUX formulations -- « celle qui a abouti » et
      « la plus recente ». Elles donnent le MEME gagnant 29 fois sur 29,
      ZERO desaccord. Les 4 cas restants sont des biens qui ne se sont JAMAIS
      vendus (plusieurs tentatives, toutes annulees) : la, seule la date
      tranche, et « celle qui a abouti » ne dit rien. D'ou UNE SEULE regle.

    ⛔ ELLE A BESOIN DU PARSEUR TOLERANT : le classeur ecrit « 5 decembre23 »
      autant que « 05/12/2023 », et les cas mesures en portaient. Avec le
      parseur d'origine la regle serait restee muette sur une ligne sur cinq.
    """
    dates = [date_du_classeur_tolerante(ligne[idx[c]])
             for c in CASES_DU_MOUVEMENT if c in idx]
    dates = [d for d in dates if d is not None]
    return max(dates) if dates else None


def charger_annuaire(cl) -> dict:
    """Range l'annuaire par NOM DE FAMILLE -> liste de personnes.

    Une « personne » est un couple (nom, prenom) ; elle peut avoir plusieurs
    FICHES (une par agence). On garde pour chaque personne la fiche a utiliser :
    l'active d'abord, sinon le plus petit identifiant -- un choix STABLE, pour
    que deux passages donnent le meme resultat.
    """
    lignes = lire_tout(cl, "app_hektor_negotiator_agency_directory",
                       "hektor_user_id,nom,prenom,is_active",
                       "hektor_user_id.asc")
    gens: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in lignes:
        nom = " ".join(sorted(mots_du_nom(r.get("nom"))))
        pre = " ".join(sorted(mots_du_nom(r.get("prenom"))))
        if nom:
            gens[(nom, pre)].append(r)
    par_nom: dict[str, list[dict]] = defaultdict(list)
    for (nom, pre), fiches in gens.items():
        actives = [f for f in fiches if f.get("is_active")]
        choix = sorted(actives or fiches,
                       key=lambda f: int(str(f["hektor_user_id"])))[0]
        par_nom[nom].append({
            "nom": nom, "prenom": pre,
            "hektor_user_id": str(choix["hektor_user_id"]),
            "fiches": len(fiches),
        })
    return par_nom


def initiales(brut: str, mots: set) -> set:
    """Les tokens d'UNE LETTRE du texte brut, que mots_du_nom() jette.

    ⭐ DECOUVERTE DU 13/11 : quand deux personnes partagent un nom, le classeur
      ecrit l'INITIALE -- « VALLA A » pour Arnaud, « VALLA J » pour Jean.
      240 lignes partaient en quarantaine faute de la lire.
    """
    out = set()
    for t in str(brut or "").replace(".", " ").replace("-", " ").split():
        t = t.strip().upper()
        if len(t) == 1 and t.isalpha():
            out.add(t)
    return out


def resoudre(brut: str, par_nom: dict, indice: set | None = None,
             sur_la_chaine: set | None = None) -> tuple:
    """Un nom du classeur -> une personne de l'annuaire, ou un REFUS motive.

    `indice` porte les mots du NEGOCIATEUR DU MANDAT (app_mandat_register_current
    .commercial_nom), qui lui est ecrit en entier. Il ne sert QUE de dernier
    recours, et seulement s'il designe UNE SEULE des candidates -- c'est une
    source, pas une devinette.
    """
    if brut in alias():
        ident, vrai = alias()[brut]
        return ({"nom_au_moment": vrai, "hektor_user_id": ident,
                 "comment": "alias"}, "")
    mots = mots_du_nom(brut)
    if not mots:
        return (None, "nom illisible")
    # le nom de famille du classeur est le ou les mots qui matchent un nom connu
    familles = [n for n in par_nom if set(n.split()) & mots]
    if not familles:
        return (None, "nom ABSENT de l'annuaire")
    candidats: list[dict] = []
    for f in familles:
        candidats.extend(par_nom[f])

    def rendre(p, comment):
        return ({"nom_au_moment": (p["prenom"] + " " + p["nom"]).strip(),
                 "hektor_user_id": p["hektor_user_id"],
                 "comment": comment}, "")

    if len(candidats) == 1:
        return rendre(candidats[0], "un seul porteur du nom")
    # (a) le classeur a-t-il donne le PRENOM en entier ?
    restants = [p for p in candidats
                if p["prenom"] and set(p["prenom"].split()) & mots]
    if len(restants) == 1:
        return rendre(restants[0], "prenom ecrit au classeur")
    # (b) a-t-il donne l'INITIALE ? « VALLA A » -> Arnaud
    ini = initiales(brut, mots)
    if ini:
        restants = [p for p in candidats
                    if p["prenom"] and p["prenom"][:1] in ini]
        if len(restants) == 1:
            return rendre(restants[0], "initiale au classeur")
    # (c) ⭐⭐⭐ LA REGLE D'ECRITURE DU CLASSEUR, dite par Frederic le 13/11.
    #   ⛔ Elle passe AVANT Hektor : c'est une VERITE sur le classeur, alors
    #     que l'indice ci-dessous n'est qu'une trace. Sans cet ordre, 69 lignes
    #     « REYNAUD » partaient sur Nicolas au lieu de Corinne.
    for f in familles:
        if f in LEVEES_D_AMBIGUITE:
            ident, vrai = LEVEES_D_AMBIGUITE[f]
            return ({"nom_au_moment": vrai, "hektor_user_id": ident,
                     "comment": "regle du classeur (Frederic 13/11)"}, "")
    # (d) l'indice PAR CHAINE : la repartition deja posee y nomme la personne.
    #   ⛔ On lui emprunte L'IDENTITE, jamais le pourcentage -- c'est le
    #     classeur qui fait foi sur les parts (decision du 02/11).
    if sur_la_chaine:
        restants = [p for p in candidats if p["hektor_user_id"] in sur_la_chaine]
        if len(restants) == 1:
            return rendre(restants[0], "deja sur la chaine (Hektor)")
    # (e) dernier recours : le negociateur du MANDAT, ecrit en entier
    if indice:
        restants = [p for p in candidats
                    if p["prenom"] and set(p["prenom"].split()) & indice]
        if len(restants) == 1:
            return rendre(restants[0], "negociateur du mandat")
    qui = " / ".join(sorted((p["prenom"] or "?") + " " + p["nom"] for p in candidats))
    return (None, "HOMONYMES, aucun prenom pour trancher : " + qui)


# ------------------------------------- le nettoyage et la decomposition

def nettoyer(noms: list[str], pcts: list) -> tuple[list[tuple], str]:
    """Rend [(nom_brut, part)] dont la somme vaut 100, ou un REFUS motive."""
    paires: list[list] = []
    for nom, p in zip(noms, pcts):
        nom = (nom or "").strip()
        if not nom:
            continue              # pourcentage SANS NOM -> ignore (regle 1)
        if nom in PAS_UNE_PERSONNE:
            if p is not None and p > 0:
                return ([], "apporteur avec une part : " + nom)
            continue
        paires.append([nom, p])
    if not paires:
        return ([], "aucun negociateur")

    # le MEME NOM deux fois -> fusionne (regle 3)
    fondu: dict[str, list] = {}
    for nom, p in paires:
        cle = " ".join(sorted(mots_du_nom(nom))) or nom.upper()
        if cle in fondu:
            if p is not None:
                a = fondu[cle][1]
                fondu[cle][1] = p if a is None else max(a, p)
        else:
            fondu[cle] = [nom, p]
    paires = list(fondu.values())

    # un NOM SANS POURCENTAGE -> reliquat (regle 2) ; un seul, sinon on refuse
    muets = [x for x in paires if x[1] is None]
    connus = sum(x[1] for x in paires if x[1] is not None)
    if len(muets) == 1:
        muets[0][1] = round(100.0 - connus, 6)
    elif len(muets) > 1:
        return ([], "%d negociateurs sans pourcentage" % len(muets))

    paires = [x for x in paires if x[1] is not None and x[1] > 0]
    if not paires:
        return ([], "aucune part positive")
    total = sum(x[1] for x in paires)
    if abs(total - 100.0) > 0.01:
        return ([], "le total fait %g, pas 100" % total)
    return ([tuple(x) for x in paires], "")


def decomposer(parts: list[tuple]) -> tuple[list[tuple], str]:
    """[(nom, part)] -> [(cote, rang, nom, pourcentage)].

    ⭐ La tete prend l'ENTREE pour 50 ; son excedent et tous les autres vont
      sur la SORTIE. Les deux cotes valent exactement 50 par construction.
    """
    ordre = sorted(parts, key=lambda t: (-t[1], t[0]))
    tete = ordre[0]
    if tete[1] < 49.99:
        return ([], "personne n'atteint 50 pour cent (le plus gros a %g)" % tete[1])
    out: list[tuple] = [("entree", 1, tete[0], 50.0)]
    sortie: list[tuple] = []
    reste = round(tete[1] - 50.0, 6)
    if reste > 0.001:
        sortie.append((tete[0], reste))
    for nom, p in ordre[1:]:
        sortie.append((nom, p))
    somme = sum(p for _, p in sortie)
    if abs(somme - 50.0) > 0.01:
        return ([], "la sortie fait %g, pas 50" % somme)
    if len(sortie) > 3:
        return ([], "%d parts en sortie, le rang est limite a 3" % len(sortie))
    for i, (nom, p) in enumerate(sortie):
        out.append(("sortie", i + 1, nom, round(p, 6)))
    return (out, "")


# ----------------------------------------------------------- le programme

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sql", action="store_true",
                    help="depose aussi le patch SQL a relire (il n'est PAS joue)")
    ap.add_argument("--seulement-changees", action="store_true",
                    help="le patch ne touche QUE les chaines dont la repartition"
                         " en base DIFFERE de ce qu'on va poser")
    args = ap.parse_args()

    cl = client()
    print(charger_alias(cl))
    entetes, lignes = charger_classeur()
    idx = {n: i for i, n in enumerate(entetes)}

    def case(l, nom):
        i = idx.get(nom)
        return str(l[i]).strip() if i is not None and i < len(l) else ""

    liens = lire_tout(cl, "app_classeur_lien", "id_unique,app_affaire_id,role",
                      "id_unique.asc,app_affaire_id.asc")
    led = lire_tout(cl, "app_affaire_ledger",
                    "app_affaire_id,app_chaine_id,app_dossier_id,kind,hektor_annonce_id",
                    "app_affaire_id.asc")
    # ⭐ LE NEGOCIATEUR DU MANDAT porte le nom EN ENTIER : c'est lui qui departage
    #   les vrais homonymes du classeur, quand il designe une seule candidate.
    reg = lire_tout(cl, "app_mandat_register_current",
                    "hektor_annonce_id,commercial_nom",
                    "hektor_annonce_id.asc,numero_mandat.asc")
    rep = lire_tout(cl, "app_affaire_repartition",
                    "app_chaine_id,cote,rang,hektor_user_id,pourcentage,origine",
                    "app_chaine_id.asc,cote.asc,rang.asc")
    par_nom = charger_annuaire(cl)
    print("classeur : %d lignes . gel : %d liens . registre : %d . repartition : %d"
          % (len(lignes), len(liens), len(led), len(rep)))
    print("annuaire : %d noms de famille, %d personnes"
          % (len(par_nom), sum(len(v) for v in par_nom.values())))

    tx = {str(x["app_affaire_id"]): x for x in led}
    par_id: dict[str, list[dict]] = defaultdict(list)
    for x in liens:
        par_id[str(x["id_unique"]).strip()].append(x)
    deja: dict[str, list[dict]] = defaultdict(list)
    for x in rep:
        deja[str(x["app_chaine_id"])].append(x)
    nego_mandat: dict[str, set] = {}
    for x in reg:
        cle = str(x.get("hektor_annonce_id") or "")
        if cle and cle not in nego_mandat:
            nego_mandat[cle] = mots_du_nom(x.get("commercial_nom"))

    notes = Counter()
    refus: list[dict] = []
    a_poser: dict[str, dict] = {}       # par chaine : les lignes a ecrire
    vu_chaine: dict[str, str] = {}      # chaine -> ID Unique, pour les conflits
    ecartees: set[str] = set()          # chaines retirees pour DIVERGENCE reelle

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
        avancee = parr.get("vente") or parr.get("compromis") or parr.get("offre")
        if avancee is None:
            avancee = list(parr.values())[0]
        chaine = str(avancee.get("app_chaine_id") or "")
        dossier = avancee.get("app_dossier_id")
        if not chaine:
            notes["transaction SANS CHAINE"] += 1
            continue
        if dossier is None:
            notes["chaine SANS DOSSIER"] += 1
            continue

        noms = [case(l, "Négociateur %d" % i) for i in (1, 2, 3)]
        pcts = [nombre(case(l, "Pourcentage %d" % i)) for i in (1, 2, 3)]
        if not any(n for n in noms):
            notes["aucun negociateur au classeur"] += 1
            continue

        parts, pourquoi = nettoyer(noms, pcts)
        if pourquoi:
            notes["REFUS nettoyage : " + pourquoi.split(":")[0].strip()] += 1
            refus.append({"ID Unique": iu, "chaine": chaine, "etape": "nettoyage",
                          "motif": pourquoi, "classeur": " | ".join(
                              "%s=%s" % (n, "" if p is None else "%g" % p)
                              for n, p in zip(noms, pcts) if n or p is not None)})
            continue

        indice = nego_mandat.get(str(avancee.get("hektor_annonce_id") or ""), set())
        sur_la_chaine = {str(r.get("hektor_user_id") or "")
                         for r in deja.get(chaine, [])}
        resolus: dict[str, dict] = {}
        bloque = ""
        for nom, _p in parts:
            qui, motif = resoudre(nom, par_nom, indice, sur_la_chaine)
            if motif:
                bloque = "%s -> %s" % (nom, motif)
                break
            resolus[nom] = qui
        if bloque:
            court = bloque.split(":")[0].split("->")[-1].strip()
            notes["REFUS resolution : " + court] += 1
            refus.append({"ID Unique": iu, "chaine": chaine, "etape": "resolution",
                          "motif": bloque, "classeur": " | ".join(
                              "%s=%g" % (n, p) for n, p in parts)})
            continue

        cotes, pourquoi = decomposer(parts)
        if pourquoi:
            notes["REFUS decomposition : " + pourquoi.split("(")[0].strip()] += 1
            refus.append({"ID Unique": iu, "chaine": chaine, "etape": "decomposition",
                          "motif": pourquoi, "classeur": " | ".join(
                              "%s=%g" % (n, p) for n, p in parts)})
            continue

        # ⛔ GARDE ② : une saisie humaine ne se perd jamais.
        anciennes = deja.get(chaine, [])
        if any(str(r.get("origine") or "") == INTOUCHABLE for r in anciennes):
            notes["REFUS : la chaine porte une SAISIE humaine"] += 1
            refus.append({"ID Unique": iu, "chaine": chaine, "etape": "garde saisie",
                          "motif": "origine=saisie, intouchable", "classeur": ""})
            continue

        # ⭐⭐ DEUX LIGNES DU CLASSEUR SUR LA MEME CHAINE -- mesure du 13/11 :
        #   sur les 205 cas, 172 DISENT EXACTEMENT LA MEME CHOSE. Il n'y a rien
        #   a trancher la : on garde la premiere, et on le COMPTE A PART pour que
        #   le chiffre reste visible. Seules les 33 vraies divergences sont
        #   refusees -- elles sont listees dans
        #   notice/A5_CONFLITS_CLASSEUR_A_TRANCHER_2026-11-13.csv.
        # ⛔ On compare la DECOMPOSITION RESOLUE (personne + cote + part), pas le
        #   texte des cases : deux ecritures differentes qui donnent la meme
        #   repartition sont la meme chose, et c'est la repartition qu'on ecrit.
        signature = tuple((c, r, resolus[n]["hektor_user_id"], pct)
                          for c, r, n, pct in cotes)
        avant = {str(r.get("origine") or "(vide)") for r in anciennes}
        entree = {
            "id_unique": iu, "dossier": int(dossier),
            "signature": signature, "doublons": [],
            "quand": dernier_mouvement(l, idx),
            "avant": "+".join(sorted(avant)) if avant else "AUCUNE",
            "avant_n": len(anciennes),
            "lignes": [(cote, rang, resolus[nom]["hektor_user_id"],
                        resolus[nom]["nom_au_moment"], pct,
                        nom, resolus[nom].get("comment", ""))
                       for cote, rang, nom, pct in cotes],
        }

        if chaine in vu_chaine:
            garde = a_poser.get(chaine)
            if garde is not None and garde["signature"] == signature:
                notes["doublon du classeur : les deux lignes disent LA MEME CHOSE"] += 1
                garde["doublons"].append(iu)
            elif garde is None:
                # La chaine a deja ete retiree faute de pouvoir departager ses
                # lignes. Une troisieme ne la sauve pas : on refuse tout le lot.
                notes["REFUS : chaine deja ecartee, dates indepartageables"] += 1
                refus.append({"ID Unique": iu, "chaine": chaine, "etape": "conflit",
                              "motif": "chaine deja ecartee (indepartageable)",
                              "classeur": ""})
            elif entree["quand"] is None or garde["quand"] is None \
                    or entree["quand"] == garde["quand"]:
                # ⛔ LE SEUL CAS QUI RESTE UN REFUS : sans date lisible des deux
                #   cotes, ou a dates EGALES, la regle ne dit rien. On ne devine
                #   pas -- on retire la chaine et on la nomme.
                notes["REFUS : divergence aux dates INDEPARTAGEABLES"] += 1
                refus.append({"ID Unique": iu, "chaine": chaine, "etape": "conflit",
                              "motif": "divergence, dates indepartageables (l autre : %s)"
                                       % vu_chaine[chaine], "classeur": ""})
                a_poser.pop(chaine, None)
                ecartees.add(chaine)
            elif entree["quand"] > garde["quand"]:
                notes["divergence TRANCHEE : la ligne la plus recente gagne"] += 1
                entree["doublons"] = garde["doublons"]
                a_poser[chaine] = entree
                vu_chaine[chaine] = iu
            else:
                notes["divergence TRANCHEE : la ligne la plus recente gagne"] += 1
            continue

        vu_chaine[chaine] = iu
        a_poser[chaine] = entree

    # ⭐⭐ « ADDITIF ET CHIRURGICAL, JAMAIS DE REMPLACEMENT MASSIF » -- la regle
    #   du projet, appliquee au patch. Sans ce filtre, un second passage rejoue
    #   les 4 439 chaines deja posees pour en ajouter 30 : un delete + insert de
    #   9 100 lignes pour 65 de neuves.
    # ⭐ La MESURE du 14/11 a prouve que c'est sans danger de les laisser de
    #   cote : entre le 13 et le 14, sur les chaines communes, 0 a change et
    #   0 n'a disparu. Mais on ne s'appuie pas sur cette mesure -- on COMPARE
    #   chaine par chaine, ici, a chaque passage.
    if args.seulement_changees:
        # ⛔ L'ORIGINE FAIT PARTIE DE LA SIGNATURE, et l'oublier m'a coute un
        #   premier filtre trop large : 8 chaines ou Hektor avait DEJA devine la
        #   bonne repartition en sortaient du patch, et gardaient l'etiquette
        #   « hektor_partage_suppose » alors que LE CLASSEUR FAIT FOI. Meme
        #   valeur, mais une provenance moins sure -- et c'est la provenance
        #   qu'on lit a l'ecran et dans les audits.
        def signature_en_base(ch: str) -> tuple:
            return tuple(sorted(
                (str(r.get("cote") or ""), int(r.get("rang") or 0),
                 str(r.get("hektor_user_id") or ""), float(r.get("pourcentage") or 0),
                 str(r.get("origine") or ""))
                for r in deja.get(ch, [])))

        def signature_voulue(v: dict) -> tuple:
            return tuple(sorted(
                (str(cote), int(rang), str(uid), float(pct), ORIGINE)
                for cote, rang, uid, _nom, pct, _n, _c in v["lignes"]))

        inchangees = [ch for ch, v in a_poser.items()
                      if signature_en_base(ch) == signature_voulue(v)]
        for ch in inchangees:
            a_poser.pop(ch)
        print()
        print("  ⭐ PATCH CHIRURGICAL : %d chaine(s) sont DEJA EXACTEMENT ainsi en"
              % len(inchangees))
        print("     base -- elles sortent du patch, qui ne touchera que les autres.")

    # ------------------------------------------------ le compte rendu
    print()
    print("  CE QUI SERAIT POSE")
    print("  " + "=" * 68)
    cases = sum(len(v["lignes"]) for v in a_poser.values())
    print("  chaines : %d . lignes de repartition : %d" % (len(a_poser), cases))
    ecrase = Counter()
    for v in a_poser.values():
        ecrase[v["avant"]] += 1
    for k, n in ecrase.most_common():
        print("     remplace une repartition « %-24s » : %5d chaine(s)" % (k, n))
    plusieurs = sum(1 for v in a_poser.values()
                    if len({x[2] for x in v["lignes"]}) > 1)
    print("  dont A PLUSIEURS PERSONNES : %d chaines (nous n'en connaissions que 19)"
          % plusieurs)
    dbl = sum(len(v["doublons"]) for v in a_poser.values())
    if dbl:
        print("  ⭐ %d ligne(s) du classeur sont des DOUBLONS INOFFENSIFS : une autre"
              % dbl)
        print("     ligne vise la meme chaine et donne LA MEME repartition.")
    tranchees = sum(n for k, n in notes.items() if k.startswith("divergence TRANCHEE"))
    if tranchees:
        print("  ⭐⭐ %d ligne(s) DIVERGENTES ont ete TRANCHEES par la regle du"
              % tranchees)
        print("     DERNIER MOUVEMENT : la plus recente porte la repartition, celle")
        print("     qui est tombee n'a jamais encaisse de commission.")
    print()
    print("  CE QUI EST REFUSE -- et pourquoi")
    print("  " + "-" * 68)
    for k, n in notes.most_common():
        # ⚠ CE NE SONT PAS DES REFUS, et les melanger ici a deja trompe la
        #   lecture : les doublons et les divergences tranchees sont comptes
        #   au-dessus, et la ligne « total refuse » ne les porte pas non plus.
        if k.startswith("doublon du classeur") or k.startswith("divergence TRANCHEE"):
            continue
        print("     %-58s %5d" % (k[:58], n))
    print("  total refuse : %d ligne(s) du classeur" % len(refus))

    detail = RACINE / "notice" / ("A5_RAPATRIEMENT_REPARTITION_%s.csv" % date.today())
    with detail.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ID Unique", "chaine", "dossier", "avant", "cote", "rang",
                    "hektor_user_id", "nom", "pourcentage",
                    "nom au classeur", "resolu comment"])
        for ch, v in sorted(a_poser.items(), key=lambda kv: int(kv[0])):
            for cote, rang, uid, nom, pct, brut, comment in v["lignes"]:
                w.writerow([v["id_unique"], ch, v["dossier"], v["avant"],
                            cote, rang, uid, nom, "%g" % pct, brut, comment])
    refuses = RACINE / "notice" / ("A5_RAPATRIEMENT_REFUS_%s.csv" % date.today())
    with refuses.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";",
                           fieldnames=["ID Unique", "chaine", "etape", "motif",
                                       "classeur"])
        w.writeheader()
        for r in refus:
            w.writerow(r)
    print()
    print("  detail : %s" % detail)
    print("  refus  : %s" % refuses)

    if args.sql:
        chemin = ecrire_le_patch(a_poser, cases)
        print("  patch  : %s" % chemin)
        print()
        print("  ⛔ LE PATCH N'A PAS ETE JOUE. Il attend la relecture de Frederic.")
    else:
        print()
        print("  ⛔ A BLANC : rien n'est ecrit, et aucun patch depose (--sql pour l'avoir).")
    return 0


def ecrire_le_patch(a_poser: dict, cases: int) -> Path:
    """Depose le SQL : sauvegarde datee, puis remplacement chaine par chaine.

    ⛔⛔ LE PATCH PORTE SON « commit; » : le jouer « pour voir » LE COMMITE.
      Leçon du 13/11 (patch-avec-commit-joue-a-blanc-s-est-commite).
    """
    jour = str(date.today())
    sauve = "app_affaire_repartition_avant_classeur_" + jour.replace("-", "")
    chemin = RACINE / "supabase" / ("patch_repartition_classeur_%s.sql" % jour)
    chaines = ", ".join(sorted(a_poser, key=int))
    out: list[str] = []
    A = out.append
    A("-- RAPATRIEMENT DES POURCENTAGES DU CLASSEUR -> app_affaire_repartition")
    A("-- Depose le %s par phase2/checks/rapatrier_repartition_classeur.py" % jour)
    A("-- %d chaines, %d lignes. Regle : ENTREE 50 + SORTIE 50." % (len(a_poser), cases))
    A("-- Les chaines portant origine='saisie' ont ete ECARTEES en amont.")
    A("-- ATTENTION : ce fichier porte son propre commit. Le jouer, c'est ecrire.")
    A("")
    A("begin;")
    A("")
    A("-- (1) SAUVEGARDE DATEE, avant le premier geste (regle du projet).")
    A("create table if not exists public.%s as" % sauve)
    A("  select * from public.app_affaire_repartition where false;")
    A("insert into public.%s" % sauve)
    A("  select r.* from public.app_affaire_repartition r")
    A("  where r.app_chaine_id in (%s);" % chaines)
    A("")
    A("-- (2) LE GARDE-FOU, en base et pas seulement dans le script.")
    A("do $$")
    A("declare n int;")
    A("begin")
    A("  select count(*) into n from public.app_affaire_repartition")
    A("   where origine = 'saisie' and app_chaine_id in (%s);" % chaines)
    A("  if n > 0 then")
    A("    raise exception 'ARRET : % ligne(s) de SAISIE humaine dans le perimetre', n;")
    A("  end if;")
    A("end $$;")
    A("")
    A("-- (3) REMPLACEMENT : on retire l'ancienne repartition de ces chaines...")
    A("delete from public.app_affaire_repartition")
    A(" where app_chaine_id in (%s);" % chaines)
    A("")
    A("-- ... puis on pose celle du classeur.")
    A("insert into public.app_affaire_repartition")
    A("  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id,")
    A("   nom_au_moment, pourcentage, origine, ecrit_par)")
    A("values")
    vals: list[str] = []
    for ch in sorted(a_poser, key=int):
        v = a_poser[ch]
        for cote, rang, uid, nom, pct, _brut, _c in v["lignes"]:
            vals.append("  (%s, %s, '%s', %d, '%s', '%s', %g, '%s', '%s')"
                        % (ch, v["dossier"], cote, rang, uid.replace("'", "''"),
                           (nom or "").replace("'", "''"), pct, ORIGINE, ECRIT_PAR))
    for i, ligne in enumerate(vals):
        A(ligne + ("," if i < len(vals) - 1 else ";"))
    A("")
    A("-- (4) LES CONTROLES, DANS LA MEME TRANSACTION : un faux et tout est annule.")
    A("-- ⛔⛔ ILS SONT BORNES AUX CHAINES DE CE PATCH, et c'est un defaut trouve")
    A("--   le 14/11 en relisant un patch CHIRURGICAL : compte sur toute la table,")
    A("--   « n <> %d » voyait les 9 100 lignes deja posees la veille et le patch" % cases)
    A("--   echouait a coup sur. Un controle doit juger SA part, pas la table.")
    A("do $$")
    A("declare n int; m int;")
    A("begin")
    A("  select count(*) into n from public.app_affaire_repartition")
    A("   where origine = '%s' and app_chaine_id in (%s);" % (ORIGINE, chaines))
    A("  if n <> %d then" % cases)
    A("    raise exception 'ARRET : % lignes posees au lieu de " + str(cases) + "', n;")
    A("  end if;")
    A("  -- chaque cote doit faire exactement 50 sur chaque chaine touchee")
    A("  select count(*) into m from (")
    A("    select app_chaine_id, cote, sum(pourcentage) as s")
    A("      from public.app_affaire_repartition")
    A("     where origine = '%s' and app_chaine_id in (%s)" % (ORIGINE, chaines))
    A("     group by 1, 2) q")
    A("   where abs(s - 50) > 0.01;")
    A("  if m > 0 then")
    A("    raise exception 'ARRET : % cote(s) ne font pas 50', m;")
    A("  end if;")
    A("  raise notice 'POSE : % lignes, tous les cotes a 50', n;")
    A("end $$;")
    A("")
    A("commit;")
    A("")
    A("-- RETOUR ARRIERE -- ⛔⛔ IL NE JUGE QUE SA PART.")
    A("--   Le premier jet disait « delete where origine = '%s' » TOUT COURT :" % ORIGINE)
    A("--   joue apres un patch chirurgical, il aurait efface LES 9 100 LIGNES")
    A("--   d'un lot precedent pour n'en remettre que %d chaine(s)." % len(a_poser))
    A("--   begin;")
    A("--   delete from public.app_affaire_repartition")
    A("--    where app_chaine_id in (%s);" % chaines)
    A("--   insert into public.app_affaire_repartition")
    A("--     select * from public.%s;" % sauve)
    A("--   commit;")
    A("--   ⚠ La sauvegarde ne porte QUE ces chaines : apres ce retour arriere,")
    A("--     elles retrouvent EXACTEMENT leur etat d'avant, et rien d'autre ne bouge.")
    chemin.write_text("\n".join(out) + "\n", encoding="utf-8")
    return chemin


if __name__ == "__main__":
    raise SystemExit(main())
