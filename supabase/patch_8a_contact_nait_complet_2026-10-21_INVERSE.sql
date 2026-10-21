-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE 8a — les deux portes de création reviennent à l'identique
--                                                                    21/10/2026
-- ⭐ La preuve est l'EMPREINTE : chaque fonction n'est réécrite que si, une fois
--    le bloc retiré, elle redonne EXACTEMENT celle du 21/10 avant le patch
--    (f1563f57… et e787461f…). Sinon : ARRÊT, rien n'est écrit.
-- ⚠ Il ne juge que SA part : les contacts déjà créés avec les champs en plus les
--   gardent (Hektor les a confirmés depuis, à la relecture).
-- Pour seulement SUSPENDRE, inutile de jouer ce fichier : éteindre l'interrupteur.
--   update public.app_setting set value = 'off', updated_at = now() where key = 'contact_nait_complet';
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $inverse$
DECLARE
    bloc text := $blk$
  -- === CHANTIER 8 / 8a (21/10/2026) : LE CONTACT NAIT COMPLET ===
  -- La ligne qu'on vient de poser recoit aussi ce que l'ecran a SAISI et qui a
  -- deja sa colonne (civilite, 2e telephone, adresse, code postal, ville,
  -- naissance, lieu, situation, commentaire). Hektor la remplacera par sa version
  -- a la relecture (~40 s) ; naissance, lieu et situation y sont reinjectes.
  -- Interrupteur : app_setting 'contact_nait_complet'. Eteint, la fonction
  -- app_contact_champs_naissance rend NULL et cette mise a jour ne touche rien.
  -- Un echec ici ne doit JAMAIS empecher ni defaire la creation : bloc a part.
  begin
    update public.app_contact_current c set
      civilite        = coalesce(n.v->>'civilite',        c.civilite),
      phone_secondary = coalesce(n.v->>'phone_secondary', c.phone_secondary),
      adresse         = coalesce(n.v->>'adresse',         c.adresse),
      code_postal     = coalesce(n.v->>'code_postal',     c.code_postal),
      ville           = coalesce(n.v->>'ville',           c.ville),
      birth_date      = coalesce(n.v->>'birth_date',      c.birth_date),
      birth_place     = coalesce(n.v->>'birth_place',     c.birth_place),
      marital_status  = coalesce(n.v->>'marital_status',  c.marital_status),
      commentaires    = coalesce(n.v->>'commentaires',    c.commentaires)
    from (select public.app_contact_champs_naissance(contact_payload) as v) n
    where c.hektor_contact_id = v_identite
      and n.v is not null;
  exception when others then
    raise warning 'contact_nait_complet : champs en plus non poses pour % (%)', v_identite, sqlerrm;
  end;
  -- === fin 8a ===
$blk$;
    marque  text := 'CHANTIER 8 / 8a (21/10/2026)';
    portes  text[][] := array[
      array['public.app_create_contact_optimistic(jsonb,integer)',
            'f1563f572a8f2b4ea985e5f111144b37',
            $a1$    '[]'::jsonb, 'app_creation_' || v_identite, now());
$a1$],
      array['public.app_create_mandant_contact_optimistic(bigint,text,jsonb,integer)',
            'e787461fd5efed34663e93ba5c92fea6',
            $a2$    on conflict (app_contact_id, hektor_annonce_id) do nothing;
  exception when others then
    null;
  end;
$a2$]];
    i       int;
    src     text;
    ancre   text;
    retour  text;
BEGIN
    bloc := replace(bloc, chr(13), '');
    FOR i IN 1 .. array_length(portes, 1) LOOP
        src   := replace(pg_get_functiondef(portes[i][1]::regprocedure), chr(13), '');
        ancre := replace(portes[i][3], chr(13), '');
        IF position(marque in src) = 0 THEN
            RAISE NOTICE '%', format('Rien a retirer de %s : le bloc 8a n''y est pas.', portes[i][1]);
            CONTINUE;
        END IF;
        retour := replace(src, ancre || bloc, ancre);
        IF md5(retour) <> portes[i][2] THEN
            RAISE EXCEPTION '%', format('ARRET : sans le bloc, %s ne redonne PAS l''empreinte du 21/10 (%s au lieu de %s). Elle a change depuis le patch : rien n''est ecrit.',
                                        portes[i][1], md5(retour), portes[i][2]);
        END IF;
        EXECUTE retour;
    END LOOP;
END
$inverse$;

drop function if exists public.app_contact_champs_naissance(jsonb);
delete from public.app_setting where key = 'contact_nait_complet';

SELECT 1 AS "#", 'porte CONTACT revenue a l''empreinte du 21/10' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_create_contact_optimistic(jsonb,integer)'::regprocedure), chr(13), ''))
                 = 'f1563f572a8f2b4ea985e5f111144b37' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'porte MANDANT revenue a l''empreinte du 21/10',
       CASE WHEN md5(replace(pg_get_functiondef('public.app_create_mandant_contact_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), ''))
                 = 'e787461fd5efed34663e93ba5c92fea6' THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'la fonction neuve est retiree',
       CASE WHEN to_regprocedure('public.app_contact_champs_naissance(jsonb)') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'contact_nait_complet') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'droits des deux portes INCHANGES (authenticated oui, anon non)',
       CASE WHEN (SELECT bool_and(has_function_privilege('authenticated', oid, 'EXECUTE')
                                  AND NOT has_function_privilege('anon', oid, 'EXECUTE'))
                    FROM pg_proc WHERE proname IN ('app_create_contact_optimistic','app_create_mandant_contact_optimistic'))
            THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
