-- ═══════════════════════════════════════════════════════════════════════════
-- CATALOGUE DES PARTENAIRES · LES NUMEROS DES NOTAIRES PAR L'INDEX   09/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §28.10 (« le délai dépassé du catalogue »).
-- A APPLIQUER avec l'accord de Frédéric, APRES la répétition, HORS du run de nuit (05:00-07:45).
--
-- Ajoute (rien n'est remplacé) :
--   · l'index idx_app_contact_current_relation_roles_gin (GIN jsonb_path_ops sur relation_roles_json ; ~250 Ko, ~0,2 s) ;
--   · la fonction public.app_catalogue_notaires_ids() : utilisateur actif seulement, anon fermé, rend la liste des NUMEROS des notaires
--     (relation_roles_json contient notaire_vendeur OU notaire_acquereur), archives comprises.
-- L'écran (CataloguePartenaires.tsx) relit ensuite les fiches par numéro, 200 par 200, SOUS LA REGLE D'ACCES habituelle,
-- et retombe sur l'ancienne lecture si la fonction manque ou refuse.
-- Verrou : la construction de l'index bloque les écritures sur les contacts ~0,2 s ; lock_timeout 3 s (sinon rien n'est écrit).
-- RETOUR ARRIERE : patch_catalogue_notaires_numeros_2026-11-09_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
SET LOCAL lock_timeout = '3s';

DO $garde$
BEGIN
  IF to_regprocedure('public.app_catalogue_notaires_ids()') IS NOT NULL THEN
    RAISE EXCEPTION 'ARRET : app_catalogue_notaires_ids existe deja. Rien n''est ecrit.';
  END IF;
  IF to_regclass('public.idx_app_contact_current_relation_roles_gin') IS NOT NULL THEN
    RAISE EXCEPTION 'ARRET : l''index idx_app_contact_current_relation_roles_gin existe deja. Rien n''est ecrit.';
  END IF;
END
$garde$;

CREATE INDEX idx_app_contact_current_relation_roles_gin ON public.app_contact_current USING gin (relation_roles_json jsonb_path_ops);

CREATE FUNCTION public.app_catalogue_notaires_ids()
 RETURNS text[]
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $f$
BEGIN
  -- 09/11/2026 (note partenaires §28.10) : les NUMEROS des notaires du catalogue, et rien d'autre (ni nom, ni telephone,
  -- ni e-mail). Sous la regle d'acces, « @> » n'est pas LEAKPROOF : l'index des roles y est inutilisable et la lecture
  -- parcourait les 94 895 contacts (delai de 8 s depasse le 09/11 a 07:14, pendant le run). Ici, sans la regle, l'index
  -- sert (3,5 ms) ; l'ecran relit ensuite les fiches PAR NUMERO, sous la regle habituelle : le perimetre ne change pas.
  -- Meme regle qu'avant (CataloguePartenaires.tsx) : les deux cotes de la table des parties, archives compris.
  IF NOT public.is_app_user_active() THEN
    RAISE EXCEPTION '%', 'Compte inactif.' USING ERRCODE = '42501';
  END IF;
  RETURN coalesce((SELECT array_agg(c.hektor_contact_id ORDER BY c.hektor_contact_id)
                     FROM public.app_contact_current c
                    WHERE c.relation_roles_json @> '["notaire_vendeur"]'::jsonb
                       OR c.relation_roles_json @> '["notaire_acquereur"]'::jsonb), '{}'::text[]);
END
$f$;

REVOKE ALL ON FUNCTION public.app_catalogue_notaires_ids() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.app_catalogue_notaires_ids() FROM anon;
GRANT EXECUTE ON FUNCTION public.app_catalogue_notaires_ids() TO authenticated, service_role;

COMMIT;
