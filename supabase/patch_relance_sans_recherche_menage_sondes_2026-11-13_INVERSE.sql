-- RETOUR ARRIÈRE — patch_relance_sans_recherche_menage_sondes_2026-11-13.sql : remet le ménage et les deux sondes comme le 13/11 avant la pose.
-- Il ne juge que SA part : il vérifie que la garde est bien là avant de la retirer, et qu'il n'en reste rien après.
begin;
set local lock_timeout = '5s';
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
commit;
