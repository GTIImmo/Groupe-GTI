-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · 8a-A — LE COMMENTAIRE D'UN CONTACT S'ÉCRIT CHEZ NOUS AU CLIC    22/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md (« 8a, fin — LA MODIFICATION DE CONTACT »)
--
-- LE DÉFAUT (audit du 22/10). En modifiant un contact, l'écran envoie le commentaire
-- (`comments`) à app_edit_contact_optimistic, mais elle ne le connaît pas : il part chez
-- Hektor et ne revient chez nous qu'à la relecture, ~11 minutes après (10 min d'attente
-- voulue + ~40 s). Hektor parti, il ne s'afficherait jamais. Les 12 autres champs, eux,
-- s'écrivent au clic.
--
-- CE QUE FAIT CE PATCH — CHIRURGICAL, TROIS ANCRES D'UNE LIGNE :
--   1. un INTERRUPTEUR, app_setting 'contact_commentaire_au_clic', posé à 'off' ;
--   2. dans app_edit_contact_optimistic : lu au début ; allumé, `comments` (ou
--      `commentaires`) s'écrit dans la colonne commentaires, et sa valeur d'avant entre
--      dans la photo (base_snapshot) comme les 12 autres. ÉTEINT : RIEN NE CHANGE.
--   Rien d'autre n'est touché : le travail pour Hektor, l'attente, la garde
--   anti-écrasement (elle ne lit que _date_maj) et la relecture restent ce qu'ils sont.
--
-- ⛔ GARDE : la fonction n'est modifiée que si son empreinte est 79d39e0e (relevée le
--    21/10 et le 22/10), chaque ancre trouvée UNE fois, et le texte neuf porte
--    l'empreinte eb93494b CALCULÉE D'AVANCE. Sinon : ARRÊT, rien n'est écrit.
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'contact_commentaire_au_clic';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'contact_commentaire_au_clic';
-- RETOUR ARRIÈRE COMPLET : supabase/patch_8a4_contact_commentaire_au_clic_2026-10-22_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('contact_commentaire_au_clic', 'off',
        'Chantier 8 / 8a-A 22/10/2026 : on = le commentaire saisi en modifiant un contact s''ecrit chez nous au clic (voir supabase/patch_8a4_contact_commentaire_au_clic_2026-10-22.sql). off = comportement d''avant (il n''arrive qu''au retour de Hektor).',
        now())
on conflict (key) do nothing;

-- 2. LA FONCTION, PAR SES TROIS ANCRES
DO $pose$
DECLARE
    d text := replace(pg_get_functiondef('public.app_edit_contact_optimistic(text,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  k text;$a1$, chr(13), ''),
        replace($a2$  if edit_fields is null or edit_fields = '{}'::jsonb then raise exception 'no_fields' using errcode='22023'; end if;$a2$, chr(13), ''),
        replace($a3$    marital_status  = case when ef ? 'marital_status'  then ef->>'marital_status'  else marital_status end$a3$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  k text;
  v_commentaire_au_clic boolean := false;  -- 8a-A 22/10 : interrupteur contact_commentaire_au_clic$n1$, chr(13), ''),
        replace($n2$  if edit_fields is null or edit_fields = '{}'::jsonb then raise exception 'no_fields' using errcode='22023'; end if;

  -- 8a-A (22/10/2026) : LE COMMENTAIRE S'ECRIT CHEZ NOUS AU CLIC. Avant, l'ecran l'envoyait
  -- (`comments`) mais seule la relecture de Hektor le posait, ~11 min apres. Interrupteur
  -- eteint : rien ne change. Allume : `comments` (ou `commentaires`) -> colonne commentaires,
  -- et sa valeur d'avant entre dans la photo (base_snapshot), comme les 12 autres.
  select lower(trim(coalesce(s.value, ''))) in ('on', '1', 'true', 'oui') into v_commentaire_au_clic
    from public.app_setting s where s.key = 'contact_commentaire_au_clic';
  v_commentaire_au_clic := coalesce(v_commentaire_au_clic, false);
  if v_commentaire_au_clic then
    alias_map := alias_map || '{"commentaires":"comments"}'::jsonb;
    col_map := col_map || '{"comments":"commentaires"}'::jsonb;
  end if;$n2$, chr(13), ''),
        replace($n3$    marital_status  = case when ef ? 'marital_status'  then ef->>'marital_status'  else marital_status end,
    commentaires    = case when v_commentaire_au_clic and ef ? 'comments' then ef->>'comments' else commentaires end$n3$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = 'eb93494b0856706f1f0426da7571d306' THEN
        RAISE NOTICE '%', 'Deja pose : app_edit_contact_optimistic porte deja l''empreinte eb93494b. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> '79d39e0e506d8afd3224fe20624598b3' THEN
        RAISE EXCEPTION '%', format('ARRET : app_edit_contact_optimistic a l''empreinte %s, attendu 79d39e0e (21/10). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : l''ancre %s est trouvee %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> 'eb93494b0856706f1f0426da7571d306' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte neuf a l''empreinte %s, attendu eb93494b (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_edit_contact_optimistic(text,jsonb,integer)'::regprocedure), chr(13), '')) <> 'eb93494b0856706f1f0426da7571d306' THEN
        RAISE EXCEPTION '%', 'ARRET : apres la pose, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose$;

-- 3. LES CONTRÔLES — tous doivent dire OK
SELECT 1 AS "#", 'app_edit_contact_optimistic porte l''empreinte eb93494b' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_edit_contact_optimistic(text,jsonb,integer)'::regprocedure), chr(13), '')) = 'eb93494b0856706f1f0426da7571d306' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur existe, ETEINT',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'contact_commentaire_au_clic' AND value = 'off') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'les droits d''appel sont inchanges (authenticated peut appeler)',
       CASE WHEN has_function_privilege('authenticated', 'public.app_edit_contact_optimistic(text,jsonb,integer)', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
