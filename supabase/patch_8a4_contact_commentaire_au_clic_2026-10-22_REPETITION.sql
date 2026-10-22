-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE 8a-A — le commentaire au clic                              22/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE : tout se passe dans UN bloc qui finit par une erreur
--   volontaire (« ESSAI ANNULE -- … ») ; le message porte le résultat. Rien ne reste :
--   ni la fonction modifiée, ni l'interrupteur, ni la saisie, ni la ligne d'attente.
-- Elle joue LE VRAI PATCH (mêmes ancres), puis appelle la fonction COMME L'ÉCRAN, au nom
-- de Frédéric, sur le contact d'essai 20000007 (« ESSAI 8A BIS », à supprimer) :
--   T1 interrupteur ÉTEINT  → le commentaire n'est PAS écrit (le témoin inverse) ;
--   T2 interrupteur ALLUMÉ  → il est écrit, il est dans la ligne d'attente, et sa valeur
--      d'avant est dans la photo ;
--   T3 les 12 autres champs s'écrivent toujours (nom changé dans T1 et T2) ;
--   T4 l'alias `commentaires` marche aussi ;
--   T5 l'inverse rend l'empreinte 79d39e0e.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    cid text := '20000007';
    avant_com text;
    r text := '';
    v text;
    snap jsonb;
    pf jsonb;
    ok int := 0;
    total int := 0;
BEGIN
    IF NOT EXISTS (select 1 from public.app_contact_current where hektor_contact_id = cid) THEN
        RAISE EXCEPTION '%', 'ARRET : le contact d''essai 20000007 n''existe plus -- la repetition ne prouverait rien.';
    END IF;
    IF EXISTS (select 1 from public.app_contact_pending where hektor_contact_id = cid) THEN
        RAISE EXCEPTION '%', 'ARRET : le contact d''essai a deja une saisie en attente -- la repetition la melangerait.';
    END IF;
    select commentaires into avant_com from public.app_contact_current where hektor_contact_id = cid;

    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    insert into public.app_setting (key, value, description, updated_at)
    values ('contact_commentaire_au_clic', 'off',
            'Chantier 8 / 8a-A 22/10/2026 : on = le commentaire saisi en modifiant un contact s''ecrit chez nous au clic (voir supabase/patch_8a4_contact_commentaire_au_clic_2026-10-22.sql). off = comportement d''avant (il n''arrive qu''au retour de Hektor).',
            now())
    on conflict (key) do nothing;
    EXECUTE $exec_pose$ DO $pose_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_edit_contact_optimistic(text,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  k text;$a1$, chr(13), ''),
        replace($a2$  if edit_fields is null or edit_fields = '{}'::jsonb then raise exception 'no_fields' using errcode='22023'; end if;$a2$, chr(13), ''),
        replace($a3$    marital_status  = case when ef ? 'marital_status'  then ef->>'marital_status'  else marital_status end$a3$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  k text;
  v_commentaire_au_clic boolean := false;  -- 8a-A 22/10 : interrupteur contact_commentaire_au_clic$n1$, chr(13), ''),
        replace($n2$  if edit_fields is null or edit_fields = '{}'::jsonb then raise exception 'no_fields' using errcode='22023'; end if;

  -- 8a-A (22/10/2026) : LE COMMENTAIRE S'ECRIT CHEZ NOUS AU CLIC. Avant, l'ecran l'envoyait
  -- (`comments`) mais seule la relecture de Hektor le posait, ~11 min apres. Interrupteur
  -- eteint : rien ne change. Allume : `comments` (ou `commentaires`) -> colonne commentaires,
  -- et sa valeur d'avant entre dans la photo (base_snapshot), comme les 12 autres.
  select lower(trim(coalesce(s.value, ''))) in ('on', '1', 'true', 'oui') into v_commentaire_au_clic
    from public.app_setting s where s.key = 'contact_commentaire_au_clic';
  v_commentaire_au_clic := coalesce(v_commentaire_au_clic, false);
  if v_commentaire_au_clic then
    alias_map := alias_map || '{"commentaires":"comments"}'::jsonb;
    col_map := col_map || '{"comments":"commentaires"}'::jsonb;
  end if;$n2$, chr(13), ''),
        replace($n3$    marital_status  = case when ef ? 'marital_status'  then ef->>'marital_status'  else marital_status end,
    commentaires    = case when v_commentaire_au_clic and ef ? 'comments' then ef->>'comments' else commentaires end$n3$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = 'eb93494b0856706f1f0426da7571d306' THEN
        RAISE NOTICE '%', 'Deja pose : app_edit_contact_optimistic porte deja l''empreinte eb93494b. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> '79d39e0e506d8afd3224fe20624598b3' THEN
        RAISE EXCEPTION '%', format('ARRET : app_edit_contact_optimistic a l''empreinte %s, attendu 79d39e0e (21/10). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : l''ancre %s est trouvee %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> 'eb93494b0856706f1f0426da7571d306' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte neuf a l''empreinte %s, attendu eb93494b (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_edit_contact_optimistic(text,jsonb,integer)'::regprocedure), chr(13), '')) <> 'eb93494b0856706f1f0426da7571d306' THEN
        RAISE EXCEPTION '%', 'ARRET : apres la pose, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose_rep$ $exec_pose$;

    -- T1 ETEINT : le commentaire ne doit PAS s'ecrire
    update public.app_setting set value = 'off' where key = 'contact_commentaire_au_clic';
    PERFORM public.app_edit_contact_optimistic(cid, jsonb_build_object('last_name', 'ESSAI 8A BIS T1', 'comments', 'COMMENTAIRE T1 ETEINT'), 0);
    select commentaires into v from public.app_contact_current where hektor_contact_id = cid;
    total := total + 1;
    IF v is not distinct from avant_com THEN ok := ok + 1; r := r || ' | T1 OK eteint : commentaire inchange';
    ELSE r := r || ' | T1 ECHEC eteint : commentaire = ' || coalesce(v, 'null'); END IF;
    select nom into v from public.app_contact_current where hektor_contact_id = cid;
    total := total + 1;
    IF v = 'ESSAI 8A BIS T1' THEN ok := ok + 1; r := r || ' | T3a OK nom ecrit (eteint)';
    ELSE r := r || ' | T3a ECHEC nom = ' || coalesce(v, 'null'); END IF;
    delete from public.app_contact_pending where hektor_contact_id = cid;

    -- T2 ALLUME : le commentaire s'ecrit, part dans l'attente, et sa valeur d'avant est dans la photo
    update public.app_setting set value = 'on' where key = 'contact_commentaire_au_clic';
    PERFORM public.app_edit_contact_optimistic(cid, jsonb_build_object('last_name', 'ESSAI 8A BIS T2', 'comments', 'COMMENTAIRE T2 ALLUME'), 0);
    select commentaires into v from public.app_contact_current where hektor_contact_id = cid;
    total := total + 1;
    IF v = 'COMMENTAIRE T2 ALLUME' THEN ok := ok + 1; r := r || ' | T2a OK allume : commentaire ecrit au clic';
    ELSE r := r || ' | T2a ECHEC allume : commentaire = ' || coalesce(v, 'null'); END IF;
    select base_snapshot, push_fields into snap, pf from public.app_contact_pending where hektor_contact_id = cid;
    total := total + 1;
    IF pf->>'comments' = 'COMMENTAIRE T2 ALLUME' THEN ok := ok + 1; r := r || ' | T2b OK le commentaire part chez Hektor (attente)';
    ELSE r := r || ' | T2b ECHEC attente = ' || coalesce(pf::text, 'null'); END IF;
    total := total + 1;
    IF snap ? 'comments' AND (snap->>'comments') is not distinct from avant_com AND snap ? '_date_maj' THEN ok := ok + 1; r := r || ' | T2c OK photo : valeur d''avant + _date_maj';
    ELSE r := r || ' | T2c ECHEC photo = ' || coalesce(snap::text, 'null'); END IF;
    select nom into v from public.app_contact_current where hektor_contact_id = cid;
    total := total + 1;
    IF v = 'ESSAI 8A BIS T2' THEN ok := ok + 1; r := r || ' | T3b OK nom ecrit (allume)';
    ELSE r := r || ' | T3b ECHEC nom = ' || coalesce(v, 'null'); END IF;
    delete from public.app_contact_pending where hektor_contact_id = cid;

    -- T4 l'alias « commentaires »
    PERFORM public.app_edit_contact_optimistic(cid, jsonb_build_object('last_name', 'ESSAI 8A BIS T4', 'commentaires', 'COMMENTAIRE T4 ALIAS'), 0);
    select commentaires into v from public.app_contact_current where hektor_contact_id = cid;
    total := total + 1;
    IF v = 'COMMENTAIRE T4 ALIAS' THEN ok := ok + 1; r := r || ' | T4 OK alias commentaires';
    ELSE r := r || ' | T4 ECHEC alias : commentaire = ' || coalesce(v, 'null'); END IF;
    delete from public.app_contact_pending where hektor_contact_id = cid;

    -- T5 L'INVERSE
    EXECUTE $exec_inv$ DO $retour$
DECLARE
    d text := replace(pg_get_functiondef('public.app_edit_contact_optimistic(text,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  k text;$a1$, chr(13), ''),
        replace($a2$  if edit_fields is null or edit_fields = '{}'::jsonb then raise exception 'no_fields' using errcode='22023'; end if;$a2$, chr(13), ''),
        replace($a3$    marital_status  = case when ef ? 'marital_status'  then ef->>'marital_status'  else marital_status end$a3$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  k text;
  v_commentaire_au_clic boolean := false;  -- 8a-A 22/10 : interrupteur contact_commentaire_au_clic$n1$, chr(13), ''),
        replace($n2$  if edit_fields is null or edit_fields = '{}'::jsonb then raise exception 'no_fields' using errcode='22023'; end if;

  -- 8a-A (22/10/2026) : LE COMMENTAIRE S'ECRIT CHEZ NOUS AU CLIC. Avant, l'ecran l'envoyait
  -- (`comments`) mais seule la relecture de Hektor le posait, ~11 min apres. Interrupteur
  -- eteint : rien ne change. Allume : `comments` (ou `commentaires`) -> colonne commentaires,
  -- et sa valeur d'avant entre dans la photo (base_snapshot), comme les 12 autres.
  select lower(trim(coalesce(s.value, ''))) in ('on', '1', 'true', 'oui') into v_commentaire_au_clic
    from public.app_setting s where s.key = 'contact_commentaire_au_clic';
  v_commentaire_au_clic := coalesce(v_commentaire_au_clic, false);
  if v_commentaire_au_clic then
    alias_map := alias_map || '{"commentaires":"comments"}'::jsonb;
    col_map := col_map || '{"comments":"commentaires"}'::jsonb;
  end if;$n2$, chr(13), ''),
        replace($n3$    marital_status  = case when ef ? 'marital_status'  then ef->>'marital_status'  else marital_status end,
    commentaires    = case when v_commentaire_au_clic and ef ? 'comments' then ef->>'comments' else commentaires end$n3$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '79d39e0e506d8afd3224fe20624598b3' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_edit_contact_optimistic porte deja l''empreinte du 21/10 (79d39e0e).';
        RETURN;
    END IF;
    IF md5(d) <> 'eb93494b0856706f1f0426da7571d306' THEN
        RAISE EXCEPTION '%', format('ARRET : app_edit_contact_optimistic a l''empreinte %s, ni eb93494b (posee) ni 79d39e0e (d''avant). Rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : le texte neuf %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '79d39e0e506d8afd3224fe20624598b3' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte rendu a l''empreinte %s, attendu 79d39e0e. Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
$retour$ $exec_inv$;
    total := total + 1;
    IF md5(replace(pg_get_functiondef('public.app_edit_contact_optimistic(text,jsonb,integer)'::regprocedure), chr(13), '')) = '79d39e0e506d8afd3224fe20624598b3' THEN ok := ok + 1; r := r || ' | T5 OK l''inverse rend 79d39e0e';
    ELSE r := r || ' | T5 ECHEC inverse'; END IF;

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
