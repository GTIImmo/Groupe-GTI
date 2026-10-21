-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · PIÈCE 1 (8a) — LE CONTACT NAÎT COMPLET                 21/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'éditeur SQL Supabase, APRES la répétition.
-- Note : notice/CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md (pièce 1)
--        notice/AUDIT_PORTES_DE_CREATION_2026-10-21.md
--
-- LE DÉFAUT. Les deux portes de création d'un contact n'écrivent chez nous que
-- 7 champs (nom, prénom, nom affiché, email, téléphone, négociateur, agence). Le
-- reste n'arrive que par la relecture de la fiche chez Hektor (~40 s), et la
-- naissance la nuit. Le jour de la coupure, ce relais n'existe plus.
--
-- CE QUE FAIT CE PATCH — ADDITIF, RIEN N'EST RETIRÉ :
--   1. un INTERRUPTEUR, app_setting 'contact_nait_complet', posé à 'off' ;
--   2. une fonction NEUVE, app_contact_champs_naissance(jsonb) : elle lit la
--      saisie et rend les 9 champs qui ont déjà une colonne — ou NULL si
--      l'interrupteur est éteint. La date de naissance jj-mm-aaaa est convertie
--      en aaaa-mm-jj ; une forme inconnue n'est PAS écrite (rien n'est inventé) ;
--   3. dans app_create_contact_optimistic ET app_create_mandant_contact_optimistic,
--      juste APRÈS l'insertion du contact, un bloc À PART qui complète la ligne.
--      Interrupteur éteint : il ne touche rien. Un échec dans ce bloc ne peut
--      ni empêcher ni défaire la création (il lève un WARNING, rien de plus).
--
-- ⛔ GARDES : chaque fonction est modifiée seulement si son empreinte est celle
--    relevée le 21/10, et si le bloc n'y est pas déjà. Sinon : ARRÊT, rien n'est écrit.
-- ⚠ La porte du mandant écrit le contact dans un bloc qui AVALE ses erreurs : le
--   bloc neuf est posé APRÈS lui, dans son propre bloc, jamais dedans.
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'contact_nait_complet';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'contact_nait_complet';
-- RETOUR ARRIÈRE COMPLET : supabase/patch_8a_contact_nait_complet_2026-10-21_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('contact_nait_complet', 'off',
        'Chantier 8 / 8a 21/10/2026 : on = un contact cree dans l''app recoit tout de suite les champs saisis qui ont une colonne (voir supabase/patch_8a_contact_nait_complet_2026-10-21.sql). off = comportement d''avant.',
        now())
on conflict (key) do nothing;

-- 2. LA FONCTION NEUVE
create or replace function public.app_contact_champs_naissance(p jsonb)
 returns jsonb
 language plpgsql
 stable
 set search_path to 'public'
as $f$
declare
  v_allume boolean;
  v_naiss  text;
  r        jsonb;
begin
  select lower(trim(coalesce(s.value, ''))) in ('on', '1', 'true', 'oui')
    into v_allume
    from public.app_setting s
   where s.key = 'contact_nait_complet';
  if not coalesce(v_allume, false) or p is null or jsonb_typeof(p) <> 'object' then
    return null;
  end if;

  -- les noms que l'ecran donne a chaque champ (memes alias que app_edit_contact_optimistic)
  r := jsonb_strip_nulls(jsonb_build_object(
    'civilite',        nullif(trim(coalesce(p->>'civilite', p->>'civility', '')), ''),
    'phone_secondary', nullif(trim(coalesce(p->>'phone_secondary', p->>'telephone2', p->>'phoneSecondary', '')), ''),
    'adresse',         nullif(trim(coalesce(p->>'address', p->>'adresse', '')), ''),
    'code_postal',     nullif(trim(coalesce(p->>'postal_code', p->>'code_postal', '')), ''),
    'ville',           nullif(trim(coalesce(p->>'city', p->>'ville', '')), ''),
    'birth_place',     nullif(trim(coalesce(p->>'birth_place', '')), ''),
    'marital_status',  nullif(trim(coalesce(p->>'marital_status', '')), ''),
    'commentaires',    nullif(trim(coalesce(p->>'comments', p->>'commentaires', '')), '')));

  -- la date de naissance : l'ecran la saisit en texte libre « jj-mm-aaaa ».
  -- La base ne porte que de l'aaaa-mm-jj (261 sur 261 le 21/10). Une autre forme
  -- n'est PAS ecrite : Hektor ou le lecteur du formulaire la donneront.
  v_naiss := nullif(trim(coalesce(p->>'birth_date', '')), '');
  if v_naiss ~ '^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$' then
    r := r || jsonb_build_object('birth_date', v_naiss);
  elsif v_naiss ~ '^(0[1-9]|[12][0-9]|3[01])[-/.](0[1-9]|1[0-2])[-/.][0-9]{4}$' then
    r := r || jsonb_build_object('birth_date',
           substr(v_naiss, 7, 4) || '-' || substr(v_naiss, 4, 2) || '-' || substr(v_naiss, 1, 2));
  end if;

  return r;
end
$f$;

-- ⚠ lecon du 13/10 : un « revoke from public » n'enleve pas un droit par defaut.
revoke all on function public.app_contact_champs_naissance(jsonb) from public;
revoke all on function public.app_contact_champs_naissance(jsonb) from anon;
revoke all on function public.app_contact_champs_naissance(jsonb) from authenticated;
grant execute on function public.app_contact_champs_naissance(jsonb) to service_role;

-- 3. LE BLOC, DANS LES DEUX PORTES
DO $patch$
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
    -- les deux portes : nom, signature, empreinte du 21/10, ancre
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
    combien int;
BEGIN
    bloc := replace(bloc, chr(13), '');
    FOR i IN 1 .. array_length(portes, 1) LOOP
        src   := replace(pg_get_functiondef(portes[i][1]::regprocedure), chr(13), '');
        ancre := replace(portes[i][3], chr(13), '');
        IF position(marque in src) > 0 THEN
            RAISE EXCEPTION '%', format('ARRET : le bloc 8a est DEJA dans %s. Rien n''est ecrit.', portes[i][1]);
        END IF;
        IF md5(src) <> portes[i][2] THEN
            RAISE EXCEPTION '%', format('ARRET : %s a change depuis le 21/10 (empreinte %s, attendue %s). Rien n''est ecrit.',
                                        portes[i][1], md5(src), portes[i][2]);
        END IF;
        combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
        IF combien <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : l''ancre de %s apparait %s fois (1 attendue). Rien n''est ecrit.',
                                        portes[i][1], combien);
        END IF;
        EXECUTE replace(src, ancre, ancre || bloc);
    END LOOP;
END
$patch$;

-- 4. LES CONTROLES
SELECT 1 AS "#", 'interrupteur pose, ETEINT' AS controle,
       CASE WHEN (SELECT value FROM public.app_setting WHERE key = 'contact_nait_complet') = 'off'
            THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'le bloc est dans la porte CONTACT, une fois',
       CASE WHEN (SELECT (length(prosrc) - length(replace(prosrc, 'CHANTIER 8 / 8a (21/10/2026)', ''))) / 28
                    FROM pg_proc WHERE oid = 'public.app_create_contact_optimistic(jsonb,integer)'::regprocedure) = 1
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'le bloc est dans la porte MANDANT, une fois',
       CASE WHEN (SELECT (length(prosrc) - length(replace(prosrc, 'CHANTIER 8 / 8a (21/10/2026)', ''))) / 28
                    FROM pg_proc WHERE oid = 'public.app_create_mandant_contact_optimistic(bigint,text,jsonb,integer)'::regprocedure) = 1
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'interrupteur eteint : la fonction neuve rend NULL',
       CASE WHEN public.app_contact_champs_naissance('{"address":"x"}'::jsonb) IS NULL
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'droits des deux portes INCHANGES (authenticated oui, anon non)',
       CASE WHEN (SELECT bool_and(has_function_privilege('authenticated', oid, 'EXECUTE')
                                  AND NOT has_function_privilege('anon', oid, 'EXECUTE'))
                    FROM pg_proc WHERE proname IN ('app_create_contact_optimistic','app_create_mandant_contact_optimistic'))
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 6, 'la fonction neuve est FERMEE a anon et authenticated',
       CASE WHEN NOT has_function_privilege('anon', 'public.app_contact_champs_naissance(jsonb)', 'EXECUTE')
             AND NOT has_function_privilege('authenticated', 'public.app_contact_champs_naissance(jsonb)', 'EXECUTE')
            THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
