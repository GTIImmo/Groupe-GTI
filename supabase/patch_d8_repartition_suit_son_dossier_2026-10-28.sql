-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ D8 — UNE RÉPARTITION SAISIE SUIT SA TRANSACTION QUAND LA NUIT CHANGE SON DOSSIER                28/10/2026
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md, §58 « D8 et D9 » ; décision de Frédéric du 28/10 :
--        « Corriger les deux ».
--
-- LE DÉFAUT. Au clic, une transaction est rangée dans un dossier (une chaîne) par la règle SQL ; la nuit refait tous les
-- dossiers avec la règle v2 et peut la recoller ailleurs. Les conditions et les notes sont lues par TRANSACTION : à l'abri.
-- La répartition de commission est rangée par DOSSIER (clé app_chaine_id, cote, rang) : si la nuit change le dossier, la
-- saisie reste sous l'ancien numéro -- gardée (la purge ne retire que les lignes « hektor »), mais INVISIBLE à l'écran.
--
-- LE REMÈDE, sans toucher ni au run ni au worker : la purge de nuit (appelée par repartition_commission.py
-- --purger-orphelines, APRÈS le push des chaînes) commence par RAMENER chaque saisie orpheline dans son dossier.
-- ⭐ Le nouveau dossier se TROUVE sans journal : le numéro d'un dossier est TOUJOURS le plus petit numéro de ses transactions
--   (mesuré le 28/10 : 12 187 dossiers, 0 exception). Une répartition orpheline du dossier A appartient donc à la transaction A :
--   son nouveau dossier est celui que la transaction A porte maintenant.
-- Règles :
--   · transaction A disparue (essai supprimé, ex. 1001347) -> la saisie reste orpheline, gardée, comptée ;
--   · le nouveau dossier porte déjà une saisie (deux dossiers de l'app fusionnés) -> on ne choisit pas : la saisie reste
--     orpheline, gardée, NOMMÉE dans le compte rendu (« en_conflit ») ;
--   · le nouveau dossier ne porte que des lignes déduites de Hektor -> la saisie les remplace (une saisie l'emporte toujours
--     sur une déduction, même règle que app_repartition_absorber) ; les lignes déduites retirées sont comptées.
--   · ecrit_le / ecrit_par / nom_au_moment ne bougent pas : la trace de l'humain reste la sienne.
-- GARDE : s'arrête si la fonction en ligne n'est pas celle d'avant (empreinte 1e107de3).
-- Retour arrière : patch_d8_repartition_suit_son_dossier_2026-10-28_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $g$
BEGIN
    IF md5(pg_get_functiondef('public.app_repartition_purger_orphelines'::regproc)) <> '1e107de38d57b23b36a4f184f348a438' THEN
        RAISE EXCEPTION '%', 'ARRET : app_repartition_purger_orphelines a change depuis l''audit du 28/10 (empreinte 1e107de3 attendue). Rien n''est change.';
    END IF;
END
$g$;

CREATE OR REPLACE FUNCTION public.app_repartition_purger_orphelines()
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
    v_supprimees integer := 0;
    v_gardees    integer := 0;
    v_ramenees   integer := 0;
    v_remplacees integer := 0;
    v_n          integer;
    v_conflits   jsonb := '[]'::jsonb;
    v_sans_tx    jsonb := '[]'::jsonb;
    v_deplaces   jsonb := '[]'::jsonb;
    o            record;
begin
    -- ⑧ D8 (28/10/2026) : D'ABORD, chaque saisie orpheline rejoint le dossier que sa transaction porte maintenant.
    for o in
        select r.app_chaine_id as ancien, l.app_chaine_id as nouveau
          from (select distinct app_chaine_id from app_affaire_repartition
                 where coalesce(origine, '') not like 'hektor%') r
          left join app_affaire_ledger l on l.app_affaire_id = r.app_chaine_id
         where not exists (select 1 from app_affaire_ledger x where x.app_chaine_id = r.app_chaine_id)
         order by r.app_chaine_id
    loop
        if o.nouveau is null then
            v_sans_tx := v_sans_tx || to_jsonb(o.ancien);
            continue;
        end if;
        if exists (select 1 from app_affaire_repartition
                    where app_chaine_id = o.nouveau and coalesce(origine, '') not like 'hektor%') then
            v_conflits := v_conflits || jsonb_build_object('ancien', o.ancien, 'nouveau', o.nouveau);
            continue;
        end if;
        delete from app_affaire_repartition
         where app_chaine_id = o.nouveau and coalesce(origine, '') like 'hektor%';
        get diagnostics v_n = row_count;
        v_remplacees := v_remplacees + v_n;
        update app_affaire_repartition set app_chaine_id = o.nouveau
         where app_chaine_id = o.ancien and coalesce(origine, '') not like 'hektor%';
        get diagnostics v_n = row_count;
        v_ramenees := v_ramenees + v_n;
        v_deplaces := v_deplaces || jsonb_build_object('ancien', o.ancien, 'nouveau', o.nouveau, 'lignes', v_n);
    end loop;

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
        'saisies_orphelines_gardees', v_gardees,
        'saisies_ramenees', v_ramenees,
        'derivees_remplacees_par_une_saisie', v_remplacees,
        'dossiers_deplaces', v_deplaces,
        'orphelines_en_conflit', v_conflits,
        'orphelines_sans_transaction', v_sans_tx);
end;
$function$;

REVOKE ALL ON FUNCTION public.app_repartition_purger_orphelines() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.app_repartition_purger_orphelines() TO service_role;

COMMIT;
