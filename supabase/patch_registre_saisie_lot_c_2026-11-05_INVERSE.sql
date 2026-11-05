-- RETOUR ARRIÈRE de patch_registre_saisie_lot_c_2026-11-05.sql (registre, étape 3 lot C : la saisie au carnet).
-- Retire SA part : les cinq fonctions, la colonne `par` et les nouveaux événements du journal, et la ligne de la nuit des
-- négociateurs qui respecte le statut au carnet. Les tables du registre (étape 2) ne sont pas touchées.
-- ⚠ Si des saisies ont déjà été faites, LE CARNET LES GARDE (ce sont des données, ce retour arrière ne les efface pas),
--   mais le journal les porte avec des événements que l'ancienne contrainte refuse : il s'arrête alors, sauf à passer
--   « set local registre.forcer = 'oui' » en tête (les lignes saisie/rendu/tranche/vu sont alors SUPPRIMÉES du journal).

do $garde$
begin
    if to_regprocedure('public.app_registre_saisir(text,bigint,jsonb)') is null then
        raise exception '%', 'ARRET : le lot C n''est pas posé. Rien n''est changé.';
    end if;
    if coalesce(current_setting('registre.forcer', true), '') <> 'oui'
       and exists (select 1 from public.app_registre_journal where evenement in ('saisie', 'rendu', 'tranche', 'vu')) then
        raise exception '%', 'ARRET : des gestes de l''app sont déjà au journal. Sauvegarder, puis relancer avec set local registre.forcer = ''oui''.';
    end if;
end
$garde$;

-- la nuit des négociateurs redevient celle d'avant (la ligne ajoutée est retirée, rien d'autre)
do $nuit$
declare
    v_def text := replace(pg_get_functiondef('public.app_negociateur_registre_maintenir(text[],boolean,integer)'::regprocedure), chr(13), '');
    v_ligne text := '             where not exists (select 1 from app_registre_champ_app k where k.objet = ''personne'' and k.objet_id = p.app_personne_id and k.champ = ''actif'')' || chr(10);
begin
    if strpos(v_def, v_ligne) = 0 then raise exception '%', 'ARRET : la ligne du statut n''est pas dans la nuit des négociateurs.'; end if;
    execute replace(v_def, v_ligne, '');
end
$nuit$;

drop function if exists public.app_registre_saisir(text, bigint, jsonb);
drop function if exists public.app_registre_rendre(text, bigint, text);
drop function if exists public.app_registre_trancher(text, bigint, text);
drop function if exists public.app_registre_personne_vue(bigint);
drop function if exists public.app_registre_ecrire_champ(text, bigint, text, text, uuid);
drop function if exists public.app_registre_champs_saisissables(text);

delete from public.app_registre_journal where evenement in ('saisie', 'rendu', 'tranche', 'vu');
alter table public.app_registre_journal drop constraint app_registre_journal_evenement_check;
alter table public.app_registre_journal add constraint app_registre_journal_evenement_check
    check (evenement = any (array['pose', 'changement', 'nouvelle', 'disparue', 'reapparue', 'ecart']));
alter table public.app_registre_journal drop column if exists par;

do $controle$
begin
    if to_regprocedure('public.app_registre_saisir(text,bigint,jsonb)') is not null then raise exception 'ARRET : la saisie est encore là'; end if;
    if md5(replace(pg_get_functiondef('public.app_negociateur_registre_maintenir(text[],boolean,integer)'::regprocedure), chr(13), ''))
       <> '725267743d8fedad1c582d830250673a' then
        raise exception 'ARRET : la nuit des négociateurs n''est pas revenue à l''identique';
    end if;
end
$controle$;
