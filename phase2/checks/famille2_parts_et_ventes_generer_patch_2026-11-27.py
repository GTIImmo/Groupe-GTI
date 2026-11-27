"""LES 47 (+2), FAMILLE 2 : LES VENTES REGLEES DONT SEUL LE « PRIX » DU SHEET EST FAUTIF -- UN GESTE EN DEUX TEMPS (27/11).

SON MOT DU 27/11 : « Fini ce qui etait prevu », puis « Fais les deux » (familles 2 et 3). LE PREVU (25/11, « ④ La methode des
47 (+2) ») : « 5 de ces chaines n'ont que des parts supposees [...] Recopier d'abord leurs parts du classeur, comme A2, serait
sa decision. » -- « Fais les deux » est ce mot. SA REGLE DU 24/11 : l'origine est le VERROU (on remplace LES DEUX parts).

LA FAMILLE (mesure du 27/11, passage 82) : 7 ventes dont SEUL le Prix du Sheet est faux (« NON TROUVE » ou « 42 ») -- les
honoraires, la facture et les dates concordent. MQ6H8TVQ N'EST PAS dans ce patch : sans facture au Sheet, et PITIOT absent de
l'annuaire (le 25/11 : « MQ6H8TVQ, qui n'a pas de facture » reste a lui). Restent 6 :
  QXDW8EQA (1029), 6FQO29C8 (19133) -- leurs chaines portent deja des parts du classeur ;
  EJN79TJ1 (27714), 2U5QPKRC (17770), I3TFR2KG (24620), 91IHSGNC (4783) -- leurs chaines n'ont que deux suppositions de la
  nuit (hektor_partage_suppose), qui nomment DEJA la bonne personne : seule l'ORIGINE change (comme A07EC3DH le 24/11).

TEMPS 1, LES PARTS (4 chaines) : la part du classeur, resolue par les regles du 13/11 (nettoyer, decomposer, resoudre --
le nom au moment ecrit comme les parts du classeur deja posees), remplace les deux suppositions, MISES DE COTE entieres.
TEMPS 2, LES VENTES (6) : la case « Vente Réglée » et la case « Numéro de facture », mot pour mot comme C8, sur des cases
vides. Le juge ne lit pas ces deux colonnes (« circulaires »).
L'ESSAI A BLANC rejoue les vraies fonctions de nuit (l'absorbeur doit SAUTER les 4 chaines ; la purge ne doit rien faire),
puis l'inverse, puis le temoin inverse (sur les 4 chaines remises en supposition, l'absorbeur doit ECRIRE).
USAGE : python -X utf8 phase2/checks/famille2_parts_et_ventes_generer_patch_2026-11-27.py [--empreinte-apres MD5]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402
import rapatrier_repartition_classeur as RR  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--empreinte-apres", default="")
arg = ap.parse_args()
LOT_P, LOT_V = "parts_famille2_2026-11-27", "ventes_reglees_famille2_2026-11-27"
MDC = "patch_famille2_2026-11-27"
TAB_P, TAB_V = "app_affaire_repartition_avant_famille2_20261127", "app_affaire_ledger_avant_ventes_reglees_f2_20261127"
OUT = RACINE / "supabase"
MESURE = RACINE / "notice" / "CLASSEUR_LES_47_VALEURS_JAMAIS_POSEES_2026-11-27_PASSAGE_82.csv"
IMAGE = "2026-11-26_094931"
VENTES = ["QXDW8EQA", "6FQO29C8", "EJN79TJ1", "2U5QPKRC", "I3TFR2KG", "91IHSGNC"]
A_RECOPIER = ["EJN79TJ1", "2U5QPKRC", "I3TFR2KG", "91IHSGNC"]
EXPR = ("md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, "
        "origine, ecrit_par), ';' order by app_chaine_id, cote, rang), ''))")

# ─── 1. LA MESURE DU JOUR : chacune n'a QUE l'ecart du Prix ────────────────────────────────────────────────────────────
with MESURE.open(encoding="utf-8") as h:
    m = {r["id_unique"]: r for r in csv.DictReader(h, delimiter=";") if r["quoi"] == "VENTE_REGLEE"}
for i in VENTES:
    v = m[i]["verdict"]
    assert v.startswith("A REGARDER : montant Hektor ") and ";" not in v and " / Prix " in v, (i, v)
con = sqlite3.connect("file:%s?mode=ro" % (P.DOSSIER / "socle.sqlite").as_posix(), uri=True)
V = {i: (v, json.loads(ps) if ps else []) for i, v, ps in con.execute("select id_unique, verdict, pieces from verdict where passage=82")}
con.close()
LIGNES = sorted(((i, int(m[i]["ligne"]), int(m[i]["piece"]), m[i]["dossier"]) for i in VENTES), key=lambda x: x[1])
for i, num, piece, dossier in LIGNES:
    assert V[i][0] == "TRANCHEE" and piece in V[i][1], (i, V.get(i))

# ─── 2. LE SHEET : l'image du 82, et le Sheet du jour qui doit dire la meme chose ──────────────────────────────────────
I = P.Image(P.IMAGES / IMAGE)
D = I.D
COLS = ["Etat Actuel", "Vente Réglée", "Numéro de facture"] + ["Négociateur %d" % n for n in (1, 2, 3)] + [
    "Pourcentage %d" % n for n in (1, 2, 3)]
IMG = {i: tuple(D.case(i, c).strip() for c in COLS) for i in VENTES}
import apparier_classeur as ac  # noqa: E402

ac.load_env_file(RACINE / ".env")
entete, lignes = ac.lire_classeur()
k = [entete.index(c) for c in COLS]
du_jour = defaultdict(list)
for num, l in lignes:
    l = [("" if x is None else str(x)) for x in list(l)] + [""] * 40
    if l[37].strip() in IMG:
        du_jour[l[37].strip()].append((num, tuple(l[j].strip() for j in k)))
for i, num, piece, dossier in LIGNES:
    assert du_jour[i] == [(num, IMG[i])], (i, du_jour[i], num, IMG[i])
    assert IMG[i][0] == "Vente réglée" and IMG[i][1] and IMG[i][2], (i, IMG[i])
print("les 6 lignes : l'image du 82 = le Sheet du jour (etat, reglement, facture, negociateurs, pourcentages)")

# ─── 3. LES REGLES DU 13/11 pour les 4 chaines a recopier ─────────────────────────────────────────────────────────────
loc = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(), uri=True)
loc.row_factory = sqlite3.Row
gens = defaultdict(list)
for r in loc.execute("select hektor_user_id, nom, prenom, is_active from app_hektor_negotiator_agency_directory"):
    n_ = " ".join(sorted(RR.mots_du_nom(r["nom"])))
    p_ = " ".join(sorted(RR.mots_du_nom(r["prenom"])))
    if n_:
        gens[(n_, p_)].append(dict(r))
loc.close()
PAR_NOM = defaultdict(list)
for (n_, p_), f in gens.items():
    act = [x for x in f if x.get("is_active") in (1, "1", True, "true", "True")]
    ch_ = sorted(act or f, key=lambda x: int(str(x["hektor_user_id"])))[0]
    PAR_NOM[n_].append({"nom": n_, "prenom": p_, "hektor_user_id": str(ch_["hektor_user_id"]), "fiches": len(f)})
NOUV = {}
for i in A_RECOPIER:
    noms = list(IMG[i][3:6])
    pcts = [RR.nombre(x) for x in IMG[i][6:9]]
    parts, pq = RR.nettoyer(noms, pcts)
    assert not pq, (i, pq)
    cotes, pq = RR.decomposer(parts)
    assert not pq, (i, pq)
    out = []
    for cote, rang, brut, pct in cotes:
        qui, motif = RR.resoudre(brut, PAR_NOM, None, None)
        assert qui is not None, (i, brut, motif)
        out.append((cote, rang, str(qui["hektor_user_id"]), qui["nom_au_moment"], float(pct)))
    NOUV[i] = out

# ─── 4. SUPABASE, LECTURE SEULE : l'etat exact que les gardes exigeront ───────────────────────────────────────────────
ids = ", ".join(str(p) for _i, _n, p, _d in LIGNES)
EMP = ("md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, app_chaine_id, app_dossier_numero, "
       "coalesce(vente_reglee_app, '-'), coalesce(numero_facture_app, '-'), coalesce(date_annulation_app, '-'), "
       "coalesce(motif_annulation_app, '-'), coalesce(honoraires_entree_app::text, '-')), ';' order by app_affaire_id), '')) "
       "from public.app_affaire_ledger where app_affaire_id in (%s)" % ids)
VR_SANS_PART = ("(select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and "
                "coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null and not exists (select 1 from "
                "public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id))")
VR_SUPPOSEES = ("(select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and "
                "coalesce(l.vente_reglee_app, '') <> '' and exists (select 1 from public.app_affaire_repartition r where "
                "r.app_chaine_id = l.app_chaine_id) and not exists (select 1 from public.app_affaire_repartition r where "
                "r.app_chaine_id = l.app_chaine_id and coalesce(r.origine, '') not like 'hektor%'))")
ORPH = ("(select count(*) from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l "
        "where l.app_chaine_id = r.app_chaine_id))")
cn, cu = P.pooler()
cu.execute("select app_affaire_id, kind, app_dossier_numero, app_chaine_id, app_dossier_id, coalesce(vente_reglee_app, ''), "
           "coalesce(numero_facture_app, '') from public.app_affaire_ledger where app_affaire_id in (%s)" % ids)
etat = {r[0]: r[1:] for r in cu.fetchall()}
CH = {i: etat[p][2] for i, _n, p, _d in LIGNES}
DOS = {i: etat[p][3] for i, _n, p, _d in LIGNES}
chaines = sorted(CH.values())
cu.execute("select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage::text, origine, ecrit_par, app_dossier_id "
           "from public.app_affaire_repartition where app_chaine_id in (%s) order by 1, 2, 3" % ", ".join(map(str, chaines)))
parts = defaultdict(list)
for r in cu.fetchall():
    parts[r[0]].append(r[1:])
cu.execute("select app_chaine_id from public.app_affaire_ledger where kind = 'vente' and coalesce(vente_reglee_app, '') <> '' "
           "and app_chaine_id in (%s)" % ", ".join(map(str, chaines)))
deja = [r[0] for r in cu.fetchall()]
CH4 = ", ".join(str(CH[i]) for i in A_RECOPIER)
cu.execute("select count(*), %s from public.app_affaire_repartition" % EXPR)
n_rep, e_rep = cu.fetchone()
cu.execute("select %s from public.app_affaire_repartition where app_chaine_id not in (%s)" % (EXPR, CH4))
e_hors = cu.fetchone()[0]
cu.execute("select (select count(*) from public.app_affaire_ledger where coalesce(vente_reglee_app, '') <> ''), "
           "(select count(*) from public.app_affaire_ledger where coalesce(numero_facture_app, '') <> ''), %s, %s, %s, (select %s)"
           % (VR_SANS_PART, VR_SUPPOSEES, ORPH, EMP))
n_vr, n_nf, vr_sans_part, vr_sup, orph, e_v = cu.fetchone()
cu.execute("select count(*) from public.app_classeur_realignement_journal where lot in (%s, %s)", (LOT_P, LOT_V))
au_journal = cu.fetchone()[0]
cu.execute("select to_regclass(%s) is not null or to_regclass(%s) is not null", ("public." + TAB_P, "public." + TAB_V))
tab_existe = cu.fetchone()[0]
cu.execute("select count(*) from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = %s", (MDC,))
mdc_deja = cu.fetchone()[0]
cn.rollback()
cn.close()
for i, num, piece, dossier in LIGNES:
    kind, numero, ch, dos, vr, nf = etat[piece]
    assert (kind, numero, vr, nf) == ("vente", dossier, "", ""), (i, etat[piece])
    p = parts[ch]
    if i in A_RECOPIER:
        assert len(p) == 2 and all(x[5] == "hektor_partage_suppose" and x[6] == "conversion" and x[4] == "50.000"
                                   and x[7] == dos for x in p) and [x[:2] for x in p] == [("entree", 1), ("sortie", 1)], (i, p)
        assert [x[2] for x in p] == [u for _c, _r, u, _n, _p in NOUV[i]], (i, p, NOUV[i])   # la meme personne : l'origine seule
    else:
        assert p and all(not str(x[5] or "").startswith("hektor") for x in p), (i, p)
assert not deja and au_journal == 0 and not tab_existe and mdc_deja == 0, (deja, au_journal, tab_existe, mdc_deja)
assert vr_sans_part == 0 and orph == 0, (vr_sans_part, orph)
for i, num, piece, dossier in LIGNES:
    print("  %-9s ligne %-5d vente %-6d %-11s chaine %-6d reglee %r ; facture %r%s" % (
        i, num, piece, dossier, CH[i], IMG[i][1], IMG[i][2],
        ("\n            parts : %s -> %s" % ([(x[0], x[2], x[3], x[5]) for x in parts[CH[i]]],
                                             [(c, u, n_, p_) for c, _r, u, n_, p_ in NOUV[i]])) if i in A_RECOPIER else ""))
print("registre des parts : %d, %s ; hors des 4 chaines %s ; ventes reglees %d, factures %d ; sans part %d ; sur supposition %d ; "
      "6 lignes %s" % (n_rep, e_rep, e_hors, n_vr, n_nf, vr_sans_part, vr_sup, e_v))


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


POURQ_P = ("SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : sa vente sera posee reglee ; "
           "le classeur fait foi, une supposition de Hektor n'est pas une donnee ; l'origine est le verrou (24/11)")
POURQ_V = ("SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : une vraie vente reglee "
           "dont seul le Prix du Sheet est faux (honoraires, facture et dates concordent), jamais posee : le gel ne la reliait pas")
jp, nv, jv = [], [], []
n = 0
for i in A_RECOPIER:
    num = [x[1] for x in LIGNES if x[0] == i][0]
    anc = {x[0]: "%s %s %s (%s)" % (x[2], x[3], x[4].rstrip("0").rstrip("."), x[5]) for x in parts[CH[i]]}
    for c, r, u, nm, p in NOUV[i]:
        n += 1
        jp.append("(%d, %s, %d, %d, '%s', %d, %s, %s, %s, %s, %s)" % (n, q(i), num, CH[i], c, r, q(u), q(nm), q("%g" % p),
                                                                    q(anc[c]), q(POURQ_P)))
        nv.append("(%d, '%s', %d, %s, %s, %s, %s)" % (CH[i], c, r, q(u), q(nm), q("%g" % p), q("classeur:" + i)))
n = 0
for i, num, piece, dossier in LIGNES:
    for col, v in (("vente_reglee_app", IMG[i][1]), ("numero_facture_app", IMG[i][2])):
        n += 1
        jv.append("(%d, %s, %d, %d, %s, %s, %s)" % (n, q(i), num, piece, q(col), q(v), q(POURQ_V)))
D_ = {"lot_p": LOT_P, "lot_v": LOT_V, "mdc": MDC, "tab_p": TAB_P, "tab_v": TAB_V, "ch4": CH4, "ids": ids, "expr": EXPR,
      "emp": EMP, "e_rep": e_rep, "e_hors": e_hors, "n_rep": n_rep, "e_v": e_v, "n_vr": n_vr, "n_nf": n_nf,
      "vr_sans_part": VR_SANS_PART, "vr_sup": VR_SUPPOSEES, "n_sup": vr_sup, "orph": ORPH, "jp": ",\n    ".join(jp),
      "nv": ",\n    ".join(nv), "jv": ",\n    ".join(jv), "image": IMAGE, "njp": len(jp), "njv": len(jv)}
TOUT = "md5((select %s from public.app_affaire_repartition) || (select %s))" % (EXPR, EMP)
D_["tout"] = TOUT

CORPS = """
-- ─── ① LES GARDES : les 4 chaines et leurs deux suppositions, les 6 ventes et leurs cases vides, tels que lus ──────────
do $$
declare n int; e text;
begin
  if to_regclass('public.%(tab_p)s') is not null or to_regclass('public.%(tab_v)s') is not null then
    raise exception '⛔ garde : une sauvegarde existe deja -- ce patch ne se rejoue pas'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot in ('%(lot_p)s', '%(lot_v)s');
  if n <> 0 then raise exception '⛔ garde : %% ligne(s) des lots deja au journal', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (%(ch4)s);
  if n <> 8 then raise exception '⛔ garde : les 4 chaines portent %% part(s) au lieu de 8', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (%(ch4)s) and rang = 1
     and cote in ('entree', 'sortie') and pourcentage = 50 and origine = 'hektor_partage_suppose' and ecrit_par = 'conversion';
  if n <> 8 then raise exception '⛔ garde : %% supposition(s) telles que mesurees sur 8', n; end if;
  e := (select %(expr)s from public.app_affaire_repartition);
  if e <> '%(e_rep)s' then raise exception '⛔ garde : le registre des parts a bouge depuis la mesure (%%)', e; end if;
  select count(*) into n from public.app_affaire_ledger where app_affaire_id in (%(ids)s) and kind = 'vente'
     and coalesce(vente_reglee_app, '') = '' and coalesce(numero_facture_app, '') = '';
  if n <> 6 then raise exception '⛔ garde : %% vente(s) sur 6 ont leurs deux cases vides', n; end if;
  e := (select %(emp)s);
  if e <> '%(e_v)s' then raise exception '⛔ garde : les 6 ventes ont change depuis la fabrication (%%)', e; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(vente_reglee_app, '') <> '') <> %(n_vr)s then
    raise exception '⛔ garde : le nombre de ventes reglees a change depuis la fabrication'; end if;
  raise notice '✅ gardes : 4 chaines a deux suppositions, 6 ventes aux cases vides, le registre tel que mesure';
end $$;

-- ─── ② LES SAUVEGARDES DATEES, AVEC cle primaire et RLS ─────────────────────────────────────────────────────────────────
create table public.%(tab_p)s (like public.app_affaire_repartition including defaults including constraints including indexes);
insert into public.%(tab_p)s select * from public.app_affaire_repartition where app_chaine_id in (%(ch4)s);
revoke all on public.%(tab_p)s from public, anon, authenticated;
alter table public.%(tab_p)s enable row level security;
create table public.%(tab_v)s as select * from public.app_affaire_ledger where app_affaire_id in (%(ids)s);
alter table public.%(tab_v)s add primary key (app_affaire_id);
revoke all on public.%(tab_v)s from public, anon, authenticated;
alter table public.%(tab_v)s enable row level security;

-- ─── ③ TEMPS 1, LES PARTS : le journal, la regle 6 (mises de cote entieres), la part du classeur ───────────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select '%(lot_p)s', v.n, 'repartition', 'app_affaire_repartition (' || v.cote || ', rang ' || v.rang || ')',
       'REMPLACER (le classeur fait foi ; l''ancienne mise de cote)', v.ch, d.kind, d.app_chaine_id, d.app_dossier_numero,
       d.app_dossier_uuid, v.ch, d.kind, d.app_chaine_id, d.app_dossier_numero, v.uid || ' ' || v.nom || ' ' || v.pct,
       v.ancienne, v.ligne, v.num, 'Sheet (Negociateurs / Pourcentages, regles du 13/11), image %(image)s = le Sheet du 27/11',
       v.pourquoi, '%(mdc)s'
  from (values
    %(jp)s
  ) v(n, ligne, num, ch, cote, rang, uid, nom, pct, ancienne, pourquoi)
  left join public.app_affaire_ledger d on d.app_affaire_id = v.ch;
insert into public.app_affaire_repartition_mise_de_cote
  (ancien_app_chaine_id, dossier_ou_elle_vit, app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment,
   pourcentage, origine, ecrit_le, ecrit_par, mise_de_cote_par, pourquoi)
select r.app_chaine_id, r.app_chaine_id, r.app_chaine_id, r.app_dossier_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment,
       r.pourcentage, r.origine, r.ecrit_le, r.ecrit_par, '%(mdc)s',
       j.pourquoi || ' -- remplacee par ' || j.valeur || ' (ligne ' || j.ligne_origine || ', n° ' || j.ligne_origine_num || ')'
  from public.app_affaire_repartition r
  join public.app_classeur_realignement_journal j
    on j.lot = '%(lot_p)s' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')';
delete from public.app_affaire_repartition r using public.app_classeur_realignement_journal j
 where j.lot = '%(lot_p)s' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select m.app_chaine_id, m.app_dossier_id, m.cote, m.rang, v.uid, v.nom, v.pct::numeric, 'classeur_reconstitue', now(), v.par
  from (values
    %(nv)s
  ) v(ch, cote, rang, uid, nom, pct, par)
  join public.app_affaire_repartition_mise_de_cote m
    on m.mise_de_cote_par = '%(mdc)s' and m.app_chaine_id = v.ch and m.cote = v.cote and m.rang = v.rang;

-- ─── ④ TEMPS 2, LES VENTES : le journal, puis seulement des cases VIDES ────────────────────────────────────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select '%(lot_v)s', v.n, 'vente_reglee_facture', v.colonne, 'POSER (case vide)', v.piece, d.kind, d.app_chaine_id,
       d.app_dossier_numero, d.app_dossier_uuid, v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero, v.valeur, 'VIDE',
       v.ligne, v.num, 'Sheet, image %(image)s (passage 82) = le Sheet du 27/11, mot pour mot comme C8 le 16/11', v.pourquoi,
       '%(mdc)s'
  from (values
    %(jv)s
  ) v(n, ligne, num, piece, colonne, valeur, pourquoi)
  join public.app_affaire_ledger d on d.app_affaire_id = v.piece;
update public.app_affaire_ledger l set vente_reglee_app = j.valeur
  from public.app_classeur_realignement_journal j
 where j.lot = '%(lot_v)s' and j.colonne = 'vente_reglee_app' and l.app_affaire_id = j.de_app_affaire_id
   and coalesce(l.vente_reglee_app, '') = '';
update public.app_affaire_ledger l set numero_facture_app = j.valeur
  from public.app_classeur_realignement_journal j
 where j.lot = '%(lot_v)s' and j.colonne = 'numero_facture_app' and l.app_affaire_id = j.de_app_affaire_id
   and coalesce(l.numero_facture_app, '') = '';

-- ─── ⑤ LES CONTROLES ───────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  -- temps 1 : chaque chaine porte EXACTEMENT la part du classeur, plus aucune part hektor, la somme a 100
  select count(*) into n from public.app_affaire_repartition r join (values
    %(nv)s
  ) v(ch, cote, rang, uid, nom, pct, par) on r.app_chaine_id = v.ch and r.cote = v.cote and r.rang = v.rang
   where r.hektor_user_id = v.uid and r.nom_au_moment = v.nom and r.pourcentage = v.pct::numeric
     and r.origine = 'classeur_reconstitue' and r.ecrit_par = v.par;
  if n <> %(njp)s or (select count(*) from public.app_affaire_repartition where app_chaine_id in (%(ch4)s)) <> %(njp)s then
    raise exception '⛔ controle : les 4 chaines ne portent pas exactement la part du classeur (%% sur %(njp)s)', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (%(ch4)s) and coalesce(origine, '') like 'hektor%%';
  if n <> 0 then raise exception '⛔ controle : %% part(s) hektor encore sur les 4 chaines', n; end if;
  select count(*) into n from (select app_chaine_id from public.app_affaire_repartition where app_chaine_id in (%(ch4)s)
                                group by 1 having sum(pourcentage) <> 100) x;
  if n <> 0 then raise exception '⛔ controle : %% chaine(s) dont la somme n''est pas 100', n; end if;
  e := (select %(expr)s from public.app_affaire_repartition where app_chaine_id not in (%(ch4)s));
  if e <> '%(e_hors)s' then raise exception '⛔ controle : une part HORS des 4 chaines a bouge (%%)', e; end if;
  if (select count(*) from public.app_affaire_repartition) <> %(n_rep)s then raise exception '⛔ controle : le nombre de parts a change'; end if;
  select count(*) into n from public.app_affaire_repartition_mise_de_cote m join public.%(tab_p)s s
    on s.app_chaine_id = m.ancien_app_chaine_id and s.cote = m.cote and s.rang = m.rang and s.hektor_user_id = m.hektor_user_id
   and s.pourcentage = m.pourcentage and s.origine is not distinct from m.origine and s.ecrit_le = m.ecrit_le
   and s.ecrit_par is not distinct from m.ecrit_par and s.nom_au_moment is not distinct from m.nom_au_moment
   and s.app_dossier_id is not distinct from m.app_dossier_id
   where m.mise_de_cote_par = '%(mdc)s';
  if n <> 8 or (select count(*) from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = '%(mdc)s') <> 8 then
    raise exception '⛔ controle : %% supposition(s) mise(s) de cote entiere(s) sur 8', n; end if;
  -- temps 2 : les 12 cases, rien d'autre
  select count(*) into n from public.app_classeur_realignement_journal j join public.app_affaire_ledger l on l.app_affaire_id = j.de_app_affaire_id
   where j.lot = '%(lot_v)s' and j.ligne_origine is not null
     and ((j.colonne = 'vente_reglee_app' and l.vente_reglee_app = j.valeur) or (j.colonne = 'numero_facture_app' and l.numero_facture_app = j.valeur));
  if n <> %(njv)s then raise exception '⛔ controle : %% case(s) posee(s) sur %(njv)s', n; end if;
  select count(*) into n from public.app_affaire_ledger l join public.%(tab_v)s s using (app_affaire_id)
   where (l.kind, l.state, l.app_chaine_id, l.app_dossier_numero, l.date_annulation_app, l.motif_annulation_app,
          l.honoraires_entree_app, l.montant, l.honoraires_entree)
         is distinct from (s.kind, s.state, s.app_chaine_id, s.app_dossier_numero, s.date_annulation_app, s.motif_annulation_app,
                           s.honoraires_entree_app, s.montant, s.honoraires_entree);
  if n <> 0 then raise exception '⛔ controle : %% vente(s) ont bouge hors de leurs deux cases', n; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(vente_reglee_app, '') <> '') <> %(n_vr)s + 6 then
    raise exception '⛔ controle : le nombre de ventes reglees n''est pas %(n_vr)s + 6'; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(numero_facture_app, '') <> '') <> %(n_nf)s + 6 then
    raise exception '⛔ controle : le nombre de factures n''est pas %(n_nf)s + 6'; end if;
  if %(vr_sans_part)s <> 0 then raise exception '⛔ controle : une vente reglee sans part'; end if;
  if %(vr_sup)s <> %(n_sup)s then raise exception '⛔ controle : une vente reglee de plus sur des parts supposees seulement'; end if;
  if %(orph)s <> 0 then raise exception '⛔ controle : des parts orphelines'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot in ('%(lot_p)s', '%(lot_v)s');
  if n <> %(njp)s + %(njv)s then raise exception '⛔ controle : %% ligne(s) au journal sur %(njp)s + %(njv)s', n; end if;
  e := %(tout)s;
  %(apres)s
  raise notice '✅ famille 2 : 4 chaines a la part du classeur (8 suppositions mises de cote), 6 ventes reglees et leurs factures ; empreinte apres %%', e;
end $$;
"""
INVERSE = """
-- ─── L'INVERSE : temps 2 puis temps 1 -- les 12 cases remises, les parts du classeur retirees, les suppositions remises ──
update public.app_affaire_ledger l set vente_reglee_app = s.vente_reglee_app
  from public.%(tab_v)s s, public.app_classeur_realignement_journal j
 where s.app_affaire_id = l.app_affaire_id and j.lot = '%(lot_v)s' and j.colonne = 'vente_reglee_app'
   and j.de_app_affaire_id = l.app_affaire_id and l.vente_reglee_app = j.valeur;
update public.app_affaire_ledger l set numero_facture_app = s.numero_facture_app
  from public.%(tab_v)s s, public.app_classeur_realignement_journal j
 where s.app_affaire_id = l.app_affaire_id and j.lot = '%(lot_v)s' and j.colonne = 'numero_facture_app'
   and j.de_app_affaire_id = l.app_affaire_id and l.numero_facture_app = j.valeur;
delete from public.app_affaire_repartition where app_chaine_id in (%(ch4)s) and origine = 'classeur_reconstitue' and ecrit_par like 'classeur:%%';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select ancien_app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
  from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = '%(mdc)s';
delete from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = '%(mdc)s';
delete from public.app_classeur_realignement_journal where lot in ('%(lot_p)s', '%(lot_v)s');
do $$
begin
  -- l'inverse ne juge que SA part (lecon 31) : les 12 cases et les 4 chaines contre leurs sauvegardes
  if (select count(*) from public.app_affaire_ledger l join public.%(tab_v)s s using (app_affaire_id)
       where (l.vente_reglee_app, l.numero_facture_app) is distinct from (s.vente_reglee_app, s.numero_facture_app)) <> 0 then
    raise exception '⛔ inverse : les 6 ventes ne sont pas revenues a la sauvegarde'; end if;
  if (select count(*) from (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
        ecrit_le, ecrit_par from public.app_affaire_repartition where app_chaine_id in (%(ch4)s)
      except all select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le,
        ecrit_par from public.%(tab_p)s) z) <> 0
     or (select count(*) from (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
        ecrit_le, ecrit_par from public.%(tab_p)s
      except all select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le,
        ecrit_par from public.app_affaire_repartition where app_chaine_id in (%(ch4)s)) z) <> 0 then
    raise exception '⛔ inverse : les 4 chaines ne sont pas revenues a la sauvegarde'; end if;
  raise notice '✅ inverse : les 6 ventes et les 4 chaines revenues a leurs sauvegardes, la mise de cote et le journal des lots vides';
end $$;
"""
LIGNES_NUIT = ("(select jsonb_agg(jsonb_build_object('app_chaine_id', app_chaine_id, 'app_dossier_id', app_dossier_id, "
               "'cote', cote, 'rang', rang, 'hektor_user_id', hektor_user_id, 'nom_au_moment', nom_au_moment, "
               "'pourcentage', pourcentage, 'origine', origine)) from public.%s)" % TAB_P)
A_BLANC_NUIT = """
-- ─── L'EPREUVE DE LA NUIT : LES VRAIES FONCTIONS, avec les lignes memes que la nuit a ecrites sur les 4 chaines ────────
create temporary table f_milieu on commit drop as select (select count(*) from public.app_affaire_repartition) n,
  (select %(expr)s from public.app_affaire_repartition) e, %(tout)s t,
  (select string_agg(app_chaine_id || ' ' || cote || ' ' || hektor_user_id || ' ' || origine, ' + ' order by app_chaine_id, cote) from public.app_affaire_repartition where app_chaine_id in (%(ch4)s)) p,
  (select count(*) from public.app_affaire_ledger where coalesce(vente_reglee_app, '') <> '') nvr;
create temporary table f_absorbeur on commit drop as select public.app_repartition_absorber(%(lignes_nuit)s) rep;
create temporary table f_purge on commit drop as select public.app_repartition_purger_orphelines() rep;
do $$
declare m record; a jsonb; p jsonb;
begin
  select * into m from f_milieu; select rep into a from f_absorbeur; select rep into p from f_purge;
  if (a->>'proteges_app')::int <> 4 or (a->>'dossiers_ecrits')::int <> 0 then
    raise exception '⛔ A BLANC : l''absorbeur n''a pas saute les 4 chaines : %%', a; end if;
  if (select %(expr)s from public.app_affaire_repartition) <> m.e then
    raise exception '⛔ A BLANC : la nuit rejouee a touche le registre des parts (purge %%)', p; end if;
end $$;
"""
TEMOIN_INVERSE = """
-- ─── LE TEMOIN INVERSE : sur les 4 chaines remises en supposition, l'absorbeur doit ECRIRE ─────────────────────────────
create temporary table f_inverse_nuit on commit drop as select public.app_repartition_absorber(%(lignes_nuit)s) rep;
do $$
declare m record; t jsonb; ab jsonb; pu jsonb;
begin
  select * into m from f_milieu; select rep into t from f_inverse_nuit; select rep into ab from f_absorbeur; select rep into pu from f_purge;
  if (t->>'dossiers_ecrits')::int <> 4 or (t->>'proteges_app')::int <> 0 then
    raise exception '⛔ A BLANC : le temoin inverse ne mord pas : %%', t; end if;
  if (select %(expr)s from public.app_affaire_repartition) <> '%(e_rep)s' then
    raise exception '⛔ A BLANC : apres le temoin inverse, le registre n''est plus celui d''avant'; end if;
  if (select %(emp)s) <> '%(e_v)s' then raise exception '⛔ A BLANC : apres l''inverse, les 6 ventes ne sont plus celles d''avant'; end if;
  raise exception 'A BLANC FAMILLE 2 VERT -- RIEN N''EST ECRIT. Apres le geste : %%, %%%% ventes reglees, empreinte apres %%. La nuit rejouee : absorbeur %%, purge %%. Apres l''inverse : = avant. Temoin inverse : %%.',
    m.p, m.nvr, m.t, ab, pu, t;
end $$;
""".replace("%%%%", "%%")
D_["lignes_nuit"] = LIGNES_NUIT
reel = ("if e <> '%s' then raise exception '⛔ controle : empreinte apres %% au lieu de %s', e; end if;" % (
    arg.empreinte_apres, arg.empreinte_apres) if arg.empreinte_apres else
    "raise exception '⛔ le patch reel exige l''empreinte d''apres rendue par l''essai a blanc (--empreinte-apres)';")
ent = "-- %s -- genere par phase2/checks/famille2_parts_et_ventes_generer_patch_2026-11-27.py (son mot du 27/11)\n"
DETAIL = ("(select string_agg(app_affaire_id || '=' || coalesce(vente_reglee_app, '-') || ' / ' || coalesce(numero_facture_app, "
          "'-'), ' ; ' order by app_affaire_id) from public.app_affaire_ledger where app_affaire_id in (%s))" % ids)
F = {
    "patch_famille2_parts_et_ventes_2026-11-27.sql": ent % "patch_famille2_parts_et_ventes_2026-11-27"
    + "-- Retour arriere : ..._INVERSE.sql . Controle : ..._REPETITION.sql\n\nbegin;\n" + CORPS % dict(D_, apres=reel)
    + "\ncommit;\n",
    "patch_famille2_parts_et_ventes_2026-11-27_A_BLANC.sql": ent % "A BLANC -- ⛔ aucun commit, une erreur VOULUE annule tout"
    + "\nbegin;\n" + CORPS % dict(D_, apres="null;") + A_BLANC_NUIT % D_ + INVERSE % D_ + TEMOIN_INVERSE % D_,
    "patch_famille2_parts_et_ventes_2026-11-27_INVERSE.sql": ent % "INVERSE" + "\nbegin;\n" + INVERSE % D_ + "\ncommit;\n",
    "patch_famille2_parts_et_ventes_2026-11-27_REPETITION.sql": ent % "REPETITION (lecture seule)" + (
        "select %s as les_6_ventes,\n"
        "  (select string_agg(app_chaine_id || ' ' || cote || ' ' || hektor_user_id || ' ' || nom_au_moment || ' ' || pourcentage "
        "|| ' ' || origine, ' + ' order by app_chaine_id, cote) from public.app_affaire_repartition where app_chaine_id in (%s)) "
        "as les_4_chaines,\n"
        "  (select count(*) from public.app_affaire_repartition where app_chaine_id in (%s) and coalesce(origine, '') like "
        "'hektor%%') as parts_hektor_attendu_0,\n"
        "  (select count(*) from public.app_classeur_realignement_journal where lot in ('%s', '%s')) as journal_attendu_%d,\n"
        "  (select count(*) from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = '%s') as mise_de_cote_attendu_8,\n"
        "  %s as ventes_reglees_sans_part_attendu_0,\n  %s as reglees_sur_supposition_seule_attendu_%d,\n"
        "  %s as orphelines_attendu_0,\n  %s as empreinte_apres;\n" % (
            DETAIL, CH4, CH4, LOT_P, LOT_V, len(jp) + len(jv), MDC, VR_SANS_PART, VR_SUPPOSEES, vr_sup, ORPH, TOUT)
    ).replace("%%", "%"),
}
for nom, txt in F.items():
    p_ = OUT / nom
    p_.write_bytes(txt.encode("utf-8"))
    print("-> supabase/%s (%d octets, md5 %s)" % (nom, p_.stat().st_size, hashlib.md5(p_.read_bytes()).hexdigest()[:8]))
print("avant : parts %d / %s ; 6 ventes %s ; ventes reglees %d, factures %d" % (n_rep, e_rep, e_v, n_vr, n_nf))
