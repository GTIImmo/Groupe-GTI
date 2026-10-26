
-- ══ LES ESSAIS (dans la transaction ; tout sera annule a la fin) ══════════════════════════════════════
create temp table essai (n int, quoi text, valeur text) on commit drop;
grant all on essai to authenticated;

-- E1 : le patch a-t-il tout pose ?
insert into essai select 10, 'parties posees', count(*)::text from public.app_affaire_partie;
insert into essai select 11, 'parties par role', string_agg(role || '=' || n, ' ') from (select role, count(*) n from public.app_affaire_partie group by 1 order by 1) x;
insert into essai select 12, 'ecarts de la sentinelle juste apres la pose', count(*)::text from public.app_v_affaire_partie_ecarts;
insert into essai select 13, 'liens acquereurs dans la vue', count(*)::text from public.app_contact_relations_current where role_contact like 'acquereur%';

-- E2 : la nuit qui renvoie TOUT SANS CHANGEMENT (le cas de chaque nuit) : le declencheur ne doit pas tourner
DO $e$ declare t0 timestamptz; n0 bigint; begin
  select count(*) into n0 from public.app_affaire_partie;
  t0 := clock_timestamp();
  update public.app_affaire_ledger set acquereurs_json = acquereurs_json, mandants_json = mandants_json, present_in_hektor = present_in_hektor;
  insert into essai values (20, 'update des 31 103 transactions SANS changement, AVEC declencheur (ms)',
                            round(extract(epoch from clock_timestamp() - t0) * 1000)::text);
  insert into essai select 21, 'parties inchangees apres cet update', (count(*) = n0)::text from public.app_affaire_partie;
end $e$;

-- E3 : la nuit du 27/10 (C4) qui CHANGE tous les vendeurs : le declencheur tourne partout
DO $e$ declare t0 timestamptz; n bigint; begin
  t0 := clock_timestamp();
  update public.app_affaire_ledger
     set mandants_json = (select jsonb_agg(x || '{"essai": 1}'::jsonb) from jsonb_array_elements(mandants_json) x)
   where jsonb_typeof(mandants_json) = 'array' and jsonb_array_length(mandants_json) > 0;
  get diagnostics n = row_count;
  insert into essai values (30, 'update qui CHANGE les vendeurs de ' || n || ' transactions, AVEC declencheur (ms)',
                            round(extract(epoch from clock_timestamp() - t0) * 1000)::text);
end $e$;
insert into essai select 31, 'ecarts apres ce grand changement', count(*)::text from public.app_v_affaire_partie_ecarts;

-- E4 : un acquereur RETIRE d'une transaction : ses parties suivent
DO $e$ declare a bigint; avant int; apres int; begin
  select app_affaire_id into a from public.app_affaire_ledger
   where jsonb_typeof(acquereurs_json) = 'array' and jsonb_array_length(acquereurs_json) = 3 and present_in_hektor limit 1;
  select count(*) into avant from public.app_affaire_partie where app_affaire_id = a and role = 'acquereur';
  update public.app_affaire_ledger set acquereurs_json = acquereurs_json - 2 where app_affaire_id = a;
  select count(*) into apres from public.app_affaire_partie where app_affaire_id = a and role = 'acquereur';
  insert into essai values (40, 'transaction ' || a || ' : acquereurs avant / apres le retrait du 3e', avant || ' / ' || apres);
end $e$;

-- E5 : une transaction RETIREE chez Hektor : ses parties restent, marquees
DO $e$ declare a bigint; begin
  select app_affaire_id into a from public.app_affaire_ledger where present_in_hektor and app_contact_id is not null limit 1;
  update public.app_affaire_ledger set present_in_hektor = false where app_affaire_id = a;
  insert into essai select 50, 'transaction ' || a || ' retiree : parties gardees / marquees retirees',
         count(*) || ' / ' || count(*) filter (where not transaction_presente) from public.app_affaire_partie where app_affaire_id = a;
  insert into essai select 51, 'elle sort de la vue des liens', (count(*) = 0)::text
    from public.app_contact_relations_current where relation_key like 'aff\_' || a || '\_%';
end $e$;

-- E6 : le declencheur EN PANNE ne fait PAS echouer l'ecriture (on force une panne : une contrainte impossible)
alter table public.app_affaire_partie add constraint essai_panne check (rang < 0) not valid;
DO $e$ declare a bigint; ok boolean := true; begin
  select app_affaire_id into a from public.app_affaire_ledger where jsonb_typeof(acquereurs_json) = 'array' and present_in_hektor limit 1;
  begin
    update public.app_affaire_ledger set acquereurs_json = acquereurs_json || '[]'::jsonb, app_contact_id = app_contact_id,
                                         hektor_acquereur_id = coalesce(hektor_acquereur_id, '') || '' where app_affaire_id = a;
    update public.app_affaire_ledger set present_in_hektor = not present_in_hektor where app_affaire_id = a;
  exception when others then ok := false;
  end;
  insert into essai values (60, 'avec le declencheur en panne, l''ecriture du registre passe quand meme', ok::text);
  insert into essai select 61, 'la panne est notee au journal', (count(*) > 0)::text from public.app_affaire_partie_erreur;
  insert into essai select 62, 'et la sentinelle la voit', (count(*) filter (where ecart = 'erreur_du_declencheur') > 0)::text from public.app_v_affaire_partie_ecarts;
end $e$;
alter table public.app_affaire_partie drop constraint essai_panne;

-- E7 : la reconstruction remet tout d'aplomb
insert into essai select 70, 'reconstruction : parties posees', public.app_affaire_partie_reconstruire()::text;
delete from public.app_affaire_partie_erreur;
insert into essai select 71, 'ecarts apres la reconstruction', count(*)::text from public.app_v_affaire_partie_ecarts;

-- E8 : le temps de la fiche d'un contact, et des invites d'un RDV (par bien)
DO $e$ declare j json; begin
  execute 'explain (analyze, format json) select * from public.app_contact_relations_current where hektor_contact_id = ''10354701''' into j;
  insert into essai values (80, 'fiche contact JACQUIER : preparation / execution (ms)', (j->0->>'Planning Time') || ' / ' || (j->0->>'Execution Time'));
  execute 'explain (analyze, format json) select * from public.app_contact_relations_current where hektor_contact_id = ''10216900''' into j;
  insert into essai values (81, 'fiche contact 10216900 : preparation / execution (ms)', (j->0->>'Planning Time') || ' / ' || (j->0->>'Execution Time'));
  execute 'explain (analyze, format json) select hektor_contact_id, role_contact from public.app_contact_relations_current where app_dossier_id = 1376593' into j;
  insert into essai values (82, 'invites d''un RDV (par bien) : preparation / execution (ms)', (j->0->>'Planning Time') || ' / ' || (j->0->>'Execution Time'));
end $e$;

-- E9 : les DROITS -- un commercial (142 biens) ne voit que les parties de SES transactions
set local role authenticated;
select set_config('request.jwt.claims', '{"sub": "05beded4-3e17-4a0c-ab58-e2c63da3da24", "role": "authenticated"}', true);
insert into essai select 90, 'commercial : parties visibles / transactions visibles',
       (select count(*) from public.app_affaire_partie) || ' / ' || (select count(*) from public.app_affaire_ledger);
insert into essai select 91, 'commercial : parties visibles HORS de ses transactions (doit valoir 0)',
       count(*)::text from public.app_affaire_partie p
        where not exists (select 1 from public.app_affaire_ledger l where l.app_affaire_id = p.app_affaire_id);
insert into essai select 92, 'commercial : peut-il ecrire dans la table ? (doit valoir false)',
       has_table_privilege('authenticated', 'public.app_affaire_partie', 'INSERT')::text;
reset role;

-- LA FIN : on ANNULE TOUT, et les resultats remontent dans le message
DO $e$ begin
  raise exception 'RESULTATS_ESSAI %', (select string_agg(n || ' | ' || quoi || ' : ' || coalesce(valeur, 'NULL'), E'\n' order by n) from essai);
end $e$;
