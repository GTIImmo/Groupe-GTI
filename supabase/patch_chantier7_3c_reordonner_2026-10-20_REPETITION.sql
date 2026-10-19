-- ════════════════════════════════════════════════════════════════════════════════
--  ⑦-3c · REPETITION DU PATCH « REORDONNER » — TOUT EST ANNULE A LA FIN
--                                                                 20/10/2026
-- ════════════════════════════════════════════════════════════════════════════════
--
--  A COLLER APRES LE PATCH. Elle ouvre UNE transaction, eprouve la recette sur le
--  bac a sable 62774, et finit par un ROLLBACK : rien ne reste.
--
--  ⚠⚠ ELLE N'APPELLE PAS HEKTOR. Elle cree un travail, et le ROLLBACK le supprime
--    avant qu'aucun worker ne puisse le prendre. Le geste reel, lui, a deja ete
--    prouve le 19/10 a 23:26 (Hektor a rendu la permutation envoyee).
--
--  ⚠ L'IDENTITE EST EMPRUNTEE DANS LA MEME TRANSACTION. Lecon du 19/10 : dans
--    l'editeur SQL `auth.uid()` est NUL, et la marche 4 a rendu
--    « droits_insuffisants » au premier essai. Un `set_config` seul se perd entre
--    deux instructions.
--    ⭐ ET ON GARDE LE REFUS SANS IDENTITE COMME TEMOIN INVERSE GRATUIT : le
--      point ① appelle AVANT d'emprunter, et doit etre refuse.
--
--  L'ETAT D'AVANT, mesure le 20/10 a 00:16 (apres la resynchro du balayage) :
--      482254  rang 1  visible
--      487603  rang 2  visible
--      487604  rang 3  visible
--      482253  rang 1  MASQUEE   <- le temoin : elle ne doit JAMAIS bouger
--  dossier 3828957 · identite d'essai codex.test 0548613b-7654-42fa-a65d-d9adc815d2c0
-- ════════════════════════════════════════════════════════════════════════════════

begin;

-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  ① TEMOIN INVERSE GRATUIT : SANS IDENTITE, C'EST REFUSE                      ║
-- ║     ⭐ Sans ce point, une recette qui laisserait passer n'importe qui         ║
-- ║       passerait les 8 autres sans qu'on le voie.                             ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

select '① sans identite' as point,
       (public.app_console_photos_reordonner_optimistic(
          3828957, '62774', array['482254','487604','487603']) ->> 'erreur') as resultat,
       'attendu : droits_insuffisants' as attendu;

-- ─── on emprunte maintenant l'identite d'essai, pour tout le reste ───────────
select set_config('request.jwt.claims',
                  '{"sub":"0548613b-7654-42fa-a65d-d9adc815d2c0","role":"authenticated"}',
                  true) as identite_empruntee;


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  ② LES REFUS, UN PAR UN — chacun doit dire LEQUEL                            ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

select '②a parametres manquants' as point,
       (public.app_console_photos_reordonner_optimistic(NULL, '62774', array['482254']) ->> 'erreur') as resultat,
       'attendu : parametres_incomplets' as attendu
union all
select '②b annonce vide',
       (public.app_console_photos_reordonner_optimistic(3828957, '  ', array['482254']) ->> 'erreur'),
       'attendu : parametres_incomplets'
union all
select '②c ordre vide',
       (public.app_console_photos_reordonner_optimistic(3828957, '62774', array[]::text[]) ->> 'erreur'),
       'attendu : ordre_vide'
union all
select '②d doublon dans la liste',
       (public.app_console_photos_reordonner_optimistic(
          3828957, '62774', array['482254','482254','487603']) ->> 'erreur'),
       'attendu : ordre_avec_doublons'
union all
select '②e photo inconnue',
       (public.app_console_photos_reordonner_optimistic(
          3828957, '62774', array['482254','487603','999999']) ->> 'erreur'),
       'attendu : ordre_avec_photos_inconnues'
union all
select '②f ordre INCOMPLET (2 sur 3)',
       (public.app_console_photos_reordonner_optimistic(
          3828957, '62774', array['482254','487603']) ->> 'erreur'),
       'attendu : ordre_incomplet'
union all
select '②g ⭐ LA MASQUEE DANS LA LISTE DES VISIBLES',
       (public.app_console_photos_reordonner_optimistic(
          3828957, '62774', array['482254','487603','487604','482253']) ->> 'erreur'),
       'attendu : ordre_avec_photos_inconnues (elle n''est pas visible)'
union all
select '②h ⭐ DEJA DANS CET ORDRE (on ne derange pas Hektor)',
       (public.app_console_photos_reordonner_optimistic(
          3828957, '62774', array['482254','487603','487604']) ->> 'deja_dans_cet_ordre')::text,
       'attendu : true';


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  ③ LE GESTE REEL : on echange les rangs 2 et 3                               ║
-- ║     ⭐ Ni une renumerotation, ni une mise en couverture : la 1re ne bouge pas.║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

select '③ le geste' as point,
       public.app_console_photos_reordonner_optimistic(
         3828957, '62774', array['482254','487604','487603']) as retour;


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  ④ LES TEMOINS, DANS LES DEUX SENS                                           ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

-- a) l'ordre chez nous, et le temoin inverse : l'ANCIEN ordre a-t-il DISPARU ?
with o as (
  select string_agg(hektor_photo_id, ',' order by sort_order asc, id asc) as suite,
         string_agg(hektor_photo_id || ':' || sort_order::text, ' ' order by sort_order asc, id asc) as rangs
    from public.app_console_photo
   where app_dossier_id = 3828957 and visible is true and present_in_hektor is true
)
select '④a l''ordre chez nous' as point, o.suite, o.rangs,
       case when o.suite = '482254,487604,487603'
            then '⭐ LE NOUVEL ORDRE EST LA' else '⛔ ROUGE : ' || o.suite end as temoin_direct,
       case when o.suite <> '482254,487603,487604'
            then '⭐ ET L''ANCIEN A DISPARU' else '⛔ ROUGE : l''ancien est encore la' end as temoin_inverse,
       case when o.rangs like '482254:0%' then '⭐ la numerotation commence a 0'
            else '⚠ elle ne commence pas a 0 : ' || o.rangs end as numerotation
  from o;

-- b) ⭐ LE TEMOIN QUI COMPTE LE PLUS : la masquee n'a pas bouge
select '④b la masquee' as point,
       count(*)                                                as masquees,
       string_agg(hektor_photo_id || ':' || sort_order::text, ' ') as detail,
       case when count(*) = 1 and string_agg(hektor_photo_id, ',') = '482253'
            then '⭐ 482253 EST TOUJOURS MASQUEE, ET SEULE'
            else '⛔ ROUGE -- le masquage a bouge' end as verdict
  from public.app_console_photo
 where app_dossier_id = 3828957 and visible is false and present_in_hektor is true;

-- c) le travail cree : son type, son motif, et SES DEUX LISTES
select '④c le travail' as point,
       job_type, status, priority,
       payload_json->>'motif'               as motif,
       payload_json->'liste_photos'         as liste_visibles,
       payload_json->'liste_photos_hidden'  as liste_masquees,
       jsonb_array_length(payload_json->'base_snapshot') as snapshot,
       case when payload_json->'liste_photos' = '["482254","487604","487603"]'::jsonb
            then '⭐ LA LISTE ENVOYEE EST LA BONNE' else '⛔ ROUGE' end as temoin_liste,
       case when jsonb_array_length(payload_json->'liste_photos_hidden') = 1
            then '⭐ LA MASQUEE EST DANS SA PROPRE LISTE (donc elle ne sera pas demasquee)'
            else '⛔ ROUGE -- la liste des masquees est vide ou fausse' end as temoin_masquees
  from public.app_console_job
 where job_type = 'reorder_hektor_photos' and payload_json->>'motif' = 'reordonnancement'
 order by requested_at desc limit 1;

-- d) ⭐ LE POST-IT : les index sont-ils marques a refaire ?
select '④d le post-it' as point,
       (select count(*) from public.app_dossier_current
         where app_dossier_id = 3828957 and adresses_app_le is null) as vivant_a_refaire,
       (select count(*) from public.app_archive_annonce_index_current
         where app_archive_id = 3828957 and adresses_app_le is null) as archive_a_refaire,
       'le retour de la recette donne index_marques_a_refaire -- a comparer' as note;


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  ⑤ LES DEUX SOEURS SONT-ELLES INTACTES ? (on n'y a pas touche)               ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

select '⑤ les soeurs' as point, p.proname,
       case md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
         when 'cbe7d5372e79040a4eb6b7cc644ff64c' then '⭐ INTACTE (couverture)'
         when '0a5f62d1b41843e9400380a15ab14958' then '⭐ INTACTE (visibilite)'
         else '⛔ A CHANGE -- ARRET' end as verdict
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_console_photo_couverture_optimistic',
                     'app_console_photo_visibilite_optimistic')
 order by p.proname;


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  ⑥ TOUT EST ANNULE                                                           ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

rollback;

-- ⑦ APRES LE ROLLBACK : l'ordre d'avant est-il bien revenu, et le travail parti ?
select '⑦ apres le rollback' as point,
       (select string_agg(hektor_photo_id, ',' order by sort_order asc, id asc)
          from public.app_console_photo
         where app_dossier_id = 3828957 and visible is true and present_in_hektor is true) as ordre,
       (select count(*) from public.app_console_job
         where job_type = 'reorder_hektor_photos'
           and payload_json->>'motif' = 'reordonnancement') as travaux_restants,
       'attendu : 482254,487603,487604  et  0 travail' as attendu;
