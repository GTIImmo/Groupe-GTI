"""Chantier classeur, ⑱ (22/11/2026) -- LA V3 : FABRIQUEE, REPETEE SUR COPIE, JAMAIS JOUEE.

Son mot du 21/11, point 1-A : « OUI, FABRIQUE-LA, NE LA JOUE PAS. [...] joue la repetition a blanc, et montre-moi UNE
SEULE chose en plus : ce que ces 83 gestes font aux ecritures rapatriees et aux repartitions orphelines. »
Point 1-B : « A PART » RESTREINTE AUX 20 (la place des 19 autres ne bouge aucune etiquette : elles ATTENDENT).
Point 3 : le classement du 19/11 ne voyait pas les reunions de E (nuit du 20 au 21) -> TOUT EST RECALCULE sur la base
d'aujourd'hui.

LECTURE SEULE. Rien dans le Sheet, rien chez Hektor, rien en base : la base locale est copiee en memoire (mode=ro), le
gel et les ecritures sont lus par le pooler en transaction read only. Le fichier des detachements V3 est ecrit DANS LE
CACHE du chantier, jamais dans phase2/sync/ (celui-la ne change que sur son « vas-y »).
Un appel = une etape, ecrite au fil de l'eau (jamais plus de 10 minutes d'un bloc).

  s       rejoue la nuit de ce soir sur copie, G2 + l'outil V2 allumes -> chaines_s_22_11.json (la base de calcul)
  calcul  « ou ca tombe » refait sur ces chaines (copie fidele de temps11, partie 6), temoin = les comptes du 20/11 ;
          puis la V3 : 20 pieces a part, les 19 neutres attendent -> v3_calcul.json + brouillon du fichier
  rejeu   rejoue G2 + le brouillon V3 : chaque morceau exact, rien hors des biens nommes, les 19 a leur place,
          les etiquettes -> chaines_v3.json
  ecrit   ce que la V3 fait aux ecritures : repartitions / notes / conditions (par app_chaine_id) et factures /
          reglements / honoraires (par transaction) ; la purge de nuit rejouee en lecture
"""
from __future__ import annotations

import contextlib
import csv
import io
import json
import os
import sqlite3
import sys
import time
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import importlib.util  # noqa: E402

import coupe_preuve_interne as K  # noqa: E402

_spec = importlib.util.spec_from_file_location("t10", Path(__file__).resolve().parent / "temps10_g2_et_l_outil_rejeu_2026-11-20.py")
T10 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T10)          # le rejeu sur copie de temps10 (charger / rejouer / ETEINTS), tel quel

CACHE = K.CACHE
JOURNAL = CACHE / "temps12_journal.txt"
NOTICE = RACINE / "notice"
LES_132 = NOTICE / "TEMPS8_DECISION_DU_20_11_LES_132_COUPES_DATEES_VALIDEES_2026-11-20.csv"
GROUPES = NOTICE / "TEMPS9_LE_CLASSEUR_DES_GROUPES_2026-11-20.csv"
QUESTIONS = NOTICE / "TEMPS10_TES_23_QUESTIONS_EN_DEUX_2026-11-20.csv"
FICHIER_V2 = RACINE / "phase2" / "sync" / "detachements_manuels.csv"
BROUILLON_V3 = CACHE / "detachements_manuels_V3_brouillon.csv"
A_PART_PAR_DECISION = {14033: "B3, sa decision du 20/11 soir"}
PROUVEES = (K.PROUVEE_DATE, K.PROUVEE_PH, K.PROPRE_C5, "PROUVEE PAR SA CHAINE")
TEMOIN_20_11 = {"morceaux": 433, "a_part": 39, "neutres": 19, "ecrites": 395, "gestes": 83}

# ⭐ SON MOT DU 22/11, POINT 3 -- LES JUMELLES : « EXCEPTION DECLAREE ET NOMMEE ». Son « ecris-les toutes les deux » du
#   20/11 tient : VIALLARD et PAOLONE s'ecrivent (395 lignes, pas 393), MAIS PAS EN SILENCE : une affaire que SON classeur
#   porte sur deux lignes, de la meme facon que 20088 (§ 18.9). Le controle « deux lignes sur un dossier » ne les compte
#   PAS comme un echec : il les SAUTE EN LES NOMMANT, a chaque passage, pour qu'on sache toujours qu'elles existent.
#   (bien, ses deux lignes) -> le nom en clair. ⛔ Une exception ne s'ajoute ici que sur SA demande, datee.
EXCEPTIONS_NOMMEES = {
    ("9748", ("3308P0UX", "YRUF0S9H")): "VIALLARD -- une affaire saisie sur deux lignes du Sheet (3785 et 3796), "
                                        "bien 9748 ; exception nommee le 22/11 (son mot, point 3)",
    ("41467", ("O6R10ZQA", "T2GZOY5O")): "PAOLONE -- une affaire saisie sur deux lignes du Sheet (3887 et 3856), "
                                         "bien 41467 ; exception nommee le 22/11 (son mot, point 3)",
}
LIGNES_EXCEPTION = {frozenset(gl): w for (_b, gl), w in EXCEPTIONS_NOMMEES.items()}


def exception_du_verrou(lignes) -> str | None:
    """Le nom de l'exception si ces lignes (celles d'un dossier partage) sont TOUTES dans UNE exception nommee."""
    s = set(lignes)
    for gl, w in LIGNES_EXCEPTION.items():
        if s <= gl:
            return w
    return None


# ⭐ SON MOT DU 22/11, POINT 2 -- LE TEMOIN DU PATCH : « Un temoin ne doit jamais porter sur le geste le MOINS valide du
#   lot ». Celui du 22/11 (« 6FQO29C8 tient 19131 ») etait le premier par ordre alphabetique -- justement un des quatre
#   gestes qu'il n'a pas valides. On ne le tire plus au sort : on le NOMME, pris dans les gestes qu'il a vus, et on en met
#   DEUX, un de chaque sens : la piece 3678 (offre du 14/08/2025, prouvee par la date sur la case « Offre Achat » de
#   c08ff7cb) passe de 721e650c a c08ff7cb.
GESTES_A_SA_DECISION = {("6FQO29C8", 19131), ("6FQO29C8", 19133), ("V3FO5NDA", 19131), ("V3FO5NDA", 19133)}
TEMOIN_RELIER = ("c08ff7cb", 3678)
TEMOIN_DELIER = ("721e650c", 3678)


def dire(s: str = "") -> None:
    ligne = "%s  %s" % (datetime.now().strftime("%H:%M:%S"), s)
    print(ligne, flush=True)
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write(ligne + "\n")


def lire_csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


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


def gel_vivant() -> list:
    cn, cu = pooler()
    cu.execute("select id_unique, app_affaire_id from app_classeur_lien")
    gel = [(i, int(a)) for i, a in cu.fetchall()]
    cn.rollback()
    cn.close()
    return gel


def etiquettes(lab_prec: dict, ch_new: dict) -> dict:
    """La pose de nuit (recopie de temps11/temps6) : la FUSION garde l'etiquette de la plus petite transaction ; la
    SCISSION laisse l'etiquette au groupe de la plus petite transaction qui la porte et en donne une NEUVE aux autres."""
    mem = defaultdict(list)
    for a, c in ch_new.items():
        mem[c].append(a)
    lab1 = {}
    for c, ms in mem.items():
        labs = {lab_prec[a] for a in ms if lab_prec.get(a)}
        g_ = (lab_prec[min(a for a in ms if lab_prec.get(a))] if labs else "NEUVE:%s" % min(ms))
        for a in ms:
            lab1[a] = g_
    tete, chaines_du_lab = {}, defaultdict(set)
    for a in sorted(lab1):
        tete.setdefault(lab1[a], ch_new[a])
        chaines_du_lab[lab1[a]].add(ch_new[a])
    return {a: (l_ if len(chaines_du_lab[l_]) == 1 or ch_new[a] == tete[l_] else "NEUVE:%s" % min(mem[ch_new[a]]))
            for a, l_ in lab1.items()}


def labels_locaux() -> dict:
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(), uri=True)
    r = {int(a): u for a, u in con.execute("select app_affaire_id, app_dossier_uuid from app_affaire_ledger")}
    con.close()
    return r


def chaines_locales() -> dict:
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(), uri=True)
    r = {int(a): int(c) for a, c in con.execute("select app_affaire_id, app_chaine_id from app_affaire_ledger")}
    con.close()
    return r


# ══ s ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
def etape_s() -> int:
    t0 = time.time()
    dire("S : la nuit de ce soir rejouee sur copie de la base d'AUJOURD'HUI, G2 + l'outil V2 (le fichier en place)")
    mod = T10.charger(T10.MODULE, "apres")
    ch_off, res_off, _ = T10.rejouer(mod, T10.ETEINTS)
    loc = chaines_locales()
    ecart_off = sum(1 for a in loc if loc[a] != ch_off.get(a))
    dire("   eteints : %d dossiers ; transactions dont le dossier differe de la base locale : %d (la nuit ne referait "
         "pas exactement hier : c'est la mesure, pas un defaut)" % (len(set(ch_off.values())), ecart_off))
    ch, res, _ = T10.rejouer(mod, {"APP_CHAINAGE_GARDE_G2": "1", "APP_CHAINAGE_DETACHEMENTS": "1"})
    dire("   G2 + outil V2 : %d dossiers ; compte rendu : %s" % (
        len(set(ch.values())), {k: v for k, v in res.items() if str(k).startswith("[X]")}))
    vieux = {int(a): c for a, c in json.loads((CACHE / "chaines_ce_soir_avec_g2_et_outil.json").read_text(
        encoding="utf-8")).items()}
    # comparer les PARTITIONS, pas les numeros : un dossier se reconnait a ses membres
    def part(chs):
        m = defaultdict(set)
        for a, c in chs.items():
            m[c].add(a)
        return {a: frozenset(m[c]) for a, c in chs.items()}
    pv, pn = part(vieux), part(ch)
    bouge = sorted(a for a in pn if pv.get(a) != pn[a])
    dire("   ⭐ contre la base de calcul du 20/11 : %d transactions dont le dossier n'a plus les memes membres %s"
         % (len(bouge), bouge[:20]))
    (CACHE / "chaines_s_22_11.json").write_text(json.dumps({str(k): v for k, v in ch.items()}), encoding="utf-8")
    (CACHE / "chaines_s_22_11_bouge.json").write_text(json.dumps(bouge), encoding="utf-8")
    dire("S : FIN (%.0f s)" % (time.time() - t0))
    return 0


# ══ calcul ═════════════════════════════════════════════════════════════════════════════════════════════════════════
def ou_ca_tombe(D, S: dict, lignes_cibles: set):
    """COPIE FIDELE de temps11, partie 6 (meme ordre, memes regles). Rend tout ce qu'il faut pour la V3."""
    biens6 = defaultdict(set)
    for i in lignes_cibles:
        for a in D.gel_l.get(i, set()):
            if a in D.REG:
                biens6[D.REG[a]["bien"]].add(i)
        for b, ls in D.lignes_bien.items():
            if i in ls:
                biens6[b].add(i)
    sort_brut = defaultdict(list)
    par_bien = {}
    a_part_tot, morceaux_tot, gestes_gel, par_chaine, par_renego = [], 0, [], [], []
    for b, ls_b in sorted(biens6.items()):
        lignes_b = (D.lignes_bien.get(b, set()) | ls_b)
        lies = {a for i in lignes_b for a in D.gel_l.get(i, set()) if a in D.REG and D.REG[a]["bien"] == b}
        chaines_t = {S[a] for a in lies if a in S}
        X = sorted(a for a in D.par_bien.get(b, []) if S.get(a) in chaines_t)
        va, apart = {}, {}
        for a in X:
            if a in A_PART_PAR_DECISION:
                apart[a] = A_PART_PAR_DECISION[a]
                continue
            ls_, quoi = K.decider(D, a, lignes_b)
            if ls_:
                va[a] = frozenset(ls_)
            else:
                apart[a] = quoi
        for a in sorted(apart):
            p_ = D.REG.get(a, {})
            if p_.get("genre") != "offre" or p_.get("etat") not in ("accepted", "acceptee") or not p_.get("date") \
                    or a in A_PART_PAR_DECISION:
                continue
            suivants = [c for c in va if S.get(c) == S.get(a) and D.REG[c]["genre"] == "compromis" and D.REG[c]["date"]
                        and 0 <= (D.REG[c]["date"] - p_["date"]).days <= 31]
            for c in sorted(suivants, key=lambda c: D.REG[c]["date"]):
                entre = [o for o in X if o != a and D.REG[o]["genre"] == "offre"
                         and D.REG[o]["etat"] in ("accepted", "acceptee") and D.REG[o]["date"]
                         and p_["date"] < D.REG[o]["date"] <= D.REG[c]["date"]]
                if not entre:
                    va[a] = va[c]
                    par_chaine.append((a, c))
                    del apart[a]
                    break
        for a in sorted(apart):
            p_ = D.REG.get(a, {})
            if p_.get("genre") != "offre" or p_.get("etat") not in ("accepted", "acceptee") or not p_.get("date") \
                    or a in A_PART_PAR_DECISION:
                continue
            origines = [o for o in va if S.get(o) == S.get(a) and D.REG[o]["genre"] == "offre" and D.REG[o]["date"]
                        and D.REG[o]["date"] < p_["date"]]
            for o in sorted(origines, key=lambda o: D.REG[o]["date"], reverse=True):
                autres = [i for i in lignes_b if i not in va[o]
                          and any(d and D.REG[o]["date"] <= d <= p_["date"]
                                  for d in (K.d_sheet(D.case(i, c)) for c in ("Offre Achat", "Compromis")))]
                if not autres:
                    va[a] = va[o]
                    par_renego.append((a, o))
                    del apart[a]
                    break
        groupes_l = []
        for a, ls_ in va.items():
            fus = [gl for gl in groupes_l if gl & ls_]
            nouveau = set(ls_).union(*fus) if fus else set(ls_)
            groupes_l = [gl for gl in groupes_l if gl not in fus] + [nouveau]
        morceaux6 = {frozenset(gl): sorted(a for a, ls_ in va.items() if ls_ & gl) for gl in groupes_l}
        morceaux_tot += len(morceaux6)
        neutres_b = {}
        for a, why in apart.items():
            possibles = [(gl, m + [a]) for gl, m in morceaux6.items() if not D.contre_dates(a, set(gl))]
            neu = K.neutre(a, [m for _gl, m in possibles]) if possibles else False
            a_part_tot.append((b, a, why, neu))
            if neu:
                neutres_b[a] = [sorted(gl) for gl, _m in possibles]
        for gl, ids in morceaux6.items():
            for i in gl:
                liens = {a for a in D.gel_l.get(i, set()) if a in D.REG and not D.REG[a]["c5"]}
                if set(ids) - liens:
                    gestes_gel.append((i, "relier", sorted(set(ids) - liens)))
                if liens - set(ids):
                    gestes_gel.append((i, "delier", sorted(liens - set(ids))))
        for i in sorted(lignes_b & lignes_cibles):
            gl = [g_ for g_ in morceaux6 if i in g_]
            liens = sorted(a for a in D.gel_l.get(i, set()) if a in D.REG and not D.REG[a]["c5"]
                           and D.REG[a]["bien"] == b)
            hk = [x for x in (morceaux6[gl[0]] if gl else []) if not D.REG[x]["c5"]]
            if gl and hk:
                sort_brut[i].append(("ECRITE", "morceau %s" % "+".join(str(x) for x in morceaux6[gl[0]]), b))
            elif gl:
                sort_brut[i].append(("NON ECRITE", "il ne lui reste que sa copie C5", b))
            elif liens:
                sort_brut[i].append(("NON ECRITE", "ses pieces sont a part ou ailleurs : " + " ; ".join(
                    "%d (%s)" % (a, apart.get(a, "donnee a une autre ligne")) for a in liens), b))
        par_bien[b] = {"X": X, "morceaux": [[sorted(gl), ids] for gl, ids in morceaux6.items()],
                       "apart": {str(a): w for a, w in apart.items()}, "neutres": {str(a): v for a, v in neutres_b.items()},
                       "lignes": sorted(lignes_b)}
    sort_ligne = {}
    for i, rs in sort_brut.items():
        ec = [r for r in rs if r[0] == "ECRITE"]
        if len(ec) == 1:
            sort_ligne[i] = ec[0][:2]
        elif len(ec) > 1:
            sort_ligne[i] = ("NON ECRITE", "ecrite sur deux biens")
        else:
            sort_ligne[i] = rs[0][:2]
    for i in lignes_cibles:
        sort_ligne.setdefault(i, ("NON ECRITE", "aucune piece chez nous"))
    return par_bien, sort_ligne, a_part_tot, morceaux_tot, gestes_gel, par_chaine, par_renego


def lignes_cibles_du_20_11() -> tuple[set, set]:
    lignes_132 = {r["id_unique"] for r in lire_csv(LES_132)}
    cibles = set(lignes_132)
    for g in lire_csv(GROUPES):
        if g["section"][:2] in ("1 ", "2 ", "3 "):
            cibles |= set(g["lignes du Sheet"].split())
    for q in lire_csv(QUESTIONS):
        if q["classe"] in ("A", "B-attend", "B-libre"):
            cibles |= set(q["lignes du Sheet"].split())
    return cibles, lignes_132


def etape_calcul() -> int:
    t0 = time.time()
    gel = gel_vivant()
    D = K.Donnees(gel)
    cibles, lignes_132 = lignes_cibles_du_20_11()
    dire("CALCUL : gel vivant %d liens ; %d lignes visees (les 132 + sections 1-3 + ses questions)" % (len(gel), len(cibles)))
    resultats = {}
    for nom, fichier in (("20_11", "chaines_ce_soir_avec_g2_et_outil.json"), ("22_11", "chaines_s_22_11.json")):
        S = {int(a): c for a, c in json.loads((CACHE / fichier).read_text(encoding="utf-8")).items()}
        r = ou_ca_tombe(D, S, cibles)
        par_bien, sort_ligne, a_part_tot, mt, gestes, pc, pr = r
        c = Counter(v[0] for v in sort_ligne.values())
        cpt = {"morceaux": mt, "a_part": len(a_part_tot), "neutres": sum(1 for x in a_part_tot if x[3]),
               "ecrites": c["ECRITE"], "gestes": len(gestes)}
        dire("   base %s : %s ; non ecrites : %s" % (nom, cpt, sorted(i for i, v in sort_ligne.items() if v[0] != "ECRITE")))
        resultats[nom] = (r, cpt)
    (r20, c20), (r22, c22) = resultats["20_11"], resultats["22_11"]
    dire("   ⭐ TEMOIN (la copie de temps11 refait le 20/11 a l'identique) : %s" % (
        "VERT" if c20 == TEMOIN_20_11 else "⛔ ROUGE %s au lieu de %s" % (c20, TEMOIN_20_11)))
    diff_sort = sorted(i for i in cibles if r20[1].get(i) != r22[1].get(i))
    diff_gestes = sorted(set(map(lambda g: (g[0], g[1], tuple(g[2])), r20[4])) ^
                         set(map(lambda g: (g[0], g[1], tuple(g[2])), r22[4])))
    dire("   ⭐ SUR LA BASE D'AUJOURD'HUI : lignes dont le sort change : %d %s ; gestes du gel differents : %d %s"
         % (len(diff_sort), diff_sort[:12], len(diff_gestes), diff_gestes[:8]))
    par_bien, sort_ligne, a_part_tot, mt, gestes, pc, pr = r22
    a20 = [(b, a, w) for b, a, w, neu in a_part_tot if not neu]
    n19 = [(b, a, w) for b, a, w, neu in a_part_tot if neu]
    dire("   A PART : %d pieces, dont %d dont la place bouge une etiquette (a part) et %d neutres (elles attendent)"
         % (len(a_part_tot), len(a20), len(n19)))
    json.dump({"par_bien": {str(b): v for b, v in par_bien.items()},
               "sort_ligne": sort_ligne, "a20": a20, "n19": n19,
               "gestes_20_11": r20[4], "gestes_22_11": gestes, "compte_20_11": c20, "compte_22_11": c22,
               "diff_sort": diff_sort, "par_chaine": pc, "par_renego": pr},
              (CACHE / "v3_calcul.json").open("w", encoding="utf-8"), ensure_ascii=False)
    dire("CALCUL : FIN (%.0f s) -> v3_calcul.json" % (time.time() - t0))
    return 0 if c20 == TEMOIN_20_11 else 1


# ══ brouillon + rejeu ══════════════════════════════════════════════════════════════════════════════════════════════
def ecrire_brouillon(d: dict, maisons: dict) -> int:
    """Une ligne par morceau (ses pieces prouvees + les neutres qui y ATTENDENT), une ligne par piece a part (les 20).
    Les neutres sans maison ne sont dans AUCUNE ligne : l'outil les laisse dans le reste de leur dossier."""
    sortie = ["# LES DETACHEMENTS DECIDES A LA MAIN -- V3 (BROUILLON, dans le cache : la place de production ne change que",
              "# sur son « vas-y »). Lu par affaire_ledger.recalculer_les_chaines SEULEMENT si APP_CHAINAGE_DETACHEMENTS=1.",
              "# Genere le %s par phase2/checks/temps12_v3_fabriquer_2026-11-22.py depuis « ou ca tombe » (validé sous"
              % datetime.now().strftime("%d/%m/%Y %H:%M"),
              "# condition le 21/11), sur la base du 22/11 : les morceaux prouves, les 20 pieces a part, les neutres qui attendent.",
              "transactions;bien;geste;pourquoi"]
    n = 0
    for b, v in sorted(d["par_bien"].items(), key=lambda kv: int(kv[0])):
        for gl, ids in v["morceaux"]:
            geste = "v3_morceau"
            if len(gl) > 1:
                # ⛔ SON VERROU (point 3) : deux de ses lignes sur un dossier -- la V3 ne le cree pas, ca lui remonte ;
                #   SAUF une EXCEPTION NOMMEE (son mot du 22/11, point 3 : les jumelles s'ecrivent, declarees)
                w = EXCEPTIONS_NOMMEES.get((str(b), tuple(sorted(gl))))
                if not w:
                    continue
                geste = "v3_exception_nommee"
            att = sorted(int(a) for a, m in maisons.items() if m == (b, tuple(gl)))
            sortie.append("%s;%s;%s;%s%s%s" % (" ".join(map(str, sorted(ids + att))), b, geste, " ".join(gl),
                                               (" (attendent ici, neutres : %s)" % " ".join(map(str, att))) if att else "",
                                               (" -- EXCEPTION NOMMEE : %s" % EXCEPTIONS_NOMMEES[(str(b), tuple(sorted(gl)))]
                                                .replace(";", ",")) if geste != "v3_morceau" else ""))
            n += 1
    for b, a, w in d["a20"]:
        sortie.append("%d;%s;v3_a_part;%s" % (a, b, w.replace(";", ",")))
        n += 1
    for a, (b, gl) in sorted(maisons.items(), key=lambda kv: int(kv[0])):
        if gl and gl[0] == "SEULE_AVEC":
            sortie.append("%s;%s;v3_attend_avec_sa_ligne;%s (neutre : sa ligne n'a aucun morceau)" % (a, b, " ".join(gl[1:])))
            n += 1
    BROUILLON_V3.write_text("\n".join(sortie) + "\n", encoding="utf-8")
    return n


def rejouer_brouillon():
    """G2 + l'outil, le module de production lisant le BROUILLON (jamais le fichier de production)."""
    sauve = T10.FICHIER_DET
    T10.FICHIER_DET = BROUILLON_V3
    try:
        mod = T10.charger(T10.MODULE, "v3")
        ch, res, _ = T10.rejouer(mod, {"APP_CHAINAGE_GARDE_G2": "1", "APP_CHAINAGE_DETACHEMENTS": "1"})
        det = mod.lire_detachements_manuels()
    finally:
        T10.FICHIER_DET = sauve
    return ch, res, det


def etape_rejeu() -> int:
    t0 = time.time()
    d = json.load((CACHE / "v3_calcul.json").open(encoding="utf-8"))
    mode = sys.argv[2] if len(sys.argv) > 2 else "dehors"
    maisons = json.load((CACHE / "v3_maisons.json").open(encoding="utf-8")) if mode == "maisons" else {}
    maisons = {a: (m[0], tuple(m[1])) for a, m in maisons.items()}
    n = ecrire_brouillon(d, maisons)
    dire("REJEU (%s) : brouillon %s -- %d lignes ; G2 + l'outil sur copie" % (mode, BROUILLON_V3.name, n))
    ch, res, det = rejouer_brouillon()
    S = {int(a): c for a, c in json.loads((CACHE / "chaines_s_22_11.json").read_text(encoding="utf-8")).items()}
    loc = chaines_locales()
    dire("   lus : %d ; compte rendu : %s" % (len(det), {k: v for k, v in res.items() if str(k).startswith("[X]")}))
    mem = defaultdict(set)
    for a, c in ch.items():
        mem[c].add(a)
    faux = [(g, sorted(ids)) for ids, _b, g, _p in det if len({ch.get(a) for a in ids}) != 1
            or mem[ch[min(ids)]] != set(ids)]
    dire("   ⭐ morceaux qui finissent EXACTEMENT comme ecrits : %d sur %d ; autrement : %s"
         % (len(det) - len(faux), len(det), faux[:6]))
    nommes = {a for ids, *_ in det for a in ids}
    biens_v3 = {int(b) for b in d["par_bien"]}
    REG = {}
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(), uri=True)
    for a, b in con.execute("select app_affaire_id, hektor_annonce_id from app_affaire_ledger"):
        REG[int(a)] = int(b) if b is not None else None
    con.close()
    # contre l'etat de PRODUCTION (eteints) : ce qui bouge, et ou
    memL = defaultdict(set)
    for a, c in loc.items():
        memL[c].add(a)
    bouge = sorted(a for a in ch if mem[ch[a]] != memL[loc[a]])
    hors = sorted(a for a in bouge if REG.get(a) not in biens_v3)
    dire("   contre la PRODUCTION (G2 et outil eteints) : dossiers %d -> %d ; transactions qui changent de membres : %d ;"
         " dont hors des biens de la V3 (G2 seule) : %d" % (len(memL), len(mem), len(bouge), len(hors)))
    # les neutres : ou finissent-elles ?
    seules = []
    for b, a, w in d["n19"]:
        comp = sorted(mem[ch[a]] - {a})
        if not comp:
            seules.append((b, a))
        dire("   neutre %d (bien %s) : %s" % (a, b, ("SEULE" if not comp else "avec %s" % comp[:8])))
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(), uri=True)
    VENTE = {int(a) for (a,) in con.execute("select app_affaire_id from app_affaire_ledger where kind = 'vente'")}
    con.close()
    deux_v = lambda chs: sorted(c for c, n in Counter(chs[a] for a in chs if a in VENTE).items() if n > 1)  # noqa: E731
    dv_av, dv_ap = deux_v(loc), deux_v(ch)
    dire("   ⭐ « jamais deux ventes dans un dossier » : aujourd'hui %d dossiers, apres la V3 %d ; que la V3 cree : %s"
         % (len(dv_av), len(dv_ap), sorted(set(dv_ap) - set(dv_av))))
    lab0 = labels_locaux()
    lab1 = etiquettes(lab0, ch)
    change = sorted(a for a in ch if lab1[a] != lab0.get(a))
    dire("   etiquettes : transactions dont l'etiquette change contre aujourd'hui : %d ; dossiers neufs : %d"
         % (len(change), len({lab1[a] for a in ch if str(lab1[a]).startswith("NEUVE")})))
    json.dump({"ch": {str(k): v for k, v in ch.items()}, "lab1": {str(k): v for k, v in lab1.items()},
               "seules": seules, "faux": faux, "bouge": bouge, "hors": hors, "mode": mode},
              (CACHE / ("v3_rejeu_%s.json" % mode)).open("w", encoding="utf-8"))
    dire("REJEU (%s) : FIN (%.0f s) ; neutres seules : %d %s" % (mode, time.time() - t0, len(seules), seules))
    return 0 if not faux else 1


def etape_maisons() -> int:
    """« ELLES ATTENDENT » (son point 1-B) : une piece neutre ne devient pas un dossier de plus ; elle reste la ou elle
    est. LA REGLE, dans cet ordre, parmi les morceaux que ses DATES permettent (jamais un autre) :
      1. le morceau de la ligne a laquelle le GEL la relie deja (elle y est aujourd'hui pour le Sheet) ;
      2. sinon le morceau qui garde la plus petite transaction de son dossier de PRODUCTION (elle y est pour l'app) ;
      3. sinon, si un seul morceau est possible, celui-la ;
      4. sinon AUCUN : elle reste seule, et elle me remonte (ce serait une 21e piece a part).
    Neutre veut dire qu'aucune de ces places ne bouge une etiquette : le choix ne coute rien au Sheet."""
    d = json.load((CACHE / "v3_calcul.json").open(encoding="utf-8"))
    gel = gel_vivant()
    tx_lignes = defaultdict(set)
    for i, a in gel:
        tx_lignes[a].add(i)
    loc = chaines_locales()
    memL = defaultdict(set)
    for a, c in loc.items():
        memL[c].add(a)
    maisons, motifs, sans = {}, Counter(), []
    for b, a, w in d["n19"]:
        v = d["par_bien"][str(b)]
        possibles = [tuple(gl) for gl in v["neutres"][str(a)]]
        ids_de = {tuple(gl): ids for gl, ids in v["morceaux"]}
        choix, pourquoi = None, ""
        lies = tx_lignes.get(a, set())
        p1 = [gl for gl in possibles if lies and lies <= set(gl)]
        if len(p1) == 1:
            choix, pourquoi = p1[0], "1 le gel la relie deja a %s" % " ".join(sorted(lies))
        # 1' LE GEL LA RELIE A UNE LIGNE QUI N'A AUCUN MORCEAU : elle reste AVEC ELLE, seule -- c'est le dossier de cette
        #    ligne, pas une piece pendante. La ranger chez un autre acheteur mettrait deux de ses lignes sur un dossier
        #    (son verrou du point 3).
        if not choix and lies and not any(lies & set(gl) for gl, _ids in v["morceaux"]):
            maisons[str(a)] = [str(b), ["SEULE_AVEC"] + sorted(lies)]
            motifs["1'"] += 1
            dire("   %d (bien %s, %s) -> SEULE, avec sa ligne %s (qui n'a aucun morceau)" % (a, b, w[:60], " ".join(sorted(lies))))
            continue
        # 2' SON DOSSIER D'AUJOURD'HUI N'A AUCUNE PIECE PROUVEE (il n'est fait que de pieces qui attendent, ou hors du
        #    bien vu) : elle y RESTE, telle quelle -- aucune ligne dans le fichier. Trouve sur 53342 (22/11) : la chaine
        #    jumelle offre 27136 + vente 27141 serait sinon versee dans le dossier d'une autre vente (deux ventes dans un
        #    dossier) et ses parts d'honoraires deviendraient orphelines.
        dans_morceaux = {x for _gl, ids in v["morceaux"] for x in ids}
        if not choix and not ((memL[loc[a]] - {a}) & dans_morceaux):
            motifs["2'"] += 1
            dire("   %d (bien %s, %s) -> RESTE dans son dossier d'aujourd'hui %d %s (aucune piece prouvee n'y est)"
                 % (a, b, w[:60], loc[a], sorted(memL[loc[a]])))
            continue
        if not choix:
            autres = sorted(memL[loc[a]] - {a})
            for t in autres:
                p2 = [gl for gl in possibles if t in ids_de[gl]]
                if p2:
                    choix, pourquoi = p2[0], "2 son dossier de production (%d) garde ici sa plus petite transaction %d" % (
                        loc[a], t)
                    break
        if not choix and len(possibles) == 1:
            choix, pourquoi = possibles[0], "3 un seul morceau possible"
        if choix:
            maisons[str(a)] = [str(b), list(choix)]
            motifs[pourquoi[0]] += 1
            dire("   %d (bien %s, %s) -> morceau de %s : %s" % (a, b, w[:60], " ".join(choix), pourquoi))
        else:
            sans.append((b, a))
            dire("   %d (bien %s) -> AUCUNE MAISON (possibles : %d ; gel : %s)" % (a, b, len(possibles), sorted(lies)))
    json.dump(maisons, (CACHE / "v3_maisons.json").open("w", encoding="utf-8"))
    dire("MAISONS : %d sur %d ; par regle %s ; sans maison %s" % (len(maisons), len(d["n19"]), dict(motifs), sans))
    return 0


# ══ gestes ═════════════════════════════════════════════════════════════════════════════════════════════════════════
def gel_complet() -> list:
    cn, cu = pooler()
    cu.execute("select id_unique, app_affaire_id, role, confiance, preuves, ligne_classeur from app_classeur_lien")
    r = [(i, int(a), ro, cf, p, lc) for i, a, ro, cf, p, lc in cu.fetchall()]
    cu.execute("select count(*), md5(string_agg(id_unique||':'||app_affaire_id||':'||role, ',' "
               "order by id_unique collate \"C\", app_affaire_id)) from app_classeur_lien")
    n, emp = cu.fetchone()
    cn.rollback()
    cn.close()
    return r, n, emp


def lignes_partagees(liens: dict, ch: dict) -> dict:
    """SON VERROU (point 3) : dossier -> les lignes du Sheet qui y tombent, quand il y en a plusieurs."""
    par = defaultdict(set)
    for i, txs in liens.items():
        for a in txs:
            if a in ch:
                par[ch[a]].add(i)
    return {c: ls for c, ls in par.items() if len(ls) > 1}


def etape_gestes() -> int:
    """LES GESTES DU GEL V3. Pour chaque morceau a UNE ligne : la ligne tient ses pieces PROUVEES (+ les neutres que le
    gel lui donne deja, qui ATTENDENT avec elle), et lache les autres. Les copies C5 ne sont jamais touchees (elles se
    retirent a part, des deux cotes -- regle du 19/11). Un morceau a DEUX lignes n'est PAS touche : son verrou du point 3
    l'interdit, il remonte. Une piece qu'une ligne doit prendre est lachee par la ligne qui la tient (exclusivite)."""
    d = json.load((CACHE / "v3_calcul.json").open(encoding="utf-8"))
    maisons = json.load((CACHE / "v3_maisons.json").open(encoding="utf-8"))
    rj = json.load((CACHE / "v3_rejeu_maisons.json").open(encoding="utf-8"))
    ch3 = {int(a): c for a, c in rj["ch"].items()}
    gel, n_gel, emp = gel_complet()
    dire("GESTES : gel vivant %d liens, empreinte %s" % (n_gel, emp))
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(), uri=True)
    KIND = {int(a): k for a, k in con.execute("select app_affaire_id, kind from app_affaire_ledger")}
    ETATS = {int(a): s for a, s in con.execute("select app_affaire_id, state from app_affaire_ledger")}
    con.close()
    un_par_role = []
    loc = chaines_locales()
    photo = json.load((CACHE / "t6_photo.json").open(encoding="utf-8"))
    NUM = {i: v["num"] for i, v in photo["lignes"].items()}
    liens = defaultdict(set)
    tient = defaultdict(set)
    for i, a, *_ in gel:
        liens[i].add(a)
        tient[a].add(i)
    att_par_morceau = defaultdict(set)
    for a, (b, gl) in maisons.items():
        if gl and gl[0] != "SEULE_AVEC":
            att_par_morceau[(b, tuple(gl))].add(int(a))
    relier, delier, deux_lignes, exceptions, exc_a_decider = [], [], [], [], []
    for b, v in sorted(d["par_bien"].items(), key=lambda kv: int(kv[0])):
        for gl, ids in v["morceaux"]:
            if len(gl) > 1:
                w = EXCEPTIONS_NOMMEES.get((str(b), tuple(sorted(gl))))
                if not w:
                    deux_lignes.append((b, gl, ids))
                    continue
                # L'EXCEPTION NOMMEE (son mot du 22/11, point 3) : ses lignes, ENSEMBLE, tiennent les pieces du morceau.
                #   . une piece du morceau deja tenue par l'une de ses lignes : rien a faire (le gel n'a qu'UNE ligne
                #     par transaction -- on ne la recopie pas sur la jumelle) ;
                #   . une piece qu'aucune des deux ne tient : elle ME REMONTE (je ne choisis pas laquelle des deux) ;
                #   . une piece qu'une de ses lignes tient HORS du morceau : deliee, comme partout.
                exceptions.append((b, gl, ids, w))
                hk = {a for a in ids if a < 1000000}
                att = {a for a in att_par_morceau[(b, tuple(gl))]}
                for a in sorted(hk):
                    if not any(a in liens[i] for i in gl):
                        exc_a_decider.append((b, gl, a))
                for i in gl:
                    for a in sorted(x for x in liens[i] if x < 1000000 and x not in hk and x not in att):
                        delier.append((i, a, b, "pas dans son morceau (exception nommee)"))
                continue
            i = gl[0]
            hk = {a for a in ids if a < 1000000}
            garde = hk | {a for a in att_par_morceau[(b, tuple(gl))] if a in liens[i]}
            # UN LIEN PAR ROLE (le gel n'en a jamais deux aujourd'hui, mesure : 0 ligne) :
            #  . SA CONVENTION APRES RENEGOCIATION (20/11) -- le role « offre » tient l'offre ACCEPTEE ; l'offre d'origine
            #    reste dans le meme dossier (le morceau), sans lien ;
            #  . une COPIE C5 tient deja le role -> on ne relie pas la vraie piece par-dessus : les copies C5 se retirent
            #    a part, des deux cotes (regle du 19/11). Le dossier est le morceau dans les deux cas : l'etiquette est la meme.
            par_role = defaultdict(list)
            for a in hk | {x for x in liens[i] if x in garde or x >= 1000000}:
                par_role[KIND.get(a)].append(a)
            sans_lien = set()
            for role_, xs in par_role.items():
                if len(xs) < 2:
                    continue
                if any(x >= 1000000 and x in liens[i] for x in xs):
                    sans_lien |= {x for x in xs if x < 1000000 and x not in liens[i]}
                    continue
                acc = [x for x in xs if role_ == "offre" and ETATS.get(x) in ("accepted", "acceptee")]
                if role_ == "offre" and len(acc) == 1:
                    sans_lien |= {x for x in xs if x != acc[0] and x not in liens[i]}
            un_par_role.extend((i, a, b) for a in sorted(sans_lien))
            for a in sorted(hk - liens[i] - sans_lien):
                relier.append((i, a, b))
            for a in sorted(x for x in liens[i] if x < 1000000 and x not in garde):
                delier.append((i, a, b, "pas dans son morceau"))
    # l'exclusivite : une piece prise par une ligne est lachee par celle qui la tenait
    lachees = {(i, a) for i, a, *_ in delier}
    par_qui = []
    for i, a, b in relier + un_par_role:          # une piece du morceau d'une ligne n'est tenue par AUCUNE autre ligne
        for m in tient.get(a, set()) - {i}:
            if (m, a) not in lachees:
                delier.append((m, a, b, "lachee pour %s (exclusivite)" % i))
                lachees.add((m, a))
                par_qui.append((m, a, i))
    # le gel d'apres, et ses controles
    apres = defaultdict(set, {i: set(s) for i, s in liens.items()})
    for i, a, *_ in delier:
        apres[i].discard(a)
    for i, a, _b in relier:
        apres[i].add(a)
    tient2 = defaultdict(set)
    for i, s in apres.items():
        for a in s:
            tient2[a].add(i)
    doubles = sorted(a for a, s in tient2.items() if len(s) > 1)
    roles = defaultdict(Counter)
    for i, s in apres.items():
        for a in s:
            roles[i][KIND.get(a)] += 1
    touchees = {i for i, *_ in relier} | {i for i, *_ in delier}
    deux_roles = sorted((i, dict(c)) for i, c in roles.items() if i in touchees and any(n > 1 for n in c.values()))
    deux_roles_avant = sorted(i for i, c in roles.items() if i not in touchees and any(n > 1 for n in c.values()))
    sur_deux = sorted(i for i in touchees if len({ch3.get(a) for a in apres[i] if a in ch3}) > 1)
    p_avant, p_apres = lignes_partagees(liens, loc), lignes_partagees(apres, ch3)
    # LES EXCEPTIONS NOMMEES : sautees PAR LEUR NOM (jamais en silence) -- elles ne comptent pas comme un echec
    exc_avant = {c: (ls, exception_du_verrou(ls)) for c, ls in p_avant.items() if exception_du_verrou(ls)}
    exc_apres = {c: (ls, exception_du_verrou(ls)) for c, ls in p_apres.items() if exception_du_verrou(ls)}
    p_avant = {c: ls for c, ls in p_avant.items() if c not in exc_avant}
    p_apres = {c: ls for c, ls in p_apres.items() if c not in exc_apres}
    dire("   exceptions nommees : %d morceau(x) %s ; pieces qu'aucune de leurs lignes ne tient (a lui) : %s"
         % (len(exceptions), [(b, gl) for b, gl, _i, _w in exceptions], exc_a_decider))
    for c, (ls, w) in sorted(exc_apres.items()):
        dire("   ⭐ VERROU, SAUTEE EN LA NOMMANT : dossier %s, lignes %s -- %s" % (c, " ".join(sorted(ls)), w))
    n_av, n_ap = len(set().union(*p_avant.values())) if p_avant else 0, len(set().union(*p_apres.values())) if p_apres else 0
    dire("   relier %d . delier %d (dont %d pour l'exclusivite : %s) . morceaux a deux lignes, NON TOUCHES : %d %s"
         % (len(relier), len(delier), len(par_qui), par_qui[:6], len(deux_lignes), [(b, gl) for b, gl, _ in deux_lignes]))
    dire("   ⭐ exclusivite apres : transactions tenues par deux lignes : %d %s" % (len(doubles), doubles[:8]))
    dire("   ⭐ lignes touchees qui auraient deux liens d'un meme role : %d %s" % (len(deux_roles), deux_roles[:8]))
    dire("      (lignes NON touchees qui en ont deja deux aujourd'hui : %d -- hors V3, a part)" % len(deux_roles_avant))
    dire("   ⭐ lignes touchees dont les liens tombent sur deux dossiers apres la V3 : %d %s" % (len(sur_deux), sur_deux[:8]))
    dire("   ⭐ SON VERROU (deux de ses lignes sur un dossier) : aujourd'hui %d lignes sur %d dossiers ; apres la V3 %d "
         "lignes sur %d dossiers" % (n_av, len(p_avant), n_ap, len(p_apres)))
    neufs = sorted(set().union(*p_apres.values()) - set().union(*p_avant.values())) if p_apres else []
    gueris = sorted(set().union(*p_avant.values()) - set().union(*p_apres.values())) if p_avant else []
    dire("      que la V3 cree : %d %s ; que la V3 guerit : %d" % (len(neufs), neufs[:12], len(gueris)))
    ecrites = {i for i, v in d["sort_ligne"].items() if v[0] == "ECRITE"}
    bloquees = sorted(ecrites & set().union(*p_apres.values())) if p_apres else []
    dire("      ⛔ parmi les %d lignes « ecrites » d'ou ca tombe, SON VERROU en bloque %d : %s"
         % (len(ecrites), len(bloquees), bloquees))
    dire("   un lien par role : %d piece(s) restent dans le morceau SANS lien %s" % (len(un_par_role), un_par_role))
    json.dump({"relier": [(i, a, b, KIND.get(a), NUM.get(i)) for i, a, b in relier], "un_par_role": un_par_role,
               "delier": [(i, a, b, w, KIND.get(a)) for i, a, b, w in delier],
               "deux_lignes": deux_lignes, "doubles": doubles, "deux_roles": deux_roles, "sur_deux": sur_deux,
               "exceptions": [(b, gl, ids, w) for b, gl, ids, w in exceptions], "exc_a_decider": exc_a_decider,
               "exc_verrou_apres": {str(c): [sorted(ls), w] for c, (ls, w) in exc_apres.items()},
               "exc_verrou_avant": {str(c): [sorted(ls), w] for c, (ls, w) in exc_avant.items()},
               "partagees_avant": {str(c): sorted(l) for c, l in p_avant.items()},
               "partagees_apres": {str(c): sorted(l) for c, l in p_apres.items()},
               "bloquees": bloquees, "gel_n": n_gel, "gel_emp": emp,
               "gel_apres": {i: sorted(s) for i, s in apres.items()}},
              (CACHE / "v3_gestes.json").open("w", encoding="utf-8"))
    ok = not doubles and not deux_roles and not sur_deux and not exc_a_decider
    dire("GESTES : %s" % ("VERT" if ok else "⛔ A REGARDER"))
    return 0 if ok else 1


# ══ ecrit ══════════════════════════════════════════════════════════════════════════════════════════════════════════
COLS_APP = ("numero_facture_app", "vente_reglee_app", "honoraires_entree_app", "honoraires_sortie_app",
            "charge_commission_app", "date_annulation_app", "motif_annulation_app")


def purge_rejouee(rep: list, ch_apres: dict) -> dict:
    """app_repartition_purger_orphelines (lue en production le 22/11, empreinte D8), REJOUEE EN MEMOIRE sur des chaines
    donnees : d'abord chaque saisie orpheline rejoint le dossier que sa transaction porte ; elle S'ARRETE si ce dossier
    porte deja une part non-Hektor (« orphelines_en_conflit ») ; puis les derivees orphelines sont supprimees."""
    existe = set(ch_apres.values())
    non_hk = defaultdict(list)
    hk = defaultdict(list)
    for r in rep:
        (hk if (r["origine"] or "").startswith("hektor") else non_hk)[r["c"]].append(r)
    conflits, sans_tx, deplaces = [], [], []
    for ancien in sorted(c for c in list(non_hk) if c not in existe):
        nouveau = ch_apres.get(ancien)
        if nouveau is None:
            sans_tx.append(ancien)
            continue
        if non_hk.get(nouveau):
            conflits.append((ancien, nouveau))
            continue
        hk.pop(nouveau, None)
        non_hk[nouveau] = non_hk.pop(ancien)
        deplaces.append((ancien, nouveau, len(non_hk[nouveau])))
    gardees = sum(len(v) for c, v in non_hk.items() if c not in existe)
    return {"conflits": conflits, "sans_tx": sans_tx, "deplaces": deplaces, "gardees": gardees, "non_hk": non_hk}


def identiques(a: list, b: list) -> bool:
    cle = lambda r: sorted((r["cote"], r["rang"], (r["nom"] or "").strip().upper(), float(r["pct"] or 0)) for r in r_)  # noqa
    ka = sorted((r["cote"], r["rang"], (r["nom"] or "").strip().upper(), float(r["pct"] or 0)) for r in a)
    kb = sorted((r["cote"], r["rang"], (r["nom"] or "").strip().upper(), float(r["pct"] or 0)) for r in b)
    return ka == kb


def etape_ecrit() -> int:
    t0 = time.time()
    g = json.load((CACHE / "v3_gestes.json").open(encoding="utf-8"))
    rj = json.load((CACHE / "v3_rejeu_maisons.json").open(encoding="utf-8"))
    ch3 = {int(a): c for a, c in rj["ch"].items()}
    loc = chaines_locales()
    cn, cu = pooler()
    cu.execute("select app_affaire_id, app_chaine_id from app_affaire_ledger")
    sb = {int(a): int(c) for a, c in cu.fetchall()}
    ecart_sb = sum(1 for a in loc if sb.get(a) != loc[a])
    dire("ECRIT : chaines de la base locale contre Supabase : %d transactions differentes (attendu 0)" % ecart_sb)
    cu.execute("select app_chaine_id, cote, rang, nom_au_moment, pourcentage, origine from app_affaire_repartition")
    rep = [{"c": int(c), "cote": co, "rang": ra, "nom": no, "pct": pc, "origine": og} for c, co, ra, no, pc, og in cu.fetchall()]
    cu.execute("select app_affaire_id, %s from app_affaire_ledger where %s" % (
        ", ".join(COLS_APP), " or ".join("%s is not null" % c for c in COLS_APP)))
    vals = {int(r[0]): {c: v for c, v in zip(COLS_APP, r[1:]) if v is not None} for r in cu.fetchall()}
    cu.execute("select app_affaire_id, origine, left(texte, 80) from app_affaire_note where origine like 'classeur%%'")
    notes = defaultdict(list)
    for a, og, tx in cu.fetchall():
        notes[int(a)].append((og, tx))
    cn.rollback()
    cn.close()
    dire("   repartitions %d (origines %s) ; transactions portant une valeur posee %d ; portant une note du Sheet %d"
         % (len(rep), dict(Counter(r["origine"] for r in rep)), len(vals), len(notes)))
    # A. LA PURGE DE NUIT, sans la V3 (temoin : ses 13 conflits) puis avec
    sans = purge_rejouee(rep, sb)
    avec = purge_rejouee(rep, ch3)
    dire("   A. PURGE REJOUEE SANS LA V3 (la nuit de ce soir telle qu'elle est) : conflits %d, sans transaction %d, "
         "deplaces %d, saisies orphelines gardees %d" % (len(sans["conflits"]), len(sans["sans_tx"]), len(sans["deplaces"]),
                                                       sans["gardees"]))
    dire("      ⭐ TEMOIN POSITIF : ses 13 conflits (3670 -> 3669, 14034 -> 14033...) : %s" % sans["conflits"])
    dire("   A. PURGE REJOUEE AVEC LA V3 : conflits %d, sans transaction %d, deplaces %d, saisies orphelines gardees %d"
         % (len(avec["conflits"]), len(avec["sans_tx"]), len(avec["deplaces"]), avec["gardees"]))
    neufs = sorted(set(map(tuple, avec["conflits"])) - set(map(tuple, sans["conflits"])))
    finis = sorted(set(map(tuple, sans["conflits"])) - set(map(tuple, avec["conflits"])))
    dire("      conflits que la V3 CREE : %d %s" % (len(neufs), neufs))
    dire("      conflits que la V3 fait TOMBER : %d %s" % (len(finis), finis))
    par_c = defaultdict(list)
    for r in rep:
        if not (r["origine"] or "").startswith("hektor"):
            par_c[r["c"]].append(r)
    for nom, res in (("sans", sans), ("avec", avec)):
        idt = [(a, n) for a, n in res["conflits"] if identiques(par_c[a], par_c[n])]
        dif = [(a, n) for a, n in res["conflits"] if not identiques(par_c[a], par_c[n])]
        dire("      %s la V3 -- paires IDENTIQUES (nom, %%, cote, rang) : %d ; DIFFERENTES : %d %s" % (
            nom, len(idt), len(dif), [(a, n, [(r["cote"], r["nom"], r["pct"]) for r in par_c[a]],
                                       [(r["cote"], r["nom"], r["pct"]) for r in par_c[n]]) for a, n in dif]))
    # B. LES REPARTITIONS QUI RESTENT EN PLACE MAIS CHANGENT DE LIGNE (silencieuses)
    liens_av = defaultdict(set)
    gel, _n, _e = gel_complet()
    for i, a, *_ in gel:
        liens_av[i].add(a)
    liens_ap = {i: set(s) for i, s in g["gel_apres"].items()}
    def lignes_du(ch, liens):
        par = defaultdict(set)
        for i, s in liens.items():
            for a in s:
                if a in ch:
                    par[ch[a]].add(i)
        return par
    L_av, L_ap = lignes_du(sb, liens_av), lignes_du(ch3, liens_ap)
    deplace_vers = {a: n for a, n, _k in avec["deplaces"]}
    silencieuses = []
    for c, rs in par_c.items():
        if not any(r["origine"] == "classeur_reconstitue" for r in rs):
            continue
        c2 = deplace_vers.get(c, c)
        if c2 not in set(ch3.values()):
            continue                       # orpheline : comptee en A
        if L_av.get(c) and L_ap.get(c2) is not None and not (L_av[c] & L_ap.get(c2, set())):
            silencieuses.append((c, c2, sorted(L_av[c]), sorted(L_ap.get(c2, set()))))
        elif L_av.get(c) and not L_ap.get(c2):
            silencieuses.append((c, c2, sorted(L_av[c]), []))
    sil_sans_v3 = []
    dire("   B. repartitions du classeur qui RESTENT sur un dossier dont leur ligne est partie (indetectables) : %d dossiers"
         " %s" % (len(silencieuses), silencieuses[:10]))
    # C/D. LES VALEURS POSEES ET LES NOTES DU SHEET dont la transaction change de ligne
    tient_av, tient_ap = defaultdict(set), defaultdict(set)
    for i, s in liens_av.items():
        for a in s:
            tient_av[a].add(i)
    for i, s in liens_ap.items():
        for a in s:
            tient_ap[a].add(i)
    bougent = sorted(a for a in set(tient_av) | set(tient_ap) if tient_av.get(a, set()) != tient_ap.get(a, set()))
    v_b = [(a, sorted(tient_av.get(a, [])), sorted(tient_ap.get(a, [])), vals[a]) for a in bougent if a in vals]
    n_b = [(a, sorted(tient_av.get(a, [])), sorted(tient_ap.get(a, [])), notes[a]) for a in bougent if a in notes]
    dire("   C. transactions dont la ligne change par le gel V3 : %d ; dont portant une VALEUR posee : %d ; une NOTE du "
         "Sheet : %d" % (len(bougent), len(v_b), len(n_b)))
    for x in v_b:
        dire("      valeur  %s" % (x,))
    for x in n_b:
        dire("      note    %d %s -> %s : %s" % (x[0], x[1], x[2], [(o, t[:50]) for o, t in x[3]]))
    json.dump({"sans": {k: v for k, v in sans.items() if k != "non_hk"}, "avec": {k: v for k, v in avec.items() if k != "non_hk"},
               "neufs": neufs, "finis": finis, "silencieuses": silencieuses, "valeurs": v_b,
               "notes": [(a, x, y, z) for a, x, y, z in n_b]},
              (CACHE / "v3_ecritures.json").open("w", encoding="utf-8"), ensure_ascii=False, default=str)
    dire("ECRIT : FIN (%.0f s)" % (time.time() - t0))
    return 0


# ══ patch ══════════════════════════════════════════════════════════════════════════════════════════════════════════
PATCH = RACINE / "supabase" / "patch_gel_v3_ou_ca_tombe_2026-11-22.sql"
SAUVEGARDE = "app_classeur_lien_avant_v3_20261122"
GELE_PAR = "v3_ou_ca_tombe_2026-11-22"
ETAGE = "preuve interne 20-22/11"


def q(s: str) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def etape_patch() -> int:
    g = json.load((CACHE / "v3_gestes.json").open(encoding="utf-8"))
    d = json.load((CACHE / "v3_calcul.json").open(encoding="utf-8"))
    convention = {a for a, _c in d["par_chaine"]} | {a for a, _o in d["par_renego"]}
    gel, n_gel, emp = gel_complet()
    if n_gel != g["gel_n"] or emp != g["gel_emp"]:
        dire("PATCH : ⛔ le gel a bouge depuis le calcul des gestes (%d %s) -- refaire « gestes »" % (n_gel, emp))
        return 1
    role_de = {(i, a): ro for i, a, ro, *_ in gel}
    ret = [(i, a, role_de[(i, a)]) for i, a, _b, _w, _k in g["delier"]]
    aj = [(i, a, k, num, "bonne" if a in convention else "sûre", 1 if a in convention else 2)
          for i, a, _b, k, num in g["relier"]]
    n_apres = n_gel - len(ret) + len(aj)
    # LES DEUX TEMOINS NOMMES (son mot du 22/11, point 2) : ils doivent etre DANS le lot, et HORS des gestes a sa decision
    if TEMOIN_RELIER not in {(i, a) for i, a, *_ in aj} or TEMOIN_DELIER not in {(i, a) for i, a, _r in ret}:
        dire("PATCH : ⛔ un temoin nomme n'est plus dans le lot (%s / %s) -- refaire le choix" % (TEMOIN_RELIER, TEMOIN_DELIER))
        return 1
    if {TEMOIN_RELIER, TEMOIN_DELIER} & GESTES_A_SA_DECISION:
        dire("PATCH : ⛔ un temoin porte sur un geste a sa decision")
        return 1
    a_sa_decision = sorted({(i, a) for i, a, *_ in aj} | {(i, a) for i, a, _r in ret} & GESTES_A_SA_DECISION)
    a_sa_decision = sorted(x for x in a_sa_decision if x in GESTES_A_SA_DECISION)
    v_ret = ",\n".join("    (%s, %d, %s)" % (q(i), a, q(r)) for i, a, r in sorted(ret))
    v_aj = ",\n".join("    (%s, %d, %s)" % (q(i), a, q(k)) for i, a, k, *_ in sorted(aj))
    lignes_ins = ",\n".join("    (%d, %d, %s, %s, %d, %s, now(), %s, %s)" % (num, a, q(k), q(cf), pr, q(ETAGE), q(GELE_PAR), q(i))
                            for i, a, k, num, cf, pr in sorted(aj))
    entete = """-- ════════════════════════════════════════════════════════════════════════════════════════════════
-- LE GEL V3 -- « OU CA TOMBE », A PART RESTREINTE AUX 20                                     22/11/2026
-- ════════════════════════════════════════════════════════════════════════════════════════════════
-- ⛔ DORMANT : il ne se joue qu'avec le « vas-y » explicite de Frederic, dans la conversation.
-- ⛔⛔ IL PORTE SON `commit;` : joue « pour voir », IL SE COMMITE. La repetition a blanc est un AUTRE fichier
--   (..._A_BLANC.sql, qui finit par rollback).
-- SOURCE : phase2/checks/temps12_v3_fabriquer_2026-11-22.py (etapes calcul, maisons, rejeu, gestes, patch) --
--   ne pas le retoucher a la main. « Ou ca tombe » refait sur la base du 22/11 : 0 ligne dont le sort change.
-- CE QU'IL FAIT : %d liens RETIRES . %d liens AJOUTES . le gel passe de %d a %d.
--   . une ligne tient les pieces que la PREUVE INTERNE lui donne (date au jour exact, ou prix + honoraires) ;
--   . les 20 pieces dont la place bouge une etiquette sont lachees (A PART) ; les 20 neutres ATTENDENT ou elles
--     sont (le gel les garde quand il les donne deja a la ligne de leur morceau) ;
--   . UN LIEN PAR ROLE : le role « offre » tient l'offre ACCEPTEE (sa convention du 20/11) ; une copie C5 qui tient
--     deja un role n'est pas doublee (les copies se retirent a part) ;
--   . LES JUMELLES, EXCEPTION NOMMEE (son mot du 22/11, point 3) : VIALLARD (bien 9748, lignes 3308P0UX et YRUF0S9H) et
--     PAOLONE (bien 41467, lignes O6R10ZQA et T2GZOY5O) s'ecrivent ; leurs lignes tiennent DEJA leurs pieces -- le gel
--     n'a qu'une ligne par transaction, il ne les recopie pas sur la jumelle ;
--   . ⛔ A SA DECISION, PAS ENCORE VALIDES (son mot du 22/11, point 2) : @@A_SA_DECISION@@
--     -- s'il les refuse, le patch est refabrique sans eux ; il ne se joue pas avant son mot ;
--   . LES TEMOINS (son mot du 22/11, point 2) : NOMMES, hors de ces gestes-la -- @@TEMOINS@@.
-- CE QU'IL NE FAIT PAS : il ne touche NI le chainage (c'est le fichier des detachements V3 + G2, sur le meme
--   « vas-y »), NI les ecritures rapatriees (repartitions, factures, reglements, notes : mesurees, a part), NI Hektor.
-- RETOUR ARRIERE : patch_gel_v3_ou_ca_tombe_2026-11-22_INVERSE.sql
-- CONTROLE       : patch_gel_v3_ou_ca_tombe_2026-11-22_REPETITION.sql (lecture seule)
-- ════════════════════════════════════════════════════════════════════════════════════════════════
""" % (len(ret), len(aj), n_gel, n_apres)
    entete = entete.replace("@@A_SA_DECISION@@", " ; ".join("%s %d" % x for x in a_sa_decision) or "aucun").replace(
        "@@TEMOINS@@", "%s tient %d ; %s ne tient plus %d" % (TEMOIN_RELIER + TEMOIN_DELIER))
    corps = """begin;

-- ── ① LA GARDE : le gel est EXACTEMENT celui que le calcul a lu ─────────────────────────────────
do $$
declare n int; emp text; manque int; cible_ko int; deja int;
begin
  select count(*), md5(string_agg(id_unique||':'||app_affaire_id||':'||role, ','
                                  order by id_unique collate "C", app_affaire_id))
    into n, emp from app_classeur_lien;
  if n <> %(n)d or emp <> %(emp)s then
    raise exception '⛔ garde : le gel a bouge (%% liens, empreinte %%) -- rien n''est ecrit', n, emp;
  end if;
  if to_regclass('public.%(sauve)s') is not null then
    raise exception '⛔ garde : la sauvegarde %(sauve)s existe deja -- ce patch a-t-il deja ete joue ?';
  end if;
  select count(*) into manque from (values
%(ret)s
  ) v(id_unique, app_affaire_id, role)
  where not exists (select 1 from app_classeur_lien l where l.id_unique = v.id_unique
                       and l.app_affaire_id = v.app_affaire_id and l.role = v.role);
  if manque <> 0 then raise exception '⛔ garde : %% lien(s) a retirer introuvable(s)', manque; end if;
  select count(*) into cible_ko from (values
%(aj)s
  ) v(id_unique, app_affaire_id, role)
  left join app_affaire_ledger a on a.app_affaire_id = v.app_affaire_id
  where a.app_affaire_id is null or a.kind <> v.role;
  if cible_ko <> 0 then raise exception '⛔ garde : %% cible(s) absente(s) du registre ou d''un autre genre', cible_ko; end if;
  select count(*) into deja from (values
%(aj)s
  ) v(id_unique, app_affaire_id, role)
  join app_classeur_lien l on l.app_affaire_id = v.app_affaire_id and l.id_unique <> v.id_unique
  where not exists (select 1 from (values
%(ret)s
    ) r(id_unique, app_affaire_id, role)
    where r.id_unique = l.id_unique and r.app_affaire_id = l.app_affaire_id);
  if deja <> 0 then raise exception '⛔ garde : %% cible(s) tenue(s) par une autre ligne qui ne la lache pas', deja; end if;
end $$;

-- ── ② LA SAUVEGARDE DATEE, FERMEE DES SA NAISSANCE ─────────────────────────────────────────────
create table %(sauve)s as select * from app_classeur_lien;
revoke all on %(sauve)s from public, anon, authenticated;
alter table %(sauve)s enable row level security;

-- ── ③ RETIRER (%(nret)d) ──────────────────────────────────────────────────────────────────────
delete from app_classeur_lien l
 using (values
%(ret)s
 ) v(id_unique, app_affaire_id, role)
 where l.id_unique = v.id_unique and l.app_affaire_id = v.app_affaire_id and l.role = v.role;

-- ── ④ AJOUTER (%(naj)d) ───────────────────────────────────────────────────────────────────────
insert into app_classeur_lien
  (ligne_classeur, app_affaire_id, role, confiance, preuves, etage, gele_le, gele_par, id_unique)
values
%(ins)s;

-- ── ⑤ LE CONTROLE, DANS LA MEME TRANSACTION ───────────────────────────────────────────────────
do $$
declare n int; doubles int; deux_roles int; poses int; restes int; garde int; temoin int;
begin
  select count(*) into n from app_classeur_lien;
  if n <> %(napres)d then raise exception '⛔ le gel porte %% liens, attendu %(napres)d', n; end if;
  select count(*) into doubles from (select app_affaire_id from app_classeur_lien
                                      group by 1 having count(distinct id_unique) > 1) x;
  if doubles <> 0 then raise exception '⛔ %% transaction(s) prises par deux lignes', doubles; end if;
  select count(*) into deux_roles from (select id_unique, role from app_classeur_lien
                                         group by 1, 2 having count(*) > 1) x;
  if deux_roles <> 0 then raise exception '⛔ %% ligne(s) a deux liens pour un meme role', deux_roles; end if;
  select count(*) into poses from app_classeur_lien where gele_par = %(gp)s;
  if poses <> %(naj)d then raise exception '⛔ %% lien(s) poses, attendu %(naj)d', poses; end if;
  select count(*) into restes from app_classeur_lien l join (values
%(ret)s
  ) v(id_unique, app_affaire_id, role) on l.id_unique = v.id_unique and l.app_affaire_id = v.app_affaire_id;
  if restes <> 0 then raise exception '⛔ %% lien(s) a retirer encore presents', restes; end if;
  select count(*) into garde from %(sauve)s;
  if garde <> %(n)d then raise exception '⛔ sauvegarde : %% au lieu de %(n)d', garde; end if;
  select count(*) into temoin from app_classeur_lien l
    join %(sauve)s s using (id_unique, app_affaire_id)
   where (l.role, l.confiance, l.preuves, l.etage, l.gele_par, l.ligne_classeur, l.gele_le)
         is distinct from (s.role, s.confiance, s.preuves, s.etage, s.gele_par, s.ligne_classeur, s.gele_le);
  if temoin <> 0 then raise exception '⛔ temoin inverse : %% lien(s) non vise(s) ont change', temoin; end if;
  -- LES DEUX TEMOINS POSITIFS NOMMES (son mot du 22/11, point 2) : pris dans les gestes qu'il a vus, un par sens
  select count(*) into temoin from app_classeur_lien where id_unique = %(tr_i)s and app_affaire_id = %(tr_a)d;
  if temoin <> 1 then raise exception '⛔ temoin positif : %(tr_i_)s ne tient pas %(tr_a)d (%% lien)', temoin; end if;
  select count(*) into temoin from app_classeur_lien where id_unique = %(td_i)s and app_affaire_id = %(td_a)d;
  if temoin <> 0 then raise exception '⛔ temoin positif : %(td_i_)s tient encore %(td_a)d (%% lien)', temoin; end if;
  raise notice '✅ gel V3 : -%(nret)d +%(naj)d = %(napres)d liens, exclusivite tenue, un lien par role, voisins intacts, temoins nommes verts.';
end $$;
""" % {"n": n_gel, "emp": q(emp), "sauve": SAUVEGARDE, "ret": v_ret, "aj": v_aj, "ins": lignes_ins,
       "nret": len(ret), "naj": len(aj), "napres": n_apres, "gp": q(GELE_PAR),
       "tr_i": q(TEMOIN_RELIER[0]), "tr_i_": TEMOIN_RELIER[0], "tr_a": TEMOIN_RELIER[1],
       "td_i": q(TEMOIN_DELIER[0]), "td_i_": TEMOIN_DELIER[0], "td_a": TEMOIN_DELIER[1]}
    PATCH.write_text(entete + corps + "\ncommit;\n", encoding="utf-8", newline="\n")
    blanc = PATCH.with_name(PATCH.stem + "_A_BLANC.sql")
    blanc.write_text(entete.replace("-- ⛔ DORMANT", "-- ⭐ REPETITION A BLANC : le patch ENTIER, puis ROLLBACK -- il ne laisse rien.\n-- ⛔ DORMANT")
                     + corps + "\nrollback;\n", encoding="utf-8", newline="\n")
    inverse = """-- RETOUR ARRIERE DU GEL V3 (22/11/2026) -- il ne juge que SA part (lecon 31).
begin;
do $$
declare n int;
begin
  if to_regclass('public.%(sauve)s') is null then raise exception '⛔ pas de sauvegarde %(sauve)s : le patch n''a pas ete joue'; end if;
  select count(*) into n from app_classeur_lien where gele_par = %(gp)s;
  if n <> %(naj)d then raise exception '⛔ %% lien(s) du patch trouves, attendu %(naj)d -- quelqu''un est passe apres', n; end if;
end $$;
delete from app_classeur_lien where gele_par = %(gp)s;
insert into app_classeur_lien
select s.* from %(sauve)s s
  join (values
%(ret)s
  ) v(id_unique, app_affaire_id, role) on s.id_unique = v.id_unique and s.app_affaire_id = v.app_affaire_id and s.role = v.role;
do $$
declare n int; emp text;
begin
  select count(*), md5(string_agg(id_unique||':'||app_affaire_id||':'||role, ','
                                  order by id_unique collate "C", app_affaire_id)) into n, emp from app_classeur_lien;
  if n <> %(n)d or emp <> %(emp)s then raise exception '⛔ inverse : le gel ne revient pas a l''etat d''avant (%% %%)', n, emp; end if;
  raise notice '✅ gel revenu a %(n)d liens, empreinte d''avant. La sauvegarde %(sauve)s est gardee.';
end $$;
commit;
""" % {"sauve": SAUVEGARDE, "gp": q(GELE_PAR), "naj": len(aj), "ret": v_ret, "n": n_gel, "emp": q(emp)}
    PATCH.with_name(PATCH.stem + "_INVERSE.sql").write_text(inverse, encoding="utf-8", newline="\n")
    repet = """-- CONTROLE DU GEL V3 (lecture seule) -- a coller APRES le patch. Chaque ligne doit dire OK.
select 'liens' controle, count(*)::text valeur, case when count(*) = %(napres)d then 'OK' else 'ROUGE' end from app_classeur_lien
union all select 'poses par la V3', count(*)::text, case when count(*) = %(naj)d then 'OK' else 'ROUGE' end from app_classeur_lien where gele_par = %(gp)s
union all select 'tenues par deux lignes', count(*)::text, case when count(*) = 0 then 'OK' else 'ROUGE' end
  from (select app_affaire_id from app_classeur_lien group by 1 having count(distinct id_unique) > 1) x
union all select 'deux liens pour un role', count(*)::text, case when count(*) = 0 then 'OK' else 'ROUGE' end
  from (select id_unique, role from app_classeur_lien group by 1, 2 having count(*) > 1) x
union all select 'sauvegarde', count(*)::text, case when count(*) = %(n)d then 'OK' else 'ROUGE' end from %(sauve)s
union all select 'temoin positif : ' || %(t_id)s || ' tient ' || %(t_a)s, count(*)::text, case when count(*) = 1 then 'OK' else 'ROUGE' end
  from app_classeur_lien where id_unique = %(t_id)s and app_affaire_id = %(t_a)s
union all select 'temoin positif : ' || %(d_id)s || ' ne tient plus ' || %(d_a)s, count(*)::text, case when count(*) = 0 then 'OK' else 'ROUGE' end
  from app_classeur_lien where id_unique = %(d_id)s and app_affaire_id = %(d_a)s;
""" % {"napres": n_apres, "naj": len(aj), "gp": q(GELE_PAR), "n": n_gel, "sauve": SAUVEGARDE,
       "t_id": q(TEMOIN_RELIER[0]), "t_a": TEMOIN_RELIER[1], "d_id": q(TEMOIN_DELIER[0]), "d_a": TEMOIN_DELIER[1]}
    PATCH.with_name(PATCH.stem + "_REPETITION.sql").write_text(repet, encoding="utf-8", newline="\n")
    dire("PATCH : %s (+ _A_BLANC, _INVERSE, _REPETITION) -- retirer %d, ajouter %d, gel %d -> %d"
         % (PATCH.name, len(ret), len(aj), n_gel, n_apres))
    return 0


def etape_blanc() -> int:
    """LA REPETITION A BLANC (son point 1-A) : le patch ENTIER dans une transaction, puis ROLLBACK. Temoin : apres, le
    gel a son empreinte d'avant et la sauvegarde n'existe pas."""
    import psycopg2
    from phase2.sync import push_upgrade_to_supabase as PU
    PU.load_env_files(PU.DEFAULT_ENV_FILES)
    u = urllib.parse.urlparse(os.environ["DATABASE_URL"])
    texte = PATCH.with_name(PATCH.stem + "_A_BLANC.sql").read_text(encoding="utf-8")
    assert texte.rstrip().endswith("rollback;") and "\ncommit;" not in texte, "le fichier a blanc porte un commit"
    corps = texte.split("begin;", 1)[1].rsplit("rollback;", 1)[0]
    cn = psycopg2.connect(host=os.environ["SUPABASE_POOLER_HOST"], port=5432, dbname="postgres",
                          user="postgres.dwaqxfrinihnychuoptk", password=urllib.parse.unquote(u.password),
                          connect_timeout=15, sslmode="require")
    cn.autocommit = False
    cu = cn.cursor()
    notes = []
    try:
        cu.execute(corps)
        notes = [x.strip() for x in cn.notices]
        verdict = "le patch est passe JUSQU'AU BOUT (garde, sauvegarde, retirer, ajouter, controle)"
    except Exception as e:  # noqa: BLE001
        verdict = "⛔ le patch S'EST ARRETE : %s" % str(e).splitlines()[0]
    finally:
        cn.rollback()
    cu.execute("set transaction read only")
    cu.execute("select count(*), md5(string_agg(id_unique||':'||app_affaire_id||':'||role, ',' order by id_unique "
               "collate \"C\", app_affaire_id)), to_regclass('public.%s') is null from app_classeur_lien" % SAUVEGARDE)
    n, emp, pas_de_sauvegarde = cu.fetchone()
    cn.rollback()
    cn.close()
    g = json.load((CACHE / "v3_gestes.json").open(encoding="utf-8"))
    intact = n == g["gel_n"] and emp == g["gel_emp"] and pas_de_sauvegarde
    dire("A BLANC : %s ; notices : %s" % (verdict, notes[-2:]))
    dire("   ⭐ TEMOIN : apres le rollback, le gel a %d liens, empreinte %s, sauvegarde absente : %s -> %s"
         % (n, emp, pas_de_sauvegarde, "RIEN N'EST RESTE" if intact else "⛔ QUELQUE CHOSE EST RESTE"))
    return 0 if intact and "JUSQU'AU BOUT" in verdict else 1


# ══ rapport ════════════════════════════════════════════════════════════════════════════════════════════════════════
# 22/11 nuit : TEMPS12_LA_V3_FABRIQUEE_2026-11-22.csv (celle qu'il a lue, gardee telle quelle) ; 22/11 matin, apres son
# mot du 22/11 (jumelles en exception nommee, temoins nommes, base du 22/11 apres la nuit) : la V3 REFAITE.
SORTIE_CSV = NOTICE / "TEMPS13_LA_V3_REFAITE_2026-11-22.csv"


def etape_rapport() -> int:
    """Le CSV qu'il lit piece par piece : les 40 pieces sans preuve (avec SA colonne : a part ou elles attendent), les
    gestes du gel, les conflits de la purge, les ecritures qui changent de ligne, et les 25 de la correction 3."""
    d = json.load((CACHE / "v3_calcul.json").open(encoding="utf-8"))
    m = json.load((CACHE / "v3_maisons.json").open(encoding="utf-8"))
    g = json.load((CACHE / "v3_gestes.json").open(encoding="utf-8"))
    e = json.load((CACHE / "v3_ecritures.json").open(encoding="utf-8"))
    rj = json.load((CACHE / "v3_rejeu_maisons.json").open(encoding="utf-8"))
    ch3 = {int(a): c for a, c in rj["ch"].items()}
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(), uri=True)
    INFO = {int(a): (k, s, mt) for a, k, s, mt in con.execute("select app_affaire_id, kind, state, montant from app_affaire_ledger")}
    con.close()
    photo = json.load((CACHE / "t6_photo.json").open(encoding="utf-8"))
    NUM = {i: v["num"] for i, v in photo["lignes"].items()}
    # G2 seule, pour separer ce que fait G2 de ce que fait le fichier V3
    mod = T10.charger(T10.MODULE, "apres")
    ch_g2, _r, _c = T10.rejouer(mod, {"APP_CHAINAGE_GARDE_G2": "1", "APP_CHAINAGE_DETACHEMENTS": "0"})
    loc = chaines_locales()
    g2_bouge = sum(1 for a in loc if ch_g2.get(a) != loc[a])
    v3_bouge = sum(1 for a in ch3 if ch3[a] != ch_g2.get(a))
    dire("RAPPORT : dossiers production %d -> G2 seule %d -> G2 + V3 %d ; transactions qui changent de dossier : par G2 %d, "
         "puis par le fichier V3 %d" % (len(set(loc.values())), len(set(ch_g2.values())), len(set(ch3.values())),
                                         g2_bouge, v3_bouge))
    # les 25 de la correction 3 : la proposition
    cn, cu = pooler()
    cu.execute("""with avant as (select id_unique, app_affaire_id from app_classeur_lien_avant_audit_v2_20261119),
      partis as (select a.* from avant a where not exists (select 1 from app_classeur_lien m
                  where m.id_unique = a.id_unique and m.app_affaire_id = a.app_affaire_id))
      select p.app_affaire_id, p.id_unique, l.kind,
        concat_ws(' | ', 'facture='||l.numero_facture_app, 'reglee='||l.vente_reglee_app, 'hon_entree='||l.honoraires_entree_app,
                  'hon_sortie='||l.honoraires_sortie_app, 'charge='||l.charge_commission_app, 'annulee_le='||l.date_annulation_app,
                  'motif='||l.motif_annulation_app),
        (select string_agg(n.origine||' : '||left(replace(n.texte, chr(10), ' / '), 100), ' || ') from app_affaire_note n
          where n.app_affaire_id = p.app_affaire_id and n.origine like 'classeur%%')
      from partis p join app_affaire_ledger l on l.app_affaire_id = p.app_affaire_id
      where coalesce(l.numero_facture_app, l.vente_reglee_app, l.honoraires_entree_app::text, l.honoraires_sortie_app::text,
                     l.charge_commission_app::text, l.date_annulation_app::text, l.motif_annulation_app) is not null
         or exists (select 1 from app_affaire_note n where n.app_affaire_id = p.app_affaire_id and n.origine like 'classeur%%')
      order by 1""")
    vingt5 = cu.fetchall()
    cn.rollback()
    cn.close()
    gel_ap = {i: set(s) for i, s in g["gel_apres"].items()}
    tient_ap = defaultdict(set)
    for i, s in gel_ap.items():
        for a in s:
            tient_ap[a].add(i)
    lignes25 = []
    for a, ancienne, kind, valeurs, notes in vingt5:
        now = sorted(tient_ap.get(a, set()))
        meme_role = sorted(x for x in gel_ap.get(ancienne, set()) if INFO.get(x, ("",))[0] == kind)
        if a >= 1000000:
            prop = "copie C5 : sa note est celle de la copie -- elle part AVEC la copie quand on retire les copies (regle du 19/11)"
        elif len(meme_role) == 1:
            prop = "DEPLACER vers %d (le %s que la ligne %s tient aujourd'hui, et tient encore apres la V3)" % (
                meme_role[0], kind, ancienne)
        elif not meme_role:
            prop = "LAISSER (la ligne %s n'a plus de %s : aucune place juste ou la mettre) -- a toi" % (ancienne, kind)
        else:
            prop = "a toi : la ligne %s tient %d %s" % (ancienne, len(meme_role), kind)
        lignes25.append((a, ancienne, NUM.get(ancienne), " ".join(now) or "aucune", kind,
                         (valeurs or "").replace("facture=", "facture ").strip(), notes or "", prop))
    with SORTIE_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["partie", "bien", "transaction", "genre", "etat", "montant", "ligne du Sheet", "numero de ligne",
                    "ce qui arrive", "pourquoi", "sa colonne : la place bouge une etiquette ?"])
        for b, a, why in d["a20"]:
            k, s, mt = INFO.get(a, ("", "", ""))
            w.writerow(["sans preuve", b, a, k, s, mt, "", "", "A PART (seule, un dossier a elle)", why, "OUI -- a part"])
        for b, a, why in d["n19"]:
            k, s, mt = INFO.get(a, ("", "", ""))
            h = m.get(str(a))
            if h and h[1][0] == "SEULE_AVEC":
                ou = "ATTEND seule, avec sa ligne %s (qui n'a aucun morceau)" % " ".join(h[1][1:])
            elif h:
                ou = "ATTEND dans le morceau de %s" % " ".join(h[1])
            else:
                ou = "ATTEND dans son dossier d'aujourd'hui (%d), tel quel" % loc.get(a, 0)
            w.writerow(["sans preuve", b, a, k, s, mt, "", "", ou, why, "NON -- elle attend"])
        marque = lambda i, a: ("A TA DECISION (ton mot du 22/11, point 2)" if (i, a) in GESTES_A_SA_DECISION  # noqa: E731
                               else "TEMOIN NOMME du patch" if (i, a) in (TEMOIN_RELIER, TEMOIN_DELIER) else "")
        for i, a, b, k, num in g["relier"]:
            w.writerow(["gel V3 : relier", b, a, k, INFO.get(a, ("", ""))[1], INFO.get(a, ("", "", ""))[2], i, num,
                        "relier", "la preuve interne la donne a cette ligne", marque(i, a)])
        for i, a, b, why, k in g["delier"]:
            w.writerow(["gel V3 : delier", b, a, k, INFO.get(a, ("", ""))[1], INFO.get(a, ("", "", ""))[2], i, NUM.get(i),
                        "delier", why, marque(i, a)])
        for b, gl, ids, why in g.get("exceptions", []):
            w.writerow(["EXCEPTION NOMMEE (ton mot du 22/11, point 3)", b, " ".join(map(str, ids)), "", "", "",
                        " ".join(gl), " ".join(str(NUM.get(x)) for x in gl), "un dossier pour ses deux lignes, ecrites toutes les deux",
                        why, "le controle « deux lignes sur un dossier » la SAUTE EN LA NOMMANT"])
        for i, a, b in g["un_par_role"]:
            w.writerow(["gel V3 : reste sans lien", b, a, INFO.get(a, ("",))[0], INFO.get(a, ("", ""))[1],
                        INFO.get(a, ("", "", ""))[2], i, NUM.get(i), "dans le dossier de la ligne, sans lien",
                        "un lien par role (sa convention apres renegociation, ou une copie C5 tient deja le role)", ""])
        for nom in ("sans", "avec"):
            for a, n in e[nom]["conflits"]:
                w.writerow(["purge de nuit %s la V3" % nom, "", a, "", "", "", "", "", "orpheline en conflit -> dossier %d" % n,
                            "le dossier d'arrivee porte deja une part non-Hektor", ""])
        for c, c2, la, lp in e["silencieuses"]:
            w.writerow(["repartition qui reste sans sa ligne", "", c, "", "", "", " ".join(la), " ".join(str(NUM.get(x)) for x in la),
                        "reste sur le dossier %d" % c2, "lignes de ce dossier apres la V3 : %s" % (" ".join(lp) or "aucune"), ""])
        for a, av, ap, vals in e["valeurs"]:
            w.writerow(["valeur posee qui change de ligne", "", a, INFO.get(a, ("",))[0], "", "", " ".join(av),
                        " ".join(str(NUM.get(x)) for x in av), "ligne apres la V3 : %s" % (" ".join(ap) or "aucune"),
                        " | ".join("%s=%s" % kv for kv in vals.items()), ""])
        for a, av, ap, ns in e["notes"]:
            w.writerow(["note du Sheet qui change de ligne", "", a, INFO.get(a, ("",))[0], "", "", " ".join(av),
                        " ".join(str(NUM.get(x)) for x in av), "ligne apres la V3 : %s" % (" ".join(ap) or "aucune"),
                        " || ".join("%s : %s" % (o, t) for o, t in ns), ""])
        for a, anc, num, now, kind, vals, notes, prop in lignes25:
            w.writerow(["correction 3 (V2) : les 25", "", a, kind, "", "", anc, num, prop,
                        ("valeur : " + vals if vals else "") + (" ; note : " + notes if notes else ""),
                        "tenue aujourd'hui par : " + now])
    dire("RAPPORT : %s -- 40 pieces, %d gestes, les 25 : %d (%s)" % (
        SORTIE_CSV.name, len(g["relier"]) + len(g["delier"]), len(lignes25),
        dict(Counter(p.split(" ")[0] for *_x, p in lignes25))))
    for x in lignes25:
        dire("   25 : %s" % (x,))
    return 0


if __name__ == "__main__":
    etape = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit({"s": etape_s, "calcul": etape_calcul, "rejeu": etape_rejeu, "maisons": etape_maisons,
              "gestes": etape_gestes, "ecrit": etape_ecrit, "patch": etape_patch, "blanc": etape_blanc,
              "rapport": etape_rapport}.get(
        etape, lambda: (print(__doc__), 3)[1])())
