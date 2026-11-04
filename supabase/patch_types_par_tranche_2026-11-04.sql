-- ════════════════════════════════════════════════════════════════════════════════════════════
-- ⑧ CONTACTS (04/11/2026) — LE TYPE DES CONTACTS SE RECALCULE PAR TRANCHES
-- Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §73-74.
--
-- POURQUOI. La nuit appelle app_recalculer_tous_les_types() par l'API, qui coupe a 8 s
--   (authenticator, statement_timeout=8s). Depuis que l'app porte 94 741 contacts (31 533 de plus le
--   04/11), un passage SANS AUCUN changement prend deja 7,2 s, et l'appel du 04/11 a 13:57 a echoue
--   (« canceling statement due to statement timeout »).
-- LE REMEDE. La MEME regle, limitee a une tranche de numeros [p_de, p_a[ (texte : les identites ont
--   toutes 8 chiffres, l'ordre du texte est celui des nombres). Le script de nuit l'appelle tranche par
--   tranche ; une tranche de 31 524 contacts se calcule en 1,4 s.
-- ⚠ app_recalculer_tous_les_types() N'EST PAS TOUCHEE : elle reste le chemin d'avant (retour arriere).
-- ⚠ DROITS : service_role seulement (revoke explicite a anon ET authenticated : « revoke from public »
--   ne ferme pas authenticated).
-- GARDE : la fonction ne doit pas exister ; la fonction d'origine doit avoir son empreinte connue.
-- ════════════════════════════════════════════════════════════════════════════════════════════
do $garde$
begin
  if exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
              where n.nspname = 'public' and p.proname = 'app_recalculer_types_tranche') then
    raise exception 'GARDE : app_recalculer_types_tranche existe deja -- rien n''est pose';
  end if;
  if (select md5(replace(pg_get_functiondef('public.app_recalculer_tous_les_types()'::regprocedure), chr(13), '')))
     <> '22f51f243410779ff74ebcf38fea88d9' then
    raise exception 'GARDE : app_recalculer_tous_les_types a change depuis l''audit du 04/11 -- rien n''est pose';
  end if;
end
$garde$;

create function public.app_recalculer_types_tranche(p_de text, p_a text)
 returns integer
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
DECLARE n integer := 0;
BEGIN
    -- ⚠ LA MÊME RÈGLE que app_recalculer_tous_les_types (et app_type_depuis_nos_registres), bornée à
    --   [p_de, p_a[ des deux côtés : les liens lus ET les fiches écrites.
    IF p_de IS NULL OR p_a IS NULL OR p_de >= p_a THEN RETURN 0; END IF;
    WITH v AS (
        SELECT d.c, jsonb_agg(d.r ORDER BY d.r COLLATE "C") AS roles
          FROM (SELECT DISTINCT x.hektor_contact_id AS c, x.role_contact AS r
                  FROM public.app_contact_relations_current x
                 WHERE x.hektor_contact_id >= p_de AND x.hektor_contact_id < p_a) d
         GROUP BY d.c)
    UPDATE public.app_contact_current k
       SET relation_roles_json = coalesce(v.roles, '[]'::jsonb)
      FROM public.app_contact_current k2
      LEFT JOIN v ON v.c = k2.hektor_contact_id
     WHERE k.hektor_contact_id = k2.hektor_contact_id
       AND k2.hektor_contact_id >= p_de AND k2.hektor_contact_id < p_a
       AND k.relation_roles_json IS DISTINCT FROM coalesce(v.roles, '[]'::jsonb);
    GET DIAGNOSTICS n = ROW_COUNT;
    RETURN n;
END
$function$;

revoke all on function public.app_recalculer_types_tranche(text, text) from public;
revoke all on function public.app_recalculer_types_tranche(text, text) from anon;
revoke all on function public.app_recalculer_types_tranche(text, text) from authenticated;
grant execute on function public.app_recalculer_types_tranche(text, text) to service_role;

comment on function public.app_recalculer_types_tranche(text, text) is
  'Type des contacts depuis nos registres, sur une tranche de numeros [p_de, p_a[ (04/11/2026, synthese couples §74). Meme regle que app_recalculer_tous_les_types.';
