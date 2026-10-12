-- ============================================================================
-- RETOUR ARRIERE DU LOT L4 -- CLOISONNER LES CONSULTATIONS
-- Inverse exact de patch_l4_cloisonnement_2026-10-12.sql
--
-- Il remet l'etat RELEVE LE 12/10/2026 avant le patch, mot pour mot :
--   - les 4 vues cessent de regarder leur gardien ;
--   - les 8 regles de lecture retrouvent leur condition d'origine
--     (empreintes md5 verifiees a la fin) ;
--   - les 2 droits de lecture sont rendus ;
--   - la case « perimetre » et les 4 fonctions neuves disparaissent.
--
-- ⚠ AVANT DE SUPPRIMER LA CASE « PERIMETRE », ce script SAUVEGARDE les comptes
--    qui ne sont pas en 'reseau' dans une table datee
--    app_user_perimetre_avant_retour_<AAAAMMJJ>. Patron du projet : on sauvegarde
--    AVANT un geste destructif, puis on nettoie.
--    Sans cela, le reglage de chaque negociateur serait perdu en silence.
-- ============================================================================

begin;

-- ----------------------------------------------------------------------------
-- 0. SAUVEGARDE DATEE de ce qui serait perdu
-- ----------------------------------------------------------------------------
do $sauvegarde$
declare
    v_table text := 'app_user_perimetre_avant_retour_' || to_char(now(), 'YYYYMMDD');
    v_hors_reseau int := 0;
begin
    if exists (select 1 from information_schema.columns
                where table_schema = 'public' and table_name = 'app_user_profile'
                  and column_name = 'perimetre') then

        execute format(
            'create table if not exists public.%I as
               select id, email, role::text as role, perimetre, now() as sauvegarde_le
                 from public.app_user_profile
                where perimetre is distinct from ''reseau''', v_table);

        execute format('select count(*) from public.%I', v_table) into v_hors_reseau;
        raise notice 'SAUVEGARDE : % compte(s) hors reseau conserves dans public.%', v_hors_reseau, v_table;
    else
        raise notice 'SAUVEGARDE : la colonne perimetre n''existe pas, rien a sauvegarder.';
    end if;
end
$sauvegarde$;


-- ----------------------------------------------------------------------------
-- 1. LES 4 VUES CESSENT DE REGARDER LEUR GARDIEN
-- ----------------------------------------------------------------------------
alter view public.app_dossiers_current            reset (security_invoker);
alter view public.app_contacts_current             reset (security_invoker);
alter view public.app_contact_relations_current     reset (security_invoker);
alter view public.app_registre_mandats_current      reset (security_invoker);


-- ----------------------------------------------------------------------------
-- 2. LES 8 REGLES RETROUVENT LEUR CONDITION D'ORIGINE
--    (texte releve le 12/10/2026 par pg_policies)
-- ----------------------------------------------------------------------------

-- 2.1 ANNONCES -- empreinte d'origine c5109c98cb7801ed5b81b3d38e9d3105
drop policy if exists app_dossier_current_select_scoped_users on public.app_dossier_current;
create policy app_dossier_current_select_scoped_users
    on public.app_dossier_current
    for select
    using (
        (select public.is_app_global_reader() as is_app_global_reader)
        or public.can_access_negotiator_email(negociateur_email)
    );

-- 2.2 CONTACTS -- empreinte d'origine 2818e450186a422804f3eda93025da02
drop policy if exists app_contact_current_select_scoped on public.app_contact_current;
create policy app_contact_current_select_scoped
    on public.app_contact_current
    for select
    using (
        (select public.is_app_global_reader() as is_app_global_reader)
        or public.can_access_negotiator_email(negociateur_email)
        or (exists (
            select 1
              from public.app_contact_relation_current r
             where r.hektor_contact_id = app_contact_current.hektor_contact_id
               and r.app_dossier_id is not null
               and public.can_access_current_dossier(r.app_dossier_id)
        ))
    );

-- 2.3 LIENS -- empreinte d'origine aba52a7eb4745a58b7ea130c7bfc9e60
drop policy if exists app_contact_relation_current_select_scoped on public.app_contact_relation_current;
create policy app_contact_relation_current_select_scoped
    on public.app_contact_relation_current
    for select
    using (
        (select public.is_app_global_reader() as is_app_global_reader)
        or (app_dossier_id is not null and public.can_access_current_dossier(app_dossier_id))
    );

-- 2.4 a 2.8 -- les cinq qui partageaient la meme condition is_app_user_active()
--             empreinte d'origine 71bef22dc7c148dc362e8670c90245b3

drop policy if exists app_archive_annonce_index_current_select_active_users on public.app_archive_annonce_index_current;
create policy app_archive_annonce_index_current_select_active_users
    on public.app_archive_annonce_index_current
    for select
    using (public.is_app_user_active());

drop policy if exists app_historical_annonce_index_current_select_active_users on public.app_historical_annonce_index_current;
create policy app_historical_annonce_index_current_select_active_users
    on public.app_historical_annonce_index_current
    for select
    using (public.is_app_user_active());

drop policy if exists app_affaire_ledger_select_active_users on public.app_affaire_ledger;
create policy app_affaire_ledger_select_active_users
    on public.app_affaire_ledger
    for select
    using (public.is_app_user_active());

drop policy if exists app_mandat_select_active_users on public.app_mandat;
create policy app_mandat_select_active_users
    on public.app_mandat
    for select
    using (public.is_app_user_active());

drop policy if exists app_mandat_register_current_select_active_users on public.app_mandat_register_current;
create policy app_mandat_register_current_select_active_users
    on public.app_mandat_register_current
    for select
    using (public.is_app_user_active());


-- ----------------------------------------------------------------------------
-- 3. LES 2 DROITS DE LECTURE SONT RENDUS
-- ----------------------------------------------------------------------------
grant select on public.app_contacts_sans_numero       to authenticated;
grant select on public.app_console_action_abandonnees to authenticated;


-- ----------------------------------------------------------------------------
-- 4. LES OBJETS NEUFS DISPARAISSENT
--    Dans cet ordre : les regles ne les utilisent plus (partie 2), donc on peut.
-- ----------------------------------------------------------------------------
drop function if exists public.app_voit_ce_dossier_selon_perimetre(bigint, text);
drop function if exists public.app_voit_cette_ligne(text, text);
drop function if exists public.app_mon_agence();
drop function if exists public.app_perimetre_courant();

alter table public.app_user_profile drop constraint if exists app_user_profile_perimetre_chk;
alter table public.app_user_profile drop column if exists perimetre;


-- ----------------------------------------------------------------------------
-- 5. CONTROLE : on verifie que l'etat d'AVANT est bien revenu, a l'empreinte
-- ----------------------------------------------------------------------------
do $controle$
declare
    v_attendu jsonb := jsonb_build_object(
        'app_dossier_current',                 'c5109c98cb7801ed5b81b3d38e9d3105',
        'app_contact_current',                 '2818e450186a422804f3eda93025da02',
        'app_contact_relation_current',        'aba52a7eb4745a58b7ea130c7bfc9e60',
        'app_affaire_ledger',                  '71bef22dc7c148dc362e8670c90245b3',
        'app_mandat',                          '71bef22dc7c148dc362e8670c90245b3',
        'app_mandat_register_current',         '71bef22dc7c148dc362e8670c90245b3',
        'app_archive_annonce_index_current',   '71bef22dc7c148dc362e8670c90245b3',
        'app_historical_annonce_index_current','71bef22dc7c148dc362e8670c90245b3'
    );
    v_table text;
    v_trouve text;
    v_ecarts int := 0;
    v_vues int;
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

    select count(*) into v_vues
      from pg_class c join pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'public' and c.relkind = 'v'
       and c.relname in ('app_dossiers_current','app_contacts_current',
                         'app_contact_relations_current','app_registre_mandats_current')
       and exists (select 1 from pg_options_to_table(c.reloptions)
                    where option_name = 'security_invoker');

    if v_ecarts > 0 then
        raise exception 'RETOUR ARRIERE INCOMPLET : % regle(s) ne correspondent pas a l''etat du 12/10.', v_ecarts;
    end if;
    if v_vues <> 0 then
        raise exception 'RETOUR ARRIERE INCOMPLET : % vue(s) portent encore le reglage.', v_vues;
    end if;

    raise notice 'RETOUR ARRIERE COMPLET : 8 regles a leur empreinte d''origine, 0 vue reglee.';
end
$controle$;

commit;
