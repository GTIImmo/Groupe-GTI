-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — L'ANNÉE DES ÉTIQUETTES                            12/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- ⛔ ELLE N'ÉCRIT RIEN : chaque bloc est un SELECT.
--    Écrite AVANT le collage, comme le projet l'exige depuis le 19/10.
--
-- ELLE SE JOUE TROIS FOIS, ET LES ATTENDUS CHANGENT À CHAQUE FOIS :
--    ⓐ AVANT tout            -> l'etat du matin, et les 708 a redater
--    ⓑ APRES ..._LECTEURS    -> les lecteurs sont repares, RIEN n'a bouge
--    ⓒ APRES ..._REPOSE      -> les etiquettes sont justes
--
-- ⚠ LES TOTAUX NE SONT PAS DES ATTENDUS. Le chaînage bouge chaque nuit : ce qui
--   doit tenir, ce sont les ÉGALITÉS et les INVARIANTS, jamais les chiffres bruts.
-- ═══════════════════════════════════════════════════════════════════════════


-- ① LES DEUX LECTEURS EXISTENT-ILS, ET LA POSE PASSE-T-ELLE PAR EUX ?
--    ⓐ 0 . 0 . false        ⓑ et ⓒ 1 . 1 . true
--    ⛔ Le 3e point est le seul qui compte vraiment : une fonction reparee que la
--      pose n'appelle pas ne sert a rien -- c'est exactement le defaut du matin.
select '① les lecteurs' as controle,
       count(*) filter (where p.proname = 'app_dossier_annee_date_transaction') as annee_attendu_1,
       count(*) filter (where p.proname = 'app_dossier_jour_date_transaction')  as jour_attendu_1,
       exists (select 1 from pg_proc q join pg_namespace m on m.oid = q.pronamespace
                where m.nspname = 'public' and q.proname = 'app_poser_etiquettes_dossier'
                  and pg_get_functiondef(q.oid) like '%app_dossier_annee_date_transaction%')
         as LA_POSE_PASSE_PAR_EUX_attendu_true,
       exists (select 1 from pg_proc q join pg_namespace m on m.oid = q.pronamespace
                where m.nspname = 'public' and q.proname = 'app_dossier_annee_ouverture'
                  and pg_get_functiondef(q.oid) like '%app_dossier_annee_date_transaction%')
         as l_annee_d_ouverture_aussi_attendu_true
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.proname in ('app_dossier_annee_date_transaction', 'app_dossier_jour_date_transaction');


-- ② LE LECTEUR, SUR LE CAS RÉEL — l'offre 3678 du dossier 3676.
--    Proposee et acceptee le 14/08/2025, refusee le 11/11/2026 par notre lot.
--    attendu : colonne 2026 . lecteur 2025 . et le TÉMOIN INVERSE à true
--    ⛔ Sans le témoin, un lecteur qui rendrait toujours la même année passerait.
select '② sur le cas reel' as controle,
       left(l.date, 4)                                            as la_colonne_dit_2026,
       public.app_dossier_annee_date_transaction(l.kind, l.date,
              l.propositions_json::text)                          as le_lecteur_dit_2025,
       public.app_dossier_jour_date_transaction(l.kind, l.date,
              l.propositions_json::text)                          as le_jour_dit_2025_08_14,
       (public.app_dossier_annee_date_transaction(l.kind, l.date, l.propositions_json::text)
        <> left(l.date, 4))                                       as temoin_inverse_attendu_true
from public.app_affaire_ledger l
where l.app_affaire_id = 3678;


-- ③ LES TÉMOINS INVERSES DU LECTEUR — les formes qui ne doivent PAS bouger.
--    ⛔ Les trois dernières lignes sont le cœur du contrôle : un compromis, une
--      vente et une offre sans journal doivent rendre EXACTEMENT leur colonne.
select '③ temoins inverses' as controle,
       public.app_dossier_annee_date_transaction('compromis', '2014-05-24', null)   as compromis_attendu_2014,
       public.app_dossier_annee_date_transaction('vente', '2025-10-03', null)       as vente_attendu_2025,
       public.app_dossier_annee_date_transaction('offre', '2020-01-15', null)       as offre_sans_journal_attendu_2020,
       public.app_dossier_annee_date_transaction('offre', '2015-06-06',
         '[{"type":"proposition","date":"0000-00-00"}]')                            as journal_0000_attendu_2015,
       public.app_dossier_annee_date_transaction('offre', '2026-11-11',
         '{"type":"proposition","date":"2018-04-04"}')                              as objet_seul_attendu_2018,
       public.app_dossier_annee_date_transaction('offre', '0000-00-00', '[]')       as rien_attendu_null,
       public.app_dossier_annee_date_transaction('offre', '2019-03-03', 'pas du json') as illisible_attendu_2019;


-- ④ COMBIEN DE DOSSIERS SONT MAL DATÉS, MAINTENANT ?
--    ⓐ et ⓑ  708 mal dates, dont 653 etiquetes « 2026 » a tort
--    ⓒ       0 et 0        <- c'est LE contrôle de la repose
--    ⛔ La 3e colonne est le témoin positif : sans elle, un 0 pourrait vouloir
--      dire « plus aucune etiquette » au lieu de « toutes justes ».
with g as (
  select l.app_chaine_id,
         min(l.app_dossier_numero) as numero,
         min(case when l.date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}' and l.date not like '0000%'
                  then left(l.date, 4) end) as par_la_colonne,
         min(public.app_dossier_annee_date_transaction(
               l.kind, l.date, l.propositions_json::text)) as par_le_lecteur
  from public.app_affaire_ledger l
  where l.app_chaine_id is not null
  group by l.app_chaine_id
)
select '④ les mal dates' as controle,
       count(*) filter (where numero is not null
                          and par_le_lecteur is not null
                          and left(numero, 5) <> 'D' || par_le_lecteur) as mal_dates_puis_0,
       count(*) filter (where numero like 'D2026-%'
                          and par_le_lecteur is not null
                          and par_le_lecteur <> '2026')                 as faux_2026_puis_0,
       count(numero)                                                    as etiquettes_posees_TEMOIN_POSITIF,
       count(*)                                                         as dossiers
from g;


-- ⑤ LA BIJECTION ET LES DEUX INVARIANTS — les trois doivent tenir aux trois temps.
--    attendu : 0 . 0 . 0 . et les deux derniers EGAUX, jamais nuls apres ⓒ
select '⑤ les invariants' as controle,
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
       (select count(*) from public.app_affaire_ledger
         where app_chaine_id is not null and app_dossier_uuid is null)
         as chainees_sans_etiquette_attendu_0,
       (select count(distinct app_dossier_uuid) from public.app_affaire_ledger
         where app_chaine_id is not null) as etiquettes,
       (select count(distinct app_chaine_id) from public.app_affaire_ledger
         where app_chaine_id is not null) as dossiers_les_deux_EGAUX;


-- ⑥ LA POSE À BLANC — elle n'écrit rien, et elle doit être MUETTE.
--    ⓐ ⓑ ⓒ : les quatre gestes à 0. Si « pose » n'est pas à 0, des groupes sont
--    nus ; si « fusion » ou « scission » bougent, le chaînage a changé depuis.
select '⑥ a blanc' as controle, * from public.app_poser_etiquettes_dossier(p_a_blanc => true);


-- ⑦ LE COMPTEUR ET LE JOURNAL se tiennent-ils ?
--    ⓒ : la somme des rangs du compteur = le nombre de dossiers, et la somme des
--    transactions journalisées = le nombre de transactions chaînées.
select '⑦ compteur et journal' as controle,
       (select coalesce(sum(dernier), 0) from public.app_dossier_numero_compteur)   as somme_des_rangs,
       (select count(distinct app_chaine_id) from public.app_affaire_ledger
         where app_chaine_id is not null)                                          as dossiers_DOIT_EGALER,
       (select count(*) from public.app_dossier_etiquette_journal)                 as lignes_de_journal,
       (select coalesce(sum(combien), 0) from public.app_dossier_etiquette_journal) as transactions_journalisees,
       (select count(*) from public.app_affaire_ledger where app_chaine_id is not null)
         as transactions_chainees_DOIT_EGALER,
       (select count(*) from public.app_dossier_numero_compteur)                   as annees_distinctes;


-- ⑧ LE FORMAT DU NUMÉRO est-il tenu partout ?
--    attendu : 0 mal formé, et le témoin positif dit combien ont été vérifiés.
select '⑧ le format' as controle,
       count(*) filter (where app_dossier_numero !~ '^D[0-9]{4}-[0-9]{4,}$')
         as mal_formes_attendu_0,
       count(app_dossier_numero) as verifies_TEMOIN_POSITIF,
       min(app_dossier_numero) as le_plus_petit,
       max(app_dossier_numero) as le_plus_grand
from public.app_affaire_ledger;


-- ⑨ LES NUMÉROS SONT-ILS CHRONOLOGIQUES DANS LEUR ANNÉE ?
--    ⭐ C'est le gain de la repose, et il ne se lit nulle part ailleurs : dans une
--      même année, un dossier ouvert plus tôt doit porter un rang plus petit.
--    ⓐ : beaucoup de desordres (653 numeros poses hors de leur annee)
--    ⓒ : 0 ou presque -- les egalites de jour se departagent par le numero de
--        chaine, donc un petit reste est NORMAL et il est affiche a part.
with d as (
  select l.app_chaine_id,
         min(l.app_dossier_numero) as numero,
         min(public.app_dossier_jour_date_transaction(
               l.kind, l.date, l.propositions_json::text)) as jour
  from public.app_affaire_ledger l
  where l.app_chaine_id is not null and l.app_dossier_uuid is not null
  group by l.app_chaine_id
),
p as (
  select left(numero, 5) as annee,
         substring(numero from 7)::integer as rang,
         jour,
         lag(jour) over (partition by left(numero, 5) order by substring(numero from 7)::integer) as jour_du_precedent
  from d where numero is not null and jour is not null
)
select '⑨ chronologie' as controle,
       count(*) filter (where jour < jour_du_precedent) as desordres,
       count(*)                                          as compares_TEMOIN_POSITIF,
       round(100.0 * count(*) filter (where jour >= jour_du_precedent)
             / nullif(count(*) filter (where jour_du_precedent is not null), 0), 2) as pourcent_en_ordre
from p;


-- ⑩ LES DROITS, et c'est le contrôle que le projet a payé deux fois.
--    « revoke all from public » NE FERME PAS authenticated.
--    attendu : false . false . true . true   (les deux derniers sont le témoin
--    inverse : si tout était fermé, le premier passerait pour la mauvaise raison)
select '⑩ les droits' as controle,
       has_function_privilege('authenticated',
         'public.app_poser_etiquettes_dossier(integer, boolean)', 'execute') as pose_authenticated_attendu_false,
       has_function_privilege('anon',
         'public.app_poser_etiquettes_dossier(integer, boolean)', 'execute') as pose_anon_attendu_false,
       has_function_privilege('service_role',
         'public.app_poser_etiquettes_dossier(integer, boolean)', 'execute') as pose_service_role_attendu_true,
       has_function_privilege('authenticated',
         'public.app_dossier_annee_date_transaction(text, text, text)', 'execute') as lecteur_authenticated_attendu_true;


-- ⑪ LA SAUVEGARDE EXISTE-T-ELLE, ET DIT-ELLE LA VÉRITÉ ?
--    ⓒ : 31 151 lignes copiées, toutes étiquetées, et les UUID ont TOUS changé.
--    ⛔ La dernière colonne est le témoin que la repose a vraiment eu lieu : si
--      elle valait 0, on aurait rejoué le patch sur un registre déjà reposé.
select '⑪ la sauvegarde' as controle,
       (select count(*) from information_schema.tables
         where table_schema = 'public'
           and table_name = 'app_etiquette_avant_repose_20261112') as table_attendu_1,
       (select count(*) from public.app_etiquette_avant_repose_20261112) as lignes_copiees,
       (select count(*) from public.app_etiquette_avant_repose_20261112 s
          join public.app_affaire_ledger l on l.app_affaire_id = s.app_affaire_id
         where l.app_dossier_uuid is distinct from s.app_dossier_uuid)
         as uuid_CHANGES_doit_etre_le_total,
       (select count(*) from public.app_etiquette_avant_repose_20261112 s
          join public.app_affaire_ledger l on l.app_affaire_id = s.app_affaire_id
         where l.app_dossier_numero is distinct from s.app_dossier_numero)
         as numeros_changes;


-- ⑫ CE QUE PERSONNE NE DOIT LIRE — à revérifier, parce que c'est la condition
--    qui rend la repose gratuite. Mesuré le 12/11 : aucune dépendance.
select '⑫ personne ne la lit' as controle,
       (select count(*) from pg_constraint
         where contype = 'f' and confrelid = 'public.app_affaire_ledger'::regclass)
         as cles_etrangeres_attendu_0,
       (select count(*) from pg_views
         where schemaname = 'public'
           and (definition ilike '%app_dossier_uuid%'
             or definition ilike '%app_dossier_numero%')) as vues_attendu_0,
       (select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public'
           and p.proname not in ('app_dossier_numero_format', 'app_poser_etiquettes_dossier')
           and (pg_get_functiondef(p.oid) ilike '%app_dossier_uuid%'
             or pg_get_functiondef(p.oid) ilike '%app_dossier_numero%')) as autres_fonctions_attendu_0;

-- ⚠ ET CE QUI NE SE LIT PAS EN SQL, à refaire à la main avant la repose :
--     grep -rn "app_dossier_uuid\|app_dossier_numero" apps/ backend/ Console/ scheduled/
--   doit rendre AUCUN résultat. Le jour où il en rend un, la repose n'est plus gratuite.
