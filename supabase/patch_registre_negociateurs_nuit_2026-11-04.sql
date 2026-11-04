-- REGISTRE DES NÉGOCIATEURS, étape 2 (04/11/2026) — LA MISE À JOUR DE NUIT.
-- Audit : notice/AUDIT_REGISTRE_NEGOCIATEURS_2026-11-04.md §12. Frédéric : « oui audit étape 2 », puis « Oui, vas-y »
-- (règles du §12.2, signaux du §12.7, une nuit à blanc d'abord).
--
-- CE QUE FAIT LA NUIT (fonction app_negociateur_registre_maintenir, appelée par phase2/sync/maintenir_registre_negociateurs.py
-- juste après la reconstruction de l'annuaire) :
--   . une fiche connue qui change    -> le journal garde AVANT / APRÈS ; la fiche prend la valeur de Hektor ; la PERSONNE
--                                       ne bouge jamais (rattachement fixe) ;
--   . une fiche absente de la liste  -> present_chez_hektor = false, absent_depuis ; jamais supprimée ; réapparue -> l'inverse ;
--   . une fiche NOUVELLE             -> adoptée : e-mail (pas une boîte d'agence) d'UNE personne -> à elle ; agence -> à
--                                       l'agence ; nom d'UNE personne -> à elle ET signalée ; sinon PERSONNE NOUVELLE, signalée ;
--   . un compte utilisateur, un n° de la répartition, un compte de l'app : mêmes règles ;
--   . la nuit ne FUSIONNE jamais deux personnes, ne SUPPRIME jamais rien, ne touche pas le compte admin n° 4 (décision).
-- SIGNALÉ (sentinelle data.negociateur_registre_signal) : e-mail, n° d'utilisateur, nom ; personne nouvelle ; rattachement
-- par le nom ; liste incomplète. AU JOURNAL SEULEMENT : téléphones, agence, actif, présence.
-- PLANCHERS : liste de la nuit < 90 % des fiches présentes la veille -> aucune absence ; moins de 40 comptes -> aucun compte absent.
-- À BLANC (p_a_blanc = true) : le MÊME chemin, puis tout est annulé ; seul le compte rendu sort.
-- Retour arrière : patch_registre_negociateurs_nuit_2026-11-04_INVERSE.sql

do $garde$
begin
    if to_regclass('public.app_negociateur_journal') is null then
        raise exception '%', 'ARRET : le registre des négociateurs (étape 1) n''est pas posé.';
    end if;
    if to_regprocedure('public.app_negociateur_registre_maintenir(text[], boolean)') is not null then
        raise exception '%', 'ARRET : la fonction de nuit existe déjà -- quelqu''un est passé avant. Rien n''est changé.';
    end if;
end
$garde$;

-- ── 1. le journal apprend à porter un événement, un signal, et sa levée ──
alter table public.app_negociateur_journal
    alter column app_fiche_id drop not null,
    add column app_personne_id bigint references public.app_negociateur_personne (app_personne_id),
    add column evenement text not null default 'changement'
        check (evenement in ('changement', 'disparue', 'reapparue', 'adoptee', 'personne_nouvelle', 'compte_app_relie',
                             'actif', 'liste_incomplete', 'conflit')),
    add column a_signaler boolean not null default false,
    add column nuit date not null default current_date,
    add column traite_le timestamptz,
    add column traite_par uuid;
create index app_negociateur_journal_ouverts_idx on public.app_negociateur_journal (id) where a_signaler and traite_le is null;
comment on column public.app_negociateur_journal.a_signaler is 'true = la sentinelle data.negociateur_registre_signal le montre tant que traite_le est vide (app_negociateur_signal_traiter).';

-- ── 2. trois petites clés, les mêmes que l'étape 1 (et que cleNom / cleAgence de lib/pilotage.ts) ──
create or replace function public.app_neg_cle_nom(p text) returns text language sql stable set search_path to 'public' as $f$
    select lower(regexp_replace(trim(extensions.unaccent(regexp_replace(coalesce(p, ''), '^\s*(m_mme|mr\.?/mme\.?|mme\.?|mlle\.?|mr\.?|m\.)\s+', '', 'i'))), '\s+', ' ', 'g'));
$f$;
create or replace function public.app_neg_cle_agence(p text) returns text language sql stable set search_path to 'public' as $f$
    select upper(regexp_replace(trim(extensions.unaccent(regexp_replace(coalesce(p, ''), '^\s*groupe\s+gti\s*', '', 'i'))), '[\s-]+', '-', 'g'));
$f$;
-- une boîte d'agence (craponne@, gtiimmobilier.ambert@wanadoo.fr…) ou l'adresse d'un compte d'agence : jamais une clé de rattachement
create or replace function public.app_neg_email_partage(p text) returns boolean language sql stable set search_path to 'public' as $f$
    select coalesce(p, '') <> '' and (lower(p) ~ '^(gtiimmobilier\.|gti\.immobilier@)'
        or split_part(lower(p), '@', 1) in ('accueil', 'ambert', 'annonay', 'brioude', 'courpiere', 'craponne', 'dunieres', 'firminy',
             'issoire', 'lepuy', 'monistrol', 'montbrison', 'stbonnet', 'stdidier', 'stetienne', 'strambert', 'tence', 'yssingeaux', 'veauche')
        or lower(p) in (select lower(trim(email)) from public.app_user_directory where upper(user_type) = 'AGENCE'));
$f$;
revoke all on function public.app_neg_cle_nom(text), public.app_neg_cle_agence(text), public.app_neg_email_partage(text) from public, anon, authenticated;
grant execute on function public.app_neg_cle_nom(text), public.app_neg_cle_agence(text), public.app_neg_email_partage(text) to service_role;

-- ── 3. adopter une fiche nouvelle : rend la personne, et dit si c'est à signaler ──
create or replace function public.app_neg_adopter(p_nom text, p_email text, p_agence text, p_user_type text, p_sorte text, p_u_id text,
                                                 out o_personne bigint, out o_par text, out o_signal text)
language plpgsql set search_path to 'public' as $f$
declare
    v_nom text := regexp_replace(trim(coalesce(p_nom, '')), '^\s*(m_mme|mr\.?/mme\.?|mme\.?|mlle\.?|mr\.?|m\.)\s+', '', 'i');
    v_nk text := public.app_neg_cle_nom(p_nom);
    v_email text := nullif(lower(trim(coalesce(p_email, ''))), '');
    v_cle text; v_n int; v_type text;
begin
    -- une agence : une personne par agence, jamais réunie par l'e-mail
    if upper(coalesce(p_user_type, '')) = 'AGENCE' or v_email = 'accueil@gti-immobilier.fr' or p_nom ~* '^\s*groupe\s+gti' or p_nom ~* '^\s*compte\s+formation'
       or p_nom ~* '^\s*(gti\s+immobilier|n[ée]go\s+gti)\s*$' then
        v_cle := 'agence:' || public.app_neg_cle_agence(coalesce(case when p_sorte = 'fiche_negociateur' then p_agence end, p_nom));
        select app_personne_id into o_personne from public.app_negociateur_personne where cle_regroupement = v_cle;
        if o_personne is null then
            insert into public.app_negociateur_personne (nom, type_personne, actif, origine, a_valider, cle_regroupement)
            values (coalesce(case when p_sorte = 'fiche_negociateur' then p_agence end, v_nom), 'agence', false, p_sorte,
                    'agence nouvelle (nuit du ' || to_char(current_date, 'DD/MM/YYYY') || ')', v_cle)
            returning app_personne_id into o_personne;
            o_signal := 'agence nouvelle';
        end if;
        o_par := 'agence';
        return;
    end if;
    -- un utilisateur supprimé de la répartition : une personne à lui
    if p_sorte = 'numero_repartition' and coalesce(p_nom, '') ~* '^utilisateur supprim' then
        insert into public.app_negociateur_personne (nom, type_personne, actif, origine, a_valider, cle_regroupement)
        values (v_nom, 'inconnu', false, p_sorte, 'utilisateur supprimé chez Hektor', 'inconnu:' || p_u_id)
        on conflict (cle_regroupement) do nothing
        returning app_personne_id into o_personne;
        if o_personne is null then select app_personne_id into o_personne from public.app_negociateur_personne where cle_regroupement = 'inconnu:' || p_u_id; end if;
        o_par := 'seul'; o_signal := 'utilisateur supprimé nouveau dans la répartition';
        return;
    end if;
    -- par l'e-mail : UNE personne (pas une agence) qui le porte déjà
    if v_email is not null and not public.app_neg_email_partage(v_email) then
        select count(distinct p.app_personne_id), min(p.app_personne_id) into v_n, o_personne
          from public.app_negociateur_personne p
         where p.type_personne <> 'agence'
           and (p.email = v_email or exists (select 1 from public.app_negociateur_fiche f where f.app_personne_id = p.app_personne_id and f.email_vu = v_email));
        if v_n = 1 then o_par := 'email'; return; end if;
        o_personne := null;
    end if;
    -- par le nom : UNE personne (pas une agence) qui le porte -> rattachée, mais signalée
    if v_nk <> '' then
        select count(*), min(app_personne_id) into v_n, o_personne
          from public.app_negociateur_personne where type_personne not in ('agence', 'inconnu') and public.app_neg_cle_nom(nom) = v_nk;
        if v_n = 1 then o_par := 'nom'; o_signal := 'rattachée par le nom'; return; end if;
        o_personne := null;
    end if;
    -- sinon : une personne nouvelle, signalée
    v_type := case when p_sorte = 'fiche_negociateur' then 'negociateur' when upper(coalesce(p_user_type, '')) = 'SECRETAIRE' then 'secretaire'
                   when upper(coalesce(p_user_type, '')) = 'ADMIN' then 'administrateur' else 'inconnu' end;
    v_cle := coalesce(case when v_email is not null and not public.app_neg_email_partage(v_email) then 'email:' || v_email end, 'nom:' || nullif(v_nk, ''), 'u:' || p_u_id);
    if exists (select 1 from public.app_negociateur_personne where cle_regroupement = v_cle) then v_cle := v_cle || ':u' || coalesce(p_u_id, ''); end if;
    insert into public.app_negociateur_personne (nom, email, type_personne, actif, origine, a_valider, cle_regroupement)
    values (coalesce(nullif(v_nom, ''), 'Sans nom (u ' || coalesce(p_u_id, '?') || ')'),
            case when v_email is not null and not public.app_neg_email_partage(v_email) then v_email end,
            v_type, false, p_sorte, 'personne nouvelle (nuit du ' || to_char(current_date, 'DD/MM/YYYY') || ')', v_cle)
    returning app_personne_id into o_personne;
    o_par := 'seul'; o_signal := 'personne nouvelle';
end
$f$;
revoke all on function public.app_neg_adopter(text, text, text, text, text, text) from public, anon, authenticated;
grant execute on function public.app_neg_adopter(text, text, text, text, text, text) to service_role;

-- ── 4. LA NUIT ──
create or replace function public.app_negociateur_registre_maintenir(p_presents text[], p_a_blanc boolean default true)
returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
    v_rapport jsonb := '{}'::jsonb;
    v_presents_hier int; v_presents_nuit int; v_liste_ok boolean; v_comptes int; v_comptes_ok boolean;
    v_n int; r record; c record; v_ad record; v_fiche bigint;
    v_nuit date := current_date;
begin
    begin  -- le bloc qu'on annule pour l'essai à blanc
        -- les planchers
        select count(*) into v_presents_hier from app_negociateur_fiche where sorte = 'fiche_negociateur' and present_chez_hektor;
        v_presents_nuit := coalesce(cardinality(p_presents), 0);
        v_liste_ok := p_presents is not null and v_presents_nuit >= 0.9 * v_presents_hier;
        select count(*) into v_comptes from app_user_directory;
        v_comptes_ok := v_comptes >= 40;
        -- un seul signal ouvert à la fois : il se tait quand un admin l'a vu, et revient si la liste reste incomplète
        if not v_liste_ok and not exists (select 1 from app_negociateur_journal where evenement = 'liste_incomplete' and traite_le is null) then
            insert into app_negociateur_journal (evenement, champ, avant, apres, a_signaler, nuit)
            values ('liste_incomplete', 'presents', v_presents_hier::text,
                    case when p_presents is null then 'inconnue (liste de la nuit incomplète)' else v_presents_nuit::text end, true, v_nuit);
        end if;

        -- A. les fiches de négociateur (l'annuaire de cette nuit)
        for r in
            select nullif(trim(hektor_negociateur_id), '') as n_id, nullif(trim(hektor_user_id), '') as u_id, nullif(trim(hektor_agence_id), '') as agence_id,
                   agence_nom, trim(coalesce(prenom, '') || ' ' || coalesce(nom, '')) as nom_vu, nullif(lower(trim(email)), '') as email,
                   telephone, portable, coalesce(is_active, false) as actif
              from app_hektor_negotiator_agency_directory where nullif(trim(hektor_negociateur_id), '') is not null
        loop
            select * into c from app_negociateur_fiche where hektor_negociateur_id = r.n_id;
            if not found then
                select * into v_ad from app_neg_adopter(r.nom_vu, r.email, r.agence_nom, null, 'fiche_negociateur', r.u_id);
                if r.u_id is not null and exists (select 1 from app_negociateur_fiche where hektor_user_id = r.u_id) then
                    insert into app_negociateur_journal (app_personne_id, evenement, champ, apres, a_signaler, nuit)
                    values (v_ad.o_personne, 'conflit', 'hektor_user_id', r.u_id || ' déjà porté par une autre fiche (n° de négociateur ' || r.n_id || ')', true, v_nuit);
                    r.u_id := null;
                end if;
                insert into app_negociateur_fiche (app_personne_id, sorte, hektor_negociateur_id, hektor_user_id, hektor_agence_id, agence_nom, nom_vu, email_vu,
                                                   telephone, portable, actif_chez_hektor, present_chez_hektor, rattache_par)
                values (v_ad.o_personne, 'fiche_negociateur', r.n_id, r.u_id, r.agence_id, r.agence_nom, r.nom_vu, r.email, r.telephone, r.portable, r.actif,
                        case when v_liste_ok then r.n_id = any(p_presents) else null end, v_ad.o_par)
                returning app_fiche_id into v_fiche;
                insert into app_negociateur_journal (app_fiche_id, app_personne_id, evenement, champ, apres, a_signaler, nuit)
                values (v_fiche, v_ad.o_personne, case when v_ad.o_signal in ('personne nouvelle', 'agence nouvelle') then 'personne_nouvelle' else 'adoptee' end,
                        'fiche', coalesce(v_ad.o_signal, 'rattachée par ' || v_ad.o_par) || ' : n° ' || r.n_id || ' / u ' || coalesce(r.u_id, '-') || ' ' || r.nom_vu,
                        v_ad.o_signal is not null, v_nuit);
                continue;
            end if;
            -- une fiche connue : chaque champ changé passe au journal ; la personne ne bouge pas
            if c.hektor_user_id is distinct from r.u_id then
                if r.u_id is not null and exists (select 1 from app_negociateur_fiche where hektor_user_id = r.u_id and app_fiche_id <> c.app_fiche_id) then
                    insert into app_negociateur_journal (app_fiche_id, app_personne_id, evenement, champ, avant, apres, a_signaler, nuit)
                    values (c.app_fiche_id, c.app_personne_id, 'conflit', 'hektor_user_id', c.hektor_user_id, r.u_id || ' (déjà porté par une autre fiche, non appliqué)', true, v_nuit);
                    r.u_id := c.hektor_user_id;
                else
                    insert into app_negociateur_journal (app_fiche_id, app_personne_id, champ, avant, apres, a_signaler, nuit)
                    values (c.app_fiche_id, c.app_personne_id, 'hektor_user_id', c.hektor_user_id, r.u_id, true, v_nuit);
                end if;
            end if;
            insert into app_negociateur_journal (app_fiche_id, app_personne_id, champ, avant, apres, a_signaler, nuit)
            select c.app_fiche_id, c.app_personne_id, x.champ, x.avant, x.apres, x.champ in ('email_vu', 'nom_vu'), v_nuit
              from (values ('nom_vu', c.nom_vu, r.nom_vu), ('email_vu', c.email_vu, r.email), ('agence_nom', c.agence_nom, r.agence_nom),
                           ('hektor_agence_id', c.hektor_agence_id, r.agence_id), ('telephone', c.telephone, r.telephone), ('portable', c.portable, r.portable),
                           ('actif_chez_hektor', c.actif_chez_hektor::text, r.actif::text)) x(champ, avant, apres)
             where x.avant is distinct from x.apres;
            if v_liste_ok and c.present_chez_hektor is distinct from (r.n_id = any(p_presents)) then
                insert into app_negociateur_journal (app_fiche_id, app_personne_id, evenement, champ, avant, apres, nuit)
                values (c.app_fiche_id, c.app_personne_id, case when r.n_id = any(p_presents) then 'reapparue' else 'disparue' end,
                        'present_chez_hektor', coalesce(c.present_chez_hektor::text, '?'), (r.n_id = any(p_presents))::text, v_nuit);
            end if;
            update app_negociateur_fiche
               set hektor_user_id = r.u_id, hektor_agence_id = r.agence_id, agence_nom = r.agence_nom, nom_vu = r.nom_vu, email_vu = r.email,
                   telephone = r.telephone, portable = r.portable, actif_chez_hektor = r.actif,
                   present_chez_hektor = case when v_liste_ok then r.n_id = any(p_presents) else present_chez_hektor end,
                   absent_depuis = case when not v_liste_ok then absent_depuis when r.n_id = any(p_presents) then null else coalesce(absent_depuis, now()) end,
                   derniere_vue = case when v_liste_ok and r.n_id = any(p_presents) then now() else derniere_vue end,
                   updated_at = case when (hektor_user_id, hektor_agence_id, agence_nom, nom_vu, email_vu, telephone, portable, actif_chez_hektor)
                                          is distinct from (r.u_id, r.agence_id, r.agence_nom, r.nom_vu, r.email, r.telephone, r.portable, r.actif)
                                     then now() else updated_at end
             where app_fiche_id = c.app_fiche_id;
        end loop;

        -- B. les comptes utilisateur sans fiche de négociateur (secrétaires, agences)
        for r in
            select nullif(trim(u.id_user), '') as u_id, coalesce(nullif(trim(coalesce(u.prenom, '') || ' ' || coalesce(u.nom, '')), ''), u.display_name) as nom_vu,
                   nullif(lower(trim(u.email)), '') as email, u.tel as telephone, u.portable, upper(u.user_type) as user_type
              from app_user_directory u
             where nullif(trim(u.id_user), '') is not null
               and not exists (select 1 from app_hektor_negotiator_agency_directory d where trim(d.hektor_user_id) = trim(u.id_user))
        loop
            select * into c from app_negociateur_fiche where hektor_user_id = r.u_id;
            if not found then
                select * into v_ad from app_neg_adopter(r.nom_vu, r.email, null, r.user_type, 'compte_utilisateur', r.u_id);
                insert into app_negociateur_fiche (app_personne_id, sorte, hektor_user_id, nom_vu, email_vu, telephone, portable, user_type,
                                                   actif_chez_hektor, present_chez_hektor, rattache_par)
                values (v_ad.o_personne, 'compte_utilisateur', r.u_id, r.nom_vu, r.email, r.telephone, r.portable, r.user_type, true, true, v_ad.o_par)
                returning app_fiche_id into v_fiche;
                insert into app_negociateur_journal (app_fiche_id, app_personne_id, evenement, champ, apres, a_signaler, nuit)
                values (v_fiche, v_ad.o_personne, case when v_ad.o_signal in ('personne nouvelle', 'agence nouvelle') then 'personne_nouvelle' else 'adoptee' end,
                        'compte', coalesce(v_ad.o_signal, 'rattaché par ' || v_ad.o_par) || ' : compte u ' || r.u_id || ' ' || coalesce(r.user_type, '') || ' ' || r.nom_vu,
                        v_ad.o_signal is not null, v_nuit);
                continue;
            end if;
            if c.rattache_par = 'decision' then continue; end if;
            insert into app_negociateur_journal (app_fiche_id, app_personne_id, champ, avant, apres, a_signaler, nuit)
            select c.app_fiche_id, c.app_personne_id, x.champ, x.avant, x.apres, x.champ in ('email_vu', 'nom_vu'), v_nuit
              from (values ('nom_vu', c.nom_vu, r.nom_vu), ('email_vu', c.email_vu, r.email), ('telephone', c.telephone, r.telephone),
                           ('portable', c.portable, r.portable), ('user_type', c.user_type, r.user_type)) x(champ, avant, apres)
             where x.avant is distinct from x.apres;
            if c.present_chez_hektor is distinct from true then
                insert into app_negociateur_journal (app_fiche_id, app_personne_id, evenement, champ, avant, apres, nuit)
                values (c.app_fiche_id, c.app_personne_id, 'reapparue', 'present_chez_hektor', coalesce(c.present_chez_hektor::text, '?'), 'true', v_nuit);
            end if;
            update app_negociateur_fiche
               set nom_vu = r.nom_vu, email_vu = r.email, telephone = r.telephone, portable = r.portable, user_type = r.user_type,
                   actif_chez_hektor = true, present_chez_hektor = true, absent_depuis = null, derniere_vue = now(),
                   updated_at = case when (nom_vu, email_vu, telephone, portable, user_type) is distinct from (r.nom_vu, r.email, r.telephone, r.portable, r.user_type)
                                     then now() else updated_at end
             where app_fiche_id = c.app_fiche_id;
        end loop;
        -- les comptes que la liste de cette nuit ne porte plus (jamais le compte admin, rattaché par décision)
        if v_comptes_ok then
            for c in
                select f.* from app_negociateur_fiche f
                 where f.sorte = 'compte_utilisateur' and f.rattache_par <> 'decision' and f.present_chez_hektor
                   and not exists (select 1 from app_user_directory u where trim(u.id_user) = f.hektor_user_id)
            loop
                insert into app_negociateur_journal (app_fiche_id, app_personne_id, evenement, champ, avant, apres, nuit)
                values (c.app_fiche_id, c.app_personne_id, 'disparue', 'present_chez_hektor', 'true', 'false', v_nuit);
                update app_negociateur_fiche set present_chez_hektor = false, actif_chez_hektor = false, absent_depuis = coalesce(absent_depuis, now())
                 where app_fiche_id = c.app_fiche_id;
            end loop;
        end if;

        -- C. un n° d'utilisateur nouveau dans la répartition, sans fiche
        for r in
            select rp.u_id, coalesce((select a2.nom_au_moment from app_affaire_repartition a2 where trim(a2.hektor_user_id) = rp.u_id and a2.nom_au_moment !~* 'supprim'
                                       group by 1 order by count(*) desc limit 1), 'Utilisateur supprimé n° ' || rp.u_id) as nom_vu
              from (select distinct trim(hektor_user_id) as u_id from app_affaire_repartition where nullif(trim(hektor_user_id), '') is not null) rp
             where not exists (select 1 from app_negociateur_fiche f where f.hektor_user_id = rp.u_id)
        loop
            select * into v_ad from app_neg_adopter(r.nom_vu, null, null, null, 'numero_repartition', r.u_id);
            insert into app_negociateur_fiche (app_personne_id, sorte, hektor_user_id, nom_vu, actif_chez_hektor, present_chez_hektor, rattache_par)
            values (v_ad.o_personne, 'numero_repartition', r.u_id, r.nom_vu, false, false, v_ad.o_par)
            returning app_fiche_id into v_fiche;
            insert into app_negociateur_journal (app_fiche_id, app_personne_id, evenement, champ, apres, a_signaler, nuit)
            values (v_fiche, v_ad.o_personne, case when v_ad.o_signal = 'personne nouvelle' then 'personne_nouvelle' else 'adoptee' end, 'repartition',
                    coalesce(v_ad.o_signal, 'rattaché par ' || v_ad.o_par) || ' : u ' || r.u_id || ' ' || r.nom_vu, true, v_nuit);
        end loop;

        -- D. un compte de l'app sans personne : par l'e-mail d'une fiche de négociateur, à défaut par le nom (signalé)
        for r in
            select u.id, lower(trim(u.email)) as email,
                   coalesce(nullif(trim(coalesce(u.first_name, '') || ' ' || coalesce(u.last_name, '')), ''), u.display_name, '') as nom
              from app_user_profile u
             where not exists (select 1 from app_negociateur_personne p where p.app_user_id = u.id)
        loop
            select count(distinct f.app_personne_id), min(f.app_personne_id) into v_n, v_fiche
              from app_negociateur_fiche f join app_negociateur_personne p using (app_personne_id)
             where f.sorte = 'fiche_negociateur' and f.email_vu = r.email and p.app_user_id is null;
            if v_n = 1 then
                update app_negociateur_personne set app_user_id = r.id, updated_at = now() where app_personne_id = v_fiche;
                insert into app_negociateur_journal (app_personne_id, evenement, champ, apres, nuit)
                values (v_fiche, 'compte_app_relie', 'app_user_id', r.email || ' (par l''e-mail)', v_nuit);
                continue;
            end if;
            select count(*), min(app_personne_id) into v_n, v_fiche from app_negociateur_personne
             where type_personne not in ('agence', 'inconnu') and app_user_id is null and app_neg_cle_nom(nom) = app_neg_cle_nom(r.nom) and app_neg_cle_nom(r.nom) <> '';
            if v_n = 1 then
                update app_negociateur_personne set app_user_id = r.id, updated_at = now(),
                       a_valider = nullif(concat_ws(' ; ', a_valider, 'compte de l''app relié par le nom'), '')
                 where app_personne_id = v_fiche;
                insert into app_negociateur_journal (app_personne_id, evenement, champ, apres, a_signaler, nuit)
                values (v_fiche, 'compte_app_relie', 'app_user_id', r.email || ' (par le nom)', true, v_nuit);
            end if;
        end loop;

        -- E. la personne : actif recalculé (une fiche de négociateur active, ou un compte présent) ; jamais supprimée
        for c in
            select p.app_personne_id, p.actif,
                   coalesce(bool_or((f.sorte = 'fiche_negociateur' and f.actif_chez_hektor) or (f.sorte = 'compte_utilisateur' and f.present_chez_hektor is true)), false) as actif_nuit
              from app_negociateur_personne p join app_negociateur_fiche f using (app_personne_id)
             group by p.app_personne_id, p.actif
            having p.actif is distinct from coalesce(bool_or((f.sorte = 'fiche_negociateur' and f.actif_chez_hektor) or (f.sorte = 'compte_utilisateur' and f.present_chez_hektor is true)), false)
        loop
            update app_negociateur_personne set actif = c.actif_nuit, updated_at = now() where app_personne_id = c.app_personne_id;
            insert into app_negociateur_journal (app_personne_id, evenement, champ, avant, apres, nuit)
            values (c.app_personne_id, 'actif', 'actif', c.actif::text, c.actif_nuit::text, v_nuit);
        end loop;

        -- le compte rendu
        select jsonb_build_object(
                 'a_blanc', p_a_blanc, 'nuit', v_nuit, 'liste_ok', v_liste_ok, 'presents_hier', v_presents_hier, 'presents_nuit', v_presents_nuit,
                 'comptes', v_comptes, 'comptes_ok', v_comptes_ok,
                 'personnes', (select count(*) from app_negociateur_personne), 'fiches', (select count(*) from app_negociateur_fiche),
                 'evenements', coalesce((select jsonb_object_agg(evenement, n) from (select evenement, count(*) n from app_negociateur_journal where nuit = v_nuit and traite_le is null group by 1) e), '{}'::jsonb),
                 'signaux', (select count(*) from app_negociateur_journal where nuit = v_nuit and a_signaler and traite_le is null),
                 'detail', coalesce((select jsonb_agg(jsonb_build_object('evenement', j.evenement, 'champ', j.champ, 'avant', j.avant, 'apres', j.apres,
                                                                         'personne', p.nom, 'signal', j.a_signaler) order by j.id)
                                      from (select * from app_negociateur_journal where nuit = v_nuit and traite_le is null order by id limit 60) j
                                      left join app_negociateur_personne p on p.app_personne_id = j.app_personne_id), '[]'::jsonb))
          into v_rapport;
        if p_a_blanc then
            raise exception using errcode = 'P0A01', message = 'a_blanc';
        end if;
    exception when sqlstate 'P0A01' then
        null;  -- à blanc : toutes les écritures du bloc sont annulées, v_rapport reste
    end;
    return v_rapport;
end
$f$;
revoke all on function public.app_negociateur_registre_maintenir(text[], boolean) from public, anon, authenticated;
grant execute on function public.app_negociateur_registre_maintenir(text[], boolean) to service_role;
comment on function public.app_negociateur_registre_maintenir(text[], boolean) is
  'REGISTRE DES NÉGOCIATEURS, étape 2 (04/11/2026) -- la mise à jour de nuit. p_presents = les n° de négociateur que la liste de Hektor de CETTE nuit contient ; p_a_blanc = true : le même chemin, puis tout est annulé, seul le compte rendu sort. Voir notice/AUDIT_REGISTRE_NEGOCIATEURS_2026-11-04.md §12.';

-- ── 5. les signaux ouverts, et la main de l'admin qui les lève ──
create view public.app_v_negociateur_signaux with (security_invoker = true) as
select j.id, j.nuit, j.evenement, j.champ, j.avant, j.apres, j.app_personne_id, p.nom, p.type_personne,
       f.hektor_negociateur_id, f.hektor_user_id, j.vu_le, j.traite_le
  from public.app_negociateur_journal j
  left join public.app_negociateur_personne p on p.app_personne_id = j.app_personne_id
  left join public.app_negociateur_fiche f on f.app_fiche_id = j.app_fiche_id
 where j.a_signaler and j.traite_le is null;
revoke all on public.app_v_negociateur_signaux from anon, public;
grant select on public.app_v_negociateur_signaux to authenticated, service_role;

create or replace function public.app_negociateur_signal_traiter(p_id bigint) returns boolean
language plpgsql security definer set search_path to 'public' as $f$
begin
    if not public.is_app_admin() then raise exception 'réservé aux administrateurs'; end if;
    update app_negociateur_journal set traite_le = now(), traite_par = auth.uid() where id = p_id and a_signaler and traite_le is null;
    return found;
end
$f$;
revoke all on function public.app_negociateur_signal_traiter(bigint) from public, anon;
grant execute on function public.app_negociateur_signal_traiter(bigint) to authenticated, service_role;

-- ── 6. la clé de battement (déclarée AVANT d'être utilisée) ──
insert into public.app_worker_registry
  (worker_key, worker_name, worker_role, worker_type, criticality, frequency,
   status, owner, script_path, expected_max_runtime_minutes, monitoring_domain, source_notes)
values
  ('phase2.registre_negociateurs',
   'Registre des négociateurs : la mise à jour de nuit',
   'Adopte les fiches Hektor nouvelles, journalise chaque changement (avant / après), marque les absences, signale les '
   'changements d''e-mail, de n° d''utilisateur ou de nom et les personnes nouvelles. Interrupteur APP_REGISTRE_NEGOCIATEURS '
   '(.env) : 0 éteint, blanc = compte rendu seul, 1 = écrit.',
   'python_worker', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'phase2\sync\maintenir_registre_negociateurs.py',
   5, 'business',
   'Ajoutée le 04/11/2026 (registre des négociateurs, étape 2). Aucune requête chez Hektor : lit les listes déjà téléchargées.')
on conflict (worker_key) do nothing;

-- ── les contrôles : la fonction répond à blanc sans rien écrire ──
do $controle$
declare v jsonb; v_avant int; v_apres int;
begin
    select count(*) into v_avant from public.app_negociateur_journal;
    v := public.app_negociateur_registre_maintenir(
           (select array_agg(hektor_negociateur_id) from public.app_negociateur_fiche where sorte = 'fiche_negociateur' and present_chez_hektor), true);
    select count(*) into v_apres from public.app_negociateur_journal;
    if v is null or not (v ? 'personnes') then raise exception 'ARRET : la fonction de nuit ne rend pas de compte rendu'; end if;
    if v_apres <> v_avant then raise exception 'ARRET : l''essai à blanc a écrit % lignes au journal', v_apres - v_avant; end if;
    if has_function_privilege('authenticated', 'public.app_negociateur_registre_maintenir(text[], boolean)', 'EXECUTE') then
        raise exception 'ARRET : un compte connecté peut lancer la fonction de nuit';
    end if;
    if (select count(*) from public.app_worker_registry where worker_key = 'phase2.registre_negociateurs') <> 1 then
        raise exception 'ARRET : la clé de battement n''est pas déclarée';
    end if;
end
$controle$;
