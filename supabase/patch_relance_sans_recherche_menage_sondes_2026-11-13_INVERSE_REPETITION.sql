-- RÉPÉTITION DU RETOUR ARRIÈRE — patch_relance_sans_recherche_menage_sondes_2026-11-13_INVERSE.sql. Pose le patch, le défait, vérifie le retour à l'état du 13/11,
-- puis lève une erreur VOLONTAIRE : RIEN n'est gardé. Attendu : « 3 OK, 0 KO ».
-- ⚠ Pas de « commit » dans ce fichier : il se joue à blanc.
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
do $inverse$
declare d text := pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure);
        garde text := 'and x.contact_search_key not like ''contact:%'' -- 13/11 : relance « sans recherche » (clé contact:<n°>), pas un orphelin' || E'\n     ';
begin
  if (length(d) - length(replace(d, garde, ''))) / length(garde) <> 4 then
    raise exception 'ARRET : les 4 gardes du patch ne sont pas dans le menage -- rien a retirer, ou le menage a change';
  end if;
  execute replace(d, garde, '');
  if position('contact:' in pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure)) > 0 then
    raise exception 'ARRET : il reste une trace de contact: dans le menage';
  end if;
  if md5(pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure)) <> 'f39dc33f0e73a2a06bd4fce103829a43' then
    raise exception 'ARRET : le menage ne retrouve pas son empreinte du 13/11';
  end if;
end
$inverse$;
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
  WHERE (NOT (EXISTS ( SELECT 1
           FROM public.app_contact_search_current s
          WHERE (s.contact_search_key = x.contact_search_key))))
UNION ALL
 SELECT 'app_notification'::text AS table_orpheline,
    n.contact_search_key
   FROM public.app_notification n
  WHERE ((n.contact_search_key IS NOT NULL) AND (NOT (EXISTS ( SELECT 1
           FROM public.app_contact_search_current s
          WHERE (s.contact_search_key = n.contact_search_key)))));

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
  WHERE ((x.contact_search_key IS NOT NULL) AND (NOT (x.contact_search_key IN ( SELECT app_contact_search_current.contact_search_key
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
  'C.4 20/09/2026 : lignes accrochees a une cle de recherche disparue. Seuil de la sonde data.orphelins_recherche : 0.';
comment on view public.app_search_orphans_non_rattachables is null;
do $verif$
begin
  if position('contact:' in pg_get_viewdef('public.app_v_orphelins_recherche'::regclass)) > 0
     or position('contact:' in pg_get_viewdef('public.app_search_orphans_non_rattachables'::regclass)) > 0 then
    raise exception 'ARRET : une sonde garde la forme contact:';
  end if;
end
$verif$;

do $essai$
declare ok int := 0; ko int := 0; j text := '';
begin
  if md5(pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure)) = 'f39dc33f0e73a2a06bd4fce103829a43' then
    ok := ok + 1; j := j || E'\nOK  ① le ménage retrouve son empreinte du 13/11';
  else ko := ko + 1; j := j || E'\nKO  ①'; end if;
  if (select count(*) from public.app_v_orphelins_recherche where contact_search_key like 'contact:%') = 1
     and (select count(*) from public.app_search_orphans_non_rattachables where contact_search_key like 'contact:%') = 1 then
    ok := ok + 1; j := j || E'\nOK  ② les deux sondes revoient la relance n° 20, comme avant';
  else ko := ko + 1; j := j || E'\nKO  ②'; end if;
  if obj_description('public.app_search_orphans_non_rattachables'::regclass) is null
     and obj_description('public.app_v_orphelins_recherche'::regclass) not like '%13/11%' then
    ok := ok + 1; j := j || E'\nOK  ③ les commentaires sont ceux d''avant';
  else ko := ko + 1; j := j || E'\nKO  ③'; end if;
  raise exception 'RÉPÉTITION DU RETOUR ARRIÈRE (rien n''est gardé) : % OK, % KO%', ok, ko, j;
end
$essai$;

rollback;
