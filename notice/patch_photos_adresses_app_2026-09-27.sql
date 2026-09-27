-- ============================================================================
-- G.15-d -- FAIRE LIRE LES PHOTOS CHEZ NOUS                         27/09/2026
--
-- Ce que ce fichier contient, et POURQUOI il existe : les objets ci-dessous ont ete
-- crees DIRECTEMENT EN BASE. Le depot n'en gardait aucune trace, alors que le reste du
-- chantier (worker, scripts, front) y est versionne. On les consigne donc ici, comme
-- notice/patch_ancre_six_mois_2026-09-26.sql l'a fait pour l'ancre des six mois.
--
-- ⚠ LA REFERENCE RESTE LA BASE. Ce fichier est une COPIE de lecture : si un jour il
--   diverge, c'est pg_get_functiondef / pg_get_viewdef qui dit la verite, pas lui.
--
-- Il est rejouable tel quel (tout est CREATE OR REPLACE), et il ne supprime rien.
--
-- ORDRE DES CHOSES : 1) les deux fonctions de remplissage, 2) les deux vues recouvertes,
-- 3) la RPC de rapprochement. Les vues dependent des colonnes soeurs, qui sont posees
-- par le patch du 26/09 (G.15-b) -- pas ici.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1) LES QUATRE INDEX -- app_photos_remplir_adresses_app
--
-- Appelee par Console/remplir_adresses_photos.js, lui-meme appele par l'etape
-- « phase2 adresses photos » du run (run_full_pipeline.ps1, l. 1140).
--
-- ⚠ L'ETAPE DOIT RESTER APRES LE PUSH (l. 943) : le push vide et reinsere les index,
--   donc une annonce neuve arrive sans adresse. C'est cet ordre qui la remplit le matin
--   meme, au lieu de la laisser une journee entiere sur Hektor.
-- ⚠ LE GARDE-FOU EST ICI, PAS DANS LE SCRIPT : si app_dossier_current passe sous 5 000
--   lignes (un push casse), la fonction REFUSE. Sans lui, un run rate VIDERAIT les
--   adresses de tout le parc et l'app retomberait entierement sur Hektor.
-- ----------------------------------------------------------------------------
create or replace function public.app_photos_remplir_adresses_app(
  p_heures integer default 48, p_tout boolean default false)
returns jsonb language plpgsql security definer set search_path = public as $$
declare
  base constant text := 'https://dwaqxfrinihnychuoptk.supabase.co/storage/v1/object/public/gti-photo/';
  vivantes bigint; quand timestamptz := now();
  n_viv bigint := 0; n_arc bigint := 0; n_his bigint := 0; n_bro bigint := 0;
begin
  select count(*) into vivantes from public.app_dossier_current;
  if vivantes < 5000 then
    return jsonb_build_object('statut','refus',
      'raison','app_dossier_current sous le plancher : le run de nuit a probablement echoue',
      'vivantes', vivantes);
  end if;

  create temporary table tmp_maj on commit drop as
  select p.app_dossier_id, max(p.derives_generes_le) as dernier
    from public.app_console_photo p
   where p_tout or p.derives_generes_le >= quand - make_interval(hours => greatest(1, p_heures))
   group by p.app_dossier_id;

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
  ) s where x is not null;

  create temporary table tmp_principale (app_dossier_id bigint primary key, url text) on commit drop;
  insert into tmp_principale (app_dossier_id, url)
  select distinct on (p.app_dossier_id) p.app_dossier_id, base || (p.derives_json->'w400'->>'chemin')
    from public.app_console_photo p join tmp_cibles c on c.app_dossier_id = p.app_dossier_id
   where p.present_in_hektor and p.derives_json ? 'w400'
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
   where p.present_in_hektor and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
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
    'archive', n_arc, 'historique', n_his, 'brouillon', n_bro);
end; $$;

grant execute on function public.app_photos_remplir_adresses_app(integer, boolean) to service_role;


-- ----------------------------------------------------------------------------
-- 2) LE REGISTRE -- app_photos_remplir_adresses_registre
--
-- Il ne CALCULE rien : il RECOPIE ce que les index savent deja.
--
-- ⚠⚠ IL SE JOINT PAR hektor_annonce_id, PAS PAR app_dossier_id.
--    Mesure du 27/09 : l'app_dossier_id du registre descend a -281 472 776 635 305 --
--    c'est un hache synthetique. Seules 746 lignes sur 23 840 portent un vrai numero
--    d'app (celles deja passees par la bascule d'identite). Joindre par lui ne touchait
--    que 3 % du registre, SANS AUCUNE ERREUR VISIBLE : juste 97 % de vide.
--    Verifie : sur les 746 ou les deux raccordements aboutissent, le numero Hektor
--    CONCORDE (0 divergence) -- rien n'avait ete mal pose.
--    ➡ hors photos : le registre ne porte pas encore de vrai numero d'app. C'est un trou
--      du chantier IDENTITE (L9), a traiter la-bas.
-- ⚠ POURQUOI UNE FONCTION A PART : en faire une cible de la fonction 1) faisait
--   recalculer la photo principale de 23 800 annonces CHAQUE NUIT (le push vide puis
--   reinsere le registre, donc ses lignes reviennent toujours sans adresse). PostgREST
--   expirait a 8 s (57014). Pilote par le registre, c'est 0,4 s.
-- ⚠ PAS D'AGREGAT SUR DU jsonb : max(jsonb) n'existe pas en Postgres (42883, paye le
--   27/09). La galerie n'existe que pour les vivantes -> un simple join.
-- ⚠ hektor_annonce_id n'a AUCUN doublon dans les 4 index (mesure du 27/09), mais la
--   regle du projet interdit d'en faire une contrainte UNIQUE : le jour ou un doublon
--   apparaitrait, ce join deviendrait non deterministe.
-- ----------------------------------------------------------------------------
create or replace function public.app_photos_remplir_adresses_registre()
returns jsonb language plpgsql security definer set search_path = public as $$
declare vivantes bigint; n_url bigint := 0; n_gal bigint := 0;
begin
  select count(*) into vivantes from public.app_dossier_current;
  if vivantes < 5000 then
    return jsonb_build_object('statut','refus',
      'raison','app_dossier_current sous le plancher', 'vivantes', vivantes);
  end if;

  -- L'ordre du coalesce est l'ordre de fraicheur : vivante > archive > historique > brouillon.
  update public.app_mandat_register_current r set photo_url_listing_app = k.url
    from (select r2.hektor_annonce_id,
                 coalesce(d.photo_url_listing_app, a.photo_url_listing_app,
                          h.photo_url_listing_app, b.photo_url_listing_app) as url
            from (select distinct hektor_annonce_id from public.app_mandat_register_current
                   where hektor_annonce_id is not null) r2
            left join public.app_dossier_current d on d.hektor_annonce_id = r2.hektor_annonce_id
            left join public.app_archive_annonce_index_current a on a.hektor_annonce_id = r2.hektor_annonce_id
            left join public.app_historical_annonce_index_current h on h.hektor_annonce_id = r2.hektor_annonce_id
            left join public.app_brouillon_annonce_index_current b on b.hektor_annonce_id = r2.hektor_annonce_id) k
   where k.hektor_annonce_id = r.hektor_annonce_id
     and k.url is not null
     and r.photo_url_listing_app is distinct from k.url;
  get diagnostics n_url = row_count;

  update public.app_mandat_register_current r
     set images_preview_json_app = d.images_preview_json_app
    from public.app_dossier_current d
   where d.hektor_annonce_id = r.hektor_annonce_id
     and d.images_preview_json_app is not null
     and r.images_preview_json_app is distinct from d.images_preview_json_app;
  get diagnostics n_gal = row_count;

  return jsonb_build_object('statut','ok','vignettes',n_url,'galeries',n_gal);
end; $$;

grant execute on function public.app_photos_remplir_adresses_registre() to service_role;


-- ----------------------------------------------------------------------------
-- 3) LES DEUX VUES RECOUVERTES -- autorise par Frederic le 27/09
--
-- Elles rendent NOS adresses sous les noms que tout le monde lit deja
-- (photo_url_listing, images_preview_json), et exposent celles de Hektor a cote sous
-- _hektor. Un seul endroit, donc aucun angle mort : le front, le backend (RDV, emails,
-- espace client) et toute RPC lisant ces vues en profitent ensemble.
--
-- ⚠ C'EST UN CHANGEMENT DE SENS, ASSUME : un lecteur qui croit lire Hektor lit
--   maintenant nos adresses. Rien n'est perdu, mais une comparaison ecrite avant le
--   27/09 verrait un faux changement.
-- ⚠ LE TYPE NE CHANGE PAS : images_preview_json est du TEXTE, la colonne soeur est du
--   jsonb -> ::text obligatoire. Sans le cast, CREATE OR REPLACE refuse (on ne peut pas
--   changer le type d'une colonne existante), et le front recevrait un objet la ou il
--   attend une chaine : galerie VIDE, sans aucune erreur.
-- ⚠ LES COLONNES NEUVES VONT A LA FIN : CREATE OR REPLACE VIEW n'accepte d'ajout qu'en
--   queue, et les inserer ailleurs decalerait tous les lecteurs.
-- ⚠ AUCUN SCRIPT NE RECREE CES VUES (verifie le 27/09 sur phase2/, backend/, Console/)
--   et le front n'y ecrit jamais. Si un jour un script les recreait, le recouvrement
--   sauterait EN SILENCE et les photos repasseraient chez Hektor.
-- ----------------------------------------------------------------------------
create or replace view public.app_dossiers_current as
 SELECT app_dossier_id, hektor_annonce_id, archive, diffusable, adresse_privee_listing,
    adresse_detail, code_postal, code_postal_prive_detail, ville_privee_detail,
    nb_portails_actifs, has_diffusion_error, portails_resume, offre_id, offre_state,
    compromis_id, compromis_state, vente_id, numero_dossier, numero_mandat, titre_bien,
    ville, type_bien, prix, commercial_id, commercial_nom, negociateur_email, agence_nom,
    statut_annonce,
    coalesce(nullif(btrim(d.photo_url_listing_app), ''), d.photo_url_listing) as photo_url_listing,
    coalesce(d.images_preview_json_app::text, d.images_preview_json) as images_preview_json,
    validation_diffusion_state, mandat_type, mandat_type_source, mandat_date_debut,
    mandat_date_fin, mandat_montant, mandants_texte, price_change_event_count,
    price_change_last_source_kind, price_change_last_old_value, price_change_last_new_value,
    price_change_last_detected_at, price_change_last_source_updated_at, etat_visibilite,
    alerte_principale, priority, has_open_blocker, commentaire_resume, date_relance_prevue,
    dernier_event_type, dernier_work_status, offre_last_proposition_type, search_text,
    date_enregistrement_annonce, offre_type, commerce_sous_type, commerce_famille,
    commerce_activite, commerce_loyer, commerce_charges, commerce_taxe_fonciere,
    commerce_bail_duree, commerce_bail_echeance, commerce_etat, commerce_zone, commerce_json,
    photo_url_listing_app, images_preview_json_app,
    d.photo_url_listing as photo_url_listing_hektor,
    d.images_preview_json as images_preview_json_hektor
   FROM app_dossier_current d;

create or replace view public.app_registre_mandats_current as
 SELECT register_row_id, app_dossier_id, hektor_annonce_id,
    coalesce(nullif(btrim(r.photo_url_listing_app), ''), r.photo_url_listing) as photo_url_listing,
    coalesce(r.images_preview_json_app::text, r.images_preview_json) as images_preview_json,
    adresse_privee_listing, adresse_detail, code_postal, code_postal_prive_detail,
    ville_privee_detail, archive, diffusable, nb_portails_actifs, has_diffusion_error,
    portails_resume, numero_dossier, numero_mandat, titre_bien, ville, type_bien, prix,
    commercial_id, commercial_nom, negociateur_email, agence_nom, statut_annonce,
    validation_diffusion_state, mandat_source_id, mandat_numero_reference, mandat_type,
    mandat_type_source, mandat_date_debut, mandat_date_fin, mandat_montant, mandants_texte,
    mandat_note, priority, offre_id, offre_state, offre_last_proposition_type, compromis_id,
    compromis_state, vente_id, source_updated_at, register_source_kind,
    register_detail_available, register_version_count, register_embedded_avenant_count,
    register_history_json, register_avenants_json, register_detail_payload_json, source_hash,
    refreshed_at, register_sort_num, register_sort_group, price_change_event_count,
    price_change_last_source_kind, price_change_last_old_value, price_change_last_new_value,
    price_change_last_detected_at, price_change_last_source_updated_at, mandat_date_cloture,
    search_text, affaires_detail_json, commerce_sous_type, offre_type,
    photo_url_listing_app, images_preview_json_app,
    r.photo_url_listing as photo_url_listing_hektor,
    r.images_preview_json as images_preview_json_hektor
   FROM app_mandat_register_current r;


-- ----------------------------------------------------------------------------
-- 4) LA RPC DE L'ECRAN RECHERCHE ACQUEREUR -- app_get_rapprochements
--
-- Un seul changement par rapport a sa version du 27/09 au matin : la colonne photo_url.
--
-- ⚠ ELLE LIT LA TABLE app_dossier_current, PAS LA VUE : le recouvrement du point 3) ne
--   l'atteint donc pas. C'est la SEULE RPC dans ce cas -- verifie sur les 4 fonctions
--   qui mentionnent une adresse de photo.
-- ⚠ CREATE OR REPLACE, JAMAIS DROP : un DROP effacerait les GRANT, qui ne sont pas
--   uniformes dans ce projet (memoire renommer-parametre-rpc-supabase-piege).
--   Verifie apres coup : anon, authenticated, service_role, postgres, PUBLIC intacts.
-- ⚠ ELLE A UN EFFET DE BORD : si elle se croit perimee, elle enfile un recalcul dans
--   app_rapprochement_dirty. Pour l'essayer sans cet effet, l'appeler avec un
--   p_max_age_minutes enorme.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.app_get_rapprochements(p_search_key text, p_max_age_minutes integer DEFAULT 1440)
 RETURNS TABLE(app_dossier_id bigint, hektor_annonce_id bigint, numero_mandat text, numero_dossier text, type_code text, ville text, title text, prix numeric, surface numeric, nb_pieces numeric, nb_chambres numeric, surface_terrain numeric, equipements text[], prix_old numeric, photo_url text, negociateur_email text, score integer, components jsonb, first_seen_at timestamp with time zone, computed_at timestamp with time zone)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE last_at timestamptz;
BEGIN
  -- Fraicheur lue sur le marqueur (existe meme quand 0 match) -> pas de re-enfilage en boucle.
  SELECT st.computed_at INTO last_at FROM app_rapprochement_search_state st
   WHERE st.contact_search_key = p_search_key;

  IF last_at IS NULL OR last_at < now() - make_interval(mins => p_max_age_minutes) THEN
    INSERT INTO app_rapprochement_dirty(entity_type, entity_id, reason)
    SELECT 'search', p_search_key, 'changed'
    WHERE NOT EXISTS (SELECT 1 FROM app_rapprochement_dirty d
                      WHERE d.entity_type='search' AND d.entity_id = p_search_key);
  END IF;

  RETURN QUERY
  SELECT r.app_dossier_id, d.hektor_annonce_id, d.numero_mandat, d.numero_dossier,
         d.type_bien, d.ville, d.titre_bien, d.prix,
         app_num(dd.detail_payload_json::jsonb->>'surface'),
         app_num(dd.detail_payload_json::jsonb->>'nb_pieces'),
         app_num(dd.detail_payload_json::jsonb->>'nb_chambres'),
         app_num(dd.detail_payload_json::jsonb->>'surface_terrain_detail'),
         app_dossier_equipements(r.app_dossier_id),
         CASE WHEN d.price_change_last_new_value < d.price_change_last_old_value
              THEN d.price_change_last_old_value END,
         -- G.15-d (27/09/2026) : NOTRE adresse d'abord, celle de Hektor en repli.
         coalesce(nullif(btrim(d.photo_url_listing_app), ''), d.photo_url_listing),
         d.negociateur_email,
         r.score, r.score_components, r.first_seen_at, r.computed_at
  FROM app_rapprochement r
  JOIN app_dossier_current d        ON d.app_dossier_id  = r.app_dossier_id
  LEFT JOIN app_dossier_detail_current dd ON dd.app_dossier_id = r.app_dossier_id
  WHERE r.contact_search_key = p_search_key AND r.eligible = true
    -- Garde-fou d'affichage : ne montrer QUE les biens encore proposables, meme si la
    -- ligne eligible=true n'a pas encore ete recalculee (fenetre jusqu'a 24h). Aligne
    -- l'affichage sur la regle du moteur app_upsert_one_rapprochement (Actif + diffusable).
    AND d.statut_annonce = 'Actif' AND d.diffusable = '1'
  ORDER BY r.score DESC, d.prix ASC;
END $function$;


-- ============================================================================
-- CE QU'ON A MESURE APRES, LE 27/09
--
--   vue vivantes   70 colonnes · 13 439 lignes · 13 439 vignettes chez nous · 0 Hektor
--                  10 217 galeries chez nous · 0 galerie mal formee
--   vue registre   70 colonnes · 23 840 lignes · 23 840 vignettes chez nous · 0 Hektor
--   la RPC         7 biens rendus, 7 photos chez nous, 0 Hektor · GRANT intacts
--
--   LE REPLI S'EXERCE-T-IL ? Oui, sur 3 222 annonces vivantes sans notre galerie.
--   Verifie : leur galerie Hektor vaut [{"url":null,"full":null,"legend":null,"order":null}]
--   -- une seule entree entierement vide. Ces annonces n'ont AUCUNE photo, ni chez nous
--   ni chez Hektor, et l'ecran filtre deja les entrees sans adresse. Comportement
--   identique avant et apres.
--
-- ⚠⚠ PIEGE DE MESURE, A NE PAS RE-CORRIGER : un HEAD sur une adresse du coffre annonce
--    cache-control: no-cache. Un GET annonce max-age=31536000, et
--    storage.objects.metadata->>'cacheControl' vaut max-age=31536000. LE CACHE VA BIEN
--    -- c'est le HEAD qui ment. J'ai cru a une regression facturable sur 149 163
--    fichiers et teste trois canaux de depot pour rien.
-- ============================================================================
