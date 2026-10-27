-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ TYPES, NOTAIRE — ÉTAPE 1 : LES NOTAIRES DANS LA VUE DES LIENS D'UN CONTACT                27/10/2026
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §40 et §41.
--
-- POURQUOI : la table des parties porte 23 351 rôles de notaire (notaire_vendeur, notaire_acquereur ; 1 330 personnes),
--   mais la 2e branche de `app_contact_relations_current` ne prenait que `p.role = 'acquereur'` : aucun notaire n'y
--   figurait, donc ni la fiche contact, ni (demain) le type, ni les invités d'un RDV ne les voyaient.
--   Décisions de Frédéric (27/10) : on ouvre le type Notaire ; « Notaire » en premier ; le notaire de l'annonce devient
--   invitable à un RDV.
-- CE QUE CE PATCH FAIT, ET RIEN D'AUTRE (3 remplacements d'une ligne chacun, dans la 2e branche) :
--   1. le filtre prend aussi les deux rôles de notaire ;
--   2. `role_contact` vaut le rôle de la partie pour un notaire (`notaire_vendeur` / `notaire_acquereur`) ; pour un
--      acheteur, il reste `acquereur_<genre>` ;
--   3. `relation_key` reçoit le suffixe `_<rôle>` POUR LES NOTAIRES SEULEMENT : la même personne a deux rôles sur la
--      même transaction 619 fois (le même notaire des deux côtés). Les clés des acheteurs restent IDENTIQUES.
--   Les lignes des acheteurs, des mandants et des propriétaires ne changent pas. Les 20 colonnes, security_invoker,
--   le propriétaire et les droits sont gardés (create or replace).
-- ⚠ CE QUE ÇA CHANGE À L'ÉCRAN DÈS LA POSE (à décider avec l'étape 3, l'écran) : la fiche contact d'un notaire liste ses
--   dossiers, avec le libellé brut du rôle tant que l'écran ne le traduit pas ; et les invités d'un RDV s'élargissent.
-- ⛔ RIEN N'EST ÉCRIT DANS UNE TABLE, RIEN CHEZ HEKTOR.
-- Le bloc vérifie l'empreinte de la vue (celle du 27/10, « transactions vivantes ») et S'ARRÊTE si elle a changé.
-- Retour arrière : patch_notaire_etape1_vue_2026-10-27_INVERSE.sql
-- Contrôle       : patch_notaire_etape1_vue_2026-10-27_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $vue$
DECLARE
    d   text := pg_get_viewdef('public.app_contact_relations_current'::regclass);
    -- ⚠ ancres et ajouts sur UNE SEULE LIGNE (leçon 30)
    f_avant  text := '(p.role = ''acquereur''::text)';
    f_apres  text := '(p.role = ANY (ARRAY[''acquereur''::text, ''notaire_vendeur''::text, ''notaire_acquereur''::text]))';
    r_avant  text := '''acquereur_''::text || l.kind';
    r_apres  text := 'CASE WHEN (p.role = ''acquereur''::text) THEN (''acquereur_''::text || l.kind) ELSE p.role END';
    k_avant  text := '|| (p.app_contact_id)::text) AS relation_key';
    k_apres  text := '|| (p.app_contact_id)::text) || CASE WHEN (p.role = ''acquereur''::text) THEN ''''::text ELSE (''_''::text || p.role) END AS relation_key';
    n1 int; n2 int; n3 int; nb int;
BEGIN
    IF position('notaire_vendeur' in d) > 0 THEN
        RAISE NOTICE '%', 'La vue porte deja les notaires : rien a faire.';
        RETURN;
    END IF;
    IF md5(d) <> '8c4d28d388a6325582013c5bfd08bc54' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue app_contact_relations_current a change depuis l''audit du 27/10 (empreinte %s au lieu de 8c4d28d3...) ; rien n''est ecrit.', md5(d));
    END IF;
    d  := replace(d, chr(13), '');
    n1 := (length(d) - length(replace(d, f_avant, ''))) / length(f_avant);
    n2 := (length(d) - length(replace(d, r_avant, ''))) / length(r_avant);
    n3 := (length(d) - length(replace(d, k_avant, ''))) / length(k_avant);
    IF n1 <> 1 OR n2 <> 1 OR n3 <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : ancres trouvees %s, %s et %s fois (1 attendue chacune) ; rien n''est ecrit.', n1, n2, n3);
    END IF;
    -- ⚠ L'ORDRE COMPTE : le filtre d'abord, car les deux autres ajouts contiennent le texte « (p.role = 'acquereur'::text) »
    d := replace(d, f_avant, f_apres);
    d := replace(d, r_avant, r_apres);
    d := replace(d, k_avant, k_apres);
    d := rtrim(rtrim(d), ';');
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as ' || d;

    SELECT count(*) INTO nb FROM pg_attribute
     WHERE attrelid = 'public.app_contact_relations_current'::regclass AND attnum > 0 AND NOT attisdropped;
    IF nb <> 20 THEN
        RAISE EXCEPTION '%', format('ARRET : la vue a %s colonnes (20 attendues) ; tout est annule.', nb);
    END IF;

    EXECUTE format('comment on view public.app_contact_relations_current is %L',
        coalesce(obj_description('public.app_contact_relations_current'::regclass), '')
        || ' -- NOTAIRE etape 1 (27/10/2026) : les roles notaire_vendeur / notaire_acquereur de la table des parties ;'
        || ' cle suffixee du role pour eux seuls.');
END
$vue$;

COMMIT;
