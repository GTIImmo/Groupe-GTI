# LA CHARGE DEPUIS LE CLASSEUR -- etape (1) posee le 04/11/2026

Ses deux decisions du 04/11 : **go** sur la pose, et **oui**, la valeur du
classeur **fait foi** -- donc elle va au carnet avec `origine = 'classeur'`.

## Ce que le classeur porte

```
lignes du classeur                 4777
charge renseignee                  957
charge vide                        3820
valeur REFUSEE (inconnue)          0
doublons divergents                0
```

## Ce qui est pose, et ce qui est ecarte

```
A POSER                            839   (802 vendeur, 37 acquereur)
ecartee -- fondue : meme mandat, meme charge (2e transaction) 55
ecartee -- lien hors 1re passe (a valider / bonne)    29
ecartee -- la ligne n est pas reliee par le gel       25
ecartee -- l affaire ne cite ni annonce ni mandat     4
ecartee -- le mandat n est pas au registre            3
conflits (deux lignes, deux charges) 2
```

### Les conflits, NOMMES (un controle qui agrege perd ce qui sert a agir)

```
46338/17322 : acquereur contre vendeur (ID afd672fa et cc33cc38)
47174/17639 : vendeur contre acquereur (ID 2c2566d7 et df0ce30c)
```

## Les temoins

```
positif VENDEUR    annonce 10702 mandat 2154
positif ACQUEREUR  annonce 11820 mandat 17888
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
