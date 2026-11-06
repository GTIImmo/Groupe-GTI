-- =====================================================================
-- RECHERCHES : LES LIBELLES DES TYPES, ET UN RAYON QUI COMPTE VRAIMENT
-- Date : 2026-11-06 -- demande de Frederic : « oui corrige et B rendre le rayon reel »
--
-- DEFAUT 1 -- LA NATURE EN CHIFFRES. Une recherche descendue de Hektor range ses
--   types en { code : libelle } -- {"1":"Maison","2":"Appartement"} (4 250
--   recherches actives sur 4 279 au 06/11). Les deux portes de MODIFICATION
--   (app_edit_search_optimistic et sa soeur de l'espace client) ecrivaient
--   jsonb_object_agg(t,t) : {"1":"1"}. Les ecrans (bloc recherche de la fiche
--   contact, page rapprochement) n'ont plus de libelle et montrent le code.
--   Le rapprochement n'en souffrait pas : app_match_score_v2 compare les CLES.
--   Victimes au 06/11 : 2, toutes deux sur des contacts d'essai
--   (20000041 « franck Gerphagnon Test 2026 », 10355711 « TEST CHAINE 25-08 »).
--
-- DEFAUT 2 -- LE RAYON DECORATIF. Le curseur « Rayon autour des localites »
--   (ContactSearchFields.tsx) n'etait qu'un etat de l'ecran, jamais enregistre ;
--   le moteur avait son rayon FIGE a 15 km (commune exacte = plein score, courbe
--   jusqu'a 15 km, au-dela hors zone et plafond 55 -- donc sous le seuil de 60).
--
-- LE REMEDE
--   1. app_search_types_libelles() : { code : libelle }, le libelle pris dans
--      l'ordre a) celui que l'ecran envoie, b) celui que la recherche portait,
--      c) celui qu'une autre recherche porte pour ce code, d) le code en dernier.
--   2. app_search_rayon : une table A PART, cle contact_search_key (le nom fige
--      depuis le 21/09, celui sur lequel app_rapprochement est deja pendu).
--      ⚠ PAS une colonne de app_contact_search_current : la nuit supprime et
--      repose des lignes de recherche (delete_searches_except_dirty, push cible),
--      la valeur y serait perdue en silence -- c'est le choix deja fait pour
--      app_contact_mandat_recherche_current.
--      Rien ne s'y ecrit sauf par les deux portes de modification (SECURITY
--      DEFINER, droits deja verifies par elles). Lecture : meme perimetre que la
--      recherche.
--   3. app_match_score_v2 : la courbe du secteur se lit sur le rayon de la
--      recherche. Sans rayon enregistre -> 15 km, l'ancienne valeur : TOUTES les
--      recherches non reglees gardent EXACTEMENT leur score d'avant (la distance
--      est ramenee a l'echelle des 15 km : dn = dist * 15 / rayon). Rayon 0 =
--      communes seules. La valeur affichee « a N km » reste la vraie distance.
--   4. Les 2 recherches touchees sont reparees, avec une sauvegarde datee.
--
-- CE QUE CA NE TOUCHE PAS : la creation d'une recherche (elle passe par Hektor et
--   n'a pas encore de nom : le curseur y reste a 15 km, et l'ecran le dit) ; le
--   push vers Hektor (ferme depuis C.3, 24/08) ; la nuit.
-- RETOUR ARRIERE : patch_recherche_libelles_et_rayon_2026-11-06_INVERSE.sql
-- CONTROLE      : patch_recherche_libelles_et_rayon_2026-11-06_REPETITION.sql
-- =====================================================================

begin;

-- ── 1. LA TABLE DU RAYON ─────────────────────────────────────────────
create table if not exists public.app_search_rayon (
  contact_search_key text primary key,
  app_search_id      bigint,
  hektor_contact_id  text not null,
  search_index       integer not null,
  rayon_km           integer not null check (rayon_km between 0 and 40),
  updated_at         timestamptz not null default now(),
  updated_by         text
);
create index if not exists app_search_rayon_contact_idx on public.app_search_rayon (hektor_contact_id);
alter table public.app_search_rayon enable row level security;
revoke all on public.app_search_rayon from public, anon, authenticated;
grant select on public.app_search_rayon to authenticated;
grant all on public.app_search_rayon to service_role;
drop policy if exists app_search_rayon_select_scoped on public.app_search_rayon;
create policy app_search_rayon_select_scoped on public.app_search_rayon
  for select to authenticated
  using (exists (select 1 from public.app_contact_current c
                 where c.hektor_contact_id = app_search_rayon.hektor_contact_id
                   and ((select public.is_app_global_reader()) or public.can_access_negotiator_email(c.negociateur_email))));

-- ── 2. LES DEUX AIDES ────────────────────────────────────────────────
-- { code : libelle } a partir des codes choisis. Rend NULL si aucun code (l'appelant
-- garde alors les types en place, comme avant).
create or replace function public.app_search_types_libelles(p_ids jsonb, p_labels jsonb, p_cur jsonb)
returns jsonb
language sql stable security definer
set search_path to 'public'
as $$
  select jsonb_object_agg(t.id, coalesce(
           -- a) le libelle envoye par l'ecran, au meme rang que le code
           (select l from (select trim(p_labels->>(t.n::int - 1)) as l) x
             where jsonb_typeof(p_labels) = 'array' and l !~ '^[0-9]*$'),
           -- b) celui que la recherche portait deja
           (select l from (select trim(p_cur->>t.id) as l) x
             where jsonb_typeof(p_cur) = 'object' and l !~ '^[0-9]*$'),
           -- c) celui qu'une autre recherche porte pour ce code (forme Hektor)
           (select e.value from public.app_contact_search_current s
              cross join lateral jsonb_each_text(case when jsonb_typeof(s.types_json) = 'object'
                                                      then s.types_json else '{}'::jsonb end) e
             where e.key = t.id and e.value !~ '^[0-9]*$'
             limit 1),
           -- d) le code, faute de mieux
           t.id))
  from jsonb_array_elements_text(case when jsonb_typeof(p_ids) = 'array' then p_ids else '[]'::jsonb end)
       with ordinality as t(id, n)
  where trim(t.id) <> ''
$$;

-- Le rayon d'une recherche, en km. 15 = l'ancienne valeur figee du moteur.
create or replace function public.app_search_rayon_km(p_search jsonb)
returns numeric
language sql stable security definer
set search_path to 'public'
as $$
  select coalesce(
    case when (p_search->>'rayon_km') ~ '^[0-9]+(\.[0-9]+)?$' then least(40, (p_search->>'rayon_km')::numeric) end,
    (select r.rayon_km::numeric from public.app_search_rayon r where r.contact_search_key = p_search->>'contact_search_key'),
    15)
$$;

revoke all on function public.app_search_types_libelles(jsonb, jsonb, jsonb) from public, anon, authenticated;
revoke all on function public.app_search_rayon_km(jsonb) from public, anon, authenticated;
grant execute on function public.app_search_types_libelles(jsonb, jsonb, jsonb) to service_role;
grant execute on function public.app_search_rayon_km(jsonb) to service_role;

-- ── 3. LE MOTEUR : LE SECTEUR SE LIT SUR LE RAYON DE LA RECHERCHE ─────
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
  -- 06/11 : le rayon de la recherche, et la distance ramenee a l'echelle des 15 km.
  v_rayon numeric; dn numeric;
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
  -- 06/11 : la courbe se lit sur le RAYON DE LA RECHERCHE (app_search_rayon, 15 km
  -- par defaut = l'ancienne valeur figee : une recherche non reglee garde son score
  -- au centime). Rayon 0 = communes seules.
  IF w_sect>0 AND jsonb_typeof(v_villes)='array' AND jsonb_array_length(v_villes)>0 THEN
    SELECT array_agg(substring(x.v from '[0-9]{5}')) INTO cps FROM jsonb_array_elements_text(v_villes) AS x(v);
    IF d_cp = ANY(COALESCE(cps,'{}'::text[])) THEN
      sub := 1; comp := comp || jsonb_build_object('k','Secteur','ok',true,'v','Commune exacte');
    ELSIF d_lat IS NOT NULL AND d_lng IS NOT NULL THEN
      SELECT min(app_haversine(d_lat,d_lng,r.latitude,r.longitude)) INTO dist FROM ref_commune_geo r WHERE r.code_postal = ANY(cps);
      v_rayon := app_search_rayon_km(p_search);
      IF dist IS NULL THEN
        sub := 0; score_cap := least(score_cap, 55);
        comp := comp || jsonb_build_object('k','Secteur','ok',false,'v','Hors zone connue');
      ELSIF dist >= v_rayon THEN
        sub := 0; score_cap := least(score_cap, 55);
        comp := comp || jsonb_build_object('k','Secteur','ok',false,'v','à '||round(dist)::text||' km');
      ELSE
        dn := dist * 15.0 / v_rayon;
        sub := CASE
          WHEN dn<=3  THEN 0.90 - 0.20*(dn/3)
          WHEN dn<=7  THEN 0.70 - 0.35*((dn-3)/4)
          WHEN dn<=12 THEN 0.35 - 0.25*((dn-7)/5)
          ELSE             0.10 - 0.10*((dn-12)/3)
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

-- ── 4. LA PORTE DE MODIFICATION DE L'APP ─────────────────────────────
CREATE OR REPLACE FUNCTION public.app_edit_search_optimistic(target_contact_id text, search_payload jsonb, debounce_seconds integer DEFAULT 600)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare clean_id text; existing_contact public.app_contact_current%rowtype;
        target_email text; target_user_id text; v_index int; v_search jsonb;
        cur public.app_contact_search_current%rowtype; v_types jsonb; v_villes jsonb; v_base jsonb;
        v_rayon_txt text;
begin
  clean_id := nullif(trim(coalesce(target_contact_id,'')),'');
  if clean_id is null or clean_id !~ '^[0-9]+$' then raise exception 'invalid_contact_id' using errcode='22023'; end if;
  v_search := case when jsonb_typeof(search_payload->'search')='object' then search_payload->'search' else search_payload end;
  v_index := coalesce((search_payload->>'search_index')::int,(search_payload->>'searchIndex')::int,0);
  if nullif(trim(coalesce(v_search->>'priceMax',v_search->>'prix_max','')),'') is null then raise exception 'missing_search_price_max' using errcode='22023'; end if;
  -- 06/11 : le rayon est verifie AVANT toute ecriture.
  v_rayon_txt := nullif(trim(coalesce(search_payload->>'rayon_km','')),'');
  if v_rayon_txt is not null and (v_rayon_txt !~ '^[0-9]+$' or v_rayon_txt::int > 40) then
    raise exception 'invalid_rayon_km' using errcode='22023'; end if;

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

  -- 06/11 : { code : libelle }, la forme de Hektor -- plus { code : code }.
  v_types := coalesce(public.app_search_types_libelles(v_search->'propertyTypeIds', search_payload->'type_labels', cur.types_json), cur.types_json);
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

  -- 06/11 : le rayon, AVANT le recalcul du rapprochement qui le lit.
  if v_rayon_txt is not null then
    insert into public.app_search_rayon(contact_search_key, app_search_id, hektor_contact_id, search_index, rayon_km, updated_at, updated_by)
    values (cur.contact_search_key, cur.app_search_id, clean_id, v_index, v_rayon_txt::int, now(), auth.uid()::text)
    on conflict (contact_search_key) do update set
      app_search_id=excluded.app_search_id, hektor_contact_id=excluded.hektor_contact_id, search_index=excluded.search_index,
      rayon_km=excluded.rayon_km, updated_at=now(), updated_by=excluded.updated_by;
  end if;

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

-- ── 5. LA PORTE DE L'ESPACE CLIENT : LES LIBELLES SEULEMENT ──────────
-- (son ecran n'a pas de curseur de rayon ; elle ne touche pas au rayon)
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

  -- 06/11 : { code : libelle }, la forme de Hektor -- plus { code : code }.
  v_types := coalesce(public.app_search_types_libelles(v_search->'propertyTypeIds', search_payload->'type_labels', cur.types_json), cur.types_json);
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

-- ── 6. LES DEUX RECHERCHES TOUCHEES ──────────────────────────────────
create table if not exists public.app_contact_search_types_avant_libelles_20261106 as
  select contact_search_key, hektor_contact_id, search_index, types_json, now() as sauve_le
  from public.app_contact_search_current
  where jsonb_typeof(types_json) = 'object' and types_json <> '{}'::jsonb
    and not exists (select 1 from jsonb_each_text(types_json) e where e.value !~ '^[0-9]*$');
alter table public.app_contact_search_types_avant_libelles_20261106 enable row level security;
revoke all on public.app_contact_search_types_avant_libelles_20261106 from public, anon, authenticated;

update public.app_contact_search_current s
   set types_json = public.app_search_types_libelles(
         (select jsonb_agg(k) from jsonb_object_keys(s.types_json) k), null, s.types_json)
 where s.contact_search_key in (select contact_search_key from public.app_contact_search_types_avant_libelles_20261106);

commit;
