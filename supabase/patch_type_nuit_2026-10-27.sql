-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ TYPES, ÉTAPE 2 — LA NUIT : LE CALCUL POUR TOUS, ET LA LIGNE DE SUIVI DE SON ÉTAPE          27/10/2026
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §43 et §46.
--
-- La nuit n'écrit plus le type (push_contacts_to_supabase.py, interrupteur APP_TYPE_PAR_NOS_REGISTRES) : une étape
-- de fin de bloc des contacts (« phase2 type des contacts depuis nos registres ») appelle cette fonction, qui remet le
-- type de CHAQUE contact de l'app d'après nos registres -- c'est ainsi qu'un geste fait DANS HEKTOR, que la nuit vient
-- d'écrire dans nos registres, arrive dans le type ; et qu'un contact NEUF (envoyé sans type, donc `[]`) reçoit le sien.
-- CE QUE CE PATCH FAIT :
--   1. app_recalculer_tous_les_types() : ensembliste (une lecture de la vue, ~2 s), MÊME RÈGLE que
--      app_type_depuis_nos_registres (rôles distincts, triés COLLATE "C") ; n'écrit que là où le type diffère ;
--      interne (clé de service seulement) ;
--   2. la ligne `supabase.type_contacts` du registre des tâches, COPIÉE de sa sœur `hektor.carnet_acquereurs` (étape
--      facultative du même bloc) : sans elle, le battement de l'étape partirait dans le vide (leçon du 13/10).
-- ⛔ RIEN CHEZ HEKTOR. Le patch n'écrit le type de personne : seule la fonction, à son appel, le fait.
-- Retour arrière : patch_type_nuit_2026-10-27_INVERSE.sql · Contrôle : _REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

CREATE OR REPLACE FUNCTION public.app_recalculer_tous_les_types()
RETURNS integer LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $f$
DECLARE n integer := 0;
BEGIN
    -- ⚠ LA MÊME RÈGLE que app_type_depuis_nos_registres : un écart entre les deux serait un type qui change
    --   selon qu'on le calcule au geste ou la nuit. La répétition le vérifie sur tous les contacts.
    WITH v AS (
        SELECT d.c, jsonb_agg(d.r ORDER BY d.r COLLATE "C") AS roles
          FROM (SELECT DISTINCT x.hektor_contact_id AS c, x.role_contact AS r
                  FROM public.app_contact_relations_current x) d
         GROUP BY d.c)
    UPDATE public.app_contact_current k
       SET relation_roles_json = coalesce(v.roles, '[]'::jsonb)
      FROM public.app_contact_current k2
      LEFT JOIN v ON v.c = k2.hektor_contact_id
     WHERE k.hektor_contact_id = k2.hektor_contact_id
       AND k.relation_roles_json IS DISTINCT FROM coalesce(v.roles, '[]'::jsonb);
    GET DIAGNOSTICS n = ROW_COUNT;
    RETURN n;
END
$f$;
REVOKE ALL ON FUNCTION public.app_recalculer_tous_les_types() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.app_recalculer_tous_les_types() TO service_role;

-- la ligne de suivi, copiée de sa sœur (règle : partir d'une ligne existante)
DO $reg$
DECLARE soeur jsonb;
BEGIN
    SELECT to_jsonb(w) INTO soeur FROM public.app_worker_registry w WHERE w.worker_key = 'hektor.carnet_acquereurs';
    IF soeur IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : la ligne soeur hektor.carnet_acquereurs est introuvable ; tout est annule.';
    END IF;
    INSERT INTO public.app_worker_registry
    SELECT * FROM jsonb_populate_record(NULL::public.app_worker_registry, soeur || jsonb_build_object(
        'worker_key',   'supabase.type_contacts',
        'worker_name',  'Type des contacts depuis nos registres',
        'worker_role',  'Remet le type de chaque contact de l''app d''apres nos registres (liens, transactions), en fin du bloc des contacts : un geste fait dans Hektor y arrive, un contact neuf recoit le sien. Le geste de l''app, lui, le pose au clic.',
        'script_path',  'phase2/sync/recalculer_types_contacts.py',
        'command_hint', '.venv\Scripts\python.exe phase2\sync\recalculer_types_contacts.py',
        'source_notes', 'Pose le 27/10/2026 (etape 2 des types, note des types §46). Inerte tant que APP_TYPE_PAR_NOS_REGISTRES n''est pas a 1.',
        'dependencies_json', '["supabase.push_contacts", "supabase.propagate_contact_ids"]'::jsonb,
        'expected_max_runtime_minutes', 5,
        'created_at', now(), 'updated_at', now(),
        'last_run_at', NULL, 'last_status', NULL, 'last_success_at', NULL, 'last_error', NULL,
        'last_run_host', NULL, 'last_duration_ms', NULL))
    ON CONFLICT (worker_key) DO NOTHING;
END
$reg$;

COMMIT;
