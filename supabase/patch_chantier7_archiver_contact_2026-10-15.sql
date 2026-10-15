-- ============================================================================
-- CHANTIER ⑦ POINT ⑦-1 -- ARCHIVER / DESARCHIVER UN CONTACT : LA BASE
-- 15/10/2026
-- ============================================================================
-- CE QUE CE PATCH FAIT, et rien de plus : il ouvre UN SEUL type de travail
-- neuf, `archive_hektor_contact`, et pose la fonction de saisie qui coche
-- l'interrupteur CHEZ NOUS et cree le travail dans la MEME transaction.
--
-- LES DECISIONS DE FREDERIC QU'IL APPLIQUE (15/10) :
--   · « 2. B »     -> le NEGOCIATEUR peut archiver SES contacts (pas seulement
--                     admin et manager). Le type rejoint donc la liste des 4
--                     deja ouverts au commercial, sans rien reecrire.
--   · « 3. Oui »   -> UN SEUL geste, avec un interrupteur : c'est la charge du
--                     travail qui porte le sens (`archive` true/false), exactement
--                     comme Hektor, qui n'a qu'un ordre pour les deux sens.
--   · « 1 menu »   -> l'ecran mettra l'item dans le menu « … » de la fiche (hors
--                     de ce patch : c'est du front).
--   · « 2 a »      -> le bouton s'affichera toujours et le REFUS sera une phrase
--                     en francais -> d'ou le message clair leve ici, et pas un
--                     code machine comme `forbidden_update_contact`.
--
-- LA COMMANDE HEKTOR, relevee en lecture seule le 15/10 (sonde_archive_contact.js,
-- confirmee identique a la capture du 01/06) :
--     POST xmlrpc.php  mode=contacts-contactProfile-archiveContact
--                      id=<idContact>  archive=<true|false>
--
-- ⚠ LES TROIS VERROUS D'UN NOUVEAU TYPE DE TRAVAIL (paye le 14/10) : la
--   CONTRAINTE, les DROITS, et la DISTRIBUTION. Oublier le troisieme = un travail
--   qui reste « pending » a vie, SANS erreur, parce qu'aucun service ne le reclame.
--
-- ⚠ CE QUI N'EST PAS DANS CE PATCH, volontairement :
--   · le worker (il faut son « vas-y », puis le redemarrage des QUATRE services) ;
--   · l'ecran ;
--   · le filet de rejeu (`app_console_action_enqueue_due_retries`) : on n'y touche
--     PAS. Un travail en erreur sonnera dans l'ecran Sante (l'alerte compte tous
--     les types) et c'est voulu pour un premier lot. L'archivage est pourtant
--     idempotent : on pourra l'y ajouter plus tard, c'est une ligne.
--
-- ⚠ CE PATCH NE RECOPIE AUCUNE FONCTION. Il les LIT dans la base, verifie que son
--   ancre est unique et que le texte n'est pas deja la, insere apres l'ancre et
--   reexecute -- le corps d'origine est conserve au caractere pres.
-- ⚠ FINS DE LIGNE : chaque ancre, chaque texte insere et chaque definition lue est
--   enveloppe de `replace(..., chr(13), '')`. Ancres MULTI-LIGNES : ZERO (toutes
--   mesurees sur une seule ligne, chacune vue exactement 1 fois le 15/10).
-- ⚠ COUT MESURE : la contrainte est refaite, donc PostgreSQL revalide
--   `app_console_job` -- 95 483 lignes le 15/10, verrou exclusif le temps de la
--   transaction. A coller hors des moments charges (pas pendant le run de 05:00,
--   pas a 22:00).
-- ============================================================================

begin;

-- ---------------------------------------------------------------------------
-- VERROU 1 sur 3 -- LA CONTRAINTE : le type devient permis
-- ---------------------------------------------------------------------------
do $do$
declare
  v_def   text;
  v_new   text;
  v_ancre text := replace('''archive_hektor_annonce''::text', chr(13), '');
  v_ajout text := replace('''archive_hektor_annonce''::text, ''archive_hektor_contact''::text', chr(13), '');
  v_vu    integer;
begin
  select replace(pg_get_constraintdef(oid), chr(13), '')
    into v_def
  from pg_constraint
  where conrelid = 'public.app_console_job'::regclass
    and conname  = 'app_console_job_job_type_check';

  if v_def is null then
    raise exception 'STOP : contrainte app_console_job_job_type_check introuvable';
  end if;

  if position(replace('archive_hektor_contact', chr(13), '') in v_def) > 0 then
    raise notice 'VERROU 1 : DEJA FAIT (le type est dans la contrainte)';
    return;
  end if;

  v_vu := (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 1 then
    raise exception 'STOP : l''ancre de la contrainte apparait % fois (attendu 1)', v_vu;
  end if;

  v_new := replace(v_def, v_ancre, v_ajout);

  execute 'alter table public.app_console_job drop constraint app_console_job_job_type_check';
  execute 'alter table public.app_console_job add constraint app_console_job_job_type_check ' || v_new;
  raise notice 'VERROU 1 : pose';
end
$do$;

-- ---------------------------------------------------------------------------
-- VERROU 2 sur 3 -- LES DROITS : le negociateur sur SES contacts (option B)
-- ---------------------------------------------------------------------------
-- La fonction a deja la bonne forme : admin et manager passent partout ; le
-- commercial doit prouver que le contact est a lui (son negociateur, OU un
-- contact lie a un bien auquel il a acces). On ajoute seulement notre type a la
-- liste des quatre qui beneficient deja de ce controle.
do $do$
declare
  v_src   text;
  v_new   text;
  v_ancre text := replace('''delete_hektor_contact_search'')', chr(13), '');
  v_ajout text := replace('''delete_hektor_contact_search'',''archive_hektor_contact'')', chr(13), '');
  v_vu    integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '')
    into v_src
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_console_can_request_contact_job';

  if v_src is null then
    raise exception 'STOP : app_console_can_request_contact_job introuvable';
  end if;

  if position(replace('archive_hektor_contact', chr(13), '') in v_src) > 0 then
    raise notice 'VERROU 2 : DEJA FAIT (le type est dans les droits)';
    return;
  end if;

  v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 1 then
    raise exception 'STOP : l''ancre des droits apparait % fois (attendu 1)', v_vu;
  end if;

  v_new := replace(v_src, v_ancre, v_ajout);
  execute v_new;
  raise notice 'VERROU 2 : pose';
end
$do$;

-- ---------------------------------------------------------------------------
-- VERROU 3 sur 3 -- LA DISTRIBUTION : quel service reclame le travail
-- ---------------------------------------------------------------------------
-- Le service « actions » et pas « admin ». Ce n'est pas un gout : c'est la regle
-- ecrite dans le worker a propos de cette liste -- « meme session negociateur,
-- meme objet, meme famille de geste ». Le service « admin » travaille avec la
-- session ADMIN et porte les gestes reserves (supprimer un contact), que le
-- negociateur n'a pas. Notre geste est ouvert au negociateur : il va avec ses
-- autres gestes contact (creer, modifier, recherches).
do $do$
declare
  v_src   text;
  v_new   text;
  v_ancre text := replace('''unlink_hektor_mandant''))', chr(13), '');
  v_ajout text := replace('''unlink_hektor_mandant'',''archive_hektor_contact''))', chr(13), '');
  v_vu    integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '')
    into v_src
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_console_claim_next_job';

  if v_src is null then
    raise exception 'STOP : app_console_claim_next_job introuvable';
  end if;

  if position(replace('archive_hektor_contact', chr(13), '') in v_src) > 0 then
    raise notice 'VERROU 3 : DEJA FAIT (le type est dans la distribution)';
    return;
  end if;

  v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 1 then
    raise exception 'STOP : l''ancre de la distribution apparait % fois (attendu 1)', v_vu;
  end if;

  v_new := replace(v_src, v_ancre, v_ajout);
  execute v_new;
  raise notice 'VERROU 3 : pose';
end
$do$;

-- ---------------------------------------------------------------------------
-- LA SAISIE -- fonction NEUVE, elle n'ecrase rien
-- ---------------------------------------------------------------------------
-- Elle fait DEUX choses dans UNE transaction : elle coche l'interrupteur chez
-- nous (« chez nous d'abord », chantier ③) et elle cree le travail pour Hektor.
-- Si Hektor refuse, le travail passe en erreur -> l'ecran Sante le compte, et la
-- nuit suivante le run remet la verite de Hektor. Les contacts n'ont pas de
-- carnet comme les annonces : ce retour arriere est NATUREL, mais MUET -- c'est
-- dit, pas decouvert.
create or replace function public.app_console_archiver_contact_optimistic(
  p_hektor_contact_id text,
  p_archive boolean
)
returns public.app_console_job
language plpgsql
security definer
set search_path to 'public'
as $fn$
declare
  c           public.app_contact_current%rowtype;
  created_job public.app_console_job;
  clean_id    text;
begin
  clean_id := nullif(trim(coalesce(p_hektor_contact_id, '')), '');
  if clean_id is null or clean_id !~ '^[0-9]+$' then
    raise exception 'invalid_contact_id' using errcode = '22023';
  end if;
  if p_archive is null then
    raise exception 'archive_manquant' using errcode = '22023';
  end if;

  select * into c from public.app_contact_current where hektor_contact_id = clean_id;
  if not found then
    raise exception 'contact_not_found' using errcode = '22023';
  end if;

  -- LE DROIT (option B). Le message est une PHRASE, pas un code : l'ecran
  -- affiche ce texte tel quel, et Frederic a choisi « le bouton reste visible,
  -- le refus s'explique » -- sinon c'est un bouton menteur.
  if not public.app_console_can_request_contact_job('archive_hektor_contact', clean_id, c.negociateur_email) then
    raise exception 'Ce contact n''est pas dans votre portefeuille : vous ne pouvez pas changer son archivage.'
      using errcode = '42501';
  end if;

  -- RIEN A FAIRE : on ne cree pas un travail Hektor pour un etat deja atteint.
  if coalesce(c.archive, false) = p_archive then
    if p_archive then
      raise exception 'Ce contact est deja archive.' using errcode = '22023';
    else
      raise exception 'Ce contact est deja actif.' using errcode = '22023';
    end if;
  end if;

  update public.app_contact_current
     set archive = p_archive
   where hektor_contact_id = clean_id;

  -- La charge porte les DEUX cles (`hektor_contact_id` et `contact_id`) parce que
  -- la distribution et le worker lisent l'une OU l'autre -- patron recopie de
  -- app_console_create_delete_contact_job.
  -- ⚠ Le numero pose ici est le NOTRE (app_contact_current.hektor_contact_id est
  --   >= 10 000 000) : c'est le worker qui traduit vers la cible Hektor.
  insert into public.app_console_job (
    job_type, app_dossier_id, hektor_annonce_id, payload_json,
    status, priority, requested_by, requested_at
  )
  values (
    'archive_hektor_contact', null, null,
    jsonb_build_object(
      'hektor_contact_id', clean_id,
      'contact_id',        clean_id,
      'archive',           p_archive,
      'base_snapshot',     jsonb_build_object('archive', coalesce(c.archive, false))
    ),
    'pending', 6, auth.uid(), now()
  )
  returning * into created_job;

  return created_job;
end;
$fn$;

-- Les droits de la fonction. ⚠ Supabase pose tout seul un GRANT a `authenticated`
-- sur toute fonction neuve (leçon du 08/10) : on le veut ici (l'ecran appelle la
-- fonction), mais on retire tout le reste et on l'ecrit noir sur blanc.
revoke all on function public.app_console_archiver_contact_optimistic(text, boolean) from public;
revoke all on function public.app_console_archiver_contact_optimistic(text, boolean) from anon;
grant execute on function public.app_console_archiver_contact_optimistic(text, boolean) to authenticated;
grant execute on function public.app_console_archiver_contact_optimistic(text, boolean) to service_role;

commit;
