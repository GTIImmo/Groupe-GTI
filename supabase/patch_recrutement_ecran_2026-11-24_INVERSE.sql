-- ═══════════════════════════════════════════════════════════════════════════
-- INVERSE — RECRUTEMENT R6 (ce que l'écran écrit et lit)                                    24/11/2026
-- Retire ce que patch_recrutement_ecran_2026-11-24.sql a posé : les 9 fonctions de l'écran, les 5 fonctions
-- internes, les 4 tables (agence_gti, suivi, evenement, retrait). Il NE TOUCHE PAS au socle R3 (fiches,
-- entreprises, collectes, carnet, liste « ne plus contacter »).
-- ⛔ GARDE : il REFUSE de tourner si l'app a déjà écrit un suivi, un fil ou un retrait (ce travail-là ne se
--   recollecte pas) : les sauvegarder d'abord, puis décider.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $$
BEGIN
  IF to_regclass('recrutement.suivi') IS NOT NULL
     AND ((SELECT count(*) FROM recrutement.suivi) + (SELECT count(*) FROM recrutement.evenement)
          + (SELECT count(*) FROM recrutement.retrait)) > 0 THEN
    RAISE EXCEPTION 'l''app a deja ecrit un suivi, un fil ou un retrait : les sauvegarder avant (rien n''a ete fait)';
  END IF;
END $$;

drop function if exists public.rec_candidats();
drop function if exists public.rec_candidat(text, text);
drop function if exists public.rec_noter(text, text, text, text, text, timestamptz);
drop function if exists public.rec_etape(text, text, integer);
drop function if exists public.rec_suivi_maj(text, text, jsonb);
drop function if exists public.rec_corriger(text, text, text, text, boolean);
drop function if exists public.rec_doublons(text, text, text, text, text, text);
drop function if exists public.rec_ajouter(jsonb);
drop function if exists public.rec_retirer(text, text, text, text, date);
drop function if exists recrutement.exiger_admin();
drop function if exists recrutement.valeur(jsonb, text, text);
drop function if exists recrutement.empreintes(text, text, text, text, text, text);
drop function if exists recrutement.empreinte(text);
drop function if exists recrutement.cle_nom(text, text);
drop table if exists recrutement.evenement;
drop table if exists recrutement.suivi;
drop table if exists recrutement.retrait;
drop table if exists recrutement.agence_gti;

-- Le retour arrière ne juge que SA part : rien de R6 ne reste, et le socle R3 est intact.
DO $$
BEGIN
  IF to_regclass('recrutement.suivi') IS NOT NULL OR to_regclass('recrutement.evenement') IS NOT NULL
     OR to_regclass('recrutement.retrait') IS NOT NULL OR to_regclass('recrutement.agence_gti') IS NOT NULL THEN
    RAISE EXCEPTION 'une table de R6 est toujours la';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_proc WHERE pronamespace = 'public'::regnamespace
               AND proname IN ('rec_candidats', 'rec_candidat', 'rec_noter', 'rec_etape', 'rec_suivi_maj', 'rec_corriger',
                               'rec_doublons', 'rec_ajouter', 'rec_retirer')) THEN
    RAISE EXCEPTION 'une fonction de l''ecran est toujours la';
  END IF;
  IF to_regclass('recrutement.fiche') IS NULL OR to_regclass('recrutement.liste_noire') IS NULL
     OR to_regprocedure('public.rec_etat_collecte()') IS NULL THEN
    RAISE EXCEPTION 'le socle R3 a ete touche : il ne devait pas l''etre';
  END IF;
END $$;

COMMIT;
