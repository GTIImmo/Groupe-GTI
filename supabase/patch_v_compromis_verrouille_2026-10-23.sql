-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · V — LE COMPROMIS EST VERROUILLÉ PAR SA VENTE                     23/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md (sections 33 et 34). Décision de
-- Frédéric : « après la vente tout est verrouillé ; pour modifier quoi que ce soit sur le compromis, il faut
-- d'abord supprimer la vente ».
--
-- LE DÉFAUT (essai réel du 23/10, compromis 50136 / vente 23357 sur VA6482). L'offre est verrouillée par
-- son compromis et sa vente depuis le 16/09 (patch_offre_verrouillee) ; le COMPROMIS, lui, ne l'était par
-- rien : le modifier renvoyait son statut à Hektor et remettait un bien VENDU « Sous compromis ».
--
-- CE QUE FAIT CE PATCH — DEUX ANCRES D'UNE LIGNE, ÉTEINT AU DÉPART :
--   1. un INTERRUPTEUR, app_setting 'compromis_verrouille_par_vente', posé à 'off' ;
--   2. app_geste_affaire_optimistic : « annuler » et « supprimer » un compromis dont la chaîne porte une
--      vente (non effacée chez Hektor) sont REFUSÉS, avec la raison et le geste qui débloque ;
--   3. app_modifier_affaire_optimistic : la modification d'un tel compromis est REFUSÉE, de même.
--   Rien d'autre ne change : l'offre, la vente (elle se supprime toujours), un compromis sans vente.
--
-- ⛔ GARDE : empreintes 20eeca7c (gestes) et 43247de7 (modification) exigées, chaque ancre trouvée UNE
--    fois, textes neufs a6569229 / 910e7947 CALCULÉS D'AVANCE. Sinon : ARRÊT, rien n'est écrit.
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'compromis_verrouille_par_vente';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'compromis_verrouille_par_vente';
-- RETOUR ARRIÈRE COMPLET : supabase/patch_v_compromis_verrouille_2026-10-23_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('compromis_verrouille_par_vente', 'off',
        'Chantier 8 / V 23/10/2026 : on = un COMPROMIS dont la chaine porte une VENTE ne se modifie, ne s''annule et ne se supprime plus (« pour revenir sur le compromis, il faut d''abord supprimer la vente » -- decision de Frederic). Voir supabase/patch_v_compromis_verrouille_2026-10-23.sql. off = comportement d''avant.',
        now())
on conflict (key) do nothing;

-- 2. LES GESTES
DO $pose_g$
DECLARE
    d text := replace(pg_get_functiondef('public.app_geste_affaire_optimistic(bigint,text,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($ga1$  -- Une transaction DEJA dans cet etat : on ne renvoie pas de travail pour rien.$ga1$, chr(13), '')];
    neufs text[] := array[
        replace($gn1$  -- ⛔ ─── V (23/10/2026, chantier 8) : LE COMPROMIS EST VERROUILLE PAR SA VENTE ─── ⛔
  -- Decision de Frederic : « apres la vente tout est verrouille ; pour modifier quoi que ce soit sur
  -- le compromis, il faut d'abord supprimer la vente ». Meme regle que l'offre ci-dessus (16/09).
  -- Essai reel du 23/10 (compromis 50135/50136) : sans elle, modifier le compromis d'une chaine vendue
  -- remettait le bien « Sous compromis » chez Hektor. Interrupteur 'compromis_verrouille_par_vente'.
  IF a.kind = 'compromis' AND geste IN ('annuler', 'supprimer') AND a.app_chaine_id IS NOT NULL
     AND coalesce((select s.value from public.app_setting s where s.key = 'compromis_verrouille_par_vente'), 'off') = 'on' THEN
      SELECT l.hektor_affaire_id::text INTO bloc_id
        FROM app_affaire_ledger l
       WHERE l.app_chaine_id = a.app_chaine_id
         AND l.app_affaire_id <> a.app_affaire_id
         AND l.kind = 'vente'
         AND NOT (btrim(coalesce(l.hektor_affaire_id::text, '')) <> ''
                  AND l.present_in_hektor IS FALSE)
       LIMIT 1;
    IF FOUND THEN
      RAISE EXCEPTION 'compromis_verrouille: ce dossier porte une vente (n° %). Pour revenir sur le compromis, il faut d''abord supprimer la vente.',
        coalesce(nullif(btrim(bloc_id), ''), '?') USING errcode = '22023';
    END IF;
  END IF;

  -- Une transaction DEJA dans cet etat : on ne renvoie pas de travail pour rien.$gn1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = 'a65692290a679d603916b9d635192b80' THEN
        RAISE NOTICE '%', 'Deja pose : app_geste_affaire_optimistic porte deja l''empreinte a6569229. Rien n''est ecrit.'; RETURN;
    END IF;
    IF md5(d) <> '20eeca7cc00bd4afe5b4175febacb2f7' THEN
        RAISE EXCEPTION '%', format('ARRET : app_geste_affaire_optimistic a l''empreinte %s, attendu 20eeca7c. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_geste_affaire_optimistic, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> 'a65692290a679d603916b9d635192b80' THEN
        RAISE EXCEPTION '%', format('ARRET : app_geste_affaire_optimistic, le texte rendu a l''empreinte %s, attendu a6569229 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_geste_affaire_optimistic(bigint,text,integer)'::regprocedure), chr(13), '')) <> 'a65692290a679d603916b9d635192b80' THEN
        RAISE EXCEPTION '%', 'ARRET : app_geste_affaire_optimistic, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose_g$;

-- 3. LA MODIFICATION
DO $pose_m$
DECLARE
    d text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($ma1$  select * into d from app_dossier_current where app_dossier_id = a.app_dossier_id;$ma1$, chr(13), '')];
    neufs text[] := array[
        replace($mn1$  -- ⛔ ─── V (23/10/2026, chantier 8) : LE COMPROMIS EST VERROUILLE PAR SA VENTE ─── ⛔
  -- Voir app_geste_affaire_optimistic. Modifier le compromis d'une chaine vendue renvoie son statut a
  -- Hektor (« Sous compromis ») alors que la vente existe. ⚠ v_cible sert ici de tampon : elle est
  -- reaffectee plus bas (genre vise), sans rapport.
  if a.kind = 'compromis' and a.app_chaine_id is not null and coalesce((select s.value from public.app_setting s where s.key = 'compromis_verrouille_par_vente'), 'off') = 'on' then
      SELECT l.hektor_affaire_id::text INTO v_cible
        FROM app_affaire_ledger l
       WHERE l.app_chaine_id = a.app_chaine_id
         AND l.app_affaire_id <> a.app_affaire_id
         AND l.kind = 'vente'
         AND NOT (btrim(coalesce(l.hektor_affaire_id::text, '')) <> ''
                  AND l.present_in_hektor IS FALSE)
       LIMIT 1;
    if found then
      raise exception 'compromis_verrouille: ce dossier porte une vente (n° %). Pour revenir sur le compromis, il faut d''abord supprimer la vente.',
        coalesce(nullif(btrim(v_cible), ''), '?') using errcode = '22023';
    end if;
  end if;

  select * into d from app_dossier_current where app_dossier_id = a.app_dossier_id;$mn1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '910e79470819a1111d21b608625f95b8' THEN
        RAISE NOTICE '%', 'Deja pose : app_modifier_affaire_optimistic porte deja l''empreinte 910e7947. Rien n''est ecrit.'; RETURN;
    END IF;
    IF md5(d) <> '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, attendu 43247de7. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '910e79470819a1111d21b608625f95b8' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, le texte rendu a l''empreinte %s, attendu 910e7947 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) <> '910e79470819a1111d21b608625f95b8' THEN
        RAISE EXCEPTION '%', 'ARRET : app_modifier_affaire_optimistic, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose_m$;

-- 4. LES CONTRÔLES — tous doivent dire OK
SELECT 1 AS "#", 'app_geste_affaire_optimistic porte l''empreinte a6569229' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_geste_affaire_optimistic(bigint,text,integer)'::regprocedure), chr(13), '')) = 'a65692290a679d603916b9d635192b80' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'app_geste_affaire_optimistic : droits d''appel inchanges, SECURITY DEFINER',
       CASE WHEN has_function_privilege('authenticated', 'public.app_geste_affaire_optimistic(bigint,text,integer)', 'EXECUTE') AND (SELECT prosecdef FROM pg_proc WHERE oid = 'public.app_geste_affaire_optimistic(bigint,text,integer)'::regprocedure) THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3 AS "#", 'app_modifier_affaire_optimistic porte l''empreinte 910e7947' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) = '910e79470819a1111d21b608625f95b8' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 4, 'app_modifier_affaire_optimistic : droits d''appel inchanges, SECURITY DEFINER',
       CASE WHEN has_function_privilege('authenticated', 'public.app_modifier_affaire_optimistic(bigint,jsonb,integer)', 'EXECUTE') AND (SELECT prosecdef FROM pg_proc WHERE oid = 'public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure) THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'l''interrupteur existe, ETEINT',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'compromis_verrouille_par_vente' AND value = 'off') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
