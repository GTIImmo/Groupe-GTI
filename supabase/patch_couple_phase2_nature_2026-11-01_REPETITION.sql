-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PHASE 2 — RÉPÉTITION (rien ne reste)                      01/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Joue le patch EN ENTIER dans une transaction, écrit sur une fiche d'essai
-- fictive 29999998 exactement ce que le push enverra, relit par la vue de l'écran,
-- puis LÈVE « ESSAI ANNULE » : tout est annulé.
-- Attendu : toutes les cases à « ok » (ou au chiffre indiqué).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

alter table public.app_contact_current
  add column if not exists nature_fiche text,
  add column if not exists couple_deuxieme text,
  add column if not exists civilite_app text,
  add column if not exists civilite_source text,
  add column if not exists suit_principale_archivee boolean,
  add column if not exists supprimee_chez_hektor boolean;

insert into public.app_worker_registry
  (worker_key, worker_name, worker_role, worker_type, criticality, frequency,
   status, owner, script_path, expected_max_runtime_minutes, monitoring_domain,
   source_notes)
values
  ('phase2.nature_contacts',
   'Nature des fiches contact (couples, civilite rendue)',
   'Calcule chaque nuit la nature de chaque fiche (personne seule, couple, conjoint, cases vides), '
   'la civilite Mme. rendue d''apres l''ancien logiciel, les cases archivees de fait et les fiches '
   'supprimees chez Hektor. Table locale contact_nature_current ; le push l''envoie si APP_CONTACT_NATURE=1.',
   'python_worker', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'phase2\contacts\nature_des_fiches.py',
   5, 'business',
   'Ajoutee le 01/11/2026 (couples, phases 1-2). Ne lit et n''ecrit que la base locale ; aucune '
   'requete chez Hektor. Mesure : ~8 s.')
on conflict (worker_key) do nothing;

DO $essai$
DECLARE
  r  record;
  t  text := '';
BEGIN
  -- la forme exacte d'une ligne du push (les booleens arrivent en JSON true/false)
  insert into public.app_contact_current(hektor_contact_id, app_contact_id, nom, prenom, display_name,
      archive, typologies_json, source_hash, refreshed_at,
      nature_fiche, couple_deuxieme, civilite_app, civilite_source, suit_principale_archivee, supprimee_chez_hektor)
  select '29999998', 29999998, 'ESSAI NATURE', 'Repetition', 'Repetition ESSAI NATURE',
      false, '[]'::jsonb, 'essai_nature', now(),
      j->>'nature_fiche', j->>'couple_deuxieme', j->>'civilite_app', j->>'civilite_source',
      (j->>'suit_principale_archivee')::boolean, (j->>'supprimee_chez_hektor')::boolean
  from (select '{"nature_fiche":"couple","couple_deuxieme":"case_vide","civilite_app":"Mme.","civilite_source":"ancien_logiciel","suit_principale_archivee":false,"supprimee_chez_hektor":true}'::jsonb as j) s;
  select * into r from public.app_contact_current where hektor_contact_id = '29999998';
  t := t || ' | 01 colonnes=' || (select count(*) from information_schema.columns
        where table_schema='public' and table_name='app_contact_current'
          and column_name in ('nature_fiche','couple_deuxieme','civilite_app','civilite_source',
                              'suit_principale_archivee','supprimee_chez_hektor')) || ' (6)';
  t := t || ' | 02 battement=' || (select count(*) from public.app_worker_registry where worker_key='phase2.nature_contacts') || ' (1)';
  t := t || ' | 03 nature=' || case when r.nature_fiche = 'couple' and r.couple_deuxieme = 'case_vide' then 'ok' else 'FAUX' end;
  t := t || ' | 04 civilite=' || case when r.civilite_app = 'Mme.' and r.civilite_source = 'ancien_logiciel' and r.civilite is null then 'ok' else 'FAUX' end;
  t := t || ' | 05 booleens=' || case when r.suit_principale_archivee = false and r.supprimee_chez_hektor = true then 'ok' else 'FAUX' end;
  -- la vue de l'ecran se lit toujours (elle ne nomme pas les colonnes neuves)
  t := t || ' | 06 vue_ecran=' || case when (select count(*) from public.app_contacts_current where hektor_contact_id = '29999998') >= 0 then 'ok' else 'FAUX' end;
  t := t || ' | 07 autres_remplies=' || (select count(*) from public.app_contact_current
                                        where nature_fiche is not null and hektor_contact_id <> '29999998') || ' (0)';
  RAISE EXCEPTION 'ESSAI ANNULE --%', t;
END
$essai$;

ROLLBACK;
