-- =====================================================================
-- LA REPARTITION DE COMMISSION APPARTIENT A L'APP            14/09/2026
-- Chantier C.19-d, tache 3.2e, lot 5.
-- =====================================================================
--
-- POURQUOI CETTE TABLE EXISTE
-- ---------------------------
-- Decision de Frederic, 14/09 : « le systeme de repartition des commissions de
-- Hektor n'est pas utile POUR MON APPS a l'avenir ». C'est le premier morceau
-- d'autonomie reelle : une donnee que l'app SAISIT, DETIENT, et n'envoie pas.
--
-- ⚠ CE N'EST PAS UN CHOIX DE CONFORT, LEUR MODELE NE SAIT PAS L'EXPRIMER.
--   Mesure du 14/09 sur 5 428 compromis dont les DEUX commerciaux sont connus :
--       1 445, soit 26,6 %, ont l'acquereur suivi par UNE AUTRE AGENCE que le bien.
--   Or la liste que la page de Hektor propose se limite aux negociateurs ACTIFS
--   DE L'AGENCE DU BIEN -- verifie sur trois agences, proposes = actifs a chaque
--   fois (Firminy 1, Annonay 2, Le Puy 3). Un quart des repartitions reelles est
--   donc inenvoyable chez eux. L'app ne DUPLIQUE pas leur donnee : elle en tient
--   une que Hektor est incapable de porter.
--
-- ⚠ ET RIEN NE PART CHEZ EUX. Le worker ne pose plus aucun champ d'intervenant
--   depuis 06bd38b. Leur fiche affichera « Part Reseau 100 % », c'est-a-dire
--   « personne d'attribue » -- ce qui est VRAI. Y ecrire le commercial de
--   l'annonce serait faux une fois sur quatre : « mieux vaut un champ absent
--   qu'un champ menteur ».
--
-- CE QUI EST MESURE, ET QUI JUSTIFIE LA FORME
-- -------------------------------------------
--   l'attribution se fait AU COMPROMIS     39 compromis reels sur 39 en portent
--   la vente REPREND celle du compromis    16 biens portant les deux, 16 identiques
--   un dossier commence par une OFFRE      72,4 % ; 12,1 % n'en ont aucune
--   « Part Reseau » est le RESIDU          100 % sans personne, 0 % des qu'on designe
--
-- ➡ La repartition se rattache donc AU DOSSIER D'AFFAIRE, pas a la transaction :
--   saisie une fois sur la premiere transaction (l'offre le plus souvent), elle
--   vaut pour le compromis puis la vente. La rattacher a la transaction
--   obligerait a la ressaisir deux fois, et deux saisies divergent.
--
-- LA FORME, ET LES QUATRE EMPLACEMENTS
-- ------------------------------------
-- Une ligne PAR PERSONNE CREDITEE. Deux cotes, deux rangs par cote, donc quatre
-- au maximum -- la forme que Frederic a demandee, et celle de Hektor, qui indexe
-- lui aussi ses champs par personne et par sens.
--
-- ⚠ UN EMPLACEMENT VIDE N'EST PAS UNE LIGNE. On n'ecrit que ce qui est decide.
--   L'ecran montre quatre cases ; la base ne porte que celles qui nomment
--   quelqu'un. Une ligne a `hektor_user_id` nul n'aurait aucun sens.
--
-- ⚠ DES POURCENTAGES, JAMAIS DES MONTANTS. La commission bouge avec le prix : un
--   montant fige mentirait des la premiere correction. On enregistre la part, on
--   affiche l'euro. C'est la meme raison qui fait qu'on ne stocke pas le net
--   vendeur calcule.
-- ⚠ ET LA PART EST CELLE DU TOTAL, pas celle du cote. Frederic : « sur les deux
--   lignes entree donc 25 % + 25 % ». Quatre lignes a 25 font 100. La part d'un
--   COTE se retrouve en sommant ses lignes -- l'inverse ne serait pas vrai.
--
-- ⚠ ON GARDE LE NOM AU MOMENT DE LA SAISIE, et ce n'est pas un doublon : c'est la
--   trace de CE QUI A ETE DECIDE ce jour-la. L'annuaire porte 219 personnes dont
--   30 actives, donc un partant reste lisible ; mais si une fiche disparait de
--   chez Hektor, un relevé de commission ne doit pas se reduire a un numero.
--   ➡ A L'AFFICHAGE, l'annuaire gagne toujours. Ce champ n'est qu'un filet.
--
-- ⚠ L'ANCRAGE, ET SON SEUL RISQUE. `app_chaine_id` est le numero de la
--   transaction qui a OUVERT le dossier -- « stable tant que la premiere
--   transaction reste en tete » (affaire_ledger.py). Si le run rechaine et qu'une
--   autre passe en tete, la repartition se retrouverait orpheline. On stocke donc
--   AUSSI `app_dossier_id` : il ne sert a rien au quotidien, il sert a reparer.
--
-- CE QUE CE PATCH NE FAIT PAS
-- ---------------------------
-- Personne ne lit ni n'ecrit encore cette table. L'ecriture depuis l'ecran
-- passera par une RPC, avec le meme controle de role que les autres gestes
-- optimistes -- exactement la demarche de app_affaire_champ_app le 29/08.
-- Le worker ne la lit pas et ne la lira pas : elle ne part pas chez Hektor.
-- ⭐ LE SERVEUR LOCAL LA RECEVRA SANS CABLAGE : pull_from_supabase.py DECOUVRE
--   les tables par la spec OpenAPI de PostgREST et en rapatrie deja 134. Elle
--   descendra au prochain run. C'est la condition posee par Frederic --
--   « au minimum sur le registre des affaires de mon apps ET le serveur ».
--
-- RETOUR ARRIERE : DROP TABLE. Rejouable sans effet de bord.
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.app_affaire_repartition (
    -- LE DOSSIER D'AFFAIRE, pas la transaction. Voir « L'ANCRAGE » ci-dessus.
    app_chaine_id   bigint      NOT NULL,
    -- Le bien. Inutile au quotidien, indispensable pour reparer un rechainage.
    app_dossier_id  bigint,
    -- 'entree' = qui a rentre l'affaire · 'sortie' = qui l'a conclue.
    cote            text        NOT NULL,
    -- 1 ou 2 : les deux emplacements de chaque cote.
    rang            smallint    NOT NULL,
    -- La personne, dans la serie `hektor_user_id` de l'annuaire.
    -- ⚠ PAS `hektor_negociateur_id` : le meme nombre y designe quelqu'un d'autre
    --   (43 = Olivier POMBAR comme negociateur, Stephanie JEOFFROY comme
    --   utilisateur). C'est la serie UTILISATEUR que Hektor emploie pour les
    --   commissions, et se tromper crediterait la mauvaise personne EN SILENCE.
    hektor_user_id  text        NOT NULL,
    -- Le nom tel qu'il etait au moment de la decision. Filet, pas source.
    nom_au_moment   text,
    -- La part DU TOTAL, en pour cent. Les lignes d'un dossier somment a 100.
    pourcentage     numeric(6,3) NOT NULL DEFAULT 0,
    -- 'defaut' = pose par l'app · 'saisie' = choisi par quelqu'un.
    origine         text,
    ecrit_le        timestamptz NOT NULL DEFAULT now(),
    ecrit_par       text,
    CONSTRAINT app_affaire_repartition_pkey PRIMARY KEY (app_chaine_id, cote, rang),
    CONSTRAINT app_affaire_repartition_cote_chk CHECK (cote IN ('entree', 'sortie')),
    CONSTRAINT app_affaire_repartition_rang_chk CHECK (rang IN (1, 2)),
    CONSTRAINT app_affaire_repartition_pct_chk  CHECK (pourcentage >= 0 AND pourcentage <= 100)
);

-- Le relevé par personne est LA raison d'etre de cette table : il doit etre
-- immediat le jour ou on le voudra, pas a refaire.
CREATE INDEX IF NOT EXISTS app_affaire_repartition_user_idx
    ON public.app_affaire_repartition (hektor_user_id);
-- Et la reparation d'un rechainage passe par le bien.
CREATE INDEX IF NOT EXISTS app_affaire_repartition_dossier_idx
    ON public.app_affaire_repartition (app_dossier_id);

COMMENT ON TABLE public.app_affaire_repartition IS
    'QUI TOUCHE LA COMMISSION, et pour quelle part. Donnee PROPRE A L''APP : elle '
    'ne part JAMAIS chez Hektor, dont le modele ne sait pas l''exprimer -- sa liste '
    'se limite aux negociateurs actifs de l''agence du bien, alors que 26,6 % des '
    'compromis ont l''acquereur suivi par une autre agence (mesure du 14/09). '
    'Rattachee au DOSSIER (app_chaine_id) et non a la transaction : saisie une fois '
    'sur la premiere transaction, elle vaut pour le compromis puis la vente.';

COMMENT ON COLUMN public.app_affaire_repartition.hektor_user_id IS
    'Serie `hektor_user_id` de l''annuaire, PAS `hektor_negociateur_id` : le meme '
    'nombre y designe deux personnes differentes (43 = POMBAR / JEOFFROY).';

COMMENT ON COLUMN public.app_affaire_repartition.pourcentage IS
    'Part DU TOTAL de la commission, en pour cent. Les lignes d''un dossier somment '
    'a 100. Jamais un montant : la commission bouge avec le prix.';

COMMENT ON COLUMN public.app_affaire_repartition.nom_au_moment IS
    'Le nom tel qu''il etait le jour de la decision. FILET, pas source : a '
    'l''affichage, l''annuaire gagne toujours.';

ALTER TABLE public.app_affaire_repartition ENABLE ROW LEVEL SECURITY;

-- LECTURE ouverte aux comptes connectes : l'ecran doit pouvoir montrer qui est
-- credite sans passer par une RPC.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies
                 WHERE schemaname = 'public'
                   AND tablename = 'app_affaire_repartition'
                   AND policyname = 'app_affaire_repartition_read') THEN
    CREATE POLICY app_affaire_repartition_read
      ON public.app_affaire_repartition FOR SELECT TO authenticated USING (true);
  END IF;
END $$;

-- ECRITURE : aucune policy, donc personne -- sauf service_role, qui contourne la
-- RLS. C'est de l'argent : le geste passera par une RPC avec controle de role,
-- comme app_modifier_affaire_optimistic. Meme demarche que le carnet le 29/08.
GRANT ALL ON TABLE public.app_affaire_repartition TO service_role;
GRANT SELECT ON TABLE public.app_affaire_repartition TO authenticated;
