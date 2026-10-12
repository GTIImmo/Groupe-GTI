-- ============================================================================
-- CHANTIER 2 -- LOT L4-BIS : LA VITESSE DU CLOISONNEMENT
-- Patch du 12/10/2026, apres le controle du lot L4 colle le meme jour.
--
-- POURQUOI CE PATCH : UNE ERREUR DE FORME, PAS DE FOND
--   Dans L4, j'ai appele mes fonctions de controle DIRECTEMENT dans les regles :
--       using (public.app_voit_cette_ligne(negociateur_email, agence_nom))
--   PostgreSQL les evalue alors UNE FOIS PAR LIGNE, et chacune rappelle
--   is_app_global_reader() et app_perimetre_courant() a chaque ligne.
--   Mesure du 12/10 : l'ecran des archives d'un negociateur = 8,15 s (35 318 lignes),
--   au lieu d'instantane avant le patch.
--
--   Les regles d'ORIGINE, elles, utilisaient exprès la forme
--       (select public.is_app_global_reader())
--   -- une sous-requete NON CORRELEE, que PostgreSQL evalue UNE SEULE FOIS pour
--   toute la requete. Je l'avais reperee pendant l'audit et je ne l'ai pas appliquee.
--
-- CE QUE CE PATCH CHANGE : LA FORME SEULE.
--   Aucune decision n'est revue. Pour chaque regle, les memes comptes voient
--   exactement les memes lignes qu'apres L4 -- c'est ce que la repetition verifie,
--   en comparant les nombres vus par un admin ET par un negociateur, avant/apres.
--
-- L'EQUIVALENCE, LIGNE PAR LIGNE
--   app_voit_cette_ligne(email, agence) rendait :
--     global reader            -> true   ... devient (select is_app_global_reader())
--     perimetre 'reseau'       -> true   ... devient (select app_perimetre_courant()) = 'reseau'
--     perimetre 'agence'       -> compare l'agence       ... idem, l'agence en (select)
--     sinon can_access_negotiator_email(email)
--            = (role admin/manager/lecture) ou (commercial et son adresse)
--            Le premier cas est DEJA couvert par le global reader en tete, donc il
--            ne reste que « commercial et son adresse » -> compare l'adresse, avec
--            le role lu dans un (select). Un role inconnu rend NULL -> faux, comme avant.
--
--   app_console_can_access_dossier(id, hid) teste les 3 index une fois par ligne.
--   Remplace par deux appartenances a un ENSEMBLE calcule une fois :
--     app_dossier_id in (select ...) or hektor_annonce_id in (select ...)
--   Les DEUX chemins sont conserves (id ET numero Hektor), comme la fonction d'origine.
--
-- RETOUR ARRIERE : patch_l4bis_vitesse_2026-10-12_INVERSE.sql
--                  (il remet les regles de L4, dont les empreintes sont connues)
-- REPETITION     : patch_l4bis_vitesse_2026-10-12_REPETITION.sql
--
-- LES WORKERS NE SONT PAS CONCERNES : service_role porte rolbypassrls.
-- ============================================================================

begin;

-- ----------------------------------------------------------------------------
-- 0. GARDE-FOU : on part bien de l'etat laisse par L4 ce matin
-- ----------------------------------------------------------------------------
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


-- ============================================================================
-- PARTIE 1 -- DEUX ENSEMBLES, CALCULES UNE SEULE FOIS
-- ============================================================================

-- 1.1 MES BIENS, au sens strict du portefeuille : les 3 index ou MON adresse est
--     le negociateur. Sert aux objets que Frederic a decides « ses biens »
--     TOUJOURS : les affaires, les commissions, les mandats.
--     Rend les deux clefs, parce que la fonction d'origine acceptait les deux.
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

-- 1.2 MES BIENS SELON LE PERIMETRE : pour les objets decides « tout le reseau »
--     mais qui ne portent pas l'adresse en propre (les liens).
--     perimetre 'reseau' -> la regle court-circuite AVANT d'appeler ceci.
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

-- 1.3 Les droits d'execution, comme pour les 4 fonctions de L4.
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


-- ============================================================================
-- PARTIE 2 -- LES 7 REGLES, MEME SENS, FORME QUI S'EVALUE UNE FOIS
-- ============================================================================

-- 2.1 ANNONCES
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

-- 2.2 ARCHIVES -- c'est elle qui mettait 8,15 s
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

-- 2.3 VENDUS / CLOS
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

-- 2.4 CONTACTS -- on garde la branche « contact rattache a un de mes biens »,
--     mais elle n'est atteinte que si le perimetre descend.
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

-- 2.5 LIENS (mandants, proprietaires, acquereurs)
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

-- 2.6 AFFAIRES ET COMMISSIONS -- « ses biens » TOUJOURS (decision de Frederic).
--     Les deux chemins de la fonction d'origine sont conserves.
drop policy if exists app_affaire_ledger_select_active_users on public.app_affaire_ledger;
create policy app_affaire_ledger_select_active_users
    on public.app_affaire_ledger
    for select
    using (
        (select public.is_app_global_reader())
        or app_dossier_id in (select m.id from public.app_mes_biens_portefeuille() m)
        or hektor_annonce_id::text in (select m.hid from public.app_mes_biens_portefeuille() m)
    );

-- 2.7 MANDATS (le bandeau de la fiche) -- Q2 option 1 : « ses biens »
drop policy if exists app_mandat_select_active_users on public.app_mandat;
create policy app_mandat_select_active_users
    on public.app_mandat
    for select
    using (
        (select public.is_app_global_reader())
        or app_dossier_id in (select m.id from public.app_mes_biens_portefeuille() m)
        or hektor_annonce_id::text in (select m.hid from public.app_mes_biens_portefeuille() m)
    );

-- NOTE : la regle du REGISTRE DES MANDATS (is_app_manager_or_admin) n'est PAS
-- touchee : elle ne lit aucune colonne, elle s'evalue deja une seule fois.


-- ============================================================================
-- PARTIE 3 -- CONTROLE IMMEDIAT
-- ============================================================================
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

    -- les 4 fonctions de L4 restent en place : elles servent encore
    if (select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public'
           and p.proname in ('app_perimetre_courant','app_mon_agence',
                             'app_voit_cette_ligne','app_voit_ce_dossier_selon_perimetre')) <> 4 then
        raise exception 'CONTROLE : une fonction de L4 a disparu.';
    end if;

    raise notice 'L4-BIS OK : 8 regles, 2 ensembles ouverts au bon niveau, les 4 fonctions de L4 intactes.';
end
$controle$;

commit;

-- ============================================================================
-- APRES LE COLLAGE
--   CHRONOMETRER a nouveau l'ecran des archives pour un negociateur :
--   il doit repasser SOUS LA SECONDE (8,15 s mesurees apres L4).
--   Et REVERIFIER que les nombres vus sont les MEMES qu'apres L4 :
--   un admin voit tout, Melanie voit 13 475 annonces, 3 affaires sur son bien
--   1346424, 0 sur le bien 1357257 d'un collegue, 0 au registre des mandats.
-- ============================================================================
