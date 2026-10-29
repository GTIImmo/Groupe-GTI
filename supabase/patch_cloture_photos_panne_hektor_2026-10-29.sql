-- =============================================================================
--  CLOTURE DES 277 TRAVAUX PHOTOS DU BLOCAGE HEKTOR DE LA NUIT DU 28-29/10   29/10/2026
-- =============================================================================
--  ACCORD DE FREDERIC, 29/10 : « tu as mon accord pour solder les photos pour
--  qu'elles soient reprises au prochain run les 277 ».
--
--  LE CONSTAT (mesure du 29/10 a 11:05). Notre IP bloquee par Hektor de ~00:55 a
--  ~07:14 (Paris). Le balayage de 23:00 a fait 723 annonces, puis 277 travaux
--  `sync_hektor_photos` en erreur entre 00:56 et 01:47 : 277 annonces, TOUS des
--  pannes (« fetch failed »), tous poses par le balayage. Aucun refus de Hektor.
--
--  MEME GESTE QUE patch_cloture_photos_panne_hektor_2026-10-28.sql (les 726 de la
--  nuit d'avant), au lot pres : le bouton « Abandonner ce geste » de l'ecran
--  (app_action_resolve, mode 'abandon') en un seul geste, une ligne dans
--  app_pending_resolution par travail, 'defait' = [] (rien a defaire pour une
--  lecture de photos). Il fait taire data.travaux_en_erreur et data.geste_abandonne.
--  ⚠ Le travail RESTE en `error` (historique). Rien n'est supprime ailleurs.
--
--  LA REPRISE. Ce patch ne repose RIEN : le balayage reprend ces 277 annonces de
--  lui-meme -- une erreur de PANNE n'ecarte plus une annonce (correctif ecb3241,
--  Console/enqueue_photos_masquees_lot.js MOTIF_PANNE), et le frein des 24 h se
--  leve quand toutes ses erreurs sont des pannes ET que Hektor repond. Depuis le
--  29/10 10:56 le balayage lit en ADMIN (dc6d70e) : il ne se fait plus passer pour
--  le negociateur a chaque annonce.
--
--  MARQUE : resolved_by = 'cloture_panne_hektor_2026-10-29' et payload_json.lot.
--  Retour arriere : patch_cloture_photos_panne_hektor_2026-10-29_INVERSE.sql
--  Controle : ..._REPETITION.sql
-- =============================================================================
begin;

do $$
declare
  v_cibles int;
  v_poses  int;
begin
  select count(*) into v_cibles
    from public.app_console_job j
   where j.job_type = 'sync_hektor_photos'
     and j.status   = 'error'
     and j.finished_at >= '2026-10-28 22:00:00+00'   -- 23:00 a Paris (28/10)
     and j.finished_at <  '2026-10-29 05:00:00+00'   -- 06:00 a Paris (29/10)
     and coalesce(j.error_message, '') ~* '(fetch failed|time ?out|timed out|ETIMEDOUT|ECONNRESET|ECONNREFUSED|ENOTFOUND|EAI_AGAIN|socket hang up|connexion_refusee|Job interrompu)'
     and not exists (select 1 from public.app_pending_resolution r
                      where r.objet = 'geste' and r.payload_json->>'job_id' = j.id::text);

  -- Garde : le compte mesure le 29/10 a 11:05. Autre chose = quelqu'un est passe avant,
  -- ou la selection ne vise pas ce qu'on croit -> on s'arrete.
  if v_cibles <> 277 then
    raise exception 'ARRET : % travaux cibles au lieu de 277 -- rien n''est ecrit', v_cibles;
  end if;

  insert into public.app_pending_resolution
    (objet, app_dossier_id, hektor_annonce_id, mode, cause, push_attempts, payload_json, resolved_by)
  select 'geste', j.app_dossier_id, j.hektor_annonce_id, 'abandon',
         left(coalesce(j.error_message, 'sans message'), 200),
         coalesce(j.attempt_count, 0),
         jsonb_build_object('defait',       '[]'::jsonb,
                            'job_id',       j.id::text,
                            'job_type',     j.job_type,
                            'requested_at', j.requested_at,
                            'payload_json', j.payload_json,
                            'lot',          'cloture_panne_hektor_2026-10-29',
                            'raison',       'blocage IP Hektor 29/10 ~00:55 -> ~07:14 ; le balayage reprend ces annonces (correctif ecb3241)'),
         'cloture_panne_hektor_2026-10-29'
    from public.app_console_job j
   where j.job_type = 'sync_hektor_photos'
     and j.status   = 'error'
     and j.finished_at >= '2026-10-28 22:00:00+00'
     and j.finished_at <  '2026-10-29 05:00:00+00'
     and coalesce(j.error_message, '') ~* '(fetch failed|time ?out|timed out|ETIMEDOUT|ECONNRESET|ECONNREFUSED|ENOTFOUND|EAI_AGAIN|socket hang up|connexion_refusee|Job interrompu)'
     and not exists (select 1 from public.app_pending_resolution r
                      where r.objet = 'geste' and r.payload_json->>'job_id' = j.id::text);
  get diagnostics v_poses = row_count;

  if v_poses <> 277 then
    raise exception 'ARRET : % lignes posees au lieu de 277 -- tout est annule', v_poses;
  end if;
  raise notice 'OK : 277 travaux de la panne clos (mode abandon)';
end
$$;

commit;
