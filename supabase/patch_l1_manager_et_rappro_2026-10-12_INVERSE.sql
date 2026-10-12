-- ============================================================================
-- RETOUR ARRIERE : L1 « manager = admin » et les rapprochements
-- Inverse exact de patch_l1_manager_et_rappro_2026-10-12.sql
--
-- Il refait l'operation contraire sur les 3 morceaux, puis VERIFIE qu'il
-- retombe exactement sur les 7 empreintes du 12/10 et sur les 3 regles « true ».
-- ============================================================================

begin;

-- ----------------------------------------------------------------------------
-- 1. LES 6 FONCTIONS « AFFAIRE » reviennent a « admin seul »
-- ----------------------------------------------------------------------------
do $affaires$
declare
    v_nom text;
    v_def text;
begin
    foreach v_nom in array array[
        'app_affaire_note_ecrire', 'app_affaire_personne_ecart_fermer',
        'app_conditions_affaire_ecrire', 'app_edit_affaire_optimistic',
        'app_geste_affaire_optimistic', 'app_modifier_affaire_optimistic'
    ] loop
        select pg_get_functiondef(p.oid) into v_def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = v_nom;

        if position('is_app_manager_or_admin()' in v_def) = 0 then
            raise notice 'AFFAIRES : % est deja en admin seul.', v_nom;
        else
            execute replace(v_def, 'is_app_manager_or_admin()', 'is_app_admin()');
        end if;
    end loop;
    raise notice 'AFFAIRES : les 6 fonctions sont revenues a « admin seul ».';
end
$affaires$;


-- ----------------------------------------------------------------------------
-- 2. LE VIDEUR : le statut et l'archivage redeviennent « admin seul »
-- ----------------------------------------------------------------------------
do $videur$
declare
    v_def text;
    v_pose text := 'return coalesce(current_app_role in (''admin'', ''manager''), false);';
    v_origine text := 'return coalesce(current_app_role = ''admin'', false);';
begin
    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_can_request_job';

    if position(v_pose in v_def) = 0 then
        raise notice 'VIDEUR : rien a retirer.';
    else
        execute replace(v_def, v_pose, v_origine);
        raise notice 'VIDEUR : le statut et l''archivage redeviennent « admin seul ».';
    end if;
end
$videur$;


-- ----------------------------------------------------------------------------
-- 3. LES RAPPROCHEMENTS redeviennent visibles de tout compte connecte
-- ----------------------------------------------------------------------------
drop policy if exists app_rapprochement_sel on public.app_rapprochement;
create policy app_rapprochement_sel on public.app_rapprochement for select using (true);

drop policy if exists app_rappro_hist_sel on public.app_rapprochement_score_history;
create policy app_rappro_hist_sel on public.app_rapprochement_score_history for select using (true);

drop policy if exists app_rel_sel on public.app_relance_rapprochement;
create policy app_rel_sel on public.app_relance_rapprochement for select using (true);


-- ----------------------------------------------------------------------------
-- 4. CONTROLE : retombe-t-on sur l'etat du 12/10 ?
-- ----------------------------------------------------------------------------
do $controle$
declare
    v_attendu jsonb := jsonb_build_object(
        'app_affaire_note_ecrire',           '23ab1ab09f19be18b82ca5c6f6430f67',
        'app_affaire_personne_ecart_fermer', 'f363f2f4336ae3e632bf3271865ab09a',
        'app_conditions_affaire_ecrire',     '84ec93cfdb8487a0206fca220fe04c79',
        'app_edit_affaire_optimistic',       'c70b690afb25c2af35f42bbf5959b2d4',
        'app_geste_affaire_optimistic',      'f2d551c1947077a9df77e4135882170d',
        'app_modifier_affaire_optimistic',   '29a02607ee212ec887040cd009b7d221',
        'app_console_can_request_job',       'e1435a48a47b4987109eefa7b9c34237'
    );
    v_nom text;
    v_trouve text;
    v_ecarts int := 0;
begin
    for v_nom in select jsonb_object_keys(v_attendu) loop
        select md5(replace(pg_get_functiondef(p.oid), chr(13), '')) into v_trouve
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = v_nom limit 1;
        if v_trouve is distinct from (v_attendu ->> v_nom) then
            v_ecarts := v_ecarts + 1;
            raise notice 'ECART sur % : trouve %, attendu %', v_nom, v_trouve, (v_attendu ->> v_nom);
        end if;
    end loop;

    if (select count(*) from pg_policies
         where schemaname = 'public' and cmd = 'SELECT'
           and tablename in ('app_rapprochement','app_rapprochement_score_history','app_relance_rapprochement')
           and md5(coalesce(qual, '')) = 'b326b5062b2f0e69046810717534cb09') <> 3 then
        v_ecarts := v_ecarts + 1;
        raise notice 'ECART : les 3 regles de rapprochement ne sont pas revenues a « true ».';
    end if;

    if v_ecarts > 0 then
        raise exception 'RETOUR ARRIERE INCOMPLET : % ecart(s).', v_ecarts;
    end if;

    raise notice 'RETOUR ARRIERE COMPLET : les 7 fonctions et les 3 regles sont revenues a l''etat du 12/10.';
end
$controle$;

commit;
