-- ============================================================================
-- CHANTIER ⑦-8 MARCHE 4 -- MASQUER / AFFICHER UNE PHOTO DEPUIS L'APP
-- 19/10/2026                                            piece 1 sur 4 : LA BASE
-- ============================================================================
-- LA COMMANDE DE HEKTOR EST PROUVEE PAR SON PROPRE CODE, capture en juin et lu
-- le 19/10 (Console/exports/extract_contact_search_2026-06-12.../js/labs_Header.js,
-- l. 6816) :
--
--     function visibiliteVignette(id, visible) {
--         var data_url = 'mode=vignette_visibilite&id=' + id
--                        + '&idann=' + $j('#idannonceVignette').val()
--                        + '&visible=' + visible;
--         $j.ajax({ type: "GET", url: "xmlrpc.php", data: data_url,
--                   success: function () { vignettes(); vignettes_hidden(); } });
--     }
--
-- ⭐ TROIS CHOSES QUE CE CODE NOUS DIT, ET QU'ON NE DEVINAIT PAS :
--   1. UNE PHOTO A LA FOIS -- chirurgical. ⛔ L'autre route connue
--      (`mode=ordonne_photos&div=liste_photos|liste_photos_hidden`) REECRIT LES
--      DEUX LISTES ENTIERES : on ne la prend pas pour un simple drapeau.
--   2. AUCUNE CASCADE SERVEUR : le rappel ne fait que RAFRAICHIR les deux
--      galeries a l'ecran. Meme forme que l'interrupteur d'archivage des
--      contacts (⑦-1), ou la mesure disait deja « aucune cascade cote navigateur ».
--   3. ⭐⭐ ET IL NOUS DIT COMMENT FINIR : apres le changement, Hektor RELIT SES
--      DEUX GALERIES. Le worker fera pareil -- il RELIRA l'etat au lieu de le
--      deviner (piece 2).
--
-- ⚠ LE SENS DE LA VIE DU GESTE, pose par Frederic le 19/10 :
--      « il faut d'abord ecrire chez nous, ensuite envoyer l'information a
--        Hektor, et sinon il y a le run quotidien pour l'autre sens »
--   C'est la doctrine du chantier ③ (« chez nous d'abord »), et l'AUTRE SENS est
--   deja ecrit : c'est le balayage de la marche 2. Si un negociateur masque une
--   photo DIRECTEMENT dans Hektor, le lot de la nuit le voit et notre registre
--   se corrige tout seul.
--
-- ⭐⭐ ET « CHEZ NOUS » A DEUX ETAGES -- c'est le point de conception de ce patch :
--      la TABLE app_console_photo    -> le PANNEAU PHOTOS       immediat
--      la BOITE images_preview_json_app -> vitrine, espace client, portail
--   Si on n'ecrit que la table, « chez nous » n'est ecrit QU'A MOITIE et la photo
--   masquee reste visible au vendeur et a l'acquereur jusqu'au lendemain.
--
--   ⛔ CE QU'ON NE FAIT PAS : recopier ici le calcul de la boite. Il vit dans
--      `app_photos_remplir_adresses_app` et « deux copies divergeraient au
--      premier ajustement » -- c'est une regle du projet, payee plusieurs fois.
--   ✅ CE QU'ON FAIT : la RPC remet `adresses_app_le` A BLANC sur l'index de
--      l'annonce. Elle redevient alors une CIBLE du fabricant (sa condition est
--      `photo_url_listing_app is null OR adresses_app_le is null OR ...`), et le
--      worker REVEILLE le fabricant juste apres son appel Hektor (piece 2).
--      ➡ UNE SEULE COPIE DE LA REGLE, et la boite est juste en quelques
--        SECONDES au lieu d'une nuit.
--   ⚠ LA VITRINE ANDROID, elle, est un EXPORT STATIQUE pousse sur GitHub par le
--      run (run_full_pipeline.ps1:1726) : RIEN ne la changera avant le prochain
--      run. Dit, pas cache.
--
-- ============================================================================
-- CE QUE CE FICHIER FAIT -- le meme squelette que ⑦-3c (16/10), a 3 jours d'age
-- ============================================================================
--   ① la CONTRAINTE des types connait `set_hektor_photo_visibility`
--   ② les DROITS l'autorisent au negociateur sur SES biens
--   ③ la DISTRIBUTION le donne au service `documents`
--   ④ la RPC `app_console_photo_visibilite_optimistic` : elle ecrit CHEZ NOUS
--      et cree le travail, dans LA MEME TRANSACTION
--
-- ⚠⚠ UN NOUVEAU TYPE DE TRAVAIL = TROIS VERROUS, pas un. La lecon est du 14/10 :
--   `app_console_claim_next_job` a sa PROPRE liste par service, et un type absent
--   de celle-la reste « pending » A VIE sans que personne le voie.
--
-- EMPREINTES MESUREES LE 19/10 (sans retours chariot) :
--   contrainte   2c77f7047159f3b68a19af7ef8fe2242  (1 547 car.)
--   droits       11a28b2a588212ea2b88d859d6db583d  (1 657 car.)
--   distribution db14e7714742c2eb57ab233aa58c0290  (4 912 car.)
-- Dans les trois, `reorder_hektor_photos` apparait EXACTEMENT UNE FOIS : c'est
-- notre ancre, verifiee avant chaque ecriture. ANCRES MULTI-LIGNES : ZERO.
-- ⚠ Les empreintes ne BLOQUENT pas (un autre type a pu etre ajoute entre-temps) :
--   elles AVERTISSENT. C'est l'ancre unique qui est le vrai garde-fou.
--
-- RETOUR ARRIERE : patch_chantier7_8_marche4_visibilite_2026-10-19_INVERSE.sql
-- EPREUVE       : patch_chantier7_8_marche4_visibilite_2026-10-19_REPETITION.sql
-- ============================================================================

BEGIN;

SET LOCAL lock_timeout = '5s';

-- ① LA CONTRAINTE DES TYPES
DO $contrainte$
DECLARE
  v_def   text;
  v_ancre text := replace('''reorder_hektor_photos''::text])))', chr(13), '');
  v_neuf  text;
BEGIN
  SELECT pg_get_constraintdef(c.oid) INTO v_def
    FROM pg_constraint c
   WHERE c.conrelid = 'public.app_console_job'::regclass
     AND c.conname  = 'app_console_job_job_type_check';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : contrainte introuvable'; END IF;

  IF position('set_hektor_photo_visibility' in v_def) > 0 THEN
    RAISE NOTICE 'DEJA FAIT : la contrainte connait set_hektor_photo_visibility';
  ELSE
    IF md5(v_def) <> '2c77f7047159f3b68a19af7ef8fe2242' THEN
      RAISE NOTICE 'ATTENTION : empreinte de contrainte % (attendue 2c77f704...) -- un autre type a ete ajoute depuis. On continue : l''ancre unique est le vrai garde-fou.', md5(v_def);
    END IF;
    IF (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 THEN
      RAISE EXCEPTION 'STOP : l''ancre de la contrainte n''est pas unique';
    END IF;
    v_neuf := replace(v_def, v_ancre,
      replace('''reorder_hektor_photos''::text, ''set_hektor_photo_visibility''::text])))', chr(13), ''));
    EXECUTE 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
    EXECUTE 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check '
            || v_neuf || ' NOT VALID';
  END IF;
END $contrainte$;

-- ② LES DROITS : le negociateur sur SES biens, comme les trois autres gestes photo
DO $droits$
DECLARE
  v_def   text;
  v_ancre text := replace('''reorder_hektor_photos'',', chr(13), '');
BEGIN
  SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_can_request_job';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : app_console_can_request_job introuvable'; END IF;

  IF position('set_hektor_photo_visibility' in v_def) > 0 THEN
    RAISE NOTICE 'DEJA FAIT : les droits connaissent set_hektor_photo_visibility';
    RETURN;
  END IF;
  IF md5(v_def) <> '11a28b2a588212ea2b88d859d6db583d' THEN
    RAISE NOTICE 'ATTENTION : empreinte des droits % (attendue 11a28b2a...). On continue : l''ancre unique est le vrai garde-fou.', md5(v_def);
  END IF;
  IF (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 THEN
    RAISE EXCEPTION 'STOP : l''ancre des droits n''est pas unique';
  END IF;
  EXECUTE replace(v_def, v_ancre,
    replace('''reorder_hektor_photos'',''set_hektor_photo_visibility'',', chr(13), ''));
END $droits$;

-- ③ LA DISTRIBUTION : branche `documents`, collee a ses trois soeurs
DO $distribution$
DECLARE
  v_def   text;
  v_ancre text := replace('''reorder_hektor_photos''', chr(13), '');
BEGIN
  SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_claim_next_job';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : app_console_claim_next_job introuvable'; END IF;

  IF position('set_hektor_photo_visibility' in v_def) > 0 THEN
    RAISE NOTICE 'DEJA FAIT : la distribution connait set_hektor_photo_visibility';
    RETURN;
  END IF;
  IF md5(v_def) <> 'db14e7714742c2eb57ab233aa58c0290' THEN
    RAISE NOTICE 'ATTENTION : empreinte de la distribution % (attendue db14e771...). On continue : l''ancre unique est le vrai garde-fou.', md5(v_def);
  END IF;
  IF (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 THEN
    RAISE EXCEPTION 'STOP : l''ancre de la distribution n''est pas unique';
  END IF;
  EXECUTE replace(v_def, v_ancre,
    replace('''reorder_hektor_photos'',''set_hektor_photo_visibility''', chr(13), ''));
END $distribution$;

-- ④ LA RPC : on ecrit CHEZ NOUS et on cree le travail, en une transaction
CREATE OR REPLACE FUNCTION public.app_console_photo_visibilite_optimistic(
  p_app_dossier_id      bigint,
  p_hektor_annonce_id   text,
  p_hektor_photo_id     text,
  p_visible             boolean
) RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $fn$
DECLARE
  v_annonce text := nullif(btrim(coalesce(p_hektor_annonce_id, '')), '');
  v_photo   text := nullif(btrim(coalesce(p_hektor_photo_id, '')), '');
  v_avant   jsonb;
  v_etat    boolean;
  v_job_id  uuid;
  v_restant integer;
  v_boites  integer := 0;
BEGIN
  -- ⓵ DES PARAMETRES LISIBLES
  IF v_annonce IS NULL OR v_photo IS NULL OR p_app_dossier_id IS NULL OR p_visible IS NULL THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'parametres_incomplets');
  END IF;

  -- ⓶ LES DROITS. La meme garde que deposer, supprimer et mettre en couverture :
  --    le negociateur sur SES biens. On ne fabrique pas une seconde regle.
  IF NOT coalesce(public.app_console_can_access_dossier(p_app_dossier_id, v_annonce), false) THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'droits_insuffisants');
  END IF;

  -- ⓷ L'ETAT D'AVANT DE TOUTE L'ANNONCE, garde dans la charge : c'est le retour
  --    arriere, et il porte le drapeau de CHAQUE photo (pas seulement la cible).
  SELECT jsonb_agg(jsonb_build_object('hektor_photo_id', hektor_photo_id,
                                      'sort_order', sort_order,
                                      'visible', visible)
                   ORDER BY visible DESC, sort_order ASC, id ASC)
    INTO v_avant
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id
     AND present_in_hektor IS TRUE;

  -- ⓸ LA CIBLE DOIT EXISTER ET ETRE CHEZ HEKTOR.
  --    ⚠ ET AVOIR UN NUMERO HEKTOR : une photo deposee par l'app et pas encore
  --      envoyee n'en a pas -- Hektor ne saurait pas de quoi on parle. Meme refus
  --      que pour supprimer et pour la couverture.
  --    ⭐ MAIS ON N'EXIGE PAS QU'ELLE SOIT VISIBLE : ce geste va dans les DEUX
  --      sens, c'est tout son objet.
  SELECT visible INTO v_etat
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id
     AND hektor_photo_id = v_photo
     AND present_in_hektor IS TRUE;
  IF v_etat IS NULL THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'photo_introuvable_chez_hektor');
  END IF;

  -- ⓹ DEJA DANS L'ETAT DEMANDE ? Alors on ne derange pas Hektor.
  IF v_etat = p_visible THEN
    RETURN jsonb_build_object('ok', true, 'deja_dans_cet_etat', true,
                              'visible', p_visible);
  END IF;

  -- ⓺ ⭐⭐ CHEZ NOUS D'ABORD -- la regle de Frederic du 19/10.
  UPDATE public.app_console_photo
     SET visible = p_visible, updated_at = now()
   WHERE app_dossier_id = p_app_dossier_id
     AND hektor_photo_id = v_photo
     AND present_in_hektor IS TRUE;

  -- ⓼ ⭐⭐ ET LA BOITE PUBLIQUE, SANS RECOPIER SA REGLE.
  --    On remet `adresses_app_le` A BLANC sur les quatre index : l'annonce
  --    redevient une CIBLE de `app_photos_remplir_adresses_app`, que le worker
  --    reveillera juste apres son appel Hektor (piece 2).
  --    ⛔ On ne recalcule PAS la boite ici : sa regle (dont le verrou
  --      « visible is not false » pose le 19/10 au matin) vit dans le fabricant,
  --      et deux copies divergeraient au premier ajustement.
  --    ⭐ LE POST-IT N'EST PAS UNE INVENTION : `adresses_app_le IS NULL` est
  --      EXACTEMENT la premiere condition de ciblage du fabricant. On n'apprend
  --      rien de neuf a personne, on utilise son propre mecanisme.
  --    ⚠ LES QUATRE INDEX, PAS SEULEMENT LES VIVANTS : une photo peut etre sur
  --      une annonce ARCHIVEE (14 des 15 annonces a masquees le sont). L'archive
  --      n'a pas de galerie publique, mais elle a une COUVERTURE, et le fabricant
  --      la recalcule depuis le meme ciblage. En oublier un, c'est une vignette
  --      d'archive qui garderait une photo masquee.
  UPDATE public.app_dossier_current SET adresses_app_le = NULL
   WHERE app_dossier_id = p_app_dossier_id AND adresses_app_le IS NOT NULL;
  GET DIAGNOSTICS v_boites = ROW_COUNT;

  UPDATE public.app_archive_annonce_index_current SET adresses_app_le = NULL
   WHERE app_archive_id = p_app_dossier_id AND adresses_app_le IS NOT NULL;
  GET DIAGNOSTICS v_restant = ROW_COUNT;  -- reutilise, puis reecrase juste apres
  v_boites := v_boites + v_restant;

  UPDATE public.app_historical_annonce_index_current SET adresses_app_le = NULL
   WHERE app_historical_id = p_app_dossier_id AND adresses_app_le IS NOT NULL;
  GET DIAGNOSTICS v_restant = ROW_COUNT;
  v_boites := v_boites + v_restant;

  UPDATE public.app_brouillon_annonce_index_current SET adresses_app_le = NULL
   WHERE app_brouillon_id = p_app_dossier_id AND adresses_app_le IS NOT NULL;
  GET DIAGNOSTICS v_restant = ROW_COUNT;
  v_boites := v_boites + v_restant;

  -- ⓼ COMBIEN DE VISIBLES RESTE-T-IL ? On compte APRES l'ecriture du drapeau,
  --    donc la cible est deja dans son nouvel etat : le compte est vrai dans les
  --    DEUX sens, sans cas particulier.
  --    ⚠ `v_restant` vient d'etre ecrase par les GET DIAGNOSTICS ci-dessus -- on
  --      le recalcule donc ici. C'est exactement le genre de reutilisation de
  --      variable qui fait dire une betise a un compte rendu.
  --    ⭐ A QUOI CA SERT : masquer la DERNIERE visible laisse l'annonce sans
  --      couverture ni galerie -- elle affichera « Sans photo ». C'est juste (le
  --      negociateur a tout masque), mais ca ne doit pas etre une SURPRISE :
  --      l'ecran peut demander confirmation avant d'appeler.
  SELECT count(*) INTO v_restant
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id
     AND present_in_hektor IS TRUE
     AND visible IS TRUE;

  -- ⓾ LE TRAVAIL, DANS LA MEME TRANSACTION. Si l'insertion echoue, le drapeau
  --    revient avec elle : on ne reste jamais avec un etat change chez nous et
  --    rien de parti chez Hektor.
  INSERT INTO public.app_console_job
    (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
  VALUES
    ('set_hektor_photo_visibility', p_app_dossier_id, v_annonce,
     jsonb_build_object(
       'hektor_photo_id', v_photo,
       'visible', p_visible,
       'etat_avant', v_etat,
       'base_snapshot', coalesce(v_avant, '[]'::jsonb)),
     20, auth.uid())
  RETURNING id INTO v_job_id;

  RETURN jsonb_build_object(
    'ok', true,
    'deja_dans_cet_etat', false,
    'job_id', v_job_id,
    'visible', p_visible,
    'visibles_restantes', v_restant,
    -- ⭐ LE POST-IT EST-IL POSE ? Si ce compte est 0, le fabricant ne reciblera
    --   PAS l'annonce et la boite resterait vieille : c'est mesurable, donc on le
    --   rend plutot que de l'esperer. (0 est normal si la boite etait deja a
    --   refaire -- adresses_app_le etait DEJA nul.)
    'index_marques_a_refaire', v_boites,
    -- ⭐ LE SIGNAL POUR L'ECRAN : apres ce geste, l'annonce n'a plus AUCUNE
    --   photo publiable. A dire a l'humain, pas a decouvrir le lendemain.
    'plus_aucune_visible', (p_visible IS FALSE AND v_restant = 0));
END $fn$;

REVOKE ALL ON FUNCTION public.app_console_photo_visibilite_optimistic(bigint, text, text, boolean) FROM public;
GRANT EXECUTE ON FUNCTION public.app_console_photo_visibilite_optimistic(bigint, text, text, boolean)
  TO authenticated, service_role;

COMMENT ON FUNCTION public.app_console_photo_visibilite_optimistic(bigint, text, text, boolean) IS
  '(7)-8 marche 4 (19/10/2026) : masque ou affiche une photo. Ecrit le drapeau CHEZ NOUS '
  'et cree le travail set_hektor_photo_visibility dans la meme transaction, avec l''etat '
  'd''avant de toute l''annonce dans base_snapshot. Remet adresses_app_le a blanc pour que '
  'le fabricant de la boite publique recible l''annonce (le worker le reveille). Garde : '
  'app_console_can_access_dossier. Rend plus_aucune_visible quand le geste laisse '
  'l''annonce sans aucune photo publiable.';

COMMIT;
