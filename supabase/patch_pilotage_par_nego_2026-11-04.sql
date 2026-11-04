-- Pilotage (04/11/2026) — le filtre par négociateur, accord de Frédéric (« oui les deux tu as mon accord mais audit
-- avant », puis « OUI REPRENDS audit avec filtre sur le nom par securité »). Audit : notice/AUDIT_PILOTAGE_GLOBAL_2026-11-02.md §40-40 ter.
-- LECTURE SEULE, trois fonctions réservées aux admins (is_app_admin), mêmes droits qu'avant :
-- 1. app_pilotage_stock() rend aussi commercial_id (le n° de NÉGOCIATEUR du bien) ;
-- 2. app_pilotage_acquereurs prend p_negos (les n° de négociateur de la personne) et p_noms (repli par le nom) ;
-- 3. app_pilotage_affaires_plus ajoute nego / nego_nom à chaque offre, acte et compromis.
-- Un négociateur a deux numéros chez Hektor (fiche négociateur / compte utilisateur), et une personne a souvent UNE
-- fiche par agence (Marion BILLIG DURAND : 52, 39, 89). L'écran regroupe la personne par l'annuaire.
-- Retour arrière : patch_pilotage_par_nego_2026-11-04_INVERSE.sql

-- les signatures changent (une colonne de plus, deux paramètres de plus) : les anciennes doivent partir
drop function if exists public.app_pilotage_stock();
drop function if exists public.app_pilotage_acquereurs(integer, text);

CREATE FUNCTION public.app_pilotage_stock()
RETURNS TABLE (
    app_dossier_id                bigint,
    hektor_annonce_id             bigint,
    statut_annonce                text,
    agence_nom                    text,
    commercial_nom                text,
    commercial_id                 text,
    negociateur_email             text,
    prix                          numeric,
    mandat_type                   text,
    mandat_date_debut             text,
    mandat_date_fin               text,
    diffusable                    text,
    nb_portails_actifs            integer,
    price_change_last_old_value   numeric,
    price_change_last_new_value   numeric,
    honoraires                    numeric,
    honoraires_charge_acquereur   boolean
)
LANGUAGE sql
STABLE SECURITY DEFINER
SET search_path TO 'public'
AS $fn$
    -- Pilotage, onglet Stock, 02/11/2026 (+ commercial_id le 04/11). Voir supabase/patch_pilotage_par_nego_2026-11-04.sql
    with adm as (
        select public.is_app_admin() as ok
    ), b as (
        select d.*,
               substr(dt.detail_payload_json, nullif(strpos(dt.detail_payload_json, '"honoraires_json":"['), 0) + 18, 1500) as p
          from public.app_dossier_current d
          join adm on adm.ok
          left join public.app_dossier_detail_current dt on dt.app_dossier_id = d.app_dossier_id
         where d.statut_annonce in ('Actif', 'Sous offre', 'Sous compromis')
    ), j as (
        select b.app_dossier_id, (substr(b.p, 1, strpos(b.p, ']"') + 1)::jsonb #>> '{}')::jsonb as hj
          from b
         where b.p is not null and strpos(b.p, ']"') > 0
    ), e as (
        select j.app_dossier_id, lower(x->>'charge') as charge,
               case when x->>'id' ~ '^\d+$' then (x->>'id')::bigint end as id,
               nullif(regexp_replace(coalesce(x->>'taux', ''), '[^0-9.]', '', 'g'), '')::numeric as t
          from j, jsonb_array_elements(case when jsonb_typeof(j.hj) = 'array' then j.hj else '[]'::jsonb end) x
    ), der as (
        select distinct on (e.app_dossier_id, e.charge) e.app_dossier_id, e.charge, e.t
          from e
         where e.t > 0
         order by e.app_dossier_id, e.charge, e.id desc nulls last
    ), h as (
        select der.app_dossier_id, sum(der.t) as honoraires, bool_or(der.charge = 'acheteur') as acq
          from der
         group by der.app_dossier_id
    )
    select b.app_dossier_id, b.hektor_annonce_id, b.statut_annonce, b.agence_nom, b.commercial_nom, nullif(trim(b.commercial_id::text), ''),
           b.negociateur_email, b.prix, b.mandat_type, b.mandat_date_debut, b.mandat_date_fin, b.diffusable,
           b.nb_portails_actifs, b.price_change_last_old_value, b.price_change_last_new_value,
           h.honoraires, coalesce(h.acq, false)
      from b
      left join h on h.app_dossier_id = b.app_dossier_id;
$fn$;

create or replace function public.app_pilotage_acquereurs(p_annee integer, p_agence text default null,
                                                          p_negos text[] default null, p_noms text[] default null)
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
         -- 03/11 : l'agence choisie à l'écran, comparée sur la même clé que cleAgence() de lib/pilotage.ts
         and (p_agence is null or upper(regexp_replace(trim(translate(regexp_replace(coalesce(agence_nom, ''), '^\s*groupe\s+gti\s*', '', 'i'),
               'àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ', 'aaaeeeeiioouuucAAAEEEEIIOOUUUC')), '[\s-]+', '-', 'g')) = p_agence)
         -- 04/11 : le négociateur choisi à l'écran = TOUS ses numéros de négociateur (un par agence chez Hektor,
         -- regroupés par l'annuaire app_hektor_negotiator_agency_directory) ; par sécurité, une fiche sans numéro
         -- est reconnue par le nom (même clé que cleNom() de lib/pilotage.ts : sans civilité, sans accents, minuscules).
         and (p_negos is null
              or hektor_negociateur_id::text = any(p_negos)
              or (coalesce(nullif(trim(hektor_negociateur_id::text), ''), '0') = '0'
                  and lower(regexp_replace(trim(extensions.unaccent(regexp_replace(coalesce(commercial_nom, ''),
                        '^\s*(m_mme|mr\.?/mme\.?|mme\.?|mlle\.?|mr\.?|m\.)\s+', '', 'i'))), '\s+', ' ', 'g')) = any(coalesce(p_noms, '{}'))))
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
             nullif(substr(mandat_date_debut, 1, 10), '') as debut, agence_nom,
             nullif(trim(commercial_id::text), '') as nego, nullif(trim(commercial_nom), '') as nego_nom
        from public.app_mandat_register_current
       where hektor_annonce_id is not null and coalesce(register_source_kind, '') <> 'recherche'
       order by hektor_annonce_id, numero_mandat, refreshed_at desc
    ), ag as (
      select distinct on (hektor_annonce_id) hektor_annonce_id, agence_nom,
             nullif(trim(commercial_id::text), '') as nego, nullif(trim(commercial_nom), '') as nego_nom
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
      -- 04/11 : nego / nego_nom = le négociateur du MANDAT (n° de négociateur Hektor, pas le n° d'utilisateur)
      select o.d, o.state, m.agence_nom as agence, m.nego, m.nego_nom, m.mandat_type as type,
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
      select v.d, ag.agence_nom as agence, ag.nego, ag.nego_nom, v.etude_id, v.etude,
             case when c.d_cp ~ '^\d{4}-\d{2}-\d{2}$' then v.d::date - c.d_cp::date end as delai,
             case when c.prevue ~ '^\d{4}-\d{2}-\d{2}$' then v.d > c.prevue end as retard
        from v
        left join c using (app_chaine_id)
        left join ag on ag.hektor_annonce_id = v.hektor_annonce_id
    ), vendus as (
      select distinct app_chaine_id from public.app_affaire_ledger where kind = 'vente' and present_in_hektor
    ), en_cours as (
      -- 03/11 : les compromis en cours (pas encore d'acte), et leur notaire retrouvé par son numéro :
      -- le compromis ne porte son nom que 204 fois sur 630, son numéro 593 fois.
      -- app_chaine_id (ajouté le 03/11 soir, après le contrôle réel) : l'écran ne garde que les chaînes que le registre dit en compromis
      select l.app_chaine_id, substr(l.date, 1, 10) as d, nullif(substr(l.date_acte, 1, 10), '') as prevue, ag.agence_nom as agence, ag.nego, ag.nego_nom,
             nullif(trim(ct.hektor_target_id), '') as etude_id,
             coalesce(nullif(trim(ct.nom), ''), nullif(trim(l.notaire_mandant_nom), '')) as etude
        from public.app_affaire_ledger l
        left join public.app_contact_current ct on ct.hektor_contact_id = l.notaire_mandant_id
        left join ag on ag.hektor_annonce_id = l.hektor_annonce_id
       where l.kind = 'compromis' and l.present_in_hektor and l.state = 'active' and l.date ~ '^\d{4}-\d{2}-\d{2}'
         and l.hektor_annonce_id not in (23287, 24933, 61398, 62774, 62965)
         and not exists (select 1 from vendus where vendus.app_chaine_id = l.app_chaine_id)
    )
    select jsonb_build_object(
      'offres', (select coalesce(jsonb_agg(to_jsonb(offres)), '[]'::jsonb) from offres),
      'actes', (select coalesce(jsonb_agg(to_jsonb(actes)), '[]'::jsonb) from actes),
      'compromis', (select coalesce(jsonb_agg(to_jsonb(en_cours)), '[]'::jsonb) from en_cours)
    )
  );
end;
$function$;


revoke all on function public.app_pilotage_stock() from public, anon;
revoke all on function public.app_pilotage_acquereurs(integer, text, text[], text[]) from public, anon;
revoke all on function public.app_pilotage_affaires_plus(integer) from public, anon;
grant execute on function public.app_pilotage_stock() to authenticated, service_role;
grant execute on function public.app_pilotage_acquereurs(integer, text, text[], text[]) to authenticated, service_role;
grant execute on function public.app_pilotage_affaires_plus(integer) to authenticated, service_role;
