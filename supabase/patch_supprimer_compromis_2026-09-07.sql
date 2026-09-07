-- ═══════════════════════════════════════════════════════════════════════════════
-- 3.4 — SUPPRIMER UN COMPROMIS : le verbe qui manquait          07/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Copie versionnee de ce qui est deploye (migration
-- `geste_affaire_supprimer_compromis`).
--
-- ─── DEUX VERBES QU'ON A LONGTEMPS CONFONDUS ───
--     annuler     le compromis RESTE, marque mort (statut 2 chez Hektor). Le
--                 statut de l'annonce NE BOUGE PAS. La trace est gardee.
--     supprimer   le compromis DISPARAIT. Le statut de l'annonce redescend.
-- Jusqu'ici seul « annuler » existait pour le compromis, et « supprimer »
-- n'existait que pour la vente. Le geste destructeur manquait a l'un des deux.
--
-- ─── CE QUI CHANGE, ET RIEN D'AUTRE ───
--   ① `supprimer` devient legal pour kind='compromis' et produit le travail
--      `delete_hektor_compromis` (il levait 'geste_incompatible' avant).
--   ② la charge porte `hektor_compromis_id` et `confirmer` = true.
--      ⚠ `confirmer` EST EXIGE cote worker : aucun appel ne part sans lui, meme
--        si le travail a ete cree par erreur. Meme garde-fou que la vente.
--
-- ─── CE QUI NE CHANGE PAS, ET C'EST VOULU ───
--   · la redescente de statut (bloc 1bis) valait deja pour `supprimer` sans
--     distinguer le genre. Elle calcule sa cible avec
--     app_statut_redescente_calcule() : une offre vivante rend « Sous offre »,
--     pas « Actif ». Le worker LIT cette cible, il ne la devine pas.
--   · `present_in_hektor = false` au lieu d'un DELETE : le delete-never tient.
--     Ce que le registre a vu, il le garde.
--   · bornes 2 et 3 : on ne bouge le statut que vers le BAS, et on ne touche NI
--     `diffusable` NI `archive`.
--
-- ⚠ LA ROUTE HEKTOR A ETE RELEVEE EN CONDITIONS REELLES le 07/09, en
--   instrumentant leur fiche pendant une suppression. DEUX appels partent :
--       GET  mode=annonce-SuiviVente-deleteCompromis&idCompromis=<id>&idAnn=<ann>
--       POST mode=ajoutebien_wizardBien   (le statut — un SECOND geste)
--   Ce n'est PAS le verbe de la vente : `ventes-deleteVente` sur un compromis
--   rend 200 avec un corps VIDE et ne fait RIEN. Le detail des trois pieges est
--   dans handleDeleteHektorCompromis (Console/console_job_worker.js).
--
-- RETOUR ARRIERE : retirer les deux branches marquees « 3.4 » ci-dessous et
-- reappliquer. Aucune donnee n'est migree ici, seule la fonction change.
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.app_geste_affaire_optimistic(
  target_affaire_id bigint, geste text, job_priority integer DEFAULT 7)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  a             app_affaire_ledger%rowtype;
  d             app_dossier_current%rowtype;
  etat_avant    text;
  etat_apres    text;
  type_job      text;
  charge        jsonb;
  nouveau_id    uuid;
  statut_avant  text;
  statut_apres  text;
BEGIN
  SELECT * INTO a FROM app_affaire_ledger WHERE app_affaire_id = target_affaire_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'affaire_not_found' USING errcode = '22023'; END IF;

  IF NOT public.is_app_admin() THEN
    RAISE EXCEPTION 'not_allowed' USING errcode = '42501';
  END IF;
  IF NOT public.app_console_can_access_dossier(a.app_dossier_id, a.hektor_annonce_id::text) THEN
    RAISE EXCEPTION 'dossier_not_allowed' USING errcode = '42501';
  END IF;

  -- Le geste doit correspondre au type de l'affaire : on ne refuse pas une vente,
  -- on ne supprime pas une offre. Le controle est ici, pas dans l'ecran.
  IF geste = 'refus' AND a.kind = 'offre' THEN
    type_job := 'change_hektor_offre_status'; etat_apres := 'refused';
  ELSIF geste = 'accepte' AND a.kind = 'offre' THEN
    type_job := 'change_hektor_offre_status'; etat_apres := 'accepted';
  ELSIF geste = 'annuler' AND a.kind = 'compromis' THEN
    type_job := 'cancel_hektor_compromis'; etat_apres := 'cancelled';
  -- ─── 3.4 (07/09/2026) : SUPPRIMER UN COMPROMIS ───
  -- Le verbe manquait. « Annuler » et « supprimer » ne sont PAS le meme geste --
  -- mesure du 04/09 : annuler laisse le compromis, marque mort, et le statut ne
  -- bouge pas ; supprimer le fait disparaitre, et le statut redescend.
  -- ⚠ LA ROUTE A ETE RELEVEE EN CONDITIONS REELLES le 07/09, en instrumentant la
  --   fiche de Hektor : mode=annonce-SuiviVente-deleteCompromis, parametres
  --   idCompromis ET idAnn. Ce N'EST PAS le verbe de la vente -- eprouve,
  --   ventes-deleteVente sur un compromis ne fait rien.
  ELSIF geste = 'supprimer' AND a.kind = 'compromis' THEN
    type_job := 'delete_hektor_compromis'; etat_apres := NULL;
  ELSIF geste = 'supprimer' AND a.kind = 'vente' THEN
    type_job := 'delete_hektor_vente'; etat_apres := NULL;
  ELSE
    RAISE EXCEPTION 'geste_incompatible: % sur %', geste, a.kind USING errcode = '22023';
  END IF;

  -- Une transaction DEJA dans cet etat : on ne renvoie pas de travail pour rien.
  IF etat_apres IS NOT NULL AND coalesce(a.state, '') = etat_apres THEN
    RETURN jsonb_build_object('ok', true, 'deja_dans_cet_etat', true,
                              'app_affaire_id', target_affaire_id, 'state', a.state);
  END IF;

  etat_avant := a.state;
  SELECT * INTO d FROM app_dossier_current WHERE app_dossier_id = a.app_dossier_id;

  -- 1. l'etat est pose CHEZ NOUS tout de suite -- c'est l'instantane
  IF geste = 'supprimer' THEN
    UPDATE app_affaire_ledger SET present_in_hektor = false
     WHERE app_affaire_id = target_affaire_id;
  ELSE
    UPDATE app_affaire_ledger SET state = etat_apres
     WHERE app_affaire_id = target_affaire_id;
  END IF;

  -- 1bis. LA REDESCENTE, sur le ledger qu'on vient d'ecrire.
  -- ⬇ 'refus' RETIRE le 02/09 (cycle 1), 'annuler' RETIRE le 02/09 (cycle 3.2).
  --   Il ne reste que 'supprimer'.
  -- ✅ ET ELLE EST MESUREE DEPUIS LE 07/09, pour le compromis : en supprimant
  --   depuis LEUR interface, un SECOND appel part aussitot --
  --   POST mode=ajoutebien_wizardBien avec statutAnnonce et idann. Hektor ne
  --   redescend donc PAS tout seul : c'est un geste, et le worker le fait
  --   (redescendreStatutHektor, appele apres la preuve de la suppression).
  IF geste = 'supprimer' AND d.app_dossier_id IS NOT NULL THEN
    statut_avant := d.statut_annonce;
    statut_apres := public.app_statut_redescente_calcule(a.app_dossier_id);

    -- BORNE 2 + hors echelle : on ne bouge que vers le BAS, et seulement depuis
    -- un barreau de l'echelle vers un autre barreau de l'echelle.
    IF public.app_statut_rang(statut_avant) IS NULL
       OR public.app_statut_rang(statut_apres) IS NULL
       OR public.app_statut_rang(statut_apres) >= public.app_statut_rang(statut_avant) THEN
      statut_apres := NULL;
    END IF;

    IF statut_apres IS NOT NULL THEN
      -- VISIBLE tout de suite. On ne touche NI diffusable NI archive (borne 3).
      UPDATE app_dossier_current
         SET statut_annonce = statut_apres
       WHERE app_dossier_id = a.app_dossier_id;

      -- SURVIT a la coupure. Dormant tant que la liste des champs app est vide.
      INSERT INTO app_annonce_champ_app (app_dossier_id, champ, valeur_app, origine, ecrit_le, ecrit_par)
      VALUES (a.app_dossier_id, 'statut', statut_apres, 'redescente_transaction', now(), coalesce(auth.uid()::text, 'app'))
      ON CONFLICT (app_dossier_id, champ) DO UPDATE
        SET valeur_app = excluded.valeur_app,
            origine    = excluded.origine,
            ecrit_le   = excluded.ecrit_le,
            ecrit_par  = excluded.ecrit_par;
    ELSE
      statut_avant := NULL;   -- rien n'a bouge : rien a restaurer
    END IF;
  END IF;

  -- 2. le travail EMPORTE l'etat precedent, pour que le worker sache quoi restaurer
  charge := jsonb_build_object(
    'hektor_annonce_id', a.hektor_annonce_id,
    'numero_dossier',    d.numero_dossier,
    'titre_bien',        d.titre_bien,
    'app_affaire_id',    target_affaire_id,
    'etat_avant',        etat_avant,
    'geste',             geste
  );
  IF statut_avant IS NOT NULL THEN
    charge := charge || jsonb_build_object('statut_avant', statut_avant,
                                           'statut_apres', statut_apres);
  END IF;
  IF type_job = 'change_hektor_offre_status' THEN
    charge := charge || jsonb_build_object('hektor_offre_id', a.hektor_affaire_id::text,
                                           'type', geste);
  ELSIF type_job = 'cancel_hektor_compromis' THEN
    charge := charge || jsonb_build_object('hektor_compromis_id', a.hektor_affaire_id::text);
  ELSIF type_job = 'delete_hektor_compromis' THEN
    -- ⚠ `confirmer` EST EXIGE, comme pour la vente : le geste est IRREVERSIBLE.
    charge := charge || jsonb_build_object('hektor_compromis_id', a.hektor_affaire_id::text,
                                           'confirmer', true);
  ELSE
    charge := charge || jsonb_build_object('hektor_vente_id', a.hektor_affaire_id::text,
                                           'confirmer', true);
  END IF;

  INSERT INTO app_console_job (job_type, app_dossier_id, hektor_annonce_id, payload_json,
                               priority, status, requested_by)
  VALUES (type_job, a.app_dossier_id, a.hektor_annonce_id::text, charge,
          coalesce(job_priority, 7), 'pending', auth.uid())
  RETURNING id INTO nouveau_id;

  RETURN jsonb_build_object(
    'ok', true,
    'job_id', nouveau_id,
    'app_affaire_id', target_affaire_id,
    'kind', a.kind,
    'etat_avant', etat_avant,
    'etat_apres', etat_apres,
    'statut_avant', statut_avant,
    'statut_apres', statut_apres,
    'job_type', type_job
  );
END
$function$;


-- ═══════════════════════════════════════════════════════════════════════════════
-- LES DEUX PORTES QU'IL FALLAIT OUVRIR AUSSI, ET ELLES SE SERAIENT TUES
-- ═══════════════════════════════════════════════════════════════════════════════
-- Un nouveau `job_type` ne suffit pas : il traverse TROIS controles, et deux
-- d'entre eux echouent EN SILENCE ou APRES coup. Trouves en relisant, pas en
-- testant -- l'essai les aurait payes cher.
--
--   ① le CHECK de app_console_job     -> exception AU INSERT, donc APRES que la
--                                        RPC a deja pose present_in_hektor=false
--                                        et redescendu le statut. L'app aurait
--                                        montre un compromis supprime que rien
--                                        n'aurait envoye.
--   ② la liste du worker `admin`      -> AUCUNE erreur : le travail reste
--                                        `pending` pour toujours. Le code du
--                                        worker l'annonce depuis le 29/08 :
--                                        « Oublier cette liste = un travail qui
--                                        reste en attente indefiniment, SANS
--                                        erreur : aucun service ne le reclame. »
--   ③ le switch de console_job_worker.js -> celui-la, au moins, leve.

-- ─── ① migration `console_job_type_delete_hektor_compromis` ───
ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check;
ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check
  CHECK (job_type = ANY (ARRAY[
    'sync_console_documents','prepare_document_cloud','generate_estimation_pdf',
    'generate_mandat_document','generate_cadastre_document','relance_signature',
    'cancel_signature_procedure','upload_document_to_hektor','delete_document_from_hektor',
    'sync_hektor_photos','upload_hektor_photo','prepare_archived_annonce_detail',
    'prepare_historical_annonce_detail','link_hektor_mandant','create_hektor_contact',
    'update_hektor_contact','add_hektor_contact_search','update_hektor_contact_search',
    'delete_hektor_contact_search','delete_hektor_contact','create_hektor_mandant_contact',
    'update_hektor_mandant_contact','update_hektor_annonce_fields',
    'create_hektor_mandat_auto_number','delete_hektor_annonce','archive_hektor_annonce',
    'restore_hektor_annonce','change_hektor_annonce_status','assign_hektor_annonce_negotiator',
    'create_hektor_draft_annonce','matterport_online','matterport_offline',
    'matterport_archive','matterport_reactivate','refresh_console_data',
    'refresh_console_contact_data','archive_cloud_documents','change_hektor_offre_status',
    'cancel_hektor_compromis','delete_hektor_compromis','delete_hektor_vente'
  ]));

-- ─── ② migration `claim_next_job_delete_hektor_compromis` ───
-- Seule la liste du kind 'admin' change dans app_console_claim_next_job ; le
-- reste de la fonction est recopie tel quel. La definition complete se relit
-- par :  SELECT pg_get_functiondef(oid) FROM pg_proc
--         WHERE proname = 'app_console_claim_next_job';
--
--     or (worker_kind = 'admin' and j.job_type in (
--            'delete_hektor_annonce','delete_hektor_contact','archive_hektor_annonce',
--            'restore_hektor_annonce','change_hektor_annonce_status',
--            'assign_hektor_annonce_negotiator',
--            'change_hektor_offre_status','cancel_hektor_compromis',
--            'delete_hektor_compromis','delete_hektor_vente'))
--
-- ⚠ SESSION ADMIN OBLIGATOIRE, et c'est pour cela qu'il va sur ce worker-la :
--   mesure du 29/08, le compte negociateur est refuse sur le compromis
--   (« Vous n'avez pas les droits pour creer un compromis lie a cette annonce »).
