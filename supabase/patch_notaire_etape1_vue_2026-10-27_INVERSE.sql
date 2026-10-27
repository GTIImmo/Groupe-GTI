-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — NOTAIRE étape 1 : la vue des liens revient sans les notaires        27/10/2026
-- Mêmes 20 colonnes : « create or replace » suffit. Le bloc EXIGE de retrouver l'empreinte d'avant (8c4d28d3...),
-- sinon tout est annulé. Le commentaire d'avant est reposé.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $inv$
DECLARE
    d        text := replace(pg_get_viewdef('public.app_contact_relations_current'::regclass), chr(13), '');
    f_avant  text := '(p.role = ''acquereur''::text)';
    f_apres  text := '(p.role = ANY (ARRAY[''acquereur''::text, ''notaire_vendeur''::text, ''notaire_acquereur''::text]))';
    -- ⚠ LA FORME RENDUE PAR POSTGRES (vue le 27/10) : les deux CASE sur plusieurs lignes, construites par chr(10) (leçon 30)
    r_apres  text := '    b.titre_bien,' || chr(10) || '        CASE' || chr(10)
                  || '            WHEN (p.role = ''acquereur''::text) THEN (''acquereur_''::text || l.kind)' || chr(10)
                  || '            ELSE p.role' || chr(10) || '        END AS role_contact';
    r_avant  text := '    b.titre_bien,' || chr(10) || '    (''acquereur_''::text || l.kind) AS role_contact';
    k_apres  text := '((((''aff_''::text || (l.app_affaire_id)::text) || ''_''::text) || (p.app_contact_id)::text) ||' || chr(10)
                  || '        CASE' || chr(10) || '            WHEN (p.role = ''acquereur''::text) THEN ''''::text' || chr(10)
                  || '            ELSE (''_''::text || p.role)' || chr(10) || '        END) AS relation_key';
    k_avant  text := '(((''aff_''::text || (l.app_affaire_id)::text) || ''_''::text) || (p.app_contact_id)::text) AS relation_key';
    com      text := obj_description('public.app_contact_relations_current'::regclass);
    marque   text := ' -- NOTAIRE etape 1 (27/10/2026) : les roles notaire_vendeur / notaire_acquereur de la table des parties ;'
                     || ' cle suffixee du role pour eux seuls.';
BEGIN
    IF position('notaire_vendeur' in d) = 0 THEN
        RAISE NOTICE '%', 'La vue ne porte pas les notaires : rien a defaire.';
        RETURN;
    END IF;
    IF position(f_apres in d) = 0 OR position(r_apres in d) = 0 OR position(k_apres in d) = 0 THEN
        RAISE EXCEPTION '%', 'ARRET : les ajouts ne sont pas sous la forme posee (quelqu''un est passe apres) ; rien n''est ecrit.';
    END IF;
    -- l'ordre inverse de la pose
    d := replace(d, k_apres, k_avant);
    d := replace(d, r_apres, r_avant);
    d := replace(d, f_apres, f_avant);
    d := rtrim(rtrim(d), ';');
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as ' || d;
    IF md5(pg_get_viewdef('public.app_contact_relations_current'::regclass)) <> '8c4d28d388a6325582013c5bfd08bc54' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue recreee n''a pas l''empreinte d''avant (%s au lieu de 8c4d28d3...) ; tout est annule.',
            md5(pg_get_viewdef('public.app_contact_relations_current'::regclass)));
    END IF;
    IF com IS NOT NULL AND position(marque in com) > 0 THEN
        EXECUTE format('comment on view public.app_contact_relations_current is %L', replace(com, marque, ''));
    END IF;
END
$inv$;

COMMIT;
