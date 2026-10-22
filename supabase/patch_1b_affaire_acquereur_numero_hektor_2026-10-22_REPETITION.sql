-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE 1b — l'acquéreur sous son numéro Hektor                      22/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE (erreur volontaire « ESSAI ANNULE -- … ») : rien ne reste, ni la
--   fonction modifiée, ni l'interrupteur, ni les transactions, ni les travaux. (La séquence des
--   numéros avance de 6 : une séquence ne recule jamais.)
-- Le VRAI PATCH, puis la fonction appelée COMME L'ÉCRAN, au nom de Frédéric, sur l'annonce
-- d'essai 63331 (dossier 10000009) :
--   T1 ÉTEINT, identité 20000008      → 20000008 rangé tel quel (le témoin inverse du doublon)
--   T2 ÉTEINT, numéro Hektor 605717    → app_contact_id VIDE (le témoin inverse du lien perdu)
--   T3 ALLUMÉ, identité 20000008      → 605946, notre contact 20000008
--   T4 ALLUMÉ, identité 10650570      → 605717, notre contact 10650570
--   T5 ALLUMÉ, numéro Hektor 605717    → 605717, notre contact 10650570 RETROUVÉ
--   T6 ALLUMÉ, numéro inconnu 999999999 → rangé tel quel, aucun contact inventé
--   (chaque cas exige aussi une chaîne posée) · T7 l'inverse rend caab6b6c.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    dossier bigint := 10000009;
    aid bigint;
    l public.app_affaire_ledger%rowtype;
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    IF NOT EXISTS (select 1 from public.app_dossier_current where app_dossier_id = dossier) THEN
        RAISE EXCEPTION '%', 'ARRET : le dossier d''essai 10000009 n''est plus dans le parc vivant.';
    END IF;
    IF (select count(*) from public.app_contact_current where hektor_contact_id in ('20000008', '10650570')) <> 2 THEN
        RAISE EXCEPTION '%', 'ARRET : un contact de l''essai a disparu -- la repetition ne prouverait rien.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    insert into public.app_setting (key, value, description, updated_at)
    values ('affaire_acquereur_numero_hektor', 'off',
            'Chantier 8 / 1b 22/10/2026 : on = une transaction creee dans l''app range l''acquereur sous SON numero Hektor dans hektor_acquereur_id (cle du rapprochement de nuit), et retrouve notre contact meme si l''ecran a envoye le numero Hektor (voir supabase/patch_1b_affaire_acquereur_numero_hektor_2026-10-22.sql). off = comportement d''avant.',
            now())
    on conflict (key) do nothing;
    EXECUTE $exec_pose$ DO $pose_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  v_nait_complete boolean := false;$a1$, chr(13), ''),
        replace($a2$    select c.app_contact_id into v_acquereur_app$a2$, chr(13), ''),
        replace($a3$  -- ─── 2.6 : LA LISTE DES ACQUEREURS, ET LEURS NOMS ───$a3$, chr(13), ''),
        replace($a4$       public.app_chaine_pour(d.hektor_annonce_id::bigint, v_acquereur, v_kind, v_affaire_id),$a4$, chr(13), ''),
        replace($a5$       v_acquereur,$a5$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  v_nait_complete boolean := false;
  -- 1b 22/10/2026 : l'acquereur sous son numero Hektor (interrupteur affaire_acquereur_numero_hektor)
  v_acquereur_cible text;$n1$, chr(13), ''),
        replace($n2$    select c.app_contact_id, nullif(btrim(coalesce(c.hektor_target_id, '')), '') into v_acquereur_app, v_acquereur_cible$n2$, chr(13), ''),
        replace($n3$  -- ─── 1b (22/10/2026, chantier 8) : L'ACQUEREUR SOUS SON NUMERO HEKTOR ───
  -- `hektor_acquereur_id` est la CLE du rapprochement de nuit (affaire_ledger.py, par
  -- acquereur) et de la chaine (app_chaine_pour la compare aux lignes venues de Hektor).
  -- Or l'ecran envoie tantot NOTRE identite (la recherche de contacts : 20000008 le 22/10),
  -- tantot le numero Hektor (605717 le 13/10). Les 62 288 contacts ont deux numeros
  -- differents : l'identite y faisait echouer le rapprochement (doublon de nuit), le
  -- numero Hektor y faisait perdre le lien vers notre contact (app_contact_id vide).
  -- Allume : on reconnait les DEUX (identite d'abord, numero Hektor ensuite), on range le
  -- numero Hektor ici et notre identite dans app_contact_id. Inconnu : on garde ce qui est
  -- venu, on n'invente rien. Le worker n'est PAS concerne : il lit la charge et traduit
  -- lui-meme. Eteint : comportement d'avant.
  if coalesce((select s.value from public.app_setting s
                where s.key = 'affaire_acquereur_numero_hektor'), 'off') = 'on' then
    if v_acquereur is not null and v_acquereur_app is null then
      select c.app_contact_id, nullif(btrim(coalesce(c.hektor_target_id, '')), '')
        into v_acquereur_app, v_acquereur_cible
        from app_contact_current c
       where c.hektor_target_id = v_acquereur
       limit 1;
    end if;
    v_acquereur_cible := coalesce(v_acquereur_cible, v_acquereur);
  else
    v_acquereur_cible := v_acquereur;
  end if;

  -- ─── 2.6 : LA LISTE DES ACQUEREURS, ET LEURS NOMS ───$n3$, chr(13), ''),
        replace($n4$       public.app_chaine_pour(d.hektor_annonce_id::bigint, v_acquereur_cible, v_kind, v_affaire_id),$n4$, chr(13), ''),
        replace($n5$       v_acquereur_cible,         -- 1b : le numero Hektor (allume) ou ce qui est venu (eteint)$n5$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = 'f9d024471d0740fa21fffa532e9aa2ae' THEN
        RAISE NOTICE '%', 'Deja pose : app_change_annonce_status_optimistic porte deja l''empreinte f9d02447. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> 'caab6b6c38091ba5b087f8819147756f' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, attendu caab6b6c (R1, 22/10). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : l''ancre %s est trouvee %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> 'f9d024471d0740fa21fffa532e9aa2ae' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte neuf a l''empreinte %s, attendu f9d02447 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) <> 'f9d024471d0740fa21fffa532e9aa2ae' THEN
        RAISE EXCEPTION '%', 'ARRET : apres la pose, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose_rep$ $exec_pose$;

    update public.app_setting set value = 'off' where key = 'affaire_acquereur_numero_hektor';
    aid := (public.app_change_annonce_status_optimistic(dossier, 'compromise', jsonb_build_object('amount', '130000', 'sale_price', '130000', 'transaction_date', '2026-10-22', 'buyer_contact_id', '20000008', 'numero_mandat', '99999', 'titre_bien', 'ESSAI 1B'), 0)->>'app_affaire_id')::bigint;
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    total := total + 1;
    IF l.hektor_acquereur_id = '20000008' and l.app_contact_id = 20000008 and l.app_chaine_id is not null THEN ok := ok + 1; r := r || ' | T1 OK eteint, identite : rangee telle quelle';
    ELSE r := r || ' | T1 ECHEC eteint, identite : rangee telle quelle : ' || coalesce(l.hektor_acquereur_id || ' / ' || coalesce(l.app_contact_id::text, 'null') || ' / chaine ' || coalesce(l.app_chaine_id::text, 'null'), 'null'); END IF;
    aid := (public.app_change_annonce_status_optimistic(dossier, 'compromise', jsonb_build_object('amount', '130000', 'sale_price', '130000', 'transaction_date', '2026-10-22', 'buyer_contact_id', '605717', 'numero_mandat', '99999', 'titre_bien', 'ESSAI 1B'), 0)->>'app_affaire_id')::bigint;
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    total := total + 1;
    IF l.hektor_acquereur_id = '605717' and l.app_contact_id is null and l.app_chaine_id is not null THEN ok := ok + 1; r := r || ' | T2 OK eteint, numero Hektor : lien vers notre contact VIDE';
    ELSE r := r || ' | T2 ECHEC eteint, numero Hektor : lien vers notre contact VIDE : ' || coalesce(l.hektor_acquereur_id || ' / ' || coalesce(l.app_contact_id::text, 'null') || ' / chaine ' || coalesce(l.app_chaine_id::text, 'null'), 'null'); END IF;

    update public.app_setting set value = 'on' where key = 'affaire_acquereur_numero_hektor';
    aid := (public.app_change_annonce_status_optimistic(dossier, 'compromise', jsonb_build_object('amount', '130000', 'sale_price', '130000', 'transaction_date', '2026-10-22', 'buyer_contact_id', '20000008', 'numero_mandat', '99999', 'titre_bien', 'ESSAI 1B'), 0)->>'app_affaire_id')::bigint;
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    total := total + 1;
    IF l.hektor_acquereur_id = '605946' and l.app_contact_id = 20000008 and l.app_chaine_id is not null THEN ok := ok + 1; r := r || ' | T3 OK allume, identite 20000008 -> 605946';
    ELSE r := r || ' | T3 ECHEC allume, identite 20000008 -> 605946 : ' || coalesce(l.hektor_acquereur_id || ' / ' || coalesce(l.app_contact_id::text, 'null') || ' / chaine ' || coalesce(l.app_chaine_id::text, 'null'), 'null'); END IF;
    aid := (public.app_change_annonce_status_optimistic(dossier, 'compromise', jsonb_build_object('amount', '130000', 'sale_price', '130000', 'transaction_date', '2026-10-22', 'buyer_contact_id', '10650570', 'numero_mandat', '99999', 'titre_bien', 'ESSAI 1B'), 0)->>'app_affaire_id')::bigint;
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    total := total + 1;
    IF l.hektor_acquereur_id = '605717' and l.app_contact_id = 10650570 and l.app_chaine_id is not null THEN ok := ok + 1; r := r || ' | T4 OK allume, identite 10650570 -> 605717';
    ELSE r := r || ' | T4 ECHEC allume, identite 10650570 -> 605717 : ' || coalesce(l.hektor_acquereur_id || ' / ' || coalesce(l.app_contact_id::text, 'null') || ' / chaine ' || coalesce(l.app_chaine_id::text, 'null'), 'null'); END IF;
    aid := (public.app_change_annonce_status_optimistic(dossier, 'compromise', jsonb_build_object('amount', '130000', 'sale_price', '130000', 'transaction_date', '2026-10-22', 'buyer_contact_id', '605717', 'numero_mandat', '99999', 'titre_bien', 'ESSAI 1B'), 0)->>'app_affaire_id')::bigint;
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    total := total + 1;
    IF l.hektor_acquereur_id = '605717' and l.app_contact_id = 10650570 and l.app_chaine_id is not null THEN ok := ok + 1; r := r || ' | T5 OK allume, numero Hektor 605717 -> contact 10650570 retrouve';
    ELSE r := r || ' | T5 ECHEC allume, numero Hektor 605717 -> contact 10650570 retrouve : ' || coalesce(l.hektor_acquereur_id || ' / ' || coalesce(l.app_contact_id::text, 'null') || ' / chaine ' || coalesce(l.app_chaine_id::text, 'null'), 'null'); END IF;
    aid := (public.app_change_annonce_status_optimistic(dossier, 'compromise', jsonb_build_object('amount', '130000', 'sale_price', '130000', 'transaction_date', '2026-10-22', 'buyer_contact_id', '999999999', 'numero_mandat', '99999', 'titre_bien', 'ESSAI 1B'), 0)->>'app_affaire_id')::bigint;
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    total := total + 1;
    IF l.hektor_acquereur_id = '999999999' and l.app_contact_id is null and l.app_chaine_id is not null THEN ok := ok + 1; r := r || ' | T6 OK allume, inconnu -> range tel quel, rien d invente';
    ELSE r := r || ' | T6 ECHEC allume, inconnu -> range tel quel, rien d invente : ' || coalesce(l.hektor_acquereur_id || ' / ' || coalesce(l.app_contact_id::text, 'null') || ' / chaine ' || coalesce(l.app_chaine_id::text, 'null'), 'null'); END IF;

    -- T7 L'INVERSE
    EXECUTE $exec_inv$ DO $retour$
DECLARE
    d text := replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  v_nait_complete boolean := false;$a1$, chr(13), ''),
        replace($a2$    select c.app_contact_id into v_acquereur_app$a2$, chr(13), ''),
        replace($a3$  -- ─── 2.6 : LA LISTE DES ACQUEREURS, ET LEURS NOMS ───$a3$, chr(13), ''),
        replace($a4$       public.app_chaine_pour(d.hektor_annonce_id::bigint, v_acquereur, v_kind, v_affaire_id),$a4$, chr(13), ''),
        replace($a5$       v_acquereur,$a5$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  v_nait_complete boolean := false;
  -- 1b 22/10/2026 : l'acquereur sous son numero Hektor (interrupteur affaire_acquereur_numero_hektor)
  v_acquereur_cible text;$n1$, chr(13), ''),
        replace($n2$    select c.app_contact_id, nullif(btrim(coalesce(c.hektor_target_id, '')), '') into v_acquereur_app, v_acquereur_cible$n2$, chr(13), ''),
        replace($n3$  -- ─── 1b (22/10/2026, chantier 8) : L'ACQUEREUR SOUS SON NUMERO HEKTOR ───
  -- `hektor_acquereur_id` est la CLE du rapprochement de nuit (affaire_ledger.py, par
  -- acquereur) et de la chaine (app_chaine_pour la compare aux lignes venues de Hektor).
  -- Or l'ecran envoie tantot NOTRE identite (la recherche de contacts : 20000008 le 22/10),
  -- tantot le numero Hektor (605717 le 13/10). Les 62 288 contacts ont deux numeros
  -- differents : l'identite y faisait echouer le rapprochement (doublon de nuit), le
  -- numero Hektor y faisait perdre le lien vers notre contact (app_contact_id vide).
  -- Allume : on reconnait les DEUX (identite d'abord, numero Hektor ensuite), on range le
  -- numero Hektor ici et notre identite dans app_contact_id. Inconnu : on garde ce qui est
  -- venu, on n'invente rien. Le worker n'est PAS concerne : il lit la charge et traduit
  -- lui-meme. Eteint : comportement d'avant.
  if coalesce((select s.value from public.app_setting s
                where s.key = 'affaire_acquereur_numero_hektor'), 'off') = 'on' then
    if v_acquereur is not null and v_acquereur_app is null then
      select c.app_contact_id, nullif(btrim(coalesce(c.hektor_target_id, '')), '')
        into v_acquereur_app, v_acquereur_cible
        from app_contact_current c
       where c.hektor_target_id = v_acquereur
       limit 1;
    end if;
    v_acquereur_cible := coalesce(v_acquereur_cible, v_acquereur);
  else
    v_acquereur_cible := v_acquereur;
  end if;

  -- ─── 2.6 : LA LISTE DES ACQUEREURS, ET LEURS NOMS ───$n3$, chr(13), ''),
        replace($n4$       public.app_chaine_pour(d.hektor_annonce_id::bigint, v_acquereur_cible, v_kind, v_affaire_id),$n4$, chr(13), ''),
        replace($n5$       v_acquereur_cible,         -- 1b : le numero Hektor (allume) ou ce qui est venu (eteint)$n5$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = 'caab6b6c38091ba5b087f8819147756f' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_change_annonce_status_optimistic porte deja l''empreinte de R1 (caab6b6c).';
        RETURN;
    END IF;
    IF md5(d) <> 'f9d024471d0740fa21fffa532e9aa2ae' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, ni f9d02447 (posee) ni caab6b6c (R1). Rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : le texte neuf %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> 'caab6b6c38091ba5b087f8819147756f' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte rendu a l''empreinte %s, attendu caab6b6c. Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
$retour$ $exec_inv$;
    total := total + 1;
    IF md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) = 'caab6b6c38091ba5b087f8819147756f' THEN ok := ok + 1; r := r || ' | T7 OK l inverse rend caab6b6c';
    ELSE r := r || ' | T7 ECHEC l inverse rend caab6b6c : ' || coalesce('empreinte differente', 'null'); END IF;

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
