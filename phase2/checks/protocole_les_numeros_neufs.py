#!/usr/bin/env python3
"""LES NUMEROS NEUFS QUE LA NUIT DONNERA -- ANCIEN -> NEUF, EN CLAIR -- chantier classeur, ㉑bis, 22/11/2026 (soir).

Son mot (reponses au rapport 21 bis, point 1 b) : « AVANT D'ECRIRE, DONNE-MOI LES 63 EN CLAIR : ancien numero -> neuf,
  ma ligne, et le nom. Je veux les relire une fois, pas les decouvrir apres. »

⛔ LECTURE SEULE. Rien en base, rien dans le Sheet, rien chez Hektor. Supabase est lu par le pooler en
   « set transaction read only » (le compteur, les dates decidees, les mandats).

CE QU'IL FAIT. L'etat d'arrivee est le rejeu E du passage (protocole_portes.py, en cache : le VRAI chainage sur la copie
  de l'image, avec le brouillon du protocole). La pose de nuit (K.pose_de_nuit) dit quels groupes recoivent une
  etiquette NEUVE. Pour chacun, ce script refait EXACTEMENT ce que fait la RPC app_poser_etiquettes_dossier, lue chez
  Supabase le 22/11 :
    . l'ANNEE = app_dossier_annee_ouverture(chaine) : la plus petite annee de ses transactions
      (app_dossier_annee_date_transaction : une offre se date sur sa premiere proposition, puis la date decidee, puis la
      colonne date), a defaut l'annee de debut du mandat de l'annonce, a defaut 0 ;
    . le RANG = le compteur de l'annee (app_dossier_numero_compteur.dernier) + son rang parmi les scissions de la meme
      annee, rangees par app_chaine_id (= la plus petite piece du groupe, verifie 11 551 sur 11 551 chez Supabase) ;
    . le NUMERO = D<annee sur 4>-<rang sur 4> (app_dossier_numero_format).
  ⚠ L'HYPOTHESE, DITE : la nuit de la pose ne frappe AUCUN autre numero de la meme annee avant ces scissions (une
    transaction neuve nue, une scission naturelle). Le premier geste de la RPC est la pose des groupes nus : il passe
    AVANT. Le numero reel se relit le lendemain matin dans app_dossier_etiquette_journal.

LE TEMOIN DE L'ANNEE (positif, jamais un zero cru sans lui) : la meme fonction, appliquee aux 11 551 dossiers
  d'aujourd'hui, doit retrouver l'annee ecrite dans leur numero. Les ecarts sont comptes et nommes.

USAGE : python -u phase2/checks/protocole_les_numeros_neufs.py [--passage P]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import coupe_preuve_interne as K  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402
import protocole_classeur as P  # noqa: E402
import protocole_portes as PO  # noqa: E402

DATE_OK = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}")
COL = {"etat": 17, "facture": 26, "acquereur": 27, "vendeur": 29, "ville": 32, "avis_envoye": 35}


def dire(s: str = "") -> None:
    print(s, flush=True)


def entrees(pj) -> list:
    """jsonb_typeof : array -> tel quel ; object -> [objet] ; sinon []."""
    if isinstance(pj, str):
        try:
            pj = json.loads(pj) if pj.strip() else None
        except ValueError:
            pj = None
    if isinstance(pj, list):
        return pj
    if isinstance(pj, dict):
        return [pj]
    return []


def date_valide(d) -> bool:
    return isinstance(d, str) and bool(DATE_OK.match(d)) and not d.startswith("0000")


def annee_transaction(p: dict, convenue: dict) -> str | None:
    """app_dossier_annee_date_transaction, recopiee de Supabase (22/11)."""
    kind = (p.get("kind") or "").lower()
    e = entrees(p.get("propositions_json"))
    if kind == "offre":
        ans = [str(x.get("date"))[:4] for x in e if isinstance(x, dict)
               and str(x.get("type") or "").lower() in ("proposition", "accepte") and date_valide(x.get("date"))]
        if ans:
            return min(ans)
    if p["app_affaire_id"] in convenue:
        return str(convenue[p["app_affaire_id"]])[:4]
    d = p.get("date")
    if date_valide(d) and (kind != "offre" or len(e) == 0):
        return d[:4]
    return None


def annee_ouverture(pieces: list, I, convenue: dict, an_mandat: dict) -> int:
    """app_dossier_annee_ouverture : min des annees de transaction, sinon le mandat de la plus petite annonce, sinon 0."""
    ans = [a for a in (annee_transaction(I.pieces[q], convenue) for q in pieces) if a]
    if ans:
        return int(min(ans))
    annonces = [int(I.pieces[q]["hektor_annonce_id"]) for q in pieces if I.pieces[q]["hektor_annonce_id"] is not None]
    if annonces and an_mandat.get(str(min(annonces))):
        return int(an_mandat[str(min(annonces))])
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--passage", type=int)
    a = ap.parse_args()
    con = P.socle()
    pid = a.passage or con.execute("select max(id) from passage where image is not null").fetchone()[0]
    image = con.execute("select image from passage where id=?", (pid,)).fetchone()[0]
    con.close()
    I = P.Image(P.IMAGES / image)
    PT = json.loads((P.DOSSIER / ("portes_passage_%d.json" % pid)).read_text(encoding="utf-8"))
    AV = json.loads((P.DOSSIER / "avis" / ("avis_contre_passage_%d.json" % pid)).read_text(encoding="utf-8"))
    brouillon = P.DOSSIER / ("brouillon_detachements_protocole_passage_%d.csv" % pid)
    chE, _ = PO.rejeu_en_cache("E", image, brouillon, {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"},
                               False)
    # Supabase, en lecture seule
    cn, cu = P.pooler()
    cu.execute("select annee, dernier from public.app_dossier_numero_compteur")
    compteur = {int(an): int(d) for an, d in cu.fetchall()}
    cu.execute("select app_affaire_id, jour from public.app_affaire_date_convenue")
    convenue = {int(x): j for x, j in cu.fetchall()}
    cu.execute("select hektor_annonce_id, min(case when date_debut ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}' and date_debut "
               "not like '0000%%' then left(date_debut, 4) end) from public.app_mandat group by 1")
    an_mandat = {k: v for k, v in cu.fetchall() if v}
    cu.execute("select count(*), max(id) from public.app_dossier_etiquette_journal")
    j_n, j_max = cu.fetchone()
    # LE TEMOIN DE LA COPIE : la VRAIE fonction de Supabase, sur chaque chaine d'aujourd'hui
    cu.execute("select app_chaine_id, public.app_dossier_annee_ouverture(app_chaine_id) from (select distinct "
               "app_chaine_id from public.app_affaire_ledger where app_chaine_id is not null) x")
    an_sql = {int(c): int(an) for c, an in cu.fetchall()}
    cn.rollback()
    cn.close()
    dire("LES NUMEROS NEUFS -- passage %d, image %s ; compteur lu chez Supabase (%d annees), journal des etiquettes : "
         "%d lignes (dernier id %s)" % (pid, image, len(compteur), j_n, j_max))

    # 1. LE TEMOIN DE L'ANNEE : la fonction, sur les 11 551 dossiers d'aujourd'hui
    lab_img = {q: I.pieces[q]["app_dossier_uuid"] for q in I.pieces}
    num_de = {I.pieces[q]["app_dossier_uuid"]: I.pieces[q]["app_dossier_numero"] for q in I.pieces
              if I.pieces[q]["app_dossier_uuid"]}
    par_lab = defaultdict(list)
    for q, u in lab_img.items():
        par_lab[u].append(q)
    ecart_an = []
    for u, qs in par_lab.items():
        an = annee_ouverture(qs, I, convenue, an_mandat)
        if "D%04d-" % an != num_de[u][:6]:
            ecart_an.append((num_de[u], an, min(qs)))
    dire("   TEMOIN DE L'ANNEE : sur %d dossiers d'aujourd'hui, l'annee recalculee est celle du numero pour %d ; %d "
         "ecart(s)%s" % (len(par_lab), len(par_lab) - len(ecart_an), len(ecart_an),
                         (" -- ex. %s" % ecart_an[:6]) if ecart_an else ""))
    par_ch = defaultdict(list)
    for q in I.pieces:
        par_ch[I.pieces[q]["app_chaine_id"]].append(q)
    copie_faux = sorted(c for c in par_ch if c in an_sql and annee_ouverture(par_ch[c], I, convenue, an_mandat)
                        != an_sql[c])
    absentes = sorted(set(par_ch) ^ set(an_sql))
    dire("   ⭐ TEMOIN DE LA COPIE : ma copie de app_dossier_annee_ouverture contre LA VRAIE, chaine par chaine : %d sur %d "
         "identiques%s%s" % (len(par_ch) - len(copie_faux) - len(set(par_ch) - set(an_sql)), len(par_ch),
                             (" -- ⛔ DIFFERENTES : %s" % copie_faux[:10]) if copie_faux else "",
                             (" ; chaines d'un seul cote (image / Supabase) : %d" % len(absentes)) if absentes else ""))

    # 2. L'ARRIVEE : qui recoit une etiquette neuve, et son numero
    labE = K.pose_de_nuit(lab_img, chE)
    mE = PO.membres(chE)
    neufs = defaultdict(set)                       # etiquette NEUVE -> chaines
    for q, l_ in labE.items():
        if str(l_).startswith("NEUVE"):
            neufs[l_].add(chE[q])
    assert all(len(c) == 1 for c in neufs.values()), "une etiquette neuve sur deux chaines"
    par_an = defaultdict(list)
    for l_, cs in neufs.items():
        c = next(iter(cs))
        par_an[annee_ouverture(sorted(mE[c]), I, convenue, an_mandat)].append((c, l_))
    numero_neuf = {}
    for an, xs in par_an.items():
        for k, (c, l_) in enumerate(sorted(xs), start=1):
            numero_neuf[l_] = "D%04d-%04d" % (an, compteur.get(an, 0) + k)
    dire("   %d dossiers recoivent un numero NEUF, sur %d annee(s) : %s" % (len(numero_neuf), len(par_an), " . ".join(
        "%d : %d (D%04d-%04d a D%04d-%04d)" % (an, len(xs), an, compteur.get(an, 0) + 1, an, compteur.get(an, 0) + len(xs))
        for an, xs in sorted(par_an.items()))))
    # l'ancien numero : celui des pieces dans l'image (a la scission, le groupe neuf vient d'UN ancien dossier)
    ancien_de_neuf = {}
    for l_ in numero_neuf:
        c = next(iter(neufs[l_]))
        olds = {lab_img[q] for q in mE[c] if lab_img.get(q)}
        ancien_de_neuf[l_] = sorted(olds)

    # 3. LES LIGNES : les 63 du temoin (celles qui collaient le 16/11) d'abord, puis toutes les autres lignes au numero neuf
    lab_ligne = PT["etiquette_a_l_arrivee"]
    lignes_du_lab = defaultdict(list)
    for i, l_ in lab_ligne.items():
        lignes_du_lab[l_].append(i)
    t63 = {r[0]: r for r in AV["lignes"] if r[4] == "MEME" and r[5] == "UN NUMERO NEUF"}
    autres_aux_2560 = {r[0] for r in AV["lignes"]}
    sortie_l, sans_numero = [], []
    for i, l_ in sorted(lab_ligne.items()):
        if not str(l_).startswith("NEUVE"):
            continue
        if l_ not in numero_neuf:
            sans_numero.append(i)
            continue
        olds = ancien_de_neuf[l_]
        ancien = " + ".join(num_de[u] for u in olds) or "-"
        # qui GARDE l'ancien numero a l'arrivee : ses lignes, ou une piece sans ligne
        garde = []
        for u in olds:
            ls = sorted(x for x in lignes_du_lab.get(u, []) if x != i)
            if ls:
                garde.append("%s -> ligne(s) %s" % (num_de[u], " ".join(
                    "%s (%s)" % (x, I.sheet["par_id"][x][0]["num"] if x in I.sheet["par_id"] else "?") for x in ls)))
            else:
                qs = sorted(q for q in labE if labE[q] == u)
                garde.append("%s -> aucune de tes lignes : la piece %s le garde (%s)" % (
                    num_de[u], " ".join(map(str, qs[:4])) or "?", ", ".join(sorted({
                        "%s %s" % (I.pieces[q]["kind"], I.pieces[q]["state"]) for q in qs[:4]}))))
        row = I.sheet["par_id"][i][0]["row"] if i in I.sheet["par_id"] else [""] * 38
        sortie_l.append([("1 -- les 63 du temoin" if i in t63 else ("2 -- autre ligne des 2 560" if i in
                          autres_aux_2560 else "3 -- ligne hors des 2 560")),
                         i, I.sheet["par_id"][i][0]["num"] if i in I.sheet["par_id"] else "", ancien,
                         numero_neuf[l_], row[COL["acquereur"]], row[COL["vendeur"]], row[COL["ville"]],
                         row[COL["etat"]], row[COL["facture"]], row[COL["avis_envoye"]], " ; ".join(garde),
                         " ".join(map(str, sorted(mE[next(iter(neufs[l_]))]))), l_])
    sortie_l.sort(key=lambda r: (r[0], r[2] or 0))
    c_sorte = Counter(r[0] for r in sortie_l)
    dire("   LIGNES AU NUMERO NEUF : %d -- %s%s" % (len(sortie_l), " . ".join("%s %d" % kv for kv in sorted(
        c_sorte.items())), (" ; ⛔ SANS NUMERO PREVU : %s" % sans_numero) if sans_numero else ""))
    manquent = sorted(set(t63) - {r[1] for r in sortie_l})
    if manquent:
        dire("   ⛔ des 63 du temoin ne sont pas au numero neuf ici : %s" % manquent)
    sortie = P.NOTICE / ("PROTOCOLE_LES_NUMEROS_NEUFS_ANCIEN_VERS_NEUF_PASSAGE_%d_2026-11-22.csv" % pid)
    with sortie.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["sorte", "id_unique", "ligne_du_sheet", "ancien_numero", "numero_neuf_prevu", "acquereur", "vendeur",
                    "ville", "etat_actuel", "numero_de_facture", "avis_envoye", "qui_garde_l_ancien_numero",
                    "pieces_du_dossier_neuf", "etiquette_simulee"])
        w.writerows(sortie_l)
    dire("-> %s" % sortie)
    (P.DOSSIER / ("numeros_neufs_passage_%d.json" % pid)).write_text(json.dumps(
        {"compteur": compteur, "journal_lignes": j_n, "journal_dernier_id": j_max, "ecarts_annee": ecart_an,
         "copie_differente": copie_faux, "chaines_d_un_seul_cote": absentes,
         "numero_neuf": numero_neuf, "lignes": sortie_l}, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in [r for r in sortie_l if r[0].startswith("1")][:5]:
        dire("   ex. %s (ligne %s) : %s -> %s . %s / %s . %s" % (r[1], r[2], r[3], r[4], r[5][:30], r[6][:30], r[11][:90]))
    return 0 if not manquent and not sans_numero and not copie_faux else 1


if __name__ == "__main__":
    sys.exit(main())
