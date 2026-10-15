-- =============================================================================
--  LE BOUTON EXISTE PARTOUT OU L'ALERTE SONNE                     15/10/2026
--  (« OUI ALIGNE LES 2 » -- Frederic, 15/10)
-- =============================================================================
--  CE QU'ON REPARE, ET POURQUOI C'EST MOI QUI L'AI CASSE A MOITIE.
--  Le 14/10 j'ai elargi la vue app_en_attente_humain a « 5 tentatives epuisees OU
--  plus de 3 heures », et j'ai ecrit « le travail devient visible ». Visible, oui.
--  TRANCHABLE, non : les deux fonctions du bandeau portent CHACUNE SA COPIE du
--  `>= 5`. Mesure du 15/10 :
--
--      app_en_attente_humain (la vue, corrigee le 14/10)  5 OU > 3 h   le voit
--      app_action_status     (le bandeau du bien)         >= 5         NE LE LISTE PAS
--      app_action_resolve    (le clic)                    >= 5         REFUSE
--
--  ➡ Le travail 47824 sonnait, apparaissait dans le moniteur, et n'avait AUCUN
--    bouton -- et le refus etait SILENCIEUX (la RPC rend
--    {"resolved": false, "reason": "rien_a_trancher"}, que le front jetait).
--
--  ⚠⚠ ET IL Y AVAIT UN TROISIEME MUR, QUE SEULE LA MESURE A TROUVE.
--  Aligner les seuils n'aurait PAS suffi. `app_action_status` commence par
--      select * into d from app_dossier_current where app_dossier_id = ...;
--      if not found then raise exception 'dossier_not_found';
--  Or le bien de 47824 -- « Maison de village a renover », VM8012 -- est VENDU :
--  depuis le 20/05 il n'est plus dans app_dossier_current mais dans
--  app_historical_annonce_index_current. La fonction levait donc une exception, le
--  front l'avalait (« un echec de lecture ne doit pas priver l'utilisateur de sa
--  fiche ») et LE BANDEAU NE S'AFFICHAIT JAMAIS.
--  ⭐ C'est la MEME supposition fausse que le defaut 5a du 08/10 -- « le bien est
--    dans app_dossier_current » -- fausse pour 44 259 biens. On la balaie ici dans
--    sa derniere case (lecon 9 : une cause structurelle se balaie dans TOUTE sa
--    famille).
--
--  ⚠ ON INCLUT LES ARCHIVES, DELIBEREMENT. Une archive est en lecture seule pour
--    ses CHAMPS -- mais trancher un geste abandonne ne modifie pas le bien : ca
--    repond a une ALERTE. L'exclure recreerait exactement le defaut qu'on repare :
--    une alerte visible et ETERNELLE.
--
--  ⚠ CE QUE CET ELARGISSEMENT COUTE, ET IL FAUT LE DIRE. Un travail de 4 heures
--    avec 2 tentatives devient tranchable, alors que le filet de rejeu pourrait
--    encore le reprendre (sa fenetre est de 24 h). Si l'humain l'abandonne et que
--    le filet le rejoue ensuite avec succes, Hektor recevra le geste APRES qu'on
--    l'a declare abandonne -- et le retour arriere du carnet (patch frere du
--    15/10) aura efface notre valeur. La descente du matin remettra tout d'accord.
--    C'est le choix de Frederic, pris en connaissance : mieux vaut un bouton qui
--    existe qu'une alerte eternelle.
--    ⭐ Et le filet ne concerne QUE 9 types idempotents : les deux travaux
--      d'aujourd'hui (sync_console_documents) n'en font pas partie -- pour eux, il
--      n'y a RIEN a rejouer, donc rien a perdre.
--
--  LES DEUX PATCHS DU 15/10 SONT INDEPENDANTS : leurs ancres ne se touchent pas.
--  On peut les coller dans n'importe quel ordre.
--
--  METHODE : on NE RECOPIE PAS les fonctions. On les LIT dans la base, on controle
--  que chaque ancre est unique, on remplace, on reexecute.
--
--  A COLLER UNE SEULE FOIS. L'editeur Supabase n'affiche pas les NOTICE.
-- =============================================================================

-- ---------------------------------------------------------------------
-- 0. GARDE-FOU D'ENTREE
-- ---------------------------------------------------------------------
DO $patch$
DECLARE n int;
BEGIN
  IF to_regprocedure('public.app_action_resolve(uuid,text)') IS NULL
     OR to_regprocedure('public.app_action_status(bigint)') IS NULL THEN
    RAISE EXCEPTION 'STOP : app_action_resolve ou app_action_status est introuvable';
  END IF;

  -- La vue du 14/10 doit bien porter la regle des 3 heures : c'est sur elle qu'on
  -- s'aligne. Si elle ne l'a pas, c'est l'autre patch qu'il faut coller d'abord.
  IF position('03:00:00' in pg_get_viewdef('public.app_en_attente_humain'::regclass, true)) = 0 THEN
    RAISE EXCEPTION 'STOP : app_en_attente_humain ne porte PAS la regle des 3 heures -- collez d''abord patch_bandeau_erreurs_definitives_2026-10-15.sql';
  END IF;

  -- Les deux index de repli doivent exister, avec la colonne qu'on va y lire.
  SELECT count(*) INTO n FROM information_schema.columns
   WHERE table_schema = 'public'
     AND ((table_name = 'app_historical_annonce_index_current'
           AND column_name IN ('app_historical_id','hektor_annonce_id'))
       OR (table_name = 'app_archive_annonce_index_current'
           AND column_name IN ('app_archive_id','hektor_annonce_id')));
  IF n <> 4 THEN RAISE EXCEPTION 'STOP : les index de repli n''ont pas leurs colonnes (%)', n; END IF;
END $patch$;

-- ---------------------------------------------------------------------
-- 1. app_action_resolve : le CLIC accepte la regle des 3 heures
-- ---------------------------------------------------------------------
DO $patch$
DECLARE
  v_corps text;
  v_occ   int;
  a1 CONSTANT text := '  if j.status <> ''error'' or coalesce(j.attempt_count, 0) < 5 then';
  n1 CONSTANT text := $neuf$  -- @seuil-3h (15/10/2026) : la MEME regle que la vue app_en_attente_humain.
  -- Un travail dont le type n'est pas rejouable n'atteindra JAMAIS 5 tentatives :
  -- il etait donc visible dans le moniteur et impossible a trancher. Passe 3 h
  -- (le filet epuise ses 5 tentatives en 50 min : marge x3,6), on laisse l'humain
  -- decider. Les 3 heures sont mesurees, pas choisies.
  if j.status <> 'error'
     or (coalesce(j.attempt_count, 0) < 5
         and j.requested_at >= now() - interval '3 hours') then$neuf$;
BEGIN
  SELECT pg_get_functiondef('public.app_action_resolve(uuid,text)'::regprocedure) INTO v_corps;

  IF position('@seuil-3h' in v_corps) > 0 THEN
    RAISE NOTICE 'DEJA POSE (app_action_resolve). Rien a faire.';
  ELSE
    v_occ := (length(v_corps) - length(replace(v_corps, a1, ''))) / length(a1);
    IF v_occ <> 1 THEN RAISE EXCEPTION 'STOP : l''ancre du seuil (resolve) apparait % fois, attendu 1', v_occ; END IF;
    EXECUTE replace(v_corps, a1, n1);
    RAISE NOTICE 'POSE : app_action_resolve accepte « 5 tentatives OU plus de 3 h ».';
  END IF;
END $patch$;

-- ---------------------------------------------------------------------
-- 2. app_action_status : le BANDEAU liste, et il trouve les vendus/clos
-- ---------------------------------------------------------------------
DO $patch$
DECLARE
  v_corps text;
  v_occ   int;

  -- ① le seuil
  a1 CONSTANT text := '     and coalesce(j.attempt_count, 0) >= 5';
  n1 CONSTANT text := $neuf$     -- @seuil-3h (15/10/2026) : la MEME regle que la vue app_en_attente_humain.
     and (coalesce(j.attempt_count, 0) >= 5
          or j.requested_at < now() - interval '3 hours')$neuf$;

  -- ② le repli vendus/clos et archives
  a2 CONSTANT text := $vieux$  select * into d from public.app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode = '22023'; end if;$vieux$;
  n2 CONSTANT text := $neuf$  select * into d from public.app_dossier_current where app_dossier_id = target_dossier_id;

  -- @repli-trancher (15/10/2026) : UN BIEN VENDU, CLOS OU ARCHIVE A AUSSI SON BOUTON.
  --
  -- MESURE DU 15/10 : le travail en erreur 47824 porte un bien VENDU
  -- (« Maison de village a renover », VM8012). Depuis le 20/05 il n'est plus dans
  -- app_dossier_current mais dans app_historical_annonce_index_current. Cette
  -- fonction levait 'dossier_not_found', le front avalait l'erreur -- il le fait
  -- EXPRES, « un echec de lecture ne doit pas priver l'utilisateur de sa fiche » --
  -- et LE BANDEAU NE S'AFFICHAIT JAMAIS. Le travail sonnait eternellement.
  --
  -- ⭐ Meme supposition fausse que le defaut 5a du 08/10 (« le bien est dans
  --   app_dossier_current »), fausse pour 44 259 biens : on la balaie ici dans sa
  --   derniere case.
  -- ⭐ LE NUMERO RECU EST LE BON : app_historical_id et app_archive_id SONT notre
  --   app_dossier_id, renomme (export_app_payload.py:363).
  -- ⚠ ON INCLUT LES ARCHIVES, deliberement : une archive est en lecture seule pour
  --   ses CHAMPS, mais trancher un geste abandonne ne modifie pas le bien -- ca
  --   repond a une ALERTE. L'exclure recreerait le defaut qu'on repare.
  if d.app_dossier_id is null then
    select h.app_historical_id, h.hektor_annonce_id
      into d.app_dossier_id, d.hektor_annonce_id
      from public.app_historical_annonce_index_current h
     where h.app_historical_id = target_dossier_id;
  end if;
  if d.app_dossier_id is null then
    select x.app_archive_id, x.hektor_annonce_id
      into d.app_dossier_id, d.hektor_annonce_id
      from public.app_archive_annonce_index_current x
     where x.app_archive_id = target_dossier_id;
  end if;
  if d.app_dossier_id is null then
    raise exception 'dossier_not_found' using errcode = '22023';
  end if;$neuf$;
BEGIN
  SELECT pg_get_functiondef('public.app_action_status(bigint)'::regprocedure) INTO v_corps;

  IF position('@repli-trancher' in v_corps) > 0 THEN
    RAISE NOTICE 'DEJA POSE (app_action_status). Rien a faire.';
  ELSE
    v_occ := (length(v_corps) - length(replace(v_corps, a1, ''))) / length(a1);
    IF v_occ <> 1 THEN RAISE EXCEPTION 'STOP : l''ancre du seuil (status) apparait % fois, attendu 1', v_occ; END IF;
    v_occ := (length(v_corps) - length(replace(v_corps, a2, ''))) / length(a2);
    IF v_occ <> 1 THEN RAISE EXCEPTION 'STOP : l''ancre du repli apparait % fois, attendu 1', v_occ; END IF;

    v_corps := replace(v_corps, a1, n1);
    v_corps := replace(v_corps, a2, n2);
    EXECUTE v_corps;
    RAISE NOTICE 'POSE : app_action_status liste aussi les travaux de plus de 3 h, et trouve les vendus/clos.';
  END IF;
END $patch$;

COMMENT ON FUNCTION public.app_action_status(bigint) IS
  'Les gestes abandonnes d''un bien, pour le bandeau de sa fiche. Regle du '
  '15/10/2026 : « 5 tentatives epuisees OU plus de 3 heures », identique a la vue '
  'app_en_attente_humain -- un type non rejouable n''atteint jamais 5 tentatives. '
  'Et le bien est cherche dans les TROIS endroits (parc vivant, vendus/clos, '
  'archives) : un bien vendu n''est plus dans app_dossier_current depuis le 20/05, '
  'et le bandeau ne s''affichait donc jamais pour lui.';

-- ---------------------------------------------------------------------
-- 3. CONTROLE
-- ---------------------------------------------------------------------
SELECT (position('@seuil-3h' in pg_get_functiondef('public.app_action_resolve(uuid,text)'::regprocedure)) > 0) AS clic_aligne,
       (position('@seuil-3h' in pg_get_functiondef('public.app_action_status(bigint)'::regprocedure)) > 0)     AS bandeau_aligne,
       (position('@repli-trancher' in pg_get_functiondef('public.app_action_status(bigint)'::regprocedure)) > 0) AS repli_pose;

-- Et la liste de ce qui est MAINTENANT tranchable. `tranchable` doit valoir true
-- pour les quatre travaux de plus de 3 heures.
SELECT j.hektor_annonce_id, j.job_type, coalesce(j.attempt_count, 0) AS tentatives,
       round(extract(epoch from (now() - j.requested_at)) / 3600.0, 1) AS age_h,
       (coalesce(j.attempt_count, 0) >= 5
        OR j.requested_at < now() - interval '3 hours') AS tranchable,
       CASE WHEN d.app_dossier_id IS NOT NULL THEN 'parc vivant'
            WHEN h.app_historical_id IS NOT NULL THEN 'vendus/clos (repli)'
            WHEN x.app_archive_id IS NOT NULL THEN 'archives (repli)'
            ELSE 'INTROUVABLE' END AS ou_est_le_bien
  FROM public.app_console_job j
  LEFT JOIN public.app_dossier_current d                 ON d.app_dossier_id = j.app_dossier_id
  LEFT JOIN public.app_historical_annonce_index_current h ON h.app_historical_id = j.app_dossier_id
  LEFT JOIN public.app_archive_annonce_index_current x    ON x.app_archive_id = j.app_dossier_id
 WHERE j.status = 'error' AND j.requested_at > now() - interval '30 days'
 ORDER BY j.requested_at;
