-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — P3 (préalable) : la vue des liens revient à « présente chez Hektor »        27/10/2026
-- Mêmes 20 colonnes : « create or replace » suffit (pas de drop). Le bloc EXIGE de retrouver l'empreinte de P2
-- (0021f0f1...), sinon tout est annulé. Le commentaire d'avant est reposé.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $inv$
DECLARE
    d       text := replace(pg_get_viewdef('public.app_contact_relations_current'::regclass), chr(13), '');
    regle   text := '(NOT ((btrim(COALESCE(l.hektor_affaire_id, ''''::text)) <> ''''::text) AND (l.present_in_hektor IS FALSE)))';
    com     text := obj_description('public.app_contact_relations_current'::regclass);
    marque  text := ' -- P3 (27/10/2026) : les acheteurs comptent quand la transaction est VIVANTE CHEZ NOUS (regle de'
                    || ' app_geste_affaire_optimistic), plus seulement « presente chez Hektor ».';
BEGIN
    IF position('l.present_in_hektor IS FALSE' in d) = 0 THEN
        RAISE NOTICE '%', 'La vue ne porte pas la regle « vivante » : rien a defaire.';
        RETURN;
    END IF;
    IF position(regle in d) = 0 THEN
        RAISE EXCEPTION '%', 'ARRET : la regle n''est pas sous la forme posee par P3 (quelqu''un est passe apres) ; rien n''est ecrit.';
    END IF;
    d := rtrim(rtrim(replace(d, regle, 'p.transaction_presente')), ';');
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as ' || d;
    IF md5(pg_get_viewdef('public.app_contact_relations_current'::regclass)) <> '0021f0f1681dcaab4ef12fd21514d254' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue recreee n''a pas l''empreinte de P2 (%s au lieu de 0021f0f1...) ; tout est annule.',
            md5(pg_get_viewdef('public.app_contact_relations_current'::regclass)));
    END IF;
    IF com IS NOT NULL AND position(marque in com) > 0 THEN
        EXECUTE format('comment on view public.app_contact_relations_current is %L', replace(com, marque, ''));
    END IF;
END
$inv$;

COMMIT;
