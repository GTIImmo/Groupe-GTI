-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE N — le notaire du vendeur d'une offre gardé chez nous   23/10/2026
-- Il rend aux deux fonctions leur texte d'avant (f9d02447 / 0dac8c86), par les MÊMES ancres, et
-- retire l'interrupteur. Il ne touche aucune donnée : les lignes de carnet déjà écrites restent.
-- Pour seulement SUSPENDRE, inutile de jouer ce fichier : éteindre l'interrupteur.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $retour_c$
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
    IF md5(d) = 'f9d024471d0740fa21fffa532e9aa2ae' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_change_annonce_status_optimistic porte deja l''empreinte d''avant (f9d02447).';
        RETURN;
    END IF;
    IF md5(d) <> '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, ni 44697dd5 (posee) ni f9d02447 (avant). Rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, le texte neuf %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> 'f9d024471d0740fa21fffa532e9aa2ae' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, le texte rendu a l''empreinte %s, attendu f9d02447. Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
$retour_c$;

DO $retour_m$
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
    IF md5(d) = '0dac8c866a73517032bf23a9bd307b71' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_modifier_affaire_optimistic porte deja l''empreinte d''avant (0dac8c86).';
        RETURN;
    END IF;
    IF md5(d) <> '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, ni 43247de7 (posee) ni 0dac8c86 (avant). Rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, le texte neuf %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '0dac8c866a73517032bf23a9bd307b71' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, le texte rendu a l''empreinte %s, attendu 0dac8c86. Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
$retour_m$;

delete from public.app_setting where key = 'offre_notaire_vendeur';

SELECT 1 AS "#", 'app_change_annonce_status_optimistic a retrouve f9d02447' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) = 'f9d024471d0740fa21fffa532e9aa2ae' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'app_modifier_affaire_optimistic a retrouve 0dac8c86',
       CASE WHEN md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) = '0dac8c866a73517032bf23a9bd307b71' THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'offre_notaire_vendeur') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
