#!/usr/bin/env python
"""L'EFFET DES COUPES SUR LA VAGUE 1 -- chantier classeur, ⑬, 20/11/2026. LECTURE SEULE, sur des copies.

LA QUESTION DE FREDERIC (20/11) : « si on faisait ces coupes, COMBIEN DES LIGNES DE LA VAGUE 1 changeraient
d'etiquette ? la meme mesure que pour G2, sur une copie, sans rien ecrire ». Une poignee : il les sort de la
vague 1 comme les 9 de G2. Beaucoup : on coupe AVANT d'ecrire.

⛔ Ce n'est PAS l'outil de scission (« pas de code de scission avant la fin de l'ecriture ») : on SIMULE ce que
   les coupes feraient aux dossiers, puis ce que la pose des etiquettes en ferait, et on compare.

ENTREE : C:\\Hektor\\chantier_classeur_q6_cache\\t7_export_coupes.json, fabrique par
         T6_EXPORT_COUPES=1 python -u phase2/checks/temps6_les_803_lignes_et_ce_qui_les_debloque_2026-11-19.py classer
         + les etats du chainage en cache (chaines_s2 : E jouee ; chaines_s3 : E + les 8 lignes) et la photo.

TROIS MESURES :
  M1  LES COUPES DES GROUPES « MELANGE » (couche 9), TELLES QUE LE SHEET LES PROPOSE : chaque transaction
      attribuee va au dossier de la ligne qui la designe (par sa date, sinon la case vide, sinon le nom) ;
      les transactions SANS ligne, DISPUTEES ou C5 restent ou elles sont. Puis la pose (la copie fidele de
      app_poser_etiquettes_dossier : FUSION -> la plus petite transaction garde ; SCISSION -> le groupe de la
      plus petite transaction garde, les autres recoivent une NEUVE).
  M1b M1 + LES REUNIONS (couche 7 : une ligne seule tient 2 ou 3 dossiers -> on les reunit).
  M2  LA MESURE LA PLUS LARGE, qui ne depend d'AUCUN modele de coupe : pour chaque ligne de la vague 1, le
      Sheet (par la DATE de sa case, colonnes independantes) designe-t-il
        . une piece d'un AUTRE acheteur DANS son dossier (« sortante ») -- si on la sortait et que c'est la
          plus petite transaction du dossier, l'etiquette PARTIRAIT avec elle ;
        . une de SES pieces rangee AILLEURS (« entrante ») -- si on la ramenait et qu'elle est plus petite que
          tout le dossier, SON etiquette gagnerait la fusion.
      Sur deux etats : la REFERENCE (etat 5 : V2 + E + 8 lignes + C5) et MARDI (E + C5, sans V2 ni les 8).

TEMOINS : ma copie de la pose redonne les etiquettes connues (lab3 depuis lab2 et l'etat 3) ; M1 change bien des
  etiquettes dans les groupes coupes (temoin POSITIF) ; une coupe SEMEE dans un dossier de la vague 1 (sa plus
  petite transaction sortie) et une piece SEMEE plus petite ramenee dans un autre sont VUES (temoins INVERSES).

USAGE : python -u phase2/checks/temps7_effet_des_coupes_sur_la_vague_1_2026-11-20.py
SORTIE : notice/TEMPS7_EFFET_DES_COUPES_SUR_LA_VAGUE_1_2026-11-20.md (+ .csv des lignes exposees). Code 0 / 2.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
CACHE = RACINE.parent / "chantier_classeur_q6_cache"
EXPORT = CACHE / "t7_export_coupes.json"
PHOTO = CACHE / "t6_photo.json"
DECISION_B = RACINE / "notice" / "TEMPS6_DECISION_B_LIGNES_REPORTEES_EN_VAGUE_2_PAR_G2_2026-11-20.csv"
SORTIE_MD = RACINE / "notice" / "TEMPS7_EFFET_DES_COUPES_SUR_LA_VAGUE_1_2026-11-20.md"
SORTIE_CSV = SORTIE_MD.with_suffix(".csv")


def etiquettes(lab_prec: dict, ch_new: dict) -> dict:
    """COPIE FIDELE de temps6.etiquettes, elle-meme la copie de app_poser_etiquettes_dossier (lue chez Supabase le
    20/11) : (3) FUSION -- un groupe qui porte plusieurs etiquettes garde celle de sa PLUS PETITE transaction
    etiquetee ; (4) SCISSION -- une etiquette etalee sur plusieurs groupes reste au groupe de la plus petite
    transaction qui la porte, les autres groupes en recoivent une NEUVE."""
    mem = defaultdict(list)
    for a, c in ch_new.items():
        mem[c].append(a)
    lab1 = {}
    for c, ms in mem.items():
        labs = {lab_prec[a] for a in ms if lab_prec.get(a)}
        g_ = (lab_prec[min(a for a in ms if lab_prec.get(a))] if labs else "NEUVE:%s" % c)
        for a in ms:
            lab1[a] = g_
    tete, chaines_du_lab = {}, defaultdict(set)
    for a in sorted(lab1):
        tete.setdefault(lab1[a], ch_new[a])
        chaines_du_lab[lab1[a]].add(ch_new[a])
    return {a: (l_ if len(chaines_du_lab[l_]) == 1 or ch_new[a] == tete[l_] else "NEUVE:%s" % ch_new[a])
            for a, l_ in lab1.items()}


def main() -> int:
    if not EXPORT.exists():
        print("⛔ l'export manque : T6_EXPORT_COUPES=1 ... temps6 ... classer (code 2)")
        return 2
    X = json.loads(EXPORT.read_text(encoding="utf-8"))
    P = json.loads(PHOTO.read_text(encoding="utf-8"))
    TX = {int(a): v for a, v in P["tx"].items()}
    LIG = P["lignes"]
    S2 = {int(a): c for a, c in json.loads((CACHE / "chaines_s2.json").read_text(encoding="utf-8")).items()}
    S3 = {int(a): c for a, c in json.loads((CACHE / "chaines_s3.json").read_text(encoding="utf-8")).items()}
    lab2 = {int(a): l_ for a, l_ in X["lab2"].items()}
    lab3 = {int(a): l_ for a, l_ in X["lab3"].items()}
    with DECISION_B.open(encoding="utf-8-sig") as f:
        B = {r["id_unique"].strip() for r in csv.DictReader(f, delimiter=";")}
    sortie, echecs = [], []

    def dire(t=""):
        print(t, flush=True)
        sortie.append(t)

    dire("photo du Sheet et du registre : %s ; export : %s" % (X["photo_du"],
         datetime.fromtimestamp(EXPORT.stat().st_mtime).isoformat(timespec="seconds")))
    # ── TEMOIN 0 : ma copie de la pose redonne lab3 a partir de lab2 et de l'etat 3 ──
    lab3_moi = etiquettes(lab2, S3)
    ecarts = [a for a in lab3 if lab3_moi.get(a) != lab3[a]]
    dire("TEMOIN 0 -- la copie de la pose redonne les etiquettes de l'etat 3 : %d ecart(s) sur %d (attendu 0)"
         % (len(ecarts), len(lab3)))
    if ecarts:
        echecs.append("temoin 0")

    def vague1(etat: dict) -> list[str]:
        return sorted(i for i, (r, ds, ts) in etat.items() if r == "VAGUE_1" and i not in B)

    etat5, mardi = X["etat5"], X["mardi"]
    v1_ref, v1_mar = vague1(etat5), vague1(mardi)
    dire("VAGUE 1 -- reference (etat 5, sans les 9 de B) : %d lignes ; mardi (E + C5, sans V2 ni les 8) : %d"
         % (len(v1_ref), len(v1_mar)))

    def change(i, etat, lab_avant, lab_apres) -> bool:
        ts = etat[i][2]
        return {lab_apres.get(a) for a in ts} != {lab_avant.get(ts[0])}

    groupes = X["groupes"]
    g9 = {k: g for k, g in groupes.items() if g["verdict"] == 9}
    g7 = {k: g for k, g in groupes.items() if g["verdict"] == 7}
    dire("GROUPES -- melanges (couche 9) : %d groupes, %d lignes ; reunions (couche 7) : %d groupes, %d lignes"
         % (len(g9), sum(len(g["lignes"]) for g in g9.values()), len(g7), sum(len(g["lignes"]) for g in g7.values())))
    dire("   etat de la coupe : %s" % dict(Counter(g["coupe_etat"] for g in g9.values())))

    # ════ M1 : les coupes des melanges ════
    ch1 = dict(S3)
    deplacees = 0
    for k, g in g9.items():
        for a, c in g["proprio"].items():
            a = int(a)
            if a in ch1:
                ch1[a] = "coupe|%s|%s" % (k, c)
                deplacees += 1
    lab_m1 = etiquettes(lab3, ch1)
    v1_m1 = [i for i in v1_ref if change(i, etat5, lab3, lab_m1)]
    lignes_g9 = sorted({i for g in g9.values() for i in g["lignes"] if i in etat5 and etat5[i][2]})
    g9_chg = [i for i in lignes_g9 if {lab_m1.get(a) for a in etat5[i][2]} != {lab3.get(a) for a in etat5[i][2]}]
    neuves = len({l_ for l_ in lab_m1.values() if str(l_).startswith("NEUVE")})
    dire("")
    dire("M1 -- LES COUPES DES %d MELANGES, appliquees TOUTES ensemble (%d transactions attribuees a une ligne)"
         % (len(g9), deplacees))
    dire("   ⭐ LIGNES DE LA VAGUE 1 QUI CHANGERAIENT D'ETIQUETTE : %d sur %d %s"
         % (len(v1_m1), len(v1_ref), v1_m1[:20]))
    dire("   TEMOIN POSITIF -- lignes des melanges dont l'etiquette change : %d sur %d ; etiquettes NEUVES : %d"
         % (len(g9_chg), len(lignes_g9), neuves))
    if not g9_chg or not neuves:
        echecs.append("M1 : la simulation ne coupe rien (temoin positif)")

    # ════ M1b : + les reunions de la couche 7 ════
    ch1b = dict(ch1)
    for k, g in g7.items():
        dos = set(g["dossiers"])
        for a, c in S3.items():
            if c in dos and ch1b.get(a) == c:
                ch1b[a] = "reunion|%s" % k
    lab_m1b = etiquettes(lab3, ch1b)
    v1_m1b = [i for i in v1_ref if change(i, etat5, lab3, lab_m1b)]
    dire("M1b -- M1 + LES REUNIONS de la couche 7 : lignes de la vague 1 qui changeraient : %d %s"
         % (len(v1_m1b), v1_m1b[:20]))

    # ── TEMOINS INVERSES de M1 : une coupe semee DANS un dossier de la vague 1 doit etre VUE ──
    mem3 = defaultdict(set)
    for a, c in S3.items():
        mem3[c].add(a)
    t1 = next(i for i in v1_ref if len(mem3[etat5[i][1][0]]) >= 2)
    t2 = next(i for i in v1_ref if i != t1 and min(mem3[etat5[i][1][0]]) > 1000)
    ch_t = dict(ch1)
    ch_t[min(mem3[etat5[t1][1][0]])] = "temoin|sortie"                   # sa plus petite transaction SORT
    d2 = etat5[t2][1][0]
    petite = next(a for a in sorted(S3) if S3[a] != d2 and a < min(mem3[d2]) and lab3.get(a))
    ch_t[petite] = d2                                                     # une piece plus petite ENTRE
    lab_t = etiquettes(lab3, ch_t)
    vus = [i for i in (t1, t2) if change(i, etat5, lab3, lab_t)]
    dire("TEMOINS INVERSES de M1 -- %s : sa plus petite transaction sortie ; %s : la transaction %d (plus petite) "
         "ramenee -> VUS : %s (attendu les deux)" % (t1, t2, petite, vus))
    if vus != [t1, t2]:
        echecs.append("temoins inverses de M1")

    # ════ M2 : l'exposition de la vague 1 a TOUT ce que le Sheet designe ════
    # ⚠ LU A LA MAIN au 2e passage : une ligne d'un AUTRE bien peut designer une piece par la seule date
    #   (OQQA94LZ, bien 47808 : son compromis 24145 du 12/10/2022 « designe » par 53T2QCFH, une ligne du bien
    #   54974 au meme jour). Une designation ne compte que si la ligne a, PAR LE GEL, une autre transaction du
    #   MEME bien (sa place dans le Sheet est ce bien-la).
    biens_de_ligne = defaultdict(set)
    for i_, a_, _c in P["gel"]:
        if a_ in TX:
            biens_de_ligne[i_].add(TX[a_]["bien"])
    designe_par = defaultdict(set)
    for i, aa in X["ds_date"].items():
        for a in aa:
            if TX.get(a, {}).get("bien") in biens_de_ligne.get(i, set()):
                designe_par[a].add(i)
    ds_date = {i: set(v) for i, v in X["ds_date"].items()}
    lignes_csv = []

    def m2(nom, etat, ch, v1):
        mem = defaultdict(set)
        for a, c in ch.items():
            mem[c].add(a)
        exp_s, exp_e, chg_s, chg_e = [], [], [], []
        for i in v1:
            d = etat[i][1][0]
            ms = mem[d]
            sortantes = sorted(a for a in ms if not TX.get(a, {}).get("classeur") and designe_par.get(a)
                               and i not in designe_par[a])
            # ⚠ LU A LA MAIN au 1er passage : le juge designe parfois, par la meme date, une piece d'un AUTRE bien
            #   (28833 du bien 61599 pour une ligne du bien 61637). Une transaction ne rejoint jamais un dossier
            #   d'un autre bien (le chainage est par bien, le fichier manuel l'exige) : MEME BIEN seulement.
            bien = {TX[a]["bien"] for a in ms if a in TX}
            entrantes = sorted(a for a in ds_date.get(i, set()) if a not in ms and designe_par[a] == {i}
                               and TX.get(a, {}).get("bien") in bien)
            if sortantes:
                exp_s.append(i)
                if min(ms) in sortantes:
                    chg_s.append(i)
            if entrantes:
                exp_e.append(i)
                if min(entrantes) < min(ms):
                    chg_e.append(i)
            if sortantes or entrantes:
                lignes_csv.append({
                    "etat": nom, "id_unique": i, "ligne": LIG.get(i, {}).get("num"), "dossier": d,
                    "plus_petite_du_dossier": min(ms), "transactions_du_dossier": " ".join(map(str, sorted(ms))),
                    "sortantes": " ".join("%d(%s %s -> %s)" % (a, TX[a]["genre"], TX[a]["etat"] or "-",
                                                               "/".join(sorted(designe_par[a]))) for a in sortantes),
                    "entrantes": " ".join("%d(%s %s, dossier %s)" % (a, TX[a]["genre"], TX[a]["etat"] or "-",
                                                                     ch.get(a)) for a in entrantes),
                    "l_etiquette_changerait": "OUI" if (i in chg_s or i in chg_e) else "non"})
        dire("M2 [%s] -- %d lignes de la vague 1" % (nom, len(v1)))
        dire("   une piece d'un AUTRE acheteur dans le dossier (sortante) : %d lignes ; l'etiquette partirait avec "
             "elle : %d %s" % (len(exp_s), len(chg_s), chg_s[:20]))
        dire("   une de SES pieces rangee ailleurs (entrante)             : %d lignes ; son etiquette gagnerait la "
             "fusion : %d %s" % (len(exp_e), len(chg_e), chg_e[:20]))
        return exp_s, exp_e, sorted(set(chg_s) | set(chg_e))

    dire("")
    r_ref = m2("reference", etat5, S3, v1_ref)
    r_mar = m2("mardi", mardi, S2, v1_mar)
    # TEMOIN POSITIF de M2 : la meme detection, sur les lignes des MELANGES, doit voir des pieces croisees
    toutes = sorted(i for i in lignes_g9 if etat5[i][1])
    mem_ = defaultdict(set)
    for a, c in S3.items():
        mem_[c].add(a)
    croisees = [i for i in toutes if any(designe_par.get(a) and i not in designe_par[a]
                                         for d in etat5[i][1] for a in mem_[d] if not TX.get(a, {}).get("classeur"))]
    dire("TEMOIN POSITIF de M2 -- lignes des melanges ou le Sheet voit une piece d'un autre acheteur : %d sur %d"
         % (len(croisees), len(toutes)))
    if not croisees:
        echecs.append("M2 : temoin positif")

    with SORTIE_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        cols = ["etat", "id_unique", "ligne", "dossier", "plus_petite_du_dossier", "transactions_du_dossier",
                "sortantes", "entrantes", "l_etiquette_changerait"]
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(lignes_csv)
    dire("")
    dire("CSV : %s (%d lignes : chaque ligne de vague 1 exposee, avec ses pieces)" % (SORTIE_CSV.name, len(lignes_csv)))
    dire("VERDICT DES TEMOINS : %s" % ("VERTS" if not echecs else "ROUGE -- %s" % echecs))
    SORTIE_MD.write_text("# L'effet des coupes sur la vague 1 (genere par %s, %s)\n\n```\n%s\n```\n"
                         % (Path(__file__).name, datetime.now().isoformat(timespec="minutes"), "\n".join(sortie)),
                         encoding="utf-8")
    return 2 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
