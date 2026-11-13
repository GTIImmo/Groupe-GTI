-- ============================================================================
-- LE RE-GEL ADDITIF -- lots A, B et C                          13/11/2026
-- ============================================================================
-- Plan : notice/PLAN_CHANTIER_CLASSEUR_2026-10-28.md, section 1.7
-- Liste relue par Frederic : notice/REGEL_ADDITIF_A_RELIRE_2026-11-13.csv
-- Sauvegarde : public.app_classeur_lien_avant_regel_20261113
--              12 422 lignes, fidelite verifiee (0 triplet manquant)
--
-- ⛔ CE PATCH REVERIFIE TOUT EN BASE AU MOMENT DE L'ECRITURE. Il ne croit pas
--   la liste figee : entre sa fabrication et son execution, la base bouge.
--   Lecon du menage du coffre (21/10) : 365 fichiers de fiches VIVANTES avaient
--   ete sauves parce que le script reverifiait a la volee au lieu de se fier a
--   une liste preparee la veille.
--
--   A  CORRIGER    9 liens -- le gel se trompe de bien (etage « 1 mandat seul »)
--                            contre-audite depuis le CLASSEUR : pour chacun,
--                            2 noms ET 3 dates au jour exact du cote de v2
--   B  RETIRER     2 liens -- poses sur une ligne DOUBLON du classeur
--   C  AJOUTER   177 liens -- « v2 seul », >= 3 familles, transaction LIBRE
--                            (48 ecartes : transaction deja prise ailleurs)
--
-- POUR REVENIR EN ARRIERE, EN UN GESTE :
--   begin;
--     delete from public.app_classeur_lien;
--     insert into public.app_classeur_lien
--       select * from public.app_classeur_lien_avant_regel_20261113;
--   commit;
begin;

-- ------------------------------------------------------------------- LOT A
create temporary table _a(ligne int, role text, tx_gel bigint, tx_v2 bigint) on commit drop;
insert into _a values
       @@LOT_A@@;

-- Garde-fou : chaque lien a corriger doit exister TEL QU'ATTENDU, et sa cible
-- doit etre libre. Sinon on ne touche a RIEN (la transaction entiere est annulee).
do $gardeA$
declare n int;
begin
  select count(*) into n
    from _a a join public.app_classeur_lien g
      on g.ligne_classeur = a.ligne and g.role = a.role and g.app_affaire_id = a.tx_gel;
  if n <> 9 then
    raise exception 'LOT A : % liens trouves sur 9 attendus -- RIEN FAIT', n;
  end if;
  select count(*) into n
    from _a a where exists (select 1 from public.app_classeur_lien g
                             where g.app_affaire_id = a.tx_v2);
  if n <> 0 then
    raise exception 'LOT A : % transactions cibles DEJA prises -- RIEN FAIT', n;
  end if;
  select count(*) into n
    from _a a join public.app_affaire_ledger l on l.app_affaire_id = a.tx_v2;
  if n <> 9 then
    raise exception 'LOT A : % transactions cibles existent sur 9 -- RIEN FAIT', n;
  end if;
end $gardeA$;

update public.app_classeur_lien g
   set app_affaire_id = a.tx_v2,
       confiance      = 'sûre',
       etage          = 'v2 : 2 noms + 3 dates au jour (corrige le 13/11)',
       gele_le        = now(),
       gele_par       = 'regel additif 13/11 -- lot A'
  from _a a
 where g.ligne_classeur = a.ligne and g.role = a.role and g.app_affaire_id = a.tx_gel;

-- ------------------------------------------------------------------- LOT B
-- Les lignes 3818 et 4100 sont des DOUBLONS du classeur (meme mandat, meme
-- acquereur, meme date d'offre que 1397 et 2346), et le gel les a rattachees a
-- un AUTRE bien que leur jumelle. Le lien ne vaut rien dans les deux lectures.
-- ⚠ Les 4 autres groupes de doublons ne sont PAS touches : 3 n'ont deja aucun
--   lien, et 3887 porte le meme bien que sa jumelle (plausible).
delete from public.app_classeur_lien where ligne_classeur in (3818, 4100);

-- ------------------------------------------------------------------- LOT C
-- ⚠ `preuves` est un SMALLINT (mesure du 13/11), pas un texte : c'est le NOMBRE
--   de preuves. Pour v2 c'est donc le NOMBRE DE FAMILLES de temoins (3 a 6).
--   Mon premier essai y a mis une phrase -> « invalid input syntax for type
--   smallint », et la transaction a tout annule : rien n'avait ete ecrit.
create temporary table _c(ligne int, role text, tx bigint, idu text, familles smallint) on commit drop;
insert into _c values
       @@LOT_C@@;

-- Garde-fou : on n'ajoute QUE ce qui est encore libre, verifie MAINTENANT.
-- ⭐ Ces deux deletes sont le coeur du patch : ils rendent le geste sur, meme
--   si la base a bouge depuis la fabrication de la liste.
delete from _c where exists
  (select 1 from public.app_classeur_lien g where g.app_affaire_id = _c.tx);
delete from _c where exists
  (select 1 from public.app_classeur_lien g
    where g.ligne_classeur = _c.ligne and g.role = _c.role);

-- Et un plancher : si la liste fond, c'est que quelque chose a change. On le DIT.
do $gardeC$
declare n int;
begin
  select count(*) into n from _c;
  raise notice 'LOT C : % liens encore libres sur 177 prevus', n;
  if n < 150 then
    raise exception 'LOT C : plus que % liens sur 177 -- la base a bouge, RIEN FAIT', n;
  end if;
end $gardeC$;

insert into public.app_classeur_lien
  (ligne_classeur, app_affaire_id, role, confiance, preuves, etage, gele_le, gele_par, id_unique)
select c.ligne, c.tx, c.role, 'sûre',
       c.familles,   -- le nombre de familles de temoins independantes (3 a 6)
       'v2 additif (13/11) : >= 3 familles', now(),
       'regel additif 13/11 -- lot C', c.idu
  from _c c;

commit;
