-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — ⑧ types : la table des parties                                          26/10/2026
-- 1. la vue des liens d'un contact reprend sa définition d'avant À L'OCTET (empreinte acf77be8 vérifiée) ;
-- 2. les déclencheurs, les fonctions, la vue de la sentinelle, la table et son journal sont retirés.
-- La table est DÉRIVÉE des listes du registre : rien n'est perdu. ⚠ Retirer AUSSI la sentinelle du moniteur
-- (data.affaire_partie_ecart, monitoring/check_gti_health.py) : sinon elle lira une vue absente (un rouge).
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
    IF position('app_affaire_partie' in d) = 0 THEN
        RAISE NOTICE '%', 'La vue ne lit pas la table des parties : rien a retirer.';
        RETURN;
    END IF;
    p := position(E'\nUNION ALL\n' in d);
    IF p = 0 THEN
        RAISE EXCEPTION '%', 'ARRET : frontiere des branches introuvable ; rien n''est ecrit.';
    END IF;
    d := left(d, p - 1) || ancienne;
    IF md5(d) <> 'acf77be8aefe5d619f904a037871eb54' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue reconstituee n''a pas l''empreinte d''avant (%s) ; rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as ' || rtrim(rtrim(d), ';');
END
$vue$;

drop trigger if exists app_affaire_partie_apres_insert on public.app_affaire_ledger;
drop trigger if exists app_affaire_partie_apres_update on public.app_affaire_ledger;
drop trigger if exists app_affaire_partie_apres_delete on public.app_affaire_ledger;
drop view if exists public.app_v_affaire_partie_ecarts;
drop function if exists public.app_affaire_partie_reconstruire();
drop function if exists public.app_affaire_partie_suivre();
drop function if exists public.app_affaire_partie_calculer(public.app_affaire_ledger);
drop table if exists public.app_affaire_partie;
drop table if exists public.app_affaire_partie_erreur;

COMMIT;

SELECT 1 AS "#", 'la vue a retrouve sa definition d''avant' AS controle,
       CASE WHEN md5(pg_get_viewdef('public.app_contact_relations_current'::regclass)) = 'acf77be8aefe5d619f904a037871eb54' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'plus aucun declencheur sur le registre',
       CASE WHEN (SELECT count(*) FROM pg_trigger WHERE tgrelid = 'public.app_affaire_ledger'::regclass AND tgname LIKE 'app_affaire_partie_%') = 0 THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'la table et son journal sont retires',
       CASE WHEN to_regclass('public.app_affaire_partie') IS NULL AND to_regclass('public.app_affaire_partie_erreur') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;
