"""R26 A BLANC (24/11, son 3e mot) : « LA COUPE EMPORTE AVEC LA LIGNE LA VENTE QUI N'APPARTIENT QU'A ELLE ».

SON MOT : « Tu mesures R26 AVANT tout le reste [...] C'EST LA QU'IL Y A DE L'ARGENT. Cinq negociateurs ne seraient pas payes
sur des ventes bien reelles -- 21662, 12182, 28147, 7126, 16019. [...] Mesure-la, avec : . son TEMOIN POSITIF : les 5 ventes
rejoignent leur ligne ; . son TEMOIN INVERSE : combien d'AUTRES ventes bougent, que je n'ai pas demandees. ⛔ Si le chiffre
n'est pas exactement 5, tu t'arretes et tu me nommes les autres ; . et le rejeu exact : 0 recul, 0 etiquette deplacee sur du
deja-rendu. »

LA CAUSE (mesuree le 24/11, temps 2) : la « coupe neuve » de la vague ecrit au brouillon un morceau = les pieces PROUVEES de la
ligne (+ R7a : ses pieces a part deja dans son dossier) ; la vente que le protocole ne prouve pas par sa date (date Hektor
fausse d'un an ou d'un mois) n'est pas dans le morceau -> elle reste dans le reste de l'ancien dossier, sans ligne, sans part.

R26, TELLE QUE MESUREE ICI (elle ne change AUCUN verdict, aucune piece, aucune etiquette du protocole : elle change le
MORCEAU que la vague coupe) -- pour une ligne tranchee :
  . ses pieces du protocole ne portent AUCUNE vraie vente ;
  . le dossier d'aujourd'hui de ses pieces (rejeu A, la nuit telle qu'elle tourne) porte UNE SEULE vraie vente hors d'elles ;
  . cette vente est a ELLE SEULE au gel (aucune autre ligne ne la lie) et AUCUNE ligne tranchee ne la tient ;
  -> son morceau l'EMPORTE (et la ligne est jugee juste avec elle).

LECTURE SEULE. protocole_portes.py N'EST PAS TOUCHE : on en execute une COPIE en memoire, retouchee par trois ancres ; le socle,
les caches de rejeu et les fichiers du passage sont COPIES dans un dossier a part (protocole_a_blanc_r26) : le vrai passage 79
et ses fichiers ne bougent pas.

USAGE : python -u -X utf8 phase2/checks/protocole_r26_vente_emportee_a_blanc_2026-11-24.py [--passage 79]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import types
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import coupe_preuve_interne as K  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402
import protocole_classeur as P  # noqa: E402

LES_CINQ = {21662: "8BJKJ6XP", 12182: "8BUW2ZVH", 28147: "HPNJ32UM", 7126: "WJ8NY16C", 16019: "ZYVO6KK1"}
VRAI_SOCLE, VRAI_DOSSIER, VRAI_NOTICE = P.SOCLE, P.DOSSIER, P.NOTICE
AB = VRAI_DOSSIER.parent / "protocole_a_blanc_r26"

R26 = '''
    # ⭐ R26 (A BLANC, proposee le 24/11) : LA COUPE EMPORTE AVEC LA LIGNE LA VENTE QUI N'APPARTIENT QU'A ELLE
    r26_de_ligne = defaultdict(set)
    for i, x in T.items():
        M_ = x["pieces"]
        if any(I.pieces[q]["kind"] == "vente" and I.nature.get(q) == PC.VRAIE for q in M_):
            continue
        U_ = set().union(*(mA[chA[q]] for q in M_))
        vs_ = [q for q in U_ - M_ if I.pieces[q]["kind"] == "vente" and I.nature.get(q) == PC.VRAIE]
        if len(vs_) == 1 and gel_p.get(vs_[0], set()) == {i} and not tenue_par.get(vs_[0]):
            r26_de_ligne[i].add(vs_[0])
    dire("   R26 (A BLANC) : %d ligne(s) dont la vente non prouvee n'appartient qu'a elle : %s" % (
        len(r26_de_ligne), " ".join("%s:%s(%s)" % (i, "+".join(map(str, sorted(v))), porte[i])
                                    for i, v in sorted(r26_de_ligne.items()))))
'''


def portes_r26() -> types.ModuleType:
    src = (Path(__file__).resolve().parent / "protocole_portes.py").read_text(encoding="utf-8")
    ancres = (
        # 1. la regle, juste apres R7a (elle a besoin de porte, tenue_par, gel_p, chA, mA)
        ('    dire("   R14 : %d ligne(s) gardent dans leur dossier la trace supprimee',
         R26 + '    dire("   R14 : %d ligne(s) gardent dans leur dossier la trace supprimee'),
        # 2. la ligne est juste AVEC sa vente emportee
        ('        M, N = T[i]["pieces"], neutres_de(T[i]["preuves"]) | TRACES.get(i, set())\n'
         '        Cs = {ch[p_] for p_ in M}',
         '        M, N = T[i]["pieces"], neutres_de(T[i]["preuves"]) | TRACES.get(i, set()) | r26_de_ligne.get(i, set())\n'
         '        Cs = {ch[p_] for p_ in M}'),
        # 3. le morceau l'emporte
        ('        k_ = frozenset(T[i]["pieces"]) | frozenset(r7a_de_ligne.get(i, set()))',
         '        k_ = frozenset(T[i]["pieces"]) | frozenset(r7a_de_ligne.get(i, set())) | frozenset(r26_de_ligne.get(i, set()))'),
        # 4. la trace dans la sortie
        ('"r7a": {i: sorted(v) for i, v in r7a_de_ligne.items()},',
         '"r7a": {i: sorted(v) for i, v in r7a_de_ligne.items()}, "r26": {i: sorted(v) for i, v in r26_de_ligne.items()},'),
    )
    for avant, apres in ancres:
        if src.count(avant) != 1:
            raise SystemExit("⛔ protocole_portes.py a change : ancre %r (%d)" % (avant[:70], src.count(avant)))
        src = src.replace(avant, apres)
    m = types.ModuleType("portes_r26")
    m.__file__ = str(Path(__file__).resolve().parent / "protocole_portes.py")
    exec(compile(src, "portes_r26 (protocole_portes.py + R26, a blanc)", "exec"), m.__dict__)
    return m


def dire(s: str = "") -> None:
    print(s, flush=True)


def membres(ch: dict) -> dict:
    m = defaultdict(set)
    for a, c in ch.items():
        m[c].add(a)
    return m


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--passage", type=int, default=79)
    a = ap.parse_args()
    pid = a.passage
    t0 = time.time()
    AB.mkdir(parents=True, exist_ok=True)
    con = P.socle()
    image, version = con.execute("select image, version from passage where id=?", (pid,)).fetchone()
    V = {}
    for i, num, v, e, ps in con.execute("select id_unique, num, verdict, etiquette, pieces from verdict where passage=?",
                                        (pid,)):
        V[i] = {"num": num, "verdict": v, "etiquette": e, "pieces": set(json.loads(ps)) if ps else set()}
    con.close()
    T = {i for i in V if V[i]["verdict"] == "TRANCHEE"}
    dire("R26 A BLANC -- passage %d (%s), image %s" % (pid, version, image))
    # les copies : le socle, le fichier des mises de cote du passage, et les caches de rejeu (memes cles -> reutilises)
    shutil.copyfile(VRAI_SOCLE, AB / "socle.sqlite")
    shutil.copyfile(VRAI_DOSSIER / ("mises_de_cote_passage_%d.json" % pid), AB / ("mises_de_cote_passage_%d.json" % pid))
    for f in VRAI_DOSSIER.glob("rejeu_%s_*.json" % image):
        if "_E_" not in f.name and not (AB / f.name).exists():
            shutil.copyfile(f, AB / f.name)
    import protocole_portes as PP
    brouillon0 = VRAI_DOSSIER / ("brouillon_detachements_protocole_passage_%d.csv" % pid)
    chE0, _r = PP.rejeu_en_cache("E", image, brouillon0, {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"},
                                 False)
    pt0 = json.loads((VRAI_DOSSIER / ("portes_passage_%d.json" % pid)).read_text(encoding="utf-8"))
    P.DOSSIER, P.SOCLE, P.NOTICE = AB, AB / "socle.sqlite", AB
    PA = portes_r26()
    for args in (["--passage", str(pid), "--rejeu", "E"], ["--passage", str(pid)]):
        sys.argv = ["portes_r26"] + args
        dire()
        dire("=" * 30 + " protocole_portes (copie + R26) %s " % " ".join(args) + "=" * 30)
        rc = PA.main()
    brouillon1 = AB / ("brouillon_detachements_protocole_passage_%d.csv" % pid)
    chE1, resE1 = PA.rejeu_en_cache("E", image, brouillon1, {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"},
                                    False)
    pt1 = json.loads((AB / ("portes_passage_%d.json" % pid)).read_text(encoding="utf-8"))
    P.DOSSIER, P.SOCLE, P.NOTICE = VRAI_DOSSIER, VRAI_SOCLE, VRAI_NOTICE

    I = P.Image(P.IMAGES / image)
    PI = I.pieces
    lab_img = {q: PI[q]["app_dossier_uuid"] for q in PI}
    num_de = {PI[q]["app_dossier_uuid"]: PI[q]["app_dossier_numero"] for q in PI if PI[q]["app_dossier_uuid"]}

    def numero(e):
        return num_de.get(e) or ("NEUF" if str(e).startswith("NEUVE") else str(e))
    mE0, mE1 = membres(chE0), membres(chE1)
    labE0, labE1 = K.pose_de_nuit(lab_img, chE0), K.pose_de_nuit(lab_img, chE1)
    tient = defaultdict(set)
    for i in T:
        for q in V[i]["pieces"]:
            tient[q].add(i)
    b0 = set(brouillon0.read_text(encoding="utf-8").splitlines()[2:])
    b1 = set(brouillon1.read_text(encoding="utf-8").splitlines()[2:])
    dire()
    dire("=" * 100)
    dire("LE BROUILLON DE LA VAGUE : %d morceaux (reference %d) ; %d morceaux changent :" % (len(b1), len(b0), len(b1 - b0)))
    for l_ in sorted(b1 - b0):
        dire("   + %s" % l_)
    for l_ in sorted(b0 - b1):
        dire("   - %s" % l_)
    r26 = {i: set(v) for i, v in pt1.get("r26", {}).items()}
    dire("R26 designe %d ligne(s) ; par porte : %s" % (len(r26), dict(Counter(pt1["detail"][i]["porte"] for i in r26))))

    # ── LE TEMOIN POSITIF : les 5 ventes rejoignent leur ligne ────────────────────────────────────────────────────────
    dire()
    dire("⭐ LE TEMOIN POSITIF : les 5 ventes rejoignent-elles le dossier de leur ligne a l'arrivee ?")
    ok5 = 0
    for v, L in sorted(LES_CINQ.items()):
        M = V[L]["pieces"]
        avant = chE0.get(v) in {chE0.get(q) for q in M}
        apres = chE1.get(v) in {chE1.get(q) for q in M}
        ok5 += apres
        dire("   %s vente %d : reference %s ; avec R26 %s -- dossier d'arrivee %s (%s), la ligne %s (%s)" % (
            L, v, "AVEC sa ligne" if avant else "laissee DERRIERE", "AVEC sa ligne" if apres else "⛔ toujours derriere",
            sorted(mE1[chE1[v]]), numero(labE1[v]), sorted(M), "/".join(sorted({numero(labE1[q]) for q in M}))))
    dire("   -> %d / 5" % ok5)

    # ── LE TEMOIN INVERSE : ce qui bouge d'AUTRE, contre le rejeu E de la reference ──────────────────────────────────
    dire()
    dire("⛔ LE TEMOIN INVERSE : tout ce qui change a l'arrivee contre le rejeu E du passage %d" % pid)
    comp = sorted(q for q in chE0 if mE0[chE0[q]] != mE1[chE1[q]])
    ventes_bougent = sorted(q for q in comp if PI.get(q, {}).get("kind") == "vente"
                            and (mE0[chE0[q]] - {q}) != (mE1[chE1[q]] - {q}) and
                            not ({x for x in mE1[chE1[q]]} >= {x for x in mE0[chE0[q]]} and q in LES_CINQ))
    vb = sorted(q for q in comp if PI.get(q, {}).get("kind") == "vente")
    dire("   %d piece(s) changent de compagnie ; dont VENTES : %d %s" % (len(comp), len(vb), vb))
    autres_ventes = sorted(set(vb) - set(LES_CINQ))
    dire("   ⛔ VENTES QUI BOUGENT HORS DES 5 : %d %s" % (len(autres_ventes), autres_ventes))
    for q in comp:
        dire("      %d %-9s %-10s : %s (%s) -> %s (%s) ; tenue par %s" % (
            q, PI[q]["kind"], PI[q]["state"] or "", sorted(mE0[chE0[q]]), numero(labE0[q]), sorted(mE1[chE1[q]]),
            numero(labE1[q]), "+".join(sorted(tient.get(q, []))) or "personne"))
    lab_ch = sorted(q for q in labE0 if labE0[q] != labE1.get(q))
    dire("   %d piece(s) changent d'etiquette : %s" % (len(lab_ch), " ".join("%d %s->%s" % (q, numero(labE0[q]),
                                                                                    numero(labE1[q])) for q in lab_ch)))
    deja = sorted(q for q in lab_ch if not str(labE0[q]).startswith("NEUVE"))
    dire("   ⛔ ETIQUETTE DEJA RENDUE (non NEUVE) qui change : %d %s" % (len(deja), [
        (q, numero(labE0[q]), numero(labE1[q])) for q in deja]))

    # ── LE REJEU EXACT : 0 recul ─────────────────────────────────────────────────────────────────────────────────────
    dire()
    dire("⭐ LE REJEU EXACT (protocole_portes, copie + R26, contre la reference) :")
    for k in ("faux_E", "diff_etiquette", "hors"):
        dire("   %-15s reference %d ; avec R26 %d %s" % (k, len(pt0[k]), len(pt1[k]), pt1[k][:10] if pt1[k] else ""))
    dire("   R7b faux : reference %d ; avec R26 %d" % (len(pt0["mises_de_cote"]["faux"]), len(pt1["mises_de_cote"]["faux"])))
    recul = sorted(i for i in T if pt0["etiquette_a_l_arrivee"].get(i) != pt1["etiquette_a_l_arrivee"].get(i))
    dire("   lignes dont l'etiquette d'arrivee change : %d %s" % (len(recul), recul[:20]))
    dire("   portes : reference %s" % pt0["portes"])
    dire("            avec R26  %s" % pt1["portes"])
    dire("   attente qui bouge : reference %d ; avec R26 %d" % (len(pt0["attente_qui_bouge"]), len(pt1["attente_qui_bouge"])))
    dire("   code de sortie de la copie : %s (0 = juste, etiquettes, hors, R7b) ; %.0f s" % (rc, time.time() - t0))
    (AB / "r26_a_blanc.json").write_text(json.dumps({
        "passage": pid, "image": image, "r26": {i: sorted(v) for i, v in r26.items()}, "positif": ok5,
        "pieces_qui_changent": comp, "ventes_qui_bougent": vb, "autres_ventes": autres_ventes, "etiquettes": lab_ch,
        "etiquettes_deja_rendues": deja, "faux_E": pt1["faux_E"], "diff_etiquette": pt1["diff_etiquette"],
        "hors": pt1["hors"], "recul": recul, "brouillon_plus": sorted(b1 - b0), "brouillon_moins": sorted(b0 - b1)},
        ensure_ascii=False, indent=1), encoding="utf-8")
    dire("-> %s" % (AB / "r26_a_blanc.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
