-- =====================================================================
-- COUPLES · PIECE C — LA CLE DE BATTEMENT DE L'ETAPE NEUVE          31/10/2026
-- Note : notice/COUPLES_ERGONOMIE_ET_ECRITURE_PROPOSITION_2026-10-30.md §17-§18
--
-- POURQUOI. Le run envoie le battement de l'etape « phase2 secondes fiches des
-- couples » sous la cle phase2.secondes_fiches_couple. Une cle SANS ligne dans
-- app_worker_registry part dans le vide, en silence (lecon du 13/10, 4j) : un
-- « DOUTE » de la piece C (sortie 1) ne serait alors vu par personne.
--
-- CE QUE FAIT CE PATCH : UNE ligne de configuration. Rien d'autre.
-- medium / optional_pipeline_step, comme ses voisines (contacts_app_seuls,
-- contacts_layer_passe2) : son echec n'aggrave rien, la nuit fait alors ce
-- qu'elle faisait avant -- mais il doit se VOIR.
-- IDEMPOTENT : on conflict do nothing.
-- RETOUR ARRIERE : delete from public.app_worker_registry where worker_key = 'phase2.secondes_fiches_couple';
-- =====================================================================

insert into public.app_worker_registry
  (worker_key, worker_name, worker_role, worker_type, criticality, frequency,
   status, owner, script_path, expected_max_runtime_minutes, monitoring_domain,
   source_notes)
values
  ('phase2.secondes_fiches_couple',
   'Secondes fiches des couples nes dans l''app',
   'Filet de la nuit : rattache la seconde fiche Hektor d''un couple cree dans l''app a '
   'la personne 2 deja ecrite chez nous, quand le worker ne l''a pas trouvee. Sans lui, '
   'la personne 2 recevrait un numero de plus (deux fiches pour une personne). Sortie 1 '
   '= un cas NON tranche, rien n''est ecrit pour lui (lire le journal du run).',
   'python_worker', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'phase2\identite\rattacher_secondes_fiches.py',
   10, 'business',
   'Ajoutee le 31/10/2026 (couples, piece C). Ne lit que le miroir et Supabase, aucune '
   'requete chez Hektor. Dormante tant qu''aucun couple ne nait dans l''app.')
on conflict (worker_key) do nothing;

select worker_key, criticality, frequency, status
  from public.app_worker_registry
 where worker_key = 'phase2.secondes_fiches_couple';
