-- =====================================================================
-- RETOUR ARRIERE du patch 3b (archiver + negociateur) -- 13/10/2026
-- Patch : supabase/patch_chantier3_3b_etat_chez_nous_2026-10-13.sql
--
-- Il refait les 3 remplacements A L'ENVERS et ne reexecute chaque fonction QUE si le texte
-- obtenu est, au caractere pres, celui d'avant le patch. Si l'une refuse, la transaction
-- annule les DEUX.
--
-- ⚠ CE QUI N'EST PAS DEFAIT : les valeurs deja ecrites. Elles sont justes -- Hektor les a
--   confirmees -- et le run reecrit de toute facon `archive` et `negociateur_email` chaque
--   nuit. Les lignes de carnet `archive_motif` restent aussi : elles sont vraies, et
--   personne ne les lit. Pour les effacer malgre tout :
--     delete from public.app_annonce_champ_app where champ = 'archive_motif';
-- =====================================================================

BEGIN;

DO $inverse$
DECLARE
  c_arch constant text := 'public.app_archive_annonce_optimistic(bigint,jsonb,integer)';
  c_nego constant text := 'public.app_assign_negotiator_optimistic(bigint,text,jsonb,integer)';
  e_arch constant text := '04dfcb30fa1a6010ce3714d4c85dfddd';
  e_nego constant text := '85bde9eb83c794ddfcd08445316e4064';

  a text[]; b text[];
  v_def text; v_retour text; v_apres text;
  i int; n int;
BEGIN
  a := ARRAY[
    $a1$  -- 1. CHEZ NOUS D'ABORD
  insert into public.app_annonce_champ_app (app_dossier_id, champ, valeur_app, origine, ecrit_par)
  values (target_dossier_id, 'archive', '1', 'geste_archiver', auth.uid()::text)
  on conflict (app_dossier_id, champ) do update
     set valeur_app = excluded.valeur_app,
         origine    = excluded.origine,
         ecrit_le   = now(),
         ecrit_par  = excluded.ecrit_par;$a1$,
    $a2$  v_charge := coalesce(job_payload, '{}'::jsonb) || jsonb_build_object(
    'numero_dossier', d.numero_dossier,
    'titre_bien',     d.titre_bien,
    'target_archive', '1');$a2$,
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

  FOR i IN 1 .. array_length(a, 1) LOOP
    a[i] := replace(a[i], chr(13), '');
    b[i] := replace(b[i], chr(13), '');
  END LOOP;

  -- ── ARCHIVER ──
  v_def := replace(pg_get_functiondef(c_arch::regprocedure), chr(13), '');
  IF position('@3b-debut' in v_def) = 0 THEN
    IF md5(v_def) = e_arch THEN
      RAISE NOTICE 'RIEN A FAIRE : % est deja revenue a l''identique', c_arch;
    ELSE
      RAISE EXCEPTION 'STOP : % n''a pas le patch 3b et son empreinte (%) n''est pas celle d''avant (%)',
        c_arch, md5(v_def), e_arch;
    END IF;
  ELSE
    v_retour := v_def;
    FOR i IN REVERSE 2 .. 1 LOOP
      n := (length(v_retour) - length(replace(v_retour, b[i], ''))) / length(b[i]);
      IF n <> 1 THEN RAISE EXCEPTION 'STOP : morceau R% trouve % fois dans %', i, n, c_arch; END IF;
      v_retour := replace(v_retour, b[i], a[i]);
    END LOOP;
    IF md5(v_retour) <> e_arch THEN
      RAISE EXCEPTION 'STOP : % -- le retrait rend % au lieu de %', c_arch, md5(v_retour), e_arch;
    END IF;
    EXECUTE v_retour;
    v_apres := replace(pg_get_functiondef(c_arch::regprocedure), chr(13), '');
    IF md5(v_apres) <> e_arch THEN
      RAISE EXCEPTION 'STOP : apres retrait, % porte %', c_arch, md5(v_apres);
    END IF;
    RAISE NOTICE 'OK : % -- revenue a l''identique', c_arch;
  END IF;

  -- ── NEGOCIATEUR ──
  v_def := replace(pg_get_functiondef(c_nego::regprocedure), chr(13), '');
  IF position('@3b-debut' in v_def) = 0 THEN
    IF md5(v_def) = e_nego THEN
      RAISE NOTICE 'RIEN A FAIRE : % est deja revenue a l''identique', c_nego;
    ELSE
      RAISE EXCEPTION 'STOP : % n''a pas le patch 3b et son empreinte (%) n''est pas celle d''avant (%)',
        c_nego, md5(v_def), e_nego;
    END IF;
  ELSE
    n := (length(v_def) - length(replace(v_def, b[3], ''))) / length(b[3]);
    IF n <> 1 THEN RAISE EXCEPTION 'STOP : morceau R3 trouve % fois dans %', n, c_nego; END IF;
    v_retour := replace(v_def, b[3], a[3]);
    IF md5(v_retour) <> e_nego THEN
      RAISE EXCEPTION 'STOP : % -- le retrait rend % au lieu de %', c_nego, md5(v_retour), e_nego;
    END IF;
    EXECUTE v_retour;
    v_apres := replace(pg_get_functiondef(c_nego::regprocedure), chr(13), '');
    IF md5(v_apres) <> e_nego THEN
      RAISE EXCEPTION 'STOP : apres retrait, % porte %', c_nego, md5(v_apres);
    END IF;
    RAISE NOTICE 'OK : % -- revenue a l''identique', c_nego;
  END IF;
END $inverse$;

COMMIT;
