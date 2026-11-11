-- ═══════════════════════════════════════════════════════════════════════════
-- LA CASCADE DE L'ANNULATION : un compromis annule entraine son offre  11/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Decision de Frederic (10/11) : « si une transaction s'annule dans une chaine,
-- les autres maillons doivent aussi changer d'etat ». Puis (11/11), sur les trois
-- questions posees : ① chez Hektor ET chez nous · ② la colonne d'annulation plus
-- tard · ③ oui pour la regle, ecrite pour que la VENTE s'y branche ensuite.
--
-- ⭐ POURQUOI LA REGLE N'A BESOIN D'AUCUN JUGE. Pour les 523 offres du rattrapage,
--   il fallait le classeur ou le fichier Netty pour dire « cette affaire est morte ».
--   Ici le dossier se contredit TOUT SEUL : son compromis est annule, donc l'affaire
--   a echoue, donc l'offre ne peut pas etre restee « acceptee ». C'est de la
--   coherence interne, pas un arbitrage.
--
-- L'AMPLEUR DU TROU, mesuree le 10/11 : 661 dossiers portent un compromis annule
-- et une offre encore « acceptee ». Et la cause n'est pas une panne -- chez Hektor,
-- annuler un compromis NE TOUCHE PAS a l'offre, depuis 2006. Nous recopions Hektor,
-- donc nous recopions l'incoherence.
-- ⭐ LA POPULATION EST SANS CAS LIMITE : les 661 ont UNE SEULE offre acceptee,
--   0 offre « proposee », et 0 recouvrement avec les 523 du rattrapage.
--
-- ⛔⛔ CE QUE LA REGLE NE TOUCHE PAS, ET C'EST MESURE :
--   . les 8 658 dossiers « vente + offre acceptee » -- une offre qui ABOUTIT reste
--     acceptee, c'est l'histoire vraie. La cascade ne vise que ce qui est MORT.
--   . le statut de l'annonce -- il ne bouge pas (seule la creation le deplace).
--   . la date et le motif d'annulation -- decision de Frederic : plus tard, avec
--     les 896 dates du classeur, qui fait foi dessus.
--
-- ⭐ ET LA VENTE S'Y BRANCHERA SANS RIEN REECRIRE. Mesure du 11/11 : sur
--   9 280 ventes, AUCUNE n'a d'etat -- la table de Hektor n'en a pas. Une vente ne
--   s'annule pas chez eux, elle DISPARAIT. Le jour ou `date_annulation_app` portera
--   des valeurs, une vente annulee CHEZ NOUS pourra declencher la meme cascade, un
--   cran plus haut : vente -> compromis -> offre. Le bloc ci-dessous est ecrit pour
--   recevoir ce cas sans etre refait.
--
-- ⚠ LE RISQUE, NOMME PLUTOT QUE TU. Deux travaux partent au lieu d'un. Si Hektor
--   acceptait le refus de l'offre ET refusait l'annulation du compromis, le worker
--   restaurerait le compromis sans restaurer l'offre : les deux divergeraient.
--   MESURE : sur 14 annulations de compromis et 57 refus d'offres, Hektor n'a JAMAIS
--   refuse -- 0 erreur sur 71 gestes. Et la reparation serait d'un clic (reaccepter).
--   C'est pourquoi la regle vit derriere un INTERRUPTEUR, eteint a la pose.
--
-- Interrupteur : app_setting 'cascade_annulation_compromis' = 'on'
-- Retour arriere : patch_cascade_annulation_2026-11-11_INVERSE.sql
-- Controle       : patch_cascade_annulation_2026-11-11_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

do $$
declare
  texte   text;
  ancre   text;
  bloc    text;
begin
  select pg_get_functiondef(p.oid) into texte
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.proname = 'app_geste_affaire_optimistic';
  if texte is null then
    raise exception 'app_geste_affaire_optimistic introuvable';
  end if;

  -- ⚠ LECON 30 : on retire les retours chariot AVANT de chercher, sinon une ancre
  --   ecrite ici ne retrouve jamais celle du corps stocke. Et l'ancre tient sur UNE
  --   SEULE LIGNE, pour la meme raison.
  texte := replace(texte, chr(13), '');
  ancre := '  PERFORM public.app_recalculer_type_du_bien(a.hektor_annonce_id::text, a.app_dossier_id);';

  if position(ancre in texte) = 0 then
    raise exception 'ancre introuvable : la fonction a change, NE PAS FORCER';
  end if;
  if position('cascade_annulation_compromis' in texte) > 0 then
    raise notice 'ⓘ la cascade est DEJA posee -- rien a faire.';
    return;
  end if;

  bloc := '
  -- ⭐⭐ LA CASCADE DE L''ANNULATION (11/11/2026) ─────────────────────────────
  -- Un compromis annule entraine l''offre de SON dossier. Chez Hektor ET chez
  -- nous, comme pour le geste humain : meme etat pose tout de suite, meme travail
  -- porteur de `etat_avant`, meme restauration si Hektor refuse.
  -- ⛔ ELLE NE VISE QUE CE QUI EST MORT : le dossier ne doit porter NI vente NI
  --   compromis encore vivant. Les 8 658 dossiers « vente + offre acceptee » sont
  --   NORMAUX et ne doivent jamais etre touches.
  -- ⚠ `sans_resynchro` : l''offre suit le compromis, qui pose deja la relecture du
  --   bien. En poser une seconde pour la meme annonce ne sert a rien.
  IF geste = ''annuler'' AND a.kind = ''compromis'' AND a.app_chaine_id IS NOT NULL
     AND coalesce((select s.value from public.app_setting s
                    where s.key = ''cascade_annulation_compromis''), ''off'') = ''on'' THEN
    FOR cascade_offre IN
      SELECT l.* FROM app_affaire_ledger l
       WHERE l.app_chaine_id = a.app_chaine_id
         AND l.app_affaire_id <> a.app_affaire_id
         AND l.kind = ''offre''
         AND lower(coalesce(l.state, '''')) IN (''accepted'', ''acceptee'')
         AND btrim(coalesce(l.hektor_affaire_id::text, '''')) <> ''''
         AND NOT (btrim(coalesce(l.hektor_affaire_id::text, '''')) <> ''''
                  AND l.present_in_hektor IS FALSE)
         AND NOT EXISTS (
               SELECT 1 FROM app_affaire_ledger v
                WHERE v.app_chaine_id = a.app_chaine_id
                  AND v.app_affaire_id <> a.app_affaire_id
                  AND NOT (btrim(coalesce(v.hektor_affaire_id::text, '''')) <> ''''
                           AND v.present_in_hektor IS FALSE)
                  AND ( v.kind = ''vente''
                     OR (v.kind = ''compromis''
                         AND lower(coalesce(v.state, '''')) NOT IN (''cancelled'', ''annule'')) ))
    LOOP
      UPDATE app_affaire_ledger SET state = ''refused''
       WHERE app_affaire_id = cascade_offre.app_affaire_id;

      INSERT INTO app_console_job (job_type, app_dossier_id, hektor_annonce_id,
                                   payload_json, priority, status, requested_by)
      VALUES (''change_hektor_offre_status'', a.app_dossier_id, a.hektor_annonce_id::text,
              jsonb_build_object(
                ''type'',              ''refus'',
                ''hektor_offre_id'',   cascade_offre.hektor_affaire_id::text,
                ''hektor_annonce_id'', a.hektor_annonce_id,
                ''app_affaire_id'',    cascade_offre.app_affaire_id,
                ''etat_avant'',        cascade_offre.state,
                ''etat_apres'',        ''refused'',
                ''geste'',             ''refus'',
                ''sans_resynchro'',    true,
                ''origine'',           ''cascade_annulation_compromis'',
                ''cascade_depuis'',    target_affaire_id),
              coalesce(job_priority, 7), ''pending'', auth.uid());
      cascade_faites := cascade_faites + 1;
    END LOOP;
  END IF;

';

  texte := replace(texte, ancre, bloc || ancre);

  -- Les deux variables de la cascade, declarees avec les autres.
  texte := replace(texte,
    '  bloc_id       text;',
    '  bloc_id       text;' || chr(10) ||
    '  -- ⭐ la cascade (11/11/2026)' || chr(10) ||
    '  cascade_offre app_affaire_ledger%rowtype;' || chr(10) ||
    '  cascade_faites int := 0;');

  -- Et on la DIT dans le retour : un geste qui en declenche un autre doit le dire.
  texte := replace(texte,
    '    ''job_type'', type_job' || chr(10) || '  );',
    '    ''job_type'', type_job,' || chr(10) ||
    '    ''offres_refusees_en_cascade'', cascade_faites' || chr(10) || '  );');

  execute texte;
  raise notice '✅ cascade posee. Interrupteur : app_setting ''cascade_annulation_compromis'' = ''on''.';
end $$;

-- ─── LE TEMOIN ─────────────────────────────────────────────────────────────
select 'pose de la cascade' as controle,
       (position('cascade_annulation_compromis' in pg_get_functiondef(p.oid)) > 0) as cascade_presente_attendu_true,
       (position('offre_verrouillee' in pg_get_functiondef(p.oid)) > 0)            as temoin_positif_garde_16_09,
       (position('compromis_verrouille' in pg_get_functiondef(p.oid)) > 0)         as temoin_positif_garde_23_10,
       p.prosecdef                                                                 as security_definer_attendu_true,
       length(pg_get_functiondef(p.oid))                                           as taille
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public' and p.proname = 'app_geste_affaire_optimistic';

-- ⛔ L'INTERRUPTEUR N'EST PAS ALLUME PAR CE PATCH. Pour l'allumer, avec accord :
--   insert into public.app_setting (key, value, description)
--   values ('cascade_annulation_compromis', 'on',
--           'Cascade 11/11/2026 : annuler un compromis refuse l''offre de son dossier')
--   on conflict (key) do update set value = excluded.value;
-- Pour l'eteindre : update public.app_setting set value='off' where key='cascade_annulation_compromis';
