-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
-- LE REALIGNEMENT DES ECRITURES RAPATRIEES -- A BLANC -- LES 42 GESTES DU TEMPS 1 (passage 79, AVEC R26)              24/11/2026
-- Genere par phase2/checks/realignement_42_generer_patch_2026-11-24.py
-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
-- SON GO (24/11, 4e mot) : « LE GO PORTE SUR R26 ET LES 42 REVISES, dans TON ordre : R26 -> les 42 -> A2 -> le retrait des
--   exclusions de E dans la MEME nuit que la vague. Sauvegarde datee avant le geste . l'ancienne place au journal pour
--   chacun des 42 . l'inverse pret (garde ton empreinte 0038d306, elle doit revenir). »
--   ⭐ « Au geste reel je veux LES DEUX ecrites » (la place ET la ligne d'origine) ; « les 4 qui restent (11138, 4496, 3701,
--   21551) [...] restent NOMMEES au journal ».
--
-- CE QUE CE PATCH FAIT (31 notes, 11 ecritures du registre) :
--   . DEPLACER : 31 notes, 4 motifs, la date 16377 -> 16378, la commission 28568 -> 28569 = 37 deplacements ;
--   . METTRE DE COTE : 5 dates d'annulation (4385, 17387, 24450, 27134, 27195) -- SA REGLE du 24/11 : la bonne piece
--     n'existe pas (leur ligne n'a qu'une offre) ; « je ne veux pas qu'une date d'annulation reste affichee sur le
--     compromis d'une autre affaire : a l'ecran, ca ment ». Leur valeur et leur ancienne place vivent au JOURNAL ;
--   . les 4 NOMMEES : ecrites au journal, sans geste.
--
-- ⛔ CE QUE CE PATCH NE FAIT PAS : aucune piece creee ni supprimee, aucune chaine ni etiquette touchee, aucune part de
--   repartition (c'est A2, plus tard), RIEN chez Hektor : date_annulation_app, motif_annulation_app, honoraires_entree_app
--   sont dans COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS (phase2/sync/affaire_ledger.py) -- le push ne les envoie pas, le run ne les
--   ecrase pas ; app_affaire_note n'est ecrite que par l'app (app_affaire_note_ecrire) et par nos lots, jamais par la nuit.
--   Aucun declencheur : sur le registre, le seul declencheur de mise a jour (app_affaire_partie_apres_update) ne regarde
--   aucune de ces colonnes ; sur les notes, aucun (mesure du 24/11).
--
-- ⭐ L'ETAT D'AVANT EST CELUI DU CONTROLE : le temps 1 rejoue CHEZ SUPABASE (lecture seule, 24/11 apres-midi) rend
--   l'empreinte 0038d306, la meme que la copie locale ; avec le geste, 46 mal placees -> 4, toutes nommees.
--
-- Retour arriere : patch_realignement_42_ecritures_2026-11-24_INVERSE.sql      Controle : patch_realignement_42_ecritures_2026-11-24_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
-- ⛔ A BLANC : LE MEME CORPS, SANS AUCUN COMMIT ; IL FINIT PAR UNE ERREUR VOULUE -> TOUT EST ANNULE.

begin;

-- ─── ① LES GARDES : l'etat d'avant, EXIGE ecriture par ecriture -- sinon RIEN n'est ecrit ─────────────────────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_ledger_avant_realignement_20261124') is not null
     or to_regclass('public.app_affaire_note_avant_realignement_20261124') is not null then
    raise exception '⛔ garde : la sauvegarde datee existe deja -- ce patch ne se rejoue pas';
  end if;
  if to_regclass('public.app_classeur_realignement_journal') is not null then
    execute 'select count(*) from public.app_classeur_realignement_journal where lot = $1' into n using 'realignement_42_2026-11-24';
    if n <> 0 then raise exception '⛔ garde : % ligne(s) du lot deja au journal -- ce patch ne se rejoue pas', n; end if;
  end if;
  -- les 11 ecritures du registre qui partent : chacune porte EXACTEMENT sa valeur mesuree
  select count(*) into n from public.app_affaire_ledger l
    join (values
    (4385, 'date_annulation_app', '2022-04-22'),
    (16377, 'date_annulation_app', '2021-04-21'),
    (17387, 'date_annulation_app', '2021-12-01'),
    (24450, 'date_annulation_app', '2022-02-01'),
    (27134, 'date_annulation_app', '2023-08-01'),
    (27195, 'date_annulation_app', '2026-07-27'),
    (4480, 'motif_annulation_app', 'Retractation'),
    (16378, 'motif_annulation_app', 'Changement de situation acquereur'),
    (16382, 'motif_annulation_app', 'Pret refuse'),
    (26013, 'motif_annulation_app', 'Retractation'),
    (28568, 'honoraires_entree_app', '4000')) v(id, famille, valeur) on l.app_affaire_id = v.id
   where case v.famille when 'date_annulation_app' then l.date_annulation_app when 'motif_annulation_app' then l.motif_annulation_app when 'honoraires_entree_app' then l.honoraires_entree_app when 'vente_reglee_app' then l.vente_reglee_app when 'numero_facture_app' then l.numero_facture_app end = v.valeur;
  if n <> 11 then raise exception '⛔ garde : % ecriture(s) du registre a leur place mesuree sur 11', n; end if;
  -- leurs 6 cibles : la case est VIDE
  select count(*) into n from public.app_affaire_ledger l
    join (values
    (16378, 'date_annulation_app'),
    (4483, 'motif_annulation_app'),
    (16383, 'motif_annulation_app'),
    (16377, 'motif_annulation_app'),
    (26016, 'motif_annulation_app'),
    (28569, 'honoraires_entree_app')) v(id, famille) on l.app_affaire_id = v.id
   where case v.famille when 'date_annulation_app' then l.date_annulation_app when 'motif_annulation_app' then l.motif_annulation_app when 'honoraires_entree_app' then l.honoraires_entree_app when 'vente_reglee_app' then l.vente_reglee_app when 'numero_facture_app' then l.numero_facture_app end is null;
  if n <> 6 then raise exception '⛔ garde : % cible(s) vide(s) sur 6', n; end if;
  -- les 31 notes qui partent : leur origine et l'empreinte de leur texte ; leurs cibles : libres, ou liberees par le
  --   meme geste (l'echange 27195 <-> 27196, la suite 27141 -> 27134 -> 27140)
  select count(*) into n from public.app_affaire_note t
    join (values
    (177, 178, 'classeur:F+G', '5a0ae56c486583c4b39b0b30a98657f0'),
    (1059, 1061, 'classeur:F+G', '09f287afb3a408ea4a8b104a8b6ca955'),
    (1101, 1104, 'classeur:F', '88a5e7993d41f070224c2711108d68f6'),
    (3650, 3646, 'classeur:F+G', 'f1c5ce901c37bf4fec6a5a2692e026fc'),
    (3701, 3699, 'classeur:G', 'b273a5ea8ba34238d104fef9df8ea7a5'),
    (4196, 4197, 'classeur:F+G', '92045929f9cd738f35d8485838ca2376'),
    (4385, 4387, 'classeur:F', 'e9cdfb971d223770c94e628eaeec15c1'),
    (4496, 19130, 'classeur:F', '92891440021060b97d5af5febcaa7985'),
    (6171, 6172, 'classeur:F+G', 'd78382c85ff68e2dc60ab35704f0e651'),
    (6555, 6554, 'classeur:F', '201a9a44d65b11437690922368fc3ae4'),
    (11138, 11139, 'classeur:F+G', 'e26e65b2a6007c51568455ba8375af6e'),
    (14111, 14115, 'classeur:G', 'f4217dd4e5b74fa12d43c6bee10f287c'),
    (14813, 14816, 'classeur:F+G', 'a71fb83a1fa0fb40740cb044959d48d6'),
    (15004, 15005, 'classeur:F+G', 'c88b737f01da2cf0a6462a3933195dc3'),
    (16342, 16343, 'classeur:F', '1dce13b343600b370b0689c3afaa249b'),
    (16377, 16378, 'classeur:F', '42db693e9eb3234db5926e834d8529e0'),
    (17136, 17131, 'classeur:F', '26cb7f4acaba4eddc89f41c2ede54b63'),
    (17427, 17431, 'classeur:F', '8faf42a67bf2e73a145e3f7d60c8e7f0'),
    (19133, 19132, 'classeur:F+G', 'cde9319350af0d3808b8d27b63ab5276'),
    (20264, 20268, 'classeur:F+G', '84db9ae61f8bb5f30d451f82b6ff43ca'),
    (23050, 23054, 'classeur:F', 'cfac0bfdc62a07c405349a87de30e9ae'),
    (24450, 24454, 'classeur:F', 'ec316d532a288209959a2ea0002891ef'),
    (26013, 26016, 'classeur:G', '6d1f6db2d6f58f3d03b1de45ae0c3600'),
    (27134, 27140, 'classeur:F+G', '8dd28b0ce6957afe95e815f72c399b76'),
    (27141, 27134, 'classeur:F+G', '126098e70e66f45682aacfc2801da61f'),
    (27195, 27196, 'classeur:F+G', '2b817378f2954e1b30740ff2be1e2aee'),
    (27196, 27195, 'classeur:G', 'c72466c1fce491afae51ff3c0cb078a5'),
    (27445, 27449, 'classeur:F', '042fcb6ffee89ceeb81f9fc2aa91dc9f'),
    (27512, 27513, 'classeur:F', 'd881137492dce05c245ba6c11a82f1a3'),
    (28568, 28569, 'classeur:G', '4f289d3ebcc536e0921ecdd2af4a8b65'),
    (30813, 23801, 'classeur:G', '1d5769d753f91aee927ba3ecfaded706')) v(de, vers, origine, empreinte) on t.app_affaire_id = v.de
   where t.origine = v.origine and md5(t.texte) = v.empreinte;
  if n <> 31 then raise exception '⛔ garde : % note(s) telles que mesurees sur 31', n; end if;
  select count(*) into n from public.app_affaire_note t
   where t.app_affaire_id in (178, 1061, 1104, 3646, 3699, 4197, 4387, 19130, 6172, 6554, 11139, 14115, 14816, 15005, 16343, 16378, 17131, 17431, 19132, 20268, 23054, 24454, 26016, 27140, 27134, 27196, 27195, 27449, 27513, 28569, 23801) and t.app_affaire_id not in (177, 1059, 1101, 3650, 3701, 4196, 4385, 4496, 6171, 6555, 11138, 14111, 14813, 15004, 16342, 16377, 17136, 17427, 19133, 20264, 23050, 24450, 26013, 27134, 27141, 27195, 27196, 27445, 27512, 28568, 30813);
  if n <> 0 then raise exception '⛔ garde : % cible(s) de note deja occupee(s)', n; end if;
  select count(*) into n from public.app_affaire_note t where t.app_affaire_id < 0;
  if n <> 0 then raise exception '⛔ garde : % note(s) a un numero negatif (un geste interrompu ?)', n; end if;
  -- les 4 NOMMEES : a leur place, telles que mesurees (elles ne bougent pas, elles sont ecrites au journal)
  select count(*) into n from (values
    (3701, 'numero_facture_app', 'GGTI00004428 reportée'),
    (4496, 'date_annulation_app', '2021-06-21'),
    (11138, 'date_annulation_app', '2026-06-02'),
    (21551, 'note', '90026668ae5f261418e4cbe9a19820e8')) v(id, famille, valeur)
   where (v.famille = 'note' and exists (select 1 from public.app_affaire_note t where t.app_affaire_id = v.id
                                          and md5(t.texte) = v.valeur))
      or (v.famille <> 'note' and exists (select 1 from public.app_affaire_ledger l where l.app_affaire_id = v.id
                                          and case v.famille when 'date_annulation_app' then l.date_annulation_app when 'motif_annulation_app' then l.motif_annulation_app when 'honoraires_entree_app' then l.honoraires_entree_app when 'vente_reglee_app' then l.vente_reglee_app when 'numero_facture_app' then l.numero_facture_app end = v.valeur));
  if n <> 4 then raise exception '⛔ garde : % nommee(s) a leur place sur 4', n; end if;
  e := (select md5(coalesce((select string_agg(concat_ws('|', l.app_affaire_id, l.vente_reglee_app, l.numero_facture_app,
         l.date_annulation_app, l.motif_annulation_app, l.honoraires_entree_app), ';' order by l.app_affaire_id)
    from public.app_affaire_ledger l where l.app_affaire_id in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813)), '') || '#' ||
  coalesce((select string_agg(concat_ws('|', n.app_affaire_id, n.origine, md5(n.texte), n.app_dossier_id, n.app_chaine_id,
         n.ecrit_par), ';' order by n.app_affaire_id)
    from public.app_affaire_note n where abs(n.app_affaire_id) in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813)), '')));
  if e <> '37add335313df9598820fbda7c003ba6' then raise exception '⛔ garde : empreinte des lignes touchees % au lieu de 37add335313df9598820fbda7c003ba6 (mesuree en lecture seule)', e; end if;
  raise notice '✅ gardes : 11 ecritures du registre, 6 cibles vides, 31 notes, 4 nommees ; empreinte des lignes touchees %', e;
end $$;

-- ─── ② LA SAUVEGARDE DATEE : les lignes ENTIERES, sources, cibles et nommees (65 pieces) ──────────────────────
create table public.app_affaire_ledger_avant_realignement_20261124 as
  select * from public.app_affaire_ledger where app_affaire_id in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813);
create table public.app_affaire_note_avant_realignement_20261124 as
  select * from public.app_affaire_note where app_affaire_id in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813);
revoke all on public.app_affaire_ledger_avant_realignement_20261124 from public, anon, authenticated;
revoke all on public.app_affaire_note_avant_realignement_20261124 from public, anon, authenticated;

-- ─── ③ LE JOURNAL (permanent) : pour chaque ecriture, SES DEUX CLES -- l'ancienne PLACE (la transaction, sa chaine, son
--   dossier) ET la LIGNE D'ORIGINE (id_unique, son numero au Sheet, son lot). C'est aussi LA que vivent les 5 dates MISES
--   DE COTE (regle 6 : on ne supprime pas, on met de cote avec son ancienne place). Les 4 nommees y sont, sans geste. ────
create table if not exists public.app_classeur_realignement_journal (
  lot                   text   not null,
  n                     int    not null,
  famille               text   not null,
  colonne               text   not null,
  geste                 text   not null,
  de_app_affaire_id     bigint not null,
  de_kind               text,
  de_app_chaine_id      bigint,
  de_dossier_numero     text,
  de_dossier_uuid       uuid,
  vers_app_affaire_id   bigint,
  vers_kind             text,
  vers_app_chaine_id    bigint,
  vers_dossier_numero   text,
  valeur                text,
  note_origine          text,
  note_md5              text,
  note_longueur         int,
  note_app_dossier_id   bigint,
  note_app_chaine_id    bigint,
  ligne_origine         text,
  ligne_origine_num     int,
  lot_origine           text,
  pourquoi              text   not null,
  ecrit_le              timestamptz not null default now(),
  ecrit_par             text   not null,
  primary key (lot, n)
);
revoke all on public.app_classeur_realignement_journal from public, anon, authenticated;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, note_origine, note_md5, note_longueur,
   note_app_dossier_id, note_app_chaine_id, ligne_origine, ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select 'realignement_42_2026-11-24', v.n, v.famille, v.colonne, v.geste, v.de, d.kind, d.app_chaine_id, d.app_dossier_numero, d.app_dossier_uuid,
       v.vers, c.kind, c.app_chaine_id, c.app_dossier_numero, v.valeur, t.origine, md5(t.texte), length(t.texte),
       t.app_dossier_id, t.app_chaine_id, v.ligne, v.num, v.lot_origine, v.pourquoi, 'patch_realignement_42_ecritures_2026-11-24'
  from (values
    (1, 'date_annulation_app', 'date_annulation_app', 'METTRE DE COTE', 4385, null, '2022-04-22', '8RWTD0YX', 3795, 'C3', 'SUR LA PIECE D''UNE AUTRE LIGNE (U0GQ3KTO) ; sa regle du 24/11 : la bonne piece n''existe pas (sa ligne n''a pas de piece de ce genre) -- mise de cote avec son ancienne place ; elle ne reste pas sur le compromis de U0GQ3KTO'),
    (2, 'date_annulation_app', 'date_annulation_app', 'DEPLACER', 16377, 16378, '2021-04-21', 'RX6J289Y', 3968, 'C3', 'SUR LA PIECE D''UNE AUTRE LIGNE (R0JRVFDC) ; vers 16378 (compromis de sa ligne), libre'),
    (3, 'date_annulation_app', 'date_annulation_app', 'METTRE DE COTE', 17387, null, '2021-12-01', '60CLRO51', 3842, 'C3', 'SUR LA PIECE D''UNE AUTRE LIGNE (S3HOG6UL) ; sa regle du 24/11 : la bonne piece n''existe pas (sa ligne n''a pas de piece de ce genre) -- mise de cote avec son ancienne place ; elle ne reste pas sur le compromis de S3HOG6UL'),
    (4, 'date_annulation_app', 'date_annulation_app', 'METTRE DE COTE', 24450, null, '2022-02-01', '4PW2L3MG', 3817, 'C3', 'SUR LA PIECE D''UNE AUTRE LIGNE (6U5DQQ4J) ; sa regle du 24/11 : la bonne piece n''existe pas (sa ligne n''a pas de piece de ce genre) -- mise de cote avec son ancienne place ; elle ne reste pas sur le compromis de 6U5DQQ4J'),
    (5, 'date_annulation_app', 'date_annulation_app', 'METTRE DE COTE', 27134, null, '2023-08-01', '2HOL5ISX', 3605, 'C3', 'SUR LA PIECE D''UNE AUTRE LIGNE (IEYXREWQ) ; sa regle du 24/11 : la bonne piece n''existe pas (sa ligne n''a pas de piece de ce genre) -- mise de cote avec son ancienne place ; elle ne reste pas sur le compromis de IEYXREWQ'),
    (6, 'date_annulation_app', 'date_annulation_app', 'METTRE DE COTE', 27195, null, '2026-07-27', '739a0db1', 4668, 'C3', 'SUR LA PIECE D''UNE AUTRE LIGNE (TR42PT5H) ; sa regle du 24/11 : la bonne piece n''existe pas (sa ligne n''a pas de piece de ce genre) -- mise de cote avec son ancienne place ; elle ne reste pas sur le compromis de TR42PT5H'),
    (7, 'motif_annulation_app', 'motif_annulation_app', 'DEPLACER', 4480, 4483, 'Retractation', '3308P0UX', 3785, 'C4 motifs', 'SUR LA PIECE D''UNE AUTRE LIGNE (9WQ204HP) ; vers 4483 (offre de sa ligne), libre'),
    (8, 'motif_annulation_app', 'motif_annulation_app', 'DEPLACER', 16378, 16383, 'Changement de situation acquereur', 'CITFQGOB', 4067, 'C4 motifs', 'SUR LA PIECE D''UNE AUTRE LIGNE (RX6J289Y) ; vers 16383 (offre de sa ligne), libre'),
    (9, 'motif_annulation_app', 'motif_annulation_app', 'DEPLACER', 16382, 16377, 'Pret refuse', 'R0JRVFDC', 4014, 'C4 motifs', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier, aujourd''hui deja et a l''arrivee) ; vers 16377 (compromis de sa ligne), libre'),
    (10, 'motif_annulation_app', 'motif_annulation_app', 'DEPLACER', 26013, 26016, 'Retractation', '7MOMHHQ1', 3599, 'C4 motifs', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier a l''arrivee ; DANS aujourd''hui : c''est LA VAGUE qui l''en sortirait) ; vers 26016 (offre de sa ligne), libre'),
    (11, 'honoraires_entree_app', 'honoraires_entree_app', 'DEPLACER', 28568, 28569, '4000', '959b7669', 4457, 'C2 2_en_cours', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier, aujourd''hui deja et a l''arrivee) ; vers 28569 (offre de sa ligne), libre'),
    (12, 'note', 'texte (app_affaire_note)', 'DEPLACER', 177, 178, null, 'XCK96Z01', 3703, 'C4 classeur:F+G', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier, aujourd''hui deja et a l''arrivee) ; vers 178 (offre de sa ligne), libre'),
    (13, 'note', 'texte (app_affaire_note)', 'DEPLACER', 1059, 1061, null, 'AHKQI7MX', 3544, 'C4 classeur:F+G', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier a l''arrivee ; DANS aujourd''hui : c''est LA VAGUE qui l''en sortirait) ; vers 1061 (offre de sa ligne), libre'),
    (14, 'note', 'texte (app_affaire_note)', 'DEPLACER', 1101, 1104, null, 'E6RLLKMN', 3959, 'C4 classeur:F', 'SUR LA PIECE D''UNE AUTRE LIGNE (2FBR2M9U) ; vers 1104 (offre de sa ligne), libre'),
    (15, 'note', 'texte (app_affaire_note)', 'DEPLACER', 3650, 3646, null, '427UDDSF', 3477, 'C4 classeur:F+G', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier a l''arrivee ; DANS aujourd''hui : c''est LA VAGUE qui l''en sortirait) ; vers 3646 (compromis de sa ligne), libre'),
    (16, 'note', 'texte (app_affaire_note)', 'DEPLACER', 3701, 3699, null, 'I847SPN3', 67, 'C4 classeur:G', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier, aujourd''hui deja et a l''arrivee) ; vers 3699 (compromis de sa ligne), libre'),
    (17, 'note', 'texte (app_affaire_note)', 'DEPLACER', 4196, 4197, null, '5R6RC36Y', 3520, 'C4 classeur:F+G', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier a l''arrivee ; DANS aujourd''hui : c''est LA VAGUE qui l''en sortirait) ; vers 4197 (offre de sa ligne), libre'),
    (18, 'note', 'texte (app_affaire_note)', 'DEPLACER', 4385, 4387, null, '8RWTD0YX', 3795, 'C4 classeur:F', 'SUR LA PIECE D''UNE AUTRE LIGNE (U0GQ3KTO) ; vers 4387 (offre de sa ligne), libre'),
    (19, 'note', 'texte (app_affaire_note)', 'DEPLACER', 4496, 19130, null, '61OW86CS', 3938, 'C4 classeur:F', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier, aujourd''hui deja et a l''arrivee) ; vers 19130 (offre de sa ligne), libre'),
    (20, 'note', 'texte (app_affaire_note)', 'DEPLACER', 6171, 6172, null, 'a5cb141f', 4358, 'C4 classeur:F+G', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier, aujourd''hui deja et a l''arrivee) ; vers 6172 (offre de sa ligne), libre'),
    (21, 'note', 'texte (app_affaire_note)', 'DEPLACER', 6555, 6554, null, 'Q602VZJX', 3970, 'C4 classeur:F', 'SUR LA PIECE D''UNE AUTRE LIGNE (EGR8KXOL) ; vers 6554 (compromis de sa ligne), libre'),
    (22, 'note', 'texte (app_affaire_note)', 'DEPLACER', 11138, 11139, null, '774aa002', 4606, 'C4 classeur:F+G', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier, aujourd''hui deja et a l''arrivee) ; vers 11139 (offre de sa ligne), libre'),
    (23, 'note', 'texte (app_affaire_note)', 'DEPLACER', 14111, 14115, null, 'AYIHPHF5', 1932, 'C4 classeur:G', 'SUR LA PIECE D''UNE AUTRE LIGNE (Z3DYDC4X) ; vers 14115 (vente de sa ligne), libre'),
    (24, 'note', 'texte (app_affaire_note)', 'DEPLACER', 14813, 14816, null, 'FJS4IJGZ', 3689, 'C4 classeur:F+G', 'SUR LA PIECE D''UNE AUTRE LIGNE (SWSN80FQ) ; vers 14816 (offre de sa ligne), libre'),
    (25, 'note', 'texte (app_affaire_note)', 'DEPLACER', 15004, 15005, null, 'MY2EIUFQ', 3742, 'C4 classeur:F+G', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier a l''arrivee ; DANS aujourd''hui : c''est LA VAGUE qui l''en sortirait) ; vers 15005 (offre de sa ligne), libre'),
    (26, 'note', 'texte (app_affaire_note)', 'DEPLACER', 16342, 16343, null, 'YATQOEPB', 3996, 'C4 classeur:F', 'SUR LA PIECE D''UNE AUTRE LIGNE (ZGNIYS1Z) ; vers 16343 (offre de sa ligne), libre'),
    (27, 'note', 'texte (app_affaire_note)', 'DEPLACER', 16377, 16378, null, 'RX6J289Y', 3968, 'C4 classeur:F', 'SUR LA PIECE D''UNE AUTRE LIGNE (R0JRVFDC) ; vers 16378 (compromis de sa ligne), libre'),
    (28, 'note', 'texte (app_affaire_note)', 'DEPLACER', 17136, 17131, null, 'ZV3QRSJG', 3954, 'C4 classeur:F', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier, aujourd''hui deja et a l''arrivee) ; vers 17131 (compromis de sa ligne), libre'),
    (29, 'note', 'texte (app_affaire_note)', 'DEPLACER', 17427, 17431, null, 'OXQSBZ9V', 3961, 'C4 classeur:F', 'SUR LA PIECE D''UNE AUTRE LIGNE (87QOXR64) ; vers 17431 (offre de sa ligne), libre'),
    (30, 'note', 'texte (app_affaire_note)', 'DEPLACER', 19133, 19132, null, 'V3FO5NDA', 3632, 'C4 classeur:F+G', 'SUR LA PIECE D''UNE AUTRE LIGNE (6FQO29C8) ; vers 19132 (offre de sa ligne), libre'),
    (31, 'note', 'texte (app_affaire_note)', 'DEPLACER', 20264, 20268, null, 'E1WD68ZB', 3561, 'C4 classeur:F+G', 'SUR LA PIECE D''UNE AUTRE LIGNE (EO8MXFE9) ; vers 20268 (offre de sa ligne), libre'),
    (32, 'note', 'texte (app_affaire_note)', 'DEPLACER', 23050, 23054, null, 'SBH4QWDW', 4005, 'C4 classeur:F', 'SUR LA PIECE D''UNE AUTRE LIGNE (VMWFLLW4) ; vers 23054 (offre de sa ligne), libre'),
    (33, 'note', 'texte (app_affaire_note)', 'DEPLACER', 24450, 24454, null, '4PW2L3MG', 3817, 'C4 classeur:F', 'SUR LA PIECE D''UNE AUTRE LIGNE (6U5DQQ4J) ; vers 24454 (offre de sa ligne), libre'),
    (34, 'note', 'texte (app_affaire_note)', 'DEPLACER', 26013, 26016, null, '7MOMHHQ1', 3599, 'C4 classeur:G', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier a l''arrivee ; DANS aujourd''hui : c''est LA VAGUE qui l''en sortirait) ; vers 26016 (offre de sa ligne), libre'),
    (35, 'note', 'texte (app_affaire_note)', 'DEPLACER', 27134, 27140, null, '2HOL5ISX', 3605, 'C4 classeur:F+G', 'SUR LA PIECE D''UNE AUTRE LIGNE (IEYXREWQ) ; vers 27140 (offre de sa ligne), libre'),
    (36, 'note', 'texte (app_affaire_note)', 'DEPLACER', 27141, 27134, null, 'IEYXREWQ', 3530, 'C4 classeur:F+G', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier, aujourd''hui deja et a l''arrivee) ; vers 27134 (compromis de sa ligne), liberee par le meme geste (echange)'),
    (37, 'note', 'texte (app_affaire_note)', 'DEPLACER', 27195, 27196, null, '739a0db1', 4668, 'C4 classeur:F+G', 'SUR LA PIECE D''UNE AUTRE LIGNE (TR42PT5H) ; vers 27196 (offre de sa ligne), liberee par le meme geste (echange)'),
    (38, 'note', 'texte (app_affaire_note)', 'DEPLACER', 27196, 27195, null, 'TR42PT5H', 173, 'C4 classeur:G', 'SUR LA PIECE D''UNE AUTRE LIGNE (739a0db1) ; vers 27195 (compromis de sa ligne), liberee par le meme geste (echange)'),
    (39, 'note', 'texte (app_affaire_note)', 'DEPLACER', 27445, 27449, null, 'H78FD3YN', 3985, 'C4 classeur:F', 'SUR LA PIECE D''UNE AUTRE LIGNE (JRN2I7TM) ; vers 27449 (offre de sa ligne), libre'),
    (40, 'note', 'texte (app_affaire_note)', 'DEPLACER', 27512, 27513, null, '1D7EIYKW', 4031, 'C4 classeur:F', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier a l''arrivee ; DANS aujourd''hui : c''est LA VAGUE qui l''en sortirait) ; vers 27513 (offre de sa ligne), libre'),
    (41, 'note', 'texte (app_affaire_note)', 'DEPLACER', 28568, 28569, null, '959b7669', 4457, 'C4 classeur:G', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier, aujourd''hui deja et a l''arrivee) ; vers 28569 (offre de sa ligne), libre'),
    (42, 'note', 'texte (app_affaire_note)', 'DEPLACER', 30813, 23801, null, '2c2566d7', 4343, 'C4 classeur:G', 'SUR LA PIECE D''UNE AUTRE LIGNE (df0ce30c) ; vers 23801 (compromis de sa ligne), libre'),
    (43, 'numero_facture_app', 'numero_facture_app', 'NOMMEE (laissee en place)', 3701, null, 'GGTI00004428 reportée', 'I847SPN3', 67, 'C8', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier, aujourd''hui deja et a l''arrivee) ; REMONTE ; sa ligne n''a pas de piece de ce genre'),
    (44, 'date_annulation_app', 'date_annulation_app', 'NOMMEE (laissee en place)', 4496, null, '2021-06-21', '61OW86CS', 3938, 'C3', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier, aujourd''hui deja et a l''arrivee) ; REMONTE ; sa ligne n''a pas de piece de ce genre'),
    (45, 'date_annulation_app', 'date_annulation_app', 'NOMMEE (laissee en place)', 11138, null, '2026-06-02', '774aa002', 4606, 'C3', 'SUR UNE PIECE QU''AUCUNE LIGNE NE TIENT (⛔ HORS de son dossier, aujourd''hui deja et a l''arrivee) ; REMONTE ; sa ligne n''a pas de piece de ce genre'),
    (46, 'note', 'texte (app_affaire_note)', 'NOMMEE (laissee en place)', 21551, null, null, '53ZS73KW', 227, 'C4 classeur:G', 'SUR LA PIECE D''UNE AUTRE LIGNE (bdb548a3), SA LIGNE EN ATTENTE ; REMONTE ; sa ligne 53ZS73KW est EN ATTENTE au protocole (sans aucun lien au gel) : aucune piece pour la recevoir -- proposition : la METTRE DE COTE')
  ) v(n, famille, colonne, geste, de, vers, valeur, ligne, num, lot_origine, pourquoi)
  left join public.app_affaire_ledger d on d.app_affaire_id = v.de
  left join public.app_affaire_ledger c on c.app_affaire_id = v.vers
  left join public.app_affaire_note t on t.app_affaire_id = v.de and v.famille = 'note';

-- ─── ④ LE GESTE, SIMULTANE : toutes les ecritures qui partent sont retirees, PUIS posees ───────────────────────────────
-- le registre : on vide d'abord les 11 sources (dont les 5 dates MISES DE COTE, qui vivent au journal)...
update public.app_affaire_ledger set date_annulation_app = null where app_affaire_id = 4385 and date_annulation_app = '2022-04-22';
update public.app_affaire_ledger set date_annulation_app = null where app_affaire_id = 16377 and date_annulation_app = '2021-04-21';
update public.app_affaire_ledger set date_annulation_app = null where app_affaire_id = 17387 and date_annulation_app = '2021-12-01';
update public.app_affaire_ledger set date_annulation_app = null where app_affaire_id = 24450 and date_annulation_app = '2022-02-01';
update public.app_affaire_ledger set date_annulation_app = null where app_affaire_id = 27134 and date_annulation_app = '2023-08-01';
update public.app_affaire_ledger set date_annulation_app = null where app_affaire_id = 27195 and date_annulation_app = '2026-07-27';
update public.app_affaire_ledger set motif_annulation_app = null where app_affaire_id = 4480 and motif_annulation_app = 'Retractation';
update public.app_affaire_ledger set motif_annulation_app = null where app_affaire_id = 16378 and motif_annulation_app = 'Changement de situation acquereur';
update public.app_affaire_ledger set motif_annulation_app = null where app_affaire_id = 16382 and motif_annulation_app = 'Pret refuse';
update public.app_affaire_ledger set motif_annulation_app = null where app_affaire_id = 26013 and motif_annulation_app = 'Retractation';
update public.app_affaire_ledger set honoraires_entree_app = null where app_affaire_id = 28568 and honoraires_entree_app = '4000';
-- ... puis on pose les 6 cibles, la valeur LUE AU JOURNAL (jamais retapee)
update public.app_affaire_ledger set date_annulation_app = (select valeur from public.app_classeur_realignement_journal where lot = 'realignement_42_2026-11-24' and n = 2) where app_affaire_id = 16378 and date_annulation_app is null;
update public.app_affaire_ledger set motif_annulation_app = (select valeur from public.app_classeur_realignement_journal where lot = 'realignement_42_2026-11-24' and n = 7) where app_affaire_id = 4483 and motif_annulation_app is null;
update public.app_affaire_ledger set motif_annulation_app = (select valeur from public.app_classeur_realignement_journal where lot = 'realignement_42_2026-11-24' and n = 8) where app_affaire_id = 16383 and motif_annulation_app is null;
update public.app_affaire_ledger set motif_annulation_app = (select valeur from public.app_classeur_realignement_journal where lot = 'realignement_42_2026-11-24' and n = 9) where app_affaire_id = 16377 and motif_annulation_app is null;
update public.app_affaire_ledger set motif_annulation_app = (select valeur from public.app_classeur_realignement_journal where lot = 'realignement_42_2026-11-24' and n = 10) where app_affaire_id = 26016 and motif_annulation_app is null;
update public.app_affaire_ledger set honoraires_entree_app = (select valeur from public.app_classeur_realignement_journal where lot = 'realignement_42_2026-11-24' and n = 11) where app_affaire_id = 28569 and honoraires_entree_app is null;
-- les notes : la cle (app_affaire_id) est primaire -> deux temps, pour l'echange : un numero NEGATIF de passage, puis la
--   cible ; le reflet (app_dossier_id, app_chaine_id) suit la transaction qui recoit la note
update public.app_affaire_note set app_affaire_id = -app_affaire_id where app_affaire_id in (177, 1059, 1101, 3650, 3701, 4196, 4385, 4496, 6171, 6555, 11138, 14111, 14813, 15004, 16342, 16377, 17136, 17427, 19133, 20264, 23050, 24450, 26013, 27134, 27141, 27195, 27196, 27445, 27512, 28568, 30813);
update public.app_affaire_note t
   set app_affaire_id = j.vers_app_affaire_id, app_dossier_id = c.app_dossier_id, app_chaine_id = c.app_chaine_id
  from public.app_classeur_realignement_journal j
  join public.app_affaire_ledger c on c.app_affaire_id = j.vers_app_affaire_id
 where j.lot = 'realignement_42_2026-11-24' and j.famille = 'note' and j.geste = 'DEPLACER' and t.app_affaire_id = -j.de_app_affaire_id;

-- ─── ⑤ LES CONTROLES, DANS LA MEME TRANSACTION -- ils jugent LEUR part, et ils ARRETENT ────────────────────────────────
do $$
declare n int; m int; e text;
begin
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'realignement_42_2026-11-24';
  if n <> 46 then raise exception '⛔ controle : % ligne(s) au journal au lieu de 46', n; end if;
  -- ⭐ SA RESERVE : les DEUX cles ecrites pour chacune des 42 (la place ET la ligne d'origine)
  select count(*) into n from public.app_classeur_realignement_journal
   where lot = 'realignement_42_2026-11-24' and geste <> 'NOMMEE (laissee en place)'
     and de_app_chaine_id is not null and ligne_origine is not null and ligne_origine_num is not null and lot_origine is not null;
  if n <> 42 then raise exception '⛔ controle : % des 42 portent leurs deux cles', n; end if;
  -- les notes : chacune sur sa cible, meme texte (md5), meme origine, reflet de la cible ; aucune a un numero negatif
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_affaire_note t on t.app_affaire_id = j.vers_app_affaire_id
    join public.app_affaire_ledger c on c.app_affaire_id = j.vers_app_affaire_id
   where j.lot = 'realignement_42_2026-11-24' and j.famille = 'note' and md5(t.texte) = j.note_md5 and t.origine = j.note_origine
     and t.app_chaine_id is not distinct from c.app_chaine_id and t.app_dossier_id is not distinct from c.app_dossier_id;
  if n <> 31 then raise exception '⛔ controle : % note(s) sur leur cible sur 31', n; end if;
  select count(*) into n from public.app_affaire_note where app_affaire_id < 0;
  if n <> 0 then raise exception '⛔ controle : % note(s) restee(s) a un numero negatif', n; end if;
  select count(*) into n from public.app_affaire_note
   where app_affaire_id in (177, 1059, 1101, 3650, 3701, 4196, 4385, 4496, 6171, 6555, 11138, 14111, 14813, 15004, 16342, 16377, 17136, 17427, 19133, 20264, 23050, 24450, 26013, 27141, 27445, 27512, 28568, 30813);
  if n <> 0 then raise exception '⛔ controle : % source(s) de note encore occupee(s)', n; end if;
  -- le registre : chaque cible porte la valeur du journal ; chaque source qui n'est pas une cible est vide
  select count(*) into n from public.app_classeur_realignement_journal v
    join public.app_affaire_ledger x on x.app_affaire_id = v.vers_app_affaire_id
   where v.lot = 'realignement_42_2026-11-24' and v.famille <> 'note' and v.geste = 'DEPLACER' and case v.famille when 'date_annulation_app' then x.date_annulation_app when 'motif_annulation_app' then x.motif_annulation_app when 'honoraires_entree_app' then x.honoraires_entree_app when 'vente_reglee_app' then x.vente_reglee_app when 'numero_facture_app' then x.numero_facture_app end = v.valeur;
  if n <> 6 then raise exception '⛔ controle : % cible(s) du registre posee(s) sur 6', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal v
    join public.app_affaire_ledger x on x.app_affaire_id = v.de_app_affaire_id
   where v.lot = 'realignement_42_2026-11-24' and v.famille <> 'note' and v.geste in ('DEPLACER', 'METTRE DE COTE') and case v.famille when 'date_annulation_app' then x.date_annulation_app when 'motif_annulation_app' then x.motif_annulation_app when 'honoraires_entree_app' then x.honoraires_entree_app when 'vente_reglee_app' then x.vente_reglee_app when 'numero_facture_app' then x.numero_facture_app end is null;
  if n <> 11 then raise exception '⛔ controle : % source(s) du registre videe(s) sur 11', n; end if;
  -- ⭐ LES 5 MISES DE COTE : leur valeur et leur ancienne place vivent au journal
  select count(*) into n from public.app_classeur_realignement_journal
   where lot = 'realignement_42_2026-11-24' and geste = 'METTRE DE COTE' and valeur is not null and vers_app_affaire_id is null
     and de_app_chaine_id is not null;
  if n <> 5 then raise exception '⛔ controle : % mise(s) de cote gardee(s) sur 5', n; end if;
  -- les 4 NOMMEES : intactes
  select count(*) into n from (values
    (3701, 'numero_facture_app', 'GGTI00004428 reportée'),
    (4496, 'date_annulation_app', '2021-06-21'),
    (11138, 'date_annulation_app', '2026-06-02'),
    (21551, 'note', '90026668ae5f261418e4cbe9a19820e8')) v(id, famille, valeur)
   where (v.famille = 'note' and exists (select 1 from public.app_affaire_note t where t.app_affaire_id = v.id
                                          and md5(t.texte) = v.valeur))
      or (v.famille <> 'note' and exists (select 1 from public.app_affaire_ledger l where l.app_affaire_id = v.id
                                          and case v.famille when 'date_annulation_app' then l.date_annulation_app when 'motif_annulation_app' then l.motif_annulation_app when 'honoraires_entree_app' then l.honoraires_entree_app when 'vente_reglee_app' then l.vente_reglee_app when 'numero_facture_app' then l.numero_facture_app end = v.valeur));
  if n <> 4 then raise exception '⛔ controle : % nommee(s) intacte(s) sur 4', n; end if;
  -- la conservation : rien ne se perd -- les notes ne changent pas de nombre, les dates d'annulation perdent les 5 mises de
  --   cote (elles sont au journal), le reste ne change pas de nombre
  select count(*) into n from public.app_affaire_note_avant_realignement_20261124;
  select count(*) into m from public.app_affaire_note where app_affaire_id in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813);
  if n <> m then raise exception '⛔ controle : notes des pieces touchees % avant, % apres', n, m; end if;
  select count(*) into n from public.app_affaire_ledger_avant_realignement_20261124 where date_annulation_app is not null;
  select count(*) into m from public.app_affaire_ledger where app_affaire_id in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813) and date_annulation_app is not null;
  if n - 5 <> m then raise exception '⛔ controle : dates d''annulation % avant, % apres (attendu -5)', n, m; end if;
  e := (select md5(coalesce((select string_agg(concat_ws('|', l.app_affaire_id, l.vente_reglee_app, l.numero_facture_app,
         l.date_annulation_app, l.motif_annulation_app, l.honoraires_entree_app), ';' order by l.app_affaire_id)
    from public.app_affaire_ledger l where l.app_affaire_id in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813)), '') || '#' ||
  coalesce((select string_agg(concat_ws('|', n.app_affaire_id, n.origine, md5(n.texte), n.app_dossier_id, n.app_chaine_id,
         n.ecrit_par), ';' order by n.app_affaire_id)
    from public.app_affaire_note n where abs(n.app_affaire_id) in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813)), '')));
  if e <> '072b3cb3afbf685ca10dfb3c0e590a07' then raise exception '⛔ controle : empreinte apres % au lieu de 072b3cb3afbf685ca10dfb3c0e590a07 (celle de l''A_BLANC)', e; end if;
  raise notice '✅ 46 lignes au journal (42 gestes + 4 nommees, les deux cles) . 31 notes sur leur cible . '
    '6 cibles du registre posees . 11 sources videes dont 5 mises de cote au journal . 4 nommees intactes . '
    'conservation BOUCLE . empreinte apres %', e;
end $$;

do $$
declare e text;
begin
  e := (select md5(coalesce((select string_agg(concat_ws('|', l.app_affaire_id, l.vente_reglee_app, l.numero_facture_app,
         l.date_annulation_app, l.motif_annulation_app, l.honoraires_entree_app), ';' order by l.app_affaire_id)
    from public.app_affaire_ledger l where l.app_affaire_id in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813)), '') || '#' ||
  coalesce((select string_agg(concat_ws('|', n.app_affaire_id, n.origine, md5(n.texte), n.app_dossier_id, n.app_chaine_id,
         n.ecrit_par), ';' order by n.app_affaire_id)
    from public.app_affaire_note n where abs(n.app_affaire_id) in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813)), '')));
  raise exception 'A BLANC VERT : toutes les gardes et tous les controles sont passes ; empreinte apres = % -- RIEN N''EST ECRIT (erreur voulue)', e;
end $$;
