-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE 8a PIÈCE 2 bis — la fonction revient à sa VERSION 1
--                                                                    21/10/2026
-- ⭐ La preuve est l'EMPREINTE : après le retour, la fonction doit redonner
--    exactement celle de la version 1 (2e33944a…), sinon tout est annulé.
-- Il ne touche ni la création d'annonce, ni l'interrupteur.
-- Pour seulement SUSPENDRE, inutile de jouer ce fichier : éteindre l'interrupteur.
--   update public.app_setting set value = 'off', updated_at = now() where key = 'annonce_nait_complete';
-- Texte de la version 1 RECOPIÉ depuis patch_8a2_annonce_nait_complete_2026-10-21.sql.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

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

SELECT 1 AS "#", 'la fonction est revenue a la version 1 (2e33944a)' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_annonce_corps_de_naissance(jsonb)'::regprocedure), chr(13), '')) = '2e33944ae87333f8062e6b5ff7e7eebf'
            THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'la fonction reste FERMEE a anon et authenticated',
       CASE WHEN NOT has_function_privilege('anon', 'public.app_annonce_corps_de_naissance(jsonb)', 'EXECUTE')
             AND NOT has_function_privilege('authenticated', 'public.app_annonce_corps_de_naissance(jsonb)', 'EXECUTE')
            THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
