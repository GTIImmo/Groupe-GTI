-- ════════════════════════════════════════════════════════════════════════════════
--  RÉPARATION DE L'ANNONCE 63073 — UN SEUL TRAVAIL, DEUX PROBLÈMES
--                                                                 19/10/2026, 23:35
-- ════════════════════════════════════════════════════════════════════════════════
--
--  POURQUOI. Le clic de Frederic du 19/10 a 14:31 (masquer une photo sur 63073) a
--  laisse DEUX choses en plan, mesurees ce soir :
--
--  ① LES 14 PHOTOS MASQUEES DECOUVERTES N'ONT JAMAIS ETE TELECHARGEES.
--     Le `sync_hektor_photos` ne de ce clic a ete TUE par le redemarrage des 4
--     services a 17:10 :
--         « Job interrompu automatiquement: execution running trop ancienne
--           (> 30 minutes). Relancer la demande si necessaire. »
--     ⚠ Et le balayage de 00:00 NE LES PRENDRA PAS : il exclut les annonces qui
--       portent un travail en erreur (regle « ne jamais rejouer un echec »).
--
--  ② LA PHOTO 485375 -- celle qu'il a masquee -- A ETE DECLAREE DISPARUE A 21:00:05
--     par l'entretien photos. Elle est donc `present_in_hektor = false`, et
--     `loadConsolePhotos` filtre sur cette colonne : ELLE EST INVISIBLE DANS L'APP,
--     DONC IMPOSSIBLE A REAFFICHER. C'est le « a sens unique » que le verrou du
--     18/10 devait empecher.
--
--  LA CAUSE DU ②, PROUVEE ET NON SUPPOSEE :
--     `accorder_photos_miroir.js` lit nos lignes dans une COPIE LOCALE
--     (`phase2/phase2.sqlite`, INDEX_LOCAL l. 116), pas dans Supabase. Mesure du
--     19/10 a 23:27 dans cette copie :
--         photo 485375  ->  visible = 1   (alors qu'elle est masquee depuis 14:31)
--         annonce 63073 ->  10 photos, 0 masquee (la production en a 24, dont 15)
--     Le verrou 7 fait `if (drapeauVisible(r) === "masquee") continue;` -- il a
--     donc lu « visible », et n'a pas protege.
--     La copie locale ne se met a jour qu'a la DESCENTE DE 07:45. Toute photo
--     masquee entre 07:45 et 21:00 tombe dans la fenetre.
--
--  AMPLEUR MESUREE CE SOIR : 1 seule photo touchee (celle-ci). Le verrou a bien
--  protege les 121 autres masquees -- parce que leur masquage est anterieur a la
--  derniere descente, donc connu de la copie locale.
--
--  ⭐ POURQUOI UN SEUL TRAVAIL SUFFIT. `sync_hektor_photos` relit les DEUX
--    galeries de Hektor (visibles + masquees) et :
--      · repose `present_in_hektor = true` sur ce que Hektor rend encore
--        -> le ② est repare (preuve de ce soir : la photo 482253 de 62774, marquee
--           disparue elle aussi a 21:00, a ete remise d'aplomb par le sync de
--           23:26:10 -- le meme geste, deja observe en vrai) ;
--      · telecharge les fichiers manquants -> le ① est repare.
--
--  COUT : 2 lectures chez Hektor pour les galeries, plus 1 telechargement par
--  photo manquante (jusqu'a 14). Soit ~16 requetes au maximum.
--  ⚠ A NE PAS COLLER PENDANT LE BALAYAGE DE 00:00 SI ON VEUT LIRE LE RESULTAT
--    TRANQUILLEMENT -- mais c'est sans danger : le worker fait la queue.
-- ════════════════════════════════════════════════════════════════════════════════


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  ① L'ETAT D'AVANT (lecture seule, pour pouvoir comparer)                     ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

select 'AVANT' as etape,
       count(*)                                                as photos_chez_nous,
       count(*) filter (where visible is true)                  as visibles,
       count(*) filter (where visible is false)                 as masquees,
       count(*) filter (where present_in_hektor is false)       as declarees_disparues,
       count(*) filter (where storage_status = 'pending')       as sans_fichier,
       count(*) filter (where derives_json is not null)         as avec_derive
  from public.app_console_photo
 where hektor_annonce_id = '63073';


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  ② LA DEMANDE DE RELECTURE                                                   ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

begin;

-- ⚠ Dans l'editeur SQL `auth.uid()` est NUL : on emprunte l'identite d'essai dans
--   la MEME transaction (lecon du 19/10, marche 4).
select set_config('request.jwt.claims',
                  '{"sub":"0548613b-7654-42fa-a65d-d9adc815d2c0","role":"authenticated"}',
                  true) as identite_empruntee;

-- ⚠ GARDE-FOU : on ne pose RIEN si un sync est deja en vol sur cette annonce
--   (meme regle que les deux `enqueue*` du worker).
do $$
declare v_en_vol integer;
begin
  select count(*) into v_en_vol
    from public.app_console_job
   where hektor_annonce_id = '63073'
     and job_type = 'sync_hektor_photos'
     and status in ('pending','running');
  if v_en_vol > 0 then
    raise exception 'ARRET : % sync_hektor_photos deja en vol sur 63073 -- rien a poser', v_en_vol;
  end if;
end $$;

insert into public.app_console_job
  (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
select 'sync_hektor_photos',
       d.app_dossier_id,
       '63073',
       jsonb_build_object('motif', 'reparation_19_10_clic_frederic_et_marquage_2100'),
       15,
       '0548613b-7654-42fa-a65d-d9adc815d2c0'::uuid
  from public.app_dossier_current d
 where d.hektor_annonce_id::text = '63073'
returning id as travail_de_reparation, app_dossier_id, hektor_annonce_id;

commit;

-- ⚠ Attendre ~60 secondes : la relecture des galeries prend ~13 s, et chaque
--   photo manquante ajoute un telechargement (jusqu'a 14).


-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  ③ LE VERDICT                                                                ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

-- a) ce que le travail a dit (son compte rendu, pas une supposition)
select status, attempt_count as tentatives,
       round(extract(epoch from (finished_at - started_at)))::text || ' s' as duree,
       coalesce(error_message,'(aucune erreur)') as erreur,
       result_json
  from public.app_console_job
 where hektor_annonce_id = '63073' and job_type = 'sync_hektor_photos'
   and payload_json->>'motif' = 'reparation_19_10_clic_frederic_et_marquage_2100'
 order by requested_at desc limit 1;

-- b) l'etat d'apres, et les deux verdicts calcules
with e as (
  select count(*)                                          as photos,
         count(*) filter (where visible is true)            as visibles,
         count(*) filter (where visible is false)           as masquees,
         count(*) filter (where present_in_hektor is false) as disparues,
         count(*) filter (where storage_status = 'pending') as sans_fichier,
         count(*) filter (where derives_json is not null)   as avec_derive
    from public.app_console_photo where hektor_annonce_id = '63073'
),
cible as (
  select visible, present_in_hektor, storage_status
    from public.app_console_photo
   where hektor_annonce_id = '63073' and hektor_photo_id = '485375'
)
select 'APRES' as etape, e.*,
       case when (select present_in_hektor from cible) is true
            then '⭐ LA PHOTO 485375 EST REVENUE -- elle est de nouveau dans le panneau'
            else '⛔ ELLE EST TOUJOURS DECLAREE DISPARUE -- a regarder' end as verdict_photo_masquee,
       case when (select visible from cible) is false
            then '⭐ ET ELLE EST TOUJOURS MASQUEE -- le geste de Frederic tient'
            else '⚠ ELLE EST REDEVENUE VISIBLE -- le masquage a ete perdu' end as verdict_masquage,
       case when e.sans_fichier = 0
            then '⭐ PLUS AUCUNE PHOTO SANS FICHIER -- les 14 sont arrivees'
            else '⚠ ' || e.sans_fichier::text || ' photo(s) encore sans fichier' end as verdict_telechargement
  from e;
