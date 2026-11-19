-- RETOUR ARRIERE de patch_correction_gel_audit_v2_2026-11-19.sql -- 19/11/2026
-- ⭐ LECON 31 : un retour arriere ne juge que SA part. Il retire les 78 liens que le patch
--   a poses (gele_par = 'audit_independant_v2_2026-11-19') et remet les 45 liens qu'il avait retires, A
--   L'IDENTIQUE, depuis la sauvegarde. Il ne refuse PAS de tourner si d'autres liens ont
--   change depuis pour une autre raison : il le DIT (notice), il ne l'efface pas.
--   ⚠ Corrige le 19/11 : l'inverse du patch du 18/11 exigeait un gel ENTIER identique a la
--   sauvegarde, et aurait donc refuse de defaire apres n'importe quel autre geste legitime.
-- ⛔ Il porte son `commit;`. Il ne supprime PAS la sauvegarde.
begin;
do $$ begin
  if to_regclass('public.app_classeur_lien_avant_audit_v2_20261119') is null then
    raise exception '⛔ pas de sauvegarde : le patch n''a jamais ete joue, rien a defaire';
  end if;
end $$;
-- ① retirer SES poses
delete from app_classeur_lien where gele_par = 'audit_independant_v2_2026-11-19';
-- ② remettre SES retraits, a l'identique (toutes colonnes, depuis la sauvegarde)
insert into app_classeur_lien
  select s.* from app_classeur_lien_avant_audit_v2_20261119 s
    join (values
    ('045ecde7', 28558, 'offre'),
    ('08GV8OMZ', 6341, 'offre'),
    ('1ESJE28Q', 12952, 'compromis'),
    ('1ESJE28Q', 12953, 'offre'),
    ('3S4ZWOFK', 1001580, 'offre'),
    ('3W10AEIK', 4747, 'offre'),
    ('427UDDSF', 3648, 'offre'),
    ('427UDDSF', 3650, 'vente'),
    ('45225170', 30712, 'offre'),
    ('45225170', 1001361, 'offre'),
    ('61OW86CS', 4496, 'compromis'),
    ('739a0db1', 27195, 'compromis'),
    ('739a0db1', 1001520, 'offre'),
    ('774aa002', 11138, 'compromis'),
    ('8Q3LHGZ4', 8321, 'compromis'),
    ('8Q3LHGZ4', 8322, 'offre'),
    ('8RWTD0YX', 4385, 'compromis'),
    ('8RWTD0YX', 1001477, 'offre'),
    ('9UO5NUN6', 11958, 'offre'),
    ('A07EC3DH', 1001563, 'offre'),
    ('CITFQGOB', 16378, 'compromis'),
    ('DAMOO7OU', 23995, 'offre'),
    ('EGR8KXOL', 6554, 'compromis'),
    ('FLPUUSY3', 1876, 'offre'),
    ('KT0601S6', 24291, 'offre'),
    ('NEFHS7JI', 26395, 'compromis'),
    ('NEFHS7JI', 26397, 'offre'),
    ('OXQSBZ9V', 17427, 'compromis'),
    ('OXQSBZ9V', 17430, 'offre'),
    ('Q602VZJX', 6555, 'compromis'),
    ('R0JRVFDC', 1001542, 'compromis'),
    ('RX6J289Y', 16377, 'compromis'),
    ('SBH4QWDW', 23050, 'compromis'),
    ('TR42PT5H', 27196, 'offre'),
    ('TRJ5Y59U', 1001561, 'offre'),
    ('UTLG66LE', 1001482, 'offre'),
    ('VEP1DVQ4', 7780, 'offre'),
    ('VMWFLLW4', 1001540, 'compromis'),
    ('WJ3KA32F', 10730, 'offre'),
    ('Y51UMZHY', 19277, 'offre'),
    ('a8aaeb2b', 998, 'compromis'),
    ('a8aaeb2b', 1000, 'offre'),
    ('f1aedc01', 28967, 'offre'),
    ('fa06e4e5', 28930, 'offre'),
    ('fa06e4e5', 1001553, 'compromis')
    ) v(id_unique, app_affaire_id, role)
      on s.id_unique = v.id_unique and s.app_affaire_id = v.app_affaire_id and s.role = v.role
   where not exists (select 1 from app_classeur_lien l
                      where l.id_unique = s.id_unique and l.app_affaire_id = s.app_affaire_id);
do $$
declare restes int; revenus int; doubles int; n int; emp text; ecart int;
begin
  -- ⭐ SA PART : plus aucune de ses poses, et ses 45 retraits revenus tels qu'ils etaient
  select count(*) into restes from app_classeur_lien where gele_par = 'audit_independant_v2_2026-11-19';
  if restes <> 0 then raise exception '⛔ % pose(s) du patch encore presente(s)', restes; end if;
  select count(*) into revenus from app_classeur_lien l
    join app_classeur_lien_avant_audit_v2_20261119 s using (id_unique, app_affaire_id)
    join (values
    ('045ecde7', 28558, 'offre'),
    ('08GV8OMZ', 6341, 'offre'),
    ('1ESJE28Q', 12952, 'compromis'),
    ('1ESJE28Q', 12953, 'offre'),
    ('3S4ZWOFK', 1001580, 'offre'),
    ('3W10AEIK', 4747, 'offre'),
    ('427UDDSF', 3648, 'offre'),
    ('427UDDSF', 3650, 'vente'),
    ('45225170', 30712, 'offre'),
    ('45225170', 1001361, 'offre'),
    ('61OW86CS', 4496, 'compromis'),
    ('739a0db1', 27195, 'compromis'),
    ('739a0db1', 1001520, 'offre'),
    ('774aa002', 11138, 'compromis'),
    ('8Q3LHGZ4', 8321, 'compromis'),
    ('8Q3LHGZ4', 8322, 'offre'),
    ('8RWTD0YX', 4385, 'compromis'),
    ('8RWTD0YX', 1001477, 'offre'),
    ('9UO5NUN6', 11958, 'offre'),
    ('A07EC3DH', 1001563, 'offre'),
    ('CITFQGOB', 16378, 'compromis'),
    ('DAMOO7OU', 23995, 'offre'),
    ('EGR8KXOL', 6554, 'compromis'),
    ('FLPUUSY3', 1876, 'offre'),
    ('KT0601S6', 24291, 'offre'),
    ('NEFHS7JI', 26395, 'compromis'),
    ('NEFHS7JI', 26397, 'offre'),
    ('OXQSBZ9V', 17427, 'compromis'),
    ('OXQSBZ9V', 17430, 'offre'),
    ('Q602VZJX', 6555, 'compromis'),
    ('R0JRVFDC', 1001542, 'compromis'),
    ('RX6J289Y', 16377, 'compromis'),
    ('SBH4QWDW', 23050, 'compromis'),
    ('TR42PT5H', 27196, 'offre'),
    ('TRJ5Y59U', 1001561, 'offre'),
    ('UTLG66LE', 1001482, 'offre'),
    ('VEP1DVQ4', 7780, 'offre'),
    ('VMWFLLW4', 1001540, 'compromis'),
    ('WJ3KA32F', 10730, 'offre'),
    ('Y51UMZHY', 19277, 'offre'),
    ('a8aaeb2b', 998, 'compromis'),
    ('a8aaeb2b', 1000, 'offre'),
    ('f1aedc01', 28967, 'offre'),
    ('fa06e4e5', 28930, 'offre'),
    ('fa06e4e5', 1001553, 'compromis')
    ) v(id_unique, app_affaire_id, role) on v.id_unique = l.id_unique and v.app_affaire_id = l.app_affaire_id
   where (l.role, l.confiance, l.preuves, l.etage, l.gele_par, l.gele_le)
         is not distinct from (s.role, s.confiance, s.preuves, s.etage, s.gele_par, s.gele_le);
  if revenus <> 45 then raise exception '⛔ % lien(s) revenu(s) a l''identique sur 45', revenus; end if;
  select count(*) into doubles from (select app_affaire_id from app_classeur_lien
                                      group by 1 having count(distinct id_unique) > 1) x;
  if doubles <> 0 then raise exception '⛔ % transaction(s) prises par deux lignes apres le retour', doubles; end if;
  -- ⓘ LE RESTE DU GEL : une information, pas une condition (lecon 31)
  select count(*), md5(string_agg(id_unique||':'||app_affaire_id||':'||role, ','
                                  order by id_unique collate "C", app_affaire_id))
    into n, emp from app_classeur_lien;
  select count(*) into ecart from (
    (select id_unique, app_affaire_id, role from app_classeur_lien
     except select id_unique, app_affaire_id, role from app_classeur_lien_avant_audit_v2_20261119)
    union all
    (select id_unique, app_affaire_id, role from app_classeur_lien_avant_audit_v2_20261119
     except select id_unique, app_affaire_id, role from app_classeur_lien)) x;
  raise notice '✅ sa part est defaite : 0 pose restante, 45 retraits revenus a l''identique.';
  raise notice 'ⓘ le gel entier : % liens (sauvegarde 12787), % ecart(s) avec la sauvegarde, empreinte % (avant : 8084e535f51ba904a839bfe0bcc88a55). Un ecart ici vient d''un AUTRE geste, posterieur.', n, ecart, emp;
end $$;
commit;
