-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE 8a-A — le commentaire au clic                           22/10/2026
-- Il rend à app_edit_contact_optimistic son texte du 21/10 (empreinte 79d39e0e),
-- par les MÊMES ancres, et retire l'interrupteur. Il ne touche aucune donnée : les
-- commentaires déjà écrits au clic restent (la relecture de Hektor les confirme ou
-- les remplace, comme avant le patch).
-- Pour seulement SUSPENDRE, inutile de jouer ce fichier : éteindre l'interrupteur.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $retour$
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
    IF md5(d) = '79d39e0e506d8afd3224fe20624598b3' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_edit_contact_optimistic porte deja l''empreinte du 21/10 (79d39e0e).';
        RETURN;
    END IF;
    IF md5(d) <> 'eb93494b0856706f1f0426da7571d306' THEN
        RAISE EXCEPTION '%', format('ARRET : app_edit_contact_optimistic a l''empreinte %s, ni eb93494b (posee) ni 79d39e0e (d''avant). Rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : le texte neuf %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '79d39e0e506d8afd3224fe20624598b3' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte rendu a l''empreinte %s, attendu 79d39e0e. Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
$retour$;

delete from public.app_setting where key = 'contact_commentaire_au_clic';

SELECT 1 AS "#", 'app_edit_contact_optimistic a retrouve l''empreinte 79d39e0e' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_edit_contact_optimistic(text,jsonb,integer)'::regprocedure), chr(13), '')) = '79d39e0e506d8afd3224fe20624598b3' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'contact_commentaire_au_clic') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
