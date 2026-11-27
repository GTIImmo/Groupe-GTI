-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE DE patch_realignement_42_ecritures_2026-11-24.sql
-- Il repose chaque ecriture a son ancienne place depuis la SAUVEGARDE DATEE (valeur ET reflet d'origine), et EXIGE que
--   chaque piece touchee redevienne exactement sa sauvegarde, et l'empreinte des lignes touchees celle d'AVANT le geste.
-- ⭐ « un retour arriere ne juge que SA part » : il ne touche que les 65 pieces du lot.
-- Il NE retire PAS le journal ni les sauvegardes : ils restent la trace (le journal porte le lot ; un nouveau geste du
--   meme lot est refuse par la garde du patch tant qu'on n'a pas vide le journal du lot, a la main, sur decision).
-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════

begin;

-- ─── ① LES GARDES : le geste est la, entier ─────────────────────────────────────────────────────────────────────────────
do $$
declare n int;
begin
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'realignement_42_2026-11-24';
  if n <> 46 then raise exception '⛔ garde : % ligne(s) du lot au journal au lieu de 46', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_affaire_note t on t.app_affaire_id = j.vers_app_affaire_id
   where j.lot = 'realignement_42_2026-11-24' and j.famille = 'note' and md5(t.texte) = j.note_md5;
  if n <> 31 then raise exception '⛔ garde : % note(s) deplacee(s) retrouvee(s) sur 31', n; end if;
  select count(*) into n from public.app_affaire_note where app_affaire_id < 0;
  if n <> 0 then raise exception '⛔ garde : % note(s) a un numero negatif', n; end if;
end $$;

-- ─── ② LE RETOUR, SIMULTANE ────────────────────────────────────────────────────────────────────────────────────────────
-- le registre : vider les cibles (seulement si elles portent ENCORE la valeur posee), puis reposer chaque source
update public.app_affaire_ledger x set date_annulation_app = case when v.famille = 'date_annulation_app' then null else x.date_annulation_app end, motif_annulation_app = case when v.famille = 'motif_annulation_app' then null else x.motif_annulation_app end, honoraires_entree_app = case when v.famille = 'honoraires_entree_app' then null else x.honoraires_entree_app end
  from public.app_classeur_realignement_journal v
 where v.lot = 'realignement_42_2026-11-24' and v.famille <> 'note' and v.geste = 'DEPLACER' and x.app_affaire_id = v.vers_app_affaire_id
   and case v.famille when 'date_annulation_app' then x.date_annulation_app when 'motif_annulation_app' then x.motif_annulation_app when 'honoraires_entree_app' then x.honoraires_entree_app when 'vente_reglee_app' then x.vente_reglee_app when 'numero_facture_app' then x.numero_facture_app end = v.valeur;
update public.app_affaire_ledger set date_annulation_app = s.date_annulation_app from public.app_affaire_ledger_avant_realignement_20261124 s where s.app_affaire_id = 4385 and public.app_affaire_ledger.app_affaire_id = 4385 and public.app_affaire_ledger.date_annulation_app is null;
update public.app_affaire_ledger set date_annulation_app = s.date_annulation_app from public.app_affaire_ledger_avant_realignement_20261124 s where s.app_affaire_id = 16377 and public.app_affaire_ledger.app_affaire_id = 16377 and public.app_affaire_ledger.date_annulation_app is null;
update public.app_affaire_ledger set date_annulation_app = s.date_annulation_app from public.app_affaire_ledger_avant_realignement_20261124 s where s.app_affaire_id = 17387 and public.app_affaire_ledger.app_affaire_id = 17387 and public.app_affaire_ledger.date_annulation_app is null;
update public.app_affaire_ledger set date_annulation_app = s.date_annulation_app from public.app_affaire_ledger_avant_realignement_20261124 s where s.app_affaire_id = 24450 and public.app_affaire_ledger.app_affaire_id = 24450 and public.app_affaire_ledger.date_annulation_app is null;
update public.app_affaire_ledger set date_annulation_app = s.date_annulation_app from public.app_affaire_ledger_avant_realignement_20261124 s where s.app_affaire_id = 27134 and public.app_affaire_ledger.app_affaire_id = 27134 and public.app_affaire_ledger.date_annulation_app is null;
update public.app_affaire_ledger set date_annulation_app = s.date_annulation_app from public.app_affaire_ledger_avant_realignement_20261124 s where s.app_affaire_id = 27195 and public.app_affaire_ledger.app_affaire_id = 27195 and public.app_affaire_ledger.date_annulation_app is null;
update public.app_affaire_ledger set motif_annulation_app = s.motif_annulation_app from public.app_affaire_ledger_avant_realignement_20261124 s where s.app_affaire_id = 4480 and public.app_affaire_ledger.app_affaire_id = 4480 and public.app_affaire_ledger.motif_annulation_app is null;
update public.app_affaire_ledger set motif_annulation_app = s.motif_annulation_app from public.app_affaire_ledger_avant_realignement_20261124 s where s.app_affaire_id = 16378 and public.app_affaire_ledger.app_affaire_id = 16378 and public.app_affaire_ledger.motif_annulation_app is null;
update public.app_affaire_ledger set motif_annulation_app = s.motif_annulation_app from public.app_affaire_ledger_avant_realignement_20261124 s where s.app_affaire_id = 16382 and public.app_affaire_ledger.app_affaire_id = 16382 and public.app_affaire_ledger.motif_annulation_app is null;
update public.app_affaire_ledger set motif_annulation_app = s.motif_annulation_app from public.app_affaire_ledger_avant_realignement_20261124 s where s.app_affaire_id = 26013 and public.app_affaire_ledger.app_affaire_id = 26013 and public.app_affaire_ledger.motif_annulation_app is null;
update public.app_affaire_ledger set honoraires_entree_app = s.honoraires_entree_app from public.app_affaire_ledger_avant_realignement_20261124 s where s.app_affaire_id = 28568 and public.app_affaire_ledger.app_affaire_id = 28568 and public.app_affaire_ledger.honoraires_entree_app is null;
-- les notes : numero negatif de passage, puis l'ancienne place, avec le reflet d'ORIGINE (lu dans la sauvegarde)
update public.app_affaire_note t set app_affaire_id = -t.app_affaire_id
  from public.app_classeur_realignement_journal j
 where j.lot = 'realignement_42_2026-11-24' and j.famille = 'note' and t.app_affaire_id = j.vers_app_affaire_id and md5(t.texte) = j.note_md5;
update public.app_affaire_note t
   set app_affaire_id = s.app_affaire_id, app_dossier_id = s.app_dossier_id, app_chaine_id = s.app_chaine_id
  from public.app_classeur_realignement_journal j
  join public.app_affaire_note_avant_realignement_20261124 s on s.app_affaire_id = j.de_app_affaire_id
 where j.lot = 'realignement_42_2026-11-24' and j.famille = 'note' and t.app_affaire_id = -j.vers_app_affaire_id;

-- ─── ③ LE CONTROLE : chaque piece touchee redevient EXACTEMENT sa sauvegarde (registre ET notes) ──────────────────────
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_affaire_ledger_avant_realignement_20261124 s
    join public.app_affaire_ledger x using (app_affaire_id)
   where (x.date_annulation_app, x.motif_annulation_app, x.honoraires_entree_app, x.vente_reglee_app, x.numero_facture_app)
         is distinct from
         (s.date_annulation_app, s.motif_annulation_app, s.honoraires_entree_app, s.vente_reglee_app, s.numero_facture_app);
  if n <> 0 then raise exception '⛔ controle : % ligne(s) du registre differente(s) de leur sauvegarde', n; end if;
  select count(*) into n from (
    (select app_affaire_id, origine, md5(texte), app_dossier_id, app_chaine_id from public.app_affaire_note_avant_realignement_20261124
     except select app_affaire_id, origine, md5(texte), app_dossier_id, app_chaine_id from public.app_affaire_note
     where app_affaire_id in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813))
    union all
    (select app_affaire_id, origine, md5(texte), app_dossier_id, app_chaine_id from public.app_affaire_note
     where app_affaire_id in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813)
     except select app_affaire_id, origine, md5(texte), app_dossier_id, app_chaine_id from public.app_affaire_note_avant_realignement_20261124)) d;
  if n <> 0 then raise exception '⛔ controle : % note(s) differente(s) de leur sauvegarde', n; end if;
  select count(*) into n from public.app_affaire_note where app_affaire_id < 0;
  if n <> 0 then raise exception '⛔ controle : % note(s) restee(s) a un numero negatif', n; end if;
  e := (select md5(coalesce((select string_agg(concat_ws('|', l.app_affaire_id, l.vente_reglee_app, l.numero_facture_app,
         l.date_annulation_app, l.motif_annulation_app, l.honoraires_entree_app), ';' order by l.app_affaire_id)
    from public.app_affaire_ledger l where l.app_affaire_id in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813)), '') || '#' ||
  coalesce((select string_agg(concat_ws('|', n.app_affaire_id, n.origine, md5(n.texte), n.app_dossier_id, n.app_chaine_id,
         n.ecrit_par), ';' order by n.app_affaire_id)
    from public.app_affaire_note n where abs(n.app_affaire_id) in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813)), '')));
  if e <> '37add335313df9598820fbda7c003ba6' then raise exception '⛔ controle : empreinte % au lieu de 37add335313df9598820fbda7c003ba6 (celle d''AVANT le geste)', e; end if;
  raise notice '✅ chaque piece touchee est revenue a sa sauvegarde ; empreinte %', e;
end $$;

commit;
