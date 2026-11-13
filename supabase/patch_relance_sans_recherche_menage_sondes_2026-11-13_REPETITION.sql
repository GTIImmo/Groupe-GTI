-- RÉPÉTITION — patch_relance_sans_recherche_menage_sondes_2026-11-13.sql. Pose le MÊME corps dans une transaction, joue la relance « sans recherche » (n° 20, contact
-- d'essai), un VRAI orphelin témoin (la relance n° 21 détachée), fait tourner LE MÉNAGE, puis lève une erreur
-- VOLONTAIRE qui porte les verdicts : RIEN n'est gardé. Attendu : « 7 OK, 0 KO ».
-- ⚠ Pas de « commit » dans ce fichier : il se joue à blanc (leçon du 13/11).
begin;
set local lock_timeout = '5s';
-- ── LE CORPS (identique dans le patch et dans sa répétition) ─────────────────────────────────────────────────────
-- Gardes : on ne touche que ce qu'on a lu le 13/11 (empreinte du ménage, 4 rattachements, aucune trace de « contact: »).
do $garde$
declare d text := pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure);
        motif text := 'and x.contact_search_key not in (select contact_search_key from public.app_contact_search_current);';
begin
  if md5(d) <> 'f39dc33f0e73a2a06bd4fce103829a43' then
    raise exception 'ARRET : le menage (app_sweep_search_orphans) a change depuis la lecture du 13/11 -- relire avant de poser';
  end if;
  if (length(d) - length(replace(d, motif, ''))) / length(motif) <> 4 then
    raise exception 'ARRET : 4 rattachements attendus dans le menage';
  end if;
  if position('contact:' in pg_get_viewdef('public.app_v_orphelins_recherche'::regclass)) > 0
     or position('contact:' in pg_get_viewdef('public.app_search_orphans_non_rattachables'::regclass)) > 0 then
    raise exception 'ARRET : une sonde connait deja la forme contact:';
  end if;
end
$garde$;

-- Les comptes AVANT, hors relances « sans recherche » : ils ne doivent pas bouger.
create temporary table _avant_relance_sans_recherche on commit drop as
select (select count(*) from public.app_v_orphelins_recherche where contact_search_key not like 'contact:%') as n1,
       (select count(*) from public.app_search_orphans_non_rattachables where contact_search_key not like 'contact:%') as n2;

-- 1) LE MÉNAGE ne raccroche plus une relance « sans recherche » à une recherche (elle n'en a jamais eu).
do $menage$
declare d text := pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure);
        motif text := 'and x.contact_search_key not in (select contact_search_key from public.app_contact_search_current);';
begin
  execute replace(d, motif,
    'and x.contact_search_key not like ''contact:%'' -- 13/11 : relance « sans recherche » (clé contact:<n°>), pas un orphelin'
    || E'\n     ' || motif);
end
$menage$;

-- 2) LA SONDE « lignes accrochées à une recherche disparue » : même texte, la branche des relances ignore contact:.
create or replace view public.app_v_orphelins_recherche as
 SELECT 'app_rapprochement'::text AS table_orpheline,
    x.contact_search_key
   FROM public.app_rapprochement x
  WHERE (NOT (EXISTS ( SELECT 1
           FROM public.app_contact_search_current s
          WHERE (s.contact_search_key = x.contact_search_key))))
UNION ALL
 SELECT 'app_rapprochement_score_history'::text AS table_orpheline,
    x.contact_search_key
   FROM public.app_rapprochement_score_history x
  WHERE (NOT (EXISTS ( SELECT 1
           FROM public.app_contact_search_current s
          WHERE (s.contact_search_key = x.contact_search_key))))
UNION ALL
 SELECT 'app_rapprochement_search_state'::text AS table_orpheline,
    x.contact_search_key
   FROM public.app_rapprochement_search_state x
  WHERE (NOT (EXISTS ( SELECT 1
           FROM public.app_contact_search_current s
          WHERE (s.contact_search_key = x.contact_search_key))))
UNION ALL
 SELECT 'app_relance_rapprochement'::text AS table_orpheline,
    x.contact_search_key
   FROM public.app_relance_rapprochement x
  WHERE ((x.contact_search_key !~~ 'contact:%'::text) AND (NOT (EXISTS ( SELECT 1
           FROM public.app_contact_search_current s
          WHERE (s.contact_search_key = x.contact_search_key)))))
UNION ALL
 SELECT 'app_notification'::text AS table_orpheline,
    n.contact_search_key
   FROM public.app_notification n
  WHERE ((n.contact_search_key IS NOT NULL) AND (NOT (EXISTS ( SELECT 1
           FROM public.app_contact_search_current s
          WHERE (s.contact_search_key = n.contact_search_key)))));

-- 3) LA SONDE « orphelins non rattachables » : idem.
create or replace view public.app_search_orphans_non_rattachables as
 SELECT 'proposition'::text AS objet,
    (x.id)::text AS ligne,
    x.hektor_contact_id,
    x.contact_search_key
   FROM public.app_proposition x
  WHERE ((x.contact_search_key IS NOT NULL) AND (NOT (x.contact_search_key IN ( SELECT app_contact_search_current.contact_search_key
           FROM public.app_contact_search_current))))
UNION ALL
 SELECT 'relance'::text AS objet,
    (x.id)::text AS ligne,
    x.hektor_contact_id,
    x.contact_search_key
   FROM public.app_relance_rapprochement x
  WHERE ((x.contact_search_key IS NOT NULL) AND (x.contact_search_key !~~ 'contact:%'::text) AND (NOT (x.contact_search_key IN ( SELECT app_contact_search_current.contact_search_key
           FROM public.app_contact_search_current))))
UNION ALL
 SELECT 'retour_acquereur'::text AS objet,
    (x.app_dossier_id)::text AS ligne,
    x.hektor_contact_id,
    x.contact_search_key
   FROM public.app_bien_acquereur_statut x
  WHERE (NOT (x.contact_search_key IN ( SELECT app_contact_search_current.contact_search_key
           FROM public.app_contact_search_current)))
UNION ALL
 SELECT 'envoi_email'::text AS objet,
    (x.id)::text AS ligne,
    x.hektor_contact_id,
    x.contact_search_key
   FROM public.app_email_envoi x
  WHERE ((x.contact_search_key IS NOT NULL) AND (NOT (x.contact_search_key IN ( SELECT app_contact_search_current.contact_search_key
           FROM public.app_contact_search_current))));

comment on view public.app_v_orphelins_recherche is
  'C.4 20/09/2026 : lignes accrochees a une cle de recherche disparue. Seuil de la sonde data.orphelins_recherche : 0. '
  '13/11/2026 : une relance « sans recherche » (cle contact:<n°>, posee par app_create_relance_for_contact) n''en est pas une.';
comment on view public.app_search_orphans_non_rattachables is
  'Orphelins que app_sweep_search_orphans ne sait pas rattacher (sonde data.recherche_orphelin_bloque, seuil 0). '
  '13/11/2026 : les relances « sans recherche » (cle contact:<n°>) sont hors champ.';

-- Les essais (tout part au rollback)
do $essai$
declare ok int := 0; ko int := 0; j text := ''; av record;
        cle20 text; cle21_apres text; n1 int; n2 int; n1t int; n2t int; d text;
begin
  select * into av from _avant_relance_sans_recherche;
  d := pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure);
  -- ① ② le geste : la relance « sans recherche » n° 20 ne fait plus crier les sondes
  select count(*) into n1 from public.app_v_orphelins_recherche where contact_search_key like 'contact:%';
  select count(*) into n2 from public.app_search_orphans_non_rattachables where contact_search_key like 'contact:%';
  if n1 = 0 then ok := ok + 1; j := j || E'\nOK  ① sonde « orphelins » : la relance sans recherche ne compte plus'; else ko := ko + 1; j := j || E'\nKO  ① ' || n1; end if;
  if n2 = 0 then ok := ok + 1; j := j || E'\nOK  ② sonde « non rattachables » : idem'; else ko := ko + 1; j := j || E'\nKO  ② ' || n2; end if;
  -- ③ les autres orphelins n'ont pas bougé
  if (select count(*) from public.app_v_orphelins_recherche) = av.n1 and (select count(*) from public.app_search_orphans_non_rattachables) = av.n2 then
    ok := ok + 1; j := j || E'\nOK  ③ les autres orphelins : comptes inchangés (' || av.n1 || ' et ' || av.n2 || ')';
  else ko := ko + 1; j := j || E'\nKO  ③'; end if;
  -- ④ TÉMOIN INVERSE : un VRAI orphelin (la relance 21 détachée de sa recherche) est toujours vu par les deux sondes
  update public.app_relance_rapprochement set contact_search_key = 'cle-disparue-essai-13-11' where id = 21;
  select count(*) into n1t from public.app_v_orphelins_recherche where contact_search_key = 'cle-disparue-essai-13-11';
  select count(*) into n2t from public.app_search_orphans_non_rattachables where contact_search_key = 'cle-disparue-essai-13-11';
  if n1t = 1 and n2t = 1 then ok := ok + 1; j := j || E'\nOK  ④ témoin : un VRAI orphelin est toujours vu par les deux sondes';
  else ko := ko + 1; j := j || E'\nKO  ④ ' || n1t || '/' || n2t; end if;
  -- ⑤ ⑥ LE MÉNAGE tourne : il raccroche le vrai orphelin, il laisse la relance sans recherche
  perform public.app_sweep_search_orphans();
  select contact_search_key into cle20 from public.app_relance_rapprochement where id = 20;
  select contact_search_key into cle21_apres from public.app_relance_rapprochement where id = 21;
  if cle20 = 'contact:10354488' then ok := ok + 1; j := j || E'\nOK  ⑤ le ménage LAISSE la relance sans recherche (clé contact:10354488)';
  else ko := ko + 1; j := j || E'\nKO  ⑤ ' || coalesce(cle20, 'nulle'); end if;
  if cle21_apres = '43ab2b41afa29b391a2b681b' then ok := ok + 1; j := j || E'\nOK  ⑥ le ménage raccroche TOUJOURS un vrai orphelin à la recherche du contact';
  else ko := ko + 1; j := j || E'\nKO  ⑥ ' || coalesce(cle21_apres, 'nulle'); end if;
  -- ⑦ le ménage porte ses 4 gardes, les droits des sondes n'ont pas bougé
  if (length(d) - length(replace(d, 'not like ''contact:%''', ''))) / length('not like ''contact:%''') = 4
     and not has_table_privilege('authenticated', 'public.app_v_orphelins_recherche', 'select')
     and not has_table_privilege('authenticated', 'public.app_search_orphans_non_rattachables', 'select')
     and has_table_privilege('service_role', 'public.app_search_orphans_non_rattachables', 'select') then
    ok := ok + 1; j := j || E'\nOK  ⑦ 4 gardes dans le ménage ; droits des sondes inchangés';
  else ko := ko + 1; j := j || E'\nKO  ⑦'; end if;
  raise exception 'RÉPÉTITION relance sans recherche (rien n''est gardé) : % OK, % KO%', ok, ko, j;
end
$essai$;

rollback;
