-- RETOUR ARRIÈRE de patch_registre_utilisateurs_agences_etape2_2026-11-05.sql (registre des utilisateurs et des agences,
-- étape 2). Retire SA part, rien d'autre : les deux fonctions, les cinq tables, les neuf colonnes de coordonnées de
-- app_negociateur_personne, la clé de battement. Le registre des négociateurs (nom, e-mail, fiches, journal) n'est pas touché.
-- ⚠ Si la nuit a déjà ÉCRIT (interrupteur à 1) ou si le carnet porte une saisie, ce retour arrière l'efface : il s'arrête
--   alors, sauf à passer la ligne « set local registre.forcer = 'oui' » en tête.

do $garde$
begin
    if to_regclass('public.app_registre_agence') is null then
        raise exception '%', 'ARRET : l''étape 2 n''est pas posée (pas de app_registre_agence). Rien n''est changé.';
    end if;
    if coalesce(current_setting('registre.forcer', true), '') <> 'oui' and (
           exists (select 1 from public.app_registre_champ_app)
        or exists (select 1 from public.app_registre_agence)) then
        raise exception '%', 'ARRET : le registre des agences porte déjà des données (nuit à 1 ou saisie au carnet). '
                             'Sauvegarder d''abord, puis relancer avec set local registre.forcer = ''oui''.';
    end if;
end
$garde$;

drop function if exists public.app_registre_utilisateurs_agences_maintenir(jsonb, jsonb, boolean);
drop function if exists public.app_registre_poser(text, bigint, jsonb, date);
alter table public.app_negociateur_personne
    drop column if exists civilite, drop column if exists prenom, drop column if exists nom_famille,
    drop column if exists fonction, drop column if exists app_agence_id, drop column if exists email_pro,
    drop column if exists telephone, drop column if exists portable, drop column if exists photo_url;
drop table if exists public.app_registre_journal;
drop table if exists public.app_registre_champ_app;
drop table if exists public.app_registre_agence_alias;
drop table if exists public.app_registre_agence;
drop table if exists public.app_registre_societe;
delete from public.app_worker_registry where worker_key = 'phase2.registre_agences';

-- contrôle : il ne reste aucune trace, et le registre des négociateurs est intact
do $controle$
begin
    if to_regclass('public.app_registre_agence') is not null or to_regclass('public.app_registre_societe') is not null
       or to_regclass('public.app_registre_champ_app') is not null or to_regclass('public.app_registre_journal') is not null
       or to_regclass('public.app_registre_agence_alias') is not null then
        raise exception 'ARRET : une table de l''étape 2 est encore là';
    end if;
    if exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'app_negociateur_personne'
                and column_name in ('civilite', 'prenom', 'nom_famille', 'fonction', 'app_agence_id', 'email_pro', 'telephone', 'portable', 'photo_url')) then
        raise exception 'ARRET : une colonne de coordonnées est encore là';
    end if;
    if to_regprocedure('public.app_negociateur_registre_maintenir(text[], boolean, integer)') is null
       or (select count(*) from public.app_negociateur_personne) = 0 then
        raise exception 'ARRET : le registre des négociateurs n''est plus intact';
    end if;
end
$controle$;
