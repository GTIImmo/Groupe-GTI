"""④ LES 6 SUPPOSITIONS DE HEKTOR ET ⑤ LES 2 MOITIES FAUSSES (24/11, ses 5e et 6e mots) -- fabrique les patchs de repartition.

SES MOTS : « ④ LES 6 SUPPOSITIONS DE HEKTOR -> RIEN A TRANCHER, J'AI DEJA TRANCHE LE 24/11 : le classeur fait foi. Tu remplaces,
l'ancienne de cote avec sa place. Applique. » -- « ⑤ [...] CORRIGE 739a0db1 ET TR42PT5H : la moitie fausse est remplacee par
le nom du Sheet, l'ancienne part MISE DE COTE avec son ancien numero (regle 6). Journal. » -- « ⛔ NE TOUCHE PAS JRE23R1G ». --
« A chaque famille : a blanc, puis le geste avec ses empreintes, puis la repetition, puis l'inverse joue a blanc. Sauvegarde
datee. Et la ligne d'origine sur chaque ecriture. »

LA MESURE (24/11 ; le Sheet de l'image du passage 79, resolu par l'annuaire avec les regles du 13/11 -- RR.nettoyer, resoudre,
decomposer ; les parts lues dans la copie locale, et EXIGEES telles quelles chez Supabase par les gardes) :
  ④ chacune des 6 chaines ne porte QUE deux suppositions de Hektor (entree + sortie, 50 / 50). On remplace LES DEUX : la
    chaine prend la repartition du classeur EN ENTIER. ⚠ Pour A07EC3DH et QXDW8EQA, la sortie nomme deja la bonne personne :
    seule son ORIGINE change (« hektor_partage_suppose » -> « classeur_reconstitue ») -- regle 6 du 23/11 : « la meme
    origine » fait partie de l'identite d'une part. Et une chaine qui garderait une seule supposition resterait a demi
    hektor, ce que le classeur dement.
  ⑤ deux chaines du classeur (13/11), une moitie fausse chacune : 27196 (739a0db1) entree COUDERT -> HERITIER ; 27195
    (TR42PT5H) entree HERITIER -> COUDERT. La sortie, juste, ne bouge pas.
LA NUIT : app_repartition_absorber saute toute chaine qui porte une part non « hektor% » -> une fois remplacees, ces chaines
  ne recoivent plus de supposition. app_repartition_purger_orphelines ne touche que les chaines sans transaction -- aucune ici.
REGLE 6 : chaque part remplacee part ENTIERE dans app_affaire_repartition_mise_de_cote (la table dessinee le 22/11), avec son
  ancien numero de chaine ; l'INVERSE la repose a l'identique.
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks")
sys.path.insert(0, r"C:\Hektor\Projet")
import rapatrier_repartition_classeur as RR  # noqa: E402

SORTIE = Path(r"C:\Hektor\Projet\supabase")


class T(str):
    def __mod__(self, m):
        out = re.sub(r"%\((\w+)\)([sd])", lambda mo: str(m[mo.group(1)]) if mo.group(2) == "s" else "%d" % m[mo.group(1)],
                     str(self))
        return out.replace("%%", "%")


def q(s):
    return "null" if s is None else "'" + str(s).replace("'", "''") + "'"


ap = argparse.ArgumentParser()
ap.add_argument("--avant", nargs="*", default=[])
ap.add_argument("--apres", nargs="*", default=[])
a = ap.parse_args()
AVANT = dict(x.split("=") for x in a.avant)
APRES = dict(x.split("=") for x in a.apres)

# le nom au moment, ecrit comme le rapatriement du 13/11 (prenom + nom de la fiche choisie, mots normalises)
loc = sqlite3.connect("file:C:/Hektor/Projet/phase2/phase2.sqlite?mode=ro", uri=True)
loc.row_factory = sqlite3.Row
gens = defaultdict(list)
for r in loc.execute("select hektor_user_id, nom, prenom, is_active from app_hektor_negotiator_agency_directory"):
    n_ = " ".join(sorted(RR.mots_du_nom(r["nom"])))
    p_ = " ".join(sorted(RR.mots_du_nom(r["prenom"])))
    if n_:
        gens[(n_, p_)].append(dict(r))
PAR_NOM = defaultdict(list)
for (n_, p_), f in gens.items():
    act = [x for x in f if x.get("is_active") in (1, "1", True, "true", "True")]
    ch = sorted(act or f, key=lambda x: int(str(x["hektor_user_id"])))[0]
    PAR_NOM[n_].append({"nom": n_, "prenom": p_, "hektor_user_id": str(ch["hektor_user_id"]), "fiches": len(f)})
# ⭐ LE NOM DU SHEET, RESOLU PAR LA MEME FONCTION QUE LE RAPATRIEMENT DU 13/11 (RR.resoudre : alias, prenom, initiale, SES
#   levees d'ambiguite du 13/11 -- « CHAMPAGNAC » -> « Joel CHAMPAGNAC »), et la personne EXIGEE egale a celle prevue
SHEET_NOM = {("A07EC3DH", "entree"): "DECHAUD", ("A07EC3DH", "sortie"): "GENTES", ("DHXRAK9O", "entree"): "NICOLOSI",
             ("DHXRAK9O", "sortie"): "NICOLOSI", ("72GQRHVB", "entree"): "CAVARD", ("72GQRHVB", "sortie"): "CAVARD",
             ("7IHI7YTJ", "entree"): "CHAMPAGNAC", ("7IHI7YTJ", "sortie"): "CHAMPAGNAC", ("QXDW8EQA", "entree"): "DIMARIA",
             ("QXDW8EQA", "sortie"): "TRIOLLIER", ("CS38OO8R", "entree"): "CHAMPAGNAC", ("CS38OO8R", "sortie"): "CHAMPAGNAC",
             ("739a0db1", "entree"): "HERITIER", ("TR42PT5H", "entree"): "COUDERT"}
NOM_RESOLU = {}
for (ligne_, cote_), brut_ in SHEET_NOM.items():
    q_, motif_ = RR.resoudre(brut_, PAR_NOM, None, None)
    assert q_ is not None, (ligne_, brut_, motif_)
    NOM_RESOLU[(ligne_, cote_)] = (str(q_["hektor_user_id"]), q_["nom_au_moment"])

# (ligne, n° au Sheet, chaine, cote, rang, ANCIENNE (uid, nom, pct, origine), NOUVELLE (uid, pct))
SUPPOSITIONS = [
    ("A07EC3DH", 535, 1875, "entree", 1, ("32", "Christèle GENTES", 50, "hektor_partage_suppose"), ("31", 50)),
    ("A07EC3DH", 535, 1875, "sortie", 1, ("32", "Christèle GENTES", 50, "hektor_partage_suppose"), ("32", 50)),
    ("DHXRAK9O", None, 9370, "entree", 1, ("0", "Cet utilisateur a été supprimé", 50, "hektor_partage_suppose"), ("146", 50)),
    ("DHXRAK9O", None, 9370, "sortie", 1, ("0", "Cet utilisateur a été supprimé", 50, "hektor_partage_suppose"), ("146", 50)),
    ("72GQRHVB", None, 6391, "entree", 1, ("0", "Cet utilisateur a été supprimé", 50, "hektor_partage_suppose"), ("149", 50)),
    ("72GQRHVB", None, 6391, "sortie", 1, ("0", "Cet utilisateur a été supprimé", 50, "hektor_partage_suppose"), ("149", 50)),
    ("7IHI7YTJ", None, 4234, "entree", 1, ("45", "Delphine BLANCHARD", 50, "hektor_partage_suppose"), ("238", 50)),
    ("7IHI7YTJ", None, 4234, "sortie", 1, ("45", "Delphine BLANCHARD", 50, "hektor_partage_suppose"), ("238", 50)),
    ("QXDW8EQA", None, 1027, "entree", 1, ("168", "M. Benjamin TRIOLLIER", 50, "hektor_partage_suppose"), ("190", 50)),
    ("QXDW8EQA", None, 1027, "sortie", 1, ("168", "M. Benjamin TRIOLLIER", 50, "hektor_partage_suppose"), ("168", 50)),
    ("CS38OO8R", None, 27984, "entree", 1, ("237", "Michel BALMAYER", 50, "hektor_partage_suppose"), ("238", 50)),
    ("CS38OO8R", None, 27984, "sortie", 1, ("237", "Michel BALMAYER", 50, "hektor_partage_suppose"), ("238", 50)),
]
CORRECTIONS = [
    ("739a0db1", 4668, 27196, "entree", 1, ("81", "NICOLAS COUDERT", 50, "classeur_reconstitue"), ("82", 50)),
    ("TR42PT5H", 173, 27195, "entree", 1, ("82", "CELINE HERITIER", 50, "classeur_reconstitue"), ("81", 50)),
]
# le numero au Sheet de chaque ligne, lu dans le passage (jamais retape)
import protocole_classeur as P  # noqa: E402
_con = P.socle()
NUM = {i: n for i, n in _con.execute("select id_unique, num from verdict where passage=79")}


def lot(nom, lignes, pourquoi_lot, n_par_chaine):
    tab = nom.replace("-", "")
    chaines = sorted({x[2] for x in lignes})
    ids = ", ".join(map(str, chaines))
    empreinte = ("(select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, "
                 "pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from "
                 "public.app_affaire_repartition where app_chaine_id in (%s))" % ids)
    anciennes = ",\n    ".join("(%d, %s, %d, %s, %s, %s)" % (x[2], q(x[3]), x[4], q(x[5][0]), q("%g" % x[5][2]), q(x[5][3]))
                               for x in lignes)
    nouvelles = ",\n    ".join("(%d, %s, %s, %d, %d, %s, %s, %s, %s, %s, %s)" % (
        k, q(x[0]), "null" if NUM.get(x[0]) is None else str(NUM[x[0]]), x[2], x[4], q(x[3]), q(x[6][0]),
        q(NOM_RESOLU[(x[0], x[3])][1]), q("%g" % x[6][1]),
        q("%s %s %g (%s)" % (x[5][0], x[5][1], x[5][2], x[5][3])), q(pourquoi_lot))
        for k, x in enumerate(lignes, 1))
    voulu = ",\n    ".join("(%d, %s, %d, %s, %s)" % (c, q(co), r, q(u), q("%g" % p)) for c, co, r, u, p in sorted(
        {(x[2], x[3], x[4], x[6][0], x[6][1]) for x in lignes}))
    for x in lignes:
        assert NOM_RESOLU[(x[0], x[3])][0] == x[6][0], ("la resolution ne donne pas la personne prevue", x, NOM_RESOLU[(x[0], x[3])])
    poser = ",\n    ".join("(%d, %s, %d, %s, %s, %s, %s)" % (x[2], q(x[3]), x[4], q(x[6][0]), q(NOM_RESOLU[(x[0], x[3])][1]),
                                                          q("%g" % x[6][1]), q(x[0])) for x in lignes)
    n = len(lignes)
    m = {"lot": nom, "tab": tab, "ids": ids, "poser": poser, "n": n, "nch": len(chaines), "nrows": n_par_chaine * len(chaines),
         "anciennes": anciennes, "nouvelles": nouvelles, "voulu": voulu, "empreinte": empreinte, "nom": "patch_" + nom,
         "garde_avant": ("if e <> '%s' then raise exception '⛔ garde : empreinte %% au lieu de %s', e; end if;" % (
             AVANT[nom], AVANT[nom])) if nom in AVANT else "-- (empreinte d'avant non exigee)",
         "garde_apres": ("if e <> '%s' then raise exception '⛔ controle : empreinte apres %% au lieu de %s', e; end if;" % (
             APRES[nom], APRES[nom])) if nom in APRES else "-- (empreinte d'apres non exigee)",
         "garde_retour": ("if e <> '%s' then raise exception '⛔ controle du retour : empreinte %% au lieu de %s (celle "
                          "d''AVANT)', e; end if;" % (AVANT[nom], AVANT[nom])) if nom in AVANT else "raise notice 'retour %', e;"}
    gardes = T("""
-- ─── ① LES GARDES : chaque part a remplacer est EXACTEMENT celle mesuree, et chaque chaine porte %(nrows)d parts en tout ──
do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_repartition_avant_%(tab)s') is not null then
    raise exception '⛔ garde : la sauvegarde existe deja -- ce patch ne se rejoue pas';
  end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s';
  if n <> 0 then raise exception '⛔ garde : % ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_affaire_repartition r join (values
    %(anciennes)s) v(ch, cote, rang, uid, pct, origine)
      on r.app_chaine_id = v.ch and r.cote = v.cote and r.rang = v.rang
   where r.hektor_user_id = v.uid and r.pourcentage = v.pct::numeric and r.origine = v.origine;
  if n <> %(n)d then raise exception '⛔ garde : % part(s) telles que mesurees sur %(n)d', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (%(ids)s);
  if n <> %(nrows)d then raise exception '⛔ garde : les %(nch)d chaines portent % part(s) au lieu de %(nrows)d', n; end if;
  e := %(empreinte)s;
  %(garde_avant)s
  raise notice '✅ gardes : %(n)d parts telles que mesurees sur %(nch)d chaines ; empreinte %%', e;
end $$;
""") % m
    aller = T("""
-- ─── ② LA SAUVEGARDE DATEE : les parts ENTIERES des %(nch)d chaines ──────────────────────────────────────────────────────
create table public.app_affaire_repartition_avant_%(tab)s as
  select * from public.app_affaire_repartition where app_chaine_id in (%(ids)s);
revoke all on public.app_affaire_repartition_avant_%(tab)s from public, anon, authenticated;

-- ─── ③ LA TABLE DE LA REGLE 6 (dessinee le 22/11, telle quelle) : une part n'est jamais supprimee, elle est mise de cote ──
create table if not exists public.app_affaire_repartition_mise_de_cote (
  id                     bigint generated always as identity primary key,
  ancien_app_chaine_id   bigint      not null,
  dossier_ou_elle_vit    bigint,
  app_chaine_id          bigint      not null,
  app_dossier_id         bigint,
  cote                   text        not null,
  rang                   smallint    not null,
  hektor_user_id         text        not null,
  nom_au_moment          text,
  pourcentage            numeric     not null,
  origine                text,
  ecrit_le               timestamptz not null,
  ecrit_par              text,
  mise_de_cote_le        timestamptz not null default now(),
  mise_de_cote_par       text        not null,
  pourquoi               text        not null
);
revoke all on public.app_affaire_repartition_mise_de_cote from public, anon, authenticated;
alter table public.app_affaire_repartition_mise_de_cote enable row level security;

-- ─── ④ LE JOURNAL : chaque part remplacee, avec SA LIGNE D'ORIGINE et SA PLACE (la chaine, le cote, le rang) ──────────────
alter table public.app_classeur_realignement_journal add column if not exists ancienne_valeur text;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select '%(lot)s', v.n, 'repartition', 'app_affaire_repartition (' || v.cote || ', rang ' || v.rang || ')',
       'REMPLACER (le classeur fait foi ; l''ancienne mise de cote)', v.ch, d.kind, d.app_chaine_id, d.app_dossier_numero,
       d.app_dossier_uuid, v.ch, d.kind, d.app_chaine_id, d.app_dossier_numero,
       v.uid || ' ' || v.nom || ' ' || v.pct, v.ancienne, v.ligne, v.num,
       'Sheet (Negociateurs / Pourcentages, regles du 13/11)', v.pourquoi, '%(nom)s'
  from (values
    %(nouvelles)s
  ) v(n, ligne, num, ch, rang, cote, uid, nom, pct, ancienne, pourquoi)
  left join public.app_affaire_ledger d on d.app_affaire_id = v.ch;

-- ─── ⑤ LE GESTE : l'ancienne part MISE DE COTE (entiere, avec son numero de chaine), puis la nouvelle posee ──────────────
insert into public.app_affaire_repartition_mise_de_cote
  (ancien_app_chaine_id, dossier_ou_elle_vit, app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment,
   pourcentage, origine, ecrit_le, ecrit_par, mise_de_cote_par, pourquoi)
select r.app_chaine_id, r.app_chaine_id, r.app_chaine_id, r.app_dossier_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment,
       r.pourcentage, r.origine, r.ecrit_le, r.ecrit_par, '%(nom)s', j.pourquoi || ' -- remplacee par ' || j.valeur || ' (ligne ' || j.ligne_origine || ')'
  from public.app_affaire_repartition r
  join public.app_classeur_realignement_journal j
    on j.lot = '%(lot)s' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')';
delete from public.app_affaire_repartition r using public.app_classeur_realignement_journal j
 where j.lot = '%(lot)s' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select m.app_chaine_id, m.app_dossier_id, m.cote, m.rang, v.uid, v.nom, v.pct::numeric, 'classeur_reconstitue', now(),
       'classeur:' || v.ligne
  from (values
    %(poser)s
  ) v(ch, cote, rang, uid, nom, pct, ligne)
  join public.app_affaire_repartition_mise_de_cote m
    on m.mise_de_cote_par = '%(nom)s' and m.app_chaine_id = v.ch and m.cote = v.cote and m.rang = v.rang;

-- ─── ⑥ LES CONTROLES ─────────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  -- chaque chaine porte EXACTEMENT la repartition voulue
  select count(*) into n from public.app_affaire_repartition r join (values
    %(voulu)s) v(ch, cote, rang, uid, pct)
      on r.app_chaine_id = v.ch and r.cote = v.cote and r.rang = v.rang
   where r.hektor_user_id = v.uid and r.pourcentage = v.pct::numeric and r.origine = 'classeur_reconstitue';
  if n <> %(n)d then raise exception '⛔ controle : % part(s) voulue(s) sur %(n)d', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (%(ids)s);
  if n <> %(nrows)d then raise exception '⛔ controle : % part(s) sur les chaines au lieu de %(nrows)d', n; end if;
  select count(*) into n from (select app_chaine_id from public.app_affaire_repartition where app_chaine_id in (%(ids)s)
                                group by 1 having sum(pourcentage) <> 100) x;
  if n <> 0 then raise exception '⛔ controle : % chaine(s) dont la somme n''est pas 100', n; end if;
  -- la regle 6 : chaque ancienne part est dans la mise de cote, ENTIERE (sa sauvegarde le prouve)
  select count(*) into n from public.app_affaire_repartition_mise_de_cote m
    join public.app_affaire_repartition_avant_%(tab)s s
      on s.app_chaine_id = m.app_chaine_id and s.cote = m.cote and s.rang = m.rang and s.hektor_user_id = m.hektor_user_id
     and s.pourcentage = m.pourcentage and s.origine is not distinct from m.origine and s.ecrit_le = m.ecrit_le
     and s.ecrit_par is not distinct from m.ecrit_par and m.ancien_app_chaine_id = s.app_chaine_id
   where m.mise_de_cote_par = '%(nom)s';
  if n <> %(n)d then raise exception '⛔ controle : % ancienne(s) part(s) mise(s) de cote, entiere(s), sur %(n)d', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal
   where lot = '%(lot)s' and ligne_origine is not null and ancienne_valeur is not null;
  if n <> %(n)d then raise exception '⛔ controle : % ligne(s) au journal, avec ligne d''origine et ancienne valeur, sur %(n)d', n; end if;
  e := %(empreinte)s;
  %(garde_apres)s
  raise notice '✅ %(n)d parts remplacees, %(n)d mises de cote entieres, sommes a 100, journal ; empreinte apres %%', e;
end $$;
""") % m
    retour = T("""
-- ─── LE RETOUR : retirer ce que le lot a pose, reposer chaque ancienne part depuis la mise de cote, a l'identique ─────────
do $$
declare n int;
begin
  select count(*) into n from public.app_affaire_repartition r join public.app_classeur_realignement_journal j
      on j.lot = '%(lot)s' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')'
   where r.origine = 'classeur_reconstitue' and r.ecrit_par = 'classeur:' || j.ligne_origine;
  if n <> %(n)d then raise exception '⛔ garde du retour : % part(s) du lot retrouvee(s) sur %(n)d (une saisie est passee ?)', n; end if;
end $$;
delete from public.app_affaire_repartition r using public.app_classeur_realignement_journal j
 where j.lot = '%(lot)s' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')'
   and r.origine = 'classeur_reconstitue' and r.ecrit_par = 'classeur:' || j.ligne_origine;
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select m.app_chaine_id, m.app_dossier_id, m.cote, m.rang, m.hektor_user_id, m.nom_au_moment, m.pourcentage, m.origine,
       m.ecrit_le, m.ecrit_par
  from public.app_affaire_repartition_mise_de_cote m where m.mise_de_cote_par = '%(nom)s';
delete from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = '%(nom)s';
do $$
declare n int; e text;
begin
  select count(*) into n from (
    (select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition where app_chaine_id in (%(ids)s)
     except select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition_avant_%(tab)s)
    union all
    (select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition_avant_%(tab)s
     except select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition where app_chaine_id in (%(ids)s))) d;
  if n <> 0 then raise exception '⛔ controle du retour : % part(s) differente(s) de la sauvegarde', n; end if;
  e := %(empreinte)s;
  %(garde_retour)s
end $$;
""") % m
    return gardes, aller, retour, empreinte


for nom, lignes, pq, npc in (
        ("suppositions_2026-11-24", SUPPOSITIONS,
         "④ SA DECISION du 24/11 (3e mot ④, 5e mot ④ « Applique ») : le classeur fait foi ; une supposition de Hektor n'est "
         "pas une donnee -- l'ancienne mise de cote avec sa place", 2),
        ("corrections_2026-11-24", CORRECTIONS,
         "⑤ SA DECISION du 24/11 (5e mot ⑤) : la moitie fausse remplacee par le nom du Sheet, l'ancienne part mise de cote "
         "avec son ancien numero (regle 6) ; COUDERT et HERITIER melanges sur le meme bien ; JRE23R1G n'est PAS touchee", 2)):
    gardes, aller, retour, empreinte = lot(nom, lignes, pq, npc)
    base = "patch_" + nom
    entete = ("-- %s -- genere par phase2/checks/repartition_4_5_generer_patchs_2026-11-24.py (« rien ne s'ecrit sans mon "
              "accord sur le patch »)\n-- Retour arriere : %s_INVERSE.sql . Controle : %s_REPETITION.sql\n" % (base, base, base))
    (SORTIE / (base + ".sql")).write_text(entete + "\nbegin;\n" + gardes + aller + "\ncommit;\n", encoding="utf-8")
    (SORTIE / (base + "_ALLER_RETOUR_A_BLANC.sql")).write_text(
        entete + "-- ⛔ A BLANC : le patch PUIS son inverse dans la MEME transaction ; aucun commit ; erreur voulue a la fin.\n"
        "\nbegin;\n" + gardes + aller + "\ndo $$ declare e text; begin e := " + empreinte + "; perform set_config('ar.apres', "
        "e, true); end $$;\n" + retour + "\ndo $$ declare e text; begin e := " + empreinte + "; raise exception "
        "'ALLER-RETOUR A BLANC VERT : apres = % ; retour = % -- RIEN N''EST ECRIT (erreur voulue)', "
        "current_setting('ar.apres'), e; end $$;\n", encoding="utf-8")
    (SORTIE / (base + "_INVERSE.sql")).write_text(entete + "\nbegin;\n" + retour + "\ncommit;\n", encoding="utf-8")
    (SORTIE / (base + "_EMPREINTE_LECTURE.sql")).write_text("select %s as empreinte;\n" % empreinte, encoding="utf-8")
    (SORTIE / (base + "_REPETITION.sql")).write_text(
        "-- %s -- les controles, rejouables. AUCUNE ECRITURE.\nselect '%s' as lot, (select count(*) from "
        "public.app_classeur_realignement_journal where lot = '%s') as au_journal, (select count(*) from "
        "public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = '%s') as mises_de_cote, %s as empreinte, "
        "'%s' as attendue;\n" % (base, nom, nom, base, empreinte, APRES.get(nom, "?")), encoding="utf-8")
for f in sorted(SORTIE.glob("patch_suppositions_2026-11-24*.sql")) + sorted(SORTIE.glob("patch_corrections_2026-11-24*.sql")):
    t = f.read_text(encoding="utf-8")
    print("%-60s %6d octets ; commit %d ; jetons %d" % (f.name, len(t.encode()), t.count("\ncommit;"), t.count("%(")))
print(NOM_RESOLU)
