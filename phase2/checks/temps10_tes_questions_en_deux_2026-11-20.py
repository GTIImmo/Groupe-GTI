"""Chantier classeur, ⑯ -- TES 23 QUESTIONS EN DEUX (A : j'ai une lecture ; B : hors de portee), et la CORRECTION de
mon classeur des groupes (le defaut trouve en les relisant).

LECTURE SEULE. Rien dans le Sheet, rien chez Hektor, rien en base : le gel est lu en direct par le pooler dans une
transaction READ ONLY ; le registre local est ouvert en lecture seule.

Sa demande (20/11, soir) : « partage mes 23 questions EN DEUX. A : celles ou tu as deja une lecture -- ta lecture, SUR
QUOI elle repose, a quel point tu y crois. B : celles qui sont hors de portee. NE FORCE RIEN. » Et : « 4 sont deja
ecrivables -- liens surs, un seul dossier, personne d'autre dedans. Verifie-le. »

CE QUE LE SCRIPT FAIT
  . il recalcule, pour chaque ligne des 23 et ses soeurs, sa case AUJOURD'HUI et sa case SI ON RETIRAIT SA QUESTION,
    sur le gel vivant, avec les chaines de l'etat 5 puis celles de ce soir avec G2 + l'outil (le classement est celui
    de temps6/temps8, recopie) ;
  . il verifie ses « 4 » : les lignes des 23 a liens surs, un seul dossier, personne d'autre, aucun audit contre ;
  . il ecrit le partage (lectures et preuves : les donnees ci-dessous, relues piece par piece au registre) ;
  . TEMOINS : les 23 lignes sont EXACTEMENT les « A TOI » de la section 3 du classeur des groupes ; chaque transaction
    citee comme preuve existe au registre avec le montant ecrit.

Usage :  python -u phase2/checks/temps10_tes_questions_en_deux_2026-11-20.py
Sortie : notice/TEMPS10_TES_23_QUESTIONS_EN_DEUX_2026-11-20.md, .csv et .xlsx ; code 0 si les temoins sont verts.
"""
from __future__ import annotations

import csv
import json
import os
import sqlite3
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase2.sync import push_upgrade_to_supabase as PU  # noqa: E402
from xlsx_simple import ecrire_xlsx  # noqa: E402

CACHE = Path(r"C:\Hektor\chantier_classeur_q6_cache")
GROUPES = RACINE / "notice" / "TEMPS9_LE_CLASSEUR_DES_GROUPES_2026-11-20.csv"
VERDICTS_18 = RACINE / "notice" / "AUDIT_INDEPENDANT_CLASSEUR_VERDICTS_2026-11-18.csv"
OPERATIONS_V2 = RACINE / "notice" / "AUDIT_INDEPENDANT_V2_OPERATIONS_AFFINEES_2026-11-19.csv"
SORTIE_MD = RACINE / "notice" / "TEMPS10_TES_23_QUESTIONS_EN_DEUX_2026-11-20.md"
SORTIE_CSV = RACINE / "notice" / "TEMPS10_TES_23_QUESTIONS_EN_DEUX_2026-11-20.csv"
SORTIE_XLSX = RACINE / "notice" / "TEMPS10_TES_23_QUESTIONS_EN_DEUX_2026-11-20.xlsx"
SURE = "sûre"

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# LE PARTAGE. « etiquette » dit si TA REPONSE change l'etiquette ecrite en colonne A (regle de la pose, lue en
# production le 20/11 : a la fusion comme a la scission, le groupe qui garde la PLUS PETITE transaction garde
# l'etiquette). « preuves » : (transaction, montant attendu au registre) -- verifiees par le temoin 2.
# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
QUESTIONS = [
    dict(n="A1", classe="A", lignes=["1D7EIYKW"], qui="GANDON-BERAUD",
         question="Un compromis le 17/02/2021, apres l'annulation du 20/11/2020 : une seconde tentative ?",
         lecture="Une seule affaire, pas de seconde tentative : le compromis 27512 n'a jamais ete signe.",
         repose="27512 vaut 51 000 dont 4 000 d'honoraires = l'offre et la commission de ta ligne ; la maison etait "
                "deja sous offre GOUTEY le 26/01/2021 (nouveau mandat) et sous compromis le 23/02 ; ta colonne « en "
                "attente » dit un refus de pret avant tout compromis ; le 20/11/2020 est une date de lot (12 lignes).",
         confiance="forte",
         etiquette="Depend de ta reponse ; avec ma lecture, rien a couper : la ligne prend le dossier 27512 + 27513.",
         preuves=[(27512, 51000), (27513, 51000)]),
    dict(n="A2", classe="A", lignes=["87QOXR64"], qui="RIGAUD",
         question="Annulee le 22/01/2022 mais un compromis le 11/02/2022 : l'annulation est-elle du 22/02 ?",
         lecture="L'annulation du 22/01 est la bonne ; le 11/02 est une date de compromis PREVUE, jamais signee.",
         repose="Ta case « Signe » est a FALSE sur cette ligne ; LECOMPTE a fait son offre le 10/02/2022 ; meme cas "
                "deja vu sur BARDY (annulee le 21/04/2021, compromis prevu le 30/04, annule chez Hektor).",
         confiance="forte",
         etiquette="Ne depend PAS de ta reponse : seule une date en depend.",
         preuves=[(17427, 184000), (17429, 184000)]),
    dict(n="A3", classe="A", lignes=["E9GL6MUS", "H6CTRVR6"], qui="SOUBEYRAND / MERCIER",
         question="Valerie FIGARI (offre 11414 du 06/04/2021, 295 000) est-elle la co-acquereuse de SOUBEYRAND ?",
         lecture="L'offre 11414 est celle de l'affaire SOUBEYRAND ; FIGARI est rangee « partenaire » chez Hektor, donc "
                 "sans doute l'intermediaire. Co-acquereuse ou non, cela ne change rien.",
         repose="Meme jour que ton classeur (06/04/2021), meme prix (295 000), seule offre ce jour-la ; le compromis "
                "11412 tombe au jour pres sur ta ligne (19/05/2021, 15 000 d'honoraires = ta commission).",
         confiance="forte",
         etiquette="Ne depend PAS de ta reponse, pour aucune des deux lignes (H6CTRVR6 n'a pas de question a elle : "
                   "elle attendait celle-ci).",
         preuves=[(11414, 295000), (11412, 295000), (11415, 295000)]),
    dict(n="A4", classe="A", lignes=["V3FO5NDA"], qui="BAUDOIN-PETIPAS",
         question="Le compromis du 08/12/2023 et la vente du 04/06/2024 manquent-ils au Sheet ?",
         lecture="Non : c'est la vente de POCHELON, ta ligne 6FQO29C8. V3FO5NDA garde son offre seule.",
         repose="6FQO29C8 porte le compromis du 08/12/2023 et la vente du 04/06/2024 au jour pres, 80 000 et 6 000 "
                "d'honoraires ; l'offre BAUDOIN etait a 87 000 avec 7 000 ; le nom BAUDOIN sur le compromis est le "
                "reste habituel de Hektor (le nom du premier acheteur recopie).",
         confiance="forte",
         etiquette="Depend de ta reponse : une coupe ; le compromis 19131 (le plus ancien) part chez POCHELON avec son "
                   "etiquette, BAUDOIN recoit une etiquette neuve sur son offre sure.",
         preuves=[(19131, 80000), (19132, 87000), (19133, 80000)]),
    dict(n="A5", classe="A", lignes=["5QE9107L", "ZW7MKTWH"], qui="DEBARD (deux affaires)",
         question="Le compromis sans date 20088 (50 000) suit-il la 1re offre (55 000, fevrier 2021) ou la 2e (50 000, "
                  "juillet 2021) ?",
         lecture="La 2e : la renegociation a 50 000 apres le CU negatif.",
         repose="Son montant (50 000) = l'offre de juillet ; dans ce lot, chaque compromis porte le prix de l'offre de "
                "son acheteur. CONTRE : ses honoraires (5 000) ne collent a aucune des deux lignes (4 700 et 0).",
         confiance="moyenne",
         etiquette="Depend de ta reponse (20088 est la plus petite transaction : qui l'a garde l'etiquette). "
                   "PROPOSITION : mettre 20088 A PART ; les deux lignes s'ecrivent alors sur leur offre sure, sans "
                   "dependre de ma lecture.",
         preuves=[(20088, 50000), (20089, 50000), (20090, 55000)]),
    dict(n="A6", classe="A", lignes=["RGCEC677"], qui="MEJEAN-MARIAGE / FAU-PIETTE",
         question="Le compromis sans date 4542 (108 000) : MEJEAN (110 000, mars 2021) ou FAU-PIETTE (108 000, "
                  "septembre 2021) ?",
         lecture="FAU-PIETTE.",
         repose="108 000 dont 100 000 net = exactement l'offre FAU-PIETTE (4544) ; dans ce lot chaque compromis "
                "verifiable porte le prix de l'offre de son acheteur. CONTRE : les honoraires (8 000) sont ceux des deux "
                "lignes ; une renegociation MEJEAN apres le « PB de parcelle » ne se verrait pas (journal migre).",
         confiance="moyenne",
         etiquette="Depend de ta reponse. PROPOSITION : 4542 A PART ; RGCEC677 et 40ELE6SQ s'ecrivent sur leur offre "
                   "sure. (Regle aussi la coupe 23 de ton classeur.)",
         preuves=[(4542, 108000), (4544, 108000), (4545, 110000)]),
    dict(n="A7", classe="A", lignes=["2dfa6ef3", "5a956cad", "d1cb8dd7"], qui="IMAW / BLACHON / MADER",
         question="UNE seule question de doctrine pour les trois : apres une renegociation, le role « offre » tient-il "
                  "l'offre d'origine (la date de ton classeur) ou l'offre acceptee (son prix) ?",
         lecture="L'offre ACCEPTEE, celle qui a mene au compromis ; l'offre d'origine reste dans le meme dossier, avec "
                 "sa date.",
         repose="Une convention, pas une mesure : les deux offres de chaque affaire sont dans le meme dossier (MADER : "
                "28832 s'y rattache, et la fusion garde l'etiquette de 28831, la plus ancienne).",
         confiance="convention",
         etiquette="Ne depend PAS de ta reponse, pour les trois.",
         preuves=[(30656, 230000), (30692, 220000), (30684, 89000), (30776, 82218), (28832, 129000), (28833, 129000)]),
    dict(n="A8", classe="A", lignes=["3308P0UX", "9WQ204HP", "O6R10ZQA", "T2GZOY5O"], qui="VIALLARD (+ MARCOS) et PAOLONE",
         question="Deux saisies de la meme affaire (VIALLARD : 3308P0UX et YRUF0S9H ; PAOLONE : O6R10ZQA et T2GZOY5O) : "
                  "laquelle garde les pieces ?",
         lecture="Celle que le gel tient deja : 3308P0UX ; pour PAOLONE, O6R10ZQA (elle porte la note du notaire). "
                 "L'autre reste sans etiquette.",
         repose="Aucune donnee ne dit laquelle est la bonne saisie -- mais l'etiquette est JUSTE sur l'une comme sur "
                "l'autre : c'est la meme affaire. MARCOS (9WQ204HP) n'a pas de question a lui : son compromis 4480 lui "
                "revient quel que soit le choix (87 000 et 6 000 = son offre et sa commission).",
         confiance="convention",
         etiquette="Ne depend PAS de ta reponse (seule la ligne qui la recoit en depend). Les dates d'annulation, "
                   "elles, sont en B.",
         preuves=[(4483, 88160), (4480, 87000), (4484, 87000), (20075, 34000), (20073, 34000)]),
    dict(n="A9", classe="A", lignes=["QJQ9M4OF"], qui="AFFONSO (soeur ROBERT)",
         question="Pas de question a elle : elle attend celle de sa soeur D9MMB7OU (« ROBERT et AFFONSO, meme menage ? »).",
         lecture="Rien a trancher pour elle : le compromis 17365 (le plus ancien) reste chez elle quoi que tu repondes "
                 "pour sa soeur.",
         repose="L'offre 17366 du 25/08/2022 tombe au jour pres sur la ligne ROBERT ; le compromis et la vente tombent "
                "au jour pres sur celle-ci, 200 000 net + 13 000 = son prix et sa commission.",
         confiance="forte",
         etiquette="Ne depend PAS de la reponse.",
         preuves=[(17365, 213000), (17366, 213000), (17367, 213000)]),
    # ── B « attend » : hors de portee, et la ligne ATTEND ta reponse ──
    dict(n="B1", classe="B-attend", lignes=["SHN6RKDI"], qui="MOSNIER",
         question="Le compromis 26613 (210 000, net vendeur 0, jamais date) a-t-il ete prepare pour les MOSNIER ?",
         lecture="Je ne sais pas.",
         repose="Son prix n'est celui d'aucune ligne (213 000 partout), son net vendeur est a 0 (un brouillon), les noms "
                "sur les trois compromis du bien sont ceux de l'acheteur final. MOSNIER est la seule affaire sans "
                "compromis -- mais un brouillon en double de l'acheteur final est tout aussi possible.",
         confiance="aucune",
         etiquette="Toute l'etiquette en depend (la ligne n'a chez nous que cette piece et une copie C5). 26613 est "
                   "DEJA A PART (exclu de E le 19/11) : sans reponse, la ligne reste sans etiquette et rien d'autre ne "
                   "bouge.",
         preuves=[(26613, 210000)]),
    dict(n="B2", classe="B-attend", lignes=["d2108609"], qui="CHOUVELLON",
         question="Le compromis 21520 (282 000, jamais date) est-il celui prepare pour le RDV du 26/08/2025, ou un "
                  "brouillon de MARTIN ?",
         lecture="Je ne sais pas.",
         repose="Prix (282 000) et honoraires (12 000) identiques pour CHOUVELLON et pour MARTIN ; le nom MARTIN ne "
                "prouve rien (Hektor recopie les noms) ; l'offre CHOUVELLON n'existe chez nous que comme copie C5.",
         confiance="aucune",
         etiquette="Toute l'etiquette en depend. 21520 est DEJA A PART (exclu de E le 19/11) : sans reponse, rien "
                   "d'ecrit, rien d'autre ne bouge.",
         preuves=[(21520, 282000), (21521, 282000)]),
    dict(n="B3", classe="B-attend", lignes=["ea6a28a7"], qui="DONNADIEU-KOSINSKI",
         question="Le compromis 14033 (140 500, jamais date, aux noms COLAS) est-il la trace de l'affaire DONNADIEU ?",
         lecture="Je ne sais pas.",
         repose="POUR : 140 500 et 9 500 sont exactement le prix et la commission de DONNADIEU. CONTRE : ce sont aussi "
                "le prix et les honoraires de l'annonce (DONNADIEU a offert « au prix ») ; les noms sont COLAS ; "
                "l'affaire a dure 6 jours et son offre n'est meme pas chez Hektor.",
         confiance="aucune",
         etiquette="Depend de ta reponse, et bloque AUSSI la vente COLAS (205f62be) : 14033 est la plus petite "
                   "transaction de son dossier. PROPOSITION : 14033 A PART -- COLAS s'ecrit tout de suite, DONNADIEU "
                   "attend ta reponse.",
         preuves=[(14033, 140500), (14034, 130000)]),
    # ── B « libre » : hors de portee, MAIS l'ecriture n'en depend pas ──
    dict(n="B4", classe="B-libre", lignes=["TA5QUCD4"], qui="DUPARANT-BACHELET",
         question="L'offre du 19/07/2018 (Sheet) ou du 11/12/2018 (Hektor) ?",
         lecture="Je ne sais pas (ta ligne porte aussi un prix « 167 » : une saisie rapide).",
         repose="Une seule affaire sur le bien : offre, compromis et vente dans le meme dossier.",
         confiance="aucune",
         etiquette="Ne depend PAS de ta reponse : la ligne s'ecrit, la question reste pour plus tard.",
         preuves=[(28362, 110000), (28363, 110000), (28364, 110000)]),
    dict(n="B5", classe="B-libre", lignes=["Y9A2L3X4"], qui="GERPHAGNON-JOINAUX",
         question="Le compromis signe le 20/06/2019 (Sheet) ou le 17/07/2019 (Hektor) ?",
         lecture="Je ne sais pas.",
         repose="Une seule affaire sur le bien.",
         confiance="aucune",
         etiquette="Ne depend PAS de ta reponse.",
         preuves=[(11996, 60000), (11997, 60000), (11998, 60000)]),
    dict(n="B6", classe="B-libre", lignes=["HUY49KEC"], qui="CANIVET",
         question="Le compromis du 16/11/2018 a-t-il existe (toutes tes dates sont au 16/11) ? Faut-il le creer ?",
         lecture="Je ne sais pas ; rien ne l'exige pour la colonne A.",
         repose="La seule affaire du lot : vente 3741 a 54 500 = 49 500 + 5 000 de commission, 3 jours avant ta "
                "« Vente reglee ».",
         confiance="aucune",
         etiquette="Ne depend PAS de ta reponse : un compromis cree rejoindrait le meme dossier sans en changer "
                   "l'etiquette.",
         preuves=[(3741, 54500)]),
    dict(n="B7", classe="B-libre", lignes=["c0a73edd"], qui="SCI LA FELOLIE",
         question="Le dossier Hektor 28614-28616 (une autre annonce) est-il un doublon de cette vente, ou un second lot ?",
         lecture="Je ne sais pas.",
         repose="Ta ligne colle au jour pres et au centime au dossier 28611-28613 (55 000 dont 5 000 a la charge de "
                "l'acquereur) ; l'autre dossier est sur une autre annonce, a 50 000, charge vendeur.",
         confiance="aucune",
         etiquette="Ne depend PAS de ta reponse.",
         preuves=[(28611, 55000), (28614, 50000)]),
]

# Les trois « A TOI » de la section 1 que tu m'as cites (DUPONT-PIPPIA, DUVET), et dont MA LECTURE ETAIT FAUSSE.
SECTION1 = [
    dict(n="C1", groupe="7 (coupe 16382)", lignes=["R0JRVFDC", "RX6J289Y", "JUTS27P6"],
         avant="Ma lecture : DUPONT-PIPPIA, apres renegociation.",
         lecture="16378 est le compromis de COMI (RX6J289Y), ni DUPONT-PIPPIA ni DU PELOUX. La coupe se fait en TROIS.",
         repose="Son acte prevu (13/05/2021) = la vente prevue de ta ligne COMI au jour pres ; 244 000 = l'offre COMI ; "
                "10 000 d'honoraires = sa commission. DUPONT-PIPPIA etait annulee le 21/01/2021. Le gel le porte DEJA "
                "juste.",
         confiance="certaine", preuves=[(16378, 244000), (16380, 244000)]),
    dict(n="C2", groupe="17 (coupe 27133)", lignes=["2HOL5ISX", "JRE23R1G", "IEYXREWQ", "GQCBSQNY"],
         avant="Ma lecture : ALONSO, qui a offert 98 000 puis renegocie.",
         lecture="ALONSO n'a pas eu de compromis. 27135 (94 000) est a GENESTAS (JRE23R1G) ; 27134 (90 000) a ARMAND "
                 "TORE (IEYXREWQ).",
         repose="94 000 et 7 000 = l'offre et la commission de GENESTAS (le gel les lui donne deja) ; 90 000 = l'offre "
                "d'ARMAND TORE au centime ; ALONSO est annulee le 01/08/2023 (« rupture d'anevrisme »), a 98 000.",
         confiance="forte (27135) / moyenne-forte (27134)", preuves=[(27135, 94000), (27139, 94000), (27134, 90000), (27138, 90000)]),
    dict(n="C3", groupe="25 (coupe 4649)", lignes=["2FOH8HE4", "HHQZC2QP", "N9J2533O", "VX5RZL6B"],
         avant="Ma lecture : DUVET apres renegociation.",
         lecture="DUVET s'est retire 5 jours apres son offre (annulee le 20/07/2020) : il n'a aucun compromis. 4649 est a "
                 "MULLER (HHQZC2QP) ; 4651 a CHECCONI (N9J2533O).",
         repose="4649 : date 22/01/2021 = le « RDV ACQ 22/1 » note sur ta ligne MULLER, 32 000 et 3 500 = son offre et sa "
                "commission. 4651 : 31 000 et 3 500 = l'offre et la commission de CHECCONI.",
         confiance="forte", preuves=[(4649, 32000), (4653, 32000), (4651, 31000), (4655, 31000)]),
]

# Les « OUI » du classeur des groupes (que tu as valides EN BLOC) que le controle contredit.
CORRECTIONS = [
    dict(groupe="8", avant="OUI (faible) : 17131 a GALLONET -- « 47 500 ne colle a personne ».",
         apres="17131 est a MELKI (ZV3QRSJG) : 47 500 et 4 500 = son offre et sa commission ; « rdv du 03/4 reporte ».",
         confiance="forte", preuves=[(17131, 47500), (17136, 47500)]),
    dict(groupe="28", avant="OUI : 7450 (sans date, 143 000) a GUERIN.",
         apres="7450 est a DURIEUX (DN5U3GER) : 143 000 = son offre, 3 500 d'honoraires = SA commission (GUERIN : "
               "4 000, et son compromis 7449 est deja date au jour pres) ; ta ligne DURIEUX note « CPMIS 29/10 reporte ».",
         confiance="forte", preuves=[(7450, 143000), (7452, 143000), (7449, 143000)]),
    dict(groupe="40", avant="OUI : 14110 (sans date, 113 000) a GENOUX, « au nom GENOUX ».",
         apres="Indecidable : prix et honoraires identiques pour GENOUX, BLANC-MOURETTE et une 3e ligne oubliee, "
               "FARGE-DEBISE (L2B2WGCF, « ACQ se retractent » : un compromis signe puis retracte) ; le nom GENOUX est sur "
               "TOUS les compromis du bien. -> 14110 A PART. Le reste de la coupe tient.",
         confiance="aucune", preuves=[(14110, 113000), (14114, 113000)]),
    dict(groupe="22", avant="OUI : 4533 (sans date, 99 000) a COULON, « le nom departage ».",
         apres="Indecidable : le nom COULON est AUSSI sur le compromis signe de BERTHAUD-JOANNON (4534) ; prix et "
               "honoraires identiques. -> 4533 A PART. Le reste de la coupe tient.",
         confiance="aucune", preuves=[(4533, 99000), (4534, 99000)]),
    dict(groupe="29", avant="OUI : 7710 (sans date, 135 000) a GRATALOUP, « le nom departage ».",
         apres="Indecidable : le nom GRATALOUP est AUSSI sur le compromis signe de ROCHE (7711) ; prix et honoraires "
               "identiques. -> 7710 A PART. Le reste de la coupe tient.",
         confiance="aucune", preuves=[(7710, 135000), (7711, 135000)]),
    dict(groupe="50", avant="OUI : 4560 (sans date, 60 000) a LOUIS-DJIKSTRA, « au nom LOUIS ET DJIKSTRA ».",
         apres="Indecidable : ce nom est AUSSI sur le compromis signe de KUZNIAR (4561) ; prix et honoraires identiques. "
               "-> 4560 A PART. Le reste de la coupe tient.",
         confiance="aucune", preuves=[(4560, 60000), (4561, 60000)]),
]

SOEURS = ["YRUF0S9H", "D9MMB7OU", "6FQO29C8", "40ELE6SQ", "205f62be", "1c7b38f9", "CC8TJTBR"]


def lire_csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main() -> int:
    out: list[str] = []

    def dire(s=""):
        print(s, flush=True)
        out.append(s)

    echecs = []
    P = json.loads((CACHE / "t6_photo.json").read_text(encoding="utf-8"))
    LIG = P["lignes"]
    TX = {int(a): v for a, v in P["tx"].items()}
    CH = {"etat 5": {int(a): c for a, c in json.loads((CACHE / "chaines_s3.json").read_text(encoding="utf-8")).items()},
          "ce soir G2+outil": {int(a): c for a, c in json.loads(
              (CACHE / "chaines_ce_soir_avec_g2_et_outil.json").read_text(encoding="utf-8")).items()}}

    # ── le gel VIVANT, en lecture seule ──
    import psycopg2
    PU.load_env_files(PU.DEFAULT_ENV_FILES)
    u = urllib.parse.urlparse(os.environ["DATABASE_URL"])
    cn = psycopg2.connect(host=os.environ["SUPABASE_POOLER_HOST"], port=5432, dbname="postgres",
                          user="postgres.dwaqxfrinihnychuoptk", password=urllib.parse.unquote(u.password),
                          connect_timeout=15, sslmode="require")
    cu = cn.cursor()
    cu.execute("set transaction read only")
    cu.execute("select id_unique, app_affaire_id, confiance from app_classeur_lien")
    gel = cu.fetchall()
    cn.rollback()
    cn.close()
    g, cf = defaultdict(set), defaultdict(set)
    for i, a, c in gel:
        g[i].add(int(a))
        cf[i].add(c)
    dire("gel vivant : %d liens" % len(gel))

    V18 = {r["id_unique"]: r for r in lire_csv(VERDICTS_18)}
    att = {}
    for i, r in V18.items():
        if r["question_pour_frederic"].strip():
            att[i] = "question"
        elif "INCERTAIN" in (r["verdict"] + r["correction_contre_expert"]).upper():
            att[i] = "incertain"
    att.setdefault("SHN6RKDI", "muette")
    for r in lire_csv(OPERATIONS_V2):
        if r["decision_v2"] != "GARDEE":
            att.setdefault(r["id_unique"], "sortie de V2")

    def ranger(S, en_att, cible):
        def liens_c5(i):
            ts = {a for a in g.get(i, set()) if a in S}
            hk = {a for a in ts if not TX[a]["classeur"]}
            return hk or ts
        par_dossier = defaultdict(set)
        for i in g:
            for a in liens_c5(i):
                par_dossier[S[a]].add(i)
        res = {}
        for i in cible:
            ts = liens_c5(i)
            dossiers = {S[a] for a in ts}
            if LIG[i]["row"][0].strip():
                r = "A_DEJA_REMPLIE"
            elif not ts:
                r = "SANS_LIEN"
            elif i in en_att:
                r = "EN_ATTENTE"
            elif len(dossiers) > 1:
                r = "PLUSIEURS_DOSSIERS"
            elif par_dossier[next(iter(dossiers))] - {i}:
                r = "ETIQUETTE_PARTAGEE"
            elif cf.get(i, set()) - {SURE}:
                r = "LIEN_A_VALIDER"
            elif i in V18 and V18[i]["verdict"] not in ("JUSTE", "JUSTE_SANS_PREUVE_FORTE"):
                r = "AUDIT_NON_JUSTE"
            elif all(TX[a]["classeur"] for a in ts):
                r = "C5_SEULE"
            elif not any(i in TX[a]["designe"] for a in ts):
                r = "GEL_SEUL"
            else:
                r = "VAGUE_1"
            res[i] = r
        return res

    les23 = [i for q in QUESTIONS for i in q["lignes"]]
    # ── TEMOIN 1 : les 23 sont exactement les « A TOI » de la section 3 du classeur des groupes ──
    attendu = {r["lignes du Sheet"] for r in lire_csv(GROUPES)
               if r["section"].startswith("3") and r["MA RECOMMANDATION"].startswith("A TOI")}
    ok1 = set(les23) == attendu and len(les23) == 23 == len(set(les23))
    dire("TEMOIN 1 -- mes 23 lignes = les 23 « A TOI » de la section 3 : %s (manque %s, en trop %s)"
         % ("VERT" if ok1 else "ROUGE", sorted(attendu - set(les23)), sorted(set(les23) - attendu)))
    if not ok1:
        echecs.append("temoin 1")

    # ── TEMOIN 2 : chaque preuve citee existe au registre avec le montant ecrit ──
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite"), uri=True)
    mauvaises = []
    toutes = [p for q in QUESTIONS + SECTION1 + CORRECTIONS for p in q["preuves"]]
    for a, m in toutes:
        r = con.execute("select montant from app_affaire_ledger where app_affaire_id=?", (a,)).fetchone()
        if not r or r[0] in (None, "") or abs(float(r[0]) - m) > 1:
            mauvaises.append((a, m, r[0] if r else None))
    dire("TEMOIN 2 -- %d preuves citees, %d fausses %s" % (len(toutes), len(mauvaises), mauvaises[:5]))
    if mauvaises:
        echecs.append("temoin 2")

    # ── l'etat de chaque ligne : aujourd'hui, et sans sa question ──
    cible = les23 + [i for i in SOEURS if i in LIG]
    etat = {}
    for nom, S in CH.items():
        auj = ranger(S, set(att), cible)
        for i in cible:
            etat[(nom, i)] = (auj[i], ranger(S, set(att) - {i}, [i])[i])
    n_att = sum(1 for i in les23 if etat[("etat 5", i)][0] == "EN_ATTENTE")
    dire("Sur les 23 : %d en EN_ATTENTE aujourd'hui (ta mesure : 22)" % n_att)

    # ── ses « 4 deja ecrivables » ──
    quatre = []
    for i in les23:
        S = CH["etat 5"]
        ts = {a for a in g.get(i, set()) if a in S}
        hk = {a for a in ts if not TX[a]["classeur"]} or ts
        dossiers = {S[a] for a in hk}
        autres = {j for j in g if j != i and any(a in S and S[a] in dossiers for a in g[j])}
        if (len(dossiers) == 1 and not (cf[i] - {SURE}) and not autres
                and (i not in V18 or V18[i]["verdict"] in ("JUSTE", "JUSTE_SANS_PREUVE_FORTE"))):
            quatre.append(i)
    dire("Liens surs + un seul dossier + personne d'autre + aucun audit contre : %d -> %s" % (len(quatre), quatre))

    # ── les sorties ──
    def etat_txt(i):
        a5, s5 = etat[("etat 5", i)]
        ag, sg = etat[("ce soir G2+outil", i)]
        return "aujourd'hui %s ; sans la question %s (avec G2 + l'outil : %s)" % (a5, s5, sg)

    md = ["# Tes 23 questions en deux -- et la correction de mon classeur des groupes (20/11, soir)", "",
          "> Lecture seule. Genere par `phase2/checks/temps10_tes_questions_en_deux_2026-11-20.py` sur le gel vivant.",
          "> Regle de la pose (lue en production) : a la fusion comme a la scission, le groupe qui garde la PLUS PETITE",
          "> transaction garde l'etiquette. D'ou la question qui compte pour la colonne A : *ta reponse change-t-elle",
          "> l'etiquette ecrite ?*", ""]
    md += ["## Ta verification", "",
           "- EN_ATTENTE : %d sur 23 (la 23e, d2108609, est GEL_SEUL)." % n_att,
           "- Liens surs, un seul dossier, personne d'autre, aucun audit contre : %s." % ", ".join(quatre),
           "  d1cb8dd7, 2dfa6ef3 et HUY49KEC : JUSTE, leur etiquette ne depend pas de la question. d2108609 : NON -- "
           "sa seule piece chez Hektor (21520) est justement l'objet de la question (voir B2, CHOUVELLON).", ""]
    for titre, cl in (("A -- j'ai une lecture (a valider en bloc, marquees « TRANCHEE AU PLUS PROBABLE »)", "A"),
                      ("B -- hors de portee, la ligne ATTEND ta reponse", "B-attend"),
                      ("B -- hors de portee, mais l'ecriture n'en depend pas", "B-libre")):
        md += ["## " + titre, ""]
        for q in QUESTIONS:
            if q["classe"] != cl:
                continue
            md += ["### %s -- %s (%s)" % (q["n"], q["qui"], " ".join(q["lignes"])), "",
                   "- **La question** : " + q["question"],
                   "- **Ma lecture** : " + q["lecture"],
                   "- **Sur quoi** : " + q["repose"],
                   "- **Confiance** : " + q["confiance"],
                   "- **L'etiquette** : " + q["etiquette"]]
            md += ["- `%s` : %s" % (i, etat_txt(i)) for i in q["lignes"]]
            md += [""]
    md += ["## Section 1 de ton classeur -- les trois « A TOI » : MA LECTURE ETAIT FAUSSE", ""]
    for q in SECTION1:
        md += ["### %s -- groupe %s" % (q["n"], q["groupe"]), "", "- Avant : " + q["avant"],
               "- **Maintenant** : " + q["lecture"], "- **Sur quoi** : " + q["repose"],
               "- **Confiance** : " + q["confiance"], ""]
    md += ["## Les « OUI » du classeur que le controle contredit (tu les avais valides en bloc)", ""]
    for c in CORRECTIONS:
        md += ["- **Groupe %s** -- avant : %s **Maintenant** : %s (confiance : %s)" % (c["groupe"], c["avant"], c["apres"],
                                                                                     c["confiance"])]
    md += ["", "Les 62 autres « OUI » tiennent au controle : montant ET honoraires uniques, ou date au jour pres.",
           "Limite : une ligne du Sheet qui n'a AUCUNE piece chez nous sur le bien n'est pas vue par ce controle.", ""]
    SORTIE_MD.write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")

    entete = ["numero", "classe", "lignes du Sheet", "qui", "la question", "ma lecture", "sur quoi", "confiance",
              "l'etiquette depend-elle de ta reponse", "etat des lignes (gel vivant)", "TA DECISION"]
    rang = [[q["n"], q["classe"], " ".join(q["lignes"]), q["qui"], q["question"], q["lecture"], q["repose"],
             q["confiance"], q["etiquette"], " | ".join("%s : %s" % (i, etat_txt(i)) for i in q["lignes"]), ""]
            for q in QUESTIONS]
    with SORTIE_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(entete)
        w.writerows(rang)
        w.writerow([])
        for q in SECTION1:
            w.writerow([q["n"], "SECTION 1 (corrigee)", " ".join(q["lignes"]), q["groupe"], q["avant"], q["lecture"],
                        q["repose"], q["confiance"], "", "", ""])
        for c in CORRECTIONS:
            w.writerow(["groupe " + c["groupe"], "CORRECTION", "", "", c["avant"], c["apres"], "", c["confiance"], "", "",
                        ""])
    lar = [7, 6, 22, 20, 46, 46, 60, 11, 44, 50, 18]
    feuilles = [("A MA LECTURE", [entete] + [r for r in rang if r[1] == "A"], lar),
                ("B HORS DE PORTEE", [entete] + [r for r in rang if r[1] != "A"], lar),
                ("SECTION 1 CORRIGEE", [["numero", "groupe", "lignes", "avant", "maintenant", "sur quoi", "confiance",
                                         "TA DECISION"]] +
                 [[q["n"], q["groupe"], " ".join(q["lignes"]), q["avant"], q["lecture"], q["repose"], q["confiance"], ""]
                  for q in SECTION1], [6, 16, 30, 40, 60, 70, 18, 18]),
                ("LES OUI A CORRIGER", [["groupe", "avant (valide en bloc)", "maintenant", "confiance", "TA DECISION"]] +
                 [[c["groupe"], c["avant"], c["apres"], c["confiance"], ""] for c in CORRECTIONS], [8, 50, 90, 12, 18])]
    ecrire_xlsx(SORTIE_XLSX, feuilles)
    dire("ecrit : %s, .csv, .xlsx" % SORTIE_MD.name)
    dire("RESULTAT : %s" % ("VERT" if not echecs else "ROUGE " + ", ".join(echecs)))
    return 0 if not echecs else 1


if __name__ == "__main__":
    sys.exit(main())
