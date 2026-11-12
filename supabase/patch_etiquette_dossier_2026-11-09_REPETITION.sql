-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DU PATCH DE L'ÉTIQUETTE DE DOSSIER                    12/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- À coller APRÈS patch_etiquette_dossier_2026-11-09.sql. ⛔ ELLE N'ÉCRIT RIEN :
-- chaque bloc est un SELECT. Les onze contrôles doivent être VERTS.
--
-- ⚠ POURQUOI ELLE ARRIVE TROIS JOURS APRÈS LE PATCH. Elle manquait — le patch
--   avait son INVERSE mais pas sa répétition, et le projet exige les deux depuis
--   le 19/10. Écrite le 12/11, avant le collage, donc rien n'a été posé sans elle.
--
-- ⚠⚠ ET LES ATTENDUS DU PATCH SONT PÉRIMÉS, CE N'EST PAS UN DÉFAUT. Ses
--   commentaires annoncent 12 138 dossiers, 12 029 / 98 / 11 : c'est la mesure du
--   09/11. Depuis, le chaînage a reçu la règle D et les rattachements à la main
--   (12/11, commit 518b08b) et le registre a 11 441 dossiers. Les attendus de
--   CETTE répétition sont ceux du 12/11, mesurés juste avant de l'écrire :
--
--       dossiers                   11 441
--       par la date de transaction 11 347   (99,2 %)
--       par la date du mandat          88   ⚠ l'année s'y trompe 1 fois sur 3
--       muets (annee 0000)              6
--       années distinctes              25   de 0000 à 2026
--
--   ⛔ SI VOS CHIFFRES DIFFÈRENT, ce n'est pas forcément faux : le chaînage bouge
--     chaque nuit. Ce qui doit tenir, ce sont les INVARIANTS (⑦ et ⑧) et les
--     égalités internes (⑥), jamais les totaux.
-- ═══════════════════════════════════════════════════════════════════════════


-- ① LES DEUX COLONNES EXISTENT, et le registre a bien ses lignes.
--    ⛔ Un zéro ne se croit pas sans témoin positif : la 3e colonne EST le témoin.
select '① les colonnes' as controle,
       count(*) filter (where column_name = 'app_dossier_uuid')   as uuid_attendu_1,
       count(*) filter (where column_name = 'app_dossier_numero') as numero_attendu_1,
       (select count(*) from public.app_affaire_ledger)           as lignes_temoin_positif
from information_schema.columns
where table_schema = 'public' and table_name = 'app_affaire_ledger'
  and column_name in ('app_dossier_uuid', 'app_dossier_numero');


-- ② LE PATCH EST DORMANT : aucune étiquette posée.
select '② dormant' as controle,
       count(app_dossier_uuid)   as uuid_poses_attendu_0,
       count(app_dossier_numero) as numeros_poses_attendu_0,
       count(*)                  as lignes_temoin_positif
from public.app_affaire_ledger;


-- ③ LES DEUX TABLES EXISTENT ET SONT VIDES.
select '③ les tables' as controle,
       (select count(*) from information_schema.tables
         where table_schema='public' and table_name='app_dossier_numero_compteur')   as compteur_attendu_1,
       (select count(*) from information_schema.tables
         where table_schema='public' and table_name='app_dossier_etiquette_journal') as journal_attendu_1,
       (select count(*) from public.app_dossier_numero_compteur)    as compteur_lignes_attendu_0,
       (select count(*) from public.app_dossier_etiquette_journal)  as journal_lignes_attendu_0;


-- ④ LES TROIS FONCTIONS EXISTENT.
select '④ les fonctions' as controle,
       count(*) filter (where p.proname = 'app_dossier_numero_format')     as format_attendu_1,
       count(*) filter (where p.proname = 'app_dossier_annee_ouverture')   as annee_attendu_1,
       count(*) filter (where p.proname = 'app_poser_etiquettes_dossier')  as pose_attendu_1
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.proname in ('app_dossier_numero_format', 'app_dossier_annee_ouverture',
                    'app_poser_etiquettes_dossier');


-- ⑤ LE FORMAT, aux trois bouts de la cascade.
--    ⛔ Et son TÉMOIN INVERSE : une valeur qu'il ne doit PAS rendre. Sans lui,
--      une fonction qui renverrait toujours la même chaîne passerait le contrôle.
select '⑤ le format' as controle,
       public.app_dossier_numero_format(2026, 431) as attendu_D2026_0431,
       public.app_dossier_numero_format(1990, 7)   as attendu_D1990_0007,
       public.app_dossier_numero_format(0, 11)     as attendu_D0000_0011,
       (public.app_dossier_numero_format(2026, 431)
        <> public.app_dossier_numero_format(2026, 432)) as temoin_inverse_attendu_true;


-- ⑥ L'ANNÉE D'OUVERTURE, avec son témoin inverse : un dossier daté doit rendre
--    une année NON nulle, et le dossier muet 28724 doit rendre 0. Sinon la
--    fonction rend 0 pour tout le monde et le contrôle ⑦ ne le verrait pas.
select '⑥ l annee' as controle,
       public.app_dossier_annee_ouverture(
         (select min(app_chaine_id) from public.app_affaire_ledger
           where date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}' and date not like '0000%'
             and app_chaine_id is not null)) as date_attendu_non_nul,
       public.app_dossier_annee_ouverture(28724) as muet_attendu_0;


-- ⑦ LA CASCADE EN ENTIER. Les trois marches doivent s'ADDITIONNER au total :
--    c'est l'égalité qui compte, pas les chiffres absolus.
with g as (
  select l.app_chaine_id,
         min(case when l.date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
                   and l.date not like '0000%'
                  then left(l.date, 4) end) as an_t,
         min(l.hektor_annonce_id)           as annonce
  from public.app_affaire_ledger l
  where l.app_chaine_id is not null
  group by l.app_chaine_id
),
m as (
  select a.hektor_annonce_id,
         min(case when a.date_debut ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
                   and a.date_debut not like '0000%'
                  then left(a.date_debut, 4) end) as an_m
  from public.app_mandat a
  group by a.hektor_annonce_id
)
select '⑦ la cascade' as controle,
       count(*)                                                    as dossiers_mesure_11441,
       count(*) filter (where g.an_t is not null)                   as par_transaction_mesure_11347,
       count(*) filter (where g.an_t is null and m.an_m is not null) as par_mandat_mesure_88,
       count(*) filter (where g.an_t is null and m.an_m is null)     as muets_mesure_6,
       (count(*) = count(*) filter (where g.an_t is not null)
                 + count(*) filter (where g.an_t is null and m.an_m is not null)
                 + count(*) filter (where g.an_t is null and m.an_m is null))
         as les_trois_marches_font_le_total_attendu_true
from g left join m on m.hektor_annonce_id = g.annonce::text;


-- ⑧ LA POSE À BLANC : ce que B3 ferait, sans rien écrire.
--    « pose » doit annoncer AUTANT de dossiers que ⑦ en compte ; les trois
--    autres gestes doivent être à 0, puisque rien n'est encore posé.
select '⑧ a blanc' as controle, *
from public.app_poser_etiquettes_dossier(p_a_blanc => true);


-- ⑨ L'INVARIANT, à relire APRÈS chaque pose : un groupe = UNE étiquette,
--    une étiquette = UN groupe. Les deux doivent rendre 0.
--    ⛔ Avant la pose ils rendent 0 parce qu'il n'y a RIEN -- c'est pourquoi la
--      3e colonne dit combien d'étiquettes sont posées : un 0 partout veut dire
--      « patch dormant », pas « invariant vérifié ».
select '⑨ l invariant' as controle,
       (select count(*) from (
          select app_chaine_id from public.app_affaire_ledger
          where app_chaine_id is not null and app_dossier_uuid is not null
          group by app_chaine_id having count(distinct app_dossier_uuid) > 1) z)
         as groupes_a_plusieurs_etiquettes_attendu_0,
       (select count(*) from (
          select app_dossier_uuid from public.app_affaire_ledger
          where app_dossier_uuid is not null and app_chaine_id is not null
          group by app_dossier_uuid having count(distinct app_chaine_id) > 1) z)
         as etiquettes_sur_plusieurs_groupes_attendu_0,
       (select count(app_dossier_uuid) from public.app_affaire_ledger)
         as etiquettes_posees_pour_lire_les_deux_zeros;


-- ⑩ LES DROITS, ET C'EST LE CONTRÔLE QUE LE PROJET A PAYÉ DEUX FOIS.
--    « revoke all from public » NE FERME PAS authenticated : chaque fonction naît
--    avec execute pour lui. On vérifie donc nommément que la fonction de POSE est
--    fermée à authenticated et à anon, et que les deux LECTURES leur sont ouvertes
--    -- ce dernier point est le témoin inverse : si tout était fermé, le premier
--    contrôle passerait pour la mauvaise raison.
select '⑩ les droits' as controle,
       has_function_privilege('authenticated',
         'public.app_poser_etiquettes_dossier(integer, boolean)', 'execute') as pose_authenticated_attendu_false,
       has_function_privilege('anon',
         'public.app_poser_etiquettes_dossier(integer, boolean)', 'execute') as pose_anon_attendu_false,
       has_function_privilege('authenticated',
         'public.app_dossier_numero_format(integer, integer)', 'execute')    as format_authenticated_attendu_true,
       has_function_privilege('authenticated',
         'public.app_dossier_annee_ouverture(bigint)', 'execute')            as annee_authenticated_attendu_true;


-- ⑪ LE RLS est actif sur les deux tables neuves, et le journal a sa politique
--    de lecture.
select '⑪ le RLS' as controle,
       (select relrowsecurity from pg_class
         where oid = 'public.app_dossier_etiquette_journal'::regclass) as journal_rls_attendu_true,
       (select relrowsecurity from pg_class
         where oid = 'public.app_dossier_numero_compteur'::regclass)   as compteur_rls_attendu_true,
       (select count(*) from pg_policies
         where schemaname='public' and tablename='app_dossier_etiquette_journal') as politiques_journal_attendu_1;


-- ═══════════════════════════════════════════════════════════════════════════
-- ⑫ CE QUI NE SE LIT PAS EN SQL -- À VÉRIFIER DANS LE CODE, AVANT B3
-- ═══════════════════════════════════════════════════════════════════════════
-- La condition C1 de l'audit du 29/10 : les DEUX colonnes doivent figurer dans
-- COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS, sinon un « --push » pousse le miroir local,
-- qui ne les connaît pas, et les EFFACE (leçon du 07/09 : une annulation de 06:38
-- effacée à 07:52).
--
--     grep -n "app_dossier_uuid" phase2/sync/affaire_ledger.py
--
-- ✅ VÉRIFIÉ LE 12/11 : les deux y sont, l. 2561 de la liste du push ET dans la
--    boucle de création des colonnes locales. Le code local est donc prêt AVANT
--    le patch -- l'ordre sûr, celui que le patch demande en tête.
