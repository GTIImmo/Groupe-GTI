-- C.13 -- LE DOMICILE DURABLE DE LA CLOTURE DE MANDAT
-- 28/08/2026
--
-- POURQUOI CETTE TABLE
-- --------------------
-- La cloture locale ecrivait dans app_mandat_register_current. Deux defauts, mesures :
--
--   1. LE REGISTRE EST FILTRE SUR LE STATUT DE L'ANNONCE. Une annonce qui passe a
--      "Clos" ou "Vendu" en SORT. La ligne disparait donc au moment precis ou l'on
--      veut y poser la date de cloture. Mesure du 28/08 : annonce 62966 -> 0 ligne,
--      et 642 des 1 105 mandats invisibles du registre le sont "parce qu'ils sont clos".
--
--   2. LE REGISTRE EST VIDE PUIS REFAIT a chaque push
--      (push_upgrade_to_supabase.py:1126, delete_all_rows). Une valeur ecrite par
--      l'app n'y survit pas.
--
-- Et une modification PostgREST qui ne correspond a AUCUNE ligne renvoie 200 : le
-- travail annoncait "done" sans avoir rien ecrit. C'est ce silence qui a fait croire
-- que la cloture fonctionnait.
--
-- LE PATRON, deja eprouve QUATRE fois dans ce projet
-- -------------------------------------------------
-- app_dossier, app_affaire_ledger, app_search_registry, app_contact : une table A PART,
-- jamais reconstruite, a cote de la table derivee. C'est la cinquieme.
--
-- LA CLE : (annonce, numero de mandat, champ)
-- ------------------------------------------
-- Le couple annonce+mandat est la seule cle unique -- 24 939 sur 24 939, mesure du 28/08.
-- Hektor reutilise ses identifiants bas : 342 sont partages entre plusieurs annonces.
-- On prend numero_mandat et non hektor_mandat_id parce que c'est ce que le worker
-- DETIENT au moment du geste (le payload du front porte numero_mandat, jamais l'id).
-- hektor_mandat_id reste disponible, rempli plus tard par le magasin cote serveur.
--
-- CE QUE CETTE TABLE N'EST PAS
-- ---------------------------
-- Ce n'est PAS le registre des mandats (chantier A.3-technique, 3 a 5 jours, range en
-- fin de plan avec A.1 et A.2). C'est le magasin d'UN champ que l'app possede --
-- l'exact equivalent des trois champs de contact (birth_date, birth_place,
-- marital_status) qui fonctionnent depuis des semaines.
--
-- RLS FERMEE : seul service_role y touche, c'est-a-dire le worker et les scripts du
-- serveur. Le front n'a aucune raison de la lire : il lit le registre et la vue.
--
-- RETOUR ARRIERE : DROP TABLE public.app_mandat_champ_app;
-- Rejouable sans effet de bord.

CREATE TABLE IF NOT EXISTS public.app_mandat_champ_app (
    hektor_annonce_id text        NOT NULL,
    numero_mandat     text        NOT NULL,
    champ             text        NOT NULL,
    valeur_app        text,
    hektor_mandat_id  text,
    origine           text,
    ecrit_le          timestamptz NOT NULL DEFAULT now(),
    ecrit_par         text,
    CONSTRAINT app_mandat_champ_app_pkey
        PRIMARY KEY (hektor_annonce_id, numero_mandat, champ)
);

COMMENT ON TABLE public.app_mandat_champ_app IS
    'Ce que l''app detient sur un mandat, hors de Hektor. Jamais reconstruite. '
    'Lue par phase2/identite/magasin_mandat_app.py, appliquee par appliquer_contrat_mandat.py.';

COMMENT ON COLUMN public.app_mandat_champ_app.valeur_app IS
    'La valeur ecrite par l''app. VIDE = l''app n''a rien a dire, et Hektor garde la main.';

-- Pour retrouver rapidement tout ce que l'app detient sur une annonce.
CREATE INDEX IF NOT EXISTS idx_app_mandat_champ_app_annonce
    ON public.app_mandat_champ_app (hektor_annonce_id);

ALTER TABLE public.app_mandat_champ_app ENABLE ROW LEVEL SECURITY;

-- Aucune policy : RLS active sans policy = personne, sauf service_role qui la contourne.
GRANT ALL ON TABLE public.app_mandat_champ_app TO service_role;
