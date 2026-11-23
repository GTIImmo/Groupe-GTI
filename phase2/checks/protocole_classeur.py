#!/usr/bin/env python3
"""LE PROTOCOLE DU CLASSEUR -- toutes ses lignes, chacune avec son verdict ou son motif (chantier classeur, ⑳, 22/11/2026).

Son mot du 22/11 (« le plan change ») : « LE PROTOCOLE PORTE SUR MES 4 794 LIGNES. TOUTES. [...] Chaque ligne ressort
avec son verdict [...], la preuve de ce verdict, nommee [...], ou, a defaut, le motif pour lequel elle n'est pas
tranchee. [...] verdicts + motifs = 4 794. » Et sa regle d'architecture (2 bis) : LE CODE FAIT LE TRAVAIL SUR TOUTES LES
LIGNES, dans un ordre ecrit, rejouable a l'identique, avec des temoins ; l'agent ne reflechit que la ou le code
s'arrete, PAR MOTIF, et ce qu'il en sort est UNE REGLE, qui redescend dans le code et se rejoue sur toutes les lignes.

⛔ LECTURE SEULE. Rien dans le Sheet (un GET), rien chez Hektor, rien en base (le pooler en `read only`, le registre
local en `mode=ro`). Tout ce que ce script produit va dans le cache du chantier :
    C:\\Hektor\\chantier_classeur_q6_cache\\protocole\\

LES ETAPES -- une par appel, `python -u` :
  image                  fige une IMAGE datee : le Sheet lu en direct, une copie du registre local (sans payload_json),
                         le gel lu chez Supabase, avec une empreinte par morceau. Chaque passage part d'une image :
                         la meme image redonne les memes verdicts (le premier temoin).
  bien <annonce>         LA LECTURE DU BIEN ENTIER (le socle du geste 5) : toutes ses pieces (copie ou vraie, par LA
                         fonction unique), toutes ses chaines, toutes ses lignes et PAR QUOI elles y sont rattachees,
                         tout ce que le gel en dit. Ecrit aussi un JSON a cote de l'image.
  passage [--note X]     un PASSAGE complet sur toutes les lignes de l'image : chaque ligne recoit son verdict ou son
                         motif, dans la table `verdict` du socle ; le passage ECHOUE si le compte ne boucle pas.
  comparer P1 P2         les verdicts qui ont change entre deux passages (pour sa regle : « tu me dis combien de
                         verdicts ont change », y compris parmi ceux deja rendus).
  compter [P]            les comptes d'un passage, par verdict et par motif.
  rapport [P]            le verdict de CHAQUE ligne en CSV (une piece par ligne du CSV), et les attentes PAR MOTIF
                         avec trois exemples chacune (les premieres par numero de ligne : rejouable).
  temoins                fabrique les TEMOINS du protocole (temoins.json) depuis les decisions deja rendues : la V3,
                         ses 132 coupes, les 29 faibles, les 20 pieces a part, les jumelles, le bien 39845. Chaque
                         passage se compare ensuite a eux, ecart par ecart (table `temoin` du socle).
  mouvement [de] [a]     CE QUE LA NUIT A DEPLACE entre deux images (son mot, reponses 20, point 5 : « MESURE CHAQUE
                         MATIN ») : le Sheet (lignes, cases lues), le registre (champ par champ), le gel (liens), et
                         les biens qui ont bouge. `comparer` entre deux images s'en sert : chaque verdict change est
                         dit venu de la nuit (sa ligne ou son bien a bouge) ou du code. Temoin positif : 22/11.
  avis [P]               LA SENTINELLE DES 2 560 NUMEROS de app_classeur_avis (son mot, reponses 21, § 2 ; 21 bis, § 2 :
                         « garde-le comme SENTINELLE, meme s'il n'est pas un juge ») : une photo de la table (lecture
                         seule), sa mesure refaite (meme / autre / plusieurs dossiers), le passage P contre chaque
                         numero -- celles qui collaient et que le protocole contredit EN TETE -- puis CE QUI A BOUGE
                         depuis la mesure precedente, ligne par ligne.
  LE MATIN : image, puis MOUVEMENT (ce que la nuit a deplace -- a dire AVANT toute comparaison, son mot 21 bis), puis
             passage, puis avis (la sentinelle), puis comparer <reference> <nouveau>.

Option commune : --image <dossier> (sinon : l'image la plus recente).
Les portes et le rejeu exact de l'etiquette : protocole_portes.py (le vrai chainage rejoue sur une copie de l'image).

v2 (22/11) : la regle P1 VALIDEE (REGLES_VALIDEES) ; le motif PIECE_SUPPRIMEE_FIGEE (trouve par le rejeu exact) ;
  les variantes R7a et R7b proposees (jamais appliquees sans son mot).
v3 (22/11 apres-midi, son mot « reponses 21 ») : R7a et R7b VALIDEES ; R7b met la piece de cote AVEC son dossier
  d'aujourd'hui (sa regle : elle garde son ancien numero) ; SES_DECISIONS (DJEBBOUR, trois affaires) remplace la coupe
  des 132 dans les temoins ; l'etape `avis` (le temoin des 2 560 numeros) ; le numero de dossier a cote de l'etiquette.
v3.1 (22/11 soir, son mot « reponses 21 bis ») : AUCUNE REGLE NE CHANGE. Le temoin des 2 560 devient une SENTINELLE (ce
  qui bouge depuis la mesure precedente) ; le passage NOMME les lignes en attente dont le dossier est fige par R7b
  (« figees ne veut pas dire reglees »). Voisins : protocole_les_numeros_neufs.py (ancien -> neuf, en clair),
  protocole_r7b_reversible.py (defaire R7b), sauvegarde_datee_classeur.py (la sauvegarde qui se relit).

v3.2 (23/11, son mot (12) : « trancher les 44 », pas desserrer le verrou) : la VARIANTE R7c proposee -- passage 24 sans elle = passage 23 (0 change) ; passage 25 avec elle : 10 pieces mises de
  cote, 12 lignes quittent le verrou, 0 deja rendu ne change, memes 19 ecarts de temoins.
v4 (23/11, son message : « Ensuite R8, puis R7c, puis le passage, PUIS le rejeu exact ») : R8 et R7c VALIDEES
  (REGLES_VALIDEES). R8 : un bien sans aucune piece -> RIEN_A_ETIQUETER, hors du reste a vider ; sauf si la triple
  preuve (date exacte + honoraires + vendeur) trouve son affaire sur UN autre bien -> AFFAIRE_SUR_UN_AUTRE_BIEN.

LES EPREUVES (le plan du 22/11, notice/PROTOCOLE_TOUTES_LES_LIGNES_PLAN_AVIS_DELAI_2026-11-22.md). Version 0 de ce
22/11 : E1 et E2 sont codees ; une ligne qui les passe recoit le motif declare `E3_A_CODER` -- le compte boucle des la
version 0, et chaque epreuve codee ensuite remplace ce motif par un verdict ou par un motif plus precis.
  E1 la ligne : un ID Unique, une seule fois ; elle nomme UN bien (gel, Mandat, product_ref, Lien CRM)
  E2 l'inventaire du bien : chaque piece est copie ou vraie (piece_copie_ou_vraie) ; un bien sans vraie piece ne decide
     d'aucune etiquette
  E3..E9 : la preuve au jour exact puis prix + honoraires, l'attribution, les contradictions, le crible du nom, son
     verrou permanent (aucune etiquette si le dossier peut encore recevoir une piece plus petite), le verrou des deux
     lignes (sauf exceptions nommees), le verdict -- A CODER (lundi 23 dans le delai envoye)

CODES : 0 fait et vert . 1 un controle a echoue (le compte ne boucle pas, un temoin crie) . 2 pas pu lire (jamais un vert)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import coupe_preuve_interne as K  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402

DOSSIER = Path(r"C:\Hektor\chantier_classeur_q6_cache\protocole")
IMAGES = DOSSIER / "images"
SOCLE = DOSSIER / "socle.sqlite"
BASE = RACINE / "phase2" / "phase2.sqlite"
CODE = [Path(__file__).resolve(), Path(K.__file__).resolve(), Path(PC.__file__).resolve()]
VERSION = "v4 -- 23/11 : R8 et R7c validees (son message du 23/11)"

# les colonnes de son Sheet que le protocole lit (et rien d'autre) -- la lecture du bien les montre telles quelles
COLONNES_LUES = ["Mandat", "product_ref", "Lien CRM", "Etat Actuel", "Offre Achat", "Compromis", "Signé",
                 "Vente Prévue", "Vente Fixée", "Signée", "Vente Réglée", "Annulée", "Prix", "Commission TTC",
                 "Acquéreur", "Vendeur", "Ville"]

# LE CATALOGUE DES MOTIFS -- un motif est DECLARE ici avant d'etre utilise (un code inconnu fait echouer le passage)
MOTIFS = {
    "SANS_ID_UNIQUE": ("E1", "la ligne a du contenu mais pas d'ID Unique : l'ecrivain ne pourrait pas l'adresser"),
    "ID_EN_DOUBLE": ("E1", "le meme ID Unique est sur plusieurs lignes du Sheet"),
    "SANS_BIEN": ("E1", "la ligne ne nomme aucun bien (ni gel, ni Mandat unique, ni product_ref, ni Lien CRM)"),
    "PLUSIEURS_BIENS": ("E1", "la ligne nomme plusieurs biens"),
    "BIEN_SANS_VRAIE_PIECE": ("E2", "le bien n'a que des copies C5 : aucune ne decide d'une etiquette (regle du 19/11)"),
    "BIEN_SANS_PIECE": ("E2", "le bien que la ligne nomme n'a AUCUNE piece chez nous (ni vraie, ni copie)"),
    "A_SA_DECISION": ("E1", "mise de cote par son mot (bien 39845, 22/11) : il veut voir ces affaires lui-meme"),
    # R8 (validee le 23/11) : un bien sans AUCUNE piece n'a pas de dossier a nommer. ⛔ RIEN_A_ETIQUETER n'est PAS une
    #   attente : la ligne SORT DU RESTE A VIDER (le passage la compte a part), et elle est rejugee a chaque passage.
    "RIEN_A_ETIQUETER": ("E2", "REGLE R8 : le bien nomme n'a AUCUNE piece chez nous, et aucune piece d'un autre bien ne "
                               "porte son affaire -- pas de dossier a nommer, rien a ecrire ; hors du reste a vider"),
    "AFFAIRE_SUR_UN_AUTRE_BIEN": ("E2", "le bien nomme n'a aucune piece, mais UNE piece d'un autre bien porte la date "
                                        "exacte d'une de ses cases, ses honoraires ET son vendeur : son affaire est la "
                                        "-- a sa decision"),
    "E3_A_CODER": ("E3", "la ligne passe E1 et E2 ; les epreuves E3 a E9 ne sont pas encore codees (version 0)"),
    # v1 (22/11) -- E3 a E9
    "AUCUNE_PIECE_PROUVEE": ("E3", "aucune vraie piece du bien n'est prouvee a cette ligne (ni date au jour exact, ni "
                                   "prix + honoraires, ni par sa chaine)"),
    "SES_PIECES_A_PART": ("E4", "les pieces que le gel lui donne sont toutes a part : aucune preuve interne ne les lui "
                                "donne, ni a une autre ligne"),
    "SES_PIECES_AILLEURS": ("E4", "les pieces que le gel lui donne sont prouvees a une AUTRE ligne du bien"),
    "COPIE_SEULE": ("E3", "la ligne ne tient que des copies C5 : aucune ne decide d'une etiquette"),
    "DEUX_LIGNES_UN_DOSSIER": ("E8", "son verrou : une autre de ses lignes tombe dans le meme dossier (hors exception "
                                     "nommee)"),
    "VERROU_PIECE_PLUS_PETITE": ("E7", "son verrou permanent : une vraie piece du bien, a part, plus petite que la plus "
                                       "petite de la ligne, peut encore rejoindre son dossier"),
    # v2 (22/11) -- trouve par le REJEU EXACT (protocole_portes.py, rejeu E) : 6 lignes tranchees que la nuit ne peut pas
    #   realiser. Le chainage NE RECALCULE PAS une piece supprimee chez Hektor (« la trace garde son dossier ») : ni un
    #   rattachement ni une coupe ne la trouvent (« transaction introuvable »)
    "PIECE_SUPPRIMEE_FIGEE": ("E9", "son morceau tient une piece SUPPRIMEE CHEZ HEKTOR (le chainage la fige dans son "
                                    "ancien dossier) et ses pieces sont dans PLUSIEURS dossiers : aucune porte ne peut les "
                                    "reunir"),
}
# a part par SA decision (20/11 soir, B3) -- la meme liste que la V3
A_PART_PAR_DECISION = {14033: "B3, sa decision du 20/11 soir"}

# ⛔ LES REGLES PROPOSEES -- jamais appliquees sans son mot. Un passage lance avec --variantes X,Y est marque
#   « VARIANTE NON VALIDEE » : il sert a mesurer ce qu'une regle changerait (comparer), rien d'autre.
#   Une variante VALIDEE par son mot quitte cette liste et passe dans REGLES_VALIDEES : elle joue alors a chaque passage,
#   et le passage qui suit est rejoue sur TOUTES les lignes (« tu me dis combien de verdicts ont change »).
REGLES_VALIDEES = {
    "P1": ("une ligne que le gel ET le mandat mettent sur le meme bien, et le seul product_ref sur un autre, est sur le "
           "bien du gel et du mandat (deux sources independantes contre une)",
           "son mot du 22/11, reponses au rapport 20, point 1 : « LA REGLE P1 : OUI. [...] Applique-la. »"),
    "R7a": ("une piece a part, plus petite, qui est DEJA dans le dossier ou sont TOUTES les pieces de la ligne, et qui "
            "n'est possible pour AUCUNE autre ligne, ne retient pas la ligne au verrou E7 : le dossier ne peut plus la "
            "recevoir, il l'a deja. Elle reste a part (jamais donnee a la ligne), et ON NE COUPE PAS le dossier entre "
            "elles : l'etiquette de la ligne est celle du dossier tel qu'il est",
            "son mot du 22/11, reponses au rapport 21, point 1 : « R7a : OUI. Applique-la. [...] elle ne menace donc "
            "aucun numero partage. On la laisse a part et on ne coupe pas le dossier. »"),
    "R7b": ("une piece a part, plus petite, possible pour CETTE seule ligne et qui est dans un AUTRE dossier, est MISE DE "
            "COTE : isolee dans un dossier a elle seule (le fichier des coupes), elle ne peut plus rejoindre aucun dossier "
            "-- donc elle ne retient plus la ligne. ⛔ ET ELLE GARDE SON ANCIEN NUMERO DE DOSSIER (sa regle, qui ne se "
            "negocie pas) : il est ecrit sur sa ligne du fichier des coupes, et le rejeu exact dit si la pose de nuit le "
            "lui laisse",
            "son mot du 22/11, reponses au rapport 21, point 2 : « R7b : OUI. Applique-la. ⚠ AVEC MA REGLE, et elle ne "
            "se negocie pas : une piece mise de cote GARDE SON ANCIEN NUMERO DE DOSSIER. On ne supprime jamais une "
            "part, on l'isole. »"),
    "R8": ("une ligne dont le bien n'a AUCUNE piece chez nous n'a pas de dossier a nommer : rien a ecrire dans sa case A ; "
           "elle sort du reste a vider (RIEN_A_ETIQUETER) et elle est rejugee a chaque passage -- une piece qui arrive la "
           "fait rentrer. ⭐ SAUF si UNE piece d'un autre bien porte la date exacte d'une de ses cases, ses honoraires "
           "(= sa Commission TTC) ET son vendeur parmi ses mandants : elle attend alors, nommee (AFFAIRE_SUR_UN_AUTRE_BIEN) "
           "-- trouve le 23/11 par les lectures chez Hektor : 3 ventes reglees vivent sur un autre bien",
           "son message du 23/11 : « Ensuite R8, puis R7c, puis le passage, PUIS le rejeu exact -- et rien ne s'ecrit "
           "avant que ce rejeu soit vert. »"),
    "R7c": ("une piece a part, plus petite, possible pour PLUSIEURS lignes, qu'AUCUNE preuve ne peut donner a aucune "
            "d'elles -- ni une date au jour exact sur une de leurs cases, ni le prix + honoraires d'une ligne du bien, ni "
            "une case de date VIDE de son genre qu'on pourrait remplir de sa date -- et qui n'est dans le dossier "
            "d'AUCUNE de ces lignes, est TRANCHEE : MISE DE COTE comme R7b (isolee AVEC son dossier d'aujourd'hui, elle "
            "garde son ancien numero) -- elle ne retient plus aucune ligne",
            "son message du 23/11 : « Ensuite R8, puis R7c, puis le passage, PUIS le rejeu exact »"),
}
VARIANTES = {
    "R4": "une piece A PART (sans preuve) ne peut jamais rejoindre plus tard un dossier dont elle deviendrait la plus "
          "petite (sa regle R4 du 20/11) -- elle ne retient donc pas la ligne au verrou E7",
    # R9 (23/11, le paquet COPIE_SEULE : 23 lignes, UNE cause) -- PROPOSEE, jamais appliquee sans son mot.
    "R9": "une ligne qui ne tient que sa copie C5 recoit LA vraie piece que son gel lui donne, quand cette piece est A "
          "PART (aucune preuve ne la donne a aucune ligne), que le gel ne la donne a AUCUNE autre ligne, que ses "
          "honoraires sont la « Commission TTC » de la ligne, qu'AUCUNE autre ligne n'a son prix + honoraires, et qu'elle "
          "n'est pas une de SES 20 pieces a part (son mot du 21/11)",
    "R9b": "R9 quand les honoraires de la piece sont INCONNUS (une offre, un compromis sans net vendeur) : son MONTANT est le "
           "« Prix » de la ligne, et AUCUNE autre ligne du bien n'a ce meme Prix",
    # R7c a quitte cette liste le 23/11 (son message) : elle est dans REGLES_VALIDEES
}
# R7a et R7b ont quitte cette liste le 22/11 (son mot, reponses au rapport 21) : elles sont dans REGLES_VALIDEES
VARIANTES_ACTIVES: set = set()


def joue(regle: str) -> bool:
    """Une regle joue si elle est VALIDEE (toujours) ou si un passage de mesure l'active (--variantes)."""
    return regle in REGLES_VALIDEES or regle in VARIANTES_ACTIVES


# LES PIECES MISES DE COTE par R7b dans le dernier passage : piece -> son ancien dossier, l'etiquette simulee, le reste
MISES_DE_COTE: dict = {}
# son mot du 22/11, point 4 : « Le bien 39845 : je veux toujours voir ces deux affaires moi-meme. Mets-les-moi de cote »
BIENS_A_SA_DECISION = {"39845": "son mot du 22/11, point 4 -- les deux affaires du bien, il les voit lui-meme"}
# SES DECISIONS DE LIGNE (son message et son mot du 23/11 (15)) : la ligne est sur CE bien -- elles remplacent ce que le
#   gel, le Mandat, le product_ref et le Lien CRM nommaient. ⛔ Jamais par le nom de l'acquereur (Hektor reutilise le contact
#   de l'acheteur precedent) : le bien, le montant, les dates.
LIGNE_SUR_LE_BIEN_PAR_DECISION = {
    "I3TFR2KG": ("48340", "sa decision du 23/11 : trois dates exactes (offre 22/10/2019, compromis 19/11/2019, vente "
                          "24/04/2020), 6 000 EUR des deux cotes, mandant CHAPPAT (la ligne : CHAPAT)"),
    "54376c72": ("54734", "sa decision du 23/11 : l'offre 33147, 13 800 EUR = 12 000 + 1 800 a l'euro, DAUPHIN des deux "
                          "cotes, mandat de vente 18053 (la ligne porte le mandat de recherche 18993)"),
    "9O6NKRIJ": ("52931", "sa decision du 23/11 : le mandat de vente 18014 EST le bien 52931 (archive, clos, sans piece) -- "
                          "R8, elle rentre seule si une piece arrive"),
}
# ses pieces donnees par decision (une preuve qu'il a validee et que les epreuves ne savent pas lire) : piece -> ligne
PIECE_DONNEE_PAR_DECISION = {
    30830: ("54376c72", "sa decision du 23/11 : 13 800 EUR = 12 000 + 1 800 a l'euro, DAUPHIN des deux cotes -- ⚠ la "
                        "case « Offre Achat » dit 11/11/2026, le commentaire de la meme ligne « 18.11 », l'offre est "
                        "proposee le 18/11 a 14:46 : on ne corrige pas une date, on corrige les lecteurs"),
}
RIEN_A_ETIQUETER_PAR_DECISION = {
    "JZ9693S0": "sa decision du 23/11 : ni bien (mandat 92560 inconnu), ni nom ; ⚠ le fil FACTURE + AVOIR (GGTI00002792 / "
                "AVR00000465) dit que l'affaire a existe en comptabilite ; « reglee » au commentaire contre « Annulee » a "
                "l'etat : signale, pas tranche",
}

# LES SOURCES DES TEMOINS -- des decisions deja rendues, jamais recalculees ici
NOTICE = RACINE / "notice"
SRC_V3 = NOTICE / "TEMPS13_DETACHEMENTS_V3_REFAIT_PRET_2026-11-22.csv"
SRC_803 = NOTICE / "TEMPS6_LES_803_LIGNES_NON_ECRITES_ET_CE_QUI_LES_DEBLOQUE_2026-11-19.csv"
SRC_132 = NOTICE / "TEMPS8_DECISION_DU_20_11_LES_132_COUPES_DATEES_VALIDEES_2026-11-20.csv"
SRC_V3_CALCUL = Path(r"C:\Hektor\chantier_classeur_q6_cache\v3_calcul.json")
TEMOINS = DOSSIER / "temoins.json"
# les jumelles : ses exceptions nommees (son mot du 22/11, point 3) et celle deja connue (§ 18.9, DEBARD)
JUMELLES = [
    {"nom": "VIALLARD", "bien": "9748", "lignes": ["3308P0UX", "YRUF0S9H"], "source": "son mot du 22/11, point 3"},
    {"nom": "PAOLONE", "bien": "41467", "lignes": ["O6R10ZQA", "T2GZOY5O"], "source": "son mot du 22/11, point 3"},
    {"nom": "DEBARD", "bien": "41481", "lignes": ["5QE9107L", "ZW7MKTWH"], "source": "§ 18.9 (mesure du 10/11)"},
]
# SES DECISIONS RENDUES APRES LES TEMOINS -- elles REMPLACENT, pour leurs lignes, ce qu'un temoin plus ancien attendait
#   (une decision ne se recalcule jamais ici : elle se recopie, avec sa source)
SES_DECISIONS = {
    "DJEBBOUR (bien 30717)": {
        "source": "son mot du 22/11, reponses au rapport 21, point 3 : « DEUX AFFAIRES. [...] ET LA 3575 EST UNE "
                  "TROISIEME, SEPAREE [...] CE BIEN PORTE TROIS AFFAIRES : HUGON COTTIN 2023, DJEBBOUR 2024, DJEBBOUR 2025 »",
        "remplace": "sa coupe des 132 du 20/11 (un seul morceau 14940 14941 14942 14944 pour 3461 et 155)",
        "lignes": {"ZE9WZW22": [14939, 14943], "Q3KTCMVB": [14941], "DKTK22F2": [14940, 14942, 14944]}},
}
ATTENDU_TEMOINS = {"v3_lignes": 456, "v3_morceau": 431, "v3_a_part": 20, "v3_attend_avec_sa_ligne": 3,
                   "v3_exception_nommee": 2, "coupes_132": 132, "lignes_132": 274, "coupes_29": 29, "lignes_29": 57,
                   "a_part_20": 20}


def dire(s: str = "") -> None:
    print(s, flush=True)


def md5_fichier(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def md5_code() -> str:
    h = hashlib.md5()
    for p in CODE:
        h.update(p.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


# ═════════════════════════════════════════════ L'IMAGE ═════════════════════════════════════════════════════════════
def pooler():
    import psycopg2
    from phase2.sync import push_upgrade_to_supabase as PU
    PU.load_env_files(PU.DEFAULT_ENV_FILES)
    u = urllib.parse.urlparse(os.environ["DATABASE_URL"])
    cn = psycopg2.connect(host=os.environ["SUPABASE_POOLER_HOST"], port=5432, dbname="postgres",
                          user="postgres.dwaqxfrinihnychuoptk", password=urllib.parse.unquote(u.password),
                          connect_timeout=15, sslmode="require")
    cu = cn.cursor()
    cu.execute("set transaction read only")
    return cn, cu


def etape_image() -> int:
    t0 = datetime.now()
    nom = t0.strftime("%Y-%m-%d_%H%M%S")
    d = IMAGES / nom
    d.mkdir(parents=True, exist_ok=False)
    dire("IMAGE %s" % d)
    # 1. le Sheet, lu en direct (un GET)
    import apparier_classeur as ac
    ac.MORCEAUX_DE_NOM = True
    ac.load_env_file(RACINE / ".env")
    try:
        entete, lignes = ac.lire_classeur()
    except Exception as e:  # noqa: BLE001
        dire("⛔ le Sheet n'a pas pu etre lu (%s) -- pas d'image (code 2)" % str(e).splitlines()[0][:160])
        return 2
    k_al, k_ab = entete.index("ID Unique"), entete.index("Acquéreur")
    par_id, sans_id, vides = defaultdict(list), [], 0
    for num, l in lignes:
        l = [("" if x is None else str(x)) for x in list(l)] + [""] * (len(entete) - len(l))
        i = l[k_al].strip()
        if i:
            par_id[i].append({"num": num, "row": l[:len(entete)], "noms_ab": sorted(ac.mots_propres(l[k_ab]))})
        elif any(x.strip() for x in l):
            sans_id.append({"num": num, "row": l[:len(entete)]})
        else:
            vides += 1
    sheet = {"lu_le": t0.isoformat(timespec="seconds"), "entete": entete, "lignes_brutes": len(lignes),
             "vides": vides, "sans_id": sans_id, "par_id": par_id}
    (d / "sheet.json").write_text(json.dumps(sheet, ensure_ascii=False), encoding="utf-8")
    dire("   Sheet : %d lignes brutes ; %d ID Unique distincts (dont %d en double) ; %d lignes avec contenu SANS ID ; "
         "%d lignes vides" % (len(lignes), len(par_id), sum(1 for v in par_id.values() if len(v) > 1), len(sans_id),
                              vides))
    # 2. le registre local, copie (sans payload_json) -- lecture seule de la source
    reg = d / "registre.sqlite"
    con = sqlite3.connect("file:%s?mode=rwc" % reg.as_posix(), uri=True)
    con.execute("attach database ? as src", ("file:%s?mode=ro" % BASE.as_posix(),))
    cols = [r[1] for r in con.execute("pragma src.table_info(app_affaire_ledger)") if r[1] != "payload_json"]
    con.execute("create table app_affaire_ledger as select %s from src.app_affaire_ledger" % ", ".join(cols))
    con.execute("create table app_mandat_register_current as select numero_mandat, hektor_annonce_id, numero_dossier "
                "from src.app_mandat_register_current")
    con.commit()
    con.execute("detach database src")
    n_reg = con.execute("select count(*) from app_affaire_ledger").fetchone()[0]
    try:
        N = PC.natures(con)
    except PC.PieceIncoherente as e:
        dire("⛔ registre incoherent -- la fonction unique refuse : %s (code 1)" % e)
        con.close()
        return 1
    con.close()
    dire("   registre : %d pieces (%d copies, %d vraies)" % (n_reg, sum(v == PC.COPIE for v in N.values()),
                                                              sum(v == PC.VRAIE for v in N.values())))
    # 3. le gel, chez Supabase (lecture seule)
    try:
        cn, cu = pooler()
        cu.execute("select id_unique, app_affaire_id, role, confiance, preuves, ligne_classeur from app_classeur_lien "
                   "order by id_unique collate \"C\", app_affaire_id")
        gel = [[i, int(a), ro, cf, p, lc] for i, a, ro, cf, p, lc in cu.fetchall()]
        cu.execute("select count(*), md5(string_agg(id_unique||':'||app_affaire_id||':'||role, ',' "
                   "order by id_unique collate \"C\", app_affaire_id)) from app_classeur_lien")
        n_gel, emp_gel = cu.fetchone()
        cn.rollback()
        cn.close()
    except Exception as e:  # noqa: BLE001
        dire("⛔ le gel n'a pas pu etre lu (%s) -- image incomplete (code 2)" % str(e).splitlines()[0][:160])
        return 2
    if n_gel != len(gel):
        dire("⛔ le gel a bouge pendant la lecture (%d contre %d) (code 2)" % (n_gel, len(gel)))
        return 2
    (d / "gel.json").write_text(json.dumps({"n": n_gel, "empreinte": emp_gel, "liens": gel}, ensure_ascii=False,
                                           default=str), encoding="utf-8")
    dire("   gel : %d liens, empreinte %s" % (n_gel, emp_gel))
    # 4. la photo au format de l'outil de coupe (une ligne par ID Unique : la PREMIERE, les doublons sont un motif)
    photo = {"lu_le": sheet["lu_le"], "entete": entete,
             "lignes": {i: v[0] for i, v in par_id.items()}, "tx": {}, "gel": [[i, a, cf] for i, a, _r, cf, *_ in gel]}
    (d / "t6_photo.json").write_text(json.dumps(photo, ensure_ascii=False), encoding="utf-8")
    man = {"fait_le": t0.isoformat(timespec="seconds"), "version": VERSION, "code": md5_code(),
           "gel": {"n": n_gel, "empreinte": emp_gel}, "registre_pieces": n_reg,
           "fichiers": {f: md5_fichier(d / f) for f in ("sheet.json", "registre.sqlite", "gel.json", "t6_photo.json")}}
    (d / "manifeste.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    dire("IMAGE FAITE en %.0f s : %s" % ((datetime.now() - t0).total_seconds(), d))
    return 0


def image_choisie(nom: str | None) -> Path:
    if nom:
        p = Path(nom)
        return p if p.is_absolute() else IMAGES / nom
    imgs = sorted(p for p in IMAGES.iterdir() if (p / "manifeste.json").exists()) if IMAGES.exists() else []
    if not imgs:
        raise SystemExit("⛔ aucune image -- lancer d'abord : protocole_classeur.py image")
    return imgs[-1]


def verifier_image(d: Path) -> dict:
    """L'image n'a pas bouge depuis qu'elle a ete faite (empreinte de chaque morceau)."""
    man = json.loads((d / "manifeste.json").read_text(encoding="utf-8"))
    for f, e in man["fichiers"].items():
        if md5_fichier(d / f) != e:
            raise SystemExit("⛔ l'image %s a bouge : %s n'a plus son empreinte" % (d.name, f))
    return man


class Image:
    """Une image figee : le Sheet, le registre, le gel -- et l'outil de coupe charge DESSUS (jamais sur le vivant)."""

    def __init__(self, d: Path):
        self.d = d
        self.man = verifier_image(d)
        self.sheet = json.loads((d / "sheet.json").read_text(encoding="utf-8"))
        g = json.loads((d / "gel.json").read_text(encoding="utf-8"))
        self.gel = g["liens"]
        K.CACHE, K.BASE = d, d / "registre.sqlite"          # l'outil de coupe lit la photo ET le registre de l'image
        self.D = K.Donnees()
        con = sqlite3.connect("file:%s?mode=ro" % (d / "registre.sqlite").as_posix(), uri=True)
        con.row_factory = sqlite3.Row
        self.pieces = {int(r["app_affaire_id"]): dict(r) for r in con.execute("select * from app_affaire_ledger")}
        con.close()
        self.nature = {a: PC.nature(a, p["transaction_origine"], p["hektor_affaire_id"]) for a, p in self.pieces.items()}
        self.gel_par_ligne = defaultdict(list)
        self.gel_par_piece = defaultdict(list)
        for i, a, ro, cf, pr, lc in self.gel:
            self.gel_par_ligne[i].append({"piece": a, "role": ro, "confiance": cf, "preuves": pr, "ligne": lc})
            self.gel_par_piece[a].append(i)
        self.biens_de_ligne = defaultdict(set)
        for b, ls in self.D.lignes_bien.items():
            for i in ls:
                self.biens_de_ligne[i].add(b)
        # SES DECISIONS DE LIGNE (23/11) : la ligne est sur CE bien, et sur lui seul
        for i, (b, _pourquoi) in LIGNE_SUR_LE_BIEN_PAR_DECISION.items():
            if i not in self.sheet["par_id"]:
                continue
            for b_ in self.biens_de_ligne.get(i, set()):
                self.D.lignes_bien[b_].discard(i)
            self.biens_de_ligne[i] = {b}
            self.D.lignes_bien[b].add(i)
            self.D.rattache_par[(b, i)].add("sa_decision")


# ═════════════════════════════════════════ LA LECTURE DU BIEN ENTIER ═══════════════════════════════════════════════
def noms(js) -> list[str]:
    try:
        v = json.loads(js) if js else []
    except (TypeError, ValueError):
        return []
    out = []
    for x in v if isinstance(v, list) else [v]:
        if isinstance(x, dict):
            n = " ".join(str(x.get(k) or "") for k in ("nom", "prenom")).strip() or str(x.get("name") or "")
            if n:
                out.append(n)
    return out


def lire_bien(I: Image, bien: str) -> dict:
    """Tout ce qu'on sait d'un bien, sans rien decider : pieces, chaines, lignes (et par quoi), gel."""
    bien = str(bien)
    ids = sorted(I.D.par_bien.get(bien, []))
    pieces = []
    for a in ids:
        p, r = I.pieces[a], I.D.REG[a]
        pieces.append({
            "piece": a, "nature": I.nature[a], "genre": p["kind"], "etat": p["state"],
            "date": str(r["date"]) if r["date"] else None, "montant": r["montant"], "honoraires": r["hon"],
            "numero_hektor": p["hektor_affaire_id"], "mandat": p["numero_mandat"], "chaine": p["app_chaine_id"],
            "etiquette": p["app_dossier_uuid"], "acquereurs": noms(p["acquereurs_json"]),
            "lignes_du_gel": sorted(I.gel_par_piece.get(a, []))})
    chaines = defaultdict(lambda: {"pieces": [], "etiquettes": set(), "lignes_du_gel": set()})
    for x in pieces:
        c = chaines[str(x["chaine"])]
        c["pieces"].append(x["piece"])
        c["etiquettes"].add(x["etiquette"])
        c["lignes_du_gel"] |= set(x["lignes_du_gel"])
    lignes = []
    for i in sorted(I.D.lignes_bien.get(bien, set())):
        v = I.D.LIG[i]
        lignes.append({
            "id_unique": i, "num": v["num"], "rattachee_par": sorted(I.D.rattache_par.get((bien, i), set())),
            "autres_biens": sorted(I.biens_de_ligne[i] - {bien}),
            "colonnes": {c: I.D.case(i, c) for c in COLONNES_LUES if c in I.D.col},
            "gel": sorted(I.gel_par_ligne.get(i, []), key=lambda g: g["piece"])})
    # ce que le gel dit, et qui sort du bien : une ligne du bien liee a une piece d'un AUTRE bien
    hors = [{"ligne": l["id_unique"], "piece": g["piece"], "bien_de_la_piece": I.D.REG[g["piece"]]["bien"]}
            for l in lignes for g in l["gel"] if g["piece"] in I.D.REG and I.D.REG[g["piece"]]["bien"] != bien]
    return {"bien": bien, "image": I.d.name, "pieces": pieces,
            "chaines": {c: {"pieces": v["pieces"], "etiquettes": sorted(e for e in v["etiquettes"] if e),
                            "lignes_du_gel": sorted(v["lignes_du_gel"])} for c, v in sorted(chaines.items())},
            "lignes": lignes, "gel_hors_du_bien": hors,
            "comptes": {"pieces": len(pieces), "vraies": sum(x["nature"] == PC.VRAIE for x in pieces),
                        "copies": sum(x["nature"] == PC.COPIE for x in pieces), "chaines": len(chaines),
                        "lignes": len(lignes)}}


def montrer_bien(b: dict) -> None:
    c = b["comptes"]
    dire("BIEN %s (image %s) : %d pieces (%d vraies, %d copies) sur %d chaine(s) ; %d ligne(s) du Sheet"
         % (b["bien"], b["image"], c["pieces"], c["vraies"], c["copies"], c["chaines"], c["lignes"]))
    dire("  PIECES")
    for x in b["pieces"]:
        dire("    %-8s %-5s %-9s %-9s %-10s %10s hon=%-8s chaine=%s etiq=%s gel=%s %s" % (
            x["piece"], x["nature"], x["genre"], x["etat"], x["date"] or "-", x["montant"], x["honoraires"],
            x["chaine"], (x["etiquette"] or "-")[:8], ",".join(x["lignes_du_gel"]) or "-", "/".join(x["acquereurs"])[:40]))
    dire("  CHAINES")
    for ch, v in b["chaines"].items():
        dire("    %s : pieces %s ; etiquette(s) %s ; lignes du gel %s" % (
            ch, v["pieces"], [e[:8] for e in v["etiquettes"]], v["lignes_du_gel"]))
    dire("  LIGNES")
    for l in b["lignes"]:
        col = {k: v for k, v in l["colonnes"].items() if str(v).strip()}
        dire("    %s (ligne %s), rattachee par %s%s" % (l["id_unique"], l["num"], "+".join(l["rattachee_par"]),
                                                       (" ; AUSSI les biens %s" % l["autres_biens"]) if l["autres_biens"] else ""))
        dire("      " + " | ".join("%s=%s" % (k, str(v)[:40]) for k, v in col.items()))
        for g in l["gel"]:
            dire("      gel : %s (%s, %s)" % (g["piece"], g["role"], g["confiance"]))
    if b["gel_hors_du_bien"]:
        dire("  ⚠ GEL HORS DU BIEN : %s" % b["gel_hors_du_bien"])


def etape_bien(I: Image, bien: str) -> int:
    b = lire_bien(I, bien)
    montrer_bien(b)
    sortie = DOSSIER / "biens" / ("bien_%s_%s.json" % (bien, I.d.name))
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(json.dumps(b, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    dire("-> %s" % sortie)
    return 0


# ═════════════════════════════════════════════ LE SOCLE DE MESURE ═════════════════════════════════════════════════
SCHEMA = """
create table if not exists passage (
  id integer primary key, image text not null, image_code text not null, code text not null, version text not null,
  debut text not null, fin text, lignes integer, tranchees integer, en_attente integer, boucle integer, note text);
create table if not exists verdict (
  passage integer not null references passage(id), id_unique text not null, num integer,
  biens text not null,                 -- JSON : les biens que la ligne nomme
  verdict text not null check (verdict in ('TRANCHEE', 'ATTENTE')),
  etiquette text,                      -- TRANCHEE seulement
  pieces text,                         -- JSON : les pieces qui lui appartiennent (TRANCHEE)
  preuves text,                        -- JSON : la preuve NOMMEE de chaque piece (quelle date / quel montant / quelle colonne)
  motif text,                          -- ATTENTE seulement : un code du catalogue
  motif_texte text, epreuve text not null,
  primary key (passage, id_unique),
  check ((verdict = 'TRANCHEE' and etiquette is not null and pieces is not null and preuves is not null and motif is null)
      or (verdict = 'ATTENTE' and motif is not null)));
create table if not exists motif (code text primary key, epreuve text not null, libelle text not null);
create table if not exists temoin (passage integer not null, temoin text not null, id_unique text, attendu text,
  obtenu text, ecart integer not null);
"""


def socle() -> sqlite3.Connection:
    DOSSIER.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(SOCLE)
    con.executescript(SCHEMA)
    con.executemany("insert into motif (code, epreuve, libelle) values (?, ?, ?) on conflict(code) do update set "
                    "epreuve = excluded.epreuve, libelle = excluded.libelle",
                    [(k, e, l) for k, (e, l) in MOTIFS.items()])
    con.commit()
    return con


STOP_VENDEUR = {"NAN", "IND", "MME", "MLLE", "MR", "SCI", "ET", "DE", "LA", "LE", "DU", "DES", "CONSORTS",
                "SUCCESSION", "INDIVISION"}


def affaire_sur_un_autre_bien(I: Image, i: str) -> dict:
    """R8 : la TRIPLE PREUVE d'une affaire portee par un autre bien -- une piece (de n'importe quel bien) dont la date
    est au jour exact d'une case de la ligne de son genre, dont les honoraires sont la « Commission TTC » de la ligne, et
    dont les mandants portent un nom du « Vendeur » de la ligne. Rend {bien: preuve}. Temoin du 23/11 (lignes TRANCHEES) :
    elle donne leur bien SEUL 3 831 fois, 15 fois avec un autre ; sur les 23 « bien sans piece » : 3 (les ventes reglees
    QXDW8EQA -> 2070, 2U5QPKRC -> 37875, MQ6H8TVQ -> 52460, verifiees chez Hektor)."""
    D = I.D
    if not hasattr(I, "_par_date"):
        I._par_date = defaultdict(list)
        for a_, r_ in D.REG.items():
            if r_["date"]:
                I._par_date[(r_["genre"], r_["date"])].append(a_)
    try:
        com = round(float(str(D.case(i, "Commission TTC")).replace(" ", "").replace(",", ".")))
    except ValueError:
        return {}
    noms = {x for x in re.findall(r"[A-ZÀ-Ü][A-ZÀ-Ü'\-]{2,}", D.case(i, "Vendeur").upper()) if x not in STOP_VENDEUR}
    out = {}
    if not noms:
        return out
    for g, cols in K.COLS_DATE.items():
        for c in cols:
            d = K.d_sheet(D.case(i, c))
            if not d:
                continue
            for a_ in I._par_date.get((g, d), []):
                h = D.REG[a_]["hon"]
                mand = str(I.pieces[a_].get("mandants_json") or "").upper()
                if h is not None and round(h) == com and any(n in mand for n in noms):
                    out.setdefault(D.REG[a_]["bien"], "%s %d du %s = colonne « %s », honoraires %d = Commission TTC, "
                                                      "vendeur parmi ses mandants" % (g, a_, d, c, com))
    return out


def juger_ligne(I: Image, i: str, v: dict) -> dict:
    """LES EPREUVES, dans l'ordre. Version 0 : E1 et E2."""
    biens = sorted(I.biens_de_ligne.get(i, set()))
    base = {"id_unique": i, "num": v["num"], "biens": biens}

    def attente(code: str, texte: str = "") -> dict:
        return dict(base, verdict="ATTENTE", motif=code, motif_texte=texte or MOTIFS[code][1], epreuve=MOTIFS[code][0])
    # E1
    if len(I.sheet["par_id"][i]) > 1:
        return attente("ID_EN_DOUBLE", "ID Unique sur les lignes %s" % [x["num"] for x in I.sheet["par_id"][i]])
    if i in RIEN_A_ETIQUETER_PAR_DECISION:
        return attente("RIEN_A_ETIQUETER", RIEN_A_ETIQUETER_PAR_DECISION[i])
    if not biens:
        return attente("SANS_BIEN")
    if len(biens) > 1 and bien_par_p1(I, i):
        biens = [bien_par_p1(I, i)]              # LA REGLE P1, validee le 22/11 (REGLES_VALIDEES)
        base["biens"] = biens
    if len(biens) > 1:
        return attente("PLUSIEURS_BIENS", "biens %s, par %s" % (biens, {b: sorted(I.D.rattache_par.get((b, i), set()))
                                                                          for b in biens}))
    b = biens[0]
    if b in BIENS_A_SA_DECISION:
        return attente("A_SA_DECISION", BIENS_A_SA_DECISION[b])
    # E2
    vraies = [a for a in I.D.par_bien.get(b, []) if I.nature[a] == PC.VRAIE]
    if not I.D.par_bien.get(b):
        if joue("R8"):
            autre = affaire_sur_un_autre_bien(I, i)
            if len(autre) == 1:
                (bb, preuve), = autre.items()
                return attente("AFFAIRE_SUR_UN_AUTRE_BIEN", "bien %s : aucune piece ; son affaire est sur le bien %s -- %s"
                               % (b, bb, preuve))
            return attente("RIEN_A_ETIQUETER", "bien %s : aucune piece, et aucune piece d'un autre bien ne porte son "
                                               "affaire (%s)" % (b, "aucune" if not autre else "%d biens" % len(autre)))
        return attente("BIEN_SANS_PIECE", "bien %s : aucune piece" % b)
    if not vraies:
        return attente("BIEN_SANS_VRAIE_PIECE", "bien %s : %d copie(s), aucune vraie piece"
                       % (b, len(I.D.par_bien.get(b, []))))
    return None                     # E1 et E2 passees : la ligne se juge AVEC SON BIEN ENTIER (juger_bien)


def supprimee_chez_hektor(p: dict) -> bool:
    """La meme condition que le chainage (affaire_ledger.recalculer_les_chaines) : un numero Hektor ET absente chez
    Hektor -> la piece n'est plus recalculee, elle garde son dossier."""
    return bool(str(p.get("hektor_affaire_id") or "").strip()) and str(p.get("present_in_hektor")) in ("0", "false",
                                                                                                       "False")


def bien_par_p1(I: Image, i: str) -> str | None:
    """LA REGLE P1 (validee le 22/11) : deux biens nommes, l'un par le gel ET le mandat, l'autre par le SEUL product_ref
    -> le bien du gel et du mandat. Sinon : None (la ligne reste PLUSIEURS_BIENS)."""
    bs = sorted(I.biens_de_ligne.get(i, set()))
    if len(bs) != 2:
        return None
    par = {b: I.D.rattache_par.get((b, i), set()) for b in bs}
    forts = [b for b in bs if {"gel", "mandat"} <= par[b]]
    if len(forts) == 1 and par[[b for b in bs if b != forts[0]][0]] == {"product_ref"}:
        return forts[0]
    return None


def r_bien(I: Image, i: str) -> str:
    """Le bien d'une ligne qui a passe E1 (un seul, ou celui que la regle P1 a choisi)."""
    bs = I.biens_de_ligne[i]
    if len(bs) == 1:
        return next(iter(bs))
    return bien_par_p1(I, i)


def exception_nommee(gl) -> str | None:
    """Un morceau a plusieurs lignes n'echappe au verrou E8 que si TOUTES ses lignes sont une paire de jumelles nommee."""
    for j in JUMELLES:
        if set(gl) <= set(j["lignes"]):
            return "%s (%s)" % (j["nom"], j["source"])
    return None


def preuve_nommee(I: Image, a: int, gl, quoi: str) -> str:
    """LA PREUVE NOMMEE d'une piece : quelle date, quel montant, quelle colonne de quelle ligne."""
    D, p = I.D, I.D.REG[a]
    tete = "%d %s %s du %s" % (a, p["genre"], p["etat"] or "", p["date"] or "?")
    if I.nature[a] == PC.COPIE:
        return "%s : copie creee depuis %s (C5) -- suit sa ligne, ne decide jamais de l'etiquette" % (
            tete, ",".join(sorted(D.gel_t.get(a, set()))))
    if quoi.startswith(K.PROUVEE_DATE):
        for i in sorted(gl):
            for c in K.COLS_DATE.get(p["genre"], []):
                if p["date"] and K.d_sheet(D.case(i, c)) == p["date"]:
                    return "%s = colonne « %s » de %s (« %s »)%s" % (tete, c, i, D.case(i, c).strip(),
                                                                       quoi[len(K.PROUVEE_DATE):])
    if quoi == K.PROUVEE_PH:
        for i in sorted(gl):
            if D.touche_ph(a, i):
                return "%s : prix %s = l'offre de %s (« Prix » %s, ou offre Hektor du jour de « Offre Achat ») ET " \
                       "honoraires %s = « Commission TTC » (%s)" % (tete, p["montant"], i, D.case(i, "Prix").strip() or "-",
                                                                     p["hon"], D.case(i, "Commission TTC").strip())
    return "%s : %s" % (tete, quoi)


_A_PART_20: set = set()


def les_20_a_part() -> set:
    """SES 20 PIECES A PART (« a part » restreinte aux 20, son mot du 21/11) -- une decision rendue : aucune regle ne les
    donne a une ligne. Lues ou les temoins les lisent (SRC_V3_CALCUL, « a20 »)."""
    if not _A_PART_20:
        _A_PART_20.update(int(a) for _b, a, _w in json.loads(SRC_V3_CALCUL.read_text(encoding="utf-8"))["a20"])
    return _A_PART_20


def regle_r9(I: Image, b: str, lignes_b: set, r: dict) -> dict:
    """R9 : pour chaque ligne du bien qui ne tient que des copies C5, la vraie piece que SON GEL lui donne -- si elle est a
    part, que le gel ne la donne a aucune autre ligne, que ses honoraires sont la Commission TTC de la ligne, et qu'aucune
    autre ligne n'a son prix + honoraires. Rend {piece: (ligne, preuve)}. Temoin du 23/11 (toutes les lignes) : quand le
    gel nomme une vraie piece pour une seule ligne et que ses honoraires sont la commission, la preuve la donne a CETTE
    ligne 4 208 fois, a une AUTRE 8 fois, et la laisse a part 53 fois."""
    D = I.D
    out = {}
    for gl, ids in r["morceaux"].items():
        if any(I.nature[q] == PC.VRAIE for q in ids) or len(gl) != 1:
            continue
        i = next(iter(gl))
        vraies_gel = sorted({int(g["piece"]) for g in I.gel_par_ligne.get(i, [])
                             if int(g["piece"]) in D.REG and D.REG[int(g["piece"])]["bien"] == b
                             and I.nature.get(int(g["piece"])) == PC.VRAIE})
        if len(vraies_gel) != 1:
            continue
        a = vraies_gel[0]
        if a not in r["apart"] or [x for x in I.gel_par_piece.get(a, []) if x != i]:
            continue
        if a in les_20_a_part():          # sa decision du 21/11 : elle reste a part (le temoin a_part_20 l'a crie le 23/11)
            continue
        try:
            com = round(float(str(D.case(i, "Commission TTC")).replace(" ", "").replace(",", ".")))
        except ValueError:
            continue
        h = D.REG[a]["hon"]
        if h is None:
            # R9b (variante) : honoraires inconnus -- le MONTANT est le Prix de la ligne, et lui seul l'a
            if not joue("R9b"):
                continue
            prix = nombre_case(D.case(i, "Prix"))
            m = D.REG[a]["montant"]
            if prix is None or m is None or round(m) != prix or any(nombre_case(D.case(j, "Prix")) == prix
                                                                     for j in lignes_b if j != i):
                continue
            out[a] = (i, "REGLE R9b (variante) : le gel du 16/11 ne la donne qu'a cette ligne ; honoraires inconnus, son "
                         "montant %d = le « Prix » de la ligne, qu'aucune autre ligne du bien n'a" % prix)
            continue
        if not joue("R9") or round(h) != com or any(D.touche_ph(a, j) for j in lignes_b if j != i):
            continue
        out[a] = (i, "REGLE R9 (variante) : le gel du 16/11 ne la donne qu'a cette ligne, et ses honoraires %d = sa "
                     "« Commission TTC » ; aucune autre ligne n'a son prix + honoraires" % com)
    return out


def nombre_case(s) -> int | None:
    try:
        return round(float(str(s).replace(" ", "").replace(",", ".")))
    except ValueError:
        return None


def juger_bien(I: Image, b: str, a_juger: set, perimetre: str) -> list[dict]:
    """E3 a E9 sur UN BIEN ENTIER : la coupe (K.couper_le_bien, les regles deja validees), puis pour chaque ligne :
    ses pieces, son verrou des deux lignes (E8), son verrou permanent (E7), son etiquette (la pose de nuit simulee)."""
    D = I.D
    lignes_b = set(D.lignes_bien.get(b, set()))
    S = {a: I.pieces[a]["app_chaine_id"] for a in D.par_bien.get(b, [])}
    if perimetre == "bien":
        X = sorted(D.par_bien.get(b, []))
    else:                           # « chaines » : comme « ou ca tombe » le 20/11 -- les chaines que le gel touche
        lies = {a for i in lignes_b for a in D.gel_l.get(i, set()) if a in D.REG and D.REG[a]["bien"] == b}
        ch_t = {S[a] for a in lies if a in S}
        X = sorted(a for a in D.par_bien.get(b, []) if S.get(a) in ch_t)
    donnee = {a_: l_ for a_, (l_, _w) in PIECE_DONNEE_PAR_DECISION.items()}
    r = K.couper_le_bien(D, b, lignes_b, S, X, A_PART_PAR_DECISION, donnee)
    if joue("R9") or joue("R9b"):
        # VARIANTE R9 (proposee le 23/11, jamais appliquee sans son mot) -- voir VARIANTES
        r9 = regle_r9(I, b, lignes_b, r)
        if r9:
            donnee.update(r9)
            r = K.couper_le_bien(D, b, lignes_b, S, X, A_PART_PAR_DECISION, donnee)
    # VARIANTE R7a (proposee, jamais appliquee sans son mot) : la piece a part plus petite DEJA dans le dossier de toute
    #   la ligne, possible pour elle seule -- on ne coupe pas le dossier entre elles (elle reste a part, jamais donnee)
    deja = {}
    if joue("R7a"):
        for gl, ids in r["morceaux"].items():
            hk_ = [a for a in ids if I.nature[a] == PC.VRAIE]
            ch_m = {S.get(a) for a in ids}
            if hk_ and len(ch_m) == 1:
                deja[gl] = sorted(a for a in r["apart"] if I.nature[a] == PC.VRAIE and a < min(hk_)
                                  and gl in r["possibles"][a] and len(r["possibles"][a]) == 1 and S.get(a) in ch_m)
    isoles, isoles_r7c = set(), set()
    if joue("R7b"):
        for gl, ids in r["morceaux"].items():
            hk_ = [a for a in ids if I.nature[a] == PC.VRAIE]
            ch_m = {S.get(a) for a in ids}
            if hk_:
                isoles |= {a for a in r["apart"] if I.nature[a] == PC.VRAIE and a < min(hk_) and gl in r["possibles"][a]
                           and len(r["possibles"][a]) == 1 and S.get(a) not in ch_m and a not in deja.get(gl, [])}
    if joue("R7c"):
        # REGLE R7c (validee le 23/11, son message : « Ensuite R8, puis R7c ») -- voir REGLES_VALIDEES
        for a in sorted(r["apart"]):
            poss = r["possibles"].get(a, [])
            if I.nature[a] != PC.VRAIE or a in isoles or len(poss) < 2:
                continue                              # une seule ligne possible : c'est R7a ou R7b, deja juges
            lignes_poss = set().union(*poss)
            reg = D.REG[a]
            cols = K.COLS_DATE.get(reg["genre"], [])
            date_exacte = bool(reg["date"]) and any(K.d_sheet(D.case(i, c)) == reg["date"] for i in lignes_poss
                                                    for c in cols)
            prix_hon = any(D.touche_ph(a, i) for i in lignes_b)
            case_vide = bool(reg["date"]) and any(all(not D.case(i, c).strip() for c in cols) for i in lignes_poss)
            dans_un_dossier = any(S.get(q) == S.get(a) for gl in poss for q in r["morceaux"].get(gl, []))
            retient = any(a < min([q for q in r["morceaux"].get(gl, []) if I.nature[q] == PC.VRAIE] or [0])
                          for gl in poss)
            if retient and not (date_exacte or prix_hon or case_vide or dans_un_dossier):
                isoles.add(a)
                isoles_r7c.add(a)
    # E9 : la pose de nuit simulee sur le decoupage (chaque morceau devient un dossier ; le reste garde sa chaine)
    ch_new = {}
    for gl, ids in r["morceaux"].items():
        for a in ids + deja.get(gl, []):
            ch_new[a] = ("morceau", min(ids))
    # R7b, AVEC SA REGLE (« une piece mise de cote GARDE SON ANCIEN NUMERO DE DOSSIER ») : elle est mise de cote AVEC son
    #   dossier d'aujourd'hui -- tout ce qu'aucun morceau ne prend -- et ce dossier est fige tel quel par le fichier des
    #   coupes. ⛔ La mettre de cote SEULE couperait son dossier quand il porte une autre piece : mesure du 22/11, 2 des
    #   13 (biens 37243 et 54990) -- l'autre piece aurait recu un numero NEUF, contre sa regle.
    groupe_isole = {}
    for a in sorted(isoles):
        g_ = groupe_isole.setdefault(S[a], sorted(q for q in D.par_bien.get(b, []) if S.get(q) == S[a]
                                                  and q not in ch_new))
        for q in g_:
            ch_new[q] = ("isole", S[a])
    for a in D.par_bien.get(b, []):
        ch_new.setdefault(a, ("chaine", S[a]))
    lab1 = K.pose_de_nuit({a: I.pieces[a]["app_dossier_uuid"] for a in ch_new}, ch_new)
    # R7b, SA REGLE : la piece mise de cote garde-t-elle son ancien numero ? (la pose de nuit simulee le dit ; le rejeu
    #   exact de protocole_portes.py le redit sur le vrai chainage)
    for a in sorted(isoles):
        ancien = I.pieces[a]["app_dossier_uuid"]
        g_ = groupe_isole[S[a]]
        hors = sorted(q for q in D.par_bien.get(b, []) if S.get(q) == S.get(a) and q not in g_)
        MISES_DE_COTE[a] = {"bien": b, "ancien_uuid": ancien, "ancien_numero": I.pieces[a]["app_dossier_numero"],
                            "ancienne_chaine": S.get(a), "etiquette_simulee": lab1[a],
                            "garde_son_numero": lab1[a] == ancien, "mise_de_cote_avec": [q for q in g_ if q != a],
                            "regle": "R7c" if a in isoles_r7c else "R7b",
                            "pieces_du_dossier_prises_par_un_morceau": hors,
                            "etiquettes_du_groupe": sorted({str(lab1[q]) for q in g_}),
                            "groupe": g_, "lignes_du_gel": {str(q): sorted(I.gel_par_piece.get(q, [])) for q in g_}}
    out = []
    for i in sorted(a_juger):
        base = {"id_unique": i, "num": D.LIG[i]["num"], "biens": [b]}

        def attente(code, texte, epreuve=None):
            return dict(base, verdict="ATTENTE", motif=code, motif_texte=texte, epreuve=epreuve or MOTIFS[code][0])
        gls = [gl for gl in r["morceaux"] if i in gl]
        if not gls:
            gel_b = sorted(a for a in D.gel_l.get(i, set()) if a in D.REG and D.REG[a]["bien"] == b
                           and I.nature[a] == PC.VRAIE)
            ailleurs = {a: sorted(r["va"][a]) for a in gel_b if a in r["va"]}
            if gel_b and all(a in r["apart"] for a in gel_b):
                out.append(attente("SES_PIECES_A_PART", "; ".join("%d : %s" % (a, r["apart"][a]) for a in gel_b)))
            elif gel_b and ailleurs:
                out.append(attente("SES_PIECES_AILLEURS", "; ".join("%d -> %s" % (a, "+".join(v))
                                                                     for a, v in ailleurs.items())))
            else:
                out.append(attente("AUCUNE_PIECE_PROUVEE", "bien %s : %d piece(s) jugee(s), aucune pour elle ; gel %s"
                                   % (b, len(X), gel_b or "aucun")))
            continue
        gl = gls[0]
        ids = r["morceaux"][gl]
        hk = [a for a in ids if I.nature[a] == PC.VRAIE]
        if not hk:
            out.append(attente("COPIE_SEULE", "morceau %s" % ids))
            continue
        figees = [a for a in ids if supprimee_chez_hektor(I.pieces[a])]
        if figees and len({S.get(a) for a in ids}) > 1:
            out.append(attente("PIECE_SUPPRIMEE_FIGEE", "supprimees chez Hektor : %s ; ses pieces sont dans %d dossiers "
                               "(%s)" % (figees, len({S.get(a) for a in ids}), sorted({S.get(a) for a in ids}))))
            continue
        exc = exception_nommee(gl) if len(gl) > 1 else None
        if len(gl) > 1 and not exc:
            out.append(attente("DEUX_LIGNES_UN_DOSSIER", "avec %s ; morceau %s" % ("+".join(sorted(gl - {i})), ids)))
            continue
        m = min(hk)
        bloque = [] if "R4" in VARIANTES_ACTIVES else \
            sorted(a for a in r["apart"] if I.nature[a] == PC.VRAIE and a < m and gl in r["possibles"][a]
                   and a not in deja.get(gl, []) and a not in isoles)
        if bloque:
            out.append(attente("VERROU_PIECE_PLUS_PETITE", "plus petite de la ligne %d ; a part et plus petites : %s"
                               % (m, "; ".join("%d (%s)" % (a, r["apart"][a]) for a in bloque))))
            continue
        neutres = sorted(a for a in r["apart"] if gl in r["possibles"][a] and a not in deja.get(gl, [])
                         and a not in isoles)
        preuves = [preuve_nommee(I, a, gl, r["preuve"].get(a, "")) for a in ids]
        if neutres:
            preuves.append("a part sans effet sur l'etiquette (son critere 2) : %s" % " ".join(map(str, neutres)))
        mis_de_cote = sorted(a for a in isoles if a < m and gl in r["possibles"][a])
        if mis_de_cote:
            if any(a in isoles_r7c for a in mis_de_cote):
                preuves.append("a part TRANCHEE PAR LA REGLE R7c (validee le 23/11) -- aucune preuve ne peut la donner a "
                               "aucune de ses lignes possibles, hors de leurs dossiers : %s" % " ".join(
                                   "%d" % a for a in mis_de_cote if a in isoles_r7c))
            preuves.append("a part MISE DE COTE avec son dossier d'aujourd'hui, possible pour elle seule, hors de son "
                           "dossier (REGLE R7b, validee le 22/11 ; elle garde son ancien numero : %s) : %s" % (", ".join(
                               "%d -> %s (dossier fige : %s)" % (a, I.pieces[a]["app_dossier_numero"] or "aucun",
                                                                  " ".join(map(str, groupe_isole[S[a]])))
                               for a in mis_de_cote), " ".join("%d" % a for a in mis_de_cote)))
        if deja.get(gl):
            preuves.append("a part deja dans son dossier, possible pour elle seule (REGLE R7a, validee le 22/11) : %s" % " ".join(
                "%d" % a for a in deja[gl]))
        if exc:
            preuves.append("exception nommee : %s -- %s" % (exc, "+".join(sorted(gl))))
        if len(I.biens_de_ligne.get(i, set())) > 1:
            autre = sorted(I.biens_de_ligne[i] - {b})
            preuves.append("son bien %s par la regle P1 (gel + mandat) ; ecarte : %s (product_ref seul) -- %s"
                           % (b, "+".join(autre), REGLES_VALIDEES["P1"][1]))
        out.append(dict(base, verdict="TRANCHEE", etiquette=lab1[m], pieces=ids, preuves=preuves, epreuve="E9"))
    return out


def etape_passage(I: Image, note: str, perimetre: str = "bien", variantes: set | None = None) -> int:
    VARIANTES_ACTIVES.clear()
    VARIANTES_ACTIVES.update(variantes or ())
    MISES_DE_COTE.clear()
    if VARIANTES_ACTIVES - set(VARIANTES):
        raise SystemExit("⛔ variante inconnue : %s" % sorted(VARIANTES_ACTIVES - set(VARIANTES)))
    if VARIANTES_ACTIVES:
        note = "⛔ VARIANTE NON VALIDEE %s -- %s" % ("+".join(sorted(VARIANTES_ACTIVES)), note)
    con = socle()
    debut = datetime.now().isoformat(timespec="seconds")
    cur = con.execute("insert into passage (image, image_code, code, version, debut, note) values (?, ?, ?, ?, ?, ?)",
                      (I.d.name, I.man["code"], md5_code(), VERSION + " / perimetre " + perimetre
                       + (" / VARIANTE " + "+".join(sorted(VARIANTES_ACTIVES)) if VARIANTES_ACTIVES else ""), debut,
                       note))
    pid = cur.lastrowid
    rangs, par_bien = [], defaultdict(set)
    for i, vs in sorted(I.sheet["par_id"].items()):
        r = juger_ligne(I, i, vs[0])
        if r is None:
            par_bien[r_bien(I, i)].add(i)
        else:
            rangs.append(r)
    for b in sorted(par_bien, key=lambda x: int(x) if x.isdigit() else 0):
        rangs.extend(juger_bien(I, b, par_bien[b], perimetre))
    for x in I.sheet["sans_id"]:
        rangs.append({"id_unique": "#%d" % x["num"], "num": x["num"], "biens": [], "verdict": "ATTENTE",
                      "motif": "SANS_ID_UNIQUE", "motif_texte": MOTIFS["SANS_ID_UNIQUE"][1], "epreuve": "E1"})
    inconnus = sorted({r["motif"] for r in rangs if r.get("motif") and r["motif"] not in MOTIFS})
    con.executemany(
        "insert into verdict (passage, id_unique, num, biens, verdict, etiquette, pieces, preuves, motif, motif_texte, "
        "epreuve) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [(pid, r["id_unique"], r["num"], json.dumps(r["biens"]), r["verdict"], r.get("etiquette"),
          json.dumps(r["pieces"]) if r.get("pieces") is not None else None,
          json.dumps(r["preuves"], ensure_ascii=False) if r.get("preuves") is not None else None,
          r.get("motif"), r.get("motif_texte"), r["epreuve"]) for r in rangs])
    # LE COMPTE QUI BOUCLE : une ligne du Sheet (avec contenu) = un verdict, ni plus ni moins
    attendu = len(I.sheet["par_id"]) + len(I.sheet["sans_id"])
    n, tr, at = con.execute("select count(*), sum(verdict='TRANCHEE'), sum(verdict='ATTENTE') from verdict "
                            "where passage=?", (pid,)).fetchone()
    tr, at = tr or 0, at or 0
    boucle = (n == attendu == tr + at) and not inconnus
    con.execute("update passage set fin=?, lignes=?, tranchees=?, en_attente=?, boucle=? where id=?",
                (datetime.now().isoformat(timespec="seconds"), n, tr, at, int(boucle), pid))
    con.commit()
    dire("PASSAGE %d sur l'image %s (%s)" % (pid, I.d.name, VERSION))
    dire("   lignes du Sheet avec contenu : %d (%d ID Unique distincts + %d sans ID) ; verdicts ecrits %d"
         % (attendu, len(I.sheet["par_id"]), len(I.sheet["sans_id"]), n))
    dire("   TRANCHEES %d + EN ATTENTE %d = %d -- %s" % (tr, at, tr + at, "LE COMPTE BOUCLE" if boucle else
                                                          "⛔ LE COMPTE NE BOUCLE PAS"))
    r8 = con.execute("select count(*) from verdict where passage=? and motif='RIEN_A_ETIQUETER'", (pid,)).fetchone()[0]
    if r8:
        dire("   ⭐ dont RIEN A ETIQUETER (regle R8, hors du reste a vider) %d -> LE RESTE A VIDER : %d" % (r8, at - r8))
    if inconnus:
        dire("   ⛔ motifs non declares au catalogue : %s" % inconnus)
    for m, k in con.execute("select motif, count(*) from verdict where passage=? and verdict='ATTENTE' group by 1 "
                            "order by 2 desc", (pid,)):
        dire("      %-24s %5d  %s" % (m, k, MOTIFS.get(m, ("", "?"))[1][:90]))
    # LES TEMOINS : chaque famille, accord / ecart / attend (un temoin qui attend n'est JAMAIS un accord)
    tm = ecarts_temoins(I, con, pid)
    con.commit()
    crie = False
    for fam, c in sorted(tm.items()):
        dire("   temoin %-14s accord %4d . ECART %4d . attend %4d" % (fam, c["accord"], c["ecart"], c["attend"]))
        crie |= c["ecart"] > 0
    con.close()
    if MISES_DE_COTE:
        g = sum(1 for x in MISES_DE_COTE.values() if x["garde_son_numero"])
        dire("   R7b : %d piece(s) mise(s) de cote ; %d gardent leur ancien numero dans la pose simulee, %d en recevraient un "
             "NEUF (voir mises_de_cote_passage_%d.json)" % (len(MISES_DE_COTE), g, len(MISES_DE_COTE) - g, pid))
        (DOSSIER / ("mises_de_cote_passage_%d.json" % pid)).write_text(json.dumps(
            {str(a): x for a, x in MISES_DE_COTE.items()}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        # SON MOT (reponses 21 bis, point 2 b) : « CES DEUX LIGNES RESTENT DANS LE RESTE A VIDER. Figees ne veut pas
        #   dire reglees. » -- les lignes EN ATTENTE dont le gel tient une piece d'un dossier fige par R7b, NOMMEES a
        #   chaque passage (affichage seul : aucune regle, aucun verdict ne change)
        v_de = {r["id_unique"]: r["verdict"] for r in rangs}
        num_fige = {q: x["ancien_numero"] for x in MISES_DE_COTE.values() for q in x["groupe"]}
        att_f = defaultdict(set)
        for i_, gs in I.gel_par_ligne.items():
            for g_ in gs:
                if g_["piece"] in num_fige and v_de.get(i_) == "ATTENTE":
                    att_f[i_].add(num_fige[g_["piece"]])
        dire("   R7b -- FIGEES N'EST PAS REGLEES : %d ligne(s) EN ATTENTE portent un dossier fige ; elles restent dans le "
             "reste a vider : %s" % (len(att_f), " . ".join("%s (%s)" % (i_, "+".join(sorted(n_))) for i_, n_ in
                                                             sorted(att_f.items())) or "aucune"))
    if crie:
        dire("   ⛔ un temoin crie : voir la table `temoin` du socle (passage %d)" % pid)
    return 0 if boucle and not crie else 1


def etape_comparer(p1: int, p2: int) -> int:
    con = socle()
    a = {i: (v, e, m) for i, v, e, m in con.execute("select id_unique, verdict, etiquette, motif from verdict "
                                                    "where passage=?", (p1,))}
    b = {i: (v, e, m) for i, v, e, m in con.execute("select id_unique, verdict, etiquette, motif from verdict "
                                                    "where passage=?", (p2,))}
    chg = sorted(i for i in set(a) & set(b) if a[i] != b[i])
    rendus = [i for i in chg if a[i][0] == "TRANCHEE"]
    dire("COMPARER %d -> %d : %d lignes communes ; %d verdicts changes, dont %d DEJA RENDUS (tranchees en %d) ; "
         "%d lignes seulement en %d, %d seulement en %d" % (p1, p2, len(set(a) & set(b)), len(chg), len(rendus), p1,
                                                           len(set(a) - set(b)), p1, len(set(b) - set(a)), p2))
    for k, n in Counter((a[i][2] or a[i][0], b[i][2] or b[i][0]) for i in chg).most_common(20):
        dire("   %-26s -> %-26s %5d" % (k[0], k[1], n))
    for i in rendus[:20]:
        dire("   ⛔ verdict rendu qui change : %s %s -> %s" % (i, a[i], b[i]))
    # deux passages sur DEUX IMAGES : chaque changement est-il venu de la nuit (son bien a bouge) ou du code ?
    im1, im2 = (con.execute("select image from passage where id=?", (p,)).fetchone()[0] for p in (p1, p2))
    if im1 != im2 and chg:
        M = mouvement(IMAGES / im1, IMAGES / im2)
        bouge = set(M["biens_bouges"])
        bs = {i: set(json.loads(x)) for i, x in con.execute("select id_unique, biens from verdict where passage in (?, ?)",
                                                              (p1, p2))}
        nuit = [i for i in chg if bs.get(i, set()) & bouge or i in M["sheet"]["lignes_changees"]]
        dire("   IMAGES DIFFERENTES (%s -> %s) : %d changements sur une ligne ou un bien que LA NUIT a deplace, %d sans "
             "aucun mouvement de la nuit (donc DU CODE)" % (im1, im2, len(nuit), len(chg) - len(nuit)))
    con.close()
    return 0


def etape_compter(p: int | None) -> int:
    con = socle()
    if p is None:
        p = con.execute("select max(id) from passage").fetchone()[0]
    row = con.execute("select image, version, lignes, tranchees, en_attente, boucle, debut from passage where id=?",
                      (p,)).fetchone()
    dire("PASSAGE %s : image %s, %s, debut %s -- %s lignes : %s tranchees + %s en attente ; boucle=%s" % ((p,) + row[:2]
         + (row[6],) + row[2:6]))
    for m, k in con.execute("select coalesce(motif, 'TRANCHEE'), count(*) from verdict where passage=? group by 1 "
                            "order by 2 desc", (p,)):
        dire("   %-24s %5d" % (m, k))
    con.close()
    return 0


# ══════════════════════════════════════ CE QUE LA NUIT A DEPLACE (son mot, reponses 20, point 5) ═════════════════════
# « le sol bouge sous tes pieds chaque matin [...] MESURE CHAQUE MATIN CE QUE LA NUIT A DEPLACE -- sinon tu comparerais
#   deux passages sans savoir ce qui vient de toi et ce qui vient de la nuit. »
CHAMPS_PIECE = ["hektor_annonce_id", "kind", "state", "date", "montant", "hektor_affaire_id", "present_in_hektor",
                "numero_mandat", "transaction_origine", "app_chaine_id", "app_dossier_uuid", "acquereurs_json"]


def mouvement(d1: Path, d2: Path) -> dict:
    """Deux images -> ce qui a bouge entre elles : le Sheet (lignes, cases lues), le registre (pieces, champ par champ),
    le gel (liens). Et LES BIENS QUI ONT BOUGE -- tout verdict d'un autre bien qui change vient du code, pas de la nuit."""
    S1, S2 = (json.loads((d / "sheet.json").read_text(encoding="utf-8")) for d in (d1, d2))
    lus = [c for c in COLONNES_LUES + ["ID Unique"] if c in S1["entete"] and c in S2["entete"]]
    k1, k2 = ({c: S["entete"].index(c) for c in lus} for S in (S1, S2))
    l1 = {i: v[0] for i, v in S1["par_id"].items()}
    l2 = {i: v[0] for i, v in S2["par_id"].items()}
    cases, chang = Counter(), set()
    for i in set(l1) & set(l2):
        if l1[i]["num"] != l2[i]["num"]:
            cases["(numero de ligne)"] += 1
            chang.add(i)
        for c in lus:
            if l1[i]["row"][k1[c]].strip() != l2[i]["row"][k2[c]].strip():
                cases[c] += 1
                chang.add(i)
    sheet = {"nouvelles": sorted(set(l2) - set(l1)), "disparues": sorted(set(l1) - set(l2)),
             "lignes_changees": sorted(chang), "cases_changees": dict(cases),
             "entete_change": S1["entete"] != S2["entete"]}
    # le registre, champ par champ
    P = []
    for d in (d1, d2):
        con = sqlite3.connect("file:%s?mode=ro" % (d / "registre.sqlite").as_posix(), uri=True)
        P.append({int(r[0]): r[1:] for r in con.execute("select app_affaire_id, %s from app_affaire_ledger"
                                                         % ", ".join(CHAMPS_PIECE))})
        con.close()
    champs, pieces_bougees = Counter(), {}
    for a in set(P[0]) & set(P[1]):
        diff = [c for c, x, y in zip(CHAMPS_PIECE, P[0][a], P[1][a]) if str(x) != str(y)]
        for c in diff:
            champs[c] += 1
        if diff:
            pieces_bougees[a] = diff
    nouv, disp = sorted(set(P[1]) - set(P[0])), sorted(set(P[0]) - set(P[1]))
    ib = CHAMPS_PIECE.index("hektor_annonce_id")
    biens = set()
    for a in pieces_bougees:
        biens |= {str(P[0][a][ib]), str(P[1][a][ib])}
    biens |= {str(P[1][a][ib]) for a in nouv} | {str(P[0][a][ib]) for a in disp}
    # le gel
    G = [{(x[0], int(x[1])) for x in json.loads((d / "gel.json").read_text(encoding="utf-8"))["liens"]} for d in (d1, d2)]
    gel = {"ajoutes": sorted(G[1] - G[0]), "retires": sorted(G[0] - G[1])}
    for i, a in gel["ajoutes"] + gel["retires"]:
        for p in (P[0].get(a), P[1].get(a)):
            if p:
                biens.add(str(p[ib]))
    # les biens des lignes du Sheet qui ont change sont pris en compte par l'appelant (ligne par ligne)
    return {"de": d1.name, "a": d2.name, "sheet": sheet,
            "registre": {"pieces": [len(P[0]), len(P[1])], "nouvelles": nouv, "disparues": disp,
                         "champs_changes": dict(champs), "pieces_bougees": {str(a): v for a, v in pieces_bougees.items()}},
            "gel": gel, "biens_bouges": sorted(biens - {"None", ""})}


def etape_mouvement(d1: Path, d2: Path) -> int:
    M = mouvement(d1, d2)
    s, r, g = M["sheet"], M["registre"], M["gel"]
    dire("CE QUI A BOUGE de l'image %s a l'image %s" % (M["de"], M["a"]))
    dire("   SHEET : %d lignes nouvelles, %d disparues, %d lignes dont une case lue a change%s" % (
        len(s["nouvelles"]), len(s["disparues"]), len(s["lignes_changees"]), " ; ⚠ L'EN-TETE A CHANGE" if
        s["entete_change"] else ""))
    for c, n in sorted(s["cases_changees"].items(), key=lambda x: -x[1]):
        dire("      %-22s %5d" % (c, n))
    dire("   REGISTRE : %d -> %d pieces ; %d nouvelles, %d disparues, %d pieces dont un champ a change"
         % (r["pieces"][0], r["pieces"][1], len(r["nouvelles"]), len(r["disparues"]), len(r["pieces_bougees"])))
    for c, n in sorted(r["champs_changes"].items(), key=lambda x: -x[1]):
        dire("      %-22s %5d" % (c, n))
    dire("   GEL : %d liens ajoutes, %d retires" % (len(g["ajoutes"]), len(g["retires"])))
    dire("   BIENS QUI ONT BOUGE : %d" % len(M["biens_bouges"]))
    sortie = DOSSIER / ("mouvement_%s_vers_%s.json" % (M["de"], M["a"]))
    sortie.write_text(json.dumps(M, ensure_ascii=False, indent=1), encoding="utf-8")
    dire("-> %s" % sortie)
    return 0


# ═══════════════════════════════════════════════ LES TEMOINS ════════════════════════════════════════════════════════
def lire_coupe(texte: str) -> list[dict]:
    """« 27100 comp(cancel)[case vide]+27102 offr(refuse) -> 0UDFLH74 CHEREAU | 27101 comp(cancel) -> 25QYWG2U LACHAL
    || ... » -> [{lignes, pieces}] ; un morceau peut aller a DEUX lignes d'un meme acheteur (« A NOM & B NOM »)."""
    import re
    out = []
    for seg in texte.split(" || ")[0].split(" | "):
        g, d = seg.split(" -> ", 1)
        out.append({"lignes": sorted(p.split()[0] for p in d.split(" & ")),
                    "pieces": sorted(int(x) for x in re.findall(r"(\d+) [a-z]", g))})
    return out


def etape_temoins() -> int:
    import csv
    import re
    T: dict = {"fait_le": datetime.now().isoformat(timespec="seconds"), "sources": {}, "familles": {}}
    for p in (SRC_V3, SRC_803, SRC_132, SRC_V3_CALCUL):
        T["sources"][p.name] = md5_fichier(p)
    # 1. LA V3 (le fichier de detachements refait le 22/11, 456 lignes)
    rows = [l for l in SRC_V3.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    # « pourquoi » porte l'ID Unique de la ligne, suivi pour 15 morceaux de « (attendent ici, neutres : 4543) »
    v3 = [{"pieces": sorted(int(x) for x in r["transactions"].split()), "bien": r["bien"], "geste": r["geste"],
           "ligne": r["pourquoi"].split()[0] if r["pourquoi"].strip() else "", "pourquoi": r["pourquoi"]}
          for r in csv.DictReader(rows, delimiter=";")]
    T["familles"]["v3"] = v3
    # 2. LES 161 COUPES NETTES du 19/11 : les 132 validees (20/11) et les 29 faibles
    with SRC_803.open(encoding="utf-8-sig") as f:
        l803 = list(csv.DictReader(f, delimiter=";"))
    coupes = defaultdict(list)
    for x in l803:
        if "coupe NETTE" in x["ce_qui_la_debloque"]:
            coupes[re.search(r"coupe NETTE : (.*?)(?: -- |$)", x["ce_qui_la_debloque"]).group(1)].append(x["id_unique"])
    with SRC_132.open(encoding="utf-8-sig") as f:
        v132 = list(csv.DictReader(f, delimiter=";"))
    num132 = {r["la_coupe"]: r["numero_de_coupe"] for r in v132}
    c132, c29 = [], []
    for texte, ls in sorted(coupes.items()):
        morceaux = lire_coupe(texte)
        manquent = set(ls) - {i for m in morceaux for i in m["lignes"]}
        if manquent:
            dire("⛔ coupe illisible : les lignes %s n'y sont pas -- %s" % (sorted(manquent), texte[:120]))
            return 1
        e = {"coupe": num132.get(texte), "texte": texte, "lignes": sorted(ls), "morceaux": morceaux}
        (c132 if texte in num132 else c29).append(e)
    T["familles"]["coupes_132"], T["familles"]["coupes_29"] = c132, c29
    # 3. LES 20 PIECES A PART (« a part » restreinte aux 20, son mot du 21/11)
    d = json.loads(SRC_V3_CALCUL.read_text(encoding="utf-8"))
    T["familles"]["a_part_20"] = [{"bien": str(b), "piece": int(a), "pourquoi": w} for b, a, w in d["a20"]]
    # 4. LES JUMELLES, 5. LE BIEN 39845
    T["familles"]["jumelles"] = JUMELLES
    T["familles"]["a_sa_decision"] = [{"bien": b, "pourquoi": w} for b, w in BIENS_A_SA_DECISION.items()]
    # les comptes connus, avant d'ecrire quoi que ce soit
    cpt = {"v3_lignes": len(v3), "coupes_132": len(c132), "lignes_132": sum(len(e["lignes"]) for e in c132),
           "coupes_29": len(c29), "lignes_29": sum(len(e["lignes"]) for e in c29), "a_part_20": len(d["a20"])}
    cpt.update(Counter(x["geste"] for x in v3))
    faux = {k: (cpt.get(k), v) for k, v in ATTENDU_TEMOINS.items() if cpt.get(k) != v}
    T["comptes"] = cpt
    if faux:
        dire("⛔ les temoins ne retrouvent pas les comptes connus : %s" % faux)
        return 1
    TEMOINS.write_text(json.dumps(T, ensure_ascii=False, indent=1), encoding="utf-8")
    dire("TEMOINS -> %s" % TEMOINS)
    for k, v in sorted(cpt.items()):
        dire("   %-26s %5d" % (k, v))
    return 0


def ecarts_temoins(I: Image, con: sqlite3.Connection, pid: int) -> dict:
    """Le passage contre chaque temoin. Un temoin n'est JUGEABLE que si la ligne est TRANCHEE ; sinon il ATTEND (et on le
    compte comme tel -- jamais comme un accord). Les ecarts vont dans la table `temoin` du socle, un par ligne."""
    if not TEMOINS.exists():
        dire("   ⚠ pas de temoins.json -- lancer : protocole_classeur.py temoins")
        return {}
    T = json.loads(TEMOINS.read_text(encoding="utf-8"))
    V = {i: (v, json.loads(p) if p else None, m) for i, v, p, m in con.execute(
        "select id_unique, verdict, pieces, motif from verdict where passage=?", (pid,))}
    PR = {i: json.loads(p) if p else [] for i, p in con.execute(
        "select id_unique, preuves from verdict where passage=?", (pid,))}
    sortie, lignes_ecart = {}, []

    def noter(famille: str, i: str, attendu: str, obtenu: str, ec):
        lignes_ecart.append((pid, famille, i, attendu, obtenu, -1 if ec is None else ec))
        sortie.setdefault(famille, Counter())["attend" if ec is None else ("ecart" if ec else "accord")] += 1

    def juger_pieces(famille: str, lignes: list, pieces: list, vraies_seules: bool = False):
        """vraies_seules : ses coupes du 20/11 ne portaient QUE les pieces Hektor (une copie ne decide pas) -- on ne
        compare alors que les vraies pieces du verdict."""
        for i in lignes:
            v = V.get(i)
            att = " ".join(map(str, pieces))
            if v is None:
                noter(famille, i, att, "ABSENTE DU SHEET", 1)
            elif v[0] != "TRANCHEE":
                noter(famille, i, att, "ATTEND (%s)" % v[2], None)
            else:
                got = sorted(a for a in (v[1] or []) if not vraies_seules or I.nature.get(a) == PC.VRAIE)
                noter(famille, i, att, " ".join(map(str, got)), int(set(got) != set(pieces)))
    import re as _re
    for x in T["familles"]["v3"]:
        if x["geste"] == "v3_morceau":
            # la V3 RANGEAIT avec la ligne ses pieces NEUTRES (« attendent ici, neutres : X ») -- le protocole ne donne a
            #   une ligne que ce qu'il PROUVE, et nomme les neutres « a part sans effet » : on compare les prouvees, puis
            #   on verifie chaque neutre a part (famille v3_neutres)
            mm = _re.search(r"neutres : ([\d ]+)\)", x["pourquoi"])
            neu = [int(n) for n in mm.group(1).split()] if mm else []
            juger_pieces("v3", [x["ligne"]], [a for a in x["pieces"] if a not in neu])
            for n in neu:
                v = V.get(x["ligne"])
                if v is None or v[0] != "TRANCHEE":
                    noter("v3_neutres", x["ligne"], "%d neutre" % n, "ATTEND (%s)" % (v[2] if v else "absente"), None)
                else:
                    ok = any(p.startswith("a part sans effet") and str(n) in p.split(":")[1].split()
                             for p in PR.get(x["ligne"], []))
                    noter("v3_neutres", x["ligne"], "%d neutre" % n, "neutre nomme" if ok else "PAS NOMME NEUTRE",
                          int(not ok))
    remplacees = {i for d_ in SES_DECISIONS.values() for i in d_["lignes"]}
    for fam in ("coupes_132", "coupes_29"):
        for e in T["familles"][fam]:
            for m in e["morceaux"]:
                juger_pieces(fam, [i for i in m["lignes"] if i not in remplacees], m["pieces"], vraies_seules=True)
    for nom, d_ in SES_DECISIONS.items():      # ses decisions rendues APRES les temoins : elles remplacent l'ancien attendu
        for i, ps in d_["lignes"].items():
            juger_pieces("ses_decisions", [i], ps, vraies_seules=True)
    # une piece a part ne doit appartenir a AUCUNE ligne tranchee -- et tant qu'aucune ligne de son bien n'est
    #   tranchee, le temoin ATTEND (« a personne » par absence de verdict n'est pas un accord)
    tenues = defaultdict(list)
    for i, (v, p, _m) in V.items():
        if v == "TRANCHEE":
            for a in p or []:
                tenues[a].append(i)
    for x in T["familles"]["a_part_20"]:
        jugees = [i for i in I.D.lignes_bien.get(x["bien"], set()) if V.get(i, ("",))[0] == "TRANCHEE"]
        if not jugees and not tenues.get(x["piece"]):
            noter("a_part_20", "", "%d a personne" % x["piece"], "ATTEND (aucune ligne du bien tranchee)", None)
        else:
            noter("a_part_20", "", "%d a personne" % x["piece"], " ".join(tenues.get(x["piece"], [])) or "a personne",
                  int(bool(tenues.get(x["piece"]))))
    # les jumelles : leurs deux lignes, ensemble -- tranchees sur les MEMES pieces, ou en attente toutes les deux
    for j in T["familles"]["jumelles"]:
        vs = [V.get(i) for i in j["lignes"]]
        if any(v is None for v in vs):
            noter("jumelles", "+".join(j["lignes"]), "les deux lignes", "une ligne ABSENTE DU SHEET", 1)
        elif all(v[0] == "TRANCHEE" for v in vs):
            noter("jumelles", "+".join(j["lignes"]), "memes pieces", str([v[1] for v in vs]),
                  int(len({tuple(sorted(v[1] or [])) for v in vs}) != 1))
        elif any(v[0] == "TRANCHEE" for v in vs):
            noter("jumelles", "+".join(j["lignes"]), "ensemble", "une seule des deux tranchee : %s" % [v[0] for v in vs], 1)
        else:
            noter("jumelles", "+".join(j["lignes"]), "ensemble", "ATTEND (%s)" % [v[2] for v in vs], None)
    # le bien 39845 : TOUTES ses lignes mises de cote pour lui
    for b in T["familles"]["a_sa_decision"]:
        for i in sorted(I.D.lignes_bien.get(b["bien"], set())):
            v = V.get(i)
            noter("a_sa_decision", i, "A_SA_DECISION", (v[2] or v[0]) if v else "ABSENTE",
                  int(not v or v[2] != "A_SA_DECISION"))
    con.executemany("insert into temoin (passage, temoin, id_unique, attendu, obtenu, ecart) values (?, ?, ?, ?, ?, ?)",
                    lignes_ecart)
    return sortie


# ════════════════════════ LE TEMOIN DES 2 560 NUMEROS DE app_classeur_avis (son mot, reponses 21, § 2) ═══════════════
# « 2 560 de mes lignes y ont DEJA leur NUMERO DE DOSSIER ecrit [...] FAIS PASSER TON PROTOCOLE CONTRE CES 2 560 LIGNES,
#   et dis-moi : combien il retrouve au numero exact ; ce qu'il dit des 17 qui ne collent pas aujourd'hui ; et s'il en
#   contredit une qui collait, CA SE REGARDE AVANT TOUT LE RESTE. »
# ⚠ D'OU VIENNENT CES NUMEROS (lu dans le code, pas suppose) : ils ont ete POSES LE 16/11 par le patch C9
#   (supabase/patch_c9_avis_etiquette_2026-11-16.sql), CALCULES DEPUIS LE GEL joint au registre de ce jour-la, et
#   seulement quand la ligne designait UN SEUL dossier. « origine = classeur » est l'origine des trois colonnes d'AVIS
#   (AH, AI, AJ de son classeur), pas du numero. Le temoin est donc LA PHOTO DU 16/11 du gel et des dossiers -- une
#   epreuve que le protocole n'a pas fabriquee, mais pas une ecriture de sa main.
AVIS = DOSSIER / "avis"


def etape_avis(I: Image, p: int | None) -> int:
    import csv
    AVIS.mkdir(parents=True, exist_ok=True)
    # 1. la photo de la table, en lecture seule (jamais ecrit_par : une identite ne s'ecrit pas sur un document)
    try:
        cn, cu = pooler()
        cu.execute("select id_unique, origine, ecrit_le::text, app_dossier_uuid::text, app_dossier_numero "
                   "from public.app_classeur_avis order by id_unique collate \"C\"")
        rows = cu.fetchall()
        cu.execute("select count(*), count(app_dossier_uuid), md5(string_agg(id_unique||':'||coalesce("
                   "app_dossier_uuid::text,'-')||':'||coalesce(app_dossier_numero,'-'), ',' order by id_unique "
                   "collate \"C\")), min(ecrit_le)::text, max(ecrit_le)::text, count(distinct origine), "
                   "string_agg(distinct origine, ',') from public.app_classeur_avis")
        n, n_uuid, emp, e_min, e_max, n_or, origines = cu.fetchone()
        cn.rollback()
        cn.close()
    except Exception as e:  # noqa: BLE001
        dire("⛔ app_classeur_avis n'a pas pu etre lue (%s) -- code 2" % str(e).splitlines()[0][:160])
        return 2
    if n != len(rows):
        dire("⛔ la table a bouge pendant la lecture (%d contre %d) -- code 2" % (n, len(rows)))
        return 2
    photo = AVIS / ("avis_%s.json" % datetime.now().strftime("%Y-%m-%d_%H%M%S"))
    photo.write_text(json.dumps({"n": n, "avec_numero": n_uuid, "empreinte": emp, "ecrit_le": [e_min, e_max],
                                 "origines": origines, "lignes": rows}, ensure_ascii=False), encoding="utf-8")
    # SON MOT (reponses 21 bis, § 2) : « GARDE LE TEMOIN DES 2 560 COMME SENTINELLE, meme s'il n'est pas un juge : il
    #   mesure ce qui bouge depuis le 16/11, et c'est lui qui a fait sortir les 63. »
    dire("SENTINELLE app_classeur_avis (PAS UN JUGE : ses numeros sortent du gel du 16/11, patch C9) -- photo %s "
         "(empreinte %s)" % (photo.name, emp))
    dire("   %d lignes, dont %d avec un numero de dossier ; origine(s) : %s ; ecrites du %s au %s" % (
        n, n_uuid, origines, (e_min or "")[:16], (e_max or "")[:16]))
    A = {i: (u, nu) for i, _o, _e, u, nu in rows if u}
    # 2. aujourd'hui (le gel et les dossiers de l'image) : sa mesure (2 543 / 10 / 7), refaite a l'identique
    lab = {a: x["app_dossier_uuid"] for a, x in I.pieces.items()}
    num_de = {x["app_dossier_uuid"]: x["app_dossier_numero"] for x in I.pieces.values() if x["app_dossier_uuid"]}
    auj = {}
    for i, (u, _nu) in A.items():
        ls = {lab[g["piece"]] for g in I.gel_par_ligne.get(i, []) if g["piece"] in lab and lab[g["piece"]]}
        auj[i] = "MEME" if ls == {u} else ("AUTRE" if len(ls) == 1 else ("PLUSIEURS" if ls else "AUCUN"))
    c_auj = Counter(auj.values())
    dire("   AUJOURD'HUI (le gel de l'image %s) : meme dossier %d . un AUTRE dossier %d . PLUSIEURS dossiers %d . aucun "
         "%d   (sa mesure : 2 543 / 10 / 7)" % (I.d.name, c_auj["MEME"], c_auj["AUTRE"], c_auj["PLUSIEURS"],
                                              c_auj["AUCUN"]))
    # 3. le protocole : le passage, et l'etiquette d'ARRIVEE du rejeu exact (protocole_portes) quand elle existe
    con = socle()
    if p is None:
        p = con.execute("select max(id) from passage").fetchone()[0]
    V = {i: (v, e, m, json.loads(ps) if ps else []) for i, v, e, m, ps in con.execute(
        "select id_unique, verdict, etiquette, motif, pieces from verdict where passage=?", (p,))}
    con.close()
    f_pt = DOSSIER / ("portes_passage_%d.json" % p)
    PT = json.loads(f_pt.read_text(encoding="utf-8")) if f_pt.exists() else {}
    arrivee = PT.get("etiquette_a_l_arrivee", {})
    porte = {i: d["porte"] for i, d in PT.get("detail", {}).items()}

    def numero(e) -> str:
        if e in num_de:
            return num_de[e] or "?"
        return "NEUF" if str(e).startswith("NEUVE") else str(e)
    cat, sortie_l = Counter(), []
    for i, (u, nu) in sorted(A.items()):
        v = V.get(i)
        if v is None:
            k, e = "ABSENTE DU SHEET", None
        elif v[0] != "TRANCHEE":
            k, e = "EN ATTENTE (%s)" % v[2], None
        else:
            e = arrivee.get(i, v[1])
            k = "AU NUMERO EXACT" if e == u else ("UN NUMERO NEUF" if str(e).startswith("NEUVE") else
                                                  "UN AUTRE NUMERO EXISTANT")
        cat[(auj[i], k if not k.startswith("EN ATTENTE") else "EN ATTENTE")] += 1
        sortie_l.append([i, I.sheet["par_id"][i][0]["num"] if i in I.sheet["par_id"] else "", nu, u, auj[i], k,
                         numero(e) if e else "", e or "", porte.get(i, ""), " ".join(map(str, v[3])) if v else ""])
    dire("   LE PROTOCOLE (passage %d%s) contre les %d :" % (p, ", etiquette d'arrivee du rejeu exact" if arrivee
                                                                else ", etiquette simulee", len(A)))
    for g in ("MEME", "AUTRE", "PLUSIEURS", "AUCUN"):
        ks = {k: n_ for (g_, k), n_ in cat.items() if g_ == g}
        if ks:
            dire("      aujourd'hui %-9s (%4d) : %s" % (g, sum(ks.values()), " . ".join(
                "%s %d" % kv for kv in sorted(ks.items(), key=lambda kv: -kv[1]))))
    sortie = NOTICE / ("PROTOCOLE_TEMOIN_AVIS_LES_2560_NUMEROS_PASSAGE_%d_2026-11-22.csv" % p)
    ordre = {"MEME": 1, "AUTRE": 2, "PLUSIEURS": 3, "AUCUN": 4}

    def contredit_(r) -> bool:
        return r[4] == "MEME" and r[5] in ("UN NUMERO NEUF", "UN AUTRE NUMERO EXISTANT")
    with sortie.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id_unique", "ligne_du_sheet", "numero_du_16_11", "etiquette_du_16_11", "aujourdhui_par_le_gel",
                    "le_protocole", "numero_a_l_arrivee", "etiquette_a_l_arrivee", "porte", "pieces_du_protocole"])
        # ⛔ D'ABORD celles qui collaient et que le protocole contredit (« ca se regarde avant tout le reste »)
        w.writerows(sorted(sortie_l, key=lambda r: (not contredit_(r), ordre[r[4]], r[1] or 0)))
    contredit = [r for r in sortie_l if contredit_(r)]
    dire("   ⛔ CELLES QUI COLLAIENT ET QUE LE PROTOCOLE CONTREDIT : %d (en tete du fichier) -> %s" % (len(contredit),
                                                                                                sortie))
    # LA SENTINELLE : ce qui a bouge depuis la mesure precedente, ligne par ligne (le numero de la table, ce que le gel
    #   designe, ce que dit le protocole) -- jamais un compte seul
    prec = sorted((f_ for f_ in AVIS.glob("avis_contre_passage_*.json")), key=lambda f_: f_.stat().st_mtime)
    if prec:
        P0 = json.loads(prec[-1].read_text(encoding="utf-8"))
        avant = {r[0]: r for r in P0["lignes"]}
        bouge = {"numero de la table": [], "ce que le gel designe": [], "ce que dit le protocole": []}
        for r in sortie_l:
            r0 = avant.get(r[0])
            if r0 is None:
                bouge["numero de la table"].append(r[0])
                continue
            for k_, j_ in (("numero de la table", 2), ("ce que le gel designe", 4), ("ce que dit le protocole", 5)):
                if r[j_] != r0[j_]:
                    bouge[k_].append(r[0])
        disparues = sorted(set(avant) - {r[0] for r in sortie_l})
        dire("   SENTINELLE -- depuis %s (photo %s) : %s%s" % (prec[-1].name, P0.get("photo"), " . ".join(
            "%s %d%s" % (k_, len(v_), (" (%s)" % " ".join(v_[:8])) if v_ else "") for k_, v_ in bouge.items()),
            (" . disparues de la table %d" % len(disparues)) if disparues else ""))
    (AVIS / ("avis_contre_passage_%d.json" % p)).write_text(json.dumps(
        {"photo": photo.name, "empreinte": emp, "aujourdhui": dict(c_auj),
         "croise": {"%s|%s" % k: n_ for k, n_ in cat.items()}, "lignes": sortie_l}, ensure_ascii=False, indent=1,
        default=str), encoding="utf-8")
    return 0


def etape_rapport(p: int | None) -> int:
    import csv
    con = socle()
    if p is None:
        p = con.execute("select max(id) from passage").fetchone()[0]
    image, version, debut = con.execute("select image, version, debut from passage where id=?", (p,)).fetchone()
    sortie = NOTICE / ("PROTOCOLE_PASSAGE_%d_LE_VERDICT_DE_CHAQUE_LIGNE_%s.csv" % (p, debut[:10]))
    # SON MOT (reponses 21, § 2) : « PARLE-MOI EN NUMERO DE DOSSIER [...] Donne-moi LES DEUX. »
    rc = sqlite3.connect("file:%s?mode=ro" % (IMAGES / image / "registre.sqlite").as_posix(), uri=True)
    num_de = dict(rc.execute("select distinct app_dossier_uuid, app_dossier_numero from app_affaire_ledger "
                             "where app_dossier_uuid is not null"))
    rc.close()

    def numero(e) -> str:
        if not e:
            return ""
        return num_de.get(e) or ("NEUF (numero donne par la nuit)" if str(e).startswith("NEUVE") else "?")
    rows = list(con.execute("select id_unique, num, biens, verdict, etiquette, pieces, preuves, motif, motif_texte, "
                            "epreuve from verdict where passage=? order by num", (p,)))
    with sortie.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id_unique", "ligne_du_sheet", "bien", "verdict", "numero_de_dossier", "etiquette", "piece",
                    "preuve_nommee", "motif", "pourquoi", "epreuve"])
        for i, n, bs, v, e, ps, pr, m, mt, ep in rows:
            b = " ".join(json.loads(bs))
            if v == "TRANCHEE":
                pieces, preuves = json.loads(ps), json.loads(pr)
                par_piece = {int(x.split()[0]): x for x in preuves if x.split()[0].isdigit()}
                for a in pieces:
                    w.writerow([i, n, b, v, numero(e), e, a, par_piece.get(a, ""), "", "", ep])
                for x in preuves:
                    if not x.split()[0].isdigit():
                        w.writerow([i, n, b, v, numero(e), e, "", x, "", "", ep])
            else:
                w.writerow([i, n, b, v, "", "", "", "", m, mt, ep])
    dire("RAPPORT du passage %d (%s, image %s) -> %s" % (p, version, image, sortie))
    for m, k in con.execute("select motif, count(*) from verdict where passage=? and verdict='ATTENTE' group by 1 "
                            "order by 2 desc", (p,)):
        dire("  %s -- %d ligne(s) : %s" % (m, k, MOTIFS.get(m, ("", "?"))[1]))
        for i, n, mt in con.execute("select id_unique, num, motif_texte from verdict where passage=? and motif=? "
                                    "order by num limit 3", (p, m)):
            dire("      ex. %s (ligne %s) : %s" % (i, n, (mt or "")[:200]))
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--image")
    sp = ap.add_subparsers(dest="etape", required=True)
    sp.add_parser("image")
    b = sp.add_parser("bien")
    b.add_argument("annonce")
    p = sp.add_parser("passage")
    p.add_argument("--note", default="")
    p.add_argument("--variantes", default="", help="regles PROPOSEES a mesurer, ex. R4 (jamais appliquees ; P1 est validee, elle joue toujours)")
    p.add_argument("--perimetre", choices=("bien", "chaines"), default="bien",
                   help="bien : toutes les pieces du bien (le protocole) ; chaines : celles que le gel touche (le 20/11)")
    c = sp.add_parser("comparer")
    c.add_argument("p1", type=int)
    c.add_argument("p2", type=int)
    k = sp.add_parser("compter")
    k.add_argument("p", type=int, nargs="?")
    sp.add_parser("temoins")
    av = sp.add_parser("avis", help="le temoin des numeros de app_classeur_avis (photo en lecture seule + croisement)")
    av.add_argument("p", type=int, nargs="?")
    r_ = sp.add_parser("rapport")
    r_.add_argument("p", type=int, nargs="?")
    mv = sp.add_parser("mouvement", help="ce que la nuit a deplace entre deux images (par defaut : les deux dernieres)")
    mv.add_argument("de", nargs="?")
    mv.add_argument("a", nargs="?")
    a = ap.parse_args()
    if a.etape == "mouvement":
        imgs = sorted(p for p in IMAGES.iterdir() if (p / "manifeste.json").exists())
        d1 = image_choisie(a.de) if a.de else imgs[-2]
        d2 = image_choisie(a.a) if a.a else imgs[-1]
        verifier_image(d1)
        verifier_image(d2)
        return etape_mouvement(d1, d2)
    if a.etape == "rapport":
        return etape_rapport(a.p)
    if a.etape == "image":
        return etape_image()
    if a.etape == "temoins":
        return etape_temoins()
    if a.etape in ("comparer", "compter"):
        return etape_comparer(a.p1, a.p2) if a.etape == "comparer" else etape_compter(a.p)
    I = Image(image_choisie(a.image))
    if a.etape == "bien":
        return etape_bien(I, a.annonce)
    if a.etape == "avis":
        return etape_avis(I, a.p)
    return etape_passage(I, a.note, a.perimetre, {x for x in a.variantes.split(",") if x})


if __name__ == "__main__":
    sys.exit(main())
