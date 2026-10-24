-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — pas de transaction sur un bien en estimation   24/10/2026
-- Il rend à app_change_annonce_status_optimistic son texte d'avant (44697dd5), par la MÊME ancre, et retire l'interrupteur.
-- Il ne touche aucune donnée. Pour seulement SUSPENDRE : éteindre l'interrupteur.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $retour$
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
    IF md5(d) = '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_change_annonce_status_optimistic porte deja l''empreinte d''avant (44697dd5).'; RETURN;
    END IF;
    IF md5(d) <> '93be71b41e9ff172de9e8c3e261233a5' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, attendu 93be71b4. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, le texte rendu a l''empreinte %s, attendu 44697dd5 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) <> '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE EXCEPTION '%', 'ARRET : app_change_annonce_status_optimistic, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$retour$;

delete from public.app_setting where key = 'transaction_refusee_sur_estimation';

SELECT 1 AS "#", 'app_change_annonce_status_optimistic a retrouve 44697dd5' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) = '44697dd59587c644cdc021bd8f52108d' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'transaction_refusee_sur_estimation') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
