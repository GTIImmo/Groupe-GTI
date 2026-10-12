-- =====================================================================
-- RETOUR ARRIERE de la correction du defaut 5a -- 13/10/2026
-- Patch : supabase/patch_chantier3_5a_vrai_numero_desarchivage_2026-10-13.sql
--
-- Il refait les 3 remplacements A L'ENVERS et ne reexecute la fonction QUE si le texte obtenu
-- est, au caractere pres, celle d'avant (empreinte 709571469083a76b1be384e879ca523b).
--
-- ⚠ CE QUI N'EST PAS DEFAIT : les travaux de desarchivage deja crees AVEC leur vrai numero le
--   gardent -- c'est une donnee juste, il n'y a aucune raison de la retirer. Et les lignes de
--   carnet `archive=0 / geste_desarchiver` posees entre-temps restent : elles sont vraies, et
--   personne ne les lit (`CHAMPS_APP_ANNONCE` est vide). Pour les effacer malgre tout :
--     delete from public.app_annonce_champ_app
--      where champ = 'archive' and origine = 'geste_desarchiver';
-- =====================================================================

BEGIN;

DO $inverse$
DECLARE
  c_sig constant text := 'public.app_restore_annonce_optimistic(bigint,jsonb,integer)';
  c_emp constant text := '709571469083a76b1be384e879ca523b';

  a text[]; b text[];
  v_def text; v_retour text; v_apres text;
  i int; n int;
BEGIN
  v_def := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');

  IF position('@5a-vrai-numero' in v_def) = 0 THEN
    IF md5(v_def) = c_emp THEN
      RAISE NOTICE 'RIEN A FAIRE : la correction n''est pas la et l''empreinte est deja celle d''avant (%)', c_emp;
      RETURN;
    END IF;
    RAISE EXCEPTION 'STOP : la correction n''est pas dans la fonction, et l''empreinte (%) n''est pas celle d''avant (%) -- a regarder a la main',
      md5(v_def), c_emp;
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

  FOR i IN 1 .. array_length(a, 1) LOOP
    a[i] := replace(a[i], chr(13), '');
    b[i] := replace(b[i], chr(13), '');
  END LOOP;

  v_retour := v_def;
  FOR i IN REVERSE array_length(b, 1) .. 1 LOOP
    n := (length(v_retour) - length(replace(v_retour, b[i], ''))) / length(b[i]);
    IF n <> 1 THEN
      RAISE EXCEPTION 'STOP : au retrait, le morceau R% a ete trouve % fois, il en faut 1', i, n;
    END IF;
    v_retour := replace(v_retour, b[i], a[i]);
  END LOOP;

  IF md5(v_retour) <> c_emp THEN
    RAISE EXCEPTION 'STOP : en defaisant la correction on obtient % au lieu de % -- retrait annule',
      md5(v_retour), c_emp;
  END IF;

  EXECUTE v_retour;

  v_apres := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  IF md5(v_apres) <> c_emp THEN
    RAISE EXCEPTION 'STOP : apres retrait la base porte % au lieu de %', md5(v_apres), c_emp;
  END IF;

  RAISE NOTICE 'OK : correction retiree, la fonction est revenue a l''identique (%)', md5(v_apres);
END $inverse$;

COMMIT;
