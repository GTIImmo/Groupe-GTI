#!/usr/bin/env python
"""CE QUI A DEPLACE UNE LIGNE DES 2 560 DEPUIS LE 16/11, ET PAR QUELLE PORTE -- chantier classeur, 22/11 soir.

SON MOT (reponses 21 ter, demande B) : « MES LIGNES 23 ET 535 CHANGERAIENT DE DOSSIER SANS AUCUNE RAISON INSCRITE ...
  pour chacune, par quelle porte le changement passe, et la preuve nommee de chaque piece, comme pour les autres. Un
  changement de dossier sans porte nommee, je ne le signe pas. »

LECTURE SEULE. Pour CHAQUE ligne des 2 560 (app_classeur_avis, C9 du 16/11) dont les pieces du gel ne portent plus,
dans l'image, l'etiquette du 16/11 (« AUTRE » ou « PLUSIEURS » au temoin des avis), et pas seulement pour les deux :
  1. LE JOURNAL des etiquettes (Supabase, lecture seule) : chaque fusion / scission qui a touche l'etiquette du 16/11
     ou celle d'aujourd'hui, avec son numero de ligne, sa date et ses pieces ;
  2. LA CAUSE, nommee par une regle ecrite, jamais devinee :
       . REGLE_E -- la fusion porte sur une piece de la liste de la regle E (sans date visible), allumee le 20/11 a 07:26
         sur son mot (« Oui, allume E ») ; la liste est celle de son compte definitif du 20/11 ;
       . COPIE_C5 -- une part de la fusion, ou de la scission et de ses soeurs, est une COPIE (creation du Sheet, C5
         du 16/11) ;
       . AUCUN_DEPLACEMENT -- aucun evenement : le gel relie la ligne a plusieurs dossiers depuis la pose du 12/11 ;
       . sinon A_EXPLIQUER (jamais un vert) ;
  3. LE TEMOIN C5 : le chainage de la nuit rejoue sur une COPIE de l'image SANS les 190 copies (« une creation du Sheet
     ne decide jamais », regle C5 du 19/11). Une separation qui disparait sans les copies ne tient que par une copie :
     ce n'est PAS une porte qui survit au recalcul ;
  4. LE PROTOCOLE : le verdict, la porte et la preuve nommee de chaque piece (le passage).

USAGE : python -u phase2/checks/protocole_ce_qui_a_deplace_les_2560_depuis_le_16_11.py [--passage N]
         (le rejeu sans les copies se garde en cache sous une cle qui porte l'image, le module et les deux fichiers)
CODES : 0 chaque deplacement a sa cause nommee . 1 au moins un A_EXPLIQUER, ou une separation tenue par une copie
        (nommee) . 2 pas pu lire
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import io
import json
import os
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import piece_copie_ou_vraie as PC  # noqa: E402
import protocole_classeur as P  # noqa: E402
import protocole_portes as PO  # noqa: E402

REGLE_E_CSV = P.NOTICE / "CHANTIER_CLASSEUR_REGLE_E_COMPTE_DEFINITIF_2026-11-20.csv"


def dire(s: str = "") -> None:
    print(s, flush=True)


def rejeu_sans_copies(image: str, I) -> dict:
    """Le chainage de la nuit (rejeu A : G2 et l'outil eteints) sur une copie EN MEMOIRE de l'image, les copies C5
    retirees -- en cache (cle : image, module, rattachements, detachements, liste des copies)."""
    copies = sorted(a for a, n in I.nature.items() if n == PC.COPIE)
    h = hashlib.md5()
    for p_ in (PO.MODULE, PO.FICHIER_RAT_PROD, PO.FICHIER_DET_PROD):
        h.update(p_.read_bytes().replace(b"\r\n", b"\n"))
    h.update(json.dumps([PO.ETEINTS, copies], sort_keys=True).encode())
    f = P.DOSSIER / ("rejeu_%s_A_SANS_COPIES_%s.json" % (image, h.hexdigest()[:12]))
    if f.exists():
        d = json.loads(f.read_text(encoding="utf-8"))
        return {int(k): v for k, v in d["ch"].items()}
    t0 = time.time()
    mod = PO.charger("sans_copies", PO.FICHIER_DET_PROD)
    gardes = {k: os.environ.get(k) for k in PO.ETEINTS}
    os.environ.update(PO.ETEINTS)
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


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--passage", type=int)
    a = ap.parse_args()
    con = P.socle()
    pid = a.passage or con.execute("select max(id) from passage where image is not null").fetchone()[0]
    image = con.execute("select image from passage where id=?", (pid,)).fetchone()[0]
    V = {i: {"num": n, "verdict": v, "etiquette": e, "pieces": json.loads(ps) if ps else [],
             "preuves": json.loads(pr) if pr else [], "motif": m}
         for i, n, v, e, ps, pr, m in con.execute("select id_unique, num, verdict, etiquette, pieces, preuves, motif "
                                                  "from verdict where passage=?", (pid,))}
    con.close()
    AV = json.loads((P.DOSSIER / "avis" / ("avis_contre_passage_%d.json" % pid)).read_text(encoding="utf-8"))
    PT = json.loads((P.DOSSIER / ("portes_passage_%d.json" % pid)).read_text(encoding="utf-8"))
    porte = {i: d["porte"] for i, d in PT.get("detail", {}).items()}
    lignes = [r for r in AV["lignes"] if r[4] != "MEME"]
    I = P.Image(P.IMAGES / image)
    lab = {q: I.pieces[q]["app_dossier_uuid"] for q in I.pieces}
    num_de = {u: I.pieces[q]["app_dossier_numero"] for q, u in lab.items() if u}
    with REGLE_E_CSV.open(encoding="utf-8-sig", newline="") as f:
        regle_e = {int(r["transaction_sans_date"]) for r in csv.DictReader(f)}
    dire("CE QUI A DEPLACE LES LIGNES DES 2 560 DEPUIS LE 16/11 -- passage %d, image %s : %d lignes dont les pieces ne "
         "portent plus l'etiquette du 16/11 (regle E : %d pieces dans son compte du 20/11)" % (
             pid, image, len(lignes), len(regle_e)))
    # 1. le journal, en lecture seule
    uuids = set()
    for r in lignes:
        uuids.add(r[3])
        uuids |= {lab[int(g["piece"])] for g in I.gel_par_ligne.get(r[0], []) if lab.get(int(g["piece"]))}
    try:
        cn, cu = P.pooler()
        cu.execute("select id, to_char(quand at time zone 'Europe/Paris', 'DD/MM HH24:MI'), evenement, "
                   "dossier_uuid::text, dossier_numero, autre_uuid::text, app_chaine_id, transactions "
                   "from public.app_dossier_etiquette_journal where evenement in ('fusion', 'scission') and "
                   "(dossier_uuid::text = any(%s) or autre_uuid::text = any(%s)) order by id",
                   (sorted(uuids), sorted(uuids)))
        J = cu.fetchall()
        cn.rollback()
        cn.close()
    except Exception as e:  # noqa: BLE001
        dire("⛔ le journal n'a pas pu etre lu (%s) -- code 2" % str(e).splitlines()[0][:160])
        return 2
    ev_de = defaultdict(list)
    for e in J:
        for u in (e[3], e[5]):
            ev_de[u].append(e)
    # 2. le temoin C5 : le chainage sans les copies
    chA, _ = PO.rejeu_en_cache("A", image, PO.FICHIER_DET_PROD, PO.ETEINTS, False)
    ch0 = rejeu_sans_copies(image, I)
    bouge0 = sorted(q for q in ch0 if ch0[q] != chA.get(q))
    m0 = PO.membres(ch0)
    dire("   TEMOIN C5 -- sans les copies, la nuit met %d piece(s) dans un autre dossier : %s" % (
        len(bouge0), " ".join("%d (%s->%s)" % (q, chA[q], ch0[q]) for q in bouge0)))
    sortie_l, a_expliquer, tenues = [], [], []
    for r in sorted(lignes, key=lambda r: r[1] or 0):
        i = r[0]
        pieces = sorted({int(g["piece"]) for g in I.gel_par_ligne.get(i, [])})
        evs = {e[0]: e for u in {r[3]} | {lab.get(q) for q in pieces} if u for e in ev_de.get(u, [])}
        causes = []
        for e in sorted(evs.values()):
            parts = set(e[7] or []) | ({e[6]} if e[6] else set())
            # une scission se lit avec SES soeurs (meme instant, meme ancien dossier) : la part qui est une copie
            #   peut etre la soeur, pas la part de la ligne (ligne 535 : 34373 = 1875 1876 1878, 34374 = la copie 1001563)
            soeurs = set()
            if e[2] == "scission":
                for e2 in J:
                    if e2[2] == "scission" and e2[1] == e[1] and e2[3] == e[3]:
                        soeurs |= set(e2[7] or [])
            if e[2] == "fusion" and (parts & regle_e or (e[6] in regle_e)):
                c = "REGLE_E"
            elif any(I.nature.get(q) == PC.COPIE for q in parts | soeurs):
                c = "COPIE_C5"
            else:
                c = "A_EXPLIQUER"
            causes.append((e, c))
        # la cause de la ligne est celle des evenements qui touchent SES pieces ; sans aucun evenement, rien n'a bouge
        recentes = [(e, c) for e, c in causes if set(e[7] or []) & set(pieces)] or causes
        if not causes and r[4] == "PLUSIEURS":
            cause = "AUCUN_DEPLACEMENT"        # le gel la relie a plusieurs dossiers depuis la pose du 12/11
        else:
            cause = recentes[-1][1] if recentes else "A_EXPLIQUER"
        if any(c == "COPIE_C5" for _e, c in recentes):
            cause = "COPIE_C5"
        tenue = sorted(q for q in pieces if q in bouge0)
        if tenue:
            tenues.append(i)
        if cause == "A_EXPLIQUER":
            a_expliquer.append(i)
        v = V.get(i, {})
        auj = sorted({num_de.get(lab.get(q), "-") for q in pieces})
        sortie_l.append([i, r[1], r[2], " + ".join(auj), r[5], r[6], porte.get(i, "") or "-", cause,
                         " ; ".join("%s %s %s %s [%s]" % (e[0], e[1], e[2], e[4], " ".join(map(str, e[7] or [])))
                                    for e, _c in causes),
                         ("SANS LES COPIES, la nuit refait le dossier de %s" % " ".join(
                             "%d->%d" % (q, ch0[q]) for q in tenue)) if tenue else "tient sans les copies",
                         "%s%s" % (v.get("verdict", ""), (" (%s)" % v["motif"]) if v.get("motif") else ""),
                         " | ".join(v.get("preuves", []))])
    for s in sortie_l:
        dire("   ligne %-5s %s : 16/11 %s -> aujourd'hui %s ; %s ; porte %s ; CAUSE %s%s" % (
            s[1], s[0], s[2], s[3], s[4], s[6], s[7], (" ; ⚠ %s" % s[9]) if s[9] != "tient sans les copies" else ""))
    sortie = P.NOTICE / ("PROTOCOLE_CE_QUI_A_DEPLACE_LES_2560_DEPUIS_LE_16_11_PASSAGE_%d_2026-11-22.csv" % pid)
    with sortie.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id_unique", "ligne_du_sheet", "numero_du_16_11", "numero_aujourdhui", "le_protocole_a_l_arrivee",
                    "numero_a_l_arrivee", "porte_du_protocole", "cause", "le_journal_des_etiquettes",
                    "temoin_c5_sans_les_copies", "verdict", "preuve_nommee_de_chaque_piece"])
        w.writerows(sortie_l)
    dire("   CAUSES : %s" % " . ".join("%s %d" % (c, sum(1 for s in sortie_l if s[7] == c))
                                       for c in ("REGLE_E", "COPIE_C5", "AUCUN_DEPLACEMENT", "A_EXPLIQUER")))
    dire("   ⚠ SEPARATIONS TENUES PAR UNE COPIE (pas une porte) : %d ligne(s) des 2 560 -- %s" % (
        len(tenues), " ".join(tenues) or "aucune"))
    dire("   -> %s" % sortie)
    return 1 if (a_expliquer or tenues) else 0


if __name__ == "__main__":
    sys.exit(main())
