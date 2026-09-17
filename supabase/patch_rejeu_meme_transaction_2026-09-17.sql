-- ═══════════════════════════════════════════════════════════════════════════════
-- LE FILET DE REJEU : « DEPASSE » SE JUGE SUR LA TRANSACTION ET SES INTENTIONS
--                     + LA SUPPRESSION DE COMPROMIS ENTRE DANS LE FILET  17/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Remplace la version du 14/09 (patch_rejeu_depasse_2026-09-14.sql). Les sections
-- 1 et 2 sont recopiees A L'IDENTIQUE de la definition en base ; seules changent
-- la liste des types et la condition de la section 0.
--
-- ─── DEFAUT 1 : LE GRAIN ETAIT FAUX ───
-- La regle du 14/09 est nee d'un vrai incident, et elle reste juste dans son
-- intention : le 13/09, un prix de 183 000 (demande 09:47, echoue puis rejoue)
-- a efface un 184 000 saisi a 09:51. Rejouer une intention depassee repose une
-- valeur perimee.
-- MAIS ELLE JUGEAIT « MEME BIEN, MEME TYPE DE TRAVAIL ». Or TOUS les gestes de
-- transaction -- creer, modifier, sur les trois genres -- portent le meme type,
-- `change_hektor_annonce_status`. Donc :
--     un ajout d'acquereur echoue, puis un simple changement de prix reussit --
--     sur la meme transaction OU sur une autre du meme bien -- et l'ajout est
--     declare « depasse » et n'est JAMAIS rejoue. Perdu, sans un mot.
-- MESURE sur l'historique : les travaux en erreur etaient apparies par l'ancienne
-- regle a 10, 32, 46 et 47 travaux « plus recents » -- presque tous sur D'AUTRES
-- transactions. C'est deja arrive une fois : le 16/09 a 10:37, sur 24933, un
-- travail qui portait des personnes (donnees de test, sans consequence ce jour-la).
--
-- ➡ UN TRAVAIL N'EST DEPASSE QUE PAR UN TRAVAIL :
--     ① sur la MEME transaction (meme `app_affaire_id` dans la charge) --
--        ou, pour une creation qui n'en a pas encore, une creation du meme genre
--        (meme `target_status`) ;
--     ② ET qui porte AU MOINS LES MEMES INTENTIONS. Les montants et les dates
--        sont presents dans presque toutes les charges, leur presence ne dit
--        pas « modifie ». Les intentions, si -- et le projet les marque deja :
--            acquereurs_affirmes = true
--            mandant_contact_ids = un TABLEAU   (null = « l'app n'y a pas touche »)
--            notaires_affirmes   = { acquereur: true, mandant: true }
--        Un travail qui affirmait des personnes n'est pas depasse par un travail
--        qui ne les affirme pas.
--
-- ⚠ PIEGE TROUVE EN REJOUANT LA REGLE SUR L'HISTORIQUE, AVANT DE L'ECRIRE : quand
--   un drapeau est ABSENT, la comparaison vaut NULL, et `NOT (NULL)` reste NULL,
--   donc faux. Ecrite naivement, la regle n'aurait PLUS JAMAIS declare un travail
--   depasse -- y compris l'incident du 13/09 qu'elle existe pour empecher. D'ou les
--   `coalesce` des deux cotes de chaque comparaison.
--
-- EPROUVE sur cinq cas, dont deux reels :
--     13/09 : 183 000 depasse par 184 000, meme transaction      -> DEPASSE  ✓
--     compromis 1001347 depasse par la vente 1001351             -> NON      ✓
--     charge sans aucun drapeau, meme transaction                -> DEPASSE  ✓
--     acquereurs affirmes, puis un prix seul, meme transaction   -> NON      ✓
--     mandants affirmes, puis une charge qui les reaffirme       -> DEPASSE  ✓
--
-- ⚠ LIMITE CONNUE, NON RESOLUE ICI : si le negociateur reaffirme une liste de
--   personnes SANS celle qu'il avait ajoutee (parce que l'ecran ne la lui a jamais
--   montree -- les personnes ne s'affichent pas en attente), le nouveau travail
--   depasse legitimement l'ancien, et l'ajout se perd quand meme. C'est le defaut
--   « les personnes n'ont pas d'affichage en attente », a traiter a part.
--
-- ─── DEFAUT 2 : LA SUPPRESSION DE COMPROMIS N'ETAIT PAS REJOUEE ───
-- `delete_hektor_compromis` est ne le 07/09 ; la liste date du 30/08 et n'a pas ete
-- completee le 14/09. Un compromis dont la suppression echouait restait en erreur
-- pour toujours. La suppression de VENTE, elle, etait couverte.
-- ⚠ LE REJEU EST SUR, VERIFIE DANS LE GESTIONNAIRE : il exige `confirmer=true`,
--   RELIT AVANT d'agir (« n'existe deja plus chez Hektor : rien n'a ete envoye »)
--   et relit apres. Une seconde tentative ne peut pas frapper deux fois.
--
-- RETOUR ARRIERE : rejouer patch_rejeu_depasse_2026-09-14.sql.
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.app_console_action_enqueue_due_retries()
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
    'delete_hektor_vente',
    -- 17/09 : absente depuis sa naissance le 07/09. Sure a rejouer : le
    -- gestionnaire relit avant d'agir et n'envoie rien s'il ne voit plus rien.
    'delete_hektor_compromis'
  ];
begin
  -- ── 0. LES TRAVAUX QU'UN PLUS RECENT A DEPASSES ──     14/09, grain corrige le 17/09
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
          -- ① LA MEME TRANSACTION -- et pas seulement le meme bien (17/09).
          and (
                ( nullif(coalesce(j.payload_json->>'app_affaire_id', ''), '') is not null
                  and coalesce(plus_recent.payload_json->>'app_affaire_id', '')
                      = j.payload_json->>'app_affaire_id' )
             or ( nullif(coalesce(j.payload_json->>'app_affaire_id', ''), '') is null
                  and nullif(coalesce(plus_recent.payload_json->>'app_affaire_id', ''), '') is null
                  and coalesce(plus_recent.payload_json->>'target_status', '')
                      = coalesce(j.payload_json->>'target_status', '') )
              )
          -- ② AU MOINS LES MEMES INTENTIONS (17/09). ⚠ `coalesce` des DEUX cotes :
          --   un drapeau absent vaut NULL, et NOT(NULL) n'est pas vrai.
          and not ( coalesce(j.payload_json->'acquereurs_affirmes', 'null'::jsonb) = 'true'::jsonb
                    and coalesce(plus_recent.payload_json->'acquereurs_affirmes', 'null'::jsonb)
                        <> 'true'::jsonb )
          and not ( coalesce(jsonb_typeof(j.payload_json->'mandant_contact_ids'), 'null') = 'array'
                    and coalesce(jsonb_typeof(plus_recent.payload_json->'mandant_contact_ids'), 'null')
                        <> 'array' )
          and not ( coalesce(j.payload_json->'notaires_affirmes'->>'acquereur', '') = 'true'
                    and coalesce(plus_recent.payload_json->'notaires_affirmes'->>'acquereur', '')
                        <> 'true' )
          and not ( coalesce(j.payload_json->'notaires_affirmes'->>'mandant', '') = 'true'
                    and coalesce(plus_recent.payload_json->'notaires_affirmes'->>'mandant', '')
                        <> 'true' )
      )
    limit 50
  loop
    update public.app_console_job
       set attempt_count = max_tentatives,
           error_message = coalesce(nullif(error_message, ''), '')
             || case when coalesce(error_message, '') = '' then '' else ' | ' end
             || 'DEPASSE : un travail plus recent a reussi sur la MEME transaction, '
             || 'avec au moins les memes intentions. Rejouer celui-ci reposerait une '
             || 'valeur plus ancienne.',
           updated_at = now()
     where id = r.id and status = 'error';

    insert into public.app_console_job_log(job_id, step, status, message)
    values (r.id, 'retry', 'done',
            'Rejeu ABANDONNE : un travail plus recent a deja reussi sur la MEME '
            || 'transaction, avec au moins les memes intentions. Le rejouer reposerait '
            || 'une valeur perimee -- c''est ce qui est arrive le 13/09, ou un prix de '
            || '183 000 a efface un 184 000 saisi six minutes plus tard.');
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
