-- =====================================================================
-- RETOUR ARRIERE du patch « VENDU / CLOS MANIPULABLE » (statut) -- 12/10/2026
-- Patch : supabase/patch_chantier3_repli_index_statut_2026-10-12.sql
--
-- Il refait les 2 remplacements A L'ENVERS et ne reexecute la fonction QUE si le texte obtenu
-- est, au caractere pres, celle d'avant ce patch (empreinte 1f9e987f…, c'est-a-dire la fonction
-- qui porte deja le bloc 3a).
--
-- ⚠ IL REMET AUSSI « Mandat clos ». Le patch corrigeait l'etiquette (« Mandat clos » -> « Clos »,
--   la vraie valeur : 34 916 lignes contre 0). Pour retirer le repli SANS perdre la correction
--   d'etiquette, supprimer la paire R2 des deux tableaux ci-dessous avant de lancer ce script.
--
-- ⚠ CE QUI N'EST PAS DEFAIT : rien d'autre. Ce script ne touche aucune donnee. Les travaux deja
--   crees pour des biens vendus/clos restent -- ils portent un VRAI numero de dossier, que le
--   worker et les ecrans savent lire.
-- =====================================================================

BEGIN;

DO $inverse$
DECLARE
  c_sig constant text := 'public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)';
  c_emp constant text := '1f9e987f3a2a9fc977ae4efd6db5b000';

  a text[]; b text[];
  v_def text; v_retour text; v_apres text;
  i int; n int;
BEGIN
  v_def := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');

  IF position('@repli-debut' in v_def) = 0 THEN
    IF md5(v_def) = c_emp THEN
      RAISE NOTICE 'RIEN A FAIRE : le repli n''est pas la et l''empreinte est deja celle d''avant (%)', c_emp;
      RETURN;
    END IF;
    RAISE EXCEPTION 'STOP : le repli n''est pas dans la fonction, et l''empreinte (%) n''est pas celle d''avant (%) -- a regarder a la main',
      md5(v_def), c_emp;
  END IF;

  a := ARRAY[
    $a1$  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode = '22023'; end if;$a1$,
    $a2$                          when 'closed'     then 'Mandat clos'$a2$
  ];

  b := ARRAY[
    $b1$  -- @repli-debut   CHANTIER 3 (12/10/2026) : LE BIEN PEUT ETRE VENDU OU CLOS
  --
  -- LA REGLE DE LA MAISON, telle que l'ECRAN la porte depuis le 21/05/2026
  -- (`isReadOnlyLightweightDetail`, App.tsx:406-411), et telle que Frederic l'a confirmee
  -- le 12/10 :
  --     · VENDU / CLOS  -> les gestes marchent (l'ecran les ouvre des que le detail est la)
  --     · ARCHIVE       -> LECTURE SEULE, sa seule sortie est « Desarchiver »
  --     · BROUILLON     -> lecture seule
  --
  -- Depuis le 20/05, les Vendu/Clos ne sont plus dans app_dossier_current : ils vivent dans
  -- `app_historical_annonce_index_current`. Cette fonction, ecrite le 25/08, l'ignorait et
  -- refusait 8 941 biens sur un « dossier_not_found » brut, alors que l'ecran affichait le
  -- bouton. L'ecran a trois etats, la base n'en avait qu'un.
  --
  -- ⭐ LE NUMERO RECU EST LE BON. `app_historical_id` n'est pas une serie a part : c'est
  --   NOTRE `app_dossier_id`, renomme (export_app_payload.py:363), verifie par les anciens
  --   travaux des memes biens. On le garde donc TEL QUEL pour les droits, le carnet et le
  --   travail -- aucun faux identifiant n'est pose nulle part.
  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then
    select h.app_historical_id, h.hektor_annonce_id, h.numero_dossier, h.titre_bien,
           h.statut_annonce, h.diffusable, h.archive
      into d.app_dossier_id, d.hektor_annonce_id, d.numero_dossier, d.titre_bien,
           d.statut_annonce, d.diffusable, d.archive
      from public.app_historical_annonce_index_current h
     where h.app_historical_id = target_dossier_id;

    if not found then
      -- UNE ARCHIVE RESTE EN LECTURE SEULE -- c'est voulu, pas un oubli. On le DIT, au lieu
      -- de rendre « dossier_not_found », qui ne veut rien dire pour celui qui lit.
      if exists (select 1 from public.app_archive_annonce_index_current x
                  where x.app_archive_id = target_dossier_id) then
        raise exception 'annonce_archivee_lecture_seule' using errcode = '22023';
      end if;
      raise exception 'dossier_not_found' using errcode = '22023';
    end if;

    -- ⚠ UNE OFFRE, UN COMPROMIS OU UNE VENTE restent reserves au parc vivant : ils creent une
    --   ligne dans le registre des affaires, et une affaire se tient sur un bien en vie.
    if target_status not in ('active', 'closed') then
      raise exception 'transaction_hors_parc_vivant' using errcode = '22023';
    end if;
  end if;
  -- @repli-fin$b1$,
    $b2$                          when 'closed'     then 'Clos'$b2$
  ];

  -- ⚠ LES FINS DE LIGNE WINDOWS : `v_def` est lu sans chr(13), mais ce script colle depuis
  --   Windows en porte. On normalise les deux tableaux de la meme facon.
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
    RAISE EXCEPTION 'STOP : en defaisant le patch on obtient % au lieu de % -- retrait annule',
      md5(v_retour), c_emp;
  END IF;

  EXECUTE v_retour;

  v_apres := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  IF md5(v_apres) <> c_emp THEN
    RAISE EXCEPTION 'STOP : apres retrait la base porte % au lieu de %', md5(v_apres), c_emp;
  END IF;
  IF position('@repli' in v_apres) > 0 THEN
    RAISE EXCEPTION 'STOP : le repli est encore la apres le retrait';
  END IF;

  RAISE NOTICE 'OK : repli retire, la fonction est revenue a l''identique (empreinte %)', md5(v_apres);
END $inverse$;

COMMIT;
