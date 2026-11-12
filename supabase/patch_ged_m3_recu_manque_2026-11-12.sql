-- ═══════════════════════════════════════════════════════════════════════════════
-- CHANTIER GED — MORCEAU 3 : « REÇU / MANQUE » — LIRE LES CLASSEMENTS                12/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md, §12.8.
--
-- ─── CE QUE CE PATCH POSE ───
--   ① une règle de LECTURE sur app_ged_classement, au MÊME périmètre que les documents eux-mêmes
--     (app_console_document_select_scope) : un lecteur global (admin, manager) voit tout ; un négociateur voit les
--     classements des biens de son portefeuille (app_mes_biens_portefeuille), et rien d'autre ;
--   ② le droit SELECT pour authenticated sur cette table, et RIEN d'autre (l'écriture reste la seule fonction
--     app_ged_classer du morceau 2) ;
--   ③ l'interrupteur ged_recu_manque, ÉTEINT (off / admin / on).
--
-- ─── CE QUE CE PATCH NE FAIT PAS ───
-- ⛔ aucune donnée écrite ; rattachements et journal restent illisibles par l'écran (rien ne les affiche encore) ;
--   rien dans app_console_document, rien chez Hektor, rien dans le worker.
--
-- ─── RETOUR ARRIÈRE ───  supabase/patch_ged_m3_recu_manque_2026-11-12_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════════

begin;
set local lock_timeout = '3s';

do $garde$
begin
  if to_regclass('public.app_ged_classement') is null then
    raise exception 'ARRET : app_ged_classement absente -- poser d''abord le morceau 1.';
  end if;
  if exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'app_ged_classement') then
    raise exception 'ARRET : une politique existe deja sur app_ged_classement -- patch deja applique ?';
  end if;
  if exists (select 1 from public.app_setting where key = 'ged_recu_manque') then
    raise exception 'ARRET : l''interrupteur ged_recu_manque existe deja -- patch deja applique ?';
  end if;
end
$garde$;

-- ─────────────────────────────────────────────────────── ① ② LA LECTURE
grant select on table public.app_ged_classement to authenticated;
create policy app_ged_classement_select_scope on public.app_ged_classement
  for select to authenticated
  using (
    (select public.is_app_global_reader())
    or hektor_annonce_id in (select m.hid from public.app_mes_biens_portefeuille() m(id, hid))
  );

-- ─────────────────────────────────────────────────────── ③ L'INTERRUPTEUR (ÉTEINT)
insert into public.app_setting (key, value, description, updated_at) values
  ('ged_recu_manque', 'off',
   'GED (12/11/2026) : le bloc « Reçu / Manque » de l''onglet Documents (les pièces du moment en cours). off / admin / on. Éteint = rien ne s''affiche.',
   now());

commit;

-- ALLUMER pour les admins : update public.app_setting set value = 'admin', updated_at = now() where key = 'ged_recu_manque';
-- ÉTEINDRE                : update public.app_setting set value = 'off',   updated_at = now() where key = 'ged_recu_manque';

-- ═══════════════════════════════════════════════════════════════════════════════
-- LES CONTRÔLES — à lire après le COMMIT. Tout doit être VERT.
-- ═══════════════════════════════════════════════════════════════════════════════
select '① une seule politique sur le classement, en lecture' as controle, count(*) as trouve,
       case when count(*) = 1 and bool_and(cmd = 'SELECT') then 'VERT' else 'ROUGE' end as verdict
  from pg_policies where schemaname = 'public' and tablename = 'app_ged_classement'
union all
select '② authenticated : SELECT seulement sur le classement', count(*),
       case when count(*) = 1 and bool_and(privilege_type = 'SELECT') then 'VERT' else 'ROUGE' end
  from information_schema.role_table_grants
 where table_schema = 'public' and table_name = 'app_ged_classement' and grantee = 'authenticated'
union all
select '③ anon : aucun droit sur les tables GED', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from information_schema.role_table_grants
 where table_schema = 'public' and table_name like 'app\_ged\_%' and grantee in ('anon', 'PUBLIC')
union all
select '④ rattachements et journal : toujours illisibles (aucune politique)', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from pg_policies where schemaname = 'public' and tablename in ('app_ged_rattachement', 'app_ged_journal')
union all
select '⑤ l''interrupteur ged_recu_manque est ÉTEINT', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from public.app_setting where key = 'ged_recu_manque' and value = 'off';
