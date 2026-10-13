-- =====================================================================
-- CHANTIER ③ -- 3c : LA DATE DE CLOTURE DU MANDAT DEVIENT LA NOTRE
-- Date : 2026-10-13 · Detail : notice/CHANTIER_3_HEKTOR_DABORD_2026-10-12.md
-- Pieces 1 et 2 sur 5. Ordre valide par Frederic le 13/10 : 1+2, puis 4, puis 3+5.
--
-- SA DEMANDE, MOT POUR MOT : « la date de cloture doit donc etre une colonne
-- supplementaire, et cette colonne doit etre maj eventuellement par Hektor mais
-- SURTOUT PAS l'app -- mais cette demande n'a pas a etre transmise a Hektor. »
--   ➡ donc DEUX colonnes : celle de Hektor, et LA NOTRE. Plus jamais melangees.
--
-- POURQUOI UNE COLONNE, ET PAS UNE JOINTURE. Le carnet `app_mandat_champ_app` a
-- RLS activee et ZERO politique : une vue en `security_invoker` qui le joindrait
-- rendrait la date VIDE POUR TOUT LE MONDE. Mesure du 13/10.
--
-- ⭐ CE PATRON EST DEJA EN SERVICE DANS CETTE VUE, POUR LES PHOTOS :
--      COALESCE(NULLIF(btrim(photo_url_listing_app), ''), photo_url_listing) AS photo_url_listing,
--      photo_url_listing_app,                              -- la notre, nue
--      photo_url_listing AS photo_url_listing_hektor       -- celle de Hektor, nue
--    et il tient sur 24 497 lignes sur 24 505. On le recopie, c'est tout.
--
-- ⚠ LA CAUSE RACINE QU'ON SUPPRIME ICI. Aujourd'hui le worker ecrit NOTRE date
--   dans LA COLONNE DE HEKTOR (`PATCH ... {mandat_date_cloture}`), puis
--   magasin_mandat_app.py relit ce meme registre comme « ce que dit l'app ».
--   NOUS RELISIONS NOTRE PROPRE ECRITURE COMME SI ELLE FAISAIT AUTORITE : c'est
--   pour ca que 4 lignes du carnet portaient une valeur qui n'etait la decision
--   de personne. La colonne separee ferme la boucle.
--
-- CE QUE FAIT CE PATCH -- quatre gestes, tous verifies avant d'ecrire :
--   1. la colonne `mandat_date_cloture_app` sur la table du registre ;
--   2. la vue REFAITE DEPUIS ELLE-MEME (jamais recopiee a la main) : notre date
--      passe devant, les deux restent lisibles separement -> 71 colonnes -> 73 ;
--   3. `app_generate_mandat_echu_alerts` : elle lit LA TABLE, pas la vue. Sans
--      ce geste, l'alerte « Mandat echu » NE DISPARAITRAIT PAS sur un mandat
--      qu'on clot. Mesure du 13/10 : c'est le SEUL autre consommateur ;
--   4. la re-pose des clotures deja faites par l'app, depuis le carnet.
--   puis PIECE 2 : le RPC de saisie `app_set_mandat_cloture_optimistic`.
--
-- CE QUI NE CHANGE PAS : rien ne part chez Hektor · le run n'est pas touche
-- (pieces 4) · le worker n'est pas touche (piece 5) · aucun nom de colonne
-- retire ni renomme · les droits de la table · les politiques RLS.
--
-- ⚠ A SAVOIR AVANT DE COLLER : sans la PIECE 4 (la re-pose apres le push), les
--   dates reposees au point 4 repartiront a la prochaine nuit -- la nuit efface
--   et reinsere la ligne du parc vivant. C'est voulu : on avance par paliers.
--
-- RETOUR ARRIERE : supabase/patch_chantier3_3c_cloture_mandat_app_2026-10-13_INVERSE.sql
-- REPETITION     : supabase/patch_chantier3_3c_cloture_mandat_app_2026-10-13_REPETITION.sql
-- ⚠ NE LE COLLER QU'UNE SEULE FOIS : le message de succes est un NOTICE, que
--   l'editeur Supabase n'affiche pas. Un second collage sera refuse par le
--   garde-fou d'empreinte, et ce refus NE VEUT PAS DIRE que le premier a echoue.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 1. LA COLONNE. Elle n'est ecrite NI par le constructeur du registre NI par
--    le push -- exactement comme `photo_url_listing_app` (zero occurrence des
--    deux cotes, mesure du 13/10). Elle est a nous seuls.
-- ---------------------------------------------------------------------
alter table public.app_mandat_register_current
  add column if not exists mandat_date_cloture_app text;

comment on column public.app_mandat_register_current.mandat_date_cloture_app is
  'Date de cloture du mandat SAISIE DANS L''APP (AAAA-MM-JJ). Hektor n''y touche '
  'jamais et ne la recoit jamais. Le carnet app_mandat_champ_app fait foi ; cette '
  'colonne est la vitrine, re-posee apres chaque push (piece 4 du chantier 3c).';

-- ---------------------------------------------------------------------
-- 2. LA VUE. On ne la recopie pas : on la RELIT et on la transforme. Recopier
--    71 colonnes a la main, c'est se donner une chance d'en perdre une en
--    silence. `CREATE OR REPLACE VIEW` suffit (on AJOUTE deux colonnes a la
--    fin) : pas de DROP, donc les droits et les dependances sont preserves.
-- ---------------------------------------------------------------------
DO $patch$
DECLARE
  c_emp    constant text := '5c64469d579405d028554350d3d44883';
  c_taille constant int  := 1873;

  v_def text; v_new text;
  a text; b text; n int;
BEGIN
  v_def := replace(pg_get_viewdef('public.app_registre_mandats_current'::regclass, true),
                   chr(13), '');

  IF md5(v_def) <> c_emp THEN
    RAISE EXCEPTION 'STOP : la vue porte % (taille %) au lieu de % (taille %)',
      md5(v_def), length(v_def), c_emp, c_taille;
  END IF;
  IF position('mandat_date_cloture_app' in v_def) > 0 THEN
    RAISE EXCEPTION 'STOP : le patch est deja passe (la vue cite deja mandat_date_cloture_app)';
  END IF;

  -- R1 -- NOTRE DATE PASSE DEVANT, SANS CHANGER LE NOM DE LA COLONNE.
  -- Le front derive le statut du mandat (Actif/Clos/Echu) de `mandat_date_cloture`
  -- (App.tsx l. 7667, api.ts l. 85) et le demande par son nom dans ses `select`
  -- (api.ts l. 6162 et 6221). Renommer casserait l'ecran ; on garde le nom et on
  -- change ce qu'il contient. C'est la decision de Frederic du 13/10 :
  -- « 1 celle de l'app ».
  -- ⚠ Ancre MULTILIGNE : les deux cotes sont normalises sans chr(13), sinon un
  --   script colle depuis Windows ne la trouve pas (piege mesure le 12/10).
  a := chr(10) || '    mandat_date_cloture,' || chr(10);
  b := chr(10) || '    COALESCE(NULLIF(btrim(mandat_date_cloture_app), ''''::text), mandat_date_cloture) AS mandat_date_cloture,' || chr(10);
  n := (length(v_def) - length(replace(v_def, a, ''))) / length(a);
  IF n <> 1 THEN
    RAISE EXCEPTION 'STOP : ancre R1 trouvee % fois, il en faut exactement 1', n;
  END IF;
  v_new := replace(v_def, a, b);

  -- R2 -- LES DEUX COLONNES NUES, A LA FIN, comme pour les photos. Elles servent
  -- a REPONDRE A LA QUESTION « qui a dit quoi » : l'ecran pourra montrer notre
  -- date ET celle de Hektor cote a cote, sans deviner.
  a := '    mandants_json' || chr(10) || '   FROM app_mandat_register_current r;';
  b := '    mandants_json,' || chr(10)
       || '    mandat_date_cloture_app,' || chr(10)
       || '    mandat_date_cloture AS mandat_date_cloture_hektor' || chr(10)
       || '   FROM app_mandat_register_current r;';
  n := (length(v_new) - length(replace(v_new, a, ''))) / length(a);
  IF n <> 1 THEN
    RAISE EXCEPTION 'STOP : ancre R2 trouvee % fois, il en faut exactement 1', n;
  END IF;
  v_new := replace(v_new, a, b);

  EXECUTE 'create or replace view public.app_registre_mandats_current '
          || 'with (security_invoker=on) as ' || v_new;

  -- CONTROLE DE SORTIE : le chemin inverse doit rendre l'empreinte d'avant,
  -- caractere pour caractere. Sinon autre chose a change et on refuse tout.
  IF md5(replace(replace(v_new, b, a),
                 chr(10) || '    COALESCE(NULLIF(btrim(mandat_date_cloture_app), ''''::text), mandat_date_cloture) AS mandat_date_cloture,' || chr(10),
                 chr(10) || '    mandat_date_cloture,' || chr(10))) <> c_emp THEN
    RAISE EXCEPTION 'STOP : le chemin inverse de la vue ne rend pas % -- on annule', c_emp;
  END IF;

  RAISE NOTICE 'OK vue : % -> % caracteres', length(v_def), length(v_new);
END $patch$;

-- ---------------------------------------------------------------------
-- 3. L'ALERTE « MANDAT ECHU ». Elle lit LA TABLE, pas la vue -- donc le
--    COALESCE ci-dessus ne l'atteint pas. Sans ce geste, une alerte
--    reapparaitrait sur un mandat que Frederic vient de clore : la promesse
--    « l'alerte disparait » serait fausse.
--    Mesure du 13/10 : `app_generate_mandat_echu_alerts` est le SEUL autre
--    consommateur de `mandat_date_cloture` dans toute la base.
-- ---------------------------------------------------------------------
DO $patch$
DECLARE
  c_sig constant text := 'public.app_generate_mandat_echu_alerts()';
  c_emp constant text := 'd45b9290d12bfca81f37713c4d361150';

  v_def text; v_apres text; a text; b text; n int;
BEGIN
  v_def := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');

  IF md5(v_def) <> c_emp THEN
    RAISE EXCEPTION 'STOP alerte : empreinte % (taille %) au lieu de %',
      md5(v_def), length(v_def), c_emp;
  END IF;
  IF position('mandat_date_cloture_app' in v_def) > 0 THEN
    RAISE EXCEPTION 'STOP alerte : le patch est deja passe';
  END IF;

  -- ⚠ CETTE ANCRE EST PRESENTE DEUX FOIS, et c'est normal : une fois pour
  --   EFFACER l'alerte d'un mandat clos, une fois pour NE PAS LA CREER. Les
  --   deux doivent changer -- sinon l'alerte serait supprimee puis recreee
  --   chaque nuit, ce qui est pire que de ne rien faire.
  a := replace($a1$          and nullif(btrim(coalesce(r.mandat_date_cloture, '')), '') is not null$a1$,
               chr(13), '');
  b := replace($b1$          and (nullif(btrim(coalesce(r.mandat_date_cloture_app, '')), '') is not null
               or nullif(btrim(coalesce(r.mandat_date_cloture, '')), '') is not null)$b1$,
               chr(13), '');

  n := (length(v_def) - length(replace(v_def, a, ''))) / length(a);
  IF n <> 2 THEN
    RAISE EXCEPTION 'STOP alerte : ancre trouvee % fois, il en faut exactement 2', n;
  END IF;

  EXECUTE replace(v_def, a, b);

  v_apres := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  IF md5(replace(v_apres, b, a)) <> c_emp THEN
    RAISE EXCEPTION 'STOP alerte : le chemin inverse rend % au lieu de %',
      md5(replace(v_apres, b, a)), c_emp;
  END IF;

  RAISE NOTICE 'OK alerte : % -> % caracteres, les 2 ancres changees',
    length(v_def), length(v_apres);
END $patch$;

-- ---------------------------------------------------------------------
-- 4. LA RE-POSE DES CLOTURES DEJA FAITES PAR L'APP.
--    On ne cite AUCUN numero en dur : on lit le carnet, et seulement les lignes
--    dont l'origine est `cloture_app` -- les VRAIES decisions de l'app, avec leur
--    auteur. ⚠ Les lignes `observe` sont ECARTEES : leur `valeur_app` est ce que
--    le registre AFFICHAIT, d'origine inconnue (souvent notre propre PATCH relu).
--    Les reprendre serait blanchir du Hektor en decision de l'app.
-- ---------------------------------------------------------------------
update public.app_mandat_register_current r
   set mandat_date_cloture_app = nullif(btrim(k.valeur_app), '')
  from public.app_mandat_champ_app k
 where k.champ   = 'mandat_date_cloture'
   and k.origine = 'cloture_app'
   and nullif(btrim(coalesce(k.valeur_app, '')), '') is not null
   and r.hektor_annonce_id::text = k.hektor_annonce_id
   and r.numero_mandat::text     = k.numero_mandat;

-- ---------------------------------------------------------------------
-- PIECE 2 -- LE RPC DE SAISIE.
--
-- POURQUOI UN RPC ET PAS UNE ECRITURE DIRECTE. Le carnet a RLS activee et ZERO
-- politique : le front ne peut NI le lire NI l'ecrire. Il faut donc un
-- SECURITY DEFINER, comme tous les autres gestes du projet.
--
-- IL ECRIT AUX DEUX ENDROITS, DANS LA MEME TRANSACTION :
--   le CARNET   -> c'est lui qui fait foi, la nuit ne le touche jamais ;
--   la VITRINE  -> pour que l'ecran le voie tout de suite, sans attendre la nuit.
-- Si l'un des deux echoue, AUCUN des deux n'est ecrit.
--
-- UNE DATE VIDE EFFACE LA NOTRE, et celle de Hektor reapparait. C'est le retour
-- arriere de l'utilisateur quand il s'est trompe -- sans quoi une faute de
-- saisie serait definitive.
--
-- IL N'ENVOIE RIEN CHEZ HEKTOR. C'est la demande de Frederic, explicite.
-- ---------------------------------------------------------------------
create or replace function public.app_set_mandat_cloture_optimistic(
  target_annonce       text,
  target_numero_mandat text,
  cloture_date         text default null
) returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $fn$
DECLARE
  v_annonce text := nullif(btrim(coalesce(target_annonce, '')), '');
  v_numero  text := nullif(btrim(coalesce(target_numero_mandat, '')), '');
  v_date    text := nullif(btrim(coalesce(cloture_date, '')), '');

  v_claims  jsonb;
  v_sub     text;
  v_role    text;
  v_email   text;

  v_avant_app     text;
  v_avant_hektor  text;
  v_trouve        boolean := false;
BEGIN
  -- ① QUI DEMANDE. Un anonyme n'ecrit pas (chantier ①). Le service_role est
  --    admis : le worker appellera ce meme RPC a la piece 5, plutot que
  --    d'ecrire a cote.
  BEGIN
    v_claims := nullif(current_setting('request.jwt.claims', true), '')::jsonb;
  EXCEPTION WHEN others THEN
    v_claims := null;
  END;
  v_sub   := nullif(btrim(coalesce(v_claims ->> 'sub',  '')), '');
  v_role  := nullif(btrim(coalesce(v_claims ->> 'role', '')), '');
  v_email := nullif(btrim(coalesce(v_claims ->> 'email', '')), '');

  IF v_sub is null AND coalesce(v_role, '') <> 'service_role' THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'non_authentifie');
  END IF;

  -- ② DES PARAMETRES LISIBLES.
  IF v_annonce is null OR v_numero is null THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'parametres_incomplets',
                              'annonce', v_annonce, 'numero_mandat', v_numero);
  END IF;

  -- ③ UNE VRAIE DATE. La forme d'abord, puis l'existence : « 2026-13-32 » a la
  --    bonne forme et n'existe pas. On refuse les deux plutot que d'ecrire un
  --    texte que personne ne saura relire.
  IF v_date is not null THEN
    IF v_date !~ '^\d{4}-\d{2}-\d{2}$' THEN
      RETURN jsonb_build_object('ok', false, 'erreur', 'date_illisible', 'valeur', v_date);
    END IF;
    BEGIN
      PERFORM v_date::date;
    EXCEPTION WHEN others THEN
      RETURN jsonb_build_object('ok', false, 'erreur', 'date_inexistante', 'valeur', v_date);
    END;
  END IF;

  -- ④ LE MANDAT DOIT EXISTER. Mesure du 13/10 : le couple (annonce, numero) est
  --    UNIQUE au registre -- 24 505 lignes pour 24 505 couples, aucune sans
  --    numero. On n'ecrit donc jamais a cote, et on ne devine jamais le mandat
  --    cible (c'est l'erreur qui a fait debrancher la cloture chez Hektor le 28/08).
  SELECT true, r.mandat_date_cloture_app, r.mandat_date_cloture
    INTO v_trouve, v_avant_app, v_avant_hektor
    FROM public.app_mandat_register_current r
   WHERE r.hektor_annonce_id::text = v_annonce
     AND r.numero_mandat::text     = v_numero;

  IF NOT coalesce(v_trouve, false) THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'mandat_introuvable',
                              'annonce', v_annonce, 'numero_mandat', v_numero);
  END IF;

  -- ⑤ LE CARNET -- CE QUI FAIT FOI.
  IF v_date is null THEN
    DELETE FROM public.app_mandat_champ_app
     WHERE hektor_annonce_id = v_annonce
       AND numero_mandat     = v_numero
       AND champ             = 'mandat_date_cloture'
       AND origine           = 'cloture_app';
  ELSE
    INSERT INTO public.app_mandat_champ_app
      (hektor_annonce_id, numero_mandat, champ, valeur_app, origine, ecrit_par, ecrit_le)
    VALUES
      (v_annonce, v_numero, 'mandat_date_cloture', v_date, 'cloture_app',
       coalesce(v_email, v_sub), now())
    ON CONFLICT (hektor_annonce_id, numero_mandat, champ) DO UPDATE
       SET valeur_app = excluded.valeur_app,
           origine    = 'cloture_app',
           ecrit_par  = excluded.ecrit_par,
           ecrit_le   = now();
  END IF;

  -- ⑥ LA VITRINE -- POUR QUE L'ECRAN LE VOIE TOUT DE SUITE.
  UPDATE public.app_mandat_register_current
     SET mandat_date_cloture_app = v_date
   WHERE hektor_annonce_id::text = v_annonce
     AND numero_mandat::text     = v_numero;

  RETURN jsonb_build_object(
    'ok', true,
    'annonce', v_annonce,
    'numero_mandat', v_numero,
    'date_cloture', v_date,
    'efface', (v_date is null),
    'avant_app', v_avant_app,
    'date_hektor', v_avant_hektor,
    'ecrit_par', coalesce(v_email, v_sub, 'service_role')
  );
END $fn$;

-- LES DROITS. Par defaut Postgres donne EXECUTE a PUBLIC, donc a `anon` :
-- on le retire, puis on l'accorde nommement (esprit du chantier ①).
revoke all on function public.app_set_mandat_cloture_optimistic(text, text, text) from public;
grant execute on function public.app_set_mandat_cloture_optimistic(text, text, text)
  to authenticated, service_role;

comment on function public.app_set_mandat_cloture_optimistic(text, text, text) is
  'Chantier 3c, 13/10/2026. Saisit (ou efface) la date de cloture du mandat DANS '
  'NOS DONNEES : carnet app_mandat_champ_app (fait foi) + colonne '
  'mandat_date_cloture_app du registre (vitrine), dans la meme transaction. '
  'N''envoie RIEN chez Hektor et ne touche JAMAIS mandat_date_cloture, qui '
  'appartient a Hektor. Une date vide efface la notre.';

notify pgrst, 'reload schema';

COMMIT;
