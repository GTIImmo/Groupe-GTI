-- ═══════════════════════════════════════════════════════════════════════════
-- LES MENUS DES FILTRES SANS RELIRE TOUT LE REGISTRE DES MANDATS                               26/10/2026
-- Décision de Frédéric (26/10 soir) : « ok fais choix 1 » -- MÊME liste qu'aujourd'hui, fabriquée en UNE lecture.
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md §22 (audit), §23 (ce patch).
--
-- AUJOURD'HUI : à chaque ouverture, l'écran (api.ts, loadMandatFilterCatalog) relit les 24 576 lignes du registre par
--   pages de 1 000 -- 25 lectures à ~820 ms -- pour en tirer ~90 valeurs (négociateurs, agences, statuts, validation,
--   diffusion, portails). Ces valeurs remplissent les menus des filtres ET la liste « Agence » du formulaire de création
--   d'annonce. Le catalogue de la nuit n'a ni agence, ni statut, ni validation : il ne peut pas les donner.
-- CE PATCH :
--   1. une vue app_filter_catalog_registre : les MÊMES valeurs, BRUTES (l'écran les nettoie et les trie comme avant :
--      même trim, même tri), DISTINCTES, calculées par la base en une lecture (84 ms mesurés pour un admin) ;
--      security_invoker : elle voit exactement ce que la personne voit du registre (admin / manager : tout ;
--      négociateur : rien, comme aujourd'hui).
--   2. la règle du registre enveloppée : (select is_app_manager_or_admin()) -- MÊME SENS, contrôlée une fois par
--      lecture au lieu d'une fois par ligne (2,2 s -> 84 ms). L'écran Registre en profite aussi.
-- CE QUI NE CHANGE PAS : le registre, ses écrivains (nuit, worker, RPC : service_role ou propriétaire), qui voit quoi.
--   La vue est NEUVE : personne ne la lit tant que l'écran ne l'appelle pas, et l'écran retombe sur l'ancienne lecture
--   si elle manque ou ne rend aucune agence. ⛔ RIEN chez Hektor.
-- Retour arrière : _INVERSE.sql.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
SET LOCAL lock_timeout = '5s';

-- ── 1. LA RÈGLE DU REGISTRE, ENVELOPPÉE ─────────────────────────────────────────────────────────────────
alter policy app_mandat_register_current_select_active_users on public.app_mandat_register_current
    using ((select public.is_app_manager_or_admin()));

-- ── 2. LES VALEURS DES MENUS, EN UNE LECTURE ────────────────────────────────────────────────────────────
-- Les valeurs restent BRUTES (pas de btrim ici) : c'est l'écran qui nettoie, avec le MÊME code qu'avant (uniqSorted :
-- trim JavaScript, vides retirés, tri 'fr'). Un btrim SQL ne retire que les espaces, le trim JavaScript retire aussi
-- les tabulations et les espaces insécables : les faire en deux endroits pourrait donner deux listes.
create or replace view public.app_filter_catalog_registre with (security_invoker = true) as
select x.filter_type, x.filter_value
  from public.app_registre_mandats_current r
  cross join lateral (values
        ('commercial',                 r.commercial_nom),
        ('agence',                     r.agence_nom),
        ('statut',                     r.statut_annonce),
        ('validation_diffusion_state', r.validation_diffusion_state),
        ('diffusable',                 case when coalesce(r.diffusable, '0') = '1' then 'diffusable' else 'non_diffusable' end)
     ) x(filter_type, filter_value)
 where r.numero_mandat is not null and r.numero_mandat <> '' and x.filter_value is not null
union
select 'passerelle', p
  from public.app_registre_mandats_current r
  cross join lateral unnest(string_to_array(coalesce(r.portails_resume, ''), ',')) p
 where r.numero_mandat is not null and r.numero_mandat <> '';

comment on view public.app_filter_catalog_registre is
  '26/10 : les valeurs des menus tirees du registre des mandats (negociateurs, agences, statuts, validation, diffusion, portails), BRUTES et distinctes, en UNE lecture. Remplace les 25 lectures par pages de loadMandatFilterCatalog (api.ts) pour un admin. security_invoker : voit ce que la personne voit du registre.';

revoke all on public.app_filter_catalog_registre from anon, authenticated;
grant select on public.app_filter_catalog_registre to authenticated;

COMMIT;

SELECT 1 AS "#", 'la regle du registre est enveloppee (une fois par lecture)' AS controle,
       (SELECT CASE WHEN pg_get_expr(polqual, polrelid) ~ '^\(?\s*SELECT is_app_manager_or_admin\(\)' THEN 'OK' ELSE '⛔ ECHEC (' || pg_get_expr(polqual, polrelid) || ')' END
          FROM pg_policy WHERE polname = 'app_mandat_register_current_select_active_users' AND polrelid = 'public.app_mandat_register_current'::regclass) AS verdict
UNION ALL SELECT 2, 'la vue existe, security_invoker, lisible par authenticated et PAS par anon',
       CASE WHEN to_regclass('public.app_filter_catalog_registre') IS NOT NULL
             AND (SELECT reloptions FROM pg_class WHERE oid = 'public.app_filter_catalog_registre'::regclass) @> array['security_invoker=true']
             AND has_table_privilege('authenticated', 'public.app_filter_catalog_registre', 'SELECT')
             AND NOT has_table_privilege('anon', 'public.app_filter_catalog_registre', 'SELECT') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'les types rendus (attendus : agence, commercial, diffusable, passerelle, statut, validation_diffusion_state)',
       (SELECT string_agg(filter_type || ' ' || n, ' · ' ORDER BY filter_type) FROM (SELECT filter_type, count(*) n FROM public.app_filter_catalog_registre GROUP BY 1) z)
ORDER BY 1;
