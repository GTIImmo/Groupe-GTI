-- REGISTRE DES NÉGOCIATEURS, étape 3 « les menus » (04/11/2026) : LE N° DU COMPTE D'AGENCE SUR CHAQUE FICHE.
-- Audit : notice/AUDIT_REGISTRE_NEGOCIATEURS_2026-11-04.md §18 et §23. Frédéric : « OK 1 ET APRES 2 ».
-- POURQUOI : les menus de négociateurs (changer le négociateur d'un bien, créer un contact) envoient à Hektor le n° du
--   compte d'AGENCE de la fiche (`agence_id_user`, champs target_agency_id_user / hektorAgencyUserId). Le registre ne le
--   portait pas -- il ne peut pas se déduire : 18 agences, 18 comptes d'agence, mais le registre ne sait pas lequel va
--   avec quelle agence (mesuré le 04/11). Sans lui, les menus ne pouvaient pas lire le registre.
-- CE QUE ÇA FAIT :
--   1. une colonne `agence_id_user` sur app_negociateur_fiche (rien d'autre ne change) ;
--   2. remplie une fois depuis l'annuaire de cette nuit, par le n° de négociateur ;
--   3. la nuit la tient à jour comme les autres champs de la fiche (même recopie, même journal des changements) :
--      sept lignes de la fonction app_negociateur_registre_maintenir, modifiées EN PLACE à partir de la version en base
--      (empreinte vérifiée avant ; chaque ancre doit apparaître une seule fois, sinon ARRÊT sans rien changer).
-- Retour arrière : patch_registre_negociateurs_agence_user_2026-11-04_INVERSE.sql

do $garde$
begin
    if exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'app_negociateur_fiche' and column_name = 'agence_id_user') then
        raise exception '%', 'ARRET : la colonne agence_id_user existe déjà -- le patch a déjà été posé. Rien n''est changé.';
    end if;
    if md5(replace(pg_get_functiondef('public.app_negociateur_registre_maintenir(text[],boolean,integer)'::regprocedure), chr(13), '')) <> 'e68a3f86c3bce79845e4af577fcca2c0' then
        raise exception '%', 'ARRET : la fonction de nuit n''est plus celle attendue (empreinte e68a3f86) -- quelqu''un est passé avant. Rien n''est changé.';
    end if;
end
$garde$;

alter table public.app_negociateur_fiche add column agence_id_user text;
comment on column public.app_negociateur_fiche.agence_id_user is
  'N° Hektor du compte d''AGENCE de la fiche (annuaire : agence_id_user). Recopié chaque nuit. Envoyé à Hektor par les menus '
  '(changer le négociateur d''un bien, créer un contact). 04/11/2026.';

update public.app_negociateur_fiche f
   set agence_id_user = nullif(trim(d.agence_id_user::text), '')
  from public.app_hektor_negotiator_agency_directory d
 where f.sorte = 'fiche_negociateur'
   and f.hektor_negociateur_id = nullif(trim(d.hektor_negociateur_id::text), '');

do $fonction$
declare
    v text := replace(pg_get_functiondef('public.app_negociateur_registre_maintenir(text[],boolean,integer)'::regprocedure), chr(13), '');
    a text[] := array[
        $a$agence_nom, trim(coalesce(prenom, '') || ' ' || coalesce(nom, '')) as nom_vu, nullif(lower(trim(email)), '') as email,$a$,
        $a$insert into app_negociateur_fiche (app_personne_id, sorte, hektor_negociateur_id, hektor_user_id, hektor_agence_id, agence_nom, nom_vu, email_vu,$a$,
        $a$values (v_ad.o_personne, 'fiche_negociateur', r.n_id, r.u_id, r.agence_id, r.agence_nom, r.nom_vu, r.email, r.telephone, r.portable, r.actif,$a$,
        $a$('hektor_agence_id', c.hektor_agence_id, r.agence_id), ('telephone', c.telephone, r.telephone), ('portable', c.portable, r.portable),$a$,
        $a$set hektor_user_id = r.u_id, hektor_agence_id = r.agence_id, agence_nom = r.agence_nom, nom_vu = r.nom_vu, email_vu = r.email,$a$,
        $a$updated_at = case when (hektor_user_id, hektor_agence_id, agence_nom, nom_vu, email_vu, telephone, portable, actif_chez_hektor)$a$,
        $a$is distinct from (r.u_id, r.agence_id, r.agence_nom, r.nom_vu, r.email, r.telephone, r.portable, r.actif)$a$];
    b text[] := array[
        $b$agence_nom, nullif(trim(agence_id_user::text), '') as agence_user, trim(coalesce(prenom, '') || ' ' || coalesce(nom, '')) as nom_vu, nullif(lower(trim(email)), '') as email,$b$,
        $b$insert into app_negociateur_fiche (app_personne_id, sorte, hektor_negociateur_id, hektor_user_id, hektor_agence_id, agence_nom, agence_id_user, nom_vu, email_vu,$b$,
        $b$values (v_ad.o_personne, 'fiche_negociateur', r.n_id, r.u_id, r.agence_id, r.agence_nom, r.agence_user, r.nom_vu, r.email, r.telephone, r.portable, r.actif,$b$,
        $b$('hektor_agence_id', c.hektor_agence_id, r.agence_id), ('agence_id_user', c.agence_id_user, r.agence_user), ('telephone', c.telephone, r.telephone), ('portable', c.portable, r.portable),$b$,
        $b$set hektor_user_id = r.u_id, hektor_agence_id = r.agence_id, agence_nom = r.agence_nom, agence_id_user = r.agence_user, nom_vu = r.nom_vu, email_vu = r.email,$b$,
        $b$updated_at = case when (hektor_user_id, hektor_agence_id, agence_nom, agence_id_user, nom_vu, email_vu, telephone, portable, actif_chez_hektor)$b$,
        $b$is distinct from (r.u_id, r.agence_id, r.agence_nom, r.agence_user, r.nom_vu, r.email, r.telephone, r.portable, r.actif)$b$];
    i int; n int;
begin
    for i in 1 .. array_length(a, 1) loop
        n := (length(v) - length(replace(v, a[i], ''))) / length(a[i]);
        if n <> 1 then raise exception 'ARRET : l''ancre % apparaît % fois (1 attendue) -- rien n''est changé', i, n; end if;
        v := replace(v, a[i], b[i]);
    end loop;
    execute v;
end
$fonction$;

do $controle$
declare v_sans int; v_diff int; v_occ int;
begin
    -- toute fiche de négociateur présente dans l'annuaire porte le n° de compte d'agence de l'annuaire
    select count(*) filter (where f.agence_id_user is null and nullif(trim(d.agence_id_user::text), '') is not null),
           count(*) filter (where f.agence_id_user is distinct from nullif(trim(d.agence_id_user::text), ''))
      into v_sans, v_diff
      from public.app_hektor_negotiator_agency_directory d
      join public.app_negociateur_fiche f on f.sorte = 'fiche_negociateur' and f.hektor_negociateur_id = nullif(trim(d.hektor_negociateur_id::text), '');
    if v_sans <> 0 or v_diff <> 0 then raise exception 'ARRET : % fiches sans compte d''agence, % différentes de l''annuaire', v_sans, v_diff; end if;
    -- la fonction de nuit recopie bien la colonne : agence_user nommé EXACTEMENT 5 fois (lecture, création, journal, mise à jour, comparaison)
    select (length(d) - length(replace(d, 'agence_user', ''))) / length('agence_user') into v_occ
      from (select replace(pg_get_functiondef('public.app_negociateur_registre_maintenir(text[],boolean,integer)'::regprocedure), chr(13), '') as d) x;
    if v_occ <> 5 then raise exception 'ARRET : la fonction de nuit nomme agence_user % fois (5 attendues)', v_occ; end if;
end
$controle$;
