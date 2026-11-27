"""LE PARTAGE DE 9Q0FHAKK SUR LA CHAINE 3647 -- LE PATCH, SON ESSAI A BLANC, SON INVERSE, SA REPETITION (son ordre du 27/11).

SON ORDRE DU 27/11 : « 3. puis le partage DECHAUD 50 / GENTES 50 sur la chaine 3647. » -- puis « Oui » a la preparation a blanc.
SA DECISION DU 24/11 : le classeur fait foi ; une supposition de Hektor n'est pas une donnee. SA REGLE DU 24/11 : « l'origine
n'est pas une etiquette, c'est le VERROU » -- on remplace LES DEUX parts hektor de la chaine, sinon la nuit les reecrit.

LE CONSTAT (mesure du 27/11, lecture seule) : la chaine 3647 (compromis 3647, offre 3648, vente 3650 ; D2024-0511, 42dd4d66)
porte GENTES 50 en entree et 50 en sortie, en hektor_partage_suppose, ecrites par la conversion de nuit. La ligne 286 du
Sheet (9Q0FHAKK, colonne A = 42dd4d66 depuis la vague2a de 10:09) dit DECHAUD 50 / GENTES 50. La chaine 3646 (427UDDSF)
porte ses propres parts du classeur (GENTES 50/50, rapatriement du 13/11) : elle ne bouge pas.

LA LECTURE (rien n'est tape a la main) : le Sheet en direct (un GET) ; la ligne de 9Q0FHAKK nettoyee, decomposee et resolue
par les MEMES fonctions que le rapatriement du 13/11 (rapatrier_repartition_classeur : nettoyer, decomposer, resoudre) ; le
verdict du protocole (passage 82) dit que ses pieces sont 3647, 3648, 3650 ; les parts lues chez Supabase par le pooler, et
EXIGEES telles quelles par les gardes.

LE GESTE (une seule chaine) :
  G0 ne se rejoue pas ; G1 3647 porte EXACTEMENT 3647, 3648, 3650, toutes sur D2024-0511 ; G2 3647 porte EXACTEMENT les deux
  suppositions mesurees ; G3 3646 inchangee (empreinte) ; G4 le registre des parts inchange depuis la mesure (empreinte).
  -> la sauvegarde datee de 3647, AVEC sa cle primaire et la RLS ; le journal (lot parts_3647_2026-11-27, ligne d'origine
  9Q0FHAKK, n° 286) ; les deux suppositions MISES DE COTE entieres (regle 6) ; les deux parts du classeur posees
  (classeur_reconstitue, « classeur:9Q0FHAKK »).
  CONTROLES : 3647 = exactement ces deux parts, somme 100 ; SON TEMOIN : plus aucune part hektor sur 3647 ; 3646 et toutes les
  parts hors de 3647 inchangees ; le meme nombre de parts ; les deux suppositions dans la mise de cote, ENTIERES ; 2 lignes au
  journal ; 0 orpheline ; 0 vente reglee sans part ; l'empreinte d'apres (exigee au patch reel : elle sort de l'essai a blanc).
L'ESSAI A BLANC rejoue LES VRAIES FONCTIONS DE NUIT dans la transaction annulee : l'absorbeur, avec les lignes memes que la nuit
  a ecrites sur 3647, doit la SAUTER (proteges_app 1) ; la purge des orphelines ne doit pas y toucher ; puis l'inverse rend
  l'etat d'avant ; puis le TEMOIN INVERSE : sur la chaine remise en supposition, l'absorbeur doit ECRIRE (sinon l'epreuve ne
  prouvait rien). Une erreur VOULUE annule tout.
USAGE : python -X utf8 phase2/checks/parts_3647_generer_patch_2026-11-27.py [--empreinte-apres MD5]
"""
from __future__ import annotations

import argparse
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

LIGNE, NUM, CH, VOISINE = "9Q0FHAKK", 286, 3647, 3646
UUID, NUMERO, MEMBRES = "42dd4d66-eb07-47b6-85d6-8db1e7000090", "D2024-0511", "3647,3648,3650"
LOT, TAB, MDC = "parts_3647_2026-11-27", "app_affaire_repartition_avant_parts3647_20261127", "patch_parts_3647_2026-11-27"
ECRIT_PAR = "classeur:" + LIGNE
OUT = RACINE / "supabase"
EXPR = ("md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, "
        "origine, ecrit_par), ';' order by app_chaine_id, cote, rang), ''))")
VR = ("(select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and "
      "coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null and not exists (select 1 from "
      "public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id))")
ORPH = ("(select count(*) from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l "
        "where l.app_chaine_id = r.app_chaine_id))")


def q(s):
    return "null" if s is None else "'" + str(s).replace("'", "''") + "'"


# ─── 1. LE SHEET EN DIRECT (un GET), la ligne de 9Q0FHAKK ──────────────────────────────────────────────────────────────
import apparier_classeur as ac  # noqa: E402

ac.load_env_file(RACINE / ".env")
entete, lignes = ac.lire_classeur()
idx = {h.strip(): i for i, h in enumerate(entete)}
trouvees = []
for num, l in lignes:
    l = [("" if x is None else str(x)) for x in list(l)] + [""] * 40
    if l[37].strip() == LIGNE:
        trouvees.append((num, l))
assert len(trouvees) == 1, "9Q0FHAKK trouvee %d fois au Sheet" % len(trouvees)
num, l = trouvees[0]


def case(nom):
    i = idx.get(nom)
    return l[i].strip() if i is not None else ""


noms = [case("Négociateur %d" % i) for i in (1, 2, 3)]
pcts = [RR.nombre(case("Pourcentage %d" % i)) for i in (1, 2, 3)]
print("Sheet : %s ligne %s ; colonne A %s ; Etat %s ; negociateurs %s ; pourcentages %s" % (
    LIGNE, num, l[0].strip(), case("Etat Actuel"), noms, pcts))
assert num == NUM, "9Q0FHAKK est a la ligne %s, pas %d" % (num, NUM)
assert l[0].strip() == UUID, "la colonne A de 9Q0FHAKK dit %r, pas %s" % (l[0].strip(), UUID)

# ─── 2. LES REGLES DU 13/11 : nettoyer, decomposer, resoudre (le nom au moment, comme le rapatriement) ────────────────
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
parts, pq = RR.nettoyer(noms, pcts)
assert not pq, "nettoyage refuse : %s" % pq
cotes, pq = RR.decomposer(parts)
assert not pq, "decomposition refusee : %s" % pq
NOUVELLES = []
for cote, rang, brut, pct in cotes:
    qui, motif = RR.resoudre(brut, PAR_NOM, None, None)
    assert qui is not None, (brut, motif)
    NOUVELLES.append((cote, rang, str(qui["hektor_user_id"]), qui["nom_au_moment"], pct, brut))
print("les parts du classeur (regles du 13/11) : %s" % [(c, r, u, n, p) for c, r, u, n, p, _ in NOUVELLES])
assert [(c, r, u, n, float(p)) for c, r, u, n, p, _ in NOUVELLES] == [
    ("entree", 1, "31", "SIMON DECHAUD", 50.0), ("sortie", 1, "32", "CHRISTELE GENTES", 50.0)], \
    "le Sheet ne dit plus DECHAUD 50 / GENTES 50 : %s" % NOUVELLES

# ─── 3. LE VERDICT DU PROTOCOLE (passage 82) : les pieces de la ligne ─────────────────────────────────────────────────
con = sqlite3.connect("file:%s?mode=ro" % (P.DOSSIER / "socle.sqlite").as_posix(), uri=True)
v = con.execute("select verdict, etiquette, pieces from verdict where passage=82 and id_unique=?", (LIGNE,)).fetchone()
con.close()
print("protocole, passage 82 : %s" % (v,))
assert v is not None and v[0] == "TRANCHEE", v
assert sorted(json.loads(v[2])) == [3647, 3648, 3650], v

# ─── 4. SUPABASE, LECTURE SEULE : l'etat exact que les gardes exigeront ───────────────────────────────────────────────
cn, cu = P.pooler()
cu.execute("select string_agg(app_affaire_id::text, ',' order by app_affaire_id), "
           "count(*) filter (where app_dossier_uuid::text = %s and app_dossier_numero = %s), min(app_dossier_id), "
           "max(app_dossier_id) from public.app_affaire_ledger where app_chaine_id = %s", (UUID, NUMERO, CH))
membres, sur_le_dossier, dmin, dmax = cu.fetchone()
cu.execute("select cote, rang, hektor_user_id, nom_au_moment, pourcentage::text, origine, ecrit_par, app_dossier_id "
           "from public.app_affaire_repartition where app_chaine_id = %s order by cote, rang", (CH,))
avant = cu.fetchall()
cu.execute("select cote, rang, hektor_user_id, nom_au_moment, pourcentage::text, origine, ecrit_par "
           "from public.app_affaire_repartition where app_chaine_id = %s order by cote, rang", (VOISINE,))
voisine = cu.fetchall()
cu.execute("select %s from public.app_affaire_repartition where app_chaine_id = %%s" % EXPR, (VOISINE,))
e_voisine = cu.fetchone()[0]
cu.execute("select count(*), %s from public.app_affaire_repartition" % EXPR)
n_rep, e_rep = cu.fetchone()
cu.execute("select %s from public.app_affaire_repartition where app_chaine_id <> %%s" % EXPR, (CH,))
e_hors = cu.fetchone()[0]
cu.execute("select %s, %s" % (ORPH, VR))
orph, vr = cu.fetchone()
cu.execute("select count(*) from public.app_classeur_realignement_journal where lot = %s", (LOT,))
deja = cu.fetchone()[0]
cu.execute("select to_regclass(%s) is not null", ("public." + TAB,))
tab_existe = cu.fetchone()[0]
cn.rollback()
cn.close()
print("3647 : membres %s (sur %s : %s), dossier %s..%s ; parts %s" % (membres, NUMERO, sur_le_dossier, dmin, dmax, avant))
print("3646 : parts %s ; empreinte %s" % (voisine, e_voisine))
print("registre des parts : %d parts, empreinte %s ; hors 3647 %s ; orphelines %d ; ventes reglees sans part %d" % (
    n_rep, e_rep, e_hors, orph, vr))
assert membres == MEMBRES and sur_le_dossier == 3 and dmin == dmax, (membres, sur_le_dossier, dmin, dmax)
DOSSIER_ID = dmin
assert [a[:7] for a in avant] == [
    ("entree", 1, "32", "Christèle GENTES", "50.000", "hektor_partage_suppose", "conversion"),
    ("sortie", 1, "32", "Christèle GENTES", "50.000", "hektor_partage_suppose", "conversion")], avant
assert all(a[7] == DOSSIER_ID for a in avant), avant
assert [x[:6] for x in voisine] == [
    ("entree", 1, "32", "CHRISTELE GENTES", "50.000", "classeur_reconstitue"),
    ("sortie", 1, "32", "CHRISTELE GENTES", "50.000", "classeur_reconstitue")], voisine
assert orph == 0 and vr == 0, (orph, vr)
assert deja == 0 and not tab_existe, (deja, tab_existe)

ANC = {c: "%s %s %s (%s)" % (u, n, p.rstrip("0").rstrip("."), o) for c, r, u, n, p, o, _e, _d in avant}
POURQUOI = ("SON ORDRE du 27/11 (« 3. puis le partage DECHAUD 50 / GENTES 50 sur la chaine 3647 ») ; sa decision du 24/11 : "
            "le classeur fait foi, une supposition de Hektor n'est pas une donnee -- l'ancienne mise de cote avec sa place")
J = ",\n".join("    (%d, '%s', %d, %s, %s, %s, %s, %s)" % (
    i + 1, c, r, q(u), q(nm), q("%g" % p), q(ANC[c]), q(POURQUOI)) for i, (c, r, u, nm, p, _b) in enumerate(NOUVELLES))
NV = ",\n".join("    ('%s', %d, %s, %s, %s)" % (c, r, q(u), q(nm), q("%g" % p)) for c, r, u, nm, p, _b in NOUVELLES)
D = {"lot": LOT, "tab": TAB, "mdc": MDC, "expr": EXPR, "vr": VR, "orph": ORPH, "n_rep": n_rep, "e_rep": e_rep,
     "e_hors": e_hors, "e_voisine": e_voisine, "ch": CH, "voisine": VOISINE, "membres": MEMBRES, "uuid": UUID,
     "numero": NUMERO, "dossier": DOSSIER_ID, "ligne": LIGNE, "num": NUM, "ecrit_par": ECRIT_PAR, "j": J, "nv": NV}

CORPS = """
-- ─── ① LES GARDES : la chaine, ses deux suppositions, sa voisine et le registre EXACTEMENT tels que mesures ──────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.%(tab)s') is not null then raise exception '⛔ G0 : la sauvegarde existe deja -- ce patch ne se rejoue pas'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s';
  if n <> 0 then raise exception '⛔ G0 : %% ligne(s) du lot deja au journal', n; end if;
  select string_agg(app_affaire_id::text, ',' order by app_affaire_id) into e from public.app_affaire_ledger where app_chaine_id = %(ch)s;
  if e is distinct from '%(membres)s' then raise exception '⛔ G1 : %(ch)s porte les membres %% au lieu de %(membres)s', e; end if;
  select count(*) into n from public.app_affaire_ledger where app_chaine_id = %(ch)s and app_dossier_uuid::text = '%(uuid)s'
     and app_dossier_numero = '%(numero)s' and app_dossier_id = %(dossier)s;
  if n <> 3 then raise exception '⛔ G1 : %% piece(s) sur 3 portent %(numero)s (%(uuid)s)', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id = %(ch)s;
  if n <> 2 then raise exception '⛔ G2 : %(ch)s porte %% part(s) au lieu des deux suppositions', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id = %(ch)s and rang = 1 and cote in ('entree', 'sortie')
     and hektor_user_id = '32' and nom_au_moment = 'Christèle GENTES' and pourcentage = 50 and origine = 'hektor_partage_suppose'
     and ecrit_par = 'conversion' and app_dossier_id = %(dossier)s;
  if n <> 2 then raise exception '⛔ G2 : les parts de %(ch)s ne sont pas les deux suppositions mesurees (GENTES 50/50, hektor_partage_suppose)'; end if;
  e := (select %(expr)s from public.app_affaire_repartition where app_chaine_id = %(voisine)s);
  if e <> '%(e_voisine)s' then raise exception '⛔ G3 : %(voisine)s (427UDDSF) a bouge : empreinte %% au lieu de %(e_voisine)s', e; end if;
  e := (select %(expr)s from public.app_affaire_repartition);
  if e <> '%(e_rep)s' then raise exception '⛔ G4 : le registre des parts a bouge depuis la mesure : empreinte %% au lieu de %(e_rep)s', e; end if;
  raise notice '✅ gardes : %(ch)s = %(membres)s sur %(numero)s, ses deux suppositions telles que mesurees ; %(voisine)s et le registre inchanges';
end $$;

-- ─── ② LA SAUVEGARDE DATEE : les parts ENTIERES de %(ch)s, AVEC la cle primaire et la RLS ──────────────────────────────
create table public.%(tab)s (like public.app_affaire_repartition including defaults including constraints including indexes);
insert into public.%(tab)s select * from public.app_affaire_repartition where app_chaine_id = %(ch)s;
revoke all on public.%(tab)s from public, anon, authenticated;
alter table public.%(tab)s enable row level security;

-- ─── ③ LE JOURNAL : chaque part remplacee, avec SA LIGNE D'ORIGINE (%(ligne)s, n° %(num)s) et SA PLACE ─────────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select '%(lot)s', v.n, 'repartition', 'app_affaire_repartition (' || v.cote || ', rang ' || v.rang || ')',
       'REMPLACER (le classeur fait foi ; l''ancienne mise de cote)', %(ch)s, d.kind, d.app_chaine_id, d.app_dossier_numero,
       d.app_dossier_uuid, %(ch)s, d.kind, d.app_chaine_id, d.app_dossier_numero,
       v.uid || ' ' || v.nom || ' ' || v.pct, v.ancienne, '%(ligne)s', %(num)s,
       'Sheet (Negociateurs / Pourcentages, regles du 13/11), ligne %(num)s lue en direct le 27/11', v.pourquoi, '%(mdc)s'
  from (values
%(j)s
  ) v(n, cote, rang, uid, nom, pct, ancienne, pourquoi)
  left join public.app_affaire_ledger d on d.app_affaire_id = %(ch)s;

-- ─── ④ LE GESTE : chaque supposition MISE DE COTE (entiere, avec son numero de chaine), puis la part du classeur posee ───
insert into public.app_affaire_repartition_mise_de_cote
  (ancien_app_chaine_id, dossier_ou_elle_vit, app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment,
   pourcentage, origine, ecrit_le, ecrit_par, mise_de_cote_par, pourquoi)
select r.app_chaine_id, r.app_chaine_id, r.app_chaine_id, r.app_dossier_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment,
       r.pourcentage, r.origine, r.ecrit_le, r.ecrit_par, '%(mdc)s',
       j.pourquoi || ' -- remplacee par ' || j.valeur || ' (ligne ' || j.ligne_origine || ', n° ' || j.ligne_origine_num || ')'
  from public.app_affaire_repartition r
  join public.app_classeur_realignement_journal j
    on j.lot = '%(lot)s' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')';
delete from public.app_affaire_repartition r using public.app_classeur_realignement_journal j
 where j.lot = '%(lot)s' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select m.app_chaine_id, m.app_dossier_id, m.cote, m.rang, v.uid, v.nom, v.pct::numeric, 'classeur_reconstitue', now(), '%(ecrit_par)s'
  from (values
%(nv)s
  ) v(cote, rang, uid, nom, pct)
  join public.app_affaire_repartition_mise_de_cote m
    on m.mise_de_cote_par = '%(mdc)s' and m.app_chaine_id = %(ch)s and m.cote = v.cote and m.rang = v.rang;

-- ─── ⑤ LES CONTROLES ───────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_affaire_repartition r join (values
%(nv)s
  ) v(cote, rang, uid, nom, pct) on r.cote = v.cote and r.rang = v.rang
   where r.app_chaine_id = %(ch)s and r.hektor_user_id = v.uid and r.nom_au_moment = v.nom and r.pourcentage = v.pct::numeric
     and r.origine = 'classeur_reconstitue' and r.ecrit_par = '%(ecrit_par)s' and r.app_dossier_id = %(dossier)s;
  if n <> 2 or (select count(*) from public.app_affaire_repartition where app_chaine_id = %(ch)s) <> 2 then
    raise exception '⛔ controle : %(ch)s ne porte pas exactement DECHAUD entree 50 + GENTES sortie 50 du classeur'; end if;
  if (select sum(pourcentage) from public.app_affaire_repartition where app_chaine_id = %(ch)s) <> 100 then
    raise exception '⛔ controle : la somme de %(ch)s n''est pas 100'; end if;
  -- SON TEMOIN : plus aucune part hektor sur %(ch)s (le verrou de la nuit : l'absorbeur saute une chaine sans part hektor%%)
  select count(*) into n from public.app_affaire_repartition where app_chaine_id = %(ch)s and coalesce(origine, '') like 'hektor%%';
  if n <> 0 then raise exception '⛔ controle : %% part(s) hektor encore sur %(ch)s', n; end if;
  e := (select %(expr)s from public.app_affaire_repartition where app_chaine_id = %(voisine)s);
  if e <> '%(e_voisine)s' then raise exception '⛔ controle : %(voisine)s a bouge (%%)', e; end if;
  e := (select %(expr)s from public.app_affaire_repartition where app_chaine_id <> %(ch)s);
  if e <> '%(e_hors)s' then raise exception '⛔ controle : une part HORS de %(ch)s a bouge (%%)', e; end if;
  if (select count(*) from public.app_affaire_repartition) <> %(n_rep)s then
    raise exception '⛔ controle : %% parts au lieu de %(n_rep)s', (select count(*) from public.app_affaire_repartition); end if;
  -- la regle 6 : chaque supposition est dans la mise de cote, ENTIERE (sa sauvegarde le prouve)
  select count(*) into n from public.app_affaire_repartition_mise_de_cote m join public.%(tab)s s
    on s.app_chaine_id = m.ancien_app_chaine_id and s.cote = m.cote and s.rang = m.rang and s.hektor_user_id = m.hektor_user_id
   and s.pourcentage = m.pourcentage and s.origine is not distinct from m.origine and s.ecrit_le = m.ecrit_le
   and s.ecrit_par is not distinct from m.ecrit_par and s.nom_au_moment is not distinct from m.nom_au_moment
   and s.app_dossier_id is not distinct from m.app_dossier_id
   where m.mise_de_cote_par = '%(mdc)s';
  if n <> 2 or (select count(*) from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = '%(mdc)s') <> 2 then
    raise exception '⛔ controle : %% supposition(s) mise(s) de cote entiere(s) sur 2', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s' and ligne_origine = '%(ligne)s'
     and ligne_origine_num = %(num)s and ancienne_valeur is not null;
  if n <> 2 then raise exception '⛔ controle : %% ligne(s) au journal sur 2', n; end if;
  if %(orph)s <> 0 then raise exception '⛔ controle : des parts orphelines'; end if;
  if %(vr)s <> 0 then raise exception '⛔ controle : une vente reglee sans part'; end if;
  e := (select %(expr)s from public.app_affaire_repartition);
  %(apres)s
  raise notice '✅ %(ch)s : DECHAUD entree 50 + GENTES sortie 50 du classeur, plus aucune part hektor ; les deux suppositions mises de cote ; %(voisine)s et le reste intacts ; empreinte apres %%', e;
end $$;
"""
INVERSE = """
-- ─── L'INVERSE : les parts du classeur retirees de %(ch)s, les deux suppositions remises, le journal du lot retire ───────
delete from public.app_affaire_repartition where app_chaine_id = %(ch)s and ecrit_par = '%(ecrit_par)s' and origine = 'classeur_reconstitue';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select ancien_app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
  from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = '%(mdc)s';
delete from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = '%(mdc)s';
delete from public.app_classeur_realignement_journal where lot = '%(lot)s';
do $$
begin
  if (select count(*) from (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
        ecrit_le, ecrit_par from public.app_affaire_repartition where app_chaine_id = %(ch)s
      except all select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le,
        ecrit_par from public.%(tab)s) z) <> 0
     or (select count(*) from (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
        ecrit_le, ecrit_par from public.%(tab)s
      except all select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le,
        ecrit_par from public.app_affaire_repartition where app_chaine_id = %(ch)s) z) <> 0 then
    raise exception '⛔ inverse : %(ch)s n''est pas revenue a la sauvegarde'; end if;
  raise notice '✅ inverse : %(ch)s est revenue aux deux suppositions, la mise de cote et le journal du lot sont vides';
end $$;
"""
LIGNES_NUIT = ("(select jsonb_agg(jsonb_build_object('app_chaine_id', app_chaine_id, 'app_dossier_id', app_dossier_id, "
               "'cote', cote, 'rang', rang, 'hektor_user_id', hektor_user_id, 'nom_au_moment', nom_au_moment, "
               "'pourcentage', pourcentage, 'origine', origine)) from public.%s)" % TAB)
P3647 = ("(select string_agg(cote || ' ' || hektor_user_id || ' ' || nom_au_moment || ' ' || pourcentage || ' ' || origine, "
         "' + ' order by cote, rang) from public.app_affaire_repartition where app_chaine_id = %d)" % CH)
E3647 = "(select %s from public.app_affaire_repartition where app_chaine_id = %d)" % (EXPR, CH)
A_BLANC_NUIT = """
-- ─── L'EPREUVE DE LA NUIT : LES VRAIES FONCTIONS, avec les lignes memes que la nuit a ecrites sur %(ch)s ──────────────────
create temporary table r_milieu on commit drop as select count(*) n, %(expr)s e, %(p3647)s p, %(e3647)s e_ch from public.app_affaire_repartition;
create temporary table r_absorbeur on commit drop as select public.app_repartition_absorber(%(lignes_nuit)s) rep;
create temporary table r_purge on commit drop as select public.app_repartition_purger_orphelines() rep;
do $$
declare m record; a jsonb; p jsonb;
begin
  select * into m from r_milieu; select rep into a from r_absorbeur; select rep into p from r_purge;
  if (a->>'proteges_app')::int <> 1 or (a->>'dossiers_ecrits')::int <> 0 then
    raise exception '⛔ A BLANC : l''absorbeur n''a pas saute %(ch)s : %%', a; end if;
  if %(e3647)s <> m.e_ch then raise exception '⛔ A BLANC : la nuit a touche %(ch)s'; end if;
  if (select %(expr)s from public.app_affaire_repartition) <> m.e then
    raise exception '⛔ A BLANC : la nuit rejouee a touche le registre des parts (purge %%)', p; end if;
end $$;
"""
TEMOIN_INVERSE = """
-- ─── LE TEMOIN INVERSE : sur %(ch)s remise en supposition, l'absorbeur doit ECRIRE (sinon l'epreuve ne prouvait rien) ───
create temporary table r_inverse_nuit on commit drop as select public.app_repartition_absorber(%(lignes_nuit)s) rep;
do $$
declare a record; m record; t jsonb; n int; e text; ab jsonb; pu jsonb;
begin
  select * into a from r_avant; select * into m from r_milieu; select rep into t from r_inverse_nuit;
  select rep into ab from r_absorbeur; select rep into pu from r_purge;
  if (t->>'dossiers_ecrits')::int <> 1 or (t->>'proteges_app')::int <> 0 then
    raise exception '⛔ A BLANC : le temoin inverse ne mord pas -- l''absorbeur n''ecrit pas sur %(ch)s en supposition : %%', t; end if;
  select count(*), %(expr)s into n, e from public.app_affaire_repartition;
  if n <> a.n or e <> a.e then raise exception '⛔ A BLANC : apres le temoin inverse, le registre n''est plus celui d''avant'; end if;
  raise exception 'A BLANC PARTS 3647 VERT -- RIEN N''EST ECRIT. Avant : %% parts (%%), 3647 = %%. Apres le patch : %% parts, 3647 = %%, empreinte apres %%. La nuit rejouee : absorbeur %%, purge %%. Apres l''inverse : = avant. Temoin inverse : %%.',
    a.n, left(a.e, 8), a.p, m.n, m.p, m.e, ab, pu, t;
end $$;
"""
D.update({"p3647": P3647, "e3647": E3647, "lignes_nuit": LIGNES_NUIT})
ent = "-- %s -- genere par phase2/checks/parts_3647_generer_patch_2026-11-27.py (son ordre du 27/11)\n"
reel_apres = ("if e <> '%s' then raise exception '⛔ controle : empreinte apres %% au lieu de %s', e; end if;" % (
    arg.empreinte_apres, arg.empreinte_apres) if arg.empreinte_apres else
    "raise exception '⛔ le patch reel exige l''empreinte d''apres rendue par l''essai a blanc (--empreinte-apres)';")
fichiers = {
    "patch_parts_3647_2026-11-27.sql": ent % "patch_parts_3647_2026-11-27"
    + "-- Retour arriere : patch_parts_3647_2026-11-27_INVERSE.sql . Controle : patch_parts_3647_2026-11-27_REPETITION.sql\n"
    + "\nbegin;\n" + (CORPS % dict(D, apres=reel_apres)) + "\ncommit;\n",
    "patch_parts_3647_2026-11-27_A_BLANC.sql": ent % "A BLANC -- ⛔ aucun commit, une erreur VOULUE annule tout" + "\nbegin;\n"
    + "create temporary table r_avant on commit drop as select count(*) n, %s e, %s p from public.app_affaire_repartition;\n" % (
        EXPR, P3647)
    + (CORPS % dict(D, apres="null;")) + (A_BLANC_NUIT % D) + (INVERSE % D) + (TEMOIN_INVERSE % D),
    "patch_parts_3647_2026-11-27_INVERSE.sql": ent % "INVERSE" + "\nbegin;\n" + (INVERSE % D) + "\ncommit;\n",
    "patch_parts_3647_2026-11-27_REPETITION.sql": ent % "REPETITION (lecture seule)" + """select
  %(p3647)s as parts_3647_attendu_dechaud_entree_gentes_sortie_classeur,
  (select count(*) from public.app_affaire_repartition where app_chaine_id = %(ch)s and coalesce(origine, '') like 'hektor%%') as parts_hektor_sur_3647_attendu_0,
  (select %(expr)s from public.app_affaire_repartition where app_chaine_id = %(voisine)s) = '%(e_voisine)s' as voisine_3646_intacte,
  (select count(*) from public.app_classeur_realignement_journal where lot = '%(lot)s') as journal_attendu_2,
  (select count(*) from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = '%(mdc)s') as mise_de_cote_attendu_2,
  %(orph)s as orphelines_attendu_0, %(vr)s as ventes_reglees_sans_part_attendu_0,
  (select count(*) from public.app_affaire_repartition) as parts_attendu_%(n_rep)s,
  (select %(expr)s from public.app_affaire_repartition) as empreinte_apres;
""" % D,
}
for nom, txt in fichiers.items():
    p_ = OUT / nom
    p_.write_bytes(txt.encode("utf-8"))
    print("-> supabase/%s (%d octets, md5 %s)" % (nom, p_.stat().st_size, hashlib.md5(p_.read_bytes()).hexdigest()[:8]))
print("avant : %d parts, %s ; hors 3647 %s ; 3646 %s" % (n_rep, e_rep, e_hors, e_voisine))
