-- ═══════════════════════════════════════════════════════════════════════════
-- C.1' — UNE SAISIE NE SE PERD JAMAIS : LES DEUX CAUSES SE SEPARENT  20/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- REGLE DE FREDERIC, 20/09 : « l'ecriture de l'utilisateur est saisie donc
-- protegee, sauf en cas d'ecriture plus recente chez Hektor. C'est moi qui dois
-- etre prevenu, puisque ce serait un bug entre Hektor et l'app. L'utilisateur,
-- lui, ne peut rien y faire. »
--
-- CE QUI CLOCHAIT : un SEUL etat, « conflit », recouvrait deux situations
-- opposees, et le code ne savait pas les distinguer -- app_annonce_pending_resolve
-- les DEVINAIT (« push_attempts >= 5 ? »), ce qui est une heuristique, pas un fait.
--
--   A. HEKTOR EST PLUS RECENT   quelqu'un a modifie la fiche dans Hektor apres la
--      saisie. Hektor gagne, c'est la regle. La saisie de l'app est soldee, avec
--      sa trace -- ce n'est PAS un incident.
--   B. L'ENVOI A ECHOUE         Hektor injoignable, session morte, 5 tentatives.
--      Personne n'a rien modifie : c'est un BUG entre Hektor et l'app. La saisie
--      se garde, se REESSAIE, et ne s'efface JAMAIS.
--
-- ⚠ ET LE DEFAUT QUI RENDAIT TOUT CELA VAIN : une saisie PARTIELLE (Hektor a
--   ignore un champ) etait remise en file A CHAQUE PASSAGE -- sans incrementer le
--   compteur, sans repousser le delai. Soit UNE ECRITURE CHEZ HEKTOR PAR MINUTE,
--   indefiniment : exactement le profil de trafic qui a fait bannir notre IP trois
--   fois en septembre. 0 ligne dans cet etat a ce jour : le defaut n'a jamais mordu.
--
-- RETOUR ARRIERE : les definitions d'avant sont dans le commit de ce patch
-- (scratchpad defs_actuelles.sql) ; la colonne `cause` peut rester, personne
-- n'echoue si elle est vide.
-- ═══════════════════════════════════════════════════════════════════════════

-- ── 1. LA CAUSE DEVIENT UN FAIT, PLUS UNE DEVINETTE ────────────────────────
alter table public.app_annonce_pending add column if not exists cause text;
alter table public.app_contact_pending add column if not exists cause text;

comment on column public.app_annonce_pending.cause is
  'C.1 prime, 20/09 : pourquoi la ligne est en conflit. hektor_plus_recent = Hektor a ete modifie depuis la saisie (il gagne, la ligne est soldee par le worker) ; envoi_impossible = l''envoi a echoue (on garde, on reessaie, on alerte Frederic). NULL = pas de conflit.';

-- ── 2. LA MISE EN FILE ─────────────────────────────────────────────────────
create or replace function public.app_annonce_enqueue_due_pushes()
 returns integer
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare r record; n int := 0; jid uuid; max_attempts int := 5;
begin
  delete from public.app_annonce_pending p
  using public.app_console_job j
  where p.push_job_id = j.id and j.status = 'done' and p.conflict = false;

  -- C.1' 24/08 : LA PURGE DES 24 H EST RETIREE.
  -- Elle effacait la ligne ET la saisie (base_snapshot + push_fields) : une
  -- edition bloquee etait perdue au bout d'un jour, vue ou pas. Desormais elle
  -- reste jusqu'a ce qu'un humain la traite (bandeau sur la fiche + sonde).

  update public.app_annonce_pending p
  set push_job_id = null,
      push_after = now() + make_interval(mins => 5 * (p.push_attempts + 1)),
      push_attempts = p.push_attempts + 1,
      updated_at = now()
  where p.push_job_id is not null and p.conflict = false and p.push_attempts < max_attempts
    and (
      not exists (select 1 from public.app_console_job j where j.id = p.push_job_id)
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id and j.status = 'error')
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id
                 and j.finished_at is null and j.requested_at < now() - interval '30 minutes')
    );

  -- 5 TENTATIVES SANS SUCCES = CAUSE B. On nomme la cause : c'est un bug entre
  -- Hektor et l'app, pas une modification faite chez Hektor. Le prochain essai
  -- est repousse a 6 h : on ne martele pas, et l'envoi repartira tout seul quand
  -- Hektor reviendra (20/09).
  update public.app_annonce_pending p
  set conflict = true,
      cause = coalesce(p.cause, 'envoi_impossible'),
      push_after = greatest(coalesce(p.push_after, now()), now() + interval '6 hours'),
      updated_at = now()
  where p.push_job_id is not null and p.conflict = false and p.push_attempts >= max_attempts
    and (
      not exists (select 1 from public.app_console_job j where j.id = p.push_job_id)
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id and j.status = 'error')
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id
                 and j.finished_at is null and j.requested_at < now() - interval '30 minutes')
    );

  for r in select * from public.app_annonce_pending
           where push_after <= now() and push_job_id is null
             -- ⬇ LE CORRECTIF DU 01/09 : « qui a du contenu », et non « qui n'est
             --   pas absent ». Un verrou de diffusion porte {} : il reste dans la
             --   bannette, et c'est le read-through qui le leve, pas le pousseur.
             and push_fields is not null
             and jsonb_typeof(push_fields) = 'object'
             and push_fields <> '{}'::jsonb
             -- ⬇ 20/09 : UNE SAISIE PARTIELLE NE SE RENVOIE PLUS. Hektor a deja
             --   ignore ce champ une fois ; le renvoyer ne change rien et produit
             --   une ecriture par minute. Elle reste affichee et attend une
             --   nouvelle edition, qui remet partial a false.
             and coalesce(partial, false) = false
             -- ⬇ 20/09 : la REPRISE ESPACEE. Une ligne en conflit de cause B
             --   repart -- toutes les 6 h, jamais plus vite. Une ligne de cause A
             --   (Hektor plus recent) n'existe plus a ce stade : le worker l'a
             --   soldee avec sa trace.
             and (conflict = false or cause = 'envoi_impossible')
           order by push_after limit 100 loop
    insert into public.app_console_job(job_type, app_dossier_id, hektor_annonce_id, payload_json, status, priority, requested_at)
    values ('update_hektor_annonce_fields', r.app_dossier_id, r.hektor_annonce_id,
      coalesce(r.push_fields, '{}'::jsonb) || jsonb_build_object(
        'app_dossier_id', r.app_dossier_id,
        'hektor_annonce_id', r.hektor_annonce_id,
        'from_pending', true,
        'base_snapshot', r.base_snapshot,
        'source', coalesce(r.source, 'nego_app')),
      'pending', 70, now())
    returning id into jid;
    update public.app_annonce_pending
       set push_job_id = jid,
           -- une reprise de cause B ne retentera pas avant 6 h, quoi qu'il arrive
           push_after = case when r.conflict then now() + interval '6 hours' else push_after end,
           updated_at = now()
     where app_dossier_id = r.app_dossier_id;
    n := n + 1;
  end loop;
  return n;
end
$function$;

-- ── 3. SOLDER UNE SAISIE QUE HEKTOR A DEPASSEE (cause A) ───────────────────
-- Appelee par le worker quand son garde-fou constate que Hektor est plus recent.
-- Hektor gagne -- mais la saisie de l'app N'EST PAS PERDUE : elle part au journal
-- des resolutions, avec sa valeur, son auteur et son heure. C'est la difference
-- entre « abandonner » et « effacer ».
create or replace function public.app_annonce_pending_solder_hektor(
  target_dossier_id bigint,
  detail jsonb default '{}'::jsonb
) returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare p app_annonce_pending%rowtype;
begin
  select * into p from public.app_annonce_pending where app_dossier_id = target_dossier_id;
  if not found then
    return jsonb_build_object('solde', false, 'reason', 'rien_en_attente');
  end if;

  insert into public.app_pending_resolution
    (objet, app_dossier_id, hektor_annonce_id, mode, cause, push_attempts, payload_json, resolved_by)
  values
    ('annonce', target_dossier_id, p.hektor_annonce_id, 'abandon', 'hektor_plus_recent',
     coalesce(p.push_attempts, 0),
     jsonb_build_object('push_fields', p.push_fields,
                        'base_snapshot', p.base_snapshot,
                        'skipped_fields', p.skipped_fields,
                        'dirty_at', p.dirty_at,
                        'dirty_by', p.dirty_by,
                        'source', p.source,
                        'detail', coalesce(detail, '{}'::jsonb)),
     'worker');

  delete from public.app_annonce_pending where app_dossier_id = target_dossier_id;
  return jsonb_build_object('solde', true, 'cause', 'hektor_plus_recent');
end
$function$;

grant execute on function public.app_annonce_pending_solder_hektor(bigint, jsonb) to service_role;

-- ── 4. LA RESOLUTION HUMAINE LIT LA CAUSE AU LIEU DE LA DEVINER ────────────
create or replace function public.app_annonce_pending_resolve(target_dossier_id bigint, mode text)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  d app_dossier_current%rowtype;
  p app_annonce_pending%rowtype;
  v_cause text;
begin
  if mode not in ('refait','abandon') then
    raise exception 'mode_invalide' using errcode='22023';
  end if;

  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode='22023'; end if;

  -- Meme controle d'acces que la lecture du statut.
  if not public.app_console_can_request_job('update_hektor_annonce_fields', target_dossier_id, d.hektor_annonce_id::text) then
    raise exception 'forbidden_annonce_resolve' using errcode='42501';
  end if;

  select * into p from app_annonce_pending where app_dossier_id = target_dossier_id;
  if not found then
    return jsonb_build_object('resolved', false, 'reason', 'rien_en_attente');
  end if;

  -- 20/09 : LA CAUSE EST UN FAIT, PORTE PAR LA LIGNE. L'heuristique d'avant
  -- (« 5 tentatives ? alors envoi impossible ») se trompait des qu'un garde-fou
  -- bloquait apres plusieurs essais.
  v_cause := coalesce(p.cause,
               case when coalesce(p.push_attempts,0) >= 5 then 'envoi_impossible'
                    else 'modifie_dans_hektor' end);

  insert into public.app_pending_resolution
    (objet, app_dossier_id, hektor_annonce_id, mode, cause, push_attempts, payload_json, resolved_by)
  values
    ('annonce', target_dossier_id, d.hektor_annonce_id::text, mode, v_cause, coalesce(p.push_attempts,0),
     jsonb_build_object('push_fields', p.push_fields,
                        'base_snapshot', p.base_snapshot,
                        'skipped_fields', p.skipped_fields,
                        'dirty_at', p.dirty_at,
                        'dirty_by', p.dirty_by,
                        'source', p.source),
     coalesce(auth.jwt() ->> 'email', current_user));

  delete from public.app_annonce_pending where app_dossier_id = target_dossier_id;

  return jsonb_build_object('resolved', true, 'mode', mode, 'cause', v_cause);
end
$function$;
