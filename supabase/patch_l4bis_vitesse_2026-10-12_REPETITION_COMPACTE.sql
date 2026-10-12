begin;
create temporary table _l4bis_mesures(
    ordre  serial,
    etape  text,
    cle    text,
    valeur text
) on commit drop;
insert into _l4bis_mesures(etape, cle, valeur)
select 'AVANT', 'regle__' || tablename, md5(coalesce(qual, ''))
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename in ('app_dossier_current', 'app_archive_annonce_index_current', 'app_historical_annonce_index_current', 'app_contact_current', 'app_contact_relation_current', 'app_affaire_ledger', 'app_mandat');
insert into _l4bis_mesures(etape, cle, valeur)
select 'AVANT', 'ensembles_presents', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_mes_biens_portefeuille', 'app_mes_biens_selon_perimetre');
insert into _l4bis_mesures(etape, cle, valeur)
select 'AVANT', 'ensembles_ouverts_sans_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_mes_biens_portefeuille', 'app_mes_biens_selon_perimetre')
   and has_function_privilege('anon', p.oid, 'EXECUTE');
insert into _l4bis_mesures(etape, cle, valeur)
select 'AVANT', 'ensembles_utilisables_par_un_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_mes_biens_portefeuille', 'app_mes_biens_selon_perimetre')
   and has_function_privilege('authenticated', p.oid, 'EXECUTE');
insert into _l4bis_mesures(etape, cle, valeur)
select 'AVANT', 'fonctions_de_L4_intactes', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_perimetre_courant', 'app_mon_agence', 'app_voit_cette_ligne', 'app_voit_ce_dossier_selon_perimetre');
insert into _l4bis_mesures(etape, cle, valeur)
select 'AVANT', 'regles_de_lecture_au_total', count(*)::text
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT'
   and tablename in ('app_dossier_current', 'app_archive_annonce_index_current', 'app_historical_annonce_index_current', 'app_contact_current', 'app_contact_relation_current', 'app_affaire_ledger', 'app_mandat', 'app_mandat_register_current');
insert into _l4bis_mesures(etape, cle, valeur)
select 'AVANT', 'registre_des_mandats_reserve',
       case when exists (select 1 from pg_policies
                          where schemaname = 'public' and cmd = 'SELECT'
                            and tablename = 'app_mandat_register_current'
                            and qual like '%is_app_manager_or_admin%')
            then 'oui' else 'NON' end;
do $garde$
declare
    v_attendu jsonb := jsonb_build_object(
        'app_dossier_current',                  'bebfbd39f19ada2ad8f37d7b28eef4b4',
        'app_archive_annonce_index_current',    'bebfbd39f19ada2ad8f37d7b28eef4b4',
        'app_historical_annonce_index_current', 'bebfbd39f19ada2ad8f37d7b28eef4b4',
        'app_contact_current',                  '075389d63245e6794da9a4c0874edf71',
        'app_contact_relation_current',         'fd9ce6dd0bdf7ecf29d728e37b028577',
        'app_affaire_ledger',                   '2d3aa9390e6cb527a55d9d347d19d52b',
        'app_mandat',                           'ce33e869d64b7a831686a25795362032'
    );
    v_table text;
    v_trouve text;
begin
    for v_table in select jsonb_object_keys(v_attendu) loop
        select md5(coalesce(qual, '')) into v_trouve
          from pg_policies
         where schemaname = 'public' and tablename = v_table and cmd = 'SELECT'
         limit 1;
        if v_trouve is distinct from (v_attendu ->> v_table) then
            raise exception 'GARDE-FOU : la regle de % n''est pas celle laissee par L4 (trouve %, attendu %). Patch arrete.',
                v_table, coalesce(v_trouve, '(aucune)'), (v_attendu ->> v_table);
        end if;
    end loop;
    if not exists (select 1 from information_schema.columns
                    where table_schema = 'public' and table_name = 'app_user_profile'
                      and column_name = 'perimetre') then
        raise exception 'GARDE-FOU : la case perimetre est absente. L4 n''est pas en place : patch arrete.';
    end if;
end
$garde$;
create or replace function public.app_mes_biens_portefeuille()
returns table (id bigint, hid text)
language sql
stable
security definer
set search_path to 'public'
as $$
    with moi as (
        select lower(trim(coalesce(p.email, ''))) as adresse
          from public.app_user_profile p
         where p.id = auth.uid() and p.is_active = true
         limit 1
    )
    select d.app_dossier_id, d.hektor_annonce_id::text
      from public.app_dossier_current d, moi
     where nullif(moi.adresse, '') is not null
       and lower(trim(coalesce(d.negociateur_email, ''))) = moi.adresse
    union all
    select a.app_archive_id, a.hektor_annonce_id::text
      from public.app_archive_annonce_index_current a, moi
     where nullif(moi.adresse, '') is not null
       and lower(trim(coalesce(a.negociateur_email, ''))) = moi.adresse
    union all
    select h.app_historical_id, h.hektor_annonce_id::text
      from public.app_historical_annonce_index_current h, moi
     where nullif(moi.adresse, '') is not null
       and lower(trim(coalesce(h.negociateur_email, ''))) = moi.adresse;
$$;
create or replace function public.app_mes_biens_selon_perimetre()
returns table (id bigint, hid text)
language sql
stable
security definer
set search_path to 'public'
as $$
    with reglage as (
        select public.app_perimetre_courant() as perimetre,
               lower(trim(coalesce(public.app_mon_agence(), ''))) as agence,
               (select lower(trim(coalesce(p.email, '')))
                  from public.app_user_profile p
                 where p.id = auth.uid() and p.is_active = true
                 limit 1) as adresse
    )
    select d.app_dossier_id, d.hektor_annonce_id::text
      from public.app_dossier_current d, reglage r
     where (r.perimetre = 'agence'
            and nullif(r.agence, '') is not null
            and lower(trim(coalesce(d.agence_nom, ''))) = r.agence)
        or (r.perimetre = 'portefeuille'
            and nullif(r.adresse, '') is not null
            and lower(trim(coalesce(d.negociateur_email, ''))) = r.adresse)
    union all
    select a.app_archive_id, a.hektor_annonce_id::text
      from public.app_archive_annonce_index_current a, reglage r
     where (r.perimetre = 'agence'
            and nullif(r.agence, '') is not null
            and lower(trim(coalesce(a.agence_nom, ''))) = r.agence)
        or (r.perimetre = 'portefeuille'
            and nullif(r.adresse, '') is not null
            and lower(trim(coalesce(a.negociateur_email, ''))) = r.adresse)
    union all
    select h.app_historical_id, h.hektor_annonce_id::text
      from public.app_historical_annonce_index_current h, reglage r
     where (r.perimetre = 'agence'
            and nullif(r.agence, '') is not null
            and lower(trim(coalesce(h.agence_nom, ''))) = r.agence)
        or (r.perimetre = 'portefeuille'
            and nullif(r.adresse, '') is not null
            and lower(trim(coalesce(h.negociateur_email, ''))) = r.adresse);
$$;
do $droits$
declare
    v_signature text;
begin
    foreach v_signature in array array[
        'public.app_mes_biens_portefeuille()',
        'public.app_mes_biens_selon_perimetre()'
    ] loop
        execute format('revoke all on function %s from public', v_signature);
        execute format('revoke all on function %s from anon', v_signature);
        execute format('grant execute on function %s to authenticated', v_signature);
        execute format('grant execute on function %s to service_role', v_signature);
    end loop;
end
$droits$;
drop policy if exists app_dossier_current_select_scoped_users on public.app_dossier_current;
create policy app_dossier_current_select_scoped_users
    on public.app_dossier_current
    for select
    using (
        (select public.is_app_global_reader())
        or (select public.app_perimetre_courant()) = 'reseau'
        or (
            (select public.app_perimetre_courant()) = 'agence'
            and nullif(trim(coalesce(agence_nom, '')), '') is not null
            and lower(trim(agence_nom)) = (select lower(trim(coalesce(public.app_mon_agence(), '##aucune##'))))
        )
        or (
            nullif(trim(coalesce(negociateur_email, '')), '') is not null
            and lower(trim(negociateur_email)) = (
                select lower(trim(coalesce(p.email, '##aucun##')))
                  from public.app_user_profile p
                 where p.id = auth.uid() and p.is_active = true and p.role::text = 'commercial'
                 limit 1)
        )
    );
drop policy if exists app_archive_annonce_index_current_select_active_users on public.app_archive_annonce_index_current;
create policy app_archive_annonce_index_current_select_active_users
    on public.app_archive_annonce_index_current
    for select
    using (
        (select public.is_app_global_reader())
        or (select public.app_perimetre_courant()) = 'reseau'
        or (
            (select public.app_perimetre_courant()) = 'agence'
            and nullif(trim(coalesce(agence_nom, '')), '') is not null
            and lower(trim(agence_nom)) = (select lower(trim(coalesce(public.app_mon_agence(), '##aucune##'))))
        )
        or (
            nullif(trim(coalesce(negociateur_email, '')), '') is not null
            and lower(trim(negociateur_email)) = (
                select lower(trim(coalesce(p.email, '##aucun##')))
                  from public.app_user_profile p
                 where p.id = auth.uid() and p.is_active = true and p.role::text = 'commercial'
                 limit 1)
        )
    );
drop policy if exists app_historical_annonce_index_current_select_active_users on public.app_historical_annonce_index_current;
create policy app_historical_annonce_index_current_select_active_users
    on public.app_historical_annonce_index_current
    for select
    using (
        (select public.is_app_global_reader())
        or (select public.app_perimetre_courant()) = 'reseau'
        or (
            (select public.app_perimetre_courant()) = 'agence'
            and nullif(trim(coalesce(agence_nom, '')), '') is not null
            and lower(trim(agence_nom)) = (select lower(trim(coalesce(public.app_mon_agence(), '##aucune##'))))
        )
        or (
            nullif(trim(coalesce(negociateur_email, '')), '') is not null
            and lower(trim(negociateur_email)) = (
                select lower(trim(coalesce(p.email, '##aucun##')))
                  from public.app_user_profile p
                 where p.id = auth.uid() and p.is_active = true and p.role::text = 'commercial'
                 limit 1)
        )
    );
drop policy if exists app_contact_current_select_scoped on public.app_contact_current;
create policy app_contact_current_select_scoped
    on public.app_contact_current
    for select
    using (
        (select public.is_app_global_reader())
        or (select public.app_perimetre_courant()) = 'reseau'
        or (
            (select public.app_perimetre_courant()) = 'agence'
            and nullif(trim(coalesce(agence_nom, '')), '') is not null
            and lower(trim(agence_nom)) = (select lower(trim(coalesce(public.app_mon_agence(), '##aucune##'))))
        )
        or (
            nullif(trim(coalesce(negociateur_email, '')), '') is not null
            and lower(trim(negociateur_email)) = (
                select lower(trim(coalesce(p.email, '##aucun##')))
                  from public.app_user_profile p
                 where p.id = auth.uid() and p.is_active = true and p.role::text = 'commercial'
                 limit 1)
        )
        or exists (
            select 1
              from public.app_contact_relation_current r
             where r.hektor_contact_id = app_contact_current.hektor_contact_id
               and r.app_dossier_id is not null
               and r.app_dossier_id in (select m.id from public.app_mes_biens_selon_perimetre() m)
        )
    );
drop policy if exists app_contact_relation_current_select_scoped on public.app_contact_relation_current;
create policy app_contact_relation_current_select_scoped
    on public.app_contact_relation_current
    for select
    using (
        (select public.is_app_global_reader())
        or (select public.app_perimetre_courant()) = 'reseau'
        or app_dossier_id in (select m.id from public.app_mes_biens_selon_perimetre() m)
        or hektor_annonce_id::text in (select m.hid from public.app_mes_biens_selon_perimetre() m)
    );
drop policy if exists app_affaire_ledger_select_active_users on public.app_affaire_ledger;
create policy app_affaire_ledger_select_active_users
    on public.app_affaire_ledger
    for select
    using (
        (select public.is_app_global_reader())
        or app_dossier_id in (select m.id from public.app_mes_biens_portefeuille() m)
        or hektor_annonce_id::text in (select m.hid from public.app_mes_biens_portefeuille() m)
    );
drop policy if exists app_mandat_select_active_users on public.app_mandat;
create policy app_mandat_select_active_users
    on public.app_mandat
    for select
    using (
        (select public.is_app_global_reader())
        or app_dossier_id in (select m.id from public.app_mes_biens_portefeuille() m)
        or hektor_annonce_id::text in (select m.hid from public.app_mes_biens_portefeuille() m)
    );
do $controle$
declare
    v_regles int;
    v_fonctions int;
begin
    select count(*) into v_regles
      from pg_policies
     where schemaname = 'public' and cmd = 'SELECT'
       and tablename in ('app_dossier_current','app_contact_current','app_contact_relation_current',
                         'app_archive_annonce_index_current','app_historical_annonce_index_current',
                         'app_affaire_ledger','app_mandat','app_mandat_register_current');
    if v_regles <> 8 then
        raise exception 'CONTROLE : % regles de lecture sur 8 attendues.', v_regles;
    end if;
    select count(*) into v_fonctions
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public'
       and p.proname in ('app_mes_biens_portefeuille', 'app_mes_biens_selon_perimetre')
       and has_function_privilege('authenticated', p.oid, 'EXECUTE')
       and not has_function_privilege('anon', p.oid, 'EXECUTE');
    if v_fonctions <> 2 then
        raise exception 'CONTROLE : les 2 ensembles ne sont pas correctement ouverts (trouve %).', v_fonctions;
    end if;
    if (select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public'
           and p.proname in ('app_perimetre_courant','app_mon_agence',
                             'app_voit_cette_ligne','app_voit_ce_dossier_selon_perimetre')) <> 4 then
        raise exception 'CONTROLE : une fonction de L4 a disparu.';
    end if;
    raise notice 'L4-BIS OK : 8 regles, 2 ensembles ouverts au bon niveau, les 4 fonctions de L4 intactes.';
end
$controle$;
insert into _l4bis_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'regle__' || tablename, md5(coalesce(qual, ''))
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename in ('app_dossier_current', 'app_archive_annonce_index_current', 'app_historical_annonce_index_current', 'app_contact_current', 'app_contact_relation_current', 'app_affaire_ledger', 'app_mandat');
insert into _l4bis_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'ensembles_presents', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_mes_biens_portefeuille', 'app_mes_biens_selon_perimetre');
insert into _l4bis_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'ensembles_ouverts_sans_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_mes_biens_portefeuille', 'app_mes_biens_selon_perimetre')
   and has_function_privilege('anon', p.oid, 'EXECUTE');
insert into _l4bis_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'ensembles_utilisables_par_un_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_mes_biens_portefeuille', 'app_mes_biens_selon_perimetre')
   and has_function_privilege('authenticated', p.oid, 'EXECUTE');
insert into _l4bis_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'fonctions_de_L4_intactes', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_perimetre_courant', 'app_mon_agence', 'app_voit_cette_ligne', 'app_voit_ce_dossier_selon_perimetre');
insert into _l4bis_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'regles_de_lecture_au_total', count(*)::text
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT'
   and tablename in ('app_dossier_current', 'app_archive_annonce_index_current', 'app_historical_annonce_index_current', 'app_contact_current', 'app_contact_relation_current', 'app_affaire_ledger', 'app_mandat', 'app_mandat_register_current');
insert into _l4bis_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'registre_des_mandats_reserve',
       case when exists (select 1 from pg_policies
                          where schemaname = 'public' and cmd = 'SELECT'
                            and tablename = 'app_mandat_register_current'
                            and qual like '%is_app_manager_or_admin%')
            then 'oui' else 'NON' end;
drop policy if exists app_dossier_current_select_scoped_users on public.app_dossier_current;
create policy app_dossier_current_select_scoped_users
    on public.app_dossier_current
    for select
    using (public.app_voit_cette_ligne(negociateur_email, agence_nom));
drop policy if exists app_archive_annonce_index_current_select_active_users on public.app_archive_annonce_index_current;
create policy app_archive_annonce_index_current_select_active_users
    on public.app_archive_annonce_index_current
    for select
    using (public.app_voit_cette_ligne(negociateur_email, agence_nom));
drop policy if exists app_historical_annonce_index_current_select_active_users on public.app_historical_annonce_index_current;
create policy app_historical_annonce_index_current_select_active_users
    on public.app_historical_annonce_index_current
    for select
    using (public.app_voit_cette_ligne(negociateur_email, agence_nom));
drop policy if exists app_contact_current_select_scoped on public.app_contact_current;
create policy app_contact_current_select_scoped
    on public.app_contact_current
    for select
    using (
        public.app_voit_cette_ligne(negociateur_email, agence_nom)
        or exists (
            select 1
              from public.app_contact_relation_current r
             where r.hektor_contact_id = app_contact_current.hektor_contact_id
               and r.app_dossier_id is not null
               and public.can_access_current_dossier(r.app_dossier_id)
        )
    );
drop policy if exists app_contact_relation_current_select_scoped on public.app_contact_relation_current;
create policy app_contact_relation_current_select_scoped
    on public.app_contact_relation_current
    for select
    using (public.app_voit_ce_dossier_selon_perimetre(app_dossier_id, hektor_annonce_id::text));
drop policy if exists app_affaire_ledger_select_active_users on public.app_affaire_ledger;
create policy app_affaire_ledger_select_active_users
    on public.app_affaire_ledger
    for select
    using (coalesce(
        public.app_console_can_access_dossier(app_dossier_id, hektor_annonce_id::text),
        false));
drop policy if exists app_mandat_select_active_users on public.app_mandat;
create policy app_mandat_select_active_users
    on public.app_mandat
    for select
    using (coalesce(
        public.app_console_can_access_dossier(app_dossier_id, hektor_annonce_id::text),
        false));
drop function if exists public.app_mes_biens_selon_perimetre();
drop function if exists public.app_mes_biens_portefeuille();
do $controle$
declare
    v_attendu jsonb := jsonb_build_object(
        'app_dossier_current',                  'bebfbd39f19ada2ad8f37d7b28eef4b4',
        'app_archive_annonce_index_current',    'bebfbd39f19ada2ad8f37d7b28eef4b4',
        'app_historical_annonce_index_current', 'bebfbd39f19ada2ad8f37d7b28eef4b4',
        'app_contact_current',                  '075389d63245e6794da9a4c0874edf71',
        'app_contact_relation_current',         'fd9ce6dd0bdf7ecf29d728e37b028577',
        'app_affaire_ledger',                   '2d3aa9390e6cb527a55d9d347d19d52b',
        'app_mandat',                           'ce33e869d64b7a831686a25795362032'
    );
    v_table text;
    v_trouve text;
    v_ecarts int := 0;
begin
    for v_table in select jsonb_object_keys(v_attendu) loop
        select md5(coalesce(qual, '')) into v_trouve
          from pg_policies
         where schemaname = 'public' and tablename = v_table and cmd = 'SELECT'
         limit 1;
        if v_trouve is distinct from (v_attendu ->> v_table) then
            v_ecarts := v_ecarts + 1;
            raise notice 'ECART sur % : trouve %, attendu %', v_table, v_trouve, (v_attendu ->> v_table);
        end if;
    end loop;
    if v_ecarts > 0 then
        raise exception 'RETOUR ARRIERE INCOMPLET : % regle(s) ne correspondent pas a l''etat laisse par L4.', v_ecarts;
    end if;
    if exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                where n.nspname = 'public'
                  and p.proname in ('app_mes_biens_portefeuille', 'app_mes_biens_selon_perimetre')) then
        raise exception 'RETOUR ARRIERE INCOMPLET : un ensemble de L4-bis est encore la.';
    end if;
    raise notice 'RETOUR ARRIERE COMPLET : les 7 regles sont revenues a la forme de L4, les 2 ensembles sont partis.';
end
$controle$;
insert into _l4bis_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'regle__' || tablename, md5(coalesce(qual, ''))
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename in ('app_dossier_current', 'app_archive_annonce_index_current', 'app_historical_annonce_index_current', 'app_contact_current', 'app_contact_relation_current', 'app_affaire_ledger', 'app_mandat');
insert into _l4bis_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'ensembles_presents', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_mes_biens_portefeuille', 'app_mes_biens_selon_perimetre');
insert into _l4bis_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'ensembles_ouverts_sans_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_mes_biens_portefeuille', 'app_mes_biens_selon_perimetre')
   and has_function_privilege('anon', p.oid, 'EXECUTE');
insert into _l4bis_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'ensembles_utilisables_par_un_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_mes_biens_portefeuille', 'app_mes_biens_selon_perimetre')
   and has_function_privilege('authenticated', p.oid, 'EXECUTE');
insert into _l4bis_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'fonctions_de_L4_intactes', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_perimetre_courant', 'app_mon_agence', 'app_voit_cette_ligne', 'app_voit_ce_dossier_selon_perimetre');
insert into _l4bis_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'regles_de_lecture_au_total', count(*)::text
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT'
   and tablename in ('app_dossier_current', 'app_archive_annonce_index_current', 'app_historical_annonce_index_current', 'app_contact_current', 'app_contact_relation_current', 'app_affaire_ledger', 'app_mandat', 'app_mandat_register_current');
insert into _l4bis_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'registre_des_mandats_reserve',
       case when exists (select 1 from pg_policies
                          where schemaname = 'public' and cmd = 'SELECT'
                            and tablename = 'app_mandat_register_current'
                            and qual like '%is_app_manager_or_admin%')
            then 'oui' else 'NON' end;
do $final$
declare
    v_txt text;
    v_pas_revenues int;
    v_pas_changees int;
begin
    select count(*) into v_pas_revenues
      from _l4bis_mesures a
      join _l4bis_mesures z on z.cle = a.cle and z.etape = 'APRES_INVERSE'
     where a.etape = 'AVANT' and starts_with(a.cle, 'regle__')
       and a.valeur is distinct from z.valeur;
    select count(*) into v_pas_changees
      from _l4bis_mesures a
      join _l4bis_mesures p on p.cle = a.cle and p.etape = 'APRES_PATCH'
     where a.etape = 'AVANT' and starts_with(a.cle, 'regle__')
       and a.valeur = p.valeur;
    select string_agg(etape || ' | ' || cle || ' = ' || coalesce(valeur, '(null)'), chr(10)
                      order by ordre)
      into v_txt
      from _l4bis_mesures;
    raise exception E'ESSAI ANNULE -- RIEN N\'A ETE ECRIT.\n\nREGLES QUI NE REVIENNENT PAS A LEUR ETAT D\'ORIGINE : %   (0 attendu)\nREGLES QUE LE PATCH N\'A PAS CHANGEES : %   (0 attendu)\n\n%\n',
        v_pas_revenues, v_pas_changees, v_txt;
end
$final$;
rollback;
