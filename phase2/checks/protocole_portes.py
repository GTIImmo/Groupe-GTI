#!/usr/bin/env python3
"""PAR QUELLE PORTE CHAQUE CORRECTION PASSE, ET CE QUE CA DEPLACE -- chantier classeur, ⑳, 22/11/2026.

Son mot du 22/11 (reponses au rapport 20, § 2) : « Ton fichier dit OU IL FAUT ARRIVER [...]. Il ne dit pas LE CHEMIN
pour y aller. [...] LE CHAINAGE REFAIT TOUS LES DOSSIERS CHAQUE NUIT : une correction posee en base serait effacee au
run suivant. » Il demande deux comptes :
  a) pour chaque ligne tranchee, PAR QUELLE PORTE sa correction passe : une regle, un rattachement a la main, une coupe,
     sa decision chez Hektor, ou rien a corriger ;
  b) LE COMPTE DU MOUVEMENT : combien de liens du gel se delient, se relient, combien de dossiers se recoupent, combien
     d'etiquettes changent de ligne.

⛔ LECTURE SEULE, sur une IMAGE du protocole : le VRAI code du chainage (phase2/sync/affaire_ledger.py) rejoue sur une
COPIE EN MEMOIRE du registre de l'image ; le fichier de coupes du protocole est un BROUILLON dans le cache, jamais dans
phase2/sync. Rien en base, rien dans le Sheet, rien chez Hektor.

LES REJEUX (le module de production, ses interrupteurs lus dans .env comme la nuit) :
  A  la nuit telle qu'elle tourne (G2 et l'outil de coupe ETEINTS) -- TEMOIN : elle doit redonner EXACTEMENT les
     dossiers de l'image, piece par piece (sinon rien de ce qui suit ne vaut).
  B  A + la regle G2 (codee le 20/11, eteinte) : ce qu'une regle DEJA ECRITE corrigerait, et ce qu'elle casserait.
  E  A + le brouillon des coupes du protocole (une ligne par morceau a corriger) : l'etat d'arrivee EXACT. Les
     etiquettes y sont posees par la pose de nuit (coupe_preuve_interne.pose_de_nuit) et comparees, ligne par ligne,
     a celles du passage (simulees) -- c'est le REJEU EXACT de l'etiquette.

LA PORTE D'UNE LIGNE TRANCHEE (sur les dossiers du rejeu A) -- M = ses pieces, N = ses neutres (a part sans effet) :
  RIEN          ses pieces sont dans UN dossier, qui ne porte rien d'autre que M et des neutres a elle
  RATTACHEMENT  ses pieces sont dans PLUSIEURS dossiers qui ne portent rien d'autre : les reunir suffit (le fichier des
                rattachements a la main, allume, joue chaque nuit)
  COUPE         un de ses dossiers porte aussi une piece qui n'est pas a elle : il faut la couper (le fichier des
                detachements, eteint) -- « deja ecrite » si un des 275 morceaux de ses 132 coupes est exactement M
  REGLE         dite a part : la ligne que la regle G2 (deja codee, eteinte) mettrait juste toute seule
  MISE_DE_COTE  la ligne est juste aujourd'hui, mais sa piece plus petite (regle R7b) doit etre FIGEE hors de son dossier,
                AVEC son dossier d'aujourd'hui : une ligne du fichier des coupes qui ne change rien ce jour-la (sa regle :
                « une piece mise de cote GARDE SON ANCIEN NUMERO DE DOSSIER »)
  HEKTOR        en surimpression : la ligne tient deux vraies pieces d'un meme genre (un doublon chez Hektor) -- sans
                effet sur l'etiquette, c'est sa decision, bien par bien
  ⭐ C5 AUX PORTES (sur son « OUI, ECRIS LA COUPE », reponses 21 quater, 22/11 soir) : une ligne RIEN (ou MISE_DE_COTE)
                que le chainage SANS LES COPIES ne tient plus juste ne doit sa separation qu'a une copie -- « une creation
                du Sheet ne decide jamais » (C5, 19/11). Elle devient COUPE_NEUVE : son morceau s'ecrit au brouillon,
                et la separation tient sans la copie. Mesure du 22/11 : 4 lignes (535, 3540 bien 5262 ; 2388, 4113
                bien 24733), et l'arrivee ne change pas (0 piece).

USAGE (un rejeu du chainage prend ~4 min 30 : la mesure est DECOUPEE, chaque rejeu ecrit au fil dans le cache) :
  python -u phase2/checks/protocole_portes.py --rejeu A     la nuit telle qu'elle tourne (et son temoin)
  python -u phase2/checks/protocole_portes.py --rejeu B     + G2
  python -u phase2/checks/protocole_portes.py --rejeu E     + le brouillon des coupes du protocole (il lui faut A)
  python -u phase2/checks/protocole_portes.py               les comptes, depuis les trois rejeux (aucun rejeu)
  option : --passage P (defaut : le dernier passage du socle)
CODES : 0 fait et vert . 1 un temoin crie (le rejeu A ne redonne pas l'image, ou l'etiquette exacte differe) . 2 pas pu
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import csv
import importlib.util
import io
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import coupe_preuve_interne as K  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402
import protocole_classeur as P  # noqa: E402

MODULE = RACINE / "phase2" / "sync" / "affaire_ledger.py"
FICHIER_DET_PROD = RACINE / "phase2" / "sync" / "detachements_manuels.csv"
FICHIER_RAT_PROD = RACINE / "phase2" / "sync" / "rattachements_manuels.csv"
ETEINTS = {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "0"}


def dire(s: str = "") -> None:
    print(s, flush=True)


def charger(nom: str, fichier_det: Path):
    """Le module de production, charge a part, son fichier de detachements pointe sur `fichier_det` (un brouillon)."""
    source = MODULE.read_text(encoding="utf-8")
    for avant, apres in (("ROOT = Path(__file__).resolve().parents[2]", "ROOT = Path(%r)" % str(RACINE)),
                         ('FICHIER_RATTACHEMENTS = Path(__file__).resolve().parent / "rattachements_manuels.csv"',
                          "FICHIER_RATTACHEMENTS = Path(%r)" % str(FICHIER_RAT_PROD)),
                         ('FICHIER_DETACHEMENTS = Path(__file__).resolve().parent / "detachements_manuels.csv"',
                          "FICHIER_DETACHEMENTS = Path(%r)" % str(fichier_det))):
        if avant not in source:
            raise SystemExit("⛔ le module de production a change : ancre introuvable %r" % avant[:60])
        source = source.replace(avant, apres)
    tmp = P.DOSSIER / ("_module_portes_%s.py" % nom)
    tmp.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("al_portes_" + nom, tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rejouer(mod, registre: Path, env: dict) -> tuple[dict, dict]:
    """recalculer_les_chaines sur une COPIE EN MEMOIRE du registre de l'image -> {piece: chaine}, compte rendu."""
    gardes = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        src = sqlite3.connect("file:%s?mode=ro" % registre.as_posix(), uri=True)
        mem = sqlite3.connect(":memory:")
        src.backup(mem)
        src.close()
        with contextlib.redirect_stdout(io.StringIO()) as sortie:
            res = mod.recalculer_les_chaines(mem)
        ch = {int(a): (int(c) if c is not None else None) for a, c in
              mem.execute("SELECT app_affaire_id, app_chaine_id FROM %s" % mod.LEDGER_TABLE)}
        mem.close()
        res["_ligne"] = sortie.getvalue().strip().splitlines()[-1] if sortie.getvalue().strip() else ""
        return ch, res
    finally:
        for k, v in gardes.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def rejeu_en_cache(nom: str, image: str, fichier_det: Path, env: dict, calculer: bool) -> tuple[dict, dict]:
    """Un rejeu, garde dans le cache sous une cle qui porte l'image, le module, les deux fichiers et les interrupteurs :
    si l'un d'eux change, la cle change et le rejeu se refait (jamais un resultat perime)."""
    h = hashlib.md5()
    for p_ in (MODULE, FICHIER_RAT_PROD, fichier_det):
        h.update(p_.read_bytes().replace(b"\r\n", b"\n"))
    h.update(json.dumps(env, sort_keys=True).encode())
    f = P.DOSSIER / ("rejeu_%s_%s_%s.json" % (image, nom, h.hexdigest()[:12]))
    if f.exists():
        d = json.loads(f.read_text(encoding="utf-8"))
        return {int(k): v for k, v in d["ch"].items()}, d["res"]
    if not calculer:
        raise SystemExit("⛔ le rejeu %s n'est pas dans le cache (%s) -- lancer d'abord : --rejeu %s" % (nom, f.name, nom))
    t0 = time.time()
    ch, res = rejouer(charger(nom.lower(), fichier_det), P.IMAGES / image / "registre.sqlite", env)
    f.write_text(json.dumps({"ch": {str(k): v for k, v in ch.items()}, "res": res, "duree_s": round(time.time() - t0)},
                            ensure_ascii=False), encoding="utf-8")
    dire("   rejeu %s fait en %.0f s -> %s" % (nom, time.time() - t0, f.name))
    return ch, res


def membres(ch: dict) -> dict:
    m = defaultdict(set)
    for a, c in ch.items():
        m[c].add(a)
    return m


def rejeu_sans_copies(image: str, I) -> dict:
    """Le chainage de la nuit (rejeu A : G2 et l'outil eteints) sur une copie EN MEMOIRE de l'image, les copies C5
    retirees -- en cache (cle : image, module, rattachements, detachements, liste des copies). Ecrit le 22/11 dans
    protocole_ce_qui_a_deplace_les_2560_depuis_le_16_11.py, rapatrie ici quand C5 est entree aux portes (meme cle)."""
    copies = sorted(a for a, n in I.nature.items() if n == PC.COPIE)
    h = hashlib.md5()
    for p_ in (MODULE, FICHIER_RAT_PROD, FICHIER_DET_PROD):
        h.update(p_.read_bytes().replace(b"\r\n", b"\n"))
    h.update(json.dumps([ETEINTS, copies], sort_keys=True).encode())
    f = P.DOSSIER / ("rejeu_%s_A_SANS_COPIES_%s.json" % (image, h.hexdigest()[:12]))
    if f.exists():
        d = json.loads(f.read_text(encoding="utf-8"))
        return {int(k): v for k, v in d["ch"].items()}
    t0 = time.time()
    mod = charger("sans_copies", FICHIER_DET_PROD)
    gardes = {k: os.environ.get(k) for k in ETEINTS}
    os.environ.update(ETEINTS)
    try:
        src = sqlite3.connect("file:%s?mode=ro" % (P.IMAGES / image / "registre.sqlite").as_posix(), uri=True)
        mem = sqlite3.connect(":memory:")
        src.backup(mem)
        src.close()
        n = mem.execute("delete from %s where app_affaire_id in (%s)" % (mod.LEDGER_TABLE, ",".join(map(str, copies)))
                        ).rowcount
        if n != len(copies):
            raise SystemExit("⛔ %d copies retirees sur %d" % (n, len(copies)))
        with contextlib.redirect_stdout(io.StringIO()):
            mod.recalculer_les_chaines(mem)
        ch = {int(a): (int(c) if c is not None else None) for a, c in
              mem.execute("select app_affaire_id, app_chaine_id from %s" % mod.LEDGER_TABLE)}
        mem.close()
    finally:
        for k, v in gardes.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    f.write_text(json.dumps({"ch": {str(k): v for k, v in ch.items()}, "copies": copies,
                             "duree_s": round(time.time() - t0)}), encoding="utf-8")
    dire("   rejeu SANS LES %d COPIES fait en %.0f s -> %s" % (len(copies), time.time() - t0, f.name))
    return ch


def neutres_de(preuves: list) -> set:
    """Les pieces a part que le dossier de la ligne peut garder : ses neutres (son critere 2) et, si la variante R7a joue,
    les plus petites deja dans son dossier."""
    out = set()
    for x in preuves:
        if x.startswith("a part sans effet") or x.startswith("a part deja dans son dossier"):
            out |= {int(n) for n in x.split(":")[-1].split()}
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--passage", type=int)
    ap.add_argument("--rejeu", choices=("A", "B", "E"))
    a = ap.parse_args()
    t0 = time.time()
    con = P.socle()
    pid = a.passage or con.execute("select max(id) from passage").fetchone()[0]
    image, version, note = con.execute("select image, version, note from passage where id=?", (pid,)).fetchone()
    if "VARIANTE" in version:
        raise SystemExit("⛔ le passage %d est une VARIANTE NON VALIDEE -- on ne compte pas les portes d'une variante" % pid)
    I = P.Image(P.IMAGES / image)
    V = {}
    for i, num, bs, v, e, ps, pr, m in con.execute("select id_unique, num, biens, verdict, etiquette, pieces, preuves, "
                                                   "motif from verdict where passage=?", (pid,)):
        V[i] = {"num": num, "biens": json.loads(bs), "verdict": v, "etiquette": e,
                "pieces": set(json.loads(ps)) if ps else set(), "preuves": json.loads(pr) if pr else [], "motif": m}
    con.close()
    T = {i: x for i, x in V.items() if x["verdict"] == "TRANCHEE"}
    dire("LES PORTES -- passage %d (%s), image %s : %d lignes tranchees sur %d" % (pid, version, image, len(T), len(V)))
    reg = I.d / "registre.sqlite"
    ch_img = {a: I.pieces[a]["app_chaine_id"] for a in I.pieces}
    lab_img = {a: I.pieces[a]["app_dossier_uuid"] for a in I.pieces}
    bien_de = {a: str(I.pieces[a]["hektor_annonce_id"]) for a in I.pieces}

    # ── REJEU A : la nuit telle qu'elle tourne -- TEMOIN : elle redonne l'image ───────────────────────────────────────
    chA, resA = rejeu_en_cache("A", image, FICHIER_DET_PROD, ETEINTS, a.rejeu == "A")
    ecartsA = sorted(x for x in ch_img if ch_img[x] != chA.get(x))
    dire("   REJEU A (la nuit, G2 et l'outil eteints) : %d pieces ; %d dans un autre dossier que l'image (attendu 0) "
         "-- %.0f s" % (len(chA), len(ecartsA), time.time() - t0))
    if ecartsA:
        dire("   ⛔ TEMOIN ROUGE : le rejeu ne redonne pas l'image -- ex. %s" % ecartsA[:10])
        return 1
    mA = membres(chA)
    if a.rejeu == "A":
        return 0

    # ── LE FICHIER DES 132 COUPES (eteint) : ses morceaux, pour dire « deja ecrite » ──────────────────────────────────
    morceaux_132 = {}
    for ligne in FICHIER_DET_PROD.read_text(encoding="utf-8-sig").splitlines():
        if not ligne.strip() or ligne.startswith("#") or ligne.startswith("transactions;"):
            continue
        p_ = ligne.split(";")
        morceaux_132[frozenset(int(x) for x in p_[0].split())] = p_[2]

    # ── LA PORTE DE CHAQUE LIGNE TRANCHEE, sur les dossiers du rejeu A ───────────────────────────────────────────────
    tenue_par = defaultdict(set)
    for i, x in T.items():
        for p_ in x["pieces"]:
            tenue_par[p_].add(i)
    gel_l = defaultdict(set)
    gel_p = defaultdict(set)
    for i, p_, *_r in I.gel:
        gel_l[i].add(int(p_))
        gel_p[int(p_)].add(i)
    porte, detail = {}, {}
    nature_extra = Counter()
    for i, x in sorted(T.items()):
        M, N = x["pieces"], neutres_de(x["preuves"])
        Cs = {chA[p_] for p_ in M}
        U = set().union(*(mA[c] for c in Cs))
        extras = U - M - N
        kinds = Counter(I.pieces[p_]["kind"] for p_ in M if I.nature[p_] == PC.VRAIE)
        doublon = sorted(k for k, n in kinds.items() if n > 1)
        if len(Cs) == 1 and not extras:
            pt = "RIEN"
        elif not extras:
            pt = "RATTACHEMENT"
        else:
            pt = "COUPE_DEJA_ECRITE" if frozenset(M) in morceaux_132 or frozenset(
                q for q in M if I.nature[q] == PC.VRAIE) in {frozenset(q for q in k if I.nature.get(q) == PC.VRAIE)
                                                             for k in morceaux_132} else "COUPE_NEUVE"
        quoi = []
        for e in sorted(extras):
            if tenue_par.get(e):
                q = "piece d'une autre ligne tranchee (%s)" % "+".join(sorted(tenue_par[e]))
                nature_extra["d'une autre ligne tranchee"] += 1
            elif gel_p.get(e) and any(V.get(j, {}).get("verdict") == "ATTENTE" for j in gel_p[e]):
                q = "piece d'une ligne EN ATTENTE par le gel (%s)" % "+".join(sorted(gel_p[e]))
                nature_extra["d'une ligne en attente (par le gel)"] += 1
            elif I.nature.get(e) == PC.COPIE:
                q = "copie C5 d'une autre ligne"
                nature_extra["copie C5 d'une autre ligne"] += 1
            else:
                q = "piece a personne (a part, ou sans ligne)"
                nature_extra["a personne (a part, ou sans ligne)"] += 1
            quoi.append("%d %s %s : %s" % (e, I.pieces[e]["kind"], I.pieces[e]["state"] or "", q))
        porte[i] = pt
        detail[i] = {"porte": pt, "dossiers_aujourdhui": len(Cs), "extras": sorted(extras), "extras_quoi": quoi,
                     "doublon_hektor": doublon, "neutres": sorted(N)}
    # R7b (validee le 22/11) : les pieces mises de cote, AVEC leur dossier d'aujourd'hui -- le passage les a ecrites
    f_mdc = P.DOSSIER / ("mises_de_cote_passage_%d.json" % pid)
    MDC = json.loads(f_mdc.read_text(encoding="utf-8")) if f_mdc.exists() else {}
    groupes_mdc = {}
    for a_, x in MDC.items():
        groupes_mdc[frozenset(x["groupe"])] = x
    mdc_de_ligne = defaultdict(set)
    for i, x in T.items():
        for pr in x["preuves"]:
            if pr.startswith("a part MISE DE COTE"):
                mdc_de_ligne[i] |= {int(n) for n in pr.split(":")[-1].split()}
    for i in mdc_de_ligne:
        if porte[i] == "RIEN":
            porte[i] = "MISE_DE_COTE"
            detail[i]["porte"] = "MISE_DE_COTE"
        detail[i]["mise_de_cote"] = sorted(mdc_de_ligne[i])
    # ⭐ C5 AUX PORTES (son « OUI, ECRIS LA COUPE », 21 quater) : une ligne RIEN ou MISE_DE_COTE que le chainage SANS LES
    #   COPIES ne tient plus juste ne doit sa separation qu'a une copie -> COUPE_NEUVE (son morceau s'ecrit au brouillon)
    ch0 = rejeu_sans_copies(image, I)
    m0 = membres(ch0)
    c5p = []
    for i, x in sorted(T.items()):
        if porte[i] not in ("RIEN", "MISE_DE_COTE"):
            continue
        Mv = {q for q in x["pieces"] if q in ch0}
        Nv = {q for q in neutres_de(x["preuves"]) if q in ch0}
        Cs0 = {ch0[q] for q in Mv}
        if Mv and len(Cs0) == 1 and not (m0[next(iter(Cs0))] - Mv - Nv):
            continue
        c5p.append(i)
        detail[i]["c5_aux_portes"] = {"porte_sans_la_regle": porte[i], "dossiers_sans_copies": len(Cs0),
                                      "pieces_de_trop_sans_copies": sorted(set().union(*(m0[c] for c in Cs0)) - Mv - Nv)
                                      if Cs0 else []}
        porte[i] = "COUPE_NEUVE"
        detail[i]["porte"] = "COUPE_NEUVE"
    dire("   C5 AUX PORTES : %d ligne(s) juste(s) aujourd'hui que le chainage SANS LES COPIES ne tient plus -> COUPE_NEUVE "
         ": %s" % (len(c5p), " ".join("%s (ligne %s, etait %s)" % (i, T[i]["num"],
                                                                   detail[i]["c5_aux_portes"]["porte_sans_la_regle"])
                                      for i in c5p)))
    # R7a (validee le 22/11) : la piece a part DEJA dans le dossier de la ligne y reste -- « on ne coupe pas le dossier
    #   entre elles » : si la ligne doit etre coupee d'autre chose, son morceau l'emporte avec elle (mesure du 22/11 :
    #   sans cela, 305KAY9W perdait sa 24124 dans le reste de l'ancien dossier)
    r7a_de_ligne = defaultdict(set)
    for i, x in T.items():
        for pr in x["preuves"]:
            if pr.startswith("a part deja dans son dossier"):
                r7a_de_ligne[i] |= {int(n) for n in pr.split(":")[-1].split()}
    dire("   R7b : %d piece(s) mise(s) de cote, en %d dossier(s) figes tels quels, pour %d ligne(s)"
         % (len(MDC), len(groupes_mdc), len(mdc_de_ligne)))
    cpt = Counter(porte.values())
    porte_a = dict(porte)                      # la porte sur la nuit d'aujourd'hui, avant de regarder G2
    dire("   LA PORTE (rejeu A) : " + " . ".join("%s %d" % kv for kv in sorted(cpt.items(), key=lambda kv: -kv[1])))
    dire("      les pieces de trop dans les dossiers a couper : " + " . ".join("%s %d" % kv for kv in
                                                                               nature_extra.most_common()))
    dbl = sorted(i for i in T if detail[i]["doublon_hektor"])
    dire("   HEKTOR (en surimpression) : %d lignes tiennent deux vraies pieces d'un meme genre" % len(dbl))

    # ── REJEU B : + la regle G2 (codee, eteinte) ────────────────────────────────────────────────────────────────────
    if a.rejeu not in (None, "B"):
        chB = None
    else:
        chB, resB = rejeu_en_cache("B", image, FICHIER_DET_PROD, {"APP_CHAINAGE_GARDE_G2": "1",
                                                                   "APP_CHAINAGE_DETACHEMENTS": "0"}, a.rejeu == "B")
    if a.rejeu == "B":
        return 0
    mB = membres(chB) if chB else {}

    def juste(i: str, ch: dict, mm: dict) -> bool:
        M, N = T[i]["pieces"], neutres_de(T[i]["preuves"])
        Cs = {ch[p_] for p_ in M}
        return len(Cs) == 1 and not (mm[next(iter(Cs))] - M - N)
    # ⚠ les lignes « C5 aux portes » ne se jugent pas sur B : B porte encore les copies, qui les tiennent justes
    par_g2 = sorted(i for i in T if porte[i] not in ("RIEN", "MISE_DE_COTE") and i not in c5p
                    and juste(i, chB, mB)) if chB else []
    casse_g2 = sorted(i for i in T if porte[i] in ("RIEN", "MISE_DE_COTE") and not juste(i, chB, mB)) if chB else []
    bouge_g2 = sum(1 for p_ in chA if chA[p_] != chB.get(p_)) if chB else -1
    dire("   REJEU B (+ G2) : %d pieces changent de dossier ; G2 mettrait JUSTES %d lignes a corriger, et en CASSERAIT %d "
         "qui sont justes aujourd'hui -- %.0f s" % (bouge_g2, len(par_g2), len(casse_g2), time.time() - t0))
    if chB:
        dire("      les %d que G2 met justes, par porte d'aujourd'hui : %s" % (len(par_g2), dict(Counter(
            porte_a[i] for i in par_g2))))
        biens_t_ = {T[i]["biens"][0] for i in T}
        hors_g2 = sorted(p_ for p_ in chA if chA[p_] != chB.get(p_) and bien_de[p_] not in biens_t_)
        att_g2 = sorted(i for i in V if V[i]["verdict"] == "ATTENTE"
                        and any(q in chA and mA[chA[q]] != mB[chB[q]] for q in gel_l[i]))
        dire("      ce que G2 fait AILLEURS : %d pieces bougent hors des biens des lignes tranchees ; %d lignes en attente "
             "dont un dossier bouge" % (len(hors_g2), len(att_g2)))
        g2_ailleurs = {"hors": len(hors_g2), "hors_ex": hors_g2[:30], "attente": att_g2}
    else:
        g2_ailleurs = {}
    for i in par_g2:
        porte[i] = "REGLE_G2"
    cpt = Counter(porte.values())
    dire("   ⭐ LA PORTE, G2 comptee en premier : " + " . ".join("%s %d" % kv for kv in
                                                              sorted(cpt.items(), key=lambda kv: -kv[1])))

    # ── REJEU E : A + le brouillon des coupes du protocole -> l'etat d'arrivee exact ──────────────────────────────────
    brouillon = P.DOSSIER / ("brouillon_detachements_protocole_passage_%d.csv" % pid)
    lignes_b = ["# BROUILLON -- jamais dans phase2/sync. Le protocole, passage %d (image %s) : un morceau par ligne "
                "tranchee dont la porte n'est pas RIEN (rattachement et coupe ensemble : l'outil de coupe sait aussi "
                "reunir). Pour le rejeu E de protocole_portes.py, rien d'autre." % (pid, image),
                "transactions;bien;geste;pourquoi"]
    vus, figes, mdc_figees = set(), [], []
    for i in sorted(T):
        k_ = frozenset(T[i]["pieces"]) | frozenset(r7a_de_ligne.get(i, set()))
        if any(P.supprimee_chez_hektor(I.pieces[q]) for q in k_) and porte_a[i] not in ("RIEN", "MISE_DE_COTE"):
            figes.append(i)                    # le chainage ne la trouverait pas (« transaction introuvable »)
            continue
        if porte_a[i] not in ("RIEN", "MISE_DE_COTE") and k_ not in vus:   # les jumelles : un seul morceau pour les deux
            vus.add(k_)
            lignes_b.append("%s;%s;protocole_%s;%s%s" % (" ".join(map(str, sorted(k_))), T[i]["biens"][0],
                                                        porte_a[i].lower(), i, (" -- avec sa piece a part deja dans son "
                                                                                "dossier (R7a) %s" % " ".join(map(
                                                                                    str, sorted(r7a_de_ligne[i]))))
                                                        if r7a_de_ligne.get(i) else ""))
    # R7b : chaque dossier mis de cote, fige tel quel, AVEC SON ANCIEN NUMERO ecrit sur sa ligne (sa regle)
    for g_, x in sorted(groupes_mdc.items(), key=lambda kv: min(kv[0])):
        if g_ in vus:
            continue
        vus.add(g_)
        f_ = [q for q in g_ if P.supprimee_chez_hektor(I.pieces[q])]
        if f_ and len(f_) == len(g_):
            # SUPPRIMEE CHEZ HEKTOR : le chainage la fige deja dans son dossier (« la trace garde son dossier ») -- elle ne
            #   peut rejoindre aucun dossier, et le fichier la dirait « introuvable » chaque nuit : pas de ligne a ecrire
            mdc_figees.append(sorted(g_))
            continue
        if f_:
            dire("   ⛔ un dossier mis de cote MELE une piece supprimee chez Hektor et d'autres : %s" % sorted(g_))
        lignes_b.append("%s;%s;protocole_mise_de_cote;garde son ancien numero %s (%s) -- regle R7b, pour %s" % (
            " ".join(map(str, sorted(g_))), x["bien"], x["ancien_numero"], x["ancien_uuid"],
            "+".join(sorted(i for i in mdc_de_ligne if mdc_de_ligne[i] & g_))))
    brouillon.write_text("\n".join(lignes_b) + "\n", encoding="utf-8")
    chE, resE = rejeu_en_cache("E", image, brouillon, {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"},
                               a.rejeu == "E")
    if a.rejeu == "E":
        return 0
    mE = membres(chE)
    lus = [x for x in lignes_b[2:]]
    refus = {k: v for k, v in resE.items() if str(k).startswith("[X]") and "decide a la main" not in str(k)}
    dire("   REJEU E (A + le brouillon : %d morceaux lus) : compte rendu %s -- %.0f s"
         % (len(lus), {k: v for k, v in resE.items() if str(k).startswith("[X]")}, time.time() - t0))
    faux_E = sorted(i for i in T if not juste(i, chE, mE))
    if figes:
        dire("   ⛔ morceaux a corriger qui tiennent une piece supprimee chez Hektor (aucune porte) : %s" % figes)
    dire("   ⭐ lignes tranchees JUSTES dans l'etat d'arrivee : %d sur %d%s" % (
        len(T) - len(faux_E), len(T), (" -- ⛔ PAS JUSTES : %s" % faux_E[:12]) if faux_E else ""))
    # R7b : chaque dossier mis de cote est-il SEUL dans son dossier a l'arrivee, et garde-t-il son ancien numero ?
    labE_ = K.pose_de_nuit(lab_img, chE)
    mdc_faux = []
    for g_, x in groupes_mdc.items():
        cs = {chE[q] for q in g_}
        seul = len(cs) == 1 and mE[next(iter(cs))] == set(g_)
        garde = all(labE_[q] == x["ancien_uuid"] for q in g_)
        if not (seul and garde):
            mdc_faux.append((sorted(g_), seul, garde))
    dire("   ⭐ R7b, SA REGLE : %d dossier(s) mis de cote sur %d sont seuls a l'arrivee ET gardent leur ancien numero%s"
         % (len(groupes_mdc) - len(mdc_faux), len(groupes_mdc), (" -- ⛔ %s" % mdc_faux) if mdc_faux else ""))
    dire("      dont %d deja figes par le chainage (supprimes chez Hektor : aucune ligne dans le fichier) : %s"
         % (len(mdc_figees), mdc_figees))
    # hors des biens du protocole, rien ne doit bouger
    biens_t = {T[i]["biens"][0] for i in T}
    hors = sorted(p_ for p_ in chA if chA[p_] != chE.get(p_) and bien_de[p_] not in biens_t)
    dire("   temoin : pieces qui bougent HORS des biens des lignes tranchees : %d (attendu 0)" % len(hors))

    # ── LE REJEU EXACT DE L'ETIQUETTE : la pose de nuit sur l'etat d'arrivee, contre l'etiquette du passage ───────────
    labE = K.pose_de_nuit(lab_img, chE)
    lab_ligne_E = {i: labE[min(q for q in T[i]["pieces"] if I.nature[q] == PC.VRAIE)] for i in T}
    # ⛔ L'ECRIVAIN EXIGE LA MEME ETIQUETTE SUR TOUTES LES VRAIES PIECES DE LA LIGNE : on l'exige aussi ici
    diff_lab = sorted(i for i in T if {labE[q] for q in T[i]["pieces"] if I.nature[q] == PC.VRAIE}
                      != {T[i]["etiquette"]})
    dire("   ⭐ REJEU EXACT DE L'ETIQUETTE : %d lignes sur %d ont la meme etiquette que le passage%s"
         % (len(T) - len(diff_lab), len(T), (" -- ⛔ autres : %s" % [(i, T[i]["etiquette"], lab_ligne_E[i])
                                                                     for i in diff_lab[:6]]) if diff_lab else ""))

    # ── LE COMPTE DU MOUVEMENT (son § 2 b) ───────────────────────────────────────────────────────────────────────────
    # 1. le gel : liens des lignes tranchees, aujourd'hui contre le protocole
    garde_ = sum(len(gel_l[i] & T[i]["pieces"]) for i in T)
    delie = sum(len(gel_l[i] - T[i]["pieces"]) for i in T)
    relie = sum(len(T[i]["pieces"] - gel_l[i]) for i in T)
    delie_v = sum(len({q for q in gel_l[i] - T[i]["pieces"] if I.nature.get(q) == PC.VRAIE}) for i in T)
    relie_v = sum(len({q for q in T[i]["pieces"] - gel_l[i] if I.nature.get(q) == PC.VRAIE}) for i in T)
    lignes_gel_ch = sum(1 for i in T if gel_l[i] != T[i]["pieces"])
    att_liens = sum(len(gel_l[i]) for i in V if V[i]["verdict"] == "ATTENTE")
    sans_ligne = sum(len(v) for i, v in gel_l.items() if i not in V)
    dire("   GEL : %d liens aujourd'hui = %d des lignes tranchees + %d des lignes en attente (on n'y touche pas) + %d "
         "d'ID absents du Sheet" % (len(I.gel), sum(len(gel_l[i]) for i in T), att_liens, sans_ligne))
    dire("      lignes tranchees : %d liens gardes, %d SE DELIENT (dont %d vraies pieces), %d SE RELIENT (dont %d vraies) ;"
         " %d lignes dont le gel change" % (garde_, delie, delie_v, relie, relie_v, lignes_gel_ch))
    # 2. les dossiers
    avant = {frozenset(v) for v in mA.values()}
    apres = {frozenset(v) for v in mE.values()}
    recoupes = [d for d in avant if d not in apres]
    neufs = [d for d in apres if d not in avant]
    pieces_ch = sum(1 for p_ in chA if mA[chA[p_]] != mE[chE[p_]])
    dire("   DOSSIERS : %d aujourd'hui -> %d ; %d dossiers d'aujourd'hui se recoupent ou se reunissent, %d dossiers "
         "d'arrivee n'existent pas aujourd'hui ; %d pieces changent de compagnie" % (len(avant), len(apres),
                                                                                   len(recoupes), len(neufs), pieces_ch))
    # 3. les etiquettes : par piece, et par ligne (comme l'ecrivain la lirait aujourd'hui : par le gel)
    lab_ch = sum(1 for p_ in lab_img if labE.get(p_) != lab_img[p_])
    dire("   ETIQUETTES DES PIECES : %d pieces changent d'etiquette dans l'app (dont %d vers une etiquette NEUVE)"
         % (lab_ch, sum(1 for p_ in lab_img if labE.get(p_) != lab_img[p_] and str(labE.get(p_)).startswith("NEUVE"))))
    auj = {}
    for i in T:
        ls = {lab_img[q] for q in gel_l[i] if I.nature.get(q) == PC.VRAIE and q in lab_img}
        auj[i] = next(iter(ls)) if len(ls) == 1 else ("PLUSIEURS" if ls else "AUCUNE")
    cat = Counter()
    for i in T:
        n_ = lab_ligne_E[i]
        if auj[i] == n_:
            cat["la meme etiquette qu'aujourd'hui"] += 1
        elif str(n_).startswith("NEUVE"):
            cat["une etiquette NEUVE"] += 1
        elif auj[i] in ("PLUSIEURS", "AUCUNE"):
            cat["une etiquette existante, la ligne n'en avait %s" % ("pas UNE seule" if auj[i] == "PLUSIEURS"
                                                                    else "aucune")] += 1
        else:
            cat["une AUTRE etiquette existante"] += 1
    dire("   ETIQUETTE DE CHAQUE LIGNE TRANCHEE (aujourd'hui par le gel -> a l'arrivee) : "
         + " . ".join("%s %d" % kv for kv in cat.most_common()))
    porteurs_auj = defaultdict(set)
    for i in T:
        if auj[i] not in ("PLUSIEURS", "AUCUNE"):
            porteurs_auj[auj[i]].add(i)
    porteurs_E = defaultdict(set)
    for i in T:
        porteurs_E[lab_ligne_E[i]].add(i)
    changent = sorted(l_ for l_ in porteurs_auj if porteurs_E.get(l_, set()) - porteurs_auj[l_])
    perdent = sorted(l_ for l_ in porteurs_auj if not porteurs_E.get(l_))
    dire("   ETIQUETTES QUI CHANGENT DE LIGNE : %d etiquettes d'aujourd'hui iraient (aussi) a une autre ligne ; %d ne "
         "seraient plus l'etiquette d'aucune ligne tranchee" % (len(changent), len(perdent)))
    # 4. ce que l'etat d'arrivee fait aux lignes EN ATTENTE (on n'y touche pas -- mais leur dossier peut bouger)
    att_bouge = sorted(i for i in V if V[i]["verdict"] == "ATTENTE"
                       and any(q in chA and mA[chA[q]] != mE[chE[q]] for q in gel_l[i]))
    dire("   ⚠ LIGNES EN ATTENTE dont un dossier bouge quand meme (une piece de leur gel change de compagnie) : %d"
         % len(att_bouge))

    # ── LA SORTIE : une ligne par ligne tranchee ─────────────────────────────────────────────────────────────────────
    num_de = {I.pieces[q]["app_dossier_uuid"]: I.pieces[q]["app_dossier_numero"] for q in I.pieces
              if I.pieces[q]["app_dossier_uuid"]}

    def numero(e) -> str:
        """SON MOT (reponses 21, § 2) : « PARLE-MOI EN NUMERO DE DOSSIER [...] Donne-moi LES DEUX. »"""
        if e in num_de:
            return num_de[e] or "?"
        return "NEUF (numero donne par la nuit)" if str(e).startswith("NEUVE") else str(e)
    sortie = P.NOTICE / ("PROTOCOLE_PASSAGE_%d_LA_PORTE_DE_CHAQUE_LIGNE_2026-11-22.csv" % pid)
    with sortie.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id_unique", "ligne_du_sheet", "bien", "porte", "dossiers_aujourdhui", "pieces_de_trop",
                    "regle_G2_la_met_juste", "doublon_hektor", "gel_aujourdhui", "pieces_du_protocole",
                    "numero_aujourdhui_par_le_gel", "etiquette_aujourdhui_par_le_gel", "numero_a_l_arrivee",
                    "etiquette_a_l_arrivee", "mise_de_cote_R7b"])
        for i in sorted(T, key=lambda j: T[j]["num"]):
            d = detail[i]
            w.writerow([i, T[i]["num"], T[i]["biens"][0], porte[i], d["dossiers_aujourdhui"], " | ".join(d["extras_quoi"]),
                        "oui" if i in par_g2 else ("CASSEE PAR G2" if i in casse_g2 else ""),
                        "+".join(d["doublon_hektor"]), " ".join(map(str, sorted(gel_l[i]))),
                        " ".join(map(str, sorted(T[i]["pieces"]))), numero(auj[i]), auj[i], numero(lab_ligne_E[i]),
                        lab_ligne_E[i], " ".join(map(str, d.get("mise_de_cote", [])))])
    res = {"passage": pid, "image": image, "portes": dict(cpt), "extras": dict(nature_extra), "doublons_hektor": dbl,
           "porte_sans_g2": dict(Counter(porte_a.values())), "g2_ailleurs": g2_ailleurs, "figes": figes,
           "g2_met_juste": par_g2, "g2_casse": casse_g2, "faux_E": faux_E, "diff_etiquette": diff_lab, "hors": hors[:50],
           "gel": {"garde": garde_, "delie": delie, "relie": relie, "delie_vraies": delie_v, "relie_vraies": relie_v,
                   "lignes": lignes_gel_ch},
           "dossiers": {"avant": len(avant), "apres": len(apres), "recoupes": len(recoupes), "neufs": len(neufs),
                        "pieces": pieces_ch},
           "etiquettes": {"pieces": lab_ch, "lignes": dict(cat), "changent_de_ligne": changent, "perdent": perdent},
           "attente_qui_bouge": att_bouge, "detail": detail, "mises_de_cote": {
               "pieces": len(MDC), "dossiers": len(groupes_mdc), "lignes": sorted(mdc_de_ligne), "faux": mdc_faux,
               "figes_par_le_chainage": mdc_figees}, "r7a": {i: sorted(v) for i, v in r7a_de_ligne.items()},
           "numero_a_l_arrivee": {i: numero(lab_ligne_E[i]) for i in T}, "etiquette_a_l_arrivee": lab_ligne_E}
    (P.DOSSIER / ("portes_passage_%d.json" % pid)).write_text(json.dumps(res, ensure_ascii=False, indent=1),
                                                             encoding="utf-8")
    dire("-> %s (%.0f s)" % (sortie, time.time() - t0))
    return 0 if not faux_E and not diff_lab and not hors and not mdc_faux else 1


if __name__ == "__main__":
    sys.exit(main())
