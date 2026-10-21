-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · PIÈCE 2 (8a, L10-2d) — L'ANNONCE NAÎT COMPLÈTE         21/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md (pièce 2)
--
-- LE DÉFAUT, mesuré en réel le 21/10 (estimation d'essai 10000001 / 63329) :
--   à la création, la fiche ne reçoit que 11 colonnes et AUCUNE fiche détaillée.
--   Pendant ~90 s l'annonce est INTROUVABLE (la recherche lit `search_text`, que la
--   création n'écrit pas ; la liste trie par `date_enregistrement_annonce`, idem),
--   et toute la saisie ne vit que dans la demande au worker -- qui n'est pas un lieu
--   sûr (nettoyages du 21/08 et du 15/10). Le jour de la coupure, plus personne ne
--   renverrait la fiche.
--
-- CE QUE FAIT CE PATCH — ADDITIF, derrière l'interrupteur 'annonce_nait_complete' (off) :
--   1. une fonction NEUVE, app_annonce_corps_de_naissance(jsonb), qui traduit la
--      saisie : les équipements (déjà aux noms de Hektor) + les champs principaux,
--      vers les noms que la fiche lit EN PREMIER (le calque app_optimistic_overlay,
--      wizardDetailValue dans App.tsx) ; le texte de recherche, construit comme le
--      serveur (build_search_text de push_upgrade_to_supabase.py) ; la date
--      d'enregistrement ; le TYPE en CODE (hektor_id_type -- jamais le libellé).
--      Elle rend NULL si l'interrupteur est éteint ;
--   2. dans app_create_annonce_job_optimistic, juste APRÈS l'insertion de la fiche,
--      un bloc À PART qui complète la fiche et pose une fiche détaillée de départ
--      (le calque + une copie de la saisie, sans les données du mandant).
--      Un échec dans ce bloc ne peut ni empêcher ni défaire la création.
--   La relecture de Hektor REMPLACE ensuite la fiche détaillée par la sienne
--   (comme aujourd'hui) ; le run de nuit l'ÉPARGNE tant que le serveur ne connaît pas
--   l'annonce (C.9-c) ; la descente de 07:45 la copie (sa doublure).
--   Ce que seul Hektor fabrique n'est PAS inventé : numéro Hektor, numéro de
--   dossier, diffusable, blocs équipements / diagnostics / photos.
--
-- ⛔ GARDES : la fonction de création n'est modifiée que si son empreinte est celle
--    du 21/10 (3407a05c…) et si le bloc n'y est pas déjà. Sinon : ARRÊT, rien n'est écrit.
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'annonce_nait_complete';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'annonce_nait_complete';
-- RETOUR ARRIÈRE COMPLET : supabase/patch_8a2_annonce_nait_complete_2026-10-21_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('annonce_nait_complete', 'off',
        'Chantier 8 / 8a piece 2 21/10/2026 : on = une annonce creee dans l''app recoit tout de suite sa fiche detaillee de depart (voir supabase/patch_8a2_annonce_nait_complete_2026-10-21.sql). off = comportement d''avant.',
        now())
on conflict (key) do nothing;

-- 2. LA FONCTION NEUVE
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

-- 3. LE BLOC, DANS LA CRÉATION
DO $patch$
DECLARE
    bloc text := $blk$
  -- === CHANTIER 8 / 8a piece 2 (21/10/2026) : L'ANNONCE NAIT COMPLETE ===
  -- La fiche qu'on vient de poser recoit aussi ce qui la rend TROUVABLE (texte de
  -- recherche, date d'enregistrement, type en code, adresse), et une fiche detaillee
  -- de depart : le calque que l'ecran lit en premier + la saisie telle quelle.
  -- La relecture de Hektor la remplacera par la sienne (~90 s).
  -- Interrupteur : app_setting 'annonce_nait_complete'. Eteint, la fonction
  -- app_annonce_corps_de_naissance rend NULL et ce bloc ne touche rien.
  -- Un echec ici ne doit JAMAIS empecher ni defaire la creation : bloc a part.
  begin
    update public.app_dossier_current d set
      type_bien                   = coalesce(n.c->'colonnes'->>'type_bien',                d.type_bien),
      adresse_detail              = coalesce(n.c->'colonnes'->>'adresse_detail',           d.adresse_detail),
      code_postal_prive_detail    = coalesce(n.c->'colonnes'->>'code_postal_prive_detail', d.code_postal_prive_detail),
      ville_privee_detail         = coalesce(n.c->'colonnes'->>'ville_privee_detail',      d.ville_privee_detail),
      date_enregistrement_annonce = coalesce(d.date_enregistrement_annonce, n.c->'colonnes'->>'date_enregistrement_annonce'),
      search_text                 = coalesce(n.c->'colonnes'->>'search_text',              d.search_text)
    from (select public.app_annonce_corps_de_naissance(draft_payload) as c) n
    where d.app_dossier_id = v_id
      and n.c is not null;

    insert into public.app_dossier_detail_current
      (app_dossier_id, hektor_annonce_id, source_updated_at, source_hash, detail_payload_json, refreshed_at)
    select v_id, null, null, 'c9e3:' || p_token::text, (n.c->'detail')::text, now()
      from (select public.app_annonce_corps_de_naissance(draft_payload) as c) n
     where n.c is not null
    on conflict (app_dossier_id) do nothing;
  exception when others then
    raise warning 'annonce_nait_complete : corps de naissance non pose pour % (%)', v_id, sqlerrm;
  end;
  -- === fin 8a piece 2 ===
$blk$;
    marque   text := 'CHANTIER 8 / 8a piece 2 (21/10/2026)';
    porte    text := 'public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)';
    attendue text := '3407a05cd7d1125b9320e468f4e0cf4f';
    ancre    text := $a$      'c9e3:' || p_token::text,
      now());
$a$;
    src      text;
    combien  int;
BEGIN
    bloc  := replace(bloc, chr(13), '');
    ancre := replace(ancre, chr(13), '');
    src   := replace(pg_get_functiondef(porte::regprocedure), chr(13), '');
    IF position(marque in src) > 0 THEN
        RAISE EXCEPTION '%', 'ARRET : le bloc 8a piece 2 est DEJA dans la creation d''annonce. Rien n''est ecrit.';
    END IF;
    IF md5(src) <> attendue THEN
        RAISE EXCEPTION '%', format('ARRET : la creation d''annonce a change depuis le 21/10 (empreinte %s, attendue %s). Rien n''est ecrit.',
                                    md5(src), attendue);
    END IF;
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre apparait %s fois (1 attendue). Rien n''est ecrit.', combien);
    END IF;
    EXECUTE replace(src, ancre, ancre || bloc);
END
$patch$;

-- 4. LES CONTROLES
SELECT 1 AS "#", 'interrupteur pose, ETEINT' AS controle,
       CASE WHEN (SELECT value FROM public.app_setting WHERE key = 'annonce_nait_complete') = 'off'
            THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'le bloc est dans la creation d''annonce, une fois',
       CASE WHEN (SELECT (length(prosrc) - length(replace(prosrc, 'CHANTIER 8 / 8a piece 2 (21/10/2026)', ''))) / 36
                    FROM pg_proc WHERE oid = 'public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)'::regprocedure) = 1
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'interrupteur eteint : la fonction neuve rend NULL',
       CASE WHEN public.app_annonce_corps_de_naissance('{"title":"x"}'::jsonb) IS NULL
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'droits de la creation INCHANGES (authenticated oui, anon non)',
       CASE WHEN has_function_privilege('authenticated', 'public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)', 'EXECUTE')
             AND NOT has_function_privilege('anon', 'public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)', 'EXECUTE')
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'la fonction neuve est FERMEE a anon et authenticated',
       CASE WHEN NOT has_function_privilege('anon', 'public.app_annonce_corps_de_naissance(jsonb)', 'EXECUTE')
             AND NOT has_function_privilege('authenticated', 'public.app_annonce_corps_de_naissance(jsonb)', 'EXECUTE')
            THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
