-- REGISTRE DES UTILISATEURS ET DES AGENCES, étape 3 LOT C (05/11/2026) — LA SAISIE AU CARNET.
-- Audit : notice/AUDIT_REGISTRE_NEGOCIATEURS_2026-11-04.md §43. Frédéric : « Vas-y, avec le statut ».
--
-- CE QUE POSE CE PATCH (des fonctions, AUCUNE donnée n'est écrite par le patch lui-même) :
--   app_registre_saisir(objet, id, champs)   un administrateur saisit des champs d'une personne, d'une agence ou de la
--                                            société : la valeur est écrite, INSCRITE AU CARNET (la nuit ne la touche
--                                            plus), et tracée au journal (avant -> après, qui) ; les écarts ouverts sur
--                                            ce champ sont classés (l'humain a tranché) ;
--   app_registre_rendre(objet, id, champ)    « Rendre à Hektor » : le champ sort du carnet, la nuit suivante le repose ;
--   app_registre_trancher(source, id, choix) un écart : « garder » (classé, il ne revient plus) ou « prendre » (la valeur
--                                            de Hektor entre au carnet) ;
--   app_registre_personne_vue(id)            le repère « À valider » d'une personne est retiré (motif gardé au journal) ;
--   la NUIT DES NÉGOCIATEURS (app_negociateur_registre_maintenir) ne recalcule plus le statut actif d'une personne dont
--   le statut est AU CARNET (« actif chez nous », décision du §38).
-- ⛔ Rien ne part chez Hektor. Les gestes vers Hektor gardent leurs fiches actives chez Hektor (§39).
-- ⛔ Réservé aux ADMINISTRATEURS : chaque fonction vérifie is_app_admin() (un négociateur reçoit un refus).
-- Retour arrière : patch_registre_saisie_lot_c_2026-11-05_INVERSE.sql

do $garde$
begin
    if to_regclass('public.app_registre_champ_app') is null or to_regclass('public.app_registre_journal') is null then
        raise exception '%', 'ARRET : l''étape 2 du registre n''est pas posée.';
    end if;
    if to_regprocedure('public.app_registre_saisir(text,bigint,jsonb)') is not null then
        raise exception '%', 'ARRET : app_registre_saisir existe déjà -- quelqu''un est passé avant. Rien n''est changé.';
    end if;
    -- la nuit des négociateurs doit être CELLE QUE J'AI LUE (empreinte sans retour chariot)
    if md5(replace(pg_get_functiondef('public.app_negociateur_registre_maintenir(text[],boolean,integer)'::regprocedure), chr(13), ''))
       <> '725267743d8fedad1c582d830250673a' then
        raise exception '%', 'ARRET : la nuit des négociateurs a changé depuis l''audit. Rien n''est changé.';
    end if;
end
$garde$;

-- ── 1. le journal apprend les gestes de l'app, et QUI les fait ──
alter table public.app_registre_journal drop constraint app_registre_journal_evenement_check;
alter table public.app_registre_journal add constraint app_registre_journal_evenement_check
    check (evenement = any (array['pose', 'changement', 'nouvelle', 'disparue', 'reapparue', 'ecart',
                                  'saisie', 'rendu', 'tranche', 'vu']));
alter table public.app_registre_journal add column par uuid;
comment on column public.app_registre_journal.par is 'Qui a fait le geste dans l''app (saisie, rendu, tranche, vu) ; NULL = la nuit.';

-- ── 2. les champs SAISISSABLES (et rien d'autre : un numéro Hektor, une photo, un logo ne se saisissent pas ici) ──
create or replace function public.app_registre_champs_saisissables(p_objet text)
returns text[] language sql immutable set search_path to 'public' as $f$
    select case p_objet
        when 'personne' then array['civilite', 'prenom', 'nom_famille', 'fonction', 'app_agence_id', 'email_pro',
                                   'telephone', 'portable', 'actif']
        when 'agence'   then array['nom', 'email', 'telephone', 'fax', 'site', 'responsable', 'adresse', 'code_postal',
                                   'ville', 'siret_etablissement', 'couleur']
        when 'societe'  then array['raison_sociale', 'forme', 'siret', 'naf', 'capital', 'rcs', 'rcs_ville', 'tva', 'rsac',
                                   'siege_adresse', 'siege_code_postal', 'siege_ville', 'telephone', 'email', 'rcp_numero',
                                   'assureur_nom', 'assureur_adresse', 'assureur_code_postal', 'assureur_ville',
                                   'mediateur_nom', 'mediateur_adresse', 'mediateur_code_postal', 'mediateur_ville',
                                   'mediateur_site', 'carte_type', 'carte_numero', 'carte_delivree_par', 'carte_validite',
                                   'carte_detenteur', 'carte_maniement_fonds', 'carte_garant', 'carte_montant']
    end
$f$;

-- ── 3. le cœur : écrire UN champ, l'inscrire au carnet, le tracer (interne, sans contrôle de droit) ──
create or replace function public.app_registre_ecrire_champ(p_objet text, p_id bigint, p_champ text, p_valeur text, p_par uuid)
returns boolean language plpgsql security definer set search_path to 'public' as $f$
declare
    v_table text := case p_objet when 'societe' then 'app_registre_societe' when 'agence' then 'app_registre_agence'
                                 when 'personne' then 'app_negociateur_personne' end;
    v_idcol text := case p_objet when 'societe' then 'app_societe_id' when 'agence' then 'app_agence_id'
                                 when 'personne' then 'app_personne_id' end;
    v_valeur text := nullif(trim(p_valeur), '');
    v_row jsonb; v_old text; v_type text;
begin
    if v_table is null then raise exception 'objet inconnu : %', p_objet; end if;
    if not (p_champ = any (app_registre_champs_saisissables(p_objet))) then
        raise exception 'champ non saisissable : % pour %', p_champ, p_objet;
    end if;
    if p_champ = 'actif' and (v_valeur is null or v_valeur not in ('true', 'false')) then raise exception 'le statut est true ou false'; end if;
    if p_champ = 'app_agence_id' and v_valeur is not null
       and not exists (select 1 from app_registre_agence where app_agence_id = v_valeur::bigint) then
        raise exception 'agence % absente du registre', v_valeur;
    end if;
    if p_champ = 'carte_validite' and v_valeur is not null then perform v_valeur::date; end if;
    execute format('select to_jsonb(t) from %I t where %I = $1', v_table, v_idcol) into v_row using p_id;
    if v_row is null then raise exception '% % absent du registre', p_objet, p_id; end if;
    v_old := v_row ->> p_champ;
    if v_old is distinct from v_valeur then
        select format_type(a.atttypid, a.atttypmod) into v_type
          from pg_attribute a where a.attrelid = v_table::regclass and a.attname = p_champ and not a.attisdropped;
        execute format('update %I set %I = $1::%s, updated_at = now() where %I = $2', v_table, p_champ, v_type, v_idcol)
          using v_valeur, p_id;
    end if;
    insert into app_registre_champ_app (objet, objet_id, champ, valeur, ecrit_par, ecrit_le)
    values (p_objet, p_id, p_champ, v_valeur, p_par, now())
    on conflict (objet, objet_id, champ) do update set valeur = excluded.valeur, ecrit_par = excluded.ecrit_par, ecrit_le = excluded.ecrit_le;
    insert into app_registre_journal (objet, objet_id, evenement, champ, avant, apres, nuit, par)
    values (p_objet, p_id, 'saisie', p_champ, v_old, v_valeur, current_date, p_par);
    -- l'humain a tranché : les écarts encore ouverts sur ce champ sont classés
    update app_registre_journal set traite_le = now(), traite_par = p_par
     where objet = p_objet and objet_id = p_id and champ = p_champ and evenement = 'ecart' and traite_le is null;
    return v_old is distinct from v_valeur;
end
$f$;
revoke all on function public.app_registre_ecrire_champ(text, bigint, text, text, uuid) from public, anon, authenticated;
grant execute on function public.app_registre_ecrire_champ(text, bigint, text, text, uuid) to service_role;

-- ── 4. les gestes de l'écran (administrateurs seuls) ──
create or replace function public.app_registre_saisir(p_objet text, p_id bigint, p_champs jsonb)
returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare k text; v jsonb; n int := 0; total int := 0;
begin
    if not is_app_admin() then raise exception 'Réservé aux administrateurs'; end if;
    if p_champs is null or jsonb_typeof(p_champs) <> 'object' then raise exception 'champs : un objet est attendu'; end if;
    for k, v in select key, value from jsonb_each(p_champs) loop
        total := total + 1;
        if app_registre_ecrire_champ(p_objet, p_id, k,
               case when jsonb_typeof(v) = 'null' then null when jsonb_typeof(v) = 'string' then v #>> '{}' else v::text end,
               auth.uid()) then
            n := n + 1;
        end if;
    end loop;
    return jsonb_build_object('ok', true, 'saisis', total, 'changes', n);
end
$f$;

create or replace function public.app_registre_rendre(p_objet text, p_id bigint, p_champ text)
returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare v_valeur text;
begin
    if not is_app_admin() then raise exception 'Réservé aux administrateurs'; end if;
    delete from app_registre_champ_app where objet = p_objet and objet_id = p_id and champ = p_champ returning valeur into v_valeur;
    if not found then return jsonb_build_object('ok', true, 'rendu', false); end if;
    insert into app_registre_journal (objet, objet_id, evenement, champ, avant, apres, nuit, par)
    values (p_objet, p_id, 'rendu', p_champ, v_valeur, 'rendu à Hektor : la nuit le reposera', current_date, auth.uid());
    return jsonb_build_object('ok', true, 'rendu', true);
end
$f$;

-- p_source : 'registre' (app_registre_journal) ou 'negociateur' (app_negociateur_journal, seulement « garder »)
create or replace function public.app_registre_trancher(p_source text, p_id bigint, p_choix text)
returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare j record;
begin
    if not is_app_admin() then raise exception 'Réservé aux administrateurs'; end if;
    if p_choix not in ('garder', 'prendre') then raise exception 'choix : garder ou prendre'; end if;
    if p_source = 'negociateur' then
        if p_choix <> 'garder' then raise exception 'un signal des fiches Hektor se classe seulement'; end if;
        update app_negociateur_journal set traite_le = now(), traite_par = auth.uid()
         where id = p_id and a_signaler and traite_le is null;
        return jsonb_build_object('ok', found);
    end if;
    if p_source <> 'registre' then raise exception 'source : registre ou negociateur'; end if;
    select * into j from app_registre_journal where id = p_id and evenement = 'ecart' and traite_le is null;
    if not found then return jsonb_build_object('ok', false, 'raison', 'écart introuvable ou déjà tranché'); end if;
    if p_choix = 'prendre' then
        -- la valeur de Hektor ENTRE AU CARNET (elle devient la nôtre) ; les écarts du champ se classent dans la foulée
        perform app_registre_ecrire_champ(j.objet, j.objet_id, j.champ, j.apres, auth.uid());
    else
        update app_registre_journal set traite_le = now(), traite_par = auth.uid() where id = p_id;
    end if;
    insert into app_registre_journal (objet, objet_id, evenement, champ, avant, apres, nuit, par)
    values (j.objet, j.objet_id, 'tranche', j.champ, j.apres,
            case p_choix when 'garder' then 'la nôtre gardée' else 'celle de Hektor prise' end, current_date, auth.uid());
    return jsonb_build_object('ok', true);
end
$f$;

create or replace function public.app_registre_personne_vue(p_id bigint)
returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare v_motif text;
begin
    if not is_app_admin() then raise exception 'Réservé aux administrateurs'; end if;
    select a_valider into v_motif from app_negociateur_personne where app_personne_id = p_id;
    if v_motif is null then return jsonb_build_object('ok', true, 'vu', false); end if;
    update app_negociateur_personne set a_valider = null, updated_at = now() where app_personne_id = p_id;
    insert into app_registre_journal (objet, objet_id, evenement, champ, avant, apres, nuit, par)
    values ('personne', p_id, 'vu', 'a_valider', v_motif, 'vu par un administrateur', current_date, auth.uid());
    return jsonb_build_object('ok', true, 'vu', true);
end
$f$;

-- ⛔ revoke from public NE FERME PAS authenticated : chaque droit est posé à la main, et le contrôle est DANS la fonction
revoke all on function public.app_registre_saisir(text, bigint, jsonb) from public, anon;
revoke all on function public.app_registre_rendre(text, bigint, text) from public, anon;
revoke all on function public.app_registre_trancher(text, bigint, text) from public, anon;
revoke all on function public.app_registre_personne_vue(bigint) from public, anon;
grant execute on function public.app_registre_saisir(text, bigint, jsonb) to authenticated, service_role;
grant execute on function public.app_registre_rendre(text, bigint, text) to authenticated, service_role;
grant execute on function public.app_registre_trancher(text, bigint, text) to authenticated, service_role;
grant execute on function public.app_registre_personne_vue(bigint) to authenticated, service_role;
revoke all on function public.app_registre_champs_saisissables(text) from public, anon;
grant execute on function public.app_registre_champs_saisissables(text) to authenticated, service_role;

-- ── 5. la nuit des négociateurs respecte le STATUT AU CARNET ──
do $nuit$
declare
    v_def text := replace(pg_get_functiondef('public.app_negociateur_registre_maintenir(text[],boolean,integer)'::regprocedure), chr(13), '');
    v_ancre text := '             group by p.app_personne_id, p.actif';
    v_neuf text := '             where not exists (select 1 from app_registre_champ_app k where k.objet = ''personne'' and k.objet_id = p.app_personne_id and k.champ = ''actif'')' || chr(10) || v_ancre;
begin
    if (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 then
        raise exception '%', 'ARRET : l''ancre du statut n''est pas trouvée une fois et une seule dans la nuit des négociateurs.';
    end if;
    execute replace(v_def, v_ancre, v_neuf);
end
$nuit$;

-- ── 6. contrôles ──
do $controle$
declare v_def text;
begin
    v_def := pg_get_functiondef('public.app_negociateur_registre_maintenir(text[],boolean,integer)'::regprocedure);
    if strpos(v_def, 'k.champ = ''actif''') = 0 then raise exception 'ARRET : la nuit ne lit pas le statut au carnet'; end if;
    if has_function_privilege('anon', 'public.app_registre_saisir(text,bigint,jsonb)', 'execute') then
        raise exception 'ARRET : anon peut saisir';
    end if;
    if has_function_privilege('authenticated', 'public.app_registre_ecrire_champ(text,bigint,text,text,uuid)', 'execute') then
        raise exception 'ARRET : authenticated peut écrire un champ sans contrôle de droit';
    end if;
    if not has_function_privilege('authenticated', 'public.app_registre_saisir(text,bigint,jsonb)', 'execute') then
        raise exception 'ARRET : l''écran ne pourra pas saisir';
    end if;
    if exists (select 1 from app_registre_journal where evenement in ('saisie', 'rendu', 'tranche', 'vu')) then
        raise exception 'ARRET : le patch a écrit au journal';
    end if;
end
$controle$;
