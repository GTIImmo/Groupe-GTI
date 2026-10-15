-- =============================================================================
--  « ABANDONNER CE GESTE » DEFAIT CE QUE L'APP AVAIT ECRIT        15/10/2026
-- =============================================================================
--  LA QUESTION DE FREDERIC, mot pour mot :
--    « comment dire a mon apps d'annuler le worker et annuler le changement dans
--      l'apps c'est a dire remettre le montant comme hektor »
--
--  LE DEFAUT. Depuis le chantier ③ (12/10), l'app ecrit CHEZ NOUS D'ABORD : un
--  changement de statut, un archivage, un desarchivage ou une affectation de
--  negociateur posent la valeur dans NOTRE base, puis le travail part chez Hektor.
--  Si le travail echoue definitivement, l'ecran offre deux boutons -- et les DEUX
--  font exactement la meme chose : un INSERT dans app_pending_resolution, qui ne
--  sert qu'a faire TAIRE l'alerte.
--    « J'ai refait »        -> masque l'alerte. Rien d'autre.
--    « Abandonner ce geste » -> masque l'alerte. Rien d'autre.
--  ➡ LA VALEUR ECRITE PAR L'APP RESTE EN PLACE, pour toujours, alors que Hektor
--    n'a jamais recu le geste. Personne ne le dit.
--
--  CE QUE CE PATCH CHANGE. « Abandonner » veut dire « ce geste n'a pas eu lieu ».
--  Il DEFAIT donc l'ecriture de l'app -- la fiche reprend la valeur d'avant, et le
--  carnet se tait, ce qui veut dire « l'app n'a rien a dire, Hektor gagne »
--  (phase2/identite/contrat_autorite.py : « l'app n'a rien -> ON NE TOUCHE A RIEN »).
--  « J'ai refait » n'est PAS touche : l'humain a fait le geste a la main, sa valeur
--  est donc la bonne -- on ne va pas la lui effacer.
--
--  ⭐⭐ CE QUE LE PROJET AVAIT DEJA TRANCHE, et qu'on ne refait pas.
--  Les 4 RPC optimistes posent DEJA l'etat d'avant dans la charge du travail --
--  'statut_avant', 'diffusable_avant', 'archive_avant', 'negociateur_avant' -- et
--  le commentaire de app_geste_affaire_optimistic le dit en clair : « le travail
--  EMPORTE l'etat precedent, pour que le worker sache quoi restaurer ». La matiere
--  du retour arriere etait deja la : il n'y a rien a inventer, juste a s'en servir.
--
--  ⚠⚠ CE QU'ON NE TOUCHE SURTOUT PAS : LES QUATRE GESTES D'AFFAIRE.
--  Pour l'offre, le compromis et la vente, le worker RESTAURE DEJA (console_job_-
--  worker.js, restaurerEtatAffaire + restaurerStatutRedescendu), et il le fait
--  exactement quand le filet de rejeu s'arrete -- donc AVANT que le bandeau ne
--  s'affiche. Y ajouter un second retour arriere serait un DOUBLE retour arriere.
--  Le garde-fou ci-dessous l'ecarte tout seul (le worker repose la valeur avec un
--  `ecrit_le` neuf, qui ne correspond plus a l'instant du travail), mais la raison
--  doit etre ecrite : ce patch ne vise QUE les gestes d'ANNONCE, les seuls dont
--  personne ne defait l'ecriture.
--
--  ⭐ LE GARDE-FOU, ET IL EST MESURE, PAS SUPPOSE.
--  Comment savoir quelles lignes du carnet appartiennent a CE travail, et pas a un
--  geste plus recent qui a reussi ? Les deux colonnes valent `now()` par defaut, et
--  `now()` est FIGE pendant une transaction : la RPC ecrit le carnet et cree le
--  travail dans la MEME transaction, donc
--        app_annonce_champ_app.ecrit_le  =  app_console_job.requested_at
--  A LA MICROSECONDE. Mesure du 15/10 sur les deux vrais travaux en erreur et leurs
--  21 couples possibles : UN SEUL couple par ligne de carnet tombe a 0,000 s ; tous
--  les autres sont a 44 s, 124 s, 8 006 s, 473 236 s. C'est un IDENTIFIANT, pas une
--  approximation -- et c'est la regle du 14/10 : « on croise sur les identifiants,
--  jamais sur les nombres ».
--  ⚠ ET CE GARDE-FOU N'EST PAS DECORATIF : sur les deux travaux en erreur
--    d'aujourd'hui, la ligne du carnet a ete ecrite par un geste PLUS RECENT
--    (61672 : 2 h 14 plus tard ; 62963 : 2 min plus tard). Sans lui, abandonner
--    aurait efface une valeur LEGITIME. Avec lui, ces deux abandons ne touchent
--    RIEN -- et c'est la bonne reponse.
--
--  LE SECOND GARDE-FOU : on ne remet la fiche que si elle porte ENCORE ce que ce
--  geste y avait ecrit. Si le run de nuit, ou un autre geste, l'a deja changee, on
--  n'y touche pas -- et le compte-rendu le dit (`fiche_remise: 0`).
--
--  ⚠ CE QU'ON NE PEUT PAS FAIRE, ET IL FAUT LE SAVOIR : « remettre comme Hektor »
--    veut dire ici « remettre la valeur que NOTRE COPIE portait juste avant le
--    geste ». C'est la meilleure source disponible entre deux descentes, et c'est
--    exactement celle que le worker utilise depuis le 01/09. Si Hektor a change
--    entre-temps, la descente du matin tranchera.
--  ⚠ ET UN TRAVAIL SANS ETAT D'AVANT NE REMET RIEN. Mesure du 15/10 : le travail de
--    61672 (13/10 11:37) n'a PAS la cle 'statut_avant' -- la ligne qui la pose est
--    arrivee apres lui. Dans ce cas on nettoie le carnet et on NE TOUCHE PAS a la
--    fiche, et le compte-rendu porte 'valeur_avant': null. On ne devine pas.
--
--  LA TRACE. Le compte-rendu de ce qui a ete defait est range dans le
--  payload_json de app_pending_resolution, cle 'defait'. Et comme tout se passe
--  dans UNE SEULE transaction (c'est une fonction plpgsql), si l'ecriture de la
--  trace echoue, les effacements sont annules avec elle -- la regle du 13/10
--  (« pour un geste irreversible, la trace est une CONDITION, pas un effet de
--  bord ») est tenue par construction.
--
--  CE QUE CA NE CHANGE PAS :
--    · la sentinelle data.travaux_en_erreur et sa cle "exclure_resolus" -- elles
--      lisent app_pending_resolution, qui recoit sa ligne comme avant ;
--    · le bandeau (app_action_status) et la vue app_en_attente_humain -- leur
--      NOT EXISTS est inchange, la ligne sort de la liste comme avant ;
--    · les droits : tout se passe dans app_action_resolve, DERRIERE sa garde
--      app_console_can_request_job. Personne ne gagne un pouvoir : celui qui peut
--      abandonner un geste est celui qui pouvait le demander.
--    · le carnet n'est relu PAR PERSONNE aujourd'hui (CHAMPS_APP_ANNONCE est vide,
--      et le front ne le lit pas) : le nettoyage n'a donc AUCUN effet visible
--      aujourd'hui. Il compte pour LE JOUR DE LA COUPURE, ou le carnet devient la
--      verite -- et c'est justement la qu'une valeur fausse ferait mal.
--
--  METHODE : on NE RECOPIE PAS la fonction. On la LIT dans la base, on verifie son
--  empreinte, on controle que chaque ancre est unique, on insere, on reexecute.
--
--  A COLLER UNE SEULE FOIS. L'editeur Supabase n'affiche pas les NOTICE.
-- =============================================================================

-- ---------------------------------------------------------------------
-- 0. GARDE-FOU D'ENTREE
-- ---------------------------------------------------------------------
DO $patch$
DECLARE v_empreinte text; n int;
BEGIN
  IF to_regprocedure('public.app_action_resolve(uuid,text)') IS NULL THEN
    RAISE EXCEPTION 'STOP : app_action_resolve(uuid,text) est introuvable';
  END IF;

  SELECT md5(replace(pg_get_functiondef('public.app_action_resolve(uuid,text)'::regprocedure), chr(13), ''))
    INTO v_empreinte;

  IF v_empreinte <> '5590da3aff0e57512d8fb69c13abab2d' THEN
    RAISE NOTICE 'ATTENTION : empreinte % -- ce n''est plus la fonction mesuree le 15/10. Les controles d''ancre decideront.', v_empreinte;
  END IF;

  -- Les colonnes dont on va se servir doivent exister, toutes les cinq.
  SELECT count(*) INTO n FROM information_schema.columns
   WHERE table_schema = 'public' AND table_name = 'app_annonce_champ_app'
     AND column_name IN ('app_dossier_id','champ','valeur_app','ecrit_le');
  IF n <> 4 THEN RAISE EXCEPTION 'STOP : app_annonce_champ_app n''a pas ses 4 colonnes (%)', n; END IF;

  SELECT count(*) INTO n FROM information_schema.columns
   WHERE table_schema = 'public' AND table_name = 'app_dossier_current'
     AND column_name IN ('statut_annonce','diffusable','archive','negociateur_email');
  IF n <> 4 THEN RAISE EXCEPTION 'STOP : app_dossier_current n''a pas ses 4 colonnes (%)', n; END IF;
END $patch$;

-- ---------------------------------------------------------------------
-- 1. LE REMPLACEMENT, SUR LE CORPS LU DANS LA BASE
-- ---------------------------------------------------------------------
DO $patch$
DECLARE
  v_corps text;
  v_occ   int;

  -- ① la declaration des variables de travail
  a1 CONSTANT text := '  j public.app_console_job%rowtype;';
  n1 CONSTANT text := $neuf$  j public.app_console_job%rowtype;
  -- @abandon (15/10/2026) : de quoi defaire ce que l'app avait ecrit.
  v_defait jsonb := '[]'::jsonb;
  v_champ  record;
  v_avant  text;
  v_fiche  int;$neuf$;

  -- ② le retour arriere, AVANT l'ecriture de la trace (meme transaction)
  a2 CONSTANT text := '  insert into public.app_pending_resolution';
  n2 CONSTANT text := $neuf$  -- @abandon-debut   15/10/2026 : « ABANDONNER » DEFAIT L'ECRITURE DE L'APP.
  --
  -- « Abandonner » veut dire « ce geste n'a pas eu lieu ». Avant aujourd'hui, les
  -- deux boutons faisaient la meme chose -- faire taire l'alerte -- et la valeur
  -- que l'app avait posee chez nous restait en place pour toujours, alors que
  -- Hektor n'avait jamais recu le geste.
  --
  -- ⭐ LES LIGNES DU CARNET QUI APPARTIENNENT A CE TRAVAIL se reconnaissent a leur
  --   instant d'ecriture : la RPC optimiste ecrit le carnet et cree le travail dans
  --   la MEME transaction, et `now()` y est figé -- donc ecrit_le = requested_at a la
  --   microseconde. Mesure du 15/10 : un seul couple a 0,000 s, les autres a 44 s,
  --   124 s, 8 006 s, 473 236 s. Un geste PLUS RECENT qui a reussi porte un autre
  --   instant : on ne le touche pas.
  -- ⚠ Et c'est ce qui ecarte tout seul LES QUATRE GESTES D'AFFAIRE : le worker les
  --   restaure deja (restaurerEtatAffaire), en reposant la valeur avec un ecrit_le
  --   neuf. Pas de double retour arriere.
  if mode = 'abandon' then
    for v_champ in
      select c.champ, c.valeur_app
        from public.app_annonce_champ_app c
       where c.app_dossier_id = j.app_dossier_id
         and c.ecrit_le = j.requested_at
       order by c.champ
    loop
      -- L'etat d'avant voyage dans la charge du travail depuis le chantier ③ : les
      -- RPC optimistes le posent (« pour que le worker sache quoi restaurer »).
      -- Un travail qui ne le porte pas ne fait RIEN remettre -- on ne devine pas.
      v_avant := case v_champ.champ
                   when 'statut'            then j.payload_json->>'statut_avant'
                   when 'diffusable'        then j.payload_json->>'diffusable_avant'
                   when 'archive'           then j.payload_json->>'archive_avant'
                   when 'negociateur_email' then j.payload_json->>'negociateur_avant'
                   else null end;
      v_fiche := 0;

      -- LA FICHE, et seulement si elle porte ENCORE ce que ce geste y a ecrit.
      -- Si le run de nuit ou un autre geste l'a deja changee, on n'y touche pas.
      -- (archive_motif et clos_motif n'ont pas de colonne de fiche : le carnet est
      --  leur seul domicile, ils sortent donc par le `else null` ci-dessus.)
      if v_avant is not null then
        if v_champ.champ = 'statut' then
          update public.app_dossier_current set statut_annonce = v_avant
           where app_dossier_id = j.app_dossier_id
             and statut_annonce is not distinct from v_champ.valeur_app;
        elsif v_champ.champ = 'diffusable' then
          update public.app_dossier_current set diffusable = v_avant
           where app_dossier_id = j.app_dossier_id
             and diffusable is not distinct from v_champ.valeur_app;
        elsif v_champ.champ = 'archive' then
          update public.app_dossier_current set archive = v_avant
           where app_dossier_id = j.app_dossier_id
             and archive is not distinct from v_champ.valeur_app;
        elsif v_champ.champ = 'negociateur_email' then
          update public.app_dossier_current set negociateur_email = v_avant
           where app_dossier_id = j.app_dossier_id
             and negociateur_email is not distinct from v_champ.valeur_app;
        end if;
        get diagnostics v_fiche = row_count;
      end if;

      -- LE CARNET : on EFFACE, on ne reecrit pas. Une ligne absente veut dire
      -- « l'app n'a rien a dire », donc Hektor gagne -- c'est la regle du contrat
      -- d'autorite. Y remettre l'ancienne valeur de Hektor serait la REVENDIQUER
      -- comme une valeur de l'app, et la FIGERAIT le jour de la coupure : c'est
      -- exactement « LE GEL » que le projet a nomme et retire le 16/09.
      delete from public.app_annonce_champ_app
       where app_dossier_id = j.app_dossier_id
         and champ          = v_champ.champ
         and ecrit_le       = j.requested_at;

      v_defait := v_defait || jsonb_build_object(
        'champ',         v_champ.champ,
        'valeur_app',    v_champ.valeur_app,
        'valeur_avant',  v_avant,
        'fiche_remise',  v_fiche,
        'carnet_efface', true);
    end loop;
  end if;
  -- @abandon-fin

  insert into public.app_pending_resolution$neuf$;

  -- ③ la trace de ce qui a ete defait, dans la ligne de resolution
  a3 CONSTANT text := '     jsonb_build_object(''job_id'', target_job_id::text,';
  n3 CONSTANT text := $neuf$     jsonb_build_object('defait', v_defait,
                        'job_id', target_job_id::text,$neuf$;

  -- ④ le compte-rendu rendu a l'ecran
  a4 CONSTANT text := '  return jsonb_build_object(''resolved'', true, ''mode'', mode, ''job_type'', j.job_type);';
  n4 CONSTANT text := $neuf$  return jsonb_build_object('resolved', true, 'mode', mode, 'job_type', j.job_type,
                            'defait', v_defait,
                            'champs_defaits', jsonb_array_length(v_defait));$neuf$;
BEGIN
  SELECT pg_get_functiondef('public.app_action_resolve(uuid,text)'::regprocedure) INTO v_corps;

  IF position('@abandon-debut' in v_corps) > 0 THEN
    RAISE NOTICE 'DEJA POSE : le retour arriere est deja dans la fonction. Rien a faire.';
    RETURN;
  END IF;

  -- Chaque ancre doit apparaitre EXACTEMENT une fois. Sinon on ne touche a rien.
  v_occ := (length(v_corps) - length(replace(v_corps, a1, ''))) / length(a1);
  IF v_occ <> 1 THEN RAISE EXCEPTION 'STOP : ancre ① vue % fois, attendu 1', v_occ; END IF;
  v_occ := (length(v_corps) - length(replace(v_corps, a2, ''))) / length(a2);
  IF v_occ <> 1 THEN RAISE EXCEPTION 'STOP : ancre ② vue % fois, attendu 1', v_occ; END IF;
  v_occ := (length(v_corps) - length(replace(v_corps, a3, ''))) / length(a3);
  IF v_occ <> 1 THEN RAISE EXCEPTION 'STOP : ancre ③ vue % fois, attendu 1', v_occ; END IF;
  v_occ := (length(v_corps) - length(replace(v_corps, a4, ''))) / length(a4);
  IF v_occ <> 1 THEN RAISE EXCEPTION 'STOP : ancre ④ vue % fois, attendu 1', v_occ; END IF;

  v_corps := replace(v_corps, a1, n1);
  v_corps := replace(v_corps, a2, n2);
  v_corps := replace(v_corps, a3, n3);
  v_corps := replace(v_corps, a4, n4);

  EXECUTE v_corps;
  RAISE NOTICE 'POSE : « Abandonner ce geste » defait desormais l''ecriture de l''app.';
END $patch$;

COMMENT ON FUNCTION public.app_action_resolve(uuid,text) IS
  'Trancher un geste abandonne. « J''ai refait » : l''humain l''a fait a la main, '
  'on ne touche a rien. « Abandonner » (15/10/2026) : le geste n''a pas eu lieu, '
  'donc on DEFAIT l''ecriture de l''app -- la fiche reprend l''etat d''avant '
  '(pose dans la charge du travail par les RPC optimistes) et la ligne du carnet '
  'est effacee, ce qui rend la parole a Hektor. Les lignes de carnet de CE travail '
  'se reconnaissent a ecrit_le = requested_at (meme transaction, a la microseconde) : '
  'un geste plus recent qui a reussi n''est jamais touche. Les quatre gestes '
  'd''affaire sont hors de portee : le worker les restaure deja.';

-- ---------------------------------------------------------------------
-- 2. CONTROLE : la fonction porte le correctif, et l'empreinte nouvelle
-- ---------------------------------------------------------------------
SELECT (position('@abandon-debut' in pg_get_functiondef('public.app_action_resolve(uuid,text)'::regprocedure)) > 0) AS correctif_pose,
       (position('''defait'', v_defait' in pg_get_functiondef('public.app_action_resolve(uuid,text)'::regprocedure)) > 0) AS trace_posee,
       md5(replace(pg_get_functiondef('public.app_action_resolve(uuid,text)'::regprocedure), chr(13), '')) AS nouvelle_empreinte;

-- Et ce qu'un abandon defferait AUJOURD'HUI sur les travaux en erreur : la colonne
-- `lignes_a_defaire` doit valoir 0 partout -- les lignes de carnet de ces deux biens
-- ont ete ecrites par un geste PLUS RECENT (mesure du 15/10).
SELECT j.hektor_annonce_id, j.job_type, coalesce(j.attempt_count, 0) AS tentatives,
       (SELECT count(*) FROM public.app_annonce_champ_app c
         WHERE c.app_dossier_id = j.app_dossier_id AND c.ecrit_le = j.requested_at) AS lignes_a_defaire
  FROM public.app_console_job j
 WHERE j.status = 'error' AND j.requested_at > now() - interval '30 days'
 ORDER BY j.requested_at;
