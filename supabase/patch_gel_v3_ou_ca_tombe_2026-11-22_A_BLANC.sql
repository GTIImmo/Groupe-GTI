-- ════════════════════════════════════════════════════════════════════════════════════════════════
-- LE GEL V3 -- « OU CA TOMBE », A PART RESTREINTE AUX 20                                     22/11/2026
-- ════════════════════════════════════════════════════════════════════════════════════════════════
-- ⭐ REPETITION A BLANC : le patch ENTIER, puis ROLLBACK -- il ne laisse rien.
-- ⛔ DORMANT : il ne se joue qu'avec le « vas-y » explicite de Frederic, dans la conversation.
-- ⛔⛔ IL PORTE SON `commit;` : joue « pour voir », IL SE COMMITE. La repetition a blanc est un AUTRE fichier
--   (..._A_BLANC.sql, qui finit par rollback).
-- SOURCE : phase2/checks/temps12_v3_fabriquer_2026-11-22.py (etapes calcul, maisons, rejeu, gestes, patch) --
--   ne pas le retoucher a la main. « Ou ca tombe » refait sur la base du 22/11 : 0 ligne dont le sort change.
-- CE QU'IL FAIT : 29 liens RETIRES . 14 liens AJOUTES . le gel passe de 12820 a 12805.
--   . une ligne tient les pieces que la PREUVE INTERNE lui donne (date au jour exact, ou prix + honoraires) ;
--   . les 20 pieces dont la place bouge une etiquette sont lachees (A PART) ; les 20 neutres ATTENDENT ou elles
--     sont (le gel les garde quand il les donne deja a la ligne de leur morceau) ;
--   . UN LIEN PAR ROLE : le role « offre » tient l'offre ACCEPTEE (sa convention du 20/11) ; une copie C5 qui tient
--     deja un role n'est pas doublee (les copies se retirent a part) ;
--   . les deux morceaux a DEUX de ses lignes (biens 9748 et 41467) ne sont PAS touches (son verrou, point 3).
-- CE QU'IL NE FAIT PAS : il ne touche NI le chainage (c'est le fichier des detachements V3 + G2, sur le meme
--   « vas-y »), NI les ecritures rapatriees (repartitions, factures, reglements, notes : mesurees, a part), NI Hektor.
-- RETOUR ARRIERE : patch_gel_v3_ou_ca_tombe_2026-11-22_INVERSE.sql
-- CONTROLE       : patch_gel_v3_ou_ca_tombe_2026-11-22_REPETITION.sql (lecture seule)
-- ════════════════════════════════════════════════════════════════════════════════════════════════
begin;

-- ── ① LA GARDE : le gel est EXACTEMENT celui que le calcul a lu ─────────────────────────────────
do $$
declare n int; emp text; manque int; cible_ko int; deja int;
begin
  select count(*), md5(string_agg(id_unique||':'||app_affaire_id||':'||role, ','
                                  order by id_unique collate "C", app_affaire_id))
    into n, emp from app_classeur_lien;
  if n <> 12820 or emp <> 'f63e54db7675531ec44641ba7abefed1' then
    raise exception '⛔ garde : le gel a bouge (% liens, empreinte %) -- rien n''est ecrit', n, emp;
  end if;
  if to_regclass('public.app_classeur_lien_avant_v3_20261122') is not null then
    raise exception '⛔ garde : la sauvegarde app_classeur_lien_avant_v3_20261122 existe deja -- ce patch a-t-il deja ete joue ?';
  end if;
  select count(*) into manque from (values
    ('1D7EIYKW', 27512, 'compromis'),
    ('2FOH8HE4', 4649, 'compromis'),
    ('2HOL5ISX', 27134, 'compromis'),
    ('305KAY9W', 24124, 'offre'),
    ('3308P0UX', 4480, 'compromis'),
    ('5QE9107L', 20088, 'compromis'),
    ('721e650c', 3678, 'offre'),
    ('9DK01H85', 7710, 'compromis'),
    ('AHKQI7MX', 1059, 'compromis'),
    ('C0HXVVCW', 28116, 'compromis'),
    ('E1WD68ZB', 20264, 'compromis'),
    ('E9GL6MUS', 11415, 'offre'),
    ('GYGF5F1X', 4669, 'compromis'),
    ('HUY49KEC', 3741, 'vente'),
    ('IEYXREWQ', 27141, 'vente'),
    ('P252U1JH', 4126, 'compromis'),
    ('PCDZXTIY', 4533, 'compromis'),
    ('PYG8JZ0C', 4327, 'compromis'),
    ('QJQ9M4OF', 17366, 'offre'),
    ('QV5AYD2K', 4560, 'compromis'),
    ('R0JRVFDC', 16382, 'offre'),
    ('RGCEC677', 4542, 'compromis'),
    ('SHN6RKDI', 26613, 'compromis'),
    ('TND2I31B', 4621, 'compromis'),
    ('V3FO5NDA', 19131, 'compromis'),
    ('V3FO5NDA', 19133, 'vente'),
    ('X2714E92', 17024, 'compromis'),
    ('YATQOEPB', 16342, 'compromis'),
    ('d2108609', 21520, 'compromis')
  ) v(id_unique, app_affaire_id, role)
  where not exists (select 1 from app_classeur_lien l where l.id_unique = v.id_unique
                       and l.app_affaire_id = v.app_affaire_id and l.role = v.role);
  if manque <> 0 then raise exception '⛔ garde : % lien(s) a retirer introuvable(s)', manque; end if;
  select count(*) into cible_ko from (values
    ('6FQO29C8', 19131, 'compromis'),
    ('6FQO29C8', 19133, 'vente'),
    ('AYIHPHF5', 14115, 'vente'),
    ('D9MMB7OU', 17366, 'offre'),
    ('DN5U3GER', 7450, 'compromis'),
    ('H6CTRVR6', 11415, 'offre'),
    ('HHQZC2QP', 4649, 'compromis'),
    ('IEYXREWQ', 27134, 'compromis'),
    ('JAW5U9OF', 17024, 'compromis'),
    ('N9J2533O', 4651, 'compromis'),
    ('Z3DYDC4X', 14113, 'offre'),
    ('ZGNIYS1Z', 16342, 'compromis'),
    ('ZV3QRSJG', 17131, 'compromis'),
    ('c08ff7cb', 3678, 'offre')
  ) v(id_unique, app_affaire_id, role)
  left join app_affaire_ledger a on a.app_affaire_id = v.app_affaire_id
  where a.app_affaire_id is null or a.kind <> v.role;
  if cible_ko <> 0 then raise exception '⛔ garde : % cible(s) absente(s) du registre ou d''un autre genre', cible_ko; end if;
  select count(*) into deja from (values
    ('6FQO29C8', 19131, 'compromis'),
    ('6FQO29C8', 19133, 'vente'),
    ('AYIHPHF5', 14115, 'vente'),
    ('D9MMB7OU', 17366, 'offre'),
    ('DN5U3GER', 7450, 'compromis'),
    ('H6CTRVR6', 11415, 'offre'),
    ('HHQZC2QP', 4649, 'compromis'),
    ('IEYXREWQ', 27134, 'compromis'),
    ('JAW5U9OF', 17024, 'compromis'),
    ('N9J2533O', 4651, 'compromis'),
    ('Z3DYDC4X', 14113, 'offre'),
    ('ZGNIYS1Z', 16342, 'compromis'),
    ('ZV3QRSJG', 17131, 'compromis'),
    ('c08ff7cb', 3678, 'offre')
  ) v(id_unique, app_affaire_id, role)
  join app_classeur_lien l on l.app_affaire_id = v.app_affaire_id and l.id_unique <> v.id_unique
  where not exists (select 1 from (values
    ('1D7EIYKW', 27512, 'compromis'),
    ('2FOH8HE4', 4649, 'compromis'),
    ('2HOL5ISX', 27134, 'compromis'),
    ('305KAY9W', 24124, 'offre'),
    ('3308P0UX', 4480, 'compromis'),
    ('5QE9107L', 20088, 'compromis'),
    ('721e650c', 3678, 'offre'),
    ('9DK01H85', 7710, 'compromis'),
    ('AHKQI7MX', 1059, 'compromis'),
    ('C0HXVVCW', 28116, 'compromis'),
    ('E1WD68ZB', 20264, 'compromis'),
    ('E9GL6MUS', 11415, 'offre'),
    ('GYGF5F1X', 4669, 'compromis'),
    ('HUY49KEC', 3741, 'vente'),
    ('IEYXREWQ', 27141, 'vente'),
    ('P252U1JH', 4126, 'compromis'),
    ('PCDZXTIY', 4533, 'compromis'),
    ('PYG8JZ0C', 4327, 'compromis'),
    ('QJQ9M4OF', 17366, 'offre'),
    ('QV5AYD2K', 4560, 'compromis'),
    ('R0JRVFDC', 16382, 'offre'),
    ('RGCEC677', 4542, 'compromis'),
    ('SHN6RKDI', 26613, 'compromis'),
    ('TND2I31B', 4621, 'compromis'),
    ('V3FO5NDA', 19131, 'compromis'),
    ('V3FO5NDA', 19133, 'vente'),
    ('X2714E92', 17024, 'compromis'),
    ('YATQOEPB', 16342, 'compromis'),
    ('d2108609', 21520, 'compromis')
    ) r(id_unique, app_affaire_id, role)
    where r.id_unique = l.id_unique and r.app_affaire_id = l.app_affaire_id);
  if deja <> 0 then raise exception '⛔ garde : % cible(s) tenue(s) par une autre ligne qui ne la lache pas', deja; end if;
end $$;

-- ── ② LA SAUVEGARDE DATEE, FERMEE DES SA NAISSANCE ─────────────────────────────────────────────
create table app_classeur_lien_avant_v3_20261122 as select * from app_classeur_lien;
revoke all on app_classeur_lien_avant_v3_20261122 from public, anon, authenticated;
alter table app_classeur_lien_avant_v3_20261122 enable row level security;

-- ── ③ RETIRER (29) ──────────────────────────────────────────────────────────────────────
delete from app_classeur_lien l
 using (values
    ('1D7EIYKW', 27512, 'compromis'),
    ('2FOH8HE4', 4649, 'compromis'),
    ('2HOL5ISX', 27134, 'compromis'),
    ('305KAY9W', 24124, 'offre'),
    ('3308P0UX', 4480, 'compromis'),
    ('5QE9107L', 20088, 'compromis'),
    ('721e650c', 3678, 'offre'),
    ('9DK01H85', 7710, 'compromis'),
    ('AHKQI7MX', 1059, 'compromis'),
    ('C0HXVVCW', 28116, 'compromis'),
    ('E1WD68ZB', 20264, 'compromis'),
    ('E9GL6MUS', 11415, 'offre'),
    ('GYGF5F1X', 4669, 'compromis'),
    ('HUY49KEC', 3741, 'vente'),
    ('IEYXREWQ', 27141, 'vente'),
    ('P252U1JH', 4126, 'compromis'),
    ('PCDZXTIY', 4533, 'compromis'),
    ('PYG8JZ0C', 4327, 'compromis'),
    ('QJQ9M4OF', 17366, 'offre'),
    ('QV5AYD2K', 4560, 'compromis'),
    ('R0JRVFDC', 16382, 'offre'),
    ('RGCEC677', 4542, 'compromis'),
    ('SHN6RKDI', 26613, 'compromis'),
    ('TND2I31B', 4621, 'compromis'),
    ('V3FO5NDA', 19131, 'compromis'),
    ('V3FO5NDA', 19133, 'vente'),
    ('X2714E92', 17024, 'compromis'),
    ('YATQOEPB', 16342, 'compromis'),
    ('d2108609', 21520, 'compromis')
 ) v(id_unique, app_affaire_id, role)
 where l.id_unique = v.id_unique and l.app_affaire_id = v.app_affaire_id and l.role = v.role;

-- ── ④ AJOUTER (14) ───────────────────────────────────────────────────────────────────────
insert into app_classeur_lien
  (ligne_classeur, app_affaire_id, role, confiance, preuves, etage, gele_le, gele_par, id_unique)
values
    (589, 19131, 'compromis', 'sûre', 2, 'preuve interne 20-22/11', now(), 'v3_ou_ca_tombe_2026-11-22', '6FQO29C8'),
    (589, 19133, 'vente', 'sûre', 2, 'preuve interne 20-22/11', now(), 'v3_ou_ca_tombe_2026-11-22', '6FQO29C8'),
    (1932, 14115, 'vente', 'sûre', 2, 'preuve interne 20-22/11', now(), 'v3_ou_ca_tombe_2026-11-22', 'AYIHPHF5'),
    (3735, 17366, 'offre', 'sûre', 2, 'preuve interne 20-22/11', now(), 'v3_ou_ca_tombe_2026-11-22', 'D9MMB7OU'),
    (4037, 7450, 'compromis', 'sûre', 2, 'preuve interne 20-22/11', now(), 'v3_ou_ca_tombe_2026-11-22', 'DN5U3GER'),
    (1841, 11415, 'offre', 'sûre', 2, 'preuve interne 20-22/11', now(), 'v3_ou_ca_tombe_2026-11-22', 'H6CTRVR6'),
    (3999, 4649, 'compromis', 'sûre', 2, 'preuve interne 20-22/11', now(), 'v3_ou_ca_tombe_2026-11-22', 'HHQZC2QP'),
    (3530, 27134, 'compromis', 'sûre', 2, 'preuve interne 20-22/11', now(), 'v3_ou_ca_tombe_2026-11-22', 'IEYXREWQ'),
    (3731, 17024, 'compromis', 'sûre', 2, 'preuve interne 20-22/11', now(), 'v3_ou_ca_tombe_2026-11-22', 'JAW5U9OF'),
    (4066, 4651, 'compromis', 'sûre', 2, 'preuve interne 20-22/11', now(), 'v3_ou_ca_tombe_2026-11-22', 'N9J2533O'),
    (3990, 14113, 'offre', 'sûre', 2, 'preuve interne 20-22/11', now(), 'v3_ou_ca_tombe_2026-11-22', 'Z3DYDC4X'),
    (3912, 16342, 'compromis', 'sûre', 2, 'preuve interne 20-22/11', now(), 'v3_ou_ca_tombe_2026-11-22', 'ZGNIYS1Z'),
    (3954, 17131, 'compromis', 'sûre', 2, 'preuve interne 20-22/11', now(), 'v3_ou_ca_tombe_2026-11-22', 'ZV3QRSJG'),
    (4284, 3678, 'offre', 'sûre', 2, 'preuve interne 20-22/11', now(), 'v3_ou_ca_tombe_2026-11-22', 'c08ff7cb');

-- ── ⑤ LE CONTROLE, DANS LA MEME TRANSACTION ───────────────────────────────────────────────────
do $$
declare n int; doubles int; deux_roles int; poses int; restes int; garde int; temoin int;
begin
  select count(*) into n from app_classeur_lien;
  if n <> 12805 then raise exception '⛔ le gel porte % liens, attendu 12805', n; end if;
  select count(*) into doubles from (select app_affaire_id from app_classeur_lien
                                      group by 1 having count(distinct id_unique) > 1) x;
  if doubles <> 0 then raise exception '⛔ % transaction(s) prises par deux lignes', doubles; end if;
  select count(*) into deux_roles from (select id_unique, role from app_classeur_lien
                                         group by 1, 2 having count(*) > 1) x;
  if deux_roles <> 0 then raise exception '⛔ % ligne(s) a deux liens pour un meme role', deux_roles; end if;
  select count(*) into poses from app_classeur_lien where gele_par = 'v3_ou_ca_tombe_2026-11-22';
  if poses <> 14 then raise exception '⛔ % lien(s) poses, attendu 14', poses; end if;
  select count(*) into restes from app_classeur_lien l join (values
    ('1D7EIYKW', 27512, 'compromis'),
    ('2FOH8HE4', 4649, 'compromis'),
    ('2HOL5ISX', 27134, 'compromis'),
    ('305KAY9W', 24124, 'offre'),
    ('3308P0UX', 4480, 'compromis'),
    ('5QE9107L', 20088, 'compromis'),
    ('721e650c', 3678, 'offre'),
    ('9DK01H85', 7710, 'compromis'),
    ('AHKQI7MX', 1059, 'compromis'),
    ('C0HXVVCW', 28116, 'compromis'),
    ('E1WD68ZB', 20264, 'compromis'),
    ('E9GL6MUS', 11415, 'offre'),
    ('GYGF5F1X', 4669, 'compromis'),
    ('HUY49KEC', 3741, 'vente'),
    ('IEYXREWQ', 27141, 'vente'),
    ('P252U1JH', 4126, 'compromis'),
    ('PCDZXTIY', 4533, 'compromis'),
    ('PYG8JZ0C', 4327, 'compromis'),
    ('QJQ9M4OF', 17366, 'offre'),
    ('QV5AYD2K', 4560, 'compromis'),
    ('R0JRVFDC', 16382, 'offre'),
    ('RGCEC677', 4542, 'compromis'),
    ('SHN6RKDI', 26613, 'compromis'),
    ('TND2I31B', 4621, 'compromis'),
    ('V3FO5NDA', 19131, 'compromis'),
    ('V3FO5NDA', 19133, 'vente'),
    ('X2714E92', 17024, 'compromis'),
    ('YATQOEPB', 16342, 'compromis'),
    ('d2108609', 21520, 'compromis')
  ) v(id_unique, app_affaire_id, role) on l.id_unique = v.id_unique and l.app_affaire_id = v.app_affaire_id;
  if restes <> 0 then raise exception '⛔ % lien(s) a retirer encore presents', restes; end if;
  select count(*) into garde from app_classeur_lien_avant_v3_20261122;
  if garde <> 12820 then raise exception '⛔ sauvegarde : % au lieu de 12820', garde; end if;
  select count(*) into temoin from app_classeur_lien l
    join app_classeur_lien_avant_v3_20261122 s using (id_unique, app_affaire_id)
   where (l.role, l.confiance, l.preuves, l.etage, l.gele_par, l.ligne_classeur, l.gele_le)
         is distinct from (s.role, s.confiance, s.preuves, s.etage, s.gele_par, s.ligne_classeur, s.gele_le);
  if temoin <> 0 then raise exception '⛔ temoin inverse : % lien(s) non vise(s) ont change', temoin; end if;
  raise notice '✅ gel V3 : -29 +14 = 12805 liens, exclusivite tenue, un lien par role, voisins intacts.';
end $$;

rollback;
