-- =====================================================================
-- CHANTIER ③ -- UN BIEN VENDU / CLOS REDEVIENT MANIPULABLE (geste : CHANGER LE STATUT)
-- Date : 2026-10-12 · Detail : notice/CHANTIER_3_HEKTOR_DABORD_2026-10-12.md
--
-- ═══ LA REGLE DE LA MAISON, ARRETEE PAR FREDERIC LE 12/10 ═══
--   · index HISTORIQUE (Vendu / Clos, 8 941)  -> les gestes marchent, comme a l'ecran
--   · index des ARCHIVES (35 318)             -> LECTURE SEULE, seule sortie « Desarchiver »
--   · index des BROUILLONS (~485)             -> lecture seule
--
-- POURQUOI C'ETAIT CASSE. L'ecran porte cette regle depuis le 21/05/2026 (`5faf38a`,
-- `isReadOnlyLightweightDetail`, App.tsx:406-411) : une archive est en lecture seule TOUJOURS,
-- un Vendu/Clos l'est seulement TANT QUE son detail n'est pas telecharge -- apres quoi la fiche
-- redevient pleinement manipulable. A l'epoque ca marchait : le front inserait le travail
-- directement. Le 25/08 (`dbaf979`), le geste est passe par cette RPC, qui ne connait qu'une
-- question : « ce bien est-il dans app_dossier_current ? ». Le bouton est reste affiche, et il
-- echoue depuis, sur « dossier_not_found » -- en jargon, et sans sentinelle.
-- L'ecran a TROIS etats, la base n'en avait qu'UN. Ce patch lui apprend le troisieme.
--
-- ⭐ ET LE NUMERO DE DOSSIER EST BIEN LA. Mesure du 12/10 : les trois index sont fabriques par
--   `CAST(app_dossier_id AS INTEGER) AS app_archive_id / app_historical_id / app_brouillon_id`
--   (export_app_payload.py:316, 363, 451). `app_historical_id` N'EST PAS une serie a part :
--   c'est NOTRE app_dossier_id, renomme. Preuve croisee par les anciens travaux du meme bien :
--       annonce 24933 -> index 1 352 132, anciens travaux 1 352 132
--       annonce 62963 -> index 5 880 239, anciens travaux 5 880 239
--   Il n'y a donc AUCUN faux identifiant a craindre : le numero recu est le bon, et tout ce qui
--   suit dans la fonction (droits, fiche, carnet, travail) continue de s'en servir TEL QUEL.
--   ⚠ Cela corrige au passage la note 5a du 08/10, qui croyait le contraire.
--
-- CE QUE FAIT LE PATCH -- 2 remplacements, chacun verifie UNIQUE avant d'etre fait :
--   R1  la garde d'entree : parc vivant -> sinon index HISTORIQUE -> sinon, si c'est une
--       ARCHIVE, un refus qui le DIT (`annonce_archivee_lecture_seule`) -> sinon
--       « dossier_not_found », comme avant.
--       Et hors parc vivant, les cibles Offre / Compromis / Vendu sont refusees avec
--       `transaction_hors_parc_vivant` : elles creent une ligne dans le registre des affaires,
--       qui se tient au parc vivant.
--   R2  ⚠ MA CORRECTION DU JOUR : le bloc 3a ecrivait « Mandat clos » (l'etiquette de l'ecran)
--       la ou la donnee vaut « Clos ». Mesure : 34 916 lignes portent « Clos », ZERO porte
--       « Mandat clos ».
--
-- CE QUI NE CHANGE PAS (verifie le 12/10) :
--   · le chemin du bien VIVANT : les deux premieres lignes sont conservees MOT POUR MOT ;
--   · les ARCHIVES : elles etaient refusees, elles le restent -- seul le message change ;
--   · les droits : admin/manager, et le controle ne se sert pas du numero de dossier ;
--   · le worker : `handleChangeHektorAnnonceStatus` (l. 14389-14399) n'a besoin que du numero
--     Hektor -> AUCUN redemarrage ;
--   · l'ecran : rien a changer, il envoie deja `app_historical_id` (`api.ts:2624`) ;
--   · le desarchivage (5a) : cette fonction n'y touche pas.
--
-- ⚠ LA FICHE D'UN BIEN HISTORIQUE N'EST PAS ECRITE, ET C'EST NORMAL : il n'a plus de ligne dans
--   `app_dossier_current`. L'`update` de 3a touche donc 0 ligne. Le CARNET, lui, est bien ecrit
--   -- avec le vrai numero -- et c'est lui qui porte ce que l'app detient.
--
-- IL N'ECRASE RIEN : il LIT la fonction dans la base, verifie son empreinte sans les retours
-- chariot, verifie que chaque ancre est unique, remplace, reexecute -- puis CONTROLE qu'en
-- refaisant le chemin INVERSE on retombe sur l'empreinte d'avant, au caractere pres.
--
-- RETOUR ARRIERE : supabase/patch_chantier3_repli_index_statut_2026-10-12_INVERSE.sql
-- REPETITION     : supabase/patch_chantier3_repli_index_statut_2026-10-12_REPETITION.sql
-- =====================================================================

BEGIN;

DO $patch$
DECLARE
  c_sig constant text := 'public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)';
  c_emp constant text := '1f9e987f3a2a9fc977ae4efd6db5b000';
  c_taille constant int := 12342;

  a text[]; b text[];
  v_def text; v_apres text; v_retour text;
  i int; n int;
BEGIN
  v_def := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');

  IF md5(v_def) <> c_emp THEN
    RAISE EXCEPTION 'STOP : la fonction n''est pas celle mesuree le 12/10 apres 3a (empreinte %, attendue %, taille % contre %)',
      md5(v_def), c_emp, length(v_def), c_taille;
  END IF;
  IF position('@repli-debut' in v_def) > 0 THEN
    RAISE EXCEPTION 'STOP : le patch est deja passe';
  END IF;

  a := ARRAY[
    $a1$  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode = '22023'; end if;$a1$,
    $a2$                          when 'closed'     then 'Mandat clos'$a2$
  ];

  b := ARRAY[
    $b1$  -- @repli-debut   CHANTIER 3 (12/10/2026) : LE BIEN PEUT ETRE VENDU OU CLOS
  --
  -- LA REGLE DE LA MAISON, telle que l'ECRAN la porte depuis le 21/05/2026
  -- (`isReadOnlyLightweightDetail`, App.tsx:406-411), et telle que Frederic l'a confirmee
  -- le 12/10 :
  --     · VENDU / CLOS  -> les gestes marchent (l'ecran les ouvre des que le detail est la)
  --     · ARCHIVE       -> LECTURE SEULE, sa seule sortie est « Desarchiver »
  --     · BROUILLON     -> lecture seule
  --
  -- Depuis le 20/05, les Vendu/Clos ne sont plus dans app_dossier_current : ils vivent dans
  -- `app_historical_annonce_index_current`. Cette fonction, ecrite le 25/08, l'ignorait et
  -- refusait 8 941 biens sur un « dossier_not_found » brut, alors que l'ecran affichait le
  -- bouton. L'ecran a trois etats, la base n'en avait qu'un.
  --
  -- ⭐ LE NUMERO RECU EST LE BON. `app_historical_id` n'est pas une serie a part : c'est
  --   NOTRE `app_dossier_id`, renomme (export_app_payload.py:363), verifie par les anciens
  --   travaux des memes biens. On le garde donc TEL QUEL pour les droits, le carnet et le
  --   travail -- aucun faux identifiant n'est pose nulle part.
  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then
    select h.app_historical_id, h.hektor_annonce_id, h.numero_dossier, h.titre_bien,
           h.statut_annonce, h.diffusable, h.archive
      into d.app_dossier_id, d.hektor_annonce_id, d.numero_dossier, d.titre_bien,
           d.statut_annonce, d.diffusable, d.archive
      from public.app_historical_annonce_index_current h
     where h.app_historical_id = target_dossier_id;

    if not found then
      -- UNE ARCHIVE RESTE EN LECTURE SEULE -- c'est voulu, pas un oubli. On le DIT, au lieu
      -- de rendre « dossier_not_found », qui ne veut rien dire pour celui qui lit.
      if exists (select 1 from public.app_archive_annonce_index_current x
                  where x.app_archive_id = target_dossier_id) then
        raise exception 'annonce_archivee_lecture_seule' using errcode = '22023';
      end if;
      raise exception 'dossier_not_found' using errcode = '22023';
    end if;

    -- ⚠ UNE OFFRE, UN COMPROMIS OU UNE VENTE restent reserves au parc vivant : ils creent une
    --   ligne dans le registre des affaires, et une affaire se tient sur un bien en vie.
    if target_status not in ('active', 'closed') then
      raise exception 'transaction_hors_parc_vivant' using errcode = '22023';
    end if;
  end if;
  -- @repli-fin$b1$,
    $b2$                          when 'closed'     then 'Clos'$b2$
  ];

  -- ⚠ LES FINS DE LIGNE WINDOWS -- piege deja paye, et retrouve ce soir.
  --   `v_def` est lu SANS retour chariot (on retire chr(13)). Mais ce script-ci, colle depuis
  --   Windows dans l'editeur SQL, arrive avec des CRLF : l'ancre R1 fait DEUX lignes, elle
  --   portait donc un chr(13) que le corps de la fonction n'a pas -> « trouvee 0 fois ».
  --   On normalise les deux tableaux de la meme facon que le corps : le patch devient
  --   insensible a la maniere dont il est colle.
  FOR i IN 1 .. array_length(a, 1) LOOP
    a[i] := replace(a[i], chr(13), '');
    b[i] := replace(b[i], chr(13), '');
  END LOOP;

  FOR i IN 1 .. array_length(a, 1) LOOP
    n := (length(v_def) - length(replace(v_def, a[i], ''))) / length(a[i]);
    IF n <> 1 THEN
      RAISE EXCEPTION 'STOP : l''ancre R% a ete trouvee % fois, il en faut exactement 1', i, n;
    END IF;
    v_def := replace(v_def, a[i], b[i]);
  END LOOP;

  EXECUTE v_def;

  -- CONTROLE DE SORTIE : le chemin inverse doit rendre l'empreinte d'avant, au caractere pres.
  v_apres  := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  v_retour := v_apres;
  FOR i IN REVERSE array_length(a, 1) .. 1 LOOP
    v_retour := replace(v_retour, b[i], a[i]);
  END LOOP;

  IF md5(v_retour) <> c_emp THEN
    RAISE EXCEPTION 'STOP : en refaisant le chemin inverse on obtient % au lieu de % -- autre chose a change',
      md5(v_retour), c_emp;
  END IF;

  RAISE NOTICE 'OK : 2 remplacements, taille % -> %, le reste est intact (retour = %)',
    c_taille, length(v_apres), md5(v_retour);
END $patch$;

COMMIT;
