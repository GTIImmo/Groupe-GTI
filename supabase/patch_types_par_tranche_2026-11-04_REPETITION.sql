-- REPETITION de patch_types_par_tranche_2026-11-04.sql, dans une transaction ANNULEE.
-- Pose la fonction, la compare a la fonction d'origine sur TOUS les contacts (en abimant d'abord des types
-- dans la transaction), verifie les droits, puis ROLLBACK : rien ne reste.
begin;

\ir patch_types_par_tranche_2026-11-04.sql

do $rep$
declare
  abimes integer; repares integer := 0; t text; bornes text[] := array['', '10100000', '10200000', '10300000', '10400000', '10500000', '10600000', '10700000', '99999999'];
  i integer; reste integer;
begin
  -- 1. temoin : la fonction d'origine ne trouve rien a changer (etat juste)
  if public.app_recalculer_tous_les_types() <> 0 then raise exception 'REP 1 : etat de depart deja faux'; end if;
  -- 2. on abime 500 types, la fonction par tranches doit les reparer TOUS, et rien d'autre
  update public.app_contact_current set relation_roles_json = '["abime"]'::jsonb
   where hektor_contact_id in (select hektor_contact_id from public.app_contact_current order by md5(hektor_contact_id) limit 500);
  get diagnostics abimes = row_count;
  for i in 1 .. array_length(bornes, 1) - 1 loop
    repares := repares + public.app_recalculer_types_tranche(bornes[i], bornes[i + 1]);
  end loop;
  if repares <> abimes then raise exception 'REP 2 : % abimes, % repares', abimes, repares; end if;
  -- 3. temoin inverse : la fonction d'origine ne trouve plus RIEN (les deux regles disent la meme chose)
  reste := public.app_recalculer_tous_les_types();
  if reste <> 0 then raise exception 'REP 3 : la fonction d''origine trouve encore % ecarts', reste; end if;
  -- 4. bornes absurdes : rien
  if public.app_recalculer_types_tranche('2', '1') <> 0 or public.app_recalculer_types_tranche(null, '1') <> 0 then
    raise exception 'REP 4 : bornes absurdes non refusees'; end if;
  -- 5. droits
  if has_function_privilege('anon', 'public.app_recalculer_types_tranche(text,text)', 'execute')
     or has_function_privilege('authenticated', 'public.app_recalculer_types_tranche(text,text)', 'execute')
     or not has_function_privilege('service_role', 'public.app_recalculer_types_tranche(text,text)', 'execute') then
    raise exception 'REP 5 : droits faux'; end if;
  raise notice 'REPETITION : 5/5 OK (% types abimes puis repares par tranches)', abimes;
end
$rep$;

rollback;
