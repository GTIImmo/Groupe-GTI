-- ============================================================================
-- REPETITION -- le geste « masquer / afficher une photo » (⑦-8 marche 4)
-- 19/10/2026
-- ⚠⚠ FICHIER GENERE -- ne pas le modifier a la main.
--    Source : patch_chantier7_8_marche4_visibilite_2026-10-19.sql
--    Generateur : scratchpad/generer_repetition_marche4.py
-- ============================================================================
-- ⚠⚠ A COLLER EN UNE SEULE FOIS, EN ENTIER. Le `begin;` de la premiere ligne et
--    l'ERREUR VOLONTAIRE de la derniere font que RIEN n'est ecrit -- ni les trois
--    verrous, ni la RPC, ni le drapeau de la photo, ni le travail.
--
-- ⭐⭐ LE CORPS JOUE EST LE PATCH, EXTRAIT A L'OCTET PRES, pas recopie a la main.
--   Recopier 190 lignes, c'est risquer une divergence invisible -- et alors on
--   eprouve une IMITATION (avertissement du 03/10). Le generateur verifie
--   l'empreinte des deux cotes.
--
-- ELLE JOUE DANS L'ORDRE REEL : mesures AVANT -> LE VRAI PATCH -> le geste sur une
-- VRAIE annonce, DANS LES DEUX SENS -> les refus -> LE VRAI INVERSE -> le retour.
--
-- LA CIBLE : le BAC A SABLE 62774 (app_dossier_id 3828957, 4 photos), photo
--   visible n° 482253. ⭐ C'est le bien d'essai designe du projet.
--
-- ⛔⛔ ELLE N'APPELLE PAS HEKTOR. Elle eprouve LA BASE : les trois verrous et la
--   RPC. Le geste CHEZ HEKTOR est la piece 2 (le worker) et il ne se prouve que
--   par un ESSAI REEL -- accord separe.
--
-- LE MESSAGE ATTENDU si tout va bien :
--   1-avant  | la contrainte / les droits / la distribution  = non, non, non
--   1-avant  | la RPC existe                                 = non
--   1-avant  | 62774 : photos / visibles                     = 4 / 4
--   1-avant  | la photo 482253 est                           = visible
--   2-patch  | la contrainte / les droits / la distribution  = OUI, OUI, OUI
--   2-patch  | la RPC existe (4 parametres)                  = OUI
--   2-patch  | anon peut l appeler                           = NON
--   3-masque | le retour est ok                              = oui, visible=false
--   3-masque | la photo 482253 est devenue                   = masquee
--   3-masque | LE POST-IT est pose (index marques)           = 1 ou plus
--   3-masque | adresses_app_le de 62774                      = A BLANC
--   3-masque | le travail cree, du bon type                  = set_hektor_photo_visibility
--   3-masque | sa charge porte l etat d avant                = true (visible)
--   3-masque | visibles restantes / plus_aucune_visible      = 3 / non
--   4-rejoue | rejouer le MEME masquage                      = deja_dans_cet_etat
--   5-affich | on la REAFFICHE                               = oui, visible=true
--   6-refus  | une photo inconnue                            = photo_introuvable_chez_hektor
--   6-refus  | des parametres vides                          = parametres_incomplets
--   6-refus  | sous l identite d un commercial               = ce que la garde repond VRAIMENT
--   7-retour | la RPC a disparu / les 3 verrous non plus     = oui, oui
-- ============================================================================

begin;

set local lock_timeout = '10s';

create temporary table essai (id serial, etape text, mesure text, valeur text) on commit drop;
create temporary table cible as
  select 3828957::bigint as dossier, '62774'::text as annonce, '482253'::text as photo;

-- ⚠ LA CIBLE EST VERIFIEE AVANT TOUT : un numero ne se devine pas, et une
--   epreuve sur la mauvaise ligne ne prouve rien.
do $garde$
declare v_n integer;
begin
  select count(*) into v_n from public.app_dossier_current d, cible c
   where d.app_dossier_id = c.dossier and d.hektor_annonce_id::text = c.annonce;
  if v_n <> 1 then
    raise exception 'STOP : 3828957 n est pas le dossier de l annonce 62774 -- remesurer';
  end if;
  select count(*) into v_n from public.app_console_photo p, cible c
   where p.app_dossier_id = c.dossier and p.hektor_photo_id = c.photo
     and p.present_in_hektor and p.visible is true;
  if v_n <> 1 then
    raise exception 'STOP : la photo 482253 n est pas VISIBLE sur 62774 -- epreuve NON CONCLUANTE';
  end if;
end $garde$;

-- =============================== 1. AVANT ==================================

insert into essai (etape, mesure, valeur)
select '1-avant ', 'la contrainte connait le type ',
       case when position('set_hektor_photo_visibility' in pg_get_constraintdef(c.oid)) > 0 then 'OUI' else 'non' end
  from pg_constraint c where c.conrelid='public.app_console_job'::regclass
   and c.conname='app_console_job_job_type_check';

insert into essai (etape, mesure, valeur)
select '1-avant ', 'les droits connaissent le type',
       case when position('set_hektor_photo_visibility' in pg_get_functiondef(p.oid)) > 0 then 'OUI' else 'non' end
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='app_console_can_request_job';

insert into essai (etape, mesure, valeur)
select '1-avant ', 'la distribution connait le type',
       case when position('set_hektor_photo_visibility' in pg_get_functiondef(p.oid)) > 0 then 'OUI' else 'non' end
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='app_console_claim_next_job';

insert into essai (etape, mesure, valeur)
select '1-avant ', 'la RPC existe                 ',
       case when exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
                          where n.nspname='public' and p.proname='app_console_photo_visibilite_optimistic')
            then 'OUI' else 'non' end;

insert into essai (etape, mesure, valeur)
select '1-avant ', '62774 : photos / visibles     ',
       count(*)::text || ' / ' || count(*) filter (where p.visible)::text
  from public.app_console_photo p, cible c
 where p.app_dossier_id = c.dossier and p.present_in_hektor;

insert into essai (etape, mesure, valeur)
select '1-avant ', 'la photo 482253 est           ',
       case when p.visible then 'visible' else 'masquee' end
  from public.app_console_photo p, cible c
 where p.app_dossier_id = c.dossier and p.hektor_photo_id = c.photo and p.present_in_hektor;

insert into essai (etape, mesure, valeur)
select '1-avant ', 'adresses_app_le de 62774      ',
       coalesce(d.adresses_app_le::text, 'DEJA A BLANC')
  from public.app_dossier_current d, cible c where d.app_dossier_id = c.dossier;

-- ============ 2. LE VRAI PATCH -- EXTRAIT DU FICHIER, PAS RECOPIE ===========
-- ① LA CONTRAINTE DES TYPES
DO $contrainte$
DECLARE
  v_def   text;
  v_ancre text := replace('''reorder_hektor_photos''::text])))', chr(13), '');
  v_neuf  text;
BEGIN
  SELECT pg_get_constraintdef(c.oid) INTO v_def
    FROM pg_constraint c
   WHERE c.conrelid = 'public.app_console_job'::regclass
     AND c.conname  = 'app_console_job_job_type_check';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : contrainte introuvable'; END IF;

  IF position('set_hektor_photo_visibility' in v_def) > 0 THEN
    RAISE NOTICE 'DEJA FAIT : la contrainte connait set_hektor_photo_visibility';
  ELSE
    IF md5(v_def) <> '2c77f7047159f3b68a19af7ef8fe2242' THEN
      RAISE NOTICE 'ATTENTION : empreinte de contrainte % (attendue 2c77f704...) -- un autre type a ete ajoute depuis. On continue : l''ancre unique est le vrai garde-fou.', md5(v_def);
    END IF;
    IF (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 THEN
      RAISE EXCEPTION 'STOP : l''ancre de la contrainte n''est pas unique';
    END IF;
    v_neuf := replace(v_def, v_ancre,
      replace('''reorder_hektor_photos''::text, ''set_hektor_photo_visibility''::text])))', chr(13), ''));
    EXECUTE 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
    EXECUTE 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check '
            || v_neuf || ' NOT VALID';
  END IF;
END $contrainte$;

-- ② LES DROITS : le negociateur sur SES biens, comme les trois autres gestes photo
DO $droits$
DECLARE
  v_def   text;
  v_ancre text := replace('''reorder_hektor_photos'',', chr(13), '');
BEGIN
  SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_can_request_job';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : app_console_can_request_job introuvable'; END IF;

  IF position('set_hektor_photo_visibility' in v_def) > 0 THEN
    RAISE NOTICE 'DEJA FAIT : les droits connaissent set_hektor_photo_visibility';
    RETURN;
  END IF;
  IF md5(v_def) <> '11a28b2a588212ea2b88d859d6db583d' THEN
    RAISE NOTICE 'ATTENTION : empreinte des droits % (attendue 11a28b2a...). On continue : l''ancre unique est le vrai garde-fou.', md5(v_def);
  END IF;
  IF (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 THEN
    RAISE EXCEPTION 'STOP : l''ancre des droits n''est pas unique';
  END IF;
  EXECUTE replace(v_def, v_ancre,
    replace('''reorder_hektor_photos'',''set_hektor_photo_visibility'',', chr(13), ''));
END $droits$;

-- ③ LA DISTRIBUTION : branche `documents`, collee a ses trois soeurs
DO $distribution$
DECLARE
  v_def   text;
  v_ancre text := replace('''reorder_hektor_photos''', chr(13), '');
BEGIN
  SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_claim_next_job';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : app_console_claim_next_job introuvable'; END IF;

  IF position('set_hektor_photo_visibility' in v_def) > 0 THEN
    RAISE NOTICE 'DEJA FAIT : la distribution connait set_hektor_photo_visibility';
    RETURN;
  END IF;
  IF md5(v_def) <> 'db14e7714742c2eb57ab233aa58c0290' THEN
    RAISE NOTICE 'ATTENTION : empreinte de la distribution % (attendue db14e771...). On continue : l''ancre unique est le vrai garde-fou.', md5(v_def);
  END IF;
  IF (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 THEN
    RAISE EXCEPTION 'STOP : l''ancre de la distribution n''est pas unique';
  END IF;
  EXECUTE replace(v_def, v_ancre,
    replace('''reorder_hektor_photos'',''set_hektor_photo_visibility''', chr(13), ''));
END $distribution$;

-- ④ LA RPC : on ecrit CHEZ NOUS et on cree le travail, en une transaction
CREATE OR REPLACE FUNCTION public.app_console_photo_visibilite_optimistic(
  p_app_dossier_id      bigint,
  p_hektor_annonce_id   text,
  p_hektor_photo_id     text,
  p_visible             boolean
) RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $fn$
DECLARE
  v_annonce text := nullif(btrim(coalesce(p_hektor_annonce_id, '')), '');
  v_photo   text := nullif(btrim(coalesce(p_hektor_photo_id, '')), '');
  v_avant   jsonb;
  v_etat    boolean;
  v_job_id  uuid;
  v_restant integer;
  v_boites  integer := 0;
BEGIN
  -- ⓵ DES PARAMETRES LISIBLES
  IF v_annonce IS NULL OR v_photo IS NULL OR p_app_dossier_id IS NULL OR p_visible IS NULL THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'parametres_incomplets');
  END IF;

  -- ⓶ LES DROITS. La meme garde que deposer, supprimer et mettre en couverture :
  --    le negociateur sur SES biens. On ne fabrique pas une seconde regle.
  IF NOT coalesce(public.app_console_can_access_dossier(p_app_dossier_id, v_annonce), false) THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'droits_insuffisants');
  END IF;

  -- ⓷ L'ETAT D'AVANT DE TOUTE L'ANNONCE, garde dans la charge : c'est le retour
  --    arriere, et il porte le drapeau de CHAQUE photo (pas seulement la cible).
  SELECT jsonb_agg(jsonb_build_object('hektor_photo_id', hektor_photo_id,
                                      'sort_order', sort_order,
                                      'visible', visible)
                   ORDER BY visible DESC, sort_order ASC, id ASC)
    INTO v_avant
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id
     AND present_in_hektor IS TRUE;

  -- ⓸ LA CIBLE DOIT EXISTER ET ETRE CHEZ HEKTOR.
  --    ⚠ ET AVOIR UN NUMERO HEKTOR : une photo deposee par l'app et pas encore
  --      envoyee n'en a pas -- Hektor ne saurait pas de quoi on parle. Meme refus
  --      que pour supprimer et pour la couverture.
  --    ⭐ MAIS ON N'EXIGE PAS QU'ELLE SOIT VISIBLE : ce geste va dans les DEUX
  --      sens, c'est tout son objet.
  SELECT visible INTO v_etat
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id
     AND hektor_photo_id = v_photo
     AND present_in_hektor IS TRUE;
  IF v_etat IS NULL THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'photo_introuvable_chez_hektor');
  END IF;

  -- ⓹ DEJA DANS L'ETAT DEMANDE ? Alors on ne derange pas Hektor.
  IF v_etat = p_visible THEN
    RETURN jsonb_build_object('ok', true, 'deja_dans_cet_etat', true,
                              'visible', p_visible);
  END IF;

  -- ⓺ ⭐⭐ CHEZ NOUS D'ABORD -- la regle de Frederic du 19/10.
  UPDATE public.app_console_photo
     SET visible = p_visible, updated_at = now()
   WHERE app_dossier_id = p_app_dossier_id
     AND hektor_photo_id = v_photo
     AND present_in_hektor IS TRUE;

  -- ⓼ ⭐⭐ ET LA BOITE PUBLIQUE, SANS RECOPIER SA REGLE.
  --    On remet `adresses_app_le` A BLANC sur les quatre index : l'annonce
  --    redevient une CIBLE de `app_photos_remplir_adresses_app`, que le worker
  --    reveillera juste apres son appel Hektor (piece 2).
  --    ⛔ On ne recalcule PAS la boite ici : sa regle (dont le verrou
  --      « visible is not false » pose le 19/10 au matin) vit dans le fabricant,
  --      et deux copies divergeraient au premier ajustement.
  --    ⭐ LE POST-IT N'EST PAS UNE INVENTION : `adresses_app_le IS NULL` est
  --      EXACTEMENT la premiere condition de ciblage du fabricant. On n'apprend
  --      rien de neuf a personne, on utilise son propre mecanisme.
  --    ⚠ LES QUATRE INDEX, PAS SEULEMENT LES VIVANTS : une photo peut etre sur
  --      une annonce ARCHIVEE (14 des 15 annonces a masquees le sont). L'archive
  --      n'a pas de galerie publique, mais elle a une COUVERTURE, et le fabricant
  --      la recalcule depuis le meme ciblage. En oublier un, c'est une vignette
  --      d'archive qui garderait une photo masquee.
  UPDATE public.app_dossier_current SET adresses_app_le = NULL
   WHERE app_dossier_id = p_app_dossier_id AND adresses_app_le IS NOT NULL;
  GET DIAGNOSTICS v_boites = ROW_COUNT;

  UPDATE public.app_archive_annonce_index_current SET adresses_app_le = NULL
   WHERE app_archive_id = p_app_dossier_id AND adresses_app_le IS NOT NULL;
  GET DIAGNOSTICS v_restant = ROW_COUNT;  -- reutilise, puis reecrase juste apres
  v_boites := v_boites + v_restant;

  UPDATE public.app_historical_annonce_index_current SET adresses_app_le = NULL
   WHERE app_historical_id = p_app_dossier_id AND adresses_app_le IS NOT NULL;
  GET DIAGNOSTICS v_restant = ROW_COUNT;
  v_boites := v_boites + v_restant;

  UPDATE public.app_brouillon_annonce_index_current SET adresses_app_le = NULL
   WHERE app_brouillon_id = p_app_dossier_id AND adresses_app_le IS NOT NULL;
  GET DIAGNOSTICS v_restant = ROW_COUNT;
  v_boites := v_boites + v_restant;

  -- ⓼ COMBIEN DE VISIBLES RESTE-T-IL ? On compte APRES l'ecriture du drapeau,
  --    donc la cible est deja dans son nouvel etat : le compte est vrai dans les
  --    DEUX sens, sans cas particulier.
  --    ⚠ `v_restant` vient d'etre ecrase par les GET DIAGNOSTICS ci-dessus -- on
  --      le recalcule donc ici. C'est exactement le genre de reutilisation de
  --      variable qui fait dire une betise a un compte rendu.
  --    ⭐ A QUOI CA SERT : masquer la DERNIERE visible laisse l'annonce sans
  --      couverture ni galerie -- elle affichera « Sans photo ». C'est juste (le
  --      negociateur a tout masque), mais ca ne doit pas etre une SURPRISE :
  --      l'ecran peut demander confirmation avant d'appeler.
  SELECT count(*) INTO v_restant
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id
     AND present_in_hektor IS TRUE
     AND visible IS TRUE;

  -- ⓾ LE TRAVAIL, DANS LA MEME TRANSACTION. Si l'insertion echoue, le drapeau
  --    revient avec elle : on ne reste jamais avec un etat change chez nous et
  --    rien de parti chez Hektor.
  INSERT INTO public.app_console_job
    (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
  VALUES
    ('set_hektor_photo_visibility', p_app_dossier_id, v_annonce,
     jsonb_build_object(
       'hektor_photo_id', v_photo,
       'visible', p_visible,
       'etat_avant', v_etat,
       'base_snapshot', coalesce(v_avant, '[]'::jsonb)),
     20, auth.uid())
  RETURNING id INTO v_job_id;

  RETURN jsonb_build_object(
    'ok', true,
    'deja_dans_cet_etat', false,
    'job_id', v_job_id,
    'visible', p_visible,
    'visibles_restantes', v_restant,
    -- ⭐ LE POST-IT EST-IL POSE ? Si ce compte est 0, le fabricant ne reciblera
    --   PAS l'annonce et la boite resterait vieille : c'est mesurable, donc on le
    --   rend plutot que de l'esperer. (0 est normal si la boite etait deja a
    --   refaire -- adresses_app_le etait DEJA nul.)
    'index_marques_a_refaire', v_boites,
    -- ⭐ LE SIGNAL POUR L'ECRAN : apres ce geste, l'annonce n'a plus AUCUNE
    --   photo publiable. A dire a l'humain, pas a decouvrir le lendemain.
    'plus_aucune_visible', (p_visible IS FALSE AND v_restant = 0));
END $fn$;

REVOKE ALL ON FUNCTION public.app_console_photo_visibilite_optimistic(bigint, text, text, boolean) FROM public;
GRANT EXECUTE ON FUNCTION public.app_console_photo_visibilite_optimistic(bigint, text, text, boolean)
  TO authenticated, service_role;

COMMENT ON FUNCTION public.app_console_photo_visibilite_optimistic(bigint, text, text, boolean) IS
  '(7)-8 marche 4 (19/10/2026) : masque ou affiche une photo. Ecrit le drapeau CHEZ NOUS '
  'et cree le travail set_hektor_photo_visibility dans la meme transaction, avec l''etat '
  'd''avant de toute l''annonce dans base_snapshot. Remet adresses_app_le a blanc pour que '
  'le fabricant de la boite publique recible l''annonce (le worker le reveille). Garde : '
  'app_console_can_access_dossier. Rend plus_aucune_visible quand le geste laisse '
  'l''annonce sans aucune photo publiable.';

-- ============================ 2bis. LE PATCH A-T-IL PRIS ? ==================

insert into essai (etape, mesure, valeur)
select '2-patch ', 'la contrainte connait le type ',
       case when position('set_hektor_photo_visibility' in pg_get_constraintdef(c.oid)) > 0 then 'OUI' else 'NON -- ECHEC' end
  from pg_constraint c where c.conrelid='public.app_console_job'::regclass
   and c.conname='app_console_job_job_type_check';

insert into essai (etape, mesure, valeur)
select '2-patch ', 'les droits connaissent le type',
       case when position('set_hektor_photo_visibility' in pg_get_functiondef(p.oid)) > 0 then 'OUI' else 'NON -- ECHEC' end
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='app_console_can_request_job';

insert into essai (etape, mesure, valeur)
select '2-patch ', 'la distribution connait le type',
       case when position('set_hektor_photo_visibility' in pg_get_functiondef(p.oid)) > 0 then 'OUI' else 'NON -- ECHEC' end
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='app_console_claim_next_job';

insert into essai (etape, mesure, valeur)
select '2-patch ', 'la RPC existe (nb parametres) ',
       'OUI (' || p.pronargs::text || ' parametres)'
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='app_console_photo_visibilite_optimistic';

-- ⚠ LE DROIT `anon` : la lecon du 08/10 (chantier ①) -- Supabase pose un GRANT
--   a `authenticated` sur TOUTE fonction neuve, et un `revoke from public` ne
--   l'enleve pas. On verifie donc ce que dit VRAIMENT proacl, pas ce que le
--   patch annonce.
insert into essai (etape, mesure, valeur)
select '2-patch ', 'anon peut l appeler           ',
       case when array_to_string(p.proacl, ' ') like '%anon=%' then 'OUI -- ECHEC' else 'NON' end
       || '  (authenticated : ' ||
       case when array_to_string(p.proacl, ' ') like '%authenticated=%' then 'oui' else 'NON' end || ')'
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='app_console_photo_visibilite_optimistic';

-- ========================= 3. LE GESTE : ON MASQUE =========================

create temporary table retour as
  select public.app_console_photo_visibilite_optimistic(c.dossier, c.annonce, c.photo, false) as r
    from cible c;

insert into essai (etape, mesure, valeur)
select '3-masque', 'le retour est ok              ',
       case when (r->>'ok') = 'true'
            then 'oui, visible=' || coalesce(r->>'visible','?')
            else 'NON : ' || coalesce(r->>'erreur','?') end
  from retour;

insert into essai (etape, mesure, valeur)
select '3-masque', 'la photo 482253 est devenue   ',
       case when p.visible then 'visible -- ECHEC' else 'masquee' end
  from public.app_console_photo p, cible c
 where p.app_dossier_id = c.dossier and p.hektor_photo_id = c.photo;

insert into essai (etape, mesure, valeur)
select '3-masque', 'LE POST-IT (index marques)    ',
       coalesce(r->>'index_marques_a_refaire','?')
       || case when coalesce((r->>'index_marques_a_refaire')::int, 0) = 0
               then '  (0 est normal si adresses_app_le etait DEJA a blanc)' else '' end
  from retour;

insert into essai (etape, mesure, valeur)
select '3-masque', 'adresses_app_le de 62774      ',
       case when d.adresses_app_le is null then 'A BLANC -- le fabricant la reciblera'
            else 'ENCORE POSEE (' || d.adresses_app_le::text || ') -- ECHEC' end
  from public.app_dossier_current d, cible c where d.app_dossier_id = c.dossier;

insert into essai (etape, mesure, valeur)
select '3-masque', 'le travail cree, du bon type  ',
       coalesce(j.job_type, 'AUCUN TRAVAIL -- ECHEC')
       || case when j.status is not null then ' (' || j.status || ')' else '' end
  from retour r left join public.app_console_job j on j.id = (r.r->>'job_id')::uuid;

insert into essai (etape, mesure, valeur)
select '3-masque', 'sa charge : l etat d avant    ',
       coalesce(j.payload_json->>'etat_avant', '(absent) -- ECHEC')
       || ', demande=' || coalesce(j.payload_json->>'visible','?')
       || ', photos dans base_snapshot=' ||
       coalesce(jsonb_array_length(j.payload_json->'base_snapshot')::text, '?')
  from retour r left join public.app_console_job j on j.id = (r.r->>'job_id')::uuid;

insert into essai (etape, mesure, valeur)
select '3-masque', 'visibles restantes / derniere ',
       coalesce(r->>'visibles_restantes','?') || ' / plus_aucune_visible=' ||
       coalesce(r->>'plus_aucune_visible','?')
  from retour;

-- ===================== 4. ON REJOUE LE MEME MASQUAGE =======================
-- ⭐ Il ne doit PAS deranger Hektor une seconde fois.

insert into essai (etape, mesure, valeur)
select '4-rejoue', 'rejouer le MEME masquage      ',
       case when (x->>'deja_dans_cet_etat') = 'true' then 'deja_dans_cet_etat -- Hektor non derange'
            when (x->>'ok') = 'true' then 'UN SECOND TRAVAIL A ETE CREE -- ECHEC'
            else 'refus : ' || coalesce(x->>'erreur','?') end
  from (select public.app_console_photo_visibilite_optimistic(c.dossier, c.annonce, c.photo, false) as x
          from cible c) z;

-- ========================= 5. ET ON LA REAFFICHE ===========================
-- ⭐ LE TEMOIN INVERSE DU GESTE : la meme commande dans l'autre sens.

create temporary table retour2 as
  select public.app_console_photo_visibilite_optimistic(c.dossier, c.annonce, c.photo, true) as r
    from cible c;

insert into essai (etape, mesure, valeur)
select '5-affich', 'on la REAFFICHE               ',
       case when (r->>'ok') = 'true' then 'oui, visible=' || coalesce(r->>'visible','?')
            else 'NON : ' || coalesce(r->>'erreur','?') end
  from retour2;

insert into essai (etape, mesure, valeur)
select '5-affich', 'la photo 482253 est revenue   ',
       case when p.visible then 'visible' else 'masquee -- ECHEC' end
  from public.app_console_photo p, cible c
 where p.app_dossier_id = c.dossier and p.hektor_photo_id = c.photo;

insert into essai (etape, mesure, valeur)
select '5-affich', 'deux travaux distincts crees  ',
       case when (select r->>'job_id' from retour) is distinct from (select r->>'job_id' from retour2)
            then 'oui' else 'NON -- ECHEC' end;

-- ============================== 6. LES REFUS ===============================

insert into essai (etape, mesure, valeur)
select '6-refus ', 'une photo inconnue            ',
       coalesce(x->>'erreur', 'AUCUN REFUS -- ECHEC')
  from (select public.app_console_photo_visibilite_optimistic(c.dossier, c.annonce, '999999999', false) as x
          from cible c) z;

insert into essai (etape, mesure, valeur)
select '6-refus ', 'des parametres vides          ',
       coalesce(x->>'erreur', 'AUCUN REFUS -- ECHEC')
  from (select public.app_console_photo_visibilite_optimistic(null, '', '', null) as x) z;

-- ========================== 7. LE VRAI INVERSE =============================
-- ⚠ L'ORDRE EST CELUI DE L'INVERSE : la RPC d'abord, la contrainte en dernier.

drop function if exists public.app_console_photo_visibilite_optimistic(bigint, text, text, boolean);

do $inv_distrib$
declare v_def text; v_pose text := replace(',''set_hektor_photo_visibility''', chr(13), '');
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_def
    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='app_console_claim_next_job';
  if position(v_pose in v_def) > 0 then execute replace(v_def, v_pose, ''); end if;
end $inv_distrib$;

do $inv_droits$
declare v_def text; v_pose text := replace('''set_hektor_photo_visibility'',', chr(13), '');
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_def
    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='app_console_can_request_job';
  if position(v_pose in v_def) > 0 then execute replace(v_def, v_pose, ''); end if;
end $inv_droits$;

do $inv_contrainte$
declare v_def text; v_pose text := replace(', ''set_hektor_photo_visibility''::text', chr(13), ''); v_neuf text;
begin
  select pg_get_constraintdef(c.oid) into v_def from pg_constraint c
   where c.conrelid='public.app_console_job'::regclass and c.conname='app_console_job_job_type_check';
  if position(v_pose in v_def) > 0 then
    v_neuf := replace(v_def, v_pose, '');
    execute 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
    execute 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check '
            || v_neuf || ' NOT VALID';
  end if;
end $inv_contrainte$;

insert into essai (etape, mesure, valeur)
select '7-retour', 'la RPC a disparu              ',
       case when exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
                          where n.nspname='public' and p.proname='app_console_photo_visibilite_optimistic')
            then 'NON -- ECHEC' else 'oui' end;

insert into essai (etape, mesure, valeur)
select '7-retour', 'les 3 verrous ne connaissent + ',
       case when (select position('set_hektor_photo_visibility' in pg_get_constraintdef(c.oid))
                    from pg_constraint c where c.conrelid='public.app_console_job'::regclass
                     and c.conname='app_console_job_job_type_check') = 0
             and (select position('set_hektor_photo_visibility' in pg_get_functiondef(p.oid))
                    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
                   where n.nspname='public' and p.proname='app_console_can_request_job') = 0
             and (select position('set_hektor_photo_visibility' in pg_get_functiondef(p.oid))
                    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
                   where n.nspname='public' and p.proname='app_console_claim_next_job') = 0
            then 'oui, aucune trace' else 'NON -- ECHEC' end;

-- ================== 8. L ERREUR VOLONTAIRE : tout est annule ================
-- ⚠ Le compte rendu voyage DANS le message : un SELECT d une transaction qui
--   echoue n est pas toujours rendu par l editeur SQL.

do $fin$
declare v_txt text;
begin
  select string_agg(etape || ' | ' || mesure || ' = ' || valeur, chr(10) order by id)
    into v_txt from essai;
  raise exception '%', 'ESSAI ANNULE -- rien n a ete ecrit : ni les verrous, ni la RPC, ni le drapeau de la photo, ni les travaux.'
    || chr(10) || v_txt;
end
$fin$;

rollback;
