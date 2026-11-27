"""LES 47 (+2), FAMILLE 3 : LES 23 DATES D'ANNULATION POSABLES -- LE PATCH, SON A BLANC, SON INVERSE, SA REPETITION (27/11).

SON MOT DU 27/11 : « Fini ce qui etait prevu », puis « Fais les deux » (familles 2 et 3). SA REGLE (24-25/11) : la date du
Sheet sur SON compromis quand il n'en a pas ; les dates anterieures au compromis restent ecartees.

LA MESURE DU 27/11 (notice/CLASSEUR_LES_47_VALEURS_JAMAIS_POSEES_2026-11-27_PASSAGE_82.csv) : 23 dates « POSABLE par sa
regle » ; 3 anterieures (LKBO1TOH, 87QOXR64, 8NZ6V6XB), 2 deja ecartees par lui (S3HOG6UL, 6U5DQQ4J) et O6R10ZQA (son double
PAOLONE) NE SONT PAS dans ce patch.

⚠ LE JUGE LIT date_annulation_app (R27 ② : « la date d'annulation deja posee sur le compromis du dossier ») -- R27 ne joue
que sur deux lignes d'un meme dossier avec le meme Mandat, le meme Acquereur et la meme Commission TTC. Mesure du 27/11 sur
les 4 805 lignes de l'image du 82 : AUCUNE des 23 n'a une telle jumelle -- la poser ne nourrit pas sa preuve. Le generateur
le REMESURE et refuse s'il en trouve une.

LA VALEUR : la case « Annulée » de l'image du 82, au format ISO (comme le geste du 25/11), EXIGEE identique dans le Sheet du
jour (un GET). LE GESTE : seulement sur une case VIDE d'un compromis annule ; la sauvegarde datee des 23 lignes (cle
primaire, RLS) ; le journal (la ligne d'origine et son numero) ; les autres colonnes INTACTES ; l'empreinte d'apres exigee.
USAGE : python -X utf8 phase2/checks/dates_annulation_famille3_generer_patch_2026-11-27.py [--empreinte-apres MD5]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
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

ap = argparse.ArgumentParser()
ap.add_argument("--empreinte-apres", default="")
arg = ap.parse_args()
LOT, TAB = "dates_annulation_famille3_2026-11-27", "app_affaire_ledger_avant_dates_f3_20261127"
OUT = RACINE / "supabase"
MESURE = RACINE / "notice" / "CLASSEUR_LES_47_VALEURS_JAMAIS_POSEES_2026-11-27_PASSAGE_82.csv"
IMAGE = "2026-11-26_094931"
REGLE = "sa regle : la date du Sheet sur SON compromis quand il n'en a pas"

# ─── 1. LA MESURE DU JOUR, et le verdict du 82 : chaque piece est celle de sa ligne tranchee ──────────────────────────
with MESURE.open(encoding="utf-8") as h:
    m = [r for r in csv.DictReader(h, delimiter=";") if r["quoi"] == "DATE_ANNULATION"]
posables = [r for r in m if r["verdict"].startswith("POSABLE")]
assert len(posables) == 23, len(posables)
con = sqlite3.connect("file:%s?mode=ro" % (P.DOSSIER / "socle.sqlite").as_posix(), uri=True)
V = {i: (v, json.loads(ps) if ps else []) for i, v, ps in con.execute("select id_unique, verdict, pieces from verdict where passage=82")}
con.close()
LIGNES = sorted(((r["id_unique"], int(r["ligne"]), int(r["piece"])) for r in posables), key=lambda x: x[1])
for i, num, piece in LIGNES:
    assert V[i][0] == "TRANCHEE" and piece in V[i][1], (i, V.get(i))

# ─── 2. LES VALEURS : l'image du 82, le Sheet du jour identique ; R27 remesuree ─────────────────────────────────────────
I = P.Image(P.IMAGES / IMAGE)
D = I.D
BRUT = {i: D.case(i, "Annulée").strip() for i, _n, _p in LIGNES}
for i, b in BRUT.items():
    assert re.fullmatch(r"\d{2}/\d{2}/\d{4}", b), (i, b)
VAL = {i: "%s-%s-%s" % (b[6:10], b[3:5], b[0:2]) for i, b in BRUT.items()}
sheet = json.loads((P.IMAGES / IMAGE / "sheet.json").read_text(encoding="utf-8"))
cle = {}
for j in sheet["par_id"]:
    cle[j] = (D.case(j, "Mandat").strip(), frozenset(P.noms_texte(D.case(j, "Acquéreur"))),
              P.nombre_case(D.case(j, "Commission TTC")))
par_cle = defaultdict(list)
for j, k in cle.items():
    if k[0] and k[1] and k[2] is not None:
        par_cle[k].append(j)
jumelles = {i: [j for j in par_cle.get(cle[i], []) if j != i] for i, _n, _p in LIGNES}
assert not any(jumelles.values()), {i: j for i, j in jumelles.items() if j}
print("R27 : aucune des 23 n'a de jumelle (meme Mandat, Acquereur, Commission) sur les %d lignes de l'image" % len(cle))
import apparier_classeur as ac  # noqa: E402

ac.load_env_file(RACINE / ".env")
entete, lignes = ac.lire_classeur()
kA, kE = entete.index("Annulée"), entete.index("Etat Actuel")
du_jour = defaultdict(list)
for num, l in lignes:
    l = [("" if x is None else str(x)) for x in list(l)] + [""] * 40
    if l[37].strip() in BRUT:
        du_jour[l[37].strip()].append((num, l[kA].strip(), l[kE].strip()))
for i, num, piece in LIGNES:
    assert len(du_jour[i]) == 1 and du_jour[i][0][:2] == (num, BRUT[i]), (i, du_jour[i], num, BRUT[i])
print("les 23 valeurs : l'image du 82 = le Sheet du jour, ligne comprise (etats du jour : %s)" % sorted(
    {du_jour[i][0][2] for i in BRUT}))

# ─── 3. SUPABASE, LECTURE SEULE : l'etat exact que les gardes exigeront ───────────────────────────────────────────────
ids = ", ".join(str(p) for _i, _n, p in LIGNES)
EMP = ("md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, app_chaine_id, app_dossier_numero, "
       "coalesce(date_annulation_app, '-'), coalesce(motif_annulation_app, '-'), coalesce(vente_reglee_app, '-'), "
       "coalesce(numero_facture_app, '-'), coalesce(honoraires_entree_app::text, '-')), ';' order by app_affaire_id), '')) "
       "from public.app_affaire_ledger where app_affaire_id in (%s)" % ids)
N_DA = "(select count(*) from public.app_affaire_ledger where coalesce(date_annulation_app, '') <> '')"
cn, cu = P.pooler()
cu.execute("select app_affaire_id, kind, state, coalesce(date_annulation_app, ''), date::text from public.app_affaire_ledger "
           "where app_affaire_id in (%s)" % ids)
etat = {r[0]: r[1:] for r in cu.fetchall()}
cu.execute("select %s, (select %s)" % (N_DA, EMP))
n_da, e_avant = cu.fetchone()
cu.execute("select count(*) from public.app_classeur_realignement_journal where lot = %s", (LOT,))
au_journal = cu.fetchone()[0]
cu.execute("select to_regclass(%s) is not null", ("public." + TAB,))
tab_existe = cu.fetchone()[0]
cn.rollback()
cn.close()
for i, num, piece in LIGNES:
    kind, st, da, dcomp = etat[piece]
    assert (kind, st, da) == ("compromis", "cancelled", ""), (i, piece, etat[piece])
    assert not dcomp or dcomp[:10] <= VAL[i], (i, dcomp, VAL[i])       # sa regle : jamais AVANT le compromis
assert au_journal == 0 and not tab_existe, (au_journal, tab_existe)
for i, num, piece in LIGNES:
    print("  %-9s ligne %-5d compromis %-6d annulee %s -> %s (compromis du %s)" % (i, num, piece, BRUT[i], VAL[i],
                                                                                    etat[piece][3] or "-"))
print("registre : %d dates d'annulation posees ; 23 lignes %s" % (n_da, e_avant))


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


VALEURS = ",\n    ".join("(%d, %s, %d, %d, %s, %s)" % (k, q(i), num, piece, q(VAL[i]), q(
    "SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- %s ; Sheet « %s » ; aucune jumelle de R27" % (
        REGLE, BRUT[i]))) for k, (i, num, piece) in enumerate(LIGNES, 1))
D_ = {"lot": LOT, "tab": TAB, "ids": ids, "emp": EMP, "e_avant": e_avant, "valeurs": VALEURS, "n_da": n_da, "image": IMAGE}
CORPS = """
-- ─── ① LES GARDES : 23 compromis annules SANS date, tels que lus ────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.%(tab)s') is not null then raise exception '⛔ garde : la sauvegarde existe deja -- ce patch ne se rejoue pas'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s';
  if n <> 0 then raise exception '⛔ garde : %% ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_affaire_ledger where app_affaire_id in (%(ids)s) and kind = 'compromis'
     and state = 'cancelled' and coalesce(date_annulation_app, '') = '';
  if n <> 23 then raise exception '⛔ garde : %% compromis annule(s) SANS date sur 23', n; end if;
  e := (select %(emp)s);
  if e <> '%(e_avant)s' then raise exception '⛔ garde : les 23 lignes ont change depuis la fabrication (%%)', e; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(date_annulation_app, '') <> '') <> %(n_da)s then
    raise exception '⛔ garde : le nombre de dates d''annulation a change depuis la fabrication'; end if;
  raise notice '✅ gardes : 23 compromis annules sans date, tels que lus';
end $$;

-- ─── ② LA SAUVEGARDE DATEE des 23 lignes, AVEC la cle primaire et la RLS ──────────────────────────────────────────────
create table public.%(tab)s as select * from public.app_affaire_ledger where app_affaire_id in (%(ids)s);
alter table public.%(tab)s add primary key (app_affaire_id);
revoke all on public.%(tab)s from public, anon, authenticated;
alter table public.%(tab)s enable row level security;

-- ─── ③ LE JOURNAL : chaque date, sa ligne d'origine et son numero ──────────────────────────────────────────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select '%(lot)s', v.n, 'date_annulation_app', 'date_annulation_app', 'POSER (case vide)', v.piece, d.kind, d.app_chaine_id,
       d.app_dossier_numero, d.app_dossier_uuid, v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero, v.valeur, 'VIDE',
       v.ligne, v.num, 'Sheet, image %(image)s (passage 82, colonne Annulee) = le Sheet du 27/11', v.pourquoi,
       'patch_dates_annulation_famille3'
  from (values
    %(valeurs)s
  ) v(n, ligne, num, piece, valeur, pourquoi)
  join public.app_affaire_ledger d on d.app_affaire_id = v.piece;

-- ─── ④ LE GESTE : seulement des cases VIDES ───────────────────────────────────────────────────────────────────────────
update public.app_affaire_ledger l set date_annulation_app = j.valeur
  from public.app_classeur_realignement_journal j
 where j.lot = '%(lot)s' and l.app_affaire_id = j.de_app_affaire_id and coalesce(l.date_annulation_app, '') = '';

-- ─── ⑤ LES CONTROLES ───────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_classeur_realignement_journal j join public.app_affaire_ledger l
    on l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app = j.valeur
   where j.lot = '%(lot)s' and j.ligne_origine is not null;
  if n <> 23 then raise exception '⛔ controle : %% date(s) posee(s) sur 23', n; end if;
  select count(*) into n from public.app_affaire_ledger l join public.%(tab)s s using (app_affaire_id)
   where (l.kind, l.state, l.app_chaine_id, l.app_dossier_numero, l.motif_annulation_app, l.vente_reglee_app,
          l.numero_facture_app, l.honoraires_entree_app, l.date)
         is distinct from (s.kind, s.state, s.app_chaine_id, s.app_dossier_numero, s.motif_annulation_app, s.vente_reglee_app,
                           s.numero_facture_app, s.honoraires_entree_app, s.date);
  if n <> 0 then raise exception '⛔ controle : %% ligne(s) ont bouge hors de leur date', n; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(date_annulation_app, '') <> '') <> %(n_da)s + 23 then
    raise exception '⛔ controle : le nombre de dates d''annulation n''est pas %(n_da)s + 23'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s';
  if n <> 23 then raise exception '⛔ controle : %% ligne(s) au journal sur 23', n; end if;
  e := (select %(emp)s);
  %(apres)s
  raise notice '✅ 23 dates posees sur leur compromis ; le reste des lignes intact ; empreinte apres %%', e;
end $$;
"""
INVERSE = """
-- ─── L'INVERSE : les 23 dates retirees (seulement si elles portent encore la valeur du lot), le journal retire ─────────
update public.app_affaire_ledger l set date_annulation_app = s.date_annulation_app
  from public.%(tab)s s, public.app_classeur_realignement_journal j
 where s.app_affaire_id = l.app_affaire_id and j.lot = '%(lot)s' and j.de_app_affaire_id = l.app_affaire_id
   and l.date_annulation_app = j.valeur;
delete from public.app_classeur_realignement_journal where lot = '%(lot)s';
do $$
begin
  -- l'inverse ne juge que SA part (lecon 31) : les 23 dates contre leur sauvegarde
  if (select count(*) from public.app_affaire_ledger l join public.%(tab)s s using (app_affaire_id)
       where l.date_annulation_app is distinct from s.date_annulation_app) <> 0 then
    raise exception '⛔ inverse : les 23 dates ne sont pas revenues a la sauvegarde'; end if;
  raise notice '✅ inverse : les 23 dates retirees, le journal du lot vide';
end $$;
"""
reel = ("if e <> '%s' then raise exception '⛔ controle : empreinte apres %% au lieu de %s', e; end if;" % (
    arg.empreinte_apres, arg.empreinte_apres) if arg.empreinte_apres else
    "raise exception '⛔ le patch reel exige l''empreinte d''apres rendue par l''essai a blanc (--empreinte-apres)';")
ent = "-- %s -- genere par phase2/checks/dates_annulation_famille3_generer_patch_2026-11-27.py (son mot du 27/11)\n"
DETAIL = ("(select string_agg(app_affaire_id || '=' || coalesce(date_annulation_app, '-'), ' ' order by app_affaire_id) "
          "from public.app_affaire_ledger where app_affaire_id in (%s))" % ids)
F = {
    "patch_dates_annulation_famille3_2026-11-27.sql": ent % "patch_dates_annulation_famille3_2026-11-27"
    + "-- Retour arriere : ..._INVERSE.sql . Controle : ..._REPETITION.sql\n\nbegin;\n" + CORPS % dict(D_, apres=reel)
    + "\ncommit;\n",
    "patch_dates_annulation_famille3_2026-11-27_A_BLANC.sql": ent % "A BLANC -- ⛔ aucun commit, une erreur VOULUE annule tout"
    + "\nbegin;\n" + CORPS % dict(D_, apres="null;")
    + "\ncreate temporary table d_milieu on commit drop as select (select %s) e, %s d, %s nda;\n" % (EMP, DETAIL, N_DA)
    + INVERSE % D_ + """
do $$
declare m record;
begin
  select * into m from d_milieu;
  if (select %(emp)s) <> '%(e_avant)s' then raise exception '⛔ A BLANC : apres l''inverse, les 23 lignes ne sont plus celles d''avant'; end if;
  raise exception 'A BLANC DATES F3 VERT -- RIEN N''EST ECRIT. Apres le geste : %%%% dates posees au registre ; %%%% ; empreinte apres %%%%. Apres l''inverse : = avant (%s).', m.nda, m.d, m.e;
end $$;
""".replace("%%%%", "%%").replace("%(emp)s", EMP).replace("%(e_avant)s", e_avant) % e_avant[:8],
    "patch_dates_annulation_famille3_2026-11-27_INVERSE.sql": ent % "INVERSE" + "\nbegin;\n" + INVERSE % D_ + "\ncommit;\n",
    "patch_dates_annulation_famille3_2026-11-27_REPETITION.sql": ent % "REPETITION (lecture seule)" + (
        "select %s as les_23_compromis,\n"
        "  (select count(*) from public.app_classeur_realignement_journal where lot = '%s') as journal_attendu_23,\n"
        "  %s as dates_posees_attendu_%d,\n  (select %s) as empreinte_apres;\n" % (DETAIL, LOT, N_DA, n_da + 23, EMP)),
}
for nom, txt in F.items():
    p_ = OUT / nom
    p_.write_bytes(txt.encode("utf-8"))
    print("-> supabase/%s (%d octets, md5 %s)" % (nom, p_.stat().st_size, hashlib.md5(p_.read_bytes()).hexdigest()[:8]))
print("empreinte d'avant des 23 lignes : %s ; dates posees %d" % (e_avant, n_da))
