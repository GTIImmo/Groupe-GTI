-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — ⑧ types, chantier 1 : l'acheteur « propriétaire depuis la vente »     26/10/2026
--
-- ⛔ D'ABORD ÉTEINDRE L'INTERRUPTEUR (APP_RELATION_ACHETEUR_PROPRIETAIRE=0 dans .env) : allumé, la nuit
--   pousserait les colonnes `origine` / `proprietaire_depuis` que ce fichier retire, et le lot ENTIER des
--   liens tomberait (« column ... does not exist »).
--
-- Il ne juge que SA part :
--   1. la vue reprend sa définition d'avant, au caractère près (empreinte 6c89ceb7… vérifiée) ;
--   2. les 55 liens nés du filet ne sont plus retirés (retire_par = 'filet_26_10' et lui seul) ;
--   3. les deux colonnes sont retirées. Ce qu'elles portaient se RECALCULE (la règle est dans le code) :
--      rien n'est perdu.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $vue$
DECLARE
    d       text := replace(pg_get_viewdef('public.app_contact_relations_current'::regclass), chr(13), '');
    ajout   text := $a$WHEN (r.origine = 'vente'::text) THEN 'proprietaire'::text$a$;
    p       int;
BEGIN
    IF position('r.origine' in d) = 0 THEN
        RAISE NOTICE '%', 'La vue ne porte pas la regle : rien a retirer.';
        RETURN;
    END IF;
    -- on retire la ligne ajoutee ET le blanc qui la suit : l'indentation qui la
    -- precedait redevient celle de la ligne d'origine (« WHEN (NULLIF(... »).
    p := position(ajout in d);
    IF p > 0 THEN
        d := left(d, p - 1) || ltrim(substr(d, p + length(ajout)), E' \n\t');
    END IF;
    IF position('r.origine' in d) > 0 THEN
        RAISE EXCEPTION '%', 'ARRET : la regle n''a pas pu etre retiree de la vue ; rien n''est ecrit.';
    END IF;
    IF md5(d) <> '6c89ceb7052f335a11514c92c47d550f' THEN
        RAISE EXCEPTION '%', format('ARRET : sans la regle, la vue ne retrouve pas son empreinte d''avant (%s) -- elle a ete modifiee par ailleurs ; rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as '
            || rtrim(rtrim(d), ';');
END
$vue$;

UPDATE public.app_relation SET retire_le = NULL, retire_par = NULL WHERE retire_par = 'filet_26_10';

alter table public.app_relation drop column if exists origine;
alter table public.app_relation drop column if exists proprietaire_depuis;

SELECT 1 AS "#", 'la vue a retrouve sa definition d''avant' AS controle,
       CASE WHEN md5(pg_get_viewdef('public.app_contact_relations_current'::regclass)) = '6c89ceb7052f335a11514c92c47d550f'
            THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'la vue reste security_invoker',
       CASE WHEN (SELECT reloptions FROM pg_class WHERE oid = 'public.app_contact_relations_current'::regclass)
                 @> array['security_invoker=true'] THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'plus aucun retrait « filet_26_10 »',
       CASE WHEN (SELECT count(*) FROM public.app_relation WHERE retire_par = 'filet_26_10') = 0 THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'les deux colonnes sont retirees',
       CASE WHEN (SELECT count(*) FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = 'app_relation'
                     AND column_name IN ('origine', 'proprietaire_depuis')) = 0 THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'les autres retraits sont intacts (2 avant le patch)',
       CASE WHEN (SELECT count(*) FROM public.app_relation WHERE retire_le IS NOT NULL) >= 2 THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
