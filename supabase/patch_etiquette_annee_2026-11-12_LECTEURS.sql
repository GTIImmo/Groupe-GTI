-- ═══════════════════════════════════════════════════════════════════════════
-- L'ANNÉE DE L'ÉTIQUETTE : LES DEUX LECTEURS, RÉPARÉS          12/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- ⭐ CE FICHIER N'ÉCRIT AUCUNE DONNÉE. Il ne remplace que des fonctions.
--    Les étiquettes déjà posées ne bougent pas d'une ligne. La repose est un
--    second fichier, à part : patch_etiquette_annee_2026-11-12_REPOSE.sql
--    Contrôles : patch_etiquette_annee_2026-11-12_REPETITION.sql
--
-- ⚠ CE QU'IL CORRIGE, ET C'EST UN DÉFAUT QUE J'AI POSÉ CE MATIN.
--
--   La pose du 12/11 à 11:00 a daté chaque dossier sur `min(date)` de ses
--   transactions. Or, POUR UNE OFFRE, `date` porte le DERNIER MOUVEMENT, pas la
--   proposition -- relevé sur l'offre 14112 : proposition 2021-03-25,
--   acceptation 2021-03-25, refus 2026-11-11, et `date` porte le refus.
--   Nos 1 185 refus de la veille ont donc daté de 2026 des dossiers de 2014.
--
--   MESURE DU 12/11, AVANT CE PATCH :
--       dossiers datés                                      11 347
--       dont l'année est FAUSSE                                708   (6,2 %)
--       dont étiquetés « 2026 » à tort                          653
--       part des dossiers « 2026 » qui sont faux       653 / 1 019   (64 %)
--       l'année vraie s'étale de 2006 à 2025
--
--   ⭐ LE PROJET AVAIT DÉJÀ TRANCHÉ LA MÉTHODE, le 12/11 au matin :
--     « ⛔ ON NE CORRIGE PAS LA COLONNE `date` -- on corrige les LECTEURS. »
--     Trois lecteurs ont été réparés ce jour-là (l'apparieur, le chaînage l'était
--     déjà, le rapport du gel l'a été l'après-midi). DEUX AVAIENT ÉTÉ OUBLIÉS,
--     et ce sont eux qui datent les dossiers :
--         ① la fonction app_dossier_annee_ouverture
--         ② la CTE « groupes » DANS app_poser_etiquettes_dossier   (le jumeau)
--     ⚠ C'est ② qui a posé les 653 numéros faux : ① ne sert qu'aux scissions.
--     « Élargir un seuil : chercher ses jumeaux » -- mémoire du projet.
--
-- ⚠ CE QUE ÇA NE CORRIGE PAS, ET IL FAUT LE SAVOIR :
--   . les 88 dossiers datés par le MANDAT gardent leur approximation (l'année du
--     mandat se trompe environ une fois sur trois) -- inchangé, déjà écrit ;
--   . les dossiers muets restent en D0000-xxxx : ils n'ont aucune date ;
--   . `date` reste telle quelle chez nous ET chez Hektor. On ne touche pas la
--     donnée, seulement sa lecture.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

-- ═══════════════════════════════════════════════════════════════════════════
-- ⓿ LE LECTEUR UNIQUE — une seule définition, appelée par les deux endroits.
--    ⛔ C'est le but : la cause du défaut est qu'il y avait DEUX copies de la
--      même règle, et qu'une seule a été réparée.
-- ═══════════════════════════════════════════════════════════════════════════
create or replace function public.app_dossier_annee_date_transaction(
  p_kind text, p_date text, p_propositions text)
returns text
language sql
immutable
as $fn$
  -- L'ANNÉE D'UNE TRANSACTION, VUE CORRECTEMENT.
  --   une OFFRE  -> l'année de sa PREMIÈRE PROPOSITION (ou acceptation) ;
  --                 à défaut seulement, `date`.
  --   les autres -> `date`, qui chez elles ne bouge pas.
  --
  -- ⛔ LES DATES « 0000 » SONT ÉCARTÉES DES DEUX CÔTÉS. Défaut trouvé à blanc le
  --   12/11 : 14 offres portent une proposition datée 0000-00-00 ; sans ce
  --   filtre, leur dossier tombait en D0000 alors que `date` portait une vraie
  --   année. La réparation aurait fabriqué 14 régressions.
  --
  -- ⚠ `propositions_json` est PARFOIS UN OBJET SEUL, pas un tableau. Le même
  --   piège a faussé une de mes mesures le 12/11 : 472 paires lues « sans nom »
  --   alors que 417 portaient deux acquéreurs différents. Les deux formes sont
  --   donc traitées ici, et une forme inconnue rend NULL -- jamais une erreur.
  --
  -- ⚠ Le REFUS est volontairement exclu : il est déjà porté par `date`, et
  --   l'ajouter n'apporterait aucune date neuve.
  select coalesce(
    case when lower(coalesce(p_kind, '')) = 'offre' then
      (select min(left(e->>'date', 4))
         from jsonb_array_elements(
                case jsonb_typeof(coalesce(p_propositions, 'null')::jsonb)
                  when 'array'  then p_propositions::jsonb
                  when 'object' then jsonb_build_array(p_propositions::jsonb)
                  else '[]'::jsonb end) e
        where lower(coalesce(e->>'type', '')) in ('proposition', 'accepte')
          and (e->>'date') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
          and (e->>'date') not like '0000%')
    end,
    case when p_date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}' and p_date not like '0000%'
         then left(p_date, 4) end);
$fn$;

-- LE JOUR, pour la même raison : c'est lui qui décide de l'ORDRE des rangs.
-- Sans lui, les années seraient justes et les numéros dans le désordre.
create or replace function public.app_dossier_jour_date_transaction(
  p_kind text, p_date text, p_propositions text)
returns text
language sql
immutable
as $fn$
  select coalesce(
    case when lower(coalesce(p_kind, '')) = 'offre' then
      (select min(left(e->>'date', 10))
         from jsonb_array_elements(
                case jsonb_typeof(coalesce(p_propositions, 'null')::jsonb)
                  when 'array'  then p_propositions::jsonb
                  when 'object' then jsonb_build_array(p_propositions::jsonb)
                  else '[]'::jsonb end) e
        where lower(coalesce(e->>'type', '')) in ('proposition', 'accepte')
          and (e->>'date') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
          and (e->>'date') not like '0000%')
    end,
    case when p_date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}' and p_date not like '0000%'
         then left(p_date, 10) end);
$fn$;

-- ⛔ LES DROITS : un CREATE OR REPLACE naît avec « execute » pour authenticated,
--   et « revoke all from public » NE FERME PAS authenticated -- le projet a payé
--   cette leçon deux fois. Ces deux-ci sont de simples lectures de forme : on les
--   laisse ouvertes à authenticated, comme app_dossier_numero_format.
revoke all on function public.app_dossier_annee_date_transaction(text, text, text) from public;
revoke all on function public.app_dossier_jour_date_transaction(text, text, text)  from public;
revoke all on function public.app_dossier_annee_date_transaction(text, text, text) from anon;
revoke all on function public.app_dossier_jour_date_transaction(text, text, text)  from anon;
grant execute on function public.app_dossier_annee_date_transaction(text, text, text) to authenticated, service_role;
grant execute on function public.app_dossier_jour_date_transaction(text, text, text)  to authenticated, service_role;


-- ═══════════════════════════════════════════════════════════════════════════
-- ① LE PREMIER LECTEUR — app_dossier_annee_ouverture (sert aux SCISSIONS)
-- ═══════════════════════════════════════════════════════════════════════════
create or replace function public.app_dossier_annee_ouverture(p_chaine bigint)
returns integer
language sql
stable
as $fn$
  with t as (
    select min(public.app_dossier_annee_date_transaction(
                 l.kind, l.date, l.propositions_json::text)) as an_transaction,
           min(l.hektor_annonce_id)                          as annonce
    from public.app_affaire_ledger l
    where l.app_chaine_id = p_chaine
  ),
  m as (
    select min(case when a.date_debut ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
                     and a.date_debut not like '0000%'
                    then left(a.date_debut, 4) end) as an_mandat
    from public.app_mandat a
    join t on a.hektor_annonce_id = t.annonce::text
  )
  select coalesce((select an_transaction from t),
                  (select an_mandat from m),
                  '0000')::integer;
$fn$;

revoke all on function public.app_dossier_annee_ouverture(bigint) from public;
revoke all on function public.app_dossier_annee_ouverture(bigint) from anon;
grant execute on function public.app_dossier_annee_ouverture(bigint) to authenticated, service_role;


-- ═══════════════════════════════════════════════════════════════════════════
-- ② LE SECOND LECTEUR — la CTE « groupes » de app_poser_etiquettes_dossier.
--    ⛔ SEULE la CTE « groupes » change. Les quatre gestes (pose, propagation,
--      fusion, scission) sont recopiés À L'IDENTIQUE du corps du 12/11 : le SQL
--      impose de réécrire la fonction entière, mais rien d'autre n'est modifié.
--      La différence se lit en trois endroits, tous marqués « ⭐ 12/11 ».
-- ═══════════════════════════════════════════════════════════════════════════
create or replace function public.app_poser_etiquettes_dossier(
  p_limite integer default null, p_a_blanc boolean default false)
returns table(geste text, dossiers integer, lignes integer)
language plpgsql
security definer
set search_path to 'public'
as $fn$
declare
  v_pose        integer := 0;  v_pose_l        integer := 0;
  v_propagation integer := 0;  v_propagation_l integer := 0;
  v_fusion      integer := 0;  v_fusion_l      integer := 0;
  v_scission    integer := 0;  v_scission_l    integer := 0;
begin
  -- (1) LES GROUPES SANS AUCUNE ETIQUETTE -> une etiquette neuve
  create temporary table _nus on commit drop as
  with groupes as (
    select l.app_chaine_id,
           -- ⭐ 12/11 : l'annee passe par le LECTEUR UNIQUE. Une offre se date
           --   sur sa premiere proposition, pas sur son dernier mouvement.
           min(public.app_dossier_annee_date_transaction(
                 l.kind, l.date, l.propositions_json::text)) as an_transaction,
           min(l.hektor_annonce_id)                          as annonce,
           -- ⭐ 12/11 : le JOUR aussi -- il decide de l'ORDRE des rangs.
           min(public.app_dossier_jour_date_transaction(
                 l.kind, l.date, l.propositions_json::text))  as plus_ancienne
    from public.app_affaire_ledger l
    where l.app_chaine_id is not null
    group by l.app_chaine_id
    having count(l.app_dossier_uuid) = 0
  ),
  mandats as (
    select a.hektor_annonce_id,
           min(case when a.date_debut ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
                     and a.date_debut not like '0000%'
                    then left(a.date_debut, 4) end) as an_mandat
    from public.app_mandat a
    group by a.hektor_annonce_id
  )
  select g.app_chaine_id,
         coalesce(g.an_transaction, m.an_mandat, '0000')::integer as annee,
         g.plus_ancienne
  from groupes g
  left join mandats m on m.hektor_annonce_id = g.annonce::text
  order by coalesce(g.an_transaction, m.an_mandat, '0000'),
           g.plus_ancienne nulls last,
           g.app_chaine_id        -- departage : l'ordre est REFAISABLE
  limit coalesce(p_limite, 2147483647);

  insert into public.app_dossier_numero_compteur (annee, dernier)
  select distinct annee, 0 from _nus
  on conflict (annee) do nothing;

  create temporary table _neufs on commit drop as
  select n.app_chaine_id,
         n.annee,
         gen_random_uuid() as dossier_uuid,
         (c.dernier + row_number() over (partition by n.annee
                                         order by n.plus_ancienne nulls last,
                                                  n.app_chaine_id))::integer as rang
  from _nus n
  join public.app_dossier_numero_compteur c on c.annee = n.annee;

  select count(*) into v_pose from _neufs;

  if not p_a_blanc and v_pose > 0 then
    update public.app_affaire_ledger l
       set app_dossier_uuid   = f.dossier_uuid,
           app_dossier_numero = public.app_dossier_numero_format(f.annee, f.rang)
      from _neufs f
     where l.app_chaine_id = f.app_chaine_id
       and l.app_dossier_uuid is null;
    get diagnostics v_pose_l = row_count;

    update public.app_dossier_numero_compteur c
       set dernier = s.dernier
      from (select annee, max(rang) as dernier from _neufs group by annee) s
     where c.annee = s.annee;

    insert into public.app_dossier_etiquette_journal
      (evenement, dossier_uuid, dossier_numero, app_chaine_id,
       transactions, combien, pourquoi)
    select 'pose', f.dossier_uuid,
           public.app_dossier_numero_format(f.annee, f.rang),
           f.app_chaine_id,
           array_agg(l.app_affaire_id order by l.app_affaire_id),
           count(*),
           'premiere pose, annee ' || f.annee
    from _neufs f
    join public.app_affaire_ledger l on l.app_chaine_id = f.app_chaine_id
    group by f.dossier_uuid, f.annee, f.rang, f.app_chaine_id;
  end if;

  -- (2) UNE TRANSACTION NUE DANS UN GROUPE DEJA ETIQUETE -> on propage
  --     C'EST LE CAS NORMAL, et c'est lui qui rend l'etiquette stable :
  --     app_chaine_id peut bouger, l'etiquette du groupe ne bouge pas.
  create temporary table _a_propager on commit drop as
  select l.app_affaire_id, l.app_chaine_id, d.dossier_uuid, d.dossier_numero
  from public.app_affaire_ledger l
  join (
    -- l'etiquette du groupe = celle de sa transaction la plus ancienne
    select distinct on (app_chaine_id)
           app_chaine_id,
           app_dossier_uuid   as dossier_uuid,
           app_dossier_numero as dossier_numero
    from public.app_affaire_ledger
    where app_chaine_id is not null and app_dossier_uuid is not null
    order by app_chaine_id, app_affaire_id
  ) d on d.app_chaine_id = l.app_chaine_id
  where l.app_dossier_uuid is null;

  select count(distinct app_chaine_id), count(*)
    into v_propagation, v_propagation_l
  from _a_propager;

  if not p_a_blanc and v_propagation_l > 0 then
    update public.app_affaire_ledger l
       set app_dossier_uuid   = p.dossier_uuid,
           app_dossier_numero = p.dossier_numero
      from _a_propager p
     where l.app_affaire_id = p.app_affaire_id;

    insert into public.app_dossier_etiquette_journal
      (evenement, dossier_uuid, dossier_numero, app_chaine_id,
       transactions, combien, pourquoi)
    select 'propagation', p.dossier_uuid, p.dossier_numero, p.app_chaine_id,
           array_agg(p.app_affaire_id order by p.app_affaire_id), count(*),
           'transaction(s) arrivee(s) dans un dossier deja etiquete'
    from _a_propager p
    group by p.dossier_uuid, p.dossier_numero, p.app_chaine_id;
  end if;

  -- (3) FUSION -- un groupe porte PLUSIEURS etiquettes. On garde la plus ANCIENNE
  --     (celle de la plus petite transaction) et on journalise les autres : c'est la
  --     ligne que le worker de la phase B devra lire pour savoir que deux lignes du
  --     classeur ne designent plus qu'un dossier.
  create temporary table _fusions on commit drop as
  with multi as (
    select app_chaine_id
    from public.app_affaire_ledger
    where app_chaine_id is not null and app_dossier_uuid is not null
    group by app_chaine_id
    having count(distinct app_dossier_uuid) > 1
  ),
  gagnante as (
    select distinct on (l.app_chaine_id)
           l.app_chaine_id,
           l.app_dossier_uuid   as garde,
           l.app_dossier_numero as garde_num
    from public.app_affaire_ledger l
    join multi using (app_chaine_id)
    where l.app_dossier_uuid is not null
    order by l.app_chaine_id, l.app_affaire_id
  )
  select l.app_affaire_id, l.app_chaine_id,
         g.garde, g.garde_num,
         l.app_dossier_uuid as absorbee
  from public.app_affaire_ledger l
  join gagnante g using (app_chaine_id)
  where l.app_dossier_uuid is not null
    and l.app_dossier_uuid is distinct from g.garde;

  select count(distinct app_chaine_id), count(*)
    into v_fusion, v_fusion_l
  from _fusions;

  if not p_a_blanc and v_fusion_l > 0 then
    -- LE JOURNAL D'ABORD : apres l'UPDATE, l'etiquette absorbee a disparu des
    -- lignes, et plus rien ne dirait laquelle elle etait.
    insert into public.app_dossier_etiquette_journal
      (evenement, dossier_uuid, dossier_numero, autre_uuid, app_chaine_id,
       transactions, combien, pourquoi)
    select 'fusion', f.garde, f.garde_num, f.absorbee, f.app_chaine_id,
           array_agg(f.app_affaire_id order by f.app_affaire_id), count(*),
           'deux dossiers etiquetes reunis dans un seul groupe'
    from _fusions f
    group by f.garde, f.garde_num, f.absorbee, f.app_chaine_id;

    update public.app_affaire_ledger l
       set app_dossier_uuid   = f.garde,
           app_dossier_numero = f.garde_num
      from _fusions f
     where l.app_affaire_id = f.app_affaire_id;
  end if;

  -- (4) SCISSION -- une etiquette etalee sur PLUSIEURS groupes. Le groupe qui garde
  --     la transaction la plus ancienne garde l'etiquette ; les autres en recoivent
  --     une neuve, journalisee -- sinon une ligne du classeur se retrouverait devant
  --     deux dossiers.
  create temporary table _scissions on commit drop as
  with etalees as (
    select app_dossier_uuid
    from public.app_affaire_ledger
    where app_dossier_uuid is not null and app_chaine_id is not null
    group by app_dossier_uuid
    having count(distinct app_chaine_id) > 1
  ),
  tete as (   -- le groupe qui GARDE : celui de la plus petite transaction
    select distinct on (l.app_dossier_uuid)
           l.app_dossier_uuid, l.app_chaine_id as garde_chaine
    from public.app_affaire_ledger l
    join etalees using (app_dossier_uuid)
    order by l.app_dossier_uuid, l.app_affaire_id
  ),
  partants as (
    select distinct
           l.app_dossier_uuid as ancienne,
           l.app_chaine_id,
           public.app_dossier_annee_ouverture(l.app_chaine_id) as annee
    from public.app_affaire_ledger l
    join tete t on t.app_dossier_uuid = l.app_dossier_uuid
    where l.app_chaine_id is distinct from t.garde_chaine
  )
  select p.ancienne, p.app_chaine_id, p.annee, gen_random_uuid() as neuve
  from partants p;

  select count(*) into v_scission from _scissions;

  if not p_a_blanc and v_scission > 0 then
    insert into public.app_dossier_numero_compteur (annee, dernier)
    select distinct annee, 0 from _scissions
    on conflict (annee) do nothing;

    create temporary table _scissions_num on commit drop as
    select s.ancienne, s.app_chaine_id, s.annee, s.neuve,
           (c.dernier + row_number() over (partition by s.annee
                                           order by s.app_chaine_id))::integer as rang
    from _scissions s
    join public.app_dossier_numero_compteur c on c.annee = s.annee;

    -- LE JOURNAL D'ABORD, pour la meme raison qu'en (3).
    insert into public.app_dossier_etiquette_journal
      (evenement, dossier_uuid, dossier_numero, autre_uuid, app_chaine_id,
       transactions, combien, pourquoi)
    select 'scission', s.ancienne,
           public.app_dossier_numero_format(s.annee, s.rang),
           s.neuve, s.app_chaine_id,
           array_agg(l.app_affaire_id order by l.app_affaire_id), count(*),
           'le dossier s''est coupe : cette part recoit une etiquette neuve'
    from _scissions_num s
    join public.app_affaire_ledger l on l.app_chaine_id   = s.app_chaine_id
                                    and l.app_dossier_uuid = s.ancienne
    group by s.ancienne, s.neuve, s.annee, s.rang, s.app_chaine_id;

    update public.app_affaire_ledger l
       set app_dossier_uuid   = s.neuve,
           app_dossier_numero = public.app_dossier_numero_format(s.annee, s.rang)
      from _scissions_num s
     where l.app_chaine_id    = s.app_chaine_id
       and l.app_dossier_uuid = s.ancienne;
    get diagnostics v_scission_l = row_count;

    update public.app_dossier_numero_compteur c
       set dernier = x.dernier
      from (select annee, max(rang) as dernier from _scissions_num group by annee) x
     where c.annee = x.annee;
  end if;

  return query
    select 'pose'::text,          v_pose,        v_pose_l
    union all
    select 'propagation'::text,   v_propagation, v_propagation_l
    union all
    select 'fusion'::text,        v_fusion,      v_fusion_l
    union all
    select 'scission'::text,      v_scission,    v_scission_l;
end;
$fn$;

-- ⛔ LES DROITS SE REPOSENT APRÈS CHAQUE REMPLACEMENT.
revoke all on function public.app_poser_etiquettes_dossier(integer, boolean) from public;
revoke all on function public.app_poser_etiquettes_dossier(integer, boolean) from anon;
revoke all on function public.app_poser_etiquettes_dossier(integer, boolean) from authenticated;
grant execute on function public.app_poser_etiquettes_dossier(integer, boolean) to service_role;

commit;

-- ═══════════════════════════════════════════════════════════════════════════
-- CE QUI DOIT ÊTRE VRAI JUSTE APRÈS CE FICHIER — à vérifier avant la repose
-- ═══════════════════════════════════════════════════════════════════════════
-- . les 31 151 étiquettes sont INCHANGÉES (ce fichier n'écrit aucune donnée) ;
-- . la pose À BLANC rend toujours 0/0/0/0 (rien n'est nu, rien n'est étalé) ;
-- . et le lecteur réparé annonce les 708 dossiers à redater.
-- Les trois se lisent dans patch_etiquette_annee_2026-11-12_REPETITION.sql
