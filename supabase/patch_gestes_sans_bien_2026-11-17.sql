-- ═══════════════════════════════════════════════════════════════════════════
-- LES GESTES SANS BIEN -- LA PORTE QUI MANQUAIT, ET LE BOUTON « VU »
-- 17/11/2026
--
-- ⛔⛔ LE DEFAUT, TROUVE PARCE QUE FREDERIC A DIT « NON IMPOSSIBLE RIEN DANS LE
--   MONITORING ». Il avait raison, et le code le prouve : le panneau qui porte
--   « J'ai refait » / « Abandonner ce geste » (SanteSystemeScreen.tsx, composant
--   TrancherIci) part d'un NUMERO DE BIEN -- il appelle
--   localiserAnnonceParNumeroHektor(numero) puis app_action_status(dossier).
--   ⭐ UN GESTE SANS BIEN N'A DONC AUCUN BIEN A CLIQUER : il est INTRANCHABLE.
--
--   MESURE : 17 travaux en erreur sur 1 045 n'ont pas d'annonce
--     (refresh_console_contact_data . update_hektor_contact .
--      create_hektor_draft_annonce)
--   -- mais ils sont 1 SUR 1 de ce qui attend un humain AUJOURD'HUI, et ce rouge
--   est LE SEUL qui envoie un e-mail chaque matin.
--
-- ⭐⭐⭐ ET LE VERROU N'EST PAS LE PROBLEME -- c'est la mesure qui l'a dit, et elle
--   a divise le travail par trois : `app_console_can_request_job` rend `true`
--   des la 2e condition pour un admin ou un manager, SANS MEME REGARDER le bien.
--   Donc `app_action_resolve` SAIT DEJA trancher un geste sans bien.
--   ➡ IL NE MANQUE QUE L'AFFICHAGE. On n'ajoute donc AUCUNE regle de droit.
--
-- CE QUE CE PATCH POSE, ET RIEN DE PLUS :
--   ① app_action_status_sans_bien()  -- la MEME lecture que app_action_status,
--      mais pour les gestes qui n'ont NI dossier NI annonce. Memes filtres,
--      meme forme de sortie, meme reserve aux admins.
--   ② le droit d'executer, pour `authenticated` seulement.
--
-- ⛔ CE QU'IL NE TOUCHE PAS : app_action_status, app_action_resolve,
--   app_console_can_request_job, la vue app_en_attente_humain, et le RPC
--   app_negociateur_signal_traiter -- tous laisses A L'IDENTIQUE.
--
-- RETOUR ARRIERE : patch_gestes_sans_bien_2026-11-17_INVERSE.sql
-- CONTROLES      : patch_gestes_sans_bien_2026-11-17_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════
begin;

-- ① LE GARDE-FOU : si la fonction existe deja, on ne la remplace pas en silence
do $$
begin
  if exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
              where n.nspname = 'public'
                and p.proname = 'app_action_status_sans_bien') then
    raise notice 'la fonction existe deja -- create or replace la met a jour';
  end if;
end $$;

-- ② LA LECTURE DES GESTES SANS BIEN
--
-- ⭐ LES QUATRE FILTRES SONT COPIES DE app_action_status, PAS REINVENTES :
--     status = 'error'
--     (5 tentatives epuisees OU plus de 3 h)   -- @seuil-3h du 15/10
--     moins de 30 jours                        -- au-dela, l'ecran ne montre plus
--     pas deja tranche                         -- app_pending_resolution
--   Une regle recopiee de travers, c'est deux verites : on garde les memes.
--
-- ⭐ ET LA CONDITION QUI LA DISTINGUE est la seule ligne neuve :
--     app_dossier_id IS NULL AND hektor_annonce_id IS NULL
--   -- donc cette fonction et sa soeur ne se CHEVAUCHENT JAMAIS : un geste
--   appartient a l'une ou a l'autre, jamais aux deux.
create or replace function public.app_action_status_sans_bien()
returns jsonb
language plpgsql
stable security definer
set search_path to 'public'
as $function$
declare
  v_role   text;
  v_gestes jsonb;
begin
  v_role := public.app_console_current_role();
  -- coalesce : un role inconnu (NULL) n'est PAS un administrateur.
  if not coalesce(v_role in ('admin', 'manager'), false) then
    raise exception 'forbidden_action_status_sans_bien' using errcode = '42501';
  end if;

  select coalesce(jsonb_agg(jsonb_build_object(
           'job_id',     j.id,
           'job_type',   j.job_type,
           'erreur',     left(coalesce(j.error_message, ''), 200),
           'tentatives', coalesce(j.attempt_count, 0),
           'depuis',     j.updated_at)
         order by j.updated_at desc), '[]'::jsonb)
    into v_gestes
    from public.app_console_job j
   where j.app_dossier_id is null
     and j.hektor_annonce_id is null
     and j.status = 'error'
     and (coalesce(j.attempt_count, 0) >= 5
          or j.requested_at < now() - interval '3 hours')
     and j.requested_at > now() - interval '30 days'
     and not exists (select 1 from public.app_pending_resolution r
                      where r.objet = 'geste'
                        and r.payload_json->>'job_id' = j.id::text);

  return jsonb_build_object('abandonnes', jsonb_array_length(v_gestes),
                            'gestes', v_gestes);
end
$function$;

-- ③ LES DROITS : comme ses soeurs, et PAS PLUS
--    ⛔ `revoke from public` ne ferme pas `authenticated` -- faute deja payee
--      deux fois. On revoque donc public ET anon NOMMEMENT.
revoke all on function public.app_action_status_sans_bien() from public, anon;
grant execute on function public.app_action_status_sans_bien() to authenticated, service_role;

-- ④ LES CONTROLES, DANS LA MEME TRANSACTION
do $$
declare n integer;
begin
  select count(*) into n from pg_proc p join pg_namespace x on x.oid = p.pronamespace
   where x.nspname = 'public' and p.proname = 'app_action_status_sans_bien';
  if n <> 1 then raise exception '⛔ la fonction n a pas ete creee (%)', n; end if;

  -- ⭐ anon NE DOIT PAS pouvoir l'executer
  if has_function_privilege('anon',
       'public.app_action_status_sans_bien()', 'EXECUTE') then
    raise exception '⛔ anon peut executer la fonction -- le revoke n a pas tenu';
  end if;
  -- ⭐ authenticated DOIT pouvoir
  if not has_function_privilege('authenticated',
       'public.app_action_status_sans_bien()', 'EXECUTE') then
    raise exception '⛔ authenticated ne peut PAS executer la fonction';
  end if;

  -- ⭐⭐ LE TEMOIN : il existe BIEN un geste sans bien a montrer aujourd'hui,
  --   sinon on aurait pose une porte sur une piece vide sans le savoir.
  select count(*) into n from public.app_console_job j
   where j.app_dossier_id is null and j.hektor_annonce_id is null
     and j.status = 'error'
     and (coalesce(j.attempt_count, 0) >= 5
          or j.requested_at < now() - interval '3 hours')
     and j.requested_at > now() - interval '30 days'
     and not exists (select 1 from public.app_pending_resolution r
                      where r.objet = 'geste'
                        and r.payload_json->>'job_id' = j.id::text);
  raise notice '✅ la fonction est posee . elle a % geste(s) a montrer aujourd hui', n;
  if n = 0 then
    raise notice '⚠ ZERO : la porte est posee mais la piece est vide -- a verifier';
  end if;

  -- ⭐ LES SOEURS SONT INTACTES : on ne les a pas touchees
  select count(*) into n from pg_proc p join pg_namespace x on x.oid = p.pronamespace
   where x.nspname = 'public'
     and p.proname in ('app_action_status', 'app_action_resolve',
                       'app_console_can_request_job', 'app_negociateur_signal_traiter');
  if n <> 4 then raise exception '⛔ une fonction soeur a disparu (% sur 4)', n; end if;
end $$;

commit;
