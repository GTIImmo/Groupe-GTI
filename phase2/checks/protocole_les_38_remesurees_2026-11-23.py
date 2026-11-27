"""LES 38 REMESUREES (23/11, son message du soir, point 3) -- LECTURE SEULE : l'image du 23/11 08:02, le socle en lecture
(passage de reference 73). Rien en base, rien dans le Sheet, rien chez Hektor ; les rattachements sont simules EN MEMOIRE.

Son message : « Les 38 : je ne suis pas sur de mes decisions anterieures. Ne me demande pas de les reconfirmer -- refais les
mesures qui les fondaient, avec l'etat d'aujourd'hui. »

  1  SES 20 A PART -- sa raison du 21/11 etait une MESURE : « on ne paie cette dette que la ou elle est obligatoire : les
     20 dont la place deplace une etiquette ». La mesure d'alors (temps12_v3_fabriquer, etape_calcul) : une piece a part
     est NEUTRE quand elle n'est la plus petite d'AUCUN morceau ou elle pourrait aller (dates compatibles) -- K.neutre,
     son critere 2 ; une piece SANS morceau possible etait comptee NON neutre (par defaut). Ici : la meme fonction sur
     les morceaux d'aujourd'hui (la coupe finale du protocole, toutes regles validees), PLUS la pose de nuit simulee
     (quelle etiquette bouge vraiment, pour quelle ligne). Temoin : les memes mesures sur les 20 neutres du 22/11 (n19).
  2  LES 5 AFFAIRES SUR UN AUTRE BIEN -- la preuve ligne par ligne (bien reel, dates au jour exact, honoraires des deux
     cotes, vendeur parmi les mandants) et le rattachement SIMULE : quel numero, quelle etiquette bouge, qui perd quoi.
  3  LES DEUX PAIRES ecartees de R13 (DTZ227ER / E9XL0N5B, IAYQ5OG2 / L597FO6M) : les pieces et les cases en face.
  4  LE BIEN 39845 : une vue (ses pieces, ses lignes, l'etage du gel qui les a rangees).
TEMOIN DE L'OUTIL : chaque bien rejuge EN MEMOIRE doit redonner le passage 73 du socle, ligne par ligne.

USAGE : python -u phase2/checks/protocole_les_38_remesurees_2026-11-23.py [1|2|3|4|tout]
"""
import sys, json, sqlite3, csv, re
from collections import Counter, defaultdict
sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks"); sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P, piece_copie_ou_vraie as PC, coupe_preuve_interne as K
sys.stdout.reconfigure(encoding="utf-8")
PASSAGE = 73
SECTIONS = set(sys.argv[1:]) or {"tout"}
if "tout" in SECTIONS:
    SECTIONS = {"1", "2", "3", "4"}


def dire(s=""):
    print(s, flush=True)


I = P.Image(P.IMAGES / "2026-11-23_080234")
D = I.D
con = sqlite3.connect("file:C:/Hektor/chantier_classeur_q6_cache/protocole/socle.sqlite?mode=ro", uri=True)
V73 = {i: {"verdict": v, "etiquette": e, "pieces": json.loads(p) if p else None, "motif": m, "texte": t}
       for i, v, e, p, m, t in con.execute("select id_unique, verdict, etiquette, pieces, motif, motif_texte from verdict "
                                           "where passage=?", (PASSAGE,))}
NUM = {}
for a_, p_ in I.pieces.items():
    if p_["app_dossier_uuid"]:
        NUM[p_["app_dossier_uuid"]] = p_["app_dossier_numero"]
AVIS = {r["id_unique"]: r for r in csv.DictReader(
    open(P.NOTICE / "PROTOCOLE_TEMOIN_AVIS_LES_2560_NUMEROS_PASSAGE_54_2026-11-22.csv", encoding="utf-8-sig"),
    delimiter=";")}
TIENT = defaultdict(set)
for i_, x_ in V73.items():
    if x_["verdict"] == "TRANCHEE":
        for q_ in x_["pieces"]:
            TIENT[q_].add(i_)


def numero(lab):
    if lab is None:
        return "-"
    return "NEUF" if str(lab).startswith("NEUVE") else (NUM.get(lab) or str(lab)[:8])


# ── l'enregistreur : la coupe finale et la pose simulee du DERNIER jugement de chaque bien ─────────────────────────────
LAST_R, LAST_POSE, COURANT = {}, {}, [None]
_couper, _pose = K.couper_le_bien, K.pose_de_nuit


def _rec_couper(D_, b, *a, **k):
    r = _couper(D_, b, *a, **k)
    LAST_R[b] = r
    return r


def _rec_pose(lab_prec, ch_new):
    lab = _pose(lab_prec, ch_new)
    if COURANT[0] is not None:
        LAST_POSE[COURANT[0]] = (dict(lab_prec), dict(ch_new), lab)
    return lab


K.couper_le_bien, K.pose_de_nuit = _rec_couper, _rec_pose


def juger(b, lignes):
    """Le bien juge comme au passage (juger_bien_garde) ; LAST_R / LAST_POSE / MISES_DE_COTE refletent le jugement rendu."""
    for q in [q for q, x in P.MISES_DE_COTE.items() if x["bien"] == b]:
        del P.MISES_DE_COTE[q]
    P.GARDE_DEJA_RENDU.pop(b, None)
    COURANT[0] = b
    try:
        out = P.juger_bien_garde(I, b, set(lignes), "bien")
        if b in P.GARDE_DEJA_RENDU:            # juge SANS les regles gardees : on rejoue SANS pour que l'enregistreur suive
            g_ = set(P.GARDE_DEJA_RENDU[b]["regles"])
            for q in [q for q, x in P.MISES_DE_COTE.items() if x["bien"] == b]:
                del P.MISES_DE_COTE[q]
            P.SUSPENDUES.update(g_)
            try:
                out = P.juger_bien(I, b, set(lignes), "bien")
            finally:
                P.SUSPENDUES.difference_update(g_)
    finally:
        COURANT[0] = None
    return {o["id_unique"]: o for o in out}


def cle(o):
    return (o["verdict"], o.get("etiquette"), tuple(o.get("pieces") or ()), o.get("motif"))


def cle73(i):
    x = V73[i]
    return (x["verdict"], x["etiquette"], tuple(x["pieces"] or ()), x["motif"])


dire("chargement : le jugement de chaque ligne (E1, E2), comme le passage ...")
PAR_BIEN, HORS = defaultdict(set), {}
for i, vs in sorted(I.sheet["par_id"].items()):
    r_ = P.juger_ligne(I, i, vs[0])
    if r_ is None:
        PAR_BIEN[P.r_bien(I, i)].add(i)
    else:
        HORS[i] = r_
TEMOIN = Counter()
ECARTS_OUTIL = []


def juger_temoin(b):
    out = juger(b, PAR_BIEN.get(b, set()))
    for i, o in out.items():
        ok = cle(o) == cle73(i)
        TEMOIN["redonne le passage 73" if ok else "ECART"] += 1
        if not ok:
            ECARTS_OUTIL.append((b, i, cle(o), cle73(i)))
    return out


def date_cases(i):
    return {c: K.d_sheet(D.case(i, c)) for c in ("Offre Achat", "Compromis", "Signé", "Vente Prévue", "Vente Fixée",
                                                  "Signée", "Vente Réglée", "Annulée")}


def montrer_ligne(i, b=None, noms=False):
    cs = {c: D.case(i, c).strip() for c in ("Etat Actuel", "Offre Achat", "Compromis", "Vente Fixée", "Signée",
                                            "Vente Réglée", "Annulée", "Prix", "Commission TTC", "Mandat")}
    s = " | ".join("%s=%s" % (k, v) for k, v in cs.items() if v)
    if noms:
        s += " | Acquéreur=%s" % D.case(i, "Acquéreur").strip()
    v = V73.get(i, {})
    av = AVIS.get(i)
    dire("     %s (ligne %s) %s" % (i, D.LIG[i]["num"], s))
    dire("        passage 73 : %s %s%s ; 16/11 : %s" % (v.get("verdict"), v.get("motif") or numero(v.get("etiquette")),
                                                       (" pieces %s" % v["pieces"]) if v.get("pieces") else "",
                                                       av["numero_du_16_11"] if av else "hors des 2 560"))


def montrer_piece(q, lignes=()):
    r = D.REG[q]
    p = I.pieces[q]
    sup = " SUPPRIMEE chez Hektor" if P.supprimee_chez_hektor(p) else ""
    acc = []
    for i in lignes:
        for c, d in date_cases(i).items():
            if d and r["date"] and d == r["date"]:
                acc.append("date = « %s » de %s" % (c, i))
        com = P.nombre_case(D.case(i, "Commission TTC"))
        if r["hon"] is not None and com is not None and abs(r["hon"] - com) <= 1:
            acc.append("honoraires = Commission de %s" % i)
        prix = P.nombre_case(D.case(i, "Prix"))
        if r["montant"] is not None and prix is not None and abs(r["montant"] - prix) <= 1:
            acc.append("montant = Prix de %s" % i)
    dire("     %-8s %-5s %-9s %-10s %-10s %9s hon=%-7s dossier %s chaine %s gel %s tenue(73) %s%s" % (
        q, I.nature[q], r["genre"], r["etat"] or "", r["date"] or "sans date", r["montant"],
        r["hon"] if r["hon"] is not None else "?", p["app_dossier_numero"] or "-", p["app_chaine_id"],
        ",".join(sorted(I.gel_par_piece.get(q, []))) or "-", ",".join(sorted(TIENT.get(q, []))) or "personne", sup))
    if acc:
        dire("              -> " + " ; ".join(acc))


# ═══════════════════════════════════════ 1. SES 20 A PART ════════════════════════════════════════════════════════════
def mesurer_piece(b, a):
    r = LAST_R[b]
    lab_prec, ch_new, lab_a = LAST_POSE[b]
    etat = ("DONNEE a %s (%s)" % ("+".join(sorted(r["va"][a])), r["preuve"].get(a, "")[:70]) if a in r["va"] else
            ("MISE DE COTE (%s, fige avec %s)" % (P.MISES_DE_COTE[a]["regle"], P.MISES_DE_COTE[a]["groupe"])
             if a in P.MISES_DE_COTE else "A PART"))
    if a in r["va"]:
        return etat, "n'est plus a part", [], None
    poss = r["possibles"].get(a, [])
    neutre_21_11 = K.neutre(a, [r["morceaux"][gl] + [a] for gl in poss]) if poss else False
    sim = []
    for gl in poss:
        ids = r["morceaux"][gl]
        hk = [q for q in ids if I.nature[q] == PC.VRAIE]
        chB = dict(ch_new)
        chB[a] = ch_new[min(ids)]
        labB = _pose(lab_prec, chB)
        avant = lab_a[min(hk)] if hk else None
        apres = labB[min(hk + [a])] if (hk + [a]) else None
        ailleurs = sorted(q for q in lab_a if q != a and q not in ids and lab_a[q] != labB.get(q))
        sim.append({"lignes": sorted(gl), "plus_petite_du_morceau": a < min(ids), "morceau": ids,
                    "etiquette_avant": numero(avant) if hk else "aucune (copie seule)",
                    "etiquette_apres": numero(apres), "bouge": (avant != apres) or bool(ailleurs),
                    "ailleurs": [(q, numero(lab_a[q]), numero(labB[q]), sorted(TIENT.get(q, []))) for q in ailleurs]})
    if not poss:
        concl = "AUCUN MORCEAU POSSIBLE : sa place ne deplace aucune etiquette (le 21/11 : non neutre PAR DEFAUT)"
    elif neutre_21_11 and not any(s["bouge"] for s in sim):
        concl = "NEUTRE : sa place ne deplace plus aucune etiquette"
    elif not neutre_21_11 and any(s["bouge"] for s in sim):
        concl = "DEPLACE ENCORE une etiquette"
    else:
        concl = "⚠ LES DEUX MESURES DIVERGENT (critere 2 : %s ; pose simulee : %s)" % (
            "neutre" if neutre_21_11 else "plus petite", "bouge" if any(s["bouge"] for s in sim) else "rien ne bouge")
    return etat, concl, sim, neutre_21_11


def section_1():
    dire("\n=== 1. SES 20 A PART : sa presence deplace-t-elle ENCORE une etiquette aujourd'hui ? (passage %d)" % PASSAGE)
    v3 = json.loads(P.SRC_V3_CALCUL.read_text(encoding="utf-8"))
    res = {}
    for fam, liste in (("LES 20", v3["a20"]), ("TEMOIN : LES 20 NEUTRES DU 22/11 (n19)", v3["n19"])):
        dire("\n--- %s" % fam)
        par_b = defaultdict(list)
        for b, a, w in liste:
            par_b[str(b)].append((int(a), w))
        cpt = Counter()
        for b in sorted(par_b, key=int):
            if b in PAR_BIEN:
                juger_temoin(b)
            for a, w in sorted(par_b[b]):
                if a not in D.REG:
                    dire("   %s (bien %s) : ABSENTE du registre de l'image" % (a, b))
                    cpt["absente"] += 1
                    continue
                if b not in PAR_BIEN:
                    dire("   %s (bien %s) : aucune ligne du bien ne passe E1/E2 -- %s" % (a, b, sorted(
                        (i, HORS[i]["motif"]) for i in D.lignes_bien.get(b, set()) if i in HORS)))
                    cpt["bien sans ligne jugee"] += 1
                    continue
                etat, concl, sim, n21 = mesurer_piece(b, a)
                cpt[concl.split(" :")[0].split(" (")[0]] += 1
                res[a] = {"bien": b, "famille": fam, "pourquoi_22_11": w, "etat": etat, "conclusion": concl, "sim": sim}
                dire("   %s (bien %s, %s %s %s) -- le 22/11 : %s" % (
                    a, b, D.REG[a]["genre"], D.REG[a]["etat"] or "", D.REG[a]["date"] or "sans date", w))
                dire("      aujourd'hui : %s ; lignes du bien jugees : %s" % (etat, " ".join(sorted(PAR_BIEN[b]))))
                dire("      ⇒ %s" % concl)
                for s in sim:
                    dire("        morceau %s %s : etiquette %s -> %s%s%s" % (
                        "+".join(s["lignes"]), s["morceau"], s["etiquette_avant"], s["etiquette_apres"],
                        " (elle y serait la PLUS PETITE)" if s["plus_petite_du_morceau"] else "",
                        (" ; ailleurs : %s" % s["ailleurs"]) if s["ailleurs"] else ""))
        dire("   COMPTE %s : %s" % (fam, dict(cpt)))
    return res


# ═══════════════════════════════════ 2. LES 5 AFFAIRES SUR UN AUTRE BIEN ════════════════════════════════════════════
CINQ = ["2U5QPKRC", "EJN79TJ1", "MQ6H8TVQ", "QXDW8EQA", "91IHSGNC"]


def vendeur_parmi_mandants(i, q):
    noms = {x for x in re.findall(r"[A-ZÀ-Ü][A-ZÀ-Ü'\-]{2,}", D.case(i, "Vendeur").upper()) if x not in P.STOP_VENDEUR}
    mand = str(I.pieces[q].get("mandants_json") or "").upper()
    return sorted(n for n in noms if n in mand)


def section_2():
    dire("\n=== 2. LES 5 AFFAIRES SUR UN AUTRE BIEN : la preuve, et le rattachement SIMULE (en memoire)")
    res = {}
    for i in CINQ:
        autre = P.affaire_sur_un_autre_bien(I, i)
        anciens = set(I.biens_de_ligne.get(i, set()))
        dire("\n--- %s : nommee sur le bien %s (par %s) ; la triple preuve : %s" % (
            i, "+".join(sorted(anciens)) or "aucun",
            {b: sorted(D.rattache_par.get((b, i), set())) for b in anciens}, autre))
        montrer_ligne(i)
        if len(autre) != 1:
            dire("   ⛔ la triple preuve ne designe pas UN bien : %s" % autre)
            continue
        (bb, preuve), = autre.items()
        dire("   LE BIEN REEL %s : ses pieces (ce qui colle a %s)" % (bb, i))
        for q in sorted(D.par_bien.get(bb, [])):
            montrer_piece(q, [i])
            v_ = vendeur_parmi_mandants(i, q)
            if v_:
                dire("              -> vendeur de la ligne parmi les mandants de la piece : oui")
        dire("   les lignes du bien %s aujourd'hui :" % bb)
        for j in sorted(D.lignes_bien.get(bb, set())):
            montrer_ligne(j)
        # le rattachement, a blanc
        avant_bb = juger_temoin(bb) if bb in PAR_BIEN else {}
        avant_old = {b0: juger_temoin(b0) for b0 in anciens if b0 in PAR_BIEN}
        for b0 in anciens:
            D.lignes_bien[b0].discard(i)
        I.biens_de_ligne[i] = {bb}
        D.lignes_bien[bb].add(i)
        D.rattache_par[(bb, i)].add("a_blanc")
        if hasattr(I, "_coupes"):
            del I._coupes
        try:
            rl = P.juger_ligne(I, i, I.sheet["par_id"][i][0])
            apres_bb = juger(bb, PAR_BIEN.get(bb, set()) | ({i} if rl is None else set()))
            apres_old = {b0: juger(b0, PAR_BIEN[b0] - {i}) for b0 in avant_old}
        finally:
            D.lignes_bien[bb].discard(i)
            for b0 in anciens:
                D.lignes_bien[b0].add(i)
            I.biens_de_ligne[i] = anciens
            D.rattache_par[(bb, i)].discard("a_blanc")
            if not D.rattache_par[(bb, i)]:
                del D.rattache_par[(bb, i)]
            if hasattr(I, "_coupes"):
                del I._coupes
        o = rl if rl is not None else apres_bb.get(i)
        av = AVIS.get(i)
        col1 = "%s %s%s" % (o["verdict"], numero(o.get("etiquette")) if o["verdict"] == "TRANCHEE" else o["motif"],
                            (" pieces %s" % o["pieces"]) if o.get("pieces") else "")
        dire("   ⇒ RATTACHEE A %s : %s ; son numero du 16/11 : %s" % (bb, col1, av["numero_du_16_11"] if av else
                                                                       "hors des 2 560"))
        bouge = []
        for j, x in sorted(apres_bb.items()):
            if j == i:
                continue
            y = avant_bb.get(j)
            if y is None or cle(x) != cle(y):
                bouge.append((j, "bien %s" % bb, (y["verdict"], numero(y.get("etiquette")), y.get("pieces"), y.get("motif"))
                              if y else None, (x["verdict"], numero(x.get("etiquette")), x.get("pieces"), x.get("motif"))))
        for b0, ap in apres_old.items():
            for j, x in sorted(ap.items()):
                y = avant_old[b0].get(j)
                if y is None or cle(x) != cle(y):
                    bouge.append((j, "bien %s" % b0, (y["verdict"], numero(y.get("etiquette")), y.get("pieces"),
                                                      y.get("motif")) if y else None,
                                  (x["verdict"], numero(x.get("etiquette")), x.get("pieces"), x.get("motif"))))
        prises = sorted(q for q in (o.get("pieces") or []) if TIENT.get(q, set()) - {i})
        dire("   ⇒ CE QUI BOUGE AILLEURS : %s" % (bouge or "RIEN (aucune autre ligne ne change)"))
        dire("   ⇒ PIECES QU'UNE AUTRE LIGNE TENAIT : %s" % ([(q, sorted(TIENT[q])) for q in prises] or "aucune"))
        res[i] = {"bien_nomme": sorted(anciens), "bien_reel": bb, "preuve": preuve, "apres": col1,
                  "numero_16_11": av["numero_du_16_11"] if av else None, "bouge": bouge, "prises": prises}
    return res


# ═══════════════════════════════════════ 3. LES DEUX PAIRES ══════════════════════════════════════════════════════════
PAIRES = [("48145", "DTZ227ER", "E9XL0N5B"), ("9705", "L597FO6M", "IAYQ5OG2")]


def section_3():
    dire("\n=== 3. LES DEUX PAIRES ECARTEES DE R13")
    for b, x, y in PAIRES:
        out = juger_temoin(b)
        r = LAST_R[b]
        dire("\n--- bien %s : %s et %s" % (b, x, y))
        for j in sorted(D.lignes_bien.get(b, set())):
            montrer_ligne(j, noms=True)
        gls = [gl for gl in r["morceaux"] if x in gl or y in gl]
        for gl in gls:
            dire("   le morceau %s : %s" % ("+".join(sorted(gl)), r["morceaux"][gl]))
        dire("   R13, sa raison : %s" % (P.pas_jumelle_pourquoi(I, {x, y}).strip(" ;") or "(aucune raison nommee)"))
        dire("   les pieces du bien :")
        for q in sorted(D.par_bien.get(b, [])):
            montrer_piece(q, sorted(D.lignes_bien.get(b, set())))
        dire("   genres des vraies pieces du bien : %s" % dict(Counter(D.REG[q]["genre"] for q in D.par_bien.get(b, [])
                                                                       if I.nature[q] == PC.VRAIE)))


# ═══════════════════════════════════════ 4. LE BIEN 39845 ════════════════════════════════════════════════════════════
def section_4():
    dire("\n=== 4. LE BIEN 39845 -- une vue")
    b = "39845"
    lignes = sorted(D.lignes_bien.get(b, set()))
    for q in sorted(D.par_bien.get(b, [])):
        montrer_piece(q, lignes)
    for j in lignes:
        montrer_ligne(j, noms=True)
        dire("        rattachee au bien par : %s" % sorted(D.rattache_par.get((b, j), set())))
    loc = sqlite3.connect("file:C:/Hektor/Projet/phase2/phase2.sqlite?mode=ro", uri=True)
    dire("   le gel (copie locale de app_classeur_lien) : ligne, piece, role, confiance, preuves, ETAGE")
    for row in loc.execute("select id_unique, ligne_classeur, app_affaire_id, role, confiance, preuves, etage "
                           "from app_classeur_lien where app_affaire_id in (%s) or id_unique in (%s) order by 1, 3" % (
                               ",".join(map(str, D.par_bien.get(b, []))), ",".join("'%s'" % j for j in lignes))):
        dire("     %s" % (row,))


# ═══════════════════════════ 5. LES DEUX PAIRES : CE QUE SON EXCEPTION NOMMEE DONNERAIT ═══════════════════════════════
def section_5():
    dire("\n=== 5. LES DEUX PAIRES : l'exception SIMULEE (l'annulee sort du bien -> rien a etiqueter), en memoire")
    for b, x, y in PAIRES:
        avant = juger_temoin(b)
        D.lignes_bien[b].discard(y)
        try:
            apres = juger(b, PAR_BIEN[b] - {y})
        finally:
            D.lignes_bien[b].add(y)
        dire("   bien %s, %s hors du bien :" % (b, y))
        for j in sorted(avant):
            o = apres.get(j)
            dire("     %s : %s %s -> %s ; 16/11 : %s" % (
                j, avant[j]["verdict"], avant[j].get("motif") or numero(avant[j].get("etiquette")),
                "%s %s pieces %s" % (o["verdict"], numero(o.get("etiquette")) if o["verdict"] == "TRANCHEE" else o["motif"],
                                     o.get("pieces")) if o else "RIEN A ETIQUETER (l'exception)",
                AVIS[j]["numero_du_16_11"] if j in AVIS else "hors des 2 560"))
        juger(b, PAR_BIEN[b])
    dire("\n   TEMOIN « ELLE RENTRE SEULE » (son point 2) : 130d81ac, avec puis sans une piece pretee EN MEMOIRE a son bien")
    i, b = "130d81ac", "62503"
    v = I.sheet["par_id"][i][0]
    r0 = P.juger_ligne(I, i, v)
    existait = b in D.par_bien
    q = sorted(D.par_bien["9705"])[0]
    D.par_bien[b] = [q]
    try:
        r1 = P.juger_ligne(I, i, v)
    finally:
        if existait:
            pass
        else:
            del D.par_bien[b]
    dire("     sans piece : %s -- %s" % (r0["motif"], r0["motif_texte"][:60]))
    dire("     avec une piece (%d pretee) : %s" % (q, "passe E2 : jugee avec son bien, par les epreuves ordinaires"
                                                  if r1 is None else "%s -- %s" % (r1["motif"], r1["motif_texte"][:60])))


# ═══════════════════ 6. CELLES QUI NE DEPLACENT PLUS RIEN : LES SORTIR DES 20, QU'EST-CE QUE CA CHANGE ? ═══════════════
LIBEREES = {1059: "2208", 24600: "48321", 27512: "53740", 24124: "47776"}


def section_6():
    dire("\n=== 6. LES SORTIR DES 20 (son « celles pour qui c'est non n'ont plus de raison d'etre a part ») -- en memoire")
    avant = {b: juger_temoin(b) for b in sorted(set(LIBEREES.values()))}
    P.les_20_a_part()
    garde = set(P._A_PART_20)
    P._A_PART_20.difference_update(LIBEREES)
    try:
        apres = {b: juger(b, PAR_BIEN.get(b, set())) for b in avant}
    finally:
        P._A_PART_20.clear()
        P._A_PART_20.update(garde)
    for b in avant:
        for j in sorted(avant[b]):
            x, y = avant[b][j], apres[b][j]
            dire("     bien %s %s : %s %s -> %s %s%s" % (
                b, j, x["verdict"], x.get("motif") or numero(x.get("etiquette")), y["verdict"],
                y.get("motif") or numero(y.get("etiquette")), "" if cle(x) == cle(y) else "  ⛔ CHANGE"))
        for a in [a for a, bb in LIBEREES.items() if bb == b]:
            r = LAST_R[b]
            dire("       %d : %s" % (a, "donnee a %s" % sorted(r["va"][a]) if a in r["va"] else "reste a part, sans "
                                    "morceau possible" if not r["possibles"].get(a) else "reste a part"))
        juger(b, PAR_BIEN.get(b, set()))


if "6" in SECTIONS:
    section_6()
if "5" in SECTIONS:
    section_5()
if "1" in SECTIONS:
    R1 = section_1()
if "2" in SECTIONS:
    R2 = section_2()
if "3" in SECTIONS:
    section_3()
if "4" in SECTIONS:
    section_4()
dire("\n=== TEMOIN DE L'OUTIL (chaque bien rejuge en memoire contre le passage %d) : %s%s" % (
    PASSAGE, dict(TEMOIN), (" -- ⛔ %s" % ECARTS_OUTIL[:6]) if ECARTS_OUTIL else ""))
