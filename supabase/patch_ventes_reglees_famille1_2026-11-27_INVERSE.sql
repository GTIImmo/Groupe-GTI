-- INVERSE -- genere par phase2/checks/ventes_reglees_famille1_generer_patch_2026-11-27.py (son mot du 27/11)

begin;

-- ─── L'INVERSE : les 18 cases remises a vide (seulement si elles portent encore la valeur du lot), le journal retire ───
update public.app_affaire_ledger l set vente_reglee_app = s.vente_reglee_app
  from public.app_affaire_ledger_avant_ventes_reglees_f1_20261127 s, public.app_classeur_realignement_journal j
 where s.app_affaire_id = l.app_affaire_id and j.lot = 'ventes_reglees_famille1_2026-11-27' and j.colonne = 'vente_reglee_app'
   and j.de_app_affaire_id = l.app_affaire_id and l.vente_reglee_app = j.valeur;
update public.app_affaire_ledger l set numero_facture_app = s.numero_facture_app
  from public.app_affaire_ledger_avant_ventes_reglees_f1_20261127 s, public.app_classeur_realignement_journal j
 where s.app_affaire_id = l.app_affaire_id and j.lot = 'ventes_reglees_famille1_2026-11-27' and j.colonne = 'numero_facture_app'
   and j.de_app_affaire_id = l.app_affaire_id and l.numero_facture_app = j.valeur;
delete from public.app_classeur_realignement_journal where lot = 'ventes_reglees_famille1_2026-11-27';
do $$
begin
  if (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, app_chaine_id, app_dossier_numero, coalesce(vente_reglee_app, '-'), coalesce(numero_facture_app, '-'), coalesce(date_annulation_app, '-'), coalesce(motif_annulation_app, '-'), coalesce(honoraires_entree_app::text, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (3650, 14115, 20674, 30835, 30828, 30844, 30834, 30846, 30847)) <> 'fe8ded18db7a56241042231833c0f217' then raise exception '⛔ inverse : les 9 lignes ne sont pas revenues a la sauvegarde'; end if;
  raise notice '✅ inverse : les 18 cases revenues a la sauvegarde, le journal du lot vide';
end $$;

commit;
