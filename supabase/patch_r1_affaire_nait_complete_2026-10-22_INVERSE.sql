-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE R1 — la transaction naît complète                       22/10/2026
-- Il rend à app_change_annonce_status_optimistic son texte du 22/10 (empreinte 3eec3f85),
-- par les MÊMES ancres, et retire l'interrupteur. Il ne touche aucune donnée : les colonnes
-- déjà posées au clic restent (la nuit les remplace par la valeur de Hektor, comme avant).
-- Pour seulement SUSPENDRE, inutile de jouer ce fichier : éteindre l'interrupteur.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $retour$
DECLARE
    d text := replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  v_acq_json      jsonb;$a1$, chr(13), ''),
        replace($a2$    end loop;$a2$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  v_acq_json      jsonb;
  -- R1 22/10/2026 : interrupteur affaire_nait_complete
  v_nait_complete boolean := false;$n1$, chr(13), ''),
        replace($n2$    end loop;

    -- ─── R1 (22/10/2026, chantier 8) : LA TRANSACTION NAIT COMPLETE ───
    -- Avant, 4 champs sur 15 entraient au registre au clic (montant, date, acquereurs,
    -- mandat) ; les autres attendaient la nuit, ou ne vivaient qu'au carnet. Allume, chaque
    -- champ saisi entre dans SA colonne, et SEULEMENT pour le genre ou Hektor le porte
    -- (notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md, section 4 D) :
    --   offre      validite, honoraires acquereur, taux
    --   compromis  date d'acte, sequestre, fin de retractation (date + jours), net vendeur,
    --              honoraires vendeur et acquereur, taux, les deux notaires, les mandants
    --   vente      net vendeur, honoraires vendeur et acquereur, taux, les deux notaires,
    --              les mandants
    -- ⚠ Les notaires vont dans notaire_acquereur_* / notaire_mandant_*, PAS dans notaire_id
    --   (colonne inerte depuis le 15/09), et SANS notaires_origine = 'saisie', qui figerait la
    --   ligne pour toujours : la console doit pouvoir la confirmer ou la corriger.
    -- ⚠ Les mandants SEULEMENT s'ils sont affirmes (un tableau) : sinon Hektor les deduit du
    --   mandat (regle du 16/09, decision de Frederic du 22/10).
    -- ⚠ Le carnet ne change pas. Une erreur ici ne fait JAMAIS echouer le geste (WARNING).
    -- Interrupteur eteint : RIEN NE CHANGE.
    v_nait_complete := coalesce((select s.value from public.app_setting s
                                  where s.key = 'affaire_nait_complete'), 'off') = 'on';
    if v_nait_complete then
      begin
        update public.app_affaire_ledger l set
          jours_validite        = case when v_kind = 'offre'
                                       then nullif(btrim(coalesce(v_payload->>'validity_days', '')), '')
                                       else l.jours_validite end,
          date_acte             = case when v_kind = 'compromis'
                                       then nullif(btrim(coalesce(v_payload->>'signature_date', '')), '')
                                       else l.date_acte end,
          sequestre             = case when v_kind = 'compromis'
                                       then nullif(btrim(coalesce(v_payload->>'sequestration', '')), '')
                                       else l.sequestre end,
          date_fin_retractation = case when v_kind = 'compromis'
                                        and coalesce(v_payload->>'transaction_date', '') ~ '^\d{4}-\d{2}-\d{2}'
                                        and btrim(coalesce(v_payload->>'retraction_days', '')) ~ '^\d{1,3}$'
                                       then to_char(left(v_payload->>'transaction_date', 10)::date
                                                    + btrim(v_payload->>'retraction_days')::int, 'YYYY-MM-DD')
                                       else l.date_fin_retractation end,
          prix_net_vendeur      = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'net_seller_price', '')), '')
                                       else l.prix_net_vendeur end,
          honoraires_entree     = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'seller_fees', '')), '')
                                       else l.honoraires_entree end,
          honoraires_sortie     = nullif(btrim(coalesce(v_payload->>'buyer_fees', '')), ''),
          taux_honoraires       = nullif(btrim(coalesce(v_payload->>'buyer_fees_rate', '')), ''),
          notaire_acquereur_id  = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'buyer_notary_id', '')), '')
                                       else l.notaire_acquereur_id end,
          notaire_acquereur_nom = case when v_kind in ('compromis', 'vente')
                                        and nullif(btrim(coalesce(v_payload->>'buyer_notary_id', '')), '') is not null
                                       then nullif(btrim(coalesce(v_payload->>'buyer_notary_nom', '')), '')
                                       else l.notaire_acquereur_nom end,
          notaire_mandant_id    = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '')
                                       else l.notaire_mandant_id end,
          notaire_mandant_nom   = case when v_kind in ('compromis', 'vente')
                                        and nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '') is not null
                                       then nullif(btrim(coalesce(v_payload->>'seller_notary_nom', '')), '')
                                       else l.notaire_mandant_nom end,
          mandants_json         = case when v_kind in ('compromis', 'vente')
                                        and jsonb_typeof(v_payload->'mandant_contact_ids') = 'array'
                                        and jsonb_array_length(v_payload->'mandant_contact_ids') > 0
                                       then public.app_acquereurs_json(array(
                                              select nullif(btrim(e), '')
                                                from jsonb_array_elements_text(v_payload->'mandant_contact_ids') e
                                               where nullif(btrim(e), '') is not null))
                                       else l.mandants_json end
         where l.app_affaire_id = v_affaire_id;
      exception when others then
        raise warning 'R1 affaire_nait_complete : colonnes non posees pour l''affaire % (%)', v_affaire_id, sqlerrm;
      end;
    end if;$n2$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '3eec3f85ad9bcd5ed4b519e229936a23' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_change_annonce_status_optimistic porte deja l''empreinte du 22/10 (3eec3f85).';
        RETURN;
    END IF;
    IF md5(d) <> 'caab6b6c38091ba5b087f8819147756f' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, ni caab6b6c (posee) ni 3eec3f85 (d''avant). Rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : le texte neuf %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '3eec3f85ad9bcd5ed4b519e229936a23' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte rendu a l''empreinte %s, attendu 3eec3f85. Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
$retour$;

delete from public.app_setting where key = 'affaire_nait_complete';

SELECT 1 AS "#", 'app_change_annonce_status_optimistic a retrouve l''empreinte 3eec3f85' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) = '3eec3f85ad9bcd5ed4b519e229936a23' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'affaire_nait_complete') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
