-- ═══════════════════════════════════════════════════════════════════════════
-- LES CONTROLES DE B2 ET B3 -- a rejouer autant de fois qu'on veut
-- 17/11/2026. ⛔ IL N'ECRIT RIEN.
-- ⭐ Chaque ligne porte CE QU'ON ATTEND, pour qu'un ecart saute aux yeux.
-- ═══════════════════════════════════════════════════════════════════════════
select 'B2 -- lignes du classeur sans lien (attendu 85)' as controle,
       count(*)::text as mesure,
       case when count(*) = 85 then '✅'
            when count(*) < 85 then '⭐ a BAISSE -- le re-gel a rattache, baisser le seuil'
            else '⛔ A MONTE -- une ligne a PERDU son lien' end as verdict
  from app_v_classeur_ligne_sans_lien
union all
select 'B3 -- orphelines au total (attendu 11)', count(*)::text,
       case when count(*) = 11 then '✅' else '⚠ a bouge' end
  from app_v_affaire_note_condition_orpheline
union all
select '⭐⭐ B3 -- orphelines NON declarees (attendu 0) : CE QUE LA SENTINELLE LIT',
       count(*)::text, case when count(*) = 0 then '✅' else '⛔' end
  from app_v_affaire_note_condition_orpheline where not deja_declaree
union all
select '⛔ TEMOIN POSITIF -- les declarees (attendu 11, prouve que le filtre MORD)',
       count(*)::text, case when count(*) = 11 then '✅' else '⛔' end
  from app_v_affaire_note_condition_orpheline where deja_declaree
union all
select '   dont des NOTES (attendu 6)', count(*)::text,
       case when count(*) = 6 then '✅' else '⚠' end
  from app_v_affaire_note_condition_orpheline where objet = 'note'
union all
select '   dont des CONDITIONS (attendu 5)', count(*)::text,
       case when count(*) = 5 then '✅' else '⚠' end
  from app_v_affaire_note_condition_orpheline where objet = 'condition'
union all
select '⭐ les 11 sont TOUTES des essais du 23/10 sur le dossier 1068399 (attendu 11)',
       count(*)::text, case when count(*) = 11 then '✅' else '⚠ une autre cause' end
  from app_v_affaire_note_condition_orpheline
 where app_dossier_id = 1068399 and origine = 'saisie'
union all
select '⛔ TEMOIN INVERSE -- anon ne lit NI l une NI l autre (attendu false)',
       (has_table_privilege('anon','public.app_v_classeur_ligne_sans_lien','SELECT')
        or has_table_privilege('anon','public.app_v_affaire_note_condition_orpheline','SELECT'))::text,
       case when not (has_table_privilege('anon','public.app_v_classeur_ligne_sans_lien','SELECT')
                   or has_table_privilege('anon','public.app_v_affaire_note_condition_orpheline','SELECT'))
            then '✅' else '⛔' end
union all
select 'authenticated lit les deux (attendu true)',
       (has_table_privilege('authenticated','public.app_v_classeur_ligne_sans_lien','SELECT')
        and has_table_privilege('authenticated','public.app_v_affaire_note_condition_orpheline','SELECT'))::text,
       case when has_table_privilege('authenticated','public.app_v_classeur_ligne_sans_lien','SELECT')
             and has_table_privilege('authenticated','public.app_v_affaire_note_condition_orpheline','SELECT')
            then '✅' else '⛔' end
union all
select '⭐ VOISINE -- app_v_repartition_orpheline en service (attendu 0 orpheline)',
       count(*)::text, case when count(*) = 0 then '✅' else '⛔' end
  from app_v_repartition_orpheline
union all
select '⭐ VOISINES -- les notes et conditions posees le 17/11 sont INTACTES',
       (select count(*)::text from app_affaire_note
         where position('[classeur F, suivi en cours au 17/11/2026]' in texte) > 0)
       || ' notes . '
       || (select count(*)::text from app_affaire_condition
            where origine = 'classeur:F-credit') || ' conditions',
       case when (select count(*) from app_affaire_note
                   where position('[classeur F, suivi en cours au 17/11/2026]' in texte) > 0) = 80
             and (select count(*) from app_affaire_condition
                   where origine = 'classeur:F-credit') = 28
            then '✅ 80 et 28' else '⛔' end;
