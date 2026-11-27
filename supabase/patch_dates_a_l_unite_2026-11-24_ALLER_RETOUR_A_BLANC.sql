-- patch_dates_a_l_unite_2026-11-24 -- genere par phase2/checks/cases_vides_generer_patchs_2026-11-24.py (son 5e mot du 24/11 : « rien ne s'ecrit sans mon accord sur le patch »)
-- Retour arriere : patch_dates_a_l_unite_2026-11-24_INVERSE.sql . Controle : patch_dates_a_l_unite_2026-11-24_REPETITION.sql
-- ⛔ A BLANC : le patch PUIS son inverse, dans la MEME transaction ; aucun commit ; erreur voulue a la fin.

begin;

-- ─── ① LES GARDES : 6 compromis ANNULES, sans date d'annulation ──────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_ledger_avant_dates_a_l_unite_20261124') is not null then
    raise exception '⛔ garde : la sauvegarde existe deja -- ce patch ne se rejoue pas';
  end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'dates_a_l_unite_2026-11-24';
  if n <> 0 then raise exception '⛔ garde : % ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_affaire_ledger
   where app_affaire_id in (27195, 4385, 27134, 16377, 17387, 24450) and kind = 'compromis' and state = 'cancelled' and date_annulation_app is null;
  if n <> 6 then raise exception '⛔ garde : % compromis annule(s) sans date sur 6', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, coalesce(date_annulation_app, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (27195, 4385, 27134, 16377, 17387, 24450));
  if e <> 'df785d764855b5721e8fe54edd072fcb' then raise exception '⛔ garde : empreinte % au lieu de df785d764855b5721e8fe54edd072fcb', e; end if;
  raise notice '✅ gardes : 6 compromis annules, sans date ; empreinte %', e;
end $$;

-- ─── ② LA SAUVEGARDE DATEE : les 6 lignes entieres ────────────────────────────────────────────────────────────────────────
create table public.app_affaire_ledger_avant_dates_a_l_unite_20261124 as
  select * from public.app_affaire_ledger where app_affaire_id in (27195, 4385, 27134, 16377, 17387, 24450);
revoke all on public.app_affaire_ledger_avant_dates_a_l_unite_20261124 from public, anon, authenticated;

-- ─── ③ LE JOURNAL : la place (le compromis) ET la ligne d'origine (id_unique, n° au Sheet) ──────────────────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ligne_origine, ligne_origine_num,
   lot_origine, pourquoi, ecrit_par)
select 'dates_a_l_unite_2026-11-24', v.n, 'date_annulation_app', 'date_annulation_app', 'POSER (case vide)', v.piece, d.kind, d.app_chaine_id,
       d.app_dossier_numero, d.app_dossier_uuid, v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero, v.valeur, v.ligne,
       v.num, 'Sheet (colonne Annulee) -- son 5e mot du 24/11', v.pourquoi, 'patch_dates_a_l_unite_2026-11-24'
  from (values
    (1, 'TR42PT5H', 173, 27195, '2025-05-20', 'sa regle du 24/11 (5e mot) : « POSE LA LEUR sur LEUR compromis quand il n''en a pas » ; la date etrangere en est partie le 24/11 (geste des 42) ; compromis du 2025-01-24'),
    (2, 'U0GQ3KTO', 3713, 4385, '2022-11-22', 'sa regle du 24/11 (5e mot) : « POSE LA LEUR sur LEUR compromis quand il n''en a pas » ; la date etrangere en est partie le 24/11 (geste des 42) ; compromis du 0000-00-00'),
    (3, 'IEYXREWQ', 3530, 27134, '2024-02-01', 'sa regle du 24/11 (5e mot) : « POSE LA LEUR sur LEUR compromis quand il n''en a pas » ; la date etrangere en est partie le 24/11 (geste des 42) ; compromis du 0000-00-00'),
    (4, 'R0JRVFDC', 4014, 16377, '2021-01-21', 'sa regle du 24/11 (5e mot) : « POSE LA LEUR sur LEUR compromis quand il n''en a pas » ; la date etrangere en est partie le 24/11 (geste des 42) ; compromis du 2020-10-27'),
    (5, 'S3HOG6UL', 3864, 17387, '2021-10-21', 'sa regle du 24/11 (5e mot) : « POSE LA LEUR sur LEUR compromis quand il n''en a pas » ; la date etrangere en est partie le 24/11 (geste des 42) ; compromis du 2021-11-03 -- ⚠ la date du Sheet est ANTERIEURE au compromis (la regle de C3 l''ecarterait)'),
    (6, '6U5DQQ4J', 3865, 24450, '2021-10-21', 'sa regle du 24/11 (5e mot) : « POSE LA LEUR sur LEUR compromis quand il n''en a pas » ; la date etrangere en est partie le 24/11 (geste des 42) ; compromis du 2021-10-28 -- ⚠ la date du Sheet est ANTERIEURE au compromis (la regle de C3 l''ecarterait)')
  ) v(n, ligne, num, piece, valeur, pourquoi)
  join public.app_affaire_ledger d on d.app_affaire_id = v.piece;

-- ─── ④ LE GESTE : la valeur LUE AU JOURNAL, seulement sur une case VIDE ───────────────────────────────────────────────────
update public.app_affaire_ledger l set date_annulation_app = j.valeur
  from public.app_classeur_realignement_journal j
 where j.lot = 'dates_a_l_unite_2026-11-24' and l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app is null;

-- ─── ⑤ LES CONTROLES ─────────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_affaire_ledger l on l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app = j.valeur
   where j.lot = 'dates_a_l_unite_2026-11-24' and j.ligne_origine is not null and j.ligne_origine_num is not null;
  if n <> 6 then raise exception '⛔ controle : % date(s) posee(s), avec leur ligne d''origine, sur 6', n; end if;
  select count(*) into n from public.app_affaire_ledger l join public.app_affaire_ledger_avant_dates_a_l_unite_20261124 s using (app_affaire_id)
   where (l.vente_reglee_app, l.numero_facture_app, l.motif_annulation_app, l.honoraires_entree_app)
         is distinct from (s.vente_reglee_app, s.numero_facture_app, s.motif_annulation_app, s.honoraires_entree_app);
  if n <> 0 then raise exception '⛔ controle : % autre(s) colonne(s) ont bouge', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, coalesce(date_annulation_app, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (27195, 4385, 27134, 16377, 17387, 24450));
  if e <> '46517bdd81346d517fed9e81bc2a7c77' then raise exception '⛔ controle : empreinte apres % au lieu de 46517bdd81346d517fed9e81bc2a7c77', e; end if;
  raise notice '✅ 6 dates posees sur leur compromis, ligne d''origine au journal ; empreinte apres %', e;
end $$;

do $$ declare e text; begin e := (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, coalesce(date_annulation_app, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (27195, 4385, 27134, 16377, 17387, 24450)); raise notice 'APRES %', e; perform set_config('ar.apres', e, true); end $$;

-- ─── LE RETOUR : vider ce que ce lot a pose (seulement si la valeur est TOUJOURS la sienne) ──────────────────────────────
update public.app_affaire_ledger l set date_annulation_app = null
  from public.app_classeur_realignement_journal j
 where j.lot = 'dates_a_l_unite_2026-11-24' and l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app = j.valeur;
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_affaire_ledger l join public.app_affaire_ledger_avant_dates_a_l_unite_20261124 s using (app_affaire_id)
   where l.date_annulation_app is distinct from s.date_annulation_app;
  if n <> 0 then raise exception '⛔ controle du retour : % ligne(s) differente(s) de la sauvegarde', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, coalesce(date_annulation_app, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (27195, 4385, 27134, 16377, 17387, 24450));
  if e <> 'df785d764855b5721e8fe54edd072fcb' then raise exception '⛔ controle du retour : empreinte % au lieu de df785d764855b5721e8fe54edd072fcb', e; end if;
end $$;

do $$ declare e text; begin e := (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, coalesce(date_annulation_app, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (27195, 4385, 27134, 16377, 17387, 24450)); raise exception 'ALLER-RETOUR A BLANC VERT : apres = % ; retour = % -- RIEN N''EST ECRIT (erreur voulue)', current_setting('ar.apres'), e; end $$;
