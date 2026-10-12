-- ============================================================================
-- REPETITION DU LOT L4 -- CLOISONNER LES CONSULTATIONS
--
-- ⚠ CE SCRIPT N'ECRIT RIEN. Il joue le vrai patch, puis le vrai inverse, puis il
--   ECHOUE EXPRES pour tout annuler, et il affiche les mesures des trois etapes.
--
-- A COLLER dans l'editeur SQL :
--   https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
--
-- CE QU'IL FAUT VOIR A LA FIN -- le message doit commencer par
--   « ESSAI ANNULE -- RIEN N'A ETE ECRIT »
-- et les mesures doivent dire EXACTEMENT ceci :
--
--   AVANT          vues_qui_regardent_le_gardien                = 0
--                  vues_techniques_lisibles_par_un_compte       = 2
--                  case_perimetre                               = absente
--                  fonctions_neuves_presentes                   = 0
--
--   APRES_PATCH    vues_qui_regardent_le_gardien                = 4
--                  vues_techniques_lisibles_par_un_compte       = 0
--                  case_perimetre                               = presente
--                  comptes_hors_reseau                          = 0
--                  fonctions_neuves_presentes                   = 4
--                  fonctions_neuves_ouvertes_sans_compte        = 0   <<< chantier 1 intact
--                  fonctions_neuves_utilisables_par_un_compte   = 4   <<< l'ecran marche
--
--   APRES_INVERSE  vues_qui_regardent_le_gardien                = 0
--                  vues_techniques_lisibles_par_un_compte       = 2
--                  case_perimetre                               = absente
--                  fonctions_neuves_presentes                   = 0
--
-- ET SURTOUT : les 8 empreintes « regle__* » de AVANT doivent etre IDENTIQUES a
-- celles de APRES_INVERSE. C'est la preuve que le retour arriere est exact.
-- Les 8 de APRES_PATCH doivent, elles, etre DIFFERENTES de AVANT.
--
-- NE PAS COLLER LE VRAI PATCH tant que ces chiffres ne sont pas ceux-la.
--
-- ⚠ Fichier ASSEMBLE par supabase/generer_repetition_l4.py depuis
--   patch_l4_cloisonnement_2026-10-12.sql et son INVERSE.
--   NE PAS LE MODIFIER A LA MAIN : modifier les patchs, puis relancer le generateur.
-- ============================================================================

begin;

create temporary table _l4_mesures(
    ordre  serial,
    etape  text,
    cle    text,
    valeur text
) on commit drop;

-- ---------- MESURES : AVANT ----------
insert into _l4_mesures(etape, cle, valeur)
select 'AVANT', 'regle__' || tablename, md5(coalesce(qual, ''))
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename in ('app_dossier_current', 'app_contact_current', 'app_contact_relation_current', 'app_archive_annonce_index_current', 'app_historical_annonce_index_current', 'app_affaire_ledger', 'app_mandat', 'app_mandat_register_current');

insert into _l4_mesures(etape, cle, valeur)
select 'AVANT', 'vues_qui_regardent_le_gardien', count(*)::text
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relkind = 'v' and c.relname in ('app_dossiers_current', 'app_contacts_current', 'app_contact_relations_current', 'app_registre_mandats_current')
   and exists (select 1 from pg_options_to_table(c.reloptions)
                where option_name = 'security_invoker' and option_value in ('on', 'true'));

insert into _l4_mesures(etape, cle, valeur)
select 'AVANT', 'vues_techniques_lisibles_par_un_compte', count(*)::text
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relname in ('app_contacts_sans_numero', 'app_console_action_abandonnees')
   and has_table_privilege('authenticated', c.oid, 'SELECT');

insert into _l4_mesures(etape, cle, valeur)
select 'AVANT', 'case_perimetre',
       case when exists (select 1 from information_schema.columns
                          where table_schema = 'public' and table_name = 'app_user_profile'
                            and column_name = 'perimetre')
            then 'presente' else 'absente' end;

-- ⚠ On lit le perimetre par to_jsonb(p) ->> 'perimetre', PAS par « p.perimetre ».
--   Raison : aux etapes AVANT et APRES_INVERSE la colonne n'existe pas, et un CASE
--   ne protege de rien -- PostgreSQL ANALYSE toute la requete avant de l'executer,
--   branche non prise comprise, donc il echoue sur « column perimetre does not
--   exist ». to_jsonb rend NULL quand la colonne est absente : la mesure passe aux
--   trois etapes, avec la meme ligne de code.
insert into _l4_mesures(etape, cle, valeur)
select 'AVANT', 'comptes_hors_reseau',
       (select count(*)::text
          from public.app_user_profile p
         where coalesce(to_jsonb(p) ->> 'perimetre', 'reseau') <> 'reseau');

insert into _l4_mesures(etape, cle, valeur)
select 'AVANT', 'fonctions_neuves_presentes', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_perimetre_courant', 'app_mon_agence',
                     'app_voit_cette_ligne', 'app_voit_ce_dossier_selon_perimetre');

insert into _l4_mesures(etape, cle, valeur)
select 'AVANT', 'fonctions_neuves_ouvertes_sans_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_perimetre_courant', 'app_mon_agence',
                     'app_voit_cette_ligne', 'app_voit_ce_dossier_selon_perimetre')
   and has_function_privilege('anon', p.oid, 'EXECUTE');

insert into _l4_mesures(etape, cle, valeur)
select 'AVANT', 'fonctions_neuves_utilisables_par_un_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_perimetre_courant', 'app_mon_agence',
                     'app_voit_cette_ligne', 'app_voit_ce_dossier_selon_perimetre')
   and has_function_privilege('authenticated', p.oid, 'EXECUTE');


-- ############ LE VRAI PATCH, CORPS EXACT ############
-- ============================================================================
-- CHANTIER 2 -- LOT L4 : CLOISONNER LES CONSULTATIONS
-- Patch du 12/10/2026. Option A, choisie par Frederic.
--
-- CE QUE CA FAIT, EN TROIS GESTES
--   GESTE 1  les 4 vues que l'ecran lit passent DEVANT le gardien de leur table
--            (reglage « security_invoker »). Aujourd'hui elles l'ignorent, donc le
--            cloisonnement « ses biens » est un filtre d'AFFICHAGE, pas une serrure.
--   GESTE 2  la consigne des gardiens est corrigee pour dire ce que Frederic a decide
--            (annonces, contacts, liens, archives, vendus = TOUT LE RESEAU).
--   GESTE 3  une case « perimetre » sur le compte, qui ABAISSE cette consigne
--            (reseau / agence / portefeuille). Defaut = 'reseau'.
--
-- >>> AU COLLAGE, RIEN NE CHANGE A L'ECRAN <<<
--   Tous les comptes naissent avec perimetre = 'reseau'. Seuls DEUX ecrans changent,
--   et ce sont des decisions de Frederic :
--     - les COMMISSIONS et les AFFAIRES se cloisonnent sur ses biens ;
--     - le REGISTRE DES MANDATS devient reserve admin + manager.
--
-- DECISIONS A NE PAS RENVERSER (12/10/2026)
--   Q1 option 3 : un compte « portefeuille » PERD les archives et les vendus qui ne
--                 portent pas son adresse (23 412 et 4 536 lignes). ASSUME.
--                 L'adresse du negociateur manque sur 66 % des archives et 51 % des
--                 vendus, et 22 649 lignes n'ont AUCUNE trace de negociateur : c'est
--                 irreparable, seule l'agence est toujours renseignee.
--   Q2 option 1 : le bandeau mandat reste visible sur SES biens ; seul l'ECRAN
--                 registre des mandats se ferme.
--   R2          : PAS de 5e valeur de app_role (une valeur d'enum PostgreSQL ne peut
--                 JAMAIS etre retiree). L'agent commercial = un perimetre, pas un role.
--   E1          : l'agence d'un compte est DEDUITE de l'annuaire Hektor.
--
-- POURQUOI ON REMPLACE LES REGLES AU LIEU D'EN AJOUTER
--   En PostgreSQL, deux regles « permissive » sur la meme commande se combinent en OU.
--   Ajouter une regle plus stricte a cote d'une regle large ne cloisonnerait RIEN :
--   l'ancienne continuerait d'autoriser. D'ou le DROP + CREATE, avec l'inverse exact
--   dans patch_l4_cloisonnement_2026-10-12_INVERSE.sql.
--
-- LES WORKERS NE SONT PAS CONCERNES -- mesure du 12/10 :
--   service_role porte rolbypassrls = true. Les 4 workers, le backend Render, phase2,
--   le run de nuit et les crons ignorent toute regle RLS. Rien a redemarrer.
--
-- RETOUR ARRIERE : patch_l4_cloisonnement_2026-10-12_INVERSE.sql
-- REPETITION     : patch_l4_cloisonnement_2026-10-12_REPETITION.sql
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 0. GARDE-FOU : on refuse de passer si l'etat d'avant n'est pas celui mesure
--    le 12/10. Si une autre session est passee entre-temps, on s'arrete.
-- ----------------------------------------------------------------------------
do $garde$
declare
    -- LES HUIT regles que ce patch remplace, avec leur empreinte du 12/10.
    -- (les 6 premieres + archives et vendus, ajoutes le 12/10 : le garde-fou doit
    --  couvrir TOUTES les regles remplacees, sinon il laisse passer un ecart.)
    v_attendu jsonb := jsonb_build_object(
        'app_dossier_current',                  'c5109c98cb7801ed5b81b3d38e9d3105',
        'app_contact_current',                  '2818e450186a422804f3eda93025da02',
        'app_contact_relation_current',         'aba52a7eb4745a58b7ea130c7bfc9e60',
        'app_affaire_ledger',                   '71bef22dc7c148dc362e8670c90245b3',
        'app_mandat',                           '71bef22dc7c148dc362e8670c90245b3',
        'app_mandat_register_current',          '71bef22dc7c148dc362e8670c90245b3',
        'app_archive_annonce_index_current',    '71bef22dc7c148dc362e8670c90245b3',
        'app_historical_annonce_index_current', '71bef22dc7c148dc362e8670c90245b3'
    );
    v_table text;
    v_trouve text;
begin
    for v_table in select jsonb_object_keys(v_attendu) loop
        select md5(coalesce(qual, '')) into v_trouve
          from pg_policies
         where schemaname = 'public' and tablename = v_table and cmd = 'SELECT'
         limit 1;

        if v_trouve is null then
            raise exception 'GARDE-FOU : aucune regle de lecture sur %. Patch arrete.', v_table;
        end if;
        if v_trouve <> (v_attendu ->> v_table) then
            raise exception 'GARDE-FOU : la regle de lecture de % a change (trouve %, attendu %). Une autre session est passee : patch arrete.',
                v_table, v_trouve, (v_attendu ->> v_table);
        end if;
    end loop;

    -- les 4 vues doivent encore IGNORER leur gardien, sinon le patch est deja passe
    if exists (
        select 1 from pg_class c join pg_namespace n on n.oid = c.relnamespace
         where n.nspname = 'public' and c.relkind = 'v'
           and c.relname in ('app_dossiers_current','app_contacts_current',
                             'app_contact_relations_current','app_registre_mandats_current')
           and exists (select 1 from pg_options_to_table(c.reloptions)
                        where option_name = 'security_invoker')
    ) then
        raise exception 'GARDE-FOU : une des 4 vues porte deja le reglage. Le patch a deja ete passe : arret.';
    end if;
end
$garde$;


-- ============================================================================
-- PARTIE 1 -- LES FONDATIONS (tout est NEUF, rien n'est touche)
-- ============================================================================

-- 1.1 La case « perimetre » sur le compte. Defaut 'reseau' => aucun compte ne
--     change de comportement au collage.
alter table public.app_user_profile
    add column if not exists perimetre text not null default 'reseau';

do $$
begin
    if not exists (select 1 from pg_constraint
                    where conrelid = 'public.app_user_profile'::regclass
                      and conname = 'app_user_profile_perimetre_chk') then
        alter table public.app_user_profile
            add constraint app_user_profile_perimetre_chk
            check (perimetre in ('portefeuille', 'agence', 'reseau'));
    end if;
end
$$;

comment on column public.app_user_profile.perimetre is
    'Jusqu''ou ce compte voit : portefeuille (ses biens) / agence / reseau. '
    'Defaut reseau. Pose le 12/10/2026, lot L4 du chantier 2. '
    'C''est ce qui remplace un 5e role « agent commercial » (decision R2) : '
    'une valeur d''enum PostgreSQL ne peut jamais etre retiree, une colonne si.';

-- 1.2 Le perimetre du compte connecte. 'reseau' si inconnu : on n'enferme jamais
--     quelqu'un par accident (meme esprit que le coalesce du patch du 30/08).
create or replace function public.app_perimetre_courant()
returns text
language sql
stable
security definer
set search_path to 'public'
as $$
    select coalesce(p.perimetre, 'reseau')
      from public.app_user_profile p
     where p.id = auth.uid()
       and p.is_active = true
     limit 1;
$$;

-- 1.3 L'agence du compte connecte, DEDUITE de l'annuaire Hektor (decision E1).
--     Mesure du 12/10 : 155 adresses, 24 ont plusieurs agences dans leur histoire
--     mais AUCUNE n'a deux agences ACTIVES en meme temps -> non ambigu.
create or replace function public.app_mon_agence()
returns text
language sql
stable
security definer
set search_path to 'public'
as $$
    select a.agence_nom
      from public.app_user_profile p
      join public.app_hektor_negotiator_agency_directory a
        on lower(trim(coalesce(a.email, ''))) = lower(trim(coalesce(p.email, '')))
     where p.id = auth.uid()
       and p.is_active = true
       and a.is_active = true
       and nullif(trim(coalesce(a.agence_nom, '')), '') is not null
     limit 1;
$$;

-- 1.4 LE GARDIEN, pour tout ce qui porte en propre l'adresse du negociateur et
--     l'agence (annonces, contacts, archives, vendus, registre).
--     reseau       -> tout
--     agence       -> son agence (l'agence est TOUJOURS renseignee : 0 manquante)
--     portefeuille -> son adresse seulement
create or replace function public.app_voit_cette_ligne(
    target_negociateur_email text,
    target_agence_nom text
)
returns boolean
language sql
stable
security definer
set search_path to 'public'
as $$
    select case
        when public.is_app_global_reader() then true
        when public.app_perimetre_courant() = 'reseau' then true
        when public.app_perimetre_courant() = 'agence' then
             nullif(trim(coalesce(target_agence_nom, '')), '') is not null
             and lower(trim(target_agence_nom))
                 = lower(trim(coalesce(public.app_mon_agence(), '##aucune##')))
        else public.can_access_negotiator_email(target_negociateur_email)
    end;
$$;

-- 1.5 LE GARDIEN, pour ce qui n'est rattache qu'a un bien (les liens).
--     Meme echelle, mais la ligne ne porte pas l'adresse : on passe par les
--     3 index (parc vivant, archives, vendus).
create or replace function public.app_voit_ce_dossier_selon_perimetre(
    target_app_dossier_id bigint,
    target_hektor_annonce_id text
)
returns boolean
language sql
stable
security definer
set search_path to 'public'
as $$
    select case
        when public.is_app_global_reader() then true
        when public.app_perimetre_courant() = 'reseau' then true
        when public.app_perimetre_courant() = 'agence' then exists (
            select 1 from public.app_dossier_current d
             where (d.app_dossier_id = target_app_dossier_id
                 or d.hektor_annonce_id::text = nullif(target_hektor_annonce_id, ''))
               and lower(trim(coalesce(d.agence_nom, '')))
                   = lower(trim(coalesce(public.app_mon_agence(), '##aucune##')))
        ) or exists (
            select 1 from public.app_archive_annonce_index_current a
             where (a.app_archive_id = target_app_dossier_id
                 or a.hektor_annonce_id::text = nullif(target_hektor_annonce_id, ''))
               and lower(trim(coalesce(a.agence_nom, '')))
                   = lower(trim(coalesce(public.app_mon_agence(), '##aucune##')))
        ) or exists (
            select 1 from public.app_historical_annonce_index_current h
             where (h.app_historical_id = target_app_dossier_id
                 or h.hektor_annonce_id::text = nullif(target_hektor_annonce_id, ''))
               and lower(trim(coalesce(h.agence_nom, '')))
                   = lower(trim(coalesce(public.app_mon_agence(), '##aucune##')))
        )
        else coalesce(
            public.app_console_can_access_dossier(target_app_dossier_id, target_hektor_annonce_id),
            false)
    end;
$$;


-- 1.6 LES DROITS D'EXECUTION DES 4 FONCTIONS NEUVES
--     Mesure du 12/10 : le chantier 1 a laisse une regle par defaut (pg_default_acl,
--     posee par postgres) qui donne EXECUTE a authenticated et service_role, et NE LE
--     DONNE PAS a anon. Nos fonctions en heritent donc deja correctement.
--     On l'ecrit quand meme : si ce defaut changeait un jour, le patch resterait juste,
--     et l'intention est lisible. Meme forme que le patch du chantier 1 du 08/10.
do $droits$
declare
    v_signature text;
begin
    foreach v_signature in array array[
        'public.app_perimetre_courant()',
        'public.app_mon_agence()',
        'public.app_voit_cette_ligne(text, text)',
        'public.app_voit_ce_dossier_selon_perimetre(bigint, text)'
    ] loop
        execute format('revoke all on function %s from public', v_signature);
        execute format('revoke all on function %s from anon', v_signature);
        execute format('grant execute on function %s to authenticated', v_signature);
        execute format('grant execute on function %s to service_role', v_signature);
    end loop;
end
$droits$;


-- ============================================================================
-- PARTIE 2 -- GESTE 1 : LES 4 VUES PASSENT DEVANT LEUR GARDIEN
--   Sans ce reglage, une vue s'execute avec les droits de son proprietaire et
--   IGNORE la regle de la table : c'est le « guichet perce a cote du gardien ».
--   Les 4 sont CHAINEES (app_contact_relations_current lit app_dossiers_current)
--   -> les quatre ensemble, ou aucune.
--   Mesure du 12/10 : authenticated a bien SELECT sur les 13 tables sous-jacentes,
--   donc aucun risque d'erreur de permission a l'ecran.
-- ============================================================================

alter view public.app_dossiers_current            set (security_invoker = true);
alter view public.app_contacts_current             set (security_invoker = true);
alter view public.app_contact_relations_current     set (security_invoker = true);
alter view public.app_registre_mandats_current      set (security_invoker = true);


-- ============================================================================
-- PARTIE 3 -- GESTE 2 : LA CONSIGNE DES GARDIENS
-- ============================================================================

-- 3.1 ANNONCES -- decision : tout le reseau (abaissable par le perimetre)
drop policy if exists app_dossier_current_select_scoped_users on public.app_dossier_current;
create policy app_dossier_current_select_scoped_users
    on public.app_dossier_current
    for select
    using (public.app_voit_cette_ligne(negociateur_email, agence_nom));

-- 3.2 CONTACTS -- decision : tout le reseau. On GARDE la branche « contact
--     rattache a un de mes biens », qui sert quand le perimetre descend.
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

-- 3.3 LIENS (mandants, proprietaires, acquereurs) -- decision : tout le reseau
drop policy if exists app_contact_relation_current_select_scoped on public.app_contact_relation_current;
create policy app_contact_relation_current_select_scoped
    on public.app_contact_relation_current
    for select
    using (public.app_voit_ce_dossier_selon_perimetre(app_dossier_id, hektor_annonce_id::text));

-- 3.4 ARCHIVES -- decision : tout le reseau.
--     ⚠ Q1 option 3 : en perimetre « portefeuille », 23 412 lignes sur 35 318
--     deviennent invisibles (pas d'adresse de negociateur). ASSUME par Frederic.
drop policy if exists app_archive_annonce_index_current_select_active_users on public.app_archive_annonce_index_current;
create policy app_archive_annonce_index_current_select_active_users
    on public.app_archive_annonce_index_current
    for select
    using (public.app_voit_cette_ligne(negociateur_email, agence_nom));

-- 3.5 VENDUS / CLOS -- decision : tout le reseau. Meme reserve (4 536 / 8 940).
drop policy if exists app_historical_annonce_index_current_select_active_users on public.app_historical_annonce_index_current;
create policy app_historical_annonce_index_current_select_active_users
    on public.app_historical_annonce_index_current
    for select
    using (public.app_voit_cette_ligne(negociateur_email, agence_nom));

-- 3.6 AFFAIRES ET COMMISSIONS -- decision : SES BIENS, toujours.
--     C'est le seul endroit ou l'ecran change vraiment au collage : un
--     negociateur ne verra plus les ventes ni les commissions de ses collegues.
--     ⭐ On reutilise la fonction qui existe deja (elle teste les 3 index et
--     repond « oui » tout de suite pour admin / manager) : rien a inventer.
drop policy if exists app_affaire_ledger_select_active_users on public.app_affaire_ledger;
create policy app_affaire_ledger_select_active_users
    on public.app_affaire_ledger
    for select
    using (coalesce(
        public.app_console_can_access_dossier(app_dossier_id, hektor_annonce_id::text),
        false));

-- 3.7 MANDATS (la table) -- Q2 option 1 : le bandeau mandat reste visible sur
--     SES biens. Ce n'est PAS l'ecran registre (voir 3.8).
drop policy if exists app_mandat_select_active_users on public.app_mandat;
create policy app_mandat_select_active_users
    on public.app_mandat
    for select
    using (coalesce(
        public.app_console_can_access_dossier(app_dossier_id, hektor_annonce_id::text),
        false));

-- 3.8 REGISTRE DES MANDATS (l'ecran) -- decision 6 : reserve admin + manager,
--     comme l'ecran Suivi. Le negociateur n'y entre plus du tout.
drop policy if exists app_mandat_register_current_select_active_users on public.app_mandat_register_current;
create policy app_mandat_register_current_select_active_users
    on public.app_mandat_register_current
    for select
    using (public.is_app_manager_or_admin());


-- ============================================================================
-- PARTIE 4 -- DEUX FUITES REFERMEES
--   Ces 2 vues contournent elles aussi leur gardien, mais l'ECRAN NE LES LIT
--   JAMAIS (0 appel dans apps/hektor-v1). Plutot que de les regler, on retire
--   simplement le droit de lecture aux comptes connectes : service_role et
--   postgres gardent le leur (rolbypassrls), donc les outils continuent.
-- ============================================================================

revoke select on public.app_contacts_sans_numero       from authenticated;
revoke select on public.app_console_action_abandonnees from authenticated;


-- ============================================================================
-- PARTIE 5 -- CONTROLE IMMEDIAT, DANS LA MEME TRANSACTION
-- ============================================================================
do $controle$
declare
    v_vues int;
    v_regles int;
    v_perimetre_defaut text;
    v_comptes_hors_reseau int;
begin
    select count(*) into v_vues
      from pg_class c join pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'public' and c.relkind = 'v'
       and c.relname in ('app_dossiers_current','app_contacts_current',
                         'app_contact_relations_current','app_registre_mandats_current')
       and exists (select 1 from pg_options_to_table(c.reloptions)
                    where option_name = 'security_invoker' and option_value in ('on','true'));
    if v_vues <> 4 then
        raise exception 'CONTROLE : % vues reglees sur 4 attendues.', v_vues;
    end if;

    select count(*) into v_regles
      from pg_policies
     where schemaname = 'public' and cmd = 'SELECT'
       and tablename in ('app_dossier_current','app_contact_current','app_contact_relation_current',
                         'app_archive_annonce_index_current','app_historical_annonce_index_current',
                         'app_affaire_ledger','app_mandat','app_mandat_register_current');
    if v_regles <> 8 then
        raise exception 'CONTROLE : % regles de lecture sur 8 attendues.', v_regles;
    end if;

    select column_default into v_perimetre_defaut
      from information_schema.columns
     where table_schema = 'public' and table_name = 'app_user_profile' and column_name = 'perimetre';
    if v_perimetre_defaut is null or v_perimetre_defaut not like '%reseau%' then
        raise exception 'CONTROLE : le defaut de perimetre n''est pas reseau (trouve %).', v_perimetre_defaut;
    end if;

    select count(*) into v_comptes_hors_reseau
      from public.app_user_profile where perimetre <> 'reseau';
    if v_comptes_hors_reseau <> 0 then
        raise exception 'CONTROLE : % compte(s) ne sont pas en perimetre reseau. Au collage, TOUS doivent l''etre.',
            v_comptes_hors_reseau;
    end if;

    -- LE CHANTIER 1 DOIT RESTER INTACT : aucune des 4 fonctions neuves ne doit
    -- etre executable sans compte.
    if exists (
        select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public'
           and p.proname in ('app_perimetre_courant','app_mon_agence',
                             'app_voit_cette_ligne','app_voit_ce_dossier_selon_perimetre')
           and has_function_privilege('anon', p.oid, 'EXECUTE')
    ) then
        raise exception 'CONTROLE : une fonction neuve est executable par anon. Le chantier 1 serait defait : patch arrete.';
    end if;

    if (select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public'
           and p.proname in ('app_perimetre_courant','app_mon_agence',
                             'app_voit_cette_ligne','app_voit_ce_dossier_selon_perimetre')
           and has_function_privilege('authenticated', p.oid, 'EXECUTE')) <> 4 then
        raise exception 'CONTROLE : les 4 fonctions neuves ne sont pas toutes executables par un compte connecte. L''ecran casserait : patch arrete.';
    end if;

    raise notice 'L4 OK : 4 vues reglees, 8 regles posees, perimetre par defaut = reseau, % comptes tous en reseau.',
        (select count(*) from public.app_user_profile);
end
$controle$;


-- ============================================================================
-- APRES LE COLLAGE -- ce qui reste a faire a la main
--   1. CONTROLER en base (voir la note du chantier, section L4).
--   2. CONTROLER l'app connectee en admin : liste des annonces, contacts,
--      une fiche avec ses affaires, le bandeau mandat, l'ecran registre.
--   3. ESSAI REEL avec un compte de negociateur (Melanie LEGRAND ou Emanuelle
--      PEREIRA) : c'est le seul vrai controle du cloisonnement.
--   4. CHRONOMETRER la liste des affaires avec ce compte (non mesure d'avance).
--   5. RIEN a redemarrer, RIEN a deployer : service_role porte rolbypassrls.
-- ============================================================================

-- ---------- MESURES : APRES_PATCH ----------
insert into _l4_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'regle__' || tablename, md5(coalesce(qual, ''))
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename in ('app_dossier_current', 'app_contact_current', 'app_contact_relation_current', 'app_archive_annonce_index_current', 'app_historical_annonce_index_current', 'app_affaire_ledger', 'app_mandat', 'app_mandat_register_current');

insert into _l4_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'vues_qui_regardent_le_gardien', count(*)::text
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relkind = 'v' and c.relname in ('app_dossiers_current', 'app_contacts_current', 'app_contact_relations_current', 'app_registre_mandats_current')
   and exists (select 1 from pg_options_to_table(c.reloptions)
                where option_name = 'security_invoker' and option_value in ('on', 'true'));

insert into _l4_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'vues_techniques_lisibles_par_un_compte', count(*)::text
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relname in ('app_contacts_sans_numero', 'app_console_action_abandonnees')
   and has_table_privilege('authenticated', c.oid, 'SELECT');

insert into _l4_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'case_perimetre',
       case when exists (select 1 from information_schema.columns
                          where table_schema = 'public' and table_name = 'app_user_profile'
                            and column_name = 'perimetre')
            then 'presente' else 'absente' end;

-- ⚠ On lit le perimetre par to_jsonb(p) ->> 'perimetre', PAS par « p.perimetre ».
--   Raison : aux etapes AVANT et APRES_INVERSE la colonne n'existe pas, et un CASE
--   ne protege de rien -- PostgreSQL ANALYSE toute la requete avant de l'executer,
--   branche non prise comprise, donc il echoue sur « column perimetre does not
--   exist ». to_jsonb rend NULL quand la colonne est absente : la mesure passe aux
--   trois etapes, avec la meme ligne de code.
insert into _l4_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'comptes_hors_reseau',
       (select count(*)::text
          from public.app_user_profile p
         where coalesce(to_jsonb(p) ->> 'perimetre', 'reseau') <> 'reseau');

insert into _l4_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'fonctions_neuves_presentes', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_perimetre_courant', 'app_mon_agence',
                     'app_voit_cette_ligne', 'app_voit_ce_dossier_selon_perimetre');

insert into _l4_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'fonctions_neuves_ouvertes_sans_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_perimetre_courant', 'app_mon_agence',
                     'app_voit_cette_ligne', 'app_voit_ce_dossier_selon_perimetre')
   and has_function_privilege('anon', p.oid, 'EXECUTE');

insert into _l4_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'fonctions_neuves_utilisables_par_un_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_perimetre_courant', 'app_mon_agence',
                     'app_voit_cette_ligne', 'app_voit_ce_dossier_selon_perimetre')
   and has_function_privilege('authenticated', p.oid, 'EXECUTE');


-- ############ LE VRAI INVERSE, CORPS EXACT ############
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


-- ---------- MESURES : APRES_INVERSE ----------
insert into _l4_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'regle__' || tablename, md5(coalesce(qual, ''))
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename in ('app_dossier_current', 'app_contact_current', 'app_contact_relation_current', 'app_archive_annonce_index_current', 'app_historical_annonce_index_current', 'app_affaire_ledger', 'app_mandat', 'app_mandat_register_current');

insert into _l4_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'vues_qui_regardent_le_gardien', count(*)::text
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relkind = 'v' and c.relname in ('app_dossiers_current', 'app_contacts_current', 'app_contact_relations_current', 'app_registre_mandats_current')
   and exists (select 1 from pg_options_to_table(c.reloptions)
                where option_name = 'security_invoker' and option_value in ('on', 'true'));

insert into _l4_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'vues_techniques_lisibles_par_un_compte', count(*)::text
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relname in ('app_contacts_sans_numero', 'app_console_action_abandonnees')
   and has_table_privilege('authenticated', c.oid, 'SELECT');

insert into _l4_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'case_perimetre',
       case when exists (select 1 from information_schema.columns
                          where table_schema = 'public' and table_name = 'app_user_profile'
                            and column_name = 'perimetre')
            then 'presente' else 'absente' end;

-- ⚠ On lit le perimetre par to_jsonb(p) ->> 'perimetre', PAS par « p.perimetre ».
--   Raison : aux etapes AVANT et APRES_INVERSE la colonne n'existe pas, et un CASE
--   ne protege de rien -- PostgreSQL ANALYSE toute la requete avant de l'executer,
--   branche non prise comprise, donc il echoue sur « column perimetre does not
--   exist ». to_jsonb rend NULL quand la colonne est absente : la mesure passe aux
--   trois etapes, avec la meme ligne de code.
insert into _l4_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'comptes_hors_reseau',
       (select count(*)::text
          from public.app_user_profile p
         where coalesce(to_jsonb(p) ->> 'perimetre', 'reseau') <> 'reseau');

insert into _l4_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'fonctions_neuves_presentes', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_perimetre_courant', 'app_mon_agence',
                     'app_voit_cette_ligne', 'app_voit_ce_dossier_selon_perimetre');

insert into _l4_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'fonctions_neuves_ouvertes_sans_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_perimetre_courant', 'app_mon_agence',
                     'app_voit_cette_ligne', 'app_voit_ce_dossier_selon_perimetre')
   and has_function_privilege('anon', p.oid, 'EXECUTE');

insert into _l4_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'fonctions_neuves_utilisables_par_un_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_perimetre_courant', 'app_mon_agence',
                     'app_voit_cette_ligne', 'app_voit_ce_dossier_selon_perimetre')
   and has_function_privilege('authenticated', p.oid, 'EXECUTE');

-- ============================================================================
-- L'ERREUR VOLONTAIRE : elle annule les trois etapes et rend les mesures
-- ============================================================================
do $final$
declare
    v_txt text;
    v_ecarts int;
begin
    select count(*) into v_ecarts
      from _l4_mesures a
      join _l4_mesures z on z.cle = a.cle and z.etape = 'APRES_INVERSE'
     where a.etape = 'AVANT' and starts_with(a.cle, 'regle__')
       and a.valeur is distinct from z.valeur;
    -- starts_with, PAS « like 'regle__%' » : dans LIKE, le caractere _ est un
    -- joker, donc le motif aurait aussi attrape des cles voisines. Piege deja
    -- paye le 08/10 sur une mesure SQLite.

    select string_agg(etape || ' | ' || cle || ' = ' || coalesce(valeur, '(null)'), chr(10)
                      order by ordre)
      into v_txt
      from _l4_mesures;

    raise exception E'ESSAI ANNULE -- RIEN N\'A ETE ECRIT.\n\nREGLES QUI NE REVIENNENT PAS A LEUR ETAT D\'ORIGINE : %\n(0 attendu)\n\n%\n',
        v_ecarts, v_txt;
end
$final$;

-- jamais atteint
rollback;
