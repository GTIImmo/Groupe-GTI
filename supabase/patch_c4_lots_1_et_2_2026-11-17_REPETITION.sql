-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (3e patch) -- LES CONTROLES, A REJOUER AUTANT DE FOIS QU'ON VEUT
-- Genere le 2026-11-17. ⛔ IL N'ECRIT RIEN.
-- ⭐ Chaque ligne porte CE QU'ON ATTEND, pour qu'un ecart saute aux yeux.
-- ═══════════════════════════════════════════════════════════════════════════
select 'LOT 1 -- textes de F marques (attendu 80)' as controle,
       count(*)::text as mesure,
       case when count(*) = 80 then '✅' else '⛔' end as verdict
  from app_affaire_note where position('[classeur F, suivi en cours au 17/11/2026]' in texte) > 0
union all
select 'LOT 1 -- dont CREEES (attendu 0)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from app_affaire_note where origine = 'classeur:F-en-cours'
union all
select 'LOT 2 -- conditions de credit (attendu 23)', count(*)::text,
       case when count(*) = 23 then '✅' else '⛔' end
  from app_affaire_condition where origine = 'classeur:F-credit'
union all
select 'toutes en etat attente (attendu 23)', count(*)::text,
       case when count(*) = 23 then '✅' else '⛔' end
  from app_affaire_condition where origine = 'classeur:F-credit' and etat = 'attente'
union all
select 'toutes avec une echeance (attendu 23)', count(*)::text,
       case when count(*) = 23 then '✅' else '⛔' end
  from app_affaire_condition
 where origine = 'classeur:F-credit' and date_echeance is not null
union all
select 'toutes sur la clause Obtention Credit (attendu 23)', count(*)::text,
       case when count(*) = 23 then '✅' else '⛔' end
  from app_affaire_condition
 where origine = 'classeur:F-credit' and catalogue_id = '2'
union all
select '⭐⭐ LE TEXTE D AVANT EST INTACT (attendu 0 perdu)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from app_c4_note_avant_20261117 s
  join app_affaire_note a on a.app_affaire_id = s.app_affaire_id
 where position(s.texte in a.texte) = 0
union all
select '⭐ VOISIN -- les 195 notes de C5 (attendu 195)', count(*)::text,
       case when count(*) = 195 then '✅' else '⛔' end
  from app_affaire_note where origine = 'classeur'
union all
select '⭐ VOISIN -- les notes du 2e patch (attendu 4325)', count(*)::text,
       case when count(*) = 4325 then '✅' else '⛔' end
  from app_affaire_note
 where origine in ('classeur:F', 'classeur:G', 'classeur:F+G')
union all
select '⭐ VOISIN -- les 5 conditions saisies (attendu 5)', count(*)::text,
       case when count(*) = 5 then '✅' else '⛔' end
  from app_affaire_condition where origine = 'saisie'
union all
select 'aucune note vide, TOUTE la table (attendu 0)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from app_affaire_note where coalesce(btrim(texte), '') = ''
union all
select 'une seule note par transaction (attendu 0 doublon)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from (select app_affaire_id from app_affaire_note
         group by app_affaire_id having count(*) > 1) d
union all
select '⛔ TEMOIN INVERSE -- aucune condition en levee (attendu 0)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from app_affaire_condition
 where origine = 'classeur:F-credit' and (etat = 'levee' or date_levee is not null)
union all
select '⛔ TEMOIN INVERSE -- aucune echeance hors 2024-2027 (attendu 0)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from app_affaire_condition
 where origine = 'classeur:F-credit'
   and (date_echeance < '2024-01-01'::date or date_echeance > '2027-12-31'::date)
union all
select '⭐ les conditions tombent sur des COMPROMIS (attendu 23)', count(*)::text,
       case when count(*) = 23 then '✅' else '⛔' end
  from app_affaire_condition c
  join app_affaire_ledger l on l.app_affaire_id = c.app_affaire_id
 where c.origine = 'classeur:F-credit' and l.kind = 'compromis'
union all
select '⭐ les notes marquees tombent sur une CHAINE (attendu 80)', count(*)::text,
       case when count(*) = 80 then '✅' else '⛔' end
  from app_affaire_note n
  join app_affaire_ledger l on l.app_affaire_id = n.app_affaire_id
 where position('[classeur F, suivi en cours au 17/11/2026]' in n.texte) > 0 and l.app_chaine_id is not null;
