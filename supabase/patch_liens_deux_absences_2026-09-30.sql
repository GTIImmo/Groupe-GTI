-- ═══════════════════════════════════════════════════════════════════════════════
-- LE REGISTRE DES LIENS DISTINGUE DEUX ABSENCES                 30/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL.
--
-- ⚠⚠ CE PATCH FERME UN TROU QUE J'AI OUVERT CE MATIN MEME.
--
-- ─── LE TROU ────────────────────────────────────────────────────────────────────
-- `app_relation` est en delete-never : rien n'en sort jamais. C'est juste pour un
-- registre -- c'est meme toute sa raison d'etre (82 386 liens qu'un bien vendu
-- emportait).
-- MAIS J'AI CONFONDU DEUX ABSENCES QUI N'ONT RIEN A VOIR :
--
--     « HEKTOR NE LE MONTRE PLUS »   le miroir ne l'a pas ramene ce coup-ci
--                                    -> on GARDE, c'est le but du registre
--
--     « ON L'A SUPPRIME »            un negociateur a supprime le contact ou
--                                    l'annonce, DELIBEREMENT
--                                    -> l'ecran ne doit PLUS le montrer
--
-- Quatre chemins effacent un lien aujourd'hui, et AUCUN ne connait app_relation :
--     le worker   cleanupSupabaseAnnonceRows      (annonce supprimee)
--     le worker   le menage du contact            (contact supprime)
--     le serveur  delete_local_annonce.py
--     le serveur  delete_local_contact.py
-- Ma vue ne filtrait rien : elle aurait affiche un lien supprime, pour toujours.
-- Zero degat a ce jour (aucune ligne n'est marquee), mais LE PREMIER CONTACT
-- SUPPRIME l'aurait produit.
--
-- ─── LA REPARATION, ET POURQUOI ELLE NE TOUCHE NI LE WORKER NI LES SUPPRESSIONS ──
-- LE REGISTRE PORTE TOUT, L'ECRAN FILTRE. C'est le principe deja applique deux
-- fois aujourd'hui (le mandat, puis les liens). La vue exclut desormais :
--     present_in_hektor = false   -> ce que le miroir ne ramene plus
--     retire_le IS NOT NULL       -> ce qu'on a supprime volontairement
-- et les lignes RESTENT au registre, dans les deux cas.
--
-- ⚠ QUAND UN CONTACT EST SUPPRIME, son lien sort de la couche -> le run suivant
--   pose `present_in_hektor = 0` -> la vue cesse de le montrer. Le trou est donc
--   ferme DES LE RUN SUIVANT, sans toucher au worker.
--
-- ⛔ CE QUI RESTE OUVERT, ET IL FAUT LE DIRE : LA FENETRE. Entre le geste (10 h)
--   et le run (5 h), la vue montre encore le lien -- jusqu'a 19 heures. Avant,
--   le worker effacait la ligne tout de suite et l'ecran suivait dans la seconde.
--   `retire_le` / `retire_par` sont posees POUR CELA : le jour ou les quatre
--   chemins les ecriront, la fenetre tombe a zero. Elles sont DORMANTES ici.
--
-- ─── LA PREUVE QUE LE FILTRE NE CACHE RIEN QU'IL NE DOIVE ───────────────────────
-- Mesure du 30/09, et c'est elle qui autorise ce patch :
--     liens sur un bien NON actif, dans la couche   82 386
--     -> un bien vendu NE FAIT PAS sortir son lien de la couche
--     -> `present_in_hektor` reste a 1
--     -> LE FILTRE NE TOUCHE PAS LES 82 386 QU'ON VIENT DE RECUPERER
--     lignes que le filtre cacherait aujourd'hui         0
-- Eprouve en BEGIN/ROLLBACK : 163 765 lignes AVANT, 163 765 APRES. Zero regression.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
-- Rejouer la vue sans les deux lignes du WHERE (patch_relations_lisent_le_registre).
-- ALTER TABLE public.app_relation DROP COLUMN retire_le, DROP COLUMN retire_par;
-- ═══════════════════════════════════════════════════════════════════════════════

ALTER TABLE public.app_relation
  ADD COLUMN IF NOT EXISTS retire_le  text,
  ADD COLUMN IF NOT EXISTS retire_par text;

COMMENT ON COLUMN public.app_relation.retire_le IS
  'QUAND le lien a ete RETIRE VOLONTAIREMENT (suppression d''un contact ou d''une '
  'annonce, ou un futur geste « retirer un mandant »). A NE PAS CONFONDRE AVEC '
  'present_in_hektor = false, qui dit seulement « le miroir ne le ramene plus ». '
  'Dans les deux cas LA LIGNE RESTE : un registre ne perd pas une ligne, il la date.';

COMMENT ON COLUMN public.app_relation.retire_par IS
  'QUI l''a retire. Un registre dit qui a agi, pas seulement que quelque chose a change.';

DROP VIEW IF EXISTS public.app_contact_relations_current;

CREATE VIEW public.app_contact_relations_current AS
WITH bien AS (
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

-- ① LES LIENS AU BIEN -- depuis le registre durable
SELECT
    r.relation_key,
    r.app_contact_id::text                       AS hektor_contact_id,
    r.hektor_annonce_id,
    r.app_dossier_id,
    b.numero_dossier,
    b.numero_mandat,
    b.titre_bien,
    -- derive quand on SAIT ; sinon on garde ce que Hektor disait. Sans ce repli,
    -- 4 961 mandants devenaient proprietaires parce que l'index d'archive a
    -- oublie leur numero de mandat -- ce serait reecrire l'histoire.
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
-- ⚠ LES DEUX ABSENCES. Le registre les GARDE ; l'ecran ne les montre pas.
WHERE r.present_in_hektor
  AND r.retire_le IS NULL

UNION ALL

-- ② LES ACQUEREURS -- encore lus dans la table de nuit.
--   ⚠ ET CE N'EST PLUS POUR LA RAISON QUE J'AVAIS DONNEE. J'avais ecrit que les
--     projeter « perdrait 791 lignes » : c'etait FAUX, ma mesure sautait en
--     silence 11 151 affaires sur 30 358 (acquereurs_json est tantot une LISTE,
--     tantot un OBJET SEUL, et mon code ecartait la seconde forme).
--     LE VRAI CHIFFRE : le ledger connait 16 080 des 16 253 couples -- 98,9 %,
--     CO-ACQUEREURS COMPRIS. La projection EST faisable.
--     Elle reste a faire, avec les 180 compromis manquants a comprendre d'abord.
SELECT
    c.relation_key, c.hektor_contact_id, c.hektor_annonce_id, c.app_dossier_id,
    c.numero_dossier, c.numero_mandat, c.titre_bien, c.role_contact,
    c.contact_date_maj, c.relation_source, c.transaction_type, c.transaction_id,
    c.transaction_state, c.transaction_date, c.transaction_amount,
    c.is_active_annonce, c.last_seen_at::text, c.refreshed_at::text
FROM public.app_contact_relation_current c
WHERE c.role_contact LIKE 'acquereur%';

COMMENT ON VIEW public.app_contact_relations_current IS
  'LES LIENS D''UN CONTACT (30/09/2026). Nom et 18 colonnes inchanges : le front '
  'ne bouge pas. Source : app_relation, le registre durable. LE REGISTRE PORTE '
  'TOUT, CETTE VUE FILTRE -- elle exclut ce que le miroir ne ramene plus '
  '(present_in_hektor) et ce qui a ete retire volontairement (retire_le), et les '
  'lignes restent au registre dans les deux cas. Les acquereurs viennent encore '
  'de la table de nuit ; leur projection depuis app_affaire_ledger est faisable '
  '(98,9 % des couples) et reste a faire.';
