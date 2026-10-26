-- ═══════════════════════════════════════════════════════════════════════════
-- LA FICHE CONTACT S'OUVRAIT EN ~4 s -- LE REMÈDE « COMPLET »                                  26/10/2026
-- Décision de Frédéric (26/10 après-midi) : « non, première idée » (la colonne texte sur les DEUX tables + la règle).
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md §19 (audit), §20 (ce patch).
--
-- LA CAUSE (mesurée sous le compte de Frédéric, pas en service_role) : la fiche lit
--   app_contact_relations_current?hektor_contact_id=eq.<n°> ; la vue fabrique ce champ par CONVERSION
--   (app_contact_id::text). Sous RLS une conversion n'est pas « leakproof » : Postgres applique la règle AVANT,
--   sur TOUTES les lignes -> lecture complète. Et la règle de app_relation, is_app_user_active(), n'est pas
--   enveloppée : elle est appelée 132 879 fois. Liens 2 175 ms, parties 274-437 ms, fiche ~2,4 s.
-- LE REMÈDE :
--   1. une colonne app_contact_id_texte, CALCULÉE PAR LA BASE (generated ... stored), sur app_relation et
--      app_affaire_partie, avec son index. Personne n'écrit dedans ; elle ne peut pas différer du vrai numéro.
--   2. la règle de app_relation enveloppée : (select is_app_user_active()) -- MÊME SENS, une fois par requête.
--   3. la vue lit ces colonnes au lieu de convertir. MÊMES colonnes, MÊMES types, MÊMES lignes (prouvé sur
--      copies, EXCEPT ALL dans les deux sens, admin et commercial : 0 / 0).
-- CE QUI NE CHANGE PAS : la nuit, le worker, les fonctions de l'app (service_role ou propriétaire : la RLS ne les
--   concerne pas ; tous les écrivains NOMMENT leurs colonnes) ; l'écran ; qui voit quoi. ⛔ RIEN chez Hektor.
-- ⚠ LA POSE RÉÉCRIT app_relation (94 Mo) : verrou de quelques secondes -> EN JOURNÉE, JAMAIS pendant le run de nuit.
--   lock_timeout 5 s : si la table est occupée, le patch S'ARRÊTE au lieu de faire attendre tout le monde.
-- Retour arrière : _INVERSE.sql (la vue d'avant à l'octet, la règle d'avant, les colonnes retirées).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '300s';

-- ── 0. LA GARDE : la vue est celle posée le 26/10 à 13:21 (ou ce patch est déjà passé) ──────────────────
DO $garde$
DECLARE
    d text := pg_get_viewdef('public.app_contact_relations_current'::regclass);
BEGIN
    IF position('app_contact_id_texte' in d) = 0 AND md5(d) <> '84ca1b2e8f8ef513f0fdb166469b7b87' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue app_contact_relations_current a change depuis le 26/10 13:21 (empreinte %s au lieu de 84ca1b2e...) ; rien n''est ecrit.', md5(d));
    END IF;
END
$garde$;

-- ── 1. LA COLONNE TEXTE DU REGISTRE DES LIENS ───────────────────────────────────────────────────────────
alter table public.app_relation
    add column if not exists app_contact_id_texte text generated always as ((app_contact_id)::text) stored;
comment on column public.app_relation.app_contact_id_texte is
  '26/10 : NOTRE numero de contact EN TEXTE, calcule par la base (personne n''ecrit dedans). Sert la vue app_contact_relations_current : sous RLS, filtrer sur une conversion empeche l''index (2 175 ms -> < 1 ms). ⚠ hektor_contact_id porte le numero de HEKTOR.';
create index if not exists idx_app_relation_contact_id_texte
    on public.app_relation (app_contact_id_texte);

-- ── 2. LA COLONNE TEXTE DE LA TABLE DES PARTIES ─────────────────────────────────────────────────────────
alter table public.app_affaire_partie
    add column if not exists app_contact_id_texte text generated always as ((app_contact_id)::text) stored;
comment on column public.app_affaire_partie.app_contact_id_texte is
  '26/10 : NOTRE numero de contact EN TEXTE, calcule par la base (le declencheur n''ecrit pas dedans). Sert la vue app_contact_relations_current (meme raison que app_relation.app_contact_id_texte).';
create index if not exists idx_app_affaire_partie_contact_id_texte
    on public.app_affaire_partie (app_contact_id_texte) where (app_contact_id_texte is not null);

-- ── 3. LA RÈGLE DE app_relation, ENVELOPPÉE (même sens : le même utilisateur pour toute la requête) ──────
alter policy app_relation_select_active_users on public.app_relation
    using ((select public.is_app_user_active()));

-- ── 4. LA VUE LIT LES COLONNES TEXTE (deux remplacements, chacun trouvé UNE seule fois) ─────────────────
DO $vue$
DECLARE
    d       text := pg_get_viewdef('public.app_contact_relations_current'::regclass);
    ancre_r text := '(r.app_contact_id)::text AS hektor_contact_id';
    ancre_p text := '(p.app_contact_id)::text AS hektor_contact_id';
BEGIN
    IF position('app_contact_id_texte' in d) > 0 THEN
        RAISE NOTICE '%', 'La vue lit deja les colonnes texte : rien a faire.';
        RETURN;
    END IF;
    IF (length(d) - length(replace(d, ancre_r, ''))) / length(ancre_r) <> 1
       OR (length(d) - length(replace(d, ancre_p, ''))) / length(ancre_p) <> 1 THEN
        RAISE EXCEPTION '%', 'ARRET : une des deux ancres de la vue n''est pas trouvee une seule fois ; rien n''est ecrit.';
    END IF;
    d := replace(d, ancre_r, 'r.app_contact_id_texte AS hektor_contact_id');
    d := replace(d, ancre_p, 'p.app_contact_id_texte AS hektor_contact_id');
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as ' || rtrim(rtrim(d), ';');
END
$vue$;

analyze public.app_relation;
analyze public.app_affaire_partie;

COMMIT;

SELECT 1 AS "#", 'les deux colonnes existent et sont CALCULEES par la base' AS controle,
       CASE WHEN (SELECT count(*) FROM pg_attribute
                   WHERE attrelid IN ('public.app_relation'::regclass, 'public.app_affaire_partie'::regclass)
                     AND attname = 'app_contact_id_texte' AND attgenerated = 's' AND NOT attisdropped) = 2
            THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'liens : la colonne vaut notre numero sur CHAQUE ligne',
       (SELECT CASE WHEN count(*) FILTER (WHERE app_contact_id_texte IS DISTINCT FROM app_contact_id::text) = 0
                    THEN 'OK (' || count(*) || ' lignes)' ELSE '⛔ ECHEC' END FROM public.app_relation)
UNION ALL SELECT 3, 'parties : la colonne vaut notre numero sur CHAQUE ligne',
       (SELECT CASE WHEN count(*) FILTER (WHERE app_contact_id_texte IS DISTINCT FROM app_contact_id::text) = 0
                    THEN 'OK (' || count(*) || ' lignes)' ELSE '⛔ ECHEC' END FROM public.app_affaire_partie)
UNION ALL SELECT 4, 'les deux index existent',
       CASE WHEN to_regclass('public.idx_app_relation_contact_id_texte') IS NOT NULL
             AND to_regclass('public.idx_app_affaire_partie_contact_id_texte') IS NOT NULL THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'la regle des liens est enveloppee (une fois par requete)',
       (SELECT CASE WHEN pg_get_expr(polqual, polrelid) ~ '^\(?\s*SELECT is_app_user_active\(\)' THEN 'OK' ELSE '⛔ ECHEC (' || pg_get_expr(polqual, polrelid) || ')' END
          FROM pg_policy WHERE polname = 'app_relation_select_active_users' AND polrelid = 'public.app_relation'::regclass)
UNION ALL SELECT 6, 'la vue lit les colonnes texte, plus aucune conversion du numero, reste security_invoker',
       CASE WHEN position('r.app_contact_id_texte AS hektor_contact_id' in pg_get_viewdef('public.app_contact_relations_current'::regclass)) > 0
             AND position('p.app_contact_id_texte AS hektor_contact_id' in pg_get_viewdef('public.app_contact_relations_current'::regclass)) > 0
             AND position('::text AS hektor_contact_id' in pg_get_viewdef('public.app_contact_relations_current'::regclass)) = 0
             AND (SELECT reloptions FROM pg_class WHERE oid = 'public.app_contact_relations_current'::regclass) @> array['security_invoker=true']
            THEN 'OK (empreinte ' || left(md5(pg_get_viewdef('public.app_contact_relations_current'::regclass)), 8) || ')' ELSE '⛔ ECHEC' END
ORDER BY 1;
