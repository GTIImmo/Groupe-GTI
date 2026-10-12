-- =====================================================================
-- CHANTIER ③ -- POINT 3a : L'ETAT DU BIEN S'ECRIT CHEZ NOUS D'ABORD
-- Date : 2026-10-12 · Detail : notice/CHANTIER_3_HEKTOR_DABORD_2026-10-12.md
--
-- POURQUOI. Regle de Frederic, 12/10 : « il faut d'abord ecrire sur l'app puis envoyer a
-- Hektor, ne pas dependre » -- et « SUR TOUS LES GESTES ». Aujourd'hui
-- app_change_annonce_status_optimistic n'ecrit chez nous que la ligne d'affaire (offre /
-- compromis / vente). L'ETAT DU BIEN n'est ecrit NULLE PART : notre base attend la reponse
-- de Hektor pour savoir dans quel etat est notre propre bien. Mesure du 08/10, annonce
-- 62963 : clic 18:48:23 -> Hektor 18:49:00 -> notre base 18:49:41, soit 78 SECONDES.
-- Et si Hektor refusait definitivement, notre base n'aurait JAMAIS su qu'on avait clique.
--
-- CE QUE FAIT LE PATCH. Il insere UN bloc dans la fonction, juste avant la creation du
-- travail Hektor. Le bloc, si l'interrupteur est allume :
--   1. range l'etat d'avant (statut + diffusable) dans la charge du travail  -> pour revenir
--   2. ecrit le statut et le diffusable sur la FICHE du bien  -> l'ecran ne mente plus
--   3. ecrit les deux au CARNET de l'annonce                  -> survit a la coupure
--
-- CE QU'IL N'ECRIT PAS : offre_id / compromis_id / vente_id (Hektor seul les cree ; les
-- inventer casserait l'annulation -- etude du 29/06) ni `archive`.
--
-- CE QUI NE CHANGE PAS (verifie le 12/10, voir la note) :
--   · 1 SEUL appelant de la fonction : l'ecran (apps/hektor-v1/src/lib/api.ts:9917).
--     Rien depuis le backend Render, les workers, phase2, un cron ou une autre fonction SQL.
--   · la vitrine publique : fabriquee depuis la base LOCALE, pas depuis Supabase.
--   · le run de nuit : il reecrit statut_annonce et diffusable depuis Hektor chaque nuit et
--     ne gele plus aucun bien depuis le 21/09 -> il garde le dernier mot.
--   · la protection champ par champ : app_annonce_reappliquer_saisies lit
--     app_annonce_pending, JAMAIS le carnet.
--   · les 4 workers : aucune ligne modifiee -> AUCUN redemarrage.
--   · les portails : diffusion gelee depuis le 07/07.
--   · le controle d'acces : inchange (app_console_can_request_job -> admin ou manager).
--
-- CE QUI ARRIVE 78 s PLUS TOT, ET QUI EST ASSUME :
--   · la page publique de RDV d'un bien mis sous mandat (son lien vient de la vitrine, qui
--     n'est refaite que la nuit : personne ne l'a encore). Pour « Mandat clos » elle se
--     FERME 78 s plus tot -- plus sur qu'aujourd'hui.
--   · le rapprochement : trg_dossier_dirty reagit a statut_annonce et diffusable, crons
--     chaque minute. Verifie : ces crons n'ecrivent que dans app_notification (la cloche
--     dans l'app) -- AUCUN e-mail ne part.
--
-- LE TROU ASSUME, ECRIT : si Hektor refuse DEFINITIVEMENT (apres les 5 essais du filet
-- C.4-bis), notre base garde le nouvel etat jusqu'au run de nuit -- au plus 24 h. Le worker
-- n'a pas de chemin de retour pour ce geste (console_job_worker.js:19016) ; l'etat d'avant
-- est deja range dans la charge pour que le second temps n'ait rien a changer ici.
-- Pour memoire : 28 gestes de statut depuis mai, 0 echec.
--
-- IL N'ECRASE RIEN. Il ne recopie pas la fonction : il la LIT dans la base, verifie son
-- empreinte SANS LES RETOURS CHARIOT, verifie que l'ancre est UNIQUE et que le bloc n'est
-- pas deja la, insere, reexecute -- puis CONTROLE qu'en retirant le bloc on retombe sur
-- l'empreinte d'avant, au caractere pres.
--
-- RETOUR ARRIERE : supabase/patch_chantier3_3a_etat_chez_nous_2026-10-12_INVERSE.sql
--                  (ou, immediat : update app_setting set value='off' ...)
-- REPETITION     : supabase/patch_chantier3_3a_etat_chez_nous_2026-10-12_REPETITION.sql
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 1. L'INTERRUPTEUR
--    ETEINDRE : update public.app_setting set value='off', updated_at=now()
--                where key='etat_annonce_ecrit_chez_nous';
-- ---------------------------------------------------------------------
INSERT INTO public.app_setting (key, value, description, updated_at)
VALUES ('etat_annonce_ecrit_chez_nous', 'on',
        'Chantier 3 point 3a (12/10/2026) : un changement de statut d''annonce ecrit le statut et le diffusable CHEZ NOUS (fiche + carnet) avant d''envoyer le travail a Hektor. off = comportement d''avant, rien n''est ecrit chez nous.',
        now())
ON CONFLICT (key) DO UPDATE
   SET value = 'on', description = excluded.description, updated_at = now();

-- ---------------------------------------------------------------------
-- 2. LA FONCTION : lue dans la base, bloc insere avant l'ancre, reexecutee
-- ---------------------------------------------------------------------
DO $patch$
DECLARE
  c_sig    constant text := 'public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)';
  c_emp    constant text := '302852e8dc23c44d6e0442b81e6cb577';
  c_taille constant int  := 8446;
  c_ancre  constant text := $ancre$  -- Le travail emporte le numero d'affaire : c'est lui qui permettra de la retrouver.$ancre$;
  v_def    text;
  v_bloc   text;
  v_apres  text;
  v_nu     text;
  i        int;
  j        int;
  n        int;
BEGIN
  -- 2.a ON LIT, ON NE RECOPIE PAS
  v_def := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');

  IF md5(v_def) <> c_emp THEN
    RAISE EXCEPTION 'STOP : la fonction n''est pas celle mesuree le 12/10 (empreinte %, attendue %, taille % contre %)',
      md5(v_def), c_emp, length(v_def), c_taille;
  END IF;

  IF position('@3a-debut' in v_def) > 0 THEN
    RAISE EXCEPTION 'STOP : le patch est deja passe (le bloc @3a-debut est deja dans la fonction)';
  END IF;

  n := (length(v_def) - length(replace(v_def, c_ancre, ''))) / length(c_ancre);
  IF n <> 1 THEN
    RAISE EXCEPTION 'STOP : l''ancre a ete trouvee % fois, il en faut exactement 1', n;
  END IF;

  -- 2.b LE BLOC
  v_bloc := $bloc$  -- @3a-debut   CHANTIER 3, POINT 3a (12/10/2026) : CHEZ NOUS D'ABORD, PUIS HEKTOR
  --
  -- POURQUOI. « Actif » et « Mandat clos » n'ecrivaient RIEN chez nous : v_kind est null
  -- pour eux, et tout ce que cette fonction ecrivait etait enferme dans
  -- `if v_kind is not null`. Notre base attendait donc la relecture de Hektor pour savoir
  -- l'etat de notre propre bien -- 78 s mesurees sur l'annonce 62963 le 08/10.
  -- Regle de Frederic du 12/10 : « d'abord ecrire sur l'app puis envoyer a Hektor, ne pas
  -- dependre », « SUR TOUS LES GESTES ».
  --
  -- LES VALEURS SONT CELLES DU WORKER, mot pour mot -- HEKTOR_STATUS_CONFIG,
  -- Console/console_job_worker.js:10924-10930 (statut 2/3/4/5/6 ; diffusable 1 pour Actif,
  -- 0 pour Mandat clos, rien pour les trois transactions : c'est Hektor qui decide).
  --
  -- ⚠ ON NE TOUCHE PAS offre_id / compromis_id / vente_id. Hektor seul les cree, et ils
  --   servent a ANNULER : les inventer casserait l'annulation (etude du 29/06). La pastille
  --   de l'ecran retombe sur statut_annonce quand ils sont vides (App.tsx:23554-23560) --
  --   le statut suffit donc a la faire bouger.
  -- ⚠ ON NE TOUCHE PAS `archive` : c'est un autre geste (point 3b).
  declare
    v_statut_cible text;
    v_diff_cible   text;
  begin
    if coalesce((select s.value from public.app_setting s
                  where s.key = 'etat_annonce_ecrit_chez_nous'), 'off') = 'on' then

      v_statut_cible := case target_status
                          when 'active'     then 'Actif'
                          when 'offer'      then 'Sous offre'
                          when 'compromise' then 'Sous compromis'
                          when 'sold'       then 'Vendu'
                          when 'closed'     then 'Mandat clos'
                          else null end;
      v_diff_cible   := case target_status
                          when 'active' then '1'
                          when 'closed' then '0'
                          else null end;

      if v_statut_cible is not null then
        -- 1. L'ETAT D'AVANT VOYAGE DANS LA CHARGE. `d` a ete lu en tete de la fonction :
        --    ce sont bien les valeurs d'AVANT. Personne ne les relit encore (le worker n'a
        --    pas de chemin de retour pour ce geste) : elles sont posees maintenant pour que
        --    le second temps n'ait plus rien a changer ici.
        v_payload := v_payload || jsonb_build_object(
          'statut_avant',     d.statut_annonce,
          'diffusable_avant', d.diffusable);

        -- 2. LA FICHE DU BIEN : visible tout de suite, par l'ecran et par tout le monde.
        update public.app_dossier_current
           set statut_annonce = v_statut_cible,
               diffusable     = coalesce(v_diff_cible, d.diffusable)
         where app_dossier_id = target_dossier_id;

        -- 3. LE CARNET : ce que l'app DETIENT, champ par champ. Il n'est relu par personne
        --    aujourd'hui (CHAMPS_APP_ANNONCE est vide dans phase2/identite/contrat_autorite.py)
        --    et c'est voulu : il devient la verite le jour ou Frederic allume l'interrupteur
        --    du contrat d'autorite. Meme patron que le geste « archiver ».
        insert into public.app_annonce_champ_app
          (app_dossier_id, champ, valeur_app, origine, ecrit_le, ecrit_par)
        select target_dossier_id, x.champ, x.valeur, 'geste_statut', now(),
               coalesce(auth.uid()::text, 'app')
          from (values ('statut'::text,     v_statut_cible),
                       ('diffusable'::text, v_diff_cible)) as x(champ, valeur)
         where x.valeur is not null
        on conflict (app_dossier_id, champ) do update
           set valeur_app = excluded.valeur_app,
               origine    = excluded.origine,
               ecrit_le   = excluded.ecrit_le,
               ecrit_par  = excluded.ecrit_par;
      end if;
    end if;
  end;
  -- @3a-fin
$bloc$;

  -- 2.c ON INSERE AVANT L'ANCRE, ET ON REEXECUTE
  v_def := replace(v_def, c_ancre, v_bloc || c_ancre);
  EXECUTE v_def;

  -- 2.d CONTROLE DE SORTIE : en RETIRANT le bloc, on doit retomber sur l'empreinte d'avant
  --     -- au caractere pres. C'est la preuve que rien d'autre n'a bouge.
  v_apres := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');

  IF position('@3a-debut' in v_apres) = 0 OR position('@3a-fin' in v_apres) = 0 THEN
    RAISE EXCEPTION 'STOP : le bloc n''est pas dans la fonction apres le patch';
  END IF;

  n := (length(v_apres) - length(replace(v_apres, c_ancre, ''))) / length(c_ancre);
  IF n <> 1 THEN
    RAISE EXCEPTION 'STOP : l''ancre a disparu ou a ete doublee (% fois)', n;
  END IF;

  i := position('  -- @3a-debut' in v_apres);
  j := position('  -- @3a-fin' in v_apres);
  v_nu := substr(v_apres, 1, i - 1) || substr(v_apres, j + length('  -- @3a-fin') + 1);

  IF md5(v_nu) <> c_emp THEN
    RAISE EXCEPTION 'STOP : en retirant le bloc on ne retombe pas sur la fonction d''avant (% au lieu de %) -- autre chose a change',
      md5(v_nu), c_emp;
  END IF;

  RAISE NOTICE 'OK : bloc insere (% caracteres), le reste est intact (empreinte nue = %)',
    length(v_apres) - length(v_nu), md5(v_nu);
END $patch$;

COMMIT;
