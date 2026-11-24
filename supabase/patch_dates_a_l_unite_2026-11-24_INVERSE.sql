-- patch_dates_a_l_unite_2026-11-24 -- genere par phase2/checks/cases_vides_generer_patchs_2026-11-24.py (son 5e mot du 24/11 : « rien ne s'ecrit sans mon accord sur le patch »)
-- Retour arriere : patch_dates_a_l_unite_2026-11-24_INVERSE.sql . Controle : patch_dates_a_l_unite_2026-11-24_REPETITION.sql
-- L'INVERSE : il retire ce que le lot a pose, et EXIGE le retour a l'empreinte d'avant. Le journal et la sauvegarde restent (la trace).

begin;

-- ─── LE RETOUR : vider ce que ce lot a pose (seulement si la valeur est TOUJOURS la sienne) ──────────────────────────────
update public.app_affaire_ledger l set date_annulation_app = null
  from public.app_classeur_realignement_journal j
 where j.lot = 'dates_a_l_unite_2026-11-24' and l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app = j.valeur;
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_affaire_ledger l join public.app_affaire_ledger_avant_dates_a_l_unite_20261124 s using (app_affaire_id)
   where l.date_annulation_app is distinct from s.date_annulation_app;
  if n <> 0 then raise exception '⛔ controle du retour : % ligne(s) differente(s) de la sauvegarde', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, coalesce(date_annulation_app, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (27195, 4385, 27134, 16377, 17387, 24450));
  if e <> 'df785d764855b5721e8fe54edd072fcb' then raise exception '⛔ controle du retour : empreinte % au lieu de df785d764855b5721e8fe54edd072fcb', e; end if;
end $$;

commit;
