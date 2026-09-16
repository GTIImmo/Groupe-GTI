-- ═══════════════════════════════════════════════════════════════════════════
-- LES CONDITIONS SUSPENSIVES APPARTIENNENT A L'APP              16/09/2026
-- Chantier C.19-d, tache 3.2d lot 3 (2e morceau).
-- ═══════════════════════════════════════════════════════════════════════════
--
-- DECISION DE FREDERIC, 16/09 : « les conditions suspensives doivent etre comme
-- d'autres champs dans la modale mais uniquement conservees dans l'app, rien
-- envoye a Hektor ».
--
-- ⚠ ET C'EST CE QUI DEBLOQUE LE LOT 3. Tant qu'on voulait les ECRIRE chez
--   Hektor, il fallait d'abord savoir ce qu'il porte -- sinon la modale les
--   ecrasait a l'aveugle. Or la console n'en a capte AUCUNE : 0 sur 18 442
--   lectures, parce qu'elles vivent sur une TROISIEME page de l'assistant que
--   l'entretien n'ouvre pas. Les lire aurait coute +50 % de flux console.
--   Ne rien envoyer supprime la question : il n'y a plus rien a ne pas ecraser.
--
-- ⚠ LA CONTREPARTIE, DITE UNE FOIS. Tant que les negociateurs saisissent dans
--   Hektor, une condition posee la-bas ne remontera pas ici, et une condition
--   posee ici ne figurera pas dans leur document. C'est le meme choix que pour
--   la repartition -- avec une difference qu'il faut nommer : leur modele ne
--   SAVAIT PAS exprimer la repartition, alors qu'il sait porter une condition.
--   Ici on choisit de ne pas la lui envoyer. C'est une decision, pas un constat.
--
-- ⭐ ET CA REND VRAI CE QUE L'ECRAN PROMET DEJA. Le cockpit affiche « Suivez les
--   conditions suspensives jusqu'a l'acte » -- et il n'y a RIEN derriere :
--   aucune table, ni en local ni en ligne. Verifie le 16/09.
--
-- LE SENS DU FLUX, ET IL EST L'INVERSE DES NOTAIRES
-- -------------------------------------------------
--   une donnee LUE chez Hektor      -> le serveur d'abord, puis l'app
--                                      (notaires, taux vendeur : 16/09)
--   une donnee TAPEE par un humain  -> l'app d'abord, puis le serveur
--                                      (ici, comme la repartition)
--   Le maitre est celui qui ECRIT. Le serveur en recoit copie par la descente,
--   pour que la sauvegarde de nuit l'emporte.
--
-- POURQUOI ATTACHEE A LA TRANSACTION, ET PAS AU DOSSIER
-- -----------------------------------------------------
-- Contrairement a la repartition (une decision qui vaut pour toute la chaine),
-- une condition suspensive est une CLAUSE DU COMPROMIS : elle nait avec lui et
-- se leve avant l'acte. Un compromis annule puis resigne n'a pas les memes.
-- C'est aussi la forme de Hektor. On la rattache donc a `app_affaire_id`.
-- ═══════════════════════════════════════════════════════════════════════════

-- ─── LE CATALOGUE DE L'AGENCE ───
--
-- Hektor en proposait un a l'ecran ; le jour de la coupure il disparait. On le
-- reprend donc chez nous. ⚠ LA CONSOLE N'EN A CAPTE QU'UN SEUL sur 18 442
-- lectures (meme raison : la troisieme page). Ses deux entrees sont reprises
-- ci-dessous a l'identique, y compris leurs identifiants, pour qu'une reprise
-- ulterieure les reconnaisse.
CREATE TABLE IF NOT EXISTS public.app_condition_catalogue (
    id            text PRIMARY KEY,
    libelle       text NOT NULL,
    -- Le delai propose par defaut, en jours. 0 = pas de delai (ex. la preemption).
    jours_defaut  integer,
    actif         boolean NOT NULL DEFAULT true,
    rang          integer NOT NULL DEFAULT 0,
    ecrit_le      timestamptz NOT NULL DEFAULT now(),
    ecrit_par     text
);

INSERT INTO public.app_condition_catalogue (id, libelle, jours_defaut, rang)
VALUES ('1', 'Préemption mairie', 0, 1),
       ('2', 'Obtention Crédit', 45, 2)
ON CONFLICT (id) DO NOTHING;

-- ─── LES CONDITIONS D'UNE TRANSACTION ───
CREATE TABLE IF NOT EXISTS public.app_affaire_condition (
    app_affaire_id  bigint  NOT NULL,
    -- L'ordre d'affichage, et la moitie de la cle. Renumerote a chaque
    -- enregistrement : la modale envoie la liste ENTIERE, jamais un fragment.
    rang            integer NOT NULL,
    libelle         text    NOT NULL,
    -- Le delai en jours depuis la signature. L'echeance est CALCULEE a partir de
    -- la date du compromis -- on ne la fige pas : si la date du compromis bouge,
    -- l'echeance doit suivre. Mais on accepte aussi une date posee a la main,
    -- qui gagne alors (« mieux vaut ce qu'un humain affirme »).
    jours           integer,
    date_echeance   date,
    -- attente : elle court · levee : obtenue · non_levee : elle a fait tomber le
    -- compromis · sans_objet : retiree d'un commun accord.
    etat            text    NOT NULL DEFAULT 'attente',
    date_levee      date,
    note            text,
    -- D'ou vient le libelle, quand il vient du catalogue. NULL = texte libre.
    catalogue_id    text,
    -- Recopies pour que le suivi par bien et par dossier soit immediat.
    app_dossier_id  bigint,
    app_chaine_id   bigint,
    -- 'saisie' aujourd'hui, toujours. La colonne existe pour le jour ou une
    -- lecture console viendrait en poser : on saura alors distinguer les deux,
    -- et une saisie humaine ne sera pas ecrasee.
    origine         text    NOT NULL DEFAULT 'saisie',
    ecrit_le        timestamptz NOT NULL DEFAULT now(),
    ecrit_par       text,
    CONSTRAINT app_affaire_condition_pkey PRIMARY KEY (app_affaire_id, rang),
    CONSTRAINT app_affaire_condition_etat_chk
        CHECK (etat IN ('attente', 'levee', 'non_levee', 'sans_objet')),
    CONSTRAINT app_affaire_condition_rang_chk CHECK (rang >= 1 AND rang <= 30)
);

-- Le suivi se lit PAR BIEN (« ou en sont mes conditions ? ») et PAR ECHEANCE
-- (« lesquelles arrivent a terme ? »). Deux index, pas un de plus.
CREATE INDEX IF NOT EXISTS app_affaire_condition_dossier_idx
    ON public.app_affaire_condition (app_dossier_id);
CREATE INDEX IF NOT EXISTS app_affaire_condition_echeance_idx
    ON public.app_affaire_condition (date_echeance)
    WHERE etat = 'attente';

COMMENT ON TABLE public.app_affaire_condition IS
    'LES CONDITIONS SUSPENSIVES D''UN COMPROMIS. Donnee PROPRE A L''APP : elle ne '
    'part JAMAIS chez Hektor (decision de Frederic, 16/09/2026). Rattachee a la '
    'TRANSACTION et non au dossier : une condition est une clause du compromis, '
    'elle nait avec lui et se leve avant l''acte.';

-- ═══ L'ECRITURE PASSE PAR UNE FONCTION, COMME LA REPARTITION ═══
--
-- ⚠ ELLE REMPLACE LA LISTE ENTIERE d'une transaction. La modale envoie toujours
--   tout : une liste arrivee a moitie perdrait l'autre moitie, et c'est
--   exactement le defaut que la RPC de repartition evite en refusant de couper
--   un dossier en deux paquets.
CREATE OR REPLACE FUNCTION public.app_conditions_affaire_ecrire(
    target_affaire_id bigint, conditions jsonb)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $function$
DECLARE
  a        app_affaire_ledger%rowtype;
  element  jsonb;
  n        integer := 0;
  rang_    integer := 0;
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

  DELETE FROM app_affaire_condition WHERE app_affaire_id = target_affaire_id;

  FOR element IN SELECT * FROM jsonb_array_elements(coalesce(conditions, '[]'::jsonb))
  LOOP
    -- Une ligne sans libelle n'est pas une condition : on la passe, sans bruit.
    CONTINUE WHEN coalesce(btrim(element->>'libelle'), '') = '';
    rang_ := rang_ + 1;
    EXIT WHEN rang_ > 30;
    INSERT INTO app_affaire_condition (
        app_affaire_id, rang, libelle, jours, date_echeance, etat, date_levee,
        note, catalogue_id, app_dossier_id, app_chaine_id, origine, ecrit_par)
    VALUES (
        target_affaire_id, rang_, btrim(element->>'libelle'),
        nullif(element->>'jours', '')::integer,
        nullif(element->>'date_echeance', '')::date,
        coalesce(nullif(element->>'etat', ''), 'attente'),
        nullif(element->>'date_levee', '')::date,
        nullif(btrim(coalesce(element->>'note', '')), ''),
        nullif(element->>'catalogue_id', ''),
        a.app_dossier_id, a.app_chaine_id, 'saisie',
        coalesce(auth.uid()::text, 'app'));
    n := n + 1;
  END LOOP;

  RETURN jsonb_build_object('ok', true, 'app_affaire_id', target_affaire_id,
                            'lignes', n);
END
$function$;

ALTER TABLE public.app_affaire_condition ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.app_condition_catalogue ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies
                  WHERE schemaname = 'public' AND tablename = 'app_affaire_condition'
                    AND policyname = 'app_affaire_condition_read') THEN
    CREATE POLICY app_affaire_condition_read ON public.app_affaire_condition
      FOR SELECT TO authenticated USING (true);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies
                  WHERE schemaname = 'public' AND tablename = 'app_condition_catalogue'
                    AND policyname = 'app_condition_catalogue_read') THEN
    CREATE POLICY app_condition_catalogue_read ON public.app_condition_catalogue
      FOR SELECT TO authenticated USING (true);
  END IF;
END
$$;

-- ⚠ AUCUN DROIT D'ECRITURE DIRECT POUR `authenticated`. On lit la table, on
--   ecrit par la fonction -- qui verifie le role ET le perimetre du dossier.
GRANT ALL    ON TABLE public.app_affaire_condition   TO service_role;
GRANT SELECT ON TABLE public.app_affaire_condition   TO authenticated;
GRANT ALL    ON TABLE public.app_condition_catalogue TO service_role;
GRANT SELECT ON TABLE public.app_condition_catalogue TO authenticated;

REVOKE EXECUTE ON FUNCTION public.app_conditions_affaire_ecrire(bigint, jsonb) FROM anon;
GRANT  EXECUTE ON FUNCTION public.app_conditions_affaire_ecrire(bigint, jsonb)
       TO authenticated, service_role;
