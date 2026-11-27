-- INVERSE -- genere par phase2/checks/dates_annulation_etape3_generer_patch_2026-11-27.py (son mot du 27/11 au soir)

begin;

-- ─── L'INVERSE : les dates retirees (seulement si elles portent encore la valeur du lot), le journal retire ─────────
update public.app_affaire_ledger l set date_annulation_app = s.date_annulation_app
  from public.app_affaire_ledger_avant_dates_e3_20261127 s, public.app_classeur_realignement_journal j
 where s.app_affaire_id = l.app_affaire_id and j.lot = 'dates_annulation_etape3_2026-11-27' and j.de_app_affaire_id = l.app_affaire_id
   and l.date_annulation_app = j.valeur;
delete from public.app_classeur_realignement_journal where lot = 'dates_annulation_etape3_2026-11-27';
do $$
begin
  if (select count(*) from public.app_affaire_ledger l join public.app_affaire_ledger_avant_dates_e3_20261127 s using (app_affaire_id)
       where l.date_annulation_app is distinct from s.date_annulation_app) <> 0 then
    raise exception '⛔ inverse : les dates ne sont pas revenues a la sauvegarde'; end if;
  raise notice '✅ inverse : les dates retirees, le journal du lot vide';
end $$;

commit;
