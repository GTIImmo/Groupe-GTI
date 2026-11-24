"""A1 ET A2, A BLANC (24/11, son mot § 4 : « CE QUI S'ACCROCHE AILLEURS ET SE DECOLLE ») -- LECTURE SEULE.
L'image du 23/11 08:02, le passage P du socle, les rejeux A (la nuit d'aujourd'hui) et E (la nuit avec le brouillon du
passage) EN CACHE (protocole_portes.py --rejeu E --passage P), le registre local en lecture (app_classeur_avis,
app_affaire_repartition). Rien en base, rien dans le Sheet, rien chez Hektor : ce script ne RECOPIE rien, il dit ce qu'une
recopie ferait.

  A1  LES AVIS -- app_classeur_avis porte un REFLET (app_dossier_uuid / app_dossier_numero) pose le 16/11, accroche a
      l'ETIQUETTE. Sa vraie cle est id_unique (la ligne). On mesure :
        . AUJOURD'HUI (temoin positif : ses chiffres, 2 543 / 10 / 25 / 3) -- l'etiquette des pieces gelees de la ligne ;
        . APRES LA NUIT du passage (rejeu E + la pose de nuit) -- les pieces de la ligne : celles du protocole si elle est
          tranchee, celles du gel sinon ;
        . LE REFLET RECALCULE depuis id_unique (sa regle A1 : une seule etiquette -> elle ; plusieurs -> VIDE plutot que
          fausse ; les trois colonnes d'avis jamais touchees) : le controle des decolles doit finir a ZERO.
  A2  LES HONORAIRES -- app_affaire_repartition a pour cle (app_chaine_id, cote, rang) : LA CHAINE. On mesure, chaine par
      chaine, la LIGNE dont elle vient (la regle du rapatriement du 13/11, rapatrier_repartition_classeur.py : la piece la
      plus avancee du gel de la ligne -- vente, sinon compromis, sinon offre -- donne la chaine) et la chaine que cette
      ligne portera apres la nuit (rejeu E). Une chaine coupee dont le numero reste au morceau d'une AUTRE ligne emporte
      les honoraires avec lui -- en silence (D8 ne voit que les orphelines). Sa regle A2 : replacer par LA LIGNE, recopier
      sur le bon morceau, journaliser, garder l'ancien numero de chaine dans la trace.

USAGE : python -u -X utf8 phase2/checks/protocole_a1_a2_avis_et_repartitions_a_blanc_2026-11-24.py --passage P [--csv]
"""
import sys, json, sqlite3, csv, argparse
from collections import Counter, defaultdict
sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks"); sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P, piece_copie_ou_vraie as PC, coupe_preuve_interne as K, protocole_portes as PO
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
I = P.Image(P.IMAGES / image)
lab_img = {a: I.pieces[a]["app_dossier_uuid"] for a in I.pieces}
num_img = {a: I.pieces[a]["app_dossier_numero"] for a in I.pieces}
NUM = {}
for a, u in lab_img.items():
    if u:
        NUM[u] = num_img[a]
chA, _ = PO.rejeu_en_cache("A", image, PO.FICHIER_DET_PROD, PO.ETEINTS, False)
brouillon = P.DOSSIER / ("brouillon_detachements_protocole_passage_%d.csv" % arg.passage)
chE, _ = PO.rejeu_en_cache("E", image, brouillon, {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"}, False)
labE = K.pose_de_nuit(lab_img, chE)
labA = K.pose_de_nuit(lab_img, chA)
gel_l = defaultdict(list)
for i, a, ro, cf, pr, lc in I.gel:
    gel_l[i].append((int(a), ro))
loc = sqlite3.connect("file:C:/Hektor/Projet/phase2/phase2.sqlite?mode=ro", uri=True)
loc.row_factory = sqlite3.Row
dire("A1 / A2 A BLANC -- passage %d (%s), image %s" % (arg.passage, version, image))
dire("   rejeu A temoin : %d pieces ; %d dans un autre dossier que l'image (attendu 0)" % (
    len(chA), sum(1 for a in I.pieces if I.pieces[a]["app_chaine_id"] != chA.get(a))))


def numero(lab):
    if lab is None:
        return "-"
    return "NEUF" if str(lab).startswith("NEUVE") else (NUM.get(lab) or str(lab)[:8])


# ═════════════════════════════════════════════════════ A1 ═════════════════════════════════════════════════════════
dire()
dire("=" * 118)
dire("A1 -- LE REFLET DES AVIS (app_classeur_avis : app_dossier_uuid / app_dossier_numero)")
dire("=" * 118)
AV = [dict(r) for r in loc.execute("select id_unique, app_dossier_uuid, app_dossier_numero, avis_a_envoyer, avis_envoye, "
                                   "commentaire_avis from app_classeur_avis")]
dire("   %d lignes dans la table ; %d avec un numero de dossier" % (len(AV), sum(1 for x in AV if x["app_dossier_uuid"])))


def etiquettes_aujourdhui(i):
    return {lab_img[a] for a, _ro in gel_l.get(i, []) if a in lab_img and lab_img[a] and I.nature.get(a) == PC.VRAIE}


def etiquettes_apres(i):
    v = V.get(i)
    if v and v["verdict"] == "TRANCHEE":
        ps = [a for a in v["pieces"] if I.nature.get(a) == PC.VRAIE]
    else:
        ps = [a for a, _ro in gel_l.get(i, []) if I.nature.get(a) == PC.VRAIE]
    return {labE[a] for a in ps if a in labE and labE[a]}


def classe(reflet, labs):
    if not reflet:
        return "sans numero au reflet"
    if not labs:
        return "la ligne n'a aucune piece"
    if len(labs) > 1:
        return "la ligne porte plusieurs etiquettes"
    return "d'accord" if next(iter(labs)) == reflet else "DECOLLE"


auj, apr, rec = Counter(), Counter(), Counter()
decolles_auj, decolles_apres, recalcul = [], [], []
for x in AV:
    i, refl = x["id_unique"], x["app_dossier_uuid"]
    la, le = etiquettes_aujourdhui(i), etiquettes_apres(i)
    c1, c2 = classe(refl, la), classe(refl, le)
    auj[c1] += 1
    apr[c2] += 1
    if c1 == "DECOLLE":
        decolles_auj.append((i, x["app_dossier_numero"], numero(next(iter(la))), x["avis_envoye"]))
    if c2 == "DECOLLE" and c1 != "DECOLLE":
        decolles_apres.append((i, x["app_dossier_numero"], numero(next(iter(le))), x["avis_envoye"],
                               V.get(i, {}).get("verdict")))
    # SA REGLE A1 : le reflet recalcule depuis id_unique -- une etiquette -> elle ; plusieurs -> VIDE ; aucune -> VIDE
    nouveau = next(iter(le)) if len(le) == 1 else None
    if nouveau != refl:
        recalcul.append((i, x["app_dossier_numero"] or "-", numero(nouveau) if nouveau else "VIDE",
                         "plusieurs etiquettes" if len(le) > 1 else ("aucune piece" if not le else "une etiquette"),
                         x["avis_envoye"]))
    rec[classe(nouveau, le) if nouveau else ("VIDE (plusieurs etiquettes)" if len(le) > 1 else
                                              ("VIDE (aucune piece)" if not le else "VIDE"))] += 1
dire("   AUJOURD'HUI (l'etiquette des pieces gelees de la ligne, image) : " + " . ".join(
    "%s %d" % kv for kv in auj.most_common()))
dire("      ses chiffres : 2 543 d'accord . 10 DECOLLES . 25 plusieurs etiquettes . 3 aucune piece gelee")
for t in decolles_auj:
    dire("      DECOLLE aujourd'hui : %s  reflet %s, ses pieces %s  (avis envoye : %s)" % t)
dire("   APRES LA NUIT DU PASSAGE %d (rejeu E + la pose de nuit ; pieces du protocole si tranchee, du gel sinon) : %s" % (
    arg.passage, " . ".join("%s %d" % kv for kv in apr.most_common())))
for t in decolles_apres:
    dire("      DECOLLE PAR LES COUPES : %s  reflet %s, a l'arrivee %s  (avis envoye : %s ; %s)" % t)
dire("   LE REFLET RECALCULE DEPUIS id_unique (sa regle A1) : %s" % " . ".join("%s %d" % kv for kv in rec.most_common()))
dire("      ⭐ le controle des decolles apres recalcul : %d (attendu 0)" % rec.get("DECOLLE", 0))
dire("      %d reflets changeraient (les trois colonnes d'avis : jamais touchees) :" % len(recalcul))
for t in recalcul:
    dire("         %s  %s -> %s  (%s ; avis envoye : %s)" % t)

# ═════════════════════════════════════════════════════ A2 ═════════════════════════════════════════════════════════
dire()
dire("=" * 118)
dire("A2 -- LES HONORAIRES (app_affaire_repartition, cle : app_chaine_id, cote, rang)")
dire("=" * 118)
REP = defaultdict(list)
for r in loc.execute("select app_chaine_id, cote, rang, nom_au_moment, pourcentage, origine from app_affaire_repartition"):
    REP[int(r["app_chaine_id"])].append(dict(r))
dire("   %d lignes de repartition sur %d chaines" % (sum(len(v) for v in REP.values()), len(REP)))
# la ligne d'ou vient chaque chaine (la regle du rapatriement du 13/11 : la piece la plus avancee du gel donne la chaine ;
#   deux lignes sur une chaine : la meme repartition -> la premiere est gardee ; une divergence -> la plus recente gagne)
import rapatrier_repartition_classeur as RR  # noqa: E402
RANG = {"vente": 0, "compromis": 1, "offre": 2}
source = defaultdict(set)
for i in V:
    g = [(a, ro) for a, ro in gel_l.get(i, []) if a in I.pieces]
    if not g:
        continue
    g.sort(key=lambda t: RANG.get(t[1] or I.pieces[t[0]]["kind"], 3))
    source[I.pieces[g[0][0]]["app_chaine_id"]].add(i)
mA, mE = PO.membres(chA), PO.membres(chE)
coupees = sorted(c for c in mA if mA[c] != mE.get(c, set()))
dire("   chaines d'aujourd'hui qui changent de membres a la nuit du passage : %d ; dont %d portent une repartition" % (
    len(coupees), sum(1 for c in coupees if c in REP)))
T = {i for i, v in V.items() if v["verdict"] == "TRANCHEE"}


def chaine_apres(i):
    """La chaine que la ligne portera apres la nuit : celle de sa plus petite vraie piece (protocole si tranchee)."""
    ps = sorted(a for a in V[i]["pieces"] if I.nature.get(a) == PC.VRAIE) if i in T else []
    return chE.get(ps[0]) if ps else None


def signature_ligne(i):
    """La repartition que la REGLE DU 13/11 tirerait de la ligne : [(cote, rang, mots du nom, part)] -- ou None."""
    noms = [I.D.case(i, "Négociateur %d" % k) for k in (1, 2, 3)]
    pcts = [K.nombre(I.D.case(i, "Pourcentage %d" % k)) for k in (1, 2, 3)]
    parts, pq = RR.nettoyer(noms, pcts)
    if pq:
        return None
    cotes, pq = RR.decomposer(parts)
    if pq:
        return None
    return sorted((c, round(pc, 2), frozenset(RR.mots_du_nom(n))) for c, _r, n, pc in cotes)


def signature_lignes_rep(rows):
    return sorted((r["cote"], round(float(r["pourcentage"] or 0), 2), frozenset(RR.mots_du_nom(r["nom_au_moment"] or "")))
                  for r in rows)


def meme_repartition(sig_l, sig_r):
    """Meme cote, meme part, et les mots du nom de la ligne DANS le nom de la fiche (le classeur n'ecrit souvent que le
    nom de famille)."""
    if sig_l is None or len(sig_l) != len(sig_r):
        return False
    for (c1, p1, n1), (c2, p2, n2) in zip(sig_l, sig_r):
        if c1 != c2 or abs(p1 - p2) > 0.01 or not n1 or not (n1 <= n2):
            return False
    return True


etat = lambda i: I.D.case(i, "Etat Actuel").strip()  # noqa: E731
CAS = defaultdict(list)
journal = []
for c in coupees:
    if c not in REP:
        continue
    rows = REP[c]
    sig_r = signature_lignes_rep(rows)
    origines = ",".join(sorted({r["origine"] for r in rows}))
    noms = " + ".join("%s %s %s%%" % (r["cote"], r["nom_au_moment"], "%g" % (r["pourcentage"] or 0))
                      for r in sorted(rows, key=lambda r: (r["cote"], r["rang"])))
    bien = str(I.pieces[c]["hektor_annonce_id"]) if c in I.pieces else str(I.pieces[min(mA[c])]["hektor_annonce_id"])
    src = sorted(source.get(c, set()))
    porteurs = sorted(i for i in T if any(a in mE.get(c, set()) for a in V[i]["pieces"]))
    orpheline = c not in mE
    if not src:
        CAS["SANS LIGNE SOURCE (aucune ligne du gel sur cette chaine)"].append((bien, c, "-", "-", origines, noms))
        continue
    for L in src:
        if L not in T:
            CAS["SA LIGNE EST EN ATTENTE (le protocole ne la tranche pas : on n'y touche pas)"].append(
                (bien, c, L, etat(L), origines, noms))
            continue
        ca = chaine_apres(L)
        dit = meme_repartition(signature_ligne(L), sig_r)
        if ca == c:
            CAS["RESTE AVEC SA LIGNE"].append((bien, c, L, etat(L), origines, noms))
            continue
        if not dit:
            CAS["LA LIGNE PERD LA CHAINE, MAIS CE N'EST PAS SA REPARTITION (une autre ligne de la chaine l'a donnee)"].append(
                (bien, c, L, etat(L), origines, noms + " ; la ligne : " + " | ".join(
                    "%s %s" % (I.D.case(L, "Négociateur %d" % k).strip(), I.D.case(L, "Pourcentage %d" % k).strip())
                    for k in (1, 2, 3) if I.D.case(L, "Négociateur %d" % k).strip())))
            continue
        quoi = ("ORPHELINE (la chaine disparait : D8 la voit)" if orpheline else
                "⛔ MUET -- la chaine %d reste a %s" % (c, "+".join("%s (%s)" % (j, etat(j)) for j in porteurs)
                                                         if porteurs else "AUCUNE LIGNE"))
        cle = ("⛔ UNE VENTE REGLEE PERD SES HONORAIRES" if etat(L) == "Vente réglée" else
               "⛔ UNE AUTRE LIGNE PERD SA REPARTITION") + " -- elle portera la chaine %s, sans repartition" % ""
        CAS[cle].append((bien, c, L, etat(L), origines, noms + " ; " + quoi + " ; sa chaine apres la nuit : %s" % ca))
        for r in rows:
            journal.append({"bien": bien, "ancienne_chaine": c, "chaine_cible_apres_la_nuit": ca, "ligne": L,
                            "etat_de_la_ligne": etat(L), "cote": r["cote"], "rang": r["rang"],
                            "nom_au_moment": r["nom_au_moment"], "pourcentage": r["pourcentage"], "origine": r["origine"],
                            "l_ancienne_chaine_reste_a": "+".join(porteurs) or ("ORPHELINE" if orpheline else "AUCUNE LIGNE"),
                            "la_cible_a_deja_une_repartition": "oui" if ca in REP else "non"})
ordre = sorted(CAS, key=lambda k: (not k.startswith("⛔ UNE VENTE"), not k.startswith("⛔"), k))
for k in ordre:
    xs = CAS[k]
    dire("   %-118s %d" % (k, len(xs)))
    if k.startswith("RESTE") or k.startswith("SANS LIGNE") or k.startswith("SA LIGNE EST"):
        for t in xs[:6]:
            dire("      bien %-6s chaine %-7s %-9s %-13s (%s) [%s]" % t)
        if len(xs) > 6:
            dire("      ... et %d autres (le fichier les porte toutes)" % (len(xs) - 6))
    else:
        for t in xs:
            dire("      bien %-6s chaine %-7s %-9s %-13s (%s) [%s]" % t)
non_coupees = [c for c in REP if c in mA and mA[c] == mE.get(c, set())]
dire("   TEMOIN INVERSE : %d chaines a repartition ne changent pas de membres a la nuit -- leur repartition ne bouge pas"
     % len(non_coupees))
dire("   ⭐ SA REGLE A2, A BLANC : %d ligne(s) de repartition seraient RECOPIEES sur la chaine que LEUR LIGNE portera apres la "
     "nuit, journalisees avec leur ancien numero de chaine ; l'ancienne reste ou elle est (on ne supprime pas une part : "
     "la mettre de cote, a sa decision)" % len(journal))
if arg.csv:
    f = P.NOTICE / ("PROTOCOLE_A2_REPARTITIONS_A_RECOPIER_A_BLANC_PASSAGE_%d_2026-11-24.csv" % arg.passage)
    with f.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(journal[0].keys()) if journal else ["vide"], delimiter=";")
        w.writeheader()
        for j in journal:
            w.writerow(j)
    f1 = P.NOTICE / ("PROTOCOLE_A1_REFLETS_A_RECALCULER_A_BLANC_PASSAGE_%d_2026-11-24.csv" % arg.passage)
    with f1.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["id_unique", "reflet_aujourdhui", "reflet_recalcule", "pourquoi", "avis_envoye"])
        for t in recalcul:
            w.writerow(t)
    dire("-> %s" % f)
    dire("-> %s" % f1)
