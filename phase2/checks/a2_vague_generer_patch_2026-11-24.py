"""A2 DE LA VAGUE DU SOIR -- LE PATCH PAR PIECES, ET SON ESSAI A BLANC SUR L'ETAT D'ARRIVEE SIMULE (son 10e mot du 24/11).

SON MOT : « VAS-Y DES CE SOIR SUR LES TROIS PIECES QUI RESTENT -- c'est de la lecture et de la fabrication, rien ne s'ecrit
[...] : le patch A2 par pieces avec son essai a blanc sur l'etat d'arrivee simule ». ⛔ « Rien ne bouge cette nuit : ni
vague, ni A2 pose ». CE SCRIPT N'ECRIT RIEN EN BASE : il LIT Supabase (le pooler en `read only`) et FABRIQUE des fichiers.

ENTREE : l'export d'A2 v3 du script du temps 2 (`--export-a2`), c'est-a-dire SA regle telle qu'elle a ete mesuree :
  recopies (la part suit sa ligne), mises de cote (regle 6 : une part n'est jamais supprimee), la completee (NRZVKH85),
  les membres de chaque chaine touchee A L'ARRIVEE, les pieces qui changent de chaine (la simulation).

« PAR PIECES » : les parts a deplacer vivent sous l'ANCIEN numero de chaine (c'est la qu'elles sont, et il ne bouge pas tant
qu'on n'y touche pas) ; leur CIBLE est designee par une PIECE -- « la chaine ou arrive la piece P » -- et le numero de cette
chaine est lu au moment du geste. Le numero d'une chaine est le plus petit app_affaire_id de ses membres
(affaire_ledger.py, « ON NUMEROTE A LA FIN ») : la garde des membres le rend donc exact.

LES GARDES (toutes avant le moindre geste ; une seule qui refuse -> rien n'est ecrit) :
  G0  le patch ne se rejoue pas (sauvegarde absente, lot absent du journal) ;
  G1  LES PIECES : chaque chaine touchee porte EXACTEMENT les membres que le rejeu prevoit (empreinte, et le detail par chaine
      dans le refus) -- c'est elle qui prouve que le chainage est arrive la ou on l'attendait ;
  G2  LES PARTS DE DEPART : les parts des chaines touchees sont EXACTEMENT celles lues a la fabrication (empreinte) ; les cibles
      sont vides ; la chaine de NRZVKH85 porte sa seule part d'entree ;
  G3  LES VENTES REGLEES SANS PART, a l'arrivee et avant A2 : exactement la liste prevue (chaines nommees).
LE GESTE, dans cet ordre : la sauvegarde datee (toute la table) -> le journal (chaque part, sa ligne d'origine, sa place de
depart et d'arrivee, l'ancienne valeur) -> les recopies (depuis les parts vivantes que G2 vient de prouver) -> les mises de
cote (entieres, avec leur ancien numero de chaine) puis leur retrait -> la completee.
LES CONTROLES : les membres n'ont pas bouge ; chaque cible porte les parts prevues, sommes a 100 ; ventes reglees sans part
a l'arrivee = 0 ; conservation (apres = avant + recopiees - mises de cote + completee) ; chaque mise de cote est entiere
(contre la sauvegarde) ; le journal ; l'empreinte d'apres (exigee au patch reel : elle sort de l'essai a blanc).

FICHIERS (supabase/) :
  patch_a2_vague_<date>.sql                  le patch reel (begin ... commit) -- ⛔ joue SEULEMENT a l'etape 7 de la vague
  patch_a2_vague_<date>_PREGARDE.sql         lecture seule : G2 et la liste de G3 SANS les membres (avant le point de non-retour)
  patch_a2_vague_<date>_A_BLANC_SIMULE.sql   l'essai : pose les chaines du rejeu, joue A2, controle, joue l'inverse, verifie que
                                             tout est revenu, et ANNULE (raise final) -- rien ne reste
  patch_a2_vague_<date>_INVERSE.sql          le retour arriere (begin ... commit)
  patch_a2_vague_<date>_REPETITION.sql       lecture seule, apres le geste

USAGE : python -X utf8 phase2/checks/a2_vague_generer_patch_2026-11-24.py --export FICHIER.json [--date 2026-11-25]
        [--empreinte-apres MD5]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks")
sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--export", required=True)
ap.add_argument("--date", default="2026-11-24", help="la date du lot (le jour de la vague)")
ap.add_argument("--empreinte-apres", default="", help="l'empreinte d'apres, rendue par l'essai a blanc simule")
arg = ap.parse_args()

X = json.loads(Path(arg.export).read_text(encoding="utf-8"))
LOT = "a2_vague_%s" % arg.date
TAB = "app_affaire_repartition_avant_a2vague_%s" % arg.date.replace("-", "")
OUT = Path(r"C:\Hektor\Projet\supabase")
BASE = "patch_a2_vague_%s" % arg.date


def dire(s=""):
    print(s, flush=True)


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


class T(str):
    """Un gabarit SQL : %(nom)s est remplace par son nom, un % seul est laisse tel quel, %% devient %."""

    def __mod__(self, d):
        import re
        return re.sub(r"%\((\w+)\)s|%%", lambda m: "%" if m.group(0) == "%%" else str(d[m.group(1)]), self)


# ─── LES ENSEMBLES ────────────────────────────────────────────────────────────────────────────────────────────────
REC, MIS, COMP = X["recopies"], X["mises"], X["completees"]
assert all(x["geste"] == "recopie" for x in REC), "un echange : ce generateur ne le sait pas (aucun en v3)"
paires = defaultdict(set)                       # (s, piece cible) -> lignes
for x in REC:
    paires[(x["ancienne_chaine"], x["chaine_cible"])].add(x["lignes"])
PAIRES = sorted((s, t, "+".join(sorted(L))) for (s, t), L in paires.items())
MISES_CH = defaultdict(set)
for x in MIS:
    MISES_CH[x["ancienne_chaine"]].add(x["lignes"])
SOURCES = sorted({s for s, _t, _l in PAIRES} | set(MISES_CH))
CIBLES = sorted({t for _s, t, _l in PAIRES})
assert not set(SOURCES) & set(CIBLES), "une chaine a la fois source et cible : ce generateur ne le sait pas"
assert len(COMP) == 1 and COMP[0]["lignes"] == "NRZVKH85", COMP
CC = COMP[0]
CH_COMP = CC["app_chaine_id"]
TOUCHEES = sorted(set(SOURCES) | set(CIBLES) | {CH_COMP})
MEMBRES = {int(c): sorted(int(a) for a in v) for c, v in X["membres_a_l_arrivee"].items()}
assert set(MEMBRES) == set(TOUCHEES), (len(MEMBRES), len(TOUCHEES))
for t in CIBLES + [CH_COMP]:
    assert MEMBRES[t] and MEMBRES[t][0] == t, "la cible %s n'est pas la tete de ses membres %s" % (t, MEMBRES[t][:5])
VERS_DE = defaultdict(set)
for s, t, _l in PAIRES:
    VERS_DE[s].add(t)
dire("A2 PAR PIECES -- export du passage %s (image %s) : %d recopies en %d paires, %d mises de cote sur %d chaines, "
     "1 completee ; %d chaines touchees (%d sources, %d cibles) ; %d pieces changent de chaine" % (
         X["passage"], X["image"], len(REC), len(PAIRES), len(MIS), len(MISES_CH), len(TOUCHEES), len(SOURCES),
         len(CIBLES), len(X["simulation_chaines"])))

# ─── G1 : l'empreinte des membres, calculee ici comme le SQL la calculera ───────────────────────────────────────────
memb_txt = ";".join("%d:%s" % (c, ",".join(map(str, MEMBRES[c]))) for c in TOUCHEES if MEMBRES[c])
E_MEMBRES = hashlib.md5(memb_txt.encode()).hexdigest()
N_MEMBRES = sum(len(v) for v in MEMBRES.values())

# ─── G2 : les parts de depart, LUES chez Supabase (lecture seule) et comparees a l'export ───────────────────────────
cn, cu = P.pooler()
LISTE = ", ".join(map(str, TOUCHEES))
cu.execute("select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage::text, origine, ecrit_par "
           "from public.app_affaire_repartition where app_chaine_id in (%s)" % LISTE)
VIV = defaultdict(list)
for r in cu.fetchall():
    VIV[int(r[0])].append(r)
attendu = defaultdict(set)
for x in REC + MIS:
    attendu[x["ancienne_chaine"]].add((x["cote"], int(x["rang"]), str(x["hektor_user_id"]), x["nom_au_moment"],
                                        float(x["pourcentage"]), x["origine"]))
ecarts = []
for s in SOURCES:
    vu = {(r[1], int(r[2]), str(r[3]), r[4], float(r[5]), r[6]) for r in VIV.get(s, [])}
    if vu != attendu[s] or len(VIV.get(s, [])) != len(attendu[s]):
        ecarts.append((s, sorted(vu), sorted(attendu[s])))
for t in CIBLES:
    if VIV.get(t):
        ecarts.append((t, "cible NON VIDE", VIV[t]))
vu_c = VIV.get(CH_COMP, [])
if len(vu_c) != 1 or vu_c[0][1] != "entree" or vu_c[0][1] == CC["cote"]:
    ecarts.append((CH_COMP, "completee", vu_c))
for s in MISES_CH:
    n_mises = sum(1 for x in MIS if x["ancienne_chaine"] == s)
    if n_mises != len(VIV.get(s, [])):
        ecarts.append((s, "mise de cote PARTIELLE", n_mises, len(VIV.get(s, []))))
if ecarts:
    dire("⛔ LES PARTS VIVANTES NE SONT PAS CELLES DE L'EXPORT (%d) :" % len(ecarts))
    for e in ecarts[:20]:
        dire("   %s" % (e,))
    sys.exit(1)
N_PARTS_TOUCHEES = sum(len(v) for v in VIV.values())
EXPR_PARTS = ("md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, "
              "origine, ecrit_par), ';' order by app_chaine_id, cote, rang), ''))")
cu.execute("select %s from public.app_affaire_repartition where app_chaine_id in (%s)" % (EXPR_PARTS, LISTE))
E_PARTS = cu.fetchone()[0]
cu.execute("select count(*), %s from public.app_affaire_repartition" % EXPR_PARTS)
N_TABLE, E_TABLE = cu.fetchone()
cu.execute("select count(*) from public.app_affaire_repartition_mise_de_cote")
N_MDC = cu.fetchone()[0]
cu.execute("select count(*) from public.app_classeur_realignement_journal")
N_JOURNAL = cu.fetchone()[0]
cn.rollback()
dire("G2 : les %d parts des %d chaines touchees = l'export, part par part ; empreinte %s ; table %d parts (%s) ; "
     "mise de cote %d ; journal %d" % (N_PARTS_TOUCHEES, len(TOUCHEES), E_PARTS[:8], N_TABLE, E_TABLE[:8], N_MDC, N_JOURNAL))

# ─── LE MOTIF DE CHAQUE MISE DE COTE, NOMME -- et PROUVE quand « les memes parts vivent deja la-bas » ──────────────────
REFUS = defaultdict(list)
for s_, t_, L_ in X["refus_annulee"]:
    REFUS[s_].append((t_, L_))
SIMC = {int(a): int(c) for a, c in X["simulation_chaines"].items()}
a_lire = sorted({SIMC[s_] for s_ in MISES_CH if s_ not in VERS_DE and s_ not in REFUS and s_ in SIMC} - set(TOUCHEES))
if a_lire:
    cn, cu = P.pooler()
    cu.execute("select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage::text, origine, ecrit_par "
               "from public.app_affaire_repartition where app_chaine_id in (%s)" % ", ".join(map(str, a_lire)))
    for r in cu.fetchall():
        VIV[int(r[0])].append(r)
    cn.rollback()
sig = lambda rows: sorted((r[1], int(r[2]), str(r[3]), float(r[5])) for r in rows)
MOTIF, VERS_MISE = {}, {}
for s_ in sorted(MISES_CH):
    L_ = "+".join(sorted(MISES_CH[s_]))
    # ✅ SON MOT du 24/11 (11e) : « LES 42 CHAINES SANS LIGNE NI PART A L'ARRIVEE : ca me va, puisque AUCUNE ne porte de
    #   vente reglee. Tu les NOMMES au journal avec leur raison, et on n'y touche pas. »
    reste = (" ; la chaine %d RESTE a l'arrivee (membres %s) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune "
             "vente reglee, on n'y touche pas)" % (s_, ",".join(map(str, MEMBRES[s_]))) if MEMBRES.get(s_) else "")
    if s_ in VERS_DE:
        VERS_MISE[s_] = min(VERS_DE[s_])
        MOTIF[s_] = "%s quitte la chaine %d -> recopiee sur la chaine de la piece %d%s" % (
            L_ if L_ != "-" else "la chaine disparait, sans ligne :", s_, VERS_MISE[s_], reste)
    elif L_ == "NRZVKH85":
        VERS_MISE[s_] = CH_COMP
        MOTIF[s_] = ("NRZVKH85 quitte la chaine %d pour %d (qui portait son entree) -> completee de sa sortie%s" % (
            s_, CH_COMP, reste))
    elif s_ in REFUS:
        VERS_MISE[s_] = None
        MOTIF[s_] = "%s arrive sur %s, une ANNULEE (son 3e mot : aucune part) -> aucune " \
                    "recopie%s%s" % (L_, " ; ".join("la chaine %d" % t_ for t_, _l in REFUS[s_]),
                                     " ; U0GQ3KTO EN RESERVE (8RWTD0YX, meme mandat 14065)" if "U0GQ3KTO" in L_ else "", reste)
    elif s_ in SIMC and sig(VIV.get(SIMC[s_], [])) == sig(VIV.get(s_, [])):
        VERS_MISE[s_] = s_
        MOTIF[s_] = ("la chaine %d disparait (la piece %d rejoint %d) -> les MEMES parts y vivent deja%s" % (
            s_, s_, SIMC[s_], reste))
    else:
        dire("⛔ mise de cote SANS MOTIF : chaine %d (%s)" % (s_, L_))
        sys.exit(1)
dire("MOTIFS des %d chaines mises de cote : %s" % (len(MOTIF), dict(__import__("collections").Counter(
    ("recopiee" if "recopiee" in m_ else "annulee" if "ANNULEE" in m_ else "memes parts" if "MEMES" in m_ else
     "completee") + (" (la chaine reste)" if " RESTE a l'arrivee (" in m_ else "") for m_ in MOTIF.values()))))
NOMMEES = sorted(s_ for s_ in MISES_CH if MEMBRES.get(s_))
dire("NOMMEES (son mot du 24/11) : %d chaines restent a l'arrivee sans ligne ni part : %s" % (
    len(NOMMEES), ", ".join(map(str, NOMMEES))))

# ─── G3 : les ventes reglees sans part A L'ARRIVEE, avant A2 (chaines nommees) ─────────────────────────────────────
# a l'arrivee (simulee ou reelle) : une chaine dont un membre est une VENTE reglee et qui ne porte aucune part
SQL_VR = """select coalesce(string_agg(c::text, ',' order by c), '') from (
    select distinct l.app_chaine_id c from public.app_affaire_ledger l
     where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null
       and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) x"""
VR_APRES = ",".join(map(str, sorted(X["garde_vente_reglee_sql_attendue"])))
assert VR_APRES == "", VR_APRES

# ─── LES FRAGMENTS SQL ────────────────────────────────────────────────────────────────────────────────────────────
V_PAIRES = ",\n    ".join("(%d, %d, %s)" % (s, t, q(l)) for s, t, l in PAIRES)
V_MISES = ",\n    ".join("(%d, %s, %s, %s)" % (s, q("+".join(sorted(L))),
                                              str(VERS_MISE[s]) if VERS_MISE[s] is not None else "null", q(MOTIF[s]))
                         for s, L in sorted(MISES_CH.items()))
D = {"lot": LOT, "tab": TAB, "liste": LISTE, "e_membres": E_MEMBRES, "n_membres": N_MEMBRES, "e_parts": E_PARTS,
     "n_parts": N_PARTS_TOUCHEES, "expr_parts": EXPR_PARTS, "sql_vr": SQL_VR, "v_paires": V_PAIRES, "v_mises": V_MISES,
     "n_rec": len(REC), "n_paires": len(PAIRES), "n_mis": len(MIS), "n_mis_ch": len(MISES_CH), "ch_comp": CH_COMP,
     "c_cote": CC["cote"], "c_rang": CC["rang"], "c_uid": CC["hektor_user_id"], "c_nom": q(CC["nom_au_moment"]),
     "c_pct": "%g" % float(CC["pourcentage"]), "n_cibles": len(CIBLES), "n_touchees": len(TOUCHEES),
     "n_journal": len(REC) + len(MIS) + 1, "cibles": ", ".join(map(str, CIBLES)),
     "sources": ", ".join(map(str, SOURCES)), "passage": X["passage"], "image": X["image"],
     "src": "phase2/checks/a2_vague_generer_patch_2026-11-24.py",
     "nommees": ", ".join(map(str, NOMMEES)) or "-1", "n_nommees": len(NOMMEES)}
D["n_net"] = len(REC) - len(MIS) + 1

EXPR_MEMBRES = T("""(select md5(coalesce(string_agg(x, ';' order by c), '')) from (
     select app_chaine_id c, app_chaine_id || ':' || string_agg(app_affaire_id::text, ',' order by app_affaire_id) x
       from public.app_affaire_ledger where app_chaine_id in (%(liste)s) group by app_chaine_id) m)""")
D["expr_membres_lit"] = EXPR_MEMBRES % D
D["expr_membres"] = EXPR_MEMBRES % dict(D, liste="select c from a2_touchees")
D["liste_lit"] = LISTE
D["cibles_lit"] = D["cibles"]
D["liste"] = "select c from a2_touchees"
D["cibles"] = "select c from a2_cibles"
D["v_touchees"] = ",\n    ".join(", ".join("(%d)" % c for c in TOUCHEES[i:i + 16]) for i in range(0, len(TOUCHEES), 16))
D["v_cibles"] = ",\n    ".join(", ".join("(%d)" % c for c in CIBLES[i:i + 16]) for i in range(0, len(CIBLES), 16))

PREAMBULE = T("""
-- ─── ⓪ LES PIECES DU LOT, une seule fois : les chaines touchees, les cibles, les paires, les mises de cote ─────────────
create temporary table a2_touchees (c bigint primary key) on commit drop;
insert into a2_touchees values
    %(v_touchees)s;
create temporary table a2_cibles (c bigint primary key) on commit drop;
insert into a2_cibles values
    %(v_cibles)s;
-- « de la chaine s (l'ancienne, la ou vivent les parts) vers la chaine ou arrive la piece P »
create temporary table a2_paires (s bigint, piece bigint, lignes text) on commit drop;
insert into a2_paires values
    %(v_paires)s;
create temporary table a2_mises (s bigint, lignes text, vers_piece bigint, motif text) on commit drop;
insert into a2_mises values
    %(v_mises)s;
""")

GARDES = T("""
-- ─── ① LES GARDES -- une seule qui refuse, et RIEN n'est ecrit ─────────────────────────────────────────────────────
do $$
declare n int; e text; d text;
begin
  -- G0 : le patch ne se rejoue pas
  if to_regclass('public.%(tab)s') is not null then
    raise exception '⛔ G0 : la sauvegarde %(tab)s existe deja -- ce patch ne se rejoue pas';
  end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s';
  if n <> 0 then raise exception '⛔ G0 : % ligne(s) du lot %(lot)s deja au journal', n; end if;
  -- G1 : LES PIECES -- chaque chaine touchee porte EXACTEMENT les membres que le rejeu prevoit
  e := %(expr_membres)s;
  if e <> '%(e_membres)s' then
    select string_agg(app_chaine_id || ' (' || count_ || ')', ', ') into d from (
      select app_chaine_id, count(*) count_ from public.app_affaire_ledger where app_chaine_id in (%(liste)s)
       group by 1 order by 1) z;
    raise exception '⛔ G1 : les membres des %(n_touchees)s chaines touchees ne sont pas ceux du rejeu (empreinte % au lieu de %(e_membres)s) -- le chainage n''est pas arrive la ou on l''attendait. Chaines (membres) : %', e, d;
  end if;
  select count(*) into n from public.app_affaire_ledger where app_chaine_id in (%(liste)s);
  if n <> %(n_membres)s then raise exception '⛔ G1 : % membres au lieu de %(n_membres)s', n; end if;
  -- G2 : LES PARTS DE DEPART sont exactement celles lues a la fabrication ; les cibles sont vides
  e := (select %(expr_parts)s from public.app_affaire_repartition where app_chaine_id in (%(liste)s));
  if e <> '%(e_parts)s' then
    raise exception '⛔ G2 : les parts des chaines touchees ont change depuis la fabrication (empreinte % au lieu de %(e_parts)s)', e;
  end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (%(liste)s);
  if n <> %(n_parts)s then raise exception '⛔ G2 : % parts sur les chaines touchees au lieu de %(n_parts)s', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (%(cibles)s);
  if n <> 0 then raise exception '⛔ G2 : % part(s) deja sur les %(n_cibles)s cibles -- elles devaient etre vides', n; end if;
  -- G3 : les ventes reglees sans part, A L'ARRIVEE et avant A2 : exactement la liste prevue
  e := (%(sql_vr)s);
  if e <> '%(vr_avant)s' then
    raise exception '⛔ G3 : ventes reglees sans part a l''arrivee : [%] au lieu de [%(vr_avant)s]', e;
  end if;
  raise notice '✅ gardes : membres % (%(n_membres)s), parts % (%(n_parts)s), cibles vides, ventes reglees sans part [%(vr_avant)s]',
    '%(e_membres)s', '%(e_parts)s';
end $$;
""")

GESTE = T("""
-- ─── ② LA SAUVEGARDE DATEE : la table ENTIERE (une part n'est jamais supprimee, elle se retrouve) ─────────────────────
create table public.%(tab)s as select * from public.app_affaire_repartition;
revoke all on public.%(tab)s from public, anon, authenticated;

-- ─── ④ LE JOURNAL : chaque part, sa ligne d'origine, sa place de depart et d'arrivee, l'ancienne valeur ────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   lot_origine, pourquoi, ecrit_par)
select '%(lot)s', row_number() over (order by k, s, cote, rang, piece), 'repartition',
       'app_affaire_repartition (' || cote || ', rang ' || rang || ')', geste, s, null, s, null, null,
       piece, vk, vch, vnum, valeur, ancienne, lignes, 'A2 v3 (passage %(passage)s, image %(image)s)', pourquoi,
       'patch_a2_vague'
  from (
    select 1 k, p.s, r.cote, r.rang, p.piece, 'RECOPIER (A2 : la part suit sa ligne)' geste, v.kind vk,
           v.app_chaine_id vch, v.app_dossier_numero vnum,
           r.hektor_user_id || ' ' || coalesce(r.nom_au_moment, '') || ' ' || r.pourcentage || ' (' || coalesce(r.origine, '-') || ')' valeur,
           'copiee depuis la chaine ' || p.s || ' ; ecrit_par d''origine : ' || coalesce(r.ecrit_par, '-') ancienne, p.lignes,
           'SA REGLE 6 (24/11) : la part recopiee sur la bonne ligne devient la part vivante ; la vague a deplace '
             || p.lignes || ' de la chaine ' || p.s || ' vers la chaine de la piece ' || p.piece pourquoi
      from a2_paires p join public.app_affaire_repartition r on r.app_chaine_id = p.s
      left join public.app_affaire_ledger v on v.app_affaire_id = p.piece
    union all
    select 2, m.s, r.cote, r.rang, m.vers_piece, 'METTRE DE COTE (regle 6 : sa ligne est partie)', v.kind,
           v.app_chaine_id, v.app_dossier_numero, null,
           r.hektor_user_id || ' ' || coalesce(r.nom_au_moment, '') || ' ' || r.pourcentage || ' (' || coalesce(r.origine, '-')
             || ') ; ecrit_par ' || coalesce(r.ecrit_par, '-'), m.lignes,
           'SA REGLE 6 : une part n''est jamais supprimee, elle est mise de cote avec son ancien numero -- ' || m.motif
      from a2_mises m join public.app_affaire_repartition r on r.app_chaine_id = m.s
      left join public.app_affaire_ledger v on v.app_affaire_id = m.vers_piece
    union all
    select 3, %(ch_comp)s, '%(c_cote)s', %(c_rang)s, %(ch_comp)s, 'COMPLETER (NRZVKH85 : la part de sortie manquait)', v.kind,
           v.app_chaine_id, v.app_dossier_numero, '%(c_uid)s ' || %(c_nom)s || ' %(c_pct)s (classeur_reconstitue)', null,
           'NRZVKH85', 'A2 v3 : la chaine de NRZVKH85 porte son entree ; le classeur porte aussi la sortie -- completee, la part existante intacte'
      from public.app_affaire_ledger v where v.app_affaire_id = %(ch_comp)s
  ) j;

-- ─── ⑤ LE GESTE : les recopies (depuis les parts vivantes que G2 vient de prouver), PUIS les mises de cote ──────────────
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select v.app_chaine_id, v.app_dossier_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment, r.pourcentage, r.origine, now(),
       '%(lot)s:' || p.lignes
  from a2_paires p
  join public.app_affaire_repartition r on r.app_chaine_id = p.s
  join public.app_affaire_ledger v on v.app_affaire_id = p.piece;
insert into public.app_affaire_repartition_mise_de_cote
  (ancien_app_chaine_id, dossier_ou_elle_vit, app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment,
   pourcentage, origine, ecrit_le, ecrit_par, mise_de_cote_par, pourquoi)
select r.app_chaine_id, v.app_chaine_id, r.app_chaine_id, r.app_dossier_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment,
       r.pourcentage, r.origine, r.ecrit_le, r.ecrit_par, 'patch_%(lot)s',
       'A2 de la vague (regle 6) : ' || m.motif
  from a2_mises m
  join public.app_affaire_repartition r on r.app_chaine_id = m.s
  left join public.app_affaire_ledger v on v.app_affaire_id = m.vers_piece;
delete from public.app_affaire_repartition r using a2_mises m where r.app_chaine_id = m.s;
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select v.app_chaine_id, v.app_dossier_id, '%(c_cote)s', %(c_rang)s, '%(c_uid)s', %(c_nom)s, %(c_pct)s, 'classeur_reconstitue', now(),
       '%(lot)s:NRZVKH85'
  from public.app_affaire_ledger v where v.app_affaire_id = %(ch_comp)s;
""")

CONTROLES = T("""
-- ─── ⑥ LES CONTROLES ───────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text; d text;
begin
  -- les membres n'ont pas bouge (A2 ne touche jamais une chaine)
  e := %(expr_membres)s;
  if e <> '%(e_membres)s' then raise exception '⛔ controle : les membres ont bouge (%)', e; end if;
  -- conservation : apres = avant + recopiees - mises de cote + completee
  select count(*) into n from public.app_affaire_repartition;
  if n <> (select count(*) from public.%(tab)s) + %(n_net)s then
    raise exception '⛔ controle : % parts au lieu de % + %(n_rec)s - %(n_mis)s + 1', n, (select count(*) from public.%(tab)s);
  end if;
  -- chaque part recopiee est sur la chaine de sa piece, telle que sur sa chaine de depart (la sauvegarde le prouve)
  select count(*) into n from a2_paires p
    join public.%(tab)s s on s.app_chaine_id = p.s
    join public.app_affaire_ledger v on v.app_affaire_id = p.piece
    join public.app_affaire_repartition r on r.app_chaine_id = v.app_chaine_id and r.cote = s.cote and r.rang = s.rang
     and r.hektor_user_id = s.hektor_user_id and r.pourcentage = s.pourcentage and r.origine is not distinct from s.origine
     and r.nom_au_moment is not distinct from s.nom_au_moment and r.ecrit_par = '%(lot)s:' || p.lignes;
  if n <> %(n_rec)s then raise exception '⛔ controle : % part(s) recopiee(s) a leur place sur %(n_rec)s', n; end if;
  -- les cibles ne portent QUE les parts recopiees, et chaque chaine somme a 100 (entree + sortie, comme le controle de ④)
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (%(cibles)s);
  if n <> %(n_rec)s then raise exception '⛔ controle : % part(s) sur les cibles au lieu de %(n_rec)s', n; end if;
  select string_agg(app_chaine_id || '/' || cote || '=' || s_, ', ') into d from (
    select app_chaine_id, 'total' cote, sum(pourcentage) s_ from public.app_affaire_repartition
     where app_chaine_id in (%(cibles)s union all select %(ch_comp)s) group by 1 having sum(pourcentage) <> 100) z;
  if d is not null then raise exception '⛔ controle : sommes differentes de 100 : %', d; end if;
  -- la regle 6 : chaque part mise de cote est ENTIERE (contre la sauvegarde), et sa chaine de depart est vide
  select count(*) into n from public.app_affaire_repartition_mise_de_cote m
    join public.%(tab)s s on s.app_chaine_id = m.ancien_app_chaine_id and s.cote = m.cote and s.rang = m.rang
     and s.hektor_user_id = m.hektor_user_id and s.pourcentage = m.pourcentage and s.origine is not distinct from m.origine
     and s.ecrit_le = m.ecrit_le and s.ecrit_par is not distinct from m.ecrit_par
     and s.nom_au_moment is not distinct from m.nom_au_moment and s.app_dossier_id is not distinct from m.app_dossier_id
   where m.mise_de_cote_par = 'patch_%(lot)s';
  if n <> %(n_mis)s then raise exception '⛔ controle : % part(s) mise(s) de cote entiere(s) sur %(n_mis)s', n; end if;
  select count(*) into n from public.app_affaire_repartition r join a2_mises m on m.s = r.app_chaine_id;
  if n <> 0 then raise exception '⛔ controle : % part(s) encore sur les chaines mises de cote', n; end if;
  -- la completee : la chaine de NRZVKH85 porte ses deux cotes
  select count(*) into n from public.app_affaire_repartition where app_chaine_id = %(ch_comp)s;
  if n <> 2 then raise exception '⛔ controle : la chaine %(ch_comp)s porte % part(s) au lieu de 2', n; end if;
  -- ✅ LES %(n_nommees)s CHAINES NOMMEES (son mot du 24/11) : elles restent a l'arrivee SANS LIGNE NI PART, et AUCUNE ne
  --    porte de vente reglee -- on n'y touche pas, et on le prouve
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (%(nommees)s);
  if n <> 0 then raise exception '⛔ controle : % part(s) sur les %(n_nommees)s chaines nommees', n; end if;
  select count(*) into n from public.app_affaire_ledger where app_chaine_id in (%(nommees)s)
     and kind = 'vente' and coalesce(vente_reglee_app, '') <> '';
  if n <> 0 then raise exception '⛔ controle : % vente(s) reglee(s) sur les %(n_nommees)s chaines nommees', n; end if;
  -- ⭐ LES ORPHELINES (l'alerte data.repartition_orpheline, 26 depuis le 21/11 : 13 dossiers du rapatriement du 13/11 que
  --    la vague fait RENAITRE, et les chaines qui disparaissent a la vague, mises de cote ci-dessus) : apres A2, AUCUNE
  --    part sur une chaine qui ne porte aucune piece (son mot du 25/11 : « ce rouge doit tomber a 0 ce soir »)
  select count(*), coalesce(string_agg(distinct r.app_chaine_id::text, ','), '') into n, d
    from public.app_affaire_repartition r
   where not exists (select 1 from public.app_affaire_ledger l where l.app_chaine_id = r.app_chaine_id);
  if n <> 0 then raise exception '⛔ controle : % part(s) orpheline(s) apres A2 (chaines %)', n, d; end if;
  -- ⭐ LA GARDE DU TEMPS 2 : plus AUCUNE vente reglee sans part a l'arrivee
  e := (%(sql_vr)s);
  if e <> '' then raise exception '⛔ controle : ventes reglees sans part apres A2 : [%]', e; end if;
  -- le journal
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s' and ligne_origine is not null;
  if n <> %(n_journal)s then raise exception '⛔ controle : % ligne(s) au journal (avec ligne d''origine) sur %(n_journal)s', n; end if;
  -- les parts qui ne sont pas du lot sont INTACTES (la sauvegarde, privee des chaines mises de cote)
  select count(*) into n from (
    (select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.%(tab)s where app_chaine_id not in (select s from a2_mises)
     except all
     select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition)
  ) z;
  if n <> 0 then raise exception '⛔ controle : % part(s) hors du lot ont change', n; end if;
  e := (select %(expr_parts)s from public.app_affaire_repartition);
  %(controle_apres)s
  raise notice '✅ A2 : %(n_rec)s recopiees (%(n_paires)s paires), %(n_mis)s mises de cote entieres (%(n_mis_ch)s chaines), 1 completee, 0 vente reglee sans part, %(n_journal)s lignes au journal ; empreinte apres %', e;
end $$;
""")

INVERSE_CORPS = T("""
-- ─── LE RETOUR ARRIERE : les parts du lot retirees, les mises de cote remises EN PLACE, le journal du lot retire ─────
do $$
declare n int;
begin
  if to_regclass('public.%(tab)s') is null then raise exception '⛔ inverse : la sauvegarde %(tab)s est absente'; end if;
  select count(*) into n from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_%(lot)s';
  if n <> %(n_mis)s then raise exception '⛔ inverse : % mise(s) de cote du lot au lieu de %(n_mis)s', n; end if;
end $$;
delete from public.app_affaire_repartition where ecrit_par like '%(lot)s:%%';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select ancien_app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
  from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_%(lot)s';
delete from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_%(lot)s';
delete from public.app_classeur_realignement_journal where lot = '%(lot)s';
do $$
declare n int;
begin
  -- la table est revenue EXACTEMENT a la sauvegarde, dans les deux sens
  select count(*) into n from (
    (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.%(tab)s
     except all
     select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition)
    union all
    (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition
     except all
     select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.%(tab)s)) z;
  if n <> 0 then raise exception '⛔ inverse : % part(s) differente(s) de la sauvegarde', n; end if;
  raise notice '✅ inverse : la repartition est revenue a la sauvegarde, la mise de cote et le journal du lot sont vides';
end $$;
""")

ENTETE = T("""-- %(base)s -- genere par %(src)s
-- A2 DE LA VAGUE DU SOIR, PAR PIECES (A2 v3 : sa regle 6, « une annulee ne porte aucune part », NRZVKH85 completee).
-- Export : passage %(passage)s, image %(image)s. Lot du journal : %(lot)s.
-- ⛔ Ce patch ne se joue qu'a l'ETAPE 7 de la vague, apres le chainage pousse et controle -- et sur SON accord.
""")
D["base"] = BASE

# ─── la liste G3 « avant A2 » : calculee depuis l'export (chaines d'arrivee avec une vente reglee et sans part) ─────
# elle n'est pas dans l'export : on la LIT a l'essai a blanc (la simulation la rend), puis on l'exige au patch reel.
VR_AVANT_FICHIER = Path(arg.export).with_suffix(".vr_avant.txt")
D["vr_avant"] = VR_AVANT_FICHIER.read_text(encoding="utf-8").strip() if VR_AVANT_FICHIER.exists() else "A_MESURER"

# ─── LA SIMULATION : les pieces qui changent de chaine, posees comme le rejeu les prevoit ────────────────────────────
SIM = sorted((int(a), int(c)) for a, c in X["simulation_chaines"].items())
D["v_sim"] = ",\n    ".join(", ".join("(%d, %d)" % x for x in SIM[i:i + 8]) for i in range(0, len(SIM), 8))
D["n_sim"] = len(SIM)

# 1) le patch reel
D["controle_apres"] = ("if e <> '%s' then raise exception '⛔ controle : empreinte apres %% au lieu de %s', e; end if;" % (
    arg.empreinte_apres, arg.empreinte_apres) if arg.empreinte_apres else
    "raise exception '⛔ le patch reel exige l''empreinte d''apres rendue par l''essai a blanc simule (--empreinte-apres)';")
reel = ENTETE % D + "\nbegin;\n" + PREAMBULE % D + GARDES % D + GESTE % D + CONTROLES % D + "\ncommit;\n"
(OUT / (BASE + ".sql")).write_text(reel, encoding="utf-8")

# 2) l'essai a blanc simule : poser les chaines du rejeu -> les gardes -> le geste -> les controles -> l'inverse -> tout est
#    revenu -> on ANNULE par une erreur voulue
D["controle_apres"] = "null;"
sim = T("""-- %(base)s_A_BLANC_SIMULE -- ⛔ N'ECRIT RIEN : la derniere instruction ANNULE toute la transaction (erreur voulue).
-- L'ETAT D'ARRIVEE SIMULE : les %(n_sim)s pieces qui changent de chaine a la vague recoivent la chaine que le rejeu prevoit
-- (le numero de chaine n'a aucun declencheur : seuls acquereurs, mandants, contacts, notaires et presence en ont un).
begin;
do $$
declare n int; e text;
begin
  e := (%(sql_vr)s);
  raise notice 'AVANT la simulation : ventes reglees sans part [%]', e;
end $$;
create temporary table a2_sim_avant on commit drop as
  select count(*) n_rep, %(expr_parts)s e_rep,
         (select count(*) from public.app_affaire_repartition_mise_de_cote) n_mdc,
         (select count(*) from public.app_classeur_realignement_journal) n_j
    from public.app_affaire_repartition;
update public.app_affaire_ledger l set app_chaine_id = v.c from (values
    %(v_sim)s) v(a, c)
 where l.app_affaire_id = v.a;
do $$
declare n int; e text;
begin
  e := (%(sql_vr)s);
  raise notice 'ARRIVEE SIMULEE : ventes reglees sans part [%]', e;
end $$;
""") % D
corps_gardes = PREAMBULE % D + GARDES % D
if D["vr_avant"] == "A_MESURER":
    # premier passage : la liste G3 n'est pas encore connue -> l'essai la REND dans son message final, sans la garder
    corps_gardes = corps_gardes.replace("if e <> 'A_MESURER' then", "if false then")
sim += corps_gardes + GESTE % D + CONTROLES % D
sim += T("""
create temporary table a2_sim_milieu on commit drop as
  select count(*) n_rep, %(expr_parts)s e_rep, (%(sql_vr)s) vr_apres,
         (select count(*) from public.app_affaire_repartition_mise_de_cote) n_mdc,
         (select count(*) from public.app_classeur_realignement_journal) n_j
    from public.app_affaire_repartition;
""") % D
sim += INVERSE_CORPS % D
sim += T("""
do $$
declare a record; m record; n_rep int; e_rep text; n_mdc int; n_j int; vr text;
begin
  select * into a from a2_sim_avant;
  select * into m from a2_sim_milieu;
  select count(*), %(expr_parts)s into n_rep, e_rep from public.app_affaire_repartition;
  select count(*) into n_mdc from public.app_affaire_repartition_mise_de_cote;
  select count(*) into n_j from public.app_classeur_realignement_journal;
  if n_rep <> a.n_rep or e_rep <> a.e_rep or n_mdc <> a.n_mdc or n_j <> a.n_j then
    raise exception '⛔ A BLANC : l''inverse n''a pas tout rendu (parts % / %, empreinte % / %, mise de cote % / %, journal % / %)',
      n_rep, a.n_rep, e_rep, a.e_rep, n_mdc, a.n_mdc, n_j, a.n_j;
  end if;
  vr := (%(sql_vr)s);
  raise exception 'A BLANC SIMULE VERT -- RIEN N''EST ECRIT (annulation voulue). Avant : % parts (%), mise de cote %, journal %. Apres A2 : % parts, empreinte apres % , ventes reglees sans part [%], mise de cote %, journal %. Apres l''inverse : % parts (%), mise de cote %, journal % = avant. Ventes reglees sans part a l''arrivee simulee, AVANT A2 : [%]',
    a.n_rep, left(a.e_rep, 8), a.n_mdc, a.n_j, m.n_rep, m.e_rep, m.vr_apres, m.n_mdc, m.n_j, n_rep, left(e_rep, 8), n_mdc, n_j, vr;
end $$;
""") % D
(OUT / (BASE + "_A_BLANC_SIMULE.sql")).write_text(sim, encoding="utf-8")

# 3) la pre-garde, LECTURE SEULE, avant le point de non-retour : G2 (les parts n'ont pas change depuis la fabrication)
pre = T("""-- %(base)s_PREGARDE -- LECTURE SEULE. A l'etape 0 de la vague, AVANT le point de non-retour : les parts que A2
-- deplacera n'ont pas change depuis la fabrication (sinon le patch refuserait APRES le chainage -- on s'arrete AVANT).
select (select %(expr_parts)s from public.app_affaire_repartition where app_chaine_id in (%(liste_lit)s)) = '%(e_parts)s' as g2_parts_inchangees,
       (select count(*) from public.app_affaire_repartition where app_chaine_id in (%(liste_lit)s)) = %(n_parts)s as g2_compte,
       (select count(*) from public.app_affaire_repartition where app_chaine_id in (%(cibles_lit)s)) = 0 as g2_cibles_vides,
       (select count(*) from public.app_classeur_realignement_journal where lot = '%(lot)s') = 0 as g0_lot_absent,
       to_regclass('public.%(tab)s') is null as g0_sauvegarde_absente;
""") % D
(OUT / (BASE + "_PREGARDE.sql")).write_text(pre, encoding="utf-8")

# 4) l'inverse reel
inv = (T("-- %(base)s_INVERSE -- le retour arriere d'A2 (begin ... commit). La sauvegarde %(tab)s reste.\n") % D
       + "begin;\n" + INVERSE_CORPS % D + "\ncommit;\n")
(OUT / (BASE + "_INVERSE.sql")).write_text(inv, encoding="utf-8")

# 5) la repetition (lecture seule, apres le geste)
rep = T("""-- %(base)s_REPETITION -- LECTURE SEULE, apres le geste.
select (select count(*) from public.app_classeur_realignement_journal where lot = '%(lot)s') as journal_attendu_%(n_journal)s,
       (select count(*) from public.app_affaire_repartition where ecrit_par like '%(lot)s:%%') as parts_du_lot_attendu_%(n_rec)s_plus_1,
       (select count(*) from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_%(lot)s') as mises_de_cote_attendu_%(n_mis)s,
       (%(sql_vr)s) as ventes_reglees_sans_part_attendu_vide,
       (select count(*) from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l
         where l.app_chaine_id = r.app_chaine_id)) as parts_orphelines_attendu_0,
       %(expr_membres_lit)s = '%(e_membres)s' as membres_comme_le_rejeu,
       (select %(expr_parts)s from public.app_affaire_repartition) as empreinte_apres;
""") % D
(OUT / (BASE + "_REPETITION.sql")).write_text(rep, encoding="utf-8")

for f in (BASE + ".sql", BASE + "_A_BLANC_SIMULE.sql", BASE + "_PREGARDE.sql", BASE + "_INVERSE.sql",
          BASE + "_REPETITION.sql"):
    p = OUT / f
    dire("-> supabase/%s (%d octets, md5 %s)" % (f, p.stat().st_size, hashlib.md5(p.read_bytes()).hexdigest()[:8]))
dire("G1 membres %s (%d pieces) ; G2 parts %s (%d) ; G3 avant A2 : %s ; empreinte apres : %s" % (
    E_MEMBRES[:8], N_MEMBRES, E_PARTS[:8], N_PARTS_TOUCHEES, D["vr_avant"], arg.empreinte_apres or "A RENDRE PAR L'ESSAI"))
