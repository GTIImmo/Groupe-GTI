-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — ⑧ types, chantier 3 : la pièce 5                                     26/10/2026
-- La vue reprend sa définition d'avant À L'OCTET (empreinte acf77be8 vérifiée) : sa branche des acquéreurs relit la table de
-- nuit (app_contact_relation_current, jamais touchée). Puis les deux index sont retirés. Rien d'autre.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $vue$
DECLARE
    d         text := pg_get_viewdef('public.app_contact_relations_current'::regclass);
    ancienne  text := $b$
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
  WHERE (c.role_contact ~~ 'acquereur%'::text);$b$;
    p         int;
BEGIN
    IF position('registre_transactions' in d) = 0 THEN
        RAISE NOTICE '%', 'La vue ne lit pas le registre des transactions : rien a retirer.';
        RETURN;
    END IF;
    -- la branche 1 ne porte aucun « UNION ALL » en colonne 0 (ses UNION ALL sont indentes) : le premier est la frontiere.
    p := position(E'\nUNION ALL\n' in d);
    IF p = 0 THEN
        RAISE EXCEPTION '%', 'ARRET : frontiere des branches introuvable ; rien n''est ecrit.';
    END IF;
    d := left(d, p - 1) || ancienne;
    IF md5(d) <> 'acf77be8aefe5d619f904a037871eb54' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue reconstituee n''a pas l''empreinte d''avant (%s) -- la branche 1 a change par ailleurs ; rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as ' || rtrim(rtrim(d), ';');
END
$vue$;

drop index if exists public.idx_app_affaire_ledger_contact_texte;
drop index if exists public.idx_app_affaire_ledger_plusieurs_acquereurs;

SELECT 1 AS "#", 'la vue a retrouve sa definition d''avant' AS controle,
       CASE WHEN md5(pg_get_viewdef('public.app_contact_relations_current'::regclass)) = 'acf77be8aefe5d619f904a037871eb54' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'les deux index sont retires',
       CASE WHEN to_regclass('public.idx_app_affaire_ledger_contact_texte') IS NULL
             AND to_regclass('public.idx_app_affaire_ledger_plusieurs_acquereurs') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
