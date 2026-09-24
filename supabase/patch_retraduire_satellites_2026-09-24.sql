-- ═══════════════════════════════════════════════════════════════════════════
-- LES TABLES SATELLITES SUIVENT LE CONTACT QUAND IL CHANGE DE NUMERO
-- 24/09/2026 -- audit : notice/AUDIT_RAPPROCHEMENTS_NUMERO_CONTACT_2026-09-24.md
-- ═══════════════════════════════════════════════════════════════════════════
--
-- LE DEFAUT. Treize tables de Supabase designent un contact par son numero
-- (hektor_contact_id) et vivent dans Supabase : le build ne les refait pas.
-- Leurs ecrivains figent ce numero a la naissance de la ligne (ON CONFLICT ...
-- DO UPDATE ne le touche jamais) et rien ne declenche de recalcul quand un
-- contact change de numero. Or les ecrans lisent PAR ce numero :
--   app_get_rapprochements_for_dossier   ligne sans nom / email / telephone
--   app_count_rapprochements_for_contact  « N biens » ne la compte pas
--   app_generate_rapprochement_alerts     pas d'alerte
-- Mesure du 24/09 : 69 rapprochements (5 contacts) + 3 compteurs sous un
-- ANCIEN numero Hektor, 0 action de negociateur dessus. +30 attendus la nuit du
-- 25/09 (les 8 contacts neufs du 24/09 recoivent leur identite).
--
-- La bascule du 23/09 avait traduit ces 13 tables UNE FOIS, a la main. L'etape
-- de nuit app_contact_id_propager ne remplit que app_contact_id quand il est
-- VIDE : elle ne corrige jamais un numero perime.
--
-- LA REGLE. Une ligne est traduite si son hektor_contact_id :
--   * est un numero de Hektor (< 10 000 000 : sept chiffres au plus) ;
--   * n'est plus porte par AUCUN contact de app_contact_current (un contact
--     neuf pas encore traduit garde le sien : on n'y touche pas) ;
--   * est la cible Hektor (hektor_target_id) d'UN SEUL contact, sous identite.
-- On ecrit l'identite dans hektor_contact_id et on remplit app_contact_id s'il
-- est vide.
--
-- CE QU'ON SAUTE, ET QU'ON COMPTE (jamais d'erreur, jamais d'ecrasement) :
--   ambigus         la cible designe plusieurs contacts
--   contradictoires app_contact_id deja rempli avec une AUTRE identite
--   collisions      4 tables ont un index unique sur le contact (override,
--                   pending, high_water, search_pending) : si l'identite y a
--                   deja sa ligne, traduire ferait tomber toute la reparation
--
-- A BLANC PAR DEFAUT (p_appliquer = false) : compte, n'ecrit rien, ne trace
-- rien. C'est aussi LA SONDE : une seule regle, lue par le run et par la sante.
-- Aucun declencheur sur ces 13 tables (verifie le 24/09) : pas d'effet de bord.
--
-- APPELEE CHAQUE NUIT par phase2/identite/propager_numeros_contact.py, AVANT
-- app_contact_id_propager, juste apres le push des contacts.
--
-- RETOUR ARRIERE : chaque traduction est tracee (app_contact_retraduction_log,
-- detail par table) ; l'ancien numero reste lisible dans hektor_target_id du
-- contact. drop function public.app_contact_retraduire_satellites(boolean);
-- ═══════════════════════════════════════════════════════════════════════════

create table if not exists public.app_contact_retraduction_log (
  run_at  timestamptz primary key default clock_timestamp(),
  total   integer not null,
  detail  jsonb   not null,
  sautes  jsonb   not null
);
alter table public.app_contact_retraduction_log enable row level security;

-- ── CORPS DEBUT ─────────────────────────────────────────────────────────────
create or replace function public.app_contact_retraduire_satellites(p_appliquer boolean default false)
returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  cibles constant text[] := array[
    'app_rapprochement',
    'app_search_count_high_water',
    'app_email_envoi',
    'app_proposition',
    'app_relance_rapprochement',
    'app_google_calendar_event_link',
    'app_bien_acquereur_statut',
    'app_espace_visite_request',
    'app_espace_message',
    'app_pending_resolution',
    'app_contact_pending',
    'app_contact_override',
    'app_search_pending'
  ];
  -- les tables a index unique sur le contact, et ce qui complete la cle
  uniques constant jsonb := jsonb_build_object(
    'app_contact_override',        '',
    'app_contact_pending',         '',
    'app_search_count_high_water', '',
    'app_search_pending',          'and u.search_index = t.search_index'
  );
  cible            text;
  collision        text;
  n                integer;
  a_traduire       jsonb := '{}'::jsonb;
  traduits         jsonb := '{}'::jsonb;
  ambigus          jsonb := '{}'::jsonb;
  contradictoires  jsonb := '{}'::jsonb;
  collisions       jsonb := '{}'::jsonb;
  total_a          integer := 0;
  total_t          integer := 0;
  total_s          integer := 0;
  traduisibles     jsonb := '{}'::jsonb;
  total_p          integer := 0;
  n_a              integer;
  n_s              integer;
  ecarts           jsonb := '{}'::jsonb;
begin
  -- La correspondance ancien numero Hektor -> identite, une fois pour toutes.
  drop table if exists pg_temp.rs_correspondance;
  create temp table rs_correspondance on commit drop as
    select c.hektor_target_id       as ancien,
           min(c.hektor_contact_id) as identite,
           -- l'identite EST le numero de l'app (0 ecart sur 62 003 le 24/09), mais
           -- app_contact_id est parfois VIDE dans app_contact_current (10 fiches le
           -- 24/09) : sans ce repli, la comparaison avec NULL ne dit ni oui ni non
           -- et la ligne passait entre les mailles (vu en preuve : 17 lignes).
           coalesce(min(c.app_contact_id), min(c.hektor_contact_id)::bigint) as app_id,
           count(*)                 as n
      from public.app_contact_current c
     where c.hektor_target_id  ~ '^[0-9]{1,7}$'
       and c.hektor_contact_id ~ '^[0-9]{8,}$'
     group by c.hektor_target_id;
  -- un numero encore porte par un contact (neuf, pas encore traduit) : intouchable
  delete from rs_correspondance m
   where exists (select 1 from public.app_contact_current x
                  where x.hektor_contact_id = m.ancien);
  create index on rs_correspondance (ancien);

  foreach cible in array cibles loop
    collision := case when uniques ? cible
      then format('exists (select 1 from public.%I u where u.hektor_contact_id = m.identite %s)',
                  cible, uniques ->> cible)
      else 'false' end;

    execute format('select count(*) from public.%I t
                      join rs_correspondance m on m.ancien = t.hektor_contact_id', cible) into n;
    if n = 0 then continue; end if;
    a_traduire := a_traduire || jsonb_build_object(cible, n);
    total_a := total_a + n;
    n_a := n;
    n_s := 0;

    execute format('select count(*) from public.%I t
                      join rs_correspondance m on m.ancien = t.hektor_contact_id
                     where m.n > 1', cible) into n;
    if n > 0 then ambigus := ambigus || jsonb_build_object(cible, n); total_s := total_s + n; n_s := n_s + n; end if;

    execute format('select count(*) from public.%I t
                      join rs_correspondance m on m.ancien = t.hektor_contact_id
                     where m.n = 1 and t.app_contact_id is not null
                       and t.app_contact_id::text is distinct from m.app_id::text', cible) into n;
    if n > 0 then contradictoires := contradictoires || jsonb_build_object(cible, n); total_s := total_s + n; n_s := n_s + n; end if;

    execute format('select count(*) from public.%I t
                      join rs_correspondance m on m.ancien = t.hektor_contact_id
                     where m.n = 1
                       and (t.app_contact_id is null or t.app_contact_id::text = m.app_id::text)
                       and %s', cible, collision) into n;
    if n > 0 then collisions := collisions || jsonb_build_object(cible, n); total_s := total_s + n; n_s := n_s + n; end if;

    -- ce qui sera traduit ; et LE COMPTE DOIT TOMBER JUSTE : a_traduire =
    -- traduisibles + sautes. Un ecart = une ligne qu'aucune regle ne classe.
    execute format('select count(*) from public.%I t
                      join rs_correspondance m on m.ancien = t.hektor_contact_id
                     where m.n = 1
                       and (t.app_contact_id is null or t.app_contact_id::text = m.app_id::text)
                       and not %s', cible, collision) into n;
    if n > 0 then traduisibles := traduisibles || jsonb_build_object(cible, n); total_p := total_p + n; end if;
    if n + n_s <> n_a then ecarts := ecarts || jsonb_build_object(cible, n_a - n - n_s); end if;

    if p_appliquer then
      execute format('update public.%I t
                         set hektor_contact_id = m.identite,
                             app_contact_id    = coalesce(t.app_contact_id, m.app_id)
                        from rs_correspondance m
                       where m.ancien = t.hektor_contact_id
                         and m.n = 1
                         and (t.app_contact_id is null or t.app_contact_id::text = m.app_id::text)
                         and not %s', cible, collision);
      get diagnostics n = row_count;
      if n > 0 then traduits := traduits || jsonb_build_object(cible, n); total_t := total_t + n; end if;
    end if;
  end loop;

  if p_appliquer and (total_t > 0 or total_s > 0) then
    insert into public.app_contact_retraduction_log (run_at, total, detail, sautes)
    values (clock_timestamp(), total_t, traduits,
            jsonb_build_object('ambigus', ambigus, 'contradictoires', contradictoires,
                               'collisions', collisions))
    on conflict (run_at) do nothing;
  end if;

  return jsonb_build_object(
    'mode',        case when p_appliquer then 'applique' else 'a_blanc' end,
    'a_traduire',  total_a,
    'traduits',    total_t,
    'sautes',      total_s,
    'traduisibles', total_p,
    'ecarts',      ecarts,
    'detail',      jsonb_build_object('a_traduire', a_traduire, 'traduisibles', traduisibles,
                                      'traduits', traduits,
                                      'ambigus', ambigus, 'contradictoires', contradictoires,
                                      'collisions', collisions));
end
$function$;
-- ── CORPS FIN ───────────────────────────────────────────────────────────────

revoke all on function public.app_contact_retraduire_satellites(boolean) from public, anon, authenticated;
grant execute on function public.app_contact_retraduire_satellites(boolean) to service_role;

-- A LANCER APRES, dans cet ordre (Frederic) :
--   select public.app_contact_retraduire_satellites(false);   -- a blanc : attendu a_traduire 72, ecarts {}
--   select public.app_contact_retraduire_satellites(true);    -- pour de bon
--   select public.app_contact_retraduire_satellites(false);   -- attendu a_traduire 0
