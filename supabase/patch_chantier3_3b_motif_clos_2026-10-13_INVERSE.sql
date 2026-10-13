-- =====================================================================
-- RETOUR ARRIERE du motif du statut « Clos » au carnet -- 13/10/2026
-- Patch : supabase/patch_chantier3_3b_motif_clos_2026-10-13.sql
--
-- Il retire la troisieme ligne du carnet et ne reexecute QUE si le texte obtenu est, au
-- caractere pres, celui d'avant (empreinte 97ef1f2538d16dadee7ce6129286adbe).
--
-- ⚠ Les lignes `clos_motif` deja ecrites restent : elles sont vraies, et personne ne les lit.
--   Pour les effacer : delete from public.app_annonce_champ_app where champ = 'clos_motif';
-- =====================================================================

BEGIN;

DO $inverse$
DECLARE
  c_sig constant text := 'public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)';
  c_emp constant text := '97ef1f2538d16dadee7ce6129286adbe';
  a text; b text; v_def text; v_retour text; v_apres text; n int;
BEGIN
  v_def := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');

  IF position('clos_motif' in v_def) = 0 THEN
    IF md5(v_def) = c_emp THEN
      RAISE NOTICE 'RIEN A FAIRE : la fonction est deja celle d''avant (%)', c_emp;
      RETURN;
    END IF;
    RAISE EXCEPTION 'STOP : pas de clos_motif, et l''empreinte (%) n''est pas celle d''avant (%)',
      md5(v_def), c_emp;
  END IF;

  a := replace($a1$          from (values ('statut'::text,     v_statut_cible),
                       ('diffusable'::text, v_diff_cible)) as x(champ, valeur)$a1$, chr(13), '');
  b := replace($b1$          from (values ('statut'::text,     v_statut_cible),
                       ('diffusable'::text, v_diff_cible),
                       -- @clos-motif (13/10/2026) : LE MOTIF DE LA CLOTURE, GARDE CHEZ NOUS.
                       --   Il est saisi a l'ecran (3 etats, 7 raisons, plus un texte libre),
                       --   le worker le normalise et le controle -- puis la seule fonction qui
                       --   l'utilise est derriere `CONSOLE_HEKTOR_CLOTURE_MANDAT`, ETEINT
                       --   depuis le 28/08 : le formulaire `validerClos` echouait sur 98,8 %
                       --   du parc (il exige un n° de mandat, et la cloture est irreversible
                       --   chez Hektor). Le motif n'allait donc NULLE PART.
                       --   Decision de Frederic du 13/10 : au carnet, comme celui de
                       --   l'archivage. ⚠ Seulement pour « closed » -- la condition
                       --   `where x.valeur is not null` ecarte les autres toute seule.
                       ('clos_motif'::text, case when target_status = 'closed'
                          then nullif(concat_ws(' · ',
                                 nullif(trim(coalesce(v_payload->>'close_etat',   '')), ''),
                                 nullif(trim(coalesce(v_payload->>'close_raison', '')), ''),
                                 nullif(trim(coalesce(v_payload->>'close_reason', '')), '')), '')
                          else null end)) as x(champ, valeur)$b1$, chr(13), '');

  n := (length(v_def) - length(replace(v_def, b, ''))) / length(b);
  IF n <> 1 THEN RAISE EXCEPTION 'STOP : le morceau a ete trouve % fois, il en faut 1', n; END IF;

  v_retour := replace(v_def, b, a);
  IF md5(v_retour) <> c_emp THEN
    RAISE EXCEPTION 'STOP : le retrait rend % au lieu de % -- annule', md5(v_retour), c_emp;
  END IF;

  EXECUTE v_retour;
  v_apres := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  IF md5(v_apres) <> c_emp THEN
    RAISE EXCEPTION 'STOP : apres retrait la base porte %', md5(v_apres);
  END IF;
  RAISE NOTICE 'OK : motif retire, la fonction est revenue a l''identique (%)', md5(v_apres);
END $inverse$;

COMMIT;
