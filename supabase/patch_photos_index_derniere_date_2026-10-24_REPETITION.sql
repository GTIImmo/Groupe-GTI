-- ============================================================================
-- REPETITION -- l'index de app_photos_remplir_adresses_app (24/10/2026)
-- ============================================================================
-- ⚠⚠ A COLLER EN UNE SEULE FOIS, EN ENTIER. Le `begin;` de la premiere ligne et
--    l'ERREUR VOLONTAIRE de la fin font que RIEN n'est ecrit : ni l'index, ni
--    les statistiques, ni les galeries.
-- ⚠ PAS entre 05:00 et 07:45, PAS pendant un geste photo : dans la transaction,
--   l'index est pose SANS `concurrently` (impossible autrement), ce qui BLOQUE
--   les ecritures de photos le temps de la repetition (quelques secondes).
--   Le bloc 0 s'arrete tout seul si un geste photo est en cours. Eviter aussi
--   21:00 (GTI Entretien Photos) et 00:00 (balayage des masquees).
--   Fenetres sures : 08:00-20:45, ou 21:15-22:00.
--
-- ⭐ CE QU'ELLE PROUVE, DANS L'ORDRE REEL :
--   1-avant   sans l'index : lecture complete (TEMOIN INVERSE), sa duree, le
--             nombre de dossiers trouves
--   2-pose    l'index, puis le plan AVANT l'analyse, puis l'analyse
--   3-apres   le plan utilise l'index, la recherche est rapide, elle trouve
--             EXACTEMENT les memes dossiers, LA FONCTION ENTIERE tient sous 2 s,
--             et son empreinte n'a pas bouge (le patch ne la touche pas)
--   4-retour  l'index retire ne laisse aucune trace
--
-- ⚠ CE QU'ELLE NE PROUVE PAS : la duree PAR L'API, a froid, comme la nuit. Ici
--   la table vient d'etre relue (index + analyse) : elle est chaude. La vraie
--   preuve est l'etape ④ du patch (`node Console\remplir_adresses_photos.js`,
--   qui chronometre l'appel par l'API), puis le run de la nuit suivante.
--
-- LE MESSAGE ATTENDU si tout va bien :
--   0-garde   | gestes photo en cours                 = 0
--   1-avant   | empreinte de la fonction              = ec8066616381cdb90df38ec561f1441f
--   1-avant   | index present                         = non
--   1-avant   | plan sans l index                     = lecture complete -- c est le defaut
--   1-avant   | dossiers bouges en 48 h               = <N>
--   1-avant   | duree de la recherche                 = plusieurs centaines / milliers de ms
--   2-pose    | plan AVANT l analyse                  = (pour information : index OU lecture complete)
--   3-apres   | plan APRES l analyse                  = utilise l index
--   3-apres   | dossiers bouges en 48 h               = <N> (le meme)
--   3-apres   | memes dossiers, a l unite pres        = oui (0 manquant, 0 en trop)
--   3-apres   | duree de la recherche                 = quelques ms
--   3-apres   | la fonction entiere                   = statut ok en < 2000 ms
--   3-apres   | empreinte de la fonction              = inchangee
--   4-retour  | index retire                          = oui
-- ============================================================================

begin;

set local lock_timeout = '10s';
set local statement_timeout = '120s';

create temporary table essai_mesures (id serial, etape text, mesure text, valeur text) on commit drop;
create temporary table essai_avant (app_dossier_id bigint, dernier timestamptz) on commit drop;
create temporary table essai_apres (app_dossier_id bigint, dernier timestamptz) on commit drop;

-- =========================== 0. LA GARDE ===================================
do $garde$
declare n bigint;
begin
  select count(*) into n from public.app_console_job
   where job_type in ('set_hektor_photo_visibility', 'reorder_hektor_photos', 'upload_hektor_photo',
                      'delete_hektor_photo', 'sync_hektor_photos')
     and status in ('pending', 'running');
  if n > 0 then
    raise exception 'STOP : % geste(s) photo en cours -- relancer la repetition plus tard. Rien n a ete ecrit.', n;
  end if;
  if (now() at time zone 'Europe/Paris')::time between '05:00' and '07:45' then
    raise exception 'STOP : run ou descente en cours (05:00-07:45) -- relancer apres 07:45. Rien n a ete ecrit.';
  end if;
  insert into essai_mesures (etape, mesure, valeur) values ('0-garde ', 'gestes photo en cours                ', '0');
end
$garde$;

-- =========================== 1. AVANT ======================================
insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'empreinte de la fonction             ',
       md5(replace(pg_get_functiondef('public.app_photos_remplir_adresses_app(integer,boolean)'::regprocedure), chr(13), ''));

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'index present                        ',
       case when to_regclass('public.app_console_photo_derniere_bouge_idx') is null then 'non' else 'OUI -- deja pose ?' end;

do $avant$
declare l text; plan text := ''; t0 timestamptz; n bigint;
begin
  -- `false or ...` : la forme exacte que prend la condition de la fonction quand
  -- p_tout vaut false (plan sur mesure).
  for l in execute $q$explain select p.app_dossier_id, max(greatest(p.derives_generes_le, p.absent_depuis))
                        from public.app_console_photo p
                       where false or greatest(p.derives_generes_le, p.absent_depuis) >= now() - interval '48 hours'
                       group by p.app_dossier_id$q$ loop
    plan := plan || l || ' ';
  end loop;
  insert into essai_mesures (etape, mesure, valeur) values ('1-avant ', 'plan sans l index                    ',
    case when plan ilike '%Seq Scan%' then 'lecture complete -- c est le defaut'
         else 'INATTENDU : ' || left(plan, 160) end);

  t0 := clock_timestamp();
  insert into essai_avant (app_dossier_id, dernier)
  select p.app_dossier_id, max(greatest(p.derives_generes_le, p.absent_depuis))
    from public.app_console_photo p
   where false or greatest(p.derives_generes_le, p.absent_depuis) >= now() - interval '48 hours'
   group by p.app_dossier_id;
  get diagnostics n = row_count;
  insert into essai_mesures (etape, mesure, valeur) values
    ('1-avant ', 'dossiers bouges en 48 h              ', n::text),
    ('1-avant ', 'duree de la recherche                ', round(extract(epoch from clock_timestamp() - t0) * 1000)::text || ' ms');
end
$avant$;

-- =========================== 2. LA POSE (annulee a la fin) =================
create index app_console_photo_derniere_bouge_idx
    on public.app_console_photo ((greatest(derives_generes_le, absent_depuis)));

do $avant_analyse$
declare l text; plan text := '';
begin
  for l in execute $q$explain select p.app_dossier_id, max(greatest(p.derives_generes_le, p.absent_depuis))
                        from public.app_console_photo p
                       where false or greatest(p.derives_generes_le, p.absent_depuis) >= now() - interval '48 hours'
                       group by p.app_dossier_id$q$ loop
    plan := plan || l || ' ';
  end loop;
  insert into essai_mesures (etape, mesure, valeur) values ('2-pose  ', 'plan AVANT l analyse (information)   ',
    case when plan ilike '%derniere_bouge_idx%' then 'utilise deja l index'
         else 'lecture complete -- d ou l analyse obligatoire' end);
end
$avant_analyse$;

analyze public.app_console_photo;

-- =========================== 3. APRES ======================================
do $apres$
declare l text; plan text := ''; t0 timestamptz; n bigint; manquent bigint; en_trop bigint;
        v jsonb; ms numeric;
begin
  for l in execute $q$explain select p.app_dossier_id, max(greatest(p.derives_generes_le, p.absent_depuis))
                        from public.app_console_photo p
                       where false or greatest(p.derives_generes_le, p.absent_depuis) >= now() - interval '48 hours'
                       group by p.app_dossier_id$q$ loop
    plan := plan || l || ' ';
  end loop;
  insert into essai_mesures (etape, mesure, valeur) values ('3-apres ', 'plan APRES l analyse                 ',
    case when plan ilike '%derniere_bouge_idx%' then 'utilise l index'
         else 'NON -- n utilise PAS l index : ' || left(plan, 160) end);

  t0 := clock_timestamp();
  insert into essai_apres (app_dossier_id, dernier)
  select p.app_dossier_id, max(greatest(p.derives_generes_le, p.absent_depuis))
    from public.app_console_photo p
   where false or greatest(p.derives_generes_le, p.absent_depuis) >= now() - interval '48 hours'
   group by p.app_dossier_id;
  get diagnostics n = row_count;
  ms := round(extract(epoch from clock_timestamp() - t0) * 1000);

  select count(*) into manquent from (select * from essai_avant except select * from essai_apres) x;
  select count(*) into en_trop  from (select * from essai_apres except select * from essai_avant) y;

  insert into essai_mesures (etape, mesure, valeur) values
    ('3-apres ', 'dossiers bouges en 48 h              ', n::text),
    ('3-apres ', 'memes dossiers, a l unite pres       ',
       case when manquent = 0 and en_trop = 0 then 'oui (0 manquant, 0 en trop)'
            else 'NON : ' || manquent || ' manquant(s), ' || en_trop || ' en trop' end),
    ('3-apres ', 'duree de la recherche                ', ms::text || ' ms');

  -- LA FONCTION ENTIERE, avec ses parametres de la nuit et du worker.
  -- Elle ECRIT (galeries) -- annule par l'erreur volontaire de la fin.
  t0 := clock_timestamp();
  v := public.app_photos_remplir_adresses_app(48, false);
  ms := round(extract(epoch from clock_timestamp() - t0) * 1000);
  insert into essai_mesures (etape, mesure, valeur) values ('3-apres ', 'la fonction entiere                  ',
    'statut ' || coalesce(v->>'statut', '?') || ' en ' || ms::text || ' ms'
    || case when ms < 2000 and v->>'statut' = 'ok' then ' -- OK (< 2000 ms)' else ' -- STOP : TROP LENT ou PAS OK' end
    || ' | cibles ' || coalesce(v->>'cibles', '?') || ', vivantes remplies ' || coalesce(v->>'vivantes_remplies', '?'));
end
$apres$;

insert into essai_mesures (etape, mesure, valeur)
select '3-apres ', 'empreinte de la fonction             ',
       case when md5(replace(pg_get_functiondef('public.app_photos_remplir_adresses_app(integer,boolean)'::regprocedure), chr(13), ''))
                 = 'ec8066616381cdb90df38ec561f1441f'
            then 'inchangee (ec806661)' else 'NON -- elle a change' end;

-- =========================== 4. LE RETOUR ==================================
drop index public.app_console_photo_derniere_bouge_idx;

insert into essai_mesures (etape, mesure, valeur)
select '4-retour', 'index retire                         ',
       case when to_regclass('public.app_console_photo_derniere_bouge_idx') is null then 'oui' else 'NON' end;

-- ================== 5. L ERREUR VOLONTAIRE : tout est annule ===============
-- ⚠ Le compte rendu voyage DANS le message : un SELECT d une transaction qui
--   echoue n est pas toujours rendu par l editeur SQL.
do $fin$
declare v_txt text;
begin
  select string_agg(etape || ' | ' || mesure || ' = ' || valeur, chr(10) order by id)
    into v_txt from essai_mesures;
  raise exception '%', 'ESSAI ANNULE -- rien n a ete ecrit : ni l index, ni les statistiques, ni les galeries.'
    || chr(10) || v_txt;
end
$fin$;

rollback;
