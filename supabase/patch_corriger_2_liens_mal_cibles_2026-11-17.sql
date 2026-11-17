-- ═══════════════════════════════════════════════════════════════════════════
-- CORRIGER LES DEUX LIENS DU GEL QUI POINTENT LA MAUVAISE TRANSACTION
-- 17/11/2026
--
-- ⭐⭐⭐ SA DEMANDE : « il faut corriger l'erreur du regel et comprendre pourquoi ».
--   ⚠ PRECISION D'ABORD : ce n'est PAS le re-gel du 17/11 (mes 195 liens sont
--     deterministes, deduits du payload). C'est LE GEL INITIAL du 29/10,
--     `apparier_classeur.py`.
--
-- L'AUDIT A BALAYE LES 12 791 LIENS (lecon 9 : une cause structurelle se balaie
-- dans TOUTE sa famille). Resultat :
--     ✅ la date colle a l'exact                        7 986   62,4 %
--     ecart, mais aucun meilleur candidat sur le bien   4 504   35,2 %
--     pas de date au classeur pour ce role                235
--     ⚠ un candidat colle mieux                            43
--     ⛔ un candidat a ECART ZERO existe                    11
--
-- ⛔⛔ ET SUR LES 11, NEUF ETAIENT DES FAUX POSITIFS DE MON AUDIT. Il ne faut
--   JAMAIS corriger les 11 : on en aurait abime neuf.
--
--   ① HUIT sont la consequence de NOS PROPRES GESTES. Les transactions pointees
--     portent des dates du 11/11 a 19:03-19:30 et du 12/11 a 15:26-15:27 -- des
--     heures GROUPEES, donc des gestes de masse, les notres. C'est le chantier
--     « la date d'une offre refusee EST la date du refus » (1 435 offres, les
--     4 lecteurs alignes le 12/11). Le gel du 29/10 pointait LA BONNE offre ;
--     c'est SA DATE qui a change depuis. Le lien est juste, la date ne l'est plus.
--     ➡ ON NE TOUCHE A RIEN. Les corriger « pour recoller » casserait des liens
--       exacts au profit d'une coincidence de dates.
--
--   ② UN est un defaut de ma mesure : f1aedc01 porte DEUX liens (28966 et 28967),
--     un par offre du bien. Mon audit comparait celui qui colle le moins. Il n'y
--     a rien a corriger.
--
-- ⭐⭐ RESTENT DEUX VRAIS CAS -- 2 sur 12 791, soit 0,016 %. Le gel est tres sain.
--
--   A) AYIHPHF5 (ligne 1932) -> liee a 14111, alors que 14109 colle a ZERO JOUR.
--      Le classeur : compromis 17/05/2021, acquereur BLANC MOURETTE, vente
--        reglee 02/03/2022. Chez nous : 14109 = compromis du 2021-05-17 (exact).
--      ⭐ ET LA LIGNE VOISINE EXPLIQUE TOUT : Z3DYDC4X (ligne 3990) porte LE MEME
--        MANDAT 13168, le meme terrain, le meme negociateur, le meme prix -- et
--        son compromis est du 06/04/2021, ANNULE le 21/03/2021, acquereur GENOUX.
--        C'est EXACTEMENT 14111 (compromis cancelled du 2021-04-06).
--      ➡ DEUX AFFAIRES SUCCESSIVES SUR LE MEME TERRAIN : GENOUX qui tombe, puis
--        BLANC MOURETTE qui achete. L'apparieur a donne a la seconde le compromis
--        de la premiere.
--      ⛔ POURQUOI IL S'EST TROMPE, ET JE NE LE DEVINE PAS : les TROIS compromis
--        du bien portent GENOUX comme acquereur chez Hektor, donc le nom ne
--        departageait pas. Et 14111 est DANS la chaine 14109 -- l'apparieur a pris
--        une transaction de la bonne chaine, mais pas la bonne transaction.
--
--   B) fa06e4e5 -> liee a 28931 (offre du 27/07) alors que le classeur dit le
--      15/07, et que 28930 porte EXACTEMENT 2026-07-15 et est LIBRE. Deux offres
--      refusees sur le bien 62311, deux chaines distinctes.
--
-- CE QUE CE PATCH FAIT, ET C'EST LE SEUL GESTE NON ADDITIF DU CHANTIER :
--   . il DEPLACE le lien d'AYIHPHF5 : 14111 -> 14109
--   . il DONNE a Z3DYDC4X le compromis qui est le sien : 14111
--   . il DEPLACE le lien de fa06e4e5 : 28931 -> 28930
--   ⛔ La clef primaire etant (ligne_classeur + app_affaire_id), un deplacement
--     est un DELETE puis un INSERT -- pas un UPDATE.
--
-- RETOUR ARRIERE : patch_corriger_2_liens_mal_cibles_2026-11-17_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════
begin;

-- ① LA SAUVEGARDE DES TROIS LIGNES TOUCHEES -- fermee des sa naissance
drop table if exists app_classeur_lien_avant_correction_20261117;
create table app_classeur_lien_avant_correction_20261117 as
  select * from app_classeur_lien
   where id_unique in ('AYIHPHF5', 'Z3DYDC4X', 'fa06e4e5');
revoke all on table public.app_classeur_lien_avant_correction_20261117
  from public, anon, authenticated;
grant select on table public.app_classeur_lien_avant_correction_20261117 to service_role;

-- ② LE GARDE-FOU : l'etat de depart doit etre EXACTEMENT celui mesure
do $$
declare n integer;
begin
  select count(*) into n from app_classeur_lien
   where id_unique = 'AYIHPHF5' and app_affaire_id = 14111;
  if n <> 1 then raise exception '⛔ AYIHPHF5 ne pointe pas 14111 -- etat inattendu'; end if;
  select count(*) into n from app_classeur_lien where id_unique = 'Z3DYDC4X';
  if n <> 0 then raise exception '⛔ Z3DYDC4X porte deja % lien(s)', n; end if;
  select count(*) into n from app_classeur_lien
   where id_unique = 'fa06e4e5' and app_affaire_id = 28931;
  if n <> 1 then raise exception '⛔ fa06e4e5 ne pointe pas 28931'; end if;
  -- ⭐ et les deux bonnes cibles doivent etre LIBRES
  select count(*) into n from app_classeur_lien where app_affaire_id in (14109, 28930);
  if n <> 0 then raise exception '⛔ une des bonnes cibles est deja liee'; end if;
end $$;

-- ③ A) AYIHPHF5 : 14111 -> 14109
delete from app_classeur_lien where id_unique = 'AYIHPHF5' and app_affaire_id = 14111;
insert into app_classeur_lien
    (ligne_classeur, app_affaire_id, role, confiance, preuves, etage, gele_par, id_unique)
values
    (1932, 14109, 'compromis', 'sûre', 0,
     '0 corrige le 17/11 : la date colle a 0 jour',
     'correction cible 2026-11-17', 'AYIHPHF5');

-- ③ A bis) Z3DYDC4X recupere le compromis qui est le sien
insert into app_classeur_lien
    (ligne_classeur, app_affaire_id, role, confiance, preuves, etage, gele_par, id_unique)
values
    (3990, 14111, 'compromis', 'sûre', 0,
     '0 corrige le 17/11 : compromis du 06/04/2021, acquereur GENOUX',
     'correction cible 2026-11-17', 'Z3DYDC4X');

-- ③ B) fa06e4e5 : 28931 -> 28930
delete from app_classeur_lien where id_unique = 'fa06e4e5' and app_affaire_id = 28931;
insert into app_classeur_lien
    (ligne_classeur, app_affaire_id, role, confiance, preuves, etage, gele_par, id_unique)
values
    ((select ligne_classeur from app_classeur_ligne_id where id_unique = 'fa06e4e5'),
     28930, 'offre', 'sûre', 0,
     '0 corrige le 17/11 : la date colle a 0 jour',
     'correction cible 2026-11-17', 'fa06e4e5');

-- ④ LES CONTROLES
do $$
declare n integer;
begin
  -- les trois lignes pointent desormais la bonne transaction
  select count(*) into n from app_classeur_lien
   where id_unique = 'AYIHPHF5' and app_affaire_id = 14109;
  if n <> 1 then raise exception '⛔ AYIHPHF5 ne pointe pas 14109'; end if;
  select count(*) into n from app_classeur_lien
   where id_unique = 'Z3DYDC4X' and app_affaire_id = 14111;
  if n <> 1 then raise exception '⛔ Z3DYDC4X ne pointe pas 14111'; end if;
  select count(*) into n from app_classeur_lien
   where id_unique = 'fa06e4e5' and app_affaire_id = 28930;
  if n <> 1 then raise exception '⛔ fa06e4e5 ne pointe pas 28930'; end if;

  -- ⭐ les anciennes cibles ne sont plus pointees PAR CES LIGNES
  select count(*) into n from app_classeur_lien
   where (id_unique = 'AYIHPHF5' and app_affaire_id = 14111)
      or (id_unique = 'fa06e4e5' and app_affaire_id = 28931);
  if n <> 0 then raise exception '⛔ un ancien lien subsiste'; end if;

  -- ⭐⭐ LA REGLE DE FAIT TIENT : aucune transaction liee a plusieurs lignes
  select count(*) into n from (select app_affaire_id from app_classeur_lien
    group by app_affaire_id having count(distinct id_unique) > 1) s;
  if n <> 0 then raise exception '⛔ % transaction(s) liee(s) a 2 lignes', n; end if;

  -- ⭐ LE GEL GAGNE EXACTEMENT UN LIEN (2 deplaces + 1 ajoute)
  select count(*) into n from app_classeur_lien;
  if n <> 12792 then raise exception '⛔ LE GEL PORTE % liens au lieu de 12 792', n; end if;

  -- ⛔ TEMOIN INVERSE : la sentinelle du gel ne bouge pas
  select count(*) into n from app_v_classeur_lien_casse;
  if n <> 9 then raise exception '⛔ la vue des liens casses passe a % (etait 9)', n; end if;

  -- ⭐ LES 195 ET LE LIEN DE D1 SONT INTACTS : on n'a touche que 3 lignes
  select count(*) into n from app_classeur_lien
   where gele_par = 'c5 re-gel additif 2026-11-17';
  if n <> 195 then raise exception '⛔ les 195 liens du re-gel ont bouge : %', n; end if;
  select count(*) into n from app_classeur_lien where gele_par = 'd1 1.5 du 2026-11-17';
  if n <> 1 then raise exception '⛔ le lien de D1-1.5 a bouge'; end if;

  raise notice '✅ 2 liens recibles, 1 ajoute . le gel passe a 12 792 . la regle tient';
end $$;

commit;
