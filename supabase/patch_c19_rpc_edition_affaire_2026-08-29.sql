-- =====================================================================
-- C.19 (etape 3) -- LA PORTE D'ECRITURE DES CHAMPS D'AFFAIRE
-- Date : 2026-08-29
--
-- POURQUOI UNE RPC ET PAS UNE ECRITURE DIRECTE
-- --------------------------------------------
-- app_affaire_champ_app a sa RLS fermee : seul service_role la traverse. Le front
-- est `authenticated`. Une RPC SECURITY DEFINER est donc la seule porte -- et
-- c'est exactement le patron deja en place pour les annonces
-- (app_edit_annonce_optimistic) et les contacts (app_edit_contact_optimistic).
--
-- CE QU'ELLE FAIT, ET SURTOUT CE QU'ELLE NE FAIT PAS
-- --------------------------------------------------
-- Elle range la valeur chez nous. Elle ne cree AUCUN travail worker, elle
-- n'appelle PAS Hektor. C'est la demande de Frederic (28/08) : les VALEURS
-- restent chez nous, seuls les CHANGEMENTS D'ETAT partent (refuser/accepter une
-- offre, annuler un compromis, supprimer une vente -- etape 4).
--
-- DEUX ECRITURES, ET ELLES N'ONT PAS LE MEME ROLE :
--   1. app_affaire_champ_app  -- CE QUI FAIT FOI. Jamais reconstruit. C'est lui
--      que le run de nuit relira pour reposer la valeur apres la reconstruction.
--   2. app_affaire_ledger     -- le CONFORT : l'ecran voit sa correction tout de
--      suite, sans attendre 05:30. Cette copie sera ecrasee par le prochain
--      rafraichissement depuis le miroir, puis REPOSEE par le contrat. Aller-retour
--      normal, deja eprouve le 29/08.
--
-- VIDER UN CHAMP = RENDRE LA MAIN A HEKTOR. On retire la ligne du magasin ; le
-- prochain rafraichissement du ledger remet la valeur de Hektor. C'est la regle
-- « l'app gagne seulement quand elle a quelque chose a dire ».
--
-- LES CHAMPS ACCEPTES sont ceux du contrat d'autorite (phase2/identite/
-- contrat_autorite.py, CHAMPS_APP_AFFAIRE). Tout autre nom est IGNORE en silence
-- plutot que refuse : un champ qu'on ajoutera demain ne doit pas casser l'ecran
-- d'aujourd'hui. Le compte rendu dit combien ont ete retenus.
--
-- LE DROIT : meme porte que la modale de statut, qui est reservee aux admins
-- (App.tsx, openStatusChangeModal : `if (!isAdmin) return`). Plus le controle
-- d'acces au dossier deja utilise par les autres RPC.
--
-- RETOUR ARRIERE : DROP FUNCTION public.app_edit_affaire_optimistic.
-- =====================================================================

CREATE OR REPLACE FUNCTION public.app_edit_affaire_optimistic(
    target_affaire_id bigint,
    edit_fields       jsonb
) RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $function$
DECLARE
  a          app_affaire_ledger%rowtype;
  champs_ok  text[] := ARRAY['montant', 'date', 'date_acte', 'sequestre'];
  k          text;
  v          text;
  retenus    int := 0;
  ignores    int := 0;
BEGIN
  SELECT * INTO a FROM app_affaire_ledger WHERE app_affaire_id = target_affaire_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'affaire_not_found' USING errcode = '22023';
  END IF;

  IF NOT public.is_app_admin() THEN
    RAISE EXCEPTION 'not_allowed' USING errcode = '42501';
  END IF;

  IF NOT public.app_console_can_access_dossier(a.app_dossier_id, a.hektor_annonce_id::text) THEN
    RAISE EXCEPTION 'dossier_not_allowed' USING errcode = '42501';
  END IF;

  FOR k IN SELECT jsonb_object_keys(edit_fields) LOOP
    IF NOT (k = ANY (champs_ok)) THEN
      ignores := ignores + 1;
      CONTINUE;
    END IF;

    v := nullif(btrim(coalesce(edit_fields ->> k, '')), '');

    IF v IS NULL THEN
      -- vider = rendre la main a Hektor
      DELETE FROM app_affaire_champ_app
       WHERE app_affaire_id = target_affaire_id AND champ = k;
    ELSE
      INSERT INTO app_affaire_champ_app (app_affaire_id, champ, valeur_app, origine, ecrit_par)
      VALUES (target_affaire_id, k, v, 'saisie_app', coalesce(auth.uid()::text, 'inconnu'))
      ON CONFLICT (app_affaire_id, champ) DO UPDATE
        SET valeur_app = excluded.valeur_app,
            origine    = excluded.origine,
            ecrit_par  = excluded.ecrit_par,
            ecrit_le   = now();

      -- confort : l'ecran voit sa correction tout de suite
      IF k = 'montant'   THEN UPDATE app_affaire_ledger SET montant   = v WHERE app_affaire_id = target_affaire_id; END IF;
      IF k = 'date'      THEN UPDATE app_affaire_ledger SET date      = v WHERE app_affaire_id = target_affaire_id; END IF;
      IF k = 'date_acte' THEN UPDATE app_affaire_ledger SET date_acte = v WHERE app_affaire_id = target_affaire_id; END IF;
      IF k = 'sequestre' THEN UPDATE app_affaire_ledger SET sequestre = v WHERE app_affaire_id = target_affaire_id; END IF;
    END IF;

    retenus := retenus + 1;
  END LOOP;

  RETURN jsonb_build_object(
    'ok', true,
    'app_affaire_id', target_affaire_id,
    'kind', a.kind,
    'champs_retenus', retenus,
    'champs_ignores', ignores,
    'hektor_informe', false
  );
END
$function$;

COMMENT ON FUNCTION public.app_edit_affaire_optimistic(bigint, jsonb) IS
    'Range une correction de transaction CHEZ NOUS. N''appelle jamais Hektor : lui '
    'n''apprend que les changements d''etat. Vider un champ rend la main a Hektor.';

REVOKE ALL ON FUNCTION public.app_edit_affaire_optimistic(bigint, jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.app_edit_affaire_optimistic(bigint, jsonb) TO authenticated, service_role;
