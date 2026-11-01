-- ═══════════════════════════════════════════════════════════════════════════
-- CONTRÔLE de patch_registre_dossiers_droits_2026-10-31.sql                                     31/10/2026
-- À coller APRÈS le patch. N'écrit RIEN : les essais « en tant que » se font dans des transactions
-- ANNULÉES. Chaque ligne doit dire OK.
-- Témoins pris dans la base (31/10) :
--   PEREIRA (commercial, c8a61bde…) :
--     POSITIF « nommé »   chaîne 1011, bien 1993 au nom de FORLICO, parts entrée + sortie à PEREIRA
--                         → il voit le dossier, ses 3 transactions et sa répartition (2 parts) ;
--     POSITIF « ses biens » chaîne 11138, son bien, sans répartition → toujours visible ;
--     NÉGATIF             chaîne 4200, bien DELAVAUD, part sortie RONDEAU → rien, ni transaction ni part.
--   FRÉDÉRIC (admin, d4b1685f…) : voit les 12 165 dossiers (chiffre du 31/10 ; il bouge avec la nuit).
-- ═══════════════════════════════════════════════════════════════════════════

-- 1-3. Ce qui est posé
select '1 regle du registre : + dossiers nommes' as controle,
       case when position('app_mes_chaines_nommees' in (select qual from pg_policies where schemaname = 'public'
                 and tablename = 'app_affaire_ledger' and policyname = 'app_affaire_ledger_select_active_users')) > 0
            then 'OK' else '⛔ ECHEC' end as resultat
union all
select '2 repartition : plus ouverte a tous',
       case when (select qual from pg_policies where schemaname = 'public' and tablename = 'app_affaire_repartition'
                  and policyname = 'app_affaire_repartition_read') <> 'true' then 'OK' else '⛔ ECHEC' end
union all
select '3 sans utilisateur : la liste est vide',
       case when (select count(*) from public.app_registre_dossiers(null)) = 0 then 'OK' else '⛔ ECHEC' end
union all
select '4 la cle publique (anon) ne peut pas lire la liste',
       case when not has_function_privilege('anon', 'public.app_registre_dossiers(integer)', 'execute')
             and not has_function_privilege('anon', 'public.app_mes_chaines_nommees()', 'execute')
            then 'OK' else '⛔ ECHEC' end;

-- 5-11. EN TANT QUE PEREIRA (négociateur), dans une transaction ANNULÉE
BEGIN;
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims', '{"sub":"c8a61bde-2899-443f-831b-3a4f5a8ec36b","role":"authenticated"}', true);
select '5 PEREIRA : 1011 est dans ses dossiers nommes' as controle,
       case when 1011 in (select public.app_mes_chaines_nommees()) then 'OK' else '⛔ ECHEC' end as resultat
union all
select '6 PEREIRA : la liste porte 1011, marque « nomme », etape vendu',
       case when exists (select 1 from public.app_registre_dossiers(null) r
                          where r.app_chaine_id = 1011 and r.je_suis_nomme and r.etape = 'vendu')
            then 'OK' else '⛔ ECHEC' end
union all
select '7 PEREIRA : la fiche voit les 3 transactions de 1011',
       case when (select count(*) from public.app_affaire_ledger where app_chaine_id = 1011) = 3 then 'OK' else '⛔ ECHEC' end
union all
select '8 PEREIRA : la repartition de 1011 est entiere (2 parts)',
       case when (select count(*) from public.app_affaire_repartition where app_chaine_id = 1011) = 2 then 'OK' else '⛔ ECHEC' end
union all
select '9 PEREIRA : son bien (11138) reste visible',
       case when exists (select 1 from public.app_registre_dossiers(null) where app_chaine_id = 11138)
             and exists (select 1 from public.app_affaire_ledger where app_chaine_id = 11138)
            then 'OK' else '⛔ ECHEC' end
union all
select '10 PEREIRA : rien sur 4200 (ni liste, ni transaction, ni part)',
       case when not exists (select 1 from public.app_registre_dossiers(null) where app_chaine_id = 4200)
             and not exists (select 1 from public.app_affaire_ledger where app_chaine_id = 4200)
             and not exists (select 1 from public.app_affaire_repartition where app_chaine_id = 4200)
            then 'OK' else '⛔ ECHEC' end
union all
select '11 PEREIRA : la liste = exactement les dossiers que la fiche lui montre',
       case when not exists (
                 (select app_chaine_id from public.app_registre_dossiers(null))
                 except
                 (select app_chaine_id from public.app_affaire_ledger
                   where not (btrim(coalesce(hektor_affaire_id, '')) <> '' and present_in_hektor is false)))
             and not exists (
                 (select app_chaine_id from public.app_affaire_ledger
                   where app_chaine_id is not null
                     and not (btrim(coalesce(hektor_affaire_id, '')) <> '' and present_in_hektor is false))
                 except
                 (select app_chaine_id from public.app_registre_dossiers(null)))
            then 'OK' else '⛔ ECHEC' end
union all
select '12 PEREIRA : aucune part visible hors de ses dossiers',
       case when not exists (select 1 from public.app_affaire_repartition r
                              where r.app_chaine_id not in (select app_chaine_id from public.app_registre_dossiers(null)))
            then 'OK' else '⛔ ECHEC' end;
ROLLBACK;

-- 13. EN TANT QUE FRÉDÉRIC (admin), dans une transaction ANNULÉE
--     Les totaux sont comptés AVANT de changer de rôle (en postgres, sans règle), puis comparés.
BEGIN;
SELECT set_config('gti.total_dossiers', (select count(distinct app_chaine_id)::text from public.app_affaire_ledger
        where app_chaine_id is not null
          and not (btrim(coalesce(hektor_affaire_id, '')) <> '' and present_in_hektor is false)), true),
       set_config('gti.total_parts', (select count(*)::text from public.app_affaire_repartition), true);
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims', '{"sub":"d4b1685f-948b-4ce8-af15-671b94a725e6","role":"authenticated"}', true);
select '13 ADMIN : la liste porte tous les dossiers' as controle,
       case when (select count(*) from public.app_registre_dossiers(null)) = current_setting('gti.total_dossiers')::bigint
            then 'OK' else '⛔ ECHEC' end as resultat
union all
select '14 ADMIN : toute la repartition reste visible',
       case when (select count(*) from public.app_affaire_repartition) = current_setting('gti.total_parts')::bigint
            then 'OK' else '⛔ ECHEC' end;
ROLLBACK;
