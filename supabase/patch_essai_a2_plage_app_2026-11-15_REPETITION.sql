-- ════════════════════════════════════════════════════════════════════════════
-- LES CONTROLES DE L'ESSAI A2 -- 15/11/2026
-- A JOUER : juste apres la pose, PUIS DEMAIN MATIN APRES LE RUN (c'est le but).
-- ⛔ LECTURE SEULE. Aucun `commit`, aucune ecriture.
-- ════════════════════════════════════════════════════════════════════════════

-- ① LA LIGNE D'ESSAI EXISTE-T-ELLE, ET PORTE-T-ELLE BIEN LE SUJET DE L'ESSAI ?
select '1. la ligne d essai' as controle,
       count(*) as n,
       coalesce(string_agg(
         app_affaire_id || ' . ' || kind || ' . ' || coalesce(state,'(sans etat)')
         || ' . numero Hektor ' || coalesce(hektor_affaire_id,'NUL')
         || ' . present_in_hektor ' || present_in_hektor::text, ' | '), '(AUCUNE)') as detail
  from app_affaire_ledger
 where (payload_json ->> 'essai_a2_2026_11_15') = 'true';
-- ATTENDU le jour de la pose : n = 1 . numero Hektor NUL . present_in_hektor false
-- ⛔ ATTENDU DEMAIN MATIN     : n = 1, IDENTIQUE. Si n = 0, LE RUN L'A EFFACEE
--    et les 241 transactions du classeur NE PEUVENT PAS etre creees ainsi.

-- ② EST-ELLE BIEN DANS LA PLAGE APP ?
select '2. dans la plage app (>= 1 000 000)' as controle,
       count(*) filter (where app_affaire_id >= 1000000) as dans_la_plage,
       count(*) filter (where app_affaire_id <  1000000) as HORS_PLAGE_ANORMAL
  from app_affaire_ledger
 where (payload_json ->> 'essai_a2_2026_11_15') = 'true';
-- ATTENDU : dans_la_plage = 1 . HORS_PLAGE_ANORMAL = 0

-- ③ LE DOSSIER D'ORIGINE EST-IL INTACT ? (temoin : on n'a rien abime)
select '3. les 2 transactions d origine' as controle,
       count(*) as n,
       string_agg(kind || ' #' || hektor_affaire_id || ' ' || coalesce(date,'?'), ' | ') as detail
  from app_affaire_ledger
 where hektor_annonce_id = 28351 and hektor_affaire_id in ('20217', '6544');
-- ATTENDU, AVANT COMME APRES : n = 2 (compromis 20217, vente 6544)

-- ④ L'ETIQUETTE DE DOSSIER A-T-ELLE SUIVI ? (la chaine en avait une)
select '4. l etiquette de la chaine 14001' as controle,
       count(distinct app_dossier_numero) as etiquettes_distinctes,
       string_agg(distinct coalesce(app_dossier_numero,'(aucune)'), ',') as lesquelles
  from app_affaire_ledger where app_chaine_id = 14001;
-- ATTENDU : 1 seule etiquette, D2006-0007 -- l essai ne doit pas en creer une autre

-- ⑤ LE DECLENCHEUR DES PARTIES A-T-IL CREE QUELQUE CHOSE ?
select '5. parties des affaires de la chaine 14001' as controle, count(*) as n
  from app_affaire_partie
 where app_affaire_id in (select app_affaire_id from app_affaire_ledger
                           where app_chaine_id = 14001);
-- ⚠ A COMPARER avec la valeur relevee AVANT la pose. La ligne d essai n a ni
--   acquereurs_json ni mandants_json : le declencheur ne devrait RIEN ajouter.

-- ⑥ TEMOIN INVERSE : les 340 lignes legitimes de la plage app sont-elles intactes ?
select '6. temoin inverse, la plage app entiere' as controle,
       count(*) as lignes_de_la_plage,
       count(*) filter (where hektor_affaire_id is null) as sans_numero_hektor
  from app_affaire_ledger where app_affaire_id >= 1000000;
-- ATTENDU le jour de la pose : 341 lignes . 1 sans numero (la notre)
-- ⛔ ATTENDU DEMAIN MATIN     : 341 et 1. Si lignes_de_la_plage retombe a 340,
--    le run a efface NOTRE ligne ; s il tombe plus bas, il en a efface d AUTRES.

-- ⑦ ET LE CHAINAGE N'A PAS BOUGE ? (une offre refusee ne doit rien declencher)
select '7. la chaine 14001' as controle,
       count(*) as transactions_de_la_chaine,
       string_agg(kind || '/' || coalesce(state,'-'), ' | ' order by kind) as detail
  from app_affaire_ledger where app_chaine_id = 14001;
-- ATTENDU : 3 transactions (compromis/active, offre/refused, vente/-)
-- ⛔ Si la chaine s est SCINDEE ou si un etat a change, le dire AVANT de conclure.
