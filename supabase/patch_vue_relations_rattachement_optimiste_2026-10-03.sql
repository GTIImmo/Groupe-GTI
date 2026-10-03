-- ═══════════════════════════════════════════════════════════════════════════════
-- app_contact_relations_current : le rattachement devient OPTIMISTE, comme le retrait
-- ═══════════════════════════════════════════════════════════════════════════════
-- QUESTION DE FREDERIC, 03/10 : « pourquoi 20 secondes ? Normalement c'est
-- instantane si on ecrit chez nous. Non ? » -- il a raison, et la cause tenait en
-- UNE ligne de cette vue :
--
--     WHERE (r.present_in_hektor AND (r.retire_le IS NULL))
--             ^^^^^^^^^^^^^^^^^^        ^^^^^^^^^^^^^^^^^^
--             le RATTACHEMENT attend     le RETRAIT n'attend
--             la confirmation d'Hektor   RIEN : on ecrit chez nous,
--                                        ca disparait tout de suite
--
-- DEUX POIDS, DEUX MESURES DANS LA MEME LIGNE. Le retrait est optimiste depuis le
-- debut ; le rattachement, lui, etait pessimiste -- alors que la RPC qui le pose
-- s'appelle `app_link_mandant_optimistic`. Elle portait « optimiste » dans son nom
-- sans l'etre.
--
-- CE QUE CA COUTAIT, mesure a l'ecran le 03/10 : un mandant qu'on vient de
-- rattacher n'apparaissait pas, donc SON BOUTON « RETIRER » N'EXISTAIT PAS. Un
-- negociateur qui se trompait de personne devait attendre le run de NUIT, ou aller
-- la retirer dans Hektor. L'inverse de l'autonomie qu'on construit.
--
-- CE QUE CHANGE CE PATCH : un lien NE DANS L'APP s'affiche des le clic. Le worker
-- previent Hektor en arriere-plan ; si Hektor REFUSE, il le defait -- exactement
-- comme il remet un retrait refuse (annulerRattachementOptimiste, pose le meme jour
-- dans console_job_worker.js, miroir de annulerRetraitOptimiste).
--
-- ⛔ L'ORDRE COMPTE, ET IL A ETE RESPECTE : le filet du worker est pose AVANT cette
--   ouverture. Ouvrir la vue sans lui ferait afficher a tort un lien refuse par
--   Hektor -- ce serait PIRE que les 20 secondes qu'on supprime.
--
-- ⚠ ON NE SE SERT QUE DE CE QUI EXISTE : `absent_depuis` veut DEJA dire « Hektor ne
--   l'a pas / plus » dans ce registre (relation_ledger.py). Un lien refuse le porte,
--   et la vue l'ecarte. La ligne RESTE -- « on efface l'etat, jamais la trace ».
--
-- SEULE LA LIGNE `WHERE` DE LA PREMIERE BRANCHE CHANGE. La seconde (les acquereurs)
-- est recopiee a l'identique, ainsi que les 18 colonnes et leur ordre.
--
-- RETOUR ARRIERE : rejouer ce fichier avec l'ancien WHERE, c'est-a-dire
--     WHERE (r.present_in_hektor AND (r.retire_le IS NULL))
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

CREATE OR REPLACE VIEW public.app_contact_relations_current AS
 SELECT r.relation_key,
    (r.app_contact_id)::text AS hektor_contact_id,
    r.hektor_annonce_id,
    r.app_dossier_id,
    b.numero_dossier,
    b.numero_mandat,
    b.titre_bien,
    COALESCE(
        CASE
            WHEN (NULLIF(btrim(COALESCE(b.numero_mandat, ''::text)), ''::text) IS NOT NULL) THEN 'mandant'::text
            ELSE NULL::text
        END, r.role_hektor, 'proprietaire'::text) AS role_contact,
    NULL::text AS contact_date_maj,
    r.source AS relation_source,
    NULL::text AS transaction_type,
    NULL::text AS transaction_id,
    NULL::text AS transaction_state,
    NULL::text AS transaction_date,
    NULL::text AS transaction_amount,
    COALESCE(b.au_parc, false) AS is_active_annonce,
    r.last_seen_at,
    r.last_seen_at AS refreshed_at
   FROM (app_relation r
     LEFT JOIN LATERAL ( SELECT s.numero_dossier,
            s.numero_mandat,
            s.titre_bien,
            s.au_parc
           FROM ( SELECT d.numero_dossier,
                    d.numero_mandat,
                    d.titre_bien,
                    true AS au_parc,
                    1 AS rang
                   FROM app_dossiers_current d
                  WHERE (d.hektor_annonce_id = (r.hektor_annonce_id)::bigint)
                UNION ALL
                 SELECT a.numero_dossier,
                    a.numero_mandat,
                    a.titre_bien,
                    false,
                    2
                   FROM app_archive_annonce_index_current a
                  WHERE (a.hektor_annonce_id = (r.hektor_annonce_id)::bigint)
                UNION ALL
                 SELECT h.numero_dossier,
                    h.numero_mandat,
                    h.titre_bien,
                    false,
                    3
                   FROM app_historical_annonce_index_current h
                  WHERE (h.hektor_annonce_id = (r.hektor_annonce_id)::bigint)) s
          ORDER BY s.rang
         LIMIT 1) b ON (true))
  -- ═══ LA SEULE LIGNE QUI CHANGE ═══
  --  · Hektor l'a                      -> on montre (comme avant)
  --  · ne dans l'app et pas refuse      -> on montre AUSSI, des le clic (nouveau)
  --  · retire                           -> on cache (comme avant, inchange)
  WHERE (((r.present_in_hektor) OR ((r.source = 'app'::text) AND (r.absent_depuis IS NULL)))
         AND (r.retire_le IS NULL))
UNION ALL
 SELECT c.relation_key,
    c.hektor_contact_id,
    c.hektor_annonce_id,
    c.app_dossier_id,
    c.numero_dossier,
    c.numero_mandat,
    c.titre_bien,
    c.role_contact,
    c.contact_date_maj,
    c.relation_source,
    c.transaction_type,
    c.transaction_id,
    c.transaction_state,
    c.transaction_date,
    c.transaction_amount,
    c.is_active_annonce,
    c.last_seen_at,
    (c.refreshed_at)::text AS refreshed_at
   FROM app_contact_relation_current c
  WHERE (c.role_contact ~~ 'acquereur%'::text);

-- ─── LE GARDE-FOU : on verifie ce qu'on vient de poser, on ne le suppose pas ───
DO $$
DECLARE n_colonnes int; n_total bigint; n_app_visibles bigint; n_retires_visibles bigint;
BEGIN
    SELECT count(*) INTO n_colonnes FROM information_schema.columns
     WHERE table_schema='public' AND table_name='app_contact_relations_current';
    IF n_colonnes <> 18 THEN
        RAISE EXCEPTION 'ARRET : la vue a % colonnes au lieu de 18 -- le front en depend.', n_colonnes;
    END IF;

    -- la branche des acquereurs doit avoir survecu
    IF position('acquereur%' in pg_get_viewdef('public.app_contact_relations_current'::regclass)) = 0 THEN
        RAISE EXCEPTION 'ARRET : la branche des acquereurs a disparu de la vue.';
    END IF;

    -- ⛔ AUCUN LIEN RETIRE NE DOIT REAPPARAITRE. C'est la regression la plus grave
    --   possible ici : elle ferait revenir a l'ecran ce qu'un negociateur a retire.
    SELECT count(*) INTO n_retires_visibles
      FROM app_contact_relations_current v
      JOIN app_relation r ON r.relation_key = v.relation_key
     WHERE r.retire_le IS NOT NULL;
    IF n_retires_visibles > 0 THEN
        RAISE EXCEPTION 'ARRET : % lien(s) RETIRE(S) sont visibles -- la vue est fausse.', n_retires_visibles;
    END IF;

    SELECT count(*) INTO n_total FROM app_contact_relations_current;
    SELECT count(*) INTO n_app_visibles
      FROM app_relation
     WHERE source = 'app' AND NOT present_in_hektor AND absent_depuis IS NULL AND retire_le IS NULL;

    RAISE NOTICE 'OK : vue a 18 colonnes, % lignes au total, dont % lien(s) ne(s) dans l app desormais visibles immediatement, 0 retire visible.',
        n_total, n_app_visibles;
END $$;

COMMIT;
