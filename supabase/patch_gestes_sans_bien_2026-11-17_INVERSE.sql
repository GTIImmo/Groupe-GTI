-- ═══════════════════════════════════════════════════════════════════════════
-- LE RETOUR ARRIERE DES GESTES SANS BIEN -- 17/11/2026
--
-- ⭐ Il ne retire QUE la fonction que le patch a creee. Il ne touche a rien
--   d'autre : le patch n'avait rien modifie d'existant.
--
-- ⛔ ET IL JUGE SA PROPRE PART (lecon 31) : il verifie que la fonction a bien
--   disparu, ET que les quatre soeurs sont toujours la.
-- ═══════════════════════════════════════════════════════════════════════════
begin;

drop function if exists public.app_action_status_sans_bien();

do $$
declare n integer;
begin
  select count(*) into n from pg_proc p join pg_namespace x on x.oid = p.pronamespace
   where x.nspname = 'public' and p.proname = 'app_action_status_sans_bien';
  if n <> 0 then raise exception '⛔ la fonction est encore la (%)', n; end if;

  -- ⭐ LES SOEURS, PROUVEES INTACTES
  select count(*) into n from pg_proc p join pg_namespace x on x.oid = p.pronamespace
   where x.nspname = 'public'
     and p.proname in ('app_action_status', 'app_action_resolve',
                       'app_console_can_request_job', 'app_negociateur_signal_traiter');
  if n <> 4 then raise exception '⛔ une fonction soeur a disparu (% sur 4)', n; end if;

  raise notice '✅ RETOUR ARRIERE COMPLET, les 4 soeurs intactes';
end $$;

commit;
