-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE 8a PIÈCE 2 bis — TOUS LES CHAMPS, UN PAR UN, puis TOUT EST ANNULÉ
--                                                                    21/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Se termine VOLONTAIREMENT par « ESSAI ANNULE -- … » : c'est ce qui annule tout.
-- CE QU'IL JOUE : la vraie version 2 · l'interrupteur allumé DANS la transaction ·
--   T1 les 173 champs de la fiche (App.tsx:1414-1696), chacun avec SA valeur ;
--   T2 les 38 noms Hektor nourris par les champs « à plat » de la saisie ;
--   T3 l'ordre : un équipement GAGNE sur le champ à plat (comme le worker) ;
--   T4 le séjour ne remplace plus l'habitable ;
--   T5 les noms à plat que lisent les autres écrans ;
--   T6 un VRAI appel de la création, au nom de l'admin Frédéric : la fiche
--      détaillée posée en base porte TOUS les champs ;
--   puis le vrai retour arrière (version 1).
-- ⚠ Une séquence ne revient pas en arrière : 1 numéro d'annonce de l'app consommé.
-- Chaque échec est NOMMÉ (jamais « N sur M » seul).
-- Fichier GÉNÉRÉ (gen_repetition_8a2b.py) : ne pas le retoucher à la main.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

create temp table _m (n int, cle text, valeur text) on commit drop;

DO $garde$
DECLARE
    src text := replace(pg_get_functiondef('public.app_annonce_corps_de_naissance(jsonb)'::regprocedure), chr(13), '');
BEGIN
    IF position('8a piece 2 bis' in src) > 0 THEN
        RAISE EXCEPTION '%', 'ARRET : la version 2 est DEJA posee. Rien n''est ecrit.';
    END IF;
    IF md5(src) <> '2e33944ae87333f8062e6b5ff7e7eebf' THEN
        RAISE EXCEPTION '%', format('ARRET : la fonction a change depuis la version 1 (empreinte %s, attendue 2e33944a...). Rien n''est ecrit.', md5(src));
    END IF;
END
$garde$;

create or replace function public.app_annonce_corps_de_naissance(p jsonb)
 returns jsonb
 language plpgsql
 stable
 set search_path to 'public'
as $f$
-- 8a piece 2 bis (21/10/2026) : TOUS les champs de la saisie, aux noms que la fiche lit
declare
  v_allume  boolean;
  -- le nom Hektor <- les cles « a plat » de la saisie, DANS L'ORDRE ou le worker les lit
  -- (buildWizardStep2/4/6/7Body, console_job_worker.js:10669-10862 ; premiere non vide)
  correspondance constant jsonb := '{
    "prix": ["price"], "PRIXNETVENDEUR": ["net_seller_price"], "surfappart": ["surface"],
    "surfterrain": ["land_surface"], "SURFACE_GARAGE": ["garage_surface"],
    "nbpieces": ["room_count"], "NB_CHAMBRES": ["bedroom_count"], "NB_NIVEAUX": ["level_count"],
    "GARAGE_BOX": ["garage_count"], "JARDIN-": ["garden"], "PISCINE-": ["pool"],
    "EXPOSITION": ["exposure"], "vuee": ["view"],
    "NB_SDB": ["bathroom_count"], "NB_SE": ["shower_room_count"], "NB_WC": ["wc_count"],
    "SURF_CARREZ": ["carrez_surface"], "SURF_SEJOUR": ["living_surface"], "CUISINE": ["kitchen"],
    "etat_interieur": ["interior_state"], "etat_exterieur": ["exterior_state"],
    "NB_TERRASSE": ["terrace_count"], "NB_PARK_INT": ["parking_inside_count"],
    "NB_PARK_EXT": ["parking_outside_count"], "ANNEE_CONS": ["construction_year"],
    "dpe_cons": ["dpe_value"], "dpe_ges": ["ges_value"],
    "copropriete_nb_lot": ["copro_lots"], "copropriete_quote_part": ["copro_quote_part"],
    "montant_fonds_travaux": ["copro_works_fund"], "CHARGES": ["copro_charges"],
    "titre": ["title"], "corps": ["description"], "adresse": ["address"],
    "codeprive": ["postal_code"], "codepublique": ["postal_code"],
    "villeprivee": ["city"], "villepublique": ["city"]}';
  -- les noms « a plat » de la fiche detaillee que les AUTRES ecrans lisent (en-tete,
  -- listes, rapprochement), et le nom Hektor d'ou ils viennent
  a_plat constant jsonb := '{
    "surface": "surfappart", "surface_habitable_detail": "surfappart",
    "surface_terrain_detail": "surfterrain", "nb_pieces": "nbpieces", "nb_chambres": "NB_CHAMBRES",
    "prix_publique": "prix", "prix_net_vendeur": "PRIXNETVENDEUR",
    "texte_principal_titre": "titre", "texte_principal_html": "corps",
    "adresse_detail": "adresse", "code_postal_detail": "codepublique",
    "code_postal_prive_detail": "codeprive", "ville_privee_detail": "villeprivee",
    "ville_publique_detail": "villepublique", "garage_box_detail": "GARAGE_BOX",
    "terrasse_detail": "TERRASSE", "ascenseur_detail": "ASCENSEUR",
    "copropriete_detail": "copropriete", "etage_detail": "ETAGE"}';
  plat      jsonb := '{}'::jsonb;
  wiz       jsonb := '{}'::jsonb;
  calque    jsonb;
  detail    jsonb;
  k         text;
  a         text;
  v         text;
  m         text;
  mots      text[] := '{}';
  vus       text[] := '{}';
  v_date    text := to_char(now() at time zone 'Europe/Paris', 'YYYY-MM-DD HH24:MI:SS');
begin
  select lower(trim(coalesce(s.value, ''))) in ('on', '1', 'true', 'oui')
    into v_allume
    from public.app_setting s
   where s.key = 'annonce_nait_complete';
  if not coalesce(v_allume, false) or p is null or jsonb_typeof(p) <> 'object' then
    return null;
  end if;

  -- 1. les champs a plat, vers leur nom Hektor (une valeur vide ou un objet ne compte pas)
  for k in select jsonb_object_keys(correspondance) loop
    v := null;
    for a in select jsonb_array_elements_text(correspondance->k) loop
      if jsonb_typeof(p->a) in ('string', 'number') then
        v := nullif(trim(p->>a), '');
      end if;
      exit when v is not null;
    end loop;
    if v is not null then
      plat := plat || jsonb_build_object(k, v);
    end if;
  end loop;

  -- 2. les equipements : l'ecran les envoie DEJA aux noms de Hektor (App.tsx:16068-16086)
  if jsonb_typeof(p->'hektor_wizard_fields') = 'object' then
    for k in select jsonb_object_keys(p->'hektor_wizard_fields') loop
      if jsonb_typeof(p->'hektor_wizard_fields'->k) in ('string', 'number')
         and nullif(trim(p->'hektor_wizard_fields'->>k), '') is not null then
        wiz := wiz || jsonb_build_object(k, trim(p->'hektor_wizard_fields'->>k));
      end if;
    end loop;
  end if;

  -- 3. les equipements GAGNENT, comme chez le worker (appliques en dernier a chaque etape)
  calque := plat || wiz;

  -- 4. le texte de recherche, comme build_search_text() du serveur : titre, ville, code
  --    postal, negociateur, agence ; chaque mot une seule fois (sans tenir compte de la casse)
  foreach m in array regexp_split_to_array(
      trim(concat_ws(' ', p->>'title', p->>'city', p->>'postal_code', p->>'hektor_user_label', p->>'agence_nom')),
      '\s+') loop
    if m <> '' and not (lower(m) = any(vus)) then
      vus  := vus  || lower(m);
      mots := mots || m;
    end if;
  end loop;

  -- 5. la fiche detaillee de depart : les noms a plat, puis le calque et la saisie
  detail := jsonb_strip_nulls(jsonb_build_object(
    'date_enregistrement_annonce', v_date,
    'agence_nom',                  nullif(trim(coalesce(p->>'agence_nom', '')), ''),
    'responsable_affichage',       nullif(trim(coalesce(p->>'hektor_user_label', '')), ''),
    'detail_statut_name',          nullif(trim(coalesce(p->>'status_label', '')), '')));
  for k in select jsonb_object_keys(a_plat) loop
    if calque ? (a_plat->>k) then
      detail := detail || jsonb_build_object(k, calque->>(a_plat->>k));
    end if;
  end loop;

  return jsonb_build_object(
    'colonnes', jsonb_strip_nulls(jsonb_build_object(
      -- le TYPE est un CODE (« 2 » = appartement), jamais le libellé
      'type_bien',                   nullif(trim(coalesce(p->>'hektor_id_type', '')), ''),
      'adresse_detail',              nullif(trim(coalesce(p->>'address', '')), ''),
      'code_postal_prive_detail',    nullif(trim(coalesce(p->>'postal_code', '')), ''),
      'ville_privee_detail',         nullif(trim(coalesce(p->>'city', '')), ''),
      'date_enregistrement_annonce', v_date,
      'search_text',                 nullif(array_to_string(mots, ' '), ''))),
    'detail', detail || jsonb_build_object(
      'app_optimistic_overlay', calque,
      -- la saisie telle quelle, pour qu'elle existe chez nous -- SANS le mandant
      -- (ses coordonnees vivent dans les contacts, pas dans la fiche du bien)
      'app_saisie_creation', p - 'creation_token' - 'initial_mandant'
                               - 'initial_mandant_contact_id' - 'initial_mandant_contact_label'));
end
$f$;

revoke all on function public.app_annonce_corps_de_naissance(jsonb) from public;
revoke all on function public.app_annonce_corps_de_naissance(jsonb) from anon;
revoke all on function public.app_annonce_corps_de_naissance(jsonb) from authenticated;
grant execute on function public.app_annonce_corps_de_naissance(jsonb) to service_role;


insert into _m values (0, 'empreinte_v2', md5(replace(pg_get_functiondef('public.app_annonce_corps_de_naissance(jsonb)'::regprocedure), chr(13), '')));

update public.app_setting set value = 'on', updated_at = now() where key = 'annonce_nait_complete';

DO $essai$
DECLARE
  noms      text[] := '{"prix","PRIXNETVENDEUR","surfappart","surfterrain","SURFACE_GARAGE","nbpieces","NB_CHAMBRES","NB_NIVEAUX","JARDIN-","PISCINE-","GARAGE_BOX","EXPOSITION","vuee","NO_DOSSIER","dateenr","codepublique","villepublique","adresse","villeprivee","codeprive","immeuble","TRANSPORT","PROXIMITE","ENVIRONNEMENT","latitude","longitude","Particularites","NB_SDB","NB_SE","NB_WC","SURF_CARREZ","SURF_SEJOUR","CUISINE","CUISINE_EQUIPEMENT","MURS_MITOYENS","floorState","ETAGE","DERNIER_ETAGE","NB_ETAGES","CAVE","SURFACE_CAVE","BALCON","NB_BALCON","SURFACE_BALCON","TERRASSE","NB_TERRASSE","SURFACE_TERRASSE","NB_PARK_INT","NB_PARK_EXT","RESIDENCE","TYPE_RESIDENCE","PISCINE_TYPE","PISCINE_NATURE","PISCINE_DIMENSIONS","PISCINE_TRAITEMENT","PISCINE_CHAUFFEE","PISCINE_COUVERTE","POOL_HOUSE","PISCINE_DETAILS","SURFACE_JARDIN","terrain_constructible","terrain_surface_constructible","SHON","terrain_viabilise","terrain_raccordement_eau","terrain_raccordement_gaz","terrain_raccordement_electricite","terrain_raccordement_telephone","terrain_arbore","terrain_piscinable","garantie_decennale","assurance_dommages_ouvrage","certificat_conformite","declaration_achevement_travaux","formatChauff","typeChauff","energieChauff","ASCENSEUR","ACCES_HANDI","climatisation","climatisationspec","EAU","ASSAINISSEMENT","DISTRIBUTION_EAU","ENERGIE_EAU","cheminee","volets_elctriques","gardien","double_vitrage","triple_vitrage","cable","porte_blindee","interphone","visiophone","alarme","digicode","detecteur_fumee","ANNEE_CONS","etat_exterieur","etat_interieur","dpe_date","dpe_non_concerne","dpe_vierge","isDpeAltitude","dpe_cons","dpe_ges","valeurEnergieFinale","dpe_couts_min","dpe_couts_max","dpe_annee_reference","diagnostiqueur","syndic","diag_termites","diag_termites_date","diag_termites_commentaire","diag_amiante","diag_amiante_date","diag_amiante_commentaire","diag_electrique","diag_electrique_date","diag_electrique_commentaire","diag_loi_carrez","diag_loi_carrez_date","diag_loi_carrez_commentaire","diag_risques_nat_tech","diag_risques_nat_tech_date","diag_risques_nat_tech_commentaire","diag_plomb","diag_plomb_date","diag_plomb_commentaire","diag_gaz","diag_gaz_date","diag_gaz_commentaire","diag_assainissement","diag_assainissement_date","diag_assainissement_commentaire","clearing","copropriete","copropriete_lot","copropriete_nb_lot","copropriete_quote_part","montant_fonds_travaux","copropriete_plan_sauvegarde","copropriete_statut_syndicat","DISPO","DATE_LIBER","DATE_DISPO","CLES","moyens_visite","_selecterHonoraires2","_tauxHonoraire2","_pourcentHonoraire2","_detailHonoraire2","_selecterHonoraires3","_tauxHonoraire3","_pourcentHonoraire3","_detailHonoraire3","masque","ESTIMATION_MONTANT","ESTIMATION_DATE","TRAVAUX","DEPOT_GARANTIE","TAXE_HABITATION","TAXE_FONCIERE","CHARGES","CHARGES_DETAIL","Loc_EstimationLoyer","Loc_ChargeLocative","Loc_RendementBrut","Loc_Occupation","diffusable","titre","corps"}'::text[];
  s_plat    jsonb := '{"title": "ESSAI 8A2B", "description": "Essai 8a2b, annule.", "price": "p_price", "net_seller_price": "p_net_seller_price", "surface": "p_surface", "carrez_surface": "p_carrez_surface", "living_surface": "p_living_surface", "room_count": "p_room_count", "bedroom_count": "p_bedroom_count", "level_count": "p_level_count", "bathroom_count": "p_bathroom_count", "shower_room_count": "p_shower_room_count", "wc_count": "p_wc_count", "kitchen": "p_kitchen", "exposure": "p_exposure", "view": "p_view", "interior_state": "p_interior_state", "exterior_state": "p_exterior_state", "land_surface": "p_land_surface", "garden": "p_garden", "terrace_count": "p_terrace_count", "garage_count": "p_garage_count", "garage_surface": "p_garage_surface", "parking_inside_count": "p_parking_inside_count", "parking_outside_count": "p_parking_outside_count", "pool": "p_pool", "construction_year": "p_construction_year", "dpe_value": "p_dpe_value", "ges_value": "p_ges_value", "copro_lots": "p_copro_lots", "copro_charges": "p_copro_charges", "copro_quote_part": "p_copro_quote_part", "copro_works_fund": "p_copro_works_fund", "address": "p_address", "postal_code": "42700", "city": "Firminy", "agence_nom": "Groupe GTI Firminy", "hektor_user_label": "Emmanuelle PEREIRA", "hektor_user_email": "pereira@gti-immobilier.fr", "hektor_user_id": "51", "hektor_negociator_form_id": "26", "hektor_id_type": "2", "property_type": "Appartement", "property_profile": "apartment", "status_label": "Estimation", "statut_annonce": "1", "creation_status": "estimation", "creation_mode": "draft_only", "offer_type": "sale", "offredem": "0", "note": "note d''essai", "composition_pieces": [{"type": "SEJOUR", "surface": "30"}], "initial_mandant": {"last_name": "NE PAS COPIER"}, "initial_mandant_contact_label": "NE PAS COPIER"}';
  s_wiz     jsonb := '{"title": "ESSAI 8A2B", "description": "Essai 8a2b, annule.", "price": "p_price", "net_seller_price": "p_net_seller_price", "surface": "p_surface", "carrez_surface": "p_carrez_surface", "living_surface": "p_living_surface", "room_count": "p_room_count", "bedroom_count": "p_bedroom_count", "level_count": "p_level_count", "bathroom_count": "p_bathroom_count", "shower_room_count": "p_shower_room_count", "wc_count": "p_wc_count", "kitchen": "p_kitchen", "exposure": "p_exposure", "view": "p_view", "interior_state": "p_interior_state", "exterior_state": "p_exterior_state", "land_surface": "p_land_surface", "garden": "p_garden", "terrace_count": "p_terrace_count", "garage_count": "p_garage_count", "garage_surface": "p_garage_surface", "parking_inside_count": "p_parking_inside_count", "parking_outside_count": "p_parking_outside_count", "pool": "p_pool", "construction_year": "p_construction_year", "dpe_value": "p_dpe_value", "ges_value": "p_ges_value", "copro_lots": "p_copro_lots", "copro_charges": "p_copro_charges", "copro_quote_part": "p_copro_quote_part", "copro_works_fund": "p_copro_works_fund", "address": "p_address", "postal_code": "42700", "city": "Firminy", "agence_nom": "Groupe GTI Firminy", "hektor_user_label": "Emmanuelle PEREIRA", "hektor_user_email": "pereira@gti-immobilier.fr", "hektor_user_id": "51", "hektor_negociator_form_id": "26", "hektor_id_type": "2", "property_type": "Appartement", "property_profile": "apartment", "status_label": "Estimation", "statut_annonce": "1", "creation_status": "estimation", "creation_mode": "draft_only", "offer_type": "sale", "offredem": "0", "note": "note d''essai", "composition_pieces": [{"type": "SEJOUR", "surface": "30"}], "initial_mandant": {"last_name": "NE PAS COPIER"}, "initial_mandant_contact_label": "NE PAS COPIER", "hektor_wizard_fields": {"prix": "w001", "PRIXNETVENDEUR": "w002", "surfappart": "w003", "surfterrain": "w004", "SURFACE_GARAGE": "w005", "nbpieces": "w006", "NB_CHAMBRES": "w007", "NB_NIVEAUX": "w008", "JARDIN-": "w009", "PISCINE-": "w010", "GARAGE_BOX": "w011", "EXPOSITION": "w012", "vuee": "w013", "NO_DOSSIER": "w014", "dateenr": "w015", "codepublique": "w016", "villepublique": "w017", "adresse": "w018", "villeprivee": "w019", "codeprive": "w020", "immeuble": "w021", "TRANSPORT": "w022", "PROXIMITE": "w023", "ENVIRONNEMENT": "w024", "latitude": "w025", "longitude": "w026", "Particularites": "w027", "NB_SDB": "w028", "NB_SE": "w029", "NB_WC": "w030", "SURF_CARREZ": "w031", "SURF_SEJOUR": "w032", "CUISINE": "w033", "CUISINE_EQUIPEMENT": "w034", "MURS_MITOYENS": "w035", "floorState": "w036", "ETAGE": "w037", "DERNIER_ETAGE": "w038", "NB_ETAGES": "w039", "CAVE": "w040", "SURFACE_CAVE": "w041", "BALCON": "w042", "NB_BALCON": "w043", "SURFACE_BALCON": "w044", "TERRASSE": "w045", "NB_TERRASSE": "w046", "SURFACE_TERRASSE": "w047", "NB_PARK_INT": "w048", "NB_PARK_EXT": "w049", "RESIDENCE": "w050", "TYPE_RESIDENCE": "w051", "PISCINE_TYPE": "w052", "PISCINE_NATURE": "w053", "PISCINE_DIMENSIONS": "w054", "PISCINE_TRAITEMENT": "w055", "PISCINE_CHAUFFEE": "w056", "PISCINE_COUVERTE": "w057", "POOL_HOUSE": "w058", "PISCINE_DETAILS": "w059", "SURFACE_JARDIN": "w060", "terrain_constructible": "w061", "terrain_surface_constructible": "w062", "SHON": "w063", "terrain_viabilise": "w064", "terrain_raccordement_eau": "w065", "terrain_raccordement_gaz": "w066", "terrain_raccordement_electricite": "w067", "terrain_raccordement_telephone": "w068", "terrain_arbore": "w069", "terrain_piscinable": "w070", "garantie_decennale": "w071", "assurance_dommages_ouvrage": "w072", "certificat_conformite": "w073", "declaration_achevement_travaux": "w074", "formatChauff": "w075", "typeChauff": "w076", "energieChauff": "w077", "ASCENSEUR": "w078", "ACCES_HANDI": "w079", "climatisation": "w080", "climatisationspec": "w081", "EAU": "w082", "ASSAINISSEMENT": "w083", "DISTRIBUTION_EAU": "w084", "ENERGIE_EAU": "w085", "cheminee": "w086", "volets_elctriques": "w087", "gardien": "w088", "double_vitrage": "w089", "triple_vitrage": "w090", "cable": "w091", "porte_blindee": "w092", "interphone": "w093", "visiophone": "w094", "alarme": "w095", "digicode": "w096", "detecteur_fumee": "w097", "ANNEE_CONS": "w098", "etat_exterieur": "w099", "etat_interieur": "w100", "dpe_date": "w101", "dpe_non_concerne": "w102", "dpe_vierge": "w103", "isDpeAltitude": "w104", "dpe_cons": "w105", "dpe_ges": "w106", "valeurEnergieFinale": "w107", "dpe_couts_min": "w108", "dpe_couts_max": "w109", "dpe_annee_reference": "w110", "diagnostiqueur": "w111", "syndic": "w112", "diag_termites": "w113", "diag_termites_date": "w114", "diag_termites_commentaire": "w115", "diag_amiante": "w116", "diag_amiante_date": "w117", "diag_amiante_commentaire": "w118", "diag_electrique": "w119", "diag_electrique_date": "w120", "diag_electrique_commentaire": "w121", "diag_loi_carrez": "w122", "diag_loi_carrez_date": "w123", "diag_loi_carrez_commentaire": "w124", "diag_risques_nat_tech": "w125", "diag_risques_nat_tech_date": "w126", "diag_risques_nat_tech_commentaire": "w127", "diag_plomb": "w128", "diag_plomb_date": "w129", "diag_plomb_commentaire": "w130", "diag_gaz": "w131", "diag_gaz_date": "w132", "diag_gaz_commentaire": "w133", "diag_assainissement": "w134", "diag_assainissement_date": "w135", "diag_assainissement_commentaire": "w136", "clearing": "w137", "copropriete": "w138", "copropriete_lot": "w139", "copropriete_nb_lot": "w140", "copropriete_quote_part": "w141", "montant_fonds_travaux": "w142", "copropriete_plan_sauvegarde": "w143", "copropriete_statut_syndicat": "w144", "DISPO": "w145", "DATE_LIBER": "w146", "DATE_DISPO": "w147", "CLES": "w148", "moyens_visite": "w149", "_selecterHonoraires2": "w150", "_tauxHonoraire2": "w151", "_pourcentHonoraire2": "w152", "_detailHonoraire2": "w153", "_selecterHonoraires3": "w154", "_tauxHonoraire3": "w155", "_pourcentHonoraire3": "w156", "_detailHonoraire3": "w157", "masque": "w158", "ESTIMATION_MONTANT": "w159", "ESTIMATION_DATE": "w160", "TRAVAUX": "w161", "DEPOT_GARANTIE": "w162", "TAXE_HABITATION": "w163", "TAXE_FONCIERE": "w164", "CHARGES": "w165", "CHARGES_DETAIL": "w166", "Loc_EstimationLoyer": "w167", "Loc_ChargeLocative": "w168", "Loc_RendementBrut": "w169", "Loc_Occupation": "w170", "diffusable": "w171", "titre": "w172", "corps": "w173"}}';
  att_plat  jsonb := '{"prix": "p_price", "PRIXNETVENDEUR": "p_net_seller_price", "surfappart": "p_surface", "surfterrain": "p_land_surface", "SURFACE_GARAGE": "p_garage_surface", "nbpieces": "p_room_count", "NB_CHAMBRES": "p_bedroom_count", "NB_NIVEAUX": "p_level_count", "GARAGE_BOX": "p_garage_count", "JARDIN-": "p_garden", "PISCINE-": "p_pool", "EXPOSITION": "p_exposure", "vuee": "p_view", "NB_SDB": "p_bathroom_count", "NB_SE": "p_shower_room_count", "NB_WC": "p_wc_count", "SURF_CARREZ": "p_carrez_surface", "SURF_SEJOUR": "p_living_surface", "CUISINE": "p_kitchen", "etat_interieur": "p_interior_state", "etat_exterieur": "p_exterior_state", "NB_TERRASSE": "p_terrace_count", "NB_PARK_INT": "p_parking_inside_count", "NB_PARK_EXT": "p_parking_outside_count", "ANNEE_CONS": "p_construction_year", "dpe_cons": "p_dpe_value", "dpe_ges": "p_ges_value", "copropriete_nb_lot": "p_copro_lots", "copropriete_quote_part": "p_copro_quote_part", "montant_fonds_travaux": "p_copro_works_fund", "CHARGES": "p_copro_charges", "titre": "ESSAI 8A2B", "corps": "Essai 8a2b, annule.", "adresse": "p_address", "codeprive": "42700", "codepublique": "42700", "villeprivee": "Firminy", "villepublique": "Firminy"}';
  r         jsonb;
  c         jsonb;
  dd        jsonb;
  i         int;
  ko        text[] := '{}';
  ok        int := 0;
  v_uid     uuid;
  v_job     public.app_console_job;
  v_id      bigint;
  k         text;
  t6_ok text; t6_ko text; t6_job text; t6_cols text; t6_err text;
BEGIN
  -- T1 : chaque champ de la fiche, dans les equipements
  r := public.app_annonce_corps_de_naissance(s_wiz);
  c := r->'detail'->'app_optimistic_overlay';
  for i in 1 .. array_length(noms, 1) loop
    if c->>noms[i] = 'w' || lpad(i::text, 3, '0') then ok := ok + 1; else ko := ko || noms[i]; end if;
  end loop;
  insert into _m values (1, 'T1_champs_de_la_fiche_ok', ok || ' sur ' || array_length(noms, 1)),
                        (2, 'T1_echecs', coalesce(nullif(array_to_string(ko, ','), ''), 'aucun'));

  -- T2 : les champs a plat seuls
  r := public.app_annonce_corps_de_naissance(s_plat);
  c := r->'detail'->'app_optimistic_overlay';
  ok := 0; ko := '{}';
  for k in select jsonb_object_keys(att_plat) loop
    if c->>k = att_plat->>k then ok := ok + 1; else ko := ko || (k || '=' || coalesce(c->>k, 'NULL')); end if;
  end loop;
  insert into _m values (3, 'T2_champs_a_plat_ok', ok || ' sur ' || (select count(*) from jsonb_object_keys(att_plat))),
                        (4, 'T2_echecs', coalesce(nullif(array_to_string(ko, ','), ''), 'aucun'));
  -- T4 : le sejour ne remplace plus l'habitable
  insert into _m values (5, 'T4_sejour_seul_dans_habitable',
    coalesce(public.app_annonce_corps_de_naissance('{"living_surface":"30"}'::jsonb)->'detail'->'app_optimistic_overlay'->>'surfappart', 'vide (OK)'));

  -- T3 : l'equipement gagne
  r := public.app_annonce_corps_de_naissance(s_wiz);
  c := r->'detail'->'app_optimistic_overlay';
  insert into _m values (6, 'T3_prix_plat_contre_equipement', coalesce(c->>'prix', 'NULL') || ' (attendu w' || lpad(array_position(noms, 'prix')::text, 3, '0') || ')');

  -- T5 : les noms a plat de la fiche detaillee = la valeur du calque
  dd := r->'detail';
  ok := 0; ko := '{}';
  foreach k in array array['surface:surfappart','surface_habitable_detail:surfappart','surface_terrain_detail:surfterrain',
      'nb_pieces:nbpieces','nb_chambres:NB_CHAMBRES','prix_publique:prix','prix_net_vendeur:PRIXNETVENDEUR',
      'texte_principal_titre:titre','texte_principal_html:corps','adresse_detail:adresse','code_postal_detail:codepublique',
      'code_postal_prive_detail:codeprive','ville_privee_detail:villeprivee','ville_publique_detail:villepublique',
      'garage_box_detail:GARAGE_BOX','terrasse_detail:TERRASSE','ascenseur_detail:ASCENSEUR',
      'copropriete_detail:copropriete','etage_detail:ETAGE'] loop
    if dd->>split_part(k, ':', 1) is not null and dd->>split_part(k, ':', 1) = c->>split_part(k, ':', 2) then ok := ok + 1;
    else ko := ko || split_part(k, ':', 1); end if;
  end loop;
  insert into _m values (7, 'T5_noms_a_plat_ok', ok || ' sur 19'),
                        (8, 'T5_echecs', coalesce(nullif(array_to_string(ko, ','), ''), 'aucun')),
                        (9, 'T5_negociateur_agence_statut', coalesce(dd->>'responsable_affichage','NULL') || ' / ' || coalesce(dd->>'agence_nom','NULL') || ' / ' || coalesce(dd->>'detail_statut_name','NULL')),
                        (10, 'mandant_et_jeton_dans_la_saisie',
                             case when (dd->'app_saisie_creation') ?| array['initial_mandant','initial_mandant_contact_label','creation_token'] then 'PRESENT' else 'absent' end),
                        (11, 'note_et_composition_gardees',
                             case when dd->'app_saisie_creation' ? 'note' and jsonb_typeof(dd->'app_saisie_creation'->'composition_pieces') = 'array' then 'oui' else 'NON' end);

  -- T6 : un VRAI appel de la creation
  select id into v_uid from public.app_user_profile
   where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1;
  perform set_config('request.jwt.claims', json_build_object('sub', v_uid::text, 'role', 'authenticated')::text, true);
  perform set_config('request.jwt.claim.sub', v_uid::text, true);
  begin
    v_job := public.app_create_annonce_job_optimistic(gen_random_uuid(),
               '{"titre_bien":"ESSAI 8A2B","prix":"150000","ville":"Firminy","code_postal":"42700","statut_annonce":"Estimation"}'::jsonb, s_wiz, 18);
    v_id := (v_job.payload_json->>'app_dossier_id')::bigint;
    select detail_payload_json::jsonb into dd from public.app_dossier_detail_current where app_dossier_id = v_id;
    c := dd->'app_optimistic_overlay';
    ok := 0; ko := '{}';
    for i in 1 .. array_length(noms, 1) loop
      if c->>noms[i] = 'w' || lpad(i::text, 3, '0') then ok := ok + 1; else ko := ko || noms[i]; end if;
    end loop;
    -- ⚠ en VARIABLES : une ecriture dans ce bloc serait annulee avec lui (essai du 21/10)
    t6_ok   := ok || ' sur ' || array_length(noms, 1);
    t6_ko   := coalesce(nullif(array_to_string(ko, ','), ''), 'aucun');
    t6_job  := case when (v_job.payload_json->'hektor_wizard_fields') = (s_wiz->'hektor_wizard_fields') then 'intacte' else 'MODIFIEE' end;
    t6_cols := coalesce((select search_text || ' / ' || type_bien from public.app_dossier_current where app_dossier_id = v_id), 'NULL');
    raise exception 'ANNULATION_INTERNE';
  exception when others then
    if sqlerrm <> 'ANNULATION_INTERNE' then t6_err := sqlerrm; end if;
  end;
  insert into _m values (12, 'T6_creation_reelle_champs_en_base', coalesce(t6_ok, '?')),
                        (13, 'T6_echecs', coalesce(t6_ko, '?')),
                        (14, 'T6_le_travail_porte_toujours_la_saisie', coalesce(t6_job, '?')),
                        (15, 'T6_fiche_recherche_et_type', coalesce(t6_cols, '?')),
                        (16, 'T6_erreur', coalesce(t6_err, 'aucune'));
END
$essai$;

-- ── LE VRAI RETOUR ARRIÈRE ──
DO $garde$
BEGIN
    IF position('8a piece 2 bis' in pg_get_functiondef('public.app_annonce_corps_de_naissance(jsonb)'::regprocedure)) = 0 THEN
        RAISE EXCEPTION '%', 'ARRET : la version 2 n''est pas posee, rien a retirer. Rien n''est ecrit.';
    END IF;
END
$garde$;

create or replace function public.app_annonce_corps_de_naissance(p jsonb)
 returns jsonb
 language plpgsql
 stable
 set search_path to 'public'
as $f$
declare
  v_allume  boolean;
  wiz       jsonb := '{}'::jsonb;
  calque    jsonb;
  k         text;
  m         text;
  mots      text[] := '{}';
  vus       text[] := '{}';
  v_date    text := to_char(now() at time zone 'Europe/Paris', 'YYYY-MM-DD HH24:MI:SS');
begin
  select lower(trim(coalesce(s.value, ''))) in ('on', '1', 'true', 'oui')
    into v_allume
    from public.app_setting s
   where s.key = 'annonce_nait_complete';
  if not coalesce(v_allume, false) or p is null or jsonb_typeof(p) <> 'object' then
    return null;
  end if;

  -- les equipements : l'ecran les envoie DEJA aux noms de Hektor (App.tsx:16068-16086,
  -- niveaux, garages, jardin, piscine, exposition, vue y sont recopies avant l'envoi)
  if jsonb_typeof(p->'hektor_wizard_fields') = 'object' then
    for k in select jsonb_object_keys(p->'hektor_wizard_fields') loop
      if jsonb_typeof(p->'hektor_wizard_fields'->k) in ('string', 'number')
         and nullif(trim(p->'hektor_wizard_fields'->>k), '') is not null then
        wiz := wiz || jsonb_build_object(k, trim(p->'hektor_wizard_fields'->>k));
      end if;
    end loop;
  end if;

  -- les champs principaux, vers les noms que la fiche lit (wizardDetailValue, App.tsx:2651)
  calque := wiz || jsonb_strip_nulls(jsonb_build_object(
    'titre',          nullif(trim(coalesce(p->>'title', '')), ''),
    'corps',          nullif(trim(coalesce(p->>'description', '')), ''),
    'prix',           nullif(trim(coalesce(p->>'price', '')), ''),
    'PRIXNETVENDEUR', nullif(trim(coalesce(p->>'net_seller_price', '')), ''),
    'surfappart',     nullif(trim(coalesce(p->>'surface', p->>'living_surface', '')), ''),
    'nbpieces',       nullif(trim(coalesce(p->>'room_count', '')), ''),
    'NB_CHAMBRES',    nullif(trim(coalesce(p->>'bedroom_count', '')), ''),
    'adresse',        nullif(trim(coalesce(p->>'address', '')), ''),
    'codeprive',      nullif(trim(coalesce(p->>'postal_code', '')), ''),
    'villeprivee',    nullif(trim(coalesce(p->>'city', '')), ''),
    'codepublique',   nullif(trim(coalesce(p->>'postal_code', '')), ''),
    'villepublique',  nullif(trim(coalesce(p->>'city', '')), '')));

  -- le texte de recherche, comme build_search_text() du serveur : titre, ville, code
  -- postal, negociateur, agence ; chaque mot une seule fois (sans tenir compte de la casse)
  foreach m in array regexp_split_to_array(
      trim(concat_ws(' ', p->>'title', p->>'city', p->>'postal_code', p->>'hektor_user_label', p->>'agence_nom')),
      '\s+') loop
    if m <> '' and not (lower(m) = any(vus)) then
      vus  := vus  || lower(m);
      mots := mots || m;
    end if;
  end loop;

  return jsonb_build_object(
    'colonnes', jsonb_strip_nulls(jsonb_build_object(
      -- le TYPE est un CODE (« 2 » = appartement), jamais le libellé
      'type_bien',                   nullif(trim(coalesce(p->>'hektor_id_type', '')), ''),
      'adresse_detail',              nullif(trim(coalesce(p->>'address', '')), ''),
      'code_postal_prive_detail',    nullif(trim(coalesce(p->>'postal_code', '')), ''),
      'ville_privee_detail',         nullif(trim(coalesce(p->>'city', '')), ''),
      'date_enregistrement_annonce', v_date,
      'search_text',                 nullif(array_to_string(mots, ' '), ''))),
    'detail', jsonb_strip_nulls(jsonb_build_object(
      'surface',                     calque->>'surfappart',
      'nb_pieces',                   calque->>'nbpieces',
      'nb_chambres',                 calque->>'NB_CHAMBRES',
      'date_enregistrement_annonce', v_date))
      || jsonb_build_object(
      'app_optimistic_overlay', calque,
      -- la saisie telle quelle, pour qu'elle existe chez nous -- SANS le mandant
      -- (ses coordonnees vivent dans les contacts, pas dans la fiche du bien)
      'app_saisie_creation', p - 'creation_token' - 'initial_mandant'
                               - 'initial_mandant_contact_id' - 'initial_mandant_contact_label'));
end
$f$;

revoke all on function public.app_annonce_corps_de_naissance(jsonb) from public;
revoke all on function public.app_annonce_corps_de_naissance(jsonb) from anon;
revoke all on function public.app_annonce_corps_de_naissance(jsonb) from authenticated;
grant execute on function public.app_annonce_corps_de_naissance(jsonb) to service_role;


DO $preuve$
DECLARE e text := md5(replace(pg_get_functiondef('public.app_annonce_corps_de_naissance(jsonb)'::regprocedure), chr(13), ''));
BEGIN
    IF e <> '2e33944ae87333f8062e6b5ff7e7eebf' THEN
        RAISE EXCEPTION '%', format('ARRET : le retour ne redonne PAS la version 1 (%s au lieu de 2e33944a...). Tout est annule.', e);
    END IF;
END
$preuve$;


insert into _m values
 (17, 'retour_version_1', case when md5(replace(pg_get_functiondef('public.app_annonce_corps_de_naissance(jsonb)'::regprocedure), chr(13), '')) = '2e33944ae87333f8062e6b5ff7e7eebf' then 'oui' else 'NON' end),
 (18, 'creation_non_retouchee', case when md5(replace(pg_get_functiondef('public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)'::regprocedure), chr(13), '')) = 'a5e70b5734876f74ecd0083681a1ebe8' then 'oui' else 'NON' end);

DO $fin$
BEGIN
  RAISE EXCEPTION '%', (select 'ESSAI ANNULE -- ' || string_agg(lpad(n::text, 2, '0') || ' ' || cle || '=' || valeur, ' | ' order by n) from _m);
END
$fin$;

ROLLBACK;
