-- REPETITION de patch_sheet_ecrit_memoire_colonne_a_2026-11-20.sql -- LECTURE SEULE, a jouer APRES le patch.
-- Chaque valeur a son attendu a cote. Une lecture qui echoue n'est JAMAIS un vert.
select json_build_object(
  'colonnes', (select string_agg(column_name || ':' || data_type || ':' || is_nullable, ' | ' order by ordinal_position)
               from information_schema.columns where table_schema = 'public' and table_name = 'app_sheet_ecrit'),
  'attendu_colonnes', 'id_unique:text:NO | colonne:text:NO | valeur:text:NO | avant:text:NO | etat:text:NO | vague:text:NO | '
                      'ligne_vue:integer:YES | ecrit_le:timestamp with time zone:NO | defait_le:timestamp with time zone:YES | '
                      'origine:text:NO',
  'clef_primaire', (select string_agg(a.attname, ',' order by k.ord)
                    from pg_constraint c
                    cross join lateral unnest(c.conkey) with ordinality as k(attnum, ord)
                    join pg_attribute a on a.attrelid = c.conrelid and a.attnum = k.attnum
                    where c.conrelid = 'public.app_sheet_ecrit'::regclass and c.contype = 'p'),
  'attendu_clef_primaire', 'id_unique,colonne',
  'contraintes_check', (select count(*) from pg_constraint
                        where conrelid = 'public.app_sheet_ecrit'::regclass and contype = 'c'),
  'attendu_contraintes_check', 4,
  'rls_active', (select relrowsecurity from pg_class where oid = 'public.app_sheet_ecrit'::regclass),
  'attendu_rls_active', true,
  'politiques', (select json_agg(json_build_object('nom', policyname, 'geste', cmd, 'roles', roles))
                 from pg_policies where schemaname = 'public' and tablename = 'app_sheet_ecrit'),
  'attendu_politiques', '1 seule : app_sheet_ecrit_select_manager, SELECT, {authenticated}',
  'anon_lit', has_table_privilege('anon', 'public.app_sheet_ecrit', 'SELECT'), 'attendu_anon_lit', false,
  'anon_ecrit', has_table_privilege('anon', 'public.app_sheet_ecrit', 'INSERT')
             or has_table_privilege('anon', 'public.app_sheet_ecrit', 'UPDATE')
             or has_table_privilege('anon', 'public.app_sheet_ecrit', 'DELETE'), 'attendu_anon_ecrit', false,
  'authenticated_ecrit', has_table_privilege('authenticated', 'public.app_sheet_ecrit', 'INSERT')
             or has_table_privilege('authenticated', 'public.app_sheet_ecrit', 'UPDATE')
             or has_table_privilege('authenticated', 'public.app_sheet_ecrit', 'DELETE'), 'attendu_authenticated_ecrit', false,
  'service_role_ecrit', has_table_privilege('service_role', 'public.app_sheet_ecrit', 'INSERT')
             and has_table_privilege('service_role', 'public.app_sheet_ecrit', 'UPDATE'), 'attendu_service_role_ecrit', true,
  'lignes', (select count(*) from public.app_sheet_ecrit), 'attendu_lignes', 0,
  'ancienne_forme_presente', exists (select 1 from information_schema.columns where table_schema = 'public'
                                     and table_name = 'app_sheet_ecrit' and column_name = 'app_chaine_id'),
  'attendu_ancienne_forme_presente', false
) r;
