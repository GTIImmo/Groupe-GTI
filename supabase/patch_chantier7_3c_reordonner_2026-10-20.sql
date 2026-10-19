-- ════════════════════════════════════════════════════════════════════════════════
--  ⑦-3c · RÉORDONNER LES PHOTOS — LA RECETTE GÉNÉRIQUE
--                                                                 20/10/2026
--  Go de Frédéric : « A » (les deux flèches), puis « Oui ».
-- ════════════════════════════════════════════════════════════════════════════════
--
--  CE QUE CE PATCH AJOUTE, ET CE QU'IL NE TOUCHE PAS.
--    ✅ AJOUTE  : une fonction NEUVE, `app_console_photos_reordonner_optimistic`.
--    ⛔ NE TOUCHE PAS : `app_console_photo_couverture_optimistic` (en production
--       depuis le 16/10), ni le worker, ni le type de travail, ni ses trois verrous.
--       Le retour arriere est donc un simple DROP -- rien a restaurer.
--
--  POURQUOI C'EST SI PETIT. Mesure du 19/10 :
--    · la commande de Hektor (`mode=ordonne_photos`) est en production depuis le
--      14/10, et son handler `handleReorderHektorPhotos` ACCEPTE UN ORDRE
--      QUELCONQUE -- la couverture n'etait qu'un cas particulier ;
--    · le type `reorder_hektor_photos` existe, ses TROIS verrous sont ouverts
--      (contrainte, droits, distribution), et il a tourne 4 fois, 0 erreur ;
--    · ⭐⭐ ET L'ESSAI DU 19/10 A 23:26 A PROUVE QUE HEKTOR ACCEPTE UNE PERMUTATION :
--      sur le bac a sable 62774, envoye `482254, 487604, 487603` (echange des rangs
--      2 et 3 -- ni une renumerotation, ni une mise en couverture), et la relecture
--      de SES galeries a rendu exactement cet ordre.
--    · et le projet l'avait deja ecrit (api.ts:8456) : « reordonner et choisir la
--      couverture sont le meme ordre -- d'ou le type reorder_hektor_photos, qui
--      servira tel quel le jour ou on ajoutera le glisser-deposer ».
--
--  SEPT DES HUIT ETAPES SONT COPIEES de la recette de couverture (empreinte
--  cbe7d537) : les droits, l'etat d'avant, la cible, le « deja fait », les deux
--  listes, le travail dans la meme transaction. UNE SEULE change : la
--  renumerotation prend l'ordre DONNE par l'ecran au lieu de « mets celle-la en 1er ».
--
--  ⭐ ET ON AJOUTE DEUX CHOSES QUE LA COUVERTURE N'A PAS :
--    ① LE GARDE-FOU DE LA LISTE EXACTE (nouveau, et il repond a un trou de l'audit).
--       ⛔ NON MESURE : on ne sait pas ce que Hektor fait d'un ordre PARTIEL (moins
--         d'ids qu'il n'a de photos). Le garde-fou du worker ne refuse que la liste
--         VIDE. On refuse donc TOUT ecart : la liste doit etre EXACTEMENT l'ensemble
--         des visibles presentes chez Hektor -- ni un doublon, ni un inconnu, ni un
--         manquant. On ne decouvre pas un comportement inconnu en production.
--    ② LE POST-IT SUR LES QUATRE INDEX, recopie A L'IDENTIQUE de la recette du
--       masquage (empreinte 0a5f62d1). ⚠ La couverture ne le pose PAS : mesure du
--       19/10, la boite publique de 63261 datait du 11/10 et celle de 63046 du
--       27/09, alors que leur couverture avait change le 16/10. La vitrine suivait
--       donc avec un jour de retard. Ici elle suivra.
--
--  ⚠ CE QUE CE PATCH NE REGLE PAS, et qui reste a decider :
--    · le REVEIL IMMEDIAT du fabricant (le handler du masquage l'appelle, celui du
--      reordonnancement non). Sans lui, la boite se refait au prochain passage du
--      fabricant au lieu de quelques secondes. C'est une modification du worker,
--      donc un REDEMARRAGE des 4 services : l'accord de Frederic.
--    · l'ecran : les deux fleches, et la limite de 12 photos (23 % des annonces en
--      ont plus, jusqu'a 166).
--
--  EMPREINTES AVANT LE PATCH (a verifier, elles ne doivent PAS changer) :
--    app_console_photo_couverture_optimistic  cbe7d5372e79040a4eb6b7cc644ff64c
--    app_console_photo_visibilite_optimistic  0a5f62d1b41843e9400380a15ab14958
-- ════════════════════════════════════════════════════════════════════════════════


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  ① AVANT : la fonction existe-t-elle deja ? (elle ne devrait PAS)            ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

select coalesce(
         (select string_agg(p.proname || '(' || pg_get_function_arguments(p.oid) || ')', E'\n')
            from pg_proc p join pg_namespace n on n.oid = p.pronamespace
           where n.nspname = 'public'
             and p.proname = 'app_console_photos_reordonner_optimistic'),
         'ABSENTE -- c''est bien une fonction NEUVE') as etat_avant;

-- et les deux soeurs, qui ne doivent pas bouger
select p.proname, md5(replace(pg_get_functiondef(p.oid), chr(13), '')) as empreinte
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_console_photo_couverture_optimistic',
                     'app_console_photo_visibilite_optimistic')
 order by 1;


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  ② LE PATCH                                                                  ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

CREATE OR REPLACE FUNCTION public.app_console_photos_reordonner_optimistic(
  p_app_dossier_id    bigint,
  p_hektor_annonce_id text,
  p_ordre             text[]
)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  v_annonce   text := nullif(btrim(coalesce(p_hektor_annonce_id, '')), '');
  v_avant     jsonb;
  v_ordre_av  text;
  v_ordre_ap  text;
  v_visibles  jsonb;
  v_masquees  jsonb;
  v_job_id    uuid;
  v_combien   integer;
  v_n_demande integer;
  v_n_distinct integer;
  v_n_reel    integer;
  v_inconnues text;
  v_manquantes text;
  v_boites    integer := 0;
  v_tampon    integer;
BEGIN
  -- ⓵ DES PARAMETRES LISIBLES
  IF v_annonce IS NULL OR p_app_dossier_id IS NULL OR p_ordre IS NULL THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'parametres_incomplets');
  END IF;
  v_n_demande := coalesce(array_length(p_ordre, 1), 0);
  IF v_n_demande = 0 THEN
    -- ⚠ Le handler du worker refuse deja une liste vide (« on refuse d'envoyer un
    --   ordre sans photo visible »). On refuse ICI AUSSI, pour ne meme pas creer le
    --   travail : un refus qui arrive plus tot est un refus qui coute moins.
    RETURN jsonb_build_object('ok', false, 'erreur', 'ordre_vide');
  END IF;

  -- ⓶ LES DROITS. La meme garde que deposer, supprimer, mettre en couverture et
  --    masquer : le negociateur sur SES biens. On ne fabrique pas une 5e regle.
  IF NOT coalesce(public.app_console_can_access_dossier(p_app_dossier_id, v_annonce), false) THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'droits_insuffisants');
  END IF;

  -- ⓷ L'ETAT D'AVANT DE TOUTE L'ANNONCE, garde dans la charge : c'est le retour
  --    arriere de l'ecran, et il porte le rang ET le drapeau de CHAQUE photo.
  SELECT jsonb_agg(jsonb_build_object('hektor_photo_id', hektor_photo_id,
                                      'sort_order', sort_order,
                                      'visible', visible)
                   ORDER BY visible DESC, sort_order ASC, id ASC)
    INTO v_avant
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id
     AND present_in_hektor IS TRUE;

  -- ⓸ ⭐⭐ LE GARDE-FOU DE LA LISTE EXACTE. C'est la piece neuve, et elle existe
  --    parce qu'un comportement de Hektor n'est PAS MESURE : on ne sait pas ce
  --    qu'il fait d'un ordre PARTIEL. On refuse donc tout ecart, en nommant
  --    lequel -- un refus qui ne dit pas ce qui cloche fait perdre une heure.
  SELECT count(DISTINCT x) INTO v_n_distinct FROM unnest(p_ordre) AS x;
  IF v_n_distinct <> v_n_demande THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'ordre_avec_doublons',
                              'demandees', v_n_demande, 'distinctes', v_n_distinct);
  END IF;

  SELECT count(*) INTO v_n_reel
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id
     AND present_in_hektor IS TRUE
     AND visible IS TRUE;

  -- les ids demandes que l'annonce ne porte pas (visibles, chez Hektor)
  SELECT string_agg(x, ',') INTO v_inconnues
    FROM unnest(p_ordre) AS x
   WHERE NOT EXISTS (
     SELECT 1 FROM public.app_console_photo p
      WHERE p.app_dossier_id = p_app_dossier_id
        AND p.hektor_photo_id = x
        AND p.present_in_hektor IS TRUE
        AND p.visible IS TRUE);
  IF v_inconnues IS NOT NULL THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'ordre_avec_photos_inconnues',
                              'inconnues', v_inconnues);
  END IF;

  -- les visibles de l'annonce que la liste oublie
  SELECT string_agg(p.hektor_photo_id, ',') INTO v_manquantes
    FROM public.app_console_photo p
   WHERE p.app_dossier_id = p_app_dossier_id
     AND p.present_in_hektor IS TRUE
     AND p.visible IS TRUE
     AND NOT (p.hektor_photo_id = ANY (p_ordre));
  IF v_manquantes IS NOT NULL THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'ordre_incomplet',
                              'manquantes', v_manquantes,
                              'demandees', v_n_demande, 'attendues', v_n_reel);
  END IF;

  -- ⓹ DEJA DANS CET ORDRE ? Alors on ne derange pas Hektor. ⭐ On compare les deux
  --    SUITES, pas les nombres : deux listes de meme taille peuvent differer.
  SELECT string_agg(hektor_photo_id, ',' ORDER BY sort_order ASC, id ASC)
    INTO v_ordre_av
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id
     AND present_in_hektor IS TRUE
     AND visible IS TRUE;
  v_ordre_ap := array_to_string(p_ordre, ',');
  IF v_ordre_av = v_ordre_ap THEN
    RETURN jsonb_build_object('ok', true, 'deja_dans_cet_ordre', true,
                              'ordre', v_ordre_ap);
  END IF;

  -- ⓺ ⭐⭐ CHEZ NOUS D'ABORD -- la regle de Frederic du 19/10. On renumerote
  --    DE 0 A n-1 dans l'ordre DONNE.
  --    ⚠ Jamais « le rang 1 » : mesure du 19/10 sur 49 192 annonces -- 47 580
  --      commencent a 0 (96,7 %), 1 569 a 1, 43 ailleurs, 338 ont des TROUS et 21
  --      ont deux photos AU MEME RANG. Renumeroter 0 -> n-1 remet tout d'aplomb,
  --      donc ce geste REPARE ces 359 annonces au passage.
  WITH voulu AS (
    SELECT x AS hektor_photo_id, (ord - 1)::integer AS rang
      FROM unnest(p_ordre) WITH ORDINALITY AS t(x, ord)
  )
  UPDATE public.app_console_photo p
     SET sort_order = v.rang, updated_at = now()
    FROM voulu v
   WHERE p.app_dossier_id = p_app_dossier_id
     AND p.hektor_photo_id = v.hektor_photo_id
     AND p.visible IS TRUE
     AND p.present_in_hektor IS TRUE
     AND p.sort_order IS DISTINCT FROM v.rang;
  GET DIAGNOSTICS v_combien = ROW_COUNT;

  -- ⓻ LES DEUX LISTES QUE HEKTOR ATTEND. Sa page en tient DEUX : les visibles
  --    (`liste_photos`) et les masquees (`liste_photos_hidden`). On lui renvoie
  --    les deux, les masquees DANS LEUR ORDRE INCHANGE.
  --    ⭐ C'est ce qui fait que reordonner NE PEUT PAS demasquer : les deux listes
  --      partent separement, et le handler SAUTE celle qui est vide.
  SELECT coalesce(jsonb_agg(hektor_photo_id ORDER BY sort_order ASC, id ASC), '[]'::jsonb)
    INTO v_visibles
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id AND visible IS TRUE AND present_in_hektor IS TRUE;

  SELECT coalesce(jsonb_agg(hektor_photo_id ORDER BY sort_order ASC, id ASC), '[]'::jsonb)
    INTO v_masquees
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id AND visible IS FALSE AND present_in_hektor IS TRUE;

  -- ⓼ ⭐⭐ LE POST-IT SUR LES QUATRE INDEX -- recopie A L'IDENTIQUE de la recette du
  --    masquage (empreinte 0a5f62d1), parce que l'ordre des photos alimente
  --    `app_photos_remplir_adresses_app`, le fabricant de la boite publique.
  --    ⛔ On ne recalcule PAS la boite ici : sa regle (dont le verrou
  --      « visible is not false ») vit dans le fabricant, et deux copies
  --      divergeraient au premier ajustement.
  --    ⚠ LES QUATRE INDEX, PAS SEULEMENT LES VIVANTS : une annonce archivee n'a pas
  --      de galerie publique mais elle a une COUVERTURE, et reordonner peut la
  --      changer (la 1re EST la couverture).
  --    ⭐ LA COUVERTURE NE LE FAIT PAS, et ca s'est vu : le 19/10, la boite de 63261
  --      datait du 11/10 et celle de 63046 du 27/09, alors que leur couverture avait
  --      change le 16/10.
  UPDATE public.app_dossier_current SET adresses_app_le = NULL
   WHERE app_dossier_id = p_app_dossier_id AND adresses_app_le IS NOT NULL;
  GET DIAGNOSTICS v_boites = ROW_COUNT;

  UPDATE public.app_archive_annonce_index_current SET adresses_app_le = NULL
   WHERE app_archive_id = p_app_dossier_id AND adresses_app_le IS NOT NULL;
  GET DIAGNOSTICS v_tampon = ROW_COUNT;
  v_boites := v_boites + v_tampon;

  UPDATE public.app_historical_annonce_index_current SET adresses_app_le = NULL
   WHERE app_historical_id = p_app_dossier_id AND adresses_app_le IS NOT NULL;
  GET DIAGNOSTICS v_tampon = ROW_COUNT;
  v_boites := v_boites + v_tampon;

  UPDATE public.app_brouillon_annonce_index_current SET adresses_app_le = NULL
   WHERE app_brouillon_id = p_app_dossier_id AND adresses_app_le IS NOT NULL;
  GET DIAGNOSTICS v_tampon = ROW_COUNT;
  v_boites := v_boites + v_tampon;

  -- ⓽ LE TRAVAIL, DANS LA MEME TRANSACTION. Si l'insertion echoue, la
  --    renumerotation est annulee avec elle : on ne reste jamais avec un ordre
  --    change chez nous et rien de parti chez Hektor.
  --    ⭐ `motif` vaut 'reordonnancement' -- la couverture pose 'couverture'. Le
  --      handler journalise le motif, donc les deux usages du MEME type de travail
  --      restent distinguables dans le suivi.
  INSERT INTO public.app_console_job
    (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
  VALUES
    ('reorder_hektor_photos', p_app_dossier_id, v_annonce,
     jsonb_build_object(
       'motif', 'reordonnancement',
       'hektor_photo_id', NULL,
       'liste_photos', v_visibles,
       'liste_photos_hidden', v_masquees,
       'base_snapshot', coalesce(v_avant, '[]'::jsonb)),
     20, auth.uid())
  RETURNING id INTO v_job_id;

  RETURN jsonb_build_object(
    'ok', true,
    'deja_dans_cet_ordre', false,
    'job_id', v_job_id,
    'ordre_avant', v_ordre_av,
    'ordre_apres', v_ordre_ap,
    'photos_renumerotees', v_combien,
    'visibles', jsonb_array_length(v_visibles),
    'masquees', jsonb_array_length(v_masquees),
    -- ⭐ LE POST-IT EST-IL POSE ? Si ce compte est 0, le fabricant ne reciblera PAS
    --   l'annonce et la boite resterait vieille : c'est mesurable, donc on le rend
    --   plutot que de l'esperer. (0 est normal si elle etait DEJA a refaire.)
    'index_marques_a_refaire', v_boites,
    -- ⭐ LE SIGNAL POUR L'ECRAN : la 1re photo EST la couverture. Si elle change,
    --   l'humain doit le savoir -- pas le decouvrir sur la vitrine.
    'couverture_a_change', (split_part(coalesce(v_ordre_av, ''), ',', 1)
                            IS DISTINCT FROM split_part(v_ordre_ap, ',', 1)),
    'nouvelle_couverture', split_part(v_ordre_ap, ',', 1));
END $function$;


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  ③ APRES : la fonction est-elle la, et les deux soeurs sont-elles intactes ? ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

select p.proname,
       md5(replace(pg_get_functiondef(p.oid), chr(13), '')) as empreinte,
       case p.proname
         when 'app_console_photo_couverture_optimistic'
           then case when md5(replace(pg_get_functiondef(p.oid), chr(13), '')) = 'cbe7d5372e79040a4eb6b7cc644ff64c'
                     then 'INTACTE' else 'A CHANGE -- ARRET' end
         when 'app_console_photo_visibilite_optimistic'
           then case when md5(replace(pg_get_functiondef(p.oid), chr(13), '')) = '0a5f62d1b41843e9400380a15ab14958'
                     then 'INTACTE' else 'A CHANGE -- ARRET' end
         else 'NEUVE'
       end as verdict
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_console_photos_reordonner_optimistic',
                     'app_console_photo_couverture_optimistic',
                     'app_console_photo_visibilite_optimistic')
 order by 1;
