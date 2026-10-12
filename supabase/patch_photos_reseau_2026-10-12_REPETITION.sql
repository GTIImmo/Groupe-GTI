-- ============================================================================
-- REPETITION -- LES PHOTOS SUIVENT LE BIEN
--
-- ⚠ CE SCRIPT N'ECRIT RIEN. Il joue le vrai patch, puis le vrai inverse, puis il
--   ECHOUE EXPRES pour tout annuler, et il affiche les mesures des trois etapes.
--
-- A COLLER dans l'editeur SQL :
--   https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
--
-- CE QU'IL FAUT VOIR A LA FIN :
--   ESSAI ANNULE -- RIEN N'A ETE ECRIT
--   REGLES QUI NE REVIENNENT PAS A L'ORIGINE : 0   (0 attendu)
--   REGLES QUE LE PATCH N'A PAS CHANGEES     : 0   (0 attendu)
--
--   AVANT          photos_suivent_le_perimetre                   = non
--                  photos_encore_sur_l_ancienne_fonction         = oui
--                  documents_en_forme_rapide                     = non
--                  documents_encore_sur_l_ancienne_fonction      = oui
--                  documents_suivent_le_perimetre_NE_DOIT_JAMAIS = non
--                  photos_lisibles_sans_compte                   = non
--
--   APRES_PATCH    photos_suivent_le_perimetre                   = oui  <<< BASCULE
--                  photos_encore_sur_l_ancienne_fonction         = non  <<< TEMOIN
--                  documents_en_forme_rapide                     = oui  <<< BASCULE
--                  documents_encore_sur_l_ancienne_fonction      = non  <<< TEMOIN
--                  documents_suivent_le_perimetre_NE_DOIT_JAMAIS = non  <<< LE PLUS IMPORTANT
--                  photos_lisibles_sans_compte                   = non  <<< chantier 1
--
--   APRES_INVERSE  identique a AVANT
--
-- ⚠ LES MESURES VONT PAR PAIRES et doivent basculer ENSEMBLE (non->oui et
--   oui->non). C'est la lecon du 12/10 : une mesure qui ne regarde qu'un sens
--   peut ne rien mesurer du tout.
--
-- ⚠ ET « documents_suivent_le_perimetre_NE_DOIT_JAMAIS » doit rester « non » AUX
--   TROIS ETAPES : le dossier d'un bien (mandat, diagnostics) reste prive, c'est
--   la decision de Frederic. Si cette ligne passe a OUI, on ne colle pas.
--
-- ⚠ Fichier ASSEMBLE par supabase/generer_repetition_photos.py.
-- ============================================================================

begin;

create temporary table _ph_mesures(
    ordre  serial,
    etape  text,
    cle    text,
    valeur text
) on commit drop;

-- ---------- MESURES : AVANT ----------
insert into _ph_mesures(etape, cle, valeur)
select 'AVANT', 'regle__' || tablename, md5(coalesce(qual, ''))
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT'
   and tablename in ('app_console_photo', 'app_console_document');

-- LES PHOTOS : la nouvelle phrase doit APPARAITRE...
insert into _ph_mesures(etape, cle, valeur)
select 'AVANT', 'photos_suivent_le_perimetre',
       case when position('app_mes_biens_selon_perimetre' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_photo' limit 1;

-- ...et l'ancienne DISPARAITRE (temoin inverse)
insert into _ph_mesures(etape, cle, valeur)
select 'AVANT', 'photos_encore_sur_l_ancienne_fonction',
       case when position('app_console_can_access_dossier' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_photo' limit 1;

-- LES DOCUMENTS : la forme rapide doit APPARAITRE...
insert into _ph_mesures(etape, cle, valeur)
select 'AVANT', 'documents_en_forme_rapide',
       case when position('app_mes_biens_portefeuille' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_document' limit 1;

-- ...l'ancienne DISPARAITRE...
insert into _ph_mesures(etape, cle, valeur)
select 'AVANT', 'documents_encore_sur_l_ancienne_fonction',
       case when position('app_console_can_access_dossier' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_document' limit 1;

-- ...et SURTOUT : les documents NE DOIVENT JAMAIS suivre le perimetre.
--    C'est le controle qui protege la decision « le dossier reste prive ».
insert into _ph_mesures(etape, cle, valeur)
select 'AVANT', 'documents_suivent_le_perimetre_NE_DOIT_JAMAIS',
       case when position('app_perimetre_courant' in coalesce(qual, '')) > 0
            then '*** OUI, GRAVE ***' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_document' limit 1;

insert into _ph_mesures(etape, cle, valeur)
select 'AVANT', 'photos_lisibles_sans_compte',
       case when has_table_privilege('anon', c.oid, 'SELECT') then '*** OUI ***' else 'non' end
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relname = 'app_console_photo';


-- ############ LE VRAI PATCH, CORPS EXACT ############
-- ============================================================================
-- CHANTIER 2 -- LES PHOTOS SUIVENT LE BIEN, PAS LE DOSSIER
-- Patch du 12/10/2026. Decision de Frederic : « fais les photos tout le reseau
-- pour les negociateurs ».
--
-- POURQUOI : une PHOTO est la vitrine du bien, un DOCUMENT est son dossier.
--   Les deux etaient ranges ensemble, avec la meme regle « ses biens » -- donc un
--   negociateur voyait l'annonce d'un collegue SANS AUCUNE PHOTO, ce qui la rend
--   inutilisable pour proposer le bien a un acquereur.
--   ⚠ Et cela ne respectait pas la grille de Frederic, qui disait depuis le debut
--   « voir les photos = tout le reseau ». L4 n'avait pas touche aux photos : c'est
--   un ecart que je n'avais pas releve, trouve le 12/10 en repondant a sa question
--   sur l'agent commercial.
--
-- CE QUE CA CHANGE -- mesure du 12/10
--   PHOTOS     441 018 au total. Melanie en voyait 5 007 (ses biens).
--              Apres : 441 018 (tout le reseau, puisqu'elle est en « reseau »).
--   DOCUMENTS  156 300 au total. Melanie en voit 4 565 (ses biens).
--              Apres : 4 565 -- INCHANGE. Le dossier reste prive.
--
-- DEUX MORCEAUX
--   1. LES PHOTOS suivent le bien : visibles sur tout le reseau, et abaissables
--      par la case « perimetre » comme les annonces.
--   2. LES DOCUMENTS gardent EXACTEMENT la meme portee (« ses biens », toujours),
--      mais passent a la forme rapide -- celle de L4-bis. ⚠ AUCUN changement de
--      comportement : seulement la vitesse. Aujourd'hui leur regle appelle une
--      fonction UNE FOIS PAR LIGNE sur 156 300 lignes, le defaut corrige ce matin.
--
-- LES WORKERS : rien. service_role porte rolbypassrls.
-- LE FRONT : rien. Aucun deploiement.
--
-- RETOUR ARRIERE : patch_photos_reseau_2026-10-12_INVERSE.sql
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 0. GARDE-FOU : les deux regles doivent etre celles du 12/10
-- ----------------------------------------------------------------------------
do $garde$
begin
    if (select count(*) from pg_policies
         where schemaname = 'public' and cmd = 'SELECT'
           and tablename in ('app_console_photo', 'app_console_document')
           and md5(coalesce(qual, '')) = 'bbd47dafebf6cada5d990b659902fa4a') <> 2 then
        raise exception 'GARDE-FOU : les regles des photos et des documents ne sont pas celles du 12/10. Patch arrete.';
    end if;

    -- les deux ensembles de L4-bis doivent exister : les nouvelles regles s'en servent
    if (select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public'
           and p.proname in ('app_mes_biens_portefeuille', 'app_mes_biens_selon_perimetre')) <> 2 then
        raise exception 'GARDE-FOU : les 2 ensembles de L4-bis sont absents. Patch arrete.';
    end if;
end
$garde$;


-- ============================================================================
-- 1. LES PHOTOS SUIVENT LE BIEN
--    reseau       -> toutes les photos du reseau
--    agence       -> celles de son agence
--    portefeuille -> celles de ses biens
-- ============================================================================
drop policy if exists app_console_photo_select_scope on public.app_console_photo;
create policy app_console_photo_select_scope
    on public.app_console_photo
    for select
    using (
        (select public.is_app_global_reader())
        or (select public.app_perimetre_courant()) = 'reseau'
        or app_dossier_id in (select m.id from public.app_mes_biens_selon_perimetre() m)
        or hektor_annonce_id in (select m.hid from public.app_mes_biens_selon_perimetre() m)
    );


-- ============================================================================
-- 2. LES DOCUMENTS RESTENT « SES BIENS » -- meme portee, forme rapide
--    (c'est la correction de L4-bis appliquee ici : l'ensemble est calcule UNE
--     FOIS au lieu d'une fonction appelee par ligne)
-- ============================================================================
drop policy if exists app_console_document_select_scope on public.app_console_document;
create policy app_console_document_select_scope
    on public.app_console_document
    for select
    using (
        (select public.is_app_global_reader())
        or app_dossier_id in (select m.id from public.app_mes_biens_portefeuille() m)
        or hektor_annonce_id in (select m.hid from public.app_mes_biens_portefeuille() m)
    );


-- ============================================================================
-- 3. CONTROLE IMMEDIAT
-- ============================================================================
do $controle$
declare
    v_photo text;
    v_doc text;
begin
    select coalesce(qual, '') into v_photo
      from pg_policies
     where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_photo' limit 1;
    select coalesce(qual, '') into v_doc
      from pg_policies
     where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_document' limit 1;

    -- les PHOTOS suivent le perimetre (la nouvelle phrase apparait)
    if position('app_perimetre_courant' in v_photo) = 0 then
        raise exception 'CONTROLE : les photos ne suivent pas le perimetre.';
    end if;
    if position('app_mes_biens_selon_perimetre' in v_photo) = 0 then
        raise exception 'CONTROLE : les photos n''utilisent pas l''ensemble du perimetre.';
    end if;
    -- TEMOIN INVERSE : l'ancienne phrase a disparu
    if position('app_console_can_access_dossier' in v_photo) > 0 then
        raise exception 'CONTROLE : les photos appellent encore l''ancienne fonction.';
    end if;

    -- les DOCUMENTS restent « ses biens » : PAS de perimetre, l'ensemble strict
    if position('app_perimetre_courant' in v_doc) > 0 then
        raise exception 'CONTROLE : les documents suivent le perimetre -- ils doivent rester « ses biens » TOUJOURS.';
    end if;
    if position('app_mes_biens_portefeuille' in v_doc) = 0 then
        raise exception 'CONTROLE : les documents n''utilisent pas l''ensemble « ses biens ».';
    end if;
    -- TEMOIN INVERSE
    if position('app_console_can_access_dossier' in v_doc) > 0 then
        raise exception 'CONTROLE : les documents appellent encore l''ancienne fonction.';
    end if;

    raise notice 'PHOTOS OK : elles suivent le bien (reseau par defaut, abaissable par le perimetre).';
    raise notice 'DOCUMENTS OK : toujours « ses biens », mais en forme rapide.';
end
$controle$;


-- ============================================================================
-- APRES LE COLLAGE -- a mesurer en empruntant l'identite de Melanie
--   PHOTOS    : 5 007 -> 441 018   (elle est en « reseau »)
--   DOCUMENTS : 4 565 -> 4 565     (INCHANGE)
--   et les deux doivent repondre SOUS LA SECONDE.
-- ============================================================================

-- ---------- MESURES : APRES_PATCH ----------
insert into _ph_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'regle__' || tablename, md5(coalesce(qual, ''))
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT'
   and tablename in ('app_console_photo', 'app_console_document');

-- LES PHOTOS : la nouvelle phrase doit APPARAITRE...
insert into _ph_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'photos_suivent_le_perimetre',
       case when position('app_mes_biens_selon_perimetre' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_photo' limit 1;

-- ...et l'ancienne DISPARAITRE (temoin inverse)
insert into _ph_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'photos_encore_sur_l_ancienne_fonction',
       case when position('app_console_can_access_dossier' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_photo' limit 1;

-- LES DOCUMENTS : la forme rapide doit APPARAITRE...
insert into _ph_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'documents_en_forme_rapide',
       case when position('app_mes_biens_portefeuille' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_document' limit 1;

-- ...l'ancienne DISPARAITRE...
insert into _ph_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'documents_encore_sur_l_ancienne_fonction',
       case when position('app_console_can_access_dossier' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_document' limit 1;

-- ...et SURTOUT : les documents NE DOIVENT JAMAIS suivre le perimetre.
--    C'est le controle qui protege la decision « le dossier reste prive ».
insert into _ph_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'documents_suivent_le_perimetre_NE_DOIT_JAMAIS',
       case when position('app_perimetre_courant' in coalesce(qual, '')) > 0
            then '*** OUI, GRAVE ***' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_document' limit 1;

insert into _ph_mesures(etape, cle, valeur)
select 'APRES_PATCH', 'photos_lisibles_sans_compte',
       case when has_table_privilege('anon', c.oid, 'SELECT') then '*** OUI ***' else 'non' end
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relname = 'app_console_photo';


-- ############ LE VRAI INVERSE, CORPS EXACT ############
-- ============================================================================
-- RETOUR ARRIERE : les photos redeviennent « ses biens »
-- Inverse exact de patch_photos_reseau_2026-10-12.sql
--
-- Il remet les DEUX regles telles qu'elles etaient le 12/10 (meme condition pour
-- les photos et les documents, empreinte bbd47dafebf6cada5d990b659902fa4a) et le
-- verifie.
--
-- ⚠ Il remet donc aussi le defaut : un negociateur ne verra plus les photos du
--    bien d'un collegue, et la regle des documents redeviendra lente sur un
--    comptage global. C'est volontaire : un retour arriere rend l'etat precedent,
--    defauts compris.
-- ============================================================================


drop policy if exists app_console_photo_select_scope on public.app_console_photo;
create policy app_console_photo_select_scope
    on public.app_console_photo
    for select
    using (app_console_can_access_dossier(app_dossier_id, hektor_annonce_id));

drop policy if exists app_console_document_select_scope on public.app_console_document;
create policy app_console_document_select_scope
    on public.app_console_document
    for select
    using (app_console_can_access_dossier(app_dossier_id, hektor_annonce_id));

do $controle$
declare
    v_conformes int;
begin
    select count(*) into v_conformes
      from pg_policies
     where schemaname = 'public' and cmd = 'SELECT'
       and tablename in ('app_console_photo', 'app_console_document')
       and md5(coalesce(qual, '')) = 'bbd47dafebf6cada5d990b659902fa4a';

    if v_conformes <> 2 then
        raise exception 'RETOUR ARRIERE INCOMPLET : % regle(s) sur 2 a leur empreinte du 12/10.', v_conformes;
    end if;

    raise notice 'RETOUR ARRIERE COMPLET : photos et documents sont revenus a leur regle du 12/10.';
end
$controle$;


-- ---------- MESURES : APRES_INVERSE ----------
insert into _ph_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'regle__' || tablename, md5(coalesce(qual, ''))
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT'
   and tablename in ('app_console_photo', 'app_console_document');

-- LES PHOTOS : la nouvelle phrase doit APPARAITRE...
insert into _ph_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'photos_suivent_le_perimetre',
       case when position('app_mes_biens_selon_perimetre' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_photo' limit 1;

-- ...et l'ancienne DISPARAITRE (temoin inverse)
insert into _ph_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'photos_encore_sur_l_ancienne_fonction',
       case when position('app_console_can_access_dossier' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_photo' limit 1;

-- LES DOCUMENTS : la forme rapide doit APPARAITRE...
insert into _ph_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'documents_en_forme_rapide',
       case when position('app_mes_biens_portefeuille' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_document' limit 1;

-- ...l'ancienne DISPARAITRE...
insert into _ph_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'documents_encore_sur_l_ancienne_fonction',
       case when position('app_console_can_access_dossier' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_document' limit 1;

-- ...et SURTOUT : les documents NE DOIVENT JAMAIS suivre le perimetre.
--    C'est le controle qui protege la decision « le dossier reste prive ».
insert into _ph_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'documents_suivent_le_perimetre_NE_DOIT_JAMAIS',
       case when position('app_perimetre_courant' in coalesce(qual, '')) > 0
            then '*** OUI, GRAVE ***' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_document' limit 1;

insert into _ph_mesures(etape, cle, valeur)
select 'APRES_INVERSE', 'photos_lisibles_sans_compte',
       case when has_table_privilege('anon', c.oid, 'SELECT') then '*** OUI ***' else 'non' end
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relname = 'app_console_photo';

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
      from _ph_mesures a
      join _ph_mesures z on z.cle = a.cle and z.etape = 'APRES_INVERSE'
     where a.etape = 'AVANT' and starts_with(a.cle, 'regle__')
       and a.valeur is distinct from z.valeur;

    select count(*) into v_pas_changees
      from _ph_mesures a
      join _ph_mesures p on p.cle = a.cle and p.etape = 'APRES_PATCH'
     where a.etape = 'AVANT' and starts_with(a.cle, 'regle__')
       and a.valeur = p.valeur;

    select string_agg(etape || ' | ' || cle || ' = ' || coalesce(valeur, '(null)'), chr(10)
                      order by ordre)
      into v_txt
      from _ph_mesures;

    raise exception E'ESSAI ANNULE -- RIEN N\'A ETE ECRIT.\n\nREGLES QUI NE REVIENNENT PAS A L\'ORIGINE : %   (0 attendu)\nREGLES QUE LE PATCH N\'A PAS CHANGEES     : %   (0 attendu)\n\n%\n',
        v_pas_revenues, v_pas_changees, v_txt;
end
$final$;

-- jamais atteint
rollback;
