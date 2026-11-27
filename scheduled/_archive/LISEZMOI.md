# scheduled/_archive — ce qui ne doit plus tourner

Un script rangé ici est **gardé pour son histoire**, pas pour servir. Il refuse de
tourner : il sort en **code 3** avant le moindre import.

## push_suivi_appsheet.py — archivé le 19/11/2026

- **Décision de Frédéric (19/11/2026)** : *« archive-le. Il n'a plus d'utilité. »*
- **Ce qu'il faisait** (13/10, corrigé le 22/10) : il créait dans le classeur Google Sheet
  les lignes des affaires nouvelles, puis les **faisait avancer** (compromis, vente,
  notaire, état), case par case, en suivant trois règles : remplir un vide sans jamais
  corriger un plein, ne jamais faire reculer un état, s'abstenir devant un doute.
  Il ne se lançait **qu'à la main** (`--envoyer`) : aucune des 174 tâches planifiées ne
  l'appelait (mesuré le 19/11).
- **Pourquoi il fallait l'arrêter** : il se souvenait du lien dans la feuille elle-même.
  Pour lui, une ligne qui porte un `affair_uuid` lui appartient. Or le chantier classeur
  (étape 5.2) va écrire **nos étiquettes de dossier** dans cette colonne, sur environ
  4 000 lignes saisies par des humains. Il les aurait prises pour les siennes et les
  aurait fait avancer. C'était le verrou P0 du § 8 de
  `notice/CHANTIER_CLASSEUR_TEMPS4_5_FINIR_2026-11-19.md`.
- **Il n'avait jamais été suivi par git.** Le premier commit de l'archive le porte
  **tel qu'il était, à l'octet** (md5 `49d8ab44e6666cf4cc84dc400a64dcf1`). Le second
  ajoute seulement l'en-tête et le refus de tourner.
  Une copie datée est aussi gardée :
  `C:\Hektor\Backups\push_suivi_appsheet_AVANT_ARCHIVAGE_2026-11-19.py`.
- **Ce qui reste vrai après lui** : le compte de service garde le droit d'écrire dans le
  Sheet. C'est voulu, puisque l'écriture des étiquettes en aura besoin. Les lecteurs du
  Sheet (`phase2/checks/apparier_classeur.py`, `rapprocher_classeur_suivi.py`,
  `rapport_gel_tous_les_champs.py`) ne font que lire, même s'ils demandent la portée qui
  écrit.
