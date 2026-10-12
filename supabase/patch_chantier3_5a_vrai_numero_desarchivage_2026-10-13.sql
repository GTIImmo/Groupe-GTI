-- =====================================================================
-- CORRECTION DU DEFAUT 5a -- LE DESARCHIVAGE POSAIT UN NUMERO VIDE
-- Date : 2026-10-13 · Detail : notice/CHANTIER_3_HEKTOR_DABORD_2026-10-12.md
--
-- POURQUOI. Le 08/10, 5a a donne a `app_restore_annonce_optimistic` un second chemin pour
-- retrouver une archive (par `app_archive_id`). Mais il posait ensuite `v_dossier := null`,
-- sur cette phrase ecrite dans la note du jour : « nous n'avons AUCUN numero de dossier pour
-- une archive » -- et la justification « y ecrire le numero d'archive serait poser un FAUX
-- identifiant (la faute meme de 5d et 5g) ».
--
-- ⭐ LA PREMISSE EST FAUSSE, ET C'EST MESURE SUR TOUT LE PARC (13/10). Les trois index sont
--   fabriques par `CAST(app_dossier_id AS INTEGER) AS app_archive_id / app_historical_id /
--   app_brouillon_id` (export_app_payload.py:316, 363, 451). Recoupement par un chemin
--   INDEPENDANT -- le numero de dossier que portent les ANCIENS travaux de chaque bien :
--       35 318 archives recoupees · 35 312 identiques · 6 ecarts
--       et les 6 sont des FANTOMES deja reconcilies (deux numeros dans leur histoire,
--       le plus recent EST `app_archive_id`).
--   La mesure qui m'avait convaincu -- « 0 des 35 317 `app_archive_id` n'existe comme
--   `app_dossier_id` » -- ne disait pas « ce n'est pas un numero de dossier » : elle disait
--   « aucune archive n'est dans la table des vivants », ce qui est la DEFINITION d'une
--   archive. J'avais pris une tautologie pour une preuve.
--
-- CE QUE COUTE LE DEFAUT (mesure du 13/10 : 16 desarchivages depuis le 21/05, tous `done`,
-- dont 1 seul sans numero -- le defaut est donc surtout DEVANT nous) :
--   ① le bandeau « geste abandonne » ne voit rien : `GesteAbandonneBanner` (App.tsx:32925)
--      appelle `loadActionStatus(dossier.app_dossier_id)` ;
--   ② le filet de rejeu ne peut pas detecter un geste DEPASSE : sa boucle 0 compare
--      `plus_recent.app_dossier_id = j.app_dossier_id`, et `NULL = NULL` n'est jamais vrai
--      -> un desarchivage deja refait par un geste plus recent serait REJOUE.
--
-- CE QUE FAIT LE PATCH -- 3 remplacements, chacun verifie UNIQUE :
--   R1  `v_dossier := null` devient `v_dossier := target_dossier_id` (le vrai numero)
--   R2  le commentaire qui portait la premisse fausse
--   R3  le commentaire qui justifiait le « faux identifiant »
--   (R2 et R3 ne changent rien a l'execution -- mais laisser un commentaire qui CONTREDIT
--    le code, c'est preparer la prochaine erreur.)
--
-- CE QUI SUIT TOUT SEUL : le `if v_dossier is not null` plus bas ecrit alors la ligne de
-- carnet `archive='0'` (aujourd'hui SAUTEE pour toute archive), et le travail porte le vrai
-- numero.
--
-- ⚠ CE QUI POURRAIT CASSER AILLEURS -- verifie le 13/10 :
--   · LES DROITS D'UN NEGOCIATEUR, le vrai point : `restore_hektor_annonce` est dans la liste
--     des gestes ouverts au `commercial`, donc ce numero part dans
--     `app_console_can_access_dossier`. Lue dans la base : elle teste
--     « (le numero de dossier correspond) OU (le numero Hektor correspond) », sur LES TROIS
--     sources (vivants, archives, historique). Aujourd'hui, numero vide -> c'est la branche
--     Hektor qui tranche ; demain les deux branches designeront LE MEME bien (0 collision
--     entre les series, mesure du 12/10). Le resultat ne peut donc pas devenir plus
--     permissif sur un AUTRE bien.
--   · le worker `handleRestoreHektorAnnonce` tolere les deux (prouve par 5a) -> AUCUN
--     redemarrage ;
--   · le filet de rejeu S'AMELIORE (la detection du geste depasse redevient possible) ;
--   · le carnet gagne 1 ligne par desarchivage, `origine='geste_desarchiver'`, relue par
--     PERSONNE aujourd'hui (`CHAMPS_APP_ANNONCE` est vide) -> aucun changement de
--     comportement ;
--   · le chemin du bien VIVANT n'est pas touche (la ligne est dans la branche « archive ») ;
--   · les 16 travaux existants ne sont pas reecrits.
--
-- RETOUR ARRIERE : supabase/patch_chantier3_5a_vrai_numero_desarchivage_2026-10-13_INVERSE.sql
-- REPETITION     : supabase/patch_chantier3_5a_vrai_numero_desarchivage_2026-10-13_REPETITION.sql
-- =====================================================================

BEGIN;

DO $patch$
DECLARE
  c_sig constant text := 'public.app_restore_annonce_optimistic(bigint,jsonb,integer)';
  c_emp constant text := '709571469083a76b1be384e879ca523b';
  c_taille constant int := 3557;

  a text[]; b text[];
  v_def text; v_apres text; v_retour text;
  i int; n int;
BEGIN
  v_def := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');

  IF md5(v_def) <> c_emp THEN
    RAISE EXCEPTION 'STOP : la fonction n''est pas celle mesuree le 13/10 (empreinte %, attendue %, taille % contre %)',
      md5(v_def), c_emp, length(v_def), c_taille;
  END IF;
  IF position('@5a-vrai-numero' in v_def) > 0 THEN
    RAISE EXCEPTION 'STOP : le patch est deja passe';
  END IF;

  a := ARRAY[
    $a1$    v_dossier := null;   -- nous n'avons AUCUN numero de dossier pour une archive$a1$,
    $a2$    --    (mesure du 08/10). L'index des archives n'a pas de numero de dossier ; l'ecran
    --    envoie donc son `app_archive_id` a cette place (api.ts:2618). C'est par la qu'on$a2$,
    $a3$  --    numero de dossier ; pour une archive il n'y en a pas, et y ecrire le numero
  --    d'archive serait poser un FAUX identifiant (la faute meme de 5d et 5g). Ce carnet$a3$
  ];

  b := ARRAY[
    $b1$    -- @5a-vrai-numero (13/10/2026) : LE NUMERO RECU EST LE NOTRE, ON LE GARDE.
    --   `app_archive_id` n'est pas une serie a part : c'est NOTRE `app_dossier_id`, renomme
    --   (export_app_payload.py:316). Recoupe le 13/10 par un chemin independant -- le numero
    --   que portent les ANCIENS travaux de chaque bien : 35 312 identiques sur 35 318, et les
    --   6 ecarts sont des fantomes deja reconcilies dont le numero RECENT est bien celui-ci.
    --   Le mettre a NULL privait le bandeau « geste abandonne » (App.tsx:32925, il cherche par
    --   numero de dossier) et empechait le filet de rejeu de voir un geste DEPASSE
    --   (`NULL = NULL` n'est jamais vrai).
    v_dossier := target_dossier_id;$b1$,
    $b2$    --    (mesure du 08/10). L'index des archives range NOTRE numero de dossier sous le
    --    nom `app_archive_id` ; l'ecran l'envoie a cette place (api.ts:2618). C'est par la qu'on$b2$,
    $b3$  --    numero de dossier -- et une archive EN A UN : `app_archive_id` est notre
  --    `app_dossier_id` renomme (verifie le 13/10). Ce carnet$b3$
  ];

  -- ⚠ FINS DE LIGNE : le corps est lu sans chr(13), ce script colle depuis Windows en porte.
  FOR i IN 1 .. array_length(a, 1) LOOP
    a[i] := replace(a[i], chr(13), '');
    b[i] := replace(b[i], chr(13), '');
  END LOOP;

  FOR i IN 1 .. array_length(a, 1) LOOP
    n := (length(v_def) - length(replace(v_def, a[i], ''))) / length(a[i]);
    IF n <> 1 THEN
      RAISE EXCEPTION 'STOP : l''ancre R% a ete trouvee % fois, il en faut exactement 1', i, n;
    END IF;
    v_def := replace(v_def, a[i], b[i]);
  END LOOP;

  EXECUTE v_def;

  -- CONTROLE DE SORTIE : le chemin inverse doit rendre l'empreinte d'avant, au caractere pres.
  v_apres  := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  v_retour := v_apres;
  FOR i IN REVERSE array_length(a, 1) .. 1 LOOP
    v_retour := replace(v_retour, b[i], a[i]);
  END LOOP;

  IF md5(v_retour) <> c_emp THEN
    RAISE EXCEPTION 'STOP : en refaisant le chemin inverse on obtient % au lieu de % -- autre chose a change',
      md5(v_retour), c_emp;
  END IF;

  RAISE NOTICE 'OK : 3 remplacements, taille % -> %, le reste est intact (retour = %)',
    c_taille, length(v_apres), md5(v_retour);
END $patch$;

COMMIT;
