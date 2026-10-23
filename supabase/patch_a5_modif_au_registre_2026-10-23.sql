-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · A5 — LA MODIFICATION D'UNE TRANSACTION ÉCRIT AU REGISTRE CE QU'ELLE ENVOIE   23/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md (section 20)
--
-- LE DÉFAUT. app_modifier_affaire_optimistic n'écrit au registre que le montant et la date. Une
-- validité, une date d'acte, un séquestre, des honoraires, un taux, une rétractation, des notaires
-- ou des mandants modifiés n'existaient que dans le carnet jusqu'au retour de Hektor (ou la nuit).
-- R1 (22/10) l'avait promis « création + modification » ; seule la création l'était.
--
-- CE QUE FAIT CE PATCH — UNE ANCRE D'UNE LIGNE, ÉTEINT AU DÉPART :
--   allumé ET avec la liste `champs_touches` du point E : chaque colonne n'est écrite que si sa
--   clé a été TAPÉE ; les notaires seulement s'ils sont AFFIRMÉS, les mandants seulement s'ils
--   sont DÉSIGNÉS. « Vide ne gagne pas ». Éteint, ou liste absente : rien ne change.
--   ⚠ PAS le net vendeur d'une VENTE, PAS le numéro de mandat : Hektor ne les relit pas au retour,
--     et l'ancien verdict comparerait la saisie à elle-même.
--   ⚠ LA CHARGE DU TRAVAIL ET LE CARNET NE SONT PAS TOUCHÉS (la photo reste la valeur d'avant).
--
-- ⛔ GARDE : empreinte 049643b8 exigée (après E2, mesurée le 23/10), l'ancre trouvée UNE fois,
--    texte neuf 0dac8c86 CALCULÉ D'AVANCE. Sinon : ARRÊT, rien n'est écrit.
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'affaire_modif_au_registre';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'affaire_modif_au_registre';
-- RETOUR ARRIÈRE COMPLET : supabase/patch_a5_modif_au_registre_2026-10-23_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('affaire_modif_au_registre', 'off',
        'Chantier 8 / A5 23/10/2026 : on = en MODIFICATION d''une transaction, ce qui a ete TAPE (liste champs_touches du point E) est ecrit AUSSI au registre, colonne par colonne, au clic (voir supabase/patch_a5_modif_au_registre_2026-10-23.sql). off, ou liste absente = comportement d''avant (montant et date seulement).',
        now())
on conflict (key) do nothing;

-- 2. LA FONCTION, PAR SON ANCRE
DO $pose$
DECLARE
    d text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  -- ─── LE CARNET, QUE LE RUN NE TOUCHE JAMAIS ───$a1$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  -- ─── A5 (23/10/2026, chantier 8) : LA MODIFICATION ECRIT AU REGISTRE CE QU'ELLE ENVOIE ───
  -- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md, section 20.
  -- R1 (22/10) l'avait promis « creation + modification » : la modification n'ecrivait que le
  -- montant et la date. Interrupteur 'affaire_modif_au_registre', ET la liste du point E : seul
  -- ce qui a ete TAPE ; les notaires s'ils sont AFFIRMES, les mandants s'ils sont DESIGNES --
  -- exactement ce que le worker envoie comme intention. « Vide ne gagne pas ».
  -- ⚠ ON N'ECRIT QUE CE QUE HEKTOR RELIT au retour, ou ce qu'aucun verdict ne juge sur le
  --   registre : sinon l'ancien verdict (marquerLeCarnetRestant) comparerait la saisie A ELLE-MEME.
  --   D'ou : PAS le net vendeur d'une VENTE (Hektor n'en a pas), PAS le numero de mandat (relu
  --   la nuit seulement).
  -- ⚠ La photo du carnet, plus bas, se prend dans `a`, lu AVANT : elle reste la valeur d'avant.
  -- ⚠ Une erreur ici ne fait JAMAIS echouer le geste (WARNING), comme R1.
  if v_touches is not null
     and coalesce((select s.value from public.app_setting s
                    where s.key = 'affaire_modif_au_registre'), 'off') = 'on' then
    begin
      update public.app_affaire_ledger l set
        jours_validite = case when a.kind in ('offre') and v_touches ? 'validity_days'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'validity_days', '')), ''), l.jours_validite)
                                     else l.jours_validite end,
        date_acte = case when a.kind in ('compromis') and v_touches ? 'signature_date'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'signature_date', '')), ''), l.date_acte)
                                     else l.date_acte end,
        sequestre = case when a.kind in ('compromis') and v_touches ? 'sequestration'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'sequestration', '')), ''), l.sequestre)
                                     else l.sequestre end,
        prix_net_vendeur = case when a.kind in ('compromis') and v_touches ? 'net_seller_price'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'net_seller_price', '')), ''), l.prix_net_vendeur)
                                     else l.prix_net_vendeur end,
        honoraires_entree = case when a.kind in ('compromis', 'vente') and v_touches ? 'seller_fees'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'seller_fees', '')), ''), l.honoraires_entree)
                                     else l.honoraires_entree end,
        honoraires_sortie = case when v_touches ? 'buyer_fees'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'buyer_fees', '')), ''), l.honoraires_sortie)
                                     else l.honoraires_sortie end,
        taux_honoraires = case when v_touches ? 'buyer_fees_rate'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'buyer_fees_rate', '')), ''), l.taux_honoraires)
                                     else l.taux_honoraires end,
        date_fin_retractation = case when a.kind = 'compromis' and v_touches ? 'retraction_days'
                                      and btrim(coalesce(v_payload->>'retraction_days', '')) ~ '^\d{1,3}$'
                                      and coalesce(l.date, '') ~ '^\d{4}-\d{2}-\d{2}'
                                     then to_char(left(l.date, 10)::date
                                                  + btrim(v_payload->>'retraction_days')::int, 'YYYY-MM-DD')
                                     else l.date_fin_retractation end,
        notaire_acquereur_id = case when a.kind in ('compromis', 'vente') and (v_payload->'notaires_affirmes'->>'acquereur') = 'true'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'buyer_notary_id', '')), ''), l.notaire_acquereur_id)
                                     else l.notaire_acquereur_id end,
        notaire_acquereur_nom = case when a.kind in ('compromis', 'vente') and (v_payload->'notaires_affirmes'->>'acquereur') = 'true'
                                      and nullif(btrim(coalesce(v_payload->>'buyer_notary_id', '')), '') is not null
                                     then nullif(btrim(coalesce(v_payload->>'buyer_notary_nom', '')), '')
                                     else l.notaire_acquereur_nom end,
        notaire_mandant_id = case when a.kind in ('compromis', 'vente') and (v_payload->'notaires_affirmes'->>'mandant') = 'true'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), ''), l.notaire_mandant_id)
                                     else l.notaire_mandant_id end,
        notaire_mandant_nom = case when a.kind in ('compromis', 'vente') and (v_payload->'notaires_affirmes'->>'mandant') = 'true'
                                      and nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '') is not null
                                     then nullif(btrim(coalesce(v_payload->>'seller_notary_nom', '')), '')
                                     else l.notaire_mandant_nom end,
        mandants_json = case when a.kind in ('compromis', 'vente')
                              and jsonb_typeof(v_payload->'mandant_contact_ids') = 'array'
                              and jsonb_array_length(v_payload->'mandant_contact_ids') > 0
                             then public.app_acquereurs_json(array(
                                    select nullif(btrim(e), '')
                                      from jsonb_array_elements_text(v_payload->'mandant_contact_ids') e
                                     where nullif(btrim(e), '') is not null))
                             else l.mandants_json end
       where l.app_affaire_id = a.app_affaire_id;
    exception when others then
      raise warning 'A5 affaire_modif_au_registre : colonnes non posees pour l''affaire % (%)', a.app_affaire_id, sqlerrm;
    end;
  end if;

  -- ─── LE CARNET, QUE LE RUN NE TOUCHE JAMAIS ───$n1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '0dac8c866a73517032bf23a9bd307b71' THEN
        RAISE NOTICE '%', 'Deja pose : app_modifier_affaire_optimistic porte deja l''empreinte 0dac8c86. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> '049643b8a2042904544586f400eb8fe3' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, attendu 049643b8 (mesuree le 23/10, apres E2). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : l''ancre %s est trouvee %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '0dac8c866a73517032bf23a9bd307b71' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte neuf a l''empreinte %s, attendu 0dac8c86 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) <> '0dac8c866a73517032bf23a9bd307b71' THEN
        RAISE EXCEPTION '%', 'ARRET : apres la pose, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose$;

-- 3. LES CONTRÔLES — tous doivent dire OK
SELECT 1 AS "#", 'app_modifier_affaire_optimistic porte l''empreinte 0dac8c86' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) = '0dac8c866a73517032bf23a9bd307b71' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur existe, ETEINT',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'affaire_modif_au_registre' AND value = 'off') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'les droits d''appel sont inchanges (authenticated peut appeler)',
       CASE WHEN has_function_privilege('authenticated', 'public.app_modifier_affaire_optimistic(bigint,jsonb,integer)', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'la fonction reste SECURITY DEFINER',
       CASE WHEN (SELECT prosecdef FROM pg_proc WHERE oid = 'public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure) THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'le point E est toujours allume (A5 en depend)',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'affaire_modif_champs_touches' AND value = 'on') THEN 'OK' ELSE '⚠ E ETEINT : A5 ne fera rien' END
ORDER BY 1;

COMMIT;
