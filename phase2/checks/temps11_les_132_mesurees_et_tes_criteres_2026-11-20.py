"""Chantier classeur, ⑰ -- LES 132 COUPES MESUREES PIECE PAR PIECE, L'OUTIL DE COUPE CORRIGE ET SON TEMOIN, SES DEUX
CRITERES APPLIQUES PARTOUT, LES LIGNES OUBLIEES.

LECTURE SEULE. Rien dans le Sheet, rien chez Hektor, rien en base : le gel est lu en direct par le pooler dans une
transaction READ ONLY ; le registre local est ouvert en lecture seule ; les chaines sont celles du rejeu sur copie
(`chaines_ce_soir_avec_g2_et_outil.json`, temps10).

Ses demandes (20/11, soir) :
  1. « LES 132 COUPES DATEES [...] Ce defaut les touche-t-il ? Je veux la MESURE, pas le principe. Si une seule est
     fausse, je retire ma validation. »
  2. « L'OUTIL DE COUPE porte ce defaut dans son code. Corrige-le et montre-moi son temoin : un cas ou l'ancien se
     trompait et ou le neuf tranche juste, ou s'abstient. »
  3. Critere 1 : « LA PREUVE INTERNE DECIDE [...] Sinon : A PART. » Critere 2 : « SI L'ETIQUETTE NE BOUGE PAS, LE
     DOUTE NE COUTE RIEN [...] combien de mes questions ne changent AUCUNE etiquette ? »
  4. « Combien d'autres groupes ont une ligne oubliee comme celle-la ? »

L'outil corrige est `coupe_preuve_interne.py` (meme dossier) ; ce script le fait tourner et ecrit le compte rendu.

Usage :  python -u phase2/checks/temps11_les_132_mesurees_et_tes_criteres_2026-11-20.py
Sortie : notice/TEMPS11_LES_132_MESUREES_ET_TES_CRITERES_2026-11-20.md et .csv ; code 0 si les temoins sont verts.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase2.sync import push_upgrade_to_supabase as PU  # noqa: E402
import coupe_preuve_interne as K  # noqa: E402

CACHE = K.CACHE
LES_132 = RACINE / "notice" / "TEMPS8_DECISION_DU_20_11_LES_132_COUPES_DATEES_VALIDEES_2026-11-20.csv"
GROUPES = RACINE / "notice" / "TEMPS9_LE_CLASSEUR_DES_GROUPES_2026-11-20.csv"
QUESTIONS = RACINE / "notice" / "TEMPS10_TES_23_QUESTIONS_EN_DEUX_2026-11-20.csv"
SORTIE_MD = RACINE / "notice" / "TEMPS11_LES_132_MESUREES_ET_TES_CRITERES_2026-11-20.md"
SORTIE_CSV = RACINE / "notice" / "TEMPS11_LES_132_MESUREES_ET_TES_CRITERES_2026-11-20.csv"
ITEM = re.compile(r"(\d+) (comp|offr|vent)\w*(\([^)]*\))?(\[[^\]]*\])?")
PROUVEES = (K.PROUVEE_DATE, K.PROUVEE_PH, K.PROPRE_C5, "PROUVEE PAR SA CHAINE")


def lire_csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def gel_vivant() -> list:
    import psycopg2
    PU.load_env_files(PU.DEFAULT_ENV_FILES)
    u = urllib.parse.urlparse(os.environ["DATABASE_URL"])
    cn = psycopg2.connect(host=os.environ["SUPABASE_POOLER_HOST"], port=5432, dbname="postgres",
                          user="postgres.dwaqxfrinihnychuoptk", password=urllib.parse.unquote(u.password),
                          connect_timeout=15, sslmode="require")
    cu = cn.cursor()
    cu.execute("set transaction read only")
    cu.execute("select id_unique, app_affaire_id from app_classeur_lien")
    gel = [(i, int(a)) for i, a in cu.fetchall()]
    cn.rollback()
    cn.close()
    return gel


def morceaux_de(texte: str, D: K.Donnees) -> list:
    """« 11145 comp(cancel) -> 4f7b9749 TOSUN | ... || ... » -> [(pieces, lignes, etiquettes de l'ancien)]."""
    out = []
    for s in texte.split("||")[0].split(" | "):
        if "->" not in s:
            continue
        g, d = s.split("->", 1)
        ls = {t for t in re.findall(r"\b\w{8}\b", d) if t in D.LIG}
        if not ls:
            continue
        out.append(([int(m.group(1)) for m in ITEM.finditer(g)], ls,
                    {int(m.group(1)): (m.group(4) or "[date]").strip("[]") for m in ITEM.finditer(g)}))
    return out


def etiquettes(lab_prec: dict, ch_new: dict) -> dict:
    """La pose de nuit (app_poser_etiquettes_dossier, lue en production le 20/11) : la FUSION garde l'etiquette de la
    plus petite transaction ; la SCISSION laisse l'etiquette au groupe de la plus petite transaction qui la porte et en
    donne une NEUVE aux autres. (Recopie de temps6.)"""
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


def main() -> int:
    out: list[str] = []

    def dire(s=""):
        print(s, flush=True)
        out.append(s)

    echecs = []
    gel = gel_vivant()
    D = K.Donnees(gel)
    dire("gel vivant : %d liens ; lignes rattachees a un bien : %d" % (len(gel), sum(len(v) for v in D.lignes_bien.values())))
    S = {int(a): c for a, c in json.loads((CACHE / "chaines_ce_soir_avec_g2_et_outil.json").read_text(
        encoding="utf-8")).items()}
    lab0 = {a: t["uuid"] for a, t in D.TX.items() if t.get("uuid")}

    # ══ 1. LES 132 COUPES DATEES, PIECE PAR PIECE ══════════════════════════════════════════════════════════════════
    coupes: dict[str, str] = {}
    for r in lire_csv(LES_132):
        coupes.setdefault(r["numero_de_coupe"], r["la_coupe"])
    lignes_132 = {r["id_unique"] for r in lire_csv(LES_132)}
    res132 = {}
    st_pieces = Counter()
    for n, txt in coupes.items():
        mx = morceaux_de(txt, D)
        autour = set().union(*[m[1] for m in mx])
        pieces = []
        for ids, ls, _tags in mx:
            for a in ids:
                st, why = K.juger(D, a, ls, autour)
                pieces.append([a, ls, st, why, ids])
        prouvees = {a for a, _l, st, _w, _i in pieces if st in PROUVEES}
        for p_ in pieces:
            if p_[2] == K.SANS_PREUVE:
                ch = K.prouvee_par_sa_chaine(D, p_[0], set(p_[4]), prouvees)
                if ch:
                    p_[2], p_[3] = "PROUVEE PAR SA CHAINE", ch
        for p_ in pieces:
            st_pieces[p_[2]] += 1
        sts = {p_[2] for p_ in pieces}
        v = ("CONTREDITE" if K.CONTREDITE in sts else "CONFLIT DATE / PRIX" if K.CONFLIT in sts else
             "SANS PREUVE" if K.SANS_PREUVE in sts else
             "PROUVEE (une offre par sa chaine)" if "PROUVEE PAR SA CHAINE" in sts else "PROUVEE")
        douteuses = [p_ for p_ in pieces if p_[2] not in PROUVEES]
        neutres = all(K.neutre(p_[0], [m[0] for m in mx]) for p_ in douteuses) if douteuses else True
        res132[n] = {"texte": txt, "morceaux": mx, "pieces": pieces, "verdict": v, "douteuses": douteuses,
                     "neutre": neutres}
    c132 = Counter(r["verdict"] for r in res132.values())
    dire("")
    dire("1. LES 132 COUPES : %d pieces -- %s" % (sum(st_pieces.values()), dict(st_pieces)))
    dire("   coupes : %s" % dict(c132))
    if sum(st_pieces.values()) < 600 or len(coupes) != 132:
        echecs.append("132 : lecture incomplete")
    # LE TEMOIN DU CRITERE 2 : la regle « la plus petite transaction » (K.neutre) doit dire EXACTEMENT ce que dit la
    # simulation de la pose. Sur CHAQUE piece des 132 (et pas seulement les douteuses) : pour chaque etat ecrit X (un
    # morceau, ou la piece a part) et chaque verite Y (un autre morceau), on ecrit X, on corrige vers Y, et on regarde
    # si l'etiquette d'une AUTRE piece bouge. La simulation est restreinte aux pieces du bien (le chainage ne traverse
    # jamais deux biens).
    accords, desaccords, neutres_vus = 0, [], 0
    for n, r in res132.items():
        mx = [list(m[0]) for m in r["morceaux"]]
        tous = {x for m in mx for x in m}
        biens = {D.REG[x]["bien"] for x in tous if x in D.REG}
        S_b = {x: S[x] for b in biens for x in D.par_bien.get(b, []) if x in S}
        lab_b = {x: lab0[x] for x in S_b if x in lab0}
        for a in sorted(tous):
            if [m for m in mx if a in m and len(m) == 1] or len(mx) < 2:
                continue
            places = [("M", k) for k in range(len(mx))] + [("SEULE", a)]

            def etat(place, a=a, mx=mx, n=n, S_b=S_b):
                ch = dict(S_b)
                for k, ids in enumerate(mx):
                    for x in ids:
                        if x != a:
                            ch[x] = ("M", n, k)
                ch[a] = ("M", n, place[1]) if place[0] == "M" else ("SEULE", a)
                return ch
            bouge = False
            for X in places:
                lab1 = etiquettes(lab_b, etat(X))
                for Y in places[:-1]:
                    if Y != X:
                        lab2 = etiquettes(lab1, etat(Y))
                        bouge = bouge or any(lab2.get(x) != lab1.get(x) for x in tous if x != a)
            neutres_vus += (not bouge)
            if bouge == (not K.neutre(a, mx)):
                accords += 1
            else:
                desaccords.append((n, a, bouge))
    dire("   TEMOIN du critere 2 -- la regle de la plus petite transaction contre la simulation de la pose (ecrire, "
         "puis corriger dans tous les sens), sur chaque piece des 132 : %d d'accord (dont %d ou rien ne bouge), "
         "%d en desaccord %s" % (accords, neutres_vus, len(desaccords), desaccords[:5]))
    if desaccords or not accords:
        echecs.append("temoin critere 2")

    # ══ 2. L'OUTIL CORRIGE CONTRE L'ANCIEN, SUR TOUTES LES COUPES (132 + sections 1 et 2 du classeur) ═════════════
    groupes = lire_csv(GROUPES)
    sources = [("132", n, r["texte"]) for n, r in sorted(res132.items(), key=lambda kv: int(kv[0]))]
    sources += [("classeur", g["ordre"], g["ce qui est propose"]) for g in groupes if g["section"][:2] in ("1 ", "2 ")]
    temoin = []
    cpt = Counter()
    for src, n, txt in sources:
        mx = morceaux_de(txt, D)
        if not mx:
            continue
        autour = set().union(*[m[1] for m in mx])
        disputees = [int(x) for x in re.findall(r"(\d{3,7}) vent", txt.split("DISPUTEES :")[1].split("||")[0])] \
            if "DISPUTEES :" in txt else []
        for ids, ls, tags in mx:
            for a in ids:
                neuf, quoi = K.decider(D, a, autour)
                if neuf is None:
                    cas = "LE NEUF S'ABSTIENT"
                elif neuf & ls:
                    cas = "MEME LIGNE"
                else:
                    cas = "LE NEUF CORRIGE"
                cpt[(src, cas)] += 1
                temoin.append((src, n, a, tags.get(a, "date"), "/".join(sorted(ls)),
                               "/".join(sorted(neuf)) if neuf else "-", quoi, cas))
        for a in disputees:
            neuf, quoi = K.decider(D, a, autour)
            cas = "LE NEUF TRANCHE UNE DISPUTE" if neuf else "TOUS DEUX S'ABSTIENNENT"
            cpt[(src, cas)] += 1
            temoin.append((src, n, a, "disputee", "-", "/".join(sorted(neuf)) if neuf else "-", quoi, cas))
    dire("")
    dire("2. L'OUTIL CORRIGE CONTRE L'ANCIEN : %s" % {"%s / %s" % k: v for k, v in sorted(cpt.items())})
    # les cas nommes : ou l'ancien se trompait
    for src, n, a, tag, vieux, neuf, quoi, cas in temoin:
        if src == "classeur" and n in ("7", "8", "17", "22", "25", "28", "29", "40", "50") and cas != "MEME LIGNE":
            dire("   groupe %s, piece %s [%s] : l'ancien -> %s ; le neuf -> %s (%s) -- %s" % (n, a, tag, vieux, neuf, quoi,
                                                                                         cas))
    attendu = {(16378, "RX6J289Y"), (27135, "JRE23R1G"), (7450, "DN5U3GER"), (17131, "ZV3QRSJG")}
    vu = {(a, neuf) for src, n, a, tag, vieux, neuf, quoi, cas in temoin if src == "classeur"}
    manque = sorted(x for x in attendu if x not in vu)
    dire("   TEMOIN de l'outil -- les 4 lectures justes que j'avais refaites a la main sont retrouvees : %s %s"
         % ("VERT" if not manque else "ROUGE", manque))
    if manque:
        echecs.append("temoin outil")
    abst = {a for src, n, a, tag, vieux, neuf, quoi, cas in temoin if src == "classeur" and cas == "LE NEUF S'ABSTIENT"}
    manque2 = sorted({4533, 7710, 4560, 14110} - abst)
    dire("   TEMOIN de l'outil -- il s'abstient sur les 4 indecidables (4533, 7710, 4560, 14110) : %s %s"
         % ("VERT" if not manque2 else "ROUGE", manque2))
    if manque2:
        echecs.append("temoin abstention")

    # ══ 3. LES LIGNES OUBLIEES ════════════════════════════════════════════════════════════════════════════════════
    oub = []
    for g in groupes:
        ls_g = set(g["lignes du Sheet"].split())
        ts = {a for i in ls_g for a in D.gel_l.get(i, set()) if a in D.REG and not D.REG[a]["c5"]}
        if not ts:
            continue
        biens = {D.REG[a]["bien"] for a in ts}
        autres = set().union(*[D.lignes_bien.get(b, set()) for b in biens]) - ls_g
        dates = [D.REG[a]["date"] for a in ts if D.REG[a]["date"]]
        reclament, contemporaines = [], []
        for i in sorted(autres):
            if any(D.touche_date(a, i) or D.touche_ph(a, i) for a in ts):
                reclament.append(i)
            else:
                di = [d for d in (K.d_sheet(D.case(i, c)) for c in ("Offre Achat", "Compromis", "Annulée",
                                                                    "Vente Fixée")) if d]
                if dates and di and any(min(dates).toordinal() - 365 <= d.toordinal() <= max(dates).toordinal() + 365
                                        for d in di):
                    contemporaines.append(i)
        if reclament or contemporaines:
            oub.append((g["ordre"], g["section"][:2].strip(), g["lignes du Sheet"], reclament, contemporaines,
                        g["MA RECOMMANDATION"].split(" ")[0]))
    n_rec = [o for o in oub if o[3]]
    n_con = [o for o in oub if o[4] and not o[3]]
    dire("")
    dire("3. LES LIGNES OUBLIEES : sur %d groupes, %d ont une ligne du meme bien HORS du groupe qui RECLAME une de "
         "leurs pieces (date au jour exact ou prix + honoraires), %d en ont une contemporaine qui ne reclame rien"
         % (len(groupes), len(n_rec), len(n_con)))
    for o in n_rec:
        dire("   groupe %s (section %s, %s) %s -> reclame : %s" % (o[0], o[1], o[5], o[2], " ".join(o[3])))
    g40 = [o for o in oub if o[0] == "40"]
    ok40 = bool(g40) and "L2B2WGCF" in (g40[0][3] + g40[0][4])
    dire("   TEMOIN : FARGE-DEBISE (L2B2WGCF) est vue sur le groupe 40 : %s" % ("VERT" if ok40 else "ROUGE"))
    if not ok40:
        echecs.append("temoin oubliee")
    # sur les 132 coupes
    oub132 = []
    for n, r in res132.items():
        ls_c = set().union(*[m[1] for m in r["morceaux"]])
        ts = [a for m in r["morceaux"] for a in m[0] if a in D.REG and not D.REG[a]["c5"]]
        biens = {D.REG[a]["bien"] for a in ts}
        autres = set().union(*[D.lignes_bien.get(b, set()) for b in biens]) - ls_c
        rec = sorted(i for i in autres if any(D.touche_date(a, i) or D.touche_ph(a, i) for a in ts))
        if rec:
            oub132.append((n, rec))
    dire("   sur les 132 coupes : %d ont une ligne hors de la coupe qui reclame une piece %s" % (len(oub132), oub132[:8]))

    # ══ 4. SES QUESTIONS : LE CRITERE 1 (la preuve) ET LE CRITERE 2 (l'etiquette bouge-t-elle) ═══════════════════
    qs = [r for r in lire_csv(QUESTIONS) if r["classe"] in ("A", "B-attend", "B-libre")]
    PIECES_EN_CAUSE = {"A1": [27512], "A3": [11414], "A4": [19131, 19133], "A5": [20088], "A6": [4542],
                       "A9": [17366], "B1": [26613], "B2": [21520], "B3": [14033]}
    PAS_DE_PIECE = {"A2": "une date d'annulation", "A7": "le role d'une offre dans un dossier qui ne change pas",
                    "A8": "laquelle des deux saisies d'une meme affaire porte l'etiquette (meme dossier)",
                    "B4": "une date d'offre", "B5": "une date de compromis",
                    "B6": "un compromis a creer : il entrerait dans le dossier avec un numero plus grand",
                    "B7": "un dossier sur une AUTRE annonce (le chainage ne traverse jamais deux biens)"}
    dire("")
    dire("4. TES 23 QUESTIONS, TES DEUX CRITERES")
    rang_q = []
    for q in qs:
        n = q["numero"]
        lignes_q = q["lignes du Sheet"].split()
        if n in PAS_DE_PIECE:
            verdict, detail = "SORT DE TA LISTE (critere 2)", "ta reponse ne deplace aucune piece : " + PAS_DE_PIECE[n]
        else:
            details, sorts = [], []
            for a in PIECES_EN_CAUSE[n]:
                autour = set(lignes_q) | {i for x in D.par_bien[D.REG[a]["bien"]] for i in D.gel_t.get(x, set())}
                neuf, quoi = K.decider(D, a, autour)
                chaine = [x for x in S if S[x] == S.get(a)]
                cands = sorted({c for c in (D.lignes_du_bien(a) | autour) if not D.contre_dates(a, {c})})
                morceaux = [[x for x in D.par_bien[D.REG[a]["bien"]] if x != a and c in D.gel_t.get(x, set())]
                            for c in cands]
                morceaux = [m + [a] for m in morceaux if m]
                neu = K.neutre(a, morceaux) if morceaux else False
                if neuf:
                    sorts.append("TRANCHEE PAR LA PREUVE")
                    details.append("%d -> %s (%s)" % (a, "/".join(sorted(neuf)), quoi))
                elif neu:
                    sorts.append("SORT DE TA LISTE (critere 2)")
                    details.append("%d : pas de preuve (%s), mais elle n'est la plus petite d'aucun dossier possible"
                                   % (a, quoi))
                else:
                    sorts.append("A PART (critere 1)")
                    details.append("%d : pas de preuve (%s) et sa place deplacerait une etiquette -> A PART" % (a, quoi))
                _ = chaine
            verdict = sorts[0] if len(set(sorts)) == 1 else " + ".join(sorted(set(sorts)))
            detail = " ; ".join(details)
        rang_q.append((n, q["classe"], " ".join(lignes_q), q["qui"], verdict, detail))
        dire("   %s %s (%s) : %s -- %s" % (n, q["qui"], " ".join(lignes_q), verdict, detail))
    sortent = [r for r in rang_q if r[4].startswith("SORT")]
    dire("   => sortent de ta liste (aucune etiquette ne bouge) : %d questions, %d lignes"
         % (len(sortent), sum(len(r[2].split()) for r in sortent)))

    # ══ 5. LES CORRECTIONS DU CLASSEUR ET LA SECTION 1, AU CRIBLE DU NEUF ═══════════════════════════════════════════
    dire("")
    dire("5. LES PIECES DE MES CORRECTIONS, AU CRIBLE DU NEUF")
    rang_c = []
    for g_, a in (("7", 16378), ("17", 27135), ("17", 27134), ("25", 4649), ("25", 4651), ("28", 7450), ("8", 17131),
                  ("22", 4533), ("29", 7710), ("50", 4560), ("40", 14110), ("40", 14115), ("50", 4564)):
        autour = {i for x in D.par_bien[D.REG[a]["bien"]] for i in D.gel_t.get(x, set())}
        neuf, quoi = K.decider(D, a, autour)
        rang_c.append((g_, a, "/".join(sorted(neuf)) if neuf else "A PART", quoi))
        dire("   groupe %s, %d -> %s (%s)" % (g_, a, "/".join(sorted(neuf)) if neuf else "A PART", quoi))

    # ══ 6. OU CA TOMBE : LES 132 ET LES SECTIONS 1 A 3 PASSEES A L'OUTIL NEUF, BIEN PAR BIEN ═══════════════════════
    #   Les pieces des dossiers touches sont donnees par la preuve (critere 1) ; une piece sans preuve est A PART ;
    #   B3 (14033) est A PART par sa decision. Une ligne s'ecrit si elle garde au moins une piece prouvee, dans un seul
    #   morceau, que personne hors de son acheteur ne partage.
    A_PART_PAR_DECISION = {14033: "B3, sa decision du 20/11 soir"}
    lignes_cibles = set(lignes_132)
    for g in groupes:
        if g["section"][:2] in ("1 ", "2 ", "3 "):
            lignes_cibles |= set(g["lignes du Sheet"].split())
    for q in qs:
        lignes_cibles |= set(q["lignes du Sheet"].split())
    biens6 = defaultdict(set)
    for i in lignes_cibles:
        for a in D.gel_l.get(i, set()):
            if a in D.REG:
                biens6[D.REG[a]["bien"]].add(i)
        for b, ls in D.lignes_bien.items():
            if i in ls:
                biens6[b].add(i)
    sort_brut = defaultdict(list)
    a_part_tot, morceaux_tot, gestes_gel, par_chaine, par_renego = [], 0, [], [], []
    for b, ls_b in sorted(biens6.items()):
        lignes_b = (D.lignes_bien.get(b, set()) | ls_b)
        lies = {a for i in lignes_b for a in D.gel_l.get(i, set()) if a in D.REG and D.REG[a]["bien"] == b}
        chaines_t = {S[a] for a in lies if a in S}
        X = sorted(a for a in D.par_bien.get(b, []) if S.get(a) in chaines_t)
        va = {}
        apart = {}
        for a in X:
            if a in A_PART_PAR_DECISION:
                apart[a] = A_PART_PAR_DECISION[a]
                continue
            ls_, quoi = K.decider(D, a, lignes_b)
            if ls_:
                va[a] = frozenset(ls_)
            else:
                apart[a] = quoi
        # LA CONVENTION APRES RENEGOCIATION (sa regle du 20/11 soir) : une offre ACCEPTEE sans preuve a elle suit le
        # compromis prouve de sa chaine quand Hektor les enchaine (le compromis vient 0 a 31 jours apres, et aucune
        # autre offre acceptee ne s'intercale) -- c'est le chainage de Hektor lui-meme, pas le nom.
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
        for a, why in apart.items():
            possibles = [m + [a] for gl, m in morceaux6.items() if not D.contre_dates(a, set(gl))]
            neu = K.neutre(a, possibles) if possibles else False
            a_part_tot.append((b, a, why, neu))
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
                sort_brut[i].append(("ECRITE", "morceau %s" % "+".join(str(x) for x in morceaux6[gl[0]])
                                     + (" (avec %s)" % " ".join(sorted(gl[0] - {i})) if len(gl[0]) > 1 else ""), b))
            elif gl:
                sort_brut[i].append(("NON ECRITE", "il ne lui reste que sa copie C5 (%s) ; ses pieces Hektor : %s" % (
                    "+".join(str(x) for x in morceaux6[gl[0]]), " ; ".join(
                        "%d a part (%s)" % (a, apart[a]) if a in apart else "%d ailleurs" % a for a in liens) or "aucune"),
                    b))
            elif liens:
                sort_brut[i].append(("NON ECRITE", "ses pieces sont a part ou ailleurs : " + " ; ".join(
                    "%d (%s)" % (a, apart.get(a, "donnee a une autre ligne")) for a in liens), b))
    sort_ligne = {}
    for i, rs in sort_brut.items():
        ec = [r for r in rs if r[0] == "ECRITE"]
        if len(ec) == 1:
            sort_ligne[i] = ec[0][:2]
        elif len(ec) > 1:
            sort_ligne[i] = ("NON ECRITE", "ecrite sur deux biens : " + " / ".join(r[1] for r in ec))
        else:
            sort_ligne[i] = rs[0][:2]
    for i in lignes_cibles:
        sort_ligne.setdefault(i, ("NON ECRITE", "aucune piece chez nous"))
    c6 = Counter(v[0] for v in sort_ligne.values())
    dire("")
    dire("6. OU CA TOMBE -- %d biens, %d morceaux, %d pieces A PART (%d dont la place ne bougerait aucune etiquette)"
         % (len(biens6), morceaux_tot, len(a_part_tot), sum(1 for x in a_part_tot if x[3])))
    dire("   lignes : %s ; offres acceptees rangees par leur compromis : %d, par sa convention de renegociation : %d" % (
        dict(c6), len(par_chaine), len(par_renego)))
    dire("   non ecrites : %s" % " ; ".join("%s (%s)" % (i, v[1][:110]) for i, v in sorted(sort_ligne.items())
                                         if v[0] != "ECRITE"))
    for q in qs:
        dire("   %s %s : %s" % (q["numero"], q["qui"], " | ".join("%s %s -- %s" % (i, *sort_ligne.get(i, ("?", "")))
                                                              for i in q["lignes du Sheet"].split())))
    perdues_132 = sorted(i for i in lignes_132 if sort_ligne.get(i, ("?",))[0] != "ECRITE")
    dire("   les 274 lignes des 132 coupes : %d ecrites, %d non -> %s" % (
        len(lignes_132) - len(perdues_132), len(perdues_132),
        " ; ".join("%s (%s)" % (i, sort_ligne.get(i, ("?", "?"))[1][:140]) for i in perdues_132)))
    dire("   gestes sur le gel pour y arriver (a faire seulement sur ton accord) : %d (relier %d, delier %d)"
         % (len(gestes_gel), sum(1 for x in gestes_gel if x[1] == "relier"),
            sum(1 for x in gestes_gel if x[1] == "delier")))
    for b, a, why, neu in a_part_tot:
        p = D.REG.get(a, {})
        dire("   A PART : %d %s %s %s (bien %s) -- %s%s" % (a, p.get("genre"), p.get("etat"), p.get("montant"), b, why,
                                                         " -- sa place ne bouge aucune etiquette" if neu else ""))

    # ══ LES SORTIES ════════════════════════════════════════════════════════════════════════════════════════════════
    with SORTIE_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["partie", "numero", "piece", "genre", "etat", "montant", "lignes", "statut", "pourquoi",
                    "critere 2 : neutre"])
        for n, r in sorted(res132.items(), key=lambda kv: int(kv[0])):
            for a, ls, st, why, _ids in r["pieces"]:
                p = D.REG.get(a, {})
                w.writerow(["132", n, a, p.get("genre"), p.get("etat"), p.get("montant"), " ".join(sorted(ls)), st, why,
                            ("oui" if K.neutre(a, [m[0] for m in r["morceaux"]]) else "non") if st not in PROUVEES else ""])
        for src, n, a, tag, vieux, neuf, quoi, cas in temoin:
            w.writerow(["temoin " + src, n, a, tag, "", "", "ancien %s / neuf %s" % (vieux, neuf), cas, quoi, ""])
        for o in oub:
            w.writerow(["oubliees", o[0], "", "", "", "", o[2], "reclame : " + " ".join(o[3]),
                        "contemporaines : " + " ".join(o[4]), ""])
        for r in rang_q:
            w.writerow(["questions", r[0], "", "", "", "", r[2], r[4], r[5], ""])
        for r in rang_c:
            w.writerow(["corrections", r[0], r[1], "", "", "", r[2], "", r[3], ""])
        for i, (s_, why) in sorted(sort_ligne.items()):
            w.writerow(["ou ca tombe", "", "", "", "", "", i, s_, why, ""])
        for b, a, why, neu in a_part_tot:
            w.writerow(["a part", b, a, D.REG.get(a, {}).get("genre"), D.REG.get(a, {}).get("etat"),
                        D.REG.get(a, {}).get("montant"), "", "A PART", why, "oui" if neu else "non"])
        for i, geste, ids in gestes_gel:
            w.writerow(["gel", "", " ".join(str(x) for x in ids), "", "", "", i, geste, "", ""])
    md = ["# Les 132 coupes mesurees, l'outil corrige, tes deux criteres (20/11, soir)", "",
          "> Lecture seule. Genere par `phase2/checks/temps11_les_132_mesurees_et_tes_criteres_2026-11-20.py` "
          "(l'outil : `coupe_preuve_interne.py`), gel vivant.", "", "```"] + out + ["```", ""]
    md += ["## Les 132, coupe par coupe (celles qui ne sont pas prouvees sans reserve)", ""]
    for n, r in sorted(res132.items(), key=lambda kv: int(kv[0])):
        if r["verdict"] == "PROUVEE":
            continue
        md += ["- **coupe %s -- %s** (critere 2 : %s) : `%s`" % (n, r["verdict"], "la place des pieces en doute ne "
               "change aucune etiquette" if r["neutre"] else "une etiquette en depend", r["texte"].split("||")[0])]
        for a, ls, st, why, _ids in r["pieces"]:
            if st not in (K.PROUVEE_DATE, K.PROUVEE_PH, K.PROPRE_C5):
                md += ["  - %s -> %s : %s -- %s" % (a, " ".join(sorted(ls)), st, why)]
    SORTIE_MD.write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    dire("")
    dire("ecrit : %s et .csv" % SORTIE_MD.name)
    dire("RESULTAT : %s" % ("VERT" if not echecs else "ROUGE " + ", ".join(echecs)))
    SORTIE_MD.write_text("\n".join(md[:5] + out + md[5 + len(out):]) + "\n", encoding="utf-8", newline="\n")
    return 0 if not echecs else 1


if __name__ == "__main__":
    sys.exit(main())
