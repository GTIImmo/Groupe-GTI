-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ — LES PERSONNES D'UNE TRANSACTION PORTENT NOS DEUX NUMÉROS (pièce 1)   24/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Étude : notice/ETUDE_NUMEROS_PERSONNES_REGISTRE_TRANSACTIONS_2026-10-24.md (§8 à §10). Règle de Frédéric :
-- « l'id Hektor pour communiquer avec Hektor, et mon id app pour le registre ».
--
-- LE DÉFAUT (mesuré le 24/10). app_acquereurs_json fabrique la liste des personnes d'une transaction : les acquéreurs à la
-- CRÉATION (le principal en tête), les mandants à la MODIFICATION. Il ne trouvait une personne que par NOTRE
-- identité ; passée sous son numéro de Hektor — ce que la modale préremplit depuis le registre — elle
-- DISPARAISSAIT de la liste, sans un mot (['605976'] → 0 personne ; ['20000015'] → 1). Et `id` changeait de sens
-- dans la journée : notre identité au clic, le numéro de Hektor quelques minutes après (relecture du worker), puis
-- la nuit.
--
-- CE QUE FAIT CE PATCH — UNE ANCRE (le corps de la fonction), ÉTEINT AU DÉPART :
--   1. un INTERRUPTEUR, app_setting 'affaire_personnes_deux_numeros', posé à 'off' ;
--   2. allumé : la personne est trouvée par ses DEUX numéros ; `id` = numéro de HEKTOR (comme la relecture et la
--      nuit) ; `app_contact_id` = le NÔTRE ; une même personne donnée deux fois ne sort qu'une fois ; inconnue :
--      rien. Éteint : exactement le texte d'avant.
--   Rien d'autre ne change : le principal (`hektor_acquereur_id` / `app_contact_id`, 1b), le chaînage, le worker.
--
-- ⛔ GARDE : empreinte 1b82fdda exigée, ancre trouvée UNE fois, texte neuf 69904a53 CALCULÉ D'AVANCE.
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'affaire_personnes_deux_numeros';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'affaire_personnes_deux_numeros';
-- RETOUR ARRIÈRE COMPLET : supabase/patch_personnes_deux_numeros_2026-10-24_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('affaire_personnes_deux_numeros', 'off',
        'Chantier 8 / 24/10/2026 : on = les personnes d''une transaction (acquereurs a la creation, mandants a la modification) sont trouvees par leurs DEUX numeros et portent les deux : id = numero de Hektor, app_contact_id = le notre. off = comportement d''avant (une personne passee sous son numero de Hektor disparaissait). Voir supabase/patch_personnes_deux_numeros_2026-10-24.sql.',
        now())
on conflict (key) do nothing;

-- 2. LA FONCTION
DO $pose$
DECLARE
    d text := replace(pg_get_functiondef('public.app_acquereurs_json(text[])'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'id',        c.hektor_contact_id,
        'civilite',  coalesce(c.civilite, ''),
        'nom',       coalesce(c.nom, ''),
        'prenom',    coalesce(c.prenom, ''),
        'coordonnees', jsonb_build_object(
          'email',    coalesce(c.email, ''),
          'portable', coalesce(c.phone_primary, '')
        )
      )
      order by array_position(p_ids, c.hektor_contact_id)
    ),
    '[]'::jsonb)
  from app_contact_current c
  where c.hektor_contact_id = any(p_ids);$a1$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  -- ⑧ (24/10/2026) : LES PERSONNES D'UNE TRANSACTION PORTENT NOS DEUX NUMEROS.
  -- Regle de Frederic : « l'id Hektor pour communiquer avec Hektor, mon id app pour le registre ».
  -- AVANT : on ne trouvait une personne que par NOTRE identite (`hektor_contact_id`, nom trompeur depuis
  --   la bascule du 23/09) ; passee sous son numero de Hektor -- ce que la modale preremplit depuis le
  --   registre -- elle DISPARAISSAIT de la liste, en silence (mesure : ['605976'] -> 0 personne).
  -- ALLUME : on la trouve par ses DEUX numeros ; `id` porte le numero de HEKTOR, comme la relecture du
  --   worker et la nuit le rangent deja (une seule signification pour `id`, du clic au lendemain) ;
  --   `app_contact_id` porte le NOTRE. Une meme personne donnee deux fois ne sort qu'une fois.
  --   Inconnue : rien (on n'invente pas). Sans numero de Hektor encore : `id` garde notre identite.
  -- Sert a la creation (acquereurs, principal en tete) et a la modification (mandants).
  -- Interrupteur 'affaire_personnes_deux_numeros'. Etude : ETUDE_NUMEROS_PERSONNES_..._2026-10-24.md.
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'id',        case when s.allume
                          then coalesce(nullif(btrim(c.hektor_target_id), ''), c.hektor_contact_id)
                          else c.hektor_contact_id end,
        'civilite',  coalesce(c.civilite, ''),
        'nom',       coalesce(c.nom, ''),
        'prenom',    coalesce(c.prenom, ''),
        'coordonnees', jsonb_build_object(
          'email',    coalesce(c.email, ''),
          'portable', coalesce(c.phone_primary, '')
        )
      ) || case when s.allume then jsonb_build_object('app_contact_id', c.app_contact_id) else '{}'::jsonb end
      order by coalesce(array_position(p_ids, c.hektor_contact_id),
                        case when s.allume then array_position(p_ids, c.hektor_target_id) end)
    ),
    '[]'::jsonb)
  from app_contact_current c
  cross join (select coalesce((select v.value from public.app_setting v
                                where v.key = 'affaire_personnes_deux_numeros'), 'off') = 'on' as allume) s
  where c.hektor_contact_id = any(p_ids)
     or (s.allume and c.hektor_target_id = any(p_ids));$n1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '69904a53433eacf9f06ce2bbfa9ff889' THEN
        RAISE NOTICE '%', 'Deja pose : app_acquereurs_json porte deja l''empreinte 69904a53. Rien n''est ecrit.'; RETURN;
    END IF;
    IF md5(d) <> '1b82fddad4387a5965b6cf16c49a9b1a' THEN
        RAISE EXCEPTION '%', format('ARRET : app_acquereurs_json a l''empreinte %s, attendu 1b82fdda. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_acquereurs_json, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '69904a53433eacf9f06ce2bbfa9ff889' THEN
        RAISE EXCEPTION '%', format('ARRET : app_acquereurs_json, le texte rendu a l''empreinte %s, attendu 69904a53 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_acquereurs_json(text[])'::regprocedure), chr(13), '')) <> '69904a53433eacf9f06ce2bbfa9ff889' THEN
        RAISE EXCEPTION '%', 'ARRET : app_acquereurs_json, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose$;

-- 3. LES CONTRÔLES — tous doivent dire OK
SELECT 1 AS "#", 'app_acquereurs_json porte l''empreinte 69904a53' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_acquereurs_json(text[])'::regprocedure), chr(13), '')) = '69904a53433eacf9f06ce2bbfa9ff889' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'app_acquereurs_json : toujours SECURITY DEFINER, toujours fermee a authenticated',
       CASE WHEN (SELECT prosecdef FROM pg_proc WHERE oid = 'public.app_acquereurs_json(text[])'::regprocedure) AND NOT has_function_privilege('authenticated', 'public.app_acquereurs_json(text[])', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'l''interrupteur existe, ETEINT',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'affaire_personnes_deux_numeros' AND value = 'off') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'eteint : le comportement d''avant (605976 introuvable, 20000015 trouve sans app_contact_id)',
       CASE WHEN jsonb_array_length(public.app_acquereurs_json(array['605976'])) = 0
             AND NOT ((public.app_acquereurs_json(array['20000015'])->0) ? 'app_contact_id') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
