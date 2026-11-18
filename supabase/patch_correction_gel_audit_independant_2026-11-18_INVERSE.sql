-- RETOUR ARRIERE de patch_correction_gel_audit_independant_2026-11-18.sql -- 18/11/2026
-- Il remet le gel EXACTEMENT comme la sauvegarde, et il juge sa part.
begin;
do $$ begin
  if to_regclass('public.app_classeur_lien_avant_audit_independant_20261118') is null then
    raise exception '⛔ pas de sauvegarde : le patch n''a jamais ete joue, rien a defaire';
  end if;
end $$;
delete from app_classeur_lien where gele_par = 'audit_independant_2026-11-18';
insert into app_classeur_lien
  select s.* from app_classeur_lien_avant_audit_independant_20261118 s
   where not exists (select 1 from app_classeur_lien l
                      where l.id_unique = s.id_unique and l.app_affaire_id = s.app_affaire_id);
do $$
declare ecart int; n int;
begin
  select count(*) into n from app_classeur_lien;
  select count(*) into ecart from (
    (select id_unique, app_affaire_id, role, confiance from app_classeur_lien
     except select id_unique, app_affaire_id, role, confiance from app_classeur_lien_avant_audit_independant_20261118)
    union all
    (select id_unique, app_affaire_id, role, confiance from app_classeur_lien_avant_audit_independant_20261118
     except select id_unique, app_affaire_id, role, confiance from app_classeur_lien)) x;
  if ecart <> 0 or n <> 12787 then
    raise exception '⛔ retour arriere incomplet : % ecart(s), % liens', ecart, n;
  end if;
  raise notice '✅ gel revenu a son etat d''avant (12787 liens, 0 ecart)';
end $$;
commit;
