-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ TYPES, P2 — LA FICHE CONTACT : UN BIEN = UNE LIGNE AVEC TOUS SES RÔLES        27/10/2026
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §31.
--
-- CE QUE CE PATCH FAIT, ET RIEN D'AUTRE :
--   la vue `app_contact_relations_current` gagne DEUX colonnes À LA FIN :
--     origine              ('vente' = l'acheteur devenu propriétaire par la vente ; lu dans app_relation)
--     proprietaire_depuis  (la date de cette vente ; lue dans app_relation)
--   NULL pour les lignes du registre des transactions (la 2e branche).
--   Les 18 colonnes d'avant gardent leur nom, leur type et leur ordre ; les lignes sont les mêmes.
--   `security_invoker`, le propriétaire et les droits sont gardés (create or replace).
-- Pourquoi : l'écran saura écrire « Propriétaire depuis le 25/09/2026 » (décision de Frédéric du 27/10).
-- Lecteurs vérifiés le 27/10 : le front (select * pour la fiche ; colonnes NOMMÉES ailleurs), deux fonctions
--   (colonnes nommées), aucune vue dépendante, la vue ne descend pas la nuit (VUES_NON_DESCENDUES).
-- ⛔ RIEN N'EST ÉCRIT DANS UNE TABLE, RIEN CHEZ HEKTOR.
-- Le bloc vérifie l'empreinte de la vue et S'ARRÊTE si elle a changé depuis l'audit.
-- Retour arrière : patch_p2_fiche_un_bien_tous_roles_2026-10-27_INVERSE.sql
-- Contrôle       : patch_p2_fiche_un_bien_tous_roles_2026-10-27_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $vue$
DECLARE
    d   text := pg_get_viewdef('public.app_contact_relations_current'::regclass);
    -- ⚠ ancres sur UNE SEULE LIGNE (leçon 30) : un retour chariot ne peut pas s'y glisser
    a1  text := 'r.last_seen_at AS refreshed_at';
    a2  text := '(l.last_seen_at)::text AS refreshed_at';
    n1  int;
    n2  int;
    nb  int;
BEGIN
    IF position('AS proprietaire_depuis' in d) > 0 OR position('r.proprietaire_depuis' in d) > 0 THEN
        RAISE NOTICE '%', 'La vue porte deja les deux colonnes : rien a faire.';
        RETURN;
    END IF;
    IF md5(d) <> 'd4350c631503f1ecedf99d28bee16c04' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue app_contact_relations_current a change depuis l''audit du 27/10 (empreinte %s au lieu de d4350c63...) ; rien n''est ecrit.', md5(d));
    END IF;
    d  := replace(d, chr(13), '');
    n1 := (length(d) - length(replace(d, a1, ''))) / length(a1);
    n2 := (length(d) - length(replace(d, a2, ''))) / length(a2);
    IF n1 <> 1 OR n2 <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : ancres trouvees %s et %s fois (1 et 1 attendues) ; rien n''est ecrit.', n1, n2);
    END IF;
    d := replace(d, a1, a1 || ',' || chr(10) || '    r.origine,' || chr(10) || '    r.proprietaire_depuis');
    d := replace(d, a2, a2 || ',' || chr(10) || '    NULL::text AS origine,' || chr(10) || '    NULL::text AS proprietaire_depuis');
    d := rtrim(rtrim(d), ';');
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as ' || d;

    SELECT count(*) INTO nb FROM pg_attribute
     WHERE attrelid = 'public.app_contact_relations_current'::regclass AND attnum > 0 AND NOT attisdropped;
    IF nb <> 20 THEN
        RAISE EXCEPTION '%', format('ARRET : la vue a %s colonnes (20 attendues) ; tout est annule.', nb);
    END IF;

    EXECUTE format('comment on view public.app_contact_relations_current is %L',
        coalesce(obj_description('public.app_contact_relations_current'::regclass), '')
        || ' -- P2 (27/10/2026) : + 2 colonnes A LA FIN, origine et proprietaire_depuis (app_relation ; NULL pour les lignes'
        || ' du registre des transactions). Les 18 premieres inchangees.');
END
$vue$;

COMMIT;
