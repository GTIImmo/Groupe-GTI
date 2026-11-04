-- =====================================================================
-- LA VITRINE DOIT DIRE LA VERITE -- 04/11/2026
-- =====================================================================
-- LE DEFAUT, mesure le 04/11 au controle du matin :
--   app_photos_remplir_adresses_app construit la vitrine
--   (images_preview_json_app) avec le BON filtre -- elle ecarte les
--   masquees. Mais elle ne REFAIT la vitrine d'une annonce que si
--   greatest(derives_generes_le, absent_depuis) a bouge.
--   MASQUER ou DEMASQUER une photo ne touche AUCUNE de ces deux dates.
--   La vitrine reste donc perimee, et le site publie la masquee.
--
-- CE QUI A ETE MESURE (04/11, lecture seule) :
--   . annonce 63184 (dossier 7589171, Actif, diffusable) : 66 photos
--     dont 51 MASQUEES le 03/11 a 22:53. Sa vitrine porte 66 entrees
--     sur 66, et 12 de ses masquees sont sur la VITRINE PUBLIQUE
--     (catalogue exporte le 04/11 a 06:19, verifie photo par photo).
--     Sa COUVERTURE est elle-meme une photo masquee.
--   . annonce 63073 (dossier 7160424) : l'inverse -- une photo
--     DEMASQUEE le 28/10 qui n'est jamais revenue. 9 entrees pour
--     10 visibles. Cachee pour rien depuis une semaine.
--   . le filtre, lui, est BON : sur 150 annonces qui ont decouvert des
--     masquees la nuit du 03-04/11, 149 ont leur vitrine propre
--     (galeries NON VIDES verifiees : le temoin n'est pas creux).
--     Les 149 ont ete sauvees par CHANCE -- leurs derives etaient frais.
--
-- DEUX FAUSSES PISTES ECARTEES PAR LA MESURE, ne pas les refaire :
--   1. hors_vitrine_depuis n'est PAS la date de masquage malgre son nom :
--      366 744 photos VISIBLES la portent, contre 132 masquees sur 5 997.
--   2. ajouter updated_at au greatest est TROP LARGE : les cibles
--      passeraient de 3 a 9 878 dossiers sur 10 299 -- presque tout le
--      parc refait chaque nuit.
--
-- LE REMEDE POSE ICI -- on ne devine plus, on VERIFIE :
--   une table temporaire tmp_incoherents nomme les dossiers dont la
--   vitrine ne contient PAS EXACTEMENT ses photos visibles, dans les
--   DEUX SENS (une de trop / une qui manque), et dont la COUVERTURE
--   pointe une photo qui n'a pas le droit d'y etre.
--   tmp_cibles recoit ces dossiers EN PLUS de ses sources actuelles.
--
--   * On compare les IDENTIFIANTS, pas les nombres. Compter raterait le
--     REMPLACEMENT (une photo echangee contre une autre chez Hektor :
--     meme compte, autre image). Regle du projet : jamais une position,
--     toujours un identifiant.
--
--   * Les trois gestes tombent dedans tout seuls, sans etre nommes :
--       masquer    -> une entree de trop    -> on refait
--       demasquer  -> une entree qui manque -> on refait
--       supprimer  -> une entree de trop    -> on refait
--       remplacer  -> deux ecarts           -> on refait
--
-- =====================================================================
-- ⛔⛔ MON ERREUR DU 04/11, ET CE QU'ELLE A COUTE -- A LIRE AVANT DE
--     RAJOUTER UN CRITERE DANS CETTE FONCTION
-- =====================================================================
-- La 1re version de ce patch portait un TROISIEME critere : « la
-- COUVERTURE pointe-t-elle une photo qui n'a pas le droit d'y etre ? »,
-- applique aux QUATRE familles. Je l'avais ajoute au nom de la regle
-- « une cause se balaie dans toute sa famille ».
--
-- A L'EXECUTION IL A ANNONCE 47 996 VITRINES INCOHERENTES AU LIEU DE 2,
-- et la fonction a reecrit 29 623 archives + 8 464 historique + 148
-- brouillons -- 38 235 lignes pour rien.
--
-- LA CAUSE, mesuree aussitot : DEUX FILTRES POUR LA MEME CHOSE.
--   tmp_principale, qui POSE les couvertures, n'exige que w400.
--   Mon critere exigeait w400 ET w1600.
--   Donc toute couverture legitime posee avec w400 seul etait declaree
--   incoherente. 44 765 faux positifs (35 304 archives, 8 923
--   historique, 538 brouillons).
--
-- ⛔ ET MEME CORRIGE, CE CRITERE NE DEVAIT PAS EXISTER :
--   . il restait 6 530 lignes designees, dont le defaut n'est PAS une
--     fuite de masquee mais une couverture ORPHELINE (la photo n'est
--     plus dans app_console_photo). C'est un autre sujet.
--   . la mesure disait DEJA 0 couverture masquee sur les 3 familles
--     (35 369 + 8 961 + 538) : il ne protegeait de rien.
--   . la couverture des VIVANTES derive de la vitrine
--     (photo_url_listing_app = g.entrees->0->>'url'), donc (1) et (2)
--     la protegent deja. C'etait la seule famille a risque, et elle
--     etait couverte.
--
-- AUCUN DEGAT : les 38 235 lignes ont ete reecrites avec la MEME valeur
--   (tmp_principale est inchangee), seul adresses_app_le a bouge.
--   Verifie apres coup : 0 couverture masquee en archives, 0 en
--   historique, 0 masquee dans une vitrine.
--
-- ⭐ LA LECON : avant d'ajouter un critere de coherence, verifier qu'il
--   emploie LE MEME FILTRE que le code qui pose la valeur. Un critere
--   plus strict que le poseur declare faux tout ce que le poseur ecrit.
--
-- ETAT REEL APRES CORRECTION (mesure le 04/11) :
--   passage 1 (reparation)  : 2 vitrines refaites, 63184 et 63073
--   passage 2 (regime)      : 0 incoherente, 0 ligne reecrite, 0,81 s
--   controle du matin       : TOUT VERT, code 0, 5 471 masquees
--                             comparees a 10 296 galeries -> 0 fuite
-- =====================================================================
--
-- COUT MESURE (EXPLAIN ANALYZE, 04/11) :
--   la fonction d'aujourd'hui                1,0 s  (287 cibles, 159 refaites)
--   la detection par comparaison des listes  0,64 s (trouve 2 annonces)
--   -> environ 1,6 s par nuit, dans un run de 2 h 19.
--
-- CE QUI EST ADDITIF : aucune ligne supprimee, aucun filtre change, le
--   plancher de securite (< 5000 dossiers -> refus) est INTACT, les
--   sources actuelles de tmp_cibles sont INTACTES. On AJOUTE une branche.
--
-- SAUVEGARDE : app_sauvegarde_fonction_20261104 porte la definition
--   d'avant (empreinte ec8066616381cdb90df38ec561f1441f, 4934 octets)
--   et celle de app_photos_remplir_adresses_registre.
-- RETOUR ARRIERE : patch_vitrine_coherence_photos_2026-11-04_INVERSE.sql
-- CONTROLE      : patch_vitrine_coherence_photos_2026-11-04_REPETITION.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- GARDE-FOU D'EMPREINTE : si quelqu'un est passe avant moi, ON S'ARRETE.
-- ---------------------------------------------------------------------
do $$
declare
  vue text;
begin
  select md5(pg_get_functiondef(p.oid)) into vue
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where p.proname = 'app_photos_remplir_adresses_app' and n.nspname = 'public';
  if vue is null then
    raise exception 'ARRET : app_photos_remplir_adresses_app est introuvable.';
  end if;
  if vue <> 'ec8066616381cdb90df38ec561f1441f' then
    raise exception 'ARRET : la fonction a change depuis la mesure du 04/11 (vue %, attendue ec8066616381cdb90df38ec561f1441f)', vue;
  end if;
end $$;

CREATE OR REPLACE FUNCTION public.app_photos_remplir_adresses_app(p_heures integer DEFAULT 48, p_tout boolean DEFAULT false)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  base constant text := 'https://dwaqxfrinihnychuoptk.supabase.co/storage/v1/object/public/gti-photo/';
  vivantes bigint; quand timestamptz := now();
  n_viv bigint := 0; n_arc bigint := 0; n_his bigint := 0; n_bro bigint := 0;
  n_incoherents bigint := 0;
begin
  select count(*) into vivantes from public.app_dossier_current;
  if vivantes < 5000 then
    return jsonb_build_object('statut','refus',
      'raison','app_dossier_current sous le plancher : le run de nuit a probablement echoue',
      'vivantes', vivantes);
  end if;

  create temporary table tmp_maj on commit drop as
  select p.app_dossier_id, max(greatest(p.derives_generes_le, p.absent_depuis)) as dernier
    from public.app_console_photo p
   where p_tout or greatest(p.derives_generes_le, p.absent_depuis) >= quand - make_interval(hours => greatest(1, p_heures))
   group by p.app_dossier_id;

  -- =================================================================
  -- NEUF 04/11 : LA VITRINE DIT-ELLE LA VERITE ?
  --   On ne devine plus « a-t-elle bouge ? » : on verifie le RESULTAT.
  --   Masquer, demasquer, supprimer et remplacer tombent tous dedans.
  --   ATTENTION : les CTE sont GLOBAUX (non correles). La forme correlee
  --   par dossier deplie le JSON 10 296 fois et s'effondre. Mesure a
  --   0,64 s sous cette forme.
  -- =================================================================
  create temporary table tmp_incoherents (app_dossier_id bigint primary key) on commit drop;

  with est_dedans as (
    select d.app_dossier_id, e->>'url' as url
      from public.app_dossier_current d
      cross join lateral jsonb_array_elements(d.images_preview_json_app) e
     where d.images_preview_json_app is not null
  ), doit_y_etre as (
    select p.app_dossier_id, base || (p.derives_json->'w400'->>'chemin') as url
      from public.app_console_photo p
     where p.present_in_hektor and p.visible is not false
       and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
  )
  insert into tmp_incoherents (app_dossier_id)
  select distinct id from (
    -- (1) une entree est DANS la vitrine sans y avoir droit
    --     (masquee, absente de Hektor, sans grande image, inconnue)
    select v.app_dossier_id as id from est_dedans v
     where not exists (select 1 from doit_y_etre t
                        where t.app_dossier_id = v.app_dossier_id and t.url = v.url)
    union
    -- (2) une entree a le droit d'y etre et N'Y EST PAS
    --     (demasquee, ajoutee, remplacee)
    select t.app_dossier_id from doit_y_etre t
     where exists (select 1 from public.app_dossier_current d
                    where d.app_dossier_id = t.app_dossier_id
                      and d.images_preview_json_app is not null)
       and not exists (select 1 from est_dedans v
                        where v.app_dossier_id = t.app_dossier_id and v.url = t.url)
  ) s where id is not null;
  -- ⛔ IL N'Y A PAS DE CRITERE (3) SUR LA COUVERTURE -- voir l'en-tete, section
  --    « MON ERREUR DU 04/11 ». Il produisait 44 765 faux positifs et ne
  --    protegeait de rien. La couverture des VIVANTES est deja protegee :
  --    photo_url_listing_app = g.entrees->0->>'url', donc elle derive de la
  --    vitrine, elle-meme couverte par (1) et (2).

  select count(*) into n_incoherents from tmp_incoherents;

  create temporary table tmp_cibles (app_dossier_id bigint primary key) on commit drop;
  insert into tmp_cibles (app_dossier_id)
  select distinct x from (
    select d.app_dossier_id as x from public.app_dossier_current d
      left join tmp_maj m on m.app_dossier_id = d.app_dossier_id
     where d.photo_url_listing_app is null or d.adresses_app_le is null
        or (m.dernier is not null and m.dernier > d.adresses_app_le)
    union select a.app_archive_id from public.app_archive_annonce_index_current a
      left join tmp_maj m on m.app_dossier_id = a.app_archive_id
     where a.photo_url_listing_app is null or a.adresses_app_le is null
        or (m.dernier is not null and m.dernier > a.adresses_app_le)
    union select h.app_historical_id from public.app_historical_annonce_index_current h
      left join tmp_maj m on m.app_dossier_id = h.app_historical_id
     where h.photo_url_listing_app is null or h.adresses_app_le is null
        or (m.dernier is not null and m.dernier > h.adresses_app_le)
    union select b.app_brouillon_id from public.app_brouillon_annonce_index_current b
      left join tmp_maj m on m.app_dossier_id = b.app_brouillon_id
     where b.photo_url_listing_app is null or b.adresses_app_le is null
        or (m.dernier is not null and m.dernier > b.adresses_app_le)
    -- NEUF 04/11 : les dossiers dont la vitrine ou la couverture MENT
    union select i.app_dossier_id from tmp_incoherents i
  ) s where x is not null;

  create temporary table tmp_principale (app_dossier_id bigint primary key, url text) on commit drop;
  insert into tmp_principale (app_dossier_id, url)
  select distinct on (p.app_dossier_id) p.app_dossier_id, base || (p.derives_json->'w400'->>'chemin')
    from public.app_console_photo p join tmp_cibles c on c.app_dossier_id = p.app_dossier_id
   where p.present_in_hektor and p.visible is not false and p.derives_json ? 'w400'
   order by p.app_dossier_id, p.visible desc nulls last, p.sort_order asc nulls last, p.id;

  create temporary table tmp_galerie (app_dossier_id bigint primary key, entrees jsonb) on commit drop;
  insert into tmp_galerie (app_dossier_id, entrees)
  select p.app_dossier_id,
         jsonb_agg(jsonb_build_object('url', base || (p.derives_json->'w400'->>'chemin'),
                                      'full', base || (p.derives_json->'w1600'->>'chemin'),
                                      'order', coalesce(p.sort_order, 9999)::text,
                                      'legend', p.legend)
           order by p.visible desc nulls last, p.sort_order asc nulls last, p.id)
    from public.app_console_photo p join tmp_cibles c on c.app_dossier_id = p.app_dossier_id
   where p.present_in_hektor and p.visible is not false and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
   group by p.app_dossier_id;

  update public.app_dossier_current d set images_preview_json_app = g.entrees,
         photo_url_listing_app = g.entrees->0->>'url', adresses_app_le = quand
    from tmp_galerie g where g.app_dossier_id = d.app_dossier_id;
  get diagnostics n_viv = row_count;
  update public.app_archive_annonce_index_current a set photo_url_listing_app = pr.url,
         adresses_app_le = quand
    from tmp_principale pr where pr.app_dossier_id = a.app_archive_id;
  get diagnostics n_arc = row_count;
  update public.app_historical_annonce_index_current h set photo_url_listing_app = pr.url,
         adresses_app_le = quand
    from tmp_principale pr where pr.app_dossier_id = h.app_historical_id;
  get diagnostics n_his = row_count;
  update public.app_brouillon_annonce_index_current b set photo_url_listing_app = pr.url,
         adresses_app_le = quand
    from tmp_principale pr where pr.app_dossier_id = b.app_brouillon_id;
  get diagnostics n_bro = row_count;

  return jsonb_build_object('statut','ok','vivantes',vivantes,
    'cibles', (select count(*) from tmp_cibles), 'vivantes_remplies', n_viv,
    'archive', n_arc, 'historique', n_his, 'brouillon', n_bro,
    'vitrines_incoherentes', n_incoherents);
end; $function$;
