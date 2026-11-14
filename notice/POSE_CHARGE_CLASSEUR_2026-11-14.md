# LA CHARGE DEPUIS LE CLASSEUR -- etape (1), passe du 14/11/2026

Ses deux decisions du 04/11 : **go** sur la pose, et **oui**, la valeur du
classeur **fait foi** -- donc elle va au carnet avec `origine = 'classeur'`.

## Ce que le classeur porte

```
lignes du classeur                 4789
charge renseignee                  971
charge vide                        3818
valeur REFUSEE (inconnue)          0
doublons divergents                0
```

## Ce qui est pose, et ce qui est ecarte

```
A POSER                            16   (15 vendeur, 1 acquereur)
ecartee -- le carnet porte DEJA une valeur (on n ecrase pas) 898
ecartee -- lien hors 1re passe (a valider / bonne)    25
ecartee -- la ligne n est pas reliee par le gel       21
ecartee -- EXCLU PAR DECISION (classeur contradictoire) 4
ecartee -- l affaire ne cite ni annonce ni mandat     4
ecartee -- le mandat n est pas au registre            3
conflits (deux lignes, deux charges) 0
```

## Les temoins

```
positif VENDEUR    annonce 47132 mandat 18874
positif ACQUEREUR  annonce 49852 mandat 17823
INVERSE            lignes vides du classeur qui seraient posees : 0
```

Les temoins sont **mesures ici**, jamais rappeles de memoire : le 04/11 au
matin, un temoin choisi de souvenir etait faux et le garde-fou a arrete le
script.

## Ce que ca pourrait casser ailleurs

`app_reposer_charge_mandat_app` filtre `origine = 'mandat_app'` **aux quatre
endroits**, dont son effacement. Elle n'est appelee par personne aujourd'hui
(temoin positif : sa soeur de la cloture **est** appelee,
`push_single_annonce_to_supabase.py:710`). Le jour ou on l'ajoute au run par
symetrie, elle **effacerait** toute valeur sans ligne `mandat_app`.
Le patch l'elargit aux deux origines : la saisie humaine garde la main
(la RPC fait `ON CONFLICT DO UPDATE` et repasse l'origine a `mandat_app`).
