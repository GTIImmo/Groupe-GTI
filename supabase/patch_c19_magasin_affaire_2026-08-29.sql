-- =====================================================================
-- C.19 (etape 1) -- LE MAGASIN DES CHAMPS D'AFFAIRE
-- Date : 2026-08-29
--
-- CE QUE C'EST
-- ------------
-- Ce que l'app detient sur une transaction : un prix corrige, une date rectifiee,
-- un sequestre saisi. Ces valeurs restent CHEZ NOUS et ne partent JAMAIS chez
-- Hektor. Seuls les changements d'ETAT lui sont envoyes -- refuser/accepter une
-- offre, annuler un compromis, supprimer une vente.
--
-- POURQUOI CETTE DIRECTION (Frederic, 28/08)
-- ------------------------------------------
-- Elle contourne un obstacle mesure le meme jour : modifier un compromis chez
-- Hektor passe par un module ES charge dynamiquement (launchPopinCompromis ->
-- await import Modules/Compromis), impilotable depuis le worker. En corrigeant
-- chez nous, on n'a plus besoin de savoir corriger chez lui.
--
-- LA CLE : app_affaire_id, ET PAS LE NUMERO HEKTOR
-- ------------------------------------------------
-- C'est deliberé. Le patch du 20/08 (patch_identite_transactions) a justement
-- retire la dependance au numero Hektor : il a donne a chaque affaire un numero
-- de l'app, UNE seule serie pour offre/compromis/vente -- parce que Hektor tient
-- trois compteurs qui se telescopent (7 541 numeros portes par deux types).
-- Ranger ce magasin par numero Hektor reconstruirait exactement la dependance
-- qu'on venait de supprimer, et interdirait a une affaire NEE DANS L'APP
-- d'avoir des champs corriges.
--
-- Verifie le 29/08 : app_affaire_ledger porte 29 293 lignes, 29 293 numeros
-- distincts, 0 sans numero. Et il est deja LISIBLE par l'app -- RLS active,
-- policy app_affaire_ledger_select_active_users. Le front peut donc obtenir
-- app_affaire_id sans qu'on ajoute quoi que ce soit.
--
-- LE PATRON, eprouve CINQ fois dans ce projet
-- -------------------------------------------
-- app_dossier, app_affaire_ledger, app_search_registry, app_contact, et
-- app_mandat_champ_app (28/08, eprouve de bout en bout) : une table A PART,
-- JAMAIS reconstruite, a cote de la table derivee. C'est la sixieme.
--
-- LA REGLE D'ARBITRAGE, deja validee par Frederic le 28/08 :
--     l'app a une valeur   ->  elle gagne
--     l'app n'a rien       ->  ON NE TOUCHE A RIEN, Hektor garde la main
--
-- CE QU'IL FAUT SAVOIR, ET QUI A ETE DIT
-- --------------------------------------
-- Un prix corrige chez nous et pas chez Hektor DIVERGE DEFINITIVEMENT. C'est le
-- but -- nos chiffres deviennent les bons -- mais tout reporting encore lu dans
-- Hektor affichera l'ancienne valeur.
--
-- RLS FERMEE pour l'instant : seul service_role y touche (le worker et les
-- scripts du serveur). L'ecriture depuis l'ecran passera par une RPC, a l'etape 3,
-- comme le fait deja l'edition optimiste des champs d'annonce.
--
-- PERSONNE NE LIT ENCORE CETTE TABLE. Retour arriere : DROP TABLE.
-- Rejouable sans effet de bord.
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.app_affaire_champ_app (
    app_affaire_id bigint      NOT NULL,
    champ          text        NOT NULL,
    valeur_app     text,
    origine        text,
    ecrit_le       timestamptz NOT NULL DEFAULT now(),
    ecrit_par      text,
    CONSTRAINT app_affaire_champ_app_pkey PRIMARY KEY (app_affaire_id, champ)
);

COMMENT ON TABLE public.app_affaire_champ_app IS
    'Ce que l''app detient sur une transaction (prix, dates, sequestre, honoraires). '
    'Jamais reconstruite. Ces valeurs ne partent JAMAIS chez Hektor : lui n''apprend '
    'que les changements d''etat. Rangee par app_affaire_id -- l''identite posee le 20/08.';

COMMENT ON COLUMN public.app_affaire_champ_app.valeur_app IS
    'La valeur saisie dans l''app. VIDE = l''app n''a rien a dire, et Hektor garde la main.';

ALTER TABLE public.app_affaire_champ_app ENABLE ROW LEVEL SECURITY;

-- Aucune policy : RLS active sans policy = personne, sauf service_role qui la contourne.
GRANT ALL ON TABLE public.app_affaire_champ_app TO service_role;
