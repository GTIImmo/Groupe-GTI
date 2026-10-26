-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ TYPES, CHANTIER 3 — LA PIÈCE 5 : les acquéreurs d'un contact lus dans NOTRE registre des transactions   26/10/2026
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §13 et §14 ; audit d'origine : §58 point 2 de
-- notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md. Décision du 30/09 : « le registre des liens PROJETTERA les
-- acquéreurs depuis le registre des transactions ; il ne les stockera pas ».
--
-- CE QUE CE PATCH FAIT :
--   1. deux index ADDITIFS sur app_affaire_ledger : le principal par son numéro EN TEXTE (même montage que
--      idx_app_relation_contact_texte) ; les 2 447 transactions à PLUSIEURS acquéreurs (seules à déplier) ;
--   2. la vue app_contact_relations_current : la branche 1 (mandants / propriétaires, registre des liens) est gardée AU
--      CARACTÈRE PRÈS ; la branche des ACQUÉREURS lit le registre des transactions au lieu de la table de nuit — mêmes 18
--      colonnes, mêmes types ; deux morceaux (le principal, les co-acquéreurs) pour que la lecture par contact ET par bien
--      passe par un index.
-- Mesures du 26/10 : 35 005 liens de la nuit retrouvés sur 35 005 (+3 offres d'essai nées dans l'app), 0 clé en double ;
-- écarts : numéro de mandat 20 (celui DE LA TRANSACTION, le juste), date de mise à jour du contact 1 973, n° de dossier 4,
-- titre 1. Le montant d'une OFFRE reste masqué (NULL), comme la nuit le fait — Frédéric n'a pas tranché (Q1), une ligne à changer.
-- La table de nuit n'est pas touchée (elle sert encore aux types de l'annuaire).
-- ⛔ RIEN N'EST ÉCRIT CHEZ HEKTOR. Retour arrière : _INVERSE.sql (la vue d'avant, à l'octet, et les deux index retirés).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

create index if not exists idx_app_affaire_ledger_contact_texte
    on public.app_affaire_ledger (((app_contact_id)::text))
    where (present_in_hektor and (app_contact_id is not null));
create index if not exists idx_app_affaire_ledger_plusieurs_acquereurs
    on public.app_affaire_ledger (app_affaire_id)
    where (present_in_hektor and (((case when (jsonb_typeof(acquereurs_json) = 'array'::text)
                                         then jsonb_array_length(acquereurs_json) else 0 end) > 1)
                                  or (app_contact_id is null)));

DO $vue$
DECLARE
    d       text := pg_get_viewdef('public.app_contact_relations_current'::regclass);
    ancre   text := E'\nUNION ALL\n SELECT c.relation_key,';
    neuve   text := $b$ SELECT (('aff_'::text || (l.app_affaire_id)::text) || '_'::text) || (l.app_contact_id)::text AS relation_key,
    (l.app_contact_id)::text AS hektor_contact_id,
    (l.hektor_annonce_id)::text AS hektor_annonce_id,
    l.app_dossier_id,
    b.numero_dossier,
    l.numero_mandat,
    b.titre_bien,
    'acquereur_'::text || l.kind AS role_contact,
    k.date_maj AS contact_date_maj,
    'registre_transactions'::text AS relation_source,
    l.kind AS transaction_type,
    l.hektor_affaire_id AS transaction_id,
        CASE
            WHEN (l.kind = 'vente'::text) THEN 'vente'::text
            ELSE l.state
        END AS transaction_state,
    l.date AS transaction_date,
        CASE
            WHEN (l.kind = 'offre'::text) THEN NULL::text
            ELSE l.montant
        END AS transaction_amount,
    (NOT (EXISTS ( SELECT 1
           FROM app_archive_annonce_index_current x
          WHERE (x.hektor_annonce_id = l.hektor_annonce_id)))) AS is_active_annonce,
    (l.last_seen_at)::text AS last_seen_at,
    (l.last_seen_at)::text AS refreshed_at
   FROM ((app_affaire_ledger l
     LEFT JOIN app_contact_current k ON ((k.hektor_contact_id = (l.app_contact_id)::text)))
     LEFT JOIN LATERAL ( SELECT s.numero_dossier,
            s.titre_bien
           FROM ( SELECT d.numero_dossier,
                    d.titre_bien,
                    1 AS rang
                   FROM app_dossiers_current d
                  WHERE (d.hektor_annonce_id = l.hektor_annonce_id)
                UNION ALL
                 SELECT a.numero_dossier,
                    a.titre_bien,
                    2
                   FROM app_archive_annonce_index_current a
                  WHERE (a.hektor_annonce_id = l.hektor_annonce_id)
                UNION ALL
                 SELECT h.numero_dossier,
                    h.titre_bien,
                    3
                   FROM app_historical_annonce_index_current h
                  WHERE (h.hektor_annonce_id = l.hektor_annonce_id)) s
          ORDER BY s.rang
         LIMIT 1) b ON (true))
  WHERE (l.present_in_hektor AND (l.app_contact_id IS NOT NULL))
UNION ALL
 SELECT (('aff_'::text || (l.app_affaire_id)::text) || '_'::text) || (e.value ->> 'app_contact_id'::text) AS relation_key,
    (e.value ->> 'app_contact_id'::text) AS hektor_contact_id,
    (l.hektor_annonce_id)::text AS hektor_annonce_id,
    l.app_dossier_id,
    b.numero_dossier,
    l.numero_mandat,
    b.titre_bien,
    'acquereur_'::text || l.kind AS role_contact,
    k.date_maj AS contact_date_maj,
    'registre_transactions'::text AS relation_source,
    l.kind AS transaction_type,
    l.hektor_affaire_id AS transaction_id,
        CASE
            WHEN (l.kind = 'vente'::text) THEN 'vente'::text
            ELSE l.state
        END AS transaction_state,
    l.date AS transaction_date,
        CASE
            WHEN (l.kind = 'offre'::text) THEN NULL::text
            ELSE l.montant
        END AS transaction_amount,
    (NOT (EXISTS ( SELECT 1
           FROM app_archive_annonce_index_current x
          WHERE (x.hektor_annonce_id = l.hektor_annonce_id)))) AS is_active_annonce,
    (l.last_seen_at)::text AS last_seen_at,
    (l.last_seen_at)::text AS refreshed_at
   FROM (((app_affaire_ledger l
     CROSS JOIN LATERAL jsonb_array_elements(
        CASE
            WHEN (jsonb_typeof(l.acquereurs_json) = 'array'::text) THEN l.acquereurs_json
            ELSE '[]'::jsonb
        END) e(value))
     LEFT JOIN app_contact_current k ON ((k.hektor_contact_id = (e.value ->> 'app_contact_id'::text))))
     LEFT JOIN LATERAL ( SELECT s.numero_dossier,
            s.titre_bien
           FROM ( SELECT d.numero_dossier,
                    d.titre_bien,
                    1 AS rang
                   FROM app_dossiers_current d
                  WHERE (d.hektor_annonce_id = l.hektor_annonce_id)
                UNION ALL
                 SELECT a.numero_dossier,
                    a.titre_bien,
                    2
                   FROM app_archive_annonce_index_current a
                  WHERE (a.hektor_annonce_id = l.hektor_annonce_id)
                UNION ALL
                 SELECT h.numero_dossier,
                    h.titre_bien,
                    3
                   FROM app_historical_annonce_index_current h
                  WHERE (h.hektor_annonce_id = l.hektor_annonce_id)) s
          ORDER BY s.rang
         LIMIT 1) b ON (true))
  WHERE (l.present_in_hektor AND ((
        CASE
            WHEN (jsonb_typeof(l.acquereurs_json) = 'array'::text) THEN jsonb_array_length(l.acquereurs_json)
            ELSE 0
        END > 1) OR (l.app_contact_id IS NULL)) AND (e.value ? 'app_contact_id'::text) AND ((e.value ->> 'app_contact_id'::text) IS DISTINCT FROM (l.app_contact_id)::text))$b$;
    p       int;
BEGIN
    IF position('registre_transactions' in d) > 0 THEN
        RAISE NOTICE '%', 'La vue lit deja le registre des transactions : rien a faire.';
        RETURN;
    END IF;
    IF md5(d) <> 'acf77be8aefe5d619f904a037871eb54' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue app_contact_relations_current a change depuis le 26/10 (empreinte %s au lieu de acf77be8...) ; rien n''est ecrit.', md5(d));
    END IF;
    IF (length(d) - length(replace(d, E'\nUNION ALL\n', ''))) / length(E'\nUNION ALL\n') <> 1
       OR (length(d) - length(replace(d, ancre, ''))) / length(ancre) <> 1 THEN
        RAISE EXCEPTION '%', 'ARRET : la branche des acquereurs n''est pas trouvee une seule fois ; rien n''est ecrit.';
    END IF;
    p := position(ancre in d);
    d := left(d, p - 1) || E'\nUNION ALL\n' || neuve;
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as ' || d;
END
$vue$;

SELECT 1 AS "#", 'les deux index existent' AS controle,
       CASE WHEN to_regclass('public.idx_app_affaire_ledger_contact_texte') IS NOT NULL
             AND to_regclass('public.idx_app_affaire_ledger_plusieurs_acquereurs') IS NOT NULL THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'la vue lit le registre des transactions, et reste security_invoker',
       CASE WHEN position('registre_transactions' in pg_get_viewdef('public.app_contact_relations_current'::regclass)) > 0
             AND position('app_contact_relation_current' in pg_get_viewdef('public.app_contact_relations_current'::regclass)) = 0
             AND (SELECT reloptions FROM pg_class WHERE oid = 'public.app_contact_relations_current'::regclass) @> array['security_invoker=true']
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'les liens acquereurs : 35 005 attendus le 26/10 (+3 offres d''essai)',
       (SELECT CASE WHEN count(*) BETWEEN 34500 AND 36000 THEN 'OK (' || count(*) || ')' ELSE '⚠ A REGARDER (' || count(*) || ')' END
          FROM public.app_contact_relations_current WHERE role_contact LIKE 'acquereur%')
ORDER BY 1;

COMMIT;
