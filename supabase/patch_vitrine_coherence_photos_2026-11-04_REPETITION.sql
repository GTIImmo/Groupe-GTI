-- =====================================================================
-- CONTROLE du critere de coherence de la vitrine -- 04/11/2026
-- A COLLER APRES le patch. TOUTES les colonnes doivent valoir true.
-- =====================================================================
-- ⚠ Un controle qui AGREGE perd ce qui sert a agir : les points 7 et 8
--   NOMMENT les annonces en defaut, ils ne se contentent pas d'un compte.
-- ⚠ Un ZERO ne se croit pas sans temoin positif : le point 6 prouve que
--   la comparaison MORD vraiment (5 400+ masquees a comparer), sinon un
--   zero ne dirait rien.
-- =====================================================================

with masquees as (
  select 'https://dwaqxfrinihnychuoptk.supabase.co/storage/v1/object/public/gti-photo/'
         || (derives_json->'w400'->>'chemin') as url, app_dossier_id
    from app_console_photo
   where visible is false and present_in_hektor is true
     and derives_json->'w400'->>'chemin' is not null
), est_dedans as (
  select d.app_dossier_id, d.hektor_annonce_id, e->>'url' as url
    from app_dossier_current d
    cross join lateral jsonb_array_elements(d.images_preview_json_app) e
   where d.images_preview_json_app is not null
), doit_y_etre as (
  select p.app_dossier_id,
         'https://dwaqxfrinihnychuoptk.supabase.co/storage/v1/object/public/gti-photo/'
         || (p.derives_json->'w400'->>'chemin') as url
    from app_console_photo p
   where p.present_in_hektor and p.visible is not false
     and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
), fuites as (
  select v.hektor_annonce_id, count(*) as n
    from est_dedans v join masquees m
      on m.url = v.url and m.app_dossier_id = v.app_dossier_id
   group by 1
), manquantes as (
  select t.app_dossier_id, count(*) as n
    from doit_y_etre t
   where exists (select 1 from app_dossier_current d
                  where d.app_dossier_id = t.app_dossier_id
                    and d.images_preview_json_app is not null)
     and not exists (select 1 from est_dedans v
                      where v.app_dossier_id = t.app_dossier_id and v.url = t.url)
   group by 1
)
select
  -- 1. LE CRITERE EST BIEN EN PLACE
  (select pg_get_functiondef(p.oid) like '%tmp_incoherents%'
     from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where p.proname='app_photos_remplir_adresses_app' and n.nspname='public')
    as C01_le_critere_est_pose,

  -- 2. LES DEUX SENS SONT COUVERTS (pas seulement « une de trop »)
  (select pg_get_functiondef(p.oid) like '%(2) une entree a le droit%'
       or (length(pg_get_functiondef(p.oid))
           - length(replace(pg_get_functiondef(p.oid), 'not exists (select 1 from est_dedans', ''))) > 0
     from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where p.proname='app_photos_remplir_adresses_app' and n.nspname='public')
    as C02_le_sens_demasquage_est_couvert,

  -- 3. ⛔ LE CRITERE SUR LA COUVERTURE N'EST PAS REVENU (44 765 faux positifs)
  (select pg_get_functiondef(p.oid) not like '%couvertures%'
     from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where p.proname='app_photos_remplir_adresses_app' and n.nspname='public')
    as C03_pas_de_critere_sur_la_couverture,

  -- 4. LE PLANCHER DE SECURITE EST INTACT (< 5000 dossiers -> refus)
  (select pg_get_functiondef(p.oid) like '%vivantes < 5000%'
     from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where p.proname='app_photos_remplir_adresses_app' and n.nspname='public')
    as C04_le_plancher_est_intact,

  -- 5. LA SAUVEGARDE DU RETOUR ARRIERE EXISTE
  (select count(*) = 2 from app_sauvegarde_fonction_20261104)
    as C05_la_sauvegarde_porte_les_deux_fonctions,

  -- 6. ⭐ TEMOIN POSITIF : la comparaison MORD-ELLE ? (sinon le zero du 7 ne vaut rien)
  (select count(*) > 5000 from masquees)
    as C06_temoin_positif_il_y_a_bien_des_masquees_a_comparer,

  -- 7. ⭐⭐ AUCUNE MASQUEE DANS UNE VITRINE -- et on NOMME les fautives
  (select count(*) = 0 from fuites)
    as C07_zero_masquee_dans_une_vitrine,
  (select coalesce(string_agg(hektor_annonce_id || ' (' || n || ' photos)', ', '), 'aucune')
     from fuites) as C07bis_les_annonces_en_fuite,

  -- 8. AUCUNE PHOTO LEGITIME OUBLIEE -- et on NOMME les fautives
  (select count(*) = 0 from manquantes)
    as C08_zero_photo_legitime_oubliee,
  (select coalesce(string_agg(app_dossier_id || ' (' || n || ')', ', '), 'aucun')
     from manquantes) as C08bis_les_dossiers_incomplets,

  -- 9. LES DEUX ANNONCES DU 04/11 SONT REPAREES
  (select jsonb_array_length(images_preview_json_app)
            = (select count(*) from app_console_photo
                where hektor_annonce_id='63184' and visible is true)
     from app_dossier_current where hektor_annonce_id=63184)
    as C09_63184_est_reparee,
  (select jsonb_array_length(images_preview_json_app)
            = (select count(*) from app_console_photo
                where hektor_annonce_id='63073' and visible is true)
     from app_dossier_current where hektor_annonce_id=63073)
    as C10_63073_est_reparee,

  -- 11. AUCUNE FONCTION D'ESSAI OUBLIEE EN PRODUCTION
  (select count(*) = 0 from pg_proc where proname like '%essai0411%')
    as C11_aucune_fonction_d_essai_oubliee,

  -- 12. ⭐ TEMOIN INVERSE : le parc n'a pas ete vide par le correctif
  (select count(*) > 10000 from app_dossier_current
    where images_preview_json_app is not null)
    as C12_temoin_inverse_les_vitrines_existent_toujours;
