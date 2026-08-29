-- =====================================================================
-- C.4-bis — LE FILET DE REJEU DES ACTIONS
-- Date : 2026-08-30
--
-- CE QU'IL RÉPARE. Mesuré le 29/08 : 7 travaux en erreur depuis le 27/08,
-- `attempt_count` à 1 partout — AUCUN n'a jamais été rejoué. Une action qui
-- échoue est perdue en silence. C'est le geste (c) de C.1', coché en août sur
-- les seules éditions de champs, jamais posé sur les actions.
--
-- POURQUOI IL N'EXISTAIT PAS. Le filet des éditions travaille sur une table
-- d'attente (`app_annonce_pending` et ses sœurs) qui porte l'INTENTION : la
-- ligne survit, le travail n'en est qu'une conséquence. Les actions n'ont pas
-- de table d'attente — le travail EST l'enregistrement. Il fallait donc un
-- filet qui travaille directement sur `app_console_job`.
--
-- ─────────────────────────────────────────────────────────────────────
-- LA CONDITION QU'IL A FALLU REMPLIR D'ABORD, et ce n'était pas évident
--
-- Un filet qui rejoue exige des vérifications qui ne dépendent pas de l'ordre
-- des choses. La vérification de l'annulation de compromis comparait la fiche
-- AVANT et APRÈS : rejouée sur un compromis déjà annulé, elle aurait déclaré
-- en échec un geste RÉUSSI, à chaque tentative, jusqu'à l'abandon. Le filet
-- aurait fabriqué de faux échecs en série.
--
-- Les neuf gestes ci-dessous ont donc été rendus ABSOLUS avant d'ouvrir le
-- filet (commits 192bf13, d05deec, a873bce), et le rejeu a été éprouvé :
-- annuler le compromis 50048 DÉJÀ annulé rend `done` en 3 secondes.
-- ─────────────────────────────────────────────────────────────────────
--
-- CE QUI EST VOLONTAIREMENT EXCLU, et c'est le cœur de la sûreté :
--
--   * les CRÉATIONS (contact, mandant, brouillon d'annonce, numéro de mandat)
--     et les DÉPÔTS (documents, photos) — rejouer une création la DOUBLE.
--     Aucune d'elles n'a de vérification absolue ; tant qu'elle n'en a pas,
--     elle ne doit pas être rejouée automatiquement ;
--   * les `update_hektor_*` — déjà couverts par le filet des éditions. Deux
--     mécanismes sur le même travail se marcheraient dessus.
--
-- L'ABANDON N'A PAS BESOIN D'UN NOUVEL ÉTAT. `app_console_job.status`
-- n'accepte que pending/running/done/error/pending_approval, et il n'y a rien
-- à y ajouter : `attempt_count >= 5` marque déjà l'abandon, puisque la règle
-- de rejeu ne regarde que les travaux en dessous. Un travail abandonné reste
-- donc en `error`, visible, et cesse simplement d'être repris.
-- =====================================================================

create or replace function public.app_console_action_enqueue_due_retries()
returns integer
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  n int := 0;
  r record;
  max_tentatives constant int := 5;
  -- Au-dela de cette anciennete, on ne rejoue plus : voir la note en fin de fichier.
  fraicheur constant interval := interval '24 hours';
  -- Uniquement les gestes IDEMPOTENTS dont l'effet se verifie de facon ABSOLUE.
  -- Toute addition a cette liste doit s'accompagner d'une verification absolue :
  -- sans elle, le rejeu transforme un succes en echec, ou double une creation.
  types_rejouables constant text[] := array[
    'archive_hektor_annonce',
    'restore_hektor_annonce',
    'delete_hektor_annonce',
    'delete_hektor_contact',
    'change_hektor_annonce_status',
    'assign_hektor_annonce_negotiator',
    'change_hektor_offre_status',
    'cancel_hektor_compromis',
    'delete_hektor_vente'
  ];
begin
  -- ── 1. LES TRAVAUX EN ERREUR, avec attente croissante : 5, 10, 15, 20 min ──
  for r in
    select j.id, j.job_type, j.attempt_count
    from public.app_console_job j
    where j.job_type = any (types_rejouables)
      and j.status = 'error'
      and coalesce(j.attempt_count, 0) between 1 and max_tentatives - 1
      and j.requested_at > now() - fraicheur
      and j.updated_at < now() - make_interval(mins => 5 * coalesce(j.attempt_count, 1))
    order by j.updated_at
    limit 50
  loop
    update public.app_console_job
       set status = 'pending', updated_at = now()
     where id = r.id and status = 'error';

    insert into public.app_console_job_log(job_id, step, status, message)
    values (r.id, 'retry', 'running',
            format('Rejeu automatique apres echec (tentative %s sur %s)',
                   coalesce(r.attempt_count, 1) + 1, max_tentatives));
    n := n + 1;
  end loop;

  -- ── 2. LES TRAVAUX RESTES EN COURS, signe d'un worker tombe en route ──
  -- 30 minutes : le plus long geste mesure tient en 45 secondes, la marge est
  -- large. Le rejeu est sans danger parce que chaque geste destructeur relit
  -- l'etat avant d'agir et n'envoie rien s'il ne le voit pas.
  for r in
    select j.id, j.attempt_count
    from public.app_console_job j
    where j.job_type = any (types_rejouables)
      and j.status = 'running'
      and coalesce(j.attempt_count, 0) < max_tentatives
      and j.requested_at > now() - fraicheur
      and coalesce(j.started_at, j.requested_at) < now() - interval '30 minutes'
    order by j.started_at
    limit 20
  loop
    update public.app_console_job
       set status = 'pending', worker_id = null, updated_at = now()
     where id = r.id and status = 'running';

    insert into public.app_console_job_log(job_id, step, status, message)
    values (r.id, 'retry', 'running',
            'Travail reste en cours plus de 30 minutes : remis en attente');
    n := n + 1;
  end loop;

  return n;
end
$function$;

revoke execute on function public.app_console_action_enqueue_due_retries() from public;
revoke execute on function public.app_console_action_enqueue_due_retries() from anon;
grant  execute on function public.app_console_action_enqueue_due_retries() to service_role;

-- ── LA SONDE : ce que le filet a renonce a reprendre ──
-- Un travail abandonne ne doit pas disparaitre du regard. Cette vue le montre,
-- avec ce qu'il portait, pour qu'un humain tranche.
drop view if exists public.app_console_action_abandonnees;

create view public.app_console_action_abandonnees as
select j.id,
       j.job_type,
       j.hektor_annonce_id,
       j.app_dossier_id,
       j.attempt_count,
       case
         when coalesce(j.attempt_count, 0) >= 5 then 'cinq tentatives epuisees'
         else 'trop ancien pour etre rejoue (plus de 24 h)'
       end as motif_abandon,
       j.error_message,
       j.requested_at,
       j.updated_at,
       j.payload_json
from public.app_console_job j
where j.status = 'error'
  and (coalesce(j.attempt_count, 0) >= 5
       or j.requested_at <= now() - interval '24 hours')
order by j.updated_at desc;

revoke all on public.app_console_action_abandonnees from public;
revoke all on public.app_console_action_abandonnees from anon;
grant select on public.app_console_action_abandonnees to authenticated, service_role;

-- =====================================================================
-- AJOUT DU MEME JOUR — LA LIMITE DE FRAICHEUR
--
-- Trouve en regardant CE QUE LE FILET AURAIT REJOUE avant de le lancer :
-- un change_hektor_annonce_status du 28/08, tombe sur un « Hektor 500 ».
-- Le rejouer deux jours plus tard aurait repose un statut decide avant-hier,
-- par-dessus un etat peut-etre plus recent.
--
-- Un filet doit rattraper un incident, pas ressusciter une decision oubliee.
-- Au-dela de 24 h, le travail reste en erreur et attend un humain.
--
--     and j.requested_at > now() - interval '24 hours'
--
-- La sonde app_console_action_abandonnees montre les DEUX motifs d'abandon,
-- pour qu'aucun ne se cache : « cinq tentatives epuisees » et « trop ancien ».
--
-- CRON : app-action-retry-due, toutes les minutes (jobid 13), aux cotes des
-- trois filets d'edition qui tournent deja au meme rythme.
--
-- EPROUVE LE 30/08 : le filet a repris le travail 09e649f3
-- (cancel_hektor_compromis 50047), en echec depuis la veille a cause du defaut
-- de relecture corrige depuis. Journal :
--     retry:running   Rejeu automatique apres echec (tentative 2 sur 5)
--     claim:running   repris par le worker
--     ...error        « Le compromis 50047 n'existe plus du tout » -- dit, pas cache
--     finish:done     resolu
-- Premier rejeu automatique du projet.
-- =====================================================================
