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

Option commune : --image <dossier> (sinon : l'image la plus recente).

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
VERSION = "v1 -- 22/11 : E1 a E9 (etiquette par la pose de nuit simulee sur le decoupage du protocole)"

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
}
# a part par SA decision (20/11 soir, B3) -- la meme liste que la V3
A_PART_PAR_DECISION = {14033: "B3, sa decision du 20/11 soir"}

# ⛔ LES REGLES PROPOSEES -- jamais appliquees sans son mot. Un passage lance avec --variantes X,Y est marque
#   « VARIANTE NON VALIDEE » : il sert a mesurer ce qu'une regle changerait (comparer), rien d'autre.
VARIANTES = {
    "P1": "une ligne que le gel ET le mandat mettent sur le meme bien, et le seul product_ref sur un autre, est sur le "
          "bien du gel et du mandat (deux sources independantes contre une)",
    "R4": "une piece A PART (sans preuve) ne peut jamais rejoindre plus tard un dossier dont elle deviendrait la plus "
          "petite (sa regle R4 du 20/11) -- elle ne retient donc pas la ligne au verrou E7",
}
VARIANTES_ACTIVES: set = set()
# son mot du 22/11, point 4 : « Le bien 39845 : je veux toujours voir ces deux affaires moi-meme. Mets-les-moi de cote »
BIENS_A_SA_DECISION = {"39845": "son mot du 22/11, point 4 -- les deux affaires du bien, il les voit lui-meme"}

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


def juger_ligne(I: Image, i: str, v: dict) -> dict:
    """LES EPREUVES, dans l'ordre. Version 0 : E1 et E2."""
    biens = sorted(I.biens_de_ligne.get(i, set()))
    base = {"id_unique": i, "num": v["num"], "biens": biens}

    def attente(code: str, texte: str = "") -> dict:
        return dict(base, verdict="ATTENTE", motif=code, motif_texte=texte or MOTIFS[code][1], epreuve=MOTIFS[code][0])
    # E1
    if len(I.sheet["par_id"][i]) > 1:
        return attente("ID_EN_DOUBLE", "ID Unique sur les lignes %s" % [x["num"] for x in I.sheet["par_id"][i]])
    if not biens:
        return attente("SANS_BIEN")
    if len(biens) > 1 and "P1" in VARIANTES_ACTIVES:
        par = {b: I.D.rattache_par.get((b, i), set()) for b in biens}
        forts = [b for b, r in par.items() if {"gel", "mandat"} <= r]
        if len(biens) == 2 and len(forts) == 1 and par[[b for b in biens if b != forts[0]][0]] == {"product_ref"}:
            biens = forts
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
        return attente("BIEN_SANS_PIECE", "bien %s : aucune piece" % b)
    if not vraies:
        return attente("BIEN_SANS_VRAIE_PIECE", "bien %s : %d copie(s), aucune vraie piece"
                       % (b, len(I.D.par_bien.get(b, []))))
    return None                     # E1 et E2 passees : la ligne se juge AVEC SON BIEN ENTIER (juger_bien)


def r_bien(I: Image, i: str) -> str:
    """Le bien d'une ligne qui a passe E1 (un seul, ou celui que la variante P1 a choisi)."""
    bs = I.biens_de_ligne[i]
    if len(bs) == 1:
        return next(iter(bs))
    forts = [b for b in bs if {"gel", "mandat"} <= I.D.rattache_par.get((b, i), set())]
    return forts[0]


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
    r = K.couper_le_bien(D, b, lignes_b, S, X, A_PART_PAR_DECISION)
    # E9 : la pose de nuit simulee sur le decoupage (chaque morceau devient un dossier ; le reste garde sa chaine)
    ch_new = {}
    for gl, ids in r["morceaux"].items():
        for a in ids:
            ch_new[a] = ("morceau", min(ids))
    for a in D.par_bien.get(b, []):
        ch_new.setdefault(a, ("chaine", S[a]))
    lab1 = K.pose_de_nuit({a: I.pieces[a]["app_dossier_uuid"] for a in ch_new}, ch_new)
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
        exc = exception_nommee(gl) if len(gl) > 1 else None
        if len(gl) > 1 and not exc:
            out.append(attente("DEUX_LIGNES_UN_DOSSIER", "avec %s ; morceau %s" % ("+".join(sorted(gl - {i})), ids)))
            continue
        m = min(hk)
        bloque = [] if "R4" in VARIANTES_ACTIVES else \
            sorted(a for a in r["apart"] if I.nature[a] == PC.VRAIE and a < m and gl in r["possibles"][a])
        if bloque:
            out.append(attente("VERROU_PIECE_PLUS_PETITE", "plus petite de la ligne %d ; a part et plus petites : %s"
                               % (m, "; ".join("%d (%s)" % (a, r["apart"][a]) for a in bloque))))
            continue
        neutres = sorted(a for a in r["apart"] if gl in r["possibles"][a])
        preuves = [preuve_nommee(I, a, gl, r["preuve"].get(a, "")) for a in ids]
        if neutres:
            preuves.append("a part sans effet sur l'etiquette (son critere 2) : %s" % " ".join(map(str, neutres)))
        if exc:
            preuves.append("exception nommee : %s -- %s" % (exc, "+".join(sorted(gl))))
        out.append(dict(base, verdict="TRANCHEE", etiquette=lab1[m], pieces=ids, preuves=preuves, epreuve="E9"))
    return out


def etape_passage(I: Image, note: str, perimetre: str = "bien", variantes: set | None = None) -> int:
    VARIANTES_ACTIVES.clear()
    VARIANTES_ACTIVES.update(variantes or ())
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
    for fam in ("coupes_132", "coupes_29"):
        for e in T["familles"][fam]:
            for m in e["morceaux"]:
                juger_pieces(fam, m["lignes"], m["pieces"], vraies_seules=True)
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


def etape_rapport(p: int | None) -> int:
    import csv
    con = socle()
    if p is None:
        p = con.execute("select max(id) from passage").fetchone()[0]
    image, version, debut = con.execute("select image, version, debut from passage where id=?", (p,)).fetchone()
    sortie = NOTICE / ("PROTOCOLE_PASSAGE_%d_LE_VERDICT_DE_CHAQUE_LIGNE_%s.csv" % (p, debut[:10]))
    rows = list(con.execute("select id_unique, num, biens, verdict, etiquette, pieces, preuves, motif, motif_texte, "
                            "epreuve from verdict where passage=? order by num", (p,)))
    with sortie.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id_unique", "ligne_du_sheet", "bien", "verdict", "etiquette", "piece", "preuve_nommee", "motif",
                    "pourquoi", "epreuve"])
        for i, n, bs, v, e, ps, pr, m, mt, ep in rows:
            b = " ".join(json.loads(bs))
            if v == "TRANCHEE":
                pieces, preuves = json.loads(ps), json.loads(pr)
                par_piece = {int(x.split()[0]): x for x in preuves if x.split()[0].isdigit()}
                for a in pieces:
                    w.writerow([i, n, b, v, e, a, par_piece.get(a, ""), "", "", ep])
                for x in preuves:
                    if not x.split()[0].isdigit():
                        w.writerow([i, n, b, v, e, "", x, "", "", ep])
            else:
                w.writerow([i, n, b, v, "", "", "", m, mt, ep])
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
    p.add_argument("--variantes", default="", help="regles PROPOSEES a mesurer, ex. P1,R4 (jamais appliquees)")
    p.add_argument("--perimetre", choices=("bien", "chaines"), default="bien",
                   help="bien : toutes les pieces du bien (le protocole) ; chaines : celles que le gel touche (le 20/11)")
    c = sp.add_parser("comparer")
    c.add_argument("p1", type=int)
    c.add_argument("p2", type=int)
    k = sp.add_parser("compter")
    k.add_argument("p", type=int, nargs="?")
    sp.add_parser("temoins")
    r_ = sp.add_parser("rapport")
    r_.add_argument("p", type=int, nargs="?")
    a = ap.parse_args()
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
    return etape_passage(I, a.note, a.perimetre, {x for x in a.variantes.split(",") if x})


if __name__ == "__main__":
    sys.exit(main())
