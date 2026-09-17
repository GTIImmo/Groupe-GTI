-- ═══════════════════════════════════════════════════════════════════════════════
-- LA NOTE D'UNE TRANSACTION -- DONNEE DE L'APP, SUR LES TROIS GENRES  17/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Copie versionnee de la migration `note_affaire`.
--
-- ─── POURQUOI ───
-- Hektor porte un `notesCompromis` : un texte libre sur le compromis. Tant qu'il
-- n'existe que la-bas, un negociateur doit ouvrir Hektor pour l'ecrire -- et c'est
-- exactement une raison d'ouvrir Hektor de moins a trouver (etape 2).
--
-- ─── LES DEUX ARBITRAGES DE FREDERIC, 16-17/09 ───
--     PAR TRANSACTION, pas par dossier. Une note ecrite sur le compromis reste
--         sur le compromis : elle ne suit pas sur la vente. C'est le comportement
--         de Hektor, et c'est le plus previsible.
--     ON N'IMPORTE RIEN. L'app part d'une page blanche. Les notes qui vivent
--         aujourd'hui dans Hektor y restent et s'eteindront a la coupure.
--         ⚠ C'EST LE PRIX ASSUME d'un defaut bien pire : deux jeux de notes dont
--           personne ne saurait lequel fait foi.
--     SUR LES TROIS GENRES (17/09). Une condition suspensive est une clause du
--         compromis par nature -- une note libre ne l'est pas. Offre, compromis
--         et vente en portent une.
--
-- ⚠ RIEN NE PART CHEZ HEKTOR, comme les conditions suspensives de la veille.
--   Consequence a connaitre : la note n'apparaitra pas sur le document que Hektor
--   imprime. Elle sert l'usage OPERATIONNEL (qui relancer, quand, quel dossier
--   bancaire), pas l'usage contractuel.
--
-- ─── OU ELLE EST RANGEE, ET POURQUOI PAS AILLEURS ───
--   PAS DANS LE REGISTRE (`app_affaire_ledger`) : il est refait chaque nuit
--     depuis le miroir. Une saisie rangee la serait ecrasee au premier run.
--   PAS DANS LE CARNET (`app_affaire_champ_app`) : le carnet sert aux champs qui
--     PARTENT chez Hektor, avec leur photo et leur verdict « arrivee / en attente
--     / conflit ». Une note qui ne part jamais y porterait un verdict
--     « inconnu » pour l'eternite -- et 4.1 prevoit justement de le retirer.
--   DONC UNE TABLE A ELLE, que le run ne touche jamais, ni en lecture ni en
--     ecriture. C'est tout l'interet.
--
-- ⚠ AUCUNE CLE ETRANGERE VERS LE REGISTRE, ET C'EST DELIBERE -- `app_affaire_
--   condition` et `app_affaire_champ_app` n'en ont pas non plus (verifie le
--   17/09). Le registre est reecrit chaque nuit et son push SAIT supprimer des
--   lignes : une cascade effacerait silencieusement la saisie d'un humain. La
--   regle du projet est « une saisie ne se perd jamais » ; une contrainte qui la
--   detruirait au menage est exactement ce qu'il ne faut pas.
--
-- RETOUR ARRIERE :
--     DROP FUNCTION public.app_affaire_note_ecrire(bigint, text);
--     DROP TABLE public.app_affaire_note;
--   Plus le bloc d'ecran. Rien d'autre ne lit cette table -- ni le run, ni le
--   worker, ni la descente.
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.app_affaire_note (
    -- UNE note par transaction : la cle primaire le dit, il n'y a pas de liste
    -- donc pas de rang, et pas de remplacement de liste a orchestrer.
    app_affaire_id  bigint PRIMARY KEY,
    texte           text NOT NULL,
    -- Recopies de l'affaire au moment de l'ecriture, comme le fait
    -- app_affaire_condition. Ils ne servent a rien aujourd'hui ; ils permettront
    -- de lire a l'echelle du dossier ou de la chaine SANS changer la cle.
    app_dossier_id  bigint,
    app_chaine_id   bigint,
    -- Tout y sera 'saisie' tant qu'on n'importe rien. La colonne existe pour le
    -- jour ou une note arriverait de Hektor : sans elle, une note IMPORTEE serait
    -- indiscernable d'une note ECRITE. Meme principe que `mandat_origine` et que
    -- le verdict du carnet -- on separe toujours ce qu'on sait de ce qu'on infere.
    origine         text NOT NULL DEFAULT 'saisie',
    ecrit_le        timestamptz NOT NULL DEFAULT now(),
    ecrit_par       text
);

COMMENT ON TABLE public.app_affaire_note IS
    'LA NOTE LIBRE D''UNE TRANSACTION (offre, compromis ou vente). Donnee PROPRE '
    'A L''APP : elle ne part JAMAIS chez Hektor (decision de Frederic, 16/09/2026) '
    'et le run de nuit ne la touche jamais. Rattachee a la TRANSACTION et non au '
    'dossier : une note ecrite sur le compromis ne suit pas sur la vente.';

ALTER TABLE public.app_affaire_note ENABLE ROW LEVEL SECURITY;

-- Lecture pour tout compte connecte, ecriture par la fonction seule -- copie
-- conforme de `app_affaire_condition_read`.
DROP POLICY IF EXISTS app_affaire_note_read ON public.app_affaire_note;
CREATE POLICY app_affaire_note_read ON public.app_affaire_note
    FOR SELECT TO authenticated USING (true);

-- ═══ L'ECRITURE PASSE PAR UNE FONCTION, COMME LES CONDITIONS ═══
--
-- ⚠ LES TROIS MEMES GARDES que `app_conditions_affaire_ecrire`, dans le meme
--   ordre : l'affaire existe, l'appelant est admin, et il a le droit sur CE
--   dossier. Les recopier plutot que les resumer, c'est ce qui evite qu'une
--   table nouvelle soit la porte ouverte du lot.
-- ⚠ UN TEXTE VIDE SUPPRIME LA LIGNE. Une note vide n'est pas une note : la
--   garder laisserait une ligne fantome que rien ne distingue d'un oubli.
CREATE OR REPLACE FUNCTION public.app_affaire_note_ecrire(
    target_affaire_id bigint, texte text)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $function$
DECLARE
  a      app_affaire_ledger%rowtype;
  propre text;
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

  propre := nullif(btrim(coalesce(texte, '')), '');

  IF propre IS NULL THEN
    DELETE FROM app_affaire_note WHERE app_affaire_id = target_affaire_id;
    RETURN jsonb_build_object('ok', true, 'app_affaire_id', target_affaire_id,
                              'vide', true);
  END IF;

  -- ⚠ Une note tres longue n'est pas un probleme de place mais de lisibilite a
  --   l'ecran. 4 000 caracteres = large pour une note de suivi, et borne.
  IF length(propre) > 4000 THEN
    propre := left(propre, 4000);
  END IF;

  INSERT INTO app_affaire_note (
      app_affaire_id, texte, app_dossier_id, app_chaine_id, origine,
      ecrit_le, ecrit_par)
  VALUES (
      target_affaire_id, propre, a.app_dossier_id, a.app_chaine_id, 'saisie',
      now(), coalesce(auth.uid()::text, 'app'))
  ON CONFLICT (app_affaire_id) DO UPDATE SET
      texte          = excluded.texte,
      app_dossier_id = excluded.app_dossier_id,
      app_chaine_id  = excluded.app_chaine_id,
      origine        = 'saisie',
      ecrit_le       = now(),
      ecrit_par      = excluded.ecrit_par;

  RETURN jsonb_build_object('ok', true, 'app_affaire_id', target_affaire_id,
                            'longueur', length(propre));
END
$function$;

COMMENT ON FUNCTION public.app_affaire_note_ecrire(bigint, text) IS
    'Ecrit (ou efface, si le texte est vide) la note libre d''une transaction. '
    'Memes gardes que app_conditions_affaire_ecrire. N''envoie RIEN chez Hektor.';
