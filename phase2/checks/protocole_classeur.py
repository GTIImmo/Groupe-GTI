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
v23 (25/11 soir, son accord « Oui, les trois -- avec une reserve sur R29 ») : R27, R28, R29 VALIDEES (REGLES_VALIDEES).
  R27 departage deux lignes d'une meme affaire (meme Mandat, Acquereur, Commission) -- elle remplace l'exception nommee
  de VIALLARD et de PAOLONE ; R28 ne joue que dans le motif COPIE_SEULE ; R29 joue APRES tous les verdicts (comme R16),
  sous sa propre garde du deja-rendu, et ne lit jamais l'etat d'une offre (nos 1 202 refus des 11-12/11/2026).

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
VERSION = ("v23.3 -- 26/11 : R29 RETIREE par son mot (« un pansement sur la cause » ; 0 candidat au 82) -- aucun verdict "
           "ne change ; v23.2 -- 26/11 : le temoin v3 attend, pour HUY49KEC, P252U1JH et d2108609, ce que SES decisions leur donnent "
           "(son mot : « trois attentes perimees ») -- aucun verdict ne change ; "
           "v23.1 -- 25/11 (nuit) : 3741 SORTIE de ses neuf a part (son mot : « la raison de la mise a part a disparu ») "
           "-- v23, 25/11 (soir) : R27, R28, R29 VALIDEES par son accord (« Oui, les trois ») -- R27 la meme affaire sur "
           "deux lignes, R28 un mandat une seule vente (dans le motif COPIE_SEULE seulement), R29 la ligne suit la vente de "
           "sa commission (un fait d'epoque, jamais le mot « refusee ») ; v22 : l'empreinte des entrees vivantes")

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
    # v18 (23/11 soir) -- trouve par le REJEU EXACT du passage 73 (le prealable P-a, « les signaux transaction
    #   introuvable ») : une transaction SANS DATE que SA decision des 19 et 20/11 exclut de la regle E du chainage
    #   (EXCLUES_DE_LA_REGLE_E de phase2/sync/affaire_ledger.py), seule dans sa chaine, n'entre jamais dans la liste des
    #   dossiers du bien : le fichier des coupes la dit « introuvable » et ignore le morceau ENTIER
    "PIECE_SANS_DATE_INVISIBLE": ("E9", "son morceau tient une piece SANS DATE que le chainage ne voit pas (exclue de la "
                                        "regle E par sa decision des 19-20/11 : « on met de cote, on ne tranche pas ») et "
                                        "ses pieces sont dans PLUSIEURS dossiers : aucune porte ne peut les reunir"),
}
# a part par SA decision (20/11 soir, B3) -- la meme liste que la V3
# 14033 : sa B3 du 20/11 (« a part ») est REMPLACEE le 23/11 par son option B (a DONNADIEU) -- PIECE_DONNEE_PAR_DECISION
A_PART_PAR_DECISION: dict = {}
# ⭐ SES 64 DECISIONS DU VERROU (24/11, son mot « MOT_DU_24_11_LES_64_TRANCHEES_LES_REGLES_ET_LE_CONTROLE » et le detail
#   SES_64_DECISIONS_DU_VERROU_23_11.md) : 64 transactions des 14 biens du verrou tranchees par lui, une par une, sur un
#   tableau qui met en face toutes les transactions du bien et toutes les lignes du Sheet. « ⛔ TU NE LES APPLIQUES PAS A
#   L'AVEUGLE. Tu les reprends avec TES propres mesures [...] UNE A LA FOIS. » -- protocole_ses_64_decisions_du_verrou_
#   2026-11-24.py : 47 des 62 pieces donnees l'etaient DEJA a la meme ligne par le protocole (0 a une autre) ; restent 15 :
#   14 posees ici (PIECE_DONNEE_PAR_DECISION), 1 en suspens (19814, son doute -- EN_SUSPENS_PAR_SON_DOUTE) ; et 2 mises
#   de cote (regle 6 -- MISE_DE_COTE_PAR_DECISION).
SON_MOT_DU_24_11 = "sa decision du 24/11 (ses 64 du verrou)"
MISE_DE_COTE_PAR_DECISION = {
    14110: "%s : « 14110 -> AUCUNE LIGNE, je la laisse de cote (regle 6) » -- compromis annule SANS DATE, 113 000, "
           "honoraires 7 000 = la commission des TROIS lignes du bien 28653 : aucune preuve ne la donne ; ⚠ un indice, "
           "pas une preuve : L2B2WGCF « ACQ se retractent » (une retractation suit un compromis signe)" % SON_MOT_DU_24_11,
    27609: "%s : « DE COTE : 27609 » -- offre refusee du 23/10/2019, 100 000 : sa date n'est sur aucune case, "
           "aucune ligne du bien 53858 n'a d'offre a ce prix" % SON_MOT_DU_24_11,
}
# ⛔ SON DOUTE (§ 6 de son mot du 24/11) : « les DEUX compromis annules 19814 (17/02/2020) et 19815 (sans date) sont tous
#   les deux sur R7NU9NPM. Or 19814 est date APRES l'annulation de R7NU9NPM (01/02/2020) et AVANT l'offre de 4G2UHO35
#   (24/02/2020) : il ne colle proprement a aucune des deux. ➡ Mesure-le et dis-moi ce que tu trouves. Ne force pas. »
#   MA MESURE (24/11) : 16 j apres l'annulation de R7NU9NPM, 7 j avant l'offre de 4G2UHO35 ; honoraires 5 980 = la
#   commission des DEUX lignes ; son acte prevu (date_acte) est le 17/05/2020 et 4G2UHO35 est annulee le 20/05/2020
#   (« financement pas sur relance 13/5 ») -- un indice vers 4G2UHO35, contre la date de son offre. NON FORCE : elle reste a
#   part, et le verrou tient les DEUX lignes dont l'etiquette dependrait d'elle (19814 est la plus petite piece de sa
#   chaine, celle qui porte D2020-0091 : la ligne qui la recevra prendra ce numero).
#   ⭐ SA REPONSE (24/11, « MOT_DU_24_11_MES_QUATRE_REPONSES », ①) : « TON INDICE EST LE MEILLEUR ARGUMENT DU DOSSIER :
#   son acte etait prevu le 17/05/2020, et 4G2UHO35 a ete annulee le 20/05/2020. C'est une preuve de DATE -- ni un nom,
#   ni un mandat. Elle est conforme a P1 et a P2. 19814 va a 4G2UHO35 (avec 19819 et 19820) ; 19815 reste a R7NU9NPM
#   (avec 19818). » -> 19814 sort du suspens : PIECE_DONNEE_PAR_DECISION. Le mecanisme reste (vide), pour le prochain doute.
EN_SUSPENS_PAR_SON_DOUTE: dict = {}
for _a, _t in MISE_DE_COTE_PAR_DECISION.items():
    A_PART_PAR_DECISION[_a] = _t
for _a, (_ls, _t) in EN_SUSPENS_PAR_SON_DOUTE.items():
    A_PART_PAR_DECISION[_a] = _t
# ⭐ SES 20 A PART, SA DECISION DU 21/11 RENVERSEE POUR ONZE (24/11, § 1 bis) : « JE RENVERSE MA PROPRE DECISION DU 21/11
#   SUR MES 20 PIECES A PART [...] j'en donne ONZE [...] 14110 -> AUCUNE LIGNE, je la laisse de cote (regle 6) [...] LA
#   LISTE DES 20 NE DISPARAIT PAS : les NEUF autres restent a part [...] ⛔ GARDE LA LISTE DANS LE CODE comme temoin, mais
#   ces onze-la n'y sont plus. » -- la liste source (SRC_V3_CALCUL, « a20 ») ne change pas : elle reste le temoin.
SORTIES_DES_20_PAR_DECISION = {4126: "P252U1JH", 4327: "PYG8JZ0C", 4533: "PCDZXTIY", 4542: "RGCEC677", 4560: "QV5AYD2K",
                               4621: "TND2I31B", 4669: "GYGF5F1X", 7710: "9DK01H85", 20088: "5QE9107L",
                               21520: "d2108609", 14110: None,
                               # ⭐ SON MOT DU 25/11 AU SOIR (apres le rejeu v23) : « HUY49KEC : oui, sors 3741 de mes
                               #   neuf pieces a part. [...] « date du 23/11/2018 sur aucune case, honoraires inconnus ».
                               #   Les honoraires sont maintenant connus, ils viennent de Hektor et non de nos recopies :
                               #   5 000 euros, exactement ma Commission TTC. La raison de la mise a part a disparu.
                               #   Sors-la, et laisse R28 lui donner D2018-0476. » -- R28 la donne (pas une decision de
                               #   piece) ; il en reste HUIT a part
                               3741: "HUY49KEC"}

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
    "R13": ("deux lignes dans un meme dossier, dont l'une est « Annulee », SANS gel sur ce dossier, au MEME Prix et a la MEME "
           "date d'offre que l'autre, que son gel tient : la meme affaire ecrite deux fois -- la ligne du gel prend le "
           "dossier, l'annulee n'a rien a etiqueter (sa convention des jumelles du 20/11 : « celle que le gel tient deja ; "
           "l'autre sans etiquette ») -- ⭐ AVEC LA MEME COMMISSION, LE MEME COMPROMIS QUAND LES DEUX EN ONT UN, ET UNE SEULE PIECE DE CHAQUE GENRE AU DOSSIER (une seule affaire : deux affaires -> exception NOMMEE, jamais implicite)",
            "son message du 23/11 : « R13 : OUI, MAIS SUR TROIS PAIRES [...] SORS E9XL0N5B [...] Une regle n'avale pas son "
            "propre ecart [...] meme affaire -> R13 ; deux affaires -> exception NOMMEE, jamais implicite » -- la verification "
            "demandee a sorti aussi IAYQ5OG2 (son propre compromis au 24/02/2022) : DEUX paires"),
    "R14": ("une piece SUPPRIMEE chez Hektor dont une JUMELLE vivante est dans le meme morceau (meme genre, meme date, meme "
           "montant -- ou montant inconnu) est la trace d'une saisie refaite : elle sort du morceau, reste FIGEE dans son "
           "ancien dossier avec son numero (on ne supprime pas une part), et la ligne se tranche sur ses pieces vivantes",
            "son message du 23/11 : « R14 : OUI, validee. Temoin inverse en place (6684bcf1 non touchee). »"),
    # ⛔ LA PHRASE DE GARDE (son mot du 23/11) : « R9 NE VAUT QUE SI LA COMMISSION EST UNIQUE AU BIEN ».
    "R9": ("une ligne sans vraie piece prouvee (qui ne tient que sa copie C5, ou rien) recoit chaque vraie piece que son gel lui donne, quand cette piece est A "
          "PART (aucune preuve ne la donne a aucune ligne), que le gel ne la donne a AUCUNE autre ligne, que ses "
          "honoraires sont la « Commission TTC » de la ligne, qu'AUCUNE autre ligne n'a son prix + honoraires, et qu'elle "
          "n'est pas une de SES 20 pieces a part (son mot du 21/11) -- ⭐ ET, L'EXCEPTION NOMMEE DE SES HUIT ECARTS : AUCUNE "
          "autre ligne du bien n'a la meme Commission TTC (temoin : 3 838 fois la meme ligne, 0 une autre)",
           "son message du 23/11 : « R9 AVEC SON EXCEPTION : OUI, VALIDEE. La preuve stricte avait raison les 8 fois, temoin "
           "a ZERO sur 3 838, cout = 1 ligne, 0 verdict rendu change. Pose-la, et note la phrase de garde : R9 ne vaut que "
           "si la commission est UNIQUE AU BIEN »"),
    "R9b": ("R9 quand les honoraires de la piece sont INCONNUS (une offre, un compromis sans net vendeur) : son MONTANT est le "
           "« Prix » de la ligne, et AUCUNE autre ligne du bien n'a ce meme Prix",
            "son mot du 23/11 (16) : « R9b : OUI. Temoin 3 659 fois la meme ligne, 0 fois une autre [...] Pose-la. » « R11 : OUI. Les 24 lignes qu'elle ferme disent TOUTES Annulee [...] Pose-la. » « R10 : OUI, mais NOMME SON UNIQUE ECART avant [...] la 59e ne rend aucun bien, elle ne contredit pas P1 »"),
    "R10": ("une ligne qui nomme DEUX biens (deux sources) est sur celui des deux ou elle a des pieces PROUVEES (date au jour "
           "exact, prix + honoraires) quand elle n'en a sur AUCUN autre -- la preuve departage les sources",
            "son mot du 23/11 (16) : « R9b : OUI. Temoin 3 659 fois la meme ligne, 0 fois une autre [...] Pose-la. » « R11 : OUI. Les 24 lignes qu'elle ferme disent TOUTES Annulee [...] Pose-la. » « R10 : OUI, mais NOMME SON UNIQUE ECART avant [...] la 59e ne rend aucun bien, elle ne contredit pas P1 »"),
    "R11": ("une ligne SANS gel, dont aucune piece n'est prouvee, et dont TOUTES les vraies pieces du bien sont prouvees a "
           "d'AUTRES lignes : son affaire n'a aucune piece chez nous -> RIEN A ETIQUETER (rejugee a chaque passage) -- sauf "
           "si la triple preuve de R8 trouve son affaire sur un autre bien",
            "son mot du 23/11 (16) : « R9b : OUI. Temoin 3 659 fois la meme ligne, 0 fois une autre [...] Pose-la. » « R11 : OUI. Les 24 lignes qu'elle ferme disent TOUTES Annulee [...] Pose-la. » « R10 : OUI, mais NOMME SON UNIQUE ECART avant [...] la 59e ne rend aucun bien, elle ne contredit pas P1 »"),
    "R16": ("une ligne « Annulee » SANS BIEN (SANS_BIEN), dont le vendeur est mandant d'au moins un bien, et dont les biens de "
           "ce vendeur n'ont AUCUNE vraie piece (offre, compromis) LIBRE -- tenue par aucune ligne a la fin du passage -- a "
           "un an de sa case ni sans date : son affaire n'a aucune piece chez Hektor -> RIEN A ETIQUETER (temoin du zero : "
           "626 des 662 « Annulee » tranchees qui tiennent une offre retrouvent LEUR piece a 7 j ; les 36 ratees = vendeur "
           "absent des mandants 31, date a plus de 7 j 5 -- la regle exige le vendeur TROUVE et regarde a UN AN). Elle ne "
           "donne aucune piece et joue APRES tous les verdicts : elle ne peut faire jouer aucune autre ligne",
            "son mot du 23/11 : « R16 : LANCE LE PASSAGE ENTIER. ⛔ Elle n'est validee que SI le passage prouve qu'aucun verdict rendu ne bouge » -- passage 49 (variante) contre 47 : 6 verdicts changes, les 6 nommes (SANS_BIEN -> RIEN_A_ETIQUETER), 0 deja rendu, temoins identiques ligne pour ligne (806 / 806), ZZ5WKMWM non touchee"),
    # ⚠ SA RESERVE (23/11, a mesurer AVANT L'ECRITURE, pas maintenant) : R17 s'appuie sur app_chaine_id, une cle
    #   RECALCULEE -- sur cinq biens au profil identique (affaire tombee puis vente au meme prix), elle decide de trois
    #   facons : 41822 reunit les deux moities (20470 + 20472) ; 9232 et 15881 les separent (4126 / 4128, 7903 / 7904) ;
    #   24390 et 28653 collent le compromis annule a l'affaire vivante (11579 dans la chaine de la vente, 14110 de meme).
    "R17": ("LA SOEUR DE CHAINE : une vraie piece A PART dont la chaine Hektor porte UNE seule piece de l'autre moitie de la "
            "meme affaire tombee (compromis ANNULE <-> offre REFUSEE), au MEME montant, prouvee a UNE seule ligne, suit cette "
            "piece a cette ligne -- SAUF si les dates la contredisent (apres l'annulation + 15 j, compromis avant l'offre), "
            "si l'offre est datee APRES le compromis, si la ligne tient deja une vraie piece de son genre, ou si la ligne "
            "est DEJA TRANCHEE (g4 : la piece doit devenir sa plus petite, et etre possible pour plusieurs lignes) (temoin : "
            "rejouee dans les deux sens sur les 302 paires tenues au passage 51, la BONNE ligne 581 fois, une AUTRE 0 ; elle "
            "s'abstient 23 fois, dont les 4 cas des 2 chaines qui melent deux affaires -- biens 2393 et 23353)",
            "son message du 23/11 : « R17 : oui, pose-la. J'ai verifie de mon cote entre les passages 51 et 54 : aucun "
            "verdict rendu change, aucune etiquette, aucune piece. Et tes deux refus (passages 52 et 53) sont le vrai "
            "travail. » -- avec SA RESERVE sur app_chaine_id (ci-dessus), a mesurer avant l'ecriture"),
    # ⭐ A PARTIR D'ICI (son message du 23/11 au soir) : « Tranche par ton raisonnement tout ce que tu peux trancher. Pour
    #   chaque paquet, construis ta regle, porte son temoin, verifie qu'aucun verdict rendu ne bouge, et avance. Tu n'as
    #   pas besoin de mon accord a chaque regle. » -- une regle est validee ICI quand son passage (variante) le prouve :
    #   0 etiquette, 0 piece d'une ligne rendue, 0 ecart de temoin nouveau (protocole_juger_un_passage_2026-11-23.py).
    "R19": ("L'ELIMINATION : une vraie piece A PART dont le prix + honoraires designent PLUSIEURS lignes va a la SEULE qui ne "
            "tient aucune vraie piece prouvee de son genre, quand TOUTES les autres tiennent deja la leur au MEME prix + "
            "honoraires (gardes : jamais une de SES 20 a part ; les dates ; jamais a une ligne deja tranchee) -- temoin : "
            "rejouee sur chaque piece prouvee dont le prix + honoraires designent au moins deux lignes, la BONNE ligne 18 "
            "fois, une AUTRE 0, abstention 10",
            "son message du 23/11 au soir (« tranche seul ») -- passage 59 (variante) contre 58 : 10 lignes (8 VERROU, 2 "
            "COPIE_SEULE), 0 verdict rendu (ni etiquette, ni piece), temoins identiques ligne pour ligne (788 / 788)"),
    "R20": ("LA SOEUR DE CHAINE RECONNAIT SANS DONNER : une vraie piece a part dont la soeur de chaine (critere de R17) est prouvee a une ligne DEJA tranchee, dont elle n'est pas la plus petite, est reconnue comme une piece de cette affaire : jamais donnee, rien ne change pour la ligne tranchee, mais elle ne retient plus aucune AUTRE ligne au verrou (temoin : celui de R17, 581 / 0)",
            "son message du 23/11 au soir (« tranche seul ») ; sa decision « les 3 offres : non, c'est du deja-rendu » est tenue (rien n'est donne) -- passage 61 contre 60 : 3 lignes (29cf0ca8, 8bcc3b63, b884cbd4), 0 verdict rendu, 0 preuve de ligne rendue, temoins identiques (788 / 788)"),
    "R21": ("L'AFFAIRE TOMBEE SANS LIGNE : une affaire tombee complete (compromis annule + offre refusee au meme montant, partenaires uniques), ses deux pieces a part, sans AUCUN lien avec les lignes du bien (ni montant, ni honoraires, ni date a 30 j, ni gel) est MISE DE COTE comme R7b / R7c, jamais donnee, jamais une de SES 20 a part (temoin : 0 / 26 sans lien tenues par une ligne tranchee ; 432 / 460 avec un lien tenues)",
            'son message du 23/11 au soir (« tranche seul ») -- passage 63 contre 62 : 3 lignes (ZZ5WKMWM, ESVJUR12, ULA087KO), 0 verdict rendu, temoins identiques (788 / 788) ; 11204 et 24649 GARDENT leur ancien numero (sa regle 6) ; la vente ESVJUR12 (hors des 2 560) recoit un numero NEUF, la regle du plus ancien'),
    "R22": ("R15 SOUS LA GARDE DU DEJA-RENDU : l'offre que le gel ne donne qu'a une ligne sans vraie piece prouvee va a cette ligne si sa date tombe a 7 jours au plus de sa case « Offre Achat », et a 7 jours d'aucune autre ligne (temoin de R15 : 4 243 / 0) -- et SEULEMENT sur un bien ou aucune ligne tranchee sans elle ne bouge avec elle (juger_bien_garde ; sinon le bien est juge sans elle et nomme)",
            'son message du 23/11 au soir (« tranche seul ») -- passage 65 contre 64 : 5 lignes (ARF57GC5, BQAVSRA1, KPDROR30, RKWNRBV1, af8d7986), 0 verdict rendu, temoins identiques (788 / 788) ; la garde a juge SANS elle les biens 25921 (2K0LUIIG aurait bouge) et 37243 (ZFLFAQ0T aurait bouge : 3QZ4DAD1 reste impossible)'),
    "R23": ("R11 ETENDUE : une vraie piece datee a plus d'UN AN de toutes les cases de date de la ligne n'est pas de son affaire -- elle ne retient plus la ligne hors de R11 (temoin T2 : 0 piece prouvee sur 12 237 n'est a plus d'un an de sa ligne)",
            'son message du 23/11 au soir (« tranche seul ») -- passage 68 contre 67 : 1 verdict (91IHSGNC : AUCUNE_PIECE_PROUVEE -> AFFAIRE_SUR_UN_AUTRE_BIEN, la triple preuve trouve son affaire sur le bien 10229), 0 verdict rendu, temoins identiques'),
    "R24": ("R11 ETENDUE, ligne « Annulee » : une VENTE dont le compromis ACTIF de sa chaine (au meme montant) est prouve a une AUTRE ligne n'est pas de son affaire -- une affaire annulee n'a pas de vente (temoins : T1, 803 « Annulee » tranchees sur 804 ne tiennent aucune vente, l'ecart LQXGFCKH tenant la vente de SA chaine ; T4, 3 608 ventes sur 3 609 sont a la ligne du compromis actif de leur chaine, l'ecart 17027 allant a l'acheteur suivant, jamais a une ligne annulee)",
            'son message du 23/11 au soir (« tranche seul ») -- passage 70 contre 69 : 1 verdict (5C80H7ZF : AUCUNE_PIECE_PROUVEE -> RIEN_A_ETIQUETER ; sa seule piece libre, la vente 22191, suit le compromis 22189 de 6VSA6EOZ), 0 verdict rendu, temoins identiques'),
    "R25": ("L'ELIMINATION PAR LES HONORAIRES : une vraie piece a part dont le prix ne colle a aucune ligne, mais dont les honoraires sont la Commission de PLUSIEURS lignes, va a la SEULE qui ne tient aucune vraie piece de son genre, quand toutes les autres tiennent deja la leur aux memes honoraires ; jamais une de SES 20 a part ; sous la garde du deja-rendu (temoin : 46 / 0, abstention 18)",
            'son message du 23/11 au soir (« tranche seul ») -- passage 72 contre 71 : 1 ligne (SYA8MH79, D2024-0458), 0 verdict rendu, temoins identiques (788 / 788)'),
    # ⭐ SES TROIS REGLES DU 25/11 AU SOIR -- mesurees par phase2/checks/mesurer_r27_r28_r29_2026-11-25.py (les champs de
    #   HEKTOR seulement, jamais nos recopies de son Sheet), puis acceptees : « Oui, les trois -- avec une reserve sur R29 »
    "R27": ("LA MEME AFFAIRE SUR DEUX LIGNES : deux lignes qui tombent dans le MEME dossier avec le meme Mandat, le meme "
            "Acquereur et la meme Commission TTC sont UNE affaire (une double saisie, ou deux tentatives du meme acheteur) : "
            "une seule porte l'etiquette, l'autre n'a rien a etiqueter. Celle qui porte, au premier critere qui tranche : "
            "① la ligne qui prouve la VENTE du dossier ; ② la ligne dont la date d'annulation est deja posee sur le "
            "compromis du dossier ; ③ la ligne dont la date d'annulation est prouvee par le journal de Hektor (refus d'une "
            "offre, annulation d'un compromis -- jamais nos refus des 11-12/11/2026) ; ④ sans argent en jeu (aucune vente, "
            "deux lignes annulees), la plus ancienne date d'annulation (une CONVENTION, pas une preuve). Ni le gel, ni le "
            "nom ne departagent. Elle ne prend jamais une paire de R13, et elle remplace l'exception nommee des jumelles "
            "VIALLARD et PAOLONE (DEBARD n'a pas la meme commission : elle reste nommee)",
            "son accord du 25/11 au soir : « R27 : d'accord [...] y compris le fait que VIALLARD aille a YRUF0S9H » -- "
            "et, avant : « d'accord sur tes deux premiers criteres [...] pas ton troisieme critere, celui du gel »"),
    "R28": ("UN MANDAT, UNE SEULE VENTE -- DANS LE MOTIF COPIE_SEULE SEULEMENT : une ligne dont le morceau ne tient que des "
            "copies C5 recoit la vente Hektor de son Mandat au Sheet quand ce mandat ne porte qu'UNE vente chez Hektor (553 "
            "mandats sur 6 218 en portent plusieurs : Hektor recycle ses numeros), que cette vente est sur son bien et a "
            "part (personne ne la tient), que ses honoraires chez Hektor sont la Commission TTC de la ligne, et qu'elle est "
            "au nom de son Acquereur ; jamais une de SES 20 a part. Aucun nombre de jours. ⛔ Hors de son motif le verrou "
            "prendrait 3 autres lignes (la paire de R27, 5C80H7ZF) : il n'y joue pas",
            "son accord du 25/11 au soir : « R28 : d'accord [...] Garde-la enfermee dans son motif » -- et, avant : « je ne "
            "veux pas fixer un nombre de jours [...] un seul mandat, une seule vente »"),
}
#: ⛔ LES REGLES RETIREES -- elles ne jouent JAMAIS, pas meme en variante de mesure (joue() les refuse) ; leur texte et leur
#  code restent ici, pour l'histoire et pour la mesure qui a justifie le retrait.
#  R29, RETIREE LE 26/11 -- SON MOT : « R29 : retire-la. Ta mesure est la bonne demonstration : le seul cas qu'elle couvrait
#  etait 9Q0FHAKK elle-meme, et il a disparu quand j'ai corrige mes deux cases. C'etait un pansement sur la cause. Ce qui a
#  protege cette ligne, c'est qu'elle est restee visiblement en attente jusqu'a ce que je la regarde. [...] une garde qui
#  laisse la ligne en attente valait mieux qu'une regle qui l'aurait tranchee seule. »
#  La mesure (mesurer_le_cas_de_r29_2026-11-26.py, dans le juge) : image du 81 -> 1 candidat, 9Q0FHAKK (arrete par sa
#  garde) ; image du 82 -> 0 candidat sur 62 lignes regardees. Elle n'a jamais tranche une ligne.
REGLES_RETIREES = {
    "R29": ("LA LIGNE SUIT LA VENTE DE SA COMMISSION : une ligne non tranchee dont le nom note est celui d'une offre Hektor "
            "PROPOSEE le jour de sa case « Offre Achat » (un fait d'epoque : la 1re proposition de son journal, l'etat de "
            "l'offre n'est jamais lu), sur une annonce dont le mandat ne porte qu'UNE vente, quand les honoraires de cette "
            "vente sont la Commission TTC de la ligne, que la vente est au nom d'un AUTRE acquereur et que personne ne la "
            "tient a la fin du passage : la ligne est sur le bien de cette vente et la recoit. Elle joue APRES tous les "
            "verdicts, sous la garde du deja-rendu (aucune ligne tranchee de l'un ou l'autre bien ne doit bouger)",
            "son accord du 25/11 au soir : « R29 : ⛔ change le mot « refusee », il ne prouve rien [...] 1 206 offres portent "
            "un refus date du 11 ou du 12 novembre 2026 [...] reecris la condition avec un fait d'epoque [...] Puis pose les "
            "trois. » -- ma mesure : ces refus sont les NOTRES (1 202 sur 1 202 portent un de nos travaux de refus)",
            "RETIREE le 26/11 par son mot : « R29 : retire-la [...] C'etait un pansement sur la cause » -- son seul cas, "
            "9Q0FHAKK (un Mandat emprunte a la ligne 245), a disparu a la source ; 0 candidat au passage 82"),
}
# R27 : les deux paires de jumelles qu'elle tranche, et la ligne qui porte -- SON accord, ecrit ici pour que le temoin le
#   redise (« y compris le fait que VIALLARD aille a YRUF0S9H ») ; PAOLONE : O6R10ZQA, la date posee (critere ②)
SON_ACCORD_R27 = {"VIALLARD": "YRUF0S9H", "PAOLONE": "O6R10ZQA"}
# R27 ③ : nos refus de masse des 11 et 12/11/2026 ne prouvent aucune date d'epoque (sa reserve du 25/11 : « le mot
#   refusee ne prouve rien » -- 1 202 offres refusees ces deux jours, toutes par nos travaux)
NOS_REFUS_DE_MASSE = {"2026-11-11", "2026-11-12"}
# R29 : les ventes qu'elle donne (piece -> (ligne, preuve)), posees par la passe d'apres les verdicts ; ses abstentions ;
#   et les lignes qu'elle a deplacees (ligne -> (ses anciens biens, le bien de la vente)), remises au passage suivant
DONNEE_PAR_R29: dict = {}
R29_ABSTENUES: dict = {}
R29_DEPLACEES: dict = {}
VARIANTES = {
    "R4": "une piece A PART (sans preuve) ne peut jamais rejoindre plus tard un dossier dont elle deviendrait la plus "
          "petite (sa regle R4 du 20/11) -- elle ne retient donc pas la ligne au verrou E7",
    # R15 (23/11, les offres refusees sous le prix : RKWNRBV1, BQAVSRA1, 40ELE6SQ) -- PROPOSEE
    "R15": "R9b quand le MONTANT ne colle pas : une OFFRE que le gel ne donne qu'a cette ligne (sans vraie piece prouvee) va "
           "a la ligne si sa date tombe a 7 JOURS AU PLUS de sa case « Offre Achat », et a 7 jours d'AUCUNE autre ligne du "
           "bien (temoin : sur les offres prouvees par la date exacte, la proximite unique donne la meme ligne 4 243 fois, "
           "une autre 0)",
    # R12 (23/11, les 25 « plusieurs acheteurs » : son mot (15), « existe-t-il un departage non regarde ? ») -- PROPOSEE
    "R12": "une piece a part dont le prix + honoraires sont ceux de PLUSIEURS lignes va a la SEULE d'entre elles que son "
           "gel nomme -- le gel departage la preuve, il ne la remplace pas (jamais une de SES 20 a part ; et, sa regle (b) "
           "du 20/11, jamais a une ligne deja tranchee si elle est plus petite que la plus petite piece de son morceau)",
    # R18 (23/11, son message : « Mesure la regle de mise de cote a blanc et presente deux colonnes ») -- MESURE SEULEMENT,
    #   ⛔ ce n'est PAS a moi de trancher : ses 20 a part sont SA decision du 21/11 ; cinq ventes y perdraient leur numero
    "R18": "SES 20 A PART QUI RETIENNENT UNE LIGNE AU VERROU sont MISES DE COTE comme R7b / R7c : isolees AVEC leur dossier "
           "d'aujourd'hui (ce qu'aucun morceau ne prend), elles gardent leur ancien numero et ne sont JAMAIS donnees -- elles "
           "ne retiennent plus aucune ligne (sa decision du 21/11, « a personne », reste vraie)",
    # 14033 (sa B3 du 20/11) : ses DEUX options, mesurees a blanc cote a cote (son mot (15)) -- jamais appliquees
    "B3A": "14033 A PART POUR TOUJOURS : mise de cote comme R7b, avec son dossier d'aujourd'hui (elle garde son numero)",
    "B3B": "14033 A DONNADIEU (ea6a28a7) : son prix 140 500 et sa commission 9 500 sont ceux de DONNADIEU (critere 1)",
    # R7c a quitte cette liste le 23/11 (son message) : elle est dans REGLES_VALIDEES
    # R16 a quitte cette liste le 23/11 (son mot, et la preuve du passage 49) : elle est dans REGLES_VALIDEES
    # R17 a quitte cette liste le 23/11 (son message, et la preuve du passage 54) : elle est dans REGLES_VALIDEES
    # R19 a quitte cette liste le 23/11 (son message « tranche seul », et la preuve du passage 59)
    # R25 a quitte cette liste le 23/11 (son message « tranche seul », et la preuve de son passage)
    # R24 a quitte cette liste le 23/11 (son message « tranche seul », et la preuve de son passage)
    # R23 a quitte cette liste le 23/11 (son message « tranche seul », et la preuve de son passage)
    # R22 a quitte cette liste le 23/11 (son message « tranche seul », et la preuve de son passage)
    # R21 a quitte cette liste le 23/11 (son message « tranche seul », et la preuve de son passage)
    # R20 a quitte cette liste le 23/11 (son message « tranche seul », et la preuve de son passage)
}
# R16 : les mandants des biens au registre (mandants_texte), FIGES le 23/11 hors de l'image -- l'image ne porte que trois
#   colonnes du registre des mandats ; le fichier est verifie par son empreinte, le passage reste rejouable
MANDANTS_R16 = Path(r"C:\Hektor\chantier_classeur_q6_cache\protocole\mandants_des_biens_2026-11-23.json")
MANDANTS_R16_MD5 = "da3b63b6612813f29d66e4532008bac5"
STOP_R16 = {"SAS", "SARL", "EURL", "SOCIETE", "SOCIÉTÉ"}
# R7a et R7b ont quitte cette liste le 22/11 (son mot, reponses au rapport 21) : elles sont dans REGLES_VALIDEES
VARIANTES_ACTIVES: set = set()


def joue(regle: str) -> bool:
    """Une regle joue si elle est VALIDEE (toujours) ou si un passage de mesure l'active (--variantes) -- sauf pendant que la
    garde du deja-rendu rejoue un bien SANS elle (SUSPENDUES)."""
    return ((regle in REGLES_VALIDEES or regle in VARIANTES_ACTIVES) and regle not in SUSPENDUES
            and regle not in REGLES_RETIREES)


SUSPENDUES: set = set()
# LA GARDE DU DEJA-RENDU, BIEN PAR BIEN (23/11, son message : « verifie qu'aucun verdict rendu ne bouge ») : une regle de
#   cette liste ne joue sur un bien que si AUCUNE ligne tranchee SANS elle n'y change (ni etiquette, ni pieces) AVEC elle.
#   Sinon le bien est juge sans elle, et il est NOMME (GARDE_DEJA_RENDU) -- R15 avait echoue la-dessus le 23/11.
#   R28 (25/11) y entre : elle donne une vente, et ne doit faire bouger aucune ligne deja tranchee de son bien
REGLES_GARDEES = {"R22", "R25", "R28"}
GARDE_DEJA_RENDU: dict = {}


# LES PIECES MISES DE COTE par R7b dans le dernier passage : piece -> son ancien dossier, l'etiquette simulee, le reste
MISES_DE_COTE: dict = {}
# son mot du 22/11, point 4 : « Le bien 39845 : je veux toujours voir ces deux affaires moi-meme. Mets-les-moi de cote »
# ⭐ 39845 TRANCHE PAR LUI le 23/11 au soir (« Le bien 39845 : OUI, ta V3 a raison. J'ai lu. ») -- voir
#   PIECE_DONNEE_PAR_DECISION (19131, 19132, 19133) et RIEN_A_ETIQUETER_PAR_DECISION (SOF45TS3) ; le bien n'est plus a part
BIENS_A_SA_DECISION: dict = {}
# son mot du 23/11 au soir : « ⛔ Le piege du contact reutilise -- jamais de rattachement par le nom de l'acquereur. »
#   (les trois pieces de 39845 portent BAUDOIN ET PETIPAS chez Hektor : le premier acheteur, que Hektor recopie ; le gel du
#   16/11 les avait rangees a V3FO5NDA a l'etage 9 « sans mandat (acquereur + vendeur) », par les NOMS)
SA_DECISION_39845 = ("sa decision du 23/11 au soir : « OUI, ta V3 a raison. J'ai lu. Il y a eu trois tentatives sur ce bien, "
                     "pas deux » -- 6FQO29C8 (mandat 16263) prend le compromis 19131 et la vente 19133 (la date du compromis "
                     "au jour, la date de la vente au jour, les 6 000 EUR d'honoraires a l'euro, « 80 000 EUR » dans son "
                     "commentaire) ; V3FO5NDA (mandat 15459) ne garde que l'offre 19132 du 19/04/2023, la sienne au jour "
                     "exact ; SOF45TS3 (mandat 15920) : rien a etiqueter")
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
    # ⭐ UNE DECISION A LA MAIN, PAS UNE REGLE (son mot du 23/11) : « la REGLE est mauvaise (elle se trompe 9 fois) ; le
    #   CAS, lui, est prouve [...] On refuse la regle et on accepte le cas avec sa preuve ecrite -- exactement la methode
    #   des onze offres sures »
    "ZZ5WKMWM": ("23562", "sa decision du 23/11, A LA MAIN : offre 11206 du 02/12/2019 (sa case : 29/11/2019, +3 j, refusee, 280 000) et compromis 11205 (annule, SANS DATE, 280 000, honoraires 15 800 = sa Commission a l'euro), vendeur THEVENOT parmi les mandants, le seul bien a porter les deux ; personne ne tient ces pieces ; le Prix « 63 » du Sheet est une faute de frappe"),
    # ⭐ LES CINQ AFFAIRES SUR UN AUTRE BIEN -- sa decision du 23/11 au soir : « Les 5 rattachements : OUI, les cinq. [...]
    #   Ta preuve tient : deux dates au jour exact et les honoraires a l'euro, cinq fois de suite, et chaque bien ne porte
    #   qu'un seul numero, celui qui existe deja. Note au carnet que leur numero de mandat au Sheet est perime -- on ne
    #   croise jamais par le mandat. »
    "2U5QPKRC": ("37875", "sa decision du 23/11 au soir (les cinq) : compromis 17769 du 03/07/2018 au jour, honoraires 6 800 "
                          "a l'euro, vente 17770 du 14/12/2018 au jour -- D2018-0271 ; ⛔ son mandat 5030 au Sheet est perime"),
    "EJN79TJ1": ("53953", "sa decision du 23/11 au soir (les cinq) : offre 27713 du 27/02/2020 et compromis 27712 du "
                          "03/06/2020 au jour, honoraires 13 000 a l'euro, vente 27714 du 04/09/2020 au jour -- D2020-0110 ; "
                          "⛔ son mandat 12234 au Sheet est perime"),
    "MQ6H8TVQ": ("52460", "sa decision du 23/11 au soir (les cinq) : offre 26696 du 14/12/2017 et compromis 26695 du "
                          "27/12/2017 au jour, honoraires 1 000 a l'euro, vente 26698 du 06/07/2018 au jour -- D2017-0313 ; "
                          "⛔ son mandat 8644 au Sheet est perime"),
    "QXDW8EQA": ("2070", "sa decision du 23/11 au soir (les cinq) : offre 1028 du 11/01/2020 et compromis 1027 du 29/05/2020 "
                         "au jour, honoraires 39 000 a l'euro, vente 1029 du 04/11/2020 au jour -- D2020-0014 ; ⛔ son mandat "
                         "13411 au Sheet est perime"),
    "91IHSGNC": ("10229", "sa decision du 23/11 au soir (les cinq) : compromis 4781 du 18/09/2019 au jour, honoraires 4 900 a "
                          "l'euro, vente 4783 du 18/12/2019 au jour -- D2019-0311 ; ⛔ son mandat 611 au Sheet est perime"),
}
# ⭐ SES DEUX EXCEPTIONS NOMMEES (23/11 au soir) -- « ⛔ Ce sont des exceptions pour ces quatre lignes seulement, pas une
#   regle generale. » La ligne annulee SORT DU BIEN (elle n'entre pas dans sa coupe) et n'a rien a etiqueter ; la ligne
#   reglee prend le dossier. Le numero attendu est ecrit ici : le passage le redit, ou il crie.
DOUBLON_PAR_DECISION = {
    "E9XL0N5B": ("48145", "DTZ227ER", "D2020-0274",
                 "son exception nommee du 23/11 au soir : « DTZ227ER et E9XL0N5B sont la meme affaire saisie deux fois : "
                 "meme mandat 3968, meme bien, memes dates, meme prix 149 400 EUR, meme acquereur avec ses deux noms "
                 "inverses, commission corrigee de 10 400 a 9 400. DTZ227ER prend D2020-0274. E9XL0N5B : rien a "
                 "etiqueter. » -- une exception pour ces deux lignes seulement, pas une regle"),
    "IAYQ5OG2": ("9705", "L597FO6M", "D2021-0711",
                 "son exception nommee du 23/11 au soir : « L597FO6M et IAYQ5OG2 sont la meme affaire saisie deux fois : "
                 "meme mandat 13695, meme bien, meme offre, meme prix, meme commission 3 500 EUR, meme acquereur, seule la "
                 "date du compromis differe. L597FO6M garde son numero du 16/11, D2021-0711. IAYQ5OG2 : rien a "
                 "etiqueter. » -- une exception pour ces deux lignes seulement, pas une regle"),
}
# ses pieces donnees par decision (une preuve qu'il a validee et que les epreuves ne savent pas lire) : piece -> ligne
PIECE_DONNEE_PAR_DECISION = {
    14033: ("ea6a28a7", "sa decision du 23/11, OPTION B : son prix 140 500 et sa commission 9 500 sont ceux de DONNADIEU "
                        "et d'aucune autre ligne ; COLAS recoit le meme numero neuf dans les deux options (son D2025-0257 "
                        "du 16/11 a ete absorbe le 21/11 par la fusion E) -- B ne lui coute rien et tranche une ligne de plus"),
    30830: ("54376c72", "sa decision du 23/11 : 13 800 EUR = 12 000 + 1 800 a l'euro, DAUPHIN des deux cotes -- ⚠ la "
                        "case « Offre Achat » dit 11/11/2026, le commentaire de la meme ligne « 18.11 », l'offre est "
                        "proposee le 18/11 a 14:46 : on ne corrige pas une date, on corrige les lecteurs"),
    11206: ("ZZ5WKMWM", "sa decision du 23/11, A LA MAIN (pas une regle) : son offre -- offre 11206 du 02/12/2019 (sa case : 29/11/2019, +3 j, refusee, 280 000) et compromis 11205 (annule, SANS DATE, 280 000, honoraires 15 800 = sa Commission a l'euro), vendeur THEVENOT parmi les mandants, le seul bien a porter les deux ; personne ne tient ces pieces ; le Prix « 63 » du Sheet est une faute de frappe"),
    11205: ("ZZ5WKMWM", "sa decision du 23/11, A LA MAIN (pas une regle) : son compromis -- offre 11206 du 02/12/2019 (sa case : 29/11/2019, +3 j, refusee, 280 000) et compromis 11205 (annule, SANS DATE, 280 000, honoraires 15 800 = sa Commission a l'euro), vendeur THEVENOT parmi les mandants, le seul bien a porter les deux ; personne ne tient ces pieces ; le Prix « 63 » du Sheet est une faute de frappe"),
    # LE BIEN 39845 (sa decision du 23/11 au soir) -- jamais par le nom : les dates au jour et les honoraires
    19131: ("6FQO29C8", SA_DECISION_39845),
    19133: ("6FQO29C8", SA_DECISION_39845),
    19132: ("V3FO5NDA", SA_DECISION_39845),
    # ⭐ SES 64 DECISIONS DU VERROU (24/11) -- les 14 que le protocole laissait a part ; MES mesures en face (le texte et
    #   l'annulation rapatries viennent DU GEL : ils appuient, ils ne prouvent pas seuls -- sa P2, temoin 1 737 / 5 / 9)
    4126: ("P252U1JH", SON_MOT_DU_24_11 + " : compromis annule sans date, 77 000, honoraires 7 000 (la commission des deux "
                       "lignes) ; FOZ6HZLK a deja son compromis actif 4125 ; appui du gel : le texte de l'annulation et "
                       "l'annulation rapatriee du 22/01/2022 sont ceux de P252U1JH"),
    4327: ("PYG8JZ0C", SON_MOT_DU_24_11 + " : compromis annule sans date, 55 000, honoraires 4 500 (la commission des trois "
                       "lignes) ; ACB4D8WI a son compromis actif 4328, G41FTEZ8 son compromis annule 4329 au jour ; "
                       "PYG8JZ0C « retractation acq » ; appui du gel : l'annulation rapatriee du 01/08/2022"),
    4533: ("PCDZXTIY", SON_MOT_DU_24_11 + " : compromis annule sans date, 99 000, honoraires 7 000 (la commission des deux "
                       "lignes) ; FYNZEKI6 a son compromis actif 4534 ; appui du gel : « attente conf ecrite ACQ "
                       "retractation » et l'annulation rapatriee sont ceux de PCDZXTIY"),
    4542: ("RGCEC677", SON_MOT_DU_24_11 + " : compromis annule sans date, 108 000, honoraires 8 000 (la commission des trois "
                       "lignes) ; appui du gel : « PB de parcelle » et l'annulation rapatriee du 01/08/2021 sont ceux de "
                       "RGCEC677 ; ⚠ son prix 108 000 est aussi celui de l'offre 4544 de 40ELE6SQ -- le prix d'une affaire "
                       "annulee est le prix negocie (sa P3) : il n'exclut pas"),
    4560: ("QV5AYD2K", SON_MOT_DU_24_11 + " : compromis annule sans date, 60 000, honoraires 5 700 (la commission des deux "
                       "lignes) ; BNWNKPJH a son compromis actif 4561 ; appui du gel : « Auboyer/Basin BVx dossX » et "
                       "l'annulation rapatriee sont ceux de QV5AYD2K"),
    4621: ("TND2I31B", SON_MOT_DU_24_11 + " : compromis annule sans date, 50 000 ; ⚠ ses honoraires 5 000 sont la commission "
                       "de 0EMKY4ZS et de 910O0A2Q, pas de TND2I31B (4 500) -- sa P3 ; TND2I31B est la seule ligne annulee "
                       "du bien dont les cases portent un compromis (« Vente Prevue » 30/01/2021, « SAFER », « RETRACTATION "
                       "ACQ ») ; 910O0A2Q a son compromis actif 4622 ; appui du gel : texte et annulation de TND2I31B"),
    4669: ("GYGF5F1X", SON_MOT_DU_24_11 + " : compromis annule sans date, 16 800, honoraires 1 800 (la commission des deux "
                       "lignes) ; ZMQZSE9Q a son compromis actif 4670 ; appui du gel : « cpmis proc ACQ envoyee 27/4 » et "
                       "l'annulation rapatriee sont ceux de GYGF5F1X"),
    7710: ("9DK01H85", SON_MOT_DU_24_11 + " : compromis annule sans date, 135 000, honoraires 7 000 (la commission des deux "
                       "lignes) ; SWDW99J5 a son compromis actif 7711 ; appui du gel : l'annulation rapatriee du "
                       "01/12/2021"),
    17203: ("LNWLBVKG", SON_MOT_DU_24_11 + " : compromis annule sans date, 150 000 = les offres de LNWLBVKG et d'ODF1PWJ0, "
                        "honoraires 8 500 (la commission des trois lignes) ; OBBBCH0X a son compromis actif 17202 ; appui du "
                        "gel : l'annulation rapatriee du 01/08/2024 et son motif sont ceux de LNWLBVKG"),
    20088: ("5QE9107L", SON_MOT_DU_24_11 + " : compromis annule sans date, 50 000, honoraires 5 000 (la commission d'aucune "
                        "ligne : 4 700 et 0) ; appui du gel : « CUb negatif redepose » et l'annulation rapatriee du "
                        "21/06/2021 sont ceux de 5QE9107L"),
    21520: ("d2108609", SON_MOT_DU_24_11 + " : compromis annule sans date, 282 000, honoraires 12 000 (la commission des deux "
                        "lignes) ; 1c7b38f9 a son compromis actif 21521 ; appui du gel : « 20.8 annulation mail pj. 19.8 "
                        "annulation orale des acq » et l'annulation rapatriee sont ceux de d2108609"),
    4543: ("Z0BDVNBZ", SON_MOT_DU_24_11 + " : offre ACCEPTEE du 16/03/2022, 72 000 -- la seule offre acceptee du bien, dans "
                       "la chaine de son compromis actif 4541 (56 j plus tard : au-dela des 31 j de « par sa chaine ») ; "
                       "⚠ Z0BDVNBZ etait deja tranchee : elle gagne cette piece, son numero D2021-0130 ne change pas"),
    19820: ("4G2UHO35", SON_MOT_DU_24_11 + ", SA CORRECTION (§ 6) : offre refusee du 29/10/2019, 69 000, sur aucune case -- "
                        "la meme chaine et le meme dossier (D2019-0517) que 19819, au jour exact sur l'Offre Achat de "
                        "4G2UHO35 ; « sans cette correction, 4G2UHO35 ne recevait RIEN »"),
    19815: ("R7NU9NPM", SON_MOT_DU_24_11 + " : compromis annule sans date, 69 000, honoraires 5 980 (la commission de "
                        "R7NU9NPM ET de 4G2UHO35)"),
    19814: ("4G2UHO35", SON_MOT_DU_24_11 + ", SA REPONSE A SON DOUTE (§ 6 -> ses quatre reponses, ①) : compromis annule du "
                        "17/02/2020, 69 000, honoraires 5 980 (la commission des deux lignes) ; son acte prevu le 17/05/2020 "
                        "et 4G2UHO35 annulee le 20/05/2020 -- « une preuve de DATE, ni un nom, ni un mandat, conforme a P1 "
                        "et a P2 » ; contre : 7 j avant l'offre de 4G2UHO35 (24/02/2020), 16 j apres l'annulation de R7NU9NPM "
                        "(01/02/2020)"),
}
RIEN_A_ETIQUETER_PAR_DECISION = {
    "SOF45TS3": "sa decision du 23/11 au soir (bien 39845) : « SOF45TS3 (mandat 15920) : rien a etiqueter -- sa tentative, "
                "annulee le 23/09/2023, n'a laisse aucune piece chez Hektor »",
    "JZ9693S0": "sa decision du 23/11 : ni bien (mandat 92560 inconnu), ni nom ; ⚠ le fil FACTURE + AVOIR (GGTI00002792 / "
                "AVR00000465) dit que l'affaire a existe en comptabilite ; « reglee » au commentaire contre « Annulee » a "
                "l'etat : signale, pas tranche",
}
# SON MESSAGE DU 23/11 AU SOIR (point 2), verifie par lui DANS NOTRE COPIE DE HEKTOR (annonce relue a 04:23, mandat non
#   cloture ; 0 offre, 0 compromis, 0 vente) : deux affaires VIVANTES du Sheet qui ne sont saisies ni chez Hektor ni dans
#   l'app. « Mets-les de cote [...] la raison exacte -- AFFAIRE NON SAISIE, PAS AFFAIRE INTROUVABLE, la nuance compte -- et
#   garde-les rejugees a chaque passage : quand la saisie sera faite, elles doivent rentrer seules. »
#   ⛔ CE N'EST PAS UN VERDICT FIGE : le texte ne joue que dans la branche R8 (le bien nomme n'a AUCUNE piece) et seulement
#   si la ligne est toujours sur CE bien. Une saisie faite (une piece sur le bien) la fait passer E2 : elle est alors jugee
#   par les epreuves ordinaires, sans rien changer ici.
AFFAIRE_NON_SAISIE = {
    "130d81ac": ("62503", "18728", "mandat du 29/06/2026 au 28/09/2027 non cloture ; au Sheet « Compromis en attente », "
                                   "compromis du 05/11/2026, 5 000 EUR de commission"),
    "a8aaeb2b": ("61592", "18398", "mandat du 23/02/2026 au 23/02/2027 non cloture ; au Sheet « Vente fixee » au "
                                   "10/12/2026, 1 000 EUR de commission"),
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
    "14033 (bien 28506)": {
        "source": "son mot du 23/11 (16) : « 14033 : OPTION B. COLAS a le meme sort dans les deux cas, donc B ne coute rien "
                  "et tranche une ligne de plus -- et la preuve donne 140 500 / 9 500 a DONNADIEU, a personne d'autre »",
        "remplace": "sa B3 du 20/11 soir (14033 a part) -- et son attendu « 14033 a personne » des 20 a part",
        "lignes": {"ea6a28a7": [14033]}},
    "les cinq rattachements (23/11 au soir)": {
        "source": "sa decision du 23/11 au soir : « Les 5 rattachements : OUI, les cinq. »",
        "remplace": "AFFAIRE_SUR_UN_AUTRE_BIEN (la ligne etait sur le bien de son mandat, perime)",
        "lignes": {"2U5QPKRC": [17769, 17770], "EJN79TJ1": [27712, 27713, 27714], "MQ6H8TVQ": [26695, 26696, 26698],
                   "QXDW8EQA": [1027, 1028, 1029], "91IHSGNC": [4781, 4783]}},
    "les deux doublons (23/11 au soir)": {
        "source": "ses deux exceptions nommees du 23/11 au soir (DOUBLON_PAR_DECISION) -- pas une regle",
        "remplace": "DEUX_LIGNES_UN_DOSSIER (R13 ne les prenait pas : commission / compromis differents)",
        "lignes": {"DTZ227ER": [24440, 24441, 24442], "L597FO6M": [4445, 4446, 4447]}},
    "ses 64 decisions du verrou (24/11)": {
        "source": "son mot du 24/11 (MOT_DU_24_11_LES_64_TRANCHEES_LES_REGLES_ET_LE_CONTROLE.md) et le detail "
                  "SES_64_DECISIONS_DU_VERROU_23_11.md : « J'ai tranche les 64 transactions libres des 14 biens du verrou, "
                  "une par une » -- les vraies pieces de chaque ligne, telles que son fichier les ecrit ; 19814 : SA "
                  "REPONSE du 24/11 (ses quatre reponses, ①) la donne a 4G2UHO35 -- son fichier l'ecrivait a R7NU9NPM",
        "remplace": "VERROU_PIECE_PLUS_PETITE (28 lignes), COPIE_SEULE (d2108609) ; sa B3 du 21/11 pour onze de ses 20 a "
                    "part ; la paire DEBARD des jumelles (§ 18.9, ma mesure du 10/11) : il en fait DEUX affaires",
        "lignes": {'FOZ6HZLK': [4125, 4127, 4129], 'P252U1JH': [4126, 4128], 'ACB4D8WI': [4328, 4332, 4333],
                   'G41FTEZ8': [4329, 4330], 'PYG8JZ0C': [4327, 4331], 'FYNZEKI6': [4534, 4535, 4537],
                   'PCDZXTIY': [4533, 4536], 'Z0BDVNBZ': [4541, 4543, 4546], '40ELE6SQ': [4544],
                   'RGCEC677': [4542, 4545], 'BNWNKPJH': [4561, 4562, 4564], 'QV5AYD2K': [4560, 4563],
                   '910O0A2Q': [4622, 4624, 4626], '0EMKY4ZS': [4623], 'TND2I31B': [4621, 4625],
                   'ZMQZSE9Q': [4670, 4671, 4673], 'GYGF5F1X': [4669, 4672], 'SWDW99J5': [7711, 7713, 7714],
                   '9DK01H85': [7710, 7712], 'AYIHPHF5': [14109, 14112, 14115], 'Z3DYDC4X': [14111, 14113],
                   'L2B2WGCF': [14114], 'OBBBCH0X': [17202, 17204, 17207], 'ODF1PWJ0': [17205],
                   'LNWLBVKG': [17203, 17206], 'MYILWKZQ': [19816, 19817, 19821], '4G2UHO35': [19814, 19819, 19820],
                   'R7NU9NPM': [19815, 19818], 'ZW7MKTWH': [20089], '5QE9107L': [20088, 20090],
                   'd2108609': [21520], '1c7b38f9': [21521, 21522, 21523], 'UM4ZU2SX': [27607, 27608, 27611],
                   'OAUI9CKR': [27610]}},
    "39845 (bien 39845)": {
        "source": SA_DECISION_39845,
        "remplace": "A_SA_DECISION (son mot du 22/11, point 4) -- et le temoin a_sa_decision",
        "lignes": {"6FQO29C8": [19131, 19133], "V3FO5NDA": [19132]}},
    "3741 sortie de ses neuf a part (25/11 au soir)": {
        "source": "son mot du 25/11 au soir : « HUY49KEC : oui, sors 3741 de mes neuf pieces a part [...] La raison de la "
                  "mise a part a disparu. Sors-la, et laisse R28 lui donner D2018-0476. »",
        "remplace": "sa mise a part du 21/11 (a20 : « date 2018-11-23 sur aucune case, honoraires inconnus ») -- le temoin "
                    "a_part_20 ne l'attend plus « a personne »",
        "lignes": {"HUY49KEC": [3741]}},
}
#: ⭐ SON MOT DU 26/11 : « Tes 30 ecarts : je les ai nommes un par un [...] Les trois neufs sont tous sur le temoin v3, et ce
#  sont mes trois decisions [...] Aucun n'est une regression : ce sont trois attentes perimees. Mets-les a jour dans le
#  temoin v3 avant ce soir, en nommant chacune par ma decision et sa date. Sinon elles crieront chaque nuit pour rien. »
#  -- la V3 (22/11) attendait l'etat d'AVANT ses decisions ; pour ces trois lignes seulement, l'attendu du temoin v3 devient
#  celui de sa decision (pieces vraies ET copies, comme la V3 les compare), et le temoin ecrit la decision dans l'attendu.
V3_ATTENDU_PAR_SA_DECISION = {
    "HUY49KEC": {"pieces": [3741, 1001587],
                 "decision": "sa decision du 25/11 au soir : 3741 sortie de ses neuf a part, R28 lui donne D2018-0476"},
    "P252U1JH": {"pieces": [4126, 4128],
                 "decision": "sa decision du 24/11 (ses 64 du verrou : 4126 + 4128), realisee par le retrait de 4126 de la "
                             "liste E a la vague du 25/11 (09:02)"},
    "d2108609": {"pieces": [21520, 1001495],
                 "decision": "sa decision du 24/11 (ses 64 du verrou : 21520), realisee par le retrait de 21520 de la liste E "
                             "a la vague du 25/11 (09:02)"},
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


# ⛔ SON MOT DU 25/11 : « LE JUGE PEUT CHANGER D'AVIS SANS QUE SON EMPREINTE BOUGE [...] fais entrer dans l'empreinte du
#   juge TOUTES ses entrees vivantes [...] Nomme-les-moi, je veux savoir de quoi depend un verdict. »
#   UN VERDICT DEPEND DE (inventaire du 25/11 : toutes les lectures de protocole_classeur.py, coupe_preuve_interne.py et
#   piece_copie_ou_vraie.py pendant un passage) :
#     . L'IMAGE -- sheet.json, registre.sqlite, gel.json, t6_photo.json : leur empreinte est au manifeste, verifiee ;
#     . LE CODE -- les trois fichiers de CODE : md5_code() ;
#     . TROIS ENTREES LUES AU MOMENT DE JUGER, hors de l'image et du code -- celles-ci :
#         ① EXCLUES_DE_LA_REGLE_E de phase2/sync/affaire_ledger.py (son arbre de syntaxe) -- la vague du 25/11 en a retire
#           4126 et 21520 : P252U1JH et d2108609 changent au rejeu (prouve sur copie) ;
#         ② « a20 » de v3_calcul.json (ses 20 a part), moins SORTIES_DES_20_PAR_DECISION ;
#         ③ mandants_des_biens_2026-11-23.json (R16) -- deja garde par MANDANTS_R16_MD5.
#   (temoins.json et les trois CSV du 19-22/11 ne servent qu'aux TEMOINS du passage, pas aux verdicts.)
#   L'empreinte porte sur CE QUE LE JUGE UTILISE (la liste E, pas tout affaire_ledger.py qui change pour d'autres raisons),
#   lu par les memes fonctions que le jugement : une entree injectee pour un rejeu y apparait telle quelle.
def entrees_vivantes() -> dict[str, str]:
    def md5_de(x) -> str:
        return hashlib.md5(json.dumps(x, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return {"EXCLUES_DE_LA_REGLE_E (phase2/sync/affaire_ledger.py)": md5_de(sorted(exclues_de_la_regle_e().items())),
            "a20 (v3_calcul.json, ses 20 a part)": md5_de(sorted(les_20_a_part())),
            "mandants R16 (%s)" % MANDANTS_R16.name: md5_fichier(MANDANTS_R16)}


def empreinte_du_juge() -> str:
    """L'empreinte du juge ENTIER : son code ET ses entrees vivantes (l'image a la sienne, au manifeste)."""
    h = hashlib.md5(md5_code().encode("ascii"))
    for k, v in sorted(entrees_vivantes().items()):
        h.update(("%s=%s;" % (k, v)).encode("utf-8"))
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
        # SES DEUX EXCEPTIONS NOMMEES (23/11 au soir) : la ligne annulee sort du bien -- elle n'entre pas dans sa coupe
        for i, (b, _reglee, _num, _pourquoi) in DOUBLON_PAR_DECISION.items():
            if i in self.sheet["par_id"]:
                self.D.lignes_bien[b].discard(i)


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


#: ⛔ SON MOT DU 25/11 : « Fais qu'un rejeu sur copie ne PUISSE PLUS ecrire dans le vrai socle, meme par erreur. » Un rejeu
#  inscrit ici le VRAI socle : socle() refuse de l'ouvrir, quel que soit le chemin qu'on a oublie de detourner.
SOCLES_INTERDITS: set = set()


def socle() -> sqlite3.Connection:
    if Path(SOCLE).resolve() in {Path(p).resolve() for p in SOCLES_INTERDITS}:
        raise SystemExit("⛔ le socle %s est INTERDIT a ce processus (rejeu sur copie) : rien n'y est ecrit" % SOCLE)
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


def rien_par_r16(I: Image, i: str, tenues: set) -> str | None:
    """REGLE R16 (validee le 23/11, passage 49) : la ligne « Annulee » sans bien dont l'affaire n'a aucune piece chez Hektor. Rend le texte du
    motif RIEN_A_ETIQUETER, ou None. `tenues` : les pieces que les verdicts du passage donnent deja (et ses decisions)."""
    D = I.D
    if D.case(i, "Etat Actuel").strip() != "Annulée" or I.gel_par_ligne.get(i):
        return None
    ns = {x for x in re.findall(r"[A-ZÀ-Ü][A-ZÀ-Ü'\-]{2,}", D.case(i, "Vendeur").upper())
          if x not in STOP_VENDEUR | STOP_R16}
    if not ns:
        return None
    if not hasattr(I, "_vendeur_r16"):
        brut = MANDANTS_R16.read_bytes()
        if hashlib.md5(brut).hexdigest() != MANDANTS_R16_MD5:
            raise SystemExit("⛔ R16 : %s n'a plus son empreinte" % MANDANTS_R16)
        par_nom = defaultdict(set)
        for b, t in json.loads(brut.decode("utf-8"))["biens"].items():
            for x in set(re.findall(r"[A-ZÀ-Ü][A-ZÀ-Ü'\-]{2,}", t.upper())):
                par_nom[x].add(b)
        for a, p in I.pieces.items():
            for x in set(re.findall(r"[A-ZÀ-Ü][A-ZÀ-Ü'\-]{2,}", str(p.get("mandants_json") or "").upper())):
                par_nom[x].add(D.REG[a]["bien"])
        I._vendeur_r16 = par_nom
    biens = set().union(*(I._vendeur_r16.get(n, set()) for n in ns))
    if not biens:
        return None                                      # le vendeur n'est pas trouve : la 1re cause de ratee n'est pas ecartee
    d_off, d_cpr = K.d_sheet(D.case(i, "Offre Achat")), K.d_sheet(D.case(i, "Compromis"))
    if not (d_off or d_cpr):
        return None
    vues = []
    for b in biens:
        for a in D.par_bien.get(b, []):
            r = D.REG[a]
            if I.nature[a] != PC.VRAIE or r["genre"] not in ("offre", "compromis"):
                continue
            ref = d_off if r["genre"] == "offre" else (d_cpr or d_off)
            if r["date"] and (not ref or abs((r["date"] - ref).days) > 365):
                continue
            if a not in tenues:
                return None                              # une piece libre (a un an, ou sans date) peut etre son affaire
            vues.append(a)
    return ("REGLE R16 : « Annulee », sans bien ; son vendeur (%s) est mandant de %d bien(s), et %s : son affaire n'a "
            "aucune piece chez Hektor -- rien a etiqueter" % ("/".join(sorted(ns)), len(biens),
            "ces biens n'ont aucune vraie piece a un an de sa case" if not vues else
            "leurs %d vraie(s) piece(s) a un an de sa case sont toutes tenues par d'autres lignes" % len(vues)))


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
    if i in DOUBLON_PAR_DECISION:
        return attente("RIEN_A_ETIQUETER", DOUBLON_PAR_DECISION[i][3])
    if not biens:
        return attente("SANS_BIEN")
    if len(biens) > 1 and bien_par_p1(I, i):
        biens = [bien_par_p1(I, i)]              # LA REGLE P1, validee le 22/11 (REGLES_VALIDEES)
        base["biens"] = biens
    if len(biens) > 1 and joue("R10") and bien_par_r10(I, i):
        biens = [bien_par_r10(I, i)]             # REGLE R10 (validee le 23/11)
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
            if i in AFFAIRE_NON_SAISIE and AFFAIRE_NON_SAISIE[i][0] == b:
                _b, mandat_, quoi_ = AFFAIRE_NON_SAISIE[i]
                return attente("RIEN_A_ETIQUETER", "AFFAIRE NON SAISIE (pas introuvable) -- mise de cote par sa decision du "
                                                   "23/11 au soir : bien %s, mandat %s (%s) ; ni chez Hektor ni dans l'app "
                                                   "(0 offre, 0 compromis, 0 vente) ; rejugee a chaque passage, elle rentre "
                                                   "seule des que la saisie est faite" % (b, mandat_, quoi_))
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


_EXCLUES_E: dict = {}


def exclues_de_la_regle_e() -> dict:
    """SES EXCLUSIONS DE LA REGLE E (19 et 20/11) -- lues dans le module de production SANS l'executer (le dictionnaire
    EXCLUES_DE_LA_REGLE_E de phase2/sync/affaire_ledger.py, par son arbre de syntaxe)."""
    if not _EXCLUES_E:
        import ast
        arbre = ast.parse((RACINE / "phase2" / "sync" / "affaire_ledger.py").read_text(encoding="utf-8"))
        for n in arbre.body:
            cible = n.target if isinstance(n, ast.AnnAssign) else (n.targets[0] if isinstance(n, ast.Assign) else None)
            if isinstance(cible, ast.Name) and cible.id == "EXCLUES_DE_LA_REGLE_E":
                _EXCLUES_E.update(ast.literal_eval(n.value))
        if not _EXCLUES_E:
            raise SystemExit("⛔ EXCLUES_DE_LA_REGLE_E introuvable dans phase2/sync/affaire_ledger.py")
    return _EXCLUES_E


def invisible_a_la_nuit(I: Image, a: int) -> bool:
    """P-a (23/11 soir, le rejeu exact du passage 73) : une transaction SANS DATE, exclue de la regle E par SA decision,
    SEULE dans sa chaine -- le chainage ne la met jamais dans la liste des dossiers du bien (affaire_ledger : « sans date
    restee invisible ») : aucune coupe, aucun rattachement ne la trouve. Comme une piece supprimee chez Hektor, elle reste
    figee dans son dossier."""
    if I.D.REG[a]["date"] is not None or a not in exclues_de_la_regle_e():
        return False
    ch = I.pieces[a]["app_chaine_id"]
    return all(q == a for q in I.D.par_bien.get(I.D.REG[a]["bien"], []) if I.pieces[q]["app_chaine_id"] == ch)


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
    return bien_par_p1(I, i) or (bien_par_r10(I, i) if joue("R10") else None)


def bien_par_r10(I: Image, i: str) -> str | None:
    """R10 : parmi les biens que la ligne nomme, le SEUL ou elle a des pieces vraies PROUVEES (la coupe du bien entier,
    comme le passage). Mesure du 23/11 : 22 des 23 lignes du paquet PLUSIEURS_BIENS -- toujours le bien du gel."""
    D = I.D
    if not hasattr(I, "_coupes"):
        I._coupes = {}
    avec = []
    for b in sorted(I.biens_de_ligne.get(i, set())):
        if b not in I._coupes:
            S = {q: I.pieces[q]["app_chaine_id"] for q in D.par_bien.get(b, [])}
            I._coupes[b] = K.couper_le_bien(D, b, set(D.lignes_bien.get(b, set())), S, sorted(D.par_bien.get(b, [])),
                                            A_PART_PAR_DECISION,
                                            {a_: l_ for a_, (l_, _w) in PIECE_DONNEE_PAR_DECISION.items()})
        r = I._coupes[b]
        if any(i in ls and I.nature[a] == PC.VRAIE for a, ls in r["va"].items()):
            avec.append(b)
    return avec[0] if len(avec) == 1 else None


def jumelle_annulee(I: Image, gl, ids) -> tuple | None:
    """R13 : (la ligne du gel, la jumelle annulee) quand l'une des deux lignes est « Annulee », n'a AUCUNE piece du morceau a
    son gel, et porte le MEME Prix et la MEME date d'offre que l'autre, dont le gel tient des pieces du morceau."""
    D = I.D
    a_, b_ = sorted(gl)
    for x, y in ((a_, b_), (b_, a_)):
        gel_y = {int(g["piece"]) for g in I.gel_par_ligne.get(y, [])} & set(ids)
        gel_x = {int(g["piece"]) for g in I.gel_par_ligne.get(x, [])} & set(ids)
        if D.case(y, "Etat Actuel").strip() != "Annulée" or gel_y or not gel_x:
            continue
        if nombre_case(D.case(x, "Prix")) is None or nombre_case(D.case(x, "Prix")) != nombre_case(D.case(y, "Prix")):
            continue
        # son mot du 23/11 : « une regle n'avale pas son propre ecart » -- la MEME commission (E9XL0N5B : 10 400 contre
        #   9 400 -> deux affaires ou une renegociation) et le MEME compromis quand les deux en ont un (IAYQ5OG2 : 24/02
        #   contre 28/03/2022) ; et « R13 ne doit pas pouvoir fabriquer une exception toute seule » : le dossier ne porte
        #   qu'UNE piece de chaque genre (une seule affaire -- jamais une paire du genre VIALLARD / PAOLONE)
        if nombre_case(D.case(x, "Commission TTC")) != nombre_case(D.case(y, "Commission TTC")):
            continue
        cx, cy = K.d_sheet(D.case(x, "Compromis")), K.d_sheet(D.case(y, "Compromis"))
        if cx and cy and cx != cy:
            continue
        genres = Counter(D.REG[q]["genre"] for q in ids if q in D.REG and I.nature[q] == PC.VRAIE)
        if any(n > 1 for n in genres.values()):
            continue
        dx, dy = K.d_sheet(D.case(x, "Offre Achat")), K.d_sheet(D.case(y, "Offre Achat"))
        if dx and dx == dy:
            return x, y
    return None


def pas_jumelle_pourquoi(I: Image, gl) -> str:
    """La raison NOMMEE pour laquelle R13 ne prend pas une paire « Vente reglee » / « Annulee » au meme Prix et a la meme
    date d'offre (son mot du 23/11 : « elle reste en attente avec sa raison nommee, et tu la remontes a Frederic »)."""
    D = I.D
    a_, b_ = sorted(gl)
    for x, y in ((a_, b_), (b_, a_)):
        if D.case(y, "Etat Actuel").strip() != "Annulée":
            continue
        if nombre_case(D.case(x, "Prix")) != nombre_case(D.case(y, "Prix")) or not K.d_sheet(D.case(x, "Offre Achat"))                 or K.d_sheet(D.case(x, "Offre Achat")) != K.d_sheet(D.case(y, "Offre Achat")):
            continue
        if nombre_case(D.case(x, "Commission TTC")) != nombre_case(D.case(y, "Commission TTC")):
            return (" ; R13 NE LA PREND PAS : la commission differe (%s contre %s) -- deux affaires ou une renegociation, "
                    "a Frederic" % (D.case(y, "Commission TTC").strip(), D.case(x, "Commission TTC").strip()))
        cx, cy = K.d_sheet(D.case(x, "Compromis")), K.d_sheet(D.case(y, "Compromis"))
        if cx and cy and cx != cy:
            return (" ; R13 NE LA PREND PAS : l'annulee a son propre compromis (%s contre %s) -- un doublon mal saisi ou un "
                    "premier compromis annule, a Frederic" % (cy, cx))
    return ""


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
        # ⭐ 24/11 (§ 1 bis) : « ces onze-la n'y sont plus » -- la source ne change pas (elle reste le temoin)
        _A_PART_20.difference_update(SORTIES_DES_20_PAR_DECISION)
    return _A_PART_20


def regle_r9(I: Image, b: str, lignes_b: set, r: dict) -> dict:
    """R9 : pour chaque ligne du bien qui ne tient que des copies C5, la vraie piece que SON GEL lui donne -- si elle est a
    part, que le gel ne la donne a aucune autre ligne, que ses honoraires sont la Commission TTC de la ligne, et qu'aucune
    autre ligne n'a son prix + honoraires. Rend {piece: (ligne, preuve)}. Temoin du 23/11 (toutes les lignes) : quand le
    gel nomme une vraie piece pour une seule ligne et que ses honoraires sont la commission, la preuve la donne a CETTE
    ligne 4 208 fois, a une AUTRE 8 fois, et la laisse a part 53 fois."""
    D = I.D
    out = {}
    # les lignes SANS vraie piece prouvee : celles dont le morceau n'a que des copies (COPIE_SEULE), et celles qui n'ont
    #   AUCUN morceau (SES_PIECES_A_PART) -- jamais une ligne deja tranchee (elle ne gagne rien, rien ne lui est retire)
    lignes_sans = [next(iter(gl)) for gl, ids in r["morceaux"].items()
                   if len(gl) == 1 and not any(I.nature[q] == PC.VRAIE for q in ids)]
    lignes_sans += sorted(lignes_b - {x for gl in r["morceaux"] for x in gl})
    for i in lignes_sans:
        vraies_gel = sorted({int(g["piece"]) for g in I.gel_par_ligne.get(i, [])
                             if int(g["piece"]) in D.REG and D.REG[int(g["piece"])]["bien"] == b
                             and I.nature.get(int(g["piece"])) == PC.VRAIE})
        for a in vraies_gel:
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
                    # VARIANTE R15 (proposee le 23/11) : l'offre dont la date est proche (7 j) de SA case, et d'aucune autre
                    dt_ = D.REG[a]["date"]
                    if (joue("R15") or joue("R22")) and D.REG[a]["genre"] == "offre" and dt_:
                        proches = [j for j in lignes_b if K.d_sheet(D.case(j, "Offre Achat"))
                                   and abs((dt_ - K.d_sheet(D.case(j, "Offre Achat"))).days) <= 7]
                        if proches == [i]:
                            out[a] = (i, ("REGLE R22 (R15 sous la garde du deja-rendu)" if joue("R22") else "REGLE R15 (variante)") + " : le gel du 16/11 ne la donne qu'a cette ligne ; sa date %s "
                                         "tombe a %d jour(s) de sa case « Offre Achat », et a 7 jours d'aucune autre ligne" % (
                                             dt_, abs((dt_ - K.d_sheet(D.case(i, "Offre Achat"))).days)))
                    continue
                out[a] = (i, "REGLE R9b (validee le 23/11) : le gel du 16/11 ne la donne qu'a cette ligne ; honoraires inconnus, son "
                             "montant %d = le « Prix » de la ligne, qu'aucune autre ligne du bien n'a" % prix)
                continue
            if not joue("R9") or round(h) != com or any(D.touche_ph(a, j) for j in lignes_b if j != i):
                continue
            # L'EXCEPTION NOMMEE (son mot (16), « nomme tes huit ») : les 8 ecarts du temoin avaient TOUS une autre ligne
            #   du bien a la MEME Commission TTC -- les honoraires collaient par hasard. Commission unique : 3 838 / 0.
            if any(nombre_case(D.case(j, "Commission TTC")) == com for j in lignes_b if j != i):
                continue
            out[a] = (i, "REGLE R9 (validee le 23/11) : le gel du 16/11 ne la donne qu'a cette ligne, et ses honoraires %d = sa "
                         "« Commission TTC » ; aucune autre ligne n'a son prix + honoraires" % com)
    return out


# R17 (validee le 23/11) : les deux moities d'une affaire TOMBEE, dans la meme chaine Hektor
AUTRE_MOITIE_R17 = {("compromis", "cancelled"): ("offre", "refused"), ("offre", "refused"): ("compromis", "cancelled")}


def regle_r17(I: Image, b: str, r: dict) -> dict:
    """R17 (VALIDEE le 23/11, son message ; mesuree sur son mot (20) du verrou) : LA SOEUR DE CHAINE. Une affaire tombee laisse deux pieces dans
    la MEME chaine Hektor : son compromis ANNULE et son offre REFUSEE, au meme montant. Quand l'une est A PART et que
    l'autre -- sa soeur UNIQUE dans la chaine, et reciproquement -- est prouvee a UNE seule ligne, la piece a part suit sa
    soeur. Ses trois gardes : g1 les dates (contre_dates) ; g2 l'offre n'est pas datee apres le compromis ; g3 la ligne ne
    tient deja aucune vraie piece du genre de la piece (sinon : deux affaires, ou une renegociation -- elle s'abstient).
    Temoin (protocole_le_verrou_mesure_2026-11-23.py, section 6) : rejouee dans les deux sens sur les 302 paires tenues au
    passage 51 -- 581 la bonne ligne, 0 une autre, 23 abstentions (dont les 4 cas des chaines 2393 et 23353, qui melent
    deux affaires au meme prix affiche). Rend {piece: (ligne, preuve)}."""
    D = I.D
    S = {a: I.pieces[a]["app_chaine_id"] for a in D.par_bien.get(b, [])}

    def soeurs(a: int) -> list:
        p = D.REG[a]
        k = AUTRE_MOITIE_R17.get((p["genre"], p["etat"]))
        if not k or p["montant"] is None:
            return []
        return [q for q in D.par_bien.get(b, []) if q != a and S.get(q) == S.get(a) and I.nature[q] == PC.VRAIE
                and (D.REG[q]["genre"], D.REG[q]["etat"]) == k and D.REG[q]["montant"] is not None
                and abs(D.REG[q]["montant"] - p["montant"]) <= 1]
    out = {}
    for a in sorted(r["apart"]):
        if I.nature[a] != PC.VRAIE or a in les_20_a_part() or a in A_PART_PAR_DECISION:
            continue
        s = soeurs(a)
        if len(s) != 1 or len(soeurs(s[0])) != 1:
            continue
        q = s[0]
        ls = r["va"].get(q)
        if not ls or len(ls) != 1:
            continue
        L = next(iter(ls))
        if D.contre_dates(a, {L}):
            continue                                                       # g1
        o, cp = (a, q) if D.REG[a]["genre"] == "offre" else (q, a)
        if D.REG[o]["date"] and D.REG[cp]["date"] and D.REG[o]["date"] > D.REG[cp]["date"]:
            continue                                                       # g2
        if [x for x, l_ in r["va"].items() if L in l_ and x != a and I.nature[x] == PC.VRAIE
                and D.REG[x]["genre"] == D.REG[a]["genre"]]:
            continue                                                       # g3
        # g4 (passage 52 -> 53) : JAMAIS A UNE LIGNE DEJA TRANCHEE. Sans elle, le passage 52 donnait la piece a 23 lignes
        #   deja tranchees (etiquette identique, une piece de plus) et faisait bouger un temoin (0OO1BEZD : coupes_29 +1
        #   accord, V3 +1 ecart, V3 neutres +1 ecart) -- « un temoin parfait ne rachete pas un effet de bord sur du
        #   deja-rendu ». La piece n'est donnee que si elle devient la PLUS PETITE vraie piece de la ligne : la ligne etait
        #   alors retenue par elle (verrou) ou sans vraie piece -- elle n'avait pas de verdict rendu.
        #   ET (passage 53 -> 54) : la piece doit etre possible pour PLUSIEURS lignes. Possible pour cette seule ligne,
        #   R7a (deja dans son dossier) ou R7b (mise de cote) la tient deja et la ligne est tranchee SANS elle -- le
        #   passage 53 la donnait encore a 4 lignes rendues par R7a (7Y9XCYOJ, J1FY054Q, O8BY6AC8, XP7WNTKK), contre le
        #   texte valide de R7a (« elle reste a part, jamais donnee a la ligne »).
        vraies_L = [x for x, l_ in r["va"].items() if L in l_ and I.nature[x] == PC.VRAIE]
        if (vraies_L and a > min(vraies_L)) or len(r["possibles"].get(a, [])) < 2:
            continue                                                       # g4
        out[a] = (L, "REGLE R17 (validee le 23/11) : sa soeur de chaine %d (%s %s, meme montant %d) est prouvee a cette ligne -- "
                     "l'autre moitie de la meme affaire tombee" % (q, D.REG[q]["genre"], D.REG[q]["etat"],
                                                                   round(D.REG[q]["montant"])))
    return out


def restantes_r11(I: Image, b: str, i: str, X: list, r: dict, pourquoi: int | None = None):
    """Les vraies pieces du bien qui pourraient ENCORE etre l'affaire de la ligne i (R11 ne la ferme que s'il n'en reste
    aucune) : celles qui ne sont prouvees a aucune ligne, MOINS --
      R23 (23/11) celles datees a plus d'UN AN de toutes les cases de date de la ligne (temoin T2 : 0 piece prouvee sur
          12 237 n'est a plus d'un an de sa ligne) ;
      R24 (23/11, ligne « Annulee » seulement) les VENTES dont la chaine porte un compromis ACTIF au meme montant, prouve a
          une AUTRE ligne (temoins : T1, 803 « Annulee » tranchees sur 804 ne tiennent aucune vente -- l'ecart LQXGFCKH
          tient la vente de SA chaine ; T4, 3 608 ventes sur 3 609 sont a la ligne du compromis actif de leur chaine -- l'ecart
          17027 va a l'acheteur suivant, jamais a la ligne annulee).
    Avec `pourquoi` : rend la raison pour laquelle CETTE piece est hors de son affaire."""
    D = I.D
    cases = [d for d in (K.d_sheet(D.case(i, c)) for c in ("Offre Achat", "Compromis", "Signé", "Vente Prévue",
                                                           "Vente Fixée", "Signée", "Vente Réglée", "Annulée")) if d]
    annulee = D.case(i, "Etat Actuel").strip().startswith("Annul")
    out, raison = [], {}
    for q in X:
        if q in r["va"] or I.nature[q] != PC.VRAIE:
            continue
        p = D.REG[q]
        if joue("R23") and p["date"] and cases and min(abs((p["date"] - d).days) for d in cases) > 365:
            raison[q] = "REGLE R23 : datee le %s, a plus d'un an de toutes ses cases" % p["date"]
            continue
        if joue("R24") and annulee and p["genre"] == "vente" and p["montant"] is not None:
            ch = I.pieces[q]["app_chaine_id"]
            cps = [c_ for c_ in D.par_bien.get(b, []) if I.pieces[c_]["app_chaine_id"] == ch
                   and D.REG[c_]["genre"] == "compromis" and D.REG[c_]["etat"] == "active" and I.nature[c_] == PC.VRAIE
                   and D.REG[c_]["montant"] is not None and abs(D.REG[c_]["montant"] - p["montant"]) <= 1]
            if len(cps) == 1 and r["va"].get(cps[0]) and i not in r["va"][cps[0]]:
                raison[q] = ("REGLE R24 : une vente, dont le compromis actif %d de sa chaine est prouve a %s -- une affaire "
                             "annulee n'a pas de vente" % (cps[0], "+".join(sorted(r["va"][cps[0]]))))
                continue
        out.append(q)
    if pourquoi is not None:
        return raison.get(pourquoi, "")
    return out


def reconnues_r20(I: Image, b: str, r: dict) -> dict:
    """R20 (23/11) : LA SOEUR DE CHAINE RECONNAIT SANS DONNER. Une vraie piece A PART dont la soeur de chaine (le critere de
    R17 : compromis ANNULE <-> offre REFUSEE, unique et reciproque dans la chaine, meme montant ; g1 les dates, g2 l'ordre,
    g3 un seul de son genre) est prouvee a une ligne L DEJA TRANCHEE, dont elle n'est PAS la plus petite (l'etiquette de L
    ne depend pas d'elle -- c'est pourquoi la g4 de R17 la refuse), est RECONNUE comme une piece de l'affaire de L : elle
    reste a part (jamais donnee, rien ne change pour L), mais elle ne retient plus AUCUNE AUTRE ligne au verrou. Sa decision
    du 23/11 (« les 3 offres sur une ligne deja tranchee : non [...] c'est du deja-rendu ») est tenue : on ne touche pas a
    L. Temoin : celui de R17 (581 la bonne ligne, 0 une autre). Rend {piece: (ligne L, soeur)}."""
    D = I.D
    S = {a: I.pieces[a]["app_chaine_id"] for a in D.par_bien.get(b, [])}

    def soeurs(a: int) -> list:
        p = D.REG[a]
        k = AUTRE_MOITIE_R17.get((p["genre"], p["etat"]))
        if not k or p["montant"] is None:
            return []
        return [q for q in D.par_bien.get(b, []) if q != a and S.get(q) == S.get(a) and I.nature[q] == PC.VRAIE
                and (D.REG[q]["genre"], D.REG[q]["etat"]) == k and D.REG[q]["montant"] is not None
                and abs(D.REG[q]["montant"] - p["montant"]) <= 1]
    out = {}
    for a in sorted(r["apart"]):
        if I.nature[a] != PC.VRAIE or a in les_20_a_part() or a in A_PART_PAR_DECISION:
            continue
        s = soeurs(a)
        if len(s) != 1 or len(soeurs(s[0])) != 1:
            continue
        q = s[0]
        ls = r["va"].get(q)
        if not ls or len(ls) != 1:
            continue
        L = next(iter(ls))
        if D.contre_dates(a, {L}):
            continue
        o, cp = (a, q) if D.REG[a]["genre"] == "offre" else (q, a)
        if D.REG[o]["date"] and D.REG[cp]["date"] and D.REG[o]["date"] > D.REG[cp]["date"]:
            continue
        vraies_L = [x for x, l_ in r["va"].items() if L in l_ and I.nature[x] == PC.VRAIE]
        if [x for x in vraies_L if x != a and D.REG[x]["genre"] == D.REG[a]["genre"]]:
            continue
        if not vraies_L or a < min(vraies_L):
            continue                       # elle serait la plus petite de L : c'est R17 (ou rien), pas R20
        out[a] = (L, q)
    return out


def tombees_sans_ligne_r21(I: Image, b: str, lignes_b: set, r: dict) -> dict:
    """R21 (23/11) : L'AFFAIRE TOMBEE SANS LIGNE. Une affaire tombee COMPLETE (un compromis ANNULE et une offre REFUSEE au
    meme montant, chacun l'unique partenaire de l'autre a ce montant sur le bien), dont les DEUX pieces sont a part, et
    qui n'a AUCUN LIEN avec les lignes du bien : l1 son montant n'est ni le Prix ni une offre prouvee d'aucune ligne ; l2
    les honoraires du compromis ne sont la Commission d'aucune ligne ; l3 l'offre est a plus de 30 jours de toute case
    « Offre Achat », le compromis (s'il est date) sur aucune case « Compromis » ; l4 aucune ligne du bien ne les tient au
    gel. Ses pieces sont MISES DE COTE (comme R7b / R7c : isolees avec leur dossier d'aujourd'hui, jamais donnees) -- elles
    ne retiennent plus aucune ligne. Jamais une de SES 20 a part. Temoin (protocole_r21_affaire_tombee_sans_ligne_
    2026-11-23.py) : sur 486 affaires tombees completes d'un bien qui a des lignes, les 26 SANS AUCUN LIEN ne sont tenues
    par AUCUNE ligne tranchee (0 / 26) ; temoin positif : 432 des 460 AVEC un lien sont tenues. Rend {piece: soeur}."""
    D = I.D
    ids = D.par_bien.get(b, [])
    cps = [q for q in ids if D.REG[q]["genre"] == "compromis" and D.REG[q]["etat"] == "cancelled" and I.nature[q] == PC.VRAIE
           and D.REG[q]["montant"] is not None]
    ofs = [q for q in ids if D.REG[q]["genre"] == "offre" and D.REG[q]["etat"] == "refused" and I.nature[q] == PC.VRAIE
           and D.REG[q]["montant"] is not None]
    out = {}
    for cp in cps:
        o_ = [o for o in ofs if abs(D.REG[o]["montant"] - D.REG[cp]["montant"]) <= 1]
        if len(o_) != 1 or len([x for x in cps if abs(D.REG[x]["montant"] - D.REG[o_[0]]["montant"]) <= 1]) != 1:
            continue
        o = o_[0]
        if cp not in r["apart"] or o not in r["apart"] or {cp, o} & les_20_a_part() or {cp, o} & set(A_PART_PAR_DECISION):
            continue
        mt = D.REG[cp]["montant"]
        lien = False
        for i in lignes_b:
            com = nombre_case(D.case(i, "Commission TTC"))
            do, dc = K.d_sheet(D.case(i, "Offre Achat")), K.d_sheet(D.case(i, "Compromis"))
            l1 = any(abs(mt - x) <= 1 for x in D.offres_de_la_ligne(i, b))
            l2 = D.REG[cp]["hon"] is not None and com is not None and abs(D.REG[cp]["hon"] - com) <= 1
            l3 = bool((do and D.REG[o]["date"] and abs((D.REG[o]["date"] - do).days) <= 30)
                      or (dc and D.REG[cp]["date"] and D.REG[cp]["date"] == dc))
            if l1 or l2 or l3:
                lien = True
        if lien or [i for q in (cp, o) for i in I.gel_par_piece.get(q, []) if i in lignes_b]:
            continue
        out[cp], out[o] = o, cp
    return out


def regle_r25(I: Image, b: str, lignes_b: set, r: dict) -> dict:
    """R25 (23/11), L'ELIMINATION PAR LES HONORAIRES : une vraie piece A PART dont le prix + honoraires ne collent a AUCUNE
    ligne, mais dont les honoraires sont la Commission TTC de PLUSIEURS lignes, va a la SEULE d'entre elles qui ne tient
    aucune vraie piece prouvee de son genre, quand TOUTES les autres tiennent deja la leur AUX MEMES honoraires. Jamais une
    de SES 20 a part ; les dates (contre_dates) ; sous la GARDE DU DEJA-RENDU (REGLES_GARDEES). Temoin
    (protocole_r19_elimination_2026-11-23.py, section R25) : rejouee sur chaque piece prouvee dont les honoraires sont la
    Commission d'au moins deux lignes -- la BONNE ligne 46 fois, une AUTRE 0, abstention 18."""
    D = I.D
    out = {}
    for a in sorted(r["apart"]):
        p = D.REG[a]
        if I.nature[a] != PC.VRAIE or a in les_20_a_part() or a in A_PART_PAR_DECISION or p["hon"] is None:
            continue
        if any(D.touche_ph(a, i) for i in lignes_b):
            continue                                   # le prix colle : c'est R19, pas elle
        cands = sorted(i for i in lignes_b if nombre_case(D.case(i, "Commission TTC")) is not None
                       and abs(p["hon"] - nombre_case(D.case(i, "Commission TTC"))) <= 1 and not D.contre_dates(a, {i}))
        if len(cands) < 2:
            continue

        def du_genre(i):
            return [q for q, ls in r["va"].items() if i in ls and q != a and I.nature[q] == PC.VRAIE
                    and D.REG[q]["genre"] == p["genre"]]
        libre = [i for i in cands if not du_genre(i)]
        if len(libre) != 1 or not all([q for q in du_genre(i) if D.REG[q]["hon"] is not None
                                       and abs(D.REG[q]["hon"] - p["hon"]) <= 1] for i in cands if i != libre[0]):
            continue
        L = libre[0]
        out[a] = (L, "REGLE R25 (23/11) : PAR ELIMINATION, SUR LES HONORAIRES -- son prix %s ne colle a aucune ligne ; ses "
                     "honoraires %d sont la Commission de %s ; %s tiennent deja leur %s a ces honoraires, %s n'en tient aucun"
                  % (p["montant"], round(p["hon"]), " ".join(cands), " ".join(i for i in cands if i != L), p["genre"], L))
    return out


def regle_r19(I: Image, b: str, lignes_b: set, r: dict) -> dict:
    """R19 (23/11), L'ELIMINATION : une vraie piece A PART dont le prix + honoraires designent PLUSIEURS lignes va a la
    SEULE d'entre elles qui ne tient AUCUNE vraie piece prouvee de son genre, quand TOUTES les autres tiennent deja une
    vraie piece de son genre AU MEME prix + honoraires (une affaire n'a qu'un compromis a ce prix). Gardes : jamais une de
    SES 20 a part (sa liste des impossibles) ; les dates (contre_dates) ; g4 de R17 -- jamais a une ligne deja tranchee (la
    piece devient sa plus petite vraie piece, et elle est possible pour plusieurs lignes). Temoin
    (protocole_r19_elimination_2026-11-23.py), rejouee sur chaque piece prouvee dont le prix + honoraires designent au
    moins deux lignes : la BONNE ligne 18 fois, une AUTRE 0, elle s'abstient 10 fois. Rend {piece: (ligne, preuve)}."""
    D = I.D
    out = {}
    for a in sorted(r["apart"]):
        p = D.REG[a]
        if I.nature[a] != PC.VRAIE or a in les_20_a_part() or a in A_PART_PAR_DECISION or p["montant"] is None \
                or p["hon"] is None:
            continue
        cands = sorted(i for i in lignes_b if D.touche_ph(a, i) and not D.contre_dates(a, {i}))
        if len(cands) < 2:
            continue

        def du_genre(i):
            return [q for q, ls in r["va"].items() if i in ls and q != a and I.nature[q] == PC.VRAIE
                    and D.REG[q]["genre"] == p["genre"]]
        libre = [i for i in cands if not du_genre(i)]
        if len(libre) != 1 or not all([q for q in du_genre(i) if D.REG[q]["montant"] == p["montant"]
                                       and D.REG[q]["hon"] == p["hon"]] for i in cands if i != libre[0]):
            continue
        L = libre[0]
        vraies_L = [x for x, l_ in r["va"].items() if L in l_ and I.nature[x] == PC.VRAIE]
        if (vraies_L and a > min(vraies_L)) or len(r["possibles"].get(a, [])) < 2:
            continue                                                       # g4 (celle de R17)
        out[a] = (L, "REGLE R19 (23/11) : PAR ELIMINATION -- son prix %d + honoraires %d designent %s ; %s tiennent deja "
                     "leur %s a ce prix + honoraires, %s n'en tient aucun" % (
                         round(p["montant"]), round(p["hon"]), " ".join(cands), " ".join(i for i in cands if i != L),
                         p["genre"], L))
    return out


def nombre_case(s) -> int | None:
    try:
        return round(float(str(s).replace(" ", "").replace(",", ".")))
    except ValueError:
        return None


# ═══════════════════════════════ R27, R28, R29 (son accord du 25/11 au soir) ═══════════════════════════════════════
#   Les champs de HEKTOR seulement : numero_mandat, honoraires_entree, les acquereurs, le journal des offres
#   (propositions_json) -- jamais nos recopies de son Sheet (vente_reglee_app, numero_facture_app : circulaires).
STOP_NOMS_R27 = {"NAN", "MME", "MR", "MLLE", "ET", "SCI", "SOCIETE", "SOCIÉTÉ", "LES", "DES", "EPOUX", "ÉPOUX", "INDIVISION"}


def noms_texte(t) -> set:
    """Les noms d'un texte (une case « Acquereur », un nom chez Hektor) -- la meme lecture que la mesure du 25/11."""
    return {x for x in re.findall(r"[A-ZÀ-Ü][A-ZÀ-Ü'\-]{2,}", str(t or "").upper()) if x not in STOP_NOMS_R27}


def noms_acquereurs_hektor(p: dict) -> set:
    out = set()
    for t in (p.get("acquereurs_json"), p.get("acquereur_json")):
        try:
            x = json.loads(t) if t else None
        except (TypeError, ValueError):
            x = None
        for y in (x if isinstance(x, list) else [x] if isinstance(x, dict) else []):
            if isinstance(y, dict):
                out |= noms_texte(y.get("nom"))
    return out


def honoraires_hektor(p: dict) -> float | None:
    try:
        return float(p.get("honoraires_entree")) if p.get("honoraires_entree") not in (None, "") else None
    except (TypeError, ValueError):
        return None


def evenements_hektor(p: dict) -> list[dict]:
    """Le journal d'une offre chez Hektor (propositions_json) : proposition, accepte, refus..."""
    try:
        pj = json.loads(p.get("propositions_json") or "[]")
    except (TypeError, ValueError):
        return []
    out = []
    for x in pj if isinstance(pj, list) else [pj]:
        for y in (x if isinstance(x, list) else [x]):
            if isinstance(y, dict):
                out.append(y)
    return out


def premiere_proposition(p: dict):
    """R29, LE FAIT D'EPOQUE : le jour de la 1re proposition de l'offre (son journal), sinon sa date -- jamais son etat."""
    for e in evenements_hektor(p):
        if e.get("type") == "proposition" and e.get("date"):
            return K.d_reg(str(e["date"]))
    return K.d_reg(str(p.get("date") or ""))


def ventes_hektor_par_mandat(I: Image) -> dict:
    """R28 et R29 : les VRAIES ventes de Hektor (jamais une copie), par numero de mandat -- tout le registre de l'image."""
    if not hasattr(I, "_ventes_par_mandat"):
        vm = defaultdict(list)
        for a, p in sorted(I.pieces.items()):
            m = str(p.get("numero_mandat") or "").strip()
            if p.get("kind") == "vente" and I.nature[a] == PC.VRAIE and m:
                vm[m].append(a)
        I._ventes_par_mandat = vm
    return I._ventes_par_mandat


def regle_r27(I: Image, gl, ids: list, r: dict) -> tuple | None:
    """R27 : (la ligne qui porte, l'autre, le critere, la preuve) quand les deux lignes du morceau sont la meme affaire --
    meme Mandat, meme Acquereur, meme Commission TTC au Sheet ; None sinon (elles restent au verrou E8, nommees)."""
    D = I.D
    if len(gl) != 2:
        return None
    x, y = sorted(gl)
    m_ = D.case(x, "Mandat").strip()
    if not m_ or m_ != D.case(y, "Mandat").strip():
        return None
    n_ = noms_texte(D.case(x, "Acquéreur"))
    if not n_ or n_ != noms_texte(D.case(y, "Acquéreur")):
        return None
    c_ = nombre_case(D.case(x, "Commission TTC"))
    if c_ is None or c_ != nombre_case(D.case(y, "Commission TTC")):
        return None
    vraies = [a for a in ids if a in D.REG and I.nature[a] == PC.VRAIE]
    ventes = [a for a in vraies if D.REG[a]["genre"] == "vente"]
    ann = {j: K.d_sheet(D.case(j, "Annulée")) for j in (x, y)}

    def rend(porteur, critere, quoi):
        autre = y if porteur == x else x
        return porteur, autre, critere, ("meme Mandat %s, meme Acquereur %s, meme Commission %s -- %s porte par le critere "
                                         "%s : %s" % (m_, " ".join(sorted(n_)), c_, porteur, critere, quoi))
    # ① la vente du dossier : la ligne qui la prouve (de l'argent est en jeu : sans preuve unique, rien n'est tranche)
    if ventes:
        pr = sorted({j for a in ventes for j in r["va"].get(a, frozenset()) if j in gl})
        if len(pr) == 1:
            return rend(pr[0], "①", "la vente %s est prouvee a elle seule (%s)" % (
                " ".join(map(str, ventes)), "; ".join(r["preuve"].get(a, "") for a in ventes)))
        return None
    # ② la date d'annulation deja posee sur le compromis du dossier
    posees = {K.d_reg(str(I.pieces[a].get("date_annulation_app") or "")) for a in vraies
              if D.REG[a]["genre"] == "compromis" and I.pieces[a].get("date_annulation_app")} - {None}
    p2 = sorted(j for j, d in ann.items() if d and d in posees)
    if len(p2) == 1:
        return rend(p2[0], "②", "son annulation du %s est deja posee sur le compromis du dossier" % ann[p2[0]])
    # ③ la date que prouve le journal de Hektor -- jamais nos refus de masse des 11-12/11/2026
    jh = {K.d_reg(str(e.get("date") or "")) for a in vraies for e in evenements_hektor(I.pieces[a])
          if e.get("type") in ("refus", "annulation") and str(e.get("date") or "")[:10] not in NOS_REFUS_DE_MASSE} - {None}
    p3 = sorted(j for j, d in ann.items() if d and d in jh)
    if len(p3) == 1:
        return rend(p3[0], "③", "son annulation du %s est prouvee par le journal de Hektor" % ann[p3[0]])
    # ④ sans argent en jeu : la plus ancienne date d'annulation -- une CONVENTION, pas une preuve
    sans_argent = all(D.case(j, "Etat Actuel").strip() == "Annulée" and ann[j] and not D.case(j, "Vente Réglée").strip()
                      for j in (x, y))
    if sans_argent and ann[x] != ann[y]:
        p4 = min((x, y), key=lambda j: ann[j])
        return rend(p4, "④", "aucune vente, deux lignes annulees : la plus ancienne annulation (%s contre %s) -- une "
                             "convention, pas une preuve ; le journal de Hektor ne departage pas" % (
                                 ann[p4], ann[y if p4 == x else x]))
    return None


def regle_r28(I: Image, b: str, r: dict) -> dict:
    """R28, DANS LE MOTIF COPIE_SEULE SEULEMENT : piece -> (ligne, preuve) pour la vente Hektor du Mandat de la ligne."""
    D, out = I.D, {}
    for gl, ids_ in r["morceaux"].items():
        if len(gl) != 1 or any(I.nature[a] == PC.VRAIE for a in ids_):
            continue                                   # hors du motif COPIE_SEULE : R28 ne joue pas
        (i,) = tuple(gl)
        m_ = D.case(i, "Mandat").strip()
        vs = ventes_hektor_par_mandat(I).get(m_, [])
        if len(vs) != 1:
            continue
        v = vs[0]
        if D.REG.get(v, {}).get("bien") != b or v not in r["apart"] or v in A_PART_PAR_DECISION or v in les_20_a_part():
            continue
        h, c_ = honoraires_hektor(I.pieces[v]), nombre_case(D.case(i, "Commission TTC"))
        if h is None or c_ is None or abs(h - c_) >= 1:
            continue
        na = noms_acquereurs_hektor(I.pieces[v]) & noms_texte(D.case(i, "Acquéreur"))
        if not na:
            continue
        vm = ventes_hektor_par_mandat(I)
        out[v] = (i, "REGLE R28 (son accord du 25/11) : la seule vente Hektor du mandat %s (%d mandats sur %d en portent "
                     "plusieurs, pas celui-la) -- honoraires Hektor %s = sa Commission TTC %s, acquereur %s ; sa ligne ne "
                     "tenait que des copies C5" % (m_, sum(1 for l_ in vm.values() if len(l_) > 1), len(vm), int(h), c_,
                                                   " ".join(sorted(na))))
    return out


def r29_candidat(I: Image, i: str, tenues: set) -> tuple | None:
    """R29 : (la vente, son bien, la preuve) pour une ligne non tranchee -- ou None. Toutes ses conditions sont requises."""
    D = I.D
    nm = noms_texte(D.case(i, "Acquéreur"))
    jo = K.d_sheet(D.case(i, "Offre Achat"))
    if not nm or not jo:
        return None
    c_ = nombre_case(D.case(i, "Commission TTC"))
    if c_ is None:
        return None
    if not hasattr(I, "_offres_r29"):
        I._offres_r29 = [(a, p) for a, p in sorted(I.pieces.items()) if p.get("kind") == "offre" and I.nature[a] == PC.VRAIE]
        I._mandats_annonce = defaultdict(set)
        for a, p in I.pieces.items():
            m_ = str(p.get("numero_mandat") or "").strip()
            if m_ and p.get("hektor_annonce_id") is not None:
                I._mandats_annonce[p["hektor_annonce_id"]].add(m_)
    trouve = {}
    for a, p in I._offres_r29:
        if not (noms_acquereurs_hektor(p) & nm) or premiere_proposition(p) != jo:
            continue
        ms = I._mandats_annonce.get(p.get("hektor_annonce_id"), set())
        vs = sorted({v for m_ in ms for v in ventes_hektor_par_mandat(I).get(m_, [])})
        if len(vs) != 1:
            continue
        v = vs[0]
        h = honoraires_hektor(I.pieces[v])
        if h is None or abs(h - c_) >= 1 or (noms_acquereurs_hektor(I.pieces[v]) & nm) or v in tenues:
            continue
        if not D.REG.get(v, {}).get("bien"):
            continue
        trouve[v] = (a, sorted(ms))
    if len(trouve) != 1:
        return None
    (v, (a, ms)), = trouve.items()
    pv = I.pieces[v]
    return v, D.REG[v]["bien"], (
        "REGLE R29 (son accord du 25/11) : son nom %s est celui de l'offre %d, PROPOSEE le %s (sa case « Offre Achat » ; "
        "l'etat de l'offre n'est pas lu) sur l'annonce %s, mandat %s -- la seule vente de ce mandat est %d (%s, honoraires "
        "Hektor %d = sa Commission TTC %d), au nom d'un AUTRE acquereur (%s), tenue par personne ; son Mandat au Sheet "
        "(%s) nommait un autre bien" % (" ".join(sorted(nm)), a, jo, I.pieces[a].get("hektor_annonce_id"), "+".join(ms), v,
                                       pv.get("date") and str(pv["date"])[:10], int(honoraires_hektor(pv)), c_,
                                       " ".join(sorted(noms_acquereurs_hektor(pv))), D.case(i, "Mandat").strip()))


def r29_remettre(I: Image) -> None:
    """Remet sur leurs anciens biens les lignes qu'un passage precedent (meme processus, meme image) a deplacees."""
    D = I.D
    for i, (anciens, tb) in list(R29_DEPLACEES.items()):
        if getattr(I, "_r29_deplacees_ici", None) is not R29_DEPLACEES:
            break                                      # une autre image : elle n'a rien deplace ici
        D.lignes_bien[tb].discard(i)
        D.rattache_par.get((tb, i), set()).discard("R29")
        for b_ in anciens:
            D.lignes_bien[b_].add(i)
        I.biens_de_ligne[i] = set(anciens)
    R29_DEPLACEES.clear()
    DONNEE_PAR_R29.clear()
    R29_ABSTENUES.clear()


def r29_apres_les_verdicts(I: Image, rangs: list, par_bien: dict, perimetre: str) -> list:
    """R29 joue APRES tous les verdicts (comme R16) : les pieces tenues sont alors connues. Pour chaque ligne prise, elle
    passe sur le bien de la vente, qui lui est donnee ; ses deux biens sont rejuges, SOUS LA GARDE DU DEJA-RENDU : une
    ligne tranchee qui bougerait (verdict, etiquette, pieces), ou la ligne qui ne serait pas tranchee avec la vente -> rien
    ne change, et la ligne est nommee dans R29_ABSTENUES."""
    D = I.D
    tenues = {a for x in rangs for a in (x.get("pieces") or [])} | set(PIECE_DONNEE_PAR_DECISION)
    par_id = {x["id_unique"]: k for k, x in enumerate(rangs)}
    decisions = set(RIEN_A_ETIQUETER_PAR_DECISION) | set(DOUBLON_PAR_DECISION) | set(LIGNE_SUR_LE_BIEN_PAR_DECISION)
    for k in range(len(rangs)):
        x = rangs[k]
        i = x["id_unique"]
        if x["verdict"] == "TRANCHEE" or i.startswith("#") or i in decisions or x.get("motif") in ("ID_EN_DOUBLE",
                                                                                                    "A_SA_DECISION") \
                or (x.get("motif") == "RIEN_A_ETIQUETER" and str(x.get("motif_texte") or "").startswith("REGLE R27")):
            continue
        c = r29_candidat(I, i, tenues)
        if not c:
            continue
        v, tb, texte = c
        anciens = set(I.biens_de_ligne.get(i, set()))
        sauve = (dict(MISES_DE_COTE), dict(GARDE_DEJA_RENDU))

        def defaire(pourquoi):
            for b_ in anciens:
                D.lignes_bien[b_].add(i)
            if tb not in anciens:
                D.lignes_bien[tb].discard(i)
                D.rattache_par.get((tb, i), set()).discard("R29")
            I.biens_de_ligne[i] = set(anciens)
            DONNEE_PAR_R29.pop(v, None)
            MISES_DE_COTE.clear()
            MISES_DE_COTE.update(sauve[0])
            GARDE_DEJA_RENDU.clear()
            GARDE_DEJA_RENDU.update(sauve[1])
            R29_ABSTENUES[i] = {"vente": v, "bien": tb, "pourquoi": pourquoi}
        for b_ in anciens:
            D.lignes_bien[b_].discard(i)
        D.lignes_bien[tb].add(i)
        D.rattache_par[(tb, i)].add("R29")
        I.biens_de_ligne[i] = {tb}
        DONNEE_PAR_R29[v] = (i, texte)
        if juger_ligne(I, i, I.sheet["par_id"][i][0]) is not None:
            defaire("la ligne ne passe pas E1/E2 sur le bien %s" % tb)
            continue
        neufs = {}
        for b_ in sorted(anciens | {tb}):
            a_j = set(par_bien.get(b_, set())) - {i}
            if b_ == tb:
                a_j.add(i)
            if a_j:
                neufs.update({o["id_unique"]: o for o in juger_bien_garde(I, b_, a_j, perimetre)})
        bouge = sorted(j for j, o in neufs.items() if j != i and j in par_id and rangs[par_id[j]]["verdict"] == "TRANCHEE"
                       and (o["verdict"], o.get("etiquette"), o.get("pieces")) != (
                           rangs[par_id[j]]["verdict"], rangs[par_id[j]].get("etiquette"), rangs[par_id[j]].get("pieces")))
        o_i = neufs.get(i)
        if bouge or not o_i or o_i["verdict"] != "TRANCHEE" or v not in (o_i.get("pieces") or []):
            defaire("GARDE DU DEJA-RENDU : %s" % ("lignes tranchees qui bougeraient %s" % bouge if bouge else
                                                   "la ligne ne serait pas tranchee avec la vente (%s)" % (
                                                       (o_i or {}).get("motif") or (o_i or {}).get("verdict"))))
            continue
        o_i["preuves"] = list(o_i.get("preuves") or []) + ["son bien %s par la REGLE R29 (son accord du 25/11) -- ecarte : "
                                                            "%s (son Mandat au Sheet)" % (tb, "+".join(sorted(anciens)) or
                                                                                         "aucun")]
        for j, o in neufs.items():
            if j in par_id:
                rangs[par_id[j]] = o
        for b_ in anciens:
            par_bien.get(b_, set()).discard(i)
        par_bien.setdefault(tb, set()).add(i)
        tenues |= set(o_i.get("pieces") or [])
        R29_DEPLACEES[i] = (set(anciens), tb)
        I._r29_deplacees_ici = R29_DEPLACEES
    return rangs


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
    # ses decisions du 24/11 portent leur raison dans la preuve (les anciennes gardent « sa decision (23/11) » : leurs
    #   verdicts rendus ne changent pas de texte)
    donnee = {a_: ((l_, _w) if _w.startswith(SON_MOT_DU_24_11) else l_)
              for a_, (l_, _w) in PIECE_DONNEE_PAR_DECISION.items()}
    a_part_dec = dict(A_PART_PAR_DECISION)
    if joue("B3B") and 14033 in a_part_dec:         # 14033 : l'option B (variante, mesure seulement)
        del a_part_dec[14033]
        donnee[14033] = ("ea6a28a7", "VARIANTE B3B (mesure) : a DONNADIEU -- prix 140 500 et commission 9 500")
    for a_, (l_, t_) in DONNEE_PAR_R29.items():      # R29 (25/11) : la vente que sa passe d'apres les verdicts donne
        if a_ in S:
            donnee[a_] = (l_, t_)
    r = K.couper_le_bien(D, b, lignes_b, S, X, a_part_dec, donnee)
    if joue("R12"):
        # VARIANTE R12 (proposee le 23/11) : le gel departage une preuve qui designe plusieurs lignes
        r12 = {}
        for a_ in sorted(r["apart"]):
            if I.nature[a_] != PC.VRAIE or a_ in les_20_a_part() or a_ in a_part_dec:
                continue
            cands = {j for j in lignes_b if D.touche_ph(a_, j)}
            gel_ = set(I.gel_par_piece.get(a_, [])) & cands
            if len(cands) > 1 and len(gel_) == 1:
                j_ = next(iter(gel_))
                # SA REGLE (b) DU 20/11 : la piece ne va a une ligne deja tranchee que si elle n'est pas plus petite que
                #   la plus petite vraie piece de son morceau -- sinon l'etiquette de cette ligne changerait
                deja_ = [q for gl_, ids_ in r["morceaux"].items() if j_ in gl_ for q in ids_ if I.nature[q] == PC.VRAIE]
                if deja_ and a_ < min(deja_):
                    continue
                r12[a_] = (next(iter(gel_)), "REGLE R12 (variante) : son prix + honoraires sont ceux de %s ; le gel du "
                                             "16/11 ne nomme que %s" % (" ".join(sorted(cands)), next(iter(gel_))))
        if r12:
            donnee.update(r12)
            r = K.couper_le_bien(D, b, lignes_b, S, X, a_part_dec, donnee)
    if joue("R9") or joue("R9b"):
        # REGLES R9 et R9b (validees le 23/11) -- voir REGLES_VALIDEES ; ⛔ R9 ne vaut que si la commission est UNIQUE AU BIEN
        r9 = regle_r9(I, b, lignes_b, r)
        if r9:
            donnee.update(r9)
            r = K.couper_le_bien(D, b, lignes_b, S, X, a_part_dec, donnee)
    if joue("R17"):
        # REGLE R17 (validee le 23/11) : la soeur de chaine -- voir REGLES_VALIDEES et regle_r17
        r17 = regle_r17(I, b, r)
        if r17:
            donnee.update(r17)
            r = K.couper_le_bien(D, b, lignes_b, S, X, a_part_dec, donnee)
    if joue("R19"):
        # REGLE R19 (validee le 23/11) : l'elimination -- voir regle_r19
        r19 = regle_r19(I, b, lignes_b, r)
        if r19:
            donnee.update(r19)
            r = K.couper_le_bien(D, b, lignes_b, S, X, a_part_dec, donnee)
    if joue("R25"):
        # R25 (23/11) : l'elimination par les honoraires, sous la garde du deja-rendu -- voir regle_r25
        r25 = regle_r25(I, b, lignes_b, r)
        if r25:
            donnee.update(r25)
            r = K.couper_le_bien(D, b, lignes_b, S, X, a_part_dec, donnee)
    if joue("R28"):
        # R28 (25/11) : un mandat, une seule vente -- DANS LE MOTIF COPIE_SEULE seulement, sous la garde du deja-rendu
        r28 = regle_r28(I, b, r)
        if r28:
            donnee.update(r28)
            r = K.couper_le_bien(D, b, lignes_b, S, X, a_part_dec, donnee)
    # VARIANTE R7a (proposee, jamais appliquee sans son mot) : la piece a part plus petite DEJA dans le dossier de toute
    #   la ligne, possible pour elle seule -- on ne coupe pas le dossier entre elles (elle reste a part, jamais donnee)
    # ⛔ SON DOUTE (24/11, § 6) : une piece EN SUSPENS reste possible pour les lignes qu'il nomme, meme si les dates la
    #   contredisent -- le verrou tient ces lignes tant qu'il n'a pas tranche (« Ne force pas »)
    for a_, (ls_, _t) in EN_SUSPENS_PAR_SON_DOUTE.items():
        if a_ in r["apart"]:
            for gl_ in r["morceaux"]:
                if gl_ & set(ls_) and gl_ not in r["possibles"][a_]:
                    r["possibles"][a_].append(gl_)
    deja = {}
    if joue("R7a"):
        for gl, ids in r["morceaux"].items():
            hk_ = [a for a in ids if I.nature[a] == PC.VRAIE]
            ch_m = {S.get(a) for a in ids}
            if hk_ and len(ch_m) == 1:
                deja[gl] = sorted(a for a in r["apart"] if I.nature[a] == PC.VRAIE and a < min(hk_)
                                  and gl in r["possibles"][a] and len(r["possibles"][a]) == 1 and S.get(a) in ch_m)
    if joue("R14"):
        # REGLE R14 (validee le 23/11) : la trace supprimee d'une saisie refaite sort du morceau, figee dans son dossier
        for gl_, ids_ in list(r["morceaux"].items()):
            vivantes = [q for q in ids_ if not supprimee_chez_hektor(I.pieces[q])]
            retirees = [q for q in ids_ if supprimee_chez_hektor(I.pieces[q]) and any(
                D.REG[v]["genre"] == D.REG[q]["genre"] and D.REG[v]["date"] and D.REG[v]["date"] == D.REG[q]["date"]
                and (D.REG[q]["montant"] is None or D.REG[v]["montant"] == D.REG[q]["montant"]) for v in vivantes)]
            if retirees:
                r["morceaux"][gl_] = [q for q in ids_ if q not in retirees]
                for q in retirees:
                    r["apart"][q] = ("REGLE R14 : la trace supprimee chez Hektor d'une saisie refaite -- sa "
                                     "jumelle vivante est dans le morceau ; figee dans son ancien dossier, avec son numero")
                    r["possibles"][q] = []
    isoles, isoles_r7c = set(), set()
    if joue("R7b"):
        for gl, ids in r["morceaux"].items():
            hk_ = [a for a in ids if I.nature[a] == PC.VRAIE]
            ch_m = {S.get(a) for a in ids}
            if hk_:
                isoles |= {a for a in r["apart"] if I.nature[a] == PC.VRAIE and a < min(hk_) and gl in r["possibles"][a]
                           and len(r["possibles"][a]) == 1 and S.get(a) not in ch_m and a not in deja.get(gl, [])}
    if joue("B3A") and 14033 in r["apart"]:          # 14033 : l'option A (variante, mesure seulement)
        isoles.add(14033)
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
    isoles_r21 = set()
    if joue("R21"):
        # R21 (23/11) : l'affaire tombee sans ligne -- voir tombees_sans_ligne_r21 ; seules les pieces qui RETIENNENT une ligne
        for a, s_ in sorted(tombees_sans_ligne_r21(I, b, lignes_b, r).items()):
            if a in isoles:
                continue
            if any(a < min([q for q in r["morceaux"].get(gl, []) if I.nature[q] == PC.VRAIE] or [0])
                   and a not in deja.get(gl, []) for gl in r["possibles"].get(a, [])):
                isoles.add(a)
                isoles_r21.add(a)
    isoles_r18 = set()
    if joue("R18"):
        # VARIANTE R18 (son message du 23/11 : « mesure la regle de mise de cote a blanc » -- MESURE SEULEMENT) : une de SES
        #   20 a part qui RETIENT une ligne au verrou (plus petite que sa plus petite vraie piece, possible pour elle, hors
        #   R7a) est mise de cote comme R7b / R7c, jamais donnee
        for a in sorted(r["apart"]):
            if I.nature[a] != PC.VRAIE or a not in les_20_a_part() or a in isoles:
                continue
            if any(a < min([q for q in r["morceaux"].get(gl, []) if I.nature[q] == PC.VRAIE] or [0])
                   and a not in deja.get(gl, []) for gl in r["possibles"].get(a, [])):
                isoles.add(a)
                isoles_r18.add(a)
    # ⭐ SA MISE DE COTE (24/11, regle 6 -- « on ne supprime pas une part, on la met de cote ») : la piece n'est donnee a
    #   personne, elle est figee avec son dossier d'aujourd'hui (tout ce qu'aucun morceau ne prend), comme R7b
    isoles_dec = set()
    for a in sorted(r["apart"]):
        if a in MISE_DE_COTE_PAR_DECISION and a not in isoles:
            isoles.add(a)
            isoles_dec.add(a)
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
                            "regle": "SA_DECISION" if a in isoles_dec else ("R21" if a in isoles_r21 else ("R18" if a in isoles_r18 else ("R7c" if a in isoles_r7c else "R7b"))),
                            "pieces_du_dossier_prises_par_un_morceau": hors,
                            "etiquettes_du_groupe": sorted({str(lab1[q]) for q in g_}),
                            "groupe": g_, "lignes_du_gel": {str(q): sorted(I.gel_par_piece.get(q, [])) for q in g_}}
    recon = reconnues_r20(I, b, r) if joue("R20") else {}
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
            elif joue("R11") and not gel_b and X and not restantes_r11(I, b, i, X, r):
                # VARIANTE R11 (proposee le 23/11) : sans gel, et TOUTES les vraies pieces du bien sont prouvees a
                #   d'autres lignes -- son affaire n'a aucune piece chez nous ; sauf si la triple preuve la trouve ailleurs
                autre = affaire_sur_un_autre_bien(I, i)
                if len(autre) == 1:
                    (bb, pr_), = autre.items()
                    out.append(attente("AFFAIRE_SUR_UN_AUTRE_BIEN", "bien %s : aucune piece pour elle ; son affaire est "
                                       "sur le bien %s -- %s" % (b, bb, pr_)))
                else:
                    ecartees = sorted(set(q for q in X if q not in r["va"] and I.nature[q] == PC.VRAIE))
                    out.append(attente("RIEN_A_ETIQUETER", "REGLE R11 (variante) : bien %s -- sans gel, et ses %d piece(s) "
                                       "sont toutes prouvees a d'autres lignes : son affaire n'a aucune piece chez nous%s"
                                       % (b, len(X), (" ; hors d'elle : %s" % ", ".join(
                                           "%d (%s)" % (q, restantes_r11(I, b, i, X, r, pourquoi=q)) for q in ecartees))
                                          if ecartees else "")))
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
        invisibles = [a for a in ids if invisible_a_la_nuit(I, a)]
        if invisibles and len({S.get(a) for a in ids}) > 1:
            out.append(attente("PIECE_SANS_DATE_INVISIBLE", "sans date, exclues de la regle E (sa decision) : %s -- %s ; "
                               "ses pieces sont dans %d dossiers (%s) : le fichier des coupes dirait le morceau "
                               "« introuvable » chaque nuit" % (
                                   invisibles, " ; ".join(exclues_de_la_regle_e()[a][:90] for a in invisibles),
                                   len({S.get(a) for a in ids}), sorted({S.get(a) for a in ids}))))
            continue
        exc = exception_nommee(gl) if len(gl) > 1 else None
        jum = jumelle_annulee(I, gl, ids) if (len(gl) == 2 and not exc and joue("R13")) else None   # REGLE R13 (validee 23/11)
        if jum and i == jum[1]:
            out.append(attente("RIEN_A_ETIQUETER", "REGLE R13 : la jumelle annulee de %s -- meme Prix, meme date d'offre, "
                                                   "sans gel sur ce dossier : la meme affaire ecrite deux fois" % jum[0]))
            continue
        # R27 (25/11) : la meme affaire sur deux lignes -- jamais une paire de R13 ; elle remplace l'exception nommee
        r27 = regle_r27(I, gl, ids, r) if (len(gl) == 2 and not jum and joue("R27")) else None
        if r27:
            porteur, autre, critere, quoi = r27
            if i != porteur:
                out.append(attente("RIEN_A_ETIQUETER", "REGLE R27 (son accord du 25/11) : la meme affaire que %s (%s) -- "
                                                       "celle-ci n'a rien a etiqueter (%s)%s" % (
                                                           porteur, quoi, "doublon" if K.d_sheet(D.case(i, "Offre Achat"))
                                                           == K.d_sheet(D.case(porteur, "Offre Achat"))
                                                           else "une autre tentative du meme acquereur",
                                                           " ; elle remplace l'exception nommee %s" % exc if exc else "")))
                continue
            exc = None
        if len(gl) > 1 and not exc and not r27 and not (jum and i == jum[0]):
            pourquoi_ = pas_jumelle_pourquoi(I, gl) if len(gl) == 2 else ""
            out.append(attente("DEUX_LIGNES_UN_DOSSIER", "avec %s ; morceau %s%s" % ("+".join(sorted(gl - {i})), ids,
                                                                                    pourquoi_)))
            continue
        m = min(hk)
        bloque = [] if "R4" in VARIANTES_ACTIVES else \
            sorted(a for a in r["apart"] if I.nature[a] == PC.VRAIE and a < m and gl in r["possibles"][a]
                   and a not in deja.get(gl, []) and a not in isoles
                   and not (a in recon and recon[a][0] not in gl))
        if bloque:
            out.append(attente("VERROU_PIECE_PLUS_PETITE", "plus petite de la ligne %d ; a part et plus petites : %s"
                               % (m, "; ".join("%d (%s)" % (a, r["apart"][a]) for a in bloque))))
            continue
        neutres = sorted(a for a in r["apart"] if gl in r["possibles"][a] and a not in deja.get(gl, [])
                         and a not in isoles and not (a in recon and recon[a][0] not in gl and a < m))
        reconnues_ici = sorted(a for a in recon if recon[a][0] not in gl and a < m and gl in r["possibles"].get(a, []))
        preuves = [preuve_nommee(I, a, gl, r["preuve"].get(a, "")) for a in ids]
        if neutres:
            preuves.append("a part sans effet sur l'etiquette (son critere 2) : %s" % " ".join(map(str, neutres)))
        if reconnues_ici:
            preuves.append("a part plus petite mais RECONNUE a une autre affaire par sa soeur de chaine (REGLE R20) : %s"
                           % "; ".join("%d est a %s (sa soeur %d y est prouvee ; jamais donnee)" % (a, recon[a][0], recon[a][1])
                                       for a in reconnues_ici))
        mis_de_cote = sorted(a for a in isoles if a < m and gl in r["possibles"][a])
        if mis_de_cote:
            if any(a in isoles_r7c for a in mis_de_cote):
                preuves.append("a part TRANCHEE PAR LA REGLE R7c (validee le 23/11) -- aucune preuve ne peut la donner a "
                               "aucune de ses lignes possibles, hors de leurs dossiers : %s" % " ".join(
                                   "%d" % a for a in mis_de_cote if a in isoles_r7c))
            m7 = [a for a in mis_de_cote if a not in isoles_r18 and a not in isoles_r21 and a not in isoles_dec]
            m_dec = [a for a in mis_de_cote if a in isoles_dec]
            if m_dec:
                preuves.append("a part MISE DE COTE PAR LA DECISION DU 24/11 (regle 6 : donnee a personne, figee avec son "
                               "dossier d'aujourd'hui) ; son ancien numero dans la pose simulee : %s" % ", ".join(
                                   "%d %s %s (dossier fige : %s)" % (
                                       a, "GARDE" if lab1[a] == I.pieces[a]["app_dossier_uuid"] else "⛔ PERD (numero NEUF)",
                                       I.pieces[a]["app_dossier_numero"] or "aucun",
                                       " ".join(map(str, groupe_isole[S[a]])))
                                   for a in m_dec))
            m21 = [a for a in mis_de_cote if a in isoles_r21]
            if m21:
                preuves.append("a part MISE DE COTE PAR LA REGLE R21 : une affaire tombee complete (compromis annule + offre "
                               "refusee au meme montant) SANS AUCUN LIEN avec les lignes du bien -- jamais donnee ; son ancien "
                               "numero dans la pose simulee : %s" % ", ".join(
                                   "%d %s %s (dossier fige : %s)" % (
                                       a, "GARDE" if lab1[a] == I.pieces[a]["app_dossier_uuid"] else "⛔ PERD (numero NEUF)",
                                       I.pieces[a]["app_dossier_numero"] or "aucun", " ".join(map(str, groupe_isole[S[a]])))
                                   for a in m21))
            if m7:
                preuves.append("a part MISE DE COTE avec son dossier d'aujourd'hui, possible pour elle seule, hors de son "
                               "dossier (REGLE R7b, validee le 22/11 ; elle garde son ancien numero : %s) : %s" % (", ".join(
                                   "%d -> %s (dossier fige : %s)" % (a, I.pieces[a]["app_dossier_numero"] or "aucun",
                                                                      " ".join(map(str, groupe_isole[S[a]])))
                                   for a in m7), " ".join("%d" % a for a in m7)))
            m18 = [a for a in mis_de_cote if a in isoles_r18]
            if m18:
                preuves.append("a part MISE DE COTE PAR LA VARIANTE R18 (mesure seulement) -- une de SES 20 a part (sa "
                               "decision du 21/11), jamais donnee ; son ancien numero dans la pose simulee : %s" % ", ".join(
                                   "%d %s %s (dossier fige : %s)" % (
                                       a, "GARDE" if lab1[a] == I.pieces[a]["app_dossier_uuid"] else "⛔ PERD (numero NEUF)",
                                       I.pieces[a]["app_dossier_numero"] or "aucun",
                                       " ".join(map(str, groupe_isole[S[a]])))
                                   for a in m18))
        if deja.get(gl):
            preuves.append("a part deja dans son dossier, possible pour elle seule (REGLE R7a, validee le 22/11) : %s" % " ".join(
                "%d" % a for a in deja[gl]))
        if exc:
            preuves.append("exception nommee : %s -- %s" % (exc, "+".join(sorted(gl))))
        if r27:
            preuves.append("REGLE R27 (son accord du 25/11) : la meme affaire que %s, qui n'a rien a etiqueter -- %s"
                           % (r27[1], r27[3]))
        if len(I.biens_de_ligne.get(i, set())) > 1:
            autre = sorted(I.biens_de_ligne[i] - {b})
            preuves.append("son bien %s par la regle P1 (gel + mandat) ; ecarte : %s (product_ref seul) -- %s"
                           % (b, "+".join(autre), REGLES_VALIDEES["P1"][1]))
        out.append(dict(base, verdict="TRANCHEE", etiquette=lab1[m], pieces=ids, preuves=preuves, epreuve="E9"))
    return out


def juger_bien_garde(I: Image, b: str, a_juger: set, perimetre: str) -> list[dict]:
    """juger_bien, sous LA GARDE DU DEJA-RENDU : si une regle de REGLES_GARDEES joue, le bien est juge AVEC et SANS elles ;
    une ligne tranchee SANS qui change AVEC (etiquette ou pieces) -> le bien est juge SANS, et nomme dans GARDE_DEJA_RENDU."""
    gardees = {x for x in REGLES_GARDEES if joue(x)}
    if not gardees:
        return juger_bien(I, b, a_juger, perimetre)
    avant = dict(MISES_DE_COTE)
    SUSPENDUES.update(gardees)
    try:
        sans = juger_bien(I, b, a_juger, perimetre)
    finally:
        SUSPENDUES.difference_update(gardees)
    m_sans = dict(MISES_DE_COTE)
    MISES_DE_COTE.clear()
    MISES_DE_COTE.update(avant)
    avec = juger_bien(I, b, a_juger, perimetre)
    s_ = {o["id_unique"]: o for o in sans}
    a_ = {o["id_unique"]: o for o in avec}
    bouge = sorted(i for i, o in s_.items() if o["verdict"] == "TRANCHEE"
                   and (a_[i]["verdict"], a_[i].get("etiquette"), a_[i].get("pieces"))
                   != (o["verdict"], o.get("etiquette"), o.get("pieces")))
    if bouge:
        GARDE_DEJA_RENDU[b] = {"regles": sorted(gardees), "lignes_rendues_qui_bougeraient": bouge,
                               "lignes_que_la_regle_aurait_tranchees": sorted(i for i, o in a_.items()
                                                                              if o["verdict"] == "TRANCHEE"
                                                                              and s_[i]["verdict"] != "TRANCHEE")}
        MISES_DE_COTE.clear()
        MISES_DE_COTE.update(m_sans)
        return sans
    return avec


def etape_passage(I: Image, note: str, perimetre: str = "bien", variantes: set | None = None) -> int:
    VARIANTES_ACTIVES.clear()
    VARIANTES_ACTIVES.update(variantes or ())
    MISES_DE_COTE.clear()
    GARDE_DEJA_RENDU.clear()
    # R29 : un passage precedent sur la MEME image a deplace des lignes -- on les remet, et la 1re passe juge sans R29
    r29_remettre(I)
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
    # ⭐ 25/11 : le passage garde l'empreinte de SES ENTREES VIVANTES (a cote du socle, sans toucher son schema)
    ent = {"passage": pid, "image": I.d.name, "code": md5_code(), "entrees": entrees_vivantes(),
           "empreinte_du_juge": empreinte_du_juge(), "fait_le": debut}
    (DOSSIER / ("entrees_passage_%d.json" % pid)).write_text(json.dumps(ent, ensure_ascii=False, indent=1),
                                                              encoding="utf-8")
    dire("   le juge : code %s ; entrees vivantes %s ; EMPREINTE DU JUGE %s" % (
        ent["code"][:8], {k.split(" (")[0]: v[:8] for k, v in ent["entrees"].items()}, ent["empreinte_du_juge"][:8]))
    rangs, par_bien = [], defaultdict(set)
    for i, vs in sorted(I.sheet["par_id"].items()):
        r = juger_ligne(I, i, vs[0])
        if r is None:
            par_bien[r_bien(I, i)].add(i)
        else:
            rangs.append(r)
    for b in sorted(par_bien, key=lambda x: int(x) if x.isdigit() else 0):
        rangs.extend(juger_bien_garde(I, b, par_bien[b], perimetre))
    for x in I.sheet["sans_id"]:
        rangs.append({"id_unique": "#%d" % x["num"], "num": x["num"], "biens": [], "verdict": "ATTENTE",
                      "motif": "SANS_ID_UNIQUE", "motif_texte": MOTIFS["SANS_ID_UNIQUE"][1], "epreuve": "E1"})
    # R29 : ⛔ RETIREE LE 26/11 (son mot, voir REGLES_RETIREES) -- joue("R29") rend toujours faux ; le bloc reste pour
    #   l'histoire du code, il ne s'execute plus
    if joue("R29"):
        rangs = r29_apres_les_verdicts(I, rangs, par_bien, perimetre)
        if DONNEE_PAR_R29 or R29_ABSTENUES:
            dire("   R29 : %d ligne(s) suivent la vente de leur commission : %s ; abstenues par sa garde : %s" % (
                len(DONNEE_PAR_R29), " . ".join("%s <- %d" % (l_, v_) for v_, (l_, _t) in sorted(DONNEE_PAR_R29.items()))
                or "aucune", " . ".join("%s (%s)" % (i_, x_["pourquoi"]) for i_, x_ in sorted(R29_ABSTENUES.items()))
                or "aucune"))
    # R16 (validee le 23/11) : APRES tous les verdicts -- les pieces tenues sont alors connues ; elle ne touche que SANS_BIEN
    if joue("R16"):
        tenues = {a for r in rangs for a in (r.get("pieces") or [])} | set(PIECE_DONNEE_PAR_DECISION)
        for r in rangs:
            if r.get("motif") == "SANS_BIEN":
                t16 = rien_par_r16(I, r["id_unique"], tenues)
                if t16:
                    r.update(motif="RIEN_A_ETIQUETER", motif_texte=t16, epreuve=MOTIFS["RIEN_A_ETIQUETER"][0])
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
    if GARDE_DEJA_RENDU:
        dire("   GARDE DU DEJA-RENDU : %d bien(s) juge(s) SANS %s, parce qu'une ligne tranchee y bougerait : %s" % (
            len(GARDE_DEJA_RENDU), "+".join(sorted({r_ for x in GARDE_DEJA_RENDU.values() for r_ in x["regles"]})),
            " . ".join("%s (rendues : %s ; aurait tranche : %s)" % (b_, "+".join(x["lignes_rendues_qui_bougeraient"]),
                                                                 "+".join(x["lignes_que_la_regle_aurait_tranchees"]) or "-")
                       for b_, x in sorted(GARDE_DEJA_RENDU.items()))))
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

    def juger_pieces(famille: str, lignes: list, pieces: list, vraies_seules: bool = False, nommee: str | None = None):
        """vraies_seules : ses coupes du 20/11 ne portaient QUE les pieces Hektor (une copie ne decide pas) -- on ne
        compare alors que les vraies pieces du verdict. nommee : la decision qui a remplace l'attendu (ecrite avec lui)."""
        for i in lignes:
            v = V.get(i)
            att = " ".join(map(str, pieces)) + (" (%s)" % nommee if nommee else "")
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
            if x["ligne"] in V3_ATTENDU_PAR_SA_DECISION:       # son mot du 26/11 : trois attentes perimees, par SA decision
                d_ = V3_ATTENDU_PAR_SA_DECISION[x["ligne"]]
                juger_pieces("v3", [x["ligne"]], d_["pieces"], nommee=d_["decision"])
            else:
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
    pieces_redecidees = {q for d_ in SES_DECISIONS.values() for ps in d_["lignes"].values() for q in ps}
    for x in T["familles"]["a_part_20"]:
        if x["piece"] in pieces_redecidees:       # sa decision posterieure remplace l'attendu (14033, 23/11)
            continue
        jugees = [i for i in I.D.lignes_bien.get(x["bien"], set()) if V.get(i, ("",))[0] == "TRANCHEE"]
        if not jugees and not tenues.get(x["piece"]):
            noter("a_part_20", "", "%d a personne" % x["piece"], "ATTEND (aucune ligne du bien tranchee)", None)
        else:
            noter("a_part_20", "", "%d a personne" % x["piece"], " ".join(tenues.get(x["piece"], [])) or "a personne",
                  int(bool(tenues.get(x["piece"]))))
    # les jumelles : leurs deux lignes, ensemble -- tranchees sur les MEMES pieces, ou en attente toutes les deux
    for j in T["familles"]["jumelles"]:
        if set(j["lignes"]) <= remplacees:     # DEBARD : sa decision du 24/11 en fait DEUX affaires (SES_DECISIONS)
            continue
        vs = [V.get(i) for i in j["lignes"]]
        if j.get("nom") in SON_ACCORD_R27 and joue("R27") and not any(v is None for v in vs):
            # SON ACCORD DU 25/11 (R27) remplace la convention des jumelles : une seule porte, l'autre n'a rien a etiqueter
            p_ = SON_ACCORD_R27[j["nom"]]
            o_ = next(i for i in j["lignes"] if i != p_)
            ok_ = V[p_][0] == "TRANCHEE" and V[o_][2] == "RIEN_A_ETIQUETER"
            noter("jumelles", "+".join(j["lignes"]), "R27 : %s porte, %s rien a etiqueter" % (p_, o_),
                  "%s %s / %s %s" % (p_, V[p_][2] or V[p_][0], o_, V[o_][2] or V[o_][0]), int(not ok_))
            continue
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
        if b["bien"] not in BIENS_A_SA_DECISION:
            continue                     # 39845 : tranche par lui le 23/11 au soir -- SES_DECISIONS le remplace
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
