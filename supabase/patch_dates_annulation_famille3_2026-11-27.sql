-- patch_dates_annulation_famille3_2026-11-27 -- genere par phase2/checks/dates_annulation_famille3_generer_patch_2026-11-27.py (son mot du 27/11)
-- Retour arriere : ..._INVERSE.sql . Controle : ..._REPETITION.sql

begin;

-- ─── ① LES GARDES : 23 compromis annules SANS date, tels que lus ────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_ledger_avant_dates_f3_20261127') is not null then raise exception '⛔ garde : la sauvegarde existe deja -- ce patch ne se rejoue pas'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'dates_annulation_famille3_2026-11-27';
  if n <> 0 then raise exception '⛔ garde : % ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_affaire_ledger where app_affaire_id in (20264, 4267, 4268, 14813, 4370, 7605, 4480, 24380, 11579, 1101, 24331, 27445, 16342, 17131, 26023, 4649, 7450, 4651, 7903, 19814, 11205, 1335, 19815) and kind = 'compromis'
     and state = 'cancelled' and coalesce(date_annulation_app, '') = '';
  if n <> 23 then raise exception '⛔ garde : % compromis annule(s) SANS date sur 23', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, app_chaine_id, app_dossier_numero, coalesce(date_annulation_app, '-'), coalesce(motif_annulation_app, '-'), coalesce(vente_reglee_app, '-'), coalesce(numero_facture_app, '-'), coalesce(honoraires_entree_app::text, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (20264, 4267, 4268, 14813, 4370, 7605, 4480, 24380, 11579, 1101, 24331, 27445, 16342, 17131, 26023, 4649, 7450, 4651, 7903, 19814, 11205, 1335, 19815));
  if e <> 'dccd53de9d1a3ddd2a3438675618a333' then raise exception '⛔ garde : les 23 lignes ont change depuis la fabrication (%)', e; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(date_annulation_app, '') <> '') <> 449 then
    raise exception '⛔ garde : le nombre de dates d''annulation a change depuis la fabrication'; end if;
  raise notice '✅ gardes : 23 compromis annules sans date, tels que lus';
end $$;

-- ─── ② LA SAUVEGARDE DATEE des 23 lignes, AVEC la cle primaire et la RLS ──────────────────────────────────────────────
create table public.app_affaire_ledger_avant_dates_f3_20261127 as select * from public.app_affaire_ledger where app_affaire_id in (20264, 4267, 4268, 14813, 4370, 7605, 4480, 24380, 11579, 1101, 24331, 27445, 16342, 17131, 26023, 4649, 7450, 4651, 7903, 19814, 11205, 1335, 19815);
alter table public.app_affaire_ledger_avant_dates_f3_20261127 add primary key (app_affaire_id);
revoke all on public.app_affaire_ledger_avant_dates_f3_20261127 from public, anon, authenticated;
alter table public.app_affaire_ledger_avant_dates_f3_20261127 enable row level security;

-- ─── ③ LE JOURNAL : chaque date, sa ligne d'origine et son numero ──────────────────────────────────────────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select 'dates_annulation_famille3_2026-11-27', v.n, 'date_annulation_app', 'date_annulation_app', 'POSER (case vide)', v.piece, d.kind, d.app_chaine_id,
       d.app_dossier_numero, d.app_dossier_uuid, v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero, v.valeur, 'VIDE',
       v.ligne, v.num, 'Sheet, image 2026-11-26_094931 (passage 82, colonne Annulee) = le Sheet du 27/11', v.pourquoi,
       'patch_dates_annulation_famille3'
  from (values
    (1, 'EO8MXFE9', 3508, 20264, '2024-04-24', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 24/04/2024 » ; aucune jumelle de R27'),
    (2, 'NSRISB3C', 3512, 4267, '2024-03-24', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 24/03/2024 » ; aucune jumelle de R27'),
    (3, '9FP3UICY', 3574, 4268, '2023-10-23', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 23/10/2023 » ; aucune jumelle de R27'),
    (4, 'SWSN80FQ', 3649, 14813, '2023-04-23', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 23/04/2023 » ; aucune jumelle de R27'),
    (5, 'FWCFAN6O', 3663, 4370, '2023-03-23', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 23/03/2023 » ; aucune jumelle de R27'),
    (6, 'R90OQT16', 3681, 7605, '2023-01-23', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 23/01/2023 » ; aucune jumelle de R27'),
    (7, '9WQ204HP', 3763, 4480, '2022-06-22', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 22/06/2022 » ; aucune jumelle de R27'),
    (8, '9KHYVR1M', 3788, 24380, '2022-05-22', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 22/05/2022 » ; aucune jumelle de R27'),
    (9, 'ULFVA1AQ', 3884, 11579, '2021-09-21', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 21/09/2021 » ; aucune jumelle de R27'),
    (10, '2FBR2M9U', 3886, 1101, '2021-09-21', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 21/09/2021 » ; aucune jumelle de R27'),
    (11, 'N8M7RKTN', 3893, 24331, '2021-09-21', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 21/09/2021 » ; aucune jumelle de R27'),
    (12, 'JRN2I7TM', 3911, 27445, '2021-08-01', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 01/08/2021 » ; aucune jumelle de R27'),
    (13, 'ZGNIYS1Z', 3912, 16342, '2021-07-21', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 21/07/2021 » ; aucune jumelle de R27'),
    (14, 'ZV3QRSJG', 3954, 17131, '2021-05-21', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 21/05/2021 » ; aucune jumelle de R27'),
    (15, 'I0K9TUCT', 3989, 26023, '2021-03-21', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 21/03/2021 » ; aucune jumelle de R27'),
    (16, 'HHQZC2QP', 3999, 4649, '2021-02-01', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 01/02/2021 » ; aucune jumelle de R27'),
    (17, 'DN5U3GER', 4037, 7450, '2020-11-20', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 20/11/2020 » ; aucune jumelle de R27'),
    (18, 'N9J2533O', 4066, 4651, '2020-09-20', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 20/09/2020 » ; aucune jumelle de R27'),
    (19, 'UAER0F0F', 4089, 7903, '2020-07-20', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 20/07/2020 » ; aucune jumelle de R27'),
    (20, '4G2UHO35', 4117, 19814, '2020-05-20', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 20/05/2020 » ; aucune jumelle de R27'),
    (21, 'ZZ5WKMWM', 4119, 11205, '2020-05-20', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 20/05/2020 » ; aucune jumelle de R27'),
    (22, 'Z6P7KE5R', 4126, 1335, '2020-04-20', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 20/04/2020 » ; aucune jumelle de R27'),
    (23, 'R7NU9NPM', 4142, 19815, '2020-02-01', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- sa regle : la date du Sheet sur SON compromis quand il n''en a pas ; Sheet « 01/02/2020 » ; aucune jumelle de R27')
  ) v(n, ligne, num, piece, valeur, pourquoi)
  join public.app_affaire_ledger d on d.app_affaire_id = v.piece;

-- ─── ④ LE GESTE : seulement des cases VIDES ───────────────────────────────────────────────────────────────────────────
update public.app_affaire_ledger l set date_annulation_app = j.valeur
  from public.app_classeur_realignement_journal j
 where j.lot = 'dates_annulation_famille3_2026-11-27' and l.app_affaire_id = j.de_app_affaire_id and coalesce(l.date_annulation_app, '') = '';

-- ─── ⑤ LES CONTROLES ───────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_classeur_realignement_journal j join public.app_affaire_ledger l
    on l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app = j.valeur
   where j.lot = 'dates_annulation_famille3_2026-11-27' and j.ligne_origine is not null;
  if n <> 23 then raise exception '⛔ controle : % date(s) posee(s) sur 23', n; end if;
  select count(*) into n from public.app_affaire_ledger l join public.app_affaire_ledger_avant_dates_f3_20261127 s using (app_affaire_id)
   where (l.kind, l.state, l.app_chaine_id, l.app_dossier_numero, l.motif_annulation_app, l.vente_reglee_app,
          l.numero_facture_app, l.honoraires_entree_app, l.date)
         is distinct from (s.kind, s.state, s.app_chaine_id, s.app_dossier_numero, s.motif_annulation_app, s.vente_reglee_app,
                           s.numero_facture_app, s.honoraires_entree_app, s.date);
  if n <> 0 then raise exception '⛔ controle : % ligne(s) ont bouge hors de leur date', n; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(date_annulation_app, '') <> '') <> 449 + 23 then
    raise exception '⛔ controle : le nombre de dates d''annulation n''est pas 449 + 23'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'dates_annulation_famille3_2026-11-27';
  if n <> 23 then raise exception '⛔ controle : % ligne(s) au journal sur 23', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, app_chaine_id, app_dossier_numero, coalesce(date_annulation_app, '-'), coalesce(motif_annulation_app, '-'), coalesce(vente_reglee_app, '-'), coalesce(numero_facture_app, '-'), coalesce(honoraires_entree_app::text, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (20264, 4267, 4268, 14813, 4370, 7605, 4480, 24380, 11579, 1101, 24331, 27445, 16342, 17131, 26023, 4649, 7450, 4651, 7903, 19814, 11205, 1335, 19815));
  if e <> 'ed9a346bf8c6fb30ff91f8638b242725' then raise exception '⛔ controle : empreinte apres % au lieu de ed9a346bf8c6fb30ff91f8638b242725', e; end if;
  raise notice '✅ 23 dates posees sur leur compromis ; le reste des lignes intact ; empreinte apres %', e;
end $$;

commit;
