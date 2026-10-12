-- ============================================================================
-- RETOUR ARRIERE DU LOT L4-BIS -- LA VITESSE DU CLOISONNEMENT
-- Inverse exact de patch_l4bis_vitesse_2026-10-12.sql
--
-- Il remet les 7 regles TELLES QUE L4 LES AVAIT POSEES ce matin, avec leurs
-- empreintes connues, et supprime les 2 ensembles ajoutes par L4-bis.
--
-- ⚠ Il ne remet PAS l'etat d'avant-hier : pour cela, enchainer ensuite
--    patch_l4_cloisonnement_2026-10-12_INVERSE.sql.
--    La chaine est : L4-BIS_INVERSE -> etat L4 ; puis L4_INVERSE -> etat d'origine.
--
-- ⚠ Il remet donc aussi LA LENTEUR mesuree le 12/10 : l'ecran des archives d'un
--    negociateur a 8,15 s. C'est volontaire : un retour arriere rend l'etat
--    precedent, defaut compris.
-- ============================================================================

begin;

-- ----------------------------------------------------------------------------
-- 1. LES 7 REGLES REVIENNENT A LA FORME DE L4
-- ----------------------------------------------------------------------------

-- 1.1 ANNONCES -- empreinte L4 bebfbd39f19ada2ad8f37d7b28eef4b4
drop policy if exists app_dossier_current_select_scoped_users on public.app_dossier_current;
create policy app_dossier_current_select_scoped_users
    on public.app_dossier_current
    for select
    using (public.app_voit_cette_ligne(negociateur_email, agence_nom));

-- 1.2 ARCHIVES -- meme empreinte L4
drop policy if exists app_archive_annonce_index_current_select_active_users on public.app_archive_annonce_index_current;
create policy app_archive_annonce_index_current_select_active_users
    on public.app_archive_annonce_index_current
    for select
    using (public.app_voit_cette_ligne(negociateur_email, agence_nom));

-- 1.3 VENDUS / CLOS -- meme empreinte L4
drop policy if exists app_historical_annonce_index_current_select_active_users on public.app_historical_annonce_index_current;
create policy app_historical_annonce_index_current_select_active_users
    on public.app_historical_annonce_index_current
    for select
    using (public.app_voit_cette_ligne(negociateur_email, agence_nom));

-- 1.4 CONTACTS -- empreinte L4 075389d63245e6794da9a4c0874edf71
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

-- 1.5 LIENS -- empreinte L4 fd9ce6dd0bdf7ecf29d728e37b028577
drop policy if exists app_contact_relation_current_select_scoped on public.app_contact_relation_current;
create policy app_contact_relation_current_select_scoped
    on public.app_contact_relation_current
    for select
    using (public.app_voit_ce_dossier_selon_perimetre(app_dossier_id, hektor_annonce_id::text));

-- 1.6 AFFAIRES ET COMMISSIONS -- empreinte L4 2d3aa9390e6cb527a55d9d347d19d52b
drop policy if exists app_affaire_ledger_select_active_users on public.app_affaire_ledger;
create policy app_affaire_ledger_select_active_users
    on public.app_affaire_ledger
    for select
    using (coalesce(
        public.app_console_can_access_dossier(app_dossier_id, hektor_annonce_id::text),
        false));

-- 1.7 MANDATS -- empreinte L4 ce33e869d64b7a831686a25795362032
drop policy if exists app_mandat_select_active_users on public.app_mandat;
create policy app_mandat_select_active_users
    on public.app_mandat
    for select
    using (coalesce(
        public.app_console_can_access_dossier(app_dossier_id, hektor_annonce_id::text),
        false));


-- ----------------------------------------------------------------------------
-- 2. LES 2 ENSEMBLES DISPARAISSENT (plus aucune regle ne les utilise)
-- ----------------------------------------------------------------------------
drop function if exists public.app_mes_biens_selon_perimetre();
drop function if exists public.app_mes_biens_portefeuille();


-- ----------------------------------------------------------------------------
-- 3. CONTROLE : on verifie les 7 empreintes de L4, a l'empreinte
-- ----------------------------------------------------------------------------
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

commit;
