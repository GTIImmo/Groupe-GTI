
## ⚠ RESERVE TROUVEE LE 16/11 (en passant, depuis le chantier classeur) -- NON TRAITEE

`transactionPourLien` (apps/hektor-v1/src/lib/assistant.ts:156, lot 3b du 16/11)
recalcule l'annee d'une chaine DANS LE NAVIGATEUR, a partir de trois colonnes :
`max(date, date_acte, date_annulation_app)`. Le registre, lui, prend
`max(jour_vrai)` -- c'est-a-dire `app_dossier_jour_date_transaction(...)`, qui rend
LA PREMIERE PROPOSITION pour une offre (decision du 12/11 : « le dernier evenement
se juge sur le JOUR REEL, sinon un refus d'hier fait paraitre recente une affaire
de 2014 »).

MESURE DU 16/11, sur 11 383 chaines lisibles :

```
   desaccord total            1 814   (15,9 %)
   du SEUL date_acte            608   une date d acte PREVUE, que le registre ignore
   du JOUR VRAI de l offre    1 206   la date du refus au lieu de la 1re proposition
   les deux a la fois             0   <- partition propre
```

CE QUE CA FAIT A L'ECRAN, lu dans le code (PAS vu en reel) :
`RegistreTransactionsScreen` appelle `loadRegistreDossiers(anneeLue)` (l. 1321) avec
l'annee donnee par le lien. Si la chaine n'y est pas, il AVOUE --
« Transaction introuvable dans le registre 2021 » (l. 1696) -- et propose
« Tout voir », qui retire le filtre de chaine : donc on perd la cible.
⭐ Ce n'est donc PAS un echec silencieux. Mais le lien n'ouvre pas sa transaction.

⭐⭐ LA FORME EST DEJA TRANCHEE PAR LE PROJET -- SIX fonctions passent par la
fonction commune : app_registre_dossiers, app_pilotage_affaires_plus,
app_pilotage_acquereurs, app_notaire_fiche, app_controle_date_offre,
app_poser_etiquettes_dossier. `transactionPourLien` est LE SEUL a recalculer.
   ➡ une RPC `app_annee_de_la_chaine(chaine)` qui rend `max(jour_vrai)`, et le front
     l'appelle au lieu de calculer. Un seul correctif couvre 608 ET 1 206, et il
     devient impossible de diverger a nouveau.

⬜ DEUX DECISIONS POUR FREDERIC, aucune prise :
   . pose-t-on ce correctif, ou le laisse-t-on en reserve ?
   . une date d'acte PREVUE doit-elle rajeunir un dossier ? Le registre dit NON
     deja aujourd'hui ; je ne l'aligne pas de moi-meme.

⛔ FREDERIC, 16/11 : « cela n'a rien a voir c'est un autre chantier » -- NE PAS le
traiter depuis le chantier classeur.
