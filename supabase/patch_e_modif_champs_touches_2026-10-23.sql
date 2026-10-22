-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · POINT E — LA MODIFICATION N'INSCRIT AU CARNET QUE CE QUI A ÉTÉ TAPÉ   23/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md (section 7)
--
-- LE DÉFAUT. app_modifier_affaire_optimistic met au carnet TOUT champ non vide de la charge.
-- Or la modale s'ouvre préremplie, et la charge part entière. Le carnet PRIME à l'écran et au
-- préremplissage suivant : du prérempli que personne n'a tapé y devenait « notre saisie ».
-- Mesure : offre 33094 (13/10), 6 lignes au carnet dont au moins 4 de prérempli.
--
-- CE QUE FAIT CE PATCH — SEPT ANCRES D'UNE LIGNE, ÉTEINT AU DÉPART :
--   allumé, et si l'écran envoie `champs_touches` (les clés qu'une saisie a changées), seules
--   ces clés entrent au carnet ET au registre (montant, date). Liste absente (écran d'avant) ou
--   éteint : comportement d'avant. ⚠ LA CHARGE DU TRAVAIL N'EST PAS TOUCHÉE : le worker reçoit
--   exactement ce qu'il recevait (il ignore `champs_touches`).
--
-- ⛔ GARDE : empreinte a5297281 exigée (mesurée le 23/10), chaque ancre trouvée UNE fois,
--    texte neuf 049643b8 CALCULÉ D'AVANCE. Sinon : ARRÊT, rien n'est écrit.
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'affaire_modif_champs_touches';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'affaire_modif_champs_touches';
-- RETOUR ARRIÈRE COMPLET : supabase/patch_e_modif_champs_touches_2026-10-23_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('affaire_modif_champs_touches', 'off',
        'Chantier 8 / point E 23/10/2026 : on = en MODIFICATION d''une transaction, seuls les champs que l''ecran declare TAPES (champs_touches) entrent au carnet et au registre ; le prerempli n''y entre plus (voir supabase/patch_e_modif_champs_touches_2026-10-23.sql). off, ou liste absente = comportement d''avant.',
        now())
on conflict (key) do nothing;

-- 2. LA FONCTION, PAR SES SEPT ANCRES
DO $pose$
DECLARE
    d text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  v_cible     text;$a1$, chr(13), ''),
        replace($a2$  v_payload := coalesce(job_payload, '{}'::jsonb);$a2$, chr(13), ''),
        replace($a3$     set montant = coalesce(nullif(btrim(coalesce(v_payload->>'amount',$a3$, chr(13), ''),
        replace($a4$                                                  v_payload->>'sale_price', '')), ''), montant),$a4$, chr(13), ''),
        replace($a5$         date    = coalesce(nullif(btrim(coalesce(v_payload->>'transaction_date', '')), ''), date)$a5$, chr(13), ''),
        replace($a6$    if v_valeur is not null then$a6$, chr(13), ''),
        replace($a7$                            'champs_au_carnet', v_au_carnet);$a7$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  v_cible     text;
  v_touches   jsonb;   -- point E 23/10/2026 (interrupteur affaire_modif_champs_touches)
  v_maj       jsonb;$n1$, chr(13), ''),
        replace($n2$  v_payload := coalesce(job_payload, '{}'::jsonb);

  -- ─── POINT E (23/10/2026, chantier 8) : CE QUI A ETE TAPE, PAS CE QUI ETAIT AFFICHE ───
  -- La modale s'ouvre PREREMPLIE et la charge part ENTIERE (le worker de l'offre reconstruit
  -- le formulaire de Hektor avec elle : on ne l'allege pas). Mais tout champ non vide entrait
  -- au carnet -- et le carnet PRIME a l'ecran. Mesure : offre 33094 (13/10), 6 lignes dont au
  -- moins 4 de prerempli (prix de l'annonce 180 000, 10 jours de retractation sur une offre).
  -- L'ecran envoie desormais `champs_touches` : les cles qu'une SAISIE a changees.
  -- Allume ET liste presente : seules ces cles vont au carnet et au registre (montant, date).
  -- Liste absente (ecran d'avant, en cache) ou eteint : comportement d'avant.
  -- ⚠ Le montant se juge sur la PAIRE amount / sale_price : l'une touchee, on garde les deux
  --   comme avant (coalesce(amount, sale_price)) -- sinon un prix de vente touche seul
  --   deviendrait le montant d'un compromis.
  if coalesce((select s.value from public.app_setting s
                where s.key = 'affaire_modif_champs_touches'), 'off') = 'on'
     and jsonb_typeof(v_payload->'champs_touches') = 'array' then
    v_touches := v_payload->'champs_touches';
  end if;
  v_maj := v_payload;
  if v_touches is not null then
    if not (v_touches ?| array['amount', 'sale_price']) then
      v_maj := v_maj - array['amount', 'sale_price'];
    end if;
    if not (v_touches ? 'transaction_date') then
      v_maj := v_maj - 'transaction_date';
    end if;
  end if;$n2$, chr(13), ''),
        replace($n3$     set montant = coalesce(nullif(btrim(coalesce(v_maj->>'amount',$n3$, chr(13), ''),
        replace($n4$                                                  v_maj->>'sale_price', '')), ''), montant),$n4$, chr(13), ''),
        replace($n5$         date    = coalesce(nullif(btrim(coalesce(v_maj->>'transaction_date', '')), ''), date)$n5$, chr(13), ''),
        replace($n6$    if v_valeur is not null
       -- point E : allume avec une liste, seul ce qui a ete TAPE entre au carnet
       and (v_touches is null or v_touches ?| (case v_champ.champ
             when 'montant'            then array['amount', 'sale_price']
             when 'date'               then array['transaction_date']
             when 'date_acte'          then array['signature_date']
             when 'sequestre'          then array['sequestration']
             when 'prix_net_vendeur'   then array['net_seller_price']
             when 'prix_publique'      then array['sale_price']
             when 'honoraires'         then array['buyer_fees']
             when 'honoraires_entree'  then array['seller_fees']
             when 'numero_mandat'      then array['selected_mandat']
             when 'jours_validite'     then array['validity_days']
             when 'jours_retractation' then array['retraction_days']
             when 'notaire_id'         then array['buyer_notary_id']
             when 'taux_honoraires'    then array['buyer_fees_rate']
             else array['--champ-inconnu--'] end)) then$n6$, chr(13), ''),
        replace($n7$                            'champs_au_carnet', v_au_carnet,
                            'champs_touches',   v_touches);$n7$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '049643b8a2042904544586f400eb8fe3' THEN
        RAISE NOTICE '%', 'Deja pose : app_modifier_affaire_optimistic porte deja l''empreinte 049643b8. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> 'a5297281686c699b89ac2fbc61864fe4' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, attendu a5297281 (mesuree le 23/10). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : l''ancre %s est trouvee %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '049643b8a2042904544586f400eb8fe3' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte neuf a l''empreinte %s, attendu 049643b8 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) <> '049643b8a2042904544586f400eb8fe3' THEN
        RAISE EXCEPTION '%', 'ARRET : apres la pose, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose$;

-- 3. LES CONTRÔLES — tous doivent dire OK
SELECT 1 AS "#", 'app_modifier_affaire_optimistic porte l''empreinte 049643b8' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) = '049643b8a2042904544586f400eb8fe3' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur existe, ETEINT',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'affaire_modif_champs_touches' AND value = 'off') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'les droits d''appel sont inchanges (authenticated peut appeler)',
       CASE WHEN has_function_privilege('authenticated', 'public.app_modifier_affaire_optimistic(bigint,jsonb,integer)', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'la fonction reste SECURITY DEFINER',
       CASE WHEN (SELECT prosecdef FROM pg_proc WHERE oid = 'public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure) THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
