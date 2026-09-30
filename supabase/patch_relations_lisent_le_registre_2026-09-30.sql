-- ═══════════════════════════════════════════════════════════════════════════════
-- LA BASCULE : L'ECRAN LIT LE REGISTRE DES LIENS               30/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL.
--
-- ─── CE QUI CHANGE, ET CE QUI NE CHANGE PAS ─────────────────────────────────────
-- ⭐ LE FRONT NE CHANGE PAS D'UNE LIGNE. `loadContactRelations` fait `select('*')`
--    sur `app_contact_relations_current` et filtre sur `hektor_contact_id` : on
--    garde EXACTEMENT le meme nom de vue et les 18 memes noms de colonnes. Ni
--    api.ts, ni le type AppContactRelation, ni App.tsx ne bougent.
--    Meme parti pris que le registre des mandats ce matin : on ne remplace pas la
--    vue, ON CHANGE LA SOURCE DE SES COLONNES.
--
-- AVANT   app_contact_relation_current  EFFACEE ET REFAITE chaque nuit, et
--                                       poussee pour les SEULS biens du parc
-- APRES   app_relation                  le registre durable, dont RIEN NE SORT
--         + trois index de biens        parc · archive · historique
--         + la table de nuit            pour les acquereurs SEULEMENT (voir ③)
--
-- ─── LE RESULTAT, MESURE EN BEGIN/ROLLBACK ──────────────────────────────────────
--                        AUJOURD'HUI      APRES
--    lignes de la vue         81 379    163 765     +82 386
--    mandant                              74 166    identique au registre
--    proprietaire                         58 456    identique
--    acquereur                31 143     31 143    IDENTIQUE, zero perte
--    sans titre                            6 433    voir ③
-- Le jour ou un bien se vendait, on cessait de savoir qui en etait le mandant.
-- 82 386 liens etaient dans ce cas.
--
-- ─── TROIS ARBITRAGES, ET LES MESURES QUI LES ONT DICTES ────────────────────────
-- ① LE ROLE SE DERIVE, MAIS IL NE REECRIT PAS L'HISTOIRE.
--    `mandant` quand le bien porte un numero de mandat ; SINON on garde ce que
--    Hektor disait (`role_hektor`).
--    ⚠ LE REPLI N'EST PAS DU CONFORT : deriver SANS lui changeait 4 961 etiquettes,
--      TOUTES dans le meme sens (mandant -> proprietaire), parce que l'index des
--      archives ne porte plus le numero de mandat d'un bien sorti du parc.
--      Un homme qui a signe un mandat en 2019 EST le mandant de ce bien-la ;
--      lui retirer le titre parce que notre index a oublie le numero serait
--      reecrire l'histoire. Avec le repli : 0 etiquette changee.
--    Le fait stocke reste « proprietaire du bien », le seul que Hektor connaisse.
--    (Mesure du 30/09 : sur 132 622 couples, ZERO ne porte les deux roles.)
--
-- ② LES ACQUEREURS RESTENT LUS DANS LA TABLE DE NUIT -- POUR L'INSTANT.
--    Le bon dessin est de les PROJETER depuis `app_affaire_ledger` : un acquereur
--    n'est pas un lien au bien, il existe PARCE QU'IL A FAIT UNE OFFRE, et le
--    ledger tient ce fait durablement.
--    ⛔ MAIS LA PROJECTION PERDRAIT 791 LIGNES, mesure : le ledger ne porte
--      qu'UN `app_contact_id` par affaire ; les CO-ACQUEREURS vivent dans le blob
--      `acquereurs_json`, qui est encore sur les numeros HEKTOR (23 798 parties,
--      0 dans la plage de l'app). 2 450 affaires ont plusieurs acquereurs.
--      Projeter aujourd'hui ferait disparaitre des couples qui achetent ensemble.
--    ➡ LA PROJECTION VIENDRA QUAND CE BLOB SERA SUR NOS NUMEROS. En attendant,
--      zero perte de fonction : c'est la regle du projet.
--
-- ③ UN LIEN SANS TITRE VAUT MIEUX QU'UN LIEN DISPARU.
--    6 433 liens portent sur 3 136 biens qu'aucun des trois index ne nomme.
--    Ils s'afficheront avec leur numero et sans titre.
--    ⛔ CE N'EST PAS UNE PERTE, C'EST UN INDEX INCOMPLET : le SERVEUR connait
--      58 598 des 58 604 biens du registre -- 6 seulement lui echappent. Ce sont
--      les index du CLOUD qui ne couvrent pas tout. A traiter a part.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
-- DROP VIEW public.app_contact_relations_current;
-- CREATE VIEW public.app_contact_relations_current AS
--   SELECT relation_key, hektor_contact_id, hektor_annonce_id, app_dossier_id,
--          numero_dossier, numero_mandat, titre_bien, role_contact, contact_date_maj,
--          relation_source, transaction_type, transaction_id, transaction_state,
--          transaction_date, transaction_amount, is_active_annonce, last_seen_at,
--          refreshed_at
--     FROM public.app_contact_relation_current;
-- La table d'avant n'est PAS touchee : elle continue d'etre remplie chaque nuit.
-- ═══════════════════════════════════════════════════════════════════════════════

DROP VIEW IF EXISTS public.app_contact_relations_current;

CREATE VIEW public.app_contact_relations_current AS
WITH bien AS (
    -- Le parc d'abord, puis l'archive, puis l'historique. DISTINCT ON garde le
    -- premier rang : un bien encore au parc n'est jamais decrit par son archive.
    SELECT DISTINCT ON (id) id, numero_dossier, numero_mandat, titre_bien, au_parc
      FROM (
        SELECT hektor_annonce_id::text AS id, numero_dossier, numero_mandat,
               titre_bien, true AS au_parc, 1 AS rang
          FROM public.app_dossiers_current WHERE hektor_annonce_id IS NOT NULL
        UNION ALL
        SELECT hektor_annonce_id::text, numero_dossier, numero_mandat,
               titre_bien, false, 2
          FROM public.app_archive_annonce_index_current WHERE hektor_annonce_id IS NOT NULL
        UNION ALL
        SELECT hektor_annonce_id::text, numero_dossier, numero_mandat,
               titre_bien, false, 3
          FROM public.app_historical_annonce_index_current WHERE hektor_annonce_id IS NOT NULL
      ) x ORDER BY id, rang
)

-- ① LES LIENS AU BIEN -- depuis le registre durable, qui ne perd rien
SELECT
    r.relation_key,
    r.app_contact_id::text                       AS hektor_contact_id,
    r.hektor_annonce_id,
    r.app_dossier_id,
    b.numero_dossier,
    b.numero_mandat,
    b.titre_bien,
    -- derive quand on SAIT ; sinon on garde ce que Hektor disait (voir ①)
    COALESCE(
        CASE WHEN NULLIF(btrim(COALESCE(b.numero_mandat, '')), '') IS NOT NULL
             THEN 'mandant' END,
        r.role_hektor,
        'proprietaire')                          AS role_contact,
    NULL::text                                   AS contact_date_maj,
    r.source                                     AS relation_source,
    NULL::text                                   AS transaction_type,
    NULL::text                                   AS transaction_id,
    NULL::text                                   AS transaction_state,
    NULL::text                                   AS transaction_date,
    NULL::text                                   AS transaction_amount,
    COALESCE(b.au_parc, false)                   AS is_active_annonce,
    r.last_seen_at::text                         AS last_seen_at,
    r.last_seen_at::text                         AS refreshed_at
FROM public.app_relation r
LEFT JOIN bien b ON b.id = r.hektor_annonce_id

UNION ALL

-- ② LES ACQUEREURS -- encore lus dans la table de nuit, le temps que les
--    co-acquereurs du ledger passent sur nos numeros (voir ②)
SELECT
    c.relation_key, c.hektor_contact_id, c.hektor_annonce_id, c.app_dossier_id,
    c.numero_dossier, c.numero_mandat, c.titre_bien, c.role_contact,
    c.contact_date_maj, c.relation_source, c.transaction_type, c.transaction_id,
    c.transaction_state, c.transaction_date, c.transaction_amount,
    c.is_active_annonce, c.last_seen_at::text, c.refreshed_at::text
FROM public.app_contact_relation_current c
WHERE c.role_contact LIKE 'acquereur%';

COMMENT ON VIEW public.app_contact_relations_current IS
  'LES LIENS D''UN CONTACT (30/09/2026). Le NOM et les 18 COLONNES sont inchanges : '
  'le front ne bouge pas. La SOURCE change -- app_relation, le registre durable '
  'dont rien ne sort, au lieu de app_contact_relation_current, effacee et refaite '
  'chaque nuit. 81 379 -> 163 765 lignes : +82 386 liens qu''un bien vendu '
  'emportait. Le role se derive du numero de mandat QUAND ON LE CONNAIT, sinon on '
  'garde ce que Hektor disait -- sans ce repli, 4 961 mandants devenaient '
  'proprietaires parce que l''index d''archive a oublie leur numero. Les acquereurs '
  'restent lus dans la table de nuit le temps que les co-acquereurs du ledger '
  'passent sur nos numeros : les projeter aujourd''hui perdrait 791 lignes.';
