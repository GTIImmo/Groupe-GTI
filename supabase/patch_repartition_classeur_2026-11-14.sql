-- RAPATRIEMENT DES POURCENTAGES DU CLASSEUR -> app_affaire_repartition
-- Depose le 2026-11-14 par phase2/checks/rapatrier_repartition_classeur.py
-- 30 chaines, 65 lignes. Regle : ENTREE 50 + SORTIE 50.
-- Les chaines portant origine='saisie' ont ete ECARTEES en amont.
-- ATTENTION : ce fichier porte son propre commit. Le jouer, c'est ecrire.

begin;

-- (1) SAUVEGARDE DATEE, avant le premier geste (regle du projet).
create table if not exists public.app_affaire_repartition_avant_classeur_20261114 as
  select * from public.app_affaire_repartition where false;
insert into public.app_affaire_repartition_avant_classeur_20261114
  select r.* from public.app_affaire_repartition r
  where r.app_chaine_id in (21, 117, 1265, 3587, 4328, 4500, 4533, 4560, 4621, 4669, 4770, 6156, 6433, 7645, 11186, 11355, 17650, 19073, 21964, 22007, 22207, 22255, 23412, 23802, 24588, 26018, 26614, 27100, 27554, 27678);

-- (2) LE GARDE-FOU, en base et pas seulement dans le script.
do $$
declare n int;
begin
  select count(*) into n from public.app_affaire_repartition
   where origine = 'saisie' and app_chaine_id in (21, 117, 1265, 3587, 4328, 4500, 4533, 4560, 4621, 4669, 4770, 6156, 6433, 7645, 11186, 11355, 17650, 19073, 21964, 22007, 22207, 22255, 23412, 23802, 24588, 26018, 26614, 27100, 27554, 27678);
  if n > 0 then
    raise exception 'ARRET : % ligne(s) de SAISIE humaine dans le perimetre', n;
  end if;
end $$;

-- (3) REMPLACEMENT : on retire l'ancienne repartition de ces chaines...
delete from public.app_affaire_repartition
 where app_chaine_id in (21, 117, 1265, 3587, 4328, 4500, 4533, 4560, 4621, 4669, 4770, 6156, 6433, 7645, 11186, 11355, 17650, 19073, 21964, 22007, 22207, 22255, 23412, 23802, 24588, 26018, 26614, 27100, 27554, 27678);

-- ... puis on pose celle du classeur.
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id,
   nom_au_moment, pourcentage, origine, ecrit_par)
values
  (21, 1100105, 'entree', 1, '29', 'LUCILLE FORLICO', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (21, 1100105, 'sortie', 1, '30', 'MELANIE LEGRAND', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (117, 10140, 'entree', 1, '29', 'LUCILLE FORLICO', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (117, 10140, 'sortie', 1, '30', 'MELANIE LEGRAND', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (1265, 1358656, 'entree', 1, '168', 'BENJAMIN TRIOLLIER', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (1265, 1358656, 'sortie', 1, '168', 'BENJAMIN TRIOLLIER', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (3587, 1390709, 'entree', 1, '31', 'SIMON DECHAUD', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (3587, 1390709, 'sortie', 1, '32', 'CHRISTELE GENTES', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (4328, 1392032, 'entree', 1, '238', 'Joel CHAMPAGNAC', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (4328, 1392032, 'sortie', 1, '238', 'Joel CHAMPAGNAC', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (4500, 1392271, 'entree', 1, '238', 'Joel CHAMPAGNAC', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (4500, 1392271, 'sortie', 1, '167', 'SOPHIE DEBULOIS', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (4533, 1392378, 'entree', 1, '238', 'Joel CHAMPAGNAC', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (4533, 1392378, 'sortie', 1, '167', 'SOPHIE DEBULOIS', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (4560, 1392417, 'entree', 1, '238', 'Joel CHAMPAGNAC', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (4560, 1392417, 'sortie', 1, '238', 'Joel CHAMPAGNAC', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (4621, 1392482, 'entree', 1, '238', 'Joel CHAMPAGNAC', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (4621, 1392482, 'sortie', 1, '238', 'Joel CHAMPAGNAC', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (4669, 1336102, 'entree', 1, '167', 'SOPHIE DEBULOIS', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (4669, 1336102, 'sortie', 1, '167', 'SOPHIE DEBULOIS', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (4770, 1336289, 'entree', 1, '238', 'Joel CHAMPAGNAC', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (4770, 1336289, 'sortie', 1, '82', 'CELINE HERITIER', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (6156, 1338037, 'entree', 1, '36', 'SANDRINE DELAVAUD', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (6156, 1338037, 'sortie', 1, '35', 'FREDERIQUE JORAND', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (6433, 1338682, 'entree', 1, '149', 'LAURE CAVARD', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (6433, 1338682, 'sortie', 1, '149', 'LAURE CAVARD', 25, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (6433, 1338682, 'sortie', 2, '52', 'VIVIEN BERGER', 25, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (7645, 1342051, 'entree', 1, '42', 'DYLAN JOURGET', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (7645, 1342051, 'sortie', 1, '42', 'DYLAN JOURGET', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (11186, 1350731, 'entree', 1, '190', 'MAGALI DIMARIA MARIA', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (11186, 1350731, 'sortie', 1, '190', 'MAGALI DIMARIA MARIA', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (11355, 1351161, 'entree', 1, '48', 'LUCAS VINCENT VINCENTLUCAS GONZALEZ', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (11355, 1351161, 'sortie', 1, '48', 'LUCAS VINCENT VINCENTLUCAS GONZALEZ', 25, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (11355, 1351161, 'sortie', 2, '30', 'MELANIE LEGRAND', 25, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (17650, 1366045, 'entree', 1, '67', 'SYLVIE TEYSSONNIER', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (17650, 1366045, 'sortie', 1, '235', 'JEAN VALLA', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (19073, 1368398, 'entree', 1, '68', 'Aline VALETTE', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (19073, 1368398, 'sortie', 1, '67', 'SYLVIE TEYSSONNIER', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (21964, 1373083, 'entree', 1, '73', 'CLAUDIE FERNANDEZ', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (21964, 1373083, 'sortie', 1, '73', 'CLAUDIE FERNANDEZ', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (22007, 1373249, 'entree', 1, '148', 'FLORENCE CATTIAUX', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (22007, 1373249, 'sortie', 1, '148', 'FLORENCE CATTIAUX', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (22207, 1373641, 'entree', 1, '199', 'MORGANE SANGUIN', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (22207, 1373641, 'sortie', 1, '199', 'MORGANE SANGUIN', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (22255, 1373754, 'entree', 1, '199', 'MORGANE SANGUIN', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (22255, 1373754, 'sortie', 1, '199', 'MORGANE SANGUIN', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (23412, 1375771, 'entree', 1, '178', 'Lucie DECHANDON', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (23412, 1375771, 'sortie', 1, '178', 'Lucie DECHANDON', 25, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (23412, 1375771, 'sortie', 2, '227', 'STEPHANE DESOUSA', 25, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (23802, 1376548, 'entree', 1, '75', 'NICOLAS RAYNAUD', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (23802, 1376548, 'sortie', 1, '75', 'NICOLAS RAYNAUD', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (24588, 1377798, 'entree', 1, '67', 'SYLVIE TEYSSONNIER', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (24588, 1377798, 'sortie', 1, '67', 'SYLVIE TEYSSONNIER', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (26018, 1379959, 'entree', 1, '163', 'RAMAZAN KUS', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (26018, 1379959, 'sortie', 1, '163', 'RAMAZAN KUS', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (26614, 1382024, 'entree', 1, '79', 'TATIANA CROIZIER', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (26614, 1382024, 'sortie', 1, '79', 'TATIANA CROIZIER', 25, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (26614, 1382024, 'sortie', 2, '43', 'STEPHANIE JEOFFROY', 25, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (27100, 1383252, 'entree', 1, '81', 'NICOLAS COUDERT', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (27100, 1383252, 'sortie', 1, '81', 'NICOLAS COUDERT', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (27554, 1383822, 'entree', 1, '81', 'NICOLAS COUDERT', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (27554, 1383822, 'sortie', 1, '80', 'CHRISTINE BRAVARD', 25, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (27554, 1383822, 'sortie', 2, '82', 'CELINE HERITIER', 25, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (27678, 1383974, 'entree', 1, '80', 'CHRISTINE BRAVARD', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026'),
  (27678, 1383974, 'sortie', 1, '81', 'NICOLAS COUDERT', 50, 'classeur_reconstitue', 'rapatriement classeur 14/11/2026');

-- (4) LES CONTROLES, DANS LA MEME TRANSACTION : un faux et tout est annule.
-- ⛔⛔ ILS SONT BORNES AUX CHAINES DE CE PATCH, et c'est un defaut trouve
--   le 14/11 en relisant un patch CHIRURGICAL : compte sur toute la table,
--   « n <> 65 » voyait les 9 100 lignes deja posees la veille et le patch
--   echouait a coup sur. Un controle doit juger SA part, pas la table.
do $$
declare n int; m int;
begin
  select count(*) into n from public.app_affaire_repartition
   where origine = 'classeur_reconstitue' and app_chaine_id in (21, 117, 1265, 3587, 4328, 4500, 4533, 4560, 4621, 4669, 4770, 6156, 6433, 7645, 11186, 11355, 17650, 19073, 21964, 22007, 22207, 22255, 23412, 23802, 24588, 26018, 26614, 27100, 27554, 27678);
  if n <> 65 then
    raise exception 'ARRET : % lignes posees au lieu de 65', n;
  end if;
  -- chaque cote doit faire exactement 50 sur chaque chaine touchee
  select count(*) into m from (
    select app_chaine_id, cote, sum(pourcentage) as s
      from public.app_affaire_repartition
     where origine = 'classeur_reconstitue' and app_chaine_id in (21, 117, 1265, 3587, 4328, 4500, 4533, 4560, 4621, 4669, 4770, 6156, 6433, 7645, 11186, 11355, 17650, 19073, 21964, 22007, 22207, 22255, 23412, 23802, 24588, 26018, 26614, 27100, 27554, 27678)
     group by 1, 2) q
   where abs(s - 50) > 0.01;
  if m > 0 then
    raise exception 'ARRET : % cote(s) ne font pas 50', m;
  end if;
  raise notice 'POSE : % lignes, tous les cotes a 50', n;
end $$;

commit;

-- RETOUR ARRIERE -- ⛔⛔ IL NE JUGE QUE SA PART.
--   Le premier jet disait « delete where origine = 'classeur_reconstitue' » TOUT COURT :
--   joue apres un patch chirurgical, il aurait efface LES 9 100 LIGNES
--   d'un lot precedent pour n'en remettre que 30 chaine(s).
--   begin;
--   delete from public.app_affaire_repartition
--    where app_chaine_id in (21, 117, 1265, 3587, 4328, 4500, 4533, 4560, 4621, 4669, 4770, 6156, 6433, 7645, 11186, 11355, 17650, 19073, 21964, 22007, 22207, 22255, 23412, 23802, 24588, 26018, 26614, 27100, 27554, 27678);
--   insert into public.app_affaire_repartition
--     select * from public.app_affaire_repartition_avant_classeur_20261114;
--   commit;
--   ⚠ La sauvegarde ne porte QUE ces chaines : apres ce retour arriere,
--     elles retrouvent EXACTEMENT leur etat d'avant, et rien d'autre ne bouge.
