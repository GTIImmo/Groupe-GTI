-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — ⑧ D8 : remettre app_repartition_purger_orphelines comme avant le 28/10/2026
-- Il ne juge que SA part : il remet la fonction d'avant (texte verbatim, empreinte 1e107de3) et ne déplace rien en retour --
-- une répartition déjà ramenée dans son dossier y est À SA PLACE ; la remettre orpheline la rendrait invisible.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
CREATE OR REPLACE FUNCTION public.app_repartition_purger_orphelines()
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
    v_supprimees integer := 0;
    v_gardees    integer := 0;
begin
    select count(*) into v_gardees
      from app_affaire_repartition r
     where coalesce(r.origine, '') not like 'hektor%'
       and not exists (select 1 from app_affaire_ledger l
                        where l.app_chaine_id = r.app_chaine_id);

    delete from app_affaire_repartition r
     where coalesce(r.origine, '') like 'hektor%'
       and not exists (select 1 from app_affaire_ledger l
                        where l.app_chaine_id = r.app_chaine_id);
    get diagnostics v_supprimees = row_count;

    return jsonb_build_object(
        'derivees_supprimees', v_supprimees,
        'saisies_orphelines_gardees', v_gardees);
end;
$function$;

DO $v$
BEGIN
    IF md5(pg_get_functiondef('public.app_repartition_purger_orphelines'::regproc)) <> '1e107de38d57b23b36a4f184f348a438' THEN
        RAISE EXCEPTION '%', 'ARRET : la fonction remise ne porte pas l''empreinte d''avant (1e107de3). Tout est annule.';
    END IF;
END
$v$;
COMMIT;
