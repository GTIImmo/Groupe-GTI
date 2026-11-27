"""L'AUDIT DES 18 COLONNES (27/11) -- LECTURE SEULE. Rien en base, rien dans le Sheet, rien chez Hektor.

Son mot du 27/11 : « Avant de poser quoi que ce soit : un audit. Pour chacune des 18 colonnes, dis-moi, colonne par colonne
et chiffre par chiffre : combien de cases mon Sheet porte · combien sont deja chez nous · combien manquent · combien
d'ecarts. Je veux tes chiffres, et je veux savoir ou tu ne sais pas repondre. »

LES SOURCES :
  - le Sheet : la photo de l'image du passage 82 (2026-11-26_094931) -- la meme que le verdict, ligne par ligne ;
  - le verdict : le passage 82 du socle (les pieces de chaque ligne TRANCHEE) ;
  - CHEZ NOUS : la base EN DIRECT (le pooler, en lecture seule) -- donc avec les gestes du 27/11 ;
  - l'annuaire des negociateurs : la copie locale (phase2.sqlite), comme le controle du § 7.

LES CASES D'UNE LIGNE EN ATTENTE (70 au 82) ne se comparent pas : elle n'a pas de pieces sures. Elles sont COMPTEES a part :
c'est la ou je ne sais pas repondre.

USAGE : python -u -X utf8 phase2/checks/audit_18_colonnes_du_classeur_2026-11-27.py
"""
import csv
import json
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date

sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks")
sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P  # noqa: E402
import coupe_preuve_interne as K  # noqa: E402
import rapatrier_repartition_classeur as RR  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
PASSAGE, IMAGE = 82, "2026-11-26_094931"
SORTIE = P.NOTICE / "AUDIT_18_COLONNES_DU_CLASSEUR_2026-11-27.csv"


def dire(s=""):
    print(s, flush=True)


# ── le verdict du 82 ──
con = sqlite3.connect("file:%s?mode=ro" % P.SOCLE.as_posix(), uri=True)
V = {}
for i, num, v, e, ps, m in con.execute("select id_unique, num, verdict, etiquette, pieces, motif from verdict "
                                       "where passage=?", (PASSAGE,)):
    V[i] = {"num": num, "verdict": v, "etiquette": e, "pieces": [int(a) for a in json.loads(ps)] if ps else [],
            "motif": m}
con.close()
T = sorted(i for i in V if V[i]["verdict"] == "TRANCHEE")
ATT = sorted(i for i in V if V[i]["verdict"] != "TRANCHEE")
TIENT = defaultdict(set)
for i in T:
    for a in V[i]["pieces"]:
        TIENT[a].add(i)

# ── le Sheet de l'image ──
S = json.loads((P.IMAGES / IMAGE / "sheet.json").read_text(encoding="utf-8"))
COL = {c: k for k, c in enumerate(S["entete"])}
ROW = {}
DOUBLES = []
for i, ent in S["par_id"].items():
    ROW[i] = ent[0]["row"]
    if len(ent) > 1:
        DOUBLES.append(i)


def case(i, c):
    r = ROW.get(i) or []
    k = COL[c]
    return (str(r[k]) if k < len(r) and r[k] is not None else "").strip()


# ── chez nous, EN DIRECT ──
cn, cu = P.pooler()
cu.execute("select app_affaire_id, kind, state, date, date_acte, montant, prix_net_vendeur, commission_agence, "
           "charge_commission_app, date_annulation_app, vente_reglee_app, numero_facture_app, honoraires_entree_app, "
           "honoraires_sortie_app, app_chaine_id, hektor_annonce_id, numero_mandat, app_dossier_uuid, present_in_hektor, "
           "payload_json, first_seen_at from public.app_affaire_ledger")
cols = [d[0] for d in cu.description]
L = {int(r[0]): dict(zip(cols, r)) for r in cu.fetchall()}
REP = defaultdict(list)
cu.execute("select app_chaine_id, cote, rang, hektor_user_id, pourcentage, origine from public.app_affaire_repartition")
for ch, cote, rang, u, pc, o in cu.fetchall():
    REP[int(ch)].append({"cote": cote, "rang": rang, "u": str(u), "pc": float(pc or 0), "origine": o or ""})
NOTES = defaultdict(list)
cu.execute("select app_affaire_id, origine, texte from public.app_affaire_note")
for a, o, t in cu.fetchall():
    NOTES[int(a)].append((o or "", t or ""))
AVIS = {}
cu.execute("select id_unique, avis_a_envoyer, commentaire_avis, avis_envoye from public.app_classeur_avis")
for i, a1, c1, e1 in cu.fetchall():
    AVIS[i] = {"Avis à envoyer (oui / non)": a1, "Commentaire Avis": c1, "Avis envoyé": e1}
CHARGE = {}
cu.execute("select hektor_annonce_id, numero_mandat, valeur_app, origine from public.app_mandat_champ_app "
           "where champ = 'charge_commission'")
for an, nm, v, o in cu.fetchall():
    CHARGE[(str(an), str(nm))] = (v, o)
cn.close()
dire("AUDIT DES 18 COLONNES -- Sheet de l'image %s, verdict du passage %d, base EN DIRECT" % (IMAGE, PASSAGE))
dire("   lignes : %d (%d tranchees, %d en attente) ; ID en double dans la photo : %d" % (len(V), len(T), len(ATT),
                                                                                       len(DOUBLES)))
dire("   chez nous : %d pieces, %d chaines avec repartition, %d notes, %d avis, %d charges de mandat" % (
    len(L), len(REP), sum(len(x) for x in NOTES.values()), len(AVIS), len(CHARGE)))

# ── l'annuaire (la regle du 13/11) ──
RR.RAP.ALIAS_NEGOCIATEUR = dict(RR.RAP.ALIAS_REPLI)
loc = sqlite3.connect("file:C:/Hektor/Projet/phase2/phase2.sqlite?mode=ro", uri=True)
loc.row_factory = sqlite3.Row
_gens = defaultdict(list)
for r in loc.execute("select hektor_user_id, nom, prenom, is_active from app_hektor_negotiator_agency_directory"):
    nom_ = " ".join(sorted(RR.mots_du_nom(r["nom"])))
    pre_ = " ".join(sorted(RR.mots_du_nom(r["prenom"])))
    if nom_:
        _gens[(nom_, pre_)].append(dict(r))
PAR_NOM = defaultdict(list)
for (nom_, pre_), fiches in _gens.items():
    act = [f_ for f_ in fiches if f_.get("is_active") in (1, "1", True, "true", "True")]
    choix = sorted(act or fiches, key=lambda f_: int(str(f_["hektor_user_id"])))[0]
    PAR_NOM[nom_].append({"nom": nom_, "prenom": pre_, "hektor_user_id": str(choix["hektor_user_id"]),
                          "fiches": len(fiches)})
loc.close()


def norm(s):
    return re.sub(r"[^0-9a-zà-ÿ]", "", (s or "").lower())


def sans_accent(s):
    return "".join(c for c in unicodedata.normalize("NFD", norm(s)) if unicodedata.category(c) != "Mn")


def blanc(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def une_date(s):
    s = str(s or "").strip()
    return K.d_sheet(s) or K.d_reg(s)


def du_genre(i, g):
    return sorted(a for a in V[i]["pieces"] if a in L and L[a]["kind"] == g)


def hon(a):
    m, n = K.nombre(L[a]["montant"]), K.nombre(L[a]["prix_net_vendeur"])
    return (m - n) if (m is not None and n is not None and n > 0) else None


ECARTS = []
R = defaultdict(Counter)       # colonne -> {etat: n}


def note(col, etat, i, sheet="", nous="", piece="", detail=""):
    R[col][etat] += 1
    if etat not in ("1 deja chez nous",):
        ECARTS.append({"colonne": col, "etat": etat, "id_unique": i, "ligne_du_sheet": V[i]["num"] if i in V else "",
                       "verdict": V[i]["verdict"] if i in V else "", "sheet": sheet, "chez_nous": nous,
                       "piece": piece, "detail": detail})


COLONNES = ["Négociateur 1", "Pourcentage 1", "Négociateur 2", "Pourcentage 2", "Négociateur 3", "Pourcentage 3",
            "COMMENTAIRES", "En attente de", "Commission TTC", "Charge Commission", "Compromis", "Vente Fixée",
            "Vente Réglée", "Annulée", "Numéro de facture", "Avis à envoyer (oui / non)", "Commentaire Avis",
            "Avis envoyé"]

# ① LE SHEET PORTE : chaque colonne, case par case, sur toutes les lignes ; les cases des lignes en attente a part
dire()
dire("① LE SHEET PORTE (cases non vides), dont sur une ligne EN ATTENTE (je ne sais pas les placer) :")
for c in COLONNES:
    n = sum(1 for i in V if case(i, c))
    na = sum(1 for i in ATT if case(i, c))
    R[c]["0 le Sheet porte"] = n
    R[c]["0 dont sur une ligne en attente"] = na
    dire("   %-28s %5d   dont en attente %3d" % (c, n, na))

# ② LA REPARTITION (les six colonnes ensemble : un pourcentage n'a pas de sens sans son nom -- la regle du 13/11)
RANG = {"vente": 0, "compromis": 1, "offre": 2}
for i in T:
    noms = [case(i, "Négociateur %d" % k) for k in (1, 2, 3)]
    if not any(noms):
        continue
    ps_ = sorted((a for a in V[i]["pieces"] if a in L), key=lambda a: (RANG.get(L[a]["kind"], 3), a))
    ch = next((int(L[a]["app_chaine_id"]) for a in ps_ if L[a]["app_chaine_id"] is not None
               and int(L[a]["app_chaine_id"]) in REP), None)
    rows = REP.get(ch, [])
    st = " | ".join("%s %s" % (n, case(i, "Pourcentage %d" % k)) for k, n in zip((1, 2, 3), noms) if n)
    nous = " + ".join("%s %s %g%% (%s)" % (r["cote"], r["u"], r["pc"], r["origine"])
                      for r in sorted(rows, key=lambda r: (r["cote"], r["rang"]))) or "AUCUNE"
    pcts = [K.nombre(case(i, "Pourcentage %d" % k)) for k in (1, 2, 3)]
    parts, pq = RR.nettoyer(noms, pcts)
    refus = ("nettoyage : " + pq) if pq else ""
    qui = {}
    if not refus:
        for nom, _p in parts:
            q, motif = RR.resoudre(nom, PAR_NOM, None, {r["u"] for r in rows})
            if motif:
                refus = "resolution : %s -> %s" % (nom, motif)
                break
            qui[nom] = q["hektor_user_id"]
    if not refus:
        cotes, pq = RR.decomposer(parts)
        if pq:
            refus = "decomposition : " + pq
    if refus:
        note("REPARTITION (les 6 colonnes)", "5 je ne sais pas lire la ligne (regle du 13/11)", i, st, nous,
             "chaine %s" % ch, refus)
        continue
    sig = {(c_, qui[n_], round(pc_, 2)) for c_, _r, n_, pc_ in cotes}
    if not ps_:
        note("REPARTITION (les 6 colonnes)", "4 sans piece chez nous", i, st, "", "", "")
    elif not rows:
        note("REPARTITION (les 6 colonnes)", "3 manque (aucune part sur ses chaines)", i, st, "AUCUNE",
             " ".join(map(str, ps_)))
    elif sig == {(r["cote"], r["u"], round(r["pc"], 2)) for r in rows}:
        note("REPARTITION (les 6 colonnes)", "1 deja chez nous", i)
    else:
        org = ",".join(sorted({r["origine"] for r in rows}))
        sous = ("une SUPPOSITION de Hektor jamais remplacee" if all(r["origine"].startswith("hektor") for r in rows)
                else "classeur ou mixte : la personne ou la part differe")
        note("REPARTITION (les 6 colonnes)", "2 ecart", i, st, nous, "chaine %s" % ch, "%s (%s)" % (sous, org))
R["REPARTITION (les 6 colonnes)"]["0 le Sheet porte"] = sum(1 for i in V if any(case(i, "Négociateur %d" % k)
                                                                               for k in (1, 2, 3)))
R["REPARTITION (les 6 colonnes)"]["0 dont sur une ligne en attente"] = sum(
    1 for i in ATT if any(case(i, "Négociateur %d" % k) for k in (1, 2, 3)))

# ③ LES TEXTES (G et F) -- contre app_affaire_note des pieces de la ligne ; « identique » (aux blancs pres),
#   « identique sauf le nettoyage du 17/11 » (pictogrammes, + € ° < > = retires), « different », « absent »
RX = re.compile(r"(?:^|\n)([FG]) : [^\n]*? -- (.*?)(?=\n[FG] : |\Z)", re.S)


def textes(a):
    out = defaultdict(list)
    for o, t in NOTES.get(a, []):
        if not o.startswith("classeur"):
            continue
        ms = list(RX.finditer(t))
        if ms:
            for m in ms:
                out[m.group(1)].append(m.group(2))
        else:
            out["?"].append(t)
    return out


F_CAT = Counter()
F_COURTS = Counter()
for c, lettre in (("COMMENTAIRES", "G"), ("En attente de", "F")):
    for i in T:
        s = case(i, c)
        if not s:
            continue
        if lettre == "F":
            if s == "V":
                note(c, "6 ecartee le 17/11 par decision (« V » seul)", i, s)
                continue
            if not re.search(r"[0-9A-Za-zÀ-ÿ]", s):
                note(c, "6 ecartee le 17/11 par decision (pictogramme seul)", i, s)
                continue
        ps_ = [a for a in V[i]["pieces"] if a in L]
        if not ps_:
            note(c, "4 sans piece chez nous", i, s[:200])
            continue
        tx = [t for a in ps_ for t in textes(a).get(lettre, [])] + [t for a in ps_ for t in textes(a).get("?", [])]
        if any(blanc(t) == blanc(s) for t in tx):
            note(c, "1 deja chez nous", i)
        elif any(norm(t) == norm(s) for t in tx):
            note(c, "2a ecart : le meme texte, abime par le nettoyage du 17/11", i, s[:200],
                 next(t for t in tx if norm(t) == norm(s))[:200])
        elif tx:
            note(c, "2b ecart : un autre texte (le Sheet a bouge depuis le 17/11)", i, s[:200], " // ".join(tx)[:200])
        else:
            note(c, "3 manque (aucune note de cette colonne sur ses pieces)", i, s[:200], "", " ".join(map(str, ps_)))
# ⭐ SA QUESTION SUR « EN ATTENTE DE » : ce qu'il y a vraiment dans les cases (TOUTES les lignes)
for i in V:
    s = case(i, "En attente de")
    if not s:
        continue
    if s == "V":
        F_CAT["« V » seul"] += 1
    elif not re.search(r"[0-9A-Za-zÀ-ÿ]", s):
        F_CAT["pictogramme(s) seul(s)"] += 1
    elif len(re.sub(r"\s", "", s)) <= 3:
        F_CAT["1 a 3 caracteres (hors pictogramme seul)"] += 1
        F_COURTS[s] += 1
    else:
        F_CAT["4 caracteres et plus"] += 1

# ④ LA COMMISSION TTC -- ⛔ AUCUNE CASE A NOUS : on ne peut que la comparer a ce que Hektor porte
for i in T:
    s = case(i, "Commission TTC")
    com = K.nombre(s)
    if not s:
        continue
    if com is None:
        note("Commission TTC", "5 je ne sais pas lire la case", i, s)
        continue
    cps = {a: hon(a) for a in du_genre(i, "compromis") if hon(a) is not None}
    vts = {a: K.nombre(L[a]["commission_agence"]) for a in du_genre(i, "vente")
           if K.nombre(L[a]["commission_agence"]) is not None}
    if not du_genre(i, "compromis") and not du_genre(i, "vente"):
        note("Commission TTC", "4 sans compromis ni vente chez nous", i, s, "", " ".join(map(str, V[i]["pieces"])))
        continue
    ok = any(abs(h - com) <= 1 for h in cps.values()) or any(abs(c * 1.2 - com) <= 1.5 or abs(c - com) <= 1
                                                             for c in vts.values())
    nous = " ; ".join(["compromis %d : %g" % kv for kv in cps.items()] +
                      ["vente %d : %g HT" % kv for kv in vts.items()])
    if ok:
        note("Commission TTC", "1 deja chez nous (chez Hektor)", i)
    elif not cps and not vts:
        note("Commission TTC", "3 manque (ses pieces ne portent ni honoraires ni commission)", i, s, "",
             " ".join(map(str, du_genre(i, "compromis") + du_genre(i, "vente"))))
    elif any(abs(c * 1.2 - com * f) <= 2 for c in vts.values() for f in (0.5, 0.25, 0.75)):
        note("Commission TTC", "2a ecart : la vente porte une PART, le Sheet le total", i, s, nous)
    else:
        note("Commission TTC", "2b ecart : un vrai desaccord de montant", i, s, nous)

# ⑤ LA CHARGE -- sur le MANDAT (le carnet app_mandat_champ_app), par le bien et le numero de mandat DES PIECES
for i in T:
    s = case(i, "Charge Commission")
    if not s:
        continue
    ks = {(str(L[a]["hektor_annonce_id"]), str(L[a]["numero_mandat"])) for a in V[i]["pieces"] if a in L
          and L[a]["numero_mandat"] not in (None, "")}
    vs = {k: CHARGE[k] for k in ks if k in CHARGE}
    if not ks:
        note("Charge Commission", "4 sans mandat sur ses pieces", i, s)
    elif not vs:
        note("Charge Commission", "3 manque (son mandat n'a pas de charge au carnet)", i, s, "", str(sorted(ks)))
    elif any(sans_accent(v[0]) == sans_accent(s) for v in vs.values()):
        note("Charge Commission", "1 deja chez nous", i)
    else:
        note("Charge Commission", "2 ecart", i, s, " ; ".join("%s/%s : %s (%s)" % (k[0], k[1], v[0], v[1])
                                                               for k, v in vs.items()))

# ⑥ LES DATES SANS CASE A NOUS : Compromis (la date du compromis), Vente Fixee (la date de la vente)
for c, g in (("Compromis", "compromis"), ("Vente Fixée", "vente")):
    for i in T:
        s = case(i, c)
        if not s:
            continue
        d = K.d_sheet(s)
        if d is None:
            note(c, "5 je ne sais pas lire la case", i, s)
            continue
        ps_ = du_genre(i, g)
        if not ps_:
            note(c, "4 sans %s chez nous" % g, i, s)
            continue
        ds = {a: K.d_reg(str(L[a]["date"] or "")) for a in ps_}
        if g == "vente":
            ds.update({-a: K.d_reg(str(L[a]["date_acte"] or "")) for a in ps_})
        if any(x == d for x in ds.values()):
            note(c, "1 deja chez nous (chez Hektor)", i)
        elif not any(ds.values()):
            note(c, "3 manque (sa piece n'a pas de date)", i, s, "", " ".join(map(str, ps_)))
        else:
            ecs = sorted(((x - d).days for x in ds.values() if x), key=abs)
            note(c, "2 ecart", i, s, " ; ".join("%d : %s" % (abs(a), x) for a, x in ds.items() if x), "",
                 "ecart %+d jours" % ecs[0])

# ⑦ LES CASES A NOUS : Vente Reglee et Facture (sur la vente), Annulee (sur le compromis, sa regle du 16/11)
ANNUL = Counter()
ANTERIEURES = []
for c, champ, g in (("Vente Réglée", "vente_reglee_app", "vente"), ("Numéro de facture", "numero_facture_app", "vente"),
                    ("Annulée", "date_annulation_app", "compromis")):
    for i in T:
        s = case(i, c)
        if not s:
            continue
        ps_ = du_genre(i, g)
        if not ps_:
            if c == "Annulée":
                offres = du_genre(i, "offre")
                sous = ("seulement une offre (%s)" % "+".join(sorted({str(L[a]["state"]) for a in offres}))
                        if offres else "ni compromis ni offre")
                note(c, "4 sans compromis chez nous : %s" % sous, i, s, "", " ".join(map(str, offres)))
            else:
                note(c, "4 sans vente chez nous", i, s)
            continue
        vals = {a: str(L[a][champ] or "").strip() for a in ps_}
        if c == "Annulée":
            ok = any(une_date(v) == une_date(s) and une_date(s) for v in vals.values())
        elif c == "Vente Réglée":
            ok = any(v == s or (une_date(v) and une_date(v) == une_date(s)) for v in vals.values())
        else:
            ok = any(blanc(v) == blanc(s) for v in vals.values())
        if ok:
            note(c, "1 deja chez nous", i)
            continue
        pleins = {a: v for a, v in vals.items() if v}
        if pleins:
            note(c, "2 ecart", i, s, " ; ".join("%d : %s" % kv for kv in pleins.items()))
            continue
        if c != "Annulée":
            note(c, "3 manque (sa vente existe, la case est vide)", i, s, "", " ".join(map(str, ps_)))
            continue
        d = une_date(s)
        dcs = {a: K.d_reg(str(L[a]["date"] or "")) for a in ps_}
        etats = {a: str(L[a]["state"]) for a in ps_}
        if d and all(x and d < x for x in dcs.values()):
            sous = "date anterieure a son compromis (le garde-fou du 16/11)"
            for a in ps_:
                ANTERIEURES.append((i, a, d, dcs[a], etats[a]))
        elif not any(e in ("cancelled", "annule", "annulé") for e in etats.values()):
            sous = "son compromis n'est pas annule chez nous (%s)" % "+".join(sorted(set(etats.values())))
        else:
            sous = "son compromis annule existe, la date n'y a jamais ete posee"
        note(c, "3 manque : " + sous, i, s, "", " ".join("%d %s %s" % (a, etats[a], dcs[a]) for a in ps_))

# ⑧ LES AVIS -- par l'ID Unique (app_classeur_avis), pas par la piece
for c in ("Avis à envoyer (oui / non)", "Commentaire Avis", "Avis envoyé"):
    for i in T:
        s = case(i, c)
        if not s:
            continue
        nous = AVIS.get(i, {}).get(c)
        if nous is None or str(nous).strip() == "":
            note(c, "3 manque", i, s, "", "", "aucun avis pour cet ID" if i not in AVIS else "")
        elif blanc(str(nous)).lower() == blanc(s).lower():
            note(c, "1 deja chez nous", i)
        else:
            note(c, "2 ecart", i, s, str(nous))

# ── LE RENDU ──
dire()
dire("② COLONNE PAR COLONNE, sur les %d lignes tranchees (les cases des lignes en attente sont au ①) :" % len(T))
ORDRE = ["REPARTITION (les 6 colonnes)", "COMMENTAIRES", "En attente de", "Commission TTC", "Charge Commission",
         "Compromis", "Vente Fixée", "Vente Réglée", "Annulée", "Numéro de facture", "Avis à envoyer (oui / non)",
         "Commentaire Avis", "Avis envoyé"]
for c in ORDRE:
    dire("   %s" % c)
    tot = 0
    for k, n in sorted(R[c].items()):
        dire("      %-75s %5d" % (k, n))
        if not k.startswith("0 "):
            tot += n
    porte_t = R[c]["0 le Sheet porte"] - R[c]["0 dont sur une ligne en attente"]
    dire("      -> somme %d = le Sheet porte sur les tranchees %d : %s" % (tot, porte_t, "BOUCLE" if tot == porte_t
                                                                          else "⛔ NE BOUCLE PAS"))
dire()
dire("③ « EN ATTENTE DE », ce qu'il y a dans les cases (toutes les lignes) : %s" % dict(F_CAT))
dire("   les courtes, les plus frequentes : %s" % F_COURTS.most_common(25))
dire()
dire("④ LES DATES D'ANNULATION ANTERIEURES A LEUR COMPROMIS (le garde-fou) : %d lignes" % len({x[0] for x in ANTERIEURES}))
ecs = sorted((dc - d).days for _i, _a, d, dc, _e in ANTERIEURES if dc)
if ecs:
    dire("   ecart (compromis - annulation) en jours : min %d, mediane %d, max %d" % (ecs[0], ecs[len(ecs) // 2], ecs[-1]))
with open(SORTIE, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(ECARTS[0].keys()), delimiter=";")
    w.writeheader()
    for x in sorted(ECARTS, key=lambda x: (ORDRE.index(x["colonne"]) if x["colonne"] in ORDRE else 99,
                                           x["etat"], x["ligne_du_sheet"] or 0)):
        w.writerow(x)
json.dump([[i, a, str(d), str(dc), e] for i, a, d, dc, e in ANTERIEURES],
          open(P.DOSSIER / "audit_18_anterieures_2026-11-27.json", "w", encoding="utf-8"))
dire("-> %s (%d lignes : tout ce qui n'est pas « deja chez nous »)" % (SORTIE, len(ECARTS)))
