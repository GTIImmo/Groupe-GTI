-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · PIÈCE 2 bis (8a, L10-2d) — TOUS LES CHAMPS, PAS SEULEMENT 16
--                                                                    21/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md (pièce 2 bis)
-- Frédéric, 21/10 : « il faut vraiment tester tous les champs, pas juste 16 ».
--
-- CE QUE LA LISTE COMPLÈTE A TROUVÉ dans la version 1 (patch_8a2, posé éteint) :
--   1. 27 champs « à plat » de la saisie (salles de bain, WC, Carrez, séjour,
--      cuisine, états, DPE, GES, copropriété, charges, parkings, terrasse, garage,
--      niveaux, jardin, piscine, exposition, vue, année) partent bien chez Hektor
--      -- le worker leur donne leur nom Hektor -- mais le calque ne les reprenait
--      pas : la fiche les aurait affichés VIDES jusqu'au retour de Hektor ;
--   2. la surface du SÉJOUR (living_surface) servait de repli à la surface
--      HABITABLE : faux, le worker l'envoie dans SURF_SEJOUR ;
--   3. l'ordre : le worker applique les équipements EN DERNIER à chaque étape
--      (applyExactHektorWizardFields, console_job_worker.js:10701-10862), ils
--      gagnent donc sur les champs à plat. La version 1 faisait l'inverse.
--   + les noms « à plat » que les autres écrans lisent dans la fiche détaillée
--     (surface_habitable_detail, prix_publique, texte_principal_titre, …).
--
-- CE QUE FAIT CE PATCH : il REMPLACE la seule fonction neuve
-- app_annonce_corps_de_naissance. La création d'annonce n'est PAS retouchée (son
-- bloc appelle la fonction par son nom). L'interrupteur n'est pas touché.
-- ⛔ GARDE : la fonction n'est remplacée que si son empreinte est celle de la
--    version 1 (2e33944a…). Sinon : ARRÊT, rien n'est écrit.
-- RETOUR ARRIÈRE : supabase/patch_8a2b_annonce_tous_les_champs_2026-10-21_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

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

SELECT 1 AS "#", 'la version 2 est posee, empreinte de la repetition (944db16b)' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_annonce_corps_de_naissance(jsonb)'::regprocedure), chr(13), '')) = '944db16babc10031b567eb535f74be8b'
            THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'interrupteur INCHANGE (eteint)',
       CASE WHEN (SELECT value FROM public.app_setting WHERE key = 'annonce_nait_complete') = 'off' THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'eteint : la fonction rend NULL',
       CASE WHEN public.app_annonce_corps_de_naissance('{"title":"x"}'::jsonb) IS NULL THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'la creation d''annonce n''est PAS retouchee (a5e70b57)',
       CASE WHEN md5(replace(pg_get_functiondef('public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)'::regprocedure), chr(13), '')) = 'a5e70b5734876f74ecd0083681a1ebe8'
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'la fonction reste FERMEE a anon et authenticated',
       CASE WHEN NOT has_function_privilege('anon', 'public.app_annonce_corps_de_naissance(jsonb)', 'EXECUTE')
             AND NOT has_function_privilege('authenticated', 'public.app_annonce_corps_de_naissance(jsonb)', 'EXECUTE')
            THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
