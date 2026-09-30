-- ═══════════════════════════════════════════════════════════════════════════════
-- ⚠⚠ URGENT (2/2) -- LA VUE DES LIENS MET 7,6 SECONDES SUR UN VRAI CONTACT
-- ═══════════════════════════════════════════════════════════════════════════════
-- 30/09/2026. A APPLIQUER APRES `patch_liens_index_urgent`. Aucune donnee touchee.
--
-- ─── POURQUOI UN SECOND CORRECTIF ───────────────────────────────────────────────
-- L'index d'expression (patch precedent) etait necessaire mais PAS SUFFISANT, et
-- je ne l'ai vu qu'en refaisant la mesure SUR UN VRAI CAS :
--
--     contact SANS aucun lien (10000023)   985 ms -> 4 ms     ✅ repare
--     contact AVEC 74 liens  (10172148)              7 586 ms  ⛔ PAS repare
--
-- ⚠⚠ MON PREMIER ESSAI NE PROUVAIT RIEN. Sur un contact sans lien, Postgres
--    n'execute jamais la partie couteuse -- le plan la marque « never executed ».
--    J'ai cru avoir repare parce que j'avais mesure LE CAS OU IL N'Y A RIEN A
--    FAIRE. C'est exactement « un echantillon pris dans l'ordre n'est pas un
--    echantillon », en version temps.
--
-- ─── LA CAUSE ───────────────────────────────────────────────────────────────────
-- La vue cherchait le bien dans un CTE `bien` qui reunit les trois index
-- (parc, archive, historique) et les DEDUPLIQUE par DISTINCT ON. Postgres doit
-- donc MATERIALISER ET TRIER 57 682 LIGNES -- a chaque ouverture de fiche, meme
-- pour n'en lire que 74.
--     Sort Method: external merge  Disk: 4168kB
--     Seq Scan on app_dossier_current ... 3 728 ms
--
-- ─── LA REPARATION : ON CONVERTIT LE PETIT COTE, PAS LE GRAND ───────────────────
-- Deux changements, et le second est le vrai :
--   ① le CTE devient un LEFT JOIN LATERAL : on ne cherche QUE les biens des
--      liens qu'on lit (74), au lieu de preparer les 57 682.
--   ② la jointure compare `d.hektor_annonce_id = r.hektor_annonce_id::bigint`
--      -- on convertit LA VALEUR (une seule), pas LA COLONNE (57 682). Les trois
--      index existants (tous sur le bigint) redeviennent utilisables.
--      ⚠ Verifie avant d'oser : 132 628 valeurs sur 132 628 sont numeriques.
--
-- MESURE, meme requete, meme contact charge :
--     7 586 ms  ->  27 ms        ~280 fois plus rapide
--     et les trois « Seq Scan » deviennent trois « Index Scan ».
--
-- ─── ET LE CONTENU NE BOUGE PAS D'UNE LIGNE ─────────────────────────────────────
-- Compare en BEGIN/ROLLBACK, la vue entiere, colonne par colonne :
--     163 765 avant · 163 765 apres · 0 perdue · 0 ajoutee
-- (`ORDER BY rang LIMIT 1` rend exactement ce que faisait `DISTINCT ON` : le
--  parc d'abord, puis l'archive, puis l'historique.)
--
-- ─── LA LECON, ET ELLE EST DEUX FOIS LA MEME AUJOURD'HUI ────────────────────────
-- Ce matin : un verrou de 8 min 30 parce que « additif et reversible » qualifie
-- ce qu'on ECRIT, pas ce que ca COUTE.
-- Cet apres-midi : une vue juste mais inutilisable, parce que « le compte est
-- juste » ne dit RIEN du temps.
-- ➡ TOUTE VUE QUE L'ECRAN INTERROGE SE MESURE AVEC `EXPLAIN ANALYZE` SUR LA
--   REQUETE REELLE DU FRONT, ET SUR UN CAS QUI RAMENE DES LIGNES.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
-- Rejouer `patch_liens_deux_absences_2026-09-30.sql` (la version a CTE).
-- Elle rend le meme resultat -- en 7,6 secondes.
-- ═══════════════════════════════════════════════════════════════════════════════

DROP VIEW IF EXISTS public.app_contact_relations_current;

CREATE VIEW public.app_contact_relations_current AS

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
-- ⚠ LATERAL, PAS UN CTE : on ne cherche QUE les biens des liens qu'on lit.
--   Et la conversion porte sur LA VALEUR (`r.hektor_annonce_id::bigint`), pas
--   sur la colonne des tables de biens -- sinon leurs index sont inutilisables.
LEFT JOIN LATERAL (
    SELECT numero_dossier, numero_mandat, titre_bien, au_parc
      FROM (
        SELECT numero_dossier, numero_mandat, titre_bien, true AS au_parc, 1 AS rang
          FROM public.app_dossiers_current d
         WHERE d.hektor_annonce_id = r.hektor_annonce_id::bigint
        UNION ALL
        SELECT numero_dossier, numero_mandat, titre_bien, false, 2
          FROM public.app_archive_annonce_index_current a
         WHERE a.hektor_annonce_id = r.hektor_annonce_id::bigint
        UNION ALL
        SELECT numero_dossier, numero_mandat, titre_bien, false, 3
          FROM public.app_historical_annonce_index_current h
         WHERE h.hektor_annonce_id = r.hektor_annonce_id::bigint
      ) s
     ORDER BY rang       -- le parc d'abord, puis l'archive, puis l'historique
     LIMIT 1
) b ON true
-- ⚠ LES DEUX ABSENCES. Le registre les GARDE ; l'ecran ne les montre pas.
WHERE r.present_in_hektor
  AND r.retire_le IS NULL

UNION ALL

-- ② LES ACQUEREURS -- encore lus dans la table de nuit.
--   Leur projection depuis app_affaire_ledger est FAISABLE (0 perdue, +1 778
--   gagnees, mesure du 30/09) mais SUSPENDUE : sa premiere version met 7,6 s,
--   le meme defaut que celui repare ici. A reprendre avec un LATERAL.
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
  'TOUT, CETTE VUE FILTRE (present_in_hektor, retire_le). Le bien est cherche par '
  'LATERAL avec conversion du PETIT cote -- un CTE + DISTINCT ON materialisait '
  '57 682 lignes a chaque ouverture de fiche : 7,6 s au lieu de 27 ms.';
