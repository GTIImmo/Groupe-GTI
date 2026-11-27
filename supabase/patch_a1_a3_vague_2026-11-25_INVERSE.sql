-- patch_a1_a3_vague_2026-11-25_INVERSE -- genere par phase2/checks/a1_a3_vague_generer_patch_2026-11-25.py
-- A1 et A3 de la vague du soir (passage 82, image 2026-11-25_072625). ⛔ Etape 7, apres A2, et SUR SON ACCORD.

begin;

-- ═══ L'INVERSE D'A3 PUIS D'A1 : les reflets reprennent leur valeur sauvegardee, le journal des deux lots est retire ═══
update public.app_affaire_note n set app_chaine_id = s.app_chaine_id from public.app_affaire_note_reflets_avant_a3vague_20261125 s
 where s.app_affaire_id = n.app_affaire_id and n.app_chaine_id is distinct from s.app_chaine_id;
update public.app_affaire_condition c set app_chaine_id = s.app_chaine_id
  from public.app_affaire_condition_reflets_avant_a3vague_20261125 s
 where s.app_affaire_id = c.app_affaire_id and s.rang = c.rang and c.app_chaine_id is distinct from s.app_chaine_id;
update public.app_classeur_avis a set app_dossier_uuid = s.app_dossier_uuid, app_dossier_numero = s.app_dossier_numero
  from public.app_classeur_avis_reflets_avant_a1vague_20261125 s
 where s.id_unique = a.id_unique and (a.app_dossier_uuid is distinct from s.app_dossier_uuid
                                      or a.app_dossier_numero is distinct from s.app_dossier_numero);
delete from public.app_classeur_realignement_journal where lot in ('a1_vague_2026-11-25', 'a3_vague_2026-11-25');
do $$
declare n int;
begin
  select count(*) into n from public.app_classeur_avis a join public.app_classeur_avis_reflets_avant_a1vague_20261125 s using (id_unique)
   where a.app_dossier_uuid is distinct from s.app_dossier_uuid or a.app_dossier_numero is distinct from s.app_dossier_numero;
  if n <> 0 then raise exception '⛔ inverse A1 : % avis differents de la sauvegarde', n; end if;
  select count(*) into n from public.app_affaire_note n join public.app_affaire_note_reflets_avant_a3vague_20261125 s using (app_affaire_id)
   where n.app_chaine_id is distinct from s.app_chaine_id;
  if n <> 0 then raise exception '⛔ inverse A3 : % notes differentes de la sauvegarde', n; end if;
  raise notice '✅ inverse A1 et A3 : les reflets sont revenus a la sauvegarde';
end $$;

commit;
