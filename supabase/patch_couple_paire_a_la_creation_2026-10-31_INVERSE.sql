-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE « COUPLES · PIÈCE A » — la porte contact revient à l'identique
--                                                                    31/10/2026
-- ⭐ La preuve est l'EMPREINTE : la fonction n'est réécrite que si, une fois les
--    trois ajouts retirés, elle redonne EXACTEMENT celle du 31/10 avant le patch
--    (95fde328…). Sinon : ARRÊT, rien n'est écrit.
-- ⚠ Il ne juge que SA part : les couples déjà créés gardent leur personne 2 et leur
--   lien (ce sont des contacts réels, confirmés par Hektor depuis).
-- Pour seulement SUSPENDRE, inutile de jouer ce fichier : éteindre l'interrupteur.
--   update public.app_setting set value = 'off', updated_at = now() where key = 'couple_nait_complet';
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $inverse$
DECLARE
    porte   text := 'public.app_create_contact_optimistic(jsonb,integer)';
    empreinte text := '95fde3280af1dff65ab45596f4b3bead';
    marque  text := 'COUPLES · LA PAIRE (31/10/2026)';
    a_decl  text := $a1$  v_identite     text;
$a1$;
    n_decl  text := $n1$  v_identite_m2  text;
$n1$;
    a_bloc  text := $a2$  -- === fin 8a ===
$a2$;
    n_bloc  text := $n2$
  -- === COUPLES · LA PAIRE (31/10/2026) : LA PERSONNE 2 NAIT AVEC LA 1 ===
  -- Interrupteur : app_setting 'couple_nait_complet'. Eteint, ou si ce n'est pas
  -- un couple, app_contact_creer_conjoint rend NULL et ne touche rien.
  -- Un echec ici ne doit JAMAIS empecher ni defaire la creation : bloc a part.
  begin
    v_identite_m2 := public.app_contact_creer_conjoint(
        contact_payload, v_identite, target_email,
        nullif(trim(coalesce(contact_payload->>'target_agency_label', contact_payload->>'agence_nom', '')), ''));
  exception when others then
    v_identite_m2 := null;
    raise warning 'couple_nait_complet : personne 2 non posee pour % (%)', v_identite, sqlerrm;
  end;
  -- === fin couples ===
$n2$;
    a_job   text := $a3$          'creation_mode', coalesce(nullif(trim(contact_payload->>'creation_mode'), ''), 'contact_global_identity')),
$a3$;
    n_job   text := $n3$          'creation_mode', coalesce(nullif(trim(contact_payload->>'creation_mode'), ''), 'contact_global_identity'))
          -- COUPLES · LA PAIRE (31/10) : le numero de la personne 2, seulement s'il existe
          || case when v_identite_m2 is not null
                  then jsonb_build_object('app_identite_m2', v_identite_m2)
                  else '{}'::jsonb end,
$n3$;
    src     text;
    retour  text;
BEGIN
    src    := replace(pg_get_functiondef(porte::regprocedure), chr(13), '');
    a_decl := replace(a_decl, chr(13), '');  n_decl := replace(n_decl, chr(13), '');
    a_bloc := replace(a_bloc, chr(13), '');  n_bloc := replace(n_bloc, chr(13), '');
    a_job  := replace(a_job,  chr(13), '');  n_job  := replace(n_job,  chr(13), '');

    IF position(marque in src) = 0 THEN
        RAISE NOTICE '%', format('Rien a retirer de %s : le bloc des couples n''y est pas.', porte);
    ELSE
        retour := replace(src, a_decl || n_decl, a_decl);
        retour := replace(retour, a_bloc || n_bloc, a_bloc);
        retour := replace(retour, n_job, a_job);
        IF md5(retour) <> empreinte THEN
            RAISE EXCEPTION '%', format('ARRET : sans les ajouts, %s ne redonne PAS l''empreinte du 31/10 (%s au lieu de %s). Elle a change depuis le patch : rien n''est ecrit.',
                                        porte, md5(retour), empreinte);
        END IF;
        EXECUTE retour;
    END IF;
END
$inverse$;

drop function if exists public.app_contact_creer_conjoint(jsonb, text, text, text);
delete from public.app_setting where key = 'couple_nait_complet';

SELECT 1 AS "#", 'porte CONTACT revenue a l''empreinte du 31/10' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_create_contact_optimistic(jsonb,integer)'::regprocedure), chr(13), ''))
                 = '95fde3280af1dff65ab45596f4b3bead'
            THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'fonction neuve retiree',
       CASE WHEN to_regprocedure('public.app_contact_creer_conjoint(jsonb,text,text,text)') IS NULL
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'interrupteur retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'couple_nait_complet')
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'droits de la porte INCHANGES (authenticated oui, anon non)',
       CASE WHEN has_function_privilege('authenticated', 'public.app_create_contact_optimistic(jsonb,integer)', 'EXECUTE')
             AND NOT has_function_privilege('anon', 'public.app_create_contact_optimistic(jsonb,integer)', 'EXECUTE')
            THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
