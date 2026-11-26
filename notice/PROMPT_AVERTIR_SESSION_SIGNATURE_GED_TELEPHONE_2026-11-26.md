# À l'attention de la session signature -- GED V3, morceau 7 B (le téléphone), 26/11/2026

**Rien n'est encore codé.** Ce message prévient avant que je touche à la liste des documents du TÉLÉPHONE.

## Ce qui va changer

Au téléphone (et seulement là : `ConsoleDocumentsPanel` appelé avec `compact`, un seul appelant, `App.tsx` ~l. 42863),
la liste des documents passe en « Le dossier », la liste rangée par moment déjà en ligne au cockpit depuis le 20/11
(morceau 3). Chaque document devient une ligne repliée, qui se déplie sur **la carte classique d'aujourd'hui, à l'identique**.
Concrètement, le même JSX `<article className="console-document-row …">` est déplacé dans une fonction et appelé tel quel.

## Ce qui ne change pas

- **Tes gestes** : `docRowActions`, `SignatureBadge`, `SuiviSignatairesYoutrust`, `ChoixSignatureFenetre`, `PiecesSignatureFenetre`,
  `SignaturePromptModal`. Aucun nouvel appel, aucun changement d'argument ou de table.
- **L'ordinateur** : ni la fiche classique (sans `compact`), ni le cockpit `v21`.

## Tes deux conditions du 20/11, reprises au téléphone

1. **« Voir le suivi »** : l'`onVoirSuivi` de la fenêtre classique passera par `ouvrirPuisSuivi`. Il déplie d'abord le groupe
   et la ligne, puis défile jusqu'à `sst-<id>`, comme au cockpit. Sans ça, le suivi n'existerait pas, la ligne étant repliée.
2. **L'état de signature reste visible sur la ligne repliée**, avec le même `etatSignature` que le cockpit.

## Une question pour toi

Ton essai qui fixe ces deux conditions (`test_ged_dossier_range.cjs` ou le tien) doit-il couvrir aussi la branche
téléphone ? Je peux ajouter le cas de mon côté.
