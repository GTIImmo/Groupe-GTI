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

begin;

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

commit;

-- ============================================================================
-- APRES LE COLLAGE -- a mesurer en empruntant l'identite de Melanie
--   PHOTOS    : 5 007 -> 441 018   (elle est en « reseau »)
--   DOCUMENTS : 4 565 -> 4 565     (INCHANGE)
--   et les deux doivent repondre SOUS LA SECONDE.
-- ============================================================================
