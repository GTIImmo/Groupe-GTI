-- ============================================================================
-- REPETITION DU LOT L2-A -- CE QUE LE NEGOCIATEUR FAIT SEUL (1/2)
--
-- ⚠ CE SCRIPT N'ECRIT RIEN. Il joue le vrai patch, puis le vrai inverse, puis il
--   ECHOUE EXPRES pour tout annuler, et il affiche les mesures des trois etapes.
--
-- A COLLER dans l'editeur SQL :
--   https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
--
-- CE QU'IL FAUT VOIR A LA FIN :
--   ESSAI ANNULE -- RIEN N'A ETE ECRIT
--   FONCTIONS QUI NE REVIENNENT PAS A LEUR CORPS D'ORIGINE : 0   (0 attendu)
--   FONCTIONS QUE LE PATCH N'A PAS CHANGEES                : 0   (0 attendu)
--
--   AVANT          types_connus_du_commercial         = 7
--                  garde_du_prix_dans_les_chemins     = 0
--                  statut_et_archivage_admin_seul     = oui
--                  controle_ses_biens_present         = oui
--                  fonctions_joignables_sans_compte   = 0
--
--   APRES_PATCH    types_connus_du_commercial         = 12  <<< les 5 gestes ouverts
--                  garde_du_prix_dans_les_chemins     = 2   <<< le prix est garde
--                                                             DANS LES DEUX chemins
--                  statut_et_archivage_admin_seul     = oui <<< pas touche
--                  controle_ses_biens_present         = oui <<< « ses biens » tient
--                  fonctions_joignables_sans_compte   = 0   <<< chantier 1 intact
--
--   APRES_INVERSE  identique a AVANT
--
-- ⚠ CE QUE CETTE REPETITION NE PROUVE PAS : qu'un negociateur peut vraiment
--   modifier un champ et vraiment pas le prix. Cela se verifie en empruntant son
--   identite, APRES le collage (lecture seule, transaction annulee).
--
-- ⚠ Fichier ASSEMBLE par supabase/generer_repetition_l2a.py.
--   NE PAS LE MODIFIER A LA MAIN : modifier les patchs, puis relancer le generateur.
-- ============================================================================

begin;

create temporary table _l2a_mesures(
    ordre  serial,
    etape  text,
    cle    text,
    valeur text
) on commit drop;

-- ---------- MESURES : AVANT ----------
-- ⚠ on compare l'empreinte SANS les retours chariot : un collage depuis Windows
--   en ajoute, et l'empreinte brute ne correspondrait jamais (piege du 08/10).
insert into _l2a_mesures(etape, cle, valeur)
select 'AVANT', 'corps__' || p.proname, md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_console_can_request_job', 'app_edit_annonce_optimistic', 'app_console_create_update_annonce_job');

insert into _l2a_mesures(etape, cle, valeur)
select 'AVANT', 'types_connus_du_commercial', count(*)::text
  from unnest(array['prepare_document_cloud', 'upload_document_to_hektor', 'prepare_archived_annonce_detail', 'prepare_historical_annonce_detail', 'sync_console_documents', 'relance_signature', 'cancel_signature_procedure', 'update_hektor_annonce_fields', 'link_hektor_mandant', 'unlink_hektor_mandant', 'create_hektor_mandant_contact', 'update_hektor_mandant_contact']) AS t(nom)
 where position(t.nom in (select pg_get_functiondef(p.oid)
                            from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                           where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
                           limit 1)) > 0;

insert into _l2a_mesures(etape, cle, valeur)
select 'AVANT', 'garde_du_prix_dans_les_chemins', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_edit_annonce_optimistic', 'app_console_create_update_annonce_job')
   and position('prix_sur_demande' in pg_get_functiondef(p.oid)) > 0;

insert into _l2a_mesures(etape, cle, valeur)
select 'AVANT', 'statut_et_archivage_admin_seul',
       case when position('archive_hektor_annonce' in d.def) > 0
             and position('change_hektor_annonce_status' in d.def) > 0
            then 'oui' else 'NON' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
         limit 1) d;

insert into _l2a_mesures(etape, cle, valeur)
select 'AVANT', 'controle_ses_biens_present',
       case when position('app_console_can_access_dossier' in d.def) > 0
            then 'oui' else 'NON' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
         limit 1) d;

insert into _l2a_mesures(etape, cle, valeur)
select 'AVANT', 'fonctions_joignables_sans_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_console_can_request_job', 'app_edit_annonce_optimistic', 'app_console_create_update_annonce_job')
   and has_function_privilege('anon', p.oid, 'EXECUTE');


-- ############ LE VRAI PATCH L2-A, CORPS EXACT ############
-- ============================================================================
-- CHANTIER 2 -- LOT L2-A : CE QUE LE NEGOCIATEUR FAIT SEUL (1/2)
-- Patch du 12/10/2026. Decoupage « B » choisi par Frederic : 5 gestes d'abord,
-- les 9 autres dans L2-B apres controle.
--
-- LES 5 GESTES OUVERTS AU NEGOCIATEUR, SUR SES BIENS
--   update_hektor_annonce_fields    modifier les champs  (⚠ SAUF LE PRIX)
--   link_hektor_mandant             rattacher un mandant
--   unlink_hektor_mandant           retirer un mandant
--   create_hektor_mandant_contact   creer un mandant
--   update_hektor_mandant_contact   modifier un mandant
--
-- LE PRIX RESTE SOUS DEMANDE (decision B1 de Frederic) : « modifier les champs »
--   est UN SEUL type de travail, donc le videur -- qui ne voit que le type, pas le
--   contenu -- ne peut pas l'arreter. Le garde se pose la ou le contenu est lu, et
--   ⭐ la fonction ISOLE DEJA LE PRIX dans une variable, avec ses TROIS cles
--   ('price', 'prix', 'ESTIMATION_MONTANT') et un controle de format juste apres.
--   On ajoute le garde A CET ENDROIT, et dans le SECOND CHEMIN (la fonction que
--   l'ecran n'appelle plus mais qui reste joignable) -- sinon le prix se contourne.
--
-- ⭐ COMMENT CE PATCH EVITE D'ECRASER QUOI QUE CE SOIT
--   Il ne RECOPIE aucune fonction. Il les LIT dans la base (pg_get_functiondef),
--   verifie leur empreinte, controle que l'ancre est unique et que le texte n'est
--   pas deja la, insere ses lignes APRES l'ancre, et reexecute. Le corps d'origine
--   est conserve au caractere pres : aucune transcription, donc aucune occasion de
--   perdre une ligne.
--
-- CE QUI N'EST PAS TOUCHE
--   statut et archivage : ils ont un cas particulier AVANT la liste, reserve a
--   l'admin. Les repartitions de commission : attachees au droit « changer le
--   statut », qu'on n'ouvre pas. Le front : AUCUNE ligne -- les boutons sont deja
--   visibles, c'est la base qui refusait. Donc AUCUN deploiement.
--
-- LES WORKERS : rien a faire. Ils recevront les memes travaux, et l'ecriture chez
--   Hektor part deja SOUS LE NOM DU NEGOCIATEUR EN CHARGE DU BIEN (audit 2a, §D).
--
-- DECISION AMENDEE LE 12/10 : desarchiver passe de « tout le reseau » a « ses
--   biens », comme les 13 autres gestes (Frederic, option 1). Il part donc dans
--   L2-B sans controle special.
--
-- RETOUR ARRIERE : patch_l2a_..._INVERSE.sql -- il RETIRE le texte insere et
--   verifie qu'il retombe EXACTEMENT sur les empreintes d'origine ci-dessous.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 0. LES EMPREINTES D'ORIGINE, mesurees le 12/10 (sans les retours chariot
--    Windows : un collage les ajoute et l'empreinte brute ne correspondrait pas)
-- ----------------------------------------------------------------------------
do $garde$
declare
    v_attendu jsonb := jsonb_build_object(
        'app_console_can_request_job',           '7143dda690cf82c8c4e65210aa40f483',
        'app_edit_annonce_optimistic',           '45110168d91358c7790032b5085e1314',
        'app_console_create_update_annonce_job', 'cc039ade1eca389ecde206ec5df54b21'
    );
    v_nom text;
    v_trouve text;
begin
    for v_nom in select jsonb_object_keys(v_attendu) loop
        select md5(replace(pg_get_functiondef(p.oid), chr(13), '')) into v_trouve
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = v_nom
         limit 1;
        if v_trouve is null then
            raise exception 'GARDE-FOU : fonction % introuvable. Patch arrete.', v_nom;
        end if;
        if v_trouve <> (v_attendu ->> v_nom) then
            raise exception 'GARDE-FOU : le corps de % a change (trouve %, attendu %). Une autre session est passee : patch arrete.',
                v_nom, v_trouve, (v_attendu ->> v_nom);
        end if;
    end loop;
end
$garde$;


-- ============================================================================
-- 1. LE VIDEUR DES ANNONCES : les 5 types rejoignent la liste du commercial
-- ============================================================================
do $ouvrir$
declare
    v_def text;
    v_ancre text := '''cancel_signature_procedure''';
    v_ajout text;
    v_occurrences int;
begin
    v_ajout := v_ancre || ','
        || chr(10) || '            ''update_hektor_annonce_fields'',''link_hektor_mandant'',''unlink_hektor_mandant'','
        || chr(10) || '            ''create_hektor_mandant_contact'',''update_hektor_mandant_contact''';

    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_can_request_job';

    if position('update_hektor_annonce_fields' in v_def) > 0 then
        raise exception 'DEJA FAIT : le videur connait deja update_hektor_annonce_fields. Patch arrete.';
    end if;

    v_occurrences := (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre);
    if v_occurrences <> 1 then
        raise exception 'ANCRE : % occurrence(s) de cancel_signature_procedure, 1 attendue. Patch arrete.', v_occurrences;
    end if;

    execute replace(v_def, v_ancre, v_ajout);
    raise notice 'VIDEUR : 5 types ajoutes a la liste du commercial (7 -> 12).';
end
$ouvrir$;


-- ============================================================================
-- 2. LE GARDE DU PRIX, chemin de la saisie (celui que l'ecran utilise)
--    Insere JUSTE APRES le controle de format du prix, qui existe deja.
-- ============================================================================
do $prix1$
declare
    v_def text;
    v_ancre text := 'raise exception ''invalid_price'' using errcode=''22023''; end if;';
    v_ajout text;
    v_occurrences int;
begin
    v_ajout := v_ancre
        || chr(10) || '-- L2-A (12/10/2026) : le PRIX reste sous demande pour un negociateur'
        || chr(10) || '-- (decision B1 de Frederic). Il passe par « Demande de baisse de prix ».'
        || chr(10) || 'if v_price is not null and public.app_console_current_role() = ''commercial'' then'
        || chr(10) || 'raise exception ''prix_sur_demande'' using errcode=''42501''; end if;';

    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_edit_annonce_optimistic';

    if position('prix_sur_demande' in v_def) > 0 then
        raise exception 'DEJA FAIT : le garde du prix est deja dans la saisie. Patch arrete.';
    end if;

    v_occurrences := (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre);
    if v_occurrences <> 1 then
        raise exception 'ANCRE : % occurrence(s) du controle invalid_price, 1 attendue. Patch arrete.', v_occurrences;
    end if;

    execute replace(v_def, v_ancre, v_ajout);
    raise notice 'SAISIE : le garde du prix est pose.';
end
$prix1$;


-- ============================================================================
-- 3. LE GARDE DU PRIX, second chemin (l'ecran ne l'appelle plus -- 0 occurrence
--    dans App.tsx -- mais la fonction reste joignable par un compte connecte,
--    donc sans ce garde le prix se contournerait)
-- ============================================================================
do $prix2$
declare
    v_def text;
    v_ancre text := 'raise exception ''forbidden_update_annonce'' using errcode = ''42501'';';
    v_ajout text;
    v_occurrences int;
begin
    v_ajout := v_ancre
        || chr(10) || '    end if;'
        || chr(10) || ''
        || chr(10) || '    -- L2-A (12/10/2026) : meme garde du prix que dans la saisie optimiste.'
        || chr(10) || '    if public.app_console_current_role() = ''commercial'''
        || chr(10) || '       and coalesce(nullif(trim(update_fields->>''price''), ''''),'
        || chr(10) || '                    nullif(trim(update_fields->>''prix''), ''''),'
        || chr(10) || '                    nullif(trim(update_fields->>''ESTIMATION_MONTANT''), '''')) is not null then'
        || chr(10) || '        raise exception ''prix_sur_demande'' using errcode = ''42501'';';

    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_create_update_annonce_job';

    if position('prix_sur_demande' in v_def) > 0 then
        raise exception 'DEJA FAIT : le garde du prix est deja dans le second chemin. Patch arrete.';
    end if;

    v_occurrences := (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre);
    if v_occurrences <> 1 then
        raise exception 'ANCRE : % occurrence(s) de forbidden_update_annonce, 1 attendue. Patch arrete.', v_occurrences;
    end if;

    execute replace(v_def, v_ancre, v_ajout);
    raise notice 'SECOND CHEMIN : le garde du prix est pose.';
end
$prix2$;


-- ============================================================================
-- 4. CONTROLE IMMEDIAT
-- ============================================================================
do $controle$
declare
    v_def_videur text;
    v_types int := 0;
    v_t text;
begin
    select pg_get_functiondef(p.oid) into v_def_videur
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_can_request_job';

    -- les 12 types que le commercial doit connaitre (7 anciens + 5 neufs)
    foreach v_t in array array[
        'prepare_document_cloud','upload_document_to_hektor','prepare_archived_annonce_detail',
        'prepare_historical_annonce_detail','sync_console_documents','relance_signature',
        'cancel_signature_procedure','update_hektor_annonce_fields','link_hektor_mandant',
        'unlink_hektor_mandant','create_hektor_mandant_contact','update_hektor_mandant_contact'
    ] loop
        if position(v_t in v_def_videur) > 0 then v_types := v_types + 1; end if;
    end loop;
    if v_types <> 12 then
        raise exception 'CONTROLE : % types sur 12 dans la liste du commercial.', v_types;
    end if;

    -- statut et archivage restent reserves a l'admin : le cas particulier est intact
    if position('archive_hektor_annonce' in v_def_videur) = 0
       or position('change_hektor_annonce_status' in v_def_videur) = 0 then
        raise exception 'CONTROLE : le cas particulier admin (statut, archivage) a disparu.';
    end if;

    -- le garde du prix est dans LES DEUX chemins
    if (select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public'
           and p.proname in ('app_edit_annonce_optimistic','app_console_create_update_annonce_job')
           and position('prix_sur_demande' in pg_get_functiondef(p.oid)) > 0) <> 2 then
        raise exception 'CONTROLE : le garde du prix n''est pas dans les deux chemins.';
    end if;

    -- le controle « ses biens » est toujours la
    if position('app_console_can_access_dossier' in v_def_videur) = 0 then
        raise exception 'CONTROLE : le controle « ses biens » a disparu du videur.';
    end if;

    raise notice 'L2-A OK : 12 types pour le commercial, statut et archivage toujours admin seul, garde du prix dans les 2 chemins, controle « ses biens » intact.';
end
$controle$;


-- ============================================================================
-- APRES LE COLLAGE
--   1. relire les 3 empreintes et les comparer a celles de la repetition ;
--   2. en empruntant l'identite de Melanie (lecture seule) : elle DOIT pouvoir
--      demander une modification de champ sur SON bien, NE DOIT PAS pouvoir
--      toucher au prix, NE DOIT PAS pouvoir modifier le bien d'un collegue, et
--      le statut comme l'archivage DOIVENT lui rester fermes ;
--   3. ⚠ un essai REEL (qui ecrit chez Hektor) demande l'accord de Frederic ;
--   4. RIEN a redemarrer, RIEN a deployer.
-- ============================================================================

-- ---------- MESURES : APRES_PATCH ----------
-- ⚠ on compare l'empreinte SANS les retours chariot : un collage depuis Windows
--   en ajoute, et l'empreinte brute ne correspondrait jamais (piege du 08/10).
insert into _l2a_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'corps__' || p.proname, md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_console_can_request_job', 'app_edit_annonce_optimistic', 'app_console_create_update_annonce_job');

insert into _l2a_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'types_connus_du_commercial', count(*)::text
  from unnest(array['prepare_document_cloud', 'upload_document_to_hektor', 'prepare_archived_annonce_detail', 'prepare_historical_annonce_detail', 'sync_console_documents', 'relance_signature', 'cancel_signature_procedure', 'update_hektor_annonce_fields', 'link_hektor_mandant', 'unlink_hektor_mandant', 'create_hektor_mandant_contact', 'update_hektor_mandant_contact']) AS t(nom)
 where position(t.nom in (select pg_get_functiondef(p.oid)
                            from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                           where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
                           limit 1)) > 0;

insert into _l2a_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'garde_du_prix_dans_les_chemins', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_edit_annonce_optimistic', 'app_console_create_update_annonce_job')
   and position('prix_sur_demande' in pg_get_functiondef(p.oid)) > 0;

insert into _l2a_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'statut_et_archivage_admin_seul',
       case when position('archive_hektor_annonce' in d.def) > 0
             and position('change_hektor_annonce_status' in d.def) > 0
            then 'oui' else 'NON' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
         limit 1) d;

insert into _l2a_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'controle_ses_biens_present',
       case when position('app_console_can_access_dossier' in d.def) > 0
            then 'oui' else 'NON' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
         limit 1) d;

insert into _l2a_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'fonctions_joignables_sans_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_console_can_request_job', 'app_edit_annonce_optimistic', 'app_console_create_update_annonce_job')
   and has_function_privilege('anon', p.oid, 'EXECUTE');


-- ############ LE VRAI INVERSE, CORPS EXACT ############
-- ============================================================================
-- RETOUR ARRIERE DU LOT L2-A
-- Inverse exact de patch_l2a_negociateur_champs_mandants_2026-10-12.sql
--
-- Il fait l'operation CONTRAIRE : il RETIRE le texte insere, en reconstruisant
-- mot pour mot le meme texte que le patch, puis il VERIFIE que les trois corps
-- retombent EXACTEMENT sur leurs empreintes d'origine du 12/10.
--
-- ⭐ C'est ce controle final qui le rend sur : si le texte retire n'etait pas
--    exactement celui insere, le remplacement ne change rien, l'empreinte ne
--    correspond pas, et le script S'ARRETE sans rien laisser a moitie defait.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. LE VIDEUR : les 5 types quittent la liste du commercial
-- ----------------------------------------------------------------------------
do $fermer$
declare
    v_def text;
    v_ancre text := '''cancel_signature_procedure''';
    v_ajout text;
begin
    v_ajout := v_ancre || ','
        || chr(10) || '            ''update_hektor_annonce_fields'',''link_hektor_mandant'',''unlink_hektor_mandant'','
        || chr(10) || '            ''create_hektor_mandant_contact'',''update_hektor_mandant_contact''';

    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_can_request_job';

    if position('update_hektor_annonce_fields' in v_def) = 0 then
        raise notice 'VIDEUR : rien a retirer, les 5 types ne sont pas la.';
    else
        execute replace(v_def, v_ajout, v_ancre);
        raise notice 'VIDEUR : les 5 types sont retires (12 -> 7).';
    end if;
end
$fermer$;


-- ----------------------------------------------------------------------------
-- 2. LE GARDE DU PRIX, chemin de la saisie
-- ----------------------------------------------------------------------------
do $prix1$
declare
    v_def text;
    v_ancre text := 'raise exception ''invalid_price'' using errcode=''22023''; end if;';
    v_ajout text;
begin
    v_ajout := v_ancre
        || chr(10) || '-- L2-A (12/10/2026) : le PRIX reste sous demande pour un negociateur'
        || chr(10) || '-- (decision B1 de Frederic). Il passe par « Demande de baisse de prix ».'
        || chr(10) || 'if v_price is not null and public.app_console_current_role() = ''commercial'' then'
        || chr(10) || 'raise exception ''prix_sur_demande'' using errcode=''42501''; end if;';

    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_edit_annonce_optimistic';

    if position('prix_sur_demande' in v_def) = 0 then
        raise notice 'SAISIE : rien a retirer.';
    else
        execute replace(v_def, v_ajout, v_ancre);
        raise notice 'SAISIE : le garde du prix est retire.';
    end if;
end
$prix1$;


-- ----------------------------------------------------------------------------
-- 3. LE GARDE DU PRIX, second chemin
-- ----------------------------------------------------------------------------
do $prix2$
declare
    v_def text;
    v_ancre text := 'raise exception ''forbidden_update_annonce'' using errcode = ''42501'';';
    v_ajout text;
begin
    v_ajout := v_ancre
        || chr(10) || '    end if;'
        || chr(10) || ''
        || chr(10) || '    -- L2-A (12/10/2026) : meme garde du prix que dans la saisie optimiste.'
        || chr(10) || '    if public.app_console_current_role() = ''commercial'''
        || chr(10) || '       and coalesce(nullif(trim(update_fields->>''price''), ''''),'
        || chr(10) || '                    nullif(trim(update_fields->>''prix''), ''''),'
        || chr(10) || '                    nullif(trim(update_fields->>''ESTIMATION_MONTANT''), '''')) is not null then'
        || chr(10) || '        raise exception ''prix_sur_demande'' using errcode = ''42501'';';

    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_create_update_annonce_job';

    if position('prix_sur_demande' in v_def) = 0 then
        raise notice 'SECOND CHEMIN : rien a retirer.';
    else
        execute replace(v_def, v_ajout, v_ancre);
        raise notice 'SECOND CHEMIN : le garde du prix est retire.';
    end if;
end
$prix2$;


-- ----------------------------------------------------------------------------
-- 4. CONTROLE : les 3 corps retombent-ils sur leurs empreintes d'origine ?
-- ----------------------------------------------------------------------------
do $controle$
declare
    v_attendu jsonb := jsonb_build_object(
        'app_console_can_request_job',           '7143dda690cf82c8c4e65210aa40f483',
        'app_edit_annonce_optimistic',           '45110168d91358c7790032b5085e1314',
        'app_console_create_update_annonce_job', 'cc039ade1eca389ecde206ec5df54b21'
    );
    v_nom text;
    v_trouve text;
    v_ecarts int := 0;
begin
    for v_nom in select jsonb_object_keys(v_attendu) loop
        select md5(replace(pg_get_functiondef(p.oid), chr(13), '')) into v_trouve
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = v_nom
         limit 1;
        if v_trouve is distinct from (v_attendu ->> v_nom) then
            v_ecarts := v_ecarts + 1;
            raise notice 'ECART sur % : trouve %, attendu %', v_nom, v_trouve, (v_attendu ->> v_nom);
        end if;
    end loop;

    if v_ecarts > 0 then
        raise exception 'RETOUR ARRIERE INCOMPLET : % fonction(s) ne retombent pas sur leur corps d''origine.', v_ecarts;
    end if;

    raise notice 'RETOUR ARRIERE COMPLET : les 3 fonctions sont revenues a leur corps du 12/10, a l''empreinte.';
end
$controle$;


-- ---------- MESURES : APRES_INVERSE ----------
-- ⚠ on compare l'empreinte SANS les retours chariot : un collage depuis Windows
--   en ajoute, et l'empreinte brute ne correspondrait jamais (piege du 08/10).
insert into _l2a_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'corps__' || p.proname, md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_console_can_request_job', 'app_edit_annonce_optimistic', 'app_console_create_update_annonce_job');

insert into _l2a_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'types_connus_du_commercial', count(*)::text
  from unnest(array['prepare_document_cloud', 'upload_document_to_hektor', 'prepare_archived_annonce_detail', 'prepare_historical_annonce_detail', 'sync_console_documents', 'relance_signature', 'cancel_signature_procedure', 'update_hektor_annonce_fields', 'link_hektor_mandant', 'unlink_hektor_mandant', 'create_hektor_mandant_contact', 'update_hektor_mandant_contact']) AS t(nom)
 where position(t.nom in (select pg_get_functiondef(p.oid)
                            from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                           where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
                           limit 1)) > 0;

insert into _l2a_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'garde_du_prix_dans_les_chemins', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_edit_annonce_optimistic', 'app_console_create_update_annonce_job')
   and position('prix_sur_demande' in pg_get_functiondef(p.oid)) > 0;

insert into _l2a_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'statut_et_archivage_admin_seul',
       case when position('archive_hektor_annonce' in d.def) > 0
             and position('change_hektor_annonce_status' in d.def) > 0
            then 'oui' else 'NON' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
         limit 1) d;

insert into _l2a_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'controle_ses_biens_present',
       case when position('app_console_can_access_dossier' in d.def) > 0
            then 'oui' else 'NON' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
         limit 1) d;

insert into _l2a_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'fonctions_joignables_sans_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('app_console_can_request_job', 'app_edit_annonce_optimistic', 'app_console_create_update_annonce_job')
   and has_function_privilege('anon', p.oid, 'EXECUTE');

-- ============================================================================
-- L'ERREUR VOLONTAIRE : elle annule les trois etapes et rend les mesures
-- ============================================================================
do $final$
declare
    v_txt text;
    v_pas_revenues int;
    v_pas_changees int;
begin
    select count(*) into v_pas_revenues
      from _l2a_mesures a
      join _l2a_mesures z on z.cle = a.cle and z.etape = 'APRES_INVERSE'
     where a.etape = 'AVANT' and starts_with(a.cle, 'corps__')
       and a.valeur is distinct from z.valeur;

    select count(*) into v_pas_changees
      from _l2a_mesures a
      join _l2a_mesures p on p.cle = a.cle and p.etape = 'APRES_PATCH'
     where a.etape = 'AVANT' and starts_with(a.cle, 'corps__')
       and a.valeur = p.valeur;

    select string_agg(etape || ' | ' || cle || ' = ' || coalesce(valeur, '(null)'), chr(10)
                      order by ordre)
      into v_txt
      from _l2a_mesures;

    raise exception E'ESSAI ANNULE -- RIEN N\'A ETE ECRIT.\n\nFONCTIONS QUI NE REVIENNENT PAS A LEUR CORPS D\'ORIGINE : %   (0 attendu)\nFONCTIONS QUE LE PATCH N\'A PAS CHANGEES                : %   (0 attendu)\n\n%\n',
        v_pas_revenues, v_pas_changees, v_txt;
end
$final$;

-- jamais atteint
rollback;
