-- ===========================================================================
-- REGEL DE app_classeur_lien -- LES 9 LIGNES NEUVES DU CLASSEUR    09/11/2026
-- ===========================================================================
-- ⭐ DEJA APPLIQUE en production le 09/11/2026, avec l'accord explicite de
--   Frederic (« Oui », apres lui avoir montre la mesure). Ce fichier est la
--   TRACE ; il est rejouable sans danger (`where not exists`).
--
-- POURQUOI. Le gel est une PHOTO du 31/10. Le classeur a grossi depuis
-- (4 775 -> 4 783 lignes), et chaque ligne neuve arrive NON RELIEE. Les 9
-- lignes posees ici sont des DOSSIERS EN COURS : 7 offres d'achat et 2
-- compromis en attente, saisis entre le 30/10 et le 06/11.
--
-- ⭐ ET DEUX D'ENTRE ELLES ATTENDAIENT DEPUIS LE 31/10 : le patch de ce
--   jour-la les avait ecartees en le disant -- « 2 lignes NEUVES au classeur
--   (1a474908, cd29653f) -- NON TRAITEES ICI, c'est un autre sujet ».
--   Elles sont restees non reliees 9 jours, sans que rien ne le signale.
--   ⬜ C'est pour ca que la SENTINELLE sur les lignes non reliees reste a poser
--     (prealable 4 de A5 section 6, toujours ouvert).
--
-- LA MESURE AVANT D'ECRIRE, PAS APRES. La cascade a ete rejouee EN LECTURE
--   SEULE (`apparier_classeur.py --reparer tout`, 09/11 10:12) et comparee
--   ligne a ligne au gel de Supabase :
--     CONCORDE 4 679  .  DIVERGE 0  .  PERDUES 0  .  GAGNEES 9
--   ⭐ ZERO PERDUE ET ZERO DIVERGENTE : ce patch n'est qu'un AJOUT. Il ne
--     modifie ni ne supprime aucun lien existant -- et le controle 5 le PROUVE
--     en comparant la sauvegarde a la table dans les DEUX sens.
--
-- ⛔ NI `preuves` NI `confiance` NE SONT RECALCULES -- lecon du 29/10 :
--   recalcules, ils BAISSENT (3 001 lignes, maximum de 8 a 7). Les valeurs
--   viennent du CSV de l'apparieur.
--   ⚠ Et contrairement au 31/10, ces lignes n'ont AUCUNE ligne soeur dont
--     copier les valeurs : elles sont neuves. D'ou les valeurs explicites.
--     Leur forme a ete verifiee contre les valeurs existantes du gel AVANT
--     d'ecrire (« 1 mandat seul », « 2 mandat + acquereur », « sure ») : on ne
--     l'invente pas.
--
-- SAUVEGARDE DATEE, PRISE DANS CE PATCH, AVANT L'INSERT :
--   public.app_classeur_lien_avant_regel_20261109  (12 413 liens)
-- RETOUR ARRIERE : patch_regel_classeur_lien_2026-11-09_INVERSE.sql
--
-- ATTENDU APRES : 12 413 + 9 = 12 422 liens  .  4 679 + 9 = 4 688 lignes
-- MESURE APRES, INDEPENDAMMENT DU PATCH : 8 controles verts, dont les deux
--   temoins (0 lien d'avant modifie, 0 lien d'avant disparu).
--
-- ⚠ LA DESCENTE SUIVRA TOUTE SEULE. `pull_from_supabase.py` decouvre les tables
--   dans le schema de Supabase : `app_classeur_lien` descend sous son propre
--   nom (pas en doublure `__sb`, verifie le 09/11). Le miroir local passera
--   donc de 12 413 a 12 422 a la descente de 07:30.
--   ⛔ NE PAS LA LANCER A LA MAIN : c'est la tache la plus lourde de celles qui
--     parlent a Supabase, elle a sature l'instance les 21-22/08.
-- ===========================================================================

-- 1. LA SAUVEGARDE DATEE, AVANT TOUT GESTE
create table if not exists public.app_classeur_lien_avant_regel_20261109 as
  select * from public.app_classeur_lien;

-- 2. LES 9 LIENS. Un INSERT pur : aucun UPDATE, aucun DELETE.
insert into public.app_classeur_lien
      (ligne_classeur, app_affaire_id, role, confiance, preuves, etage,
       gele_le, gele_par, id_unique)
select v.ligne, v.affaire, v.role, v.confiance, v.preuves, v.etage,
       now(), 'regel_2026-11-09', v.id_unique
  from (values
          (4780, 30785::bigint, 'offre', 'sûre', 5::smallint, '1 mandat seul',          'cd29653f'),
          (4781, 30784::bigint, 'offre', 'sûre', 5::smallint, '2 mandat + acquéreur',   '1a474908'),
          (4782, 30786::bigint, 'offre', 'sûre', 5::smallint, '1 mandat seul',          '63790b81'),
          (4783, 30792::bigint, 'offre', 'sûre', 5::smallint, '1 mandat seul',          'b251d01e'),
          (4784, 30803::bigint, 'offre', 'sûre', 5::smallint, '1 mandat seul',          'dad56e75'),
          (4785, 30797::bigint, 'offre', 'sûre', 5::smallint, '1 mandat seul',          'f9a2b718'),
          (4786, 30796::bigint, 'offre', 'sûre', 5::smallint, '1 mandat seul',          '918d3b44'),
          (4787, 30804::bigint, 'offre', 'sûre', 5::smallint, '1 mandat seul',          '800693bd'),
          (4788, 30802::bigint, 'offre', 'sûre', 5::smallint, '1 mandat seul',          'dedeafeb')
       ) as v(ligne, affaire, role, confiance, preuves, etage, id_unique)
 where not exists (select 1 from public.app_classeur_lien x
                    where x.id_unique = v.id_unique
                      and x.app_affaire_id = v.affaire);

-- 3. LES 7 CONTROLES, DANS LA MEME TRANSACTION : si un seul est faux, TOUT TOMBE.
do $ctrl$
declare
  v_liens int; v_lignes int; v_poses int; v_sauve int;
  v_touches int; v_double int; v_manquantes int;
begin
  select count(*), count(distinct id_unique) into v_liens, v_lignes
    from public.app_classeur_lien;
  select count(*) into v_poses from public.app_classeur_lien
   where gele_par = 'regel_2026-11-09';
  select count(*) into v_sauve from public.app_classeur_lien_avant_regel_20261109;

  -- ⭐ LE TEMOIN DE NON-REGRESSION : aucune ligne D'AVANT n'a bouge.
  select count(*) into v_touches from (
      select ligne_classeur, app_affaire_id, role, confiance, preuves, etage, id_unique
        from public.app_classeur_lien_avant_regel_20261109
      except
      select ligne_classeur, app_affaire_id, role, confiance, preuves, etage, id_unique
        from public.app_classeur_lien
  ) d;

  -- l'EXCLUSIVITE : aucune affaire ne doit recevoir deux lignes de classeur
  select count(*) into v_double from (
      select app_affaire_id from public.app_classeur_lien
       group by app_affaire_id having count(distinct id_unique) > 1
  ) e;

  select count(*) into v_manquantes from (values
      ('cd29653f'),('1a474908'),('63790b81'),('b251d01e'),('dad56e75'),
      ('f9a2b718'),('918d3b44'),('800693bd'),('dedeafeb')
    ) as a(iu)
   where not exists (select 1 from public.app_classeur_lien l where l.id_unique = a.iu);

  if v_sauve <> 12413 then
    raise exception 'CONTROLE 1 ROUGE : la sauvegarde porte % liens, attendu 12 413', v_sauve;
  end if;
  if v_poses <> 9 then
    raise exception 'CONTROLE 2 ROUGE : % lien(s) pose(s), attendu 9', v_poses;
  end if;
  if v_liens <> 12422 then
    raise exception 'CONTROLE 3 ROUGE : % liens, attendu 12 422', v_liens;
  end if;
  if v_lignes <> 4688 then
    raise exception 'CONTROLE 4 ROUGE : % lignes du classeur, attendu 4 688', v_lignes;
  end if;
  if v_touches <> 0 then
    raise exception 'CONTROLE 5 ROUGE : % lien(s) D''AVANT ont change -- ce patch ne devait RIEN modifier', v_touches;
  end if;
  if v_double <> 0 then
    raise exception 'CONTROLE 6 ROUGE : % affaire(s) recoivent deux lignes de classeur', v_double;
  end if;
  if v_manquantes <> 0 then
    raise exception 'CONTROLE 7 ROUGE : % des 9 lignes visees ne sont pas reliees', v_manquantes;
  end if;

  raise notice 'LES 7 CONTROLES SONT VERTS : % liens (dont 9 neufs), % lignes, 0 lien d''avant modifie, 0 double, sauvegarde % liens',
               v_liens, v_lignes, v_sauve;
end
$ctrl$;
