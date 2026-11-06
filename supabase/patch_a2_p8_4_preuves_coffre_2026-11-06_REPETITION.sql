-- RÉPÉTITION de patch_a2_p8_4_preuves_coffre_2026-11-06.sql -- à lancer APRÈS le patch, dans une transaction ANNULÉE.
-- Elle n'écrit rien : elle LIT le coffre sous l'identité de vrais utilisateurs (rôle `authenticated` + leur jeton), et
-- compare ce que la règle laisse voir à ce que la garde d'accès dit. Le rôle n'est pris QU'AUTOUR de la lecture
-- (leçon du 06/11 : une mise en scène en `authenticated` n'écrit rien sous RLS).
begin;
create temp table _rep_p8_4 (controle text, ok boolean, detail text) on commit drop;
grant all on _rep_p8_4 to authenticated;
create temp table _ech (name text, app_dossier_id bigint, hid text, attendu boolean, vu boolean) on commit drop;
grant all on _ech to authenticated;

do $$
declare
  v_doc uuid := 'f0d73f5a-b283-407d-a5f8-49496deb7027';   -- le mandat Youtrust d'essai de 61398
  v_fred text := '{"sub":"d4b1685f-948b-4ce8-af15-671b94a725e6","role":"authenticated","email":"frederic.gerphagnon@gti-immobilier.fr"}';
  v_n int; v_attendu int; v_c record; v_temoins_partiels int := 0; v_commerciaux int := 0; v_ecarts int := 0;
  v_orphelin text;
begin
  -- [1] la branche est dans la règle
  insert into _rep_p8_4 select '1 branche posee', qual ilike '%app_console_dossier_document_lisible%', null
    from pg_policies where schemaname = 'storage' and tablename = 'objects' and policyname = 'hektor_console_documents_read_scope';

  -- [2] Frédéric (admin) voit les 5 fichiers du dossier de l'essai : original, signé, 3 preuves
  perform set_config('request.jwt.claims', v_fred, true);
  execute 'set local role authenticated';
  select count(*) into v_n from storage.objects where bucket_id = 'hektor-console-documents' and name like 'annonces/61398/documents/' || v_doc::text || '/%';
  execute 'reset role';
  insert into _rep_p8_4 values ('2 admin : 5 fichiers du dossier de l''essai (original + signe + 3 preuves)', v_n = 5, v_n::text);

  -- [3] Chaque commercial actif voit EXACTEMENT les ZIP ImmoSign que la garde lui ouvre -- ni plus, ni moins.
  --     ⚠ 1er passage (06/11) : la garde appelée sur les 848 ZIP pour chaque commercial a dépassé le délai. Désormais un
  --     ÉCHANTILLON par commercial : 20 ZIP de ses biens (choisis par son e-mail -- le CHOIX seulement) + 20 d'autres
  --     biens ; le VERDICT reste celui de la vraie garde (app_console_can_access_dossier), fichier par fichier.
  for v_c in select id, email from public.app_user_profile where is_active and role::text = 'commercial' order by id limit 25 loop
    v_commerciaux := v_commerciaux + 1;
    delete from _ech where true;
    insert into _ech (name, app_dossier_id, hid)
    select x.name, x.app_dossier_id, x.hektor_annonce_id from (
      (select o.name, d.app_dossier_id, d.hektor_annonce_id
         from storage.objects o
         join public.app_console_document d on d.id = (case when (storage.foldername(o.name))[4] ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' then ((storage.foldername(o.name))[4])::uuid end)
         join public.app_annonces_current a on a.hektor_annonce_id::text = d.hektor_annonce_id
        where o.bucket_id = 'hektor-console-documents' and o.name like 'annonces/%/documents/%/immosign/%' and d.storage_status = 'cloud_available'
          and lower(coalesce(a.negociateur_email, '')) = lower(coalesce(v_c.email, ''))
        order by o.name limit 20)
      union all
      (select o.name, d.app_dossier_id, d.hektor_annonce_id
         from storage.objects o
         join public.app_console_document d on d.id = (case when (storage.foldername(o.name))[4] ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' then ((storage.foldername(o.name))[4])::uuid end)
        where o.bucket_id = 'hektor-console-documents' and o.name like 'annonces/%/documents/%/immosign/%' and d.storage_status = 'cloud_available'
        order by o.name desc limit 20)
    ) x;
    perform set_config('request.jwt.claims', json_build_object('sub', v_c.id, 'role', 'authenticated')::text, true);
    update _ech set attendu = coalesce(public.app_console_can_access_dossier(app_dossier_id, hid), false) where true;
    execute 'set local role authenticated';
    update _ech e set vu = exists (select 1 from storage.objects o where o.bucket_id = 'hektor-console-documents' and o.name = e.name) where true;
    execute 'reset role';
    select count(*) filter (where vu is distinct from attendu), count(*) filter (where attendu), count(*) into v_ecarts, v_attendu, v_n from _ech;
    if v_attendu > 0 and v_attendu < v_n then v_temoins_partiels := v_temoins_partiels + 1; end if;
    insert into _rep_p8_4 values ('3 commercial ' || v_commerciaux || ' : vu = garde, fichier par fichier', v_ecarts = 0,
      v_n || ' fichiers, ' || v_attendu || ' ouverts par la garde, ' || v_ecarts || ' ecart(s)');
  end loop;
  insert into _rep_p8_4 values ('3 TEMOIN : au moins un commercial a des fichiers OUVERTS ET FERMES dans son echantillon', v_temoins_partiels > 0, v_temoins_partiels || ' sur ' || v_commerciaux);

  -- [4] les chemins mal formés rendent FAUX, jamais une erreur
  insert into _rep_p8_4 values ('4 uuid illisible -> faux', not public.app_console_dossier_document_lisible('annonces/61398/documents/pas-un-uuid/x.pdf'), null);
  insert into _rep_p8_4 values ('4 autre numero d''annonce dans le chemin -> faux', not public.app_console_dossier_document_lisible('annonces/1/documents/' || v_doc::text || '/x.pdf'), null);
  insert into _rep_p8_4 values ('4 hors annonces -> faux', not public.app_console_dossier_document_lisible('temp/uploads/' || v_doc::text || '/x.pdf'), null);

  -- [5] TÉMOIN : un objet orphelin (aucun document vivant) reste FERMÉ, même pour l'admin
  select o.name into v_orphelin from storage.objects o
   where o.bucket_id = 'hektor-console-documents' and (storage.foldername(o.name))[1] = 'annonces' and (storage.foldername(o.name))[3] = 'documents'
     and (storage.foldername(o.name))[4] ~ '^[0-9a-f-]{36}$'
     and not exists (select 1 from public.app_console_document d where d.id = (case when (storage.foldername(o.name))[4] ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' then ((storage.foldername(o.name))[4])::uuid end))
   limit 1;
  perform set_config('request.jwt.claims', v_fred, true);
  insert into _rep_p8_4 values ('5 TEMOIN : un orphelin reste ferme (admin)', v_orphelin is not null and not public.app_console_dossier_document_lisible(v_orphelin), case when v_orphelin is null then 'aucun orphelin trouve' else 'orphelin trouve' end);
end $$;

select controle, ok, detail from _rep_p8_4 order by controle;
rollback;
