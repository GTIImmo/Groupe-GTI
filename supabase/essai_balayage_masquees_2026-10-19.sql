-- ============================================================================
-- ESSAI REEL DU BALAYAGE DES PHOTOS MASQUEES -- UNE SEULE ANNONCE
-- 19/10/2026                                     ⑦-8 marche 2, avant d'ecrire
-- ============================================================================
-- ⚠⚠ CE FICHIER ECRIT POUR DE VRAI : il pose UN travail, et le worker
--    « documents » appellera Hektor DEUX fois (les deux galeries).
--    Il n'y a pas de rollback : c'est l'essai, pas une repetition.
--
-- POURQUOI CET ESSAI AVANT D'ECRIRE L'EMPILEUR : parce que tout le dessin de la
-- marche 2 repose sur une affirmation que PERSONNE n'a verifiee en reel depuis
-- le 17/08 -- « le travail sync_hektor_photos ramene les masquees et les marque
-- correctement ». 314 travaux existent, le dernier a tourne le 27/09, et leur
-- `result_json` porte bien une cle `hidden` -- mais toujours a 0. Donc le chemin
-- n'a JAMAIS ete vu ramener une masquee. Un essai sur UNE annonce le prouve pour
-- 4 requetes Hektor.
--
-- LA CIBLE : annonce 62189 « Maison de village », Actif, app_dossier_id 1388194.
--   Choisie parce que TOUT est connu d'avance :
--     · chez nous ....... 4 photos, 0 masquee  (mesure du 19/10)
--     · chez Hektor ..... 3 MASQUEES           (sonde du 19/10, lecture seule)
--     · aucun travail en cours sur elle, et aucun sync_hektor_photos jamais pose
--
-- ⭐ LA PREDICTION, ECRITE AVANT (sinon ce n'est pas une preuve) :
--     result_json.hidden ...... 3
--     result_json.visible ..... 4   (nos 4 actuelles sont les visibles)
--     result_json.total ....... 7
--     app_console_photo ....... 7 lignes, dont 3 a visible = false
--     la BOITE PUBLIQUE ....... 4 photos, PAS 7   <- le verrou de la marche 1
--   Si `hidden` vaut 0, le dessin de la marche 2 est faux et il faut s'arreter.
--
-- ⚠ LE RISQUE, DIT : le travail marque « plus chez Hektor » toute photo qu'il ne
--   voit pas. Si la galerie visible de Hektor rendait MOINS de 4 photos, nos
--   surplus seraient marques absents. Trois choses limitent ce risque :
--     1. la regle DELETE-NEVER : on MARQUE, on ne supprime jamais ;
--     2. le garde-fou de LISTE VIDE (13/10) : une page vide ne marque RIEN ;
--     3. le retour arriere tient en une ligne (en bas de ce fichier).
--
-- APRES AVOIR COLLE : le worker prend le travail en ~10 s. Attendre ~1 min, puis
-- jouer la partie « CONTROLE » ci-dessous (elle ne fait que LIRE).
-- ============================================================================


-- ─────────────────────── 1. L'ETAT D'AVANT (lecture) ────────────────────────
-- A garder sous les yeux : c'est la reference du controle.

select 'AVANT' as moment,
       (select count(*) from app_console_photo where app_dossier_id = 1388194) as photos,
       (select count(*) from app_console_photo where app_dossier_id = 1388194 and visible is false) as masquees,
       (select count(*) from app_console_photo where app_dossier_id = 1388194 and derives_json ? 'w400') as avec_derive,
       (select coalesce(jsonb_array_length(images_preview_json_app), 0) from app_dossier_current where app_dossier_id = 1388194) as boite_publique;


-- ──────────────────── 2. ON POSE LE TRAVAIL (ecriture) ──────────────────────
-- ⚠ La charge est VIDE : c'est la forme exacte des 314 travaux existants
--   (payload_json = '{}'), on copie, on n'invente pas. priority 5 comme eux.

do $essai$
declare
  v_en_cours integer;
  v_id       uuid;
begin
  -- GARDE 1 : ne jamais doubler un travail en vol (regle du projet : ne jamais
  -- rejouer, les 403 repetes ont fait bannir l'IP le 20/08).
  select count(*) into v_en_cours
    from public.app_console_job
   where hektor_annonce_id = '62189'
     and status in ('pending','running');
  if v_en_cours > 0 then
    raise exception 'STOP : % travail(aux) deja en vol sur 62189 -- ne pas empiler', v_en_cours;
  end if;

  -- GARDE 2 : la cible doit etre le bon dossier (un numero ne se devine pas).
  if not exists (select 1 from public.app_dossier_current
                  where app_dossier_id = 1388194 and hektor_annonce_id::text = '62189') then
    raise exception 'STOP : 1388194 n est pas le dossier de l annonce 62189 -- remesurer';
  end if;

  insert into public.app_console_job (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority)
  values ('sync_hektor_photos', 1388194, '62189', '{}'::jsonb, 5)
  returning id into v_id;

  raise notice 'TRAVAIL POSE : % -- le service « documents » le prendra en ~10 s.', v_id;
  raise notice 'ATTENDRE ~1 min, puis jouer la partie CONTROLE (lecture seule).';
end
$essai$;


-- ============================================================================
-- 3. CONTROLE -- A JOUER ~1 MINUTE APRES. IL NE FAIT QUE LIRE.
-- ============================================================================
-- Decoller les lignes ci-dessous et les jouer seules.
--
--   select j.status, j.attempt_count, j.error_message,
--          j.result_json->>'hidden'  as hidden_attendu_3,
--          j.result_json->>'visible' as visible_attendu_4,
--          j.result_json->>'total'   as total_attendu_7,
--          j.result_json->>'photos_downloaded' as telechargees,
--          j.finished_at::text
--     from app_console_job j
--    where j.hektor_annonce_id = '62189' and j.job_type = 'sync_hektor_photos'
--    order by j.requested_at desc limit 1;
--
--   select 'APRES' as moment,
--          (select count(*) from app_console_photo where app_dossier_id = 1388194) as photos_attendu_7,
--          (select count(*) from app_console_photo where app_dossier_id = 1388194 and visible is false) as masquees_attendu_3,
--          (select count(*) from app_console_photo where app_dossier_id = 1388194 and present_in_hektor is false) as marquees_absentes_attendu_0,
--          (select coalesce(jsonb_array_length(images_preview_json_app),0) from app_dossier_current where app_dossier_id = 1388194) as boite_publique;
--
-- ⭐ LA BOITE PUBLIQUE ne doit PAS monter a 7. Elle restera a 4 -- et meme quand
--   les derives des 3 masquees seront fabriques, le VERROU de la marche 1 les
--   tiendra dehors. C'est la preuve que les deux marches travaillent ensemble.


-- ============================================================================
-- 4. RETOUR ARRIERE -- si l'essai tourne mal
-- ============================================================================
-- ⚠ Il ne SUPPRIME pas les lignes (regle delete-never : leur identifiant porte
--   le chemin du fichier sur le serveur). Il les remet « absentes », l'etat
--   qu'elles avaient avant d'exister chez nous -- donc invisibles pour l'app.
--
--   update app_console_photo
--      set present_in_hektor = false, absent_depuis = now()
--    where app_dossier_id = 1388194 and visible is false;
--
-- Et pour annuler un travail resté en attente :
--   update app_console_job set status = 'cancelled'
--    where hektor_annonce_id = '62189' and job_type = 'sync_hektor_photos'
--      and status = 'pending';
