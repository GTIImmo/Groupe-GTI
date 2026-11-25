"""LES DATES D'ANNULATION QUI RESTENT -- LE PATCH, SON ESSAI A BLANC, SON INVERSE, SA REPETITION (son mot du 25/11).

SON MOT : « ⭐ ET DANS LE MEME GESTE, POSE LES DATES D'ANNULATION QUI RESTENT -- ma regle : la date du Sheet sur SON compromis
quand il n'en a pas. Dis-moi combien exactement avant de poser. Les 2 anterieures restent ecartees. »

LE COMPTE, MESURE le 25/11 (apres la vague) : les 6 du 24/11 sont toujours des compromis ANNULES SANS DATE ; moins les 2
anterieures (S3HOG6UL sur 17387, 6U5DQQ4J sur 24450 : sa decision du 24/11, comme les 106 de C3) -> 4 A POSER. Les jumelles :
O6R10ZQA est la bonne et sa date (21/09/2021) est DEJA sur 20073 ; T2GZOY5O est en reserve -> rien a poser.
Les dates sont RELUES dans le Sheet du jour (image 2026-11-25_072625, colonne « Annulée »).

LE GESTE : seulement sur une case VIDE, la valeur LUE AU JOURNAL ; les 2 anterieures et T2GZOY5O NOMMEES au journal (rien
ecrit) ; la sauvegarde datee des 7 lignes ; les autres colonnes de ces lignes INTACTES ; l'empreinte d'apres exigee.
USAGE : python -X utf8 phase2/checks/dates_annulation_generer_patch_2026-11-25.py [--empreinte-apres MD5]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import protocole_classeur as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--empreinte-apres", default="")
arg = ap.parse_args()
LOT, TAB = "dates_annulation_2026-11-25", "app_affaire_ledger_avant_dates_annulation_20261125"
OUT = Path(__file__).resolve().parents[2] / "supabase"
I = P.Image(P.IMAGES / "2026-11-25_072625")
D = I.D
iso = lambda s: "%s-%s-%s" % (s[6:10], s[3:5], s[0:2])
# (ligne, n° au Sheet, son compromis, geste, pourquoi)
LIGNES = [
    ("TR42PT5H", 173, 27195, "POSER", "sa regle : la date du Sheet sur SON compromis quand il n'en a pas (compromis du 24/01/2025)"),
    ("U0GQ3KTO", 3713, 4385, "POSER", "sa regle : la date du Sheet sur SON compromis quand il n'en a pas (compromis sans date chez Hektor)"),
    ("IEYXREWQ", 3530, 27134, "POSER", "sa regle : la date du Sheet sur SON compromis quand il n'en a pas (compromis sans date chez Hektor)"),
    ("R0JRVFDC", 4014, 16377, "POSER", "sa regle : la date du Sheet sur SON compromis quand il n'en a pas (compromis du 27/10/2020)"),
    ("S3HOG6UL", 3864, 17387, "NOMMEE", "ECARTEE : la date du Sheet (21/10/2021) est ANTERIEURE au compromis (03/11/2021) -- sa decision du 24/11, comme les 106 de C3"),
    ("6U5DQQ4J", 3865, 24450, "NOMMEE", "ECARTEE : la date du Sheet (21/10/2021) est ANTERIEURE au compromis (28/10/2021) -- sa decision du 24/11, comme les 106 de C3"),
    ("T2GZOY5O", 3856, 20073, "NOMMEE", "EN RESERVE : jumelle de O6R10ZQA (meme affaire, mandat 4369) ; O6R10ZQA est la bonne et sa date 21/09/2021 est DEJA sur 20073 -- sa decision du 24/11"),
]
for i, num, piece, geste, _p in LIGNES:
    assert D.case(i, "Annulée").strip(), i
VAL = {i: iso(D.case(i, "Annulée").strip()) for i, *_r in LIGNES}
POSER = [x for x in LIGNES if x[3] == "POSER"]
ids_poser = ", ".join(str(x[2]) for x in POSER)
ids_tous = ", ".join(str(x[2]) for x in LIGNES)

cn, cu = P.pooler()
cu.execute("select app_affaire_id, kind, state, date_annulation_app from public.app_affaire_ledger where app_affaire_id in (%s) "
           "order by app_affaire_id" % ids_tous)
etat = {r[0]: r[1:] for r in cu.fetchall()}
EMP = ("md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, coalesce(date_annulation_app, '-'), "
       "coalesce(motif_annulation_app, '-'), coalesce(vente_reglee_app, '-'), coalesce(numero_facture_app, '-'), "
       "coalesce(honoraires_entree_app::text, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where "
       "app_affaire_id in (%s)" % ids_tous)
cu.execute("select " + EMP)
e_avant = cu.fetchone()[0]
cn.rollback()
cn.close()
print("l'etat du jour :", etat)
for i, num, piece, geste, _p in POSER:
    assert etat[piece] == ("compromis", "cancelled", None), (i, piece, etat[piece])
print("LE COMPTE : %d date(s) a poser (%s) ; %d nommee(s), rien ecrit (%s)" % (
    len(POSER), ", ".join("%s -> %d le %s" % (x[0], x[2], VAL[x[0]]) for x in POSER), len(LIGNES) - len(POSER),
    ", ".join(x[0] for x in LIGNES if x[3] == "NOMMEE")))
q = lambda s: "'" + str(s).replace("'", "''") + "'"
valeurs = ",\n    ".join("(%d, %s, %d, %d, %s, %s, %s)" % (k, q(i), num, piece, q(VAL[i]), q("POSER (case vide)" if g == "POSER"
                                                                                           else "NOMMEE -- rien ecrit"), q(p))
                         for k, (i, num, piece, g, p) in enumerate(LIGNES, 1))
D_ = {"lot": LOT, "tab": TAB, "ids_poser": ids_poser, "ids_tous": ids_tous, "n": len(POSER), "nl": len(LIGNES), "emp": EMP,
      "e_avant": e_avant, "valeurs": valeurs}
CORPS = """
do $$
declare n int; e text;
begin
  if to_regclass('public.%(tab)s') is not null then raise exception '⛔ garde : la sauvegarde existe deja'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s';
  if n <> 0 then raise exception '⛔ garde : %% ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_affaire_ledger where app_affaire_id in (%(ids_poser)s) and kind = 'compromis'
     and state = 'cancelled' and date_annulation_app is null;
  if n <> %(n)s then raise exception '⛔ garde : %% compromis annule(s) SANS DATE sur %(n)s', n; end if;
  e := (select %(emp)s);
  if e <> '%(e_avant)s' then raise exception '⛔ garde : les 7 lignes ont change depuis la fabrication (%%)', e; end if;
  raise notice '✅ gardes : %(n)s compromis annules sans date ; les 7 lignes telles que lues';
end $$;
create table public.%(tab)s as select * from public.app_affaire_ledger where app_affaire_id in (%(ids_tous)s);
revoke all on public.%(tab)s from public, anon, authenticated;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select '%(lot)s', v.n, 'date_annulation_app', 'date_annulation_app', v.geste, v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero,
       d.app_dossier_uuid, v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero, v.valeur, coalesce(d.date_annulation_app, 'VIDE'),
       v.ligne, v.num, 'Sheet du 25/11 (image 2026-11-25_072625, colonne Annulee) -- son mot du 25/11', v.pourquoi,
       'patch_dates_annulation'
  from (values
    %(valeurs)s
  ) v(n, ligne, num, piece, valeur, geste, pourquoi)
  join public.app_affaire_ledger d on d.app_affaire_id = v.piece;
update public.app_affaire_ledger l set date_annulation_app = j.valeur
  from public.app_classeur_realignement_journal j
 where j.lot = '%(lot)s' and j.geste = 'POSER (case vide)' and l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app is null;
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_classeur_realignement_journal j join public.app_affaire_ledger l
    on l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app = j.valeur
   where j.lot = '%(lot)s' and j.geste = 'POSER (case vide)' and j.ligne_origine is not null;
  if n <> %(n)s then raise exception '⛔ controle : %% date(s) posee(s) sur %(n)s', n; end if;
  -- les NOMMEES n'ont pas bouge, et aucune autre colonne des 7 lignes non plus
  select count(*) into n from public.app_affaire_ledger l join public.%(tab)s s using (app_affaire_id)
   where (l.app_affaire_id not in (%(ids_poser)s) and l.date_annulation_app is distinct from s.date_annulation_app)
      or (l.motif_annulation_app, l.vente_reglee_app, l.numero_facture_app, l.honoraires_entree_app, l.kind, l.state, l.app_chaine_id)
         is distinct from (s.motif_annulation_app, s.vente_reglee_app, s.numero_facture_app, s.honoraires_entree_app, s.kind, s.state,
                           s.app_chaine_id);
  if n <> 0 then raise exception '⛔ controle : %% ligne(s) ont bouge hors de leur date', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s';
  if n <> %(nl)s then raise exception '⛔ controle : %% ligne(s) au journal sur %(nl)s', n; end if;
  e := (select %(emp)s);
  %(apres)s
  raise notice '✅ %(n)s dates posees sur leur compromis (et %(nl)s lignes au journal, 3 nommees) ; empreinte apres %%', e;
end $$;
"""
INVERSE = """
update public.app_affaire_ledger l set date_annulation_app = null
  from public.app_classeur_realignement_journal j
 where j.lot = '%(lot)s' and j.geste = 'POSER (case vide)' and l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app = j.valeur;
delete from public.app_classeur_realignement_journal where lot = '%(lot)s';
do $$
begin
  if (select count(*) from public.app_affaire_ledger l join public.%(tab)s s using (app_affaire_id)
       where l.date_annulation_app is distinct from s.date_annulation_app) <> 0 then
    raise exception '⛔ inverse : les dates ne sont pas revenues a la sauvegarde'; end if;
  if (select %(emp)s) <> '%(e_avant)s' then raise exception '⛔ inverse : l''empreinte n''est pas celle d''avant'; end if;
  raise notice '✅ inverse : les 4 dates retirees, le journal du lot vide, l''empreinte d''avant revenue';
end $$;
"""
reel = ("if e <> '%s' then raise exception '⛔ controle : empreinte apres %% au lieu de %s', e; end if;" % (
    arg.empreinte_apres, arg.empreinte_apres) if arg.empreinte_apres else
    "raise exception '⛔ le patch reel exige l''empreinte d''apres rendue par l''essai a blanc (--empreinte-apres)';")
ent = "-- %s -- genere par phase2/checks/dates_annulation_generer_patch_2026-11-25.py (son mot du 25/11)\n"
F = {
    "patch_dates_annulation_2026-11-25.sql": ent % "patch_dates_annulation_2026-11-25" + "\nbegin;\n" + CORPS % dict(D_, apres=reel)
    + "\ncommit;\n",
    "patch_dates_annulation_2026-11-25_A_BLANC.sql": ent % "A BLANC -- aucun commit, une erreur VOULUE annule tout" + "\nbegin;\n"
    + CORPS % dict(D_, apres="null;") + "\ncreate temporary table d_milieu on commit drop as select (select %s) e, (select string_agg("
    "app_affaire_id || '=' || coalesce(date_annulation_app, '-'), ' ' order by app_affaire_id) from public.app_affaire_ledger where "
    "app_affaire_id in (%s)) d;\n" % (EMP, ids_tous) + INVERSE % D_ + """
do $$
declare m record;
begin
  select * into m from d_milieu;
  raise exception 'A BLANC DATES VERT -- RIEN N''EST ECRIT. Apres le geste : %%, empreinte apres %%. Apres l''inverse : = avant (%s).', m.d, m.e;
end $$;
""" % e_avant[:8],
    "patch_dates_annulation_2026-11-25_INVERSE.sql": ent % "INVERSE" + "\nbegin;\n" + INVERSE % D_ + "\ncommit;\n",
    "patch_dates_annulation_2026-11-25_REPETITION.sql": ent % "REPETITION (lecture seule)" + (
        "select (select string_agg(app_affaire_id || '=' || coalesce(date_annulation_app, '-'), ' ' order by app_affaire_id) from "
        "public.app_affaire_ledger where app_affaire_id in (%s)) as les_7_compromis,\n"
        "  (select count(*) from public.app_classeur_realignement_journal where lot = '%s') as journal_attendu_%d,\n"
        "  (select %s) as empreinte_apres;\n" % (ids_tous, LOT, len(LIGNES), EMP)),
}
for nom, txt in F.items():
    p_ = OUT / nom
    p_.write_text(txt, encoding="utf-8")
    print("-> supabase/%s (%d octets, md5 %s)" % (nom, p_.stat().st_size, hashlib.md5(p_.read_bytes()).hexdigest()[:8]))
print("empreinte d'avant : %s" % e_avant)
