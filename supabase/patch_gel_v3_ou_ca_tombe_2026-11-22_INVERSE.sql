-- RETOUR ARRIERE DU GEL V3 (22/11/2026) -- il ne juge que SA part (lecon 31).
begin;
do $$
declare n int;
begin
  if to_regclass('public.app_classeur_lien_avant_v3_20261122') is null then raise exception '⛔ pas de sauvegarde app_classeur_lien_avant_v3_20261122 : le patch n''a pas ete joue'; end if;
  select count(*) into n from app_classeur_lien where gele_par = 'v3_ou_ca_tombe_2026-11-22';
  if n <> 14 then raise exception '⛔ % lien(s) du patch trouves, attendu 14 -- quelqu''un est passe apres', n; end if;
end $$;
delete from app_classeur_lien where gele_par = 'v3_ou_ca_tombe_2026-11-22';
insert into app_classeur_lien
select s.* from app_classeur_lien_avant_v3_20261122 s
  join (values
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
  ) v(id_unique, app_affaire_id, role) on s.id_unique = v.id_unique and s.app_affaire_id = v.app_affaire_id and s.role = v.role;
do $$
declare n int; emp text;
begin
  select count(*), md5(string_agg(id_unique||':'||app_affaire_id||':'||role, ','
                                  order by id_unique collate "C", app_affaire_id)) into n, emp from app_classeur_lien;
  if n <> 12820 or emp <> 'f63e54db7675531ec44641ba7abefed1' then raise exception '⛔ inverse : le gel ne revient pas a l''etat d''avant (% %)', n, emp; end if;
  raise notice '✅ gel revenu a 12820 liens, empreinte d''avant. La sauvegarde app_classeur_lien_avant_v3_20261122 est gardee.';
end $$;
commit;
