-- =====================================================================
-- UN REJEU S'EFFACE DEVANT UN SUCCES PLUS RECENT          14/09/2026
-- Complete C.4-bis (patch_c4bis_filet_rejeu_actions_2026-08-30.sql).
-- =====================================================================
--
-- CE QU'ON A VU, ET QUI N'ETAIT PAS PREVU
-- ---------------------------------------
-- 13/09, bien temoin. Un travail de modification echoue a 07:47 (Hektor refuse
-- un intervenant absent de sa liste). Deux travaux PLUS RECENTS reussissent
-- ensuite, a 07:48 puis 07:51, chacun avec un prix plus recent. A 07:53 le
-- filet rejoue le PREMIER -- et repose SON prix, 183 000, par-dessus le 184 000
-- saisi six minutes plus tard.
--
-- ⚠ RIEN N'ETAIT INCOHERENT : Hektor et le registre affichaient tous deux
--   183 000. C'est bien pire qu'une incoherence -- l'intention LA PLUS RECENTE
--   avait disparu sans laisser de trace, et les deux cotes etaient d'accord sur
--   la mauvaise valeur. Une divergence se voit ; celle-ci, non.
--
-- CE QUE LE FILET NE REGARDAIT PAS. Il verifie l'age, le nombre de tentatives et
-- le delai d'attente. Il ne se demande jamais si QUELQU'UN A FAIT MIEUX DEPUIS.
--
-- LA MESURE, sur 60 jours et sur les seuls changements de statut :
--     11 rejeux, dont 8 APRES un succes plus recent sur le meme bien.
-- ⚠ MAIS 8 DE CES 11 SONT SUR LE BIEN D'ESSAI, martele toute la journee du 13.
--   En exploitation reelle le cas est RARE -- un seul bien, le 30/08. Ce qui est
--   certain, c'est que le mecanisme le permet et que rien ne le signale.
--
-- L'ARBITRAGE DE FREDERIC, 14/09 : un rejeu s'efface devant un succes plus
-- recent, et il est marque comme DEPASSE plutot que laisse en erreur muette.
--
-- ⚠ POURQUOI « DEPASSE » N'EST PAS UN NOUVEL ETAT. `app_console_job.status`
--   n'accepte que pending/running/done/error/pending_approval, et C.4-bis a deja
--   tranche : « attempt_count >= 5 marque deja l'abandon ». On reutilise donc le
--   meme signal -- le travail reste en `error`, VISIBLE, cesse d'etre repris, et
--   son `error_message` DIT pourquoi. Ajouter un etat obligerait a toucher a
--   toutes les lectures existantes pour un cas rare.
--
-- ⚠ ON COMPARE PAR BIEN, PAS PAR AFFAIRE, et c'est volontaire. Un travail de
--   statut porte parfois un numero d'affaire, parfois non (une creation n'en a
--   pas encore). Le bien, lui, est toujours la. Comparer par affaire laisserait
--   passer precisement le cas qui nous a mordu.
-- ⚠ ET SEULEMENT ENTRE TRAVAUX DU MEME TYPE : un archivage reussi ne rend pas
--   caduque une modification de prix.
--
-- RETOUR ARRIERE : rejouer le patch du 30/08, qui redefinit la fonction sans ce
-- garde-fou. Rien d'autre a defaire.
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
  fraicheur constant interval := interval '24 hours';
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
  -- ── 0. LES TRAVAUX QU'UN PLUS RECENT A DEPASSES ──              14/09/2026
  -- On les retire de la file AVANT de rejouer quoi que ce soit : les traiter
  -- apres laisserait une fenetre ou l'un d'eux repartirait quand meme.
  for r in
    select j.id, j.job_type, j.app_dossier_id, j.attempt_count
    from public.app_console_job j
    where j.job_type = any (types_rejouables)
      and j.status = 'error'
      and coalesce(j.attempt_count, 0) between 1 and max_tentatives - 1
      and j.requested_at > now() - fraicheur
      and exists (
        select 1
        from public.app_console_job plus_recent
        where plus_recent.app_dossier_id = j.app_dossier_id
          and plus_recent.job_type = j.job_type
          and plus_recent.id <> j.id
          and plus_recent.status = 'done'
          -- « plus recent » se juge sur la DEMANDE, pas sur la fin : c'est
          -- l'intention qui compte, et c'est elle qu'on ne doit pas ecraser.
          and plus_recent.requested_at > j.requested_at
      )
    limit 50
  loop
    update public.app_console_job
       set attempt_count = max_tentatives,
           error_message = coalesce(nullif(error_message, ''), '')
             || case when coalesce(error_message, '') = '' then '' else ' | ' end
             || 'DEPASSE : un travail plus recent du meme type a reussi sur ce bien. '
             || 'Rejouer celui-ci reposerait une valeur plus ancienne.',
           updated_at = now()
     where id = r.id and status = 'error';

    insert into public.app_console_job_log(job_id, step, status, message)
    values (r.id, 'retry', 'done',
            'Rejeu ABANDONNE : un travail plus recent du meme type a deja reussi '
            || 'sur ce bien. Le rejouer reposerait une valeur perimee -- c''est ce '
            || 'qui est arrive le 13/09, ou un prix de 183 000 a efface un 184 000 '
            || 'saisi six minutes plus tard.');
  end loop;

  -- ── 1. LES TRAVAUX EN ERREUR, avec attente croissante : 5, 10, 15, 20 min ──
  -- La boucle 0 vient de porter les depasses a `attempt_count = max_tentatives` :
  -- ils sortent donc d'eux-memes de la condition ci-dessous.
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
    limit 50
  loop
    update public.app_console_job
       set status = 'pending', updated_at = now()
     where id = r.id and status = 'running';

    insert into public.app_console_job_log(job_id, step, status, message)
    values (r.id, 'retry', 'running',
            format('Reprise apres interruption (tentative %s sur %s)',
                   coalesce(r.attempt_count, 1) + 1, max_tentatives));
    n := n + 1;
  end loop;

  return n;
end;
$function$;

COMMENT ON FUNCTION public.app_console_action_enqueue_due_retries() IS
    'Rejoue les actions echouees ou interrompues (C.4-bis, 30/08). Depuis le '
    '14/09, un travail qu''un PLUS RECENT du meme type a deja reussi sur le meme '
    'bien n''est plus rejoue : il serait reparti avec une valeur perimee. Il est '
    'porte a 5 tentatives -- donc abandonne -- et son error_message dit pourquoi.';
