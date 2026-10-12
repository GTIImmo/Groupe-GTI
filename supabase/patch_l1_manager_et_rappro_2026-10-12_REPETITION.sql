-- ============================================================================
-- REPETITION DU LOT L1 -- « manager = admin » + les rapprochements
--
-- ⚠ CE SCRIPT N'ECRIT RIEN. Il joue le vrai patch, puis le vrai inverse, puis il
--   ECHOUE EXPRES pour tout annuler, et il affiche les mesures des trois etapes.
--
-- A COLLER dans l'editeur SQL :
--   https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
--
-- CE QU'IL FAUT VOIR A LA FIN :
--   ESSAI ANNULE -- RIEN N'A ETE ECRIT
--   CORPS QUI NE REVIENNENT PAS A L'ORIGINE : 0   (0 attendu)
--   CORPS QUE LE PATCH N'A PAS CHANGES      : 0   (0 attendu)
--
--   AVANT          fonctions_affaire_ouvertes_au_manager          = 0
--                  statut_et_archivage_ouverts_au_manager         = non
--                  statut_et_archivage_encore_admin_seul          = oui
--                  regles_rapprochement_qui_suivent_le_perimetre  = 0
--                  types_du_commercial_intacts                    = 21
--                  archivage_entre_dans_la_liste_du_commercial    = non
--                  is_app_admin_existe_toujours                   = oui
--                  rapprochements_lisibles_sans_compte            = 0
--
--   APRES_PATCH    fonctions_affaire_ouvertes_au_manager          = 6
--                  statut_et_archivage_ouverts_au_manager         = oui  <<< BASCULE
--                  statut_et_archivage_encore_admin_seul          = non  <<< TEMOIN INVERSE
--                  regles_rapprochement_qui_suivent_le_perimetre  = 3
--                  types_du_commercial_intacts                    = 21  <<< PAS TOUCHES
--                  archivage_entre_dans_la_liste_du_commercial    = non <<< TOUJOURS
--                  is_app_admin_existe_toujours                   = oui <<< CONSERVEE
--                  rapprochements_lisibles_sans_compte            = 0   <<< chantier 1
--
--   ⚠ LES DEUX LIGNES « statut_et_archivage_* » VONT PAR PAIRE, et elles doivent
--     BASCULER TOUTES LES DEUX (non->oui et oui->non). Au premier essai du 12/10,
--     la premiere disait « oui » aux trois etapes : la mesure cherchait une phrase
--     qui existait DEJA dans le videur, donc elle ne prouvait rien. Le temoin
--     inverse est la pour que ce piege ne puisse plus passer.
--
--   APRES_INVERSE  identique a AVANT
--
-- ⚠ POURQUOI « is_app_admin_existe_toujours » COMPTE : cette fonction sert AUSSI
--   a la regle de lecture des profils. On ne la modifie pas -- on remplace
--   seulement son APPEL dans les 6 fonctions « affaire ».
--
-- ⚠ AU COLLAGE, RIEN NE CHANGE POUR PERSONNE : comptes_manager = 0 et
--   comptes_hors_reseau = 0. Le mecanisme est pose, eteint.
--
-- ⚠ Fichier ASSEMBLE par supabase/generer_repetition_l1.py.
--   NE PAS LE MODIFIER A LA MAIN : modifier les patchs, puis relancer le generateur.
-- ============================================================================

begin;

create temporary table _l1_mesures(
    ordre  serial,
    etape  text,
    cle    text,
    valeur text
) on commit drop;

-- ---------- MESURES : AVANT ----------
insert into _l1_mesures(etape, cle, valeur)
select 'AVANT', 'corps__' || p.proname, md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_affaire_note_ecrire', 'app_affaire_personne_ecart_fermer', 'app_conditions_affaire_ecrire', 'app_edit_affaire_optimistic', 'app_geste_affaire_optimistic', 'app_modifier_affaire_optimistic', 'app_console_can_request_job');

insert into _l1_mesures(etape, cle, valeur)
select 'AVANT', 'fonctions_affaire_ouvertes_au_manager', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_affaire_note_ecrire', 'app_affaire_personne_ecart_fermer', 'app_conditions_affaire_ecrire', 'app_edit_affaire_optimistic', 'app_geste_affaire_optimistic', 'app_modifier_affaire_optimistic')
   and position('is_app_manager_or_admin()' in pg_get_functiondef(p.oid)) > 0;

insert into _l1_mesures(etape, cle, valeur)
select 'AVANT', 'is_app_admin_existe_toujours',
       case when exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                          where n.nspname = 'public' and p.proname = 'is_app_admin')
            then 'oui' else '*** NON ***' end;

-- ⚠ ON CHERCHE LE CAS PARTICULIER, PAS N'IMPORTE QUEL « admin, manager ».
--   La phrase « current_app_role in ('admin', 'manager') » EXISTE DEJA dans le
--   videur : c'est celle qui donne au manager tout le reste. La chercher rendait
--   « oui » aux trois etapes et ne mesurait RIEN (erreur trouvee par la repetition
--   du 12/10 -- « chercher un mot n'est pas mesurer un comportement »).
--   La seule phrase qui change est celle du RETURN du cas particulier.
insert into _l1_mesures(etape, cle, valeur)
select 'AVANT', 'statut_et_archivage_ouverts_au_manager',
       case when position('coalesce(current_app_role in (''admin'', ''manager''), false)' in d.def) > 0
            then 'oui' else 'non' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job' limit 1) d;

-- et le temoin inverse : l'ancienne phrase doit DISPARAITRE (1 -> 0)
insert into _l1_mesures(etape, cle, valeur)
select 'AVANT', 'statut_et_archivage_encore_admin_seul',
       case when position('coalesce(current_app_role = ''admin'', false)' in d.def) > 0
            then 'oui' else 'non' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job' limit 1) d;

insert into _l1_mesures(etape, cle, valeur)
select 'AVANT', 'types_du_commercial_intacts', count(*)::text
  from unnest(array['prepare_document_cloud', 'upload_document_to_hektor', 'prepare_archived_annonce_detail', 'prepare_historical_annonce_detail', 'sync_console_documents', 'relance_signature', 'cancel_signature_procedure', 'update_hektor_annonce_fields', 'link_hektor_mandant', 'unlink_hektor_mandant', 'create_hektor_mandant_contact', 'update_hektor_mandant_contact', 'delete_document_from_hektor', 'generate_estimation_pdf', 'generate_mandat_document', 'generate_cadastre_document', 'upload_hektor_photo', 'sync_hektor_photos', 'matterport_action', 'create_hektor_mandat_auto_number', 'restore_hektor_annonce']) AS t(nom)
 where position(t.nom in (select pg_get_functiondef(p.oid)
                            from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                           where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
                           limit 1)) > 0;

insert into _l1_mesures(etape, cle, valeur)
select 'AVANT', 'archivage_entre_dans_la_liste_du_commercial',
       case when position('''archive_hektor_annonce''' in
                          substring(d.def from position('current_app_role = ''commercial''' in d.def))) > 0
            then '*** OUI, GRAVE ***' else 'non' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job' limit 1) d;

insert into _l1_mesures(etape, cle, valeur)
select 'AVANT', 'regles_rapprochement_qui_suivent_le_perimetre', count(*)::text
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename in ('app_rapprochement', 'app_rapprochement_score_history', 'app_relance_rapprochement')
   and coalesce(qual, '') like '%app_perimetre_courant%';

insert into _l1_mesures(etape, cle, valeur)
select 'AVANT', 'rapprochements_lisibles_sans_compte', count(*)::text
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relname in ('app_rapprochement', 'app_rapprochement_score_history', 'app_relance_rapprochement')
   and has_table_privilege('anon', c.oid, 'SELECT');

insert into _l1_mesures(etape, cle, valeur)
select 'AVANT', 'comptes_manager', count(*)::text
  from public.app_user_profile where role::text = 'manager';

insert into _l1_mesures(etape, cle, valeur)
select 'AVANT', 'comptes_hors_reseau', count(*)::text
  from public.app_user_profile p
 where coalesce(to_jsonb(p) ->> 'perimetre', 'reseau') <> 'reseau';


-- ############ LE VRAI PATCH L1, CORPS EXACT ############
-- ============================================================================
-- CHANTIER 2 -- FINIR LE CHANTIER, PARTIE BASE
--   L1  « manager = admin »  (decision de Frederic du 12/10)
--   +   cacher l'ecran Rapprochement a un compte au perimetre reduit
--
-- TROIS MORCEAUX, AUCUN DEPLOIEMENT
--
--   1. LES 6 FONCTIONS « AFFAIRE » passent de « admin seul » a « admin + manager »
--      (offre, compromis, vente, note, conditions, ecart de personne).
--      ⚠ On ne touche PAS la fonction is_app_admin() elle-meme : elle sert aussi a
--      la regle de lecture des profils, qu'on n'a pas besoin de changer -- l'outil
--      « Utilisateurs » passe par la fonction serveur admin-users, qui lit avec la
--      cle de service. On remplace seulement son APPEL dans les 6 fonctions.
--
--   2. LE VIDEUR DES ANNONCES : le cas particulier « statut et archivage », reserve
--      a l'admin depuis le 21/05 SANS RAISON ECRITE, s'ouvre au manager.
--      ⚠ La liste du commercial n'est PAS touchee : le patch le verifie.
--
--   3. LES RAPPROCHEMENTS se cachent a un compte dont le perimetre n'est pas
--      « reseau ». POURQUOI : l'essai du 12/10 sur Melanie l'a mesure --
--      52 835 rapprochements visibles, dont 49 300 (93 %) pointaient vers un bien
--      qu'elle ne pouvait PLUS ouvrir. Mieux vaut un ecran absent qu'un ecran qui
--      ment. C'est une SOLUTION D'ATTENTE, assumee : le vrai sujet (ce que doit
--      voir un agent commercial) est NOTE et sera tranche plus tard par Frederic.
--
-- >>> AU COLLAGE, RIEN NE CHANGE POUR PERSONNE <<<
--   Il n'y a AUCUN compte manager (0 actif, 0 inactif), et tous les comptes sont
--   en perimetre « reseau » -- donc la regle des rapprochements reste vraie pour
--   tout le monde. Le mecanisme est pose, eteint.
--
-- CE QUI N'EST PAS ICI, et qui demandera un deploiement :
--   - la case « perimetre » dans l'ecran et dans la fonction serveur admin-users ;
--   - les ~45 endroits de l'ecran ou « admin » doit devenir « admin ou manager »
--     (⚠ SAUF l'ecran Sante, qui reste ADMIN SEUL -- exception voulue par Frederic,
--      tandis que l'outil Utilisateurs s'ouvre au manager, et il l'est DEJA cote
--      serveur : la fonction admin-users accepte ['admin','manager'] depuis
--      toujours, l. 62).
--
-- MEME METHODE QUE L2-A ET L2-B : le patch ne RECOPIE aucune fonction. Il la LIT
--   dans la base, verifie son empreinte, controle que l'ancre est UNIQUE et que le
--   texte n'est pas deja la, remplace, reexecute.
--
-- RETOUR ARRIERE : patch_l1_manager_et_rappro_2026-10-12_INVERSE.sql
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 0. GARDE-FOU : les 7 empreintes et les 3 regles attendues
-- ----------------------------------------------------------------------------
do $garde$
declare
    v_attendu jsonb := jsonb_build_object(
        'app_affaire_note_ecrire',           '23ab1ab09f19be18b82ca5c6f6430f67',
        'app_affaire_personne_ecart_fermer', 'f363f2f4336ae3e632bf3271865ab09a',
        'app_conditions_affaire_ecrire',     '84ec93cfdb8487a0206fca220fe04c79',
        'app_edit_affaire_optimistic',       'c70b690afb25c2af35f42bbf5959b2d4',
        'app_geste_affaire_optimistic',      'f2d551c1947077a9df77e4135882170d',
        'app_modifier_affaire_optimistic',   '29a02607ee212ec887040cd009b7d221',
        'app_console_can_request_job',       'e1435a48a47b4987109eefa7b9c34237'
    );
    v_nom text;
    v_trouve text;
begin
    for v_nom in select jsonb_object_keys(v_attendu) loop
        select md5(replace(pg_get_functiondef(p.oid), chr(13), '')) into v_trouve
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = v_nom limit 1;
        if v_trouve is distinct from (v_attendu ->> v_nom) then
            raise exception 'GARDE-FOU : % a change (trouve %, attendu %). Patch arrete.',
                v_nom, coalesce(v_trouve, '(introuvable)'), (v_attendu ->> v_nom);
        end if;
    end loop;

    if (select count(*) from pg_policies
         where schemaname = 'public' and cmd = 'SELECT'
           and tablename in ('app_rapprochement','app_rapprochement_score_history','app_relance_rapprochement')
           and md5(coalesce(qual, '')) = 'b326b5062b2f0e69046810717534cb09') <> 3 then
        raise exception 'GARDE-FOU : les 3 regles de rapprochement ne sont pas toutes a « true ». Patch arrete.';
    end if;
end
$garde$;


-- ============================================================================
-- 1. LES 6 FONCTIONS « AFFAIRE » : admin seul -> admin + manager
-- ============================================================================
do $affaires$
declare
    v_nom text;
    v_def text;
    v_occurrences int;
    v_faites int := 0;
begin
    foreach v_nom in array array[
        'app_affaire_note_ecrire', 'app_affaire_personne_ecart_fermer',
        'app_conditions_affaire_ecrire', 'app_edit_affaire_optimistic',
        'app_geste_affaire_optimistic', 'app_modifier_affaire_optimistic'
    ] loop
        select pg_get_functiondef(p.oid) into v_def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = v_nom;

        if position('is_app_manager_or_admin()' in v_def) > 0 then
            raise exception 'DEJA FAIT : % appelle deja is_app_manager_or_admin. Patch arrete.', v_nom;
        end if;

        v_occurrences := (length(v_def) - length(replace(v_def, 'is_app_admin()', ''))) / length('is_app_admin()');
        if v_occurrences <> 1 then
            raise exception 'ANCRE : % appelle is_app_admin() % fois, 1 attendue. Patch arrete.', v_nom, v_occurrences;
        end if;

        execute replace(v_def, 'is_app_admin()', 'is_app_manager_or_admin()');
        v_faites := v_faites + 1;
    end loop;

    raise notice 'AFFAIRES : % fonctions sur 6 ouvertes au manager.', v_faites;
end
$affaires$;


-- ============================================================================
-- 2. LE VIDEUR : le statut et l'archivage s'ouvrent au manager
-- ============================================================================
do $videur$
declare
    v_def text;
    v_ancre text := 'return coalesce(current_app_role = ''admin'', false);';
    v_nouveau text := 'return coalesce(current_app_role in (''admin'', ''manager''), false);';
    v_occurrences int;
begin
    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_can_request_job';

    if position(v_nouveau in v_def) > 0 then
        raise exception 'DEJA FAIT : le videur ouvre deja le statut au manager. Patch arrete.';
    end if;

    v_occurrences := (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre);
    if v_occurrences <> 1 then
        raise exception 'ANCRE : % occurrence(s) du cas particulier admin, 1 attendue. Patch arrete.', v_occurrences;
    end if;

    execute replace(v_def, v_ancre, v_nouveau);
    raise notice 'VIDEUR : le statut et l''archivage s''ouvrent au manager.';
end
$videur$;


-- ============================================================================
-- 3. LES RAPPROCHEMENTS : caches a un compte au perimetre reduit
--    ⚠ is_app_user_active() en tete : sans compte, on ne voit rien -- sinon
--    app_perimetre_courant() rendrait « reseau » par defaut et ouvrirait la porte.
-- ============================================================================

drop policy if exists app_rapprochement_sel on public.app_rapprochement;
create policy app_rapprochement_sel
    on public.app_rapprochement
    for select
    using (
        (select public.is_app_global_reader())
        or ((select public.is_app_user_active())
            and (select public.app_perimetre_courant()) = 'reseau')
    );

drop policy if exists app_rappro_hist_sel on public.app_rapprochement_score_history;
create policy app_rappro_hist_sel
    on public.app_rapprochement_score_history
    for select
    using (
        (select public.is_app_global_reader())
        or ((select public.is_app_user_active())
            and (select public.app_perimetre_courant()) = 'reseau')
    );

drop policy if exists app_rel_sel on public.app_relance_rapprochement;
create policy app_rel_sel
    on public.app_relance_rapprochement
    for select
    using (
        (select public.is_app_global_reader())
        or ((select public.is_app_user_active())
            and (select public.app_perimetre_courant()) = 'reseau')
    );


-- ============================================================================
-- 4. CONTROLE IMMEDIAT
-- ============================================================================
do $controle$
declare
    v_def text;
    v_affaires int;
    v_types int := 0;
    v_t text;
begin
    -- les 6 fonctions appellent bien la nouvelle
    select count(*) into v_affaires
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public'
       and p.proname in ('app_affaire_note_ecrire','app_affaire_personne_ecart_fermer',
                         'app_conditions_affaire_ecrire','app_edit_affaire_optimistic',
                         'app_geste_affaire_optimistic','app_modifier_affaire_optimistic')
       and position('is_app_manager_or_admin()' in pg_get_functiondef(p.oid)) > 0;
    if v_affaires <> 6 then
        raise exception 'CONTROLE : % fonctions affaire sur 6 ouvertes au manager.', v_affaires;
    end if;

    -- is_app_admin() n'est plus appelee par aucune des 6
    if (select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public'
           and p.proname in ('app_affaire_note_ecrire','app_affaire_personne_ecart_fermer',
                             'app_conditions_affaire_ecrire','app_edit_affaire_optimistic',
                             'app_geste_affaire_optimistic','app_modifier_affaire_optimistic')
           and position('is_app_admin()' in pg_get_functiondef(p.oid)) > 0) <> 0 then
        raise exception 'CONTROLE : une fonction affaire appelle encore is_app_admin().';
    end if;

    -- la fonction is_app_admin existe TOUJOURS (la regle des profils s'en sert)
    if not exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                    where n.nspname = 'public' and p.proname = 'is_app_admin') then
        raise exception 'CONTROLE : is_app_admin a disparu -- la regle de lecture des profils en depend.';
    end if;

    -- le videur : le manager a le statut, et la liste du commercial est INTACTE
    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_can_request_job';

    -- ⚠ ON CHERCHE LE RETURN DU CAS PARTICULIER, pas n'importe quel « admin, manager » :
    --   la phrase « current_app_role in ('admin', 'manager') » EXISTE DEJA dans le videur
    --   (c'est celle qui donne au manager tout le reste), donc la chercher ne prouvait
    --   RIEN. Erreur trouvee par la repetition du 12/10.
    if position('coalesce(current_app_role in (''admin'', ''manager''), false)' in v_def) = 0 then
        raise exception 'CONTROLE : le videur n''ouvre pas le statut au manager.';
    end if;
    -- et le temoin inverse : l'ancienne phrase doit avoir disparu
    if position('coalesce(current_app_role = ''admin'', false)' in v_def) > 0 then
        raise exception 'CONTROLE : le cas particulier « admin seul » est encore la.';
    end if;

    foreach v_t in array array[
        'prepare_document_cloud','upload_document_to_hektor','prepare_archived_annonce_detail',
        'prepare_historical_annonce_detail','sync_console_documents','relance_signature',
        'cancel_signature_procedure','update_hektor_annonce_fields','link_hektor_mandant',
        'unlink_hektor_mandant','create_hektor_mandant_contact','update_hektor_mandant_contact',
        'delete_document_from_hektor','generate_estimation_pdf','generate_mandat_document',
        'generate_cadastre_document','upload_hektor_photo','sync_hektor_photos',
        'matterport_action','create_hektor_mandat_auto_number','restore_hektor_annonce'
    ] loop
        if position(v_t in v_def) > 0 then v_types := v_types + 1; end if;
    end loop;
    if v_types <> 21 then
        raise exception 'CONTROLE : % types sur 21 pour le commercial -- la liste a bouge.', v_types;
    end if;

    -- ⚠ et archiver ne doit TOUJOURS pas etre dans la liste du commercial
    if position('''archive_hektor_annonce''' in
                substring(v_def from position('current_app_role = ''commercial''' in v_def))) > 0 then
        raise exception 'CONTROLE : archive_hektor_annonce est entre dans la liste du commercial.';
    end if;

    -- les 3 regles de rapprochement
    if (select count(*) from pg_policies
         where schemaname = 'public' and cmd = 'SELECT'
           and tablename in ('app_rapprochement','app_rapprochement_score_history','app_relance_rapprochement')
           and coalesce(qual, '') like '%app_perimetre_courant%') <> 3 then
        raise exception 'CONTROLE : les 3 regles de rapprochement ne suivent pas le perimetre.';
    end if;

    raise notice 'L1 OK : 6 fonctions affaire au manager, is_app_admin conservee, videur ouvert au manager, 21 types du commercial intacts, archivage toujours hors de sa liste, 3 regles de rapprochement posees.';
    raise notice 'RAPPEL : aucun compte manager n''existe et tous les comptes sont en « reseau » -- RIEN NE CHANGE POUR PERSONNE aujourd''hui.';
end
$controle$;


-- ---------- MESURES : APRES_PATCH ----------
insert into _l1_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'corps__' || p.proname, md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_affaire_note_ecrire', 'app_affaire_personne_ecart_fermer', 'app_conditions_affaire_ecrire', 'app_edit_affaire_optimistic', 'app_geste_affaire_optimistic', 'app_modifier_affaire_optimistic', 'app_console_can_request_job');

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'fonctions_affaire_ouvertes_au_manager', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_affaire_note_ecrire', 'app_affaire_personne_ecart_fermer', 'app_conditions_affaire_ecrire', 'app_edit_affaire_optimistic', 'app_geste_affaire_optimistic', 'app_modifier_affaire_optimistic')
   and position('is_app_manager_or_admin()' in pg_get_functiondef(p.oid)) > 0;

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'is_app_admin_existe_toujours',
       case when exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                          where n.nspname = 'public' and p.proname = 'is_app_admin')
            then 'oui' else '*** NON ***' end;

-- ⚠ ON CHERCHE LE CAS PARTICULIER, PAS N'IMPORTE QUEL « admin, manager ».
--   La phrase « current_app_role in ('admin', 'manager') » EXISTE DEJA dans le
--   videur : c'est celle qui donne au manager tout le reste. La chercher rendait
--   « oui » aux trois etapes et ne mesurait RIEN (erreur trouvee par la repetition
--   du 12/10 -- « chercher un mot n'est pas mesurer un comportement »).
--   La seule phrase qui change est celle du RETURN du cas particulier.
insert into _l1_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'statut_et_archivage_ouverts_au_manager',
       case when position('coalesce(current_app_role in (''admin'', ''manager''), false)' in d.def) > 0
            then 'oui' else 'non' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job' limit 1) d;

-- et le temoin inverse : l'ancienne phrase doit DISPARAITRE (1 -> 0)
insert into _l1_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'statut_et_archivage_encore_admin_seul',
       case when position('coalesce(current_app_role = ''admin'', false)' in d.def) > 0
            then 'oui' else 'non' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job' limit 1) d;

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'types_du_commercial_intacts', count(*)::text
  from unnest(array['prepare_document_cloud', 'upload_document_to_hektor', 'prepare_archived_annonce_detail', 'prepare_historical_annonce_detail', 'sync_console_documents', 'relance_signature', 'cancel_signature_procedure', 'update_hektor_annonce_fields', 'link_hektor_mandant', 'unlink_hektor_mandant', 'create_hektor_mandant_contact', 'update_hektor_mandant_contact', 'delete_document_from_hektor', 'generate_estimation_pdf', 'generate_mandat_document', 'generate_cadastre_document', 'upload_hektor_photo', 'sync_hektor_photos', 'matterport_action', 'create_hektor_mandat_auto_number', 'restore_hektor_annonce']) AS t(nom)
 where position(t.nom in (select pg_get_functiondef(p.oid)
                            from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                           where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
                           limit 1)) > 0;

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'archivage_entre_dans_la_liste_du_commercial',
       case when position('''archive_hektor_annonce''' in
                          substring(d.def from position('current_app_role = ''commercial''' in d.def))) > 0
            then '*** OUI, GRAVE ***' else 'non' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job' limit 1) d;

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'regles_rapprochement_qui_suivent_le_perimetre', count(*)::text
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename in ('app_rapprochement', 'app_rapprochement_score_history', 'app_relance_rapprochement')
   and coalesce(qual, '') like '%app_perimetre_courant%';

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'rapprochements_lisibles_sans_compte', count(*)::text
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relname in ('app_rapprochement', 'app_rapprochement_score_history', 'app_relance_rapprochement')
   and has_table_privilege('anon', c.oid, 'SELECT');

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'comptes_manager', count(*)::text
  from public.app_user_profile where role::text = 'manager';

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'comptes_hors_reseau', count(*)::text
  from public.app_user_profile p
 where coalesce(to_jsonb(p) ->> 'perimetre', 'reseau') <> 'reseau';


-- ############ LE VRAI INVERSE, CORPS EXACT ############
-- ============================================================================
-- RETOUR ARRIERE : L1 « manager = admin » et les rapprochements
-- Inverse exact de patch_l1_manager_et_rappro_2026-10-12.sql
--
-- Il refait l'operation contraire sur les 3 morceaux, puis VERIFIE qu'il
-- retombe exactement sur les 7 empreintes du 12/10 et sur les 3 regles « true ».
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. LES 6 FONCTIONS « AFFAIRE » reviennent a « admin seul »
-- ----------------------------------------------------------------------------
do $affaires$
declare
    v_nom text;
    v_def text;
begin
    foreach v_nom in array array[
        'app_affaire_note_ecrire', 'app_affaire_personne_ecart_fermer',
        'app_conditions_affaire_ecrire', 'app_edit_affaire_optimistic',
        'app_geste_affaire_optimistic', 'app_modifier_affaire_optimistic'
    ] loop
        select pg_get_functiondef(p.oid) into v_def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = v_nom;

        if position('is_app_manager_or_admin()' in v_def) = 0 then
            raise notice 'AFFAIRES : % est deja en admin seul.', v_nom;
        else
            execute replace(v_def, 'is_app_manager_or_admin()', 'is_app_admin()');
        end if;
    end loop;
    raise notice 'AFFAIRES : les 6 fonctions sont revenues a « admin seul ».';
end
$affaires$;


-- ----------------------------------------------------------------------------
-- 2. LE VIDEUR : le statut et l'archivage redeviennent « admin seul »
-- ----------------------------------------------------------------------------
do $videur$
declare
    v_def text;
    v_pose text := 'return coalesce(current_app_role in (''admin'', ''manager''), false);';
    v_origine text := 'return coalesce(current_app_role = ''admin'', false);';
begin
    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_can_request_job';

    if position(v_pose in v_def) = 0 then
        raise notice 'VIDEUR : rien a retirer.';
    else
        execute replace(v_def, v_pose, v_origine);
        raise notice 'VIDEUR : le statut et l''archivage redeviennent « admin seul ».';
    end if;
end
$videur$;


-- ----------------------------------------------------------------------------
-- 3. LES RAPPROCHEMENTS redeviennent visibles de tout compte connecte
-- ----------------------------------------------------------------------------
drop policy if exists app_rapprochement_sel on public.app_rapprochement;
create policy app_rapprochement_sel on public.app_rapprochement for select using (true);

drop policy if exists app_rappro_hist_sel on public.app_rapprochement_score_history;
create policy app_rappro_hist_sel on public.app_rapprochement_score_history for select using (true);

drop policy if exists app_rel_sel on public.app_relance_rapprochement;
create policy app_rel_sel on public.app_relance_rapprochement for select using (true);


-- ----------------------------------------------------------------------------
-- 4. CONTROLE : retombe-t-on sur l'etat du 12/10 ?
-- ----------------------------------------------------------------------------
do $controle$
declare
    v_attendu jsonb := jsonb_build_object(
        'app_affaire_note_ecrire',           '23ab1ab09f19be18b82ca5c6f6430f67',
        'app_affaire_personne_ecart_fermer', 'f363f2f4336ae3e632bf3271865ab09a',
        'app_conditions_affaire_ecrire',     '84ec93cfdb8487a0206fca220fe04c79',
        'app_edit_affaire_optimistic',       'c70b690afb25c2af35f42bbf5959b2d4',
        'app_geste_affaire_optimistic',      'f2d551c1947077a9df77e4135882170d',
        'app_modifier_affaire_optimistic',   '29a02607ee212ec887040cd009b7d221',
        'app_console_can_request_job',       'e1435a48a47b4987109eefa7b9c34237'
    );
    v_nom text;
    v_trouve text;
    v_ecarts int := 0;
begin
    for v_nom in select jsonb_object_keys(v_attendu) loop
        select md5(replace(pg_get_functiondef(p.oid), chr(13), '')) into v_trouve
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = v_nom limit 1;
        if v_trouve is distinct from (v_attendu ->> v_nom) then
            v_ecarts := v_ecarts + 1;
            raise notice 'ECART sur % : trouve %, attendu %', v_nom, v_trouve, (v_attendu ->> v_nom);
        end if;
    end loop;

    if (select count(*) from pg_policies
         where schemaname = 'public' and cmd = 'SELECT'
           and tablename in ('app_rapprochement','app_rapprochement_score_history','app_relance_rapprochement')
           and md5(coalesce(qual, '')) = 'b326b5062b2f0e69046810717534cb09') <> 3 then
        v_ecarts := v_ecarts + 1;
        raise notice 'ECART : les 3 regles de rapprochement ne sont pas revenues a « true ».';
    end if;

    if v_ecarts > 0 then
        raise exception 'RETOUR ARRIERE INCOMPLET : % ecart(s).', v_ecarts;
    end if;

    raise notice 'RETOUR ARRIERE COMPLET : les 7 fonctions et les 3 regles sont revenues a l''etat du 12/10.';
end
$controle$;


-- ---------- MESURES : APRES_INVERSE ----------
insert into _l1_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'corps__' || p.proname, md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_affaire_note_ecrire', 'app_affaire_personne_ecart_fermer', 'app_conditions_affaire_ecrire', 'app_edit_affaire_optimistic', 'app_geste_affaire_optimistic', 'app_modifier_affaire_optimistic', 'app_console_can_request_job');

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'fonctions_affaire_ouvertes_au_manager', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_affaire_note_ecrire', 'app_affaire_personne_ecart_fermer', 'app_conditions_affaire_ecrire', 'app_edit_affaire_optimistic', 'app_geste_affaire_optimistic', 'app_modifier_affaire_optimistic')
   and position('is_app_manager_or_admin()' in pg_get_functiondef(p.oid)) > 0;

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'is_app_admin_existe_toujours',
       case when exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                          where n.nspname = 'public' and p.proname = 'is_app_admin')
            then 'oui' else '*** NON ***' end;

-- ⚠ ON CHERCHE LE CAS PARTICULIER, PAS N'IMPORTE QUEL « admin, manager ».
--   La phrase « current_app_role in ('admin', 'manager') » EXISTE DEJA dans le
--   videur : c'est celle qui donne au manager tout le reste. La chercher rendait
--   « oui » aux trois etapes et ne mesurait RIEN (erreur trouvee par la repetition
--   du 12/10 -- « chercher un mot n'est pas mesurer un comportement »).
--   La seule phrase qui change est celle du RETURN du cas particulier.
insert into _l1_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'statut_et_archivage_ouverts_au_manager',
       case when position('coalesce(current_app_role in (''admin'', ''manager''), false)' in d.def) > 0
            then 'oui' else 'non' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job' limit 1) d;

-- et le temoin inverse : l'ancienne phrase doit DISPARAITRE (1 -> 0)
insert into _l1_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'statut_et_archivage_encore_admin_seul',
       case when position('coalesce(current_app_role = ''admin'', false)' in d.def) > 0
            then 'oui' else 'non' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job' limit 1) d;

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'types_du_commercial_intacts', count(*)::text
  from unnest(array['prepare_document_cloud', 'upload_document_to_hektor', 'prepare_archived_annonce_detail', 'prepare_historical_annonce_detail', 'sync_console_documents', 'relance_signature', 'cancel_signature_procedure', 'update_hektor_annonce_fields', 'link_hektor_mandant', 'unlink_hektor_mandant', 'create_hektor_mandant_contact', 'update_hektor_mandant_contact', 'delete_document_from_hektor', 'generate_estimation_pdf', 'generate_mandat_document', 'generate_cadastre_document', 'upload_hektor_photo', 'sync_hektor_photos', 'matterport_action', 'create_hektor_mandat_auto_number', 'restore_hektor_annonce']) AS t(nom)
 where position(t.nom in (select pg_get_functiondef(p.oid)
                            from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                           where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
                           limit 1)) > 0;

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'archivage_entre_dans_la_liste_du_commercial',
       case when position('''archive_hektor_annonce''' in
                          substring(d.def from position('current_app_role = ''commercial''' in d.def))) > 0
            then '*** OUI, GRAVE ***' else 'non' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job' limit 1) d;

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'regles_rapprochement_qui_suivent_le_perimetre', count(*)::text
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename in ('app_rapprochement', 'app_rapprochement_score_history', 'app_relance_rapprochement')
   and coalesce(qual, '') like '%app_perimetre_courant%';

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'rapprochements_lisibles_sans_compte', count(*)::text
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relname in ('app_rapprochement', 'app_rapprochement_score_history', 'app_relance_rapprochement')
   and has_table_privilege('anon', c.oid, 'SELECT');

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'comptes_manager', count(*)::text
  from public.app_user_profile where role::text = 'manager';

insert into _l1_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'comptes_hors_reseau', count(*)::text
  from public.app_user_profile p
 where coalesce(to_jsonb(p) ->> 'perimetre', 'reseau') <> 'reseau';

-- ============================================================================
-- L'ERREUR VOLONTAIRE : elle annule les trois etapes et rend les mesures
-- ============================================================================
do $final$
declare
    v_txt text;
    v_pas_revenus int;
    v_pas_changes int;
begin
    select count(*) into v_pas_revenus
      from _l1_mesures a
      join _l1_mesures z on z.cle = a.cle and z.etape = 'APRES_INVERSE'
     where a.etape = 'AVANT' and starts_with(a.cle, 'corps__')
       and a.valeur is distinct from z.valeur;

    select count(*) into v_pas_changes
      from _l1_mesures a
      join _l1_mesures p on p.cle = a.cle and p.etape = 'APRES_PATCH'
     where a.etape = 'AVANT' and starts_with(a.cle, 'corps__')
       and a.valeur = p.valeur;

    select string_agg(etape || ' | ' || cle || ' = ' || coalesce(valeur, '(null)'), chr(10)
                      order by ordre)
      into v_txt
      from _l1_mesures;

    raise exception E'ESSAI ANNULE -- RIEN N\'A ETE ECRIT.\n\nCORPS QUI NE REVIENNENT PAS A L\'ORIGINE : %   (0 attendu)\nCORPS QUE LE PATCH N\'A PAS CHANGES      : %   (0 attendu)\n\n%\n',
        v_pas_revenus, v_pas_changes, v_txt;
end
$final$;

-- jamais atteint
rollback;
