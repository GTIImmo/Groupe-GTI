-- patch_a3_vague_2026-11-25 -- genere par phase2/checks/a1_a3_vague_generer_patch_2026-11-25.py
-- A1 et A3 de la vague du soir (passage 82, image 2026-11-25_072625). ⛔ Etape 7, apres A2, et SUR SON ACCORD.

begin;

-- ═══ A3 : LE REFLET DE CHAINE DES NOTES ET DES CONDITIONS, PAR LA TRANSACTION -- lot a3_vague_2026-11-25 ═════════════════
do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_note_reflets_avant_a3vague_20261125') is not null then
    raise exception '⛔ A3 G0 : la sauvegarde existe deja -- ce patch ne se rejoue pas'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'a3_vague_2026-11-25';
  if n <> 0 then raise exception '⛔ A3 G0 : % ligne(s) du lot deja au journal', n; end if;
  select count(*), md5(coalesce(string_agg(concat_ws('|', app_affaire_id, app_chaine_id), ';' order by app_affaire_id), '')) into n, e from public.app_affaire_note;
  if n <> 4524 or e <> '174ab8ac5e52d6b3910153299b82e2c5' then
    raise exception '⛔ A3 G1 : les notes ont change depuis la fabrication (% , %)', n, e; end if;
  select count(*), md5(coalesce(string_agg(concat_ws('|', app_affaire_id, rang, app_chaine_id), ';' order by app_affaire_id, rang), '')) into n, e from public.app_affaire_condition;
  if n <> 33 or e <> '1a303f39ab051366587a0c2fc936b5af' then
    raise exception '⛔ A3 G1 : les conditions ont change depuis la fabrication (% , %)', n, e; end if;
end $$;
create table public.app_affaire_note_reflets_avant_a3vague_20261125 as
  select app_affaire_id, app_chaine_id, now() as copie_le from public.app_affaire_note;
create table public.app_affaire_condition_reflets_avant_a3vague_20261125 as
  select app_affaire_id, rang, app_chaine_id, now() as copie_le from public.app_affaire_condition;
revoke all on public.app_affaire_note_reflets_avant_a3vague_20261125, public.app_affaire_condition_reflets_avant_a3vague_20261125
  from public, anon, authenticated;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_app_chaine_id, vers_app_affaire_id, vers_app_chaine_id, valeur,
   ancienne_valeur, lot_origine, pourquoi, ecrit_par)
select 'a3_vague_2026-11-25', row_number() over (order by t, a, r), 'reflet', colonne, 'RAFRAICHIR LE REFLET (A3)', a, avant, a,
       apres, coalesce(apres::text, '-'), coalesce(avant::text, '-'), 'A3 (passage 82, image 2026-11-25_072625)',
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
  if n <> 6 then raise exception '⛔ A3 controle : % note(s) sans transaction au lieu de 6 (1001388, 1001389, 1001391, 1001392, 1001394, 1001395)', n; end if;
  select count(*) into j from public.app_classeur_realignement_journal where lot = 'a3_vague_2026-11-25';
  select (select count(*) from public.app_affaire_note n join public.app_affaire_note_reflets_avant_a3vague_20261125 s using (app_affaire_id)
           where n.app_chaine_id is distinct from s.app_chaine_id)
       + (select count(*) from public.app_affaire_condition c join public.app_affaire_condition_reflets_avant_a3vague_20261125 s
           using (app_affaire_id, rang) where c.app_chaine_id is distinct from s.app_chaine_id) into n;
  if n <> j then raise exception '⛔ A3 controle : % reflet(s) change(s) pour % ligne(s) au journal', n, j; end if;
  if 269 >= 0 and j <> 269 then
    raise exception '⛔ A3 controle : % ecriture(s) au lieu des 269 mesurees par l''essai a blanc complet', j; end if;
  raise notice '✅ A3 : % reflet(s) de chaine rafraichi(s) (notes et conditions), tous au journal ; 0 faux', j;
end $$;

commit;
