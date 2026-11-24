"""SES 64 DECISIONS DU VERROU (24/11, son mot « LES 64 TRANCHEES, LES REGLES ET LE CONTROLE ») -- LECTURE SEULE.
L'image du 23/11 08:02, le socle en lecture (passage de reference 76), le registre local en lecture (les textes
rapatries, app_affaire_note). Rien en base, rien dans le Sheet, rien chez Hektor.

Son mot : « ⛔ TU NE LES APPLIQUES PAS A L'AVEUGLE. Tu les reprends avec TES propres mesures, et tu me dis si l'une d'elles
ne tient pas, UNE A LA FOIS. Mais le rangement est fait. »

  1  SES DECISIONS, PIECE PAR PIECE -- lues dans SON fichier (C:\\Hektor\\SES_64_DECISIONS_DU_VERROU_23_11.md), jamais
     recopiees : pour chaque piece, la ligne qu'il nomme, ce que le protocole en dit au passage 76, et MES preuves vers
     cette ligne et vers les autres lignes du bien :
       . la DATE au jour exact d'une colonne (la date d'une offre = sa 1re proposition) ;
       . les HONORAIRES = la commission de la ligne, a l'euro (montant - prix net vendeur) ;
       . le PRIX + HONORAIRES (le critere 1 du protocole) ;
       . le TEXTE RAPATRIE (app_affaire_note, classeur:F / classeur:G) quand il ne se retrouve que sur UNE ligne des 4 798
         -- ⚠ il a ete rapatrie PAR LE GEL : il appuie, il ne prouve pas seul (P2, son temoin 1 737 / 5 / 9) ;
       . les CONTRADICTIONS (datee plus de 15 j apres l'annulation de la ligne ; compromis ou vente avant son offre).
     Le verdict de chaque piece : TIENT (une preuve vers sa ligne, aucune vers une autre, aucune contradiction) ; TIENT PAR
     SA STRUCTURE (aucune preuve propre, aucune contre : c'est sa lecture du tableau) ; NE TIENT PAS (une preuve vers une
     AUTRE ligne, ou une contradiction) -- celles-la, UNE A LA FOIS, a lui.
TEMOIN DE L'OUTIL : chaque bien rejuge EN MEMOIRE doit redonner le passage 76 du socle, ligne par ligne.

USAGE : python -u -X utf8 phase2/checks/protocole_ses_64_decisions_du_verrou_2026-11-24.py [1|...]
"""
import sys, json, sqlite3, re
from collections import defaultdict
sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks"); sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P, piece_copie_ou_vraie as PC, coupe_preuve_interne as K
sys.stdout.reconfigure(encoding="utf-8")
PASSAGE = int(next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("--passage=")), 76))
SECTIONS = {a for a in sys.argv[1:] if not a.startswith("--")} or {"1"}
SON_FICHIER = r"C:\Hektor\SES_64_DECISIONS_DU_VERROU_23_11.md"


def dire(s=""):
    print(s, flush=True)


# ── SON FICHIER, lu tel quel ───────────────────────────────────────────────────────────────────────────────────────────
def lire_ses_decisions():
    """bien -> {"lignes": {ligne: etat}, "pieces": [(piece, ligne | None, genre, etat, date, montant, deja)]}."""
    out, b, ligne = {}, None, None
    for brut in open(SON_FICHIER, encoding="utf-8"):
        s = brut.rstrip("\r\n")
        m = re.match(r"^BIEN (\d+)", s)
        if m:
            b = m.group(1)
            out[b] = {"lignes": {}, "pieces": []}
            continue
        if b is None:
            continue
        m = re.match(r"^  ([0-9A-Za-z]{8})  (\S.*?)\s{2,}", s + "  ")
        if m and not s.startswith("   "):
            ligne = m.group(1)
            out[b]["lignes"][ligne] = m.group(2).strip()
            continue
        m = re.match(r"^\s+(DE COTE : )?(\d+)\s+(\S+)\s+(.*)$", s)
        if m:
            reste = m.group(4)
            out[b]["pieces"].append({"piece": int(m.group(2)), "ligne": None if m.group(1) else ligne,
                                     "genre": m.group(3), "texte": reste.strip(),
                                     "deja": "(deja au protocole)" in reste})
    return out


SES = lire_ses_decisions()
I = P.Image(P.IMAGES / "2026-11-23_080234")
D = I.D
con = sqlite3.connect("file:C:/Hektor/chantier_classeur_q6_cache/protocole/socle.sqlite?mode=ro", uri=True)
VREF = {i: {"verdict": v, "etiquette": e, "pieces": json.loads(p) if p else None, "motif": m, "texte": t}
        for i, v, e, p, m, t in con.execute("select id_unique, verdict, etiquette, pieces, motif, motif_texte from verdict "
                                            "where passage=?", (PASSAGE,))}
NUM = {}
for a_, p_ in I.pieces.items():
    if p_["app_dossier_uuid"]:
        NUM[p_["app_dossier_uuid"]] = p_["app_dossier_numero"]
loc = sqlite3.connect("file:C:/Hektor/Projet/phase2/phase2.sqlite?mode=ro", uri=True)
NOTES = defaultdict(list)
for a_, o_, t_ in loc.execute("select app_affaire_id, origine, texte from app_affaire_note"):
    NOTES[int(a_)].append((o_, t_ or ""))


def norm(s):
    """Le texte compare SANS sa ponctuation ni ses espaces : le rapatriement du 17/11 a perdu des signes (« 20/1>Retard » est
    devenu « 20/1Retard », « 25/3+2mois > » est devenu « 25/32mois  ») -- on compare les lettres et les chiffres."""
    return re.sub(r"[^0-9a-zà-ÿ]", "", (s or "").lower())


COL_F, COL_G = "En attente de", "COMMENTAIRES"
TEXTE_LIGNES = defaultdict(set)          # texte normalise -> lignes (sur les 4 798) qui le portent en F ou en G
for i_ in D.LIG:
    for c_ in (COL_F, COL_G):
        t_ = norm(D.case(i_, c_))
        if t_:
            TEXTE_LIGNES[(c_, t_)].add(i_)


def textes_de(a):
    """Les textes rapatries d'une piece : [(colonne, texte, lignes des 4 798 qui le portent)]."""
    out = []
    for o_, t_ in NOTES.get(a, []):
        for bloc in t_.split("\n" if "\nG : " in t_ else "\0"):
            pass
        for m in re.finditer(r"(?:^|\n)([FG]) : [^\n]*? -- (.*?)(?=\n[FG] : |\Z)", t_, re.S):
            col = COL_F if m.group(1) == "F" else COL_G
            out.append((col, m.group(2), sorted(TEXTE_LIGNES.get((col, norm(m.group(2))), set()))))
        if o_ == "classeur":
            mm = re.search(r"ligne (\w{8})", t_)
            out.append(("classeur", t_[:60], [mm.group(1)] if mm else []))
    return out


def numero(lab):
    if lab is None:
        return "-"
    return "NEUF" if str(lab).startswith("NEUVE") else (NUM.get(lab) or str(lab)[:8])


# ── l'enregistreur : la coupe finale du DERNIER jugement de chaque bien ──────────────────────────────────────────────
LAST_R = {}
_couper = K.couper_le_bien


def _rec_couper(D_, b, *a, **k):
    r = _couper(D_, b, *a, **k)
    LAST_R[b] = r
    return r


K.couper_le_bien = _rec_couper


def rejuger(b):
    """Le bien entier rejuge EN MEMOIRE comme le passage (juger_ligne puis juger_bien_garde)."""
    a_juger = set()
    out = {}
    for i in sorted(D.lignes_bien.get(b, set())):
        if i not in I.sheet["par_id"]:
            continue
        v = I.sheet["par_id"][i][0]
        x = P.juger_ligne(I, i, v)
        if x is None:
            if P.r_bien(I, i) == b:
                a_juger.add(i)
        else:
            out[i] = x
    for x in P.juger_bien_garde(I, b, a_juger, "bien") if a_juger else []:
        out[x["id_unique"]] = x
    return out


def resume(x):
    if x is None:
        return "-"
    if x["verdict"] == "TRANCHEE":
        return "TRANCHEE %s %s" % (numero(x.get("etiquette")), x.get("pieces"))
    return "%s %s" % (x["verdict"], x.get("motif"))


def preuves_vers(a, lignes):
    """MES preuves d'une piece vers chaque ligne : {ligne: [preuves]}."""
    p = D.REG[a]
    out = {}
    for i in sorted(lignes):
        pr = []
        for c in K.COLS_DATE.get(p["genre"], []):
            if p["date"] and K.d_sheet(D.case(i, c)) == p["date"]:
                pr.append("DATE « %s » %s" % (c, D.case(i, c).strip()))
        com = K.nombre(D.case(i, "Commission TTC"))
        if p["hon"] is not None and com is not None and abs(p["hon"] - com) <= 1:
            pr.append("HONORAIRES %s = commission" % int(p["hon"]))
        if D.touche_ph(a, i):
            pr.append("PRIX+HON")
        for col, t_, ls in textes_de(a):
            if ls == [i]:
                pr.append("TEXTE %s unique (« %s »)" % ("F" if col == COL_F else ("G" if col == COL_G else "classeur"),
                                                         t_.strip()[:50].replace(chr(10), " / ")))
        ann_app = K.d_reg(I.pieces[a].get("date_annulation_app"))
        if ann_app and K.d_sheet(D.case(i, "Annulée")) == ann_app:
            pr.append("ANNULATION rapatriee %s = « Annulée »" % ann_app)
        out[i] = pr
    return out


def classer(a, L, pv, contre):
    """(verdict, discriminantes vers L, appuis du gel vers L, contre) -- les honoraires / le prix ne DISCRIMINENT que s'ils
    ne touchent QUE la ligne ; le texte et l'annulation rapatries viennent DU GEL (ils appuient, ils ne prouvent pas seuls)."""
    def disc(i):
        out = [x for x in pv.get(i, []) if x.startswith("DATE")]
        hon = [x for x in pv.get(i, []) if x.startswith(("HONORAIRES", "PRIX+HON"))]
        autres_hon = [j for j in pv if j != i and any(x.startswith(("HONORAIRES", "PRIX+HON")) for x in pv[j])]
        if hon and not autres_hon:
            out += hon
        return out
    appui = [x for x in pv.get(L, []) if x.startswith(("TEXTE", "ANNULATION"))]
    d_L = disc(L)
    contre = list(contre)
    for j in pv:
        if j != L and [x for x in pv[j] if x.startswith("DATE")] and not d_L:
            contre.append("sa DATE tombe sur %s" % j)
    hon_L = any(x.startswith("HONORAIRES") for x in pv.get(L, []))
    hon_ailleurs = sorted(j for j in pv if j != L and any(x.startswith("HONORAIRES") for x in pv[j]))
    reserve = ("ses honoraires %d sont la commission de %s, PAS de %s (%s)" % (
        int(D.REG[a]["hon"]), " ".join(hon_ailleurs), L, D.case(L, "Commission TTC").strip())
        if hon_ailleurs and not hon_L else "")
    if contre:
        return "⛔ DOUTE", d_L, appui, contre, reserve
    if d_L:
        return "TIENT PAR SA PREUVE", d_L, appui, contre, reserve
    if appui:
        return "TIENT PAR L'APPUI DU GEL + SA STRUCTURE", d_L, appui, contre, reserve
    return "TIENT PAR SA STRUCTURE SEULE", d_L, appui, contre, reserve


if "1" in SECTIONS:
    dire("=" * 118)
    dire("1 -- SES DECISIONS, PIECE PAR PIECE (lues dans son fichier ; reference : passage %d du socle)" % PASSAGE)
    dire("=" * 118)
    total, libres, deja, cote = 0, 0, 0, 0
    CLASSE = defaultdict(list)
    temoin_ok, temoin_ko = 0, []
    for b, S_ in SES.items():
        J = rejuger(b)
        for i, x in J.items():
            ref = VREF.get(i)
            if ref and (ref["verdict"], ref.get("etiquette"), ref.get("pieces") if ref["verdict"] == "TRANCHEE" else None,
                        ref["motif"]) == (x["verdict"], x.get("etiquette"),
                                          x.get("pieces") if x["verdict"] == "TRANCHEE" else None, x.get("motif")):
                temoin_ok += 1
            else:
                temoin_ko.append((b, i, resume(ref) if ref else "absente", resume(x)))
        r = LAST_R.get(b)
        lignes_b = set(D.lignes_bien.get(b, set()))
        dire()
        dire("BIEN %s -- lignes au Sheet sur ce bien : %s" % (b, " ".join(sorted(lignes_b))))
        for i in sorted(set(S_["lignes"]) | lignes_b):
            dire("   %s  %-26s son etat : %-14s passage %d : %s" % (
                i, D.case(i, "Etat Actuel").strip()[:26] if i in D.LIG else "(hors Sheet)", S_["lignes"].get(i, "-"),
                PASSAGE, resume(VREF.get(i))))
        for e in S_["pieces"]:
            a, L = e["piece"], e["ligne"]
            total += 1
            if e["deja"]:
                deja += 1
            elif L is None:
                cote += 1
            else:
                libres += 1
            p = D.REG.get(a)
            if p is None:
                dire("   ⛔ %d : ABSENTE DU REGISTRE DE L'IMAGE" % a)
                ne_tient.append((b, a, L, "absente du registre"))
                continue
            nat = "copie C5" if I.nature[a] == PC.COPIE else "vraie"
            etat_proto = ("-> %s (%s)" % ("+".join(sorted(r["va"][a])), r["preuve"].get(a, "")[:60]) if r and a in r["va"]
                          else ("A PART (%s)" % (r["apart"].get(a, "?")[:70]) if r and a in r["apart"] else "hors coupe"))
            pv = preuves_vers(a, lignes_b | ({L} if L else set()))
            contre = D.contre_dates(a, {L}) if L else []
            pour = pv.get(L, []) if L else []
            ailleurs = {i: v for i, v in pv.items() if i != L and v}
            marque = ""
            if not e["deja"]:
                if L is None:
                    marque = "DE COTE"
                else:
                    deja_proto = bool(r and a in r["va"] and r["va"][a] == frozenset({L}))
                    v_, d_L, appui, contre_, reserve = classer(a, L, pv, contre)
                    marque = v_ + ("" if not reserve else "  ⚠ " + reserve)
                    CLASSE[v_].append((b, a, L, deja_proto, d_L, appui, contre_, reserve))
            dire("   %s %-7d %-9s %-9s %-10s %8s hon %-6s ch %-7s %-11s %s -> %s%s" % (
                "·" if e["deja"] else "▸", a, p["genre"], (p["etat"] or "")[:9], p["date"] or "sans date",
                int(p["montant"]) if p["montant"] is not None else "-", int(p["hon"]) if p["hon"] is not None else "-",
                I.pieces[a]["app_chaine_id"], I.pieces[a]["app_dossier_numero"] or "-", nat, L or "DE COTE",
                "  (deja rangee)" if e["deja"] else ""))
            dire("        protocole : %s" % etat_proto)
            dire("        mes preuves vers %s : %s%s" % (L or "-", " + ".join(pour) or "aucune",
                                                         ("  ⛔ CONTRE : %s" % "; ".join(contre)) if contre else ""))
            if ailleurs:
                dire("        ⚠ preuves vers une AUTRE ligne : %s" % "; ".join(
                    "%s -> %s" % (i, " + ".join(v)) for i, v in ailleurs.items()))
            if textes_de(a):
                dire("        textes rapatries : %s" % "; ".join(
                    "%s « %s » (%d ligne(s) des 4 798 : %s)" % ("F" if c == COL_F else ("G" if c == COL_G else c),
                                                               t.strip()[:40], len(ls), " ".join(ls[:4]))
                    for c, t, ls in textes_de(a)))
            if marque and not e["deja"]:
                dire("        => %s" % marque)
    dire()
    dire("-" * 118)
    dire("SON FICHIER : %d pieces lues -- %d deja rangees par le protocole, %d donnees par lui, %d mises de cote" % (
        total, deja, libres, cote))
    dire("   (son total : « 64 transactions tranchees par lui, dont 2 mises de cote ; les 14 autres deja rangees »)")
    dire("MES MESURES sur ses %d pieces donnees :" % libres)
    for v_ in ("TIENT PAR SA PREUVE", "TIENT PAR L'APPUI DU GEL + SA STRUCTURE", "TIENT PAR SA STRUCTURE SEULE", "⛔ DOUTE"):
        xs = CLASSE.get(v_, [])
        dp = [x for x in xs if x[3]]
        dire("   %-42s %2d   (dont %d que le protocole donnait DEJA a la meme ligne au passage %d)" % (v_, len(xs), len(dp),
                                                                                                    PASSAGE))
        if v_ != "TIENT PAR SA PREUVE":
            for b, a, L, deja_proto, d_L, appui, contre_, reserve in xs:
                dire("      bien %-6s %-7d -> %s : %s%s%s" % (b, a, L, " + ".join(d_L + appui) or "aucune preuve",
                                                             ("  ⛔ " + " ; ".join(contre_)) if contre_ else "",
                                                             ("  ⚠ " + reserve) if reserve else ""))
    contraires = [x for xs in CLASSE.values() for x in xs if x[3] is False and False]
    autre_ligne = sorted((b, a, L) for xs in CLASSE.values() for (b, a, L, dp, *_r) in xs
                         if LAST_R.get(b) and a in LAST_R[b]["va"] and LAST_R[b]["va"][a] != frozenset({L}))
    dire("   ⛔ pieces que le protocole donne a une AUTRE ligne que la sienne : %d %s" % (len(autre_ligne), autre_ligne))
    dire("TEMOIN DE L'OUTIL : %d lignes rejugees = le passage %d ; %d ecart(s)" % (temoin_ok, PASSAGE, len(temoin_ko)))
    for t in temoin_ko:
        dire("   ⛔ %s %s : socle %s / en memoire %s" % t)
