-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE V — le compromis verrouillé par sa vente    23/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE (erreur volontaire « ESSAI ANNULE -- … ») : rien ne reste, ni les fonctions
--   modifiées, ni l'interrupteur, ni les travaux, ni le registre.
-- Le VRAI PATCH, puis les fonctions appelées COMME L'ÉCRAN, au nom de Frédéric, sur la chaîne d'essai 1001390
-- de VA6482 (offre 1001390, compromis 1001391 = 50136, vente 1001392 = 23357 ; essai 4 du 23/10).
--   T1 ÉTEINT : modifier le compromis → accepté (le témoin inverse : le défaut)
--   T2 allumé : modifier le compromis → REFUSÉ « compromis_verrouille »
--   T3 allumé : annuler le compromis → REFUSÉ   · T4 allumé : supprimer le compromis → REFUSÉ
--   T5 allumé : modifier la VENTE → accepté (la vente n'est pas verrouillée)
--   T6 allumé : le verrou de l'OFFRE répond toujours (refuser l'offre → « offre_verrouillee »)
--   T7 allumé : la vente EFFACÉE chez Hektor ne verrouille plus → modifier le compromis accepté
--   T8 l'inverse rend 20eeca7c et 43247de7.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    res jsonb;
    err text;
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.app_affaire_ledger WHERE app_affaire_id = 1001391 AND kind = 'compromis')
       OR NOT EXISTS (SELECT 1 FROM public.app_affaire_ledger WHERE app_affaire_id = 1001392 AND kind = 'vente' AND present_in_hektor IS NOT FALSE) THEN
        RAISE EXCEPTION '%', 'ARRET : la chaine d''essai 1001390 n''a plus son compromis ou sa vente -- la repetition ne prouverait rien.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    insert into public.app_setting (key, value, description, updated_at)
    values ('compromis_verrouille_par_vente', 'off',
            'Chantier 8 / V 23/10/2026 : on = un COMPROMIS dont la chaine porte une VENTE ne se modifie, ne s''annule et ne se supprime plus (« pour revenir sur le compromis, il faut d''abord supprimer la vente » -- decision de Frederic). Voir supabase/patch_v_compromis_verrouille_2026-10-23.sql. off = comportement d''avant.',
            now())
    on conflict (key) do nothing;
    EXECUTE $exec_g$ DO $pose_g_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_geste_affaire_optimistic(bigint,text,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($ga1$  -- Une transaction DEJA dans cet etat : on ne renvoie pas de travail pour rien.$ga1$, chr(13), '')];
    neufs text[] := array[
        replace($gn1$  -- ⛔ ─── V (23/10/2026, chantier 8) : LE COMPROMIS EST VERROUILLE PAR SA VENTE ─── ⛔
  -- Decision de Frederic : « apres la vente tout est verrouille ; pour modifier quoi que ce soit sur
  -- le compromis, il faut d'abord supprimer la vente ». Meme regle que l'offre ci-dessus (16/09).
  -- Essai reel du 23/10 (compromis 50135/50136) : sans elle, modifier le compromis d'une chaine vendue
  -- remettait le bien « Sous compromis » chez Hektor. Interrupteur 'compromis_verrouille_par_vente'.
  IF a.kind = 'compromis' AND geste IN ('annuler', 'supprimer') AND a.app_chaine_id IS NOT NULL
     AND coalesce((select s.value from public.app_setting s where s.key = 'compromis_verrouille_par_vente'), 'off') = 'on' THEN
      SELECT l.hektor_affaire_id::text INTO bloc_id
        FROM app_affaire_ledger l
       WHERE l.app_chaine_id = a.app_chaine_id
         AND l.app_affaire_id <> a.app_affaire_id
         AND l.kind = 'vente'
         AND NOT (btrim(coalesce(l.hektor_affaire_id::text, '')) <> ''
                  AND l.present_in_hektor IS FALSE)
       LIMIT 1;
    IF FOUND THEN
      RAISE EXCEPTION 'compromis_verrouille: ce dossier porte une vente (n° %). Pour revenir sur le compromis, il faut d''abord supprimer la vente.',
        coalesce(nullif(btrim(bloc_id), ''), '?') USING errcode = '22023';
    END IF;
  END IF;

  -- Une transaction DEJA dans cet etat : on ne renvoie pas de travail pour rien.$gn1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = 'a65692290a679d603916b9d635192b80' THEN
        RAISE NOTICE '%', 'Deja pose : app_geste_affaire_optimistic porte deja l''empreinte a6569229. Rien n''est ecrit.'; RETURN;
    END IF;
    IF md5(d) <> '20eeca7cc00bd4afe5b4175febacb2f7' THEN
        RAISE EXCEPTION '%', format('ARRET : app_geste_affaire_optimistic a l''empreinte %s, attendu 20eeca7c. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_geste_affaire_optimistic, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> 'a65692290a679d603916b9d635192b80' THEN
        RAISE EXCEPTION '%', format('ARRET : app_geste_affaire_optimistic, le texte rendu a l''empreinte %s, attendu a6569229 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_geste_affaire_optimistic(bigint,text,integer)'::regprocedure), chr(13), '')) <> 'a65692290a679d603916b9d635192b80' THEN
        RAISE EXCEPTION '%', 'ARRET : app_geste_affaire_optimistic, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose_g_rep$ $exec_g$;
    EXECUTE $exec_m$ DO $pose_m_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($ma1$  select * into d from app_dossier_current where app_dossier_id = a.app_dossier_id;$ma1$, chr(13), '')];
    neufs text[] := array[
        replace($mn1$  -- ⛔ ─── V (23/10/2026, chantier 8) : LE COMPROMIS EST VERROUILLE PAR SA VENTE ─── ⛔
  -- Voir app_geste_affaire_optimistic. Modifier le compromis d'une chaine vendue renvoie son statut a
  -- Hektor (« Sous compromis ») alors que la vente existe. ⚠ v_cible sert ici de tampon : elle est
  -- reaffectee plus bas (genre vise), sans rapport.
  if a.kind = 'compromis' and a.app_chaine_id is not null and coalesce((select s.value from public.app_setting s where s.key = 'compromis_verrouille_par_vente'), 'off') = 'on' then
      SELECT l.hektor_affaire_id::text INTO v_cible
        FROM app_affaire_ledger l
       WHERE l.app_chaine_id = a.app_chaine_id
         AND l.app_affaire_id <> a.app_affaire_id
         AND l.kind = 'vente'
         AND NOT (btrim(coalesce(l.hektor_affaire_id::text, '')) <> ''
                  AND l.present_in_hektor IS FALSE)
       LIMIT 1;
    if found then
      raise exception 'compromis_verrouille: ce dossier porte une vente (n° %). Pour revenir sur le compromis, il faut d''abord supprimer la vente.',
        coalesce(nullif(btrim(v_cible), ''), '?') using errcode = '22023';
    end if;
  end if;

  select * into d from app_dossier_current where app_dossier_id = a.app_dossier_id;$mn1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '910e79470819a1111d21b608625f95b8' THEN
        RAISE NOTICE '%', 'Deja pose : app_modifier_affaire_optimistic porte deja l''empreinte 910e7947. Rien n''est ecrit.'; RETURN;
    END IF;
    IF md5(d) <> '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, attendu 43247de7. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '910e79470819a1111d21b608625f95b8' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, le texte rendu a l''empreinte %s, attendu 910e7947 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) <> '910e79470819a1111d21b608625f95b8' THEN
        RAISE EXCEPTION '%', 'ARRET : app_modifier_affaire_optimistic, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose_m_rep$ $exec_m$;

    -- T1 ETEINT
    err := '';
    BEGIN
      res := public.app_modifier_affaire_optimistic(1001391, jsonb_build_object('amount', '115000', 'champs_touches', jsonb_build_array()), 9);
      delete from public.app_console_job where id::text = res->>'job_id';
    EXCEPTION WHEN others THEN err := SQLERRM;
    END;
    total := total + 1;
    IF err = '' THEN ok := ok + 1; r := r || ' | T1 OK eteint : modifier le compromis est accepte';
    ELSE r := r || ' | T1 ECHEC eteint : modifier le compromis est accepte : ' || coalesce(err, 'null'); END IF;

    update public.app_setting set value = 'on' where key = 'compromis_verrouille_par_vente';
    -- T2
    err := '';
    BEGIN
      res := public.app_modifier_affaire_optimistic(1001391, jsonb_build_object('amount', '115000', 'champs_touches', jsonb_build_array()), 9);
      delete from public.app_console_job where id::text = res->>'job_id';
    EXCEPTION WHEN others THEN err := SQLERRM;
    END;
    total := total + 1;
    IF err like 'compromis_verrouille:%' and err like '%23357%' THEN ok := ok + 1; r := r || ' | T2 OK allume : modifier le compromis est refuse';
    ELSE r := r || ' | T2 ECHEC allume : modifier le compromis est refuse : ' || coalesce(nullif(err, ''), 'null'); END IF;
    -- T3
    err := '';
    BEGIN
      res := public.app_geste_affaire_optimistic(1001391, 'annuler', 9);
      delete from public.app_console_job where id::text = res->>'job_id';
    EXCEPTION WHEN others THEN err := SQLERRM;
    END;
    total := total + 1;
    IF err like 'compromis_verrouille:%' THEN ok := ok + 1; r := r || ' | T3 OK allume : annuler le compromis est refuse';
    ELSE r := r || ' | T3 ECHEC allume : annuler le compromis est refuse : ' || coalesce(nullif(err, ''), 'null'); END IF;
    -- T4
    err := '';
    BEGIN
      res := public.app_geste_affaire_optimistic(1001391, 'supprimer', 9);
      delete from public.app_console_job where id::text = res->>'job_id';
    EXCEPTION WHEN others THEN err := SQLERRM;
    END;
    total := total + 1;
    IF err like 'compromis_verrouille:%' THEN ok := ok + 1; r := r || ' | T4 OK allume : supprimer le compromis est refuse';
    ELSE r := r || ' | T4 ECHEC allume : supprimer le compromis est refuse : ' || coalesce(nullif(err, ''), 'null'); END IF;
    -- T5
    err := '';
    BEGIN
      res := public.app_modifier_affaire_optimistic(1001392, jsonb_build_object('amount', '115000', 'champs_touches', jsonb_build_array()), 9);
      delete from public.app_console_job where id::text = res->>'job_id';
    EXCEPTION WHEN others THEN err := SQLERRM;
    END;
    total := total + 1;
    IF err = '' THEN ok := ok + 1; r := r || ' | T5 OK allume : modifier la vente reste accepte';
    ELSE r := r || ' | T5 ECHEC allume : modifier la vente reste accepte : ' || coalesce(err, 'null'); END IF;
    -- T6
    err := '';
    BEGIN
      res := public.app_geste_affaire_optimistic(1001390, 'refus', 9);
      delete from public.app_console_job where id::text = res->>'job_id';
    EXCEPTION WHEN others THEN err := SQLERRM;
    END;
    total := total + 1;
    IF err like 'offre_verrouillee:%' THEN ok := ok + 1; r := r || ' | T6 OK le verrou de l offre repond toujours';
    ELSE r := r || ' | T6 ECHEC le verrou de l offre repond toujours : ' || coalesce(nullif(err, ''), 'null'); END IF;
    -- T7
    update public.app_affaire_ledger set present_in_hektor = false where app_affaire_id = 1001392;
    err := '';
    BEGIN
      res := public.app_modifier_affaire_optimistic(1001391, jsonb_build_object('amount', '115000', 'champs_touches', jsonb_build_array()), 9);
      delete from public.app_console_job where id::text = res->>'job_id';
    EXCEPTION WHEN others THEN err := SQLERRM;
    END;
    update public.app_affaire_ledger set present_in_hektor = true where app_affaire_id = 1001392;
    total := total + 1;
    IF err = '' THEN ok := ok + 1; r := r || ' | T7 OK une vente effacee chez Hektor ne verrouille plus';
    ELSE r := r || ' | T7 ECHEC une vente effacee chez Hektor ne verrouille plus : ' || coalesce(err, 'null'); END IF;

    -- T8 L'INVERSE
    EXECUTE $exec_ig$ DO $retour_g_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_geste_affaire_optimistic(bigint,text,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($ga1$  -- Une transaction DEJA dans cet etat : on ne renvoie pas de travail pour rien.$ga1$, chr(13), '')];
    neufs text[] := array[
        replace($gn1$  -- ⛔ ─── V (23/10/2026, chantier 8) : LE COMPROMIS EST VERROUILLE PAR SA VENTE ─── ⛔
  -- Decision de Frederic : « apres la vente tout est verrouille ; pour modifier quoi que ce soit sur
  -- le compromis, il faut d'abord supprimer la vente ». Meme regle que l'offre ci-dessus (16/09).
  -- Essai reel du 23/10 (compromis 50135/50136) : sans elle, modifier le compromis d'une chaine vendue
  -- remettait le bien « Sous compromis » chez Hektor. Interrupteur 'compromis_verrouille_par_vente'.
  IF a.kind = 'compromis' AND geste IN ('annuler', 'supprimer') AND a.app_chaine_id IS NOT NULL
     AND coalesce((select s.value from public.app_setting s where s.key = 'compromis_verrouille_par_vente'), 'off') = 'on' THEN
      SELECT l.hektor_affaire_id::text INTO bloc_id
        FROM app_affaire_ledger l
       WHERE l.app_chaine_id = a.app_chaine_id
         AND l.app_affaire_id <> a.app_affaire_id
         AND l.kind = 'vente'
         AND NOT (btrim(coalesce(l.hektor_affaire_id::text, '')) <> ''
                  AND l.present_in_hektor IS FALSE)
       LIMIT 1;
    IF FOUND THEN
      RAISE EXCEPTION 'compromis_verrouille: ce dossier porte une vente (n° %). Pour revenir sur le compromis, il faut d''abord supprimer la vente.',
        coalesce(nullif(btrim(bloc_id), ''), '?') USING errcode = '22023';
    END IF;
  END IF;

  -- Une transaction DEJA dans cet etat : on ne renvoie pas de travail pour rien.$gn1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '20eeca7cc00bd4afe5b4175febacb2f7' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_geste_affaire_optimistic porte deja l''empreinte d''avant (20eeca7c).'; RETURN;
    END IF;
    IF md5(d) <> 'a65692290a679d603916b9d635192b80' THEN
        RAISE EXCEPTION '%', format('ARRET : app_geste_affaire_optimistic a l''empreinte %s, attendu a6569229. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_geste_affaire_optimistic, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '20eeca7cc00bd4afe5b4175febacb2f7' THEN
        RAISE EXCEPTION '%', format('ARRET : app_geste_affaire_optimistic, le texte rendu a l''empreinte %s, attendu 20eeca7c (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_geste_affaire_optimistic(bigint,text,integer)'::regprocedure), chr(13), '')) <> '20eeca7cc00bd4afe5b4175febacb2f7' THEN
        RAISE EXCEPTION '%', 'ARRET : app_geste_affaire_optimistic, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$retour_g_rep$ $exec_ig$;
    EXECUTE $exec_im$ DO $retour_m_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($ma1$  select * into d from app_dossier_current where app_dossier_id = a.app_dossier_id;$ma1$, chr(13), '')];
    neufs text[] := array[
        replace($mn1$  -- ⛔ ─── V (23/10/2026, chantier 8) : LE COMPROMIS EST VERROUILLE PAR SA VENTE ─── ⛔
  -- Voir app_geste_affaire_optimistic. Modifier le compromis d'une chaine vendue renvoie son statut a
  -- Hektor (« Sous compromis ») alors que la vente existe. ⚠ v_cible sert ici de tampon : elle est
  -- reaffectee plus bas (genre vise), sans rapport.
  if a.kind = 'compromis' and a.app_chaine_id is not null and coalesce((select s.value from public.app_setting s where s.key = 'compromis_verrouille_par_vente'), 'off') = 'on' then
      SELECT l.hektor_affaire_id::text INTO v_cible
        FROM app_affaire_ledger l
       WHERE l.app_chaine_id = a.app_chaine_id
         AND l.app_affaire_id <> a.app_affaire_id
         AND l.kind = 'vente'
         AND NOT (btrim(coalesce(l.hektor_affaire_id::text, '')) <> ''
                  AND l.present_in_hektor IS FALSE)
       LIMIT 1;
    if found then
      raise exception 'compromis_verrouille: ce dossier porte une vente (n° %). Pour revenir sur le compromis, il faut d''abord supprimer la vente.',
        coalesce(nullif(btrim(v_cible), ''), '?') using errcode = '22023';
    end if;
  end if;

  select * into d from app_dossier_current where app_dossier_id = a.app_dossier_id;$mn1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_modifier_affaire_optimistic porte deja l''empreinte d''avant (43247de7).'; RETURN;
    END IF;
    IF md5(d) <> '910e79470819a1111d21b608625f95b8' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, attendu 910e7947. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, le texte rendu a l''empreinte %s, attendu 43247de7 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) <> '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE EXCEPTION '%', 'ARRET : app_modifier_affaire_optimistic, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$retour_m_rep$ $exec_im$;
    total := total + 1;
    IF md5(replace(pg_get_functiondef('public.app_geste_affaire_optimistic(bigint,text,integer)'::regprocedure), chr(13), '')) = '20eeca7cc00bd4afe5b4175febacb2f7' and md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) = '43247de7ff89e395d3b6e970353a891b' THEN ok := ok + 1; r := r || ' | T8 OK l inverse rend les deux empreintes';
    ELSE r := r || ' | T8 ECHEC l inverse rend les deux empreintes : ' || coalesce('empreinte differente', 'null'); END IF;

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
