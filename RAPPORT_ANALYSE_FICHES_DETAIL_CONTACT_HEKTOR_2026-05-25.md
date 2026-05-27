# Analyse des fiches detail contact Hektor - 2026-05-25

## Objet

Cette analyse vise a comprendre ce que retourne reellement l'endpoint Hektor
`/Api/Contact/ContactById`, afin de ne pas confondre :

- la fiche identite du contact ;
- les recherches acquereur ;
- les liens annonce/proprietaire visibles depuis la fiche contact.

Aucune suppression n'a ete faite. Aucun push Supabase n'a ete fait.

## Echantillon controle

J'ai appele Hektor sur 11 contacts representatifs, puis stocke uniquement les
reponses brutes dans la base locale `data/hektor.sqlite`, table
`raw_api_response`, endpoint `contact_detail`.

Echantillon couvert :

| Profil teste | Archive | Resultat |
| --- | --- | --- |
| Acquereur pur | actif | fiche contact presente, `recherches` presente mais vide |
| Acquereur pur | archive | fiche contact presente, `recherches` presente mais vide |
| Mandant pur | actif | fiche contact presente, `annonces` presente |
| Mandant pur | archive | fiche contact presente, `annonces` presente mais vide |
| Partenaire pur | actif | fiche contact presente uniquement |
| Partenaire pur | archive | fiche contact presente uniquement |
| Acquereur + mandant | actif | fiche contact presente, `recherches` presente, `annonces` presente |
| Acquereur + mandant | archive | fiche contact presente, `recherches` presente, `annonces` presente |
| Mandant + partenaire | actif | fiche contact presente, `annonces` presente |
| Mandant + partenaire | archive | fiche contact presente, `annonces` presente |
| Typologie vide | archive | fiche contact presente uniquement |

## Structure reelle observee

Le retour Hektor contient toujours ce socle :

```json
{
  "data": {
    "contact": {}
  },
  "metadata": {},
  "refresh": null,
  "error": null
}
```

Selon le role du contact, `data` peut contenir aussi :

```json
{
  "data": {
    "contact": {},
    "recherches": [],
    "annonces": []
  }
}
```

Point important : sur les non-acquereurs testes, le champ `recherches` n'est
pas toujours un tableau vide. Il est souvent absent. Il faut donc interpreter
`recherches absent` et `recherches: []` comme deux cas differents techniquement,
mais proches fonctionnellement : pas de recherche acquereur exploitable.

## Bloc `contact`

Sur les 11 fiches testees, `data.contact` contient toujours les 17 champs :

```text
agence
archive
civilite
commentaires
coordonnees
dateAutoArchiv
dateenr
datemaj
id
id_negociateur
localite
nom
prenom
refCouple
siret
typologie
url
```

Interpretation :

- `contact` est la fiche identite/annuaire.
- Elle existe aussi pour les mandants, partenaires et contacts sans typologie.
- Elle n'est pas une preuve de recherche acquereur.
- Dans l'echantillon, le bloc `contact` est quasiment identique au listing
  `ListContacts`. Une difference a ete observee sur `id_negociateur` pour un
  contact, donc `ContactById` peut quand meme servir d'autorite de fraicheur.

Exemple anonymise d'un contact `acquereur + mandant` :

```json
{
  "id": "masque",
  "archive": "0",
  "typologie": ["acquereur", "mandant"],
  "agence": "1",
  "id_negociateur": "1",
  "dateenr": "2025-10-09",
  "datemaj": "2025-12-09 11:38:58",
  "dateAutoArchiv": "2026-10-09 00:00:00",
  "refCouple": null,
  "siret": null,
  "url": null,
  "commentaires": {
    "present": false,
    "longueur": 0
  },
  "coordonnees": {
    "email": "masque"
  },
  "localite": {
    "pays": "fr",
    "ville_presente": false,
    "code_present": false,
    "adresse_presente": false
  }
}
```

Exemple anonymise d'un mandant pur :

```json
{
  "id": "masque",
  "archive": "0",
  "typologie": ["mandant"],
  "agence": "18",
  "id_negociateur": "4",
  "dateenr": "2023-10-19",
  "datemaj": "2025-01-20 16:05:01",
  "dateAutoArchiv": "0000-00-00 00:00:00",
  "coordonnees": {},
  "localite": {
    "pays": "",
    "ville_presente": false,
    "code_present": false,
    "adresse_presente": false
  }
}
```

## Bloc `recherches`

Le bloc `recherches` correspond aux recherches acquereur.

Dans l'echantillon :

| Profil | Champ `recherches` |
| --- | --- |
| Acquereur pur actif | present, tableau vide |
| Acquereur pur archive | present, tableau vide |
| Acquereur + mandant actif | present, 1 recherche |
| Acquereur + mandant archive | present, 1 recherche |
| Mandant pur | absent |
| Partenaire pur | absent |
| Mandant + partenaire | absent |
| Typologie vide | absent |

Structure observee d'une recherche :

```json
{
  "offre": "0",
  "archive": "0 ou 1",
  "types": {
    "id_type_bien": "libelle ou valeur Hektor"
  },
  "types_commerces": null,
  "activites_commerces": null,
  "villes": [],
  "quartiers": null,
  "particularites": null,
  "criteres": [
    {
      "cle": "critere",
      "valeur": "valeur",
      "ponderation": "poids"
    }
  ]
}
```

Interpretation :

- `recherches` doit alimenter un module separe "Recherches acquereurs".
- Un contact acquereur peut avoir `recherches: []` : il est acquereur dans
  l'annuaire, mais sans recherche exploitable dans le detail teste.
- Une recherche a son propre etat `archive`, independant du champ archive du
  contact.
- Il faut normaliser `types`, `villes` et `criteres` avant de pouvoir faire un
  matching propre avec les annonces.

## Bloc `annonces`

Le bloc `annonces` apparait sur les mandants et certains contacts mixtes.

Dans l'echantillon :

| Profil | Champ `annonces` |
| --- | --- |
| Mandant pur actif | present, 1 annonce |
| Mandant pur archive | present, tableau vide |
| Mandant + partenaire actif | present, 1 annonce |
| Mandant + partenaire archive | present, 1 annonce |
| Acquereur + mandant | present, tableau vide dans les 2 cas testes |
| Acquereur pur | absent |
| Partenaire pur | absent |
| Typologie vide | absent |

Structure observee d'une annonce rattachee :

```json
{
  "id": "id_annonce",
  "NO_DOSSIER": "reference dossier",
  "NO_MANDAT": "numero mandat",
  "offredem": "0",
  "idtype": "type bien",
  "prix": 0,
  "surface": "surface",
  "titre": "titre",
  "corps": "description",
  "photo": "url photo",
  "agence": "id agence",
  "NEGOCIATEUR": "id negociateur",
  "archive": "0 ou 1",
  "diffusable": "0 ou 1",
  "partage": "0 ou 1",
  "localite": {},
  "valide": "0 ou 1",
  "dateenr": "date creation",
  "datemaj": "date maj"
}
```

Interpretation :

- `annonces` semble etre le rattachement proprietaire/mandant vu depuis la
  fiche contact.
- Ce bloc peut completer les relations annonce-contact deja extraites depuis
  les details annonce.
- Il ne faut pas le melanger avec `recherches`, car il ne represente pas une
  demande acquereur.

## Conclusion fonctionnelle

La bonne interpretation est :

1. `data.contact` = annuaire global du contact.
2. `data.recherches` = recherches acquereur, a stocker dans une table/module
   dedie.
3. `data.annonces` = annonces rattachees au contact cote mandant/proprietaire,
   a rapprocher des relations annonce-contact.

Donc l'integration doit etre separee en trois couches :

- annuaire contacts ;
- recherches acquereurs ;
- relations contact-annonce.

Il ne faut pas considerer qu'une fiche detail contact est une fiche acquereur.
La fiche detail est globale ; seule la presence de recherches exploitables
permet de creer une ligne "recherche acquereur".

## Consequence pour l'export massif

Avant de lancer les 340 000+ fiches :

- exporter par lots limites et reprenables ;
- prioriser les contacts avec typologie `acquereur`, puis les mixtes ;
- echantillonner aussi des mandants/partenaires pour mesurer le volume reel de
  `annonces` ;
- normaliser localement tous les blocs bruts ;
- ne pousser vers Supabase qu'une version limitee, sans JSON complet ni donnees
  inutiles.
