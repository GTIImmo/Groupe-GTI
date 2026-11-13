-- RETOUR ARRIÈRE — patch_assistant_ia_etape2_statut_mandat_2026-11-12.sql (ASSISTANT IA, étape 2, décision « B »).
-- Retire la vue app_v_mandat_statut et ses 4 fonctions de calcul. ⛔ Refuse si un AUTRE objet dépend encore de la vue
-- ou des fonctions (l'écran les aurait reprises entre-temps) : il faut alors décider, pas casser.
-- Ne touche à RIEN d'autre (le registre des mandats reste tel quel). Pas de `cascade`.
begin;
set local lock_timeout = '3s';
do $garde$
begin
  if to_regclass('public.app_v_mandat_statut') is null then raise exception 'ARRET : rien a retirer'; end if;
  if exists (select 1 from pg_depend dp join pg_rewrite rw on rw.oid = dp.objid join pg_class k on k.oid = rw.ev_class
             where dp.refobjid = 'public.app_v_mandat_statut'::regclass and k.relname <> 'app_v_mandat_statut') then
    raise exception 'ARRET : un autre objet depend de app_v_mandat_statut -- a decider avant de retirer';
  end if;
end
$garde$;
drop view public.app_v_mandat_statut;
drop function public.app_mandat_etat(text, text);
drop function public.app_mandat_statut(text, text, text, text);
drop function public.app_mandat_date_fin_valide(text);
drop function public.app_mandat_statut_norm(text);
do $verif$
begin
  if to_regclass('public.app_v_mandat_statut') is not null
     or to_regprocedure('public.app_mandat_statut(text,text,text,text)') is not null
     or to_regprocedure('public.app_mandat_etat(text,text)') is not null
     or to_regprocedure('public.app_mandat_date_fin_valide(text)') is not null
     or to_regprocedure('public.app_mandat_statut_norm(text)') is not null then
    raise exception 'ARRET : un objet reste';
  end if;
  if to_regclass('public.app_registre_mandats_current') is null then raise exception 'ARRET : le registre a disparu'; end if;
end
$verif$;
commit;
