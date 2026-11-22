-- ═══════════════════════════════════════════════════════════════════════════
-- L'ANCIEN NUMERO DANS SA LIGNE DU JOURNAL DES ETIQUETTES        22/11/2026 (soir)
-- Fabrique par phase2/checks/fabriquer_patch_journal_ancien_numero.py -- NE PAS RETOUCHER A LA MAIN.
--
-- SON MOT (reponses au rapport 21 bis, point 1 a) : « L'ANCIEN NUMERO RESTE TRACE. [...] chaque changement doit y
--   laisser sa ligne, avec l'ancien et le neuf. »
--
-- LA MESURE (lecture seule, 22/11) : chaque changement laisse BIEN sa ligne -- pose 11 454, propagation 13,
--   fusion 47, scission 143. Mais l'ANCIEN NUMERO n'y est pas ecrit :
--     . SCISSION : dossier_uuid = l'ANCIEN uuid, dossier_numero = le NEUF numero (141 sur 143 ; 0 l'ancien) ;
--     . FUSION   : dossier_uuid / dossier_numero = le dossier GARDE, autre_uuid = l'absorbe, SANS son numero.
--   L'ancien numero se retrouve par la ligne de naissance de l'ancien uuid (190 sur 190), pas dans la ligne.
--
-- CE QUE LE PATCH FAIT :
--   1. une colonne neuve, ancien_numero (texte, vide pour une pose ou une propagation) ;
--   2. la RPC app_poser_etiquettes_dossier l'ecrit a CHAQUE fusion (le numero absorbe) et a CHAQUE scission
--      (le numero du dossier coupe). Rien d'autre ne change dans la fonction : 5 remplacements, ancres d'une ligne ;
--   3. les 190 lignes deja ecrites (143 scissions, 47 fusions) recoivent leur ancien numero, lu dans leur ligne de
--      naissance -- et le patch S'ARRETE si une seule reste vide ;
--   4. la contrainte des evenements accepte « restauration » : une restauration est aussi un changement de numero,
--      elle doit pouvoir laisser sa ligne (sauvegarde_datee_classeur.py l'ecrit).
-- CE QU'IL NE FAIT PAS : il ne touche a aucune etiquette, a aucun numero, a aucune ligne du registre.
-- ⛔ IL S'ARRETE SEUL, sans rien laisser, si la fonction n'est plus celle lue le 22/11 (empreinte 815e956f716cceb6477876b774b9f885),
--   si la colonne existe deja, ou si la contrainte des evenements a change.
-- Ensuite : patch_journal_ancien_numero_2026-11-22_REPETITION.sql (lecture seule). Retour arriere : patch_journal_ancien_numero_2026-11-22_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

begin;

do $garde$
begin
  if md5(pg_get_functiondef('public.app_poser_etiquettes_dossier'::regproc)) <> '815e956f716cceb6477876b774b9f885' then
    raise exception 'la fonction app_poser_etiquettes_dossier a change depuis le 22/11 -- patch ARRETE, rien n''est fait';
  end if;
  if exists (select 1 from information_schema.columns where table_schema = 'public'
               and table_name = 'app_dossier_etiquette_journal' and column_name = 'ancien_numero') then
    raise exception 'la colonne ancien_numero existe deja -- patch ARRETE, rien n''est fait';
  end if;
  if (select pg_get_constraintdef(oid) from pg_constraint
       where conname = 'app_dossier_etiquette_journal_evenement_check')
     is distinct from 'CHECK ((evenement = ANY (ARRAY[''pose''::text, ''propagation''::text, ''fusion''::text, ''scission''::text])))' then
    raise exception 'la contrainte des evenements a change depuis le 22/11 -- patch ARRETE, rien n''est fait';
  end if;
end
$garde$;

alter table public.app_dossier_etiquette_journal add column ancien_numero text;
-- UNE RESTAURATION EST AUSSI UN CHANGEMENT DE NUMERO : elle doit pouvoir laisser sa ligne (son mot : « chaque
--   changement doit y laisser sa ligne »). Aujourd'hui la contrainte ne connait que pose, propagation, fusion, scission.
alter table public.app_dossier_etiquette_journal drop constraint app_dossier_etiquette_journal_evenement_check;
alter table public.app_dossier_etiquette_journal add constraint app_dossier_etiquette_journal_evenement_check
  check (evenement in ('pose', 'propagation', 'fusion', 'scission', 'restauration'));
comment on column public.app_dossier_etiquette_journal.ancien_numero is
  'Le numero AVANT le changement (22/11/2026, son mot : « avec l''ancien et le neuf »). FUSION : le numero absorbe '
  '(le neuf est dossier_numero, celui du dossier garde). SCISSION : le numero du dossier coupe (le neuf est '
  'dossier_numero, porte par autre_uuid). RESTAURATION : le numero quitte (le neuf est dossier_numero, celui de la '
  'sauvegarde). Vide pour une pose ou une propagation : rien ne change de numero.';

CREATE OR REPLACE FUNCTION public.app_poser_etiquettes_dossier(p_limite integer DEFAULT NULL::integer, p_a_blanc boolean DEFAULT false)
 RETURNS TABLE(geste text, dossiers integer, lignes integer)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
           -- ⭐ 12/11 : l'annee passe par le LECTEUR UNIQUE -- une offre se date
           --   sur sa premiere proposition, pas sur son dernier mouvement.
           min(public.app_dossier_annee_date_transaction(
                 l.kind, l.date, l.propositions_json, l.app_affaire_id)) as an_transaction,
           min(l.hektor_annonce_id)                          as annonce,
           -- ⭐ 12/11 : le JOUR aussi -- il decide de l'ORDRE des rangs.
           min(public.app_dossier_jour_date_transaction(
                 l.kind, l.date, l.propositions_json, l.app_affaire_id))  as plus_ancienne
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
           g.app_chaine_id
  limit coalesce(p_limite, 2147483647);

  insert into public.app_dossier_numero_compteur (annee, dernier)
  select distinct annee, 0 from _nus
  on conflict (annee) do nothing;

  create temporary table _neufs on commit drop as
  select n.app_chaine_id, n.annee, gen_random_uuid() as dossier_uuid,
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
     where l.app_chaine_id = f.app_chaine_id and l.app_dossier_uuid is null;
    get diagnostics v_pose_l = row_count;

    update public.app_dossier_numero_compteur c
       set dernier = s.dernier
      from (select annee, max(rang) as dernier from _neufs group by annee) s
     where c.annee = s.annee;

    insert into public.app_dossier_etiquette_journal
      (evenement, dossier_uuid, dossier_numero, app_chaine_id, transactions, combien, pourquoi)
    select 'pose', f.dossier_uuid,
           public.app_dossier_numero_format(f.annee, f.rang), f.app_chaine_id,
           array_agg(l.app_affaire_id order by l.app_affaire_id), count(*),
           'premiere pose, annee ' || f.annee
    from _neufs f
    join public.app_affaire_ledger l on l.app_chaine_id = f.app_chaine_id
    group by f.dossier_uuid, f.annee, f.rang, f.app_chaine_id;
  end if;

  -- (2) UNE TRANSACTION NUE DANS UN GROUPE DEJA ETIQUETE -> on propage.
  --     C'EST LE CAS NORMAL, et c'est lui qui rend l'etiquette stable :
  --     app_chaine_id peut bouger, l'etiquette du groupe ne bouge pas.
  create temporary table _a_propager on commit drop as
  select l.app_affaire_id, l.app_chaine_id, d.dossier_uuid, d.dossier_numero
  from public.app_affaire_ledger l
  join (
    select distinct on (app_chaine_id)
           app_chaine_id, app_dossier_uuid as dossier_uuid, app_dossier_numero as dossier_numero
    from public.app_affaire_ledger
    where app_chaine_id is not null and app_dossier_uuid is not null
    order by app_chaine_id, app_affaire_id
  ) d on d.app_chaine_id = l.app_chaine_id
  where l.app_dossier_uuid is null;

  select count(distinct app_chaine_id), count(*) into v_propagation, v_propagation_l from _a_propager;

  if not p_a_blanc and v_propagation_l > 0 then
    update public.app_affaire_ledger l
       set app_dossier_uuid = p.dossier_uuid, app_dossier_numero = p.dossier_numero
      from _a_propager p where l.app_affaire_id = p.app_affaire_id;

    insert into public.app_dossier_etiquette_journal
      (evenement, dossier_uuid, dossier_numero, app_chaine_id, transactions, combien, pourquoi)
    select 'propagation', p.dossier_uuid, p.dossier_numero, p.app_chaine_id,
           array_agg(p.app_affaire_id order by p.app_affaire_id), count(*),
           'transaction(s) arrivee(s) dans un dossier deja etiquete'
    from _a_propager p group by p.dossier_uuid, p.dossier_numero, p.app_chaine_id;
  end if;

  -- (3) FUSION -- un groupe porte PLUSIEURS etiquettes. On garde la plus ANCIENNE
  --     et on journalise l'absorbee : c'est la ligne que la phase B devra lire.
  create temporary table _fusions on commit drop as
  with multi as (
    select app_chaine_id from public.app_affaire_ledger
    where app_chaine_id is not null and app_dossier_uuid is not null
    group by app_chaine_id having count(distinct app_dossier_uuid) > 1
  ),
  gagnante as (
    select distinct on (l.app_chaine_id)
           l.app_chaine_id, l.app_dossier_uuid as garde, l.app_dossier_numero as garde_num
    from public.app_affaire_ledger l join multi using (app_chaine_id)
    where l.app_dossier_uuid is not null
    order by l.app_chaine_id, l.app_affaire_id
  )
  select l.app_affaire_id, l.app_chaine_id, g.garde, g.garde_num,
         l.app_dossier_uuid as absorbee, l.app_dossier_numero as absorbee_num
  from public.app_affaire_ledger l join gagnante g using (app_chaine_id)
  where l.app_dossier_uuid is not null and l.app_dossier_uuid is distinct from g.garde;

  select count(distinct app_chaine_id), count(*) into v_fusion, v_fusion_l from _fusions;

  if not p_a_blanc and v_fusion_l > 0 then
    -- LE JOURNAL D'ABORD : apres l'UPDATE, l'etiquette absorbee a disparu des
    -- lignes, et plus rien ne dirait laquelle elle etait.
    insert into public.app_dossier_etiquette_journal
      (evenement, dossier_uuid, dossier_numero, autre_uuid, app_chaine_id, transactions, combien, pourquoi,
       ancien_numero)
    select 'fusion', f.garde, f.garde_num, f.absorbee, f.app_chaine_id,
           array_agg(f.app_affaire_id order by f.app_affaire_id), count(*),
           'deux dossiers etiquetes reunis dans un seul groupe',
           f.absorbee_num
    from _fusions f group by f.garde, f.garde_num, f.absorbee, f.app_chaine_id, f.absorbee_num;

    update public.app_affaire_ledger l
       set app_dossier_uuid = f.garde, app_dossier_numero = f.garde_num
      from _fusions f where l.app_affaire_id = f.app_affaire_id;
  end if;

  -- (4) SCISSION -- une etiquette etalee sur PLUSIEURS groupes.
  create temporary table _scissions on commit drop as
  with etalees as (
    select app_dossier_uuid from public.app_affaire_ledger
    where app_dossier_uuid is not null and app_chaine_id is not null
    group by app_dossier_uuid having count(distinct app_chaine_id) > 1
  ),
  tete as (
    select distinct on (l.app_dossier_uuid) l.app_dossier_uuid, l.app_chaine_id as garde_chaine
    from public.app_affaire_ledger l join etalees using (app_dossier_uuid)
    order by l.app_dossier_uuid, l.app_affaire_id
  ),
  partants as (
    select distinct l.app_dossier_uuid as ancienne, l.app_chaine_id,
           public.app_dossier_annee_ouverture(l.app_chaine_id) as annee
    from public.app_affaire_ledger l
    join tete t on t.app_dossier_uuid = l.app_dossier_uuid
    where l.app_chaine_id is distinct from t.garde_chaine
  )
  select p.ancienne, p.app_chaine_id, p.annee, gen_random_uuid() as neuve from partants p;

  select count(*) into v_scission from _scissions;

  if not p_a_blanc and v_scission > 0 then
    insert into public.app_dossier_numero_compteur (annee, dernier)
    select distinct annee, 0 from _scissions on conflict (annee) do nothing;

    create temporary table _scissions_num on commit drop as
    select s.ancienne, s.app_chaine_id, s.annee, s.neuve,
           (c.dernier + row_number() over (partition by s.annee
                                           order by s.app_chaine_id))::integer as rang
    from _scissions s join public.app_dossier_numero_compteur c on c.annee = s.annee;

    insert into public.app_dossier_etiquette_journal
      (evenement, dossier_uuid, dossier_numero, autre_uuid, app_chaine_id, transactions, combien, pourquoi,
       ancien_numero)
    select 'scission', s.ancienne, public.app_dossier_numero_format(s.annee, s.rang),
           s.neuve, s.app_chaine_id,
           array_agg(l.app_affaire_id order by l.app_affaire_id), count(*),
           'le dossier s''est coupe : cette part recoit une etiquette neuve',
           min(l.app_dossier_numero)
    from _scissions_num s
    join public.app_affaire_ledger l on l.app_chaine_id = s.app_chaine_id
                                    and l.app_dossier_uuid = s.ancienne
    group by s.ancienne, s.neuve, s.annee, s.rang, s.app_chaine_id;

    update public.app_affaire_ledger l
       set app_dossier_uuid = s.neuve,
           app_dossier_numero = public.app_dossier_numero_format(s.annee, s.rang)
      from _scissions_num s
     where l.app_chaine_id = s.app_chaine_id and l.app_dossier_uuid = s.ancienne;
    get diagnostics v_scission_l = row_count;

    update public.app_dossier_numero_compteur c
       set dernier = x.dernier
      from (select annee, max(rang) as dernier from _scissions_num group by annee) x
     where c.annee = x.annee;
  end if;

  return query
    select 'pose'::text, v_pose, v_pose_l
    union all select 'propagation'::text, v_propagation, v_propagation_l
    union all select 'fusion'::text, v_fusion, v_fusion_l
    union all select 'scission'::text, v_scission, v_scission_l;
end;
$function$;

-- les lignes deja ecrites : l'ancien numero, lu dans la ligne de naissance de l'ancien uuid
update public.app_dossier_etiquette_journal j
   set ancien_numero = b.n
  from (select dossier_uuid as u, dossier_numero as n from public.app_dossier_etiquette_journal where evenement = 'pose'
     union all
     select autre_uuid, dossier_numero from public.app_dossier_etiquette_journal where evenement = 'scission') b
 where j.evenement = 'scission' and j.ancien_numero is null and b.u = j.dossier_uuid;

update public.app_dossier_etiquette_journal j
   set ancien_numero = b.n
  from (select dossier_uuid as u, dossier_numero as n from public.app_dossier_etiquette_journal where evenement = 'pose'
     union all
     select autre_uuid, dossier_numero from public.app_dossier_etiquette_journal where evenement = 'scission') b
 where j.evenement = 'fusion' and j.ancien_numero is null and b.u = j.autre_uuid;

do $controle$
declare v_vides integer; v_egaux integer; v_mots integer;
begin
  select count(*) into v_vides from public.app_dossier_etiquette_journal
   where evenement in ('fusion', 'scission') and ancien_numero is null;
  if v_vides > 0 then
    raise exception '% ligne(s) de fusion ou de scission restent sans ancien numero -- patch ARRETE, rien n''est fait', v_vides;
  end if;
  select count(*) into v_egaux from public.app_dossier_etiquette_journal
   where evenement in ('fusion', 'scission') and ancien_numero = dossier_numero;
  if v_egaux > 0 then
    raise exception '% ligne(s) ou l''ancien numero est egal au neuf -- patch ARRETE, rien n''est fait', v_egaux;
  end if;
  select (length(pg_get_functiondef('public.app_poser_etiquettes_dossier'::regproc))
          - length(replace(pg_get_functiondef('public.app_poser_etiquettes_dossier'::regproc), 'ancien_numero', ''))) / length('ancien_numero')
    into v_mots;
  if v_mots <> 2 then
    raise exception 'la fonction posee porte % fois ancien_numero (attendu 2) -- patch ARRETE', v_mots;
  end if;
end
$controle$;

commit;
