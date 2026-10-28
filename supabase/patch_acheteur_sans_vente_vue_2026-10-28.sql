-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ TYPES §52 — L'ACQUÉREUR SANS VENTE N'EST NI MANDANT NI PROPRIÉTAIRE DU BIEN, DANS LA VUE DES LIENS    28/10/2026
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §52.
--
-- POURQUOI : à la vente, Hektor ajoute l'acheteur aux personnes du bien (rangé « mandant ») et ne l'en retire jamais quand
--   la vente est supprimée (5 cas sur 5, 28/10). Décisions de Frédéric (28/10) : tant qu'une transaction de la personne est
--   présente sur le bien, elle en est ACHETEUR ; notre écriture gagne ; « il ne faut pas retirer mandant ou propriétaire ».
-- CE QUE CE PATCH FAIT, ET RIEN D'AUTRE (1 remplacement d'une ligne, dans la 1re branche, celle des liens au bien) :
--   la ligne « lien au bien » d'une personne n'est plus montrée (elle reste au registre, rien n'est effacé) quand :
--     a. la nuit l'a marquée `origine = 'acheteur'` (relation_ledger._acheteurs_sans_vente, ses gardes y sont écrites) ;
--     b. OU elle est « née de la vente » (`origine = 'vente'`) mais la personne n'a plus de vente vivante sur ce bien ET y a
--        encore une transaction vivante : c'est le geste « Supprimer la vente » de l'app, vu DÈS LE CLIC (la fonction du
--        geste passe la vente à « absente » et recalcule le type) — la nuit pose ensuite la marque a.
--   La personne reste visible par sa transaction (2e branche : acquereur_offre, acquereur_compromis…). Le type se recalcule
--   sur la vue : il devient « acheteur », plus « mandant » ni « propriétaire ».
--   Les 20 colonnes, security_invoker, le propriétaire et les droits sont gardés (create or replace).
-- ⭐ La règle b vit dans `app_lien_vente_devenu_acheteur` (SECURITY DEFINER) : même réponse pour tous les comptes.
-- ⚠ COALESCE autour de `origine` dans les DEUX tests : sans lui, un lien sans marque (NULL) rend « inconnu », et
--   NOT(inconnu) CACHE la ligne. L'essai l'a attrapé : 10 lignes perdues, dont les 4 vrais mandants (10414, 39032…).
-- ⛔ RIEN N'EST ÉCRIT DANS UNE TABLE, RIEN CHEZ HEKTOR.
-- Le bloc vérifie l'empreinte de la vue (celle du 28/10 10:29, notaires) et S'ARRÊTE si elle a changé.
-- Retour arrière : patch_acheteur_sans_vente_vue_2026-10-28_INVERSE.sql
-- Contrôle       : patch_acheteur_sans_vente_vue_2026-10-28_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- La règle b, dans une fonction : SECURITY DEFINER (elle juge sur TOUT le registre, pas sur le portefeuille d'un
-- négociateur) et appelée SEULEMENT pour un lien « né de la vente » (CASE). Mesuré le 28/10 sous le compte d'un
-- commercial : la même règle écrite dans la vue, rejugée sous RLS, faisait passer sa fiche de 155 à 430 ms.
-- Elle ne rend qu'un oui / non : jamais une transaction.
CREATE OR REPLACE FUNCTION public.app_lien_vente_devenu_acheteur(p_contact text, p_annonce text)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $f$
  SELECT NOT EXISTS (
           SELECT 1 FROM app_affaire_partie p JOIN app_affaire_ledger l ON l.app_affaire_id = p.app_affaire_id
            WHERE p.app_contact_id_texte = p_contact AND p.role = 'acquereur' AND l.hektor_annonce_id::text = p_annonce
              AND l.kind = 'vente'
              AND NOT (btrim(coalesce(l.hektor_affaire_id, '')) <> '' AND l.present_in_hektor IS FALSE))
     AND EXISTS (
           SELECT 1 FROM app_affaire_partie p JOIN app_affaire_ledger l ON l.app_affaire_id = p.app_affaire_id
            WHERE p.app_contact_id_texte = p_contact AND p.role = 'acquereur' AND l.hektor_annonce_id::text = p_annonce
              AND NOT (btrim(coalesce(l.hektor_affaire_id, '')) <> '' AND l.present_in_hektor IS FALSE));
$f$;
REVOKE ALL ON FUNCTION public.app_lien_vente_devenu_acheteur(text, text) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.app_lien_vente_devenu_acheteur(text, text) TO authenticated, service_role;

DO $vue$
DECLARE
    d   text := pg_get_viewdef('public.app_contact_relations_current'::regclass);
    -- ⚠ ancre et ajout sur UNE SEULE LIGNE (leçon 30)
    a_avant  text := 'AND (r.retire_le IS NULL))';
    a_apres  text := 'AND (r.retire_le IS NULL) AND (COALESCE(r.origine, ''''::text) <> ''acheteur''::text) AND (NOT CASE WHEN (COALESCE(r.origine, ''''::text) = ''vente''::text) THEN public.app_lien_vente_devenu_acheteur(r.app_contact_id_texte, r.hektor_annonce_id) ELSE false END))';
    n int;
BEGIN
    IF md5(d) <> '647c32855a9b4d8db7b3db8f19247e1e' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue app_contact_relations_current a change depuis l''audit du 28/10 (empreinte %s au lieu de 647c3285...) ; rien n''est ecrit.', md5(d));
    END IF;
    n := (length(d) - length(replace(d, a_avant, ''))) / length(a_avant);
    IF n <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre de la 1re branche est trouvee %s fois (1 attendue) ; rien n''est ecrit.', n);
    END IF;
    d := replace(d, a_avant, a_apres);
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as ' || d;
END
$vue$;

COMMIT;
