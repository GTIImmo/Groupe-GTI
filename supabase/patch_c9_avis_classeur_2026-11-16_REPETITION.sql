-- ═══════════════════════════════════════════════════════════════════════════
-- C9 (1re moitie) -- LES CONTROLES, REJOUABLES. Aucune ecriture.
-- Ecrite AVANT le collage, comme le projet l'exige.
-- ═══════════════════════════════════════════════════════════════════════════

select 'lignes posees' as controle, count(*)::text as mesure, '2588' as attendu
  from public.app_classeur_avis
union all
select 'avis_a_envoyer renseignes', count(avis_a_envoyer)::text, '2266'
  from public.app_classeur_avis
union all
select 'commentaire_avis renseignes', count(commentaire_avis)::text, '392'
  from public.app_classeur_avis
union all
select 'avis_envoye renseignes', count(avis_envoye)::text, '2405'
  from public.app_classeur_avis
union all
select 'aucune ligne entierement vide', count(*)::text, '0'
  from public.app_classeur_avis
 where avis_a_envoyer is null and commentaire_avis is null and avis_envoye is null
union all
select 'toutes portent la marque du lot', count(*)::text, '0'
  from public.app_classeur_avis where ecrit_par is distinct from 'classeur:C9:2026-11-16'
union all
select 'origine = classeur partout', count(*)::text, '0'
  from public.app_classeur_avis where origine <> 'classeur'
union all
-- ⭐⭐ LE CONTROLE QUI FAIT LA SPECIFICITE DE C9 : les lignes HORS DU PONT sont
--   la quand meme, parce que la clef est `id_unique` et non la transaction.
-- ⛔⛔ ET LES DEUX CHIFFRES SONT MESURES, PAS SOUHAITES. Ma premiere version
--   annoncait « doit etre > 0 » pour les deux : la mesure du 16/11 rend 0 et 8.
--   Un controle qui attend une valeur FAUSSE est pire qu'aucun controle -- il
--   rougit pour rien, et on apprend a ignorer ses rouges.
select 'posees SANS identite dans le pont', count(*)::text,
       '0 au 16/11 : les 18 absentes de A6 ne portent AUCUN avis'
  from public.app_classeur_avis a
 where not exists (select 1 from public.app_classeur_ligne_id p
                    where p.id_unique = a.id_unique)
union all
select 'posees SANS AUCUN LIEN dans le gel', count(*)::text,
       '8 au 16/11 -- autant d avis que C8 et C4 PERDRAIENT, eux'
  from public.app_classeur_avis a
 where not exists (select 1 from public.app_classeur_lien l
                    where l.id_unique = a.id_unique)
union all
-- ⭐ TEMOIN DE VOCABULAIRE : les valeurs doivent rester VARIEES. Un lot ramene a
--   deux ou trois valeurs signalerait une normalisation involontaire.
select 'valeurs distinctes en avis_a_envoyer',
       count(distinct avis_a_envoyer)::text, '~120 (A1)'
  from public.app_classeur_avis
union all
select 'valeurs distinctes en avis_envoye',
       count(distinct avis_envoye)::text, '~69 (A1)'
  from public.app_classeur_avis
order by 1;
