-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ TYPES, CHANTIER 1 — L'ACHETEUR « PROPRIÉTAIRE DEPUIS LA VENTE »              26/10/2026
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §7 et §8.
--
-- Décision D2 de Frédéric : « l'acheteur devient nouveau propriétaire daté de l'acte, sans être
-- mandant ». Hektor range l'acheteur d'une vente parmi les propriétaires ; la vue des liens d'un
-- contact en faisait un « mandant » parce que le bien porte un numéro de mandat.
--
-- CE QUE CE PATCH FAIT, EN TROIS GESTES :
--   1. deux colonnes ADDITIVES au registre des liens : `origine` ('vente') et `proprietaire_depuis`
--      (date de la vente). Personne ne les écrit encore : la nuit ne les pose qu'interrupteur allumé
--      (APP_RELATION_ACHETEUR_PROPRIETAIRE=1, phase2/sync/relation_ledger.py) ;
--   2. la vue `app_contact_relations_current` : un lien d'origine « vente » s'affiche « proprietaire ».
--      UNE ligne insérée dans le CASE de la branche 1, rien d'autre ; tant que `origine` est vide
--      partout, la vue rend EXACTEMENT les mêmes lignes ;
--   3. D5 c : les 55 liens NÉS DU FILET `app_relation_app_seule` (49 « acquéreur », 6 « mandant », tous
--      absents chez Hektor, tous invisibles à l'écran) sont marqués RETIRÉS — jamais supprimés
--      (delete-never). La nuit adopte ce retrait depuis la doublure (relation_ledger.py, « LES RETRAITS
--      DÉCIDÉS DANS L'APP »).
-- ⛔ RIEN N'EST ÉCRIT CHEZ HEKTOR.
-- Chaque bloc vérifie l'état qu'il attend et S'ARRÊTE s'il a changé depuis l'audit.
-- Retour arrière : patch_acheteur_proprietaire_2026-10-26_INVERSE.sql.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- ── 1. les deux colonnes ───────────────────────────────────────────────────
alter table public.app_relation add column if not exists origine text;
alter table public.app_relation add column if not exists proprietaire_depuis text;
comment on column public.app_relation.origine is
  '⑧ 26/10 : ''vente'' = lien ne d''une vente (l''acheteur, que Hektor range parmi les proprietaires) -- proprietaire, jamais mandant (D2). Pose par la nuit, relation_ledger.py.';
comment on column public.app_relation.proprietaire_depuis is
  '⑧ 26/10 : date de la vente qui a fait de l''acheteur le proprietaire (D2). Jamais reecrite.';

-- ── 2. la vue ──────────────────────────────────────────────────────────────
DO $vue$
DECLARE
    d       text := pg_get_viewdef('public.app_contact_relations_current'::regclass);
    ancre   text := $a$WHEN (NULLIF(btrim(COALESCE(b.numero_mandat, ''::text)), ''::text) IS NOT NULL) THEN 'mandant'::text$a$;
    ajout   text := $a$WHEN (r.origine = 'vente'::text) THEN 'proprietaire'::text$a$;
    n       int;
BEGIN
    IF position(ajout in replace(d, chr(13), '')) > 0 THEN
        RAISE NOTICE '%', 'La vue porte deja la regle : rien a faire.';
        RETURN;
    END IF;
    IF md5(d) <> '6c89ceb7052f335a11514c92c47d550f' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue app_contact_relations_current a change depuis l''audit du 26/10 (empreinte %s au lieu de 6c89ceb7...) ; rien n''est ecrit.', md5(d));
    END IF;
    d := replace(d, chr(13), '');
    n := (length(d) - length(replace(d, ancre, ''))) / length(ancre);
    IF n <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre est trouvee %s fois (1 attendue) ; rien n''est ecrit.', n);
    END IF;
    d := replace(d, ancre, ajout || chr(10) || '            ' || ancre);
    d := rtrim(rtrim(d), ';');
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as ' || d;
END
$vue$;

-- ── 3. D5 c : les 55 liens nés du filet, marqués retirés ────────────────────
DO $filet$
DECLARE
    ids bigint[] := array[132623,132624,132625,132626,132627,132628,132661,132662,132663,132664,132773,
                          132788,132800,132801,132802,132803,132804,132805,132806,132807,132808,132809,
                          132810,132811,132812,132813,132814,132815,132816,132828,132829,132830,132831,
                          132832,132833,132834,132835,132836,132837,132838,132839,132855,132856,132857,
                          132858,132859,132860,132861,132862,132863,132864,132865,132866,132867,132868];
    attendus int;
    n int;
BEGIN
    SELECT count(*) INTO attendus FROM public.app_relation
     WHERE app_relation_id = any(ids) AND source = 'app_seule' AND NOT present_in_hektor;
    IF attendus <> 55 THEN
        RAISE EXCEPTION '%', format('ARRET : %s ligne(s) du filet trouvee(s) sur 55 attendues (elles ont change depuis l''audit) ; rien n''est ecrit.', attendus);
    END IF;
    UPDATE public.app_relation
       SET retire_le = now()::text, retire_par = 'filet_26_10'
     WHERE app_relation_id = any(ids) AND source = 'app_seule' AND NOT present_in_hektor
       AND retire_le IS NULL;
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE NOTICE '%', format('%s lien(s) ne(s) du filet marque(s) retire(s) (filet_26_10)', n);
END
$filet$;

-- ── les contrôles ───────────────────────────────────────────────────────────
SELECT 1 AS "#", 'les deux colonnes existent' AS controle,
       CASE WHEN (SELECT count(*) FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = 'app_relation'
                     AND column_name IN ('origine', 'proprietaire_depuis')) = 2 THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'la vue porte la regle, une seule fois',
       CASE WHEN (length(pg_get_viewdef('public.app_contact_relations_current'::regclass))
                  - length(replace(pg_get_viewdef('public.app_contact_relations_current'::regclass), 'r.origine', ''))) / 9 = 1
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'la vue reste security_invoker',
       CASE WHEN (SELECT reloptions FROM pg_class WHERE oid = 'public.app_contact_relations_current'::regclass)
                 @> array['security_invoker=true'] THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'les 55 liens du filet sont retires (filet_26_10)',
       CASE WHEN (SELECT count(*) FROM public.app_relation WHERE retire_par = 'filet_26_10') = 55 THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'personne n''a encore d''origine « vente » (interrupteur eteint)',
       CASE WHEN (SELECT count(*) FROM public.app_relation WHERE origine IS NOT NULL) = 0 THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
