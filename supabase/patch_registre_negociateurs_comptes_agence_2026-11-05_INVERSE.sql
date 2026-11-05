-- Retour arrière de patch_registre_negociateurs_comptes_agence_2026-11-05.sql : remet les fiches 1000032 (compte 24) et
-- 1000027 (compte 23) comme mesurées le 05/11, retire les deux fiches créées (comptes 22 et 25 -- les SEULES lignes que le
-- patch a créées), remet les 4 agences inactives et la note de 1000021. Le journal garde la trace des deux gestes.
do $inverse$
declare v_nuit date := current_date;
begin
    update public.app_negociateur_fiche
       set app_personne_id = 1000021, sorte = 'numero_repartition', hektor_agence_id = null, agence_nom = null, nom_vu = 'Utilisateur supprimé n° 24',
           user_type = null, actif_chez_hektor = false, present_chez_hektor = false, rattache_par = 'seul', updated_at = now()
     where app_fiche_id = 1000032;
    update public.app_negociateur_fiche
       set sorte = 'numero_repartition', hektor_agence_id = null, agence_nom = null, user_type = null,
           actif_chez_hektor = false, present_chez_hektor = false, rattache_par = 'agence', updated_at = now()
     where app_fiche_id = 1000027;
    delete from public.app_negociateur_journal where app_fiche_id in (select app_fiche_id from public.app_negociateur_fiche
     where sorte = 'compte_utilisateur' and rattache_par = 'decision' and (hektor_user_id, app_personne_id) in (('25', 1000019), ('22', 1000017)));
    delete from public.app_negociateur_fiche
     where sorte = 'compte_utilisateur' and rattache_par = 'decision' and (hektor_user_id, app_personne_id) in (('25', 1000019), ('22', 1000017));
    update public.app_negociateur_personne set actif = false, updated_at = now() where app_personne_id in (1000016, 1000017, 1000018, 1000019);
    update public.app_negociateur_personne set a_valider = 'utilisateur supprimé chez Hektor', updated_at = now() where app_personne_id = 1000021;
    insert into public.app_negociateur_journal (evenement, champ, apres, nuit)
    values ('changement', 'retour_arriere', 'patch des comptes d''agence du 05/11 défait', v_nuit);
end
$inverse$;
