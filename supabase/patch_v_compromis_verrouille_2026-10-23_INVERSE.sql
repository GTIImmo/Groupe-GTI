-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE V — le compromis verrouillé par sa vente   23/10/2026
-- Il rend aux deux fonctions leur texte d'avant (20eeca7c / 43247de7), par les MÊMES ancres, et
-- retire l'interrupteur. Il ne touche aucune donnée. Pour seulement SUSPENDRE : éteindre l'interrupteur.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $retour_g$
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
    IF md5(d) = '20eeca7cc00bd4afe5b4175febacb2f7' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_geste_affaire_optimistic porte deja l''empreinte d''avant (20eeca7c).'; RETURN;
    END IF;
    IF md5(d) <> 'a65692290a679d603916b9d635192b80' THEN
        RAISE EXCEPTION '%', format('ARRET : app_geste_affaire_optimistic a l''empreinte %s, attendu a6569229. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_geste_affaire_optimistic, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '20eeca7cc00bd4afe5b4175febacb2f7' THEN
        RAISE EXCEPTION '%', format('ARRET : app_geste_affaire_optimistic, le texte rendu a l''empreinte %s, attendu 20eeca7c (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_geste_affaire_optimistic(bigint,text,integer)'::regprocedure), chr(13), '')) <> '20eeca7cc00bd4afe5b4175febacb2f7' THEN
        RAISE EXCEPTION '%', 'ARRET : app_geste_affaire_optimistic, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$retour_g$;

DO $retour_m$
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
    IF md5(d) = '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_modifier_affaire_optimistic porte deja l''empreinte d''avant (43247de7).'; RETURN;
    END IF;
    IF md5(d) <> '910e79470819a1111d21b608625f95b8' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, attendu 910e7947. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, le texte rendu a l''empreinte %s, attendu 43247de7 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) <> '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE EXCEPTION '%', 'ARRET : app_modifier_affaire_optimistic, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$retour_m$;

delete from public.app_setting where key = 'compromis_verrouille_par_vente';

SELECT 1 AS "#", 'app_geste_affaire_optimistic a retrouve 20eeca7c' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_geste_affaire_optimistic(bigint,text,integer)'::regprocedure), chr(13), '')) = '20eeca7cc00bd4afe5b4175febacb2f7' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'app_modifier_affaire_optimistic a retrouve 43247de7',
       CASE WHEN md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) = '43247de7ff89e395d3b6e970353a891b' THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'compromis_verrouille_par_vente') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
