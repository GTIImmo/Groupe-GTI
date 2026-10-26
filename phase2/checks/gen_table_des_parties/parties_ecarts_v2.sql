create or replace view public.app_v_affaire_partie_ecarts with (security_invoker = true) as
with attendu as (
    select q.app_affaire_id, q.role, q.rang, q.app_contact_id,
           case when q.role like 'notaire%' then null else q.hektor_contact_id end as hektor_contact_id,
           q.est_principal, q.fiche_sans_nom, q.transaction_presente
      from public.app_affaire_ledger l cross join lateral public.app_affaire_partie_calculer(l) q),
reel as (
    select p.app_affaire_id, p.role, p.rang, p.app_contact_id,
           case when p.role like 'notaire%' then null else p.hektor_contact_id end as hektor_contact_id,
           p.est_principal, p.fiche_sans_nom, p.transaction_presente
      from public.app_affaire_partie p where p.origine = 'listes_du_registre')
select case when r.app_affaire_id is null then 'manquante'
            when a.app_affaire_id is null then 'en_trop'
            else 'differente' end::text as ecart,
       coalesce(a.app_affaire_id, r.app_affaire_id) as app_affaire_id,
       coalesce(a.role, r.role) as role,
       coalesce(a.rang, r.rang) as rang,
       coalesce(a.app_contact_id, r.app_contact_id) as app_contact_id,
       null::text as detail
  from attendu a full join reel r
    on r.app_affaire_id = a.app_affaire_id and r.role = a.role and r.rang = a.rang
 where a.app_affaire_id is null or r.app_affaire_id is null
    or (a.app_contact_id, a.hektor_contact_id, a.est_principal, a.fiche_sans_nom, a.transaction_presente)
       is distinct from (r.app_contact_id, r.hektor_contact_id, r.est_principal, r.fiche_sans_nom, r.transaction_presente)
union all
select 'erreur_du_declencheur', e.app_affaire_id, null, null, null, e.erreur
  from public.app_affaire_partie_erreur e where e.le > now() - interval '24 hours';
