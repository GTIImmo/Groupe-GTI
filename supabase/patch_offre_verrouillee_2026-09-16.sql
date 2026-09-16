-- ═══════════════════════════════════════════════════════════════════════════════
-- ON NE TOUCHE PLUS A UNE OFFRE DONT LE DOSSIER PORTE UN COMPROMIS   16/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Copie versionnee de la migration `geste_offre_verrouillee_par_le_compromis`.
--
-- LA REGLE, DANS LES MOTS DE FREDERIC (16/09) :
--     « il faut empecher la modification des offres d'achat du moment ou un
--       compromis est ouvert. Refuser une offre sur une chaine avec compromis
--       et vente ne devrait pas etre possible. »
--
-- ─── POURQUOI ICI, ET PAS SEULEMENT DANS L'ECRAN ───
-- L'ecran cache desormais les boutons (App.tsx, meme jour). Mais un ecran n'est
-- pas une serrure : un travail rejoue, un appel direct a la RPC, une version du
-- front en cache, et le geste passe. La RPC est la SEULE porte par ou le geste
-- entre -- c'est donc ici que le refus doit vivre.
--
-- ─── CE QUE CA EMPECHE, ET POURQUOI C'EST GRAVE ───
-- Une offre acceptee, un compromis signe derriere, puis l'offre passee en REFUS :
-- son etat FINAL devient « refusee », et la regle de chainage -- qui lit l'etat
-- final -- ne voit plus d'offre acceptee. Le compromis se retrouve orphelin et
-- part dans son propre dossier. L'affaire est coupee en deux.
-- MESURE DU 16/09 : c'est arrive QUATRE fois (annonces 1970, 23353, 40519, 61599).
--
-- ─── L'ARBITRAGE, TRANCHE PAR FREDERIC LE 16/09 ───
-- On verrouille sur le COMPROMIS OUVERT, pas sur la simple acceptation de
-- l'offre. Revenir sur une offre acceptee tant que rien n'est signe est un geste
-- legitime et frequent (l'acquereur se retracte) : le bloquer enfermerait le
-- negociateur, qui devrait rouvrir Hektor -- exactement ce que l'etape 2 veut
-- eviter.
--
-- ─── LA PORTE DE SORTIE EST GARDEE OUVERTE ───
-- On ne bloque QUE l'offre. « Annuler le compromis » et « Supprimer le
-- compromis » restent disponibles : c'est par la qu'on libere le dossier, et
-- l'offre redevient alors modifiable. L'ordre est impose, rien n'est interdit.
--
-- ⚠ UNE AFFAIRE SANS DOSSIER N'EST PAS VERROUILLEE. Une transaction nee dans
--   l'app porte app_chaine_id NULL jusqu'a ce que le run l'adopte : sans dossier,
--   il n'y a rien a proteger, et refuser serait bloquer une offre toute neuve.
-- ⚠ CE QUE HEKTOR A EFFACE NE VERROUILLE RIEN -- meme clause que le chainage
--   depuis le 07/09 : un compromis supprime chez eux ne doit pas tenir une offre
--   en otage. Sans cela, le bien resterait bloque POUR TOUJOURS.
--
-- EMPREINTE MESUREE LE 16/09 : 131 dossiers portent un compromis vivant sans
-- vente ; 103 offres vivantes y seraient verrouillees.
--
-- RETOUR ARRIERE : rejouer ce fichier en retirant le bloc marque « 16/09 ».
-- Le corps de la fonction n'est modifie NULLE PART AILLEURS -- il est recopie
-- ici depuis pg_get_functiondef(), pas depuis une note.
-- ⚠ CREATE OR REPLACE, MEME SIGNATURE : les GRANT survivent. C'est la lecon du
--   piege des RPC (un DROP les effacerait, et ils ne sont pas uniformes).
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.app_geste_affaire_optimistic(target_affaire_id bigint, geste text, job_priority integer DEFAULT 7)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  a             app_affaire_ledger%rowtype;
  d             app_dossier_current%rowtype;
  etat_avant    text;
  etat_apres    text;
  type_job      text;
  charge        jsonb;
  nouveau_id    uuid;
  statut_avant  text;
  statut_apres  text;
  -- 16/09 : ce qui verrouille l'offre, s'il existe.
  bloc_kind     text;
  bloc_id       text;
BEGIN
  SELECT * INTO a FROM app_affaire_ledger WHERE app_affaire_id = target_affaire_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'affaire_not_found' USING errcode = '22023'; END IF;

  IF NOT public.is_app_admin() THEN
    RAISE EXCEPTION 'not_allowed' USING errcode = '42501';
  END IF;
  IF NOT public.app_console_can_access_dossier(a.app_dossier_id, a.hektor_annonce_id::text) THEN
    RAISE EXCEPTION 'dossier_not_allowed' USING errcode = '42501';
  END IF;

  -- Le geste doit correspondre au type de l'affaire : on ne refuse pas une vente,
  -- on ne supprime pas une offre. Le controle est ici, pas dans l'ecran.
  IF geste = 'refus' AND a.kind = 'offre' THEN
    type_job := 'change_hektor_offre_status'; etat_apres := 'refused';
  ELSIF geste = 'accepte' AND a.kind = 'offre' THEN
    type_job := 'change_hektor_offre_status'; etat_apres := 'accepted';
  ELSIF geste = 'annuler' AND a.kind = 'compromis' THEN
    type_job := 'cancel_hektor_compromis'; etat_apres := 'cancelled';
  -- ─── 3.4 (07/09/2026) : SUPPRIMER UN COMPROMIS ───
  -- Le verbe manquait. « Annuler » et « supprimer » ne sont PAS le meme geste --
  -- mesure du 04/09 : annuler laisse le compromis, marque mort, et le statut ne
  -- bouge pas ; supprimer le fait disparaitre, et le statut redescend.
  -- ⚠ LA ROUTE A ETE RELEVEE EN CONDITIONS REELLES le 07/09, en instrumentant la
  --   fiche de Hektor : mode=annonce-SuiviVente-deleteCompromis, parametres
  --   idCompromis ET idAnn. Ce N'EST PAS le verbe de la vente -- eprouve,
  --   ventes-deleteVente sur un compromis ne fait rien.
  ELSIF geste = 'supprimer' AND a.kind = 'compromis' THEN
    type_job := 'delete_hektor_compromis'; etat_apres := NULL;
  ELSIF geste = 'supprimer' AND a.kind = 'vente' THEN
    type_job := 'delete_hektor_vente'; etat_apres := NULL;
  ELSE
    RAISE EXCEPTION 'geste_incompatible: % sur %', geste, a.kind USING errcode = '22023';
  END IF;

  -- ⛔ ─── 16/09/2026 : L'OFFRE EST VERROUILLEE PAR SON COMPROMIS ─── ⛔
  -- Voir l'en-tete de ce fichier. On ne lit QUE le dossier de CETTE offre : une
  -- offre d'un autre acquereur, dans un autre dossier du meme bien, reste libre
  -- -- refuser les offres ecartees quand une autre est retenue est le geste
  -- normal du metier, et rien ne le casse.
  IF a.kind = 'offre' AND geste IN ('refus', 'accepte') AND a.app_chaine_id IS NOT NULL THEN
    SELECT l.kind, l.hektor_affaire_id::text INTO bloc_kind, bloc_id
      FROM app_affaire_ledger l
     WHERE l.app_chaine_id = a.app_chaine_id
       AND l.app_affaire_id <> a.app_affaire_id
       AND NOT (btrim(coalesce(l.hektor_affaire_id::text, '')) <> ''
                AND l.present_in_hektor IS FALSE)
       AND ( l.kind = 'vente'
          OR (l.kind = 'compromis'
              AND lower(coalesce(l.state, '')) NOT IN ('cancelled', 'annule')) )
     ORDER BY CASE l.kind WHEN 'vente' THEN 0 ELSE 1 END
     LIMIT 1;
    IF bloc_kind IS NOT NULL THEN
      RAISE EXCEPTION 'offre_verrouillee: ce dossier porte % (n° %). Levez-le avant de revenir sur l''offre.',
        CASE bloc_kind WHEN 'vente' THEN 'une vente' ELSE 'un compromis en cours' END,
        coalesce(nullif(btrim(bloc_id), ''), '?')
        USING errcode = '22023';
    END IF;
  END IF;

  -- Une transaction DEJA dans cet etat : on ne renvoie pas de travail pour rien.
  IF etat_apres IS NOT NULL AND coalesce(a.state, '') = etat_apres THEN
    RETURN jsonb_build_object('ok', true, 'deja_dans_cet_etat', true,
                              'app_affaire_id', target_affaire_id, 'state', a.state);
  END IF;

  etat_avant := a.state;
  SELECT * INTO d FROM app_dossier_current WHERE app_dossier_id = a.app_dossier_id;

  -- 1. l'etat est pose CHEZ NOUS tout de suite -- c'est l'instantane
  IF geste = 'supprimer' THEN
    UPDATE app_affaire_ledger SET present_in_hektor = false
     WHERE app_affaire_id = target_affaire_id;
  ELSE
    UPDATE app_affaire_ledger SET state = etat_apres
     WHERE app_affaire_id = target_affaire_id;
  END IF;

  -- 1bis. LA REDESCENTE, sur le ledger qu'on vient d'ecrire.
  -- ⬇ 'refus' RETIRE le 02/09 (cycle 1), 'annuler' RETIRE le 02/09 (cycle 3.2).
  --   Il ne reste que 'supprimer'.
  -- ✅ ET ELLE EST MESUREE DEPUIS LE 07/09, pour le compromis : en supprimant
  --   depuis LEUR interface, un SECOND appel part aussitot --
  --   POST mode=ajoutebien_wizardBien avec statutAnnonce et idann. Hektor ne
  --   redescend donc PAS tout seul : c'est un geste, et le worker devra le faire.
  IF geste = 'supprimer' AND d.app_dossier_id IS NOT NULL THEN
    statut_avant := d.statut_annonce;
    statut_apres := public.app_statut_redescente_calcule(a.app_dossier_id);

    -- BORNE 2 + hors echelle : on ne bouge que vers le BAS, et seulement depuis
    -- un barreau de l'echelle vers un autre barreau de l'echelle.
    IF public.app_statut_rang(statut_avant) IS NULL
       OR public.app_statut_rang(statut_apres) IS NULL
       OR public.app_statut_rang(statut_apres) >= public.app_statut_rang(statut_avant) THEN
      statut_apres := NULL;
    END IF;

    IF statut_apres IS NOT NULL THEN
      -- VISIBLE tout de suite. On ne touche NI diffusable NI archive (borne 3).
      UPDATE app_dossier_current
         SET statut_annonce = statut_apres
       WHERE app_dossier_id = a.app_dossier_id;

      -- SURVIT a la coupure. Dormant tant que la liste des champs app est vide.
      INSERT INTO app_annonce_champ_app (app_dossier_id, champ, valeur_app, origine, ecrit_le, ecrit_par)
      VALUES (a.app_dossier_id, 'statut', statut_apres, 'redescente_transaction', now(), coalesce(auth.uid()::text, 'app'))
      ON CONFLICT (app_dossier_id, champ) DO UPDATE
        SET valeur_app = excluded.valeur_app,
            origine    = excluded.origine,
            ecrit_le   = excluded.ecrit_le,
            ecrit_par  = excluded.ecrit_par;
    ELSE
      statut_avant := NULL;   -- rien n'a bouge : rien a restaurer
    END IF;
  END IF;

  -- 2. le travail EMPORTE l'etat precedent, pour que le worker sache quoi restaurer
  charge := jsonb_build_object(
    'hektor_annonce_id', a.hektor_annonce_id,
    'numero_dossier',    d.numero_dossier,
    'titre_bien',        d.titre_bien,
    'app_affaire_id',    target_affaire_id,
    'etat_avant',        etat_avant,
    'geste',             geste
  );
  IF statut_avant IS NOT NULL THEN
    charge := charge || jsonb_build_object('statut_avant', statut_avant,
                                           'statut_apres', statut_apres);
  END IF;
  IF type_job = 'change_hektor_offre_status' THEN
    charge := charge || jsonb_build_object('hektor_offre_id', a.hektor_affaire_id::text,
                                           'type', geste);
  ELSIF type_job = 'cancel_hektor_compromis' THEN
    charge := charge || jsonb_build_object('hektor_compromis_id', a.hektor_affaire_id::text);
  ELSIF type_job = 'delete_hektor_compromis' THEN
    -- ⚠ `confirmer` EST EXIGE, comme pour la vente : le geste est IRREVERSIBLE.
    charge := charge || jsonb_build_object('hektor_compromis_id', a.hektor_affaire_id::text,
                                           'confirmer', true);
  ELSE
    charge := charge || jsonb_build_object('hektor_vente_id', a.hektor_affaire_id::text,
                                           'confirmer', true);
  END IF;

  INSERT INTO app_console_job (job_type, app_dossier_id, hektor_annonce_id, payload_json,
                               priority, status, requested_by)
  VALUES (type_job, a.app_dossier_id, a.hektor_annonce_id::text, charge,
          coalesce(job_priority, 7), 'pending', auth.uid())
  RETURNING id INTO nouveau_id;

  RETURN jsonb_build_object(
    'ok', true,
    'job_id', nouveau_id,
    'app_affaire_id', target_affaire_id,
    'kind', a.kind,
    'etat_avant', etat_avant,
    'etat_apres', etat_apres,
    'statut_avant', statut_avant,
    'statut_apres', statut_apres,
    'job_type', type_job
  );
END
$function$;
