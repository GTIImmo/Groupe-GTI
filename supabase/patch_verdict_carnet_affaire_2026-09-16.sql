-- ═══════════════════════════════════════════════════════════════════════════════
-- 3.1 (suite) -- LE VERDICT SUR LA SAISIE : arrivee, en attente, ou conflit
-- ═══════════════════════════════════════════════════════════════════════════════
-- Copie versionnee de la migration `carnet_affaire_verdict_de_la_saisie`.
-- Elle complete patch_photo_saisie_affaire_2026-09-16.sql, pose deux heures plus tot.
--
-- ─── LE DEFAUT, TEL QU'IL SE VOIT A L'ECRAN ───
-- Un negociateur corrige un prix, clique « Modifier chez Hektor ». La valeur
-- s'affiche en VERT (elle vient du carnet, elle prime). Ensuite, trois choses
-- peuvent arriver, et LES TROIS SE RESSEMBLENT :
--     l'envoi est arrive           -> le worker retire la ligne, le vert disparait
--     l'envoi n'est jamais parti   -> la ligne RESTE en vert
--     quelqu'un a change chez eux  -> la ligne RESTE en vert
-- Les deux derniers cas sont indiscernables d'une saisie faite il y a trois
-- secondes. Le negociateur croit que c'est parti.
--
-- ─── LE VERDICT SE DEDUIT, IL NE S'OBSERVE PAS ───
-- Depuis la photo, le worker tient TROIS valeurs. Le verdict en decoule :
--     la photo      ce que Hektor portait AVANT la saisie
--     la saisie     ce que le negociateur a tape
--     la relue      ce que le registre porte APRES l'envoi (= ce que Hektor a retenu)
--
--     relue == saisie   ->  arrivee      (la ligne aurait du etre retiree : on le DIT)
--     relue == photo    ->  en_attente   (rien n'a bouge chez eux : l'envoi n'est pas passe)
--     ni l'un ni l'autre->  conflit      (leur valeur a change, et ce n'est pas la notre)
--     pas de photo      ->  inconnu      (on ne devine pas)
--
-- ⚠ ON COMPARE AU REGISTRE, PAS AUX CLES DE HEKTOR, et c'est ce qui rend la
--   chose sure : `reporterAuRegistre` vient d'y ecrire ce que Hektor a RETENU.
--   Les champs qui ont recu une photo sont EXACTEMENT ceux qu'on sait juger --
--   la symetrie evite une seconde table de correspondance, qui divergerait.
--
-- ─── LA POUSSEE PARTIELLE N'A PAS BESOIN DE COLONNE ───
-- Pour l'annonce, `partial` + `skipped_fields` disent « 7 champs sur 10 sont
-- passes ». Ici le carnet porte UNE LIGNE PAR CHAMP : les 7 arrives sont
-- retires, les 3 restants portent leur propre verdict. La poussee partielle se
-- LIT, elle n'a rien a stocker. On ne recopie donc pas le patron a la lettre --
-- c'est voulu, et c'est plus simple.
--
-- ⚠ CE QUI RESTE INCONNU, ET C'EST HONNETE : les 28 lignes ecrites AVANT la
--   photo n'en ont pas, donc leur verdict est `inconnu`. On ne fabrique pas un
--   jugement retroactif -- elles se resoudront a la prochaine saisie.
--
-- RETOUR ARRIERE : rien ne casse si personne ne lit ces colonnes. Sinon
-- `ALTER TABLE ... DROP COLUMN etat, valeur_hektor_relue, constate_le`.
-- ═══════════════════════════════════════════════════════════════════════════════

ALTER TABLE public.app_affaire_champ_app
  ADD COLUMN IF NOT EXISTS etat                text,
  ADD COLUMN IF NOT EXISTS valeur_hektor_relue text,
  ADD COLUMN IF NOT EXISTS constate_le         timestamptz;

COMMENT ON COLUMN public.app_affaire_champ_app.etat IS
  'Le verdict sur la saisie (3.1, 16/09/2026) : arrivee · en_attente · conflit · '
  'inconnu. Pose par le worker apres la relecture, en comparant la photo, la '
  'saisie et ce que le registre porte. NULL = jamais juge.';

COMMENT ON COLUMN public.app_affaire_champ_app.valeur_hektor_relue IS
  'Ce que le registre portait de Hektor au moment du verdict -- la troisieme '
  'valeur de la comparaison. Gardee pour que le verdict soit RELISIBLE : sans '
  'elle, « conflit » serait une affirmation sans piece jointe.';

COMMENT ON COLUMN public.app_affaire_champ_app.constate_le IS
  'Quand le verdict a ete pose. Un verdict vieux de trois jours sur une saisie '
  'de ce matin ne veut rien dire -- la date le fait voir.';
