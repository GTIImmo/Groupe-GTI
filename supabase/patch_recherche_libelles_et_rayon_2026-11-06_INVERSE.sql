-- =====================================================================
-- RETOUR ARRIERE de patch_recherche_libelles_et_rayon_2026-11-06.sql
-- Il remet les TROIS fonctions dans leur version d'avant (relevee en base le
-- 06/11 au matin), rend aux recherches reparees leurs types sauvegardes (sauf si
-- elles ont change depuis), retire les deux aides, et met la table des rayons DE
-- COTE (renommee, jamais supprimee : un rayon saisi ne se perd pas).
-- =====================================================================

begin;

-- ── 1. LE MOTEUR, rayon fige a 15 km ─────────────────────────────────
CREATE OR REPLACE FUNCTION public.app_match_score_v2(p_search jsonb, p_dossier jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  -- C.15 lot B 27/08 : le type d'offre de la RECHERCHE et celui de l'ANNONCE.
  s_offre text := COALESCE(NULLIF(TRIM(p_search->>'offre'), ''), '0');
  d_offre text := COALESCE(NULLIF(TRIM(p_dossier->>'offre_type'), ''), '0');
  v_types  jsonb := COALESCE(p_search->'types_json','{}'::jsonb);
  v_villes jsonb := COALESCE(p_search->'villes_json','[]'::jsonb);
  v_prixmax  numeric := NULLIF(app_num(p_search->>'prix_max'),0);
  v_surfmin  numeric := NULLIF(app_num(p_search->>'surface_min'),0);
  v_terrmin  numeric := NULLIF(app_num(p_search->>'surface_terrain_min'),0);
  v_chmin    numeric := NULLIF(app_num(p_search->>'chambre_min'),0);
  d_garage boolean := FALSE; d_balter boolean := FALSE;
  d_type text := COALESCE(p_dossier->>'type_bien','');
  d_prix numeric := app_num(p_dossier->>'prix');
  d_cp   text := COALESCE(p_dossier->>'code_postal','');
  d_lat  numeric := app_num(p_dossier->>'lat');
  d_lng  numeric := app_num(p_dossier->>'lng');
  d_surf numeric := app_num(p_dossier->>'surface');
  d_terr numeric := app_num(p_dossier->>'surface_terrain');
  d_ch   numeric := app_num(p_dossier->>'nb_chambres');
  b_garage boolean := COALESCE((p_dossier->>'garage')::boolean,FALSE) OR COALESCE((p_dossier->>'parking')::boolean,FALSE);
  b_balter boolean := COALESCE((p_dossier->>'terrasse')::boolean,FALSE) OR COALESCE((p_dossier->>'balcon')::boolean,FALSE);
  grille text; w_prix numeric:=0; w_sect numeric:=0; w_surf numeric:=0;
  w_terr numeric:=0; w_ch numeric:=0; w_gar numeric:=0; w_balter numeric:=0;
  num numeric:=0; den numeric:=0; sub numeric; marge numeric;
  seuil numeric; dist numeric; excl numeric; shortfall numeric; sc int;
  score_cap int := 100;
  comp jsonb := '[]'::jsonb; flags jsonb := '[]'::jsonb; cps text[]; missing int := 0;
BEGIN
  -- C.15 lot B 27/08 -- PREMIER GARDE-FOU : on n'apparie que des types compatibles.
  -- Un local commercial ne se propose pas a quelqu'un qui cherche une maison, et
  -- inversement les 22 acquereurs qui cherchent du commercial ne doivent plus
  -- recevoir du residentiel. La regle compare les DEUX types, elle n'en code aucun
  -- en dur : le jour ou un acquereur cherchera de la location, ca marchera seul.
  -- INERTE tant que tout vaut '0' des deux cotes.
  IF s_offre <> d_offre THEN
    RETURN jsonb_build_object('score',0,'eligible',false,'grille','type_offre','components','[]'::jsonb);
  END IF;
  IF jsonb_typeof(v_types)='object' AND v_types <> '{}'::jsonb AND NOT (v_types ? d_type) THEN
    RETURN jsonb_build_object('score',0,'eligible',false,'grille',null,'components','[]'::jsonb);
  END IF;

  grille := CASE
    WHEN d_type IN ('1','10','11','17','22','25','27','28','30','39','49') THEN 'maison'
    WHEN d_type IN ('2','4','18','26','31','41','50') THEN 'appartement'
    WHEN d_type IN ('5','43','44','45') THEN 'terrain'
    WHEN d_type = '21' THEN 'immeuble'
    WHEN d_type IN ('15','16','29') THEN 'exclu'
    ELSE 'autre' END;
  IF grille='exclu' THEN
    RETURN jsonb_build_object('score',0,'eligible',false,'grille','exclu','components','[]'::jsonb);
  END IF;

  IF grille='maison' THEN w_prix:=23; w_sect:=23; w_surf:=15; w_terr:=15; w_ch:=15; w_gar:=9;
  ELSIF grille='appartement' THEN w_prix:=24; w_sect:=24; w_surf:=18; w_ch:=15; w_balter:=11; w_gar:=8;
  ELSIF grille='terrain' THEN w_sect:=40; w_prix:=30; w_terr:=30;
  ELSIF grille='immeuble' THEN w_sect:=50; w_prix:=50;
  ELSE w_prix:=50; w_sect:=50; END IF;

  d_garage := EXISTS (SELECT 1 FROM jsonb_array_elements(COALESCE(p_search->'criteres_json','[]'::jsonb)) c
                      WHERE c->>'cle'='ITEM_GARAGE_PARKING' AND upper(c->>'valeur')='OUI');
  d_balter := EXISTS (SELECT 1 FROM jsonb_array_elements(COALESCE(p_search->'criteres_json','[]'::jsonb)) c
                      WHERE c->>'cle' IN ('ITEM_TERRASSE','ITEM_BALCON') AND upper(c->>'valeur')='OUI');

  -- PRIX
  IF w_prix>0 AND v_prixmax IS NOT NULL THEN
    IF d_prix IS NULL THEN
      comp := comp || jsonb_build_object('k','Budget','ok',true,'v','à compléter');
    ELSE
      IF d_prix <= v_prixmax THEN
        sub := 1;
        IF d_prix < 0.45*v_prixmax THEN flags := flags || to_jsonb('prix très bas, à vérifier'::text); END IF;
        comp := comp || jsonb_build_object('k','Budget','ok',true,'v','100 %');
      ELSE
        marge := app_num((SELECT c->>'valeur' FROM jsonb_array_elements(COALESCE(p_search->'criteres_json','[]'::jsonb)) c WHERE c->>'cle'='ITEM_PRIX_MARGE' LIMIT 1));
        IF marge IS NULL THEN marge := CASE WHEN v_prixmax<=150000 THEN 10 WHEN v_prixmax<=300000 THEN 8 WHEN v_prixmax<=500000 THEN 6 ELSE 5 END; END IF;
        seuil := v_prixmax*(1+marge/100);
        IF d_prix > seuil THEN
          RETURN jsonb_build_object('score',0,'eligible',false,'grille',grille,
            'components', comp || jsonb_build_object('k','Budget','ok',false,'v','Hors budget'));
        END IF;
        sub := 1 - (d_prix - v_prixmax)/(seuil - v_prixmax);
        comp := comp || jsonb_build_object('k','Budget','ok',true,'v',round(sub*100)::text||' %');
      END IF;
      num := num + w_prix*sub; den := den + w_prix;
    END IF;
  END IF;

  -- SECTEUR (durci : courbe distance + plafond global 55 % si hors zone)
  IF w_sect>0 AND jsonb_typeof(v_villes)='array' AND jsonb_array_length(v_villes)>0 THEN
    SELECT array_agg(substring(x.v from '[0-9]{5}')) INTO cps FROM jsonb_array_elements_text(v_villes) AS x(v);
    IF d_cp = ANY(COALESCE(cps,'{}'::text[])) THEN
      sub := 1; comp := comp || jsonb_build_object('k','Secteur','ok',true,'v','Commune exacte');
    ELSIF d_lat IS NOT NULL AND d_lng IS NOT NULL THEN
      SELECT min(app_haversine(d_lat,d_lng,r.latitude,r.longitude)) INTO dist FROM ref_commune_geo r WHERE r.code_postal = ANY(cps);
      IF dist IS NULL THEN
        sub := 0; score_cap := least(score_cap, 55);
        comp := comp || jsonb_build_object('k','Secteur','ok',false,'v','Hors zone connue');
      ELSIF dist >= 15 THEN
        sub := 0; score_cap := least(score_cap, 55);
        comp := comp || jsonb_build_object('k','Secteur','ok',false,'v','à '||round(dist)::text||' km');
      ELSE
        sub := CASE
          WHEN dist<=3  THEN 0.90 - 0.20*(dist/3)
          WHEN dist<=7  THEN 0.70 - 0.35*((dist-3)/4)
          WHEN dist<=12 THEN 0.35 - 0.25*((dist-7)/5)
          ELSE              0.10 - 0.10*((dist-12)/3)
        END;
        comp := comp || jsonb_build_object('k','Secteur','ok',sub>=0.5,'v','à '||round(dist)::text||' km');
      END IF;
    ELSE
      sub := 0; score_cap := least(score_cap, 55);
      comp := comp || jsonb_build_object('k','Secteur','ok',false,'v','Sans géolocalisation');
    END IF;
    num := num + w_sect*sub; den := den + w_sect;
  END IF;

  -- SURFACE HABITABLE (seuil d'exclusion resserré : maison -20..-30 %, appart -15..-25 %)
  IF w_surf>0 AND v_surfmin IS NOT NULL THEN
    IF d_surf IS NULL THEN
      comp := comp || jsonb_build_object('k','Surface','ok',true,'v','à compléter');
    ELSE
      excl := CASE grille
        WHEN 'maison' THEN 0.20 + 0.10*least(1,greatest(0,(v_surfmin-70)/80.0))
        WHEN 'appartement' THEN 0.15 + 0.10*least(1,greatest(0,(v_surfmin-45)/50.0))
        ELSE 0.40 END;
      IF d_surf >= v_surfmin THEN
        sub := 1; comp := comp || jsonb_build_object('k','Surface','ok',true,'v','100 %');
      ELSE
        shortfall := (v_surfmin - d_surf)/v_surfmin;
        IF shortfall >= excl THEN
          RETURN jsonb_build_object('score',0,'eligible',false,'grille',grille,
            'components', comp || jsonb_build_object('k','Surface','ok',false,'v','Trop petit'));
        END IF;
        sub := 1 - shortfall/excl;
        comp := comp || jsonb_build_object('k','Surface','ok',sub>=0.5,'v',round(sub*100)::text||' %');
      END IF;
      num := num + w_surf*sub; den := den + w_surf;
    END IF;
  END IF;

  -- SURFACE TERRAIN
  IF w_terr>0 AND v_terrmin IS NOT NULL THEN
    IF d_terr IS NULL THEN
      comp := comp || jsonb_build_object('k','Terrain','ok',true,'v','à compléter');
    ELSE
      shortfall := greatest(0,(v_terrmin - d_terr)/v_terrmin);
      sub := CASE
        WHEN shortfall<=0   THEN 1
        WHEN shortfall<=0.3 THEN 1 - 0.15*(shortfall/0.3)
        WHEN shortfall<=0.6 THEN 0.85 - 0.35*((shortfall-0.3)/0.3)
        WHEN shortfall<=0.8 THEN 0.50 - 0.30*((shortfall-0.6)/0.2)
        ELSE greatest(0, 0.20*(1-(shortfall-0.8)/0.2)) END;
      num := num + w_terr*sub; den := den + w_terr;
      comp := comp || jsonb_build_object('k','Terrain','ok',sub>=0.5,'v',round(sub*100)::text||' %');
    END IF;
  END IF;

  -- CHAMBRES
  IF w_ch>0 AND v_chmin IS NOT NULL THEN
    IF d_ch IS NULL THEN
      comp := comp || jsonb_build_object('k','Chambres','ok',true,'v','à compléter');
    ELSE
      sub := CASE WHEN d_ch >= v_chmin THEN 1 ELSE 0 END;
      num := num + w_ch*sub; den := den + w_ch;
      comp := comp || jsonb_build_object('k','Chambres','ok',sub=1,'v',CASE WHEN sub=1 THEN '100 %' ELSE 'Insuffisant' END);
    END IF;
  END IF;

  -- GARAGE / PARKING
  IF w_gar>0 AND d_garage THEN
    sub := CASE WHEN b_garage THEN 1 ELSE 0 END;
    num := num + w_gar*sub; den := den + w_gar;
    comp := comp || jsonb_build_object('k','Garage','ok',sub=1,'v',CASE WHEN sub=1 THEN 'Oui' ELSE 'Non' END);
  END IF;

  -- BALCON / TERRASSE
  IF w_balter>0 AND d_balter THEN
    sub := CASE WHEN b_balter THEN 1 ELSE 0 END;
    num := num + w_balter*sub; den := den + w_balter;
    comp := comp || jsonb_build_object('k','Balcon/Terrasse','ok',sub=1,'v',CASE WHEN sub=1 THEN 'Oui' ELSE 'Non' END);
  END IF;

  IF den = 0 THEN sc := 30; ELSE sc := round(num/den*100); END IF;

  sc := least(sc, score_cap);

  IF v_prixmax IS NULL THEN missing := missing + 1; END IF;
  IF NOT (jsonb_typeof(v_villes)='array' AND jsonb_array_length(v_villes)>0) THEN missing := missing + 1; END IF;
  IF missing = 1 THEN sc := least(sc,55); ELSIF missing >= 2 THEN sc := least(sc,40); END IF;

  RETURN jsonb_build_object('score',sc,'eligible',true,'grille',grille,'components',comp,'flags',flags);
END $function$;

-- ── 2. LA PORTE DE L'APP, version d'avant ────────────────────────────
CREATE OR REPLACE FUNCTION public.app_edit_search_optimistic(target_contact_id text, search_payload jsonb, debounce_seconds integer DEFAULT 600)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare clean_id text; existing_contact public.app_contact_current%rowtype;
        target_email text; target_user_id text; v_index int; v_search jsonb;
        cur public.app_contact_search_current%rowtype; v_types jsonb; v_villes jsonb; v_base jsonb;
begin
  clean_id := nullif(trim(coalesce(target_contact_id,'')),'');
  if clean_id is null or clean_id !~ '^[0-9]+$' then raise exception 'invalid_contact_id' using errcode='22023'; end if;
  v_search := case when jsonb_typeof(search_payload->'search')='object' then search_payload->'search' else search_payload end;
  v_index := coalesce((search_payload->>'search_index')::int,(search_payload->>'searchIndex')::int,0);
  if nullif(trim(coalesce(v_search->>'priceMax',v_search->>'prix_max','')),'') is null then raise exception 'missing_search_price_max' using errcode='22023'; end if;

  select * into existing_contact from public.app_contact_current where hektor_contact_id=clean_id limit 1;
  if existing_contact.hektor_contact_id is null then raise exception 'contact_not_found' using errcode='22023'; end if;
  select r.target_email, r.target_user_id into target_email, target_user_id
    from public.app_console_resolve_contact_hektor_user(existing_contact,
      coalesce(search_payload->>'hektor_user_email',search_payload->>'target_hektor_user_email'),
      coalesce(search_payload->>'hektor_user_id',search_payload->>'target_hektor_user_id')) r;
  if not public.app_console_can_request_contact_job('update_hektor_contact_search', clean_id, target_email) then
    raise exception 'forbidden_update_contact_search' using errcode='42501'; end if;

  select * into cur from public.app_contact_search_current where hektor_contact_id=clean_id and search_index=v_index limit 1;
  if cur.contact_search_key is null then raise exception 'search_not_found' using errcode='22023'; end if;

  v_types := coalesce((select jsonb_object_agg(t,t) from jsonb_array_elements_text(v_search->'propertyTypeIds') t), cur.types_json);
  v_villes := coalesce((select jsonb_agg(trim(coalesce(l->>'city','')||' '||coalesce(l->>'postalCode','')))
                        from jsonb_array_elements(v_search->'localities') l
                        where coalesce(l->>'city','')<>'' or coalesce(l->>'postalCode','')<>''), cur.villes_json);

  if exists (select 1 from public.app_search_pending p where p.hektor_contact_id=clean_id and p.search_index=v_index)
    then select base_snapshot into v_base from public.app_search_pending where hektor_contact_id=clean_id and search_index=v_index;
    else v_base := jsonb_build_object('offre',cur.offre,'types_json',cur.types_json,'villes_json',cur.villes_json,
           'surface_terrain_min',cur.surface_terrain_min,'criteres_json',cur.criteres_json,'prix_min',cur.prix_min,
           'prix_max',cur.prix_max,'surface_min',cur.surface_min,'pieces_min',cur.pieces_min,'chambre_min',cur.chambre_min);
  end if;

  update public.app_contact_search_current set
    offre=coalesce(nullif(v_search->>'offerCode',''),offre), types_json=v_types, villes_json=v_villes,
    -- 30/08 : FUSION, plus remplacement. Voir app_search_criteres_fusion.
    criteres_json=public.app_search_criteres_fusion(cur.criteres_json, v_search),
    prix_min=coalesce(nullif(v_search->>'priceMin',''),prix_min), prix_max=nullif(v_search->>'priceMax',''),
    surface_min=nullif(v_search->>'surfaceMin',''), pieces_min=nullif(v_search->>'roomsMin',''),
    chambre_min=nullif(v_search->>'bedroomsMin',''), surface_terrain_min=nullif(v_search->>'landSurfaceMin',''),
    refreshed_at=now()
  where hektor_contact_id=clean_id and search_index=v_index;

  perform public.app_refresh_rapprochements_for_search(cur.contact_search_key);

  insert into public.app_search_pending(hektor_contact_id,search_index,app_contact_id,base_snapshot,push_search,push_after,source,dirty_by)
  values (clean_id,v_index,(select app_contact_id from public.app_contact_current where hektor_contact_id = clean_id),v_base, null /* C.3 24/08 : plus d'envoi vers Hektor */, now()+make_interval(secs=>greatest(debounce_seconds,30)),'nego_app',auth.uid()::text)
  on conflict (hektor_contact_id,search_index) do update set
    app_contact_id=coalesce(app_search_pending.app_contact_id,excluded.app_contact_id),
    push_search=excluded.push_search, push_after=now()+make_interval(secs=>greatest(debounce_seconds,30)),
    push_job_id=null, conflict=false, push_attempts=0, updated_at=now();

  return jsonb_build_object('ok',true,'contact_id',clean_id,'search_index',v_index,
    'app_contact_id',(select app_contact_id from public.app_contact_current where hektor_contact_id = clean_id));
end; $function$;

-- ── 3. LA PORTE DE L'ESPACE CLIENT, version d'avant ──────────────────
CREATE OR REPLACE FUNCTION public.app_espace_edit_search_optimistic(target_contact_id text, search_payload jsonb, debounce_seconds integer DEFAULT 600)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare clean_id text; cur public.app_contact_search_current%rowtype;
        v_index int; v_search jsonb; v_types jsonb; v_villes jsonb; v_base jsonb;
begin
  clean_id := nullif(trim(coalesce(target_contact_id,'')),'');
  if clean_id is null or clean_id !~ '^[0-9]+$' then raise exception 'invalid_contact_id' using errcode='22023'; end if;
  v_search := case when jsonb_typeof(search_payload->'search')='object' then search_payload->'search' else search_payload end;
  v_index := coalesce((search_payload->>'search_index')::int,(search_payload->>'searchIndex')::int,0);
  if nullif(trim(coalesce(v_search->>'priceMax',v_search->>'prix_max','')),'') is null then raise exception 'missing_search_price_max' using errcode='22023'; end if;

  select * into cur from public.app_contact_search_current where hektor_contact_id=clean_id and search_index=v_index limit 1;
  if cur.contact_search_key is null then raise exception 'search_not_found' using errcode='22023'; end if;

  v_types := coalesce((select jsonb_object_agg(t,t) from jsonb_array_elements_text(v_search->'propertyTypeIds') t), cur.types_json);
  v_villes := coalesce((select jsonb_agg(trim(coalesce(l->>'city','')||' '||coalesce(l->>'postalCode','')))
                        from jsonb_array_elements(v_search->'localities') l
                        where coalesce(l->>'city','')<>'' or coalesce(l->>'postalCode','')<>''), cur.villes_json);

  if exists (select 1 from public.app_search_pending p where p.hektor_contact_id=clean_id and p.search_index=v_index)
    then select base_snapshot into v_base from public.app_search_pending where hektor_contact_id=clean_id and search_index=v_index;
    else v_base := jsonb_build_object('offre',cur.offre,'types_json',cur.types_json,'villes_json',cur.villes_json,
           'surface_terrain_min',cur.surface_terrain_min,'criteres_json',cur.criteres_json,'prix_min',cur.prix_min,
           'prix_max',cur.prix_max,'surface_min',cur.surface_min,'pieces_min',cur.pieces_min,'chambre_min',cur.chambre_min);
  end if;

  update public.app_contact_search_current set
    offre=coalesce(nullif(v_search->>'offerCode',''),offre), types_json=v_types, villes_json=v_villes,
    -- 30/08 : FUSION, plus remplacement. Voir app_search_criteres_fusion.
    criteres_json=public.app_search_criteres_fusion(cur.criteres_json, v_search),
    prix_min=coalesce(nullif(v_search->>'priceMin',''),prix_min), prix_max=nullif(v_search->>'priceMax',''),
    surface_min=nullif(v_search->>'surfaceMin',''), pieces_min=nullif(v_search->>'roomsMin',''),
    chambre_min=nullif(v_search->>'bedroomsMin',''), surface_terrain_min=nullif(v_search->>'landSurfaceMin',''),
    refreshed_at=now()
  where hektor_contact_id=clean_id and search_index=v_index;

  perform public.app_refresh_rapprochements_for_search(cur.contact_search_key);

  insert into public.app_search_pending(hektor_contact_id,search_index,app_contact_id,base_snapshot,push_search,push_after,source,dirty_by)
  values (clean_id,v_index,(select app_contact_id from public.app_contact_current where hektor_contact_id = clean_id),v_base, null /* C.3 24/08 : plus d'envoi vers Hektor */, now()+make_interval(secs=>greatest(debounce_seconds,30)),'espace_client',
          nullif(search_payload->>'dirty_by',''))
  on conflict (hektor_contact_id,search_index) do update set
    app_contact_id=coalesce(app_search_pending.app_contact_id,excluded.app_contact_id),
    push_search=excluded.push_search, push_after=now()+make_interval(secs=>greatest(debounce_seconds,30)),
    push_job_id=null, conflict=false, push_attempts=0, updated_at=now();

  return jsonb_build_object('ok',true,'contact_id',clean_id,'search_index',v_index,
    'app_contact_id',(select app_contact_id from public.app_contact_current where hektor_contact_id = clean_id));
end; $function$;

-- ── 4. LES RECHERCHES REPAREES : leurs types d'avant, sauf si elles ont change depuis ──
update public.app_contact_search_current s
   set types_json = b.types_json
  from public.app_contact_search_types_avant_libelles_20261106 b
 where s.contact_search_key = b.contact_search_key
   and (select jsonb_agg(k order by k) from jsonb_object_keys(s.types_json) k)
     = (select jsonb_agg(k order by k) from jsonb_object_keys(b.types_json) k);

-- ── 5. LES AIDES, ET LA TABLE DES RAYONS MISE DE COTE ────────────────
drop function if exists public.app_search_rayon_km(jsonb);
drop function if exists public.app_search_types_libelles(jsonb, jsonb, jsonb);
alter table if exists public.app_search_rayon rename to app_search_rayon_retire_20261106;

-- Un retour arriere ne juge que SA part : il ne doit rester aucune trace active.
do $verif$
begin
  if exists (select 1 from pg_proc where proname in ('app_search_rayon_km','app_search_types_libelles')) then
    raise exception 'INVERSE INCOMPLET : une aide est restee';
  end if;
  if exists (select 1 from pg_class where relname = 'app_search_rayon') then
    raise exception 'INVERSE INCOMPLET : la table des rayons est encore active';
  end if;
  if pg_get_functiondef('public.app_match_score_v2(jsonb,jsonb)'::regprocedure) ~ 'app_search_rayon_km' then
    raise exception 'INVERSE INCOMPLET : le moteur lit encore le rayon';
  end if;
end $verif$;

commit;
