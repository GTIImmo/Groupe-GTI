-- ============================================================================
-- CHANTIER 2 -- LOT L2-B : CE QUE LE NEGOCIATEUR FAIT SEUL (2/2)
-- Patch du 12/10/2026, apres L2-A applique et controle le meme jour.
--
-- LES 9 DERNIERS GESTES OUVERTS AU NEGOCIATEUR, SUR SES BIENS
--   delete_document_from_hektor         supprimer un document chez Hektor
--   generate_estimation_pdf             generer un avis de valeur
--   generate_mandat_document            generer le PDF du mandat
--   generate_cadastre_document          generer le plan cadastral
--   upload_hektor_photo                 ajouter une photo
--   sync_hektor_photos                  resynchroniser les photos
--   matterport_action                   visite virtuelle
--   create_hektor_mandat_auto_number    demander un numero de mandat
--   restore_hektor_annonce              desarchiver
--
--   -> le commercial passera de 12 a 21 types.
--
-- ⚠ DEUX CHOSES A SAVOIR, MESUREES LE 12/10
--
--   1. SUPPRIMER UN DOCUMENT CHEZ HEKTOR EST DESTRUCTEUR : le geste efface le
--      document chez Hektor, le fichier sur notre serveur ET la copie dans le
--      cloud. Frederic l'a mis en « S + ses biens » apres objection (reponse 3
--      du 12/10) : c'est assume, ce n'est pas un oubli.
--
--   2. DESARCHIVER SERA SOUVENT REFUSE, ET C'EST NORMAL : le controle « ses
--      biens » cherche l'adresse du negociateur dans les 3 index, et
--      23 412 archives sur 35 318 N'EN PORTENT AUCUNE (irreparable : 22 649
--      n'ont meme pas d'identifiant). Melanie pourra desarchiver 774 archives.
--      Les autres restent reservees a un admin ou un manager.
--      C'est la consequence directe de la decision Q1 option 3 (assumee).
--
-- CE QUI N'EST PAS TOUCHE
--   statut, archivage, transactions, commissions, supprimer une annonce : tous
--   restent fermes. Le PRIX reste sous demande (garde pose par L2-A, intact).
--   Le front : AUCUNE ligne -- les boutons sont deja visibles. Aucun deploiement.
--   Les workers : rien. Ils recevront les memes travaux, sous le nom du
--   negociateur en charge du bien (audit 2a, §D).
--
-- MEME METHODE QUE L2-A, et c'est elle qui garantit qu'on n'ecrase rien :
--   le patch ne RECOPIE pas la fonction. Il la LIT dans la base, verifie son
--   empreinte, controle que l'ancre est UNIQUE et que le texte n'est pas deja
--   la, insere APRES l'ancre, reexecute. Corps conserve au caractere pres.
--
-- RETOUR ARRIERE : patch_l2b_..._INVERSE.sql -- il retire les 9 types et verifie
--   qu'il retombe sur l'empreinte laissee par L2-A.
-- ============================================================================

begin;

-- ----------------------------------------------------------------------------
-- 0. GARDE-FOU : on part bien de l'etat laisse par L2-A
-- ----------------------------------------------------------------------------
do $garde$
declare
    v_trouve text;
    v_attendu text := '7eea707fd7bd93b9f34473d57b5371fa';
begin
    select md5(replace(pg_get_functiondef(p.oid), chr(13), '')) into v_trouve
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
     limit 1;

    if v_trouve is null then
        raise exception 'GARDE-FOU : le videur est introuvable. Patch arrete.';
    end if;
    if v_trouve <> v_attendu then
        raise exception 'GARDE-FOU : le videur n''est pas celui laisse par L2-A (trouve %, attendu %). Patch arrete.',
            v_trouve, v_attendu;
    end if;

    -- le garde du prix pose par L2-A doit etre encore la, dans les DEUX chemins
    if (select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public'
           and p.proname in ('app_edit_annonce_optimistic','app_console_create_update_annonce_job')
           and position('prix_sur_demande' in pg_get_functiondef(p.oid)) > 0) <> 2 then
        raise exception 'GARDE-FOU : le garde du prix de L2-A n''est plus dans les deux chemins. Patch arrete.';
    end if;
end
$garde$;


-- ============================================================================
-- 1. LE VIDEUR DES ANNONCES : les 9 derniers types rejoignent la liste
-- ============================================================================
do $ouvrir$
declare
    v_def text;
    v_ancre text := '''update_hektor_mandant_contact''';
    v_ajout text;
    v_occurrences int;
begin
    v_ajout := v_ancre || ','
        || chr(10) || '            ''delete_document_from_hektor'',''generate_estimation_pdf'','
        || chr(10) || '            ''generate_mandat_document'',''generate_cadastre_document'','
        || chr(10) || '            ''upload_hektor_photo'',''sync_hektor_photos'',''matterport_action'','
        || chr(10) || '            ''create_hektor_mandat_auto_number'',''restore_hektor_annonce''';

    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_can_request_job';

    if position('upload_hektor_photo' in v_def) > 0 then
        raise exception 'DEJA FAIT : le videur connait deja upload_hektor_photo. Patch arrete.';
    end if;

    v_occurrences := (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre);
    if v_occurrences <> 1 then
        raise exception 'ANCRE : % occurrence(s) de update_hektor_mandant_contact, 1 attendue. Patch arrete.', v_occurrences;
    end if;

    execute replace(v_def, v_ancre, v_ajout);
    raise notice 'VIDEUR : 9 types ajoutes a la liste du commercial (12 -> 21).';
end
$ouvrir$;


-- ============================================================================
-- 2. CONTROLE IMMEDIAT
-- ============================================================================
do $controle$
declare
    v_def text;
    v_types int := 0;
    v_t text;
begin
    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_can_request_job';

    -- les 21 types que le commercial doit connaitre (7 + 5 de L2-A + 9 de L2-B)
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
        raise exception 'CONTROLE : % types sur 21 dans la liste du commercial.', v_types;
    end if;

    -- statut et archivage restent reserves a l'admin
    if position('archive_hektor_annonce' in v_def) = 0
       or position('change_hektor_annonce_status' in v_def) = 0 then
        raise exception 'CONTROLE : le cas particulier admin (statut, archivage) a disparu.';
    end if;

    -- ⚠ et il ne faut PAS que archive_hektor_annonce soit entre dans la liste du
    --   commercial : il n'y figure que dans le cas particulier, AVANT la liste.
    if position('''archive_hektor_annonce''' in
                substring(v_def from position('current_app_role = ''commercial''' in v_def))) > 0 then
        raise exception 'CONTROLE : archive_hektor_annonce s''est retrouve dans la liste du commercial.';
    end if;

    -- le controle « ses biens » est toujours la
    if position('app_console_can_access_dossier' in v_def) = 0 then
        raise exception 'CONTROLE : le controle « ses biens » a disparu du videur.';
    end if;

    -- le garde du prix de L2-A est intact
    if (select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public'
           and p.proname in ('app_edit_annonce_optimistic','app_console_create_update_annonce_job')
           and position('prix_sur_demande' in pg_get_functiondef(p.oid)) > 0) <> 2 then
        raise exception 'CONTROLE : le garde du prix de L2-A a bouge.';
    end if;

    raise notice 'L2-B OK : 21 types pour le commercial, statut et archivage toujours admin seul, controle « ses biens » intact, garde du prix de L2-A intact.';
end
$controle$;

commit;

-- ============================================================================
-- APRES LE COLLAGE
--   1. relire l'empreinte du videur et la comparer a celle de la repetition ;
--   2. en empruntant l'identite de Melanie (lecture seule) : les 9 gestes
--      DOIVENT repondre « oui » sur SON bien et « non » sur celui d'un collegue,
--      et le statut comme l'archivage DOIVENT lui rester fermes ;
--   3. desarchiver : « oui » sur une archive QUI PORTE SON ADRESSE (774 pour
--      elle), « non » sur une archive sans adresse (23 412) -- c'est voulu ;
--   4. RIEN a redemarrer, RIEN a deployer.
-- ============================================================================
