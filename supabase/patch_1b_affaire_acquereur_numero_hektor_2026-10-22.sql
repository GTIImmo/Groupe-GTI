-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · 1b — L'ACQUÉREUR SOUS SON NUMÉRO HEKTOR                         22/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md (section 6)
--
-- LE DÉFAUT (essai réel du 22/10, VA6482). La RPC range dans hektor_acquereur_id le numéro
-- envoyé par l'écran. Les 62 288 contacts ont DEUX numéros (notre identité ≥ 10 M, le leur) et
-- l'écran envoie tantôt l'un, tantôt l'autre :
--   identité (20000008)    -> la nuit ne rapproche pas la ligne du compromis de Hektor : DOUBLON
--   numéro Hektor (605717) -> le lien vers notre contact (app_contact_id) se perd (la nuit le refait)
--
-- CE QUE FAIT CE PATCH — CHIRURGICAL, CINQ ANCRES D'UNE LIGNE, ÉTEINT AU DÉPART :
--   allumé, la RPC reconnaît le contact par l'un OU l'autre numéro, range le numéro HEKTOR
--   dans hektor_acquereur_id et passe le même à app_chaine_pour ; notre identité reste dans
--   app_contact_id. Contact inconnu : rien n'est inventé. Éteint : comportement d'avant.
--   ⚠ LE WORKER N'EST PAS TOUCHÉ : il lit la charge (inchangée) et traduit lui-même.
--
-- ⛔ GARDE : empreinte caab6b6c exigée (posée par R1 le 22/10 à 18:19), chaque ancre trouvée
--    UNE fois, texte neuf f9d02447 CALCULÉ D'AVANCE. Sinon : ARRÊT, rien n'est écrit.
-- ⚠ ORDRE DES RETOURS ARRIÈRE : l'inverse de 1b AVANT celui de R1 (R1 exige caab6b6c).
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'affaire_acquereur_numero_hektor';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'affaire_acquereur_numero_hektor';
-- RETOUR ARRIÈRE COMPLET : supabase/patch_1b_affaire_acquereur_numero_hektor_2026-10-22_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('affaire_acquereur_numero_hektor', 'off',
        'Chantier 8 / 1b 22/10/2026 : on = une transaction creee dans l''app range l''acquereur sous SON numero Hektor dans hektor_acquereur_id (cle du rapprochement de nuit), et retrouve notre contact meme si l''ecran a envoye le numero Hektor (voir supabase/patch_1b_affaire_acquereur_numero_hektor_2026-10-22.sql). off = comportement d''avant.',
        now())
on conflict (key) do nothing;

-- 2. LA FONCTION, PAR SES CINQ ANCRES
DO $pose$
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
$pose$;

-- 3. LES CONTRÔLES — tous doivent dire OK
SELECT 1 AS "#", 'app_change_annonce_status_optimistic porte l''empreinte f9d02447' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) = 'f9d024471d0740fa21fffa532e9aa2ae' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur existe, ETEINT',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'affaire_acquereur_numero_hektor' AND value = 'off') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'les droits d''appel sont inchanges (authenticated peut appeler)',
       CASE WHEN has_function_privilege('authenticated', 'public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'l''interrupteur de R1 est toujours la',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'affaire_nait_complete') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
