-- A BLANC de patch_3bis_lot_b_en_attente_de_2026-11-27 -- ETAPE 3 BIS, LOT B (EN ATTENTE DE), chez nous seulement, jamais chez Hektor
-- Genere par phase2/checks/etape_3bis_commentaires_et_avis_generer_patch_2026-11-27.py (passage officiel 84, image 2026-11-26_094931)
-- Retour arriere : ..._INVERSE.sql . Controle : ..._REPETITION.sql
-- ⛔ SANS commit : il finit par une erreur VOULUE, tout est annule.

begin;
-- 0. ⛔ LES 9 NOTES SAISIES DANS L'APP, NOMMEES : 1001384, 1001388, 1001389, 1001390, 1001391, 1001392, 1001393, 1001394, 1001395 -- on prend leur empreinte AVANT
create temp table _saisies_avant on commit drop as select app_affaire_id, md5(texte) m, origine
  from public.app_affaire_note where origine = 'saisie';
do $$ begin
  if (select string_agg(app_affaire_id::text, ',' order by app_affaire_id) from _saisies_avant) <> '1001384,1001388,1001389,1001390,1001391,1001392,1001393,1001394,1001395' then
    raise exception '⛔ garde : les notes saisies ne sont plus les 9 nommees -- rien n''est ecrit'; end if;
end $$;
-- 1. LA GARDE : rien de ce lot n'est deja pose, et les sauvegardes n'existent pas
do $$ begin
  if exists (select 1 from public.app_affaire_note where ecrit_par = 'classeur:3bisB:2026-11-27')
     or to_regclass('public.app_affaire_note_avant_3bisB_20261127') is not null or to_regclass('public.app_classeur_avis_avant_3bisB_20261127') is not null then
    raise exception '⛔ garde : le lot 3 bis B est deja (en partie) pose -- ce patch ne se rejoue pas'; end if;
end $$;
-- 2. LES SAUVEGARDES DATEES (ce que l'inverse rendra a l'octet), RLS allumee, aucun droit ouvert
create table public.app_affaire_note_avant_3bisB_20261127 as select * from public.app_affaire_note where app_affaire_id in (20, 22, 74, 101, 117, 160, 200, 958, 987, 1019, 1064, 1103, 1874, 2490, 2533, 3699, 3719, 3733, 3735, 4111, 4126, 4130, 4179, 4198, 4203, 4277, 4290, 4293, 4300, 4321, 4327, 4329, 4353, 4421, 4508, 4567, 4653, 4661, 4734, 4931, 6138, 6157, 6208, 6341, 6343, 6431, 6499, 7051, 7067, 7106, 7115, 7123, 7177, 7180, 7232, 7241, 7251, 7422, 7438, 7443, 7560, 7580, 7645, 7646, 7667, 7724, 7741, 7761, 7762, 8839, 8840, 8845, 8856, 8864, 8868, 8917, 8925, 9359, 9362, 9896, 9965, 9979, 10015, 10027, 11110, 11111, 11139, 11501, 11524, 11596, 11665, 11667, 14046, 14083, 14131, 14143, 14935, 14964, 15020, 15032, 15042, 15073, 15155, 15854, 15901, 15914, 15915, 16046, 16096, 16169, 16170, 16182, 16191, 16251, 16298, 16305, 16327, 16787, 16792, 16833, 16880, 17011, 17203, 17209, 17215, 17226, 17291, 17301, 17366, 17377, 17401, 17422, 17431, 17433, 17567, 17635, 19086, 19095, 19102, 19113, 19415, 19456, 19472, 19512, 19561, 19619, 19634, 19657, 20073, 20077, 20088, 20267, 20296, 21598, 22008, 22024, 23009, 23037, 23355, 23447, 23881, 23893, 24008, 24121, 24165, 24168, 24188, 24297, 24335, 24512, 24588, 24610, 24652, 25742, 25839, 25867, 25877, 25880, 25965, 25970, 26016, 26072, 26076, 26603, 26605, 27096, 27101, 27143, 27145, 27170, 27178, 27243, 27247, 27285, 27332, 27338, 27427, 27513, 27528, 27533, 28135, 28155, 28209, 28258, 28263, 28294, 28299, 28301, 28554, 28560, 28569, 28676, 28680, 28839, 28881, 28897, 28921, 28944, 28964, 28970, 28972, 28979, 28985, 28995, 30648, 30676, 30678, 30687, 30688, 30691, 30692, 30701, 30702, 30703, 30705, 30706, 30709, 30714, 30721, 30722, 30726, 30728, 30729, 30736, 30747, 30757, 30763, 30764, 30766, 30769, 30770, 30779, 30791, 30793, 30795, 30796, 30797, 30801, 30804, 30808, 30809, 30815, 30817, 30818, 30820, 30821, 30824, 30825, 30826, 30827, 30829, 30830, 30836, 30837, 30841, 30842, 30843, 30845, 30848, 1000142, 1000146, 1000313, 1000320, 1001530, 1001532);
create table public.app_classeur_avis_avant_3bisB_20261127 as select * from public.app_classeur_avis where id_unique in (NULL);
alter table public.app_affaire_note_avant_3bisB_20261127 enable row level security; revoke all on public.app_affaire_note_avant_3bisB_20261127 from public, anon, authenticated;
alter table public.app_classeur_avis_avant_3bisB_20261127 enable row level security; revoke all on public.app_classeur_avis_avant_3bisB_20261127 from public, anon, authenticated;
-- 3. LES NOTES NEUVES (57)
insert into public.app_affaire_note (app_affaire_id, app_dossier_id, app_chaine_id, origine, texte, ecrit_par)
values
  (7725, 1342239, 7725, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] RETRACTATION ACQ', 'classeur:3bisB:2026-11-27'),
  (22256, 1373754, 22256, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus prêt', 'classeur:3bisB:2026-11-27'),
  (16388, 1362249, 16388, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus prêt', 'classeur:3bisB:2026-11-27'),
  (30840, 1386896, 30784, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] 17/12 ADP17/12 plomb ODP31/1 DB20/2 Bougon/Khouri 🅿110K 20a', 'classeur:3bisB:2026-11-27'),
  (11963, 1351919, 11963, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] rétractation acq
.', 'classeur:3bisB:2026-11-27'),
  (4771, 1336289, 4771, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus prêt', 'classeur:3bisB:2026-11-27'),
  (25911, 1379622, 25911, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus de prêt', 'classeur:3bisB:2026-11-27'),
  (30850, 7589143, 30759, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] 22/01 retrait cuve gaz + formalités DB24/2 C. Barre / Chomarat 💰', 'classeur:3bisB:2026-11-27'),
  (19814, 1369747, 19814, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] financement pas sûr relancé 13/5', 'classeur:3bisB:2026-11-27'),
  (27372, 1383605, 27372, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] RETRACTATION ACQ', 'classeur:3bisB:2026-11-27'),
  (17428, 1365545, 17428, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] SAFER', 'classeur:3bisB:2026-11-27'),
  (30838, 1388343, 30768, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] 16/12 ADP20/12 ODP20/1 DB16/2 Me Tessier/ Rimoux-Rogue 🅿Antoine 100K 25a', 'classeur:3bisB:2026-11-27'),
  (16841, 1363926, 16841, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus de prêt', 'classeur:3bisB:2026-11-27'),
  (23486, 1375903, 23485, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] Goyet/Garde VENDEUR ne veut plus vendre manque signatures sur mandat', 'classeur:3bisB:2026-11-27'),
  (30849, 2804138, 30735, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] 18/02 point avancement cdt. susp. DB24/11/2028  🅿', 'classeur:3bisB:2026-11-27'),
  (23931, 1376844, 23931, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] retractation acq', 'classeur:3bisB:2026-11-27'),
  (4268, 1391951, 4268, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] retractation acq', 'classeur:3bisB:2026-11-27'),
  (17525, 1365788, 17525, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] retractation ACQ', 'classeur:3bisB:2026-11-27'),
  (24443, 1377617, 24443, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] changement d''avis ACQ', 'classeur:3bisB:2026-11-27'),
  (16383, 1362132, 16383, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] perte d''emploi', 'classeur:3bisB:2026-11-27'),
  (16846, 1363927, 16846, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus de prêt', 'classeur:3bisB:2026-11-27'),
  (20408, 1370633, 20408, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] retractation SRU', 'classeur:3bisB:2026-11-27'),
  (14141, 1356287, 14141, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus de prêt', 'classeur:3bisB:2026-11-27'),
  (11885, 1351841, 11885, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] rétractation acq
.', 'classeur:3bisB:2026-11-27'),
  (26152, 1380444, 26152, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] retractation SRU', 'classeur:3bisB:2026-11-27'),
  (7699, 1342178, 7699, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] SRU', 'classeur:3bisB:2026-11-27'),
  (19785, 1369668, 19784, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] ACQ se rétractent frais de saisine+désencombrement', 'classeur:3bisB:2026-11-27'),
  (25897, 1379614, 25897, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] changement d''avis acq', 'classeur:3bisB:2026-11-27'),
  (1089, 1350956, 1089, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus prêt', 'classeur:3bisB:2026-11-27'),
  (4706, 1336175, 4706, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus prêt', 'classeur:3bisB:2026-11-27'),
  (27661, 1383956, 27661, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus prêt', 'classeur:3bisB:2026-11-27'),
  (14086, 1356252, 14086, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] SRU', 'classeur:3bisB:2026-11-27'),
  (259, 1390586, 259, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus prêt', 'classeur:3bisB:2026-11-27'),
  (20613, 1370804, 20613, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] retractation SRU', 'classeur:3bisB:2026-11-27'),
  (1000141, 5834522, 1000105, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] Pailhes ACCEPTATION offre sous réserve du JUGE (mandataire)', 'classeur:3bisB:2026-11-27'),
  (11791, 1351721, 11791, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] retractation SRU', 'classeur:3bisB:2026-11-27'),
  (11972, 1351931, 11972, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] rétractation acq
.', 'classeur:3bisB:2026-11-27'),
  (24499, 1377717, 24499, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] retractation SRU', 'classeur:3bisB:2026-11-27'),
  (16377, 1362132, 16377, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] REFUS PRET', 'classeur:3bisB:2026-11-27'),
  (7605, 1341975, 7605, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus prêt', 'classeur:3bisB:2026-11-27'),
  (19665, 1369492, 19665, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus prêt', 'classeur:3bisB:2026-11-27'),
  (28289, 1385138, 28289, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] rétractation acq.', 'classeur:3bisB:2026-11-27'),
  (15096, 1358962, 15096, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] annulation ACQ', 'classeur:3bisB:2026-11-27'),
  (15059, 1358830, 15059, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus de prêt', 'classeur:3bisB:2026-11-27'),
  (24564, 1377781, 24564, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus prêt', 'classeur:3bisB:2026-11-27'),
  (23809, 1376578, 23809, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] annulée', 'classeur:3bisB:2026-11-27'),
  (4799, 1336336, 4799, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] retractation ACQ', 'classeur:3bisB:2026-11-27'),
  (269, 1107702, 269, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] RETRACTATION SRU', 'classeur:3bisB:2026-11-27'),
  (1229, 1358083, 1229, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus prêt', 'classeur:3bisB:2026-11-27'),
  (26028, 1380026, 26028, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] SRU', 'classeur:3bisB:2026-11-27'),
  (4483, 1392245, 4483, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus prêt', 'classeur:3bisB:2026-11-27'),
  (14111, 1356265, 14111, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] Latour/Pennaneach dossier complet 09/3 - maladie diagnostiquée ACQ', 'classeur:3bisB:2026-11-27'),
  (1335, 1362958, 1335, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] cpmis 21/2 reporté Mallon malade // annulé', 'classeur:3bisB:2026-11-27'),
  (11472, 1351285, 11472, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] annulation ACQ', 'classeur:3bisB:2026-11-27'),
  (26155, 1380460, 26155, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] refus prêt', 'classeur:3bisB:2026-11-27'),
  (11205, 1350748, 11205, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] prix mandat LRAR 2/12 / ACQ pas sûr / relancé 14/5 / 28.5', 'classeur:3bisB:2026-11-27'),
  (30831, 1386366, 30741, 'classeur:F', '[classeur F, suivi en cours au 26/11/2026] 29/12 formalités Robin DB29/1 💰', 'classeur:3bisB:2026-11-27');
-- 4. LES PARAGRAPHES DATES AJOUTES (285 pieces) -- le texte d'avant reste intact au-dessus
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation écrite' where app_affaire_id = 20;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 22;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation écrite' where app_affaire_id = 74;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] SRU' where app_affaire_id = 101;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] rétractation SRU' where app_affaire_id = 117;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation écrite' where app_affaire_id = 160;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] SRU' where app_affaire_id = 200;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 958;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🔴 Litige > Hordot' where app_affaire_id = 987;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation écrite' where app_affaire_id = 1019;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] mainlevée CNI V+1A' where app_affaire_id = 1064;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Giraud-Vallet/Camus BVok ADPCE 1REFUS nv rdv bq 03/9>ACQ Hospitalisé' where app_affaire_id = 1103;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulation écrite' where app_affaire_id = 1874;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] renégo 120''000€ refusée' where app_affaire_id = 2490;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] SRU' where app_affaire_id = 2533;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 27/11 délib. CA18/11 Me Chalet 💰' where app_affaire_id = 3699;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] ANNULE' where app_affaire_id = 3719;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus PC + prêts' where app_affaire_id = 3733;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] PB PC+refus PRET Rochette BVok dossOk PB logivelay devis logette Reglé' where app_affaire_id = 3735;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 4111;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Sauret/Detoqueville 20/1>Retard CovidACQ // 07/1 doss ouvert notaires.' where app_affaire_id = 4126;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Sauret/Mourier-Varenne dossOk simul+cpmis relancés 24/3 Sophie appelle les notaires' where app_affaire_id = 4130;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] SRU' where app_affaire_id = 4179;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 4198;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulé' where app_affaire_id = 4203;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 4277;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Purge locataire + liste tvx vendeurs par poste+DP à régulariser+Source' where app_affaire_id = 4290;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] PB estim bien acq en cdt -100 000€ p/r estim autre agence' where app_affaire_id = 4293;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 4300;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation ecrite' where app_affaire_id = 4321;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation acq' where app_affaire_id = 4327;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 4329;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] merule+terrain' where app_affaire_id = 4353;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] PB Charpente +mérule expertise 28/10 (vu sur crm)' where app_affaire_id = 4421;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation SRU' where app_affaire_id = 4508;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Bertucat - Partage judiciaire + attestation de propriété Me Bayle - Bertucat relancé - annulation ACQ' where app_affaire_id = 4567;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] PB financement Chapat/Rousset - RDVACQ22/1 VENDprocs pas signé 28/1 relancé 02/2+09/2' where app_affaire_id = 4653;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Sauret cpmis envoyé à Thibault >14/4 >ne pourra le retourner que le 20MAI' where app_affaire_id = 4661;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] PB RETRACTATION SANS REFUS -> LRAR MANGON 8/01' where app_affaire_id = 4734;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus CIC+CA+ SG attente VEND' where app_affaire_id = 4931;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulée' where app_affaire_id = 6138;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🔴 🅿 refusé' where app_affaire_id = 6157;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] PB prise en charge G1 - Me?/Auboyer - vente ACQ+division terrain+etude de sol / acq tjrs en négo' where app_affaire_id = 6208;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 6341;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de pret' where app_affaire_id = 6343;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] rétractation acq' where app_affaire_id = 6431;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 2 REFUS prêt' where app_affaire_id = 6499;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢 🅿70K 25a+PTZ' where app_affaire_id = 7051;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] a changé d''avis' where app_affaire_id = 7067;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 07/12 suite avocat DB29/1 Me Bouron 💰' where app_affaire_id = 7106;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] copie06/01' where app_affaire_id = 7115;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] pb PRET + maître d''oeuvre dPC24/10 ODP24/10 ADPvousfinancer' where app_affaire_id = 7123;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] pb financement' where app_affaire_id = 7177;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] pente+virage' where app_affaire_id = 7180;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 7232;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢 ❗pb volets + tvx copro' where app_affaire_id = 7241;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation écrite' where app_affaire_id = 7251;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation SRU' where app_affaire_id = 7422;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 7438;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] PB financement + parcelle devant maison à régulariser' where app_affaire_id = 7443;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 7560;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 7580;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation SRU' where app_affaire_id = 7645;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulée' where app_affaire_id = 7646;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulé' where app_affaire_id = 7667;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 7724;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Zilic BV+simul demandés RETRACTATION acq' where app_affaire_id = 7741;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] BV+simul demandés PB fille demande l''incapacité de son père' where app_affaire_id = 7761;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Poyet/Paihes vente bien acq 30/6 > financement pas sûr NON SIGNE VENDEUR ont remise en vente' where app_affaire_id = 7762;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 8839;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 8840;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] a changé d''avis' where app_affaire_id = 8845;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] SRU' where app_affaire_id = 8856;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulé' where app_affaire_id = 8864;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] CI V+A' where app_affaire_id = 8868;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulée' where app_affaire_id = 8917;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] rétractation écrite' where app_affaire_id = 8925;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] pb financement' where app_affaire_id = 9359;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation' where app_affaire_id = 9362;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 9896;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 27/11 AVNT DB14/11 🅿650K 2a' where app_affaire_id = 9965;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] CNI.V+A' where app_affaire_id = 9979;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 10015;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] rdv29/9 notaire+vend. point procs 40héritiers' where app_affaire_id = 10027;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] raison familiale' where app_affaire_id = 11110;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] SRU' where app_affaire_id = 11111;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🔴 rétractation + clôture du mandat expiré Guibert 🅿' where app_affaire_id = 11139;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] SRU' where app_affaire_id = 11501;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] renonciation acq' where app_affaire_id = 11524;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation acq' where app_affaire_id = 11596;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Auboyer/Benoist cpmis 06/5 reporté > nvelle date ?' where app_affaire_id = 11665;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Goyet/Macret REFUS DE PRET 360B+CE' where app_affaire_id = 11667;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] ! APPORTEUR 🟢 🅿105K PTZ+PTH' where app_affaire_id = 14046;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulé' where app_affaire_id = 14083;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] DP refusée 02/9 SDS / revendu + cher et +grand' where app_affaire_id = 14131;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] notaires? + rdv constructeur demandés' where app_affaire_id = 14143;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] à changé d''avis' where app_affaire_id = 14935;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] R27/2 négo voisin+CNI A' where app_affaire_id = 14964;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] financement+divorce pas prononcé+vente bien' where app_affaire_id = 15020;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 15032;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulée' where app_affaire_id = 15042;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulée' where app_affaire_id = 15073;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] PB financement + avenant demandé relancé 24/6 / annulé attente document 08/7' where app_affaire_id = 15155;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 30/11 🔴 suite Mise en demeure DB28/8 🅿125K 25a' where app_affaire_id = 15854;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🔴 🅿refusé' where app_affaire_id = 15901;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulé' where app_affaire_id = 15914;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation acq' where app_affaire_id = 15915;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 16046;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 16096;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation ecrite' where app_affaire_id = 16169;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] perte d''emploi' where app_affaire_id = 16170;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] PB combles 09/12 - cpmis30/10 annulé Me Giraud<procs' where app_affaire_id = 16182;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] BDH - refus prêt SCI > redepot de dossier en nom REFUS CA non conforme - ne passera pas d''après Laurent' where app_affaire_id = 16191;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 16251;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 16298;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 16305;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] ANNULE' where app_affaire_id = 16327;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] ❗ pb après vente > LITIGE > Hordot' where app_affaire_id = 16787;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 01/12 rdv V+Guy+Stéph. DB30/10 - CI Philippe, Max et Serge Jay manquantes' where app_affaire_id = 16792;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 16833;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Giraud/BDH ADP+DPC 22/4' where app_affaire_id = 16880;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation écrite' where app_affaire_id = 17011;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] raison familiale' where app_affaire_id = 17203;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] SRU' where app_affaire_id = 17209;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] R22/2 CNI V+A' where app_affaire_id = 17215;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation écrite' where app_affaire_id = 17226;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulée' where app_affaire_id = 17291;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulée' where app_affaire_id = 17301;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] renégo déclassement terrain' where app_affaire_id = 17366;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] DPE-F + absence de gge' where app_affaire_id = 17377;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] notaire? BVok diag+spanc à reactualiser' where app_affaire_id = 17401;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] en attente renégociation 220 000€' where app_affaire_id = 17422;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Dumas  - simul et dossier + long : projet agricole' where app_affaire_id = 17431;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 17433;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Rocher/Perrier délégation PLAINE - offre au prix - devis DIAG autre association proprio Rocher s''en occupe relancé 16/3+24/3> ACQ attente retractation ecrite' where app_affaire_id = 17567;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] diags 6/10 + diag mérule / cpmis tournant VENDproc ACQrdv' where app_affaire_id = 17635;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus PC' where app_affaire_id = 19086;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus banque' where app_affaire_id = 19095;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulation écrite' where app_affaire_id = 19102;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 19113;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 07/12 AVNT B. Rocher Dumas DB17/12>30/1 🅿140K 15a' where app_affaire_id = 19415;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 19456;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Dumas route + absence terrain' where app_affaire_id = 19472;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus banque' where app_affaire_id = 19512;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation' where app_affaire_id = 19561;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus banque' where app_affaire_id = 19619;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢 ❗ pb assainissement + humidité' where app_affaire_id = 19634;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 19657;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Simonet BVx ADP+dPC' where app_affaire_id = 20073;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 20077;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] CUb négatif redéposé 25/3+2mois > négatif à nouveau 27/4> attente décision ACQ' where app_affaire_id = 20088;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] copie16/4 CNI V+A' where app_affaire_id = 20267;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 20296;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus PC' where app_affaire_id = 21598;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 2 Refus prêt' where app_affaire_id = 22008;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] bien ACQ pas vendu+ DIVORCE' where app_affaire_id = 22024;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢 🏡+🅿189K 25a' where app_affaire_id = 23009;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] plus 30.000€ budget cons. /PA obligatoire pour cpmis + étude hydraulique' where app_affaire_id = 23037;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] pb banque CA + sté acq' where app_affaire_id = 23355;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation acq' where app_affaire_id = 23447;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 30/11 conf. V03/12 DB11/12 (2°avnt) 🅿260K 15a  Lot 7' where app_affaire_id = 23881;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] pb DP+annulation zone agricole cf suivi 17388' where app_affaire_id = 23893;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulé' where app_affaire_id = 24008;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] devis demolition 40000€' where app_affaire_id = 24121;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] annulée' where app_affaire_id = 24165;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] trop de travaux' where app_affaire_id = 24168;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 2 refus de prêt' where app_affaire_id = 24188;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] trop de travaux' where app_affaire_id = 24297;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Latour BV+simul demandés' where app_affaire_id = 24335;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] ODP relancé 23/6/ retractation PUA délais tutelle + SAFER trop longs' where app_affaire_id = 24512;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retard ODP+ASS+PTZ vente FEVRIER' where app_affaire_id = 24588;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] puits + mérule' where app_affaire_id = 24610;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 08/9 notaire ACQ veut remise en eau piscine VEND non> Marion leur a demandé de signé en l''état attente réponse' where app_affaire_id = 24652;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] renonciation acq' where app_affaire_id = 25742;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🔴 🅿+PC' where app_affaire_id = 25839;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation acq' where app_affaire_id = 25867;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 2 refus de prêt' where app_affaire_id = 25877;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation écrite + nvelle offre nvl acq' where app_affaire_id = 25880;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 25965;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢 🅿64K-PTZ+20K-2%+87K-3.5% 25a' where app_affaire_id = 25970;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation écrite' where app_affaire_id = 26016;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus prêt' where app_affaire_id = 26072;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] trop de travaux' where app_affaire_id = 26076;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] trop de travaux' where app_affaire_id = 26603;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation SRU' where app_affaire_id = 26605;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] V directe' where app_affaire_id = 27096;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] hypo+dette constructeur' where app_affaire_id = 27101;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 27143;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation écrite' where app_affaire_id = 27145;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] scierie à proximité' where app_affaire_id = 27170;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation SRU' where app_affaire_id = 27178;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] trop de travaux' where app_affaire_id = 27243;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] décision Acq>ne répond plus' where app_affaire_id = 27247;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢 🅿75K+PTZ N. Coudert' where app_affaire_id = 27285;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] PB servitude + divers éléments' where app_affaire_id = 27332;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus de prêt' where app_affaire_id = 27338;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Labidoire BVok att. RETRACTATION  écrite >maladie' where app_affaire_id = 27427;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] attente diag + simul banque = refus de pret att. écrit -4000' where app_affaire_id = 27513;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] SUCC pas réglée depuis 1990 ! recherche d''héritiers en cours + servitude voisin passage TAE' where app_affaire_id = 27528;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] Lemaitre PB liquidation judiciaire VEND + annulation VENTE bien ACQ suite mérule' where app_affaire_id = 27533;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢 🅿relais42K+Casden 370K' where app_affaire_id = 28135;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] financement' where app_affaire_id = 28155;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢 🅿relais 105K 2a + 138K 25a CE' where app_affaire_id = 28209;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] zone humide à préserver' where app_affaire_id = 28258;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] zone humide à préserver' where app_affaire_id = 28263;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] ACQ se retractent REFUS CA + refus 360B' where app_affaire_id = 28294;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] PUV expirée vente annulée - att. Nico veux vendre autre terrain ACQ + récuperer mandats maisons' where app_affaire_id = 28299;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] PB Devis Coût DRAINAGE / PC+PRET' where app_affaire_id = 28301;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢 🅿relais+245K' where app_affaire_id = 28554;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢🅿150K 25a ! RETROCESSION 1000€' where app_affaire_id = 28560;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 13/01 point Sylvie att. accord ministère L. Rocher 💰' where app_affaire_id = 28569;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢  🅿+pc' where app_affaire_id = 28676;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🔴 refus prêt 🅿+pc' where app_affaire_id = 28680;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🔴🅿 refusé' where app_affaire_id = 28839;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🔴 refus de prêt' where app_affaire_id = 28881;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 27/11 ! ODP15/11vousfinancer DB15/12 (avnt) Me Rochette 🅿' where app_affaire_id = 28897;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 26/11 rdv Vente DB30/10 Me Labidoire 🏡🅿' where app_affaire_id = 28921;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 15/12 dPC30/11 OPC01/3 DB15/6 Me BDH / Me Damas 💰 18393 à archiver après vente' where app_affaire_id = 28944;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 27/11 retard dPC30/9 PC31/12 accord eau DB01/3 🏡💰 Me Chazottes-Leconte/Barre' where app_affaire_id = 28964;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢 🅿290K 25a lié vente 18711' where app_affaire_id = 28970;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢 🅿265K+144€relais G. Perret' where app_affaire_id = 28972;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 26/11 retard ODP + (V)chaudière DB14/11 🅿️78K 10A' where app_affaire_id = 28979;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 30/11 rdv G1 + rpse PC14/11 Auboyer 🅿+pc' where app_affaire_id = 28985;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 22/01 retrait cuve fioul  DB22/2 Me Latour 💰' where app_affaire_id = 28995;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🔴🅿refusé' where app_affaire_id = 30648;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 26/11🔴 prêt vendeur ? ODP24/11 DB28/12 Me Cornu 🅿106K 25a' where app_affaire_id = 30676;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢🅿189K 25a +🏡' where app_affaire_id = 30678;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 26/11 🔴 ODP28/11 DB21/12 Guibert 🅿️161K 25a' where app_affaire_id = 30687;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢 🅿 ref. EM70300' where app_affaire_id = 30688;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 01/12 ODP01/12 BP DB15/01 Me Chomarat 🅿81K 25a' where app_affaire_id = 30691;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 30/11 devis plombier Me Argoeuves / Pougalan 🅿' where app_affaire_id = 30692;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 30/11 ODP30/11 achat18790 DB30/01 Me Labidoire 🅿25372 25a' where app_affaire_id = 30701;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 15/12 PTZ ODP15/12 + fact. chaudière + achat17383 DB30/1 Me Labidoire ref. V810062813' where app_affaire_id = 30702;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 30/11 ODP30/11 DB29/12 Me Cornu/Lancry 🅿' where app_affaire_id = 30703;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 08/12 copie C7/12 Me Chomarat 🅿+subvention Région' where app_affaire_id = 30705;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 27/11 !! copie C12/11 Me Didier 🅿+cub' where app_affaire_id = 30706;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 02/12 🚩 AVNT Laura Lhermet + rpse CIC ODP24/10 DB23/11 L. Rocher 🅿60K 15a' where app_affaire_id = 30709;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 03/12 ODP5/12 + (V)cuve + accord juge contentieux DB05/1 Me Carton' where app_affaire_id = 30714;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 01/12 ODP02/12 + factures V. DB02/01 Me Goutorbe 🅿' where app_affaire_id = 30721;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 30/11 renonciation prêt + report délai DBFEV. DB08/01 Me Brion 🅿99K 2a' where app_affaire_id = 30722;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 15/12 7j. ODP22/12 DB08/01 Me Sanial 🅿260K Hab.+gge mécanique' where app_affaire_id = 30726;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 30/11 DP + ADP30/11 ODP31/12 DB15/3 🅿150K+pc maison inachevée' where app_affaire_id = 30728;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 08/12 7j. ODP15/12 relogmt-V DB27/3 🅿 E. Pereira / départ VL Gonzalez 09sept.' where app_affaire_id = 30729;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 07/12 6j. ODP12/12 + (V)non opp.Daact  DB12/01 Labidoire 🅿109K' where app_affaire_id = 30736;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 30/11 devis ODP15/12 SAFER DB15/01 🅿 MDR bien V330062851' where app_affaire_id = 30747;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 27/11 ! ADP19/11 ODP18/01 DB20/02 Me Sanial🅿245K' where app_affaire_id = 30757;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 23/12 ADP23/12 ODP25/01 DB12/3 Chalet/Chassang46 🅿218K' where app_affaire_id = 30763;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 26/11 copie C25/11 Metay / Prebost 💰' where app_affaire_id = 30764;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 16/12 rpse CM ODP  🅿50K 11a Me Exbrayat / Sauret' where app_affaire_id = 30766;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 27/11 ADP26/11 + DP(V) ODP26/12 DB26/1 Marion/Serpantié 🅿' where app_affaire_id = 30769;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 21/12 10j. ODP31/12 DB01/2 Me Guillauma 🅿' where app_affaire_id = 30770;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 01/12 ! ADP26/11 ODP05/1 DB26/01 🅿' where app_affaire_id = 30779;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 16/12 ADP+DP ODP05/1 DP31/1 31/3 Latour/Ravel-D. 🅿' where app_affaire_id = 30791;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 18/12 🏡18/12+DPdivision DB30/1 Me Didier/Giroux69' where app_affaire_id = 30793;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 03/12 ADP03/12 ODP03/1 Vacq.18/12 DB03/2 Me Milan/Henrion 🅿+relais+🏡' where app_affaire_id = 30795;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 30/11 copie C27/11 accord du juge habilitation Sauret 💰' where app_affaire_id = 30796;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 26/11 copie C24/11 🅿 Me Poyet/Chazotte' where app_affaire_id = 30797;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 30/11 copie C27/11 Me Rimoux/Monteiro 🅿' where app_affaire_id = 30801;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 08/12 copie C07/12 Garde 🅿134K+🏠40K 19/11' where app_affaire_id = 30804;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 01/12 copie C30/11 Me Sabot 🅿' where app_affaire_id = 30808;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 02/12 DPU + Vente directe 💰gge' where app_affaire_id = 30809;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 27/11 !! copie C20/11 🅿 Me Didier/Josserand' where app_affaire_id = 30815;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 25/11 copie C24/11 Me Champelovier 💰' where app_affaire_id = 30817;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 26/11 prêt ok ? PUA SAFER DB30/4 PUV SAFER DB30/6 Me Robin' where app_affaire_id = 30818;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 08/12 copie C07/12 Me Robin 🏠' where app_affaire_id = 30820;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 09/12 copie C08/12 Me De Zan / Me Bionda 💰' where app_affaire_id = 30821;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 27/11 rdv Me Sanial 🅿+Cub' where app_affaire_id = 30824;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 09/12 copie C08/12 Me Mousset / Me Guibert 🅿' where app_affaire_id = 30825;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 02/12 rdv Me Exbrayat / Verdonnet 💰 ref. 18286' where app_affaire_id = 30826;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 14/12 ADP13/12 ODP13/1 DB13/2 Me Sauret 🅿' where app_affaire_id = 30827;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 30/11 liste materiaux + envoi Me Bougon 🅿' where app_affaire_id = 30829;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 26/11 rapport TAE + envoi Me Brisson Vente directe ? 💰 réf. 18053' where app_affaire_id = 30830;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 02/12 rdv Latour 💰' where app_affaire_id = 30836;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 26/11 sign.V Me Teyssier / Poyet 🅿' where app_affaire_id = 30837;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 01/12 rdv BDH 🅿' where app_affaire_id = 30841;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 03/12 rdv Me Martin 🅿' where app_affaire_id = 30842;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 03/12 rdv Begon 🅿' where app_affaire_id = 30843;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 03/12 rdv Borel 🅿' where app_affaire_id = 30845;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 03/12 envoi Labidoire 🅿 ! parrainage' where app_affaire_id = 30848;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] retractation écrite' where app_affaire_id = 1000142;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] refus AG division+changement d''affectation' where app_affaire_id = 1000146;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 🟢 🅿119500K' where app_affaire_id = 1000313;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] 30/11 EDD Coulaud Me Bougon 🅿 PTZ Antoine' where app_affaire_id = 1000320;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] REFUS prêt' where app_affaire_id = 1001530;
update public.app_affaire_note set texte = texte || E'\n' || '[classeur F, suivi en cours au 26/11/2026] SRU' where app_affaire_id = 1001532;
-- 5. LES AVIS (0 cases, 0 lignes neuves)
-- 6. LES CONTROLES
do $$ declare n int; begin
  select count(*) into n from public.app_affaire_note where ecrit_par = 'classeur:3bisB:2026-11-27';
  if n <> 57 then raise exception '⛔ controle : % notes neuves (attendu 57)', n; end if;
  select count(*) into n from public.app_affaire_note where texte like '%[classeur F, suivi en cours au 26/11/2026]%';
  if n <> 342 then raise exception '⛔ controle : % notes portent le paragraphe (attendu 342)', n; end if;
  select count(*) into n from public.app_affaire_note;
  if n <> 4628 then raise exception '⛔ controle : % notes en tout (attendu 4628)', n; end if;
  select count(*) into n from public.app_affaire_note a join public.app_affaire_note_avant_3bisB_20261127 s using (app_affaire_id)
   where left(a.texte, length(s.texte)) <> s.texte;
  if n <> 0 then raise exception '⛔ controle : % note(s) dont le texte d''avant n''est plus intact', n; end if;
  select count(*) into n from public.app_classeur_avis where ecrit_par = 'classeur:3bisB:2026-11-27';
  if n <> 0 then raise exception '⛔ controle : % lignes d''avis marquees (attendu 0)', n; end if;
  select count(*) into n from _saisies_avant s join public.app_affaire_note a using (app_affaire_id)
   where md5(a.texte) = s.m and a.origine = 'saisie';
  if n <> 9 then raise exception '⛔ controle : % des 9 notes saisies seulement sont intactes', n; end if;
  raise notice '✅ lot 3 bis B : 57 notes neuves, 285 paragraphes, 0 lignes d''avis touchees';
end $$;
do $$ begin raise exception 'A BLANC LOT 3 BIS B VERT -- RIEN N''EST ECRIT'; end $$;
