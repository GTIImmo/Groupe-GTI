-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE 1b — l'acquéreur sous son numéro Hektor                   22/10/2026
-- Il rend à app_change_annonce_status_optimistic son texte de R1 (empreinte caab6b6c), par
-- les MÊMES ancres, et retire l'interrupteur. Il ne touche aucune donnée.
-- Pour seulement SUSPENDRE, inutile de jouer ce fichier : éteindre l'interrupteur.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $retour$
DECLARE
    d text := replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  v_nait_complete boolean := false;$a1$, chr(13), ''),
        replace($a2$    select c.app_contact_id into v_acquereur_app$a2$, chr(13), ''),
        replace($a3$  -- ─── 2.6 : LA LISTE DES ACQUEREURS, ET LEURS NOMS ───$a3$, chr(13), ''),
        replace($a4$       public.app_chaine_pour(d.hektor_annonce_id::bigint, v_acquereur, v_kind, v_affaire_id),$a4$, chr(13), ''),
        replace($a5$       v_acquereur,$a5$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  v_nait_complete boolean := false;
  -- 1b 22/10/2026 : l'acquereur sous son numero Hektor (interrupteur affaire_acquereur_numero_hektor)
  v_acquereur_cible text;$n1$, chr(13), ''),
        replace($n2$    select c.app_contact_id, nullif(btrim(coalesce(c.hektor_target_id, '')), '') into v_acquereur_app, v_acquereur_cible$n2$, chr(13), ''),
        replace($n3$  -- ─── 1b (22/10/2026, chantier 8) : L'ACQUEREUR SOUS SON NUMERO HEKTOR ───
  -- `hektor_acquereur_id` est la CLE du rapprochement de nuit (affaire_ledger.py, par
  -- acquereur) et de la chaine (app_chaine_pour la compare aux lignes venues de Hektor).
  -- Or l'ecran envoie tantot NOTRE identite (la recherche de contacts : 20000008 le 22/10),
  -- tantot le numero Hektor (605717 le 13/10). Les 62 288 contacts ont deux numeros
  -- differents : l'identite y faisait echouer le rapprochement (doublon de nuit), le
  -- numero Hektor y faisait perdre le lien vers notre contact (app_contact_id vide).
  -- Allume : on reconnait les DEUX (identite d'abord, numero Hektor ensuite), on range le
  -- numero Hektor ici et notre identite dans app_contact_id. Inconnu : on garde ce qui est
  -- venu, on n'invente rien. Le worker n'est PAS concerne : il lit la charge et traduit
  -- lui-meme. Eteint : comportement d'avant.
  if coalesce((select s.value from public.app_setting s
                where s.key = 'affaire_acquereur_numero_hektor'), 'off') = 'on' then
    if v_acquereur is not null and v_acquereur_app is null then
      select c.app_contact_id, nullif(btrim(coalesce(c.hektor_target_id, '')), '')
        into v_acquereur_app, v_acquereur_cible
        from app_contact_current c
       where c.hektor_target_id = v_acquereur
       limit 1;
    end if;
    v_acquereur_cible := coalesce(v_acquereur_cible, v_acquereur);
  else
    v_acquereur_cible := v_acquereur;
  end if;

  -- ─── 2.6 : LA LISTE DES ACQUEREURS, ET LEURS NOMS ───$n3$, chr(13), ''),
        replace($n4$       public.app_chaine_pour(d.hektor_annonce_id::bigint, v_acquereur_cible, v_kind, v_affaire_id),$n4$, chr(13), ''),
        replace($n5$       v_acquereur_cible,         -- 1b : le numero Hektor (allume) ou ce qui est venu (eteint)$n5$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = 'caab6b6c38091ba5b087f8819147756f' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_change_annonce_status_optimistic porte deja l''empreinte de R1 (caab6b6c).';
        RETURN;
    END IF;
    IF md5(d) <> 'f9d024471d0740fa21fffa532e9aa2ae' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, ni f9d02447 (posee) ni caab6b6c (R1). Rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : le texte neuf %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> 'caab6b6c38091ba5b087f8819147756f' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte rendu a l''empreinte %s, attendu caab6b6c. Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
$retour$;

delete from public.app_setting where key = 'affaire_acquereur_numero_hektor';

SELECT 1 AS "#", 'app_change_annonce_status_optimistic a retrouve l''empreinte caab6b6c' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) = 'caab6b6c38091ba5b087f8819147756f' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'affaire_acquereur_numero_hektor') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
