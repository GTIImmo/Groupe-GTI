-- INVERSE -- genere par phase2/checks/dates_annulation_generer_patch_2026-11-25.py (son mot du 25/11)

begin;

update public.app_affaire_ledger l set date_annulation_app = null
  from public.app_classeur_realignement_journal j
 where j.lot = 'dates_annulation_2026-11-25' and j.geste = 'POSER (case vide)' and l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app = j.valeur;
delete from public.app_classeur_realignement_journal where lot = 'dates_annulation_2026-11-25';
do $$
begin
  if (select count(*) from public.app_affaire_ledger l join public.app_affaire_ledger_avant_dates_annulation_20261125 s using (app_affaire_id)
       where l.date_annulation_app is distinct from s.date_annulation_app) <> 0 then
    raise exception '⛔ inverse : les dates ne sont pas revenues a la sauvegarde'; end if;
  if (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, coalesce(date_annulation_app, '-'), coalesce(motif_annulation_app, '-'), coalesce(vente_reglee_app, '-'), coalesce(numero_facture_app, '-'), coalesce(honoraires_entree_app::text, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (27195, 4385, 27134, 16377, 17387, 24450, 20073)) <> '4011dda97ca0bcfc4d6d69a547ac00c2' then raise exception '⛔ inverse : l''empreinte n''est pas celle d''avant'; end if;
  raise notice '✅ inverse : les 4 dates retirees, le journal du lot vide, l''empreinte d''avant revenue';
end $$;

commit;
