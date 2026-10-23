-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · N — LE NOTAIRE DU VENDEUR D'UNE OFFRE EST GARDÉ CHEZ NOUS        23/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md (section 27). Décision de
-- Frédéric : « A » (le garder chez nous, et que le compromis le reprenne).
--
-- LE DÉFAUT. La modale propose « Notaire du vendeur » sur l'onglet Offre ; le worker l'envoie à Hektor,
-- qui ne le garde pas sur une offre (0 sur 11 190) ; R1 ne l'écrit qu'au compromis et à la vente ; le
-- carnet n'avait qu'un champ notaire, celui de l'acquéreur. La saisie se perdait.
--
-- CE QUE FAIT CE PATCH — TROIS ANCRES D'UNE LIGNE, ÉTEINT AU DÉPART :
--   1. un INTERRUPTEUR, app_setting 'offre_notaire_vendeur', posé à 'off' ;
--   2. app_change_annonce_status_optimistic (création) : deux lignes de plus dans la carte du carnet,
--      notaire_mandant_id / notaire_mandant_nom, POUR UNE OFFRE SEULEMENT ;
--   3. app_modifier_affaire_optimistic (modification) : les mêmes, seulement si le notaire du vendeur
--      est AFFIRMÉ (notaires_affirmes.mandant), et la clé 'seller_notary_id' dans la liste du point E.
--   Rien d'autre ne change : le travail pour Hektor, le registre, le compromis, la vente.
--   ⚠ Ces lignes de carnet n'ont PAS de colonne : elles restent au carnet (règle de sortie du 16/09).
--
-- ⛔ GARDE : empreintes f9d02447 (création) et 0dac8c86 (modification) exigées, chaque ancre
--    trouvée UNE fois, textes neufs 44697dd5 / 43247de7 CALCULÉS D'AVANCE. Sinon : ARRÊT.
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'offre_notaire_vendeur';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'offre_notaire_vendeur';
-- RETOUR ARRIÈRE COMPLET : supabase/patch_n_offre_notaire_vendeur_2026-10-23_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('offre_notaire_vendeur', 'off',
        'Chantier 8 / N 23/10/2026 : on = le notaire du VENDEUR saisi sur une OFFRE est garde au carnet (notaire_mandant_id / notaire_mandant_nom), a la creation et a la modification s''il est affirme (voir supabase/patch_n_offre_notaire_vendeur_2026-10-23.sql). Hektor ne le garde pas sur une offre. off = comportement d''avant (il se perd).',
        now())
on conflict (key) do nothing;

-- 2. LA CRÉATION
DO $pose_c$
DECLARE
    d text := replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($ca1$        ('notaire_id',         v_payload->>'buyer_notary_id'),$ca1$, chr(13), '')];
    neufs text[] := array[
        replace($cn1$        ('notaire_id',         v_payload->>'buyer_notary_id'),
        -- N (23/10/2026, chantier 8) : le notaire du VENDEUR d'une OFFRE. Hektor ne le garde pas sur une
        --   offre (0 sur 11 190) : le carnet le garde, et le compromis de la chaine le reprend.
        --   Interrupteur 'offre_notaire_vendeur'. Compromis et vente : inchanges (R1 les ecrit au registre).
        ('notaire_mandant_id',  case when v_kind = 'offre' and coalesce((select s.value from public.app_setting s where s.key = 'offre_notaire_vendeur'), 'off') = 'on'
                                 then v_payload->>'seller_notary_id' end),
        ('notaire_mandant_nom', case when v_kind = 'offre' and coalesce((select s.value from public.app_setting s where s.key = 'offre_notaire_vendeur'), 'off') = 'on'
                                  and nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '') is not null
                                 then v_payload->>'seller_notary_nom' end),$cn1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE NOTICE '%', 'Deja pose : app_change_annonce_status_optimistic porte deja l''empreinte 44697dd5. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> 'f9d024471d0740fa21fffa532e9aa2ae' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, attendu f9d02447 (mesuree le 23/10). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, l''ancre %s est trouvee %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, le texte neuf a l''empreinte %s, attendu 44697dd5 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) <> '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE EXCEPTION '%', 'ARRET : app_change_annonce_status_optimistic, apres la pose, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose_c$;

-- 3. LA MODIFICATION
DO $pose_m$
DECLARE
    d text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($ma1$      ('notaire_id',         v_payload->>'buyer_notary_id',                             null::text),$ma1$, chr(13), ''),
        replace($ma2$             when 'notaire_id'         then array['buyer_notary_id']$ma2$, chr(13), '')];
    neufs text[] := array[
        replace($mn1$      ('notaire_id',         v_payload->>'buyer_notary_id',                             null::text),
      -- N (23/10/2026) : le notaire du VENDEUR d'une OFFRE, s'il est AFFIRME (voir la creation).
      ('notaire_mandant_id',  case when a.kind = 'offre' and (v_payload->'notaires_affirmes'->>'mandant') = 'true' and coalesce((select s.value from public.app_setting s where s.key = 'offre_notaire_vendeur'), 'off') = 'on'
                               then v_payload->>'seller_notary_id' end,                null::text),
      ('notaire_mandant_nom', case when a.kind = 'offre' and (v_payload->'notaires_affirmes'->>'mandant') = 'true' and coalesce((select s.value from public.app_setting s where s.key = 'offre_notaire_vendeur'), 'off') = 'on'
                                and nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '') is not null
                               then v_payload->>'seller_notary_nom' end,               null::text),$mn1$, chr(13), ''),
        replace($mn2$             when 'notaire_id'         then array['buyer_notary_id']
             when 'notaire_mandant_id'  then array['seller_notary_id']
             when 'notaire_mandant_nom' then array['seller_notary_id']$mn2$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE NOTICE '%', 'Deja pose : app_modifier_affaire_optimistic porte deja l''empreinte 43247de7. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> '0dac8c866a73517032bf23a9bd307b71' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, attendu 0dac8c86 (mesuree le 23/10). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, l''ancre %s est trouvee %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, le texte neuf a l''empreinte %s, attendu 43247de7 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) <> '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE EXCEPTION '%', 'ARRET : app_modifier_affaire_optimistic, apres la pose, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose_m$;

-- 4. LES CONTRÔLES — tous doivent dire OK
SELECT 1 AS "#", 'app_change_annonce_status_optimistic porte l''empreinte 44697dd5' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) = '44697dd59587c644cdc021bd8f52108d' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'app_change_annonce_status_optimistic : droits d''appel inchanges, SECURITY DEFINER',
       CASE WHEN has_function_privilege('authenticated', 'public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)', 'EXECUTE') AND (SELECT prosecdef FROM pg_proc WHERE oid = 'public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure) THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3 AS "#", 'app_modifier_affaire_optimistic porte l''empreinte 43247de7' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) = '43247de7ff89e395d3b6e970353a891b' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 4, 'app_modifier_affaire_optimistic : droits d''appel inchanges, SECURITY DEFINER',
       CASE WHEN has_function_privilege('authenticated', 'public.app_modifier_affaire_optimistic(bigint,jsonb,integer)', 'EXECUTE') AND (SELECT prosecdef FROM pg_proc WHERE oid = 'public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure) THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'l''interrupteur existe, ETEINT',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'offre_notaire_vendeur' AND value = 'off') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
