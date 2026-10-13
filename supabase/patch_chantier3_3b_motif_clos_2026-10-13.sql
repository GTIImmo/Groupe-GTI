-- =====================================================================
-- CHANTIER ③ -- LE MOTIF DU STATUT « CLOS » EST GARDE CHEZ NOUS
-- Date : 2026-10-13 · Detail : notice/CHANTIER_3_HEKTOR_DABORD_2026-10-12.md
-- Decision de Frederic, 13/10 : « ok pour le carnet ».
--
-- POURQUOI. Audit du 13/10 : quand on passe une annonce en « Clos », l'ecran demande un
-- motif (3 etats, 7 raisons, plus un texte libre), le worker le normalise et le CONTROLE
-- (`normalizeHektorClosureMotif`, `HEKTOR_CLOSURE_RAISONS`)... puis la seule fonction qui
-- l'utilise est derriere `CONSOLE_HEKTOR_CLOTURE_MANDAT`, ETEINT et jamais pose.
--   ➡ LE MOTIF NE VA NULLE PART : ni chez Hektor, ni dans nos tables. Mesure : 0 colonne
--     motif / raison / cause sur l'annonce, dans tout le schema.
--   ⚠ Et la modale promet pourtant « Motif transmis a Hektor ».
--
-- 📜 CE N'EST PAS UN OUBLI. Le 28/08 (C.13), la cloture chez Hektor a ete debranchee parce
--    qu'elle ECHOUAIT SUR 98,8 % DU PARC -- son formulaire exige un n° de mandat, et « la
--    cloture est IRREVERSIBLE cote Hektor -> on refuse de deviner le mandat cible ». Un geste
--    qui marche etait pris en otage par un geste qui echoue. Le motif est tombe avec lui ;
--    personne n'a decide qu'il devait disparaitre.
--
-- CE QUE FAIT LE PATCH -- 1 remplacement, verifie UNIQUE : une troisieme ligne au carnet,
-- `clos_motif`, a cote de `statut` et `diffusable`, dans la MEME transaction. Elle n'est
-- posee QUE pour la cible « closed » (les autres n'ont pas de motif) : la condition
-- `where x.valeur is not null`, deja presente, les ecarte toute seule.
--
-- CE QUI NE CHANGE PAS : rien de ce qui part chez Hektor · aucune autre ecriture · les
-- droits · les workers (AUCUN redemarrage) · le repli vendu/clos · le run, qui ne relit
-- pas le carnet. Le carnet n'est relu par personne aujourd'hui : poser cette ligne ne change
-- donc AUCUN comportement -- elle sert a la coupure.
--
-- RETOUR ARRIERE : supabase/patch_chantier3_3b_motif_clos_2026-10-13_INVERSE.sql
-- REPETITION     : supabase/patch_chantier3_3b_motif_clos_2026-10-13_REPETITION.sql
-- =====================================================================

BEGIN;

DO $patch$
DECLARE
  c_sig constant text := 'public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)';
  c_emp constant text := '97ef1f2538d16dadee7ce6129286adbe';
  c_taille constant int := 14685;

  a text; b text;
  v_def text; v_apres text; v_retour text;
  n int;
BEGIN
  v_def := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');

  IF md5(v_def) <> c_emp THEN
    RAISE EXCEPTION 'STOP : la fonction porte % au lieu de % (taille % contre %)',
      md5(v_def), c_emp, length(v_def), c_taille;
  END IF;
  IF position('clos_motif' in v_def) > 0 THEN
    RAISE EXCEPTION 'STOP : le patch est deja passe';
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

  n := (length(v_def) - length(replace(v_def, a, ''))) / length(a);
  IF n <> 1 THEN
    RAISE EXCEPTION 'STOP : l''ancre a ete trouvee % fois, il en faut exactement 1', n;
  END IF;

  EXECUTE replace(v_def, a, b);

  -- CONTROLE DE SORTIE : le chemin inverse doit rendre l'empreinte d'avant.
  v_apres  := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  v_retour := replace(v_apres, b, a);
  IF md5(v_retour) <> c_emp THEN
    RAISE EXCEPTION 'STOP : le chemin inverse rend % au lieu de % -- autre chose a change',
      md5(v_retour), c_emp;
  END IF;

  RAISE NOTICE 'OK : motif du Clos pose au carnet, taille % -> %, le reste est intact',
    c_taille, length(v_apres);
END $patch$;

COMMIT;
