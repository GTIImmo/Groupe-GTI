-- Retour arrière de patch_registre_negociateurs_agence_user_2026-11-04.sql : la fonction de nuit reprend ses sept lignes
-- d'avant (même méthode, ancres vérifiées), puis la colonne agence_id_user est retirée. ⚠ À ne poser qu'APRÈS avoir remis
-- les menus de l'app sur l'annuaire (sinon ils perdent le n° du compte d'agence).
do $fonction$
declare
    v text := replace(pg_get_functiondef('public.app_negociateur_registre_maintenir(text[],boolean,integer)'::regprocedure), chr(13), '');
    b text[] := array[
        $b$agence_nom, nullif(trim(agence_id_user::text), '') as agence_user, trim(coalesce(prenom, '') || ' ' || coalesce(nom, '')) as nom_vu, nullif(lower(trim(email)), '') as email,$b$,
        $b$insert into app_negociateur_fiche (app_personne_id, sorte, hektor_negociateur_id, hektor_user_id, hektor_agence_id, agence_nom, agence_id_user, nom_vu, email_vu,$b$,
        $b$values (v_ad.o_personne, 'fiche_negociateur', r.n_id, r.u_id, r.agence_id, r.agence_nom, r.agence_user, r.nom_vu, r.email, r.telephone, r.portable, r.actif,$b$,
        $b$('hektor_agence_id', c.hektor_agence_id, r.agence_id), ('agence_id_user', c.agence_id_user, r.agence_user), ('telephone', c.telephone, r.telephone), ('portable', c.portable, r.portable),$b$,
        $b$set hektor_user_id = r.u_id, hektor_agence_id = r.agence_id, agence_nom = r.agence_nom, agence_id_user = r.agence_user, nom_vu = r.nom_vu, email_vu = r.email,$b$,
        $b$updated_at = case when (hektor_user_id, hektor_agence_id, agence_nom, agence_id_user, nom_vu, email_vu, telephone, portable, actif_chez_hektor)$b$,
        $b$is distinct from (r.u_id, r.agence_id, r.agence_nom, r.agence_user, r.nom_vu, r.email, r.telephone, r.portable, r.actif)$b$];
    a text[] := array[
        $a$agence_nom, trim(coalesce(prenom, '') || ' ' || coalesce(nom, '')) as nom_vu, nullif(lower(trim(email)), '') as email,$a$,
        $a$insert into app_negociateur_fiche (app_personne_id, sorte, hektor_negociateur_id, hektor_user_id, hektor_agence_id, agence_nom, nom_vu, email_vu,$a$,
        $a$values (v_ad.o_personne, 'fiche_negociateur', r.n_id, r.u_id, r.agence_id, r.agence_nom, r.nom_vu, r.email, r.telephone, r.portable, r.actif,$a$,
        $a$('hektor_agence_id', c.hektor_agence_id, r.agence_id), ('telephone', c.telephone, r.telephone), ('portable', c.portable, r.portable),$a$,
        $a$set hektor_user_id = r.u_id, hektor_agence_id = r.agence_id, agence_nom = r.agence_nom, nom_vu = r.nom_vu, email_vu = r.email,$a$,
        $a$updated_at = case when (hektor_user_id, hektor_agence_id, agence_nom, nom_vu, email_vu, telephone, portable, actif_chez_hektor)$a$,
        $a$is distinct from (r.u_id, r.agence_id, r.agence_nom, r.nom_vu, r.email, r.telephone, r.portable, r.actif)$a$];
    i int; n int;
begin
    for i in 1 .. array_length(b, 1) loop
        n := (length(v) - length(replace(v, b[i], ''))) / length(b[i]);
        if n <> 1 then raise exception 'ARRET : l''ancre % apparaît % fois (1 attendue) -- rien n''est changé', i, n; end if;
        v := replace(v, b[i], a[i]);
    end loop;
    execute v;
    if md5(replace(pg_get_functiondef('public.app_negociateur_registre_maintenir(text[],boolean,integer)'::regprocedure), chr(13), '')) <> 'e68a3f86c3bce79845e4af577fcca2c0' then
        raise exception '%', 'ARRET : la fonction rendue n''a pas l''empreinte d''avant (e68a3f86)';
    end if;
end
$fonction$;

alter table public.app_negociateur_fiche drop column agence_id_user;
