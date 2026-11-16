#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C3 -- GENERE LE PATCH DES 450 DATES D'ANNULATION.                 16/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\c3_generer_patch_dates_annulation_2026-11-16.py

⛔ CE SCRIPT N'ECRIT RIEN EN BASE. Il lit la mesure et il GENERE trois fichiers SQL :
     supabase/patch_c3_dates_annulation_2026-11-16.sql             le patch
     supabase/patch_c3_dates_annulation_2026-11-16_INVERSE.sql     le retour arriere
     supabase/patch_c3_dates_annulation_2026-11-16_REPETITION.sql  les controles

⭐⭐⭐ LA REGLE, DE FREDERIC, 16/11/2026 :
    « La date d'annulation dans le Sheet represente la date d'annulation du
      COMPROMIS. »
  Et son perimetre, le meme jour : « 450 » -- les cas ou un SEUL compromis annule
  porte la ligne, ou sa date est coherente avec la notre, et ou rien n'est deja pose.

CE QUE LE PATCH NE FAIT PAS, ET C'EST VOULU :
  . il ne touche AUCUNE offre (pour une offre refusee, `date` porte DEJA la date du
    refus -- regle du 12/11 : une colonne d'annulation y serait un doublon) ;
  . il ne touche AUCUNE vente (0 des 9 281 ventes n'a d'etat : une vente ne
    s'annule pas, elle disparait) ;
  . il n'ecrit RIEN chez Hektor -- `date_annulation_app` est « A NOUS » (commentaire
    de la colonne 46) et figure dans COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS depuis le
    10/11, donc le push ne l'enverra pas non plus ;
  . il ne reveille PAS la cascade : `cascade_annulation_compromis` vit dans
    `app_geste_affaire_optimistic`, appelee par L'ECRAN, et il n'existe aucun
    declencheur de cascade sur la table (mesure du 16/11).

LES GARDES SONT DANS LE `WHERE`, PAS DANS MA CONFIANCE : chaque ligne n'est posee
que si elle est TOUJOURS un compromis `cancelled` ET TOUJOURS sans date. Si l'etat a
bouge depuis la mesure, la ligne n'est pas touchee -- et le controle d'apres le DIT,
parce qu'il exige le compte exact.
"""
from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
MESURE = RACINE / "notice" / "C3_OU_SE_POSENT_LES_DATES_ANNULATION_2026-11-16.csv"
BASE = RACINE / "supabase" / "patch_c3_dates_annulation_2026-11-16"
MARQUE = "c3_dates_annulation_2026_11_16"


def main() -> int:
    with MESURE.open(encoding="utf-8-sig", newline="") as h:
        mesure = list(csv.DictReader(h, delimiter=";"))
    lignes = []
    for x in mesure:
        if x["verdict"] != "nette":
            continue
        aff, d = str(x["app_affaire_id"]).strip(), str(x["date_annulation_classeur"]).strip()
        if not re.match(r"^\d+$", aff) or not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            raise SystemExit("⛔ ligne illisible dans la mesure : %r / %r" % (aff, d))
        if str(x["type"]) != "compromis" or str(x["etat"]) != "cancelled":
            raise SystemExit("⛔ une ligne « nette » n'est pas un compromis annule : %r" % x)
        lignes.append((int(aff), d, x["id_unique"], x["annonce"]))

    if len(lignes) != len({a for a, _d, _i, _n in lignes}):
        raise SystemExit("⛔ un app_affaire_id apparait DEUX FOIS -- on ne pose rien.")
    n = len(lignes)
    print("lignes retenues : %d" % n)
    if n < 400 or n > 500:
        raise SystemExit("⛔ %d lignes, hors de la fourchette attendue (450). ARRET." % n)

    annees = {}
    for _a, d, _i, _nn in lignes:
        annees[d[:4]] = annees.get(d[:4], 0) + 1
    print("   par annee : %s" % dict(sorted(annees.items())))

    valeurs = ",\n    ".join("(%d, '%s')" % (a, d) for a, d, _i, _nn in sorted(lignes))
    ids = ", ".join(str(a) for a, _d, _i, _nn in sorted(lignes))

    # ─── LE PATCH ────────────────────────────────────────────────────────────
    patch = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C3 -- LES {n} DATES D'ANNULATION DU CLASSEUR (colonne Z) SUR LEUR COMPROMIS
-- Genere le {date.today().isoformat()} par phase2/checks/c3_generer_patch_dates_annulation_2026-11-16.py
--
-- LA REGLE, DE FREDERIC le 16/11/2026 :
--   « La date d'annulation dans le Sheet represente la date d'annulation du
--     COMPROMIS. »   Perimetre arrete par lui le meme jour : {n}.
--
-- CE QU'ON POSE : public.app_affaire_ledger.date_annulation_app, et RIEN d'autre.
--   Colonne de CLASSE A, « A NOUS » (son propre commentaire), en TEXT -- pas en
--   `date`, parce que Hektor met 0000-00-00 dans la colonne `date` voisine et
--   qu'une colonne `date` ferait tomber le run.
--
-- ⛔ CE QUE CE PATCH NE FAIT PAS :
--   . aucune offre touchee -- pour une offre refusee, `date` porte DEJA la date du
--     refus (regle du 12/11) : une date d'annulation y serait un doublon ;
--   . aucune vente touchee -- 0 des 9 281 ventes n'a d'etat : une vente ne
--     s'annule pas, elle DISPARAIT ;
--   . RIEN ne part chez Hektor : la colonne est dans
--     COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS (phase2/sync/affaire_ledger.py) depuis le
--     10/11, donc AVANT tout remplissage -- lecon du 07/09 ;
--   . la cascade `cascade_annulation_compromis` n'est PAS reveillee : elle vit dans
--     `app_geste_affaire_optimistic`, que seul L'ECRAN appelle, et il n'existe
--     aucun declencheur de cascade sur la table (mesure du 16/11).
--
-- ⚠ CE QUE CE PATCH REND VISIBLE, ET QUI RESTE A FAIRE : l'app ne demande AUCUNE
--   date quand on annule un compromis (`app_geste_affaire_optimistic` prend
--   target_affaire_id, geste, job_priority -- et son corps n'ecrit ni la date ni le
--   motif). L'historique sera donc juste, et le PRESENT muet, jusqu'a ce que la
--   saisie soit branchee. C'est un chantier a part, decide le 16/11.
--
-- LES GARDES SONT DANS LE `WHERE` : une ligne n'est posee que si elle est TOUJOURS
--   un compromis `cancelled` et TOUJOURS sans date. Si un etat a bouge depuis la
--   mesure, la ligne est laissee -- et le controle 4 ARRETE TOUT, parce qu'il exige
--   le compte exact.
--
-- Retour arriere : patch_c3_dates_annulation_2026-11-16_INVERSE.sql
-- Controle       : patch_c3_dates_annulation_2026-11-16_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

begin;

-- ─── 1. L'ETAT D'AVANT, EXIGE ──────────────────────────────────────────────
do $$
declare
  deja  integer;
  cibles integer;
begin
  select count(*) into deja from public.app_affaire_ledger
   where date_annulation_app is not null;
  if deja <> 0 then
    raise exception '⛔ ARRET : % date(s) d''annulation sont DEJA posees. Ce patch '
      'suppose une colonne vierge (0 au 16/11). Relire avant de jouer.', deja;
  end if;

  select count(*) into cibles from public.app_affaire_ledger
   where app_affaire_id in ({ids})
     and kind = 'compromis' and state = 'cancelled';
  if cibles <> {n} then
    raise exception '⛔ ARRET : % compromis annules retrouves sur les {n} attendus. '
      'Un etat a bouge depuis la mesure du 16/11.', cibles;
  end if;
  raise notice '✅ etat d''avant : 0 date posee, {n} compromis annules retrouves.';
end $$;

-- ─── 2. LA SAUVEGARDE DATEE ────────────────────────────────────────────────
-- ⭐ Elle ne sert pas a « revenir » (l'INVERSE le fait) : elle sert a PROUVER
--   l'etat d'avant si une question se pose dans six mois.
create table if not exists public.app_affaire_avant_c3_dates_20261116 as
  select app_affaire_id, app_chaine_id, hektor_annonce_id, kind, state, date,
         date_annulation_app, now() as photographie_le
    from public.app_affaire_ledger
   where app_affaire_id in ({ids});

-- ─── 3. LA POSE ────────────────────────────────────────────────────────────
with poser(app_affaire_id, jour) as (values
    {valeurs}
)
update public.app_affaire_ledger l
   set date_annulation_app = p.jour
  from poser p
 where l.app_affaire_id = p.app_affaire_id
   and l.kind = 'compromis'
   and l.state = 'cancelled'
   and l.date_annulation_app is null;

-- ─── 4. LES CONTROLES, ET ILS ARRETENT ─────────────────────────────────────
do $$
declare
  posees      integer;
  ailleurs    integer;
  mauvais     integer;
  sauvegarde  integer;
  offres      integer;
  ventes      integer;
begin
  -- 4a le compte EXACT
  select count(*) into posees from public.app_affaire_ledger
   where app_affaire_id in ({ids}) and date_annulation_app is not null;
  if posees <> {n} then
    raise exception '⛔ {n} attendues, % posees.', posees;
  end if;

  -- 4b LE TEMOIN INVERSE : personne d'autre n'a bouge
  select count(*) into ailleurs from public.app_affaire_ledger
   where date_annulation_app is not null
     and app_affaire_id not in ({ids});
  if ailleurs <> 0 then
    raise exception '⛔ % ligne(s) HORS du lot portent une date. Le patch a debordé.', ailleurs;
  end if;

  -- 4c aucune date mal formee, aucune date future
  select count(*) into mauvais from public.app_affaire_ledger
   where date_annulation_app is not null
     and (date_annulation_app !~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}$'
          or date_annulation_app > to_char(now(), 'YYYY-MM-DD'));
  if mauvais <> 0 then
    raise exception '⛔ % date(s) mal formee(s) ou dans le futur.', mauvais;
  end if;

  -- 4d NI UNE OFFRE NI UNE VENTE n'a recu de date
  select count(*) into offres from public.app_affaire_ledger
   where date_annulation_app is not null and kind <> 'compromis';
  if offres <> 0 then
    raise exception '⛔ % transaction(s) qui ne sont pas des compromis ont une date.', offres;
  end if;

  -- 4e tout ce qui porte une date est bien ANNULE
  select count(*) into ventes from public.app_affaire_ledger
   where date_annulation_app is not null and state <> 'cancelled';
  if ventes <> 0 then
    raise exception '⛔ % ligne(s) datee(s) ne sont pas `cancelled`.', ventes;
  end if;

  -- 4f la sauvegarde est complete
  select count(*) into sauvegarde from public.app_affaire_avant_c3_dates_20261116;
  if sauvegarde <> {n} then
    raise exception '⛔ la sauvegarde porte % lignes sur {n}.', sauvegarde;
  end if;

  raise notice '✅ {n} dates posees . 0 hors du lot . 0 mal formee . 0 non-compromis '
    '. 0 non-annulee . sauvegarde {n}.';
end $$;

commit;

-- ⛔ APRES LE COLLAGE : jouer la REPETITION. Elle rejoue les memes controles, plus
--   ceux que le patch ne pouvait pas faire sur lui-meme (les voisines du registre).
"""

    # ─── L'INVERSE ───────────────────────────────────────────────────────────
    inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C3 -- RETOUR ARRIERE DES {n} DATES D'ANNULATION
-- ⭐ « Un retour arriere ne juge que SA part » (lecon 31) : il verifie d'abord
--   qu'il ne reste aucune trace de ce qu'il devait retirer, et il NE TOUCHE RIEN
--   d'autre que les {n} numeros de ce lot.
--
-- ⛔ IL REFUSE DE SE JOUER si une de ces dates a ete MODIFIEE depuis la pose --
--   parce qu'alors ce n'est plus notre valeur, c'est celle d'un humain ou d'un
--   geste de l'app, et l'effacer serait perdre une saisie. Meme protection que
--   l'inverse de B1.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

do $$
declare
  changees integer;
begin
  with attendu(app_affaire_id, jour) as (values
      {valeurs}
  )
  select count(*) into changees
    from attendu a
    join public.app_affaire_ledger l using (app_affaire_id)
   where coalesce(l.date_annulation_app, '') <> a.jour;
  if changees <> 0 then
    raise exception '⛔ ARRET : % ligne(s) ne portent plus la valeur posee par C3. '
      'Quelqu''un est passe apres nous -- ne RIEN effacer sans relire.', changees;
  end if;
  raise notice '✅ les {n} lignes portent bien la valeur de C3 : le retrait est sur.';
end $$;

update public.app_affaire_ledger
   set date_annulation_app = null
 where app_affaire_id in ({ids})
   and date_annulation_app is not null;

do $$
declare
  reste    integer;
  ailleurs integer;
begin
  select count(*) into reste from public.app_affaire_ledger
   where app_affaire_id in ({ids}) and date_annulation_app is not null;
  if reste <> 0 then
    raise exception '⛔ il reste % date(s) du lot.', reste;
  end if;
  -- ⭐ SA PART, ET SEULEMENT SA PART : la colonne doit revenir a son etat du 16/11,
  --   c'est-a-dire VIDE PARTOUT -- mais on le dit, on ne l'exige pas, parce qu'une
  --   saisie faite dans l'app entre-temps aurait parfaitement le droit d'etre la.
  select count(*) into ailleurs from public.app_affaire_ledger
   where date_annulation_app is not null;
  raise notice '✅ {n} dates retirees . il reste % date(s) dans la table, posee(s) '
    'par autre chose que C3 (0 attendu au 16/11).', ailleurs;
end $$;

-- ⚠ La sauvegarde n'est PAS supprimee : elle prouve l'etat d'avant.
--   Pour la retirer, une fois la question close :
--     drop table if exists public.app_affaire_avant_c3_dates_20261116;

commit;
"""

    # ─── LA REPETITION ───────────────────────────────────────────────────────
    repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C3 -- LES CONTROLES, REJOUABLES. Aucune ecriture.
-- ⭐ Ecrite AVANT le collage du patch, comme le projet l'exige.
-- ═══════════════════════════════════════════════════════════════════════════

select 'les {n} dates sont posees' as controle,
       count(*)::text as mesure, '{n}' as attendu
  from public.app_affaire_ledger
 where app_affaire_id in ({ids}) and date_annulation_app is not null
union all
select 'AUCUNE date hors du lot (temoin inverse)',
       count(*)::text, '0'
  from public.app_affaire_ledger
 where date_annulation_app is not null and app_affaire_id not in ({ids})
union all
select 'toutes sur un COMPROMIS',
       count(*)::text, '0'
  from public.app_affaire_ledger
 where date_annulation_app is not null and kind <> 'compromis'
union all
select 'toutes sur un compromis ANNULE',
       count(*)::text, '0'
  from public.app_affaire_ledger
 where date_annulation_app is not null and state <> 'cancelled'
union all
select 'aucune date mal formee ni future',
       count(*)::text, '0'
  from public.app_affaire_ledger
 where date_annulation_app is not null
   and (date_annulation_app !~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}$'
        or date_annulation_app > to_char(now(), 'YYYY-MM-DD'))
union all
select 'aucune date ANTERIEURE a la date du compromis',
       count(*)::text, '0'
  from public.app_affaire_ledger
 where date_annulation_app is not null
   and date ~ '^[0-9]{{4}}-' and date not like '0000%'
   and date_annulation_app < left(date, 10)
union all
select 'la sauvegarde porte le lot entier',
       count(*)::text, '{n}'
  from public.app_affaire_avant_c3_dates_20261116
union all
-- ⭐⭐ LES VOISINES : le patch ne pouvait pas se juger lui-meme sur ce point.
select 'voisines INTACTES -- transactions au total',
       count(*)::text, '31352 au 16/11'
  from public.app_affaire_ledger
union all
select 'voisines INTACTES -- compromis annules au total',
       count(*)::text, '1425 au 16/11'
  from public.app_affaire_ledger
 where kind = 'compromis' and state = 'cancelled'
union all
select 'voisines INTACTES -- aucun motif pose par erreur',
       count(*)::text, '0'
  from public.app_affaire_ledger
 where motif_annulation_app is not null
union all
-- ⭐ LE TEMOIN POSITIF : les dates doivent se repartir sur PLUSIEURS annees.
--   Un lot entier sur une seule annee signalerait une erreur de lecture.
select 'annees distinctes couvertes',
       count(distinct left(date_annulation_app, 4))::text, '7 (2020 a 2026)'
  from public.app_affaire_ledger
 where date_annulation_app is not null
order by 1;
"""

    for suffixe, contenu in ((".sql", patch), ("_INVERSE.sql", inverse),
                             ("_REPETITION.sql", repetition)):
        f = Path(str(BASE) + suffixe)
        f.write_bytes(contenu.encode("utf-8"))
        print("ecrit : %-62s %7d octets" % (f.name, len(f.read_bytes())))

    print()
    print("⛔ RIEN N'A ETE JOUE. Ces trois fichiers attendent un « colle ».")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
