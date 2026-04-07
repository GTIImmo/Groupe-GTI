# Hektor API v2 - Documentation

> **Version** : v2
> 
> 
> **Base URL** : `{{url}}/Api/`
> 
> **Dernière mise à jour** : Février 2024
> 

---

# Table des matières

---

# Présentation

L'API Hektor permet à un utilisateur de s'authentifier et de manipuler les ressources présentes sur son logiciel Hektor (CRM immobilier).

L'authentification se fait avec un **JWT**, via une **clé d'autorisation propre à un client (oAuth)**.

> Pour définir un client auprès de La Boîte Immo, envoyez un mail à : [technique@la-boite-immo.com](mailto:technique@la-boite-immo.com)
> 

---

# Authentification

Toutes les routes (hors authentification) nécessitent un header d'authentification :

| Header | Description |
| --- | --- |
| `jwt` | Token JWT obtenu via SSO ou login |

## oAuth Client Credentials

Obtient un access token sans connexion utilisateur. L'utilisateur référent est celui défini par le client sur l'instance logicielle cible.

```
POST /Api/OAuth/Authenticate/
```

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `client_id` | string | oui | Identifiant du client oAuth |
| `client_secret` | string | oui | Secret du client oAuth |
| `grant_type` | string | oui | Toujours `client_credentials` |

**Réponse** :

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

---

## JWT via SSO

Retourne un token JWT de connexion à partir d'un access token oAuth valide.

```
POST /Api/OAuth/Sso/
```

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `client_id` | string | oui | Identifiant du client oAuth |
| `token` | string | oui | Access token obtenu via Client Credentials |
| `scope` | string | oui | Toujours `sso` |

**Réponse** :

```json
{
  "jwt": "eyJhbGciOiJIUzI1NiIs..."
}
```

---

## Connexion externe

Génère une URI de connexion externe pour un service tiers.

```
GET /Api/ExternalConnect/connectUri/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `source` | string | oui | Source de la connexion externe |
| `id` | int | oui | Identifiant de la ressource cible |

---

# Format de réponse

## v2 - A PRIVILEGIER

Toutes les réponses suivent un format standardisé :

```json
{
  "data": { ... },
  "metadata": {
      "total": 0,
      "perPage": 10,
      "currentPage": 1,
      "prevPage": null,
      "nextPage": null,
      "from": 1,
      "to": 1
  },
  "refresh": "eyJhbG...",
  "error": null
}
```

| Champ | Type | Description |
| --- | --- | --- |
| `data` | mixed | Données de la réponse (objet ou tableau) |
| `metadata` | object | Métadonnées (pagination, nombre, etc.) |
| `refresh` | string | Nouveau JWT si le token actuel expire bientôt (< 10 min) |
| `error` | string | Message d'erreur le cas échéant |

## v1 (legacy) - DEPRECATED

Pour forcer la v1, passer `version=v0` ou `version=v1` en paramètre.

```json
{
  "res": { ... },
  "count": 42,
  "refresh": "eyJhbG..."
}
```

---

## Pagination

Les listings sont paginés par **20 éléments** par défaut.

| Paramètre | Type | Description |
| --- | --- | --- |
| `page` | int | Numéro de page (commence à 1) |

Le champ `metadata.total` (v2) ou `count` (v1) indique le nombre total d'éléments.

---

# Endpoints

---

## User

### Détail User

Retourne le détail d'un utilisateur. Si aucun `id` n'est spécifié, retourne l'utilisateur authentifié par le JWT.

```
GET /Api/User/UserFromId/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token de l'utilisateur (ou du client via token/client_id) |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `id` | int | non | ID de l'utilisateur (défaut : utilisateur du token) |
| `version` | string | non | Version de l'API (`v0`, `v1`, `v2`). |

**Réponse v2** :

```json
{
  "data": {
    "idunique": "instance.example.com_4",
    "idUser": "4",
    "type": "ADMIN",
    "nom": "DOE",
    "prenom": "John",
    "site": "<https://www.example.com>",
    "coordonnees": {
      "tel": "01 00 00 00 01",
      "portable": "06 00 00 00 01",
      "mail": "john.doe@example.com"
    },
    "adresse": {
      "adresse": "1 rue des Exemples",
      "ville": "Exempleville",
      "code": "75000"
    },
    "img": "<https://cdn.example.com/img/user/4.png>",
    "color": "#3358AD",
    "lastConnexion": "2026-02-16 14:14:03",
    "state": "1"
  },
  "metadata": {
    "total": 0,
    "perPage": 10,
    "currentPage": 1,
    "prevPage": null,
    "nextPage": null,
    "from": 1,
    "to": 1
  },
  "refresh": null,
  "error": null
}
```

---

### Liste Users

Liste les utilisateurs enfants d'un parent dans la hiérarchie.

```
GET /Api/User/UsersOfParent/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `idParent` | int | non | ID de l'utilisateur parent (défaut : user du token) |
| `page` | int | oui | Page du listing |
| `actif` | int | non | Filtre sur le statut actif : `1` = actifs, `0` = inactifs |
| `version` | string | non | Version de l'API |
| `mailUser` | string | non | Filtre par e-mail utilisateur |

**Réponse v2** :

```json
{
  "data": [
    {
      "idunique": "instance.example.com_1",
      "idUser": "1",
      "type": "AGENCE",
      "nom": "Agence Exemple Immo",
      "prenom": "",
      "site": "www.exemple-immo.com",
      "coordonnees": {
        "tel": "01 00 00 00 02",
        "portable": "06 00 00 00 02",
        "mail": "contact@exemple-immo.com"
      },
      "adresse": {
        "adresse": "1 rue des Exemples",
        "ville": "Exempleville",
        "code": "75000"
      },
      "img": "<https://cdn.example.com/img/agence/1.jpg>",
      "color": "#3358AD",
      "lastConnexion": "2025-12-08 16:42:59",
      "state": "1"
    },
    {
      "idunique": "instance.example.com_8",
      "idUser": "8",
      "type": "NEGO",
      "nom": "DURAND",
      "prenom": "Alice",
      "site": "<https://www.example.com>",
      "coordonnees": {
        "tel": "01 00 00 00 05",
        "portable": "06 00 00 00 05",
        "mail": "alice.durand@exemple-immo.com"
      },
      "adresse": {
        "adresse": "1 rue des Exemples",
        "ville": "Exempleville",
        "code": "75000"
      },
      "img": "<https://cdn.example.com/img/nego/8.jpg>",
      "color": "#22f0db",
      "lastConnexion": "2023-03-10 14:31:50",
      "state": "1"
    }
  ],
  "metadata": {
    "total": 13,
    "perPage": 10,
    "currentPage": 1,
    "prevPage": null,
    "nextPage": 2,
    "from": 1,
    "to": 2
  },
  "refresh": null,
  "error": null
}
```

---

## Annonce

### Listing Annonces

Liste les annonces avec filtres et tri.

```
GET /Api/Annonce/ListAnnonces/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `offre` | int | non | Type d'offre : `0` vente, `2` location, `6` neuf, `8` saisonnier, `10` vente immo pro, `11` location immo pro |
| `type` | int | non | ID du type de bien (ex : `1` maison, `2` appartement, `4` studio, `25` villa) |
| `archive` | int | non | `0` actifs, `1` archivés |
| `sort` | string | non | Champ de tri (ex : `prix`, `date`). Défaut : date de création |
| `way` | string | non | Sens du tri : `ASC` ou `DESC` (défaut : `DESC`) |
| `page` | int | oui | Page du listing (commence à 0) |
| `agence` | int | non | ID d'agence pour filtrer |
| `diffusable` | int | non | `1` diffusables, `0` non diffusables |
| `version` | string | non | Version de l'API |

**Réponse v2** :

```json
{
  "data": [
    {
      "id": "5108",
      "NO_DOSSIER": "1702",
      "NO_MANDAT": "1702",
      "offredem": "0",
      "idtype": "2",
      "prix": 120000,
      "surface": "29.3",
      "titre": "T2 TRAVERSANT AVEC PARKING",
      "corps": "<p>Description du bien...</p>",
      "photo": "<https://cdn.example.com/img/biens/1/photo.jpg>",
      "agence": "1",
      "NEGOCIATEUR": "15",
      "archive": "0",
      "diffusable": "1",
      "partage": "1",
      "localite": {
        "pays": "fr",
        "publique": {
          "ville": "Exempleville",
          "code": "75000",
          "latitude": "48.000000000",
          "longitude": "2.000000000"
        },
        "privee": {
          "ville": "Exempleville",
          "code": "75000",
          "latitude": "48.000000000",
          "longitude": "2.000000000",
          "adresse": "4 rue des Exemples - Résidence A - Appartement 45"
        }
      },
      "valide": "0"
    }
  ],
  "metadata": {
    "total": 150,
    "perPage": 20,
    "currentPage": 3,
    "prevPage": 2,
    "nextPage": 4,
    "from": 1,
    "to": 8
  },
  "refresh": null,
  "error": null
}
```

---

### Recherche Annonces

Recherche textuelle parmi les annonces accessibles par l'utilisateur. Même format de réponse que le listing.

```
GET /Api/Annonce/searchAnnonces/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `search` | string | oui | Terme de recherche |
| `strict` | int | non | `1` pour recherche stricte |
| `version` | string | non | Version de l'API |

---

### Détail Annonce

Retourne le détail complet d'une annonce.

```
GET /Api/Annonce/AnnonceById/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `id` | int | oui | ID de l'annonce |
| `version` | string | non | Version de l'API |

**Réponse v2** (structure détaillée) :

```json
{
  "data": {
    "localite": {
      "pays": "fr",
      "publique": {
        "ville": "Exempleville",
        "code": "75000",
        "latitude": "48.000000000",
        "longitude": "2.000000000"
      },
      "privee": {
        "ville": "Exempleville",
        "code": "75000",
        "latitude": "48.000000000",
        "longitude": "2.000000000",
        "adresse": "10 impasse Modèle"
      }
    },
    "mandats": [
      {
        "id": "508",
        "type": "Simple",
        "debut": "2024-01-15",
        "fin": "2025-01-15",
        "cloture": null,
        "numero": "10005",
        "CartePro": null,
        "note": "",
        "duree_irrevocabilite": "",
        "taciteReconduction": "0",
        "montant": "275000",
        "mandants": "DOE - 5 PLACE DES EXEMPLES - Autreville 75100",
        "avenants": []
      }
    ],
    "pieces": null,
    "images": null,
    "proprietaires": [
      {
        "id": "304",
        "civilite": "M.",
        "nom": "DOE",
        "prenom": "John",
        "commentaires": "",
        "datemaj": null,
        "dateenr": "2024-01-01",
        "agence": "1",
        "archive": "0",
        "id_negociateur": null,
        "localite": {
          "pays": "fr",
          "localite": {
            "ville": "Autreville",
            "code": "75100",
            "latitude": "48.000000000",
            "longitude": "2.000000000",
            "adresse": "5 PLACE DES EXEMPLES"
          }
        },
        "siret": null,
        "url": null,
        "typologie": ["mandant"],
        "coordonnees": {
          "portable": "06 00 00 00 00"
        }
      }
    ],
    "honoraires": [
      {
        "id": "1595",
        "taux": "5",
        "charge": "Acheteur"
      }
    ],
    "textes": [
      {
        "id": 0,
        "type": "principal",
        "lang": "fr",
        "titre": "Charmante maison avec jardin",
        "text": "Description détaillée du bien..."
      }
    ],
    "statut": { "id": 1, "name": "Actif" },
    "particularites": [{ "id": 7, "name": "Jardin" }],
    "zones": {
      "quartiers": [{ "id": 3, "name": "Quartier Nord" }],
      "secteurs": [{ "id": 5, "name": "Secteur A" }]
    },
    "notes": [{ "type": "publique", "texte": "Disponible pour visite le week-end." }]
  },
  "metadata": null,
  "refresh": null,
  "error": null
}
```

---

## Lead

### Créer un Lead

Crée un nouveau lead (contact entrant) dans Hektor.

```
POST /Api/Lead/NewLead/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

**Body** (`form-data`) :

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `json` | string | oui | Contenu du lead au format JSON (voir structure ci-dessous) |
| `idUser` | int | non | ID user destinataire (défaut : user du token) |
| `idAnnonce` | int | non | ID annonce associée |
| `source` | string | non | Source du lead (ex : `SeLoger`, `LeBonCoin`, nom du partenaire) |
| `version` | string | non | Version de l'API |

**Structure JSON du lead** :

```json
{
  "first_name": "Doe",
  "last_name": "Jane",
  "email": "jane.doe@example.com",
  "phone": "+33600000000",
  "message": "Bonjour, je souhaiterais obtenir des informations sur ce bien.",
  "listing_id": "CLIENT_REF_123",
  "ad_id": "456",
  "params": {
    "prixMin": "200000",
    "prixMax": "400000",
    "surfMin": "60",
    "pieceMin": "3",
    "chambreMin": "2",
    "geoLocalites": [
      { "ville": "exempleville", "code": "75000" },
      { "ville": "autreville", "code": "75100" }
    ]
  }
}
```

**Réponse v2** :

```json
{
  "data": {
    "id": "3064",
    "createDate": "2026-02-19 14:47:16",
    "nom": "Jane",
    "prenom": "Doe",
    "email": "jane.doe@example.com",
    "tel": "+33600000000",
    "message": "Bonjour, je souhaiterais obtenir des informations sur ce bien.",
    "source": "SOURCE_NAME",
    "offre": "Offres De Location",
    "id_agence": "1",
    "assignation": null,
    "recherche": null,
    "annonces": null
  },
  "metadata": {
    "total": 0,
    "perPage": 10,
    "currentPage": 1,
    "prevPage": null,
    "nextPage": null,
    "from": 1,
    "to": 1
  },
  "refresh": null,
  "error": null
}
```

---

### Listing Leads

Liste les leads reçus.

```
GET /Api/Lead/listLeads
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `idAgence` | int | non | Agence en réception des leads (assignés ou non) |
| `idUser` | int | non | User à qui sont assignés les leads listés |
| `page` | int | oui | Page du listing (pages de 20 items) |
| `version` | string | non | Version de l'API |

**Réponse v2** :

```json
{
  "data": [
    {
      "id": "3053",
      "createDate": "2025-12-22 16:26:55",
      "nom": "Doe",
      "prenom": "Jane",
      "email": "jane.doe@example.com",
      "tel": "+33600000000",
      "message": "Bonjour, je souhaiterais obtenir des informations.",
      "source": "API LBI",
      "offre": "Offres De Vente",
      "id_agence": "1",
      "assignation": {
        "idunique": "instance.example.com_19",
        "idUser": "19",
        "type": "NEGO",
        "nom": "MARTIN",
        "prenom": "Claire"
      },
      "recherche": {
        "garage": true,
        "parking": true,
        "terrace": true,
        "offre": "NEW_BUILDINGS",
        "propertyTypes": ["HOUSES", "APARTMENTS", "LAND", "OTHER"],
        "priceMin": 200000,
        "priceMax": 400000,
        "priceMargin": 10.2,
        "livingAreaMin": 40,
        "livingAreaMax": 100,
        "roomMin": 2,
        "roomMax": 5,
        "bedroomMin": 1,
        "bedroomMax": 3,
        "localities": [
          { "city": "exempleville", "zipCode": "75000", "inseeCode": "75001" },
          { "city": "autreville", "zipCode": "75100", "inseeCode": "75002" }
        ]
      },
      "annonces": ["5250"]
    }
  ],
  "metadata": {
    "total": 320,
    "perPage": 20,
    "currentPage": 1,
    "prevPage": null,
    "nextPage": 2,
    "from": 1,
    "to": 16
  },
  "refresh": null,
  "error": null
}
```

---

## Agence

### Listing Agences

Liste les agences du réseau, paginée par 20.

```
GET /Api/Agence/ListAgences/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui (ou oAuth) | Token JWT |
| `token` | string | alternatif | Access token oAuth |
| `clientid` | string | alternatif | Client ID oAuth |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `page` | int | oui | Page demandée (commence à 0) |
| `actif` | int | non | `1` actives, `0` inactives, absent = toutes |
| `version` | string | non | Version de l'API |

**Réponse v2** :

```json
{
  "data": [
    {
      "id": "1",
      "idUser": "1",
      "nom": "AGENCE EXEMPLE IMMO",
      "prenom": null,
      "alias": null,
      "mail": "contact@exemple-immo.com",
      "tel": "01 00 00 00 02",
      "fax": "01 00 00 00 11",
      "site": "www.exemple-immo.com",
      "responsable": "John DOE",
      "color": "#3358AD",
      "logo": "<https://cdn.example.com/img/logo.jpg>",
      "avatar": "<https://cdn.example.com/img/avatar.jpg>",
      "bareme": "<https://www.example.com/honoraires>",
      "informationJuridique": {
        "id": "1",
        "type_entreprise": "SARL",
        "name": "AGENCE EXEMPLE IMMO",
        "siret": "00000000000000",
        "naf": "6831Z",
        "capital": "7500",
        "rcs": "000000000000000",
        "numero_tva": "FR 00000000000000"
      },
      "carteProfessionnelle": {
        "id": "1",
        "card_type": "TGS",
        "maniements": "OUI",
        "detenteur": "John DOE",
        "num_card": "CPI XXXX XXXX XXX XXX XXX",
        "delivered_name": "Chambre de commerce",
        "date": "2020-06-01",
        "garant": "GARANT EXEMPLE",
        "montant": "120000"
      },
      "parent": "4",
      "type": "AGENCE",
      "specification": null
    }
  ],
  "metadata": {
    "total": 3,
    "perPage": 20,
    "currentPage": 1,
    "prevPage": null,
    "nextPage": null,
    "from": 1,
    "to": 1
  },
  "refresh": null,
  "error": null
}
```

---

### Détail Agence

Retourne le détail d'une agence par son ID. Même structure de réponse que le listing (objet unique au lieu d'un tableau).

```
GET /Api/Agence/AgenceById/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `id` | int | oui | ID de l'agence |
| `version` | string | non | Version de l'API |

---

## Mandat

### Liste Mandats (entre 2 dates)

Liste les mandats entre deux dates, avec pagination.

```
GET /Api/Mandat/ListMandat
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `beginDate` | string | oui | Date de début (format `YYYY-MM-DD`) |
| `endDate` | string | oui | Date de fin (format `YYYY-MM-DD`) |
| `idAgence` | int | non | ID agence (défaut : scope de l'user du token) |
| `page` | int | oui | Page souhaitée (commence à 0) |
| `state` | int | non | État du mandat |
| `sort` | string | non | Champ de tri |
| `way` | string | non | Sens du tri (`ASC` / `DESC`) |
| `version` | string | non | Version de l'API |

**Réponse v2** :

```json
{
  "data": [
    {
      "id": "355",
      "type": "Simple",
      "debut": "2024-02-19",
      "fin": "2025-03-31",
      "cloture": null,
      "numero": "394",
      "CartePro": "CPI XXXX XXXX XXX XXX XXX",
      "note": "",
      "duree_irrevocabilite": "",
      "taciteReconduction": "0",
      "montant": "275000",
      "mandants": "DOE - 1 rue des Exemples - Exempleville",
      "avenants": []
    }
  ],
  "metadata": {
    "total": 85,
    "perPage": 10,
    "currentPage": 1,
    "prevPage": null,
    "nextPage": 2,
    "from": 1,
    "to": 9
  },
  "refresh": null,
  "error": null
}
```

---

### Mandats par Annonce

Liste les mandats associés à une annonce.

```
GET /Api/Mandat/MandatsByIdAnnonce/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `idAnnonce` | int | oui | ID de l'annonce |
| `version` | string | non | Version de l'API |

**Réponse v2** :

```json
{
  "data": [
    {
      "id": "508",
      "idUser": "1",
      "idAnnonce": "2285",
      "idCartePro": "0",
      "numero": "10005",
      "type": "Simple",
      "dateEnregistrement": "2024-01-15 00:00:00",
      "dateDebut": "2024-01-15",
      "dateCloture": null,
      "dateFin": "2024-04-15",
      "taciteReconduction": "0",
      "montant": "275000",
      "mandants": "DOE - 5 PLACE DES EXEMPLES - Autreville 75100",
      "adresse": "10 impasse Modèle - 75000 Exempleville",
      "note": "",
      "duree_irrevocabilite": "",
      "_avenants": []
    }
  ],
  "metadata": {
    "total": 1,
    "perPage": 10,
    "currentPage": 1,
    "prevPage": null,
    "nextPage": null,
    "from": 1,
    "to": 1
  },
  "refresh": null,
  "error": null
}
```

---

### Détail Mandat

Retourne le détail d'un mandat par son ID.

```
GET /Api/Mandat/MandatById/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `id` | int | oui | ID du mandat |
| `version` | string | non | Version de l'API |

**Réponse v2** (structure détaillée) :

```json
{
  "data": {
    "id": "508",
    "type": "Simple",
    "debut": "2024-01-15",
    "fin": "2024-04-15",
    "cloture": null,
    "numero": "10005",
    "CartePro": null,
    "note": "",
    "duree_irrevocabilite": "",
    "taciteReconduction": "0",
    "montant": "275000",
    "mandants": "DOE - 5 PLACE DES EXEMPLES - Autreville 75100",
    "avenants": []
  },
  "metadata": {
    "total": 0,
    "perPage": 10,
    "currentPage": 1,
    "prevPage": null,
    "nextPage": null,
    "from": 1,
    "to": 1
  },
  "refresh": null,
  "error": null
}
```

---

## Négociateur

### Listing Négociateurs

Liste les négociateurs du réseau, paginés par 20.

```
GET /Api/Negociateur/listNegos/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui (ou oAuth) | Token JWT |
| `token` | string | alternatif | Access token oAuth |
| `clientid` | string | alternatif | Client ID oAuth |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `page` | int | oui | Page demandée (commence à 0) |
| `actif` | int | non | `1` actifs, `0` inactifs, absent = tous |
| `version` | string | non | Version de l'API |

**Réponse v2** :

```json
{
  "data": [
    {
      "id": "15",
      "idUser": "19",
      "agence": "1",
      "nom": "MARTIN",
      "prenom": "Claire",
      "fonction": "",
      "telephone": "0100000010",
      "portable": "0600000010",
      "email": "claire.martin@exemple-immo.com",
      "color": "#3358AD",
      "logo": "<https://cdn.example.com/img/logo.jpg>",
      "avatar": "<https://cdn.example.com/img/nego/15.jpg>"
    },
    {
      "id": "12",
      "idUser": "16",
      "agence": "1",
      "nom": "PETIT",
      "prenom": "Emma",
      "fonction": "",
      "telephone": "0100000008",
      "portable": "",
      "email": "emma.petit@exemple-immo.com",
      "color": "#3358AD",
      "logo": "<https://cdn.example.com/img/logo.jpg>",
      "avatar": "<https://cdn.example.com/img/nego/12.jpg>"
    }
  ],
  "metadata": {
    "total": 7,
    "perPage": 10,
    "currentPage": 1,
    "prevPage": null,
    "nextPage": null,
    "from": 1,
    "to": 1
  },
  "refresh": null,
  "error": null
}
```

---

### Détail Négociateur

Retourne le détail d'un négociateur par son ID. Même structure de réponse que le listing (objet unique).

```
GET /Api/Negociateur/NegoById/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui (ou oAuth) | Token JWT |
| `token` | string | alternatif | Access token oAuth |
| `clientid` | string | alternatif | Client ID oAuth |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `id` | int | oui | ID du négociateur |
| `version` | string | non | Version de l'API |

---

## Contact

### Listing Contacts

Liste les contacts d'une agence ou du scope de l'utilisateur.

```
GET /Api/Contact/ListContacts/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `agence` | int | non | ID agence (défaut : scope du user authentifié) |
| `archive` | int | non | `0` actifs, `1` archivés |
| `page` | int | oui | Page du listing |
| `type` | int | non | Type de contact |
| `sort` | string | non | Champ de tri |
| `way` | string | non | Sens du tri (`ASC` / `DESC`) |
| `version` | string | non | Version de l'API |

**Réponse v2** :

```json
{
  "data": [
    {
      "id": "7941",
      "civilite": "M.",
      "nom": "DOE",
      "commentaires": "",
      "datemaj": "2025-10-29 14:07:36",
      "dateenr": "2025-10-29",
      "agence": "1",
      "archive": "0",
      "id_negociateur": null,
      "dateAutoArchiv": "0000-00-00 00:00:00",
      "refCouple": null,
      "localite": {
        "pays": "fr",
        "localite": {
          "ville": "Exempleville",
          "code": "75000",
          "latitude": "48.000000000",
          "longitude": "2.000000000",
          "adresse": "1 rue des Exemples"
        }
      },
      "siret": null,
      "url": null,
      "prenom": "John",
      "typologie": ["partenaire"],
      "coordonnees": {
        "fixe": "0100000001",
        "email": "john.doe@example.com"
      }
    }
  ],
  "metadata": {
    "total": 42,
    "perPage": 20,
    "currentPage": 1,
    "prevPage": null,
    "nextPage": 2,
    "from": 1,
    "to": 3
  },
  "refresh": null,
  "error": null
}
```

---

### Recherche Contacts

Recherche textuelle parmi les contacts. Même format de réponse que le listing.

```
GET /Api/Contact/searchContacts/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `search` | string | oui | Terme de recherche |
| `agence` | int | non | ID agence pour filtrer |
| `page` | int | oui | Page du listing |
| `strict` | int | non | `1` pour recherche stricte |
| `version` | string | non | Version de l'API |

---

### Détail Contact

Retourne le détail d'un contact avec ses recherches associées.

```
GET /Api/Contact/ContactById
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `id` | int | oui | ID du contact |
| `version` | string | non | Version de l'API |

**Réponse v2** :

```json
{
  "data": {
    "contact": {
      "id": "7950",
      "civilite": "M.",
      "nom": "DOE",
      "commentaires": "",
      "datemaj": "2026-02-04 08:34:40",
      "dateenr": "2026-02-04",
      "agence": "1",
      "archive": "0",
      "id_negociateur": "0",
      "dateAutoArchiv": "2027-02-04 00:00:00",
      "refCouple": null,
      "localite": {
        "pays": "fr",
        "localite": {
          "ville": "",
          "code": "",
          "latitude": "0.000000000",
          "longitude": "0.000000000",
          "adresse": ""
        }
      },
      "siret": null,
      "url": null,
      "prenom": "John",
      "typologie": ["acquéreur"],
      "coordonnees": {
        "fixe": "+33100000000",
        "email": "john.doe@example.com"
      }
    },
    "recherches": []
  },
  "metadata": {
    "total": 0,
    "perPage": 10,
    "currentPage": 1,
    "prevPage": null,
    "nextPage": null,
    "from": 1,
    "to": 1
  },
  "refresh": null,
  "error": null
}
```

---

## Vente

### Liste Compromis

Liste les compromis (promesses de vente) paginés.

```
GET /Api/Vente/ListCompromis/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `page` | int | oui | Page du listing (commence à 0) |
| `sort` | string | non | Champ de tri (ex : `dateStart`) |
| `way` | string | non | Sens du tri (`asc` / `desc`) |
| `agence` | int | non | ID agence pour filtrer |
| `version` | string | non | Version de l'API |

**Réponse v2** :

```json
{
  "data": [
    {
      "id": "115",
      "date_start": "2024-06-01",
      "date_end": "2024-09-01",
      "note": null,
      "status": "1",
      "date_signature_acte": null,
      "part_admin": null,
      "sequestre": "10000.00",
      "prix_net": null,
      "honoraires_entree": null,
      "honoraires_sortie": null,
      "prix_publique": null,
      "annonce": {
        "id": "5092",
        "NO_DOSSIER": "1692",
        "offredem": "0",
        "idtype": "2",
        "prix": 140000,
        "surface": "43.54",
        "titre": "APPARTEMENT 2 PIÈCES AVEC VUE",
        "photo": "<https://cdn.example.com/img/biens/5092.jpg>",
        "agence": "1"
      },
      "mandat": {
        "id": "11153",
        "type": "EXCLUSIF",
        "numero": "1692",
        "CartePro": "CPI XXXX XXXX XXX XXX XXX",
        "montant": "140000",
        "mandants": "M. DOE John - 1 rue des Exemples - Exempleville (75000)"
      },
      "acquereurs": [
        {
          "id": "7804",
          "civilite": "M.",
          "nom": "DUPONT",
          "prenom": "Pierre"
        }
      ]
    }
  ],
  "metadata": {
    "total": 12,
    "perPage": 20,
    "currentPage": 1,
    "prevPage": null,
    "nextPage": null,
    "from": 1,
    "to": 1
  },
  "refresh": null,
  "error": null
}
```

---

### Détail Compromis

Retourne le détail d'un compromis.

```
GET /Api/Vente/CompromisById/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `idCompromis` | int | oui | ID du compromis |
| `version` | string | non | Version de l'API |

---

### Listing Ventes

Liste les ventes (actes signés) avec filtres de dates.

```
GET /Api/Vente/ListVentes/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |
| `agence` | int | non | ID agence (header) |
| `access_token` | string | alternatif | Access token oAuth |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `page` | int | oui | Page du listing (commence à 0) |
| `sort` | string | non | Champ de tri (ex : `date`) |
| `order` | string | non | Sens du tri (`asc` / `desc`) |
| `dateStart` | string | non | Date de début (format `YYYY-MM-DD`) |
| `dateEnd` | string | non | Date de fin (format `YYYY-MM-DD`) |
| `agency` | int | non | ID agence pour filtrer |

**Réponse v2** :

```json
{
  "data": [
    {
      "id": "148",
      "prix": "275000.00",
      "honoraires": "15000.00",
      "date": "2023-01-21",
      "retro_idUser": null,
      "retro_idContact": null,
      "retro_nom": null,
      "retro_qualite": null,
      "retro_honoraires": "0.00",
      "hono_entree": null,
      "hono_sortie": null,
      "hono_hors_taxe": null,
      "commission_agence": null,
      "part_admin": null,
      "annonce": {
        "id": "5074",
        "NO_DOSSIER": "1684",
        "NO_MANDAT": "1684",
        "offredem": "0",
        "idtype": "2",
        "prix": 275000,
        "surface": "95",
        "titre": "APPARTEMENT T4 AVEC TERRASSE",
        "corps": "<p>Description du bien...</p>",
        "photo": "<https://cdn.example.com/img/biens/5074.jpg>",
        "agence": "1",
        "NEGOCIATEUR": "12",
        "archive": "1",
        "diffusable": "1",
        "partage": "1",
        "localite": {
          "pays": "fr",
          "publique": {
            "ville": "Exempleville",
            "code": "75000",
            "latitude": "48.000000000",
            "longitude": "2.000000000"
          },
          "privee": {
            "ville": "Exempleville",
            "code": "75000",
            "latitude": "48.000000000",
            "longitude": "2.000000000",
            "adresse": "1 rue des Exemples - Résidence A - Appartement 10"
          }
        },
        "valide": "0"
      },
      "mandat": {
        "id": "11079",
        "type": "SIMPLE",
        "debut": null,
        "fin": null,
        "cloture": null,
        "numero": "1684",
        "CartePro": "CPI XXXX XXXX XXX XXX XXX",
        "note": "",
        "duree_irrevocabilite": "",
        "taciteReconduction": "0",
        "montant": "275000",
        "mandants": "M. DOE John - 1 rue des Exemples - Exempleville (75000)",
        "avenants": []
      },
      "mandants": [
        {
          "id": "7429",
          "civilite": "M.",
          "nom": "DOE",
          "prenom": "John",
          "agence": "1",
          "archive": "1",
          "localite": {
            "pays": "fr",
            "localite": {
              "ville": "Exempleville",
              "code": "75000",
              "adresse": "1 rue des Exemples"
            }
          },
          "typologie": ["mandant"],
          "coordonnees": {
            "portable": "0600000001",
            "email": "john.doe@example.com"
          }
        }
      ],
      "acquereurs": [
        {
          "id": "7538",
          "civilite": "M.",
          "nom": "DUPONT",
          "prenom": "Pierre",
          "agence": "1",
          "archive": "1",
          "localite": {
            "pays": "fr",
            "localite": {
              "ville": "",
              "code": "",
              "adresse": ""
            }
          },
          "typologie": ["acquéreur"],
          "coordonnees": {
            "portable": "0600000002",
            "email": "pierre.dupont@example.com"
          }
        }
      ],
      "notaires": {
        "entree": null,
        "sortie": null
      }
    }
  ],
  "metadata": {
    "total": 28,
    "perPage": 20,
    "currentPage": 1,
    "prevPage": null,
    "nextPage": 2,
    "from": 1,
    "to": 2
  },
  "refresh": null,
  "error": null
}
```

---

### Détail Vente

Retourne le détail d'une vente.

```
GET /Api/Vente/VenteById/
```

| Header | Type | Requis | Description |
| --- | --- | --- | --- |
| `jwt` | string | oui | Token JWT |

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| `id` | int | oui | ID de la vente |
| `version` | string | non | Version de l'API |

**Réponse v2** :

```json
{
  "data": {
    "id": "148",
    "prix": "275000.00",
    "honoraires": "15000.00",
    "date": "2023-01-21",
    "retro_idUser": null,
    "retro_idContact": null,
    "retro_nom": null,
    "retro_qualite": null,
    "retro_honoraires": "0.00",
    "hono_entree": null,
    "hono_sortie": null,
    "hono_hors_taxe": null,
    "commission_agence": null,
    "part_admin": null,
    "annonce": {
      "id": "5074",
      "NO_DOSSIER": "1684",
      "NO_MANDAT": "1684",
      "offredem": "0",
      "idtype": "2",
      "prix": 275000,
      "surface": "95",
      "titre": "APPARTEMENT T4 AVEC TERRASSE",
      "corps": "<p>Description du bien...</p>",
      "photo": "<https://cdn.example.com/img/biens/5074.jpg>",
      "agence": "1",
      "NEGOCIATEUR": "12",
      "archive": "1",
      "diffusable": "1",
      "partage": "1",
      "localite": {
        "pays": "fr",
        "publique": {
          "ville": "Exempleville",
          "code": "75000",
          "latitude": "48.000000000",
          "longitude": "2.000000000"
        },
        "privee": {
          "ville": "Exempleville",
          "code": "75000",
          "latitude": "48.000000000",
          "longitude": "2.000000000",
          "adresse": "1 rue des Exemples - Résidence A - Appartement 10"
        }
      },
      "valide": "0"
    },
    "mandat": {
      "id": "11079",
      "type": "SIMPLE",
      "debut": null,
      "fin": null,
      "cloture": null,
      "numero": "1684",
      "CartePro": "CPI XXXX XXXX XXX XXX XXX",
      "note": "",
      "duree_irrevocabilite": "",
      "taciteReconduction": "0",
      "montant": "275000",
      "mandants": "M. DOE John - 1 rue des Exemples - Exempleville (75000)",
      "avenants": []
    },
    "mandants": [
      {
        "id": "7429",
        "civilite": "M.",
        "nom": "DOE",
        "commentaires": "",
        "datemaj": "2023-01-30 16:18:02",
        "dateenr": "2022-08-05",
        "agence": "1",
        "archive": "1",
        "id_negociateur": "12",
        "dateAutoArchiv": "2023-08-05 00:00:00",
        "refCouple": null,
        "localite": {
          "pays": "fr",
          "localite": {
            "ville": "Exempleville",
            "code": "75000",
            "latitude": "0.000000000",
            "longitude": "0.000000000",
            "adresse": "1 rue des Exemples"
          }
        },
        "siret": null,
        "url": null,
        "prenom": "John",
        "typologie": ["mandant"],
        "coordonnees": {
          "portable": "0600000001",
          "email": "john.doe@example.com"
        }
      }
    ],
    "acquereurs": [
      {
        "id": "7538",
        "civilite": "M.",
        "nom": "DUPONT",
        "commentaires": "",
        "datemaj": "2022-10-13 17:45:27",
        "dateenr": "2022-09-30",
        "agence": "1",
        "archive": "1",
        "id_negociateur": "12",
        "dateAutoArchiv": "2023-09-30 00:00:00",
        "refCouple": null,
        "localite": {
          "pays": "fr",
          "localite": {
            "ville": "",
            "code": "",
            "latitude": "0.000000000",
            "longitude": "0.000000000",
            "adresse": ""
          }
        },
        "siret": null,
        "url": null,
        "prenom": "Pierre",
        "typologie": ["acquéreur"],
        "coordonnees": {
          "portable": "0600000002",
          "email": "pierre.dupont@example.com"
        }
      }
    ],
    "notaires": {
      "entree": {
        "id": "7623",
        "civilite": "",
        "nom": "Etude Notariale de Maître EXEMPLE",
        "commentaires": "",
        "datemaj": "2022-10-28 11:37:41",
        "dateenr": "2022-10-28",
        "agence": "1",
        "archive": "0",
        "id_negociateur": "12",
        "dateAutoArchiv": "0000-00-00 00:00:00",
        "refCouple": null,
        "localite": {
          "pays": "fr",
          "localite": {
            "ville": "Exempleville",
            "code": "75000",
            "latitude": "48.000000000",
            "longitude": "2.000000000",
            "adresse": "14 boulevard du Soleil"
          }
        },
        "siret": null,
        "url": null,
        "prenom": "",
        "typologie": ["partenaire"],
        "coordonnees": {
          "email": "notaire@example.com"
        }
      },
      "sortie": null
    }
  },
  "metadata": null,
  "refresh": null,
  "error": null
}
```

---

## Variables de collection

Variables utilisées dans les appels API (à configurer selon votre environnement) :

| Variable | Description |
| --- | --- |
| `url` | URL de base de l'instance Hektor |
| `client_id` | Identifiant du client oAuth |
| `client_secret` | Secret du client oAuth |
| `access_token` | Token d'accès oAuth (rempli automatiquement) |
| `jwt` | Token JWT (rempli automatiquement) |
| `version` | Version de l'API (`v2`) |
| `idAnnonce` | ID d'une annonce pour les tests |
| `idMandat` | ID d'un mandat pour les tests |
| `idContact` | ID d'un contact pour les tests |
| `idCompromis` | ID d'un compromis pour les tests |
| `idVente` | ID d'une vente pour les tests |

---

## Codes d'erreur HTTP

| Code | Description |
| --- | --- |
| 200 | Succès |
| 403 | Authentification requise ou token invalide |
| 404 | Ressource non trouvée ou scope invalide |
| 500 | Erreur serveur |

---

## Notes

- Le paramètre `version` est optionnel sur tous les endpoints. S'il n'est pas spécifié, la version legacy est utilisée, merci de spécifié `v2`.
- Le token JWT est rafraîchi automatiquement dans le champ `refresh` de la réponse lorsque le token expire dans moins de 10 minutes.
- Les droits d'accès sont vérifiés hiérarchiquement : un utilisateur ne peut voir que les ressources auxquelles il a accès selon sa position dans la hiérarchie (admin > agence > négociateur > secrétaire).
- Tous les listings sont paginés par 10 ou 20 éléments.