-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE de patch_fiche_contact_vitesse_2026-10-26.sql                                 26/10/2026
-- Il ne retire QUE sa part : la vue revient à l'octet (empreinte 84ca1b2e, celle du 26/10 13:21), la règle des liens
-- revient à is_app_user_active(), les deux colonnes texte et leurs index sont retirés. Rien d'autre n'est touché
-- (la table des parties reste, avec ses lignes : elle est hors de ce patch).
-- ⚠ Retirer une colonne ne réécrit pas la table (instantané) ; lock_timeout 5 s par prudence.
-- ⛔ RIEN chez Hektor.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
SET LOCAL lock_timeout = '5s';

-- ── 1. LA VUE D'AVANT (la vue d'abord : les colonnes ne peuvent pas partir tant qu'elle les lit) ─────────
DO $vue$
DECLARE
    d       text := pg_get_viewdef('public.app_contact_relations_current'::regclass);
    neuve_r text := 'r.app_contact_id_texte AS hektor_contact_id';
    neuve_p text := 'p.app_contact_id_texte AS hektor_contact_id';
BEGIN
    IF position('app_contact_id_texte' in d) = 0 THEN
        RAISE NOTICE '%', 'La vue ne lit pas les colonnes texte : rien a defaire sur la vue.';
        RETURN;
    END IF;
    IF (length(d) - length(replace(d, neuve_r, ''))) / length(neuve_r) <> 1
       OR (length(d) - length(replace(d, neuve_p, ''))) / length(neuve_p) <> 1 THEN
        RAISE EXCEPTION '%', 'ARRET : la vue a change depuis le patch (ancres absentes ou en double) ; rien n''est ecrit.';
    END IF;
    d := replace(d, neuve_r, '(r.app_contact_id)::text AS hektor_contact_id');
    d := replace(d, neuve_p, '(p.app_contact_id)::text AS hektor_contact_id');
    IF md5(d) <> '84ca1b2e8f8ef513f0fdb166469b7b87' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue reconstituee n''a pas l''empreinte d''avant (%s) ; rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as ' || rtrim(rtrim(d), ';');
END
$vue$;

-- ── 2. LA RÈGLE D'AVANT ─────────────────────────────────────────────────────────────────────────────────
alter policy app_relation_select_active_users on public.app_relation
    using (public.is_app_user_active());

-- ── 3. LES COLONNES ET LEURS INDEX ──────────────────────────────────────────────────────────────────────
drop index if exists public.idx_app_relation_contact_id_texte;
drop index if exists public.idx_app_affaire_partie_contact_id_texte;
alter table public.app_relation       drop column if exists app_contact_id_texte;
alter table public.app_affaire_partie drop column if exists app_contact_id_texte;

COMMIT;

SELECT 1 AS "#", 'la vue est revenue a l''octet (84ca1b2e)' AS controle,
       CASE WHEN md5(pg_get_viewdef('public.app_contact_relations_current'::regclass)) = '84ca1b2e8f8ef513f0fdb166469b7b87'
             AND (SELECT reloptions FROM pg_class WHERE oid = 'public.app_contact_relations_current'::regclass) @> array['security_invoker=true']
            THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'la regle des liens est revenue a is_app_user_active()',
       (SELECT CASE WHEN pg_get_expr(polqual, polrelid) = 'is_app_user_active()' THEN 'OK' ELSE '⛔ ECHEC (' || pg_get_expr(polqual, polrelid) || ')' END
          FROM pg_policy WHERE polname = 'app_relation_select_active_users' AND polrelid = 'public.app_relation'::regclass)
UNION ALL SELECT 3, 'aucune trace des colonnes texte ni de leurs index',
       CASE WHEN NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attname = 'app_contact_id_texte' AND NOT attisdropped
                              AND attrelid IN ('public.app_relation'::regclass, 'public.app_affaire_partie'::regclass))
             AND to_regclass('public.idx_app_relation_contact_id_texte') IS NULL
             AND to_regclass('public.idx_app_affaire_partie_contact_id_texte') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'ce qui n''est pas a ce patch est intact (table des parties, ses lignes, ses index d''origine)',
       CASE WHEN to_regclass('public.app_affaire_partie') IS NOT NULL
             AND to_regclass('public.idx_app_affaire_partie_contact_texte') IS NOT NULL
             AND to_regclass('public.idx_app_relation_contact_texte') IS NOT NULL
             AND (SELECT count(*) FROM public.app_affaire_partie) > 100000 THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;
