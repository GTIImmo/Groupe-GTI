-- patch_dates_annulation_2026-11-25 -- genere par phase2/checks/dates_annulation_generer_patch_2026-11-25.py (son mot du 25/11)

begin;

do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_ledger_avant_dates_annulation_20261125') is not null then raise exception '⛔ garde : la sauvegarde existe deja'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'dates_annulation_2026-11-25';
  if n <> 0 then raise exception '⛔ garde : % ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_affaire_ledger where app_affaire_id in (27195, 4385, 27134, 16377) and kind = 'compromis'
     and state = 'cancelled' and date_annulation_app is null;
  if n <> 4 then raise exception '⛔ garde : % compromis annule(s) SANS DATE sur 4', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, coalesce(date_annulation_app, '-'), coalesce(motif_annulation_app, '-'), coalesce(vente_reglee_app, '-'), coalesce(numero_facture_app, '-'), coalesce(honoraires_entree_app::text, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (27195, 4385, 27134, 16377, 17387, 24450, 20073));
  if e <> '4011dda97ca0bcfc4d6d69a547ac00c2' then raise exception '⛔ garde : les 7 lignes ont change depuis la fabrication (%)', e; end if;
  raise notice '✅ gardes : 4 compromis annules sans date ; les 7 lignes telles que lues';
end $$;
create table public.app_affaire_ledger_avant_dates_annulation_20261125 as select * from public.app_affaire_ledger where app_affaire_id in (27195, 4385, 27134, 16377, 17387, 24450, 20073);
revoke all on public.app_affaire_ledger_avant_dates_annulation_20261125 from public, anon, authenticated;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select 'dates_annulation_2026-11-25', v.n, 'date_annulation_app', 'date_annulation_app', v.geste, v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero,
       d.app_dossier_uuid, v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero, v.valeur, coalesce(d.date_annulation_app, 'VIDE'),
       v.ligne, v.num, 'Sheet du 25/11 (image 2026-11-25_072625, colonne Annulee) -- son mot du 25/11', v.pourquoi,
       'patch_dates_annulation'
  from (values
    (1, 'TR42PT5H', 173, 27195, '2025-05-20', 'POSER (case vide)', 'sa regle : la date du Sheet sur SON compromis quand il n''en a pas (compromis du 24/01/2025)'),
    (2, 'U0GQ3KTO', 3713, 4385, '2022-11-22', 'POSER (case vide)', 'sa regle : la date du Sheet sur SON compromis quand il n''en a pas (compromis sans date chez Hektor)'),
    (3, 'IEYXREWQ', 3530, 27134, '2024-02-01', 'POSER (case vide)', 'sa regle : la date du Sheet sur SON compromis quand il n''en a pas (compromis sans date chez Hektor)'),
    (4, 'R0JRVFDC', 4014, 16377, '2021-01-21', 'POSER (case vide)', 'sa regle : la date du Sheet sur SON compromis quand il n''en a pas (compromis du 27/10/2020)'),
    (5, 'S3HOG6UL', 3864, 17387, '2021-10-21', 'NOMMEE -- rien ecrit', 'ECARTEE : la date du Sheet (21/10/2021) est ANTERIEURE au compromis (03/11/2021) -- sa decision du 24/11, comme les 106 de C3'),
    (6, '6U5DQQ4J', 3865, 24450, '2021-10-21', 'NOMMEE -- rien ecrit', 'ECARTEE : la date du Sheet (21/10/2021) est ANTERIEURE au compromis (28/10/2021) -- sa decision du 24/11, comme les 106 de C3'),
    (7, 'T2GZOY5O', 3856, 20073, '2021-11-21', 'NOMMEE -- rien ecrit', 'EN RESERVE : jumelle de O6R10ZQA (meme affaire, mandat 4369) ; O6R10ZQA est la bonne et sa date 21/09/2021 est DEJA sur 20073 -- sa decision du 24/11')
  ) v(n, ligne, num, piece, valeur, geste, pourquoi)
  join public.app_affaire_ledger d on d.app_affaire_id = v.piece;
update public.app_affaire_ledger l set date_annulation_app = j.valeur
  from public.app_classeur_realignement_journal j
 where j.lot = 'dates_annulation_2026-11-25' and j.geste = 'POSER (case vide)' and l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app is null;
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_classeur_realignement_journal j join public.app_affaire_ledger l
    on l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app = j.valeur
   where j.lot = 'dates_annulation_2026-11-25' and j.geste = 'POSER (case vide)' and j.ligne_origine is not null;
  if n <> 4 then raise exception '⛔ controle : % date(s) posee(s) sur 4', n; end if;
  -- les NOMMEES n'ont pas bouge, et aucune autre colonne des 7 lignes non plus
  select count(*) into n from public.app_affaire_ledger l join public.app_affaire_ledger_avant_dates_annulation_20261125 s using (app_affaire_id)
   where (l.app_affaire_id not in (27195, 4385, 27134, 16377) and l.date_annulation_app is distinct from s.date_annulation_app)
      or (l.motif_annulation_app, l.vente_reglee_app, l.numero_facture_app, l.honoraires_entree_app, l.kind, l.state, l.app_chaine_id)
         is distinct from (s.motif_annulation_app, s.vente_reglee_app, s.numero_facture_app, s.honoraires_entree_app, s.kind, s.state,
                           s.app_chaine_id);
  if n <> 0 then raise exception '⛔ controle : % ligne(s) ont bouge hors de leur date', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'dates_annulation_2026-11-25';
  if n <> 7 then raise exception '⛔ controle : % ligne(s) au journal sur 7', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, coalesce(date_annulation_app, '-'), coalesce(motif_annulation_app, '-'), coalesce(vente_reglee_app, '-'), coalesce(numero_facture_app, '-'), coalesce(honoraires_entree_app::text, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (27195, 4385, 27134, 16377, 17387, 24450, 20073));
  if e <> 'ce7e070a449625b7e9beb1a224043bc6' then raise exception '⛔ controle : empreinte apres % au lieu de ce7e070a449625b7e9beb1a224043bc6', e; end if;
  raise notice '✅ 4 dates posees sur leur compromis (et 7 lignes au journal, 3 nommees) ; empreinte apres %', e;
end $$;

commit;
