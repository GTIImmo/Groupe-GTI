"""LES ETIQUETTES DE LA VAGUE : LA VRAIE POSE CONTRE LA PREVISION DU PROTOCOLE, PIECE PAR PIECE -- un essai a blanc (25/11).

POURQUOI. L'essai a blanc complet a rendu les quatre gestes de la VRAIE pose (app_poser_etiquettes_dossier) sur l'arrivee
de la vague : pose 0, propagation 0, FUSION 231 dossiers / 250 lignes, SCISSION 295 dossiers / 612 lignes. Le protocole,
lui, prevoit 797 pieces qui changent d'etiquette dont 612 vers une NEUVE (son modele : coupe_preuve_interne.pose_de_nuit).
612 + 250 = 862 n'est pas 797 : on ne laisse pas passer un ecart non explique. On compare donc PIECE PAR PIECE.

LE FICHIER (supabase/vague_du_soir_<jour>_ETIQUETTES_A_BLANC.sql), joue par la commande (`--a-blanc-sql`), tout s'annule :
  les chaines de la vague -> la vraie pose -> pour chaque piece : l'etiquette d'avant, celle d'apres, celle que le protocole
  prevoit (une etiquette existante, ou « NEUVE:<groupe> ») -> les ecarts, nommes.

USAGE : python -X utf8 phase2/checks/vague_etiquettes_a_blanc.py --passage P --date J   (le passage a blanc du retrait)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks")
sys.path.insert(0, r"C:\Hektor\Projet")
import coupe_preuve_interne as K  # noqa: E402
import protocole_classeur as P  # noqa: E402
import protocole_portes as PO  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--passage", type=int, required=True)
ap.add_argument("--date", required=True)
arg = ap.parse_args()
_AB = P.DOSSIER.parent / "protocole_a_blanc_retrait_e"
P.SOCLE, P.DOSSIER, PO.MODULE = _AB / "socle.sqlite", _AB, _AB / "affaire_ledger_sans_4126_21520.py"
con = P.socle()
image, = con.execute("select image from passage where id=?", (arg.passage,)).fetchone()
con.close()
I = P.Image(P.IMAGES / image)
lab_img = {a: I.pieces[a]["app_dossier_uuid"] for a in I.pieces}
chE, _ = PO.rejeu_en_cache("E", image, P.DOSSIER / ("brouillon_detachements_protocole_passage_%d.csv" % arg.passage),
                           {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"}, False)
labE = K.pose_de_nuit(lab_img, chE)
change = {a: l_ for a, l_ in labE.items() if l_ != lab_img.get(a)}
neuves = {a for a, l_ in change.items() if str(l_).startswith("NEUVE")}
print("la prevision du protocole : %d pieces changent d'etiquette, dont %d vers une NEUVE (%d groupes neufs) ; %d vers une "
      "etiquette existante" % (len(change), len(neuves), len({change[a] for a in neuves}), len(change) - len(neuves)))
A2 = json.loads((Path(r"C:\Hektor\chantier_classeur_q6_cache\vague_du_soir") / ("corps_a2_%s.json" % arg.date))
                .read_text(encoding="utf-8"))
TXT = ";".join("%d=%s" % (a, change[a]) for a in sorted(change))
assert "'" not in TXT
sql = """-- vague_du_soir_%(d)s_ETIQUETTES_A_BLANC -- genere par phase2/checks/vague_etiquettes_a_blanc.py
-- ⛔ N'ECRIT RIEN : la derniere instruction ANNULE tout (erreur voulue). AUCUN commit.
begin;
create temporary table vet_avant on commit drop as select app_affaire_id a, app_dossier_uuid u from public.app_affaire_ledger;
%(sim)s
create temporary table vet_pose on commit drop as select * from public.app_poser_etiquettes_dossier();
create temporary table vet_apres on commit drop as select app_affaire_id a, app_dossier_uuid u from public.app_affaire_ledger;
create temporary table vet_prevu (a bigint primary key, prevu text) on commit drop;
insert into vet_prevu select split_part(x, '=', 1)::bigint, split_part(x, '=', 2) from unnest(string_to_array('%(txt)s', ';')) x;
do $$
declare p text; n_chg int; n_prevu int; inatt int; exist_ok int; exist_ko int; neuf_neuf int; neuf_pas int;
        grp_bij int; grp_n int; uuid_n int; ex text; ex2 text;
begin
  select string_agg(geste || ' ' || dossiers || '/' || lignes, ' ; ') into p from vet_pose;
  select count(*) into n_chg from vet_avant v join vet_apres w using (a) where v.u is distinct from w.u;
  select count(*) into n_prevu from vet_prevu;
  -- 1. les pieces qui changent alors que le protocole ne le prevoit pas
  select count(*), string_agg(v.a || ':' || coalesce(v.u::text, '-') || '->' || coalesce(w.u::text, '-'), ' ' order by v.a)
    into inatt, ex from vet_avant v join vet_apres w using (a)
   where v.u is distinct from w.u and not exists (select 1 from vet_prevu p where p.a = v.a);
  -- 2. prevues vers une etiquette EXISTANTE : la meme ?
  select count(*) filter (where w.u::text = p.prevu), count(*) filter (where w.u::text is distinct from p.prevu)
    into exist_ok, exist_ko from vet_prevu p join vet_apres w using (a) where p.prevu not like 'NEUVE%%';
  select string_agg(p.a || ' prevu ' || p.prevu || ' obtenu ' || coalesce(w.u::text, '-'), ' ; ' order by p.a) into ex2
    from (select * from vet_prevu where prevu not like 'NEUVE%%') p join vet_apres w using (a) where w.u::text is distinct from p.prevu;
  -- 3. prevues NEUVES : une etiquette qui n'existait pas avant, et LA MEME par groupe, une DIFFERENTE par groupe
  select count(*) filter (where w.u is not null and not exists (select 1 from vet_avant v2 where v2.u = w.u)),
         count(*) filter (where w.u is null or exists (select 1 from vet_avant v2 where v2.u = w.u))
    into neuf_neuf, neuf_pas from vet_prevu p join vet_apres w using (a) where p.prevu like 'NEUVE%%';
  select count(distinct p.prevu), count(distinct w.u) into grp_n, uuid_n
    from vet_prevu p join vet_apres w using (a) where p.prevu like 'NEUVE%%';
  select count(*) into grp_bij from (select p.prevu from vet_prevu p join vet_apres w using (a) where p.prevu like 'NEUVE%%'
                                      group by p.prevu having count(distinct w.u) <> 1) z;
  raise exception 'A BLANC ETIQUETTES -- RIEN N''EST ECRIT. LA VRAIE POSE : %%. Pieces dont l''etiquette change : %% (prevues : %%). ① changees SANS etre prevues : %% %%. ② prevues vers une etiquette existante : %% identiques, %% differentes %%. ③ prevues NEUVES : %% recoivent une etiquette qui n''existait pas, %% non ; %% groupes prevus -> %% etiquettes neuves obtenues, %% groupe(s) eclate(s).',
    p, n_chg, n_prevu, inatt, coalesce(left(ex, 600), ''), exist_ok, exist_ko, coalesce(left(ex2, 600), ''), neuf_neuf, neuf_pas,
    grp_n, uuid_n, grp_bij;
end $$;
""" % {"d": arg.date, "sim": A2["sim"], "txt": TXT}
out = Path(r"C:\Hektor\Projet\supabase") / ("vague_du_soir_%s_ETIQUETTES_A_BLANC.sql" % arg.date)
out.write_text(sql, encoding="utf-8")
print("-> %s (%d octets, md5 %s)" % (out, out.stat().st_size, hashlib.md5(out.read_bytes()).hexdigest()[:8]))
