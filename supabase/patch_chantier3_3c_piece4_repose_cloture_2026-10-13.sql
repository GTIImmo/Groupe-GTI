-- =====================================================================
-- CHANTIER ③ -- 3c PIECE 4 : LA RE-POSE DE LA CLOTURE APRES CHAQUE PUSH
-- Date : 2026-10-13 · Detail : notice/CHANTIER_3_HEKTOR_DABORD_2026-10-12.md
--
-- LE PROBLEME, MESURE. La ligne de registre qui AFFICHE notre date est detruite
-- puis refaite, par DEUX chemins :
--   le run de nuit   push_upgrade_to_supabase.py l. 1726-1737 : delete + insert
--   le worker        push_single_annonce_to_supabase.py l. 358-360 puis 630 :
--                    delete_target_remote efface TOUJOURS les lignes de registre
--                    de l'annonce, puis upsert -- donc ~1 min apres n'importe quel
--                    geste sur cette annonce
-- ➡ notre colonne `mandat_date_cloture_app` repart a NULL les deux fois.
--
-- ⭐ CE N'EST PAS UNE DECOUVERTE : le run le dit (l. ~1495) -- « les colonnes
--    soeurs SURVIVENT (merge-duplicates ne touche que les colonnes du payload) ».
--    VRAI pour la fiche et les index (upsert), FAUX pour le registre
--    (delete+insert). C'est exactement pourquoi
--    `app_photos_remplir_adresses_registre` existe : « le registre RECOPIE ce que
--    les index savent ». On recopie ce patron, pour la cloture.
--
-- CE QUE FAIT CETTE FONCTION : **LE REGISTRE REFLETE LE CARNET.**
--   elle POSE   `mandat_date_cloture_app` la ou le carnet dit quelque chose
--               (champ='mandat_date_cloture', origine='cloture_app', valeur non vide) ;
--   elle EFFACE la ou le carnet ne dit plus rien -- sinon une cloture ANNULEE
--               resterait affichee pour toujours.
--   Sans portee = tout le parc. Avec portee = une seule annonce (le chemin immediat).
--
-- ⚠ LE GARDE-FOU EST EN BASE, COMME POUR LES PHOTOS : elle REFUSE d'agir si le
--   registre est sous son plancher (10 000 ; il en porte 24 505). Sans lui, un push
--   casse VIDERAIT nos clotures en silence. Le refus sort en `statut: 'refus'`, que
--   l'appelant transforme en code 1 -> heartbeat en erreur -> le moniteur le dit.
-- ⭐ LE PLANCHER EST UN PARAMETRE pour que la repetition puisse PROUVER le refus
--   sans rien supprimer (on l'appelle avec 1 000 000). Les appelants ne le passent pas.
--
-- ⚠ ELLE N'ECRIT QU'UNE SEULE COLONNE. Ni les photos, ni `mandat_date_cloture`
--   (celle de Hektor), ni rien d'autre.
--
-- DROITS : `service_role` seulement -- le run et le worker l'appellent avec la cle de
-- service. Le front n'a aucune raison de l'appeler.
--
-- RETOUR ARRIERE : supabase/patch_chantier3_3c_piece4_repose_cloture_2026-10-13_INVERSE.sql
-- REPETITION     : supabase/patch_chantier3_3c_piece4_repose_cloture_2026-10-13_REPETITION.sql
-- ⚠ NE LE COLLER QU'UNE SEULE FOIS (le succes est un NOTICE, invisible dans l'editeur).
-- =====================================================================

BEGIN;

create or replace function public.app_reposer_cloture_mandat_app(
  target_annonce    text default null,
  plancher_registre int  default 10000
) returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $fn$
DECLARE
  v_annonce  text   := nullif(btrim(coalesce(target_annonce, '')), '');
  v_plancher int    := greatest(coalesce(plancher_registre, 10000), 0);
  v_lignes   bigint;
  v_carnet   bigint;
  v_posees   bigint := 0;
  v_effacees bigint := 0;
BEGIN
  -- ① LE GARDE-FOU. Un registre anormalement petit = un push casse : on ne touche
  --    a rien. Mieux vaut une date qui attend une nuit qu'un parc vide.
  SELECT count(*) INTO v_lignes FROM public.app_mandat_register_current;
  IF v_lignes < v_plancher THEN
    RETURN jsonb_build_object(
      'statut', 'refus',
      'raison', format('le registre ne porte que %s lignes, sous le plancher de %s',
                       v_lignes, v_plancher),
      'lignes_registre', v_lignes);
  END IF;

  SELECT count(*) INTO v_carnet
    FROM public.app_mandat_champ_app
   WHERE champ = 'mandat_date_cloture'
     AND origine = 'cloture_app'
     AND nullif(btrim(coalesce(valeur_app, '')), '') IS NOT NULL;

  -- ② ON POSE CE QUE LE CARNET DIT.
  --    ⚠ `coalesce(...) <> ...` evite de reecrire une ligne deja juste : une nuit
  --      ordinaire ne touchera donc AUCUNE ligne, et le compte rendu le dira.
  WITH poses AS (
    UPDATE public.app_mandat_register_current r
       SET mandat_date_cloture_app = nullif(btrim(k.valeur_app), '')
      FROM public.app_mandat_champ_app k
     WHERE k.champ   = 'mandat_date_cloture'
       AND k.origine = 'cloture_app'
       AND nullif(btrim(coalesce(k.valeur_app, '')), '') IS NOT NULL
       AND r.hektor_annonce_id::text = k.hektor_annonce_id
       AND r.numero_mandat::text     = k.numero_mandat
       AND (v_annonce IS NULL OR r.hektor_annonce_id::text = v_annonce)
       AND coalesce(r.mandat_date_cloture_app, '') <> nullif(btrim(k.valeur_app), '')
    RETURNING 1)
  SELECT count(*) INTO v_posees FROM poses;

  -- ③ ON EFFACE LA OU LE CARNET NE DIT PLUS RIEN.
  --    C'est la moitie qui rend le geste REVERSIBLE : sans elle, une cloture annulee
  --    resterait a l'ecran indefiniment, et l'app mentirait.
  WITH effacements AS (
    UPDATE public.app_mandat_register_current r
       SET mandat_date_cloture_app = NULL
     WHERE nullif(btrim(coalesce(r.mandat_date_cloture_app, '')), '') IS NOT NULL
       AND (v_annonce IS NULL OR r.hektor_annonce_id::text = v_annonce)
       AND NOT EXISTS (
         SELECT 1 FROM public.app_mandat_champ_app k
          WHERE k.champ   = 'mandat_date_cloture'
            AND k.origine = 'cloture_app'
            AND nullif(btrim(coalesce(k.valeur_app, '')), '') IS NOT NULL
            AND k.hektor_annonce_id = r.hektor_annonce_id::text
            AND k.numero_mandat     = r.numero_mandat::text)
    RETURNING 1)
  SELECT count(*) INTO v_effacees FROM effacements;

  RETURN jsonb_build_object(
    'statut', 'ok',
    'portee', coalesce(v_annonce, 'tout le parc'),
    'carnet', v_carnet,
    'posees', v_posees,
    'effacees', v_effacees,
    'lignes_registre', v_lignes);
END $fn$;

revoke all on function public.app_reposer_cloture_mandat_app(text, int) from public;
grant execute on function public.app_reposer_cloture_mandat_app(text, int) to service_role;

comment on function public.app_reposer_cloture_mandat_app(text, int) is
  'Chantier 3c piece 4, 13/10/2026. LE REGISTRE REFLETE LE CARNET : repose '
  'mandat_date_cloture_app depuis app_mandat_champ_app (origine=cloture_app) et '
  'l''efface la ou le carnet ne dit plus rien. Appelee APRES chaque reconstruction du '
  'registre -- par le run (tout le parc) et par push_single_annonce (une annonce). '
  'REFUSE si le registre est sous son plancher (garde-fou copie des photos). '
  'N''ecrit qu''une colonne, ne touche jamais mandat_date_cloture (a Hektor).';

-- ---------------------------------------------------------------------
-- L'ENREGISTREMENT DU BATTEMENT DE COEUR -- ET SANS LUI MON GARDE-FOU SERAIT
-- DECORATIF.
--
-- ⚠ MESURE DU 13/10, ET ELLE M'A RATTRAPE. J'allais ecrire « un refus sort en 1 ->
--   heartbeat en erreur -> le moniteur le dit ». C'EST FAUX PAR DEFAUT :
--     - monitoring/heartbeat.py ecrit en **PATCH FILTRE** sur app_worker_registry
--       (l. 105-120). Si la cle n'y a pas de ligne, il touche **0 ligne**, recoit
--       **204**, et le code `200 <= status < 300` compte **un succes** ;
--     - check_gti_health.check_worker_heartbeat (l. 1276) **enumere la table** :
--       une cle sans ligne n'est jamais regardee.
--   ➡ UNE CLE NON ENREGISTREE = UN BATTEMENT QUI PART DANS LE VIDE, EN SILENCE.
--
-- ⚠⚠ ET CE N'EST PAS QUE MOI : **9 des 40 cles du run n'ont aucune ligne** --
--   phase1.archived_details · phase2.adresses_photos · phase2.correspondance_annonces
--   · phase2.correspondance_identite · phase2.derives_photos · phase2.doublure_mandat
--   · phase2.doublure_relation · phase2.rattrapage_photos · phase2.sonde_photos.
--   Le commentaire du run promet pourtant le contraire pour les photos, depuis le
--   27/09. C'est un sujet du chantier ④ (echecs silencieux), PAS celui-ci : signale
--   a Frederic, non corrige ici.
--
-- Le modele copie est `phase2.reappliquer_saisies` -- meme esprit, mot pour mot :
-- « repose, apres le push, les champs saisis dans l'app que Hektor n'a pas encore
-- confirmes » -- donc meme criticite (medium) et meme frequence.
-- ---------------------------------------------------------------------
insert into public.app_worker_registry
  (worker_key, worker_name, worker_role, worker_type, criticality, frequency,
   status, owner, script_path, expected_max_runtime_minutes, monitoring_domain,
   source_notes)
values
  ('phase2.repose_cloture_mandat',
   'Re-pose de la cloture de mandat',
   'Repose, APRES le push, notre date de cloture de mandat sur la ligne du registre '
   'que le push vient de detruire et de refaire. Le registre REFLETE le carnet '
   'app_mandat_champ_app, qui fait foi. Chantier 3c, piece 4.',
   'node_worker', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'Console/reposer_cloture_mandat.js',
   5, 'business',
   'Ajoute le 13/10/2026 avec la piece 4 du chantier 3c. Non bloquante : un echec '
   'fait attendre la date une nuit, il ne la perd jamais (le carnet la porte).')
on conflict (worker_key) do nothing;

notify pgrst, 'reload schema';

COMMIT;
