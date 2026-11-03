-- Pilotage (03/11/2026) — deux lectures réservées aux admins, en LECTURE SEULE, sur le modèle de app_pilotage_stock.
-- Accord de Frédéric : « FAIS LES DEUX MANQUES » (l'onglet Acquéreurs, et dans Affaires le prix obtenu,
-- l'exclusif contre le simple, les notaires). Audit : notice/AUDIT_PILOTAGE_GLOBAL_2026-11-02.md § 36.
-- Elles n'écrivent rien. Retour arrière : patch_pilotage_acquereurs_affaires_2026-11-03_INVERSE.sql.
--
-- 1. app_pilotage_acquereurs(p_annee) : le fichier acquéreurs en CHIFFRES (aucune fiche nominative ne sort),
--    par négociateur au nom de la fiche. Mesuré le 03/11 : 17 075 fiches, 9 465 vivantes, 4 018 avec une
--    recherche active, 6 013 joignables, 1 725 créées en 2026 contre 1 633.
-- 2. app_pilotage_affaires_plus(p_annee) : une ligne par offre (prix ÷ prix du mandat, type de mandat,
--    jours depuis le début du mandat) et une par acte (étude du notaire, délai compromis → acte, retard),
--    pour l'année et la précédente ; l'écran agrège et filtre par agence.
--    Mesuré le 03/11 : 573 offres acceptées comparables, prix obtenu médian 94,6 %.

create or replace function public.app_pilotage_acquereurs(p_annee integer)
returns jsonb
language plpgsql
stable
security definer
set search_path to 'public'
as $function$
begin
  if not public.is_app_admin() then
    return null;
  end if;
  return (
    with p as (
      select p_annee as annee,
             case when p_annee = extract(year from current_date)::int then to_char(current_date, 'MM-DD') else '12-31' end as borne,
             to_char(current_date - 90, 'YYYY-MM-DD') as il_y_a_90
    ), c as (
      select app_contact_id, hektor_target_id, nullif(trim(commercial_nom), '') as nego, archive,
             date_enregistrement as d_crea, date_maj,
             nullif(trim(email), '') is not null as mail,
             nullif(trim(coalesce(phone_primary, phone_secondary)), '') is not null as tel
        from public.app_contact_current
       where typologies_json ? 'acquéreur' and not coalesce(supprimee_chez_hektor, false)
    ), s as (
      select app_contact_id,
             bool_or(nullif(regexp_replace(coalesce(prix_max, ''), '[^0-9.]', '', 'g'), '')::numeric > 0) as budget,
             max(nullif(regexp_replace(coalesce(prix_max, ''), '[^0-9.]', '', 'g'), '')::numeric) as budget_max,
             bool_or(jsonb_typeof(villes_json) = 'array' and jsonb_array_length(villes_json) > 0) as secteur,
             bool_or((jsonb_typeof(types_json) = 'object' and types_json <> '{}'::jsonb)
                  or (jsonb_typeof(types_json) = 'array' and jsonb_array_length(types_json) > 0)) as typ,
             bool_or(coalesce(surface_min, '') ~ '[1-9]' or coalesce(pieces_min, '') ~ '[1-9]' or coalesce(chambre_min, '') ~ '[1-9]') as taille
        from public.app_contact_search_current
       where is_active and not coalesce(archive, false)
       group by 1
    ), o as (
      select hektor_acquereur_id, min(substr(date, 1, 10)) as premiere_offre,
             bool_or(kind = 'vente') as achete,
             bool_or((kind = 'offre' and state in ('accepted', 'proposed')) or (kind = 'compromis' and state = 'active')) as en_cours
        from public.app_affaire_ledger
       where present_in_hektor and hektor_acquereur_id is not null and date ~ '^\d{4}-\d{2}-\d{2}'
       group by 1
    ), f as (
      select c.*, s.app_contact_id is not null as rech, coalesce(s.budget, false) as budget, s.budget_max,
             coalesce(s.secteur, false) as secteur, coalesce(s.typ, false) as typ, coalesce(s.taille, false) as taille,
             o.premiere_offre, coalesce(o.achete, false) as achete, coalesce(o.en_cours, false) as en_cours
        from c
        left join s using (app_contact_id)
        left join o on o.hektor_acquereur_id = c.hektor_target_id
    ), v as (
      select * from f where not archive
    )
    select jsonb_build_object(
      'total', (select count(*) from f),
      'vivantes', (select count(*) from v),
      'crees', (select count(*) from f, p where f.d_crea like p.annee || '%'),
      'crees_prec', (select count(*) from f, p where f.d_crea like (p.annee - 1) || '%' and substr(f.d_crea, 6, 5) <= p.borne),
      'touchees90', (select count(*) from v, p where v.date_maj >= p.il_y_a_90),
      'sans_nego', (select count(*) from v where v.nego is null),
      'sans_contact', (select count(*) from v where not v.mail and not v.tel),
      'qualite', (select jsonb_build_object(
          'tel', count(*) filter (where tel), 'mail', count(*) filter (where mail), 'recherche', count(*) filter (where rech),
          'type', count(*) filter (where typ), 'budget', count(*) filter (where budget), 'secteur', count(*) filter (where secteur),
          'taille', count(*) filter (where taille)) from v),
      'vivier', (select jsonb_build_array(
          count(*),
          count(*) filter (where rech),
          count(*) filter (where budget and secteur and typ),
          count(*) filter (where budget and secteur and typ and mail and tel),
          count(*) filter (where budget and secteur and typ and mail and tel and not en_cours and not achete)) from v),
      'conversion', (select jsonb_build_object(
          'fiches', count(*),
          'avec_offre', count(*) filter (where f.premiere_offre >= substr(f.d_crea, 1, 10)),
          'acheteurs', count(*) filter (where f.achete and f.premiere_offre >= substr(f.d_crea, 1, 10)),
          'delai_median', percentile_cont(0.5) within group (order by (f.premiere_offre::date - substr(f.d_crea, 1, 10)::date))
                          filter (where f.premiere_offre >= substr(f.d_crea, 1, 10)),
          'sous30', count(*) filter (where f.premiere_offre >= substr(f.d_crea, 1, 10)
                                       and f.premiere_offre::date - substr(f.d_crea, 1, 10)::date <= 30))
          from f, p
         where f.d_crea ~ '^\d{4}-\d{2}-\d{2}' and substr(f.d_crea, 1, 4)::int in (p.annee - 2, p.annee - 1)),
      'budgets', (select coalesce(jsonb_agg(jsonb_build_object('tranche', x.t, 'n', x.n) order by x.t), '[]'::jsonb)
          from (select case when budget_max < 100000 then 1 when budget_max < 150000 then 2 when budget_max < 200000 then 3
                            when budget_max < 300000 then 4 else 5 end as t, count(*) as n
                  from v where budget group by 1) x),
      'negos', (select coalesce(jsonb_agg(to_jsonb(x) order by x.crees desc, x.vivantes desc), '[]'::jsonb)
          from (select f.nego as nom,
                       count(*) filter (where f.d_crea like p.annee || '%') as crees,
                       count(*) filter (where f.d_crea like (p.annee - 1) || '%' and substr(f.d_crea, 6, 5) <= p.borne) as crees_prec,
                       count(*) filter (where not f.archive) as vivantes,
                       count(*) filter (where not f.archive and f.rech) as avec_rech,
                       count(*) filter (where not f.archive and f.budget and f.secteur and f.typ) as completes,
                       count(*) filter (where not f.archive and f.mail and f.tel) as joignables,
                       count(*) filter (where not f.archive and f.date_maj >= p.il_y_a_90) as touchees90
                  from f, p
                 where f.nego is not null
                 group by f.nego, p.annee, p.borne, p.il_y_a_90
                having count(*) filter (where not f.archive) > 0) x)
    )
  );
end;
$function$;

create or replace function public.app_pilotage_affaires_plus(p_annee integer)
returns jsonb
language plpgsql
stable
security definer
set search_path to 'public'
as $function$
begin
  if not public.is_app_admin() then
    return null;
  end if;
  return (
    with m as (
      select distinct on (hektor_annonce_id, numero_mandat)
             hektor_annonce_id, numero_mandat, mandat_montant, upper(trim(mandat_type)) as mandat_type,
             nullif(substr(mandat_date_debut, 1, 10), '') as debut, agence_nom
        from public.app_mandat_register_current
       where hektor_annonce_id is not null and coalesce(register_source_kind, '') <> 'recherche'
       order by hektor_annonce_id, numero_mandat, refreshed_at desc
    ), ag as (
      select distinct on (hektor_annonce_id) hektor_annonce_id, agence_nom
        from public.app_mandat_register_current
       where hektor_annonce_id is not null
       order by hektor_annonce_id, refreshed_at desc
    ), o as (
      select l.hektor_annonce_id, l.numero_mandat, substr(l.date, 1, 10) as d, l.state,
             nullif(regexp_replace(coalesce(l.montant, ''), '[^0-9.]', '', 'g'), '')::numeric as montant
        from public.app_affaire_ledger l
       where l.kind = 'offre' and l.present_in_hektor and l.date ~ '^\d{4}-\d{2}-\d{2}'
         and substr(l.date, 1, 4)::int between p_annee - 1 and p_annee
         and l.hektor_annonce_id not in (23287, 24933, 61398, 62774, 62965)
    ), offres as (
      select o.d, o.state, m.agence_nom as agence, m.mandat_type as type,
             round(o.montant / nullif(m.mandat_montant, 0), 4) as ratio,
             case when m.debut ~ '^\d{4}-\d{2}-\d{2}$' then o.d::date - m.debut::date end as jours,
             o.d = min(o.d) over (partition by o.hektor_annonce_id, o.numero_mandat) as premiere
        from o join m using (hektor_annonce_id, numero_mandat)
    ), c as (
      select app_chaine_id, min(substr(date, 1, 10)) as d_cp, max(nullif(substr(date_acte, 1, 10), '')) as prevue
        from public.app_affaire_ledger
       where kind = 'compromis' and present_in_hektor and date ~ '^\d{4}-\d{2}-\d{2}'
       group by 1
    ), v as (
      select distinct on (l.app_chaine_id) l.app_chaine_id, l.hektor_annonce_id, substr(l.date, 1, 10) as d,
             nullif(trim(l.notaires_json -> 'entree' ->> 'id'), '') as etude_id,
             coalesce(nullif(trim(l.notaires_json -> 'entree' ->> 'nom'), ''), nullif(trim(l.notaire_mandant_nom), '')) as etude
        from public.app_affaire_ledger l
       where l.kind = 'vente' and l.present_in_hektor and l.date ~ '^\d{4}-\d{2}-\d{2}'
         and substr(l.date, 1, 4)::int between p_annee - 1 and p_annee
         and l.hektor_annonce_id not in (23287, 24933, 61398, 62774, 62965)
       order by l.app_chaine_id, l.date
    ), actes as (
      select v.d, ag.agence_nom as agence, v.etude_id, v.etude,
             case when c.d_cp ~ '^\d{4}-\d{2}-\d{2}$' then v.d::date - c.d_cp::date end as delai,
             case when c.prevue ~ '^\d{4}-\d{2}-\d{2}$' then v.d > c.prevue end as retard
        from v
        left join c using (app_chaine_id)
        left join ag on ag.hektor_annonce_id = v.hektor_annonce_id
    )
    select jsonb_build_object(
      'offres', (select coalesce(jsonb_agg(to_jsonb(offres)), '[]'::jsonb) from offres),
      'actes', (select coalesce(jsonb_agg(to_jsonb(actes)), '[]'::jsonb) from actes)
    )
  );
end;
$function$;

revoke all on function public.app_pilotage_acquereurs(integer) from public, anon;
revoke all on function public.app_pilotage_affaires_plus(integer) from public, anon;
grant execute on function public.app_pilotage_acquereurs(integer) to authenticated, service_role;
grant execute on function public.app_pilotage_affaires_plus(integer) to authenticated, service_role;
