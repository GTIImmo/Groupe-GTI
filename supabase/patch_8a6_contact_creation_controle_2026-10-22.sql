-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · 8a-B2 — LE CONTRÔLE AU RETOUR S'ÉTEND À LA CRÉATION DE CONTACT  22/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md (« Clôturer 8a »)
--
-- LE DÉFAUT (audit du 22/10) : B (patch 8a5) ne garde que les MODIFICATIONS. Un contact CRÉÉ
-- dans l'app part chez Hektor ; si Hektor ne garde pas un champ (une ville sans son code
-- postal, une ville contraire au code postal — prouvé ce jour), la relecture le remplace
-- en silence, exactement comme avant B.
--
-- CE QUE FAIT CE PATCH — CHIRURGICAL, trois ancres d'une ligne dans la fonction de garde :
--   · elle accepte aussi « created » (contact) et « created_and_linked » (mandant) ;
--   · elle retrouve le contact aussi par notre numéro dans la charge (app_identite) et par
--     celui de Hektor dans le résultat ;
--   · le déclencheur est recréé avec les deux types de création en plus.
-- Rien d'autre : la table, le verdict, la vue, la sentinelle et l'interrupteur
-- (contact_retour_controle) sont ceux de B.
--
-- ⛔ GARDE : la fonction n'est modifiée que si son empreinte est 4af27d6a (posée le 22/10 à
--    13:05) et le texte neuf porte l'empreinte 7a1b2292 CALCULÉE D'AVANCE.
-- RETOUR ARRIÈRE : supabase/patch_8a6_contact_creation_controle_2026-10-22_INVERSE.sql (rend 4af27d6a et le déclencheur à 2 types).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $pose$
DECLARE
    d text := replace(pg_get_functiondef('public.app_contact_saisie_modif_job_trg()'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$    if coalesce(new.result_json->>'status', '') <> 'updated' then return null; end if;  -- held_conflict, etc.$a1$, chr(13), ''),
        replace($a2$    ident := nullif(trim(coalesce(new.payload_json->>'hektor_contact_id', new.payload_json->>'contact_id', '')), '');$a2$, chr(13), ''),
        replace($a3$     where c.hektor_contact_id = ident or c.hektor_target_id = ident$a3$, chr(13), '')];
    neufs text[] := array[
        replace($n1$    -- 8a-B2 (22/10) : la CREATION aussi -- created (contact), created_and_linked (mandant).
    if coalesce(new.result_json->>'status', '') not in ('updated', 'created', 'created_and_linked') then return null; end if;  -- held_conflict, etc.$n1$, chr(13), ''),
        replace($n2$    -- a la creation, notre numero est dans la charge (app_identite), celui de Hektor dans le resultat
    ident := nullif(trim(coalesce(new.payload_json->>'hektor_contact_id', new.payload_json->>'contact_id', new.payload_json->>'app_identite', new.result_json->>'hektor_contact_id', '')), '');$n2$, chr(13), ''),
        replace($n3$     where c.hektor_contact_id = ident or c.hektor_target_id = ident
        or c.hektor_target_id = nullif(trim(coalesce(new.result_json->>'hektor_contact_id', '')), '')$n3$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '7a1b2292ce75c60cfc636208ebe7e0a7' THEN
        RAISE NOTICE '%', 'Deja dans l''etat voulu (7a1b2292) : la fonction n''est pas reecrite.';
    ELSE
        IF md5(d) <> '4af27d6a8dd2aa1153c1b1426db6a563' THEN
            RAISE EXCEPTION '%', format('ARRET : app_contact_saisie_modif_job_trg a l''empreinte %s, attendu 4af27d6a. Rien n''est ecrit.', md5(d));
        END IF;
        FOR i IN 1 .. array_length(ancres, 1) LOOP
            nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
            IF nb <> 1 THEN
                RAISE EXCEPTION '%', format('ARRET : le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
            END IF;
            d := replace(d, ancres[i], neufs[i]);
        END LOOP;
        IF md5(d) <> '7a1b2292ce75c60cfc636208ebe7e0a7' THEN
            RAISE EXCEPTION '%', format('ARRET : le texte obtenu a l''empreinte %s, attendu 7a1b2292 (calcule d''avance). Rien n''est ecrit.', md5(d));
        END IF;
        EXECUTE d;
    END IF;
    -- le declencheur : sa clause WHEN porte la liste des travaux
    EXECUTE 'drop trigger if exists app_contact_saisie_modif_job_trg on public.app_console_job';
    EXECUTE $t$create trigger app_contact_saisie_modif_job_trg
  after update on public.app_console_job
  for each row
  when (new.status = 'done' and old.status is distinct from 'done'
        and new.job_type in ('update_hektor_contact', 'update_hektor_mandant_contact', 'create_hektor_contact', 'create_hektor_mandant_contact'))
  execute function public.app_contact_saisie_modif_job_trg()$t$;
END
$pose$;

-- LES CONTRÔLES — tous doivent dire OK
SELECT 1 AS "#", 'la fonction de garde porte l''empreinte 7a1b2292' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_contact_saisie_modif_job_trg()'::regprocedure), chr(13), '')) = '7a1b2292ce75c60cfc636208ebe7e0a7' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'le declencheur existe, un seul, sur 4 types de travail',
       CASE WHEN (SELECT count(*) FROM pg_trigger WHERE tgname = 'app_contact_saisie_modif_job_trg') = 1
             AND (SELECT pg_get_triggerdef(oid) FROM pg_trigger WHERE tgname = 'app_contact_saisie_modif_job_trg') LIKE '%update_hektor_mandant_contact%'
             AND ((SELECT pg_get_triggerdef(oid) FROM pg_trigger WHERE tgname = 'app_contact_saisie_modif_job_trg') LIKE '%create_hektor_contact%') = true
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'l''interrupteur du controle est inchange',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'contact_retour_controle') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
