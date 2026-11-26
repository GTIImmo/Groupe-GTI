#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LE CLASSEMENT DE LA COLONNE A SUR LES PIECES DU PROTOCOLE (son mot du 25/11) -- LECTURE SEULE.

    python -X utf8 -u phase2\checks\classer_colonne_a_par_le_protocole_2026-11-25.py

SON MOT : « ALORS ON SUIT LE PROTOCOLE. C'est lui mon juge [...] Refais le classement sur SES pieces, pas sur le gel. »
« VIALLARD (3308P0UX / YRUF0S9H) et PAOLONE (T2GZOY5O / O6R10ZQA) [...] NE TRANCHE PAS SEUL : laisse les quatre lignes
VIDES et nomme-les. »

LE JUGE : le socle du protocole, passage 81 (celui que la vague du 25/11 a realise). Les pieces d'une ligne sont CELLES DU
PROTOCOLE ; le gel (app_classeur_lien) n'est lu que pour dire en quoi il differe. Les cases, la premiere qui concerne la
ligne la range -- les memes que l'ecrivain juge a l'ecriture (juger_paquet, branche sur le protocole le 25/11) :
    A_DEJA_REMPLIE        la colonne A porte deja une valeur : on n'ecrase jamais
    PAS_TRANCHEE          le protocole ne l'a pas tranchee (ATTENTE : son motif) -- dont les 58 « rien a etiqueter »
    C5_SEULE              toutes ses pieces sont des copies du Sheet : aucune ne decide de l'etiquette
    PLUSIEURS_DOSSIERS    ses pieces (effectives) sont dans plusieurs dossiers AUJOURD'HUI
    ARRIVEE_NON_TENUE     l'etiquette d'aujourd'hui de ses pieces n'est pas son etiquette a l'arrivee
    DOUBLE_DE_SAISIE      une AUTRE ligne tranchee porte le meme dossier : la colonne A ne porte une etiquette que sur
                          UNE ligne -- son classeur en faute, A LUI de dire laquelle (les quatre restent vides)
    ETIQUETTE_DEJA_EN_A   son etiquette est deja dans la colonne A, sur une autre ligne
    DECISION_B / DECISION_19   ses decisions du 20/11 (l'ecrivain les refuse tant qu'il ne les leve pas)
    VAGUE_1               rien de tout cela : ecrivable

⛔ N'ECRIT RIEN, ni dans le Sheet ni en base. Il ecrit le classement et sa FICHE DE FABRICATION (l'heure prise AVANT toute
lecture : une vague pendant la mesure le perime ; l'ecrivain refuse un classement plus vieux que la derniere vague).
Sortie : 0 mesure faite . 2 un temoin a echoue.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402

NOTICE = RACINE / "notice"
SOCLE = P.DOSSIER / "socle.sqlite"
#: ⭐ SON MOT DU 26/11 : « Pour 9Q0FHAKK, vas-y dans cet ordre : l'ecrivain au passage 82 (il lit encore le 81, je l'ai vu
#  ligne 95) » -- le passage OFFICIEL 82 (26/11 10:22, socle 5ca7c766, empreinte des verdicts b7dae92e). Le classement du
#  81 reste tel quel dans son fichier du 25/11 ; celui du 82 va dans un fichier NEUF (jamais d'ecrasement).
PASSAGE = 82
PAR_LE_GEL = NOTICE / "CLASSEMENT_COLONNE_A_APRES_LA_VAGUE_2026-11-25.csv"
SORTIE = NOTICE / "CLASSEMENT_COLONNE_A_PAR_LE_PROTOCOLE_2026-11-26_PASSAGE_82.csv"
ORDRE = ["A_DEJA_REMPLIE", "PAS_TRANCHEE", "C5_SEULE", "PLUSIEURS_DOSSIERS", "ARRIVEE_NON_TENUE", "DOUBLE_DE_SAISIE",
         "ETIQUETTE_DEJA_EN_A", "DECISION_B", "DECISION_19", "VAGUE_1"]
#: ⚠ 25/11 : 8NZ6V6XB est une des 19 de sa decision du 20/11 -- l'ecrivain la refusait DEJA (lire_hors_vague) ; le
#  danger reel par le gel etait donc de 4 lignes, pas 5 (mon compte de l'apres-midi, corrige ici et dans le compte rendu)
#  ⭐ 25/11 (soir) : ses decisions du 20/11 LEVEES -> 8NZ6V6XB est ecrivable, avec l'etiquette du PROTOCOLE (pas celle du gel)
CONTRE_PAR_LE_GEL_AU_81 = {"8NZ6V6XB": "VAGUE_1", "ZV3QRSJG": "VAGUE_1", "P252U1JH": "PAS_TRANCHEE",
                           "3THZJOOG": "PAS_TRANCHEE", "3QZ4DAD1": "PAS_TRANCHEE"}
#: ⭐ 26/11, AU PASSAGE 82 -- trois attentes PERIMEES, chacune nommee par ce qui l'a fait bouger (son mot du 26/11 sur le
#  temoin v3 : « Mets-les a jour [...] en nommant chacune par ma decision et sa date. Sinon elles crieront chaque nuit pour
#  rien ») ; les deux autres n'ont pas bouge.
CONTRE_PAR_LE_GEL = {
    "8NZ6V6XB": ("A_DEJA_REMPLIE", "ecrite le 25/11 a 19:40 UTC par la vague1f (app_sheet_ecrit), sur l'etiquette du protocole"),
    "ZV3QRSJG": ("A_DEJA_REMPLIE", "ecrite le 25/11 a 19:40 UTC par la vague1f (app_sheet_ecrit), sur l'etiquette du protocole"),
    "P252U1JH": ("VAGUE_1", "sa decision du 24/11 (4126 + 4128), realisee par le retrait de 4126 de la liste E a la vague "
                            "du 25/11 (09:02)"),
    "3THZJOOG": ("PAS_TRANCHEE", "inchangee"),
    "3QZ4DAD1": ("PAS_TRANCHEE", "inchangee")}
SES_DOUBLES = {"3308P0UX", "YRUF0S9H", "T2GZOY5O", "O6R10ZQA"}


def main() -> int:
    debut = datetime.now(timezone.utc)
    echecs: list[str] = []
    spec = importlib.util.spec_from_file_location("outil_a", ICI / "ecrire_colonne_a_du_sheet_2026-11-20.py")
    outil = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(outil)
    exclus = outil.lire_hors_vague()

    import apparier_classeur as ac
    ac.load_env_file(RACINE / ".env")
    entete, lignes = ac.lire_classeur()
    assert entete[0] == "affair_uuid" and entete[37] == "ID Unique", "l'en-tete du Sheet a bouge"
    kE = entete.index("Etat Actuel")
    col_a, ligne_de, etat, en_double = {}, {}, {}, []
    for num, l in lignes:
        l = [("" if x is None else str(x)) for x in list(l)] + [""] * 38
        i = l[37].strip()
        if not i:
            continue
        if i in ligne_de:
            en_double.append(i)
        ligne_de[i], col_a[i], etat[i] = num, l[0].strip(), l[kE].strip()
    print("Sheet lu (GET) : %d lignes, %d ID Unique, %d case(s) A remplie(s), %d ID en double" % (
        len(lignes), len(ligne_de), sum(1 for v in col_a.values() if v), len(en_double)), flush=True)
    if en_double:
        echecs.append("ID Unique en double : %s" % en_double[:5])

    con = sqlite3.connect("file:%s?mode=ro" % SOCLE.as_posix(), uri=True)
    image = con.execute("select image from passage where id=?", (PASSAGE,)).fetchone()[0]
    V = {}
    for i, v, e, ps, m, mt in con.execute("select id_unique, verdict, etiquette, pieces, motif, motif_texte from verdict "
                                          "where passage=?", (PASSAGE,)):
        V[i] = {"verdict": v, "etiquette": e or "", "pieces": json.loads(ps) if ps else [], "motif": m or "",
                "motif_texte": mt or ""}
    con.close()
    cn, cu = P.pooler()
    cu.execute("select app_affaire_id, app_dossier_uuid::text, app_dossier_numero, transaction_origine, "
               "hektor_affaire_id from public.app_affaire_ledger")
    reg = {int(a): {"uuid": u, "numero": n, "copie": PC.est_copie(int(a), o, h)} for a, u, n, o, h in cu.fetchall()}
    cu.execute("select id_unique, app_affaire_id from public.app_classeur_lien")
    gel = defaultdict(set)
    for i, a in cu.fetchall():
        gel[i].add(int(a))
    cn.rollback()
    cn.close()
    print("protocole : passage %d (image %s), %s ; registre %d pieces ; gel %d lignes" % (
        PASSAGE, image, dict(Counter(v["verdict"] for v in V.values())), len(reg), len(gel)), flush=True)

    def eff(ts):
        k = [a for a in ts if a in reg]
        hk = [a for a in k if not reg[a]["copie"]]
        return hk or k

    def arrivee(v):
        e = v["etiquette"]
        return reg.get(int(e.split(":")[1]), {}).get("uuid") if e.startswith("NEUVE:") else e

    tr = {i: v for i, v in V.items() if v["verdict"] == "TRANCHEE"}
    # TEMOIN 1 : la vague a realise le protocole
    tenue = sum(1 for v in tr.values() if {reg[a]["uuid"] for a in eff(v["pieces"])} == {arrivee(v)})
    print("TEMOIN 1 : etiquette a l'arrivee = etiquette d'aujourd'hui de ses pieces : %d / %d" % (tenue, len(tr)))
    if tenue != len(tr):
        echecs.append("protocole non tenu par le registre : %d / %d" % (tenue, len(tr)))

    lignes_u = defaultdict(set)
    for i, v in tr.items():
        for a in eff(v["pieces"]):
            lignes_u[reg[a]["uuid"]].add(i)
    en_a = defaultdict(set)
    for i, u in col_a.items():
        if u:
            en_a[u].add(i)

    out = {}
    for i in sorted(ligne_de, key=lambda x: ligne_de[x]):
        v = V.get(i)
        pp = sorted(v["pieces"]) if v and v["verdict"] == "TRANCHEE" else []
        us = sorted({reg[a]["uuid"] for a in eff(pp)}, key=str)
        motif, autres = "", []
        if col_a.get(i):
            c = "A_DEJA_REMPLIE"
        elif i in SES_DOUBLES:
            # ⛔ SON MOT DU 26/11 : « les quatre doubles devaient rester vides par decision ». Au 81 la case DOUBLE_DE_SAISIE
            #   les prenait d'elle-meme (deux lignes tranchees sur le meme dossier) ; au 82, R27 met une des deux en attente
            #   et la regle ne les voyait plus -- SEUL le temoin 5 les arretait. Sa decision est desormais une REGLE, avant
            #   tout verdict : ces quatre lignes restent vides, quel que soit ce que le juge en dit.
            c, autres = "DOUBLE_DE_SAISIE", sorted(SES_DOUBLES - {i})
            motif = "sa decision du 25/11 : « laisse les quatre lignes VIDES et nomme-les » (redite le 26/11)"
        elif not v or v["verdict"] != "TRANCHEE":
            c = "PAS_TRANCHEE"
            motif = ("%s : %s" % (v["motif"], v["motif_texte"][:140])) if v else "absente du passage %d" % PASSAGE
        elif all(reg.get(a, {}).get("copie") for a in pp):
            c = "C5_SEULE"
        elif len(us) != 1:
            c = "PLUSIEURS_DOSSIERS"
        elif us[0] != arrivee(v):
            c = "ARRIVEE_NON_TENUE"
        elif lignes_u[us[0]] - {i}:
            c, autres = "DOUBLE_DE_SAISIE", sorted(lignes_u[us[0]] - {i})
        elif en_a.get(us[0], set()) - {i}:
            c, autres = "ETIQUETTE_DEJA_EN_A", sorted(en_a[us[0]] - {i})
        elif i in exclus:
            c, motif = exclus[i][0], exclus[i][1]
        else:
            c = "VAGUE_1"
        out[i] = {"case": c, "pieces": pp, "uuid": us[0] if len(us) == 1 else "", "motif": motif, "autres": autres,
                  "numero": " ".join(sorted({str(reg[a]["numero"]) for a in eff(pp)}))}

    # les temoins
    ecrites = [i for i in out if col_a.get(i)]
    bonnes = [i for i in ecrites if i in tr and col_a[i] == arrivee(tr[i])]
    print("TEMOIN 2 : les %d cases A deja remplies portent l'etiquette du protocole : %d / %d" % (
        len(ecrites), len(bonnes), len(ecrites)))
    if len(bonnes) != len(ecrites):
        echecs.append("case A differente du protocole : %s" % sorted(set(ecrites) - set(bonnes))[:5])
    v1 = [i for i in out if out[i]["case"] == "VAGUE_1"]
    u_v1 = Counter(out[i]["uuid"] for i in v1)
    print("TEMOIN 3 : VAGUE_1 %d lignes, %d etiquettes distinctes, %d deja en A" % (
        len(v1), len(u_v1), sum(1 for u in u_v1 if en_a.get(u))))
    if len(u_v1) != len(v1) or any(en_a.get(u) for u in u_v1):
        echecs.append("VAGUE_1 : une etiquette sur deux lignes ou deja en A")
    t4 = {i: out[i]["case"] for i in CONTRE_PAR_LE_GEL if i in out}
    att4 = {i: c_ for i, (c_, _r) in CONTRE_PAR_LE_GEL.items()}
    print("TEMOIN 4 : les 5 que le gel ecrirait contre le protocole : %s (attendu %s)" % (t4, att4))
    for i, (c_, r_) in CONTRE_PAR_LE_GEL.items():
        if CONTRE_PAR_LE_GEL_AU_81.get(i) != c_:
            print("          %s : %s au 81 -> %s au 82 -- %s" % (i, CONTRE_PAR_LE_GEL_AU_81.get(i), c_, r_))
    if t4 != att4:
        echecs.append("les 5 : %s" % t4)
    t5 = sorted(i for i in out if out[i]["case"] == "DOUBLE_DE_SAISIE")
    print("TEMOIN 5 : ses doubles de saisie, laisses VIDES et nommes : %s (attendu %s)" % (t5, sorted(SES_DOUBLES)))
    if set(t5) != SES_DOUBLES:
        echecs.append("doubles : %s" % t5)
    ecrivables = [i for i in out if out[i]["case"] in ("VAGUE_1", "A_DEJA_REMPLIE", "DECISION_B", "DECISION_19")]
    print("TEMOIN 6 : ecrivables par le protocole (VAGUE_1 + deja ecrites + ses decisions) : %d (mesure de l'apres-midi "
          ": 4 725) ; sans ses decisions : %d (4 697)" % (
              len(ecrivables), sum(1 for i in ecrivables if out[i]["case"] not in ("DECISION_B", "DECISION_19"))))

    # le classement par le gel (le meme jour) contre celui-ci
    gel_c = {}
    with PAR_LE_GEL.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            gel_c[r["id_unique"]] = r
    trans = Counter((gel_c[i]["case_25_11"], out[i]["case"]) for i in out if i in gel_c
                    and gel_c[i]["case_25_11"] != out[i]["case"])
    autre_etiq = [i for i in v1 if i in gel_c and gel_c[i]["etiquette_a_ecrire"] and
                  gel_c[i]["etiquette_a_ecrire"] != out[i]["uuid"]]

    c = Counter(x["case"] for x in out.values())
    print("\n① LES %d LIGNES DU SHEET, rangees sur les pieces du protocole :" % len(out))
    for k in ORDRE:
        if c[k]:
            print("   %-22s %5d" % (k, c[k]))
    print("   %-22s %5d" % ("TOTAL", sum(c.values())))
    print("   PAS_TRANCHEE, par motif : %s" % dict(Counter(V[i]["motif"] if i in V else "ABSENTE" for i in out
                                                            if out[i]["case"] == "PAS_TRANCHEE")))
    print("   VAGUE_1 : %d ventes reglees au Sheet ; %d dont l'etiquette differe de la lecture par le gel %s" % (
        sum(1 for i in v1 if etat.get(i) == "Vente réglée"), len(autre_etiq), autre_etiq))
    print("\n   par rapport au classement PAR LE GEL de ce midi (case -> case) :")
    for (a, b), n in sorted(trans.items(), key=lambda t: -t[1]):
        print("      %-20s -> %-20s %4d" % (a, b, n))
    nouvelles = [i for i in v1 if i in gel_c and gel_c[i]["case_25_11"] != "VAGUE_1"]
    print("   lignes NOUVELLEMENT ecrivables (VAGUE_1 ici, pas par le gel) : %d, dont %d ventes reglees au Sheet" % (
        len(nouvelles), sum(1 for i in nouvelles if etat.get(i) == "Vente réglée")))

    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id_unique", "ligne_du_sheet", "case_aujourd_hui", "etiquette_a_ecrire", "dossier",
                    "pieces_du_protocole", "gel_aujourdhui", "gel_egal_protocole", "case_par_le_gel", "etat_au_sheet",
                    "motif", "autres_lignes"])
        for i in sorted(out, key=lambda x: ligne_de[x]):
            x = out[i]
            w.writerow([i, ligne_de[i], x["case"], x["uuid"] if x["case"] == "VAGUE_1" else "", x["numero"],
                        " ".join(map(str, x["pieces"])), " ".join(map(str, sorted(gel.get(i, set())))),
                        ("OUI" if set(x["pieces"]) == gel.get(i, set()) else "NON") if x["pieces"] else "",
                        gel_c.get(i, {}).get("case_25_11", ""), etat.get(i, ""), x["motif"], " ".join(x["autres"])])
    print("\nCSV : %s" % SORTIE)
    if echecs:
        print("⛔ TEMOIN(S) EN ECHEC : %s (code 2) -- PAS de fiche de fabrication : l'ecrivain le refusera" % echecs)
        return 2
    fiche = SORTIE.with_name(SORTIE.name + ".json")
    fiche.write_text(json.dumps({"fait_le": debut.isoformat(timespec="seconds"),
                                 "sha256": hashlib.sha256(SORTIE.read_bytes()).hexdigest(),
                                 "par": Path(__file__).name, "juge": "protocole, passage %d (image %s)" % (PASSAGE, image),
                                 "lignes": len(out)}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("FICHE DE FABRICATION : %s (fait le %s)" % (fiche, debut.isoformat(timespec="seconds")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
