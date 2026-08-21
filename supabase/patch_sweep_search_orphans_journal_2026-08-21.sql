-- =====================================================================
-- Le balayage nocturne tient un carnet
-- Date : 2026-08-21
-- Applique en prod via la migration `app_sweep_search_orphans_journal`
--
-- POURQUOI. Le balayage pose le 20/08 calcule deja ses compteurs -- combien de
-- propositions rattachees, combien de rapprochements supprimes -- mais pg_cron
-- jette la valeur de retour. Verifie le 21/08 au matin : le premier passage a
-- reussi en 2 secondes, et il etait IMPOSSIBLE de savoir s'il avait repare 0 ou
-- 40 lignes. Une reparation nocturne qui ne dit pas ce qu'elle repare ne se
-- surveille pas.
--
-- A QUOI CA SERT, concretement. C'est la mesure de la tache 4bis du plan : a
-- quelle frequence une recherche se detache-t-elle reellement ? De la reponse
-- depend la forme du chantier suivant -- si (contact + rang) suffit pour
-- reconnaitre une recherche au retour de Hektor, ou s'il faut capturer son
-- numero chez Hektor. Dans deux semaines, on aura des chiffres au lieu d'un avis.
--
-- CE QUI NE CHANGE PAS. Les memes UPDATE, les memes DELETE, le meme garde-fou
-- d'unicite sur app_bien_acquereur_statut qui annule tout plutot que d'ecrire a
-- moitie. Seule l'ecriture du carnet est ajoutee. La fonction n'ayant AUCUN
-- parametre, `create or replace` suffit et conserve les droits -- contrairement
-- au piege documente le 20/08 sur les fonctions a parametres.
--
-- VERIFIE : lance une fois a blanc le 21/08 sur un parc propre -> tout a zero,
-- et la ligne s'ecrit bien dans le carnet.
-- =====================================================================

create table if not exists public.app_sweep_search_orphans_log (
  run_at              timestamptz primary key default now(),
  ok                  boolean not null,
  raison              text,
  propositions        int not null default 0,
  relances            int not null default 0,
  retours_acquereur   int not null default 0,
  envois_email        int not null default 0,
  rapprochements      int not null default 0,
  historique_score    int not null default 0
);

comment on table public.app_sweep_search_orphans_log is
  'Ce que le balayage nocturne a reellement fait, nuit par nuit. Sert a mesurer le rythme de detachement des recherches.';

alter table public.app_sweep_search_orphans_log enable row level security;
drop policy if exists app_sweep_log_select on public.app_sweep_search_orphans_log;
create policy app_sweep_log_select on public.app_sweep_search_orphans_log
  for select to authenticated using (true);

-- La fonction est identique a celle du 20/08, aux deux `insert into ... log` pres.
-- Corps complet : voir la migration `app_sweep_search_orphans_journal`.
--
-- Les deux ajouts :
--   * en cas de conflit d'unicite (sortie anticipee) :
--       insert into app_sweep_search_orphans_log(ok, raison, propositions)
--       values (false, 'conflit_unicite', conflits) on conflict (run_at) do nothing;
--   * a la fin, le compte rendu complet :
--       insert into app_sweep_search_orphans_log(ok, propositions, relances,
--         retours_acquereur, envois_email, rapprochements, historique_score)
--       values (true, n_prop, n_rel, n_ret, n_env, n_rap, n_hist)
--       on conflict (run_at) do nothing;
--
-- L'ecriture est dans la transaction du balayage : si elle echouait, tout serait
-- annule. D'ou le `on conflict do nothing`, seul cas realiste (deux passages dans
-- la meme microseconde).
