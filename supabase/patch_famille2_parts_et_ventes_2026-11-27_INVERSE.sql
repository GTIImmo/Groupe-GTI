-- INVERSE -- genere par phase2/checks/famille2_parts_et_ventes_generer_patch_2026-11-27.py (son mot du 27/11)

begin;

-- ─── L'INVERSE : temps 2 puis temps 1 -- les 12 cases remises, les parts du classeur retirees, les suppositions remises ──
update public.app_affaire_ledger l set vente_reglee_app = s.vente_reglee_app
  from public.app_affaire_ledger_avant_ventes_reglees_f2_20261127 s, public.app_classeur_realignement_journal j
 where s.app_affaire_id = l.app_affaire_id and j.lot = 'ventes_reglees_famille2_2026-11-27' and j.colonne = 'vente_reglee_app'
   and j.de_app_affaire_id = l.app_affaire_id and l.vente_reglee_app = j.valeur;
update public.app_affaire_ledger l set numero_facture_app = s.numero_facture_app
  from public.app_affaire_ledger_avant_ventes_reglees_f2_20261127 s, public.app_classeur_realignement_journal j
 where s.app_affaire_id = l.app_affaire_id and j.lot = 'ventes_reglees_famille2_2026-11-27' and j.colonne = 'numero_facture_app'
   and j.de_app_affaire_id = l.app_affaire_id and l.numero_facture_app = j.valeur;
delete from public.app_affaire_repartition where app_chaine_id in (27712, 17769, 24618, 4781) and origine = 'classeur_reconstitue' and ecrit_par like 'classeur:%';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select ancien_app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
  from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_famille2_2026-11-27';
delete from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_famille2_2026-11-27';
delete from public.app_classeur_realignement_journal where lot in ('parts_famille2_2026-11-27', 'ventes_reglees_famille2_2026-11-27');
do $$
begin
  -- l'inverse ne juge que SA part (lecon 31) : les 12 cases et les 4 chaines contre leurs sauvegardes
  if (select count(*) from public.app_affaire_ledger l join public.app_affaire_ledger_avant_ventes_reglees_f2_20261127 s using (app_affaire_id)
       where (l.vente_reglee_app, l.numero_facture_app) is distinct from (s.vente_reglee_app, s.numero_facture_app)) <> 0 then
    raise exception '⛔ inverse : les 6 ventes ne sont pas revenues a la sauvegarde'; end if;
  if (select count(*) from (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
        ecrit_le, ecrit_par from public.app_affaire_repartition where app_chaine_id in (27712, 17769, 24618, 4781)
      except all select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le,
        ecrit_par from public.app_affaire_repartition_avant_famille2_20261127) z) <> 0
     or (select count(*) from (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
        ecrit_le, ecrit_par from public.app_affaire_repartition_avant_famille2_20261127
      except all select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le,
        ecrit_par from public.app_affaire_repartition where app_chaine_id in (27712, 17769, 24618, 4781)) z) <> 0 then
    raise exception '⛔ inverse : les 4 chaines ne sont pas revenues a la sauvegarde'; end if;
  raise notice '✅ inverse : les 6 ventes et les 4 chaines revenues a leurs sauvegardes, la mise de cote et le journal des lots vides';
end $$;

commit;
