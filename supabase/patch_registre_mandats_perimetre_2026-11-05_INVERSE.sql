-- Retour arrière de patch_registre_mandats_perimetre_2026-11-05.sql : la vue reprend les droits de son propriétaire, la
-- règle de lecture par périmètre est retirée (la règle admin/manager, d'origine, reste).
alter view public.app_registre_mandats_current reset (security_invoker);
drop policy if exists app_mandat_register_current_select_perimetre on public.app_mandat_register_current;
