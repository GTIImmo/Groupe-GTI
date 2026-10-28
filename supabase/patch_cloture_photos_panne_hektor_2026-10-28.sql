-- =============================================================================
--  CLOTURE DES 726 TRAVAUX PHOTOS DE LA PANNE HEKTOR DU 27-28/10     28/10/2026
-- =============================================================================
--  LE CONSTAT. Hektor injoignable de 23:57 (27/10) a ~06:24 (28/10). Le balayage
--  des photos masquees a frappe a la porte toutes les 10 s : 726 travaux
--  `sync_hektor_photos` en erreur, 726 annonces, TOUS des pannes (718 « fetch
--  failed », 7 delais depasses, 1 connexion ratee). Aucun refus de Hektor.
--
--  POURQUOI LES CLORE. Ils font sonner deux alertes qui ne se tairont pas seules :
--    · data.geste_abandonne (727) -- jusqu'au 27/11 (fenetre de 30 jours) ;
--    · data.travaux_en_erreur (741, CRITIQUE) -- sans fin, tant qu'un humain n'a
--      pas repondu (et le plafond de 200 du moniteur, corrige a part).
--  Il n'y a rien a refaire a la main : le balayage reprend ces annonces de
--  lui-meme depuis le correctif ecb3241 (« une porte fermee n'est pas un refus »).
--
--  CE QUE FAIT CE PATCH : EXACTEMENT ce que fait le bouton « Abandonner ce geste »
--  de l'ecran (app_action_resolve, mode 'abandon'), en un seul geste au lieu de
--  726 clics : une ligne dans app_pending_resolution par travail. Pour un travail
--  de photos, app_action_resolve n'a rien a defaire (aucune ligne du carnet
--  n'appartient a un travail pose par le balayage -- controle 3 de la repetition) :
--  'defait' vaut donc [] comme il le vaudrait au clic.
--  ⚠ Le travail RESTE en `error` : c'est de l'historique, c'est voulu (meme regle
--    que le bouton). Rien n'est supprime, rien n'est modifie ailleurs.
--
--  MARQUE : resolved_by = 'cloture_panne_hektor_2026-10-28' et payload_json.lot,
--  pour que l'INVERSE ne touche QUE ces lignes.
--  Retour arriere : patch_cloture_photos_panne_hektor_2026-10-28_INVERSE.sql
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
     and j.finished_at >= '2026-10-27 22:00:00+00'   -- 23:00 a Paris
     and j.finished_at <  '2026-10-28 02:00:00+00'   -- 03:00 a Paris
     and coalesce(j.error_message, '') ~* '(fetch failed|time ?out|timed out|ETIMEDOUT|ECONNRESET|ECONNREFUSED|ENOTFOUND|EAI_AGAIN|socket hang up|connexion_refusee|Job interrompu)'
     and not exists (select 1 from public.app_pending_resolution r
                      where r.objet = 'geste' and r.payload_json->>'job_id' = j.id::text);

  -- Garde : le compte mesure le 28/10. Autre chose = quelqu'un est passe avant,
  -- ou la selection ne vise pas ce qu'on croit -> on s'arrete.
  if v_cibles <> 726 then
    raise exception 'ARRET : % travaux cibles au lieu de 726 -- rien n''est ecrit', v_cibles;
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
                            'lot',          'cloture_panne_hektor_2026-10-28',
                            'raison',       'panne Hektor 27/10 23:57 -> 28/10 06:24 ; le balayage reprend ces annonces (correctif ecb3241)'),
         'cloture_panne_hektor_2026-10-28'
    from public.app_console_job j
   where j.job_type = 'sync_hektor_photos'
     and j.status   = 'error'
     and j.finished_at >= '2026-10-27 22:00:00+00'
     and j.finished_at <  '2026-10-28 02:00:00+00'
     and coalesce(j.error_message, '') ~* '(fetch failed|time ?out|timed out|ETIMEDOUT|ECONNRESET|ECONNREFUSED|ENOTFOUND|EAI_AGAIN|socket hang up|connexion_refusee|Job interrompu)'
     and not exists (select 1 from public.app_pending_resolution r
                      where r.objet = 'geste' and r.payload_json->>'job_id' = j.id::text);
  get diagnostics v_poses = row_count;

  if v_poses <> 726 then
    raise exception 'ARRET : % lignes posees au lieu de 726 -- tout est annule', v_poses;
  end if;
  raise notice 'OK : 726 travaux de la panne clos (mode abandon)';
end
$$;

commit;
