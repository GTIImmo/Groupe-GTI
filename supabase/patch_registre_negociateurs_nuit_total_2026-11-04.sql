-- REGISTRE DES NÉGOCIATEURS, étape 2 bis (04/11/2026) — la nuit lit désormais la liste COMPLÈTE des négociateurs
-- (sync_raw.py : plus de plafond de 5 pages pour « negos »). Frédéric : « VAS Y ».
-- Ce que ça change à la fonction de nuit :
--   . p_total (nouveau) = le total que Hektor annonce pour la liste complète ; une liste lue jusqu'à ce total FAIT FOI,
--     même si elle compte bien moins de fiches que la veille (l'étape 1 a compté 186 présentes à cause de vieilles pages
--     d'avril et de juin, la vraie liste en compte 152 : le plancher des 90 % aurait tout bloqué) ;
--   . plus de 5 fiches disparues en une nuit -> un signal « disparitions_nombreuses » (rien n'est annulé).
-- Retour arrière : patch_registre_negociateurs_nuit_total_2026-11-04_INVERSE.sql (remet la version à 2 paramètres).

alter table public.app_negociateur_journal drop constraint if exists app_negociateur_journal_evenement_check;
alter table public.app_negociateur_journal add constraint app_negociateur_journal_evenement_check
    check (evenement in ('changement', 'disparue', 'reapparue', 'adoptee', 'personne_nouvelle', 'compte_app_relie',
                         'actif', 'liste_incomplete', 'conflit', 'disparitions_nombreuses'));

drop function if exists public.app_negociateur_registre_maintenir(text[], boolean);

create or replace function public.app_negociateur_registre_maintenir(p_presents text[], p_a_blanc boolean default true, p_total integer default null)
returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
    v_rapport jsonb := '{}'::jsonb;
    v_presents_hier int; v_presents_nuit int; v_liste_ok boolean; v_comptes int; v_comptes_ok boolean;
    v_n int; r record; c record; v_ad record; v_fiche bigint;
    v_nuit date := current_date;
    v_disparues int := 0;
begin
    begin  -- le bloc qu'on annule pour l'essai à blanc
        -- les planchers
        select count(*) into v_presents_hier from app_negociateur_fiche where sorte = 'fiche_negociateur' and present_chez_hektor;
        v_presents_nuit := coalesce(cardinality(p_presents), 0);
        -- la liste est sûre si elle a été lue JUSQU'AU BOUT (autant de fiches que le total que Hektor annonce) ;
        -- à défaut de total, le plancher : au moins 90 % des fiches présentes la veille
        v_liste_ok := p_presents is not null and ((p_total is not null and v_presents_nuit >= p_total) or v_presents_nuit >= 0.9 * v_presents_hier);
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
                if not (r.n_id = any(p_presents)) then v_disparues := v_disparues + 1; end if;
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

        -- beaucoup de disparitions en une seule nuit : rien n'est annulé, mais un humain regarde
        if v_disparues > 5 then
            insert into app_negociateur_journal (evenement, champ, avant, apres, a_signaler, nuit)
            values ('disparitions_nombreuses', 'present_chez_hektor', v_presents_hier::text,
                    v_disparues || ' fiches absentes de la liste de Hektor cette nuit (liste de ' || v_presents_nuit || ' fiches'
                    || coalesce(', total annoncé ' || p_total, '') || ')', true, v_nuit);
        end if;

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
                 'a_blanc', p_a_blanc, 'nuit', v_nuit, 'liste_ok', v_liste_ok, 'total_annonce', p_total, 'disparues', v_disparues, 'presents_hier', v_presents_hier, 'presents_nuit', v_presents_nuit,
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
revoke all on function public.app_negociateur_registre_maintenir(text[], boolean, integer) from public, anon, authenticated;
grant execute on function public.app_negociateur_registre_maintenir(text[], boolean, integer) to service_role;
comment on function public.app_negociateur_registre_maintenir(text[], boolean, integer) is
  'REGISTRE DES NÉGOCIATEURS, étape 2 (04/11/2026) -- la mise à jour de nuit. p_presents = les n° de négociateur que la liste de Hektor de CETTE nuit contient (null = inconnue) ; p_a_blanc = true : le même chemin, puis tout est annulé ; p_total = le total annoncé par Hektor (une liste lue jusqu''au bout fait foi). Voir notice/AUDIT_REGISTRE_NEGOCIATEURS_2026-11-04.md §13-14.';

do $controle$
declare v jsonb; v_avant int; v_apres int;
begin
    select count(*) into v_avant from public.app_negociateur_journal;
    -- à blanc : une liste « complète » de 152 fiches (total 152) doit être acceptée, et ses disparitions comptées
    v := public.app_negociateur_registre_maintenir(
           (select array_agg(hektor_negociateur_id order by hektor_negociateur_id::int) from (select hektor_negociateur_id from public.app_negociateur_fiche
             where sorte = 'fiche_negociateur' and present_chez_hektor order by hektor_negociateur_id::int limit 152) x), true, 152);
    select count(*) into v_apres from public.app_negociateur_journal;
    if v_apres <> v_avant then raise exception 'ARRET : l''essai à blanc a écrit % lignes', v_apres - v_avant; end if;
    if not (v->>'liste_ok')::boolean then raise exception 'ARRET : une liste lue jusqu''à son total n''est pas acceptée : %', v; end if;
    if (v->>'disparues')::int <> 34 then raise exception 'ARRET : 34 disparitions attendues dans l''essai, % comptées', v->>'disparues'; end if;
    if has_function_privilege('authenticated', 'public.app_negociateur_registre_maintenir(text[], boolean, integer)', 'EXECUTE') then
        raise exception 'ARRET : un compte connecté peut lancer la fonction de nuit';
    end if;
    if to_regprocedure('public.app_negociateur_registre_maintenir(text[], boolean)') is not null then
        raise exception 'ARRET : l''ancienne version à 2 paramètres est restée';
    end if;
end
$controle$;
