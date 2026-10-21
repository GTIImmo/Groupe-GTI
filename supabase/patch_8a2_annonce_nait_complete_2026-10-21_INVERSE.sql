-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE 8a PIÈCE 2 — la création d'annonce revient à l'identique
--                                                                    21/10/2026
-- ⭐ La preuve est l'EMPREINTE : la fonction n'est réécrite que si, une fois le
--    bloc retiré, elle redonne EXACTEMENT celle du 21/10 avant le patch
--    (3407a05c…). Sinon : ARRÊT, rien n'est écrit.
-- ⚠ Il ne juge que SA part : les annonces déjà nées avec leur fiche de départ la
--   gardent (la relecture de Hektor l'a remplacée par la sienne depuis).
-- Pour seulement SUSPENDRE, inutile de jouer ce fichier : éteindre l'interrupteur.
--   update public.app_setting set value = 'off', updated_at = now() where key = 'annonce_nait_complete';
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $inverse$
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
    retour   text;
BEGIN
    bloc  := replace(bloc, chr(13), '');
    ancre := replace(ancre, chr(13), '');
    src   := replace(pg_get_functiondef(porte::regprocedure), chr(13), '');
    IF position(marque in src) = 0 THEN
        RAISE NOTICE '%', 'Rien a retirer : le bloc 8a piece 2 n''est pas dans la creation d''annonce.';
    ELSE
        retour := replace(src, ancre || bloc, ancre);
        IF md5(retour) <> attendue THEN
            RAISE EXCEPTION '%', format('ARRET : sans le bloc, la creation d''annonce ne redonne PAS l''empreinte du 21/10 (%s au lieu de %s). Elle a change depuis le patch : rien n''est ecrit.',
                                        md5(retour), attendue);
        END IF;
        EXECUTE retour;
    END IF;
END
$inverse$;

drop function if exists public.app_annonce_corps_de_naissance(jsonb);
delete from public.app_setting where key = 'annonce_nait_complete';

SELECT 1 AS "#", 'la creation d''annonce est revenue a l''empreinte du 21/10' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)'::regprocedure), chr(13), ''))
                 = '3407a05cd7d1125b9320e468f4e0cf4f' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'la fonction neuve est retiree',
       CASE WHEN to_regprocedure('public.app_annonce_corps_de_naissance(jsonb)') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'annonce_nait_complete') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'droits de la creation INCHANGES (authenticated oui, anon non)',
       CASE WHEN has_function_privilege('authenticated', 'public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)', 'EXECUTE')
             AND NOT has_function_privilege('anon', 'public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)', 'EXECUTE')
            THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
