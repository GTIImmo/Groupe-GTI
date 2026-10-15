-- =============================================================================
--  LE BANDEAU MONTRE AUSSI LES TRAVAUX QUE PLUS RIEN NE REJOUERA   15/10/2026
-- =============================================================================
--  CE QUE FREDERIC A CONSTATE.
--  Son ecran Sante affiche « Travaux console en erreur : 3 », mais il ne peut
--  en trancher que DEUX : le troisieme n'apparait NULLE PART dans l'app.
--
--  POURQUOI. La branche 1 de app_en_attente_humain exige
--  `COALESCE(j.attempt_count, 0) >= 5`. Le travail en cause -- annonce 47824,
--  `sync_console_documents`, 14/10 a 19:00 -- n'a qu'UNE tentative.
--
--  ET IL N'EN AURA JAMAIS CINQ. Le filet de rejeu
--  (app_console_action_enqueue_due_retries, patch c4bis du 30/08) ne rejoue
--  QUE NEUF types, et son commentaire dit pourquoi : « uniquement les gestes
--  IDEMPOTENTS dont l'effet se verifie de facon ABSOLUE ; sans cela le rejeu
--  transforme un succes en echec, ou double une creation ».
--  `sync_console_documents` n'y est pas -- deliberement.
--
--  ➡ UN TRAVAIL NON REJOUABLE QUI ECHOUE EST DONC INVISIBLE *ET* ETERNEL :
--    il fait sonner le rouge, et personne ne peut le trancher.
--
--  LE REMEDE, ET POURQUOI IL EST SUR.
--  On ne touche PAS au filet de rejeu, et on n'ouvre PAS la liste des types
--  rejouables : on elargit seulement CE QUE LE BANDEAU MONTRE.
--  La regle devient : « 5 tentatives epuisees  OU  plus vieux que 3 heures ».
--  LES 3 HEURES SONT MESUREES, PAS CHOISIES. Le filet rejoue avec des attentes
--  de 5, 10, 15 et 20 minutes : CINQUANTE MINUTES en tout pour epuiser les 5
--  tentatives. Passe 3 heures (marge de 3,6 fois), un travail qui n'est pas a
--  5 tentatives ne le sera JAMAIS -- son type n'est pas rejouable. Le montrer
--  ne peut donc pas etre premature.
--  ⚠ MA PREMIERE VERSION DISAIT 24 HEURES (la constante `fraicheur` du filet).
--    L'epreuve a montre qu'elle ne changeait RIEN aujourd'hui : le travail 47824
--    a 14 heures. J'aurais fait attendre Frederic jusqu'a 19:00 pour rien.
--  ⭐ Et on ne duplique pas la liste des neuf types : on s'appuie sur une regle
--    DEJA ECRITE ailleurs, qui ne pourra pas diverger.
--
--  METHODE : on NE RECOPIE PAS la vue. On la LIT dans la base, on verifie son
--  empreinte, on controle que l'ancre est unique, on remplace, on reexecute --
--  le reste du corps est conserve au caractere pres.
--
--  A COLLER UNE SEULE FOIS. L'editeur Supabase n'affiche pas les NOTICE.
-- =============================================================================

-- ---------------------------------------------------------------------
-- 0. GARDE-FOU D'ENTREE
-- ---------------------------------------------------------------------
DO $$
DECLARE v_empreinte text; n int;
BEGIN
  IF to_regclass('public.app_en_attente_humain') IS NULL THEN
    RAISE EXCEPTION 'STOP : la vue app_en_attente_humain est introuvable';
  END IF;

  SELECT md5(replace(pg_get_viewdef('public.app_en_attente_humain'::regclass, true), chr(13), ''))
    INTO v_empreinte;

  IF v_empreinte = 'A_REMPLIR_APRES_POSE' THEN
    RAISE NOTICE 'DEJA POSE : la vue porte deja le correctif. Rien a faire.';
    RETURN;
  END IF;

  IF v_empreinte <> '8ae7e3abdf139acf519027762539ce58' THEN
    RAISE EXCEPTION 'STOP : la vue n''est plus celle mesuree le 15/10 (empreinte %) -- une autre session est passee', v_empreinte;
  END IF;

  SELECT count(*) INTO n FROM information_schema.columns
   WHERE table_name = 'app_en_attente_humain'
     AND column_name IN ('objet','reference','libelle','nature','cause','tentatives','depuis');
  IF n <> 7 THEN RAISE EXCEPTION 'STOP : la vue n''a pas ses 7 colonnes (%)', n; END IF;
END $$;

-- ---------------------------------------------------------------------
-- 1. LE REMPLACEMENT, SUR LE CORPS LU DANS LA BASE
-- ---------------------------------------------------------------------
DO $$
DECLARE
  v_corps  text;
  v_ancre  CONSTANT text := 'COALESCE(j.attempt_count, 0) >= 5';
  v_neuf   CONSTANT text := '(COALESCE(j.attempt_count, 0) >= 5 OR j.requested_at < (now() - ''3 hours''::interval))';
  v_occ    int;
BEGIN
  SELECT pg_get_viewdef('public.app_en_attente_humain'::regclass, true) INTO v_corps;

  IF position(v_neuf in v_corps) > 0 THEN
    RAISE NOTICE 'DEJA POSE : le texte est deja present.';
    RETURN;
  END IF;

  v_occ := (length(v_corps) - length(replace(v_corps, v_ancre, ''))) / length(v_ancre);
  IF v_occ <> 1 THEN
    RAISE EXCEPTION 'STOP : l''ancre apparait % fois, attendu 1', v_occ;
  END IF;

  v_corps := replace(v_corps, v_ancre, v_neuf);
  EXECUTE 'CREATE OR REPLACE VIEW public.app_en_attente_humain AS ' || v_corps;

  RAISE NOTICE 'POSE : le bandeau montre desormais les travaux que plus rien ne rejouera.';
END $$;

COMMENT ON VIEW public.app_en_attente_humain IS
  'Ce qui attend un humain. Branche 1 : les gestes abandonnes -- 5 tentatives '
  'epuisees OU plus vieux que 3 h (15/10/2026 : un '
  'travail non rejouable n''atteint jamais 5 tentatives, il etait donc '
  'invisible ET eternel). Branche 2 : la creation reussie dont la suite a '
  'echoue (4a, 09/10/2026). Dans les deux cas, une trace dans '
  'app_pending_resolution fait sortir la ligne.';

-- ---------------------------------------------------------------------
-- 2. CONTROLE : ce que le bandeau montre maintenant
-- ---------------------------------------------------------------------
SELECT objet, reference, libelle, tentatives,
       to_char(depuis, 'DD/MM HH24:MI') AS depuis,
       left(cause, 54) AS cause
  FROM public.app_en_attente_humain
 ORDER BY depuis;

-- Et la nouvelle empreinte, a reporter en tete de ce fichier si on veut le
-- rejouer plus tard sans risque.
SELECT md5(replace(pg_get_viewdef('public.app_en_attente_humain'::regclass, true), chr(13), ''))
       AS nouvelle_empreinte;
