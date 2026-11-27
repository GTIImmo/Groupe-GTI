"""SON ② DU 24/11 (« MOT_DU_24_11_MES_QUATRE_REPONSES ») -- RETIRER 4126 ET 21520 DES EXCLUSIONS DE LA REGLE E, A BLANC.

« ⛔ MAIS C'EST UN GESTE SUR LE CODE DE LA NUIT. Donc : mesure a blanc d'abord, tu me rends le resultat, et je dis
  « vas-y » ou non. . combien de lignes se debloquent (attendu : P252U1JH et d2108609) ; . ⛔ et surtout : combien
  d'AUTRES lignes bougent, que je n'ai pas demandees. Si le chiffre n'est pas exactement 2, tu t'arretes et tu me nommes
  les autres. »

LECTURE SEULE. Le module de nuit (phase2/sync/affaire_ledger.py) N'EST PAS TOUCHE : on en fait une COPIE hors du depot
dont le dictionnaire EXCLUES_DE_LA_REGLE_E perd ses deux entrees (4126, 21520), par son arbre de syntaxe. Le socle du
protocole est COPIE lui aussi : le passage a blanc s'ecrit dans la copie, jamais dans le vrai socle.

TROIS MESURES, contre le passage de reference (le dernier du vrai socle) :
  A  LA NUIT TELLE QU'ELLE TOURNE (G2 et l'outil de coupe ETEINTS -- l'interrupteur APP_CHAINAGE_DETACHEMENTS reste
     eteint tant qu'A2 n'est pas corrige, son mot) : le module retouche contre le module de production, sur l'image ->
     les pieces qui changent de dossier, les lignes que ca touche, les etiquettes qui bougent.
  P  LE PROTOCOLE : le passage a blanc (copie du socle) contre le passage de reference -> les verdicts qui changent.
  E  LA VAGUE (l'outil de coupe ALLUME + le brouillon du passage a blanc) contre le rejeu E du passage de reference ->
     les lignes dont le dossier ou l'etiquette d'arrivee change ; et les lignes en attente.

Sortie : sa console, et AB / retrait_e_a_blanc.json.
"""
from __future__ import annotations

import ast
import json
import shutil
import sqlite3
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

A_RETIRER = (4126, 21520)
ATTENDUES = {"P252U1JH", "d2108609"}
VRAI_SOCLE = P.SOCLE
VRAI_DOSSIER = P.DOSSIER
AB = VRAI_DOSSIER.parent / "protocole_a_blanc_retrait_e"


def dire(s: str = "") -> None:
    print(s, flush=True)


def module_retouche() -> Path:
    """La copie du module de nuit, ses deux exclusions retirees -- par l'arbre de syntaxe (lignes exactes de chaque cle
    et de sa valeur), et relue pour prouver qu'il ne manque QUE ces deux-la."""
    src = (RACINE / "phase2" / "sync" / "affaire_ledger.py").read_text(encoding="utf-8")
    arbre = ast.parse(src)
    noeud = next(n for n in arbre.body if isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") ==
                 "EXCLUES_DE_LA_REGLE_E")
    lignes = src.split("\n")
    a_effacer = set()
    for k, v in zip(noeud.value.keys, noeud.value.values):
        if ast.literal_eval(k) in A_RETIRER:
            a_effacer |= set(range(k.lineno - 1, v.end_lineno))
    neuf = "\n".join(l_ for n, l_ in enumerate(lignes) if n not in a_effacer)
    avant = ast.literal_eval(noeud.value)
    apres = next(ast.literal_eval(n.value) for n in ast.parse(neuf).body if isinstance(n, ast.AnnAssign)
                 and getattr(n.target, "id", "") == "EXCLUES_DE_LA_REGLE_E")
    if set(avant) - set(apres) != set(A_RETIRER) or any(apres[k] != avant[k] for k in apres):
        raise SystemExit("⛔ la retouche ne retire pas exactement %s : %s -> %s" % (A_RETIRER, sorted(avant), sorted(apres)))
    f = AB / "affaire_ledger_sans_4126_21520.py"
    f.write_text(neuf, encoding="utf-8")
    dire("   module retouche : %d -> %d exclusions (%s retirees) ; %d lignes en moins -> %s"
         % (len(avant), len(apres), "+".join(map(str, A_RETIRER)), len(a_effacer), f))
    return f, apres


def portes_a_blanc(mod_path: Path) -> types.ModuleType:
    """protocole_portes.py, son module de nuit pointe sur la copie retouchee. ⚠ Son temoin A (« le rejeu redonne
    l'image ») NE PEUT PAS etre vert ici : la nuit retouchee bouge deja l'image -- c'est la mesure A, faite a part. On le
    garde a l'ecran, sans s'arreter."""
    src = (Path(__file__).resolve().parent / "protocole_portes.py").read_text(encoding="utf-8")
    for avant, apres in (
            ('MODULE = RACINE / "phase2" / "sync" / "affaire_ledger.py"', "MODULE = Path(%r)" % str(mod_path)),
            ('        dire("   ⛔ TEMOIN ROUGE : le rejeu ne redonne pas l\'image -- ex. %s" % ecartsA[:10])\n'
             '        return 1\n',
             '        dire("   (a blanc) le rejeu A retouche ne redonne pas l\'image : %d pieces -- c\'est la mesure A, '
             'pas un temoin" % len(ecartsA))\n')):
        if src.count(avant) != 1:
            raise SystemExit("⛔ protocole_portes.py a change : ancre %r" % avant[:60])
        src = src.replace(avant, apres)
    m = types.ModuleType("portes_a_blanc")
    # __file__ = le vrai : RACINE (parents[2]) et les deux fichiers de production s'en deduisent
    m.__file__ = str(Path(__file__).resolve().parent / "protocole_portes.py")
    exec(compile(src, "portes_a_blanc (protocole_portes.py, module de nuit retouche)", "exec"), m.__dict__)
    return m


def verdicts(con: sqlite3.Connection, pid: int) -> dict:
    out = {}
    for i, v, e, ps, m in con.execute("select id_unique, verdict, etiquette, pieces, motif from verdict where passage=?",
                                      (pid,)):
        out[i] = {"verdict": v, "etiquette": e, "pieces": set(json.loads(ps)) if ps else set(), "motif": m}
    return out


def membres(ch: dict) -> dict:
    m = defaultdict(set)
    for a, c in ch.items():
        m[c].add(a)
    return m


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.time()
    AB.mkdir(parents=True, exist_ok=True)
    con_v = sqlite3.connect("file:%s?mode=ro" % VRAI_SOCLE.as_posix(), uri=True)
    ref = con_v.execute("select max(id) from passage").fetchone()[0]
    image, version = con_v.execute("select image, version from passage where id=?", (ref,)).fetchone()
    V0 = verdicts(con_v, ref)
    con_v.close()
    dire("RETRAIT DE %s DES EXCLUSIONS DE LA REGLE E -- A BLANC, contre le passage %d (%s), image %s"
         % (" ET ".join(map(str, A_RETIRER)), ref, version, image))
    mod_path, excl_apres = module_retouche()
    shutil.copyfile(VRAI_SOCLE, AB / "socle.sqlite")
    I = P.Image(P.IMAGES / image)
    gel_l = defaultdict(set)
    for i, p_, *_r in I.gel:
        gel_l[i].add(int(p_))
    lab_img = {a: I.pieces[a]["app_dossier_uuid"] for a in I.pieces}
    num_de = {I.pieces[q]["app_dossier_uuid"]: I.pieces[q]["app_dossier_numero"] for q in I.pieces
              if I.pieces[q]["app_dossier_uuid"]}

    def numero(e) -> str:
        return num_de.get(e) or ("NEUF" if str(e).startswith("NEUVE") else str(e))

    def pieces_de(i: str, Vx: dict) -> set:
        return Vx[i]["pieces"] if Vx.get(i, {}).get("verdict") == "TRANCHEE" else gel_l.get(i, set())

    # ── A : LA NUIT TELLE QU'ELLE TOURNE (coupes eteintes), module retouche contre module de production ──────────────
    import protocole_portes as PP
    chA, _r = PP.rejeu_en_cache("A", image, PP.FICHIER_DET_PROD, PP.ETEINTS, False)
    PA = portes_a_blanc(mod_path)
    P.DOSSIER = AB                              # les caches, brouillons et sorties du rejeu a blanc : dans AB
    P.SOCLE = AB / "socle.sqlite"
    P.NOTICE = AB
    chA2, resA2 = PA.rejeu_en_cache("A", image, PA.FICHIER_DET_PROD, PA.ETEINTS, True)
    bougeA = sorted(a for a in chA if chA[a] != chA2.get(a))
    mA, mA2 = membres(chA), membres(chA2)
    compagnieA = sorted(a for a in chA if mA[chA[a]] != mA2[chA2[a]])
    labA = K.pose_de_nuit(lab_img, chA)
    labA2 = K.pose_de_nuit(lab_img, chA2)
    lab_bougeA = sorted(a for a in labA if labA[a] != labA2.get(a))
    dire()
    dire("A  LA NUIT TELLE QU'ELLE TOURNE, coupes ETEINTES (l'interrupteur reste eteint tant qu'A2 n'est pas corrige) :")
    dire("   compte rendu E du module retouche : %s" % {k: v for k, v in resA2.items() if str(k).startswith("[E]")})
    dire("   %d piece(s) changent de numero de chaine ; %d piece(s) changent de compagnie ; %d piece(s) changent "
         "d'etiquette" % (len(bougeA), len(compagnieA), len(lab_bougeA)))
    for a in compagnieA:
        dire("      %d %s %s : dossier %s (%s) -> avec %s" % (
            a, I.pieces[a]["kind"], I.pieces[a]["state"] or "", sorted(mA[chA[a]]), numero(labA[a]),
            sorted(mA2[chA2[a]])))
    lignesA = sorted(i for i in V0 if pieces_de(i, V0) & set(compagnieA))
    dire("   ⛔ LIGNES DONT LE DOSSIER BOUGE A LA PROCHAINE NUIT, sans aucune vague : %d" % len(lignesA))
    for i in lignesA:
        dire("      %s (%s%s) : pieces %s -- etiquette %s -> %s" % (
            i, V0[i]["verdict"], (", " + V0[i]["motif"]) if V0[i]["motif"] else "",
            " ".join(map(str, sorted(pieces_de(i, V0)))),
            "/".join(sorted({numero(labA[q]) for q in pieces_de(i, V0) if q in labA})),
            "/".join(sorted({numero(labA2[q]) for q in pieces_de(i, V0) if q in labA2}))))

    # ── P : LE PROTOCOLE, passage a blanc (copie du socle), les exclusions retirees ────────────────────────────────────
    P._EXCLUES_E.clear()
    P._EXCLUES_E.update(excl_apres)
    rc = P.etape_passage(I, "A BLANC -- %s retirees des exclusions de E (son ② du 24/11) ; reference : passage %d"
                         % ("+".join(map(str, A_RETIRER)), ref))
    con_ab = sqlite3.connect(P.SOCLE)
    pid = con_ab.execute("select max(id) from passage").fetchone()[0]
    V1 = verdicts(con_ab, pid)
    con_ab.close()
    chg = sorted(i for i in V0 if (V0[i]["verdict"], V0[i]["etiquette"], V0[i]["pieces"]) !=
                 (V1[i]["verdict"], V1[i]["etiquette"], V1[i]["pieces"]))
    dire()
    dire("P  LE PROTOCOLE (passage a blanc %d de la copie du socle, contre %d) : %d ligne(s) changent (code %s)"
         % (pid, ref, len(chg), rc))
    for i in chg:
        dire("      %s : %s %s %s -> %s %s %s" % (
            i, V0[i]["verdict"], V0[i]["motif"] or "", " ".join(map(str, sorted(V0[i]["pieces"]))) or "-",
            V1[i]["verdict"], numero(V1[i]["etiquette"]) if V1[i]["etiquette"] else (V1[i]["motif"] or ""),
            " ".join(map(str, sorted(V1[i]["pieces"]))) or "-"))
    autres_P = sorted(set(chg) - ATTENDUES)

    # ── E : LA VAGUE (outil de coupe allume, brouillon du passage a blanc), contre le rejeu E de la reference ─────────
    sys.argv = ["portes_a_blanc", "--passage", str(pid), "--rejeu", "B"]
    PA.main()
    sys.argv = ["portes_a_blanc", "--passage", str(pid), "--rejeu", "E"]
    PA.main()
    sys.argv = ["portes_a_blanc", "--passage", str(pid)]
    rcE = PA.main()
    pt1 = json.loads((AB / ("portes_passage_%d.json" % pid)).read_text(encoding="utf-8"))
    pt0 = json.loads((VRAI_DOSSIER / ("portes_passage_%d.json" % ref)).read_text(encoding="utf-8"))
    # les deux etats d'arrivee : le rejeu E de reference (module de production, brouillon de reference) ...
    P.DOSSIER = VRAI_DOSSIER
    brouillon0 = VRAI_DOSSIER / ("brouillon_detachements_protocole_passage_%d.csv" % ref)
    chE0, _ = PP.rejeu_en_cache("E", image, brouillon0, {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"},
                                False)
    P.DOSSIER = AB
    brouillon1 = AB / ("brouillon_detachements_protocole_passage_%d.csv" % pid)
    chE1, resE1 = PA.rejeu_en_cache("E", image, brouillon1, {"APP_CHAINAGE_GARDE_G2": "0",
                                                             "APP_CHAINAGE_DETACHEMENTS": "1"}, False)
    mE0, mE1 = membres(chE0), membres(chE1)
    labE0, labE1 = K.pose_de_nuit(lab_img, chE0), K.pose_de_nuit(lab_img, chE1)
    compE = sorted(a for a in chE0 if mE0[chE0[a]] != mE1[chE1[a]])
    labE = sorted(a for a in labE0 if labE0[a] != labE1.get(a))
    b0 = set(brouillon0.read_text(encoding="utf-8").splitlines()[2:])
    b1 = set(brouillon1.read_text(encoding="utf-8").splitlines()[2:])
    dire()
    dire("E  LA VAGUE (outil de coupe allume, le brouillon du passage a blanc) contre le rejeu E du passage %d (code %s) :"
         % (ref, rcE))
    dire("   compte rendu [X] : %s" % {k: v for k, v in resE1.items() if str(k).startswith("[X]")})
    dire("   brouillon : %d morceaux (reference %d) ; + %s ; - %s" % (len(b1), len(b0), sorted(b1 - b0), sorted(b0 - b1)))
    dire("   %d piece(s) changent de compagnie a l'arrivee ; %d piece(s) changent d'etiquette" % (len(compE), len(labE)))
    for a in sorted(set(compE) | set(labE)):
        dire("      %d %s %s : %s (%s) -> %s (%s)" % (a, I.pieces[a]["kind"], I.pieces[a]["state"] or "",
                                                   sorted(mE0[chE0[a]]), numero(labE0[a]), sorted(mE1[chE1[a]]),
                                                   numero(labE1[a])))
    touchees = set(compE) | set(labE)
    lignesE = sorted(i for i in V1 if (pieces_de(i, V1) | pieces_de(i, V0)) & touchees)
    autres_E = sorted(set(lignesE) - ATTENDUES)
    dire("   lignes que la vague touche autrement que la reference : %d -- %s" % (len(lignesE), lignesE))
    att = sorted(i for i in V1 if V1[i]["verdict"] == "ATTENTE" and gel_l.get(i, set()) & touchees)
    dire("   lignes EN ATTENTE dont un dossier d'arrivee change : %d %s" % (len(att), att))

    dire()
    dire("LE CHIFFRE QU'IL DEMANDE :")
    dire("   se debloquent : %s (attendu %s)" % (sorted(i for i in chg if V1[i]["verdict"] == "TRANCHEE"),
                                                sorted(ATTENDUES)))
    dire("   ⛔ AUTRES lignes qui bougent -- nuit sans vague (A) : %d %s" % (len(set(lignesA) - ATTENDUES),
                                                                         sorted(set(lignesA) - ATTENDUES)))
    dire("   ⛔ AUTRES lignes qui bougent -- protocole (P) : %d %s ; vague (E) : %d %s"
         % (len(autres_P), autres_P, len(autres_E), autres_E))
    (AB / "retrait_e_a_blanc.json").write_text(json.dumps({
        "reference": ref, "passage_a_blanc": pid, "image": image, "A_pieces": compagnieA, "A_lignes": lignesA,
        "A_etiquettes": lab_bougeA, "P_changent": chg, "E_pieces": compE, "E_etiquettes": labE, "E_lignes": lignesE,
        "E_attente": att, "portes_ref": pt0["portes"], "portes_ab": pt1["portes"],
        "faux_E_ab": pt1["faux_E"], "diff_etiquette_ab": pt1["diff_etiquette"], "hors_ab": pt1["hors"],
        "duree_s": round(time.time() - t0)}, ensure_ascii=False, indent=1), encoding="utf-8")
    dire("-> %s (%.0f s)" % (AB / "retrait_e_a_blanc.json", time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
