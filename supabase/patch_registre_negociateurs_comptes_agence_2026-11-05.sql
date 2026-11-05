-- REGISTRE DES NÉGOCIATEURS (05/11/2026) : LES COMPTES D'AGENCE RATTACHÉS À LEUR AGENCE.
-- Audit : notice/AUDIT_REGISTRE_NEGOCIATEURS_2026-11-04.md §25. Frédéric : « Rattache oui ».
-- Le compte UTILISATEUR de chaque agence (celui que les menus envoient comme agence_id_user) n'est pas rendu par la liste
-- des utilisateurs de Hektor pour 4 agences ; l'organigramme de Hektor (lu le 05/11) les montre pourtant VIVANTES.
--   Saint-Étienne (agence 18) : compte n° 25 -- ABSENT du registre      -> fiche créée sous 1000019 Groupe GTI Saint-Etienne
--   Issoire       (agence 15) : compte n° 22 -- ABSENT du registre      -> fiche créée sous 1000017 Groupe GTI Issoire
--   Le Puy        (agence 17) : compte n° 24 -- sous 1000021 « Utilisateur supprimé n° 24 » -> déplacée sous 1000018
--   Ambert        (agence 16) : compte n° 23 -- « numéro de répartition » de 1000016 -> devient son compte d'agence
-- Chaque fiche : sorte compte_utilisateur, user_type AGENCE, PRÉSENTE et ACTIVE (l'organigramme du 05/11), rattachée par
-- DÉCISION -- la nuit ne la modifie pas et ne la marque jamais absente (même règle que le compte admin n° 4). Les 4 agences
-- deviennent actives (la règle de la nuit : un compte présent = personne active). Rien n'est supprimé : 1000021 reste,
-- vide, avec une note. Journal : une ligne par geste.
-- Retour arrière : patch_registre_negociateurs_comptes_agence_2026-11-05_INVERSE.sql

do $comptes$
declare v_nuit date := current_date; v_fiche bigint; v_n int;
begin
    -- les gardes : l'état mesuré le 05/11, sinon ARRÊT sans rien changer
    if exists (select 1 from public.app_negociateur_fiche where hektor_user_id in ('22', '25')) then
        raise exception '%', 'ARRET : un compte 22 ou 25 est déjà au registre -- rien n''est changé';
    end if;
    if not exists (select 1 from public.app_negociateur_fiche where app_fiche_id = 1000032 and hektor_user_id = '24' and app_personne_id = 1000021 and sorte = 'numero_repartition')
       or not exists (select 1 from public.app_negociateur_fiche where app_fiche_id = 1000027 and hektor_user_id = '23' and app_personne_id = 1000016 and sorte = 'numero_repartition') then
        raise exception '%', 'ARRET : les fiches des comptes 24 / 23 ne sont plus celles mesurées le 05/11 -- rien n''est changé';
    end if;
    select count(*) into v_n from public.app_negociateur_personne
     where (app_personne_id, nom) in ((1000016, 'Groupe GTI Ambert'), (1000017, 'Groupe GTI Issoire'), (1000018, 'Groupe Gti Le Puy en Velay'), (1000019, 'Groupe GTI Saint-Etienne'))
       and type_personne = 'agence';
    if v_n <> 4 then raise exception 'ARRET : % agences sur 4 trouvées au registre -- rien n''est changé', v_n; end if;

    -- Saint-Étienne et Issoire : le compte d'agence est créé
    insert into public.app_negociateur_fiche (app_personne_id, sorte, hektor_user_id, hektor_agence_id, agence_nom, nom_vu, user_type,
                                              actif_chez_hektor, present_chez_hektor, rattache_par, premiere_vue, derniere_vue)
    values (1000019, 'compte_utilisateur', '25', '18', 'Groupe GTI Saint-Etienne', 'Groupe GTI Saint-Etienne', 'AGENCE', true, true, 'decision', now(), now())
    returning app_fiche_id into v_fiche;
    insert into public.app_negociateur_journal (app_fiche_id, app_personne_id, evenement, champ, apres, a_signaler, nuit)
    values (v_fiche, 1000019, 'adoptee', 'compte', 'compte d''agence n° 25 rattaché par décision de Frédéric (05/11), organigramme Hektor', false, v_nuit);

    insert into public.app_negociateur_fiche (app_personne_id, sorte, hektor_user_id, hektor_agence_id, agence_nom, nom_vu, user_type,
                                              actif_chez_hektor, present_chez_hektor, rattache_par, premiere_vue, derniere_vue)
    values (1000017, 'compte_utilisateur', '22', '15', 'Groupe GTI Issoire', 'Groupe GTI Issoire', 'AGENCE', true, true, 'decision', now(), now())
    returning app_fiche_id into v_fiche;
    insert into public.app_negociateur_journal (app_fiche_id, app_personne_id, evenement, champ, apres, a_signaler, nuit)
    values (v_fiche, 1000017, 'adoptee', 'compte', 'compte d''agence n° 22 rattaché par décision de Frédéric (05/11), organigramme Hektor', false, v_nuit);

    -- Le Puy : la fiche du compte 24 change de personne (de « Utilisateur supprimé n° 24 » à l'agence du Puy)
    update public.app_negociateur_fiche
       set app_personne_id = 1000018, sorte = 'compte_utilisateur', hektor_agence_id = '17', agence_nom = 'Groupe Gti Le Puy en Velay',
           nom_vu = 'Groupe Gti Le Puy en Velay', user_type = 'AGENCE', actif_chez_hektor = true, present_chez_hektor = true,
           absent_depuis = null, rattache_par = 'decision', derniere_vue = now(), updated_at = now()
     where app_fiche_id = 1000032;
    insert into public.app_negociateur_journal (app_fiche_id, app_personne_id, evenement, champ, avant, apres, a_signaler, nuit)
    values (1000032, 1000018, 'changement', 'app_personne_id', '1000021 Utilisateur supprimé n° 24 (numero_repartition)',
            '1000018 Groupe Gti Le Puy en Velay : compte d''agence n° 24, décision de Frédéric (05/11)', false, v_nuit);
    update public.app_negociateur_personne
       set a_valider = 'vide depuis le 05/11 : son n° 24 est le compte de l''agence du Puy (fiche 1000032 déplacée sous 1000018, décision de Frédéric)',
           updated_at = now()
     where app_personne_id = 1000021;

    -- Ambert : le n° 23 n'était qu'un « numéro de répartition » ; c'est le compte de l'agence
    update public.app_negociateur_fiche
       set sorte = 'compte_utilisateur', hektor_agence_id = '16', agence_nom = 'Groupe GTI Ambert', nom_vu = 'Groupe GTI Ambert', user_type = 'AGENCE',
           actif_chez_hektor = true, present_chez_hektor = true, absent_depuis = null, rattache_par = 'decision', derniere_vue = now(), updated_at = now()
     where app_fiche_id = 1000027;
    insert into public.app_negociateur_journal (app_fiche_id, app_personne_id, evenement, champ, avant, apres, a_signaler, nuit)
    values (1000027, 1000016, 'changement', 'sorte', 'numero_repartition', 'compte_utilisateur : compte d''agence n° 23, décision de Frédéric (05/11)', false, v_nuit);

    -- les 4 agences vivent (la règle de la nuit : un compte présent = personne active)
    update public.app_negociateur_personne set actif = true, updated_at = now()
     where app_personne_id in (1000016, 1000017, 1000018, 1000019) and actif is distinct from true;
    insert into public.app_negociateur_journal (app_personne_id, evenement, champ, avant, apres, nuit)
    select app_personne_id, 'actif', 'actif', 'false', 'true', v_nuit from public.app_negociateur_personne where app_personne_id in (1000016, 1000017, 1000018, 1000019);

    -- contrôle de fin
    select count(*) into v_n from public.app_negociateur_fiche f
     where f.sorte = 'compte_utilisateur' and f.user_type = 'AGENCE' and f.rattache_par = 'decision'
       and (f.hektor_user_id, f.app_personne_id) in (('25', 1000019), ('22', 1000017), ('24', 1000018), ('23', 1000016));
    if v_n <> 4 then raise exception 'ARRET : % comptes d''agence sur 4 en place', v_n; end if;
    if exists (select 1 from (select distinct agence_id_user::text as u from public.app_hektor_negotiator_agency_directory where agence_id_user is not null and hektor_agence_id::text <> '19') a
                where not exists (select 1 from public.app_negociateur_fiche f join public.app_negociateur_personne p using (app_personne_id)
                                   where f.hektor_user_id = a.u and p.type_personne in ('agence'))) then
        raise exception '%', 'ARRET : un compte d''agence (hors agence 19 supprimée) n''est toujours pas sous une agence';
    end if;
end
$comptes$;
