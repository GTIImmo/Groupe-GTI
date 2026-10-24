-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ — PAS DE TRANSACTION SUR UN BIEN EN ESTIMATION                       24/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md (sections 45 et 46). Règle de
-- Frédéric (24/10) : « pas de transaction pour les biens en état Vendu, Clos ou Estimation ; si l'état revient
-- à Actif, possibilité de refaire une nouvelle chaîne ».
--
-- LE CONSTAT (mesure du 24/10). La création refuse déjà Vendu et Clos (hors parc vivant,
-- `transaction_hors_parc_vivant`) et l'archive. Mais l'ESTIMATION est DANS le parc vivant (12 781 biens) :
-- une offre, un compromis ou une vente y passaient, sans rien pour les arrêter. L'écran les cache depuis le
-- 24/10 ; ce patch est la SERRURE (« l'écran prévient, la base refuse »).
--
-- CE QUE FAIT CE PATCH — UNE ANCRE D'UNE LIGNE, ÉTEINT AU DÉPART :
--   1. un INTERRUPTEUR, app_setting 'transaction_refusee_sur_estimation', posé à 'off' ;
--   2. app_change_annonce_status_optimistic : créer une offre, un compromis ou une vente sur un bien en Estimation est REFUSÉ
--      (`transaction_sur_estimation`, traduit à l'écran). « Actif » et « Clos » passent toujours.
--   Rien d'autre ne change : Actif / Sous offre / Sous compromis, la MODIFICATION (autre fonction), les gestes.
--
-- ⛔ GARDE : empreinte 44697dd5 exigée, ancre trouvée UNE fois, texte neuf 93be71b4 CALCULÉ D'AVANCE.
--    Sinon : ARRÊT, rien n'est écrit.
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'transaction_refusee_sur_estimation';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'transaction_refusee_sur_estimation';
-- RETOUR ARRIÈRE COMPLET : supabase/patch_transaction_sur_estimation_2026-10-24_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('transaction_refusee_sur_estimation', 'off',
        'Chantier 8 / 24/10/2026 : on = la creation d''une OFFRE, d''un COMPROMIS ou d''une VENTE est refusee sur un bien en ESTIMATION (« pas de transaction pour les biens Vendu, Clos ou Estimation » -- regle de Frederic ; Vendu et Clos sont deja refuses hors parc vivant). Voir supabase/patch_transaction_sur_estimation_2026-10-24.sql. off = comportement d''avant.',
        now())
on conflict (key) do nothing;

-- 2. LA CRÉATION
DO $pose$
DECLARE
    d text := replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  -- @repli-fin$a1$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  -- @repli-fin

  -- ⛔ ─── ⑧ (24/10/2026) : PAS DE TRANSACTION SUR UN BIEN EN ESTIMATION ─── ⛔
  -- La regle de Frederic : « pas de transaction pour les biens en etat Vendu, Clos ou Estimation ; si
  -- l'etat revient a Actif, possibilite de refaire une nouvelle chaine ». Vendu et Clos sont refuses
  -- juste au-dessus (hors parc vivant) ; l'Estimation, elle, est DANS le parc vivant (12 781 biens le
  -- 24/10) et passait. On ne regarde que l'ETAT du bien, jamais ses anciennes transactions.
  -- « Actif » et « Clos » (le chemin pour sortir de l'estimation) ne sont pas touches.
  -- Interrupteur 'transaction_refusee_sur_estimation'.
  if target_status in ('offer', 'compromise', 'sold')
     and lower(btrim(coalesce(d.statut_annonce, ''))) like '%estimation%'
     and coalesce((select s.value from public.app_setting s where s.key = 'transaction_refusee_sur_estimation'), 'off') = 'on' then
    raise exception 'transaction_sur_estimation: ce bien est en Estimation. Une offre, un compromis ou une vente se font sur un bien Actif : passez-le d''abord en Actif.' using errcode = '22023';
  end if;$n1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '93be71b41e9ff172de9e8c3e261233a5' THEN
        RAISE NOTICE '%', 'Deja pose : app_change_annonce_status_optimistic porte deja l''empreinte 93be71b4. Rien n''est ecrit.'; RETURN;
    END IF;
    IF md5(d) <> '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, attendu 44697dd5. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '93be71b41e9ff172de9e8c3e261233a5' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, le texte rendu a l''empreinte %s, attendu 93be71b4 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) <> '93be71b41e9ff172de9e8c3e261233a5' THEN
        RAISE EXCEPTION '%', 'ARRET : app_change_annonce_status_optimistic, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose$;

-- 3. LES CONTRÔLES — tous doivent dire OK
SELECT 1 AS "#", 'app_change_annonce_status_optimistic porte l''empreinte 93be71b4' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) = '93be71b41e9ff172de9e8c3e261233a5' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'app_change_annonce_status_optimistic : droits d''appel inchanges, SECURITY DEFINER',
       CASE WHEN has_function_privilege('authenticated', 'public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)', 'EXECUTE') AND (SELECT prosecdef FROM pg_proc WHERE oid = 'public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure) THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'l''interrupteur existe, ETEINT',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'transaction_refusee_sur_estimation' AND value = 'off') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
