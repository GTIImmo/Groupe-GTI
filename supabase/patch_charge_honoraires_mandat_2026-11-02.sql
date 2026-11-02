-- =====================================================================
-- LA CHARGE DES HONORAIRES, MEMORISEE SUR LE MANDAT        02/11/2026
-- Palier 1 (la base). Patron recopie : patch_chantier3_3c_cloture_mandat_app.
--
-- DEMANDE DE FREDERIC (02/11) : « lorsqu'on edite un mandat pour signature le
--   choix de la charge des honoraires doit etre memorise dans le registre des
--   mandats », et « a la saisie de la modale offre ou compromis il faudrait que
--   la charge de la commission se pre-remplisse mais reste modifiable ».
--
-- SES QUATRE DECISIONS DU 02/11, et ce patch les respecte :
--   1. on memorise DES QU'ON GENERE LE DOCUMENT (pas a la signature) ;
--   2. L'AVENANT N'ECRASE PAS -- le mandat d'origine fait foi. Tenu par le
--      FRONT, qui n'appelle pas cette RPC en mode avenant (piece F) ;
--   3. defaut « vendeur » des deux cotes (piece F) ;
--   4. deux paliers : LA BASE ICI, le pre-remplissage de la modale ensuite.
--
-- POURQUOI CE CHAMP EST LEGITIME CHEZ NOUS. Le critere du projet est ecrit dans
--   magasin_mandat_app.py:58 : on ne confie a l'app que les champs « ou Hektor
--   n'a rien a dire ». La date de cloture a franchi ce critere a 0,4 % (94
--   mandats sur 24 939). La charge, Hektor n'en porte RIEN : mesure du 02/11
--   sur les raw_json -- mandat 17 cles, compromis 16, vente 19, AUCUNE charge.
--   Et elle ne se deduit pas de ses chiffres : le 14/10, sur 25 lignes ou le
--   classeur dit « Acquereur », 13 etaient rangees cote vendeur chez lui.
--
-- ⭐⭐⭐ LA LECON DU PATRON, ET C'EST LA PIECE QU'ON OUBLIERAIT :
--   LE CARNET FAIT FOI, LA COLONNE DU REGISTRE EST UN REFLET QU'ON REPOSE.
--   La ligne du registre est detruite puis refaite par le worker a chaque push
--   d'une annonce (push_single_annonce_to_supabase.py), et par le run en mode
--   --rebuild-register-only (push_upgrade_to_supabase.py:1300, delete_all_rows).
--   Sans la fonction de re-pose, la charge disparaitrait de l'ecran.
--
-- ⚠ CE QUE J'AI MESURE LE 02/11 ET QUI CORRIGE LA SPEC :
--   . le RUN DE NUIT ORDINAIRE NE TOUCHE PAS cette table (le delete_all_rows
--     est sous `if args.rebuild_register_only`). Seuls le worker et ce mode
--     manuel la refont. La re-pose reste donc necessaire, mais le risque
--     quotidien est celui du WORKER, pas de la nuit.
--   . CINQ fonctions lisent la table, AUCUNE la vue :
--     app_generate_mandat_echu_alerts · app_photos_remplir_adresses_registre
--     app_registre_dossiers · app_reposer_cloture_mandat_app
--     app_set_mandat_cloture_optimistic
--     ⭐ AUCUNE ne fait `select *`, AUCUNE n'utilise %rowtype, toutes rendent un
--     type fixe -> AJOUTER UNE COLONNE NE PEUT CASSER AUCUNE DES CINQ. Mesure,
--     pas supposition. Et aucune n'a besoin de la charge : le patron du 13/10
--     avait une piece 3 pour les alertes, ici elle N'A PAS D'EQUIVALENT.
--
-- CE QUI NE CHANGE PAS : rien ne part chez Hektor (il n'a aucune destination) ·
--   le run n'est pas touche · le worker n'est pas touche par ce patch (piece F)
--   · aucune colonne retiree ni renommee · les droits · les politiques RLS ·
--   la cloture de mandat (ses deux fonctions ne sont pas modifiees).
--
-- RETOUR ARRIERE : patch_charge_honoraires_mandat_2026-11-02_INVERSE.sql
-- REPETITION     : patch_charge_honoraires_mandat_2026-11-02_REPETITION.sql
-- ⚠ NE LE COLLER QU'UNE SEULE FOIS. Le message de succes est un NOTICE, que
--   l'editeur Supabase n'affiche pas. Un second collage sera refuse par le
--   garde-fou d'empreinte, et CE REFUS NE VEUT PAS DIRE que le premier a echoue.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- A. LA COLONNE. Elle est a nous seuls : ni le constructeur du registre ni le
--    push ne l'ecrivent -- exactement comme mandat_date_cloture_app et
--    photo_url_listing_app.
--    ⛔ JAMAIS une colonne de Hektor : c'est la cause racine que le patron du
--      13/10 a fermee (« nous relisions notre propre ecriture comme si elle
--      faisait autorite »). Le suffixe _app n'est pas une decoration.
-- ---------------------------------------------------------------------
alter table public.app_mandat_register_current
  add column if not exists mandat_charge_honoraires_app text;

comment on column public.app_mandat_register_current.mandat_charge_honoraires_app is
  'Qui paie les honoraires : vendeur | acquereur. A NOUS (Hektor ne porte pas '
  'cette notion : 0 cle sur les 17 du mandat, mesure du 02/11). Reflet du '
  'carnet app_mandat_champ_app (champ = charge_commission), repose apres chaque '
  'push par app_reposer_charge_mandat_app(). 02/11/2026.';

-- ---------------------------------------------------------------------
-- B. LA VUE, REFAITE DEPUIS ELLE-MEME -- jamais recopiee a la main.
--    ⚠ CREATE OR REPLACE VIEW interdit d'inserer une colonne au milieu : on
--      AJOUTE A LA FIN. C'est pour ca que le patron du 13/10 a mis
--      mandat_date_cloture_app et _hektor en queue.
--    ⚠ LECON 30 : l'ancre tient sur UNE SEULE LIGNE, et on normalise chr(13).
-- ---------------------------------------------------------------------
DO $do$
DECLARE
  v_def    text;
  v_ancre  text := '    mandat_date_cloture AS mandat_date_cloture_hektor';
  v_ajout  text;
  v_occ    int;
BEGIN
  v_def := replace(pg_get_viewdef('public.app_registre_mandats_current'::regclass, true),
                   chr(13), '');

  IF position('mandat_charge_honoraires_app' in v_def) > 0 THEN
    RAISE EXCEPTION 'STOP : le patch est deja passe (la vue cite deja mandat_charge_honoraires_app)';
  END IF;

  v_occ := (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre);
  IF v_occ <> 1 THEN
    RAISE EXCEPTION 'STOP : l''ancre de la vue est presente % fois, il en faut exactement 1', v_occ;
  END IF;

  v_ajout := v_ancre || ',' || chr(10) || '    mandat_charge_honoraires_app';
  v_def   := replace(v_def, v_ancre, v_ajout);

  EXECUTE 'CREATE OR REPLACE VIEW public.app_registre_mandats_current AS ' || v_def;
  RAISE NOTICE 'B : la vue porte desormais mandat_charge_honoraires_app';
END $do$;

-- ---------------------------------------------------------------------
-- D. LA RE-POSE. Patron : app_reposer_cloture_mandat_app, a l'identique --
--    meme garde-fou de plancher, meme « poser puis effacer », meme forme de
--    compte rendu. Les DEUX moities sont necessaires : sans la seconde, une
--    charge retiree du carnet resterait a l'ecran et l'app mentirait.
-- ---------------------------------------------------------------------
create or replace function public.app_reposer_charge_mandat_app(
  target_annonce    text default null,
  plancher_registre int  default 10000
) returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $fn$
DECLARE
  v_annonce  text   := nullif(btrim(coalesce(target_annonce, '')), '');
  v_plancher int    := greatest(coalesce(plancher_registre, 10000), 0);
  v_lignes   bigint;
  v_carnet   bigint;
  v_posees   bigint := 0;
  v_effacees bigint := 0;
BEGIN
  -- ① LE GARDE-FOU. Un registre anormalement petit = un push casse : on ne
  --    touche a rien. Mieux vaut une charge qui attend qu'un parc vide.
  SELECT count(*) INTO v_lignes FROM public.app_mandat_register_current;
  IF v_lignes < v_plancher THEN
    RETURN jsonb_build_object(
      'statut', 'refus',
      'raison', format('le registre ne porte que %s lignes, sous le plancher de %s',
                       v_lignes, v_plancher),
      'lignes_registre', v_lignes);
  END IF;

  SELECT count(*) INTO v_carnet
    FROM public.app_mandat_champ_app
   WHERE champ = 'charge_commission'
     AND origine = 'mandat_app'
     AND nullif(btrim(coalesce(valeur_app, '')), '') IS NOT NULL;

  -- ② ON POSE CE QUE LE CARNET DIT.
  --    ⚠ le `<>` evite de reecrire une ligne deja juste : un push ordinaire ne
  --      touchera donc AUCUNE ligne, et le compte rendu le dira.
  WITH poses AS (
    UPDATE public.app_mandat_register_current r
       SET mandat_charge_honoraires_app = nullif(btrim(k.valeur_app), '')
      FROM public.app_mandat_champ_app k
     WHERE k.champ   = 'charge_commission'
       AND k.origine = 'mandat_app'
       AND nullif(btrim(coalesce(k.valeur_app, '')), '') IS NOT NULL
       AND r.hektor_annonce_id::text = k.hektor_annonce_id
       AND r.numero_mandat::text     = k.numero_mandat
       AND (v_annonce IS NULL OR r.hektor_annonce_id::text = v_annonce)
       AND coalesce(r.mandat_charge_honoraires_app, '') <> nullif(btrim(k.valeur_app), '')
    RETURNING 1)
  SELECT count(*) INTO v_posees FROM poses;

  -- ③ ON EFFACE LA OU LE CARNET NE DIT PLUS RIEN -- c'est la moitie qui rend
  --    le geste REVERSIBLE.
  WITH effacements AS (
    UPDATE public.app_mandat_register_current r
       SET mandat_charge_honoraires_app = NULL
     WHERE nullif(btrim(coalesce(r.mandat_charge_honoraires_app, '')), '') IS NOT NULL
       AND (v_annonce IS NULL OR r.hektor_annonce_id::text = v_annonce)
       AND NOT EXISTS (
         SELECT 1 FROM public.app_mandat_champ_app k
          WHERE k.champ   = 'charge_commission'
            AND k.origine = 'mandat_app'
            AND nullif(btrim(coalesce(k.valeur_app, '')), '') IS NOT NULL
            AND k.hektor_annonce_id = r.hektor_annonce_id::text
            AND k.numero_mandat     = r.numero_mandat::text)
    RETURNING 1)
  SELECT count(*) INTO v_effacees FROM effacements;

  RETURN jsonb_build_object(
    'statut', 'ok',
    'annonce', v_annonce,
    'lignes_registre', v_lignes,
    'lignes_carnet', v_carnet,
    'posees', v_posees,
    'effacees', v_effacees);
END $fn$;

revoke all on function public.app_reposer_charge_mandat_app(text, int) from public;
-- ⛔⛔ LE REVOKE NOMME EST OBLIGATOIRE, mesure a l'epreuve du 02/11 :
--   un DROIT PAR DEFAUT du schema public (pg_default_acl, pose par postgres)
--   donne authenticated=X a TOUTE fonction neuve, et `from public` NE L'ENLEVE
--   PAS (le pseudo-role public n'est pas le role authenticated). Sans cette
--   ligne, n'importe quel utilisateur connecte pourrait lancer une re-pose
--   GLOBALE. Sa jumelle app_reposer_cloture_mandat_app est bien fermee : c'est
--   la comparaison avec elle qui a fait sortir le rouge.
revoke execute on function public.app_reposer_charge_mandat_app(text, int)
  from anon, authenticated;
grant execute on function public.app_reposer_charge_mandat_app(text, int)
  to service_role;

comment on function public.app_reposer_charge_mandat_app(text, int) is
  'Le registre REFLETE le carnet pour la charge des honoraires. A appeler APRES '
  'chaque push d''annonce : la ligne du registre est detruite puis refaite, et '
  'la colonne _app repartirait a NULL. Patron : app_reposer_cloture_mandat_app. '
  '02/11/2026.';

-- ---------------------------------------------------------------------
-- E. LA SAISIE. Patron : app_set_mandat_cloture_optimistic.
--    ⭐ ELLE GARDE L'AUTEUR, et ce n'est pas un detail : le 21/10 on a mesure
--      que le WORKER ecrit ce carnet SANS utilisateur et EFFACE ainsi la trace
--      de l'humain (ecrit_par passe a NULL). C'est de l'argent : la charge doit
--      etre ecrite PAR LE FRONT, avec le jeton de celui qui a choisi.
--    ⚠ LE VOCABULAIRE. Le document de mandat dit « mandant », la transaction et
--      le classeur disent « vendeur ». On traduit ICI, sur LE MOT DU MENU, et
--      jamais en relisant un role de contact -- notre « Mandant » est pollue
--      depuis le 17/07 (l'acheteur y est range a tort).
-- ---------------------------------------------------------------------
create or replace function public.app_set_mandat_charge_optimistic(
  target_annonce       text,
  target_numero_mandat text,
  charge               text default null
) returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $fn$
DECLARE
  v_annonce text := nullif(btrim(coalesce(target_annonce, '')), '');
  v_numero  text := nullif(btrim(coalesce(target_numero_mandat, '')), '');
  v_charge  text := nullif(btrim(coalesce(charge, '')), '');

  v_claims  jsonb;
  v_sub     text;
  v_role    text;
  v_email   text;

  v_avant   text;
  v_trouve  boolean := false;
BEGIN
  -- ① QUI DEMANDE. Un anonyme n'ecrit pas (chantier ①). Le service_role est
  --    admis pour qu'un rattrapage puisse passer par la meme porte.
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

  IF v_annonce is null OR v_numero is null THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'parametres_incomplets',
                              'annonce', v_annonce, 'numero_mandat', v_numero);
  END IF;

  -- ② LA TRADUCTION ET LE CONTROLE. « mandant » est le mot du document,
  --    « vendeur » celui de la transaction et du classeur : une seule valeur
  --    doit sortir d'ici, sinon on fabriquerait deux vocabulaires.
  IF v_charge is not null THEN
    v_charge := lower(v_charge);
    v_charge := translate(v_charge, 'eeeeaaaiioouuu', 'eeeeaaaiioouuu');
    v_charge := translate(v_charge, 'éèêëàâäïîôöùûü', 'eeeeaaaiioouuu');
    IF v_charge = 'mandant' THEN
      v_charge := 'vendeur';
    END IF;
    IF v_charge not in ('vendeur', 'acquereur') THEN
      RETURN jsonb_build_object('ok', false, 'erreur', 'charge_invalide',
                                'valeur', charge);
    END IF;
  END IF;

  -- ③ LE MANDAT DOIT EXISTER. Le couple (annonce, numero) est UNIQUE au
  --    registre (mesure du 13/10 : 24 505 lignes pour 24 505 couples) : on
  --    n'ecrit donc jamais a cote, et on ne devine jamais le mandat cible.
  SELECT true, r.mandat_charge_honoraires_app
    INTO v_trouve, v_avant
    FROM public.app_mandat_register_current r
   WHERE r.hektor_annonce_id::text = v_annonce
     AND r.numero_mandat::text     = v_numero;

  IF NOT coalesce(v_trouve, false) THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'mandat_introuvable',
                              'annonce', v_annonce, 'numero_mandat', v_numero);
  END IF;

  -- ④ LE CARNET -- CE QUI FAIT FOI, et ce qui survit a un retour arriere.
  IF v_charge is null THEN
    DELETE FROM public.app_mandat_champ_app
     WHERE hektor_annonce_id = v_annonce
       AND numero_mandat     = v_numero
       AND champ             = 'charge_commission'
       AND origine           = 'mandat_app';
  ELSE
    INSERT INTO public.app_mandat_champ_app
      (hektor_annonce_id, numero_mandat, champ, valeur_app, origine, ecrit_par, ecrit_le)
    VALUES
      (v_annonce, v_numero, 'charge_commission', v_charge, 'mandat_app',
       coalesce(v_email, v_sub), now())
    ON CONFLICT (hektor_annonce_id, numero_mandat, champ) DO UPDATE
       SET valeur_app = excluded.valeur_app,
           origine    = 'mandat_app',
           ecrit_par  = excluded.ecrit_par,
           ecrit_le   = now();
  END IF;

  -- ⑤ LA VITRINE -- POUR QUE L'ECRAN LE VOIE TOUT DE SUITE.
  UPDATE public.app_mandat_register_current
     SET mandat_charge_honoraires_app = v_charge
   WHERE hektor_annonce_id::text = v_annonce
     AND numero_mandat::text     = v_numero;

  RETURN jsonb_build_object(
    'ok', true,
    'annonce', v_annonce,
    'numero_mandat', v_numero,
    'charge', v_charge,
    'efface', (v_charge is null),
    'avant', v_avant,
    'ecrit_par', coalesce(v_email, v_sub, 'service_role'));
END $fn$;

revoke all on function public.app_set_mandat_charge_optimistic(text, text, text) from public;
grant execute on function public.app_set_mandat_charge_optimistic(text, text, text)
  to authenticated, service_role;

comment on function public.app_set_mandat_charge_optimistic(text, text, text) is
  'Memorise QUI PAIE les honoraires sur un mandat, au moment ou le document est '
  'genere. Ecrit le carnet (qui fait foi) PUIS la vitrine. Traduit « mandant » '
  'en « vendeur ». Appelee par le FRONT pour garder l''auteur -- le worker, lui, '
  'ecrit sans utilisateur et effacerait ecrit_par (mesure du 21/10). 02/11/2026.';

-- ---------------------------------------------------------------------
-- LES CONTROLES. Ils s'executent DANS la transaction : un rouge annule tout.
-- ---------------------------------------------------------------------
DO $do$
DECLARE
  v_col  int;
  v_vue  int;
  v_f1   int;
  v_f2   int;
  v_perd int;
  v_dr   int;
BEGIN
  SELECT count(*) INTO v_col FROM information_schema.columns
   WHERE table_schema = 'public' AND table_name = 'app_mandat_register_current'
     AND column_name = 'mandat_charge_honoraires_app';
  IF v_col <> 1 THEN RAISE EXCEPTION 'CONTROLE A : la colonne manque'; END IF;

  SELECT count(*) INTO v_vue FROM information_schema.columns
   WHERE table_schema = 'public' AND table_name = 'app_registre_mandats_current'
     AND column_name = 'mandat_charge_honoraires_app';
  IF v_vue <> 1 THEN RAISE EXCEPTION 'CONTROLE B : la vue ne porte pas la colonne'; END IF;

  -- ⭐ TEMOIN INVERSE : la cloture doit etre INTACTE dans la vue. Si la
  --    reconstruction avait perdu une colonne, c'est ici qu'on le verrait.
  SELECT count(*) INTO v_perd FROM information_schema.columns
   WHERE table_schema = 'public' AND table_name = 'app_registre_mandats_current'
     AND column_name in ('mandat_date_cloture', 'mandat_date_cloture_app',
                         'mandat_date_cloture_hektor');
  IF v_perd <> 3 THEN
    RAISE EXCEPTION 'CONTROLE B bis : la vue a PERDU une colonne de cloture (% sur 3)', v_perd;
  END IF;

  SELECT count(*) INTO v_f1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_reposer_charge_mandat_app';
  IF v_f1 <> 1 THEN RAISE EXCEPTION 'CONTROLE D : la re-pose manque'; END IF;

  SELECT count(*) INTO v_f2 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_set_mandat_charge_optimistic';
  IF v_f2 <> 1 THEN RAISE EXCEPTION 'CONTROLE E : la saisie manque'; END IF;

  -- ⭐ CONTROLE DES DROITS -- ajoute le 02/11 APRES que l'epreuve a sorti un
  --   rouge ici. Une seule des deux fonctions doit etre ouverte a
  --   authenticated : LA SAISIE. La re-pose est un geste de service.
  SELECT count(*) INTO v_dr FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public'
     AND p.proname in ('app_reposer_charge_mandat_app', 'app_set_mandat_charge_optimistic')
     AND has_function_privilege('authenticated', p.oid, 'execute');
  IF v_dr <> 1 THEN
    RAISE EXCEPTION 'CONTROLE DROITS : % fonction(s) ouverte(s) a authenticated, il en faut 1 (la saisie seule)', v_dr;
  END IF;

  SELECT count(*) INTO v_dr FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public'
     AND p.proname in ('app_reposer_charge_mandat_app', 'app_set_mandat_charge_optimistic')
     AND has_function_privilege('anon', p.oid, 'execute');
  IF v_dr <> 0 THEN
    RAISE EXCEPTION 'CONTROLE DROITS : anon peut executer % fonction(s), il en faut 0', v_dr;
  END IF;

  RAISE NOTICE 'LES 7 CONTROLES SONT VERTS. colonne OK · vue OK · cloture intacte (3/3) · re-pose OK · saisie OK · droits authenticated 1/1 · anon 0';
END $do$;

COMMIT;
