-- ═══════════════════════════════════════════════════════════════════════════
-- LES CONTROLES DU RE-GEL ADDITIF -- a rejouer autant de fois qu'on veut
-- 17/11/2026. ⛔ IL N'ECRIT RIEN.
-- ⭐ Chaque ligne porte CE QU'ON ATTEND, pour qu'un ecart saute aux yeux.
-- ═══════════════════════════════════════════════════════════════════════════
select 'liens poses par le re-gel (attendu 195)' as controle,
       count(*)::text as mesure,
       case when count(*) = 195 then '✅' else '⛔' end as verdict
  from app_classeur_lien where gele_par = 'c5 re-gel additif 2026-11-17'
union all
select 'le gel au total (attendu 12 790 = 12 595 + 195)', count(*)::text,
       case when count(*) = 12790 then '✅' else '⛔' end from app_classeur_lien
union all
select '⭐ LE BUT : les 195 transactions SANS lien (attendu 0)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from app_affaire_ledger l where l.transaction_origine = 'classeur'
   and not exists (select 1 from app_classeur_lien k where k.app_affaire_id = l.app_affaire_id)
union all
select '⭐⭐ liens d origine DISPARUS (attendu 0)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from app_classeur_lien_avant_regel_20261117 s
  left join app_classeur_lien k on k.ligne_classeur = s.ligne_classeur
                               and k.app_affaire_id = s.app_affaire_id
 where k.app_affaire_id is null
union all
select '⭐⭐ liens d origine MODIFIES (attendu 0)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from app_classeur_lien_avant_regel_20261117 s
  join app_classeur_lien k on k.ligne_classeur = s.ligne_classeur
                          and k.app_affaire_id = s.app_affaire_id
 where k.role is distinct from s.role or k.confiance is distinct from s.confiance
    or k.preuves is distinct from s.preuves or k.etage is distinct from s.etage
    or k.id_unique is distinct from s.id_unique
union all
select 'chaque lien neuf a le MEME role que sa transaction (attendu 0 faux)',
       count(*)::text, case when count(*) = 0 then '✅' else '⛔' end
  from app_classeur_lien k join app_affaire_ledger l on l.app_affaire_id = k.app_affaire_id
 where k.gele_par = 'c5 re-gel additif 2026-11-17' and k.role <> l.kind
union all
select 'et le MEME id_unique que son payload (attendu 0 faux)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from app_classeur_lien k join app_affaire_ledger l on l.app_affaire_id = k.app_affaire_id
 where k.gele_par = 'c5 re-gel additif 2026-11-17'
   and k.id_unique is distinct from l.payload_json->>'classeur_id_unique'
union all
select '⛔ TEMOIN INVERSE -- liens CASSES (attendu 0)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from app_v_classeur_lien_casse where gravite = 'DISPARUE'
union all
select '⛔ TEMOIN INVERSE -- la vue des liens casses (attendu 9, inchange)',
       count(*)::text, case when count(*) = 9 then '✅' else '⚠ a bouge' end
  from app_v_classeur_lien_casse
union all
select 'lignes du classeur couvertes (attendu >= 4 702)',
       count(distinct id_unique)::text,
       case when count(distinct id_unique) >= 4702 then '✅' else '⛔' end
  from app_classeur_lien
union all
select '⭐ VOISINES -- les 195 transactions (attendu 195)', count(*)::text,
       case when count(*) = 195 then '✅' else '⛔' end
  from app_affaire_ledger where transaction_origine = 'classeur'
union all
select '⭐ les 3 lots des 195, chacun entierement lie',
       (select string_agg(lot || '=' || n, ' . ' order by lot)
          from (select l.payload_json->>'classeur_lot' as lot, count(*)::text as n
                  from app_affaire_ledger l
                  join app_classeur_lien k on k.app_affaire_id = l.app_affaire_id
                 where l.transaction_origine = 'classeur'
                   and k.gele_par = 'c5 re-gel additif 2026-11-17'
                 group by 1) s),
       case when (select count(*) from app_affaire_ledger l
                   join app_classeur_lien k on k.app_affaire_id = l.app_affaire_id
                  where l.transaction_origine = 'classeur'
                    and k.gele_par = 'c5 re-gel additif 2026-11-17') = 195
            then '✅' else '⛔' end;
