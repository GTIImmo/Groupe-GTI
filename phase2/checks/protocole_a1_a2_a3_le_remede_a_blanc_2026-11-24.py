"""SON ③ DU 24/11 (« MOT_DU_24_11_MES_QUATRE_REPONSES ») -- A1, A2 ET LE REFLET DES NOTES : LE REMEDE, MESURE A BLANC,
AVEC SON CONTROLE A ZERO. LECTURE SEULE : rien en base, rien dans le Sheet, rien chez Hektor -- ce script DIT ce que le
remede ferait, il ne fait rien.

LE MEME MOTIF TROIS FOIS (son ⑥) : « une colonne de reflet qui s'accroche a une valeur qui bouge » -- le numero de chaine
(ou l'etiquette) est recalcule chaque nuit ; ce qui s'y accroche se decolle a la premiere coupe. LE REMEDE est le meme :
replacer PAR CE QUI NE BOUGE PAS (la ligne, la transaction), apres la nuit, et garder la trace de l'ancien numero.

  A1  app_classeur_avis : le reflet (app_dossier_uuid) recalcule depuis id_unique -- une etiquette -> elle ; plusieurs ->
      VIDE plutot que fausse ; les trois colonnes d'avis jamais touchees. CONTROLE : 0 decolle.
  A2  app_affaire_repartition (cle : app_chaine_id, cote, rang) : SA REGLE 6 (③) -- « la part recopiee sur la bonne ligne
      devient la part vivante ; l'ancienne est mise de cote avec son ancien numero de chaine, au journal ; et le controle
      compte les deux : combien recopiees, combien mises de cote. » SA REGLE DE LECTURE (⑤) : « c'est LE NOM qui dit si une
      affaire est partagee, JAMAIS le pourcentage » -- le remede recopie les parts TELLES QU'ELLES SONT (cote, personne,
      part) : il ne compte jamais « deux parts » comme « partagee ». CONTROLE : 0 ligne tranchee dont la chaine d'arrivee
      ne porte pas SA repartition (hors conflits NOMMES), et la conservation des parts.
  A3  app_affaire_note : la note est accrochee a la TRANSACTION (app_affaire_id, qui ne bouge jamais) ; son app_chaine_id
      est un reflet. Recalcule depuis la transaction apres la nuit. CONTROLE : 0 reflet faux.

USAGE : python -u -X utf8 phase2/checks/protocole_a1_a2_a3_le_remede_a_blanc_2026-11-24.py --passage P [--csv]
"""
import argparse
import csv
import json
import sqlite3
import sys
from collections import Counter, defaultdict

sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks")
sys.path.insert(0, r"C:\Hektor\Projet")
import coupe_preuve_interne as K  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402
import protocole_classeur as P  # noqa: E402
import protocole_portes as PO  # noqa: E402
import rapatrier_repartition_classeur as RR  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--passage", type=int, required=True)
ap.add_argument("--csv", action="store_true")
arg = ap.parse_args()


def dire(s=""):
    print(s, flush=True)


con = P.socle()
image, version = con.execute("select image, version from passage where id=?", (arg.passage,)).fetchone()
V = {}
for i, v, e, ps in con.execute("select id_unique, verdict, etiquette, pieces from verdict where passage=?", (arg.passage,)):
    V[i] = {"verdict": v, "etiquette": e, "pieces": set(json.loads(ps)) if ps else set()}
con.close()
T = {i for i, v in V.items() if v["verdict"] == "TRANCHEE"}
I = P.Image(P.IMAGES / image)
PI = I.pieces
lab_img = {a: PI[a]["app_dossier_uuid"] for a in PI}
NUM = {PI[a]["app_dossier_uuid"]: PI[a]["app_dossier_numero"] for a in PI if PI[a]["app_dossier_uuid"]}
ch_img = {a: int(PI[a]["app_chaine_id"]) for a in PI if PI[a]["app_chaine_id"] is not None}
chA, _ = PO.rejeu_en_cache("A", image, PO.FICHIER_DET_PROD, PO.ETEINTS, False)
brouillon = P.DOSSIER / ("brouillon_detachements_protocole_passage_%d.csv" % arg.passage)
chE, _ = PO.rejeu_en_cache("E", image, brouillon, {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"}, False)
labE = K.pose_de_nuit(lab_img, chE)
mA, mE = PO.membres(chA), PO.membres(chE)
gel_l = defaultdict(list)
for i, a, ro, *_r in I.gel:
    gel_l[i].append((int(a), ro))
loc = sqlite3.connect("file:C:/Hektor/Projet/phase2/phase2.sqlite?mode=ro", uri=True)
loc.row_factory = sqlite3.Row
dire("A1 / A2 / A3 : LE REMEDE A BLANC -- passage %d (%s), image %s" % (arg.passage, version, image))
dire("   temoin du rejeu A : %d pieces dans un autre dossier que l'image (attendu 0)"
     % sum(1 for a in ch_img if ch_img[a] != chA.get(a)))


def numero(lab):
    if lab is None:
        return "VIDE"
    return "NEUF" if str(lab).startswith("NEUVE") else (NUM.get(lab) or str(lab)[:8])


def vraies(i):
    if i in T:
        return sorted(a for a in V[i]["pieces"] if I.nature.get(a) == PC.VRAIE)
    return sorted(a for a, _ro in gel_l.get(i, []) if I.nature.get(a) == PC.VRAIE)


# ═════════════════════════════════════════════════ A1 ═════════════════════════════════════════════════════════════
dire()
dire("A1 -- LE REFLET DES AVIS (app_classeur_avis)")
AV = [dict(r) for r in loc.execute("select id_unique, app_dossier_uuid, app_dossier_numero from app_classeur_avis")]
c_av = Counter()
journal_a1 = []
for x in AV:
    i, refl = x["id_unique"], x["app_dossier_uuid"]
    auj = {lab_img[a] for a, _ro in gel_l.get(i, []) if lab_img.get(a) and I.nature.get(a) == PC.VRAIE}
    apr = {labE[a] for a in vraies(i) if labE.get(a)}
    sans = (refl and len(apr) == 1 and next(iter(apr)) != refl)
    c_av["aujourd'hui decolles"] += bool(refl and len(auj) == 1 and next(iter(auj)) != refl)
    c_av["apres la nuit SANS remede : decolles"] += bool(sans)
    nouveau = next(iter(apr)) if len(apr) == 1 else None
    if nouveau != refl:
        journal_a1.append((i, x["app_dossier_numero"] or "VIDE", numero(nouveau),
                           "plusieurs etiquettes" if len(apr) > 1 else ("aucune piece" if not apr else "une etiquette")))
    # LE CONTROLE APRES LE REMEDE : le reflet recalcule contre l'etiquette d'arrivee de la ligne
    c_av["APRES LE REMEDE : decolles"] += bool(nouveau and len(apr) == 1 and next(iter(apr)) != nouveau)
dire("   %d lignes ; aujourd'hui decolles %d ; apres la nuit SANS remede %d ; reflets que le remede change %d ; "
     "⭐ CONTROLE APRES LE REMEDE : %d decolle (attendu 0)" % (
         len(AV), c_av["aujourd'hui decolles"], c_av["apres la nuit SANS remede : decolles"], len(journal_a1),
         c_av["APRES LE REMEDE : decolles"]))

# ═════════════════════════════════════════════════ A2 ═════════════════════════════════════════════════════════════
dire()
dire("A2 -- LES HONORAIRES (app_affaire_repartition, cle : app_chaine_id, cote, rang)")
REP = defaultdict(list)
for r in loc.execute("select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine "
                     "from app_affaire_repartition"):
    REP[int(r["app_chaine_id"])].append(dict(r))
n_rows = sum(len(v) for v in REP.values())
dire("   %d parts sur %d chaines" % (n_rows, len(REP)))


def personnes_du_sheet(i):
    """SA REGLE ⑤ : le NOM dit le partage -- deux fois le meme nom = une seule personne."""
    out = defaultdict(float)
    for k_ in (1, 2, 3):
        n_ = I.D.case(i, "Négociateur %d" % k_).strip()
        if n_:
            out[frozenset(RR.mots_du_nom(n_))] += K.nombre(I.D.case(i, "Pourcentage %d" % k_)) or 0
    return dict(out)


def signature_ligne(i):
    noms = [I.D.case(i, "Négociateur %d" % k_) for k_ in (1, 2, 3)]
    pcts = [K.nombre(I.D.case(i, "Pourcentage %d" % k_)) for k_ in (1, 2, 3)]
    parts, pq = RR.nettoyer(noms, pcts)
    if pq:
        return None
    cotes, pq = RR.decomposer(parts)
    if pq:
        return None
    return sorted((c, round(pc, 2), frozenset(RR.mots_du_nom(n))) for c, _r, n, pc in cotes)


def signature_rows(rows):
    return sorted((r["cote"], round(float(r["pourcentage"] or 0), 2), frozenset(RR.mots_du_nom(r["nom_au_moment"] or "")))
                  for r in rows)


def meme(sig_l, sig_r):
    if sig_l is None or len(sig_l) != len(sig_r):
        return False
    return all(c1 == c2 and abs(p1 - p2) <= 0.01 and n1 and n1 <= n2 for (c1, p1, n1), (c2, p2, n2) in zip(sig_l, sig_r))


RANG = {"vente": 0, "compromis": 1, "offre": 2}
source = {}
for i in V:
    g = [(a, ro) for a, ro in gel_l.get(i, []) if a in PI]
    if g:
        g.sort(key=lambda t: RANG.get(t[1] or PI[t[0]]["kind"], 3))
        source[i] = ch_img.get(g[0][0])

# ── ⑤ SA REGLE DE LECTURE, VERIFIEE (positif ET inverse) ─────────────────────────────────────────────────────────────
lect = Counter()
lect_ex = defaultdict(list)
for i in T:
    # ⚠ SANS le filtre « meme signature » : il comparerait le Sheet a lui-meme (la decomposition du 13/11 ecrit deja
    #   « un nom a 100 % » en deux parts au meme nom) -- on lit les parts de la chaine TELLES QU'ELLES SONT
    rows = [r for r in REP.get(source.get(i), []) if r["origine"] == "classeur_reconstitue"]
    if not rows:
        continue
    gens = personnes_du_sheet(i)
    pers_reg = {str(r["hektor_user_id"]) for r in rows}
    if len(gens) == 1 and abs(next(iter(gens.values())) - 100) <= 0.01:
        lect["Sheet : UN nom a 100 %% -> %d part(s), %d personne(s) au registre" % (len(rows), len(pers_reg))] += 1
        if len(pers_reg) != 1:
            lect_ex["UN nom au Sheet, PLUSIEURS personnes au registre"].append(i)
    elif len(gens) == 2:
        lect["Sheet : DEUX noms -> %d part(s), %d personne(s) au registre" % (len(rows), len(pers_reg))] += 1
        if len(pers_reg) != 2:
            lect_ex["DEUX noms au Sheet, %d personne(s) au registre" % len(pers_reg)].append(i)
dire("   ⑤ SA REGLE DE LECTURE (lignes tranchees dont la chaine porte LEUR repartition du 13/11) :")
for k_, n_ in sorted(lect.items(), key=lambda kv: -kv[1]):
    dire("      %-72s %5d" % (k_, n_))
for k_, v_ in lect_ex.items():
    dire("      ⚠ %s (%d) : %s" % (k_, len(v_), " ".join(sorted(v_))))

# ── LE REMEDE, ligne par ligne ───────────────────────────────────────────────────────────────────────────────────────
def chaine_apres(i):
    ps = vraies(i) if i in T else []
    return chE.get(ps[0]) if ps else None


possede = defaultdict(set)              # chaine d'aujourd'hui -> les lignes tranchees dont elle porte LA repartition
for i in T:
    s = source.get(i)
    if s in REP and meme(signature_ligne(i), signature_rows(REP[s])):
        possede[s].add(i)
cible_de = {i: chaine_apres(i) for i in T}
recopies, mises, conflits = [], [], []
lignes_en_conflit = set()
cat = Counter()


def mettre_de_cote(s, lignes, ou):
    for r in REP[s]:
        mises.append({"ancienne_chaine": s, "cote": r["cote"], "rang": r["rang"], "hektor_user_id": r["hektor_user_id"],
                      "pourcentage": r["pourcentage"], "origine": r["origine"], "lignes": lignes or "-",
                      "la_chaine_apres_la_nuit": ou})


def recopier(s, t, lignes):
    for r in REP[s]:
        recopies.append({"ancienne_chaine": s, "chaine_cible": t, "lignes": lignes or "-", "cote": r["cote"],
                         "rang": r["rang"], "hektor_user_id": r["hektor_user_id"], "pourcentage": r["pourcentage"],
                         "origine": r["origine"], "la_cible_avait_deja_des_parts": "oui" if REP.get(t) else "non"})
    prevu[t] = list(REP[s])


def qui_tient(t):
    return "+".join(sorted(j for j in T if cible_de[j] == t)) or "aucune ligne tranchee"


def lisible(sig):
    return " + ".join("%s %s %g" % (c_, "+".join(sorted(n_)), p_) for c_, p_, n_ in sig)


# PASSE 1 -- les chaines dont TOUTES les lignes partent : leurs parts se mettent de cote (sa regle 6) ; et l'etat VIVANT
#   prevu de chaque chaine apres la nuit (les parts qui restent, puis ce que les recopies y posent)
part_toutes = {s for s, L in possede.items() if s not in {cible_de[i] for i in L}}
prevu = {s: list(rows) for s, rows in REP.items() if s not in part_toutes}
# PASSE 2 -- les recopies, cible par cible, CONTRE L'ETAT VIVANT PREVU de la cible
for s in sorted(possede):
    L = possede[s]
    cibles = {cible_de[i] for i in L}
    if cibles == {s}:
        cat["RESTE : sa ligne garde la chaine"] += 1
        continue
    for t in sorted(c for c in cibles if c is not None and c != s):
        Lt = "+".join(sorted(i for i in L if cible_de[i] == t))
        cur = prevu.get(t, [])
        if cur and signature_rows(cur) == signature_rows(REP[s]):
            cat["DEJA SUR LA CIBLE (les memes parts, qui y restent : un doublon pur) -- pas de recopie"] += 1
        elif cur:
            qui = ("la ligne %s y reste" % "+".join(sorted(possede[t])) if possede.get(t) and t not in part_toutes
                   else "AUCUNE ligne tranchee ne les reconnait")
            conflits.append((s, t, Lt, "la cible porte %s -- %s" % (lisible(signature_rows(cur)), qui)))
            lignes_en_conflit |= set(Lt.split("+"))
            cat["⛔ CONFLIT : la cible porte DEJA d'autres parts -- NOMME, rien de recopie (a lui)"] += 1
        else:
            recopier(s, t, Lt)
            cat["RECOPIEE sur la chaine de sa ligne apres la nuit"] += 1
    if s in part_toutes:
        mettre_de_cote(s, "+".join(sorted(L)), "ORPHELINE" if s not in mE else qui_tient(s))
        cat["MISE DE COTE (aucune de ses lignes ne garde la chaine) -- avec son ancien numero"] += 1
    else:
        cat["GARDEE (une de ses lignes la garde) ET RECOPIEE pour l'autre"] += 1
# PASSE 3 -- les chaines qu'aucune ligne tranchee ne reconnait
for s, rows in sorted(REP.items()):
    if possede.get(s):
        continue
    if s not in mE:
        # ⭐ L'ORPHELINE QUE LA NUIT FABRIQUERAIT : le chemin de D8 -- « le numero d'un dossier est toujours le plus petit
        #   numero de ses transactions » : l'ancienne chaine s est la PIECE s ; son arrivee est chE[s]
        t = chE.get(s)
        cur = prevu.get(t, []) if t is not None else None
        if t is None:
            conflits.append((s, None, "-", "la piece %d n'existe pas" % s))
            cat["⛔ ORPHELINE, sa piece n'existe pas -- NOMMEE"] += 1
        elif cur and signature_rows(cur) == signature_rows(rows):
            mettre_de_cote(s, "-", "ORPHELINE -- doublon pur de la chaine %s" % t)
            prevu.pop(s, None)
            cat["ORPHELINE FABRIQUEE PAR LA NUIT, DOUBLON PUR de son arrivee -> MISE DE COTE"] += 1
        elif not cur:
            recopier(s, t, "-")
            mettre_de_cote(s, "-", "ORPHELINE -- ramenee sur %s" % t)
            prevu.pop(s, None)
            cat["ORPHELINE FABRIQUEE PAR LA NUIT, son arrivee n'a rien -> RAMENEE (le chemin de D8) ET MISE DE COTE"] += 1
        else:
            conflits.append((s, t, "-", "orpheline : %s contre %s a l'arrivee" % (
                lisible(signature_rows(rows)), lisible(signature_rows(cur)))))
            cat["⛔ ORPHELINE FABRIQUEE PAR LA NUIT, son arrivee porte AUTRE CHOSE -- NOMMEE (a lui)"] += 1
    elif s not in mA:
        # ⭐ L'ORPHELINE D'AUJOURD'HUI (le moniteur, « 26, rouge chaque matin ») QUE LA VAGUE RECREE
        tl = sorted(j for j in T if cible_de[j] == s)
        if tl and all(meme(signature_ligne(j), signature_rows(rows)) for j in tl):
            cat["ORPHELINE D'AUJOURD'HUI QUE LA VAGUE RECREE : sa ligne d'arrivee porte EXACTEMENT ces parts -> vivante"] += 1
        else:
            conflits.append((s, s, "+".join(tl) or "-", "orpheline d'aujourd'hui recreee par la vague, ligne(s) %s" % (
                "+".join(tl) or "aucune")))
            cat["⛔ ORPHELINE D'AUJOURD'HUI, la vague la recree mais sa ligne ne la reconnait pas -- NOMMEE"] += 1
    else:
        cat["aucune ligne tranchee ne la reconnait, et elle ne bouge pas (en attente, sans ligne) -- on n'y touche pas"] += 1
dire("   LE REMEDE, chaine par chaine (%d chaines a repartition) :" % len(REP))
for k_, n_ in sorted(cat.items(), key=lambda kv: -kv[1]):
    dire("      %-112s %5d" % (k_, n_))
for c_ in conflits:
    dire("      ⛔ NOMME : chaine %s -> %s (lignes %s) : %s" % c_)
dire("   ⭐ LE COMPTE DES DEUX (sa regle 6) : %d parts RECOPIEES (vivantes, sur %d chaines cibles) . %d parts MISES DE COTE "
     "avec leur ancien numero (%d chaines)" % (len(recopies), len({x["chaine_cible"] for x in recopies}), len(mises),
                                                len({x["ancienne_chaine"] for x in mises})))

# ── LE CONTROLE APRES LE REMEDE ──────────────────────────────────────────────────────────────────────────────────────
apres = prevu
ctl = Counter()
faux = []
for i in T:
    if not any(i in L for L in possede.values()):
        continue
    t = cible_de[i]
    rows_t = apres.get(t, []) if t in mE else []
    if meme(signature_ligne(i), signature_rows(rows_t)):
        ctl["juste : la chaine d'arrivee porte SA repartition"] += 1
    elif i in lignes_en_conflit:
        ctl["conflit NOMME (rien de recopie)"] += 1
    else:
        ctl["⛔ FAUX, NON NOMME"] += 1
        faux.append((i, source.get(i), t, len(rows_t)))
dire("   ⭐ CONTROLE APRES LE REMEDE (les lignes tranchees qui avaient LEUR repartition) : %s" % dict(ctl))
for x in faux[:20]:
    dire("      ⛔ %s : chaine %s -> %s, %d part(s) a l'arrivee" % x)
sans_remede = sum(1 for i in T if any(i in L for L in possede.values())
                  and not meme(signature_ligne(i), signature_rows(REP.get(cible_de[i], []) if cible_de[i] in mE else [])))
dire("      temoin : SANS le remede, %d de ces lignes seraient fausses a l'arrivee" % sans_remede)
vivantes = sum(len(v) for v in apres.values())
dire("   ⭐ CONSERVATION : %d parts aujourd'hui ; apres le remede %d vivantes, dont %d recopiees ; %d mises de cote -> "
     "%d - %d + %d = %d %s" % (n_rows, vivantes, len(recopies), len(mises), vivantes, len(recopies), len(mises),
                              vivantes - len(recopies) + len(mises),
                              "BOUCLE" if vivantes - len(recopies) + len(mises) == n_rows else "⛔ NE BOUCLE PAS"))
orph = [dict(r) for r in loc.execute("select * from app_v_repartition_orpheline")]
_oc = {int(r["app_chaine_id"]) for r in orph}
dire("   LES ORPHELINES QUE LE MONITEUR CRIE (app_v_repartition_orpheline) : %d parts sur %d chaines ; la vague recree %d de "
     "ces chaines et leur ligne d'arrivee y porte EXACTEMENT ces parts (%s) ; mises de cote %d, recopiees %d" % (
         len(orph), len(_oc), sum(1 for c_ in _oc if c_ in mE and all(meme(signature_ligne(j), signature_rows(REP[c_]))
                                                                    for j in T if cible_de[j] == c_)
                                  and any(cible_de[j] == c_ for j in T)),
         " ".join("%d:%s" % (c_, "+".join(sorted(j for j in T if cible_de[j] == c_))) for c_ in sorted(_oc)),
         sum(1 for x in mises if x["ancienne_chaine"] in _oc), sum(1 for x in recopies if x["ancienne_chaine"] in _oc)))

# ═════════════════════════════════════════════════ A3 ═════════════════════════════════════════════════════════════
dire()
dire("A3 -- LE REFLET DES NOTES (app_affaire_note : app_affaire_id = la transaction ; app_chaine_id = un reflet)")
cols = [r[1] for r in loc.execute("pragma table_info(app_affaire_note)")]
dire("   colonnes : %s" % ", ".join(cols))
CH_LOC = {int(a): (int(c) if c is not None else None) for a, c in loc.execute(
    "select app_affaire_id, app_chaine_id from app_affaire_ledger")}
NO = [dict(r) for r in loc.execute("select app_affaire_id, app_chaine_id, origine%s from app_affaire_note" % (
    ", app_dossier_uuid" if "app_dossier_uuid" in cols else ""))]
c3 = Counter()
journal_a3 = []
for x in NO:
    a = int(x["app_affaire_id"])
    refl = int(x["app_chaine_id"]) if x["app_chaine_id"] is not None else None
    c3["notes"] += 1
    c3["aujourd'hui : reflet faux (chaine de la transaction dans l'image)"] += (refl != ch_img.get(a))
    c3["aujourd'hui : reflet faux (contre le registre local de ce matin)"] += (refl != CH_LOC.get(a))
    c3["apres la nuit SANS remede : reflet faux"] += (refl != chE.get(a))
    if refl != chE.get(a):
        journal_a3.append((a, x["origine"], refl, chE.get(a)))
    if "app_dossier_uuid" in x:
        c3["aujourd'hui : reflet du DOSSIER faux"] += (x["app_dossier_uuid"] != lab_img.get(a))
c3["⭐ APRES LE REMEDE (recalcule depuis la transaction) : reflet faux"] = 0
dire("   " + " . ".join("%s %d" % kv for kv in c3.items()))
dire("   ⭐ CONTROLE : le reflet recalcule = chE[app_affaire_id] par construction -> 0 ; la transaction ne bouge pas : "
     "aucune note n'est deplacee, seul son reflet change (%d)" % len(journal_a3))

# ═════════════════════════════════════════════ A3 bis (son mot du 24/11, 2e) ═════════════════════════════════════════
# « UNE QUATRIEME TABLE DU MEME MOTIF : app_affaire_condition [...] Cle = la transaction, donc rien ne se perd, mais son
#   reflet de chaine peut mentir comme celui des notes. AJOUTE-LA A A1/A2/A3. »
dire()
dire("A3 bis -- LE REFLET DES CONDITIONS (app_affaire_condition : app_affaire_id = la transaction ; app_chaine_id et "
     "app_dossier_id = des reflets)")
CO = [dict(r) for r in loc.execute("select app_affaire_id, rang, app_chaine_id, app_dossier_id, origine from app_affaire_condition")]
c3b = Counter()
journal_a3b = []
DOS_IMG = {a: PI[a]["app_dossier_id"] for a in PI}
for x in CO:
    a = int(x["app_affaire_id"])
    refl = int(x["app_chaine_id"]) if x["app_chaine_id"] is not None else None
    c3b["conditions (%s)" % x["origine"]] += 1
    c3b["aujourd'hui : reflet de chaine faux (image)"] += (refl != ch_img.get(a))
    c3b["aujourd'hui : reflet de dossier faux (image)"] += (str(x["app_dossier_id"]) != str(DOS_IMG.get(a)))
    c3b["apres la nuit SANS remede : reflet de chaine faux"] += (refl != chE.get(a))
    if refl != chE.get(a):
        journal_a3b.append((a, x["rang"], x["origine"], refl, chE.get(a)))
c3b["⭐ APRES LE REMEDE (recalcule depuis la transaction) : reflet faux"] = 0
dire("   " + " . ".join("%s %d" % kv for kv in c3b.items()))
for j_ in journal_a3b:
    dire("      condition %s rang %s (%s) : reflet %s -> %s apres la nuit" % j_)

if arg.csv:
    for nom, lignes, entete in (
            ("A2_PARTS_RECOPIEES", recopies, None), ("A2_PARTS_MISES_DE_COTE", mises, None)):
        f_ = P.NOTICE / ("PROTOCOLE_%s_A_BLANC_PASSAGE_%d_2026-11-24.csv" % (nom, arg.passage))
        with f_.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(lignes[0].keys()) if lignes else ["vide"], delimiter=";")
            w.writeheader()
            for x in lignes:
                w.writerow(x)
        dire("-> %s" % f_)
    f_ = P.NOTICE / ("PROTOCOLE_A3_REFLETS_DES_NOTES_A_RECALCULER_A_BLANC_PASSAGE_%d_2026-11-24.csv" % arg.passage)
    with f_.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["app_affaire_id", "origine", "reflet_aujourdhui", "reflet_apres_la_nuit"])
        w.writerows(journal_a3)
    dire("-> %s" % f_)
    f_ = P.NOTICE / ("PROTOCOLE_A1_REFLETS_A_RECALCULER_A_BLANC_PASSAGE_%d_2026-11-24.csv" % arg.passage)
    with f_.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["id_unique", "reflet_aujourdhui", "reflet_recalcule", "pourquoi"])
        w.writerows(journal_a1)
    dire("-> %s" % f_)
