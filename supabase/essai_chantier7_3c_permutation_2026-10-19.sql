-- ════════════════════════════════════════════════════════════════════════════════
--  ⑦-3c · ESSAI : HEKTOR ACCEPTE-T-IL UNE PERMUTATION QUELCONQUE ?
--  Bac a sable 62774 (dossier 3828957)                           19/10/2026
--  Accord de Frederic : « A et oui pour essai »
-- ════════════════════════════════════════════════════════════════════════════════
--
--  CE QU'ON VEUT PROUVER, ET POURQUOI CE N'EST PAS DEJA PROUVE.
--  `mode=ordonne_photos` tourne en production depuis le 14/10, mais seulement
--  pour DEUX usages :
--      · renumeroter apres une suppression  (la liste change de TAILLE)
--      · mettre une photo en 1er            (la couverture)
--  ⛔ Il n'a JAMAIS recu une permutation quelconque. Tant qu'on ne l'a pas
--     mesure, les deux fleches de l'ecran reposent sur une supposition.
--
--  ⭐ L'ESSAI CHOISI : ECHANGER LES RANGS 2 ET 3.
--     C'est le cas le plus probant, parce que ce n'est NI l'un NI l'autre des
--     deux usages connus :
--         la liste garde la MEME taille      -> ce n'est pas une renumerotation
--         la PREMIERE photo ne bouge PAS     -> ce n'est pas une couverture
--     Et c'est exactement ce que fera la fleche -> de l'ecran.
--
--  L'ETAT D'AVANT, mesure le 19/10 :
--      482254  rang 1  visible
--      487603  rang 2  visible
--      487604  rang 3  visible
--      482253  rang 1  ⛔ MASQUEE  <- le temoin de ⑦-8, elle doit RESTER masquee
--
--  L'ORDRE VOULU :  482254 , 487604 , 487603      (2 et 3 echanges)
--
--  ⚠ CE N'EST PAS UNE IMITATION : on insere un vrai travail
--    `reorder_hektor_photos`, celui que le worker execute depuis le 16/10, et on
--    construit ses deux listes DEPUIS NOTRE TABLE -- exactement comme le fera la
--    future RPC. On eprouve LE code, pas une maquette.
--
--  ⚠ ET ON RENUMEROTE CHEZ NOUS D'ABORD, dans la MEME transaction. C'est la
--    regle de Frederic du 19/10 : « il faut d'abord ecrire chez nous, ensuite
--    envoyer l'information a Hektor ». Si l'insertion du travail echouait, la
--    renumerotation est annulee avec elle.
--
--  ⚠ SI HEKTOR REFUSE : notre ordre serait faux jusqu'a la PARTIE 2, qui relit
--    ses galeries et remet notre table d'aplomb. C'est dit, ce n'est pas cache.
-- ════════════════════════════════════════════════════════════════════════════════


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  PARTIE 1 -- L'ENVOI.  A coller en entier.                                   ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

begin;

-- ⓵ L'IDENTITE D'ESSAI. ⚠ Dans l'editeur SQL `auth.uid()` est NUL : la lecon du
--    19/10 (marche 4 a rendu « droits_insuffisants » au 1er essai). On emprunte
--    donc codex.test, et dans la MEME transaction -- un set_config seul se perd
--    entre deux instructions.
select set_config('request.jwt.claims',
                  '{"sub":"0548613b-7654-42fa-a65d-d9adc815d2c0","role":"authenticated"}',
                  true) as identite_empruntee;

-- ⓶ LE TEMOIN D'AVANT, pour pouvoir comparer apres.
select '① AVANT' as etape, hektor_photo_id, sort_order, visible
  from public.app_console_photo
 where hektor_annonce_id = '62774' and present_in_hektor is true
 order by visible desc, sort_order asc, id asc;

-- ⓷ LA RENUMEROTATION CHEZ NOUS, 0 -> n-1, dans l'ORDRE VOULU.
--    ⚠ On renumerote par une liste EXPLICITE : c'est ce que l'ecran enverra.
--      (La RPC generique fera pareil, avec la liste recue du front.)
with voulu(hektor_photo_id, rang) as (
  values ('482254', 0), ('487604', 1), ('487603', 2)
)
update public.app_console_photo p
   set sort_order = v.rang, updated_at = now()
  from voulu v
 where p.hektor_annonce_id = '62774'
   and p.hektor_photo_id   = v.hektor_photo_id
   and p.visible is true
   and p.present_in_hektor is true;

-- ⓸ LE GARDE-FOU : on a bien touche 3 photos, pas 2, pas 4.
do $$
declare v_n integer;
begin
  select count(*) into v_n
    from public.app_console_photo
   where hektor_annonce_id = '62774' and visible is true and present_in_hektor is true
     and sort_order in (0,1,2);
  if v_n <> 3 then
    raise exception 'ARRET : % photos en rang 0-1-2, il en faut exactement 3', v_n;
  end if;
end $$;

-- ⓹ LE TRAVAIL, construit DEPUIS NOTRE TABLE -- comme le fera la RPC.
with visibles as (
  select coalesce(jsonb_agg(hektor_photo_id order by sort_order asc, id asc), '[]'::jsonb) as liste
    from public.app_console_photo
   where app_dossier_id = 3828957 and visible is true and present_in_hektor is true
),
masquees as (
  select coalesce(jsonb_agg(hektor_photo_id order by sort_order asc, id asc), '[]'::jsonb) as liste
    from public.app_console_photo
   where app_dossier_id = 3828957 and visible is false and present_in_hektor is true
),
avant as (
  select coalesce(jsonb_agg(jsonb_build_object('hektor_photo_id', hektor_photo_id,
                                               'sort_order', sort_order,
                                               'visible', visible)
                            order by visible desc, sort_order asc, id asc), '[]'::jsonb) as etat
    from public.app_console_photo
   where app_dossier_id = 3828957 and present_in_hektor is true
)
insert into public.app_console_job
  (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
select 'reorder_hektor_photos', 3828957, '62774',
       jsonb_build_object(
         'motif', 'essai_permutation_quelconque',
         'hektor_photo_id', null,
         'liste_photos', v.liste,
         'liste_photos_hidden', m.liste,
         'base_snapshot', a.etat),
       15, '0548613b-7654-42fa-a65d-d9adc815d2c0'::uuid
  from visibles v, masquees m, avant a
returning id as travail_cree,
          payload_json->'liste_photos'        as ordre_envoye_visibles,
          payload_json->'liste_photos_hidden' as ordre_envoye_masquees;

-- ⓺ LE TEMOIN D'APRES, chez nous.
select '② APRES (chez nous)' as etape, hektor_photo_id, sort_order, visible
  from public.app_console_photo
 where hektor_annonce_id = '62774' and present_in_hektor is true
 order by visible desc, sort_order asc, id asc;

commit;

-- ⚠ APRES LE COMMIT : le worker prend le travail en 1 a 6 secondes (mesure sur
--   les 4 precedents). Attendre ~15 secondes, puis coller la PARTIE 2.


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  PARTIE 2 -- LE JUGE.  A coller ~15 s plus tard.                             ║
-- ║                                                                              ║
-- ║  ⭐ C'est la relecture des galeries de HEKTOR qui tranche, pas notre table.  ║
-- ║     `sync_hektor_photos` lit ses DEUX galeries et reecrit nos rangs depuis    ║
-- ║     ce qu'il rend. Donc :                                                    ║
-- ║        si Hektor a ACCEPTE -> nos rangs restent 482254, 487604, 487603        ║
-- ║        s'il a REFUSE       -> ils reviennent a 482254, 487603, 487604         ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

-- ⓵ CE QUE LE TRAVAIL A DIT (son compte rendu, pas une supposition).
select id, status, attempt_count,
       round(extract(epoch from (finished_at - started_at)))::text || ' s' as duree,
       worker_id,
       coalesce(error_message, '(aucune erreur)') as erreur,
       result_json
  from public.app_console_job
 where job_type = 'reorder_hektor_photos'
   and payload_json->>'motif' = 'essai_permutation_quelconque'
 order by requested_at desc
 limit 1;

-- ⓶ ON DEMANDE LA RELECTURE DES GALERIES (c'est elle qui juge).
begin;
select set_config('request.jwt.claims',
                  '{"sub":"0548613b-7654-42fa-a65d-d9adc815d2c0","role":"authenticated"}',
                  true) as identite_empruntee;
insert into public.app_console_job
  (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
values
  ('sync_hektor_photos', 3828957, '62774',
   jsonb_build_object('motif', 'juge_essai_permutation'),
   15, '0548613b-7654-42fa-a65d-d9adc815d2c0'::uuid)
returning id as travail_de_relecture;
commit;

-- ⚠ Attendre ~30 secondes (une relecture de galerie prend plus qu'un envoi),
--   puis coller la PARTIE 2 bis.


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  PARTIE 2 bis -- LE VERDICT.                                                 ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

select '③ APRES RELECTURE DE HEKTOR' as etape,
       hektor_photo_id, sort_order, visible,
       to_char(updated_at, 'DD/MM HH24:MI:SS') as ecrite_le
  from public.app_console_photo
 where hektor_annonce_id = '62774' and present_in_hektor is true
 order by visible desc, sort_order asc, id asc;

-- ⭐ LE VERDICT, EN UNE LIGNE, calcule et non interprete.
with ordre as (
  select string_agg(hektor_photo_id, ',' order by sort_order asc, id asc) as visibles
    from public.app_console_photo
   where hektor_annonce_id = '62774' and visible is true and present_in_hektor is true
),
etat as (
  select (select count(*) from public.app_console_photo
           where hektor_annonce_id = '62774' and visible is false and present_in_hektor is true) as masquees,
         (select count(*) from public.app_console_photo
           where hektor_annonce_id = '62774' and present_in_hektor is true) as total
)
select o.visibles as ordre_des_visibles,
       e.masquees, e.total,
       case
         when o.visibles = '482254,487604,487603'
           then '⭐⭐ HEKTOR A ACCEPTE LA PERMUTATION -- les deux fleches sont fondees'
         when o.visibles = '482254,487603,487604'
           then '⛔ HEKTOR A REFUSE (ou ignore) -- il a rendu l''ordre d''avant'
         else '⚠ ORDRE INATTENDU : ' || o.visibles || ' -- a lire avant de conclure'
       end as verdict_permutation,
       case when e.masquees = 1 and e.total = 4
            then '⭐ LE TEMOIN TIENT : 482253 est toujours masquee, 4 photos en tout'
            else '⛔ LE TEMOIN A BOUGE -- a regarder tout de suite' end as verdict_masquage
  from ordre o, etat e;


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  PARTIE 3 -- LE RETOUR ARRIERE.  A coller QUEL QUE SOIT LE RESULTAT.         ║
-- ║                                                                              ║
-- ║  ⚠ Il remet l'ordre d'avant l'essai : 482254, 487603, 487604.                ║
-- ║    On ne laisse pas le bac a sable dans un etat qu'on a fabrique.            ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

begin;

select set_config('request.jwt.claims',
                  '{"sub":"0548613b-7654-42fa-a65d-d9adc815d2c0","role":"authenticated"}',
                  true) as identite_empruntee;

with avant(hektor_photo_id, rang) as (
  values ('482254', 0), ('487603', 1), ('487604', 2)
)
update public.app_console_photo p
   set sort_order = a.rang, updated_at = now()
  from avant a
 where p.hektor_annonce_id = '62774'
   and p.hektor_photo_id   = a.hektor_photo_id
   and p.visible is true
   and p.present_in_hektor is true;

with visibles as (
  select coalesce(jsonb_agg(hektor_photo_id order by sort_order asc, id asc), '[]'::jsonb) as liste
    from public.app_console_photo
   where app_dossier_id = 3828957 and visible is true and present_in_hektor is true
),
masquees as (
  select coalesce(jsonb_agg(hektor_photo_id order by sort_order asc, id asc), '[]'::jsonb) as liste
    from public.app_console_photo
   where app_dossier_id = 3828957 and visible is false and present_in_hektor is true
)
insert into public.app_console_job
  (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
select 'reorder_hektor_photos', 3828957, '62774',
       jsonb_build_object(
         'motif', 'retour_arriere_essai_permutation',
         'hektor_photo_id', null,
         'liste_photos', v.liste,
         'liste_photos_hidden', m.liste),
       15, '0548613b-7654-42fa-a65d-d9adc815d2c0'::uuid
  from visibles v, masquees m
returning id as travail_de_retour, payload_json->'liste_photos' as ordre_remis;

select '④ APRES LE RETOUR ARRIERE' as etape, hektor_photo_id, sort_order, visible
  from public.app_console_photo
 where hektor_annonce_id = '62774' and present_in_hektor is true
 order by visible desc, sort_order asc, id asc;

commit;
