-- =====================================================================
-- MASQUER LES 54 COQUILLES D'OFFRE AU REGISTRE          02/11/2026
-- =====================================================================
--
-- DECIDE PAR FREDERIC le 02/11 : « masque les 54 coquilles ».
--
-- CE QU'EST UNE COQUILLE, et c'est MESURE, pas suppose (audit
-- notice/AUDIT_DATES_0000_COMPROMIS_ET_OFFRES_2026-11-02.md) :
--   une offre dont la liste des PROPOSITIONS est vide. Chez Hektor le montant,
--   le statut et la date d'une offre vivent DANS les propositions -- donc
--   « sans date », « sans montant » et « sans statut » sont UN SEUL FAIT dit
--   trois fois. Contraste : 0 des 11 131 autres offres est dans ce cas.
--   * L'API l'a confirme le 02/11 a 13:29 : /Api/Offre/OffreById/ rend
--     trouve=true mais 0 proposition. Hektor n'en sait pas plus que sa liste,
--     avec DEUX TEMOINS POSITIFS pour prouver que la route repond.
--
-- /!\ CE QU'ON NE MASQUE SURTOUT PAS : LES 14 OFFRES A « 0000-00-00 ».
--   Elles n'ont pas de date non plus, mais ce sont de VRAIES offres : 2
--   propositions typees chacune, un montant de 65 000 a 328 000 EUR, 6
--   acceptees. Le predicat ci-dessous les garde DELIBEREMENT -- il regarde les
--   PROPOSITIONS, pas la date. Temoin inverse dans le controle final.
--
-- POURQUOI UN FILTRE D'AFFICHAGE, ET PAS UNE SUPPRESSION :
--   . elles EXISTENT chez Hektor -- les ranger dans app_affaire_supprimee
--     (« efface chez Hektor ») serait un mensonge ;
--   . rien d'humain n'y est attache (0 note, 0 condition, 0 champ saisi,
--     0 decision de carnet -- mesure du 02/11), MAIS il y a 54 parties, 40
--     relations de contact et /!\ 1 LIEN DE CLASSEUR (ligne 3847, « a valider »,
--     pose par apparier_classeur.py le 29/10). Un filtre ne casse rien de tout
--     cela ; une suppression les aurait casses ;
--   . et aucune donnee n'est touchee : le retour arriere est une fonction a
--     remettre, pas une restauration.
--
-- CE QUE CE PATCH FAIT, ET CE QU'IL NE FAIT PAS :
--   [FAIT]    la LISTE du registre (app_registre_dossiers) ne les montre plus.
--             7 dossiers disparaissent : ceux qui ne contenaient QUE des
--             coquilles. Les 42 autres gardent leur place et perdent juste la
--             ligne fantome. Mesure : 12 117 -> 12 110 dossiers, 31 107 ->
--             31 053 lignes.
--   [A FAIRE] LES DEUX FICHES passent par apps/hektor-v1/src/lib/api.ts
--             (loadDossierDeLaChaine et loadAffairesForDossier), QUE JE NE
--             TOUCHE PAS : une autre session y travaille avec des
--             modifications NON COMMITEES, et stager ce fichier emporterait
--             son travail en cours. A faire des qu'elle a commite.
--             Voir notice/CHANTIER_COQUILLES_OFFRE_2026-11-02.md.
--
-- POURQUOI PAR ANCRE, ET PAS EN RECOPIANT LA FONCTION (leçon 30 du projet) :
--   recopier les 6 251 caracteres de app_registre_dossiers ecraserait en
--   silence toute modification qu'une autre session y aurait faite entre ma
--   lecture et mon application. On part donc de la definition VIVANTE, on
--   verifie son empreinte, et on n'insere qu'une ligne. L'ancre tient sur UNE
--   SEULE LIGNE et son unicite est verifiee avant usage.
-- =====================================================================

-- --- 1. LE PREDICAT, UNE SEULE FOIS, POUR TOUTES LES PORTES ---
-- * Regle du projet : une exclusion vit a part et se fait APPELER ; recopiee
--   dans chaque requete, elle derive. Et elle se DECLARE, elle ne se cache pas.
CREATE OR REPLACE FUNCTION public.app_affaire_est_coquille(
    p_kind text, p_date text, p_propositions jsonb)
RETURNS boolean
LANGUAGE sql IMMUTABLE
AS $coq$
    SELECT p_kind = 'offre'
       AND p_date IS NULL
       AND coalesce(btrim(p_propositions::text), '') IN ('', '[]', 'null')
$coq$;

COMMENT ON FUNCTION public.app_affaire_est_coquille(text, text, jsonb) IS
'Une offre que Hektor porte SANS AUCUNE PROPOSITION : ni montant, ni statut, ni date. 54 lignes au 02/11/2026. Masquee a l''affichage, JAMAIS supprimee. Ne vise PAS les 14 offres a 0000-00-00, qui ont des propositions et un montant.';

REVOKE ALL ON FUNCTION public.app_affaire_est_coquille(text, text, jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.app_affaire_est_coquille(text, text, jsonb) TO authenticated, anon, service_role;

-- --- 2. LE FILTRE, INSERE DANS LA DEFINITION VIVANTE ---
DO $pose$
DECLARE
    def      text;
    nouvelle text;
    ancre    text := '                or l.app_chaine_id in (select id from nom))';
    ajout    text := E'\n           -- 02/11/2026 : ON NE MONTRE PLUS LES COQUILLES D''OFFRE. Un seul\n           -- predicat, appele par CHAQUE porte -- voir app_affaire_est_coquille.\n           and not public.app_affaire_est_coquille(l.kind, l.date, l.propositions_json)';
BEGIN
    SELECT pg_get_functiondef(p.oid) INTO def
      FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = 'public' AND p.proname = 'app_registre_dossiers';

    IF def IS NULL THEN
        RAISE EXCEPTION 'app_registre_dossiers n''existe pas -- ON NE TOUCHE A RIEN';
    END IF;

    -- /!\ L'EMPREINTE : si une autre session est passee avant moi, on S'ARRETE
    --   au lieu d'ecraser son travail.
    IF md5(def) <> '321f7de2307ddee735e6a849f33f4855' THEN
        RAISE EXCEPTION 'app_registre_dossiers a change (empreinte %) -- quelqu''un est passe avant moi, ON NE TOUCHE A RIEN', md5(def);
    END IF;

    IF position(ancre in def) = 0 THEN
        RAISE EXCEPTION 'ancre introuvable -- ON NE TOUCHE A RIEN';
    END IF;
    -- * UNICITE DE L'ANCRE : sans ce controle, un remplacement pourrait frapper
    --   deux endroits et le filtre se retrouverait la ou il n'a rien a faire.
    IF (length(def) - length(replace(def, ancre, ''))) / length(ancre) <> 1 THEN
        RAISE EXCEPTION 'ancre presente % fois au lieu d''une -- ON NE TOUCHE A RIEN',
                        (length(def) - length(replace(def, ancre, ''))) / length(ancre);
    END IF;

    -- deja posee ? on ne repose pas (le patch doit pouvoir etre rejoue)
    IF position('app_affaire_est_coquille' in def) > 0 THEN
        RAISE NOTICE 'le filtre est deja en place -- rien a faire.';
        RETURN;
    END IF;

    nouvelle := replace(def, ancre, ancre || ajout);
    EXECUTE nouvelle;
    RAISE NOTICE 'filtre pose dans app_registre_dossiers.';
END $pose$;

REVOKE ALL ON FUNCTION public.app_registre_dossiers(integer) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.app_registre_dossiers(integer) TO authenticated, service_role;

-- --- 3. LA PREUVE, PAS L'ABSENCE D'ERREUR ---
DO $preuve$
DECLARE coq integer; gardees integer; restants integer; pose boolean;
BEGIN
    SELECT position('app_affaire_est_coquille' in pg_get_functiondef(p.oid)) > 0 INTO pose
      FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = 'public' AND p.proname = 'app_registre_dossiers';
    IF NOT coalesce(pose, false) THEN
        RAISE EXCEPTION 'le filtre N''EST PAS dans la fonction -- rien n''a ete pose';
    END IF;

    SELECT count(*) INTO coq FROM public.app_affaire_ledger l
     WHERE public.app_affaire_est_coquille(l.kind, l.date, l.propositions_json);

    SELECT count(*) INTO gardees FROM public.app_affaire_ledger l
     WHERE l.kind = 'offre' AND l.date IS NULL
       AND NOT public.app_affaire_est_coquille(l.kind, l.date, l.propositions_json);

    -- /!\ ON NE COMPTE PAS app_registre_dossiers(NULL) ICI, et c'est VOULU :
    --   elle filtre par is_app_global_reader() et le portefeuille de
    --   l'appelant. Executee par un outil sans utilisateur authentifie, elle
    --   rend 0 -- legitimement. Un controle base sur elle crierait au rouge
    --   sur une lecture parfaitement saine. On mesure donc LA TABLE, avec le
    --   meme predicat que la fonction : ca ne depend d'aucun droit.
    SELECT count(DISTINCT l.app_chaine_id) INTO restants
      FROM public.app_affaire_ledger l
     WHERE l.app_chaine_id IS NOT NULL
       AND NOT (btrim(coalesce(l.hektor_affaire_id, '')) <> '' AND l.present_in_hektor IS false)
       AND NOT public.app_affaire_est_coquille(l.kind, l.date, l.propositions_json);

    RAISE NOTICE 'coquilles reconnues : % (54 attendu) | offres a 0000 GARDEES : % (14 attendu) | dossiers restants : % (12 110 attendu, contre 12 117 avant)',
                 coq, gardees, restants;

    IF coq <> 54 THEN
        RAISE EXCEPTION 'le predicat reconnait % coquilles au lieu de 54 -- RIEN N''EST VALIDE', coq;
    END IF;
    -- * LE TEMOIN INVERSE : si ce chiffre bouge, le filtre a mordu sur les 14.
    IF gardees <> 14 THEN
        RAISE EXCEPTION 'les 14 offres a 0000 ne sont plus que % -- le filtre MORD TROP LARGE', gardees;
    END IF;
    -- * LES 7 QUI PARTENT SONT LES CHAINES 100 %% COQUILLES (49 touchees,
    --   7 pures, 42 mixtes -- mesure du 02/11).
    IF restants <> 12110 THEN
        RAISE EXCEPTION 'il reste % dossiers au lieu de 12 110 -- RIEN N''EST VALIDE', restants;
    END IF;
END $preuve$;
