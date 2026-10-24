-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — les personnes d'une transaction portent nos deux numéros   24/10/2026
-- Il rend à app_acquereurs_json son texte d'avant (1b82fdda), par la MÊME ancre, et retire l'interrupteur.
-- Il ne touche aucune donnée : les listes déjà écrites gardent leur `app_contact_id` (une clé de plus, que
-- personne ne lit encore). Pour seulement SUSPENDRE : éteindre l'interrupteur.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $retour$
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
    IF md5(d) = '1b82fddad4387a5965b6cf16c49a9b1a' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_acquereurs_json porte deja l''empreinte d''avant (1b82fdda).'; RETURN;
    END IF;
    IF md5(d) <> '69904a53433eacf9f06ce2bbfa9ff889' THEN
        RAISE EXCEPTION '%', format('ARRET : app_acquereurs_json a l''empreinte %s, attendu 69904a53. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_acquereurs_json, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '1b82fddad4387a5965b6cf16c49a9b1a' THEN
        RAISE EXCEPTION '%', format('ARRET : app_acquereurs_json, le texte rendu a l''empreinte %s, attendu 1b82fdda (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_acquereurs_json(text[])'::regprocedure), chr(13), '')) <> '1b82fddad4387a5965b6cf16c49a9b1a' THEN
        RAISE EXCEPTION '%', 'ARRET : app_acquereurs_json, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$retour$;

delete from public.app_setting where key = 'affaire_personnes_deux_numeros';

SELECT 1 AS "#", 'app_acquereurs_json a retrouve 1b82fdda' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_acquereurs_json(text[])'::regprocedure), chr(13), '')) = '1b82fddad4387a5965b6cf16c49a9b1a' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'affaire_personnes_deux_numeros') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
