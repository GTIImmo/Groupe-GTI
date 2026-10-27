-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — P2 : la vue des liens d'un contact revient à ses 18 colonnes        27/10/2026
-- ⚠ Postgres ne sait pas RETIRER une colonne par « create or replace view » : il faut la recréer.
--   La vue n'a AUCUNE vue dépendante (vérifié le 27/10) ; le « drop » sans CASCADE refuserait sinon.
-- Le bloc reconstitue la définition d'avant, la recrée, et EXIGE de retrouver l'empreinte de l'audit
--   (d4350c63...) — sinon tout est annulé. Droits, propriétaire et commentaire d'avant reposés.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $inv$
DECLARE
    d    text := replace(pg_get_viewdef('public.app_contact_relations_current'::regclass), chr(13), '');
    ajout1 text := 'r.last_seen_at AS refreshed_at,' || chr(10) || '    r.origine,' || chr(10) || '    r.proprietaire_depuis';
    ajout2 text := '(l.last_seen_at)::text AS refreshed_at,' || chr(10) || '    NULL::text AS origine,' || chr(10) || '    NULL::text AS proprietaire_depuis';
    nouvelle text;
BEGIN
    IF position('proprietaire_depuis' in d) = 0 THEN
        RAISE NOTICE '%', 'La vue n''a pas les deux colonnes : rien a defaire.';
        RETURN;
    END IF;
    IF position(ajout1 in d) = 0 OR position(ajout2 in d) = 0 THEN
        RAISE EXCEPTION '%', 'ARRET : la vue ne porte pas les deux ajouts sous la forme posee par P2 (quelqu''un est passe apres) ; rien n''est ecrit.';
    END IF;
    d := replace(d, ajout1, 'r.last_seen_at AS refreshed_at');
    d := replace(d, ajout2, '(l.last_seen_at)::text AS refreshed_at');
    d := rtrim(rtrim(d), ';');

    DROP VIEW public.app_contact_relations_current;
    EXECUTE 'create view public.app_contact_relations_current with (security_invoker = true) as ' || d;
    ALTER VIEW public.app_contact_relations_current OWNER TO postgres;
    -- ⚠ les droits par défaut de Supabase donnent TOUT à anon et authenticated sur une vue neuve : on les retire d'abord
    REVOKE ALL ON public.app_contact_relations_current FROM PUBLIC, anon, authenticated;
    GRANT SELECT ON public.app_contact_relations_current TO authenticated;
    GRANT ALL ON public.app_contact_relations_current TO service_role;

    nouvelle := pg_get_viewdef('public.app_contact_relations_current'::regclass);
    IF md5(nouvelle) <> 'd4350c631503f1ecedf99d28bee16c04' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue recreee n''a pas l''empreinte d''avant (%s au lieu de d4350c63...) ; tout est annule.', md5(nouvelle));
    END IF;
END
$inv$;

COMMENT ON VIEW public.app_contact_relations_current IS $c$LES LIENS D'UN CONTACT (30/09/2026). Nom et 18 colonnes inchanges : le front ne bouge pas. Source : app_relation, le registre durable. LE REGISTRE PORTE TOUT, CETTE VUE FILTRE (present_in_hektor, retire_le). Le bien est cherche par LATERAL avec conversion du PETIT cote -- un CTE + DISTINCT ON materialisait 57 682 lignes a chaque ouverture de fiche : 7,6 s au lieu de 27 ms.$c$;

-- le contrôle de l'inverse : 18 colonnes, les droits d'avant
DO $ctl$
DECLARE nb int; acl text;
BEGIN
    SELECT count(*) INTO nb FROM pg_attribute
     WHERE attrelid = 'public.app_contact_relations_current'::regclass AND attnum > 0 AND NOT attisdropped;
    SELECT (SELECT string_agg(x::text, ',' ORDER BY x::text) FROM unnest(relacl) x) INTO acl FROM pg_class WHERE oid = 'public.app_contact_relations_current'::regclass;
    IF nb <> 18 OR acl IS DISTINCT FROM 'authenticated=r/postgres,postgres=arwdDxtm/postgres,service_role=arwdDxtm/postgres' THEN
        RAISE EXCEPTION '%', format('ARRET : apres l''inverse, %s colonnes et droits %s (18 et ceux d''avant attendus) ; tout est annule.', nb, acl);
    END IF;
END
$ctl$;

COMMIT;
