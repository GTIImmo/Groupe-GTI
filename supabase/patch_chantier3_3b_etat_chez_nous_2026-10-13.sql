-- =====================================================================
-- CHANTIER ③ -- POINT 3b : ARCHIVER ET CHANGER DE NEGOCIATEUR S'ECRIVENT CHEZ NOUS
-- Date : 2026-10-13 · Detail : notice/CHANTIER_3_HEKTOR_DABORD_2026-10-12.md
--
-- POURQUOI. C'est le meme defaut que 3a, sur deux gestes de plus. Ces deux fonctions
-- ecrivent bien « chez nous d'abord » -- mais SEULEMENT au CARNET, que personne ne relit
-- aujourd'hui. La FICHE du bien, elle, n'est pas touchee : notre base continue de dire
-- « actif » et « ancien negociateur » tant que Hektor n'a pas repondu.
--   · archiver        : mesure du 12/10 sur le bien 62965 -- 2 a 3 minutes d'ecart
--   · negociateur     : 4 gestes depuis juillet, la colonne n'a JAMAIS ete juste avant
--                       la reponse de Hektor
--
-- ⚠ ET LE MOTIF D'ARCHIVAGE SE PERD. Audit du 13/10 : la modale demande un motif riche
--   (2 motifs principaux, 9 causes, prix, confrere) et le worker l'ENVOIE bien a Hektor
--   (`context=validerArchivage`). Mais AUCUNE colonne de notre base ne le porte -- recherche
--   sur tout le schema : 0 colonne motif/raison/cause sur l'annonce. Il ne survit que dans
--   `app_console_job.payload_json`, conserve mais introuvable sans fouiller. A la coupure,
--   on garderait la date et le geste, et on perdrait LA RAISON.
--   ➡ Ce patch le range au carnet, dans la MEME transaction. Si Frederic n'en veut pas,
--     c'est la paire R2 qu'il faut retirer -- le reste tient sans elle.
--
-- CE QUE FAIT LE PATCH -- 3 remplacements, chacun verifie UNIQUE :
--   R1  archiver    : la FICHE recoit `archive='1'`
--   R2  archiver    : le CARNET recoit le MOTIF (`archive_motif`), a cote de `archive`
--   R3  archiver    : l'etat d'avant (`archive_avant`) voyage dans la charge du travail
--   R4  negociateur : la FICHE recoit le nouvel email, et l'ancien part dans la charge
--
-- CE QUI NE CHANGE PAS (verifie le 13/10) :
--   · ce qui part chez Hektor : RIEN n'est modifie dans la charge au-dela de l'etat d'avant ;
--   · les droits : `app_console_can_request_job` -- inchange, admin/manager ;
--   · les workers : aucune ligne modifiee -> AUCUN redemarrage ;
--   · le repli vendu/clos pose hier soir : conserve mot pour mot (il est au-dessus) ;
--   · la protection des saisies (L3) : elle lit `app_annonce_pending`, pas ces champs ;
--   · le run : il reecrit `archive` et `negociateur_email` depuis Hektor chaque nuit
--     -> retour arriere automatique au pire la nuit suivante.
--
-- ⚠ CE QUI ARRIVE PLUS TOT, ET QUI EST ASSUME :
--   · `archive='1'` -> le bien sort des listes actives TOUT DE SUITE (c'est le geste voulu),
--     et la page RDV publique se FERME plus tot : plus sur qu'aujourd'hui ;
--   · `negociateur_email` -> c'est LE champ du perimetre du negociateur (chantier ②) :
--     changer la colonne change immediatement QUI VOIT LE BIEN. C'est le geste voulu, et
--     cela arrive de toute facon 2 a 3 minutes plus tard. Mais cela se dit.
--   · ⚠ un bien VENDU/CLOS n'a plus de ligne dans `app_dossier_current` : l'`update` touche
--     alors 0 ligne, sans erreur -- et le carnet, lui, recoit bien la valeur.
--
-- RETOUR ARRIERE : supabase/patch_chantier3_3b_etat_chez_nous_2026-10-13_INVERSE.sql
-- REPETITION     : supabase/patch_chantier3_3b_etat_chez_nous_2026-10-13_REPETITION.sql
-- =====================================================================

BEGIN;

DO $patch$
DECLARE
  c_arch constant text := 'public.app_archive_annonce_optimistic(bigint,jsonb,integer)';
  c_nego constant text := 'public.app_assign_negotiator_optimistic(bigint,text,jsonb,integer)';
  e_arch constant text := '04dfcb30fa1a6010ce3714d4c85dfddd';
  e_nego constant text := '85bde9eb83c794ddfcd08445316e4064';

  a text[]; b text[];
  v_def text; v_apres text; v_retour text;
  i int; n int;
BEGIN
  a := ARRAY[
    -- R1+R2 : le bloc « chez nous d'abord » de l'archivage
    $a1$  -- 1. CHEZ NOUS D'ABORD
  insert into public.app_annonce_champ_app (app_dossier_id, champ, valeur_app, origine, ecrit_par)
  values (target_dossier_id, 'archive', '1', 'geste_archiver', auth.uid()::text)
  on conflict (app_dossier_id, champ) do update
     set valeur_app = excluded.valeur_app,
         origine    = excluded.origine,
         ecrit_le   = now(),
         ecrit_par  = excluded.ecrit_par;$a1$,
    -- R3 : la charge du travail d'archivage
    $a2$  v_charge := coalesce(job_payload, '{}'::jsonb) || jsonb_build_object(
    'numero_dossier', d.numero_dossier,
    'titre_bien',     d.titre_bien,
    'target_archive', '1');$a2$,
    -- R3 : le bloc « chez nous d'abord » du negociateur
    $a3$  -- 1. CHEZ NOUS D'ABORD -- mais seulement si on a quelque chose a dire.
  -- Sans email, on n'invente pas une valeur : le travail part quand meme, et le
  -- carnet reste muet. « L'app gagne seulement quand elle a quelque chose a dire. »
  if v_email is not null then$a3$
  ];

  b := ARRAY[
    $b1$  -- @3b-debut   CHANTIER 3, POINT 3b (13/10/2026) : LA FICHE AUSSI, ET LE MOTIF
  --
  -- Avant, ce geste n'ecrivait QUE le carnet -- que personne ne relit aujourd'hui. La
  -- fiche du bien n'etait pas touchee : notre base disait « actif » tant que Hektor
  -- n'avait pas repondu (2 a 3 minutes, mesure du 12/10 sur le bien 62965).
  --
  -- ⚠ ET LE MOTIF SE PERDAIT. La modale en demande un (2 motifs principaux, 9 causes,
  --   prix, confrere) et le worker l'envoie bien a Hektor (`validerArchivage`), mais
  --   AUCUNE colonne de notre base ne le portait -- 0 sur tout le schema. Il ne vivait
  --   que dans la charge du travail. A la coupure on aurait garde la date et le geste,
  --   et perdu LA RAISON. On le range donc au carnet, avec le reste.
  --
  -- ⚠ Si le bien est VENDU/CLOS il n'a plus de ligne ici : l'update touche 0 ligne, sans
  --   erreur, et le carnet recoit quand meme la valeur. C'est voulu.
  update public.app_dossier_current
     set archive = '1'
   where app_dossier_id = target_dossier_id;

  insert into public.app_annonce_champ_app (app_dossier_id, champ, valeur_app, origine, ecrit_le, ecrit_par)
  select target_dossier_id, x.champ, x.valeur, 'geste_archiver', now(), auth.uid()::text
    from (values
      ('archive'::text,       '1'::text),
      ('archive_motif'::text, nullif(concat_ws(' · ',
          nullif(trim(coalesce(job_payload->>'archive_main_choice', '')), ''),
          nullif(trim(coalesce(job_payload->>'archive_sub_choice',  '')), ''),
          nullif(trim(coalesce(job_payload->>'archive_other_text',  '')), '')), ''))
    ) as x(champ, valeur)
   where x.valeur is not null
  on conflict (app_dossier_id, champ) do update
     set valeur_app = excluded.valeur_app,
         origine    = excluded.origine,
         ecrit_le   = excluded.ecrit_le,
         ecrit_par  = excluded.ecrit_par;
  -- @3b-fin$b1$,
    $b2$  -- @3b-charge : l'etat d'avant voyage avec le travail, pour pouvoir revenir.
  v_charge := coalesce(job_payload, '{}'::jsonb) || jsonb_build_object(
    'numero_dossier', d.numero_dossier,
    'titre_bien',     d.titre_bien,
    'archive_avant',  d.archive,
    'target_archive', '1');$b2$,
    $b3$  -- @3b-debut   CHANTIER 3, POINT 3b (13/10/2026) : LA FICHE AUSSI
  --
  -- Avant, ce geste n'ecrivait QUE le carnet. La colonne `negociateur_email` de la fiche
  -- n'etait jamais juste avant la reponse de Hektor (4 gestes depuis juillet, mesure du
  -- 13/10). Or c'est ELLE que lit tout le reste de l'app.
  --
  -- ⚠ C'est aussi LE champ du perimetre du negociateur (chantier ②) : l'ecrire change
  --   immediatement qui voit le bien. C'est le geste voulu -- et cela arrivait de toute
  --   facon 2 a 3 minutes plus tard, par la relecture.
  --
  -- La regle d'avant est conservee mot pour mot : sans email, on n'invente rien, le
  -- travail part quand meme et le carnet reste muet.
  if v_email is not null then
    v_charge := v_charge || jsonb_build_object('negociateur_avant', d.negociateur_email);
    update public.app_dossier_current
       set negociateur_email = v_email
     where app_dossier_id = target_dossier_id;
  -- @3b-fin$b3$
  ];

  -- ⚠ FINS DE LIGNE : le corps est lu sans chr(13), ce script colle depuis Windows en porte.
  FOR i IN 1 .. array_length(a, 1) LOOP
    a[i] := replace(a[i], chr(13), '');
    b[i] := replace(b[i], chr(13), '');
  END LOOP;

  -- ── ARCHIVER ──
  v_def := replace(pg_get_functiondef(c_arch::regprocedure), chr(13), '');
  IF md5(v_def) <> e_arch THEN
    RAISE EXCEPTION 'STOP : % porte % au lieu de %', c_arch, md5(v_def), e_arch;
  END IF;
  IF position('@3b-debut' in v_def) > 0 THEN
    RAISE EXCEPTION 'STOP : % porte deja le patch 3b', c_arch;
  END IF;
  FOR i IN 1 .. 2 LOOP
    n := (length(v_def) - length(replace(v_def, a[i], ''))) / length(a[i]);
    IF n <> 1 THEN RAISE EXCEPTION 'STOP : ancre R% trouvee % fois dans %', i, n, c_arch; END IF;
    v_def := replace(v_def, a[i], b[i]);
  END LOOP;
  EXECUTE v_def;

  v_retour := replace(pg_get_functiondef(c_arch::regprocedure), chr(13), '');
  FOR i IN REVERSE 2 .. 1 LOOP
    v_retour := replace(v_retour, b[i], a[i]);
  END LOOP;
  IF md5(v_retour) <> e_arch THEN
    RAISE EXCEPTION 'STOP : % -- le chemin inverse rend % au lieu de %', c_arch, md5(v_retour), e_arch;
  END IF;
  RAISE NOTICE 'OK : % -- fiche + motif poses, le reste est intact', c_arch;

  -- ── NEGOCIATEUR ──
  v_def := replace(pg_get_functiondef(c_nego::regprocedure), chr(13), '');
  IF md5(v_def) <> e_nego THEN
    RAISE EXCEPTION 'STOP : % porte % au lieu de %', c_nego, md5(v_def), e_nego;
  END IF;
  IF position('@3b-debut' in v_def) > 0 THEN
    RAISE EXCEPTION 'STOP : % porte deja le patch 3b', c_nego;
  END IF;
  n := (length(v_def) - length(replace(v_def, a[3], ''))) / length(a[3]);
  IF n <> 1 THEN RAISE EXCEPTION 'STOP : ancre R3 trouvee % fois dans %', n, c_nego; END IF;
  v_def := replace(v_def, a[3], b[3]);
  EXECUTE v_def;

  v_apres  := replace(pg_get_functiondef(c_nego::regprocedure), chr(13), '');
  v_retour := replace(v_apres, b[3], a[3]);
  IF md5(v_retour) <> e_nego THEN
    RAISE EXCEPTION 'STOP : % -- le chemin inverse rend % au lieu de %', c_nego, md5(v_retour), e_nego;
  END IF;
  RAISE NOTICE 'OK : % -- fiche posee, le reste est intact', c_nego;
END $patch$;

COMMIT;
