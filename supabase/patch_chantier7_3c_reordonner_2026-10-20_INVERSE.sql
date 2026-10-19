-- ════════════════════════════════════════════════════════════════════════════════
--  ⑦-3c · RETOUR ARRIERE DU PATCH « REORDONNER »
--                                                                 20/10/2026
-- ════════════════════════════════════════════════════════════════════════════════
--
--  ⭐ IL EST SIMPLE PARCE QUE LE PATCH EST ADDITIF : il n'a REMPLACE aucune
--    fonction, il en a AJOUTE une. Il n'y a donc rien a restaurer -- seulement a
--    retirer.
--
--  ⚠⚠ ET UN RETOUR ARRIERE NE JUGE QUE SA PART (lecon 31 du projet) : il ne suffit
--    pas de supprimer la fonction, il faut VERIFIER qu'il ne reste aucune trace de
--    ce qu'on devait retirer -- et que les deux soeurs, qu'on n'a jamais touchees,
--    sont toujours la et toujours intactes.
--
--  ⛔ CE QU'IL NE DEFAIT PAS, ET C'EST VOULU :
--    · les travaux `reorder_hektor_photos` deja crees et executes restent dans le
--      suivi (c'est l'historique, on ne le reecrit pas) ;
--    · les `sort_order` deja renumerotes restent tels quels. ⭐ Ce n'est pas une
--      perte : l'entretien photos de 21:00 aligne notre ordre sur celui de HEKTOR
--      chaque soir (mesure du 19/10 : `photos_reordonnees: 5`), et Hektor a recu
--      l'ordre. Les deux cotes sont donc d'accord -- il n'y a rien a defaire.
--    · les `adresses_app_le` remis a blanc : le fabricant les recalculera, c'est
--      son travail normal. Un post-it en trop ne coute qu'un recalcul.
-- ════════════════════════════════════════════════════════════════════════════════

-- ① AVANT : elle est bien la (sinon il n'y a rien a retirer)
select coalesce(
         (select 'PRESENTE : ' || p.proname || '(' || pg_get_function_arguments(p.oid) || ')'
            from pg_proc p join pg_namespace n on n.oid = p.pronamespace
           where n.nspname = 'public'
             and p.proname = 'app_console_photos_reordonner_optimistic'),
         'DEJA ABSENTE -- le retour arriere n''a rien a faire') as etat_avant;

-- ② LE RETRAIT
DROP FUNCTION IF EXISTS public.app_console_photos_reordonner_optimistic(bigint, text, text[]);

-- ③ APRES : LES DEUX TEMOINS, dans les deux sens
select
  -- a) le temoin DIRECT : il ne reste aucune trace de la fonction retiree
  coalesce(
    (select 'ROUGE -- ELLE EST ENCORE LA : ' || string_agg(pg_get_function_arguments(p.oid), ' | ')
       from pg_proc p join pg_namespace n on n.oid = p.pronamespace
      where n.nspname = 'public'
        and p.proname = 'app_console_photos_reordonner_optimistic'),
    'OK -- plus aucune trace de app_console_photos_reordonner_optimistic') as temoin_direct,
  -- b) le temoin INVERSE : les deux soeurs sont toujours la, et intactes
  coalesce(
    (select string_agg(p.proname || ' : ' ||
              case md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
                when 'cbe7d5372e79040a4eb6b7cc644ff64c' then 'INTACTE'
                when '0a5f62d1b41843e9400380a15ab14958' then 'INTACTE'
                else 'A CHANGE -- ARRET' end, E'\n')
       from pg_proc p join pg_namespace n on n.oid = p.pronamespace
      where n.nspname = 'public'
        and p.proname in ('app_console_photo_couverture_optimistic',
                          'app_console_photo_visibilite_optimistic')),
    'ROUGE -- LES DEUX SOEURS ONT DISPARU') as temoin_inverse;
