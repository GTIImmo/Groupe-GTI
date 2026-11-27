"""A1 ET A3 DE LA VAGUE DU SOIR -- LES PATCHS ET LEUR CHIFFRAGE (son 11e mot du 24/11 et son mot du 25/11).

SON MOT : « ⭐ (a). A1 ET A3 AVEC LA VAGUE, A L'ETAPE 7, LE MEME SOIR. [...] un reflet N'EST PAS UNE CLE. Les avis sont
identifies par la ligne du Sheet, les notes et les conditions par leur transaction -- tout cela est FIXE. Rafraichir un
reflet ne peut deplacer aucune ecriture. [...] ⬜ Mais chiffre-le-moi [...] : sur ces 7 000, COMBIEN la vague rend faux,
et combien A1 et A3 en reparent ? Je veux savoir ce que je repare. »

CE SCRIPT N'ECRIT RIEN EN BASE : il lit la copie locale (a jour apres la descente) et Supabase (pooler en lecture seule), et
FABRIQUE des fichiers.

  A1  app_classeur_avis (cle : id_unique, la ligne du Sheet) : le reflet (app_dossier_uuid, app_dossier_numero) recalcule
      depuis les VRAIES pieces de la ligne (le jugement du protocole pour une ligne tranchee, le gel sinon) : UNE etiquette
      -> elle ; plusieurs ou aucune -> VIDE plutot que fausse (sa regle du 24/11). Les trois colonnes d'avis jamais touchees.
      PAR PIECES : la liste ligne -> pieces voyage dans le patch ; l'etiquette est lue AU MOMENT DU GESTE, apres la pose.
  A3  app_affaire_note (cle : app_affaire_id) et app_affaire_condition (cle : app_affaire_id, rang) : le reflet
      app_chaine_id recalcule depuis la transaction (le registre, au moment du geste). ⚠ Leur app_dossier_id est le numero
      de BIEN de l'app (affaire_ledger.py, l. 55), pas l'etiquette : la vague n'y touche pas, A3 non plus.
  Ni ecrit_le ni ecrit_par ne bougent : un reflet rafraichi n'est pas une ecriture de quelqu'un. Chaque reflet change est
  au journal (lot a1_vague_<jour> / a3_vague_<jour>) avec l'ancienne valeur ; l'inverse relit la sauvegarde datee.

LE CHIFFRAGE (sa question), PREVU ICI par le rejeu, et MESURE par l'essai a blanc complet (la vraie pose des etiquettes) :
  pour chaque table : combien de reflets ; combien sont FAUX AUJOURD'HUI ; combien LA VAGUE REND FAUX (justes aujourd'hui,
  faux apres) ; combien A1/A3 ECRIVENT (= tous les faux apres la vague, y compris ceux d'aujourd'hui) ; FAUX APRES : 0.

USAGE : python -X utf8 phase2/checks/a1_a3_vague_generer_patch_2026-11-25.py --passage P [--retrait-e] --date J
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks")
sys.path.insert(0, r"C:\Hektor\Projet")
import coupe_preuve_interne as K  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402
import protocole_classeur as P  # noqa: E402
import protocole_portes as PO  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--passage", type=int, required=True)
ap.add_argument("--retrait-e", action="store_true", help="la vague entiere : le dossier a blanc du retrait de E")
ap.add_argument("--date", required=True)
ap.add_argument("--a1-attendu", type=int, default=-1, help="le nombre d'ecritures d'A1 MESURE par l'essai a blanc complet")
ap.add_argument("--a3-attendu", type=int, default=-1, help="le nombre d'ecritures d'A3 MESURE par l'essai a blanc complet")
arg = ap.parse_args()
if arg.retrait_e:
    _AB = P.DOSSIER.parent / "protocole_a_blanc_retrait_e"
    P.SOCLE, P.DOSSIER, PO.MODULE = _AB / "socle.sqlite", _AB, _AB / "affaire_ledger_sans_4126_21520.py"
OUT = Path(r"C:\Hektor\Projet\supabase")
D8 = arg.date.replace("-", "")


def dire(s=""):
    print(s, flush=True)


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


class T(str):
    def __mod__(self, d):
        import re
        return re.sub(r"%\((\w+)\)s|%%", lambda m: "%" if m.group(0) == "%%" else str(d[m.group(1)]), self)


# ─── L'ETAT D'ARRIVEE PREVU ───────────────────────────────────────────────────────────────────────────────────────
con = P.socle()
image, version = con.execute("select image, version from passage where id=?", (arg.passage,)).fetchone()
V = {i: {"verdict": v, "pieces": set(json.loads(ps)) if ps else set()}
     for i, v, ps in con.execute("select id_unique, verdict, pieces from verdict where passage=?", (arg.passage,))}
con.close()
TR = {i for i, v in V.items() if v["verdict"] == "TRANCHEE"}
I = P.Image(P.IMAGES / image)
PI = I.pieces
lab_img = {a: PI[a]["app_dossier_uuid"] for a in PI}
NUM = {PI[a]["app_dossier_uuid"]: PI[a]["app_dossier_numero"] for a in PI if PI[a]["app_dossier_uuid"]}
ch_img = {a: int(PI[a]["app_chaine_id"]) for a in PI if PI[a]["app_chaine_id"] is not None}
brouillon = P.DOSSIER / ("brouillon_detachements_protocole_passage_%d.csv" % arg.passage)
chE, _ = PO.rejeu_en_cache("E", image, brouillon, {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"}, False)
labE = K.pose_de_nuit(lab_img, chE)
gel_l = defaultdict(list)
for i, a, ro, *_r in I.gel:
    gel_l[i].append(int(a))
dire("A1 / A3 DE LA VAGUE -- passage %d (%s), image %s ; brouillon %s" % (arg.passage, version, image, brouillon.name))


def vraies(i):
    src = V[i]["pieces"] if i in TR else gel_l.get(i, [])
    return sorted(a for a in src if I.nature.get(a) == PC.VRAIE)


def regle(labs: set):
    labs = {x for x in labs if x}
    return next(iter(labs)) if len(labs) == 1 else None


def num(lab):
    if lab is None:
        return "VIDE"
    return "NEUF" if str(lab).startswith("NEUVE") else (NUM.get(lab) or str(lab)[:8])


loc = sqlite3.connect("file:C:/Hektor/Projet/phase2/phase2.sqlite?mode=ro", uri=True)
AV = loc.execute("select id_unique, app_dossier_uuid, app_dossier_numero from app_classeur_avis").fetchall()
NO = loc.execute("select app_affaire_id, app_chaine_id from app_affaire_note").fetchall()
CO = loc.execute("select app_affaire_id, rang, app_chaine_id from app_affaire_condition").fetchall()
loc.close()

# ─── LE CHIFFRAGE PREVU ───────────────────────────────────────────────────────────────────────────────────────────
ch = {"A1 avis": Counter(), "A3 notes": Counter(), "A3 conditions": Counter()}
mapping = {}
for i, refl, _n in AV:
    pcs = vraies(i)
    mapping[i] = pcs
    auj, apres = regle({lab_img.get(a) for a in pcs}), regle({labE.get(a) for a in pcs})
    c = ch["A1 avis"]
    c["reflets"] += 1
    c["portent un reflet"] += refl is not None
    c["FAUX AUJOURD'HUI"] += (refl != auj)
    c["LA VAGUE REND FAUX (justes aujourd'hui)"] += (refl == auj and refl != apres)
    c["A1 ECRIT (tous les faux apres la vague)"] += (refl != apres)
    c["dont -> VIDE (plusieurs ou aucune etiquette)"] += (refl != apres and apres is None)
    c["dont -> un numero NEUF de la vague"] += (refl != apres and apres is not None and str(apres).startswith("NEUVE"))
for nom, rows in (("A3 notes", [(a, None, c_) for a, c_ in NO]), ("A3 conditions", CO)):
    c = ch[nom]
    for a, _r, refl in rows:
        a = int(a)
        refl = int(refl) if refl is not None else None
        c["reflets"] += 1
        if a not in ch_img:
            c["transaction ABSENTE du registre (nommee, pas touchee)"] += 1
            continue
        c["FAUX AUJOURD'HUI"] += (refl != ch_img[a])
        c["LA VAGUE REND FAUX (justes aujourd'hui)"] += (refl == ch_img[a] and refl != chE.get(a))
        c["A3 ECRIT (tous les faux apres la vague)"] += (refl != chE.get(a))
dire()
dire("LE CHIFFRAGE PREVU (le rejeu de la vague ; l'essai a blanc complet le MESURE avec la vraie pose des etiquettes) :")
for nom, c in ch.items():
    dire("   %-14s %s" % (nom, " . ".join("%s %d" % kv for kv in c.items())))
absentes = sorted(int(a) for a, _c in NO if int(a) not in ch_img)
absentes_co = sorted("%d/%d" % (int(a), int(r)) for a, r, _c in CO if int(a) not in ch_img)
dire("   les notes dont la transaction n'est plus au registre (nommees, pas touchees) : %s" % absentes)
dire("   les conditions dont la transaction n'est plus au registre (nommees, pas touchees) : %s" % absentes_co)

# ─── LES EMPREINTES DE FABRICATION, CHEZ SUPABASE (lecture seule) ────────────────────────────────────────────────
E_AV = ("md5(coalesce(string_agg(concat_ws('|', id_unique, app_dossier_uuid, app_dossier_numero), ';' order by id_unique), ''))")
E_NO = "md5(coalesce(string_agg(concat_ws('|', app_affaire_id, app_chaine_id), ';' order by app_affaire_id), ''))"
E_CO = "md5(coalesce(string_agg(concat_ws('|', app_affaire_id, rang, app_chaine_id), ';' order by app_affaire_id, rang), ''))"
cn, cu = P.pooler()
cu.execute("select (select count(*) from public.app_classeur_avis), (select %s from public.app_classeur_avis), "
           "(select count(*) from public.app_affaire_note), (select %s from public.app_affaire_note), "
           "(select count(*) from public.app_affaire_condition), (select %s from public.app_affaire_condition)"
           % (E_AV, E_NO, E_CO))
n_av, e_av, n_no, e_no, n_co, e_co = cu.fetchone()
cu.execute("select id_unique from public.app_classeur_avis")
ids_sb = {r[0] for r in cu.fetchall()}
cn.rollback()
cn.close()
if ids_sb != set(mapping) or n_no != len(NO) or n_co != len(CO):
    dire("⛔ la copie locale n'est pas Supabase (avis %d/%d, notes %d/%d, conditions %d/%d)" % (
        len(ids_sb), len(mapping), n_no, len(NO), n_co, len(CO)))
    sys.exit(1)
dire("   chez Supabase : avis %d (%s) . notes %d (%s) . conditions %d (%s) -- la copie locale porte les memes cles" % (
    n_av, e_av[:8], n_no, e_no[:8], n_co, e_co[:8]))

# ─── LES PATCHS ───────────────────────────────────────────────────────────────────────────────────────────────────
M_TXT = ";".join("%s:%s" % (i, ",".join(map(str, mapping[i]))) for i in sorted(mapping))
assert "'" not in M_TXT and ";" not in "".join(mapping)
D = {"d": arg.date, "d8": D8, "m": "'" + M_TXT + "'", "n_av": n_av, "e_av": e_av, "n_no": n_no, "e_no": e_no,
     "n_co": n_co, "e_co": e_co, "E_AV": E_AV, "E_NO": E_NO, "E_CO": E_CO, "passage": arg.passage, "image": image,
     "n_abs": len(absentes), "absentes": ", ".join(map(str, absentes)) or "-1",
     "src": "phase2/checks/a1_a3_vague_generer_patch_2026-11-25.py", "a1_att": arg.a1_attendu, "a3_att": arg.a3_attendu}

A1 = T("""
-- ═══ A1 : LE REFLET DES AVIS (app_classeur_avis), PAR PIECES -- lot a1_vague_%(d)s ═══════════════════════════════════
do $$
declare n int; e text;
begin
  if to_regclass('public.app_classeur_avis_reflets_avant_a1vague_%(d8)s') is not null then
    raise exception '⛔ A1 G0 : la sauvegarde existe deja -- ce patch ne se rejoue pas'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'a1_vague_%(d)s';
  if n <> 0 then raise exception '⛔ A1 G0 : % ligne(s) du lot deja au journal', n; end if;
  select count(*), %(E_AV)s into n, e from public.app_classeur_avis;
  if n <> %(n_av)s or e <> '%(e_av)s' then
    raise exception '⛔ A1 G1 : les avis ont change depuis la fabrication (% lignes, empreinte % au lieu de %(n_av)s, %(e_av)s)', n, e;
  end if;
end $$;
-- LA LISTE « ligne -> ses vraies pieces » (le jugement du protocole), une seule fois
create temporary table a1_m (x text) on commit drop;
insert into a1_m select unnest(string_to_array(%(m)s, ';'));
create temporary table a1_lignes (id_unique text primary key) on commit drop;
insert into a1_lignes select split_part(x, ':', 1) from a1_m;
create temporary table a1_pieces (id_unique text, piece bigint) on commit drop;
insert into a1_pieces select split_part(x, ':', 1), p::bigint
  from a1_m cross join lateral unnest(string_to_array(split_part(x, ':', 2), ',')) p
 where p <> '';
do $$
declare n int;
begin
  select count(*) into n from public.app_classeur_avis a where not exists (select 1 from a1_lignes g where g.id_unique = a.id_unique);
  if n <> 0 then raise exception '⛔ A1 G2 : % avis hors de la liste des lignes', n; end if;
  select count(*) into n from a1_pieces p where not exists (select 1 from public.app_affaire_ledger l where l.app_affaire_id = p.piece);
  if n <> 0 then raise exception '⛔ A1 G2 : % piece(s) de la liste absentes du registre', n; end if;
end $$;
-- LA CIBLE : une etiquette parmi les vraies pieces de la ligne -> elle ; plusieurs ou aucune -> VIDE
create temporary table a1_cible on commit drop as
select g.id_unique, case when count(distinct l.app_dossier_uuid) = 1 then min(l.app_dossier_uuid::text)::uuid end as uuid
  from a1_lignes g left join a1_pieces p on p.id_unique = g.id_unique
  left join public.app_affaire_ledger l on l.app_affaire_id = p.piece
 group by g.id_unique;
alter table a1_cible add column numero text;
update a1_cible c set numero = (select l.app_dossier_numero from public.app_affaire_ledger l
                                 where l.app_dossier_uuid = c.uuid and l.app_dossier_numero is not null limit 1)
 where c.uuid is not null;
create table public.app_classeur_avis_reflets_avant_a1vague_%(d8)s as
  select id_unique, app_dossier_uuid, app_dossier_numero, now() as copie_le from public.app_classeur_avis;
revoke all on public.app_classeur_avis_reflets_avant_a1vague_%(d8)s from public, anon, authenticated;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, valeur, ancienne_valeur, ligne_origine, lot_origine, pourquoi, ecrit_par)
select 'a1_vague_%(d)s', row_number() over (order by a.id_unique), 'reflet', 'app_classeur_avis (app_dossier_uuid, app_dossier_numero)',
       'RAFRAICHIR LE REFLET (A1)', coalesce((select min(p.piece) from a1_pieces p where p.id_unique = a.id_unique), 0),
       coalesce(c.numero, 'VIDE') || ' ' || coalesce(c.uuid::text, '-'),
       coalesce(a.app_dossier_numero, 'VIDE') || ' ' || coalesce(a.app_dossier_uuid::text, '-'), a.id_unique,
       'A1 (passage %(passage)s, image %(image)s)',
       'SON MOT du 24/11 : un reflet n''est pas une cle -- le reflet suit les vraies pieces de la ligne (une etiquette -> elle ; plusieurs ou aucune -> VIDE)',
       'patch_a1_vague'
  from public.app_classeur_avis a join a1_cible c on c.id_unique = a.id_unique
 where a.app_dossier_uuid is distinct from c.uuid or a.app_dossier_numero is distinct from c.numero;
update public.app_classeur_avis a set app_dossier_uuid = c.uuid, app_dossier_numero = c.numero
  from a1_cible c
 where c.id_unique = a.id_unique and (a.app_dossier_uuid is distinct from c.uuid or a.app_dossier_numero is distinct from c.numero);
do $$
declare n int; j int;
begin
  select count(*) into n from public.app_classeur_avis a join a1_cible c on c.id_unique = a.id_unique
   where a.app_dossier_uuid is distinct from c.uuid or a.app_dossier_numero is distinct from c.numero;
  if n <> 0 then raise exception '⛔ A1 controle : % reflet(s) d''avis encore decolle(s)', n; end if;
  select count(*) into j from public.app_classeur_realignement_journal where lot = 'a1_vague_%(d)s';
  select count(*) into n from public.app_classeur_avis a join public.app_classeur_avis_reflets_avant_a1vague_%(d8)s s using (id_unique)
   where a.app_dossier_uuid is distinct from s.app_dossier_uuid or a.app_dossier_numero is distinct from s.app_dossier_numero;
  if n <> j then raise exception '⛔ A1 controle : % reflet(s) change(s) pour % ligne(s) au journal', n, j; end if;
  if %(a1_att)s >= 0 and j <> %(a1_att)s then
    raise exception '⛔ A1 controle : % ecriture(s) au lieu des %(a1_att)s mesurees par l''essai a blanc complet', j; end if;
  raise notice '✅ A1 : % reflet(s) d''avis rafraichi(s), tous au journal ; 0 decolle', j;
end $$;
""")

A3 = T("""
-- ═══ A3 : LE REFLET DE CHAINE DES NOTES ET DES CONDITIONS, PAR LA TRANSACTION -- lot a3_vague_%(d)s ═════════════════
do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_note_reflets_avant_a3vague_%(d8)s') is not null then
    raise exception '⛔ A3 G0 : la sauvegarde existe deja -- ce patch ne se rejoue pas'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'a3_vague_%(d)s';
  if n <> 0 then raise exception '⛔ A3 G0 : % ligne(s) du lot deja au journal', n; end if;
  select count(*), %(E_NO)s into n, e from public.app_affaire_note;
  if n <> %(n_no)s or e <> '%(e_no)s' then
    raise exception '⛔ A3 G1 : les notes ont change depuis la fabrication (% , %)', n, e; end if;
  select count(*), %(E_CO)s into n, e from public.app_affaire_condition;
  if n <> %(n_co)s or e <> '%(e_co)s' then
    raise exception '⛔ A3 G1 : les conditions ont change depuis la fabrication (% , %)', n, e; end if;
end $$;
create table public.app_affaire_note_reflets_avant_a3vague_%(d8)s as
  select app_affaire_id, app_chaine_id, now() as copie_le from public.app_affaire_note;
create table public.app_affaire_condition_reflets_avant_a3vague_%(d8)s as
  select app_affaire_id, rang, app_chaine_id, now() as copie_le from public.app_affaire_condition;
revoke all on public.app_affaire_note_reflets_avant_a3vague_%(d8)s, public.app_affaire_condition_reflets_avant_a3vague_%(d8)s
  from public, anon, authenticated;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_app_chaine_id, vers_app_affaire_id, vers_app_chaine_id, valeur,
   ancienne_valeur, lot_origine, pourquoi, ecrit_par)
select 'a3_vague_%(d)s', row_number() over (order by t, a, r), 'reflet', colonne, 'RAFRAICHIR LE REFLET (A3)', a, avant, a,
       apres, coalesce(apres::text, '-'), coalesce(avant::text, '-'), 'A3 (passage %(passage)s, image %(image)s)',
       'SON MOT du 24/11 : un reflet n''est pas une cle -- le reflet de chaine suit la transaction (le registre)', 'patch_a3_vague'
  from (select 1 t, n.app_affaire_id a, 0 r, 'app_affaire_note.app_chaine_id' colonne, n.app_chaine_id avant, l.app_chaine_id apres
          from public.app_affaire_note n join public.app_affaire_ledger l on l.app_affaire_id = n.app_affaire_id
         where n.app_chaine_id is distinct from l.app_chaine_id
        union all
        select 2, c.app_affaire_id, c.rang, 'app_affaire_condition.app_chaine_id (rang ' || c.rang || ')', c.app_chaine_id, l.app_chaine_id
          from public.app_affaire_condition c join public.app_affaire_ledger l on l.app_affaire_id = c.app_affaire_id
         where c.app_chaine_id is distinct from l.app_chaine_id) x;
update public.app_affaire_note n set app_chaine_id = l.app_chaine_id from public.app_affaire_ledger l
 where l.app_affaire_id = n.app_affaire_id and n.app_chaine_id is distinct from l.app_chaine_id;
update public.app_affaire_condition c set app_chaine_id = l.app_chaine_id from public.app_affaire_ledger l
 where l.app_affaire_id = c.app_affaire_id and c.app_chaine_id is distinct from l.app_chaine_id;
do $$
declare n int; j int;
begin
  select count(*) into n from public.app_affaire_note n join public.app_affaire_ledger l on l.app_affaire_id = n.app_affaire_id
   where n.app_chaine_id is distinct from l.app_chaine_id;
  if n <> 0 then raise exception '⛔ A3 controle : % note(s) au reflet faux', n; end if;
  select count(*) into n from public.app_affaire_condition c join public.app_affaire_ledger l on l.app_affaire_id = c.app_affaire_id
   where c.app_chaine_id is distinct from l.app_chaine_id;
  if n <> 0 then raise exception '⛔ A3 controle : % condition(s) au reflet faux', n; end if;
  -- les notes dont la transaction n'est plus au registre : NOMMEES, pas touchees
  select count(*) into n from public.app_affaire_note n
   where not exists (select 1 from public.app_affaire_ledger l where l.app_affaire_id = n.app_affaire_id);
  if n <> %(n_abs)s then raise exception '⛔ A3 controle : % note(s) sans transaction au lieu de %(n_abs)s (%(absentes)s)', n; end if;
  select count(*) into j from public.app_classeur_realignement_journal where lot = 'a3_vague_%(d)s';
  select (select count(*) from public.app_affaire_note n join public.app_affaire_note_reflets_avant_a3vague_%(d8)s s using (app_affaire_id)
           where n.app_chaine_id is distinct from s.app_chaine_id)
       + (select count(*) from public.app_affaire_condition c join public.app_affaire_condition_reflets_avant_a3vague_%(d8)s s
           using (app_affaire_id, rang) where c.app_chaine_id is distinct from s.app_chaine_id) into n;
  if n <> j then raise exception '⛔ A3 controle : % reflet(s) change(s) pour % ligne(s) au journal', n, j; end if;
  if %(a3_att)s >= 0 and j <> %(a3_att)s then
    raise exception '⛔ A3 controle : % ecriture(s) au lieu des %(a3_att)s mesurees par l''essai a blanc complet', j; end if;
  raise notice '✅ A3 : % reflet(s) de chaine rafraichi(s) (notes et conditions), tous au journal ; 0 faux', j;
end $$;
""")

INV = T("""
-- ═══ L'INVERSE D'A3 PUIS D'A1 : les reflets reprennent leur valeur sauvegardee, le journal des deux lots est retire ═══
update public.app_affaire_note n set app_chaine_id = s.app_chaine_id from public.app_affaire_note_reflets_avant_a3vague_%(d8)s s
 where s.app_affaire_id = n.app_affaire_id and n.app_chaine_id is distinct from s.app_chaine_id;
update public.app_affaire_condition c set app_chaine_id = s.app_chaine_id
  from public.app_affaire_condition_reflets_avant_a3vague_%(d8)s s
 where s.app_affaire_id = c.app_affaire_id and s.rang = c.rang and c.app_chaine_id is distinct from s.app_chaine_id;
update public.app_classeur_avis a set app_dossier_uuid = s.app_dossier_uuid, app_dossier_numero = s.app_dossier_numero
  from public.app_classeur_avis_reflets_avant_a1vague_%(d8)s s
 where s.id_unique = a.id_unique and (a.app_dossier_uuid is distinct from s.app_dossier_uuid
                                      or a.app_dossier_numero is distinct from s.app_dossier_numero);
delete from public.app_classeur_realignement_journal where lot in ('a1_vague_%(d)s', 'a3_vague_%(d)s');
do $$
declare n int;
begin
  select count(*) into n from public.app_classeur_avis a join public.app_classeur_avis_reflets_avant_a1vague_%(d8)s s using (id_unique)
   where a.app_dossier_uuid is distinct from s.app_dossier_uuid or a.app_dossier_numero is distinct from s.app_dossier_numero;
  if n <> 0 then raise exception '⛔ inverse A1 : % avis differents de la sauvegarde', n; end if;
  select count(*) into n from public.app_affaire_note n join public.app_affaire_note_reflets_avant_a3vague_%(d8)s s using (app_affaire_id)
   where n.app_chaine_id is distinct from s.app_chaine_id;
  if n <> 0 then raise exception '⛔ inverse A3 : % notes differentes de la sauvegarde', n; end if;
  raise notice '✅ inverse A1 et A3 : les reflets sont revenus a la sauvegarde';
end $$;
""")

ENT = T("""-- %(nom)s -- genere par %(src)s
-- A1 et A3 de la vague du soir (passage %(passage)s, image %(image)s). ⛔ Etape 7, apres A2, et SUR SON ACCORD.
""")
for nom, corps in (("patch_a1_vague_%s" % arg.date, A1), ("patch_a3_vague_%s" % arg.date, A3)):
    (OUT / (nom + ".sql")).write_text(ENT % dict(D, nom=nom) + "\nbegin;\n" + corps % D + "\ncommit;\n", encoding="utf-8")
(OUT / ("patch_a1_a3_vague_%s_INVERSE.sql" % arg.date)).write_text(
    ENT % dict(D, nom="patch_a1_a3_vague_%s_INVERSE" % arg.date) + "\nbegin;\n" + INV % D + "\ncommit;\n", encoding="utf-8")
# les corps seuls, pour l'essai a blanc complet (compose avec A2)
(Path(r"C:\Hektor\chantier_classeur_q6_cache\vague_du_soir") / ("corps_a1_a3_%s.json" % arg.date)).write_text(
    json.dumps({"a1": A1 % D, "a3": A3 % D, "inverse": INV % D, "chiffrage_prevu": {k: dict(v) for k, v in ch.items()},
                "absentes": absentes, "absentes_conditions": absentes_co,
                "empreintes": {"avis": e_av, "notes": e_no, "conditions": e_co}}, ensure_ascii=False), encoding="utf-8")
for f in ("patch_a1_vague_%s.sql" % arg.date, "patch_a3_vague_%s.sql" % arg.date, "patch_a1_a3_vague_%s_INVERSE.sql" % arg.date):
    p = OUT / f
    dire("-> supabase/%s (%d octets, md5 %s)" % (f, p.stat().st_size, hashlib.md5(p.read_bytes()).hexdigest()[:8]))
