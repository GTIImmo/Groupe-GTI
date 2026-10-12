-- =====================================================================
-- CHANTIER ③ -- UN BIEN VENDU / CLOS REDEVIENT MANIPULABLE (gestes 2 et 3)
--   ② ARCHIVER                 app_archive_annonce_optimistic
--   ③ CHANGER DE NEGOCIATEUR   app_assign_negotiator_optimistic
-- Date : 2026-10-12 · Detail : notice/CHANTIER_3_HEKTOR_DABORD_2026-10-12.md
--
-- POURQUOI DEUX FONCTIONS DANS UN SEUL PATCH : elles portent la MEME garde, au caractere
-- pres, et on y insere le MEME bloc. Les separer n'ajouterait aucune securite -- chacune
-- garde sa propre empreinte d'entree et son propre controle de sortie -- et obligerait a
-- coller deux fois. Si l'une des deux echoue, la transaction annule les DEUX.
--
-- ═══ LA REGLE DE LA MAISON (Frederic, 12/10) ═══
--   · index HISTORIQUE (Vendu / Clos, 8 941) -> les gestes marchent, comme a l'ecran
--   · index des ARCHIVES (35 318)            -> LECTURE SEULE, seule sortie « Desarchiver »
--
-- CE QUE FAIT LE PATCH : dans CHACUNE des deux fonctions, 1 remplacement -- la garde
-- d'entree devient : parc vivant -> sinon index HISTORIQUE -> sinon, si c'est une ARCHIVE,
-- un refus qui le DIT -> sinon « dossier_not_found », comme avant.
--   · archiver        : une archive rend `annonce_deja_archivee` (elle l'est deja)
--   · negociateur     : une archive rend `annonce_archivee_lecture_seule`
--
-- ⭐ LE NUMERO RECU EST LE BON : `app_historical_id` EST notre `app_dossier_id`, renomme
--   (export_app_payload.py:363), verifie le 12/10 par les anciens travaux des memes biens.
--   Tout ce qui suit dans les deux fonctions -- droits, carnet, travail -- continue donc de
--   s'en servir TEL QUEL. Aucun faux identifiant n'est pose nulle part.
--
-- CE QUI NE CHANGE PAS (verifie le 12/10) :
--   · le chemin du bien VIVANT : les deux lignes d'origine sont conservees MOT POUR MOT ;
--   · les ARCHIVES : elles etaient refusees, elles le restent -- seul le message change ;
--   · le desarchivage (`app_restore_annonce_optimistic`) : pas touche ;
--   · les droits : `app_console_can_request_job` -- admin/manager pour « archiver », et pour
--     « negociateur » ; le controle ne se sert pas du numero de dossier ;
--   · les workers : `handleArchiveHektorAnnonce` (l. 19952) n'utilise `app_dossier_id` que
--     pour le journal, `handleAssignHektorAnnonceNegotiator` (l. 14737-14746) rattrape deja
--     son absence -> AUCUN redemarrage ;
--   · l'ecran : rien a changer, il envoie deja `app_historical_id` (`api.ts:2624`).
--
-- ⚠ LA FICHE D'UN BIEN HISTORIQUE N'EST PAS ECRITE : il n'a plus de ligne dans
--   `app_dossier_current`. Ces deux fonctions n'y ecrivaient de toute facon pas -- elles
--   ecrivent au CARNET, qui lui recoit bien le vrai numero.
--
-- IL N'ECRASE RIEN : chaque fonction est LUE dans la base, son empreinte verifiee sans les
-- retours chariot, son ancre verifiee UNIQUE, puis reexecutee -- et on CONTROLE qu'en
-- retirant le bloc on retombe sur l'empreinte d'avant, au caractere pres.
--
-- RETOUR ARRIERE : supabase/patch_chantier3_repli_index_archiver_negociateur_2026-10-12_INVERSE.sql
-- REPETITION     : supabase/patch_chantier3_repli_index_archiver_negociateur_2026-10-12_REPETITION.sql
-- =====================================================================

BEGIN;

DO $patch$
DECLARE
  sigs  constant text[] := ARRAY[
    'public.app_archive_annonce_optimistic(bigint,jsonb,integer)',
    'public.app_assign_negotiator_optimistic(bigint,text,jsonb,integer)'];
  emps  constant text[] := ARRAY[
    'b9bf9d40d32be0a16959ee4a35548ac9',
    '275f8d9d1000fb4100889c10314c8cf5'];
  refus constant text[] := ARRAY[
    'annonce_deja_archivee',
    'annonce_archivee_lecture_seule'];

  c_ancre text;
  v_bloc text; v_def text; v_apres text; v_retour text;
  i int; n int;
BEGIN
  -- ⚠ FINS DE LIGNE : le corps est lu sans chr(13) ; ce script, colle depuis Windows, en
  --   porte. On normalise les deux cotes (piege paye le 12/10 sur le patch precedent).
  c_ancre := replace($anc$  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode = '22023'; end if;$anc$, chr(13), '');

  FOR i IN 1 .. 2 LOOP
    v_def := replace(pg_get_functiondef(sigs[i]::regprocedure), chr(13), '');

    IF md5(v_def) <> emps[i] THEN
      RAISE EXCEPTION 'STOP : % n''est pas celle mesuree le 12/10 (empreinte %, attendue %)',
        sigs[i], md5(v_def), emps[i];
    END IF;
    IF position('@repli-debut' in v_def) > 0 THEN
      RAISE EXCEPTION 'STOP : % porte deja le repli', sigs[i];
    END IF;

    n := (length(v_def) - length(replace(v_def, c_ancre, ''))) / length(c_ancre);
    IF n <> 1 THEN
      RAISE EXCEPTION 'STOP : dans %, l''ancre a ete trouvee % fois, il en faut exactement 1', sigs[i], n;
    END IF;

    v_bloc := replace(replace($bloc$  -- @repli-debut   CHANTIER 3 (12/10/2026) : LE BIEN PEUT ETRE VENDU OU CLOS
  --
  -- LA REGLE DE LA MAISON, telle que l'ECRAN la porte depuis le 21/05/2026
  -- (`isReadOnlyLightweightDetail`, App.tsx:406-411), confirmee par Frederic le 12/10 :
  --     · VENDU / CLOS  -> les gestes marchent (l'ecran les ouvre des que le detail est la)
  --     · ARCHIVE       -> LECTURE SEULE, sa seule sortie est « Desarchiver »
  --
  -- Depuis le 20/05, les Vendu/Clos ne sont plus dans app_dossier_current : ils vivent dans
  -- `app_historical_annonce_index_current`. Les RPC « optimistes », ecrites les 25 et 30/08,
  -- l'ignoraient et refusaient 8 941 biens sur un « dossier_not_found » brut -- alors que
  -- l'ecran, lui, affichait le bouton. L'ecran a trois etats, la base n'en avait qu'un.
  --
  -- ⭐ LE NUMERO RECU EST LE BON : `app_historical_id` EST notre `app_dossier_id`, renomme
  --   (export_app_payload.py:363), verifie par les anciens travaux des memes biens. On le
  --   garde donc TEL QUEL pour les droits, le carnet et le travail.
  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then
    select h.app_historical_id, h.hektor_annonce_id, h.numero_dossier, h.titre_bien,
           h.statut_annonce, h.diffusable, h.archive, h.negociateur_email
      into d.app_dossier_id, d.hektor_annonce_id, d.numero_dossier, d.titre_bien,
           d.statut_annonce, d.diffusable, d.archive, d.negociateur_email
      from public.app_historical_annonce_index_current h
     where h.app_historical_id = target_dossier_id;

    if not found then
      -- UNE ARCHIVE RESTE EN LECTURE SEULE -- c'est voulu, pas un oubli. On le DIT, au lieu
      -- de rendre « dossier_not_found », qui ne veut rien dire pour celui qui lit.
      if exists (select 1 from public.app_archive_annonce_index_current x
                  where x.app_archive_id = target_dossier_id) then
        raise exception '__REFUS__' using errcode = '22023';
      end if;
      raise exception 'dossier_not_found' using errcode = '22023';
    end if;
  end if;
  -- @repli-fin$bloc$, chr(13), ''), '__REFUS__', refus[i]);

    v_apres := replace(v_def, c_ancre, v_bloc);
    EXECUTE v_apres;

    -- CONTROLE DE SORTIE, fonction par fonction : en retirant le bloc on doit retomber sur
    -- l'empreinte d'avant, au caractere pres.
    v_retour := replace(replace(pg_get_functiondef(sigs[i]::regprocedure), chr(13), ''), v_bloc, c_ancre);
    IF md5(v_retour) <> emps[i] THEN
      RAISE EXCEPTION 'STOP : pour %, en retirant le bloc on obtient % au lieu de % -- autre chose a change',
        sigs[i], md5(v_retour), emps[i];
    END IF;

    RAISE NOTICE 'OK : % -- repli pose, le reste est intact', sigs[i];
  END LOOP;
END $patch$;

COMMIT;
